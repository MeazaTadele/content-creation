# Experiments

Each entry: **hypothesis → change → result**, with the evidence (log lines, measurements) and
the reason for the choice that followed. One thing is changed at a time; seeds are fixed when
comparing prompts.

## E11. Does telling the video model what must not appear remove an artefact? (Thu 26 Nov)

- **Hypothesis:** the first good s06 clip (Wan 2.2) grew a glowing pink rod halfway through. Meaza
  wanted nothing added, only smoke moving. A motion prompt that says the camera is still and only
  the smoke moves, plus a "must not show" list for this shot (sword, rod, wand, glowing light, new
  objects, moving people, camera movement), should give a clip with nothing new in it.
- **Change:** `motion.prompt` rewritten, `motion.negative` added (a per-shot field, so s05 and s09
  kept their fingerprints and were not regenerated), and a new seed (3006).
- **Result:** the new clip has no rod and no added objects; only the smoke moves, the camera almost
  still (`outputs/shots/s06_frames_check.jpg`). Cost: one more Wan run, 21 min of GPU session.
- **Caveat:** the seed changed too, so I can't say how much of the fix is the wording and how much is
  the new seed. One run each is not enough to separate them.
- **Decision:** keep the new clip (decision 39). The per-shot "must not show" list stays as an option.

## E10. Does masked repainting change only what I ask? (Thu 26 Nov)

- **Hypothesis:** after E9, an inpainting model given a mask should change only the masked areas.
  For s08: remove the girl sitting with my father and brother, and put me (at the door) in my olive
  pyjamas.
- **Change:** two polygons in `storyboard.json` (`image.inpaint`), SDXL inpainting on Kaggle, three
  seeds. After each step the code pastes back every pixel outside the mask, so the rest of the
  picture cannot change.
- **Result:** the girl was removed in 3 of 3 candidates (an empty seat in her place). The pyjamas:
  olive trousers in 2 of 3, but the top came out cream or white in all three, not the olive t-shirt.
  Everything outside the masks is identical to v4 by construction. 5 min of GPU session for all three.
- **What it taught me:** removing something is easy for inpainting; matching a specific outfit from
  words alone is harder, because SDXL inpainting can't take the character reference image.
- **Decision:** Meaza chose candidate C (seed 3208, decision 38).

## E9. Can the open image model change one thing in a picture? (Thu 26 Nov)

- **Hypothesis:** FLUX.2 klein takes reference images, so giving it the chosen picture first, with
  "keep everything, change only X", should make a targeted edit (s07: make my father and brother as
  big as my mother; s08 and s09: two small changes each).
- **Changes and results:**
  1. "Keep the picture exactly the same, except…": 6-15% of pixels changed in each picture and none
     of the requested changes happened (measured against v4).
  2. Describing the wanted result instead, with the father and brother references, four seeds: the
     men a little bigger, still smaller than my mother.
  3. Rebuilding s07 as a wider shot from the s05 room, the men beside her: bigger, but 3 of 4
     candidates had the wrong people (two fathers, an extra man, a bald brother).
  4. Gemini's image editing instead: refused, not on the free tier (F18).
- **What it taught me:** the fast 4-step model follows its reference picture very closely. That is
  what made E8 work, and also why it can't edit: it copies.
- **Decision:** s07 stays as v4 (decision 36); s08 moves to masked repainting (E10).

## E8. Does giving the model one shot's picture keep the room the same? (Thu 26 Nov)

- **Hypothesis:** in the first full keyframe set, every shot invented a new room, with a new coffee
  table, jebena and brazier, though the story happens in one room. Giving the image model the s05
  picture as the first reference image should keep the room the same in s06-s10.
- **Change:** `image.scene_from: "s05"` on s06-s10, and a fixed sentence in the prompt saying the
  first reference image is the room to keep (decision 34).
- **Result:** in the v4 sheet, s06-s10 show the same walls, window, seats, carved table, jebena on
  its straw ring, brazier and ketema as s05 (`outputs/keyframes/contact_sheet_9x16_v4.jpg`, compared
  with `contact_sheet_9x16_v3.jpg`). New problems appeared with the people: an extra girl on the seat
  in s08, a wrong family in s10, and the father and brother small next to the mother in s07.
- **Decision:** keep `scene_from`; fix the people shot by shot (E9, E10).

