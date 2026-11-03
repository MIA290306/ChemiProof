"""M5 runner (protocol LOAO-UQ-v1, ADR-017): abstention, intervals, robustness. INDUCTIVE only.

`compute_fold` never indexes held-out labels: it reads y only at TRAIN rows. A label-shuffle
canary re-runs it with the held-out labels permuted and requires identical decisions.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np

from chemiproof.config import ExperimentConfig
from chemiproof.data.manifest import ManifestRow
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.evaluation.protocols import Fold, audit_folds, loao_folds
from chemiproof.logging_utils import log_event
from chemiproof.modeling.baselines import SEED, SelectedModel, make_base_estimator, model_factory
from chemiproof.pipeline import Dataset, load_dataset
from chemiproof.provenance import config_hash, environment_info, file_sha256, make_run_id
from chemiproof.spectra.preprocess import AUTHOR_V1, preprocess_features, preprocess_intensity
from chemiproof.uncertainty import perturb
from chemiproof.uncertainty.calibration import interval_halfwidths, retention_thresholds
from chemiproof.uncertainty.scores import MahalanobisScorer, model_disagreement
from chemiproof.uncertainty.selective import (
    oracle_curve,
    random_curve,
    rank_curve,
    score_error_spearman,
    selective_stats,
)

PROTOCOL_ID = "LOAO-UQ-v1"
SCORES = ("ood_maha", "model_disagreement")
UQ_LIMITATIONS = [
    "Five held-out adulterant systems only; one instrument and laboratory; laboratory binary "
    "mixtures. A favourable result here says nothing about other systems or deployment.",
    "Intervals and thresholds come from SOURCE-only cross-fitted residuals and scores. Under a new "
    "adulterant the exchangeability assumption fails, so observed coverage is empirical and no "
    "coverage guarantee exists. Calibration residuals are slightly optimistic because the outer "
    "hyper-parameters were chosen by inner CV that also saw each calibration adulterant.",
    "Abstention is a research-level risk cue, not a safety or regulatory decision, and not a "
    "guaranteed out-of-distribution detector.",
    "Brand imbalance (walnut = 1 brand) is an uncontrolled confounder; brand breakdowns are "
    "descriptive.",
    "Inductive mode only. The design was written after M3/M4 outer errors were seen (ADR-017 "
    "disclosure); no constant was tuned on a held-out adulterant.",
]


@dataclass
class FoldResult:
    fold_id: str
    test_idx: np.ndarray
    models: dict[str, SelectedModel]
    scorer: MahalanobisScorer
    pred: dict[str, np.ndarray]
    score: dict[str, np.ndarray]  # score name -> per test sample
    halfwidth: dict[str, dict[str, float]]  # model -> variant -> q
    threshold: dict[str, dict[float, float]]  # score -> goal -> threshold
    n_cal: int
    selected: dict[str, Any]


def _uq(cfg: ExperimentConfig) -> dict[str, Any]:
    uq = cfg.model_dump().get("uncertainty")
    if not uq or uq.get("protocol_id") != PROTOCOL_ID:
        raise ChemiProofError(StatusCode.INVALID_CONFIG, f"config must declare {PROTOCOL_ID}")
    return uq


def compute_fold(
    X: np.ndarray,
    y: np.ndarray,
    adul: np.ndarray,
    fold: Fold,
    keys: list[str],
    uq: dict[str, Any],
) -> FoldResult:
    """Fit on train rows only; calibrate by leaving each SOURCE adulterant out in turn."""
    tr, te = fold.train_idx, fold.test_idx
    models = {k: model_factory(k)().fit(X[tr], y[tr], groups=adul[tr]) for k in keys}
    pred = {k: models[k].predict(X[te]) for k in keys}
    ncomp = {k: models[k].selected_.get("n_components") for k in keys}
    k_pca = int(uq["pca_components_for_ood"])
    scorer = MahalanobisScorer(k_pca).fit(X[tr])
    score = {"ood_maha": scorer.score(X[te]), "model_disagreement": model_disagreement(pred)}

    res: dict[str, dict[str, np.ndarray]] = {k: {} for k in keys}
    cal_scores: dict[str, list[np.ndarray]] = {s: [] for s in SCORES}
    for s in sorted(set(adul[tr].tolist())):
        held = tr[adul[tr] == s]
        fit = tr[adul[tr] != s]
        cal_pred = {}
        for k in keys:
            est = make_base_estimator(k, ncomp[k]).fit(X[fit], y[fit])  # hyper-params fixed
            cal_pred[k] = np.asarray(est.predict(X[held])).reshape(-1)
            res[k][s] = y[held] - cal_pred[k]
        cal_scores["ood_maha"].append(MahalanobisScorer(k_pca).fit(X[fit]).score(X[held]))
        cal_scores["model_disagreement"].append(model_disagreement(cal_pred))

    lvl = float(uq["interval"]["nominal_level"])
    halfwidth = {
        k: interval_halfwidths(
            res[k], lvl, int(uq["min_calibration_points"]), int(uq["min_calibration_groups"])
        )
        for k in keys
    }
    goals = [float(g) for g in uq["retention_goals"]]
    threshold = {s: retention_thresholds(np.concatenate(cal_scores[s]), goals) for s in SCORES}
    n_cal = int(sum(a.size for a in cal_scores["ood_maha"]))
    return FoldResult(
        fold.fold_id, te, models, scorer, pred, score, halfwidth, threshold, n_cal,
        {k: models[k].selected_.get("n_components") for k in keys},
    )  # fmt: skip


def _same(a: FoldResult, b: FoldResult) -> bool:
    return (
        all(np.array_equal(a.pred[k], b.pred[k]) for k in a.pred)
        and all(np.array_equal(a.score[s], b.score[s]) for s in a.score)
        and a.halfwidth == b.halfwidth
        and a.threshold == b.threshold
        and a.selected == b.selected
    )


def label_canary(
    X: np.ndarray, y: np.ndarray, adul: np.ndarray, folds: list[Fold], keys: list[str],
    uq: dict[str, Any], base: dict[str, FoldResult],
) -> dict[str, Any]:  # fmt: skip
    """Shuffle held-out labels: predictions, scores, intervals and thresholds must not move."""
    out = []
    for fold in folds:
        y_c = y.copy()
        rng = np.random.default_rng(SEED + 1)
        sh = rng.permutation(y[fold.test_idx])
        if np.array_equal(sh, y[fold.test_idx]):
            sh = np.roll(sh, 1)
        y_c[fold.test_idx] = sh
        alt = compute_fold(X, y_c, adul, fold, keys, uq)
        same = _same(base[fold.fold_id], alt)
        out.append({"fold_id": fold.fold_id, "heldout_labels_shuffled": True, "unchanged": same})
        if not same:
            raise ChemiProofError(
                StatusCode.QC_REVIEW_REQUIRED,
                "LEAKAGE: shuffling held-out labels changed abstention/interval inputs",
                fold=fold.fold_id,
            )
    return {"passed": True, "folds": out}


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def _evaluate(
    run_id: str, rows: list[ManifestRow], y: np.ndarray, folds: list[Fold],
    results: dict[str, FoldResult], keys: list[str], uq: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:  # fmt: skip
    """All tables. Held-out labels y[te] are read here, AFTER every decision exists."""
    goals = [float(g) for g in uq["retention_goals"]]
    pct = [int(p) for p in uq["curve_retention_percent"]]
    reps = int(uq["random_rejection_repeats"])
    lvl = float(uq["interval"]["nominal_level"])
    T: dict[str, list[dict[str, Any]]] = {
        n: [] for n in ("predictions", "selective", "curve", "coverage", "diag", "brand", "fail")
    }
    for fold in folds:
        r = results[fold.fold_id]
        te = fold.test_idx
        yt = y[te]
        for k in keys:
            yh = r.pred[k]
            ae = np.abs(yh - yt)
            hw = r.halfwidth[k]
            abst80 = {s: r.score[s] > r.threshold[s][0.8] for s in SCORES}
            for i, idx in enumerate(te):
                row = {
                    "run_id": run_id, "fold_id": fold.fold_id, "model": k, "mode": "inductive",
                    "protocol_id": PROTOCOL_ID, "source_sample_hash": rows[idx].sha256,
                    "sample_id": rows[idx].sample_id, "y_true_fraction": float(yt[i]),
                    "y_pred_fraction": float(yh[i]), "ood_score": float(r.score["ood_maha"][i]),
                    "model_disagreement": float(r.score["model_disagreement"][i]),
                    "abstain": bool(abst80["ood_maha"][i]),  # primary score, goal 0.80
                    "interval_lo": float(yh[i] - hw["pooled"]),
                    "interval_hi": float(yh[i] + hw["pooled"]),
                    "interval_lo_max_domain": float(yh[i] - hw["max_domain"]),
                    "interval_hi_max_domain": float(yh[i] + hw["max_domain"]),
                }  # fmt: skip
                T["predictions"].append(row)
            for variant, q in hw.items():
                lo, hi = yh - q, yh + q
                T["coverage"].append({
                    "run_id": run_id, "fold_id": fold.fold_id, "model": k, "variant": variant,
                    "nominal_level": lvl, "half_width_fraction": q,
                    "observed_coverage": float(np.mean((yt >= lo) & (yt <= hi))),
                    "mean_width_fraction": 2 * q,
                    "mean_width_clipped_fraction": float(
                        np.mean(np.clip(hi, 0, 1) - np.clip(lo, 0, 1))),
                    "n": int(yt.size), "mode": "inductive",
                    "note": "empirical coverage; no guarantee under adulterant shift",
                })  # fmt: skip
            for s in SCORES:
                sc = r.score[s]
                for g in goals:
                    thr = r.threshold[s][g]
                    st = selective_stats(ae, sc > thr)
                    T["selective"].append({
                        "run_id": run_id, "fold_id": fold.fold_id, "model": k, "score": s,
                        "retention_goal": g, "threshold": thr,
                        "full_mae_fraction": float(ae.mean()),
                        "mode": "inductive", **st})  # fmt: skip
                rk = rank_curve(ae, sc, pct)
                rd = random_curve(ae, pct, reps, SEED)
                orc = oracle_curve(ae, pct)
                for j, p in enumerate(pct):
                    T["curve"].append({
                        "run_id": run_id, "fold_id": fold.fold_id, "model": k, "score": s,
                        "retention_percent": p, "rank_selective_mae": rk[j],
                        "random_mean": rd["mean"][j], "random_p05": rd["p05"][j],
                        "random_p95": rd["p95"][j], "oracle_mae_diagnostic": orc[j],
                    })  # fmt: skip
                T["diag"].append({
                    "run_id": run_id, "fold_id": fold.fold_id, "model": k, "score": s,
                    "spearman_score_vs_abs_error": score_error_spearman(ae, sc),
                    "mean_score": float(sc.mean()), "max_score": float(sc.max()),
                    "source_threshold_r0.9": r.threshold[s][0.9],
                    "source_threshold_r0.8": r.threshold[s][0.8],
                    "n_calibration": r.n_cal,
                })  # fmt: skip
            brands = np.array([rows[i].evoo_brand for i in te])
            for b in sorted(set(brands.tolist())):
                m = brands == b
                T["brand"].append({
                    "run_id": run_id, "fold_id": fold.fold_id, "model": k, "brand": b,
                    "n": int(m.sum()), "mae_fraction": float(ae[m].mean()),
                    "abstain_rate_ood_maha_r0.8": float(abst80["ood_maha"][m].mean()),
                })  # fmt: skip
            for i in np.argsort(-ae)[:5]:
                T["fail"].append({
                    "run_id": run_id, "fold_id": fold.fold_id, "model": k,
                    "sample_id": rows[te[i]].sample_id, "brand": rows[te[i]].evoo_brand,
                    "y_true_fraction": float(yt[i]), "y_pred_fraction": float(yh[i]),
                    "abs_error_fraction": float(ae[i]),
                    "ood_score": float(r.score["ood_maha"][i]),
                    "abstained_ood_maha_r0.8": bool(abst80["ood_maha"][i]),
                })  # fmt: skip
    return T


def usefulness(sel: list[dict[str, Any]], curve: list[dict[str, Any]], keys: list[str],
               uq: dict[str, Any]) -> dict[str, Any]:  # fmt: skip
    """Rule fixed in ADR-017: >= 4/5 folds improved (threshold-based at goal 0.8) AND rank-based
    selective MAE at 80 % below the random-rejection 5th percentile in >= 4/5 folds."""
    rule = uq["usefulness_rule"]
    out: dict[str, Any] = {"rule": rule, "verdicts": {}}
    for k in keys:
        for s in SCORES:
            a = [r for r in sel if r["model"] == k and r["score"] == s
                 and r["retention_goal"] == rule["goal"]]  # fmt: skip
            imp = sum(
                1 for r in a if r["n_retained"] > 0 and r["selective_mae"] < r["full_mae_fraction"]
            )
            c = [r for r in curve if r["model"] == k and r["score"] == s
                 and r["retention_percent"] == int(rule["goal"] * 100)]  # fmt: skip
            beat = sum(1 for r in c if r["rank_selective_mae"] < r["random_p05"])
            ok = imp >= rule["min_folds_improved"] and beat >= rule["must_beat_random_p05_in_folds"]
            out["verdicts"][f"{k}/{s}"] = {
                "folds_threshold_improved": imp, "folds_beat_random_p05": beat,
                "n_folds": len(a), "useful_on_this_benchmark": bool(ok),
            }  # fmt: skip
    return out


def _perturbation_table(
    ds: Dataset, X: np.ndarray, y: np.ndarray, folds: list[Fold],
    results: dict[str, FoldResult], keys: list[str], uq: dict[str, Any], run_id: str,
) -> list[dict[str, Any]]:  # fmt: skip
    pcfg = _perturb_cfg(uq)
    settings: list[tuple[str, float, int | None]] = []
    settings += [
        ("noise", f, s) for f in pcfg["noise_fraction_of_max"] for s in pcfg["noise_seeds"]
    ]
    settings += [("offset", g, None) for g in pcfg["baseline_offset_fraction_of_max"]]
    settings += [("scale", c, None) for c in pcfg["intensity_scale"]]
    out: list[dict[str, Any]] = []
    for fi, fold in enumerate(folds):
        r = results[fold.fold_id]
        te = fold.test_idx
        base_x = X[te]
        thr = r.threshold["ood_maha"][0.8]
        for kind, level, seed in [("clean", 0.0, None), *settings]:
            if kind == "clean":
                Xp = base_x
            else:
                rng = np.random.default_rng([seed if seed is not None else 0, fi])
                feats = []
                for i in te:
                    raw = ds.spectra[i].intensity
                    if kind == "noise":
                        raw = perturb.add_noise(raw, level, rng)
                    elif kind == "offset":
                        raw = perturb.add_offset(raw, level)
                    else:
                        raw = perturb.scale(raw, level)
                    feats.append(preprocess_intensity(raw, AUTHOR_V1).reshape(-1))
                Xp = np.stack(feats)
            sc = r.scorer.score(Xp)
            for k in keys:
                yh = np.asarray(r.models[k].predict(Xp)).reshape(-1)
                out.append({
                    "run_id": run_id, "fold_id": fold.fold_id, "model": k,
                    "perturbation": kind, "level": level, "seed": "" if seed is None else seed,
                    "mae_fraction": float(np.mean(np.abs(yh - y[te]))),
                    "max_abs_feature_change": float(np.max(np.abs(Xp - base_x))),
                    "mean_ood_score": float(sc.mean()),
                    "abstain_rate_ood_maha_r0.8": float(np.mean(sc > thr)),
                    "mode": "inductive",
                })  # fmt: skip
    return out


def _perturb_cfg(uq_root_cfg: dict[str, Any]) -> dict[str, Any]:
    return uq_root_cfg["_perturbations"]


def run_uncertainty(
    cfg: ExperimentConfig, data_dir: Path, manifest: Path, output_root: Path
) -> Path:
    from chemiproof.evaluation.runner import git_state
    from chemiproof.experiments import _append_registry

    uq = dict(_uq(cfg))
    uq["_perturbations"] = cfg.model_dump().get("perturbations") or {}
    if cfg.mode != "inductive" or cfg.protocol != "loao":
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "LOAO-UQ-v1 is inductive LOAO only")
    if (cfg.model_dump().get("preprocessing") or {}).get("version") != AUTHOR_V1.version:
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "preprocessing must be author_v1")
    if cfg.random_seed != SEED:
        raise ChemiProofError(StatusCode.INVALID_CONFIG, f"random_seed must be {SEED}")
    if cfg.run_class == "locked" and git_state()["dirty"]:
        raise ChemiProofError(
            StatusCode.INVALID_CONFIG, "a locked run needs a clean tracked git tree"
        )
    keys = list(cfg.models or ("svr_raw", "pca_svr", "pls"))

    ds = load_dataset(manifest, data_dir)
    manifest_sha = file_sha256(manifest)
    X = preprocess_features(ds.spectra, AUTHOR_V1)
    y = ds.y
    adul = np.array([r.adulterant_type for r in ds.rows])
    folds = loao_folds(ds.rows)
    if len(folds) != 5:
        raise ChemiProofError(StatusCode.QC_REVIEW_REQUIRED, f"expected 5 folds, got {len(folds)}")
    try:
        fold_audit = audit_folds(ds.rows, folds, expect_full=cfg.subset_brand is None)
    except ValueError as exc:
        raise ChemiProofError(StatusCode.QC_REVIEW_REQUIRED, f"fold audit failed: {exc}") from exc

    resolved: dict[str, Any] = {
        **{k: v for k, v in cfg.model_dump().items()},
        "protocol_id": PROTOCOL_ID,
        "preprocessing_resolved": AUTHOR_V1.as_dict(),
        "manifest_sha256": manifest_sha,
        "n_samples": len(ds.rows),
    }
    resolved["_config_sha256"] = config_hash(resolved)
    run_id = make_run_id(resolved)

    results: dict[str, FoldResult] = {}
    for fold in folds:
        results[fold.fold_id] = compute_fold(X, y, adul, fold, keys, uq)
        log_event("uq_fold_done", fold=fold.fold_id, protocol=PROTOCOL_ID)
    canary = label_canary(X, y, adul, folds, keys, uq, results)

    T = _evaluate(run_id, ds.rows, y, folds, results, keys, uq)
    verdict = usefulness(T["selective"], T["curve"], keys, uq)
    T["perturbation"] = _perturbation_table(ds, X, y, folds, results, keys, uq, run_id)

    # ablation: author_v1 without Savitzky-Golay, ranking quality only (ADR-017, exploratory)
    X_ns = preprocess_features(ds.spectra, replace(AUTHOR_V1, smooth_axes=()))
    abl = []
    for fold in folds:
        r2 = compute_fold(X_ns, y, adul, fold, keys, uq)
        for k in keys:
            ae = np.abs(r2.pred[k] - y[fold.test_idx])
            for s in SCORES:
                abl.append({
                    "run_id": run_id, "fold_id": fold.fold_id, "model": k, "score": s,
                    "variant": "author_v1_without_savgol",
                    "mae_fraction": float(ae.mean()),
                    "spearman_score_vs_abs_error": score_error_spearman(ae, r2.score[s]),
                })  # fmt: skip
    T["ablation"] = abl

    out_dir = output_root / f"M5_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    import yaml

    (out_dir / "config_resolved.yaml").write_text(
        yaml.safe_dump(resolved, sort_keys=True, allow_unicode=True), encoding="utf-8"
    )
    (out_dir / "environment.json").write_text(json.dumps(environment_info(), indent=2), "utf-8")
    (out_dir / "git_state.json").write_text(json.dumps(git_state(), indent=2), "utf-8")
    (out_dir / "dataset_manifest_sha256.txt").write_text(manifest_sha + "\n", "utf-8")
    (out_dir / "leakage_audit.json").write_text(
        json.dumps({"fold_audit": fold_audit, "label_shuffle_canary": canary}, indent=2), "utf-8"
    )
    names = {
        "predictions": "predictions.csv", "selective": "selective_risk.csv",
        "curve": "risk_coverage_curve.csv", "coverage": "interval_coverage.csv",
        "diag": "score_diagnostics.csv", "brand": "brand_breakdown.csv",
        "fail": "failure_cases.csv", "perturbation": "perturbation_table.csv",
        "ablation": "ablation_no_savgol.csv",
    }  # fmt: skip
    for key, fname in names.items():
        _write_csv(out_dir / fname, T[key])
    (out_dir / "usefulness.json").write_text(json.dumps(verdict, indent=2), "utf-8")
    summary = {
        "run_id": run_id, "protocol_id": PROTOCOL_ID, "mode": "inductive",
        "config_sha256": resolved["_config_sha256"], "manifest_sha256": manifest_sha,
        "git": git_state(), "run_class": cfg.run_class,
        "units": "errors/widths: olive volume FRACTION (0.01 = 1 percentage point)",
        "usefulness": verdict, "limitations": UQ_LIMITATIONS,
        "leakage_audit": {"canary_passed": canary["passed"], "fold_audit": fold_audit["checks"]},
    }  # fmt: skip
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), "utf-8")
    from chemiproof.uncertainty.report import write_plots, write_report

    write_plots(out_dir, T, keys)
    (out_dir / "run_report.md").write_text(write_report(run_id, T, verdict, keys), "utf-8")
    _append_registry(
        output_root, run_id, cfg, resolved["_config_sha256"], out_dir,
        protocol=PROTOCOL_ID, run_class=cfg.run_class,
    )  # fmt: skip
    return out_dir
