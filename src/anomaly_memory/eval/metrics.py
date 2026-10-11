"""Metric replica for MVTec AD.

Conventions follow the official MVTec AD evaluation code (BSD-3, vendored
under ``tests/reference/mvtec_official`` and checked by tests):

* AU-PRO: connected components of each ground-truth mask with an 8-connected
  structuring element; per-region overlap averaged over ALL regions of the
  evaluated image set; FPR over all anomaly-free pixels (normal images and
  the normal pixels of defective images); every distinct score is a
  threshold (no binning); curve starts at (0,0) and ends at (1,1); area by
  the trapezoidal rule up to ``integration_limit`` (default 0.3) with linear
  interpolation at the limit, divided by the limit.
* Image AUROC: exact, ties merged (equivalent to the official ROC +
  trapezoid). The image score is supplied by the method (official script
  uses max of the anomaly map; PatchCore uses its own patch-score max).
* Pixel AUROC: exact AUROC over all pixels of the evaluated set.

Which resolution the maps are evaluated at is a protocol decision recorded
in the evaluation config, not here.
"""

from __future__ import annotations

from bisect import bisect

import numpy as np
from scipy import ndimage
from scipy.stats import rankdata

STRUCTURE_8 = np.ones((3, 3), dtype=int)
STRUCTURE_4 = ndimage.generate_binary_structure(2, 1).astype(int)


def structure_for(connectivity: int) -> np.ndarray:
    if connectivity == 8:
        return STRUCTURE_8
    if connectivity == 4:
        return STRUCTURE_4
    raise ValueError("connectivity must be 4 or 8")


def auroc(scores, labels) -> float:
    """Exact AUROC with tie averaging (Mann-Whitney U). NaN if a class is empty."""
    s = np.asarray(scores).ravel()
    if s.dtype not in (np.float32, np.float64):
        s = s.astype(np.float64)
    y = np.asarray(labels).ravel().astype(bool)
    if s.shape != y.shape:
        raise ValueError(f"shape mismatch {s.shape} vs {y.shape}")
    if not np.all(np.isfinite(s)):
        raise ValueError("non-finite scores")
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = rankdata(s)
    u = ranks[y].sum() - n_pos * (n_pos + 1) / 2.0
    return float(u / (n_pos * n_neg))


def _stack(maps) -> np.ndarray:
    arr = np.asarray(maps) if not isinstance(maps, np.ndarray) else maps
    if arr.ndim != 3:
        raise ValueError(f"expected (N,H,W) maps, got shape {arr.shape}")
    return arr


def pixel_auroc(anomaly_maps, gt_masks) -> float:
    a = _stack(anomaly_maps)
    g = _stack(gt_masks)
    if a.shape != g.shape:
        raise ValueError(f"map/mask shape mismatch {a.shape} vs {g.shape}")
    flat = a.reshape(-1)
    if flat.dtype not in (np.float32, np.float64):
        flat = flat.astype(np.float32)
    return auroc(flat, g.reshape(-1) > 0)


def pro_weights(gt_masks, connectivity: int = 8, region_filter=None):
    """Per-pixel FP and PRO increments, as in the official ``compute_pro``.

    ``region_filter(area_px) -> bool`` optionally keeps only some GT regions
    (used for component-size strata). Pixels of excluded regions are neither
    OK pixels nor counted regions, so they do not affect the curve.
    Returns (fp_inc uint8, pro_inc float64, n_ok, n_regions).
    """
    g = _stack(gt_masks) > 0
    st = structure_for(connectivity)
    fp_inc = np.zeros(g.shape, dtype=np.uint8)
    pro_inc = np.zeros(g.shape, dtype=np.float64)
    n_ok = 0
    n_regions = 0
    for i in range(g.shape[0]):
        labeled, n = ndimage.label(g[i], structure=st)
        ok = labeled == 0
        fp_inc[i][ok] = 1
        n_ok += int(ok.sum())
        if n:
            areas = np.bincount(labeled.ravel(), minlength=n + 1)
            for k in range(1, n + 1):
                if region_filter is not None and not region_filter(int(areas[k])):
                    continue
                pro_inc[i][labeled == k] = 1.0 / areas[k]
                n_regions += 1
    return fp_inc, pro_inc, n_ok, n_regions