## E7. Can the narrator keep my delivery without my voice? (Wed 25 Nov)

- **Hypothesis:** radio cut v3 (OmniVoice copying my own 11 s sample) had the natural Amharic
  delivery and pronunciation that user test 1 asked for, but sounded like me. Another sample voice,
  or OmniVoice's voice-design words, might keep the delivery with a different voice.
- **Changes and results:**
  1. A synthetic female sample (Gemini Kore): first attempt broken by F15 (Gemini read its English
     instruction aloud); with a clean sample, the voice was a woman's but the Amharic pronunciation
     and pace were wrong to my ear, even at speed 1.25 (radio cuts v4-v7).
  2. My sample plus voice-design words ("female, young adult, high pitch" and two others) on one
     line: the three clips differ, but all still sounded like me.
- **What it taught me:** OmniVoice takes timbre and delivery from the same sample; they can't be
  separated with its own options. The pace also comes from the sample (its duration estimator
  scales by the sample's speaking rate).
- **Decision:** keep v3 (my voice, with consent), slowed to tempo 0.9 with FFmpeg so nothing is
  re-voiced.

## E6. Does a different OmniVoice voice remove the "reading a script" feeling? (Wed 25 Nov)

- **Hypothesis:** user test 1 (all three testers) heard the narration as script-like. OmniVoice
  copies the delivery of its sample voice, and the sample was a test sentence, so a voice
  generated without that sample might sound more natural.
- **Change:** five OmniVoice voices, each with a different seed and no sample voice, read the same
  line (shot 9) on Kaggle's CPU (`outputs/voicebench/casting/`, `runs.jsonl` stage
  `voicecasting`). Everything else unchanged.
- **Result:** my judgement as a native speaker: all five still sound like someone reading a
  script, and the narrator needs to be a woman's voice. All five clips were exactly 10.4 s, so
  OmniVoice appears to set the length from the text alone, which may be part of the flat,
  read-aloud rhythm.
- **Decision:** move on with the pictures and come back to the voice before user test 2 (only the
  narration, timing and assembly rerun). Next to try: a female AI sample voice for OmniVoice to follow.

## E5. Can image editing change clothes but keep a face? (Wed 25 Nov)

- **Hypothesis:** giving FLUX.2 klein an already-chosen character image plus "the same person, only
  the outfit changes" keeps the face while changing the clothes, which plain text generation can't
  do (every new description gave a new face).
- **Change:** two attempts. (1) Mother: edit candidate 1 to a specific kemis; prompt listed the whole
  dress. (2) Father and brother: edit their chosen round-4 images to one simpler outfit (white
  tunic with a red embroidered border, a striped gabi over one shoulder, beige trousers, sandals).
- **Result:** (1) barely changed the dress: the edits kept the original short tunic and skirt. One
  wording was also blocked by Cloudflare's safety filter (FAILURES.md F10). (2) worked: both men
  kept their faces and beards and wore the new outfit (`outputs/refsheet/contact_sheet_v7.jpg`,
  "before" next to the edits).
- **What it suggests:** editing works when the change is a clear swap of one outfit for a simple
  one; a long, detailed dress description competes with what is already in the image. For the
  mother, generating fresh with the full description worked better (rounds 6 and 7).

## E4. Do more specific character descriptions fix the faces? (Wed 25 Nov)

