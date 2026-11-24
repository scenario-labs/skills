---
name: scenario-3dsmax-game-assets
description: "Use when a 3ds Max model must become a game or real-time engine asset: high to low or mid-poly hard-surface props, smoothing groups, hard edges, weighted normals, chamfer or Smart Bevel shading, LOD chains, UCX collision, sockets, pivots, scale and axis, modular kits on a grid, vertex color masks, mesh cleanup, or turning a scan, CAD or generated GLB into an engine asset. Also when users say FBX comes in at the wrong scale in Unreal, rotated -90 in Unity, faceted or black shading in the engine, normal map shows seams on hard edges, collision does not work, LODs pop, export to Unreal, Unity, Datasmith or glTF, or clean up an AI-generated 3D model."
license: MIT
---

# 3ds Max Game Assets

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit.

Expert level here means the asset arrives in the engine right the first time: real size, identity
transform, pivot where the designer needs it, shading that holds in the engine's lighting, LODs that
do not pop, collision that matches its name. The stance: decide the shading strategy and the export
contract before modeling detail, measure every gate with numbers, and judge shading in the target
engine, not in the 3ds Max viewport. If a sibling skill named here is missing from your available
skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit,
current-3ds-Max traps).

## Stance (the expert delta)

1. **Pick the shading strategy from what the surface must carry.** Mid-poly (zero-segment chamfer on
   every hard edge, smoothing group 1, Weighted Normals) needs no sculpt and no bake (Next Level
   Game Art, cGQJBU2RYPA 00:03:30). Bake a normal map only when detail must exist as shading.
   jjbigley refuses to rank them: a test box costs 12 tris with hard edges plus seams, 44 chamfered,
   108 with loops (SKXrtpTIsNI 00:40:30).
2. **A hard edge is a vertex split, and it must sit on a UV seam.** A hard edge raises the engine
   vertex count (SKXrtpTIsNI 00:14:58). A baked normal map shows residue on hard edges unless a UV
   seam runs there (00:37:06). Not every UV seam needs a hard edge (Polycount wiki).
3. **Judge normals in the engine.** Averaged normals can look fine in 3ds Max and wrong in Unreal,
   so the engine view is the reference, not the Max capture (SKXrtpTIsNI 00:35:48). Weighted normals
   are required once a UE5 material uses tessellation with displacement: unweighted edges open up
   (cGQJBU2RYPA 00:12:05). The trigger is tessellation, not Nanite alone (the test mesh had Nanite
   on, 00:10:58).
4. **Pivot and origin are part of the asset.** FBX always exports the pivot at the origin, so build
   at the origin with a corner or base there (Epic static mesh doc). Kit pieces get a corner pivot
   on a grid point, and a 240 box in a 256 cell leaves a built-in gap against z-fighting
   (CtrlAultDel, J1lnlTbMtKs 00:05:23).
5. **Fix at the lowest level in 3ds Max.** Each model must arrive with rotation 0, position 0 and
   scale 1, never "fixed later in a prefab" (Ghost Pig, z1ws_LOo9AU 00:08:34). For Unity: Up Axis Z
   on export plus Bake Axis Conversion on import. A 1e-06 position is residue: re-enter 0.
6. **LODs: about 50 percent per step, never above 67.** Remove whole parts first, then optimize.
   ProOptimizer needs Keep Textures and Keep UV Boundaries before Calculate, and stops before holes
   (Crytek, s_RShJy4k-g 00:03:35, 00:05:44). The goal is no visible popping, not minimum triangles.
7. **Retopologize Boolean or scanned meshes before you bevel them.** Chamfer breaks where cut lines
   sit near edges (Autodesk, HhUMdy-0kSI 00:00:37). In 2027, Smart Bevel sits above the Boolean,
   Weighted Normals on top (Autodesk, lDpcfhxP3qU 00:03:00).
8. **Clean in a fixed order with a small weld.** Weld at 0.001, not 0.1; then isolated vertices,
   flipped normals, loose edges, duplicate elements, Turn to Poly Max Size 4, Reset XForm, unhidden
   faces (MZONE3D, 3PuxYRayJGE 00:00:52, frame 00:07:25). On a symmetric piece, set the Symmetry
   threshold to 0.01 (default 0.1 cm) and check mirror-plane vertices sit at exactly 0 (ChamferZone,
   tP7FD4l-qus 01:05:28). If a dense or generated mesh is "completely messy", regenerate it instead
   of repairing it (Top 3D AI, O6G6taj5M14 00:09:22).

## Establish first

