"""Every package submodule imports (guards the unanchored-gitignore class of bug)
and the package does not import torch at import time."""
import importlib
import pkgutil
import subprocess
import sys

import anomaly_memory

EXPECTED = {"anomaly_memory.data.mvtec", "anomaly_memory.data.acquire", "anomaly_memory.data.profile",
            "anomaly_memory.data.preprocess", "anomaly_memory.eval.metrics", "anomaly_memory.eval.strata",
            "anomaly_memory.eval.evaluate", "anomaly_memory.eval.predictions", "anomaly_memory.budget",
            "anomaly_memory.manifest", "anomaly_memory.runctx", "anomaly_memory.features.cache",
            "anomaly_memory.memory.accounting", "anomaly_memory.baselines.trivial"}


def test_import_every_submodule():
    names = {m.name for m in pkgutil.walk_packages(anomaly_memory.__path__, "anomaly_memory.")}
    missing = EXPECTED - names
    assert not missing, f"submodules missing from the package tree: {missing}"
    for n in sorted(names):
        importlib.import_module(n)


def test_no_torch_at_import():
    code = ("import sys, pkgutil, importlib, anomaly_memory\n"
            "[importlib.import_module(m.name) for m in pkgutil.walk_packages(anomaly_memory.__path__, 'anomaly_memory.')]\n"
            "print('torch' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         env={"PYTHONPATH": anomaly_memory.__path__[0] + "/.."}).stdout.strip()
    assert out == "False"
