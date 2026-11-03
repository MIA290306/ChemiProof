# Power BI Data Model and Data Contract (M6.5)

**Status: SPECIFICATION ONLY.** No exporter, no `.pbip`/`.pbix` and no DAX has been written or run. Nothing in this file is a result. It defines what a future export from the ChemiProof Python pipeline must contain so Power BI can show the validated outputs without changing them.

Companion documents: `docs/bi/18_POWER_BI_SPEC.md` (dashboard and process), `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md` (tests), `config/bi/export_contract.yaml` (machine-readable twin of the tables below; `tests/unit/test_docs_consistency.py` checks that both lists of columns match).

## 1. Design principles

1. **Python computes, Power BI presents.** Every metric shown in Power BI must be reproducible from the exported experiment outputs with Python (see section 6). Power BI never fits a model, tunes a threshold, or reads raw spectra.
2. **Identify before you aggregate.** Every fact row carries `run_id`, `model_key` and `mode`; every run carries `protocol_id`, `run_class`, `config_sha256`, `manifest_sha256` and `git_head`. Results of different protocols or information-access modes are never combined into one number (section 4).
3. **Evaluation outputs only.** The export reads finished run directories under `results/`. Test labels appear only because they are part of those evaluation artifacts (`y_true_fraction`); they are never an input to any model.
4. **No raw data, no spectra.** The export contains per-sample metadata, QC summaries and predictions. It contains no intensity matrices, no raw `.dat` content and no `.pbix` data cache is committed.
5. **Unknown stays unknown.** Missing values are exported as null with the reason in a documented column; the exporter never fabricates rows for experiments that do not exist (for example uncertainty before M5).
6. **Units are explicit.** Concentration labels are olive-oil volume fractions in [0,1]; percentage-point columns are always `100 x fraction` and are validated.

## 2. Files produced by the export (specification)

```text
exports/bi/<export_id>/            # git-ignored by default; <export_id> = UTC time + exporter git hash + input-runs hash
  export_manifest.json
  dim_adulterant.csv|parquet   dim_brand   dim_sample   dim_model   dim_fold   dim_experiment
  fact_predictions   fact_model_metrics   fact_uncertainty   fact_selective_risk
  fact_data_quality   fact_data_issues   fact_ot_diagnostics   fact_robustness   fact_published_reference
```

- **Formats:** CSV (UTF-8, comma, `\n`, decimal point, ISO 8601 UTC timestamps, booleans `true/false`) is the default and needs no extra dependency. Parquet is an optional second format (`pyarrow`, optional extra `bi`, see ADR-016) with identical column names and types. Power BI Desktop has built-in CSV and Parquet connectors (to be confirmed on first use).
- **Determinism:** rows are sorted by primary key; floats are written with a fixed number of significant digits (17); the only non-deterministic content is the creation time stored in `export_manifest.json`.
- **`export_manifest.json`** records: `export_id`, `contract_version`, `created_utc`, exporter `git_head` and `git_dirty`, Python/package versions, for each source run `{run_id, run_dir, protocol_id, run_class, config_sha256, manifest_sha256, git_head, git_dirty}`, for each file `{table, format, rows, sha256}`, and flags `uncertainty_available`, `selective_risk_available`, `robustness_available`.
- **Location policy:** the export never writes inside `data/` or inside a source run directory and never modifies the dataset.

## 3. Tables

Reference counts observed when this specification was written (2026-11-03): 330 spectra; 5 adulterants; 3 brands; run directories on disk: M2 source-internal 1, M3 LOAO locked 2 (+2 negative controls), M4 OT locked 2 (+2 batch-stress), M1 data audit 1. Expected `fact_predictions` rows for the five scored runs: 1,320 (M2) + 1,320 + 600 (M3) + 1,650 + 750 (M4) = 5,640. These counts illustrate the contract; the exporter must compute its own.

### `dim_adulterant`

- **Kind:** dimension · **Grain:** one row per adulterant system (5)
- **Primary key:** `adulterant_key`
- **Source:** reference constants (chemiproof.data.labels; docs/science/03_DATA_CONTRACT.md); NOT measurements
- **Availability:** `AVAILABLE_M1`

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `adulterant_key` | string |  | no | enum: soybean, peanut, rapeseed, corn, walnut |
| `adulterant_label` | string |  | no | English display name, e.g. 'Soybean oil' |
| `expected_samples` | int | samples | no | published expectation 60/60/90/90/30; reference value, not a measurement |
| `expected_brands` | int | brands | no | published design: soybean 2, peanut 2, rapeseed 3, corn 3, walnut 1 |

### `dim_brand`

- **Kind:** dimension · **Grain:** one row per EVOO brand (3)
- **Primary key:** `brand_key`
- **Source:** reference constants (chemiproof.data.labels; article Table 2 via 03_DATA_CONTRACT)
- **Availability:** `AVAILABLE_M1`

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `brand_key` | string |  | no | enum: luhua, olivera, earl_grey |
| `brand_label` | string |  | no | display name: Luhua, OliVera, Earl Grey |

