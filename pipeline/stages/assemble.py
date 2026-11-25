"""Assembly: FFmpeg only, no AI. Same inputs, same film.

Per aspect ratio: shot segments (a Wan clip, or a Ken Burns move over the keyframe), joined
with the storyboard's transitions, then an end card. The soundtrack is built once: narration
placed on the timeline, the chosen music cues crossfaded, music ducked under the voice with
sidechaincompress, then two-pass loudness normalisation to -14 LUFS / -1 dBTP. Subtitles are
burned in per ratio. Every intermediate is cached by fingerprint.
"""
from __future__ import annotations

from pathlib import Path

from .. import atomic, media, subtitles
from ..config import (CANVAS, CROSSFADE_SEC, DUCK, FPS, MUSIC_STEM_LUFS, NARRATION_STEM_LUFS, OUTPUTS,
                      ROOT, SAMPLE_RATE, TARGET_LUFS, TARGET_TP)
from ..fingerprint import fingerprint
from . import keyframes, music, shots
from .base import Context, Unit, check_stage_version, execute, out_path, rel, say

STAGE = "assemble"
STAGE_VERSION = 2  # 2: clips play, then drift over their last frame (decision 29a)
MOVES = ["in", "right", "out", "left"]
CLIP_HEAD_TRIM = 0.2  # many generated clips have a weak first moment


# ---------------------------------------------------------------- picture
def _kenburns_filter(move: str, frames: int, w: int, h: int) -> str:
    n = max(frames - 1, 1)
    center = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if move == "in":
        z, xy = f"1+0.12*on/{n}", center
    elif move == "out":
        z, xy = f"1.12-0.12*on/{n}", center
    elif move == "left":
        z, xy = "1.12", f"x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-(ih/zoom/2)'"
    else:
        z, xy = "1.12", f"x='(iw-iw/zoom)*on/{n}':y='ih/2-(ih/zoom/2)'"
    # upscale first so the slow move doesn't jitter
    return (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
            f"zoompan=z='{z}':{xy}:d={frames}:s={w}x{h}:fps={FPS},format=yuv420p")


DRIFT_ZOOM = 0.06  # how far the camera drifts in after a clip ends (decision 29a)


