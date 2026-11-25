"""What every stage shares: units of work, cache checks, atomic outputs, manifest updates."""
from __future__ import annotations

import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .. import atomic
from ..config import OUTPUTS, ROOT
from ..fingerprint import file_sha256, short
from ..manifest import Manifest


@dataclass
class Context:
    sb: dict
    manifest: Manifest
    tmp_dir: Path = field(default_factory=lambda: Path(tempfile.mkdtemp(prefix="heritage-")))
    dry_run: bool = False

    def shot(self, shot_id: str) -> dict:
        return next(s for s in self.sb["shots"] if s["id"] == shot_id)


@dataclass
class Unit:
    stage: str
    unit: str
    fingerprint: str
    output: Path
    describe: str
    run: Callable[[Path, Path], dict]    # (tmp_output, tmp_dir) -> extra manifest fields
    model_call: bool = False
    provider: str = ""
    model: str = ""


def out_path(stage: str, unit: str, fp: str, ext: str) -> Path:
    return OUTPUTS / stage / f"{unit}__{short(fp)}.{ext}"


def rel(p: Path) -> str:
    return str(p.resolve().relative_to(ROOT))


def say(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def execute(ctx: Context, units: list[Unit], keep_going: bool = False) -> dict:
    """Run every unit whose fingerprint is not already in the manifest. Returns counts.
    keep_going: a unit that fails is reported and skipped, and the others still run."""
    stats = {"cached": 0, "generated": 0, "failed": 0}
    for u in units:
        if ctx.manifest.is_fresh(u.stage, u.unit, u.fingerprint):
            stats["cached"] += 1
            say(f"  cached     {u.stage}/{u.unit}  ({short(u.fingerprint)})")
            continue
        if ctx.dry_run:
            stats["generated"] += 1
            say(f"  would run  {u.stage}/{u.unit}  ({u.describe})")
            continue
        say(f"  generating {u.stage}/{u.unit}  ({u.describe})")
        tmp = atomic.tmp_path_for(u.output)
        t0 = time.monotonic()
        try:
            extra = u.run(tmp, ctx.tmp_dir) or {}
            atomic.commit(tmp, u.output)
        except Exception as e:
            tmp.unlink(missing_ok=True)
            stats["failed"] += 1
            if not keep_going:
                raise
            say(f"  FAILED     {u.stage}/{u.unit}: {str(e)[:160]}")
            continue
        ctx.manifest.put(u.stage, u.unit, {
            "fingerprint": u.fingerprint, "output": rel(u.output), "status": "generated",
            "provider": u.provider, "model": u.model, "seconds": round(time.monotonic() - t0, 2),
            **extra,
        })
        stats["generated"] += 1
    return stats


def check_stage_version(manifest: Manifest, stage: str, version: int, module_file: str) -> None:
    """Decision 23: warn when a stage's code changed but its STAGE_VERSION did not."""
    sha = file_sha256(Path(module_file))
    prev = manifest.data["stage_sources"].get(stage)
    if prev and prev["version"] == version and prev["sha"] != sha:
        say(f"  WARNING: {stage} code changed since the last run but STAGE_VERSION is still {version}. "
            f"If the change affects outputs, raise STAGE_VERSION in {Path(module_file).name}.")
    manifest.data["stage_sources"][stage] = {"version": version, "sha": sha}
    manifest.save()
