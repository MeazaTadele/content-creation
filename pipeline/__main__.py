"""Command line: python -m pipeline <command>. The Makefile wraps these.

  validate   check storyboard.json against the schema
  plan       dry run: what would be generated, nothing is called
  narration | timing | refsheet | keyframes | music   one stage
  radio      narration + timing + the radio cut (user test 1)
  film       every stage in order, then both exports
  smoke      one call per provider, logged to runs.jsonl
"""
from __future__ import annotations

import argparse
import shutil
import sys

from . import config, contract
from .manifest import Manifest
from .stages import assemble, keyframes, music, narration, refsheet, timing
from .stages.base import Context, say


_TMP_DIRS = []


def _ctx(dry: bool = False) -> Context:
    config.load_env()
    sb = contract.load()
    ctx = Context(sb=sb, manifest=Manifest(), dry_run=dry)
    _TMP_DIRS.append(ctx.tmp_dir)
    return ctx


def _report(name: str, s: dict) -> None:
    say(f"{name}: {s['generated']} generated, {s['cached']} cached" + (f", {s['failed']} failed" if s["failed"] else ""))


def cmd_validate(_):
    sb = contract.load()
    say(f"storyboard.json is valid: {len(sb['shots'])} shots, voice '{sb['voice']['use']}'"
        + (" (placeholder text)" if sb.get("placeholder") else ""))


def cmd_narration(_):
    ctx = _ctx()
    say("narration")
    _report("narration", narration.run(ctx))


def cmd_timing(_):
    timing.run(_ctx())


def cmd_refsheet(_):
    ctx = _ctx()
    say("reference sheet")
    _report("refsheet", refsheet.run(ctx))


def cmd_keyframes(_):
    ctx = _ctx()
    say("keyframes")
    _report("keyframes", keyframes.run(ctx))


def cmd_music(_):
    ctx = _ctx()
    tl = ctx.manifest.data["measured"].get("timeline") or timing.compute(ctx)
    say("music")
    _report("music", music.run(ctx, tl))


def cmd_radio(_):
    ctx = _ctx()
    say("narration (chosen voice)")
    _report("narration", narration.run(ctx, [ctx.sb["voice"]["use"]]))
    tl = timing.run(ctx)
    say("placeholder music")
    _ensure_placeholder_music(ctx, tl)
    say("radio cut")
    _report("radio cut", assemble.run_radio(ctx, tl))


def _ensure_placeholder_music(ctx, tl):
    sb = {**ctx.sb, "providers": {**ctx.sb["providers"], "music": "placeholder"},
          "music": {**ctx.sb["music"], "candidates": 1}}
    sub = Context(sb=sb, manifest=ctx.manifest, tmp_dir=ctx.tmp_dir)
    _report("music", music.run(sub, tl))


def cmd_film(_):
    ctx = _ctx()
    say("1/6 narration")
    _report("narration", narration.run(ctx))
    say("2/6 timing")
    tl = timing.run(ctx)
    say("3/6 reference sheet")
    _report("refsheet", refsheet.run(ctx))
    say("4/6 keyframes")
    _report("keyframes", keyframes.run(ctx))
    say("5/6 music")
    _report("music", music.run(ctx, tl))
    say("6/6 assembly")
    _report("assembly", assemble.run_film(ctx, tl))


def cmd_plan(_):
    ctx = _ctx(dry=True)
    say("plan (nothing is generated or called)")
    for name, fn in (("narration", lambda: narration.run(ctx)), ("refsheet", lambda: refsheet.run(ctx)),
                     ("keyframes", lambda: keyframes.run(ctx))):
        say(name)
        _report(name, fn())
    try:
        tl = timing.compute(ctx)
    except timing.TimingError as e:
        say(f"music and assembly: after narration ({e})")
        return
    say("music")
    _report("music", music.run(ctx, tl))
    say("assembly: reruns only the parts whose inputs changed")


def cmd_smoke(_):
    from . import smoke
    config.load_env()
    smoke.run()


def main(argv=None):
    p = argparse.ArgumentParser(prog="pipeline", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "plan", "narration", "timing", "refsheet", "keyframes", "music", "radio", "film", "smoke"):
        sub.add_parser(name)
    args = p.parse_args(argv)
    if not shutil.which("ffmpeg"):
        say("ffmpeg is not installed or not on PATH; see README.md")
        return 2
    try:
        globals()[f"cmd_{args.cmd}"](args)
    except contract.ContractError as e:
        say(str(e))
        return 1
    finally:
        for d in _TMP_DIRS:
            shutil.rmtree(d, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
