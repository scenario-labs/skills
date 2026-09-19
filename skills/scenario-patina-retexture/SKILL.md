---
name: scenario-patina-retexture
description: "Use when retexturing an existing 3D asset with PATINA PBR materials through the Scenario MCP server: a GLB or Blender scene (an image-to-3D result with flat colors, a prop, a diorama) whose surfaces need basecolor, normal, roughness, metalness, and height maps per material family with geometry untouched, or a matched before-and-after comparison film rendered in Blender with one camera path, lighting, and cut. Keywords: PATINA, PBR retexture, material families, Blender EEVEE, comparison video."
license: MIT
---

# Scenario PATINA retexture

## Overview

A mesh whose materials are flat colors or placeholders (an image-to-3D result such as a GPT-6 Astra 3D prop, a whole diorama) becomes a PBR-shaded asset in three moves: group its materials into physical surface families, generate one seamless PATINA material per family on Scenario, and wire the five maps into Blender materials with the geometry left byte-identical. An optional film renders the original and the retextured scene along one camera path with the same lights, exposure, and cut, so the material response is the only thing that differs between the two panels.

PATINA is Patina AI's material family on Scenario (tag `sc:texture`): PATINA Material builds a tiling PBR set from a prompt or a reference image, PATINA Image to Maps predicts maps from a flat texture, PATINA Material Extract flattens one material out of a photo. This skill runs PATINA Material; the flat-texture members belong to `scenario-textures`. Repainting a mesh with a 3D-to-3D texturing model (Meshy, Tripo, Trellis) is a different lane, covered by `scenario-3d`: it projects one new texture over the whole mesh, while this workflow keeps per-material control and yields editable Blender shaders. The agent's own steps stay on MCP; the bundled Blender and ffmpeg scripts (Blender 4.2 or newer, Python 3 with Pillow and numpy, ffmpeg with libx264) do the local repetition and never call Scenario. Connection and the core loop: the `scenario` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step           | Tool                                                             | Notes                                                                                                                        |
| -------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Scope          | `teams_list`, `projects_list`                                    | The source asset and the generation destination may live in different projects: pass the right pair on every call            |
| Fetch the mesh | `asset_get`, then `asset_download`                               | `properties.materialCount`, `faceCount`, `hasUVs`, `dimensions`; save with `curl -L`                                         |
| Inventory      | [inventory.py](scripts/inventory.py) in Blender                  | Writes `Before.blend` and `inventory.json`: per-material object counts, bounds, base color                                   |
| Find PATINA    | `search` with `target="models"`, `query="patina"`, `public=true` | Pick PATINA Material (`txt2img`); `model_schema_get` before running                                                          |
| Price          | `model_run` with `dry_run=true`                                  | One 1024x1024 five-map set was 17 CU at authoring time; `width`, `height`, `maps`, `upscaleFactor`, and `numOutputs` move it |
| Generate       | `model_run` with `wait=false`, one per family                    | Fixed `seed` per family; `jobs_wait` with every `job_id`, re-called with `pending_job_ids`                                   |
| Identify maps  | `asset_get` on each output                                       | `metadata.type` names the role; never rely on position                                                                       |
| Download       | `asset_download`, then `curl -L`                                 | `textures/<family>/<role>.png`                                                                                               |
| Apply          | [apply_materials.py](scripts/apply_materials.py) in Blender      | Manifest in [materials-manifest.md](references/materials-manifest.md); geometry hash asserted                                |
| Film           | [film.py](scripts/film.py) `pilot`, `run`, `status`              | Config in [film-config.md](references/film-config.md); resumable                                                             |

## Material families

Read `inventory.json`, not the scene. Group materials by what the surface physically is (plaster, cedar, terracotta, glazed ceramic, brass, painted steel, glass, canvas, asphalt, foliage), reusing one family across color variants: by default the shader keeps each original color as a tint under the PATINA basecolor, so one plaster set serves cream, ochre, and grey walls. Split a shared color that sits on different surfaces (the same green on a canvas awning and a painted sign) with an `object_overrides` entry keyed by object-name prefix. A 41-material diorama needed 14 families; expect one job per family. Where the mesh already models bricks, roof tiles, or planks, prompt for the material of one element (fired clay, weathered cedar), never for the pattern: the geometry supplies the structure and a patterned map doubles it.

## Generating one set per family

`model_schema_get` on the discovered id is the contract; the names below held at authoring time. `prompt` (required, 2048 characters) describes a flat, evenly lit, seamless physical surface with no objects or signage. `maps` is an array even for one entry (a bare string is ignored); keep the default of all five. `width` and `height` run 512 to 2048 in steps of 16, 1024 by default; `upscaleFactor` 2 or 4 enlarges the predicted maps only, not the base texture. `tilingMode` restricts the repeat to one axis for planks or corrugation. `numOutputs` returns up to 4 variants of one prompt, each priced. `enablePromptExpansion` is on by default: turn it off when the prompt is deliberate. Set `seed` per family and keep it in the manifest so a family can be regenerated identically.

Price the exact payload with `dry_run=true`, confirm the budget (families times cost), then launch every family with `wait=false` and one `jobs_wait` over all the job ids (32 per call); a timeout returns `pending_job_ids` to re-call with, never a reason for a second `model_run`. On a transport error, `jobs_list` before re-running: the job usually landed.

