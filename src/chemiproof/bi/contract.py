"""Loads the BI data contract and protocol map; the only place that knows their shape.

CP-651 wrote config/bi/export_contract.yaml and config/bi/protocol_map.yaml as the frozen
twins of docs/bi/19_POWER_BI_DATA_MODEL.md. This module reads them back for the exporter
(CP-652) so a contract change is a one-file edit, never a code change.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

import yaml

CONTRACT_VERSION = "bi-contract-1.0.0"


def load_contract(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data["contract_version"] != CONTRACT_VERSION:
        raise ValueError(f"unexpected contract_version {data['contract_version']!r}")
    return data


def load_protocol_map(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data["contract_version"] != CONTRACT_VERSION:
        raise ValueError(f"unexpected contract_version {data['contract_version']!r}")
    return data


def table_columns(contract: dict[str, Any], table: str) -> list[str]:
    return [c["name"] for c in contract["tables"][table]["columns"]]


def resolve_protocol_id(protocol_map: dict[str, Any], config_sha256: str) -> tuple[str, bool]:
    """Rule P-2: the hash alone is the key; family/mode/run_class are descriptive only."""
    short = config_sha256[:16]
    for entry in protocol_map["entries"]:
        if short in entry["accepted_config_sha256"]:
            return entry["protocol_id"], True
    return protocol_map["fallback"]["protocol_id"], False


def _check_columns(
    table: str, contract: dict[str, Any], rows: list[dict[str, Any]], cols: list[str]
) -> None:
    """V-01: every row's keys must be exactly the contract's columns, in contract order."""
    expected = set(cols)
    for row in rows:
        got = set(row)
        if got != expected:
            raise ValueError(
                f"{table}: row columns {sorted(got)} do not match contract {sorted(expected)}"
            )


def write_table_csv(
    out_dir: Path, contract: dict[str, Any], table: str, rows: list[dict[str, Any]]
) -> dict[str, Any]:
    cols = table_columns(contract, table)
    _check_columns(table, contract, rows, cols)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{table}.csv"
    if path.exists():
        raise FileExistsError(f"refuse to overwrite existing export file: {path}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: ("" if row[k] is None else row[k]) for k in cols})
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"table": table, "format": "csv", "rows": len(rows), "sha256": sha}


def write_table_parquet(
    out_dir: Path, contract: dict[str, Any], table: str, rows: list[dict[str, Any]]
) -> dict[str, Any]:
    """Optional format behind the 'bi' extra (ADR-016 point 4); CSV stays the default."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ImportError("Parquet export needs the 'bi' extra: pip install -e '.[bi]'") from exc
    cols = table_columns(contract, table)
    _check_columns(table, contract, rows, cols)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{table}.parquet"
    if path.exists():
        raise FileExistsError(f"refuse to overwrite existing export file: {path}")
    arrays = {c: [row[c] for row in rows] for c in cols}
    pq.write_table(pa.table(arrays), path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"table": table, "format": "parquet", "rows": len(rows), "sha256": sha}


def write_table(
    out_dir: Path,
    contract: dict[str, Any],
    table: str,
    rows: list[dict[str, Any]],
    fmt: str = "csv",
) -> dict[str, Any]:
    if fmt == "csv":
        return write_table_csv(out_dir, contract, table, rows)
    if fmt == "parquet":
        return write_table_parquet(out_dir, contract, table, rows)
    raise ValueError(f"unknown export format {fmt!r}; use 'csv' or 'parquet'")
