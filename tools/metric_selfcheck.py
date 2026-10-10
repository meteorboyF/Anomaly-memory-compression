"""Validate the metric replica on CPU, without the dataset.

Checks (all must pass, else nonzero exit):
1. exact agreement with the vendored official MVTec AD evaluation code
   (AU-PRO, PRO curve, image AUROC) on randomized synthetic sets, including
   heavy score ties;
2. the official toy example (200 random maps, 10x10 GT) from the MVTec code;
3. analytic cases: perfect maps -> 1.0, constant maps -> AU-PRO 0.15,
   inverted maps -> AUROC 0.0.

    python tools/metric_selfcheck.py --config metric_selfcheck
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from anomaly_memory.eval import metrics as M  # noqa: E402
from anomaly_memory.io_utils import atomic_write_json  # noqa: E402
from anomaly_memory.runctx import RunContext, ToolSpec, run_tool  # noqa: E402


@dataclasses.dataclass
class Config:
    SCHEMA_VERSION = 1
    n_random_cases: int
    tolerance: float
    integration_limit: float = 0.3
    seed: int = 0


SPEC = ToolSpec(name="metric_selfcheck", schema=Config, tier="cpu", phase="phase0",
                science_modules=["anomaly_memory.eval.metrics"], durable_kind="manifests", description=__doc__)


def _official():
    sys.path.insert(0, str(ROOT / "tests" / "reference" / "mvtec_official"))
    import generic_util as G  # noqa: E402
    import pro_curve_util as P  # noqa: E402
    import roc_curve_util as R  # noqa: E402
    return G, P, R


def random_case(rng, quantize):
    n, h, w = int(rng.integers(3, 9)), int(rng.integers(8, 40)), int(rng.integers(8, 40))
    gt = np.zeros((n, h, w))
    for i in range(n):
        if rng.random() < 0.7:
            for _ in range(int(rng.integers(1, 4))):
                y, x = rng.integers(0, h - 3), rng.integers(0, w - 3)
                gt[i, y:y + rng.integers(1, 7), x:x + rng.integers(1, 7)] = 1
    if gt.sum() == 0:
        gt[0, 0, 0] = 1
    if gt[:, :, :].reshape(n, -1).any(1).all():
        gt[-1] = 0  # keep at least one normal image
    maps = rng.random((n, h, w)) + rng.random() * gt
    if quantize:
        maps = np.round(maps * quantize) / quantize
    return maps, gt


def body(ctx: RunContext) -> dict:
    cfg: Config = ctx.cfg
    G, P, R = _official()
    rng = np.random.default_rng(cfg.seed)
    lim = cfg.integration_limit
    worst = {"au_pro": 0.0, "pro_curve": 0.0, "image_auroc": 0.0}
    n_cases = 5 if ctx.smoke else cfg.n_random_cases
    quiet = io.StringIO()
    for i in range(n_cases):
        maps, gt = random_case(rng, [None, 3, 10, 100][i % 4])
        with contextlib.redirect_stdout(quiet):
            f1, p1 = P.compute_pro(list(maps), list(gt))
        a1 = G.trapezoid(f1, p1, x_max=lim) / lim
        f2, p2 = M.pro_curve(maps, gt)
        worst["au_pro"] = max(worst["au_pro"], float(abs(a1 - M.au_pro(maps, gt, lim))))
        worst["pro_curve"] = max(worst["pro_curve"], float(np.abs(f1 - f2).max()), float(np.abs(p1 - p2).max()))
        labels = [int(g.any()) for g in gt]
        fr, tr = R.compute_classification_roc(list(maps), np.max, labels)
        worst["image_auroc"] = max(worst["image_auroc"],
                                   float(abs(G.trapezoid(fr, tr) - M.auroc(M.image_scores_from_maps(maps), labels))))
    # official toy example (same generator/seed as pro_curve_util.main)
    np.random.seed(1338)
    toy_maps = np.stack([np.random.random((300, 500)) for _ in range(40 if ctx.smoke else 200)])
    toy_gt = np.zeros_like(toy_maps)
    toy_gt[:, 0:10, 0:10] = 1
    with contextlib.redirect_stdout(quiet):
        tf, tp = P.compute_pro(list(toy_maps), list(toy_gt))
    toy_official = G.trapezoid(tf, tp, x_max=lim) / lim
    toy_ours = M.au_pro(toy_maps, toy_gt, lim)
    # analytic
    gt = np.zeros((4, 16, 16))
    gt[0, 2:5, 2:5] = 1
    gt[1, 8:14, 1:3] = 1
    analytic = {
        "perfect_au_pro": M.au_pro(gt.copy(), gt, lim),
        "perfect_pixel_auroc": M.pixel_auroc(gt.copy(), gt),
        "constant_au_pro": M.au_pro(np.zeros_like(gt), gt, lim),
        "inverted_pixel_auroc": M.pixel_auroc(1 - gt, gt),
    }
    expected = {"perfect_au_pro": 1.0, "perfect_pixel_auroc": 1.0, "constant_au_pro": 0.15,
                "inverted_pixel_auroc": 0.0}
    failures = [k for k, v in worst.items() if v > cfg.tolerance]
    if abs(toy_official - toy_ours) > cfg.tolerance:
        failures.append("official_toy_example")
    failures += [k for k, v in analytic.items() if abs(v - expected[k]) > 1e-9]
    report = {"metric_version": M.METRIC_VERSION, "n_random_cases": n_cases, "max_abs_diff_vs_official": worst,
              "official_toy_au_pro": {"official": float(toy_official), "ours": float(toy_ours)}, "analytic": analytic,
              "analytic_expected": expected, "tolerance": cfg.tolerance, "failures": failures}
    out = ctx.work_dir / "metric_selfcheck.json"
    atomic_write_json(out, report)
    ctx.register(out, kind="report")
    ctx.log(f"max |diff| vs official: {worst}; toy AU-PRO official={toy_official:.6f} ours={toy_ours:.6f}")
    if failures:
        raise AssertionError(f"metric self-check FAILED: {failures}")
    ctx.log("metric self-check PASSED")
    return report


if __name__ == "__main__":
    sys.exit(run_tool(SPEC, body))
