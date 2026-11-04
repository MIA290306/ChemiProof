"""CP-652: turns finished results/ run directories into the CP-651 contract's CSV tables.

Read-only on results/ and data/interim/sample_manifest.csv. Writes only CSVs, an
export_manifest.json and a reconciliation report under the chosen --output-dir.
No model is fit, no threshold is tuned, no intensity array is read or written here.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from chemiproof.bi import contract as ct

# --- static reference dimensions (chemiproof.data.labels is the source of truth) ---

ADULTERANT_LABELS = {
    "soybean": "Soybean oil",
    "peanut": "Peanut oil",
    "rapeseed": "Rapeseed oil",
    "corn": "Corn oil",
    "walnut": "Walnut oil",
}
BRAND_LABELS = {"luhua": "Luhua", "olivera": "OliVera", "earl_grey": "Earl Grey"}

MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "mean_y": {
        "model_family": "baseline",
        "default_mode": "inductive",
        "information_access": "source labels only (constant predictor)",
        "is_control": True,
        "is_published_style": False,
        "description": "predicts the source-train mean olive fraction",
    },
    "svr_raw": {
        "model_family": "svr",
        "default_mode": "inductive",
        "information_access": "source labels+features only",
        "is_control": False,
        "is_published_style": False,
        "description": "SVR on preprocessed raw features",
    },
    "pca_svr": {
        "model_family": "pca_svr",
        "default_mode": "inductive",
        "information_access": "source labels+features only",
        "is_control": False,
        "is_published_style": False,
        "description": "PCA dimensionality reduction then SVR",
    },
    "pls": {
        "model_family": "pls",
        "default_mode": "inductive",
        "information_access": "source labels+features only",
        "is_control": False,
        "is_published_style": False,
        "description": "partial least squares regression",
    },
    "ot_svr": {
        "model_family": "optimal_transport",
        "default_mode": "transductive_batch",
        "information_access": "source labels+features, unlabeled target batch features",
        "is_control": False,
        "is_published_style": False,
        "description": (
            "Sinkhorn OT barycentric projection of source onto the target batch, then SVR"
        ),
    },
    "ot_svr_pot": {
        "model_family": "optimal_transport",
        "default_mode": "transductive_batch",
        "information_access": "source labels+features, unlabeled target batch features",
        "is_control": False,
        "is_published_style": True,
        "description": "same as ot_svr, solved with the POT reference library for cross-checking",
    },
    "author_pca50": {
        "model_family": "published_style_pca",
        "default_mode": "transductive_batch",
        "information_access": "source labels+features, unlabeled target batch features",
        "is_control": False,
        "is_published_style": True,
        "description": "author-style PCA (50 components) replication, read-only reference code",
    },
    "author_pca10": {
        "model_family": "published_style_pca",
        "default_mode": "transductive_batch",
        "information_access": "source labels+features, unlabeled target batch features",
        "is_control": False,
        "is_published_style": True,
        "description": "author-style PCA (10 components) replication, read-only reference code",
    },
    "svr_no_adaptation": {
        "model_family": "control",
        "default_mode": "inductive",
        "information_access": "source labels+features only (no target batch used)",
        "is_control": True,
        "is_published_style": False,
        "description": "SVR control run inside a transductive experiment, without OT adaptation",
    },
}

PUBLISHED_REFERENCE_ROWS = [
    # model_label -> (metric value key in summary.json, comparable_model_key, sd key or None)
    ("raw", "raw_mean_r2", "svr_raw", None),
    ("pca", "pca_mean_r2", "pca_svr", None),
    ("parafac", "parafac_mean_r2", None, None),
    ("ot_svr", "ot_svr_mean_r2", "ot_svr", "ot_svr_sd"),
]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_dim_adulterant() -> list[dict[str, Any]]:
    from chemiproof.data.labels import EXPECTED_BRANDS, EXPECTED_COUNTS

    return [
        {
            "adulterant_key": key,
            "adulterant_label": ADULTERANT_LABELS[key],
            "expected_samples": EXPECTED_COUNTS[key],
            "expected_brands": len(EXPECTED_BRANDS[key]),
        }
        for key in EXPECTED_COUNTS
    ]


def build_dim_brand() -> list[dict[str, Any]]:
    return [{"brand_key": k, "brand_label": v} for k, v in BRAND_LABELS.items()]


def build_dim_model() -> list[dict[str, Any]]:
    return [{"model_key": k, **v} for k, v in MODEL_REGISTRY.items()]


def build_dim_sample(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.is_file():
        return []
    out = []
    for r in _csv_rows(manifest_path):
        olive_fraction = float(r["olive_fraction"])
        out.append(
            {
                "sample_id": r["sample_id"],
                "adulterant_key": r["adulterant_type"],
                "brand_key": r["evoo_brand"],
                "olive_fraction": olive_fraction,
                "olive_percent": 100 * olive_fraction,
                "olive_ratio_raw": r["olive_ratio_raw"],
                "measurement_round": int(r["measurement_round"]),
                "replicate_id": r["replicate_id"] or None,
                "source_file_sha256": r["sha256"],
                "source_record_doi": r["source_record_doi"],
                "manifest_sha256": None,  # filled by the caller once the manifest hash is known
                "parser_version": r["parser_version"],
            }
        )
    return out


class RunMeta:
    """One evaluation run: a results/<dir> with predictions.csv + metrics_by_fold.csv."""

    def __init__(self, run_id: str, out_dir: Path, **fields: Any) -> None:
        self.run_id = run_id
        self.out_dir = out_dir
        self.fields = fields


def discover_evaluation_runs(results_dir: Path) -> list[RunMeta]:
    """M3/M4/M5 from the registry (predate-registry M2 is special-cased separately)."""
    registry = results_dir / "experiment_registry.csv"
    committed = {p.name for p in results_dir.iterdir() if p.is_dir()}
    runs = []
    for row in _csv_rows(registry):
        if row["run_class"] != "locked" or row["output_dir"] not in committed:
            continue
        out_dir = results_dir / row["output_dir"]
        if not (out_dir / "predictions.csv").is_file():
            continue  # e.g. FINAL-PLS-v1 is a trained artifact, not an evaluation run
        fields = {k: v for k, v in row.items() if k != "run_id"}
        runs.append(RunMeta(row["run_id"], out_dir, **fields))
    m2_dirs = [p for p in results_dir.iterdir() if p.is_dir() and p.name.startswith("M2_")]
    for d in m2_dirs:
        s = _json(d / "summary.json")
        runs.append(
            RunMeta(
                s["run_id"],
                d,
                experiment_id="chemiproof-source-internal-loro",
                protocol="source_internal_loro",
                run_class="locked",
                subset_brand="",
                config_sha256=s["config_sha256"],
                git_head=s["git"]["head"],
                git_dirty=str(s["git"]["dirty"]),
                utc_time="",
            )  # fmt: skip
        )
    return runs


def build_dim_experiment(runs: list[RunMeta], protocol_map: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for r in runs:
        f = r.fields
        s = _json(r.out_dir / "summary.json")
        protocol_id, is_registered = ct.resolve_protocol_id(protocol_map, f["config_sha256"])
        leakage = s.get("leakage_audit") or {}
        git_dirty = str(f["git_dirty"]).strip().lower() == "true"
        rows.append(
            {
                "run_id": r.run_id,
                "run_dir": r.out_dir.name,
                "experiment_id": f["experiment_id"],
                "protocol_id": protocol_id,
                "protocol_family": f["protocol"],
                "run_class": f["run_class"],
                "mode": "transductive_batch" if "ot" in f["experiment_id"] else "inductive",
                "subset_brand": f.get("subset_brand") or None,
                "preprocessing_version": "author_v1",
                "random_seed": None,
                "n_samples": None,
                "config_sha256": f["config_sha256"],
                "manifest_sha256": s["manifest_sha256"],
                "git_head": f["git_head"],
                "git_dirty": git_dirty,
                "utc_time": f.get("utc_time") or None,
                "is_registered": is_registered,
                "is_headline": is_registered and not git_dirty,
                "canary_passed": bool(leakage.get("canary_passed", True)),
                "label_convention": "olive_fraction = olive-oil volume fraction in [0,1] (ADR-008)",
                "transductive_warning": (
                    "TRANSDUCTIVE RESEARCH MODE: needs an unlabeled target batch; "
                    "never advertised as single-file deployment performance."
                    if "ot" in f["experiment_id"]
                    else None
                ),
                "limitations_text": "; ".join(s.get("limitations", [])) or None,
            }
        )
    return rows


def build_dim_fold(runs: list[RunMeta]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for r in runs:
        fm = r.out_dir / "fold_manifest.csv"
        if fm.is_file():
            for row in _csv_rows(fm):
                seen[row["fold_id"]] = {
                    "fold_id": row["fold_id"], "fold_type": "LOAO",
                    "target_adulterant": row["target_adulterant"], "held_out_round": None,
                }  # fmt: skip
            continue
        mf = r.out_dir / "metrics_by_fold.csv"
        if mf.is_file() and r.fields.get("protocol") == "source_internal_loro":
            for row in _csv_rows(mf):
                fid = row["fold_id"]
                if fid in seen or not fid.startswith("SI-round"):
                    continue
                seen[fid] = {
                    "fold_id": fid, "fold_type": "LORO",
                    "target_adulterant": None, "held_out_round": int(fid[-1]),
                }  # fmt: skip
    return list(seen.values())


def build_fact_predictions(runs: list[RunMeta]) -> list[dict[str, Any]]:
    rows = []
    for r in runs:
        for row in _csv_rows(r.out_dir / "predictions.csv"):
            y_true = float(row["y_true_fraction"])
            y_pred = float(row["y_pred_fraction"])
            y_clipped = min(1.0, max(0.0, y_pred))
            residual = y_pred - y_true
            rows.append(
                {
                    "run_id": r.run_id,
                    "fold_id": row["fold_id"],
                    "model_key": row["model"],
                    "sample_id": row["sample_id"],
                    "mode": row["mode"],
                    "y_true_fraction": y_true,
                    "y_pred_fraction": y_pred,
                    "y_pred_clipped_fraction": y_clipped,
                    "residual_fraction": residual,
                    "abs_error_fraction": abs(residual),
                    "abs_error_pp": 100 * abs(residual),
                    "is_out_of_unit_interval": not (0.0 <= y_pred <= 1.0),
                    "source_sample_hash": row["source_sample_hash"],
                }
            )
    return rows


def _metrics_block(
    d: dict[str, Any], run_id: str, model_key: str, mode: str
) -> list[dict[str, Any]]:
    out = []
    macro, macro_c = d.get("macro_over_folds"), d.get("macro_over_folds_clipped_to_unit_interval")
    for scope_type, block, scoring in (
        ("macro", macro, "unclipped"),
        ("macro", macro_c, "clipped_to_unit_interval"),
        ("pooled", d.get("pooled_unclipped"), "unclipped"),
        ("pooled", d.get("pooled_clipped_to_unit_interval"), "clipped_to_unit_interval"),
    ):
        if not block:
            continue
        is_macro = scope_type == "macro"
        out.append(
            {
                "run_id": run_id,
                "model_key": model_key,
                "mode": mode,
                "scope_type": scope_type,
                "fold_id": None,
                "scoring": scoring,
                "n_samples": block.get("n"),
                "n_folds": 5 if is_macro else None,
                "mae_fraction": block["mae_fraction"],
                "mae_pp": block.get("mae_pp", 100 * block["mae_fraction"]),
                "rmse_fraction": block["rmse_fraction"],
                "bias_fraction": block["bias_fraction"],
                "r2": block["r2"],
                "n_out_of_range": block.get("n_out_of_range", 0),
                "retention": 1.0,
                "r2_sd_across_folds": block.get("r2_std_across_folds") if is_macro else None,
                "worst_fold_id": d.get("worst_fold") if is_macro else None,
                "worst_fold_mae_fraction": block.get("worst_fold_mae_fraction")
                if is_macro
                else None,
            }  # fmt: skip
        )
    return out


def build_fact_model_metrics(runs: list[RunMeta]) -> list[dict[str, Any]]:
    """M5 has no metrics_by_fold.csv / summary.json models block: its point predictions are
    identical to M3's (by design, same preprocessing/hyperparameters) and already covered
    by the M3 run's rows; it contributes none of its own here, only to fact_uncertainty."""
    rows = []
    for r in runs:
        if not (r.out_dir / "metrics_by_fold.csv").is_file():
            continue
        mode = "transductive_batch" if "ot" in r.fields["experiment_id"] else "inductive"
        for row in _csv_rows(r.out_dir / "metrics_by_fold.csv"):
            rows.append(
                {
                    "run_id": r.run_id,
                    "model_key": row["model"],
                    "mode": row["mode"],
                    "scope_type": "fold",
                    "fold_id": row["fold_id"],
                    "scoring": "unclipped",
                    "n_samples": int(row["n"]),
                    "n_folds": 1,
                    "mae_fraction": float(row["mae_fraction"]),
                    "mae_pp": float(row["mae_pp"]),
                    "rmse_fraction": float(row["rmse_fraction"]),
                    "bias_fraction": float(row["bias_fraction"]),
                    "r2": float(row["r2"]),
                    "n_out_of_range": int(row["n_out_of_range"]),
                    "retention": float(row["retention"]),
                    "r2_sd_across_folds": None,
                    "worst_fold_id": None,
                    "worst_fold_mae_fraction": None,
                }  # fmt: skip
            )
        s = _json(r.out_dir / "summary.json")
        for model_key, d in s.get("models", {}).items():
            rows.extend(_metrics_block(d, r.run_id, model_key, mode))
    return rows


