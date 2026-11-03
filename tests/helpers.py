"""Test helpers: write SYNTHETIC .dat files in the observed Zenodo layout."""

from __future__ import annotations

from pathlib import Path

from chemiproof.data.schema import EEMSpectrum


def dat_text(spec: EEMSpectrum, norm: str = "1.00", descending: bool = True) -> str:
    ex = spec.excitation_nm[::-1] if descending else spec.excitation_nm
    z = spec.intensity[::-1] if descending else spec.intensity  # (ex, em)
    lines = ["Sample\t" + "\t".join(f"{x:g}" for x in ex) + "\t", "nm", f"Normalized by {norm}"]
    for j, e in enumerate(spec.emission_nm):
        lines.append(f"{e:.6f}\t" + "\t".join(f"{v:.6f}" for v in z[:, j]) + "\t")
    return "\n".join(lines) + "\n"


def write_dat(path: Path, spec: EEMSpectrum, **kw) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dat_text(spec, **kw), encoding="ascii")
    return path
