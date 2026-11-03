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
    TRANSDUCTIVE_KEYS,
    RunOutput,
    git_state,
    run_models,
    run_transductive,
    summarize,
    write_run_artifacts,
)
from chemiproof.modeling.baselines import MODEL_KEYS, SEED
from chemiproof.modeling.ot import TRANSDUCTIVE_WARNING, OTConfig
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

OT_LIMITATIONS = [
    TRANSDUCTIVE_WARNING,
    "Each fold uses the WHOLE held-out adulterant (30-90 spectra spanning all ten levels and every "
    "brand of that adulterant) as the unlabeled batch; a batch with a different composition (fewer "
    "samples, one level, one brand) is a different problem (see the batch-sensitivity run).",
    "Only the target-batch FEATURES are read; target labels are used for scoring only (canary: "
    "shuffling them changes nothing). This is still not an inductive protocol: compare with "
    "svr_no_adaptation, which uses the same SVR and features without the batch.",
    "Our OT solver is an independent log-domain implementation; ot_svr_pot calls POT the way the "
    "authors describe. Their gap quantifies solver sensitivity of the polynomial SVR.",
    "author_pca50/author_pca10 are published-style PCA baselines fitted on source + unlabeled "
    "target X with prespecified sizes; the authors' 'PARAFAC-10' column is PCA with 10 components "
    "in their code. CORAL/MMD are not reproduced: the authors tune their size on target labels.",
    "Brand imbalance, five folds, one instrument, laboratory binary mixtures: see LOAO-v1 limits.",
    "Published numbers are shown separately and were not measured by ChemiProof; the authors clip "
    "predictions to [0, 1], we score unclipped (clipped values are reported as secondary).",
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


def _ot_config(cfg: ExperimentConfig) -> OTConfig:
    raw = cfg.model_dump().get("optimal_transport") or {}
    if raw.get("method") != "entropic_sinkhorn_barycentric_projection":
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG,
            "optimal_transport.method must be entropic_sinkhorn_barycentric_projection",
        )
    if raw.get("cost") != "euclidean_unnormalized":
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG, "only the euclidean_unnormalized cost is defined"
        )
    return OTConfig(float(raw["epsilon"]), int(raw["max_iter"]), float(raw["tol"]))


def _ot_dict(c: OTConfig | None) -> dict[str, Any]:
    return {"epsilon": c.epsilon, "max_iter": c.max_iter, "tol": c.tol} if c else {}


def _write_diagnostics(path: Path, diags: list[dict[str, Any]]) -> None:
    cols = list(dict.fromkeys(k for d in diags for k in d))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(diags)


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


