# Run 20261103T044812Z_7129cde_44fba4b8: five-domain LOAO benchmark, TRANSDUCTIVE (OT) mode restricted to brand luhua

> **TRANSDUCTIVE RESEARCH MODE: these predictions need a BATCH of unlabeled target spectra from the same unseen adulterant. Metrics from this mode must never be advertised as single-file (inductive) deployment performance.**

Units: MAE in percentage points (pp) = 100 x fraction; RMSE/bias in olive-oil volume fraction; R2 unitless and never clamped. Predictions are scored UNCLIPPED.

## Macro over folds (unweighted)

| model | mode | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | worst fold (MAE) |
|---|---|---:|---:|---:|---:|---:|---|
| ot_svr | transductive_batch | 3.13 | 0.0382 | -0.0009 | 0.977 | 0.009 | LOAO-walnut (3.88 pp) |
| ot_svr_pot | transductive_batch | 3.14 | 0.0383 | -0.0010 | 0.977 | 0.009 | LOAO-walnut (3.87 pp) |
| author_pca50 | transductive_batch | 23.65 | 0.4179 | -0.1521 | -1.949 | 2.014 | LOAO-peanut (34.52 pp) |
| author_pca10 | transductive_batch | 25.77 | 0.4643 | -0.1726 | -2.774 | 2.850 | LOAO-peanut (37.49 pp) |
| svr_no_adaptation | inductive | 6.95 | 0.0833 | -0.0023 | 0.859 | 0.180 | LOAO-rapeseed (13.91 pp) |

## Same, predictions clipped to [0, 1] (reference-style, secondary)

| model | mode | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | worst fold (MAE) |
|---|---|---:|---:|---:|---:|---:|---|
| ot_svr | transductive_batch | 3.13 | 0.0382 | -0.0009 | 0.977 | 0.009 | LOAO-walnut (3.88 pp) |
| ot_svr_pot | transductive_batch | 3.14 | 0.0383 | -0.0010 | 0.977 | 0.009 | LOAO-walnut (3.87 pp) |
| author_pca50 | transductive_batch | 10.72 | 0.1304 | -0.0228 | 0.730 | 0.173 | LOAO-peanut (15.01 pp) |
| author_pca10 | transductive_batch | 11.01 | 0.1334 | -0.0250 | 0.718 | 0.175 | LOAO-peanut (15.65 pp) |
| svr_no_adaptation | inductive | 6.95 | 0.0833 | -0.0023 | 0.859 | 0.180 | LOAO-rapeseed (13.91 pp) |

## Per fold

| fold | model | mode | n | MAE (pp) | RMSE | bias | R2 | out of [0,1] |
|---|---|---|---:|---:|---:|---:|---:|---:|
| LOAO-soybean | ot_svr | transductive_batch | 30 | 3.42 | 0.0427 | -0.0132 | 0.973 | 0 |
| LOAO-soybean | ot_svr_pot | transductive_batch | 30 | 3.46 | 0.0433 | -0.0135 | 0.973 | 0 |
| LOAO-soybean | author_pca50 | transductive_batch | 30 | 16.42 | 0.2738 | -0.0742 | -0.099 | 5 |
| LOAO-soybean | author_pca10 | transductive_batch | 30 | 17.02 | 0.2886 | -0.0775 | -0.222 | 6 |
| LOAO-soybean | svr_no_adaptation | inductive | 30 | 4.17 | 0.0481 | +0.0212 | 0.966 | 0 |
| LOAO-peanut | ot_svr | transductive_batch | 30 | 1.99 | 0.0225 | -0.0011 | 0.993 | 0 |
| LOAO-peanut | ot_svr_pot | transductive_batch | 30 | 1.99 | 0.0226 | -0.0010 | 0.993 | 0 |
| LOAO-peanut | author_pca50 | transductive_batch | 30 | 34.52 | 0.6373 | -0.3281 | -4.957 | 6 |
| LOAO-peanut | author_pca10 | transductive_batch | 30 | 37.49 | 0.7013 | -0.3570 | -6.214 | 6 |
| LOAO-peanut | svr_no_adaptation | inductive | 30 | 7.03 | 0.0740 | -0.0703 | 0.920 | 0 |
| LOAO-rapeseed | ot_svr | transductive_batch | 30 | 3.13 | 0.0367 | +0.0005 | 0.980 | 0 |
| LOAO-rapeseed | ot_svr_pot | transductive_batch | 30 | 3.15 | 0.0367 | +0.0003 | 0.980 | 0 |
| LOAO-rapeseed | author_pca50 | transductive_batch | 30 | 15.01 | 0.2047 | +0.0966 | 0.386 | 0 |
| LOAO-rapeseed | author_pca10 | transductive_batch | 30 | 15.65 | 0.2069 | +0.0907 | 0.372 | 0 |
| LOAO-rapeseed | svr_no_adaptation | inductive | 30 | 13.91 | 0.1845 | +0.1164 | 0.501 | 0 |
| LOAO-corn | ot_svr | transductive_batch | 30 | 3.26 | 0.0399 | +0.0068 | 0.977 | 0 |
| LOAO-corn | ot_svr_pot | transductive_batch | 30 | 3.25 | 0.0399 | +0.0069 | 0.977 | 0 |
| LOAO-corn | author_pca50 | transductive_batch | 30 | 28.29 | 0.5510 | -0.2458 | -3.453 | 6 |
| LOAO-corn | author_pca10 | transductive_batch | 30 | 34.14 | 0.6967 | -0.2991 | -6.119 | 7 |
| LOAO-corn | svr_no_adaptation | inductive | 30 | 5.80 | 0.0628 | -0.0541 | 0.942 | 0 |
| LOAO-walnut | ot_svr | transductive_batch | 30 | 3.88 | 0.0492 | +0.0026 | 0.965 | 0 |
| LOAO-walnut | ot_svr_pot | transductive_batch | 30 | 3.87 | 0.0491 | +0.0026 | 0.965 | 0 |
| LOAO-walnut | author_pca50 | transductive_batch | 30 | 24.00 | 0.4226 | -0.2088 | -1.620 | 6 |
| LOAO-walnut | author_pca10 | transductive_batch | 30 | 24.55 | 0.4278 | -0.2200 | -1.684 | 6 |
| LOAO-walnut | svr_no_adaptation | inductive | 30 | 3.84 | 0.0471 | -0.0244 | 0.968 | 0 |
