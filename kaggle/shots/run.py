"""Kaggle script: Wan 2.2 TI2V-5B image-to-video for every unit in job.json.

Runs on GPU T4 x2: the units are split across the two GPUs, one worker process each. Every unit
writes <unit>.mp4 and <unit>.result.json to /kaggle/working as soon as it finishes, so a job that
times out still returns every finished clip.
"""
import glob
import json
import os
import subprocess
import sys
import time
import traceback

WORK = "/kaggle/working"
MODEL_ID = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"


def find_inputs():
    hits = glob.glob("/kaggle/input/**/job.json", recursive=True)
    if not hits:
        raise SystemExit("job.json not found under /kaggle/input")
    return os.path.dirname(hits[0])


def worker(gpu: int, unit_ids: list):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)
    import torch
    from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
    from diffusers.utils import export_to_video, load_image

    inp = find_inputs()
    job = json.load(open(os.path.join(inp, "job.json")))
    s = job["settings"]
    units = [u for u in job["units"] if u["unit"] in unit_ids]
    t_load = time.time()
    vae = AutoencoderKLWan.from_pretrained(MODEL_ID, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanImageToVideoPipeline.from_pretrained(MODEL_ID, vae=vae, torch_dtype=torch.float16)
    pipe.enable_model_cpu_offload()
    load_s = time.time() - t_load
    print(f"[gpu{gpu}] model loaded in {load_s:.0f} s", flush=True)
    for u in units:
        out_mp4 = os.path.join(WORK, f"{u['unit']}.mp4")
        res = {"unit": u["unit"], "fingerprint": u["fingerprint"], "gpu": gpu, "model": MODEL_ID}
        t0 = time.time()
        try:
            img = load_image(os.path.join(inp, u["keyframe"])).resize((s["width"], s["height"]))
            g = torch.Generator(device="cpu").manual_seed(u["seed"])
            frames = pipe(image=img, prompt=u["prompt"], negative_prompt=s.get("negative", ""),
                          height=s["height"], width=s["width"], num_frames=s["frames"],
                          num_inference_steps=s["steps"], guidance_scale=s["guidance"], generator=g).frames[0]
            export_to_video(frames, out_mp4, fps=s["fps"])
            res.update(status="ok", seconds=round(time.time() - t0, 1), gpu_seconds=round(time.time() - t0, 1),
                       output=f"{u['unit']}.mp4")
        except Exception as e:  # keep going: one bad shot must not lose the others
            res.update(status="error", seconds=round(time.time() - t0, 1), gpu_seconds=round(time.time() - t0, 1),
                       error=f"{type(e).__name__}: {e}"[:500])
            traceback.print_exc()
            if "out of memory" in str(e).lower():
                torch.cuda.empty_cache()
        json.dump(res, open(os.path.join(WORK, f"{u['unit']}.result.json"), "w"))
        print(f"[gpu{gpu}] {u['unit']}: {res['status']} in {res['seconds']} s", flush=True)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--worker":
        worker(int(sys.argv[2]), sys.argv[3].split(","))
        return
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.35", "transformers",
                    "accelerate", "ftfy", "imageio", "imageio-ffmpeg"], check=True)
    inp = find_inputs()
    job = json.load(open(os.path.join(inp, "job.json")))
    ids = [u["unit"] for u in job["units"]]
    import torch
    n_gpu = max(1, torch.cuda.device_count())
    print(f"{len(ids)} units on {n_gpu} GPU(s)", flush=True)
    groups = [ids[i::n_gpu] for i in range(n_gpu)]
    procs = [subprocess.Popen([sys.executable, __file__, "--worker", str(i), ",".join(g)])
             for i, g in enumerate(groups) if g]
    for p in procs:
        p.wait()


if __name__ == "__main__":
    main()
