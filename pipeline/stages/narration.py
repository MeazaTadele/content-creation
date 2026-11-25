"""Narration: one WAV per shot for every compared voice, with the spoken part measured.

Runs first (architecture change 1): the measured speech length sets every shot's duration.
Voices that run on Kaggle (MMS, OmniVoice, CosyVoice2) are produced by the voice benchmark job.
"""
from __future__ import annotations

import os
import shutil

from .. import calls, kaggle, media, providers
from ..calls import log_job_unit
from ..fingerprint import fingerprint
from ..config import ROOT
from .base import Context, Unit, check_stage_version, execute, out_path, rel, say

STAGE = "narration"
STAGE_VERSION = 1


def units(ctx: Context, voices: list[str] | None = None) -> list[Unit]:
    sb = ctx.sb
    voices = voices or sb["voice"]["compare"]
    style = sb["voice"].get("style_instruction")
    names = sb["voice"].get("voice_names", {})
    out = []
    for v in voices:
        prov = providers.tts(v)
        if getattr(prov, "batch", False):
            continue
        for shot in sb["shots"]:
            text = shot["narration"]["am"]
            voice_name = names.get(v)
            fp = fingerprint(STAGE, STAGE_VERSION, {
                "text": text, "provider": v, "voice": voice_name, "style": style,
                "model": prov.model or None,
            })
            unit = f"{v}/{shot['id']}"
            dst = out_path(STAGE, unit, fp, "wav")

            def run(tmp, tmp_dir, prov=prov, text=text, voice_name=voice_name, unit=unit, fp=fp, dst=dst):
                raw = tmp_dir / f"{unit.replace('/', '_')}.raw.wav"
                if prov.is_model:
                    prov.check_ready()
                    calls.call_model(stage=STAGE, unit=unit, provider=prov.name, model=prov.model,
                                     params={"voice": voice_name, "style": style}, seed=None,
                                     fn=lambda: prov.synthesize(text, voice_name, style, raw, tmp_dir),
                                     fingerprint=fp, output=rel(dst),
                                     price=prov.price)
                else:
                    prov.synthesize(text, voice_name, style, raw, tmp_dir)
                media.to_wav(raw, tmp)
                raw.unlink(missing_ok=True)
                start, end, total = media.speech_bounds(tmp)
                return {"speech_start": start, "speech_end": end, "file_seconds": total,
                        "speech_seconds": round(end - start, 3), "voice": v, "shot": unit.split("/")[1]}

            out.append(Unit(STAGE, unit, fp, dst, f"{v} voice, {len(text)} chars", run,
                            model_call=prov.is_model, provider=prov.name, model=prov.model))
    return out


def batch_units(ctx: Context, voices: list[str] | None = None) -> list[dict]:
    """Lines for the open voices that run as one Kaggle job (MMS, OmniVoice, CosyVoice2)."""
    sb = ctx.sb
    voices = voices or sb["voice"]["compare"]
    out = []
    for v in voices:
        prov = providers.tts(v)
        if not getattr(prov, "batch", False):
            continue
        ref = sb["voice"].get("references", {}).get(v)
        ref_path = (ROOT / ref["audio"]) if ref else None
        for shot in sb["shots"]:
            text = shot["narration"]["am"]
            fp = fingerprint(STAGE, STAGE_VERSION, {"text": text, "provider": v, "model": prov.model, "seed": 7,
                                                     "reference": ref_path, "reference_text": ref and ref["text"]})
            unit = f"{v}/{shot['id']}"
            if ctx.manifest.is_fresh(STAGE, unit, fp):
                say(f"  cached     {STAGE}/{unit}  ({fp[:8]})")
                continue
            out.append({"voice": v, "shot": shot["id"], "unit": unit, "fp": fp, "text": text, "model": prov.model,
                        "reference": ref_path, "reference_text": ref and ref["text"]})
    return out


def run_batch(ctx: Context, voices: list[str] | None = None) -> dict:
    todo = batch_units(ctx, voices)
    stats = {"generated": 0, "cached": 0, "failed": 0}
    if not todo:
        return stats
    if ctx.dry_run:
        for t in todo:
            say(f"  would run  {STAGE}/{t['unit']}  ({t['voice']} on Kaggle)")
        stats["generated"] = len(todo)
        return stats
    files, job_units = {}, []
    for t in todo:
        ju = {"unit": f"{t['voice']}_{t['shot']}", "model": t["voice"], "text": t["text"], "seed": 7,
              "fingerprint": t["fp"]}
        if t["reference"]:
            name = f"reference_{t['voice']}.wav"
            files[name] = t["reference"]
            ju.update(reference=name, reference_text=t["reference_text"])
        job_units.append(ju)
    # KAGGLE_TTS_DEVICE=cpu skips the GPU queue: the open voices are small (OmniVoice ~3 GB)
    on_gpu = os.environ.get("KAGGLE_TTS_DEVICE", "gpu") != "cpu"
    job_id, res = kaggle.run_job("tts-open", job_units, files, timeout=3600, gpu=on_gpu,
                                 settings={"device": "cuda" if on_gpu else "cpu"})
    for t, ju in zip(todo, job_units):
        r = kaggle.read_result(res, ju["unit"])
        dst = out_path(STAGE, t["unit"], t["fp"], "wav")
        ok = bool(r and r.get("status") == "ok" and (res / r["output"]).exists())
        if ok:
            dst.parent.mkdir(parents=True, exist_ok=True)
            media.to_wav(res / r["output"], dst)
            start, end, total = media.speech_bounds(dst)
            ctx.manifest.put(STAGE, t["unit"], {
                "fingerprint": t["fp"], "output": rel(dst), "status": "generated", "provider": t["voice"],
                "model": r.get("model", t["model"]), "seconds": r.get("seconds"), "speech_start": start,
                "speech_end": end, "file_seconds": total, "speech_seconds": round(end - start, 3),
                "voice": t["voice"], "shot": t["shot"]})
            stats["generated"] += 1
        else:
            stats["failed"] += 1
            say(f"  {STAGE}/{t['unit']}: failed on Kaggle: {(r or {}).get('error', 'no result')[:150]}")
        log_job_unit(stage=STAGE, unit=t["unit"], provider=t["voice"], model=(r or {}).get("model", t["model"]),
                     params={"text_chars": len(t["text"])}, seed=7, status=(r or {}).get("status", "missing"),
                     latency_ms=int(((r or {}).get("seconds") or 0) * 1000),
                     gpu_seconds=(r or {}).get("gpu_seconds") or 0, fingerprint=t["fp"],
                     output=rel(dst) if ok else None, job_id=job_id, error=(r or {}).get("error"))
    return stats


def run(ctx: Context, voices: list[str] | None = None) -> dict:
    """Each voice runs on its own: one voice hitting a quota never stops the others.
    Only a failure of the film's chosen voice (voice.use) stops the run."""
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    voices = voices or ctx.sb["voice"]["compare"]
    total = {"generated": 0, "cached": 0, "failed": 0}
    for v in voices:
        if getattr(providers.tts(v), "batch", False):
            continue
        try:
            s = execute(ctx, units(ctx, [v]))
        except Exception as e:  # noqa: BLE001
            if v == ctx.sb["voice"]["use"]:
                raise
            say(f"  {v}: stopped ({calls.redact(str(e))[:160]}); other voices continue, rerun later for the rest")
            s = {"generated": 0, "cached": 0, "failed": 1}
        total = {k: total[k] + s[k] for k in total}
    b = run_batch(ctx, voices)
    return {k: total[k] + b[k] for k in total}
