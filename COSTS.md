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

## Per stage

_To be filled from the first runs._
