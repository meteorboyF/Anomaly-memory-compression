"""Phase-gate and accelerator-allocation status; accelerator session bookkeeping.

    python tools/budget.py status
    python tools/budget.py preflight --config patchcore_features --tier gpu --phase phase1 --hours 0.5
    python tools/budget.py session-start --allocation A1   # when a GPU runtime is attached
    python tools/budget.py session-end   --allocation A1   # before disconnecting it

The guard is an approximate wall-clock safeguard, NOT a CU meter. Reconcile
against the balance shown in Colab after every batch.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anomaly_memory import budget as B  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    pf = sub.add_parser("preflight")
    pf.add_argument("--config", required=True)
    pf.add_argument("--tier", choices=["cpu", "gpu"], required=True)
    pf.add_argument("--phase", required=True)
    pf.add_argument("--hours", type=float, default=0.0)
    for name in ("session-start", "session-end"):
        s = sub.add_parser(name)
        s.add_argument("--allocation", required=True)
        s.add_argument("--balance", type=float, default=None, help="CU balance shown in Colab now")
    a = p.parse_args(argv)

    if a.cmd == "status":
        g = B.load_gates()
        print(f"gates: phase0={g.phase0_approved} phase1={g.phase1_approved} phase2={g.phase2_approved} "
              f"{g.approved_on or ''}")
        allocs = B.load_allocations()
        if not allocs:
            print("allocations: none recorded -> every accelerator job is refused")
        usage = []
        try:
            usage = B.read_usage()
        except OSError as e:
            print(f"(usage log unavailable: {e})")
        for al in allocs:
            used = B.hours_used(al.id, usage)
            print(f"  {al.id} [{al.status}] {al.gpu_type} ceiling={al.cu_ceiling} CU rate={al.rate_cu_per_hour} "
                  f"CU/h wall-limit={al.max_wall_hours} h used~{used:.2f} h configs={al.configs}")
        return 0
    if a.cmd == "preflight":
        try:
            r = B.preflight(a.tier, a.config, a.phase, a.hours)
        except B.BudgetRefused as e:
            print(f"REFUSED: {e}")
            return 3
        print(f"OK: {r.message}")
        return 0
    allocs = {x.id: x for x in B.load_allocations()}
    if a.allocation not in allocs or allocs[a.allocation].status != "approved":
        print(f"REFUSED: allocation {a.allocation!r} is not an approved allocation")
        return 3
    event = "session_start" if a.cmd == "session-start" else "session_end"
    row = B.session_event(event, a.allocation, balance_cu=a.balance)
    print(f"recorded {event} for {a.allocation} at {row['utc']}"
          + (f" (balance {a.balance} CU)" if a.balance is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
