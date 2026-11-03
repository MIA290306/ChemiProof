# Tests

Run: `.venv/bin/python -m pytest -q -m "not dataset"` (synthetic fixtures only; no network, no dataset).

- `unit/`: parser, labels, preprocessing, metrics, LOAO folds, leakage guards, OT, controls, rerun comparison, committed-result recomputation, docs consistency.
- `integration/`: CLI, manifest, experiment runs (M2-M5), final model, Streamlit explorer.
- `@pytest.mark.dataset`: needs the real Zenodo archive; fails loudly (never silently skips) without it. Not run in CI.

Acceptance-test IDs (`T001`-`T024`) are defined in `docs/engineering/07_ACCEPTANCE_TESTS.md`; their status per milestone is in `docs/project/14_PROGRESS_LOG.md`.

- `unit/test_docs_consistency.py`: documentation checks (internal links, milestone graph, Power BI specification consistency, YAML validity). Plain pytest, no data needed.
