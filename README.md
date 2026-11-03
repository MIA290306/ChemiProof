# ChemiProof 🧪

**Explainable & Uncertainty-Aware Olive-Oil Adulteration Research**  
**Status: M0-M4 (tooling, data audit, baselines, LOAO benchmark, optimal-transport replication) awaiting owner review. The published OT numbers are reproduced independently, but the OT gain needs a batch of unlabeled spectra with the right composition (it collapses on skewed or tiny batches); abstention and UI are not built yet.**  
**Owner:** Mia Ho (`MIA290306`) · **Created:** 2026-10-24

ChemiProof is a reproducible **research prototype** for estimating **olive-oil volume fraction** from **excitation–emission matrix (EEM) fluorescence spectra** and evaluating when a predictive system ought to **abstain** under unfamiliar adulterant distributions.

> **Not a certified authenticity test.** Outputs are experimental screening estimates, not regulatory findings, legal proof of adulteration, or food-safety decisions.

## What makes this worth building?

A 2026 research article showed that alignment via optimal transport (OT) can support regression on an adulterant system not seen during supervised training. ChemiProof extends that research workflow toward **auditable benchmarking, provenance, uncertainty, domain-shift stress testing, selective prediction and honest reporting**. **It does not claim to invent the published OT approach.**

### Verified primary sources

- Sun et al. (2026), *Open-world quantification of olive-oil adulteration from fluorescence spectra via optimal-transport alignment*, *npj Science of Food*. DOI: https://doi.org/10.1038/s41538-026-01037-6
- Spectral data: Sun et al. (2026), Zenodo record 19755088, DOI: https://doi.org/10.5281/zenodo.19755088
- Authors' code: https://github.com/Zhanjun-Li/fluorescence_NonLinear

Published dataset summary: **330 EEM measurements**, five adulterants (**soybean 60, peanut 60, rapeseed 90, corn-germ 90, walnut 30**) and **35 excitation × 270 emission channels** per measurement. The original work also involves three EVOO brands, with unequal brand representation across adulterants. These are *published descriptions*; verify them against archive contents in Milestone M1.

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
- A short research report that cites baseline work and separates replicated findings from original additions.

## Quick start status

**Do not run commands from docs expecting an application today:** this pack is an implementation blueprint. First the agent must create and test the Python package and inspect the actual raw .dat files. Full environment commands become valid at the end of M0/M1; see [`docs/engineering/11_DEV_SETUP.md`](docs/engineering/11_DEV_SETUP.md).

## License / data distribution

Do **not** commit raw Zenodo data or authors' code into this repository. Verify the exact data and code license before redistribution. Cite the original authors and dataset DOI. Choose a license for **your own** code only after rights review.

## Roadmap

**M0** Repo setup → **M1** Dataset audit → **M2** Chemometric baselines → **M3** Open-world evaluation → **M4** OT reproduction → **M5** Uncertainty/abstention → **M6** App/reports → **M7** Validation/public release.

All status indicators and metrics must be computed from real runs; **never manufacture a result or mark a milestone complete to make the demo look impressive.**
