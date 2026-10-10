"""Filesystem layout: repository, durable Drive root, and fast local work area.

Durable artifacts live under the Drive root (configurable with
``AMC_DRIVE_ROOT``). Active data and high-frequency writes live on local disk
(``AMC_LOCAL_ROOT``) and are copied atomically to Drive when complete.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DRIVE_ROOT = "/content/drive/MyDrive/Research/Anomaly-memory-compression"
COLAB_LOCAL_ROOT = "/content/amc_local"

# Subfolders of the Drive root. Keys are stable identifiers used in configs.
DRIVE_SUBDIRS = {
    "archives": "datasets/archives",
    "features": "artifacts/features",
    "memory_banks": "artifacts/memory_banks",
    "checkpoints": "artifacts/checkpoints",
    "predictions": "artifacts/predictions",
    "manifests": "artifacts/manifests",
    "logs": "artifacts/logs",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def configs_dir() -> Path:
    return repo_root() / "configs"


def drive_root() -> Path:
    return Path(os.environ.get("AMC_DRIVE_ROOT", DEFAULT_DRIVE_ROOT))


def local_root() -> Path:
    env = os.environ.get("AMC_LOCAL_ROOT")
    if env:
        return Path(env)
    if Path("/content").is_dir():
        return Path(COLAB_LOCAL_ROOT)
    return Path.home() / ".cache" / "anomaly_memory"


def drive_dir(key: str) -> Path:
    if key not in DRIVE_SUBDIRS:
        raise KeyError(f"unknown Drive subdir {key!r}; known: {sorted(DRIVE_SUBDIRS)}")
    return drive_root() / DRIVE_SUBDIRS[key]


def local_data_dir() -> Path:
    """Where the dataset is extracted for active work (never Drive)."""
    return local_root() / "data"


def is_drive_mounted() -> bool:
    return Path("/content/drive/MyDrive").is_dir()
