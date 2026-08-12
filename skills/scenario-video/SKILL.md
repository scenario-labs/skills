---
name: scenario-video
description: "Use when generating or editing video on Scenario via MCP: text-to-video, image-to-video (animating a still, first/last frame anchors), motion prompt iteration, lipsync and talking avatars, video upscale to 4K, prompt-based video editing, trim, split, concat, reframe, resize, extend, frame extraction, background removal, or waiting on long video jobs. Keywords: txt2video, img2video, video2video, I2V, T2V, V2V, ads, film previz, game cinematics, social clips."
license: MIT
---

# Scenario Video Generation and Editing

## Overview

Scenario exposes a large video catalog through one MCP loop: text-to-video and image-to-video generators (Kling, Veo, Seedance, LTX, Luma, Runway, Grok) plus video-to-video editors, lipsync, upscalers, and deterministic cut/split/concat tools. Video jobs run long, so launch with `wait=false` and block on `jobs_wait` instead of polling.

Connection and the core generation loop: see the `scenario` skill in this repo.

## Quick reference

| Step           | Tool                          | Notes                                                                                                      |
| -------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Find a model   | `search`                      | `target="models"`, `public=true`, query `"image to video"`, `"video upscale"`, `"lipsync"`, `"video edit"` |
| Inspect inputs | `model_schema_get`            | Always before `model_run`; video schemas differ widely (duration, aspect ratio, frame anchors)             |
| Upload source  | `upload_asset`                | A local still or clip becomes an `asset_id`; never pass file paths                                         |
| Refine prompt  | `prompt_spark`                | Optional; rewrites a thin motion idea into an on-model prompt                                              |
| Generate       | `model_run`                   | `wait=false` for video; `dry_run=true` to estimate cost first                                              |
| Wait           | `jobs_wait`                   | Re-call with the returned `pending_job_ids` until done                                                     |
| Review         | `asset_display` / `asset_get` | Display inline; save video from the `asset_get` URL with `curl -L`                                         |

## Worked example: animate a key art still into a short ad clip

1. `search` with `target="models"`, `query="image to video"`, `public=true`. Live hits include `model_kling-v2-6-i2v-pro` and `model_veo3-1-fast`; re-discover rather than hardcoding, availability shifts per team.
2. `model_schema_get` with `model_id="model_kling-v2-6-i2v-pro"`. Note the image field, duration options, and any last-frame anchor.
3. `upload_asset` the still; it returns `asset_id="asset_abc"`.
4. `model_run` with `parameters={"image": "asset_abc", "prompt": "slow dolly-in, steam rising from the mug, shallow depth of field"}` and `wait=false`. Returns a `job_id`.
5. `jobs_wait` with `job_ids=["job_xyz"]`. On `status="in_progress"`, call again, passing the returned `pending_job_ids` as `job_ids`.
6. `asset_display` the output video; save the file from the `asset_get` URL with `curl -L`.

Iterating on motion: the source image already fixes the look, so prompt only motion, camera, and timing ("orbit left", "hold on the final pose"), changing one clause per retry. Several image-to-video models also accept first and last frame anchors or keyframe sequences (Kling, Veo 3.1, Seedance, Luma Ray 3.2); take exact parameter names from `model_schema_get`, never from memory.

## Editing existing footage

All editing is `model_run` on a video-input model; discover each with `search`:

- Prompt-driven edits (restyle, swap objects, characters, or backgrounds): query `"video edit"` (Grok Edit Video, Wan 2.7 Video Edit, Lucy Edit, Luma Modify Video).
- Lipsync and dubbing: query `"lipsync"` for video-to-video sync (Sync Lipsync, Kling Lipsync, Veed) and talking-portrait image-to-video avatars.
- Upscaling up to 4K: query `"video upscale"` (Topaz, SeedVR2, Magnific, Flash VSR).
- Deterministic utilities: query `"tool"` or `"video"` for trim (Video Cut), split, concat with transitions, resize, reverse, reframe to new aspect ratios, background removal, and frame extraction (Video to Image Sequence).
- Extending a clip with new footage from its last frame: query `"extend video"`.

## Common mistakes

- Passing a local file path as `image` or `video`: models take `asset_id`s; `upload_asset` first.
- Calling `model_run` without `model_schema_get`: field names and duration limits differ per model; a payload that worked on Kling will not fit Veo.
- Polling `job_get` in a loop: use `jobs_wait`; its ~180s timeout is not an error; re-call with `pending_job_ids`.
- Treating search hits as stable: catalogs evolve, so re-run `search` and prefer non-deprecated hits (many deprecated models carry a `deprecated:<replacement_id>` tag pointing at the successor; some only a bare tag).
- Pasting raw CDN URLs into chat: use `asset_display` for inline preview.
- Downloading video with `asset_download`: image conversion only; take the file URL from `asset_get`.
