"""Read-only helpers for the M6 explorer. No Streamlit import, so they are unit-testable.

The explorer shows only artifacts that exist on disk and copies every number from them; it never
fits, tunes or re-scores anything of record (CLAUDE.md invariant 11).
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chemiproof.errors import DESCRIPTIONS, ChemiProofError, StatusCode

BENCHMARK_PROTOCOLS = ("loao", "LOAO-UQ-v1")
MODE_LABEL = {
    "inductive": "Inductive (no target batch)",
    "inductive_single": "Inductive (no target batch)",
    "transductive_batch": "Transductive (unlabeled target batch used)",
}
_BAD_FILE = "Spectrum format or wavelength grid could not be validated; no estimate generated."
MESSAGES = {  # docs/product/08_UX_SPEC.md "Empty/error states"
    StatusCode.BAD_FILE_FORMAT: _BAD_FILE,
    StatusCode.INVALID_WAVELENGTH_GRID: _BAD_FILE,
    StatusCode.NONFINITE_SPECTRUM: _BAD_FILE,
    StatusCode.NO_TRAINED_MODEL: (
        "Research model not available: complete the model-validation milestones first."
    ),
    StatusCode.ABSTAIN_OOD_RISK: (
        "Review required: input differs from reference research spectra. "
        "This is a statistical flag, not a diagnosis."
    ),
    StatusCode.INSUFFICIENT_CALIBRATION: (
        "Prediction interval unavailable: evidence is insufficient."
    ),
    StatusCode.NUMERICAL_NONCONVERGENCE: (
        "Batch analysis stopped: optimal transport did not converge."
    ),
    StatusCode.TRANSDUCTIVE_BATCH_REQUIRED: (
        "Batch research mode needs a batch of unlabeled spectra; a single file is never scored "
        "transductively."
    ),
    StatusCode.QC_REVIEW_REQUIRED: "Input failed QC; human review required. No estimate generated.",
    StatusCode.DATASET_NOT_AVAILABLE: (
        "The audited dataset is not present on this machine; see docs/engineering/11_DEV_SETUP.md."
    ),
}
_BRAND = re.compile(r"^[a-z]+_(earl_grey|[a-z]+)_R\d")


def results_dir() -> Path:
    return Path(os.environ.get("CHEMIPROOF_RESULTS_DIR", "results"))


def data_dir() -> Path:
    return Path(os.environ.get("CHEMIPROOF_DATA_DIR", "data/raw/extracted"))


def manifest_path() -> Path:
    return Path(os.environ.get("CHEMIPROOF_MANIFEST", "data/interim/sample_manifest.csv"))


def user_message(err: ChemiProofError) -> str:
    return f"{MESSAGES.get(err.code, DESCRIPTIONS[err.code])} [{err.code.value}]"


def brand_of(sample_id: str) -> str:
    m = _BRAND.match(sample_id)
    return m.group(1) if m else "unknown"


@dataclass(frozen=True)
class Run:
    run_id: str
    path: Path
    experiment_id: str
    protocol: str
    subset_brand: str
    utc_time: str

    @property
    def label(self) -> str:
        subset = f", {self.subset_brand} only" if self.subset_brand else ", all brands"
        return f"{self.experiment_id}{subset} ({self.run_id})"


def benchmark_runs(root: Path) -> list[Run]:
    """Locked benchmark runs present on disk; reruns with an identical config hash are hidden."""
    reg = root / "experiment_registry.csv"
    if not reg.is_file():
        return []
    seen: set[str] = set()
    out = []
    with reg.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            path = root / r["output_dir"]
            if (
                r["run_class"] != "locked"
                or r["protocol"] not in BENCHMARK_PROTOCOLS
                or r["config_sha256"] in seen
                or not (path / "summary.json").is_file()
            ):
                continue
            seen.add(r["config_sha256"])
            out.append(
                Run(r["run_id"], path, r["experiment_id"], r["protocol"],
                    r["subset_brand"], r["utc_time"])
            )  # fmt: skip
    return out


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def model_modes(run: Run) -> dict[str, str]:
    """model -> mode, as recorded per row in metrics_by_fold.csv."""
    with (run.path / "metrics_by_fold.csv").open(encoding="utf-8", newline="") as fh:
        return {r["model"]: r["mode"] for r in csv.DictReader(fh)}


def headline_rows(runs: list[Run]) -> list[dict[str, Any]]:
    """Macro metrics copied from each run's summary.json (LOAO-v1 / LOAO-OT-v1 runs only)."""
    rows = []
    for run in runs:
        summary = read_json(run.path / "summary.json")
        if run.protocol != "loao":
            continue
        modes = model_modes(run)
        for model, m in summary["models"].items():
            macro = m["macro_over_folds"]
            rows.append({
                "run": run.label,
                "model": model,
                "mode": MODE_LABEL.get(modes.get(model, ""), modes.get(model, "")),
                "macro MAE (pp)": round(100 * macro["mae_fraction"], 2),
                "worst-fold MAE (pp)": round(100 * macro["worst_fold_mae_fraction"], 2),
                "macro R2": round(macro["r2"], 3),
                "run_id": run.run_id,
            })  # fmt: skip
    return rows