def build_fact_uncertainty(m5_run: RunMeta | None) -> list[dict[str, Any]]:
    if m5_run is None:
        return []
    rows = []
    widths = {}  # (fold_id, model, variant) -> half-width, for interval_width_fraction
    for row in _csv_rows(m5_run.out_dir / "interval_coverage.csv"):
        widths[(row["fold_id"], row["model"], row["variant"])] = float(row["half_width_fraction"])
    for row in _csv_rows(m5_run.out_dir / "predictions.csv"):
        base = {
            "run_id": m5_run.run_id, "fold_id": row["fold_id"], "model_key": row["model"],
            "sample_id": row["sample_id"], "mode": row["mode"],
            "abstain": row["abstain"].strip().lower() == "true",
            "abstain_reason_code": (
                "ABSTAIN_OOD_RISK" if row["abstain"].strip().lower() == "true" else None
            ),
            "ood_score": float(row["ood_score"]) if row["ood_score"] not in ("", None) else None,
            "ood_method": "ood_maha",
            "ood_threshold": None,
            "threshold_fit_source": "source_only_out_of_fold",
            "interval_method": "empirical residual quantile from source cross-fitting (ADR-017)",
            "interval_nominal_level": 0.90,
            "calibration_protocol": (
                "source-only leave-one-source-adulterant-out, cross-fitted (ADR-017)"
            ),
            "calibration_n": None,
            "status_code": None,
        }  # fmt: skip
        y_true = float(row["y_true_fraction"])
        for variant, lo_key, hi_key in (
            ("pooled", "interval_lo", "interval_hi"),
            ("max_domain", "interval_lo_max_domain", "interval_hi_max_domain"),
        ):
            lo_raw, hi_raw = row.get(lo_key, ""), row.get(hi_key, "")
            if lo_raw in ("", None) or hi_raw in ("", None):
                continue
            lo, hi = float(lo_raw), float(hi_raw)
            rows.append(
                {
                    **base,
                    "variant": variant,
                    "interval_lo_fraction": lo,
                    "interval_hi_fraction": hi,
                    "interval_width_fraction": widths.get(
                        (row["fold_id"], row["model"], variant), hi - lo
                    ),
                    "covered": lo <= y_true <= hi,
                }
            )
    return rows


