"""Generate notebooks/runner.ipynb (output-free, deterministic).

    python tools/build_notebook.py          # write
    python tools/build_notebook.py --check  # exit 1 if the committed file is stale
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "notebooks" / "runner.ipynb"

INTRO = """# Anomaly Memory Compression — Colab runner

Thin wrapper: every scientific step runs `tools/<tool>.py --config <name>` from the GitHub
repository in a **fresh subprocess**; no research code is imported into this kernel.

**Runtime:** use a **CPU** runtime for setup, the dataset download, and all of Phase 0.
Do not attach a GPU until the Phase 0 gate and a specific CU allocation are approved.

**Order:** Cell 1 (setup) → Cell 2 (dataset to Drive) → Cell 3 (CPU checks). Cells 5–9 are
accelerator/Phase 1 cells; they do nothing unless explicitly enabled *and* the repository's
gate and allocation files allow it, so **Run all is safe**.

**Repair loop:** share the traceback → fix is pushed → run **Cell 4 (refresh code)** → rerun the
failed cell. No kernel restart for ordinary Python fixes. A dependency change is flagged
separately; compiled-package changes, dead Drive mounts (`Transport endpoint is not connected`)
or a lost runtime require *Runtime → Restart session* (or a new runtime) and re-running Cell 1,
which restores state from Drive idempotently.
"""

CELL1 = '''#@title 1 · Setup (CPU runtime). Safe to re-run; restores state on a new runtime.
REPO_URL = "https://github.com/meteorboyF/Anomaly-memory-compression.git"
BRANCH = "main"     # branch to track
COMMIT = ""         # optional exact SHA to pin (overrides the branch head)
DRIVE_ROOT = "/content/drive/MyDrive/Research/Anomaly-memory-compression"
REPO_DIR = "/content/Anomaly-memory-compression"
USE_GH_TOKEN = False  # only if the repo becomes private: Colab Secrets -> GH_TOKEN

import os, subprocess, base64
from google.colab import drive
drive.mount("/content/drive")
os.environ.update(AMC_DRIVE_ROOT=DRIVE_ROOT, AMC_LOCAL_ROOT="/content/amc_local")
os.makedirs(DRIVE_ROOT, exist_ok=True)
if USE_GH_TOKEN:
    from google.colab import userdata
    os.environ["GH_TOKEN"] = userdata.get("GH_TOKEN")  # process env only; never saved or printed
if not os.path.isdir(os.path.join(REPO_DIR, ".git")):
    tok = os.environ.get("GH_TOKEN")
    auth = ["-c", "http.extraHeader=Authorization: Basic "
            + base64.b64encode(f"x-access-token:{tok}".encode()).decode()] if tok else []
    r = subprocess.run(["git", *auth, "clone", "--branch", BRANCH, REPO_URL, REPO_DIR],
                       capture_output=True, text=True)  # plain URL: no credential stored in the remote
    if r.returncode:
        raise RuntimeError("clone failed: " + r.stderr.replace(tok or "\\0", "***"))
exec(open(os.path.join(REPO_DIR, "notebooks", "colab_driver.py")).read())
refresh_code()        # fast-forward (or pin COMMIT); refuses on a dirty checkout; prints the SHA
install_deps("cpu")   # skipped when the CPU dependency fingerprint is unchanged
hardware()
status()
'''

CELL2_MD = """## 2 · Download dataset into Google Drive
Calls the committed acquisition tool: resolves the official MVTec AD link, streams to local disk
with resume and bounded retries, rejects HTML/error pages, hashes (SHA-256, ours — the publisher
provides no checksum), safely extracts and checks all 15 categories and every image–mask pair,
then copies the archive atomically to Drive and writes a verified marker. Re-running skips
verified work; on a new runtime it only re-stages from Drive. Works on a CPU runtime.

