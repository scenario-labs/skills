---
name: scenario-seedance-storyboard
description: "Use when a Seedance video must hold continuous movement across shots: dance choreography, fights, sports, or any performance where limbs teleport, feet slide, or motion resets at every cut, or when turning a storyboard and character sheet into a multi-shot sequence that plays as one take. Keywords: storyboard to video, choreography, movement control, pose chain, timecoded shot script, first and last frame chaining, character sheet, multi-shot continuity, Seedance 2.5 and 2.0."
license: MIT
---

# Scenario Seedance Storyboard

## Overview

Prompted shot by shot, generated movement falls apart: limbs teleport, feet slide, and every cut resets the performance. So storyboard instead of prompting harder. Write a timecoded shot script, draw a character sheet and a numbered panel per shot with an image model, and hold one rule: every shot ends in the pose the next one starts from. Pinned boundaries leave nothing to reset: the cuts play as one continuous performance. Dance is the stress test: what holds choreography holds any movement.

Connection and the core loop: the `scenario` skill; the Seedance parameter contract, conditioning traps, and sound lanes: the `scenario-seedance` skill; identity across stills: the `scenario-consistency` skill; splitting and rejoining shots: the `scenario-video-editing` and `scenario-video-assembly` skills. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step               | What                                | How                                                                        |
| ------------------ | ----------------------------------- | -------------------------------------------------------------------------- |
| 1. Script          | timecoded shot list                 | per shot: number, framing (WS, MS, CU), action verbs, entry and exit poses |
| 2. Character sheet | one performer, several angles       | image model via `search`                                                   |
| 3. Boards          | numbered panels, or boundary stills | image model, character sheet as reference, delivery aspect ratio           |
| 4. Video           | one scripted run, or chained runs   | Seedance `model_run`, one of the two lanes below                           |
| 5. Check           | the frames at every cut agree       | `asset_display`, compare each boundary to its panel                        |

Write the script the way boards are drawn: a few verbs per shot ("Strut in. Pose. Attitude."), one camera idea, both edge poses named. Adjacent shots share an edge by construction: shot 3's exit is shot 4's entry. That rule is the whole trick, so state it in the script and draw it into the panels.

## Two lanes

**One scripted run.** When the sequence fits one job's duration cap (30 seconds on 2.5 at authoring time; read it off `model_schema_get`), pass the character sheet and board as `referenceImages` and the script as the prompt: "@image1 is the character sheet, the same dancer throughout. @image2 is the storyboard, play panels 1 to 12 in order; every shot ends in the pose the next begins. 0:00-0:02 WS, strut in, ends weight left, arm hooked overhead. 0:02-0:04 MS, hip sway, begins arm hooked overhead...". One generation carries the internal cuts: references hold identity, the pose chain holds continuity. Reference mode anchors frame one to the base state of the reference world (see `scenario-seedance`), so a sequence that must open on an exact pose belongs in the chained lane.

**Chained per-shot runs.** For longer sequences or per-shot control, make the chain literal. Render each boundary pose as a still, then run each shot in first and last frame mode: shot N takes `image` = boundary still N-1 and `lastFrameImage` = boundary still N. Adjacent shots share the still, so every cut lands on a frame both sides agree on. This mode excludes `referenceImages` (mutually exclusive), so the stills themselves carry identity: that is what the character sheet bought. When a delivered ending beats the drawn one, extract that last frame (`search` with `target="models"`, query `"image sequence"` surfaces a frame-extraction model) into the next shot's `image`. Score once over the assembled cut, never per shot: the sound lanes are in `scenario-seedance`.

## Worked example: a 12-shot dance in one run

1. Write the script: 12 shots over 24 seconds, edge poses named, every exit matching the next entry. Show it to the user first; it is the cheapest place to be wrong; unattended, write it down and continue.
2. Generate the character sheet with an image model (via `search`), then the numbered 12-panel board with the sheet as reference so every panel is the same performer. Upload anything local with `upload_asset` (see the `scenario` skill).
3. `search` with `target="models"`, `query="seedance"`, `public=true`; prefer the newest non-deprecated hit, e.g. `model_bytedance-seedance-2-5` (a live hit at authoring time: re-discover each session), then `model_schema_get` for caps and defaults.
4. `model_run` with `dry_run=true` and `parameters={"prompt": "<the timecoded script>", "referenceImages": ["asset_sheet", "asset_board"], "duration": 24, "resolution": "720p"}` for the estimate; re-estimate after any change.
5. Re-run with `wait=false`, then `jobs_wait` with the job id, re-called with `pending_job_ids` on timeout. A timeout is not a failure and never justifies a second `model_run`.
6. `asset_display` and step through every cut: both sides must agree in pose and match the panel. Repair a broken shot in the chained lane: render its two boundary stills (as that lane teaches), split the master at the shot's timecodes, regenerate the shot between them, rejoin (`scenario-video-editing`, `scenario-video-assembly`).

## Common mistakes

- Prompting choreography as adjectives ("dances energetically"): timecoded verbs and edge poses survive generation; mood words do not.
- Breaking the chain once: one mismatched pair of edge poses reintroduces the reset the storyboard exists to remove.
- Passing `referenceImages` alongside `image`: mutually exclusive; in the chained lane the boundary stills must carry identity themselves.
- Expecting a scripted run to open on a prompt-described pose: reference mode anchors frame one to the base state; exact openings are the chained lane's job.
- A script past the prompt's `max_length`, or timecodes past the duration cap: read both off `model_schema_get`; an overrun is a 400, never a trim.
- Boards drawn at a different aspect ratio from delivery: the reframe moves the poses the chain depends on.
