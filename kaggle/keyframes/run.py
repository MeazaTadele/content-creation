"""Kaggle script: FLUX.2 klein 4B keyframes for every unit in job.json (decision 32).

Used when Cloudflare's daily allowance is exhausted. Same open model as on Cloudflare (Apache 2.0).
Runs on one T4 (two workers ran out of RAM, F16); each image and its result file are written as soon as it
is done, so a job that stops early keeps every finished image.
"""
import glob
import json
import os
import subprocess
import sys
import time
import traceback

WORK = "/kaggle/working"
MODEL_ID = "black-forest-labs/FLUX.2-klein-4B"


def inputs_dir():
    return os.path.dirname(glob.glob("/kaggle/input/**/job.json", recursive=True)[0])


def worker(gpu, unit_ids):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    import torch
    from diffusers import DiffusionPipeline
    from PIL import Image
    inp = inputs_dir()
    job = json.load(open(os.path.join(inp, "job.json")))
    units = [u for u in job["units"] if u["unit"] in unit_ids]
    t0 = time.time()
    pipe = DiffusionPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.float16)  # T4: no fast bf16
    pipe.enable_model_cpu_offload()
    print(f"[gpu{gpu}] {type(pipe).__name__} loaded in {time.time() - t0:.0f} s", flush=True)
    for u in units:
        res = {"unit": u["unit"], "fingerprint": u["fingerprint"], "model": MODEL_ID, "gpu": gpu}
        t1 = time.time()
        try:
            g = torch.Generator(device="cpu").manual_seed(u["seed"])
            kw = dict(prompt=u["prompt"], height=u["height"], width=u["width"], generator=g,
                      num_inference_steps=u.get("steps", 4))
            refs = [Image.open(os.path.join(inp, r)).convert("RGB") for r in u.get("refs", [])]
            if refs:
                kw["image"] = refs if len(refs) > 1 else refs[0]
            try:
                img = pipe(**kw).images[0]
            except TypeError:
                kw.pop("image", None)  # a pipeline version without reference images: text only
                res["note"] = "reference images not supported by this pipeline version; text only"
                img = pipe(**kw).images[0]
            out = f"{u['unit']}.png"
            img.save(os.path.join(WORK, out))
            res.update(status="ok", output=out, seconds=round(time.time() - t1, 1), gpu_seconds=round(time.time() - t1, 1))
        except Exception as e:
            traceback.print_exc()
            res.update(status="error", error=f"{type(e).__name__}: {e}"[:500], seconds=round(time.time() - t1, 1),
                       gpu_seconds=round(time.time() - t1, 1))
            if "out of memory" in str(e).lower():
                torch.cuda.empty_cache()
        json.dump(res, open(os.path.join(WORK, f"{u['unit']}.result.json"), "w"))
        print(f"[gpu{gpu}] {u['unit']}: {res['status']} {res['seconds']} s", flush=True)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--worker":
        worker(int(sys.argv[2]), sys.argv[3].split(","))
        return
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.36", "transformers",
                    "accelerate", "sentencepiece"], check=True)
    job = json.load(open(os.path.join(inputs_dir(), "job.json")))
    ids = [u["unit"] for u in job["units"]]
    import torch
    # One worker: two model copies parked in RAM by CPU offload ran the machine out of memory and the
    # first worker died silently (FAILURES.md F16). One GPU is fast enough (~30 s per image).
    n = 1
    groups = [ids[i::n] for i in range(n)]
    procs = [subprocess.Popen([sys.executable, __file__, "--worker", str(i), ",".join(g)]) for i, g in enumerate(groups) if g]
    for p in procs:
        p.wait()


if __name__ == "__main__":
    main()
