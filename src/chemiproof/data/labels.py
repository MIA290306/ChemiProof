"""Folder-name -> metadata rules for the Zenodo 19755088 archive (ADR-008, ADR-009).

Every rule here is *evidence-backed or explicitly flagged*:
- ratio `a：b` (full-width colon) = olive : adulterant, parts by volume, a + b == 11, so
  olive_fraction = a / 11.  Source: Zenodo description ("ten olive-oil volume fractions
  ranging from 9.09% to 90.91%", "olive-oil-to-adulterant ratio"); supported by the chlorophyll
  probe in `chemiproof.spectra.qc`.
- adulterant / brand names: exact Chinese folder-name fragments -> English labels; the brand set
  {Earl Grey, Luhua, OliVera} and per-adulterant brand lists are those of the article's Table 2
  as recorded in docs/science/03_DATA_CONTRACT.md. Unknown names raise UNVERIFIED_LABEL.
"""

from __future__ import annotations

import re
import unicodedata

from chemiproof.errors import ChemiProofError, StatusCode

LABEL_SOURCE = "zenodo_19755088_description+ADR-008"
RATIO_TOTAL_PARTS = 11

BRAND_BY_PREFIX = {
    "鲁花特级初榨混": "luhua",
    "欧丽薇兰特级初榨混": "olivera",
    "伯爵特级初榨混": "earl_grey",
}
ADULTERANT_BY_SUFFIX = {
    "西王玉米胚芽油": "corn",
    "金龙鱼菜籽油": "rapeseed",
    "福临门大豆油": "soybean",
    "家香味花生油": "peanut",
    "家乡味花生油": "peanut",
    "晟麦核桃油": "walnut",
}
ROUND_BY_NAME = {"第一轮": 1, "第二轮": 2, "第三轮": 3}
EXPECTED_COUNTS = {"soybean": 60, "peanut": 60, "rapeseed": 90, "corn": 90, "walnut": 30}
EXPECTED_BRANDS = {
    "soybean": {"luhua", "olivera"},
    "peanut": {"luhua", "olivera"},
    "rapeseed": {"earl_grey", "luhua", "olivera"},
    "corn": {"earl_grey", "luhua", "olivera"},
    "walnut": {"luhua"},
}
_RATIO = re.compile(r"^(\d{1,2}):(\d{1,2})$")


def nfc(text: str) -> str:
    """macOS may hand back decomposed (NFD) names; always compare in NFC."""
    return unicodedata.normalize("NFC", text)


def parse_group_dir(name: str) -> tuple[str, str]:
    """Top-level folder -> (evoo_brand, adulterant_type)."""
    n = nfc(name)
    for prefix, brand in BRAND_BY_PREFIX.items():
        if n.startswith(prefix):
            rest = n[len(prefix) :]
            if rest in ADULTERANT_BY_SUFFIX:
                return brand, ADULTERANT_BY_SUFFIX[rest]
    raise ChemiProofError(StatusCode.UNVERIFIED_LABEL, "unrecognized group folder", folder=n)


def parse_round_dir(name: str) -> int:
    n = nfc(name)
    if n not in ROUND_BY_NAME:
        raise ChemiProofError(StatusCode.UNVERIFIED_LABEL, "unrecognized round folder", folder=n)
    return ROUND_BY_NAME[n]


def parse_ratio_dir(name: str) -> tuple[int, int, float]:
    """`8：3` -> (8, 3, 8/11). NFKC maps the full-width colon to ':'."""
    n = unicodedata.normalize("NFKC", name).replace(" ", "")
    m = _RATIO.match(n)
    if not m:
        raise ChemiProofError(StatusCode.UNVERIFIED_LABEL, "unrecognized ratio folder", folder=name)
    a, b = int(m.group(1)), int(m.group(2))
    if a < 1 or b < 1 or a + b != RATIO_TOTAL_PARTS:
        raise ChemiProofError(
            StatusCode.UNVERIFIED_LABEL,
            f"ratio parts must be >=1 and sum to 11, got {a}:{b}",
            folder=name,
        )
    return a, b, a / RATIO_TOTAL_PARTS
