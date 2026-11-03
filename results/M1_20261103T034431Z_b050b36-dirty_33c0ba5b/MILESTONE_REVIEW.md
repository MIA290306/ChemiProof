# Milestone M1 — Evidence-based Handoff

**Date:** 2026-11-02 · **Milestone:** M1 Data provenance, parsing and EEM QC
**Status:** REVIEW REQUIRED (agent cannot self-approve ACCEPTED) · **Owner reviewer:** Mia Ho
**Run ID:** `20261103T034431Z_b050b36-dirty_33c0ba5b` · full evidence: `results/M1_20261103T034431Z_b050b36-dirty_33c0ba5b/validation_report.md`

## Scope actually delivered

- Tasks: CP-101..CP-107 (license review, directory inspection, parser for the observed schema, ratio parsing, 330-record manifest and audit, real EEM heatmaps, malformed/corrupt/duplicate/axis tests).
- Behaviour: `chemiproof dataset inspect|audit|inspect-zip`, `chemiproof spectra plot`, `load_dataset()` that re-verifies every file's SHA-256, strict parser, safe ZIP inspection/extraction.
- Not implemented: preprocessing, models, metrics, splits (M2+).

## Scientific assumptions and protocol deviations

- Original spec: download the zip, check MD5, inspect without extraction. Actual: owner supplied an extracted folder (ADR-009); MD5 not checkable; per-file SHA-256 recorded instead.
- Label convention `olive_fraction = a/11` for folder `a：b` (ADR-008), accepted by the agent under the owner's blanket delegation; **owner explicit review requested**.
- Owner approval required? yes (ADR-008, ADR-009, ADR-010).

## Files and artifacts

| Path | Purpose | SHA/Run ID |
|---|---|---|
| `data/interim/sample_manifest.csv` (git-ignored) | 330-row manifest | sha256 `31c718edd95b4faca5f0f3fe68871870dc6f1b5d2307a8af93e8ce3712765495` |
| `results/M1_20261103T034431Z_b050b36-dirty_33c0ba5b/data_audit.json`, `qc_summary.csv`, `metadata_evidence.json` | audit | `20261103T034431Z_b050b36-dirty_33c0ba5b` |
| `results/M1_20261103T034431Z_b050b36-dirty_33c0ba5b/eem_examples.png` (git-ignored) | 10 real EEMs | `20261103T034431Z_b050b36-dirty_33c0ba5b` |
| `src/chemiproof/data/{parser,labels,manifest,zipsafe}.py`, `spectra/{qc,visualize}.py` | code | n/a |

## Executed verification

pytest (not dataset) exit 0, 90 passed; pytest (dataset, real data) exit 0, 3 passed; ruff check/format exit 0; audit exit 0. T001-T006 PASS (T003 with the MD5 limitation). GitHub Actions `ci` on head commit 2d6e03b: PASS (run 41574366884, https://github.com/MIA290306/ChemiProof/actions/runs/41574366884).

## Scientific results (if any)

`NO EXPERIMENTAL RESULTS YET` (data facts only: see validation report).

## Open blockers and adverse observations

1. Published-zip MD5 unverifiable; the data copy's integrity vs Zenodo is unproven.
2. ADR-008 evidence is documentary + spectral consistency; 3 OliVera pairs show a weak chlorophyll trend.
3. All 330 spectra contain negative intensities: M2 must decide and document a baseline treatment.
4. Brand imbalance is real and is a confounder (walnut = one brand only).

## Recommendations and next action

- Decision requested: review ADR-008/009/010.
- Conditions before M1 may be ACCEPTED: owner review (CI condition met: green run 41574366884).
- Suggested next milestone AFTER approval: M2 (preprocessing + baselines).
