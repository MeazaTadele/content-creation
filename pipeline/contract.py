"""Load storyboard.json and validate it against the schema, plus the rules a schema can't express."""
from __future__ import annotations

import json
from pathlib import Path

from .config import ROOT, SCHEMA_PATH, STORYBOARD_PATH


class ContractError(ValueError):
    pass


def load(path: Path = STORYBOARD_PATH) -> dict:
    try:
        sb = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ContractError(f"storyboard not found: {path}") from None
    except json.JSONDecodeError as e:
        raise ContractError(f"storyboard is not valid JSON: line {e.lineno}, column {e.colno}: {e.msg}") from None
    validate(sb)
    return sb


def validate(sb: dict) -> None:
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(sb), key=lambda e: list(e.absolute_path))
    problems = [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}" for e in errors]

    if not problems:
        problems += _semantic_checks(sb)
    if problems:
        raise ContractError("storyboard.json is invalid:\n  - " + "\n  - ".join(problems))


def _semantic_checks(sb: dict) -> list[str]:
    out = []
    shot_ids = [s["id"] for s in sb["shots"]]
    if len(set(shot_ids)) != len(shot_ids):
        out.append("shots: shot ids must be unique")
    char_ids = {c["id"] for c in sb["characters"]}
    for s in sb["shots"]:
        for c in s["image"].get("characters", []):
            if c not in char_ids:
                out.append(f"shots/{s['id']}: unknown character '{c}'")
    for i, s in enumerate(sb["shots"]):
        im = s["image"]
        src = im.get("scene_from")
        if src and src not in shot_ids[:i]:
            out.append(f"shots/{s['id']}: scene_from '{src}' must be an earlier shot")
        for field in ("edit_from", "locked"):
            for ratio, f in (im.get(field) or {}).items():
                if not (ROOT / f).exists():
                    out.append(f"shots/{s['id']}: image.{field}.{ratio} file not found: {f}")
        if im.get("provider") == "kaggle-inpaint" and not (im.get("inpaint") and im.get("edit_from")):
            out.append(f"shots/{s['id']}: kaggle-inpaint needs image.inpaint and image.edit_from")
    if sb["voice"]["use"] not in sb["voice"]["compare"]:
        out.append("voice/use must be one of voice/compare")
    cues = sb["music"]["cues"]
    if cues[0]["from_shot"] != shot_ids[0]:
        out.append("music/cues: the first cue must start at the first shot")
    for c in cues:
        if c["from_shot"] not in shot_ids:
            out.append(f"music/cues/{c['id']}: unknown shot '{c['from_shot']}'")
    order = [shot_ids.index(c["from_shot"]) for c in cues if c["from_shot"] in shot_ids]
    if order != sorted(order):
        out.append("music/cues: cues must be in shot order")
    uses_placeholder = "placeholder" in (sb["voice"]["use"], sb["providers"]["keyframes"], sb["providers"]["music"])
    if uses_placeholder and not sb.get("placeholder"):
        out.append("placeholder providers are only allowed while 'placeholder' is true")
    return out