def _render_clip_with_drift(clip: Path, ratio: str, w: int, h: int, dur: float, tmp_dir: Path, out: Path) -> dict:
    """Decision 29 (a): play the generated clip, then keep the camera drifting slowly over its last
    frame until the shot's narration is done. The drift starts at the clip's last framing, so there
    is no jump. 16:9 shows the vertical result over a blurred copy of itself (decision 6)."""
    vw, vh = CANVAS["9x16"]
    clip_len = max(0.0, media.duration(clip) - CLIP_HEAD_TRIM)
    play = min(clip_len, dur)
    rest = max(0.0, dur - play)
    stem = out.stem
    part1 = tmp_dir / f"{stem}_play.mp4"
    media.run(["-ss", str(CLIP_HEAD_TRIM), "-i", str(clip), "-t", f"{play:.3f}", "-vf",
               f"scale={vw}:{vh}:force_original_aspect_ratio=increase,crop={vw}:{vh},fps={FPS},format=yuv420p",
               "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(part1)])
    parts = [part1]
    if rest > 1 / FPS:
        last = tmp_dir / f"{stem}_last.png"
        media.run(["-sseof", "-0.1", "-i", str(part1), "-frames:v", "1", "-update", "1", str(last)])
        frames = max(1, round(rest * FPS))
        n = max(frames - 1, 1)
        part2 = tmp_dir / f"{stem}_drift.mp4"
        media.run(["-i", str(last), "-vf",
                   f"scale={vw * 2}:{vh * 2},zoompan=z='1+{DRIFT_ZOOM}*on/{n}':x='iw/2-(iw/zoom/2)':"
                   f"y='ih/2-(ih/zoom/2)':d={frames}:s={vw}x{vh}:fps={FPS},format=yuv420p",
                   "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                   str(part2)])
        parts.append(part2)
    joined = tmp_dir / f"{stem}_vertical.mp4"
    if len(parts) == 1:
        joined = part1
    else:
        lst = tmp_dir / f"{stem}_list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        media.run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    if ratio == "9x16":
        media.run(["-i", str(joined), "-vf", f"fps={FPS},tpad=stop_mode=clone:stop_duration=1,trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p",
                   "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(out)])
    else:
        media.run(["-i", str(joined), "-filter_complex",
                   f"[0:v]split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                   f"boxblur=40:4,eq=brightness=-0.08[bg];[b]scale=-2:{h}[fg];[bg][fg]overlay=(W-w)/2:0,"
                   f"fps={FPS},tpad=stop_mode=clone:stop_duration=1,trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p[v]",
                   "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", str(out)])
    return {"clip_seconds": round(play, 3), "drift_seconds": round(rest, 3)}


def segment_units(ctx: Context, timeline: dict, ratio: str) -> list[Unit]:
    w, h = CANVAS[ratio]
    out = []
    for i, t in enumerate(timeline["shots"]):
        shot = ctx.shot(t["id"])
        dur = t["duration"]
        frames = round(dur * FPS)
        clip = None if shot["motion"].get("kenburns") else shots.clip_path(ctx, shot["id"])
        if clip is not None:
            source, kind, move = clip, "clip", None
        else:
            source = keyframes.path(ctx, shot["id"], ratio)
            if source is None:
                raise RuntimeError(f"no keyframe for {shot['id']} ({ratio}); run the keyframes stage")
            kind, move = "kenburns", shot["motion"].get("kenburns_move", MOVES[i % len(MOVES)])
        fp = fingerprint(STAGE, STAGE_VERSION, {"part": "segment", "ratio": ratio, "source": source,
                                                 "kind": kind, "move": move, "frames": frames})
        unit = f"segments/{ratio}/{shot['id']}"
        dst = out_path(STAGE, unit, fp, "mp4")

        def run(tmp, tmp_dir, source=source, kind=kind, move=move, frames=frames, dur=dur):
            if kind == "clip":
                extra = _render_clip_with_drift(source, ratio, w, h, dur, tmp_dir, tmp)
                return {"kind": kind, "move": "clip+drift", "frames": frames, **extra}
            else:
                media.run(["-i", str(source), "-vf", _kenburns_filter(move, frames, w, h), "-frames:v",
                           str(frames), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                           "-r", str(FPS), str(tmp)])
            return {"kind": kind, "move": move, "frames": frames}

        out.append(Unit(STAGE, unit, fp, dst, f"{kind} segment, {dur:.2f} s", run))
    return out


def endcard_unit(ctx: Context, timeline: dict, ratio: str) -> Unit:
    w, h = CANVAS[ratio]
    secs = timeline["end_card_seconds"] + CROSSFADE_SEC
    fp = fingerprint(STAGE, STAGE_VERSION, {"part": "endcard-bg", "ratio": ratio, "seconds": secs})
    unit = f"segments/{ratio}/end-card"
    dst = out_path(STAGE, unit, fp, "mp4")

    def run(tmp, tmp_dir):
        media.run(["-f", "lavfi", "-i", f"color=c=0x15110e:s={w}x{h}:r={FPS}:d={secs:.3f}",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(tmp)])
        return {"kind": "end-card"}

    return Unit(STAGE, unit, fp, dst, "end card background", run)


def join_unit(ctx: Context, timeline: dict, ratio: str, seg_paths: list[Path]) -> Unit:
    """Join segments: crossfade where the storyboard says so, a straight cut otherwise."""
    overlaps = [t["overlap_out"] for t in timeline["shots"]]
    starts = [t["start"] for t in timeline["shots"]] + [timeline["end_card_start"]]
    fp = fingerprint(STAGE, STAGE_VERSION, {"part": "join", "ratio": ratio, "segments": seg_paths,
                                             "overlaps": overlaps, "starts": starts})
    unit = f"picture/{ratio}"
    dst = out_path(STAGE, unit, fp, "mp4")

    def run(tmp, tmp_dir):
        args, chain = [], []
        for p in seg_paths:
            args += ["-i", str(p)]
        # one timebase and frame rate everywhere, or xfade refuses to mix concat output with a file
        for k in range(len(seg_paths)):
            chain.append(f"[{k}:v]fps={FPS},settb=AVTB,setpts=PTS-STARTPTS[s{k}]")
        cur = "[s0]"
        for k in range(1, len(seg_paths)):
            ov = overlaps[k - 1]
            nxt = f"[s{k}]"
            label = f"[j{k}]"
            if ov > 0:
                chain.append(f"{cur}{nxt}xfade=transition=fade:duration={ov}:offset={starts[k]:.3f},"
                             f"settb=AVTB{label}")
            else:
                chain.append(f"{cur}{nxt}concat=n=2:v=1:a=0,settb=AVTB{label}")
            cur = label
        chain.append(f"{cur}format=yuv420p[v]")
        media.run([*args, "-filter_complex", ";".join(chain), "-map", "[v]", "-an", "-c:v", "libx264",
                   "-preset", "veryfast", "-crf", "16", "-r", str(FPS), str(tmp)])
        return {"seconds": round(media.duration(tmp), 3)}

    return Unit(STAGE, unit, fp, dst, f"join {len(seg_paths)} segments", run)


# ---------------------------------------------------------------- sound
def narration_inputs(ctx: Context, timeline: dict) -> list[dict]:
    voice = timeline["voice"]
    items = []
    for t in timeline["shots"]:
        e = ctx.manifest.get("narration", f"{voice}/{t['id']}")
        items.append({"path": ROOT / e["output"], "trim": t["speech_trim"], "at": t["narration_start"]})
    return items


def music_inputs(ctx: Context, timeline: dict, placeholder: bool) -> list[dict]:
    sb = ctx.sb
    items = []
    spans = music.cue_spans(sb, timeline)
    for cue, span in zip(sb["music"]["cues"], spans):
        p = music.chosen(ctx, cue) if not placeholder else music.chosen(ctx, {**cue, "use": 0})
        if p is None:
            raise RuntimeError(f"no music for cue '{cue['id']}'; run the music stage")
        items.append({"path": p, "start": span["start"], "seconds": span["seconds"]})
    return items


def soundtrack_unit(ctx: Context, timeline: dict, music_items: list[dict], name: str) -> Unit:
    narr = narration_inputs(ctx, timeline)
    total = timeline["total_seconds"]
    fp = fingerprint(STAGE, STAGE_VERSION, {
        "part": "soundtrack", "narration": [{**n, "path": n["path"]} for n in narr],
        "music": [{**m, "path": m["path"]} for m in music_items], "total": total, "duck": DUCK,
        "targets": [NARRATION_STEM_LUFS, MUSIC_STEM_LUFS, TARGET_LUFS, TARGET_TP]})
    unit = f"sound/{name}"
    dst = out_path(STAGE, unit, fp, "wav")

    def run(tmp, tmp_dir):
        sr = SAMPLE_RATE
        # 1. narration stem: each line trimmed to its words, placed on the timeline
        args, parts = [], []
        for i, n in enumerate(narr):
            args += ["-i", str(n["path"])]
            a, b = n["trim"]
            parts.append(f"[{i}:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
                         f"adelay={int(n['at'] * 1000)}:all=1[n{i}]")
        mix = "".join(f"[n{i}]" for i in range(len(narr)))
        parts.append(f"{mix}amix=inputs={len(narr)}:normalize=0,apad=whole_dur={total:.3f}[out]")
        narr_raw = tmp_dir / f"{name}_narration_raw.wav"
        media.run([*args, "-filter_complex", ";".join(parts), "-map", "[out]", "-ac", "1", "-ar", str(sr),
                   "-c:a", "pcm_s16le", "-t", f"{total:.3f}", str(narr_raw)])
        narr_stem = tmp_dir / f"{name}_narration.wav"
        media.loudnorm_two_pass(narr_raw, narr_stem, NARRATION_STEM_LUFS, -3.0)

        # 2. music stem: cues trimmed, faded and overlapped into one bed
        args, parts = [], []
        last = len(music_items) - 1
        for i, m in enumerate(music_items):
            args += ["-i", str(m["path"])]
            fades = f"afade=t=in:d={2.0 if i else 1.5}"
            if i < last:
                fades += f",afade=t=out:st={m['seconds'] - 2.0:.3f}:d=2"
            else:
                fades += f",afade=t=out:st={max(0.0, m['seconds'] - 3.5):.3f}:d=3.5"
            parts.append(f"[{i}:a]atrim=duration={m['seconds']:.3f},asetpts=PTS-STARTPTS,{fades},"
                         f"adelay={int(m['start'] * 1000)}:all=1[m{i}]")
        mix = "".join(f"[m{i}]" for i in range(len(music_items)))
        parts.append(f"{mix}amix=inputs={len(music_items)}:normalize=0,apad=whole_dur={total:.3f}[out]")
        music_raw = tmp_dir / f"{name}_music_raw.wav"
        media.run([*args, "-filter_complex", ";".join(parts), "-map", "[out]", "-ac", "1", "-ar", str(sr),
                   "-c:a", "pcm_s16le", "-t", f"{total:.3f}", str(music_raw)])
        music_stem = tmp_dir / f"{name}_music.wav"
        media.loudnorm_two_pass(music_raw, music_stem, MUSIC_STEM_LUFS, -6.0)

        # 3. duck the music under the voice, mix, then master to -14 LUFS / -1 dBTP
        d = DUCK
        pre = tmp_dir / f"{name}_premaster.wav"
        media.run(["-i", str(music_stem), "-i", str(narr_stem), "-filter_complex",
                   f"[1:a]asplit=2[sc][voice];[0:a][sc]sidechaincompress=threshold={d['threshold']}:"
                   f"ratio={d['ratio']}:attack={d['attack']}:release={d['release']}[ducked];"
                   f"[ducked][voice]amix=inputs=2:normalize=0[out]",
                   "-map", "[out]", "-ac", "2", "-ar", str(sr), "-c:a", "pcm_s16le", "-t", f"{total:.3f}", str(pre)])
        measured = media.loudnorm_two_pass(pre, tmp, TARGET_LUFS, TARGET_TP)
        return {"lufs": measured["lufs"], "true_peak_db": measured["true_peak_db"]}

    return Unit(STAGE, unit, fp, dst, f"soundtrack ({name})", run)


# ---------------------------------------------------------------- final
def final_unit(ctx: Context, timeline: dict, ratio: str, picture: Path | None, sound: Path,
               ass_text: str, name: str) -> Unit:
    w, h = CANVAS[ratio]
    total = timeline["total_seconds"]
    fp = fingerprint(STAGE, STAGE_VERSION, {"part": "final", "ratio": ratio, "picture": picture,
                                             "sound": sound, "ass": ass_text, "total": total})
    dst = OUTPUTS / "final" / f"{name}_{ratio}.mp4"
    unit = f"final/{name}_{ratio}"

    def run(tmp, tmp_dir):
        ass_path = tmp_dir / f"{name}_{ratio}.ass"
        ass_path.write_text(ass_text, encoding="utf-8")
        src = (["-i", str(picture)] if picture else
               ["-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={FPS}:d={total:.3f}"])
        esc = str(ass_path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        media.run([*src, "-i", str(sound), "-vf", f"ass='{esc}',format=yuv420p", "-map", "0:v", "-map", "1:a",
                   "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(FPS), "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE), "-t", f"{total:.3f}",
                   "-movflags", "+faststart", str(tmp)])
        m = media.loudness(tmp)
        return {"ratio": ratio, "seconds": round(media.duration(tmp), 3), "lufs": m["lufs"],
                "true_peak_db": m["true_peak_db"], "bytes": tmp.stat().st_size}

    return Unit(STAGE, unit, fp, dst, f"{name} {ratio} export", run)


def _ass_for(ctx: Context, timeline: dict, ratio: str, with_card: bool) -> str:
    w, h = CANVAS[ratio]
    evts = subtitles.events(ctx.sb, timeline)
    card = None
    if with_card:
        card = {"lines": ctx.sb["end_card"]["lines"], "start": timeline["end_card_start"],
                "end": timeline["total_seconds"]}
    return subtitles.ass(evts, ratio, w, h, card)


def _write_srt(ctx: Context, timeline: dict) -> None:
    atomic.write_bytes(OUTPUTS / "final" / "subtitles_en.srt",
                       subtitles.srt(subtitles.events(ctx.sb, timeline)).encode("utf-8"))


def run_film(ctx: Context, timeline: dict) -> dict:
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    stats = {"cached": 0, "generated": 0, "failed": 0}

    def add(s):
        for k in stats:
            stats[k] += s[k]

    snd = soundtrack_unit(ctx, timeline, music_inputs(ctx, timeline, placeholder=False), "film")
    add(execute(ctx, [snd]))
    for ratio in ("9x16", "16x9"):
        segs = segment_units(ctx, timeline, ratio) + [endcard_unit(ctx, timeline, ratio)]
        add(execute(ctx, segs))
        j = join_unit(ctx, timeline, ratio, [u.output for u in segs])
        add(execute(ctx, [j]))
        fin = final_unit(ctx, timeline, ratio, j.output, snd.output, _ass_for(ctx, timeline, ratio, True), "film")
        add(execute(ctx, [fin]))
        e = ctx.manifest.get(STAGE, fin.unit)
        if e:
            say(f"  {rel(fin.output)}: {e['seconds']:.1f} s, {e['lufs']:.1f} LUFS, "
                f"true peak {e['true_peak_db']:.1f} dB, {e['bytes'] / 1e6:.1f} MB")
            ctx.manifest.measure(f"loudness_{ratio}", {"lufs": e["lufs"], "true_peak_db": e["true_peak_db"]})
    _write_srt(ctx, timeline)
    return stats


def run_radio(ctx: Context, timeline: dict) -> dict:
    """The radio cut: narration over placeholder music on a black screen, for user test 1."""
    check_stage_version(ctx.manifest, STAGE, STAGE_VERSION, __file__)
    snd = soundtrack_unit(ctx, timeline, music_inputs(ctx, timeline, placeholder=True), "radio")
    s1 = execute(ctx, [snd])
    fin = final_unit(ctx, timeline, "9x16", None, snd.output, _ass_for(ctx, timeline, "9x16", False), "radio_cut")
    s2 = execute(ctx, [fin])
    _write_srt(ctx, timeline)
    e = ctx.manifest.get(STAGE, fin.unit)
    if e:
        say(f"  {rel(fin.output)}: {e['seconds']:.1f} s, {e['lufs']:.1f} LUFS")
    return {k: s1[k] + s2[k] for k in s1}
