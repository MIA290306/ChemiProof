# M3 Five-domain LOAO benchmark: validation report

**Date:** 2026-11-02 · **Protocol:** `LOAO-v1`, frozen by ADR-013 before any scored run · inductive mode only (no OT, no abstention)
**Locked runs:** all 330 samples `M3_20261103T042740Z_01a9d42_b1c2dfa1` (config `2c427bf82704fa93...`) and Luhua-only sensitivity `M3_20261103T042759Z_01a9d42_2fbd19b6` (config `c98da7473d7088d3...`). Both ran from git `01a9d42` with a clean tracked tree (`dirty=False`/`False`); every run is listed in `results/experiment_registry.csv`.
**Manifest:** sha256 `31c718edd95b4fac...` (330 spectra, 35x270, preprocessing `author_v1`).
**Question answered:** how well do source-only models trained on four adulterants predict the olive fraction of a wholly unseen fifth adulterant? Units: MAE in percentage points (pp) = 100 x fraction; RMSE/bias in fraction; R2 unitless and never clamped; primary scoring is UNCLIPPED.

## Commands actually run

| Command | Exit | Result |
|---|---|---|
| `chemiproof experiment run --config config/experiments/baseline.yaml` (locked) | 0 | `M3_20261103T042740Z_01a9d42_b1c2dfa1` |
| `chemiproof experiment run --config config/experiments/loao_luhua_only.yaml` (locked) | 0 | `M3_20261103T042759Z_01a9d42_2fbd19b6` |
| `chemiproof experiment control --config config/experiments/baseline.yaml` / `loao_luhua_only.yaml` (exploratory) | 0 / 0 | `M3_control_20261103T043013Z_932d990_9a3dc967`, `M3_control_20261103T043022Z_932d990-dirty_b1d73c83` |
| `pytest -q -m "not dataset"` | 0 | 140 passed |
| `pytest -q -m dataset` (real data) | 0 | 6 passed (structure/determinism only) |
| `ruff check .` / `ruff format --check .` | 0 / 0 | clean |

Frozen-file hashes (ADR-013) re-checked after the runs: unchanged.

## Fold design and leakage audit (independent re-check from the manifest)

| fold | n_test | n_train | train adulterants | test brands | test brands absent from train |
|---|---:|---:|---|---|---|
| LOAO-soybean | 60 | 270 | corn, peanut, rapeseed, walnut | {'luhua': 30, 'olivera': 30} | none |
| LOAO-peanut | 60 | 270 | corn, rapeseed, soybean, walnut | {'luhua': 30, 'olivera': 30} | none |
| LOAO-rapeseed | 90 | 240 | corn, peanut, soybean, walnut | {'earl_grey': 30, 'luhua': 30, 'olivera': 30} | none |
| LOAO-corn | 90 | 240 | peanut, rapeseed, soybean, walnut | {'earl_grey': 30, 'luhua': 30, 'olivera': 30} | none |
| LOAO-walnut | 30 | 300 | corn, peanut, rapeseed, soybean | {'luhua': 30} | none |

Audit checks (all hold): each test set is exactly one adulterant; the target adulterant is absent from train; train/test sample IDs are disjoint; every sample is tested exactly once; fold sizes equal the published 60/60/90/90/30. **Label-shuffle canary** (held-out labels of each fold shuffled, refit, predictions and selected hyper-parameters identical for every model): passed for all 5 folds in both locked runs.

## Results, all 330 samples (primary)

| model | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 min..max over folds | worst fold by MAE | pooled R2 | pooled out of [0,1] |
|---|---:|---:|---:|---:|---|---|---:|---:|
| mean_y | 22.73 | 0.2611 | -0.0000 | -0.000 | -0.000 .. 0.000 | walnut | 0.000 | 0 |
| svr_raw | 8.37 | 0.1005 | +0.0136 | 0.831 | 0.601 .. 0.948 | rapeseed | 0.815 | 1 |
| pca_svr | 16.55 | 0.2346 | +0.0979 | 0.019 | -1.189 .. 0.813 | soybean | -0.127 | 30 |
| pls | 6.50 | 0.0775 | +0.0075 | 0.903 | 0.773 .. 0.954 | soybean | 0.909 | 0 |

