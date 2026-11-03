"""T012-T015 building blocks: Sinkhorn correctness, cross-check with POT, no target labels."""

import inspect

import numpy as np
import pytest

from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.modeling import ot
from chemiproof.modeling.ot import (
    MIN_TARGET_BATCH,
    OTConfig,
    author_style_pca_svr_fit_predict,
    barycentric_projection,
    euclidean_cost,
    ot_svr_fit_predict,
    ot_svr_pot_reference_fit_predict,
    sinkhorn_log,
    svr_no_adaptation_fit_predict,
)


def _blobs(ns=40, nt=15, d=30, shift=0.3, seed=0):
    rng = np.random.default_rng(seed)
    xs = rng.random((ns, d))
    xt = rng.random((nt, d)) + shift
    ys = xs[:, 0] * 0.6 + xs[:, 1] * 0.4  # a learnable target in [0, 1]
    return xs, ys, xt


def test_euclidean_cost_matches_naive_and_is_nonnegative():
    xs, _, xt = _blobs()
    naive = np.sqrt(((xs[:, None, :] - xt[None, :, :]) ** 2).sum(-1))
    np.testing.assert_allclose(euclidean_cost(xs, xt), naive, atol=1e-10)
    assert euclidean_cost(xs, xs).min() >= 0


def test_t014_sinkhorn_marginals_mass_and_convergence_are_recorded():
    xs, _, xt = _blobs()
    a, b = np.full(40, 1 / 40), np.full(15, 1 / 15)
    res = sinkhorn_log(a, b, euclidean_cost(xs, xt), OTConfig(epsilon=0.5))
    assert res.converged and res.n_iter < 1000
    assert res.row_marginal_l1 < 1e-8 and res.col_marginal_l1 < 1e-3
    assert res.col_marginal_sq_l2 < 1e-9
    assert res.total_mass == pytest.approx(1.0, abs=1e-8)
    assert (res.plan >= 0).all()


def test_sinkhorn_nonconvergence_is_reported_not_hidden():
    xs, ys, xt = _blobs()
    a, b = np.full(40, 1 / 40), np.full(15, 1 / 15)
    res = sinkhorn_log(a, b, euclidean_cost(xs, xt), OTConfig(epsilon=0.01, max_iter=2, tol=1e-15))
    assert res.converged is False and res.n_iter == 2
    with pytest.raises(ChemiProofError) as e:
        ot_svr_fit_predict(xs, ys, xt, OTConfig(epsilon=0.01, max_iter=2, tol=1e-15))
    assert e.value.code is StatusCode.NUMERICAL_NONCONVERGENCE


def test_log_domain_sinkhorn_survives_a_cost_scale_that_breaks_the_plain_kernel():
    xs, _, xt = _blobs()
    a, b = np.full(40, 1 / 40), np.full(15, 1 / 15)
    cost = euclidean_cost(xs, xt) * 400.0  # exp(-cost/0.1) underflows to exactly 0
    assert (np.exp(-cost / 0.1) == 0).any()
    res = sinkhorn_log(a, b, cost, OTConfig(epsilon=0.1, max_iter=5000, tol=1e-9))
    assert np.all(np.isfinite(res.plan)) and res.total_mass == pytest.approx(1.0, abs=1e-6)


def test_agrees_with_pot_same_fixed_point_and_bounded_gap_at_published_tolerance():
    """Independent implementation vs POT. Same solution when both are solved tightly; at the
    published loose tolerance (1e-9 on a squared L2 error) the two stopping rules end at slightly
    different points inside the tolerance band, and that gap is small and documented."""
    import ot as pot

    rng = np.random.default_rng(3)
    xs, xt = rng.random((120, 400)), rng.random((40, 400)) + 0.05  # cost scale like the real data
    a, b = np.full(120, 1 / 120), np.full(40, 1 / 40)
    cost = euclidean_cost(xs, xt)
    pot_cost = pot.dist(xs, xt, metric="euclidean")
    # 1) tight solve -> identical fixed point
    tight = OTConfig(0.1, 5000, 1e-24)
    ours_t = sinkhorn_log(a, b, cost, tight)
    pot_t = pot.sinkhorn(a, b, pot_cost, 0.1, numItermax=5000, stopThr=1e-24)
    assert ours_t.converged
    np.testing.assert_allclose(ours_t.plan, pot_t, atol=1e-10)
    # 2) published settings -> both converged by their own rules; bounded gap
    ours = sinkhorn_log(a, b, cost, OTConfig())
    theirs = pot.sinkhorn(a, b, pot_cost, 0.1, numItermax=1000, stopThr=1e-9)
    assert ours.converged
    assert np.abs(ours.plan - theirs).max() < 5e-6 * 10  # plan entries are ~1e-3
    np.testing.assert_allclose(
        barycentric_projection(ours.plan, xt), barycentric_projection(theirs, xt), atol=2e-3
    )


