# Decisions

Every design decision in this project, the options that were considered, and what was chosen.
All decisions are Meaza's. The coding agent (Claude Code) researched options and, when asked,
made suggestions; where a suggestion was adopted, the table says so. Newest decisions are added
at the bottom of each section.

## Story and audience

| # | Decision | Options considered | Chosen | Date |
|---|---|---|---|---|
| 1 | Story, audience, language | a person's moment, a ritual, a saying, a place, a journey, an object | The Fasika morning my mother was home; audience Betty, Yishak and my brother Henok; Amharic narration | Tue 24 Nov |
| 19 | Intent | joy; gratitude; bittersweet; recognition of one's own family | Feel happy, understand that being there matters as much as providing, and think about their own families' holidays (see DESIGN.md) | Wed 25 Nov |
| 32 | Where keyframes are made after Cloudflare's daily allowance stayed exhausted | wait for Cloudflare (likely about 21:00, close to the deadline); the same FLUX.2 klein 4B model on Kaggle's GPU | Kaggle's GPU, one batch job (Thu 26 Nov, 06:40 EAT) | Thu 26 Nov |
| 37 | s09 | keep trying the pouring edit, or reuse | s09 is exactly like s10: the v4 s09 picture (the family laughing and sipping) is used for both. s09 is the video of it; s10 the still. No pouring shot | Thu 26 Nov |
| 36 | s07 and the edit model | keep trying FLUX, Gemini image editing, an open editing model, a hand edit | Tried Gemini (refused: not on the free tier, F18). Then: keep s07 as v4 (locked). s08: remove the girl sitting with my father and brother, and put me (standing at the door) in my pyjamas | Thu 26 Nov |
| 35 | Keyframe fixes after the v4 sheet | regenerate, or edit the v4 images | I love v4: keep most of it and change only what I listed. s07: only make my father and brother bigger next to my mother. s08: only remove the girl sitting next to my father, put me in pyjamas at the door, and make my father and brother bigger. s09 v4 is perfect: it moves to s10 unchanged. New s09: the same set-up, but my mother pouring coffee instead of drinking. Done as edits of the v4 images (image.edit_from) and a locked copy (image.locked); s09's video movement changed back to the pouring | Thu 26 Nov |
| 34 | Keyframe fixes after the v3 sheet | redo the flagged shots one by one, or tie the later shots to one room | Keep s05 as it is. s06: close-up of the jebena, cups and the coffee my mother is making, same set-up. s07: the s05 room, wider, my father and brother sitting with my mother. s08: the same set-up, me at the door looking at them, my mother looking and dressed as in the other shots. s09 (close) and s10 (wide): the s05 room, the family laughing and sipping coffee. s04: the whole girl with no extra leg. 9:16 first, 16:9 after the fixes. Done by giving the s05 image to the model as the room (image.scene_from) | Thu 26 Nov |
| 33 | Final narration | radio cuts v1-v9 | Radio cut v9: OmniVoice following my own voice sample (v3's takes), tempo 0.9, my longer lines 1-2, pauses 0.25 s / 0.5 s, 62.7 s. Locked | Thu 26 Nov |
| 31 | Final character references | nine rounds of candidates (reference sheet stage), edits toward the chosen outfits and Ethiopian features | Girl 3 (round 4); mother 1, father 1, brother 0 (round 7: the family outfits, before the last face edit, which I liked less). Locked in `references/*_final.png` | Wed 25 Nov |
| 2 | Visual style | painted/illustrated; photorealistic; soft animated | Painted/illustrated, warm and soft like a memory (suggested by the agent, adopted) | Wed 25 Nov |
| 8 | Music structure | one track; two cues; a looping bed | Two cues: a quiet "before" and a warm "Easter morning", crossfaded at the turn (suggested, adopted) | Wed 25 Nov |
| 6 | Both aspect ratios | crop one composition both ways; 9:16 video with a blurred-background 16:9; generate everything twice | 9:16 video; 16:9 shows it over a blurred copy; Ken Burns stills made natively in both ratios (suggested, adopted). Reason: on a T4, video is about 480p, so cropping 9:16 out of 16:9 would leave about 270×480 pixels | Wed 25 Nov |

## Tools and models

| # | Decision | Options considered | Chosen | Date |
|---|---|---|---|---|
| 6 | Commit author | Claude as author; me as author with Claude as co-author | Me as author, Claude credited as co-author in every commit message (from Wed 25 Nov; earlier commits stay as they were) | Wed 25 Nov |
| 13 | Coding agent | Claude Code; Antigravity CLI; OpenCode; a mix | Claude Code writes most of the code under my direction | Tue 24 Nov |
| 3 | Code language | Python; Node/TypeScript | Python | Wed 25 Nov |
| 16 | GPU platform | Kaggle; Colab | Kaggle | Wed 25 Nov |
| 14 | Models | brief's defaults or alternatives (LTX-2, HunyuanVideo, other TTS) | Brief's defaults for script (Gemini Flash), keyframes (FLUX on Cloudflare), video (Wan 2.2 TI2V-5B), music (ACE-Step 1.5); Wan tested on Kaggle first | Wed 25 Nov |
| 14b | Amharic voices to compare | Gemini TTS, ElevenLabs, Azure, OmniVoice Amharic, MMS-TTS, CosyVoice2 Amharic, Chatterbox Amharic | Gemini TTS, ElevenLabs, OmniVoice Amharic, MMS-TTS, CosyVoice2 Amharic | Wed 25 Nov |
| 24 | Voice benchmark order | all five now; phased; fewer | Gemini, ElevenLabs and MMS first; OmniVoice and CosyVoice2 after the film works (suggested, adopted) | Wed 25 Nov |
| 18 | How voices are judged | my ear; blind listening by testers; speech-recognition check | All three, plus latency and cost | Tue 24 Nov |
| 25 | How the three checks are weighed | equal; blind listening decides; my ear decides | Blind listening decides; speech recognition and my ear support it (suggested, adopted). Speech recognition for Amharic is itself unreliable | Wed 25 Nov |
| 25b | The film's voice (update to 25) | blind test; my own voice as the sample; a synthetic female sample; my sample plus voice-design words | My own voice as OmniVoice's sample (radio cut v3), slowed to tempo 0.9. It had the most natural Amharic pronunciation and delivery; the alternatives either lost that or still sounded like me. Consent recorded in ETHICS.md | Wed 25 Nov |
| 12 | Reuse an earlier project of mine | fork it; borrow ideas only; use it as a front end later | Borrow ideas only; no code reused | Wed 25 Nov |

## Pipeline design

| # | Decision | Options considered | Chosen | Date |
|---|---|---|---|---|
| 15 | Where it runs | cloud container; my computer; both | Built and tested in a cloud container, then cloned and run on my computer | Wed 25 Nov |
| 4 | The one command | Makefile; Python CLI | `make film` | Wed 25 Nov |
| 5 | How Kaggle fits into one command | automatic via the Kaggle API; manual runs picked up from cache; GPU stages optional | Automatic via the Kaggle API, with a Ken Burns fallback for any missing clip | Wed 25 Nov |
| 7 | Generated media in git | commit small outputs; Git LFS; no media | Commit media while every file is under GitHub's 100 MB limit | Wed 25 Nov |
| 10 | What a cache fingerprint includes | (a) the whole shot; (b) only the inputs each stage uses + model, settings, seed, input-file hashes, a manual stage version; (c) (b) + a hash of the stage's code | (b): only the affected parts rerun after an edit. Known weak point: the stage version must be raised by hand (mitigated by a warning, decision 23) | Wed 25 Nov |
| 20 | Stage design | the brief's six stages, or improved | Seven changes: narration first, with shot lengths from measured narration; swappable providers; a voice-check stage; a reference-sheet stage; a `plan` dry run; an automatic Ken Burns fallback; measured values kept in a generated manifest, never written into the storyboard | Wed 25 Nov |
| 9 | When a shot falls back to Ken Burns | number of attempts; manual override | Two automatic attempts, then Ken Burns; a `kenburns` flag in the storyboard forces it (suggested, adopted) | Wed 25 Nov |
| 22 | Build order | minimal end-to-end first; everything at once | Minimal end-to-end first, after an external architecture review rated scope vs deadline 5/10 (suggested, adopted) | Wed 25 Nov |
| 23 | Fixes from the architecture review | adopt, adapt or skip each | Adopted: silence trimming, atomic writes and per-unit recovery, separate retries for API calls and Kaggle jobs, raw and normalised error rates, crossfade timing in subtitles, leak checks, two documented reproduction modes, failed attempts marked in the log, a warning when stage code changes without a version bump. Skipped: file locks (single user) | Wed 25 Nov |
| — | Implementation details | agent's proposals | Approved: package named `pipeline/`; API retries up to 4 attempts with backoff; Kaggle jobs polled with their own timeout; outputs named `<shot>__<fingerprint>`; music length rounded up to the next 15 s; cache hits not written to `runs.jsonl` | Wed 25 Nov |
| 29 | Filling 6–8 s shots with 2 s clips | (a) play the clip, then drift over its last frame; (b) slow motion; (c) chain three clips per shot; (d) video only on key shots | (a) + (d): real video on shots 5 (mother), 6 (incense smoke) and 9 (pouring coffee), each followed by a slow drift; Ken Burns moves on stills for the other seven. Less GPU time and fewer Kaggle queue waits (FAILURES.md F9) | Wed 25 Nov |
| 28 | When a model is retired or a quota runs out | (a) stop clearly, rely on the cache, Ken Burns for video; (b) a backup image model; (c) quota use shown by `make plan` | All three. The narration voice is never switched automatically mid-film, because the narrator would change between shots | Wed 25 Nov |
| 11 | Ceiling work | voice benchmark; more languages; LoRA; a tool for others | The Amharic voice benchmark for now; revisit after the film works | Wed 25 Nov |
