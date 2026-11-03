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
- [ ] Review original authors' code and paper, record exact OT cost, normalization, regularization (`ε=0.1` cited), tolerance/iteration settings, projection and SVR label scale.
- [ ] Implement or appropriately depend on OT solver (e.g., Python Optimal Transport), log numerical convergence and transport mass checks.
- [ ] Build source+unlabeled-target batch protocol. Enforce prohibition on target y in training and tuning at API/test level.
- [ ] Verify source barycentric projection semantics and whether target feature representation is untouched (as in paper).
- [ ] Run five LOAO comparisons, including source-only and author's reported benchmark (reference values visibly identified as external).
- [ ] Provide discrepancies table and investigate baseline/reproduction mismatch systematically.
- [ ] Add warning: transductive performance requires a batch and must not be advertised as one-file deployment.

**Artifacts:** OT runner, convergence log, per-fold comparison, reproduction notes, method diagram.

**Exit gate:** reproducible full five-fold OT experiment; no target labels touched until scoring; gap from published figures explained, even if not matched.

## M5 — Trustworthiness & Original Research Contribution

**Scientific purpose:** determine whether the model knows when estimates are likely unreliable.

**Tasks**
- [ ] Preregister primary risk / uncertainty scoring rules before target results; source-trained OOD proxy and residual-based intervals.
- [ ] Select abstention threshold via **source-only validation**. Never tune to outer test errors.
- [ ] Run selective risk vs retention curves, compare random rejection baseline, report retained/rejected errors and worst-case folds.
- [ ] Report empirical interval coverage per unseen adulterant; explicitly no theoretical target-shift coverage guarantee.
- [ ] Conduct seeded spectral perturbation tests with justified magnitudes and full robustness table.
- [ ] Review failure examples, confounding by brand, ablation of filtering/normalization, and whether effect is stable.
- [ ] Write original-contribution claim conservatively: e.g., *an empirical audit of abstention and robustness on a published domain-shift benchmark*.

**Artifacts:** selective-risk plot, interval tables, stress-test figures, detailed error case studies, decisions documented.

**Exit gate:** results include unfavorable cases; at least one meaningful novel comparison and transparent limitations; no false confidence claims.

## M6 — Research Explorer & Export

**Scientific purpose:** make valid results inspectable and useful to scientists and future reviewers.

**Tasks**
- [ ] Build streamlined Streamlit navigation described in `docs/product/08_UX_SPEC.md`.
- [ ] Add `.dat` upload validation, EEM heatmap, QC messages and model selection by mode.
- [ ] Single-file path calls **inductive only**; batch OT path demands >1 sample and explicitly explains dependencies/limitations.
- [ ] Display decimal fraction and percent clearly, predictions or withheld estimate, optional **empirical** interval + warnings.
- [ ] Link run ID/model card/methods, per-fold metrics and PDF/HTML/Markdown report export (choose least complex working export).
- [ ] Handle malformed file, missing model and numeric failure without crash; no evidence of certification.
- [ ] Check keyboard navigation, small screen and legibility; no fake testimonials or fabricated findings.

**Artifacts:** functioning local UI, UI tests, screenshots, walkthrough demo, export fixture.

**Exit gate:** reviewer can inspect genuine test-run artifacts, upload valid and invalid examples and see honest methodological labels.

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
