"""Evaluation metrics. y is olive-oil volume FRACTION in [0, 1]; 0.01 fraction = 1 percentage point.

Predictions are scored UNCLIPPED. Out-of-range predictions are counted, and clipped metrics are
available separately (docs/science/05_EVALUATION_PLAN.md section 5).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class Metrics:
    n: int
    mae_fraction: float
    rmse_fraction: float
    bias_fraction: float  # mean(pred - true); positive = olive content overestimated
    r2: float  # can be negative; never clamped
    mae_pp: float  # percentage points = 100 * mae_fraction
    n_out_of_range: int  # predictions outside [0, 1]

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _arrays(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    yt, yp = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    if yt.shape != yp.shape or yt.ndim != 1 or yt.size == 0:
        raise ValueError("y_true and y_pred must be non-empty 1-D arrays of equal length")
    if not (np.all(np.isfinite(yt)) and np.all(np.isfinite(yp))):
        raise ValueError("non-finite values in metrics input")
    return yt, yp


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    yt, yp = _arrays(y_true, y_pred)
    ss_res = float(np.sum((yt - yp) ** 2))
    ss_tot = float(np.sum((yt - yt.mean()) ** 2))
    if ss_tot == 0.0:
        return float("nan")  # undefined for a constant target
    return 1.0 - ss_res / ss_tot


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Metrics:
    yt, yp = _arrays(y_true, y_pred)
    err = yp - yt
    mae = float(np.mean(np.abs(err)))
    return Metrics(
        n=int(yt.size),
        mae_fraction=mae,
        rmse_fraction=float(np.sqrt(np.mean(err**2))),
        bias_fraction=float(np.mean(err)),
        r2=r2_score(yt, yp),
        mae_pp=100.0 * mae,
        n_out_of_range=int(np.sum((yp < 0.0) | (yp > 1.0))),
    )


def macro_average(per_fold: list[Metrics]) -> dict[str, float]:
    """Unweighted mean over folds (R2 computed per fold first, then averaged)."""
    keys = ("mae_fraction", "rmse_fraction", "bias_fraction", "r2")
    out = {k: float(np.mean([getattr(m, k) for m in per_fold])) for k in keys}
    out["r2_std_across_folds"] = float(np.std([m.r2 for m in per_fold]))
    out["worst_fold_mae_fraction"] = float(max(m.mae_fraction for m in per_fold))
    return out
