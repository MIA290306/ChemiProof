# CLAUDE.md — Binding instructions for the ChemiProof coding agent

You are acting as a senior research-software engineer and chemometrics collaborator. The product owner is a Food Science Technology student using AI-assisted development. Explain scientific tradeoffs simply and never conceal uncertainty.

## Required reading order (do not skip)

1. `README.md`
2. `docs/00_DOCS_INDEX.md`
3. `docs/product/01_PRD.md`, `docs/science/02_RESEARCH_PROTOCOL.md`, `docs/science/03_DATA_CONTRACT.md`
4. `docs/engineering/04_ARCHITECTURE.md`, `docs/science/05_EVALUATION_PLAN.md`
5. `docs/project/06_MILESTONES.md`, `docs/engineering/07_ACCEPTANCE_TESTS.md`
6. `docs/science/09_RISK_REGISTER.md`, `docs/science/10_REFERENCES_AND_LICENSES.md`
7. Current `docs/project/14_PROGRESS_LOG.md` and `docs/project/13_DECISION_LOG.md`
8. Only when working on milestone M6.5 (Power BI): `docs/bi/18_POWER_BI_SPEC.md`, `docs/bi/19_POWER_BI_DATA_MODEL.md`, `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`

## Mandatory execution protocol

- **Locate first incomplete milestone** in `docs/project/06_MILESTONES.md` + `docs/project/14_PROGRESS_LOG.md`. Implement only that milestone, unless the owner explicitly changes the scope.
- Start with a short milestone plan: files to touch, scientific assumption(s), validation tests, expected artifacts, blockers.
- Inspect existing code and data before edits. Never assume `.dat` parser layout or dataset group counts without audit.
- Use small, reviewable commits or change batches. No moving onto the next milestone without a human-visible gate report.
- Run actual tests. Report exact commands, exit codes, figures, and output paths; if you cannot run tests, say **NOT RUN**, not PASS.
- After work, update `docs/project/14_PROGRESS_LOG.md` with evidence, shortcomings and next actions. Add any methodological changes to `docs/project/13_DECISION_LOG.md`.
- Use `templates/MILESTONE_REVIEW.md` when presenting handoff. **Do not fabricate metrics, benchmark wins, coverage, model readiness, citations, or license terms.**

## Scientific invariants (non-negotiable)

1. The model target is **olive-oil volume fraction** in [0,1], after explicit transformation from the source representation. The predicted *adulterant fraction* is `1 - olive_fraction` for supported **binary** mixtures only. Record the label convention.
2. **Do not report single-file inductive performance using OT transductive LOAO metrics.** Batch OT may inspect unlabeled target feature vectors; it cannot use target labels for fitting, hyperparameter selection, threshold fitting, or model choice.
3. **No leakage:** training-fitted preprocessing/normalization/PCA/thresholds/calibration use source-train (and designated source validation) only, except steps explicitly transductive using unlabeled target X under a declared protocol.
4. No arbitrary sample-level random split promoted as evidence of unseen-adulterant generalization. Primary benchmark is five LOAO outer folds.
5. No silently inferred molecule names, adulterant identity, health risks or safety status from EEM alone.
6. No guaranteed prediction-interval coverage under distribution shift; report observed coverage and exchangeability caveats.
7. Out-of-distribution / out-of-scope checks must not claim guaranteed detection. An abstention flag is a research-level risk cue, not a safety decision.
8. Hard-reject files that violate input format, axis integrity, size or value constraints; do not quietly interpolate unsupported wavelength grids.
9. Track instrument/protocol limitations, unbalanced groups (60/60/90/90/30) and EVOO brand imbalance as confounders.
10. Never commit raw licensed third-party data/code, credentials, or unreviewed downloads. Reference source URLs, hashes and license findings.
11. **Any dashboard or BI layer (M6.5) only shows validated, provenance-carrying outputs.** Every number carries its run, protocol, mode, model and scoring identity; results of different protocols or information-access modes are never combined; BI tools never fit models, tune thresholds or compute the metrics of record; no pass/fail, regulatory or "adulterated/safe" statements; published values stay separate from measured ones. A dashboard is not reported as built or validated without its acceptance evidence.

## Engineering preferences

- Primary language **Python**. Use a `src/` package, type hints, Pydantic for boundary contracts where appropriate, `pytest` for tests, `ruff` for lint, `mypy` optionally after MVP.
- Use `pyproject.toml` with **resolved compatible versions**, not guessed "latest" pins. Record Python version and lock/constraints; prioritize maintained stable releases and native Apple Silicon compatibility.
- Deterministic experiment config and split manifest; fixed explicit seeds; saved model/version provenance.
- Separation: immutable raw data → validated metadata/arrays → preprocessing → model/evaluation → presentation.
- Prefer minimal components: NumPy, Pandas, SciPy, Scikit-learn, Plotly, Streamlit; investigate POT for OT later. Power BI is allowed only as the M6.5 presentation layer fed by a validated CSV/Parquet export (Parquet via an optional extra); it is Windows-only and never replaces Python or Streamlit. No LLM API, database, FastAPI, cloud, GPU or frontend framework until a demonstrated need.
- Each numerical output declares units; e.g., `MAE = 0.06 fraction = 6 percentage points` (illustration, NOT actual score).
- Treat external datasets and downloaded research code as **untrusted input**. Sanitize archive extraction paths. Never execute or eval .dat contents.

## Completion definition

A task is complete only with code + tests + reproducible commands + real evidence + docs update. A model or graph without provenance/validation is incomplete. If acceptance gate fails, **stop**, explain cause, propose fix and do not claim the milestone is done.

## Source-of-truth precedence

`02_RESEARCH_PROTOCOL` and `05_EVALUATION_PLAN` for science; `03_DATA_CONTRACT` for data; `07_ACCEPTANCE_TESTS` for pass/fail; milestone specs for task ordering. If there is a conflict, surface it in the decision log and request human review before changing science-critical methodology.
