---
name: scenario-game-ua-ads
description: "Use when making a finished mobile game user-acquisition (UA) video ad with Scenario at an exact length for TikTok, Reels, Stories, Meta feed, YouTube Shorts, or ad networks: from a one-line concept or the game's own screenshots, screen recording, gameplay video, characters, icon, or UI kit. Pin-pull, parking jam, match-3, swallow hole, evolution runner, stacker, draw to protect, odd one out, gacha, merge. Also hook, hand, HUD counter, end card. Not for ads from a product photo."
license: MIT
---

# Scenario Game UA Ads

## Overview

A UA ad that plays like gameplay: Scenario generates or adapts the board art and the motion, and
every piece of game UI is composited on top. The user gives a concept and a placement, not a shot
list. The deliverable is the requested length and format at final render quality, never a draft or a
single clip. The test of every beat: a stranger who has never heard of the game thinks "I really
want to try this". For ads from a product photo, use `scenario-video-ads`; for hook, CTA, or
end-card variants of a finished ad, `scenario-ad-variants`. Connection, discovery, and recovery
follow `scenario`. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

## Brief: ask once, then run

Ask in one round, then run without stopping:

- **Concept** or the game's core loop, and the **game name**. Invent a fictional name when none is
  given.
- **Platform and placement**. They fix the ratio, safe zones, recommended length, and sound
  ([platforms](references/platforms.md)).
- **Exact length** in seconds. Without one, use the placement's recommended UA length.
- **The game's own material**, all optional ([inputs](references/inputs.md)): screenshots, a screen
  recording or gameplay video, characters and items, the app icon, logo, or UI kit.
- Palette and spend ceiling.

With the game's own material, the ad must look and play like that game: boards built from its
screenshots, its characters on-model, its real icon on the end card. Invent gameplay only when the
user has none to give.

## Quick reference

| Stage       | What happens                                                                      | Sibling                                  |
| ----------- | --------------------------------------------------------------------------------- | ---------------------------------------- |
| 1. Plan     | Ratio, safe zones, second-by-second timeline ([concepts](references/concepts.md)) |                                          |
| 2. Board    | One text-free still per mechanic at the delivery ratio, from the user's material  | `scenario-game-assets`, `scenario-image` |
| 3. Clips    | Final-quality takes from the still, or cuts of the user's footage                 | `scenario-video`, `scenario-seedance`    |
| 4. Logic    | Full-resolution frames around every action, before any assembly                   |                                          |
| 5. UI       | Hook, HUD, hand, bursts, effects, end card ([ui](references/ui-layers.md))        | `scenario-text-overlay`                  |
| 6. Assemble | One timeline at the exact length and canvas                                       | `scenario-video-assembly`                |
| 7. Sound    | A hit on every event, a separate music bed, mixed in assembly                     | `scenario-audio`                         |
| 8. Check    | Probe, levels, a 2 fps sheet, then the reject list                                |                                          |

## Length and format

| Length | Setup or fail              | Payoff                     | End card |
| ------ | -------------------------- | -------------------------- | -------- |
| 6 s    | none, hook over payoff     | 4.5 s                      | 1.5 s    |
| 10 s   | 3.5 s                      | 4.5 s                      | 2 s      |
| 15 s   | 5 s                        | 6 s                        | 4 s      |
| 20 s   | 5 s                        | 6 s, then a 5 s escalation | 4 s      |
| 30 s   | two rounds of fail and win | or three escalations       | 4 s      |

From the user's footage, setup and payoff become the footage's own beats
([inputs](references/inputs.md)).

- Compose each ratio natively: generate the board at the delivery canvas (1080x1920 for 9:16,
  1080x1350 for 4:5, 1080x1080 for 1:1, 1920x1080 for 16:9). Never crop one ratio out of another.
- Plan the board still in the placement's bands: background only under the platform UI, the HUD and
  hook just below it, every key action in the safe middle. Overlays with text stay in the safe zone
  too.
- Several placements: one board per ratio and one assembly run each, from the same plan.

## Make the viewer want to play

A board that changes correctly sells nothing. Plan every concept around its fantasy (power,
cleverness, order, growth, rescue) and its **Fun** line in [concepts](references/concepts.md):

