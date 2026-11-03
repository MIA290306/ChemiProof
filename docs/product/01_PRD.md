# Product Requirements Document (PRD) — ChemiProof v0.1

**Date:** 2026-10-24 · **Stage:** Planned research prototype · **Product owner:** Mia Ho

## 1. Problem statement

Food authenticity studies use analytical chemistry to estimate composition from spectral signals. The challenge is not just fitting concentration on a familiar training domain: performance can degrade when the adulterant type changes. Researchers need a **traceable and reproducible** workflow to understand model limitations and decide when a spectrum should be flagged for human review instead of confidently quantified.

## 2. Target users and jobs to be done

- **Food science student / researcher:** import a legitimate EEM measurement, inspect raw/processed spectra, reproduce experiments and explain quantitative estimates.
- **Chemometrics researcher:** compare source-only and transductive methods under a defensible LOAO protocol; export methods, artifacts and per-fold metrics.
- **QA/Food authenticity trainee:** learn how a research screening model differs from confirmatory lab testing and regulation.

**Not intended for:** consumers uploading food photos; clinicians; inspectors making compliance determinations; automatic counterfeit/alarm enforcement; replacement for confirmatory chemical methods.

## 3. Scientific scope

- One matrix: olive oil mixed with **one** of five adulterant oils under published experimental conditions.
- Input: legitimate instrument EEM data compatible with the validated dataset protocol.
- Predict: olive-oil **volume fraction** (fraction of binary mixture).
- Important: if an experimental sample is truly adulterated at 20%, its olive fraction is 80%. The mapping is conditional on binary volume mixing; do not apply it to arbitrary products.
- Research modes: baseline inductive; batch-level transductive OT; selective-prediction comparative analysis.

## 4. MVP features (prioritized)

### P0 — Evidence before interface

- **F-01 Source registry:** upstream DOI, download URL, size, MD5/SHA-256, retrieval date, usage/license status; cache location outside tracked Git.
- **F-02 Spectrum parser:** inspect actual .dat format; reject missing/ambiguous orientation; preserve original excitation/emission grids and measurements.
- **F-03 Data audit:** verify total, group/brand representation where identifiable, ten concentration levels, replicate counts and file-path source; surface discrepancies.
- **F-04 Reproducible transformations:** labeled preprocessing stages, parameters and tests; physics-aware QC and informative warnings.
- **F-05 Baseline regression:** constant/mean, PLSRegression, PCA+regression, raw SVR; source-fitted transforms; hyperparameter selection nested within source only.
- **F-06 LOAO evaluation:** five held-out adulterant systems, reports of MAE/RMSE/R²/bias and counts by held-out system, macro and pooled metrics clearly separated.
- **F-07 OT benchmark:** optional unlabeled-target-batch adaptation; explicit labeling as *transductive research*; comparisons with no adaptation.
- **F-08 Traceability:** reproducible CLI, split manifests, config and artifact hashes, environment info, fail-fast diagnostics.

### P1 — Research extension

- **F-09 Uncertainty & abstention:** test residual-based intervals, OOD scores, selective-risk vs coverage; acknowledge no conformal coverage guarantee under domain shift.
- **F-10 Robustness:** reproducible stress tests (intensity perturbation, baseline drift, spectral noise, missing bands), ranges justified and reported; stress tests are simulations, **not** proof of cross-instrument validity.
- **F-11 Interpretability:** visual compare spectra, residuals, wavelength attributions with non-causal caveats, outlier explanations and confidence limits.

### P2 — UI + reporting

- **F-12 Streamlit explorer:** validated file uploader, spectrum viewer, model/mode badges, prediction with units and clear warnings, batch analysis.
- **F-13 Scientific report export:** reproducibility appendix, model and dataset IDs, assumptions, fold metrics, limitations and reference citations.
- **F-14 Portfolio release:** clean GitHub README, demonstration with **labeled synthetic example data** if dataset cannot be redistributed, demo GIF/screenshots and honest research result table.

## 5. Explicitly out of scope

- Identification of any ingredient from an arbitrary photo.
- Fraud determination, food-grade certification or enforcement.
- Determining physical safety or toxicity from spectra.
- Claiming inference on every oil, unknown product, region, brand, instrument, or wavelength grid.
- A generative AI chatbot, auth system, payments, cloud backend or automated surveillance.
- Deployment before minimum research gates pass.

## 6. Usability and trust requirements

- **Every result shows:** model version, method/mode, input QC status, predicted target unit, bounds/interval interpretation, relevant warning(s), a link to limitations and downloadable provenance.
- Never call a regression point estimate a **probability of authenticity**.
- If unsupported data or QC fail → refuse numerical prediction, show actionable error.
- If rejected by abstention decision → show “Review required / estimate withheld” and reasons; do not hide a point estimate behind confident wording.
- Single-file path cannot select transductive OT unless a labeled **batch input requirement** is met; do not quietly switch models.

## 7. Success indicators (goals, not achieved results)

- All accepted data parse deterministically; all expected sample inventory differences reconciled or explained.
- 5/5 LOAO outer folds have reproducible evaluation artifacts; at least three baselines, consistent units.
- Transductive OT replicated within an explicitly recorded tolerance or discrepancy analysis documents differences from paper.
- Scientific extension yields a **measured** selective-risk tradeoff, not necessarily a positive result; negative results are acceptable.
- Unit/integration/data-leakage tests pass; a new researcher can rerun experiment from a clean environment.
- Research UI refuses malformed or out-of-scope inputs and never confuses screening with confirmation.

## 8. Nonfunctional requirements

- Local-first; runs on an ordinary laptop/Apple Silicon without assumed GPU.
- Python packages versioned/locked after resolving stable compatible releases.
- No network needed for training after original dataset acquisition.
- CLI commands reproducible with fixed config. Tests must run on small **synthetic fixtures** without downloading 96 MB dataset.
- Errors distinguish input issue, missing dataset, model not trained, mode mismatch and numerical failure.

## 9. Deliverables

Open reproducible repository + data dictionary + evidence-based figures + experiment logs + trained artifact(s) *only if legally redistributable* + lightweight UI + 4–8 page research-style report + model card.

## 10. Constraints and open questions

- Data zip ~95.9 MB; license and right to redistribute must be verified; source files remain external by default.
- Source repository code rights must be independently verified. Citation alone does **not** replace license permission.
- Per-group EVOO-brand imbalance and unequal sample counts may limit causal interpretation.
- Small number of distinct adulterant systems (5) yields only five outer domains; uncertainty across domains cannot be summarized as if there were hundreds of independent held-out systems.
- No true external laboratory validation at MVP time. Keep claims within analyzed dataset.
