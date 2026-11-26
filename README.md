# Easter Morning (Heritage Short)

A 63-second Amharic short film about the Fasika (Ethiopian Easter) morning my mother was home: the
first holiday I remember with her, because she usually worked on holidays. The film is made by a
code pipeline from one file, `storyboard.json`: Amharic narration, English subtitles, AI keyframes
and video clips, an original score ducked under the voice, and an AI end card, exported as 9:16
and 16:9 MP4.

- **The film:** [9:16 (main)](https://drive.google.com/file/d/1twXHqIaS-cN-A5olPJ7U1uYYv16567BI/view?usp=sharing)
  and [16:9](https://drive.google.com/file/d/1uJQOa8DJli_I0rhymMmdJ6eRopjfRdmN/view?usp=sharing) (Google Drive);
  in the repository: `outputs/final/locked/easter_morning_9x16_final.mp4` and `…_16x9_final.mp4`
- **The public post:** [YouTube Shorts](https://youtube.com/shorts/CB9pj5Bhc80), with YouTube's AI
  label ("altered or synthetic content") switched on
- **What it's for and who it's for:** `DESIGN.md` (audience, intent, both user tests)
- **How it works:** `ARCHITECTURE.md`

## Run it

Requirements: Python 3.10+, FFmpeg on your PATH, and `make` (optional).

```bash
pip install -e .          # or: pip install jsonschema requests python-dotenv kaggle pytest
cp .env.example .env      # add your keys (never commit .env)
make film                 # validate, generate only what changed, export outputs/final/film_*.mp4
```

**From a fresh clone, `make film` needs no keys and no GPU:** every generated file and
`outputs/manifest.json` are in the repository, so every unit is a cache hit and only the FFmpeg
assembly runs (about 3 minutes for both films). Keys are needed only when you change something
that has to be generated again:

| Change in `storyboard.json` | Regenerates | Needs |
|---|---|---|
| a narration line | that line's voice clip, then the timing and assembly | Kaggle (OmniVoice), and the private voice sample, which is not in the repository (see ETHICS.md) |
| a shot's image prompt or seed | that keyframe, then its video clip if it has one | Kaggle (FLUX.2 klein), or Cloudflare with `providers.keyframes: "cloudflare-flux"` |
| a shot's motion prompt | that clip | Kaggle (Wan 2.2), about 20 min of GPU plus the queue |
| a music cue | that cue's candidates | Kaggle (ACE-Step 1.5) |
| subtitles, pacing, transitions, ducking | assembly only | nothing |

Keys go in `.env` (template: `.env.example`): `GEMINI_API_KEY` (Google AI Studio),
`CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`, `ELEVENLABS_API_KEY` (only for the voice
comparison), and `KAGGLE_USERNAME` with `KAGGLE_API_TOKEN` or a legacy `KAGGLE_KEY`. All are free
tiers; Kaggle needs a phone-verified account for GPUs.

Other commands:

| Command | What it does |
|---|---|
| `make plan` | dry run: what would be generated, without calling anything |
| `make radio` | narration and placeholder music on black: the radio cut for user test 1 |
| `make validate` | check `storyboard.json` against `schema/storyboard.schema.json` |
| `make smoke` | one call to each provider with a key, logged to `runs.jsonl` |
| `make check` | schema check, unit tests, and a scan for committed secrets |
| `make narration`, `make keyframes`, `make shots`, `make music` | one stage |
| `python -m pipeline keyframes --shot s08 --seeds 1,2,3` | candidates for one shot to choose from |

Without `make`: `python -m pipeline film` (and so on).

## What it costs

Measured in `COSTS.md`: about 4 hours of free Kaggle T4 GPU time and 124 free Cloudflare images
for the whole project, about $1.60 at paid list prices. The real limit was the Kaggle GPU queue:
jobs waited 15-25 minutes each on the last day.

## The repository

| File | What's in it |
|---|---|
| `storyboard.json` | the film: characters, voice, music cues, and the ten shots |
| `pipeline/` | the stages, providers, caching, logging and the Kaggle job runner |
| `kaggle/<stage>/run.py` | the scripts that run on Kaggle's GPU |
| `runs.jsonl` | one line per model call attempt, written by the pipeline |
| `outputs/` | every generated file, named `<unit>__<fingerprint>`, and `manifest.json` |
| `references/` | the locked character portraits and the keyframes chosen as they are |
| `DESIGN.md` | audience, intent, user tests 1 and 2, and the changes they caused |
| `ARCHITECTURE.md` | stages, the storyboard contract, caching, failure handling |
| `EXPERIMENTS.md` | 11 experiments: hypothesis, change, result |
| `FAILURES.md` | 19 real blockers and how they were solved or worked around |
| `COSTS.md` | measured time and GPU minutes per stage, and paid-price equivalents |
| `ETHICS.md` | consent records, the licence of every model, how the film is labelled as AI |
| `docs/DECISIONS.md` | every decision, the options, and what was chosen |

Claude Code wrote most of this code under my direction; every design decision is mine and is
recorded in `docs/DECISIONS.md`.
