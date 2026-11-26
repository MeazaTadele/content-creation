"""Open Amharic voices (MMS, OmniVoice, CosyVoice2) run as a Kaggle batch job, not one call at a time.

The narration stage collects their units and hands them to pipeline.kaggle; this class only
exists so the registry can name them. Phase 2 of the voice benchmark (decision 24).
"""
from __future__ import annotations

from ..calls import FatalError
from .base import TTSProvider

MODELS = {
    "mms": ("facebook/mms-tts-amh", "CC BY-NC 4.0"),
    "omnivoice": ("Lab-et/omnivoice-amharic", "Apache 2.0"),
    "cosyvoice2": ("gabar-tech/cosyvoice2-amharic", "check model card"),
}


class KaggleTTS(TTSProvider):
    batch = True

    def __init__(self, name: str):
        self.name = name
        self.model, self.licence = MODELS[name]

    def synthesize(self, *a, **k):
        raise FatalError(f"{self.name} runs as a Kaggle batch job (make voicebench), not per call")
