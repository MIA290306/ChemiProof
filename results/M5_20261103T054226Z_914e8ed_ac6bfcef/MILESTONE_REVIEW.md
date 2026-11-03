# Milestone M5: Evidence-based Handoff

**Date:** 2026-11-03 · **Milestone:** M5 Trustworthiness (abstention, intervals, robustness) · **Status:** REVIEW REQUIRED · **Owner reviewer:** Mia Ho
**Run:** `M5_20261103T054226Z_914e8ed_ac6bfcef` · full evidence: `validation_report.md` in the same folder · INDUCTIVE mode · protocol LOAO-UQ-v1 (ADR-017)

## Scope actually delivered
- Preregistration (ADR-017) before scoring; `src/chemiproof/uncertainty/` (Mahalanobis OOD score, model disagreement, cross-fitted source calibration, intervals, retention thresholds, selective-risk curves with random-rejection and diagnostic oracle, perturbations); CLI `chemiproof experiment uncertainty`; tests; one locked run; CSV tables, plots, report.
- Not implemented: OT abstention (transductive), Luhua-only M5 run, brand-effect test, UI (M6).

## Scientific assumptions and deviations
- Design written after M3/M4 outer errors were seen; constants fixed, nothing tuned (disclosed in ADR-017). Calibration residuals slightly optimistic (outer hyper-parameters chosen with the calibration adulterants in the inner CV). Owner approval needed for ADR-017: yes.

## Executed verification
Locked run exit 0 with `dirty=False`; label-shuffle canary passed in all 5 folds; `pytest -m dataset -k m5` exit 0; unit/synthetic tests passed before the run; ruff clean. T011, T016, T017, T018 PASS.

## Measured results (macro over 5 held-out adulterants)
Best point model PLS: 6.50 pp full MAE; abstention with `ood_maha` at goal 0.80 gives 6.22 pp (observed retention 0.83): only 3/5 folds improve. Usefulness rule met by 1 of 6 model/score pairs (`pca_svr`/`model_disagreement`, weak model). Pooled 90 % intervals: observed coverage 0.47-1.00 depending on system (PLS soybean 0.65); the `max_domain` variant is 45 pp wide. Offset/scale invariance measured (max feature change 6.7e-16); noise at 1 % of max raises PLS MAE to 17.7 pp and `ood_maha` abstention to 57 %.

## Open blockers and adverse observations
1. Abstention and intervals do not provide dependable reliability on this benchmark; reported as unfavourable.
2. Score-error rank correlation flips sign between held-out systems.
3. Strongest errors cluster in soybean-olivera; brand/batch effect untested.
4. OT batch-composition hazard (ADR-015) still has no detector.
5. Five systems, one instrument, laboratory mixtures.

## Recommendations and next action
- Decision requested: review ADR-017 and the conservative claim: "an empirical audit of abstention and robustness on a published domain-shift benchmark, with largely negative findings for label-free scores".
- Next milestone after approval: M6 (research UI) showing these limits; OT batch-composition detector and brand-effect test are candidate follow-ups (new ADRs).
