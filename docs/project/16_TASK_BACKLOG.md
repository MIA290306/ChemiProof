# AI Coding Task Backlog — bite-sized, dependency-aware work orders

**Read first:** `CLAUDE.md`. Task status lives in `docs/project/14_PROGRESS_LOG.md`; M5-M7 and M6.5 (CP-651 to CP-660, full cards in `docs/project/06_MILESTONES.md`) are NOT STARTED. This backlog turns stage goals into reviewable tasks. The agent implements tasks **within** the active milestone, not all at once. Use task IDs in commits/reviews.

| Task ID | Milestone | Task | Dependencies | Evidence to submit |
|---|---|---|---|---|
| CP-001 | M0 | Choose Python version / env manager and record supported package versions | None | ADR update, install log |
| CP-002 | M0 | Create installable `src/` package, CLI with `--help` and truthful unavailable commands | CP-001 | CLI output, tests |
| CP-003 | M0 | Add config loader with validation and explicit defaults; disallow unknown model mode | CP-002 | config tests |
| CP-004 | M0 | Generate synthetic 35×270 EEM fixtures + wavelength axes | CP-002 | deterministic unit tests |
| CP-005 | M0 | Set up lint/test CI, pre-commit and repository guard against raw data | CP-002 | CI report / passing command |
| CP-006 | M0 | Create results provenance helper (seed/config/data hash/git SHA) | CP-003 | example artifact from synthetic fixture |
| CP-101 | M1 | Official Zenodo source verification, checksum and rights review | CP-005 | source registry, digest |
| CP-102 | M1 | Safely inspect ZIP hierarchy and sample .dat layout across five groups | CP-101 | inspection report with examples |
| CP-103 | M1 | Implement `.dat` parser for **observed** native schema and explicit axes | CP-102 | parser tests |
| CP-104 | M1 | Parse ratio tokens into olive-volume fraction with independently verified direction | CP-102 | positive and negative cases |
| CP-105 | M1 | Produce 330-record manifest / 60-60-90-90-30 audit and brand cross-tab | CP-103,CP-104 | actual CSV + QC report |
| CP-106 | M1 | Write real EEM heatmaps and record QC anomalies | CP-105 | labeled plots with hashes |
| CP-107 | M1 | Test corrupted ZIP/.dat, duplicate hashes, invalid axes and mislabel conditions | CP-103 | test log |
| CP-201 | M2 | Implement orientation/baseline/smoothing/intensity normalization stages | CP-105 | science tests and transformations report |
| CP-202 | M2 | Fit train-only scaler and optional PCA with pipeline abstraction | CP-201 | no-leakage tests |
| CP-203 | M2 | Implement mean, raw SVR, PCA-SVR and optional PLS baselines | CP-202 | real source-validation scores |
| CP-204 | M2 | Verify target scale against author's reference settings / epsilon | CP-203 | method note and ADR |
| CP-205 | M2 | Build metrics+experiment runner with config/hashes | CP-203 | saved predictions and metrics |
| CP-301 | M3 | Implement immutable five-domain LOAO manifest | CP-105 | splits + disjointness tests |
| CP-302 | M3 | Implement nested source-only inner group selection and calibration partition | CP-301 | tune log + label leakage tests |
| CP-303 | M3 | Run full baseline cross-domain matrix and macro/pooled metrics | CP-302,CP-205 | all five fold score files |
| CP-304 | M3 | Inspect EVOO brand imbalance and worst-case adulterant | CP-303 | descriptive plots and limitations |
| CP-305 | M3 | Lock protocol ID, frozen configs and reproducibility run | CP-304 | reproduction log |
| CP-401 | M4 | Inspect paper/author OT code and document exact values/conventions | CP-305 | method replication note |
| CP-402 | M4 | Implement Sinkhorn OT and barycentric projected source features | CP-401 | numerical tests / convergence logs |
| CP-403 | M4 | Run five transductive LOAO folds without target y access | CP-402 | real metrics and leakage tests |
| CP-404 | M4 | Compare with reference author results; report discrepancies, label mode | CP-403 | sourced comparison table |
| CP-405 | M4 | Enforce single-file API rejection of transductive model | CP-403 | mode mismatch tests |
| CP-501 | M5 | Preregister rule for OOD/abstention on source inner folds | CP-404 | protocol version + ADR |
| CP-502 | M5 | Implement interval calibration with explicit exchangeability caveat | CP-501 | observed interval coverage metrics |
| CP-503 | M5 | Calculate selective-risk vs retention curves and random reject control | CP-501 | figures + per-fold CSV |
| CP-504 | M5 | Run synthetic perturbation stress matrix and negative tests | CP-503 | declared perturbation table and results |
| CP-505 | M5 | Review failure cases, abstention failures and genuine novel claim | CP-504 | empirical limitations report |
| CP-601 | M6 | Build read-only benchmark/data pages in Streamlit | CP-505 | interactive screenshots |
| CP-602 | M6 | Build valid/invalid EEM explorer and source-only single screening | CP-601 | upload+error tests |
| CP-603 | M6 | Build explicit transductive batch research mode with guardrails | CP-602 | batch workflow demo |
| CP-604 | M6 | Add provenance export, accessible status wording and mode docs | CP-603 | export check and walkthrough |
| CP-651 | M6.5 | BI requirements and data-contract specification (contract v1.0.0, protocol map, KPI catalog) | M3, M4 accepted; M5 metadata fields agreed | approved `config/bi/export_contract.yaml`, protocol map, consistency test |
| CP-652 | M6.5 | Validated `chemiproof export bi` pipeline (CSV, optional Parquet, reconciliation, provenance) | CP-651, M3-M5, M6 | tests BI001-BI014 PASS, real export with manifest |
| CP-653 | M6.5 | Power BI semantic model and relationships (`.pbip`, TMDL) on Windows | CP-652, Windows + Power BI Desktop | model view, TMDL diff, BI020 |
| CP-654 | M6.5 | DAX measures and KPI definitions with run guard | CP-653 | reconciliation table, BI021, BI022 |
| CP-655 | M6.5 | Dashboard Page 1: Dataset and Quality Overview | CP-654, M1 | page checklist, BI023/BI025 |
| CP-656 | M6.5 | Dashboard Page 2: Machine Learning Performance | CP-654, M3, M4 | page checklist, BI023/BI026 |
| CP-657 | M6.5 | Dashboard Page 3: Uncertainty and Screening Assessment | CP-654, M5 (hard) | page checklist, BI023/BI028 |
| CP-658 | M6.5 | Dashboard Page 4: Scientific Research Insights | CP-654, CP-656, M4, M5 | page checklist, BI023/BI026 |
| CP-659 | M6.5 | Data refresh and reproducibility procedure | CP-655-CP-658 | README procedure, BI027, BI032 |
| CP-660 | M6.5 | Dashboard testing, documentation and portfolio presentation | CP-659 | evidence table, milestone review |
| CP-701 | M7 | Clean-environment reproduce all five folds with locked configs | CP-604 | commands/hashes and equality analysis |
| CP-702 | M7 | Write short research report and model/data cards | CP-701 | evidence-based reports |
| CP-703 | M7 | Licenses, citations, raw-data redaction and scientific third-party review | CP-702 | review checklist |
| CP-704 | M7 | Publish a portfolio-ready README/demo and tag release after signoff | CP-703 | release artifacts and URL |

## Work-order checklist (apply to every CP task)

- [ ] Confirm current milestone is active and dependencies accepted.
- [ ] State scientific assumption / boundary changed by task.
- [ ] Make code change with explicit input/output contract.
- [ ] Add positive and negative tests; do not depend on internet for unit tests.
- [ ] Run the test commands; cite outputs and numerical units.
- [ ] Update docs if method/config changed.
- [ ] Record artifacts, source/hashes, limitations and review outcome.
- [ ] Stop after a task review if a scientific blocking issue appears.

## Priority rule

Within milestone: scientific correctness + data provenance + leak prevention > performance > UX > cosmetic polish. A pipeline with R²=0.85 and trustworthy methods is stronger than R²=0.99 produced with contaminated test data.
