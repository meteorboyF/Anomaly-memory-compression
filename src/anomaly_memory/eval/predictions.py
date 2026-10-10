"""On-disk prediction format: one ``<category>.npz`` per category.

Keys: ``relpaths`` (str, test image paths relative to the dataset root),
``image_scores`` (float32), ``anomaly_maps`` (float16, N x H x W at the
evaluation resolution), ``meta`` (JSON string: method, geometry policy).
Raw maps are kept so metrics can be recomputed without re-running any
backbone. float16 is used for storage; scores are cast to float64 for
metrics. (float16 creates ties among close scores; the tie handling of the
metric replica is exact, and the precision choice is recorded in ``meta``.)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

KEYS = ("relpaths", "image_scores", "anomaly_maps", "meta")


class PredictionError(ValueError):
    pass


def save(path: Path, relpaths: list[str], image_scores, anomaly_maps, meta: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    maps = np.asarray(anomaly_maps)
    if maps.ndim != 3 or maps.shape[0] != len(relpaths):
        raise PredictionError(f"anomaly_maps shape {maps.shape} inconsistent with {len(relpaths)} paths")
    scores = np.asarray(image_scores, dtype=np.float32)
    if scores.shape != (len(relpaths),):
        raise PredictionError("image_scores must have one value per path")
    if not (np.isfinite(scores).all() and np.isfinite(maps).all()):
        raise PredictionError("non-finite predictions")
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, relpaths=np.array(relpaths), image_scores=scores,
                        anomaly_maps=maps.astype(np.float16), meta=np.array(json.dumps(meta, sort_keys=True)))
    tmp.replace(path)
    return path


def load(path: Path, expected_relpaths: list[str] | None = None) -> dict:
    with np.load(path, allow_pickle=False) as z:
        missing = [k for k in KEYS if k not in z.files]
        if missing:
            raise PredictionError(f"{path}: missing keys {missing}")
        out = {"relpaths": [str(x) for x in z["relpaths"]], "image_scores": z["image_scores"].astype(np.float64),
               "anomaly_maps": z["anomaly_maps"], "meta": json.loads(str(z["meta"]))}
    if len(set(out["relpaths"])) != len(out["relpaths"]):
        raise PredictionError(f"{path}: duplicate relpaths")
    if expected_relpaths is not None and sorted(out["relpaths"]) != sorted(expected_relpaths):
        a, b = set(out["relpaths"]), set(expected_relpaths)
        raise PredictionError(f"{path}: prediction set != official test split "
                              f"(missing {len(b - a)}, extra {len(a - b)})")
    return out