def published_reference(runs: list[Run]) -> dict[str, Any] | None:
    for run in runs:
        ref = read_json(run.path / "summary.json").get("published_reference_not_measured")
        if ref:
            return ref
    return None


def _fmt(x: float | None) -> str:
    return "withheld" if x is None else f"{x:.3f} fraction ({100 * x:.1f} %)"


def screening_report_md(res: Any, card: dict[str, Any]) -> str:
    """Markdown export of one screening result with its provenance and limitations."""
    lines = [
        "# ChemiProof research screening report",
        "",
        "Research screening only; not a certified authenticity test; no regulatory meaning.",
        "",
        f"- File: `{res.sample_id}` (SHA-256 `{res.file_sha256}`)",
        f"- Status: **{res.status}**",
        f"- Estimated olive-oil volume fraction: {_fmt(res.olive_fraction)}",
    ]
    if res.interval:
        lo, hi = res.interval["pooled"]
        lines.append(
            f"- Empirical research interval (nominal 0.90, pooled): [{lo:.3f}, {hi:.3f}] fraction; "
            "coverage on unseen adulterants is not guaranteed."
        )
    lines += [
        f"- OOD score (ood_maha): {res.ood_score:.3f}; review threshold {res.ood_threshold:.3f}",
        *[f"- Warning: {w}" for w in res.warnings],
        "",
        "## Provenance",
        f"- Model: {card.get('protocol_id')} ({card.get('model')}, "
        f"{card.get('n_components')} components), mode {card.get('mode')}",
        f"- Model run id: {card.get('run_id')}; git {card.get('git', {}).get('head', '?')[:12]}",
        f"- Training manifest SHA-256: {card.get('manifest_sha256')}",
        f"- Data source: doi:{card.get('data_source_doi')} (CC BY 4.0)",
        "",
        "## Limitations",
        *[f"- {x}" for x in card.get("limitations", [])],
    ]
    return "\n".join(lines) + "\n"


def methods_report_md(card: dict[str, Any] | None, runs: list[Run]) -> str:
    """Reproducibility report: sources, model card, benchmark runs and the commands to rerun."""
    lines = [
        "# ChemiProof reproducibility report",
        "",
        "- Dataset: Zenodo doi:10.5281/zenodo.19755088 (CC BY 4.0), 330 EEM spectra",
        "- Paper: Sun et al. 2026, npj Science of Food, doi:10.1038/s41538-026-01037-6",
        "",
        "## Benchmark runs shown in the explorer",
        *[f"- {r.label}: protocol `{r.protocol}`, folder `{r.path.name}`" for r in runs],
        "",
        "## Screening model",
    ]
    if card:
        keep = ("protocol_id", "mode", "model", "n_components", "run_id", "config_sha256",
                "manifest_sha256", "train_sample_ids_hash", "model_npz_sha256")  # fmt: skip
        lines += [f"- {k}: {card.get(k)}" for k in keep]
        lines += [f"- limitation: {x}" for x in card.get("limitations", [])]
    else:
        lines.append("- none: research model not available")
    lines += [
        "",
        "## Commands",
        "```bash",
        "chemiproof dataset audit",
        "chemiproof experiment run --config config/experiments/baseline.yaml",
        "chemiproof experiment run --config config/experiments/ot_transductive.yaml",
        "chemiproof experiment uncertainty --config config/experiments/uncertainty_loao.yaml",
        "chemiproof model train-final",
        "chemiproof app",
        "```",
    ]
    return "\n".join(lines) + "\n"
