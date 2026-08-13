---
name: scenario-video-assembly
description: "Use when generated clips must become a finished video on Scenario via MCP: cutting a shot list together, laying a timeline, concatenating with transitions, overlaying a logo or title card, adding a music bed or voiceover, burning in or exporting captions and subtitles, trimming and splitting, or producing vertical and square variants of one master. Keywords: edit, assemble, stitch, concat, compositor, timeline, layers, overlay, captions, SRT, ad, UGC, social cut."
license: MIT
---

# Scenario Video Assembly

## Overview

Scenario has no editing tools on the MCP surface. Every compositor, concatenator, trimmer and captioner is a deterministic model run through `model_run`, so assembly uses the same loop as generation. Discover them with `search`, `target="models"`, `public=true`, `filters={"tags": ["tool"]}`, which returned 84 hits at authoring time. Connection and the core loop: see the `scenario` skill in this repo; generating the clips themselves: see `scenario-video`.

## Pick the backend first

| Need                                              | Model                          |
| ------------------------------------------------- | ------------------------------ |
| Clips end to end, optional transitions between    | `model_scenario-video-concat`  |
| Anything overlapping: overlays, music bed, titles | `model_scenario-compose-video` |
| Still layout (thumbnails, sheets, key art)        | `model_scenario-compose-image` |

Concat is sequential: `videos` is a file array of 2 to 50 (never 1), and the optional `transitions` array's "length must be number of videos - 1". It offers 18 transition types.

Video Studio is an absolute timeline: `layers` holds 1 to 50 image, video or audio sources, each placed by `startTime`, stacked by `zIndex`, and it offers 35 transition types. At least one layer must be a video, so a music bed over a still image is rejected.

## The Video Studio contract

Per layer, three different timing ideas share similar names:

- `startTime` and `endTime` place the layer on the timeline.
- `trimStart` and `trimEnd` choose which part of the source plays.
- `duration` overrides the layer's length, and is a different field from the top-level `duration`, which sets the whole composition's length and only applies when `durationMode` is `"custom"`.

Everything is in seconds with `step: 0.1`, so do not promise frame-accurate cuts. `x` and `y` are strings, taking pixels, percentages, or words like `"center"`. `fit` defaults to `"fill"`, which stretches, so pass `"contain"` or `"cover"` when a layer's aspect ratio differs from the canvas. Dimensions come from `canvasWidth` and `canvasHeight` and are ignored unless `canvasMode` is `"custom"`. The output field is `videoOutputFormat` here, `imageOutputFormat` in Image Studio, and `outputFormat` in concat and the trim utilities.

There is no text layer. `source` accepts only image, video and audio, so titles, lower thirds and end cards arrive as rendered PNGs composited as image layers.

## Worked example: three clips, a music bed, and captions

1. For each generated clip, `asset_get` and read `properties`: it carries the real `duration`, `frameRate`, `nbFrames`, `width` and `height`. A model asked for eight seconds does not always return exactly eight, and these numbers are what the timeline is built from.
2. Add the durations to get each clip's `startTime`, then `model_schema_get` on `model_scenario-compose-video`.
3. `model_run` it with `layers` holding the three clips at their computed `startTime`s (`zIndex: 0`), a logo PNG pinned with `x: "center"`, `y: "bottom"`, and the music track as an audio layer with `volume` and `audioFadeOut`. Set `canvasMode: "custom"` with the delivery size, and `fps`.
4. `jobs_wait`, then caption the finished cut rather than each clip: `model_scenario-caption-studio` takes the assembled video, burns captions in by default, and also returns a sidecar `.srt` when `outputSrt` is set to true.
5. `asset_display` to review, `asset_download` (no `format`) for the file.

Other utilities, discovered the same way: `model_scenario-video-cut` trims to a `startTime` and `endTime`, `model_scenario-video-split` takes `cutPoints` (N points produce N+1 segments), and `model_scenario-resize-video` reframes.

## Common mistakes

- Reaching for an MCP tool named something like `video_compose`, or dropping to local ffmpeg. The editing surface is `model_run` on tool models.
- Handing concat one clip, or one transition per clip. The minimum is 2 videos and transitions run one fewer than that.
- Confusing `trimStart` with `startTime`, so clips start late and run short.
- Passing numbers to `x` and `y`: they are strings.
- Planning a text layer for the title card. Render it as an image first.
- Timing a cut from the duration you requested rather than the duration `asset_get` reports.
- Captioning each clip and then concatenating: caption timings belong to the final master, and re-cutting afterwards invalidates them.
- Trusting `dry_run` here as a validation pass. On these models it returns a cost estimate only, and an assembly payload is the most structurally complex in the catalog.
