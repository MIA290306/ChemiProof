"""T010 + LOAO leakage tests: five folds, independent audit, held-out labels are inert."""

import numpy as np
import pytest

from chemiproof import experiments
from chemiproof.errors import ChemiProofError, StatusCode
from chemiproof.evaluation import runner
from chemiproof.evaluation.metrics import compute_metrics
from chemiproof.evaluation.protocols import (
    ADULTERANT_ORDER,
    Fold,
    audit_folds,
    loao_folds,
)
from chemiproof.evaluation.runner import run_models
from chemiproof.modeling.baselines import MODEL_KEYS, SelectedModel
from chemiproof.pipeline import Dataset
from chemiproof.spectra.preprocess import preprocess_features
from helpers import PUBLISHED_DESIGN, fake_rows_multi


def test_t010_five_folds_one_adulterant_each_with_published_sizes():
    rows = fake_rows_multi()
    assert len(rows) == 330
    folds = loao_folds(rows)
    assert [f.fold_id for f in folds] == [f"LOAO-{a}" for a in ADULTERANT_ORDER]
    assert [len(f.test_idx) for f in folds] == [60, 60, 90, 90, 30]
    for f in folds:
        target = f.fold_id.removeprefix("LOAO-")
        assert {rows[i].adulterant_type for i in f.test_idx} == {target}
        assert target not in {rows[i].adulterant_type for i in f.train_idx}
        assert not {rows[i].sample_id for i in f.test_idx} & {
            rows[i].sample_id for i in f.train_idx
        }
    audit = audit_folds(rows, folds, expect_full=True)
    assert audit["n_folds"] == 5 and all(audit["checks"].values())  # full design: all True
    walnut = next(f for f in audit["folds"] if f["target_adulterant"] == "walnut")
    assert walnut["test_brands"] == {"luhua": 30} and walnut["test_brands_absent_from_train"] == []


def test_folds_are_deterministic_and_not_row_level():
    rows = fake_rows_multi()
    a, b = loao_folds(rows), loao_folds(list(rows))
    for fa, fb in zip(a, b, strict=True):
        np.testing.assert_array_equal(fa.test_idx, fb.test_idx)
    shuffled = list(reversed(rows))  # row order must not matter for membership
    assert {shuffled[i].sample_id for i in loao_folds(shuffled)[0].test_idx} == {
        rows[i].sample_id for i in a[0].test_idx
    }


def _tamper(rows, mutate):
    folds = loao_folds(rows)
    return audit_folds(rows, mutate(folds, rows), expect_full=True)


@pytest.mark.parametrize(
    "mutate",
    [
        # target samples leaked into train
        lambda fs, rows: [
            Fold(fs[0].fold_id, np.append(fs[0].train_idx, fs[0].test_idx[0]), fs[0].test_idx, "x"),
            *fs[1:],
        ],
        # a test set mixing two adulterants
        lambda fs, rows: [
            Fold(
                fs[0].fold_id,
                fs[0].train_idx[1:],
                np.append(fs[0].test_idx, fs[0].train_idx[0]),
                "x",
            ),
            *fs[1:],
        ],
        # a sample never tested
        lambda fs, rows: [Fold(fs[0].fold_id, fs[0].train_idx, fs[0].test_idx[1:], "x"), *fs[1:]],
        # the same test fold twice (samples reused)
        lambda fs, rows: [fs[0], fs[0], *fs[2:]],
    ],
)
def test_independent_audit_catches_tampered_folds(mutate):
    with pytest.raises(ValueError):
        _tamper(fake_rows_multi(), mutate)


def test_audit_rejects_unexpected_sizes_when_full_design_expected():
    rows = fake_rows_multi({a: b[:1] for a, b in PUBLISHED_DESIGN.items()})  # 30 each
    with pytest.raises(ValueError, match="published"):
        audit_folds(rows, loao_folds(rows), expect_full=True)
    audit_folds(rows, loao_folds(rows), expect_full=False)  # fine for a declared subset


def test_missing_adulterant_yields_fewer_than_five_folds():
    rows = [r for r in fake_rows_multi() if r.adulterant_type != "walnut"]
    assert len(loao_folds(rows)) == 4


# ---- synthetic LOAO world: adulterant-specific second component = a domain shift -------------
ADULT_SEED = {"soybean": 11, "peanut": 12, "rapeseed": 13, "corn": 14, "walnut": 15}
SHIFT = 0.15  # strength of the adulterant-specific part of the "adulterant" component


