"""Moving shots: Wan 2.2 TI2V-5B image-to-video on Kaggle (decision 5), with the Ken Burns fallback.

Each shot's clip is fingerprinted by its 9:16 keyframe, motion prompt, seed and generation
settings, but not by the shot's duration: assembly trims or holds the clip to length, so a
narration edit never spends GPU time. A shot gets at most MAX_ATTEMPTS automatic tries
(decision 9); after that, or when motion.kenburns is set, assembly uses a Ken Burns move.
"""
from __future__ import annotations

import shutil

from .. import kaggle
from ..calls import log_job_unit
from ..config import ROOT
from ..fingerprint import fingerprint
from . import keyframes
from .base import Context, check_stage_version, out_path, rel, say

STAGE = "shots"
STAGE_VERSION = 2  # 2: memory settings for the T4 (FAILURES.md F5)
MAX_ATTEMPTS = 2
MODEL = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
SETTINGS = {"width": 480, "height": 832, "frames": 49, "fps": 24, "steps": 30, "guidance": 5.0,
            "offload": "sequential",
            "negative": "blurry, distorted face, extra fingers, text, watermark, flicker"}


def plan(ctx: Context) -> list[dict]:
    """Units that need a clip: not cached, not forced to Ken Burns, attempts left."""
    out = []
    for shot in ctx.sb["shots"]:
        if shot["motion"].get("kenburns"):
            continue
        kf = keyframes.path(ctx, shot["id"], "9x16")
        if kf is None:
            continue
        inputs = {"keyframe": kf, "prompt": shot["motion"]["prompt"], "seed": shot["motion"]["seed"],
                  "model": MODEL, "settings": SETTINGS}
        if shot["motion"].get("negative"):  # only shots that set it get a different fingerprint
            inputs["negative"] = shot["motion"]["negative"]
        fp = fingerprint(STAGE, STAGE_VERSION, inputs)
        e = ctx.manifest.get(STAGE, shot["id"])
        if e and e.get("fingerprint") == fp:
            if e.get("status") == "generated" and (ROOT / e["output"]).exists():
                continue
            if e.get("attempts", 0) >= MAX_ATTEMPTS:
                continue
        out.append({"shot": shot, "fingerprint": fp, "keyframe": kf,
                    "attempts": (e or {}).get("attempts", 0) if e and e.get("fingerprint") == fp else 0})
    return out


def run(ctx: Context) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    if ctx.sb["providers"]["shots"] == "none":
        say("  video clips are switched off (providers.shots = none): every shot uses Ken Burns")
        return {"generated": 0, "cached": 0, "failed": 0}
    todo = plan(ctx)
    if not todo:
        say("  every shot has a clip, or is set to Ken Burns, or has used its attempts")
        return {"generated": 0, "cached": len(ctx.sb["shots"]), "failed": 0}
    if ctx.dry_run:
        for t in todo:
            say(f"  would run  shots/{t['shot']['id']}  (Wan 2.2 on Kaggle)")
        return {"generated": len(todo), "cached": 0, "failed": 0}
    units, files = [], {}
    for t in todo:
        name = f"{t['shot']['id']}_keyframe.png"
        files[name] = t["keyframe"]
        units.append({"unit": t["shot"]["id"], "fingerprint": t["fingerprint"], "keyframe": name,
                      "prompt": t["shot"]["motion"]["prompt"], "seed": t["shot"]["motion"]["seed"],
                      **({"negative": SETTINGS["negative"] + ", " + t["shot"]["motion"]["negative"]}
                         if t["shot"]["motion"].get("negative") else {})})
    job_id, results = kaggle.run_job(STAGE, units, files, settings=SETTINGS)
    stats = {"generated": 0, "cached": 0, "failed": 0}
    for t in todo:
        sid, fp = t["shot"]["id"], t["fingerprint"]
        r = kaggle.read_result(results, sid)
        dst = out_path(STAGE, sid, fp, "mp4")
        attempts = t["attempts"] + 1
        if r and r.get("status") == "ok" and (results / r["output"]).exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(results / r["output"], dst)
            ctx.manifest.put(STAGE, sid, {"fingerprint": fp, "output": rel(dst), "status": "generated",
                                          "provider": "kaggle-wan22", "model": MODEL, "attempts": attempts,
                                          "seconds": r.get("seconds"), "gpu_seconds": r.get("gpu_seconds")})
            stats["generated"] += 1
        else:
            reason = (r or {}).get("error", "no result returned (job failed or timed out)")
            ctx.manifest.put(STAGE, sid, {"fingerprint": fp, "output": None, "status": "fallback",
                                          "reason": reason, "attempts": attempts, "provider": "kaggle-wan22"})
            say(f"  shots/{sid}: no clip ({reason[:120]}); Ken Burns will be used"
                + (" from now on" if attempts >= MAX_ATTEMPTS else f" unless the next run succeeds"))
            stats["failed"] += 1
        log_job_unit(stage=STAGE, unit=sid, provider="kaggle-wan22", model=MODEL, params=SETTINGS,
                     seed=t["shot"]["motion"]["seed"], status=(r or {}).get("status", "missing"),
                     latency_ms=int(((r or {}).get("seconds") or 0) * 1000),
                     gpu_seconds=(r or {}).get("gpu_seconds") or 0, fingerprint=fp,
                     output=rel(dst) if dst.exists() else None,
                     job_id=job_id, error=(r or {}).get("error"))
    return stats


def clip_path(ctx: Context, shot_id: str):
    e = ctx.manifest.get(STAGE, shot_id)
    if not e or e.get("status") != "generated" or not e.get("output"):
        return None
    p = ROOT / e["output"]
    return p if p.exists() else None
