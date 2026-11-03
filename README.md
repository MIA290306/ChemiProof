# ChemiProof 🧪

**Explainable & Uncertainty-Aware Olive-Oil Adulteration Research**  
**Status: `v1.0.0` research release (2026-11-03).** Research report, model card and data card: [`docs/release/`](docs/release/). Every locked run reproduces from a fresh clone and environment. **Not reviewed by an external scientist** (waived for this release, ADR-020).  
**Owner:** Mia Ho (`MIA290306`) · **Created:** 2026-10-24

ChemiProof is a reproducible **research prototype** for estimating **olive-oil volume fraction** from **excitation–emission matrix (EEM) fluorescence spectra** and evaluating when a predictive system ought to **abstain** under unfamiliar adulterant distributions.

> **Not a certified authenticity test.** Outputs are experimental screening estimates, not regulatory findings, legal proof of adulteration, or food-safety decisions.

## What makes this worth building?

A 2026 research article showed that alignment via optimal transport (OT) can support regression on an adulterant system not seen during supervised training. ChemiProof extends that research workflow toward **auditable benchmarking, provenance, uncertainty, domain-shift stress testing, selective prediction and honest reporting**. **It does not claim to invent the published OT approach.**

### Verified primary sources

- Sun et al. (2026), *Open-world quantification of olive-oil adulteration from fluorescence spectra via optimal-transport alignment*, *npj Science of Food*. DOI: https://doi.org/10.1038/s41538-026-01037-6
- Spectral data: Sun et al. (2026), Zenodo record 19755088, DOI: https://doi.org/10.5281/zenodo.19755088
- Authors' code: https://github.com/Zhanjun-Li/fluorescence_NonLinear

Dataset: **330 EEM measurements**, five adulterants (**soybean 60, peanut 60, rapeseed 90, corn-germ 90, walnut 30**), **35 excitation × 270 emission channels**, three EVOO brands with unequal representation. These published counts were confirmed by our audit (M1; [`docs/release/DATA_CARD.md`](docs/release/DATA_CARD.md)).

## Results (measured by ChemiProof; five leave-one-adulterant-out folds)

> **Not a certified authenticity test.** Laboratory binary blends, one instrument and laboratory. Unit: olive-oil volume fraction; MAE in percentage points (pp). Full tables, run IDs and caveats: [`docs/release/RESEARCH_REPORT.md`](docs/release/RESEARCH_REPORT.md).

**Inductive (one spectrum at a time)**, run `M3_20261103T042740Z_01a9d42_b1c2dfa1`:

| Held-out adulterant | soybean | peanut | rapeseed | corn | walnut | macro |
|---|---:|---:|---:|---:|---:|---:|
| PLS MAE (pp) | 10.75 | 4.78 | 4.79 | 5.20 | 6.99 | **6.50** (R² 0.903) |
| raw SVR MAE (pp) | 9.47 | 7.05 | 12.97 | 5.14 | 7.23 | 8.37 (R² 0.831) |

**Transductive (needs a whole unlabeled batch of the new adulterant; not single-file performance)**, run `M4_20261103T044749Z_7129cde_363deee6`: our independent OT-SVR gives macro MAE **4.09 pp**, mean R² **0.964**, versus **0.965 published** by Sun et al. (2026). With random 10-spectrum batches it is no better than no adaptation (9.17 vs 8.61 pp), and with label-skewed batches it collapses (R² about -3).

**Trust signals (negative result)**, run `M5_20261103T054226Z_914e8ed_ac6bfcef`: a preregistered label-free abstention rule met its usefulness criterion for 1 of 6 model/score pairs; 90 % intervals covered 0.65-1.00 of held-out samples per fold, so coverage is not guaranteed.

## Read this first

- New to Food Chemistry + tech? Start with [`docs/vi/START_HERE_VI.md`](docs/vi/START_HERE_VI.md) and [`docs/vi/ROADMAP_VI.md`](docs/vi/ROADMAP_VI.md).
- Coding with Claude Code? Read [`CLAUDE.md`](CLAUDE.md), then [`docs/00_DOCS_INDEX.md`](docs/00_DOCS_INDEX.md), and work on **the first incomplete milestone** only.
- Need product requirements? [`docs/product/01_PRD.md`](docs/product/01_PRD.md).
- Need the actual scientific protocol? [`docs/science/02_RESEARCH_PROTOCOL.md`](docs/science/02_RESEARCH_PROTOCOL.md).
- Need phase-specific deliverables and stop/go gates? [`docs/project/06_MILESTONES.md`](docs/project/06_MILESTONES.md).

