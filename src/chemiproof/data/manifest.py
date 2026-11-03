"""Build, write, read and audit the sample manifest (docs/science/03_DATA_CONTRACT.md).

The manifest is derived only from the folder layout + parsed `.dat` content; it never "fills in"
missing records. Unknown/odd things go to `problems` and the discrepancy ledger.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from chemiproof.data import labels
from chemiproof.data.parser import PARSER_VERSION, ParsedDat, parse_dat
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.provenance import file_sha256

SOURCE_DOI = "10.5281/zenodo.19755088"


@dataclass
class ManifestRow:
    sample_id: str
    relative_path: str
    sha256: str
    source_record_doi: str
    adulterant_type: str
    evoo_brand: str
    olive_fraction: float
    olive_ratio_raw: str
    measurement_round: int
    replicate_id: str  # empty: round->replicate mapping is not proven (ADR-008 notes)
    excitation_channels: int
    emission_channels: int
    excitation_min_nm: float
    excitation_max_nm: float
    emission_min_nm: float
    emission_max_nm: float
    axis_sha256: str
    source_excitation_order: str
    normalization_factor: float
    intensity_min: float
    intensity_max: float
    negative_cells: int
    qc_status: str  # PASS | WARN | FAIL
    qc_flags: str  # ';'-separated
    parser_version: str


@dataclass
class BuildResult:
    rows: list[ManifestRow]
    problems: list[dict[str, str]]
    extra_files: list[str]  # non-.dat files other than the expected companions, as NFC rel paths


def _axis_fingerprint(parsed: ParsedDat) -> str:
    s = parsed.spectrum
    return hashlib.sha256(s.excitation_nm.tobytes() + s.emission_nm.tobytes()).hexdigest()[:16]


def _row_from_parsed(rel: str, sha: str, meta: dict[str, Any], parsed: ParsedDat) -> ManifestRow:
    s = parsed.spectrum
    neg = int((s.intensity < 0).sum())
    flags = []
    status = "PASS"
    if neg:
        flags.append("NEGATIVE_INTENSITY")
        status = "WARN"
    if float(s.intensity.max()) == float(s.intensity.min()):
        flags.append("CONSTANT_SIGNAL")
        status = "FAIL"
    a, b = meta["ratio_parts"]
    sample_id = f"{meta['adulterant']}_{meta['brand']}_R{meta['round']}_{a:02d}-{b:02d}_{sha[:8]}"
    return ManifestRow(
        sample_id=sample_id,
        relative_path=rel,
        sha256=sha,
        source_record_doi=SOURCE_DOI,
        adulterant_type=meta["adulterant"],
        evoo_brand=meta["brand"],
        olive_fraction=meta["fraction"],
        olive_ratio_raw=meta["ratio_raw"],
        measurement_round=meta["round"],
        replicate_id="",
        excitation_channels=int(s.excitation_nm.size),
        emission_channels=int(s.emission_nm.size),
        excitation_min_nm=float(s.excitation_nm[0]),
        excitation_max_nm=float(s.excitation_nm[-1]),
        emission_min_nm=float(s.emission_nm[0]),
        emission_max_nm=float(s.emission_nm[-1]),
        axis_sha256=_axis_fingerprint(parsed),
        source_excitation_order=parsed.source_excitation_order,
        normalization_factor=parsed.normalization_factor,
        intensity_min=float(s.intensity.min()),
        intensity_max=float(s.intensity.max()),
        negative_cells=neg,
        qc_status=status,
        qc_flags=";".join(flags),
        parser_version=PARSER_VERSION,
    )


def build_manifest(data_dir: Path) -> BuildResult:
    if not data_dir.is_dir():
        raise ChemiProofError(
            StatusCode.DATASET_NOT_AVAILABLE, "data directory not found", data_dir=data_dir.name
        )
    rows: list[ManifestRow] = []
    problems: list[dict[str, str]] = []
    extras: list[str] = []
    for group in sorted(p for p in data_dir.iterdir() if p.is_dir() and not p.name.startswith(".")):
        try:
            brand, adulterant = labels.parse_group_dir(group.name)
        except ChemiProofError as exc:
            problems.append({"path": labels.nfc(group.name), "issue": exc.message})
            continue
        for rnd in sorted(p for p in group.iterdir() if p.is_dir()):
            for ratio in sorted(p for p in rnd.iterdir() if p.is_dir()):
                rel = "/".join(labels.nfc(x) for x in (group.name, rnd.name, ratio.name))
                try:
                    rnum = labels.parse_round_dir(rnd.name)
                    a, b, frac = labels.parse_ratio_dir(ratio.name)
                except ChemiProofError as exc:
                    problems.append({"path": rel, "issue": exc.message})
                    continue
                files = sorted(
                    f for f in ratio.iterdir() if f.is_file() and not f.name.startswith(".")
                )
                dats = [f for f in files if f.suffix == ".dat"]
                extras += [f"{rel}/{labels.nfc(f.name)}" for f in files if f.suffix != ".dat"]
                if len(dats) != 1:
                    problems.append(
                        {"path": rel, "issue": f"expected exactly 1 .dat, found {len(dats)}"}
                    )
                    continue
                meta = {
                    "adulterant": adulterant,
                    "brand": brand,
                    "round": rnum,
                    "ratio_parts": (a, b),
                    "fraction": frac,
                    "ratio_raw": labels.nfc(ratio.name),
                }
                sha = file_sha256(dats[0])
                rel_file = f"{rel}/{labels.nfc(dats[0].name)}"
                try:
                    parsed = parse_dat(dats[0], sample_id=rel_file)
                except ChemiProofError as exc:
                    problems.append({"path": rel_file, "issue": str(exc)})
                    continue
                rows.append(_row_from_parsed(rel_file, sha, meta, parsed))
    return BuildResult(rows, problems, extras)


def write_manifest_csv(rows: list[ManifestRow], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [f.name for f in fields(ManifestRow)]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))
    return file_sha256(path)


def read_manifest_csv(path: Path) -> list[ManifestRow]:
    if not path.is_file():
        raise ChemiProofError(
            StatusCode.DATASET_NOT_AVAILABLE,
            "sample manifest not found; run the dataset audit first",
            manifest=path.name,
        )
    casts: dict[str, Any] = {
        f.name: (int if f.type == "int" else float if f.type == "float" else str)
        for f in fields(ManifestRow)
    }
    out = []
    with path.open(newline="", encoding="utf-8") as fh:
        for rec in csv.DictReader(fh):
            out.append(ManifestRow(**{k: casts[k](v) for k, v in rec.items()}))
    return out


def build_audit(result: BuildResult) -> dict[str, Any]:
    """Compare observed inventory with the published expectations; list every discrepancy."""
    rows = result.rows
    by_ad = Counter(r.adulterant_type for r in rows)
    brand_x = defaultdict(Counter)
    for r in rows:
        brand_x[r.adulterant_type][r.evoo_brand] += 1
    cell = defaultdict(lambda: defaultdict(set))  # (brand, ad) -> level -> rounds
    for r in rows:
        cell[(r.evoo_brand, r.adulterant_type)][r.olive_ratio_raw].add(r.measurement_round)
    ledger: list[str] = []
    for ad, exp in labels.EXPECTED_COUNTS.items():
        if by_ad.get(ad, 0) != exp:
            ledger.append(f"{ad}: observed {by_ad.get(ad, 0)}, expected {exp}")
    for ad, brands in labels.EXPECTED_BRANDS.items():
        seen = set(brand_x[ad])
        if seen != brands:
            ledger.append(f"{ad}: brands observed {sorted(seen)}, expected {sorted(brands)}")
    for (brand, ad), levels in sorted(cell.items()):
        if len(levels) != 10:
            ledger.append(f"{brand}/{ad}: {len(levels)} ratio levels, expected 10")
        for lvl, rounds in sorted(levels.items()):
            if rounds != {1, 2, 3}:
                ledger.append(f"{brand}/{ad}/{lvl}: rounds {sorted(rounds)}, expected [1, 2, 3]")
    if len(rows) != 330:
        ledger.append(f"total records {len(rows)}, expected 330")
    sha_counts = Counter(r.sha256 for r in rows)
    dups = {h: c for h, c in sha_counts.items() if c > 1}
    if dups:
        ledger.append(f"duplicate file contents: {len(dups)} hashes")
    if len({r.axis_sha256 for r in rows}) > 1:
        ledger.append("wavelength axes differ between files")
    for p in result.problems:
        ledger.append(f"problem: {p['path']}: {p['issue']}")
    names = Counter(Path(r.relative_path).name for r in rows)
    extra_by_suffix = Counter(Path(e).suffix.lower() for e in result.extra_files)
    duplicate_copies = sorted(e for e in result.extra_files if "(" in Path(e).name)
    return {
        "total_records": len(rows),
        "expected_total": 330,
        "by_adulterant": {
            a: {"observed": by_ad.get(a, 0), "expected": e}
            for a, e in labels.EXPECTED_COUNTS.items()
        },
        "brand_by_adulterant": {a: dict(c) for a, c in sorted(brand_x.items())},
        "ratio_levels": sorted({r.olive_ratio_raw for r in rows}),
        "olive_fraction_range": [
            min(r.olive_fraction for r in rows),
            max(r.olive_fraction for r in rows),
        ]
        if rows
        else None,
        "qc_status": dict(Counter(r.qc_status for r in rows)),
        "qc_flags": dict(Counter(f for r in rows for f in r.qc_flags.split(";") if f)),
        "negative_cells_total": int(sum(r.negative_cells for r in rows)),
        "intensity_min": float(min(r.intensity_min for r in rows)) if rows else None,
        "intensity_max": float(max(r.intensity_max for r in rows)) if rows else None,
        "distinct_axes": len({r.axis_sha256 for r in rows}),
        "source_excitation_order": dict(Counter(r.source_excitation_order for r in rows)),
        "normalization_factors": dict(Counter(str(r.normalization_factor) for r in rows)),
        "dat_file_names": dict(names),
        "duplicate_hashes": len(dups),
        "extra_non_dat_files": len(result.extra_files),
        "extra_non_dat_by_suffix": dict(extra_by_suffix),
        "extra_duplicate_copy_files": duplicate_copies,
        "problems": result.problems,
        "discrepancy_ledger": ledger,
        "parser_version": PARSER_VERSION,
    }


def evidence_json() -> dict[str, Any]:
    return {
        "olive_fraction": {
            "rule": "folder 'a：b' (full-width colon) = olive:adulterant parts by volume; "
            "a+b==11; y=a/11",
            "source": "Zenodo 19755088 description: 'olive-oil volume fractions 9.09% to 90.91%', "
            "'olive-oil-to-adulterant ratio'",
            "supporting": "chlorophyll-band probe (data_audit.json); decision ADR-008",
        },
        "adulterant_type_and_evoo_brand": {
            "rule": "exact Chinese folder-name fragments -> labels (chemiproof.data.labels)",
            "source": "article Table 2 as recorded in docs/science/03_DATA_CONTRACT.md "
            "(Earl Grey=伯爵, Luhua=鲁花, OliVera=欧丽薇兰); observed counts agree",
        },
        "measurement_round": {"rule": "folder 第一/二/三轮 -> 1/2/3", "source": "folder name"},
        "replicate_id": {
            "rule": "left empty",
            "source": "round->replicate equivalence is not proven",
        },
        "excitation_axis": {
            "rule": "file order descending 640->300 nm; reordered ascending by one explicit rule",
            "source": "parser.py; source order recorded per row",
        },
    }


def write_audit_outputs(
    out_dir: Path, result: BuildResult, audit: dict[str, Any], extra: dict[str, Any] | None = None
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    full = {**audit, **(extra or {})}
    (out_dir / "data_audit.json").write_text(
        json.dumps(full, indent=2, ensure_ascii=False), "utf-8"
    )
    (out_dir / "metadata_evidence.json").write_text(
        json.dumps(evidence_json(), indent=2, ensure_ascii=False), "utf-8"
    )
    with (out_dir / "qc_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "sample_id",
                "qc_status",
                "qc_flags",
                "intensity_min",
                "intensity_max",
                "negative_cells",
            ]
        )
        for r in result.rows:
            w.writerow(
                [
                    r.sample_id,
                    r.qc_status,
                    r.qc_flags,
                    r.intensity_min,
                    r.intensity_max,
                    r.negative_cells,
                ]
            )


def manifest_fingerprint(rows: list[ManifestRow]) -> str:
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda x: x.sample_id):
        h.update(f"{r.sample_id}|{r.sha256}|{r.olive_fraction}".encode())
    return h.hexdigest()
