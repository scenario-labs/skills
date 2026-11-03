---
name: scenario-game-ua-ads
description: "Use when making a short mobile game user-acquisition (UA) video ad with Scenario from a one-line concept and invented gameplay: pin-pull rescue with a fail tease, number-gate crowd runner, satisfying sort, gacha summon, merge crisis story, or only-1%-can-solve puzzle. Also hook line, hand cursor, combo badge, counter, win burst, end card, 9:16 game ads for studios. Not for ads from a real product photo or edits of existing footage."
license: MIT
---

# Scenario Game UA Ads

## Overview

A UA ad that plays like gameplay but is staged: Scenario generates the board art and the motion, and
every piece of game UI is composited on top. The user gives a concept ("a 15 second ad, rescue with
a fail tease"), not a shot list. For ads from a real product photo, use `scenario-video-ads`; for
edits of existing footage, `scenario-ad-variants`. Connection, discovery, and recovery follow
`scenario`. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

Ask once: concept, game name (invent a fictional one when none is given), palette, length (6 to 15
seconds), spend ceiling. A supplied screenshot or style reference becomes a reference image for the
board still. Then run without stopping.

## Quick reference

| Stage       | What happens                                                                   | Sibling                                  |
| ----------- | ------------------------------------------------------------------------------ | ---------------------------------------- |
| 1. Beats    | Pick the concept, write timed beats ([concepts](references/concepts.md))       |                                          |
| 2. Board    | One text-free 9:16 still per mechanic, `recommend` for the model               | `scenario-game-assets`, `scenario-image` |
| 3. Clips    | One image-to-video clip per beat, all from the approved still                  | `scenario-video`, `scenario-seedance`    |
| 4. UI       | Hook, bursts, badges, counters, hand, end card ([ui](references/ui-layers.md)) | `scenario-text-overlay`                  |
| 5. Assemble | Clips and UI layers on one timeline                                            | `scenario-video-assembly`                |
| 6. Sound    | Bed on the cut, one tactile effect per beat, no baked-in clip audio            | `scenario-audio`                         |
| 7. Check    | Contact sheet of the master at 2 fps                                           |                                          |

## Rules that carry the ad

- The first frame holds the premise: board, hook line, and stakes at t=0. No logo intro.
- Never let a video or image model draw text, numbers, gate values, buttons, or the hand. They drift
  between frames. Leave gate faces and badge slots blank in the still and composite them.
- One mechanic, one escalation. Counters and combo badges only climb.
- A fail tease is two clips from one still: the wrong move and its consequence, then the right move.
  Cut between them on a burst word.
- Prompt each clip as one locked camera and one action sequence. A tracking shot is fine when the UI
  is HUD only.
- Test motion at low cost first: a draft or lower-resolution tier, then final quality for the
  approved take. Image-to-video follows the first frame's shape, so the still must already be 9:16.
- Use the `compose-video` timeline model for assembly: it is Scenario's one deterministic
  compositor, so its id is fixed (`model_scenario-compose-video`; confirm with `search`).
- Sound is two jobs. Run a video-to-audio model on the silent assembled cut for effects timed to the
  action. Generate the music bed separately: that model's music prompt returned faint ambience.
- Prompt the bed with tempo, instruments, and a build-then-lift shape, and ban ambient pads and
  nature sounds. Mix both in the compose run (effects louder than the bed) and check levels and a
  spectrogram, never the auto-caption.
- End on a payoff frame, then the end card for the last 1.5 seconds.

## Worked example: rescue with a fail tease, 10 seconds, 9:16

1. Beats: hook line 0 to 2.5 s, fail take 0 to 5 s, FAIL burst at 4 s, win take 5 to 10 s, NICE
   burst at 8 s, end card 8.5 to 10 s.
2. `recommend` an image model for polished casual game art. Generate the board natively at the
   delivery ratio, text-free: stone wall, four chambers (lava, gold, trapped miner, empty bin), pins
   and pipes. Look at it before animating: the chambers must read at phone size.
3. `model_schema_get` on the video model, then run two clips from the same still with `wait: false`.
   Fail take: "Locked camera. The top-left pin slides out, lava pours down the pipe and floods the
   miner's chamber." Win take: the other pin slides out and gold fills the bin. State what stays
   still.
4. Render UI with `scenario-text-overlay`: hook line, FAIL, NICE, hand, end card. Upload each.
5. `model_run` on the compose model: both clips on the timeline at their `startTime`s with
   `fit: "cover"` to the canvas, overlays above (higher `zIndex`) with `transitionIn: "zoomin"` on
   the bursts and `fadeOut` on the hook line.
6. Add sound as the rules say, then sweep the master at 2 fps into a contact sheet: text verbatim,
   hand on target, no drift between the two takes' boards.

## Common mistakes

- Prompting "with the number 10 on the gate": the number changes every frame. Blank gate, overlay.
- Fixing a label to a moving object: it slides off. Keep it to the static second or use the HUD.
- Scaling a full-canvas overlay in the compose run: everything on it scales from the corner and can
  leave the frame. Render the element at its final size instead.
- Two escalations in one ad: pick one counter or one badge chain.
- One long clip at the model's maximum length: generate 4 to 5 second beats and cut to rhythm.
- Leaving clip audio on: the bed is built in assembly, so turn generated audio off where the schema
  offers it.
- Cropping a 16:9 ad to 9:16: compose the board natively for each ratio.
- Naming a real game, studio, or character in invented gameplay.
