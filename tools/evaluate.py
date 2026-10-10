"""Evaluate a complete prediction run on CPU (Phase 1+).

Refuses unless the referenced prediction run has a complete, valid manifest
from a clean checkout (citable). Re-scoring from saved raw predictions needs
no backbone or GPU.

    python tools/evaluate.py --config baseline_eval
"""

from __future__ import annotations

import csv
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anomaly_memory.data import mvtec  # noqa: E402
from anomaly_memory.data.preprocess import GeometryPolicy  # noqa: E402
from anomaly_memory.eval.evaluate import MetricSpec, evaluate_category, macro_average  # noqa: E402
from anomaly_memory.eval.metrics import METRIC_VERSION  # noqa: E402
from anomaly_memory.eval.strata import StrataSpec  # noqa: E402
from anomaly_memory.io_utils import atomic_write_json  # noqa: E402
from anomaly_memory.manifest import load_manifest  # noqa: E402
from anomaly_memory.paths import drive_dir  # noqa: E402
from anomaly_memory.runctx import RunContext, ToolSpec, run_tool  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_data import dataset_root  # noqa: E402


@dataclasses.dataclass
class Config:
    SCHEMA_VERSION = 1
    predictions_run: str  # "<tool>/<run_id>" under the Drive predictions dir
    extracted_dirname: str
    categories: list[str]
    geometry: GeometryPolicy
    metric: MetricSpec
    strata: StrataSpec
    require_clean_git: bool = True
    seed: int = 0


SPEC = ToolSpec(name="evaluate", schema=Config, tier="cpu", phase="phase1",
                science_modules=["anomaly_memory.eval.metrics", "anomaly_memory.eval.evaluate",
                                 "anomaly_memory.eval.strata", "anomaly_memory.eval.predictions",
                                 "anomaly_memory.data.preprocess"],
                durable_kind="manifests", description=__doc__)


def body(ctx: RunContext) -> dict:
    cfg: Config = ctx.cfg
    pred_dir = drive_dir("predictions") / cfg.predictions_run
    src = load_manifest(pred_dir, require_clean_git=cfg.require_clean_git)
    ctx.extra_manifest["inputs"] = {"predictions_run": cfg.predictions_run, "identity": src["identity"]["full"]}
    root = dataset_root(cfg.extracted_dirname)
    per_cat, rows = {}, []
    for cat in cfg.categories:
        recs, rep = mvtec.scan(root, [cat])
        if not rep.ok:
            raise RuntimeError(rep.errors[:5])
        res, r = evaluate_category(root, recs, pred_dir / f"{cat}.npz", cfg.geometry, cfg.metric, cfg.strata)
        per_cat[cat] = res
        rows += r
        ctx.log(f"{cat:11s} img {res['image_auroc']:.4f} pix {res['pixel_auroc']:.4f} aupro {res['au_pro']:.4f}")
    macro = {k: macro_average(per_cat, k) for k in ("image_auroc", "pixel_auroc", "au_pro")}
    out = ctx.work_dir / "metrics.json"
    atomic_write_json(out, {"metric_version": METRIC_VERSION, "per_category": per_cat, "macro": macro})
    ctx.register(out, kind="metrics")
    cp = ctx.work_dir / "per_image.csv"
    with open(cp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    ctx.register(cp, kind="table")
    return {"metric_version": METRIC_VERSION, "macro": macro}


if __name__ == "__main__":
    sys.exit(run_tool(SPEC, body))
