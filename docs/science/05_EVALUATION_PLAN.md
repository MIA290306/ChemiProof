# Quantitative Evaluation and Leakage Prevention Plan

## 0. The benchmark must answer the right question

Target = proportion of **olive oil by volume**, not boolean fraud and not adulterant identity. Prefer `y` in [0,1], but determine author's preprocessing/target scale before attempting direct hyperparameter reproduction. **Report MAE/RMSE in fraction and percentage points**, e.g. MAE 0.08 = 8 pp; **illustration only**.

## 1. Outer folds (primary test protocol)

| Outer fold ID | Entire target domain withheld | Expected target samples (verify M1) |
|---|---|---:|
| `LOAO-soybean` | soybean | 60 |
| `LOAO-peanut` | peanut | 60 |
| `LOAO-rapeseed` | rapeseed | 90 |
| `LOAO-corn` | corn-germ | 90 |
| `LOAO-walnut` | walnut | 30 |

Five source sets are complementary groups. For each outer fold, record train source makeup, brands present, validation group and target batch size.

## 2. Data leakage checklist

- [ ] Targets of outer held-out oil **never** used in fitting supervised model.
- [ ] Outer target **labels** never used for supervised preprocessing, tuning, calibration, OOD threshold selection or feature selection.
- [ ] Any use of outer target **features** must be declared transductive and separated from inductive baseline.
- [ ] Source-fitted scaler/PCA/SVR uses proper `fit/transform` boundaries (Pipeline or equivalent).
- [ ] Replicate/preparation groups within source do not straddle internal training/calibration where independence matters.
- [ ] Smoothing/baseline parameters selected without inspecting target labels.
- [ ] LOAO scores are not a source for repeated unofficial “tuning until better” without registering exploratory status.
- [ ] Splits, configs, random seeds and all runs are preserved and reviewable.

## 3. Models (minimum matrix)

| Key | Protocol | Explanation |
|---|---|---|
| `mean_y` | inductive | constant source mean, sanity floor |
| `svr_raw` | inductive | preprocessed flattened EEM + source-fitted transform/SVR |
| `pca_svr` | inductive | PCA fit on source only (unlike published joint PCA transductive baseline); note distinction |
| `pls` | inductive | standard chemometric regression (components tuned source-internally) |
| `ot_svr` | **transductive** | unlabeled target batch X used for alignment; no target y |
| `author_pca` (optional) | **transductive** | published-style PCA fit on source+unlabeled-target X, explicitly labeled |

Use fair common deterministic spectral preprocessing where applicable; do **not** compare transductive and inductive methods without noting different information access. Reproduce author's exact baselines in a separate benchmark column where methods differ.

## 4. Source-internal training and tuning

1. On every LOAO outer fold, use only 4 source adulterant types.
2. Run inner pseudo-LOAO on source systems to select hyperparameters. When testing transductive candidate methods, inner target features can be used unlabeled as defined by protocol; **inner target labels only for inner scoring**.
3. Establish separate source held-out or cross-fitted residuals for calibration/abstention. Never fit threshold on outer target outcomes.
4. Record all candidate configs tested and criteria. Avoid choosing after outer test inspection. Mark paper-replication fixed hyperparameters separately from exploratory tuned variants.

## 5. Scores

Let $y_i$ be fraction and $\hat y_i$ be predicted fraction:

- MAE = mean absolute error; primary easy-to-interpret percentage-point error.
- RMSE = root mean squared error; penalizes large errors.
- Bias = mean(predicted − actual), signed (positive = olive content overestimated).
- R² = coefficient of determination; can be negative on poor external predictions; never clamp to zero.
- Fraction predictions outside [0,1] must be logged; UI policy may cap display but evaluation uses **unclipped raw predictions** and separately reports clipping consequences if used.

### Aggregation

- **Macro-adulterant** mean: unweighted average over five held-out domains.
- **Pooled per-sample** metric: all held-out predictions concatenated; naturally weights groups 30/60/90 differently.
- Report worst-target score, standard deviation across the **five domains**, and counts.
- R² should be computed **per fold** then macro-averaged; pooled R² is a different statistic and must be labeled.

## 6. Paper replication target

Published LOAO mean R² OT-SVR = 0.965 (sd 0.004), raw = 0.831, PCA = 0.693, PARAFAC = 0.659 (as summarized in published abstract). **These are reference results only.** Reproduction success requires matching exact dataset processing and experimental settings and reporting per-fold differences; do not simply engineer to match target score.

Proposed transparent comparison tolerance (not scientific success criterion): compare mean R² within **0.03** when exact author's code/settings can be verified; when not matched, classify *partial reproduction* and provide written root-cause analysis. Never mislabel as “failed project” because a legitimate independent implementation differs.

## 7. Selective prediction / abstention

Choose thresholds using source cross-validation residuals and/or label-free source OOD features. For each LOAO domain report:

| Metric | Definition |
|---|---|
| `retention` | fraction not abstained |
| `selective_mae` | MAE only among retained predictions |
| `rejection_rate` | 1 − retention |
| `rejected_mae` | retrospective MAE among rejected samples; metric only, not visible as future truth |
| `interval_coverage` | observed fraction with true y inside declared interval |
| `interval_mean_width` | average interval width (fraction/pp) |
| `worst_retained_error` | max abs error among retained |
| `mode` | inductive / transductive; never merged silently |

At predefined retention goals 100/90/80/70%, compare selective risk against random-abstain control (multiple seeded repeats) and raw baseline. **On only five target domains, a favorable mean does not imply deployment-wide reliability.** Source-only calibrated prediction intervals generally lack conformal coverage guarantee on shifted target systems; label observed intervals as experimental.

## 8. Stress tests and audit

- Identical input repeated should give stable output within numerical tolerance for fixed model/config.
- EEM orientation flip w/o axes validation should fail, not silently be accepted.
- Missing bands, different measurement grids, NaN/Inf and constant EEM reject clearly.
- Synthetic perturbation matrix: seeded Gaussian noise at justified signal fractions, additive baseline offsets, intensity scale factors. Parameter grid chosen **before** inspecting test error.
- Repeat under different seeds where algorithms are stochastic; document run count and distribution.
- Sensitivity by EVOO brand if verified metadata exist; no claiming brand-specific results from unverified filename inference.

## 9. Required export tables

`predictions.csv`: `run_id,fold_id,source_sample_hash,sample_id,y_true_fraction,y_pred_fraction,model,mode,abstain,ood_score,interval_lo,interval_hi` (test labels only in *evaluation* artifacts; not in UI prediction objects).  
`metrics_by_fold.csv`: `run_id,fold_id,model,mode,n,mae_fraction,rmse_fraction,bias_fraction,r2,retention`.  
`summary.json`: configuration hash, macro and pooled metrics, reference comparison, confidence/uncertainty caveats and git SHA.

## 10. Minimum interpretation standard

The report must identify which hypothesis was supported, unsupported or inconclusive; provide adverse cases and plots, not cherry-picked best-fold screenshots. An inconclusive or negative selective-prediction result is a valid research finding.
