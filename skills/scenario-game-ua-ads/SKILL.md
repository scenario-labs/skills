---
name: scenario-game-ua-ads
description: "Use when making a finished 15 second mobile game user-acquisition (UA) video ad with Scenario from a one-line concept and invented gameplay: pin-pull rescue with a fail tease, number-gate crowd runner, satisfying sort, gacha summon, merge crisis story, or only-1%-can-solve puzzle. Also hook line, hand cursor, HUD counter, win burst, app icon end card, 9:16 game ads for studios. Not for ads from a real product photo or edits of existing footage."
license: MIT
---

# Scenario Game UA Ads

## Overview

A UA ad that plays like gameplay but is staged: Scenario generates the board art and the motion, and
every piece of game UI is composited on top. The user gives a concept ("a 15 second ad, rescue with
a fail tease"), not a shot list. The deliverable is the requested length at final render quality,
never a draft or a single clip. For ads from a real product photo, use `scenario-video-ads`; for
edits of existing footage, `scenario-ad-variants`. Connection, discovery, and recovery follow
`scenario`. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

Ask once: concept, game name (invent a fictional one when none is given), palette, length (default
15 seconds), spend ceiling. A supplied screenshot or style reference becomes a reference image for
the board still. Then run without stopping.

## Quick reference

| Stage       | What happens                                                                   | Sibling                                  |
| ----------- | ------------------------------------------------------------------------------ | ---------------------------------------- |
| 1. Timeline | Write the second-by-second plan ([concepts](references/concepts.md))           |                                          |
| 2. Board    | One text-free 9:16 still per mechanic, plus an app icon                        | `scenario-game-assets`, `scenario-image` |
| 3. Clips    | Two or more final-quality clips from the still, 5 to 10 s each                 | `scenario-video`, `scenario-seedance`    |
| 4. UI       | Hook, HUD, hand, bursts, end card ([ui](references/ui-layers.md))              | `scenario-text-overlay`                  |
| 5. Assemble | Clips and UI layers on one timeline, exact length                              | `scenario-video-assembly`                |
| 6. Sound    | Effects from the silent cut, music bed generated separately, mixed in assembly | `scenario-audio`                         |
| 7. Check    | Contact sheet at 2 fps, then the reject list below                             |                                          |

## Rules that carry the ad

- The deliverable is the length asked. Check it with a probe of the final file, never from the plan.
- A 15 second ad is three parts: a fail or setup take (about 5 s), a payoff take (about 6 s), and an
  end card (about 4 s). One 5 second clip is not an ad.
- The first frame holds the premise: board, hook line, and stakes. No logo intro.
- Never let a video or image model draw text, numbers, gate values, buttons, or the hand. Leave gate
  faces and badge slots blank in the still and composite them.
- One mechanic, one escalation. Counters only climb, in 4 or 5 visible steps.
- A fail tease is two clips from one still: the wrong move and its consequence, then the right move.
  Cut on a burst word.
- Prompt each clip as one locked camera. No push-in over a busy board: pipes, gates, and slots warp
  in the last seconds. Ask for a longer clip than needed and use only the clean first part.
- Render the clips at final quality. Draft tiers are for motion tests only.
- The game logic must hold, because players spot a cheat at once. Video models ignore barriers: lava
  and coins flow through a closed pin. So design the still with exactly one visible move per path
  and no second pin, gate, or wall the clip does not open.
- Prefer straight drops and straight lanes. Contents sitting right above their target fall in a line
  the model keeps; a pipe or a bend invites a shortcut outside it.
- When the payoff has a fixed end state, edit the board into that state with the same counts, then
  pin it as the clip's last frame. Pinning also locks the camera.
- Keep the top 15% of the still free of play pieces: the HUD and hook sit there.
- Name every barrier's state in the clip prompt ("the pipe opens straight into the chamber", "coins
  stay inside the glass") and what stays still.
- Look at the board still before animating: every chamber, gate, or card must read at phone size,
  and the puzzle must be solvable as drawn.
- Use the `compose-video` timeline model for assembly: it is Scenario's one deterministic
  compositor, so its id is fixed (`model_scenario-compose-video`; confirm with `search`).
- Sound is two jobs. Run a video-to-audio model on the silent cut for effects (its effect prompt is
  capped near 200 characters). Generate the music bed separately, with tempo, instruments, and a
  build-then-lift shape, banning ambient pads. Mix both in a final compose run, effects louder.
- End on the payoff, then a designed end card with the app icon, name, stars, and button.

## Worked example: rescue with a fail tease, 15 seconds, 9:16

1. Timeline: hook 0 to 3 s. Fail take 0 to 5.2 s, FAIL burst and red flash at 3.7 s. Payoff take 5.2
   to 11.1 s, NICE burst at 9 s. End card 11.1 to 15 s.
2. Board: `recommend` an image model for polished casual game art. Two glass shafts, text-free: lava
   above the trapped miner, gold above an empty cart, one pin as the floor of each top compartment.
   Edit it into the solved state (same gold amount in the cart, lava held, miner cheering). Also
   generate a square app icon of the hero.
3. Clips: `model_schema_get`, then two runs with `wait: false`, final tier. Fail take 5 s from the
   board: the left pin slides out at second 1, lava drops onto the miner. Payoff take 10 s, board as
   first frame and solved still as last: the right pin slides out, gold drops into the cart. State
   what stays still.
4. UI with `scenario-text-overlay`: hook, level badge, one counter pill per value, FAIL, NICE, red
   flash, end card. Measure pin ring positions on the still and place the hand there in two steps.
5. Assemble: clips at their `startTime`s with `fit: "cover"`, `mute: true`, payoff trimmed to the
   clean part. Overlays above, `durationMode: "custom"`, `duration: 15`. Run it silent first.
6. Sound as the rules say, one final compose run, then probe length and levels.
7. Check: before assembling, extract full-resolution frames every 0.5 s around each clip's action
   and inspect crops at 540 px or wider for logic. After assembling, sweep at 2 fps into one contact
   sheet for timing and overlays. Apply the reject list.

## Reject list

- Anything passing through a closed pin, gate, wall, glass, or floor, or leaving its container. A
  small contact sheet hides this: judge it on full-resolution crops.
- An action that does not follow from the move the hand shows, or a HUD count that contradicts what
  is visible.
- Hook, badge, and counter overlap, or any text under 6% of frame height.
- A black frame at a cut: the end card starts exactly when the last clip ends, with no fade.
- The board shifting between takes, or pipes and slots warping near a clip's end: trim earlier.
- A hand off its target, or a number that does not climb.
- Missing audio, a flat bed, or silence over the payoff. Check levels and a spectrogram, never the
  auto-caption.

## Common mistakes

- Calling a 5 or 10 second render a 15 second ad: probe the file.
- Prompting "with the number 10 on the gate": the number changes every frame. Blank gate, overlay.
- A label fixed to a moving object slides off it. Keep it to the static second or use the HUD.
- Scaling a full-canvas overlay in the compose run: it scales from the corner and can leave the
  frame. Render the element at final size. Offsetting a layer with `x` or `y` is fine.
- Leaving clip audio on: the bed is built in assembly, so mute clips or turn generated audio off.
- Cropping a 16:9 ad to 9:16: compose the board natively for each ratio.
- Naming a real game, studio, or character in invented gameplay.
