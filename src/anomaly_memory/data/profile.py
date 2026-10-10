"""Outcome-free dataset profile: sizes, mask areas, geometry losses, duplicates.

Everything here is computed from images and supplied masks only. No model
output is involved, so examining it does not contaminate pre-registration
of the defect-size strata.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from ..eval.metrics import structure_for
from .mvtec import Record
from .preprocess import GeometryPolicy, load_mask, native_crop_window, transform_mask

ROW_FIELDS = (
    "category", "split", "defect_type", "relpath", "label", "width", "height", "mode",
    "file_sha256", "pixel_sha256",
    "native_area_px", "native_area_fraction", "native_components", "native_min_component_px",
    "native_max_component_px", "policy_area_px", "policy_area_fraction", "policy_components",
    "erased_by_policy", "native_px_outside_crop", "components_fully_outside_crop",
)


def _hashes(path: Path) -> tuple[str, str, tuple[int, int], str]:
    data = path.read_bytes()
    fsha = hashlib.sha256(data).hexdigest()
    with Image.open(path) as im:
        size, mode = im.size, im.mode
        psha = hashlib.sha256(np.asarray(im).tobytes() + str(im.size).encode()).hexdigest()
    return fsha, psha, size, mode


def profile_record(root: Path, r: Record, policy: GeometryPolicy, connectivity: int = 8) -> dict:
    fsha, psha, (w, h), mode = _hashes(root / r.relpath)
    row = {"category": r.category, "split": r.split, "defect_type": r.defect_type, "relpath": r.relpath,
           "label": r.label, "width": w, "height": h, "mode": mode, "file_sha256": fsha, "pixel_sha256": psha}
    if r.mask_relpath is None:
        row.update({k: 0 for k in ROW_FIELDS if k not in row})
        row["erased_by_policy"] = False
        return row
    m = load_mask(root / r.mask_relpath)
    st = structure_for(connectivity)
    lab, n = ndimage.label(m, structure=st)
    areas = np.bincount(lab.ravel())[1:] if n else np.array([0])
    pm = transform_mask(m, policy)
    _, pn = ndimage.label(pm, structure=st)
    t, l, b, rr = native_crop_window(m.shape, policy)
    inside = np.zeros_like(m)
    inside[t:b, l:rr] = True
    outside_px = int((m & ~inside).sum())
    fully_out = 0
    for k in range(1, n + 1):
        if not (inside & (lab == k)).any():
            fully_out += 1
    row.update({
        "native_area_px": int(m.sum()), "native_area_fraction": float(m.mean()), "native_components": int(n),
        "native_min_component_px": int(areas.min()), "native_max_component_px": int(areas.max()),
        "policy_area_px": int(pm.sum()), "policy_area_fraction": float(pm.mean()), "policy_components": int(pn),
        "erased_by_policy": bool(m.any() and not pm.any()), "native_px_outside_crop": outside_px,
        "components_fully_outside_crop": fully_out,
    })
    return row


def summarise(rows: list[dict]) -> dict:
    by_cat: dict = defaultdict(lambda: {"train_good": 0, "test_good": 0, "test_defect": 0, "sizes": Counter(),
                                        "modes": Counter(), "defect_types": Counter()})
    file_groups = defaultdict(list)
    pixel_groups = defaultdict(list)
    for r in rows:
        c = by_cat[r["category"]]
        key = "train_good" if r["split"] == "train" else ("test_defect" if r["label"] else "test_good")
        c[key] += 1
        c["sizes"][f"{r['width']}x{r['height']}"] += 1
        c["modes"][r["mode"]] += 1
        if r["label"]:
            c["defect_types"][r["defect_type"]] += 1
        file_groups[r["file_sha256"]].append(r)
        pixel_groups[r["pixel_sha256"]].append(r)

    def dup_report(groups):
        dups = [g for g in groups.values() if len(g) > 1]
        cross_split = [g for g in dups if len({x["split"] for x in g}) > 1]
        cross_cat = [g for g in dups if len({x["category"] for x in g}) > 1]
        return {"n_duplicate_groups": len(dups), "n_cross_split_groups": len(cross_split),
                "n_cross_category_groups": len(cross_cat),
                "examples": [[x["relpath"] for x in g] for g in dups[:20]]}

    defect = [r for r in rows if r["label"]]
    fr = np.array([r["native_area_fraction"] for r in defect]) if defect else np.array([])
    quant = {f"q{int(q * 100):02d}": float(np.quantile(fr, q)) for q in (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)} \
        if fr.size else {}
    per_cat_area = {}
    for cat in sorted(by_cat):
        f = np.array([r["native_area_fraction"] for r in defect if r["category"] == cat])
        if f.size:
            per_cat_area[cat] = {"n": int(f.size), "median": float(np.median(f)), "min": float(f.min()),
                                 "max": float(f.max())}
    return {
        "categories": {k: {**{kk: v for kk, v in d.items() if kk not in ("sizes", "modes", "defect_types")},
                           "sizes": dict(d["sizes"]), "modes": dict(d["modes"]),
                           "defect_types": dict(d["defect_types"])} for k, d in sorted(by_cat.items())},
        "totals": {"images": len(rows), "train_good": sum(d["train_good"] for d in by_cat.values()),
                   "test_good": sum(d["test_good"] for d in by_cat.values()),
                   "test_defect": sum(d["test_defect"] for d in by_cat.values())},
        "defect_area_fraction_quantiles": quant,
        "per_category_defect_area": per_cat_area,
        "erased_by_policy": [r["relpath"] for r in defect if r["erased_by_policy"]],
        "defects_with_pixels_outside_crop": sum(1 for r in defect if r["native_px_outside_crop"] > 0),
        "components_fully_outside_crop_total": int(sum(r["components_fully_outside_crop"] for r in defect)),
        "defective_with_empty_mask": [r["relpath"] for r in defect if r["native_area_px"] == 0],
        "exact_file_duplicates": dup_report(file_groups),
        "exact_pixel_duplicates": dup_report(pixel_groups),
    }
