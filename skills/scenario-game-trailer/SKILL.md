---
name: scenario-game-trailer
description: "Use when a game, often a simple casual or mobile one, needs a cinematic trailer made with Scenario: screenshots, a gameplay clip, a logo, or only a game idea turned into a 40 to 60 second launch trailer or teaser that looks like an animated feature film, with the characters recast in 3D, a genre-parody story, a narrator, one score, and a logo end card. Keywords: game trailer, launch trailer, teaser, cinematic trailer, gameplay to trailer, reveal trailer."
license: MIT
---

# Scenario Game Trailer

## Overview

A casual game that looks simple (flat 2D, isometric, side view, low-poly) becomes a trailer that looks like an animated feature film. **Only two things carry over: the character idea and the gameplay idea.** The look, the story, the music, and the sound are new. The reference run made three trailers of 47 to 52 seconds, 13 to 16 shots each: an isometric diner rush as an action-movie comeback, a block-cat stacker as an epic fantasy, a low-poly delivery racer as a monster movie.

Image-to-video is by far the largest cost, so the stills carry every decision and the user approves the priced shot list before anything animates. Pick every model with `recommend` at run time, read `model_schema_get` before each first call, and price each paid step with `dry_run=true`. Connection and the core loop: see the `scenario` skill. Game art when none exists: `scenario-game-assets`; motion and the first-and-last-frame lane: `scenario-video`; song, narrator, and effects: `scenario-audio`; the Video Studio contract: `scenario-video-assembly`. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

The two scripts run locally on downloads and only measure; the edit itself is a Video Studio run. They need Python 3 with numpy and Pillow, plus ffmpeg on the PATH for `song_hits.py`. Each prints its usage without arguments, refuses to overwrite an output without `--force`, and never writes over its input.

## Quick reference

| Stage           | What happens                                                                                          | Detail                                     |
| --------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| 1. The game     | If none exists: a character sheet, a transparent logo, three screenshots, a five-second gameplay clip | `scenario-game-assets`                     |
| 2. The cast     | One 3D sheet per character (close-up, front, side, back) from the game art, world frames per location | [prompts](references/prompts.md)           |
| 3. The story    | A genre whose grammar fits the gameplay, one joke at the end, beats laid out as song sections         | [shot list](references/shot-list.md)       |
| 4. The song     | One continuous song in sections sharing tempo, key, and theme, then its hits measured                 | [song_hits.py](scripts/song_hits.py)       |
| 5. Shot list    | 13 to 16 shots timed to the measured hits, each with a size, a camera move, and one action            | [shot list](references/shot-list.md)       |
| 6. Stills       | One 16:9 still per shot, cast sheet as reference, the look described in words                         | [prompts](references/prompts.md)           |
| 7. Motion       | Image-to-video per shot, 4 to 10 seconds, real-time speed, generated audio off                        | `scenario-video`                           |
| 8. Voice, sound | Three narrator lines at most, directed in brackets; one sound effect per beat                         | `scenario-audio`                           |
| 9. End card     | Logo pieces extracted, aligned back onto the logo, revealed on the title hit, the exact logo last     | [align_pieces.py](scripts/align_pieces.py) |
| 10. The cut     | One Video Studio timeline: clips on their hits, the song, the voice, the effects, the end card        | `scenario-video-assembly`                  |

## Worked example: a 47-second monster-movie trailer for a delivery game