| Input                              | Why it changes the plan                                    | Default when unstated                                          |
| ---------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------- |
| Target engine and route            | FBX, Datasmith and glTF keep different data                | Unreal 5 by FBX                                                |
| UE5 tessellation with displacement | Weighted normals become mandatory                          | Ask; assume yes for UE5 hard-surface props                     |
| Moving parts (lid, door)           | Each becomes its own FBX with its own UCX                  | Ask                                                            |
| Triangle budget per LOD, LOD count | Drives mid-poly versus bake and the ProOptimizer percent   | Ask; else LOD0 from the asset role, 3 LODs at 50 percent steps |
| Camera distance class              | Texel density target (handed to scenario-3dsmax-uv-baking) | Third person, 5.12 px/cm                                       |
| Source of the mesh                 | Authored, scan, CAD or generated: sets the cleanup path    | Inspect it                                                     |
| System unit                        | Every number assumes it                                    | Centimeters, 1 unit = 1 cm                                     |
| 3ds Max release                    | glTF import from 2027.3; Smart Bevel from 2027             | 2027.3                                                         |
| Channel                            | `mcp-safe` allows MAXScript only, no Python                | From `max_env.doctor()`                                        |

## Procedure

Code, channels and result checks: [procedures.md](references/procedures.md); GUI paths:
[gui-paths.md](references/gui-paths.md).

1. **Inspect.** How: run `scripts/mxs/game_audit.ms` (read-only MAXScript, every channel) or
   `maxkit_game.game_audit()`, plus `stats.snapshot()` and `capture.views()`. Feed the JSON to
   `python scripts/game_rules.py report <file> --target unreal`. GATE: units, tris per node, open
   edges, isolated vertices, transforms and names are known; captures from four views exist.
2. **Intake and cleanup** (imported, scanned, CAD or generated meshes). How: `xio.import_any`, then
   `maxkit_game.normalize_intake(node, target_cm, measure, pivot)`. Run the cleanup order from
   Stance 8. Generated assets enter through scenario-3dsmax-generation. GATE: dimensions within 1
   percent of the real size, scale [1,1,1], no negative scale, 0 isolated vertices, open edges only
   where intended.
3. **Topology route.** Hard-surface prop or kit piece: mid-poly (Stance 1). Dense scan, CAD or
   generated mesh: ProOptimizer, then Retopology, then a normal bake from the original; a plain
   reduction that keeps UVs can beat retopology on props (O6G6taj5M14 00:12:24). Triangulated CAD:
   Subdivide to even density, Mesh Cleaner, then Retopology (Pg2Nm-fwyME). Hand modeling and
   Booleans go to scenario-3dsmax-modeling. GATE: LOD0 within budget, no Boolean-seam artifacts in a
   close capture.
4. **Normals and smoothing.** Mid-poly on clean quads: Chamfer modifier with 0 segments, edges
   chosen by its Filter By group (From Smoothing: Unsmoothed Edges, or Min./Max. Angle). Older
   Chamfers get `SetVersion #VerLatest`; after Tri mitering, turn Limit Effect off explicitly
   (Chamfer doc). Above a Boolean: `SmartBevelModifier` with the on-screen start values (Numbers).
   Then smoothing groups cleared to 1 and Weighted Normals: Area and Angle, Blending 1.0, Iterations
   10; Hard Edge Detection by smoothing groups, UV seams or edge angle keeps deliberate hard edges
   (WN doc, lDpcfhxP3qU frame 00:03:00). Bake route: hard edges only on UV seams; hand unwrap and
   bake (Bake to Texture with Projection, MikkT tangents, a small test size first) to
   scenario-3dsmax-uv-baking. GATE: glossy capture shows no smearing on flats; `sg0_faces` is not
   equal to `tris`.
5. **LOD chain.** How: `maxkit_game.make_lod(node, level, percent)` on copies; delete parts by hand
   first where they vanish at distance. How 3ds Max writes an FBX LOD group is not in the sources:
   default to one FBX per LOD, imported in the Static Mesh Editor. Datasmith does not import 3ds Max
   LODs (Epic Datasmith doc). GATE: `game_rules` `lod.ratio` clean (each level at most 67 percent of
   the previous), silhouettes match side by side.
6. **Collision and sockets.** How: `maxkit_game.add_box_collision(node, index)` for boxes, or
   hand-built convex pieces named `UCX_<RenderMesh>_00`, `_01`, with gaps between hulls. Sockets are
   Dummy helpers named `SOCKET_<RenderMesh>_00`; an FBX with sockets holds one render mesh. From a
   multi-mesh FBX, Unreal imports only the first mesh's custom collision (Epic doc). So a moving
   part (hinged lid) is its own render mesh in its own FBX with its own UCX, pivot on the hinge line
   [added]. GATE: `convex_violations` 0 and `open_edges` 0 on every UCX; every UCX and SOCKET name
   matches a render mesh in the same file.
