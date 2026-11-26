"""Kaggle script: repaint only masked areas of a chosen keyframe (decision 37).

For each unit: the base image and a list of steps, each a mask and a prompt. Every step repaints
its mask with SDXL inpainting, then pastes only the masked pixels back onto the picture, so
everything outside the masks stays exactly as it was. Result files are written per unit.
"""
import glob
import json
import os
import subprocess
import sys
import time
import traceback

WORK = "/kaggle/working"
MODEL_ID = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"


def inputs_dir():
    return os.path.dirname(glob.glob("/kaggle/input/**/job.json", recursive=True)[0])


def main():
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.30", "transformers", "accelerate"],
                   check=True)
    import torch
    from diffusers import AutoPipelineForInpainting
    from PIL import Image, ImageFilter
    inp = inputs_dir()
    job = json.load(open(os.path.join(inp, "job.json")))
    t0 = time.time()
    pipe = AutoPipelineForInpainting.from_pretrained(MODEL_ID, torch_dtype=torch.float16, variant="fp16").to("cuda")
    print(f"{type(pipe).__name__} loaded in {time.time() - t0:.0f} s", flush=True)
    for u in job["units"]:
        res = {"unit": u["unit"], "fingerprint": u["fingerprint"], "model": MODEL_ID}
        t1 = time.time()
        try:
            img = Image.open(os.path.join(inp, u["base"])).convert("RGB")
            w, h = img.size
            for k, step in enumerate(u["steps"]):
                mask = Image.open(os.path.join(inp, step["mask"])).convert("L").resize((w, h))
                g = torch.Generator(device="cuda").manual_seed(u["seed"] + k)
                out = pipe(prompt=step["prompt"], negative_prompt=step.get("negative", ""), image=img, mask_image=mask,
                           height=h, width=w, strength=0.99, guidance_scale=7.0, num_inference_steps=30,
                           generator=g).images[0].resize((w, h))
                soft = mask.filter(ImageFilter.GaussianBlur(3))
                img = Image.composite(out, img, soft)  # only the masked area changes
            name = f"{u['unit']}.png"
            img.save(os.path.join(WORK, name))
            took = round(time.time() - t1, 1)
            res.update(status="ok", output=name, seconds=took, gpu_seconds=took)
        except Exception as e:
            traceback.print_exc()
            took = round(time.time() - t1, 1)
            res.update(status="error", error=f"{type(e).__name__}: {e}"[:500], seconds=took, gpu_seconds=took)
        json.dump(res, open(os.path.join(WORK, f"{u['unit']}.result.json"), "w"))
        print(f"{u['unit']}: {res['status']} {res['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
