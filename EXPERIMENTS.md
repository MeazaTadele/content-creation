# Experiments

Each entry: **hypothesis → change → result**, with the evidence (log lines, measurements) and
the reason for the choice that followed. One thing is changed at a time; seeds are fixed when
comparing prompts.

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