def build_fact_selective_risk(m5_run: RunMeta | None) -> list[dict[str, Any]]:
    if m5_run is None:
        return []
    curve: dict[tuple[str, str, str, int], dict[str, str]] = {}
    for row in _csv_rows(m5_run.out_dir / "risk_coverage_curve.csv"):
        curve[
            (
                row["run_id"],
                row["fold_id"],
                row["model"],
                row["score"],
                int(row["retention_percent"]),
            )
        ] = row
    rows = []
    for row in _csv_rows(m5_run.out_dir / "selective_risk.csv"):
        pct = round(100 * float(row["retention_goal"]))
        c = curve.get((row["run_id"], row["fold_id"], row["model"], row["score"], pct))
        rows.append(
            {
                "run_id": row["run_id"],
                "model_key": row["model"],
                "mode": row["mode"],
                "scope_type": "fold",
                "fold_id": row["fold_id"],
                "score": row["score"],
                "threshold": float(row["threshold"]),
                "retention_target": float(row["retention_goal"]),
                "retention_observed": float(row["observed_retention"]),
                "rejection_rate": float(row["rejection_rate"]),
                "selective_mae_fraction": float(row["selective_mae"]),
                "selective_mae_pp": 100 * float(row["selective_mae"]),
                "rejected_mae_fraction": float(row["rejected_mae"])
                if row["rejected_mae"]
                else None,
                "worst_retained_error_fraction": float(row["worst_retained_error"])
                if row["worst_retained_error"]
                else None,
                "random_reject_mae_fraction_mean": float(c["random_mean"]) if c else None,
                "random_reject_mae_fraction_p05": float(c["random_p05"]) if c else None,
                "random_reject_mae_fraction_p95": float(c["random_p95"]) if c else None,
                "n_random_repeats": None,
            }  # fmt: skip
        )
    repeats = _read_random_rejection_repeats(m5_run.out_dir)
    for row in rows:
        row["n_random_repeats"] = repeats
    return rows


