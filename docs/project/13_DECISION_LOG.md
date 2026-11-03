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

## ADR-014: LOAO-OT-v1 protocol freeze (transductive OT, before scoring any held-out adulterant with it)

- **Date:** 2026-11-02 · **Status:** ACCEPTED (agent, under owner delegation); owner review requested at the M4 gate
- **Mode:** `transductive_batch`. Information access: the SOURCE features and labels (4 adulterants) plus the UNLABELED feature matrix of the held-out adulterant (the whole batch, 30-90 spectra). Held-out labels are first read by the scoring function after predictions exist. The OT/baseline functions have no target-label parameter (signature test), and a label-shuffle canary re-runs every fold with shuffled held-out labels and requires identical predictions and diagnostics.
- **Frozen method `ot_svr`:** cost = Euclidean distance between preprocessed (`author_v1`) spectra, unnormalized; entropic Sinkhorn, uniform marginals, epsilon 0.1, max 1000 iterations, tolerance 1e-9 on the squared L2 error of the target marginal; barycentric projection of the SOURCE onto the target batch (row-normalized plan times Xt; target features untouched); reference SVR (poly, degree 3, C 1, gamma scale, epsilon 0.1 fraction) fitted on projected source + source labels, then predicts the untouched target batch. No hyper-parameter is tuned (all fixed at the published values).
- **Variants and controls (all prespecified, no tuning):** `ot_svr_pot` (same method solved by POT's `ot.sinkhorn` called as the authors describe: measures solver sensitivity); `author_pca50` and `author_pca10` (PCA fitted on source + unlabeled target X, then the same SVR; the authors' "PARAFAC-10" column is PCA-10 in their code); `svr_no_adaptation` (same SVR on the same features without the batch; inductive information; the only valid like-for-like control).
- **Solver choice rule (label-free):** the independent log-domain solver is primary because it is correct at any cost scale. Before freezing, only label-free diagnostics were inspected on the real data: Euclidean costs span 0.36-12.8 (so exp(-M/0.1) stays above 1e-56, no float underflow), POT converges without warning with marginal errors about 1e-9, and our solver reaches the tolerance in 171-371 iterations in all 10 folds (5 folds x all-330 and Luhua-only). A non-converged Sinkhorn raises `NUMERICAL_NONCONVERGENCE` and stops the run; nothing is scored silently. These probes read features only, never held-out labels.
- **Finding recorded before freezing:** the plans of our solver and POT agree to about 1e-11 when both are solved tightly, but a degree-3 polynomial SVR with `gamma='scale'` fitted on projected features is hypersensitive to tiny plan differences (projected source rows have very small variance, so gamma is large). The loose published tolerance lets the two stopping rules end at slightly different points (about 1e-6 on plan entries), so `ot_svr` and `ot_svr_pot` may predict differently. This is reported, not tuned away.
- **Files frozen (SHA-256 prefixes, before the first scored OT run):** `config/experiments/ot_transductive.yaml` `b4274e84d6b79692`; `config/experiments/ot_luhua_only.yaml` `44b244d4f9bed524`; `src/chemiproof/modeling/ot.py` `984583f300f626fe`; `src/chemiproof/modeling/baselines.py` `a932daedfaf2de5b`; `src/chemiproof/spectra/preprocess.py` `f694baa01f934cae`. A change requires protocol LOAO-OT-v2 and a new ADR.
- **Planned runs, nothing else:** (1) locked all-330 run; (2) locked Luhua-only sensitivity; (3) exploratory batch-size/composition sensitivity (random batches of 10 and 20 spectra, 5 seeded draws each, and every single-brand batch) to quantify why a single file is not a batch; (4) real-data structural OT tests are added only AFTER runs 1-2, so no real-data OT scoring happened before the freeze.
- **Required wording everywhere:** "TRANSDUCTIVE RESEARCH MODE: needs a batch of unlabeled target spectra; never advertise as single-file deployment performance". `screen_single` refuses the transductive mode with `TRANSDUCTIVE_BATCH_REQUIRED`.
- **Owner signoff:** delegated; review pending

## ADR-015: label-skewed batch stress test for OT (declared before it was run)

