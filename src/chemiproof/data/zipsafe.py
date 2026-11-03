"""Safe inspection/extraction of untrusted ZIP archives (extracts only if all checks pass)."""

from __future__ import annotations

import stat
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from chemiproof.errors import ChemiProofError, StatusCode

MAX_MEMBERS = 5_000
MAX_TOTAL_UNCOMPRESSED = 2 * 1024**3  # 2 GiB
MAX_RATIO = 200  # compressed -> uncompressed expansion per member (archive-bomb guard)


@dataclass
class ZipReport:
    members: int = 0
    total_uncompressed: int = 0
    extensions: dict[str, int] = field(default_factory=dict)


def _bad(msg: str, **ctx: object) -> ChemiProofError:
    return ChemiProofError(StatusCode.BAD_FILE_FORMAT, msg, **ctx)


def inspect_zip(archive: Path) -> ZipReport:
    """Inspect WITHOUT extracting. Raises BAD_FILE_FORMAT on traversal, symlinks, bombs, dupes."""
    try:
        zf = zipfile.ZipFile(archive)
    except (zipfile.BadZipFile, OSError) as exc:
        raise _bad("not a readable ZIP archive", archive=archive.name) from exc
    report = ZipReport()
    seen: set[str] = set()
    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_MEMBERS:
            raise _bad(f"too many members ({len(infos)})", archive=archive.name)
        for info in infos:
            name = info.filename
            p = PurePosixPath(name)
            if (
                p.is_absolute()
                or ".." in p.parts
                or "\\" in name
                or (len(name) > 1 and name[1] == ":")
            ):
                raise _bad("unsafe member path (traversal/absolute)", member=name)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise _bad("symlink member rejected", member=name)
            key = name.casefold()
            if key in seen:
                raise _bad("duplicate member name", member=name)
            seen.add(key)
            if info.compress_size and info.file_size / info.compress_size > MAX_RATIO:
                raise _bad("suspicious compression ratio (possible archive bomb)", member=name)
            report.members += 1
            report.total_uncompressed += info.file_size
            if report.total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                raise _bad("uncompressed size exceeds limit", archive=archive.name)
            ext = p.suffix.lower() or "<none>"
            report.extensions[ext] = report.extensions.get(ext, 0) + 1
    return report


def safe_extract(archive: Path, dest: Path) -> ZipReport:
    """Extract into an empty/new `dest` after inspect_zip passes; resolves every target path."""
    report = inspect_zip(archive)
    dest.mkdir(parents=True, exist_ok=True)
    if any(dest.iterdir()):
        raise _bad("destination must be empty", dest=dest.name)
    root = dest.resolve()
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = (root / info.filename).resolve()
            if root != target and root not in target.parents:
                raise _bad("member escapes destination", member=info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, target.open("wb") as out:
                    out.write(src.read())
    return report
