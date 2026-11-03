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


def test_transductive_mode_is_not_runnable_here(world, repo, tmp_path, capsys):
    rc, _ = _run(
        world,
        repo,
        tmp_path,
        mode="transductive_batch",
        allowed_target_information="unlabeled_X_only",
        forbidden_target_information=["y"],
    )
    assert rc == EXIT_ERROR and "NOT_IMPLEMENTED" in capsys.readouterr().err


def test_unknown_brand_subset_is_refused(world, repo, tmp_path, capsys):
    rc, _ = _run(world, repo, tmp_path, subset_brand="olivera")  # no such samples in this tree
    assert rc == EXIT_ERROR and "INVALID_CONFIG" in capsys.readouterr().err
