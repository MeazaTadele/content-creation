# Architecture

One file, `storyboard.json`, describes the whole film. The pipeline reads it, checks it against
a schema, and runs seven stages. Each stage turns parts of the storyboard into files, records
what it made in `outputs/manifest.json`, and logs every model call in `runs.jsonl`. Change one
shot in the storyboard, run `make film` again, and only the parts that depend on that shot are
made again.

```
        Story, narration and shots written by hand (no AI script stage)
                                │
                                ▼
                         storyboard.json  (the contract, checked by schema/storyboard.schema.json)
                                │
   ┌──────────────┬─────────────┼──────────────┬──────────────┐
   ▼              ▼             ▼              ▼              ▼
1 narration   3 reference   4 keyframes    5 video clips   6 music
  (voice per    sheet         (one still     (Wan 2.2 on     (ACE-Step 1.5
  line)         (characters)  per shot)      Kaggle)         on Kaggle)
   │              │             │              │              │
   ▼              └────────────►│ refs         │              │
2 timing ◄──────────────────────┼──────────────┼──────────────┘
  (shot lengths from            │              │
  the voice)                    ▼              ▼
   └──────────────────────► 7 assembly (FFmpeg only): picture, voice, music, subtitles,
                              loudness, end card → outputs/final/film_9x16.mp4, film_16x9.mp4
```

## The contract: `storyboard.json`

- **What it holds:** the title, the characters (description, consent link, locked reference image),
  the voice (which provider speaks, its reference sample, tempo), pacing, the music cues, the
  providers per stage, and the ten shots. Each shot has its narration line, image prompt and seed,
  the characters in it, and its motion (a video prompt, or a Ken Burns move).
- **Checked before every run** (`pipeline/contract.py`): first the JSON Schema, then checks the
  schema can't express (every character a shot names exists, music cues start at real shots and
  in order, a shot can only borrow the room of an earlier shot, and every locked or edited picture
  file exists). An invalid storyboard
  stops the run before anything is called.
- **Decisions live in it, not in code.** A picture chosen to keep is `image.locked`; an edit
  is `image.edit_from` plus a description or repaint areas. Anyone who clones the repository and
  runs `make film` gets the same film.

## The stages

| # | Stage | Reads | Makes | Where it runs |
|---|---|---|---|---|
| 1 | narration (`stages/narration.py`) | each shot's line, `voice` | one WAV per line per voice | Gemini TTS and ElevenLabs (API); OmniVoice, MMS (Kaggle batch) |
| 2 | timing (`stages/timing.py`) | narration lengths, `pacing`, `voice.tempo` | `outputs/timeline.json`: start and length of every shot | local |
| 3 | reference sheet (`stages/refsheet.py`) | characters | candidate portraits; skipped when a reference is locked | Cloudflare FLUX.2 klein |
| 4 | keyframes (`stages/keyframes.py`) | image prompt, style, seed, references | one 9:16 still per shot | FLUX.2 klein on Kaggle (or Cloudflare); SDXL inpainting on Kaggle for repaints |
| 5 | video clips (`stages/shots.py`) | keyframe, motion prompt, seed | a 2 s clip (49 frames, 480×832) for shots s05, s06, s09 | Wan 2.2 TI2V-5B on Kaggle |
| 6 | music (`stages/music.py`) | cues, timeline | 3 candidates per cue; the chosen one is `use` | ACE-Step 1.5 on Kaggle |
| 7 | assembly (`stages/assemble.py`) | everything above | both films | FFmpeg, local, no AI |

`make film` runs them in that order (`pipeline/__main__.py`). Each also runs alone
(`make narration`, `make keyframes`, …), and `make plan` shows what would be made without
calling anything.

### Keyframes in more detail

The keyframe stage grew four ways to make a still, because one shot needed different help than
another (decisions 31-37, FAILURES F11-F18):

- **Generate** from the prompt, with the locked character portraits as reference images.
- **`scene_from`**: also give the model an earlier shot's picture as the room, so s06-s10 share
  the room of s05 (decision 34).
- **`kaggle-inpaint`**: repaint only marked areas (polygons in the storyboard) with SDXL
  inpainting; every pixel outside them is pasted back unchanged (decision 36).
