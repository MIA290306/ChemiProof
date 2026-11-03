"""T002: malicious archives are rejected before anything is extracted."""

import stat
import warnings
import zipfile
from pathlib import Path

import pytest

from chemiproof.data.zipsafe import inspect_zip, safe_extract
from chemiproof.errors import ChemiProofError, StatusCode


def _zip(path: Path, members: dict[str, bytes], symlink: str | None = None) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
        if symlink:
            info = zipfile.ZipInfo(symlink)
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(info, "/etc/passwd")
    return path


@pytest.mark.parametrize(
    "name", ["../evil.dat", "a/../../evil.dat", "/abs/evil.dat", "a\\..\\b.dat", "C:/evil.dat"]
)
def test_t002_traversal_and_absolute_paths_rejected(tmp_path, name):
    z = _zip(tmp_path / "bad.zip", {name: b"x"})
    with pytest.raises(ChemiProofError) as e:
        inspect_zip(z)
    assert e.value.code is StatusCode.BAD_FILE_FORMAT
    dest = tmp_path / "out"
    with pytest.raises(ChemiProofError):
        safe_extract(z, dest)
    assert not any(tmp_path.rglob("evil.dat"))  # nothing was written anywhere


def test_symlink_member_rejected(tmp_path):
    z = _zip(tmp_path / "s.zip", {"ok.dat": b"1"}, symlink="link")
    with pytest.raises(ChemiProofError):
        inspect_zip(z)


@pytest.mark.parametrize(("first", "second"), [("a.dat", "a.dat"), ("a.dat", "A.dat")])
def test_duplicate_member_names_rejected_case_insensitively(tmp_path, first, second):
    p = tmp_path / "d.zip"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # zipfile warns on exact duplicates
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr(first, b"1")
            zf.writestr(second, b"2")
    with pytest.raises(ChemiProofError):
        inspect_zip(p)


def test_archive_bomb_ratio_rejected(tmp_path):
    z = _zip(tmp_path / "bomb.zip", {"zeros.dat": b"\0" * 5_000_000})
    with pytest.raises(ChemiProofError) as e:
        inspect_zip(z)
    assert "compression ratio" in e.value.message


def test_not_a_zip_rejected(tmp_path):
    p = tmp_path / "n.zip"
    p.write_bytes(b"not a zip")
    with pytest.raises(ChemiProofError):
        inspect_zip(p)


def test_valid_zip_inspected_and_extracted_into_empty_dir(tmp_path):
    z = _zip(tmp_path / "ok.zip", {"g/r/1.dat": b"abc", "g/r/2.txt": b"def"})
    rep = inspect_zip(z)
    assert rep.members == 2 and rep.extensions == {".dat": 1, ".txt": 1}
    dest = tmp_path / "out"
    safe_extract(z, dest)
    assert (dest / "g/r/1.dat").read_bytes() == b"abc"
    with pytest.raises(ChemiProofError):  # non-empty destination refused
        safe_extract(z, dest)
