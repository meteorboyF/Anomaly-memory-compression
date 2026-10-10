"""Evaluator-sanity baselines (Phase 0, CPU only).

* ``constant``: every pixel and image scores 0 -> AUROC 0.5, AU-PRO@0.3 = 0.15.
* ``random``: i.i.d. uniform scores -> AUROC ~0.5, AU-PRO@0.3 ~0.15.
* ``oracle_mask``: the evaluation mask itself -> 1.0 on every metric. This
  reads test masks and exists ONLY to verify the evaluator end to end; it is
  never a method and never enters a comparison.

If a trivial baseline scores near published SOTA, the evaluator or split is
broken.
"""

from __future__ import annotations

import numpy as np

KINDS = ("constant", "random", "oracle_mask")


def make_maps(kind: str, masks: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    n = masks.shape[0]
    if kind == "constant":
        maps = np.zeros(masks.shape, dtype=np.float32)
        return maps, np.zeros(n, dtype=np.float32)
    if kind == "random":
        g = np.random.default_rng(seed)
        maps = g.random(masks.shape, dtype=np.float32)
        return maps, g.random(n, dtype=np.float32)
    if kind == "oracle_mask":
        maps = masks.astype(np.float32)
        return maps, maps.reshape(n, -1).max(1)
    raise ValueError(f"unknown trivial baseline {kind!r}; choose from {KINDS}")
