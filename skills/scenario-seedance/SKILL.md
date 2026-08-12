---
name: scenario-seedance
description: "Use when generating or editing video with Seedance models on Scenario via MCP: text-to-video, image-to-video from a first frame, first and last frame anchors, reference-to-video with identity, product, or world references, prompt-based video editing, extending a clip, audio-conditioned motion, or deciding between first-frame and reference conditioning. Keywords: Seedance 2.5, ByteDance, T2V, I2V, V2V, multimodal references, video extension."
license: MIT
---

# Scenario Seedance Video

## Overview

Seedance, ByteDance's video family on Scenario, folds text-to-video, first/last frame, reference-to-video, editing, and extension into one model that infers the mode from your inputs and prompt, so the conditioning inputs you pass decide more than prompt wording does. Discover it with `search` and treat `model_schema_get` as the contract: the family evolves and availability differs per team.

Connection and the core generation loop: see the `scenario` skill in this repo. Model-agnostic video work: see the `scenario-video` skill in this repo.

## Quick reference

Mode follows from the inputs (names from the live schema):

| Mode         | Inputs                              | Behavior                                           |
| ------------ | ----------------------------------- | -------------------------------------------------- |
| Text         | `prompt`                            | `aspectRatio` honored (21:9 through 9:16)          |
| First frame  | `image` (+ `prompt`)                | opens on that frame; `aspectRatio` ignored         |
| First + last | `image` + `lastFrameImage`          | `lastFrameImage` is only valid alongside `image`   |
| Reference    | `referenceImages` (up to 30)        | carries identity and world, not the opening state  |
| Edit         | `referenceVideos` + edit prompt     | requires `duration: -1`; output follows the source |
| Extend       | `referenceVideos` + boundary prompt | continues the clip; geometry follows the source    |

`image` and the reference arrays are mutually exclusive. `referenceVideos` (up to 10) and `referenceAudio` (up to 10, timing and energy conditioning) combine with `referenceImages`. Reference parameters are arrays even for one asset. Prompt tags bind by array order: `@image1` is `referenceImages[0]`; likewise `@video1`, `@audio1`. Duration: 4 to 30 seconds or -1 auto (the longest reference clip's length). Resolution: `480p` or `720p`. `generateAudio` defaults to true. No seed, mask, or camera parameter exists: camera moves live in the prompt, one dominant move per shot.

## The conditioning rule

In reference mode, frame one anchors to the base state of the reference world, and no prompt wording overrides it. If the shot must open in a specific state, render a still of it and pass it as `image`; use `referenceImages` when only identity, world, and palette matter. Deciding this per shot before generating is worth more than any prompt tuning.

## Worked example: a product shot from references

1. `search` with `target="models"`, `query="seedance"`, `public=true`. Prefer the newest non-deprecated hit, e.g. `model_bytedance-seedance-2-5` (a live hit at authoring time: re-discover each session).
2. `model_schema_get` with that id: confirm fields, caps, and defaults first.
3. `upload_asset` the product stills (see the `scenario` skill) to get asset ids.
4. `model_run` with that `model_id`, `dry_run=true`, and the exact `parameters={"prompt": "@image1 defines the bottle and label. Slow dolly-in as condensation beads. No text, no captions.", "referenceImages": ["asset_a", "asset_b"], "duration": 8, "resolution": "720p", "generateAudio": false}}` for the cost estimate; re-estimate after any change to duration, resolution, or references.
5. Repeat `model_run` with `wait=false`, then `jobs_wait` with the returned job id, re-called with `pending_job_ids` on timeout. A timeout is not a failure and never justifies a second `model_run`.
6. `asset_display` the output. For a file, take the URL from `asset_get` and fetch it with `curl -L` (`asset_download` converts image formats only).

## Common mistakes

- Prompting an opening state in reference mode: it will not appear; pass it as `image`.
- A bare string where the schema says array: one reference still goes as `["asset_x"]`.
- Combining `image` with `referenceImages` or `referenceVideos`: mutually exclusive inputs.
- Edit mode with a fixed duration: editing requires `duration: -1`.
- Setting `aspectRatio` in first-frame, edit, or extend modes: ignored; geometry follows the input.
- Leaving `generateAudio` at its default (true) when the soundtrack comes later.
- Rendering captions, prices, logos, or UI: reserve clean space and composite text in post.
