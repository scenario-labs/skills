---
name: scenario-meshy
description: "Use when creating or refining 3D assets with Meshy models on Scenario via MCP: image-to-3D from one photo or 1-4 angles, text-to-3D, retexturing a GLB, remeshing to a target polycount, UV unwrapping, auto-rigging a humanoid or four-legged character (dog, horse), or applying a library animation clip. Keywords: Meshy 7.1, Meshy T2.5 Smart Topology, Ultra 2K or 4K geometry, PBR maps, texture prompt, triangle or quad topology, low-poly game-ready mesh, biped, quadruped, A-pose, T-pose, GLB."
license: MIT
---

# Scenario Meshy 3D

## Overview

Meshy on Scenario is a toolchain rather than one model. Generators: Meshy 7.1 Image to 3D, Multi
Image to 3D, and Text-to-3D, plus Meshy T2.5 Smart Topology for text or one image. GLB-in, GLB-out
utilities: Retexture, Remesh, UV Unwrap, Rigging, Animation. Work runs as a pipeline: generate a
mesh, refine it, then rig or animate, each stage its own `model_run` whose `model` parameter takes
the 3D asset id the previous stage returned. Discover members with `search` and treat
`model_schema_get` as the contract: members disagree on defaults as basic as `enablePbr` (true on
Image to 3D, Text-to-3D, and Retexture, false on Multi Image and Smart Topology at authoring time).

Members rotate. A hit tagged `Deprecated` also carries `deprecated:<successor id>`: run the
successor, never the deprecated id. At authoring time the Meshy 7 generators pointed to 7.1, and T2
Smart Topology to T2.5.

Connection and the core loop: see the `scenario` skill in this repo; model-agnostic 3D work (viewer,
capture, engine import): the `scenario-3d` skill. If a sibling skill named here is missing from your
available skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

## Quick reference

Members and their traps (names from the live schema, caps at authoring time):

| Member                | Core input                        | Watch for                                                          |
| --------------------- | --------------------------------- | ------------------------------------------------------------------ |
| 7.1 Image to 3D       | `image` (1-4)                     | `geometryResolution` `4k` takes one image only; raw mesh default   |
| 7.1 Multi Image to 3D | `image` (1-4, first = front view) | remeshes in-run; `savePreRemeshedModel` keeps the raw GLB          |
| 7.1 Text-to-3D        | `prompt` (600 chars)              | `shouldRemesh` off by default                                      |
| T2.5 Smart Topology   | `prompt` or one `image`           | builds at `targetPolycount` (100 to 30,000), no remesh step        |
| Retexture             | `model` + one style input         | geometry untouched; keep inputs near 30K polys; `enableOriginalUv` |
| Remesh                | `model`                           | `targetPolycount` 100 to 300,000, `resizeHeight`, `originAt`       |
| UV Unwrap             | `model`                           | rejects meshes above 44,000 faces; Remesh down first               |
| Rigging               | `model`, `rigType`                | `biped` by default; `quadruped` rigs add walk and run clips        |
| Animation             | `model`, `rigType`, `actionId`    | the action's rig type must match `rigType`; auto-rigs first        |

One silent rule runs through every texture control: an image beats text. On the generators
`textureImage` overrides `texturePrompt` (the text is ignored, not blended), and both need
`shouldTexture` on (Text-to-3D has no such toggle: it always textures). Multi Image takes
`textureImages` (1 to 4 views) instead, and rejects them beside `texturePrompt`. Retexture is
stricter: exactly one of `textStylePrompt`, `imageStyle`, or `multiviewImage` (1 to 4 views, first
is the front). `textureResolution` runs 2k, 4k, or 8k; at 8k the PBR maps come back at 4K with no
emission map (Meshy 7.1 never produces one), and 8k pairs only with triangle topology when
remeshing. `poseMode` takes lowercase `"a-pose"` or `"t-pose"`: set one on any biped headed for
rigging. Both poses place arms, so leave it empty for a four-legged animal.

## Generate raw, refine on purpose

