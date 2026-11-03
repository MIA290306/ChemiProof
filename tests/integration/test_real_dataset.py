"""T003/T004 on the REAL archive. Run with `-m dataset` only (not in CI); fails loudly if absent."""

from collections import Counter

import pytest

from chemiproof.data.manifest import build_audit, build_manifest
from chemiproof.errors import StatusCode
from chemiproof.spectra.qc import chlorophyll_probe

pytestmark = pytest.mark.dataset


@pytest.fixture(scope="module")
def built(repo):
    d = repo / "data/raw/extracted"
    assert d.is_dir(), f"{StatusCode.DATASET_NOT_AVAILABLE}: {d} missing"
    return d, build_manifest(d)


def test_t003_inventory_matches_published_330_and_groups(built):
    _, res = built
    audit = build_audit(res)
    assert audit["total_records"] == 330 and not res.problems
    assert Counter(r.adulterant_type for r in res.rows) == {
        "soybean": 60,
        "peanut": 60,
        "rapeseed": 90,
        "corn": 90,
        "walnut": 30,
    }
    assert audit["discrepancy_ledger"] == []
    assert audit["distinct_axes"] == 1


def test_t004_labels_are_k_over_11_with_documented_direction(built):
    _, res = built
    levels = sorted({round(r.olive_fraction * 11) for r in res.rows})
    assert levels == list(range(1, 11))
    assert {r.olive_ratio_raw for r in res.rows if round(r.olive_fraction * 11) == 10} == {"10：1"}


def test_label_direction_is_consistent_with_chlorophyll_signal(built):
    d, res = built
    probe = chlorophyll_probe(d, res.rows)
    assert len(probe) == 11
    assert all(p["band_mean_at_max_olive"] > p["band_mean_at_min_olive"] for p in probe)


def test_m2_source_internal_run_on_real_data(repo, tmp_path):
    """Real M2 run: structure, floor sanity and determinism (not a performance claim)."""
    import csv
    import json

    from chemiproof.cli import EXIT_OK, main

    data_dir = repo / "data/raw/extracted"
    manifest = repo / "data/interim/sample_manifest.csv"
    assert manifest.is_file(), f"{StatusCode.DATASET_NOT_AVAILABLE}: run `chemiproof dataset audit`"
    dirs = []
    for name in ("a", "b"):
        rc = main(
            [
                "experiment",
                "run",
                "--config",
                str(repo / "config/experiments/m2_source_internal.yaml"),
                "--data-dir",
                str(data_dir),
                "--output-root",
                str(tmp_path / name),
            ]
        )
        assert rc == EXIT_OK
        (d,) = list((tmp_path / name).glob("M2_*"))
        dirs.append(d)
    s = json.loads((dirs[0] / "summary.json").read_text())
    n = 330
    for key in ("mean_y", "svr_raw", "pca_svr", "pls"):
        assert s["models"][key]["pooled_unclipped"]["n"] == n
    floor = s["models"]["mean_y"]
    assert abs(floor["macro_over_folds"]["r2"]) < 0.02  # constant predictor explains ~nothing
    assert floor["pooled_unclipped"]["mae_fraction"] == pytest.approx(0.2273, abs=0.01)
    for key in ("svr_raw", "pca_svr", "pls"):  # models beat the floor on this optimistic protocol
        assert (
            s["models"][key]["macro_over_folds"]["mae_fraction"]
            < floor["macro_over_folds"]["mae_fraction"]
        )
    rows = [
        [
            (r["sample_id"], r["model"], r["y_pred_fraction"])
            for r in csv.DictReader((d / "predictions.csv").open())
        ]
        for d in dirs
    ]
    assert rows[0] == rows[1]  # deterministic


