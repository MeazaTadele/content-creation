# Ethics: consent, licences, labelling

## Consent

Consent is recorded here **before** anything depicting or voicing a real person is generated.
Each record is informed: the person is told the film is AI-generated, what the narration says
about them, and that it will be posted publicly with an AI label, and that they can say no.

| Person | Shown or voiced | Consent | Given how, when | Their words |
|---|---|---|---|---|
| Meaza (me) | shown as a child; narration is in my voice as narrator (AI text-to-speech, not a clone of my voice) | _pending_ | | |
| My mother | shown as a character based on her | _pending_ | | |
| Henok, my brother | _to be decided whether he appears_ | _pending_ | | |

No voice is cloned from a real person.

## Licences

| Model or tool | Used for | Licence or terms | Notes |
|---|---|---|---|
| Wan 2.2 TI2V-5B | video clips | Apache 2.0 | |
| ACE-Step 1.5 | music | MIT; outputs usable commercially | |
| FLUX.2 klein 4B | keyframes | Apache 2.0 (the 9B model is non-commercial and not used) | via Cloudflare Workers AI |
| OmniVoice Amharic | voice benchmark | Apache 2.0 | |
| MMS-TTS (Amharic) | voice benchmark | CC BY-NC 4.0, non-commercial | fine for this non-commercial film; text is romanised with uroman first |
| Gemini, Gemini TTS | script, narration | Google API terms | _to check_ |
| ElevenLabs | voice benchmark | ElevenLabs terms (free plan) | _to check: attribution and commercial-use terms_ |
| CosyVoice2 Amharic | voice benchmark | CC BY-SA 4.0 (base model Apache 2.0); adds a PerTh watermark to its audio | needs a reference voice: a synthetic Gemini clip is used, never a real person's voice |
| FFmpeg | assembly | LGPL/GPL | |

## Labelling

- A visible end card says the film was made with AI and names the models.
- The platform's AI-content label is switched on when the film is posted.
- Watermarks and provenance metadata (SynthID, C2PA) are left intact; the pipeline does not strip them.

## Private data

- Free AI services may use what they receive for training. Image prompts describe characters
  in general terms; personal family details are kept out of prompts.
- Logs, outputs and notebook files are checked for keys and private details before each push.

## Style

Visual style is described by its qualities (warm, soft, painted), never by naming a living artist.
