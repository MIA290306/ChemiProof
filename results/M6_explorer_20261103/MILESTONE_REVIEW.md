# Milestone M6 — Evidence-based Handoff

**Date:** 2026-11-03  
**Milestone:** M6 Research Explorer & Export  
**Status:** REVIEW REQUIRED (agent cannot self-approve ACCEPTED)  
**Owner reviewer:** Mia Ho

## Scope actually delivered

- Tasks: Streamlit navigation per `08_UX_SPEC`; `.dat` upload validation, heatmap, QC messages, mode-separated model paths; single-file inductive only, batch OT opt-in with >= 10 files; fraction + percent display, withheld estimate, empirical interval; run id / model card / per-fold metrics and Markdown report export; malformed file, missing model and non-convergence handled without crash; keyboard and small-screen check.
- Behaviour: see `validation_report.md`.
- Not implemented: PDF/HTML export (Markdown chosen as least complex); transformed-spectrum download; contrast / screen-reader audit.

## Scientific assumptions and protocol deviations

- Spec expectation: a validated inductive artifact for single-file screening.
- Actual method: `FINAL-PLS-v1` (ADR-018) trained on all 330 spectra, so it has no independent test; evidence is LOAO-v1 for the procedure (optimistic, selected post hoc). OOD flag withholds although it did not meet the M5 usefulness rule.
- Owner approval required? **yes** (ADR-018, delegated decision).

## Files and artifacts

| Path | Purpose | SHA/Run ID |
|---|---|---|
| `src/chemiproof/modeling/final.py` | artifact train/save/load | commit on `m6/research-explorer` |
| `src/chemiproof/pipeline.py` | `screen_single`, `screen_batch` | same |
| `src/chemiproof/ui/{app,artifacts}.py` | explorer | same |
| `results/M6_final_20261103T074605Z_ce2423b_82b39d6c/model_card.json` | model card (npz git-ignored) | npz `bbcff343...` |
| `results/M6_explorer_20261103/validation_report.md` | evidence | - |

## Executed verification — not just expectations

| Command / test ID | Exit code | Measured result or diagnostic | PASS/FAIL/NOT RUN |
|---|---|---|---|
| `pytest -q -m "not dataset"` | 0 | 221 passed | PASS |
| `pytest -q -m dataset` | 0 | 9 passed | PASS |
| `ruff check .`, `ruff format --check .` | 0 | clean | PASS |
| T013, T019, T020, T023 | - | see validation report | PASS |
| Contrast / screen reader | - | - | NOT RUN |

## Scientific results (if any)

- NO NEW EXPERIMENTAL RESULTS. The explorer displays the existing M3-M5 runs. The final model has no test metric; the selection score (5.61 pp inner CV) is not a test.

## Open blockers and adverse observations

1. M0-M5 and every delegated ADR still await owner review (owner chose to continue without it).
2. The batch path is unevaluated and fragile to batch composition.

## Recommendations and next action

- Decision requested from owner: review ADR-018 and this milestone.
- Conditions before M6 may be ACCEPTED: owner opens the app (`chemiproof model train-final`, then `chemiproof app`) and checks the walkthrough.
- Suggested next milestone: M7 (release); M6.5 needs a Windows machine.
