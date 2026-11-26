# Failures

What broke, what was tried, and what fixed it or how it was worked around. Includes quota,
memory, consistency and language problems, and tools that changed or disappeared. Newest first.

## F22. `pip install -e .` failed on a fresh Windows machine (Thu 26 Nov)

- **What broke:** setting up the repository on Meaza's own computer for the walkthrough, the install
  stopped with "Multiple top-level packages discovered in a flat-layout: kaggle, schema, outputs,
  pipeline, references". `pyproject.toml` never said which folder is the package, and the cloud
  container had never run the install from a clean clone.
- **Fix:** `pyproject.toml` now names the build backend and includes only `pipeline*`; tested with
  a clean virtual environment. The four dependencies can also be installed directly, as the README says.
- **Lesson:** "one command from a fresh clone" has to be tested on a fresh machine, not only where the
  code was written.

## F21. The 16:9 film showed old pictures (Thu 26 Nov)

- **What broke:** Meaza noticed the 16:9 film's pictures were completely different from the 9:16
  film's. The seven Ken Burns shots in 16:9 used the separate 16:9 keyframes from the first Kaggle
  image job, made before all her fixes (decisions 34-39); only the three video clips used the 9:16
  picture over a blurred copy, as decision 6 says.
- **Fix:** every 16:9 segment now uses the shot's 9:16 keyframe over a blurred, darkened copy of
  itself. The 9:16 film was not touched (all its parts stayed cached); only the 16:9 was rebuilt.
- **Lesson:** a decision has to hold on every path through the code, not only the one I tested.
  The 16:9 keyframes are no longer used by the film.

## F20. A listening copy overwrote two music candidates (Thu 26 Nov)

- **What broke:** right after the ACE-Step job, I (the agent) converted the six candidates to MP3
  for Meaza to listen to. The file pattern for candidate A matched several files, and FFmpeg took the
  extra names as outputs, so it wrote the placeholder music over the real candidate A of both cues
  (and over four placeholder files). Caught by measuring them before sending: A was 75 s and 30 s
  long at -31 LUFS, like the placeholders, instead of 45 s like B and C.
- **Fix:** the real candidates were still in the Kaggle download folder and the placeholders were in
  git, so everything was restored; the MP3s are now made from the exact paths in the manifest.
- **Lesson:** never pass a glob to FFmpeg as an input; check the output (length, loudness) before
  handing anything over.

## F19. The same memory problem in the video job (Thu 26 Nov)

- **What broke:** the Wan 2.2 job split three clips across the two T4s. GPU 0 made s05 and s09
  (781 s and 766 s each, after 390 s loading the model); GPU 1, holding s06, left no result and no
  error, the same silent stop as F16.
- **Why:** each worker parks its own copy of the model in RAM (sequential CPU offload, F5); two
  copies are more than the machine's RAM.
- **Fix:** the video job also runs one worker. Only s06 was sent again; s05 and s09 stayed cached.
- **Lesson:** F16 should have been fixed in every Kaggle job at once, not only in the one where it
  showed up. Two GPUs only help when each model fits in RAM twice.

## F18. Gemini's image models are not on the free tier (Thu 26 Nov)

- **What broke:** after F17, Meaza chose to try Gemini image editing for s07. Both image models the
  key can see, gemini-2.5-flash-image and gemini-3.1-flash-image, answered HTTP 429 at once. The
  quota names in the error were the free-tier ones (requests per day, requests per minute, input
  tokens per minute), with no allowance left to use: the free tier gives these models nothing. This
  matches the brief: the frontier image models "moved behind paid billing".
- **What it cost:** nothing. The key has no billing, so the refused calls cannot be charged. One
  pipeline call is in runs.jsonl as QuotaExhausted, with no retries: a 429 that says "limit: 0" or
  a daily quota now stops at once instead of waiting 65 s four times.
- **What stays:** the provider (image.provider "gemini-image", pipeline/providers/gemini_image.py)
  stays in the code as an option for a key with billing. s07 went back to the open-model version.

## F17. The open image model would not make a targeted edit (Thu 26 Nov)

- **What broke:** Meaza wanted only the sizes of the father and brother changed in s07 (and two small
  changes each in s08 and s09). FLUX.2 klein, given the chosen picture as the first reference and
  told to keep everything else, returned nearly the same picture: 6-15% of pixels changed, and none
  of the requested changes. Four more seeds with a "describe the result" prompt made the men only a
  little bigger. Rebuilding s07 as a wider shot from the s05 room made them bigger, but 3 of 4
  candidates had the wrong people (two fathers, an extra man, a bald brother).
