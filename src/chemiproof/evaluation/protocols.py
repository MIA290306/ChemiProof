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
