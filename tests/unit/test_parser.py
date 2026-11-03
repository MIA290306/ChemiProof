import numpy as np
import pytest

from chemiproof.data.parser import MAX_DAT_BYTES, parse_dat, parse_dat_text
from chemiproof.data.synthetic import make_synthetic_eem
from chemiproof.errors import ChemiProofError, StatusCode
from helpers import dat_text, write_dat


def _code(text: str) -> StatusCode:
    with pytest.raises(ChemiProofError) as e:
        parse_dat_text(text, "s")
    return e.value.code


def test_descending_file_becomes_canonical_ascending_without_losing_pairing(tmp_path):
    src = make_synthetic_eem(7)
    p = write_dat(tmp_path / "0_RM.dat", src, descending=True)
    parsed = parse_dat(p, "s")
    assert parsed.source_excitation_order == "descending"
    assert parsed.normalization_factor == 1.0
    out = parsed.spectrum
    assert out.intensity.shape == (35, 270)
    assert np.all(np.diff(out.excitation_nm) > 0) and np.all(np.diff(out.emission_nm) > 0)
    np.testing.assert_allclose(out.excitation_nm, src.excitation_nm, atol=1e-5)
    # a given (excitation, emission) cell keeps its value: orientation not scrambled
    np.testing.assert_allclose(out.intensity, src.intensity, atol=1e-5)


def test_ascending_file_accepted_and_recorded():
    src = make_synthetic_eem(8)
    parsed = parse_dat_text(dat_text(src, descending=False), "s")
    assert parsed.source_excitation_order == "ascending"
    np.testing.assert_allclose(parsed.spectrum.intensity, src.intensity, atol=1e-5)


def test_negative_intensity_is_kept_not_clamped():
    src = make_synthetic_eem(9)
    text = dat_text(src).replace("\t", "\t-1.5\t", 0)
    lines = dat_text(src).split("\n")
    lines[10] = lines[10].split("\t")[0] + "\t-3.25" + "\t" + "\t".join(lines[10].split("\t")[2:])
    parsed = parse_dat_text("\n".join(lines), "s")
    assert parsed.spectrum.intensity.min() == pytest.approx(-3.25)
    assert text  # silence unused


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda t: t.replace("Sample", "Probe", 1), StatusCode.BAD_FILE_FORMAT),
        (lambda t: t.replace("\nnm\n", "\nmm\n", 1), StatusCode.BAD_FILE_FORMAT),
        (lambda t: t.replace("Normalized by", "Scaled by", 1), StatusCode.BAD_FILE_FORMAT),
        (lambda t: "\n".join(t.split("\n")[:-3]) + "\n", StatusCode.INVALID_WAVELENGTH_GRID),
        (
            lambda t: t.split("\n")[0].rsplit("\t", 2)[0] + "\n" + "\n".join(t.split("\n")[1:]),
            StatusCode.INVALID_WAVELENGTH_GRID,
        ),
        (lambda t: t.replace("\t", "\tabc\t", 1), StatusCode.BAD_FILE_FORMAT),
        (lambda t: t.replace("\t", "\t1_0\t", 1), StatusCode.BAD_FILE_FORMAT),
        (lambda t: "x\n", StatusCode.BAD_FILE_FORMAT),
    ],
)
def test_malformed_files_rejected_with_specific_codes(mutate, code):
    assert _code(mutate(dat_text(make_synthetic_eem(1)))) is code


def test_nan_and_nonmonotonic_axis_rejected():
    lines = dat_text(make_synthetic_eem(2)).split("\n")
    f = lines[5].split("\t")
    f[3] = "nan"
    lines[5] = "\t".join(f)
    assert _code("\n".join(lines)) is StatusCode.NONFINITE_SPECTRUM
    lines = dat_text(make_synthetic_eem(2)).split("\n")
    head = lines[0].split("\t")
    head[3], head[4] = head[4], head[3]
    lines[0] = "\t".join(head)
    assert _code("\n".join(lines)) is StatusCode.INVALID_WAVELENGTH_GRID


def test_non_ascii_and_oversized_files_rejected(tmp_path):
    bad = tmp_path / "x.dat"
    bad.write_bytes("Sample\t\u00e9".encode())
    with pytest.raises(ChemiProofError) as e:
        parse_dat(bad)
    assert e.value.code is StatusCode.BAD_FILE_FORMAT
    big = tmp_path / "big.dat"
    big.write_bytes(b"a" * (MAX_DAT_BYTES + 1))
    with pytest.raises(ChemiProofError):
        parse_dat(big)
