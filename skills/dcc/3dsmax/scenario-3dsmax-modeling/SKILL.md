---
name: scenario-3dsmax-modeling
description: "Use when modeling in 3ds Max: Editable Poly, the modifier stack, hard-surface cuts with the Boolean modifier, chamfer or Smart Bevel pinching after a boolean, OpenVDB merges, OpenSubdiv or TurboSmooth stretching, creases and crease sets, support loops, the Retopology modifier failing or giving messy quads, cleaning CAD or scan meshes into quads, Symmetry, Array, Conform, Displace wrinkles, splines with Loft, Sweep, Lathe or pipes, or furniture and product models from reference photos (chair, sofa cushion, tap, headphones). Also when users say 'model this from the reference', 'boolean leaves artifacts', 'the bevel looks wrong', 'subdivision ruins my edges', 'retopologize this', 'make it non-destructive'."
license: MIT
---

# 3ds Max modeling

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit.

**Status: not yet run in 3ds Max.** Nothing here has been executed in the application. Code is
checked against the cited documentation, and unconfirmed API names carry a bracketed `verify` mark:
confirm each in the live session first.

Expert modeling in 3ds Max means a short, readable modifier stack that stays live until the look is
approved, with every problem fixed at the lowest level that causes it. An agent has no mouse: it
builds stacks, sets parameters and selects by rule, and it hands the few truly interactive moves to
the user with an exact GUI path. If a sibling skill named here is missing from your available
skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit,
current-3ds-Max traps).

## Stance (the expert delta)

1. **Fix it at the bottom of the stack.** Holes after a merge are fixed in the Star or Loft below,
   not in the mesh above; the whole stack updates (Todd D, uDfhmKCdR0U 00:13:46). Collapse only a
   copy, and only for a local fix.
2. **The Boolean already selected your edges.** It outputs the intersection edges as a selection:
   Poly Select passes it to Chamfer with Selection set to Selected Edges. Then an empty Poly Select
   clears it, or the next Chamfer re-bevels the old edges (Autodesk, TEz7tBiRrXc 00:04:10,
   00:04:40). In 2027, Smart Bevel above the Boolean replaces this chain on dense intersections,
   with width in world units (Autodesk, lDpcfhxP3qU 00:01:07).
3. **Cutters are designed, not defaulted.** A Create-panel cylinder has 18 sides and 5 height
   segments; set 1 height segment, and 6 to 8 sides if the result will be subdivided (Arrimus,
   fXI2MJ7Bw2k 00:02:57; Todd D, yx-lpHy8yPs 00:01:39). Box cutters stay 1x1x1 (yx-lpHy8yPs
   00:12:41).
4. **Retopology quality is capped by the source.** A 14-segment sphere cannot give clean 255-face
   loops; a 64-segment one can (fXI2MJ7Bw2k 00:17:00). Fix smoothing groups by angle, halve
   symmetric parts with Slice, and Subdivide to even triangles before ReForm (Autodesk, sKEu2Gs3G_U
   00:00:21 to 00:02:22).
5. **Creases beat support loops on subdivision cages, within limits.** OpenSubdiv reads crease
   values from below it, so Crease and CreaseSet sit between the base and OpenSubdiv (Jake Denham,
   QIPOLr4j3lM 00:12:41). An all-creased box with no loops still stretches; add loops, then
   recrease, since new loops start at 0 (Adam Z, UpBbEXkqeuw 00:01:42).
6. **OpenVDB voxel size is relative to the object.** The default 1.0 destroyed a 13 cm object; 0.1
   worked. Every new Boolean resets to Mesh and 1.0 (uDfhmKCdR0U 00:12:03, 00:12:38). Retopology
   after VDB loses edges; Conform with Closest Point onto the original recovers them (Autodesk,
   sRLKiz4HSgA 00:08:55).
7. **Choose the cut method by what comes after.** A subdivided low-poly cage that needs
   hand-controlled flow: Todd's floater cut (attach a simple cutter, push its top face through,
   weld). Anything that must stay editable, or a complex cutter: the Boolean modifier (yx-lpHy8yPs
   00:12:10; QIPOLr4j3lM 00:06:41).
8. **Judge the smoothed result, not the cage.** Extra edges added for noise or seams harden the
   smoothed surface (Adam Z, 75_n7o0u8sw 00:04:41, 00:06:52).

## Establish first

- **Units and scale:** system unit and display unit (default assumption here: centimeters). Every
  voxel, chamfer, weld threshold and Smart Bevel width is a distance. If the scene is unset, stop
  and hand to scenario-3dsmax-scene.
- **Deliverable:** close-up render (subdivision, render iterations), game asset (mid-poly with Smart
  Bevel and Weighted Normals, handed to scenario-3dsmax-game-assets), or archviz prop (light,
  Chamfer without subdivision).
