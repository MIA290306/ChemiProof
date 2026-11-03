# M2 Preprocessing and first models: validation report

**Date:** 2026-11-02 · **Run ID:** `20261103T041143Z_ca43062_4097e86f` (git `ca43062`, dirty=False) · config sha256 `5ddb4697c349f887...` · manifest sha256 `31c718edd95b4fac...`
**Protocol:** `source_internal_loro` = leave one MEASUREMENT ROUND out over all 330 spectra (3 folds, n=110 each), inductive.
**READ THIS FIRST:** this protocol is **optimistic by construction** (the held-out round shares brand/adulterant/ratio cells with the training rounds). These numbers are **not** evidence of unseen-adulterant generalization; that is M3 (LOAO). No published number appears in this table; all values are ChemiProof measurements.

## Commands actually run

| Command | Exit | Result |
|---|---|---|
| `chemiproof experiment run --config config/experiments/m2_source_internal.yaml` | 0 | artifacts in `results/M2_20261103T041143Z_ca43062_4097e86f/` |
| `chemiproof spectra compare --output results/M2_20261103T041143Z_ca43062_4097e86f/preprocessing_before_after.png` | 0 | raw vs processed EEM (PNG git-ignored) |
| `pytest -q` (all, incl. real-data tests) | 0 | 124 passed |
| `pytest -q -m "not dataset"` | 0 | 120 passed, 4 deselected |
| `ruff check .` / `ruff format --check .` | 0 / 0 | clean |

## Preprocessing `author_v1` (prespecified from the published code, ADR-011; not tuned on any labels)

Steps: subtract global minimum of the EEM; Savitzky-Golay(window 5, polyorder 2) along the emission axis; divide by global maximum; flatten to 9,450 features (35 x 270). Every step is per-spectrum, nothing is fitted, so it cannot leak between samples. Label scale: y = olive volume fraction in [0, 1]; the reference SVR epsilon 0.1 = 0.1 fraction (10 percentage points).

## Results (units: MAE in percentage points = 100 x fraction; RMSE/bias in fraction; R2 unitless)

### Macro over the 3 folds (unweighted) and pooled counts

| model | macro MAE (pp) | macro RMSE | macro bias | macro R2 (sd over folds) | worst-fold MAE (pp) | pooled out of [0,1] |
|---|---:|---:|---:|---:|---:|---:|
| mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 (0.000) | 22.73 | 0 |
| svr_raw | 5.10 | 0.0603 | -0.0183 | 0.947 (0.003) | 5.26 | 4 |
| pca_svr | 7.09 | 0.0814 | +0.0125 | 0.903 (0.002) | 7.12 | 9 |
| pls | 1.37 | 0.0175 | -0.0002 | 0.996 (0.000) | 1.40 | 0 |

### Per fold

| fold | model | n | MAE (pp) | RMSE (fraction) | bias (fraction) | R2 | out of [0,1] |
|---|---|---:|---:|---:|---:|---:|---:|
| SI-round1 | mean_y | 110 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| SI-round1 | svr_raw | 110 | 5.26 | 0.0618 | -0.0235 | 0.944 | 2 |
| SI-round1 | pca_svr | 110 | 7.07 | 0.0813 | +0.0081 | 0.903 | 3 |
| SI-round1 | pls | 110 | 1.37 | 0.0175 | -0.0052 | 0.996 | 0 |
| SI-round2 | mean_y | 110 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| SI-round2 | svr_raw | 110 | 4.95 | 0.0584 | -0.0171 | 0.950 | 1 |
| SI-round2 | pca_svr | 110 | 7.09 | 0.0802 | +0.0120 | 0.906 | 2 |
| SI-round2 | pls | 110 | 1.40 | 0.0179 | +0.0035 | 0.995 | 0 |
| SI-round3 | mean_y | 110 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| SI-round3 | svr_raw | 110 | 5.10 | 0.0609 | -0.0144 | 0.946 | 1 |
| SI-round3 | pca_svr | 110 | 7.12 | 0.0825 | +0.0173 | 0.900 | 4 |
| SI-round3 | pls | 110 | 1.32 | 0.0172 | +0.0009 | 0.996 | 0 |

Selected hyperparameters (inner CV on training rounds only): SI-round1 pca_svr=20; SI-round1 pls=24; SI-round2 pca_svr=40; SI-round2 pls=16; SI-round3 pca_svr=80; SI-round3 pls=24.

### Descriptive per-adulterant MAE (pp), pooled over the 3 held-out rounds

Descriptive only: the adulterants were present in training, so this is not LOAO.

| model | soybean | peanut | rapeseed | corn | walnut |
|---|---:|---:|---:|---:|---:|
| mean_y | 22.73 | 22.73 | 22.73 | 22.73 | 22.73 |
| svr_raw | 5.41 | 6.18 | 5.21 | 4.54 | 3.72 |
| pca_svr | 7.48 | 8.13 | 6.61 | 6.70 | 6.85 |
| pls | 1.22 | 1.40 | 1.46 | 1.31 | 1.47 |

## Acceptance tests

| ID | Status | Evidence |
|---|---|---|
| T007 preprocess a synthetic known EEM | PASS | `tests/unit/test_preprocess.py` |
| T008 fit never touches test rows / test groups | PASS | `tests/unit/test_baselines_leakage.py` (spy estimator; PCA mean equals training mean) |
| T009 metrics equal hand calculation | PASS | `tests/unit/test_metrics.py` |
| T011 changing held-out labels cannot change that fold's predictions | PASS (for the M2 protocol) | `test_t011_...` |
| T024 permuted source labels degrade the benchmark | PASS (synthetic) | `test_t024_...` |
| Synthetic benchmark learns; mean_y floor R2 about 0 | PASS | `test_synthetic_benchmark_...` |
| Real-data run is structurally valid and deterministic | PASS | `tests/integration/test_real_dataset.py::test_m2_source_internal_run_on_real_data` |
| T010, T012-T023 | NOT RUN | M3 onwards |
| GitHub Actions for the M2 commits | NOT RUN | needs push |

## Adverse observations and limitations

1. **Grid history (ADR-012):** with the first grids, PLS picked its largest candidate in 3/3 folds (macro MAE then: pls 1.98 pp, pca_svr 7.08 pp, svr_raw 5.10 pp). Grids were widened using inner CV only; the final numbers above come from the wider grids. M2 scores are therefore exploratory-development numbers; M3 must freeze the protocol before scoring any held-out adulterant. In the final run, pca_svr picked 80 components (its upper bound) in one fold.
2. `svr_raw` (paper-fixed) has a negative bias of about -1.8 pp and produced a few out-of-range predictions (scored unclipped; clipping changes nothing material here).
3. PCA-SVR is worse than raw SVR here; plausible reasons (unscaled PCA on max-normalized spectra, fixed SVR parameters) were not investigated.
4. Round is probably, but not provably, a replicate; brand imbalance is an uncontrolled confounder; no brand-wise result is claimed.
5. The 3-fold macro spread (R2 sd about 0.001-0.003) reflects only 3 rounds of the same cells, not uncertainty about new adulterants.
