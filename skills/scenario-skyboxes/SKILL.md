---
name: scenario-skyboxes
description: Use when a task involves generating or iterating on skyboxes, 360 panoramas, equirectangular images, environment maps, or VR backdrops through the Scenario MCP. Triggers include text-to-skybox, turning a photo into a 360 environment, restyling a panorama's mood, upscaling a skybox without breaking the seam wrap, or exporting equirectangular or cubemap layouts for game engines such as Unity, Unreal, or Godot.
license: MIT
---

# Scenario Skyboxes and 360 Panoramas

## Overview

Scenario hosts dedicated skybox models that produce seamless equirectangular 360 panoramas, plus a seam-preserving skybox upscaler. Always generate with a skybox-specific model rather than a generic image model: these enforce the seam continuity and pole geometry that ordinary text-to-image output lacks.

Connection and the core generation loop: see the `scenario` skill in this repo. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step | Tool                                                    | Purpose                                       |
| ---- | ------------------------------------------------------- | --------------------------------------------- |
| 1    | `search` (target="models", query="skybox", public=true) | Discover current skybox models                |
| 2    | `model_schema_get`                                      | Exact parameter contract for the chosen model |
| 3    | `model_run`                                             | Generate the panorama                         |
| 4    | `jobs_wait`                                             | Block until the job completes                 |
| 5    | `asset_display` / `asset_download`                      | Review inline, then save the file             |

Model IDs below were live `search` hits at authoring time. Re-discover them each time: availability differs per team and evolves.

- `model_scenario-skybox-flux`: text to 360 panorama, 21 style presets, automatic seam and pole correction, optional reference image with a strength slider.
- `model_scenario-skybox-gpt`: text to 360 panorama guided by up to 10 reference images, quality presets, width and height up to 3840 px.
- `model_hunyuan-world-image-to-skybox`: one photo of a place to a seamless 360 skybox.
- `model_sc-upscale-flux-skybox`: 2x to 8x skybox upscale that preserves the seamless wrap.

## Workflow: generate, iterate, export

Example: a stylized forest skybox for a game scene.

1. `search` with target="models", query="skybox", public=true. Pick a text-to-skybox model, for example `model_scenario-skybox-flux`.
2. `model_schema_get` for that model. Expect fields like prompt, style, negativePrompt, image, strength, numOutputs, geometryEnforcement, seed.
3. `model_run` with parameters={"prompt": "ancient pine forest at dawn, mist between trunks, god rays", "style": "cinematic", "numOutputs": 2}. Take style preset names from the schema response.
4. `jobs_wait` with job_ids=[the returned job_id], then `asset_display` each output.
5. Iterate on mood: copy the seed from the best result and change only style (cinematic, oil-painting, cyberpunk, and more). To keep composition while shifting look, pass the favorite as image with low strength (0.2 to 0.4). To steer mood from concept art instead, switch to `model_scenario-skybox-gpt` and pass referenceImages.
6. Export: run `model_sc-upscale-flux-skybox` with image=asset_id and upscaleFactor=4. baseModel defaults to FLUX.1-dev (stylized); a Krea-based realism option exists, so read the exact allowed values from `model_schema_get` before switching. Then `asset_download` the final asset.

Engine format notes: Skybox Flux outputs equirectangular panoramas; keep the default sizing. Skybox GPT's catalog lists equirectangular 2:1 plus cubemap strip 6:1 and cubemap cross 4:3 layouts, but its schema exposes only width and height, so confirm the layout contract with `model_schema_get` before relying on a cubemap layout. Beyond flat backdrops, the same search surfaces `model_hunyuan-world-skybox-to-splat`, and a separate search (query="world") finds the Marble world models; both turn a finished panorama into a navigable 3D Gaussian splat scene.

## Common mistakes

- Prompting a generic image model for a "360 panorama": edges will not wrap and poles smear. Use a dedicated skybox model.
- Upscaling with a generic upscaler: it breaks continuity at the wrap seam. Use the skybox upscaler.
- Hardcoding model IDs in scripts or docs: re-discover with `search`; the catalog changes.
- Fighting seam or pole distortion through prompt wording on Skybox Flux: raise geometryEnforcement above 0 instead, and only when distortion is actually visible.
- Requesting a non 2:1 width to height ratio on Skybox GPT while expecting equirectangular output: keep 2:1 (for example 2048x1024) for correct 360 viewing.
- Skipping `model_schema_get`: skybox models carry model-specific fields (style, geometryEnforcement, quality) that generic assumptions miss.
