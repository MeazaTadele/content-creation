# Ethics: consent, licences, labelling

## Consent

Consent is recorded here **before** anything depicting or voicing a real person is generated.
No real person's voice is cloned: the narration is an AI voice. OmniVoice is given a reference clip only to keep one narrator across lines, and that clip is itself AI-generated (`outputs/voicebench/samples/omnivoice_1.wav`). The first generation of any
kind in this project was on Wed 25 Nov (see `runs.jsonl`); all consent below was given earlier.

### Records

| Person | Role in the film | Asked | Replied | Status |
|---|---|---|---|---|
| Meaza (me) | narrator; shown as a girl of about twelve (shots 1, 4 and 8) | — | — | I consent as the author of the film |
| My father | appears seen from behind or as hands only (shots 3 and 7); replied for both parents | Tue 24 Nov 2026, 20:02 EAT, Telegram | Tue 24 Nov 2026, 21:11 EAT | agreed, for himself and for my mother |
| My mother | shown as a drawn character based on her (shots 5 and 9); the story is about her | same message, sent to both parents | through my father's reply | agreed (relayed by my father) |
| Henok, my brother | appears seen from behind or as hands only (shots 3 and 7) | Tue 24 Nov 2026, 20:02 EAT, Telegram | Tue 24 Nov 2026, evening | agreed |

### The messages, word for word

**To my parents** (Amharic):

> ሰላም ጋሼ እና እናት እንዴት ዋላችሁ፣ እየወሰድኩት ላለው ትሬኒንግ ፊልም ስሩ ተብለን ነበር እና እኔ የምሰራው
> ፊልም እኛ ቤት ስላሳለፍነው አንድ ፋሲካ በዓል ነው እና ስለእናንተ ያወራል። ከመስራቴ በፊት የእናንተን ፈቃድ
> መጠየቅ ስላለብኝ ነው፤ ፈቃደኛ ናችሁ?

English: "Hello Dad and Mom, how was your day? For the training I'm taking, we were told to make
a film. The film I'm making is about a Fasika holiday we spent at home, and it talks about you.
Before I make it I need to ask for your permission. Do you agree?"

**My father's reply:**

> መልካም፣ እኔም እናትሽም ተስማምተናል። Good luck እምዬ

English: "Good. Both your mother and I agree. Good luck, Emeye."

**To Henok** (English):

> hey bro i am making a short AI film for a course about a holiday morning in our house. and
> you are gonna be part of it, wanted to get you consent first

**Henok's reply:** "yeah go ahead"

### Notes on these records (Wed 25 Nov)

- **Why my mother's consent came through my father:** my mother does not text, and my parents live
  in a different city from me, so she could not reply in writing herself. The message was addressed
  to both of my parents, and my father replied for both of them. I decided to keep the record as it
  is rather than send a further follow-up.
- **What the messages said and didn't say:** my parents' message explained that the film is for my
  course, is about a Fasika holiday at home, and talks about them. It did not say that the pictures
  and voice are made by AI or that the film will be posted publicly. Henok's message said it is an
  AI film, but not that it will be public. I am recording this openly rather than leaving it out.
- **Photos were used only to write descriptions (Wed 25 Nov):** to make the characters look more
  like my family, I showed Claude Code photos of my mother, father and brother, plus a photo of a
  traditional dress. Claude turned them into word descriptions (skin tone, face shape, hair,
  clothing) in `storyboard.json`. The photos were not given to any image model, not uploaded to
  any service by the pipeline, and are not in this repository. The drawn characters are therefore
  closer to my family's likeness than before, which this record states openly.
- **Clothing reference photos:** photos of traditional outfits (a dress in a shop, and two people
  modelling clothes, strangers to me) were used only to describe the clothes in words. Their faces
  were not described or used, and the photos were not given to any model or added to this repository.

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
