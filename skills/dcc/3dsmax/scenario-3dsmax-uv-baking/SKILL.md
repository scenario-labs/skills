---
name: scenario-3dsmax-uv-baking
description: "Use when UVs, mapping or baking in 3ds Max are the task or the problem: unwrap a model, Unwrap UVW seams, Peel, Quick Peel, Reset Peel, relax, stitch, pack UVs, texel density, padding, UV coverage, a lightmap UV channel, map channels, UVW Map and real-world map size, texture looks stretched or blurry, texture repeats or tiles visibly, triplanar or UVW randomizer in V-Ray or Corona, bake high to low, Bake to Texture or Render to Texture, Projection modifier and cage, ray misses, normal map looks wrong, seams or flares in the normal map, MikkT, green channel flip, bake AO, curvature or PBR maps for Unreal, Unity or glTF, Shell material after a bake, preparing a model for Substance Painter texture sets, or checking the UVs of an imported or generated mesh."
license: MIT
---

# 3ds Max UV and Bake Artist

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit. Code status: not yet run in 3ds Max.

Expert level here means every UV and bake decision is measured: texel density in px/cm against a
target, padding in pixels at the final size, no unintended overlap, and a diagnostic bake before the
final one. The core stance: fix what a parameter can fix, keep the original material and UVs
recoverable, and judge with a checker, a red ray-miss color and a lit capture, never with the
finished texture alone.

If a sibling skill named here is missing from your available skills, load it with `skill_get`
(Scenario MCP) or ask the user to install it (https://github.com/scenario-labs/skills#install);
unattended, proceed from tool schemas and flag the gap.

**REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit, current-3ds-Max
traps).

## Stance (the expert delta)

1. **Texel density is px/cm of surface, not visual quality.** Pick it from camera distance: 20.48
   weapon in hand, 10.24 first person, 5.12 third person, 2.56 top-down (Huge Menace, sR1sAWWT2x8
   00:12:28). A blurry bake on one shell means too few pixels there, not a bake error (Abe Leal,
   2gv1jYDAoJc 00:21:47).
2. **Padding is never zero.** Mipmaps bleed neighbors: 8 px between shells at 2K (2gv1jYDAoJc
   00:14:46). Bake output size must equal the texture size the UVs were planned for (00:21:12).
3. **Since 3ds Max 2023, Peel behaves differently.** Unfold3D is the default solver; it adds its own
   pins and "always produces a result, even an undesirable one" (Unwrap UVW doc). Reset Peel no
   longer joins islands unless the solver is LSCM, and Peel packs every time unless Pack is set to
   Recursive Packing (Jordan Younie, RcObIKoUTvE 00:00:33, 00:02:20).
4. **Hard edges and UV seams travel together on a baked asset.** A hard edge without a UV split
   leaves a line in the normal map (game-assets digest, SKXrtpTIsNI 00:37:06). Box shapes get their
   corners cut: more seams, far less stretch (2gv1jYDAoJc 00:07:51).
5. **Bake settings and viewport settings are a pair.** Normal Map Space, MikkT and per-pixel
   bitangent in Bake to Texture must match Customize > Preferences > General > Normal Bump Mode, or
   a correct map displays wrong (Ken LaRue, Autodesk, -SMLc0od_5Y 00:03:19; BTT doc).
6. **Diagnose before the final bake.** First bake with Ray Miss Color set to the diagnostic color;
   misses show as flat red (BTT doc). Use a cage only when high and low do not line up; otherwise
   Raytrace with Max Ray Distance 10.0 "works in most cases" (-SMLc0od_5Y 00:01:38).
7. **Bake non-destructively.** Output To > Create New Material keeps the original inside a Shell
   material so you can edit the source and re-bake (Autodesk, 2IhYmRsKZ4Q 00:02:30).
8. **Archviz surfaces often need no unwrap.** Real-world sized UVW Map plus a randomizer or
   triplanar removes repetition at render time (Jonas Noell, 6FalgHWkhKE).

## Establish first

- **Deliverable:** engine (Unreal, Unity, glTF), Substance Painter round trip, or a 3ds Max render.
  This decides unwrap versus triplanar, tangent basis and the green channel. For an engine, ask
  whether lighting is baked (lightmaps) or fully dynamic (Lumen in Unreal): it decides Stage 6.
- **Camera class and texture budget:** texel density target and maximum map size. Default to 5.12
  px/cm and 2048 when unstated, and say so.
- **System units** (`audit.units`): texel density needs centimeters. Reset XForm before measuring;
  polyop areas ignore node scale.
