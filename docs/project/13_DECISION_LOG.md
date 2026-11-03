# Architecture Decision Records (ADRs) / Scientific Decision Log

## ADR-001 — Research before dashboard

- **Date:** 2026-10-24
- **Status:** ACCEPTED as initial scope
- **Decision:** Validate data and LOAO evaluation before a UI.
- **Why:** The product is only credible if input labels/axes and comparison method are verified.
- **Consequences:** M0–M5 focus on parsing, experiments and uncertainty. Streamlit is M6.

## ADR-002 — Independent single-sample versus batch adaptation

- **Date:** 2026-10-24
- **Status:** ACCEPTED
- **Decision:** Define `inductive_single` and `transductive_batch` as separate and never present one mode's metric as the other.
- **Why:** Published OT method uses unlabeled target batch X; a single-file prediction does not have this target distribution.
- **Consequences:** Different tests, artifacts and UI entry points.

## ADR-003 — Use external original dataset, not embedded archive

- **Date:** 2026-10-24
- **Status:** ACCEPTED provisionally (subject to rights verification)
- **Decision:** Source Zenodo `10.5281/zenodo.19755088`, keep raw third-party data outside tracked Git, record hash and citation.
- **Why:** Reproducibility + risk of unauthorized distribution.
- **Consequences:** Need opt-in M1 download, manifest and license check.

## ADR-004 — Primary metric protocol

- **Date:** 2026-10-24
- **Status:** ACCEPTED
- **Decision:** Five LOAO outer folds, per-fold MAE/RMSE/R²/bias, macro plus pooled, source-only inner model selection.
- **Why:** Random split would not measure unseen adulterant performance; unequal group sizes affect pooled scores.
- **Consequences:** More stringent and honest comparison; a single aggregate score is insufficient.

## ADR-005 — Calibration claims

- **Date:** 2026-10-24
- **Status:** ACCEPTED
- **Decision:** No nominal prediction-interval coverage guarantee under LOAO shift. Report empirical target coverage and selective error at coverage.
- **Why:** Standard exchangeability requirements may fail when target adulterant changes.
- **Consequences:** UI uses “empirical research interval” rather than certainty.

## ADR-006 — Basic stack

- **Date:** 2026-10-24
- **Status:** ACCEPTED at M0 (2026-11-02), pending owner sign-off with M0 review
- **Decision proposal:** Python + NumPy/Pandas/SciPy/scikit-learn, Pytest/Ruff, POT only in M4, Streamlit in M6. No backend/auth/LLM services.
- **Why:** Appropriate to single-user reproducible scientific research.
- **Resolved at M0:** CPython 3.12 (Homebrew 3.12.15, arm64); `python -m venv` + pip with a `constraints.txt` produced by `pip freeze` (no `uv`); `argparse` CLI; Pydantic + PyYAML (`safe_load` only) for config. Verified via `pip install --dry-run --only-binary=:all:` that NumPy, SciPy, scikit-learn, pandas, Pydantic, PyYAML, pytest, ruff, pre-commit all have arm64 wheels for 3.12. Runtime deps at M0 are only numpy, pydantic, PyYAML; SciPy/scikit-learn/pandas are added when first needed (M1/M2) and the lock is regenerated then. Locked versions: see `constraints.txt`.

## ADR-007 — M0 additions to the status taxonomy and artifact policy

- **Date:** 2026-11-02
- **Status:** PROPOSED (needs owner approval)
- **Problem:** The taxonomy in docs/engineering/04_ARCHITECTURE.md had no code for a missing dataset, an invalid config or an unimplemented stage; M0 acceptance requires an explicit `DATASET_NOT_AVAILABLE` path. Also `.gitignore` blocked `results/*`, which conflicts with the required `results/M0.../validation_report.md`.
- **Decision:** Add `DATASET_NOT_AVAILABLE`, `INVALID_CONFIG`, `NOT_IMPLEMENTED` to `chemiproof.errors.StatusCode`; use directory name `results/M0_foundation/` and un-ignore only that directory.
- **Consequences:** No scientific methodology changed. Experiment configs must keep `status: NOT_RUN` (validator rejects anything else) so a hand edit cannot claim a finished run; `ui.allow_transductive_single_sample` must be `false` (ADR-002 enforced in code).
- **Owner signoff:** pending

## Future ADR template

```text
## ADR-NNN — Short title
Date:
Status: PROPOSED / ACCEPTED / REJECTED / SUPERSEDED
Problem:
Options and tradeoffs:
Decision:
Evidence / reference:
Reproducibility implications:
Owner signoff:
```

**Protocol-changing ADRs must be approved before locked final evaluation.**
