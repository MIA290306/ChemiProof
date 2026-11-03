"""Benchmark figures drawn from saved prediction/metric rows (matplotlib, Agg backend)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

PALETTE = ["#4c78a8", "#f58518", "#54a24b", "#b279a2", "#e45756"]  # colour-blind-safe-ish


def plot_mae_r2_by_fold(fold_metrics: list[dict[str, Any]], out_png: Path) -> None:
    folds = list(dict.fromkeys(r["fold_id"] for r in fold_metrics))
    models = list(dict.fromkeys(r["model"] for r in fold_metrics))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    width = 0.8 / len(models)
    for j, (field, label) in enumerate(
        (("mae_fraction", "MAE [percentage points]"), ("r2", "R2 (unitless, unclipped)"))
    ):
        ax = axes[j]
        for i, m in enumerate(models):
            vals = [
                next(r[field] for r in fold_metrics if r["fold_id"] == f and r["model"] == m)
                for f in folds
            ]
            vals = [100 * v for v in vals] if field == "mae_fraction" else vals
            ax.bar(np.arange(len(folds)) + i * width, vals, width, label=m, color=PALETTE[i % 5])
        ax.set_xticks(np.arange(len(folds)) + width * (len(models) - 1) / 2, folds, rotation=20)
        ax.set_ylabel(label)
        ax.axhline(0, color="black", linewidth=0.6)
    axes[0].legend(frameon=False)
    fig.suptitle("Held-out-adulterant (LOAO) benchmark: each bar is one held-out adulterant")
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=120)
    plt.close(fig)


def plot_parity(predictions: list[dict[str, Any]], out_png: Path) -> None:
    models = list(dict.fromkeys(p["model"] for p in predictions))
    folds = list(dict.fromkeys(p["fold_id"] for p in predictions))
    fig, axes = plt.subplots(1, len(models), figsize=(4.2 * len(models), 4.2), squeeze=False)
    for ax, m in zip(axes[0], models, strict=True):
        for i, f in enumerate(folds):
            pts = [p for p in predictions if p["model"] == m and p["fold_id"] == f]
            ax.scatter(
                [p["y_true_fraction"] for p in pts],
                [p["y_pred_fraction"] for p in pts],
                s=9,
                alpha=0.6,
                color=PALETTE[i % 5],
                label=f.removeprefix("LOAO-"),
            )
        ax.plot([0, 1], [0, 1], color="black", linewidth=0.8)
        ax.set_title(m)
        ax.set_xlabel("true olive fraction")
        ax.set_ylabel("predicted olive fraction (unclipped)")
    axes[0][0].legend(title="held-out", frameon=False, fontsize=7)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