- **Date:** 2026-11-02 · **Status:** ACCEPTED (agent, under owner delegation)
- **Why:** OT with uniform marginals pairs every source spectrum with target spectra. In every LOAO fold the held-out batch has the same ten equally frequent olive levels as the source, so a good score might partly come from that distribution match instead of from spectral alignment. A real unlabeled batch will not have a uniform composition.
- **Design (exploratory, extends run (3) of ADR-014; `ot.py` and the frozen configs are untouched):** inside each LOAO fold, in addition to random batches of 10/20 and single-brand batches, score two label-skewed batches: all held-out samples with olive fraction < 0.5 ("skew_low_olive") and > 0.5 ("skew_high_olive") (levels 1-5 and 6-10), each only if it has at least 10 samples. Adaptation uses the batch FEATURES only; held-out labels are used (a) to define batch membership for the stress scenario and (b) for scoring. Compared with `svr_no_adaptation` on the same samples. No result of this run feeds back into any frozen protocol.
- **Prediction (stated in advance):** if OT relies on a matching label distribution, OT's error will grow clearly on skewed batches while the no-adaptation control stays roughly the same. This is a stress test, not a tuning step.
- **Owner signoff:** delegated; review pending

## ADR-016: Power BI as a presentation layer (milestone M6.5), specification only

- **Date:** 2026-11-03 · **Status:** ACCEPTED as a plan; implementation NOT STARTED
- **Context:** the owner wants the project to speak to Food Science, QA/QC and laboratory-data audiences. Power BI is a common tool in that world. The scientific pipeline (M0-M5) and the Streamlit explorer (M6) must stay intact.
- **Decision:** (1) Power BI is an **extension layer** that reads validated experiment outputs through a documented, versioned export contract; it never trains, tunes, or computes the metrics of record. (2) The work is a new milestone **M6.5** between M6 and M7 with prerequisites M5 and M6; M0-M7 keep their numbers and meaning. (3) **M7 does not depend on M6.5**: Power BI Desktop is Windows-only and the owner develops on macOS, so making the release depend on it would let tooling availability block the scientific release; if M6.5 is not accepted, the release states "Power BI layer: not delivered". The owner may change this. (4) Export format: **CSV default**, Parquet optional behind an optional extra `bi` (`pyarrow`); CSV needs no new dependency and keeps the "minimal components" preference of `CLAUDE.md`. (5) **Protocol identity** is mandatory: `protocol_id` comes from a versioned protocol map seeded with the five runs that exist; unmapped runs are `UNREGISTERED` and never headline. (6) Project format **`.pbip` (text)** rather than `.pbix` (binary, embeds data); `.pbix` and caches are git-ignored. (7) Documents live in `docs/bi/` as numbers 18-20 (instead of the root-level `docs/18_...` suggested in the request) to follow the topic folders of the reorganized docs; `docs/00_DOCS_INDEX.md` lists them.
- **Alternatives considered:** BI before M6 (rejected: needs M5 uncertainty data); Power BI inside the release gate (rejected, see above); a second Python dashboard only (kept as M6 Streamlit, unchanged); computing metrics in DAX (rejected: not reproducible against the protocol, breaks the "Python computes" rule).
- **Environment facts (Microsoft Learn, checked 2026-11-03):** Power BI Desktop requires Windows 10 or later (Windows on ARM needs a specific update; supported on Azure Virtual Desktop and Windows 365); the Power BI service needs a work or school account (personal e-mail not accepted directly; Desktop needs no sign-in); `.pbip` is plain text (TMDL/PBIR) that can be edited externally but is loaded and checked by Desktop. Consequence: in this macOS environment no dashboard can be built or validated, and M6.5 must be reported as `BLOCKED` rather than done if no Windows environment is available.
- **Consequences:** new documents `docs/bi/18-20`, `config/bi/export_contract.yaml`, new acceptance tests BI001-BI032, risks R21-R26, backlog CP-651 to CP-660, a docs-consistency test; no change to code, protocols or results.
- **Owner signoff:** pending

## ADR-017: LOAO-UQ-v1 preregistration (abstention, intervals, robustness; declared before any M5 scoring)

