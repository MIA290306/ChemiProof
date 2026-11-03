# Model card: FINAL-PLS-v1 (ChemiProof inductive screening model)

**Status:** released with `v1.0.0`; not externally reviewed (ADR-020). Source of every value: `results/M6_final_20261103T074605Z_ce2423b_82b39d6c/model_card.json` (tracked) and the LOAO runs named below. Decision record: ADR-018.

> **Research prototype. Not a certified authenticity test, not a regulatory or food-safety decision, and not validated outside the published laboratory dataset.**

## 1. Identity

| Field | Value |
|---|---|
| Model ID / version | `FINAL-PLS-v1` (protocol id), model key `pls`, package `chemiproof 0.0.1` |
| Run ID | `20261103T074605Z_ce2423b_82b39d6c` (git `ce2423b`, clean tree) |
| Config sha256 | `82b39d6c5ceed1a50ba8441a30ba4854767ec2c2e745608aef3657de58739623` |
| Artifact | `model.npz`, sha256 `bbcff343011aa4e7ac674f7151affd6f6cf164f09acd68557f0a05e47261aa4c` (git-ignored: it contains PCA mean/components derived from the third-party spectra; rebuilt bit-identically by `chemiproof model train-final`) |
| Owner | Mia Ho (`MIA290306`); implementation by Claude Code for collaborator Bruce1508 |
| Date | 2026-11-03 |

## 2. Task and units

- **Target:** olive-oil **volume fraction** in [0, 1] (0.01 = 1 percentage point, pp). The adulterant fraction is `1 - olive_fraction` for **binary** mixtures only.
- **Input:** one EEM `.dat` file with exactly the training axes (35 excitation x 270 emission channels, section 4 of the data card). Any other grid is rejected with `INVALID_WAVELENGTH_GRID`; nothing is interpolated.
- **Mode:** `inductive_single`: the estimate uses only the uploaded file and the trained model; it never looks at other uploads.

## 3. Method

- Preprocessing `author_v1` (per spectrum, nothing fitted): subtract global minimum, Savitzky-Golay window 5 / order 2 along emission, divide by global maximum, flatten to 9,450 features.
- PLS regression (`scale=False`), **6 components**, chosen by leave-one-adulterant-out CV over all five adulterants on the grid 2/4/6/8/12/16/24/32. Inner-CV MAE by components (fraction): 2: 0.103, 4: 0.060, **6: 0.056**, 8: 0.069, 12: 0.144, 16: 0.206, 24: 0.171, 32: 0.144. The 5.61 pp at 6 components is a **selection score, not a test result**.
- Training data: all 330 spectra (corn 90, peanut 60, rapeseed 90, soybean 60, walnut 30); training-file SHA-256 list and sample-ID hash `f3a06924...` in the card.

## 4. Performance evidence (and why it is indirect)

There is **no independent test of this exact model**: it was trained on every available spectrum. The only evidence is the LOAO-v1 benchmark of the **same procedure** with one adulterant held out at a time (run `20261103T042740Z_01a9d42_b1c2dfa1`, inductive, unclipped):

| Held-out adulterant | n | MAE (pp) | R2 | bias (fraction) |
|---|---:|---:|---:|---:|
| soybean | 60 | 10.75 | 0.773 | +0.104 |
| peanut | 60 | 4.78 | 0.954 | +0.011 |
| rapeseed | 90 | 4.79 | 0.941 | +0.019 |
| corn | 90 | 5.20 | 0.940 | -0.027 |
| walnut | 30 | 6.99 | 0.907 | -0.070 |
| **macro (unweighted)** | | **6.50** | **0.903** | |

Caveats that make 6.50 pp **optimistic**: PLS was picked as the best of three inductive models after these outer results were seen (ADR-018); the ranking is unstable (on the Luhua-only subset `svr_raw` had higher R2, 0.859 vs 0.828; run `20261103T042759Z_01a9d42_2fbd19b6`). Errors on the soybean fold concentrate in the OliVera brand (13.63 pp vs 7.88 pp for Luhua; M5 `brand_breakdown.csv`).

