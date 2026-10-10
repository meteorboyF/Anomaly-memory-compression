"""Colab control CLI used by notebooks/colab_driver.py (always as a subprocess).

    python tools/colab_ctl.py deps --tier cpu|gpu
    python tools/colab_ctl.py refresh --branch main [--commit SHA]
    python tools/colab_ctl.py status
    python tools/colab_ctl.py verify-artifacts

Stdlib + this repo only, so it works before any dependency is installed.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(os.environ.get("AMC_REPO_DIR") or Path(__file__).resolve().parents[1])
STATE = Path(os.environ.get("AMC_STATE_DIR", "/content/amc_state"))
ACTIVE = STATE / "active_run.json"
REQ = {"cpu": REPO / "requirements-cpu.txt", "gpu": REPO / "requirements-gpu.txt"}
EXIT_REFUSED = 3


def _git_auth() -> list[str]:
    tok = os.environ.get("GH_TOKEN")
    if not tok:
        return []
    basic = base64.b64encode(f"x-access-token:{tok}".encode()).decode()
    return ["-c", f"http.extraHeader=Authorization: Basic {basic}"]


def git(*args: str, auth: bool = False, check: bool = True) -> str:
    cmd = ["git", *(_git_auth() if auth else []), *args]
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if check and r.returncode:
        msg = r.stderr.strip().replace(os.environ.get("GH_TOKEN", "\0"), "***")
        raise RuntimeError(f"git {args[0]} failed: {msg}")
    return r.stdout.strip()


def fingerprint(tier: str) -> dict:
    req = REQ[tier]
    text = req.read_text() if req.exists() else ""
    fp = hashlib.sha256(f"{tier}|{sys.version.split()[0]}|{text}".encode()).hexdigest()
    return {"tier": tier, "python": sys.version.split()[0], "requirements_sha256": fp, "requirements": text}


def cmd_deps(tier: str) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    marker = STATE / f"deps_{tier}.json"
    fp = fingerprint(tier)
    if marker.exists():
        old = json.loads(marker.read_text())
        if old["requirements_sha256"] == fp["requirements_sha256"]:
            print(f"[deps:{tier}] environment fingerprint unchanged ({fp['requirements_sha256'][:12]}); "
                  "skipping install")
            return 0
        print(f"[deps:{tier}] DEPENDENCY CHANGE detected (requirements-{tier}.txt or Python changed). "
              "Installing. If a compiled package (torch, faiss, numpy, scipy) changed version, use "
              "Runtime > Restart session afterwards, then re-run Cell 1.")
    print(f"[deps:{tier}] installing {REQ[tier].name} ...", flush=True)
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(REQ[tier])])
    if r.returncode:
        print(f"[deps:{tier}] pip install failed (exit {r.returncode})")
        return r.returncode
    tmp = marker.with_suffix(".tmp")
    tmp.write_text(json.dumps(fp, indent=2))
    tmp.replace(marker)
    print(f"[deps:{tier}] done; fingerprint {fp['requirements_sha256'][:12]} recorded")
    return 0


def active_run() -> dict | None:
    if not ACTIVE.exists():
        return None
    info = json.loads(ACTIVE.read_text())
    try:
        os.kill(int(info["pid"]), 0)
    except (OSError, ValueError):
        ACTIVE.unlink(missing_ok=True)  # stale lock from a finished/killed process
        return None
    return info


def cmd_refresh(branch: str, commit: str | None) -> int:
    run = active_run()
    if run:
        print(f"[refresh] REFUSED: experiment subprocess still active (pid {run['pid']}, {run['tool']}). "
              "Wait for it or stop it first.")
        return EXIT_REFUSED
    dirty = git("status", "--porcelain", "--untracked-files=no")
    if dirty:
        print("[refresh] REFUSED: the Colab checkout has local modifications; refusing to overwrite them:\n"
              + dirty + "\nIf they are disposable: `git -C /content/Anomaly-memory-compression stash` and retry.")
        return EXIT_REFUSED
    old = git("rev-parse", "HEAD")
    git("fetch", "--prune", "origin", auth=True)
    if commit:
        git("checkout", "--detach", commit)
    else:
        current = git("rev-parse", "--abbrev-ref", "HEAD")
        if current != branch:
            git("checkout", "-B", branch, f"origin/{branch}")
        ahead = git("rev-list", "--count", f"origin/{branch}..HEAD")
        if ahead != "0":
            print(f"[refresh] REFUSED: local branch has {ahead} commit(s) not on origin; not discarding them.")
            return EXIT_REFUSED
        git("merge", "--ff-only", f"origin/{branch}")
    new = git("rev-parse", "HEAD")
    if old == new:
        print(f"[refresh] already up to date at {new}")
        return 0
    changed = git("diff", "--name-only", old, new).splitlines()
    print(f"[refresh] {old[:12]} -> {new}  ({len(changed)} files changed)")
    for f in changed[:40]:
        print(f"    {f}")
    dep = [f for f in changed if f.startswith("requirements")]
    if dep:
        print(f"[refresh] DEPENDENCY FILES CHANGED: {dep}. Run install_deps('cpu') (and 'gpu' if used).")
    sci = [f for f in changed if f.startswith("src/anomaly_memory/")]
    if sci:
        print("[refresh] package code changed; tools whose scientific modules changed will get a NEW "
              "experiment identity (old results are kept separately, never mixed).")
    if "notebooks/colab_driver.py" in changed:
        print("[refresh] the notebook driver changed; refresh_code() reloads it automatically.")
    return 0


def cmd_status() -> int:
    sha = git("rev-parse", "HEAD", check=False)
    dirty = git("status", "--porcelain", "--untracked-files=no", check=False)
    print(f"repo {REPO} @ {sha}{' DIRTY' if dirty else ''}")
    for tier in ("cpu", "gpu"):
        m = STATE / f"deps_{tier}.json"
        state = json.loads(m.read_text())["requirements_sha256"][:12] if m.exists() else "not installed"
        cur = fingerprint(tier)["requirements_sha256"][:12]
        flag = "" if state in ("not installed", cur) else "  <-- CHANGED since install"
        print(f"deps[{tier}]: installed={state} current={cur}{flag}")
    run = active_run()
    print(f"active run: {run or 'none'}")
    drive = Path(os.environ.get("AMC_DRIVE_ROOT", "/content/drive/MyDrive/Research/Anomaly-memory-compression"))
    print(f"drive root: {drive} ({'present' if drive.exists() else 'MISSING'})")
    marker = drive / "datasets/archives/mvtec_anomaly_detection.tar.xz.verified.json"
    print(f"dataset archive marker: {'VERIFIED' if marker.exists() else 'absent'}")
    local = Path(os.environ.get("AMC_LOCAL_ROOT", "/content/amc_local")) / "data/mvtec_ad.extracted.json"
    print(f"local extraction marker: {'VERIFIED' if local.exists() else 'absent (run Cell 2 on this runtime)'}")
    r = subprocess.run([sys.executable, str(REPO / "tools/budget.py"), "status"], cwd=REPO,
                       env={**os.environ, "PYTHONPATH": str(REPO / "src")})
    return r.returncode


def cmd_verify() -> int:
    sys.path.insert(0, str(REPO / "src"))
    from anomaly_memory.manifest import ManifestError, load_manifest
    drive = Path(os.environ.get("AMC_DRIVE_ROOT", "/content/drive/MyDrive/Research/Anomaly-memory-compression"))
    found = sorted(p.parent for p in (drive / "artifacts").rglob("manifest.json")) if drive.exists() else []
    ok = bad = 0
    for d in found:
        if "_partial" in d.parts:
            continue
        try:
            m = load_manifest(d)
            ok += 1
            print(f"  OK        {d.relative_to(drive)}  sha={m['git']['sha'][:10]}{' dirty' if m['git']['dirty'] else ''}")
        except ManifestError as e:
            bad += 1
            print(f"  INCOMPLETE/INVALID {d.relative_to(drive)}: {e}")
    print(f"verified {ok} complete run(s); {bad} incomplete/invalid (never used as complete)")
    return 0 if bad == 0 else 2


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("deps")
    d.add_argument("--tier", choices=["cpu", "gpu"], required=True)
    r = sub.add_parser("refresh")
    r.add_argument("--branch", default="main")
    r.add_argument("--commit", default=None)
    sub.add_parser("status")
    sub.add_parser("verify-artifacts")
    a = p.parse_args(argv)
    try:
        if a.cmd == "deps":
            return cmd_deps(a.tier)
        if a.cmd == "refresh":
            return cmd_refresh(a.branch, a.commit or None)
        if a.cmd == "status":
            return cmd_status()
        return cmd_verify()
    except RuntimeError as e:
        print(f"[{a.cmd}] ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
