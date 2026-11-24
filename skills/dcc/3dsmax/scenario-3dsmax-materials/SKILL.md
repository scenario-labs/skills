---
name: scenario-3dsmax-materials
description: "Use when creating, fixing or judging materials in 3ds Max: OpenPBR, Physical, glTF Material, VRayMtl or Corona Physical; building a material from a downloaded or generated PBR texture set; color space, OCIO, ACEScg, sRGB versus Raw maps; 'roughness looks wrong', 'material looks flat or CG', 'too shiny', 'texture is the wrong size', 'normal map looks inverted', 'glass renders black'; wear, dirt, dust, edge wear, curvature, VRayDirt, falloff masks; layered or blend materials, VRayBlendMtl, Corona Layered; glass, car paint, wood, concrete, metal, fabric; Slate Material Editor and compounds; Multi/Sub-Object; Scene Converter for legacy materials; a look-dev scene to compare against a reference photo."
license: MIT
---

# 3ds Max Materials and Look-Dev

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit. Code status: not yet run in 3ds Max.

Expert level here means every map has a declared color role before it is wired, a material is a
stack of physical states rather than one hero shader, and every judgment is made against a
photograph under controlled light. The agent builds by script, resolves class and property names at
run time, and proves each material with numbers and a render, never with a material-editor
thumbnail. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit,
current-3ds-Max traps).

## Stance (the expert delta)

1. **Declare color space before switching anything.** Color maps are sRGB; roughness, gloss,
   metalness, normal, height, AO and masks are Raw. Auto settings only guess, and the guess changes
   between sRGB and ACEScg; roughness is the usual victim because V-Ray fixes normal maps but not
   roughness (Jonas Noell, QuJe2j7SHZ0 00:03:12 to 00:08:53). Set color management before materials
   and lights, or every map needs redoing (Autodesk, dlwDiLsPWgI 00:04:08).
2. **Build states, then mask between them.** Keep the clean base; make a weathered copy and blend it
   back with a mask (Chaos, D-tB0dJp9sU 00:02:31). Wear sits on convex edges, dirt in concave and
   occluded areas, dust on up-facing surfaces, all from geometry masks (Chaos, aHgu1dwjzSo
   00:08:58).
3. **Debug every mask in saturated red, then ship it faint.** Paint the layer red until placement is
   right, then swap in the real color. Final dirt opacities were 25, 20 and 5 percent (Noell,
   38-TGp5QCMY 00:05:09, 00:08:33).
4. **Realism lives in roughness variation.** Vary roughness with a map, never one global value. Keep
   gloss below 1.0 everywhere (D-tB0dJp9sU 00:05:34, 00:06:08). Dielectric reflectivity barely
   varies in reality, scattering does (Autodesk Physical Material doc).
5. **Do a "general feeling" pass before any texture.** Flat colors per large area, no pure white or
   black, walls and floor first because they set the image's warmth and contrast (Ira Ostrovska,
   64vzHYEWedI 00:15:01 to 00:27:26).
6. **Metalness is a switch.** Use 0 or 1; values between are only for masked blends such as rust
   (Arnold, tEUiIBApw-U 00:01:12; V-Ray 7 doc). In OpenPBR, metalness 1 disables transmission and
   subsurface; transmission weight 1 removes subsurface (Adobe OpenPBR FAQ).
7. **Judge against a photo with matched tone.** Match the reference's tone mapping, bloom and glare
   before judging the shader (Gor_cgi, CxHKVjeycv0 00:17:19). Judge bump only in a pre-final render
   under directional light: denoised previews and overcast light hide it (64vzHYEWedI 00:45:59,
   01:33:52).
8. **Weaken a texture with the slot amount, not by editing the bitmap.** Take a close texture and
   color-correct it instead of hunting for the exact one (64vzHYEWedI 00:59:08; Arch Viz Artist,
   870bbZJTRB0 00:03:35).

## Establish first

- **Renderer** (`rt.renderers.current`): it decides the material class. V-Ray GPU or CPU matters:
  VRayMtl OpenPBR mode and diffuse Roughness do not run on GPU.
- **Color management mode**: OCIO with ACEScg is the default for new scenes since 2025. Some Corona
  and V-Ray studios still choose Gamma Workflow 2.2 on purpose (fundamentals note hz07nIgm7EA);
  follow the project, never switch it mid-job. Under 3ds Max OCIO, V-Ray's own color management is
  grayed out (QuJe2j7SHZ0 00:14:43).
