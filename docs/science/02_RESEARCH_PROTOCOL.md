# Scientific Research Protocol — ChemiProof

**Stage:** preregistration-style plan (not registered); revise in decision log before final evaluation.  
**Primary aim:** measure generalization of olive-oil **volume-fraction** regression under unseen adulterant domain shift, and test whether selective prediction can identify higher-risk estimates.

## 1. Scientific context

EEM measures fluorescence intensity as a function of excitation and emission wavelength. Spectral peaks and backgrounds depend on chemical composition and instrumental/sample conditions. A learned association is **not** proof that any one molecule uniquely caused a prediction. Chemometrics should preserve traceability to measured values and plausible signal-processing steps.

The main reference (Sun et al. 2026) reported **mean R² 0.965 ± 0.004 across five LOAO adulterant systems** using OT-aligned SVR versus raw-feature R² ~0.831. These are **published** numbers, not ChemiProof results. Preprocessing described: consistent emission orientation, baseline correction, Savitzky–Golay smoothing along both spectral axes, intensity normalization and flattening to 9,450 features. Determine precise implementations from original source code before replication.

## 2. Data facts and confounders

- 330 spectra; 35 excitation channels (reported 300–640 nm), 270 emission channels (reported 300–800 nm); precise grids must come from raw files.
- Adulterants: soybean 60, peanut 60, rapeseed 90, corn-germ 90, walnut 30.
- Ten olive fraction levels: 9.09%, 18.18%, 27.27%, 36.36%, 45.45%, 54.55%, 63.64%, 72.73%, 81.82%, 90.91% (source publication rounded).
- Three replicate samples per brand × adulterant × level; three EVOO brands involved in an *unbalanced* design: soybean/peanut 2 brands, rapeseed/corn 3, walnut 1. **Potential confounding**, document every fold's brand makeup and limitations.
- Prefer label derivation from exact volume-ratio metadata when available, not rounded percentages. Never reconstruct labels silently from alphabetical order.

## 3. Research questions (predefined)

**RQ1 — Baseline:** How well do conventional regression pipelines estimate olive-oil fraction on unseen adulterants?  
**RQ2 — Domain adaptation:** Under an unlabeled-target-batch transductive protocol, how much does OT help relative to source-only baselines?  
**RQ3 — Trustworthiness:** At predefined retention rates (e.g., 100%, 90%, 80%, 70%) does an **honestly validated** abstention rule reduce error of retained predictions on held-out adulterant folds?  
**RQ4 — Robustness:** How sensitive are models/flags to reasonable synthetic signal perturbations and to shifts in source brand makeup?

## 4. Hypotheses (falsifiable)

- H1: Unseen-adulterant errors will differ materially between target systems.
- H2: OT may improve mean predictive error in the transductive setting, but improvement is not assumed and may vary per fold.
- H3: An abstention rule fitted without target labels may improve retained-set MAE, **but improvement is not guaranteed**.
- H4: Some target systems or perturbed spectra will remain unsafe to quantify; transparent refusal is preferable to overconfident precision.

## 5. Evaluation design

### Outer holdout (mandatory)

For each adulterant in `[soybean, peanut, rapeseed, corn, walnut]`:
1. Set all samples from that adulterant aside as target evaluation domain `T`.
2. Four other adulterant systems form source domain `S`.
3. Fit/tune baseline models and calibration/thresholds **only within source-domain partitions**. Keep any replicate groups and independent preparation units together where relevant.
4. Record target `X` access mode before execution: **inductive** no target batch adaptation, versus **transductive** unsupervised adaptation using only `X_T` (never `y_T`).
5. Freeze preprocessing selection, model family, hyperparameters and abstention thresholds before scoring withheld `y_T`.
6. Evaluate once per protocol version; log deviations and avoid retrospectively tailoring to target results.

### Transductive OT methodology

Published-style OT uses batch of unlabeled target X. For each fold it constructs a source–target cost matrix, computes entropic OT and projects labeled source spectra into the target distribution before learning SVR. This is **not** a deployment strategy for arbitrary single-file input unless a separately tested inductive adaptation method is developed.

Published reported algorithm: entropic regularization epsilon=0.1, Sinkhorn max_iter=1000 (validate numerical units and reproducibility); polynomial SVR degree=3, C=1.0, epsilon=0.1, gamma=`scale`. **Label scaling in author's implementation must be inspected before reusing SVR epsilon; do not infer its units from the paper alone.**

### Nested model selection

