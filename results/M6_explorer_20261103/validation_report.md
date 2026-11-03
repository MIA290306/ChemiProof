# M6 validation report: Research Explorer (Streamlit) and FINAL-PLS-v1

**Date:** 2026-11-03 · **Branch:** `m6/research-explorer` · **Agent:** Claude Code for Bruce1508 (collaborator) · **Owner:** Mia Ho
**Authority:** the owner asked (relayed by Bruce1508, 2026-11-03) to continue without waiting for her formal ACCEPTED of M0-M5; see ADR-018.

## What was built

- `FINAL-PLS-v1` screening artifact (ADR-018, declared before training): PLS on all 330 spectra, `n_components` by leave-one-adulterant-out inner CV, `ood_maha` flag and 90 % empirical interval calibrated by leaving each adulterant out. Code `src/chemiproof/modeling/final.py`; CLI `chemiproof model train-final`.
- `pipeline.screen_single` (inductive, exact wavelength-grid gate, withholds on the flag, flags in-sample uploads) and `pipeline.screen_batch` (transductive OT, opt-in, at least 10 files, duplicate refusal, convergence stop).
- Streamlit explorer `src/chemiproof/ui/app.py` (`chemiproof app`): Overview, Explore EEM, Benchmarks (+ LOAO-UQ-v1 abstention/interval section), Screen sample, Batch research, Methods & provenance (Markdown reproducibility report, model card download). Benchmark numbers are copied from the committed run folders; inductive and transductive results are shown in separate tables.

## Model artifact (real data)

| Field | Value |
|---|---|
| Run | `M6_final_20261103T074605Z_ce2423b_82b39d6c` (git `ce2423b`, dirty=False) |
| Manifest sha256 | `31c718edd95b4faca5f0f3fe68871870dc6f1b5d2307a8af93e8ce3712765495` |
| Selected `n_components` | 6 (inner leave-one-adulterant-out MAE 0.0561 fraction = 5.61 pp; a selection score, optimistic, not a test) |
| OOD threshold (`ood_maha`, goal 0.80, 330 cross-fitted scores) | 5.320 |
| 90 % half-width, pooled / max_domain | 0.1048 / 0.1602 fraction (10.5 / 16.0 pp) |
| `model.npz` sha256 | `bbcff343011aa4e7ac674f7151affd6f6cf164f09acd68557f0a05e47261aa4c` (git-ignored; identical on a second training run, and on the earlier run `M6_final_20261103T074230Z_f22ae1d_82b39d6c`) |

**There is no independent evaluation of this model.** Its only performance evidence is LOAO-v1 for the same procedure (PLS macro MAE 6.50 pp, optimistic because PLS was selected after that result).

## Executed verification

| Command / test | Exit | Result | Status |
|---|---|---|---|
| `pytest -q -m "not dataset"` | 0 | 229 passed, 9 deselected | PASS |
| `pytest -q -m dataset` (real data present) | 0 | 9 passed (incl. new `test_m6_final_model_rebuilds_the_committed_card`) | PASS |
| `ruff check .`; `ruff format --check .` | 0; 0 | clean | PASS |
| `chemiproof model train-final` (twice, clean tree) | 0; 0 | identical `model.npz` sha256 | PASS |
| T013 single-file transductive refused; batch < 10 refused | - | `TRANSDUCTIVE_BATCH_REQUIRED` (`test_loao_run.py`, `test_final_model.py`) | PASS |
| T019 malformed / non-ASCII / NaN / wrong grid upload | - | refused with UX wording (`test_final_model.py`, `test_ui_app.py`, screenshot 06) | PASS |
| T020 valid file, no trained artifact | - | "Research model not available ..." (`test_ui_app.py::test_no_model_gives_honest_message`) | PASS |
| T023 research-screening wording, unit, no certification | - | AppTest wording checks + forbidden-phrase scan on all six pages; screenshot 04 | PASS |
| Saved arrays reproduce scikit-learn PLS / PCA scorer | - | max abs diff <= 1e-10 (synthetic) | PASS |
| Tampered `model.npz` | - | refused (`NO_TRAINED_MODEL`) | PASS |

## Manual walkthrough (Playwright, Chromium, 2026-11-03)

Local app on the collaborator's Mac with the real dataset. Screenshots in `screenshots/` (git-ignored: several show third-party spectra).

1. Overview (`01`): measured LOAO tables split into inductive and transductive; published reference in its own table labelled "not a ChemiProof measurement".
2. Explore EEM (`02`): audited sample, validation strip, heatmap axes in nm, intensity in Counts/uA, raw/processed toggle, slice with data-table alternative.
3. Benchmarks (`03`): fold selector, n and brand makeup, metric table, worst fold, estimated-vs-actual plot, LOAO-UQ-v1 risk-coverage curve with random-rejection band, usefulness verdict, coverage table, failure cases.
4. Screen sample (`04`): `peanut_olivera_R1_06-05` -> estimate 0.60 (60 %), interval 0.49-0.70 fraction, OOD 1.85 < 5.32. **In-sample file** (one of the 330 training spectra): this demonstrates the UI, it is not a test.
5. Screen sample (`05`): `walnut_luhua_R2_01-10` -> OOD 6.01 > 5.32 -> "Review required — estimate withheld"; IN_SAMPLE warning shown.
6. Screen sample (`06`): malformed file -> "No estimate: validation failed".
7. Batch research (`07`): 30 walnut files, consent checkbox, Sinkhorn converged (228 iterations), batch manifest id, IN_SAMPLE 30/30 warning. No error metric is reported for this run because every file is a training spectrum.
8. Methods (`08`), small screen 390 px (`09`): DOI links, label rule, preprocessing, calibration caveat, export buttons; layout readable at phone width.
9. Keyboard: with the section radio focused, ArrowDown moved Overview -> Explore EEM.

## Not done / limitations

- No contrast audit or screen-reader test was run (NOT RUN); only keyboard section switching and the 390 px layout were checked. Charts have data-table alternatives.
- Screenshots are local only; the UI tests use synthetic models and the committed CSV/JSON artifacts.
- The batch path (source = all 330) has no evaluation at all; label-skewed batches are known to fail (ADR-015).
- `ood_maha` did not meet its preregistered usefulness rule for PLS in M5; the UI says it is a weak cue.
- Transformed-spectrum download (UX spec "only if rights permit") was not implemented.