def _diag(o: RunOutput, fold_id: str) -> list[Any]:
    return [
        {k: v for k, v in d.items() if k != "run_id"}
        for d in o.diagnostics
        if d["fold_id"] == fold_id
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
    run_fn: Any = None,
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
        alt = (run_fn or run_models)(ds.rows, X, y_c, [fold], keys, groups, run_id)

        fid = fold.fold_id
        same = (
            _preds(base, fid) == _preds(alt, fid)
            and _selected(base, fid) == _selected(alt, fid)
            and _diag(base, fid) == _diag(alt, fid)
        )
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
        "| model | mode | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | "
        "worst fold (MAE) |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for k, s in summary.items():
        m = s[key]
        lines.append(
            f"| {k} | {s.get('mode', '')} | {100 * m['mae_fraction']:.2f} | "
            f"{m['rmse_fraction']:.4f} | {m['bias_fraction']:+.4f} | {m['r2']:.3f} | "
            f"{m['r2_std_across_folds']:.3f} | "
            f"{s['worst_fold']} ({100 * m['worst_fold_mae_fraction']:.2f} pp) |"
        )
    return lines


def _markdown_report(
    run_id: str,
    protocol: str,
    summary: dict[str, Any],
    out: RunOutput,
    subset: str | None,
    mode: str = "inductive",
) -> str:
    head = {
        "source_internal_loro": "source-internal evaluation (leave-one-round-out; OPTIMISTIC)",
        "loao": (
            "five-domain LOAO benchmark, TRANSDUCTIVE (OT) mode"
            if mode == "transductive_batch"
            else "five-domain LOAO benchmark (inductive)"
        )
        + (f" restricted to brand {subset}" if subset else ""),
    }[protocol]
    lines = [f"# Run {run_id}: {head}", ""]
    if mode == "transductive_batch":
        lines += [f"> **{TRANSDUCTIVE_WARNING}**", ""]
    lines += [
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
        "| fold | model | mode | n | MAE (pp) | RMSE | bias | R2 | out of [0,1] |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in out.fold_metrics:
        lines.append(
            f"| {r['fold_id']} | {r['model']} | {r['mode']} | {r['n']} | "
            f"{100 * r['mae_fraction']:.2f} | {r['rmse_fraction']:.4f} | "
            f"{r['bias_fraction']:+.4f} | {r['r2']:.3f} | {r['n_out_of_range']} |"
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
    transductive = cfg.mode == "transductive_batch"
    if transductive and cfg.protocol != "loao":
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG, "transductive runs are defined for the LOAO protocol only"
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
    keys = list(cfg.models or (TRANSDUCTIVE_KEYS if transductive else MODEL_KEYS))
    ot_cfg = _ot_config(cfg) if transductive else None

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
        prefix, limits = ("M4", OT_LIMITATIONS) if transductive else ("M3", LOAO_LIMITATIONS)
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

    if transductive:

        def run_fn(rows_, X_, y_, folds_, keys_, groups_, run_id_):  # same args as run_models
            return run_transductive(rows_, X_, y_, folds_, keys_, ot_cfg, run_id_)

        out = run_fn(ds.rows, X, y, folds, keys, groups, run_id)
    else:
        run_fn = None
        out = run_models(ds.rows, X, y, folds, keys, groups, run_id)
    summary = summarize(out, keys, ds.rows)
    out_dir = output_root / f"{prefix}_{run_id}"
    write_run_artifacts(
        out_dir, run_id, resolved, manifest_sha, ds.rows, folds, out, summary, limits
    )

    extra: dict[str, Any] = {}
    if cfg.protocol == "loao":
        canary = _label_canary(ds, X, y, folds, keys, groups, out, run_id, run_fn)
        audit = {"fold_audit": fold_audit, "label_shuffle_canary": canary}
        (out_dir / "leakage_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        _write_fold_manifest(out_dir / "fold_manifest.csv", fold_audit)
        plot_mae_r2_by_fold(out.fold_metrics, out_dir / "mae_r2_by_fold.png")
        plot_parity(out.predictions, out_dir / "parity_by_model.png")
        if transductive:
            _write_diagnostics(out_dir / "ot_diagnostics.csv", out.diagnostics)
        extra = {
            "published_reference_not_measured": PUBLISHED_REFERENCE,
            "mode": cfg.mode,
            **(
                {
                    "transductive_warning": TRANSDUCTIVE_WARNING,
                    "optimal_transport": _ot_dict(ot_cfg),
                }
                if transductive
                else {}
            ),
            "run_class": cfg.run_class,
            "subset_brand": cfg.subset_brand,
            "leakage_audit": {"fold_audit_checks": fold_audit["checks"], "canary_passed": True},
        }
        full = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
        full.update(extra)
        (out_dir / "summary.json").write_text(json.dumps(full, indent=2), encoding="utf-8")

    (out_dir / "run_report.md").write_text(
        _markdown_report(run_id, cfg.protocol, summary, out, cfg.subset_brand, cfg.mode),
        encoding="utf-8",
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


def _batch_predict(
    name: str, xs: np.ndarray, ys: np.ndarray, xt: np.ndarray, ot_cfg: OTConfig
) -> np.ndarray:
    from chemiproof.modeling.ot import ot_svr_fit_predict, svr_no_adaptation_fit_predict

    if name == "ot_svr":
        return ot_svr_fit_predict(xs, ys, xt, ot_cfg).y_pred
    return svr_no_adaptation_fit_predict(xs, ys, xt).y_pred


BATCH_SIZES = (10, 20)  # prespecified in ADR-014, never tuned
BATCH_REPEATS = 5


def run_ot_batch_sensitivity(
    cfg: ExperimentConfig, data_dir: Path, manifest: Path, output_root: Path
) -> Path:
    """Exploratory: how does OT behave when the unlabeled target batch is SMALLER or covers ONE
    brand only? Prespecified subsets (sizes 10 and 20, 5 seeded draws each; every single-brand
    batch inside a fold). Scored against the true labels of the subset only; adaptation uses the
    subset's features only. Compared with the same SVR without adaptation on the same subsets."""
    from chemiproof.evaluation.metrics import compute_metrics

    if cfg.mode != "transductive_batch" or cfg.protocol != "loao":
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "batch sensitivity needs the OT config")
    ot_cfg = _ot_config(cfg)
    ds = _subset(load_dataset(manifest, data_dir), cfg.subset_brand)
    X = preprocess_features(ds.spectra, AUTHOR_V1)
    y = ds.y
    folds = loao_folds(ds.rows)
    results: dict[str, Any] = {}
    for fold in folds:
        xs, ys = X[fold.train_idx], y[fold.train_idx]
        te = fold.test_idx
        brands = np.array([ds.rows[i].evoo_brand for i in te])
        batches: list[tuple[str, np.ndarray]] = []
        for k in BATCH_SIZES:
            for rep in range(BATCH_REPEATS):
                rng = np.random.default_rng(SEED + 200 + 10 * k + rep)
                batches.append((f"random_{k}", rng.choice(len(te), size=k, replace=False)))
        if len(set(brands.tolist())) > 1:
            batches += [(f"brand_{b}", np.flatnonzero(brands == b)) for b in sorted(set(brands))]
        rows_out: dict[str, list[dict[str, float]]] = {}
        for label, sel in batches:
            xt = X[te][sel]
            for name in ("ot_svr", "svr_no_adaptation"):
                try:
                    pred = _batch_predict(name, xs, ys, xt, ot_cfg)
                    m = compute_metrics(y[te][sel], pred)
                    rec = {
                        "mae_fraction": m.mae_fraction,
                        "r2": m.r2,
                        "bias_fraction": m.bias_fraction,
                    }
                except ChemiProofError as exc:
                    rec = {"error": exc.code.value}
                rows_out.setdefault(f"{label}|{name}", []).append(rec)
        agg: dict[str, Any] = {}
        for key, recs in rows_out.items():
            ok = [r for r in recs if "error" not in r]
            agg[key] = {
                "n_batches": len(recs),
                "n_failed": len(recs) - len(ok),
                **(
                    {
                        "mae_fraction_mean": float(np.mean([r["mae_fraction"] for r in ok])),
                        "mae_fraction_max": float(np.max([r["mae_fraction"] for r in ok])),
                        "r2_mean": float(np.mean([r["r2"] for r in ok])),
                        "r2_min": float(np.min([r["r2"] for r in ok])),
                    }
                    if ok
                    else {}
                ),
            }
        results[fold.fold_id] = agg
    run_id = make_run_id(
        {"batch_sensitivity": cfg.experiment_id, "manifest": file_sha256(manifest)}
    )
    out_dir = output_root / f"M4_batch_sensitivity_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "experiment_id": cfg.experiment_id,
        "subset_brand": cfg.subset_brand,
        "sizes": list(BATCH_SIZES),
        "repeats": BATCH_REPEATS,
        "note": "exploratory; metrics on the SUBSET batch; adaptation uses subset features only",
        "warning": TRANSDUCTIVE_WARNING,
        "folds": results,
    }
    (out_dir / "batch_sensitivity.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    _append_registry(
        output_root,
        run_id,
        cfg,
        "batch_sensitivity",
        out_dir,
        protocol="loao_ot_batch_sensitivity",
        run_class="exploratory",
    )
    return out_dir
