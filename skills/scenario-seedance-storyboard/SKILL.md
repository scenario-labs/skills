---
name: scenario-seedance-storyboard
description: "Use when a Seedance video must hold continuous movement across shots: dance choreography, fights, sports, or any performance where limbs teleport, feet slide, or motion resets at every cut, or when turning a storyboard and character sheet into a multi-shot sequence that plays as one take. Keywords: storyboard to video, choreography, movement control, pose chain, timecoded shot script, first and last frame chaining, character sheet, multi-shot continuity, Seedance 2.5 and 2.0."
license: MIT
---

# Scenario Seedance Storyboard

## Overview

Prompted shot by shot, generated movement falls apart: limbs teleport, feet slide, and every cut resets the performance. So storyboard instead of prompting harder. Write a timecoded shot script, draw a character sheet and a numbered panel per shot, and hold one rule: every shot ends in the pose the next one starts from. Pinned boundaries leave nothing to reset: the cuts play as one continuous performance. Dance is the stress test: what holds choreography holds any movement.

Connection and the core loop: the `scenario` skill; the Seedance parameter contract, conditioning traps, and sound lanes: the `scenario-seedance` skill; identity across stills: the `scenario-consistency` skill; splitting and rejoining shots: the `scenario-video-editing` and `scenario-video-assembly` skills. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step               | What                              | How                                                                        |
| ------------------ | --------------------------------- | -------------------------------------------------------------------------- |
| 1. Script          | timecoded shot list               | per shot: number, framing (WS, MS, CU), action verbs, entry and exit poses |
| 2. Character sheet | the cast, several angles          | image model via `search`; one clean still of a real performer also works   |
| 3. Boards          | drawn numbered panels             | same model, sheet as reference, each panel at the delivery ratio           |
| 4. Video           | one scripted run, or chained runs | Seedance `model_run`, one of the two lanes below                           |
| 5. Check           | the frames at every cut agree     | extract the boundary frames (step 6), compare each to its panel            |

Keep each shot to a few verbs ("Strut in. Pose. Attitude.") and one camera idea. Adjacent shots share an edge by construction: shot 3's exit is shot 4's entry, stated in the script and drawn into the panels.

Draw the panels as line art, not photoreal frames: a drawn panel reads as blocking to follow, a photoreal one reads as footage to match, down to a number badge burned into the corner for the whole clip. So number the panels under each frame, never inside it, and do not rely on a negative clause to suppress a badge you drew in frame. The sheet can stay photographic while the board is drawn. Pick the board model for legible in-image text, strict grid adherence, and `referenceImages` input so panels lock to the sheet; shortlist with `search`, since `recommend` can answer this step with style LoRAs.

## Two lanes

**One scripted run.** When the sequence fits one job's duration cap (30 seconds on 2.5 at authoring time; read it off `model_schema_get`), pass the character sheet and board as `referenceImages` and the script as the prompt: "@image1 is the character sheet, the same dancer throughout. @image2 is the storyboard, play panels 1 to 12 in order; every shot ends in the pose the next begins. 0:00-0:02 WS, strut in, ends weight left, arm hooked overhead. 0:02-0:04 MS, hip sway, begins arm hooked overhead...". One generation carries the internal cuts: references hold identity, the pose chain holds continuity. Pass `aspectRatio`, which defaults to `adaptive` and is honored here, or a portrait board hands back a portrait video. Reference mode anchors frame one to the base state of the reference world (see `scenario-seedance`), so a sequence that must open on an exact pose belongs in the chained lane.

**Chained per-shot runs.** For longer sequences or per-shot control, make the chain literal. Draw the board first even here, it is the cheap place to catch a broken chain, then render each boundary pose as a still and run each shot in first and last frame mode: shot N takes `image` = boundary still N-1 and `lastFrameImage` = boundary still N. Adjacent shots share the still, so every cut lands on a frame both sides agree on. This mode excludes `referenceImages` (mutually exclusive), so the stills are the only identity a shot gets, and the sheet makes each one plausible alone, not identical to the next. Vary only the pose clause of one baseline prompt (`scenario-consistency`), pin which side of frame each character holds (a named pose is not a named position: a mirrored still asks two fighters to swap sides mid-shot), and keep the framing static, because a traveling camera cannot land on a boundary drawn from the anchor framing. Review the set together before spending a video run: costume detail drifts still to still (a mask, a crest, a metal finish) and every drift lands on a cut. Regenerate the still, not the shot. N shots cost N+1 stills and N runs. When a delivered ending beats the drawn one, pass that clip's `lastFrame` asset id (from `asset_get`) as the next shot's `image`. Score once over the assembled cut, never per shot: the sound lanes are in `scenario-seedance`.

## Worked example: a 12-shot dance in one run

1. Write the script: 12 shots over 24 seconds, edge poses named, every exit matching the next entry. Show it to the user first; it is the cheapest place to be wrong; unattended, write it down and continue.
2. Generate the character sheet with an image model, then the numbered 12-panel board with the sheet as reference so every panel is the same performer. A board is a large canvas: a size inside the schema's per-axis limits can still hit an unstated total-pixel ceiling, so read the error hint and step down. Upload anything local with `upload_asset` (see the `scenario` skill).
3. `search` with `target="models"`, `query="seedance"`, `public=true`. Hits rank by relevance, not generation, so scan them all for the newest non-deprecated member rather than taking the first: at authoring time `model_bytedance-seedance-2-5` (re-discover each session), which takes the most references in the family and holds identity best. Then `model_schema_get` for caps and defaults.
4. `model_run` with `dry_run=true` and `parameters={"prompt": "<the timecoded script>", "referenceImages": ["asset_sheet", "asset_board"], "duration": 24, "resolution": "720p", "aspectRatio": "16:9"}` for the estimate; re-estimate after any change.
5. Re-run with `wait=false`, then `jobs_wait` with the job id, re-called with `pending_job_ids` on timeout. A timeout is not a failure and never justifies a second `model_run`.
6. Step through every cut: both sides must agree in pose and match the panel, and the corners must be clean of leaked panel numbers. `asset_display` hands back a link for video, not frames. In the chained lane the frames are free: `asset_get` returns each clip's `firstFrame` and `lastFrame` as asset ids, one pair per join. In one scripted run the cuts sit where the model put them, so detect them and pull those frames locally, or with a frame-extraction model (`search`, query `"image sequence"`) when there is no local tool or the frames must return as assets.
7. Repair a broken shot in the chained lane: render its two boundary stills, split the master at its timecodes, regenerate between them, rejoin (`scenario-video-editing`, `scenario-video-assembly`).

## Common mistakes

- Prompting choreography as adjectives ("dances energetically"): timecoded verbs and edge poses survive generation; mood words do not.
- Breaking the chain once: one mismatched pair of edge poses reintroduces the reset the storyboard exists to remove.
- Naming the pose but not the position: in a two-character scene a mirrored boundary still breaks the cut as hard as a wrong limb.
- Trusting the sheet to hold costume detail across separately generated stills: review the set together, and fix the still rather than the delivered shot.
- Passing `referenceImages` alongside `image`: mutually exclusive; in the chained lane the boundary stills must carry identity themselves.
- Expecting a scripted run to open on a prompt-described pose: reference mode anchors frame one to the base state; exact openings are the chained lane's job.
- A script past the prompt's `max_length`, or timecodes past the duration cap: read both off `model_schema_get`; an overrun is a 400, never a trim.
- Panels drawn at a different ratio from delivery: the reframe moves the poses the chain depends on. The grid's shape is free, each panel's is not.