- **System units** (all numbers below assume centimeters) and the **real-world size** of each
  texture repeat.
- **Deliverable**: still or animation render, glTF or GLB, FBX to a game engine, USD.
- **UVs**: present and clean, or none (triplanar and box mapping).
- **Reference**: a photo of the real material. No reference means a draft, said as such.
- **Channel**: the lead's `max_env.doctor()`. Builds run through `batch`, `bridge` or `handoff`;
  `mcp-safe` gets the read-only MAXScript audit.

### Material class per renderer and deliverable

| Case                          | Class                                           | Note                                                                                   |
| ----------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------- |
| Arnold (bundled)              | OpenPBR Material                                | Default material since 2026; "OpenPBR Material" from 2025.3                            |
| V-Ray 7                       | VRayMtl                                         | V-Ray features are guaranteed only with V-Ray materials                                |
| V-Ray 7, OpenPBR              | VRayMtl, Shading mode OpenPBR                   | a mode switch on the same material; CPU only; renamed gloss parameters reverse meaning |
| Corona                        | Corona Physical Material                        | Legacy Material only to re-render old scenes                                           |
| glTF or GLB                   | glTF Material                                   | Bitmap Texture is its only map input                                                   |
| FBX to an engine, bake target | Physical Material or PBR Material (Metal/Rough) | Spec/Gloss does not guarantee plausibility                                             |
| USD or MaterialX exchange     | OpenPBR Material                                | USD exporter carries OpenPBR since 2026.1                                              |
| Legacy or mixed scene         | Scene Converter first                           | mental ray nodes are removed, not converted                                            |

## Procedure

1. **Probe (read-only).** Goal: know what is there. Run `audit_materials()` and `audit_textures()`
   from `scripts/maxkit_materials.py`, or `scripts/mxs/materials_audit.ms` through `mcp-safe`; read
   renderer, color mode, units. Dump property names of one instance per class with `discover()`;
   this turns `[verify]` names into facts. GATE: class counts, missing maps and color-space findings
   recorded.
2. **Check the texture set on arrival.** Run `scripts/pbr_set.py <folder>`. It assigns roles and
   color roles from suffixes, and flags gloss versus roughness, DirectX versus OpenGL normals,
   packed ORM, AO, mixed resolutions and a missing real-world size. Tile each color map 2 x 2
   (`seam_preview`) and look for seams. Generated sets get the same check (generation:
   scenario-3dsmax-generation). GATE: every file has a role, one roughness convention, a known
   normal convention, a real-world size.
3. **Pick the class** from the table. Never mix roughness and glossiness conventions inside one
   material.
4. **General feeling pass (scenes).** `general_feeling({"Wall*": (145, 140, 132), ...})` assigns one
   flat material per name group and records the previous assignment. Tune walls and floor first,
   keep fabric reflections low, then ask the lighting sibling for a mood check. GATE: the brightest
   area is the intended focal point when you squint; no albedo at 0 or 255.
5. **Build from the set.** `build_material(target, maps, name, flip_green)` loads each map with the
   right color space (`openBitmap colorSpace:`), wraps the normal map in the renderer's normal node,
   inverts gloss for roughness slots, and reports every slot it resolved. Map real-world size with
   `box_map(node, size_cm)`, or triplanar when UVs are missing. Drive all maps of a material from
   one mapping source so one edit retiles everything (aHgu1dwjzSo 00:03:59). Leave AO out of base
   color for path tracers by default and keep height for close-up displacement. GATE: every slot
   `connected: True`; each `colorSpace` readback is Raw for data and sRGB for color; status is not
   `#forcedDefault`.
6. **Add imperfection in this order:** roughness breakup, then layered states, then color.
   Imperfection maps go into roughness through a mix amount (870bbZJTRB0 00:04:43). For states, use
   VRayBlendMtl, Corona Layered Material or Composite maps with a red dummy in the coat until each
   mask is right. Masks:
   - Wear: curvature convex, inverted, broken by a Dent or noise via Maximum or Multiply at two
     scales (D-tB0dJp9sU 00:08:19; aHgu1dwjzSo 00:07:18).
   - Dirt: VRayDirt with colors swapped and "Consider same object only" on, or the floor blacks out
     the underside; add concave curvature (max color 2.5) for crevices (aHgu1dwjzSo 00:10:04 to
     00:12:24).
   - Streaks: VRayDirt ambient occlusion mode, Bias Z 0.9, radius driven by a streak bitmap
     (38-TGp5QCMY 00:06:54).
   - Dust: Falloff, Towards/Away, World Z (aHgu1dwjzSo 00:12:24).
   - Arnold or renderer-neutral: bake curvature or AO through scenario-3dsmax-uv-baking and use the
     map as a mask. The OSL UVW Randomizer and Bitmap Random Tiling maps replace the V-Ray
     randomizer (osl-map-2027 doc); test-render them first. GATE: no red left (audit
     `debug_red_left`), masks above 1.0 use a color node with a multiplier, not a clamped swatch.
