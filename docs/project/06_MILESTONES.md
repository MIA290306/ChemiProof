# Milestones & Stage-Gate Execution Plan

**Total target schedule:** approximately 12–18 weeks at 6–10 hours/week for a new Python user, with the main research benchmark complete by M4. Estimates are planning aids, not promises. A gate cannot pass without artifacts and owner review. **Sequence matters more than dates.**

## Milestone overview

| Milestone | Indicative span | Main deliverable | Gate / demonstration |
|---|---|---|---|
| **M0** Foundation | Week 1 | local repo, tooling, CLI design, sample fixtures, CI | lint/tests on clean machine |
| **M1** Source & Data Audit | Weeks 2–3 | official archive provenance, .dat parser, 330-row sample audit | verified counts, axes, target labels |
| **M2** Chemometric Baselines | Weeks 4–5 | preprocessing, source-only baselines, initial QC | scientific tests, basic metrics on valid split |
| **M3** Open-world Evaluation | Weeks 6–7 | five LOAO folds, group-aware internal tuning and locked reports | complete per-domain table, leakage audit |
| **M4** OT Replication | Weeks 8–10 | unlabeled-target-batch OT+SVR, method comparison | reproducible benchmark; explicit mode distinction |
| **M5** Trustworthiness Research | Weeks 11–13 | uncertainty/abstention, risk-coverage plots, robustness | empirical analysis including failures |
| **M6** Research Explorer | Weeks 14–15 | Streamlit UI, controlled upload, explainable report | realistic researcher walkthrough |
| **M6.5** Power BI Food Quality Intelligence (optional extension) | After M6; can overlap M7 drafting | validated BI export pipeline, data contract, four-page Power BI dashboard, KPI reconciliation | export tests pass on real runs; dashboard opened and verified in Power BI Desktop on Windows; every KPI reproduces from Python |
| **M7** Scientific Release | Weeks 16–18 | report, model card, reproducibility bundle, portfolio README | third-party rerun checklist and no overclaims |

## M0 — Foundation / Ready to Develop

**Scientific purpose:** make all later experiments inspectable and reproducible; do NOT build fake predictions.

**Tasks**
- [x] Create `pyproject.toml`, compatible Python interpreter/lock and `src/chemiproof` package with CLI placeholder.
- [x] Set up `ruff`, `pytest`, pre-commit and GitHub Actions for **synthetic data only** (type checker deferred; CI run NOT RUN yet).
- [x] Create `.gitignore` excluding external datasets, cache, weights, outputs containing proprietary/uncleared content, secrets.
- [x] Create `config/project.yaml`, `config/experiments/baseline.yaml`, validate CLI configuration before any training.
- [x] Implement deterministic synthetic EEM fixture with explicit wavelengths for parser/unit tests (not marketed as real data).
- [x] Add provenance/run ID helper, simple structured logging and standardized errors.
- [x] Set up empty pipeline stages and tests that fail meaningfully on missing dataset; do not fabricate passing scientific tests.
- [x] Read all docs and resolve any blocking ambiguities; write `docs/project/13_DECISION_LOG.md` entry.

**Artifacts:** `pyproject.toml`, lockfile, `src/`, `tests/`, `.github/workflows/ci.yml`, `results/M0.../validation_report.md`.

**Exit gate:** clean install works, `pytest` passes on synthetic fixtures, lint passes, CLI help and explicit `DATASET_NOT_AVAILABLE` path tested, docs match existing repo.

**Do not:** download data automatically in CI; implement complex model before parser.

## M1 — Dataset Provenance, Parsing and EEM QC

**Scientific purpose:** establish that labels and wavelengths match measurements before learning chemistry from numbers.