### `dim_sample`

- **Kind:** dimension · **Grain:** one row per validated spectrum (330 expected)
- **Primary key:** `sample_id`
- **Source:** data/interim/sample_manifest.csv (M1)
- **Availability:** `AVAILABLE_M1`

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `sample_id` | string |  | no | stable ID from the manifest; unique |
| `adulterant_key` | string |  | no | FK to dim_adulterant |
| `brand_key` | string |  | no | FK to dim_brand (a confounder, never an outcome) |
| `olive_fraction` | decimal | fraction | no | olive-oil VOLUME fraction a/11 in [0,1] (ADR-008); the label convention |
| `olive_percent` | decimal | percent | no | = 100 * olive_fraction (exported for display; validated) |
| `olive_ratio_raw` | string |  | no | raw folder token, e.g. '10：1' (olive : adulterant), kept as evidence |
| `measurement_round` | int | round | no | 1, 2 or 3 (folder name); replicate equivalence is unproven |
| `replicate_id` | string |  | yes | empty in the current manifest; never guessed |
| `source_file_sha256` | string |  | no | SHA-256 of the source .dat (64 hex); provenance |
| `source_record_doi` | string |  | no | 10.5281/zenodo.19755088 |
| `manifest_sha256` | string |  | no | SHA-256 of the manifest this row came from |
| `parser_version` | string |  | no | parser that produced the row |

### `dim_model`

- **Kind:** dimension · **Grain:** one row per model key
- **Primary key:** `model_key`
- **Source:** reference table maintained with the code (chemiproof.modeling); versioned by contract_version
- **Availability:** `AVAILABLE_M3_M4`

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `model_key` | string |  | no | mean_y, svr_raw, pca_svr, pls, ot_svr, ot_svr_pot, author_pca50, author_pca10, svr_no_adaptation |
| `model_family` | string |  | no | enum: baseline, svr, pca_svr, pls, optimal_transport, published_style_pca, control |
| `default_mode` | string |  | no | enum: inductive, transductive_batch |
| `information_access` | string |  | no | plain-language statement of what the model may read (e.g. 'source labels+features only') |
| `is_control` | bool |  | no | true for mean_y and svr_no_adaptation |
| `is_published_style` | bool |  | no | true for author_pca50 / author_pca10 / ot_svr_pot |
| `description` | string |  | no | short description; no performance claims |

### `dim_fold`

- **Kind:** dimension · **Grain:** one row per fold id
- **Primary key:** `fold_id`
- **Source:** fold manifests / metrics_by_fold.csv
- **Availability:** `AVAILABLE_M3`

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `fold_id` | string |  | no | LOAO-soybean, LOAO-peanut, LOAO-rapeseed, LOAO-corn, LOAO-walnut, SI-round1..3 |
| `fold_type` | string |  | no | enum: LOAO, SOURCE_INTERNAL_ROUND |
| `target_adulterant` | string |  | yes | held-out adulterant for LOAO folds, null otherwise (text attribute, no relationship) |
| `held_out_round` | int | round | yes | held-out measurement round for SOURCE_INTERNAL_ROUND folds |

### `dim_experiment`

- **Kind:** dimension · **Grain:** one row per evaluation run (run directory)
- **Primary key:** `run_id`
- **Source:** results/<run>/summary.json, config_resolved.yaml, git_state.json, results/experiment_registry.csv, protocol map
- **Availability:** `AVAILABLE_M2_M4`

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `run_id` | string |  | no | UTC timestamp + git hash + config hash (matches the run directory name suffix) |
| `run_dir` | string |  | no | run directory name only (no absolute path) |
| `experiment_id` | string |  | no | from the resolved config |
| `protocol_id` | string |  | no | e.g. LOAO-v1, LOAO-OT-v1, SI-LORO-v1; from the versioned protocol map; 'UNREGISTERED' if unmapped |
| `protocol_family` | string |  | no | artifact protocol: loao, source_internal_loro, loao_negative_control, loao_ot_batch_sensitivity |
| `run_class` | string |  | no | enum: locked, exploratory |
| `mode` | string |  | no | enum: inductive, transductive_batch (run-level information access) |
| `subset_brand` | string |  | yes | brand restriction (e.g. luhua) or null for all samples |
| `preprocessing_version` | string |  | no | e.g. author_v1 |
| `random_seed` | int |  | no | seed from the config |
| `n_samples` | int | samples | no | samples used by the run |
| `config_sha256` | string |  | no | SHA-256 of the resolved config (64 hex) |
| `manifest_sha256` | string |  | no | dataset manifest hash |
| `git_head` | string |  | no | commit of the code that produced the run |
| `git_dirty` | bool |  | no | true if tracked files were modified at run time |
| `utc_time` | datetime | UTC | yes | from the run registry; null for runs that predate it (M2) |
| `is_registered` | bool |  | no | protocol_id comes from the protocol map |
| `is_headline` | bool |  | no | run_class=locked AND is_registered AND NOT git_dirty; only these feed default KPI views |
| `canary_passed` | bool |  | yes | label-shuffle canary result for LOAO runs; null where not applicable |
| `label_convention` | string |  | no | 'olive_fraction = a/(a+b), a = olive parts by volume (ADR-008)' |
| `transductive_warning` | string |  | yes | mandatory wording for transductive runs; null otherwise |
| `limitations_text` | string |  | no | run limitations joined with ' || ' |

