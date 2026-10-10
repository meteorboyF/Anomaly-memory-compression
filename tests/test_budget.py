import time

import pytest

from anomaly_memory import budget as B


def gates(p0=True, p1=True, p2=False):
    return B.Gates(phase0_approved=p0, phase1_approved=p1, phase2_approved=p2)


def alloc(**kw):
    d = dict(id="A1", status="approved", purpose="pilot", phase="phase1", gpu_type="T4", cu_ceiling=10.0,
             rate_cu_per_hour=2.0, max_wall_hours=4.0, configs=["feat"], approved_on="2026-10-12")
    d.update(kw)
    a = B.Allocation(**d)
    a.validate()
    return a


def test_repo_state_blocks_everything_beyond_phase0():
    g = B.load_gates()
    assert not g.phase1_approved and not g.phase2_approved
    assert B.load_allocations() == []
    with pytest.raises(B.BudgetRefused):
        B.preflight("gpu", "patchcore_features", "phase1", 0.1)
    with pytest.raises(B.BudgetRefused):
        B.preflight("cpu", "baseline_eval", "phase1", 0.0)
    assert B.preflight("cpu", "phase0_data", "phase0", 0.0).allocation_id is None


def test_gpu_needs_covering_allocation():
    with pytest.raises(B.BudgetRefused, match="no approved"):
        B.preflight("gpu", "feat", "phase1", 0.5, gates=gates(), allocations=[], usage=[])
    with pytest.raises(B.BudgetRefused, match="no approved"):
        B.preflight("gpu", "other", "phase1", 0.5, gates=gates(), allocations=[alloc()], usage=[])
    r = B.preflight("gpu", "feat", "phase1", 0.5, gates=gates(), allocations=[alloc()], usage=[])
    assert r.allocation_id == "A1" and r.remaining_hours == pytest.approx(3.9)


def test_gate_blocks_even_with_allocation():
    with pytest.raises(B.BudgetRefused, match="not approved"):
        B.preflight("gpu", "feat", "phase1", 0.5, gates=gates(p0=False), allocations=[alloc()], usage=[])


def test_usage_and_session_time_exhaust_allocation():
    now = time.time()
    usage = [{"event": "session_start", "allocation_id": "A1", "t": now - 3.95 * 3600},
             {"event": "session_start", "allocation_id": "A1", "t": now - 60}]  # re-run must not reset
    assert B.hours_used("A1", usage, now) == pytest.approx(3.95, abs=1e-3)
    with pytest.raises(B.BudgetRefused, match="request a new allocation"):
        B.preflight("gpu", "feat", "phase1", 0.2, gates=gates(), allocations=[alloc()], usage=usage)
    jobs = [{"event": "job_end", "allocation_id": "A1", "wall_hours": 1.0}] * 2
    assert B.hours_used("A1", jobs, now) == pytest.approx(2.0)


def test_allocation_validation():
    with pytest.raises(ValueError, match="rate"):
        alloc(rate_cu_per_hour=None)
    with pytest.raises(ValueError, match="exceeds"):
        alloc(max_wall_hours=6.0)


def test_time_guard():
    g = B.TimeGuard(time.monotonic() + 1000, checkpoint_margin_s=10)
    assert not g.should_stop()
    g2 = B.TimeGuard(time.monotonic() - 1)
    assert g2.should_stop()
    with pytest.raises(B.TimeGuardExpired):
        g2.check()
    assert not B.TimeGuard(None).should_stop()
