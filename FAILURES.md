# Failures

What broke, what was tried, and what fixed it or how it was worked around. Includes quota,
memory, consistency and language problems, and tools that changed or disappeared. Newest first.

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
