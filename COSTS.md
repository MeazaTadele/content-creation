# Costs

Measured from `runs.jsonl`: latency and GPU minutes per stage, and what the same work would cost
at paid list prices.

## Free-tier limits found (measured, Wed 25 Nov)

| Provider | Limit found | How it showed up |
|---|---|---|
| Cloudflare Workers AI (FLUX.2 klein 4B) | 10,000 neurons a day, reset 00:00 UTC (03:00 EAT) | Ran out after 124 images: about 80 neurons per image. List price $0.011 per 1,000 neurons, so about $0.0009 per image, or about $0.11 for the day's images |
| Gemini 3.8 Flash TTS | A per-minute limit, hit after 6 lines in a row | HTTP 429; one request a minute later worked (FAILURES.md F8) |
| Kaggle | About 30 GPU hours a week; GPU jobs can wait in a queue | A narration job queued 45 minutes without starting (F9); CPU jobs start at once |
| ElevenLabs (free plan) | Monthly character allowance | Not reached |

## Per stage (measured, Wed 25 - Thu 26 Nov)

Kaggle GPU time is the session time Kaggle counts against the weekly allowance: from the moment
the job leaves the queue to the moment it completes, so it includes installing packages and
loading the model. It comes from the job logs (time to complete minus time queued, measured with
a 60 s poll, so each figure can be up to a minute off). "Model time" is the time the model itself
took per unit, from `gpu_seconds` in `runs.jsonl`.

| Stage | Model and where | Units made | GPU session time | Model time per unit | Queue wait |
|---|---|---|---|---|---|
| Narration, open voices | OmniVoice and MMS, Kaggle T4 | 7 GPU jobs, 56 clips | about 13 min | 3-6 s a line | 0-45 min (F9) |
| Narration, open voices on CPU | OmniVoice and MMS, Kaggle CPU | 4 jobs, 49 clips | not GPU (about 2.7 h of CPU) | 2-6 min a line | none |
| Narration, hosted | Gemini 3.8 Flash TTS, ElevenLabs eleven_v3 | 10 Gemini and 29 ElevenLabs lines | none | median 5.0 s (Gemini), 3.6 s (ElevenLabs) a line, API latency | none |
| Reference sheet | FLUX.2 klein 4B, Cloudflare | 82 portraits (with edits) | none | median 10.5 s each, API latency | none |
| Keyframes, Cloudflare | FLUX.2 klein 4B, Cloudflare | 40 (then the daily allowance ran out, F13) | none | median 8.5 s each, API latency | none |
| Keyframes, Kaggle | FLUX.2 klein 4B, Kaggle T4 | 6 jobs, 48 images | 52 min | about 32 s an image | 0-14 min |
| Keyframe repaint | SDXL inpainting, Kaggle T4 | 1 job, 3 images (2 areas each) | 5 min | about 60 s an image | 19 min |
| Video tests | Wan 2.2 TI2V-5B, Kaggle T4 | 2 jobs (one out of memory, F5) | 104 min | 781 s a clip | none |
| Video, film | Wan 2.2 TI2V-5B, Kaggle T4 | 3 jobs, 4 clips (1 lost to F19) | 77 min | 766-781 s a clip, plus 390 s to load the model | 16-24 min |
| Music | ACE-Step 1.5 turbo, Kaggle T4 | 1 job, 6 candidates | _running_ | _running_ | 15 min |
| Assembly | FFmpeg, this machine | both films, 27 parts | none | about 3 min for both films from scratch (file times) | none |

**Total Kaggle GPU time so far: about 4 hours 10 minutes** of the roughly 30 hours a week. Waiting
in the GPU queue added about 2.5 hours of waiting on Thu 26 Nov alone, more than the GPU time that
day: the queue, not the GPU allowance, was the real limit (as the brief predicted).

## What it would cost at paid list prices

| Work | Paid equivalent | Price used | Cost |
|---|---|---|---|
| 4 h 10 min of T4 GPU time | renting one NVIDIA T4 on Google Cloud | $0.35 per GPU-hour, on-demand list price ([Google Cloud GPU pricing](https://cloud.google.com/products/compute/gpus-pricing), checked Thu 26 Nov), without the machine it is attached to | about $1.46 |
| 124 images on Cloudflare (82 portraits, 42 keyframes and tests) | Workers AI beyond the free 10,000 neurons a day | $0.011 per 1,000 neurons, about 80 neurons an image (measured, F13) | about $0.11 |
| Gemini and ElevenLabs narration | within the free tiers | not charged | $0 |
| **Total** | | | **about $1.60** |

Kaggle sessions come with two T4s; renting both for the same time would double the GPU line. The
jobs used one GPU in the end, because two copies of a model ran out of the machine's memory (F16,
F19). The real cost of this film was time, not money: about 4 hours of GPU work, and 2-3 hours of
queue on the last day.

## Frontier comparison

Not possible on this account: Google's image models (Gemini 2.5 and 3.1 Flash Image) are not on the
free tier (F18), and no frontier video or music lane was offered. The voice comparison (Gemini and
ElevenLabs against the open OmniVoice and MMS) is in EXPERIMENTS.md E1 and E2.