- **Date:** 2026-11-03 · **Status:** ACCEPTED (agent, under owner delegation); owner review requested at the M5 gate
- **Disclosure first:** the M3 and M4 outer-fold errors were already seen before this design was written. The design below therefore cannot claim to be blind to them. What is guaranteed is narrower: **every constant is fixed here, none is fitted to or tuned on any held-out adulterant**, and thresholds/intervals are computed from source-only cross-fitted quantities. Results are reported whatever they show, including failure.
- **Protocol id:** `LOAO-UQ-v1`. Mode: **inductive only** (single spectrum in, no batch). Primary models `svr_raw`, `pca_svr`, `pls` exactly as in LOAO-v1 (same preprocessing `author_v1`, same grids, same outer-selected hyper-parameters, so point predictions equal the LOAO-v1 ones). Transductive OT is **not** given abstention in this protocol (batch-level information is a different protocol); the batch-composition hazard found in ADR-015 stays a documented limitation and a report column (mean batch OOD score), not a scored rule.
- **Label-free risk scores (computed from X only; PCA fitted on the outer-train rows):**
  - `ood_maha` (PRIMARY): Mahalanobis distance of the spectrum in a 10-component PCA space of the training spectra, `sqrt(sum_k z_k^2 / lambda_k)`.
  - `model_disagreement` (SECONDARY): standard deviation of the three models' predictions for the same spectrum.
  - No combination, no extra score, no weighting is allowed in this protocol.
- **Source-only calibration set (cross-fitted):** for each outer fold and each of its 4 source adulterants `s`: fit on the other 3 source adulterants with hyper-parameters FIXED at the outer-selected values (no further tuning), predict `s`, record residual `y - y_hat` and the risk scores (PCA refitted on the 3). The 4 groups are pooled (about 240-330 points). Known optimism: the outer hyper-parameters were chosen by inner CV that also saw `s`, so calibration residuals are slightly optimistic; reported as a limitation.
- **Intervals:** `y_hat +/- q`, nominal level **0.90**. Two prespecified variants: `pooled` (q = the ceil((n+1)*0.9)/n empirical quantile of pooled absolute calibration residuals) and `max_domain` (q = the largest per-source-adulterant 0.90 quantile; conservative). Rejected with `INSUFFICIENT_CALIBRATION` when the pooled set has fewer than 100 points or fewer than 3 source groups (T016). Intervals are NOT clipped for scoring; clipped-to-[0,1] width is a secondary column. **No coverage guarantee under shift is claimed; observed coverage per held-out adulterant is the result.**
- **Abstention rule:** for retention goals **1.00 / 0.90 / 0.80 / 0.70**, the threshold is the corresponding quantile of the pooled cross-fitted source scores; a held-out sample abstains when its score is above the threshold. The OBSERVED target retention is reported next to the goal (shift can make it differ widely; that itself is a finding). The threshold uses no outer-test information (T018).
- **Selective-risk analysis:** (a) deployable, threshold-based `selective_mae`, `rejected_mae`, `rejection_rate`, `worst_retained_error` per fold, model, score; (b) diagnostic rank-based risk-coverage curve at retention 100,95,...,10 % using the same score; (c) comparator "random rejection" with 200 seeded repeats (seed 20261024) at the same retention, reported as mean and 5-95 % band; (d) retrospective oracle (reject largest true errors) only as a lower bound, labelled diagnostic; (e) Spearman correlation of score vs absolute error per fold (post-hoc diagnostic).
- **Usefulness rule, stated before running:** a score counts as useful for a model only if, at the 0.80 goal, threshold-based selective MAE is below the full-set MAE in at least **4 of 5** folds AND the rank-based selective MAE at 80 % lies below the random-rejection 5th percentile in at least 4 of 5 folds. Otherwise it is reported as **not useful on this benchmark**. Passing would still show nothing beyond these five systems.
- **Spectral perturbation tests (parameters fixed now; applied to held-out RAW spectra, then `author_v1` preprocessing; models stay fitted on clean source data):** additive Gaussian noise with sd = f * max of that spectrum, f in {0.001, 0.003, 0.01, 0.03}, 5 seeds each (seeds 20261024..28); uniform additive baseline offset g * max, g in {0.01, 0.03, 0.1}; global intensity scale in {0.5, 0.8, 1.25, 2.0}. Recorded: MAE change, mean score change, abstention rate at the 0.80 threshold. Expectation stated in advance: `author_v1` subtracts the global minimum and divides by the global maximum, so a uniform offset and a global scale should leave the features unchanged up to floating point; only noise should matter. If that expectation fails, it is reported as a pipeline finding.
- **Other analyses (exploratory, no feeding back):** failure-case table (largest errors, brand, level, score, abstained?), brand-wise breakdown (only brands present in verified manifest metadata; no brand-specific claim), one ablation (`author_v1` without Savitzky-Golay) on score ranking quality.
- **Honest limits to repeat in every report:** five domains only; one instrument and lab; brand confound; empirical, not guaranteed, coverage; abstention is a research cue, never a safety decision; a favourable mean on five systems says nothing about deployment.
- **Files to be frozen (SHA-256 prefixes, recorded in an addendum below BEFORE the first scored run):** `config/experiments/uncertainty_loao.yaml`, `src/chemiproof/uncertainty/*.py`, `src/chemiproof/modeling/baselines.py`, `src/chemiproof/spectra/preprocess.py`. A change needs protocol LOAO-UQ-v2 and a new ADR. Locked run requires a clean tracked git tree.
- **Freeze addendum (ADR-017), recorded after the code and its synthetic tests existed and BEFORE the first scored M5 run:** SHA-256 prefixes `config/experiments/uncertainty_loao.yaml` `569a35728409c966`; `src/chemiproof/uncertainty/scores.py` `068a923ecb258469`; `src/chemiproof/uncertainty/calibration.py` `f6bc520d0b830b85`; `src/chemiproof/uncertainty/selective.py` `53b0bdb0e95d0a4c`; `src/chemiproof/uncertainty/perturb.py` `d85ff0b49f208bb9`; `src/chemiproof/uncertainty/runner.py` `b0edac092f0904b4`; `src/chemiproof/modeling/baselines.py` `a932daedfaf2de5b`; `src/chemiproof/spectra/preprocess.py` `f694baa01f934cae`; Any later change needs protocol LOAO-UQ-v2 and a new ADR. Implementation notes: `report.py` and `__init__.py` only format output; the CLI entry is `chemiproof experiment uncertainty --config config/experiments/uncertainty_loao.yaml`. Planned scored runs, nothing else: one locked all-330 run. Synthetic tests (194 passing) include a held-out-label shuffle canary and the offset/scale invariance check.
- **Owner signoff:** delegated; review pending