- The input reads within 2 s: the hand and the piece move together, and the game answers at once.
- Every input gets a satisfying reaction in the motion itself: anticipation, contact, reaction. A
  piece wobbles on an edge, tips, then drops with a spin; a stack sways and settles. Write it beat
  by beat in the clip prompt.
- Show a limit, then overcome it: a too-big object rattles across the rim until the hole grows.
- Escalate: each beat bigger or faster than the last, a near-fail, one clever move nobody expected,
  then the biggest moment near the end of gameplay.
- Never simplify the mechanic until the model cannot break it. Build a rich one in chained stages:
  one state still per step, each edited from the last, each take pinned from one state to the next
  with one visible move. Or script it from cut pieces (below).

## Rules that carry the ad

- Probe the final file for length and canvas, never trust the plan.
- The first frame holds the premise: board, hook line, stakes. A sound at 0.0, motion by 0.3 s, no
  logo intro.
- Never let a model draw text, numbers, gate values, buttons, or the hand. Leave slots blank in the
  still and composite them.
- One mechanic, escalating. Counters only climb, in 4 or 5 visible steps, each proportional to the
  event that causes it: one pickup never jumps a level from 30 to 99.
- A fail tease is two takes from one still: the wrong move and its consequence, then the right move.
  Cut on a burst word.
- One locked camera per take, at final quality. No push-in over a busy board: pipes, gates, and
  slots warp. Ask for a longer take and keep the clean first part.
- The game logic must hold, because players spot a cheat at once:
  - Video models ignore barriers: lava and coins flow through a closed pin. Design one visible move
    per path, with no pin, gate, or wall the take does not open.
  - Prefer straight drops and straight lanes. A pipe or a bend invites a shortcut outside it.
  - Every player move needs a reason on the board: a swipe reaches a collectible or dodges a hazard.
    Collectibles in one line make the swipe pointless.
  - Name every barrier's state in the prompt ("coins stay inside the glass") and what stays still.
  - A fixed end state is its own still, edited from the board with the same counts, pinned as the
    take's last frame. Pinning also locks the camera.
  - A precise move a model cannot do cleanly (a two-piece swap) is built as layers from the still;
    the model animates only the consequence.
  - A board whose every move must be exact (tile match, sort, merge, screw puzzle) is scripted
    whole: cut the pieces from the board still or the user's screenshot and animate them as layers.
    The rules stay exact, and a video model adds only ambient motion behind them.
- Assembly runs on `model_scenario-compose-video`, Scenario's one deterministic compositor, so its
  id is fixed (confirm with `search`).
- Anything that moves on the UI layer (the hand, the counter pop, rewards flying to the counter, a
  burst) is one transparent ProRes 4444 `.mov`, cropped to its motion box. Never use a run of
  stepped image layers, which compose can show two at a time, and never WebM alpha, which comes out
  black ([ui](references/ui-layers.md)).
- Sound: a hit on every visible event (tap, impact, pickup, counter step) on its frame, louder than
  the music. A video-to-audio pass on the silent cut adds incidental sound but misses events; its
  effect prompt is capped near 200 characters. Generate the bed separately, banning ambient pads,
  and shift it so its lift lands on the payoff.
- Compose takes at most 50 layers and has no limiter, so assembly runs in passes:
  - picture: clips and overlays, muted, into a silent master;
  - sound: the silent master as the one video layer under every audio layer, times to the
    millisecond;
  - loudness, only when the sound pass misses -16 to -14 LUFS or peaks above -1 dBTP:
    `model_scenario-audio-extract` with `normalizeLoudness: true`, then the silent master plus that
    one track. Scenario ships one tool for each of these jobs, so the ids are fixed.
- End on the payoff, then a living end card: the icon pops, the hero bounces in, stars twinkle. The
  call to action follows the placement: a label on social feeds, which ban fake buttons, and a
  button only on clickable ad-network cards.

## Scripts

The agent runs these locally with Python 3, Pillow, numpy, and ffmpeg. They render and plan; uploads
and compose runs stay MCP calls. Each takes a JSON spec; `--help` lists its fields.

