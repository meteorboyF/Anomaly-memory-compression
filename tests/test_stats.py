"""Pre-registered inference: grid AU-PRO accuracy, paired bootstrap, verdict rules."""
import numpy as np
import pytest

from anomaly_memory.eval import stats as S

EDGES = [0.0, 0.01, 1.0]  # S: <1 %, L: >=1 % of a 40x40 image (16 px)


def make_category(seed, small_penalty, n_def=24, n_good=12):
    """Masks with one small (4 px) and one large (64 px) region per defective image.
    'cmp' arm lowers scores inside small regions by small_penalty."""
    g = np.random.default_rng(seed)
    n = n_def + n_good
    masks = np.zeros((n, 40, 40), bool)
    for i in range(n_def):
        masks[i, 2:4, 2:4] = True
        masks[i, 20:28, 20:28] = True
    base = g.random(masks.shape) + 1.2 * masks
    cmp = base.copy()
    small = np.zeros_like(masks)
    small[:n_def, 2:4, 2:4] = True
    cmp[small] -= small_penalty
    th = S.threshold_grid(base, masks, 1500)
    summ = {"ref": {0: S.summarise_pro(base, masks, th)}, "cmp": {0: S.summarise_pro(cmp, masks, th)}}
    is_def = np.arange(n) < n_def
    return S.CategoryArms(f"c{seed}", is_def, summ), base, masks


def test_grid_matches_exact():
    _, maps, masks = make_category(0, 0.0)
    th = S.threshold_grid(maps, masks, 2000)
    assert S.max_grid_error(maps, masks, th) < 2e-3


def test_effect_detected_and_null_classified():
    eff = [make_category(i, 0.8)[0] for i in range(4)]
    r = S.bootstrap_contrast(eff, EDGES, "ref", "cmp", min_regions=5, n_boot=200)
    assert r["D"] > 0.05 and r["ci95"][0] > 0
    assert S.classify(r, sesoi=0.02).startswith("supported")
    null = [make_category(i, 0.0)[0] for i in range(4)]
    r0 = S.bootstrap_contrast(null, EDGES, "ref", "cmp", min_regions=5, n_boot=200)
    assert r0["D"] == pytest.approx(0.0, abs=1e-12)
    assert S.classify(r0, sesoi=0.02).startswith("informative null")


def test_invalid_cells_excluded():
    cat = make_category(0, 0.5)[0]
    r = S.bootstrap_contrast([cat], EDGES, "ref", "cmp", min_regions=1000, n_boot=10)
    assert r["valid_categories"] == [] and np.isnan(r["D"])


def test_classify_inconclusive():
    r = {"D": 0.01, "ci95": [-0.03, 0.05], "ci90": [-0.025, 0.045], "D_per_seed": [0.01, 0.02, -0.01]}
    assert S.classify(r, 0.02).startswith("inconclusive")