Leave `shouldRemesh` off on Meshy 7.1 Image to 3D (its default and the schema's advice): take the
raw mesh at generation, then control polycount with Remesh, which owns `targetPolycount`, topology,
`resizeHeight` in meters (0 keeps scale), and origin placement. On the generator, `targetPolycount`
does nothing while `shouldRemesh` is off. `geometryResolution` buys finer geometry: `2k` and `4k`
add an Ultra pass at extra cost, and `4k` accepts one input image only (Multi Image stops at `2k`).
When hidden sides matter more than micro detail, spend the budget on up to four views instead. Costs
spread widely across members and tiers: `dry_run` before batches.

## Rig or animate, not both

Rigging and Animation are alternatives, not stages. Both take `rigType`:

- `biped`, the default, for a humanoid;
- `quadruped` for a dog, horse, or any four-legged animal.

Animation auto-rigs internally, then applies the clip named by `actionId`, a number from Meshy's
animation library (ids listed at docs.meshy.ai/en/api/animation-library). The action's rig type must
match `rigType`; quadruped actions were ids 1055 and up at authoring time.

- Run Rigging alone for a rigged GLB to drive with your own clips. A quadruped rig already carries
  walk and run clips: an animal that only walks or runs needs no `actionId` and no Animation job.
  Confirm the clips arrived (`asset_get`: `properties.hasAnimations`) before stopping; send a
  missing one to Animation.
- Go straight to Animation for one library clip, optionally setting `postProcessOperation` to
  `change_fps` (`postProcessFps` 24, 25, 30, or 60) or `extract_armature`.
- `skeletonTemplate` (Mixamo, UE5 Mannequin, Unity Humanoid, and others) and `includeFingers` are
  biped-only: keep `meshyrig` on a quadruped. Meshy Rig comes back in centimeters unless
  `includeFingers` is on; every other template comes back in meters.
- `heightMeters` scales the rig: pass the character's real height. Unset, a biped assumes 1.7 and a
  quadruped keeps its own size.

## Worked example: photo to animated character

1. `search` with `target="models"`, `query="meshy"`, `public=true`. Single-image route:
   `model_meshy-7-1-img23d` (a live hit at authoring time: re-discover each session). `search` does
   not flag plan access, and several Meshy members, Animation and Rigging included, sat above the
   entry plans at authoring time. Before paying step 3, `recommend` with `capability="3d23d"` and
   the rig or animation need. If the Rigging or Animation entry you will run carries
   `requires_plan_upgrade`, surface the upgrade or stop at the static mesh: step 5 would otherwise
   fail with a 403 naming the plan (`ModelAccessRestrictedError`) after step 3 was billed.
2. `model_schema_get` with that id, then `upload_asset` the character photo (see the `scenario`
   skill).
3. `model_run` with `dry_run=true` and
   `parameters={"image": ["asset_photo"], "poseMode": "t-pose", "texturePrompt": "worn leather armor, muted palette", "enablePbr": true}`
   for the estimate; then re-run with `wait=false` and `jobs_wait` with the job id, re-called with
   `pending_job_ids` on timeout, never a second `model_run`.
4. `asset_display` the GLB; check silhouette and texture before spending further.
5. `search` for the animation member, `model_schema_get`, then `model_run` with
   `parameters={"model": "<GLB asset id from step 4>", "rigType": "biped", "heightMeters": 1.8, "actionId": <biped id from the library>}`.
6. `jobs_wait`, `asset_display`, then `asset_download` for engine import.

## Common mistakes

- `texturePrompt` next to `textureImage` expecting a blend: the image wins, the text is ignored.
- Two style inputs on Retexture: it takes exactly one of prompt, style image, or multi-view images.
- `geometryResolution: "4k"` with several images: 4K takes a single input image.
- A dog or horse on the default `rigType`: it gets a biped skeleton. Set `quadruped`, and on
  Animation pick a quadruped action.
- UV Unwrap on a dense mesh: above 44,000 faces the job is rejected; Remesh down first.
- Rigging before Animation: Animation rigs by itself, so the chain wastes a job.
- `targetPolycount` on Image to 3D or Text-to-3D with `shouldRemesh` off: it does not apply.
- A bare string where the schema says array: one photo goes as `["asset_x"]`.
- Pricing step 5 with a placeholder asset id: file ids resolve before plan access is checked, so the
  dry run returns 404 and proves neither price nor access.
