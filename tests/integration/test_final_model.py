"""FINAL-PLS-v1 (ADR-018) and the screening entry points, on the SYNTHETIC LOAO tree (150)."""

import json

import numpy as np
import pytest
from test_loao_run import world  # noqa: F401  (module fixture)

from chemiproof import pipeline
from chemiproof.cli import EXIT_OK, main
from chemiproof.data.schema import EEMSpectrum
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.modeling import final
from chemiproof.modeling.baselines import make_base_estimator
from chemiproof.spectra.preprocess import preprocess_features
from chemiproof.uncertainty.scores import MahalanobisScorer
from helpers import dat_text


@pytest.fixture(scope="module")
def trained(world, tmp_path_factory):  # noqa: F811
    _, root, manifest = world
    ds = pipeline.load_dataset(manifest, root)
    X = preprocess_features(ds.spectra)
    s0 = ds.spectra[0]
    m = final.train_final(X, ds.y, ds.groups, s0.excitation_nm, s0.emission_nm)
    art = final.save_final(m, tmp_path_factory.mktemp("final") / "M6_final_test")
    return ds, X, m, art


def test_saved_arrays_reproduce_sklearn(trained):
    ds, X, m, art = trained
    loaded = final.load_final(art)
    ref = make_base_estimator("pls", m.card["n_components"]).fit(X, ds.y)
    np.testing.assert_allclose(loaded.predict(X), np.ravel(ref.predict(X)), atol=1e-10)
    scorer = MahalanobisScorer(final.OOD_COMPONENTS).fit(X)
    np.testing.assert_allclose(loaded.ood_score(X), scorer.score(X), rtol=1e-8)
    assert loaded.threshold == m.threshold and loaded.halfwidth == m.halfwidth
    assert (
        m.card["ood"]["n_calibration"] == 150 and m.card["interval"]["coverage_guarantee"] is False
    )


def test_tampered_or_missing_artifact_is_refused(trained, tmp_path):
    *_, art = trained
    with pytest.raises(ChemiProofError) as e:
        final.load_final(tmp_path)
    assert e.value.code is StatusCode.NO_TRAINED_MODEL  # T020
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "model.npz").write_bytes((art / "model.npz").read_bytes() + b"x")
    (bad / "model_card.json").write_text((art / "model_card.json").read_text())
    with pytest.raises(ChemiProofError) as e:
        final.load_final(bad)
    assert e.value.code is StatusCode.NO_TRAINED_MODEL


def test_screen_single_estimate_and_interval(trained):
    ds, _, m, _ = trained
    res = pipeline.screen_single(dat_text(ds.spectra[3]), "s.dat", m)
    assert res.status == "ESTIMATE" and res.olive_fraction is not None
    lo, hi = res.interval["pooled"]
    assert lo < res.olive_fraction < hi
    assert res.ood_score <= res.ood_threshold


def test_screen_single_withholds_far_spectrum(trained):
    ds, _, m, _ = trained
    s = ds.spectra[0]
    weird = EEMSpectrum("weird", s.excitation_nm, s.emission_nm, s.intensity[::-1, ::-1].copy())
    res = pipeline.screen_single(dat_text(weird), "w.dat", m)
    assert res.status == StatusCode.ABSTAIN_OOD_RISK.value
    assert res.olive_fraction is None and res.interval is None


@pytest.mark.parametrize(
    "mutate, code",
    [
        (lambda t: t.replace("Normalized by", "Scaled by"), StatusCode.BAD_FILE_FORMAT),
        (lambda t: "\n".join(t.splitlines()[:-5]) + "\n", StatusCode.INVALID_WAVELENGTH_GRID),
        (lambda t: t.replace("\t", "\tnan", 1), StatusCode.BAD_FILE_FORMAT),
        (lambda t: "é" + t, StatusCode.BAD_FILE_FORMAT),
    ],
)
def test_screen_single_refuses_invalid_files(trained, mutate, code):  # T019 logic
    ds, _, m, _ = trained
    with pytest.raises(ChemiProofError) as e:
        pipeline.screen_single(mutate(dat_text(ds.spectra[0])).encode("utf-8"), "x.dat", m)
    assert e.value.code is code


