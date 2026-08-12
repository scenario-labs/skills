---
name: scenario-textures
description: "Use when a task involves game textures or materials through the Scenario MCP: seamless or tileable textures, themed texture packs (brick, wood, stone, floors, hand-painted), PBR materials (albedo, metallic, roughness, normal) on 3D assets, retexturing a mesh, material iteration from reference images, texture upscaling that must preserve tiling, or sizing textures for game engines. Keywords: seamless texture, tileable, PBR, material, retexture, texture upscale, surface."
license: MIT
---

# Scenario texture and material workflows

## Overview

Scenario generates seamless, tileable textures from text or reference images, upscales them without breaking the tile, and applies PBR materials when texturing 3D meshes. Model availability differs per team and evolves, so always discover models with `search` at run time instead of hardcoding IDs.

Connection and the core generation loop: see the `scenario` skill in this repo.

## Quick reference

| Step | Tool | Notes |
| --- | --- | --- |
| Find texture models | `search` with `target="models"`, `query="seamless tileable"`, `public=true` | Also try `query="texture"` or `"PBR"` |
| Inspect inputs | `model_schema_get` | Always call before `model_run` |
| Generate | `model_run` | Schema-conformant parameters |
| Wait | `jobs_wait` | Never poll `job_get` in a loop |
| View and save | `asset_display`, then `asset_download` | Download for engine import |
| Upscale | `model_run` on a texture upscaler | 2x to 8x, tiling preserved |

## What live search confirms (examples to re-discover, not constants)

- Seamless generation: `model_scenario-texture` (Scenario Texture) takes a prompt (a tileable hint is appended automatically), `width`/`height` from 16 to 3840 in multiples of 16, `quality`, `seed`, up to 10 `referenceImages` for style, and `eraseSeam` with `overlap`/`featherRadius` to inpaint away both seam axes.
- Themed texture LoRAs (Flux.1 LoRA, tag `sc:texture`): floors, marble, concrete, stone walls, wood boards, brick, terracotta, hand-painted, cybernetic, realistic textures. They expose dedicated texture capabilities (`txt2img_texture`, `img2img_texture`, `controlnet_texture`).
- Tiling-safe upscaling: `model_sc-upscale-flux-texture` (Scenario Texture Upscale), `upscaleFactor` 2 to 8, presets `precise`/`balanced`/`creative`, optional prompt and style images.
- Material-look conversion: `model_sc-texture-converter` (Texture Converter) turns a flat image into a surface material using `raised`, `shiny`, `polished`, `angular` sliders and an `invert` relief toggle.
- PBR maps ship with 3D texturing and image-to-3D models, not as standalone 2D map decomposition. Examples seen live: Tripo 3.0 Texturing (PBR mode outputs albedo, metallic, roughness, normal), Tencent Texture Edit (prompt mode outputs full PBR maps for FBX models), Meshy 7 Retexture (optional PBR maps). Enable the model's PBR toggle found via `model_schema_get`.

## Worked example: seamless brick, iterated then upscaled

1. `search` `target="models"`, `query="seamless tileable"`, `public=true`, pick the seamless generator (e.g. `model_scenario-texture`).
2. `model_schema_get` `model_id="model_scenario-texture"`.
3. `model_run` with `parameters={"prompt": "weathered red brick wall, moss in the mortar joints", "width": 1024, "height": 1024, "eraseSeam": true, "seed": 42}`.
4. `jobs_wait` with `job_ids=["job_..."]` (the id returned by `model_run`), then `asset_display` the output asset.
5. Iterate: rerun with the same `seed` and an edited prompt, or add `referenceImages=["asset_..."]` to lock a style.
6. Upscale: `model_schema_get` then `model_run` `model_id="model_sc-upscale-flux-texture"` with `parameters={"image": "asset_...", "upscaleFactor": 4, "preset": "precise"}`.
7. `asset_download` the final asset for engine import.

## Common mistakes

- Skipping `model_schema_get`: parameter names differ per model and most models reject an empty payload.
- Using a generic upscaler on a tileable texture: it breaks the repeat at the seams. Use the texture-specific upscaler, which preserves tiling.
- Generating huge sizes directly: generate near 1024, then upscale 2x to 8x. Generation dimensions cap at 3840.
- Expecting a texture-to-PBR splitter: no live model decomposes a flat texture into separate map files. PBR maps come from 3D texturing models with PBR enabled.
- Ignoring engine sizing: engines expect square power-of-two textures (the seamless generator defaults to 1024x1024, 1:1). The generator accepts any multiple of 16, so choose 1024 or 2048 deliberately.
- Hardcoding model IDs: availability differs per team. Re-discover with `search` each session.
