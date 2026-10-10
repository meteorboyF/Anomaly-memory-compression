"""Evaluate a directory of predictions against the official MVTec AD test split."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np

from ..data.mvtec import Record
from ..data.preprocess import GeometryPolicy, load_mask, transform_mask
from . import metrics, predictions, strata


@dataclasses.dataclass
class MetricSpec:
    pro_integration_limit: float = 0.3
    connectivity: int = 8
    category_average: str = "macro"  # unweighted mean over categories, as in the literature


def ground_truth(root: Path, recs: list[Record], policy: GeometryPolicy) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Masks at the evaluation resolution, labels, and NATIVE area fractions."""
    masks, labels, native_frac = [], [], []
    for r in recs:
        with_size = None
        if r.mask_relpath:
            m = load_mask(root / r.mask_relpath)
            native_frac.append(float(m.mean()))
        else:
            from PIL import Image
            with Image.open(root / r.relpath) as im:
                with_size = (im.size[1], im.size[0])
            m = np.zeros(with_size, dtype=bool)
            native_frac.append(0.0)
        masks.append(transform_mask(m, policy))
        labels.append(r.label)
    return np.stack(masks), np.asarray(labels, dtype=int), np.asarray(native_frac)


def evaluate_category(root: Path, recs: list[Record], pred_path: Path, policy: GeometryPolicy,
                      mspec: MetricSpec, sspec: strata.StrataSpec | None) -> tuple[dict, list[dict]]:
    test = [r for r in recs if r.split == "test"]
    pred = predictions.load(pred_path, expected_relpaths=[r.relpath for r in test])
    order = {p: i for i, p in enumerate(pred["relpaths"])}
    idx = np.array([order[r.relpath] for r in test])
    maps = pred["anomaly_maps"][idx].astype(np.float32)  # stored as float16; float32 is exact
    scores = pred["image_scores"][idx]
    masks, labels, native_frac = ground_truth(root, test, policy)
    if maps.shape != masks.shape:
        raise predictions.PredictionError(f"{pred_path}: map shape {maps.shape[1:]} != evaluation mask shape "
                                          f"{masks.shape[1:]} under policy {policy.name}")
    erased = (labels == 1) & (masks.reshape(len(test), -1).sum(1) == 0)
    res = {
        "n_test": len(test), "n_defective": int(labels.sum()), "n_erased_by_policy": int(erased.sum()),
        "image_auroc": metrics.auroc(scores, labels),
        "pixel_auroc": metrics.pixel_auroc(maps, masks),
        "au_pro": metrics.au_pro(maps, masks, mspec.pro_integration_limit, mspec.connectivity),
    }
    rows = []
    if sspec is not None:
        st = np.where(labels == 1, strata.assign(native_frac, sspec), -1)
        img = strata.stratified_image_auroc(scores, labels, st, len(sspec.labels))
        pro = strata.stratified_au_pro(maps, masks, labels, st, len(sspec.labels), mspec.pro_integration_limit,
                                       mspec.connectivity)
        cells = []
        for a, b in zip(img, pro):
            ok = a["n_defective"] >= sspec.min_images_per_cell
            cells.append({"stratum": sspec.labels[a["stratum"]], "n_defective": a["n_defective"],
                          "n_normal": a["n_normal"], "reportable": ok,
                          "image_auroc": a["image_auroc"], "au_pro": b["au_pro"]})
        res["strata"] = cells
    else:
        st = np.full(len(test), -1)
    for r, s, sc, fr, er in zip(test, st, scores, native_frac, erased):
        rows.append({"relpath": r.relpath, "category": r.category, "defect_type": r.defect_type, "label": r.label,
                     "image_score": float(sc), "native_area_fraction": float(fr),
                     "stratum": (sspec.labels[s] if sspec is not None and s >= 0 else ""),
                     "erased_by_policy": bool(er)})
    return res, rows


def macro_average(per_cat: dict[str, dict], key: str) -> float:
    vals = [v[key] for v in per_cat.values() if np.isfinite(v[key])]
    return float(np.mean(vals)) if vals else float("nan")
