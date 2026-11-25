import copy
import json
from pathlib import Path

import pytest

from pipeline import contract, subtitles
from pipeline.calls import redact
from pipeline.fingerprint import fingerprint
from pipeline.manifest import Manifest
from pipeline.stages import timing
from pipeline.stages.base import Context

ROOT = Path(__file__).resolve().parent.parent
SB = json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8"))


def test_storyboard_is_valid():
    contract.validate(SB)


def test_schema_rejects_missing_reason():
    sb = copy.deepcopy(SB)
    del sb["shots"][0]["reason"]
    with pytest.raises(contract.ContractError, match="reason"):
        contract.validate(sb)


def test_schema_rejects_too_few_shots():
    sb = copy.deepcopy(SB)
    sb["shots"] = sb["shots"][:5]
    with pytest.raises(contract.ContractError):
        contract.validate(sb)


def test_semantic_check_unknown_character():
    sb = copy.deepcopy(SB)
    sb["shots"][0]["image"]["characters"] = ["nobody"]
    with pytest.raises(contract.ContractError, match="unknown character"):
        contract.validate(sb)


def test_placeholder_providers_need_placeholder_flag():
    sb = copy.deepcopy(SB)
    sb["placeholder"] = False
    with pytest.raises(contract.ContractError, match="placeholder"):
        contract.validate(sb)


def test_fingerprint_is_stable_and_order_independent():
    a = fingerprint("narration", 1, {"text": "x", "voice": "v"})
    b = fingerprint("narration", 1, {"voice": "v", "text": "x"})
    assert a == b


def test_fingerprint_changes_with_inputs_and_version():
    base = fingerprint("narration", 1, {"text": "x"})
    assert fingerprint("narration", 1, {"text": "y"}) != base
    assert fingerprint("narration", 2, {"text": "x"}) != base


def test_fingerprint_hashes_file_contents(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"one")
    first = fingerprint("keyframes", 1, {"ref": f})
    f.write_bytes(b"two")
    assert fingerprint("keyframes", 1, {"ref": f}) != first


def _ctx_with_narration(tmp_path, speech=3.0):
    m = Manifest(tmp_path / "manifest.json")
    for s in SB["shots"]:
        m.data["units"][f"narration/{SB['voice']['use']}/{s['id']}"] = {
            "speech_start": 0.2, "speech_end": 0.2 + speech, "speech_seconds": speech}
    return Context(sb=SB, manifest=m, tmp_dir=tmp_path)


def test_timing_uses_measured_speech_and_crossfades(tmp_path):
    tl = timing.compute(_ctx_with_narration(tmp_path, speech=5.0))
    shots = tl["shots"]
    assert all(s["duration"] >= 5.0 for s in shots)
    for a, b in zip(shots, shots[1:]):
        # the next shot starts where this one ends, minus any crossfade
        assert b["start"] == pytest.approx(a["start"] + a["duration"] - a["overlap_out"], abs=1e-3)
        # narration never overlaps across shots
        assert b["narration_start"] >= a["narration_end"] + timing.MIN_GAP - 1e-6


def test_timing_respects_minimum_shot_length(tmp_path):
    tl = timing.compute(_ctx_with_narration(tmp_path, speech=0.5))
    assert all(s["duration"] >= 3.0 for s in tl["shots"])


def test_subtitles_wrap_and_never_exceed_two_lines(tmp_path):
    tl = timing.compute(_ctx_with_narration(tmp_path, speech=4.0))
    for e in subtitles.events(SB, tl):
        assert 1 <= len(e["lines"]) <= 2
        assert all(len(line) <= subtitles.MAX_CHARS for line in e["lines"])
        assert e["end"] > e["start"]


def test_redact_hides_keys():
    text = 'error with key AIzaSyA1234567890abcdefghijKLMNOP and Bearer abcdefghijklmnopqrstuvwxyz123456'
    out = redact(text)
    assert "AIza" not in out and "abcdefghijklmnopqrstuvwxyz123456" not in out
