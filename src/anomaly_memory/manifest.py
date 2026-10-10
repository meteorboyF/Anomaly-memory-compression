"""Run manifests: written for every run, validated on every load.

A manifest is a JSON file next to a run's outputs. It is first written with
``complete: false`` when the run starts and rewritten with ``complete: true``
as the LAST key, only after every listed artifact has been written and hashed.
Loading re-validates and refuses (raises) with a printed reason; it never
warns-and-continues.
"""

from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path
from typing import Any

from .io_utils import atomic_write_json, read_json, sha256_file

MANIFEST_NAME = "manifest.json"
MANIFEST_VERSION = 1

REQUIRED_KEYS = ("manifest_version", "tool", "run_id", "identity", "config", "git",
                 "seed", "environment", "hardware", "started_utc", "artifacts", "complete")


class ManifestError(RuntimeError):
    pass


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def artifact_entry(run_dir: Path, path: Path, kind: str = "file") -> dict:
    path = Path(path)
    rel = os.path.relpath(path, run_dir)
    if rel.startswith(".."):
        raise ManifestError(f"artifact {path} is outside run dir {run_dir}")
    return {"path": rel, "kind": kind, "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def write_manifest(run_dir: Path, data: dict, complete: bool) -> Path:
    """Write ``data`` with ``complete`` as the final key, atomically."""
    body = {k: v for k, v in data.items() if k != "complete"}
    body["manifest_version"] = MANIFEST_VERSION
    if complete:
        missing = [k for k in REQUIRED_KEYS if k != "complete" and k not in body]
        if missing:
            raise ManifestError(f"refusing to mark complete: missing keys {missing}")
        body["finished_utc"] = body.get("finished_utc") or utcnow()
        _verify_artifacts(Path(run_dir), body["artifacts"])
    body["complete"] = bool(complete)
    path = Path(run_dir) / MANIFEST_NAME
    atomic_write_json(path, body)
    return path


def _verify_artifacts(run_dir: Path, artifacts: list[dict], check_hash: bool = True,
                      scope: str = "all") -> None:
    for a in artifacts:
        p = run_dir / a["path"]
        if not p.is_file():
            if scope == "present":
                continue  # mirror copy (e.g. results/manifests): heavy artifacts stay on Drive
            raise ManifestError(f"artifact missing: {p}")
        size = p.stat().st_size
        if size != a["bytes"]:
            raise ManifestError(f"artifact size changed: {p} ({size} != {a['bytes']})")
        if check_hash and sha256_file(p) != a["sha256"]:
            raise ManifestError(f"artifact hash mismatch: {p}")


def load_manifest(run_dir: Path, *, require_complete: bool = True, require_clean_git: bool = False,
                  expect: dict[str, Any] | None = None, check_hash: bool = True,
                  artifact_scope: str = "all") -> dict:
    """Load and validate a manifest; raise ManifestError with the reason otherwise.

    ``artifact_scope="present"`` validates a mirror that holds only the small
    artifacts: present files must match their recorded hashes; absent ones are
    assumed to live on Drive. ``expect`` maps dotted keys (e.g. ``"identity"`` or ``"config.hash"``) to
    required values; any mismatch is refused (incompatible inputs).
    """
    run_dir = Path(run_dir)
    path = run_dir / MANIFEST_NAME
    if not path.is_file():
        raise ManifestError(f"no manifest at {path}")
    try:
        m = read_json(path)
    except Exception as e:
        raise ManifestError(f"unreadable manifest {path}: {e}") from e
    missing = [k for k in REQUIRED_KEYS if k not in m]
    if missing:
        raise ManifestError(f"{path}: missing keys {missing}")
    if m.get("manifest_version") != MANIFEST_VERSION:
        raise ManifestError(f"{path}: manifest_version {m.get('manifest_version')} unsupported")
    if require_complete:
        if m["complete"] is not True:
            raise ManifestError(f"{path}: run is not complete (complete={m['complete']!r})")
        if list(m)[-1] != "complete":
            raise ManifestError(f"{path}: 'complete' is not the last key; manifest was not finalised")
        _verify_artifacts(run_dir, m["artifacts"], check_hash=check_hash, scope=artifact_scope)
    if require_clean_git and (m["git"].get("dirty") or m["git"].get("sha") in (None, "unknown")):
        raise ManifestError(f"{path}: produced from a dirty or unknown git state; not citable")
    for dotted, want in (expect or {}).items():
        cur: Any = m
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                raise ManifestError(f"{path}: expected key {dotted!r} absent")
            cur = cur[part]
        if cur != want:
            raise ManifestError(f"{path}: incompatible {dotted}: {cur!r} != expected {want!r}")
    return m
