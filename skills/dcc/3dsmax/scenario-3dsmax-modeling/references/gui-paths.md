# GUI paths for the modeling procedures

For a human, or a computer-use agent with a mouse. Paths are from the Autodesk docs where cited;
others are from the videos and may differ in the 2027 UI (marked [UI 20xx] with the release shown on
screen). Hotkeys are as stated by the experts; check them in Customize > Hotkey Editor.

## What an agent can and cannot do here

| Move                                                        | Scriptable substitute                                                                                          | Interactive (GUI path below)                                                         |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Add, order, enable modifiers, set parameters                | yes: `addModifier`, properties found by P1                                                                     | none needed                                                                          |
| Boolean operands                                            | `AppendOperand` seen in the macro recorder [verify]; per-operand data is scriptable since 2027                 | Operands rollout > Add Operands; Capture vs Live Reference is decided before picking |
| Edge selection for creases or bevels                        | select by rule: face angle, smoothing groups (Chamfer From Smoothing, Min/Max Angle), Boolean output selection | picking loops by eye, Ctrl-double-click rings                                        |
| Cut, Swift Loop, Target Weld, Set Flow, Loop Regularizer    | partial: `polyop` attach, extrude, weld, bridge [verify]; no clean equivalent for Set Flow or Loop Regularizer | Modeling ribbon                                                                      |
| Retopology Compute                                          | none documented; probe the modifier's interfaces (P1)                                                          | Modify panel > Retopology > Compute                                                  |
| FFD control points, Loft Scale/Twist curves, Displace gizmo | compute transforms or spline radii in script; gizmo transforms [verify]                                        | sub-object moves, Deformation dialogs                                                |
| Shift-drag floater cut, sculpt and Soften brushes           | Boolean modifier; Relax modifier                                                                               | Freeform ribbon                                                                      |
| Data Channel presets (Explode Elements)                     | not documented                                                                                                 | Presets > Load                                                                       |

## Finding a modifier

- Modify panel > Modifier List > Object-Space Modifiers > name. Typing the name with the list open
  filters it.
- Modifiers menu groups: Boolean under Parametric Deformers; Chamfer under Geometry (Mesh Editing);
  OpenSubdiv under Subdivision Surfaces (boolean, chamfer and opensubdiv docs).
- Global Search (2025+) also lists modifiers by name (re4hEa2o_qk frame 00:02:22).

## P1. Names from the macro recorder

- Scripting > MAXScript Listener. Make sure the macro recorder is on (Listener menu > Macro
  Recorder > Enable). Do the step once by hand, copy the lines it prints, and give them to the
  agent.

## P2. Boolean chain

- Add: select the base > Modify panel > Modifier List > Boolean.
- Operands: Operands rollout > Add Operands, then pick the cutter in the viewport. Tick "Use Live
  Reference" before picking if the operands animate; it cannot be changed after (TEz7tBiRrXc
  00:03:12).
- Operation type: click the type icon next to the operand in the list (TEz7tBiRrXc 00:00:21).
- Reorder, disable, delete: drag in the Operands list; right-click an operand > Extract Operand (or
  Options > Extract Selected, Extract Copy) (boolean doc; TEz7tBiRrXc 00:02:38).
- Manipulate Operands button: dot gizmos per operand; right-click a dot for the same menu
  (TEz7tBiRrXc 00:07:21). Group operands with Create a Folder (00:07:53).
- Options rollout: Use Material, Method (Mesh or OpenVDB), Imprint, Cookie, Retain Non-Planar Faces;
  Voxel Size under Volume Options. ESC aborts a long OpenVDB compute (boolean doc).
- Operand check: a point-triangle icon next to an operand means it is not watertight (boolean doc).
  Check with the STL Check modifier or the Measure utility; fill with Cap Holes.
