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
    secondary_integration_limit: float = 0.05  # MVTec AD 2 convention, more sensitive to small defects
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
    }
    # one global sort serves the aggregate curve and every region-size bin (identical to separate calls)
    filters = {"all": None}
    if sspec is not None:
        n_px = masks.shape[1] * masks.shape[2]
        e = sspec.area_fraction_edges
        for i, lab in enumerate(sspec.labels):
            last = i == len(sspec.labels) - 1
            filters[lab] = (lambda a, lo=e[i], hi=e[i + 1], last=last:
                            lo <= a / n_px < hi or (last and a / n_px == hi))
    curves = metrics.pro_curves_shared(maps, masks, filters, mspec.connectivity)

    def area(c, lim):
        return float("nan") if c is None else metrics.trapezoid(c[0], c[1], x_max=lim) / lim
    res["au_pro"] = area(curves["all"], mspec.pro_integration_limit)
    res["au_pro_secondary"] = area(curves["all"], mspec.secondary_integration_limit)
    rows = []
    if sspec is not None:
        # PRIMARY (H-01): region-level strata, every 8-connected component in its own size bin
        res["region_strata"] = [
            {"stratum": lab, "n_regions": 0 if curves[lab] is None else curves[lab][2],
             "reportable": curves[lab] is not None and curves[lab][2] >= sspec.min_images_per_cell,
             "au_pro": area(curves[lab], mspec.pro_integration_limit),
             "au_pro_secondary": area(curves[lab], mspec.secondary_integration_limit)}
            for lab in sspec.labels]
        # SECONDARY: image-level detection strata; an image takes the bin of its LARGEST component
        largest = np.array([_largest_component_fraction(m, mspec.connectivity) if l else 0.0
                            for m, l in zip(masks, labels)])
        st = np.where(labels == 1, strata.assign(largest, sspec), -1)
        img = strata.stratified_image_auroc(scores, labels, st, len(sspec.labels))
        res["strata"] = [{"stratum": sspec.labels[a["stratum"]], "n_defective": a["n_defective"],
                          "n_normal": a["n_normal"], "reportable": a["n_defective"] >= sspec.min_images_per_cell,
                          "image_auroc": a["image_auroc"]} for a in img]
    else:
        st = np.full(len(test), -1)
    for r, s, sc, fr, er in zip(test, st, scores, native_frac, erased):
        rows.append({"relpath": r.relpath, "category": r.category, "defect_type": r.defect_type, "label": r.label,
                     "image_score": float(sc), "native_area_fraction": float(fr),
                     "stratum": (sspec.labels[s] if sspec is not None and s >= 0 else ""),
                     "erased_by_policy": bool(er)})
    return res, rows


def _largest_component_fraction(mask: np.ndarray, connectivity: int) -> float:
    from scipy import ndimage
    lab, n = ndimage.label(mask, structure=metrics.structure_for(connectivity))
    return float(np.bincount(lab.ravel())[1:].max() / mask.size) if n else 0.0


def macro_average(per_cat: dict[str, dict], key: str) -> float:
    vals = [v[key] for v in per_cat.values() if np.isfinite(v[key])]
    return float(np.mean(vals)) if vals else float("nan")
