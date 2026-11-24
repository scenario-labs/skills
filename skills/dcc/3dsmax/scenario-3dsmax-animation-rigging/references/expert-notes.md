# Expert notes: animation and rigging

Principles and judgment by source, with timestamps. Items marked [added] are this skill's additions,
not the expert's. Doc items cite the saved Autodesk page.

## Lee Minardi: six-bar excavator linkage (cm7OP3niwvI, 2015, 3ds Max 2014)

- A planar mechanism is a 2D problem: build it in the Front view [00:00:36].
- Pivots must sit on the pin axes before rigging; his model came from AutoCAD with pivots set
  [00:00:36].
- Bones are kinematic helpers, not deformers: the real parts are linked to the bones [00:01:10].
- Snap bones pivot to pivot. Where nothing snaps, move a circle onto the pin hole to make a snap
  target [00:01:10 to 00:01:49].
- HI Solver from the root bone to the end bone closes the four-bar [00:02:46].
- A Dummy on the driving pivot, linked to the bucket, parents the IK solver: rotating the bucket now
  works the linkage [00:03:10 to 00:03:49].
- Slider cylinder: the inner half LookAts the outer half with axis Y, Flip if reversed [00:04:07].
- Circular references are refused. The outer cylinder aims at Link B, whose pivot coincides with the
  inner cylinder's pivot [00:05:00].
- Linking the bone to the arm flipped every part. Fix: Hierarchy > Reset Transform on the arm first,
  then link [00:06:46 to 00:07:24].
- Twisting the arm out of plane spun the clevis pin. Fix: LookAt Upnode from World to the end arm,
  on the pin and the inner cylinder [00:08:17 to 00:08:51].
- Judgment: move the bucket and arm, watch every link follow, twist out of plane [00:07:42 to
  00:08:51].
- LookAt panel values on screen: weight 50, Keep Initial Offset off, Viewline Length 100 [frame
  00:08:44].

## Autodesk 3ds Max Learning Channel: custom attributes and wiring (ytW9dyEtxqc, 2011)

- One master object with an Attribute Holder carries every slider, so the animator never selects
  doors and lights one by one [00:00:32].
- Ranges are real limits: door 0 to 170 (a door never opens 180), window 0 to 90 [00:01:55,
  00:03:34].
- Two-way wiring when the value is also edited on the object; one-way when the slider must be the
  only driver [00:03:03, 00:07:10].
- Path percent shows 0 to 100 but is 0 to 1 internally; a 0 to 100 slider makes jerky motion. Fix
  with `/100` in the expression or a 0 to 1 attribute [00:07:21 to 00:08:29].
- Pick hard-to-click helpers with H (select by name) [00:06:34].
- Rotation tracks take radians in wire expressions, the same class of trap [added].

## ThePolymonger: eye rig with LookAt (QRB-6wnDcPw, 2012)

- Plan the hierarchy before rigging [00:05:40].
- Controls are splines, never keys on geometry; one master parents two single controls [00:05:41 to
  00:06:15].
- Align controls to the eye pivots in position only when the eyes face forward [00:02:33].
- Offset controls in front of the face so the head never hides them [00:06:40].
- Driven object selected first, driver picked second [00:06:40].
- An eye that snaps on assignment needs Keep Initial Offset or the right aim axis [00:07:13 to
  00:07:48].

## Arch Viz Artist (Saga): walkthrough camera (e3g4boZKyFU, 2020)

- She calls walkthroughs boring and old-fashioned but teaches them because clients ask [00:00:00].
- Round the corners of the route line: "the smoother the better" [00:00:54, 00:01:29].
- Interpolation Steps 16; raise to 200 when still bumpy [00:02:11, 00:05:25].
- Camera target off; line at eye level, about 160 cm above the floor; "path to eye level" works only
  with the ground at Z=0 [00:02:11 to 00:03:18].
- Normalize Spline gives even knot spacing and steady speed [00:03:56].
- Slower: End Time 1400 and drag the last key to the end [00:05:25 to 00:06:41].
- Look-around with Auto Key, then Auto tangents on the rotation keys; an extra key holds the glance
  longer [00:06:41 to 00:11:39].

## Arch Viz Artist (Aga): keys and Curve Editor (rv2kFxbBtMA, 2021)

- Auto Key is the usual method; Set Key when a key must be added without moving [00:02:02].
- Constant speed needs linear tangents chosen before keying; Bezier defaults ease in and out
  [00:02:55 to 00:03:28].
- Show only the changing axis in the Curve Editor to read the curve [00:05:23].
- Modifier parameters animate and read the same way as transforms [00:09:39].

## Simulation Lab (Kyle): rigging crash course (Pgzy2_HxH2w, 2021, 3ds Max 2018)

