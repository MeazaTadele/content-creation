"""Keyframes: one still per shot and per aspect ratio, conditioned on the chosen references.

9:16 keyframes start the video clips; both ratios are used directly for Ken Burns shots
(decision 6), so a still shot never has to be cropped from the other ratio.
"""
from __future__ import annotations

from .. import calls, providers
from ..fingerprint import fingerprint
from . import refsheet
from .base import Context, Unit, check_stage_version, execute, out_path, rel, say

STAGE = "keyframes"
STAGE_VERSION = 3  # 3: style and exclusions placed first in long prompts
SIZES = {"9x16": (768, 1344), "16x9": (1344, 768)}


SCENE = ("One single full-frame illustrated scene from a film, with a real setting filling the whole frame. "
         "Not a character sheet: no plain background, no inset portraits, no multiple views of the same person")


def full_prompt(sb: dict, shot: dict) -> str:
    """The scene comes first; the reference images only say what the people look like (FAILURES.md F12)."""
    chars = {c["id"]: c for c in sb["characters"]}
    ids = [c for c in shot["image"].get("characters", []) if c in chars]
    who = ""
    if ids:
        who = ("The people look like the reference images (same face and clothes), placed into this scene: "
               + "; ".join(chars[c]["description"] for c in ids))
    scene = shot["image"]["prompt"]
    avoid = ""
    if "Not in the picture:" in scene:  # put the exclusions up front, where a long prompt can't cut them off
        scene, avoid = scene.split("Not in the picture:", 1)
        avoid = "Not in the picture:" + avoid
    # style and exclusions first, details after: if the text encoder truncates a long prompt, it loses
    # detail, not the look of the film
    parts = [SCENE, sb["style"]["block"], avoid, scene, who]
    return ". ".join(p.strip().rstrip(".") for p in parts if p and p.strip())


def units(ctx: Context) -> list[Unit]:
    sb = ctx.sb
    prov = providers.image(sb["providers"]["keyframes"])
    out = []
    for shot in sb["shots"]:
        refs = []
        for c in shot["image"].get("characters", []):
            p = refsheet.chosen(ctx, c)
            if p is None:
                say(f"  note: {shot['id']} uses '{c}' but no reference is chosen yet (characters[].reference_use)")
            else:
                refs.append(p)
        prompt = full_prompt(sb, shot)
        for ratio, size in SIZES.items():
            fp = fingerprint(STAGE, STAGE_VERSION, {"prompt": prompt, "negative": sb["style"].get("negative"),
                                                     "seed": shot["image"]["seed"], "size": size,
                                                     "refs": refs, "provider": prov.name, "model": prov.model})
            unit = f"{shot['id']}/{ratio}"
            dst = out_path(STAGE, unit, fp, "png")

            def run(tmp, tmp_dir, prompt=prompt, size=size, refs=refs, unit=unit, fp=fp, dst=dst, shot=shot):
                seed = shot["image"]["seed"]
                gen = lambda: prov.generate(prompt, sb["style"].get("negative"), seed, *size, refs, tmp, tmp_dir)
                if prov.is_model:
                    prov.check_ready()
                    calls.call_model(stage=STAGE, unit=unit, provider=prov.name, model=prov.model,
                                     params={"size": list(size), "refs": len(refs)}, seed=seed, fn=gen,
                                     fingerprint=fp, output=rel(dst), price=prov.price)
                else:
                    gen()
                return {"shot": shot["id"], "ratio": unit.split("/")[1]}

            out.append(Unit(STAGE, unit, fp, dst, f"{ratio} keyframe", run,
                            model_call=prov.is_model, provider=prov.name, model=prov.model))
    return out


def path(ctx: Context, shot_id: str, ratio: str):
    from ..config import ROOT
    e = ctx.manifest.get(STAGE, f"{shot_id}/{ratio}")
    return (ROOT / e["output"]) if e else None


KAGGLE_MODEL = "black-forest-labs/FLUX.2-klein-4B"


