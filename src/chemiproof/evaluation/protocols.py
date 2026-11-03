"""Evaluation splits. A fold is just disjoint train/test row indices plus a description.

M2 implements `source_internal_loro` only. The LOAO outer folds (M3) will live here too.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from chemiproof.data.manifest import ManifestRow


@dataclass(frozen=True)
class Fold:
    fold_id: str
    train_idx: np.ndarray
    test_idx: np.ndarray
    description: str

    def __post_init__(self) -> None:
        if set(self.train_idx.tolist()) & set(self.test_idx.tolist()):
            raise ValueError(f"fold {self.fold_id}: train and test overlap")
        if self.train_idx.size == 0 or self.test_idx.size == 0:
            raise ValueError(f"fold {self.fold_id}: empty train or test set")


def source_internal_loro_folds(rows: list[ManifestRow]) -> list[Fold]:
    """Leave one measurement round out over ALL spectra (3 folds).

    Optimistic by construction: the held-out round shares brand/adulterant/ratio cells with the
    training rounds. It measures round (replicate/batch) generalization inside known adulterants,
    NOT unseen-adulterant generalization (that is the M3 LOAO benchmark).
    """
    rounds = np.array([r.measurement_round for r in rows])
    folds = []
    for rnd in sorted(set(rounds.tolist())):
        test = np.flatnonzero(rounds == rnd)
        train = np.flatnonzero(rounds != rnd)
        folds.append(
            Fold(
                f"SI-round{rnd}",
                train,
                test,
                f"train on other rounds; test on round {rnd}",
            )
        )
    return folds


ADULTERANT_ORDER = ("soybean", "peanut", "rapeseed", "corn", "walnut")  # fixed, = fold order
EXPECTED_TARGET_SIZES = {"soybean": 60, "peanut": 60, "rapeseed": 90, "corn": 90, "walnut": 30}


def loao_folds(rows: list[ManifestRow]) -> list[Fold]:
    """Exactly five outer folds, one per adulterant type, in the fixed ADULTERANT_ORDER.

    Fold `LOAO-<x>`: test = every sample whose adulterant is x; train = every other sample.
    Deterministic (no randomness, no row-level splitting). A fold is skipped only if the
    adulterant is absent from `rows`; the caller decides whether that is acceptable.
    """
    adulterants = np.array([r.adulterant_type for r in rows])
    folds = []
    for ad in ADULTERANT_ORDER:
        test = np.flatnonzero(adulterants == ad)
        if test.size == 0:
            continue
        train = np.flatnonzero(adulterants != ad)
        folds.append(
            Fold(f"LOAO-{ad}", train, test, f"hold out ALL {ad} samples; train on the rest")
        )
    return folds


def audit_folds(rows: list[ManifestRow], folds: list[Fold], *, expect_full: bool) -> dict:
    """Independent re-check of fold membership straight from the manifest rows.

    Raises ValueError on any violation; otherwise returns a JSON-able audit record. It does not
    reuse `loao_folds`, so a bug there cannot hide here.
    """
    ids = [r.sample_id for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate sample_id in manifest rows")
    checks: dict[str, bool | None] = {}
    per_fold = []
    seen_test: set[str] = set()
    for f in folds:
        test_ids = {ids[i] for i in f.test_idx}
        train_ids = {ids[i] for i in f.train_idx}
        target = f.fold_id.removeprefix("LOAO-")
        test_ad = {rows[i].adulterant_type for i in f.test_idx}
        train_ad = {rows[i].adulterant_type for i in f.train_idx}
        if test_ad != {target}:
            raise ValueError(f"{f.fold_id}: test set is not exactly adulterant {target}: {test_ad}")
        if target in train_ad:
            raise ValueError(f"{f.fold_id}: target adulterant leaked into train")
        if test_ids & train_ids:
            raise ValueError(f"{f.fold_id}: shared sample ids between train and test")
        if len(test_ids) + len(train_ids) != len(rows):
            raise ValueError(f"{f.fold_id}: train + test does not cover every sample exactly once")
        if test_ids & seen_test:
            raise ValueError(f"{f.fold_id}: test samples reused by another fold")
        seen_test |= test_ids
        n_test = len(test_ids)
        if expect_full and n_test != EXPECTED_TARGET_SIZES[target]:
            raise ValueError(
                f"{f.fold_id}: n_test {n_test} != published {EXPECTED_TARGET_SIZES[target]}"
            )
        per_fold.append(
            {
                "fold_id": f.fold_id,
                "target_adulterant": target,
                "n_test": n_test,
                "n_train": len(train_ids),
                "train_adulterants": sorted(train_ad),
                "test_brands": dict(sorted(_count(rows[i].evoo_brand for i in f.test_idx).items())),
                "train_brands": dict(
                    sorted(_count(rows[i].evoo_brand for i in f.train_idx).items())
                ),
                "test_brands_absent_from_train": sorted(
                    {rows[i].evoo_brand for i in f.test_idx}
                    - {rows[i].evoo_brand for i in f.train_idx}
                ),
            }
        )
    if seen_test != set(ids):
        raise ValueError("the union of test sets is not every sample")
    checks.update(
        each_test_is_exactly_one_adulterant=True,
        target_adulterant_absent_from_train=True,
        train_test_sample_ids_disjoint=True,
        every_sample_tested_exactly_once=True,
        # True only when the full published design was expected AND matched; None = not applicable
        sizes_match_published=True if expect_full else None,
    )
    return {"n_samples": len(rows), "n_folds": len(folds), "checks": checks, "folds": per_fold}


def _count(items) -> dict[str, int]:
    out: dict[str, int] = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out
