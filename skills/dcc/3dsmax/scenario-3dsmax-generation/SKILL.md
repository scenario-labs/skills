---
name: scenario-3dsmax-generation
description: "Use when generated AI assets must land in a 3ds Max scene or a 3ds Max scene must feed a generator: import a GLB or FBX from Scenario, AI props or furniture at the wrong scale, a generated model with too many polygons or no UVs, AI PBR textures or seamless materials, an HDRI or skybox from a site photo, a Gaussian splat world (SPZ, PLY), render enhancement, client variants, season or time-of-day versions, upscale to 4K, a viewport capture, playblast or render turned into an image edit or a video, or choosing between tyDiffusion, Chaos AI Enhancer, Veras, Cosmos AI, Autodesk Assistant and the Scenario MCP. Keywords: Scenario MCP, generative AI in 3ds Max, text to 3D, image to 3D, AI render, make it look like the reference."
license: MIT
---

# 3ds Max Generation

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit. Code status: not yet run in 3ds Max.

Expert level here means knowing where generation earns its place in a 3ds Max job and where it would
break design fidelity, then landing each generated file as a measured, named, traceable scene asset.
The 3ds Max scene stays the source of truth: generation adds mood, context, entourage, surfaces and
concepts on top of it. There is no Scenario plugin for 3ds Max: the agent generates through the
Scenario MCP, moves the file itself, and imports it through a 3ds Max channel. If a sibling skill
named here is missing from your available skills, load it with `skill_get` (Scenario MCP) or ask the
user to install it (https://github.com/scenario-labs/skills#install); unattended, proceed from tool
schemas and flag the gap. **REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop,
toolkit, current-3ds-Max traps). Generation itself follows `scenario` plus the Scenario skill for
the asset type.

## Stance (the expert delta)

1. Geometry, camera, specified materials and light stay in 3ds Max; AI adds mood, context,
   vegetation and atmosphere (Arch Viz Artist, elm00WQ03vw 00:04:05; Chaos Corona, 2WmOd4C5r7s
   00:02:10). An image edit that moves architecture is rejected, not patched.
2. Constrain the generator instead of prompting harder: depth and edge passes, start and end frames,
   reference images, an explicit "do not change the building" line (Jonas Noell, D-1Vy864PtQ
   00:12:17; renderdrop, 1A7uOdk9Sng 00:02:50; 2WmOd4C5r7s 00:01:04).
3. Keep the render's own pixels where truth matters: composite the original glass, reflections and
   architecture over the AI image with ID masks (elm00WQ03vw 00:05:14, 00:07:05).
4. Re-render what the renderer does exactly. Sun direction, time of day and exposure come from 3ds
   Max; match the 3D light to the chosen AI mood before the final render (elm00WQ03vw 00:04:05).
5. Download when a good library asset exists; generate when it is custom, missing or a variant (Nuno
   Silva, i3UbOzrAgLk 00:10:27; Forever Stu, kBo57xFC3ic 00:26:57).
6. A generated mesh is raw input, not a finished asset: arbitrary scale, origin and axes, holes,
   double shells, weak UVs (Top 3D AI, O6G6taj5M14 00:03:35, 00:12:46). Measure it against a known
   dimension before anything else.
7. Explore at low resolution, finish at high; an upscaler adds pixels, not detail (2WmOd4C5r7s
   00:06:38; Matt Hallett, j2qd-kLQY1Q 00:09:30).
8. Agents do setup well and art direction badly: keep a human gate on taste (Arch Viz Artist,
   UuWmWAvB4Y0 00:03:16, 00:05:29; kBo57xFC3ic 00:14:06).

## Where generation fits, and when to refuse

