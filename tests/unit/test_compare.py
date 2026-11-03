"""T021 rerun equality check: tolerance, ignored run_id, structural and text differences."""

import pytest

from chemiproof.errors import ChemiProofError
from chemiproof.evaluation.compare import compare_run_dirs

HEADER = "run_id,fold_id,mae_fraction,abstain\n"


def _run(path, rows, manifest="abc"):
    path.mkdir()
    (path / "metrics_by_fold.csv").write_text(HEADER + "".join(rows))
    (path / "dataset_manifest_sha256.txt").write_text(manifest + "\n")
    return path


def test_identical_except_run_id_and_round_off(tmp_path):
    ref = _run(tmp_path / "a", ["r1,LOAO-corn,0.05,\n", "r1,LOAO-walnut,nan,True\n"])
    new = _run(tmp_path / "b", ["r2,LOAO-corn,0.05000000000002,\n", "r2,LOAO-walnut,nan,True\n"])
    res = {r.name: r for r in compare_run_dirs(ref, new)}
    assert all(r.ok for r in res.values())
    assert 0 < res["metrics_by_fold.csv"].max_abs_diff < 1e-12


@pytest.mark.parametrize(
    "rows, manifest, expect",
    [
        (["r,LOAO-corn,0.06,\n", "r,LOAO-walnut,nan,True\n"], "abc", "|diff|"),  # beyond atol
        (["r,LOAO-corn,0.05,\n", "r,LOAO-walnut,0.1,True\n"], "abc", "nan"),  # NaN vs number
        (["r,LOAO-peanut,0.05,\n", "r,LOAO-walnut,nan,True\n"], "abc", "LOAO-peanut"),  # text
        (["r,LOAO-corn,0.05,\n"], "abc", "row count"),
        (["r,LOAO-corn,0.05,\n", "r,LOAO-walnut,nan,True\n"], "xyz", "content differs"),
    ],
)
def test_differences_are_reported(tmp_path, rows, manifest, expect):
    ref = _run(tmp_path / "a", ["r1,LOAO-corn,0.05,\n", "r1,LOAO-walnut,nan,True\n"])
    new = _run(tmp_path / "b", rows, manifest)
    problems = [p for r in compare_run_dirs(ref, new) for p in r.problems]
    assert problems and any(expect in p for p in problems)


def test_missing_table_and_bad_folders(tmp_path):
    ref = _run(tmp_path / "a", ["r1,LOAO-corn,0.05,\n"])
    (ref / "splits.csv").write_text("fold_id\nLOAO-corn\n")
    new = _run(tmp_path / "b", ["r2,LOAO-corn,0.05,\n"])
    res = {r.name: r for r in compare_run_dirs(ref, new)}
    assert res["splits.csv"].problems == ["missing in rerun"]
    with pytest.raises(ChemiProofError):
        compare_run_dirs(ref, tmp_path / "absent")
    (tmp_path / "empty").mkdir()
    with pytest.raises(ChemiProofError):
        compare_run_dirs(tmp_path / "empty", new)