def test_screen_single_refuses_other_wavelength_grid(trained):
    ds, _, m, _ = trained
    s = ds.spectra[0]
    shifted = EEMSpectrum("g", s.excitation_nm + 1.0, s.emission_nm, s.intensity)
    with pytest.raises(ChemiProofError) as e:
        pipeline.screen_single(dat_text(shifted), "g.dat", m)
    assert e.value.code is StatusCode.INVALID_WAVELENGTH_GRID


def test_screen_batch_is_transductive_and_needs_a_batch(trained):
    ds, _, m, _ = trained
    one_adulterant = [(f"b{i}.dat", dat_text(ds.spectra[i]).encode()) for i in range(30)]
    res = pipeline.screen_batch(one_adulterant, ds, m)
    assert len(res.olive_fraction) == 30 and res.diagnostics["mode"] == "transductive_batch"
    assert res.diagnostics["converged"] and len(res.batch_sha256) == 64
    with pytest.raises(ChemiProofError) as e:
        pipeline.screen_batch(one_adulterant[:5], ds, m)
    assert e.value.code is StatusCode.TRANSDUCTIVE_BATCH_REQUIRED
    with pytest.raises(ChemiProofError) as e:
        pipeline.screen_batch(one_adulterant[:9] + one_adulterant[:1], ds, m)
    assert e.value.code is StatusCode.QC_REVIEW_REQUIRED  # duplicate file
    mixed = [(f"m{i}.dat", dat_text(ds.spectra[i]).encode()) for i in range(0, 150, 15)]
    with pytest.raises(ChemiProofError) as e:  # frozen solver budget: stops, never scores
        pipeline.screen_batch(mixed, ds, m)
    assert e.value.code is StatusCode.NUMERICAL_NONCONVERGENCE


def test_cli_train_final_writes_card_and_registry(world, tmp_path):  # noqa: F811
    _, root, manifest = world
    out = tmp_path / "res"
    argv = ["model", "train-final", "--data-dir", str(root), "--manifest", str(manifest)]
    assert main(argv + ["--output-root", str(out)]) == EXIT_OK
    (art,) = list(out.glob("M6_final_*"))
    card = json.loads((art / "model_card.json").read_text())
    assert card["protocol_id"] == "FINAL-PLS-v1" and card["n_train"] == 150
    assert "FINAL-PLS-v1" in (out / "experiment_registry.csv").read_text()
    assert final.latest_artifact(out) == art


def test_in_sample_upload_is_flagged(trained):
    ds, _, m, _ = trained
    text = dat_text(ds.spectra[7])
    import hashlib
    from dataclasses import replace

    marked = replace(
        m, card=m.card | {"train_file_sha256": [hashlib.sha256(text.encode()).hexdigest()]}
    )
    assert any(
        w.startswith("IN_SAMPLE") for w in pipeline.screen_single(text, "t.dat", marked).warnings
    )
    assert not any(
        w.startswith("IN_SAMPLE") for w in pipeline.screen_single(text, "t.dat", m).warnings
    )


