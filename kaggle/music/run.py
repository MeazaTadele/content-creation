"""Kaggle script: ACE-Step 1.5 music candidates for every unit in job.json (decisions 8 and 14).

Runs the turbo DiT only (no 5 Hz language model), so the cue description in storyboard.json is
used as written instead of being rewritten by the model. On the T4 the model picks float16 by
itself (no fast bfloat16 before Ampere). Each candidate and its result file are written as soon as
it is done, so a job that stops early keeps every finished candidate.
"""
import glob
import json
import os
import subprocess
import sys
import time
import traceback

WORK = "/kaggle/working"
REPO = "https://github.com/ace-step/ACE-Step-1.5.git"
SRC = "/kaggle/temp/ace15"
MODEL = "acestep-v15-turbo"


def inputs_dir():
    return os.path.dirname(glob.glob("/kaggle/input/**/job.json", recursive=True)[0])


def install():
    """Keep Kaggle's own torch; install only what the inference path imports. Kaggle runs Python 3.13,
    newer than ACE-Step lists (3.11-3.12), so the version check is skipped."""
    if not os.path.exists(SRC):
        subprocess.run(["git", "clone", "-q", "--depth", "1", REPO, SRC], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers>=4.51.0,<4.58.0", "diffusers>=0.37.0",
                    "accelerate>=1.12.0", "soundfile", "loguru", "einops", "scipy", "numba", "diskcache", "toml",
                    "vector-quantize-pytorch>=1.27.15", "matplotlib"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "--ignore-requires-python", "-e", SRC], check=True)
    sys.path.insert(0, SRC)


def main():
    install()
    os.environ.setdefault("ACESTEP_CHECKPOINTS_DIR", os.path.join(SRC, "checkpoints"))
    import soundfile as sf
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music

    job = json.load(open(os.path.join(inputs_dir(), "job.json")))
    t0 = time.time()
    dit = AceStepHandler()
    msg, ok = dit.initialize_service(project_root=SRC, config_path=MODEL, device="cuda", offload_to_cpu=False)
    print(f"model {MODEL}: ok={ok} in {time.time() - t0:.0f} s: {str(msg)[:300]}", flush=True)
    for u in job["units"]:
        res = {"unit": u["unit"], "fingerprint": u["fingerprint"], "model": f"ACE-Step/{MODEL}"}
        t1 = time.time()
        try:
            if not ok:
                raise RuntimeError(f"model did not load: {str(msg)[:300]}")
            params = GenerationParams(task_type="text2music", thinking=False, caption=u["caption"],
                                      lyrics="[Instrumental]" if u.get("instrumental", True) else "",
                                      instrumental=u.get("instrumental", True), bpm=u.get("bpm"),
                                      keyscale=u.get("key") or "", duration=float(u["seconds"]),
                                      inference_steps=8, shift=3.0, seed=int(u["seed"]))
            config = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[int(u["seed"])], audio_format="wav")
            r = generate_music(dit, None, params=params, config=config, save_dir=None)
            if not r.success or not r.audios:
                raise RuntimeError(f"generation failed: {r.error or r.status_message}"[:400])
            a = r.audios[0]
            out = f"{u['unit']}.wav"
            sf.write(os.path.join(WORK, out), a["tensor"].numpy().T, a["sample_rate"])
            took = round(time.time() - t1, 1)
            res.update(status="ok", output=out, seconds=took, gpu_seconds=took, sample_rate=a["sample_rate"])
        except Exception as e:
            traceback.print_exc()
            took = round(time.time() - t1, 1)
            res.update(status="error", error=f"{type(e).__name__}: {e}"[:500], seconds=took, gpu_seconds=took)
        json.dump(res, open(os.path.join(WORK, f"{u['unit']}.result.json"), "w"))
        print(f"{u['unit']}: {res['status']} {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
