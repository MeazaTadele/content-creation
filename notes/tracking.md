# Heritage Short: tracking log

Working log for the "AI-Content Generation: The Heritage Short" assignment (10 Academy, B2W0).
Deadline for both submissions: **Thursday 26 November 2026, 23:59 EAT**.

This file holds everything the brief asks us to record. Entries feed the final files
(`DESIGN.md`, `EXPERIMENTS.md`, `FAILURES.md`, `COSTS.md`, `ETHICS.md`) and the report.
`runs.jsonl` is written by the pipeline code itself, not here.

## Ground rules for this log

- Meaza makes every decision. This log records options and trade-offs, not choices made for her.
- Record **all** decisions, challenges, experiments and practices. Meaza picks which ones to highlight
  (the hardest problem, the "one hard decision", the practice that helped and the one that didn't).
- Times are EAT (Addis Ababa).

## Status

| When | Status |
|---|---|
| Tue 24 Nov, ~19:15 | Research and planning only. Building has **not** started. |
| Tue 24 Nov, 19:16 | Assignment repo created: `MeazaTadele/content-creation` (public). |

Checkpoints from the brief:
- [ ] Phase 1: radio cut plays end to end; DESIGN.md records user test 1
- [ ] Phase 2: rough cut with a picture for every shot and the chosen score
- [ ] Phase 3: film public, pipeline runs end to end, walkthrough recorded, report written

---

## 1. Decisions

Every decision faced, open or made. Meaza chooses which one is "the hard decision" for the walkthrough.

| # | Decision | Options found so far | Status | Logged |
|---|---|---|---|---|
| 1 | Story, person, audience, language | Story, audience, language chosen | **Partly decided Tue 24 Nov.** Story: the Easter morning Meaza woke up and her mom was home, the first holiday she remembers celebrating with her mom (mom usually works on holidays). Audience: friends Yishak and Betty, and her brother (confirmed as tester Tue 24 Nov). Language: **Amharic** (decided Tue 24 Nov) | Tue 24 Nov |
| 2 | Visual style | realistic, illustrated, painted, animated-looking (illustrated hides inconsistency better) | Open | Tue 24 Nov |
| 3 | Code language | Python (FFmpeg, Kaggle, ACE-Step tooling are mostly Python) or Node/TypeScript | Open | Tue 24 Nov |
| 4 | Orchestrator | Makefile, Python CLI, other | Open | Tue 24 Nov |
| 5 | How Kaggle GPU stages fit "one command" | drive Kaggle via its API (push, wait, pull); run GPU stages manually and let the pipeline pick up cached outputs; make GPU stages optional with Ken Burns as default | Open | Tue 24 Nov |
| 6 | How to produce both aspect ratios | generate in one ratio and crop; generate both; pad with blur | Open | Tue 24 Nov |
| 7 | Generated media in git | Git LFS; compressed drafts; keep media out and document it (GitHub blocks files > 100 MB) | Open | Tue 24 Nov |
| 8 | Music structure | one continuous track; one cue per section | Open | Tue 24 Nov |
| 9 | Ken Burns fallback rule | number of attempts, quality bar | Open | Tue 24 Nov |
| 10 | What each stage's cache hash includes | prompt, seed, model, settings, input file hash (chain effect: keyframe change → clip regenerates) | Open | Tue 24 Nov |
| 11 | Ceiling work, if any | see research notes below | Open | Tue 24 Nov |
| 12 | Reuse anything from Instant Vlog Clip | A: fork the app; B: new pipeline, borrow ideas only; C: new pipeline now, app as a front end later | Open | Tue 24 Nov |
| 13 | Which coding agent writes the pipeline code | Claude Code (paid) or the free agents the brief suggests (Antigravity CLI, OpenCode). Relevant to the report's "agent writes the scripts" practice | **Decided Tue 24 Nov: Claude Code.** Report must state this openly | Tue 24 Nov |
| 14 | Model for each stage | Script: Gemini 3.8 Flash / Flash-Lite. Narration: Gemini TTS, OmniVoice Amharic, CosyVoice2 Amharic. Keyframes: FLUX.2 klein 4B, FLUX.1 schnell. Video: Wan 2.2 TI2V-5B, HunyuanVideo 1.5, LTX-2 family. Music: ACE-Step 1.5 | Open | Tue 24 Nov |
| 15 | Where the pipeline runs | This Claude Code cloud container (needs network access to providers + keys saved as environment secrets) or Meaza's own computer (needs Python/Node, FFmpeg installed) | Open | Tue 24 Nov |
| 16 | GPU platform for video and music | Kaggle (2x T4, ~30 GPU h/week, brief's main pick) or Colab (backup) | Open | Tue 24 Nov |
| 17 | Branch workflow in the repo | merge `tracking-log` into `main` and work on `main`; or work on branches and merge | Open | Tue 24 Nov |

## 2. Challenges and blockers

All of them, small or large. Feeds `FAILURES.md` and the report's "hardest problem".

| When | Challenge | What was tried | Outcome |
|---|---|---|---|
| Tue 24 Nov | Instant Vlog Clip repo could not be read from the claude.ai session (access denied) | Moved to Claude Code, attached the repo there | Resolved Tue 24 Nov |
| Tue 24 Nov | Audience is exactly 3 testers (Yishak, Betty, brother), the minimum per test, with no backup. Brother is also in the story, so not a neutral viewer | Brother confirmed as tester | Open: no backup tester yet |
| Tue 24 Nov | Real people in the story: Meaza, her mom, maybe her brother. Consent needed before generating their likeness or putting words about them on screen; includes the detail that mom works on holidays | — | Open |
| Tue 24 Nov | How to record consent: Meaza plans to text parents and brother. Graders don't open images in the repo, so screenshots alone wouldn't count; the record has to be written into ETHICS.md | — | Open |
| Tue 24 Nov | Mom is a small shop owner: whether the shop appears or is named in the film, and whether to cover it in mom's consent | — | Open |
| Tue 24 Nov | Private family detail (mom's work) would go to free AI services that may train on data, and into a public post | — | Open |
| Tue 24 Nov | Ownership of Instant Vlog Clip code (built for a client) vs. the assignment's public-repo requirement. The repo has no LICENSE file | — | Open: check the contract before copying any code |

## 3. Experiments (→ `EXPERIMENTS.md`, target ≥ 10)

Format: hypothesis → change → result, with evidence and the reason for the choice.

Expected by the brief: score candidates (~3 ACE-Step tracks) and why one was chosen; character consistency iterations; fixed-seed prompt comparisons; model comparisons.

_None yet._

## 4. Failures (→ `FAILURES.md`)

What broke, what was tried, what fixed it. Types the brief names: quota, memory, consistency, language.
Also: mispronounced names/places, and tools that changed or disappeared (and their replacements).

_None yet._

## 5. Costs and limits (→ `COSTS.md`)

- Free-tier limits actually found at the start, per provider: _not checked yet_
- Smoke test (one call per provider, latency): _not run yet_
- Measured latency per stage: —
- GPU minutes per stage: —
- Paid list-price equivalent: —
- Frontier comparison (if access is given): —

## 6. Audience and user tests (→ `DESIGN.md`)

- Audience: friends Yishak and Betty, and Meaza's brother (brother confirmed Tue 24 Nov)
- Language: Amharic (Tue 24 Nov)
- Where they watch: _not decided_
- Intent (what they should feel or understand): _not decided_
- Written before generating anything: date/commit to be recorded here

### User test 1: radio cut (≥ 3 people)
| Person (who they are) | What they said | What will change |
|---|---|---|

### User test 2: near-final cut (≥ 3 people)
| Person (who they are) | What they said | What changed |
|---|---|---|

### Storyboard changes traced to feedback
| Feedback | Storyboard change | Commit |
|---|---|---|

## 7. Consent, licences, labelling (→ `ETHICS.md`)

- Consent records (before generating anything of a real person; informed; covers the words they're shown saying): _none yet_
- Licences of every model and output:
  - Wan 2.2: Apache 2.0 (per brief)
  - ACE-Step 1.5: MIT, outputs usable commercially (per brief)
  - FLUX.2 klein 4B: Apache 2.0; 9B: non-commercial (per brief)
  - Gemini / Gemini TTS: _to check_
- Labelling plan: AI end card, platform AI disclosure, leave SynthID/C2PA intact
- Private family details kept out of free services that may train on data: _to record_
- Style described by qualities, not living artists' names

## 8. Suggested practices (→ report: one that beat instinct, one that didn't)

Record evidence for and against each as it happens.

| Practice | Evidence it helped | Evidence it didn't |
|---|---|---|
| JSON contract between stages | | |
| Reference sheet before keyframes | | |
| Logging every call | | |
| Agent writes the stage scripts while you design and review | | |
| Other suggested tips (480p drafts, 3 music candidates, cue list, ducking settings…) | | |

## 9. Report notes

- What we set out to make, and for whom: —
- What the audience said: see §6
- Hardest problem: Meaza picks from §2
- Ceiling work (what, what was measured, what it taught): —
- What to build next: —

## 10. Walkthrough and interview prep

- Hard decision to explain: Meaza picks from §1
- Shot or line to change live: —
- Log line proving only that shot regenerated: —
- Why the pipeline is shaped this way: —

## 11. Submission checklist

Assignment 1 (codebase and report)
- [ ] Public repo link
- [ ] One command tested from a fresh clone
- [ ] Report (PDF, Word or link)

Assignment 2 (film, walkthrough, post)
- [ ] Vertical 9:16 MP4 link (main submission)
- [ ] Horizontal 16:9 MP4 link
- [ ] Walkthrough link (≤ 5 min)
- [ ] Public post link or screenshot, AI label on; story, why it matters, one thing learned
- [ ] Every link opens without a login

---

## Research notes

### Instant Vlog Clip (`projectsdev77/instant-vlog-clip`, commit e054b42, 27 Oct 2026)

- Browser web app: React + Vite + TypeScript, Supabase backend, Gemini or Claude for text, ElevenLabs for voice.
  Video and audio are rendered **in the browser** (WebCodecs/mediabunny), not FFmpeg.
- Overlap with the brief: narration-first, picture cut to the voice, captions, music ducking,
  9:16 / 1:1 / 16:9 export, Ken Burns-style motions (zoomIn, zoomOut, panLeft, panRight), loudness normalisation.
- Mismatch with what the brief grades:

| Brief requires | Instant Vlog Clip |
|---|---|
| CLI batch pipeline, one command from fresh clone | Web app, clicked through |
| FFmpeg assembly | Browser rendering (FFmpeg only for test clips) |
| `storyboard.json` validated by JSON Schema | Project data in browser storage, zod types |
| `runs.jsonl`, one line per model call | Call durations only in the server function logs |
| Gemini TTS, FLUX, Wan, ACE-Step | Gemini/Claude + ElevenLabs; no image, video or music models |
| −14 LUFS, true peak < −1 dB | Normalises to −16 dB with a soft peak limit |

- Possibly reusable as logic or reference:
  - `src/domain/timing.ts`: speech length from words/sec (2.6), lead-in and tail per line
  - `src/render/mix.ts`: ducking curve (music to ~30% under voice), end fade
  - `src/render/styles.ts`, `compositor.ts`: caption styles, safe areas
  - `hasFreshAudio` + `textHash`: regenerate a narration line only when its text changed (same idea as cache-by-hash)
  - `src/ai/live.ts` (AI call wrapper), `scripts/ai-smoke.ts` (smoke test)

### Model alternatives (from research, Tue 24 Nov)

Video
- Wan 2.2 TI2V-5B (brief's pick): T4 builds limit to ~480p height / 720p width and 81–120 frames. Step-distilled variants (LightX2V, FastVideo) are faster.
- LTX-2 / 2.3 / 2.5 (Lightricks): synced video + audio up to 20 s, reportedly Apache 2.0; LTX-2.3 is 20.9B, so T4 viability is unconfirmed. WanGP (DeepBeepMeep) packages it for low-memory GPUs, with Kaggle builds.
- MiniMax H3: open weights, 33B, likely too heavy for free GPUs; less permissive licence.
- Wan 3.0: top of a Nov 2026 leaderboard; downloadable weights unconfirmed.

Amharic narration
- Gemini TTS (brief's pick): free, 130+ languages; Amharic quality unknown.
- OmniVoice Amharic (`Lab-et/omnivoice-amharic`): open, Apache 2.0, published MOS scores, dialect support; needs a GPU; voice cloning from 10 s triggers consent requirements.
- CosyVoice2 Amharic fine-tune (`gabar-tech/cosyvoice2-amharic`): stock checkpoint was unintelligible in Amharic; publishes before/after.

Speech recognition
- Ethio-ASR (arXiv 2603.23654): Amharic, Tigrinya, Oromo, Sidaama, Wolaytta. Paper is CC BY-NC-ND; check the model licence separately.

Pipeline logic ideas (measured rather than eyeballed)
- Pronunciation check: TTS → ASR → word error rate against the script
- Character consistency score: embedding similarity of each keyframe to the reference
- Shot length set from the measured narration length
- Automatic Ken Burns fallback after N failed attempts, logged
- Dry run: show what would regenerate and estimated GPU minutes
- Log measured LUFS after assembly

Public-value ideas
- Family tool (web app or Telegram bot) where a relative tells a story by voice and gets a film back
- Open evaluation of AI for Ethiopian languages (overlaps "more languages" and "a real benchmark")
- Package the pipeline as a CLI or MCP server
- Archive the real recording (with consent) alongside the film