- **Why:** the fast distilled model (4 steps) follows its reference image very closely: good for
  keeping a room the same (decision 34), poor for changing one thing inside a picture.
- **Lesson:** use reference images for consistency, not for edits; an edit needs a model built for
  editing, or repainting only a masked area.

## F16. Half the Kaggle keyframes came back missing: one GPU worker died without an error (Thu 26 Nov)

- **What broke:** the first FLUX.2 klein job on Kaggle (decision 32) returned all ten 16:9 images and
  none of the ten 9:16 ones. The job split the units across the two T4s, alternating, so worker 0 got
  every 9:16 unit. Its log shows the model loaded after 136 s and then nothing: no traceback, no
  result files.
- **Why (most likely):** each worker parks a full model copy in normal memory (RAM) between steps
  (model CPU offload). Two copies of the 4B model plus its text encoder were more than the machine's
  RAM, and the system killed one process. A process killed that way leaves no Python error.
- **Fix:** the keyframe job now runs one worker on one GPU (about 30 s per image, so 10 images take
  about 5 minutes). Caching meant the rerun only made the 10 missing images; the 10 finished ones
  were not regenerated.
- **Lesson:** a batch job must report units that produced no result file as failures, which the
  pipeline did ("failed on Kaggle: no result"), so nothing silently went missing from the film.

## F15. Gemini read the English style instruction aloud, and the narration turned to nonsense (Wed 25 Nov)

- **What broke:** radio cut v4 was not understandable Amharic. Two linked causes:
  1. The Gemini provider sent a style instruction ("Read in Amharic, calm, warm and unhurried…")
     in front of each line, and Gemini spoke the instruction too. The lengths gave it away: shot 8
     has three words, but its Gemini clip was 16.9 s long.
  2. One of those Gemini clips was then used as the sample voice OmniVoice copies, with only the
     Amharic line as its transcript. A sample whose words don't match its transcript made OmniVoice
     produce nonsense for every line (and made it very slow: 103 s of speech).
- **What was tried:** comparing each clip's length with its word count across voices pointed straight
  at Gemini.
- **Fix:** Gemini now gets the line alone, never an instruction in front of it. OmniVoice's sample is
  a clean Kore clip (two neutral sentences, no instruction, transcript exact). The narration stage
  now warns when a clip is far too long for its words. The Gemini comparison lines will be redone
  when its daily quota resets.
- **Lesson:** an HTTP 200 and a playable file prove nothing about the content. A cheap sanity check
  (seconds per word) would have caught this before it reached the film.

## F14. The keyframes got Ethiopian culture wrong (Wed 25 Nov, caught by me)

- **What broke:** looking at the keyframes, I found: "fresh grass" on the floor came out as a
  growing lawn, but ketema is freshly cut long grass scattered on an indoor floor; the coffee
  ceremony showed a Western iron stove, a copper kettle and mugs with handles, instead of a clay
  charcoal brazier, a flat roasting pan, a black clay jebena on a straw ring, a carved rekebot
  tray-table and small handleless cups; one shot had a Christmas tree; and the girl in shot 1 was
  deformed.
- **What was tried:** I gave Claude photos of real coffee ceremonies. They were used only to write
  exact word descriptions of the objects (the people in them were not described or used, and the
  photos were not given to the image model or committed). One shared description for each object
  is now used in every shot where it appears, so the ceremony looks the same throughout.
- **Shot 1:** reframed to a side view with the arms under the blanket, so there is less body for
  the model to get wrong, and a new seed.
- **Lesson:** the image model's default for "holiday", "grass" or "coffee" is Western. Cultural
  objects have to be named and described concretely, and checked by someone who knows them.

## F13. Cloudflare's daily free allowance ran out mid-run (Wed 25 Nov, 20:45 EAT)

- **What broke:** while regenerating four keyframes, Cloudflare Workers AI answered HTTP 429: "you
  have used up your daily free allocation of 10,000 neurons". By then 124 images had been made
  that day (reference sheet rounds and two keyframe passes). The pipeline treated the 429 like a
  per-minute limit and retried each image four times, a minute apart, which could never succeed.
- **What was tried:** the job was stopped; the error text showed it was the daily allowance, which
  resets at 00:00 UTC (03:00 EAT).