### `fact_predictions`

- **Kind:** fact · **Grain:** one row per run x fold x model x held-out sample
- **Primary key:** `run_id`, `fold_id`, `model_key`, `sample_id`
- **Source:** results/<run>/predictions.csv
- **Availability:** `AVAILABLE_M2_M4`
- **Note:** Test labels exist only in evaluation artifacts; this table is never an input to any model.

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `run_id` | string |  | no | FK dim_experiment |
| `fold_id` | string |  | no | FK dim_fold |
| `model_key` | string |  | no | FK dim_model |
| `sample_id` | string |  | no | FK dim_sample |
| `mode` | string |  | no | information access of THIS model in THIS run (svr_no_adaptation is inductive inside a transductive run) |
| `y_true_fraction` | decimal | fraction | no | evaluation label; must equal dim_sample.olive_fraction (validated) |
| `y_pred_fraction` | decimal | fraction | no | UNCLIPPED prediction; may fall outside [0,1] |
| `y_pred_clipped_fraction` | decimal | fraction | no | clip(y_pred, 0, 1); secondary, reference-style scoring only |
| `residual_fraction` | decimal | fraction | no | y_pred - y_true (positive = olive overestimated) |
| `abs_error_fraction` | decimal | fraction | no | |residual| |
| `abs_error_pp` | decimal | percentage points | no | 100 * abs_error_fraction |
| `is_out_of_unit_interval` | bool |  | no | y_pred < 0 or y_pred > 1 |
| `source_sample_hash` | string |  | no | SHA-256 of the source .dat (from predictions.csv) |

### `fact_model_metrics`

- **Kind:** fact · **Grain:** one row per run x model x scope x scoring
- **Primary key:** `run_id`, `model_key`, `scope_type`, `fold_id`, `scoring`
- **Source:** results/<run>/metrics_by_fold.csv and summary.json
- **Availability:** `AVAILABLE_M2_M4`
- **Note:** macro and pooled are different statistics and are never shown under one unlabeled name.

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `run_id` | string |  | no | FK dim_experiment |
| `model_key` | string |  | no | FK dim_model |
| `mode` | string |  | no | information access of the model in this run |
| `scope_type` | string |  | no | enum: fold, macro (unweighted mean over folds), pooled (all held-out predictions) |
| `fold_id` | string |  | yes | FK dim_fold for scope_type=fold; null for macro/pooled |
| `scoring` | string |  | no | enum: unclipped (primary), clipped_to_unit_interval (secondary) |
| `n_samples` | int | samples | no | samples scored (macro: sum over folds) |
| `n_folds` | int | folds | no | 1 for fold rows; number of folds for macro; number of folds pooled |
| `mae_fraction` | decimal | fraction | no | mean absolute error |
| `mae_pp` | decimal | percentage points | no | 100 * mae_fraction |
| `rmse_fraction` | decimal | fraction | no | root mean squared error |
| `bias_fraction` | decimal | fraction | no | mean(pred - true) |
| `r2` | decimal | unitless | yes | coefficient of determination, never clamped; null if undefined |
| `n_out_of_range` | int | predictions | no | predictions outside [0,1] (unclipped scoring) |
| `retention` | decimal | fraction | no | fraction of predictions kept (1.0 until M5 abstention exists) |
| `r2_sd_across_folds` | decimal | unitless | yes | macro rows only |
| `worst_fold_id` | string |  | yes | macro rows only: fold with the largest MAE |
| `worst_fold_mae_fraction` | decimal | fraction | yes | macro rows only |

### `fact_uncertainty`