- **Renderer** (`rt.renderers.current`): Arnold is the bundled default and the BTT doc's
  recommendation for albedo, metalness, roughness and AO. V-Ray or Corona decide which triplanar and
  randomizer nodes exist.
- **Which map channel feeds which material** (channel 1 for textures, 2 for lightmaps by convention
  [added]).
- **Channel** from `max_env.doctor()`. The Unwrap UVW editor is interactive; most hand UV work is
  GUI-only.
- **Generated meshes** arrive through scenario-3dsmax-generation: treat their UVs as unverified and
  run Stage 1 before anything else.

## Procedure

Full code for each stage is in [references/procedures.md](references/procedures.md); GUI paths in
[references/gui-paths.md](references/gui-paths.md).

1. **Audit the existing UVs.** Run `uv_audit(node, channel, tex_size, target_td)` from
   `scripts/maxkit_uv.py`, prepended to the chunk and wrapped with
   `max_wrap(kit=["audit", "capture"])` (batch, bridge, handoff); `scripts/mxs/maxkit_uv.ms` per
   object on mcp-safe. Capture a checker view with `capture.views`. GATE: report of shells, overlap,
   flipped faces, coverage, texel density spread, minimum gap. Adding UVW Map over textured UVs
   destroys them, so inspect first (fundamentals-scene digest).
2. **Choose the mapping strategy.** Unwrap if maps leave 3ds Max or the asset is baked. UVW Map with
   Real-World Map Size for architecture and tiling materials. Triplanar plus a randomizer when UVs
   are bad or absent and the asset stays in V-Ray or Corona. Projected decals for graphics and
   imperfections. GATE: strategy and reason written in the report.
3. **Prepare the low poly.** Delete faces the camera never sees (2gv1jYDAoJc 00:01:56). Use one
   material per texture set, named for the set: the material name becomes the Painter texture set
   (Adobe, xuLRnFBvLyI 00:00:54). Hard edges are decided with scenario-3dsmax-game-assets. GATE: one
   material ID per intended set, node scale 1.
4. **Seams and unfold (GUI-led).** Detach parts, cut seams on real breaks and sewing lines, Peel,
   Relax By Polygon Angles (Numbers), Straighten grid-like shells only, Stitch continuing seams
   (Arch Viz Artist, aMCWmnml0o0 00:02:45, 00:06:33, 00:12:53). Set the solver and pack method first
   (Stance 3). Scripted substitute: Flatten by angle or smoothing group, then Pack. Unwrap UVW
   script names are `[verify]`: run the P0 interface dump first. GATE: checker squares square and
   straight in a capture; audit shows no folds.
5. **Scale and pack.** Rescale for uniform density, raise deliberately for hero detail. Pack per
   texture set (xuLRnFBvLyI) with Rescale and Rotate on, and padding converted from pixels
   (`td_plan.py --pad-px 8 --size 2048` gives 0.0039). GATE: texel density within ±15% of target
   [added tolerance], min gap ≥ 8 px at 2K, coverage ≥ 75% for a shipped game asset (sR1sAWWT2x8
   00:16:44), or a written reason.
6. **Lightmap channel only when the engine bakes light.** Fully dynamic lighting (Lumen): none,
   lightmap generation off at import (qsV4k09kPV8 00:03:32). Unreal can generate them on import.
   Hand-made: new Unwrap UVW on channel 2, no overlap, selected through a Datasmith Attributes
   Modifier or Light Map Coordinate Index (Datasmith doc). GATE: channel 2 audit has zero overlap
   and zero mirrored stacks.
7. **Set up the bake.** Rendering > Bake to Texture, or the `BakeToTexture` interface (P6, P7).
   Select the low poly, add maps, pick the high poly in Projected From (this creates a Projection
   modifier), set Image Size, Padding and File Type. Engine normals: Tangent, MikkT, Output into
   Normal Bump off (HL doc). Per-pixel bitangent: Unity off (BTT doc), "most engines" on (HL doc);
   no source gives Unreal's, so bake both on a test bevel and compare in the target (P7). Curvature:
   no common map; use Override or Arnold_map_override (P7). Rounded Corners rounds sharp edges
   without a high poly (BTT doc). GATE: every queued map `bakeable` true and `frozen` false.
