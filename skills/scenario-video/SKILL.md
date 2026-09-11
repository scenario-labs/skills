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
| Wait           | `jobs_wait`                        | Re-call with the returned `pending_job_ids` until done; its ~180s timeout is not an error                                     |
| Review         | `asset_display` / `asset_download` | Display inline; `asset_download` returns the file URL, save it with `curl -L`                                                 |

## Worked example: animate a key art still into a short ad clip

1. `recommend` with the user's own words as `prompt` (the need is a capability, `img2video`); handle `next_step` as the `scenario` skill directs.
2. `model_schema_get` on the pick. Note the image field, duration options, and any last-frame anchor.
3. `upload_asset` the still; it returns `asset_id="asset_abc"`.
4. `model_run` with `parameters={"image": "asset_abc", "prompt": "Close-up on the mug; slow dolly-in as steam curls through window light, shallow focus on the rim. Room tone, no music, no subtitles."}` and `wait=false`. Returns a `job_id`.
5. `jobs_wait` with `job_ids=["job_xyz"]`, re-called with `pending_job_ids` while any remain.
6. `asset_display` the output, then `asset_download` (no `format`).

The source image already fixes the look, so prompt only motion, camera, and timing ("orbit left", "hold on the final pose"), changing one clause per retry. A first-frame field pins how the clip opens (a last-frame field, where offered, how it lands); a reference-image field carries identity and look without fixing any moment. So an exact opening composition goes in as a rendered still and a recurring character or product as references; whether one run takes both is per schema, and several forbid the pair. Iterate at the cheapest resolution tier and shortest useful `duration`, then upscale the keeper: a re-run at a higher tier is a new generation, since many video schemas expose no `seed` and none promises one reproduces a shot across tiers.

## Prompting a shot

Write the prompt as a shot direction in sentences, not tags: shot size, setting, subject and one action, one named slow camera move, light source, style, and an audio line, in the order the family skill gives. Named moves and concrete light survive generation; mood words do not.

Many generators return sound with the picture (dialogue, effects, ambience, sometimes a score), switched by `generateAudio` or `audio` where the schema has one, each with its own default; with none, the search hit says whether sound comes back, and the prompt is the only lever over what does. Effects and ambience go in plain words, dialogue in quotes, plus "no music" (the score is laid once in assembly; switch the audio off when assembly supplies the whole soundtrack) and "no subtitles, no on-screen text", since a caption tool adds captions and removes none. Exclusions ride the prompt unless the schema has `negativePrompt`. Type the viewer must read is composited in assembly (`scenario-video-assembly`): generated type drifts.

## Editing existing footage

All editing is `model_run` on a video-input model found with `recommend`:

- Prompt-driven edits (restyle, swap objects, characters, backgrounds, or reframe to another aspect ratio). A reframe outpaints past the frame, unlike a deterministic resize. When a prompt-driven editor misses a directed change (a recolor, a prop swap), edit the still: `asset_get` returns the clip's `firstFrame` as a free asset id; edit it with an image model and re-render from it as the first frame, the source clip beside it where the schema takes that pair (few do).
- Lipsync and dubbing: see the next section.
- Upscaling up to 4K.
- Deterministic utilities (trim, split, resize, effects, grading, frame extraction, background removal): see `scenario-video-editing`. Assembling a finished cut: see `scenario-video-assembly`.
- Extending a clip from its last frame, on a dedicated extend member or by chaining first-frame runs past any member's duration cap: `asset_get` the rendered clip and pass its `lastFrame` asset id as the next run's first frame, writing that prompt from what the frame shows (positions, facing, the camera's side, so screen direction survives the seam) rather than from the plan, since renders drift from it.

## Dubbing is not lipsync

Dubbing translates the speech and keeps each speaker's own voice, tone, and timing. It does not move the mouth, so a dubbed talking head still has lips forming the original language. Three steps, after any trim the limits below require:

1. **Dub.** Takes the clip as `file` and a required `targetLang` from the schema's allowed values. Omit `sourceLang` to auto-detect, since the value that means auto differs between models. When a brand or name must survive translation, pick a hit whose schema carries `keyterms`, as not all do; where it is `array: true`, pass `["Scenario"]` even for one term.
2. **Extract.** Dubbing returns a dubbed video, not a bare track, and lipsync wants an audio asset. Pull the speech out with `model_scenario-audio-extract`, a fixed first-party id: Scenario's single deterministic tool for the operation, so discovery would only re-derive it.
3. **Lipsync.** Pass the dubbed video together with its extracted track. No schema says whether the input's own audio survives, so listen to the output before shipping. The clip and the track are separate fields, `video`/`audio` on most hits and `videoUrl`/`audioFile` on others. A duration-mismatch control is not universal: where present it is `syncMode` or `lipsyncMode` (`cut_off`, `loop`, `bounce`, `silence`, `remap`) with a per-model default, and there `loop` and `bounce` extend the shorter stream while `cut_off` ends at it; elsewhere a `loop` boolean loops the audio instead.

Judge a localized talking head on a stylized character before promising it on a photoreal one.

## Duration limits

Where a model bounds input length it rejects rather than trims: a 30.08 second reference against a 30.0 second limit fails the whole run, with the error naming both numbers. A ceiling can be a typed `max_duration` on the file field, prose in that field's description, or absent, so check both, on the audio input as readily as the video. When one applies, trim with the deterministic cut or split tools (`model_scenario-video-cut`, `model_scenario-video-split`, fixed ids for the same reason as the extractor above) before the run that enforces it, and before any step whose output must match the trimmed footage, such as a dub. Land inside the stated range, not on its edge.

## Common mistakes

- Calling `model_run` without `model_schema_get`: a payload that worked on Kling will not fit Veo.
- Treating search hits as stable: catalogs evolve, so re-run `search` and prefer non-deprecated hits (a `deprecated:<replacement_id>` tag names the successor).
