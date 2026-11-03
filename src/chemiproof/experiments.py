"""Experiment entry points: `source_internal_loro` (M2) and `loao` (M3, inductive baselines)."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from chemiproof.config import ExperimentConfig
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.evaluation.plots import plot_mae_r2_by_fold, plot_parity
from chemiproof.evaluation.protocols import (
    Fold,
    audit_folds,
    loao_folds,
    source_internal_loro_folds,
)
from chemiproof.evaluation.runner import (
    RunOutput,
    git_state,
    run_models,
    summarize,
    write_run_artifacts,
)
from chemiproof.modeling.baselines import MODEL_KEYS, SEED
from chemiproof.pipeline import Dataset, load_dataset
from chemiproof.provenance import config_hash, file_sha256, make_run_id
from chemiproof.spectra.preprocess import AUTHOR_V1, preprocess_features

# Numbers PUBLISHED by Sun et al. (2026, abstract). NOT measured by ChemiProof; kept apart.
PUBLISHED_REFERENCE = {
    "source": "Sun et al. 2026 abstract, doi:10.1038/s41538-026-01037-6 (LOAO mean R2)",
    "status": "published; NOT a ChemiProof measurement",
    "raw_mean_r2": 0.831,
    "pca_mean_r2": 0.693,
    "parafac_mean_r2": 0.659,
    "ot_svr_mean_r2": 0.965,
    "ot_svr_sd": 0.004,
    "caveat": "their protocol clips predictions to [0,1], fits PCA on source+target X, and tunes "
    "CORAL/MMD with target labels (ADR-011); our numbers are not directly comparable",
}

SOURCE_INTERNAL_LIMITATIONS = [
    "Protocol source_internal_loro holds out a MEASUREMENT ROUND, not an adulterant: the held-out "
    "round shares brand/adulterant/ratio cells with the training rounds, so scores are optimistic "
    "and are NOT evidence of unseen-adulterant generalization (see M3 LOAO).",
    "Rounds are probably replicates but this is unproven (replicate_id is empty in the manifest).",
    "Brand imbalance (walnut = 1 brand; soybean/peanut = 2; rapeseed/corn = 3) is an uncontrolled "
    "confounder; no brand-wise results are claimed.",
    "Predictions are scored unclipped; values outside [0, 1] are counted per fold.",
]

LOAO_LIMITATIONS = [
    "Only FIVE held-out adulterant systems exist: a macro mean over five folds says little about "
    "systems beyond them; the spread across folds matters more than the mean.",
    "Brand imbalance is a confounder (walnut = Luhua only; soybean/peanut = 2 brands; "
    "rapeseed/corn = 3). Every test brand also appears in training under other adulterants, so a "
    "model can partly exploit brand-specific fluorescence; the Luhua-only sensitivity run removes "
    "this confound at the price of fewer samples.",
    "All spectra come from one instrument and one lab protocol; no cross-device claim.",
    "Samples are laboratory binary mixtures, not marketplace products. Not a certified test.",
    "Inductive mode only: no information from the held-out batch is used. Transductive (OT) "
    "numbers belong to M4 and must never be mixed with these.",
    "Predictions are scored unclipped; clipped-to-[0,1] metrics are reported separately.",
    "The protocol was frozen (ADR-013) before the held-out adulterants were scored; the M2 grids "
    "were widened once before freezing, using inner CV only (ADR-012).",
]


def _subset(ds: Dataset, brand: str | None) -> Dataset:
    if brand is None:
        return ds
    keep = [i for i, r in enumerate(ds.rows) if r.evoo_brand == brand]
    if not keep:
        raise ChemiProofError(StatusCode.INVALID_CONFIG, f"no samples for brand {brand!r}")
    return Dataset([ds.rows[i] for i in keep], [ds.spectra[i] for i in keep])


def _preds(o: RunOutput, fold_id: str) -> list[tuple[str, str, float]]:
    return [
        (p["model"], p["sample_id"], p["y_pred_fraction"])
        for p in o.predictions
        if p["fold_id"] == fold_id
    ]


def _selected(o: RunOutput, fold_id: str) -> list[Any]:
    return [h for h in o.selected if h["fold_id"] == fold_id]


def _label_canary(
    ds: Dataset,
    X: np.ndarray,
    y: np.ndarray,
    folds: list[Fold],
    keys: list[str],
    groups: np.ndarray,
    base: RunOutput,
    run_id: str,
) -> dict[str, Any]:
    """Shuffle the HELD-OUT labels of each fold and refit: predictions and selected
    hyper-parameters must not move. Catches any future code path that lets test labels in."""
    results = []
    for fold in folds:
        y_c = y.copy()
        rng = np.random.default_rng(SEED + 1)
        shuffled = rng.permutation(y[fold.test_idx])
        if np.array_equal(shuffled, y[fold.test_idx]):
            shuffled = np.roll(shuffled, 1)
        y_c[fold.test_idx] = shuffled
        alt = run_models(ds.rows, X, y_c, [fold], keys, groups, run_id)

        fid = fold.fold_id
        same = _preds(base, fid) == _preds(alt, fid) and _selected(base, fid) == _selected(alt, fid)
        results.append(
            {"fold_id": fold.fold_id, "heldout_labels_shuffled": True, "unchanged": same}
        )
        if not same:
            raise ChemiProofError(
                StatusCode.QC_REVIEW_REQUIRED,
                "LEAKAGE: shuffling held-out labels changed predictions or hyper-parameters",
                fold=fold.fold_id,
            )
    return {"passed": True, "folds": results}


def _table(summary: dict[str, Any], clipped: bool = False) -> list[str]:
    key = "macro_over_folds_clipped_to_unit_interval" if clipped else "macro_over_folds"
    lines = [
        "| model | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | "
        "worst fold (MAE) |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for k, s in summary.items():
        m = s[key]
        lines.append(
            f"| {k} | {100 * m['mae_fraction']:.2f} | {m['rmse_fraction']:.4f} | "
            f"{m['bias_fraction']:+.4f} | {m['r2']:.3f} | {m['r2_std_across_folds']:.3f} | "
            f"{s['worst_fold']} ({100 * m['worst_fold_mae_fraction']:.2f} pp) |"
        )
    return lines


def _markdown_report(
    run_id: str, protocol: str, summary: dict[str, Any], out: RunOutput, subset: str | None
) -> str:
    head = {
        "source_internal_loro": "source-internal evaluation (leave-one-round-out; OPTIMISTIC)",
        "loao": "five-domain LOAO benchmark (inductive)"
        + (f" restricted to brand {subset}" if subset else ""),
    }[protocol]
    lines = [
        f"# Run {run_id}: {head}",
        "",
        "Units: MAE in percentage points (pp) = 100 x fraction; RMSE/bias in olive-oil volume "
        "fraction; R2 unitless and never clamped. Predictions are scored UNCLIPPED.",
        "",
        "## Macro over folds (unweighted)",
        "",
        *_table(summary),
        "",
        "## Same, predictions clipped to [0, 1] (reference-style, secondary)",
        "",
        *_table(summary, clipped=True),
        "",
        "## Per fold",
        "",
        "| fold | model | n | MAE (pp) | RMSE | bias | R2 | out of [0,1] |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in out.fold_metrics:
        lines.append(
            f"| {r['fold_id']} | {r['model']} | {r['n']} | {100 * r['mae_fraction']:.2f} | "
            f"{r['rmse_fraction']:.4f} | {r['bias_fraction']:+.4f} | {r['r2']:.3f} | "
            f"{r['n_out_of_range']} |"
        )
    if protocol == "source_internal_loro":
        lines += ["", "Optimistic protocol, not unseen-adulterant evidence (see summary.json)."]
    return "\n".join(lines) + "\n"


def _write_fold_manifest(path: Path, audit: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        cols = [
            "fold_id",
            "target_adulterant",
            "n_test",
            "n_train",
            "train_adulterants",
            "test_brands",
            "train_brands",
            "test_brands_absent_from_train",
        ]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for f in audit["folds"]:
            w.writerow(
                {k: json.dumps(f[k]) if isinstance(f[k], (dict, list)) else f[k] for k in cols}
            )


def _append_registry(
    output_root: Path,
    run_id: str,
    cfg: ExperimentConfig,
    cfg_sha: str,
    out_dir: Path,
    *,
    protocol: str | None = None,
    run_class: str | None = None,
) -> None:
    """Every run, exploratory or locked, leaves a line: attempt history is never deleted."""
    reg = output_root / "experiment_registry.csv"
    new = not reg.exists()
    g = git_state()
    with reg.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(
                [
                    "utc_time",
                    "run_id",
                    "experiment_id",
                    "protocol",
                    "run_class",
                    "subset_brand",
                    "config_sha256",
                    "git_head",
                    "git_dirty",
                    "output_dir",
                ]
            )
        w.writerow(
            [
                datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                run_id,
                cfg.experiment_id,
                protocol or cfg.protocol,
                run_class or cfg.run_class,
                cfg.subset_brand or "",
                cfg_sha[:16],
                g["head"][:12],
                g["dirty"],
                out_dir.name,
            ]
        )


def run_experiment(
    cfg: ExperimentConfig, data_dir: Path, manifest: Path, output_root: Path
) -> Path:
    if cfg.mode != "inductive":
        raise ChemiProofError(
            StatusCode.NOT_IMPLEMENTED, "transductive_batch (OT) runs are implemented in M4"
        )
    pre = (cfg.model_dump().get("preprocessing") or {}).get("version")
    if pre != AUTHOR_V1.version:
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG, f"unknown preprocessing version {pre!r}; known: author_v1"
        )
    if cfg.random_seed != SEED:
        raise ChemiProofError(StatusCode.INVALID_CONFIG, f"random_seed must be {SEED}")
    if cfg.run_class == "locked" and git_state()["dirty"]:
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG,
            "a locked run needs a clean tracked git tree (commit first so the run is traceable)",
        )
    keys = list(cfg.models or MODEL_KEYS)

    ds = _subset(load_dataset(manifest, data_dir), cfg.subset_brand)  # re-verifies SHA-256s
    manifest_sha = file_sha256(manifest)
    X = preprocess_features(ds.spectra, AUTHOR_V1)  # per-spectrum, nothing fitted
    y = ds.y

    if cfg.protocol == "source_internal_loro":
        folds = source_internal_loro_folds(ds.rows)
        groups = np.array([r.measurement_round for r in ds.rows])
        prefix, limits, fold_audit = "M2", SOURCE_INTERNAL_LIMITATIONS, None
    else:
        folds = loao_folds(ds.rows)
        groups = np.array(
            [r.adulterant_type for r in ds.rows]
        )  # inner CV: leave-one-SOURCE-adulterant
        prefix, limits = "M3", LOAO_LIMITATIONS
        if len(folds) != 5:
            raise ChemiProofError(
                StatusCode.QC_REVIEW_REQUIRED, f"expected 5 LOAO folds, got {len(folds)}"
            )
        try:
            fold_audit = audit_folds(ds.rows, folds, expect_full=cfg.subset_brand is None)
        except ValueError as exc:
            raise ChemiProofError(
                StatusCode.QC_REVIEW_REQUIRED, f"fold audit failed: {exc}"
            ) from exc

    resolved: dict[str, Any] = {
        **cfg.model_dump(),
        "preprocessing_resolved": AUTHOR_V1.as_dict(),
        "preprocessing_steps": AUTHOR_V1.describe(),
        "manifest_sha256": manifest_sha,
        "n_samples": len(ds.rows),
        "n_features": int(X.shape[1]),
    }
    resolved["_config_sha256"] = config_hash(resolved)
    run_id = make_run_id(resolved)

    out = run_models(ds.rows, X, y, folds, keys, groups, run_id)
    summary = summarize(out, keys, ds.rows)
    out_dir = output_root / f"{prefix}_{run_id}"
    write_run_artifacts(
        out_dir, run_id, resolved, manifest_sha, ds.rows, folds, out, summary, limits
    )

    extra: dict[str, Any] = {}
    if cfg.protocol == "loao":
        canary = _label_canary(ds, X, y, folds, keys, groups, out, run_id)
        audit = {"fold_audit": fold_audit, "label_shuffle_canary": canary}
        (out_dir / "leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        _write_fold_manifest(out_dir / "fold_manifest.csv", fold_audit)
        plot_mae_r2_by_fold(out.fold_metrics, out_dir / "mae_r2_by_fold.png")
        plot_parity(out.predictions, out_dir / "parity_by_model.png")
        extra = {
            "published_reference_not_measured": PUBLISHED_REFERENCE,
            "run_class": cfg.run_class,
            "subset_brand": cfg.subset_brand,
            "leakage_audit": {"fold_audit_checks": fold_audit["checks"], "canary_passed": True},
        }
        full = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
        full.update(extra)
        (out_dir / "summary.json").write_text(json.dumps(full, indent=2), encoding="utf-8")

    (out_dir / "run_report.md").write_text(
        _markdown_report(run_id, cfg.protocol, summary, out, cfg.subset_brand), encoding="utf-8"
    )
    _append_registry(output_root, run_id, cfg, resolved["_config_sha256"], out_dir)
    return out_dir


def run_negative_control(
    cfg: ExperimentConfig, data_dir: Path, manifest: Path, output_root: Path
) -> Path:
    """Exploratory negative control for a LOAO config (never locked, never a headline result)."""
    from chemiproof.evaluation.controls import permuted_source_label_control

    if cfg.protocol != "loao" or cfg.mode != "inductive":
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "controls run on inductive loao configs")
    ds = _subset(load_dataset(manifest, data_dir), cfg.subset_brand)
    X = preprocess_features(ds.spectra, AUTHOR_V1)
    folds = loao_folds(ds.rows)
    groups = np.array([r.adulterant_type for r in ds.rows])
    keys = list(cfg.models or MODEL_KEYS)
    result = permuted_source_label_control(ds.rows, X, ds.y, folds, keys, groups)
    run_id = make_run_id(
        {
            "control": "permuted_source_labels",
            "experiment": cfg.experiment_id,
            "manifest": file_sha256(manifest),
            "subset": cfg.subset_brand,
        }
    )
    out_dir = output_root / f"M3_control_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    result["experiment_id"] = cfg.experiment_id
    result["subset_brand"] = cfg.subset_brand
    result["note"] = "negative control, exploratory; scored against TRUE held-out labels"
    (out_dir / "control_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    _append_registry(
        output_root,
        run_id,
        cfg,
        "control",
        out_dir,
        protocol="loao_negative_control",
        run_class="exploratory",
    )
    return out_dir
