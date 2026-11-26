"""ElevenLabs text-to-speech (one of the compared Amharic voices)."""
from __future__ import annotations

import os

from .. import media
from ..calls import CallResult, FatalError
from . import http
from .base import TTSProvider

API = "https://api.elevenlabs.io/v1"
KEY_HINT = "Create a key on elevenlabs.io (API keys page) and save it as ELEVENLABS_API_KEY."


class ElevenLabsTTS(TTSProvider):
    name, licence = "elevenlabs", "ElevenLabs terms (free plan: non-commercial, attribution)"

    def __init__(self):
        self.model = os.environ.get("ELEVENLABS_MODEL", "eleven_v3")

    def check_ready(self):
        http.require_env("ELEVENLABS_API_KEY", KEY_HINT)

    def synthesize(self, text, voice, style, out_wav, tmp_dir):
        key = http.require_env("ELEVENLABS_API_KEY", KEY_HINT)
        if not voice:
            raise FatalError("set voice.voice_names.elevenlabs in storyboard.json to an ElevenLabs voice id")
        body = {"text": text, "model_id": self.model}
        # eleven_v3 rejects language_code "am" (smoke test, 25 Nov), but accepts Amharic text without it
        if os.environ.get("ELEVENLABS_LANGUAGE_CODE"):
            body["language_code"] = os.environ["ELEVENLABS_LANGUAGE_CODE"]
        r = http.post(f"{API}/text-to-speech/{voice}?output_format=pcm_24000",
                      headers={"xi-api-key": key, "Content-Type": "application/json"}, json=body)
        if not r.content:
            raise FatalError("ElevenLabs returned no audio")
        media.pcm_to_wav(r.content, 24000, out_wav, tmp_dir)
        return CallResult(out_wav, {"chars": len(text)}, self.model)
