"""Strict parser for the Zenodo 19755088 `.dat` EEM files (schema observed in M1, 2026-11-02).

Observed layout (ASCII, tab-separated), identical in all 330 files:

    Sample \\t <35 excitation wavelengths, nm>      # file order: 640 -> 300 (descending)
    nm
    Normalized by <factor>
    <emission nm> \\t <35 intensities>              # 270 rows, emission ascending

Policy (docs/science/03_DATA_CONTRACT.md): shape must be exactly 35 x 270, values are never
eval'd, and the descending excitation axis is reordered by ONE explicit, recorded rule.
Negative intensities are kept as-is (flagged by QC, never clamped).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from chemiproof.data.schema import N_EMISSION, N_EXCITATION, EEMSpectrum
from chemiproof.errors import ChemiProofError, StatusCode

PARSER_VERSION = "1.0.0"
MAX_DAT_BYTES = 5_000_000  # real files are ~58 kB; refuse anything absurd
_NUMBER = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_SPECIAL = {"nan", "inf", "+inf", "-inf"}  # parsed, then rejected as NONFINITE_SPECTRUM


@dataclass(frozen=True)
class ParsedDat:
    spectrum: EEMSpectrum  # canonical: shape (35, 270) = (excitation, emission), both ascending
    normalization_factor: float
    source_excitation_order: str  # "descending" | "ascending" (as found in the file)


def _fail(code: StatusCode, message: str, sample_id: str, **ctx: object) -> ChemiProofError:
    return ChemiProofError(code, message, sample_id=sample_id, **ctx)


def _number(token: str, sample_id: str, where: str) -> float:
    t = token.strip()
    if t.lower() in _SPECIAL:
        return float(t)
    if not _NUMBER.match(t):
        raise _fail(StatusCode.BAD_FILE_FORMAT, f"non-numeric token in {where}", sample_id)
    return float(t)


def _fields(line: str) -> list[str]:
    parts = line.rstrip("\r\n").split("\t")
    while parts and parts[-1].strip() == "":
        parts.pop()
    return parts


def parse_dat_text(text: str, sample_id: str) -> ParsedDat:
    lines = [ln for ln in text.splitlines()]
    if len(lines) < 4:
        raise _fail(StatusCode.BAD_FILE_FORMAT, "fewer than 4 lines", sample_id)
    head = _fields(lines[0])
    if not head or head[0].strip() != "Sample":
        raise _fail(StatusCode.BAD_FILE_FORMAT, "first line must start with 'Sample'", sample_id)
    if lines[1].strip() != "nm":
        raise _fail(StatusCode.BAD_FILE_FORMAT, "second line must be 'nm'", sample_id)
    m = re.match(r"^Normalized by\s+(\S+)\s*$", lines[2])
    if not m:
        raise _fail(StatusCode.BAD_FILE_FORMAT, "third line must be 'Normalized by <x>'", sample_id)
    norm = _number(m.group(1), sample_id, "normalization factor")

    ex = np.array([_number(t, sample_id, "excitation header") for t in head[1:]])
    if ex.size != N_EXCITATION:
        raise _fail(
            StatusCode.INVALID_WAVELENGTH_GRID,
            f"expected {N_EXCITATION} excitation wavelengths, found {ex.size}",
            sample_id,
        )
    body = [ln for ln in lines[3:] if ln.strip()]
    if len(body) != N_EMISSION:
        raise _fail(
            StatusCode.INVALID_WAVELENGTH_GRID,
            f"expected {N_EMISSION} emission rows, found {len(body)}",
            sample_id,
        )
    em = np.empty(N_EMISSION)
    z = np.empty((N_EMISSION, N_EXCITATION))
    for i, ln in enumerate(body):
        f = _fields(ln)
        if len(f) != N_EXCITATION + 1:
            raise _fail(
                StatusCode.INVALID_WAVELENGTH_GRID,
                f"row {i} has {len(f)} fields, expected {N_EXCITATION + 1}",
                sample_id,
            )
        vals = [_number(t, sample_id, f"row {i}") for t in f]
        em[i], z[i] = vals[0], vals[1:]

    intensity = z.T  # (excitation, emission)
    if np.all(np.diff(ex) < 0):
        order, ex, intensity = "descending", ex[::-1], intensity[::-1]  # the explicit rule
    elif np.all(np.diff(ex) > 0):
        order = "ascending"
    else:
        raise _fail(StatusCode.INVALID_WAVELENGTH_GRID, "excitation axis not monotonic", sample_id)
    spectrum = EEMSpectrum(sample_id, ex, em, np.ascontiguousarray(intensity))
    return ParsedDat(spectrum, norm, order)


def parse_dat_bytes(data: bytes, sample_id: str) -> ParsedDat:
    """Size + ASCII gate, then the strict text parser (used for files and UI uploads)."""
    if len(data) > MAX_DAT_BYTES:
        raise _fail(StatusCode.BAD_FILE_FORMAT, f"file too large ({len(data)} bytes)", sample_id)
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise _fail(StatusCode.BAD_FILE_FORMAT, "file is not ASCII text", sample_id) from exc
    return parse_dat_text(text, sample_id)


def parse_dat(path: Path, sample_id: str | None = None) -> ParsedDat:
    sid = sample_id or path.stem
    size = path.stat().st_size
    if size > MAX_DAT_BYTES:
        raise _fail(StatusCode.BAD_FILE_FORMAT, f"file too large ({size} bytes)", sid)
    return parse_dat_bytes(path.read_bytes(), sid)
