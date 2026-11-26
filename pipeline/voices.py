"""Voice casting: several OmniVoice voices reading the same line, with no sample voice to follow,
so the author can pick the warmest, most natural narrator. The chosen clip (AI-generated, not a
real person's voice) becomes voice.references.omnivoice in the storyboard.

    python -m pipeline.voices <shot id> [number of voices]
"""
from __future__ import annotations

import shutil
import sys

from . import config, contract, kaggle
from .calls import log_job_unit
from .config import OUTPUTS
from .stages.base import rel, say


def main(shot_id: str = "s09", n: int = 5) -> None:
    config.load_env()
    sb = contract.load()
    text = next(s for s in sb["shots"] if s["id"] == shot_id)["narration"]["am"]
    units = [{"unit": f"voice_{k}", "model": "omnivoice", "text": text, "seed": 100 + k,
              "fingerprint": f"casting-{shot_id}-{k}"} for k in range(n)]
    job_id, res = kaggle.run_job("tts-open", units, {}, timeout=3600, gpu=False,
                                 settings={"device": "cpu"}, slug="heritage-voice-casting")
    out = OUTPUTS / "voicebench" / "casting"
    out.mkdir(parents=True, exist_ok=True)
    for u in units:
        r = kaggle.read_result(res, u["unit"])
        ok = bool(r and r.get("status") == "ok" and (res / r["output"]).exists())
        dst = out / f"{shot_id}_{u['unit']}.wav"
        if ok:
            shutil.copy2(res / r["output"], dst)
        say(f"  {u['unit']}: {'ok' if ok else (r or {}).get('error', 'missing')}")
        log_job_unit(stage="voicecasting", unit=u["unit"], provider="omnivoice", model=(r or {}).get("model", "omnivoice"),
                     params={"shot": shot_id, "reference": None}, seed=u["seed"], status=(r or {}).get("status", "missing"),
                     latency_ms=int(((r or {}).get("seconds") or 0) * 1000), gpu_seconds=0,
                     fingerprint=u["fingerprint"], output=rel(dst) if ok else None, job_id=job_id,
                     error=(r or {}).get("error"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "s09", int(sys.argv[2]) if len(sys.argv) > 2 else 5)
