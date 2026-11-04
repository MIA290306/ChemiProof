"""CP-652 on the REAL, committed results/ runs and the real manifest. Run with `-m dataset`
only (not in CI): dim_sample/fact_data_quality need data/interim/sample_manifest.csv, which
needs the real Zenodo archive to have been audited once (`chemiproof dataset audit`).
"""

from __future__ import annotations

import pytest

from chemiproof.bi.export import export_all

pytestmark = pytest.mark.dataset


@pytest.fixture(scope="module")
def manifest(repo):
    path = repo / "data/interim/sample_manifest.csv"
    assert path.is_file(), (
        f"DATASET_NOT_AVAILABLE: {path} missing; run `chemiproof dataset audit` first"
    )
    return path


@pytest.fixture(scope="module")
def exported(repo, manifest, tmp_path_factory):
    out = tmp_path_factory.mktemp("bi_export")
    return export_all(
        repo / "results",
        manifest,
        repo / "config/bi/export_contract.yaml",
        repo / "config/bi/protocol_map.yaml",
        out,
    ), out


def test_export_has_zero_validation_violations(exported):
    manifest, _ = exported
    assert manifest["validation_violations"] == []


def test_export_covers_every_contract_table_plus_kpis(exported):
    manifest, out_dir = exported
    tables = {f["table"] for f in manifest["files"]}
    assert tables >= {
        "dim_adulterant", "dim_brand", "dim_sample", "dim_model", "dim_fold", "dim_experiment",
        "fact_predictions", "fact_model_metrics", "fact_uncertainty", "fact_selective_risk",
        "fact_data_quality", "fact_data_issues", "fact_ot_diagnostics", "fact_robustness",
        "fact_published_reference", "expected_kpis",
    }  # fmt: skip
    assert (out_dir / "export_manifest.json").is_file()


def test_real_dataset_tables_are_fully_populated(exported):
    manifest, _ = exported
    rows_by_table = {f["table"]: f["rows"] for f in manifest["files"]}
    assert rows_by_table["dim_sample"] == 330
    assert rows_by_table["fact_data_quality"] == 330


def test_m5_uncertainty_available_and_nonempty(exported):
    manifest, _ = exported
    assert manifest["uncertainty_available"] is True
    assert manifest["selective_risk_available"] is True
    assert manifest["robustness_available"] is True
    rows_by_table = {f["table"]: f["rows"] for f in manifest["files"]}
    assert rows_by_table["fact_uncertainty"] > 0
    assert rows_by_table["fact_selective_risk"] > 0


def test_refuses_to_overwrite_a_nonempty_output_dir(repo, manifest, exported):
    _, out_dir = exported
    with pytest.raises(FileExistsError):
        export_all(
            repo / "results", manifest,
            repo / "config/bi/export_contract.yaml", repo / "config/bi/protocol_map.yaml",
            out_dir,
        )  # fmt: skip


def test_export_is_byte_identical_on_rerun(repo, manifest, exported, tmp_path_factory):
    _, out_dir = exported
    out_dir2 = tmp_path_factory.mktemp("bi_export_rerun")
    export_all(
        repo / "results", manifest,
        repo / "config/bi/export_contract.yaml", repo / "config/bi/protocol_map.yaml",
        out_dir2,
    )  # fmt: skip
    for path in sorted(out_dir.glob("*.csv")) + [out_dir / "expected_kpis.json"]:
        other = out_dir2 / path.name
        assert other.read_bytes() == path.read_bytes(), f"{path.name} differs on rerun"


def test_export_manifest_names_excluded_m6_final_run(exported):
    manifest, _ = exported
    assert "M6_final_*" in manifest["excluded_runs"]
    run_dirs = {s["run_dir"] for s in manifest["sources"]}
    assert not any(d.startswith("M6_final_") for d in run_dirs)


def test_csv_and_parquet_exports_have_identical_values(repo, manifest, exported, tmp_path_factory):
    pytest.importorskip("pyarrow")
    import csv

    import pyarrow.parquet as pq

    _, csv_dir = exported
    pq_dir = tmp_path_factory.mktemp("bi_export_parquet")
    export_all(
        repo / "results", manifest,
        repo / "config/bi/export_contract.yaml", repo / "config/bi/protocol_map.yaml",
        pq_dir, "parquet",
    )  # fmt: skip
    for csv_path in sorted(csv_dir.glob("*.csv")):
        with csv_path.open(newline="", encoding="utf-8") as fh:
            csv_rows = list(csv.DictReader(fh))
        pq_rows = pq.read_table(pq_dir / f"{csv_path.stem}.parquet").to_pylist()
        assert len(csv_rows) == len(pq_rows), csv_path.stem
        for c, p in zip(csv_rows, pq_rows, strict=True):
            for k in c:
                assert c[k] == ("" if p[k] is None else str(p[k])), (csv_path.stem, k, c[k], p[k])


def test_cli_parses_export_bi_subcommand():
    from chemiproof.cli import build_parser

    args = build_parser().parse_args(
        ["export", "bi", "--output-dir", "/tmp/unused-path-not-created"]
    )
    assert args.command == "export" and args.action == "bi" and args.format == "csv"
