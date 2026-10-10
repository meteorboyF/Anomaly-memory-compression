"""Code, environment and hardware provenance recorded in every manifest."""

from __future__ import annotations

import importlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .io_utils import sha256_bytes
from .paths import repo_root

TRACKED_PACKAGES = ("numpy", "scipy", "PIL", "yaml", "sklearn", "matplotlib",
                    "torch", "torchvision", "timm", "faiss")


def _git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd or repo_root(), check=True,
                          capture_output=True, text=True).stdout.strip()


def git_info(cwd: Path | None = None) -> dict:
    """Return sha, branch and dirtiness. ``sha`` is 'unknown' outside a checkout."""
    try:
        sha = _git("rev-parse", "HEAD", cwd=cwd)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"sha": "unknown", "dirty": True, "branch": "unknown", "dirty_files": []}
    status = _git("status", "--porcelain", "--untracked-files=no", cwd=cwd)
    try:
        branch = _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
    except subprocess.CalledProcessError:
        branch = "unknown"
    dirty_files = [line[3:] for line in status.splitlines() if line.strip()]
    return {"sha": sha, "dirty": bool(dirty_files), "branch": branch, "dirty_files": dirty_files}


def package_versions(names=TRACKED_PACKAGES, import_missing: bool = False) -> dict:
    """Versions of tracked packages. By default only already-imported modules
    are inspected, so recording provenance never imports torch by accident."""
    out = {}
    for n in names:
        mod = sys.modules.get(n)
        if mod is None and import_missing:
            try:
                mod = importlib.import_module(n)
            except Exception:
                mod = None
        if mod is not None:
            out[n] = getattr(mod, "__version__", "unknown")
    return out


def pip_freeze_hash() -> dict:
    try:
        out = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True,
                             text=True, timeout=120).stdout
    except Exception as e:  # pragma: no cover - environment specific
        return {"sha256": None, "error": str(e)}
    return {"sha256": sha256_bytes(out.encode()), "n_packages": len(out.splitlines()), "text": out}


def gpu_info() -> list[dict]:
    if shutil.which("nvidia-smi") is None:
        return []
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return []
    gpus = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3:
            gpus.append({"name": parts[0], "memory_total": parts[1], "driver": parts[2]})
    return gpus


def mem_total_bytes() -> int | None:
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        return None
    return None


def environment_info() -> dict:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": package_versions(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }


def hardware_info() -> dict:
    return {"cpu_count": os.cpu_count(), "mem_total_bytes": mem_total_bytes(), "gpus": gpu_info()}