If it prints **MANUAL FALLBACK** instructions: download the whole-dataset archive from the official
page, upload it **compressed** to the Drive path printed, and re-run this cell."""

CELL2 = '''#@title 2 · Download/verify MVTec AD -> Drive (idempotent, CPU)
run("acquire_data", config="acquire_mvtec_ad")
'''

CELL3 = '''#@title 3 · CPU checks: metric replica, data profile, evaluator sanity (no GPU)
run("metric_selfcheck", config="metric_selfcheck")
run("profile_data", config="phase0_data")
run("evaluator_sanity", config="evaluator_sanity")          # PatchCore-reproduction geometry (224 crop)
run("evaluator_sanity", config="evaluator_sanity_native")   # study protocol: native resolution, no crop
'''

CELL4 = '''#@title 4 · Refresh code from GitHub (after a fix is pushed). No restart needed.
refresh_code()
status()
'''

CELL5_MD = """## Accelerator cells (BLOCKED in Phase 0)
Enable only after the Phase 0 gate **and** a specific CU allocation are approved in chat and recorded
in `configs/control/`. Then: *Runtime → Change runtime type →* the approved GPU, re-run Cell 1 (and
Cell 2 to re-stage data), then the cells below. The wall-clock guard is approximate, not a CU meter."""

CELL5 = '''#@title 5 · Accelerator dependencies + budget preflight
ENABLE_ACCELERATOR = False   # True only for an approved allocation
ALLOCATION_ID = ""           # e.g. "A1" from configs/control/allocations.yaml
CU_BALANCE_NOW = None        # the compute-unit balance Colab shows now (for reconciliation)
if not ENABLE_ACCELERATOR:
    print("Accelerator work is disabled (Phase 0). Nothing was run.")
else:
    assert hardware(), "No GPU attached: Runtime > Change runtime type."
    install_deps("gpu")
    budget("session-start", "--allocation", ALLOCATION_ID,
           *(["--balance", str(CU_BALANCE_NOW)] if CU_BALANCE_NOW is not None else []))
    budget("status")
'''

CELL6 = '''#@title 6 · Tiny smoke test (accelerator)
if globals().get("ENABLE_ACCELERATOR"):
    run("extract_features", config="patchcore_features", smoke=True)
else:
    print("skipped (accelerator disabled)")
'''

CELL7 = '''#@title 7 · Feature extraction (accelerator, resumable)
if globals().get("ENABLE_ACCELERATOR"):
    run("extract_features", config="patchcore_features", resume=True)
else:
    print("skipped (accelerator disabled)")
'''

CELL8 = '''#@title 8 · Baseline execution (accelerator, resumable)
if globals().get("ENABLE_ACCELERATOR"):
    run("run_baseline", config="patchcore_baseline", resume=True)
else:
    print("skipped (accelerator disabled)")
'''

CELL9 = '''#@title 9 · Evaluation from saved raw predictions (CPU; Phase 1+)
RUN_EVALUATION = False   # True once a complete prediction run exists
if RUN_EVALUATION:
    run("evaluate", config="baseline_eval")
else:
    print("skipped")
'''

CELL10 = '''#@title 10 · Manifest-driven figures/tables (preview; publication copies are built in the repo)
import subprocess, sys
subprocess.run([sys.executable, f"{REPO_DIR}/scripts/make_tables.py", "--manifest-root",
                f"{DRIVE_ROOT}/artifacts/manifests", "--out", "/content/amc_local/preview"], check=False)
subprocess.run([sys.executable, f"{REPO_DIR}/scripts/make_figures.py", "--manifest-root",
                f"{DRIVE_ROOT}/artifacts/manifests", "--out", "/content/amc_local/preview"], check=False)
'''

CELL11 = '''#@title 11 · Status, artifact verification, shutdown reminder
status()
verify_artifacts()
if globals().get("ENABLE_ACCELERATOR"):
    finish_accelerator_batch(ALLOCATION_ID, CU_BALANCE_NOW)  # prints the shutdown instruction after verifying
else:
    print("CPU session: nothing to release. Runtime > Disconnect and delete runtime when finished.")
'''


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": text.splitlines(keepends=True)}


def notebook() -> dict:
    cells = [md(INTRO), code(CELL1), md(CELL2_MD), code(CELL2), code(CELL3), code(CELL4), md(CELL5_MD),
             code(CELL5), code(CELL6), code(CELL7), code(CELL8), code(CELL9), code(CELL10), code(CELL11)]
    return {"cells": cells, "metadata": {"colab": {"provenance": []},
                                         "kernelspec": {"display_name": "Python 3", "name": "python3"},
                                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5}


def render() -> str:
    nb = notebook()
    for i, c in enumerate(nb["cells"]):
        c["id"] = f"cell-{i:02d}"
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    text = render()
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text() != text:
            print("notebooks/runner.ipynb is stale; run tools/build_notebook.py")
            return 1
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