8. **Diagnostic bake, then final.** Set `projectionRayMissColorType = 2`, bake at reduced size, read
   the maps (`scripts/bake_check.py`, P9) and a lit capture. Fix misses with cage push or ray
   distance. Several high sources in one map: `projectionHitOnlyMatchingMatID` true with matching
   material IDs, no exploded bake needed (BTT, MBT). Include Working Model (legacy RTT) fixes misses
   only when the low does not occlude the high (PO doc). Seams: padding and seam splits. Flares:
   Flip Horizontal on the flipped shells (TS doc). Rebake: miss color 0, full size. GATE: no
   diagnostic-color pixels; critique rubric passed.
9. **Deliver.** `BakeToTexture.clearShellKeepBaked nodes:#(obj)` on an export copy. Hand maps and
   the material to scenario-3dsmax-materials, or the FBX export to scenario-3dsmax-game-assets.
   Unreal's FBX import connects only Color and Normal and does not import AO: wire the rest by hand
   (Unreal FBX doc). GATE: file list with sizes, bit depth, color space (Data Image or Raw for
   normals and masks).

## Numbers

| Value                  | Number                                                | Relative to                               |
| ---------------------- | ----------------------------------------------------- | ----------------------------------------- |
| Texel density targets  | 20.48 / 10.24 / 5.12 / 2.56 px/cm                     | weapon, FPS, TPS, top-down (sR1sAWWT2x8)  |
| Padding                | 8 px shell, 8 px tile                                 | 2048 map (2gv1jYDAoJc); scale with size   |
| UV utilization         | ≥ 75%                                                 | shipped game asset (sR1sAWWT2x8)          |
| Flatten defaults       | angle 60, spacing 0.02, normalize, rotate             | Unwrap UVW doc                            |
| Pack padding in a demo | 0.02 UV                                               | Painter prep (xuLRnFBvLyI)                |
| Relax                  | Polygon Angles, 100 iterations, Amount 1.0, Stretch 0 | aMCWmnml0o0 frame 00:03:09                |
| Weld threshold         | 0.01 (UV units)                                       | Unwrap UVW doc                            |
| Max Ray Distance       | 10.0 default, 0 to 10000                              | scene units (BTT doc, MBT)                |
| BTT defaults seen      | 2048, padding 2, PNG, UV channel 1                    | 2IhYmRsKZ4Q frame 00:01:46                |
| edgePadding range      | 0 to 128 px                                           | MBT                                       |
| Triplanar blend        | V-Ray 0.1 default; Corona Blending 0.25               | VTT doc, CMR doc                          |
| Stochastic tile blend  | 0.01 (bricks) to 0.2 (ground)                         | VUR doc, 6FalgHWkhKE                      |
| Brick tile height      | 56 courses x 7 cm ≈ 400 cm                            | millimeter scene: type 4000 (zLDLOSx-qL0) |
| Randomizer row step    | Step = 1 / rows (7 rows: 0.143)                       | Corona Mapping Randomizer doc             |

## Quality gates

- **Measurable:** zero cross-shell overlap on bake channels. Mirrored halves offset on W on purpose
  (TS doc). Flipped faces only where mirroring is intended. Stage 5 density, gap and coverage
  numbers. Every BTT map `bakeable`, image size equal to the planned size, edgePadding at least 2.
  No Edit Normals modifier on the low poly (TS doc). Normal options equal to the target's settings.
- **Visual:** checker capture with square, unbanded squares. Normal map viewed on the model under a
  raking light at 2 or 3 angles: no flares, no seams, no wavy cylinders. AO without contact from
  foreign parts. Judge randomizers and triplanar in an interactive render: they do not show in the
  viewport (4o3j7PBHLrQ 00:03:23). Full rubric: [references/critique.md](references/critique.md).

## Common mistakes

| Mistake                                  | Symptom                                   | Fix                                                                             |
| ---------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------- |
| Reset Peel with Unfold3D                 | islands stay separate, layout repacks     | Peel solver LSCM; Pack method Recursive Packing, then Cancel                    |
| Bake size below texture size             | pixelated bake                            | match Image Size to the planned map                                             |
| Re-tuning the bake for a blurry shell    | still blurry                              | raise density there; minimal ray depth and sampling, check the filter (BTT doc) |
| Two parts intersecting                   | hard line survives the normal bake        | boolean merge and soften, or accept (2gv1jYDAoJc 00:23:26)                      |
| Hard edge with no UV split               | line along the edge in the normal map     | split the UVs on every hard edge                                                |
| Two materials on the low poly            | two texture sets in Painter               | one material per set, stray face fixed                                          |
| BTT and viewport normal settings differ  | map looks inverted or faceted in viewport | set both MikkT and the same per-pixel setting                                   |
| Cage too far                             | neighbors baked into a part               | push only until misses vanish; explode parts                                    |
| Rays parallel to detail                  | cylinder end detail missing               | move that cage end out and scale in, or Break low-res verts (TS doc)            |
| Overlapping mirrored UVs                 | garbage on one half                       | offset one half on W, or bake unique then mirror                                |
| UVW Map channel changed                  | edits on the other channel overwritten    | save first; the change copies silently (UVW Map doc)                            |
| Real-World Map Size on one side only     | texture far too big or small              | enable it in the modifier and the bitmap                                        |
| Whole-number randomizer offsets          | no visible change                         | use fractional ranges or Step 1/rows                                            |
| Randomizer rotation on a normal map      | wrong lighting direction                  | no rotation on the normal path, or check in render                              |
| Triplanar fed by the randomizer reversed | mapping ignored                           | randomizer goes into the triplanar (CMR doc)                                    |
| Linked VRayBitmaps share blur            | soft normal map                           | lower blur on the normal bitmap (6FalgHWkhKE 00:13:02)                          |
| Step copied between renderers            | different pattern                         | Corona Step is an increment, V-Ray Step a count (CMR, VUR docs)                 |

