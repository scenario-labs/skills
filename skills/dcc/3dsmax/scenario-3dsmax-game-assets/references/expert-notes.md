# Expert notes: game assets

Principles and judgment, grouped by expert. Timestamps are `HH:MM:SS` in the video; `frame` means
the value was read on screen, not heard. `[added]` marks the skill author's own addition. URLs are
in [sources.md](sources.md).

## Shading strategy and normals

### jjbigley, game art instructor (SKXrtpTIsNI, 2020)

- Three ways to make a box read right, with their cost: hard edges plus UV seams (12 tris), chamfer
  plus weighted normals (44), support loops (108) (00:40:30). He refuses to rank them: the budget
  and the unwrap and paint effort decide.
- A hard edge is a vertex split in the engine, so every hard edge raises the vertex count (00:14:58
  to 00:15:31). In Edit Normals, Unify welds and Break splits.
- A normal map baked onto a mesh with hard edges leaves residue lines unless a UV seam runs along
  each hard edge (00:37:06 to 00:38:17).
- Averaged normals can look fine in the 3ds Max viewport and wrong in Unreal. Judge in the engine
  (00:35:09 to 00:35:48).
- Balance example: two C-shaped strips with chamfers and one smoothing group each keep paint work to
  two pieces (00:42:46 to 00:44:37).
- Bake in a tool with MikkTSpace tangents when the engine uses it; his Marmoset bake was cleaner
  than the old 3ds Max default on the same mesh (00:44:58 to 00:46:49).
- Numbers on screen: Chamfer 0.025 m, 1 segment, Uniform mitering (frame 00:10:19); Auto Smooth 89
  makes right angles hard (00:21:25).

### Next Level Game Art, environment artist (cGQJBU2RYPA, 2025)

- Mid-poly is a different philosophy from TurboSmooth with support edges: add chamfers, not loops
  (00:01:19).
- Recipe: chamfer all edges with 0 segments, clear smoothing groups and set all faces to 1, add
  Weighted Normals with default settings (00:02:26 to 00:05:18). Chamfer plus one smoothing group
  without the modifier looks "completely weird" (00:04:06).
- Panel defaults on screen: Area and Angle on, Use Convex Corner Angle on, Snap To Largest Face off,
  Blending 1.0, By Edge Angle 30 (frame 00:04:54).
- Cost: a 12-tri cube becomes 26 (00:06:29). It reads as much higher quality at a reasonable budget
  and instances well (00:07:53).
- Downside: repeated modules look identical; variation must come from elsewhere (00:08:55).
- Nanite was enabled by hand on the meshes before UE 5.5.4 and is automatic from 5.5.4 (00:10:58).
  The failure he shows comes from tessellation with displacement, not from Nanite alone.
- UE5 tessellation test on two 3 x 4 m walls: the unweighted wall opens up along its edges, the
  weighted one holds at reasonable displacement (00:12:05 to 00:13:45). "You will need it if you
  expect to use tessellation in Unreal Engine" (00:13:14).

### Polycount wiki, Smoothing Groups page (community reference, last edited 2015)

- Face-weighted normals: bevels with normals made perpendicular to the larger flat faces, so shading
  blends over the bevel only.
- Split UVs wherever there are hard edges, to avoid tangent-space errors; not every UV seam needs a
  hard edge.
- Bevels create long thin triangles that cost rendering time.

### Autodesk Weighted Normals modifier doc (2027 help)

- Used with a zero-segment Chamfer modifier, shading blends across the chamfered faces only.
- Hard Edge Detection can come from smoothing groups, UV seams in a chosen map, or edge angle.
- Parameters in the doc: Area, Angle, Use Convex Corner Angle, Snap To Largest Face, Blending, Hard
  Edge Detection (Use Smoothing Groups, Use UV Map, By Edge Angle), Smoothing, Hard Edge Blending,
  Iterations. There is no "Keep Explicit" or "Blend" toggle.

## Hard surface after Booleans

### Autodesk, Smart Bevel introduction (lDpcfhxP3qU, 2026, 3ds Max 2027)

