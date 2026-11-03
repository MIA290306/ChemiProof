"""In-memory EEM record contract. The real .dat layout is NOT known until M1."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from chemiproof.errors import ChemiProofError, StatusCode

N_EXCITATION = 35  # from the publication; verify against real files in M1
N_EMISSION = 270


@dataclass(frozen=True)
class EEMSpectrum:
    """One EEM. Arrays are copied and made read-only, so downstream code cannot mutate them.

    intensity has shape (len(excitation_nm), len(emission_nm)); units are instrument counts
    (arbitrary) unless a source says otherwise. `synthetic=True` marks generated test data.
    """

    sample_id: str
    excitation_nm: np.ndarray
    emission_nm: np.ndarray
    intensity: np.ndarray
    synthetic: bool = False

    def __post_init__(self) -> None:
        for name in ("excitation_nm", "emission_nm", "intensity"):
            arr = np.array(getattr(self, name), dtype=np.float64, copy=True)
            arr.setflags(write=False)
            object.__setattr__(self, name, arr)
        self.validate()

    def validate(self) -> None:
        for name, axis in (
            ("excitation_nm", self.excitation_nm),
            ("emission_nm", self.emission_nm),
        ):
            if axis.ndim != 1 or axis.size < 2 or not np.all(np.isfinite(axis)):
                raise ChemiProofError(
                    StatusCode.INVALID_WAVELENGTH_GRID,
                    f"{name} must be a finite 1-D axis",
                    sample_id=self.sample_id,
                )
            if not np.all(np.diff(axis) > 0):
                raise ChemiProofError(
                    StatusCode.INVALID_WAVELENGTH_GRID,
                    f"{name} must be strictly increasing",
                    sample_id=self.sample_id,
                )
        expected = (self.excitation_nm.size, self.emission_nm.size)
        if self.intensity.shape != expected:
            raise ChemiProofError(
                StatusCode.INVALID_WAVELENGTH_GRID,
                f"intensity shape {self.intensity.shape} does not match axes {expected}",
                sample_id=self.sample_id,
            )
        if not np.all(np.isfinite(self.intensity)):
            raise ChemiProofError(
                StatusCode.NONFINITE_SPECTRUM,
                "intensity contains NaN or Inf",
                sample_id=self.sample_id,
            )
