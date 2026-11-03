"""T009: fixed toy values match hand calculations."""

import numpy as np
import pytest

from chemiproof.evaluation.metrics import compute_metrics, macro_average, r2_score


def test_t009_hand_computed_values():
    yt = np.array([0.1, 0.5, 0.9])
    yp = np.array([0.2, 0.4, 1.1])  # errors +0.1, -0.1, +0.2
    m = compute_metrics(yt, yp)
    assert m.n == 3
    assert m.mae_fraction == pytest.approx(0.4 / 3)
    assert m.mae_pp == pytest.approx(100 * 0.4 / 3)
    assert m.rmse_fraction == pytest.approx(np.sqrt(0.06 / 3))
    assert m.bias_fraction == pytest.approx(0.2 / 3)  # positive = olive overestimated
    assert m.r2 == pytest.approx(1 - 0.06 / 0.32)  # 0.8125
    assert m.n_out_of_range == 1  # 1.1 is reported, not clipped


def test_r2_is_not_clamped_and_can_be_negative():
    yt = np.array([0.1, 0.5, 0.9])
    assert r2_score(yt, np.array([0.9, 0.5, 0.1])) < 0
    assert r2_score(yt, np.full(3, yt.mean())) == pytest.approx(0.0)


def test_constant_target_gives_nan_r2_and_bad_input_raises():
    assert np.isnan(r2_score(np.full(4, 0.5), np.array([0.4, 0.5, 0.6, 0.5])))
    with pytest.raises(ValueError):
        compute_metrics(np.array([0.1, np.nan]), np.array([0.1, 0.2]))
    with pytest.raises(ValueError):
        compute_metrics(np.array([0.1]), np.array([0.1, 0.2]))


def test_macro_average_is_unweighted_over_folds():
    a = compute_metrics(np.array([0.0, 1.0]), np.array([0.1, 0.9]))
    b = compute_metrics(np.array([0.0, 0.5, 1.0, 0.25]), np.array([0.3, 0.5, 0.7, 0.25]))
    macro = macro_average([a, b])
    assert macro["mae_fraction"] == pytest.approx((a.mae_fraction + b.mae_fraction) / 2)
    assert macro["worst_fold_mae_fraction"] == pytest.approx(max(a.mae_fraction, b.mae_fraction))
