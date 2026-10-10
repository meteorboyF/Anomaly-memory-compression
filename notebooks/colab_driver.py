"""Thin Colab driver, exec'd into the notebook by Cell 1 (and again by refresh_code).

It defines wrapper functions ONLY. Every one of them runs a fresh Python
subprocess (``PYTHONPATH=src``) so no research module is ever imported into
the notebook kernel: pulling new code from GitHub takes effect on the next
``run()`` without restarting the kernel.

Expected globals set by Cell 1: REPO_DIR, BRANCH, COMMIT.
"""

import datetime as _dt
import json as _json
import os as _os
import shutil as _shutil
import subprocess as _sp
import sys as _sys

_STATE = _os.environ.get("AMC_STATE_DIR", "/content/amc_state")
_LOCAL_LOGS = _os.path.join(_os.environ.get("AMC_LOCAL_ROOT", "/content/amc_local"), "logs")
_EXIT_HELP = {
    1: "the tool failed. Copy the traceback above into chat; after the fix is pushed, run refresh_code() and "
       "re-run this cell (add resume=True only if the message says the identity is unchanged).",
    2: "verification found incomplete or invalid artifacts (listed above). They are never treated as complete.",
    3: "REFUSED by a safeguard (phase gate, CU allocation, dirty checkout, or active run). Nothing was "
       "computed. Read the reason above.",
    4: "config error (unknown/missing key or wrong type). Fix the YAML in configs/, push, refresh_code().",
}


def _env():
    env = dict(_os.environ)
    env["PYTHONPATH"] = _os.path.join(REPO_DIR, "src")  # noqa: F821
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _sha():
    return _sp.run(["git", "rev-parse", "HEAD"], cwd=REPO_DIR, capture_output=True, text=True).stdout.strip()  # noqa: F821


def _stream(cmd, log_name):
    """Run ``cmd`` in a fresh process, stream output, tee to a log, return exit code."""
    _os.makedirs(_LOCAL_LOGS, exist_ok=True)
    _os.makedirs(_STATE, exist_ok=True)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = _os.path.join(_LOCAL_LOGS, f"{stamp}_{log_name}.log")
    sha = _sha()
    header = f"# {stamp} sha={sha} cmd={' '.join(cmd)}\n"
    print(header.strip(), flush=True)
    proc = _sp.Popen(cmd, cwd=REPO_DIR, env=_env(), stdout=_sp.PIPE, stderr=_sp.STDOUT, text=True,  # noqa: F821
                     bufsize=1)
    with open(_os.path.join(_STATE, "active_run.json"), "w") as f:
        _json.dump({"pid": proc.pid, "tool": log_name, "sha": sha, "started": stamp}, f)
    try:
        with open(log_path, "w") as log:
            log.write(header)
            for line in proc.stdout:
                print(line, end="", flush=True)
                log.write(line)
        code = proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except _sp.TimeoutExpired:
            proc.kill()
        print("\n[driver] interrupted; subprocess stopped. Partial work is never marked complete.")
        code = 130
    finally:
        try:
            _os.remove(_os.path.join(_STATE, "active_run.json"))
        except OSError:
            pass
    drive_logs = _os.path.join(_os.environ.get("AMC_DRIVE_ROOT", ""), "artifacts", "logs")
    if _os.path.isdir(_os.path.dirname(drive_logs)):
        try:
            _os.makedirs(drive_logs, exist_ok=True)
            tmp = _os.path.join(drive_logs, "." + _os.path.basename(log_path) + ".tmp")
            _shutil.copyfile(log_path, tmp)
            _os.replace(tmp, _os.path.join(drive_logs, _os.path.basename(log_path)))
        except OSError as e:
            print(f"[driver] WARNING: could not copy log to Drive ({e}); local copy: {log_path}")
    return code, log_path


def _check(code, log_path, what):
    if code == 0:
        print(f"[driver] {what}: OK (log: {log_path})")
        return
    raise RuntimeError(f"{what} exited with code {code}: {_EXIT_HELP.get(code, 'see output above')} "
                       f"(log: {log_path})")


def run(tool, config, resume=False, smoke=False, force=False, extra=()):
    """Run tools/<tool>.py --config <config> in a fresh subprocess."""
    cmd = [_sys.executable, _os.path.join(REPO_DIR, "tools", f"{tool}.py"), "--config", config]  # noqa: F821
    cmd += (["--resume"] if resume else []) + (["--smoke"] if smoke else []) + (["--force"] if force else [])
    cmd += list(extra)
    code, log = _stream(cmd, f"{tool}_{config}{'_smoke' if smoke else ''}")
    _check(code, log, f"{tool} --config {config}")


def ctl(*args):
    code, log = _stream([_sys.executable, _os.path.join(REPO_DIR, "tools", "colab_ctl.py"), *args],  # noqa: F821
                        "ctl_" + args[0])
    _check(code, log, "colab_ctl " + " ".join(args))


def budget(*args):
    code, log = _stream([_sys.executable, _os.path.join(REPO_DIR, "tools", "budget.py"), *args],  # noqa: F821
                        "budget_" + args[0])
    _check(code, log, "budget " + " ".join(args))


def install_deps(tier="cpu"):
    ctl("deps", "--tier", tier)


def refresh_code():
    """Fetch and fast-forward the selected branch/commit; reload this driver."""
    args = ["refresh", "--branch", BRANCH] + (["--commit", COMMIT] if COMMIT else [])  # noqa: F821
    ctl(*args)
    with open(_os.path.join(REPO_DIR, "notebooks", "colab_driver.py")) as f:  # noqa: F821
        exec(compile(f.read(), "colab_driver.py", "exec"), globals())
    print(f"[driver] code at {_sha()}")


def status():
    ctl("status")


def verify_artifacts():
    ctl("verify-artifacts")


def hardware():
    gpu = _sp.run(["bash", "-lc", "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null"],
                  capture_output=True, text=True).stdout.strip()
    disk = _shutil.disk_usage("/content")
    with open("/proc/meminfo") as f:
        mem = int(f.readline().split()[1]) / 1024 ** 2
    print(f"[hardware] GPU: {gpu or 'none (CPU runtime)'} | RAM {mem:.1f} GB | CPUs {_os.cpu_count()} | "
          f"local disk free {disk.free / 1024 ** 3:.1f} GB of {disk.total / 1024 ** 3:.1f} GB")
    return bool(gpu)


def finish_accelerator_batch(allocation_id, balance_now=None):
    """Verify every artifact, close the accelerator session, then remind to shut down.
    Raises (and prints nothing reassuring) if verification fails."""
    verify_artifacts()
    budget("session-end", "--allocation", allocation_id,
           *(["--balance", str(balance_now)] if balance_now is not None else []))
    print("Results saved and verified. Disconnect/delete the accelerator runtime now if no further GPU work is "
          "planned.\n  Colab menu: Runtime > Disconnect and delete runtime (then confirm). Ending a Python "
          "subprocess does NOT release the runtime; idle attached GPUs keep consuming compute units.")
