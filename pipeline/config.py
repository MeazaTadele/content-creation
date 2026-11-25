"""Paths and settings shared by every stage."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "storyboard.schema.json"
STORYBOARD_PATH = Path(os.environ.get("STORYBOARD", ROOT / "storyboard.json"))
OUTPUTS = ROOT / "outputs"
MANIFEST_PATH = OUTPUTS / "manifest.json"
RUNS_LOG = ROOT / "runs.jsonl"

# Picture settings
FPS = 24
CANVAS = {"9x16": (1080, 1920), "16x9": (1920, 1080)}
RATIOS = ("9x16", "16x9")
CROSSFADE_SEC = 0.5

# Audio settings
SAMPLE_RATE = 48000
TARGET_LUFS = -14.0
TARGET_TP = -1.0
NARRATION_STEM_LUFS = -18.0
MUSIC_STEM_LUFS = -26.0
DUCK = {"threshold": 0.02, "ratio": 6, "attack": 300, "release": 1500}

# Timing defaults (seconds)
DEFAULT_LEAD_IN = 0.3
DEFAULT_TAIL = 0.6
DEFAULT_MIN_SHOT = 3.0
MUSIC_LENGTH_BUCKET = 15.0


def load_env() -> None:
    """Load .env if python-dotenv is installed; real environment variables win."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ROOT / ".env", override=False)
