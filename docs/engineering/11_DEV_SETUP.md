# Development Setup & Reproducibility Operations

## Recommended environment

- macOS / Apple Silicon laptop supported as **target**, not yet validated until M0.
- Use a maintained **stable CPython** version compatible with selected NumPy/SciPy/scikit-learn/POT builds; verify actual package support before pinning (e.g. 3.12 or 3.13 if supported). Do not blindly choose nightly/beta.
- Use isolated virtual environment and a **lockfile / frozen resolution**. The AI agent selects tools after checking up-to-date official package docs and records its choice in `docs/project/13_DECISION_LOG.md`.
- Suggested libraries: NumPy, Pandas, SciPy, Scikit-learn, Plotly, Pytest, Ruff, Streamlit; POT for OT after M4. Keep optional packages optional until needed.

## Bootstrapping

These commands have been run since M0 (latest evidence: `docs/project/14_PROGRESS_LOG.md`). Python must satisfy `requires-python` in `pyproject.toml` (3.12):

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q -m "not dataset"   # synthetic only, as in CI; real-data tests: -m dataset
ruff check .
python -m chemiproof.cli --help
```

If project chooses `uv`, use resolved lockfile and equivalent commands instead; do **not** generate conflicting package managers.

## Proposed CLI contract (implemented incrementally)

```bash
chemiproof dataset inspect --archive data/raw/data.zip
chemiproof dataset audit --archive data/raw/data.zip --output results/M1.../
chemiproof spectra plot --sample <verified_sample_id> --output results/M1.../
chemiproof experiment run --config config/experiments/baseline.yaml
chemiproof experiment run --config config/experiments/ot_transductive.yaml
chemiproof experiment report --run-id <id>
chemiproof app
chemiproof export bi --run results/M3_<run_id> --run results/M4_<run_id> --output exports/bi   # planned, M6.5
```

CLI must fail with a clear message when a command is not yet implemented. Do not mock completed ML results.

## Seed and numerical reproducibility

- Choose and record a primary seed (e.g., 20261024) and any additional study seeds.
- Capture Python/NumPy/SciPy/sklearn/POT versions, OS/architecture, Git commit, source manifest hash, resolved config.
- Save float precision and convergence settings for OT; avoid overly tight bit-for-bit equality across different BLAS implementations.
- Reruns should match splits exactly and scores within documented numerical tolerance. Any variation is logged.

## Data download and safety

- The official archive is about 96 MB. Download manually or via an opt-in agent command only after checking source URL, permissions and disk availability.
- Save in `data/raw/` (gitignored). Never include in package release by default.
- Validate archive paths before extraction, cap max total uncompressed size and reject symlinks/traversal.
- Record published MD5 and calculated SHA-256, check both as appropriate.

## Tests without downloaded data

The default `pytest` and CI must run using tiny generated EEM fixtures with clearly **synthetic** origins. Mark dataset-dependent tests (`@pytest.mark.dataset`) and run explicitly only when source archive is present and checked. Do not let tests silently become no-ops presented as success.

## Developer hygiene

- Avoid committing enormous generated artifacts, user local absolute paths, .env or secrets.
- Store experiment output summaries in small public JSON/CSV only if license/privacy permits; large arrays under ignored `results/` unless specifically approved.
- Add a reproducible `results/README.md` documenting exactly how results were obtained and how public extracts relate to private raw data.
- Keep schemas validated at boundaries and clear exception messages for novice maintainers.

## Power BI (M6.5 only; optional, specification-level)

- **Where it runs:** Power BI Desktop requires Windows 10 or later (checked against Microsoft Learn on 2026-11-03). There is **no macOS version**. On a Mac use a Windows PC, a Windows VM (verify compatibility with Apple silicon first), or a cloud Windows desktop (Windows 365 or Azure Virtual Desktop, which Microsoft documents as supported). Desktop works without signing in; the Power BI service (web, sharing, scheduled refresh) needs a work or school account and personal e-mail addresses such as Gmail are not accepted directly.
- **What can be done on macOS:** write and test the Python export (`src/chemiproof/bi/`), the data contract and KPI recomputation; edit `.pbip` text files (TMDL/PBIR) in VS Code. **What cannot:** open, refresh or verify the report. Text generated outside Desktop is unvalidated until opened there; record this in the milestone review.
- **Files:** use the `.pbip` project format; `.pbix`, `.pbi/cache.abf` and `exports/bi/` are git-ignored. Exports are produced by `chemiproof export bi` and pointed to by the `ExportFolder` parameter. No gateway, scheduled refresh or publishing is assumed.
- **Optional dependency:** Parquet output needs `pip install -e '.[bi]'` (adds `pyarrow`, added only when M6.5 starts); CSV needs nothing.
- Full procedure and tests: `docs/bi/18_POWER_BI_SPEC.md`, `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`.

## CI minimum proposed

On PR/push: install from lock/constraints, `ruff check`, `pytest -m 'not dataset'`, packaging import check and verify no tracked `data/raw/*.dat` or `data.zip`. Science full benchmark is explicitly launched locally and is **not** a fake CI success check.
