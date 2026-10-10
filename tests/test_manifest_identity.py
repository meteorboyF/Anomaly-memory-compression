import json

import pytest

from anomaly_memory.identity import experiment_identity
from anomaly_memory.manifest import ManifestError, artifact_entry, load_manifest, write_manifest


def _base(tmp_path):
    f = tmp_path / "a.json"
    f.write_text("{}")
    return {"tool": "t", "run_id": "r", "identity": {"full": "x"}, "config": {}, "git": {"sha": "abc", "dirty": False},
            "seed": {}, "environment": {}, "hardware": {}, "started_utc": "now",
            "artifacts": [artifact_entry(tmp_path, f)]}


def test_complete_last_and_roundtrip(tmp_path):
    write_manifest(tmp_path, _base(tmp_path), complete=True)
    m = json.loads((tmp_path / "manifest.json").read_text())
    assert list(m)[-1] == "complete" and m["complete"] is True
    load_manifest(tmp_path, expect={"identity.full": "x"})
    with pytest.raises(ManifestError):
        load_manifest(tmp_path, expect={"identity.full": "y"})


def test_incomplete_and_tampered_refused(tmp_path):
    write_manifest(tmp_path, _base(tmp_path), complete=False)
    with pytest.raises(ManifestError, match="not complete"):
        load_manifest(tmp_path)
    write_manifest(tmp_path, _base(tmp_path), complete=True)
    (tmp_path / "a.json").write_text('{"x": 1}')
    with pytest.raises(ManifestError):
        load_manifest(tmp_path)


def test_missing_artifact_and_mirror_scope(tmp_path):
    write_manifest(tmp_path, _base(tmp_path), complete=True)
    (tmp_path / "a.json").unlink()
    with pytest.raises(ManifestError, match="missing"):
        load_manifest(tmp_path)
    load_manifest(tmp_path, artifact_scope="present")


def test_dirty_not_citable(tmp_path):
    b = _base(tmp_path)
    b["git"] = {"sha": "abc", "dirty": True}
    write_manifest(tmp_path, b, complete=True)
    load_manifest(tmp_path)
    with pytest.raises(ManifestError, match="citable"):
        load_manifest(tmp_path, require_clean_git=True)


def test_identity_tracks_science_code(tmp_path, monkeypatch):
    mod = tmp_path / "sci_mod_x.py"
    mod.write_text("A = 1\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    a = experiment_identity("cfg", ["sci_mod_x"])
    mod.write_text("A = 2\n")
    b = experiment_identity("cfg", ["sci_mod_x"])
    c = experiment_identity("cfg2", ["sci_mod_x"])
    assert a["id"] != b["id"] != c["id"]
    assert experiment_identity("cfg", ["sci_mod_x"])["id"] == b["id"]