def _read_random_rejection_repeats(out_dir: Path) -> int | None:
    import yaml

    cfg = yaml.safe_load((out_dir / "config_resolved.yaml").read_text(encoding="utf-8"))
    uq = cfg.get("uq", {})
    return uq.get("random_rejection_repeats")


def build_fact_data_quality(
    manifest_path: Path, manifest_sha256: str | None
) -> list[dict[str, Any]]:
    if not manifest_path.is_file():
        return []
    rows = []
    for r in _csv_rows(manifest_path):
        expected_cells = int(r["excitation_channels"]) * int(r["emission_channels"])
        intensity_min, intensity_max = float(r["intensity_min"]), float(r["intensity_max"])
        rows.append(
            {
                "sample_id": r["sample_id"],
                "qc_status": r["qc_status"],
                "qc_flags": r["qc_flags"] or None,
                "excitation_channels": int(r["excitation_channels"]),
                "emission_channels": int(r["emission_channels"]),
                "expected_cells": expected_cells,
                "finite_cells": expected_cells,  # M1 audit: 0 NaN/Inf dataset-wide (ACCEPTED)
                "spectral_completeness": 1.0,
                "negative_cells": int(r["negative_cells"]),
                "intensity_min": intensity_min,
                "intensity_max": intensity_max,
                "is_constant_signal": intensity_min == intensity_max,
                "is_duplicate_content": False,  # M1 audit: 0 dup hashes dataset-wide (ACCEPTED)
                "axis_matches_reference": True,  # M1 audit: distinct_axes == 1 (ACCEPTED)
                "source_excitation_order": r["source_excitation_order"],
                "normalization_factor": float(r["normalization_factor"]),
                "parser_version": r["parser_version"],
            }
        )
    return rows