- Put Smart Bevel above the Boolean, not Chamfer (00:01:07). Width is in world units; Depth negative
  is concave, 0 linear, positive convex (00:02:12).
- Starting values on screen: Width 2.38, Segments 1, Depth 0.5, Selected Edges plus Use Unsmoothed
  Edges, Output Smooth Bevel Only, Smooth to Adjacent, Threshold 30 (frame 00:02:12).
- Stack: Editable Poly, Boolean, Smart Bevel, Weighted Normals (Area plus Angle, Convex Corner Angle
  on, Blending 1.0, Iterations 10) (frame 00:03:00).
- Preset names encode intent and size (Round: L Boolean, Stock: M Selected, Straight: S Support)
  (frame 00:01:48).

### Martin Coven, Autodesk 3ds Max Principal Experience Designer (HhUMdy-0kSI, 2020)

- A Boolean mesh can look clean in wireframe and still fail under Chamfer, because cut lines pass
  very close to existing edges (00:00:04 to 00:00:37). Retopologize first.
- Stack that works: Slice (Remove Bottom), Subdivide (Adaptive, edge length 2), Retopology (Face
  Count 6000, Regularize 1, Adaptivity 0), Symmetry, Smooth (Auto Smooth 35), Chamfer (from
  Unsmoothed Edges, Minimum Angle off, Radial mitering), OpenSubdiv (Iterations 2) (00:01:10 to
  00:04:44).
- Pass smoothing groups down the stack instead of editing by hand (00:03:08).
- When one part shades badly, make its Retopology modifier unique and give it its own face count
  (150 on screen) (00:04:44).

### Tim Bergholz, ChamferZone (tP7FD4l-qus, 2015 content)

- Floaters for small parts: Chamfer (Unsmooth Edges) plus TurboSmooth (Iterations 2, frame 00:39:28)
  on bake-only pieces; delete the modifiers to get back the low poly (00:37:19, 00:40:39).
- Symmetry threshold: default 0.1 cm on screen (00:10:29); he advises 0.01 and a re-check of
  vertices on X = 0 (01:05:28).
- Ctrl+Backspace removes an edge and its vertices; leftover vertices cause shading artifacts
  (01:07:43).
- Remove edges on flat surfaces before export (01:23:46).
- Outdated for 2027: the chamfer-plus-TurboSmooth smoothing loop is superseded for hard surface by
  Smart Bevel plus Weighted Normals [added].

## Retopology of dense input

### Eloi Andaluz Fullà, archviz and VFX educator (Pg2Nm-fwyME, 2020, silent, values from frames)

- Stack for scans: Editable Mesh, ProOptimizer, Retopology, Projection Holder, Weighted Normals
  (frame 00:06:23).
- ReForm gave regular quads; Instant Mesh left holes at thin parts (frames 00:02:23 vs 00:03:23).
- Face Count is the main control: 60000, 30000, 10000 and 5000 compared on one subject (frames
  00:08:03 to 00:09:57).
- Triangulated CAD: Subdivide (Variable Curvature, Preserve Sharp Edges 30) for even density, Mesh
  Cleaner, then Retopology at 20000 faces, OpenSubdiv 1 (frames 00:13:53 to 00:15:56).
- Close the loop with a tangent normal bake from the original: 2048 px, MikkT (frames 00:11:58 to
  00:12:28).

### Top 3D AI, AI 3D tools reviewer (O6G6taj5M14, 2026, Blender, not 3ds Max)

- "Generating it's only half of the job" (00:00:00): generated meshes arrive with holes, merged
  parts, triangles, stretched UVs.
- Regenerate in a better model before repairing; if the mesh is "completely messy", redo it
  (00:03:04, 00:09:22).
- For props, a plain decimation that keeps UVs and texture beats AI retopology when detail matters;
  the ratio is per model (0.5 in his example) (00:12:24).
- Re-texture after any mesh rework; never patch an old texture onto a changed mesh (00:20:13).
- Generated characters need far fewer polygons before auto-rigging: under about 700,000 (00:22:41).

## LODs

### Alin Alexa, Technical Support Specialist, Crytek (s_RShJy4k-g, 2020)

