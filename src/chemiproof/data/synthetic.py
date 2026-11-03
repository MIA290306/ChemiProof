"""Deterministic SYNTHETIC EEM generator for tests only.

Gaussian blobs on made-up wavelength axes. It carries no chemical meaning and must never be
presented as real data, fitted for performance claims, or mixed with real samples.
"""

from __future__ import annotations

import numpy as np

from chemiproof.data.schema import N_EMISSION, N_EXCITATION, EEMSpectrum

# Axis ranges echo config/project.yaml (reported in the paper, unverified until M1).
SYNTHETIC_EXCITATION_NM = (300.0, 640.0)
SYNTHETIC_EMISSION_NM = (300.0, 800.0)


def make_synthetic_eem(seed: int = 0, sample_id: str | None = None) -> EEMSpectrum:
    rng = np.random.default_rng(seed)
    ex = np.linspace(*SYNTHETIC_EXCITATION_NM, N_EXCITATION)
    em = np.linspace(*SYNTHETIC_EMISSION_NM, N_EMISSION)
    ex_grid, em_grid = np.meshgrid(ex, em, indexing="ij")
    intensity = np.zeros_like(ex_grid)
    for _ in range(3):
        cx, cy = rng.uniform(320, 600), rng.uniform(350, 750)
        sx, sy = rng.uniform(15, 40), rng.uniform(20, 60)
        amp = rng.uniform(100, 1000)
        intensity += amp * np.exp(
            -((ex_grid - cx) ** 2 / (2 * sx**2) + (em_grid - cy) ** 2 / (2 * sy**2))
        )
    intensity += rng.uniform(0, 5, size=intensity.shape)  # strictly positive noise floor
    return EEMSpectrum(
        sample_id=sample_id or f"synthetic-{seed:04d}",
        excitation_nm=ex,
        emission_nm=em,
        intensity=intensity,
        synthetic=True,
    )