- **Kind:** fact · **Grain:** one row per run x fold x model x held-out sample (only for runs with an uncertainty experiment)
- **Primary key:** `run_id`, `fold_id`, `model_key`, `sample_id`
- **Source:** M5 artifacts (planned; predictions.csv already reserves abstain, ood_score, interval_lo, interval_hi)
- **Availability:** `PLANNED_M5`
- **Note:** Does not exist until M5 produces it. The exporter must emit zero rows and uncertainty_available=false rather than invent values.

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `run_id` | string |  | no | FK dim_experiment |
| `fold_id` | string |  | no | FK dim_fold |
| `model_key` | string |  | no | FK dim_model |
| `sample_id` | string |  | no | FK dim_sample |
| `mode` | string |  | no | inductive or transductive_batch |
| `abstain` | bool |  | no | research-level review flag; NOT a safety or fraud decision |
| `abstain_reason_code` | string |  | yes | status code, e.g. ABSTAIN_OOD_RISK, INSUFFICIENT_CALIBRATION |
| `ood_score` | decimal | method-specific | yes | proxy score; not an oracle of unseen adulterants |
| `ood_method` | string |  | yes | actual method name (e.g. source-PCA reconstruction residual) |
| `ood_threshold` | decimal | method-specific | yes | threshold value used |
| `threshold_fit_source` | string |  | yes | must state source-only fitting, e.g. 'source_only_out_of_fold'; target labels never allowed |
| `interval_lo_fraction` | decimal | fraction | yes | unclipped lower bound |
| `interval_hi_fraction` | decimal | fraction | yes | unclipped upper bound |
| `interval_width_fraction` | decimal | fraction | yes | hi - lo |
| `interval_method` | string |  | yes | ACTUAL statistical method (e.g. empirical residual quantile from source cross-fitting); never just 'confidence interval' |
| `interval_nominal_level` | decimal | fraction | yes | nominal level, e.g. 0.90; NOT a guarantee under distribution shift |
| `calibration_protocol` | string |  | yes | how calibration residuals were obtained (source-only) |
| `calibration_n` | int | samples | yes | calibration sample count |
| `covered` | bool |  | yes | lo <= y_true <= hi, computed in the exporter from the evaluation label; observed, empirical |
| `status_code` | string |  | yes | taxonomy code from docs/engineering/04_ARCHITECTURE.md |

### `fact_selective_risk`

- **Kind:** fact · **Grain:** one row per run x model x scope x retention target (only for runs with an abstention experiment)
- **Primary key:** `run_id`, `model_key`, `scope_type`, `fold_id`, `retention_target`, `rule_id`
- **Source:** M5 selective_risk.csv (planned; columns follow docs/science/05_EVALUATION_PLAN.md section 7)
- **Availability:** `PLANNED_M5`
- **Note:** Abstention can lower error simply by discarding hard cases; retention must always be shown beside selective error.

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `run_id` | string |  | no | FK dim_experiment |
| `model_key` | string |  | no | FK dim_model |
| `mode` | string |  | no | inductive or transductive_batch; never merged |
| `scope_type` | string |  | no | enum: fold, macro |
| `fold_id` | string |  | yes | FK dim_fold for fold rows |
| `rule_id` | string |  | no | identifier of the preregistered abstention rule |
| `retention_target` | decimal | fraction | no | 1.0, 0.9, 0.8, 0.7 |
| `retention_observed` | decimal | fraction | no | actual fraction retained |
| `rejection_rate` | decimal | fraction | no | 1 - retention_observed |
| `selective_mae_fraction` | decimal | fraction | no | MAE over retained predictions |
| `selective_mae_pp` | decimal | percentage points | no | 100 * selective_mae_fraction |
| `rejected_mae_fraction` | decimal | fraction | yes | retrospective MAE of rejected samples; analysis only |
| `worst_retained_error_fraction` | decimal | fraction | yes | max absolute error among retained |
| `random_reject_mae_fraction_mean` | decimal | fraction | yes | random-abstention control, mean over seeded repeats |
| `random_reject_mae_fraction_sd` | decimal | fraction | yes | random-abstention control, sd |
| `n_random_repeats` | int | repeats | yes | number of seeded repeats |

### `fact_data_quality`

- **Kind:** fact · **Grain:** one row per validated spectrum
- **Primary key:** `sample_id`
- **Source:** data/interim/sample_manifest.csv and M1 qc_summary.csv/data_audit.json
- **Availability:** `AVAILABLE_M1`

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `sample_id` | string |  | no | FK dim_sample |
| `qc_status` | string |  | no | enum: PASS, WARN, FAIL |
| `qc_flags` | string |  | yes | ';'-separated flags, e.g. NEGATIVE_INTENSITY |
| `excitation_channels` | int | channels | no | 35 expected |
| `emission_channels` | int | channels | no | 270 expected |
| `expected_cells` | int | cells | no | reference value 35 x 270 = 9450 |
| `finite_cells` | int | cells | no | cells with finite intensity |
| `spectral_completeness` | decimal | fraction | no | finite_cells / expected_cells in [0,1] |
| `negative_cells` | int | cells | no | cells with intensity < 0 (kept raw, flagged) |
| `intensity_min` | decimal | Counts/uA | no | minimum raw intensity |
| `intensity_max` | decimal | Counts/uA | no | maximum raw intensity |
| `is_constant_signal` | bool |  | no | constant spectrum (QC FAIL) |
| `is_duplicate_content` | bool |  | no | another sample has the same source SHA-256 |
| `axis_matches_reference` | bool |  | no | wavelength axes identical to the reference axes |
| `source_excitation_order` | string |  | no | order found in the file (descending in the current data); reordered by one recorded rule |
| `normalization_factor` | decimal |  | no | 'Normalized by' header value |
| `parser_version` | string |  | no | parser version |

