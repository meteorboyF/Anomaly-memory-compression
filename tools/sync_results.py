"""Mirror complete manifests + their small JSON artifacts into results/manifests.

    python tools/sync_results.py --from <dir with tool/run_id/manifest.json> [--to results/manifests]

Only complete, valid manifests are copied; only ``.json`` artifacts under
1 MB are copied (and re-verified against their recorded SHA-256). Heavy
artifacts stay on Drive. Smoke runs are skipped. The mirror is what the
figure/table scripts read when building the paper.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from anomaly_memory.io_utils import sha256_file  # noqa: E402
from anomaly_memory.manifest import ManifestError, load_manifest  # noqa: E402

MAX_ARTIFACT = 1_000_000


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--from", dest="src", required=True)
    p.add_argument("--to", default=str(REPO / "results" / "manifests"))
    a = p.parse_args(argv)
    src, dst = Path(a.src), Path(a.to)
    n = 0
    for mf in sorted(src.rglob("manifest.json")):
        d = mf.parent
        if "_partial" in d.parts:
            continue
        try:
            m = load_manifest(d)
        except ManifestError as e:
            print(f"skip (not complete/valid): {d}: {e}")
            continue
        if m.get("smoke"):
            continue
        out = dst / m["tool"] / m["run_id"]
        out.mkdir(parents=True, exist_ok=True)
        for art in m["artifacts"]:
            f = d / art["path"]
            if f.suffix == ".json" and art["bytes"] <= MAX_ARTIFACT:
                target = out / art["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, target)
                if sha256_file(target) != art["sha256"]:
                    raise SystemExit(f"hash mismatch copying {f}")
        shutil.copyfile(mf, out / "manifest.json")
        load_manifest(out, artifact_scope="present")
        n += 1
        print(f"mirrored {m['tool']}/{m['run_id']}")
    print(f"{n} run(s) mirrored to {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
