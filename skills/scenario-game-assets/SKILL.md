---
name: scenario-game-assets
description: Use when creating game art through the Scenario MCP, including sprites, sprite sheets, game icons, props, loot, tilesets, seamless tiles, isometric buildings, top-down maps, pixel art, UI components such as buttons and panels, and character or concept art, or when game assets need transparent backgrounds, background removal, style-consistent variation batches (restyling an approved component into a set), upscaling, pixel-grid cleanup, or engine-ready PNG export for Unity, Godot, or Unreal.
license: MIT
---

# Scenario Game Assets

## Overview

Scenario's public catalog carries purpose-trained models per asset type (sprites, icons, props, tilesets, isometric scenes, pixel art, concept art) plus utilities for background removal, upscaling, and pixel cleanup. Discover by asset type, inspect the schema, generate, post-process, export. A sheet whose cells are one character's animation frames, and any walk cycle, loop, or GIF, belongs to `scenario-sprite-animation`. Connection and core loop: see the `scenario` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Task                       | Call                                                                                                                                               |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Find a model by asset type | `recommend` with the asset need in the user's own words (sprite, game icon, tileset, isometric, pixel art); `search` is for a member known by name |
| Inspect inputs             | `model_schema_get` (always before `model_run`)                                                                                                     |
| Generate                   | `model_run` (`dry_run=true` prices a batch; launch `wait=false`), then `jobs_wait`; on timeout re-call with `pending_job_ids`                      |
| Transparent background     | `recommend` for a native-alpha generator first; else for background removal on the asset                                                           |
| Upscale or enhance         | `recommend` for upscaling (2x to 16x tools exist)                                                                                                  |
| Pixel-art cleanup          | `recommend` for cleanup (grid snapping, palette reduction)                                                                                         |
| Export for an engine       | `asset_download` with format="png"                                                                                                                 |

## Worked example: a transparent potion icon set

Request: "four style-matched potion icons for an RPG inventory."

1. `recommend` with the user's own words as `prompt` ("four style-matched potion icons for an RPG inventory"). Typical picks: cartoon icon LoRAs ("Stylized Game Icons & Props"). Confirm the pick with the user: catalogs differ per team; re-discover, never hardcode model IDs.
2. `model_schema_get` model_id="<picked id>". Note the prompt field, size fields, and any sample-count parameter.
3. `model_run` parameters={"prompt": "health potion, corked glass bottle, glowing red liquid, bold outline, centered, plain background"} (a plain field cuts cleanly in a removal pass; a native-alpha model wants the subject alone, never the word transparent). The schema's sample-count parameter repeats one prompt for variants of one item; different items are separate runs varying only the item ("mana potion", "stamina potion") with the wording template fixed. Price with `dry_run=true` first (one dry run prices one leg; multiply across the batch), then launch with `wait=false`.
4. `jobs_wait` job_ids=["<returned job_id>"] (up to 32 ids, one call covers the batch); on timeout re-call with the returned `pending_job_ids`, never a second `model_run`. Then `asset_display` to review, one `asset_id` per call.
5. Transparency: `recommend` for a native-alpha generator first, since it makes the icons transparent at the source and skips a billed removal pass per icon. Treat the pick as opaque unless its `recommend` entry or its schema says it outputs transparency. Fall back to a removal model only when the chosen generator lacks alpha: `recommend` for background removal (Photoroom, Pixelcut, 851 Labs at authoring time), `model_schema_get` the pick, then `model_run` with its image field set to the generated asset id.
6. Optional: upscale keepers (`recommend` for upscaling, `model_schema_get` as always; upscalers go 2x to 8x and beyond).
7. `asset_download` asset_id, format="png" (PNG keeps alpha). Follow redirects: `curl -L -o potion.png "<url>"`.

## Style consistency

- The cheap levers first: reuse one `seed` across the batch, and pin the model's prompt-expansion flag off where the schema has one; an expander rewrites each prompt independently and defeats a fixed template.
- Reference images: `upload_asset` the art direction images, then pass the asset ids (never local paths) to the model's image or reference parameters.
- `asset_describe` turns one on-style asset into a promptable style synthesis reusable across prompts (catalog tool, billed, `dry_run: true` prices it: run via `scenario_tools_search` + `scenario_tool_execute_read`; see the `scenario` skill).
- `search` target="assets" images={like: ["asset_..."]} finds assets already matching the target look.
- For a locked-in project style, train a custom LoRA on the project's own art (the `scenario-model-training` skill); trained models use the same generation loop.

## Preparing a variation-batch reference

Restyling one approved component into a set (button, panel, popup well, icon family) fails on the reference more often than the prompt: the model treats everything composited onto the object as the object.