**Tasks**
- [x] Data obtained by owner as an extracted folder (no zip; ADR-009); permission review done (CC BY 4.0 dataset, unlicensed author code); safe ZIP inspection implemented and tested on synthetic malicious archives (real zip not available; MD5 NOT CHECKED).
- [x] Inspect representative actual `.dat` across oil groups, ratio directories, brands/rounds; document discovered columns/orientation.
- [x] Implement safe parser with actual schema, monotonic axes, stable ID, checksum, validation.
- [x] Generate manifest with `adulterant_type`, exact `olive_fraction`, `evoo_brand` only when grounded, replicate information, measurement round and evidence source.
- [x] Reconcile published totals (330 = 60/60/90/90/30, no discrepancy): soybean 60, peanut 60, rapeseed 90, corn 90, walnut 30; total 330.
- [x] Verify 10 concentration levels (10 levels x 3 rounds in every brand x adulterant cell; ledger empty) and 3 reps per valid brand×group×level; report any exceptions.
- [x] Inspect unexpected duplicates (0 duplicate hashes, 0 NaN/Inf, 0 constant; negatives in all files -> WARN), NaN/Inf, negative intensity, constant spectra, axis mismatch, file count deviations.
- [x] Plot at least 5 real (10 EEMs, `eem_examples.png`) spectra/EEM heatmaps with captions naming actual sample ID and units.
- [x] Test parser on malformed fixtures, archive traversal protection, wrong labels, corrupted .dat.

**Artifacts:** audit metadata + checksum; `data/interim/sample_manifest.csv`, QA report, EEM figure gallery, parser tests, licensing decision.

**Exit gate:** independently provable label mapping and axis convention; inventory discrepancies resolved/documented; scientific owner approves data map. **BLOCK if the olive/adulterant ratio direction remains ambiguous.**

## M2 — Preprocessing and First Models

**Scientific purpose:** produce simple **inductive** methods that establish a defensible floor for later OT.

**Tasks**
- [x] Build physically justified processing (author_v1: orientation, subtract-min baseline, SG along emission, max-norm; Rayleigh removal deliberately off, as in the reference): orientation, baseline correction, axis-wise Savitzky–Golay smoothing, intensity normalization.
- [x] Match published preprocessing (read-only from the unlicensed author code; ADR-011) from author code if accessible; version any alternative.
- [x] Implement source-only mean predictor and at least two baselines (raw SVR, PLS or source-only PCA+SVR).
- [x] Fit all learned transforms **inside** train-only pipeline; unit tests prevent leakage.
- [x] Include one synthetic benchmark and a real **source-internal** evaluation with MAE/RMSE/R²/bias.
- [x] Validate `y` scale (fraction; reference epsilon 0.1 fraction) and compare SVR epsilon against actual reference implementation.
- [x] Verify consistent feature length (9450) after parsing; visualize before/after spectra without overwriting raw data.

**Artifacts:** model implementations/tests, preprocessing notebook or script, source-only evaluation report, frozen config.

**Exit gate:** metrics from real data exported, leakage tests green, expected preprocessing changes documented, no target group leakage.

## M3 — Five-Domain LOAO Benchmark

**Scientific purpose:** answer whether known-adulterant models generalize to wholly unseen adulterant types.

**Tasks**
- [x] Deterministically produce exactly five outer folds by adulterant type (NOT random row-level split).
- [x] Within each source fold, choose parameters (inner leave-one-source-adulterant-out; separate calibration residuals are an M5 topic) by source-only inner pseudo-LOAO or justified method; separate calibration residuals.
- [x] Run baselines, export predictions and per-fold MAE, RMSE, R², bias, `n` and macro/pooled metrics.
- [x] Validate equal fold rules and sample-level disjointness; independent audit checks group memberships.
- [x] Analyze EVOO-brand composition (descriptive + Luhua-only sensitivity) and sensitivity/confounding.
- [x] Track all experiments (registry, locked/exploratory); freeze configs and generate `results/.../validation_report.md`.

**Artifacts:** split manifest, raw predictions, 5-fold table, model comparison plots, leakage audit.

**Exit gate:** all 5 folds reproducible without running on hidden test target labels during model selection; report worst fold and brand caveats.

## M4 — Published-style Optimal Transport Replication

**Scientific purpose:** evaluate how unlabeled target-batch adaptation changes unseen-adulterant regression.

**Tasks**
- [x] Review original authors' code and paper (read-only; ADR-011/014), record exact OT cost, normalization, regularization (`ε=0.1` cited), tolerance/iteration settings, projection and SVR label scale.
- [x] Implement or appropriately depend on OT solver (independent log-domain Sinkhorn; POT variant for cross-check) (e.g., Python Optimal Transport), log numerical convergence and transport mass checks.
- [x] Build source+unlabeled-target batch protocol (no target-label parameter anywhere; canary). Enforce prohibition on target y in training and tuning at API/test level.
- [x] Verify source barycentric projection semantics (source projected onto the target batch; target features untouched) and whether target feature representation is untouched (as in paper).
- [x] Run five LOAO comparisons (source-only control and published values, kept visibly separate), including source-only and author's reported benchmark (reference values visibly identified as external).
- [x] Provide discrepancies table and investigate baseline/reproduction mismatch systematically.
- [x] Add warning: transductive performance (report, summary, CLI errors) requires a batch and must not be advertised as one-file deployment.

