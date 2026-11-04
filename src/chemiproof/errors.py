"""Standardized status codes and exceptions (docs/engineering/04_ARCHITECTURE.md taxonomy)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class StatusCode(StrEnum):
    BAD_FILE_FORMAT = "BAD_FILE_FORMAT"
    INVALID_WAVELENGTH_GRID = "INVALID_WAVELENGTH_GRID"
    NONFINITE_SPECTRUM = "NONFINITE_SPECTRUM"
    UNVERIFIED_LABEL = "UNVERIFIED_LABEL"
    NO_TRAINED_MODEL = "NO_TRAINED_MODEL"
    TRANSDUCTIVE_BATCH_REQUIRED = "TRANSDUCTIVE_BATCH_REQUIRED"
    QC_REVIEW_REQUIRED = "QC_REVIEW_REQUIRED"
    ABSTAIN_OOD_RISK = "ABSTAIN_OOD_RISK"
    INSUFFICIENT_CALIBRATION = "INSUFFICIENT_CALIBRATION"
    NUMERICAL_NONCONVERGENCE = "NUMERICAL_NONCONVERGENCE"
    LICENSE_REVIEW_PENDING = "LICENSE_REVIEW_PENDING"
    # Added in M0 (see decision log): the taxonomy had no code for these.
    DATASET_NOT_AVAILABLE = "DATASET_NOT_AVAILABLE"
    INVALID_CONFIG = "INVALID_CONFIG"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    # Added in M6.5 CP-652 (BI export): no code in the original taxonomy covered these.
    BI_EXPORT_EXISTS = "BI_EXPORT_EXISTS"
    BI_VALIDATION_FAILED = "BI_VALIDATION_FAILED"


DESCRIPTIONS: dict[StatusCode, str] = {
    StatusCode.BAD_FILE_FORMAT: "Input file does not match the supported format.",
    StatusCode.INVALID_WAVELENGTH_GRID: "Wavelength axes are missing, wrong size or not monotonic.",
    StatusCode.NONFINITE_SPECTRUM: "Spectrum contains NaN or Inf.",
    StatusCode.UNVERIFIED_LABEL: "Olive-fraction label mapping is not verified.",
    StatusCode.NO_TRAINED_MODEL: "No validated trained model artifact exists.",
    StatusCode.TRANSDUCTIVE_BATCH_REQUIRED: "Transductive OT needs a batch of unlabeled spectra.",
    StatusCode.QC_REVIEW_REQUIRED: "Input failed QC; human review required.",
    StatusCode.ABSTAIN_OOD_RISK: "Estimate withheld: research-level out-of-distribution risk cue.",
    StatusCode.INSUFFICIENT_CALIBRATION: "Not enough source data to calibrate an interval.",
    StatusCode.NUMERICAL_NONCONVERGENCE: "Numerical solver did not converge.",
    StatusCode.LICENSE_REVIEW_PENDING: "Data/code license review is not finished.",
    StatusCode.DATASET_NOT_AVAILABLE: "The required dataset archive or manifest is not present.",
    StatusCode.INVALID_CONFIG: "Configuration failed validation.",
    StatusCode.NOT_IMPLEMENTED: "This stage is not implemented in the current milestone.",
    StatusCode.BI_EXPORT_EXISTS: "The BI export output directory already has files in it.",
    StatusCode.BI_VALIDATION_FAILED: "The BI export failed its own contract validation rules.",
}


class ChemiProofError(Exception):
    """Error carrying a StatusCode and technical context (no secrets, no absolute user paths)."""

    def __init__(self, code: StatusCode, message: str, **context: Any) -> None:
        super().__init__(f"[{code.value}] {message}")
        self.code = code
        self.message = message
        self.context = context
