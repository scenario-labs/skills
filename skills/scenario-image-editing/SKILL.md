---
name: scenario-image-editing
description: "Use when editing an image that already exists on Scenario through MCP with a tool model instead of a new generation: 3D LUT color grade, color correction, posterize, solarize, vignette, film grain, blur, sharpen, glow, chromatic aberration, oilify, cubism, crystallize, dodge and burn, tint, desaturate, expand or uncrop to a wider canvas, reframe an aspect ratio, resize to exact pixels, crop padding, slice tiles, contact sheet, split into layers, remove a background or watermark, vectorize."
license: MIT
---

# Scenario Image Editing

## Overview

Editing an existing image is a `model_run` on a tool model: one file in, a few numeric knobs, one or more assets out, nothing to prompt on most of them. Generating a new image, prompt-driven edits and masked inpainting are `scenario-image`; the same effects on footage are `scenario-video-editing`; stacking layers is `scenario-video-assembly` (Image Studio). Connection and the core loop: `scenario`. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

Discover with `search`, `target="models"`, `public=true`:

| Need                          | Filter or query                                                    |
| ----------------------------- | ------------------------------------------------------------------ |
| The effects family            | `filters={"tags": ["Post Processing"]}` (40 hits, image and video) |
| Any other utility             | `filters={"tags": ["tool"]}`, one query per job                    |
| Cutouts, watermarks, relight  | `"remove background"`, `"text remover"`, `"relighting"`            |
| Layers, tiles, sheets, vector | `"layers"`, `"slice"`, `"grid"`, `"vectorize"`                     |

Ids below are authoring-time hits, not constants: re-discover them.

## The effects family

Eighteen effects share one shape, a required `image` file plus one to three knobs: blur, chromatic aberration, color correction, crystallize, cubism, desaturate, dissolve, dodge and burn, glow and bloom, grain, 3D color LUT, oilify, parabolize, posterize, sharpen, solarize, tint, vignette.

Ranges are per tool and unguessable. `posterizeThreshold` runs 0 to 1 (default 0.5) while Color Correction's `temperature`, `contrast` and `saturation` run -100 to 100 with `gamma` on 0.2 to 2.2. All of it comes from `model_schema_get`. Not every knob is a number: Grain takes a 22-value profile enum, a color temperature and a boolean, with no strength control at all. Those profiles are looks rather than intensities, and some soften the picture instead of texturing it, so compare the result against the input rather than assuming grain landed. Defaults disagree too, Color Correction's being no-ops (a run with nothing set returns the input unchanged and still charges) where LUT and Posterize ship a visible default.

`lutStyle` holds 120+ exact strings, one of which contains a space, so copy them from the schema rather than retyping. They sort into three families: `cgc_film_emulation_*` and `rec709_*` emulate film stocks, `cgc_look_*` are graded looks, and `cgc_log_to_rec709_*` expect log footage and will over-contrast an ordinary render.

These finish inside `model_run`, returning `status: "success"` with the assets attached, so no `jobs_wait`. Chain them by passing one run's `asset_id` to the next, in pipeline order: reshape, then grade, then texture. Grain and sharpening are high-frequency effects that any later resize interpolates away, so they go last, at delivery resolution; a LUT is resolution-tolerant and sits on either side.

## Expanding a canvas is four different tools

- **Reframe** (`model_scenario-gemini-reframe`): an `aspectRatio` enum plus a `resolution` tier (1K, 2K, 4K), so an exact pixel target is out of reach; takes an optional `prompt`. The enum is approximate, not exact: `4:5` came back 1856x2304, which is 29:36, so a true ratio needs a Resize Image pass after it.
- **Smart Reframe** (`model_scenario-smart-reframe`): `width` and `height` are required and exact, and it protects on-image text, brand marks and palette. `textDensity: "DENSE"` costs substantially more.
- **Photoroom Expand**: exact `outputWidth` and `outputHeight` up to 4096, plus a `seed`.
- **Photoroom Uncrop**: rebuilds a subject the frame edge cut off.

Resize Image is none of these: it scales pixels, never invents canvas.

Both reframes recompose generatively rather than filling new canvas, and they are the expensive step in any chain, tens of times an effect's price, so `dry_run` them. Because they re-render, reframe first and grade after: a grade and grain pass applied beforehand comes back partly reinterpreted.

## Cardinality

Effects take a scalar `image`. Resize Image (`images`, max 10) and Grid Maker (`images`, max 100) are `array: true`, where a bare id is dropped silently and the run then succeeds having ignored it.

## Worked example: grade a key art, then export at size

1. `upload_asset` the file, then `upload_asset_complete` unless it went inline under ~100KB.
2. Reshape first: Resize Image to the delivery size, with `images` as an array even for the one file.
3. `search` with `filters={"tags": ["Post Processing"]}` and `query="LUT"`, `model_schema_get` the hit, pick a `lutStyle` from its enum, price it with `model_run` and `dry_run=true`, then run it with `lutIntensity` near 0.6 for a restrained grade.
4. Grain last, on that output, so its texture is sized for the frame that ships.
5. `asset_display` to review, `asset_download` to save.

## Common mistakes

- Reaching for an `image_edit` MCP tool, or for local ImageMagick or Pillow: the surface is `model_run` on tool models.
- Prompting an effect ("more posterized"): they read numbers only. Reframe and the layer extractors take text.
- Slicing or extracting layers before grading: both return one asset per piece, so every piece then needs its own run.
