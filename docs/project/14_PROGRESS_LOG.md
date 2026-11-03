# Milestone Progress / Evidence Ledger

**Updated:** 2026-11-03  
**Current overall state:** M0-M5 REVIEW REQUIRED; measured inductive, transductive (OT) and abstention/interval/robustness results exist; OT is conditional on batch composition; label-free abstention and source-calibrated intervals are NOT reliably useful on this benchmark; no UI yet.  
**Rule:** Agent may set `REVIEW REQUIRED`; **only owner** may mark `ACCEPTED` after evidence review.

| Milestone | Status | Evidence / artifacts | Next action |
|---|---|---|---|
| M0 Foundations | REVIEW REQUIRED | `results/M0_foundation/validation_report.md`, `MILESTONE_REVIEW.md`; 41 tests pass locally and in CI | Owner review and ADR-007 approval (CI green: run 41572684248) |
| M1 Dataset audit | REVIEW REQUIRED | `results/M1_20261103T034431Z_b050b36-dirty_33c0ba5b/` (validation_report, MILESTONE_REVIEW); 330/330 parsed, ledger empty; 93 tests | Owner review (CI green: run 41574366884) |
| M2 Chemometric baselines | REVIEW REQUIRED | `results/M2_20261103T041143Z_ca43062_4097e86f/` (validation_report, MILESTONE_REVIEW); 124 tests; source-internal results exported | Owner review (CI green: run 41581270090) |
| M3 LOAO benchmark | REVIEW REQUIRED | `results/M3_20261103T042740Z_01a9d42_b1c2dfa1/` (validation_report, MILESTONE_REVIEW); two locked runs + controls | Owner review (CI green: run 41581270090) |
| M4 OT replication | REVIEW REQUIRED | `results/M4_20261103T044749Z_7129cde_363deee6/` (validation_report, MILESTONE_REVIEW); two locked runs + stress tests | Owner review (CI green: run 41581270090) |
| M5 Abstention/robustness | REVIEW REQUIRED | `results/M5_20261103T054226Z_914e8ed_ac6bfcef/` (validation_report, MILESTONE_REVIEW); one locked run, largely unfavourable findings | Owner review of ADR-017 and results |
| M6 Research UI | NOT STARTED | UX spec only | Await validated artifact |
| M6.5 Power BI quality-analytics layer (optional extension) | NOT STARTED | Specification only: `docs/bi/18_POWER_BI_SPEC.md`, `19_POWER_BI_DATA_MODEL.md`, `20_POWER_BI_ACCEPTANCE_TESTS.md`, `config/bi/export_contract.yaml`; no export code, no Power BI file | Await M5 and M6 acceptance and a Windows environment |
| M7 Release | NOT STARTED | Templates only | Await M6 acceptance |

## Current blockers / unknowns

1. `.dat` actual internal schema, wavelength grid orientation, exact filename-to-label mapping unverified.
2. Data Zenodo license not yet verified from an explicit machine-readable rights field; source GitHub code license not checked.
3. Local environment and 41 synthetic-fixture tests now exist (M0); GitHub Actions `ci` passed on c1e8a98.
4. No ChemiProof benchmark results, UI or proof of model generalization exist.

## Agent update format (append; do not overwrite history)

```text
### YYYY-MM-DD — Mx — STATUS
Owner / agent:
Scope attempted:
Files changed:
Actual commands + exit codes:
Measured results (with units; if none say NONE):
Artifact paths + checksums:
Acceptance tests (IDs / PASS, FAIL, NOT RUN):
Risks / open questions:
Owner signoff:
Next milestone (only after ACCEPTED):
```

### 2026-11-02 — Docs reorganization (no milestone change) — DONE
Owner / agent: Claude Code
Scope attempted: group markdown docs by purpose; fix all cross-references. No scientific content edited.
Files changed: moved `docs/NN_*.md` into `docs/{product,science,engineering,project,vi}/`; moved `START_HERE_VI.md`, `ROADMAP_VI.md` to `docs/vi/`; rewrote `docs/00_DOCS_INDEX.md`; updated path references in `CLAUDE.md`, `README.md`, `AGENTS.md`-adjacent docs, prompts, READMEs, `config/milestones.yaml`.
Actual commands + exit codes: mv/sed batch, link-existence check over all `docs|templates|config` paths: no missing targets.
Measured results: NONE (documentation only). Milestone statuses unchanged (M0 still NOT STARTED).
Risks / open questions: prompts in `docs/engineering/12_AI_PROMPTS.md` now say "the docs numbered 02,05" instead of "docs/02,05".
Owner signoff: pending

