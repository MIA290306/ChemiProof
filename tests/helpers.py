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


def mixture_eem(y: float, seed_a: int = 1, seed_b: int = 2, noise: float = 0.0, rng_seed: int = 0):
    """SYNTHETIC mixture EEM: y * A + (1 - y) * B (+ noise). Gives models a learnable signal."""
    import numpy as np

    from chemiproof.data.schema import EEMSpectrum
    from chemiproof.data.synthetic import make_synthetic_eem

    a, b = make_synthetic_eem(seed_a), make_synthetic_eem(seed_b)
    rng = np.random.default_rng(rng_seed)
    z = y * a.intensity + (1 - y) * b.intensity + noise * rng.standard_normal(a.intensity.shape)
    return EEMSpectrum(f"mix-{y:.3f}", a.excitation_nm, a.emission_nm, z, synthetic=True)


def fake_rows(rounds: list[int], ys: list[float]):
    """Minimal ManifestRow list (synthetic) for runner tests: one row per (round, y)."""
    from chemiproof.data.manifest import ManifestRow

    rows = []
    for rnd in rounds:
        for i, y in enumerate(ys):
            rows.append(
                ManifestRow(
                    sample_id=f"fake_R{rnd}_{i:02d}",
                    relative_path=f"fake/{rnd}/{i}.dat",
                    sha256=f"{rnd:02d}{i:02d}".ljust(64, "0"),
                    source_record_doi="synthetic",
                    adulterant_type="walnut",
                    evoo_brand="luhua",
                    olive_fraction=y,
                    olive_ratio_raw="x",
                    measurement_round=rnd,
                    replicate_id="",
                    excitation_channels=35,
                    emission_channels=270,
                    excitation_min_nm=300.0,
                    excitation_max_nm=640.0,
                    emission_min_nm=300.0,
                    emission_max_nm=800.0,
                    axis_sha256="0",
                    source_excitation_order="descending",
                    normalization_factor=1.0,
                    intensity_min=0.0,
                    intensity_max=1.0,
                    negative_cells=0,
                    qc_status="PASS",
                    qc_flags="",
                    parser_version="test",
                )
            )
    return rows


PUBLISHED_DESIGN = {  # adulterant -> EVOO brands, = docs/science/03_DATA_CONTRACT.md (330 samples)
    "soybean": ["luhua", "olivera"],
    "peanut": ["luhua", "olivera"],
    "rapeseed": ["earl_grey", "luhua", "olivera"],
    "corn": ["earl_grey", "luhua", "olivera"],
    "walnut": ["luhua"],
}


def fake_rows_multi(design=None, rounds=(1, 2, 3), n_levels=10):
    """Synthetic ManifestRow list with the published group x brand design (no spectra)."""
    from dataclasses import replace

    base = fake_rows([1], [0.5])[0]
    rows = []
    for ad, brands in (design or PUBLISHED_DESIGN).items():
        for brand in brands:
            for rnd in rounds:
                for a in range(1, n_levels + 1):
                    sid = f"{ad}_{brand}_R{rnd}_{a:02d}"
                    rows.append(
                        replace(
                            base,
                            sample_id=sid,
                            sha256=sid.encode().hex().ljust(64, "0")[:64],
                            adulterant_type=ad,
                            evoo_brand=brand,
                            measurement_round=rnd,
                            olive_fraction=a / 11,
                            olive_ratio_raw=f"{a}:{11 - a}",
                        )
                    )
    return rows