1. **The game.** A T-rex pizza courier on a tiny scooter in a low-poly toy town. With no game art yet, `recommend` an image member, price it, and make a character sheet, a transparent logo, and three screenshots with a HUD; animate one screenshot into a five-second gameplay clip. Keep it plain: it is the before the trailer is compared against.
2. **The cast.** `upload_asset` the game sheet (or reuse its asset id), `recommend` with `capability="img2img"`, and ask for one cast sheet that translates every character into a photoreal stylized 3D animated feature film look: close-up, front, side, and back, same colors, outfits, and proportions. `asset_display` it for approval before any shot uses it.
3. **The story.** A delivery race becomes a monster movie: the delivery promise, the ride through town, giant footsteps in the rain, a family frozen on the couch, a shadow on the curtains, the doorbell, and the punchline that it is only the pizza, a little late. Lay those beats out as song sections: an intro, a driving ride, a drop to silence for the scare, a slam, a title hit.
4. **The song.** `recommend` with `capability="txt2audio"` and "one continuous trailer score in sections"; confirm a sections field on `model_schema_get`. Every section line repeats the tempo, key, and theme ("one continuous original action-comedy film score, 120 bpm, E minor, one catchy main theme throughout"), then says what changes; keep each line short, since some members cap a section's text. `asset_download` it and run `python3 scripts/song_hits.py music.mp3 hits.json`: tempo, beat length, loud and silent sections, and the strongest hits.
5. **The shot list.** Fill the template in [references/shot-list.md](references/shot-list.md) against `hits.json`: the scare starts in the silence, the reveal lands on a hit, the title on the biggest hit near the end. Durations in whole beats keep the cut musical.
6. **Stills.** One `model_run` per shot on an image member, with the cast sheet (and the world frame for that location) as references and a prompt that states shot size, lens, light, and one action: "Cinematic film still from a photoreal stylized 3D animated feature film. Extreme close-up in a dark family kitchen at night: a glass of water on a wooden table, its surface showing perfect concentric ripple rings, as if from a distant heavy footstep. Anamorphic lens, shallow depth of field." Describe the look and never name a film studio or a film: video members reject studio names and music members reject film titles. Review the set on one sheet from `model_scenario-grid-maker` (a fixed first-party id: Scenario's single deterministic grid tool, so discovery would only re-derive it) and fix a wrong still by generating it again, never by fixing its clip.
7. **Motion.** `recommend` with `capability="img2video"`, then read the duration enum, the resolution, the first-frame and last-frame fields, and the audio toggle on `model_schema_get`. `dry_run` every shot and quote the user the whole list before launching. Launch with `wait=false` under the team's concurrency ceiling (the `scenario` skill), then `jobs_wait` on at most 32 ids per call, re-called with `pending_job_ids` as `job_ids`. Prompt "real-time speed" for action, since slow motion makes comedy drag, and keep generated audio off. One continuous camera move (a crane from the base of a tower to its top) takes a first and a last frame. Review each clip across its frames as `scenario-video` describes, not from its first frame.
8. **Voice and effects.** `recommend` with `capability="txt2audio"` for the narrator, audition voices on one line, then direct the chosen one in brackets: `[deep, ominous movie-trailer voice, slow, almost whispered] Something is coming... for dinner.` Three lines at most. A sound-effects member makes one effect per beat (footsteps, doorbell, scooter). A character line goes in only where a mouth on screen moves with it.
9. **The end card.** Extract each logo piece (letters, emblem, the character) with an image edit on a transparent background, `asset_download` the pieces and the logo, then run `python3 scripts/align_pieces.py logo.png pieces/ aligned/` and `upload_asset` each aligned PNG. A high `error` in `aligned/align.json` means the edit redrew the piece: cut that piece from the original logo instead. Every aligned PNG is the logo's size, so in Video Studio each piece takes the logo's exact position and size, and staggered `startTime` plus `fadeIn` reveals the pieces on the beats before the title hit. The contract in `scenario-video-assembly` carries no motion fields, so the pieces are revealed in place, not flown in. The exact logo fades in last, over a dark background still, with a Play Now button rendered by `scenario-text-overlay`.
10. **The cut.** `asset_get` every source for its real duration, then one `model_run` on `model_scenario-compose-video` (the fixed id and full contract are in `scenario-video-assembly`):
    - Each clip is a video layer at its shot's `startTime`, with `trimStart` as the in-point that lands its key moment (a slam, a jump, a door) on its hit, and `mute: true`.
    - The song is an audio layer from zero. `volume` is fixed per layer and there is no sidechain, so to duck it, lay the bed as consecutive layers over the same song, each with its `startTime` equal to its `trimStart` so the song stays continuous, and a lower `volume` on the layers under a narrator line.
    - Narrator lines and effects are audio layers at their beats; the end card layers come last.
    - A composition holds at most 50 layers and a full trailer gets close: compose the picture and effects first, then use that master as the video layer of a second pass with the song and the voice.
    - If the song ends before the logo settles, add one more bed layer that replays its main theme under the end card.

    `asset_display` the result and check that each visible cue lands on its sound.

## Common mistakes

- **Stitching music from several tracks.** It never matches. Make one continuous song and cut the picture to it.
- **Cutting the edit locally.** ffmpeg on the downloads is the wrong lane: the scripts measure, and the timeline is a Video Studio run, so every layer stays an asset.
- **A stock narrator voice.** The first narrator sounded like every trailer. Audition on one line, then direct the chosen voice in brackets.
- **Generated clip audio under the score.** Video members can add music that clashes with the song. Turn generated audio off and add every sound on purpose.
- **Lifeless or squashed characters.** Cats climb onto each other rather than being flattened, a fall happens in real time, fallen characters stay dizzy but alive, and background characters sit or stand still instead of sliding.
- **Revealing the payoff early.** Keep the character of the final shot out of every earlier shot.
- **A restyle pass over finished clips.** A video-to-video restyle turned night into day, added characters, and turned fire into solid shapes. Change the look in the stills, before animating.