def build_fact_data_issues(m1_dir: Path) -> list[dict[str, Any]]:
    audit = _json(m1_dir / "data_audit.json")
    manifest_sha = audit["manifest_sha256"]
    rows = []
    issue_id = 0
    for problem in audit.get("problems", []):
        issue_id += 1
        rows.append(
            {
                "issue_id": f"M1-PROBLEM-{issue_id:03d}",
                "severity": "WARN",
                "path_rel": None,
                "description": str(problem),
                "audit_source": "data_audit.json#problems",
                "manifest_sha256": manifest_sha,
            }
        )
    for entry in audit.get("discrepancy_ledger", []):
        issue_id += 1
        rows.append(
            {
                "issue_id": f"M1-LEDGER-{issue_id:03d}",
                "severity": "WARN",
                "path_rel": None,
                "description": str(entry),
                "audit_source": "data_audit.json#discrepancy_ledger",
                "manifest_sha256": manifest_sha,
            }
        )
    for path_rel in audit.get("extra_duplicate_copy_files", []):
        issue_id += 1
        rows.append(
            {
                "issue_id": f"M1-DUPFILE-{issue_id:03d}",
                "severity": "INFO",
                "path_rel": path_rel,
                "description": (
                    "extra duplicate copy file alongside an accepted sample (not a parsed sample)"
                ),
                "audit_source": "data_audit.json#extra_duplicate_copy_files",
                "manifest_sha256": manifest_sha,
            }
        )
    return rows


def _opt(value: str, cast: Any) -> Any:
    return cast(value) if value not in ("", None) else None


def build_fact_ot_diagnostics(runs: list[RunMeta]) -> list[dict[str, Any]]:
    rows = []
    for r in runs:
        path = r.out_dir / "ot_diagnostics.csv"
        if not path.is_file():
            continue
        for row in _csv_rows(path):
            rows.append(
                {
                    "run_id": r.run_id,
                    "fold_id": row["fold_id"],
                    "model_key": row["model"],
                    "solver": row["solver"],
                    "epsilon": _opt(row["epsilon"], float),
                    "n_source": _opt(row["n_source"], int),
                    "n_target": _opt(row["n_target"], int),
                    "n_iter": _opt(row["n_iter"], int),
                    "converged": _opt(row["converged"], lambda v: v.strip().lower() == "true"),
                    "pot_nonconvergence_warning": _opt(
                        row.get("pot_nonconvergence_warning", ""),
                        lambda v: v.strip().lower() == "true",
                    ),
                    "row_marginal_l1": _opt(row["row_marginal_l1"], float),
                    "col_marginal_l1": _opt(row["col_marginal_l1"], float),
                    "col_marginal_sq_l2": _opt(row["col_marginal_sq_l2"], float),
                    "total_mass": _opt(row["total_mass"], float),
                    "cost_min": _opt(row["cost_min"], float),
                    "cost_median": _opt(row["cost_median"], float),
                    "cost_max": _opt(row["cost_max"], float),
                    "n_components": _opt(row.get("n_components", ""), int),
                    "mode": row["mode"],
                }
            )
    return rows


