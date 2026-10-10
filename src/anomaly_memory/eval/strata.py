"""Defect-size strata, computed only from supplied ground-truth masks.

Primary unit: the defective test IMAGE, stratified by its native-resolution
defect area fraction (mask pixels / image pixels). Boundaries and minimum
cell counts are pre-registered in the evaluation config (see
``docs/REALITY_CHECK.md``) before any comparative outcome is examined.

Masks are never used for memory construction, method design, thresholds or
hyper-parameter selection; only here and in scripted evaluation.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from . import metrics


@dataclasses.dataclass
class StrataSpec:
    # Bin edges on native area fraction, ascending, first 0.0 and last 1.0;
    # bins are [lo, hi) except the last, which is closed.
    area_fraction_edges: list[float]
    labels: list[str]
    min_images_per_cell: int  # per category x stratum; smaller cells are reported as n/a
    min_images_pooled: int

    def validate(self) -> None:
        e = self.area_fraction_edges
        if len(e) < 2 or e[0] != 0.0 or e[-1] != 1.0 or any(b <= a for a, b in zip(e, e[1:])):
            raise ValueError("area_fraction_edges must increase strictly from 0.0 to 1.0")
        if len(self.labels) != len(e) - 1:
            raise ValueError("need one label per bin")


def assign(area_fraction: np.ndarray, spec: StrataSpec) -> np.ndarray:
    """Stratum index per image; -1 for normal images (area 0 and label 0 handled by caller)."""
    a = np.asarray(area_fraction, dtype=np.float64)
    idx = np.searchsorted(np.asarray(spec.area_fraction_edges[1:-1]), a, side="right")
    return idx.astype(int)


def stratified_image_auroc(scores, labels, strata, n_strata: int) -> list[dict]:
    """AUROC of each stratum's defective images against ALL normal test images."""
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels).astype(bool)
    strata = np.asarray(strata)
    normal = ~labels
    out = []
    for s in range(n_strata):
        sel = labels & (strata == s)
        keep = normal | sel
        n_def = int(sel.sum())
        val = metrics.auroc(scores[keep], labels[keep]) if n_def and normal.any() else float("nan")
        out.append({"stratum": s, "n_defective": n_def, "n_normal": int(normal.sum()), "image_auroc": val})
    return out


def stratified_au_pro(maps, masks, labels, strata, n_strata: int, integration_limit: float = 0.3,
                      connectivity: int = 8) -> list[dict]:
    """AU-PRO restricted to one stratum's defective images, with ALL normal
    images' pixels in the FPR (plus the normal pixels of the selected images)."""
    labels = np.asarray(labels).astype(bool)
    strata = np.asarray(strata)
    out = []
    for s in range(n_strata):
        sel = labels & (strata == s)
        keep = ~labels | sel
        if sel.sum() == 0:
            out.append({"stratum": s, "n_defective": 0, "au_pro": float("nan")})
            continue
        val = metrics.au_pro(maps[keep], masks[keep], integration_limit, connectivity)
        out.append({"stratum": s, "n_defective": int(sel.sum()), "au_pro": val})
    return out


def region_stratified_au_pro(maps, masks, spec: StrataSpec, integration_limit: float = 0.3,
                             connectivity: int = 8) -> list[dict]:
    """AU-PRO over only the GT regions whose size fraction falls in each bin.

    Region size = component pixels / image pixels at the evaluation
    resolution (native under P-STUDY). FPR uses all defect-free pixels of the
    evaluated set (official definition); pixels of regions outside the bin
    count neither as OK pixels nor as regions.
    """
    maps = np.asarray(maps)
    masks = np.asarray(masks)
    n_px = masks.shape[1] * masks.shape[2]
    edges = spec.area_fraction_edges
    out = []
    for s, label in enumerate(spec.labels):
        lo, hi = edges[s], edges[s + 1]
        last = s == len(spec.labels) - 1

        def keep(area_px, lo=lo, hi=hi, last=last):
            f = area_px / n_px
            return lo <= f < hi or (last and f == hi)

        _, _, _, n_regions = metrics.pro_weights(masks, connectivity, keep)
        val = metrics.au_pro(maps, masks, integration_limit, connectivity, keep) if n_regions else float("nan")
        out.append({"stratum": label, "n_regions": n_regions, "au_pro": val})
    return out
