"""Narration: one WAV per shot for every compared voice, with the spoken part measured.

Runs first (architecture change 1): the measured speech length sets every shot's duration.
Voices that run on Kaggle (MMS, OmniVoice, CosyVoice2) are produced by the voice benchmark job.
"""
from __future__ import annotations

from .. import calls, media, providers
from ..fingerprint import fingerprint
from .base import Context, Unit, check_stage_version, execute, out_path, rel

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


def run(ctx: Context, voices: list[str] | None = None) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    return execute(ctx, units(ctx, voices))
