# Milestone M4: Evidence-based Handoff

**Date:** 2026-11-02 · **Milestone:** M4 Published-style optimal-transport replication · **Status:** REVIEW REQUIRED · **Owner reviewer:** Mia Ho
**Runs:** `M4_20261103T044749Z_7129cde_363deee6` (all 330) and `M4_20261103T044812Z_7129cde_44fba4b8` (Luhua-only) · full evidence: `results/M4_20261103T044749Z_7129cde_363deee6/validation_report.md`
**TRANSDUCTIVE RESEARCH MODE: needs a batch of unlabeled target spectra; never advertise as single-file deployment performance.**

## Scope actually delivered

- Tasks: CP-401..CP-405 (authors' method facts read and recorded; independent log-domain Sinkhorn + barycentric projection + SVR; five LOAO folds with no target labels in the API; discrepancy table; single-file refusal).
- Added: POT-called variant, published-style PCA-50/PCA-10 baselines, no-adaptation control, solver diagnostics (iterations, marginals, mass), label-shuffle canary for transductive runs, batch-size / single-brand / label-skew stress tests.
- Not implemented: abstention/intervals (M5), UI (M6).

## Scientific assumptions and protocol deviations

- Protocol LOAO-OT-v1 frozen before scoring (ADR-014, file hashes recorded and re-checked); stress test declared in ADR-015 before running; real-data OT tests added after the locked runs.
- Scoring unclipped (authors clip); clipped values are reported separately because the published PCA numbers only reproduce when clipped.
- Authors' code was read, not copied (no license). CORAL/MMD not reproduced (they tune with target labels).
- Owner approval required? yes (ADR-014, ADR-015).

## Executed verification

pytest not-dataset 158 passed (exit 0); pytest dataset 7 passed (exit 0); ruff clean; both locked runs exit 0 with `git dirty=False`; Sinkhorn converged in all 10 folds. T012, T013, T014, T015 PASS. GitHub Actions for the M2-M4 commits: NOT RUN (not pushed yet).

## Scientific results (measured; transductive unless stated)

All 330, macro over 5 held-out adulterants: ot_svr MAE 4.09 pp, R2 0.964; ot_svr_pot 4.09 pp / 0.965; no-adaptation control (inductive) 8.37 pp / 0.831. Luhua-only: ot_svr 3.13 pp / 0.977; control 0.859. The published means (raw 0.831, PCA 0.693, "PARAFAC" 0.659, OT-SVR 0.965) are reproduced within 0.001 (clipped scoring for the PCA columns). Published values are shown separately in the report and were not measured here as ours.
**Key caveat:** on label-skewed batches OT collapses (MAE about 22 pp, R2 -2.6 to -3.2 on average) while the no-adaptation control does not; with 10-spectrum batches OT is no better than no adaptation.

## Open blockers and adverse observations

1. The headline OT result holds only for batches with the same olive-fraction distribution as the source and enough spectra; nothing in the model detects a violating batch (this is the job of M5).
2. Published PCA-type baselines look acceptable only because predictions are clipped; unclipped they fail.
3. The authors' per-fold values and manuscript Methods were not retrieved; only means are compared.
4. One POT-variant fold (Luhua-only soybean) hit the iteration limit; flagged and reported.
5. Only five held-out systems, one instrument, laboratory mixtures.

## Recommendations and next action

- Decision requested: review ADR-014/015; confirm the wording that OT results are conditional on batch composition.
- Conditions before M4 may be ACCEPTED: owner review; green CI on the pushed commits.
- Suggested next milestone AFTER approval: M5 (abstention / uncertainty; should include a batch-composition risk flag).
