"""Pipeline stage entry points. M0: every stage fails honestly; nothing here fabricates results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chemiproof.errors import ChemiProofError, StatusCode


def load_dataset(manifest_path: Path) -> Any:
    """Load the audited manifest + arrays. Real loader arrives in M1."""
    if not manifest_path.is_file():
        raise ChemiProofError(
            StatusCode.DATASET_NOT_AVAILABLE,
            "sample manifest not found; run the dataset audit (M1) first",
            manifest=manifest_path.name,
        )
    raise ChemiProofError(StatusCode.NOT_IMPLEMENTED, "dataset loading is implemented in M1")


def make_outer_folds(manifest: Any) -> Any:
    raise ChemiProofError(StatusCode.NOT_IMPLEMENTED, "LOAO folds are implemented in M3")


def fit_baseline(*_: Any, **__: Any) -> Any:
    raise ChemiProofError(StatusCode.NOT_IMPLEMENTED, "baseline models are implemented in M2")


def screen_single(*_: Any, **__: Any) -> Any:
    raise ChemiProofError(
        StatusCode.NO_TRAINED_MODEL, "no validated trained model exists; no prediction is shown"
    )
