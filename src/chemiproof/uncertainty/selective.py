"""Selective-risk statistics. Absolute errors are used AFTER predictions and decisions exist."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import spearmanr


def selective_stats(abs_err: np.ndarray, abstain: np.ndarray) -> dict[str, float]:
    keep = ~abstain
    n = abs_err.size
    n_keep = int(keep.sum())
    return {
        "n": n,
        "n_retained": n_keep,
        "observed_retention": n_keep / n,
        "rejection_rate": 1.0 - n_keep / n,
        "selective_mae": float(abs_err[keep].mean()) if n_keep else float("nan"),
        "rejected_mae": float(abs_err[~keep].mean()) if n_keep < n else float("nan"),
        "worst_retained_error": float(abs_err[keep].max()) if n_keep else float("nan"),
    }


def _kept(n: int, percent: int) -> int:
    return max(1, math.ceil(n * percent / 100))


def rank_curve(abs_err: np.ndarray, score: np.ndarray, percents: list[int]) -> list[float]:
    """Keep the lowest-score share of samples (stable order for ties); MAE of those kept."""
    order = np.argsort(score, kind="stable")
    return [float(abs_err[order[: _kept(abs_err.size, p)]].mean()) for p in percents]


def oracle_curve(abs_err: np.ndarray, percents: list[int]) -> list[float]:
    """Diagnostic lower bound: reject the largest TRUE errors (needs labels; not deployable)."""
    order = np.argsort(abs_err, kind="stable")
    return [float(abs_err[order[: _kept(abs_err.size, p)]].mean()) for p in percents]


def random_curve(
    abs_err: np.ndarray, percents: list[int], repeats: int, seed: int
) -> dict[str, list[float]]:
    rng = np.random.default_rng(seed)
    n = abs_err.size
    draws = np.empty((repeats, len(percents)))
    for r in range(repeats):
        perm = rng.permutation(n)
        for j, p in enumerate(percents):
            draws[r, j] = abs_err[perm[: _kept(n, p)]].mean()
    return {
        "mean": draws.mean(axis=0).tolist(),
        "p05": np.quantile(draws, 0.05, axis=0).tolist(),
        "p95": np.quantile(draws, 0.95, axis=0).tolist(),
    }


def score_error_spearman(abs_err: np.ndarray, score: np.ndarray) -> float:
    if np.ptp(score) == 0 or np.ptp(abs_err) == 0:
        return float("nan")
    return float(spearmanr(score, abs_err).statistic)
