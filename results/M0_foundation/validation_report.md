# M0 Foundation — validation report

**Date:** 2026-11-02 · **Env:** Python 3.12.15, macOS arm64, packages pinned in `constraints.txt`
**Scope:** tooling, config validation, synthetic fixtures, truthful CLI. **NO EXPERIMENTAL RESULTS** (no real data, no model, no metrics).

## Commands actually run (from repo root, venv `.venv`)

| Command | Exit | Result |
|---|---|---|
| `python3.12 -m venv .venv && pip install -e '.[dev]'` | 0 | installed; all deps had arm64 wheels (`--only-binary` dry-run succeeded) |
| `pytest -q -m "not dataset"` | 0 | 41 passed, 1 deselected |
| `ruff check .` | 0 | All checks passed |
| `ruff format --check .` | 0 | 45 files already formatted |
| `pre-commit run --all-files` | 0 | ruff check/format passed; raw-data guard skipped (no matching files) |
| Clean install: new venv, `pip install -c constraints.txt -e '.[dev]'`, then pytest + ruff | 0 | 41 passed; ruff clean |
| `chemiproof --help` | 0 | usage printed, shows "NOT a certified authenticity test" |
| `chemiproof dataset audit` (no archive) | 3 | `ERROR [DATASET_NOT_AVAILABLE] ...` |
| `chemiproof experiment run --config config/experiments/baseline.yaml` | 3 | `ERROR [DATASET_NOT_AVAILABLE] sample manifest not found` |
| `chemiproof config validate project config/project.yaml` | 0 | OK (schema check only) |
| `pytest -q -m dataset` | 1 | fails on purpose: dataset tests never pass silently without the archive |

## Acceptance tests

| ID | Status | Evidence |
|---|---|---|
| T001 (synthetic 35×270 EEM, monotonic axes, finite, no mutation) | PASS | `tests/unit/test_synthetic_eem.py` |
| T002–T024 | NOT RUN | belong to M1–M7 |
| GitHub Actions `ci` workflow on the remote | PASS | run 41572684248, commit `c1e8a98`, conclusion `success` (queried with `gh run list`): https://github.com/MIA290306/ChemiProof/actions/runs/41572684248 |

## M0 exit-gate checklist

- Clean install works: PASS (see clean-install row).
- `pytest` passes on synthetic fixtures: PASS (41 tests).
- Lint passes: PASS.
- CLI help and `DATASET_NOT_AVAILABLE` path tested: PASS (`tests/integration/test_cli_and_stages.py`).
- Docs match repo: see decision log ADR-006/007 and progress log.
- CI green on GitHub: PASS (run above).

## Known limitations

- Fixtures are Gaussian blobs with invented axes; they say nothing about real chemistry.
- Axis ranges (300–640 / 300–800 nm) and the 35×270 shape come from the paper and are unverified until M1.
- `pre-commit install` was not run (it edits `.git/hooks`); the config is validated only via `run --all-files`.
- Pipeline stages other than `load_dataset`/`screen_single` are CLI-level placeholders returning `NOT_IMPLEMENTED`.