Each completed job carries six asset ids: the base texture first (`metadata.type` `inference-txt2img-texture`), then the five maps in the order requested, each labeled `texture-albedo`, `texture-normal`, `texture-smoothness`, `texture-metallic`, or `texture-height` (also `source: texture:<role>`). Read the label with `asset_get` rather than trusting the order. The roughness request comes back labeled smoothness, and at authoring time the values were roughness (a brushed brass map read darker than a matte grey one), so the label is the trap, not the data: `asset_display` that map for a family whose finish you know before touching `roughness_is_smoothness` in the manifest, which inverts it when true. `asset_download` each map (PNG by default) into `textures/<family>/<role>.png`, and record prompt, seed, job id, asset ids, scope pair, and billed `cuCost` under the manifest's `provenance` so the run is reproducible and attributable.

## Applying in Blender

`blender --background --factory-startup --python scripts/inventory.py -- model.glb work/` imports the GLB (or opens a `.blend`), saves a packed `work/Before.blend`, and writes `work/inventory.json`. Write `work/materials.json` mapping every material name to a family and every family to its five maps, then run `blender --background --factory-startup work/Before.blend --python scripts/apply_materials.py -- work/materials.json`. The script validates the manifest first (an unmapped material, an undefined family, a missing map file, or a bad range fails the run with every problem listed), adds a dedicated `PatinaUV` layer projected along each face's dominant axis at object scale so `tile_span` means meters per repeat, builds one Principled BSDF per original material and family (data maps as Non-Color, a normal map node plus a subtle height bump, no displacement), packs the images, asserts the geometry hash is unchanged, and saves the output plus a `.materials.json` report. Inspect curved objects and wood direction: the planar projection suits architecture, and an authored UV set may deserve to stay on those objects. The `.blend` is the deliverable; a glTF export flattens the calibrated shader graph (the exporter carries only direct texture links), so bake before exporting to an engine. Open the result or render one still before spending render time on a film.

## Comparison film

`python3 scripts/film.py config.json pilot` renders both endpoints of every shot at half resolution for both passes and writes `Pilot Contact.jpg` with a rough time estimate. Fix framing and material defects from that sheet, then `run` renders at native resolution, resumes valid frames, saves both camera scenes as editable `.blend` files, joins the shots with crossfades, stacks the passes under captions (2560x3200 from two 2368x1332 panels), exports a 1440-wide sharing copy, and checks every frame count with ffprobe; `status` prints progress. The run folder is fingerprinted from the inputs, the scripts, and the config: change any of them and a new folder starts.

Design shots from `inventory.json` bounds (a wide opener, close material studies, a closing pullback), not from the example plan, whose coordinates fit one asset. The fast preset (EEVEE, 24 samples, half-resolution ray-traced reflections with denoising, 12 fps sources interpolated to 24 fps for slow moves) finished 472 matched frames per pass in about 7.5 minutes on a laptop; use native 24 fps for fast motion. Verify with `review/Sweep Contact.jpg`, sampled at 2 fps across the whole master: one still per shot passes a defect that fades in mid-shot. A clean encoder log is not visual approval.

## Worked example: retexture a street diorama and film the comparison

1. `teams_list`, confirm the pair with the user. `asset_get` on the diorama (a GPT-6 Astra 3D result: 41 materials, no image textures, 78K faces), `asset_download`, then `curl -L -o work/street.glb "<url>"`.
2. Inventory with `inventory.py`; group the 41 materials into families such as `plaster`, `cedar`, `terracotta`, `ceramic`, `brass`, `steel`, `glass`, `canvas`, `asphalt`, and `leaf`, with an override sending the awning objects to `canvas`.
3. `search` for PATINA, then `model_schema_get` on PATINA Material (`model_patina-material` was the live id at authoring time; re-discover each session).
4. `model_run` with `dry_run=true` on one family payload: 17 CU, so 14 families price at 238 CU; confirm with the user.
5. Fourteen `model_run` calls with `wait=false`, prompts such as "aged lime plaster wall, fine mineral grain, flat, evenly lit, seamless", `seed` fixed per family; one `jobs_wait` with all fourteen ids, re-called with `pending_job_ids` until every row is complete.
6. `asset_get` on each output to read `metadata.type`; `asset_display` the smoothness-labeled plaster map to settle polarity; `asset_download` and `curl -L` every map into `textures/<family>/`.
7. Write `materials.json` (roughness ranges per family, `roughness_is_smoothness` as settled, `provenance` with job ids and cost) and run `apply_materials.py`; open `PATINA.blend` once.
8. Copy [example-config.json](references/example-config.json), replace the shots with ones framed from the inventory bounds, run `film.py` in `pilot` mode, inspect, then `run`; hand over the master, the sharing copy, both passes, and the two editable scenes, naming the interpolation used.
9. Optional: `upload_asset` the master as `kind: "video"` and file it with the source and the maps in a collection (`collection_create`, then `collection_add_assets`).

## Common mistakes

- Mapping outputs by position or by the `source` field alone: read `metadata.type`, and confirm the smoothness label's polarity before inverting.
- Prompting for bricks, tiles, or planks on a mesh that already models them: the pattern doubles.
- Asking a PATINA prompt for signage, objects, or lighting: it produces a material, not a scene.
- Regenerating a family because `jobs_wait` timed out or `model_run` raised a transport error: re-call with `pending_job_ids`, or `jobs_list` first.
- Running the full film before a pilot, or approving it from one still per shot instead of the 2 fps sweep sheet.
- Editing the config or a script mid-run and expecting the render to resume: the fingerprint changed, so it starts fresh.
- Hardcoding the PATINA id or the 17 CU figure: re-discover with `search`, re-price with `dry_run`.
