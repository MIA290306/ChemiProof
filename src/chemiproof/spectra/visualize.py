"""EEM heatmaps from REAL parsed spectra (matplotlib, Agg backend, no display needed)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from chemiproof.data.manifest import ManifestRow  # noqa: E402
from chemiproof.data.parser import parse_dat  # noqa: E402
from chemiproof.data.schema import EEMSpectrum  # noqa: E402

UNIT = "Intensity [Counts/µA]"


def _draw(ax, fig, spec: EEMSpectrum, title: str) -> None:
    mesh = ax.pcolormesh(spec.emission_nm, spec.excitation_nm, spec.intensity, shading="auto")
    ax.set_xlabel("Emission wavelength [nm]")
    ax.set_ylabel("Excitation wavelength [nm]")
    ax.set_title(title, fontsize=7)
    fig.colorbar(mesh, ax=ax, label=UNIT)


def plot_sample(data_dir: Path, row: ManifestRow, out_png: Path) -> None:
    spec = parse_dat(data_dir / row.relative_path, row.sample_id).spectrum
    fig, ax = plt.subplots(figsize=(6, 4.5))
    _draw(ax, fig, spec, f"{row.sample_id}\nolive fraction = {row.olive_fraction:.4f} (a/11)")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_png, dpi=130)
    plt.close(fig)


def plot_gallery(
    data_dir: Path, rows: list[ManifestRow], out_png: Path, brand: str = "luhua"
) -> list[str]:
    """One high- and one low-olive EEM per adulterant (round 1, one brand); returns sample IDs."""
    adulterants = ["soybean", "peanut", "rapeseed", "corn", "walnut"]
    fig, axes = plt.subplots(2, len(adulterants), figsize=(4.2 * len(adulterants), 7.5))
    used: list[str] = []
    for j, ad in enumerate(adulterants):
        pool = [
            r
            for r in rows
            if r.adulterant_type == ad and r.evoo_brand == brand and r.measurement_round == 1
        ]
        for i, pick in enumerate((max, min)):
            row = pick(pool, key=lambda r: r.olive_fraction)
            spec = parse_dat(data_dir / row.relative_path, row.sample_id).spectrum
            _draw(axes[i][j], fig, spec, f"{row.sample_id}\nolive = {row.olive_fraction:.4f}")
            used.append(row.sample_id)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_png, dpi=110)
    plt.close(fig)
    return used
