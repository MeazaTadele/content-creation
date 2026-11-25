"""English subtitles from the timing: at most two lines of about 40 characters on screen at once."""
from __future__ import annotations

MAX_CHARS = 40
MAX_LINES = 2


def wrap(text: str, width: int = MAX_CHARS) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def events(sb: dict, timeline: dict) -> list[dict]:
    """One or more subtitle events per shot, timed to that shot's spoken words."""
    out = []
    by_id = {s["id"]: s for s in sb["shots"]}
    shots = timeline["shots"]
    for i, t in enumerate(shots):
        text = by_id[t["id"]]["narration"]["en"].strip()
        start, end = t["narration_start"], t["narration_end"]
        # hold a little after the words, but never into the next shot's words
        hold_to = end + 0.4
        if i + 1 < len(shots):
            hold_to = min(hold_to, shots[i + 1]["narration_start"] - 0.05)
        end = max(end, hold_to)
        lines = wrap(text)
        chunks = [lines[k:k + MAX_LINES] for k in range(0, len(lines), MAX_LINES)] or [[""]]
        total_chars = sum(len(" ".join(c)) for c in chunks) or 1
        t0 = start
        for c in chunks:
            share = len(" ".join(c)) / total_chars
            t1 = t0 + (end - start) * share
            out.append({"start": round(t0, 3), "end": round(t1, 3), "lines": c})
            t0 = t1
    return out


def _ts_srt(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ts_ass(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def srt(evts: list[dict]) -> str:
    blocks = []
    for i, e in enumerate(evts, 1):
        blocks.append(f"{i}\n{_ts_srt(e['start'])} --> {_ts_srt(e['end'])}\n" + "\n".join(e["lines"]))
    return "\n\n".join(blocks) + "\n"


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


# Phone safe area: keep 9:16 subtitles well above the bottom ~18% where app buttons sit.
STYLES = {
    "9x16": {"size": 56, "margin_v": 360, "margin_lr": 90},
    "16x9": {"size": 50, "margin_v": 70, "margin_lr": 160},
}


def ass(evts: list[dict], ratio: str, width: int, height: int, end_card: dict | None = None) -> str:
    st = STYLES[ratio]
    head = (
        "[Script Info]\nScriptType: v4.00+\nWrapStyle: 2\nScaledBorderAndShadow: yes\n"
        f"PlayResX: {width}\nPlayResY: {height}\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
        "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Sub,DejaVu Sans,{st['size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,"
        f"3,1,2,{st['margin_lr']},{st['margin_lr']},{st['margin_v']},1\n"
        f"Style: Card,DejaVu Sans,{int(st['size'] * 0.95)},&H00F2F2F2,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,"
        f"100,100,0,0,1,0,0,5,{st['margin_lr']},{st['margin_lr']},0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    rows = [f"Dialogue: 0,{_ts_ass(e['start'])},{_ts_ass(e['end'])},Sub,,0,0,0,,"
            + "\\N".join(_esc(l) for l in e["lines"]) for e in evts]
    if end_card:
        width = 26 if ratio == "9x16" else 50
        text = "\\N\\N".join("\\N".join(_esc(x) for x in wrap(l, width)) for l in end_card["lines"])
        rows.append(f"Dialogue: 0,{_ts_ass(end_card['start'] + 0.4)},{_ts_ass(end_card['end'])},Card,,0,0,0,,"
                    f"{{\\fad(400,300)}}{text}")
    return head + "\n".join(rows) + "\n"
