"""Experiment identity: config hash + hash of the scientific code it ran.

Each tool declares the modules whose behaviour determines its scientific
output (``SCIENCE_MODULES``). Editing any of them changes the identity, so
results from old and new code land in different run directories and are
never mixed or resumed across. Edits to non-scientific code (logging, the
Colab driver, budget checks) keep the identity, so ordinary fixes do not
orphan valid artifacts.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from .io_utils import sha256_bytes, sha256_json


def module_file(module: str) -> Path:
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None:
        raise ImportError(f"cannot locate module {module!r}")
    return Path(spec.origin)


def science_code_hash(modules: list[str]) -> dict:
    files = {}
    for m in sorted(set(modules)):
        p = module_file(m)
        # normalise line endings so checkouts on different OSes agree
        files[m] = sha256_bytes(p.read_bytes().replace(b"\r\n", b"\n"))
    return {"modules": files, "hash": sha256_json(files)}


def experiment_identity(config_hash: str, modules: list[str], extra: dict | None = None) -> dict:
    code = science_code_hash(modules)
    ident = sha256_json({"config": config_hash, "code": code["hash"], "extra": extra or {}})
    return {"id": ident[:16], "full": ident, "config_hash": config_hash,
            "science_code": code, "extra": extra or {}}