### `fact_data_issues`

- **Kind:** fact · **Grain:** one row per rejected file, discrepancy or informational audit note
- **Primary key:** `issue_id`
- **Source:** M1 data_audit.json (problems, discrepancy_ledger, extra_duplicate_copy_files)
- **Availability:** `AVAILABLE_M1`
- **Note:** An empty table is a legitimate result (zero rejected files) and must be shown as 0, never hidden.

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `issue_id` | string |  | no | stable ID: sha256 of (severity, path_rel, description)[:16] |
| `severity` | string |  | no | enum: REJECTED_FILE, DISCREPANCY, INFORMATIONAL |
| `path_rel` | string |  | yes | path relative to the dataset root, Unicode NFC; never an absolute path |
| `description` | string |  | no | audit text |
| `audit_source` | string |  | no | problems | discrepancy_ledger | extra_duplicate_copy_files |
| `manifest_sha256` | string |  | no | manifest the audit belongs to |

### `fact_ot_diagnostics`

- **Kind:** fact · **Grain:** one row per run x fold x transductive model
- **Primary key:** `run_id`, `fold_id`, `model_key`
- **Source:** results/<run>/ot_diagnostics.csv (M4)
- **Availability:** `AVAILABLE_M4`

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `run_id` | string |  | no | FK dim_experiment |
| `fold_id` | string |  | no | FK dim_fold |
| `model_key` | string |  | no | FK dim_model |
| `solver` | string |  | no | sinkhorn_log_domain, pot_sinkhorn, pca_source_plus_target_X, none |
| `epsilon` | decimal | cost units | yes | entropic regularization |
| `n_source` | int | samples | no | source batch size |
| `n_target` | int | samples | no | unlabeled target batch size |
| `n_iter` | int | iterations | yes | solver iterations (POT value is an estimate from its error log) |
| `converged` | bool |  | yes | recorded honestly; false rows are shown, never dropped |
| `pot_nonconvergence_warning` | bool |  | yes | POT warned about non-convergence |
| `row_marginal_l1` | decimal |  | yes | L1 error of source marginal |
| `col_marginal_l1` | decimal |  | yes | L1 error of target marginal |
| `col_marginal_sq_l2` | decimal |  | yes | stopping statistic (squared L2 of target-marginal error) |
| `total_mass` | decimal |  | yes | transported mass, should be 1 |
| `cost_min` | decimal | Euclidean distance | yes | minimum cost entry |
| `cost_median` | decimal | Euclidean distance | yes | median cost entry |
| `cost_max` | decimal | Euclidean distance | yes | maximum cost entry |
| `n_components` | int | components | yes | PCA size for published-style PCA baselines |
| `mode` | string |  | no | information access of this model |

### `fact_robustness`

- **Kind:** fact · **Grain:** one row per run x stress type x fold x batch kind x model (or per control model)
- **Primary key:** `run_id`, `stress_type`, `fold_id`, `batch_kind`, `model_key`
- **Source:** M3 control_summary.json, M4 batch_sensitivity.json, M5 perturbation results (planned)
- **Availability:** `AVAILABLE_M3_M4_PLANNED_M5`
- **Note:** Always exploratory. Scores describe the stress batch, not a full fold.

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `run_id` | string |  | no | FK dim_experiment (an exploratory run) |
| `stress_type` | string |  | no | enum: permuted_source_labels, batch_size, batch_brand, batch_label_skew, synthetic_perturbation |
| `fold_id` | string |  | yes | FK dim_fold; null for controls summarized over folds |
| `batch_kind` | string |  | yes | random_10, random_20, brand_<key>, skew_low_olive, skew_high_olive, ... |
| `model_key` | string |  | no | FK dim_model |
| `mode` | string |  | no | information access |
| `n_batches` | int | batches | yes | number of batches or permutation repeats |
| `n_failed` | int | batches | yes | batches that raised an error |
| `mae_fraction_mean` | decimal | fraction | yes | mean MAE over batches |
| `mae_fraction_max` | decimal | fraction | yes | worst MAE over batches |
| `r2_mean` | decimal | unitless | yes | mean R2 over batches (or mean macro R2 for controls) |
| `r2_min` | decimal | unitless | yes | worst R2 over batches |
| `scored_on` | string |  | no | what the numbers describe, e.g. 'the stress batch itself' or 'true held-out labels' |

### `fact_published_reference`

- **Kind:** fact · **Grain:** one row per published number used for comparison
- **Primary key:** `reference_id`
- **Source:** published values recorded in docs/science/02_RESEARCH_PROTOCOL.md and the M3/M4 reports
- **Availability:** `AVAILABLE_M4`
- **Note:** No relationship to fact_model_metrics. Visuals must show it in its own labeled area.

