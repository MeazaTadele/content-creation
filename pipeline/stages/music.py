"""Music: candidates for each cue (decision 8: a quiet "before" cue and a warm "Easter morning" cue).

Cue lengths come from the timing, rounded up to the next 15 s (MUSIC_LENGTH_BUCKET), so small
timing changes don't regenerate music; assembly trims and fades. ACE-Step runs as a Kaggle batch
job; the placeholder provider runs here, for the radio cut and offline tests.
"""
from __future__ import annotations

import math

from .. import providers
from ..config import MUSIC_LENGTH_BUCKET, ROOT
from ..fingerprint import fingerprint
from .base import Context, Unit, check_stage_version, execute, out_path

STAGE = "music"
STAGE_VERSION = 1
CUE_OVERLAP = 2.0  # seconds two cues overlap when they crossfade
TAIL_PAD = 1.0


def cue_spans(sb: dict, timeline: dict) -> list[dict]:
    """Start and needed length of each cue on the film's timeline (end card included)."""
    starts = {s["id"]: s["start"] for s in timeline["shots"]}
    cues = sb["music"]["cues"]
    spans = []
    for i, c in enumerate(cues):
        start = starts[c["from_shot"]]
        if i > 0:
            start = max(0.0, start - CUE_OVERLAP / 2)
        if i + 1 < len(cues):
            end = starts[cues[i + 1]["from_shot"]] + CUE_OVERLAP / 2
        else:
            end = timeline["total_seconds"] + TAIL_PAD
        need = end - start
        spans.append({"id": c["id"], "start": round(start, 3), "seconds": round(need, 3),
                      "generate_seconds": math.ceil(need / MUSIC_LENGTH_BUCKET) * MUSIC_LENGTH_BUCKET})
    return spans


def units(ctx: Context, timeline: dict) -> list[Unit]:
    sb = ctx.sb
    name = sb["providers"]["music"]
    if name != "placeholder":
        return []  # produced by the Kaggle music job
    prov = providers.music(name)
    n = sb["music"].get("candidates", 3)
    out = []
    for cue, span in zip(sb["music"]["cues"], cue_spans(sb, timeline)):
        for k in range(n):
            seed = cue.get("seed", 7) + k
            fp = fingerprint(STAGE, STAGE_VERSION, {
                "caption": cue["caption"], "bpm": cue.get("bpm"), "key": cue.get("key"),
                "instrumental": cue.get("instrumental", True), "seed": seed,
                "seconds": span["generate_seconds"], "provider": prov.name, "model": prov.model})
            unit = f"{cue['id']}/{k}"
            dst = out_path(STAGE, unit, fp, "wav")

            def run(tmp, tmp_dir, cue=cue, span=span, seed=seed, unit=unit):
                prov.compose(cue["caption"], span["generate_seconds"], cue.get("bpm"), cue.get("key"), seed,
                             cue.get("instrumental", True), tmp, tmp_dir)
                return {"cue": cue["id"], "candidate": int(unit.split("/")[1]), "seconds": span["generate_seconds"]}

            out.append(Unit(STAGE, unit, fp, dst, f"{span['generate_seconds']:.0f} s candidate", run,
                            model_call=prov.is_model, provider=prov.name, model=prov.model))
    return out


def chosen(ctx: Context, cue: dict):
    k = cue.get("use")
    k = 0 if k is None else k
    e = ctx.manifest.get(STAGE, f"{cue['id']}/{k}")
    return (ROOT / e["output"]) if e else None


def run(ctx: Context, timeline: dict) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    return execute(ctx, units(ctx, timeline))
