import dataclasses
from typing import Literal

import pytest

from anomaly_memory.config import ConfigError, from_dict, load_config


@dataclasses.dataclass
class Inner:
    a: int
    mode: Literal["x", "y"] = "x"


@dataclasses.dataclass
class Schema:
    SCHEMA_VERSION = 1
    name: str
    inner: Inner
    vals: list[float]
    opt: int | None = None


def test_valid_and_coercion():
    s = from_dict(Schema, {"name": "n", "inner": {"a": 1}, "vals": [1, 2.5]})
    assert s.vals == [1.0, 2.5] and s.inner.mode == "x"


@pytest.mark.parametrize("bad", [
    {"name": "n", "inner": {"a": 1}, "vals": [], "typo": 1},          # unknown key
    {"name": "n", "inner": {"a": 1}},                                  # missing key
    {"name": "n", "inner": {"a": "1"}, "vals": []},                    # wrong type
    {"name": "n", "inner": {"a": True}, "vals": []},                   # bool is not int
    {"name": "n", "inner": {"a": 1, "mode": "z"}, "vals": []},         # literal
])
def test_invalid_fails_loudly(bad):
    with pytest.raises(ConfigError):
        from_dict(Schema, bad)


def test_load_config_checks_tool_and_hash(tmp_path):
    (tmp_path / "c.yaml").write_text("tool: t\nschema_version: 1\nname: n\ninner: {a: 1}\nvals: [1]\n")
    a = load_config("c", Schema, "t", root=tmp_path)
    b = load_config("c", Schema, "t", root=tmp_path)
    assert a.hash == b.hash
    with pytest.raises(ConfigError):
        load_config("c", Schema, "other_tool", root=tmp_path)
    (tmp_path / "c2.yaml").write_text("tool: t\nschema_version: 1\nname: n\ninner: {a: 2}\nvals: [1]\n")
    assert load_config("c2", Schema, "t", root=tmp_path).hash != a.hash


def test_all_repo_configs_validate():
    """Every committed config loads against its tool's schema."""
    import importlib
    from pathlib import Path

    import yaml
    root = Path(__file__).resolve().parents[1] / "configs"
    for p in sorted(root.glob("*.yaml")):
        tool = yaml.safe_load(p.read_text())["tool"]
        mod = importlib.import_module(tool)
        load_config(p.stem, mod.SPEC.schema, tool)
