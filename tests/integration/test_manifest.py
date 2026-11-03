"""Manifest/audit on a SYNTHETIC archive tree in the real folder layout (no real data needed)."""

import shutil
from pathlib import Path

import numpy as np
import pytest

from chemiproof.data.manifest import (
    build_audit,
    build_manifest,
    read_manifest_csv,
    write_manifest_csv,
)
from chemiproof.data.synthetic import make_synthetic_eem
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.pipeline import load_dataset
from helpers import write_dat

GROUP = "鲁花特级初榨混晟麦核桃油"  # luhua + walnut
ROUNDS = ("第一轮", "第二轮", "第三轮")


def _tree(root: Path, ratios=(1, 10), rounds=ROUNDS) -> Path:
    seed = 0
    for rnd in rounds:
        for a in ratios:
            seed += 1
            write_dat(root / GROUP / rnd / f"{a}：{11 - a}" / "0_RM.dat", make_synthetic_eem(seed))
    return root


def test_rows_labels_and_axes(tmp_path):
    res = build_manifest(_tree(tmp_path / "d"))
    assert len(res.rows) == 6 and not res.problems
    r = next(x for x in res.rows if x.olive_ratio_raw == "10：1" and x.measurement_round == 2)
    assert (r.adulterant_type, r.evoo_brand) == ("walnut", "luhua")
    assert r.olive_fraction == pytest.approx(10 / 11)
    assert r.source_excitation_order == "descending" and r.excitation_min_nm < r.excitation_max_nm
    assert len({x.sample_id for x in res.rows}) == 6
    assert r.replicate_id == ""  # not guessed


def test_audit_reports_every_deviation_from_expectations(tmp_path):
    ledger = "\n".join(build_audit(build_manifest(_tree(tmp_path / "d")))["discrepancy_ledger"])
    assert "total records 6, expected 330" in ledger
    assert "walnut: observed 6, expected 30" in ledger
    assert "soybean: observed 0, expected 60" in ledger
    assert "luhua/walnut: 2 ratio levels, expected 10" in ledger


def test_t006_duplicate_content_is_reported_not_hidden(tmp_path):
    root = _tree(tmp_path / "d")
    a = root / GROUP / "第一轮" / "1：10" / "0_RM.dat"
    shutil.copy(a, root / GROUP / "第二轮" / "1：10" / "0_RM.dat")
    audit = build_audit(build_manifest(root))
    assert audit["duplicate_hashes"] == 1
    assert any("duplicate file contents" in x for x in audit["discrepancy_ledger"])


def test_t005_malformed_dat_is_a_problem_with_path_info_not_silently_skipped(tmp_path):
    root = _tree(tmp_path / "d")
    bad = root / GROUP / "第三轮" / "10：1" / "0_RM.dat"
    bad.write_text("Sample\t1\t2\nnm\nNormalized by 1.00\n1\t2\t3\n")
    res = build_manifest(root)
    assert len(res.rows) == 5
    assert len(res.problems) == 1 and "第三轮/10：1/0_RM.dat" in res.problems[0]["path"]
    assert any("problem:" in x for x in build_audit(res)["discrepancy_ledger"])


def test_unknown_folders_and_missing_or_multiple_dat_are_problems(tmp_path):
    root = _tree(tmp_path / "d")
    write_dat(root / "神秘油" / "第一轮" / "1：10" / "0.dat", make_synthetic_eem(99))
    (root / GROUP / "第一轮" / "10：1" / "0_RM.dat").unlink()
    write_dat(root / GROUP / "第二轮" / "10：1" / "extra.dat", make_synthetic_eem(98))
    res = build_manifest(root)
    issues = " | ".join(p["issue"] for p in res.problems)
    assert "unrecognized group folder" in issues
    assert "found 0" in issues and "found 2" in issues


def test_manifest_csv_roundtrip_and_dataset_loading(tmp_path):
    root = _tree(tmp_path / "d")
    res = build_manifest(root)
    csv_path = tmp_path / "m.csv"
    write_manifest_csv(res.rows, csv_path)
    assert read_manifest_csv(csv_path) == res.rows
    ds = load_dataset(csv_path, root)
    assert ds.features().shape == (6, 9450) and ds.y.shape == (6,)
    assert set(np.round(ds.y * 11)) == {1.0, 10.0}
    assert set(ds.groups) == {"walnut"}


def test_dataset_load_fails_if_a_file_changed_after_manifest(tmp_path):
    root = _tree(tmp_path / "d")
    csv_path = tmp_path / "m.csv"
    write_manifest_csv(build_manifest(root).rows, csv_path)
    f = root / GROUP / "第一轮" / "1：10" / "0_RM.dat"
    f.write_text(f.read_text().replace("Normalized by 1.00", "Normalized by 2.00"))
    with pytest.raises(ChemiProofError) as e:
        load_dataset(csv_path, root)
    assert e.value.code is StatusCode.BAD_FILE_FORMAT


def test_missing_data_dir_or_manifest_is_dataset_not_available(tmp_path):
    with pytest.raises(ChemiProofError) as e:
        build_manifest(tmp_path / "nope")
    assert e.value.code is StatusCode.DATASET_NOT_AVAILABLE
    with pytest.raises(ChemiProofError) as e:
        load_dataset(tmp_path / "nope.csv", tmp_path)
    assert e.value.code is StatusCode.DATASET_NOT_AVAILABLE
