"""Outcome-free MVTec AD profile on CPU: counts, sizes, defect areas, geometry
losses under the baseline preprocessing, exact duplicates, and the content
hash that pins the dataset for every later run.

    python tools/profile_data.py --config phase0_data
"""

from __future__ import annotations

import csv
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anomaly_memory.data import mvtec  # noqa: E402
from anomaly_memory.data.preprocess import GeometryPolicy  # noqa: E402
from anomaly_memory.data.profile import ROW_FIELDS, profile_record, summarise  # noqa: E402
from anomaly_memory.io_utils import atomic_write_json, read_json  # noqa: E402
from anomaly_memory.paths import local_root  # noqa: E402
from anomaly_memory.runctx import RunContext, ToolSpec, run_tool  # noqa: E402


@dataclasses.dataclass
class Config:
    SCHEMA_VERSION = 1
    extracted_dirname: str
    categories: list[str]
    geometry: GeometryPolicy
    connectivity: int = 8
    seed: int = 0


SPEC = ToolSpec(name="profile_data", schema=Config, tier="cpu", phase="phase0",
                science_modules=["anomaly_memory.data.profile", "anomaly_memory.data.mvtec",
                                 "anomaly_memory.data.preprocess", "anomaly_memory.eval.metrics"],
                durable_kind="manifests", description=__doc__)


def dataset_root(extracted_dirname: str) -> Path:
    marker = local_root() / "data" / f"{extracted_dirname}.extracted.json"
    if not marker.exists():
        raise FileNotFoundError(f"no verified local extraction ({marker}). Run notebook Cell 2 "
                                "(acquire_data) on this runtime first.")
    return Path(read_json(marker)["dataset_root"])


def body(ctx: RunContext) -> dict:
    cfg: Config = ctx.cfg
    root = dataset_root(cfg.extracted_dirname)
    cats = cfg.categories[:2] if ctx.smoke else cfg.categories
    records, report = mvtec.scan(root, cats)
    if not report.ok:
        raise RuntimeError(f"dataset validation failed: {report.errors[:10]}")
    ctx.log(f"profiling {len(records)} images in {len(cats)} categories under policy {cfg.geometry.name}")
    rows = []
    for i, r in enumerate(records, 1):
        rows.append(profile_record(root, r, cfg.geometry, cfg.connectivity))
        if i % 500 == 0:
            ctx.log(f"  {i}/{len(records)}")
    hashes = {}
    for r, row in zip(records, rows):
        hashes[r.relpath] = row["file_sha256"]
    for r in records:
        if r.mask_relpath:
            from anomaly_memory.io_utils import sha256_file
            hashes[r.mask_relpath] = sha256_file(root / r.mask_relpath)
    summary = summarise(rows)
    summary["dataset_hash"] = mvtec.dataset_hash(hashes)
    summary["split_hash"] = mvtec.split_hash(records)
    summary["geometry_policy"] = dataclasses.asdict(cfg.geometry)
    summary["validation_warnings"] = report.warnings
    csv_path = ctx.work_dir / "profile_per_image.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ROW_FIELDS)
        w.writeheader()
        w.writerows(rows)
    ctx.register(csv_path, kind="table")
    sp = ctx.work_dir / "profile_summary.json"
    atomic_write_json(sp, summary)
    ctx.register(sp, kind="summary")
    ip = ctx.work_dir / "dataset_index.json"
    atomic_write_json(ip, {"records": [r.as_dict() for r in records], "file_sha256": hashes,
                           "dataset_hash": summary["dataset_hash"], "split_hash": summary["split_hash"]})
    ctx.register(ip, kind="index")
    ctx.extra_manifest["dataset"] = {"name": "mvtec_ad", "dataset_hash": summary["dataset_hash"],
                                     "split_hash": summary["split_hash"]}
    t = summary["totals"]
    ctx.log(f"totals: {t}; dataset_hash {summary['dataset_hash'][:16]}; split_hash {summary['split_hash'][:16]}")
    ctx.log(f"defect area-fraction quantiles: {summary['defect_area_fraction_quantiles']}")
    ctx.log(f"erased by policy: {len(summary['erased_by_policy'])}; defects with pixels outside crop: "
            f"{summary['defects_with_pixels_outside_crop']}")
    ctx.log(f"exact duplicates: files {summary['exact_file_duplicates']['n_duplicate_groups']} groups "
            f"({summary['exact_file_duplicates']['n_cross_split_groups']} cross-split)")
    return {"totals": t, "dataset_hash": summary["dataset_hash"], "split_hash": summary["split_hash"],
            "n_erased_by_policy": len(summary["erased_by_policy"]),
            "defect_area_fraction_quantiles": summary["defect_area_fraction_quantiles"],
            "duplicates": {k: summary[k]["n_duplicate_groups"] for k in ("exact_file_duplicates",
                                                                         "exact_pixel_duplicates")},
            "cross_split_duplicates": summary["exact_pixel_duplicates"]["n_cross_split_groups"]}


if __name__ == "__main__":
    sys.exit(run_tool(SPEC, body))