def test_calibration_recomputed_independently_from_held_out_fits(trained):
    """Half-widths and threshold must come from fits that EXCLUDE the scored adulterant."""
    import math

    from sklearn.cross_decomposition import PLSRegression
    from sklearn.decomposition import PCA

    ds, X, m, _ = trained
    y, groups = ds.y, ds.groups
    res, scores, per_group = [], [], []
    for a in sorted(set(groups.tolist())):
        held, fit = groups == a, groups != a
        pls = PLSRegression(m.card["n_components"], scale=False).fit(X[fit], y[fit])
        r = np.abs(y[held] - np.ravel(pls.predict(X[held])))
        res.append(r)
        k = math.ceil((r.size + 1) * 0.9)
        per_group.append(np.sort(r)[k - 1])
        pca = PCA(10, random_state=20261024).fit(X[fit])
        z = pca.transform(X[held])
        scores.append(np.sqrt(np.sum(z**2 / pca.explained_variance_, axis=1)))
    pooled = np.sort(np.concatenate(res))
    expected_pooled = pooled[math.ceil((pooled.size + 1) * 0.9) - 1]
    assert m.halfwidth["pooled"] == pytest.approx(expected_pooled, abs=1e-12)
    assert m.halfwidth["max_domain"] == pytest.approx(max(per_group), abs=1e-12)
    expected_thr = np.quantile(np.concatenate(scores), 0.8, method="higher")
    assert m.threshold == pytest.approx(expected_thr, rel=1e-9)


def test_withheld_result_cannot_carry_an_estimate(trained):
    ds, _, m, _ = trained
    res = pipeline.screen_single(dat_text(ds.spectra[3]), "s.dat", m)
    from dataclasses import replace

    with pytest.raises(ValueError):
        replace(res, status=StatusCode.ABSTAIN_OOD_RISK.value)
    with pytest.raises(ValueError):
        replace(res, olive_fraction=None)


def test_out_of_range_output_is_warned_not_clipped(trained):
    from dataclasses import replace

    ds, _, m, _ = trained
    res = pipeline.screen_single(
        dat_text(ds.spectra[3]), "s.dat", replace(m, intercept=m.intercept + 5)
    )
    assert res.olive_fraction > 1 and any("outside [0, 1]" in w for w in res.warnings)


def test_batch_counts_in_sample_files(trained):
    import hashlib
    from dataclasses import replace

    ds, _, m, _ = trained
    files = [(f"b{i}.dat", dat_text(ds.spectra[i]).encode()) for i in range(30)]
    marked = replace(
        m,
        card=m.card | {"train_file_sha256": [hashlib.sha256(d).hexdigest() for _, d in files[:12]]},
    )
    assert pipeline.screen_batch(files, ds, marked).n_in_sample == 12


def test_latest_artifact_skips_incomplete_runs(trained, tmp_path):
    *_, art = trained
    good = tmp_path / "M6_final_20990101T000000Z_a_0"
    good.mkdir()
    for f in ("model.npz", "model_card.json"):
        (good / f).write_bytes((art / f).read_bytes())
    broken = tmp_path / "M6_final_20990102T000000Z_b_0"  # newer, interrupted: no card
    broken.mkdir()
    (broken / "model.npz").write_bytes((art / "model.npz").read_bytes())
    assert final.latest_artifact(tmp_path) == good


def test_exported_reports_keep_disclaimer_limitations_and_provenance(trained):
    from chemiproof.ui import artifacts as A

    ds, _, m, _ = trained
    card = m.card | {"run_id": "RUN123", "manifest_sha256": "MANI", "data_source_doi": "10.x/y"}
    est = pipeline.screen_single(dat_text(ds.spectra[3]), "s.dat", m)
    md = A.screening_report_md(est, card)
    assert "not a certified authenticity test" in md and "RUN123" in md and "MANI" in md
    assert est.file_sha256 in md and all(x in md for x in final.LIMITATIONS)
    assert "coverage on unseen adulterants is not guaranteed" in md
    s = ds.spectra[0]
    weird = EEMSpectrum("weird", s.excitation_nm, s.emission_nm, s.intensity[::-1, ::-1].copy())
    md_w = A.screening_report_md(pipeline.screen_single(dat_text(weird), "w.dat", m), card)
    assert "withheld" in md_w and "research interval" not in md_w
    meth = A.methods_report_md(card, [])
    assert "zenodo.19755088" in meth and "chemiproof model train-final" in meth and "RUN123" in meth
    assert "research model not available" in A.methods_report_md(None, [])
