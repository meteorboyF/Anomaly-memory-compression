"""Pre-registered inference for H-01 (compression x defect size).

Primary quantity, per category c, seed s and size bin b:
    Delta_b = AUPRO_b(reference memory) - AUPRO_b(compressed memory)
    D = Delta_S - Delta_L      (> 0: compression costs small defects more)
averaged over seeds within a category, then macro-averaged over the
categories whose S and L cells meet the pre-registered minimum region count.

Uncertainty: a PAIRED, STRATIFIED image bootstrap. Within each category,
normal and defective test images are resampled with replacement separately,
and the SAME resampled image multiset is applied to every arm and every seed,
so the repeated measurement of an image across memories and seeds stays
paired; regions move with their image (clustering). Categories are fixed
strata (all 15 are the population of interest). Seeds enter as the mean
over the 3 paired seeds; their spread is reported separately and the sign
of D must agree across seeds for a "supported" verdict.

To make thousands of resamples affordable, AU-PRO is rebuilt from per-image
summaries on a fixed threshold grid (normal-pixel exceedance counts per
image, per-region overlap fractions). The grid approximation is checked
against the exact official computation (``max_grid_error``); point estimates
in the paper always use the exact algorithm (``metrics.au_pro``).
"""

from __future__ import annotations

import dataclasses

import numpy as np
from scipy import ndimage

from . import metrics


@dataclasses.dataclass
class PROSummary:
    thresholds: np.ndarray  # (T,) descending
    normal_exceed: np.ndarray  # (N, T) normal pixels with score >= t, per image
    n_normal: np.ndarray  # (N,)
    region_overlap: np.ndarray  # (R, T) fraction of region pixels with score >= t
    region_image: np.ndarray  # (R,) image index of each region
    region_frac: np.ndarray  # (R,) region pixels / image pixels


def threshold_grid(maps, masks, n_thresholds: int = 2000, max_fpr: float = 0.5) -> np.ndarray:
    """Thresholds at evenly spaced normal-pixel FPR levels in [0, max_fpr] (descending)."""
    normal = np.asarray(maps)[~(np.asarray(masks) > 0)]
    q = 1.0 - np.linspace(0.0, max_fpr, n_thresholds)
    return np.unique(np.quantile(normal, q))[::-1]


def summarise_pro(maps, masks, thresholds: np.ndarray, connectivity: int = 8) -> PROSummary:
    maps = np.asarray(maps)
    masks = np.asarray(masks) > 0
    asc = thresholds[::-1]  # ascending for searchsorted
    st = metrics.structure_for(connectivity)
    n_img, n_t = maps.shape[0], len(thresholds)
    exceed = np.zeros((n_img, n_t), dtype=np.int64)
    n_normal = np.zeros(n_img, dtype=np.int64)
    overlaps, r_img, r_frac = [], [], []
    for i in range(n_img):
        m = masks[i]
        lab, n = ndimage.label(m, structure=st)
        normal = np.sort(maps[i][~m])
        n_normal[i] = normal.size
        # count of normal scores >= t  =  size - (number < t)
        exceed[i] = (normal.size - np.searchsorted(normal, asc, side="left"))[::-1]
        for k in range(1, n + 1):
            vals = np.sort(maps[i][lab == k])
            overlaps.append(((vals.size - np.searchsorted(vals, asc, side="left")) / vals.size)[::-1])
            r_img.append(i)
            r_frac.append(vals.size / m.size)
    ov = np.array(overlaps) if overlaps else np.zeros((0, n_t))
    return PROSummary(thresholds, exceed, n_normal, ov, np.array(r_img, dtype=int), np.array(r_frac))


def au_pro_from_summary(s: PROSummary, image_weight: np.ndarray, region_keep: np.ndarray,
                        integration_limit: float = 0.3) -> float:
    """AU-PRO on the threshold grid for a weighted (resampled) image multiset."""
    rw = image_weight[s.region_image] * region_keep
    if rw.sum() == 0:
        return float("nan")
    fpr = (image_weight @ s.normal_exceed) / (image_weight @ s.n_normal)
    pro = (rw @ s.region_overlap) / rw.sum()
    fpr = np.concatenate(([0.0], fpr, [1.0]))
    pro = np.concatenate(([0.0], pro, [1.0]))
    return metrics.trapezoid(fpr, pro, x_max=integration_limit) / integration_limit


def bin_mask(region_frac: np.ndarray, lo: float, hi: float, last: bool) -> np.ndarray:
    return ((region_frac >= lo) & (region_frac < hi)) | (last & (region_frac == hi))


@dataclasses.dataclass
class CategoryArms:
    """All arms/seeds of one category, evaluated on the same test images in the same order."""
    name: str
    is_defective: np.ndarray  # (N,) bool
    summaries: dict  # {arm: {seed: PROSummary}} sharing regions (masks are identical)


