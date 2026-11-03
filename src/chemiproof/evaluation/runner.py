"""Run models over folds and write the standard artifact set (see 04_ARCHITECTURE.md)."""

from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from chemiproof.data.manifest import ManifestRow
from chemiproof.evaluation.metrics import Metrics, compute_metrics, macro_average
from chemiproof.evaluation.protocols import Fold
from chemiproof.logging_utils import log_event
from chemiproof.modeling.baselines import model_factory
from chemiproof.provenance import environment_info


@dataclass
class RunOutput:
    predictions: list[dict[str, Any]]
    fold_metrics: list[dict[str, Any]]
    selected: list[dict[str, Any]]
    metrics_objects: dict[tuple[str, str], Metrics]


def run_models(
    rows: list[ManifestRow],
    X: np.ndarray,
    y: np.ndarray,
    folds: list[Fold],
    model_keys: list[str],
    inner_groups: np.ndarray,
    run_id: str,
    mode: str = "inductive",
) -> RunOutput:
    """For each fold and model: fit on train rows ONLY (inner CV groups come from train rows only),
    then predict the test rows. Test labels are touched only by `compute_metrics` afterwards."""
    preds, fold_rows, selected = [], [], []
    mobj: dict[tuple[str, str], Metrics] = {}
    for fold in folds:
        tr, te = fold.train_idx, fold.test_idx
        for key in model_keys:
            model = model_factory(key)()
            model.fit(X[tr], y[tr], groups=inner_groups[tr])
            y_hat = model.predict(X[te])
            m = compute_metrics(y[te], y_hat)  # first and only use of y[te]
            mobj[(fold.fold_id, key)] = m
            log_event("fold_done", fold=fold.fold_id, model=key, mae=round(m.mae_fraction, 4))
            fold_rows.append(
                {
                    "run_id": run_id,
                    "fold_id": fold.fold_id,
                    "model": key,
                    "mode": mode,
                    "n": m.n,
                    "mae_fraction": m.mae_fraction,
                    "rmse_fraction": m.rmse_fraction,
                    "bias_fraction": m.bias_fraction,
                    "r2": m.r2,
                    "retention": 1.0,  # no abstention in M2
                    "mae_pp": m.mae_pp,
                    "n_out_of_range": m.n_out_of_range,
                }
            )
            selected.append({"fold_id": fold.fold_id, "model": key, **model.selected_})
            for i, p in zip(te, y_hat, strict=True):
                preds.append(
                    {
                        "run_id": run_id,
                        "fold_id": fold.fold_id,
                        "source_sample_hash": rows[i].sha256,
                        "sample_id": rows[i].sample_id,
                        "y_true_fraction": float(y[i]),
                        "y_pred_fraction": float(p),
                        "model": key,
                        "mode": mode,
                        "abstain": "",
                        "ood_score": "",
                        "interval_lo": "",
                        "interval_hi": "",
                    }
                )
    return RunOutput(preds, fold_rows, selected, mobj)


def summarize(
    out: RunOutput, model_keys: list[str], rows: list[ManifestRow] | None = None
) -> dict[str, Any]:
    """Macro (unweighted over folds) and pooled metrics, unclipped primary + clipped secondary."""
    by_sample = {r.sample_id: r for r in rows} if rows else {}
    summary: dict[str, Any] = {}
    for key in model_keys:
        preds = [p for p in out.predictions if p["model"] == key]
        per_fold = [m for (fid, k), m in out.metrics_objects.items() if k == key]
        fold_ids = [fid for (fid, k) in out.metrics_objects if k == key]
        pooled_t = np.array([p["y_true_fraction"] for p in preds])
        pooled_p = np.array([p["y_pred_fraction"] for p in preds])
        clipped_folds = []
        for fid in fold_ids:
            fp = [p for p in preds if p["fold_id"] == fid]
            clipped_folds.append(
                compute_metrics(
                    np.array([p["y_true_fraction"] for p in fp]),
                    np.clip([p["y_pred_fraction"] for p in fp], 0.0, 1.0),
                )
            )
        entry: dict[str, Any] = {
            "macro_over_folds": macro_average(per_fold),
            "macro_over_folds_clipped_to_unit_interval": macro_average(clipped_folds),
            "pooled_unclipped": compute_metrics(pooled_t, pooled_p).as_dict(),
            "pooled_clipped_to_unit_interval": compute_metrics(
                pooled_t, np.clip(pooled_p, 0.0, 1.0)
            ).as_dict(),
            "worst_fold": max(
                zip(fold_ids, per_fold, strict=True), key=lambda t: t[1].mae_fraction
            )[0],
        }
        if by_sample:
            brand: dict[str, dict[str, dict[str, float]]] = {}
            for fid in fold_ids:
                groups: dict[str, list[float]] = {}
                for p in preds:
                    if p["fold_id"] == fid:
                        err = p["y_pred_fraction"] - p["y_true_fraction"]
                        groups.setdefault(by_sample[p["sample_id"]].evoo_brand, []).append(err)
                brand[fid] = {
                    b: {
                        "n": len(e),
                        "mae_fraction": float(np.mean(np.abs(e))),
                        "bias_fraction": float(np.mean(e)),
                    }
                    for b, e in sorted(groups.items())
                }
            entry["descriptive_by_brand"] = brand
        summary[key] = entry
    return summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def git_state(repo: Path | None = None) -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(repo) if repo else None,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "unavailable"

    return {
        "head": run("rev-parse", "HEAD"),
        "dirty": bool(run("status", "--porcelain", "--untracked-files=no")),
    }


def write_run_artifacts(
    out_dir: Path,
    run_id: str,
    resolved_config: dict[str, Any],
    manifest_sha256: str,
    rows: list[ManifestRow],
    folds: list[Fold],
    out: RunOutput,
    summary: dict[str, Any],
    limitations: list[str],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "config_resolved.yaml").write_text(
        yaml.safe_dump(resolved_config, sort_keys=True, allow_unicode=True), encoding="utf-8"
    )
    (out_dir / "environment.json").write_text(json.dumps(environment_info(), indent=2), "utf-8")
    (out_dir / "git_state.json").write_text(json.dumps(git_state(), indent=2), "utf-8")
    (out_dir / "dataset_manifest_sha256.txt").write_text(manifest_sha256 + "\n", "utf-8")
    split_rows = [
        {"fold_id": f.fold_id, "role": role, "sample_id": rows[i].sample_id}
        for f in folds
        for role, idx in (("train", f.train_idx), ("test", f.test_idx))
        for i in idx
    ]
    _write_csv(out_dir / "splits.csv", split_rows)
    _write_csv(out_dir / "predictions.csv", out.predictions)
    _write_csv(out_dir / "metrics_by_fold.csv", out.fold_metrics)
    full = {
        "run_id": run_id,
        "config_sha256": resolved_config.get("_config_sha256"),
        "manifest_sha256": manifest_sha256,
        "git": git_state(),
        "units": "MAE/RMSE/bias: olive volume FRACTION (0.01 = 1 percentage point); R2 unitless",
        "models": summary,
        "selected_hyperparameters": out.selected,
        "limitations": limitations,
    }
    (out_dir / "summary.json").write_text(json.dumps(full, indent=2), encoding="utf-8")
