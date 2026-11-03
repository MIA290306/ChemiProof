"""Rerun equality check (M7, CP-701 / T021): compare a rerun folder with a reference run folder.

Every CSV table of the reference run must exist in the rerun with the same columns and rows.
Numeric cells must agree within an absolute tolerance (in the cell's own unit, mostly fraction);
other cells must be identical. `run_id` differs between runs by construction and is ignored.
Figures (PNG) and free-text reports are not compared: they are derived from these tables.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

from chemiproof.errors import ChemiProofError, StatusCode

IGNORED_COLUMNS = frozenset({"run_id"})
EXACT_TEXT_FILES = ("dataset_manifest_sha256.txt",)
DEFAULT_ATOL = 1e-9  # fraction; 1e-7 percentage points. Observed reruns differ by <= 3e-14.


@dataclass
class FileComparison:
    name: str
    rows: int = 0
    max_abs_diff: float = 0.0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def _as_float(text: str | None) -> float | None:
    try:
        return float(text)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # None = cell missing from a short row
        return None


def _compare_csv(ref: Path, new: Path, atol: float) -> FileComparison:
    out = FileComparison(ref.name)
    ref_cols, ref_rows = _read_csv(ref)
    new_cols, new_rows = _read_csv(new)
    if ref_cols != new_cols:
        out.problems.append(f"columns differ: {ref_cols} vs {new_cols}")
        return out
    if len(ref_rows) != len(new_rows):
        out.problems.append(f"row count {len(ref_rows)} vs {len(new_rows)}")
        return out
    out.rows = len(ref_rows)
    cols = [c for c in ref_cols if c not in IGNORED_COLUMNS]
    for i, (a, b) in enumerate(zip(ref_rows, new_rows, strict=True), start=2):
        for col in cols:
            x, y = a[col], b[col]
            if x == y:
                continue
            fx, fy = _as_float(x), _as_float(y)
            if fx is None or fy is None:
                out.problems.append(f"line {i} {col}: {x!r} vs {y!r}")
            elif math.isnan(fx) or math.isnan(fy):
                if not (math.isnan(fx) and math.isnan(fy)):
                    out.problems.append(f"line {i} {col}: {x} vs {y}")
            else:
                d = abs(fx - fy)
                out.max_abs_diff = max(out.max_abs_diff, d)
                if d > atol:
                    out.problems.append(f"line {i} {col}: {x} vs {y} (|diff| {d:.3g} > {atol:g})")
        if len(out.problems) >= 20:
            out.problems.append("... further differences not listed")
            break
    return out


def compare_run_dirs(
    reference: Path, rerun: Path, atol: float = DEFAULT_ATOL
) -> list[FileComparison]:
    """Compare every CSV (and the manifest hash) of `reference` with the same file in `rerun`."""
    for d in (reference, rerun):
        if not d.is_dir():
            raise ChemiProofError(StatusCode.BAD_FILE_FORMAT, "not a run folder", path=d.name)
    names = sorted(p.name for p in reference.glob("*.csv"))
    names += [n for n in EXACT_TEXT_FILES if (reference / n).is_file()]
    if not names:
        raise ChemiProofError(
            StatusCode.BAD_FILE_FORMAT, "reference folder has no tables", path=reference.name
        )
    results = []
    for name in names:
        new = rerun / name
        if not new.is_file():
            results.append(FileComparison(name, problems=["missing in rerun"]))
        elif name.endswith(".csv"):
            results.append(_compare_csv(reference / name, new, atol))
        else:
            same = (reference / name).read_bytes().strip() == new.read_bytes().strip()
            results.append(FileComparison(name, problems=[] if same else ["content differs"]))
    return results
