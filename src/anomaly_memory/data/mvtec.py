"""Original MVTec AD layout: index, validation, and dataset/split hashes.

Expected structure under the dataset root::

    <category>/train/good/*.png
    <category>/test/<defect_type>/*.png          (defect_type includes 'good')
    <category>/ground_truth/<defect_type>/<stem>_mask.png   (not for 'good')

Only ``train/good`` images may construct memory. Test masks are for
evaluation and scripted analysis only.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from ..io_utils import sha256_file, sha256_json

CATEGORIES = (
    "bottle", "cable", "capsule", "carpet", "grid", "hazelnut", "leather", "metal_nut",
    "pill", "screw", "tile", "toothbrush", "transistor", "wood", "zipper",
)
TEXTURES = ("carpet", "grid", "leather", "tile", "wood")
OBJECTS = tuple(c for c in CATEGORIES if c not in TEXTURES)
IMAGE_EXTS = (".png",)
GOOD = "good"


@dataclasses.dataclass(frozen=True)
class Record:
    category: str
    split: str  # "train" | "test"
    defect_type: str  # "good" or the defect folder name
    relpath: str  # relative to dataset root, POSIX
    mask_relpath: str | None
    label: int  # 0 normal, 1 anomalous

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ValidationReport:
    errors: list[str]
    warnings: list[str]
    counts: dict

    @property
    def ok(self) -> bool:
        return not self.errors


def mask_relpath_for(category: str, defect_type: str, image_name: str) -> str:
    stem = Path(image_name).stem
    return f"{category}/ground_truth/{defect_type}/{stem}_mask.png"


def scan(root: Path, categories=CATEGORIES) -> tuple[list[Record], ValidationReport]:
    """Index the dataset and validate structure and image-mask pairing."""
    root = Path(root)
    records: list[Record] = []
    errors: list[str] = []
    warnings: list[str] = []
    counts: dict = {}
    for cat in categories:
        cdir = root / cat
        c = {"train_good": 0, "test_good": 0, "test_defect": 0, "defect_types": {}}
        counts[cat] = c
        if not cdir.is_dir():
            errors.append(f"missing category folder {cat}/")
            continue
        train = cdir / "train" / GOOD
        if not train.is_dir():
            errors.append(f"{cat}: missing train/good/")
        else:
            for p in sorted(train.iterdir()):
                if p.suffix.lower() not in IMAGE_EXTS:
                    warnings.append(f"{cat}: non-image file in train/good: {p.name}")
                    continue
                records.append(Record(cat, "train", GOOD, p.relative_to(root).as_posix(), None, 0))
                c["train_good"] += 1
            other_train = [d.name for d in (cdir / "train").iterdir() if d.is_dir() and d.name != GOOD]
            if other_train:
                errors.append(f"{cat}: unexpected train subfolders {other_train} (train must be normal-only)")
        test = cdir / "test"
        if not test.is_dir():
            errors.append(f"{cat}: missing test/")
            continue
        gt_root = cdir / "ground_truth"
        expected_masks = set()
        for ddir in sorted(d for d in test.iterdir() if d.is_dir()):
            dt = ddir.name
            n = 0
            for p in sorted(ddir.iterdir()):
                if p.suffix.lower() not in IMAGE_EXTS:
                    warnings.append(f"{cat}/test/{dt}: non-image file {p.name}")
                    continue
                n += 1
                rel = p.relative_to(root).as_posix()
                if dt == GOOD:
                    records.append(Record(cat, "test", GOOD, rel, None, 0))
                    c["test_good"] += 1
                else:
                    m = mask_relpath_for(cat, dt, p.name)
                    expected_masks.add(m)
                    if not (root / m).is_file():
                        errors.append(f"{cat}: missing mask for test image {rel} (expected {m})")
                    records.append(Record(cat, "test", dt, rel, m, 1))
                    c["test_defect"] += 1
            c["defect_types"][dt] = n
        if (gt_root / GOOD).exists():
            errors.append(f"{cat}: ground_truth/good/ should not exist")
        if gt_root.is_dir():
            for m in sorted(gt_root.rglob("*.png")):
                rel = m.relative_to(root).as_posix()
                if rel not in expected_masks:
                    errors.append(f"{cat}: orphan mask without test image: {rel}")
        elif c["test_defect"]:
            errors.append(f"{cat}: missing ground_truth/")
        if c["test_good"] == 0:
            errors.append(f"{cat}: no test/good images")
        if c["test_defect"] == 0:
            errors.append(f"{cat}: no defective test images")
    return records, ValidationReport(errors, warnings, counts)


def check_expected_counts(report: ValidationReport, expected: dict[str, dict[str, int]]) -> None:
    """Compare against published per-category counts; mismatches become errors."""
    for cat, exp in expected.items():
        got = report.counts.get(cat, {})
        for k, v in exp.items():
            if got.get(k) != v:
                report.errors.append(f"{cat}: {k} = {got.get(k)} but published count is {v}")


def check_image_mask_sizes(root: Path, records: list[Record]) -> list[str]:
    """Each mask must have the same pixel size as its image (header read only)."""
    from PIL import Image

    errs = []
    for r in records:
        if r.mask_relpath is None:
            continue
        with Image.open(root / r.relpath) as im, Image.open(root / r.mask_relpath) as mk:
            if im.size != mk.size:
                errs.append(f"size mismatch {r.relpath} {im.size} vs mask {mk.size}")
    return errs


def split_hash(records: list[Record]) -> str:
    """Hash of the official split assignment (paths, splits, labels), not content."""
    rows = sorted((r.category, r.split, r.defect_type, r.relpath, r.mask_relpath or "", r.label) for r in records)
    return sha256_json(rows)


def content_hashes(root: Path, records: list[Record]) -> dict[str, str]:
    out = {}
    for r in records:
        out[r.relpath] = sha256_file(Path(root) / r.relpath)
        if r.mask_relpath:
            out[r.mask_relpath] = sha256_file(Path(root) / r.mask_relpath)
    return out


def dataset_hash(file_hashes: dict[str, str]) -> str:
    return sha256_json(sorted(file_hashes.items()))
