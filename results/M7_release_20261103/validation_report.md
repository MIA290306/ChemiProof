# M7 Scientific release: validation report

**Date:** 2026-11-03 · **Branch:** `m7/release` (from `27c6efb`) · **Machine:** collaborator's Mac, macOS 26.6.2 arm64
**Scope:** CP-701 clean reproduction, CP-702 report and cards, CP-703 rights/citation review, CP-704 README. **No new experimental result** was produced; this milestone re-runs and documents the existing ones.

## CP-701: clean-environment reproduction

Procedure (script kept in the session scratchpad; steps are the checklist in `docs/release/RELEASE_REVIEW.md` section 4):

| Step | Command | Exit | Result |
|---|---|---|---|
| fresh checkout | `git clone <repo>` + `git checkout m7/release` (HEAD `27c6efb`) | 0 | clean tree |
| data | copy of the extracted Zenodo `.dat` folders into the clone's `data/raw/extracted/` | 0 | 330 files |
| environment | `uv venv --python 3.12 .venv --no-cache`; `uv pip install --no-cache -c constraints.txt -e '.[dev]'` | 0 | Python 3.12.13; numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, POT 0.9.7.post1 |
| synthetic tests | `pytest -q -m "not dataset"` | 0 | 226 passed, 9 deselected |
| audit | `chemiproof dataset audit` | 0 | manifest sha256 `31c718edd95b4fac...`, 330 = 60/60/90/90/30, QC flag NEGATIVE_INTENSITY 330 |
| dataset tests | `pytest -q -m dataset` | 0 | 9 passed (a first call placed before the audit failed 6 tests because `data/interim/sample_manifest.csv` did not exist yet; ordering error in the script, rerun after the audit) |
| M2 | `chemiproof experiment run --config config/experiments/m2_source_internal.yaml` | 0 | `M2_20261103T084038Z_27c6efb_68d00a8b` |
| M3 | `... baseline.yaml`, `... loao_luhua_only.yaml` | 0, 0 | `M3_..._27c6efb_b1c2dfa1`, `M3_..._27c6efb_2fbd19b6` (locked, git dirty False) |
| M4 | `... ot_transductive.yaml`, `... ot_luhua_only.yaml` | 0, 0 | `M4_..._27c6efb_363deee6`, `M4_..._27c6efb_44fba4b8` (locked) |
| M5 | `chemiproof experiment uncertainty --config config/experiments/uncertainty_loao.yaml` | 0 | `M5_..._27c6efb_ac6bfcef` (locked) |
| controls | `chemiproof experiment control` for `baseline.yaml` and `loao_luhua_only.yaml` | 0, 0 | exploratory |
| stress tests | `chemiproof experiment batch-sensitivity` for `ot_transductive.yaml` and `ot_luhua_only.yaml` | 0, 0 | exploratory |
| final model | `chemiproof model train-final` | 0 | `M6_final_20261103T084209Z_27c6efb_82b39d6c` |

Comparison with the committed runs, by the new `chemiproof experiment compare` (every CSV plus `dataset_manifest_sha256.txt`; `run_id` ignored; absolute tolerance 1e-9 fraction). Verbatim output: `reproduction_compare.txt`.

| Committed run | Files | Rows | Max abs. difference | Exit |
|---|---:|---:|---:|---:|
| `M2_20261103T041143Z_ca43062_4097e86f` | 4 | 2,322 | 8e-15 | 0 |
| `M3_20261103T042740Z_01a9d42_b1c2dfa1` | 5 | 2,995 | 2.3e-14 | 0 |
| `M3_20261103T042759Z_01a9d42_2fbd19b6` | 5 | 1,375 | 0 | 0 |
| `M4_20261103T044749Z_7129cde_363deee6` | 6 | 3,355 | 0 | 0 |
| `M4_20261103T044812Z_7129cde_44fba4b8` | 6 | 1,555 | 0 | 0 |
| `M5_20261103T054226Z_914e8ed_ac6bfcef` | 10 | 2,298 | 7.2e-16 | 0 |

- Negative controls (`control_summary.json`, 38 numeric leaves each): equal to 1.1e-16 and 0. Batch stress tests (`batch_sensitivity.json`, 367 and 247 leaves): equal (0). Compared with a short JSON-leaf script, not with the CLI (it compares CSVs).
- FINAL-PLS-v1: `model_npz_sha256` `bbcff343011aa4e7...` identical; `n_components` 6, OOD threshold, interval half-widths and the 330 training-file hashes identical to the committed card.
- **Deviation explained:** the M2 rerun's folder suffix (config hash) is `68d00a8b`, not `4097e86f`. `config_resolved.yaml` differs only by three keys added to the schema after M2 with defaults (`n_samples: 330`, `run_class: exploratory`, `subset_brand: null`); `config/experiments/m2_source_internal.yaml` is unchanged since its M2 commit `f6d2144`, and every M2 table matches.

## Other checks on this branch

| Command | Exit | Result |
|---|---|---|
| `pytest -q -m "not dataset"` (repo venv, after M7 changes) | 0 | 236 passed, 9 deselected |
| `pytest -q -m dataset` | 0 | 9 passed |
| `ruff check .` / `ruff format --check .` | 0 / 0 | clean / 128 files formatted |
| package licenses from installed metadata (`docs/release/RELEASE_REVIEW.md` section 2) | 0 | 64 locked packages, all permissive (MIT/BSD/Apache-2.0/PSF/MPL-2.0) |

## Acceptance tests

| ID | Status | Evidence |
|---|---|---|
| T021 frozen results rerun within tolerance | PASS | table above; `tests/unit/test_compare.py` (7 tests) and `test_experiment_compare_cli` |
| T022 source links / data-reuse statements | PASS for dataset and author code; PENDING for ChemiProof's own license | `docs/release/RELEASE_REVIEW.md` sections 1-3; ADR-019 |
| T023 UI says research screening, unit, no certification | PASS (M6, unchanged) | `results/M6_explorer_20261103/validation_report.md` |
| External reviewer signoff | NOT RUN | no reviewer assigned |

## Limitations of this evidence

- Same OS family (macOS arm64) and the same numpy/scipy/scikit-learn versions as the original runs; Linux, x86 and other library versions are untested.
- The data in the clone is a copy of the same extracted folder; the published archive's MD5 is still unmatched (data card section 2).
- POT's version is not written to run `environment.json` (only numpy, scipy, scikit-learn, pydantic, PyYAML); recorded here instead.
