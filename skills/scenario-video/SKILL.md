---
name: scenario-video
description: "Use when generating or editing video on Scenario via MCP: text-to-video, image-to-video (still animation, first/last frame anchors), motion prompting, lipsync and talking avatars, dubbing or translating a clip, video upscale to 4K, prompt-based editing, trim, split, concat, extend, reframe, resize, background removal, frame or audio extraction, waiting on long video jobs, or a clip rejected for exceeding a duration limit. Keywords: txt2video, img2video, video2video, I2V, T2V, V2V, localization."
license: MIT
---

# Scenario Video Generation and Editing

## Overview

Scenario exposes a large video catalog through one MCP loop: text-to-video and image-to-video generators plus video-to-video editors, lipsync, upscalers, and deterministic cut/split/concat tools. Per-family contracts: `scenario-kling`, `scenario-veo`, `scenario-seedance`, `scenario-gemini-omni`, `scenario-luma-video`, `scenario-runway`, `scenario-grok-imagine-video`, `scenario-wan`, `scenario-minimax-video`, `scenario-vidu`.

Connection and the core generation loop: see the `scenario` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step           | Tool                               | Notes                                                                                                                         |
| -------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Find a model   | `recommend` or `search`            | `recommend` with the need in the user's own words for a capability (`img2video`, lipsync, upscale, edit); `search` for a name |
| Inspect inputs | `model_schema_get`                 | Always before `model_run`; video schemas differ widely (duration, aspect ratio, frame anchors)                                |
| Upload source  | `upload_asset`                     | A local still or clip becomes an `asset_id`                                                                                   |
| Generate       | `model_run`                        | `wait=false` for video; `dry_run=true` to estimate cost first                                                                 |
| Wait           | `jobs_wait`                        | Re-call with the returned `pending_job_ids` until done                                                                        |
| Review         | `asset_display` / `asset_download` | Display inline; `asset_download` returns the file URL, save it with `curl -L`                                                 |

## Worked example: animate a key art still into a short ad clip

1. `recommend` with the user's own words as `prompt`; the need is a capability (`img2video`), not a member known by name. Handle `next_step` as the `scenario` skill directs.
2. `model_schema_get` on the pick. Note the image field, duration options, and any last-frame anchor.
3. `upload_asset` the still; it returns `asset_id="asset_abc"`.
4. `model_run` with `parameters={"image": "asset_abc", "prompt": "slow dolly-in, steam rising from the mug, shallow depth of field"}` and `wait=false`. Returns a `job_id`.
5. `jobs_wait` with `job_ids=["job_xyz"]`, re-calling with the returned `pending_job_ids` while any remain.
6. `asset_display` the output, then `asset_download` (no `format`).

The source image already fixes the look, so prompt only motion, camera, and timing ("orbit left", "hold on the final pose"), changing one clause per retry. Several also accept first and last frame anchors or keyframe sequences; take the exact names from `model_schema_get`.

## Editing existing footage

All editing is `model_run` on a video-input model; discover each with `recommend`, stating the need in the user's own words:

- Prompt-driven edits (restyle, swap objects, characters, backgrounds, or reframe to another aspect ratio). A reframe outpaints past the frame, unlike a deterministic resize.
- Lipsync and dubbing: see the next section.
- Upscaling up to 4K.
- Deterministic utilities (trim, split, resize, effects, grading, frame extraction, background removal): see `scenario-video-editing`. Assembling a finished cut: see `scenario-video-assembly`.
- Extending a clip with new footage from its last frame.

## Dubbing is not lipsync

Dubbing translates the speech and keeps each speaker's own voice, tone, and timing. It does not move the mouth, so a dubbed talking head still has lips forming the original language. Three steps, after any trim the limits below require:

