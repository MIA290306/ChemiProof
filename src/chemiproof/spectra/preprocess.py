"""Deterministic, per-spectrum EEM preprocessing. Nothing here is fitted on a dataset.

`author_v1` is prespecified from the published code (ADR-011), not tuned on any labels:
subtract the EEM's global minimum -> Savitzky-Golay along the emission axis -> divide by the
EEM's global maximum -> flatten (35 x 270 = 9,450 features). Every step uses only the one
spectrum it is applied to, so it cannot leak information between samples or between train/test.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from scipy.signal import savgol_filter

from chemiproof.data.schema import N_EMISSION, N_EXCITATION, EEMSpectrum
from chemiproof.errors import ChemiProofError, StatusCode

N_FEATURES = N_EXCITATION * N_EMISSION  # 9450

Axis = Literal["emission", "excitation"]


@dataclass(frozen=True)
class PreprocessConfig:
    version: str = "author_v1"
    baseline: Literal["subtract_min", "none"] = "subtract_min"
    sg_window: int = 5
    sg_polyorder: int = 2
    smooth_axes: tuple[Axis, ...] = ("emission",)
    normalize: Literal["max", "none"] = "max"

    def describe(self) -> list[str]:
        steps = []
        if self.baseline == "subtract_min":
            steps.append(
                "baseline: subtract global minimum of the EEM (never clamps negatives away)"
            )
        if self.smooth_axes:
            steps.append(
                f"savitzky_golay(window={self.sg_window}, polyorder={self.sg_polyorder}) "
                f"along {list(self.smooth_axes)}"
            )
        if self.normalize == "max":
            steps.append("normalize: divide by global maximum of the EEM")
        steps.append(f"flatten (excitation, emission) C-order -> {N_FEATURES} features")
        return steps

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


AUTHOR_V1 = PreprocessConfig()


def preprocess_intensity(intensity: np.ndarray, cfg: PreprocessConfig = AUTHOR_V1) -> np.ndarray:
    """(35, 270) intensity -> processed (35, 270); returns a new array, input untouched."""
    if intensity.shape != (N_EXCITATION, N_EMISSION):
        raise ChemiProofError(
            StatusCode.INVALID_WAVELENGTH_GRID,
            f"expected {(N_EXCITATION, N_EMISSION)}, got {intensity.shape}",
        )
    x = np.array(intensity, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(x)):
        raise ChemiProofError(StatusCode.NONFINITE_SPECTRUM, "non-finite intensity")
    if cfg.baseline == "subtract_min":
        x = x - x.min()
    for axis_name in cfg.smooth_axes:
        axis = 1 if axis_name == "emission" else 0
        if cfg.sg_window >= x.shape[axis]:
            raise ChemiProofError(StatusCode.INVALID_CONFIG, "sg_window larger than the axis")
        x = savgol_filter(x, cfg.sg_window, cfg.sg_polyorder, axis=axis)
    if cfg.normalize == "max":
        top = x.max()
        if not top > 0:
            raise ChemiProofError(
                StatusCode.QC_REVIEW_REQUIRED, "constant or empty spectrum cannot be normalized"
            )
        x = x / top
    return x


def preprocess_features(
    spectra: list[EEMSpectrum], cfg: PreprocessConfig = AUTHOR_V1
) -> np.ndarray:
    """Flattened features, shape (n_samples, 9450)."""
    return np.stack([preprocess_intensity(s.intensity, cfg).reshape(-1) for s in spectra])
