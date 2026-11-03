# Milestone M2: Evidence-based Handoff

**Date:** 2026-11-02 · **Milestone:** M2 Preprocessing and first models · **Status:** REVIEW REQUIRED · **Owner reviewer:** Mia Ho
**Run ID:** `20261103T041143Z_ca43062_4097e86f` · full evidence: `results/M2_20261103T041143Z_ca43062_4097e86f/validation_report.md`

## Scope actually delivered

- Tasks: CP-201..CP-205 (prespecified `author_v1` preprocessing; train-only learned transforms; mean/SVR/PCA-SVR/PLS baselines; verified target scale and reference SVR epsilon; metrics + experiment runner with provenance artifacts).
- New CLI: `experiment run` (protocol `source_internal_loro`), `spectra compare`.
- Not implemented: LOAO outer folds (M3), OT (M4), abstention/intervals (M5), UI (M6).

## Scientific assumptions and protocol deviations

- Spec: "match published preprocessing from author code": done by reading the unlicensed code (not copying) and recording facts in ADR-011. Paper text says smoothing on both axes; code smooths emission only; we follow the code (documented).
- M2 evaluation is leave-one-round-out (optimistic, same adulterants in train), chosen so that no LOAO target label is consumed before M3.
- Grids widened after the first run (ADR-012), inner-CV only.
- Owner approval required? yes (ADR-011, ADR-012).

## Files and artifacts

| Path | Purpose | Run ID |
|---|---|---|
| `src/chemiproof/spectra/preprocess.py` | author_v1 | n/a |
| `src/chemiproof/modeling/baselines.py` | models | n/a |
| `src/chemiproof/evaluation/{metrics,protocols,runner}.py`, `experiments.py` | evaluation | n/a |
| `config/experiments/m2_source_internal.yaml` | frozen M2 config | sha256 `5ddb4697c349f887...` |
| `results/M2_20261103T041143Z_ca43062_4097e86f/predictions.csv, metrics_by_fold.csv, summary.json, splits.csv, config_resolved.yaml, environment.json, git_state.json` | results | `20261103T041143Z_ca43062_4097e86f` |

## Executed verification

pytest (all) exit 0, 124 passed; ruff exit 0; run exit 0 with `git dirty=false`. T007, T008, T009, T011, T024 PASS. GitHub Actions for these commits: NOT RUN.

## Scientific results (if any)

Source-internal (optimistic) macro over 3 rounds: mean_y 22.73 pp (R2 0.000); svr_raw 5.10 pp (R2 0.947); pca_svr 7.09 pp (R2 0.903); pls 1.37 pp (R2 0.996). Not unseen-adulterant evidence. Paper reference values: not used here.

## Open blockers and adverse observations

1. Scores are exploratory-development numbers (ADR-012); M3 must freeze before scoring.
2. PCA-SVR underperforms raw SVR; unexplained.
3. Round-as-replicate unproven; brand confounding.

## Recommendations and next action

- Decision requested: review ADR-011/012; confirm the unlicensed-code policy (read-only) is acceptable.
- Conditions before M2 may be ACCEPTED: owner review; green CI on pushed commits.
- Suggested next milestone AFTER approval: M3 (five LOAO outer folds, frozen protocol).
