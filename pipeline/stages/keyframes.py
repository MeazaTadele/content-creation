"""Keyframes: one still per shot and per aspect ratio, conditioned on the chosen references.

9:16 keyframes start the video clips; both ratios are used directly for Ken Burns shots
(decision 6), so a still shot never has to be cropped from the other ratio.
"""
from __future__ import annotations

from .. import calls, providers
from ..config import ROOT
from ..fingerprint import fingerprint
from . import refsheet
from .base import Context, Unit, check_stage_version, execute, out_path, rel, say

STAGE = "keyframes"
STAGE_VERSION = 3  # 3: style and exclusions placed first in long prompts
SIZES = {"9x16": (768, 1344), "16x9": (1344, 768)}


SCENE = ("One single full-frame illustrated scene from a film, with a real setting filling the whole frame. "
         "Not a character sheet: no plain background, no inset portraits, no multiple views of the same person")


SAME_ROOM = ("The first reference image is the room for this shot: the same living room, the same walls, window, "
             "curtains and seats, the same carved coffee table with the same small cups, the same black clay coffee pot "
             "on its straw ring, the same clay charcoal brazier and incense burner, the same cut grass on the floor, the "
             "same light and painting style. Keep all of it the same; only the camera framing and the people change, "
             "as described below")


EDIT = ("The first reference image is the picture to change: keep its room, objects, colours, light, camera position and "
        "painting style, and change it as described below")


def scene_ref(ctx: Context, shot: dict, ratio: str):
    """The keyframe of the shot named in image.scene_from, in the same ratio (None if it isn't made yet)."""
    src = shot["image"].get("scene_from")
    if not src:
        return None
    e = ctx.manifest.get(STAGE, f"{src}/{ratio}")
    return (ROOT / e["output"]) if e else None


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
    same_room = (EDIT if shot["image"].get("edit_from")
                 else SAME_ROOM if shot["image"].get("scene_from") else "")
    parts = [SCENE, sb["style"]["block"], same_room, avoid, scene, who]
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


