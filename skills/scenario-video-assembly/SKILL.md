---
name: scenario-video-assembly
description: "Use when generated clips must become a finished video on Scenario via MCP: cutting a shot list together, laying a timeline, concatenating with transitions, overlaying a logo or title card, adding a music bed or voiceover, burning in or exporting captions and subtitles, trimming and splitting, or producing vertical and square variants of one master. Keywords: edit, assemble, stitch, concat, compositor, timeline, layers, overlay, captions, SRT, ad, UGC, social cut."
license: MIT
---

# Scenario Video Assembly

## Overview

Scenario has no editing tools on the MCP surface. Every compositor, concatenator, trimmer and captioner is a deterministic model run through `model_run`, so assembly reuses the generation loop. Find them with `search`, `target="models"`, `public=true`, `filters={"tags": ["tool"]}` (84 hits at authoring time). Connection and the core loop: see the `scenario` skill; generating the clips: see `scenario-video`.

## Pick the backend first

| Need                                              | Model                          |
| ------------------------------------------------- | ------------------------------ |
| Clips end to end, optional transitions between    | `model_scenario-video-concat`  |
| Anything overlapping: overlays, music bed, titles | `model_scenario-compose-video` |
| Still layout (thumbnails, sheets, key art)        | `model_scenario-compose-image` |

Concat is sequential: `videos` takes 2 to 50 files (never 1) and the optional `transitions` array's "length must be number of videos - 1", with 18 transition types.

Video Studio is an absolute timeline: `layers` holds 1 to 50 image, video or audio sources placed by `startTime` and stacked by `zIndex`, with 35 transition types. At least one layer must be a video, so a music bed over a still is rejected.

## The Video Studio contract

Per layer, three timing ideas have confusable names:

- `startTime` and `endTime` place the layer on the timeline.
- `trimStart` and `trimEnd` are amounts shaved off the head and tail of the source, not in and out points: to play the first 20 seconds of a 90-second track, set `trimEnd: 70`.
- `duration` overrides the layer's length. The top-level `duration` is a different field, setting the whole composition, and applies only when `durationMode` is `"custom"`.

Everything is in seconds at `step: 0.1`, so do not promise frame-accurate cuts. `x` and `y` are strings taking pixels, percentages, or words (`left`, `center`, `right`; `top`, `center`, `bottom`), and `anchor` decides which point of the layer that coordinate addresses, defaulting to `"top-left"`. A bottom-right logo is `x: "right"`, `y: "bottom"`, `anchor: "bottom-right"`.

`canvasMode` and `durationMode` both default to `"auto"`, computed from the layers. `fit` only acts on a layer that also sets `width` and `height`: to reframe a clip into a different aspect ratio set both to the canvas size and pass `"cover"` (crops) or `"contain"` (letterboxes), since the default `"fill"` stretches. The output field is `videoOutputFormat` here, `imageOutputFormat` in Image Studio, and `outputFormat` in concat and the trim utilities.

There is no text layer. `source` accepts only image, video and audio, so titles, lower thirds and end cards arrive as rendered PNGs composited as image layers.

## Worked example: three clips, a music bed, and captions

1. For each clip, `asset_get` and read `properties`: the real `duration`, `frameRate`, `nbFrames`, `width` and `height`. A model asked for eight seconds does not always return exactly eight, and the timeline is built from these numbers.
2. Add the durations to get each clip's `startTime`, then `model_schema_get` on `model_scenario-compose-video`.
3. `model_run` it with `layers` holding the three clips at their computed `startTime`s (`zIndex: 0`), a logo PNG pinned by `x`/`y`/`anchor`, and the music track as an audio layer (`volume` runs 0 to 2, `audioFadeOut` up to 10 seconds; `mute` the clips when the bed carries the mix). Set `canvasMode: "custom"` with the delivery size, and `fps`.
4. `jobs_wait`, then caption the finished cut rather than each clip: `model_scenario-caption-studio` transcribes the assembled video's own audio and burns the captions in by default, takes an existing `.srt` when the wording is fixed, and returns a sidecar file when `outputSrt` is true.
5. `asset_display` to review, `asset_download` (no `format`) for the file.

Other utilities, found the same way: `model_scenario-video-cut`, `model_scenario-video-split` (`cutPoints`, N points give N+1 segments) and `model_scenario-resize-video`.

## Common mistakes

- Reaching for an MCP tool like `video_compose`, or dropping to local ffmpeg. The editing surface is `model_run` on tool models.
- Handing concat one clip, or one transition per clip. The minimum is 2 videos and transitions run one fewer than that.
- Confusing `trimStart` with `startTime`, or reading `trimEnd` as an out-point rather than an amount.
- Timing a cut from the duration you requested rather than the duration `asset_get` reports.
- Captioning each clip and then concatenating: caption timings belong to the final master, and re-cutting afterwards invalidates them.
- Trusting `dry_run` here as validation. On these models it returns a cost estimate only, and assembly payloads are the most structurally complex in the catalog.