| Asset                                 | Replaces                                              | Scenario skill                             | Refuse or redirect when                                   |
| ------------------------------------- | ----------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------- |
| Props, furniture, decor               | buying, downloading, relinking, unit and pivot fixing | `scenario-3d`                              | client-specified product, or a piece built from drawings  |
| Vegetation, entourage                 | species packs, cutout people                          | `scenario-3d`, `scenario-image`            | species fixed by a planting schedule; near-camera people  |
| PBR textures, materials               | buying sets, maps derived in Photoshop                | `scenario-textures`                        | a supplier sample must be matched: scan or photograph it  |
| HDRI, sky, backplate                  | browsing HDRI packs, photo extension                  | `scenario-skyboxes`                        | physically exact light (daylight study): use Sun and Sky  |
| Gaussian splat context                | scan shoots, context modeling                         | `scenario-3d-worlds`                       | the real site must match; release before 2027.2           |
| Concept, reference images             | web search, moodboards                                | `scenario-image`                           | never as design documentation                             |
| Enhancement, upscale, client variants | Photoshop retouch, re-rendering each option           | `scenario-image`, `scenario-image-editing` | glass, signage, brand items; lighting changes (re-render) |
| Render or viewport to video           | Vantage or full animation renders                     | `scenario-seedance`, `scenario-video`      | final animation with an exact camera path                 |
| Rigs, motion                          | mocap cleanup, hand keys                              | `scenario-3d` (rigging)                    | a studio rig standard (Biped, CAT) is required            |

Refuse generation outright for anything that must match drawings (building shell, joinery): model it
from the CAD (Arch Viz Artist, c3acjyR7j7E 00:03:11). Refuse a generated mesh where subdivision
topology is needed; hand the reference to `scenario-3dsmax-modeling`. Full map with evidence:
[expert-notes.md](references/expert-notes.md).

## Establish first

- **3ds Max release.** It decides the file format (Numbers) and whether splats and the Autodesk 3ds
  Max MCP server exist.
- **Channel**, from `max_env.doctor()`. What each can do with files:

| Channel    | Gets the file                                      | Imports                             | Captures                  |
| ---------- | -------------------------------------------------- | ----------------------------------- | ------------------------- |
| `batch`    | runner downloads first                             | `importFile` with `#noPrompt`       | render only               |
| `mcp-safe` | agent's own shell (no download tool, .NET blocked) | not documented: test one small file | not documented: test once |
| `bridge`   | runner downloads, off the main thread              | yes, inside undo                    | viewport and render       |
| `handoff`  | runner or user                                     | user runs the script                | via the result file       |

- **Renderer** (`rt.renderers.current`), color management mode (OCIO is the default for new scenes
  since 2025) and system units.
- **Deliverable** and what must stay exact: products, drawings, brand, light.
- **Known dimensions** for every generated object (schedule, brief, reference), never guessed.
- **Project folder** on the machine that runs 3ds Max.
- **Scenario scope and spend authorization**, per the `scenario` skill.

## Procedure

1. **Decide fit.** Check the table above. GATE: a one-line decision per asset (generate, download,
   model, or render), with the reason.
2. **Prepare inputs from 3ds Max** (P1). Prepare the scene first: proxies swapped for full geometry,
   hidden helpers off, window glass off, edged faces off, furniture chamfered (zARHVN_XN4U 00:24:34,
   00:28:47). Render the control kit from the locked camera at the deliverable aspect: white clay
   render plus a wire-color or ID mask pass from `scenario-3dsmax-lighting-rendering` (zARHVN_XN4U
   00:31:19). Capture views around an object for multi-view 3D. GATE: aspect equals the render
   output aspect; every capture opened and looked at.
3. **Generate through the Scenario MCP** (P2). Load `scenario` and the type skill; `recommend` with
   quality priority, never a hard-coded model; `model_schema_get`; `dry_run` for batches;
   `model_run`; `jobs_wait`. For 3D, prefer a schema with `outputFormat` and request the format for
   the release. Explore at low resolution (1K) with several variants per prompt and a new seed each
   run; once a take is liked, lock its seed for every variant of it (2WmOd4C5r7s 00:06:38;
   zARHVN_XN4U 00:14:15). Generate high resolution only for the kept result. GATE: `asset_display`
   looked at; subject, anatomy and seam acceptable before download.
4. **Download and record provenance** (P3). Untouched file under `generated/<date>/<kind>/<name>/`,
   sidecar `<file>.scenario.json` with model name and id, prompt, seed, references, job and asset
   ids, date. GATE: file size above zero, extension matches the request, sidecar written.
