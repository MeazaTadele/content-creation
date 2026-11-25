"""FFmpeg helpers. Nothing here calls an AI model."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .config import SAMPLE_RATE


class MediaError(RuntimeError):
    pass


def run(args: list[str], quiet: bool = True) -> subprocess.CompletedProcess:
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y", *args]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        tail = "\n".join(p.stderr.strip().splitlines()[-25:])
        raise MediaError(f"ffmpeg failed ({p.returncode}):\n{tail}")
    return p


def duration(path: Path) -> float:
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "json", str(path)], capture_output=True, text=True)
    if p.returncode != 0:
        raise MediaError(p.stderr)
    return float(json.loads(p.stdout)["format"]["duration"])


def to_wav(src: Path, dst: Path) -> None:
    """Any audio in, 48 kHz mono 16-bit WAV out."""
    run(["-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)])


def pcm_to_wav(pcm: bytes, rate: int, dst: Path, tmp_dir: Path) -> None:
    raw = tmp_dir / (dst.stem + ".raw")
    raw.write_bytes(pcm)
    try:
        run(["-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", str(raw),
             "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)])
    finally:
        raw.unlink(missing_ok=True)


_SIL_START = re.compile(r"silence_start: (-?[\d.]+)")
_SIL_END = re.compile(r"silence_end: (-?[\d.]+)")


def speech_bounds(path: Path, noise_db: float = -40.0, min_sil: float = 0.08) -> tuple[float, float, float]:
    """(speech_start, speech_end, file_duration): leading and trailing silence trimmed.

    A WAV's length is not the length of the words in it; this measures the words.
    """
    total = duration(path)
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-af",
                        f"silencedetect=noise={noise_db}dB:d={min_sil}", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in _SIL_START.findall(p.stderr)]
    ends = [float(x) for x in _SIL_END.findall(p.stderr)]
    speech_start, speech_end = 0.0, total
    if starts and starts[0] <= 0.01 and ends:
        speech_start = ends[0]
    if starts and (len(ends) < len(starts) or ends[-1] >= total - 0.02):
        last_start = starts[-1]
        if last_start > speech_start:
            speech_end = last_start
    if speech_end - speech_start < 0.2:  # nothing detected as speech: keep the whole file
        speech_start, speech_end = 0.0, total
    return round(speech_start, 3), round(speech_end, 3), round(total, 3)


def loudness(path: Path) -> dict:
    """Integrated loudness (LUFS) and true peak (dBTP) of a file's audio."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-af",
                        "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    if not m:
        raise MediaError("could not measure loudness")
    j = json.loads(m.group(0))
    return {"lufs": float(j["input_i"]), "true_peak_db": float(j["input_tp"]), "lra": float(j["input_lra"]),
            "_raw": j}


def loudnorm_two_pass(src: Path, dst: Path, target_i: float, target_tp: float, lra: float = 11.0) -> dict:
    """Two-pass EBU R128 normalisation of an audio file, as the brief recommends."""
    m = loudness(src)["_raw"]
    af = (f"loudnorm=I={target_i}:TP={target_tp}:LRA={lra}:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}:linear=true")
    run(["-i", str(src), "-af", af, "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)])
    return loudness(dst)
