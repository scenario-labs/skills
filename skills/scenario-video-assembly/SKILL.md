---
name: scenario-video-assembly
description: "Use when generated clips must become a finished video on Scenario via MCP: cutting a shot list together, laying a timeline, concatenating with transitions, overlaying a logo or title card, adding a music bed or voiceover, burning in or exporting captions and subtitles, trimming and splitting, or producing vertical and square variants of one master. Keywords: edit, assemble, stitch, concat, compositor, timeline, layers, overlay, captions, SRT, ad, UGC, social cut."
license: MIT
---

# Scenario Video Assembly

## Overview

Scenario has no editing tools on the MCP surface. Every compositor, concatenator, trimmer and captioner is a deterministic model run through `model_run`. Find them with `search`, `target="models"`, `public=true`, `filters={"tags": ["tool"]}` (84 hits at authoring time), one capability per query. Connection and the core loop: see the `scenario` skill; the clips themselves: see `scenario-video`.

## Quick reference: pick the backend first

| Need                                       | Model                          |
| ------------------------------------------ | ------------------------------ |
| Clips end to end, optional transitions     | `model_scenario-video-concat`  |
| Anything overlapping: overlay, bed, titles | `model_scenario-compose-video` |
| Still layout (thumbnails, sheets, key art) | `model_scenario-compose-image` |

These ids are authoring-time search hits, not constants: re-discover them, availability differs per team.

Concat is sequential: `videos` takes 2 to 50 files (never 1) and the optional `transitions` array's "length must be number of videos - 1", 18 types.

Video Studio is an absolute timeline: `layers` holds 1 to 50 image, video or audio sources placed by `startTime` and stacked by `zIndex` (higher in front), with per-layer `transitionIn`/`transitionOut`/`transitionDuration` instead of a between-clip array. At least one layer must be a video, so a music bed over a still is rejected.

## The Video Studio contract

Per layer, three timing ideas have confusable names:

- `startTime` and `endTime` place the layer on the timeline.
- `trimStart` and `trimEnd` are amounts shaved off the head and tail of the source, not in and out points: to play the first 20 seconds of a 90-second track, set `trimEnd: 70`.
- `duration` overrides the layer's length. The top-level `duration` is a different field, setting the whole composition, and applies only when `durationMode` is `"custom"`.

Everything is in seconds at `step: 0.1`, so do not promise frame-accurate cuts. `x` and `y` are strings taking pixels, percentages or words, and `anchor` says which point of the layer they address: `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right` (the middle one is bare `center`), defaulting to `"top-left"`. A bottom-right logo is `x: "right"`, `y: "bottom"`, `anchor: "bottom-right"`, flush to the edge unless you inset it with a percentage.

`canvasMode` and `durationMode` both default to `"auto"`, computed from the layers: a custom frame is `canvasMode: "custom"` plus numeric `canvasWidth` and `canvasHeight` (there are no top-level `width`/`height`, and unlike the layers' string `width`/`height` these are numbers), and a custom length is `durationMode: "custom"` plus the top-level `duration`. `fit` only acts on a layer that also sets the layer's own `width` and `height`, strings like `x` and `y`: to reframe a clip, set both to the canvas size and pass `"cover"` (crops) or `"contain"` (letterboxes), since the default `"fill"` stretches. The output field is `videoOutputFormat` here, `imageOutputFormat` in Image Studio, and `outputFormat` in concat and the trim utilities.

A layer has no `type` field: its kind is inferred from `source`, which accepts only image, video and audio. There is no text layer, so titles, lower thirds and end cards arrive as rendered PNGs composited as image layers.

## Worked example: three clips, a music bed, and captions

1. For every source, `asset_get` and read `properties`: the real `duration` (audio carries it too), `frameRate` on video, and `width`/`height` on video and images alike. A model asked for eight seconds does not always return exactly eight.
2. Add them up to get each clip's `startTime`, then `model_schema_get` on `model_scenario-compose-video`.
3. `model_run` it with `layers` holding the three clips at their computed `startTime`s (`zIndex: 0`), a logo PNG pinned by `x`/`y`/`anchor` at `zIndex: 1`, and the music as an audio layer trimmed to the clips' total with `trimEnd`, since auto `durationMode` computes from every layer, the bed included. `volume` (0 to 2) and `mute` are per-layer and apply to video layers too, so balance the bed from either side. Set `canvasMode: "custom"` with `canvasWidth` and `canvasHeight`; `fps` defaults to 30.
4. `jobs_wait`, then caption the finished cut rather than each clip: `model_scenario-caption-studio` takes it as `video` and transcribes whatever audio the master actually carries, so lower the bed's `volume` rather than muting the dialogue. It burns captions in by default, takes an existing `.srt` as `subtitles`, a file input needing `upload_asset` first, returns a sidecar when `outputSrt` is true, and positions them with `textPosition` (`top`, `middle` or `bottom`, default `bottom`, so move it off a bottom-edge overlay).
5. `asset_display` to review, then `asset_download` with `format` left unset (it is an image conversion target) for the file.

Trim, split and resize have their own tool models. Note `model_scenario-video-cut`'s `startTime`/`endTime` are source in and out points, not timeline placement.

## Common mistakes

- Reaching for an MCP tool like `video_compose`, or for local ffmpeg. The editing surface is `model_run` on tool models.
- Handing concat one clip, or one transition per clip: the minimum is 2 videos, and transitions run one fewer.
- Trusting `dry_run` here as validation: it returns a cost estimate only, and assembly payloads are the most structurally complex in the catalog.