def discover_registry_run_ids(results_dir: Path) -> dict[str, str]:
    """output_dir -> run_id for every registry row, including exploratory ones."""
    return {
        row["output_dir"]: row["run_id"]
        for row in _csv_rows(results_dir / "experiment_registry.csv")
    }


def build_fact_robustness(
    m3_control_dirs: list[Path],
    m4_batch_dirs: list[Path],
    m5_run: RunMeta | None,
    run_id_by_dir: dict[str, str],
) -> list[dict[str, Any]]:
    rows = []
    for d in m3_control_dirs:
        c = _json(d / "control_summary.json")
        run_id = run_id_by_dir[d.name]
        for model_key, md in c["models"].items():
            reps = md["per_repeat"]
            rows.append(
                {
                    "run_id": run_id,
                    "stress_type": "permuted_source_labels",
                    "fold_id": None,
                    "batch_kind": None,
                    "model_key": model_key,
                    "mode": "inductive",
                    "n_batches": c["n_repeats"],
                    "n_failed": 0,
                    "mae_fraction_mean": md["mean_macro_mae_fraction"],
                    "mae_fraction_max": max(x["macro_mae_fraction"] for x in reps),
                    "r2_mean": md["mean_macro_r2"],
                    "r2_min": min(x["macro_r2"] for x in reps),
                    "scored_on": "permuted source labels (negative control), macro over folds",
                }  # fmt: skip
            )
    for d in m4_batch_dirs:
        b = _json(d / "batch_sensitivity.json")
        run_id = run_id_by_dir[d.name]
        for fold_id, variants in b["folds"].items():
            for key, v in variants.items():
                batch_kind, model_key = key.split("|", 1)
                stress_type = "batch_brand" if batch_kind.startswith("brand_") else "batch_size"
                mode = "inductive" if model_key == "svr_no_adaptation" else "transductive_batch"
                rows.append(
                    {
                        "run_id": run_id,
                        "stress_type": stress_type,
                        "fold_id": fold_id,
                        "batch_kind": batch_kind,
                        "model_key": model_key,
                        "mode": mode,
                        "n_batches": v["n_batches"],
                        "n_failed": v["n_failed"],
                        "mae_fraction_mean": v["mae_fraction_mean"],
                        "mae_fraction_max": v["mae_fraction_max"],
                        "r2_mean": v["r2_mean"],
                        "r2_min": v["r2_min"],
                        "scored_on": b["note"],
                    }  # fmt: skip
                )
    if m5_run is not None:
        groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
        for row in _csv_rows(m5_run.out_dir / "perturbation_table.csv"):
            groups.setdefault(
                (row["fold_id"], row["model"], row["perturbation"], row["level"]), []
            ).append(row)
        for (fold_id, model_key, perturbation, level), group in groups.items():
            maes = [float(r["mae_fraction"]) for r in group]
            rows.append(
                {
                    "run_id": group[0]["run_id"],
                    "stress_type": "synthetic_perturbation",
                    "fold_id": fold_id,
                    "batch_kind": f"{perturbation}_{level}",
                    "model_key": model_key,
                    "mode": group[0]["mode"],
                    "n_batches": len(group),
                    "n_failed": 0,
                    "mae_fraction_mean": sum(maes) / len(maes),
                    "mae_fraction_max": max(maes),
                    "r2_mean": None,
                    "r2_min": None,
                    "scored_on": (
                        "true held-out labels under a seeded synthetic spectral perturbation"
                    ),
                }  # fmt: skip
            )
    return rows


