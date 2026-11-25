"""Provider interfaces. Every provider declares its model, licence and whether it is a real model call."""
from __future__ import annotations

from pathlib import Path

from ..calls import CallResult


class Provider:
    name: str = ""
    model: str = ""
    licence: str = ""
    is_model: bool = True  # placeholders are not model calls and are never written to runs.jsonl

    def price(self, units: dict) -> float:
        """List-price equivalent in USD for the units used; 0.0 when unknown (see COSTS.md)."""
        return 0.0

    def check_ready(self) -> None:
        """Raise a clear error if credentials or settings are missing."""


class TTSProvider(Provider):
    def synthesize(self, text: str, voice: str | None, style: str | None, out_wav: Path, tmp_dir: Path) -> CallResult:
        raise NotImplementedError


class ImageProvider(Provider):
    def generate(self, prompt: str, negative: str | None, seed: int, width: int, height: int,
                 refs: list[Path], out_png: Path, tmp_dir: Path) -> CallResult:
        raise NotImplementedError


class MusicProvider(Provider):
    def compose(self, caption: str, seconds: float, bpm: int | None, key: str | None, seed: int,
                instrumental: bool, out_wav: Path, tmp_dir: Path) -> CallResult:
        raise NotImplementedError