Selected hyper-parameters (inner leave-one-source-adulterant-out CV): soybean pca_svr=5; soybean pls=4; peanut pca_svr=10; peanut pls=6; rapeseed pca_svr=20; rapeseed pls=4; corn pca_svr=20; corn pls=6; walnut pca_svr=5; walnut pls=6.

### Per fold (all 330)

| fold | n | model | MAE (pp) | RMSE | bias | R2 | out of [0,1] |
|---|---:|---|---:|---:|---:|---:|---:|
| LOAO-soybean | 60 | mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-soybean | 60 | svr_raw | 9.47 | 0.1189 | +0.0691 | 0.793 | 1 |
| LOAO-soybean | 60 | pca_svr | 26.18 | 0.3382 | +0.2455 | -0.677 | 12 |
| LOAO-soybean | 60 | pls | 10.75 | 0.1245 | +0.1042 | 0.773 | 0 |
| LOAO-peanut | 60 | mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-peanut | 60 | svr_raw | 7.05 | 0.0750 | -0.0235 | 0.918 | 0 |
| LOAO-peanut | 60 | pca_svr | 12.06 | 0.1365 | +0.0311 | 0.727 | 9 |
| LOAO-peanut | 60 | pls | 4.78 | 0.0560 | +0.0109 | 0.954 | 0 |
| LOAO-rapeseed | 90 | mean_y | 22.73 | 0.2611 | -0.0000 | -0.000 | 0 |
| LOAO-rapeseed | 90 | svr_raw | 12.97 | 0.1649 | +0.0974 | 0.601 | 0 |
| LOAO-rapeseed | 90 | pca_svr | 15.53 | 0.1990 | +0.0735 | 0.419 | 0 |
| LOAO-rapeseed | 90 | pls | 4.79 | 0.0636 | +0.0191 | 0.941 | 0 |
| LOAO-corn | 90 | mean_y | 22.73 | 0.2611 | -0.0000 | -0.000 | 0 |
| LOAO-corn | 90 | svr_raw | 5.14 | 0.0596 | -0.0435 | 0.948 | 0 |
| LOAO-corn | 90 | pca_svr | 19.28 | 0.3863 | +0.1161 | -1.189 | 6 |
| LOAO-corn | 90 | pls | 5.20 | 0.0637 | -0.0271 | 0.940 | 0 |
| LOAO-walnut | 30 | mean_y | 22.73 | 0.2611 | +0.0000 | 0.000 | 0 |
| LOAO-walnut | 30 | svr_raw | 7.23 | 0.0843 | -0.0314 | 0.896 | 0 |
| LOAO-walnut | 30 | pca_svr | 9.70 | 0.1128 | +0.0232 | 0.813 | 3 |
| LOAO-walnut | 30 | pls | 6.99 | 0.0798 | -0.0697 | 0.907 | 0 |

## Sensitivity: Luhua-only (brand present for all five adulterants; 30 per adulterant)

| model | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 min..max over folds | worst fold by MAE | pooled R2 | pooled out of [0,1] |
|---|---:|---:|---:|---:|---|---|---:|---:|
| mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0.000 .. 0.000 | soybean | 0.000 | 0 |
| svr_raw | 6.95 | 0.0833 | -0.0023 | 0.859 | 0.501 .. 0.968 | rapeseed | 0.859 | 0 |
| pca_svr | 13.56 | 0.1999 | +0.0206 | 0.301 | -0.694 .. 0.820 | soybean | 0.301 | 14 |
| pls | 8.64 | 0.1009 | +0.0264 | 0.828 | 0.535 .. 0.935 | rapeseed | 0.828 | 3 |

### Per fold (Luhua-only)

