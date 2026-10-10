"""One seeding utility, called once per entrypoint; the seed goes in the manifest."""

from __future__ import annotations

import os
import random
import sys

import numpy as np


def set_seed(seed: int, deterministic: bool = True) -> dict:
    """Seed python, numpy and (if already imported) torch. Returns what was set.

    torch is only seeded when the entrypoint has imported it, so CPU tools do
    not pay the torch import cost. Full CUDA determinism is not guaranteed for
    every kernel; headline results rely on seed-averaged reporting instead.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    info = {"seed": seed, "python": True, "numpy": True, "torch": False, "deterministic": False}
    torch = sys.modules.get("torch")
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        info["torch"] = True
        if deterministic:
            os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
            torch.use_deterministic_algorithms(True, warn_only=True)
            torch.backends.cudnn.benchmark = False
            info["deterministic"] = "warn_only"
    return info


def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)
