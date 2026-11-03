# M7 release review: rights, citations, third-party rerun and external review (CP-703)

**Status:** REVIEW REQUIRED, 2026-11-03. The release is **not tagged**: it needs the owner's license decision and at least one external reviewer's signoff (`docs/project/06_MILESTONES.md`, M7 exit gate; `docs/project/15_RELEASE_AND_RESEARCH_REPORT.md`, final exit rule).

## 1. Rights and redistribution

| Item | Finding | Status |
|---|---|---|
| Zenodo dataset 19755088 | CC BY 4.0, open access (Zenodo API, 2026-11-02). Redistribution allowed with attribution. | Checked |
| Raw data in this repository | none tracked; `data/raw/` git-ignored; CI guard "no raw data tracked" | Checked (CI step) |
| Data-derived figures, arrays, `model.npz` | git-ignored (screenshots, PNGs, PCA components of the spectra) | Checked |
| Small derived tables in `results/` (per-sample predictions with sample IDs and true labels, metrics, audit counts) | tracked. CC BY 4.0 allows this with attribution; attribution is in every report and card. | **Owner to confirm** that publishing these tables is acceptable (ADR-019, question 2) |
| Authors' code `Zhanjun-Li/fluorescence_NonLinear` | GitHub reports no license = all rights reserved. Read for method details only; nothing copied; cited. | Checked |
| Paper figures | not reused; all ChemiProof figures are generated from our own runs | Checked |
| ChemiProof's own code and docs | **no license file yet** | **Owner decision** (ADR-019, PROPOSED) |
| Third-party Python packages | see section 2; all permissive, no copyleft in the runtime lock | Checked from installed metadata |

## 2. Third-party package licenses (from installed package metadata, `constraints.txt`, 2026-11-03)

Direct dependencies:

| Package | Version | License (as declared) | Used for |
|---|---|---|---|
| numpy | 2.5.4 | BSD-3-Clause (+ 0BSD, MIT, Zlib, CC0-1.0 parts) | arrays |
| scipy | 1.18.1 | BSD | Savitzky-Golay, numerics |
| scikit-learn | 1.9.1 | BSD-3-Clause | PLS, SVR, PCA |
| pydantic | 2.14.2 | MIT | config contracts |
| PyYAML | 6.0.3 | MIT | configs |
| pandas | 3.1.0 | BSD-3-Clause | UI tables |
| streamlit | 1.66.1 | Apache-2.0 | research explorer (extra `ui`) |
| plotly | 7.1.0 | MIT | explorer figures |
| matplotlib | 3.11.2 | PSF-based (matplotlib license) | run figures (extra `plot`) |
| POT | 0.9.7.post1 | MIT | OT cross-check (extra `ot-reference`) |
| pytest, ruff, pre-commit | 9.2.0, 0.17.3, 4.7.0 | MIT | development only |

Transitive packages (53 more) declare MIT, BSD, Apache-2.0, PSF or MPL-2.0 (`certifi`). Regenerate with:

```bash
python - <<'PY'
import importlib.metadata as md
for line in open("constraints.txt"):
    if "==" in line and not line.startswith("#"):
        m = md.metadata(line.split("==")[0])
        print(m["Name"], m["Version"], m.get("License-Expression") or m.get("License", "")[:60])
PY
```

Finding fixed in M7: `POT` (in the `dev` extra) was missing from `constraints.txt`; it is now pinned at 0.9.7.post1, the version the clean reproduction resolved.

## 3. Citation and attribution (where it appears)

`README.md` (sources section), `docs/release/RESEARCH_REPORT.md` (header, Contributions, References), `docs/release/DATA_CARD.md` (section 9), `docs/release/MODEL_CARD.md` (section 11), the explorer's Overview and Methods pages, and `docs/science/10_REFERENCES_AND_LICENSES.md`.

## 4. Third-party rerun checklist (for a reviewer or another student)

