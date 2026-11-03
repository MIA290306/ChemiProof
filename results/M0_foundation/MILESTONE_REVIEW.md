# Milestone M0 — Evidence-based Handoff

**Date:** 2026-11-02  
**Milestone:** M0 Foundation  
**Status:** REVIEW REQUIRED (agent cannot self-approve ACCEPTED)  
**Owner reviewer:** Mia Ho

## Scope actually delivered

- Task IDs and names: CP-001 (Python/env choice), CP-002 (package + CLI), CP-003 (config validation), CP-004 (synthetic EEM fixtures), CP-005 (lint/test/CI, raw-data guard), CP-006 (provenance helper; no example artifact yet).
- Summary of implemented behavior: installable `chemiproof` package, argparse CLI whose later-milestone commands fail with `NOT_IMPLEMENTED`/`DATASET_NOT_AVAILABLE`, pydantic config validation enforcing scientific invariants, deterministic synthetic EEM, `run_id` helper, CI workflow, pre-commit config.
- What was explicitly **not** implemented: any parser, real data access, preprocessing, models, metrics, UI. No example provenance artifact (CP-006 evidence) was produced.

## Scientific assumptions and protocol deviations

- Original spec expectation: status taxonomy in docs/engineering/04_ARCHITECTURE.md; `results/M0.../validation_report.md`.
- Actual method: taxonomy extended with `DATASET_NOT_AVAILABLE`, `INVALID_CONFIG`, `NOT_IMPLEMENTED`; `.gitignore` exception for `results/M0_foundation/`.
- Reason and reference: docs/project/13_DECISION_LOG.md ADR-007.
- Owner approval required? yes (taxonomy extension)

## Files and artifacts

| Path | Purpose | SHA/Run ID |
|---|---|---|
| pyproject.toml, constraints.txt, .python-version | package + resolved lock | n/a |
| src/chemiproof/ | package | n/a |
| tests/ | 41 tests + 1 dataset-gated | n/a |
| .github/workflows/ci.yml, .pre-commit-config.yaml | CI / hooks | CI not yet run |
| results/M0_foundation/validation_report.md | evidence | n/a |

## Executed verification — not just expectations

See `results/M0_foundation/validation_report.md` for the full command/exit-code table. Summary: pytest 41 passed (exit 0); ruff check/format clean (exit 0); clean-venv install from constraints OK (exit 0); T001 PASS; GitHub Actions `ci` PASS (run 41572684248, commit c1e8a98).

## Scientific results (if any)

`NO EXPERIMENTAL RESULTS YET`

## Open blockers and adverse observations

1. ~~CI not yet run~~ Resolved: green run 41572684248 on commit c1e8a98.
2. `pre-commit install` not performed (modifies `.git/hooks`); owner can run `.venv/bin/pre-commit install`.
3. Dataset license, `.dat` schema and label direction remain unverified (M1 scope).

## Recommendations and next action

- Decision requested from owner: approve ADR-007 (extra status codes).
- Conditions before M0 may be ACCEPTED: owner review of this report and ADR-007 (CI condition met).
- Suggested next milestone AFTER approval: M1 (dataset audit; needs manual Zenodo download and license check).
