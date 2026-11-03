"""Signal-level checks used for label/axis evidence (not for model fitting)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from chemiproof.data.manifest import ManifestRow
from chemiproof.data.parser import parse_dat

# Chlorophyll fluoresces near 670-680 nm under violet excitation; it is characteristic of olive
# oil. Used ONLY as supporting evidence for the ratio direction (ADR-008), never as a feature rule.
CHL_EX_NM = (400.0, 420.0)
CHL_EM_NM = (660.0, 690.0)


def _ranks(x: list[float]) -> np.ndarray:
    return np.argsort(np.argsort(np.asarray(x, dtype=float))).astype(float)


def spearman(x: list[float], y: list[float]) -> float:
    rx, ry = _ranks(x), _ranks(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def chlorophyll_probe(data_dir: Path, rows: list[ManifestRow]) -> list[dict[str, Any]]:
    """Per (brand, adulterant): Spearman(olive_fraction, chlorophyll-band mean intensity)."""
    band: dict[tuple[str, str], dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        s = parse_dat(data_dir / r.relative_path, r.sample_id).spectrum
        e = (s.excitation_nm >= CHL_EX_NM[0]) & (s.excitation_nm <= CHL_EX_NM[1])
        m = (s.emission_nm >= CHL_EM_NM[0]) & (s.emission_nm <= CHL_EM_NM[1])
        band[(r.evoo_brand, r.adulterant_type)][r.olive_fraction].append(
            float(s.intensity[np.ix_(e, m)].mean())
        )
    out = []
    for (brand, ad), by_y in sorted(band.items()):
        ys = sorted(by_y)
        means = [float(np.mean(by_y[y])) for y in ys]
        out.append(
            {
                "evoo_brand": brand,
                "adulterant_type": ad,
                "spearman_olive_fraction_vs_band": round(spearman(ys, means), 3),
                "band_mean_at_min_olive": round(means[0], 1),
                "band_mean_at_max_olive": round(means[-1], 1),
                "unit": "Counts/uA (mean over band)",
            }
        )
    return out