**Artifacts:** OT runner, convergence log, per-fold comparison, reproduction notes, method diagram.

**Exit gate:** reproducible full five-fold OT experiment; no target labels touched until scoring; gap from published figures explained, even if not matched.

## M5 — Trustworthiness & Original Research Contribution

**Scientific purpose:** determine whether the model knows when estimates are likely unreliable.

**Tasks**
- [x] Preregister primary risk / uncertainty scoring rules before target results; source-trained OOD proxy and residual-based intervals.
- [x] Select abstention threshold via **source-only validation**. Never tune to outer test errors.
- [x] Run selective risk vs retention curves, compare random rejection baseline, report retained/rejected errors and worst-case folds.
- [x] Report empirical interval coverage per unseen adulterant; explicitly no theoretical target-shift coverage guarantee.
- [x] Conduct seeded spectral perturbation tests with justified magnitudes and full robustness table.
- [x] Review failure examples, confounding by brand, ablation of filtering/normalization, and whether effect is stable. *(done; brand effect described but not tested; effect NOT stable across folds)*
- [x] Write original-contribution claim conservatively: e.g., *an empirical audit of abstention and robustness on a published domain-shift benchmark*.

**Artifacts:** selective-risk plot, interval tables, stress-test figures, detailed error case studies, decisions documented.

**Exit gate:** results include unfavorable cases; at least one meaningful novel comparison and transparent limitations; no false confidence claims.

## M6 — Research Explorer & Export

**Scientific purpose:** make valid results inspectable and useful to scientists and future reviewers.

**Tasks**
- [x] Build streamlined Streamlit navigation described in `docs/product/08_UX_SPEC.md`.
- [x] Add `.dat` upload validation, EEM heatmap, QC messages and model selection by mode.
- [x] Single-file path calls **inductive only**; batch OT path demands >1 sample (>= 10, `MIN_TARGET_BATCH`) and explicitly explains dependencies/limitations.
- [x] Display decimal fraction and percent clearly, predictions or withheld estimate, optional **empirical** interval + warnings.
- [x] Link run ID/model card/methods, per-fold metrics and PDF/HTML/Markdown report export (choose least complex working export). *(Markdown)*
- [x] Handle malformed file, missing model and numeric failure without crash; no evidence of certification.
- [x] Check keyboard navigation, small screen and legibility; no fake testimonials or fabricated findings. *(keyboard section switching and 390 px layout checked; contrast/screen-reader audit NOT RUN)*

**Artifacts:** functioning local UI, UI tests, screenshots, walkthrough demo, export fixture.

**Exit gate:** reviewer can inspect genuine test-run artifacts, upload valid and invalid examples and see honest methodological labels.

## M6.5 — Power BI Food Quality Intelligence (extension; NOT STARTED)

**Scientific and product purpose:** give Food Science, QA/QC and laboratory readers a business-intelligence view of dataset quality, model performance, uncertainty and research findings, built **only** from validated experiment outputs. Power BI is a presentation layer; Python remains the only place where metrics, intervals and abstention are computed. This milestone neither renumbers nor changes M0–M7 and does not alter the scientific protocols.

**Specification documents:** `docs/bi/18_POWER_BI_SPEC.md` (dashboard, rules, environment), `docs/bi/19_POWER_BI_DATA_MODEL.md` (data contract, relationships, KPIs, DAX drafts), `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md` (tests BI001 to BI032, Definition of Done), `config/bi/export_contract.yaml`. Decision: ADR-016.

**Prerequisites:** M5 accepted (uncertainty/abstention outputs and their method metadata) and M6 accepted (shared artifact conventions). Task-level dependencies are listed below; data-quality work needs only M1, performance work only M3 and M4. M7 does **not** depend on M6.5 (ADR-016): if M6.5 is not accepted the release states "Power BI layer: not delivered".

**Environment limitation:** Power BI Desktop runs on Windows only. The development machine is macOS, so the dashboard cannot be built or validated there. If no Windows environment is available the dashboard tasks (CP-653 to CP-660) are recorded as `BLOCKED`, never as done. Python-side tasks (CP-651, CP-652, KPI recomputation in CP-654) run on macOS.