def test_barycentric_projection_is_a_convex_combination_of_target_rows():
    xs, _, xt = _blobs()
    a, b = np.full(40, 1 / 40), np.full(15, 1 / 15)
    proj = barycentric_projection(
        sinkhorn_log(a, b, euclidean_cost(xs, xt), OTConfig(0.5)).plan, xt
    )
    assert proj.shape == xs.shape
    assert (proj >= xt.min(0) - 1e-12).all() and (proj <= xt.max(0) + 1e-12).all()


def test_no_function_accepts_target_labels():
    """Invariant 2: the transductive API cannot receive y_target at all."""
    for fn in (
        ot_svr_fit_predict,
        ot_svr_pot_reference_fit_predict,
        author_style_pca_svr_fit_predict,
        svr_no_adaptation_fit_predict,
        sinkhorn_log,
        barycentric_projection,
    ):
        names = set(inspect.signature(fn).parameters)
        assert not {n for n in names if "target" in n and "y" in n.replace("target", "")}, fn
        assert "y_target" not in names and "yt" not in names and "y_test" not in names, fn
    assert "yt" not in inspect.getsource(ot).split("def ot_svr_fit_predict")[1].split("return")[0]


def test_t012_prediction_uses_target_X_only_and_is_batch_order_invariant():
    xs, ys, xt = _blobs(ns=60, nt=20)
    base = ot_svr_fit_predict(xs, ys, xt, OTConfig(epsilon=0.5))
    perm = np.random.default_rng(1).permutation(len(xt))
    shuffled = ot_svr_fit_predict(xs, ys, xt[perm], OTConfig(epsilon=0.5))
    np.testing.assert_allclose(shuffled.y_pred, base.y_pred[perm], atol=1e-7)
    assert base.diagnostics["mode"] == "transductive_batch" and base.diagnostics["converged"]
    assert base.y_pred.shape == (20,)


def test_t013_a_single_spectrum_or_tiny_batch_is_refused():
    xs, ys, xt = _blobs(ns=60, nt=20)
    for bad in (xt[0], xt[:1], xt[: MIN_TARGET_BATCH - 1]):
        with pytest.raises(ChemiProofError) as e:
            ot_svr_fit_predict(xs, ys, bad)
        assert e.value.code is StatusCode.TRANSDUCTIVE_BATCH_REQUIRED
    ot_svr_fit_predict(xs, ys, xt[:MIN_TARGET_BATCH], OTConfig(epsilon=0.5))  # exactly the minimum


def test_bad_inputs_are_rejected():
    xs, ys, xt = _blobs()
    with pytest.raises(ChemiProofError):
        ot_svr_fit_predict(xs[:, :5], ys, xt)
    bad = xt.copy()
    bad[0, 0] = np.nan
    with pytest.raises(ChemiProofError) as e:
        ot_svr_fit_predict(xs, ys, bad)
    assert e.value.code is StatusCode.NONFINITE_SPECTRUM
    with pytest.raises(ChemiProofError):
        OTConfig(epsilon=0.0)


def test_pot_reference_variant_and_control_variants_run_and_are_labeled():
    xs, ys, xt = _blobs(ns=80, nt=25, shift=0.1)
    xs, xt = xs * 0.2, xt * 0.2  # keep the polynomial kernel in a tame range
    tight = OTConfig(epsilon=0.1, max_iter=20000, tol=1e-16)
    ours = ot_svr_fit_predict(xs, ys, xt, tight)
    pot_ref = ot_svr_pot_reference_fit_predict(xs, ys, xt, tight)
    # Same transport plan -> same projection. Predictions are NOT compared tightly on purpose:
    # a degree-3 polynomial SVR with gamma='scale' on projected features is hypersensitive to
    # 1e-11 plan differences (documented finding, ADR-014); we only require valid output.
    assert np.all(np.isfinite(ours.y_pred)) and np.all(np.isfinite(pot_ref.y_pred))
    assert ours.y_pred.shape == pot_ref.y_pred.shape == (25,)
    assert pot_ref.diagnostics["solver"] == "pot_sinkhorn"
    none = svr_no_adaptation_fit_predict(xs, ys, xt)
    assert none.diagnostics["mode"] == "inductive"
    pca = author_style_pca_svr_fit_predict(xs, ys, xt, n_components=5)
    assert pca.diagnostics["mode"] == "transductive_batch" and pca.y_pred.shape == (25,)