- **Fix:** a 429 whose message names a daily allowance is now a `QuotaExhausted` error: the
  pipeline stops at once with a clear message instead of retrying (decision 28a). The remaining
  keyframes run after the reset; finished ones are cached.
- **Measured:** about 10,000 neurons for 124 FLUX.2 klein images, so roughly 80 neurons per image
  (COSTS.md).

## F12. Keyframes came out as character sheets (Wed 25 Nov)

- **What broke:** keyframes for shots with people copied the layout of the reference images they
  were conditioned on: a person on a plain background with portrait insets, not a scene. One
  shot merged the father and brother into one man; one turned "roasting smoke" into fire; one
  added a Christmas tree for "holiday"; one added strangers around the mother.
- **What was tried:** a scene-first prompt ("one single full-frame scene… not a character sheet")
  fixed most shots. Shots where faces don't matter (hands, people from behind, the empty room)
  dropped the reference images and describe the people in words instead. "No fire, no flames"
  and "no Christmas tree, no Western holiday decorations" were added where needed.
- **Lesson:** reference images carry their layout, not only the face. Character sheets made good
  references for the people but the wrong template for a scene.

## F10. Cloudflare's safety filter blocked a harmless image edit (Wed 25 Nov)

- **What broke:** editing the mother's reference image with the prompt "the same woman as in the
  reference image, with the same face, hair and body, now wearing exactly this dress…" returned HTTP
  400, "Your output has been flagged".
