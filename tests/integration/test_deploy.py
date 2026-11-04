"""Cloud bootstrap (ADR-021): fails closed, only installs a model that reproduces the locked card.

Synthetic data only (CI-safe, no network): downloads use file:// URLs.
"""

import copy
import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from test_loao_run import world  # noqa: F401  (module fixture)

from chemiproof import cli, deploy
from chemiproof.modeling.final import latest_artifact


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes(), usedforsecurity=False).hexdigest()


@pytest.fixture(scope="module")
def locked(world, tmp_path_factory):  # noqa: F811
    """A 'committed' results tree: the card of a FINAL-PLS-v1 trained on the synthetic data,
    with its model.npz removed exactly as git-ignore does in the real repository."""
    _, root, manifest = world
    res = tmp_path_factory.mktemp("locked_results")
    assert cli.main(["model", "train-final", "--data-dir", str(root), "--manifest",
                     str(manifest), "--output-root", str(res)]) == 0  # fmt: skip
    art = latest_artifact(res)
    (art / "model.npz").unlink()
    (res / "experiment_registry.csv").unlink()
    return res, json.loads((art / "model_card.json").read_text(encoding="utf-8"))


def test_check_card_accepts_identical_and_rounding_only(locked):
    _, card = locked
    deploy.check_card(card, card)
    near = copy.deepcopy(card)
    near["ood"]["threshold"] *= 1 + 1e-12
    deploy.check_card(near, card)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda c: c.__setitem__("n_components", c["n_components"] + 2),
        lambda c: c.__setitem__("manifest_sha256", "0" * 64),
        lambda c: c.__setitem__("train_sample_ids_hash", "0" * 64),
        lambda c: c["ood"].__setitem__("threshold", c["ood"]["threshold"] * 1.001),
        lambda c: c["interval"]["halfwidth_fraction"].__setitem__("pooled", 0.5),
    ],
)
def test_check_card_rejects_a_different_model(locked, mutate):
    _, card = locked
    other = copy.deepcopy(card)
    mutate(other)
    with pytest.raises(deploy.BootstrapError):
        deploy.check_card(other, card)


def test_download_verifies_published_md5(tmp_path):
    src = tmp_path / "src.zip"
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("a/b.dat", "x")
    dest = tmp_path / "cache" / "data.zip"
    with pytest.raises(deploy.BootstrapError, match="MD5 mismatch"):
        deploy.download_zip(dest, src.as_uri(), "0" * 32)
    assert not dest.exists() and not dest.with_suffix(".part").exists()
    assert deploy.download_zip(dest, src.as_uri(), _md5(src)) == dest
    assert _md5(dest) == _md5(src)


def test_data_root_unwraps_single_top_level_folder(tmp_path):
    (tmp_path / "data" / "brand_a").mkdir(parents=True)
    (tmp_path / "data" / "brand_b").mkdir()
    (tmp_path / "__MACOSX").mkdir()
    assert deploy._data_root(tmp_path) == tmp_path / "data"


def test_bad_download_leaves_app_degraded(locked, tmp_path):
    res, _ = locked
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not the dataset")
    rep = deploy.ensure_ready(res, tmp_path / "raw", tmp_path / "m.csv", tmp_path / "work",
                              url=bad.as_uri())  # fmt: skip
    assert rep.status == "failed" and "MD5 mismatch" in rep.error
    assert latest_artifact(res) is None and not (tmp_path / "raw").exists()


def test_rebuild_installs_model_only_when_it_reproduces_locked_card(world, locked, tmp_path):  # noqa: F811
    _, root, manifest = world
    res, card = locked
    results = tmp_path / "results"
    results.mkdir()
    for p in res.iterdir():  # copy of the 'committed' tree
        (results / p.name).mkdir()
        (results / p.name / "model_card.json").write_bytes((p / "model_card.json").read_bytes())
    rep = deploy.ensure_ready(results, root, manifest, tmp_path / "work")
    assert rep.status == "ready", rep.error
    art = latest_artifact(results)
    assert art is not None and str(art) == rep.artifact
    again = deploy.ensure_ready(results, root, manifest, tmp_path / "work")
    assert again.status == "already_present"


def test_rebuild_refuses_model_that_differs_from_locked_card(world, locked, tmp_path):  # noqa: F811
    _, root, manifest = world
    res, card = locked
    results = tmp_path / "results"
    tampered = copy.deepcopy(card)
    tampered["ood"]["threshold"] += 1.0
    d = results / f"M6_final_{card['run_id']}"
    d.mkdir(parents=True)
    (d / "model_card.json").write_text(json.dumps(tampered), encoding="utf-8")
    rep = deploy.ensure_ready(results, root, manifest, tmp_path / "work")
    assert rep.status == "failed" and "ood.threshold" in rep.error
    assert latest_artifact(results) is None
