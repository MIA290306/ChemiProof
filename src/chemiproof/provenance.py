"""Run provenance: config hash, git state, environment, run ID.

run_id = UTC timestamp + short git hash + short config hash (docs/engineering/04_ARCHITECTURE.md).
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

SHORT = 8


def config_hash(config: dict[str, Any]) -> str:
    """SHA-256 of canonical JSON (sorted keys); independent of key order."""
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_short_hash(repo: Path | None = None) -> str:
    """Short HEAD hash, '+dirty' if the tree has uncommitted changes, 'nogit' if unavailable."""
    cwd = str(repo) if repo else None
    try:
        head = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "nogit"
    return f"{head}+dirty" if dirty else head


def make_run_id(config: dict[str, Any], now: datetime | None = None, git: str | None = None) -> str:
    """`now` and `git` are injectable so the ID is deterministic in tests."""
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    git_part = (git if git is not None else git_short_hash()).replace("+", "-")
    return f"{moment:%Y%m%dT%H%M%SZ}_{git_part}_{config_hash(config)[:SHORT]}"


def environment_info() -> dict[str, Any]:
    versions: dict[str, str] = {}
    for pkg in ("numpy", "scipy", "scikit-learn", "pydantic", "PyYAML", "chemiproof"):
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            versions[pkg] = "not-installed"
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": versions,
    }
