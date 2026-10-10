"""Common harness for every ``tools/*.py`` entrypoint.

Responsibilities, in order:
1. parse ``--config`` (required) and standard flags; load + validate config;
2. record the git SHA at process start (dirty checkouts are marked, and are
   refused for accelerator jobs unless ``--allow-dirty``);
3. budget/phase preflight (``budget.preflight``);
4. compute the experiment identity (config hash + scientific code hash);
5. skip if a complete, valid manifest with that identity already exists;
6. set the seed; prepare a local work dir (resumable only with ``--resume``
   and a matching identity) and the durable Drive run dir;
7. run the tool body; copy registered artifacts atomically to the durable
   dir, hash them, and write the manifest with ``complete: true`` last.
"""

from __future__ import annotations

import argparse
import dataclasses
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable

from .budget import BudgetRefused, TimeGuard, preflight, session_event
from .config import ConfigError, LoadedConfig, load_config
from .identity import experiment_identity
from .io_utils import atomic_copy, atomic_write_json, read_json
from .manifest import ManifestError, artifact_entry, load_manifest, utcnow, write_manifest
from .paths import drive_dir, drive_root, is_drive_mounted, local_root
from .provenance import environment_info, git_info, hardware_info, pip_freeze_hash
from .seed import set_seed

EXIT_OK, EXIT_ERROR, EXIT_REFUSED, EXIT_CONFIG = 0, 1, 3, 4


@dataclasses.dataclass
class ToolSpec:
    name: str
    schema: type
    tier: str  # "cpu" | "gpu"
    phase: str  # "phase0" | "phase1" | "phase2"
    science_modules: list[str]
    durable_kind: str = "manifests"  # key of paths.DRIVE_SUBDIRS
    est_hours: Callable[[Any], float] = lambda cfg: 0.0
    description: str = ""
    # False for idempotent tools that must re-check external state every time
    # (e.g. acquisition, which must restage data on a fresh runtime).
    skip_if_complete: bool = True


@dataclasses.dataclass
class RunContext:
    spec: ToolSpec
    loaded: LoadedConfig
    args: argparse.Namespace
    identity: dict
    git: dict
    work_dir: Path
    durable_dir: Path
    guard: TimeGuard
    seed_info: dict
    preflight_msg: str
    allocation_id: str | None
    artifacts: list[tuple[Path, str]] = dataclasses.field(default_factory=list)
    extra_manifest: dict = dataclasses.field(default_factory=dict)

    @property
    def cfg(self) -> Any:
        return self.loaded.cfg

    @property
    def smoke(self) -> bool:
        return bool(self.args.smoke)

    def register(self, path: Path, kind: str = "file") -> Path:
        """Register a file in ``work_dir`` to be copied to Drive and hashed."""
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"cannot register missing artifact {path}")
        self.artifacts.append((path, kind))
        return path

    def log(self, msg: str) -> None:
        print(f"[{self.spec.name}] {msg}", flush=True)

    def persist_partial(self, path: Path) -> Path:
        """Copy a resumable checkpoint to ``durable_dir/_partial`` atomically,
        so a lost runtime can resume. Partial files are never artifacts."""
        rel = Path(path).relative_to(self.work_dir)
        dst = self.durable_dir / "_partial" / rel
        atomic_copy(path, dst)
        atomic_write_json(self.durable_dir / "_partial" / "identity.json", {"identity": self.identity["full"]})
        return dst


def _parser(spec: ToolSpec) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=spec.name, description=spec.description)
    p.add_argument("--config", required=True, help="config name in configs/ (without .yaml)")
    p.add_argument("--resume", action="store_true", help="resume a partial run with the same identity")
    p.add_argument("--smoke", action="store_true", help="tiny end-to-end run; never citable")
    p.add_argument("--out-root", default=None, help="override the durable output root (default: Drive)")
    p.add_argument("--allow-dirty", action="store_true", help="permit a dirty checkout (never citable)")
    p.add_argument("--force", action="store_true", help="re-run even if a complete manifest exists")
    return p


def _durable_root(spec: ToolSpec, out_root: str | None) -> Path:
    if out_root:
        return Path(out_root)
    if not (is_drive_mounted() or drive_root().exists()):
        raise BudgetRefused(f"Drive root {drive_root()} is not available. Mount Drive in Colab, set "
                            "AMC_DRIVE_ROOT, or pass --out-root for a local (non-durable) run.")
    return drive_dir(spec.durable_kind)


def _prepare_work_dir(work_dir: Path, durable_dir: Path, identity: dict, resume: bool, log) -> None:
    marker = work_dir / ".identity.json"
    if work_dir.exists():
        same = marker.exists() and read_json(marker).get("identity") == identity["full"]
        if resume and same:
            log(f"resuming local partial work in {work_dir}")
            return
        reason = "identity mismatch" if not same else "--resume not given"
        log(f"discarding local partial work ({reason}): {work_dir}")
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    atomic_write_json(marker, {"identity": identity["full"]})
    partial = durable_dir / "_partial"
    if resume and partial.is_dir():
        pid = partial / "identity.json"
        if not pid.exists() or read_json(pid).get("identity") != identity["full"]:
            raise ManifestError(f"durable partial checkpoint at {partial} has a different identity; "
                                "refusing to resume across code/config changes")
        for f in partial.rglob("*"):
            if f.is_file() and f.name != "identity.json":
                dst = work_dir / f.relative_to(partial)
                atomic_copy(f, dst)
        log(f"restored durable partial checkpoint from {partial}")


