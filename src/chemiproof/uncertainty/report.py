"""Plots and the markdown run report for M5 (numbers come only from the computed tables)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

HEADER = (
    "# M5 run report: abstention, intervals, robustness (LOAO-UQ-v1)\n\n"
    "INDUCTIVE research mode. Abstention is a research cue, NOT a safety decision. Intervals are "
    "EMPIRICAL; no coverage guarantee under a new adulterant. Five systems only.\n"
)


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    v = [r[key] for r in rows if not (isinstance(r[key], float) and np.isnan(r[key]))]
    return float(np.mean(v)) if v else float("nan")


def write_plots(out_dir: Path, T: dict[str, list[dict[str, Any]]], keys: list[str]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    folds = sorted({r["fold_id"] for r in T["curve"]})
    fig, axes = plt.subplots(len(keys), len(folds), figsize=(3.2 * len(folds), 2.8 * len(keys)),
                             squeeze=False, sharex=True)  # fmt: skip
    for i, k in enumerate(keys):
        for j, f in enumerate(folds):
            ax = axes[i][j]
            c = [r for r in T["curve"] if r["model"] == k and r["fold_id"] == f
                 and r["score"] == "ood_maha"]  # fmt: skip
            x = [r["retention_percent"] for r in c]
            ax.plot(x, [100 * r["rank_selective_mae"] for r in c], label="ood_maha rank")
            ax.plot(x, [100 * r["random_mean"] for r in c], "--", label="random")
            ax.fill_between(x, [100 * r["random_p05"] for r in c],
                            [100 * r["random_p95"] for r in c], alpha=0.2)  # fmt: skip
            ax.plot(x, [100 * r["oracle_mae_diagnostic"] for r in c], ":", label="oracle (diag.)")
            ax.set_title(f"{k} / {f.removeprefix('LOAO-')}", fontsize=8)
            ax.invert_xaxis()
            if i == len(keys) - 1:
                ax.set_xlabel("retention (%)", fontsize=7)
            if j == 0:
                ax.set_ylabel("selective MAE (pp)", fontsize=7)
    axes[0][0].legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(out_dir / "selective_risk_curves.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3.2))
    cov = [r for r in T["coverage"] if r["variant"] == "pooled"]
    w = 0.25
    for n, k in enumerate(keys):
        vals = [r["observed_coverage"] for r in cov if r["model"] == k]
        ax.bar(np.arange(len(vals)) + n * w, vals, w, label=k)
    ax.axhline(0.9, color="k", ls="--", lw=0.8)
    ax.set_xticks(np.arange(len(folds)) + w)
    ax.set_xticklabels([f.removeprefix("LOAO-") for f in folds], fontsize=8)
    ax.set_ylabel("observed coverage (nominal 0.90)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out_dir / "interval_coverage.png", dpi=130)
    plt.close(fig)


def write_report(
    run_id: str, T: dict[str, list[dict[str, Any]]], verdict: dict[str, Any], keys: list[str]
) -> str:
    L = [HEADER, f"Run: `{run_id}`. Units: fraction (0.01 = 1 percentage point).\n"]
    L.append("## Selective risk at the 0.80 retention goal (threshold from SOURCE only)\n")
    L.append("| model | score | full MAE (pp) | observed retention | selective MAE (pp) | "
             "rejected MAE (pp) |\n|---|---|---|---|---|---|")  # fmt: skip
    for k in keys:
        for s in ("ood_maha", "model_disagreement"):
            a = [r for r in T["selective"] if r["model"] == k and r["score"] == s
                 and r["retention_goal"] == 0.8]  # fmt: skip
            L.append(
                f"| {k} | {s} | {100 * _mean(a, 'full_mae_fraction'):.2f} | "
                f"{_mean(a, 'observed_retention'):.2f} | {100 * _mean(a, 'selective_mae'):.2f} | "
                f"{100 * _mean(a, 'rejected_mae'):.2f} |"
            )
    L.append("\nMeans are unweighted over the five folds. Per-fold rows: `selective_risk.csv`.\n")
    L.append("## Usefulness verdict (rule fixed in ADR-017)\n")
    L.append("| model/score | folds improved | folds beat random p05 | useful |\n|---|---|---|---|")
    for name, v in verdict["verdicts"].items():
        L.append(f"| {name} | {v['folds_threshold_improved']}/{v['n_folds']} | "
                 f"{v['folds_beat_random_p05']}/{v['n_folds']} | "
                 f"{'yes' if v['useful_on_this_benchmark'] else 'NO'} |")  # fmt: skip
    L.append("\n## Observed interval coverage (nominal 0.90; empirical, not guaranteed)\n")
    L.append("| model | variant | " + " | ".join(sorted({r['fold_id'] for r in T['coverage']}))
             + " | mean width (pp) |")  # fmt: skip
    folds = sorted({r["fold_id"] for r in T["coverage"]})
    L.append("|---|---|" + "---|" * (len(folds) + 1))
    for k in keys:
        for var in ("pooled", "max_domain"):
            a = [r for r in T["coverage"] if r["model"] == k and r["variant"] == var]
            cells = [f"{next(r['observed_coverage'] for r in a if r['fold_id'] == f):.2f}"
                     for f in folds]  # fmt: skip
            L.append(f"| {k} | {var} | " + " | ".join(cells)
                     + f" | {100 * _mean(a, 'mean_width_fraction'):.1f} |")  # fmt: skip
    L.append("\n## Robustness (held-out MAE vs clean, mean over folds)\n")
    L.append("| model | perturbation | level | MAE (pp) | max feature change | abstain rate |"
             "\n|---|---|---|---|---|---|")  # fmt: skip
    seen: set[tuple[Any, ...]] = set()
    for r in T["perturbation"]:
        key = (r["model"], r["perturbation"], r["level"])
        if key in seen:
            continue
        seen.add(key)
        a = [x for x in T["perturbation"] if (x["model"], x["perturbation"], x["level"]) == key]
        L.append(f"| {key[0]} | {key[1]} | {key[2]} | {100 * _mean(a, 'mae_fraction'):.2f} | "
                 f"{max(x['max_abs_feature_change'] for x in a):.2e} | "
                 f"{_mean(a, 'abstain_rate_ood_maha_r0.8'):.2f} |")  # fmt: skip
    L.append("\nNoise rows average over seeds. Full detail: `perturbation_table.csv`.\n")
    L.append("## Limitations\n\nSee `summary.json` (`limitations`) and ADR-017.\n")
    return "\n".join(L) + "\n"
