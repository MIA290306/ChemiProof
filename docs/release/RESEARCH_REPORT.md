# ChemiProof: unseen-adulterant quantification of olive oil from EEM fluorescence, re-examined with leave-one-adulterant-out evaluation, optimal-transport replication and honest abstention

**Author:** Mia Ho (owner). Implementation and analysis: Claude Code (AI coding agent) for the owner and collaborator Bruce1508; see *Contributions*.
**Data source DOI:** 10.5281/zenodo.19755088 (CC BY 4.0) · **Benchmark reference DOI:** 10.1038/s41538-026-01037-6
**Report date:** 2026-11-03 · **Code:** branch `m7/release` (based on commit `27c6efb`) · **Runs:** listed in Appendix A
**Status:** DRAFT, REVIEW REQUIRED. Not reviewed by an external scientist yet (see `docs/release/RELEASE_REVIEW.md`).

> **Notice:** experimental screening software. Not a validated or certified regulatory food-authenticity method. Every number below is a ChemiProof measurement from a committed run unless it is explicitly labelled **published**.

## Contributions

- **Sun et al. (2026)** collected the 330 EEM spectra, published the dataset, proposed the optimal-transport (OT) alignment + SVR method and the leave-one-adulterant-out (LOAO) framing, and reported its results.
- **ChemiProof (this work)** contributes: an independent parser, data audit and label-direction check; a frozen, leakage-tested LOAO benchmark of inductive baselines; an independent re-implementation of the published OT method (no author code copied; the authors' repository has no license); a stress test of OT under batch composition; a preregistered abstention / interval / robustness study; a screening model with a model card; and a local research explorer. Nothing here claims the OT method as ours.

## Abstract

Fluorescence excitation-emission matrices (EEM) can quantify olive oil in binary blends, but a practical model meets adulterants it was never trained on. Using the public dataset of Sun et al. (2026) (330 spectra, five adulterants, three extra-virgin olive-oil brands, one instrument), we scored olive-oil volume fraction in five LOAO folds, where each adulterant is held out in turn and its labels are used only for scoring. The best inductive (single-spectrum) model, PLS, reached a macro mean absolute error (MAE) of 6.50 percentage points (pp; R2 0.903), with fold errors from 4.78 pp (peanut) to 10.75 pp (soybean). Our independent implementation of the published OT method reproduced the published mean R2 (measured 0.964 vs published 0.965; macro MAE 4.09 pp), but only in a transductive setting that needs a whole unlabelled batch of the new adulterant: with random batches of 10 spectra it did no better than no adaptation (9.17 vs 8.61 pp), and with label-skewed batches it collapsed (R2 about -3). A preregistered label-free abstention rule did not reliably reduce error (1 of 6 model/score pairs met the usefulness rule), and source-calibrated 90 % intervals covered 0.65 to 1.00 of held-out samples per fold, so no coverage guarantee holds. All results reproduce to floating-point round-off in a fresh clone and environment. The findings are limited to laboratory blends from one instrument and laboratory; external validation is still required.

## 1. Introduction

Olive oil is a frequent target of economically motivated adulteration with cheaper vegetable oils. EEM fluorescence captures chlorophyll, tocopherol and oxidation-product signals quickly and without reagents, and chemometric regression can turn a spectrum into a blend estimate. The hard case is **domain shift**: a model calibrated on known adulterants is applied to an oil it has never seen. Sun et al. (2026) addressed this with entropic OT that aligns labelled source spectra to an unlabelled batch of target spectra before fitting an SVR, and reported a mean R2 of 0.965 across five LOAO folds (published). We ask what of this holds under a strict, leakage-free protocol, what it costs in information access, and whether a model can signal when not to trust its own estimate.

## 2. Research questions and hypotheses (preregistered in `docs/science/02_RESEARCH_PROTOCOL.md`)

- **RQ1 Baseline:** how well do conventional pipelines estimate olive fraction on unseen adulterants?
- **RQ2 Domain adaptation:** with an unlabelled target batch, how much does OT help over source-only baselines?
- **RQ3 Trustworthiness:** at fixed retention, does an honestly validated abstention rule reduce retained-set error?
- **RQ4 Robustness:** how sensitive are models and flags to signal perturbations and brand makeup?

Hypotheses: H1 errors differ materially between target systems; H2 OT may improve mean error transductively, not assumed and possibly fold-dependent; H3 label-free abstention may improve retained-set MAE, not guaranteed; H4 some systems or perturbed spectra remain unsafe to quantify.

## 3. Materials and methods

### 3.1 Dataset (audit run `20261103T034431Z_b050b36-dirty_33c0ba5b`)

330 ASCII `.dat` EEMs parsed without error: soybean 60, peanut 60, rapeseed 90, corn 90, walnut 30 (matches the publication). Each spectrum has 35 excitation (300-640 nm) x 270 emission (297.4-802.5 nm) channels with one identical axis grid. Brands: corn and rapeseed with Earl Grey, Luhua, OliVera; soybean and peanut with Luhua, OliVera; walnut with Luhua only; 30 spectra per brand x adulterant cell (10 ratios x 3 rounds). Label: folder ratio a:b is olive : adulterant by volume, so `olive_fraction = a/11` (0.091-0.909; ADR-008, supported by a chlorophyll-band check in 11/11 pairs, weak in three OliVera pairs). Manifest sha256 `31c718ed...`. Details: `docs/release/DATA_CARD.md`.

### 3.2 QC and preprocessing

No NaN/Inf, constant or duplicate spectra. Every file contains some negative cells (22,982 in total, min -22.37 Counts/uA); they are flagged, not clamped. Preprocessing `author_v1` follows the authors' released code (ADR-011): subtract the spectrum's global minimum, Savitzky-Golay smoothing (window 5, order 2) along emission, divide by the global maximum, flatten to 9,450 features. Each step uses one spectrum only, so preprocessing cannot leak between samples. (The paper text mentions smoothing along both axes; the code smooths emission only. We followed the code.)

### 3.3 LOAO protocol (frozen as `LOAO-v1`, ADR-013, before any held-out scoring)

Five outer folds; test = all spectra of one adulterant, train = the other four. Hyper-parameters (PLS components 2-32; PCA components 5-80) are chosen by an inner leave-one-source-adulterant-out CV on the four training adulterants only. Models: `mean_y` (predicts the training mean), `svr_raw` (polynomial SVR, degree 3, C 1, epsilon 0.1 fraction, the authors' settings), `pca_svr` (PCA fitted on source only + the same SVR), `pls`. Seed 20261024. A permuted-label negative control and a fold-label canary test guard against leakage.

### 3.4 Inductive versus transductive information access

**Inductive** models see only labelled source spectra and score each target spectrum alone. **Transductive** OT (`LOAO-OT-v1`, ADR-014: Euclidean cost, entropic regularisation 0.1, up to 1000 Sinkhorn iterations, stop threshold 1e-9) also reads the **unlabelled features of the whole target batch** to align the source before fitting the SVR; target labels are never read before scoring. We implemented a log-domain Sinkhorn solver independently and cross-checked it with the POT library. The authors' PCA baselines fit PCA on source + target features (transductive) and are reported as such. The two modes are always reported in separate tables.

### 3.5 Metrics, abstention and intervals

MAE in pp (= 100 x fraction), RMSE and bias in fraction, R2 unitless and never clamped. Predictions are scored **unclipped** (primary); clipping to [0, 1], as the authors do, is reported as secondary. Macro = unweighted mean over the five folds. `LOAO-UQ-v1` (ADR-017, preregistered before scoring) fits everything on source rows: a Mahalanobis out-of-distribution score on 10 PCA components (`ood_maha`) and a model-disagreement score; thresholds at retention goals 1.00/0.90/0.80/0.70 from cross-fitted source scores; 90 % intervals from cross-fitted source residuals (`pooled` and the wider `max_domain`). A score is "useful" only if, at goal 0.80, selective MAE beats full MAE in at least 4/5 folds **and** the rank-based selective MAE beats the 5th percentile of random rejection in at least 4/5 folds.

## 4. Results

### 4.1 Data audit

Section 3.1. The 330 files reproduce the published counts; the discrepancy ledger is empty. The archive copy available to us did not match the published MD5 (probably re-zipped on macOS) although its 330 `.dat` files are identical to the owner's copy; byte-level integrity against the published archive is unverified.

### 4.2 Inductive baselines on unseen adulterants (run `20261103T042740Z_01a9d42_b1c2dfa1`)

| Held-out adulterant (n) | mean_y MAE (pp) | svr_raw MAE (pp) / R2 | pca_svr MAE (pp) / R2 | pls MAE (pp) / R2 |
|---|---:|---:|---:|---:|
| soybean (60) | 22.73 | 9.47 / 0.793 | 26.18 / -0.677 | 10.75 / 0.773 |
| peanut (60) | 22.73 | 7.05 / 0.918 | 12.06 / 0.727 | 4.78 / 0.954 |
| rapeseed (90) | 22.73 | 12.97 / 0.601 | 15.53 / 0.419 | 4.79 / 0.941 |
| corn (90) | 22.73 | 5.14 / 0.948 | 19.28 / -1.189 | 5.20 / 0.940 |
| walnut (30) | 22.73 | 7.23 / 0.896 | 9.70 / 0.813 | 6.99 / 0.907 |
| **macro** | **22.73** | **8.37 / 0.831** | **16.55 / 0.019** | **6.50 / 0.903** |

PLS has the lowest macro error, but no model is best on every fold (svr_raw wins on corn), and source-only PCA + SVR fails badly on soybean and corn. On the Luhua-only subset (run `20261103T042759Z_01a9d42_2fbd19b6`, 30 spectra per fold) the ranking flips: svr_raw macro 6.95 pp / R2 0.859 versus PLS 8.64 pp / 0.828. With permuted source labels every model's mean macro R2 was at or below 0 (no single repeat above 0.06), so the benchmark does not reward memorised structure.

For orientation only: on the optimistic leave-one-measurement-round-out split (same adulterants in training; run `20261103T041143Z_ca43062_4097e86f`) PLS scored 1.37 pp. The gap to 6.50 pp is the cost of meeting a new adulterant.

### 4.3 Published-style OT adaptation (TRANSDUCTIVE; run `20261103T044749Z_7129cde_363deee6`)

> These numbers need a batch of unlabelled spectra from the same unseen adulterant and must never be read as single-file performance.

| Held-out adulterant | ot_svr MAE (pp) / R2 | no adaptation (inductive svr_raw) MAE (pp) / R2 |
|---|---:|---:|
| soybean | 4.64 / 0.958 | 9.47 / 0.793 |
| peanut | 4.38 / 0.964 | 7.05 / 0.918 |
| rapeseed | 3.73 / 0.966 | 12.97 / 0.601 |
| corn | 3.95 / 0.965 | 5.14 / 0.948 |
| walnut | 3.78 / 0.969 | 7.23 / 0.896 |
| **macro** | **4.09 / 0.964** | **8.37 / 0.831** |

Comparison with the **published** means (Sun et al. 2026; mean R2 over the five folds, scored with clipping as the authors do):

| Published column | Published mean R2 | ChemiProof measured, clipped | ChemiProof measured, unclipped (primary) |
|---|---:|---:|---:|
| Raw SVR | 0.831 | 0.831 | 0.831 |
| PCA | 0.693 | 0.693 | -1.394 |
| "PARAFAC" (computed as 10-component PCA in the released code) | 0.659 | 0.659 | -2.494 |
| OT-SVR | 0.965 | 0.964 | 0.964 |
| OT-SVR, POT solver | 0.965 | 0.965 | 0.965 |

The published means reproduce within 0.001 R2. Per-fold published values were not available, so only means are compared. The PCA-type baselines match only when clipped; unclipped they extrapolate far outside [0, 1] (up to 17 of 90 predictions per fold), so clipping hides large errors. Sinkhorn converged in every fold.

**Batch composition stress test (exploratory, ADR-015; scores on the stress batch):**

| Target batch | OT MAE (pp) / R2, mean over folds | no adaptation MAE (pp) / R2 |
|---|---:|---:|
| random, 10 spectra | 9.17 / 0.791 | 8.61 / 0.826 |
| random, 20 spectra | 6.40 / 0.900 | 8.78 / 0.801 |
| single brand, all ratio levels | 3.16 / 0.974 | 8.74 / 0.807 |
| only olive fraction < 0.5 | 21.80 / -3.214 | 9.57 / 0.022 |
| only olive fraction > 0.5 | 21.94 / -2.594 | 7.18 / 0.585 |

OT helps when the target batch covers the full label range; it is no better than no adaptation for small random batches and is far worse when the batch is label-skewed, which a real batch of suspect samples could easily be.

### 4.4 Abstention and intervals (INDUCTIVE; run `20261103T054226Z_914e8ed_ac6bfcef`)

At the 0.80 retention goal the observed retention was 0.83 (`ood_maha`) and 0.73 (`model_disagreement`) because shift moves score distributions. For PLS, `ood_maha` abstention lowered macro MAE from 6.50 to 6.22 pp (rejected samples: 8.02 pp) but improved only 3 of 5 folds. The usefulness rule was met by **1 of 6** model/score pairs, the weak pca_svr with model disagreement (16.55 -> 10.16 pp). H3 is therefore **not supported** for the models that matter.

Observed coverage of nominal 90 % intervals (empirical; no guarantee):

| Model / variant | corn | peanut | rapeseed | soybean | walnut | mean width (pp) |
|---|---:|---:|---:|---:|---:|---:|
| pls / pooled | 0.92 | 1.00 | 0.94 | **0.65** | 1.00 | 27.2 |
| pls / max_domain | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 44.7 |
| svr_raw / pooled | 1.00 | 1.00 | **0.60** | 0.83 | 1.00 | 41.7 |

Pooled intervals under-cover the hardest system; the conservative variant covers everything only by being about 45 pp wide, which is too wide to be useful on a 0-100 % scale.

### 4.5 Robustness and brand

Uniform baseline offsets (up to 10 % of the maximum) and global intensity scaling (0.5-2.0) leave the features unchanged up to 7e-16 (the preprocessing removes them), so errors are identical. Additive Gaussian noise matters: at 0.3 %, 1 % and 3 % of the spectrum maximum PLS MAE rises from 6.50 to 7.92, 17.7 and 51.3 pp, while `ood_maha` withholds 20 %, 57 % and 100 % of estimates (17 % clean); the flag detects gross degradation even though it does not rank ordinary errors. By brand, PLS errors on held-out soybean concentrate in OliVera (13.63 pp vs Luhua 7.88 pp); other cells range 3.62-6.99 pp. This is descriptive: brand and adulterant are entangled and no brand-effect test was run. Dropping the Savitzky-Golay step changed PLS macro MAE only from 6.50 to 6.15 pp (exploratory; no conclusion drawn).

## 5. Discussion

**H1 supported:** errors differ by target system (PLS 4.78-10.75 pp; svr_raw 5.14-12.97 pp), and the model ranking changes with brand makeup, so a single headline number hides real variation. **H2 supported, with a condition that changes its meaning:** OT halves the error relative to no adaptation when it receives a full, balanced, unlabelled batch of the new adulterant, and our independent implementation reproduces the published result. But this is a statement about a laboratory design in which every target batch spans all ten ratios. With small or label-skewed batches the gain disappears or reverses, and we have no label-free test for whether a real batch is safe to align. **H3 not supported:** simple label-free scores do not tell the model when it is wrong across these five systems. **H4 supported:** soybean (especially with OliVera) and noisy spectra remain unsafe, and intervals under-cover exactly there.

The comparison with Sun et al. (2026) is therefore one of agreement on arithmetic and disagreement on emphasis: the published means are correct under the published protocol, but the transductive requirement, the clipping of baselines and the sensitivity to batch composition belong next to the headline R2.

**Alternative explanations and confounders.** Brand is entangled with adulterant (walnut has one brand), so part of each fold's difficulty may be brand rather than adulterant. Measurement rounds may not be independent replicates. PLS was chosen as the screening model after its LOAO results were seen, so 6.50 pp is optimistic for the selected procedure. Calibration residuals in LOAO-UQ-v1 are slightly optimistic because hyper-parameters were chosen by a CV that saw each calibration adulterant. Everything comes from one instrument, one laboratory, lab-made binary blends at ten levels between 9.1 % and 90.9 % olive oil.

## 6. Conclusion

**Demonstrated** on this benchmark: (1) a leakage-tested LOAO evaluation in which the best single-spectrum model estimates olive-oil fraction with a macro error of 6.50 pp across five unseen adulterants, with a worst fold of 10.75 pp; (2) an independent reproduction of the published OT result (mean R2 0.964 vs 0.965), together with the finding that it depends on a complete, label-balanced unlabelled batch; (3) the negative result that simple label-free abstention and source-calibrated intervals are not reliably useful here; (4) bit-for-bit or round-off-level reproducibility from a fresh clone and environment.

**Not demonstrated:** performance on commercial products, other adulterants, multi-adulterant blends, other instruments or laboratories; any guaranteed coverage or detection; any authenticity, safety or compliance decision. These need external data that was never used for model choice.

## References

- Sun, R., Li, Q., Wang, T., et al. (2026). Open-world quantification of olive-oil adulteration from fluorescence spectra via optimal-transport alignment. *npj Science of Food*. https://doi.org/10.1038/s41538-026-01037-6
- Sun, R., Li, Q., Wang, T., et al. (2026). EEM fluorescence spectral dataset of olive-oil adulteration samples across five adulterant systems. Zenodo. https://doi.org/10.5281/zenodo.19755088 (CC BY 4.0)
- Authors' code (read for method details only; no license, nothing copied): https://github.com/Zhanjun-Li/fluorescence_NonLinear
- Peyré, G., & Cuturi, M. (2019). Computational Optimal Transport. https://arxiv.org/abs/1803.00567 (entropic OT, Sinkhorn)
- Flamary, R., et al. (2021). POT: Python Optimal Transport. *JMLR* 22(78), 1-8. Used as a cross-check solver (MIT license).
- Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *JMLR* 12, 2825-2830 (PLS, SVR, PCA).
- Conformal prediction under distribution shift, background: https://aims.stanford.edu/textbook/src/chap9.html

## Appendix A: reproducibility

| Item | Value |
|---|---|
| Code | branch `m7/release`; runs produced at the commits in their run IDs; release tag NOT created (needs reviewer signoff) |
| Environment | original runs: Python 3.12.15, macOS 26.5.1 arm64 (owner's machine); clean reproduction: Python 3.12.13, macOS 26.6.2 arm64 (collaborator's machine); both numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1; POT 0.9.7.post1 in the reproduction (POT's version is not recorded in run `environment.json`); all pins in `constraints.txt` |
| Upstream dataset | Zenodo 19755088; published MD5 `dfad908d186e584b96b6070d90cbeec4` (NOT matched by our copy, see 4.1); manifest sha256 `31c718edd95b4faca5f0f3fe68871870dc6f1b5d2307a8af93e8ce3712765495` |
| Preprocessing | `author_v1` (ADR-011), parameters in each run's `config_resolved.yaml` |
| Splits | deterministic LOAO folds; `splits.csv` and `fold_manifest.csv` in each run |
| Screening model | FINAL-PLS-v1, `model.npz` sha256 `bbcff343011aa4e7ac674f7151affd6f6cf164f09acd68557f0a05e47261aa4c` |
| License decision | PROPOSED, owner decision pending (ADR-019) |

| Run (results/...) | Protocol / mode | Config sha256 (prefix) |
|---|---|---|
| `M1_20261103T034431Z_b050b36-dirty_33c0ba5b` | data audit | n/a |
| `M2_20261103T041143Z_ca43062_4097e86f` | source-internal leave-one-round-out, inductive (optimistic) | `5ddb4697` |
| `M3_20261103T042740Z_01a9d42_b1c2dfa1` | LOAO-v1, inductive, all 330 | `2c427bf8` |
| `M3_20261103T042759Z_01a9d42_2fbd19b6` | LOAO-v1, inductive, Luhua only | `c98da747` |
| `M3_control_*` | permuted-label negative control (exploratory) | n/a |
| `M4_20261103T044749Z_7129cde_363deee6` | LOAO-OT-v1, transductive, all 330 | `417e41b5` |
| `M4_20261103T044812Z_7129cde_44fba4b8` | LOAO-OT-v1, transductive, Luhua only | `70f0c2f5` |
| `M4_batch_sensitivity_*` | OT batch stress test (exploratory) | n/a |
| `M5_20261103T054226Z_914e8ed_ac6bfcef` | LOAO-UQ-v1, inductive | `f93cfb4c` |
| `M6_final_20261103T074605Z_ce2423b_82b39d6c` | FINAL-PLS-v1, model card | `82b39d6c` |

**Commands** (repository root, dataset extracted to `data/raw/extracted/`; see `docs/release/RELEASE_REVIEW.md` for the full third-party checklist):

```bash
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -c constraints.txt -e '.[dev]'
chemiproof dataset audit
chemiproof experiment run --config config/experiments/baseline.yaml          # M3, LOAO-v1
chemiproof experiment run --config config/experiments/ot_transductive.yaml   # M4, LOAO-OT-v1
chemiproof experiment uncertainty --config config/experiments/uncertainty_loao.yaml   # M5
chemiproof model train-final                                                 # FINAL-PLS-v1
chemiproof experiment compare results/<committed run> results/<your rerun>   # T021
```

**Clean reproduction (CP-701, 2026-11-03):** a fresh `git clone` at `27c6efb` with a new virtual environment (`uv`, no cache) reran every locked and final config. `chemiproof experiment compare` (absolute tolerance 1e-9 fraction) found all tables equal: M2 max |diff| 8e-15, M3 2.3e-14 and 0, M4 0 and 0, M5 7.2e-16; negative controls and batch stress tests equal to 1e-16; FINAL-PLS-v1 `model.npz` sha256 identical. A different machine and Python patch release from the original runs, but the same OS family (macOS arm64) and the same numerical libraries, so other platforms and library versions remain untested. Evidence: `results/M7_release_20261103/validation_report.md`.
