"""End-to-end M5 on the SYNTHETIC Luhua-only tree used by the LOAO integration test."""

import csv
import json

import pytest
import yaml
from test_loao_run import world  # noqa: F401  (module fixture)

from chemiproof import experiments
from chemiproof.errors import ChemiProofError


def _cfg(world, repo, tmp_path, **over):  # noqa: F811
    _, _, manifest = world
    cfg = yaml.safe_load((repo / "config/experiments/uncertainty_loao.yaml").read_text())
    cfg.update(dataset_manifest=str(manifest), subset_brand="luhua", run_class="exploratory")
    cfg["uncertainty"]["random_rejection_repeats"] = 20
    cfg["perturbations"]["noise_seeds"] = [20261024, 20261025]
    cfg.update(over)
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return p


@pytest.fixture(scope="module")
def uq_out(world, tmp_path_factory):  # noqa: F811
    from pathlib import Path

    from chemiproof.config import load_experiment_config

    repo = Path(__file__).resolve().parents[2]
    tmp = tmp_path_factory.mktemp("uq")
    cfg = load_experiment_config(_cfg(world, repo, tmp))
    _, root, manifest = world
    return experiments.run_uncertainty_experiment(cfg, root, manifest, tmp / "res")


def _rows(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_artifacts_and_canary(uq_out):
    for f in ("predictions.csv", "selective_risk.csv", "risk_coverage_curve.csv",
              "interval_coverage.csv", "perturbation_table.csv", "usefulness.json",
              "leakage_audit.json", "run_report.md", "summary.json"):  # fmt: skip
        assert (uq_out / f).is_file(), f
    audit = json.loads((uq_out / "leakage_audit.json").read_text())
    assert audit["label_shuffle_canary"]["passed"]
    assert all(f["unchanged"] for f in audit["label_shuffle_canary"]["folds"])
    summ = json.loads((uq_out / "summary.json").read_text())
    assert summ["mode"] == "inductive" and summ["protocol_id"] == "LOAO-UQ-v1"


def test_coverage_rows_are_empirical_and_complete(uq_out):
    cov = _rows(uq_out / "interval_coverage.csv")
    assert len(cov) == 5 * 3 * 2  # folds x models x variants
    assert all("no guarantee" in r["note"] for r in cov)
    assert all(0.0 <= float(r["observed_coverage"]) <= 1.0 for r in cov)


def test_retention_goal_one_keeps_all(uq_out):
    sel = _rows(uq_out / "selective_risk.csv")
    full = [r for r in sel if float(r["retention_goal"]) == 1.0]
    assert full and all(float(r["observed_retention"]) == 1.0 for r in full)
    assert all(r["mode"] == "inductive" for r in sel)


def test_offset_and_scale_do_not_change_features(uq_out):
    pert = _rows(uq_out / "perturbation_table.csv")
    inv = [r for r in pert if r["perturbation"] in ("offset", "scale")]
    assert inv and all(float(r["max_abs_feature_change"]) < 1e-8 for r in inv)
    noisy = [r for r in pert if r["perturbation"] == "noise" and float(r["level"]) >= 0.03]
    assert any(float(r["max_abs_feature_change"]) > 1e-3 for r in noisy)


def test_locked_run_needs_clean_tree_error_type(world, tmp_path):  # noqa: F811
    from pathlib import Path

    from chemiproof.config import load_experiment_config

    repo = Path(__file__).resolve().parents[2]
    p = _cfg(world, repo, tmp_path)
    cfg = load_experiment_config(p).model_copy(update={"protocol": "loao", "mode": "inductive"})
    bad = cfg.model_dump()
    bad["uncertainty"]["protocol_id"] = "WRONG"
    from chemiproof.config import ExperimentConfig

    with pytest.raises(ChemiProofError):
        _, root, manifest = world
        experiments.run_uncertainty_experiment(
            ExperimentConfig(**bad), root, manifest, tmp_path / "r"
        )