- The goal is avoiding visible popping, not minimum triangles (00:00:21).
- Each LOD about 50 percent of the previous one; the exporter warns above 67 percent. Screen: "It
  has 1055 faces, its parent has 1436. It should have less than 957" (00:03:35, frame 00:03:53).
- Keep every part in LOD1, delete unseen faces in LOD2, strip minor parts in LOD3 (00:03:02 to
  00:04:07).
- Remove parts first, then optimize (00:05:11).
- ProOptimizer: tick Keep Textures and Keep UV Boundaries before Calculate; he lowers the Vertex %
  spinner and stops near 77 percent "where things start to get a bit weird" (00:05:44). That is the
  spinner value on one demo LOD, not a general floor or an LOD ratio.
- ProOptimizer is quick but messy: fine for far LODs only (00:04:40).
- LODs reuse LOD0's materials (00:09:41). Naming `$lod1_<name>` under an unprefixed LOD0 parent is
  the CRYENGINE contract, for both its own exporter and FBX (00:02:02 to 00:03:02).

## Pivots, scale, axes, export

### Ghost Pig, game developer (z1ws_LOo9AU, 2021)

- "I always like to have my models on the lowest level as perfect as possible" (00:08:34).
- Set 3ds Max to centimeters; Unity's Convert Units then reads "1cm (File) to 0.01m (Unity)" with
  Scale Factor 1 (frame 00:02:50).
- Default result in Unity: rotation X -90 and swapped axes, because 3ds Max is Z up right-handed and
  Unity is Y up left-handed (00:03:25).
- Best fix: export with Up Axis Z, then tick Bake Axis Conversion in Unity's model importer
  (00:04:16 to 00:04:52). The Unity FBX Exporter route forces Y up and has no Up Axis option
  (00:04:52).
- Fallback: rotate the pivot (not the mesh) X 90 so Unity's -90 cancels (00:05:24 to 00:05:56).
- Mirroring to fix handedness breaks the axes in 3ds Max and risks inconsistency across assets:
  decide once for the whole library (00:06:58).
- A 1e-06 position in Unity with 0 in 3ds Max is display precision: move away and back to 0, check
  the pivot is 0 (00:07:30 to 00:08:34).
- Judge with a test model carrying labeled axis arrows, dragged into the Hierarchy (00:03:25).

### Adam Zollinger, Learn Archviz (CM3GwvoOSP4, 2015)

- Take export settings from the engine docs: Smoothing Groups and Triangulate on (00:00:35 to
  00:01:11).
- A "Turned Edges" warning means Editable Poly edges were turned: tick Preserve edge orientation,
  which converts and triangulates them (00:01:45 to 00:02:21).
- Read every warning; some can be ignored, none should be skipped unread (frame 00:02:08).

### Epic Games, FBX Static Mesh Pipeline doc (UE5)

- The FBX pipeline uses FBX 2020.2; other versions risk incompatibilities.
- The pivot is always exported at the origin: build at the origin, with the origin at a corner for
  grid snapping.
- Triangulate in the 3D app when you can; exporter or importer triangulation allows no cleanup.
- Collision `UCX_<RenderMeshName>` with `_00`, `_01` suffixes, in the same FBX, convex, with gaps
  between hulls. The name must match the render mesh; the file name plays no role. Spheres and boxes
  fail on non-uniformly scaled meshes.
- With several meshes with custom collision in one file, only the first mesh's collision imports.
- Sockets: Dummy or Helper named `SOCKET_<RenderMeshName>_##`; an FBX with sockets holds one render
  mesh.
- Only Color and Normal maps connect automatically on import; Specular imports unconnected; others
  may not import.
- LODs import from the DCC through FBX, or one by one in the Static Mesh Editor.

## Datasmith

### Unreal ArchWizard, archviz artist (qsV4k09kPV8, 2025)

- Geometry in 3ds Max, materials and lighting in Unreal; on re-import untick everything but geometry
  (00:09:17).
- Simple materials survive Datasmith; for a hero project he rebuilds every material in Unreal from
  master materials (00:04:04 to 00:04:36).
