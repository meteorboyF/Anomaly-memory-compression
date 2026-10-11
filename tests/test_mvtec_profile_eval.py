"""Layout scan, profile, prediction I/O, evaluator, and the tool harness on fake data."""
import json

import numpy as np
import pytest

from anomaly_memory.data import mvtec
from anomaly_memory.data.preprocess import GeometryPolicy, crop_box, transform_mask
from anomaly_memory.data.profile import profile_record, summarise
from anomaly_memory.eval import predictions
from anomaly_memory.eval.evaluate import MetricSpec, evaluate_category
from anomaly_memory.eval.strata import StrataSpec

POL = GeometryPolicy("t", resize=32, crop=28)
SPEC = StrataSpec([0.0, 0.02, 1.0], ["small", "large"], 1, 1)


def test_scan_counts_and_hashes(fake_mvtec):
    recs, rep = mvtec.scan(fake_mvtec, ["bottle", "carpet"])
    assert rep.ok, rep.errors
    assert rep.counts["bottle"] == {"train_good": 3, "test_good": 2, "test_defect": 4,
                                    "defect_types": {"crack": 2, "good": 2, "hole": 2}}
    assert all(r.label == 0 for r in recs if r.split == "train")
    h1 = mvtec.split_hash(recs)
    assert h1 == mvtec.split_hash(list(reversed(recs)))
    mvtec.check_expected_counts(rep, {"bottle": {"train_good": 99}})
    assert not rep.ok


def test_scan_flags_defect_in_train(fake_mvtec):
    (fake_mvtec / "bottle" / "train" / "crack").mkdir()
    _, rep = mvtec.scan(fake_mvtec, ["bottle"])
    assert any("normal-only" in e for e in rep.errors)


def test_geometry_matches_torchvision_rule():
    assert crop_box((256, 256), 224) == (16, 16, 240, 240)
    m = np.zeros((64, 64), bool)
    m[0:2, 0:2] = True  # corner defect: cropped away
    assert not transform_mask(m, POL).any()


def test_profile_and_summary(fake_mvtec):
    recs, _ = mvtec.scan(fake_mvtec, ["bottle", "carpet"])
    rows = [profile_record(fake_mvtec, r, POL) for r in recs]
    s = summarise(rows)
    assert s["totals"]["test_defect"] == 8
    d = [r for r in rows if r["label"]]
    assert all(r["native_components"] == 1 and r["native_area_fraction"] > 0 for r in d)
    assert s["exact_file_duplicates"]["n_duplicate_groups"] == 0
    from anomaly_memory.data.profile import bin_counts, mask_checks
    # fake squares: side 2,8 (crack) and 8,14 (hole) px on 64x64 -> 0.1%,1.6%,1.6%,4.8%
    bc = bin_counts(rows, [0.0, 0.01, 1.0], ["S", "L"])
    assert bc["per_category"]["bottle"]["regions"] == {"S": 1, "L": 3}
    assert bc["per_category"]["bottle"]["images_by_largest"] == {"S": 1, "L": 3}
    assert mask_checks(rows)["non_binary_masks"] == []


def test_predictions_roundtrip_and_validation(tmp_path):
    p = predictions.save(tmp_path / "c.npz", ["a", "b"], [0.1, 0.2], np.zeros((2, 4, 4)), {"m": 1})
    out = predictions.load(p, expected_relpaths=["b", "a"])
    assert out["meta"] == {"m": 1}
    with pytest.raises(predictions.PredictionError):
        predictions.load(p, expected_relpaths=["a"])
    with pytest.raises(predictions.PredictionError):
        predictions.save(tmp_path / "d.npz", ["a"], [np.nan], np.zeros((1, 4, 4)), {})


