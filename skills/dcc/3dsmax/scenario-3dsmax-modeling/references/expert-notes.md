# Expert notes: principles and judgment by source

Timestamps are `[hh:mm:ss]` in the video named. `[frame]` means read from a key frame, not from
speech. `[added]` marks a rule this skill adds; it is not stated by the source. The UI in most
videos predates 2027: the "Now" lines say what changed.

## Autodesk Learning Channel, Changsoo: Boolean modifier (TEz7tBiRrXc, 2025 UI)

- Boolean is a modifier, so operands can be reordered, disabled, retyped and copied later
  [00:00:05], [00:06:49].
- Types: Subtract, Intersect, Union, Split (subtract plus intersect in one pass), Merge, Attach,
  Insert [00:00:21 to 00:02:34]. Split plus the Data Channel preset "Explode Elements" breaks an
  object procedurally [00:00:53], [00:08:15].
- Capture for modeling, Live Reference for animation. The mode cannot be switched after the operand
  is added: extract and re-add [00:03:43].
- The chain: Boolean, Poly Select (the intersection edges arrive selected), Chamfer with Selection =
  Selected Edges, then an empty Poly Select, because Chamfer also outputs its edges [00:04:10],
  [00:04:40]. Chamfer widths shrink with the features: 0.3, 0.2, 0.2, 0.1. Save the Chamfer as a
  preset and reload it per stage.
- Frame values for that Chamfer: Mitering Uniform, End Bias 0.5, Amount Type Fixed, Segments 1,
  Depth Type Fixed, Depth 0.5 [frame 00:06:50].
- Use Material on builds a Multi/Sub-Object material from the operands; off keeps the base IDs
  [00:04:40].
- A thick teal line under the Boolean in the stack means you are looking at an operand's own history
  [00:06:29].
- OpenVDB (Union, Intersect, Subtract only), voxel 0.25 on his column [00:09:00]. An Array whose
  distribution source is the base cannot be an operand of that same base: add a second Boolean above
  a Reference copy [00:10:08].
- Retopology Preprocess "generates evenly distributed triangles": a good distribution source for
  Array Surface (2,000 faces, 75 percent removed) [00:09:32].
- Now: Smart Bevel (2027) is the documented alternative to the Poly Select plus Chamfer chain after
  Booleans; improved recursive welding applies to Booleans created in 2027.

## Todd D: OpenVDB soft serve (uDfhmKCdR0U, 2024 UI) and floater cuts (yx-lpHy8yPs, 2024 UI)

- Keep the model parametric and fix holes at the base (Star inner radius 1.3 to 1.5) [00:13:46].
  Plug gaps in the source early (a sphere in the Loft opening) [00:09:48].
- Type values with units in any spinner (`0.5"` then Tab) and 3ds Max converts to the scene unit
  [00:01:06].
- OpenVDB as a "melt it together" welder; voxel default 1.0 too coarse at real scale, 0.5 poor, 0.1
  to 0.11 used on a 5 inch (12.7 cm) swirl [00:11:30], [00:12:03].
- Each new Boolean resets Method to Mesh and voxel to 1.0; set both again [00:12:38]. An Edit Poly
  between Booleans as a "bookmark" is optional.
- Retopology ReForm, Preprocess on: 2,000 too soft, 5,000, then 8,000 (result 8,197) [00:15:59 to
  00:18:13]. Face Count field: clear it before typing [00:15:25]. After edits below, Reset then
  Compute [00:14:52].
- Floater cut: attach a 1-height-segment, 8-sided cylinder; Shift-drag its top face down through the
  base; never push the bottom face up, which melts it in [00:02:11]. Fours and eights weld into quad
  grids [00:01:39].
- Integrity tests: Ctrl-double-click a ring around the hole gives a full loop only when all verts
  are welded [00:04:23]; doubled edges show as 3 versus 7 edges and must be welded [00:04:55].
- Support loops fast: select the polygon ring, Extrude with Local Normal at 0 [00:06:35].
- A 9x9-segment box cutter gives inside faces and overlaps: keep cutters 1x1x1 [00:12:41]. The
  method pays only for simple cutters; cleanup grows with cutter complexity [00:12:10].
- Deciding condition against the Boolean modifier: use the floater cut when the low-poly cage will
  be subdivided and edge flow matters; use the Boolean modifier when the base must stay editable or
  the cutter is complex (digest batch3).