- **References:** photos or drawings, and one real dimension to scale them (P10).
- **Release:** 2027.x enables Smart Bevel and the 2027 Boolean welding. On 2025 or 2026, use the
  Poly Select plus Chamfer chain.
- **Channel:** `bridge` or `handoff` for captures and Retopology Compute; `batch` for building and
  auditing stacks on saved files; `mcp-safe` takes MAXScript only (twins in `scripts/mxs/`).
- **What may change:** the user's file is never overwritten. Save as `_v002`, and work on a copy of
  any node you collapse.

## What an agent can and cannot do here

- **Scriptable:** adding, ordering and setting modifiers (names from P1); selecting edges by rule
  (face angle, smoothing groups, the Boolean's output selection); Boolean operands through
  `AppendOperand` [verify].
- **GUI only, handed to the user with a path:** Retopology Compute, Swift Loop, Cut, Set Flow, Loop
  Regularizer, Shift-drag floater cuts, Loft Scale and Twist curves, Data Channel presets. Decide
  Capture vs Live Reference before picking an operand.
- Full table with substitutes: [references/gui-paths.md](references/gui-paths.md).

## Procedure

Each stage runs as a chunk through `max_wrap.wrap`, inside one undo record, and ends with its gate.
Name the channel of every chunk in your plan. Full code is in
[references/procedures.md](references/procedures.md).

1. **Probe names (P1).** Goal: real class and property names for this build. How: create each
   modifier and list `getPropNames` plus interfaces; for operands and enums, ask for one
   macro-recorder line (P1b). GATE: every family you need resolves; `[verify]` names in later chunks
   are replaced.
2. **Set up references and scale (P10).** Goal: planes at the image aspect, scaled to one known real
   dimension (Tim Bergholz, tP7FD4l-qus 00:02:46). GATE: plane size printed in cm matches the known
   dimension; front capture lines up with the reference.
3. **Block out the cage.** Goal: primitives or splines at real size, few segments, even quads. How:
   Box, Cylinder, Plane by script; model half under Symmetry (tP7FD4l-qus 00:10:04). Shape broad
   masses with FFD below the smoothing modifier (75_n7o0u8sw 00:07:25). GATE: `stack_audit` clean;
   quad ratio near 1 on the cage; silhouette within the reference.
4. **Cut and bevel hard-surface details (P2).** Goal: Booleans with designed cutters, bevels only on
   intersections. How: Boolean per cutter, then Smart Bevel (2027) or Poly Select, Chamfer (Limit
   Effect on), empty Poly Select, with chamfer widths descending as features shrink. Build the
   surrounding loops first, or turn on Imprint to insert intersection edges without removing faces
   (fXI2MJ7Bw2k 00:02:26; boolean doc). Round openings: Loop Regularizer, then Set Flow (GUI,
   0jXxaGKuW6Y 00:03:30). GATE: operands closed and welded; no `selection-not-cleared`; after every
   push-through cut, weldable verts 0 and no doubled edges before subdividing (yx-lpHy8yPs 00:04:23,
   00:04:55); Edged Faces capture shows even bevel width and no pinch.
5. **Organic merges (P3).** Goal: one watertight form from overlapping parts. How: Boolean Method
   OpenVDB, voxel near 1/100 of the largest side [added], then Retopology, then Conform Closest
   Point to the original. GATE: voxel ratio between 50 and 500; open edges 0; face count near
   target.
6. **Clean imported or generated meshes (P4).** Goal: quads from CAD, scan or generated triangles.
   How: the P4 stack, Smooth 30 to Retopology to Symmetry, then Smooth 35, Chamfer Radial,
   OpenSubdiv (HhUMdy-0kSI 00:01:10 to 00:04:44). GATE: source has at least 2x the target faces
   [added]; Compute reports no failed elements; loops follow the form.
7. **Subdivision and creases (P5).** Goal: crisp edges without loop clutter. How: creases by
   face-angle rule, or one named CreaseSet per edge group with its own value (also eases UVW seams,
   UpBbEXkqeuw 00:05:42); OpenSubdiv iterations 1 viewport, 2 render, Chaikin for mixed weights.
   Fast support loop: extrude the polygon ring with Local Normal at 0 (yx-lpHy8yPs 00:06:35). GATE:
   captures at iterations 1 and 2 show no stretching on flats and no soft corners.
8. **Splines, shells and soft detail (P6, P6b, P7, P8).** Goal: frames, pipes and lathed parts as
   live splines; tapered spouts as a Loft with a Scale deformation (uDfhmKCdR0U 00:07:07);
   even-thickness parts as a one-sided surface plus Shell; fabric wrinkles as stacked Displace, the
   same modifier pasted onto cushion and piping; stitching as Array along a Create Shape From
   Selection spline (QIPOLr4j3lM 00:00:52); subtle sag with Affect Region (QIPOLr4j3lM 00:00:33).
   GATE: bends round at hero distance; no gizmo outlines in the test render; no circular dependency.
9. **Verify and hand off (P9).** Goal: numbers then pictures. How: `mesh_checks`, `stack_audit`,
   four-view captures at two subdivision levels, one contact sheet. GATE:
   [references/critique.md](references/critique.md) passes; save `_v002`; state what stays live.

## Numbers

| Item                         | Value                                                                       | Relative to                                          |
| ---------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------- |
| Cylinder cutter              | 1 height seg; 6 to 8 sides if subdivided, more if chamfered only            | Create default 18 sides, 5 height segs               |
| Box cutter                   | 1x1x1 segments                                                              | floater or Boolean                                   |
| Chamfer chain widths         | 0.3, 0.2, 0.2, 0.1, descending                                              | scene units, feature size (TEz7tBiRrXc)              |
| Chamfer screen defaults      | Uniform, Fixed 1.0 cm, 1 seg, Depth 0.5, smooth 30                          | cm scene (QIPOLr4j3lM frame 00:09:40)                |
| Chamfer/Smart Bevel depth    | 1.0 sharp, 0 flat, negative concave                                         | dimensionless (chamfer doc; lDpcfhxP3qU)             |
| Smart Bevel segments         | start at 1, add only for highlight roll                                     | geometry cost                                        |
| OpenVDB voxel                | start at largest side / 100 [added]; 0.1 on a 13 cm part; 0.2 on a CAD part | object size, default 1.0                             |
| OpenSubdiv iterations        | 1 while editing, 2 final; range 0 to 6, render 0 to 10                      | viewport vs render (doc)                             |
| Crease                       | 1.0 hard; low values (0.14 shown) soft                                      | per edge or per set                                  |
| Retopology face count        | default 5,000; 8,197 hero prop; 25,000 CAD part                             | source must hold 2x [added]                          |
| ReForm tuning                | Regularize 1, Adaptivity 0 for straighter loops                             | defaults 0.5 (Pg2Nm-fwyME frames)                    |
| Smoothing by angle           | 30 before Retopology; 35 before Chamfer                                     | degrees                                              |
| Subdivide before ReForm      | Adaptive, edge length 2                                                     | scene units (HhUMdy-0kSI)                            |
| Symmetry weld threshold      | 0.1 cm default; 0.01 cm to avoid stray welds                                | cm (tP7FD4l-qus)                                     |
| Bend receiver                | at least 16 edges along the bend                                            | magazine curve (tP7FD4l-qus 00:55:32)                |
| Conform Volume               | Influence 10%, Falloff 25%                                                  | scan alignment (sRLKiz4HSgA)                         |
| Relax after Conform          | Value 1.0, 100 to 256 iterations                                            | soft blend                                           |
| Data Channel Smooth on seams | 32 iterations, amount 1.0                                                   | soft-selection seam                                  |
| Array scatter                | Remove 75%, distribution source about 2,000 faces                           | retopologized reference                              |
| Spline tube                  | radial thickness and 16 sides for close-ups                                 | 3dJ1VLgeKmM frame                                    |
| Shell on a one-sided drape   | Inner 0, Outer 0.4 cm, then TurboSmooth 2                                   | cm (QIPOLr4j3lM frame 00:12:20, value marked unsure) |
| Stitch Array on a spline     | Position 0.7, axis Y                                                        | QIPOLr4j3lM 00:00:52                                 |

## Quality gates

Measurable (P9 and `maxkit_modeling`):

- Open edges 0 unless the part is meant to be open (Cookie makes open meshes by design).
- Weldable verts at 0.001 cm: 0. N-gons: 0 on subdivided parts; at most a few deliberate poles.
  Triangles on dense curved areas pass; chasing all-quad rarely pays (fXI2MJ7Bw2k 00:14:25).
- `stack_audit`: no crease above subdivision, no FFD above smoothing, no Chamfer selection leaking
  into a later Boolean, viewport iterations at most 2.
- Retopology: face count within about 10 percent of target [added]; source at least 2x target.
- Dimensions: bounding box against the real measurement.

Visual (one contact sheet, four views, iterations 1 and 2, Edged Faces):

- Loops run continuously around cutouts; no fan of thin triangles at a Boolean seam.
- Flat faces read flat; corners hold; no pinch where a pole meets a highlight.
- Silhouette matches the reference capture; wrinkles fade without gizmo outlines.

## Common mistakes

| Mistake                                                | Symptom                                       | Fix                                                                                                             |
| ------------------------------------------------------ | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Chamfer straight on Boolean output                     | pinching, uneven width (lDpcfhxP3qU 00:00:42) | Smart Bevel above the Boolean, or retopologize first (HhUMdy-0kSI)                                              |
| Selection not cleared after Chamfer                    | earlier bevels widen                          | empty Poly Select before the next Boolean                                                                       |
| Default 18x5 cylinder cutter                           | rings inside the hole, messy cleanup          | 1 height segment, chosen sides                                                                                  |
| Voxel left at 1.0                                      | melted, wonky shape                           | voxel near 1/100 of the object                                                                                  |
| Live Reference wanted after picking                    | cannot switch                                 | extract the operand, re-add                                                                                     |
| Operand made from the same base                        | circular dependency                           | second Boolean above a Reference copy                                                                           |
| Crease modifier above OpenSubdiv                       | no sharp edges                                | move it below                                                                                                   |
| Retopology on a too-simple source                      | blotchy, angular shading                      | add source density first                                                                                        |
| Editing below a computed Retopology                    | stale result                                  | Reset, then Compute                                                                                             |
| Conform on a Y-up import                               | nothing seems to happen                       | projection axis Y                                                                                               |
| Old Chamfer from pre-2023.2 files, or Limit Effect off | self-intersections                            | Limit Effect on; `SetVersion #VerLatest` on old modifiers; never Legacy amount type on new models (chamfer doc) |
| Doubled edges after a push-through cut                 | creases or holes after subdividing            | weld before OpenSubdiv; test the ring (yx-lpHy8yPs 00:04:55)                                                    |
| Drape modeled as Displace                              | stiff, gizmo-shaped folds                     | Cloth, Shell, TurboSmooth via scenario-3dsmax-fx                                                                |
| Inverted operand                                       | unpredictable result                          | subtract the mesh from a large box (boolean doc)                                                                |

## Handoffs

- **Receives** from scenario-3dsmax-scene: units set, intake cleaned (CAD, FBX). From
  scenario-3dsmax-generation: a generated mesh or a reference image file; it enters at P4 (mesh) or
  P10 (image) as raw input, never as a finished model.
- **Delivers** to scenario-3dsmax-uv-baking: a quad mesh with its stack (live, or collapsed on a
  `_v002` copy) and the high-poly bake variant. To scenario-3dsmax-game-assets: Smart Bevel or
  Chamfer stacks; it owns smoothing, Weighted Normals, LODs, export. To scenario-3dsmax-materials:
  material IDs from Boolean Use Material or Chamfer Set Chamfer Material.
- **Routes away:** cloth drapes and tyFlow to scenario-3dsmax-fx; custom tools and UIs to
  scenario-3dsmax-scripting.

## Current 3ds Max notes

From the project's version-deltas table (modeling section) and the saved Autodesk docs.

- 2027: Smart Bevel; Boolean recursive welding for Booleans created in 2027 only (old files keep old
  results); Spline Chamfer fixed radius (`UseRadius`, `AutoWeld`); Extrude direction
  (`Extrude_Direction`); Array surface distribution with Z growth, Pack Element on splines; faster
  ReForm; Flow Retopology under Tools; Noise Plus (`NoisePlusModifier`); Boolean per-operand data
  scriptable.
- 2027.1 to 2027.3: Smart Bevel handles more complex geometry, runs faster (quoted up to 20x), and
  in 2027.3 removes very short edges first; 2027.3 documents `SmartBevelModifier` and
  `SmartBevelModGlobal`. Array `outputType` outputs points for Point Instance (2027.2). Mesh Cleaner
  gains Dead Vertices (2027.3).
- 2025: OpenSubdiv lost Operating Mode, Adaptive Subdivision and Mesh Controls; Retopology gained
  standalone preprocess and OpenVDB remeshing. 2025.2: Stack Selection in Poly Select and Mesh
  Select.
- Legacy: ProBoolean (use the Boolean modifier: Imprint inserts edges, Cookie cuts open holes);
  Chamfer Legacy amount type (old files only).

## References

- [references/procedures.md](references/procedures.md): P1 to P10, full code, channel, status,
  checks.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps and
  the deciding conditions.
- [references/critique.md](references/critique.md): self-review rubric with numbers and capture
  checks.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for every interactive step.
- [references/sources.md](references/sources.md): every video and doc, what it is best for.
- [scripts/maxkit_modeling.py](scripts/maxkit_modeling.py): `add_mod`, `set_props`, `stack_audit`,
  `mesh_checks`, `voxel_ratio`, `mirror_seam_check`.
- [scripts/mxs/maxkit_modeling.ms](scripts/mxs/maxkit_modeling.ms): MAXScript twin for `mcp-safe`.