def test_evaluate_oracle_and_constant(fake_mvtec, tmp_path):
    recs, _ = mvtec.scan(fake_mvtec, ["bottle"])
    test = [r for r in recs if r.split == "test"]
    from anomaly_memory.baselines.trivial import make_maps
    from anomaly_memory.eval.evaluate import ground_truth
    masks, labels, frac = ground_truth(fake_mvtec, test, POL)
    for kind, expect in (("oracle_mask", 1.0), ("constant", 0.5)):
        maps, scores = make_maps(kind, masks, 0)
        p = predictions.save(tmp_path / f"{kind}.npz", [r.relpath for r in test], scores, maps, {})
        res, rows = evaluate_category(fake_mvtec, recs, p, POL, MetricSpec(), SPEC)
        assert res["image_auroc"] == pytest.approx(expect)
        assert res["pixel_auroc"] == pytest.approx(expect)
        assert {c["stratum"] for c in res["strata"]} == {"small", "large"}
        assert len(rows) == len(test)


def test_tool_harness_end_to_end(fake_mvtec, isolated_env, monkeypatch):
    """acquire-marker -> profile_data -> evaluator_sanity via run_tool, then skip on rerun."""
    import profile_data
    import evaluator_sanity
    from anomaly_memory.io_utils import atomic_write_json
    local = isolated_env / "local" / "data"
    atomic_write_json(local / "mvtec_ad.extracted.json", {"dataset_root": str(fake_mvtec)})
    cfgdir = isolated_env / "cfg"
    cfgdir.mkdir()
    geom = "geometry: {name: t, resize: 32, crop: 28}\n"
    (cfgdir / "p.yaml").write_text("tool: profile_data\nschema_version: 1\nextracted_dirname: mvtec_ad\n"
                                   "categories: [bottle, carpet]\n" + geom +
                                   "strata: {area_fraction_edges: [0.0, 0.02, 1.0], labels: [s, l], "
                                   "min_images_per_cell: 1, min_images_pooled: 1}\n")
    (cfgdir / "e.yaml").write_text(
        "tool: evaluator_sanity\nschema_version: 1\nextracted_dirname: mvtec_ad\ncategories: [bottle, carpet]\n"
        "kinds: [constant, oracle_mask]\n" + geom + "metric: {}\n"
        "strata: {area_fraction_edges: [0.0, 0.02, 1.0], labels: [s, l], min_images_per_cell: 1, "
        "min_images_pooled: 1}\n")
    from anomaly_memory import runctx
    monkeypatch.setattr(runctx, "load_config", lambda name, schema, tool: __import__(
        "anomaly_memory.config", fromlist=["x"]).load_config(name, schema, tool, root=cfgdir))
    out = isolated_env / "out"
    assert runctx.run_tool(profile_data.SPEC, profile_data.body, ["--config", "p", "--out-root", str(out)]) == 0
    assert runctx.run_tool(evaluator_sanity.SPEC, evaluator_sanity.body,
                           ["--config", "e", "--out-root", str(out)]) == 0
    mf = next((out / "evaluator_sanity").glob("*/manifest.json"))
    m = json.loads(mf.read_text())
    assert m["complete"] is True and m["results"]["oracle_mask"]["au_pro"] == pytest.approx(1.0)
    assert m["results"]["constant"]["au_pro"] == pytest.approx(0.15)
    # rerun is skipped (complete identity exists)
    assert runctx.run_tool(evaluator_sanity.SPEC, evaluator_sanity.body,
                           ["--config", "e", "--out-root", str(out)]) == 0


def test_gpu_tool_refused_by_gate(isolated_env):
    """With the committed gate/allocation files, accelerator tools refuse before any work."""
    import subprocess
    import sys
    from conftest import REPO
    for tool, cfg in (("extract_features", "patchcore_features"), ("run_baseline", "patchcore_baseline")):
        r = subprocess.run([sys.executable, str(REPO / "tools" / f"{tool}.py"), "--config", cfg, "--out-root",
                            str(isolated_env / "out"), "--allow-dirty"], capture_output=True, text=True)
        assert r.returncode == 3, r.stdout + r.stderr
        assert "not approved" in r.stderr
    assert not (isolated_env / "out").exists()
