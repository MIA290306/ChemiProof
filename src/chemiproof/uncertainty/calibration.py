"""Source-only calibration: interval half-widths and retention thresholds (ADR-017)."""

from __future__ import annotations

import math

import numpy as np

from chemiproof.errors import ChemiProofError, StatusCode


def finite_sample_quantile(values: np.ndarray, level: float) -> float:
    """Empirical quantile with the (n+1) finite-sample rank: the ceil((n+1)*level)-th smallest.

    This is the split-conformal rank; it is a plain empirical quantile when exchangeability fails,
    which is the case for a new adulterant. No coverage guarantee is implied.
    """
    v = np.sort(np.asarray(values, dtype=float))
    n = v.size
    k = math.ceil((n + 1) * level)
    if n == 0 or k > n:
        raise ChemiProofError(
            StatusCode.INSUFFICIENT_CALIBRATION,
            "too few calibration points for this level",
            n=n,
            level=level,
        )
    return float(v[k - 1])


def interval_halfwidths(
    residuals_by_group: dict[str, np.ndarray],
    level: float,
    min_points: int,
    min_groups: int,
) -> dict[str, float]:
    """`pooled` and `max_domain` half-widths from cross-fitted absolute residuals."""
    n = sum(r.size for r in residuals_by_group.values())
    if n < min_points or len(residuals_by_group) < min_groups:
        raise ChemiProofError(
            StatusCode.INSUFFICIENT_CALIBRATION,
            "calibration set too small; refusing to invent an interval",
            n_points=n,
            n_groups=len(residuals_by_group),
        )
    pooled = np.abs(np.concatenate(list(residuals_by_group.values())))
    per_group = [finite_sample_quantile(np.abs(r), level) for r in residuals_by_group.values()]
    return {"pooled": finite_sample_quantile(pooled, level), "max_domain": float(max(per_group))}


def retention_thresholds(scores: np.ndarray, goals: list[float]) -> dict[float, float]:
    """Threshold per retention goal = that quantile of the pooled source cross-fitted scores.

    A goal of 1.0 keeps everything (threshold +inf). 'higher' interpolation keeps the source
    rejection rate at or below 1 - goal.
    """
    s = np.asarray(scores, dtype=float)
    out: dict[float, float] = {}
    for g in goals:
        out[g] = float("inf") if g >= 1.0 else float(np.quantile(s, g, method="higher"))
    return out