**Global rules for every task:** no fabricated results; no hard-coded metrics; no leakage; protocol, mode, model version and provenance on every number; published values kept separate; no raw data or `.pbix` committed; no claim that the dashboard is built or validated before its tests have evidence.

### Task CP-651: BI requirements and data-contract specification

- **Objective:** freeze what the dashboard needs and the exact tables, columns, units, relationships, protocol map and KPI definitions the exporter must provide.
- **Dependencies:** M3 and M4 accepted (artifact shapes are final); the M5 method-metadata fields agreed with the M5 owner (soft dependency, completes before CP-657).
- **Files to create or modify:** `docs/bi/18_POWER_BI_SPEC.md`, `docs/bi/19_POWER_BI_DATA_MODEL.md`, `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`, `config/bi/export_contract.yaml`, new `config/bi/protocol_map.yaml`, `docs/project/13_DECISION_LOG.md`.
- **Technical implementation requirements:** re-check every column against the real artifacts of the accepted runs; add the M5 uncertainty fields; protocol map entries with accepted `config_sha256`; contract versioned (`contract_version`); the YAML twin and the Markdown tables stay identical.
- **Expected deliverables:** approved contract (version 1.0.0), protocol map, KPI catalog with a Python recompute rule per KPI.
- **Acceptance criteria:** the contract covers all fields of the artifacts present; every KPI has a source and a recompute rule; no table can mix protocols without identifiers; owner approves the contract.
- **Verification procedure:** `pytest tests/unit/test_docs_consistency.py`; a review checklist signed by the owner; schema cross-check against `results/*/predictions.csv`, `metrics_by_fold.csv`, `summary.json`.
- **Definition of Done:** contract and protocol map merged, tests green, ADR updated, review recorded in `docs/project/14_PROGRESS_LOG.md`.

### Task CP-652: Validated model-output export pipeline

- **Objective:** a reproducible, validated `chemiproof export bi` that turns finished run directories into the contract tables (CSV, optional Parquet) with provenance.
- **Dependencies:** CP-651; M3, M4 and M5 outputs; M6 conventions.
- **Files to create or modify:** `src/chemiproof/bi/` (`contract.py`, `export.py`, `kpis.py`), `src/chemiproof/cli.py`, `src/chemiproof/errors.py` (BI status codes), `pyproject.toml` (optional extra `bi`), `constraints.txt`, `.gitignore` (`exports/bi/`), `tests/unit/test_bi_export.py`, `tests/integration/test_bi_export_real.py` (dataset marker), `docs/engineering/11_DEV_SETUP.md`.
- **Technical implementation requirements:** rules V-01 to V-12; read-only access to runs and dataset; deterministic output; refuse to overwrite; `uncertainty_available=false` and empty tables when M5 output is absent; protocol identity and provenance on every row; metrics reconciled from predictions; an `expected_kpis.json` written from Python for BI021; no intensity data in the export.
- **Expected deliverables:** the CLI, the test suite, one real export folder with `export_manifest.json`, a reconciliation report.
- **Acceptance criteria:** BI001 to BI014 PASS on synthetic fixtures and, where applicable, on the real runs (M2, M3, M4 and the M5 runs); export is byte-identical on rerun.
- **Verification procedure:** `pytest -q -m "not dataset"`, `pytest -q -m dataset`, `chemiproof export bi ...` twice and compare hashes, dataset hash before/after.
- **Definition of Done:** code, tests, documented commands, real-export evidence, docs updated, CI green, progress log updated.

### Task CP-653: Data model and relationships

- **Objective:** a Power BI semantic model that loads the export and implements the star-schema relationships of the contract.
- **Dependencies:** CP-652; a Windows machine with Power BI Desktop.
- **Files to create or modify:** `bi/powerbi/ChemiProofBI.pbip`, `bi/powerbi/ChemiProofBI.SemanticModel/` (TMDL), `bi/powerbi/README.md`, `docs/bi/19_POWER_BI_DATA_MODEL.md`.
- **Technical implementation requirements:** import mode from CSV/Parquet through the `ExportFolder` parameter; column types and formats as in the contract; the 22 relationships single-direction; no calculated tables; no auto date tables; key columns hidden; `contract_version` check query.
- **Expected deliverables:** the semantic model project files and a model-view screenshot from a real export.
- **Acceptance criteria:** BI020 PASS; wrong `contract_version` stops refresh with a visible error.
- **Verification procedure:** open the `.pbip` in Power BI Desktop, compare the model with `config/bi/export_contract.yaml` (TMDL diff), refresh.
- **Definition of Done:** model committed as text, BI020 evidence stored, Windows environment and Desktop version recorded.

