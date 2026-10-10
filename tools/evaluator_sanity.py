"""Evaluator sanity on the REAL test split (CPU): constant, random, and
oracle-mask predictions pushed through the full prediction-file -> evaluator
path. Expected: constant/random ~0.5 AUROC and ~0.15 AU-PRO; oracle 1.0
(minus any defects erased by the geometry policy, which this reports).

    python tools/evaluator_sanity.py --config evaluator_sanity
"""

from __future__ import annotations

import csv
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anomaly_memory.baselines.trivial import KINDS, make_maps  # noqa: E402
from anomaly_memory.data import mvtec  # noqa: E402
from anomaly_memory.data.preprocess import GeometryPolicy  # noqa: E402
from anomaly_memory.eval import predictions  # noqa: E402
from anomaly_memory.eval.evaluate import MetricSpec, evaluate_category, ground_truth, macro_average  # noqa: E402
from anomaly_memory.eval.strata import StrataSpec  # noqa: E402
from anomaly_memory.io_utils import atomic_write_json  # noqa: E402
from anomaly_memory.runctx import RunContext, ToolSpec, run_tool  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_data import dataset_root  # noqa: E402


@dataclasses.dataclass
class Config:
    SCHEMA_VERSION = 1
    extracted_dirname: str
    categories: list[str]
    kinds: list[str]
    geometry: GeometryPolicy
    metric: MetricSpec
    strata: StrataSpec
    seed: int = 0

    def validate(self) -> None:
        bad = set(self.kinds) - set(KINDS)
        if bad:
            raise ValueError(f"unknown kinds {bad}")


SPEC = ToolSpec(name="evaluator_sanity", schema=Config, tier="cpu", phase="phase0",
                science_modules=["anomaly_memory.eval.metrics", "anomaly_memory.eval.evaluate",
                                 "anomaly_memory.eval.strata", "anomaly_memory.eval.predictions",
                                 "anomaly_memory.data.preprocess", "anomaly_memory.baselines.trivial"],
                durable_kind="manifests", description=__doc__)


def body(ctx: RunContext) -> dict:
    cfg: Config = ctx.cfg
    root = dataset_root(cfg.extracted_dirname)
    cats = cfg.categories[:2] if ctx.smoke else cfg.categories
    results: dict = {}
    for kind in cfg.kinds:
        per_cat, all_rows = {}, []
        for ci, cat in enumerate(cats):
            recs, rep = mvtec.scan(root, [cat])
            if not rep.ok:
                raise RuntimeError(rep.errors[:5])
            test = [r for r in recs if r.split == "test"]
            masks, _, _ = ground_truth(root, test, cfg.geometry)
            maps, scores = make_maps(kind, masks, cfg.seed + ci)
            p = predictions.save(ctx.work_dir / "pred" / kind / f"{cat}.npz", [r.relpath for r in test], scores,
                                 maps, {"method": f"trivial:{kind}", "geometry": cfg.geometry.name})
            res, rows = evaluate_category(root, recs, p, cfg.geometry, cfg.metric, cfg.strata)
            p.unlink()  # trivial predictions are cheap to regenerate; not persisted
            per_cat[cat] = res
            all_rows += [dict(r, method=kind) for r in rows]
            ctx.log(f"{kind:12s} {cat:11s} img {res['image_auroc']:.4f} pix {res['pixel_auroc']:.4f} "
                    f"aupro {res['au_pro']:.4f} erased {res['n_erased_by_policy']}")
        results[kind] = {"per_category": per_cat,
                         "macro": {k: macro_average(per_cat, k) for k in ("image_auroc", "pixel_auroc", "au_pro")}}
        csv_path = ctx.work_dir / f"per_image_{kind}.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)
        ctx.register(csv_path, kind="table")
    out = ctx.work_dir / "evaluator_sanity.json"
    atomic_write_json(out, results)
    ctx.register(out, kind="metrics")
    for kind, r in results.items():
        ctx.log(f"MACRO {kind}: {r['macro']}")
    return {k: v["macro"] for k, v in results.items()}


if __name__ == "__main__":
    sys.exit(run_tool(SPEC, body))
