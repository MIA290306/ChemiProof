# Power BI Acceptance Tests and Definition of Done (M6.5)

**Status: NO TEST HAS BEEN WRITTEN OR RUN.** Every test below is `NOT RUN`. Automated tests (BI001 to BI014) are intended for `pytest` on any platform; Power BI tests (BI020 to BI032) need Power BI Desktop on Windows and are manual with saved evidence. Never mark a test PASS without its evidence.

Related: `docs/bi/18_POWER_BI_SPEC.md`, `docs/bi/19_POWER_BI_DATA_MODEL.md`, `docs/engineering/07_ACCEPTANCE_TESTS.md` (general test policy).

## 1. Automated export tests (Python, no Power BI needed)

| ID | Given | Expected result | Status |
|---|---|---|---|
| BI001 | Same run directories exported twice | All table files are byte-identical (only `created_utc` in `export_manifest.json` differs) | NOT RUN |
| BI002 | Any export | Every table matches `config/bi/export_contract.yaml`: names, order, types, nullability | NOT RUN |
| BI003 | Any export | Primary keys unique and non-null; every foreign key resolves (rule V-02) | NOT RUN |
| BI004 | Any export | `olive_fraction`/`y_true_fraction` in [0,1] and equal to `dim_sample`; all `*_pp` equal `100 x fraction`; residual/abs-error/clip columns consistent (V-03, V-04) | NOT RUN |
| BI005 | Real M3 and M4 runs | Metrics recomputed from `fact_predictions` equal `fact_model_metrics` (fold, macro, pooled; unclipped and clipped) within 1e-9 (V-05) | NOT RUN |
| BI006 | Run directories with mixed protocols | Every fact row carries `run_id`, `model_key`, `mode`; `protocol_id` assigned by the map; an unmapped run gets `UNREGISTERED`, `is_registered=false`, `is_headline=false` (P-2) | NOT RUN |
| BI007 | Run with `git_dirty=true` or missing hash fields | Missing provenance rejects the run; dirty locked run exported with `is_headline=false` and a warning (V-06) | NOT RUN |
| BI008 | LOAO run lacking `leakage_audit.json` or with a failed canary | Run rejected with `BI_RUN_REJECTED` (V-07) | NOT RUN |
| BI009 | Export containing published numbers | They appear only in `fact_published_reference` with `is_measured=false`; no relationship, no row in any measured table (V-11) | NOT RUN |
| BI010 | Dataset directory hashed before and after export | Identical; exporter wrote nothing inside `data/` or a source run folder; existing export folder is not overwritten (V-12) | NOT RUN |
| BI011 | Any export | No intensity arrays, no absolute paths, no user names or e-mail addresses in any column (V-10, V-12) | NOT RUN |
| BI012 | Runs without M5 outputs | `fact_uncertainty` and `fact_selective_risk` are empty, `uncertainty_available=false`; no fabricated rows | NOT RUN |
| BI013 | Uncertainty fixture with a threshold fitted on target labels, or missing method/level fields | Export rejected (V-09) | NOT RUN |
| BI014 | CSV and Parquet exports of the same runs | Identical values and types (Parquet only if the optional extra is installed) | NOT RUN |

## 2. Power BI tests (Windows, Power BI Desktop; manual with evidence)