### Task CP-654: DAX measures and KPI definitions

- **Objective:** implement the KPI catalog as measures that reproduce the Python values and refuse ambiguous selections.
- **Dependencies:** CP-653 and the `expected_kpis.json` from CP-652.
- **Files to create or modify:** measures in `bi/powerbi/ChemiProofBI.SemanticModel/`, `docs/bi/19_POWER_BI_DATA_MODEL.md` (final DAX), `tests/unit/test_bi_kpis.py`.
- **Technical implementation requirements:** the `m_RunGuardOK` guard; BLANK instead of zero on ambiguous or empty selections; pooled and macro metrics named separately; unclipped primary; no hard-coded numbers or invented thresholds; units in measure names.
- **Expected deliverables:** the measure set and a reconciliation table (Power BI value vs Python value).
- **Acceptance criteria:** BI021 and BI022 PASS for every headline run.
- **Verification procedure:** run the Python KPI script, compare with the report cards, test multi-run selections.
- **Definition of Done:** all KPIs reconcile, DAX documented, evidence recorded.

### Task CP-655: Dashboard Page 1, Dataset & Quality Overview

- **Objective:** the data-quality page described in `docs/bi/18_POWER_BI_SPEC.md` section 6.2.
- **Dependencies:** CP-654; M1 data (`dim_sample`, `fact_data_quality`, `fact_data_issues`).
- **Files to create or modify:** `bi/powerbi/ChemiProofBI.Report/` page definition.
- **Technical implementation requirements:** cards, observed-vs-expected bars, adulterant x brand x round matrix, concentration distribution, QC table, issues table with an explicit empty state; header strip and footer; published expectation captioned as such.
- **Expected deliverables:** the page and screenshots from a real export.
- **Acceptance criteria:** BI023 (page 1), BI025, BI029, BI030.
- **Verification procedure:** page checklist against section 6.2, KPI reconciliation of K01 to K08.
- **Definition of Done:** checklist complete, evidence stored, wording lint clean.

### Task CP-656: Dashboard Page 2, Machine Learning Performance

- **Objective:** the performance page of section 6.3 with the LOAO evaluation.
- **Dependencies:** CP-654; M3 and M4 runs.
- **Files to create or modify:** report page definition.
- **Technical implementation requirements:** MAE (pp), RMSE, bias, R2 with scope and scoring shown; actual-vs-predicted, residual plots, per-adulterant fold results, a by-experiment table with protocol, mode, run class and subset visible; transductive warning for OT runs; no chart mixing protocols.
- **Expected deliverables:** the page and screenshots.
- **Acceptance criteria:** BI023 (page 2), BI026, BI021 for K09 to K14.
- **Verification procedure:** checklist and reconciliation against the M3/M4 reports.
- **Definition of Done:** as CP-655.

### Task CP-657: Dashboard Page 3, Uncertainty & Screening Assessment

- **Objective:** the uncertainty page of section 6.4.
- **Dependencies:** CP-654; **M5 accepted** (hard). Without M5 only the empty-state version can be built and verified; the task is then not complete.
- **Files to create or modify:** report page definition.
- **Technical implementation requirements:** interval plot, observed coverage labeled empirical, abstention rate with retention, error-vs-coverage with the random-abstain control, "flagged for additional review" table, method card with interval method, nominal level, calibration protocol and threshold fitting source; standing caution text.
- **Expected deliverables:** the page and screenshots from a real M5 export.
- **Acceptance criteria:** BI023 (page 3), BI025, BI028, K15 to K19 reconcile.
- **Verification procedure:** checklist; confirm every threshold in the report was fitted on source data only according to the M5 artifacts.
- **Definition of Done:** as CP-655, plus the owner confirms the wording.

### Task CP-658: Dashboard Page 4, Scientific Research Insights

