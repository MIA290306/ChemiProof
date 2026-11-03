"""T008 / T011 / T024: no train/test leakage, no label access, permuted labels degrade."""

import numpy as np
import pytest

from chemiproof.errors import ChemiProofError  # noqa: F401  (kept for symmetry with other tests)
from chemiproof.evaluation import runner
from chemiproof.evaluation.metrics import compute_metrics
from chemiproof.evaluation.protocols import Fold, source_internal_loro_folds
from chemiproof.evaluation.runner import run_models
from chemiproof.modeling.baselines import MODEL_KEYS, PLS_GRID, SelectedModel, model_factory
from chemiproof.spectra.preprocess import preprocess_features
from helpers import fake_rows, mixture_eem

YS = [round(k / 11, 6) for k in range(1, 11)]


def _dataset(noise=0.002):
    rows = fake_rows([1, 2, 3], YS)
    specs = [mixture_eem(r.olive_fraction, noise=noise, rng_seed=i) for i, r in enumerate(rows)]
    X = preprocess_features(specs)
    y = np.array([r.olive_fraction for r in rows])
    rounds = np.array([r.measurement_round for r in rows])
    return rows, X, y, rounds


def test_folds_are_disjoint_complete_and_round_pure():
    rows = fake_rows([1, 2, 3], YS)
    folds = source_internal_loro_folds(rows)
    assert [f.fold_id for f in folds] == ["SI-round1", "SI-round2", "SI-round3"]
    all_test = np.concatenate([f.test_idx for f in folds])
    assert sorted(all_test.tolist()) == list(range(len(rows)))  # each row tested exactly once
    for f in folds:
        assert not set(f.train_idx) & set(f.test_idx)
        assert len({rows[i].measurement_round for i in f.test_idx}) == 1


def test_fold_rejects_overlap_or_empty():
    with pytest.raises(ValueError):
        Fold("x", np.array([0, 1]), np.array([1, 2]), "overlap")
    with pytest.raises(ValueError):
        Fold("x", np.array([0]), np.array([], dtype=int), "empty")


def test_t008_fit_never_sees_test_rows_or_test_groups(monkeypatch):
    rows, X, y, rounds = _dataset()
    X = X.copy()
    X[:, 0] = np.arange(len(rows))  # column 0 carries the row index so we can audit what fit saw
    seen = []

    class Spy(SelectedModel):
        def fit(self, Xf, yf, groups=None):
            seen.append((set(Xf[:, 0].astype(int)), None if groups is None else set(groups)))
            return super().fit(Xf, yf, groups)

    monkeypatch.setattr(runner, "model_factory", lambda key: lambda: Spy(key))
    folds = source_internal_loro_folds(rows)
    run_models(rows, X, y, folds, ["pls", "mean_y"], rounds, "t")
    for (fit_rows, fit_groups), fold in zip(
        seen, [f for f in folds for _ in range(2)], strict=True
    ):
        assert not fit_rows & set(fold.test_idx.tolist())
        held_round = rows[fold.test_idx[0]].measurement_round
        assert held_round not in (fit_groups or set())  # inner-CV groups come from train rows only


def test_t011_changing_test_labels_cannot_change_that_folds_predictions():
    rows, X, y, rounds = _dataset()
    folds = source_internal_loro_folds(rows)
    base = run_models(rows, X, y, folds, list(MODEL_KEYS), rounds, "t")
    y2 = y.copy()
    held = folds[0].test_idx  # round 1
    y2[held] = np.random.default_rng(0).permutation(y2[held])[::-1] * 0.5 + 0.25  # garbage labels
    alt = run_models(rows, X, y2, folds, list(MODEL_KEYS), rounds, "t")

    def preds(out, fold_id):
        return [
            (p["model"], p["sample_id"], p["y_pred_fraction"])
            for p in out.predictions
            if p["fold_id"] == fold_id
        ]

    assert preds(base, "SI-round1") == preds(alt, "SI-round1")  # labels of round 1 unused for it
    assert preds(base, "SI-round2") != preds(
        alt, "SI-round2"
    )  # ...but legitimately used to train others


def test_pca_is_fitted_on_training_rows_only():
    rows, X, y, rounds = _dataset()
    tr = rounds != 3
    model = SelectedModel("pca_svr").fit(X[tr], y[tr], groups=rounds[tr])
    pca = model.model_.named_steps["pca"]
    np.testing.assert_allclose(pca.mean_, X[tr].mean(axis=0))
    assert not np.allclose(pca.mean_, X.mean(axis=0))  # would differ if test rows leaked in


def test_selected_hyperparameters_come_from_training_groups_only():
    rows, X, y, rounds = _dataset()
    tr = rounds != 3
    m = SelectedModel("pls").fit(X[tr], y[tr], groups=rounds[tr])
    assert m.selected_["n_components"] in PLS_GRID
    assert set(m.selected_["inner_cv_mae_by_n"]) <= set(PLS_GRID)


def test_tunable_models_refuse_to_tune_without_groups_and_unknown_keys_fail():
    rows, X, y, rounds = _dataset()
    with pytest.raises(ValueError):
        SelectedModel("pls").fit(X, y, groups=None)
    with pytest.raises(ValueError):
        SelectedModel("pca_svr").fit(X[rounds == 1], y[rounds == 1], groups=rounds[rounds == 1])
    with pytest.raises(KeyError):
        model_factory("deep_magic")


def test_synthetic_benchmark_models_learn_and_mean_floor_is_zero_r2():
    rows, X, y, rounds = _dataset()
    folds = source_internal_loro_folds(rows)
    out = run_models(rows, X, y, folds, list(MODEL_KEYS), rounds, "t")

    def pooled(key):
        t = np.array([p["y_true_fraction"] for p in out.predictions if p["model"] == key])
        p = np.array([p["y_pred_fraction"] for p in out.predictions if p["model"] == key])
        return compute_metrics(t, p)

    floor = pooled("mean_y")
    assert abs(floor.r2) < 0.05  # constant predictor explains ~nothing
    assert floor.mae_fraction == pytest.approx(0.2273, abs=0.02)
    for key in ("svr_raw", "pca_svr", "pls"):
        m = pooled(key)
        assert m.mae_fraction < floor.mae_fraction / 2 and m.r2 > 0.8, key
    assert pooled("pls").r2 > 0.99  # linear mixture + tiny noise: PLS must nail it


def test_t024_permuted_source_labels_degrade_the_benchmark():
    rows, X, y, rounds = _dataset()
    folds = source_internal_loro_folds(rows)
    rng = np.random.default_rng(1)
    y_perm = y.copy()
    for rnd in (1, 2, 3):  # permute labels within each round, spectra stay put
        idx = np.flatnonzero(rounds == rnd)
        y_perm[idx] = y[rng.permutation(idx)]
    good = run_models(rows, X, y, folds, ["pls"], rounds, "t")
    bad = run_models(rows, X, y_perm, folds, ["pls"], rounds, "t")

    def r2(out):
        return np.mean([f["r2"] for f in out.fold_metrics])

    assert r2(good) > 0.95
    assert r2(bad) < 0.3  # benchmark collapses when the spectrum-label link is destroyed
