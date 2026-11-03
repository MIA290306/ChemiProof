# Milestone Progress / Evidence Ledger

**Updated:** 2026-10-24  
**Current overall state:** M0 REVIEW REQUIRED (tooling only); no data, model or experimental results.  
**Rule:** Agent may set `REVIEW REQUIRED`; **only owner** may mark `ACCEPTED` after evidence review.

| Milestone | Status | Evidence / artifacts | Next action |
|---|---|---|---|
| M0 Foundations | REVIEW REQUIRED | `results/M0_foundation/validation_report.md`, `MILESTONE_REVIEW.md`; 41 tests pass locally | Owner review; push and confirm green GitHub Actions run |
| M1 Dataset audit | NOT STARTED | Published Zenodo link only; no archive downloaded | Perform safe M1 acquisition and parse |
| M2 Chemometric baselines | NOT STARTED | None | Await M1 acceptance |
| M3 LOAO benchmark | NOT STARTED | None | Await M2 acceptance |
| M4 OT replication | NOT STARTED | Published paper numbers, not our results | Await M3 acceptance |
| M5 Abstention/robustness | NOT STARTED | None | Await M4 acceptance |
| M6 Research UI | NOT STARTED | UX spec only | Await validated artifact |
| M7 Release | NOT STARTED | Templates only | Await M6 acceptance |

## Current blockers / unknowns

1. `.dat` actual internal schema, wavelength grid orientation, exact filename-to-label mapping unverified.
2. Data Zenodo license not yet verified from an explicit machine-readable rights field; source GitHub code license not checked.
3. Local environment and 41 synthetic-fixture tests now exist (M0); GitHub Actions has not run yet.
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
Acceptance tests (IDs / PASS, FAIL, NOT RUN): T001 PASS; T002-T024 NOT RUN (later milestones); GitHub Actions NOT RUN.
Risks / open questions: ADR-007 needs owner approval; CP-006 example provenance artifact not produced; pre-commit hook not installed.
Owner signoff: pending
Next milestone (only after ACCEPTED): M1
