"""Cloud bootstrap for the public Streamlit explorer (ADR-021).

The repository never contains the raw spectra or the trained model file (CLAUDE.md invariant 10).
A hosted instance therefore rebuilds them on first start, using only already-validated steps:

1. download `data.zip` from the official Zenodo record and verify the PUBLISHED MD5;
2. inspect and extract it with `zipsafe` (traversal, symlink and archive-bomb guards);
3. run `chemiproof dataset audit`; the manifest SHA-256 must equal the locked value;
4. run `chemiproof model train-final` into a staging folder;
5. compare the new model card with the COMMITTED FINAL-PLS-v1 card (same manifest, same training
   ids, same n_components, OOD threshold and interval half-widths within a tight tolerance).

Only if every check passes is the artifact moved into `results/`. Any failure leaves the app in
its documented degraded state (benchmark pages only; "Research model not available"). Nothing is
tuned, selected or re-scored here: this re-executes the locked protocol and checks it reproduces.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from chemiproof.modeling.final import ARTIFACT_PREFIX, PROTOCOL_ID, latest_artifact

ZENODO_URL = "https://zenodo.org/api/records/19755088/files/data.zip/content"
ZENODO_MD5 = "dfad908d186e584b96b6070d90cbeec4"  # published on the Zenodo record (03_DATA_CONTRACT)
ZIP_MAX_BYTES = 200 * 1024**2  # published size ~95.9 MB; refuse anything far larger
LOCKED_MANIFEST_SHA256 = "31c718edd95b4faca5f0f3fe68871870dc6f1b5d2307a8af93e8ce3712765495"
REL_TOL = 1e-6  # cross-platform BLAS rounding only; anything larger means a different model


class BootstrapError(RuntimeError):
    """A bootstrap check failed; the app must stay in its degraded state."""


@dataclass
class BootstrapReport:
    status: str = "not_run"  # ready | already_present | failed
    steps: list[str] = field(default_factory=list)
    artifact: str | None = None
    error: str | None = None


def _md5(path: Path) -> str:
    h = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_zip(dest: Path, url: str = ZENODO_URL, expected_md5: str = ZENODO_MD5) -> Path:
    """Download to `dest` (skipped if a verified copy is already there); verify the MD5."""
    if dest.is_file() and _md5(dest) == expected_md5:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "chemiproof-explorer"})
    with urllib.request.urlopen(req, timeout=120) as resp, part.open("wb") as out:  # noqa: S310
        total = 0
        for chunk in iter(lambda: resp.read(1 << 20), b""):
            total += len(chunk)
            if total > ZIP_MAX_BYTES:
                raise BootstrapError(f"download exceeds {ZIP_MAX_BYTES} bytes; refused")
            out.write(chunk)
    got = _md5(part)
    if got != expected_md5:
        part.unlink(missing_ok=True)
        raise BootstrapError(f"MD5 mismatch: got {got}, published {expected_md5}")
    part.replace(dest)
    return dest


def _data_root(extracted: Path) -> Path:
    """The archive may wrap the sample folders in one top-level directory."""
    root = extracted
    while True:
        entries = [p for p in root.iterdir() if not p.name.startswith((".", "__MACOSX"))]
        if len(entries) == 1 and entries[0].is_dir():
            root = entries[0]
        else:
            return root


def check_card(new: dict, locked: dict) -> None:
    """The rebuilt model must be the locked FINAL-PLS-v1, not merely a similar one."""
    for key in ("protocol_id", "mode", "model", "preprocess", "n_components", "n_train",
                "train_counts_by_adulterant", "manifest_sha256", "train_sample_ids_hash",
                "data_source_doi"):  # fmt: skip
        if new.get(key) != locked.get(key):
            raise BootstrapError(f"model card differs from locked card on {key!r}")
    pairs = [(new["ood"]["threshold"], locked["ood"]["threshold"], "ood.threshold")]
    for k, v in locked["interval"]["halfwidth_fraction"].items():
        pairs.append((new["interval"]["halfwidth_fraction"][k], v, f"interval.halfwidth.{k}"))
    for a, b, name in pairs:
        if abs(float(a) - float(b)) > REL_TOL * max(1.0, abs(float(b))):
            raise BootstrapError(f"{name} differs from locked card: {a} vs {b}")


def locked_card(results: Path) -> dict:
    """The committed FINAL-PLS-v1 card (its model.npz is git-ignored, so only the card exists)."""
    cards = sorted(results.glob(f"{ARTIFACT_PREFIX}*/model_card.json"))
    for c in reversed(cards):
        card = json.loads(c.read_text(encoding="utf-8"))
        if card.get("protocol_id") == PROTOCOL_ID:
            return card
    raise BootstrapError("no committed FINAL-PLS-v1 model card to verify against")


def ensure_ready(
    results: Path,
    data_dir: Path,
    manifest: Path,
    work: Path,
    url: str = ZENODO_URL,
    expected_md5: str = ZENODO_MD5,
    expected_manifest_sha: str = LOCKED_MANIFEST_SHA256,
) -> BootstrapReport:
    """Idempotent: does nothing when a verified dataset and model are already present."""
    from chemiproof import cli
    from chemiproof.data.zipsafe import safe_extract

    rep = BootstrapReport()
    have_model = latest_artifact(results) is not None
    have_data = manifest.is_file() and data_dir.is_dir()
    if have_model and have_data:
        rep.status = "already_present"
        rep.artifact = str(latest_artifact(results))
        return rep
    try:
        reference = locked_card(results)
        if not have_data:
            archive = download_zip(work / "data.zip", url, expected_md5)
            rep.steps.append(f"downloaded data.zip, MD5 {expected_md5} verified")
            extracted = work / "extracted"
            if extracted.exists():
                shutil.rmtree(extracted)
            zr = safe_extract(archive, extracted)
            rep.steps.append(f"safe-extracted {zr.members} members")
            src = _data_root(extracted)
            if data_dir.exists():
                shutil.rmtree(data_dir)
            data_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(data_dir))
            archive.unlink(missing_ok=True)  # keep only the extracted copy (disk)
            audit_out = work / "audit"
            code = cli.main(["dataset", "audit", "--data-dir", str(data_dir), "--manifest",
                             str(manifest), "--output-dir", str(audit_out)])  # fmt: skip
            if code != 0:
                raise BootstrapError(f"dataset audit failed (exit {code})")
            got = hashlib.sha256(manifest.read_bytes()).hexdigest()
            if got != expected_manifest_sha:
                raise BootstrapError(f"manifest SHA-256 {got[:16]}... is not the locked one")
            rep.steps.append(f"audit passed, manifest SHA-256 {got[:16]}... matches locked")
        if not have_model:
            staging = work / "staging"
            if staging.exists():
                shutil.rmtree(staging)
            code = cli.main(["model", "train-final", "--data-dir", str(data_dir), "--manifest",
                             str(manifest), "--output-root", str(staging)])  # fmt: skip
            if code != 0:
                raise BootstrapError(f"train-final failed (exit {code})")
            art = latest_artifact(staging)
            if art is None:
                raise BootstrapError("train-final produced no complete artifact")
            check_card(json.loads((art / "model_card.json").read_text(encoding="utf-8")), reference)
            rep.steps.append(f"FINAL-PLS-v1 rebuilt and matches locked card {reference['run_id']}")
            target = results / art.name
            shutil.move(str(art), str(target))
            rep.artifact = str(target)
        else:
            rep.artifact = str(latest_artifact(results))
        rep.status = "ready"
    except Exception as exc:  # noqa: BLE001  (any failure -> documented degraded state)
        rep.status, rep.error = "failed", f"{type(exc).__name__}: {exc}"
    return rep