- **`locked`**: use a chosen picture as it is, never regenerated (s07, s09, s10).

`python -m pipeline keyframes --shot s08 --seeds 1008,2108,3208` makes candidates. Each candidate is stored
under the fingerprint it would have as the main picture, so picking one means writing its seed in
the storyboard and nothing is generated again.

## Caching

- **A fingerprint per unit** (`pipeline/fingerprint.py`): a hash of exactly the inputs that unit
  uses (prompt, seed, size, model, provider, and the bytes of any input file such as a reference
  image or the keyframe a clip starts from), plus the stage's `STAGE_VERSION`. Decision 10: only
  the inputs each stage uses, so editing one narration line does not touch any picture.
- **A cache hit** means the manifest has the same fingerprint for that unit and the output file
  still exists. Hits are skipped and not logged.
- **Chains follow automatically:** a new keyframe has new bytes, so its video clip's fingerprint
  changes and the clip is made again; every other shot stays cached.
- **Outputs are named `<unit>__<fingerprint>`**, so an old version is never overwritten, and
  switching back to an earlier prompt finds its old output again.
- **Stage code changes:** if a stage's file changed but its `STAGE_VERSION` did not, the run prints
  a warning, so a change that affects outputs is not silently mixed with old outputs.
- **Music lengths are rounded up to the next 15 s,** so a small timing change does not regenerate
  music; assembly trims and fades.

## Failure handling

- **Every model call goes through `calls.call_model`**, which retries up to 4 attempts with
  backoff on network errors, HTTP 5xx and 429. A 429 with no `Retry-After` waits 65 s, because the
  free per-minute limits need about a minute (F8).
- **Daily allowances stop at once:** a 429 that names a daily quota, or a free-tier limit of zero,
  raises `QuotaExhausted` and the stage stops instead of retrying (F13, F18).
- **One bad unit doesn't stop the others:** narration voices run one by one, and keyframes keep
  going past a unit blocked by a safety filter (F10).
- **Kaggle batch jobs** (`pipeline/kaggle.py`): inputs are uploaded as a private dataset, the job
  script is pushed as a GPU kernel, the status is polled, and the outputs are downloaded. Each unit
  writes its own result file, so a job that stops part-way keeps every finished unit, and a unit
  with no result is reported as failed (F16).
- **Video has a fallback:** a shot gets at most 2 automatic tries on Wan; after that, or when
  `motion.kenburns` is set, assembly uses a slow Ken Burns move over the keyframe (decision 9).
- **Writes are atomic** (`pipeline/atomic.py`): every file goes to a temporary name first, and the
  manifest re-reads and merges before each write, so two runs or a crash cannot corrupt it.

## Logging: `runs.jsonl`

One line per call attempt, written by the pipeline, never by hand: time, run id, stage, unit,
provider, model, parameters, seed, attempt number, status, whether it was the final attempt,
latency, fingerprint, output path, and the error with any key redacted (`calls.redact`). Kaggle
jobs add one line per unit with its GPU seconds and the job id. Cache hits are not logged.

## Assembly

FFmpeg only, so the same inputs always give the same film. Each shot becomes a segment: its
Wan clip, which plays and then drifts slowly over its last frame (decision 29), or a Ken Burns
move over the keyframe. Segments are joined with the storyboard's transitions, then the end card.
The soundtrack: narration placed on the timeline (with `voice.tempo`), the two music cues
crossfaded, music ducked under the voice with `sidechaincompress`, both stems normalised in two
passes (narration -18 LUFS, music -26 LUFS), and the mix to -14 LUFS / -1 dBTP. Subtitles are
ASS files inside a safe area. The 16:9 film shows the 9:16 picture over a blurred, darkened copy
of itself (decision 6).

## Adding or swapping a model

Providers sit behind small classes in `pipeline/providers/` (an image provider has `generate`, a
voice provider has `synthesize`). The storyboard names the provider per stage (`providers`) or per
shot (`image.provider`), so a different model is a new class plus one word in the storyboard.
Kaggle models are a script in `kaggle/<stage>/run.py` that reads `job.json` and writes one result
file per unit.

## Secrets

Keys live only in `.env` (git-ignored) or as network secrets in the cloud environment, never in
the repository. `make check` scans tracked files for anything that looks like a key.