## Arrimus3D: Booleans (fXI2MJ7Bw2k, 2022 to 2023 UI) and spline trick (3dJ1VLgeKmM)

- Topology before the Boolean: build the surrounding loops, isolate the cut zone, then cut without
  edge removal [00:02:26]. Now: ProBoolean is legacy; Imprint in the Boolean modifier inserts
  intersection edges without removing faces (boolean doc).
- Cutter defaults are bad: 18 sides and 5 height segments; use 1 height segment and choose sides
  [00:02:57]. 6 sides suffice on a flat target that will be subdivided [00:03:30]; many sides when a
  Chamfer or render-time bevel will smooth it instead [00:06:11].
- A loop that refuses to pass: Weld all; if that fails, convert to Mesh and back to Poly [00:05:26].
- Fast detail (stacked primitives) is hard to fix later; the fixable route is a flat kit part,
  Slice, Symmetry, Smooth, Retopology twice, then Conform onto the curved surface [00:08:25],
  [00:10:14].
- "Triangles will not be a problem if you have enough density on your curved surface" [00:14:58].
- Retopology: "the complexity of the beginning is your limit". 14-segment sphere fails at 255 and
  555 faces; 64 segments handles 255 to 1,000 [00:17:00 to 00:18:37]. Reveal splotchiness with
  contrast-heavy shading or TurboSmooth on top [00:17:32].
- Splines: with a line selected, hold Shift to keep extending it; Corner vertex type first (Alt+A)
  [00:00:08], [00:01:56]. Axis-constrained snapping aligns new runs [00:01:51]. Spline Chamfer gives
  live fillets [00:02:45]; 2027 adds a fixed radius.

## Adam Zollinger, Learn Archviz: OpenSubdiv creases (UpBbEXkqeuw) and cushion (75_n7o0u8sw)

- Crease values replace support loops on an OpenSubdiv cage; fewer loops mean easier edits and
  easier unwrapping [00:05:42], [00:06:07].
- Not magic: an all-creased box with no loops stretches; add a few loops; new loops start at crease
  0 [00:01:42], [00:02:20].
- CreaseSet stores named edge groups, each with its own value (0.14 soft example) [00:03:26 to
  00:04:42 frame].
- Now: the Operating Mode, Adaptive Subdivision and Mesh Controls shown were removed in 2025
  (opensubdiv doc).
- Cushion: Box, connect for equal faces, raise the center, Symmetry for the bottom, seam by
  extruding edges, Noise on a face selection then collapse [00:01:19 to 00:06:19].
- FFD 4x4x4 below TurboSmooth acts like a large soft selection for billow [00:07:25]. Extra edges
  added for noise harden the smoothed surface [00:06:52]. Never judge the pre-smooth cage
  [00:04:41].

## Martin Coven, Autodesk: Retopology on CAD (sKEu2Gs3G_U) and on a Boolean model (HhUMdy-0kSI), 2021.3

- Smoothing groups drive ReForm: Smooth 30 degrees first [00:00:21].
- Sliver faces from CAD translation break Compute ("Calculation failed"): relax them, re-smooth
  [00:01:15].
- Slice a symmetric object in half: faster and exactly symmetric; Symmetry back after [00:01:51].
- Subdivide before ReForm: Delaunay fastest, Adaptive needs a small edge length, Variable Curvature
  best on sharp features with variable density lowered [00:02:22 to 00:02:54].
- Crooked loops: raise Regularize, lower Anisotropy [00:03:26]. Then Edit Poly detail, Chamfer with
  Min Angle, OpenSubdiv [00:03:58].
- A Boolean mesh can look clean in wireframe and still break under Chamfer, because cut lines pass
  close to existing edges: retopologize first (HhUMdy-0kSI 00:00:04 to 00:00:37).
- Stack: Slice (Remove Bottom), Subdivide Adaptive edge length 2, Retopology 6,000 with Regularize 1
  and Adaptivity 0, Symmetry (axis Y, zero the gizmo), Smooth Auto 35, Chamfer From Smoothing =
  Unsmoothed Edges with Radial mitering, OpenSubdiv 2 (HhUMdy-0kSI 00:01:10 to 00:04:44). One part
  too coarse: make its Retopology unique, face count 150 [00:04:44].
