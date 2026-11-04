# `chemiproof` package

| Module | Responsibility |
|---|---|
| `data/` | `.dat` parser, labels (`olive_fraction = a/11`, ADR-008), manifest and audit, safe ZIP inspection, synthetic fixtures |
| `spectra/` | QC flags, `author_v1` preprocessing (ADR-011), plots |
| `modeling/` | baselines (SVR, PCA+SVR, PLS), OT (Sinkhorn + SVR), `FINAL-PLS-v1` artifact |
| `evaluation/` | fold protocols (LOAO, leave-one-round-out), metrics, runner, controls, rerun comparison |
| `uncertainty/` | OOD and disagreement scores, calibration, selective risk, perturbations (`LOAO-UQ-v1`) |
| `ui/` | Streamlit research explorer |
| `experiments.py`, `pipeline.py`, `cli.py` | experiment orchestration, screening entry points, command line |
| `errors.py`, `config.py`, `provenance.py` | status codes, validated configs, run IDs and environment capture |

Interfaces and invariants: `docs/engineering/04_ARCHITECTURE.md`.