5. **Land by type.**
   - 3D (P4): import one root per asset, scale uniformly to the known dimension, base on the floor,
     `GEN_` names, `GEN_<kind>` layer, provenance on nodes and in file properties. For 2027.3 GLB,
     pick the material type in the importer dialog (OpenPBR Mtl for Arnold and OpenPBR scenes). The
     dialog offers no VRayMtl or Corona type: in those scenes import as Physical Mtl and hand the
     list to `scenario-3dsmax-materials` for Scene Converter. Check UV stretch: AI UVs are the
     weakest output (O6G6taj5M14 00:12:46). After any mesh rework, regenerate or rebake the texture
     from the original UVs and input images (O6G6taj5M14 00:20:13). GATE: report numbers in range,
     captures checked.
   - Textures (P5): 2 x 2 tile sheet; a seam cross is fixed by a half-size offset, then a masked fix
     of the cross (i3UbOzrAgLk 00:05:01, 00:06:05). Then `scenario-3dsmax-materials` builds the
     material with base color sRGB and data maps Raw. GATE: 3 x 3 plane render at real-world size.
   - Sky (P6): from a site photo, upload it to an image-to-skybox model picked by `recommend`. Seam
     ratio, then `scenario-3dsmax-lighting-rendering` sets the environment, horizon and sun azimuth
     aligned to the photo. GATE: no seam across the meridian; shadows match the photo.
   - Splats (P7): import PLY or SPZ, set Preset, Up Axis and Units. GATE: extent matches a known
     site dimension; renders in Arnold.
6. **Viewport-to-image loop** (P8). Sort each variant first: time of day, sun or exposure is a 3ds
   Max re-render; season, weather and context (snow, fog, foliage) are image edits on that render.
   Render, upload, edit with a prompt that freezes geometry, download, restore protected regions
   from the render, compare with `max_review.compare` and a contact sheet. Protect glass, fabric,
   fog and foggy brick: enhancement fails there; pavement responds best (y2-zbS5n8Ps 00:05:07 to
   00:06:31). Stay near the model's pixel ceiling: send detail crops at one common aspect (4:3) and
   repair the small shift that pixel-count scaling causes with local inpaints (elm00WQ03vw 00:06:02,
   00:08:33). For 4K, render the base at 4K in 3ds Max and composite edited crops onto it (P8, 4K
   delivery). GATE: edges and openings identical inside protected masks.
7. **Viewport-to-video loop** (P9). Render a short sequence from an animated camera for
   video-to-video, or matched start and end frames for still-to-video. Add people to the start frame
   by image edit before animating, and name the character as a reference element where the model
   allows; one start and end pair per transition, never one multi-shot run for several seasons
   (1A7uOdk9Sng 00:05:15, 00:07:26). GATE: contact sheet per take; reject geometry drift and
   auto-inserted cuts.
8. **Report** (P10): files, numbers, captures seen, handoffs, assumptions.

Stays manual: art direction between variants, masks where no ID pass exists, final retouch, take
selection, client sign-off.

## Numbers

| Value                                                    | Relative to                                                       | Source                            |
| -------------------------------------------------------- | ----------------------------------------------------------------- | --------------------------------- |
| GLB import native                                        | 3ds Max 2027.3 and later; FBX before                              | Autodesk 2027.3 docs              |
| Splat import (PLY, SPZ, LCC)                             | 3ds Max 2027.2 and later; Arnold renders them                     | Autodesk docs                     |
| `faceBudget` 1,000 to 2,000,000 triangles                | Scenario's own 3D models with `outputFormat` (schema, 2026-11-24) | Scenario schemas, read 2026-11-24 |
| Quads requested as GLB fail                              | same models; ask FBX for quads                                    | Scenario schemas, read 2026-11-24 |
| Skybox 2:1, up to 3840 px wide, step 16                  | Skybox GPT schema                                                 | Scenario schemas, read 2026-11-24 |
| Skybox upscale adds detail only up to 4096 px            | Scenario Skybox Upscale                                           | Scenario schemas, read 2026-11-24 |
| Seam ratio below 0.3                                     | `gen_runner.seam_ratio`                                           | [added]                           |
| Seamless texture model up to 3840 px, multiples of 16    | color map only                                                    | `scenario-textures`               |
| PBR material model maps 512 to 2048 px, x2 or x4 upscale | five generated maps                                               | Scenario schemas, read 2026-11-24 |
| World model `splatResolution` 100k, 500k, full           | splat density                                                     | `scenario-3d-worlds`              |
| Video-to-video input up to 15 s, 50 MB                   | one 3D-to-video model's schema                                    | Scenario schemas, read 2026-11-24 |
| Auto-rig input under about 700k polygons                 | Mixamo, as one expert used it                                     | O6G6taj5M14 00:22:41              |
| Scale within 2 percent of the known dimension            | landed asset                                                      | [added]                           |