| Column | Type | Unit | Nullable | Meaning / validation |
|---|---|---|---|---|
| `reference_id` | string |  | no | e.g. sun2026_raw_mean_r2 |
| `source_doi` | string |  | no | 10.1038/s41538-026-01037-6 |
| `model_label` | string |  | no | the authors' column name (e.g. 'PARAFAC') |
| `metric` | string |  | no | mean_r2 over five LOAO systems |
| `value` | decimal | unitless | no | published number |
| `sd` | decimal | unitless | yes | published sd if given |
| `is_measured` | bool |  | no | ALWAYS false: published, not measured by ChemiProof |
| `comparable_model_key` | string |  | yes | our closest model, for display pairing only; never joined into metrics |
| `caveat` | string |  | no | e.g. 'authors clip predictions to [0,1]' |

## 4. Protocol and model identity

**Rule P-1.** Every fact row can be traced to exactly one `dim_experiment` row and one `dim_model` row; `mode` is stored on the fact because a transductive run also contains an inductive control (`svr_no_adaptation`).

**Rule P-2.** `protocol_id` is assigned by the exporter from a versioned protocol map. Initial entries, derived from the artifacts that exist (2026-11-03):

| Artifact protocol (`protocol_family`) | mode | run class | `protocol_id` | Accepted `config_sha256` (observed) | Meaning |
|---|---|---|---|---|---|
| `source_internal_loro` | inductive | any | `SI-LORO-v1` | `5ddb4697c349f887` | leave-one-measurement-round-out; OPTIMISTIC, not unseen-adulterant evidence |
| `loao` | inductive | locked | `LOAO-v1` | `2c427bf82704fa93` (all 330), `c98da7473d7088d3` (Luhua-only) | frozen five-fold held-out-adulterant benchmark (ADR-013) |
| `loao` | transductive_batch | locked | `LOAO-OT-v1` | `417e41b5b3029099` (all 330), `70f0c2f5af843fb8` (Luhua-only) | frozen OT benchmark, needs an unlabeled batch (ADR-014) |
| `loao_negative_control` | inductive | exploratory | `LOAO-v1/negative-control` | n/a | permuted-source-label control |
| `loao_ot_batch_sensitivity` | transductive_batch | exploratory | `LOAO-OT-v1/batch-stress` | n/a | batch size, brand and label-skew stress tests (ADR-014/015) |
| `loao` | any | exploratory | `EXPLORATORY` | any | never headline |
| anything else, or a locked run whose `config_sha256` is not accepted | | | `UNREGISTERED` | | exported with `is_registered=false`, excluded from default views |

Registering a new protocol or run requires an ADR and owner approval. The M2 run predates `results/experiment_registry.csv`, so the exporter must also be able to read `summary.json` and `config_resolved.yaml` directly; registry fields missing for such runs are null.

**Rule P-3 (no mixing).** Headline KPIs use exactly one run. Any visual that shows several runs, protocols or modes must display `protocol_id`, `mode`, `run_class` and `subset_brand` as visible fields. Published numbers (`fact_published_reference`) are never placed in the same axis series as measured values without the label "published, not measured by ChemiProof".

**Rule P-4 (clipping and aggregation labels).** `scoring` (unclipped primary / clipped secondary) and `scope_type` (fold / macro / pooled) must be visible wherever a metric is shown.

## 5. Relationships

All relationships are active, single-direction (dimension filters fact), many-to-one unless stated.

| One side | Many side | Cardinality | Filter direction |
|---|---|---|---|
| `dim_experiment[run_id]` | `fact_predictions[run_id]` | 1:* | single (dim -> fact) |
| `dim_experiment[run_id]` | `fact_model_metrics[run_id]` | 1:* | single |
| `dim_experiment[run_id]` | `fact_uncertainty[run_id]` | 1:* | single |
| `dim_experiment[run_id]` | `fact_selective_risk[run_id]` | 1:* | single |
| `dim_experiment[run_id]` | `fact_ot_diagnostics[run_id]` | 1:* | single |
| `dim_experiment[run_id]` | `fact_robustness[run_id]` | 1:* | single |
| `dim_model[model_key]` | `fact_predictions[model_key]` | 1:* | single |
| `dim_model[model_key]` | `fact_model_metrics[model_key]` | 1:* | single |
| `dim_model[model_key]` | `fact_uncertainty[model_key]` | 1:* | single |
| `dim_model[model_key]` | `fact_selective_risk[model_key]` | 1:* | single |
| `dim_model[model_key]` | `fact_ot_diagnostics[model_key]` | 1:* | single |
| `dim_model[model_key]` | `fact_robustness[model_key]` | 1:* | single |
| `dim_fold[fold_id]` | `fact_predictions[fold_id]` | 1:* | single |
| `dim_fold[fold_id]` | `fact_model_metrics[fold_id]` | 1:* | single (null fold_id for macro/pooled rows) |
| `dim_fold[fold_id]` | `fact_uncertainty[fold_id]` | 1:* | single |
| `dim_fold[fold_id]` | `fact_ot_diagnostics[fold_id]` | 1:* | single |
| `dim_fold[fold_id]` | `fact_robustness[fold_id]` | 1:* | single |
| `dim_sample[sample_id]` | `fact_predictions[sample_id]` | 1:* | single |
| `dim_sample[sample_id]` | `fact_uncertainty[sample_id]` | 1:* | single |
| `dim_sample[sample_id]` | `fact_data_quality[sample_id]` | 1:1 | single |
| `dim_adulterant[adulterant_key]` | `dim_sample[adulterant_key]` | 1:* | single |
| `dim_brand[brand_key]` | `dim_sample[brand_key]` | 1:* | single |

