"""Small I/O helpers: streaming hashes, atomic writes and copies, free space."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

CHUNK = 8 * 1024 * 1024


def sha256_file(path: str | os.PathLike, chunk: int = CHUNK) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_json(obj: Any) -> str:
    return sha256_bytes(canonical_json(obj).encode())


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass  # some FUSE mounts (Drive) do not support directory fsync
    finally:
        os.close(fd)


def atomic_write_text(path: str | os.PathLike, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    _fsync_dir(path.parent)


def atomic_write_json(path: str | os.PathLike, obj: Any) -> None:
    atomic_write_text(path, json.dumps(obj, indent=2, sort_keys=False, default=str) + "\n")


def read_json(path: str | os.PathLike) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def atomic_copy(src: str | os.PathLike, dst: str | os.PathLike, verify_sha: str | None = None) -> str:
    """Copy ``src`` to ``dst`` via a temporary name, verify, then rename.

    Returns the SHA-256 of the destination as re-read from disk. If
    ``verify_sha`` is given, the destination must match it.
    """
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.name}.tmp-{os.getpid()}")
    try:
        with open(src, "rb") as fi, open(tmp, "wb") as fo:
            shutil.copyfileobj(fi, fo, CHUNK)
            fo.flush()
            os.fsync(fo.fileno())
        if tmp.stat().st_size != src.stat().st_size:
            raise IOError(f"size mismatch copying {src} -> {tmp}")
        got = sha256_file(tmp)
        expected = verify_sha or sha256_file(src)
        if got != expected:
            raise IOError(f"sha256 mismatch copying {src} -> {dst}: {got} != {expected}")
        os.replace(tmp, dst)
        _fsync_dir(dst.parent)
        return got
    finally:
        if tmp.exists():
            tmp.unlink()


def free_bytes(path: str | os.PathLike) -> int:
    p = Path(path)
    while not p.exists() and p != p.parent:
        p = p.parent
    return shutil.disk_usage(p).free


def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TB"


def dir_bytes(path: str | os.PathLike) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total
