# M1 Data provenance, parsing and EEM QC — validation report

**Date:** 2026-11-02 · **Run ID:** `20261103T034431Z_b050b36-dirty_33c0ba5b` · **Env:** Python 3.12.15, macOS arm64, `constraints.txt`
**Data:** owner-provided extracted copy of Zenodo 10.5281/zenodo.19755088 at `data/raw/extracted/` (no zip; ADR-009).
**Scope:** data audit only. **NO MODEL RESULTS / NO PREDICTION METRICS** exist yet.

## Commands actually run (repo root, `.venv`)

| Command | Exit | Result |
|---|---|---|
| `chemiproof dataset audit` | 0 | manifest 330 rows (sha256 `31c718edd95b4fac...`), discrepancy ledger empty |
| `chemiproof spectra plot --output results/M1_20261103T034431Z_b050b36-dirty_33c0ba5b/eem_examples.png` | 0 | 10 real EEMs plotted (PNG git-ignored) |
| `pytest -q -m "not dataset"` | 0 | 90 passed, 3 deselected |
| `pytest -q -m dataset` (real data) | 0 | 3 passed, 90 deselected |
| `ruff check .` / `ruff format --check .` | 0 / 0 | clean / 60 files formatted |

## Measured data facts (from `data_audit.json`)

- 330 `.dat` parsed, 0 problems: soybean 60, peanut 60, rapeseed 90, corn 90, walnut 30 (matches publication).
- Brand x adulterant cells: corn/rapeseed = Earl Grey, Luhua, OliVera (30 each); soybean/peanut = Luhua, OliVera (30 each); walnut = Luhua (30). 11 cells x 10 ratio levels x 3 rounds.
- Layout: ASCII; 35 excitation (640 -> 300 nm, descending in file; stored ascending), 270 emission (297.417 -> 802.484 nm); ONE identical axis fingerprint across all files; `Normalized by 1.00` everywhere; unit Counts/uA.
- Labels: `olive_fraction = a/11` (1/11 = 0.0909 ... 10/11 = 0.9091), ADR-008.
- QC: 0 NaN/Inf, 0 constant spectra, 0 duplicate file hashes; 330/330 files contain negative cells (22,982 cells; min -22.37, max 10,617.7 Counts/uA) -> WARN, not clamped.
- Oddities: 16 files named `0.dat` (rest `0_RM.dat`); 8 extra `(1).txt` copies in 4 folders; non-`.dat` files (668 txt, 330 jpg, 330 spc) are ignored by the parser.
- Chlorophyll-band probe (supports label direction): band mean higher at max-olive than at min-olive in 11/11 brand-adulterant pairs; Spearman rho +0.90 to +1.00 for 7 pairs (Earl Grey x2, Luhua x5), +0.82 for OliVera/rapeseed, and weak for OliVera/corn (+0.31), OliVera/peanut (+0.39) and OliVera/soybean (-0.04). Exact values: `data_audit.json: chlorophyll_probe`.

## Acceptance tests

| ID | Status | Evidence |
|---|---|---|
| T001 | PASS | `tests/unit/test_synthetic_eem.py` |
| T002 malicious ZIP | PASS (synthetic archives) | `tests/unit/test_zipsafe.py`; the real data was not an archive, so real-zip traversal is not exercised |
| T003 real archive inventory | PASS with limitation | counts reconciled (`tests/integration/test_real_dataset.py`); **published MD5 NOT CHECKED** (no zip) |
| T004 ratio -> olive volume fraction | PASS | `tests/unit/test_labels.py`, real-data test; direction per ADR-008 (documentary + chlorophyll evidence) |
| T005 bad/missing axes or size | PASS | `tests/unit/test_parser.py`, `tests/integration/test_manifest.py` (error carries sample path) |
| T006 duplicates | PASS | synthetic duplicate test; real data has 0 duplicate hashes |
| T007-T024 | NOT RUN | later milestones |

## Known limitations

- ADR-008 direction rests on the Zenodo description plus a spectral consistency check, not on the paper's Methods text (only the abstract page was retrievable). 3 OliVera pairs have weak chlorophyll trend.
- Integrity of the data copy vs the published zip cannot be proven; per-file SHA-256 are recorded for future comparison.
- Chinese-name -> brand/adulterant mapping is by the agent, cross-checked against Table 2 counts, not by the authors.
- PNG figures are git-ignored (derived from third-party data).