- **Hypothesis:** reference sheet round 1 used short descriptions ("an Ethiopian woman in her
  forties…") and gave faces that read as South Asian or European, and a girl who looked 6–8. More
  specific descriptions (skin tone, face shape, hair, exact clothing, "Habesha Ethiopian") should
  give recognisably Ethiopian characters of the right age.
- **Change:** descriptions rewritten in words from family photos (the photos themselves were not
  given to the model; ETHICS.md); new seeds; same model (FLUX.2 klein 4B), same style block.
- **Result:** clothing improved a lot: the mother's white kemis with a tibeb border and a
  blue-and-maroon netela, the father's houndstooth jacket, the brother's plaid shirt all match.
  Faces are still not clearly Ethiopian, and the girl still looks younger than twelve. The word
  "Habesha" seems not to be understood by the model. Evidence: `outputs/refsheet/contact_sheet_v1.jpg`
  and `contact_sheet_v2.jpg`.
- **Round 3** (my notes: brother is 19 with a beard; mother without a headscarf, in the specific
  kemis from a reference photo of the dress): the dress came out close to the photo (tibeb panel,
  crosses, sash, leaf motifs). Faces were still generic.
- **Round 4** (named facial features instead of the label alone: slender oval face, large
  almond-shaped eyes, narrow nose, tightly curled hair; the girl "tall, slim, on the edge of her
  teens"): the girls now read as Ethiopian and older, with braids; the mother is closer, mostly in
  candidates 0 and 2; the father and brother improved less. Evidence:
  `outputs/refsheet/contact_sheet_v3.jpg`, `contact_sheet_v4.jpg`.
- **What it taught me:** the model follows concrete visual words (features, clothing details) far
  better than identity labels. Four rounds took about four minutes of generation in total.

## E3. Can Wan 2.2 make video on a free Kaggle T4? (Wed 25 Nov)

- **Hypothesis:** Wan 2.2 TI2V-5B can turn a keyframe into a short clip on a 16 GB T4 if memory
  use is reduced.
- **Change:** run 1 used half precision with model-level CPU offload, 480×832, 81 frames: out of
  memory (FAILURES.md F5). Run 2 changed only memory settings and length: sequential CPU offload,
  VAE tiling, 49 frames.
- **Result:** run 2 worked: a 2.0 s, 49-frame clip in 781 s of GPU time. The image is clean and
  consistent with the keyframe, but the motion is very small (the prompt asked for rising steam;
  the frames barely change). Evidence: `outputs/smoke/wan_test_wantest.mp4`, `runs.jsonl` (stage
  `smoke`, unit `wan22-feasibility`).
- **What it means:** about 13 GPU minutes per clip, so 8–12 shots fit easily in the weekly quota
  (about 2–3 GPU hours, with two clips at a time on the two T4s). But a 2 s clip is shorter than a
  6–8 s shot; how to fill the rest is an open design question.

## E2. Do the open Amharic models beat the hosted ones? (Wed 25 Nov)

- **Hypothesis:** models built or fine-tuned for Amharic (OmniVoice Amharic, MMS-TTS Amharic,
  CosyVoice2 Amharic) should sound more natural than general multilingual voices.
- **Change:** the same two neutral sentences ("ሰላም። ይህ የድምፅ ሙከራ ነው።" and "በበዓሉ ጠዋት ቤቱ በቡና
  መዓዛ ተሞላ።") were read by Gemini 3.8 Flash TTS (API) and by MMS and OmniVoice (one Kaggle job,
  GPU T4). CosyVoice2 could not be installed (FAILURES.md F6).
- **Result:** OmniVoice was my clear favourite as a native speaker; Gemini was also good.
  Generation time per sentence on the T4: OmniVoice 1.4–1.9 s, MMS 0.3 s after an 11 s warm-up
  (`runs.jsonl`, stage `voicebench`).
- **Caveat:** this is my own, non-blind first listen on two sentences. Decision 25 says blind
  listening by the testers decides the film's voice; the speech-recognition check and this note
  support it.
- **Next:** generate the real narration lines with the leading voices and run the blind test.

## E1. Which ElevenLabs model can read Amharic? (Wed 25 Nov)

- **Hypothesis:** ElevenLabs lists Amharic among its text-to-speech languages, so at least one of
  its models should read an Amharic sentence acceptably.
- **Change:** the same Amharic test sentence ("ሰላም። ይህ የድምፅ ሙከራ ነው።", "Hello. This is a voice
  test.") was sent to four models (eleven_v3, eleven_multilingual_v2, eleven_flash_v2_5,
  eleven_turbo_v2_5) with the same voice, after eleven_v3 rejected the language code `am`
  (FAILURES.md F3). Gemini 3.8 Flash TTS read the same sentence for comparison.
- **Result:** all four ElevenLabs models returned audio (HTTP 200; `runs.jsonl`, stage `smoke`),
  but to a native speaker's ear (mine) the ElevenLabs Amharic was very bad. Gemini's reading of
  the same sentence was good.
- **Evidence:** audio in `outputs/smoke/`; calls and latencies in `runs.jsonl`.
- **Decision that followed:** an HTTP 200 does not mean the language works. ElevenLabs stays in
  the benchmark as a measured low baseline, but is not a candidate for the film's narration.
  Next: hear the open Amharic models (MMS, OmniVoice, CosyVoice2) on the same sentences.
