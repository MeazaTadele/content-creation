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


def run(ctx: Context) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    # one image blocked by the provider's safety filter must not stop the other shots (FAILURES.md F10)
    return execute(ctx, units(ctx), keep_going=True)
