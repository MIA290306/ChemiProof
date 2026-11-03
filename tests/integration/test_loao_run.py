"""End-to-end LOAO on a SYNTHETIC Luhua-only tree (5 adulterants x 3 rounds x 10 ratios = 150)."""

import csv
import json

import numpy as np
import pytest
import yaml

from chemiproof import experiments
from chemiproof.cli import EXIT_ERROR, EXIT_OK, main
from chemiproof.data.manifest import build_manifest, write_manifest_csv
from chemiproof.data.schema import EEMSpectrum
from chemiproof.data.synthetic import make_synthetic_eem
from helpers import write_dat

FOLDERS = {
    "soybean": "福临门大豆油",
    "peanut": "家香味花生油",
    "rapeseed": "金龙鱼菜籽油",
    "corn": "西王玉米胚芽油",
    "walnut": "晟麦核桃油",
}
ROUNDS = ("第一轮", "第二轮", "第三轮")


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("loao")
    root = tmp / "d"
    a_, b_ = make_synthetic_eem(1), make_synthetic_eem(2)
    i = 0
    for k, fname in enumerate(FOLDERS.values()):
        c = make_synthetic_eem(20 + k)
        for rnd in ROUNDS:
            for a in range(1, 11):
                i += 1
                y = a / 11
                z = y * a_.intensity + (1 - y) * (b_.intensity + 0.15 * c.intensity)
                z = z + 0.002 * np.random.default_rng(i).standard_normal(z.shape)
                spec = EEMSpectrum(f"s{i}", a_.excitation_nm, a_.emission_nm, z)
                write_dat(
                    root / f"鲁花特级初榨混{fname}" / rnd / f"{a}：{11 - a}" / "0_RM.dat", spec
                )
    manifest = tmp / "m.csv"
    res = build_manifest(root)
    assert len(res.rows) == 150 and not res.problems
    write_manifest_csv(res.rows, manifest)
    return tmp, root, manifest


def _cfg(world, repo, tmp_path, **over):
    _, _, manifest = world
    cfg = yaml.safe_load((repo / "config/experiments/baseline.yaml").read_text())
    cfg.update(dataset_manifest=str(manifest), subset_brand="luhua", run_class="exploratory")
    cfg.update(over)
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return p


def _run(world, repo, tmp_path, name="out", **over):
    _, root, _ = world
    out = tmp_path / name
    rc = main(
        [
            "experiment",
            "run",
            "--config",
            str(_cfg(world, repo, tmp_path, **over)),
            "--data-dir",
            str(root),
            "--output-root",
            str(out),
        ]
    )
    return rc, out


def test_loao_end_to_end_artifacts_and_audit(world, repo, tmp_path):
    rc, out = _run(world, repo, tmp_path)
    assert rc == EXIT_OK
    (d,) = list(out.glob("M3_*"))
    for name in (
        "predictions.csv",
        "metrics_by_fold.csv",
        "splits.csv",
        "fold_manifest.csv",
        "leakage_audit.json",
        "summary.json",
        "config_resolved.yaml",
        "run_report.md",
        "mae_r2_by_fold.png",
        "parity_by_model.png",
    ):
        assert (d / name).is_file(), name
    metrics = list(csv.DictReader((d / "metrics_by_fold.csv").open()))
    assert {m["fold_id"] for m in metrics} == {f"LOAO-{a}" for a in FOLDERS}
    assert {m["n"] for m in metrics} == {"30"} and {m["mode"] for m in metrics} == {"inductive"}
    audit = json.loads((d / "leakage_audit.json").read_text())
    assert audit["label_shuffle_canary"]["passed"] and all(
        v for v in audit["fold_audit"]["checks"].values() if v is not None
    )
    assert audit["fold_audit"]["checks"]["sizes_match_published"] is None
    summary = json.loads((d / "summary.json").read_text())
    ref = summary["published_reference_not_measured"]
    assert "NOT a ChemiProof measurement" in ref["status"]
    assert summary["models"]["pls"]["macro_over_folds"]["r2"] != ref["ot_svr_mean_r2"]
    assert "walnut" in json.dumps(summary["models"]["mean_y"]["descriptive_by_brand"])
    folds_csv = list(csv.DictReader((d / "fold_manifest.csv").open()))
    assert [r["n_test"] for r in folds_csv] == ["30"] * 5
    reg = list(csv.DictReader((out / "experiment_registry.csv").open()))
    assert len(reg) == 1 and reg[0]["protocol"] == "loao" and reg[0]["subset_brand"] == "luhua"


