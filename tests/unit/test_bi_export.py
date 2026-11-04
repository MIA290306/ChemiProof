"""CP-652 unit tests: pure contract/export logic on synthetic fixtures, no real dataset."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from chemiproof.bi import contract as ct
from chemiproof.bi import export as ex
from chemiproof.bi import kpis as kp

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / "config/bi/export_contract.yaml"
PROTOCOL_MAP_PATH = REPO / "config/bi/protocol_map.yaml"


@pytest.fixture(scope="module")
def contract():
    return ct.load_contract(CONTRACT_PATH)


@pytest.fixture(scope="module")
def protocol_map():
    return ct.load_protocol_map(PROTOCOL_MAP_PATH)


def test_resolve_protocol_id_hits_and_falls_back(protocol_map):
    assert ct.resolve_protocol_id(protocol_map, "f93cfb4c97d22ad2ffff") == ("LOAO-UQ-v1", True)
    assert ct.resolve_protocol_id(protocol_map, "0000000000000000") == ("UNREGISTERED", False)


def test_write_table_csv_round_trips_and_orders_columns(tmp_path, contract):
    cols = ct.table_columns(contract, "dim_brand")
    rows = [{"brand_key": "luhua", "brand_label": "Luhua"}]
    meta = ct.write_table_csv(tmp_path, contract, "dim_brand", rows)
    assert meta["rows"] == 1
    with (tmp_path / "dim_brand.csv").open(newline="", encoding="utf-8") as fh:
        assert next(csv.reader(fh)) == cols


def test_write_table_csv_rejects_column_mismatch(tmp_path, contract):
    with pytest.raises(ValueError, match="do not match contract"):
        ct.write_table_csv(tmp_path, contract, "dim_brand", [{"brand_key": "luhua"}])


def test_write_table_csv_refuses_to_overwrite(tmp_path, contract):
    rows = [{"brand_key": "luhua", "brand_label": "Luhua"}]
    ct.write_table_csv(tmp_path, contract, "dim_brand", rows)
    with pytest.raises(FileExistsError):
        ct.write_table_csv(tmp_path, contract, "dim_brand", rows)


def test_build_dim_adulterant_matches_published_expectations(contract):
    rows = {r["adulterant_key"]: r for r in ex.build_dim_adulterant()}
    assert rows["soybean"]["expected_samples"] == 60
    assert rows["walnut"]["expected_samples"] == 30
    assert sum(r["expected_samples"] for r in rows.values()) == 330
    cols = set(ct.table_columns(contract, "dim_adulterant"))
    assert set(next(iter(rows.values()))) == cols


def test_build_dim_model_covers_every_fact_predictions_model_key():
    models = {r["model_key"] for r in ex.build_dim_model()}
    assert {"mean_y", "svr_raw", "pca_svr", "pls", "ot_svr", "svr_no_adaptation"} <= models


def _write_predictions_csv(path: Path, rows: list[dict[str, str]]) -> None:
    cols = [
        "run_id",
        "fold_id",
        "source_sample_hash",
        "sample_id",
        "y_true_fraction",
        "y_pred_fraction",
        "model",
        "mode",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def test_build_fact_predictions_computes_derived_fields_correctly(tmp_path):
    _write_predictions_csv(
        tmp_path / "predictions.csv",
        [
            {
                "run_id": "r1",
                "fold_id": "LOAO-soybean",
                "source_sample_hash": "h1",
                "sample_id": "s1",
                "y_true_fraction": "0.5",
                "y_pred_fraction": "0.6",
                "model": "svr_raw",
                "mode": "inductive",
            },
            {  # out-of-unit-interval prediction
                "run_id": "r1",
                "fold_id": "LOAO-soybean",
                "source_sample_hash": "h2",
                "sample_id": "s2",
                "y_true_fraction": "0.9",
                "y_pred_fraction": "1.05",
                "model": "svr_raw",
                "mode": "inductive",
            },
        ],
    )  # fmt: skip
    run = ex.RunMeta("r1", tmp_path, experiment_id="chemiproof-source-baselines")
    rows = ex.build_fact_predictions([run])
    a, b = rows
    assert a["residual_fraction"] == pytest.approx(0.1)
    assert a["abs_error_fraction"] == pytest.approx(0.1)
    assert a["abs_error_pp"] == pytest.approx(10.0)
    assert a["is_out_of_unit_interval"] is False
    assert b["is_out_of_unit_interval"] is True
    assert b["y_pred_clipped_fraction"] == pytest.approx(1.0)


def test_validate_export_catches_out_of_range_fraction(contract):
    tables = {
        "dim_sample": [{"sample_id": "s1", "olive_fraction": 1.5, "olive_percent": 150.0}],
        "fact_predictions": [],
        "fact_model_metrics": [],
        "dim_experiment": [],
        "fact_published_reference": [],
    }
    problems = ex.validate_export(contract, tables)
    assert any("V-03" in p and "s1" in p for p in problems)


def test_validate_export_clean_on_well_formed_rows(contract):
    tables = {
        "dim_sample": [{"sample_id": "s1", "olive_fraction": 0.5, "olive_percent": 50.0}],
        "fact_predictions": [
            {
                "run_id": "r1",
                "model_key": "svr_raw",
                "sample_id": "s1",
                "y_true_fraction": 0.5,
                "abs_error_fraction": 0.1,
                "abs_error_pp": 10.0,
                "y_pred_fraction": 0.6,
            },
        ],
        "fact_model_metrics": [],
        "dim_experiment": [
            {
                "run_id": "r1",
                "config_sha256": "a" * 16,
                "manifest_sha256": "b" * 16,
                "git_head": "c" * 8,
                "git_dirty": False,
                "is_headline": True,
                "protocol_family": "loao",
                "canary_passed": True,
            },
        ],
        "fact_published_reference": [{"reference_id": "ref1", "is_measured": False}],
    }  # fmt: skip
    assert ex.validate_export(contract, tables) == []


def test_validate_export_catches_dirty_headline_run(contract):
    tables = {
        "dim_sample": [], "fact_predictions": [], "fact_model_metrics": [],
        "fact_published_reference": [],
        "dim_experiment": [
            {
                "run_id": "r1",
                "config_sha256": "a" * 16,
                "manifest_sha256": "b" * 16,
                "git_head": "c" * 8,
                "git_dirty": True,
                "is_headline": True,
                "protocol_family": "loao",
                "canary_passed": True,
            },
        ],
    }  # fmt: skip
    problems = ex.validate_export(contract, tables)
    assert any("V-06" in p for p in problems)


def test_validate_export_catches_absolute_path_leak(contract):
    tables = {
        "dim_sample": [], "fact_predictions": [], "fact_model_metrics": [],
        "dim_experiment": [], "fact_published_reference": [],
        "fact_data_issues": [{"path_rel": "/Users/someone/secret/data.dat"}],
    }  # fmt: skip
    problems = ex.validate_export(contract, tables)
    assert any("V-10" in p for p in problems)


def test_compute_kpis_k01_and_k09(contract):
    tables = {
        "dim_sample": [{"adulterant_key": "soybean", "brand_key": "luhua", "olive_percent": 50.0}],
        "dim_adulterant": ex.build_dim_adulterant(),
        "fact_data_quality": [],
        "fact_data_issues": [],
        "fact_predictions": [
            {
                "run_id": "r1", "model_key": "svr_raw", "y_true_fraction": 0.5,
                "y_pred_fraction": 0.6, "abs_error_fraction": 0.1,
                "residual_fraction": 0.1, "is_out_of_unit_interval": False,
            },
            {
                "run_id": "r1", "model_key": "svr_raw", "y_true_fraction": 0.3,
                "y_pred_fraction": 0.3, "abs_error_fraction": 0.0,
                "residual_fraction": 0.0, "is_out_of_unit_interval": False,
            },
        ],
        "fact_model_metrics": [], "fact_uncertainty": [], "fact_selective_risk": [],
        "fact_ot_diagnostics": [], "fact_robustness": [],
    }  # fmt: skip
    kpis = kp.compute_kpis(tables)
    k01 = next(k for k in kpis if k["kpi"] == "K01")
    assert k01["value"] == 1
    k09 = next(k for k in kpis if k["kpi"] == "K09")
    assert k09["value"] == pytest.approx(5.0)  # mean(10, 0) pp