- **What was tried:** the same request reworded ("same face and hairstyle, now dressed in exactly this
  traditional outfit"), with a new seed.
- **Fix:** the reworded prompt passed. The likely trigger was asking to keep the "body" while
  changing clothes. Edit prompts now name only the face, hair and outfit.

## F11. A code change regenerated images that had already been chosen (Wed 25 Nov)

- **What broke:** adding image editing to the reference stage added a new field to every
  character's fingerprint, so the next run regenerated all twelve reference images, including the
  three Meaza had just picked, which came back different.
- **Fix:** the picked images were still on disk and were restored in the manifest; the fingerprint
  now includes the input image only for edited candidates, so other fingerprints stay unchanged.
- **Lesson:** this is the known weak point of fingerprint option (b): any change to what goes into
  a fingerprint invalidates its cache. A new input should be added only where it exists.

## F9. The narration job waited 45 minutes in Kaggle's GPU queue (Wed 25 Nov)

- **What broke:** the OmniVoice and MMS narration job was pushed to Kaggle on GPU T4 x2 and stayed
  "queued" for about 45 minutes without starting. Earlier jobs had waited about a minute. Kaggle
  reported no error; the likely cause is demand for the shared free GPUs at that moment (Kaggle
  doesn't say why a job waits).
- **What was tried:** waiting, then checking the kernel status directly (still `QUEUED`).
- **Workaround:** the open voices are small (OmniVoice about 3 GB), so the job was cancelled and
  pushed again as a CPU-only job, which doesn't wait for a GPU. The pipeline now has a CPU option
  for these voices (`KAGGLE_TTS_DEVICE=cpu`).
- **Lesson for the GPU stages:** video and music can't move to CPU, so they are run early and as
  one batch each, and every shot still has the Ken Burns fallback if video never runs.

## F8. Gemini's per-minute limit stopped the narration run (Wed 25 Nov)

- **What broke:** generating the real narration, Gemini TTS returned HTTP 429 ("You exceeded your
  current quota") after 6 of 10 lines. The four automatic retries waited 2, 4 and 8 seconds, all
  inside the same minute, so all four failed, and the whole narration run stopped, including the
  voices that had nothing to do with Gemini.
- **What was tried:** one tiny request a minute later succeeded (logged in `runs.jsonl`), which
  showed it was a per-minute rate limit, not the daily quota.
- **Fix:** an HTTP 429 without a `Retry-After` header now waits 65 seconds before retrying, and
  each voice runs on its own: a voice that runs out of quota is reported and skipped, and the other
  voices continue. Only a failure of the film's chosen voice stops the run. This is decision 28 (a)
  in practice.

## F7. Kaggle results could not be downloaded (Wed 25 Nov)

- **What broke:** both Kaggle jobs finished, but downloading their outputs failed: Kaggle serves
  job files from a separate host that this environment's network allowlist did not include.
- **What was tried:** the error named the host.
- **Fix:** the host was added to the environment's allowlist and the outputs were downloaded
  again. The `runs.jsonl` lines written while they were missing are followed by corrected lines.

## F6. CosyVoice2 Amharic could not be installed on Kaggle (Wed 25 Nov)

- **What broke:** installing CosyVoice's pinned requirements failed on Kaggle's image (pip exited
  with an error), so neither CosyVoice2 sample was produced. MMS and OmniVoice in the same job
  worked, because each model is set up and saved separately.
- **What was tried:** nothing yet beyond the documented install.
- **Next:** read the pip error in the job log (`outputs/voicebench/kaggle_logs/`) and install only
  what inference needs, or drop CosyVoice2 from the benchmark if it costs too much time; the
  decision and its reason will be recorded here.

## F5. Wan 2.2 ran out of GPU memory on a free T4 (Wed 25 Nov)

- **What broke:** the first Wan 2.2 TI2V-5B test (480×832, 81 frames, 30 steps, half precision,
  model CPU offload) loaded in 282 s and then failed after 15 s: CUDA out of memory, 14.54 GiB of
  the T4's 14.56 GiB in use.
- **What it means:** the reviewer's concern was right; the default settings don't fit a 16 GB T4.
- **Tried:** sequential CPU offload (weights moved to the GPU layer by layer), VAE tiling and
  slicing, `expandable_segments` to reduce fragmentation, and 49 frames instead of 81.
- **Fixed:** the second test produced a clean 2.0 s clip at 480×832 (49 frames, 24 fps). It took
  781 s of GPU time for one clip, plus about 40 minutes of job overhead (installs and the model
  download) per job. Cost: much slower generation in exchange for fitting in memory.

## F3. ElevenLabs' newest model refused Amharic as a language code (Wed 25 Nov)

- **What broke:** the first ElevenLabs smoke call failed with HTTP 400: "Model 'eleven_v3' does
  not support language_code 'am'." The API key also lacks permission to list models, so the
  supported languages could not be read from the API.
- **What was tried:** the same Amharic test sentence was sent to four models (eleven_v3,
  eleven_multilingual_v2, eleven_flash_v2_5, eleven_turbo_v2_5) without a language code. All
  four returned audio (logged in `runs.jsonl`, audio in `outputs/smoke/`).
- **Workaround:** the provider no longer sends a language code unless one is configured. Whether
  the audio is actually understandable Amharic is not known from a 200 response: it goes to a
  native-speaker listen and the speech-recognition check.

## F4. The Kaggle command-line tool would not accept a proxy-injected token (Wed 25 Nov)

- **What broke:** API keys in this setup are injected into request headers by a network proxy,
  so the code never holds them. Kaggle CLI 2.x first checks a new-style token by sending it
  in a request body, which a header-injecting proxy cannot fill in, so it refused to start.
- **What was tried:** skipping that check still failed (HTTP 401), because the saved credential
  was a legacy `kaggle.json` key, not a new-style token.
- **Fix:** the legacy username + key are saved as Basic authentication, which travels in a
  header. The pipeline runs the CLI with the legacy key path; listing kernels then worked.

## F2. Crossfades refused to join segments (Wed 25 Nov)

- **What broke:** the first full film run stopped in the join step. FFmpeg's `xfade` filter
  reported that its two inputs had different timebases (1/1000000 vs 1/12288): the output of a
  `concat` (used for straight cuts) and a segment file did not match.
- **What was tried:** the error named the filter and the mismatch, so the fix went straight there.
- **Fix:** every segment is normalised to 24 fps and the same timebase (`fps=24,settb=AVTB`)
  before joining, and the output of each `xfade` or `concat` is set back to that timebase.
  Mixed cuts and crossfades now join in one pass.

## F1. An audio step never stopped and filled the disk (Wed 25 Nov)

- **What broke:** the first radio-cut run did not finish. One FFmpeg command placing the
  narration on the timeline kept writing audio until the temporary disk was full: a 60 GB WAV
  file, 186 hours long.
- **What was tried:** the step was reproduced in isolation with a 2-second test tone and a
  20-second time limit. It ran until killed, which showed the cause: `apad` (pad with silence)
  produces audio forever, and the `atrim=duration=…` placed after it did not end the filter
  graph in this FFmpeg build.
- **Fix:** `apad=whole_dur=<film length>` pads only up to the film's length, and every mixing
  command also gets an explicit output duration (`-t`) as a second safeguard. Temporary
  folders are now deleted at the end of every command. The radio cut then took 28 seconds.
- **Lesson:** every FFmpeg command that can generate audio needs a hard length limit.
