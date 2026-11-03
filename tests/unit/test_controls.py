"""T024 (LOAO): permuting SOURCE labels must collapse the benchmark; true labels are scored."""

import numpy as np
from test_loao import _world

from chemiproof.evaluation.controls import permuted_source_label_control
from chemiproof.evaluation.protocols import loao_folds


def test_permuted_source_labels_collapse_loao_scores_on_synthetic_world():
    rows, _, X, y, g = _world()
    folds = loao_folds(rows)
    res = permuted_source_label_control(rows, X, y, folds, ["mean_y", "svr_raw", "pls"], g, 2)
    assert res["n_repeats"] == 2 and set(res["models"]) == {"mean_y", "svr_raw", "pls"}
    for key in ("svr_raw", "pls"):
        assert res["models"][key]["mean_macro_r2"] < 0.3  # real labels give > 0.9 here
    assert abs(res["models"]["mean_y"]["mean_macro_r2"]) < 0.5
    again = permuted_source_label_control(rows, X, y, folds, ["pls"], g, 2)
    assert np.isclose(
        again["models"]["pls"]["mean_macro_r2"], res["models"]["pls"]["mean_macro_r2"]
    )