| fold | n | model | MAE (pp) | RMSE | bias | R2 | out of [0,1] |
|---|---:|---|---:|---:|---:|---:|---:|
| LOAO-soybean | 30 | mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-soybean | 30 | svr_raw | 4.17 | 0.0481 | +0.0212 | 0.966 | 0 |
| LOAO-soybean | 30 | pca_svr | 19.36 | 0.3399 | +0.1563 | -0.694 | 3 |
| LOAO-soybean | 30 | pls | 8.04 | 0.0887 | +0.0801 | 0.885 | 0 |
| LOAO-peanut | 30 | mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-peanut | 30 | svr_raw | 7.03 | 0.0740 | -0.0703 | 0.920 | 0 |
| LOAO-peanut | 30 | pca_svr | 16.00 | 0.2521 | -0.1329 | 0.068 | 6 |
| LOAO-peanut | 30 | pls | 8.19 | 0.0937 | -0.0819 | 0.871 | 3 |
| LOAO-rapeseed | 30 | mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-rapeseed | 30 | svr_raw | 13.91 | 0.1845 | +0.1164 | 0.501 | 0 |
| LOAO-rapeseed | 30 | pca_svr | 13.46 | 0.1859 | +0.0923 | 0.493 | 0 |
| LOAO-rapeseed | 30 | pls | 13.75 | 0.1781 | +0.1372 | 0.535 | 0 |
| LOAO-corn | 30 | mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-corn | 30 | svr_raw | 5.80 | 0.0628 | -0.0541 | 0.942 | 0 |
| LOAO-corn | 30 | pca_svr | 9.75 | 0.1108 | +0.0238 | 0.820 | 0 |
| LOAO-corn | 30 | pls | 6.24 | 0.0664 | +0.0624 | 0.935 | 0 |
| LOAO-walnut | 30 | mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-walnut | 30 | svr_raw | 3.84 | 0.0471 | -0.0244 | 0.968 | 0 |
| LOAO-walnut | 30 | pca_svr | 9.23 | 0.1111 | -0.0365 | 0.819 | 5 |
| LOAO-walnut | 30 | pls | 7.00 | 0.0776 | -0.0659 | 0.912 | 0 |

## Brand analysis (descriptive, all-330 run, error inside each held-out fold)

| held-out | brand | n | svr_raw MAE (pp) / bias | pls MAE (pp) / bias |
|---|---|---:|---|---|
| soybean | luhua | 30 | 4.7 / +0.000 | 7.9 / +0.072 |
| soybean | olivera | 30 | 14.3 / +0.138 | 13.6 / +0.136 |
| peanut | luhua | 30 | 8.1 / -0.081 | 3.6 / -0.018 |
| peanut | olivera | 30 | 6.0 / +0.034 | 5.9 / +0.040 |
| rapeseed | earl_grey | 30 | 13.0 / +0.084 | 6.0 / -0.002 |
| rapeseed | luhua | 30 | 12.7 / +0.080 | 4.3 / +0.033 |
| rapeseed | olivera | 30 | 13.3 / +0.128 | 4.0 / +0.025 |
| corn | earl_grey | 30 | 6.0 / -0.060 | 5.9 / -0.054 |
| corn | luhua | 30 | 6.2 / -0.056 | 4.1 / +0.001 |
| corn | olivera | 30 | 3.2 / -0.015 | 5.5 / -0.028 |
| walnut | luhua | 30 | 7.2 / -0.031 | 7.0 / -0.070 |

## Negative control (T024): permute the SOURCE labels, score against TRUE held-out labels

| model | macro R2, real labels | macro R2, permuted source labels (mean of 3 repeats) |
|---|---:|---:|
| mean_y (all 330) | -0.000 | -0.000 |
| svr_raw (all 330) | 0.831 | -0.139 |
| pca_svr (all 330) | 0.019 | -0.477 |
| pls (all 330) | 0.903 | -0.067 |
| mean_y (Luhua-only) | 0.000 | 0.000 |
| svr_raw (Luhua-only) | 0.859 | -0.081 |
| pca_svr (Luhua-only) | 0.301 | -0.386 |
| pls (Luhua-only) | 0.828 | -0.018 |

