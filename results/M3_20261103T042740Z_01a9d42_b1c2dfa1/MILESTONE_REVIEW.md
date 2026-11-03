# Milestone M3: Evidence-based Handoff

**Date:** 2026-11-02 · **Milestone:** M3 Five-domain LOAO benchmark · **Status:** REVIEW REQUIRED · **Owner reviewer:** Mia Ho
**Runs:** `M3_20261103T042740Z_01a9d42_b1c2dfa1` (all 330) and `M3_20261103T042759Z_01a9d42_2fbd19b6` (Luhua-only) · full evidence: `results/M3_20261103T042740Z_01a9d42_b1c2dfa1/validation_report.md`

## Scope actually delivered

- Tasks: CP-301..CP-305 (deterministic five LOAO folds with independent audit; nested source-only inner leave-one-source-adulterant-out tuning; baselines with per-fold + macro + pooled metrics; brand-imbalance analysis and Luhua-only sensitivity; frozen protocol, registry, reproducibility checks).
- Added: label-shuffle canary after every LOAO run, permuted-source-label negative control, run registry with locked/exploratory classes and a clean-tree guard.
- Not implemented: OT (M4), abstention/intervals (M5), UI (M6). The brand analysis is descriptive; no brand-blocked training was added.

## Scientific assumptions and protocol deviations

- Protocol LOAO-v1 frozen before scoring (ADR-013, file hashes recorded); two locked runs only; no tuning after seeing held-out scores.
- Scoring is unclipped (reference clips to [0,1]); clipped values are reported separately.
- Owner approval required? yes (ADR-013).

## Executed verification

pytest not-dataset 140 passed (exit 0); pytest dataset 6 passed (exit 0); ruff clean; both locked runs exit 0 with `git dirty=False`; control runs exit 0. T008, T010, T011, T024 PASS. GitHub Actions for M2/M3 commits: NOT RUN (not pushed yet).

## Scientific results (measured; held-out adulterant, inductive)

All 330 samples, macro over 5 folds: mean_y MAE 22.73 pp / R2 -0.000; svr_raw 8.37 pp / 0.831; pca_svr 16.55 pp / 0.019; pls 6.50 pp / 0.903. Luhua-only: svr_raw 6.95 pp / 0.859; pls 8.64 pp / 0.828; pca_svr 0.301. Worst folds: svr_raw rapeseed (R2 0.601); pls soybean (MAE 10.75 pp). Published reference values are shown separately in the report and were not measured here; our svr_raw macro R2 equals the published raw 0.831.

## Open blockers and adverse observations

1. pca_svr fails badly (macro R2 0.019); cause not investigated, protocol frozen.
2. Model ranking flips between all-330 and Luhua-only; only 5 folds.
3. Brand and adulterant are confounded; soybean/OliVera is a clearly hard cell.
4. `pytest -m dataset` executes the LOAO pipeline on real data (outputs discarded; disclosed in ADR-013).
5. The second control run's registry line shows `git_dirty=True` because the (then tracked) registry file counted as a change; fixed afterwards by excluding the registry from the dirty check (test added).

## Recommendations and next action

- Decision requested: review ADR-013 and the report; confirm that pca_svr's failure should stand as a reported negative result.
- Conditions before M3 may be ACCEPTED: owner review; green CI on the pushed commits.
- Suggested next milestone AFTER approval: M4 (OT replication, transductive mode, clearly separated from these inductive numbers).
