# Failures

What broke, what was tried, and what fixed it or how it was worked around. Includes quota,
memory, consistency and language problems, and tools that changed or disappeared. Newest first.

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
