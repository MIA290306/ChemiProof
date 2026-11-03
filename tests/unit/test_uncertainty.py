"""Unit tests for M5 building blocks (SYNTHETIC numbers only)."""

import numpy as np
import pytest

from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.uncertainty.calibration import (
    finite_sample_quantile,
    interval_halfwidths,
    retention_thresholds,
)
from chemiproof.uncertainty.scores import MahalanobisScorer, model_disagreement
from chemiproof.uncertainty.selective import (
    oracle_curve,
    random_curve,
    rank_curve,
    score_error_spearman,
    selective_stats,
)


def test_finite_sample_quantile_rank():
    v = np.arange(1, 100.0)  # n = 99, level 0.9 -> k = ceil(100*0.9) = 90
    assert finite_sample_quantile(v, 0.9) == 90.0


def test_quantile_refuses_when_rank_exceeds_n():  # T016 flavour
    with pytest.raises(ChemiProofError) as e:
        finite_sample_quantile(np.arange(5.0), 0.99)
    assert e.value.code is StatusCode.INSUFFICIENT_CALIBRATION


def test_interval_refuses_small_or_few_groups():  # T016
    rng = np.random.default_rng(0)
    small = {s: rng.normal(size=10) for s in "abcd"}
    with pytest.raises(ChemiProofError) as e:
        interval_halfwidths(small, 0.9, min_points=100, min_groups=3)
    assert e.value.code is StatusCode.INSUFFICIENT_CALIBRATION
    two = {s: rng.normal(size=100) for s in "ab"}
    with pytest.raises(ChemiProofError):
        interval_halfwidths(two, 0.9, min_points=100, min_groups=3)


def test_max_domain_is_at_least_pooled_when_a_group_is_wider():
    rng = np.random.default_rng(1)
    g = {"a": rng.normal(0, 0.01, 60), "b": rng.normal(0, 0.01, 60), "c": rng.normal(0, 0.2, 60)}
    hw = interval_halfwidths(g, 0.9, 100, 3)
    assert hw["max_domain"] >= hw["pooled"]


def test_thresholds_goal_one_keeps_everything_and_are_monotone():
    s = np.random.default_rng(2).random(200)
    t = retention_thresholds(s, [1.0, 0.9, 0.8, 0.7])
    assert t[1.0] == float("inf")
    assert t[0.9] >= t[0.8] >= t[0.7]
    assert np.mean(s > t[0.8]) <= 0.2 + 1e-9


def test_selective_stats_and_curves():
    err = np.array([0.0, 0.1, 0.2, 0.3])
    st = selective_stats(err, np.array([False, False, True, True]))
    assert st["observed_retention"] == 0.5
    assert st["selective_mae"] == pytest.approx(0.05)
    assert st["rejected_mae"] == pytest.approx(0.25)
    assert st["worst_retained_error"] == pytest.approx(0.1)
    all_out = selective_stats(err, np.ones(4, dtype=bool))
    assert np.isnan(all_out["selective_mae"]) and all_out["n_retained"] == 0
    # a perfect score (= the error) reproduces the oracle
    assert rank_curve(err, err, [50, 100]) == oracle_curve(err, [50, 100])
    assert score_error_spearman(err, err) == pytest.approx(1.0)


def test_random_rejection_is_seeded_and_centered_on_full_mae():
    err = np.random.default_rng(3).random(120)
    a = random_curve(err, [100, 50], repeats=200, seed=7)
    b = random_curve(err, [100, 50], repeats=200, seed=7)
    assert a == b
    assert a["mean"][0] == pytest.approx(err.mean())
    assert a["p05"][1] <= a["mean"][1] <= a["p95"][1]
    assert a["mean"][1] == pytest.approx(err.mean(), abs=0.03)


def test_mahalanobis_scores_far_points_higher_and_is_label_free():
    rng = np.random.default_rng(4)
    train = rng.normal(size=(80, 30))
    sc = MahalanobisScorer(5).fit(train)
    near, far = rng.normal(size=(10, 30)), rng.normal(size=(10, 30)) + 6.0
    assert sc.score(far).mean() > sc.score(near).mean()
    import inspect

    assert list(inspect.signature(MahalanobisScorer.fit).parameters) == ["self", "X"]


def test_disagreement_zero_for_identical_models():
    p = np.array([0.1, 0.5, 0.9])
    assert np.allclose(model_disagreement({"a": p, "b": p, "c": p}), 0.0)
