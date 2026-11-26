"""Music: candidates for each cue (decision 8: a quiet "before" cue and a warm "Easter morning" cue).

Cue lengths come from the timing, rounded up to the next 15 s (MUSIC_LENGTH_BUCKET), so small
timing changes don't regenerate music; assembly trims and fades. ACE-Step runs as a Kaggle batch
job; the placeholder provider runs here, for the radio cut and offline tests.
"""
from __future__ import annotations

import math
import shutil

from .. import providers
from ..config import MUSIC_LENGTH_BUCKET, ROOT
from ..fingerprint import fingerprint
from .base import Context, Unit, check_stage_version, execute, out_path, rel, say

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


KAGGLE_MODEL = "ACE-Step/acestep-v15-turbo"


def run_kaggle(ctx: Context, timeline: dict) -> dict:
    """ACE-Step 1.5 on Kaggle's GPU: every cue's candidates in one batch job."""
    from .. import kaggle
    from ..calls import log_job_unit
    sb = ctx.sb
    n = sb["music"].get("candidates", 3)
    todo = []
    for cue, span in zip(sb["music"]["cues"], cue_spans(sb, timeline)):
        for k in range(n):
            seed = cue.get("seed", 7) + k
            fp = fingerprint(STAGE, STAGE_VERSION, {
                "caption": cue["caption"], "bpm": cue.get("bpm"), "key": cue.get("key"),
                "instrumental": cue.get("instrumental", True), "seed": seed,
                "seconds": span["generate_seconds"], "provider": "kaggle-acestep", "model": KAGGLE_MODEL})
            key = f"{cue['id']}/{k}"
            if ctx.manifest.is_fresh(STAGE, key, fp):
                say(f"  cached     {STAGE}/{key}  ({fp[:8]})")
                continue
            todo.append({"unit": key.replace("/", "_"), "key": key, "fingerprint": fp, "caption": cue["caption"],
                         "bpm": cue.get("bpm"), "key_scale": cue.get("key"), "instrumental": cue.get("instrumental", True),
                         "seconds": span["generate_seconds"], "seed": seed, "cue": cue["id"], "candidate": k})
    if not todo:
        return {"generated": 0, "cached": len(sb["music"]["cues"]) * n, "failed": 0}
    if ctx.dry_run:
        for t in todo:
            say(f"  would run  {STAGE}/{t['key']}  ({t['seconds']} s, ACE-Step on Kaggle)")
        return {"generated": len(todo), "cached": 0, "failed": 0}
    job_units = [{"unit": t["unit"], "fingerprint": t["fingerprint"], "caption": t["caption"], "bpm": t["bpm"],
                  "key": t["key_scale"], "instrumental": t["instrumental"], "seconds": t["seconds"], "seed": t["seed"]}
                 for t in todo]
    job_id, res = kaggle.run_job("music", job_units, {}, timeout=2 * 3600, gpu=True)
    stats = {"generated": 0, "cached": 0, "failed": 0}
    for t in todo:
        r = kaggle.read_result(res, t["unit"])
        dst = out_path(STAGE, t["key"], t["fingerprint"], "wav")
        ok = bool(r and r.get("status") == "ok" and (res / r["output"]).exists())
        if ok:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(res / r["output"], dst)
            ctx.manifest.put(STAGE, t["key"], {"fingerprint": t["fingerprint"], "output": rel(dst), "status": "generated",
                                               "provider": "kaggle-acestep", "model": KAGGLE_MODEL, "cue": t["cue"],
                                               "candidate": t["candidate"], "seconds": t["seconds"]})
            stats["generated"] += 1
        else:
            stats["failed"] += 1
            say(f"  {STAGE}/{t['key']}: failed on Kaggle: {(r or {}).get('error', 'no result')[:150]}")
        log_job_unit(stage=STAGE, unit=t["key"], provider="kaggle-acestep", model=KAGGLE_MODEL,
                     params={"seconds": t["seconds"], "bpm": t["bpm"], "key": t["key_scale"], "steps": 8},
                     seed=t["seed"], status=(r or {}).get("status", "missing"),
                     latency_ms=int(((r or {}).get("seconds") or 0) * 1000), gpu_seconds=(r or {}).get("gpu_seconds") or 0,
                     fingerprint=t["fingerprint"], output=rel(dst) if ok else None, job_id=job_id, error=(r or {}).get("error"))
    return stats


def run(ctx: Context, timeline: dict) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    if ctx.sb["providers"]["music"] == "kaggle-acestep":
        return run_kaggle(ctx, timeline)
    return execute(ctx, units(ctx, timeline))