def test_loao_runs_are_deterministic_and_registry_keeps_history(world, repo, tmp_path):
    _, out1 = _run(world, repo, tmp_path, "o")
    _, out2 = _run(world, repo, tmp_path, "o")  # same output root: history must accumulate
    runs = sorted((tmp_path / "o").glob("M3_*"))
    assert len(runs) == 1 or len(runs) == 2  # same run_id may reuse the dir; registry still grows
    reg = list(csv.DictReader((tmp_path / "o" / "experiment_registry.csv").open()))
    assert len(reg) == 2
    p1 = [r["y_pred_fraction"] for r in csv.DictReader((runs[0] / "predictions.csv").open())]
    p2 = [r["y_pred_fraction"] for r in csv.DictReader((runs[-1] / "predictions.csv").open())]
    assert p1 == p2


def test_full_design_expectation_fails_loudly_on_a_subset(world, repo, tmp_path, capsys):
    rc, _ = _run(world, repo, tmp_path, subset_brand=None)  # 30 per adulterant != published sizes
    assert rc == EXIT_ERROR
    assert "QC_REVIEW_REQUIRED" in capsys.readouterr().err


def test_locked_run_requires_clean_tree(world, repo, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(experiments, "git_state", lambda: {"head": "abc", "dirty": True})
    rc, out = _run(world, repo, tmp_path, run_class="locked")
    assert rc == EXIT_ERROR and "clean tracked git tree" in capsys.readouterr().err
    assert not out.exists()
    monkeypatch.setattr(experiments, "git_state", lambda: {"head": "abc", "dirty": False})
    rc, out = _run(world, repo, tmp_path, "ok", run_class="locked")
    assert rc == EXIT_OK
    reg = list(csv.DictReader((out / "experiment_registry.csv").open()))
    assert reg[0]["run_class"] == "locked"


OT_KEYS = ["ot_svr", "ot_svr_pot", "author_pca50", "svr_no_adaptation"]


def _ot_over(**over):
    base = dict(
        mode="transductive_batch",
        allowed_target_information="unlabeled_X_only",
        forbidden_target_information=["y", "labels_for_tuning", "labels_for_calibration"],
        optimal_transport={
            "method": "entropic_sinkhorn_barycentric_projection",
            "cost": "euclidean_unnormalized",
            "epsilon": 1.0,  # scaled to the synthetic cost range
            "max_iter": 1000,
            "tol": 1e-9,
        },
        models=OT_KEYS,
    )
    base.update(over)
    return base


def test_ot_run_end_to_end_is_labeled_transductive_with_diagnostics(world, repo, tmp_path):
    rc, out = _run(world, repo, tmp_path, **_ot_over())
    assert rc == EXIT_OK
    (d,) = list(out.glob("M4_*"))
    for name in (
        "predictions.csv",
        "metrics_by_fold.csv",
        "ot_diagnostics.csv",
        "fold_manifest.csv",
        "leakage_audit.json",
        "summary.json",
        "run_report.md",
    ):
        assert (d / name).is_file(), name
    modes = {r["model"]: r["mode"] for r in csv.DictReader((d / "metrics_by_fold.csv").open())}
    assert modes == {
        "ot_svr": "transductive_batch",
        "ot_svr_pot": "transductive_batch",
        "author_pca50": "transductive_batch",
        "svr_no_adaptation": "inductive",
    }
    preds = list(csv.DictReader((d / "predictions.csv").open()))
    assert {p["mode"] for p in preds} == {"transductive_batch", "inductive"}
    diags = [r for r in csv.DictReader((d / "ot_diagnostics.csv").open()) if r["model"] == "ot_svr"]
    assert len(diags) == 5 and all(r["converged"] == "True" for r in diags)
    assert all(
        float(r["col_marginal_sq_l2"]) < 1e-9 and abs(float(r["total_mass"]) - 1) < 1e-6
        for r in diags
    )
    assert {int(r["n_target"]) for r in diags} == {30} and {int(r["n_source"]) for r in diags} == {
        120
    }
    summary = json.loads((d / "summary.json").read_text())
    assert (
        "TRANSDUCTIVE" in summary["transductive_warning"]
        and summary["mode"] == "transductive_batch"
    )
    assert "NOT a ChemiProof measurement" in summary["published_reference_not_measured"]["status"]
    assert summary["models"]["ot_svr"]["mode"] == "transductive_batch"
    assert summary["models"]["svr_no_adaptation"]["mode"] == "inductive"
    assert json.loads((d / "leakage_audit.json").read_text())["label_shuffle_canary"]["passed"]
    report = (d / "run_report.md").read_text()
    assert "TRANSDUCTIVE RESEARCH MODE" in report and "never be advertised" in report
    # T015: published reference numbers never show up as measured numbers
    measured = {
        round(float(r["r2"]), 3) for r in csv.DictReader((d / "metrics_by_fold.csv").open())
    }
    assert 0.965 not in measured and 0.831 not in measured
    assert "paper_reported" not in json.dumps(summary["models"])


def test_ot_predictions_ignore_heldout_labels_even_in_the_runner(
    world, repo, tmp_path, monkeypatch
):
    """Spy on the OT function: it must never receive anything shaped like the target labels."""
    from chemiproof.modeling import ot

    seen = []
    real = ot.ot_svr_fit_predict

    def spy(xs, ys, xt, cfg=ot.DEFAULT_OT):
        seen.append((xs.shape, ys.shape, xt.shape))
        return real(xs, ys, xt, cfg)

    monkeypatch.setattr(ot, "ot_svr_fit_predict", spy)
    rc, _ = _run(world, repo, tmp_path, **_ot_over(models=["ot_svr"]))
    assert rc == EXIT_OK
    assert seen and all(ys == (xs[0],) for xs, ys, _ in seen)  # labels only for the SOURCE rows


@pytest.mark.parametrize(
    "over",
    [
        dict(mode="transductive_batch", models=["pls"]),  # inductive model in OT mode
        dict(models=["ot_svr"]),  # OT model in inductive mode
        dict(protocol="source_internal_loro", **_ot_over()),  # OT only defined for LOAO
    ],
)
def test_mode_and_model_mismatches_are_refused(world, repo, tmp_path, capsys, over):
    if over.get("mode") == "transductive_batch" and "allowed_target_information" not in over:
        over = {
            **over,
            "allowed_target_information": "unlabeled_X_only",
            "forbidden_target_information": ["y"],
        }
    rc, out = _run(world, repo, tmp_path, **over)
    assert rc == EXIT_ERROR and "INVALID_CONFIG" in capsys.readouterr().err
    assert not out.exists()


def test_ot_without_the_optimal_transport_section_or_with_wrong_method_is_refused(
    world, repo, tmp_path, capsys
):
    rc, _ = _run(world, repo, tmp_path, **_ot_over(optimal_transport={"method": "magic"}))
    assert rc == EXIT_ERROR and "INVALID_CONFIG" in capsys.readouterr().err


def test_unknown_brand_subset_is_refused(world, repo, tmp_path, capsys):
    rc, _ = _run(world, repo, tmp_path, subset_brand="olivera")  # no such samples in this tree
    assert rc == EXIT_ERROR and "INVALID_CONFIG" in capsys.readouterr().err


def test_batch_sensitivity_runs_and_labels_itself_exploratory(world, repo, tmp_path):
    import yaml as _yaml

    from chemiproof.cli import main as _main

    cfg = _cfg(world, repo, tmp_path, **_ot_over())
    out = tmp_path / "bs"
    rc = _main(
        [
            "experiment",
            "batch-sensitivity",
            "--config",
            str(cfg),
            "--data-dir",
            str(world[1]),
            "--output-root",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    (d,) = list(out.glob("M4_batch_sensitivity_*"))
    doc = json.loads((d / "batch_sensitivity.json").read_text())
    assert "TRANSDUCTIVE" in doc["warning"] and doc["sizes"] == [10, 20]
    walnut = doc["folds"]["LOAO-walnut"]
    assert {"random_10|ot_svr", "random_20|svr_no_adaptation"} <= set(walnut)
    assert walnut["random_10|ot_svr"]["n_batches"] == 5
    assert {"skew_low_olive|ot_svr", "skew_high_olive|svr_no_adaptation"} <= set(walnut)  # ADR-015
    reg = list(csv.DictReader((out / "experiment_registry.csv").open()))
    assert (
        reg[-1]["run_class"] == "exploratory" and reg[-1]["protocol"] == "loao_ot_batch_sensitivity"
    )
    assert _yaml  # (imported to keep the helper config path explicit)


def test_screen_single_refuses_transductive_requests():
    from chemiproof import pipeline
    from chemiproof.errors import ChemiProofError, StatusCode

    with pytest.raises(ChemiProofError) as e:
        pipeline.screen_single("one_file.dat", mode="transductive_batch")
    assert e.value.code is StatusCode.TRANSDUCTIVE_BATCH_REQUIRED  # T013
