---
name: scenario-video-editing
description: "Use when editing footage that already exists on Scenario through MCP with a tool model instead of a new generation: 3D LUT grading, color correction, film grain, vignette, blur, sharpen, glow, tint, desaturate, posterize, solarize, cubism, crystallize, oilify, chromatic aberration or dodge and burn on a clip; trimming to a time range, splitting at cut points, reversing, resizing, re-encoding, frame extraction, image sequences, background removal, segmentation masks, subjects as layers."
license: MIT
---

# Scenario Video Editing

## Overview

Every image post-processing effect has a video twin, and each is a `model_run` on a tool model: one clip in, a few numbers, one clip out. Generating or restyling footage, lipsync, dubbing and upscaling are `scenario-video`; concatenating, compositing and captioning a cut are `scenario-video-assembly`; the still-image side is `scenario-image-editing`. Connection and the core loop: `scenario`. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## The twin rule

A video effect's id is the image id with `-video` appended, its file field is `video` rather than `image`, and the knobs are identical: `model_scenario-postprocessing-lut-video` takes the same `lutStyle` enum and `lutIntensity` as `model_scenario-postprocessing-lut`. All eighteen have twins: blur, chromatic aberration, color correction, crystallize, cubism, desaturate, dissolve, dodge and burn, glow and bloom, grain, 3D color LUT, oilify, parabolize, posterize, sharpen, solarize, tint, vignette.

One twin differs: Dissolve (Video) blends the clip with a still `dissolveImage`, not a second clip; crossfading two clips is a concat transition.

## Quick reference

| Need                  | Model or query                                                           |
| --------------------- | ------------------------------------------------------------------------ |
| Grade or stylize      | `filters={"tags": ["Post Processing"]}`, plus the effect name as `query` |
| Trim to a range       | `model_scenario-video-cut` (`startTime`, `endTime`)                      |
| Cut into segments     | `model_scenario-video-split` (`cutPoints`; N points give N+1 clips)      |
| Rescale or re-encode  | `model_scenario-resize-video`                                            |
| Frames out, frames in | `model_scenario-video-to-image-seq`, `model_scenario-image-seq-to-video` |
| Subjects as layers    | `model_scenario-video-layers-extractor`                                  |
| Masks, cutouts, audio | query `"segmentation"`, `"video background removal"`, `"audio extract"`  |

All via `search`, `target="models"`, `public=true`; re-discover rather than hardcoding, availability differs per team.

## Cost follows the clip, so trim first

On the video twins the `video` input carries `cost_impact: true`, which the image versions do not: price tracks the footage rather than the settings. Trim to the frames that ship, then grade; `dry_run=true` prices a payload before it runs. Video tools also outlast `model_run`'s wait window, so launch with `wait=false` and follow with `jobs_wait`, re-calling it with the returned `pending_job_ids`.

## Field names drift between neighbors

- Video Cut takes a scalar `video`. Resize Video takes `video` as an `array: true` field capped at one item, where a bare id is dropped silently.
- The output format field is `outputFormat` on cut and split, `videoOutputFormat` on resize.
- `preserveAudio` defaults to true on cut, split and resize.
- `asset_download` takes no `format` for a video: it converts image formats only.

## Resizing is not reframing

No tool model repaints a video's canvas: Resize Video fits the clip inside the target, or stretches it when `preserveAspectRatio` is false. Changing aspect ratio for real is either a generative reframe model (`query="reframe"` surfaces Luma Ray 3.2 Reframe and Wan 2.2 Reframe, `scenario-video` territory) or Video Studio with the layer's `fit` set to `"cover"`.

## Worked example: a graded vertical cutdown

1. `asset_get` the master and read `properties.duration` before choosing times.
2. `model_run` `model_scenario-video-cut` with `startTime` and `endTime` in seconds.
3. `model_schema_get`, then `model_run` `model_scenario-postprocessing-lut-video` on the trimmed asset with `lutIntensity` near 0.6.
4. Run the Grain twin on that output with `wait=false`, then `jobs_wait`.
5. Resize last: `model_scenario-resize-video`, `video` as a one-item array, `videoOutputFormat: "mp4"`.
6. `asset_display` to review, then `asset_download` with no `format`.

## Common mistakes

- Grading each source clip and then concatenating: grade the finished master once, or the shots drift apart.
- Reaching for local ffmpeg, or for an MCP tool named `video_edit`: the surface is `model_run` on tool models.
- Polling `job_get` in a loop instead of `jobs_wait`, whose timeout is not an error.
