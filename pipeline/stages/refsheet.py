"""Reference sheet: several candidate images per character, made before any keyframe.

The author picks one by setting characters[].reference_use in the storyboard; keyframes are
then conditioned on that image (architecture change 4).
"""
from __future__ import annotations

from .. import calls, providers
from ..fingerprint import fingerprint
from ..config import ROOT
from .base import Context, Unit, check_stage_version, execute, out_path, rel

STAGE = "refsheet"
STAGE_VERSION = 1
SIZE = (768, 1024)


def prompt_for(sb: dict, ch: dict) -> str:
    if ch.get("edit_from"):
        return (f"Edit the reference image: {ch['description']}. Keep the pose, framing, background and painting style; "
                f"change nothing else. {sb['style']['block']}")
    return (f"Character reference sheet, full body front view and a head-and-shoulders close-up, "
            f"plain background. {ch['description']}. {sb['style']['block']}")


def units(ctx: Context) -> list[Unit]:
    sb = ctx.sb
    if all(ch.get("reference_image") for ch in sb["characters"]):
        return []  # every character is locked: nothing to generate, and no image provider needed
    prov = providers.image(sb["providers"]["keyframes"])
    out = []
    for ch in sb["characters"]:
        if ch.get("reference_image"):
            continue  # locked: the chosen image is used as is
        refs = [ROOT / ch["edit_from"]] if ch.get("edit_from") else []
        n = ch.get("reference_candidates", 4)
        base_seed = ch.get("reference_seed", 1000)
        for k in range(n):
            seed = base_seed + k
            prompt = prompt_for(sb, ch)
            inputs = {"prompt": prompt, "negative": sb["style"].get("negative"), "seed": seed, "size": SIZE,
                      "provider": prov.name, "model": prov.model}
            if refs:  # only edited candidates depend on an input image; leave every other fingerprint unchanged
                inputs["refs"] = refs
            fp = fingerprint(STAGE, STAGE_VERSION, inputs)
            unit = f"{ch['id']}/{k}"
            dst = out_path(STAGE, unit, fp, "png")

            def run(tmp, tmp_dir, prompt=prompt, seed=seed, unit=unit, fp=fp, dst=dst, refs=refs):
                gen = lambda: prov.generate(prompt, sb["style"].get("negative"), seed, *SIZE, refs, tmp, tmp_dir)
                if prov.is_model:
                    prov.check_ready()
                    calls.call_model(stage=STAGE, unit=unit, provider=prov.name, model=prov.model,
                                     params={"size": SIZE, "refs": len(refs)}, seed=seed, fn=gen, fingerprint=fp,
                                     output=rel(dst), price=prov.price)
                else:
                    gen()
                return {"character": unit.split("/")[0], "candidate": int(unit.split("/")[1])}

            out.append(Unit(STAGE, unit, fp, dst, f"reference candidate {k}", run,
                            model_call=prov.is_model, provider=prov.name, model=prov.model))
    return out


def chosen(ctx: Context, char_id: str):
    """Path of the reference image the author chose for a character, or None if not chosen yet."""
    ch = next(c for c in ctx.sb["characters"] if c["id"] == char_id)
    if ch.get("reference_image"):
        return ROOT / ch["reference_image"]
    k = ch.get("reference_use")
    if k is None:
        return None
    e = ctx.manifest.get(STAGE, f"{char_id}/{k}")
    return (ROOT / e["output"]) if e else None


def run(ctx: Context) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    return execute(ctx, units(ctx))