- **Crop to the object's own bounds.** Transparent padding reads as composition: scale and offset drift every run, so sprite-measuring code gets a different box. Trim the alpha, generate, re-pad to a fixed canvas. When the model's supported aspect ratios exclude the source's, aspect also drifts per run; reconcile UI components with a nine-slice-aware rescale (stretch middle bands, keep corners and lettering undistorted) before re-padding.
- **Strip baked effects before generating.** A drop shadow, outer glow, or bevel in the reference reads as silhouette and comes back thickened, doubled, or fused to the object. Feed flat art and re-apply the effect in engine, where it stays adjustable. For a final PNG matching a shadowed source, lift the source's effect layer by alpha (on a transparent source the shadow is semi-transparent and the object opaque, but so is the object's antialiased rim: take the shadow as the semi-transparent pixels outside a 1 to 2 px dilation of the opaque mask, and keep the rim with the object) and composite it under each output.
- **Say which parts are functional.** A nine-slice panel needs stretchable middles and fixed corners; diffusion has no concept of either. Name the constraint in the prompt, then check that it held.
- **One object, plain field, no scene.** Several objects in one reference get recombined into a hybrid.
- **Check the alpha edge on any transparent output.** Removed shadows leave a semi-transparent fringe; native-alpha models can ship a large semi-transparent glow around the object. Both read as a halo on a colored UI background. Check interior alpha too: a native-alpha model can punch one item's see-through surface (empty glass) to alpha 0 while painting the next item's opaque, so the set disagrees in an engine slot.

Verify the set by measurement, not by eye: compare each output's alpha bounding box against the source before accepting the batch.

## Isometric tiles and masked fills

Choose the grid before the style. A 2:1 diamond is a common game projection; a projected hex is a different footprint. Share one projection, placement anchor, light direction, and shadow side across a set. A tile's ground footprint is not its full sprite silhouette: trees and buildings rise above it and may overlap the tile behind. Never clip a tall object through the ground mask. Check a small assembled map for joins, path connections, occlusion, and visual quality before scaling the batch; a clean alpha boundary alone is not acceptance.

Use the [isometric template guide](isometric-templates.md) to choose a neutral ground or slab reference and separate ground, side, and object regions. The [JSON manifest](isometric-templates.json) records their geometry, filenames, and source hashes. The [template builder](scripts/build_isometric_templates.py), run by a maintainer or an agent needing local geometry, creates the PNGs and manifest. It generates geometry only, not finished game art. Keep the geometry reference separate from the approved style reference; neutral geometry must not force a palette or faceted look. Resolve uploaded assets and publish new versions through the `scenario` skill's [shared asset lifecycle](../scenario/references/shared-assets.md); upload local inputs only when no matching asset is accessible.

Dedicated isometric members exist in the public catalog. `recommend` with the user's tile need, then `model_schema_get`. Read the reference, mask, seed, and strength fields instead of assuming they exist or that low strength preserves geometry: conventions vary. Keep the camera and lighting wording fixed while varying the subject. Reuse a seed only when supported. If the model drifts in projection or light despite a consistent reference, use `scenario-consistency`, then consider `scenario-model-training` on approved tiles.

For a ground fill or content explicitly bounded to a shape, use masked `img2img`. If the specialty pick has no mask field, `recommend` again with `capability: "img2img"` and the mask need. Read mask polarity and any required base-image field from `model_schema_get` (`scenario-image` covers model-specific conventions). Template region images are white inside; adapt them to the model's convention, including alpha if required. The base canvas must match the mask dimensions and placement; an approved style reference does not replace it. When that canvas is opaque, preserve its background during the edit: asking for transparent output simultaneously contradicts the protected-canvas constraint. Extract transparency afterward. Use the ground region for terrain, and the taller object region for trees or buildings; the latter is editing space, never a final silhouette mask.

Run one tile first. Measure changes outside the edit region against the source canvas and inspect the result. A few-pixel overrun on a deliberately bounded ground fill can be clipped to its mask; extensive drift needs diagnosis of polarity, base canvas, and consumed references before retrying. For taller sprites, preserve the object silhouette with native alpha or background removal and verify the ground anchor separately. A deterministic ground mask cannot repair a wrong camera or a poor composition.

A "low-poly" look and a low-poly mesh are different deliverables. The look is a 2D style word on an image model. The mesh is `scenario-3d`: whether the image-to-3D pick (`recommend`, `capability: "img23d"`) exposes a polycount target or a topology choice is read off `model_schema_get`, never assumed, and when it exposes neither a separate remesh utility (its own billed run, found with `recommend`, `capability: "3d23d"`) brings the count down afterwards. Either way the concept image feeding it wants flat shading, a clean silhouette, and a plain background so the geometry reads.

## Common mistakes

- Prompting "transparent background" at a diffusion model: outputs are opaque. Cut the background afterward with a removal tool, or pick a native-alpha model.
- Exporting JPG sprites: JPG has no alpha channel; keep format="png".
- Shipping AI pixel art with off-grid pixels or noisy palettes: post-process with a pixel cleanup tool (found with `recommend`) for grid snapping and a strict palette.
- Skipping `model_schema_get`: specialty models (the pixel-art family) are txt2img-only with their own fields; generic parameters get rejected.
- Hand-stitching tilesets: dedicated seamless tileset generators exist (find one with `recommend`); texture-specific upscalers preserve tiling.
- Single-sampling lettered assets: the same recipe can render one word and fail another (dark embossed text, not the reference typography). Generate several samples per run (schema's sample-count parameter) and pin exact hex colors in the prompt when the palette drifts.
