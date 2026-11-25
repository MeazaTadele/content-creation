"""Timing: shot lengths from the measured narration of the chosen voice.

Not cached: it is pure arithmetic over the manifest and takes milliseconds. The result goes
into the manifest's measured values and outputs/timing.json, never into the storyboard.
"""
from __future__ import annotations

from .. import atomic
from ..config import (CROSSFADE_SEC, DEFAULT_LEAD_IN, DEFAULT_MIN_SHOT, DEFAULT_TAIL, OUTPUTS)
from .base import Context, say

MIN_GAP = 0.25  # seconds of quiet between one shot's narration and the next


class TimingError(RuntimeError):
    pass


def compute(ctx: Context) -> dict:
    sb = ctx.sb
    voice = sb["voice"]["use"]
    shots = []
    start = 0.0
    prev_narr_end = None
    n = len(sb["shots"])
    for i, s in enumerate(sb["shots"]):
        e = ctx.manifest.get("narration", f"{voice}/{s['id']}")
        if not e:
            raise TimingError(f"no narration for {voice}/{s['id']}; run the narration stage first")
        t = s.get("timing", {})
        lead = t.get("lead_in", DEFAULT_LEAD_IN)
        tail = t.get("tail", DEFAULT_TAIL)
        speech = e["speech_seconds"]
        narr_start = start + lead
        if prev_narr_end is not None and narr_start < prev_narr_end + MIN_GAP:
            # a crossfade pulled this shot's words too close to the last shot's: push them later
            lead += prev_narr_end + MIN_GAP - narr_start
            narr_start = start + lead
        dur = max(t.get("min", DEFAULT_MIN_SHOT), lead + speech + tail)
        overlap = CROSSFADE_SEC if (s.get("transition", "cut") == "crossfade" or i == n - 1) else 0.0
        shots.append({
            "id": s["id"], "start": round(start, 3), "duration": round(dur, 3),
            "narration_start": round(narr_start, 3), "narration_end": round(narr_start + speech, 3),
            "speech_trim": [e["speech_start"], e["speech_end"]], "overlap_out": overlap,
        })
        prev_narr_end = narr_start + speech
        start = start + dur - overlap
    end_card = sb["end_card"]["seconds"]
    end_card_start = start  # already moved back by the last shot's crossfade
    total = end_card_start + end_card
    timeline = {"voice": voice, "shots": shots, "end_card_start": round(end_card_start, 3),
                "end_card_seconds": end_card, "film_seconds": round(end_card_start + CROSSFADE_SEC, 3),
                "total_seconds": round(total, 3), "crossfade_seconds": CROSSFADE_SEC}
    return timeline


def run(ctx: Context) -> dict:
    tl = compute(ctx)
    ctx.manifest.measure("timeline", tl)
    atomic.write_json(OUTPUTS / "timing.json", tl)
    total = tl["total_seconds"]
    note = "" if 60 <= total <= 90 + 6 else "  (outside 60-90 s plus end card: adjust narration)"
    say(f"  timing: {len(tl['shots'])} shots, film {tl['film_seconds']:.1f} s + end card "
        f"{tl['end_card_seconds']} s = {total:.1f} s{note}")
    return tl
