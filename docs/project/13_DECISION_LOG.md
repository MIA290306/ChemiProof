# Architecture Decision Records (ADRs) / Scientific Decision Log

## ADR-001 — Research before dashboard

- **Date:** 2026-10-24
- **Status:** ACCEPTED as initial scope
- **Decision:** Validate data and LOAO evaluation before a UI.
- **Why:** The product is only credible if input labels/axes and comparison method are verified.
- **Consequences:** M0–M5 focus on parsing, experiments and uncertainty. Streamlit is M6.

## ADR-002 — Independent single-sample versus batch adaptation

- **Date:** 2026-10-24
- **Status:** ACCEPTED
- **Decision:** Define `inductive_single` and `transductive_batch` as separate and never present one mode's metric as the other.
- **Why:** Published OT method uses unlabeled target batch X; a single-file prediction does not have this target distribution.
- **Consequences:** Different tests, artifacts and UI entry points.

## ADR-003 — Use external original dataset, not embedded archive

- **Date:** 2026-10-24
- **Status:** ACCEPTED provisionally (subject to rights verification)
- **Decision:** Source Zenodo `10.5281/zenodo.19755088`, keep raw third-party data outside tracked Git, record hash and citation.
- **Why:** Reproducibility + risk of unauthorized distribution.
- **Consequences:** Need opt-in M1 download, manifest and license check.

## ADR-004 — Primary metric protocol

- **Date:** 2026-10-24
- **Status:** ACCEPTED
- **Decision:** Five LOAO outer folds, per-fold MAE/RMSE/R²/bias, macro plus pooled, source-only inner model selection.
- **Why:** Random split would not measure unseen adulterant performance; unequal group sizes affect pooled scores.
- **Consequences:** More stringent and honest comparison; a single aggregate score is insufficient.

## ADR-005 — Calibration claims

- **Date:** 2026-10-24
- **Status:** ACCEPTED
- **Decision:** No nominal prediction-interval coverage guarantee under LOAO shift. Report empirical target coverage and selective error at coverage.
- **Why:** Standard exchangeability requirements may fail when target adulterant changes.
- **Consequences:** UI uses “empirical research interval” rather than certainty.

## ADR-006 — Basic stack

- **Date:** 2026-10-24
- **Status:** ACCEPTED at M0 (2026-11-02), pending owner sign-off with M0 review
- **Decision proposal:** Python + NumPy/Pandas/SciPy/scikit-learn, Pytest/Ruff, POT only in M4, Streamlit in M6. No backend/auth/LLM services.
- **Why:** Appropriate to single-user reproducible scientific research.
- **Resolved at M0:** CPython 3.12 (Homebrew 3.12.15, arm64); `python -m venv` + pip with a `constraints.txt` produced by `pip freeze` (no `uv`); `argparse` CLI; Pydantic + PyYAML (`safe_load` only) for config. Verified via `pip install --dry-run --only-binary=:all:` that NumPy, SciPy, scikit-learn, pandas, Pydantic, PyYAML, pytest, ruff, pre-commit all have arm64 wheels for 3.12. Runtime deps at M0 are only numpy, pydantic, PyYAML; SciPy/scikit-learn/pandas are added when first needed (M1/M2) and the lock is regenerated then. Locked versions: see `constraints.txt`.

## ADR-007 — M0 additions to the status taxonomy and artifact policy

- **Date:** 2026-11-02
- **Status:** PROPOSED (needs owner approval)
- **Problem:** The taxonomy in docs/engineering/04_ARCHITECTURE.md had no code for a missing dataset, an invalid config or an unimplemented stage; M0 acceptance requires an explicit `DATASET_NOT_AVAILABLE` path. Also `.gitignore` blocked `results/*`, which conflicts with the required `results/M0.../validation_report.md`.
- **Decision:** Add `DATASET_NOT_AVAILABLE`, `INVALID_CONFIG`, `NOT_IMPLEMENTED` to `chemiproof.errors.StatusCode`; use directory name `results/M0_foundation/` and un-ignore only that directory.
- **Consequences:** No scientific methodology changed. Experiment configs must keep `status: NOT_RUN` (validator rejects anything else) so a hand edit cannot claim a finished run; `ui.allow_transductive_single_sample` must be `false` (ADR-002 enforced in code).
- **Owner signoff:** pending