- Smart Bevel: Modifier List > Smart Bevel, placed above the Boolean. Parameters: Presets drop-down,
  Selection rollout (From Stack or a selection mode, Use Unsmoothed Edges), Bevel Options (Width,
  Segments, Depth), Output (Smooth Bevel Only, Smooth to Adjacent, Threshold, Remove Isolated Arcs)
  (lDpcfhxP3qU frames 00:01:48, 00:02:12).
- Chamfer chain: Poly Select (leave it empty: it passes the Boolean's edge selection), Chamfer with
  Selection = Selected Edges, save as preset from the Presets drop-down, then another empty Poly
  Select (TEz7tBiRrXc 00:04:10).
- Explode by Split: Data Channel modifier > Presets > Explode Elements > Load; Boolean Create
  rollout > Create Objects (TEz7tBiRrXc 00:00:53, 00:08:45).

## Floater cut (Todd D, yx-lpHy8yPs) [UI 2024]

1. Create > Cylinder with AutoGrid on, 1 height segment, 8 sides, on the surface.
2. Select the base, Editable Poly > Attach, pick the cylinder.
3. Polygon level, select the cylinder's top face, hold Shift and Move it down through the bottom of
   the base.
4. Vertex level: Target Weld near-miss pairs; Swift Loop and Connect (Ctrl+Shift+E) orphan verts.
5. Test: Ctrl-double-click a polygon ring around the hole; a full ring means welded. Weld doubled
   edges.
6. Support loop: select the ring, Extrude with Local Normal and amount at 0 (right-click the
   spinner).

## P3. Retopology and Conform

- Retopology: Modifier List > Retopology. Algorithm drop-down (ReForm; Instant Mesh seen in 2021.3
  frames, QuadFlow seen in a later video; 2025 adds standalone preprocess and OpenVDB remeshing;
  check the list in your build). Target Size > Face Count; ReForm Settings: Quad Tolerance,
  Subdivision Factor, Regularize, Anisotropy, Adaptivity; Auto Edge: Smoothing Groups, Material IDs,
  UV Channel, Boolean Seams, Specified Normals, Selected Edges, By Angle. Buttons: Compute, Reset
  (Pg2Nm-fwyME and HhUMdy-0kSI frames).
- Face Count field: clear it before typing a new value (uDfhmKCdR0U 00:15:25).
- Flow Retopology (2027): Tools > Flow Retopology (whatsnew-2027).
- Conform: Modifier List > Conform. Target pick, Method (Shrink Wrap, Volume), Direction (Axis,
  Target Direction, Helper Direction, Vertex Normal, Closest Point), Influence, Falloff; Advanced
  rollout: Selection Output (Existing, Selection, Missed, Ray Distance), Normalize Selection, Cache
  button at the bottom (sRLKiz4HSgA frames 00:00:50, 00:03:10, 00:07:50, 00:05:35).
- Data Channel seam smoothing: Data Channel > Add Operator: Vertex Input (Vertex Selection), Smooth
  (Iterations 32, Amount 1.0), Vertex Output (sRLKiz4HSgA 00:04:38).

## P4. Retopology prerequisites

- Smoothing by angle: Editable Poly ribbon > Properties > Smooth 30, or the Smooth modifier with
  Auto Smooth and Threshold (sKEu2Gs3G_U 00:00:21; HhUMdy-0kSI 00:03:08).
- Hard-edge display to see smoothing groups (sKEu2Gs3G_U 00:00:21).
- Slivers: Ribbon > Freeform > Relax/Soften brush (sKEu2Gs3G_U 00:01:15).
- Slice: key 1 for the gizmo, rotate it onto the mirror plane, Remove Bottom (HhUMdy-0kSI 00:01:10).
- Subdivide modifier: Delaunay, Adaptive (Edge Length), Variable Curvature (Variable Density,
  Preserve Sharp Edges).
- Symmetry: Mirror Axis, Slice Along Mirror, Weld Seam threshold; adjust the Mirror gizmo in
  sub-object mode and zero its transform (HhUMdy-0kSI 00:02:35).
- Make one Retopology unique: right-click the modifier > Make Unique (HhUMdy-0kSI 00:04:44).
- Poly count: viewport label menu > Configure Viewports > Statistics, Total plus Selection; key 7
  toggles (HhUMdy-0kSI 00:04:11).

## P5. Creases and OpenSubdiv

- Per edge: Editable Poly or Edit Poly > Edge level > Edit Edges > Edge Properties > Crease
  (UpBbEXkqeuw 00:00:38).
- Crease sets: Modifier List > CreaseSet; select edges, type a name, Create Set; set the value per
  set; Show End Result off to edit (UpBbEXkqeuw 00:03:26 to 00:05:42).
- Crease modifier: between the base and OpenSubdiv, "From all edges" (QIPOLr4j3lM 00:12:41).
- OpenSubdiv: General Controls (Iterations 0 to 6, Render Iterations 0 to 10 with its checkbox,
  Isoline Display); OpenSubdiv Controls (Vertex, UV Boundary, Smooth Triangles, Crease Uniform or
  Chaikin) (opensubdiv doc).

## P6. Splines

- Create > Shapes > Line. Hold Shift while drawing on a selected line to extend it (3dJ1VLgeKmM
  00:00:08). Alt+A sets Corner type; S toggles snaps; Alt+D toggles the axis constraint as stated by
  the expert [verify hotkey].
- Rendering rollout: Enable In Renderer, Enable In Viewport, Radial Thickness, Sides (3dJ1VLgeKmM
  frame 00:03:35).
- Spline Chamfer modifier: 2027 fixed radius option (whatsnew-2027).
- Loft: Create > Geometry > Compound Objects > Loft > Get Path or Get Shape; Modify > Deformations >
  Scale, Twist (dialogs with curve points) (uDfhmKCdR0U 00:06:02 to 00:09:15).
- Create Shape from an edge loop: Edit Poly > Edge > Create Shape From Selection, linear
  (75_n7o0u8sw 00:08:32; tP7FD4l-qus 00:31:35).
- Lathe: Modifier List > Lathe on a profile spline (0jXxaGKuW6Y 00:12:28).
- Shell (P6b): Modifier List > Shell on the open surface; Inner Amount, Outer Amount (QIPOLr4j3lM
  frame 00:12:20).
- Round opening: Modeling ribbon > Loop Regularizer on the face ring, then Set Flow (0jXxaGKuW6Y
  00:03:30) [UI 2024].

## P7. Displace wrinkles

- Modifier List > Displace; expand it in the stack, select Gizmo, move, rotate and scale it
  (ALiGLb6TsS4 00:01:03).
- Map: drag the bitmap from the Material Editor onto the Displace Map button, choose Instance.
- Copy and paste: right-click the modifier > Copy, then right-click > Paste on the same or another
  object; move the new gizmo (00:04:38, 00:05:57).
- Outline fix: Decay, then in Slate a Mix map with a Gradient Ramp (Radial) in Mix Amount
  (00:03:15).

## P8. Array

- Modifier List > Array; rollouts Distribution, Transform, Randomization, Material ID, UV, Remove,
  Create (EMaI6o162Cs).
- Create Objects makes a layer `<Original>_Clones`; Use Instance is on by default (00:11:30).
- Stitching: Edit Poly > Edge > Create Shape From Selection on the seam loop; Array on the stitch
  element distributed along that spline, Position 0.7, axis Y (QIPOLr4j3lM 00:00:52).

## P10. References and checks

- Reference plane: Create > Plane at the image aspect, 1 segment; drag the image onto it; Object
  Properties > Backface Cull; Alt+X for see-through (tP7FD4l-qus 00:01:04, 00:02:46).
- Scale to a real dimension: a Box of the known size, Scale Transform Type-In (right-click the Scale
  tool) (tP7FD4l-qus 00:03:49).
- Viewport checks: F3 wireframe, F4 Edged Faces, Alt+Q isolate (0jXxaGKuW6Y overlay).
- xView checks for open edges, overlapping faces and isolated vertices: viewport label menu > xView
  [verify menu name in 2027].
