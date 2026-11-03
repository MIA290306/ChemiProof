# Acceptance Test Plan & Definition of Done

## Testing pyramid

**Unit:** numeric functions, .dat schema parser, ratio parsing, wavelength check, baseline subtraction, smoothing, normalization, metrics, OOD threshold, errors.  
**Integration:** raw ZIP→manifest→features; real parser to model; experiment runner→artifact; UI upload→valid/invalid outputs.  
**Science-validation:** LOAO split integrity, no target-label access, macro/pooled metric correctness, numerical convergence checks, counterfactual shuffles and validity assumptions.  
**End-to-end:** a second person recreates results with source DOI, checksum, config, code SHA and commands.

## Required test IDs

| ID | Given | Expected result | Gate |
|---|---|---|---|
| T001 | Valid synthetic 35×270 EEM + monotonic wavelength axes | Parses to proper orientation without mutation; intensity finite | M0/M1 |
| T002 | Malicious archive `../evil.dat` or absolute member path | Safe ZIP rejection | M1 |
| T003 | Real official archive (checksum verified) | File count, 330 EEM records + breakdown reconciled or documented with blocking deviation | M1 |
| T004 | Verified ratio name/metadata | Derived olive **volume** fraction matches source, e.g. ratios used in dataset | M1 |
| T005 | Missing/nonmonotonic axes or wrong size | Validation error with sample/path info | M1 |
| T006 | Duplicate IDs/identical raw hashes | Explicit duplicate diagnostic; no hidden collision | M1 |
| T007 | Preprocess a synthetic known EEM | Correct matrix shape, stable documented operations and QC | M2 |
| T008 | Source-only pipeline + held-out pseudo group | Fitted scaler/PCA/model never calls `fit` on target `X` in inductive mode | M2/M3 |
| T009 | Fixed toy y/pred values | MAE/RMSE/bias/R² match reference manual calculations | M2 |
| T010 | Manifest contains five groups | Each LOAO target comprises only one adulterant; no shared IDs | M3 |
| T011 | Shuffle entire target y before training | Trained model parameters, hyperparameters, abstention threshold stay identical | M3–M5 |
| T012 | OT target batch X provided (target y hidden) | Algorithm uses X for alignment only and logs mode=`transductive` | M4 |
| T013 | OT only one sample passed through single-sample API | Clear `TRANSDUCTIVE_BATCH_REQUIRED` error | M4/M6 |
| T014 | Sinkhorn plan computed | Marginal constraints close to expected within documented tolerance; convergence status recorded | M4 |
| T015 | Published reference metrics in config | Never appear in experiment output as measured results absent model run | M4 |
| T016 | Calibration with insufficient source data | Reject interval rather than invent confidence | M5 |
| T017 | Shifted target distribution, nominal 90% interval | Report **observed** coverage; no guarantee claim | M5 |
| T018 | Source-derived fixed abstention threshold | No target labels used in threshold fit; rejected samples counted | M5 |
| T019 | Intentionally invalid/malformed .dat upload | UI refuses prediction with accessible error | M6 |
| T020 | Valid single-file + no trained artifact | UI says model unavailable; no demo result presented as real | M6 |
| T021 | Frozen valid results set | Re-run matches metrics within documented numeric tolerance | M7 |
| T022 | Source links/data reuse statements | Correct license/attribution and no repackaged third-party data without permission | M7 |
| T023 | Screen using source EEM and label mode | UI clearly says research screening, target unit, no certification | M6/M7 |
| T024 | Negative/control shuffled source y | Model benchmark appropriately degrades or discrepancy scientifically investigated | M3 |

## Release-blocking scientific tests

- No target-label leakage — **hard fail**, independent of achieved R².
- Evidence report missing — **hard fail**.
- Unverified olive_fraction label mapping — **hard fail**.
- Model modes conflated — **hard fail**.
- External publication result copied into our performance table without distinguishing source — **hard fail**.
- Scientifically unsupported UI claims — **hard fail**.
- *(M6.5)* A BI visual or measure mixing protocols or modes, a KPI that does not reproduce from the export, or a dashboard reported as built/validated without Windows verification evidence — **hard fail** (see below).

## Power BI layer (milestone M6.5)

Tests BI001 to BI014 (automated export checks, any platform) and BI020 to BI032 (Power BI Desktop on Windows, manual with evidence) are defined in `docs/bi/20_POWER_BI_ACCEPTANCE_TESTS.md`, together with the M6.5 Definition of Done. Status of all of them: `NOT RUN` (nothing is implemented). They add to, and never replace, T001 to T024; the general evidence rules below apply.

## Minimum engineering standards

- Tests on synthetic fixtures run without external dataset/network.
- All numeric outputs typed and labeled with units; ratio-to-fraction conversion covered by tests.
- CI pipeline returns zero exit status for lint/tests; coverage percentages are optional at early stages but critical numerical functions must be directly tested.
- Deterministic code paths log seed, data manifest hash, config hash and versions.
- Exceptions are specific, logged, and do not print sensitive local file paths in public interface.

## Evidence required for each test

Use a saved CI URL or local command with exit code, a test output extract, reference to test file and the artifact path. Do not mark test green just because a developer expects it to pass.

## Acceptance flow

1. Agent completes tasks with code and artifacts.
2. Agent runs test suite and science-validation job available for that milestone.
3. Agent writes milestone review from template and updates progress as `REVIEW REQUIRED`.
4. Owner opens outputs and checks gate conditions.
5. Owner approves → mark `ACCEPTED`; otherwise `BLOCKED` with bug list.