## ADR-008 — Label convention: folder ratio `a：b` = olive : adulterant (parts by volume)

- **Date:** 2026-11-02
- **Status:** ACCEPTED 2026-11-02 under the owner's blanket delegation ("I fully delegate and trust your decisions"); owner review of this ADR still requested at the M1 gate
- **Problem:** Folder names carry ratios `10：1 ... 1：10` (full-width colon) whose parts always sum to 11, so volume fractions are k/11, not tenths. Direction (which number is olive) was ambiguous, which is an M1 BLOCK condition.
- **Evidence (documentary):** Zenodo record 19755088 (read 2026-11-02): "ten olive-oil volume fractions ranging from 9.09% to 90.91%" and "Directory structure encodes adulterant type, measurement round, and olive-oil-to-adulterant ratio". 1/11 = 9.09%, 10/11 = 90.91%.
- **Evidence (empirical, supporting only):** mean intensity in the chlorophyll band (ex 400-420 nm, em 660-690 nm), averaged per ratio folder over the 3 rounds: higher at `10：1` than at `1：10` in all 11 brand-oil pairs; Spearman rho vs `a` = +0.96, +0.99, +0.39, -0.04, +0.31, +0.82, +1.00, +0.99, +0.90, +1.00, +1.00 (three OliVera pairs are weak). This is a consistency check by the agent, not proof; chlorophyll content also varies by adulterant and brand.
- **Decision proposed:** `olive_fraction = a / (a + b)` where folder is `a：b`; record `label_source = zenodo_description_19755088` plus the probe as evidence; manifest rows must keep the raw folder string. Adulterant fraction = 1 - olive_fraction (binary mixtures only).
- **Open caveats:** the Zenodo text is a description, not a methods section; the full-text methods of the paper were not obtained (only the abstract page loaded). Owner may ask the corresponding authors to confirm.
- **Owner signoff:** delegated to agent 2026-11-02; explicit review pending
- **Update 2026-11-02 (author code, read-only):** the authors' loader (`code/src/data_loader.py`, `_parse_ratio`) documents `10:1 -> 10/(10+1) = 0.909`, i.e. label = a/(a+b) with a = olive. This independently confirms the convention from the primary code (the repo is unlicensed, so it was only read, not copied).
- **Update 2026-11-02 (visual check):** the real EEM gallery shows the ~675 nm emission / ~400 nm excitation chlorophyll peak strongest at `10：1` and clearly weaker at `1：10` for all five adulterants, with broad 400-500 nm emission (excitation ~350 nm) growing at `1：10`, consistent with ADR-008.

## ADR-009 — Dataset provided as an extracted folder, no zip

- **Date:** 2026-11-02
- **Status:** ACCEPTED as a limitation
- **Decision:** Use the owner-provided extracted copy at `data/raw/extracted/` (gitignored). The published MD5 `dfad908d...` applies to `data.zip` and cannot be checked; integrity is instead tracked by SHA-256 of every `.dat` in the M1 manifest. If the zip is ever re-downloaded, verify its MD5 and compare file hashes.
- **Consequences:** M1 acceptance test T003 (checksum verified) can only be PASS-with-limitation; ZIP traversal protection (T002) is still implemented and tested with synthetic malicious zips, but is not exercised by the real data.
- **Owner signoff:** pending

## ADR-010 — M1 implementation decisions