The benchmark collapses to R2 <= 0 when the spectrum-label link in training is destroyed, as it should; `mean_y` stays at 0.

## Published reference (NOT measured by ChemiProof; kept separate)

Sun et al. 2026 report, over the same five LOAO systems: raw R2 0.831, PCA 0.693, PARAFAC 0.659, OT-SVR 0.965 (sd 0.004). Our `svr_raw` (reference SVR settings, our independent re-implementation, unclipped scoring) has macro R2 0.831 (clipped 0.831), which equals the published raw value to three decimals. Only the mean is comparable: the per-fold published values were not retrieved, so no per-fold comparison is made; this is a *consistent* partial reproduction of the Raw baseline, not a reproduction of OT-SVR (M4). Our `pca_svr` is a different method (source-only PCA with tuned size; theirs fits PCA on source + target X) and is not comparable to their PCA 0.693.

## Hypotheses (docs/science/02_RESEARCH_PROTOCOL.md)

- **H1 (errors differ materially between target systems): supported.** `svr_raw` per-fold R2 ranges 0.601 (rapeseed) to 0.948 (corn); MAE 5.1 to 13.0 pp. `pls` ranges 0.773 (soybean) to 0.954 (peanut).
- H2 (OT helps), H3 (abstention helps), H4 (some systems unsafe to quantify): not tested here (M4/M5).

## Findings, adverse observations and limitations

1. **No model is reliable on every unseen adulterant.** Best macro R2 is `pls` 0.903 (MAE 6.50 pp) in the 330-sample run, but its worst fold (soybean) has MAE 10.75 pp and bias +0.104; `svr_raw` is worst on rapeseed (R2 0.601, MAE 12.97 pp, +0.097 bias).
2. **Model ranking is not stable across sample sets.** `pls` beats `svr_raw` on all 330 samples (macro R2 0.903 vs 0.831) but loses on Luhua-only (0.828 vs 0.859). With five folds this ranking should not be over-read.
3. **`pca_svr` fails** (macro R2 0.019; fold R2 down to -1.19; predictions up to about 1.7 at true 0.09, 30 out-of-range predictions). The cause was not investigated (hypothesis: polynomial-kernel SVR on unscaled PCA scores extrapolates badly); changing it now would break the freeze, so it is reported as is and only a new protocol id (LOAO-v2) may revisit it.
4. **Brand effect is partly visible:** in the soybean fold both models are much worse on OliVera (svr_raw 14.3 pp, bias +0.138; pls 13.6 pp, +0.136) than on Luhua (4.7 / 7.9 pp), whereas rapeseed is hard for `svr_raw` on all three brands (about 13 pp each), i.e. an adulterant effect. Brand and adulterant are confounded by design; every test brand also appears in training under other adulterants.
5. Only five held-out systems: the min..max over folds is reported instead of a confidence interval; replicates are not independent domains. Walnut is one brand and n=30.
6. All data come from one instrument/lab; binary laboratory mixtures; not a certified test; inductive mode only.
7. Disclosure: `pytest -m dataset` runs the LOAO pipeline on real data (outputs discarded, structural assertions only; no configuration was changed in response), see ADR-013.

## Acceptance tests

| ID | Status | Evidence |
|---|---|---|
| T008 (LOAO: fit never sees target rows or group) | PASS | `tests/unit/test_loao.py::test_t008_loao_...` |
| T010 (five folds, one adulterant each, no shared IDs) | PASS | `tests/unit/test_loao.py`, runtime `audit_folds` |
| T011 (shuffled held-out labels change nothing) | PASS | unit test + canary in both locked runs (leakage_audit.json) |
| T024 (permuted source labels degrade) | PASS | synthetic test + real-data control above |
| T012-T023 | NOT RUN | M4 onwards |
| GitHub Actions `ci` on head commit 6f878a6 (covers M2-M4) | PASS (run 41581270090, commit 6f878a6, https://github.com/MIA290306/ChemiProof/actions/runs/41581270090) | |
