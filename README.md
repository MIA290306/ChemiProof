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

## What is in this repository

| Part | What it does | Where |
|---|---|---|
| Data audit | Parses the 330 `.dat` EEMs, checks axes, labels and file hashes, writes a manifest | `chemiproof dataset audit`, `src/chemiproof/data/` |
| Inductive benchmark | Five leave-one-adulterant-out folds (`LOAO-v1`) for mean, SVR, PCA+SVR, PLS | `config/experiments/baseline.yaml` |
| Transductive OT | Independent re-implementation of the published OT-SVR (`LOAO-OT-v1`) and batch stress tests | `config/experiments/ot_transductive.yaml` |
| Trust study | Preregistered abstention, intervals and perturbations (`LOAO-UQ-v1`) | `config/experiments/uncertainty_loao.yaml` |
| Screening model | `FINAL-PLS-v1` with model card, OOD flag and empirical intervals | `chemiproof model train-final`, [`docs/release/MODEL_CARD.md`](docs/release/MODEL_CARD.md) |
| Research explorer | Local Streamlit app: data, benchmarks, single-file screening, batch research, methods | `chemiproof app` |
| Evidence | Every run's config, hashes, per-fold tables and reports | [`results/`](results/) |

Two information-access modes are always kept apart: **inductive** (one spectrum, no target data) and **transductive** (OT needs a batch of unlabelled target spectra; its numbers are never single-file performance).

## Documentation

- Research report, model card, data card, release review: [`docs/release/`](docs/release/)
- Protocol and evaluation plan: [`docs/science/02_RESEARCH_PROTOCOL.md`](docs/science/02_RESEARCH_PROTOCOL.md), [`docs/science/05_EVALUATION_PLAN.md`](docs/science/05_EVALUATION_PLAN.md)
- Decisions (ADR-001 to ADR-020) and progress evidence: [`docs/project/13_DECISION_LOG.md`](docs/project/13_DECISION_LOG.md), [`docs/project/14_PROGRESS_LOG.md`](docs/project/14_PROGRESS_LOG.md)
- Full map: [`docs/00_DOCS_INDEX.md`](docs/00_DOCS_INDEX.md) · Vietnamese onboarding: [`docs/vi/START_HERE_VI.md`](docs/vi/START_HERE_VI.md)
- Contributors using an AI coding agent: [`CLAUDE.md`](CLAUDE.md) / [`AGENTS.md`](AGENTS.md)

## Repository layout

```text
src/chemiproof/   package: data, spectra, modeling, evaluation, uncertainty, ui, cli
tests/            unit + integration tests (synthetic by default; `-m dataset` needs the real data)
config/           project, experiment and milestone configs
results/          committed run evidence (small tables and reports only)
docs/             product, science, engineering, project, release, bi (spec), vi
templates/        report and milestone-review templates
```

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
- Power BI layer (optional milestone M6.5): specified in [`docs/bi/`](docs/bi/), not built (Power BI Desktop needs Windows).

## Status and roadmap

M0-M7 delivered and released as `v1.0.0`. Open: an external methods review (waived for v1.0.0, ADR-020), a brand-effect test and an OT batch-composition check (M5 follow-ups), and the optional Power BI layer (M6.5).

All metrics come from real runs; nothing in this repository is a manufactured or tuned-to-impress result.
