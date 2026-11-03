"""Command-line interface. Commands for later milestones fail with a truthful status code."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from chemiproof import __version__
from chemiproof.config import load_experiment_config, load_project_config
from chemiproof.data.manifest import (
    build_audit,
    build_manifest,
    manifest_fingerprint,
    read_manifest_csv,
    write_audit_outputs,
    write_manifest_csv,
)
from chemiproof.data.zipsafe import inspect_zip
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.experiments import (
    run_experiment,
    run_negative_control,
    run_ot_batch_sensitivity,
)
from chemiproof.provenance import environment_info, make_run_id

EXIT_OK = 0
EXIT_ERROR = 3  # argparse itself exits 2 on usage errors

DEFAULT_DATA_DIR = Path("data/raw/extracted")
DEFAULT_MANIFEST = Path("data/interim/sample_manifest.csv")
DEFAULT_RESULTS = Path("results")


def _not_implemented(milestone: str, what: str) -> ChemiProofError:
    return ChemiProofError(StatusCode.NOT_IMPLEMENTED, f"{what} is implemented in {milestone}")


def _cmd_config_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if args.kind == "project":
        load_project_config(path)
    else:
        load_experiment_config(path)
    print(f"OK: {path.name} is a valid {args.kind} config (schema check only; no run performed)")
    return EXIT_OK


def _cmd_inspect_zip(args: argparse.Namespace) -> int:
    archive = Path(args.archive)
    if not archive.is_file():
        raise ChemiProofError(
            StatusCode.DATASET_NOT_AVAILABLE, "archive not found", archive=archive.name
        )
    rep = inspect_zip(archive)
    print(
        f"ZIP OK (not extracted): {rep.members} members, {rep.total_uncompressed} bytes, "
        f"extensions={rep.extensions}"
    )
    return EXIT_OK


def _cmd_dataset_inspect(args: argparse.Namespace) -> int:
    result = build_manifest(Path(args.data_dir))
    audit = build_audit(result)
    print(
        json.dumps(
            {
                k: audit[k]
                for k in (
                    "total_records",
                    "by_adulterant",
                    "brand_by_adulterant",
                    "qc_status",
                    "discrepancy_ledger",
                )
            },
            indent=2,
        )
    )
    return EXIT_OK if not audit["discrepancy_ledger"] else EXIT_ERROR


def _cmd_dataset_audit(args: argparse.Namespace) -> int:
    from chemiproof.spectra.qc import chlorophyll_probe

    data_dir = Path(args.data_dir)
    result = build_manifest(data_dir)
    audit = build_audit(result)
    manifest_sha = write_manifest_csv(result.rows, Path(args.manifest))
    run_id = make_run_id({"manifest_sha256": manifest_sha, "parser": audit["parser_version"]})
    out = Path(args.output_dir) if args.output_dir else DEFAULT_RESULTS / f"M1_{run_id}"
    extra = {
        "run_id": run_id,
        "manifest_sha256": manifest_sha,
        "manifest_fingerprint": manifest_fingerprint(result.rows),
        "source_doi": "10.5281/zenodo.19755088",
        "environment": environment_info(),
        "chlorophyll_probe": chlorophyll_probe(data_dir, result.rows),
    }
    write_audit_outputs(out, result, audit, extra)
    (Path(args.manifest).parent / "manifest_sha256.txt").write_text(manifest_sha + "\n")
    print(
        f"manifest: {args.manifest} (sha256 {manifest_sha[:16]}...) "
        f"records={audit['total_records']}"
    )
    print(f"audit outputs: {out}")
    if audit["discrepancy_ledger"]:
        print("DISCREPANCIES:\n  " + "\n  ".join(audit["discrepancy_ledger"]), file=sys.stderr)
        raise ChemiProofError(StatusCode.QC_REVIEW_REQUIRED, "inventory differs from expectations")
    print(
        "inventory matches published expectations (330 = 60/60/90/90/30); QC flags: "
        f"{audit['qc_flags']}"
    )
    return EXIT_OK


def _cmd_spectra_plot(args: argparse.Namespace) -> int:
    from chemiproof.spectra.visualize import plot_gallery, plot_sample

    rows = read_manifest_csv(Path(args.manifest))
    data_dir, out = Path(args.data_dir), Path(args.output)
    if args.sample:
        match = [r for r in rows if r.sample_id == args.sample]
        if not match:
            raise ChemiProofError(
                StatusCode.UNVERIFIED_LABEL, "unknown sample id", sample_id=args.sample
            )
        plot_sample(data_dir, match[0], out)
        print(f"wrote {out} ({args.sample})")
    else:
        ids = plot_gallery(data_dir, rows, out)
        print(f"wrote {out} showing {len(ids)} real EEMs: {', '.join(ids)}")
    return EXIT_OK


def _cmd_spectra_compare(args: argparse.Namespace) -> int:
    from chemiproof.spectra.visualize import plot_preprocessing

    rows = read_manifest_csv(Path(args.manifest))
    used = plot_preprocessing(Path(args.data_dir), rows, Path(args.output))
    print(f"wrote {args.output} (raw vs processed; raw files untouched): {', '.join(used)}")
    return EXIT_OK


def _cmd_experiment(args: argparse.Namespace) -> int:
    cfg = load_experiment_config(Path(args.config))  # validate BEFORE anything else
    manifest = Path(cfg.model_dump().get("dataset_manifest", DEFAULT_MANIFEST))
    out_dir = run_experiment(cfg, Path(args.data_dir), manifest, Path(args.output_root))
    print(f"run artifacts: {out_dir}")
    print((out_dir / "run_report.md").read_text(encoding="utf-8"))
    return EXIT_OK


def _cmd_control(args: argparse.Namespace) -> int:
    cfg = load_experiment_config(Path(args.config))
    manifest = Path(cfg.model_dump().get("dataset_manifest", DEFAULT_MANIFEST))
    out_dir = run_negative_control(cfg, Path(args.data_dir), manifest, Path(args.output_root))
    print(f"control artifacts: {out_dir}")
    print((out_dir / "control_summary.json").read_text(encoding="utf-8"))
    return EXIT_OK


def _cmd_batch_sensitivity(args: argparse.Namespace) -> int:
    cfg = load_experiment_config(Path(args.config))
    manifest = Path(cfg.model_dump().get("dataset_manifest", DEFAULT_MANIFEST))
    out_dir = run_ot_batch_sensitivity(cfg, Path(args.data_dir), manifest, Path(args.output_root))
    print(f"batch-sensitivity artifacts: {out_dir}")
    return EXIT_OK


def _unavailable(milestone: str, what: str) -> Callable[[argparse.Namespace], int]:
    def run(_: argparse.Namespace) -> int:
        raise _not_implemented(milestone, what)

    return run


def _add_data_args(p: argparse.ArgumentParser, manifest: bool = True) -> None:
    p.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    if manifest:
        p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chemiproof",
        description=(
            "ChemiProof research CLI. Research prototype; NOT a certified authenticity test."
        ),
    )
    parser.add_argument("--version", action="version", version=f"chemiproof {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    cfg = sub.add_parser("config", help="validate configuration files")
    val = cfg.add_subparsers(dest="action", required=True).add_parser("validate")
    val.add_argument("kind", choices=["project", "experiment"])
    val.add_argument("path")
    val.set_defaults(func=_cmd_config_validate)

    ds = sub.add_parser("dataset", help="dataset inspection and audit (M1)")
    ds_sub = ds.add_subparsers(dest="action", required=True)
    z = ds_sub.add_parser("inspect-zip", help="safety-check a ZIP without extracting")
    z.add_argument("--archive", default="data/raw/data.zip")
    z.set_defaults(func=_cmd_inspect_zip)
    i = ds_sub.add_parser("inspect", help="print inventory only; writes nothing")
    _add_data_args(i, manifest=False)
    i.set_defaults(func=_cmd_dataset_inspect)
    a = ds_sub.add_parser("audit", help="build manifest + audit report")
    _add_data_args(a)
    a.add_argument("--output-dir", default=None)
    a.set_defaults(func=_cmd_dataset_audit)

    sp = sub.add_parser("spectra", help="spectrum plots from real data")
    sp_sub = sp.add_subparsers(dest="action", required=True)
    p = sp_sub.add_parser("plot")
    _add_data_args(p)
    p.add_argument("--sample", default=None, help="sample_id; default: gallery of 10 samples")
    p.add_argument("--output", required=True)
    p.set_defaults(func=_cmd_spectra_plot)
    c = sp_sub.add_parser("compare", help="raw vs preprocessed EEM (reads raw, never overwrites)")
    _add_data_args(c)
    c.add_argument("--output", required=True)
    c.set_defaults(func=_cmd_spectra_compare)

    ex = sub.add_parser("experiment", help="experiments (available from M2)")
    ex_sub = ex.add_subparsers(dest="action", required=True)
    run = ex_sub.add_parser("run")
    run.add_argument("--config", required=True)
    run.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    run.add_argument("--output-root", default=str(DEFAULT_RESULTS))
    run.set_defaults(func=_cmd_experiment)
    ctl = ex_sub.add_parser(
        "control", help="negative control: permuted source labels (exploratory)"
    )
    ctl.add_argument("--config", required=True)
    ctl.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    ctl.add_argument("--output-root", default=str(DEFAULT_RESULTS))
    ctl.set_defaults(func=_cmd_control)
    bs = ex_sub.add_parser("batch-sensitivity", help="OT with smaller / single-brand batches")
    bs.add_argument("--config", required=True)
    bs.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    bs.add_argument("--output-root", default=str(DEFAULT_RESULTS))
    bs.set_defaults(func=_cmd_batch_sensitivity)
    ex_sub.add_parser("report").set_defaults(func=_unavailable("M7", "experiment report"))

    sub.add_parser("app", help="research explorer (available from M6)").set_defaults(
        func=_unavailable("M6", "the Streamlit explorer")
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ChemiProofError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