- **Date:** 2026-11-02 · **Status:** ACCEPTED (agent, under owner delegation)
- **Excitation orientation:** files list excitation 640 -> 300 nm (descending). The parser applies ONE explicit rule (reverse to ascending, keeping each intensity row attached to its wavelength) and records `source_excitation_order` per sample. Tested to keep the (excitation, emission) pairing intact (`tests/unit/test_parser.py`). No other reordering or interpolation exists.
- **Negative intensities:** all 330 files contain negative cells (22,982 total; min -22.37, max 10,617.7 Counts/uA). Kept raw, flagged `NEGATIVE_INTENSITY` (WARN). Treatment (baseline correction etc.) is a documented M2 decision; no clamping.
- **Brand/adulterant mapping:** exact Chinese folder-name fragments mapped to {Luhua, OliVera, Earl Grey} x {soybean, peanut, rapeseed, corn, walnut}; unknown names raise `UNVERIFIED_LABEL`. Mapping agrees with article Table 2 (via 03_DATA_CONTRACT) in brand sets and counts.
- **replicate_id left empty:** three folders ("rounds") per level are probably the 3 replicates, but this is not proven; the leakage-safe grouping used from M2 on is the stronger `(brand, adulterant, ratio)` cell, not `replicate_id`.
- **Plots:** matplotlib added (dev + `plot` extra) for static PNG QC galleries; Plotly remains the choice for the M6 UI. PNGs are git-ignored because they are derived from third-party data.
- **Licenses:** dataset CC BY 4.0 (Zenodo API); authors' code has no license (read-only reference, independent reimplementation). See docs/science/10_REFERENCES_AND_LICENSES.md.
- **Owner signoff:** delegated; review pending

## ADR-011 — M2 preprocessing and reference-protocol findings (from READING the authors' unlicensed code)

- **Date:** 2026-11-02 · **Status:** ACCEPTED (agent, under owner delegation)
- **Facts read** (`code/reproduce.py`, `code/src/preprocessing.py`; nothing copied): default pipeline = NaN->0, reverse the 640->300 nm axis to ascending, **no Rayleigh/Raman removal**, baseline = subtract the global minimum of the EEM, Savitzky-Golay window 5 / polyorder 2 applied along the **emission** axis only (the paper text says both axes), divide by the spectrum's global maximum, flatten to 9,450. Reference SVR: `kernel=poly, degree=3, C=1.0, gamma='scale'`, epsilon left at the scikit-learn default 0.1, labels in fraction [0,1] (so epsilon = 10 percentage points), no feature standardization, predictions clipped to [0,1] before scoring.
- **Decision:** preprocessing `author_v1` = exactly the pipeline above, **prespecified** from the code (not tuned on any labels) and used by every model. Versions with other choices (e.g. smoothing on both axes) must be new named versions and cannot be chosen using outer-fold scores. Our feature order is (excitation, emission) C-order whereas the authors' is (emission, excitation); poly-kernel SVR, PCA, PLS and Euclidean OT are invariant to feature permutation, so results are unaffected.
- **Label scale / epsilon (CP-204):** y = fraction in [0,1]; reference epsilon 0.1 = 0.1 fraction. We keep epsilon = 0.1 for the paper-fixed `svr_raw`.
- **Reference-protocol deviations we will NOT copy** (for the discrepancy table in M4): (1) predictions clipped to [0,1] before scoring (we score unclipped and report clipped separately, as required by docs/science/05_EVALUATION_PLAN.md); (2) their PCA/CORAL/MMD baselines are fitted on source + unlabeled target X (transductive; we also provide a source-only PCA); (3) their CORAL/MMD `n_components` is selected using the labels of the corn target fold (target-label tuning, which our protocol forbids); (4) one-line OT: Euclidean cost, entropic Sinkhorn reg=0.1, numItermax=1000, stopThr=1e-9, row-normalized plan, barycentric projection of source onto target (to be reimplemented independently in M4).
- **M2 evaluation protocol (`source_internal_loro`):** leave-one-measurement-round-out over all 330 spectra (3 folds), hyperparameters selected by an inner leave-one-round-out inside the training rounds only. It measures replicate/round generalization **within known adulterants**, is optimistic by construction, and is **not** evidence of unseen-adulterant generalization (that is the LOAO benchmark of M3).
- **Owner signoff:** delegated; review pending

## ADR-012 — Wider inner-CV grids for pca_svr and pls (development decision, inner CV only)

