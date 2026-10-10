"""Pre-commit hook refuses forbidden material (tested in a scratch repo, nothing committed here);
root-anchored /data/ ignore; figure/table scripts are manifest-driven."""
import json
import shutil
import subprocess
import sys

import pytest

from conftest import REPO

# fake secrets are assembled at runtime so this file itself never contains one
FAKE_GH = "gh" + "p_" + "A1b2C3d4" * 5
FAKE_AWS = "AK" + "IA" + "ABCDEFGHIJKLMNOP"


def git(cwd, *a, check=True):
    return subprocess.run(["git", *a], cwd=cwd, check=check, capture_output=True, text=True)


@pytest.fixture
def scratch(tmp_path):
    git(tmp_path, "init", "-q")
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        git(tmp_path, "config", k, v)
    (tmp_path / "tools").mkdir()
    shutil.copy(REPO / "tools" / "precommit_check.py", tmp_path / "tools")
    shutil.copytree(REPO / ".githooks", tmp_path / ".githooks")
    git(tmp_path, "config", "core.hooksPath", ".githooks")
    return tmp_path


def try_commit(repo, rel, data: bytes):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    git(repo, "add", "-f", rel)
    r = git(repo, "commit", "-qm", "x", check=False)
    git(repo, "reset", "-q")
    return r


@pytest.mark.parametrize("rel,data,why", [
    ("cfg.py", f"TOKEN = '{FAKE_GH}'\n".encode(), "GitHub token"),
    ("notes.md", f"key {FAKE_AWS}\n".encode(), "AWS"),
    ("x.txt", ("-----BEGIN RSA PRIV" + "ATE KEY-----\n").encode(), "private key"),
    ("data/train.csv", b"a,b\n", "data/artifact"),
    ("feats.npz", b"PK\x03\x04", "npz"),
    ("big.txt", b"a" * 1_100_000, "exceeds"),
    ("docs/img.png", b"\x89PNG", "raster"),
    ("nb.ipynb", json.dumps({"cells": [{"cell_type": "code", "outputs": [{"text": "x"}], "execution_count": 3,
                                        "source": []}], "metadata": {}}).encode(), "saved outputs"),
], ids=lambda v: v if isinstance(v, str) and len(v) < 40 else "")
def test_hook_refuses(scratch, rel, data, why):
    r = try_commit(scratch, rel, data)
    assert r.returncode != 0 and why in r.stderr, r.stderr
    assert git(scratch, "log", "--oneline", check=False).stdout == ""


def test_hook_allows_clean(scratch):
    assert try_commit(scratch, "ok.py", b"print('fine')\n").returncode == 0


def test_whole_repo_passes_checker():
    r = subprocess.run([sys.executable, str(REPO / "tools" / "precommit_check.py"), "--all"], cwd=REPO,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_data_ignore_is_root_anchored():
    def ignored(path):
        return git(REPO, "check-ignore", "-q", "--no-index", path, check=False).returncode == 0
    assert ignored("data/x.png") and ignored("data/sub/y")
    assert not ignored("src/anomaly_memory/data/mvtec.py")
    assert not ignored("src/anomaly_memory/data/__init__.py")


def test_scripts_build_from_manifests_only(tmp_path):
    from anomaly_memory.manifest import artifact_entry, write_manifest
    run = tmp_path / "m" / "profile_data" / "phase0_data-abc"
    run.mkdir(parents=True)
    summ = {"categories": {"bottle": {"train_good": 3, "test_good": 2, "test_defect": 4,
                                      "defect_types": {"crack": 2}}},
            "per_category_defect_area": {"bottle": {"n": 4, "median": 0.01, "min": 0.001, "max": 0.1}}}
    (run / "profile_summary.json").write_text(json.dumps(summ))
    write_manifest(run, {"tool": "profile_data", "run_id": "phase0_data-abc", "identity": {}, "smoke": False,
                         "config": {"name": "phase0_data"}, "git": {"sha": "a" * 40, "dirty": False}, "seed": {},
                         "environment": {}, "hardware": {}, "started_utc": "t",
                         "results": {"totals": {"images": 9, "train_good": 3, "test_good": 2, "test_defect": 4},
                                     "n_erased_by_policy": 0},
                         "artifacts": [artifact_entry(run, run / "profile_summary.json")]}, complete=True)
    out = tmp_path / "gen"
    for s in ("make_tables.py", "make_figures.py"):
        r = subprocess.run([sys.executable, str(REPO / "scripts" / s), "--manifest-root", str(tmp_path / "m"),
                            "--out", str(out), "--citable"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    macros = (out / "results_macros.tex").read_text()
    assert r"\newcommand{\DatasetNumImages}{9}" in macros and "[pending]" in macros  # others still pending
    assert "bottle & 3 & 2 & 4 & 1 & 1.00" in (out / "table_dataset.tex").read_text()
    pdf = (out / "defect_area_by_category.pdf").read_bytes()
    assert pdf.startswith(b"%PDF") and b"/FontFile2" in pdf  # TrueType fonts embedded