7. **Special materials.** Use the recipes in `references/expert-notes.md`:
   - Glass: thin-walled for single-face panes; transmission depth at object scale when it renders
     dark. VRayMtl Thin-walled needs Translucency SSS; turn on Fog system units scaling, or fog
     depends on object size (V-Ray 7 doc).
   - Car paint: base, flakes and clear coat; Corona Glints replaces OSL flakes in recent versions.
   - Wood: gloss derived from the desaturated diffuse; grain rotation in the shared randomizer.
   - Concrete: triplanar, randomizer and VRayDirt layers.
8. **Judge in look-dev.** `lookdev_rig(25)` makes a 50 cm ball, a floor and a camera named `LKD_*`.
   Lights come from scenario-3dsmax-lighting-rendering and include one raking directional light.
   Render with `capture.render`, then contact-sheet it with the reference
   (`max_review.contact_sheet`). Score with `references/critique.md`. GATE: all critique items pass
   or are listed as known gaps.
9. **Ship.** Re-run both audits. Save the scene as `_v002` and, if asked, the material to a library.
   Never overwrite source textures.

## Numbers

| Value                | Number                                                    | Relative to                           |
| -------------------- | --------------------------------------------------------- | ------------------------------------- |
| Dielectric IOR       | 1.5 (OpenPBR default), 1.52 glass, 1.3 concrete (Noell)   | material                              |
| Metalness            | 0 or 1                                                    | intermediate only under a mask        |
| Gloss ceiling        | below 1.0 everywhere                                      | VRayMtl glossiness mode               |
| Dirt layer opacity   | 25, 20, 5, final edge 3 percent                           | Composite layers, V-Ray concrete      |
| VRayDirt streaks     | radius 150, Bias Z 0.9                                    | cm, facade scale                      |
| Curvature wear       | convex radius 0.5, max color 5 to 10                      | V-Ray, product scale                  |
| VRayEdges rounding   | 3 cm (default 0.1 cm too small)                           | archviz                               |
| Triplanar size       | 300 facade, 15 countertop                                 | cm per repeat                         |
| UVW randomizer       | scale 50 to 150 percent, offset 0 to 1, rotation 0        | stochastic tiling                     |
| Car paint clear coat | 0.85 amount (1.0 washes color), base roughness 0.8        | Corona Physical                       |
| Orange peel bump     | 0.06 to 0.1, noise size 0.35                              | 50 cm shader ball                     |
| Thin film            | 0 to 1 micrometer (OpenPBR); 10 to 2000 nm (Corona)       | unit differs per host                 |
| Abbe number          | 20 default, 10 to 70 typical (OpenPBR); 30 to 60 (Corona) | dispersion off until scale is above 0 |
| Emission             | nits; soft max 1000                                       | OpenPBR                               |
| Wall albedo          | about 145 of 255, warm                                    | general feeling pass                  |

## Quality gates

- **Measurable**:
  - Zero `data_map_as_color`, `colorspace_failed`, `missing_map`, `debug_red_left` and
    `layered_empty_base` findings.
  - No Standard or Legacy classes unless the renderer requires them.
  - Metalness at 0 or 1 where no map is attached; VRayMtl Cutoff above 0.
  - Every Multi/Sub-Object face ID has a sub-material; every normal map passes through a normal
    node.
- **Visual**: judge renders of the rig and the shot, not thumbnails.
  - Close crop and distant crop: dirt subtle at distance, readable close.
  - No repetition on the largest face.
  - Wear only on convex edges and broken up; dirt follows gravity; dust only on top faces.
  - Roughness is not inverted: veins and edges reflect where the reference does.
  - Side by side with the reference at matched exposure.

## Common mistakes

