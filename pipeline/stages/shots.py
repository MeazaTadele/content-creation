"""Moving shots: Wan 2.2 image-to-video on Kaggle (decision 5), with the Ken Burns fallback (decision 9).

This module records which shots have a usable clip. The Kaggle batch job itself lives in
pipeline/kaggle.py and kaggle/shots/. A shot with no clip, or with motion.kenburns set, is
rendered as a Ken Burns move in assembly, and the manifest says why.
"""
from __future__ import annotations

from ..config import ROOT
from .base import Context

STAGE = "shots"
STAGE_VERSION = 1
MAX_ATTEMPTS = 2  # decision 9: two automatic attempts per clip, then Ken Burns


def clip_path(ctx: Context, shot_id: str):
    e = ctx.manifest.get(STAGE, shot_id)
    if not e or e.get("status") != "generated":
        return None
    p = ROOT / e["output"]
    return p if p.exists() else None