## 5. Uncertainty and abstention

| Component | Value | What it is NOT |
|---|---|---|
| Risk flag `ood_maha` | 10-component PCA Mahalanobis distance; threshold **5.32** = 0.80 retention-goal quantile of cross-fitted leave-one-adulterant-out scores (330 points). Above it the estimate is **withheld** (`ABSTAIN_OOD_RISK`). | Not a validated out-of-distribution or fraud detector. In LOAO-UQ-v1 it failed the preregistered usefulness rule for PLS (3/5 folds improved; macro selective MAE 6.50 -> 6.22 pp at goal 0.80). |
| 90 % interval | `estimate +/- 0.105` (pooled, primary; 10.5 pp) or `+/- 0.160` (max_domain; 16.0 pp), from cross-fitted residuals | No coverage guarantee: unseen adulterants break exchangeability. Observed LOAO coverage of pooled PLS intervals ranged 0.65 (soybean) to 1.00 (M5 run `20261103T054226Z_914e8ed_ac6bfcef`). |

Known failure modes (measured in M5, inductive LOAO): additive Gaussian noise of 1 % of the spectrum maximum raised PLS MAE from 6.50 to 17.7 pp (3 %: 51.3 pp), while the flag withheld 57 % (100 % at 3 %); baseline offsets and global intensity scaling have no effect (removed by preprocessing). Training spectra score lower than unseen spectra, so they are withheld less often than the 20 % source rate (ADR-018 review note 1).

## 6. Fairness / imbalance

Brands are unequally represented (walnut = Luhua only; Earl Grey only with rapeseed and corn). Brand and adulterant are entangled, and the soybean-OliVera error concentration is described but not tested (needs a new ADR). Results must not be read as brand-independent.

## 7. Intended and out-of-scope uses

| Intended | Not intended |
|---|---|
| Teaching and research demonstration of EEM chemometrics, LOAO evaluation and honest abstention | Deciding whether a product is adulterated, authentic, safe, legal or compliant |
| Screening estimates on spectra from **this** instrument protocol and grid, read together with the warnings | Commercial products, other adulterants, multi-adulterant blends, other instruments or laboratories |
| Reproducing and auditing the published benchmark | Identifying the adulterant, molecules or health risk from EEM alone |

## 8. Security and integrity

- `.dat` files are parsed as text and validated (size, axes, finite values); their content is never executed.
- `model.npz` holds plain arrays and is loaded with `allow_pickle=False`; its SHA-256 must match the card or loading fails.
- An upload whose bytes match a training file is labelled `IN_SAMPLE` (exact byte match only).

## 9. Batch research path (separate, transductive)

The explorer's batch page runs `ot_svr` with LOAO-OT-v1 settings and source = all 330 spectra on a batch of at least 10 unlabelled files. This configuration has **never been evaluated** (every M4 fold held one adulterant out), and label-skewed batches collapsed in the M4 stress test (OT R2 about -3). Its outputs are not FINAL-PLS-v1 outputs and are never single-file performance.

## 10. Re-evaluation and rollback

- Rebuild: `chemiproof model train-final` (needs the dataset; about 7 s; the npz sha256 must equal the value above).
- Any change to preprocessing, model, grid, flag or interval method requires a new protocol id and ADR; FINAL-PLS-v1 stays as recorded.
- Rollback: delete or move the newer `results/M6_final_*` folder; the explorer loads the latest folder that has both `model.npz` and `model_card.json`.
- Re-evaluation is required before any use on a new instrument, laboratory, product type or adulterant, using data never seen in training.

## 11. References

- Sun et al. (2026), *npj Science of Food*, DOI 10.1038/s41538-026-01037-6 (published method and benchmark).
- Sun et al. (2026), Zenodo dataset, DOI 10.5281/zenodo.19755088, CC BY 4.0.
- ChemiProof decision log: ADR-008 (labels), ADR-011 (preprocessing), ADR-013 (LOAO-v1), ADR-017 (LOAO-UQ-v1), ADR-018 (this model).