- Outer target system labels cannot affect any tuning choice.
- Within each outer source set, conduct **inner source-only folds** (prefer leave-one-source-adulterant-out) for hyperparameters and threshold selection. Brand-aware sensitivity where source metadata allow.
- For target-X-dependent transductive tuning: inner pseudo-target source adulterants can be used unlabeled for unsupervised OT, then scored with their labels **only as inner validation**. Actual outer target labels remain unseen.
- Keep separate development exploratory runs and locked final runs; preserve all attempt history.

## 6. Research groups and controls

- Control A: mean/median predictor trained on S (sanity floor).
- Control B: raw flattened EEM → source-only SVR.
- Control C: source-fitted PCA → linear or SVR model; optionally PLSRegression for chemometric benchmark.
- Method D: OT-transductive + SVR, explicitly labeled.
- Extension E: each method + abstention rule trained/calibrated from source-only data; compare risk at equal coverage.
- Negative controls: permuted source labels, intentionally wrong grid, obviously corrupt spectrum, blank/near-zero features, and synthetic shifted/noise inputs. Ensure permuted control degrades (not necessarily to exact numeric tolerance).

## 7. Preprocessing audit

- Preserve immutable raw files. Record explicit order of matrix orientation and axes.
- Distinguish within-spectrum deterministic transformations (e.g., fixed Savitzky–Golay filter) from training-fitted transformations (PCA, standardization, selected thresholds). Both must be documented.
- Baseline correction and fluorescence Rayleigh/Raman scatter treatment **must be scientifically justified**; no arbitrary masking without provenance.
- Smoothing window sizes, polynomial orders, intensity normalization denominator and order must be determined from paper/code or carefully prespecified as alternative methods.
- Prohibit data-dependent spectral window selection using target labels.
- In QC, flag zero intensity, NaN/Inf, negative values (may be plausible after correction; raw negatives require investigation), saturation, axis mismatch, and extreme intensities.

## 8. Metrics and inference

- Primary per-fold: MAE in **olive fraction** (and percentage points), RMSE, bias, R², sample count.
- Show **macro mean over five adulterant systems** separately from pooled sample-weighted metrics; do not hide walnut's small size.
- Calculate sample-level error plots, residual vs fraction, aggregate worst-fold score and domain spread.
- Replicates are not statistically independent adulterant domains. Confidence intervals clustered by appropriate preparation/measurement group; with five held-out domains, present uncertainty conservatively.
- Reproducibility: identical code/config/data provenance yields equal splits and numerically consistent output within specified tolerances.

## 9. Uncertainty and abstention extension

- A prediction interval can be computed from source-held-out/calibration residuals, and reported as **empirical** coverage on each outer target domain. Standard conformal guarantees require exchangeability; LOAO distribution shift violates the usual guarantee.
- An OOD score (e.g., source PCA reconstruction residual or distance) is a *proxy*, not an oracle of unknown adulterants.
- Set rule(s) and thresholds using source-only out-of-fold data. Evaluate predeclared coverage levels (100/90/80/70%).
- Show rejection frequency, retained-set MAE, discarded-set MAE (retrospective only), observed interval coverage, interval width, false-security cases; do not tune after seeing outer target errors.
- If too few calibration points, return insufficient calibration rather than numeric certainty.

## 10. Robustness experiments

- Synthetic additive noise at predeclared relative levels, baseline offsets, intensity scaling, spectral-axis perturbation where physically coherent. Record assumptions and transformation equations in report.
- Model should fail gracefully on malformed shape or unsupported wavelength grid; such QA rejection is not the same as statistically detecting domain shift.
- If an external aging dataset (Venturini et al. 2023) is explored, note it is **not** an adulteration-labeled external validation set; do not score adulteration error on it.

## 11. Limitations and publication integrity

- Original study is limited to one food matrix and one experimental instrument environment. Cross-device and marketplace performance are unproven.
- Dataset lacks/has uneven representation of base brands by adulterant. A LOAO gain does not establish brand-independent chemistry.
- Data are laboratory-prepared binary mixtures, not a random survey of real commercial fraud.
- Abstention coverage can improve simply by discarding samples; report acceptance rate and error simultaneously.
- Do not claim regulatory food authenticity or compliance decisions.

## 12. Required research artifacts

`dataset_manifest.json`, `qc_report.json`, `fold_manifest.csv`, `benchmark_per_fold.csv`, `benchmark_summary.json`, `selective_risk.csv`, `robustness_results.csv`, `experiment_config.yaml`, `provenance.json`, generated figures and `research_report.md`.
