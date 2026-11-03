"""Negative control: permute the SOURCE labels, score against the TRUE held-out labels.

If the benchmark measures real spectrum-to-label structure, scores must collapse (R2 near or
below 0). Held-out labels are used only for scoring, exactly as in the real runs.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from chemiproof.data.manifest import ManifestRow
from chemiproof.evaluation.metrics import compute_metrics
from chemiproof.evaluation.protocols import Fold
from chemiproof.modeling.baselines import SEED, model_factory


def permuted_source_label_control(
    rows: list[ManifestRow],
    X: np.ndarray,
    y: np.ndarray,
    folds: list[Fold],
    keys: list[str],
    groups: np.ndarray,
    n_repeats: int = 3,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "control": "permuted_source_labels",
        "n_repeats": n_repeats,
        "seed": SEED,
        "models": {},
    }
    for key in keys:
        per_repeat = []
        for rep in range(n_repeats):
            rng = np.random.default_rng(SEED + 100 + rep)
            r2s, maes = [], []
            for fold in folds:
                tr, te = fold.train_idx, fold.test_idx
                y_perm = rng.permutation(y[tr])  # destroys the spectrum-label link in training
                model = model_factory(key)().fit(X[tr], y_perm, groups=groups[tr])
                m = compute_metrics(y[te], model.predict(X[te]))
                r2s.append(m.r2)
                maes.append(m.mae_fraction)
            per_repeat.append(
                {"macro_r2": float(np.mean(r2s)), "macro_mae_fraction": float(np.mean(maes))}
            )
        out["models"][key] = {
            "per_repeat": per_repeat,
            "mean_macro_r2": float(np.mean([p["macro_r2"] for p in per_repeat])),
            "mean_macro_mae_fraction": float(
                np.mean([p["macro_mae_fraction"] for p in per_repeat])
            ),
        }
    return out
