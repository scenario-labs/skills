# GUI paths: animation and rigging

Menus and panels for the same work as procedures.md, for a human or a computer-use agent. Paths come
from the source videos (older UIs) and the saved docs; menus were reorganized in recent releases, so
confirm the location in 2027.3 [verify]. "GUI only" marks steps with no documented script route.

## GUI-only steps (hand each to the user with its path)

No documented script route; name the path below when a procedure reaches the step:

- Weight Solver pass: Skin > Weight Properties > Weight Solver > Voxel or Heatmap > settings > Apply
  (section Skin).
- Fingers and neck by vertex: Skin > Edit Envelopes > Vertices > select > Weight Table or Weight
  Tool (section Skin).
- DQ mask on twisting joints: Skin > Parameters > Dual Quaternion (section Skin).
- Walkthrough Assistant: Animation menu > Walkthrough Assistant (section Camera on a path).
- CAT and Biped setup, Figure Mode, Layer Manager (sections CAT, Biped and mocap).
- Workbench Key Reducer, Mixer Time Warp, Planted keys (section Biped and mocap).
- Reaction Manager states (section Control surface).
- FBX checkboxes without a known script key: Convert Deforming Dummies to Bones, Preserve edge
  orientation (section FBX export).
- Animation Layers toolbar (section Keys and curves).

## Keys and curves (P2)

- Auto Key: N, or the Auto button under the time slider. Set Key mode: the Set Key toggle, then K or
  the key button to add a key.
- Key Filters (Set Key mode): Key Filters button > turn all off > Modifiers only, for Morpher work
  (MMHfDujrGwo 00:02:27).
- Default tangent for new keys: the tangent flyout next to the key buttons; choose Linear before
  keying for constant speed (rv2kFxbBtMA 00:03:28).
- Curve Editor: Graph Editors > Track View - Curve Editor. Select keys > Set Tangents to Auto /
  Linear. Show only the changing axis in the tree (rv2kFxbBtMA 00:05:23).
- Out-of-range types: Curve Editor > Controller menu > Out-of-Range Types (Loop, Relative Repeat).
- Time Configuration: the button under the time controls > Frame Rate, Start Time, End Time.
- Animation Layers: right-click the main toolbar > Animation Layers. Enable Anim Layers > choose
  tracks; Add, Collapse, Disable (`animation-layers-2023`).

## Camera on a path (P3)

- Route: Create > Shapes > Line, round the corners (vertex type Smooth or Bezier). Interpolation
  rollout > Steps 16, then 200 (e3g4boZKyFU 00:02:11, 00:05:25).
- Modifier List > Normalize Spline (default length); Show Nodes to see spacing (00:03:56).
- Camera: Create > Cameras > Free (target off).
- Walkthrough Assistant (GUI only): Animation menu > Walkthrough Assistant > Pick Path. "Path to eye
  level" only with the ground at Z=0 (00:02:44 to 00:03:18).
- Or: Animation > Constraints > Path Constraint > pick the line; Motion panel > Path Parameters >
  Follow, Constant Velocity; Axis X/Y/Z and Flip if the camera looks sideways [verify labels].

## Constraints and LookAt (P4, P5)

- Animation > Constraints > LookAt Constraint, then pick the target (driven selected first)
  (QRB-6wnDcPw 00:06:40).
- Motion panel > LookAt Constraint rollout: Add LookAt Target, Weight, Keep Initial Offset, Select
  LookAt Axis X/Y/Z + Flip, Select Upnode (uncheck World, pick the parent), Upnode Control LookAt /
  Axis Alignment (cm7OP3niwvI frames 00:08:44, 00:09:04).
- Constraint menu entries seen: Attachment, Surface, Path, Position, Link, LookAt, Orientation
  (QRB-6wnDcPw frame 00:08:11).
- Align: select, Alt+A, pick target, Pivot Point to Pivot Point, position and orientation axes as
  needed.
- Link: main toolbar Select and Link, or Graph Editors > Schematic View > Connect (drag child to
  parent).
- Reset XForm before linking: Hierarchy panel > Adjust Transform > Reset: Transform (as in
  cm7OP3niwvI 00:06:46), or Utilities > Reset XForm > Reset Selected, then collapse the XForm
  modifier.

## Bones and IK (P5)

- Create > Systems > Bones. Bone Parameters seen: Width 2.0, Height 3.0, Taper 90, Side Fins off, IK
  Chain Assignment IKHISolver, Assign To Children off (cm7OP3niwvI frame 00:01:39).
- Snaps: Snaps toggle with Pivot enabled to place bones pivot to pivot (00:01:10).
- Animation > IK Solvers > HI Solver, then click the end bone (00:02:46).
- Create > Helpers > Dummy for the driver.
- Animation > Bone Tools for fins, color and resizing. Set as Skin Pose / Assume Skin Pose / Skin
  Pose Mode in the Animation menu (frame 00:02:49).
- Hide bones: Display panel > Hide by Category > Bone Objects (Pgzy2_HxH2w 00:14:44).

## Control surface (P6)

- Modify panel > Modifier List > Attribute Holder on the master object.
- Animation > Parameter Editor (Alt+1): Add to Type "Selected Object's Current Modifier", Parameter
  Type Float or Color, UI Type Slider, Spinner or ColorPicker, Range From/To, Default (ytW9dyEtxqc
  frame 00:01:42).
- Edit an attribute: Parameter Editor > Edit/Delete > pick > change range > Apply Changes (00:07:21
  to 00:08:29).
