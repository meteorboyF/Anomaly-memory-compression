"""Shared manifest discovery for the figure/table scripts.

Only complete, validated manifests are used. A mirror (``results/manifests``)
holds manifests plus their small JSON artifacts; heavy artifacts stay on Drive
(``artifact_scope="present"``). ``--citable`` additionally refuses manifests
from dirty or unknown git states (required for the submitted paper).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from anomaly_memory.io_utils import read_json  # noqa: E402
from anomaly_memory.manifest import ManifestError, load_manifest  # noqa: E402


def latest_runs(root: Path, citable: bool) -> dict[tuple[str, str], tuple[Path, dict]]:
    """Latest complete run per (tool, config name), excluding smoke runs."""
    out: dict[tuple[str, str], tuple[Path, dict]] = {}
    for mf in sorted(Path(root).rglob("manifest.json")) if Path(root).exists() else []:
        d = mf.parent
        if "_partial" in d.parts:
            continue
        try:
            m = load_manifest(d, require_clean_git=citable, artifact_scope="present")
        except ManifestError as e:
            print(f"  skip {d}: {e}")
            continue
        if m.get("smoke"):
            continue
        key = (m["tool"], m["config"]["name"])
        if key not in out or m["finished_utc"] > out[key][1]["finished_utc"]:
            out[key] = (d, m)
    return out


def artifact_json(run_dir: Path, m: dict, name: str) -> dict | None:
    for a in m["artifacts"]:
        if a["path"] == name and (run_dir / name).is_file():
            return read_json(run_dir / name)
    return None