- Direct Link for light scenes; heavy scenes go out layer by layer with Export Selected (00:08:10).
- Version pairing matters: Max 2025 needs Unreal 5.4 or later (00:00:49). Datasmith export lives in
  the ribbon (00:01:45).
- Import geometry and materials; skip lights and animation; use cameras for position only
  (00:03:00).

### Epic Games, How Datasmith translates 3ds Max content (doc)

- 6 existing UV channels survive (Unreal keeps 8, Datasmith adds 2 for lightmaps); indices are
  remapped from 0.
- Instances become one Static Mesh with many placements; different pivots plus non-uniform scale are
  unsupported: Reset XForm.
- 3ds Max LODs are not imported; generate them in Unreal.
- Custom collision goes through a Datasmith Attributes Modifier; keep the collision pivot in the
  same relative place.
- Procedural textures bake to TGA, limited by Datasmith > Settings > Limit Texture Resolution.
- Metadata on the User Defined tab as `key = value` with a space on both sides of `=`.

## Cleanup, kits and vertex color

### MZONE3D (3PuxYRayJGE, 2019)

- Most "broken model" symptoms come from a few causes; check them in a fixed order: weld, isolated
  vertices, flipped normals, loose edges, duplicates, ngons, transform, hidden faces.
- Weld at 0.001; 0.1 fuses vertices that must stay apart (00:00:52).
- Black area on a lit model: flipped normals (00:02:44). Flicker: coplanar duplicate elements
  (00:05:07).
- Turn to Poly with Max Size 4 and Remove Mid-Edge Vertices cleans the whole mesh (frame 00:07:25).
- Last resort: OBJ round trip, or attach to a fresh box, then Reset XForm, collapse and center the
  pivot (00:09:32 to 00:12:16).

### CtrlAultDelTutorials (J1lnlTbMtKs, 2015)

- A 240 box in a 256 cell gives a built-in gap so touching walls do not z-fight (00:05:23).
- Pivot offset -128, -128 puts the pivot on a grid corner for engine snapping (00:05:55).
- Extend floors and walls by one grid step (8) where a door sits, so no hole opens when sections
  join (00:09:52).
- Name pieces by wall and door count plus a description (00:13:36). All wall variants share one UV
  region, so one texture swap re-themes the kit (00:36:38).
- Auto Smooth after Clear All cures faceted banding on walls (00:27:24).

### FastTrack Tutorials (aQIQH0hZkDg, 2021, no audio, frames only)

- Vertex Color, Vertex Illum, Vertex Alpha and Map Channel are separate paint targets in the
  VertexPaint modifier (frame 00:03:12).
- Paint on a subdivided mesh so gradients have enough vertices (frame 00:01:46).

## Where experts disagree, and the deciding condition

| Choice              | Option A                                | Option B                                 | Decide by                                                            |
| ------------------- | --------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------- |
| Shading             | Mid-poly weighted normals (cGQJBU2RYPA) | Bake from high poly (SKXrtpTIsNI)        | Must the detail exist as shading? Budget and unwrap time             |
| Bevel tool          | Chamfer on clean quads                  | Smart Bevel after Booleans (lDpcfhxP3qU) | Topology: clean edges or Boolean cut lines                           |
| Triangulation       | Exporter triangulates (CM3GwvoOSP4)     | By hand in the 3D app (Epic doc)         | Whether edge direction affects shading or the bake                   |
| Unity axes          | Bake Axis Conversion                    | Pivot pre-rotated X 90                   | Whether the importer offers Bake Axis Conversion                     |
| Handedness          | Accept the X flip (Ghost Pig)           | Mirror every asset                       | Asymmetric assets where side matters; one rule for the whole library |
| Datasmith materials | Import and fix (qsV4k09kPV8)            | Rebuild from master materials            | Review speed versus hero quality                                     |
| Dense input         | Retopology plus bake (Pg2Nm-fwyME)      | Decimate keeping UVs (O6G6taj5M14)       | Deforming or hero asset versus static prop                           |
| LOD source          | DCC LODs through FBX                    | Unreal generates (Datasmith route)       | Export route                                                         |
