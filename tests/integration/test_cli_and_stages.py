"""CLI behaviour and honest failure of unimplemented stages (no fabricated passing science)."""

import pytest

from chemiproof import pipeline
from chemiproof.cli import EXIT_ERROR, EXIT_OK, main
from chemiproof.errors import ChemiProofError, StatusCode


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    assert "NOT a certified authenticity test" in " ".join(capsys.readouterr().out.split())


def test_config_validate_ok_and_bad(repo, tmp_path, capsys):
    assert main(["config", "validate", "project", str(repo / "config/project.yaml")]) == EXIT_OK
    bad = tmp_path / "b.yaml"
    bad.write_text("mode: magic\n")
    assert main(["config", "validate", "experiment", str(bad)]) == EXIT_ERROR
    assert "INVALID_CONFIG" in capsys.readouterr().err


def test_dataset_missing_reports_dataset_not_available(tmp_path, capsys):
    rc = main(["dataset", "audit", "--data-dir", str(tmp_path / "nope")])
    assert rc == EXIT_ERROR and "DATASET_NOT_AVAILABLE" in capsys.readouterr().err
    rc = main(["dataset", "inspect-zip", "--archive", str(tmp_path / "data.zip")])
    assert rc == EXIT_ERROR and "DATASET_NOT_AVAILABLE" in capsys.readouterr().err


def test_inspect_zip_command_and_unsafe_zip(tmp_path, capsys):
    import zipfile

    ok = tmp_path / "ok.zip"
    with zipfile.ZipFile(ok, "w") as zf:
        zf.writestr("a/1.dat", "x")
    assert main(["dataset", "inspect-zip", "--archive", str(ok)]) == EXIT_OK
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("../evil.dat", "x")
    assert main(["dataset", "inspect-zip", "--archive", str(bad)]) == EXIT_ERROR
    assert "BAD_FILE_FORMAT" in capsys.readouterr().err


def test_audit_command_on_synthetic_tree_flags_discrepancies(tmp_path, capsys):
    from chemiproof.data.synthetic import make_synthetic_eem
    from helpers import write_dat

    root = tmp_path / "d"
    write_dat(
        root / "鲁花特级初榨混晟麦核桃油" / "第一轮" / "10：1" / "0.dat", make_synthetic_eem(1)
    )
    args = [
        "dataset",
        "audit",
        "--data-dir",
        str(root),
        "--manifest",
        str(tmp_path / "m.csv"),
        "--output-dir",
        str(tmp_path / "out"),
    ]
    rc = main(args)
    err = capsys.readouterr().err
    assert rc == EXIT_ERROR and "QC_REVIEW_REQUIRED" in err and "expected 330" in err
    assert (tmp_path / "out/data_audit.json").is_file() and (tmp_path / "m.csv").is_file()


def test_experiment_run_validates_config_first_then_needs_dataset(repo, tmp_path, capsys):
    import yaml

    bad = tmp_path / "b.yaml"
    bad.write_text("mode: magic\n")
    assert main(["experiment", "run", "--config", str(bad)]) == EXIT_ERROR
    assert "INVALID_CONFIG" in capsys.readouterr().err
    cfg = yaml.safe_load((repo / "config/experiments/baseline.yaml").read_text())
    cfg["run_class"] = "exploratory"  # independent of the git tree state
    good = tmp_path / "g.yaml"
    good.write_text(yaml.safe_dump(cfg))
    rc = main(["experiment", "run", "--config", str(good), "--data-dir", str(tmp_path / "nodata")])
    assert rc == EXIT_ERROR and "DATASET_NOT_AVAILABLE" in capsys.readouterr().err


def test_experiment_compare_cli(tmp_path, capsys):
    ref, new = tmp_path / "ref", tmp_path / "new"
    for d, pred in ((ref, "0.5"), (new, "0.5000000000001")):
        d.mkdir()
        (d / "predictions.csv").write_text(f"run_id,y_pred_fraction\n{d.name},{pred}\n")
    assert main(["experiment", "compare", str(ref), str(new)]) == 0
    assert "1/1 files match" in capsys.readouterr().out
    (new / "predictions.csv").write_text("run_id,y_pred_fraction\nnew,0.51\n")
    assert main(["experiment", "compare", str(ref), str(new)]) == 1
    assert main(["experiment", "compare", str(ref), str(tmp_path / "absent")]) == EXIT_ERROR


def test_load_dataset_missing_manifest(tmp_path):
    with pytest.raises(ChemiProofError) as e:
        pipeline.load_dataset(tmp_path / "sample_manifest.csv", tmp_path)
    assert e.value.code is StatusCode.DATASET_NOT_AVAILABLE


def test_screen_single_never_returns_a_prediction():
    with pytest.raises(ChemiProofError) as e:
        pipeline.screen_single("anything")
    assert e.value.code is StatusCode.NO_TRAINED_MODEL
