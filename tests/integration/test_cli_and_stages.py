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
    rc = main(["dataset", "audit", "--archive", str(tmp_path / "data.zip")])
    assert rc == EXIT_ERROR and "DATASET_NOT_AVAILABLE" in capsys.readouterr().err


def test_dataset_present_but_audit_not_implemented(tmp_path, capsys):
    archive = tmp_path / "data.zip"
    archive.write_bytes(b"")
    assert main(["dataset", "inspect", "--archive", str(archive)]) == EXIT_ERROR
    assert "NOT_IMPLEMENTED" in capsys.readouterr().err


def test_experiment_run_validates_config_first_then_needs_dataset(repo, tmp_path, capsys):
    bad = tmp_path / "b.yaml"
    bad.write_text("mode: magic\n")
    assert main(["experiment", "run", "--config", str(bad)]) == EXIT_ERROR
    assert "INVALID_CONFIG" in capsys.readouterr().err
    rc = main(["experiment", "run", "--config", str(repo / "config/experiments/baseline.yaml")])
    assert rc == EXIT_ERROR and "DATASET_NOT_AVAILABLE" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [["app"], ["spectra", "plot"], ["experiment", "report"]])
def test_later_milestone_commands_are_truthful(argv, capsys):
    assert main(argv) == EXIT_ERROR
    assert "NOT_IMPLEMENTED" in capsys.readouterr().err


def test_load_dataset_missing_manifest(tmp_path):
    with pytest.raises(ChemiProofError) as e:
        pipeline.load_dataset(tmp_path / "sample_manifest.csv")
    assert e.value.code is StatusCode.DATASET_NOT_AVAILABLE


def test_screen_single_never_returns_a_prediction():
    with pytest.raises(ChemiProofError) as e:
        pipeline.screen_single("anything")
    assert e.value.code is StatusCode.NO_TRAINED_MODEL


@pytest.mark.dataset
def test_real_archive_present_placeholder(repo):
    """Dataset-gated: fails loudly (never silently skipped) when the archive is absent."""
    assert (repo / "data/raw/data.zip").is_file(), "DATASET_NOT_AVAILABLE: real archive missing"
