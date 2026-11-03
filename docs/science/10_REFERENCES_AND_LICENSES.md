# Primary Sources, Evidence and Licensing Review

**Last verified by web research:** 2026-10-24. This is a source registry, not a full legal opinion. Confirm current rights/record metadata before public distribution.

## Primary benchmark

**Sun, R., Li, Q., Wang, T., et al. (2026).** “Open-world quantification of olive-oil adulteration from fluorescence spectra via optimal-transport alignment.” *npj Science of Food*. DOI: https://doi.org/10.1038/s41538-026-01037-6. Published 5 August 2026.  
Supports: open-world hypothesis, LOAO framing, reported OT-SVR results, EEM preprocessing, published methodology. It does **not** establish ChemiProof performance or cross-instrument generality.

**Dataset:** Sun et al. (2026). “EEM fluorescence spectral dataset of olive-oil adulteration samples across five adulterant systems.” Zenodo v1 (25 April 2026). DOI: https://doi.org/10.5281/zenodo.19755088. `data.zip` ~95.9 MB, listed MD5 `dfad908d186e584b96b6070d90cbeec4`.  
Supports: published 330 EEM measurements, source archive and original data description. **Publication details** supplement the shortened repository description: groups 60/60/90/90/30 reflect different EVOO brand combinations.

**Original author repository:** https://github.com/Zhanjun-Li/fluorescence_NonLinear  
Supports: replication reference. **Check whether this repo contains a license before copying any source. A public GitHub repository is not automatically permission to republish code.**

## Additional sources (context, not direct validation)

- 2026 rapid authentication of virgin olive oil using 3D fluorescence and chemometrics, *Chemometrics and Intelligent Laboratory Systems*. DOI: https://doi.org/10.1016/j.chemolab.2026.105822. Different system, not apples-to-apples benchmark.
- Venturini et al. (2023), **Dataset of Fluorescence EEM and UV Spectroscopy Data of Olive Oils during Ageing**, Mendeley Data. DOI: https://doi.org/10.17632/g6y69g8gwm.1. **Aging** dataset, **not labeled adulteration**, cannot directly compute adulteration MAE.
- scikit-learn documentation, pipeline: https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html.
- Introduction to conformal limitations under shift: https://aims.stanford.edu/textbook/src/chap9.html. Ordinary coverage guarantees assume exchangeability; unseen adulterants may violate it.
- General concept: Peyré & Cuturi (2019), *Computational Optimal Transport*. https://arxiv.org/abs/1803.00567.

- Microsoft Learn, Power BI documentation (checked 2026-11-03; context for milestone M6.5, not scientific evidence): Power BI Desktop download and minimum requirements (Windows 10 or later; no macOS) https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop ; signing up for the Power BI service (work or school account needed; Desktop needs no sign-in) https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-signup-purchase-for-power-bi ; Power BI Desktop projects (.pbip, text-based) https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview .

## Rights checklist — MUST complete at M1/M7

- [x] Zenodo dataset license, read from the record's machine-readable metadata (`https://zenodo.org/api/records/19755088`, queried 2026-11-02): `license.id = cc-by-4.0`, `access_right = open`. (The HTML page does not show it; the API does.) Attribution is required.
- [x] CC BY 4.0 permits redistribution/derivatives with attribution, but project policy (CLAUDE.md invariant 10, ADR-003) stays: raw data and data-derived figures are **not committed**; only code, synthetic fixtures and small audit summaries are tracked. Re-evaluate at M7 with the owner.
- [x] Authors' repo `Zhanjun-Li/fluorescence_NonLinear`: GitHub API (queried 2026-11-02) reports `license: null`, size 11 KB, no description. **No license = all rights reserved**: do not copy code; read only to confirm method details (M2/M4) and reimplement independently; cite it.
- [x] Record paper's content/image license before reusing figures; create your own figures by running experiments where possible. (M7: no paper figure is reused; all figures come from our runs)
- [ ] Choose license for **ChemiProof original code** and keep upstream software and dataset licensing separate. (M7: PROPOSED in ADR-019, owner decision)
- [x] Cite original researchers/DOI prominently in README, results and scientific report. Credit is required even if redistribution is not used. (M7: locations listed in `docs/release/RELEASE_REVIEW.md` section 3)
- [x] List any third-party Python package licenses from lockfile / environment at release. (M7: `docs/release/RELEASE_REVIEW.md` section 2; all permissive)
- [ ] (M6.5) Power BI: no `.pbix`/data cache or exported tables committed without owner approval; no "publish to web" or public sharing before this rights review; any published dashboard carries the attribution footer (Sun et al. 2026, Zenodo DOI 10.5281/zenodo.19755088, CC BY 4.0); confirm the Power BI Desktop/service licence terms that apply to the person building the report.

## Evidence vs claim table

| Claim | Evidence status | Safe public wording |
|---|---|---|
| 2026 authors reported OT-SVR mean R² 0.965 in LOAO | published | `The authors reported...` + DOI |
| Dataset contains 330 spectra | published; **audited in M1: 330 `.dat` parsed, 60/60/90/90/30, no discrepancies** (our measurement of the owner-provided extracted copy, run `data_audit.json`) | `We parsed 330 spectra from Zenodo 10.5281/zenodo.19755088` |
| ChemiProof reproduces R²=0.965 | **NOT VERIFIED** | Do not say until actual replication results |
| ChemiProof detects fraud in marketplace products | **NOT VERIFIED** | Do not claim |
| 90% interval is guaranteed on novel oils | **NOT SUPPORTED** | Say `empirical coverage on the tested folds` if measured |
| OOD score identifies all unseen adulterants | **NOT SUPPORTED** | Say `experimental risk flag` |
| Model works on consumer phone photos | **NOT SUPPORTED** | Never imply this input mode |

## Academic attribution and integrity

Describe your extension accurately: "Independent implementation and comparative analysis of spectral QC, domain-shift baselines, abstention and robustness using a public 2026 fluorescence benchmark." Do not claim you collected original EEM dataset or authored OT methodology. Distinguish author reported figures from our measured values in every figure/table.
