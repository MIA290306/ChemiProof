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

## Rights checklist — MUST complete at M1/M7

- [ ] Record exact Zenodo dataset license name/identifier visible in **record metadata**. (The public page fetched during planning did not expose a usable value under Rights; **do not assume CC BY simply because it is a Zenodo default**.)
- [ ] Check allowed derivative work and redistribution; if ambiguous, keep **all raw/derived data** local and share only code plus independently created small synthetic fixtures.
- [ ] Record license/permissions on original GitHub repo. If license missing, do not copy-paste code wholesale or redistribute fragments; develop independent implementation referencing paper/methodology.
- [ ] Record paper's content/image license before reusing figures; create your own figures by running experiments where possible.
- [ ] Choose license for **ChemiProof original code** and keep upstream software and dataset licensing separate.
- [ ] Cite original researchers/DOI prominently in README, results and scientific report. Credit is required even if redistribution is not used.
- [ ] List any third-party Python package licenses from lockfile / environment at release.

## Evidence vs claim table

| Claim | Evidence status | Safe public wording |
|---|---|---|
| 2026 authors reported OT-SVR mean R² 0.965 in LOAO | published | `The authors reported...` + DOI |
| Dataset contains 330 spectra | published; verify archive in M1 | `The published dataset describes 330 spectra...` |
| ChemiProof reproduces R²=0.965 | **NOT VERIFIED** | Do not say until actual replication results |
| ChemiProof detects fraud in marketplace products | **NOT VERIFIED** | Do not claim |
| 90% interval is guaranteed on novel oils | **NOT SUPPORTED** | Say `empirical coverage on the tested folds` if measured |
| OOD score identifies all unseen adulterants | **NOT SUPPORTED** | Say `experimental risk flag` |
| Model works on consumer phone photos | **NOT SUPPORTED** | Never imply this input mode |

## Academic attribution and integrity

Describe your extension accurately: "Independent implementation and comparative analysis of spectral QC, domain-shift baselines, abstention and robustness using a public 2026 fluorescence benchmark." Do not claim you collected original EEM dataset or authored OT methodology. Distinguish author reported figures from our measured values in every figure/table.