- Wire: right-click the master > Wire Parameters > Modified Object > Attribute Holder > Custom
  Attributes > attribute; click the target > parameter; Parameter Wiring dialog: direction,
  expression, Connect (00:02:30 to 00:03:34).
- Reaction Manager: Animation menu > Reaction Manager; Add Driver, Add Driven, Create Mode, Create
  State (`reaction-manager-2025`).

## Skin (P7, P8)

- Modify panel > Modifier List > Skin > Parameters > Add (Select Bones dialog; Display > Expand All
  for big hierarchies) (Pgzy2_HxH2w 00:09:53).
- Edit Envelopes > select bone > drag inner and outer envelope rings (00:41:02).
- Fingers and neck (solver fails where bones and mesh are close): Weight Table to blend by hand
  (Kimn7CIZ5bI 00:04:10 to 00:05:02).
- Vertex weights (GUI for selection): Edit Envelopes on > Vertices on > select vertices > bone
  highlighted > Weight Properties > Abs. Effect; Weight Table; Weight Tool (Set Weight 0.5, Scale
  Weight 0.95, Copy, Paste, Blend) (`skin-modifier-2026`; Kimn7CIZ5bI frame 00:05:55).
- Weight Solver (GUI only): Weight Properties > Weight Solver dropdown Voxel or Heatmap > settings
  button > Falloff, Max Influence, Max Resolution, Use Winding Numbers > Apply (Kimn7CIZ5bI
  00:02:14; `weight-solver-voxel-heatmap`).
- Mirror: Mirror Parameters > Mirror Mode > Mirror Offset to the center > raise Mirror Thresh until
  no red vertices > Paste green or blue (`skin-modifier-2026`).
- Dual quaternion: Parameters > Dual Quaternion > DQ Skinning Toggle on > Blend Weights on > Weight
  Tool > 1 > Blend several times > Blend Weights off (`skin-modifier-2026`).
- Move mesh or bones without losing envelopes: Advanced Parameters > Always Deform off, transform,
  on.
- Skin transfer: Utilities panel > More > SkinUtilities > Extract Skin Data To Mesh; Import Skin
  Data From Mesh > Paste Skin Data dialog: pair Target and Source bones, or Match By Name
  (G47NnPXsPHM 00:04:13 to 00:05:51).
- Accessories: Modifier List > Skin Wrap > Add the skinned body (Pgzy2_HxH2w 01:00:05).
- Hide bone brackets: Customize > Preferences > Animation > Key Bracket Display None (G47NnPXsPHM
  00:00:33).

## CAT

- Create > Helpers > CAT Objects > CATParent; Create Pelvis; Hub Setup: Add Leg, Add Arm, Add Spine,
  Add Tail, Add Bone (R5NmiXpqBsQ 00:01:23 to 00:02:34). Or pick a preset rig in the CATParent list
  and trim it (Pgzy2_HxH2w 00:17:28).
- Limb Setup: L/M/R, Collarbone, Palm, Bones count (R5NmiXpqBsQ frame 00:02:56).
- Layers: select a CAT bone > Motion panel > Layer Manager > new Absolute or Adjustment layer; Local
  Weight and Global Weight; bone coloring by layer (0xKZ5hV4MK8 00:01:02 to 00:04:05). Animation
  mode needs at least one layer.
- CATMotion: Layer Manager > new CATMotion layer > CATMotion Editor (per-bone parameters, presets)
  (R5NmiXpqBsQ 00:08:19).
- Save and load animation or a layer for another rig from the Layer Manager (00:04:07).
- Related clips (walk, trot, run) as layers in one file: Layer Manager > new layer per clip
  (0xKZ5hV4MK8 00:04:05).

## Biped and mocap (P10)

- Create > Systems > Biped, drag in a viewport. Mesh: Object Properties > See-Through and Freeze
  (Pgzy2_HxH2w 00:29:36).
- Motion panel > Biped > Figure Mode; Structure rollout for link counts; Copy/Paste > Copy Posture >
  Paste Posture Opposite (00:31:12 to 00:37:12).
- Motion panel > Biped > Load File (BIP or mocap FBX); Save File with "Save Segment at Current
  Position and Rotation" and "A Keyframe per Frame" (WUELGPaQu8o 00:03:40, frame 00:39:37).
- Biped Apps > Workbench > Filters > Key Reducer on selected parts and active segment (00:07:10).
- Layers rollout > Create Layer; Collapse (Pgzy2_HxH2w 00:50:10; WUELGPaQu8o 00:10:01).
- Key Info > Set Planted Key / IK keys for contacts (WUELGPaQu8o 00:32:45, garbled narration)
  [verify label].
- Biped Apps > Mixer > clip > right-click > Time Warp > edit the warp curve > Mix Down (00:39:21 to
  00:43:51).

## Morpher and audio (P9)

- Curve Editor > Sound > right-click Soundtrack > Properties > add the WAV; set the range to the
  clip length (MMHfDujrGwo 00:00:00).
- Modifier List > Morpher > Channel Parameters > Load Multiple Targets; right-click the modifier to
  rename it; drag in the stack to reorder (00:01:54, 00:06:15, 00:07:22).

## FBX export (P13)

- File > Export > Export Selected > Autodesk (*.fbx). Preset; Include > Geometry: TurboSmooth,
  Convert Deforming Dummies to Bones, Triangulate, Preserve edge orientation; Animation > Bake
  Animation with Start, End, Step; Characters > CAT Characters as HIK; Advanced Options > Units and
  Axis (5M7jlvzGWQ4 frames f_00192, f_00238).
- Unreal import log "bones missing from the bind pose" for end bones: Use T0 as ref pose in the
  import options (f_00324).
