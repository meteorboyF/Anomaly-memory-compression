import io
import sys
import tarfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))


def _png(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)


def make_fake_mvtec(root: Path, categories=("bottle", "carpet"), size=64, n_train=3, n_good=2,
                    defects=("crack", "hole"), n_def=2) -> Path:
    """Tiny MVTec-shaped tree. Defects are squares of different sizes."""
    g = np.random.default_rng(0)
    for c in categories:
        for i in range(n_train):
            _png(root / c / "train" / "good" / f"{i:03d}.png", g.integers(0, 255, (size, size, 3), dtype=np.uint8))
        for i in range(n_good):
            _png(root / c / "test" / "good" / f"{i:03d}.png", g.integers(0, 255, (size, size, 3), dtype=np.uint8))
        for d_i, d in enumerate(defects):
            for i in range(n_def):
                _png(root / c / "test" / d / f"{i:03d}.png", g.integers(0, 255, (size, size, 3), dtype=np.uint8))
                m = np.zeros((size, size), dtype=np.uint8)
                s = 2 + 6 * (i + d_i)
                m[10:10 + s, 20:20 + s] = 255
                _png(root / c / "ground_truth" / d / f"{i:03d}_mask.png", m)
    return root


def make_archive(src_root: Path, out: Path, top: str | None = None, extra_members=()) -> Path:
    with tarfile.open(out, "w:xz") as tf:
        for p in sorted(src_root.rglob("*")):
            arc = p.relative_to(src_root).as_posix()
            tf.add(p, arcname=f"{top}/{arc}" if top else arc, recursive=False)
        for name, data in extra_members:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return out


@pytest.fixture
def fake_mvtec(tmp_path):
    return make_fake_mvtec(tmp_path / "mvtec")


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Point Drive/local/state roots at temp dirs."""
    monkeypatch.setenv("AMC_DRIVE_ROOT", str(tmp_path / "drive"))
    monkeypatch.setenv("AMC_LOCAL_ROOT", str(tmp_path / "local"))
    monkeypatch.setenv("AMC_STATE_DIR", str(tmp_path / "state"))
    (tmp_path / "drive").mkdir()
    return tmp_path
