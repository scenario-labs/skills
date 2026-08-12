---
name: scenario-game-assets
description: Use when creating game art through the Scenario MCP, including sprites, sprite sheets, game icons, props, loot, tilesets, seamless tiles, isometric buildings, top-down maps, pixel art, and character or concept art, or when game assets need transparent backgrounds, background removal, style-consistent variation batches, upscaling, pixel-grid cleanup, or engine-ready PNG export for Unity, Godot, or Unreal.
---

# Scenario Game Assets

## Overview

Scenario's public catalog carries purpose-trained models for game asset types (sprites, icons, props, tilesets, isometric scenes, pixel art, concept art) plus utility models for background removal, upscaling, and pixel cleanup. The workflow is always: discover a model by asset type, inspect its schema, generate, post-process, export. Connection and the core generation loop: see the `scenario` skill in this repo.

## Quick reference

| Task | Call |
| --- | --- |
| Find a model by asset type | `search` target="models", public=true, query="sprite" / "game icon" / "tileset" / "isometric" / "pixel art" |
| Inspect inputs | `model_schema_get` (always before `model_run`) |
| Generate | `model_run`, then `jobs_wait` |
| Transparent background | `search` query="background removal", run that tool model on the asset |
| Upscale or enhance | `search` query="upscale" (2x to 16x tools exist) |
| Pixel-art cleanup | `search` query="pixel" (grid snapping, palette reduction) |
| Export for an engine | `asset_download` with format="png" |

## Worked example: an icon set with transparent backgrounds

Request: "four style-matched potion icons for an RPG inventory."

1. `search` target="models", query="game icon", public=true. Typical hits: cartoon icon LoRAs such as "Stylized Game Icons & Props". Confirm the pick with the user; catalogs differ per team, so re-discover instead of hardcoding model IDs.
2. `model_schema_get` model_id="<picked id>". Note the prompt field, size fields, and any sample-count parameter.
3. `model_run` parameters={"prompt": "health potion, corked glass bottle, glowing red liquid, bold outline, centered, plain background"}. For the batch, use the schema's sample-count parameter when present, or rerun varying only the item ("mana potion", "stamina potion"). Keep the wording template fixed so the set stays coherent.
4. `jobs_wait` with job_ids=["<returned job_id>"] (it accepts up to 32 ids, so one call covers the whole batch), then `asset_display` to review.
5. `search` query="background removal" (Photoroom, Pixelcut, and 851 Labs variants exist), `model_schema_get` the picked tool, then `model_run` with the schema's image field set to the generated asset id. Some models generate native alpha directly; search "transparent".
6. Optional: run an upscaler on keepers (search "upscale", then `model_schema_get` as always; Scenario's Flux upscalers go 2x to 8x and beyond).
7. `asset_download` asset_id, format="png" (PNG keeps the alpha channel). Follow redirects when saving: `curl -L -o potion.png "<url>"`.

## Style consistency

- Reference images: `upload_asset` the art direction images, then pass their asset ids to the model's image or reference parameters (asset ids, never local paths).
- `asset_describe` turns one on-style asset into a promptable style synthesis to reuse across prompts (full-toolset tool: if it is not listed, reconnect with `?toolsets=full` or run it via `scenario_tools_search` + `scenario_tool_execute_read`; see the `scenario` skill).
- `search` target="assets" with images={like: ["asset_..."]} finds existing assets that already match the target look.
- For a locked-in project style, train a custom LoRA on the project's own art: see the `scenario-model-training` skill in this repo. Trained models run through the same generation loop.

## Common mistakes

- Prompting "transparent background" at a diffusion model: outputs are opaque. Cut the background afterward with a removal tool, or pick a native-alpha model.
- Exporting JPG sprites: JPG has no alpha channel; keep format="png".
- Shipping AI pixel art with off-grid pixels or noisy palettes: post-process with a pixel cleanup tool (search "pixel") that snaps pixels to a grid and enforces a strict palette.
- Skipping `model_schema_get`: specialty models (the pixel-art family, for example) are txt2img-only with their own fields, and generic parameters get rejected.
- Hand-stitching tilesets: dedicated seamless tileset generators exist (search "pixel art" surfaces them), and texture-specific upscalers preserve tiling.
