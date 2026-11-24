# Critique rubric: is this asset ready for the engine?

Use after every stage and before any export. Score each line pass, fail or n/a, and write the number
next to it. An asset ships only with every "block" line passing. Numbers come from
`scripts/mxs/game_audit.ms` or `maxkit_game.game_audit()` run through `scripts/game_rules.py`;
visual lines come from `capture.views()` and engine screenshots.

## 1. Measurable (block)

| Check                            | Pass                                                                                                                  | Where the number comes from                      |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| System unit                      | `centimeters` for Unreal and Unity                                                                                    | audit `units`                                    |
| Real size                        | Each dimension within 1 percent of the brief (in cm), or the GLB `size_m_xyz` in meters                               | audit `bbox_min`/`bbox_max`; `game_rules.py glb` |
| Transform                        | scale [1,1,1], `rotation_identity` true, `negative_scale` false on every exported node                                | audit                                            |
| Origin                           | Render mesh `pos` [0,0,0], no component between 0 and 1e-4                                                            | audit; rule `pivot.residue`                      |
| Pivot                            | At the agreed place: base center for props, grid corner for kit pieces, hinge line for moving parts                   | audit `pivot` versus `bbox_min`                  |
| Topology                         | `iso_verts` 0; `open_edges` 0 on closed props; ngons 0 on the export copy                                             | audit                                            |
| Budget                           | Triangles per LOD at or under the budget                                                                              | audit `tris`; `--budget`                         |
| LOD ratio                        | Each LOD at most 67 percent of the previous, about 50 percent targeted, levels contiguous                             | rules `lod.ratio`, `lod.gap`                     |
| Collision                        | Every `UCX_` matches a render mesh name, `convex_violations` 0, `open_edges` 0                                        | rules `collision.*`                              |
| Sockets                          | `SOCKET_` names match; one render mesh per FBX with sockets                                                           | rules `socket.*`                                 |
| One render mesh per FBX with UCX | Each moving part (lid, door) in its own FBX; Unreal keeps only the first mesh's custom collision in a multi-mesh file | export node list                                 |
| Symmetry                         | Threshold 0.01, not the 0.1 cm default; mirror-plane vertices at exactly 0                                            | modifier panel; vertex audit                     |
| UV                               | Channel 1 present; at most 8 UV channels (6 for Datasmith)                                                            | audit `map_channels`                             |
| FBX                              | Binary, header version 7700; `set_fbx_params` mismatch empty                                                          | `game_rules.py fbx`; export report               |

## 2. Measurable (warn: decide and write the reason)

- `sg0_faces` equals `tris`: the mesh has no smoothing group. Acceptable only when Weighted Normals
  or explicit normals were collapsed in and the capture looks right.
- Vertex count far above triangle count times 0.6 [added]: many hard edges or UV splits. Check that
  each hard edge earns its cost.
- LOD step under 20 percent of the previous one: expect popping; check silhouettes.
- Map channel 0 (vertex color) on a glTF target: the 3ds Max glTF exporter drops it.
- A Chamfer from a file older than 2023.2 not upgraded with `SetVersion #VerLatest`, or Limit Effect
  left on after Tri mitering.
- Long thin triangles on bevels or extra edges on flat faces: remove the edges; read the
  triangulation on the export copy.
- Smart Bevel used at 0 segments as a mid-poly chamfer: not sourced; compare glossy captures with
  the Chamfer route first.
- More than one material on LOD2 and below: draw calls; Epic allows fewer materials on lower LODs.

## 3. Visual, in 3ds Max captures

Look at the four views from `capture.views()` and one close perspective with a glossy material.

- **Flats read flat.** One clean highlight band per flat face; no gradient smearing from edge to
  edge. Smearing means missing weighted normals or a missing chamfer.
- **Bevels roll light.** A thin soft highlight along every hard-surface edge at the target camera
  distance. A hard black line means a hard edge with no chamfer.
- **No black patches.** A dark area on a lit surface is a flipped normal (MZONE3D).
- **No flicker or stripes.** Stripes on coplanar surfaces mean duplicate elements or z-fighting kit
  pieces.
- **Boolean seams.** Close capture of each cut: no pinching or zigzag shading along the cut line.
- **Silhouette.** Compare with the reference in front and side views at the same scale.
- **LOD lineup.** All LODs side by side in the front view: same outline; no holes; small parts
  vanish only at the far levels.
- **Collision overlay.** UCX hulls shown in wireframe over the mesh: they hug the volume and leave
  gaps between hulls.

## 4. Visual, in the engine (ask for screenshots)

- Static Mesh Editor (Unreal): Approx Size equals the real size; LOD picker shows each level; Show >
  Collision outlines the UCX hulls, not an auto hull.
- Lit preview: the shading matches the 3ds Max capture. Faceting in the engine but not in 3ds Max
  means normals were recomputed on import (jjbigley 00:35:48). When the two disagree, the engine is
  the reference.
- Normal-mapped assets: no thin lines along hard edges.
- Tessellated or displaced materials (UE5): edges stay closed (Next Level Game Art 00:12:05).
- Unity: dragged into the Hierarchy, Transform reads 0, 0, 0 / 0, 0, 0 / 1, 1, 1; a labeled axis
  test model points the right way (Ghost Pig).
- Web viewer: the model stands upright at the right size on the grid; materials show base color,
  roughness, metal and normal.

## 5. Process

- The work file was saved under a new version name before any destructive step.
- Every `[verify]` name the chunk used either worked (result shows it) or is reported as missing; no
  guessed property was silently skipped.
- The exported file names carry `_v002` and up when a file of that name existed.
- The handoff note lists the hard edges and texel density class sent to scenario-3dsmax-uv-baking.
