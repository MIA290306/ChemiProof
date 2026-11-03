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
