"""Pre-commit guard: refuse secrets, datasets/heavy artifacts, large blobs, and
notebooks with saved outputs. Stdlib only.

    python tools/precommit_check.py          # staged files (git hook)
    python tools/precommit_check.py --all    # every tracked file (CI)

Install the hook once per clone:  git config core.hooksPath .githooks
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import PurePosixPath

MAX_BYTES = 1_000_000
MAX_BYTES_EXCEPTIONS = {"paper/figures/": 3_000_000}
BLOCKED_DIRS = ("data/", "datasets/", "artifacts/", "checkpoints/", "outputs/", "runs/", "wandb/")
BLOCKED_EXT = {
    ".npz", ".npy", ".pt", ".pth", ".ckpt", ".safetensors", ".bin", ".h5", ".hdf5", ".pkl", ".pickle",
    ".joblib", ".tar", ".gz", ".tgz", ".xz", ".bz2", ".zip", ".7z", ".rar", ".parquet", ".feather", ".arrow",
    ".faiss", ".index", ".onnx", ".lmdb", ".mdb",
}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".gif", ".webp"}
IMAGE_ALLOWED_PREFIX = ("paper/",)  # e.g. a graphical abstract; plots must be vector PDF
SECRET_PATTERNS = [
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("Hugging Face token", re.compile(r"\bhf_[A-Za-z0-9]{30,}\b")),
    ("API secret key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("HTTP basic auth header", re.compile(r"Authorization:\s*Basic\s+[A-Za-z0-9+/=]{16,}")),
    ("credential in URL", re.compile(r"https?://[^/\s:@]+:[^/\s@]{6,}@")),
    ("hard-coded secret", re.compile(r"(?i)\b(?:password|passwd|secret|api_key|apikey|token)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]")),
]


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def staged_files() -> list[str]:
    out = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    return [p for p in out.decode().split("\0") if p]


def tracked_files() -> list[str]:
    return [p for p in _git("ls-files", "-z").decode().split("\0") if p]


def content(path: str, staged: bool) -> bytes:
    if staged:
        return _git("show", f":{path}")
    with open(path, "rb") as f:
        return f.read()


def check_file(path: str, data: bytes) -> list[str]:
    errs = []
    p = PurePosixPath(path)
    ext = p.suffix.lower()
    if any(path.startswith(d) for d in BLOCKED_DIRS):
        errs.append(f"{path}: data/artifact directories must never be committed (store on Drive)")
    if ext in BLOCKED_EXT:
        errs.append(f"{path}: '{ext}' files are datasets/weights/archives; store them on Drive")
    if ext in IMAGE_EXT and not path.startswith(IMAGE_ALLOWED_PREFIX):
        errs.append(f"{path}: raster images are not allowed outside paper/ (no dataset images in git)")
    limit = next((v for k, v in MAX_BYTES_EXCEPTIONS.items() if path.startswith(k)), MAX_BYTES)
    if len(data) > limit:
        errs.append(f"{path}: {len(data)} bytes exceeds the {limit}-byte limit for committed files")
    if ext == ".ipynb":
        try:
            nb = json.loads(data.decode("utf-8"))
            dirty = [i for i, c in enumerate(nb.get("cells", []))
                     if c.get("cell_type") == "code" and (c.get("outputs") or c.get("execution_count") is not None)]
            if dirty:
                errs.append(f"{path}: notebook has saved outputs/execution counts in cells {dirty}; strip them")
            if "widgets" in nb.get("metadata", {}):
                errs.append(f"{path}: notebook carries widget state metadata; strip it")
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            errs.append(f"{path}: unreadable notebook ({e})")
    if b"\0" not in data[:8192]:
        text = data.decode("utf-8", "replace")
        for name, pat in SECRET_PATTERNS:
            m = pat.search(text)
            if m:
                line = text.count("\n", 0, m.start()) + 1
                errs.append(f"{path}:{line}: possible {name}; remove it (secrets belong in Colab Secrets only)")
    return errs


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    all_mode = "--all" in argv
    files = tracked_files() if all_mode else staged_files()
    errs = []
    for f in files:
        try:
            errs += check_file(f, content(f, staged=not all_mode))
        except (OSError, subprocess.CalledProcessError) as e:
            errs.append(f"{f}: cannot read ({e})")
    if errs:
        print("pre-commit check FAILED:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