- Now: Retopology is built in (was a 2021.3 download); 2025 added standalone preprocess and OpenVDB
  remeshing; 2026 a newer ReForm; 2027 a faster ReForm.

## Eloi Andaluz Fullà: Retopology tips (Pg2Nm-fwyME, silent, frames only)

- Scan pipeline: ProOptimizer, then Retopology [frame 00:02:23]. ReForm gave cleaner quads than
  Instant Mesh, which left holes [frames 00:02:23, 00:03:23].
- ReForm defaults on screen: Quad Tolerance 10 percent, Subdivision Factor 1, Regularize 0.5,
  Anisotropy 0.5, Adaptivity 0.5; Auto Edge By Angle 30 [frames].
- CAD: Subdivide Variable Curvature with Preserve Sharp Edges 30, then Mesh Cleaner (degenerate and
  non-manifold counts 0), then Retopology 20,000 [frames 00:13:53 to 00:15:26].
- Close the loop with a normal bake because retopology loses detail [chapter 10:31] (baking belongs
  to scenario-3dsmax-uv-baking).

## Changsoo, Autodesk: Conform (sRLKiz4HSgA, 2025.2) and Array (EMaI6o162Cs, 2025)

- Conform direction by cost: Closest Point slowest and most accurate, Vertex Normal in most cases,
  Axis when the up axis is known [00:00:48], [00:09:30]. Y-up imports need axis Y [00:02:25].
- Selection Output (Selection, Missed, Ray Distance) passes influence to the next modifier: a second
  Shrink Wrap Conform closes edge gaps; Ray Distance guides relax-conform rounds [00:03:31],
  [00:07:45].
- Seam after double processing: Data Channel Vertex Input, Smooth 32 iterations amount 1.0, Vertex
  Output [00:04:38].
- Cache stores the result in the modifier; lower modifiers can be disabled; scenes open faster
  [00:05:10].
- Use Select modifiers instead of Edit modifiers when only selecting; they are lighter [00:01:20].
- Detail recovery: OpenVDB voxel 0.2 (1.0 too big), Retopology 25,000, Conform Shrink Wrap Closest
  Point to the original [00:08:22 to 00:09:30].
- Array: distribute, then transform, then randomize; Transform Before Projection for surface
  projection [00:03:23]. By Element: Offset 0 to diagnose, Center By per axis [00:05:49]. Pack
  Elements Offset 1.0 means no gap [00:07:30]. Material ID or UV outputs break instancing on Create
  Objects [00:11:30]. A value that does not refresh: change Phase and cancel [00:08:34].

## Jake Denham: modifiers for archviz (QIPOLr4j3lM)

- Crease and CreaseSet between the base and OpenSubdiv [00:12:41], [00:13:15].
- Boolean Split with a noised plane gives tear-away cutaways without touching the base [00:06:41].
- Chamfer modifier screen defaults: Uniform, End Bias 0.5, Fixed 1.0 cm, 1 segment, Depth 0.5,
  smoothing threshold 30 [frame 00:09:40]. "Radial is pretty good" [00:09:30].
- Affect Region at low strength makes bought furniture look used [00:00:33]. Stitches: Create Shape
  from a sofa edge loop, Array along the spline [00:00:52].
- Camera Map needs a dense receiver plane [00:09:06]. Cloth then Shell then TurboSmooth 2 for a
  tablecloth [00:12:06] (simulation belongs to scenario-3dsmax-fx).

## RenderRam: stacked Displace wrinkles (ALiGLb6TsS4)

- Displace modifier, not render displacement: it moves vertices in the viewport, so wrinkles can be
  placed [00:00:35].
- Paint by stacking copies, each with its own gizmo position, rotation and strength; the modeling
  stack below stays intact [00:04:38], [00:06:30].
- Blur softens; Luminance Center keeps region ends from rising [00:01:38], [00:02:14]. Gizmo
  outline: Decay first, then a radial Gradient Ramp mask in a Mix [00:02:14 to 00:03:50].
- Same map as an instance on every copy; TurboSmooth below for finer detail [00:01:38], [00:06:30].
  "It's not super precise but it will get the job done" [00:06:00]. Judged on renders.

## Igor Mota: headphones (0jXxaGKuW6Y, 2024 UI)

