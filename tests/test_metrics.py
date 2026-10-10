"""Metric replica vs the vendored official MVTec code, sklearn, and analytic cases."""
import contextlib
import io
import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

from anomaly_memory.eval import metrics as M
from anomaly_memory.eval import strata as S

sys.path.insert(0, str(Path(__file__).parent / "reference" / "mvtec_official"))
import generic_util as G  # noqa: E402
import pro_curve_util as P  # noqa: E402
import roc_curve_util as R  # noqa: E402


def _case(seed, quant):
    g = np.random.default_rng(seed)
    n, h, w = 6, 24, 20
    gt = np.zeros((n, h, w))
    for i in range(n - 2):
        for _ in range(g.integers(1, 3)):
            y, x = g.integers(0, h - 5), g.integers(0, w - 5)
            gt[i, y:y + g.integers(1, 5), x:x + g.integers(1, 5)] = 1
    maps = g.random((n, h, w)) + 0.7 * gt
    if quant:
        maps = np.round(maps * quant) / quant
    return maps, gt


@pytest.mark.parametrize("seed", range(12))
def test_matches_official(seed):
    maps, gt = _case(seed, [None, 4, 32][seed % 3])
    with contextlib.redirect_stdout(io.StringIO()):
        f1, p1 = P.compute_pro(list(maps), list(gt))
    f2, p2 = M.pro_curve(maps, gt)
    np.testing.assert_allclose(f1, f2, atol=1e-6)  # official FPR uses float32
    np.testing.assert_allclose(p1, p2, atol=1e-9)
    for lim in (0.3, 0.05, 1.0):
        assert abs(G.trapezoid(f1, p1, x_max=lim) / lim - M.au_pro(maps, gt, lim)) < 1e-6
    labels = [int(x.any()) for x in gt]
    fr, tr = R.compute_classification_roc(list(maps), np.max, labels)
    assert abs(G.trapezoid(fr, tr) - M.auroc(M.image_scores_from_maps(maps), labels)) < 1e-12


def test_auroc_matches_sklearn_with_ties():
    g = np.random.default_rng(1)
    s = np.round(g.random(500), 1)
    y = g.random(500) < 0.3
    assert abs(M.auroc(s, y) - roc_auc_score(y, s)) < 1e-12
    assert np.isnan(M.auroc([1, 2], [0, 0]))


def test_analytic():
    gt = np.zeros((3, 10, 10))
    gt[0, 1:4, 1:4] = 1
    assert M.au_pro(gt.copy(), gt) == pytest.approx(1.0)
    assert M.au_pro(np.zeros_like(gt), gt) == pytest.approx(0.15)
    assert M.pixel_auroc(1 - gt, gt) == pytest.approx(0.0)


def test_connectivity_matters():
    gt = np.zeros((1, 6, 6))
    gt[0, 1, 1] = gt[0, 2, 2] = 1  # diagonal neighbours: 1 region (8-conn), 2 regions (4-conn)
    assert M.pro_weights(gt, 8)[3] == 1
    assert M.pro_weights(gt, 4)[3] == 2


def test_errors():
    with pytest.raises(ValueError):
        M.au_pro(np.zeros((2, 4, 4)), np.zeros((2, 4, 4)))  # no regions
    with pytest.raises(ValueError):
        M.auroc([np.nan, 1], [0, 1])


def test_strata_assignment_and_stratified_metrics():
    spec = S.StrataSpec([0.0, 0.01, 0.1, 1.0], ["s", "m", "l"], 1, 1)
    assert list(S.assign(np.array([0.0005, 0.01, 0.05, 0.5, 1.0]), spec)) == [0, 1, 1, 2, 2]
    scores = np.array([0.1, 0.2, 0.9, 0.3])
    labels = np.array([0, 0, 1, 1])
    st = np.array([-1, -1, 0, 1])
    res = S.stratified_image_auroc(scores, labels, st, 3)
    assert res[0]["image_auroc"] == 1.0 and res[1]["image_auroc"] == 1.0 and np.isnan(res[2]["image_auroc"])
    with pytest.raises(ValueError):
        S.StrataSpec([0.0, 0.5], ["a", "b"], 1, 1).validate()


def test_region_stratified_au_pro():
    gt = np.zeros((3, 20, 20))
    gt[0, 1, 1] = 1                 # 1 px region  -> 0.25% of 400 px (small)
    gt[0, 10:16, 10:16] = 1         # 36 px region -> 9% (large)
    maps = np.random.default_rng(0).random(gt.shape) * 0.5
    maps[0, 10:16, 10:16] = 1.0     # large region found, small one missed
    spec = S.StrataSpec([0.0, 0.01, 1.0], ["S", "L"], 1, 1)
    res = {r["stratum"]: r for r in S.region_stratified_au_pro(maps, gt, spec)}
    assert res["S"]["n_regions"] == 1 and res["L"]["n_regions"] == 1
    assert res["L"]["au_pro"] > 0.99 and res["S"]["au_pro"] < res["L"]["au_pro"]
