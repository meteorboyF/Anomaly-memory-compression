"""Memory-bank baseline (PatchCore-style) from cached features (Phase 1).

BLOCKED until the Phase 0 gate and a CU allocation are approved; see
extract_features.py. Writes raw predictions (image scores + anomaly maps) in
the format of ``anomaly_memory.eval.predictions`` for CPU re-scoring.

    python tools/run_baseline.py --config patchcore_baseline --resume
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anomaly_memory.runctx import ToolSpec, phase_blocked_body, run_tool  # noqa: E402


@dataclasses.dataclass
class Config:
    SCHEMA_VERSION = 1
    features_config: str
    method: str
    coreset_ratio: float
    projection_dim: int
    neighbours: int
    seeds: list[int]
    est_gpu_hours: float
    seed: int = 0


SPEC = ToolSpec(name="run_baseline", schema=Config, tier="gpu", phase="phase1",
                science_modules=["anomaly_memory.memory.accounting"], durable_kind="predictions",
                est_hours=lambda c: c.est_gpu_hours, description=__doc__)

if __name__ == "__main__":
    sys.exit(run_tool(SPEC, phase_blocked_body("memory-bank baseline")))
