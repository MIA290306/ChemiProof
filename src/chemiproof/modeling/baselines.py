"""Source-only (inductive) baseline models. Every learned transform lives INSIDE the estimator,
so `fit` only ever sees the rows it is given (no train/test leakage by construction).

Keys (docs/science/05_EVALUATION_PLAN.md): mean_y, svr_raw, pca_svr, pls.
`svr_raw` uses the published-reference settings (ADR-011); pca_svr / pls tune one integer
hyper-parameter by an inner group-wise CV over the TRAINING rows only.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR

SEED = 20261024
MODEL_KEYS = ("mean_y", "svr_raw", "pca_svr", "pls")
# v2 grids (ADR-012): v1 was PCA (5,10,20,40) / PLS (2,4,6,8,12) and PLS hit its upper bound 3/3.
PCA_GRID = (5, 10, 20, 40, 80)
PLS_GRID = (2, 4, 6, 8, 12, 16, 24, 32)


def reference_svr() -> SVR:
    """Published-reference SVR: poly, degree 3, C=1, gamma='scale', epsilon=0.1 (fraction units)."""
    return SVR(kernel="poly", degree=3, C=1.0, gamma="scale", epsilon=0.1)


def make_base_estimator(key: str, n_components: int | None = None) -> BaseEstimator:
    if key == "mean_y":
        return DummyRegressor(strategy="mean")
    if key == "svr_raw":
        return reference_svr()
    if key == "pca_svr":
        return Pipeline(
            [
                ("pca", PCA(n_components=n_components or PCA_GRID[0], random_state=SEED)),
                ("svr", reference_svr()),
            ]
        )
    if key == "pls":
        return PLSRegression(n_components=n_components or PLS_GRID[0], scale=False)
    raise KeyError(f"unknown model key {key!r}; expected one of {MODEL_KEYS}")


class SelectedModel(BaseEstimator, RegressorMixin):
    """Fits `key`; for tunable keys chooses n_components by group-wise inner CV on the fit data.

    `groups` (e.g. measurement round) are passed to `fit` and used ONLY to build inner folds from
    the training rows. Chosen value is stored in `selected_`.
    """

    def __init__(self, key: str = "mean_y") -> None:
        self.key = key

    def _grid(self) -> tuple[int, ...] | None:
        return {"pca_svr": PCA_GRID, "pls": PLS_GRID}.get(self.key)

    def fit(self, X: np.ndarray, y: np.ndarray, groups: np.ndarray | None = None) -> SelectedModel:
        grid = self._grid()
        self.selected_: dict[str, Any] = {}
        n_comp = None
        if grid is not None:
            if groups is None or len(set(groups)) < 2:
                raise ValueError("tunable models need >= 2 training groups for inner CV")
            # Components must fit the SMALLEST inner training fold (rank <= n_rows - 1).
            smallest_inner = min(int(np.sum(groups != g)) for g in set(groups))
            max_comp = min(smallest_inner - 1, X.shape[1])
            if max_comp < 1:
                raise ValueError("not enough training rows for inner CV")
            scores = {}
            for c in grid:
                if c > max_comp:
                    continue
                errs = []
                for g in sorted(set(groups)):
                    tr, va = groups != g, groups == g
                    model = make_base_estimator(self.key, c).fit(X[tr], y[tr])
                    pred = np.asarray(model.predict(X[va])).reshape(-1)
                    errs.append(np.mean(np.abs(pred - y[va])))
                scores[c] = float(np.mean(errs))
            n_comp = min(scores, key=lambda c: (scores[c], c))  # ties -> fewer components
            self.selected_ = {"n_components": n_comp, "inner_cv_mae_by_n": scores}
        self.model_ = clone(make_base_estimator(self.key, n_comp)).fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray(self.model_.predict(X)).reshape(-1)


def model_factory(key: str) -> Callable[[], SelectedModel]:
    if key not in MODEL_KEYS:
        raise KeyError(f"unknown model key {key!r}; expected one of {MODEL_KEYS}")
    return lambda: SelectedModel(key)
