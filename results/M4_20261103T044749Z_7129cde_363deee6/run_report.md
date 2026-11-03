# Run 20261103T044749Z_7129cde_363deee6: five-domain LOAO benchmark, TRANSDUCTIVE (OT) mode

> **TRANSDUCTIVE RESEARCH MODE: these predictions need a BATCH of unlabeled target spectra from the same unseen adulterant. Metrics from this mode must never be advertised as single-file (inductive) deployment performance.**

Units: MAE in percentage points (pp) = 100 x fraction; RMSE/bias in olive-oil volume fraction; R2 unitless and never clamped. Predictions are scored UNCLIPPED.

## Macro over folds (unweighted)

| model | mode | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | worst fold (MAE) |
|---|---|---:|---:|---:|---:|---:|---|
| ot_svr | transductive_batch | 4.09 | 0.0492 | -0.0050 | 0.964 | 0.004 | LOAO-soybean (4.64 pp) |
| ot_svr_pot | transductive_batch | 4.09 | 0.0491 | -0.0050 | 0.965 | 0.004 | LOAO-soybean (4.64 pp) |
| author_pca50 | transductive_batch | 22.41 | 0.3851 | -0.0947 | -1.394 | 1.484 | LOAO-corn (28.68 pp) |
| author_pca10 | transductive_batch | 25.58 | 0.4531 | -0.1199 | -2.494 | 2.688 | LOAO-corn (35.42 pp) |
| svr_no_adaptation | inductive | 8.37 | 0.1005 | +0.0136 | 0.831 | 0.126 | LOAO-rapeseed (12.97 pp) |

## Same, predictions clipped to [0, 1] (reference-style, secondary)

| model | mode | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | worst fold (MAE) |
|---|---|---:|---:|---:|---:|---:|---|
| ot_svr | transductive_batch | 4.09 | 0.0492 | -0.0050 | 0.964 | 0.004 | LOAO-soybean (4.64 pp) |
| ot_svr_pot | transductive_batch | 4.09 | 0.0491 | -0.0050 | 0.965 | 0.004 | LOAO-soybean (4.64 pp) |
| author_pca50 | transductive_batch | 11.84 | 0.1392 | +0.0091 | 0.693 | 0.191 | LOAO-corn (16.95 pp) |
| author_pca10 | transductive_batch | 12.58 | 0.1476 | +0.0099 | 0.659 | 0.183 | LOAO-corn (17.56 pp) |
| svr_no_adaptation | inductive | 8.37 | 0.1005 | +0.0137 | 0.831 | 0.126 | LOAO-rapeseed (12.97 pp) |

## Per fold

| fold | model | mode | n | MAE (pp) | RMSE | bias | R2 | out of [0,1] |
|---|---|---|---:|---:|---:|---:|---:|---:|
| LOAO-soybean | ot_svr | transductive_batch | 60 | 4.64 | 0.0537 | +0.0012 | 0.958 | 0 |
| LOAO-soybean | ot_svr_pot | transductive_batch | 60 | 4.64 | 0.0537 | +0.0012 | 0.958 | 0 |
| LOAO-soybean | author_pca50 | transductive_batch | 60 | 22.09 | 0.3592 | -0.0234 | -0.892 | 11 |
| LOAO-soybean | author_pca10 | transductive_batch | 60 | 24.12 | 0.3816 | -0.0116 | -1.136 | 9 |
| LOAO-soybean | svr_no_adaptation | inductive | 60 | 9.47 | 0.1189 | +0.0691 | 0.793 | 1 |
| LOAO-peanut | ot_svr | transductive_batch | 60 | 4.38 | 0.0495 | -0.0109 | 0.964 | 0 |
| LOAO-peanut | ot_svr_pot | transductive_batch | 60 | 4.37 | 0.0494 | -0.0108 | 0.964 | 0 |
| LOAO-peanut | author_pca50 | transductive_batch | 60 | 23.56 | 0.4227 | -0.1196 | -1.621 | 12 |
| LOAO-peanut | author_pca10 | transductive_batch | 60 | 21.47 | 0.3842 | -0.0970 | -1.165 | 12 |
| LOAO-peanut | svr_no_adaptation | inductive | 60 | 7.05 | 0.0750 | -0.0235 | 0.918 | 0 |
| LOAO-rapeseed | ot_svr | transductive_batch | 90 | 3.73 | 0.0479 | -0.0079 | 0.966 | 0 |
| LOAO-rapeseed | ot_svr_pot | transductive_batch | 90 | 3.72 | 0.0478 | -0.0079 | 0.967 | 0 |
| LOAO-rapeseed | author_pca50 | transductive_batch | 90 | 16.95 | 0.2151 | +0.0932 | 0.321 | 0 |
| LOAO-rapeseed | author_pca10 | transductive_batch | 90 | 17.56 | 0.2146 | +0.0807 | 0.325 | 0 |
| LOAO-rapeseed | svr_no_adaptation | inductive | 90 | 12.97 | 0.1649 | +0.0974 | 0.601 | 0 |
| LOAO-corn | ot_svr | transductive_batch | 90 | 3.95 | 0.0490 | -0.0077 | 0.965 | 0 |
| LOAO-corn | ot_svr_pot | transductive_batch | 90 | 3.95 | 0.0489 | -0.0077 | 0.965 | 0 |
| LOAO-corn | author_pca50 | transductive_batch | 90 | 28.68 | 0.5891 | -0.2458 | -4.090 | 17 |
| LOAO-corn | author_pca10 | transductive_batch | 90 | 35.42 | 0.7575 | -0.3059 | -7.416 | 17 |
| LOAO-corn | svr_no_adaptation | inductive | 90 | 5.14 | 0.0596 | -0.0435 | 0.948 | 0 |
| LOAO-walnut | ot_svr | transductive_batch | 30 | 3.78 | 0.0458 | +0.0004 | 0.969 | 0 |
| LOAO-walnut | ot_svr_pot | transductive_batch | 30 | 3.78 | 0.0458 | +0.0005 | 0.969 | 0 |
| LOAO-walnut | author_pca50 | transductive_batch | 30 | 20.79 | 0.3394 | -0.1780 | -0.689 | 6 |
| LOAO-walnut | author_pca10 | transductive_batch | 30 | 29.35 | 0.5274 | -0.2654 | -3.079 | 6 |
| LOAO-walnut | svr_no_adaptation | inductive | 30 | 7.23 | 0.0843 | -0.0314 | 0.896 | 0 |
