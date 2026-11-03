# Run 20261103T042759Z_01a9d42_2fbd19b6: five-domain LOAO benchmark (inductive) restricted to brand luhua

Units: MAE in percentage points (pp) = 100 x fraction; RMSE/bias in olive-oil volume fraction; R2 unitless and never clamped. Predictions are scored UNCLIPPED.

## Macro over folds (unweighted)

| model | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | worst fold (MAE) |
|---|---:|---:|---:|---:|---:|---|
| mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0.000 | LOAO-soybean (22.73 pp) |
| svr_raw | 6.95 | 0.0833 | -0.0023 | 0.859 | 0.180 | LOAO-rapeseed (13.91 pp) |
| pca_svr | 13.56 | 0.1999 | +0.0206 | 0.301 | 0.569 | LOAO-soybean (19.36 pp) |
| pls | 8.64 | 0.1009 | +0.0264 | 0.828 | 0.148 | LOAO-rapeseed (13.75 pp) |

## Same, predictions clipped to [0, 1] (reference-style, secondary)

| model | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | worst fold (MAE) |
|---|---:|---:|---:|---:|---:|---|
| mean_y | 22.73 | 0.2611 | -0.0000 | 0.000 | 0.000 | LOAO-soybean (22.73 pp) |
| svr_raw | 6.95 | 0.0833 | -0.0023 | 0.859 | 0.180 | LOAO-rapeseed (13.91 pp) |
| pca_svr | 11.52 | 0.1579 | +0.0367 | 0.528 | 0.504 | LOAO-soybean (18.45 pp) |
| pls | 8.56 | 0.0999 | +0.0272 | 0.830 | 0.149 | LOAO-rapeseed (13.75 pp) |

## Per fold

| fold | model | n | MAE (pp) | RMSE | bias | R2 | out of [0,1] |
|---|---|---:|---:|---:|---:|---:|---:|
| LOAO-soybean | mean_y | 30 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-soybean | svr_raw | 30 | 4.17 | 0.0481 | +0.0212 | 0.966 | 0 |
| LOAO-soybean | pca_svr | 30 | 19.36 | 0.3399 | +0.1563 | -0.694 | 3 |
| LOAO-soybean | pls | 30 | 8.04 | 0.0887 | +0.0801 | 0.885 | 0 |
| LOAO-peanut | mean_y | 30 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-peanut | svr_raw | 30 | 7.03 | 0.0740 | -0.0703 | 0.920 | 0 |
| LOAO-peanut | pca_svr | 30 | 16.00 | 0.2521 | -0.1329 | 0.068 | 6 |
| LOAO-peanut | pls | 30 | 8.19 | 0.0937 | -0.0819 | 0.871 | 3 |
| LOAO-rapeseed | mean_y | 30 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-rapeseed | svr_raw | 30 | 13.91 | 0.1845 | +0.1164 | 0.501 | 0 |
| LOAO-rapeseed | pca_svr | 30 | 13.46 | 0.1859 | +0.0923 | 0.493 | 0 |
| LOAO-rapeseed | pls | 30 | 13.75 | 0.1781 | +0.1372 | 0.535 | 0 |
| LOAO-corn | mean_y | 30 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-corn | svr_raw | 30 | 5.80 | 0.0628 | -0.0541 | 0.942 | 0 |
| LOAO-corn | pca_svr | 30 | 9.75 | 0.1108 | +0.0238 | 0.820 | 0 |
| LOAO-corn | pls | 30 | 6.24 | 0.0664 | +0.0624 | 0.935 | 0 |
| LOAO-walnut | mean_y | 30 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-walnut | svr_raw | 30 | 3.84 | 0.0471 | -0.0244 | 0.968 | 0 |
| LOAO-walnut | pca_svr | 30 | 9.23 | 0.1111 | -0.0365 | 0.819 | 5 |
| LOAO-walnut | pls | 30 | 7.00 | 0.0776 | -0.0659 | 0.912 | 0 |