Not related: `fact_published_reference` and `fact_data_issues` (standalone, labeled areas); `dim_fold.target_adulterant` is a text attribute, not a relationship, to avoid an ambiguous second path to `dim_adulterant` (use `dim_sample[adulterant_key]` for sample-level views and `dim_fold[target_adulterant]` for fold-level views). `fact_selective_risk` may relate to `dim_fold` for fold rows; macro rows carry a null `fold_id`.

## 6. Validation rules (applied by the exporter before writing; each failure aborts the export)

| ID | Rule |
|---|---|
| V-01 | Every table matches `config/bi/export_contract.yaml` (names, order, types, nullability). |
| V-02 | Primary keys are unique and non-null; foreign keys resolve (referential integrity), including `fact_predictions.sample_id` in `dim_sample`. |
| V-03 | `olive_fraction` and `y_true_fraction` are in [0,1]; `y_true_fraction` equals `dim_sample.olive_fraction` for the same sample; `olive_percent = 100 x olive_fraction`; every `*_pp` column equals `100 x` its fraction column (tolerance 1e-9). |
| V-04 | `residual_fraction = y_pred_fraction - y_true_fraction`; `abs_error_fraction = |residual|`; `y_pred_clipped = clip(y_pred, 0, 1)`; `is_out_of_unit_interval` consistent. |
| V-05 | Reconciliation: metrics recomputed from `fact_predictions` equal `fact_model_metrics` (fold, macro, pooled; both scorings) within 1e-9 (MAE/RMSE/bias) and 1e-9 (R2). |
| V-06 | Every run in the export has a complete provenance set (`config_sha256`, `manifest_sha256`, `git_head`, `git_dirty`); locked runs with `git_dirty=true` are exported with `is_headline=false` and a warning. |
| V-07 | LOAO runs must carry `canary_passed=true` and the fold audit checks; a run without them is rejected (leakage guard). |
| V-08 | Each (run, model) in `fact_predictions` covers every held-out sample of its folds exactly once; fold sizes match the run's fold manifest. |
| V-09 | Uncertainty tables must state `interval_method`, `interval_nominal_level`, `calibration_protocol` and `threshold_fit_source`; thresholds fitted on target labels are rejected; if M5 outputs are absent the tables are empty and `uncertainty_available=false`. |
| V-10 | No absolute filesystem paths, user names or e-mail addresses appear in any exported column. |
| V-11 | `fact_published_reference.is_measured` is false for every row. |
| V-12 | The export contains no spectral intensity arrays and the dataset directory hash before and after the export is identical. |

## 7. KPI catalog

All KPIs are defined for a **single selected run** unless the row says otherwise. "Python recompute" names the check that must reproduce the Power BI value from the same export (see `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`, BI021).

