from pathlib import Path

import pytest
import yaml

from chemiproof.config import load_experiment_config, load_project_config
from chemiproof.errors import ChemiProofError, StatusCode


def _write(tmp_path: Path, data: dict, name="c.yaml") -> Path:
    p = tmp_path / name
    p.write_text(yaml.safe_dump(data))
    return p


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def test_repo_configs_are_valid(repo):
    load_project_config(repo / "config/project.yaml")
    load_experiment_config(repo / "config/experiments/baseline.yaml")
    load_experiment_config(repo / "config/experiments/ot_transductive.yaml")


def test_missing_file_and_non_mapping(tmp_path):
    with pytest.raises(ChemiProofError) as e:
        load_project_config(tmp_path / "nope.yaml")
    assert e.value.code is StatusCode.INVALID_CONFIG
    bad = tmp_path / "list.yaml"
    bad.write_text("- 1\n- 2\n")
    with pytest.raises(ChemiProofError):
        load_project_config(bad)


def test_yaml_python_tags_are_not_executed(tmp_path):
    evil = tmp_path / "evil.yaml"
    evil.write_text("a: !!python/object/apply:os.system ['echo pwned']\n")
    with pytest.raises(ChemiProofError):
        load_project_config(evil)


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("project", "accepted_range", [0, 100]),
        ("project", "target_unit", "percent"),
        ("ui", "allow_transductive_single_sample", True),
        ("ui", "certified_authenticity_claims", True),
        ("evaluation", "outer_split", "random"),
        ("evaluation", "adulterants", ["soybean", "peanut"]),
        ("spectra", "expected_features", 1000),
    ],
)
def test_project_config_rejects_scientifically_invalid(repo, tmp_path, section, key, value):
    cfg = _load(repo / "config/project.yaml")
    cfg[section][key] = value
    with pytest.raises(ChemiProofError) as e:
        load_project_config(_write(tmp_path, cfg))
    assert e.value.code is StatusCode.INVALID_CONFIG


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("mode", "magic"),
        ("status", "DONE"),  # a hand-edited config must not claim a finished run
        ("outer_cv", "random_kfold"),
        ("metrics", ["accuracy"]),
    ],
)
def test_experiment_config_rejects_invalid(repo, tmp_path, key, value):
    cfg = _load(repo / "config/experiments/baseline.yaml")
    cfg[key] = value
    with pytest.raises(ChemiProofError):
        load_experiment_config(_write(tmp_path, cfg))


def test_transductive_must_hide_target_labels(repo, tmp_path):
    cfg = _load(repo / "config/experiments/ot_transductive.yaml")
    cfg["forbidden_target_information"] = []
    with pytest.raises(ChemiProofError):
        load_experiment_config(_write(tmp_path, cfg))
    cfg = _load(repo / "config/experiments/ot_transductive.yaml")
    cfg["allowed_target_information"] = "labels"
    with pytest.raises(ChemiProofError):
        load_experiment_config(_write(tmp_path, cfg))


def test_inductive_must_not_declare_target_access(repo, tmp_path):
    cfg = _load(repo / "config/experiments/baseline.yaml")
    cfg["allowed_target_information"] = "unlabeled_X_only"
    with pytest.raises(ChemiProofError):
        load_experiment_config(_write(tmp_path, cfg))


def test_loao_protocol_requires_outer_cv_and_source_internal_does_not(repo, tmp_path):
    cfg = _load(repo / "config/experiments/baseline.yaml")
    cfg.pop("outer_cv")
    with pytest.raises(ChemiProofError):
        load_experiment_config(_write(tmp_path, cfg))
    load_experiment_config(repo / "config/experiments/m2_source_internal.yaml")


def test_unknown_model_key_rejected(repo, tmp_path):
    cfg = _load(repo / "config/experiments/m2_source_internal.yaml")
    cfg["models"] = ["mean_y", "deep_magic"]
    with pytest.raises(ChemiProofError):
        load_experiment_config(_write(tmp_path, cfg))