7. **Export.** How: `maxkit_game.export_fbx_game(path, nodes, target="unreal"|"unity")` triangulates
   copies, sets the preset, reads every parameter back, never overwrites a file. Before it, remove
   unneeded edges on flats and check bevel triangulation by hand (Epic doc, tP7FD4l-qus 01:23:46).
   For glTF, `exportFile` with a `.glb` path; options have no documented script interface. For
   Datasmith, use the ribbon; Reset XForm instances with different pivots and non-uniform scale.
   GATE: `game_rules.py fbx` reports binary version 7700 (FBX 2019/2020 family [added]);
   `set_fbx_params` shows no mismatch; `game_rules.py glb` gives the expected size in meters.
8. **Verify in the engine.** How: the user or an engine-side agent imports and reports. Unreal:
   Static Mesh Editor size, Show > Collision, LOD picker, lit preview. Unity: Model tab Convert
   Units and Bake Axis Conversion, Transform reads 0, 0, 0. GATE: the checklist in
   [critique.md](references/critique.md) passes on engine screenshots; when they disagree with the
   Max capture, the engine wins.

## Numbers

| Value                                                                                                 | What it is relative to                                                                                  | Source                                                 |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 1 unit = 1 cm                                                                                         | System unit for Unreal and Unity export                                                                 | Ghost Pig 00:02:53; Epic                               |
| Weld 0.001 (not 0.1)                                                                                  | System units, prop scale                                                                                | MZONE3D 00:00:52                                       |
| Chamfer 0 segments; Weighted Normals Area + Angle, Blending 1.0, edge angle 30, Iterations 10         | Mid-poly hard surface                                                                                   | cGQJBU2RYPA frame 00:04:54; lDpcfhxP3qU frame 00:03:00 |
| Smart Bevel Width 2.38, Segments 1, Depth 0.5, Use Unsmoothed Edges, Smooth to Adjacent, Threshold 30 | Above a Boolean; Width in world units. No zero-segment value is sourced: Chamfer is the 0-segment route | lDpcfhxP3qU frame 00:02:12                             |
| Cube 12 tris plain, 26 weighted chamfered                                                             | Regression target for the mid-poly method                                                               | cGQJBU2RYPA 00:06:29                                   |
| LOD step about 50 percent, error above 67 percent                                                     | Triangles of the previous LOD                                                                           | Crytek 00:03:35                                        |
| ProOptimizer Vertex % about 77                                                                        | Spinner value kept on one demo LOD where artifacts began; not a general floor                           | Crytek 00:05:44                                        |
| Symmetry threshold 0.01 (default 0.1 cm)                                                              | Weld on the mirror plane                                                                                | tP7FD4l-qus 00:10:29, 01:05:28                         |
| Kit cell 256, piece 240, pivot -128,-128, door extension 8                                            | Kit project units                                                                                       | J1lnlTbMtKs 00:05:23 to 00:09:52                       |
| Texel density 20.48 / 10.24 / 5.12 / 2.56 px/cm                                                       | Weapon / first person / third person / top-down                                                         | sR1sAWWT2x8 00:12:28                                   |
| UV channels: 8 in Unreal; 6 survive Datasmith                                                         | Unreal static mesh                                                                                      | Epic Datasmith doc                                     |
| FBX 2020.2                                                                                            | Unreal FBX pipeline version                                                                             | Epic static mesh doc                                   |

## Quality gates

Full rubric with pass values: [critique.md](references/critique.md). The blocking lines:

- Measurable (audit JSON, `game_rules.py`): units cm; scale [1,1,1], rotation identity, no negative
  scale; origin with no 1e-06 residue; 0 isolated vertices; open edges 0 on closed props and every
  UCX; LOD budget and 67 percent ratio; map channel 1, at most 8 UV channels (6 for Datasmith);
  `UCX_` and `SOCKET_` names match; FBX binary 7700 read back; GLB size in meters.
- Visual (captures, then engine screenshots): straight highlights on flats, soft over bevels; no
  black patches or flicker; LOD silhouettes match; collision overlay hugs the mesh; no normal-map
  lines on hard edges.

## Common mistakes