| ID | KPI | Definition | Unit | Source | Notes |
|---|---|---|---|---|---|
| K01 | Total samples | count of `dim_sample` rows | samples | `dim_sample` | reference expectation 330 shown beside, labeled "published expectation" |
| K02 | Samples by adulterant | count by `adulterant_key`, next to `expected_samples` | samples | `dim_sample`, `dim_adulterant` | gap = expected - observed |
| K03 | Samples by brand | count by `brand_key` | samples | `dim_sample` | brand imbalance is a confounder |
| K04 | Olive concentration distribution | count by `olive_percent` level | samples | `dim_sample` | x axis in percent; ten levels (9.09 to 90.91) |
| K05 | Spectral completeness | mean of `spectral_completeness`; share of samples at 1.0 | fraction | `fact_data_quality` | |
| K06 | Rejected files / invalid samples | count of `fact_data_issues` with severity `REJECTED_FILE` | files | `fact_data_issues` | zero is shown as 0 |
| K07 | QC status mix | count by `qc_status` and by flag | samples | `fact_data_quality` | currently NEGATIVE_INTENSITY is a WARN, not an error |
| K08 | Duplicate content | count of `is_duplicate_content` | samples | `fact_data_quality` | |
| K09 | MAE | pooled: mean `abs_error_pp`; macro: `fact_model_metrics` macro row | percentage points | `fact_predictions` / `fact_model_metrics` | label pooled vs macro; unclipped primary |
| K10 | RMSE | pooled: sqrt(mean residual^2) | fraction | `fact_predictions` | also shown in pp (x100) |
| K11 | Bias | mean residual | fraction (pp) | `fact_predictions` | positive = olive overestimated |
| K12 | R2 | pooled: 1 - SSres/SStot; macro: mean of fold R2 | unitless | `fact_predictions` / `fact_model_metrics` | never clamped; can be negative |
| K13 | R2 spread and worst fold | sd of fold R2; fold with largest MAE | unitless, fold id | `fact_model_metrics` | five folds only |
| K14 | Out-of-range predictions | count of `is_out_of_unit_interval` | predictions | `fact_predictions` | |
| K15 | Observed interval coverage | covered / intervals | fraction | `fact_uncertainty` | EMPIRICAL on this run's held-out samples; not a guarantee under shift |
| K16 | Mean interval width | mean `interval_width_fraction` | fraction (pp) | `fact_uncertainty` | |
| K17 | Abstention rate and retention | abstain / rows; 1 - rate | fraction | `fact_uncertainty` | a research cue, not a decision |
| K18 | Selective MAE | MAE over retained predictions with retention beside it | percentage points | `fact_selective_risk` | always shown with the random-abstain control |
| K19 | Review-required samples | count of `abstain=true` | samples | `fact_uncertainty` | wording: "review required", never "adulterated" |
| K20 | OT convergence | converged folds / folds | fraction | `fact_ot_diagnostics` | non-converged rows are shown |
| K21 | Stress-test MAE | `mae_fraction_mean` by `batch_kind` next to the no-adaptation control | percentage points | `fact_robustness` | scores describe the stress batch only |

## 8. DAX measure catalog (DRAFT, NOT EXECUTED)

These drafts define intent. They have **not** been run in Power BI. Each must pass reconciliation (BI021) before use. Names use the prefix `m_`.

```dax
// Guard: exactly one run, one mode (per visible model) is selected
m_RunGuardOK =
VAR runs  = DISTINCTCOUNT ( dim_experiment[run_id] )
RETURN runs = 1

m_Samples = COUNTROWS ( dim_sample )

m_MAE_pp_pooled =
IF ( [m_RunGuardOK], AVERAGE ( fact_predictions[abs_error_pp] ) )

m_Bias_fraction_pooled =
IF ( [m_RunGuardOK], AVERAGE ( fact_predictions[residual_fraction] ) )

m_RMSE_fraction_pooled =
IF ( [m_RunGuardOK],
     SQRT ( AVERAGEX ( fact_predictions, fact_predictions[residual_fraction] ^ 2 ) ) )

m_R2_pooled =
VAR ymean = AVERAGE ( fact_predictions[y_true_fraction] )
VAR ssres = SUMX ( fact_predictions, fact_predictions[residual_fraction] ^ 2 )
VAR sstot = SUMX ( fact_predictions, ( fact_predictions[y_true_fraction] - ymean ) ^ 2 )
RETURN IF ( [m_RunGuardOK] && sstot > 0, 1 - DIVIDE ( ssres, sstot ) )

// macro metrics are read from the stored macro rows (unweighted mean over folds)
m_MAE_pp_macro =
IF ( [m_RunGuardOK],
     CALCULATE ( MAX ( fact_model_metrics[mae_pp] ),
                 fact_model_metrics[scope_type] = "macro",
                 fact_model_metrics[scoring] = "unclipped" ) )

m_ObservedCoverage =
VAR withInterval = FILTER ( fact_uncertainty, NOT ISBLANK ( fact_uncertainty[covered] ) )
RETURN IF ( [m_RunGuardOK], DIVIDE ( COUNTROWS ( FILTER ( withInterval, fact_uncertainty[covered] = TRUE () ) ),
                                      COUNTROWS ( withInterval ) ) )

m_AbstentionRate =
IF ( [m_RunGuardOK],
     DIVIDE ( COUNTROWS ( FILTER ( fact_uncertainty, fact_uncertainty[abstain] = TRUE () ) ),
              COUNTROWS ( fact_uncertainty ) ) )

m_SelectiveMAE_pp_retained =
IF ( [m_RunGuardOK],
     AVERAGEX ( FILTER ( fact_uncertainty, fact_uncertainty[abstain] = FALSE () ),
                CALCULATE ( MAX ( fact_predictions[abs_error_pp] ) ) ) )
```

Rules for every measure: return BLANK (not zero) when the selection is ambiguous or the underlying table is empty; never hide a zero count of rejected files; no hard-coded numbers; no thresholds that are not defined in the Python pipeline.

## 9. Refresh and versioning

- The report reads one export folder through a Power Query parameter `ExportFolder`. A query step reads `export_manifest.json` and stops with a visible error if `contract_version` differs from the version the report was built for.
- Refresh = run the exporter again (new `<export_id>`), point `ExportFolder` to it, refresh. No gateway, scheduled refresh or cloud publishing is assumed.
- A contract change increments `contract_version` and requires an ADR. Old exports are kept immutable.
