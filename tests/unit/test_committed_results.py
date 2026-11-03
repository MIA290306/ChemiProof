"""Independent re-check of the COMMITTED run artifacts (no dataset needed, runs in CI).

Recomputes every per-fold and macro metric from `predictions.csv` with plain NumPy (not
chemiproof.evaluation.metrics), checks LOAO fold integrity, and re-derives the M5 selective-risk
and pooled-interval coverage numbers. A hand-edited or stale table fails here.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest

RESULTS = Path(__file__).resolve().parents[2] / "results"
SCORED_RUNS = sorted(
    d for d in RESULTS.glob("M[234]_*") if (d / "predictions.csv").is_file()
    and (d / "metrics_by_fold.csv").is_file()
)  # fmt: skip
M5_RUNS = sorted(d for d in RESULTS.glob("M5_*") if (d / "selective_risk.csv").is_file())


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _by(rows, *keys):
    out = defaultdict(list)
    for r in rows:
        out[tuple(r[k] for k in keys)].append(r)
    return out


def _arr(rows, col):
    return np.array([float(r[col]) for r in rows])


def test_committed_runs_exist():
    assert SCORED_RUNS and M5_RUNS, "expected committed M2-M5 run directories under results/"


@pytest.mark.parametrize("run", SCORED_RUNS, ids=lambda d: d.name)
def test_fold_metrics_and_macro_match_predictions(run: Path):
    preds = _by(_rows(run / "predictions.csv"), "model", "fold_id")
    table = {(r["model"], r["fold_id"]): r for r in _rows(run / "metrics_by_fold.csv")}
    assert set(preds) == set(table)
    for (model, fold), rows in preds.items():
        t, p = _arr(rows, "y_true_fraction"), _arr(rows, "y_pred_fraction")
        e = p - t
        expected = {
            "n": t.size,
            "mae_fraction": np.abs(e).mean(),
            "rmse_fraction": np.sqrt((e**2).mean()),
            "bias_fraction": e.mean(),
            "r2": 1 - (e**2).sum() / ((t - t.mean()) ** 2).sum(),
        }
        for col, val in expected.items():
            assert float(table[(model, fold)][col]) == pytest.approx(val, abs=1e-12), (fold, col)
        assert np.allclose(t * 11, np.round(t * 11)), "labels must lie on the a/11 grid"
        if fold.startswith("LOAO-"):
            adulterant = fold.removeprefix("LOAO-")
            assert all(r["sample_id"].startswith(adulterant + "_") for r in rows), fold

    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))["models"]
    for (model,), rows in _by(_rows(run / "predictions.csv"), "model").items():
        hashes = [r["source_sample_hash"] for r in rows]
        assert len(hashes) == len(set(hashes)), f"{model}: a sample is scored twice"
        folds = [row for (m, _), row in table.items() if m == model]
        macro = summary[model]["macro_over_folds"]
        for col in ("mae_fraction", "r2"):
            assert macro[col] == pytest.approx(np.mean([float(f[col]) for f in folds]), abs=1e-12)


@pytest.mark.parametrize("run", M5_RUNS, ids=lambda d: d.name)
def test_m5_selective_risk_and_coverage_match_predictions(run: Path):
    preds = _by(_rows(run / "predictions.csv"), "model", "fold_id")
    sel = {
        (r["model"], r["fold_id"]): r
        for r in _rows(run / "selective_risk.csv")
        if r["score"] == "ood_maha" and float(r["retention_goal"]) == 0.8
    }
    cov = {
        (r["model"], r["fold_id"]): r
        for r in _rows(run / "interval_coverage.csv")
        if r["variant"] == "pooled"
    }
    for key, rows in preds.items():
        t, p = _arr(rows, "y_true_fraction"), _arr(rows, "y_pred_fraction")
        ae = np.abs(p - t)
        keep = np.array([r["abstain"] != "True" for r in rows])  # abstain column = ood_maha @ 0.80
        assert int(sel[key]["n_retained"]) == keep.sum()
        assert float(sel[key]["full_mae_fraction"]) == pytest.approx(ae.mean(), abs=1e-12)
        assert float(sel[key]["selective_mae"]) == pytest.approx(ae[keep].mean(), abs=1e-12)
        lo, hi = _arr(rows, "interval_lo"), _arr(rows, "interval_hi")
        observed = np.mean((t >= lo) & (t <= hi))
        assert float(cov[key]["observed_coverage"]) == pytest.approx(observed, abs=1e-12)
