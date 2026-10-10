"""Phase gates, accelerator allocations, and the approximate runtime guard.

Nothing here meters Colab compute units. Colab does not expose a CU meter to
code, so spending is controlled indirectly:

* ``configs/control/gates.yaml`` records which phases the researcher approved.
* ``configs/control/allocations.yaml`` records each approved accelerator batch
  (CU ceiling, GPU type, the CU/hour rate shown in the session, and a
  conservative wall-clock limit derived from them).
* Every accelerator job runs ``preflight`` first. It refuses unless the phase
  is approved, an open allocation explicitly covers the config, and the
  logged accelerator wall-clock (including idle session time since the
  accelerator session was opened) leaves room for the job's estimate.
* ``TimeGuard`` lets long jobs checkpoint and stop before the wall-clock
  limit. It is an approximate spending safeguard, not an exact CU meter.

Allocations and gate approvals are edited only when the researcher approves
them in chat; tools never create or widen them.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path
from typing import Literal

import yaml

from .config import from_dict
from .manifest import utcnow
from .paths import configs_dir, drive_dir

Tier = Literal["cpu", "gpu"]


class BudgetRefused(RuntimeError):
    pass


class TimeGuardExpired(RuntimeError):
    pass


@dataclasses.dataclass
class Gates:
    phase0_approved: bool
    phase1_approved: bool
    phase2_approved: bool
    approved_on: dict[str, str] = dataclasses.field(default_factory=dict)
    notes: str = ""


@dataclasses.dataclass
class Allocation:
    id: str
    status: Literal["proposed", "approved", "closed"]
    purpose: str
    phase: Literal["phase1", "phase2"]
    gpu_type: str
    cu_ceiling: float
    # CU/hour as displayed in the researcher's Colab session; None = unknown,
    # in which case the allocation cannot be approved (no invented conversion).
    rate_cu_per_hour: float | None
    max_wall_hours: float  # conservative: below cu_ceiling / rate, incl. setup + idle
    configs: list[str]
    approved_on: str | None = None
    start_balance_cu: float | None = None
    end_balance_cu: float | None = None
    notes: str = ""

    def validate(self) -> None:
        if self.status == "approved":
            if self.rate_cu_per_hour is None or self.rate_cu_per_hour <= 0:
                raise ValueError(f"allocation {self.id}: approved allocations need the session's CU/hour rate")
            if self.max_wall_hours * self.rate_cu_per_hour > self.cu_ceiling + 1e-9:
                raise ValueError(f"allocation {self.id}: max_wall_hours x rate exceeds the CU ceiling")
            if not self.approved_on:
                raise ValueError(f"allocation {self.id}: approved allocations need approved_on")


@dataclasses.dataclass
class AllocationFile:
    allocations: list[Allocation]


def load_gates(path: Path | None = None) -> Gates:
    path = path or configs_dir() / "control" / "gates.yaml"
    with open(path, encoding="utf-8") as f:
        return from_dict(Gates, yaml.safe_load(f), where=str(path))


def load_allocations(path: Path | None = None) -> list[Allocation]:
    path = path or configs_dir() / "control" / "allocations.yaml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {"allocations": []}
    allocs = from_dict(AllocationFile, raw, where=str(path)).allocations
    ids = [a.id for a in allocs]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate allocation ids")
    return allocs


def usage_log_path() -> Path:
    return drive_dir("logs") / "accelerator_usage.jsonl"


def read_usage(path: Path | None = None) -> list[dict]:
    path = path or usage_log_path()
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_usage(row: dict, path: Path | None = None) -> None:
    path = path or usage_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
        f.flush()


def hours_used(allocation_id: str, rows: list[dict], now: float | None = None) -> float:
    """Approximate accelerator wall-hours charged to an allocation.

    Each accelerator session is opened with a ``session_start`` row and closed
    with ``session_end``. An open session counts up to ``now``: the runtime
    bills while attached, whether or not a job is running. Job rows are
    summed separately and the larger of the two totals is returned.
    """
    now = time.time() if now is None else now
    sessions = 0.0
    jobs = 0.0
    open_start = None
    for r in rows:
        if r.get("allocation_id") != allocation_id:
            continue
        ev = r.get("event")
        if ev == "session_start":
            if open_start is None:  # a repeated start (cell re-run) must not reset the clock
                open_start = r["t"]
        elif ev == "session_end" and open_start is not None:
            sessions += (r["t"] - open_start) / 3600
            open_start = None
        elif ev == "job_end":
            jobs += r.get("wall_hours", 0.0)
    if open_start is not None:
        sessions += (now - open_start) / 3600
    return max(sessions, jobs)


@dataclasses.dataclass
class Preflight:
    allocation_id: str | None
    remaining_hours: float | None
    deadline_monotonic: float | None
    message: str


def preflight(tier: Tier, config_name: str, phase: str, est_hours: float, *,
              gates: Gates | None = None, allocations: list[Allocation] | None = None,
              usage: list[dict] | None = None, safety_margin_hours: float = 0.1,
              smoke: bool = False) -> Preflight:
    """Refuse unless this job is allowed to run now. CPU jobs only need their phase gate."""
    gates = gates or load_gates()
    gate_ok = {"phase0": True, "phase1": gates.phase1_approved and gates.phase0_approved,
               "phase2": gates.phase2_approved and gates.phase1_approved}
    if phase not in gate_ok:
        raise BudgetRefused(f"unknown phase {phase!r}")
    if not gate_ok[phase]:
        raise BudgetRefused(
            f"{phase} is not approved in configs/control/gates.yaml. Phase 1/2 work is blocked until "
            "the researcher approves the Phase 0 gate in chat and the gate file is updated.")
    if tier == "cpu":
        return Preflight(None, None, None, f"CPU job permitted ({phase} gate open)")
    allocations = load_allocations() if allocations is None else allocations
    usage = read_usage() if usage is None else usage
    covering = [a for a in allocations if a.status == "approved" and config_name in a.configs]
    if not covering:
        raise BudgetRefused(
            f"no approved accelerator allocation covers config {config_name!r}. Ask the researcher for a "
            "specific CU allocation; it is recorded in configs/control/allocations.yaml only after approval.")
    if len(covering) > 1:
        raise BudgetRefused(f"config {config_name!r} is covered by several approved allocations "
                            f"{[a.id for a in covering]}; close all but one")
    a = covering[0]
    used = hours_used(a.id, usage)
    remaining = a.max_wall_hours - used - safety_margin_hours
    need = 0.0 if smoke else est_hours
    if remaining <= 0 or need > remaining:
        raise BudgetRefused(
            f"allocation {a.id}: ~{used:.2f} h used of {a.max_wall_hours:.2f} h wall limit "
            f"(CU ceiling {a.cu_ceiling}); job needs ~{need:.2f} h, {max(remaining, 0):.2f} h left. "
            "Stop, reconcile the CU balance, and request a new allocation.")
    deadline = time.monotonic() + remaining * 3600
    return Preflight(a.id, remaining, deadline,
                     f"allocation {a.id} ({a.gpu_type}): {remaining:.2f} h of wall-clock guard remaining "
                     "(approximate; not a CU meter)")


class TimeGuard:
    """Approximate wall-clock guard. Long loops call ``should_stop`` between
    work units, checkpoint, and exit cleanly before the allocation limit."""

    def __init__(self, deadline_monotonic: float | None, checkpoint_margin_s: float = 300.0):
        self.deadline = deadline_monotonic
        self.margin = checkpoint_margin_s

    def remaining_s(self) -> float:
        return float("inf") if self.deadline is None else self.deadline - time.monotonic()

    def should_stop(self) -> bool:
        return self.remaining_s() <= self.margin

    def check(self) -> None:
        if self.remaining_s() <= 0:
            raise TimeGuardExpired("allocation wall-clock guard reached; stop and reconcile CU spend")


def session_event(event: Literal["session_start", "session_end", "job_end"], allocation_id: str,
                  **extra) -> dict:
    row = {"event": event, "allocation_id": allocation_id, "t": time.time(), "utc": utcnow(), **extra}
    append_usage(row)
    return row
