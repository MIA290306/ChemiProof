"""Pipeline stage entry points. Stages fail honestly; nothing here fabricates results."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from chemiproof.data.manifest import ManifestRow, read_manifest_csv
from chemiproof.data.parser import parse_dat, parse_dat_bytes
from chemiproof.data.schema import EEMSpectrum
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.modeling.final import FinalModel
from chemiproof.modeling.ot import ot_svr_fit_predict
from chemiproof.provenance import file_sha256
from chemiproof.spectra.preprocess import preprocess_intensity


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


@dataclass(frozen=True)
class ScreeningResult:
    """One inductive research estimate (or a withheld one). Fractions in [0, 1] units."""

    sample_id: str
    file_sha256: str
    status: str  # "ESTIMATE" | "ABSTAIN_OOD_RISK"
    olive_fraction: float | None  # None when withheld; unclipped model output otherwise
    interval: dict[str, tuple[float, float]] | None  # variant -> (lo, hi), unclipped
    ood_score: float
    ood_threshold: float
    spectrum: EEMSpectrum
    warnings: list[str] = field(default_factory=list)


def _validated_spectrum(data: bytes, name: str, model: FinalModel) -> EEMSpectrum:
    spec = parse_dat_bytes(data, name).spectrum
    if not (
        np.array_equal(spec.excitation_nm, model.excitation_nm)
        and np.array_equal(spec.emission_nm, model.emission_nm)
    ):
        raise ChemiProofError(
            StatusCode.INVALID_WAVELENGTH_GRID,
            "wavelength grid differs from the training grid; no interpolation is done",
            sample_id=name,
        )
    return spec


def screen_single(
    data: bytes | str, name: str = "upload.dat", model: FinalModel | None = None,
    mode: str = "inductive",
) -> ScreeningResult:  # fmt: skip
    """QC -> FINAL-PLS-v1 -> estimate or ABSTAIN. OT adaptation is a batch method: refused here."""
    if mode != "inductive":
        raise ChemiProofError(
            StatusCode.TRANSDUCTIVE_BATCH_REQUIRED,
            "transductive OT needs a batch of unlabeled spectra; it cannot score a single file",
        )
    if model is None:
        raise ChemiProofError(
            StatusCode.NO_TRAINED_MODEL, "no validated trained model exists; no prediction is shown"
        )
    raw = data.encode() if isinstance(data, str) else data
    spec = _validated_spectrum(raw, name, model)
    sha = hashlib.sha256(raw).hexdigest()
    x = preprocess_intensity(spec.intensity).reshape(1, -1)
    y_hat = float(model.predict(x)[0])
    score = float(model.ood_score(x)[0])
    warnings = []
    if sha in set(model.card.get("train_file_sha256", [])):
        warnings.append(
            "IN_SAMPLE: this file is one of the training spectra, so the estimate is in-sample "
            "and is not a test of the model"
        )
    if spec.intensity.min() < 0:
        warnings.append("NEGATIVE_INTENSITY: raw spectrum has negative cells (kept, not clamped)")
    if score > model.threshold:
        return ScreeningResult(
            name, sha, StatusCode.ABSTAIN_OOD_RISK.value, None, None,
            score, model.threshold, spec, warnings,
        )  # fmt: skip
    if not 0.0 <= y_hat <= 1.0:
        warnings.append("model output lies outside [0, 1]; shown unclipped")
    interval = {k: (y_hat - q, y_hat + q) for k, q in model.halfwidth.items()}
    return ScreeningResult(
        name, sha, "ESTIMATE", y_hat, interval, score,
        model.threshold, spec, warnings,
    )  # fmt: skip


@dataclass(frozen=True)
class BatchResult:
    batch_sha256: str  # hash of the sorted per-file hashes: the batch identity
    sample_ids: list[str]
    olive_fraction: np.ndarray  # unclipped, transductive
    diagnostics: dict[str, Any]


def screen_batch(files: list[tuple[str, bytes]], source: Dataset, model: FinalModel) -> BatchResult:
    """TRANSDUCTIVE research mode (ADR-018): OT+SVR adapts all 330 source spectra to this batch.

    Uses the unlabeled batch FEATURES only; there is no label input. Never evaluated in this exact
    configuration; label-skewed batches are known to fail (ADR-015).
    """
    specs = [_validated_spectrum(data, name, model) for name, data in files]
    hashes = sorted(hashlib.sha256(d).hexdigest() for _, d in files)
    if len(set(hashes)) != len(hashes):
        raise ChemiProofError(StatusCode.QC_REVIEW_REQUIRED, "batch contains duplicate files")
    xt = np.stack([preprocess_intensity(s.intensity).reshape(-1) for s in specs])
    xs = np.stack([preprocess_intensity(s.intensity).reshape(-1) for s in source.spectra])
    pred = ot_svr_fit_predict(
        xs, source.y, xt
    )  # raises TRANSDUCTIVE_BATCH_REQUIRED / NONCONVERGENCE
    batch_id = hashlib.sha256("".join(hashes).encode()).hexdigest()
    return BatchResult(batch_id, [n for n, _ in files], pred.y_pred, pred.diagnostics)
