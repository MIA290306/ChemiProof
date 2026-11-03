# Risk Register — Research / Engineering / Ethics

**Scoring:** Likelihood (L) and impact (I) on a 1–5 planning scale. `L × I` is *prioritization*, not a probability or measured risk. Review after every gate. Owner may adjust ratings.

| ID | Risk | L×I | Early signal | Prevention / mitigation | Owner / gate |
|---|---|---:|---|---|---|
| R01 | Assumed `.dat` layout wrong | 4×5 | heatmap transposed or dimensions odd | inspect representative files across groups; verified axes | Data engineer / M1 |
| R02 | Olive:adulterant ratio inverted | 3×5 | plots trend opposite expectation | preserve raw ratio tokens and verify direction from author sources | Research / M1 |
| R03 | Artificial inflation from target-label leakage | 4×5 | suspicious near-perfect target score | frozen LOAO, source-only tuning, target-y shuffle invariance tests | ML / M3–M5 |
| R04 | Transductive OT marketed as single-file predictor | 4×5 | “upload one sample gives 0.965 R²” | separate modes and API paths; explicit docs/UI language | Owner / M4/M6 |
| R05 | No coverage guarantee under unseen adulterants | 4×4 | UI “90% certainty” | report observed interval coverage + distribution-shift caveat | ML / M5 |
| R06 | Different EVOO brand per adulterant confounds results | 5×4 | performance varies with brand mix | stratified descriptive audit; sensitivity analysis and limitations | Research / M1/M3 |
| R07 | Small and unequal group sizes | 5×3 | macro vs pooled ranking inconsistent | both aggregation types; per-domain n, dispersion | ML / M3 |
| R08 | External code/data license unclear | 3×5 | missing/unreadable license | independent rights review; do not redistribute unlicensed assets | Owner / M1/M7 |
| R09 | Matching paper R² prioritized over honest replication | 4×4 | repeated tuning on outer test | inner folds only; log all runs, locked final evaluation | Research / M3/M4 |
| R10 | Unsupported wavelength grid accepted by heuristic reshape | 3×5 | unexplained offsets or distorted peaks | fail-fast native schema, axes validation | Data / M1/M6 |
| R11 | OT numerical instability / cost scales | 3×4 | NaN transport, non-convergence | inspect cost scale, solver residuals; deterministic unit tests | ML / M4 |
| R12 | Raw data accidentally committed | 3×4 | ZIP/.dat appears in Git diff | ignore rules + CI secret/data scan | Dev / M0/M7 |
| R13 | Predicted composition equated to legal fraud | 4×5 | wording “fraud confirmed” | screening-only disclaimer, no threshold compliance claims | Product / all |
| R14 | AI assistant makes up results/figures | 4×5 | screenshots before runs, reference R² shown as ours | prohibit synthetic evidence; require artifact hashes and commands | Owner / all |
| R15 | Unverified chemical attribution to peaks | 3×4 | “this peak proves chlorophyll” | interpret associations cautiously; literature and standards | Research / M5/M7 |
| R16 | Public demo accepts arbitrary unsafe file | 3×4 | malformed ZIP exhaustion / processing | file size limits, sanitize/disable unsafe extraction, UI sandbox | Dev / M6 |
| R17 | Attempted extrapolation to honey/milk/other oils | 4×4 | multi-food marketing claim | document restricted matrix/protocol | Product / M7 |
| R18 | Single-device paper appears production-ready | 4×4 | no external lab validation caveat | model card; recommend confirmatory testing | Owner / M7 |
| R19 | Artificially injected noise treated as actual robustness evidence | 4×3 | “validated on other instruments” | label synthetic perturbation only | Research / M5 |
| R20 | Agent overbuilds infrastructure instead of science | 4×3 | auth/db/LLM integrations before LOAO | strict milestone limits, local-first MVP | Owner / M0–M5 |
| R21 | A BI visual or measure mixes protocols or information-access modes (for example inductive and OT results in one series) | 4×5 | numbers change when a slicer moves; series without protocol labels | run guard, protocol/mode shown in every visual, rules P-1 to P-4, tests BI006/BI022/BI026 | BI engineer / M6.5 |
| R22 | A Power BI KPI cannot be reproduced from the Python outputs | 3×5 | reconciliation mismatch; hard-coded numbers | no hard-coded metrics, exporter reconciliation V-05, KPI recompute BI021 | BI engineer / M6.5 |
| R23 | Dashboard wording or colours read as a fraud, safety or compliance verdict | 3×5 | words like adulterated/safe/compliant, traffic lights, thresholds | wording rules, no thresholds, lint BI024, owner review of wording | UX + owner / M6.5 |
| R24 | Power BI Desktop is Windows-only; a macOS-only environment cannot build or verify the report, tempting an unverified "done" claim | 4×4 | `.pbip` files without screenshots or open logs | record the limitation, mark BLOCKED, Windows verification evidence required (BI020-BI032) | Owner / M6.5 |
| R25 | Stale or inconsistent exports (old runs, schema drift, unregistered protocols) feed the dashboard | 3×4 | contract-version mismatch, config hash not in the protocol map | immutable versioned exports, protocol map with `UNREGISTERED`, refresh guard BI027 | Data engineer / M6.5 |
| R26 | Derived data or an embedded-data `.pbix` is committed or published publicly before the rights review | 2×4 | `.pbix` in Git, "publish to web" used | `.gitignore`, no public publishing before M7, attribution footer BI030, rights checklist | Owner / M6.5-M7 |
| R27 | Uncertainty or abstention shown without its method, level, calibration or retention, creating false assurance | 3×5 | label "90% interval" only; error shown without retention | method card, validation V-09, tests BI013/BI028 | Research lead / M6.5 |

## Escalation rules

- **Critical / block now:** possible target-label leakage, unverifiable ground-truth label, incorrect axes, misleading scientific claim or unlicensed redistribution.
- **High / document before proceeding:** brand imbalance, invalid cross-domain inference, failed numerical convergence, missing calibration evidence.
- **Medium / monitor:** UI polish, runtime optimization, optional package choice.

## Review cadence

At each M0–M7 gate, update risk probability/impact, mitigation evidence, next owner/action. New methods that change information access require documented approval.