| Mistake                                        | Symptom                                      | Fix                                                                             |
| ---------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------- |
| Roughness map loaded as sRGB                   | glossy patches wrong, worse after ACEScg     | Raw color space or `_raw` tag                                                   |
| Gloss map in a roughness slot                  | shiny where it should be matte               | invert, or switch the material mode                                             |
| Normal map straight into bump                  | lumpy, wrong lighting                        | normal node; flip green for DirectX                                             |
| VRayDirt without same-object-only              | underside black near the floor               | enable it                                                                       |
| One global roughness                           | plastic CG look                              | roughness map plus breakup                                                      |
| Tone mapper on top of OCIO view                | crushed highlights and shadows               | remove VFB tone layers, keep white balance                                      |
| Corona Layered base empty                      | white or cyan render                         | connect a base material                                                         |
| Bump too strong on fabric or bed               | dark pixel noise, "crispy" look              | lower it; check at pre-final resolution                                         |
| Clear coat 1.0 on car paint                    | color washed out                             | 0.85 and a slight absorption tint                                               |
| Gloss values kept across a VRayMtl mode switch | sharp turns blurry, glossy sheen turns matte | OpenPBR mode reverses glossiness; read values before and after (procedures P14) |
| Face IDs without sub-materials                 | black faces                                  | `audit_multisub(node)` and fill the IDs                                         |

## Handoffs

- **Receives** meshes with UVs from scenario-3dsmax-uv-baking and scenario-3dsmax-modeling, a clean
  scene from scenario-3dsmax-scene, and texture sets from scenario-3dsmax-generation (which drives
  `scenario-textures` through the Scenario MCP).
- **Delivers** assigned materials plus the build report to scenario-3dsmax-lighting-rendering
  (look-dev lights, OCIO view, render elements), scenario-3dsmax-archviz (scene-wide passes) and
  scenario-3dsmax-game-assets (glTF or Physical materials for export).
- Bakes of curvature, AO and texture sets go to scenario-3dsmax-uv-baking; library tools and UI go
  to scenario-3dsmax-scripting.

## Current 3ds Max notes

From `sources/3dsmax-version-deltas.md` and the cluster digests.

- OpenPBR is the default material from 2026. It is named "OpenPBR Material" from 2025.3 and "OpenPBR
  Surface" before, so a 2025 scene may default to Physical.
- The viewport draws OpenPBR with a simplified shader. `[OpenPBR] UseSimplifiedViewportShader=0` in
  `CurrentDefaults.ini` gives a closer preview. Viewport captures never judge a material.
- OCIO is the default color mode for new scenes since 2025; 2024 called it a technology preview.
  Bitmap color-space properties are read-only in MAXScript: request the space at load time
  (`openBitmap colorSpace:`).
- The material editor is tone-mapped by color management (QuJe2j7SHZ0 00:14:10). From 2027.1 the
  Slate Preview window has a tone-map choice.
- 2027: the Color Selector eyedropper samples display or scene color; pick scene color for albedo
  values. 2027.2 keeps color settings when the OCIO config path is missing.
- 2027.1: Multi/Sub-Object shows up to 30 sub-materials in the UI.
- MAXtoA 5.9 (2027) changed OpenPBR thin-film energy; old thin-film assets can shift hue.
- Substance for 3ds Max: 3.0.6 in 2027, 3.1.1 with OpenPBR in 2027.3. The 2027.3 glTF importer
  creates OpenPBR, glTF, Physical or Arnold materials.
- MaterialX export from OpenPBR in 2027 is not confirmed by any saved page.
- V-Ray 7 Update 3 turns Keep continuity on for displacement by default; old scenes can change. Set
  displacement in one place only: material or VRayDisplacementMod.
- Corona: Roughness Modulation is the default normals filtering from Corona 11. Glints replaced OSL
  flakes in a recent version; the doc gives no version number.

## References

- [references/expert-notes.md](references/expert-notes.md): principles, recipes and numbers by
  expert, with timestamps.
- [references/procedures.md](references/procedures.md): full code per procedure, channel, status and
  what to check.
- [references/critique.md](references/critique.md): self-review rubric with numbers and capture
  checks.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for the same work, for a
  human or a computer-use agent.
- [references/sources.md](references/sources.md): every source with URL, expert and best timestamps.
- [scripts/pbr_set.py](scripts/pbr_set.py): runner-side arrival check and tagged copy of a texture
  set.
- [scripts/maxkit_materials.py](scripts/maxkit_materials.py): in-Max builders and audits (inline
  through `max_wrap`).
- [scripts/mxs/materials_audit.ms](scripts/mxs/materials_audit.ms): read-only audit for the
  `mcp-safe` channel.
