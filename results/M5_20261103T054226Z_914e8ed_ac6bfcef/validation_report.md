# M5 validation report: abstention, intervals, robustness (protocol LOAO-UQ-v1)

Run `20261103T054226Z_914e8ed_ac6bfcef` · locked · git head `914e8ed`, `dirty=False` · config sha256 `f93cfb4c97d22ad2...` · INDUCTIVE mode · dataset manifest `31c718edd95b4fac...`. Units: errors and widths are olive volume FRACTION (0.01 = 1 percentage point, pp). Everything below is measured by this run; nothing is copied from the paper.

## Commands and exit codes

| Command | Exit |
|---|---|
| `chemiproof experiment uncertainty --config config/experiments/uncertainty_loao.yaml` (locked, clean tree) | 0 |
| `pytest -m dataset -k m5` (real data structure, equality with frozen LOAO-v1 predictions) | 0 (1 passed) |
| `pytest -q -x` before the run (synthetic + unit, 194 tests) | 0 |
| `ruff check .` / `ruff format --check .` | 0 / 0 |

## Protocol integrity

- ADR-017 and `uncertainty_loao.yaml` were committed (`b0d7d2c`) BEFORE any M5 code; file hashes were recorded (`914e8ed`) BEFORE the first scored run. One scored run was made, nothing was re-run or adjusted.
- Disclosure (also in ADR-017): the M3/M4 outer errors had been seen when the design was written. No constant was fitted to a held-out adulterant.
- Leakage audit: fold audit passed; the label-shuffle canary (held-out labels permuted, everything refitted) left predictions, scores, intervals and thresholds unchanged in all 5 folds (T011, T018).
- Calibration sets contained 240-300 source points from 3-4 source adulterants; no interval was refused (T016 is verified in unit tests with too-small and too-few-group sets).
- Point predictions equal the frozen LOAO-v1 predictions (checked to 1e-9 in the real-data test).

## Findings (macro over the five held-out adulterants; per-fold rows are in the CSV files)

1. **Abstention is not reliably useful.** At the 0.80 retention goal (threshold from source only; observed retention 0.83 for `ood_maha`, 0.73 for `model_disagreement`, because the shift moves target scores) the rule of ADR-017 is met by only ONE of six model/score pairs: `pca_svr` with `model_disagreement` (5/5 folds, 5/5 beat random p05). For the best point model, PLS (6.50 pp), `ood_maha` lowers MAE from 6.50 to 6.22 pp and passes in 3/5 folds; `model_disagreement` 6.50 to 6.23 pp, 3/5 and 1/5. Verdict: **not useful on this benchmark** for `svr_raw` and `pls`.
2. **Why the single "yes" is weak:** `pca_svr` is the worst model (16.55 pp, R2 0.019); its disagreement with the other two models mostly marks cases where the weak model is wrong. This is a property of the ensemble, not evidence that errors of the good models are detectable.
3. **Score vs error ranking (post-hoc diagnostic, Spearman, mean over folds):** `ood_maha` 0.38 (pca_svr), 0.05 (svr_raw), 0.11 (pls); `model_disagreement` 0.59, -0.07, -0.03. Per-fold signs flip (for example svr_raw `ood_maha`: rapeseed +0.73, corn -0.76), so no score is stable across held-out systems.
4. **Intervals (nominal 0.90, observed per held-out adulterant):** pooled intervals under-cover on some systems: PLS soybean 0.65, `pca_svr` soybean 0.47, `svr_raw` rapeseed 0.60, and over-cover on others (1.00 on peanut and walnut). The conservative `max_domain` variant reaches about 0.9-1.0 but is 45 pp wide for PLS (59 pp svr_raw, 84 pp pca_svr): not informative on a 0-100 pp scale. Mean pooled width: PLS 27 pp, svr_raw 42 pp, pca_svr 55 pp. **No coverage guarantee holds under adulterant shift, as expected.**
5. **Robustness:** a uniform baseline offset (up to 10 % of max) and a global intensity scale (0.5-2.0) change the features by at most 6.7e-16, so scores, MAE and abstention are identical (the expected invariance of `author_v1`, now measured). Added Gaussian noise matters: at 0.3 % of max PLS MAE rises 6.50 to 7.92 pp; at 1 % to 17.7 pp; at 3 % to 51.3 pp. `ood_maha` does react to noise (abstention at the 0.80 threshold: 17 % clean, 20 %, 57 %, 100 % at 0.3 %, 1 %, 3 %), so it is a usable detector of gross spectral degradation even though it does not rank within-distribution errors.
6. **Smoothing ablation (author_v1 without Savitzky-Golay):** mean Spearman changes little (PLS `ood_maha` 0.11 to 0.21, svr_raw 0.05 to 0.06, pca_svr 0.38 to 0.36); no conclusion is drawn from it.
7. **Brand view (PLS, descriptive):** the largest errors sit in soybean-olivera (MAE 13.6 pp, abstain rate 0.43) versus soybean-luhua (7.9 pp, 0.20); the top failure cases are all soybean-olivera and are abstained. A brand or batch effect is a plausible explanation but NOT tested here; no brand-specific claim is made.

## Honest summary

Within the declared scope the model does not "know when it is wrong": simple label-free scores catch gross noise and some soybean/olivera failures, but they do not rank errors consistently across the five systems, and source-calibrated intervals are either too narrow on some systems or too wide to be useful. This unfavourable outcome is reported as the result. Five systems, one instrument and laboratory mixtures only; nothing here supports a deployment or safety claim.

## Acceptance tests

T011 (with M3), T016, T017, T018: PASS (unit + integration + real-data canary). T016 wording: the interval is refused when the calibration set is too small. T017: observed coverage reported, "no guarantee" in every coverage row. T018: thresholds use source cross-fitted scores only; the canary proves no held-out label influences them.

## Not done / limits

OT (transductive) abstention is out of scope of LOAO-UQ-v1 (ADR-017); the batch-composition hazard from ADR-015 remains an open limitation. Luhua-only M5 run not made. Brand-effect hypotheses not tested. Random-rejection band uses 200 draws of the same fold's errors.
