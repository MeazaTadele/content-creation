"""Gemini: text (script stage) and text-to-speech (narration).

The model ids change often, so they come from the environment when set, otherwise the
provider asks the API which models exist and picks the newest Flash TTS model.
"""
from __future__ import annotations

import base64
import os
import re

from .. import media
from ..calls import CallResult, FatalError
from . import http
from .base import TTSProvider

API = "https://generativelanguage.googleapis.com/v1beta"
KEY_HINT = "Create a key in Google AI Studio and save it as GEMINI_API_KEY (see .env.example)."
DEFAULT_VOICE = "Kore"


def _headers() -> dict:
    return {"x-goog-api-key": http.require_env("GEMINI_API_KEY", KEY_HINT), "Content-Type": "application/json"}


def list_models() -> list[str]:
    r = http.get(f"{API}/models", headers=_headers(), params={"pageSize": 1000})
    return [m["name"].removeprefix("models/") for m in r.json().get("models", [])]


def _version_key(name: str):
    nums = [int(x) for x in re.findall(r"\d+", name)]
    return (0 if "preview" in name else 1, nums)


def pick_tts_model() -> str:
    env = os.environ.get("GEMINI_TTS_MODEL")
    if env:
        return env
    tts = [m for m in list_models() if "tts" in m and "flash" in m]
    if not tts:
        raise FatalError("no Gemini Flash TTS model is listed for this key; set GEMINI_TTS_MODEL")
    return sorted(tts, key=_version_key)[-1]


class GeminiTTS(TTSProvider):
    name, licence = "gemini", "Google Gemini API terms"

    def __init__(self):
        self.model = os.environ.get("GEMINI_TTS_MODEL", "")

    def check_ready(self):
        http.require_env("GEMINI_API_KEY", KEY_HINT)
        if not self.model:
            self.model = pick_tts_model()

    def synthesize(self, text, voice, style, out_wav, tmp_dir):
        self.check_ready()
        prompt = f"{style.strip()}:\n{text}" if style else text
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice or DEFAULT_VOICE}}},
            },
        }
        r = http.post(f"{API}/models/{self.model}:generateContent", headers=_headers(), json=body)
        j = r.json()
        try:
            part = j["candidates"][0]["content"]["parts"][0]["inlineData"]
        except (KeyError, IndexError):
            raise FatalError(f"Gemini returned no audio: {str(j)[:300]}") from None
        pcm = base64.b64decode(part["data"])
        rate = 24000
        m = re.search(r"rate=(\d+)", part.get("mimeType", ""))
        if m:
            rate = int(m.group(1))
        media.pcm_to_wav(pcm, rate, out_wav, tmp_dir)
        return CallResult(out_wav, {"chars": len(text)}, j.get("modelVersion") or self.model)
