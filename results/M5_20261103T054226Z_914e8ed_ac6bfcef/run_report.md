# M5 run report: abstention, intervals, robustness (LOAO-UQ-v1)

INDUCTIVE research mode. Abstention is a research cue, NOT a safety decision. Intervals are EMPIRICAL; no coverage guarantee under a new adulterant. Five systems only.

Run: `20261103T054226Z_914e8ed_ac6bfcef`. Units: fraction (0.01 = 1 percentage point).

## Selective risk at the 0.80 retention goal (threshold from SOURCE only)

| model | score | full MAE (pp) | observed retention | selective MAE (pp) | rejected MAE (pp) |
|---|---|---|---|---|---|
| svr_raw | ood_maha | 8.37 | 0.83 | 7.06 | 13.74 |
| svr_raw | model_disagreement | 8.37 | 0.73 | 7.42 | 8.86 |
| pca_svr | ood_maha | 16.55 | 0.83 | 11.86 | 45.94 |
| pca_svr | model_disagreement | 16.55 | 0.73 | 10.16 | 37.65 |
| pls | ood_maha | 6.50 | 0.83 | 6.22 | 8.02 |
| pls | model_disagreement | 6.50 | 0.73 | 6.23 | 7.49 |

Means are unweighted over the five folds. Per-fold rows: `selective_risk.csv`.

## Usefulness verdict (rule fixed in ADR-017)

| model/score | folds improved | folds beat random p05 | useful |
|---|---|---|---|
| svr_raw/ood_maha | 3/5 | 2/5 | NO |
| svr_raw/model_disagreement | 2/5 | 1/5 | NO |
| pca_svr/ood_maha | 3/5 | 4/5 | NO |
| pca_svr/model_disagreement | 5/5 | 5/5 | yes |
| pls/ood_maha | 3/5 | 3/5 | NO |
| pls/model_disagreement | 3/5 | 1/5 | NO |

## Observed interval coverage (nominal 0.90; empirical, not guaranteed)

| model | variant | LOAO-corn | LOAO-peanut | LOAO-rapeseed | LOAO-soybean | LOAO-walnut | mean width (pp) |
|---|---|---|---|---|---|---|---|
| svr_raw | pooled | 1.00 | 1.00 | 0.60 | 0.83 | 1.00 | 41.7 |
| svr_raw | max_domain | 1.00 | 1.00 | 0.67 | 1.00 | 1.00 | 58.8 |
| pca_svr | pooled | 0.87 | 1.00 | 0.70 | 0.47 | 1.00 | 54.7 |
| pca_svr | max_domain | 0.90 | 1.00 | 0.70 | 0.95 | 1.00 | 84.4 |
| pls | pooled | 0.92 | 1.00 | 0.94 | 0.65 | 1.00 | 27.2 |
| pls | max_domain | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 44.7 |

## Robustness (held-out MAE vs clean, mean over folds)

| model | perturbation | level | MAE (pp) | max feature change | abstain rate |
|---|---|---|---|---|---|
| svr_raw | clean | 0.0 | 8.37 | 0.00e+00 | 0.17 |
| pca_svr | clean | 0.0 | 16.55 | 0.00e+00 | 0.17 |
| pls | clean | 0.0 | 6.50 | 0.00e+00 | 0.17 |
| svr_raw | noise | 0.001 | 8.52 | 7.64e-03 | 0.18 |
| pca_svr | noise | 0.001 | 16.33 | 7.64e-03 | 0.18 |
| pls | noise | 0.001 | 6.62 | 7.64e-03 | 0.18 |
| svr_raw | noise | 0.003 | 9.19 | 2.42e-02 | 0.20 |
| pca_svr | noise | 0.003 | 15.92 | 2.42e-02 | 0.20 |
| pls | noise | 0.003 | 7.92 | 2.42e-02 | 0.20 |
| svr_raw | noise | 0.01 | 15.68 | 7.95e-02 | 0.57 |
| pca_svr | noise | 0.01 | 20.08 | 7.95e-02 | 0.57 |
| pls | noise | 0.01 | 17.74 | 7.95e-02 | 0.57 |
| svr_raw | noise | 0.03 | 54.73 | 2.19e-01 | 1.00 |
| pca_svr | noise | 0.03 | 79.64 | 2.19e-01 | 1.00 |
| pls | noise | 0.03 | 51.31 | 2.19e-01 | 1.00 |
| svr_raw | offset | 0.01 | 8.37 | 6.66e-16 | 0.17 |
| pca_svr | offset | 0.01 | 16.55 | 6.66e-16 | 0.17 |
| pls | offset | 0.01 | 6.50 | 6.66e-16 | 0.17 |
| svr_raw | offset | 0.03 | 8.37 | 6.66e-16 | 0.17 |
| pca_svr | offset | 0.03 | 16.55 | 6.66e-16 | 0.17 |
| pls | offset | 0.03 | 6.50 | 6.66e-16 | 0.17 |
| svr_raw | offset | 0.1 | 8.37 | 5.55e-16 | 0.17 |
| pca_svr | offset | 0.1 | 16.55 | 5.55e-16 | 0.17 |
| pls | offset | 0.1 | 6.50 | 5.55e-16 | 0.17 |
| svr_raw | scale | 0.5 | 8.37 | 0.00e+00 | 0.17 |
| pca_svr | scale | 0.5 | 16.55 | 0.00e+00 | 0.17 |
| pls | scale | 0.5 | 6.50 | 0.00e+00 | 0.17 |
| svr_raw | scale | 0.8 | 8.37 | 5.55e-16 | 0.17 |
| pca_svr | scale | 0.8 | 16.55 | 5.55e-16 | 0.17 |
| pls | scale | 0.8 | 6.50 | 5.55e-16 | 0.17 |
| svr_raw | scale | 1.25 | 8.37 | 5.55e-16 | 0.17 |
| pca_svr | scale | 1.25 | 16.55 | 5.55e-16 | 0.17 |
| pls | scale | 1.25 | 6.50 | 5.55e-16 | 0.17 |
| svr_raw | scale | 2.0 | 8.37 | 0.00e+00 | 0.17 |
| pca_svr | scale | 2.0 | 16.55 | 0.00e+00 | 0.17 |
| pls | scale | 2.0 | 6.50 | 0.00e+00 | 0.17 |

Noise rows average over seeds. Full detail: `perturbation_table.csv`.

## Limitations

See `summary.json` (`limitations`) and ADR-017.

