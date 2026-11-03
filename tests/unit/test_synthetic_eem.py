"""T001: valid synthetic 35x270 EEM + monotonic axes parses without mutation; finite intensity."""

import numpy as np
import pytest

from chemiproof.data.schema import N_EMISSION, N_EXCITATION, EEMSpectrum
from chemiproof.data.synthetic import make_synthetic_eem
from chemiproof.errors import ChemiProofError, StatusCode


def test_t001_shape_axes_finite_and_flagged_synthetic():
    s = make_synthetic_eem(seed=1)
    assert s.intensity.shape == (N_EXCITATION, N_EMISSION) == (35, 270)
    assert s.intensity.size == 9450
    assert np.all(np.diff(s.excitation_nm) > 0) and np.all(np.diff(s.emission_nm) > 0)
    assert np.all(np.isfinite(s.intensity))
    assert s.synthetic is True


def test_deterministic_per_seed_and_different_across_seeds():
    a, b, c = make_synthetic_eem(3), make_synthetic_eem(3), make_synthetic_eem(4)
    np.testing.assert_array_equal(a.intensity, b.intensity)
    assert not np.array_equal(a.intensity, c.intensity)


def test_input_arrays_not_mutated_and_result_readonly():
    s = make_synthetic_eem(2)
    ex, em, z = s.excitation_nm.copy(), s.emission_nm.copy(), s.intensity.copy()
    again = EEMSpectrum("x", ex, em, z)
    np.testing.assert_array_equal(z, s.intensity)  # caller's array untouched
    with pytest.raises(ValueError):
        again.intensity[0, 0] = 1.0  # read-only


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda ex, em, z: (ex[::-1], em, z), StatusCode.INVALID_WAVELENGTH_GRID),
        (
            lambda ex, em, z: (np.where(ex == ex[5], ex[4], ex), em, z),
            StatusCode.INVALID_WAVELENGTH_GRID,
        ),
        (lambda ex, em, z: (ex, em, z[:, :-1]), StatusCode.INVALID_WAVELENGTH_GRID),
        (lambda ex, em, z: (ex, np.append(em[:-1], np.nan), z), StatusCode.INVALID_WAVELENGTH_GRID),
        (
            lambda ex, em, z: (
                ex,
                em,
                np.where(np.arange(z.size).reshape(z.shape) == 7, np.nan, z),
            ),
            StatusCode.NONFINITE_SPECTRUM,
        ),
    ],
)
def test_invalid_inputs_rejected_with_sample_id(mutate, code):
    s = make_synthetic_eem(5, sample_id="bad-1")
    ex, em, z = mutate(s.excitation_nm.copy(), s.emission_nm.copy(), s.intensity.copy())
    with pytest.raises(ChemiProofError) as err:
        EEMSpectrum("bad-1", ex, em, z)
    assert err.value.code is code
    assert err.value.context["sample_id"] == "bad-1"