## ADR-018: FINAL-PLS-v1, the inductive screening artifact for the M6 explorer (declared before training)

- **Date:** 2026-11-03 · **Status:** ACCEPTED (agent, under owner delegation); owner review requested at the M6 gate
- **Authority:** on 2026-11-03 the owner (Mia Ho), relayed by the collaborator Bruce1508 after merging PR #2, asked to continue the milestones without waiting for her formal ACCEPTED. M0-M5 therefore stay `REVIEW REQUIRED` (nobody but the owner may set `ACCEPTED`) and M6 starts under that instruction, as M1 started before M0 was accepted.
- **Problem:** M6 needs a single-file (inductive) estimate. Every LOAO-v1 model was fitted with one adulterant held out; a screening tool should use all 330 spectra. A model trained on everything has, by construction, **no independent test set**.
- **Decision (protocol id `FINAL-PLS-v1`, mode `inductive_single`):**
  - Model `pls` exactly as in LOAO-v1 (`author_v1` preprocessing, grid v2 2/4/6/8/12/16/24/32, `scale=False`), fitted on all 330 spectra; `n_components` chosen by the same inner CV, now leave-one-adulterant-out over all **five** adulterants.
  - Risk flag `ood_maha` (10-component PCA Mahalanobis, as LOAO-UQ-v1) fitted on all 330. Threshold = the 0.80 retention-goal quantile (`method="higher"`) of cross-fitted scores: for each adulterant, PCA refitted on the other four, the held-out adulterant scored. A spectrum above the threshold gets `ABSTAIN_OOD_RISK` and **its estimate is withheld**.
  - Interval: `y_hat +/- q`, nominal 0.90, `pooled` (primary) and `max_domain` half-widths from cross-fitted leave-one-adulterant-out residuals with `n_components` fixed at the final value (330 points, 5 groups; `INSUFFICIENT_CALIBRATION` below 100 points or 3 groups, as ADR-017).
  - Input gate: the parser of M1 plus an **exact** match of both wavelength axes to the training axes (`INVALID_WAVELENGTH_GRID` otherwise; no interpolation, invariant 8).
