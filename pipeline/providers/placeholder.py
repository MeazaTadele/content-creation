"""Stand-ins used while the story text is a placeholder or before keys exist.

They make no model calls: they let the whole pipeline (timing, caching, assembly) run end to
end offline. They are never written to runs.jsonl.
"""
from __future__ import annotations

from pathlib import Path

from .. import media
from ..calls import CallResult
from ..config import SAMPLE_RATE
from .base import ImageProvider, MusicProvider, TTSProvider

WORDS_PER_SEC = 2.6  # rough speaking rate, only used to size placeholder audio


class PlaceholderTTS(TTSProvider):
    name, model, licence, is_model = "placeholder", "tone", "n/a", False

    def synthesize(self, text, voice, style, out_wav, tmp_dir):
        words = max(1, len(text.split()))
        secs = max(1.2, words / WORDS_PER_SEC)
        # 0.25 s silence, a soft tone for the "speech", 0.35 s silence: exercises silence trimming
        media.run(["-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono:d=0.25",
                   "-f", "lavfi", "-i", f"sine=frequency=330:sample_rate={SAMPLE_RATE}:duration={secs:.2f}",
                   "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono:d=0.35",
                   "-filter_complex", "[1]volume=0.25[t];[0][t][2]concat=n=3:v=0:a=1",
                   "-c:a", "pcm_s16le", str(out_wav)])
        return CallResult(out_wav, {"chars": len(text)}, self.model)


class PlaceholderImage(ImageProvider):
    name, model, licence, is_model = "placeholder", "gradient", "n/a", False

    def generate(self, prompt, negative, seed, width, height, refs, out_png, tmp_dir):
        hue = seed % 360
        media.run(["-f", "lavfi", "-i", f"gradients=s={width}x{height}:c0=0x2b1d14:c1=0xc98b4a:seed={seed}:duration=1",
                   "-vf", f"hue=h={hue}", "-frames:v", "1", str(out_png)])
        return CallResult(out_png, {"images": 1}, self.model)


class PlaceholderMusic(MusicProvider):
    name, model, licence, is_model = "placeholder", "pad", "n/a", False

    def compose(self, caption, seconds, bpm, key, seed, instrumental, out_wav, tmp_dir):
        # a quiet two-note pad with slow tremolo; enough to test ducking and crossfades
        base = 196 + (seed % 5) * 22
        media.run(["-f", "lavfi", "-i", f"sine=frequency={base}:sample_rate={SAMPLE_RATE}:duration={seconds:.2f}",
                   "-f", "lavfi", "-i", f"sine=frequency={base * 1.5:.1f}:sample_rate={SAMPLE_RATE}:duration={seconds:.2f}",
                   "-filter_complex", "[0][1]amix=inputs=2:normalize=0,tremolo=f=0.3:d=0.4,volume=0.3,"
                   "afade=t=in:d=1.5",
                   "-ac", "1", "-c:a", "pcm_s16le", str(out_wav)])
        return CallResult(out_wav, {"seconds": seconds}, self.model)