- Choose the system by subject: Bones for simple objects, CAT for non-bipeds, Biped for humans with
  mocap and BIP files; CAT is fine for humans too [00:02:06, 00:21:50].
- Units to centimeters before anything [00:04:27].
- Bone size is the default envelope size: fit bones to the mesh, or make them skinny and paint
  weights [00:11:51, 00:33:26].
- Model characters in T-pose, legs straight down, arms straight out [00:26:56].
- Size the pelvis to the hip joints, since the thighs are its children [00:32:23].
- Work one side, then Copy Posture and Paste Posture Opposite [00:32:55, 00:36:39].
- Figure Mode refits bones after skinning and animating without breaking either [00:46:30].
- Deleting foot bones on a footless mesh does not hurt the skin [00:49:20].
- Instanced parts must be made unique before each gets its own Skin [00:42:39].
- Corrections over mocap go on an animation layer, then Collapse [00:50:10 to 00:55:49].
- Accessories follow deformation through Skin Wrap, not linking to the head bone and not Edit Poly
  Attach [00:59:20 to 01:01:42].
- Head bone displayed as Box so it does not hide face work [00:58:38]. Hide bones by category to
  review [00:14:44].
- Judgment: rotate each bone, Edged Faces on, play with bones hidden [00:43:44, 00:45:52].

## Autodesk 3ds Max Learning Channel: Voxel Solver (Kimn7CIZ5bI, 2015)

- Not a magic button: about 95% done, finish the last 5% by vertex [00:03:24, 00:04:10].
- Add bones from a selection set (`SKIN_BODY_BONES`): almost every bone except nubs and FK/IK blend
  bones [00:00:45].
- Start Falloff 0.2 and Max Resolution 64; try Max Influence 3, 4 or 6 and compare joints [00:02:14
  to 00:03:24].
- Fingers fail where bones and mesh are close: Weight Table blends by hand [00:04:10 to 00:05:02].
- Head: its own Skin with head, neck, clavicles and spine bones [00:06:16].
- Skull only the head bone; base of skull blends with the neck; neck base only the clavicles; eyes,
  teeth and tongue rigid to the head [00:07:47 to 00:10:27].
- About 10 minutes against over an hour for the old manual method [00:10:27].
- Disagreement: he says Max Influence 0 lets the software decide; the current doc says 0 is treated
  as 1 and -1 lets the solver decide. Follow the doc.

## Miloš Černý: FBX to CAT with skin transfer (G47NnPXsPHM, 2018)

- An imported rigged FBX keeps bones and skin but no rig controls, so it is not practically
  animatable [00:00:00].
- Align new CAT bones to old bones with Align (pivot to pivot, position and orientation): IK
  platform first, ankle next, then top to bottom; a second pass or FK for IK drift [00:01:08 to
  00:02:16].
- Old and new rigs on separate layers with clear names [00:03:41].
- SkinUtilities: Extract Skin Data To Mesh, delete the Skin, add a Skin with only new bones, Import
  Skin Data From Mesh, pair bones or Match By Name [00:04:13 to 00:05:51].
- Import does nothing without a Skin and bones on the target [00:04:46].
- Bone size does not matter when weights are transferred [00:01:43].
- Hide bone brackets: Preferences > Animation > Key Bracket Display None [00:00:33].

## Miloš Černý: CAT (R5NmiXpqBsQ, 2020; 0xKZ5hV4MK8, 2017)

- A CAT rig builds in a few clicks from the CATParent and hub: legs, spine, arms, tail, extra spines
  for any topology [R5N 00:02:04 to 00:03:55].
- Saved animation loads onto a different CAT rig and keeps timing; it needs adjusting; unmatched
  bones stay still; scrub to refresh the pose [R5N 00:04:07 to 00:05:45].
- Per-layer bone weights exclude parts from a borrowed layer (wings at 0 in the run layer) [R5N
  00:07:32].
- CATMotion makes cycles without keys; a fresh motion layer looks wrong and needs per-bone edits
  [R5N 00:08:19 to 00:09:14].
- CAT has been barely updated since 2010 (his view) [R5N 00:00:22].
- An Absolute layer overrides everything below like a Photoshop stack; even plain keys are the first
  absolute layer [0xK 00:00:31, 00:01:02].
- CAT will not enter animation mode until a layer exists [0xK 00:01:02].
- Local Weight 0 on a chain shows the layer below; Global Weight is rig-wide; both animate [0xK
  00:03:34, 00:04:05].
- Keep related clips (walk, trot, run) as layers in one file [0xK 00:04:05].
- Deciding condition, CAT versus Biped: Biped for mocap cleanup (Workbench, Mixer, Biped layers);
  CAT for creatures, quadrupeds and animation sharing.

## Autodesk 3ds Max Learning Channel: Morpher lip sync (MMHfDujrGwo, 2010)

