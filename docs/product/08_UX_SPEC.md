# UX / Research Explorer Specification

## Interaction principles

ChemiProof is a research interface, not a consumer “is this food fake?” app. Favor clarity, provenance, readable charts and easy inspection of limitations over animation and fabricated “AI confidence percentages.”

## Information architecture

1. **Overview** — honest project status, dataset scope, disclaimer, primary published paper vs *our measured* results.
2. **Explore EEM** — load a validated sample, view matrix heatmap, excitation/emission axes, spectrum slices, QC flags, preprocessing versions.
3. **Benchmarks** — per-oil metrics table, macro/pooled metrics, residuals, replicate/brand distribution, direct inductive vs transductive comparison with explicit access labels.
4. **Screen Sample** — one-file inductive research estimate only (when a validated artifact exists); QC/abstention-first output.
5. **Batch Research** — upload/select group of EEM files and explicitly opt into transductive OT methodology, with batch identity and limitations shown.
6. **Methods & Provenance** — data DOI, model ID, code hash, preprocessing, splits, calibration caveat, environment details and citations.

## Screen details

### Overview

Hero: `ChemiProof / Spectral Screening Research`. Subline: `Experimental estimates of olive-oil volume fraction from EEM fluorescence spectra.` Neutral disclaimer, feature mode chips, date of last real run. Charts only from actual artifacts. `No results available` if no completed experiments.

### Spectrum explorer

- Input: choose one sample from audited manifest or upload `.dat` with documented native format.
- Validation strip: parser ✓/!, wavelength grid ✓/!, finite values ✓/!, normalization status, sample provenance.
- Heatmap axes **in nm**, intensity in source instrument unit or `arbitrary units` if correct unit unknown.
- Controls: raw vs processed; excitation/emission slice; preprocessing version; warning list.
- Download transformed spectrum only with metadata and traceable source hash, if rights permit.

### Benchmarks

- Dropdown outer adulterant. Always show n, source brand makeup and protocol label.
- Paired plot estimated vs actual and residuals. Paper reference results only in clearly sourced separate overlay/table.
- Metric table MAE fraction/pp, RMSE, R², bias, worst fold; note group imbalance.
- Side-by-side legend: `Inductive (no target batch)` vs `Transductive (unlabeled target batch used)`.

### Screen sample (inductive)

- Upload accepted after spectrum QC; unsupported files yield `No estimate: validation failed`.
- Main result: `Estimated olive-oil fraction: 0.xx (xx%)` only if model exists, QC passes, and decision allows prediction.
- If abstain: `Review required — estimate withheld`, with QC vs model-risk reason, never “fraud detected”.
- Intervals: state `Empirical research interval; coverage on unseen adulterants is not guaranteed.`
- Always display model/preprocessing provenance, mode, studied matrix, limitations.

### Batch research

- Requires validated batch data, says `Research transductive mode: this procedure adapts using the unlabeled spectra of the full batch.`
- Prohibit ambiguous one-file batch method and separate this from single-sample screening.
- After run, show status and per-sample outputs with batch manifest ID and OT numerical convergence.

## Empty/error states

| State | UI wording |
|---|---|
| No benchmark runs | `No verified benchmark results yet.` |
| Missing trained model | `Research model not available: complete the model-validation milestones first.` |
| Bad file | `Spectrum format or wavelength grid could not be validated; no estimate generated.` |
| Domain-shift flag | `Review required: input differs from reference research spectra. This is a statistical flag, not a diagnosis.` |
| Insufficient calibration | `Prediction interval unavailable: evidence is insufficient.` |
| Failed OT convergence | `Batch analysis stopped: optimal transport did not converge.` |

## Visual style

Minimalist laboratory notebook look: off-white/very light neutral background, ink-dark typography, muted sage/teal accents, no “fraud red” unless a technical stop/error. Simple scientific charts with legends, units, QC annotations; colorblind-compatible categorical palette. Good mobile responsiveness but desktop-first for spectra exploration.

## Accessibility and semantics

- Labels, keyboard controls, contrast checks, chart tables/alternative summaries.
- All figures exportable with captions describing units/protocol, not decorative meaningless charts.
- No progress bar that suggests a probability of authenticity unless the metric genuinely supports that meaning (likely not).

## Demo journey (3 minutes)

1. View actual audited EEM spectrum and its scientific context.
2. Select held-out `walnut` benchmark; explain small n and brand imbalance.
3. Compare raw SVR with OT-transductive results and show why their access conditions differ.
4. Inspect selective-risk curve and one failure case.
5. Demonstrate invalid upload refusal or abstention when risk is high.
6. Export reproducibility report and cite original dataset/paper.

**Do not design a standalone app authentication system or SaaS backend during MVP.**

## Power BI dashboard (M6.5, specification only)

The optional BI dashboard follows the same trust language as this explorer: research screening, not a certified test; estimated olive-oil volume fraction in percentage points; "review required" instead of any verdict; protocol, mode and model version always visible; the transductive warning on every OT view. Page layouts, slicers, wording rules (including forbidden phrases) and the empty states are in `docs/bi/18_POWER_BI_SPEC.md` section 6. The BI report must not offer capabilities this UI deliberately withholds (no single-file OT, no quality verdicts, no thresholds).
