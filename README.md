# Heritage Short

A pipeline that turns one file, `storyboard.json`, into a 60–90 second short film: Amharic
narration, English subtitles, AI-generated keyframes and clips, an original score ducked under
the voice, and an AI end card, exported as 9:16 and 16:9 MP4.

> Status: in progress. The pipeline runs end to end with placeholder story text and stand-in
> providers; real models are being connected next.

## Run it

Requirements: Python 3.10+, FFmpeg on your PATH, and `make` (optional).

```bash
pip install -e .          # or: pip install jsonschema requests python-dotenv kaggle pytest
cp .env.example .env      # add your keys (never commit .env)
make film                 # validate, generate what changed, export outputs/final/film_*.mp4
```

Other commands:

| Command | What it does |
|---|---|
| `make plan` | dry run: what would be generated, without calling anything |
| `make radio` | narration + placeholder music on black: the radio cut for user test 1 |
| `make validate` | check `storyboard.json` against `schema/storyboard.schema.json` |
| `make smoke` | one call to each provider with a key, logged to `runs.jsonl` |
| `make check` | schema check, unit tests, scan for committed secrets |
| `make narration`, `make keyframes`, … | one stage |

Without `make`: `python -m pipeline film` (and so on).

## How it works

Every stage reads `storyboard.json`; nothing writes to it. Each unit of work (one shot's
narration in one voice, one keyframe in one aspect ratio, one music candidate…) is cached under a
fingerprint of exactly the inputs it uses, so editing one shot regenerates only that shot.
Every real model call is logged to `runs.jsonl`. See `ARCHITECTURE.md` and `docs/DECISIONS.md`.

Claude Code wrote most of this code under my direction; every design decision is mine and is
recorded in `docs/DECISIONS.md`.
