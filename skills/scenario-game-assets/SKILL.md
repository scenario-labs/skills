---
name: scenario-game-assets
description: Use when creating game art through the Scenario MCP, including sprites, sprite sheets, game icons, props, loot, tilesets, seamless tiles, isometric buildings, top-down maps, pixel art, UI components such as buttons and panels, and character or concept art, or when game assets need transparent backgrounds, background removal, style-consistent variation batches (restyling an approved component into a set), upscaling, pixel-grid cleanup, or engine-ready PNG export for Unity, Godot, or Unreal.
license: MIT
---

# Scenario Game Assets

## Overview

Scenario's public catalog carries purpose-trained models per asset type (sprites, icons, props, tilesets, isometric scenes, pixel art, concept art) plus utilities for background removal, upscaling, and pixel cleanup. Discover by asset type, inspect the schema, generate, post-process, export. Connection and core loop: see the `scenario` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Task                       | Call                                                                                                        |
| -------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Find a model by asset type | `search` target="models", public=true, query="sprite" / "game icon" / "tileset" / "isometric" / "pixel art" |
| Inspect inputs             | `model_schema_get` (always before `model_run`)                                                              |
| Generate                   | `model_run`, then `jobs_wait`                                                                               |
| Transparent background     | `search` query="background removal", run that tool model on the asset                                       |
| Upscale or enhance         | `search` query="upscale" (2x to 16x tools exist)                                                            |
| Pixel-art cleanup          | `search` query="pixel" (grid snapping, palette reduction)                                                   |
| Export for an engine       | `asset_download` with format="png"                                                                          |

## Worked example: a transparent potion icon set

Request: "four style-matched potion icons for an RPG inventory."

1. `search` target="models", query="game icon", public=true. Typical hits: cartoon icon LoRAs ("Stylized Game Icons & Props"). Confirm the pick with the user: catalogs differ per team; re-discover, never hardcode model IDs.
2. `model_schema_get` model_id="<picked id>". Note the prompt field, size fields, and any sample-count parameter.
3. `model_run` parameters={"prompt": "health potion, corked glass bottle, glowing red liquid, bold outline, centered, plain background"}. Batch via the schema's sample-count parameter when present, or rerun varying only the item ("mana potion", "stamina potion") with the wording template fixed for a coherent set.
4. `jobs_wait` job_ids=["<returned job_id>"] (up to 32 ids, one call covers the batch), then `asset_display` to review.
5. `search` query="background removal" (Photoroom, Pixelcut, 851 Labs), `model_schema_get` the pick, then `model_run` with its image field set to the generated asset id. Some models generate native alpha; search "transparent".
6. Optional: upscale keepers (search "upscale", `model_schema_get` as always; Scenario's Flux upscalers go 2x to 8x and beyond).
7. `asset_download` asset_id, format="png" (PNG keeps alpha). Follow redirects: `curl -L -o potion.png "<url>"`.

## Style consistency

- Reference images: `upload_asset` the art direction images, then pass the asset ids (never local paths) to the model's image or reference parameters.
- `asset_describe` turns one on-style asset into a promptable style synthesis reusable across prompts (full-toolset tool: if unlisted, reconnect with `?toolsets=full` or run via `scenario_tools_search` + `scenario_tool_execute_read`; see the `scenario` skill).
- `search` target="assets" images={like: ["asset_..."]} finds assets already matching the target look.
- For a locked-in project style, train a custom LoRA on the project's own art (the `scenario-model-training` skill); trained models use the same generation loop.

## Preparing a variation-batch reference

Restyling one approved component into a set (button, panel, popup well, icon family) fails on the reference more often than the prompt: the model treats everything composited onto the object as the object.

- **Crop to the object's own bounds.** Transparent padding reads as composition: scale and offset drift every run, so sprite-measuring code gets a different box. Trim the alpha, generate, re-pad to a fixed canvas. When the model's supported aspect ratios exclude the source's, aspect also drifts per run; reconcile UI components with a nine-slice-aware rescale (stretch middle bands, keep corners and lettering undistorted) before re-padding.
- **Strip baked effects before generating.** A drop shadow, outer glow, or bevel in the reference reads as silhouette and comes back thickened, doubled, or fused to the object. Feed flat art and re-apply the effect in engine, where it stays adjustable. For a final PNG matching a shadowed source, lift the source's effect layer by alpha (on a transparent source, shadow pixels are semi-transparent, the object fully opaque) and composite it under each output.
- **Say which parts are functional.** A nine-slice panel needs stretchable middles and fixed corners; diffusion has no concept of either. Name the constraint in the prompt, then check that it held.
- **One object, plain field, no scene.** Several objects in one reference get recombined into a hybrid.
- **Check the alpha edge on any transparent output.** Removed shadows leave a semi-transparent fringe; native-alpha models can ship a large semi-transparent glow around the object. Both read as a halo on a colored UI background.

Verify the set by measurement, not by eye: compare each output's alpha bounding box against the source before accepting the batch.

## Common mistakes

- Prompting "transparent background" at a diffusion model: outputs are opaque. Cut the background afterward with a removal tool, or pick a native-alpha model.
- Exporting JPG sprites: JPG has no alpha channel; keep format="png".
- Shipping AI pixel art with off-grid pixels or noisy palettes: post-process with a pixel cleanup tool (search "pixel") for grid snapping and a strict palette.
- Skipping `model_schema_get`: specialty models (the pixel-art family) are txt2img-only with their own fields; generic parameters get rejected.
- Hand-stitching tilesets: dedicated seamless tileset generators exist (search "pixel art"); texture-specific upscalers preserve tiling.
- Single-sampling lettered assets: the same recipe can render one word and fail another (dark embossed text, not the reference typography). Generate several samples per run (schema's sample-count parameter) and pin exact hex colors in the prompt when the palette drifts.