- Phones are sounds, not letters; about 7 of 16 heads for a short line [00:01:19].
- Targets share the base vertex count [00:01:54].
- Set Key with the Modifiers key filter only: one key keys every channel, zeros included, for
  controlled interpolation [00:02:27].
- Neutral keys bracket each phrase (25, 76, 117, 140); few channels reach 0 or 100 [00:02:54 to
  00:05:55].
- Phones and expressions in separate Morphers; the higher modifier is evaluated last and wins, so
  expressions go below [00:06:47 to 00:07:22].
- No blink on a frame with phone keys [00:07:55].
- Judgment: scrub with sound; a still upper face reads dead [00:05:55 to 00:06:15].

## Norberto Aguilera: AI mocap cleanup in Biped (WUELGPaQu8o, 2024)

- Video-to-mocap returns an FBX in about a minute with timing and poses right; the rest is about 50
  minutes of cleanup [00:00:34 to 00:03:04].
- Load on a Biped, save as BIP, reload in Figure Mode for a clean key set [00:03:40, 00:04:46].
- The clip stopped two frames before the video: extend the trajectory and key two frames before the
  end [00:05:21].
- Workbench Key Reducer on selected parts and the active segment before pose work [00:07:10].
- A Biped layer for pose fixes; copy one pose forward when a limb must hold [00:10:01 to 00:14:19].
- A freeze plane at floor level as the contact reference [00:16:24].
- Feet, then hands, then lower `Bip01` so hands reach the floor [00:16:59 to 00:28:44].
- Delete a sliding key and Biped re-solves the curve [00:30:46]. Work extended arms little by little
  [00:34:01].
- Timing last in the Mixer with Time Warp (37 frames to about 30), then Mix Down [00:39:21 to
  00:43:51].
- Save BIP with "Save Segment at Current Position and Rotation" and "A Keyframe per Frame" [frame
  00:39:37].

## Norberto Aguilera: FBX export for engines (5M7jlvzGWQ4, 2022, frames only)

- Two files: T-pose skin file and the animation file [frames 00:03:48, 00:05:44].
- Geometry: TurboSmooth on, Convert Deforming Dummies to Bones on, Triangulate off, Preserve edge
  orientation on, smoothing groups and tangents off [f_00192].
- Biped animation exported with Bake Animation off; CAT Characters as HIK off [f_00238].
- Unreal lists Nub and Xtra end bones as missing from the bind pose; they are unweighted end bones;
  the engine hint is Use T0 as ref pose [f_00324].
- Unreal previewed the clip at 30 fps [frame 00:05:38].
- No speech: the settings are what the frames show, not explained choices.

## Eloi Andaluz: October 2025 news (UAh24-Q77WQ)

- Studios fill native gaps with plugins: SmartAnim (template rigs, IK/FK, curve IK, pose kit,
  transfer between rigs; Max 2020 to 2026) [00:00:00 to 00:02:15].
- An AI-assisted retarget from Anima mocap to a SmartAnim rig was teased, not released [00:02:49].
- He regrets the new animation toolkit is not native [00:18:32].

## Autodesk docs (saved)

- Skin (`animation-rigging__skin-modifier-2026.md`): avoid an animated parent on a skinned mesh;
  Abs. Effect 1.0 is one bone only; mirror with Mirror Offset at the center and Mirror Thresh up
  until no red vertices; to move mesh or bones keep envelopes by turning Always Deform off and on;
  linear weighting by default, DQ for twisting bones with a blended DQ mask; Morph Angle Deformer
  from the stack, then remove the helper Edit Mesh or the morph doubles.
- Weight Solver (`weight-solver-voxel-heatmap.md`): Voxel and Heatmap; Apply or nothing happens;
  Falloff lower is smoother; Max Influence 0 is 1, -1 is automatic; Max Resolution and Use Winding
  Numbers are Voxel only; applies to selected vertices or all.
- Animation Layers (`animation-layers-2023.md`): Base Layer holds existing keys; no Layer controller
  inside a List or another Layer; collapse skips disabled layers and keys every frame when
  controller types, tangent types or Euler settings differ; a layer cannot be pasted between
  objects; enabling layers renames tracks and needs new Motion Mixer maps.
- Reaction Manager (`reaction-manager-2025.md`): a reaction needs two states; Create Mode with the
  driven entry highlighted makes a state for that entry only; Replace Driver keeps only the default
  state.
- CAT (`cat-overview-2023.md`): rigging, layers, CATMotion that adapts to velocity and uneven
  ground, mocap loaded into the Layer Manager, muscles.
- 2026 animation update (`whats-new-2026-animation.md`): CAT cloning and paste fixes, Biped exact
  name matching, `#extraBonesNameMatch`.