def _world(noise=0.002):
    """y * A + (1 - y) * (B + SHIFT * C_adulterant): a mild, adulterant-specific domain shift."""
    from chemiproof.data.schema import EEMSpectrum
    from chemiproof.data.synthetic import make_synthetic_eem

    rows = fake_rows_multi({a: ["luhua"] for a in ADULTERANT_ORDER})  # 150 rows
    a_, b_ = make_synthetic_eem(1), make_synthetic_eem(2)
    specs = []
    for i, r in enumerate(rows):
        c = make_synthetic_eem(ADULT_SEED[r.adulterant_type])
        rng = np.random.default_rng(i)
        z = r.olive_fraction * a_.intensity + (1 - r.olive_fraction) * (
            b_.intensity + SHIFT * c.intensity
        )
        z = z + noise * rng.standard_normal(z.shape)
        specs.append(EEMSpectrum(r.sample_id, a_.excitation_nm, a_.emission_nm, z, synthetic=True))
    X = preprocess_features(specs)
    y = np.array([r.olive_fraction for r in rows])
    g = np.array([r.adulterant_type for r in rows])
    return rows, specs, X, y, g


def test_t008_loao_fit_never_sees_target_rows_or_target_group(monkeypatch):
    rows, _, X, y, g = _world()
    X = X.copy()
    X[:, 0] = np.arange(len(rows))  # column 0 = row id, so we can audit what `fit` received
    seen = []

    class Spy(SelectedModel):
        def fit(self, Xf, yf, groups=None):
            seen.append((set(Xf[:, 0].astype(int)), set(groups)))
            return super().fit(Xf, yf, groups)

    monkeypatch.setattr(runner, "model_factory", lambda key: lambda: Spy(key))
    folds = loao_folds(rows)
    run_models(rows, X, y, folds, ["pls", "mean_y"], g, "t")
    for (fit_rows, fit_groups), fold in zip(
        seen, [f for f in folds for _ in range(2)], strict=True
    ):
        target = fold.fold_id.removeprefix("LOAO-")
        assert not fit_rows & set(fold.test_idx.tolist())
        assert target not in fit_groups  # inner-CV groups = the 4 SOURCE adulterants only
        assert len(fit_groups) == 4


def test_t011_shuffling_heldout_labels_changes_nothing_for_every_fold_and_model():
    rows, specs, X, y, g = _world()
    folds = loao_folds(rows)
    base = run_models(rows, X, y, folds, list(MODEL_KEYS), g, "t")
    report = experiments._label_canary(
        Dataset(rows, specs), X, y, folds, list(MODEL_KEYS), g, base, "t"
    )
    assert report["passed"] and len(report["folds"]) == 5
    assert all(f["unchanged"] and f["heldout_labels_shuffled"] for f in report["folds"])


def test_canary_detects_a_leaky_pipeline(monkeypatch):
    rows, specs, X, y, g = _world()
    folds = loao_folds(rows)
    base = run_models(rows, X, y, folds, ["mean_y"], g, "t")

    def leaky(rows_, X_, y_, folds_, keys, groups, run_id, mode="inductive"):
        out = run_models(rows_, X_, y_, folds_, keys, groups, run_id)
        for p, i in zip(out.predictions, folds_[0].test_idx, strict=False):
            p["y_pred_fraction"] = float(y_[i])  # cheating: reads the held-out label
        return out

    monkeypatch.setattr(experiments, "run_models", leaky)
    with pytest.raises(ChemiProofError) as e:
        experiments._label_canary(Dataset(rows, specs), X, y, folds, ["mean_y"], g, base, "t")
    assert e.value.code is StatusCode.QC_REVIEW_REQUIRED and "LEAKAGE" in e.value.message


def test_synthetic_loao_benchmark_generalizes_and_floor_is_poor():
    rows, _, X, y, g = _world()
    out = run_models(rows, X, y, loao_folds(rows), list(MODEL_KEYS), g, "t")

    def pooled(key):
        t = np.array([p["y_true_fraction"] for p in out.predictions if p["model"] == key])
        p = np.array([p["y_pred_fraction"] for p in out.predictions if p["model"] == key])
        return compute_metrics(t, p)

    floor = pooled("mean_y")
    assert floor.r2 == pytest.approx(0.0, abs=0.05)
    assert pooled("pls").mae_fraction < 0.05 < floor.mae_fraction  # learns across adulterants
    assert {f["fold_id"] for f in out.fold_metrics} == {f"LOAO-{a}" for a in ADULTERANT_ORDER}
    assert all(f["n"] == 30 for f in out.fold_metrics)
