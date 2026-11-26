"""Kaggle script: open Amharic TTS models for the voice benchmark (decision 24, phase 2).

Every unit in job.json names a model and an Amharic text. Each model is set up once, then each
unit writes <unit>.wav and <unit>.result.json to /kaggle/working as soon as it is done, so one
model failing never loses the others.

  mms         facebook/mms-tts-amh       (CC BY-NC 4.0)  single voice; text romanised with uroman first
  omnivoice   Lab-et/omnivoice-amharic   (Apache 2.0)    no reference audio needed
  cosyvoice2  gabar-tech/cosyvoice2-amharic (CC BY-SA 4.0) needs a reference voice: a synthetic
              (AI-generated) clip is used, so no real person's voice is cloned
"""
import glob
import json
import os
import subprocess
import sys
import time
import traceback

WORK = "/kaggle/working"
DEVICE = "cuda"


def pip(*pkgs):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *pkgs], check=True)


def inputs_dir():
    hits = glob.glob("/kaggle/input/**/job.json", recursive=True)
    return os.path.dirname(hits[0])


def save(unit, model_id, t0, ok, wav=None, sr=None, err=None):
    import numpy as np
    import soundfile as sf
    res = {"unit": unit["unit"], "fingerprint": unit.get("fingerprint"), "model": model_id,
           "seconds": round(time.time() - t0, 2), "gpu_seconds": round(time.time() - t0, 2)}
    if ok:
        out = f"{unit['unit']}.wav"
        sf.write(os.path.join(WORK, out), np.asarray(wav, dtype="float32").squeeze(), sr)
        res.update(status="ok", output=out, sample_rate=sr)
    else:
        res.update(status="error", error=str(err)[:500])
    json.dump(res, open(os.path.join(WORK, f"{unit['unit']}.result.json"), "w"), ensure_ascii=False)
    print(unit["unit"], res["status"], res["seconds"], "s", flush=True)


def setup_failed(units, model_id, err):
    for u in units:
        save(u, model_id, time.time(), False, err=f"setup failed: {err}")


def run_mms(units):
    model_id = "facebook/mms-tts-amh"
    try:
        pip("transformers>=4.40", "uroman", "soundfile")
        import torch
        import uroman as ur
        from transformers import AutoTokenizer, VitsModel
        rom = ur.Uroman()
        model = VitsModel.from_pretrained(model_id).to(DEVICE)
        tok = AutoTokenizer.from_pretrained(model_id)
    except Exception as e:
        traceback.print_exc()
        return setup_failed(units, model_id, e)
    for u in units:
        t0 = time.time()
        try:
            text = rom.romanize_string(u["text"], lcode="amh")
            torch.manual_seed(u.get("seed", 0))
            with torch.no_grad():
                wav = model(**tok(text, return_tensors="pt").to(DEVICE)).waveform.cpu().numpy()
            save(u, model_id, t0, True, wav, model.config.sampling_rate)
        except Exception as e:
            traceback.print_exc()
            save(u, model_id, t0, False, err=e)


def run_omnivoice(units, inp):
    model_id = "Lab-et/omnivoice-amharic"
    try:
        pip("omnivoice", "soundfile")
        import torch
        from omnivoice import OmniVoice, OmniVoiceGenerationConfig
        model = None
        for rid in (model_id, "african-low-resource/omnivoice-amharic"):
            try:
                model = OmniVoice.from_pretrained(rid, device_map="cuda:0" if DEVICE == "cuda" else "cpu",
                                                  dtype=torch.float16 if DEVICE == "cuda" else torch.float32)
                model_id = rid
                break
            except Exception as e:  # the card's example names a second repo id
                print("could not load", rid, e, flush=True)
        if model is None:
            raise RuntimeError("no OmniVoice Amharic checkpoint could be loaded")
        cfg = OmniVoiceGenerationConfig(num_step=32, guidance_scale=2.0)
    except Exception as e:
        traceback.print_exc()
        return setup_failed(units, model_id, e)
    prompts = {}
    for u in units:
        t0 = time.time()
        try:
            torch.manual_seed(u.get("seed", 0))
            kw = {}
            if u.get("reference"):
                # follow one SYNTHETIC reference voice so every line has the same narrator
                if u["reference"] not in prompts:
                    prompts[u["reference"]] = model.create_voice_clone_prompt(
                        ref_audio=os.path.join(inp, u["reference"]), ref_text=u.get("reference_text"))
                kw["voice_clone_prompt"] = prompts[u["reference"]]
            if u.get("instruct"):
                kw["instruct"] = u["instruct"]  # voice design words, e.g. "female, young adult, high pitch"
            if u.get("speed"):
                kw["speed"] = float(u["speed"])  # OmniVoice paces lines from the sample voice; >1 speaks faster
            audio = model.generate(text=u["text"], language="Amharic", generation_config=cfg, **kw)
            save(u, model_id, t0, True, audio[0], 24000)
        except Exception as e:
            traceback.print_exc()
            save(u, model_id, t0, False, err=e)


def run_cosyvoice2(units, inp):
    model_id = "gabar-tech/cosyvoice2-amharic"
    try:
        os.chdir("/kaggle/working")
        if not os.path.isdir("CosyVoice"):
            subprocess.run(["git", "clone", "-q", "--recurse-submodules",
                            "https://github.com/FunAudioLLM/CosyVoice.git"], check=True)
            subprocess.run(["git", "-C", "CosyVoice", "checkout", "-q",
                            "074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc"], check=True)
        pip("-r", "CosyVoice/requirements.txt", "resemble-perth", "huggingface_hub", "soundfile")
        sys.path[:0] = ["CosyVoice", "CosyVoice/third_party/Matcha-TTS"]
        import importlib.util
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(model_id, "amharic_tts.py")
        spec = importlib.util.spec_from_file_location("amharic_tts", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tts = mod.load_amharic_tts(cosyvoice_repo="CosyVoice")
    except Exception as e:
        traceback.print_exc()
        return setup_failed(units, model_id, e)
    for u in units:
        t0 = time.time()
        try:
            wav = tts.generate(u["text"], audio_prompt_path=os.path.join(inp, u["reference"]),
                               prompt_text=u.get("reference_text"))
            save(u, model_id, t0, True, wav.cpu().numpy() if hasattr(wav, "cpu") else wav, tts.sr)
        except Exception as e:
            traceback.print_exc()
            save(u, model_id, t0, False, err=e)
    # free the folder so it isn't returned as job output
    subprocess.run(["rm", "-rf", "/kaggle/working/CosyVoice"])


def main():
    global DEVICE
    inp = inputs_dir()
    job = json.load(open(os.path.join(inp, "job.json")))
    DEVICE = job.get("settings", {}).get("device", "cuda")
    print("device:", DEVICE, flush=True)
    by_model = {}
    for u in job["units"]:
        by_model.setdefault(u["model"], []).append(u)
    order = [m for m in ("mms", "omnivoice", "cosyvoice2") if m in by_model]
    for m in order:
        print("=== model", m, len(by_model[m]), "units", flush=True)
        if m == "mms":
            run_mms(by_model[m])
        elif m == "omnivoice":
            run_omnivoice(by_model[m], inp)
        else:
            run_cosyvoice2(by_model[m], inp)


if __name__ == "__main__":
    main()