- Two orthographic reference planes; low cage in Edit Poly; Symmetry; OpenSubdiv as a continuous
  check [00:00:28], [00:05:41].
- Edit Poly above Symmetry for details that must not mirror; drop OpenSubdiv to 1 iteration while
  editing seams [00:07:04], [00:11:32].
- Loop Regularizer turns a face into a circle; Set Flow fits loops to curvature [00:03:30] (GUI
  only).
- Chamfer on support edges keeps them hard [00:09:38]. Lathe for the stand base [00:12:28].

## Tim Bergholz, ChamferZone: AKM weapon (tP7FD4l-qus, 2016 UI)

- Scale reference planes to one known real dimension (87.884 cm overall) [00:02:46]; plane at the
  image aspect, 1 segment, backface cull [00:01:04].
- Half-model under Symmetry; collapse only to cross the mirror plane; Symmetry weld threshold 0.01
  cm, not the default 0.1, to avoid stray welds [00:10:04], [01:05:28].
- FFD for shaping instead of pushing verts [00:06:39]. Flow Connect adds tangent-following loops
  [00:19:14].
- Floaters (separate detail pieces for the bake) carry Chamfer (Unsmoothed Edges) plus TurboSmooth:
  delete the two modifiers for the low poly, keep them for the high poly [00:37:19], [00:40:39].
- At least 16 edges, 20 chosen, before a Bend; decide the curve before committing [00:55:32].
- Flat surfaces get no extra edges [01:23:46]. Incremental saves (akm, akm2 ... akm7) [frames].

## Colton, Autodesk: Smart Bevel (lDpcfhxP3qU, 2027)

- Chamfer follows topology and offsets only along neighbor edges, so after a Boolean it pinches and
  gives uneven width; Smart Bevel walks the surface at a constant distance [00:00:42].
- Width in world units; segments "use only what you need"; Depth negative concave, 0 linear,
  positive rounded [00:02:12].
- Place it above the Boolean; switch Selection from From Stack to a selection mode to bevel only
  intersections [00:01:39]. Leave Remove Isolated Arcs on [00:02:46]. Weighted Normals on top [frame
  00:03:00].
- Presets on screen: Chamfer: L Stack, Chamfer: S Hard Edge, Cover: L Hard Edge, Round: L Boolean,
  Round: S Angle, Round: S Boolean, Stock: M Selected, Stock: M Stack, Straight: S Support [frame
  00:01:48].
- Chamfer is "still powerful"; Smart Bevel is for Boolean-heavy work [00:03:05].

## Where the experts disagree, and the deciding condition

| Choice               | Option A                                    | Option B                                               | Decide by                                                                 |
| -------------------- | ------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------- |
| Sharp edges          | Creases plus OpenSubdiv (Adam Z)            | Boolean plus Chamfer or Smart Bevel (Changsoo, Colton) | subdivided soft form versus polygonal hard surface                        |
| Cut method           | Floater push-through, hand cleanup (Todd D) | Boolean modifier (Jake, Changsoo)                      | simple cutter on a subdivided cage versus editable base or complex cutter |
| Cutter sides         | few (6 to 8)                                | many                                                   | result subdivided versus only chamfered                                   |
| Topology after a cut | pre-built loops, no edge removal (Arrimus)  | retopologize, then conform (Martin, Arrimus)           | clean flat hard-surface kit versus messy CAD or organic                   |
| Boolean method       | Mesh: precise, sharp                        | OpenVDB: robust, rounds detail, quads                  | operand cleanliness and the detail you can lose                           |
| Conform direction    | Closest Point                               | Vertex Normal or Axis                                  | accuracy needed versus mesh weight                                        |
| Broad soft shaping   | FFD below the smoothing modifier            | Noise on a selection, then collapse                    | large form change versus local variation                                  |
| Freeze a heavy stack | collapse a copy                             | Conform Cache                                          | file weight versus keeping the stack                                      |
| Smoothing            | TurboSmooth (older stacks)                  | OpenSubdiv with creases                                | crease control needed; OpenSubdiv has no TurboSmooth-style loop control   |

## Version speed notes

- 2026: Conform about 40 percent faster (Embree 4.3.3), Displace 2 to 3x (expert-stated;
  version-deltas table, row "Conform speed").
