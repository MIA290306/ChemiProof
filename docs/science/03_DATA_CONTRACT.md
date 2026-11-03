# Dataset & Ingestion Contract

## Source of truth

Zenodo dataset: https://zenodo.org/records/19755088 (DOI 10.5281/zenodo.19755088). File listed `data.zip` **~95.9 MB**, publication MD5 `dfad908d186e584b96b6070d90cbeec4`. The download is **not included** in this repo. Rights/license must be reviewed before republication.

## Expected research inventory (from publication, not yet audited against archive)

| Adulterant | EVOO brands reported | Expected spectra | 10 levels × 3 replicates × brands |
|---|---|---:|---:|
| soybean | Luhua, OliVera | 60 | 10 × 3 × 2 |
| peanut | Luhua, OliVera | 60 | 10 × 3 × 2 |
| rapeseed | Earl Grey, Luhua, OliVera | 90 | 10 × 3 × 3 |
| corn-germ | Earl Grey, Luhua, OliVera | 90 | 10 × 3 × 3 |
| walnut | Luhua | 30 | 10 × 3 × 1 |
| **Total** | 3 brands, unbalanced | **330** |  |

> Important: the Zenodo description alone (five oil systems × 10 levels × 3 replicates) superficially suggests 150. The article's detailed Table 2 explains the 330 through **brand combinations**. If actual ZIP contents disagree, document the discrepancy rather than filling in missing records.

Reported wavelength range: excitation 300–640 nm (35 channels); emission 300–800 nm (270 channels). **Do not assume wavelengths are uniformly spaced, specific orientations, or column/header schema until opening sample files**.

## Four zones of data

- `data/raw/` (**gitignored**) downloaded archive and unchanged extracted files. Immutable and provenance-tracked.
- `data/interim/` (**gitignored**) parsed arrays and metadata with exact source SHA-256.
- `data/processed/` (**gitignored**) outputs of specific named preprocessing version.
- `data/fixtures/` (**tracked**) small explicitly **synthetic** or freely distributable fixtures that cannot be mistaken for laboratory measurement data.

## Proposed canonical metadata schema

Store `data/interim/sample_manifest.csv` with columns:

| Column | Type | Semantics / validation |
|---|---|---|
| `sample_id` | string | stable unique ID generated from relative path + checksum; no collisions |
| `relative_path` | string | path relative to archive root; normalized; no `..` |
| `sha256` | 64-char hex | content digest of source .dat |
| `source_record_doi` | string | `10.5281/zenodo.19755088` |
| `adulterant_type` | enum | `soybean`, `peanut`, `rapeseed`, `corn`, `walnut`; backed by verified mapping |
| `evoo_brand` | enum or null | verified from source encoding where possible; otherwise null and record reason |
| `olive_fraction` | float | 0 ≤ y ≤ 1; derived from verified **volume** ratio |
| `olive_ratio_raw` | string | exact raw folder token/ratio to preserve original evidence |
| `replicate_id` | string or null | physical/sample replicate code if identifiable; not guessed from sort order |
| `measurement_round` | string or null | round/batch if identifiable |
| `excitation_channels` | int | expected 35 after valid parsing |
| `emission_channels` | int | expected 270 after valid parsing |
| `excitation_min_nm/max_nm` | float | as parsed; report without coercion |
| `emission_min_nm/max_nm` | float | as parsed; report without coercion |
| `qc_status` | enum | `PASS/WARN/FAIL`, separate flags |
| `parser_version` | string | semantic version + git SHA |

Add `metadata_evidence.json` for each inferred field: what file path/header rule justified the value. **Unknown is better than fabricated.**

## Proposed spectrum object

```python
SpectrumRecord(
    sample_id: str,
    excitation_nm: FloatArray,          # (35,) after validation
    emission_nm: FloatArray,            # (270,) after validation
    intensity: FloatArray,              # canonical orientation (35, 270)
    metadata: SampleMetadata,
    raw_sha256: str,
    preprocessing_history: list,
)
```

**At ingestion:** distinguish raw instrument axes vs transformed aligned arrays; do not merely reshape 9,450 floats if no axis metadata exists to establish correct orientation.

## Required M1 acquisition and parse procedure

1. Acquire directly from official Zenodo link. Record URL, retrieval time, published MD5 and actual computed SHA-256/MD5.
2. Verify checksum. If mismatch, stop. Do not download from random mirrors.
3. Inspect ZIP **without extraction**: member count, extensions, compressed/uncompressed total sizes, traversal paths, symlinks, duplicates, archive bombs. Quarantine suspicious paths.
4. Sample at least one .dat from EACH adulterant and EACH distinct layout variant. Record first rows, delimiters, headers and axes in a safe local audit; redact copyrighted/raw content from public docs as needed.
5. Write parser for **actual discovered** schema. Do not use `eval`, `pickle`, unsafe deserialization or floating-point `reshape` guesswork.
6. Cross-check all 330 records and expected breakdown; log unexplained extras/missing files and whether pure-oil spectra are included in archive.
7. Verify ratio orientation: e.g. folder token A:B could mean olive:adulterant or reverse; prove via primary paper or author code before assigning target values.
8. Validate replicate patterns, duplicate hashes, identical matrices and repeated filenames. Reject compromised or contradictory labels.
9. Store a versioned manifest/QA report, with file-level warnings and scientific uncertainties.
10. Generate **actual spectra** visualization as optional proof; never use demo figures as evidence of raw experimental results.

## Parser and QC failure modes

| Problem | Policy |
|---|---|
| Unsupported extension/ZIP member | skip only if explicit rule; log and count |
| Invalid path traversal | reject archive |
| Non-monotonic/missing wavelength axis | reject or quarantine; no silent reversal without explicit validated rule |
| Shape incompatible with 35 × 270 | reject and report exact discovered dimensions |
| Non-finite values | fail spectrum by default pending scientific review |
| Raw negative intensity | warn/review instrument conventions; do not blindly clamp |
| Corrected negative intensity | permitted only if correction operation is documented |
| Zero/constant signal | fail prediction QC; data audit still retains record |
| Saturation / extreme noise | warn/flag; preregister decision thresholds |
| Unknown brand or ratio | retain provenance; forbid training label inference until resolved |
| Duplicate biological or technical replicates | identify grouping; don't let cross-partition leakage occur |

## Structured output from M1

```text
data/interim/sample_manifest.csv
results/M1_<run_id>/data_audit.json
results/M1_<run_id>/qc_summary.csv
results/M1_<run_id>/eem_examples.png
results/M1_<run_id>/README.md
```

**Acceptance**: discrepancy ledger completely filled; exact rows and label frequencies justified; all required axes confirmed; parser tested on synthetic valid/malformed fixtures; failures are explicit. Counts are a hypothesis to test, not a reason to alter the data.