1. **Dub.** Takes the clip as `file` and a required `targetLang` from the schema's allowed values. Omit `sourceLang` to auto-detect, since the value that means auto differs between models. When a brand or name must survive translation, pick a hit whose schema carries `keyterms`, as not all do; where it is `array: true`, pass `["Scenario"]` even for one term.
2. **Extract.** Dubbing returns a dubbed video, not a bare track, and lipsync wants an audio asset. Pull the speech out with `model_scenario-audio-extract`, a fixed first-party id: Scenario's single deterministic tool for the operation, so discovery would only re-derive it.
3. **Lipsync.** Pass the dubbed video together with its extracted track. No schema says whether the input's own audio survives, so listen to the output before shipping. The clip and the track are separate fields, `video`/`audio` on most hits and `videoUrl`/`audioFile` on others. A duration-mismatch control is not universal: where present it is `syncMode` or `lipsyncMode` (`cut_off`, `loop`, `bounce`, `silence`, `remap`) with a per-model default, and there `loop` and `bounce` extend the shorter stream while `cut_off` ends at it; elsewhere a `loop` boolean loops the audio instead. Take names and defaults from `model_schema_get`.

Judge a localized talking head on a stylized character before promising it on a photoreal one.

## Duration limits

Where a model bounds input length it rejects rather than trims: a 30.08 second reference against a 30.0 second limit fails the whole run, with the error naming both numbers. A ceiling can be a typed `max_duration` on the file field, prose in that field's description, or absent, so check both, on the audio input as readily as the video. When one applies, trim with the deterministic cut or split tools (`model_scenario-video-cut`, `model_scenario-video-split`, fixed ids for the same reason as the extractor above) before the run that enforces it, and before any step whose output must match the trimmed footage, such as a dub. Land inside the stated range, not on its edge.

## Lipsync: footage or a still

Two lanes, told apart by the input in hand. Footage plus a new track is `recommend` with `capability="video2video"` and the ask in the user's words: these members redraw the mouth region and keep the rest of the frame (`video` and `audio`, or `videoUrl` and `audioFile`; some take typed `text` with a voice instead of audio, never both). A still plus a track is `capability="img2video"`: the talking-avatar members animate the whole portrait and invent its motion, so they serve a portrait with no footage, or footage whose motion is disposable, and never rescue a clip whose lipsync failed, since the result is a different performance of a different shot. Naming lipsync as the capability gets re-read as one of these two, so name the input.

Preflight is free and decides the run. Sync members redraw pixels around the mouth they detect; a face that is small in frame, turned away, occluded, or blurred by motion gives them nothing to redraw, and the run then completes and bills with the mouth still under the new track, the failure users report as "no lipsync at all". `asset_display` the clip's `firstFrame` (free, from `asset_get`): the lips should read at display size. When they do not, reframe onto the face first (`scenario-video-assembly`'s compositor, or a generative reframe) rather than retrying members. With several faces in frame, pick a member exposing speaker selection (`activeSpeaker` on one at authoring time) or crop to one speaker. Per-member limits sit in the schema, not the description: one member takes clips of 2 to 10 seconds at 720p to 1080p, others carry none; the `video` field carries `cost_impact: true`, so trim to the shipped range before the run (Duration limits above).

Plan gating is common here: `recommend` marks such members `requires_plan_upgrade` (unless its response says plan gating is `_degraded`), and running one anyway returns a 403 naming the model and the plan it needs, which no retry clears; pick an available member or surface the upgrade, per the `scenario` skill's plan row.

A completed job proves the model ran, not that the mouth moved. Before shipping, download the output and the source and compare frames at the same timestamps (sweep both into contact sheets locally, `ffmpeg -vf "fps=2"`, and read the mouth region): unchanged mouth pixels across the sweep mean the face was not found, and the same payload reproduces it, so change the framing or the lane rather than the seed. Listen as well: whether the input's own track survives is undocumented (Dubbing above).

## Common mistakes

- Shipping a lipsync run on the strength of its completed status: the failure mode is a still mouth under the new track, so compare frames against the source first.
- Passing a local file path as `image` or `video`: models take `asset_id`s; `upload_asset` first.
- Calling `model_run` without `model_schema_get`: field names and duration limits differ per model; a payload that worked on Kling will not fit Veo.
- Polling `job_get` in a loop: use `jobs_wait`; its ~180s timeout is not an error; re-call with `pending_job_ids`.
- Treating search hits as stable: catalogs evolve, so re-run `search` and prefer non-deprecated hits (a `deprecated:<replacement_id>` tag names the successor).
- Pasting raw CDN URLs into chat: use `asset_display` for inline preview.
- Passing `format` to `asset_download` for a video: it converts image formats only, so omit it.
