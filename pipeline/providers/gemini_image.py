"""Gemini image editing (decision 36): change one thing in a chosen keyframe, keep the rest.

Used per shot (image.provider "gemini-image") when the open model on Kaggle could not make a
targeted edit (FAILURES.md F17). The model id comes from GEMINI_IMAGE_MODEL when set.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

from ..calls import CallResult, FatalError
from . import http
from .gemini import API, _headers

DEFAULT_MODEL = "gemini-2.5-flash-image"
RATIOS = {"9x16": "9:16", "16x9": "16:9"}


class GeminiImageEdit:
    name, licence, is_model = "gemini-image", "Google Gemini API terms (outputs carry a SynthID watermark)", True

    def __init__(self):
        self.model = os.environ.get("GEMINI_IMAGE_MODEL", DEFAULT_MODEL)

    def edit(self, base: Path, instruction: str, refs: list[Path], ratio: str, out_png: Path) -> CallResult:
        parts = [{"inline_data": {"mime_type": "image/png", "data": base64.b64encode(base.read_bytes()).decode()}}]
        for r in refs:
            parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(r.read_bytes()).decode()}})
        parts.append({"text": instruction})
        body = {"contents": [{"parts": parts}],
                "generationConfig": {"responseModalities": ["IMAGE"],
                                     "imageConfig": {"aspectRatio": RATIOS.get(ratio, "9:16")}}}
        j = http.post(f"{API}/models/{self.model}:generateContent", headers=_headers(), json=body).json()
        for part in (j.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
            data = (part.get("inlineData") or part.get("inline_data") or {}).get("data")
            if data:
                out_png.write_bytes(base64.b64decode(data))
                return CallResult(value=str(out_png), units={"images": 1}, model=j.get("modelVersion") or self.model)
        raise FatalError(f"Gemini returned no image: {str(j)[:300]}")