def run_tool(spec: ToolSpec, body: Callable[[RunContext], dict], argv: list[str] | None = None) -> int:
    args = _parser(spec).parse_args(argv)
    t0 = time.time()
    git = git_info()
    print(f"[{spec.name}] git {git['sha']}{' (DIRTY)' if git['dirty'] else ''} branch={git['branch']}", flush=True)
    try:
        loaded = load_config(args.config, spec.schema, spec.name)
    except ConfigError as e:
        print(f"[{spec.name}] CONFIG ERROR: {e}", file=sys.stderr, flush=True)
        return EXIT_CONFIG
    try:
        if spec.tier == "gpu" and git["dirty"] and not args.allow_dirty:
            raise BudgetRefused("refusing an accelerator job from a dirty checkout; commit first "
                                "(or --allow-dirty for a non-citable debug run)")
        pf = preflight(spec.tier, loaded.name, spec.phase, spec.est_hours(loaded.cfg), smoke=args.smoke)
        print(f"[{spec.name}] preflight: {pf.message}", flush=True)
        identity = experiment_identity(loaded.hash, spec.science_modules, extra={"smoke": bool(args.smoke)})
        run_id = f"{loaded.name}{'-smoke' if args.smoke else ''}-{identity['id']}"
        durable_dir = _durable_root(spec, args.out_root) / spec.name / run_id
        print(f"[{spec.name}] identity {identity['id']} -> {durable_dir}", flush=True)
        if spec.skip_if_complete and not args.force and (durable_dir / "manifest.json").exists():
            try:
                load_manifest(durable_dir, expect={"identity.full": identity["full"]})
                print(f"[{spec.name}] complete verified run already exists; skipping. (--force to redo)", flush=True)
                return EXIT_OK
            except ManifestError as e:
                print(f"[{spec.name}] existing manifest not usable ({e}); re-running", flush=True)
        work_dir = local_root() / "runs" / spec.name / run_id
        log = lambda m: print(f"[{spec.name}] {m}", flush=True)  # noqa: E731
        _prepare_work_dir(work_dir, durable_dir, identity, args.resume, log)
        seed = int(getattr(loaded.cfg, "seed", 0))
        seed_info = set_seed(seed)
        ctx = RunContext(spec=spec, loaded=loaded, args=args, identity=identity, git=git, work_dir=work_dir,
                         durable_dir=durable_dir, guard=TimeGuard(pf.deadline_monotonic), seed_info=seed_info,
                         preflight_msg=pf.message, allocation_id=pf.allocation_id)
    except (BudgetRefused, ManifestError) as e:
        print(f"[{spec.name}] REFUSED: {e}", file=sys.stderr, flush=True)
        return EXIT_REFUSED

    base = {
        "tool": spec.name, "run_id": run_id, "identity": identity, "config": loaded.as_dict(),
        "git": git, "seed": seed_info, "smoke": bool(args.smoke), "phase": spec.phase, "tier": spec.tier,
        "allocation_id": pf.allocation_id, "environment": environment_info(), "hardware": hardware_info(),
        "started_utc": utcnow(), "artifacts": [],
    }
    write_manifest(work_dir, base, complete=False)
    status = "failed"
    try:
        result = body(ctx) or {}
        base["environment"] = environment_info()  # body may have imported torch etc.
        freeze = pip_freeze_hash()
        (work_dir / "pip_freeze.txt").write_text(freeze.pop("text", "") or "")
        ctx.register(work_dir / "pip_freeze.txt", kind="environment")
        base["environment"]["pip_freeze"] = freeze
        entries = []
        for path, kind in ctx.artifacts:
            rel = path.relative_to(work_dir)
            atomic_copy(path, durable_dir / rel)
            entries.append(artifact_entry(durable_dir, durable_dir / rel, kind))
        base.update(ctx.extra_manifest)
        base["results"] = result
        base["artifacts"] = entries
        base["wall_seconds"] = round(time.time() - t0, 3)
        write_manifest(durable_dir, base, complete=True)
        load_manifest(durable_dir, expect={"identity.full": identity["full"]})  # re-validate what we wrote
        shutil.rmtree(durable_dir / "_partial", ignore_errors=True)
        status = "complete"
        print(f"[{spec.name}] COMPLETE: manifest verified at {durable_dir / 'manifest.json'}", flush=True)
        return EXIT_OK
    except BudgetRefused as e:
        print(f"[{spec.name}] REFUSED: {e}", file=sys.stderr, flush=True)
        return EXIT_REFUSED
    except Exception:
        traceback.print_exc()
        print(f"[{spec.name}] FAILED. Partial work kept at {work_dir}; nothing was marked complete. "
              "Fix, refresh code, and rerun (add --resume only if the identity is unchanged).",
              file=sys.stderr, flush=True)
        return EXIT_ERROR
    finally:
        if spec.tier == "gpu" and pf.allocation_id:
            try:
                session_event("job_end", pf.allocation_id, run_id=run_id, status=status,
                              wall_hours=(time.time() - t0) / 3600)
            except OSError as e:
                print(f"[{spec.name}] WARNING: could not append usage log: {e}", file=sys.stderr)


def phase_blocked_body(what: str) -> Callable[[RunContext], dict]:
    """Body for entrypoints whose implementation waits for gate approval."""
    def body(ctx: RunContext) -> dict:
        raise NotImplementedError(f"{what} is not implemented yet: it belongs to a phase that has not "
                                  "been approved. No compute was used.")
    return body
