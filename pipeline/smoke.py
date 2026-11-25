"""Smoke test: one small call to each provider whose key is set, logged to runs.jsonl with latency.

Uses neutral test content only, never anything about real people.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from . import calls
from .config import OUTPUTS
from .fingerprint import fingerprint
from .stages.base import rel, say

TEST_AM = "ሰላም። ይህ የድምፅ ሙከራ ነው።"  # "Hello. This is a voice test."
TEST_IMAGE = "a ceramic coffee pot on a wooden table in soft morning light, warm painted illustration"


def _run(name, fn):
    try:
        fn()
        say(f"  ok      {name}")
        return True
    except Exception as e:  # noqa: BLE001
        say(f"  FAILED  {name}: {calls.redact(str(e))[:300]}")
        return False


def run() -> None:
    out = OUTPUTS / "smoke"
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="smoke-"))
    results = {}

    if os.environ.get("GEMINI_API_KEY"):
        from .providers.gemini import GeminiTTS
        p = GeminiTTS()

        def gemini():
            p.check_ready()
            dst = out / "gemini_tts.wav"
            calls.call_model(stage="smoke", unit="gemini-tts", provider="gemini", model=p.model,
                             params={"voice": "Kore"}, seed=None, fingerprint=fingerprint("smoke", 1, {"t": TEST_AM}),
                             fn=lambda: p.synthesize(TEST_AM, None, None, dst, tmp), output=rel(dst))
        results["gemini"] = _run(f"Gemini TTS", gemini)
    else:
        say("  skip    Gemini (GEMINI_API_KEY not set)")

    if os.environ.get("CLOUDFLARE_API_TOKEN") and os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        from .providers.cloudflare import CloudflareFlux
        p = CloudflareFlux()

        def cf():
            dst = out / "cloudflare_flux.png"
            calls.call_model(stage="smoke", unit="cloudflare-flux", provider="cloudflare-flux", model=p.model,
                             params={"size": [512, 512]}, seed=1, fingerprint=fingerprint("smoke", 1, {"p": TEST_IMAGE}),
                             fn=lambda: p.generate(TEST_IMAGE, None, 1, 512, 512, [], dst, tmp), output=rel(dst))
        results["cloudflare"] = _run("Cloudflare FLUX", cf)
    else:
        say("  skip    Cloudflare (CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN not set)")

    if os.environ.get("ELEVENLABS_API_KEY"):
        from .providers.elevenlabs import ElevenLabsTTS
        p = ElevenLabsTTS()
        voice = os.environ.get("ELEVENLABS_VOICE_ID", "")

        def el():
            dst = out / "elevenlabs_tts.wav"
            calls.call_model(stage="smoke", unit="elevenlabs-tts", provider="elevenlabs", model=p.model,
                             params={"voice": voice}, seed=None, fingerprint=fingerprint("smoke", 1, {"t": TEST_AM}),
                             fn=lambda: p.synthesize(TEST_AM, voice, None, dst, tmp), output=rel(dst))
        results["elevenlabs"] = _run("ElevenLabs TTS", el) if voice else False
        if not voice:
            say("  skip    ElevenLabs TTS call (set ELEVENLABS_VOICE_ID to a voice id first)")
    else:
        say("  skip    ElevenLabs (ELEVENLABS_API_KEY not set)")

    if os.environ.get("KAGGLE_USERNAME") and (os.environ.get("KAGGLE_KEY") or os.environ.get("KAGGLE_API_TOKEN")):
        def kg():
            def call():
                r = subprocess.run(["kaggle", "kernels", "list", "--mine", "--page-size", "1"],
                                   capture_output=True, text=True, timeout=120)
                if r.returncode != 0:
                    raise calls.FatalError(r.stderr.strip()[:300] or r.stdout.strip()[:300])
                return calls.CallResult(None, {})
            calls.call_model(stage="smoke", unit="kaggle-auth", provider="kaggle", model="kaggle-api",
                             params={}, seed=None, fingerprint=fingerprint("smoke", 1, {"k": 1}), fn=call)
        results["kaggle"] = _run("Kaggle API authentication", kg)
    else:
        say("  skip    Kaggle (KAGGLE_USERNAME / KAGGLE_KEY not set)")

    say(f"smoke test: {sum(results.values())} of {len(results)} providers ok; details in runs.jsonl")
