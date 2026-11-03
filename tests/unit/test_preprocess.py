"""T007: preprocessing a known synthetic EEM gives the documented, shape-stable result."""

import numpy as np
import pytest

from chemiproof.data.synthetic import make_synthetic_eem
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.spectra.preprocess import (
    AUTHOR_V1,
    N_FEATURES,
    PreprocessConfig,
    preprocess_features,
    preprocess_intensity,
)


def test_author_v1_properties_on_synthetic_eem():
    z = make_synthetic_eem(3).intensity - 2.0  # force some negative cells
    assert z.min() < 0
    out = preprocess_intensity(z)
    assert out.shape == (35, 270) and np.all(np.isfinite(out))
    assert out.max() == pytest.approx(1.0)  # divided by global max
    assert out.min() >= -0.05  # SG can undershoot slightly after min subtraction, never wildly
    assert np.abs(out).max() <= 1.0 + 1e-12


def test_input_not_mutated_and_deterministic():
    z = make_synthetic_eem(4).intensity
    before = z.copy()
    a, b = preprocess_intensity(z), preprocess_intensity(z)
    np.testing.assert_array_equal(z, before)
    np.testing.assert_array_equal(a, b)


def test_savgol_preserves_quadratic_along_emission_axis():
    cfg = PreprocessConfig(baseline="none", normalize="none")
    em = np.arange(270, dtype=float)
    z = np.tile(0.001 * em**2 + 0.5 * em + 3.0, (35, 1))
    out = preprocess_intensity(z, cfg)
    np.testing.assert_allclose(out, z, rtol=1e-9, atol=1e-6)  # polyorder 2 reproduces a quadratic


def test_smoothing_is_only_along_emission_axis():
    cfg = PreprocessConfig(baseline="none", normalize="none")
    z = np.zeros((35, 270))
    z[:, 100] = 1.0  # a vertical line in emission: constant across excitation rows
    out = preprocess_intensity(z, cfg)
    for i in range(1, 35):  # every excitation row identical -> nothing mixed across rows
        np.testing.assert_allclose(out[i], out[0])
    z2 = np.zeros((35, 270))
    z2[10, :] = 1.0  # a horizontal line: SG along emission leaves a constant row unchanged
    out2 = preprocess_intensity(z2, cfg)
    np.testing.assert_allclose(out2[10], 1.0)
    np.testing.assert_allclose(out2[9], 0.0, atol=1e-12)  # no leakage into neighbouring rows


def test_per_spectrum_independence_batch_equals_single():
    specs = [make_synthetic_eem(s) for s in (5, 6, 7)]
    batch = preprocess_features(specs)
    assert batch.shape == (3, N_FEATURES) == (3, 9450)
    for i, s in enumerate(specs):
        np.testing.assert_array_equal(batch[i], preprocess_features([s])[0])
        np.testing.assert_array_equal(batch[i], preprocess_intensity(s.intensity).reshape(-1))


def test_rejects_bad_inputs():
    with pytest.raises(ChemiProofError) as e:
        preprocess_intensity(np.ones((34, 270)))
    assert e.value.code is StatusCode.INVALID_WAVELENGTH_GRID
    bad = np.ones((35, 270))
    bad[0, 0] = np.nan
    with pytest.raises(ChemiProofError) as e:
        preprocess_intensity(bad)
    assert e.value.code is StatusCode.NONFINITE_SPECTRUM
    with pytest.raises(ChemiProofError) as e:  # constant spectrum -> max-normalization undefined
        preprocess_intensity(np.full((35, 270), 7.0))
    assert e.value.code is StatusCode.QC_REVIEW_REQUIRED


def test_config_is_documented_and_prespecified():
    assert AUTHOR_V1.version == "author_v1"
    steps = " ".join(AUTHOR_V1.describe())
    assert "subtract global minimum" in steps and "window=5, polyorder=2" in steps
    assert "['emission']" in steps and "9450" in steps