| Mistake                                           | Symptom                                               | Fix                                                                                          |
| ------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Scene unit not cm                                 | Asset 100x or 2.54x off in the engine                 | Set units before modeling; scale once with Reset XForm                                       |
| Mesh far from origin                              | Asset spawns offset or rotates around empty space     | Pivot at base or corner, node at 0,0,0                                                       |
| Default Unity import                              | Rotation X -90, axes swapped                          | Up Axis Z + Bake Axis Conversion; or pivot pre-rotated X 90                                  |
| One smoothing group, no Weighted Normals          | Gradient smears across flats                          | Zero-segment chamfer + Weighted Normals                                                      |
| Hard edge without UV seam                         | Line or residue along the edge after bake             | Split UVs on every hard edge                                                                 |
| Chamfer on a raw Boolean                          | Pinches along cut lines                               | Retopology first, or Smart Bevel above the Boolean                                           |
| ProOptimizer without Keep UV Boundaries           | Broken textures on LODs                               | Tick Keep Textures and Keep UV Boundaries first                                              |
| UCX name not matching the render mesh             | Engine builds its own collision                       | `UCX_<exact render mesh name>_00`; the file name plays no role                               |
| Several meshes with sockets or UCX in one FBX     | Sockets lost; only the first mesh's collision imports | One render mesh per FBX                                                                      |
| Chamfer from an older file, or after Tri mitering | Self-intersections; Limit Effect stuck on             | `SetVersion #VerLatest`; turn Limit Effect off                                               |
| Long thin bevel triangles, edges left on flats    | Cost and shading artifacts                            | Remove flat edges; check triangulation by hand                                               |
| "Turned Edges" export warning                     | Edge direction changes, shading shifts                | Preserve Edge Orientation (converts to Editable Mesh, triangulates), or triangulate the copy |
| glTF for a vertex-color shader                    | Colors missing in the viewer                          | The 3ds Max glTF exporter drops vertex colors: use FBX                                       |

## Handoffs

- Receives a scene with set units from scenario-3dsmax-scene; modeled pieces and Booleans from
  scenario-3dsmax-modeling; generated GLB or FBX plus real size from scenario-3dsmax-generation.
- Delivers to scenario-3dsmax-uv-baking: low and high meshes, hard-edge list, texel density class,
  texture size; receives UVs and baked maps.
- Delivers to scenario-3dsmax-materials: material slots and names; keep engine materials simple
  (qsV4k09kPV8 00:04:04).
- Skinned or animated exports go to scenario-3dsmax-animation-rigging; batch export of many assets
  to scenario-3dsmax-scripting.
- Delivers to the user or an engine-side agent: the exported files, the audit JSON and the engine
  checklist.

## Current 3ds Max notes

From `sources/3dsmax-version-deltas.md`:

- 2027.3 has native Khronos glTF import and export; the exporter flattens hierarchies, drops vertex
  colors, reads Bitmap Texture only, and has no documented option script interface. Before 2027.3,
  ask for FBX or install the Khronos plug-in.
- Smart Bevel (2027) is scripted as `SmartBevelModifier` (documented, not GUI only); it changed in
  each 2027.x update, so retest bevels.
- `FBXExporterGetParam` gained `to:` and `enumAsString:` in 2027.2. `FBXExporterSetParam` names are
  not in the saved docs: read every value back.
- Retopology is built in (OpenVDB remesh since 2025, faster ReForm in 2027). Mesh Cleaner gained
  Dead Vertices in 2027.3.
- OpenPBR is the default material since 2026. Unreal's FBX import auto-connects Color and Normal
  only; check what arrives.
- The Datasmith version matrix for 3ds Max 2027 is not confirmed: Max 2025 needs Unreal 5.4 or later
  (qsV4k09kPV8 00:00:49).
- The Autodesk 3ds Max MCP server (2027.3) runs MAXScript only at the Safe level: use
  `mxs/game_audit.ms` there.

## References

- [expert-notes.md](references/expert-notes.md): principles and judgment by expert, with timestamps.
- [procedures.md](references/procedures.md): agent procedures with full code, channel, status and
  result checks.
- [critique.md](references/critique.md): the self-review rubric with numbers and capture checks.
- [gui-paths.md](references/gui-paths.md): menus, panels and engine import settings for each
  procedure.
- [sources.md](references/sources.md): every source, credential, URL and best timestamps.
- [maxkit_game.py](scripts/maxkit_game.py): in-Max helpers (audit, intake, LOD, UCX, FBX export).
- [game_audit.ms](scripts/mxs/game_audit.ms): read-only MAXScript audit for `mcp-safe`.
- [game_rules.py](scripts/game_rules.py): offline gates on the audit JSON, FBX header and GLB.