1. Clone the repository; check out the commit under review.
2. Download `data.zip` from https://doi.org/10.5281/zenodo.19755088 and record its MD5 (published: `dfad908d186e584b96b6070d90cbeec4`). Inspect it safely: `chemiproof dataset inspect-zip --archive data/raw/data.zip`. Extract the `.dat` folders to `data/raw/extracted/` (skip `__MACOSX/`).
3. `uv venv --python 3.12 .venv && source .venv/bin/activate && uv pip install -c constraints.txt -e '.[dev]'`
4. `pytest -q -m "not dataset"` (no data needed), then `chemiproof dataset audit` (must print manifest sha256 `31c718ed...` and 330 = 60/60/90/90/30), then `pytest -q -m dataset`.
5. Rerun the locked configs (each must report git dirty = False):
   `chemiproof experiment run --config config/experiments/baseline.yaml`, `... loao_luhua_only.yaml`, `... ot_transductive.yaml`, `... ot_luhua_only.yaml`, `chemiproof experiment uncertainty --config config/experiments/uncertainty_loao.yaml`, `chemiproof model train-final`.
6. For each rerun: `chemiproof experiment compare results/<committed run> results/<new run>`; exit 0 = every table equal within 1e-9 fraction. For FINAL-PLS-v1 compare `model_npz_sha256` in the two `model_card.json` files.
7. Report any difference with your OS, Python and package versions. A difference is a finding, not something to hide.

## 5. External review packet

Send: `docs/release/RESEARCH_REPORT.md`, `MODEL_CARD.md`, `DATA_CARD.md`, this file, `docs/project/13_DECISION_LOG.md` (ADR-008, 011, 013, 014, 015, 017, 018) and the repository link. Reviewer questions (from `15_RELEASE_AND_RESEARCH_REPORT.md`):

| # | Question | Reviewer answer |
|---|---|---|
| 1 | Is the spectral preprocessing (minimum subtraction, emission-axis Savitzky-Golay, max normalisation, no Rayleigh/Raman removal) physically plausible for EEM of edible oils? | pending |
| 2 | Is the label direction (folder ratio = olive : adulterant) convincing from the evidence in ADR-008 and the data card? | pending |
| 3 | Can you confirm that no target-domain label influenced fitting, hyper-parameter choice, thresholds or model choice (code paths listed in the 2026-11-03 audit entry of the progress log)? | pending |
| 4 | Can you reproduce at least one table from a fresh environment (section 4)? | pending |
| 5 | Is it clear which parts are Sun et al.'s method and which are ChemiProof's extension? | pending |
| 6 | Are errors, the soybean/OliVera concentration, brand imbalance, abstention failure and the transductive dependency visible rather than buried? | pending |
| 7 | Does any sentence claim more than the evidence (authenticity, safety, generality, guaranteed coverage)? | pending |

Reviewer name / role / date / verdict: **not yet assigned**.

## 6. Scientific integrity checklist (`15_RELEASE_AND_RESEARCH_REPORT.md`)

| Item | Status | Where |
|---|---|---|
| Every figure/table from a saved artifact with run ID | yes | report Appendix A; every table names its run |
| Counts and label units consistent with the audited manifest | yes | data card sections 3 and 5 |
| Experimental conditions and calibrations specified | yes | report 3.2-3.5; ADR-013/014/017 |
| Inductive and transductive shown separately | yes | report 4.2 vs 4.3; model card section 9 |
| Per-adulterant metrics, not only overall R2 | yes | report 4.2, 4.3 |
| Negative/ambiguous outcomes included | yes | report 4.3 stress test, 4.4, 5 (H3 not supported) |
| Interval coverage described as empirical under shift | yes | report 4.4; model card section 5 |
| Brands and unequal groups discussed as confounders | yes | report 4.5, 5; data card section 3 |
| Published scores separated from measured results | yes | report 4.3 table |
| No claim of definitive counterfeit detection or compliance | yes | notices in report, cards, README, UI |
| Source data and author code licenses checked before redistribution | yes (section 1); own license pending | ADR-019 |

## 7. Release gate status

| Gate item | Status |
|---|---|
| Clean-environment reproduction (CP-701, T021) | PASS: `results/M7_release_20261103/validation_report.md` |
| Source links / reuse statements (T022) | PASS for data and author code; ChemiProof license PENDING owner |
| Research report, model card, data card (CP-702) | DRAFT written; external review pending |
| README with real results and reproduce commands | done; screenshots NOT added (data-derived, owner decision, ADR-019 question 3) |
| External reviewer signoff | **NOT DONE** (blocking) |
| Tag `v1.0` | **NOT CREATED** (blocked by the two items above) |
| Power BI layer (M6.5) | not delivered (needs Windows; M7 does not depend on it, ADR-016) |
| Poster or 90-second demo | NOT DONE (needs screenshots decision) |