- **Objective:** the research page of section 6.5.
- **Dependencies:** CP-654 and CP-656; M4; M5 for OOD and perturbation robustness.
- **Files to create or modify:** report page definition.
- **Technical implementation requirements:** baseline comparison inside one protocol, separate transductive panel with the warning and the no-adaptation control, condition comparison (all samples vs one brand), brand view, robustness and negative-control charts, OT diagnostics, OOD view only if M5 provides it, published-reference panel, findings and limitations fed from artifacts.
- **Expected deliverables:** the page and screenshots.
- **Acceptance criteria:** BI023 (page 4), BI026, K20 and K21 reconcile.
- **Verification procedure:** checklist; confirm that no published number shares a series with a measured value.
- **Definition of Done:** as CP-655.

### Task CP-659: Data refresh and reproducibility

- **Objective:** a refresh procedure that a second person can follow to get the same KPIs.
- **Dependencies:** CP-655 to CP-658.
- **Files to create or modify:** `bi/powerbi/README.md`, `docs/engineering/11_DEV_SETUP.md`, optional helper script for KPI reconciliation.
- **Technical implementation requirements:** documented `ExportFolder` parameter, export-manifest hash check, contract-version guard, versioned immutable exports, no gateway or cloud refresh assumed.
- **Expected deliverables:** the README procedure and one successful refresh log.
- **Acceptance criteria:** BI027 and BI032 PASS.
- **Verification procedure:** a reviewer follows the README on a clean Windows machine.
- **Definition of Done:** reviewer log stored, limitations documented.

### Task CP-660: Dashboard testing, documentation and portfolio presentation

- **Objective:** complete the verification, documentation and honest presentation.
- **Dependencies:** CP-659.
- **Files to create or modify:** `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md` (results), `README.md` (BI section with real screenshots), `docs/project/14_PROGRESS_LOG.md`, a milestone review from `templates/MILESTONE_REVIEW.md`, `docs/project/15_RELEASE_AND_RESEARCH_REPORT.md`.
- **Technical implementation requirements:** run every test of `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`; screenshots only from real exports; state the Windows/Desktop version, export id and commit; list known limitations.
- **Expected deliverables:** test evidence table, milestone review, portfolio section.
- **Acceptance criteria:** the Definition of Done of `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md` section 4.
- **Verification procedure:** owner review of the evidence; independent reviewer run (BI032).
- **Definition of Done:** all required tests PASS with evidence, docs and README updated, no overclaim, owner sets `ACCEPTED`.

**Exit gate:** reproducible export with passing tests on real runs; Power BI project opened and verified on Windows; all KPIs reconcile with Python; four pages meet the checklists; no unsupported claim. **Do not** start building the dashboard before M5 and M6 are accepted, unless the owner explicitly changes the scope for the data-quality and performance pages (CP-655, CP-656).

## M7 — Reproducible Public Portfolio Release

**Scientific purpose:** demonstrate a standalone, scientifically responsible project.

**Tasks**
- [ ] Freeze final evaluation; run reproducibility checks on new environment.
- [ ] Produce 4–8 page research report using `templates/RESEARCH_REPORT.md`; create model card and data card.
- [ ] Add actual results, source attribution, reproducibility command and clear screenshots to README.
- [ ] Decide code/data license after checking original rights. Never automatically mirror original dataset or author's repository.
- [ ] Have at least one external reviewer (scientific instructor/mentor/QA practitioner if available) review methods and claims.
- [ ] Fix blocking bugs; tag release only when package/test/docs/UI checks pass.

**Artifacts:** report, reproducibility appendix, model card, GitHub release, tagged code, research poster or 90-second demo.

**Exit gate:** honest public claim supported by archived experiment artifacts; no unknown legal permissions or misleading metrics.

## Stage-gate stop rules

- **Gate blocked** if original source rights unknown and agent wants to redistribute data/code.
- **Gate blocked** if label direction, group assignment or axes cannot be verified.
- **Gate blocked** if test labels influence any fitted model or threshold.
- **Gate blocked** if single-file UI displays OT-transductive results as if independently deployable.
- **Gate blocked** if all tests “pass” only because the dataset was mocked when real science results were required.
- **Gate blocked** if provenance missing for benchmark numbers.

## Reporting discipline

Each milestone handoff: `scope implemented`, `files changed`, `exact commands/results`, `real artifacts`, `numerical metrics if and only if measured`, `deviations`, `known risks`, `decision needed`, `next milestone`. Update progress log only after pass/fail evidence. **Owner approval required to change milestone status to ACCEPTED.**
