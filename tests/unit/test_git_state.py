"""The dirty flag must reflect code/doc changes but not the run registry or untracked files."""

import subprocess

from chemiproof.evaluation.runner import git_state
from chemiproof.provenance import git_short_hash


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_dirty_flag_ignores_registry_and_untracked_but_sees_real_changes(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "results").mkdir()
    (tmp_path / "results/experiment_registry.csv").write_text("a\n")
    (tmp_path / "code.py").write_text("x = 1\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "init")
    assert git_state(tmp_path)["dirty"] is False
    (tmp_path / "results/experiment_registry.csv").write_text("a\nb\n")  # registry append
    (tmp_path / "scratch.txt").write_text("untracked")
    assert git_state(tmp_path)["dirty"] is False
    assert not git_short_hash(tmp_path).endswith("+dirty")
    (tmp_path / "code.py").write_text("x = 2\n")  # a real tracked change
    assert git_state(tmp_path)["dirty"] is True
    assert git_short_hash(tmp_path).endswith("+dirty")
