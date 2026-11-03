# Scientific Report, Portfolio & Release Standard

## Scientific deliverable structure (4–8 pages, ideally plus technical appendix)

1. **Title / authorship / original sources** — identify your contributions versus published study.
2. **Abstract (150–250 words)** — question, dataset/method, measured results, limitations.
3. **Introduction** — food fraud and EEM; why unseen-adulterant domain shift matters.
4. **Data & methods** — sample distribution, brands, ten ratios, spectroscopy grids, preprocessing, LOAO splits, baseline + OT modes, metric units and threshold rules.
5. **Results** — 5-fold table, macro/pooled comparison, uncertainty/risk curves, perturbations, error examples; no invented values.
6. **Discussion** — interpretation, known confounders, source domain shift, why transduction matters, how results compare with Sun et al. (2026), limitations and generalization claims.
7. **Conclusion** — what *was demonstrated* versus what requires external validation.
8. **References** — source DOI and dataset DOI; reused methods noted.
9. **Appendix** — configs, hashes, experiment commands, model/data cards, extra results, implementation/tool versions.

## Scientific integrity checklist

- [ ] Every figure/table derived from saved experiment artifact with run ID.
- [ ] Data sample counts and label units are consistent with audited manifest.
- [ ] All experimental conditions and calibrations are specified.
- [ ] Inductive and transductive modes shown separately.
- [ ] Per-adulterant metrics included (not only overall R²).
- [ ] Negative/ambiguous outcomes included, not just favorable results.
- [ ] Interval coverage described as empirical under shift.
- [ ] Base EVOO brands and unequal groups discussed as confounders.
- [ ] Distinguish reported paper scores vs our measured results.
- [ ] No claims of definitive counterfeit detection or compliance approval.
- [ ] Source data and author code licenses checked before redistribution.

## Final model card minimum

Model ID/version; owner; date; task and target units; supported matrix and instrument/wavelength protocol; training/validation data; LOAO benchmark; inductive/transductive information access; uncertainty method and known failures; fairness/brand imbalance issues; security; intended/not intended uses; references; reevaluation/rollback procedure.

## Portfolio README sections

1. Friendly intro + legitimate scientific problem statement.
2. One research figure and a 90-second demo GIF created from **real** application, not stock graph.
3. Original research source + dataset citations.
4. Diagram of EEM → QC → split → model → uncertainty/refusal → report.
5. Baseline vs method evaluation with five domains and reported limitations.
6. `How to reproduce` commands requiring official external data.
7. Technical stack, CI tests, exact contribution list, roadmap/known caveats.
7a. *(only if M6.5 is accepted)* the Power BI dashboard with screenshots taken from real exports and the Windows/Desktop version used; otherwise state "Power BI layer: not delivered".
8. `Not a certified authenticity test` prominent near result section.

## External review questions

- Can a food chemistry instructor verify spectral preprocessing is physically plausible?
- Can an ML reviewer verify no labels from target domain influence selection?
- Can another student reproduce figures from a fresh environment?
- If a Power BI dashboard is included: does every KPI reproduce from the exported data with Python, and does any visual combine protocols or modes?
- Can a reviewer tell exactly which methods were proposed by Sun et al. and which pieces are your extension?
- Are errors, odd samples, group imbalance, model refusal and transductive dependency visible rather than buried?

## Final exit rule

Do not tag v1.0 until reviewer signoff and all hard-block acceptance tests pass. A responsible negative or null experimental outcome can still form a strong scientific portfolio if methods and limitations are exceptionally clear.