def pro_curve(anomaly_maps, gt_masks, connectivity: int = 8, region_filter=None):
    """(fprs, pros) arrays exactly as the official ``compute_pro`` returns them."""
    a = _stack(anomaly_maps)
    fp_inc, pro_inc, n_ok, n_regions = pro_weights(gt_masks, connectivity, region_filter)
    if a.shape != fp_inc.shape:
        raise ValueError(f"map/mask shape mismatch {a.shape} vs {fp_inc.shape}")
    if n_regions == 0:
        raise ValueError("no ground-truth regions in the evaluated set; PRO undefined")
    if n_ok == 0:
        raise ValueError("no anomaly-free pixels; FPR undefined")
    scores = a.reshape(-1)
    if scores.dtype not in (np.float32, np.float64):
        scores = scores.astype(np.float32)  # float16 storage -> exact in float32; avoids 8-byte copies
    order = np.argsort(scores, kind="stable")[::-1]
    del a
    s_sorted = scores[order]
    keep = np.append(np.diff(s_sorted) != 0, True)
    del s_sorted
    fprs = np.cumsum(fp_inc.reshape(-1)[order], dtype=np.int64)[keep] / n_ok
    pros = np.cumsum(pro_inc.reshape(-1)[order])[keep] / n_regions
    fprs = np.clip(fprs, None, 1.0)
    pros = np.clip(pros, None, 1.0)
    return np.concatenate(([0.0], fprs, [1.0])), np.concatenate(([0.0], pros, [1.0]))


def trapezoid(x, y, x_max: float | None = None) -> float:
    """Trapezoidal area with the official interpolated cut-off at ``x_max``."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    finite = np.isfinite(x) & np.isfinite(y)
    x, y = x[finite], y[finite]
    correction = 0.0
    if x_max is not None:
        if x_max not in x:
            ins = bisect(x.tolist(), x_max)
            if not 0 < ins < len(x):
                raise ValueError("x_max outside the curve's range")
            y_interp = y[ins - 1] + (y[ins] - y[ins - 1]) * (x_max - x[ins - 1]) / (x[ins] - x[ins - 1])
            correction = 0.5 * (y_interp + y[ins - 1]) * (x_max - x[ins - 1])
        keep = x <= x_max
        x, y = x[keep], y[keep]
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * (x[1:] - x[:-1])) + correction)


def au_pro(anomaly_maps, gt_masks, integration_limit: float = 0.3, connectivity: int = 8,
           region_filter=None) -> float:
    """Normalised area under the PRO curve up to ``integration_limit`` (FPR)."""
    if not 0.0 < integration_limit <= 1.0:
        raise ValueError("integration_limit must be in (0, 1]")
    fprs, pros = pro_curve(anomaly_maps, gt_masks, connectivity, region_filter)
    return trapezoid(fprs, pros, x_max=integration_limit) / integration_limit


def image_scores_from_maps(anomaly_maps, reduce: str = "max") -> np.ndarray:
    a = _stack(anomaly_maps)
    if reduce == "max":
        return a.reshape(a.shape[0], -1).max(axis=1)
    if reduce == "mean":
        return a.reshape(a.shape[0], -1).mean(axis=1)
    raise ValueError(f"unknown reduce {reduce!r}")


METRIC_VERSION = "mvtec-official-replica-v1"


def pro_curves_shared(anomaly_maps, gt_masks, region_filters: dict, connectivity: int = 8) -> dict:
    """PRO curves for several region filters with ONE global sort (identical to
    calling ``pro_curve`` per filter). ``region_filters`` maps a name to
    ``None`` (all regions) or a predicate on region area in pixels."""
    a = _stack(anomaly_maps)
    g = _stack(gt_masks) > 0
    if a.shape != g.shape:
        raise ValueError(f"map/mask shape mismatch {a.shape} vs {g.shape}")
    st = structure_for(connectivity)
    labels = np.zeros(g.shape, dtype=np.int32)
    areas_all, offset = [0], 0
    for i in range(g.shape[0]):
        lab, n = ndimage.label(g[i], structure=st)
        if n:
            areas_all.extend(np.bincount(lab.ravel(), minlength=n + 1)[1:].tolist())
            labels[i] = np.where(lab > 0, lab + offset, 0)
            offset += n
    areas = np.asarray(areas_all, dtype=np.float64)  # index 0 = background
    scores = a.reshape(-1)
    if scores.dtype not in (np.float32, np.float64):
        scores = scores.astype(np.float32)
    order = np.argsort(scores, kind="stable")[::-1]
    s_sorted = scores[order]
    keep = np.append(np.diff(s_sorted) != 0, True)
    del s_sorted
    lab_sorted = labels.reshape(-1)[order]
    del order
    out = {}
    for name, filt in region_filters.items():
        sel = np.ones(len(areas), bool) if filt is None else np.array([filt(int(x)) for x in areas])
        sel[0] = False
        n_regions = int(sel.sum())
        if n_regions == 0:
            out[name] = None
            continue
        is_ok = lab_sorted == 0
        n_ok = int(is_ok.sum())
        w = np.where(sel, 1.0 / np.maximum(areas, 1), 0.0)
        fprs = np.cumsum(is_ok, dtype=np.int64)[keep] / n_ok
        pros = np.cumsum(w[lab_sorted])[keep] / n_regions
        out[name] = (np.concatenate(([0.0], np.clip(fprs, None, 1.0), [1.0])),
                     np.concatenate(([0.0], np.clip(pros, None, 1.0), [1.0])), n_regions)
    return out
