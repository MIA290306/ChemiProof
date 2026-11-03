"""Entropic optimal-transport domain adaptation (TRANSDUCTIVE research mode).

Method (re-implemented independently from the published description; the authors' repository
has no license, so only facts were read, never code copied; ADR-011/014):
  1. cost M[i, j] = Euclidean distance between source spectrum i and target spectrum j
     (preprocessed features, NOT rescaled);
  2. entropic OT plan G with uniform marginals and regularization epsilon (Sinkhorn);
  3. barycentric projection of each source spectrum onto the target batch:
     Xs_proj[i] = sum_j G[i, j] Xt[j] / sum_j G[i, j];
  4. fit the reference SVR on (Xs_proj, y_source) and predict the target batch Xt.

INFORMATION ACCESS: this is transductive. It reads the UNLABELED target batch `Xt`. No function
here accepts target labels, so the "no target y" rule is enforced by the signature (and tested).
A single spectrum is NOT a batch: see `MIN_TARGET_BATCH` and `TransductiveBatchRequired`.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.special import logsumexp

from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.modeling.baselines import reference_svr

# Smallest batch the guard accepts (a guard, not a scientific threshold: real batches are 30-90).
MIN_TARGET_BATCH = 10

TRANSDUCTIVE_WARNING = (
    "TRANSDUCTIVE RESEARCH MODE: these predictions need a BATCH of unlabeled target spectra "
    "from the same unseen adulterant. Metrics from this mode must never be advertised as "
    "single-file (inductive) deployment performance."
)


@dataclass(frozen=True)
class OTConfig:
    epsilon: float = 0.1  # entropic regularization, in cost (Euclidean-distance) units
    max_iter: int = 1000
    tol: float = 1e-9  # on the squared L2 error of the target marginal
    # cost: Euclidean distance, unnormalized (published-style); not configurable on purpose

    def __post_init__(self) -> None:
        if not (self.epsilon > 0 and self.max_iter >= 1 and self.tol > 0):
            raise ChemiProofError(
                StatusCode.INVALID_CONFIG, "OT epsilon, max_iter, tol must be > 0"
            )


DEFAULT_OT = OTConfig()


@dataclass(frozen=True)
class SinkhornResult:
    plan: np.ndarray
    converged: bool
    n_iter: int
    row_marginal_l1: float  # sum |G 1 - a|
    col_marginal_l1: float  # sum |G^T 1 - b|
    col_marginal_sq_l2: float  # the stopping statistic
    total_mass: float  # sum G (should be 1)


def euclidean_cost(xs: np.ndarray, xt: np.ndarray) -> np.ndarray:
    """Pairwise Euclidean distances (n_source, n_target), computed stably in float64."""
    xs, xt = np.asarray(xs, dtype=np.float64), np.asarray(xt, dtype=np.float64)
    d2 = (xs**2).sum(1)[:, None] + (xt**2).sum(1)[None, :] - 2.0 * xs @ xt.T
    return np.sqrt(np.maximum(d2, 0.0))


def sinkhorn_log(a: np.ndarray, b: np.ndarray, cost: np.ndarray, cfg: OTConfig) -> SinkhornResult:
    """Log-domain Sinkhorn (no kernel underflow whatever the cost scale)."""
    if cost.shape != (a.size, b.size):
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "cost shape does not match marginals")
    if not (
        np.isclose(a.sum(), 1.0) and np.isclose(b.sum(), 1.0) and (a > 0).all() and (b > 0).all()
    ):
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "marginals must be positive and sum to 1")
    eps = cfg.epsilon
    log_a, log_b = np.log(a), np.log(b)
    f, g = np.zeros_like(a), np.zeros_like(b)
    plan = np.exp((f[:, None] + g[None, :] - cost) / eps)
    err, converged, n_iter = np.inf, False, 0
    for k in range(1, cfg.max_iter + 1):
        n_iter = k
        g = eps * (log_b - logsumexp((f[:, None] - cost) / eps, axis=0))
        f = eps * (log_a - logsumexp((g[None, :] - cost) / eps, axis=1))
        plan = np.exp((f[:, None] + g[None, :] - cost) / eps)
        err = float(np.sum((plan.sum(0) - b) ** 2))
        if err < cfg.tol:
            converged = True
            break
    if not np.all(np.isfinite(plan)):
        raise ChemiProofError(StatusCode.NUMERICAL_NONCONVERGENCE, "non-finite transport plan")
    return SinkhornResult(
        plan=plan,
        converged=converged,
        n_iter=n_iter,
        row_marginal_l1=float(np.abs(plan.sum(1) - a).sum()),
        col_marginal_l1=float(np.abs(plan.sum(0) - b).sum()),
        col_marginal_sq_l2=err,
        total_mass=float(plan.sum()),
    )


def barycentric_projection(plan: np.ndarray, xt: np.ndarray) -> np.ndarray:
    """Map every source row onto the target batch: row-normalized plan times Xt."""
    mass = plan.sum(axis=1, keepdims=True)
    if not np.all(mass > 0):
        raise ChemiProofError(StatusCode.NUMERICAL_NONCONVERGENCE, "source row with zero mass")
    return (plan / mass) @ xt


@dataclass(frozen=True)
class OTPrediction:
    y_pred: np.ndarray
    diagnostics: dict[str, Any]


def _check_batch(xs: np.ndarray, ys: np.ndarray, xt: np.ndarray) -> None:
    if xt.ndim != 2 or xt.shape[0] < MIN_TARGET_BATCH:
        raise ChemiProofError(
            StatusCode.TRANSDUCTIVE_BATCH_REQUIRED,
            f"OT needs a batch of at least {MIN_TARGET_BATCH} unlabeled target spectra, "
            f"got {xt.shape[0] if xt.ndim == 2 else 'a single vector'}",
        )
    if xs.ndim != 2 or xs.shape[1] != xt.shape[1] or xs.shape[0] != ys.shape[0]:
        raise ChemiProofError(StatusCode.INVALID_CONFIG, "source/target feature shapes disagree")
    if not (np.all(np.isfinite(xs)) and np.all(np.isfinite(xt)) and np.all(np.isfinite(ys))):
        raise ChemiProofError(StatusCode.NONFINITE_SPECTRUM, "non-finite source/target values")


def ot_svr_fit_predict(
    xs: np.ndarray, ys: np.ndarray, xt: np.ndarray, cfg: OTConfig = DEFAULT_OT
) -> OTPrediction:
    """Adapt SOURCE spectra to the unlabeled target batch with entropic OT, fit SVR, predict Xt.

    Signature has no target-label argument on purpose (invariant 2 of CLAUDE.md).
    """
    _check_batch(xs, ys, xt)
    a = np.full(xs.shape[0], 1.0 / xs.shape[0])
    b = np.full(xt.shape[0], 1.0 / xt.shape[0])
    cost = euclidean_cost(xs, xt)
    res = sinkhorn_log(a, b, cost, cfg)
    if not res.converged:
        raise ChemiProofError(
            StatusCode.NUMERICAL_NONCONVERGENCE,
            f"Sinkhorn did not reach tol={cfg.tol} in {cfg.max_iter} iterations "
            f"(statistic {res.col_marginal_sq_l2:.3e})",
        )
    xs_proj = barycentric_projection(res.plan, xt)
    model = reference_svr().fit(xs_proj, ys)
    diag = {
        "solver": "sinkhorn_log_domain",
        "epsilon": cfg.epsilon,
        "n_source": int(xs.shape[0]),
        "n_target": int(xt.shape[0]),
        "n_iter": res.n_iter,
        "converged": res.converged,
        "row_marginal_l1": res.row_marginal_l1,
        "col_marginal_l1": res.col_marginal_l1,
        "col_marginal_sq_l2": res.col_marginal_sq_l2,
        "total_mass": res.total_mass,
        "cost_min": float(cost.min()),
        "cost_median": float(np.median(cost)),
        "cost_max": float(cost.max()),
        "mode": "transductive_batch",
    }
    return OTPrediction(np.asarray(model.predict(xt)).reshape(-1), diag)


def ot_svr_pot_reference_fit_predict(
    xs: np.ndarray, ys: np.ndarray, xt: np.ndarray, cfg: OTConfig = DEFAULT_OT
) -> OTPrediction:
    """The SAME method but solved by `ot.sinkhorn` called the way the authors describe
    (epsilon 0.1, numItermax 1000, stopThr 1e-9, Euclidean cost). Documents solver discrepancy."""
    import ot  # optional dependency (extra: ot-reference)

    _check_batch(xs, ys, xt)
    a = np.full(xs.shape[0], 1.0 / xs.shape[0])
    b = np.full(xt.shape[0], 1.0 / xt.shape[0])
    cost = ot.dist(xs, xt, metric="euclidean")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        plan, info = ot.sinkhorn(
            a, b, cost, cfg.epsilon, numItermax=cfg.max_iter, stopThr=cfg.tol, log=True
        )
    pot_warned = any("did not converge" in str(w.message).lower() for w in caught)
    if not np.all(np.isfinite(plan)):
        raise ChemiProofError(StatusCode.NUMERICAL_NONCONVERGENCE, "POT returned a non-finite plan")
    model = reference_svr().fit(barycentric_projection(plan, xt), ys)
    stat = float(np.sum((plan.sum(0) - b) ** 2))
    diag = {
        "solver": "pot_sinkhorn",
        "epsilon": cfg.epsilon,
        "n_source": int(xs.shape[0]),
        "n_target": int(xt.shape[0]),
        "n_iter": int(len(info.get("err", [])) * 10) if "err" in info else -1,
        # honest: no POT warning AND the same statistic we use for our solver is below tol
        "converged": bool((not pot_warned) and stat < cfg.tol),
        "pot_nonconvergence_warning": pot_warned,
        "row_marginal_l1": float(np.abs(plan.sum(1) - a).sum()),
        "col_marginal_l1": float(np.abs(plan.sum(0) - b).sum()),
        "col_marginal_sq_l2": stat,
        "total_mass": float(plan.sum()),
        "cost_min": float(cost.min()),
        "cost_median": float(np.median(cost)),
        "cost_max": float(cost.max()),
        "mode": "transductive_batch",
    }
    return OTPrediction(np.asarray(model.predict(xt)).reshape(-1), diag)


def author_style_pca_svr_fit_predict(
    xs: np.ndarray, ys: np.ndarray, xt: np.ndarray, n_components: int
) -> OTPrediction:
    """Published-style PCA baseline: PCA fitted on source + UNLABELED target X (transductive),
    then the reference SVR. n_components is prespecified (50 and 10), never tuned."""
    from sklearn.decomposition import PCA

    from chemiproof.modeling.baselines import SEED

    _check_batch(xs, ys, xt)
    pca = PCA(n_components=n_components, random_state=SEED).fit(np.vstack([xs, xt]))
    model = reference_svr().fit(pca.transform(xs), ys)
    diag = {
        "solver": "pca_source_plus_target_X",
        "n_components": n_components,
        "n_source": int(xs.shape[0]),
        "n_target": int(xt.shape[0]),
        "mode": "transductive_batch",
    }
    return OTPrediction(np.asarray(model.predict(pca.transform(xt))).reshape(-1), diag)


def svr_no_adaptation_fit_predict(xs: np.ndarray, ys: np.ndarray, xt: np.ndarray) -> OTPrediction:
    """Control: the same SVR on the same features WITHOUT adaptation (inductive information)."""
    model = reference_svr().fit(xs, ys)
    diag = {
        "solver": "none",
        "n_source": int(xs.shape[0]),
        "n_target": int(xt.shape[0]),
        "mode": "inductive",
    }
    return OTPrediction(np.asarray(model.predict(xt)).reshape(-1), diag)
