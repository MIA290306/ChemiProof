"""FINAL-PLS-v1 (ADR-018): the inductive screening artifact used by the M6 explorer.

Fitted on ALL 330 spectra, so it has NO independent test set. Its only performance evidence is
LOAO-v1 / LOAO-UQ-v1 for the same procedure (M3/M5). The artifact is plain arrays in an `.npz`
(loaded with `allow_pickle=False`) plus a JSON card whose SHA-256 entry guards the arrays.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.modeling.baselines import SelectedModel, make_base_estimator
from chemiproof.provenance import file_sha256
from chemiproof.spectra.preprocess import AUTHOR_V1
from chemiproof.uncertainty.calibration import interval_halfwidths, retention_thresholds
from chemiproof.uncertainty.scores import MahalanobisScorer

PROTOCOL_ID = "FINAL-PLS-v1"
MODE = "inductive_single"
MODEL_KEY = "pls"
OOD_COMPONENTS = 10
RETENTION_GOAL = 0.80
INTERVAL_LEVEL = 0.90
MIN_CAL_POINTS = 100
MIN_CAL_GROUPS = 3
ARTIFACT_PREFIX = "M6_final_"
LIMITATIONS = [
    "Trained on all 330 spectra: there is NO independent test of this exact model. The evidence "
    "is LOAO-v1 for the same procedure (PLS macro MAE 6.50 pp over five unseen adulterants), "
    "which is optimistic because PLS was chosen after those results were seen (ADR-018).",
    "Five adulterant systems, one instrument and laboratory, laboratory binary mixtures, "
    "imbalanced EVOO brands. Nothing here generalises to other oils, instruments or blends.",
    "The out-of-distribution flag is a weak research-level cue: in LOAO-UQ-v1 it did not meet "
    "its usefulness rule for PLS. It is not a validated detector and not a safety decision.",
    "Intervals are empirical (observed 90 % coverage ranged widely across unseen adulterants in "
    "LOAO-UQ-v1); no coverage is guaranteed under a new adulterant.",
    "Research screening only: not a certified authenticity test and no regulatory meaning.",
]


@dataclass(frozen=True)
class FinalModel:
    x_mean: np.ndarray  # PLS: y = (x - x_mean) @ coef + intercept  (scale=False)
    coef: np.ndarray
    intercept: float
    ood_mean: np.ndarray  # PCA: z = (x - ood_mean) @ ood_components.T
    ood_components: np.ndarray
    ood_var: np.ndarray
    excitation_nm: np.ndarray
    emission_nm: np.ndarray
    threshold: float
    halfwidth: dict[str, float]
    card: dict[str, Any] = field(default_factory=dict)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return (X - self.x_mean) @ self.coef + self.intercept

    def ood_score(self, X: np.ndarray) -> np.ndarray:
        z = (X - self.ood_mean) @ self.ood_components.T
        return np.sqrt(np.sum(z**2 / self.ood_var, axis=1))


def train_final(
    X: np.ndarray,
    y: np.ndarray,
    adulterant: np.ndarray,
    excitation_nm: np.ndarray,
    emission_nm: np.ndarray,
    card: dict[str, Any] | None = None,
) -> FinalModel:
    """Fit on every row; calibrate the flag and interval by leaving each adulterant out."""
    sel = SelectedModel(MODEL_KEY).fit(X, y, groups=adulterant)
    n_comp = int(sel.selected_["n_components"])
    pls = sel.model_
    residuals: dict[str, np.ndarray] = {}
    cal_scores = []
    for a in sorted(set(adulterant.tolist())):
        held, fit = adulterant == a, adulterant != a
        est = make_base_estimator(MODEL_KEY, n_comp).fit(X[fit], y[fit])  # n_comp fixed
        residuals[a] = y[held] - np.asarray(est.predict(X[held])).reshape(-1)
        cal_scores.append(MahalanobisScorer(OOD_COMPONENTS).fit(X[fit]).score(X[held]))
    halfwidth = interval_halfwidths(residuals, INTERVAL_LEVEL, MIN_CAL_POINTS, MIN_CAL_GROUPS)
    threshold = retention_thresholds(np.concatenate(cal_scores), [RETENTION_GOAL])[RETENTION_GOAL]
    scorer = MahalanobisScorer(OOD_COMPONENTS).fit(X)
    meta = {
        "protocol_id": PROTOCOL_ID,
        "mode": MODE,
        "model": MODEL_KEY,
        "preprocess": AUTHOR_V1.as_dict(),
        "n_components": n_comp,
        "inner_cv_mae_by_n_fraction": {
            str(k): v for k, v in sel.selected_["inner_cv_mae_by_n"].items()
        },
        "n_train": int(X.shape[0]),
        "train_counts_by_adulterant": {
            a: int(np.sum(adulterant == a)) for a in sorted(set(adulterant.tolist()))
        },
        "ood": {"score": "ood_maha", "pca_components": OOD_COMPONENTS,
                "retention_goal": RETENTION_GOAL, "threshold": threshold,
                "n_calibration": int(sum(s.size for s in cal_scores))},
        "interval": {"nominal_level": INTERVAL_LEVEL, "halfwidth_fraction": halfwidth,
                     "primary": "pooled", "coverage_guarantee": False},
        "units": "olive-oil volume FRACTION in [0, 1] (0.01 = 1 percentage point)",
        "limitations": LIMITATIONS,
    } | (card or {})  # fmt: skip
    return FinalModel(
        x_mean=np.asarray(pls._x_mean, dtype=float),
        coef=np.asarray(pls.coef_, dtype=float).reshape(-1),
        intercept=float(np.asarray(pls.intercept_).reshape(-1)[0]),
        ood_mean=np.asarray(scorer.pca_.mean_, dtype=float),
        ood_components=np.asarray(scorer.pca_.components_, dtype=float),
        ood_var=np.asarray(scorer.var_, dtype=float),
        excitation_nm=np.asarray(excitation_nm, dtype=float),
        emission_nm=np.asarray(emission_nm, dtype=float),
        threshold=float(threshold),
        halfwidth=halfwidth,
        card=meta,
    )


_ARRAYS = ("x_mean", "coef", "ood_mean", "ood_components", "ood_var",
           "excitation_nm", "emission_nm")  # fmt: skip


def save_final(model: FinalModel, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=False)  # never overwrite an artifact
    npz = out_dir / "model.npz"
    np.savez(npz, **{k: getattr(model, k) for k in _ARRAYS}, intercept=np.array(model.intercept))
    card = model.card | {"model_npz_sha256": file_sha256(npz)}
    (out_dir / "model_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    return out_dir


def load_final(art_dir: Path) -> FinalModel:
    card_path, npz = art_dir / "model_card.json", art_dir / "model.npz"
    if not (card_path.is_file() and npz.is_file()):
        raise ChemiProofError(
            StatusCode.NO_TRAINED_MODEL,
            "research model not available: run `chemiproof model train-final` first",
        )
    card = json.loads(card_path.read_text(encoding="utf-8"))
    if card.get("protocol_id") != PROTOCOL_ID or file_sha256(npz) != card.get("model_npz_sha256"):
        raise ChemiProofError(
            StatusCode.NO_TRAINED_MODEL, "model artifact does not match its card; retrain it"
        )
    with np.load(npz, allow_pickle=False) as z:
        arrays = {k: np.array(z[k]) for k in _ARRAYS}
        intercept = float(z["intercept"])
    return FinalModel(
        **arrays,
        intercept=intercept,
        threshold=float(card["ood"]["threshold"]),
        halfwidth={k: float(v) for k, v in card["interval"]["halfwidth_fraction"].items()},
        card=card,
    )


def latest_artifact(results_root: Path) -> Path | None:
    """Newest complete `M6_final_*` folder (npz and card); run ids start with a UTC timestamp,
    so an interrupted training run without a card never hides an older valid artifact."""
    dirs = sorted(
        p
        for p in results_root.glob(f"{ARTIFACT_PREFIX}*")
        if (p / "model.npz").is_file() and (p / "model_card.json").is_file()
    )
    return dirs[-1] if dirs else None