def _category_D(cat: CategoryArms, w: np.ndarray, ref: str, cmp: str, bins, small: int, large: int,
                limit: float) -> np.ndarray:
    """D per seed for one category under image weights w."""
    seeds = sorted(cat.summaries[ref])
    out = []
    for sd in seeds:
        deltas = []
        for b in (small, large):
            lo, hi, last = bins[b]
            keep = bin_mask(cat.summaries[ref][sd].region_frac, lo, hi, last)
            a_ref = au_pro_from_summary(cat.summaries[ref][sd], w, keep, limit)
            a_cmp = au_pro_from_summary(cat.summaries[cmp][sd], w, keep, limit)
            deltas.append(a_ref - a_cmp)
        out.append(deltas[0] - deltas[1])
    return np.array(out)


def bootstrap_contrast(cats: list[CategoryArms], edges: list[float], ref: str, cmp: str, *,
                       small: int = 0, large: int = -1, min_regions: int = 10, n_boot: int = 2000,
                       seed: int = 0, integration_limit: float = 0.3) -> dict:
    """Paired stratified image bootstrap of the macro D (in AU-PRO units, 0-1)."""
    nb = len(edges) - 1
    large = large % nb
    bins = [(edges[i], edges[i + 1], i == nb - 1) for i in range(nb)]
    valid, per_cat = [], {}
    for c in cats:
        any_sd = next(iter(c.summaries[ref].values()))
        n_s = int(bin_mask(any_sd.region_frac, *bins[small]).sum())
        n_l = int(bin_mask(any_sd.region_frac, *bins[large]).sum())
        ok = n_s >= min_regions and n_l >= min_regions
        full = np.ones(len(c.is_defective))
        d_seeds = _category_D(c, full, ref, cmp, bins, small, large, integration_limit)
        per_cat[c.name] = {"n_regions_small": n_s, "n_regions_large": n_l, "valid": ok,
                           "D_per_seed": d_seeds.tolist(), "D": float(d_seeds.mean())}
        if ok:
            valid.append(c)
    if not valid:
        return {"valid_categories": [], "per_category": per_cat, "D": float("nan")}
    point_seeds = np.mean([per_cat[c.name]["D_per_seed"] for c in valid], axis=0)
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot)
    for bi in range(n_boot):
        vals = []
        for c in valid:
            w = np.zeros(len(c.is_defective))
            for group in (np.flatnonzero(~c.is_defective), np.flatnonzero(c.is_defective)):
                np.add.at(w, rng.choice(group, size=group.size, replace=True), 1.0)
            vals.append(_category_D(c, w, ref, cmp, bins, small, large, integration_limit).mean())
        boot[bi] = np.mean(vals)
    return {
        "valid_categories": [c.name for c in valid], "per_category": per_cat,
        "D": float(point_seeds.mean()), "D_per_seed": point_seeds.tolist(),
        "seed_sd": float(point_seeds.std(ddof=1)) if len(point_seeds) > 1 else float("nan"),
        "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
        "ci90": [float(np.quantile(boot, 0.05)), float(np.quantile(boot, 0.95))],
        "n_boot": n_boot, "categories_D_positive": int(sum(per_cat[c.name]["D"] > 0 for c in valid)),
    }


def classify(result: dict, sesoi: float) -> str:
    """Pre-registered verdict (D-020). ``sesoi`` in the same units as D."""
    d = result["D"]
    lo95, hi95 = result["ci95"]
    lo90, hi90 = result["ci90"]
    seeds = np.sign(result["D_per_seed"])
    consistent = bool(np.all(seeds == np.sign(d))) if d != 0 else False
    if lo95 > 0 and d >= sesoi and consistent:
        return "supported: practically meaningful disproportionate loss on small defects"
    if hi95 < 0 and -d >= sesoi and consistent:
        return "reversed: practically meaningful disproportionate loss on LARGE defects"
    if -sesoi < lo90 and hi90 < sesoi:
        return "informative null: equivalence within +/- SESOI (TOST, alpha=0.05)"
    if lo95 > 0 or hi95 < 0:
        return "detectable but below SESOI or inconsistent across seeds"
    return "inconclusive: neither a meaningful effect nor equivalence is established"


def max_grid_error(maps, masks, thresholds, region_keep=None, integration_limit: float = 0.3) -> float:
    """|grid AU-PRO - exact AU-PRO| on the full image set (validation of the approximation)."""
    s = summarise_pro(maps, masks, thresholds)
    keep = np.ones(len(s.region_frac), bool) if region_keep is None else region_keep
    approx = au_pro_from_summary(s, np.ones(maps.shape[0]), keep, integration_limit)
    exact = metrics.au_pro(maps, masks, integration_limit)
    return abs(approx - exact)
