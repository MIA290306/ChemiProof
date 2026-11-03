"""End-to-end `experiment run` on a SYNTHETIC archive tree: artifacts, determinism, refusals."""

import csv
import json
from pathlib import Path

import pytest
import yaml

from chemiproof.cli import EXIT_ERROR, EXIT_OK, main
from chemiproof.data.manifest import build_manifest, write_manifest_csv
from helpers import mixture_eem, write_dat

GROUP = "鲁花特级初榨混晟麦核桃油"


@pytest.fixture
def synthetic_world(tmp_path, repo):
    root = tmp_path / "d"
    i = 0
    for rnd in ("第一轮", "第二轮", "第三轮"):
        for a in range(1, 11):
            i += 1
            spec = mixture_eem(a / 11, noise=0.002, rng_seed=i)
            write_dat(root / GROUP / rnd / f"{a}：{11 - a}" / "0_RM.dat", spec)
    manifest = tmp_path / "m.csv"
    write_manifest_csv(build_manifest(root).rows, manifest)
    cfg = yaml.safe_load((repo / "config/experiments/m2_source_internal.yaml").read_text())
    cfg["dataset_manifest"] = str(manifest)
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))
    return root, manifest, cfg, cfg_path


def _run(world, tmp_path, name="out"):
    root, _, _, cfg_path = world
    out = tmp_path / name
    rc = main(
        [
            "experiment",
            "run",
            "--config",
            str(cfg_path),
            "--data-dir",
            str(root),
            "--output-root",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    (run_dir,) = list(out.glob("M2_*"))
    return run_dir


def test_run_writes_full_artifact_set_with_spec_columns(synthetic_world, tmp_path, capsys):
    d = _run(synthetic_world, tmp_path)
    for name in (
        "config_resolved.yaml",
        "environment.json",
        "git_state.json",
        "dataset_manifest_sha256.txt",
        "splits.csv",
        "predictions.csv",
        "metrics_by_fold.csv",
        "summary.json",
        "run_report.md",
    ):
        assert (d / name).is_file(), name
    preds = list(csv.DictReader((d / "predictions.csv").open()))
    assert list(preds[0]) == [
        "run_id",
        "fold_id",
        "source_sample_hash",
        "sample_id",
        "y_true_fraction",
        "y_pred_fraction",
        "model",
        "mode",
        "abstain",
        "ood_score",
        "interval_lo",
        "interval_hi",
    ]
    assert len(preds) == 30 * 4  # every sample predicted once per model
    metrics = list(csv.DictReader((d / "metrics_by_fold.csv").open()))
    assert {
        "run_id",
        "fold_id",
        "model",
        "mode",
        "n",
        "mae_fraction",
        "rmse_fraction",
        "bias_fraction",
        "r2",
        "retention",
    } <= set(metrics[0])
    assert {m["mode"] for m in metrics} == {"inductive"} and len(metrics) == 3 * 4
    summary = json.loads((d / "summary.json").read_text())
    assert "NOT evidence of unseen-adulterant" in " ".join(summary["limitations"])
    assert "FRACTION" in summary["units"] and summary["manifest_sha256"]
    assert summary["models"]["pls"]["macro_over_folds"]["r2"] > 0.9
    assert "Optimistic protocol" in capsys.readouterr().out


def test_two_runs_give_identical_predictions(synthetic_world, tmp_path):
    a = _run(synthetic_world, tmp_path, "a")
    b = _run(synthetic_world, tmp_path, "b")
    pa = [
        (r["sample_id"], r["model"], r["y_pred_fraction"])
        for r in csv.DictReader((a / "predictions.csv").open())
    ]
    pb = [
        (r["sample_id"], r["model"], r["y_pred_fraction"])
        for r in csv.DictReader((b / "predictions.csv").open())
    ]
    assert pa == pb


def test_config_hash_is_part_of_the_run_id_and_changes_with_config(synthetic_world, tmp_path):
    root, manifest, cfg, cfg_path = synthetic_world
    a = _run(synthetic_world, tmp_path, "a")
    cfg["models"] = ["mean_y", "pls"]
    cfg_path.write_text(yaml.safe_dump(cfg))
    b = _run(synthetic_world, tmp_path, "b")
    assert a.name != b.name


@pytest.mark.parametrize(
    ("key", "value", "needle"),
    [
        ("mode", "transductive_batch", "NOT_IMPLEMENTED"),
        ("random_seed", 1, "INVALID_CONFIG"),
    ],
)
def test_refuses_invalid_runs(synthetic_world, tmp_path, capsys, key, value, needle):
    root, _, cfg, cfg_path = synthetic_world
    cfg[key] = value
    if key == "mode":
        cfg["allowed_target_information"] = "unlabeled_X_only"
        cfg["forbidden_target_information"] = ["y"]
    cfg_path.write_text(yaml.safe_dump(cfg))
    rc = main(
        [
            "experiment",
            "run",
            "--config",
            str(cfg_path),
            "--data-dir",
            str(root),
            "--output-root",
            str(tmp_path / "o"),
        ]
    )
    assert rc == EXIT_ERROR and needle in capsys.readouterr().err


def test_unknown_preprocessing_version_refused(synthetic_world, tmp_path, capsys):
    root, _, cfg, cfg_path = synthetic_world
    cfg["preprocessing"]["version"] = "my_tuned_v2"
    cfg_path.write_text(yaml.safe_dump(cfg))
    rc = main(
        [
            "experiment",
            "run",
            "--config",
            str(cfg_path),
            "--data-dir",
            str(root),
            "--output-root",
            str(tmp_path / "o"),
        ]
    )
    assert rc == EXIT_ERROR and "unknown preprocessing version" in capsys.readouterr().err


def test_loao_without_data_reports_dataset_not_available(repo, tmp_path, capsys):
    rc = main(
        [
            "experiment",
            "run",
            "--config",
            str(repo / "config/experiments/baseline.yaml"),
            "--data-dir",
            str(tmp_path / "nodata"),
            "--output-root",
            str(tmp_path),
        ]
    )
    assert rc == EXIT_ERROR
    assert "DATASET_NOT_AVAILABLE" in capsys.readouterr().err


def test_modified_data_file_is_detected_before_any_model_runs(synthetic_world, tmp_path, capsys):
    root, _, _, cfg_path = synthetic_world
    victim = next(Path(root).rglob("0_RM.dat"))
    victim.write_text(victim.read_text().replace("Normalized by 1.00", "Normalized by 3.00"))
    rc = main(
        [
            "experiment",
            "run",
            "--config",
            str(cfg_path),
            "--data-dir",
            str(root),
            "--output-root",
            str(tmp_path / "o"),
        ]
    )
    assert rc == EXIT_ERROR and "changed since the manifest" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()
