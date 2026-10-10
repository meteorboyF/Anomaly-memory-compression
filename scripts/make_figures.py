"""Build publication figures (vector PDF, embedded fonts) from manifests only.

    python scripts/make_figures.py [--manifest-root results/manifests] [--out paper/figures] [--citable]

A figure whose inputs do not exist yet is skipped with a message, never faked.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _manifests import REPO, artifact_json, latest_runs

COLUMN_IN = 3.5  # single-column width for Elsevier two-column layouts
INK = "#1f1f1f"
MUTED = "#8a8a8a"


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "pdf.fonttype": 42, "ps.fonttype": 42,  # embed TrueType fonts
        "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    })
    return plt


def fig_defect_area(summary: dict, out: Path) -> Path:
    """Per-category defect-area fraction: median (dot) and min-max range (line), log scale."""
    plt = _mpl()
    area = summary["per_category_defect_area"]
    cats = sorted(area, key=lambda c: area[c]["median"])
    fig, ax = plt.subplots(figsize=(COLUMN_IN, 0.18 * len(cats) + 0.6))
    for i, c in enumerate(cats):
        a = area[c]
        ax.plot([100 * max(a["min"], 1e-6), 100 * a["max"]], [i, i], color=MUTED, lw=1.2, solid_capstyle="round")
        ax.plot(100 * a["median"], i, "o", ms=4.5, color=INK, mec="white", mew=0.8)
    ax.set_yticks(range(len(cats)), [f"{c.replace('_', ' ')} (n={area[c]['n']})" for c in cats])
    ax.set_xscale("log")
    ax.set_xlabel("Defect area (% of image pixels, native resolution)")
    ax.grid(axis="x", color="#e6e6e6", lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout(pad=0.3)
    path = out / "defect_area_by_category.pdf"
    fig.savefig(path)
    plt.close(fig)
    return path


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest-root", default=str(REPO / "results" / "manifests"))
    p.add_argument("--out", default=str(REPO / "paper" / "figures"))
    p.add_argument("--citable", action="store_true")
    a = p.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    runs = latest_runs(Path(a.manifest_root), a.citable)
    r = runs.get(("profile_data", "phase0_data"))
    summary = artifact_json(r[0], r[1], "profile_summary.json") if r else None
    if summary:
        print(f"wrote {fig_defect_area(summary, out)}")
    else:
        print("defect_area_by_category: pending (no complete profile_data manifest)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