## Core workflows

1. **Inductive single-sample baseline:** a source-trained model handles one EEM without seeing a target batch. Claims limited to measured inductive performance.
2. **Transductive research batch:** OT aligns to a **batch of unlabeled target spectra** and predicts that batch. The batch is required for the published-style transductive method; never market its metrics as single-upload performance.
3. **Selective prediction research:** measure error–coverage trade-offs and rate of abstention. Prediction intervals require explicit assumptions; no blanket 90% coverage guarantees under unseen adulterants.

## Intended scientific outputs

- Verifiable data inventory, data dictionary, QC report and provenance trail.
- Five leave-one-adulterant-out evaluations with **per-adulterant** MAE, RMSE, R², bias, plus macro-average and dispersion.
- Source-only baseline, published-style OT benchmark, an **abstention/robustness extension**, negative controls and reproducibility artifacts.
- A local Streamlit research explorer with **clear non-clinical/non-regulatory warnings**, model mode and limitations visible.
- *(Planned extension M6.5, specification only)* A **Power BI quality-analytics dashboard**, "ChemiProof: Food Authenticity & Quality Intelligence", built from validated experiment exports for Food Science, QA/QC and laboratory audiences. Python stays the only place where metrics are computed. Power BI Desktop is Windows-only, so macOS users need a Windows machine, VM or cloud desktop to build or verify it. See [`docs/bi/18_POWER_BI_SPEC.md`](docs/bi/18_POWER_BI_SPEC.md).
- A short research report that cites baseline work and separates replicated findings from original additions.

## Power BI layer (planned, milestone M6.5)

Architecture: **Zenodo dataset → Python data processing → machine learning and uncertainty evaluation → validated analysis outputs → export pipeline → Power BI dashboard**. Power BI never trains models, tunes thresholds or reads raw spectra; every KPI must reproduce from the exported outputs with Python; protocols and modes are never mixed. Status: **specification only, nothing built**. Documents: [`docs/bi/18_POWER_BI_SPEC.md`](docs/bi/18_POWER_BI_SPEC.md), [`docs/bi/19_POWER_BI_DATA_MODEL.md`](docs/bi/19_POWER_BI_DATA_MODEL.md), [`docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`](docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md).

## How to reproduce

Requires the official dataset from https://doi.org/10.5281/zenodo.19755088 (not included here), extracted to `data/raw/extracted/`. Python 3.12, macOS or Linux; details in [`docs/engineering/11_DEV_SETUP.md`](docs/engineering/11_DEV_SETUP.md) and the third-party checklist in [`docs/release/RELEASE_REVIEW.md`](docs/release/RELEASE_REVIEW.md).

```bash
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -c constraints.txt -e '.[dev]'
pytest -q -m "not dataset"                     # no data needed
chemiproof dataset audit                       # manifest sha256 31c718ed..., 330 = 60/60/90/90/30
chemiproof experiment run --config config/experiments/baseline.yaml          # inductive LOAO
chemiproof experiment run --config config/experiments/ot_transductive.yaml   # transductive OT
chemiproof experiment uncertainty --config config/experiments/uncertainty_loao.yaml
chemiproof experiment compare results/<committed run> results/<your rerun>   # must exit 0
chemiproof model train-final && chemiproof app # local research explorer
```

## License / data distribution

- Dataset: Sun et al. (2026), Zenodo 10.5281/zenodo.19755088, **CC BY 4.0**. It is not redistributed here; raw spectra, data-derived figures and the trained model file are git-ignored.
- Authors' code: no license (all rights reserved); read for method details only, nothing copied.
- ChemiProof's code: **MIT** ([`LICENSE`](LICENSE)). Documentation and research report: **CC BY 4.0**. Decision: ADR-019 in [`docs/project/13_DECISION_LOG.md`](docs/project/13_DECISION_LOG.md).
- Power BI layer: not delivered (M6.5 needs Windows; M7 does not depend on it).

## Roadmap

**M0** Repo setup → **M1** Dataset audit → **M2** Chemometric baselines → **M3** Open-world evaluation → **M4** OT reproduction → **M5** Uncertainty/abstention → **M6** App/reports → *(optional extension)* **M6.5** Power BI food-quality intelligence → **M7** Validation/public release. M6.5 does not change M0-M7 and does not block M7.

All status indicators and metrics must be computed from real runs; **never manufacture a result or mark a milestone complete to make the demo look impressive.**
