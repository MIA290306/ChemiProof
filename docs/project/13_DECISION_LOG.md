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
- **Status:** PROPOSED (resolve at M0)
- **Decision proposal:** Python + NumPy/Pandas/SciPy/scikit-learn, Pytest/Ruff, POT only in M4, Streamlit in M6. No backend/auth/LLM services.
- **Why:** Appropriate to single-user reproducible scientific research.
- **To decide:** Actual interpreter/package versions and environment manager after checking supported stable releases.

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
