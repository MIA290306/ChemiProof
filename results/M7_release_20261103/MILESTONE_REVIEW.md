# Milestone M7 — Evidence-based Handoff

**Date:** 2026-11-03
**Milestone:** M7 Reproducible public portfolio release
**Status:** REVIEW REQUIRED (agent cannot self-approve ACCEPTED); release **not tagged**
**Owner reviewer:** Mia Ho

## Scope actually delivered

- **CP-701** clean-environment reproduction of every locked and final run; new `chemiproof experiment compare` (T021).
- **CP-702** `docs/release/RESEARCH_REPORT.md` (about 3,200 words, template sections, every number with its run), `MODEL_CARD.md`, `DATA_CARD.md`.
- **CP-703** `docs/release/RELEASE_REVIEW.md`: rights table, package licenses, citation locations, third-party rerun checklist, external review packet with seven questions, integrity checklist, gate status. ADR-019 (license) PROPOSED.
- **CP-704 (partial)** README: real results, attribution, reproduce commands, license status.
- **Not implemented:** license file (owner decision), README screenshots and 90-second demo (data-derived; ADR-019 question 3), external review, release tag, Power BI layer (M6.5, Windows).

## Scientific assumptions and protocol deviations

- No protocol, config or model changed; no new metric of record. The report only restates committed numbers.
- `experiment report --run-id` (planned in `11_DEV_SETUP.md`) was dropped: every run already writes `run_report.md`. Replaced by `experiment compare`.
- `constraints.txt` gained the missing `POT==0.9.7.post1` pin (the version the clean install resolved). Owner approval required? no (environment pin only).

## Files and artifacts

| Path | Purpose | SHA/Run ID |
|---|---|---|
| `src/chemiproof/evaluation/compare.py`, `cli.py` | rerun equality check | branch `m7/release` |
| `tests/unit/test_compare.py`, `tests/integration/test_cli_and_stages.py` | tests for it | |
| `docs/release/*.md` | report, cards, release review | |
| `docs/project/13_DECISION_LOG.md` | ADR-019 PROPOSED | |
| `results/M7_release_20261103/{validation_report.md,reproduction_compare.txt}` | evidence | rerun folders kept in scratch only |

## Executed verification — not just expectations

| Command / test ID | Exit code | Measured result or diagnostic | PASS/FAIL/NOT RUN |
|---|---|---|---|
| clean clone + fresh venv + all locked/final configs | 0 | see validation report | PASS |
| `chemiproof experiment compare` x 6 | 0 | max abs. diff 2.3e-14 fraction | PASS (T021) |
| final `model.npz` sha256 | n/a | identical `bbcff343...` | PASS |
| `pytest -q -m "not dataset"` | 0 | 236 passed | PASS |
| `pytest -q -m dataset` | 0 | 9 passed | PASS |
| `ruff check .`, `ruff format --check .` | 0, 0 | clean | PASS |
| T022 | n/a | data + author code cleared; own license pending | PARTIAL |
| external reviewer | n/a | none assigned | NOT RUN |

## Scientific results (if any)

- NO NEW EXPERIMENTAL RESULTS. Existing results reproduced to round-off.
- Paper reference values: kept separate (report section 4.3).

## Open blockers and adverse observations

1. ChemiProof license not chosen (ADR-019); until then all rights reserved and no tag.
2. No external reviewer; the M7 exit gate and `15_RELEASE...` final exit rule require one.
3. Reproduction covers one OS family and one set of library versions.
4. Published archive MD5 still unmatched.
5. FINAL-PLS-v1 has no independent test; abstention and intervals are not reliably useful (stated in the report).

## Recommendations and next action

- **Decisions requested from owner:** (1) accept or change ADR-019 (license, copyright holder name, public result tables, screenshots); (2) name an external reviewer (instructor, mentor or QA practitioner) and send the packet in `RELEASE_REVIEW.md` section 5; (3) review and merge the M7 pull request (PR #3, M6, was merged on 2026-11-03 as `3035439`; merging is not the same as marking M6 ACCEPTED).
- **Conditions before M7 may be ACCEPTED:** license decided and `LICENSE` added; reviewer answers recorded; any blocking review finding fixed; then tag `v1.0`.
- **Suggested next milestone AFTER approval:** none in the plan; optional M6.5 on a Windows machine, and the two open M5 questions (brand-effect test, OT batch-composition detector) as new ADRs.
