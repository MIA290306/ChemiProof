# Paste-ready Claude Code Prompts

**Operating mode:** run **one prompt at a time**. The agent must not continue to subsequent milestone without a status review. Save its handoff in `templates/MILESTONE_REVIEW.md` format.

## PROMPT 0 — Read docs and start M0

```text
You are the lead research software engineer on ChemiProof. First read CLAUDE.md, AGENTS.md, docs/vi/START_HERE_VI.md, README.md, every numbered file under docs/ (00-17, see docs/00_DOCS_INDEX.md), and config files. Summarize (a) research objective and scientific caveats, (b) current implementation state, (c) M0 acceptance gate, (d) critical data leakage and licensing risks. Then implement ONLY Milestone M0 in docs/project/06_MILESTONES.md. Do not fabricate research results or skip tests. Create the smallest maintainable Python package, dependency setup and lock, synthetic EEM fixtures, lint/tests/CI, configuration validation and truthful CLI placeholders. Run tests and give exact commands/results. Update docs/project/14_PROGRESS_LOG.md to REVIEW REQUIRED, not ACCEPTED. Create a milestone review using templates/MILESTONE_REVIEW.md. Stop. Respond in Vietnamese for the owner, preserve technical names in English.
```

## PROMPT 1 — Source archive and M1 parsing

```text
Read CLAUDE.md plus the docs numbered 02,03,06,07,09,10 and progress log. Work ONLY on M1. Verify dataset download, rights, and published checksum; do not redistribute the archive. Before writing a parser, inspect actual .dat layouts from each oil group and validate wavelength axis orientation. Build safe loader/manifest with file hashes, true volume fraction labels and source evidence, group/brand/replicate audit. Check published expected counts soybean60, peanut60, rapeseed90, corn90, walnut30, total330; treat differences as a finding, never fake missing records. Generate QC and real spectrum figures, parser tests including malformed files and ZIP traversal attack. If labels or grids are ambiguous, BLOCK M1 with exact questions. Run tests, report artifacts and update docs log to REVIEW REQUIRED. Stop.
```

## PROMPT 2 — Chemometric baselines M2

```text
Read CLAUDE.md, the docs numbered 02,04,05,06,07 and accepted M1 artifacts. Implement ONLY M2: auditable EEM preprocessing with justified physical operations, source-fitted transformations, mean baseline, raw SVR, PCA+SVR and optional PLS. Verify label scale and paper settings before adopting hyperparameters. Use source-internal validation, tests for transformation leakage and numerical metrics. Export first REAL measured source-validation results with configuration, sample IDs and provenance. Never use held-out outer target labels for tuning. Provide review and stop.
```

## PROMPT 3 — Full LOAO M3

```text
Read the docs numbered 02,05,06,07 and existing pipeline. Implement exactly five LOAO outer folds (oil-system holdout), source-only inner hyperparameter selection, immutable manifests, per-fold MAE/RMSE/R2/bias/n, macro + pooled aggregates, and brand/confounding analysis. Create test that perturbing outer target labels cannot change model training, thresholds or hyperparameters. Export predictions and honest reference-vs-measured tables. Stop at REVIEW REQUIRED with evidence.
```

## PROMPT 4 — OT batch adaptation M4

```text
Read the docs numbered 02,04,05,06,07 and paper/author repo. Implement the published-style ENTROPIC OT -> barycentric source projection -> SVR LOAO research protocol. Enforce that ONLY unlabeled target spectral X may be used for transductive adaptation, NEVER target y until final scoring. Validate epsilon, cost scale, marginal residuals, solver convergence and paper SVR label units. Never present transductive output as independent single-file prediction. Compare paper report with our actual runs and document discrepancies. Run tests + deliver review then stop.
```

## PROMPT 5 — Honest uncertainty and selective prediction M5

```text
Read the docs numbered 02,05,06,07,09. Propose a preregistered, implementable selective prediction rule calibrated ONLY within the source domains. Implement empirical intervals/abstention, risk-versus-coverage plots at 100/90/80/70% retention, per-adulterant interval coverage and robust synthetic perturbation experiments with limits. Never promise conformal coverage under LOAO distribution shift. Include negative results/failure cases, distinguish baseline from OT mode, compare random rejection. Export original findings and stop for human review.
```

## PROMPT 6 — Research UI M6

```text
Read the docs numbered 01,04,07,08. Implement a minimal local Streamlit research explorer reading validated models and real benchmark artifacts. Six planned sections: Overview, EEM Explorer, Benchmarks, Single-sample inductive screening, Batch transductive research, Methods/Provenance. Invalid or unsupported file must refuse output; abstention says Review Required. Show olive-oil volume fraction, mode, model provenance, uncertainty caveat and not-for-certification disclaimer. No fake dashboard metrics, no login/database/cloud. Test malformed uploads and mode mismatch. Stop for review.
```

## PROMPT 7 — Portfolio release M7

```text
Read all docs, accepted milestone reports and templates/RESEARCH_REPORT.md. Perform independent clean rerun and science/engineering gate audit. Write a real research-style report with honest per-fold quantitative figures, detailed methods, limitations, comparative results and original contribution. Create model/data card and README with attribution to Sun et al. 2026 and Zenodo DOI. Review upstream licenses BEFORE redistribution, do not publish source data by default. Do not claim certified fraud detection. Produce release checklist, request reviewer comments and stop at REVIEW REQUIRED.
```

## PROMPT for a code review (any phase)

```text
Act as a skeptical chemometrics method reviewer and senior Python engineer. Inspect current diff and compare against CLAUDE.md, the docs numbered 02,03,05,07. Find leakage risks, bad labels/axes, untested numerical assumptions, transductive/inductive mismatch, dataset rights issues, misleading UI claims, weak tests, and reproducibility holes. Report concrete severity-ranked findings with file paths/lines, an actionable fix, and commands/tests to prove fixes. Do not mark a review clean without executing the available tests.
```

## PROMPT for student explanation (any phase)

```text
Explain the last milestone in Vietnamese to someone studying Food Science but new to Python. Define EEM/chemometrics concepts, show what actual inputs and outputs mean, distinguish measured results from sample numbers, explain each chart's units, and give three understanding-check questions. Do not assert achievements without checking saved artifacts.
```
