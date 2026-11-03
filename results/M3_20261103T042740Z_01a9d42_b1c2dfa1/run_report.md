# Run 20261103T042740Z_01a9d42_b1c2dfa1: five-domain LOAO benchmark (inductive)

Units: MAE in percentage points (pp) = 100 x fraction; RMSE/bias in olive-oil volume fraction; R2 unitless and never clamped. Predictions are scored UNCLIPPED.

## Macro over folds (unweighted)

| model | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | worst fold (MAE) |
|---|---:|---:|---:|---:|---:|---|
| mean_y | 22.73 | 0.2611 | -0.0000 | -0.000 | 0.000 | LOAO-walnut (22.73 pp) |
| svr_raw | 8.37 | 0.1005 | +0.0136 | 0.831 | 0.126 | LOAO-rapeseed (12.97 pp) |
| pca_svr | 16.55 | 0.2346 | +0.0979 | 0.019 | 0.804 | LOAO-soybean (26.18 pp) |
| pls | 6.50 | 0.0775 | +0.0075 | 0.903 | 0.067 | LOAO-soybean (10.75 pp) |

## Same, predictions clipped to [0, 1] (reference-style, secondary)

| model | macro MAE (pp) | macro RMSE | macro bias | macro R2 | R2 sd over folds | worst fold (MAE) |
|---|---:|---:|---:|---:|---:|---|
| mean_y | 22.73 | 0.2611 | -0.0000 | -0.000 | 0.000 | LOAO-walnut (22.73 pp) |
| svr_raw | 8.37 | 0.1005 | +0.0137 | 0.831 | 0.126 | LOAO-rapeseed (12.97 pp) |
| pca_svr | 15.20 | 0.2031 | +0.0897 | 0.291 | 0.515 | LOAO-soybean (24.69 pp) |
| pls | 6.50 | 0.0775 | +0.0075 | 0.903 | 0.067 | LOAO-soybean (10.75 pp) |

## Per fold

| fold | model | n | MAE (pp) | RMSE | bias | R2 | out of [0,1] |
|---|---|---:|---:|---:|---:|---:|---:|
| LOAO-soybean | mean_y | 60 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-soybean | svr_raw | 60 | 9.47 | 0.1189 | +0.0691 | 0.793 | 1 |
| LOAO-soybean | pca_svr | 60 | 26.18 | 0.3382 | +0.2455 | -0.677 | 12 |
| LOAO-soybean | pls | 60 | 10.75 | 0.1245 | +0.1042 | 0.773 | 0 |
| LOAO-peanut | mean_y | 60 | 22.73 | 0.2611 | -0.0000 | 0.000 | 0 |
| LOAO-peanut | svr_raw | 60 | 7.05 | 0.0750 | -0.0235 | 0.918 | 0 |
| LOAO-peanut | pca_svr | 60 | 12.06 | 0.1365 | +0.0311 | 0.727 | 9 |
| LOAO-peanut | pls | 60 | 4.78 | 0.0560 | +0.0109 | 0.954 | 0 |
| LOAO-rapeseed | mean_y | 90 | 22.73 | 0.2611 | -0.0000 | -0.000 | 0 |
| LOAO-rapeseed | svr_raw | 90 | 12.97 | 0.1649 | +0.0974 | 0.601 | 0 |
| LOAO-rapeseed | pca_svr | 90 | 15.53 | 0.1990 | +0.0735 | 0.419 | 0 |
| LOAO-rapeseed | pls | 90 | 4.79 | 0.0636 | +0.0191 | 0.941 | 0 |
| LOAO-corn | mean_y | 90 | 22.73 | 0.2611 | -0.0000 | -0.000 | 0 |
| LOAO-corn | svr_raw | 90 | 5.14 | 0.0596 | -0.0435 | 0.948 | 0 |
| LOAO-corn | pca_svr | 90 | 19.28 | 0.3863 | +0.1161 | -1.189 | 6 |
| LOAO-corn | pls | 90 | 5.20 | 0.0637 | -0.0271 | 0.940 | 0 |
| LOAO-walnut | mean_y | 30 | 22.73 | 0.2611 | +0.0000 | 0.000 | 0 |
| LOAO-walnut | svr_raw | 30 | 7.23 | 0.0843 | -0.0314 | 0.896 | 0 |
| LOAO-walnut | pca_svr | 30 | 9.70 | 0.1128 | +0.0232 | 0.813 | 3 |
| LOAO-walnut | pls | 30 | 6.99 | 0.0798 | -0.0697 | 0.907 | 0 |
