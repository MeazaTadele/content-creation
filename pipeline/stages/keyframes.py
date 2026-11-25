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
STAGE_VERSION = 1
SIZES = {"9x16": (768, 1344), "16x9": (1344, 768)}


def full_prompt(sb: dict, shot: dict) -> str:
    chars = {c["id"]: c for c in sb["characters"]}
    who = " ".join(chars[c]["description"] for c in shot["image"].get("characters", []) if c in chars)
    parts = [shot["image"]["prompt"], who, sb["style"]["block"]]
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
    return execute(ctx, units(ctx))
