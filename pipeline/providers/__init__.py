"""Swappable model providers (architecture change 2).

Each capability has one small interface. A stage asks the registry for a provider by the
name written in the storyboard, so adding a model means adding one provider, not changing a stage.
"""
from __future__ import annotations

from .base import ImageProvider, MusicProvider, TTSProvider


def tts(name: str) -> TTSProvider:
    if name == "placeholder":
        from .placeholder import PlaceholderTTS
        return PlaceholderTTS()
    if name == "gemini":
        from .gemini import GeminiTTS
        return GeminiTTS()
    if name == "elevenlabs":
        from .elevenlabs import ElevenLabsTTS
        return ElevenLabsTTS()
    if name in ("mms", "omnivoice", "cosyvoice2"):
        from .kaggle_tts import KaggleTTS
        return KaggleTTS(name)
    raise KeyError(f"unknown TTS provider '{name}'")


def image(name: str) -> ImageProvider:
    if name == "placeholder":
        from .placeholder import PlaceholderImage
        return PlaceholderImage()
    if name == "cloudflare-flux":
        from .cloudflare import CloudflareFlux
        return CloudflareFlux()
    raise KeyError(f"unknown image provider '{name}'")


def music(name: str) -> MusicProvider:
    if name == "placeholder":
        from .placeholder import PlaceholderMusic
        return PlaceholderMusic()
    raise KeyError(f"music provider '{name}' runs as a Kaggle batch job, not synchronously")
