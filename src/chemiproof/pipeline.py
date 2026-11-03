"""Pipeline stage entry points. M0: every stage fails honestly; nothing here fabricates results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from chemiproof.data.manifest import ManifestRow, read_manifest_csv
from chemiproof.data.parser import parse_dat
from chemiproof.data.schema import EEMSpectrum
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.provenance import file_sha256


@dataclass
class Dataset:
    rows: list[ManifestRow]
    spectra: list[EEMSpectrum]  # same order as rows; canonical (35, 270), both axes ascending

    @property
    def y(self) -> np.ndarray:
        """Olive-oil volume fraction (unit: fraction in [0, 1]); convention in ADR-008."""
        return np.array([r.olive_fraction for r in self.rows])

    @property
    def groups(self) -> np.ndarray:
        return np.array([r.adulterant_type for r in self.rows])

    def features(self) -> np.ndarray:
        """Flattened raw EEMs, shape (n_samples, 9450); no preprocessing applied."""
        return np.stack([s.intensity.reshape(-1) for s in self.spectra])


def load_dataset(manifest_path: Path, data_dir: Path | None = None) -> Dataset:
    """Load manifest + arrays, re-checking every file's SHA-256 against the manifest."""
    rows = read_manifest_csv(manifest_path)  # raises DATASET_NOT_AVAILABLE if missing
    root = data_dir or Path(load_project_data_dir())
    if not root.is_dir():
        raise ChemiProofError(
            StatusCode.DATASET_NOT_AVAILABLE, "data directory not found", data_dir=root.name
        )
    spectra = []
    for r in rows:
        path = root / r.relative_path
        if not path.is_file() or file_sha256(path) != r.sha256:
            raise ChemiProofError(
                StatusCode.BAD_FILE_FORMAT,
                "file missing or changed since the manifest was built",
                sample_id=r.sample_id,
            )
        spectra.append(parse_dat(path, r.sample_id).spectrum)
    return Dataset(rows, spectra)


def load_project_data_dir() -> str:
    return "data/raw/extracted"


def make_outer_folds(manifest: Any) -> Any:
    raise ChemiProofError(StatusCode.NOT_IMPLEMENTED, "LOAO folds are implemented in M3")


def fit_baseline(*_: Any, **__: Any) -> Any:
    raise ChemiProofError(StatusCode.NOT_IMPLEMENTED, "baseline models are implemented in M2")


def screen_single(*_: Any, **__: Any) -> Any:
    raise ChemiProofError(
        StatusCode.NO_TRAINED_MODEL, "no validated trained model exists; no prediction is shown"
    )
