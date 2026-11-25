"""Reference sheet: several candidate images per character, made before any keyframe.

The author picks one by setting characters[].reference_use in the storyboard; keyframes are
then conditioned on that image (architecture change 4).
"""
from __future__ import annotations

from .. import calls, providers
from ..fingerprint import fingerprint
from .base import Context, Unit, check_stage_version, execute, out_path, rel

STAGE = "refsheet"
STAGE_VERSION = 1
SIZE = (768, 1024)


def prompt_for(sb: dict, ch: dict) -> str:
    return (f"Character reference sheet, full body front view and a head-and-shoulders close-up, "
            f"plain background. {ch['description']}. {sb['style']['block']}")


def units(ctx: Context) -> list[Unit]:
    sb = ctx.sb
    prov = providers.image(sb["providers"]["keyframes"])
    out = []
    for ch in sb["characters"]:
        n = ch.get("reference_candidates", 4)
        base_seed = ch.get("reference_seed", 1000)
        for k in range(n):
            seed = base_seed + k
            prompt = prompt_for(sb, ch)
            fp = fingerprint(STAGE, STAGE_VERSION, {"prompt": prompt, "negative": sb["style"].get("negative"),
                                                     "seed": seed, "size": SIZE, "provider": prov.name,
                                                     "model": prov.model})
            unit = f"{ch['id']}/{k}"
            dst = out_path(STAGE, unit, fp, "png")

            def run(tmp, tmp_dir, prompt=prompt, seed=seed, unit=unit, fp=fp, dst=dst):
                gen = lambda: prov.generate(prompt, sb["style"].get("negative"), seed, *SIZE, [], tmp, tmp_dir)
                if prov.is_model:
                    prov.check_ready()
                    calls.call_model(stage=STAGE, unit=unit, provider=prov.name, model=prov.model,
                                     params={"size": SIZE}, seed=seed, fn=gen, fingerprint=fp,
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
    k = ch.get("reference_use")
    if k is None:
        return None
    e = ctx.manifest.get(STAGE, f"{char_id}/{k}")
    from ..config import ROOT
    return (ROOT / e["output"]) if e else None


def run(ctx: Context) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    return execute(ctx, units(ctx))