## Handoffs

- **Receives** low and high meshes, hard-edge decisions and LODs from scenario-3dsmax-game-assets,
  finished topology from scenario-3dsmax-modeling, and generated meshes (Stage 1 first) from
  scenario-3dsmax-generation.
- **Delivers** baked map files and a Shell or flattened material to scenario-3dsmax-materials.
  Delivers an export-ready mesh with clean channels to scenario-3dsmax-game-assets for FBX. Delivers
  real-world mapping and randomizers on archviz surfaces to scenario-3dsmax-archviz.
- **Asks** scenario-3dsmax-lighting-rendering for renderer and color management setup, and
  scenario-3dsmax-scripting for batch tools over many files.
- **Generated textures:** tileable PBR sets from scenario-3dsmax-generation; this skill sets their
  scale and randomization.

## Current 3ds Max notes

Checked against the version deltas (UVs and baking) and the cluster docs.

- Peel and Pack default to Unfold3D (2023 and later; same on 2025 and 2026), with LSCM and legacy
  Recursive Packing selectable. Peel auto-packs.
- OpenPBR is the default material since 2026. For Create New Material, read the slot names with
  `getTargetMaterialSlots`; they differ from the 2021 PBR Metal/Rough names. 2027.3 ships the
  Substance plug-in 3.1.1 with OpenPBR.
- Bake to Texture (2021 and later) replaces Render to Texture for new work (queue, PBR outputs,
  Output To, UDIM). Render to Texture and `render rendertype:#bakeSelected` remain for scripted
  legacy bakes on Scanline.
- Follow the 2027 BTT page (Arnold, Render Setup F10) over the high-to-low page (Scanline, F1);
  Scanline only for legacy Height or Lighting elements.
- 2027 MAXScript adds `BakeToOneAll` and `BakeToOneSel` render types with `bakeToOneMaps`,
  `numDilations` and `bakesize` (MAXScript what's new 2027). Their behavior is undocumented in the
  saved pages: `[verify]`.
- OCIO is the default color management since 2025. Bake normals, masks and roughness as Data Image
  (Raw).
- `BakeToTexture.getCompatibleMapTypes()` is incomplete until `showDialog()` has run. Batch mode has
  no dialogs, so a headless BTT bake is unproven. The legacy `render rendertype:#bakeSelected` path
  is the batch fallback.
- On the Autodesk 3ds Max MCP server (Safe level), whether `BakeToTexture.bake()` and bitmap writes
  pass is not documented.

## References

- [references/procedures.md](references/procedures.md): full code for audit, unwrap, UVW Map, bakes,
  randomizers, Painter hand-off.
- [references/critique.md](references/critique.md): the self-review rubric with numbers and capture
  checks.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps and
  disagreements.
- [references/gui-paths.md](references/gui-paths.md): menus and dialog settings for every procedure.
- [references/sources.md](references/sources.md): every video and doc, what each is best for.
- [scripts/maxkit_uv.py](scripts/maxkit_uv.py): UV audit inside 3ds Max (shells, density, overlap,
  padding, flipped faces).
- [scripts/mxs/maxkit_uv.ms](scripts/mxs/maxkit_uv.ms): per-object MAXScript twin for mcp-safe.
- [scripts/td_plan.py](scripts/td_plan.py): runner-side texel density, texture size and padding
  planner.
- [scripts/bake_check.py](scripts/bake_check.py): runner-side read of baked maps (Pillow): size,
  diagnostic ray-miss share, normal map mean and negative-Z share, JSON per file.