- [render_tracks.py](scripts/render_tracks.py): renders the hand, counter pops, progress bar,
  floaters, reward flights, bursts, win stars, icon pop, bounce-in, and label pulse as cropped
  ProRes 4444 tracks, plus `layers.json` with floored times and safe-zone warnings.
- [build_passes.py](scripts/build_passes.py): `simulate` sums the cue sheet locally and prints
  loudness, true peak, and each hit's margin; `picture` and `sound` write the two compose payloads.
- [check_master.py](scripts/check_master.py): run on the downloaded master: canvas, length,
  loudness, true peak, levels per section, a 2 fps sheet, and each hit's onset.
- [make_patch.py](scripts/make_patch.py): builds a clean-plate image layer that hides a static piece
  contradicting the count, and checks every take it covers.

## Worked example: rescue with a fail tease, 15 seconds, TikTok 9:16

1. Plan: 1080x1920, TikTok safe zone: shafts in the middle band, HUD from y 280. Hook 0 to 3 s. Fail
   take 0 to 5.2 s, FAIL burst and red flash at 3.7 s. Payoff take 5.2 to 11.1 s, NICE at 9 s. End
   card 11.1 to 15 s.
2. Board: `recommend` an image model for polished casual game art. Two glass shafts, text-free: lava
   above the trapped miner, gold above an empty cart, one pin as the floor of each top compartment.
   Edit it into the solved state (same gold in the cart, lava held, miner cheering). A square app
   icon of the hero.
3. Clips: `model_schema_get`, then two runs with `wait: false`, final tier. Fail take 5 s from the
   board: the left pin slides out, lava drops onto the miner. Payoff take 10 s, board as first
   frame, solved still as last: the right pin slides out, gold drops into the cart.
4. Logic: frames every 0.25 s around each pin pull, crops at 540 px or wider. Nothing passes the
   other pin or the glass, and the gold in the cart matches the gold that fell.
5. UI with `scenario-text-overlay`: hook, level badge, counter values, FAIL, NICE, red flash, end
   card with a "PLAY FREE" label. `render_tracks.py` renders the hand following the pin ring and a
   coin flight to the counter on each step.
6. Picture pass: `build_passes.py picture` lays the clips at their `startTime`s, `fit: "cover"`,
   `mute: true`, overlays above, `durationMode: "custom"`, `duration: 15`.
7. Sound pass on the silent master: hits on the pin pulls, the lava, the coins, each counter step,
   and the end card; the video-to-audio pass under them; the bed with its lift at 5.2 s. Run
   `simulate` first and trim until the peak sits under -1 dBTP.
8. Check: `check_master.py`, then the reject list on full-resolution frames.

## Reject list

- A beat where the board changes with no readable player input, or an input with no satisfying
  reaction: correct, but nobody wants to play it.
- Anything passing through a closed pin, gate, wall, glass, or floor, or leaving its container. A
  small contact sheet hides this: judge it on full-resolution crops.
- A hand gesture with no matching action, an action with no gesture, or a count that contradicts the
  screen.
- A win that leaves a piece on the board ("cleared" with one car still parked), even half under the
  HUD.
- A timer or meter that runs faster than real seconds.
- A character or item off-model against the user's assets, or a board that no longer matches their
  screenshots.
- UI outside the placement's safe zone, overlapping elements, or HUD digits under 72 px on 1080
  wide.
- A black frame at a cut: the end card starts exactly when the last clip ends, with no fade.
- The board shifting between takes, or pieces warping near a take's end: trim earlier.
- An event with no hit, a hit more than 0.1 s off its frame, a quiet first second, or a peak above
  -1 dBTP.
- A counter step, reward, burst, or star with no event on screen to cause it.

## Common mistakes

- Calling a 5 or 10 second render a 15 second ad: probe the file.
- Prompting "with the number 10 on the gate": the number changes every frame. Blank gate, overlay.
- A label fixed to a moving object slides off it. Keep it to the static second or use the HUD.
- Scaling a full-canvas overlay in the compose run: it scales from the corner and can leave the
  frame. Render each element at final size; offsetting with `x` or `y` is fine.
- Leaving clip audio on: mute clips or turn generated audio off.
- Cropping a 16:9 ad to 9:16, or stretching a screenshot to the canvas.
- Naming a real game, studio, or character in invented gameplay.