@pytest.mark.parametrize("subset", [None, "luhua"])
def test_m3_loao_run_on_real_data(repo, tmp_path, subset):
    """Real LOAO runs (exploratory class so a dirty tree does not block): structure + determinism,
    not performance claims."""
    import csv
    import json

    import yaml

    from chemiproof.cli import EXIT_OK, main

    cfg = yaml.safe_load((repo / "config/experiments/baseline.yaml").read_text())
    cfg.update(
        run_class="exploratory",
        subset_brand=subset,
        dataset_manifest=str(repo / "data/interim/sample_manifest.csv"),
    )
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg))
    dirs = []
    for name in ("a", "b"):
        rc = main(
            [
                "experiment",
                "run",
                "--config",
                str(p),
                "--data-dir",
                str(repo / "data/raw/extracted"),
                "--output-root",
                str(tmp_path / name),
            ]
        )
        assert rc == EXIT_OK
        (d,) = list((tmp_path / name).glob("M3_*"))
        dirs.append(d)
    m = list(csv.DictReader((dirs[0] / "metrics_by_fold.csv").open()))
    sizes = {r["fold_id"]: int(r["n"]) for r in m if r["model"] == "mean_y"}
    expected = (
        {
            "LOAO-soybean": 60,
            "LOAO-peanut": 60,
            "LOAO-rapeseed": 90,
            "LOAO-corn": 90,
            "LOAO-walnut": 30,
        }
        if subset is None
        else {f"LOAO-{a}": 30 for a in ("soybean", "peanut", "rapeseed", "corn", "walnut")}
    )
    assert sizes == expected
    audit = json.loads((dirs[0] / "leakage_audit.json").read_text())
    assert (
        audit["label_shuffle_canary"]["passed"] and len(audit["label_shuffle_canary"]["folds"]) == 5
    )
    rows = [
        [
            (r["sample_id"], r["model"], r["y_pred_fraction"])
            for r in csv.DictReader((d / "predictions.csv").open())
        ]
        for d in dirs
    ]
    assert rows[0] == rows[1]


def test_m4_ot_run_on_real_data_structure_convergence_and_determinism(repo, tmp_path):
    """Added AFTER the locked OT runs (ADR-014): structural/numerical checks only."""
    import csv
    import json

    import yaml

    from chemiproof.cli import EXIT_OK, main

    cfg = yaml.safe_load((repo / "config/experiments/ot_transductive.yaml").read_text())
    cfg.update(
        run_class="exploratory",
        models=["ot_svr", "svr_no_adaptation"],
        dataset_manifest=str(repo / "data/interim/sample_manifest.csv"),
    )
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg))
    dirs = []
    for name in ("a", "b"):
        rc = main(
            [
                "experiment",
                "run",
                "--config",
                str(p),
                "--data-dir",
                str(repo / "data/raw/extracted"),
                "--output-root",
                str(tmp_path / name),
            ]
        )
        assert rc == EXIT_OK
        (d,) = list((tmp_path / name).glob("M4_*"))
        dirs.append(d)
    diags = [
        r for r in csv.DictReader((dirs[0] / "ot_diagnostics.csv").open()) if r["model"] == "ot_svr"
    ]
    assert len(diags) == 5 and all(r["converged"] == "True" for r in diags)
    assert all(
        abs(float(r["total_mass"]) - 1.0) < 1e-9 and float(r["col_marginal_sq_l2"]) < 1e-9
        for r in diags
    )
    assert [(int(r["n_source"]), int(r["n_target"])) for r in diags] == [
        (270, 60),
        (270, 60),
        (240, 90),
        (240, 90),
        (300, 30),
    ]
    s = json.loads((dirs[0] / "summary.json").read_text())
    assert s["models"]["ot_svr"]["mode"] == "transductive_batch"
    assert s["models"]["svr_no_adaptation"]["mode"] == "inductive"
    assert "TRANSDUCTIVE" in s["transductive_warning"]
    assert json.loads((dirs[0] / "leakage_audit.json").read_text())["label_shuffle_canary"][
        "passed"
    ]
    rows = [
        [
            (r["sample_id"], r["model"], r["y_pred_fraction"])
            for r in csv.DictReader((d / "predictions.csv").open())
        ]
        for d in dirs
    ]
    assert rows[0] == rows[1]