- **Why PLS, and the honest cost of that choice:** PLS had the lowest LOAO-v1 macro MAE among inductive models on all 330 spectra (6.50 pp, R2 0.903; svr_raw 8.37 pp, pca_svr 16.55 pp). Choosing it after seeing those outer-fold results makes 6.50 pp an **optimistic** estimate for the chosen procedure (best of three), and the ranking is not stable: on the Luhua-only subset svr_raw had the higher R2 (0.859 vs 0.828). The only performance evidence for `FINAL-PLS-v1` is LOAO-v1 / LOAO-UQ-v1 for the same procedure; the UI must say so.
- **Why the flag withholds although M5 found it weak:** in LOAO-UQ-v1 `ood_maha` did not meet the usefulness rule for PLS (selective MAE improved in 3 of 5 folds at goal 0.80, 6.50 -> 6.22 pp macro). Withholding is kept because the UX spec puts abstention first and withholding errs on the cautious side; the UI must state that the flag is a weak, research-level cue, not a validated detector. Calibration residuals carry the optimism disclosed in ADR-017 (`n_components` was chosen by a CV that also saw each held-out adulterant).
- **Batch research path:** `ot_svr` with the frozen LOAO-OT-v1 settings (ADR-014), source = all 330 labelled spectra, target = the uploaded batch (at least `MIN_TARGET_BATCH` = 10 files). This exact configuration was **never evaluated** (every M4 fold held one adulterant out of the source), and ADR-015 showed label-skewed batches collapse (R2 about -3). The UI shows the transductive warning, the batch manifest hash and the Sinkhorn diagnostics; a non-converged plan stops with `NUMERICAL_NONCONVERGENCE`.
- **Artifacts:** `results/M6_final_<run_id>/` with `model_card.json` (tracked: provenance, selected components, threshold, half-widths, hashes) and `model.npz` (git-ignored, because it holds the PCA mean and components of the third-party spectra; rebuilt deterministically by `chemiproof model train-final`). The npz holds plain arrays, is loaded with `allow_pickle=False` and its SHA-256 is checked against the card.
- **Not changed:** no frozen protocol file (`baselines.py`, `preprocess.py`, `ot.py`, `uncertainty/*`, the experiment configs) is edited; no new metric of record is computed; nothing here feeds back into LOAO-v1, LOAO-OT-v1 or LOAO-UQ-v1.
- **Review notes (PR #3, 2026-11-03):** (1) the threshold comes from cross-fitted scores while the deployed scorer is fitted on all 330 spectra (the same pattern as LOAO-UQ-v1), so training spectra score lower than unseen ones and are withheld less often than the 0.20 source rate; this is expected, not a calibration error. (2) The IN_SAMPLE flag matches the uploaded bytes' SHA-256 exactly; a training file whose bytes were altered (e.g. line endings rewritten) is not flagged. (3) Calibration is recomputed independently in `tests/integration/test_final_model.py` so a leak of the held-out adulterant into its own calibration fit would fail CI.
- **Owner signoff:** delegated; review pending

## ADR-019: release licensing and what the public repository may contain (M7)

- **Date:** 2026-11-03 · **Status:** PROPOSED; **owner decision required** (the agent may not choose a license for the owner's work)
- **Problem:** the M7 exit gate needs "no unknown legal permissions". The dataset is CC BY 4.0 and the authors' code has no license (read only, nothing copied), but ChemiProof's own code and documents have no license file, and the repository already tracks small data-derived tables (`results/*/predictions.csv` with sample IDs and true labels; metric and audit tables).
- **Options and tradeoffs:**
  - Code: **MIT** (shortest, permissive, common for portfolio/research code) or **Apache-2.0** (permissive plus an explicit patent grant and change-notice rule). Both are compatible with every runtime dependency (all permissive; `docs/release/RELEASE_REVIEW.md` section 2). A copyleft license (GPL) would restrict reuse by labs and is not suggested.
  - Documents and report: **CC BY 4.0** (matches the dataset) or the same license as the code.
  - No license: the repository stays "all rights reserved"; others may read it but not legally reuse it.
- **Proposed decision (for the owner to accept or change):** MIT for code; CC BY 4.0 for `docs/` and the report; keep the dataset, data-derived figures, screenshots and `model.npz` out of git; keep the small tracked result tables with the CC BY 4.0 attribution that already appears in every report and card.
- **Questions for the owner:** (1) which license, under which copyright holder name; (2) may the tracked per-sample tables in `results/` stay public (CC BY 4.0 allows it with attribution); (3) may README screenshots of the explorer that show real spectra be committed (also allowed by CC BY 4.0, but against the current conservative policy of ADR-003 / invariant 10).
- **Until decided:** no `LICENSE` file is added, no release tag is created, and the release review lists T022 as pending for ChemiProof's own license.
- **Owner signoff:** pending

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
