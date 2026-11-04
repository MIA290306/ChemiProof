"""M6 explorer (Streamlit AppTest): pages render, empty states and refusals are honest.

Benchmark pages read the COMMITTED result folders; the screening model is a SYNTHETIC
FINAL-PLS-v1 trained on the synthetic LOAO tree, so no real data is needed (CI-safe).
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from test_loao_run import world  # noqa: F401  (module fixture)

from chemiproof import pipeline
from chemiproof.modeling import final
from chemiproof.spectra.preprocess import preprocess_features
from helpers import dat_text

APP = str(Path(__file__).resolve().parents[2] / "src/chemiproof/ui/app.py")
PAGES = ["Overview", "Explore EEM", "Benchmarks", "Screen sample", "Batch research",
         "Methods & provenance"]  # fmt: skip
FORBIDDEN = ("fraud detected", "is authentic", "adulterated", "safe to consume", "certified test")


def _text(at: AppTest) -> str:
    parts = [e.value for kind in ("markdown", "caption", "info", "warning", "error", "subheader",
             "header", "title") for e in getattr(at, kind)]  # fmt: skip
    return "\n".join(str(p) for p in parts)


def _app(monkeypatch, results: Path, tmp_path: Path, page: str) -> AppTest:
    monkeypatch.setenv("CHEMIPROOF_RESULTS_DIR", str(results))
    monkeypatch.setenv("CHEMIPROOF_DATA_DIR", str(tmp_path / "no_data"))
    monkeypatch.setenv("CHEMIPROOF_MANIFEST", str(tmp_path / "no_manifest.csv"))
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, at.exception
    return at


@pytest.fixture(scope="module")
def synthetic(world, tmp_path_factory):  # noqa: F811
    _, root, manifest = world
    ds = pipeline.load_dataset(manifest, root)
    s0 = ds.spectra[0]
    m = final.train_final(
        preprocess_features(ds.spectra), ds.y, ds.groups, s0.excitation_nm, s0.emission_nm
    )
    res = tmp_path_factory.mktemp("uires")
    final.save_final(m, res / "M6_final_20990101T000000Z_test_0")
    return res, ds


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders_with_committed_results(page, repo, tmp_path, monkeypatch):
    at = _app(monkeypatch, repo / "results", tmp_path, page)
    text = _text(at).lower()
    assert not any(f in text for f in FORBIDDEN)


@pytest.mark.parametrize("page", ["Screen sample", "Batch research"])
def test_no_model_gives_honest_message(page, tmp_path, monkeypatch):  # T020
    text = _text(_app(monkeypatch, tmp_path, tmp_path, page)).lower()
    assert "research model not available" in text and "estimated" not in text


def test_overview_and_benchmarks_without_runs(tmp_path, monkeypatch):
    for page in ("Overview", "Benchmarks"):
        at = _app(monkeypatch, tmp_path, tmp_path, page)
        assert "No verified benchmark results yet." in _text(at)


def test_overview_separates_measured_and_published(repo, tmp_path, monkeypatch):
    text = _text(_app(monkeypatch, repo / "results", tmp_path, "Overview"))
    assert "not a ChemiProof measurement" in text
    assert "not a certified authenticity test" in text.lower()


def test_screen_valid_upload_gives_labelled_estimate(synthetic, tmp_path, monkeypatch):
    res, ds = synthetic
    at = _app(monkeypatch, res, tmp_path, "Screen sample")
    at.file_uploader[0].set_value(("ok.dat", dat_text(ds.spectra[5]).encode(), "text/plain"))
    text = _text(at.run())
    assert not at.exception
    assert "Estimated olive-oil fraction" in text and "not guaranteed" in text  # T023


def test_screen_invalid_upload_is_refused(synthetic, tmp_path, monkeypatch):  # T019
    res, _ = synthetic
    at = _app(monkeypatch, res, tmp_path, "Screen sample")
    at.file_uploader[0].set_value(("bad.dat", b"Sample\t1\nnot a spectrum\n", "text/plain"))
    at.run()
    assert not at.exception
    errors = " ".join(e.value for e in at.error)
    assert "No estimate: validation failed" in errors and "Estimated" not in _text(at)


def test_batch_page_requires_dataset(synthetic, tmp_path, monkeypatch):
    res, _ = synthetic
    text = _text(_app(monkeypatch, res, tmp_path, "Batch research"))
    assert "transductive" in text.lower() and "dataset is not present" in text


def test_benchmark_runs_dedupe_and_missing(tmp_path):
    from chemiproof.ui import artifacts as A

    for d in ("run_a", "run_b"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "summary.json").write_text("{}")
    head = (
        "utc_time,run_id,experiment_id,protocol,run_class,subset_brand,config_sha256,"
        "git_head,git_dirty,output_dir\n"
    )
    rows = [
        "t1,A,exp,loao,locked,,cfg1,h,False,run_a",
        "t2,A2,exp,loao,locked,,cfg1,h,False,run_b",  # identical config rerun: hidden
        "t3,B,exp,loao,locked,,cfg2,h,False,run_missing",  # locked, no folder: reported
        "t4,C,exp,loao,exploratory,,cfg3,h,False,run_b",  # not locked: ignored
    ]
    (tmp_path / "experiment_registry.csv").write_text(head + "\n".join(rows) + "\n")
    runs, missing = A.benchmark_runs_and_missing(tmp_path)
    assert [r.run_id for r in runs] == ["A"] and missing == ["B"]


def test_dataset_integrity_error_is_not_disguised_as_missing(world, tmp_path, monkeypatch):  # noqa: F811
    import shutil

    _, root, manifest = world
    data = tmp_path / "data"
    shutil.copytree(root, data)
    victim = next(data.rglob("*.dat"))
    victim.write_text(victim.read_text().replace("Normalized by 1.00", "Normalized by 1.01"))
    monkeypatch.setenv("CHEMIPROOF_RESULTS_DIR", str(tmp_path))
    monkeypatch.setenv("CHEMIPROOF_DATA_DIR", str(data))
    monkeypatch.setenv("CHEMIPROOF_MANIFEST", str(manifest))
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.radio[0].set_value("Explore EEM").run()
    assert not at.exception
    assert "BAD_FILE_FORMAT" in " ".join(e.value for e in at.error)


CLOUD_APP = str(Path(__file__).resolve().parents[2] / "streamlit_app.py")


def test_cloud_entry_point_serves_ready_model_without_network(world, synthetic, monkeypatch):  # noqa: F811
    """ADR-021: when a verified model and dataset are present, the bootstrap is a no-op."""
    _, root, manifest = world
    res, _ = synthetic
    monkeypatch.setenv("CHEMIPROOF_RESULTS_DIR", str(res))
    monkeypatch.setenv("CHEMIPROOF_DATA_DIR", str(root))
    monkeypatch.setenv("CHEMIPROOF_MANIFEST", str(manifest))
    at = AppTest.from_file(CLOUD_APP, default_timeout=60).run()
    assert not at.exception, at.exception
    assert len(at.sidebar.radio) == 1  # app.main() ran exactly once (no double render)
    at.sidebar.radio[0].set_value("Screen sample").run()
    assert not at.exception
    assert "research model not available" not in _text(at).lower()


def test_cloud_entry_point_degrades_when_rebuild_impossible(repo, tmp_path, monkeypatch):
    """No locked card -> bootstrap fails before any download; benchmark pages still render."""
    monkeypatch.setenv("CHEMIPROOF_RESULTS_DIR", str(tmp_path))
    monkeypatch.setenv("CHEMIPROOF_DATA_DIR", str(tmp_path / "no_data"))
    monkeypatch.setenv("CHEMIPROOF_MANIFEST", str(tmp_path / "no_manifest.csv"))
    at = AppTest.from_file(CLOUD_APP, default_timeout=60).run()
    assert not at.exception, at.exception
    warn = " ".join(w.value for w in at.sidebar.warning)
    assert "screening is disabled" in warn and "no committed FINAL-PLS-v1" in warn
