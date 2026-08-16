---
name: scenario-3d
description: Use when generating or handling 3D assets through the Scenario MCP server, including text-to-3D or image-to-3D meshes, GLB, FBX, OBJ, or VOX files, PBR-textured or game-ready models, voxel models, multi-view reconstruction, retexture, remesh, UV unwrap, auto-rigging a biped or quadruped character, skin weights, or retargeting an animation, previewing a mesh in the inline 3D viewer, capturing a viewer screenshot, or downloading a model for import into Unity, Unreal, Godot, or Blender.
license: MIT
---

# Scenario 3D Asset Workflows

## Overview

Scenario runs text-to-3D, image-to-3D, and 3D-to-3D models behind the same MCP generation loop used for images. The most reliable pipeline generates a concept image first, then feeds it to an image-to-3D model; direct text-to-3D models exist (`txt23d` capability) but the image-to-3D catalog is larger and gives more art direction control. Connection and the core generation loop: see the `scenario` skill in this repo. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Step           | Tool                                                               | Notes                                                                                                |
| -------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| Find 3D models | `search` (`target="models"`, `query="image to 3d"`, `public=true`) | Capabilities: `txt23d`, `img23d`, `3d23d`                                                            |
| Inspect inputs | `model_schema_get`                                                 | Always call before `model_run`                                                                       |
| Generate       | `model_run`                                                        | Pass reference images as asset IDs                                                                   |
| Wait           | `jobs_wait`                                                        | Long jobs return `in_progress` with a `job_id`; pass it in `job_ids`; never poll `job_get` in a loop |
| Preview        | `asset_display`                                                    | Interactive GLB/FBX/VOX/OBJ viewer on MCP App hosts                                                  |
| Download       | `asset_download`                                                   | Returns a URL; save with `curl -L`                                                                   |

## Workflow: concept image to game-ready mesh

A realistic sequence for "make a 3D treasure chest prop":

1. Generate the concept: pick a text-to-image model via `search`, then `model_schema_get` and `model_run` with a prompt describing a single centered subject on a plain background. If the user already has a reference, `upload_asset` it (plus `upload_asset_complete` for multipart uploads) and pass the returned asset ID instead.
2. `search` `target="models"`, `query="image to 3d"`, `public=true`. Live results include families like Hunyuan 3D, Meshy, Tripo, and Trellis (for example `model_meshy-7-img23d`); re-discover instead of hardcoding, availability evolves per team.
3. `model_schema_get` on the chosen model. 3D schemas vary widely: single image vs multi-view arrays, polycount targets, PBR toggles, topology choices.
4. `model_run` with `parameters={"image": "asset_xxx", ...}` and `wait=false`, then `jobs_wait` with `job_ids=["<job_id>"]` (it accepts up to 32 ids; re-call it with the returned `pending_job_ids` as `job_ids` if it times out).
5. `asset_display` with the output `asset_id` to preview, then `asset_download` and `curl -L -o chest.glb "<url>"` for engine import.

Multi-view models accept several images of the same subject from different angles; the accepted count varies per model (from 1-4 up to 8), so take it and the image ordering from `model_schema_get` (the first image is usually the front view).

## Inspecting results

`asset_display` renders 3D assets in an interactive viewer (GLB, FBX, VOX, OBJ) on hosts that support MCP Apps; other hosts get the `app_url` dashboard link. The viewer's capture button calls `capture_3d_view`, an app-only tool: it uploads the current camera view as a new image asset and posts the `asset_id` back into the conversation. Use that capture as a reference image for follow-up generations or similarity `search`. Never call `capture_3d_view` yourself; it requires PNG canvas data only the viewer has.

## Refining meshes

3D-to-3D utilities (`3d23d` capability) cover retexturing, remeshing, UV unwrapping, and part segmentation. Find them with `search` `target="models"`, `query="mesh"` or `query="retexture"`. Most take an existing 3D `asset_id` as input.

## Rigging and animation

Rigging is a separate `3d23d` step run on a finished mesh, not a flag on the generator. Find the models with `search` `query="rigging"`.

Body plan picks the model. Humanoid models take the mesh and little else (a front-facing hint, or an approximate height, depending on the model) and infer a biped skeleton. Non-biped work goes to a model exposing `rigType`, whose values cover `quadruped`, `hexapod`, `octopod`, `avian`, `serpentine`, and `aquatic`. Nothing exposes a custom bone hierarchy or a skin-influence count, so export the rigged file and finish weighting or retargeting in a DCC such as Blender or Maya.

Three schema details decide whether the output is usable:

- **Input format.** Rigging models accept GLB, and often OBJ, FBX, or STL. OBJ cannot carry a rig, so the output goes out as GLB or FBX.
- **Size ceiling.** A `max_size` on the file input is the exception rather than the rule (one humanoid rigging model caps at 30 MB). Check the schema before assuming a large mesh needs decimating.
- **Animation versus rig.** Setting the optional `animation` field retargets a preset clip, and by default only the retarget file comes back. Set `includeRiggedModel` to keep the plain rigged mesh too.

When only motion is wanted, motion-transfer video models animate a still character image with no skeleton at all: see `scenario-video`.

## Common mistakes

- Running `model_run` without `model_schema_get`: 3D model parameters differ far more between models than image models do.
- Passing a local file path as an image input: `upload_asset` first, then pass the returned asset ID.
- Hardcoding model IDs: catalogs rotate (live search shows Meshy 6 models tagged deprecated in favor of Meshy 7). Re-discover with `search` each session.
- Pasting raw asset URLs into chat instead of calling `asset_display`.
- Forgetting `-L` with curl: download URLs may redirect before serving the file.
- Promising a named skeleton or a specific influence count: pick the body plan and the export format, then finish the rest in a DCC.
- Sending a biped to a `rigType` model: the enum has no biped value, because humanoids have their own rigging models.
