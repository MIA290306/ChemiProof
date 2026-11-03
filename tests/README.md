# Tests

Run: `.venv/bin/python -m pytest -q -m "not dataset"` (synthetic fixtures only; no network, no dataset).

- `unit/`: EEM schema + synthetic fixture (T001), config validation, provenance, status codes.
- `integration/`: CLI behaviour and honest failure of unimplemented stages.
- `@pytest.mark.dataset`: needs the real Zenodo archive; fails loudly (never silently skips) without it. Not run in CI.

Remaining IDs `T002`-`T024` in `docs/engineering/07_ACCEPTANCE_TESTS.md` belong to later milestones.

- `unit/test_docs_consistency.py`: documentation checks (internal links, milestone graph, Power BI specification consistency, YAML validity). Plain pytest, no data needed.