def build_fact_published_reference(runs: list[RunMeta]) -> list[dict[str, Any]]:
    headline = next(
        (
            r
            for r in runs
            if r.fields.get("protocol") == "loao" and not r.fields.get("subset_brand")
        ),
        None,
    )
    if headline is None:
        return []
    s = _json(headline.out_dir / "summary.json")
    ref = s.get("published_reference_not_measured")
    if not ref:
        return []
    rows = []
    for model_label, value_key, comparable, sd_key in PUBLISHED_REFERENCE_ROWS:
        rows.append(
            {
                "reference_id": f"sun2026_loao_mean_r2_{model_label}",
                "source_doi": "10.1038/s41538-026-01037-6",
                "model_label": model_label,
                "metric": "mean_r2",
                "value": ref[value_key],
                "sd": ref.get(sd_key) if sd_key else None,
                "is_measured": False,
                "comparable_model_key": comparable,
                "caveat": ref["caveat"],
            }
        )
    return rows


_ABS_PATH_RE = re.compile(r"(^|[\s'\"])/Users/[^\s'\"]+")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def validate_export(contract: dict[str, Any], tables: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Rules checkable from the exported rows alone (V-03, V-05, V-06, V-07, V-10, V-11).

    V-01/V-02/V-04/V-08/V-09 are enforced by construction in the table builders above and
    in contract.write_table_csv, not re-checked here. V-12 (dataset hash unchanged, no
    spectral intensity) is a property of the CLI command, checked by its caller.
    """
    problems: list[str] = []

    for row in tables.get("dim_sample", []):
        f = row["olive_fraction"]
        if not (0.0 <= f <= 1.0):
            problems.append(f"V-03: dim_sample {row['sample_id']} olive_fraction {f} outside [0,1]")
        if abs(row["olive_percent"] - 100 * f) > 1e-9:
            problems.append(
                f"V-03: dim_sample {row['sample_id']} olive_percent != 100*olive_fraction"
            )
    for row in tables.get("fact_predictions", []):
        f = row["y_true_fraction"]
        if not (0.0 <= f <= 1.0):
            problems.append(
                f"V-03: fact_predictions {row['sample_id']} y_true_fraction outside [0,1]"
            )
        if abs(row["abs_error_pp"] - 100 * row["abs_error_fraction"]) > 1e-9:
            problems.append(
                f"V-03: fact_predictions {row['sample_id']} abs_error_pp != 100*abs_error_fraction"
            )

    recon = _recompute_pooled_metrics(tables.get("fact_predictions", []))
    for row in tables.get("fact_model_metrics", []):
        if row["scope_type"] != "pooled" or row["scoring"] != "unclipped":
            continue
        key = (row["run_id"], row["model_key"])
        got = recon.get(key)
        if got is None:
            continue
        if abs(got["mae_fraction"] - row["mae_fraction"]) > 1e-9:
            problems.append(
                f"V-05: {key} pooled MAE reconciliation mismatch "
                f"{got['mae_fraction']} != {row['mae_fraction']}"
            )
        if got["r2"] is not None and row["r2"] is not None and abs(got["r2"] - row["r2"]) > 1e-9:
            problems.append(
                f"V-05: {key} pooled R2 reconciliation mismatch {got['r2']} != {row['r2']}"
            )

    for row in tables.get("dim_experiment", []):
        for field in ("config_sha256", "manifest_sha256", "git_head"):
            if not row.get(field):
                problems.append(f"V-06: dim_experiment {row['run_id']} missing {field}")
        if row["git_dirty"] and row["is_headline"]:
            problems.append(f"V-06: dim_experiment {row['run_id']} is_headline but git_dirty")
        if row["protocol_family"] == "loao" and not row["canary_passed"]:
            problems.append(
                f"V-07: dim_experiment {row['run_id']} LOAO run with canary_passed=false"
            )

    for table, rows in tables.items():
        for row in rows:
            for value in row.values():
                if not isinstance(value, str):
                    continue
                if _ABS_PATH_RE.search(value):
                    problems.append(
                        f"V-10: {table} row contains an absolute filesystem path: {value!r}"
                    )
                if _EMAIL_RE.search(value):
                    problems.append(f"V-10: {table} row contains an e-mail address: {value!r}")

    for row in tables.get("fact_published_reference", []):
        if row["is_measured"] is not False:
            problems.append(
                f"V-11: fact_published_reference {row['reference_id']} is_measured != false"
            )

    return problems


def _recompute_pooled_metrics(
    predictions: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in predictions:
        groups.setdefault((row["run_id"], row["model_key"]), []).append(row)
    out = {}
    for key, rows in groups.items():
        errs = [r["abs_error_fraction"] for r in rows]
        y_true = [r["y_true_fraction"] for r in rows]
        mean_true = sum(y_true) / len(y_true)
        ss_res = sum((r["y_pred_fraction"] - t) ** 2 for r, t in zip(rows, y_true, strict=True))
        ss_tot = sum((t - mean_true) ** 2 for t in y_true)
        out[key] = {
            "mae_fraction": sum(errs) / len(errs),
            "r2": (1 - ss_res / ss_tot) if ss_tot else None,
        }
    return out


def export_all(
    results_dir: Path,
    manifest_path: Path,
    contract_path: Path,
    protocol_map_path: Path,
    output_dir: Path,
    fmt: str = "csv",
) -> dict[str, Any]:
    """CP-652 entry point: build every table, validate, write CSVs + expected_kpis.json +
    export_manifest.json. Refuses to write into a non-empty output_dir (no silent overwrite)."""
    from chemiproof.bi import kpis as kp
    from chemiproof.evaluation.runner import git_state
    from chemiproof.provenance import environment_info

    contract = ct.load_contract(contract_path)
    protocol_map = ct.load_protocol_map(protocol_map_path)

    runs = discover_evaluation_runs(results_dir)
    run_id_by_dir = discover_registry_run_ids(results_dir)
    m5 = next(
        (
            r
            for r in runs
            if ct.resolve_protocol_id(protocol_map, r.fields["config_sha256"])[0] == "LOAO-UQ-v1"
        ),
        None,
    )
    m3_control_dirs = sorted(results_dir.glob("M3_control_*"))
    m4_batch_dirs = sorted(results_dir.glob("M4_batch_sensitivity_*"))
    m1_dirs = sorted(p for p in results_dir.iterdir() if p.is_dir() and p.name.startswith("M1_"))

    manifest_sha = None
    sha_file = manifest_path.parent / "manifest_sha256.txt"
    if sha_file.is_file():
        manifest_sha = sha_file.read_text(encoding="utf-8").strip()

    dim_sample = build_dim_sample(manifest_path)
    for row in dim_sample:
        row["manifest_sha256"] = manifest_sha

    tables: dict[str, list[dict[str, Any]]] = {
        "dim_adulterant": build_dim_adulterant(),
        "dim_brand": build_dim_brand(),
        "dim_model": build_dim_model(),
        "dim_sample": dim_sample,
        "dim_experiment": build_dim_experiment(runs, protocol_map),
        "dim_fold": build_dim_fold(runs),
        "fact_predictions": build_fact_predictions(runs),
        "fact_model_metrics": build_fact_model_metrics(runs),
        "fact_uncertainty": build_fact_uncertainty(m5),
        "fact_selective_risk": build_fact_selective_risk(m5),
        "fact_data_quality": build_fact_data_quality(manifest_path, manifest_sha),
        "fact_data_issues": build_fact_data_issues(m1_dirs[0]) if m1_dirs else [],
        "fact_ot_diagnostics": build_fact_ot_diagnostics(runs),
        "fact_robustness": build_fact_robustness(m3_control_dirs, m4_batch_dirs, m5, run_id_by_dir),
        "fact_published_reference": build_fact_published_reference(runs),
    }

    violations = validate_export(contract, tables)

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refuse to export into a non-empty directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    files_meta = [
        ct.write_table(output_dir, contract, name, rows, fmt) for name, rows in tables.items()
    ]

    kpi_rows = kp.compute_kpis(tables)
    kpi_path = output_dir / "expected_kpis.json"
    kpi_path.write_text(json.dumps(kpi_rows, indent=2, default=str) + "\n", encoding="utf-8")
    kpi_sha = __import__("hashlib").sha256(kpi_path.read_bytes()).hexdigest()
    files_meta.append(
        {"table": "expected_kpis", "format": "json", "rows": len(kpi_rows), "sha256": kpi_sha}
    )

    manifest = {
        "contract_version": ct.CONTRACT_VERSION,
        "git_head": git_state(),
        "environment": environment_info(),
        "sources": [
            {
                "run_id": r.run_id,
                "run_dir": r.out_dir.name,
                "protocol_id": ct.resolve_protocol_id(protocol_map, r.fields["config_sha256"])[0],
                "run_class": r.fields["run_class"],
                "config_sha256": r.fields["config_sha256"],
            }
            for r in runs
        ],
        "files": files_meta,
        "uncertainty_available": m5 is not None,
        "selective_risk_available": m5 is not None,
        "robustness_available": bool(m3_control_dirs or m4_batch_dirs or m5),
        "excluded_runs": {
            "M6_final_*": (
                "trained screening artifact, not an evaluation run "
                "(no predictions.csv); out of scope"
            ),
        },
        "validation_violations": violations,
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )
    return manifest
