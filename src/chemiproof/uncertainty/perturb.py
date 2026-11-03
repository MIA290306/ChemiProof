"""Seeded spectral perturbations applied to RAW intensities (ADR-017 grid; fixed before running)."""

from __future__ import annotations

import numpy as np


def add_noise(
    intensity: np.ndarray, fraction_of_max: float, rng: np.random.Generator
) -> np.ndarray:
    return intensity + rng.normal(0.0, fraction_of_max * float(intensity.max()), intensity.shape)


def add_offset(intensity: np.ndarray, fraction_of_max: float) -> np.ndarray:
    return intensity + fraction_of_max * float(intensity.max())


def scale(intensity: np.ndarray, factor: float) -> np.ndarray:
    return intensity * factor