def run_kaggle(ctx: Context, ratios: list[str] | None = None, shots: list[str] | None = None,
               try_seeds: list[int] | None = None) -> dict:
    """Decision 32: the same FLUX.2 klein model on Kaggle's GPU, as one batch job."""
    import shutil
    from .. import kaggle, media
    from ..calls import log_job_unit
    sb = ctx.sb
    todo, files = [], {}
    for shot in sb["shots"]:
        if (shots and shot["id"] not in shots) or shot["image"].get("provider") in ("gemini-image", "kaggle-inpaint"):
            continue
        char_refs = [p for c in shot["image"].get("characters", []) if (p := refsheet.chosen(ctx, c)) is not None]
        prompt = full_prompt(sb, shot)
        for ratio, size in SIZES.items():
            if ratios and ratio not in ratios:
                continue
            refs = char_refs
            locked = (shot["image"].get("locked") or {}).get(ratio)
            if locked:  # a keyframe Meaza chose to keep as it is (decision 35): copy, never regenerate
                src = ROOT / locked
                fp = fingerprint(STAGE, STAGE_VERSION, {"locked": src})
                unit = f"{shot['id']}/{ratio}"
                if ctx.dry_run and not ctx.manifest.is_fresh(STAGE, unit, fp):
                    say(f"  would lock {STAGE}/{unit}  <- {locked}")
                elif not ctx.manifest.is_fresh(STAGE, unit, fp):
                    dst = out_path(STAGE, unit, fp, "png")
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    ctx.manifest.put(STAGE, unit, {"fingerprint": fp, "output": rel(dst), "status": "locked",
                                                   "source": locked, "shot": shot["id"], "ratio": ratio})
                    say(f"  locked     {STAGE}/{unit}  <- {locked}")
                continue
            if shot["image"].get("edit_from"):
                base = (shot["image"]["edit_from"] or {}).get(ratio)
                if not base:
                    say(f"  skipped    {STAGE}/{shot['id']}/{ratio}: no image to edit for this ratio yet")
                    continue
                refs = [ROOT / base] + char_refs  # the image being edited first
            elif shot["image"].get("scene_from"):
                room = scene_ref(ctx, shot, ratio)
                if room is None:
                    say(f"  skipped    {STAGE}/{shot['id']}/{ratio}: its room ({shot['image']['scene_from']}) has no keyframe yet")
                    continue
                refs = [room] + char_refs  # the room first: the prompt calls it "the first reference image"
            # candidate mode (--shot X --seeds a,b,c): try several seeds for one shot; each candidate keeps the
            # fingerprint it would have as the main keyframe, so the chosen seed is reused, not regenerated
            trying = bool(try_seeds and shot["id"] in (shots or []))
            for seed in (try_seeds if trying else [shot["image"]["seed"]]):
                fp = fingerprint(STAGE, STAGE_VERSION, {"prompt": prompt, "seed": seed, "size": size,
                                                         "refs": refs, "provider": "kaggle-flux", "model": KAGGLE_MODEL})
                unit = f"{shot['id']}/{ratio}" + (f"/try{seed}" if trying else "")
                if ctx.manifest.is_fresh(STAGE, unit, fp):
                    say(f"  cached     {STAGE}/{unit}  ({fp[:8]})")
                    continue
                names = []
                for r in refs:
                    names.append(r.name)
                    files[r.name] = r
                todo.append({"unit": unit.replace("/", "_"), "key": unit, "fingerprint": fp, "prompt": prompt,
                             "width": size[0], "height": size[1], "seed": seed, "refs": names,
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


INPAINT_MODEL = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"


def _mask_png(step: dict, size: tuple[int, int], dst) -> None:
    from PIL import Image, ImageDraw
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.polygon([tuple(p) for p in step["area"]], fill=255)
    for k in step.get("keep", []):
        d.polygon([tuple(p) for p in k], fill=0)
    m.save(dst)


def run_inpaint(ctx: Context, ratios: list[str] | None, shots: list[str] | None, try_seeds: list[int] | None) -> dict:
    """Decision 37: repaint only marked areas of a chosen keyframe (SDXL inpainting on Kaggle)."""
    import shutil
    import tempfile
    from pathlib import Path
    from .. import kaggle
    from ..calls import log_job_unit
    todo, files = [], {}
    tmpd = Path(tempfile.mkdtemp(prefix="masks-"))
    for shot in ctx.sb["shots"]:
        im = shot["image"]
        if im.get("provider") != "kaggle-inpaint" or (shots and shot["id"] not in shots):
            continue
        for ratio, base in (im.get("edit_from") or {}).items():
            if ratios and ratio not in ratios:
                continue
            base_p = ROOT / base
            trying = bool(try_seeds and shot["id"] in (shots or []))
            for seed in (try_seeds if trying else [im["seed"]]):
                fp = fingerprint(STAGE, STAGE_VERSION, {"inpaint": im["inpaint"], "base": base_p, "seed": seed,
                                                         "provider": "kaggle-inpaint", "model": INPAINT_MODEL})
                unit = f"{shot['id']}/{ratio}" + (f"/try{seed}" if trying else "")
                if ctx.manifest.is_fresh(STAGE, unit, fp):
                    say(f"  cached     {STAGE}/{unit}  ({fp[:8]})")
                    continue
                uname = unit.replace("/", "_")
                steps = []
                for k, st in enumerate(im["inpaint"]):
                    mp = tmpd / f"{uname}_mask{k}.png"
                    _mask_png(st, SIZES[ratio], mp)
                    files[mp.name] = mp
                    steps.append({"mask": mp.name, "prompt": st["prompt"], "negative": st.get("negative", "")})
                files[base_p.name] = base_p
                todo.append({"unit": uname, "key": unit, "fingerprint": fp, "base": base_p.name, "steps": steps,
                             "seed": seed, "shot": shot["id"], "ratio": ratio})
    if not todo:
        return {"generated": 0, "cached": 0, "failed": 0}
    if ctx.dry_run:
        for t in todo:
            say(f"  would run  {STAGE}/{t['key']}  (repaint {len(t['steps'])} areas on Kaggle)")
        return {"generated": len(todo), "cached": 0, "failed": 0}
    job_id, res = kaggle.run_job("inpaint", [{k: v for k, v in t.items() if k not in ("key", "shot", "ratio")} for t in todo],
                                 files, timeout=2 * 3600, gpu=True)
    stats = {"generated": 0, "cached": 0, "failed": 0}
    for t in todo:
        r = kaggle.read_result(res, t["unit"])
        dst = out_path(STAGE, t["key"], t["fingerprint"], "png")
        ok = bool(r and r.get("status") == "ok" and (res / r["output"]).exists())
        if ok:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(res / r["output"], dst)
            ctx.manifest.put(STAGE, t["key"], {"fingerprint": t["fingerprint"], "output": rel(dst), "status": "generated",
                                               "provider": "kaggle-inpaint", "model": INPAINT_MODEL, "shot": t["shot"],
                                               "ratio": t["ratio"], "seconds": r.get("seconds")})
            stats["generated"] += 1
        else:
            stats["failed"] += 1
            say(f"  {STAGE}/{t['key']}: failed on Kaggle: {(r or {}).get('error', 'no result')[:150]}")
        log_job_unit(stage=STAGE, unit=t["key"], provider="kaggle-inpaint", model=INPAINT_MODEL,
                     params={"areas": len(t["steps"]), "steps": 30}, seed=t["seed"],
                     status=(r or {}).get("status", "missing"), latency_ms=int(((r or {}).get("seconds") or 0) * 1000),
                     gpu_seconds=(r or {}).get("gpu_seconds") or 0, fingerprint=t["fingerprint"],
                     output=rel(dst) if ok else None, job_id=job_id, error=(r or {}).get("error"))
    return stats


WIDE_SIZE = (1344, 768)  # SDXL works in multiples of 8; assembly scales it to 1920x1080
WIDE_PROMPT = ("the same simple Ethiopian home continues to the left and to the right: the same plain painted walls in "
               "the same colour, the same floor, the same low cushioned seats along the walls, bare walls, an uncluttered "
               "room, the same light and colours, warm soft painted illustration, gentle morning light, visible brush texture")
WIDE_NEGATIVE = ("people, person, face, child, text, letters, picture frame, painting on the wall, poster, lamp, dresser, "
                 "cabinet, chest of drawers, armchair, bookshelf, shelf, pillar, column, door frame, wardrobe, plant, "
                 "split screen, panel, border, blurry")


def run_wide(ctx: Context) -> dict:
    """Decision 43: each 16:9 keyframe is its 9:16 keyframe, unchanged in the middle, with the room
    painted on both sides (outpainting with SDXL inpainting on Kaggle)."""
    import shutil
    import tempfile
    from pathlib import Path
    from PIL import Image, ImageDraw, ImageFilter
    from .. import kaggle
    from ..calls import log_job_unit
    if ctx.sb.get("wide") != "outpaint":
        return {"generated": 0, "cached": 0, "failed": 0}
    W, H = WIDE_SIZE
    todo, files = [], {}
    tmpd = Path(tempfile.mkdtemp(prefix="wide-"))
    for shot in ctx.sb["shots"]:
        base = path(ctx, shot["id"], "9x16")
        if base is None:
            continue
        prompt = WIDE_PROMPT + (", " + shot["image"]["wide_prompt"] if shot["image"].get("wide_prompt") else "")
        negative = WIDE_NEGATIVE
        if shot["image"].get("wide_prompt"):  # a shot that asks for a person on the sides allows one
            negative = negative.replace("people, person, face, ", "")
        fp = fingerprint(STAGE, STAGE_VERSION, {"wide_from": base, "prompt": prompt, "negative": negative,
                                                 "size": WIDE_SIZE, "seed": shot["image"]["seed"],
                                                 "provider": "kaggle-inpaint", "model": INPAINT_MODEL})
        unit = f"{shot['id']}/16x9"
        if ctx.manifest.is_fresh(STAGE, unit, fp):
            say(f"  cached     {STAGE}/{unit}  ({fp[:8]})")
            continue
        uname = unit.replace("/", "_")
        img = Image.open(base).convert("RGB")
        w = round(img.width * H / img.height / 2) * 2
        img = img.resize((w, H), Image.LANCZOS)
        x0 = (W - w) // 2
        canvas = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(30))  # colour hint only
        canvas.paste(img, (x0, 0))
        cp, mp = tmpd / f"{uname}_canvas.png", tmpd / f"{uname}_mask.png"
        canvas.save(cp)
        m = Image.new("L", (W, H), 255)
        ImageDraw.Draw(m).rectangle([x0 + 6, 0, x0 + w - 7, H], fill=0)  # the 9:16 picture is kept
        m.save(mp)
        files[cp.name], files[mp.name] = cp, mp
        todo.append({"unit": uname, "key": unit, "fingerprint": fp, "base": cp.name, "seed": shot["image"]["seed"],
                     "steps": [{"mask": mp.name, "prompt": prompt, "negative": negative}], "shot": shot["id"]})
    if not todo:
        return {"generated": 0, "cached": len(ctx.sb["shots"]), "failed": 0}
    if ctx.dry_run:
        for t in todo:
            say(f"  would run  {STAGE}/{t['key']}  (9:16 picture widened by outpainting on Kaggle)")
        return {"generated": len(todo), "cached": 0, "failed": 0}
    job_id, res = kaggle.run_job("inpaint", [{k: v for k, v in t.items() if k not in ("key", "shot")} for t in todo],
                                 files, timeout=2 * 3600, gpu=True)
    stats = {"generated": 0, "cached": 0, "failed": 0}
    for t in todo:
        r = kaggle.read_result(res, t["unit"])
        dst = out_path(STAGE, t["key"], t["fingerprint"], "png")
        ok = bool(r and r.get("status") == "ok" and (res / r["output"]).exists())
        if ok:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(res / r["output"], dst)
            ctx.manifest.put(STAGE, t["key"], {"fingerprint": t["fingerprint"], "output": rel(dst), "status": "generated",
                                               "provider": "kaggle-inpaint", "model": INPAINT_MODEL, "shot": t["shot"],
                                               "ratio": "16x9", "wide_from": "9x16", "seconds": r.get("seconds")})
            stats["generated"] += 1
        else:
            stats["failed"] += 1
            say(f"  {STAGE}/{t['key']}: failed on Kaggle: {(r or {}).get('error', 'no result')[:150]}")
        log_job_unit(stage=STAGE, unit=t["key"], provider="kaggle-inpaint", model=INPAINT_MODEL,
                     params={"outpaint": "9x16 to 16x9", "size": list(WIDE_SIZE), "steps": 30}, seed=t["seed"],
                     status=(r or {}).get("status", "missing"), latency_ms=int(((r or {}).get("seconds") or 0) * 1000),
                     gpu_seconds=(r or {}).get("gpu_seconds") or 0, fingerprint=t["fingerprint"],
                     output=rel(dst) if ok else None, job_id=job_id, error=(r or {}).get("error"))
    return stats


def run_gemini_edits(ctx: Context, ratios: list[str] | None, shots: list[str] | None) -> dict:
    """Decision 36: shots with image.provider "gemini-image" are edits of a chosen keyframe, made by Gemini."""
    import shutil
    from ..providers.gemini_image import GeminiImageEdit
    prov = GeminiImageEdit()
    stats = {"generated": 0, "cached": 0, "failed": 0}
    for shot in ctx.sb["shots"]:
        im = shot["image"]
        if im.get("provider") != "gemini-image" or (shots and shot["id"] not in shots):
            continue
        refs = [p for c in im.get("characters", []) if (p := refsheet.chosen(ctx, c)) is not None]
        for ratio, base in (im.get("edit_from") or {}).items():
            if ratios and ratio not in ratios:
                continue
            base_p = ROOT / base
            fp = fingerprint(STAGE, STAGE_VERSION, {"edit": im["prompt"], "base": base_p, "refs": refs,
                                                     "provider": prov.name, "model": prov.model})
            unit = f"{shot['id']}/{ratio}"
            if ctx.manifest.is_fresh(STAGE, unit, fp):
                say(f"  cached     {STAGE}/{unit}  ({fp[:8]})")
                stats["cached"] += 1
                continue
            if ctx.dry_run:
                say(f"  would run  {STAGE}/{unit}  (edit with {prov.model})")
                stats["generated"] += 1
                continue
            dst = out_path(STAGE, unit, fp, "png")
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_suffix(".tmp.png")
            try:
                calls.call_model(stage=STAGE, unit=unit, provider=prov.name, model=prov.model,
                                 params={"edit_from": base, "refs": len(refs), "ratio": ratio}, seed=None,
                                 fn=lambda: prov.edit(base_p, im["prompt"], refs, ratio, tmp), fingerprint=fp,
                                 output=rel(dst))
            except Exception as e:  # noqa: BLE001 - logged in runs.jsonl; the other shots go on
                say(f"  {STAGE}/{unit}: Gemini edit failed: {str(e)[:200]}")
                stats["failed"] += 1
                continue
            w, h = SIZES[ratio]
            from .. import media
            media.run(["-i", str(tmp), "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                       "-frames:v", "1", str(dst)])
            tmp.unlink(missing_ok=True)
            ctx.manifest.put(STAGE, unit, {"fingerprint": fp, "output": rel(dst), "status": "generated",
                                           "provider": prov.name, "model": prov.model, "shot": shot["id"],
                                           "ratio": ratio, "edit_from": base})
            say(f"  edited     {STAGE}/{unit}  ({prov.model})")
            stats["generated"] += 1
    return stats


def run(ctx: Context, ratios: list[str] | None = None, shots: list[str] | None = None,
        try_seeds: list[int] | None = None) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    g = run_gemini_edits(ctx, ratios, shots)
    i = run_inpaint(ctx, ratios, shots, try_seeds)
    if ctx.sb["providers"]["keyframes"] == "kaggle-flux":
        k = run_kaggle(ctx, ratios, shots, try_seeds)
        return {key: g[key] + i[key] + k[key] for key in k}
    # one image blocked by the provider's safety filter must not stop the other shots (FAILURES.md F10)
    return execute(ctx, units(ctx), keep_going=True)
