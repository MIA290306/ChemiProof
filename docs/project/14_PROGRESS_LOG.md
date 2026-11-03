# Milestone Progress / Evidence Ledger

**Updated:** 2026-10-24  
**Current overall state:** M0, M1, M2 REVIEW REQUIRED; data audited (330 spectra); first source-internal (optimistic) baseline results exist; no LOAO / unseen-adulterant results yet.  
**Rule:** Agent may set `REVIEW REQUIRED`; **only owner** may mark `ACCEPTED` after evidence review.

| Milestone | Status | Evidence / artifacts | Next action |
|---|---|---|---|
| M0 Foundations | REVIEW REQUIRED | `results/M0_foundation/validation_report.md`, `MILESTONE_REVIEW.md`; 41 tests pass locally and in CI | Owner review and ADR-007 approval (CI green: run 41572684248) |
| M1 Dataset audit | REVIEW REQUIRED | `results/M1_20261103T034431Z_b050b36-dirty_33c0ba5b/` (validation_report, MILESTONE_REVIEW); 330/330 parsed, ledger empty; 93 tests | Owner review (CI green: run 41574366884) |
| M2 Chemometric baselines | REVIEW REQUIRED | `results/M2_20261103T041143Z_ca43062_4097e86f/` (validation_report, MILESTONE_REVIEW); 124 tests; source-internal results exported | Owner review; push and confirm CI |
| M3 LOAO benchmark | NOT STARTED | None | Await M2 acceptance |
| M4 OT replication | NOT STARTED | Published paper numbers, not our results | Await M3 acceptance |
| M5 Abstention/robustness | NOT STARTED | None | Await M4 acceptance |
| M6 Research UI | NOT STARTED | UX spec only | Await validated artifact |
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
Acceptance tests: T007, T008, T009, T011 (M2 protocol), T024 PASS; T010, T012-T023 NOT RUN; GitHub Actions for M2 commits NOT RUN.
Risks / open questions: grids widened after first run (ADR-012: scores are exploratory-development numbers; M3 must freeze); PCA-SVR underperforms raw SVR (unexplained); round-as-replicate unproven; brand confounding.
Owner signoff: pending
Next milestone (only after ACCEPTED): M3