### 2026-11-02 — M0 — REVIEW REQUIRED
Owner / agent: Mia Ho / Claude Code
Scope attempted: CP-001..CP-006 (package, CLI, config validation, synthetic EEM, lint/test/CI, provenance helper).
Files changed: `pyproject.toml`, `constraints.txt`, `.python-version`, `src/chemiproof/*`, `tests/*`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `.gitignore`, `config/project.yaml` (stage), docs (decision log ADR-006/007, this log, milestones).
Actual commands + exit codes: see `results/M0_foundation/validation_report.md` (pytest exit 0 with 41 passed; ruff exit 0; clean-venv install exit 0; CLI DATASET_NOT_AVAILABLE exit 3).
Measured results (with units; if none say NONE): NONE (no experiments).
Artifact paths + checksums: `results/M0_foundation/` (no checksums needed; text reports).
Acceptance tests (IDs / PASS, FAIL, NOT RUN): T001 PASS; T002-T024 NOT RUN (later milestones); GitHub Actions PASS (run 41572684248, commit c1e8a98).
Risks / open questions: ADR-007 needs owner approval; CP-006 example provenance artifact not produced; pre-commit hook not installed (owner may run `pre-commit install`).
Owner signoff: pending
Next milestone (only after ACCEPTED): M1

### 2026-11-02 — M1 — IN PROGRESS (exploration only; no parser/manifest code yet)
Owner / agent: Mia Ho / Claude Code
Scope attempted: read-only path inventory and plain-text audit of the provided data (scripts kept outside the repo). Owner authorized starting M1 before formal ACCEPTED of M0 (M0 stays REVIEW REQUIRED until owner signs).
Files changed: `.gitignore` (ignore all of `data/` except README and fixtures, plus `*.spc`), `config/project.yaml` (data dir, observed axes), ADR-008/009 in decision log. Data moved to `data/raw/extracted/` (gitignored).
Actual commands + exit codes: path inventory (exit 0); `.dat` audit over 330 files (exit 0); chlorophyll probe (exit 0); Zenodo + paper page fetched via Firecrawl.
Measured results (data facts, not model results):
- 330 `.dat` files, 11 brand x adulterant folders x 3 rounds x 10 ratios; per-adulterant totals by folder-name reading: soybean 60, peanut 60, rapeseed 90, corn 90, walnut 30 (Chinese-name -> oil mapping is the agent's reading, still to be confirmed).
- `.dat` = ASCII tab-separated: header `Sample` + 35 excitation values (640 -> 300 nm, descending), line `nm`, line `Normalized by 1.00`, then 270 rows of [emission nm, 35 intensities]. Emission 297.417 -> 802.484 nm (ascending), identical in all files; unit per header file `Counts/uA`.
- 0 non-finite values, 0 constant spectra, 0 duplicate file hashes; all 330 files contain negative cells (22,982 cells total, min -22.37, max 10,617.7).
- Anomalies: 16 files named `0.dat` instead of `0_RM.dat`; 4 folders hold extra `(1).txt` copies (one `.dat` each).
- Label direction: see ADR-008 (documentary + supporting empirical evidence; not yet owner-approved).
- License of the dataset NOT found on the fetched Zenodo page; the paper is CC BY 4.0. Dataset/author-code license remain UNVERIFIED (LICENSE_REVIEW_PENDING). Zenodo text says "submitted to Nature Food" whereas the paper is published in npj Science of Food (2026-08-05): metadata inconsistency to cite carefully.
Artifact paths + checksums: none yet.
Acceptance tests (IDs / PASS, FAIL, NOT RUN): T002-T006 NOT RUN.
Risks / open questions: ADR-008 approval; dataset license; zip MD5 unverifiable (ADR-009); Chinese NFC/NFD + full-width colon in paths; negative intensities need a documented preprocessing decision in M2.
Owner signoff: pending
Next milestone (only after ACCEPTED): M1 implementation (parser, manifest, QC figures).

### 2026-11-02 — M1 — REVIEW REQUIRED
Owner / agent: Mia Ho (blanket delegation: "follow the .md steps, I trust your decisions, prioritize shipping") / Claude Code
Scope attempted: CP-101..CP-107. Files changed: `src/chemiproof/data/{parser,labels,manifest,zipsafe}.py`, `spectra/{qc,visualize}.py`, `pipeline.py` (`load_dataset` real), `cli.py`, tests (unit + integration + `-m dataset`), `pyproject.toml`/`constraints.txt` (matplotlib), `.gitignore`, license registry, ADR-008/009/010.
Actual commands + exit codes: see `results/M1_20261103T034431Z_b050b36-dirty_33c0ba5b/validation_report.md` (audit exit 0; pytest 90 passed exit 0; dataset tests 3 passed exit 0; ruff exit 0).
Measured results: data facts only: 330 spectra, 60/60/90/90/30, 35x270 grid, 0 NaN, 0 duplicates, 22,982 negative cells in 330/330 files. Model metrics: NONE.
Artifact paths + checksums: manifest sha256 `31c718edd95b4faca5f0f3fe68871870dc6f1b5d2307a8af93e8ce3712765495`; run `20261103T034431Z_b050b36-dirty_33c0ba5b`.
Acceptance tests: T001-T006 PASS (T003 limitation: MD5 unverified; T002 on synthetic zips); T007+ NOT RUN; GitHub Actions PASS on 2d6e03b (run 41574366884).
Risks / open questions: ADR-008 direction evidence (documentary + spectral; 3 weak OliVera pairs); MD5; negative intensities (M2); brand confounding.
Owner signoff: pending
Next milestone (only after ACCEPTED): M2

### 2026-11-02 — M2 — REVIEW REQUIRED
Owner / agent: Mia Ho (blanket delegation) / Claude Code
Scope attempted: CP-201..CP-205. Files changed: `src/chemiproof/{spectra/preprocess,modeling/baselines,evaluation/{metrics,protocols,runner},experiments}.py`, `cli.py` (`experiment run`, `spectra compare`), `config.py` (protocol/models), `config/experiments/{m2_source_internal,baseline}.yaml`, tests (preprocess, metrics, leakage, experiment run, real-data), `pyproject.toml`/`constraints.txt` (scipy, scikit-learn), ADR-011/012.
Actual commands + exit codes: see `results/M2_20261103T041143Z_ca43062_4097e86f/validation_report.md` (run exit 0, git dirty=false; pytest 124 passed exit 0; ruff exit 0).
Measured results (source-internal leave-one-round-out, 3 folds x n=110; OPTIMISTIC, same adulterants in train; macro MAE in percentage points, R2): mean_y 22.73 pp / 0.000; svr_raw 5.10 pp / 0.947; pca_svr 7.09 pp / 0.903; pls 1.37 pp / 0.996. Not unseen-adulterant evidence.
Artifact paths + checksums: `results/M2_20261103T041143Z_ca43062_4097e86f/`; config sha256 `5ddb4697c349f887...`; manifest sha256 `31c718edd95b4fac...`.
Acceptance tests: T007, T008, T009, T011 (M2 protocol), T024 PASS; T010, T012-T023 NOT RUN; GitHub Actions PASS (run 41581270090, commit 6f878a6).
Risks / open questions: grids widened after first run (ADR-012: scores are exploratory-development numbers; M3 must freeze); PCA-SVR underperforms raw SVR (unexplained); round-as-replicate unproven; brand confounding.
Owner signoff: pending
Next milestone (only after ACCEPTED): M3

### 2026-11-02 — M3 — REVIEW REQUIRED
Owner / agent: Mia Ho (blanket delegation) / Claude Code
Scope attempted: CP-301..CP-305. Files changed: `evaluation/{protocols,runner,controls,plots}.py`, `experiments.py` (LOAO, canary, registry, control), `cli.py` (`experiment control`), `config.py` (`run_class`, `subset_brand`), `provenance.py` (dirty flag ignores the registry), configs (`baseline.yaml` locked, `loao_luhua_only.yaml`), tests (LOAO, controls, git state, end-to-end, real-data), ADR-013.
Actual commands + exit codes: see `results/M3_20261103T042740Z_01a9d42_b1c2dfa1/validation_report.md` (two locked runs exit 0 with git dirty=False; controls exit 0; pytest 140 + 6 passed; ruff clean).
Measured results (LOAO-v1, inductive, macro over 5 held-out adulterants; MAE in pp / R2): all-330: mean_y 22.73 / -0.000; svr_raw 8.37 / 0.831; pca_svr 16.55 / 0.019; pls 6.50 / 0.903. Luhua-only: svr_raw 0.859, pls 0.828, pca_svr 0.301. Permuted-label control: R2 <= 0 for all models.
Artifact paths + checksums: `M3_20261103T042740Z_01a9d42_b1c2dfa1`, `M3_20261103T042759Z_01a9d42_2fbd19b6` (config sha256 `2c427bf82704fa93...`, `c98da7473d7088d3...`), manifest `31c718edd95b4fac...`; registry `results/experiment_registry.csv`.
Acceptance tests: T008, T010, T011, T024 PASS; T012-T023 NOT RUN; GitHub Actions PASS (run 41581270090, commit 6f878a6).
Risks / open questions: pca_svr failure unexplained; ranking instability; brand/adulterant confounding; only five folds.
Owner signoff: pending
Next milestone (only after ACCEPTED): M4

### 2026-11-02 — M4 — REVIEW REQUIRED
Owner / agent: Mia Ho (blanket delegation) / Claude Code
Scope attempted: CP-401..CP-405. Files changed: `modeling/ot.py` (independent Sinkhorn, projection, SVR, POT variant, PCA baselines, control), `evaluation/runner.py` (`run_transductive`), `experiments.py` (OT mode, diagnostics, canary, batch sensitivity), `cli.py` (`experiment batch-sensitivity`), `config.py`, `pipeline.py` (`screen_single` refuses OT), configs (`ot_transductive.yaml`, `ot_luhua_only.yaml`), tests (OT unit, end-to-end, real-data), ADR-014/015.
Actual commands + exit codes: see `results/M4_20261103T044749Z_7129cde_363deee6/validation_report.md` (two locked runs exit 0, git dirty=False; stress tests exit 0; pytest 158 + 7 passed; ruff clean).
Measured results (transductive LOAO-OT-v1, macro over 5 held-out adulterants; MAE pp / R2): all-330: ot_svr 4.09 / 0.964; ot_svr_pot 4.09 / 0.965; no-adaptation control (inductive) 8.37 / 0.831; unclipped author_pca50 -1.39, author_pca10 -2.49 (clipped 0.693 / 0.659). Luhua-only: ot_svr 0.977. Stress: label-skewed batches R2 about -3 for OT.
Artifact paths + checksums: `M4_20261103T044749Z_7129cde_363deee6`, `M4_20261103T044812Z_7129cde_44fba4b8` (config sha256 `417e41b5b3029099...`, `70f0c2f5af843fb8...`), batch-sensitivity dirs, manifest `31c718edd95b4fac...`; registry `results/experiment_registry.csv`.
Acceptance tests: T012, T013, T014, T015 PASS; T016-T023 NOT RUN; GitHub Actions PASS (run 41581270090, commit 6f878a6).
Risks / open questions: OT conditional on batch composition and size; published PCA baselines reproduce only with clipping; per-fold published values not compared.
Owner signoff: pending
Next milestone (only after ACCEPTED): M5

### 2026-11-03 — M5 — REVIEW REQUIRED
Owner / agent: Mia Ho (blanket delegation) / Claude Code
Scope attempted: preregistration ADR-017 (LOAO-UQ-v1), `src/chemiproof/uncertainty/{scores,calibration,selective,perturb,runner,report}.py`, `experiments.py` and `cli.py` entry `experiment uncertainty`, config `uncertainty_loao.yaml`, tests (`test_uncertainty.py`, `test_uncertainty_run.py`, real-data M5 test).
Actual commands + exit codes: see `results/M5_20261103T054226Z_914e8ed_ac6bfcef/validation_report.md` (locked run exit 0, git dirty=False; dataset test exit 0; ruff clean).
Measured results (inductive, macro over 5 held-out adulterants): PLS 6.50 pp full MAE, 6.22 pp after `ood_maha` abstention at goal 0.80 (3/5 folds improve). Usefulness rule met by 1 of 6 model/score pairs (the weak pca_svr). Pooled 90 % interval observed coverage 0.47-1.00 by system; `max_domain` intervals 45 pp wide (PLS). Offset/scale invariance measured; 1 % noise lifts PLS MAE to 17.7 pp and OOD abstention to 57 %.
Artifact paths + checksums: `M5_20261103T054226Z_914e8ed_ac6bfcef` (config sha256 `f93cfb4c97d22ad2...`), manifest `31c718edd95b4fac...`; registry `results/experiment_registry.csv`.
Acceptance tests: T011, T016, T017, T018 PASS; T019-T023 NOT RUN.
Risks / open questions: unfavourable abstention result stands as reported; brand/batch effect (soybean-olivera) untested; OT batch-composition detector missing; ADR-017 needs owner review.
Owner signoff: pending
Next milestone (only after ACCEPTED): M6

### 2026-11-03 — Power BI integration (documentation only; M6.5 added to the plan)
Owner / agent: Mia Ho / Claude Code
Scope attempted: audit the repository and artifacts, add Power BI as a presentation layer to the architecture, define the export data contract, the four-page dashboard, KPIs, tests and the new milestone M6.5 (tasks CP-651 to CP-660). No code, no export, no Power BI file, no dashboard was built; M0-M7 numbering and the scientific protocols are unchanged.
Files created: `docs/bi/18_POWER_BI_SPEC.md`, `docs/bi/19_POWER_BI_DATA_MODEL.md`, `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`, `config/bi/export_contract.yaml`, `tests/unit/test_docs_consistency.py`.
Files modified: `README.md`, `CLAUDE.md` (reading item 8, invariant 11, engineering preference), `AGENTS.md`, `docs/vi/ROADMAP_VI.md`, `docs/vi/START_HERE_VI.md`, `docs/vi/17_GLOSSARY_VI.md`, `docs/00_DOCS_INDEX.md`, `docs/product/01_PRD.md`, `docs/product/08_UX_SPEC.md`, `docs/engineering/04_ARCHITECTURE.md`, `docs/engineering/07_ACCEPTANCE_TESTS.md`, `docs/engineering/11_DEV_SETUP.md`, `docs/engineering/12_AI_PROMPTS.md`, `docs/science/05_EVALUATION_PLAN.md`, `docs/science/09_RISK_REGISTER.md` (R21-R27), `docs/science/10_REFERENCES_AND_LICENSES.md`, `docs/project/06_MILESTONES.md` (M6.5), `docs/project/13_DECISION_LOG.md` (ADR-016), `docs/project/15_RELEASE_AND_RESEARCH_REPORT.md`, `docs/project/16_TASK_BACKLOG.md`, `config/milestones.yaml` (added M6.5, statuses refreshed to match this log), `.gitignore`, `tests/README.md`.
Actual commands + exit codes: see the verification list in the final summary of this change (docs consistency test, full pytest, ruff).
Measured results: NONE (documentation only). No model metric was produced or changed.
Acceptance tests: BI001-BI014 and BI020-BI032 defined, all NOT RUN. T001-T024 unchanged.
Risks / open questions: Power BI Desktop is Windows-only and the owner works on macOS (M6.5 may end BLOCKED); uncertainty tables depend on M5 metadata that does not exist yet; the protocol map is seeded from five existing runs; ADR-016 needs owner approval (including M7 not depending on M6.5).
Owner signoff: pending
Next milestone (only after ACCEPTED): M5 (unchanged); M6.5 only after M5 and M6.
