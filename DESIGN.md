# Design

Audience and intent were written **before anything was generated**: this file's first commit
comes before the first model call in `runs.jsonl`. The two user tests, and what changed because
of them, are added below as they happen.

## The film

A 60–90 second film, narrated in Amharic with English subtitles, about one of my happiest
moments: the Fasika (Ethiopian Easter) morning I woke up and my mother was home. It is the
first holiday I remember celebrating with her there.

## Audience

| Who | Relationship | Where and how they watch |
|---|---|---|
| Betty | friend | on their own phone, sent as a video on Telegram |
| Yishak | friend | on their own phone, sent as a video on Telegram |
| Henok | my brother | on my phone, watching with me |

## Intent

When the film ends, they should:

1. **feel happy**: they have just seen one of my happiest moments, my happiest holiday;
2. **understand the importance of being there**: a parent's presence, and the presence of the
   people you love in general. Love is not only providing for the people you love; it is being
   there with them;
3. **start thinking about their own families**: how holidays are in their homes, and their own
   happy holiday moments.

## What this means for the film

- **Vertical first.** Two of the three watch on a phone, so 9:16 is the main version. The 16:9
  version shows the vertical picture over a blurred copy of itself.
- **Subtitles burned in.** Telegram videos often start muted, and Betty and Yishak may watch
  without sound at first. The English subtitles stay inside the phone's safe area.
- **A phone-speaker mix.** The narration has to stay clear on a phone speaker, so the music is
  ducked well under the voice.
- **Henok watches with me.** I can see his reaction directly. He may also remember the day
  himself, so his view of what the film gets right is different from Betty's and Yishak's.

## How we will know it worked

The same core questions are asked in both user tests, before I say what I intended:

- What happened in the film? Tell it back in your own words.
- What did you feel at the end?
- What do you think the film is saying about being there for people?
- Did it make you think of a holiday in your own family? Which one?
- Was there a moment you got lost or bored? Where?
- Was any Amharic word unclear or mispronounced?

## User test 1: radio cut

**What was tested:** `outputs/final/radio_cut_9x16.mp4`, OmniVoice narrating all ten lines over
placeholder music with English subtitles on black (about 100 s). Asked the three questions in
`docs/user-tests/questionnaire.md`.

| Who | How | What they said |
|---|---|---|
| Henok (brother) | Wed 25 Nov, evening | "Okay got it, the story is nice, but if the Amharic version matters, it doesn't feel natural. Maybe if you have the time and the means, the Amharic needs a lot of change (the English version is nice). On the story demo, if you develop the story (explain a little more) at the beginning a little it would be nice, on the place that says 'For me every holiday is the same.'" |
| Yishak (friend) | Wed 25 Nov, evening | It sounds robotic, like someone reading off a script; it doesn't sound natural at all. |
| Betty (friend) | Wed 25 Nov, evening | Same as Yishak: it sounds like someone reading from a script. The transcript could be a little better, with better storytelling, and there are a lot of noticeable pauses. |

**What I take from it so far:**

- Both found the **Amharic narration unnatural**. Yishak described the voice as robotic, like
  reading a script; Henok said the Amharic itself needs a lot of change, while the English reads well.
- Henok understood the story and liked it, but wants **more at the beginning**, around shot 2
  ("For me every holiday is the same"), to explain the situation before the turn.
- Betty agreed about the script-like reading, asked for **better storytelling in the text**, and
  noticed **a lot of pauses**.
- All three understood the order of events; nobody was confused about what happened.
- **All three** heard the narration as unnatural. That is the clearest finding of this test.

**What changed:** see "Storyboard changes traced to feedback" below. In short: I rewrote the
narration myself, the narrator now follows my own recorded voice, and the pauses are tighter.


## User test 2: near-final cut

**What was tested:** `outputs/final/rough_cut_v1_9x16.mp4` (Thu 26 Nov): all ten shots (three video
clips, seven slow moves over keyframes), the locked narration (radio cut v9), English subtitles,
the end card and placeholder music; 62.8 s. The same three testers and the same three questions as
test 1 (`docs/user-tests/questionnaire.md`), sent the same way (Telegram for Yishak and Betty, my
phone for Henok).

| Who | How | What they said |
|---|---|---|
| Betty (friend) | Thu 26 Nov, Telegram | "It is a very sweet story, made me miss my mom." |
| Henok (brother) | Thu 26 Nov, on my phone | "I actually forgot about that day and how holidays looked like back then, it's very nice." |
| Yishak (friend) | Thu 26 Nov, Telegram | "The characters look Ethiopian, the clothes, the ketema looks nice, the story as well is very sweet." |

All three also said the sound is much better than in the radio cut.

**What I take from it:**

- **The intent landed** (DESIGN.md, Intent): Betty thought of her own mother and Henok remembered
  our own holidays back then. That is the reaction I wanted: thinking of their own family.
- **The narration problem from test 1 is gone:** in test 1 all three heard the voice as robotic or
  read from a script; now all three said the sound is much better.
- **The cultural details read as right:** Yishak named the Ethiopian look of the characters, the
  clothes and the ketema. Those were the details I corrected after the first keyframes (ketema as cut
  grass on the floor, traditional clothes, no Western objects; FAILURES.md F14).
- **Nobody reported anything confusing, too slow or mispronounced** (question 3). They answered in
  their own words rather than one answer per question, so questions 1 and 3 have no separate answer;
  none of them described the story wrongly.

**What changed:** nothing in the storyboard. Nobody raised a problem, and I did not want to change
something only to show a change. The only change after this test is the planned one: the chosen
ACE-Step music replaces the placeholder music.

## Storyboard changes traced to feedback

| Feedback (test 1) | Who | Storyboard change | Evidence |
|---|---|---|---|
| The narration sounds read from a script; the story needs better storytelling | Yishak, Betty, Henok | I rewrote all the narration lines myself, warmer and more natural (radio cut v2) | commit cbb4f12 "Storyboard changes from user test 1" |
| More at the beginning, around "every holiday is the same" | Henok | Lines 1 and 2 made longer, to explain why I stay in bed and why holidays were the same at home | commits c5227d3, 75e7df3 |
| The voice is robotic, not natural Amharic | all three | The narrator follows my own recorded voice as its sample, slowed to tempo 0.9 (`voice.references`, `voice.tempo`; decisions 25b, 33) | commits 0d0259a, 1f2ad00 |
| A lot of noticeable pauses | Betty | Pauses cut to 0.25 s before and 0.5 s after each line, shots at least 3.5 s (`pacing`) | commit 75e7df3 |

Test 2 raised no problems, so no storyboard change came from it (see above). The picture changes made
on Thu 26 Nov (decisions 34-39) came from my own review of the keyframes, not from the testers.
