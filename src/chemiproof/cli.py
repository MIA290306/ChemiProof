"""Command-line interface. Commands for later milestones fail with a truthful status code."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from chemiproof import __version__
from chemiproof.config import load_experiment_config, load_project_config
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.pipeline import load_dataset

EXIT_OK = 0
EXIT_ERROR = 3  # argparse itself exits 2 on usage errors

DEFAULT_ARCHIVE = Path("data/raw/data.zip")
DEFAULT_MANIFEST = Path("data/interim/sample_manifest.csv")


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


def _cmd_dataset(args: argparse.Namespace) -> int:
    archive = Path(args.archive)
    if not archive.is_file():
        raise ChemiProofError(
            StatusCode.DATASET_NOT_AVAILABLE,
            "dataset archive not found; download it manually after a license check "
            "(see data/README.md)",
            archive=archive.name,
        )
    raise _not_implemented("M1", f"dataset {args.action}")


def _cmd_experiment(args: argparse.Namespace) -> int:
    cfg = load_experiment_config(Path(args.config))  # validate BEFORE anything else
    load_dataset(Path(cfg.model_dump().get("dataset_manifest", DEFAULT_MANIFEST)))
    raise _not_implemented("M2-M4", "experiment run")


def _cmd_unavailable(milestone: str, what: str):
    def run(_: argparse.Namespace) -> int:
        raise _not_implemented(milestone, what)

    return run


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
    cfg_sub = cfg.add_subparsers(dest="action", required=True)
    val = cfg_sub.add_parser("validate", help="schema-check a YAML config")
    val.add_argument("kind", choices=["project", "experiment"])
    val.add_argument("path")
    val.set_defaults(func=_cmd_config_validate)

    ds = sub.add_parser("dataset", help="dataset audit (available from M1)")
    ds_sub = ds.add_subparsers(dest="action", required=True)
    for action in ("inspect", "audit"):
        p = ds_sub.add_parser(action)
        p.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
        p.set_defaults(func=_cmd_dataset)

    sp = sub.add_parser("spectra", help="spectrum plots (available from M1)")
    sp.add_subparsers(dest="action", required=True).add_parser("plot").set_defaults(
        func=_cmd_unavailable("M1", "spectra plot")
    )

    ex = sub.add_parser("experiment", help="experiments (available from M2)")
    ex_sub = ex.add_subparsers(dest="action", required=True)
    run = ex_sub.add_parser("run")
    run.add_argument("--config", required=True)
    run.set_defaults(func=_cmd_experiment)
    ex_sub.add_parser("report").set_defaults(func=_cmd_unavailable("M7", "experiment report"))

    sub.add_parser("app", help="research explorer (available from M6)").set_defaults(
        func=_cmd_unavailable("M6", "the Streamlit explorer")
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