def run_kaggle(ctx: Context) -> dict:
    """Decision 32: the same FLUX.2 klein model on Kaggle's GPU, as one batch job."""
    import shutil
    from .. import kaggle, media
    from ..calls import log_job_unit
    sb = ctx.sb
    todo, files = [], {}
    for shot in sb["shots"]:
        refs = [p for c in shot["image"].get("characters", []) if (p := refsheet.chosen(ctx, c)) is not None]
        prompt = full_prompt(sb, shot)
        for ratio, size in SIZES.items():
            fp = fingerprint(STAGE, STAGE_VERSION, {"prompt": prompt, "seed": shot["image"]["seed"], "size": size,
                                                     "refs": refs, "provider": "kaggle-flux", "model": KAGGLE_MODEL})
            unit = f"{shot['id']}/{ratio}"
            if ctx.manifest.is_fresh(STAGE, unit, fp):
                say(f"  cached     {STAGE}/{unit}  ({fp[:8]})")
                continue
            names = []
            for r in refs:
                names.append(r.name)
                files[r.name] = r
            todo.append({"unit": unit.replace("/", "_"), "key": unit, "fingerprint": fp, "prompt": prompt,
                         "width": size[0], "height": size[1], "seed": shot["image"]["seed"], "refs": names,
                         "shot": shot["id"], "ratio": ratio})
    if not todo:
        return {"generated": 0, "cached": len(sb["shots"]) * 2, "failed": 0}
    if ctx.dry_run:
        for t in todo:
            say(f"  would run  {STAGE}/{t['key']}  (FLUX.2 klein on Kaggle)")
        return {"generated": len(todo), "cached": 0, "failed": 0}
    job_id, res = kaggle.run_job("keyframes", [{k: v for k, v in t.items() if k not in ("key", "shot", "ratio")} for t in todo],
                                 files, timeout=3 * 3600, gpu=True)
    stats = {"generated": 0, "cached": 0, "failed": 0}
    for t in todo:
        r = kaggle.read_result(res, t["unit"])
        dst = out_path(STAGE, t["key"], t["fingerprint"], "png")
        ok = bool(r and r.get("status") == "ok" and (res / r["output"]).exists())
        if ok:
            dst.parent.mkdir(parents=True, exist_ok=True)
            w, h = t["width"], t["height"]
            media.run(["-i", str(res / r["output"]), "-vf",
                       f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}", "-frames:v", "1", str(dst)])
            ctx.manifest.put(STAGE, t["key"], {"fingerprint": t["fingerprint"], "output": rel(dst), "status": "generated",
                                               "provider": "kaggle-flux", "model": KAGGLE_MODEL, "shot": t["shot"],
                                               "ratio": t["ratio"], "seconds": r.get("seconds"),
                                               **({"note": r["note"]} if r.get("note") else {})})
            stats["generated"] += 1
        else:
            stats["failed"] += 1
            say(f"  {STAGE}/{t['key']}: failed on Kaggle: {(r or {}).get('error', 'no result')[:150]}")
        log_job_unit(stage=STAGE, unit=t["key"], provider="kaggle-flux", model=KAGGLE_MODEL,
                     params={"size": [t["width"], t["height"]], "refs": len(t["refs"]), "steps": 4}, seed=t["seed"],
                     status=(r or {}).get("status", "missing"), latency_ms=int(((r or {}).get("seconds") or 0) * 1000),
                     gpu_seconds=(r or {}).get("gpu_seconds") or 0, fingerprint=t["fingerprint"],
                     output=rel(dst) if ok else None, job_id=job_id, error=(r or {}).get("error"))
    return stats


def run(ctx: Context) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    if ctx.sb["providers"]["keyframes"] == "kaggle-flux":
        return run_kaggle(ctx)
    # one image blocked by the provider's safety filter must not stop the other shots (FAILURES.md F10)
    return execute(ctx, units(ctx), keep_going=True)
