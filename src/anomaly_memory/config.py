"""Strict, typed experiment configs.

Each tool defines a dataclass schema. ``load_config`` reads
``configs/<name>.yaml``, rejects unknown or missing keys and wrong types, and
returns the validated object plus its canonical hash. A typo fails loudly.

Every config file has the top-level keys ``tool`` (must match the entrypoint)
and ``schema_version``; the remaining keys are validated against the schema.
"""

from __future__ import annotations

import dataclasses
import types
import typing
from pathlib import Path
from typing import Any, TypeVar

import yaml

from .io_utils import sha256_json
from .paths import configs_dir

T = TypeVar("T")


class ConfigError(ValueError):
    pass


def _type_name(tp: Any) -> str:
    return getattr(tp, "__name__", str(tp))


def _coerce(value: Any, tp: Any, where: str) -> Any:
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)
    if tp is Any:
        return value
    if origin in (typing.Union, types.UnionType):
        if value is None and type(None) in args:
            return None
        errors = []
        for a in args:
            if a is type(None):
                continue
            try:
                return _coerce(value, a, where)
            except ConfigError as e:
                errors.append(str(e))
        raise ConfigError(f"{where}: {value!r} matches none of {args}: {errors}")
    if origin is typing.Literal:
        if value not in args:
            raise ConfigError(f"{where}: {value!r} not in allowed values {args}")
        return value
    if origin in (list, tuple):
        if not isinstance(value, list):
            raise ConfigError(f"{where}: expected list, got {type(value).__name__}")
        inner = args[0] if args else Any
        return [_coerce(v, inner, f"{where}[{i}]") for i, v in enumerate(value)]
    if origin is dict:
        if not isinstance(value, dict):
            raise ConfigError(f"{where}: expected mapping, got {type(value).__name__}")
        vt = args[1] if len(args) == 2 else Any
        return {str(k): _coerce(v, vt, f"{where}.{k}") for k, v in value.items()}
    if dataclasses.is_dataclass(tp):
        return from_dict(tp, value, where)
    if tp is bool:
        if not isinstance(value, bool):
            raise ConfigError(f"{where}: expected bool, got {value!r}")
        return value
    if tp is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"{where}: expected int, got {value!r}")
        return value
    if tp is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{where}: expected float, got {value!r}")
        return float(value)
    if tp is str:
        if not isinstance(value, str):
            raise ConfigError(f"{where}: expected str, got {value!r}")
        return value
    raise ConfigError(f"{where}: unsupported schema type {_type_name(tp)}")


def from_dict(cls: type[T], data: Any, where: str = "config") -> T:
    if not isinstance(data, dict):
        raise ConfigError(f"{where}: expected mapping for {cls.__name__}, got {type(data).__name__}")
    hints = typing.get_type_hints(cls)
    fields = {f.name: f for f in dataclasses.fields(cls)}
    unknown = sorted(set(data) - set(fields))
    if unknown:
        raise ConfigError(f"{where}: unknown key(s) {unknown} for {cls.__name__}; allowed: {sorted(fields)}")
    kwargs = {}
    for name, f in fields.items():
        if name in data:
            kwargs[name] = _coerce(data[name], hints[name], f"{where}.{name}")
        elif f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
            raise ConfigError(f"{where}: missing required key {name!r} for {cls.__name__}")
    obj = cls(**kwargs)
    validate = getattr(obj, "validate", None)
    if callable(validate):
        validate()
    return obj


def to_dict(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj):
        return {f.name: to_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, list):
        return [to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


@dataclasses.dataclass(frozen=True)
class LoadedConfig(typing.Generic[T]):
    name: str
    path: Path
    tool: str
    schema_version: int
    cfg: T
    hash: str  # sha256 over tool, schema_version and the validated values

    def as_dict(self) -> dict:
        return {"name": self.name, "tool": self.tool, "schema_version": self.schema_version,
                "values": to_dict(self.cfg), "hash": self.hash}


def resolve_config_path(name: str, root: Path | None = None) -> Path:
    root = root or configs_dir()
    p = Path(name)
    if p.suffix in (".yaml", ".yml") and p.exists():
        return p
    candidate = root / f"{name}.yaml"
    if not candidate.exists():
        available = sorted(x.stem for x in root.glob("*.yaml"))
        raise ConfigError(f"config {name!r} not found in {root}; available: {available}")
    return candidate


def load_config(name: str, schema: type[T], tool: str, root: Path | None = None) -> LoadedConfig[T]:
    path = resolve_config_path(name, root)
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    raw = dict(raw)
    file_tool = raw.pop("tool", None)
    version = raw.pop("schema_version", None)
    if file_tool != tool:
        raise ConfigError(f"{path}: config is for tool {file_tool!r}, not {tool!r}")
    if not isinstance(version, int):
        raise ConfigError(f"{path}: schema_version must be an int")
    expected_version = getattr(schema, "SCHEMA_VERSION", 1)
    if version != expected_version:
        raise ConfigError(f"{path}: schema_version {version} != tool's {expected_version}")
    cfg = from_dict(schema, raw, where=path.stem)
    h = sha256_json({"tool": tool, "schema_version": version, "values": to_dict(cfg)})
    return LoadedConfig(name=path.stem, path=path, tool=tool, schema_version=version, cfg=cfg, hash=h)
