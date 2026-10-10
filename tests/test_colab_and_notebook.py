"""Colab control (refresh safety, deps fingerprint), driver subprocess wrapper, notebook hygiene."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO

CTL = REPO / "tools" / "colab_ctl.py"


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def clone_pair(tmp_path):
    """origin (bare) <- work (pushes) ; colab (clone under test)."""
    bare = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    work = tmp_path / "work"
    git(tmp_path, "clone", "-q", str(bare), str(work))
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        git(work, "config", k, v)
    (work / "requirements-cpu.txt").write_text("numpy\n")
    (work / "a.py").write_text("x = 1\n")
    git(work, "add", ".")
    git(work, "commit", "-qm", "init")
    git(work, "push", "-q", "origin", "main")
    colab = tmp_path / "colab"
    git(tmp_path, "clone", "-q", str(bare), str(colab))
    return work, colab, tmp_path


def ctl(colab, state, *args):
    env = {**os.environ, "AMC_REPO_DIR": str(colab), "AMC_STATE_DIR": str(state)}
    return subprocess.run([sys.executable, str(CTL), *args], env=env, capture_output=True, text=True)


def test_refresh_fast_forwards_and_reports_deps(clone_pair):
    work, colab, tmp = clone_pair
    (work / "requirements-cpu.txt").write_text("numpy\nscipy\n")
    git(work, "commit", "-qam", "deps")
    git(work, "push", "-q", "origin", "main")
    r = ctl(colab, tmp / "state", "refresh", "--branch", "main")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DEPENDENCY FILES CHANGED" in r.stdout
    assert git(colab, "rev-parse", "HEAD") == git(work, "rev-parse", "HEAD")


def test_refresh_refuses_dirty_checkout(clone_pair):
    _, colab, tmp = clone_pair
    (colab / "a.py").write_text("x = 'local edit'\n")
    r = ctl(colab, tmp / "state", "refresh", "--branch", "main")
    assert r.returncode == 3 and "local modifications" in r.stdout
    assert (colab / "a.py").read_text() == "x = 'local edit'\n"


def test_refresh_refuses_during_active_run(clone_pair):
    _, colab, tmp = clone_pair
    state = tmp / "state"
    state.mkdir()
    (state / "active_run.json").write_text(json.dumps({"pid": os.getpid(), "tool": "x"}))
    r = ctl(colab, state, "refresh", "--branch", "main")
    assert r.returncode == 3 and "still active" in r.stdout
    (state / "active_run.json").write_text(json.dumps({"pid": 2 ** 22 + 12345, "tool": "x"}))  # stale
    assert ctl(colab, state, "refresh", "--branch", "main").returncode == 0


def test_deps_fingerprint_skips_when_unchanged(clone_pair):
    _, colab, tmp = clone_pair
    state = tmp / "state"
    state.mkdir()
    sys.path.insert(0, str(REPO / "tools"))
    os.environ["AMC_REPO_DIR"] = str(colab)
    try:
        import importlib
        import colab_ctl
        importlib.reload(colab_ctl)
        (state / "deps_cpu.json").write_text(json.dumps(colab_ctl.fingerprint("cpu")))
    finally:
        del os.environ["AMC_REPO_DIR"]
    r = ctl(colab, state, "deps", "--tier", "cpu")
    assert r.returncode == 0 and "unchanged" in r.stdout


def test_driver_runs_fresh_subprocess_and_surfaces_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("AMC_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("AMC_LOCAL_ROOT", str(tmp_path / "local"))
    monkeypatch.setenv("AMC_DRIVE_ROOT", str(tmp_path / "drive"))
    ns = {"REPO_DIR": str(REPO), "BRANCH": "main", "COMMIT": ""}
    exec(compile((REPO / "notebooks" / "colab_driver.py").read_text(), "colab_driver.py", "exec"), ns)
    with pytest.raises(RuntimeError, match="REFUSED by a safeguard"):
        ns["run"]("extract_features", config="patchcore_features", extra=["--out-root", str(tmp_path / "o")])
    with pytest.raises(RuntimeError, match="config error"):
        ns["run"]("metric_selfcheck", config="does_not_exist")
    logs = list((tmp_path / "local" / "logs").glob("*.log"))
    assert logs and all(l.read_text().startswith("# ") for l in logs)
    assert not (tmp_path / "state" / "active_run.json").exists()
    # the driver namespace holds only wrappers, never research modules
    assert not any(getattr(v, "__name__", "").startswith("anomaly_memory") for v in ns.values())


def test_notebook_is_clean_and_ordered():
    assert subprocess.run([sys.executable, str(REPO / "tools" / "build_notebook.py"), "--check"]).returncode == 0
    nb = json.loads((REPO / "notebooks" / "runner.ipynb").read_text())
    code = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
    assert all(c["outputs"] == [] and c["execution_count"] is None for c in nb["cells"] if c["cell_type"] == "code")
    assert "drive.mount" in code[0] and "refresh_code()" in code[0] and "install_deps(\"cpu\")" in code[0]
    assert 'run("acquire_data"' in code[1]  # dataset cell directly after setup
    for c in code:
        assert "import anomaly_memory" not in c and "from anomaly_memory" not in c
    gpu_cells = [c for c in code if "extract_features" in c or "run_baseline" in c]
    assert gpu_cells and all("ENABLE_ACCELERATOR" in c for c in gpu_cells)
    assert "ENABLE_ACCELERATOR = False" in "".join(code)
    driver = (REPO / "notebooks" / "colab_driver.py").read_text()
    assert "anomaly_memory" not in driver.replace("REPO_DIR", "")
