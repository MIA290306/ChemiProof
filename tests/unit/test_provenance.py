from datetime import UTC, datetime

from chemiproof.provenance import config_hash, environment_info, file_sha256, make_run_id


def test_config_hash_is_order_independent_and_sensitive():
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})
    assert config_hash({"a": 1}) != config_hash({"a": 2})


def test_run_id_deterministic_and_well_formed():
    now = datetime(2026, 11, 2, 12, 30, 5, tzinfo=UTC)
    rid = make_run_id({"seed": 1}, now=now, git="abc1234")
    assert rid == make_run_id({"seed": 1}, now=now, git="abc1234")
    ts, git, cfg = rid.split("_")
    assert ts == "20261102T123005Z" and git == "abc1234" and len(cfg) == 8
    assert make_run_id({"seed": 2}, now=now, git="abc1234") != rid


def test_dirty_marker_is_filesystem_safe():
    assert "+" not in make_run_id({}, git="abc1234+dirty")


def test_file_sha256_known_value(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"abc")
    assert file_sha256(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_environment_info_has_versions():
    info = environment_info()
    assert info["python"].startswith("3.12") and "numpy" in info["packages"]
