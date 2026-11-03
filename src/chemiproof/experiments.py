"""Experiment entry points. M2: `source_internal_loro`; LOAO (`loao`) arrives in M3."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from chemiproof.config import ExperimentConfig
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.evaluation.protocols import source_internal_loro_folds
from chemiproof.evaluation.runner import run_models, summarize, write_run_artifacts
from chemiproof.modeling.baselines import MODEL_KEYS, SEED
from chemiproof.pipeline import load_dataset
from chemiproof.provenance import config_hash, file_sha256, make_run_id
from chemiproof.spectra.preprocess import AUTHOR_V1, preprocess_features

SOURCE_INTERNAL_LIMITATIONS = [
    "Protocol source_internal_loro holds out a MEASUREMENT ROUND, not an adulterant: the held-out "
    "round shares brand/adulterant/ratio cells with the training rounds, so scores are optimistic "
    "and are NOT evidence of unseen-adulterant generalization (see M3 LOAO).",
    "Rounds are probably replicates but this is unproven (replicate_id is empty in the manifest).",
    "Brand imbalance (walnut = 1 brand; soybean/peanut = 2; rapeseed/corn = 3) is an uncontrolled "
    "confounder; no brand-wise results are claimed.",
    "Predictions are scored unclipped; values outside [0, 1] are counted per fold.",
    "Preprocessing author_v1 was prespecified from published code, not tuned; other versions are "
    "not compared in M2.",
]


def _markdown_report(run_id: str, summary: dict[str, Any], folds: list[str]) -> str:
    lines = [
        f"# Run {run_id}: source-internal evaluation (leave-one-round-out)",
        "",
        "Units: MAE/RMSE/bias in olive-oil volume fraction (0.01 = 1 percentage point). "
        f"Folds: {', '.join(folds)}.",
        "",
        "| model | macro MAE (pp) | macro RMSE (fraction) | macro bias (fraction) | macro R2 |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, s in summary.items():
        m = s["macro_over_folds"]
        lines.append(
            f"| {key} | {100 * m['mae_fraction']:.2f} | {m['rmse_fraction']:.4f} | "
            f"{m['bias_fraction']:+.4f} | {m['r2']:.3f} |"
        )
    lines += [
        "",
        "Optimistic protocol, not unseen-adulterant evidence. See summary.json limitations.",
    ]
    return "\n".join(lines) + "\n"


def run_source_internal(
    cfg: ExperimentConfig, data_dir: Path, manifest: Path, output_root: Path
) -> Path:
    if cfg.protocol != "source_internal_loro":
        raise ChemiProofError(StatusCode.NOT_IMPLEMENTED, "protocol 'loao' is implemented in M3")
    if cfg.mode != "inductive":
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "source_internal_loro is inductive only")
    pre = (cfg.model_dump().get("preprocessing") or {}).get("version")
    if pre != AUTHOR_V1.version:
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG, f"unknown preprocessing version {pre!r}; known: author_v1"
        )
    if cfg.random_seed != SEED:
        raise ChemiProofError(StatusCode.INVALID_CONFIG, f"random_seed must be {SEED} for M2")
    keys = list(cfg.models or MODEL_KEYS)

    ds = load_dataset(manifest, data_dir)  # re-verifies every file's SHA-256 against the manifest
    manifest_sha = file_sha256(manifest)
    X = preprocess_features(ds.spectra, AUTHOR_V1)  # per-spectrum, nothing fitted
    y = ds.y
    rounds = np.array([r.measurement_round for r in ds.rows])
    folds = source_internal_loro_folds(ds.rows)

    resolved: dict[str, Any] = {
        **cfg.model_dump(),
        "preprocessing_resolved": AUTHOR_V1.as_dict(),
        "preprocessing_steps": AUTHOR_V1.describe(),
        "manifest_sha256": manifest_sha,
        "n_features": int(X.shape[1]),
    }
    resolved["_config_sha256"] = config_hash(resolved)
    run_id = make_run_id(resolved)

    out = run_models(ds.rows, X, y, folds, keys, rounds, run_id)
    summary = summarize(out, keys)
    out_dir = output_root / f"M2_{run_id}"
    write_run_artifacts(
        out_dir,
        run_id,
        resolved,
        manifest_sha,
        ds.rows,
        folds,
        out,
        summary,
        SOURCE_INTERNAL_LIMITATIONS,
    )
    (out_dir / "run_report.md").write_text(
        _markdown_report(run_id, summary, [f.fold_id for f in folds]), encoding="utf-8"
    )
    return out_dir