## Quality gates

- Measurable: `land_model` report (scale factor, size per axis, base height, faces, material
  classes); `stats.diff` before and after; seam ratio; splat extent; files and sidecars present;
  scene saved as a new version.
- Visual: `capture.views` of each landed asset beside a known object; a render from the scene
  camera; tile sheets; source and edited image side by side at full size; video contact sheets.
  Checklist in [critique.md](references/critique.md).

## Common mistakes

| Mistake                                        | Symptom                                  | Fix                                                                              |
| ---------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------- |
| Asking for GLB on 2025 or 2026                 | no glTF importer in the list             | request FBX, or install the Khronos plugin                                       |
| Trusting the file's scale                      | chair 100 times too large                | scale to a known dimension, per asset                                            |
| Scaling each mesh part                         | parts drift apart                        | one root, uniform scale about the base                                           |
| Assuming `#noPrompt` reuses the dialog choice  | wrong material class in an OpenPBR scene | doc says default configuration: check classes after the first `#noPrompt` import |
| Mesh reworked, old texture kept                | texture swims or stretches               | regenerate or rebake from the original UVs and inputs                            |
| Time-of-day change by image edit               | shadows disagree with the sun            | re-render the lighting state in 3ds Max                                          |
| Data maps in sRGB                              | washed roughness, wrong bumps            | Raw for normal, roughness, metalness, height                                     |
| Generated LDR sky as the only light            | flat shadows                             | physical sun for light, sky as background                                        |
| Native splat object in a V-Ray or Corona scene | splats missing from the render           | render in Arnold, or use the renderer's own splat loader                         |
| Image edit on the whole frame                  | windows and mullions change              | protect masks, composite the render back                                         |
| Second `model_run` after a `jobs_wait` timeout | double spend                             | re-call `jobs_wait` with `pending_job_ids`                                       |

## Handoffs

- Receives: a scene, camera and deliverable from `scenario-3dsmax-archviz`; masks and ID passes from
  `scenario-3dsmax-lighting-rendering`.
- Delivers: landed meshes with a report to `scenario-3dsmax-game-assets` (retopology, LODs,
  collision, cleanup of AI meshes) or `scenario-3dsmax-modeling` (quad rebuild, subdivision); UVs to
  `scenario-3dsmax-uv-baking`; material list and map files to `scenario-3dsmax-materials`; HDR or
  EXR environment and role to `scenario-3dsmax-lighting-rendering`; rigs and clips to
  `scenario-3dsmax-animation-rigging`; layers and naming conflicts to `scenario-3dsmax-scene`.

## Current 3ds Max notes

- 2027.3: native Khronos glTF import with a material type choice (Scanline, Physical, PBR, glTF,
  Arnold, USD, OpenPBR). No saved doc gives scripted importer option names [verify]. `#noPrompt`
  uses "the default configuration" (importFile doc); whether that follows the last dialog choice is
  not documented.
- 2027.3: the Autodesk 3ds Max MCP server blocks file copy and delete, `setINISetting` and .NET;
  importer options stored in INI cannot be set through it.
- 2027.2: Gaussian splats as Gaussian Splat or Editable Point objects; 2027.3 adds the viewport
  splat shader and PLY export.
- 2026: OpenPBR is the default material; 2025 starts new scenes under OCIO.
- USDZ is export-only: never request it for import.
- In-Max AI tools the user may already own: [in-max-ai-tools.md](references/in-max-ai-tools.md).

## References

- [expert-notes.md](references/expert-notes.md): expert judgment with timestamps, the full fit and
  refusal map, Scenario output facts.
- [procedures.md](references/procedures.md): P1 to P10 with code, channel and checks.
- [critique.md](references/critique.md): self-review rubric with numbers and what to look for in
  captures.
- [gui-paths.md](references/gui-paths.md): menus and dialogs for the same steps.
- [sources.md](references/sources.md): every source with URL and best timestamps.
- [in-max-ai-tools.md](references/in-max-ai-tools.md): AI tools already inside 3ds Max and when to
  use them.
- [gen_runner.py](scripts/gen_runner.py) (runner side) and
  [maxkit_generation.py](scripts/maxkit_generation.py) (inside 3ds Max).
