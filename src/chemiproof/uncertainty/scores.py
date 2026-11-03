"""Label-free risk scores (ADR-017). They read spectra / model outputs only, never labels."""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA

from chemiproof.modeling.baselines import SEED


class MahalanobisScorer:
    """Mahalanobis distance in a k-component PCA space of the FITTED spectra.

    `score = sqrt(sum_k z_k^2 / lambda_k)`; fitted on training spectra only. A large value means
    the spectrum lies far from the training cloud: a research-level risk cue, nothing more.
    """

    def __init__(self, n_components: int = 10) -> None:
        self.n_components = n_components

    def fit(self, X: np.ndarray) -> MahalanobisScorer:
        k = min(self.n_components, X.shape[0] - 1, X.shape[1])
        if k < 1:
            raise ValueError("not enough rows to fit the OOD scorer")
        self.pca_ = PCA(n_components=k, random_state=SEED).fit(X)
        var = np.asarray(self.pca_.explained_variance_, dtype=float)
        self.var_ = np.maximum(var, np.finfo(float).tiny)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        z = self.pca_.transform(X)
        return np.sqrt(np.sum(z**2 / self.var_, axis=1))


def model_disagreement(preds: dict[str, np.ndarray]) -> np.ndarray:
    """Population standard deviation of the models' predictions for the same spectrum."""
    stack = np.stack([np.asarray(p, dtype=float).reshape(-1) for p in preds.values()])
    return np.std(stack, axis=0)
