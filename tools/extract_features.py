"""Frozen-backbone feature extraction (Phase 1, accelerator).

BLOCKED until the Phase 0 gate and a specific CU allocation are approved.
The harness refuses before any GPU work: phase gate -> allocation covering
this config -> wall-clock guard. The body is implemented in Phase 1, after
the baseline protocol is frozen; until then it raises without computing.

    python tools/extract_features.py --config patchcore_features --resume
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anomaly_memory.data.preprocess import GeometryPolicy  # noqa: E402
from anomaly_memory.runctx import ToolSpec, phase_blocked_body, run_tool  # noqa: E402


@dataclasses.dataclass
class Config:
    SCHEMA_VERSION = 1
    extracted_dirname: str
    categories: list[str]
    backbone: str
    weights_source: str
    layers: list[str]
    geometry: GeometryPolicy
    precision: str
    batch_size: int
    chunk_images: int
    est_gpu_hours: float
    seed: int = 0


SPEC = ToolSpec(name="extract_features", schema=Config, tier="gpu", phase="phase1",
                science_modules=["anomaly_memory.features.cache", "anomaly_memory.data.preprocess"],
                durable_kind="features", est_hours=lambda c: c.est_gpu_hours, description=__doc__)

if __name__ == "__main__":
    sys.exit(run_tool(SPEC, phase_blocked_body("feature extraction")))
