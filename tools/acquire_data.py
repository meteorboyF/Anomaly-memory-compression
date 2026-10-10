"""Download/verify MVTec AD into Google Drive and stage it on local disk (CPU).

    python tools/acquire_data.py --config acquire_mvtec_ad

Idempotent: skips verified downloads and verified local extraction. On
failure prints exact manual-upload instructions; a manually uploaded archive
is detected and verified automatically on the next run.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anomaly_memory.data import acquire as A  # noqa: E402
from anomaly_memory.data.mvtec import CATEGORIES  # noqa: E402
from anomaly_memory.io_utils import atomic_write_json  # noqa: E402
from anomaly_memory.paths import drive_dir, local_root  # noqa: E402
from anomaly_memory.runctx import RunContext, ToolSpec, run_tool  # noqa: E402


@dataclasses.dataclass
class Config:
    SCHEMA_VERSION = 1
    dataset: str
    downloads_page: str
    archive_name: str
    fallback_url: str
    expected_bytes: int | None
    extracted_bytes_estimate: int
    publisher_sha256: str | None
    publisher_md5: str | None
    extracted_dirname: str
    categories: list[str]
    expected_counts: dict[str, dict[str, int]] | None
    max_retries: int = 5
    timeout_s: float = 60.0
    seed: int = 0

    def validate(self) -> None:
        if self.dataset != "mvtec_ad":
            raise ValueError("only original MVTec AD is supported")
        bad = sorted(set(self.categories) - set(CATEGORIES))
        if bad:
            raise ValueError(f"unknown categories {bad}")
        if not 1 <= self.max_retries <= 10:
            raise ValueError("max_retries must be within 1..10 (bounded retries)")


SPEC = ToolSpec(name="acquire_data", schema=Config, tier="cpu", phase="phase0",
                science_modules=["anomaly_memory.data.acquire", "anomaly_memory.data.mvtec"],
                durable_kind="manifests", skip_if_complete=False, description=__doc__)


def plan_from(cfg: Config) -> A.Plan:
    return A.Plan(archive_name=cfg.archive_name, downloads_page=cfg.downloads_page, fallback_url=cfg.fallback_url,
                  expected_bytes=cfg.expected_bytes, extracted_bytes_estimate=cfg.extracted_bytes_estimate,
                  publisher_sha256=cfg.publisher_sha256, publisher_md5=cfg.publisher_md5,
                  drive_archive_dir=drive_dir("archives"), local_root=local_root(),
                  extracted_dirname=cfg.extracted_dirname, categories=cfg.categories,
                  expected_counts=cfg.expected_counts, max_retries=cfg.max_retries, timeout_s=cfg.timeout_s)


def body(ctx: RunContext) -> dict:
    plan = plan_from(ctx.cfg)
    try:
        result = A.acquire(plan, ctx.log)
    except A.AcquireError as e:
        print("\n" + "=" * 78 + f"\nACQUISITION FAILED: {e}\n" + "=" * 78, flush=True)
        print(A.manual_instructions(plan), flush=True)
        raise
    out = ctx.work_dir / "acquisition_result.json"
    atomic_write_json(out, result)
    ctx.register(out, kind="record")
    print("\n" + "=" * 78)
    print(f"DATASET READY. Archive on Drive (verified): {plan.drive_archive}")
    print(f"Local working copy (verified): {result['dataset_root']}")
    print(f"archive: {result['archive_status']}; extraction: {result['extraction_status']}")
    print("=" * 78, flush=True)
    m = result["drive_marker"]
    return {"archive_status": result["archive_status"], "extraction_status": result["extraction_status"],
            "dataset_root": result["dataset_root"], "archive_sha256_calculated_by_us": m["sha256_calculated_by_us"],
            "archive_bytes": m["bytes"], "publisher_checksum": m.get("publisher_checksum"),
            "split_hash": result["extraction"]["split_hash"], "counts": result["extraction"]["counts"]}


if __name__ == "__main__":
    sys.exit(run_tool(SPEC, body))
