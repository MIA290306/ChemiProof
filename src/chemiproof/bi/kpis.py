"""K01-K21 (docs/bi/19_POWER_BI_DATA_MODEL.md section 6): computed from the exported tables
in memory, written to expected_kpis.json so BI021 can reconcile the Power BI measures
against these Python numbers. Every KPI is grouped by run_id (and model_key where it
varies by model), never pooled across protocols.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import pstdev
from typing import Any

Tables = dict[str, list[dict[str, Any]]]


def _group(rows: list[dict[str, Any]], *keys: str) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    out: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        out[tuple(r[k] for k in keys)].append(r)
    return out


def compute_kpis(tables: Tables) -> list[dict[str, Any]]:
    kpis: list[dict[str, Any]] = []
    dim_sample = tables.get("dim_sample", [])
    dim_adulterant = {r["adulterant_key"]: r for r in tables.get("dim_adulterant", [])}
    dq = tables.get("fact_data_quality", [])
    issues = tables.get("fact_data_issues", [])
    preds = tables.get("fact_predictions", [])
    metrics = tables.get("fact_model_metrics", [])
    unc = tables.get("fact_uncertainty", [])
    sel = tables.get("fact_selective_risk", [])
    ot = tables.get("fact_ot_diagnostics", [])
    rob = tables.get("fact_robustness", [])

    kpis.append(
        {"kpi": "K01", "label": "Total samples", "value": len(dim_sample), "unit": "samples"}
    )

    for key, rows in _group(dim_sample, "adulterant_key").items():
        (adulterant,) = key
        expected = dim_adulterant.get(adulterant, {}).get("expected_samples")
        kpis.append(
            {
                "kpi": "K02",
                "label": "Samples by adulterant",
                "group": {"adulterant_key": adulterant},
                "value": len(rows),
                "expected": expected,
                "gap": (expected - len(rows)) if expected is not None else None,
                "unit": "samples",
            }
        )
    for key, rows in _group(dim_sample, "brand_key").items():
        (brand,) = key
        kpis.append(
            {
                "kpi": "K03",
                "label": "Samples by brand",
                "group": {"brand_key": brand},
                "value": len(rows),
                "unit": "samples",
            }
        )
    for key, rows in _group(dim_sample, "olive_percent").items():
        (pct,) = key
        kpis.append(
            {
                "kpi": "K04",
                "label": "Olive concentration distribution",
                "group": {"olive_percent": pct},
                "value": len(rows),
                "unit": "samples",
            }
        )

    if dq:
        completeness = [r["spectral_completeness"] for r in dq]
        kpis.append(
            {
                "kpi": "K05",
                "label": "Spectral completeness",
                "value": sum(completeness) / len(completeness),
                "share_at_1": sum(1 for c in completeness if c == 1.0) / len(completeness),
                "unit": "fraction",
            }
        )
    kpis.append(
        {"kpi": "K06", "label": "Rejected files / invalid samples",
         "value": sum(1 for i in issues if i["severity"] == "REJECTED_FILE"), "unit": "files"}
    )  # fmt: skip
    for key, rows in _group(dq, "qc_status").items():
        (status,) = key
        kpis.append(
            {
                "kpi": "K07",
                "label": "QC status mix",
                "group": {"qc_status": status},
                "value": len(rows),
                "unit": "samples",
            }
        )
    kpis.append(
        {
            "kpi": "K08",
            "label": "Duplicate content",
            "value": sum(1 for r in dq if r["is_duplicate_content"]),
            "unit": "samples",
        }
    )

    for key, rows in _group(preds, "run_id", "model_key").items():
        run_id, model_key = key
        errs = [r["abs_error_fraction"] for r in rows]
        residuals = [r["residual_fraction"] for r in rows]
        y_true = [r["y_true_fraction"] for r in rows]
        mean_true = sum(y_true) / len(y_true)
        ss_res = sum((r["y_pred_fraction"] - t) ** 2 for r, t in zip(rows, y_true, strict=True))
        ss_tot = sum((t - mean_true) ** 2 for t in y_true)
        group = {"run_id": run_id, "model_key": model_key}
        kpis.append(
            {
                "kpi": "K09",
                "label": "MAE (pooled)",
                "group": group,
                "scope_type": "pooled",
                "value": 100 * sum(errs) / len(errs),
                "unit": "percentage points",
            }
        )
        kpis.append(
            {
                "kpi": "K10",
                "label": "RMSE (pooled)",
                "group": group,
                "scope_type": "pooled",
                "value": (sum(r * r for r in residuals) / len(residuals)) ** 0.5,
                "unit": "fraction",
            }
        )
        kpis.append(
            {
                "kpi": "K11",
                "label": "Bias (pooled)",
                "group": group,
                "scope_type": "pooled",
                "value": sum(residuals) / len(residuals),
                "unit": "fraction",
            }
        )
        kpis.append(
            {
                "kpi": "K12",
                "label": "R2 (pooled)",
                "group": group,
                "scope_type": "pooled",
                "value": (1 - ss_res / ss_tot) if ss_tot else None,
                "unit": "unitless",
            }
        )
        kpis.append(
            {
                "kpi": "K14",
                "label": "Out-of-range predictions",
                "group": group,
                "value": sum(1 for r in rows if r["is_out_of_unit_interval"]),
                "unit": "predictions",
            }
        )

    for key, rows in _group(
        [m for m in metrics if m["scope_type"] == "fold"], "run_id", "model_key"
    ).items():
        run_id, model_key = key
        r2s = [m["r2"] for m in rows if m["r2"] is not None]
        if not r2s:
            continue
        worst = max(rows, key=lambda m: m["mae_fraction"])
        group = {"run_id": run_id, "model_key": model_key}
        kpis.append(
            {
                "kpi": "K12",
                "label": "R2 (macro, mean of fold R2)",
                "group": group,
                "scope_type": "macro",
                "value": sum(r2s) / len(r2s),
                "unit": "unitless",
            }
        )
        kpis.append(
            {
                "kpi": "K13",
                "label": "R2 spread and worst fold",
                "group": group,
                "value": pstdev(r2s) if len(r2s) > 1 else 0.0,
                "worst_fold_id": worst["fold_id"],
                "unit": "unitless, fold id",
            }
        )

    for key, rows in _group(unc, "run_id", "model_key", "variant").items():
        run_id, model_key, variant = key
        group = {"run_id": run_id, "model_key": model_key, "variant": variant}
        with_interval = [r for r in rows if r["covered"] is not None]
        if with_interval:
            kpis.append(
                {
                    "kpi": "K15",
                    "label": "Observed interval coverage",
                    "group": group,
                    "value": sum(1 for r in with_interval if r["covered"]) / len(with_interval),
                    "unit": "fraction",
                }
            )
            widths = [r["interval_width_fraction"] for r in with_interval]
            kpis.append(
                {
                    "kpi": "K16",
                    "label": "Mean interval width",
                    "group": group,
                    "value": sum(widths) / len(widths),
                    "unit": "fraction",
                }
            )
        abstains = sum(1 for r in rows if r["abstain"])
        kpis.append(
            {
                "kpi": "K17",
                "label": "Abstention rate and retention",
                "group": group,
                "abstain_rate": abstains / len(rows),
                "retention": 1 - abstains / len(rows),
                "unit": "fraction",
            }
        )
        kpis.append(
            {
                "kpi": "K19",
                "label": "Review-required samples",
                "group": group,
                "value": abstains,
                "unit": "samples",
            }
        )

    for key, rows in _group(sel, "run_id", "model_key", "score").items():
        run_id, model_key, score = key
        kpis.append(
            {
                "kpi": "K18",
                "label": "Selective MAE",
                "group": {"run_id": run_id, "model_key": model_key, "score": score},
                "value": [
                    {
                        "retention_target": r["retention_target"],
                        "selective_mae_pp": r["selective_mae_pp"],
                        "retention_observed": r["retention_observed"],
                    }
                    for r in rows
                ],
                "unit": "percentage points",
            }  # fmt: skip
        )

    for key, rows in _group(ot, "run_id").items():
        (run_id,) = key
        converged = sum(1 for r in rows if r["converged"])
        kpis.append(
            {
                "kpi": "K20",
                "label": "OT convergence",
                "group": {"run_id": run_id},
                "value": converged / len(rows),
                "unit": "fraction",
            }
        )

    for key, rows in _group(rob, "run_id", "batch_kind").items():
        run_id, batch_kind = key
        kpis.append(
            {
                "kpi": "K21",
                "label": "Stress-test MAE",
                "group": {"run_id": run_id, "batch_kind": batch_kind},
                "value": [
                    {"model_key": r["model_key"], "mae_fraction_mean": r["mae_fraction_mean"]}
                    for r in rows
                ],
                "unit": "percentage points",
            }  # fmt: skip
        )

    return kpis
