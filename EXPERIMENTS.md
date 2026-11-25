# Experiments

Each entry: **hypothesis → change → result**, with the evidence (log lines, measurements) and
the reason for the choice that followed. One thing is changed at a time; seeds are fixed when
comparing prompts.

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