| ID | Given | Expected result | Evidence | Status |
|---|---|---|---|---|
| BI020 | Report opened from the `.pbip` project | Tables, columns and relationships equal the contract (22 relationships, single-direction); no extra calculated tables | model-view screenshot, TMDL diff against the contract | NOT RUN |
| BI021 | KPI reconciliation file produced by Python from the same export | Every KPI card/measure equals the Python value (counts exact; ratios within 1e-6) for each headline run | table of Power BI value vs Python value | NOT RUN |
| BI022 | Two runs or two protocols selected in the Run slicer | KPI cards show the "select one run" state, not a number (run guard) | screenshot | NOT RUN |
| BI023 | Each of the four pages | Required elements of `docs/bi/18_POWER_BI_SPEC.md` section 6 are present; header strip and footer present; units in titles | page checklist | NOT RUN |
| BI024 | Wording lint over the report definition and visible text | None of: adulterated, fraud detected, fake, safe, unsafe, compliant, illegal, authenticity score, guaranteed coverage; no threshold or traffic-light semantics | lint output | NOT RUN |
| BI025 | Export without uncertainty (before M5) and with empty issue table | Page 3 shows only the banner; Page 1 shows "0 rejected files"; no placeholder values | screenshots | NOT RUN |
| BI026 | A transductive run selected | Transductive warning banner visible; OT results never share a series with inductive models; published values only in their labeled panel | screenshots | NOT RUN |
| BI027 | New export folder pointed to by `ExportFolder`, then Refresh | Data and KPIs update and still reconcile (BI021); a wrong `contract_version` stops the refresh with a visible error | refresh log, screenshots | NOT RUN |
| BI028 | Page 3 with a real uncertainty export (needs M5) | Method card shows the actual interval method, nominal level, calibration protocol, `threshold_fit_source`; coverage is labeled empirical; retention is shown beside selective MAE | screenshots | NOT RUN |
| BI029 | Accessibility check | Colour-blind-safe palette, alt text on all visuals, logical tab order, contrast adequate | checklist | NOT RUN |
| BI030 | Footer and About | Cites Sun et al. (2026), Zenodo DOI 10.5281/zenodo.19755088 and CC BY 4.0; states "not a certified test" | screenshot | NOT RUN |
| BI031 | Repository contents | No `.pbix`, cache, raw data or absolute paths committed; `.pbip` text files open without error | `git ls-files` listing, open log | NOT RUN |
| BI032 | Reviewer who did not build the report follows `bi/powerbi/README.md` on a clean Windows machine | Report opens, refreshes and reconciles | reviewer log | NOT RUN |

## 3. Release-blocking failures (hard fail for M6.5)

- A KPI that does not reproduce from the export with Python (BI021).
- Any visual or measure that mixes protocols, modes, scoring or aggregation levels without showing them.
- A leakage path: a run exported without a passed canary, a threshold fitted on target labels, or Power BI used to select a model on held-out data.
- A published number presented as a ChemiProof measurement.
- Wording that implies adulteration, safety, compliance or a guaranteed interval coverage.
- Reporting the dashboard as built or validated without the Windows verification evidence.
- Raw data, spectra or `.pbix` data caches committed to Git.

## 4. Definition of Done for M6.5

M6.5 is complete only when all of the following hold, with evidence recorded in `docs/project/14_PROGRESS_LOG.md` and a milestone review (`templates/MILESTONE_REVIEW.md`):

1. The export pipeline exists with code, tests BI001 to BI014 PASS on real runs, and reproducible commands.
2. The data contract, protocol map and KPI catalog are final and match `config/bi/export_contract.yaml`.
3. The Power BI project opens on Windows, passes BI020 to BI027 and BI029 to BI031 (BI028 if M5 exists), with screenshots taken from real exports only.
4. Every KPI reconciles (BI021) and the refresh procedure is reproducible by a second person (BI032).
5. Limitations are visible in the report and documented (macOS environment, Windows verification, one dataset, five adulterant systems).
6. The owner has reviewed the report; only the owner marks M6.5 `ACCEPTED`.

## 5. Windows verification procedure (for the person who builds or reviews the report)

1. Install Power BI Desktop on Windows 10 or later. Sign-in is not required for Desktop.
2. Obtain the repository and run `chemiproof export bi ...` (or receive a validated `exports/bi/<export_id>/` with its `export_manifest.json`; confirm the file hashes).
3. Open `bi/powerbi/ChemiProofBI.pbip`; set the `ExportFolder` parameter; refresh.
4. Run the Python KPI reconciliation script, then compare with the report (BI021).
5. Walk through BI022 to BI030, saving screenshots into the review folder.
6. Record the result, the Power BI Desktop version, the export id and the git commit in the milestone review.

## 6. Status summary

| Group | Tests | Status |
|---|---|---|
| Automated export | BI001 to BI014 | all NOT RUN (exporter not implemented) |
| Power BI (Windows) | BI020 to BI032 | all NOT RUN (no Power BI project exists) |