- **Date:** 2026-11-02 · **Status:** ACCEPTED (agent, under owner delegation)
- **Observation:** in the first complete M2 run (grid v1: PCA 5/10/20/40, PLS 2/4/6/8/12; run `20261103T041046Z_54def60_4097e86f`, discarded after this ADR) PLS selected its largest candidate (12) in 3 of 3 folds, so the grid was probably too narrow. v1 macro results (leave-one-round-out): mean_y 22.73 pp / R2 0.000, svr_raw 5.10 pp / 0.947, pca_svr 7.08 pp / 0.903, pls 1.98 pp / 0.991.
- **Decision:** grid v2 = PCA 5/10/20/40/80, PLS 2/4/6/8/12/16/24/32, still selected only by the inner leave-one-round-out CV inside each training set (components are capped by the smallest inner fold). No held-out round, and no adulterant label from any future outer fold, took part in this choice; the M2 protocol is not the M3 benchmark.
- **Why it is allowed and its limit:** it is a within-training model-selection refinement, but it was prompted by looking at the M2 outer-round scores, so M2 numbers are exploratory-development numbers. M3 will freeze grid v2 and the protocol before scoring any held-out adulterant (docs/science/05_EVALUATION_PLAN.md section 2).
- **Owner signoff:** delegated; review pending

## ADR-013: LOAO-v1 protocol freeze (before scoring any held-out adulterant)

- **Date:** 2026-11-02 · **Status:** ACCEPTED (agent, under owner delegation); owner review requested at the M3 gate
- **Frozen protocol `LOAO-v1`:** five outer folds `LOAO-{soybean,peanut,rapeseed,corn,walnut}` (test = every sample of that adulterant, train = the other four; deterministic, no randomness); inductive mode only; preprocessing `author_v1`; models `mean_y`, `svr_raw` (poly, degree 3, C=1, gamma=scale, epsilon=0.1), `pca_svr` (PCA grid 5/10/20/40/80 + the same SVR), `pls` (grid 2/4/6/8/12/16/24/32); hyper-parameters chosen by an inner **leave-one-source-adulterant-out** CV on the 4 source adulterants only (components capped by the smallest inner fold); metrics MAE/RMSE/bias/R2 per fold, macro (unweighted) and pooled, primary scoring unclipped, clipped secondary; seed 20261024.
- **Files frozen (SHA-256, taken before the first scored run):** `config/experiments/baseline.yaml` `60ca7cf5cd1bfac7...`; `config/experiments/loao_luhua_only.yaml` `f8f3878d8d27c42a...`; `src/chemiproof/modeling/baselines.py` `a932daedfaf2de5b...`; `src/chemiproof/spectra/preprocess.py` `f694baa01f934caeb...`. Any change to these files requires a new protocol id (LOAO-v2) and a new ADR; results of different protocol ids are never merged.
- **Two locked runs are planned and nothing else:** (1) all 330 samples (`baseline.yaml`); (2) sensitivity restricted to brand Luhua, the only brand present for all five adulterants, which removes brand imbalance as a confounder (`loao_luhua_only.yaml`). Both are run once on a clean tracked git tree; `run_class: locked` refuses a dirty tree. Every run (exploratory or locked) is appended to `results/experiment_registry.csv`.
- **Disclosure about earlier scoring:** the dataset-marked tests (`pytest -m dataset`) execute the LOAO pipeline on the real data to check structure and determinism. Their outputs go to temporary directories and are discarded, only structural assertions (fold sizes, determinism, canary pass) are made, and no configuration was changed in response to them.
- **Safeguards in code:** independent fold audit (`audit_folds`), and a label-shuffle canary run after every LOAO experiment (shuffles each fold's held-out labels, refits, requires identical predictions and hyper-parameters, otherwise raises `QC_REVIEW_REQUIRED`).
- **Not frozen / out of scope:** OT (M4) and abstention (M5) get their own protocol ids.
- **Owner signoff:** delegated; review pending

## Future ADR template

```text
## ADR-NNN — Short title
Date:
Status: PROPOSED / ACCEPTED / REJECTED / SUPERSEDED
Problem:
Options and tradeoffs:
Decision:
Evidence / reference:
Reproducibility implications:
Owner signoff:
```

**Protocol-changing ADRs must be approved before locked final evaluation.**
