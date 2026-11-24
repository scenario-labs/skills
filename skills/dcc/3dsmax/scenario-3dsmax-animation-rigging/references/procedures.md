# Procedures: animation and rigging in 3ds Max 2027.3

Every block here is **not yet run in 3ds Max**. Each names its channel and the source it was checked
against. Names marked `[verify]` are not in the saved Autodesk docs: they come from expert notes or
common use, so read the first result before trusting them.

Conventions:

- Wrap each Python chunk with `scripts/anim_wrap.py`:
  `wrap_anim(code, kit=["xio", "capture"], result_path=...)`. It calls the lead's `max_wrap.wrap`
  with `maxkit_anim` as a sibling kit (`kit_dirs` = this skill's `scripts/`), which adds the undo
  record and the JSON result; the chunk sets `result`. The explicit `pymxs.undo` blocks below matter
  only when a chunk is pasted by hand.
- Wrap MAXScript blocks with `max_wrap.wrap(code, lang="maxscript")`; drop their own `undo ... on`
  line when wrapping, since the wrapper adds one.
- `ARGS` at the top of a chunk holds the values the agent fills in. Never hard-code a user path.
- Distances assume the scene's system unit. Run `maxkit_anim.units_report()` first and convert.
- MAXScript blocks are the form to propose through `mcp-safe`. They avoid the Safe Scene Script
  Execution block list.
- Run `max_check.check(code=..., lang=..., channel=...)` on every chunk before sending it.
- A step marked GUI only goes to the user with its menu path from `gui-paths.md` (section "GUI-only
  steps"), never as "by hand".

| #   | Procedure                                                        | Channels                          |
| --- | ---------------------------------------------------------------- | --------------------------------- |
| P1  | Arrival check of a rigged or animated character                  | batch, bridge, handoff            |
| P2  | Keyframes by script: animate context, tangents, ranges, loops    | all                               |
| P3  | Camera on a path (walkthrough)                                   | all                               |
| P4  | LookAt rig (eyes, aim controls)                                  | all                               |
| P5  | Mechanical rig with pistons, then invariants and collision check | bridge, handoff, mcp-safe (build) |
| P6  | Control surface: custom attributes and wire parameters           | mcp-safe, bridge, handoff         |
| P7  | Skin: bones, solver pass, scripted fixes, weight audit           | bridge, handoff                   |
| P8  | Skin transfer to a new skeleton                                  | bridge, handoff                   |
| P9  | Morpher lip sync and expressions                                 | all                               |
| P10 | Mocap on Biped: load, measure contacts, clean                    | bridge, handoff (GUI fixes)       |
| P11 | Retarget between skeletons                                       | bridge, handoff                   |
| P12 | Cycle along a path without foot slide                            | bridge, handoff                   |
| P13 | FBX animation export and re-import check                         | batch, bridge, handoff            |

---

## P1. Arrival check of a rigged or animated character

Goal: know what arrived before touching it: skeleton hierarchy, scale, bind pose, frame rate, clip
range, skin. Use it for any FBX or GLB from a generator, a library or another studio. Generation
itself belongs to `scenario-3dsmax-generation`.

Run it in `batch` on a fresh scene. In a live session (`bridge`, `handoff`), import into a new empty
file only after the artist has saved their scene; never import an unknown rig into the working
scene.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (importFile), scripting-pipeline__gltf-import-2027.md (animation options), notes 5M7jlvzGWQ4 and G47NnPXsPHM
import pymxs
rt = pymxs.runtime
ARGS = {"path": "<file.fbx or file.glb>", "expected_height": 180.0}  # height in system units

path = ARGS["path"]
fbx_in = {}
if path.lower().endswith(".fbx"):
    for key in ("Animation", "Skin", "Shape"):          # Shape = morph targets
        rt.FBXImporterSetParam(key, True)               # [verify] setter and key names
        fbx_in[key] = str(rt.FBXImporterGetParam(key))  # getter is in the 2027 what's new page
    arrived = xio.import_any(path, using="FBXIMP")
else:
    arrived = xio.import_any(path)  # glTF import is native from 2027.3; its options have no documented script interface

skeleton = maxkit_anim.hierarchy()
meshes = [n for n in rt.geometry if maxkit_anim.find_skin(n) is not None]  # [verify] rt.geometry
morph = [str(n.name) for n in rt.geometry if any(str(rt.classOf(m)) == "Morpher" for m in n.modifiers)]
first, last = maxkit_anim.frame_range()
size = maxkit_anim.height_report(meshes or list(rt.geometry))
result = {
    "arrived": arrived,
    "fbx_import_params": fbx_in,
    "units": maxkit_anim.units_report(),
    "skeleton": skeleton,
    "skinned_meshes": [str(n.name) for n in meshes],
    "skinned_with_parent": [str(n.name) for n in meshes if n.parent is not None],
    "morpher_meshes": morph,
    "range": (first, last),
    "height": size,
    "height_ratio": (size["height"] / ARGS["expected_height"]) if size else None,
}
capture.views(ARGS.get("capture_dir", "captures/arrival"))  # lead toolkit: persp, front, left, top
```

Check in the result:

- `height_ratio` between 0.95 and 1.05. A ratio near 0.01, 2.54, 0.394 or 100 is a unit mismatch:
  fix it at import, never by scaling the skinned mesh.
- One root in `skeleton.roots` (two or more means a stray helper or a split skeleton).
  `non_unit_scale` empty. `duplicate_names` empty.
- `units.frame_rate` equals the clip's authored rate (30 is common; ask the source). `range` matches
  the clip length.
- `skinned_with_parent` empty: a skinned mesh with an animated parent gives unexpected results (Skin
  doc).
- Captures: the skeleton sits inside the mesh at the first frame, in a T-pose or A-pose; no limb
  outside the mesh.

Decide next:

- Bones named by a generator (`J_LegUp_L`, `mixamorig:*`, numbered joints): build a rename map
  before anything else (P11 uses it). The sources give no safe bone-rename procedure: rename on a
  copy (`_v002`), then rerun P1 and `skin_report()` and compare bone count and weights with the
  original before trusting it.
- Wrong scale: fix it with the importer's unit settings and rerun P1. The sources give no other
  route; if import cannot fix it, ask for a re-export at the right unit. Never scale the skinned
  mesh or the bones.
- Clip per file: keep the T-pose file as the skin file; load each clip separately (P13 exports the
  same way).
- Animator will edit the motion: rebuild a CAT or Biped rig and transfer the skin (P8), as the FBX
  keeps bones and skin but no rig controls (Miloš Černý, G47NnPXsPHM 00:00:00).

## P2. Keyframes by script: animate context, tangents, ranges, loops

Goal: create keys that play as intended. Constant speed needs linear tangents set before keying
(Aga, rv2kFxbBtMA 00:03:28).

```maxscript
-- channel: mcp-safe | bridge | handoff
-- status: not yet run in 3ds Max; checked against scripting-pipeline__maxscript-bitmap-values-2027.md ("animate on at time" pattern), note rv2kFxbBtMA
undo "anim: keys" on
(
    obj = getNodeByName "BOX_Slide"
    setDefaultTangentType #linear #linear                  -- [verify] set before keying
    animationRange = interval 0 80
    animate on
    (
        at time 0  obj.pos.x = 0
        at time 80 obj.pos.x = 100                          -- system units
    )
    ctrl = obj.pos.controller.X_Position.controller          -- [verify] Position_XYZ sub-controller
    setAfterORT ctrl #loop                                   -- [verify]
    setBeforeORT ctrl #loop                                  -- [verify]
    format "keys:% tangents:%\n" ctrl.keys.count ctrl.keys[1].outTangentType   -- [verify]
)
```

Rules:

- Set the frame rate and range before keying. Changing the frame rate later rescales or rounds keys
  [verify on first run].
- Key every channel that must hold, not only the one that moves (Set Key behavior, MMHfDujrGwo
  00:02:27).
- `relative repeat` out-of-range type suits a cycle that travels; `loop` suits an in-place cycle
  [verify names `#relativeRepeat`, `#loop`].
- Rotation keys on a camera or head turn: Auto tangents remove stiff corners (Arch Viz Artist,
  e3g4boZKyFU 00:08:32).
- Animation Layers: enabling them renames tracks (`Position\Base Layer\X Position`), so Motion Mixer
  maps must be regenerated; a layer cannot be pasted from one object to another; collapse keys every
  frame when controller or tangent types differ (`animation-layers-2023`). Use the GUI toolbar;
  scripting the layer manager is `[verify]`.

## P3. Camera on a path (walkthrough)

Goal: a camera that moves at constant speed with no steps at corners and turns its head naturally.
Smooth path first, then speed, then rotation (Arch Viz Artist, e3g4boZKyFU).

```maxscript
-- channel: mcp-safe | bridge | handoff | batch
-- status: not yet run in 3ds Max; checked against note e3g4boZKyFU (steps 16 then 200, Normalize Spline, eye 160 cm, End 1400) and note ytW9dyEtxqc (percent is 0 to 1 internally)
undo "anim: walkthrough" on
(
    pth = getNodeByName "SPL_Walk"                           -- route drawn by the user, rounded corners
    pth.steps = 200                                          -- [verify] spline interpolation steps
    addModifier pth (Normalize_Spline())                     -- [verify] class name; even knot spacing
    eyeZ = 160.0                                             -- cm; convert for other units
    cam = Freecamera name:"CAM_Walk"                         -- [verify]
    pc = Path_Constraint()                                   -- [verify]
    cam.position.controller = pc
    pc.appendTarget pth 100.0                                -- [verify]
    pc.follow = true                                         -- [verify]
    pc.constantVel = true                                    -- [verify]
    animationRange = interval 0 1400                         -- longer range = slower walk
    format "pathZ:% camZ:%\n" pth.min.z cam.pos.z
)
```

Then, in order:

1. Height: the line must sit at eye level above the floor, not above Z=0. Move the spline so
   `cam.pos.z - floorZ` is about 160 cm; the "path to eye level" option only works when the ground
   is at Z=0 (e3g4boZKyFU 00:02:44 to 00:03:18).
2. Speed: Path Constraint keys percent at the range ends. Slower means a longer range with the last
   percent key moved to the end (00:05:25 to 00:06:41). Move the key by time, not by value: the
   percent track is 0 to 1 internally while the panel shows 0 to 100 (ytW9dyEtxqc 00:07:21).
3. Head turns: key rotation on a parent dummy or with Follow off and an aim target, then set those
   keys to Auto tangents. A look target dummy on the same path a few percent ahead gives a leading
   view [added].
4. Measure with `maxkit_anim.speed_profile(cam, 0, 1400)`: `max_step_change_ratio` under 0.05 means
   no visible steps [added]. Higher: raise steps, check Normalize Spline, round the corner knots.
5. Capture a contact sheet every 50 frames with `capture.viewport` and look for jumps, horizon tilt
   and walls in frame.
6. Follow axis: with Follow on, the first capture must look along the path. If it looks sideways or
   backward, change the Path Parameters axis and Flip and capture again; the sources give no axis
   value for a Free camera [verify].
7. Animator control: when the camera position must be scrubbed by hand, wire a 0 to 1 custom
   attribute to the Path Constraint percent (P6, `targetPos`), never a raw 0 to 100 slider
   (ytW9dyEtxqc 00:07:21).

GUI substitute: Animation > Walkthrough Assistant > Pick Path (GUI only).

## P4. LookAt rig (eyes, aim controls)

Goal: controls that aim parts without flips. Driven object first, driver second; controls are
separate objects, never keys on geometry (ThePolymonger, QRB-6wnDcPw 00:06:40).

```maxscript
-- channel: mcp-safe | bridge | handoff
-- status: not yet run in 3ds Max; checked against notes QRB-6wnDcPw (hierarchy, Keep Initial Offset) and cm7OP3niwvI (axis, Flip, Upnode, LookAt panel fields on frames 00:08:44, 00:09:04)
undo "rig: eye aim" on
(
    master = Circle radius:12 name:"M_Eye_CTRL"              -- [verify] Circle params
    for side in #("L", "R") do
    (
        eye = getNodeByName (side + "_Eye")
        c = Circle radius:4 name:(side + "_Eye_CTRL")
        c.pos = eye.pos + [0, -40, 0]                        -- in front of the face, cm; offset keeps it selectable
        c.parent = master
        la = LookAt_Constraint()                             -- [verify]
        eye.rotation.controller = la
        la.appendTarget c 50.0                               -- [verify]
        la.relative = true                                   -- [verify] Keep Initial Offset
        la.upnode_world = false                              -- [verify]
        la.pickUpNode = eye.parent                           -- [verify] head, so the roll follows the head
    )
)
```

Check: move each control to four positions (up, down, left, right) and read `eye.rotation` at each;
no value jumps by more than the control moved, and a capture shows both pupils on the control. If an
eye snaps on assignment, set Keep Initial Offset or the aim axis (QRB-6wnDcPw 00:07:13). Upnode on
World spins parts when the parent rolls (Lee Minardi, cm7OP3niwvI 00:08:17).

## P5. Mechanical rig with pistons, then invariants and collision check

Goal: a linkage where every part follows, pistons stay coaxial and connected, and nothing passes
through anything else across the animated range (Lee Minardi, cm7OP3niwvI).

Prerequisites: each part has its pivot on its pin axis (CAD pivots or set by the modeler); parts are
named; the mechanism is planar and built in the Front view (00:00:36).

Build order, each line one step:

1. Reset XForm every part that will be linked or receive a linked bone, then collapse. A bone linked
   to a part that still carries a scale or rotation offset flips it (00:06:46).
2. Bones from pivot to pivot for each closed linkage; HI solver from root bone to end bone (00:01:10
   to 00:02:46).
3. Link the real parts to the bones; bones are kinematic helpers, not deformers (00:01:10).
4. A Dummy on the driving pivot, linked to the driving part; link the IK solver to the Dummy, so
   rotating the part works the four-bar (00:03:10 to 00:03:49).
5. Pistons: the inner half LookAts the outer half. The outer half cannot LookAt the inner one
   (circular reference), so it aims at the link that shares the inner half's pivot (00:05:00).
6. Upnode of every LookAt: the parent arm, not World (00:08:17).

```maxscript
-- channel: mcp-safe | bridge | handoff
-- status: not yet run in 3ds Max; checked against note cm7OP3niwvI (frames 00:01:39, 00:04:39, 00:07:26, 00:08:44); fundamentals-scene digest batch1 (ResetXForm then collapseStack)
undo "rig: linkage" on
(
    fn aimAt obj tgt upn axisIdx flipIt =
    (
        la = LookAt_Constraint()                             -- [verify]
        obj.rotation.controller = la
        la.appendTarget tgt 50.0                             -- [verify]
        la.target_axis = axisIdx                             -- [verify] 0 X, 1 Y, 2 Z
        la.target_axisFlip = flipIt                          -- [verify]
        la.upnode_world = false                              -- [verify]
        la.pickUpNode = upn                                  -- [verify]
        la
    )
    for n in #("Link_A", "Link_B", "Main_Arm", "End_Arm") do
    (
        o = getNodeByName n
        ResetXForm o                                         -- [verify] before any link
        collapseStack o                                      -- [verify]
    )
    pA = (getNodeByName "Main_Arm").pivot
    pB = (getNodeByName "Link_A").pivot
    pC = (getNodeByName "Link_B").pivot
    b1 = BoneSys.createBone pA pB [0, -1, 0]                 -- [verify] Front view: Y is the plane normal
    b2 = BoneSys.createBone pB pC [0, -1, 0]
    b2.parent = b1
    ik = IKSys.ikChain b1 b2 "IKHISolver"                    -- [verify] returns the solver node
    (getNodeByName "Link_A").parent = b1
    (getNodeByName "Link_B").parent = b2
    drv = Dummy name:"DRV_Bucket" pos:(getNodeByName "Bucket").pivot
    drv.parent = getNodeByName "Bucket"
    ik.parent = drv
    inner = getNodeByName "Cyl_Inner"
    outer = getNodeByName "Cyl_Outer"
    aimAt inner outer (getNodeByName "End_Arm") 1 false
    aimAt outer (getNodeByName "Link_B") (getNodeByName "End_Arm") 1 true   -- shares inner's pivot
    inner.parent = getNodeByName "Link_B"
    outer.parent = getNodeByName "Main_Arm"
)
```

Then animate the drivers through their full range (keys at the limits) and measure:

```python
# channel: bridge | handoff | batch (on a saved file)
# status: not yet run in 3ds Max; checked against note cm7OP3niwvI (link lengths, out-of-plane test) and scripts/maxkit_anim.py
import math
import pymxs
rt = pymxs.runtime
ARGS = {
    "rigid_pairs": [["Link_A_PinTop", "Link_A_PinBottom"], ["Link_B_PinTop", "Link_B_PinBottom"]],
    "pistons": [["Cyl_Inner", "Cyl_Outer"]],
    "stroke_pins": [["Cyl_Outer_Pin", "Cyl_Inner_Pin", 80.0, 140.0]],  # min, max pin distance, system units
    "moving": ["Main_Arm", "End_Arm", "Bucket", "Link_A", "Link_B", "Cyl_Inner", "Cyl_Outer"],
    "touching_by_design": [["Cyl_Inner", "Cyl_Outer"], ["Link_A", "Main_Arm"], ["Link_B", "Bucket"]],
}
node = rt.getNodeByName
first, last = maxkit_anim.frame_range()
drift = maxkit_anim.pivot_distance_drift([(node(a), node(b)) for a, b in ARGS["rigid_pairs"]], first, last)
coax = maxkit_anim.axis_alignment([(node(a), node(b)) for a, b in ARGS["pistons"]], first, last, axis=1)
stroke = []
for a, b, lo, hi in ARGS["stroke_pins"]:
    d = [math.dist(maxkit_anim.world_pos(node(a), f), maxkit_anim.world_pos(node(b), f))
         for f in range(first, last + 1)]
    stroke.append({"pair": (a, b), "min": min(d), "max": max(d), "ok": lo <= min(d) and max(d) <= hi})
hits = maxkit_anim.bbox_overlaps([node(n) for n in ARGS["moving"]], first, last,
                                 allow=[tuple(p) for p in ARGS["touching_by_design"]])
result = {"drift": drift, "coaxial": coax, "stroke": stroke, "bbox_hits": hits}
```

Pass criteria:

- `max_drift` under 0.01 system units on every rigid pair: the rig solves without stretching.
- `min_abs_dot` above 0.9999 on every piston pair: halves stay coaxial.
- Every `stroke` ok: the rod never leaves the barrel and never bottoms out. Read the limits from the
  model (barrel length, rod length) [added].
- `bbox_hits` empty, or each remaining hit confirmed clear on a capture at the listed frames.
  Bounding boxes are conservative; parts at an angle overlap as boxes without touching.
- Twist the whole arm out of plane and replay: no part spins (Upnode test, 00:08:17).

## P6. Control surface: custom attributes and wire parameters

Goal: the animator drives the rig from one object with sliders whose ranges are the real limits
(Autodesk Learning Channel, ytW9dyEtxqc 00:00:32, 00:01:55).

```maxscript
-- channel: mcp-safe | bridge | handoff
-- status: not yet run in 3ds Max; checked against note ytW9dyEtxqc (Attribute Holder, ranges 0 to 170 and 0 to 1, two-way versus one-way wiring); custAttributes and paramWire syntax [verify]
undo "rig: controls" on
(
    master = getNodeByName "CTRL_Master"
    holder = EmptyModifier name:"Controls"                   -- [verify] Attribute Holder class
    addModifier master holder
    def = attributes rigControls
    (
        parameters main rollout:ro
        (
            boomAngle type:#float ui:spBoom default:0.0
            targetPos type:#float ui:spTarget default:0.5
        )
        rollout ro "Controls"
        (
            slider spBoom "Boom (deg)" range:[-45, 30, 0]     -- mechanical limits, not 360
            slider spTarget "Target on path" range:[0, 1, 0.5] -- path percent is 0 to 1 internally
        )
    )
    custAttributes.add master.modifiers[#Controls] def      -- [verify]
    ca = master.modifiers[#Controls].rigControls
    paramWire.connect ca[#boomAngle] (getNodeByName "Main_Arm").rotation.controller[#Y_Rotation] "degToRad boomAngle"   -- [verify]
    paramWire.connect ca[#targetPos] (getNodeByName "TGT_Light").position.controller[#Percent] "targetPos"             -- [verify]
)
```

Rules:

- Rotation tracks take radians in a wire expression; path percent takes 0 to 1. A slider in degrees
  or 0 to 100 wired raw makes the motion jump (ytW9dyEtxqc 00:07:21; radians [added]).
- One-way wiring when the slider must be the only driver; two-way when the artist also edits the
  target directly (00:03:03, 00:07:10).
- Custom attributes and script controllers are embedded scripts: a scene that carries them is
  scanned by Safe Scene Script Execution when opened (`safe-scene-script-execution-2027`). Keep them
  free of file, network and .NET calls.
- Reaction Manager is the GUI alternative for state-based drivers. Replace Driver deletes every
  state except the default; add states with the driven entry highlighted, or the new state applies
  to all driven entries (`reaction-manager-2025`).

Check: set each slider to its min, default and max by script and read the target value; it equals
the expected angle or percent within 0.001.

## P7. Skin: bones, solver pass, scripted fixes, weight audit

Goal: a skin that deforms through extreme poses with at most N influences per vertex and normalized
weights. Automatic pass first, hand finish on the last 5% (Autodesk Learning Channel, Kimn7CIZ5bI
00:04:10).

Order:

1. Units and pose: character in T-pose, legs straight down, arms straight out (Simulation Lab,
   Pgzy2_HxH2w 00:26:56). No animated parent on the mesh. Instanced parts made unique before each
   gets its own Skin (00:42:39).
2. Bones fitted to the mesh: bone size sets the default envelopes, so fitted bones mean less cleanup
   (00:11:51). Size the pelvis to the hip joints, since the thighs are its children (00:32:23).
3. Skin per mesh with its own bone list: body with almost every bone except nubs and IK/FK helpers;
   head with head, neck, clavicles and spine (Kimn7CIZ5bI 00:00:45, 00:06:16).
4. Weight Solver pass (GUI only, no documented script call): Skin > Weight Properties > Weight
   Solver > Voxel or Heatmap > settings, then **Apply**; closing the dialog does nothing
   (`weight-solver-voxel-heatmap`). Start Falloff 0.2, Max Resolution 64, Max Influence 4 (or -1 to
   let the solver decide; 0 is treated as 1 in the current docs, whatever the 2016 video says).
5. Scripted fixes below: rigid parts to one bone, head and neck rules.
6. Twisting joints (forearm, neck): DQ Skinning Toggle with a blended DQ mask through the Weight
   Tool (GUI, `skin-modifier-2026`).
7. Audit with `maxkit_anim.skin_report`, then pose captures.

```python
# channel: bridge | handoff  (skinOps reads the Modify panel; not batch)
# status: not yet run in 3ds Max; checked against skin-modifier-2026 (Abs. Effect 1.0 = one bone), note Kimn7CIZ5bI (rigid eyes, teeth, tongue; skull 100% head); skinOps names [verify]
import pymxs
rt = pymxs.runtime
ARGS = {"mesh": "CHR_Head", "bones": ["Head", "Neck", "L_Clavicle", "R_Clavicle", "Spine2"],
        "rigid": {"Head": "selected"}, "limit": 4}  # rigid: bone -> list of vertex indices, or "selected"

mesh = rt.getNodeByName(ARGS["mesh"])
skin = maxkit_anim.find_skin(mesh)
with pymxs.undo(True, "skin: build and fix"):
    if skin is None:
        skin = rt.Skin()  # [verify]
        rt.addModifier(mesh, skin)
    rt.select(mesh)
    rt.execute("max modify mode")
    rt.modPanel.setCurrentObject(skin)  # [verify]
    have = {str(rt.skinOps.GetBoneName(skin, i, 0)) for i in range(1, int(rt.skinOps.GetNumberBones(skin)) + 1)}  # [verify]
    for name in ARGS["bones"]:
        if name not in have:
            rt.skinOps.addBone(skin, rt.getNodeByName(name), 1)  # [verify]
    names = [str(rt.skinOps.GetBoneName(skin, i, 0)) for i in range(1, int(rt.skinOps.GetNumberBones(skin)) + 1)]
    nverts = int(rt.skinOps.GetNumberVertices(skin))  # [verify]
    for bone, verts in ARGS["rigid"].items():
        bid = names.index(bone) + 1
        if verts == "selected":
            verts = [v for v in range(1, nverts + 1) if rt.skinOps.IsVertexSelected(skin, v)]  # [verify]
        for v in verts:
            rt.skinOps.ReplaceVertexWeights(skin, v, bid, 1.0)  # [verify]
result = maxkit_anim.skin_report(mesh, limit=ARGS["limit"])
```

Vertex picking is GUI work: the artist selects the skull, eyes and teeth vertices at the Skin's
vertex level, or the agent passes index lists it computed (for example every vertex of a detached
eye element).

Pass criteria from `skin_report`: `over_limit` 0 for the target engine's limit (4 is a common game
limit [added]), `unweighted` 0, `bad_sum` 0, `unused_bones` only nubs and helpers. Then pose
captures (critique.md, section Skin).

Head and neck rules (Kimn7CIZ5bI 00:07:47 to 00:10:27): skull only the head bone; base of skull
blends with the neck; base of neck only the clavicles; rings between blend progressively; eyes,
teeth and tongue rigid to the head. Fingers: the solver fails where bones and mesh are close; weight
them by hand (00:04:10).

Moving the mesh or bones after skinning without losing envelopes: save, turn Always Deform off,
transform, turn it back on; or use Skin Pose for bones only (`skin-modifier-2026`).

## P8. Skin transfer to a new skeleton

Goal: move weights from an imported skeleton to a new rig (CAT, Biped or clean bones) without losing
them. Deleting the Skin and adding new bones destroys the weights (Miloš Černý, G47NnPXsPHM
00:04:13).

GUI route (G47NnPXsPHM 00:04:13 to 00:05:51): Utilities > More > SkinUtilities > Extract Skin Data
To Mesh; delete the old Skin; add a new Skin with only the new bones; select both meshes > Import
Skin Data From Mesh; pair bones (Match By Name when names match). Import does nothing unless the
target already has a Skin with bones (00:04:46).

Scripted route, on a copy so the original stays intact:

```python
# channel: bridge | handoff
# status: not yet run in 3ds Max; checked against note G47NnPXsPHM (extract before delete, new bones only, pair by name); skinOps names [verify]
import json
import pymxs
rt = pymxs.runtime
ARGS = {"mesh": "CHR_Body", "bone_map": {"J_Hip": "CATRigPelvis", "J_Spine1": "CATRigSpine1"},
        "backup_json": "<results folder>/CHR_Body_weights_v001.json"}

src = rt.getNodeByName(ARGS["mesh"])
old = maxkit_anim.find_skin(src)
rt.select(src)
rt.execute("max modify mode")
rt.modPanel.setCurrentObject(old)  # [verify]
old_names = [str(rt.skinOps.GetBoneName(old, i, 0)) for i in range(1, int(rt.skinOps.GetNumberBones(old)) + 1)]  # [verify]
weights = []
for v in range(1, int(rt.skinOps.GetNumberVertices(old)) + 1):  # [verify]
    row = {}
    for i in range(1, int(rt.skinOps.GetVertexWeightCount(old, v)) + 1):  # [verify]
        b = old_names[int(rt.skinOps.GetVertexWeightBoneID(old, v, i)) - 1]  # [verify]
        row[b] = row.get(b, 0.0) + float(rt.skinOps.GetVertexWeight(old, v, i))  # [verify]
    weights.append(row)
with open(ARGS["backup_json"], "w", encoding="utf-8") as fh:
    json.dump({"bones": old_names, "weights": weights}, fh)

missing = sorted({b for row in weights for b in row if b not in ARGS["bone_map"]})
if missing:
    result = {"ok": False, "unmapped_bones": missing}
else:
    with pymxs.undo(True, "skin: transfer"):
        dst = rt.copy(src)  # [verify] the copy keeps the old Skin; the original is untouched
        dst.name = str(src.name) + "_newrig"
        rt.deleteModifier(dst, maxkit_anim.find_skin(dst))  # [verify]
        new = rt.Skin()  # [verify]
        rt.addModifier(dst, new)
        rt.select(dst)
        rt.modPanel.setCurrentObject(new)  # [verify]
        targets = sorted(set(ARGS["bone_map"].values()))
        for t in targets:
            rt.skinOps.addBone(new, rt.getNodeByName(t), 1)  # [verify]
        ids = {str(rt.skinOps.GetBoneName(new, i, 0)): i for i in range(1, int(rt.skinOps.GetNumberBones(new)) + 1)}
        for v, row in enumerate(weights, start=1):
            merged = {}
            for b, w in row.items():
                t = ids[ARGS["bone_map"][b]]
                merged[t] = merged.get(t, 0.0) + w
            rt.skinOps.ReplaceVertexWeights(new, v, list(merged.keys()), list(merged.values()))  # [verify] arrays via pymxs
        src.isHidden = True  # [verify]
    result = {"ok": True, "new_mesh": str(dst.name), "report": maxkit_anim.skin_report(dst)}
```

Check: same vertex count on both meshes, `report` clean, and three extreme poses captured on old and
new rigs side by side (critique.md). Keep old and new rigs on separate layers until the artist
approves (00:03:41). Delete nothing; the artist removes the old rig.

## P9. Morpher lip sync and expressions

Goal: a line of dialogue that reads, with an upper face that lives. The agent cannot hear audio: it
needs a phoneme list with frames from the user, a transcript with timings or a speech-to-viseme
tool.

```maxscript
-- channel: mcp-safe | bridge | handoff
-- status: not yet run in 3ds Max; checked against note MMHfDujrGwo (two Morphers, order, neutral brackets, all channels keyed, blink 16/18/20); WM3_* names [verify]
undo "face: lip sync" on
(
    head = getNodeByName "CHR_Head"
    phones = #("aah", "BMP", "DST", "ee", "eeh", "GK", "oh")
    expr = Morpher name:"Morpher_Expressions"               -- [verify]
    addModifier head expr                                    -- added first, so it sits lower
    ph = Morpher name:"Morpher_Phones"
    addModifier head ph                                      -- top of stack: evaluated last, wins
    for i = 1 to phones.count do WM3_MC_BuildFromNode ph i (getNodeByName ("PH_" + phones[i]))   -- [verify]
    WM3_MC_BuildFromNode expr 1 (getNodeByName "EX_Blink")
    -- keys: frame, then one value per phone channel; every channel keyed at every key time
    keysTbl = #(#(25, #(0,0,0,0,0,0,0)), #(30, #(0,0,0,0,0,80,0)), #(37, #(60,0,0,0,0,10,31)), #(76, #(0,0,0,0,0,0,0)))
    animate on
    for k in keysTbl do
        at time k[1] (for i = 1 to phones.count do WM3_MC_SetValue ph i (k[2][i] as float))   -- [verify]
    for f in #(16, 18, 20) do
        animate on at time f WM3_MC_SetValue expr 1 (if f == 18 then 100.0 else 0.0)
)
```

Rules (Autodesk Learning Channel, MMHfDujrGwo):

- Targets share the base vertex count (00:01:54). Check with `getNumVerts` [verify] before building.
- Transcribe sounds, not letters; a short line needs about 7 of 16 shapes (00:01:19).
- Bracket each phrase with neutral keys; key all channels at each key time, zeros included (00:02:27
  to 00:05:55). Few channels reach 0 or 100 (00:04:06).
- Phones Morpher above expressions in the stack: the higher modifier is evaluated last and wins
  (00:07:22).
- Blinks never on frames that carry phone keys: the phones evaluate after the blink and cancel it
  (00:07:55).

Check: `head.modifiers[1].name` is the phones Morpher [verify index order]; each key frame has a
value on every phone channel; blink frames and phone frames do not coincide; captures of the mouth
at each key frame match the intended shape.

## P10. Mocap on Biped: load, measure contacts, clean

Goal: an AI video-to-mocap or optical take that keeps its timing and loses its foot slide, floating
hands and early stop. Order: contacts (feet, then hands), then COM height, then timing, then mix
down (Norberto Aguilera, WUELGPaQu8o 00:16:59, 00:39:21).

1. Create a Biped, Motion panel > Biped > Load File (BIP, or the FBX from the mocap tool). From
   2026, BIP loads by exact name match; MAXScript `#extraBonesNameMatch` keeps extra-bone animation
   such as tails and wings (`whats-new-2026-animation`).
2. Save as `.bip`, switch to Figure Mode, reload: gives a clean key set (00:04:46).
3. Measure (code below) before fixing anything.
4. Trajectory: when the clip stops before the reference video, extend the root trajectory and key
   two frames before the end (00:05:21).
5. Workbench > Key Reducer on the selected parts and the active segment, before pose work
   (00:07:10).
6. A Biped layer for pose fixes; a freeze plane at floor level as contact reference (00:10:01,
   00:16:24).
7. Feet: plant with IK keys; delete a sliding key and let Biped re-solve the curve before touching
   handles (00:30:46). Hands: lower `Bip001` slightly, then re-key the hand (00:26:13).
8. Timing last: Mixer > Time Warp, then Mix Down (00:39:21 to 00:43:51).
9. Save `.bip` with "Save Segment at Current Position and Rotation" and "A Keyframe per Frame" on
   (frame 00:39:37).

```python
# channel: bridge | handoff | batch (on a saved file)
# status: not yet run in 3ds Max; checked against note WUELGPaQu8o (contacts, COM, freeze plane) and scripts/maxkit_anim.py; Biped node names from note 5M7jlvzGWQ4 frames
import pymxs
rt = pymxs.runtime
ARGS = {"prefix": "Bip001", "ground_z": 0.0, "foot_tol": 2.0, "hand_tol": 3.0}  # cm

node = rt.getNodeByName
p = ARGS["prefix"]
first, last = maxkit_anim.frame_range()
feet = {s: maxkit_anim.contact_slide(node(f"{p} {s} Foot"), first, last, ARGS["ground_z"], ARGS["foot_tol"]) for s in ("L", "R")}
hands = {s: maxkit_anim.contact_slide(node(f"{p} {s} Hand"), first, last, ARGS["ground_z"], ARGS["hand_tol"]) for s in ("L", "R")}
com = [maxkit_anim.world_pos(node(p), f)[2] for f in range(first, last + 1)]
result = {
    "range": (first, last),
    "foot_phases": feet,
    "worst_foot_slide": max((ph["slide"] for s in feet.values() for ph in s), default=0.0),
    "hand_contacts": hands,
    "com_min": min(com), "com_max": max(com),
}
```

Pass criteria: `worst_foot_slide` under 1 cm per contact phase [added, the expert judges by eye];
`height_jitter` under 0.5 cm in contacts; hand contacts present where the reference shows them; COM
never drops below a plausible height. Then a side-by-side contact sheet against the reference video
frames (critique.md).

GUI only: Workbench curve filters, Mixer Time Warp curve, IK key on a planted foot. Biped scripting
(`biped.loadBipFile`, `biped.saveBipFile`, layer functions) is `[verify]`.

## P11. Retarget between skeletons

Pick the route by what the target is:

- Biped to Biped: BIP files, with the 2026 exact name matching (`whats-new-2026-animation`).
- CAT to CAT: save the animation or a single layer and load it on the other rig. It works across
  different skeletons and keeps timing but needs adjusting; give unmatched bones (wings, tails)
  weight 0 on the borrowed layer. The pose looks broken until the time slider moves (Miloš Černý,
  R5NmiXpqBsQ 00:04:07, 00:07:32).
- Plain bones from two generators or an FBX library: constrain, sample, bake (below) [added]. Or
  retarget in the engine (Unreal IK Retargeter) when the clip is only needed there.

Constrain-and-bake, on a copy of the target skeleton:

1. Put both skeletons in the same rest pose at one reference frame (both T or both A).
2. Orientation-constrain each mapped target bone to its source bone with Keep Initial Offset;
   position-constrain only the root, scaled by the leg-length ratio.
3. Sample world transforms every frame, replace the constraints with plain controllers, write the
   samples as keys.

```python
# channel: bridge | handoff
# status: not yet run in 3ds Max; [added] method; constraint and controller names [verify]; sampling helpers in scripts/maxkit_anim.py
import pymxs
rt = pymxs.runtime
ARGS = {"map": {"src_hips": "pelvis", "src_spine": "spine_01", "src_thigh_l": "thigh_l"}, "root": "pelvis"}

node = rt.getNodeByName
first, last = maxkit_anim.frame_range()
targets = []
with pymxs.undo(True, "retarget: constrain"):
    for s, t in ARGS["map"].items():
        oc = rt.Orientation_Constraint()  # [verify]
        node(t).rotation.controller = oc
        oc.appendTarget(node(s), 100.0)  # [verify]
        oc.relative = True  # [verify] keep the rest-pose offset
        targets.append(node(t))
    pc = rt.Position_Constraint()  # [verify]
    node(ARGS["root"]).position.controller = pc
    pc.appendTarget(node([k for k, v in ARGS["map"].items() if v == ARGS["root"]][0]), 100.0)
    pc.relative = True  # [verify]
samples = maxkit_anim.sample_world(targets, first, last)
with pymxs.undo(True, "retarget: bake"):
    for n in targets:
        n.transform.controller = rt.prs()  # [verify] plain Position/Rotation/Scale
    maxkit_anim.apply_world_samples(samples)
result = {"baked": [str(n.name) for n in targets], "frames": (first, last),
          "loop": maxkit_anim.loop_gap(targets, first, last)}
```

Check: P10 contact measures on the target feet (a different leg length shows up as slide), and a
capture of source and target side by side every 10 frames.

## P12. Cycle along a path without foot slide

Goal: an in-place walk cycle that travels along a path in Max (for a shot), with the feet planted.

1. Loop check: `maxkit_anim.loop_gap(bones, first, last)` near zero; if the last frame duplicates
   the first, play `first` to `last - 1` [added].
2. Stride: measure the root travel of one cycle from the original root-motion clip, or the distance
   a planted foot covers in one cycle relative to the root.
3. Speed = stride length / cycle duration (frames / frame rate). Set the path dummy's range so path
   length / speed = shot duration.
4. Link the character root to a Dummy on a Path Constraint with Follow and Constant Velocity (P3
   code), cycle keys set to `loop`.
5. Measure foot slide in world space with `contact_slide`; slide in one direction means the speed is
   off by `slide / phase duration`.

## P13. FBX animation export and re-import check

Goal: files an engine imports with the right skeleton, scale, frame range and motion. The glTF
export page says no animation, skin or morpher data is exported (`gltf-export-2027`) while the
2027.3 what's new says animation is supported; until that is checked, animated characters leave as
FBX. `xio.export_fbx` never overwrites: it picks the next free name.

Two files: the skinned mesh in its bind pose (`SK_<name>.fbx`) and each clip with the skeleton
(`A_<name>_<clip>.fbx`) (Norberto Aguilera, 5M7jlvzGWQ4 frames 00:03:48, 00:05:44). In the max file,
keep related clips (walk, trot, run) as CAT layers of one rig and export one clip at a time (Miloš
Černý, 0xKZ5hV4MK8 00:04:05).

Root bone and root motion: the sources give no Unreal rule for a dedicated root bone or for in-place
against root-motion clips. Ask which the engine team wants, export one clip, import it in the
engine, and check that the character moves (root motion) or stays (in place) as asked before
exporting the rest.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (exportFile signature), note 5M7jlvzGWQ4 frames f_00192 and f_00238; FBXExporterSetParam names [verify]
import os
import pymxs
rt = pymxs.runtime
ARGS = {"out": "<export folder>", "name": "Hero", "clip": "Walk", "bake": True, "nodes": ["CHR_Body", "Bip001"]}

first, last = maxkit_anim.frame_range()
sel = []
for n in ARGS["nodes"]:
    root = rt.getNodeByName(n)
    stack = [root]
    while stack:
        cur = stack.pop()
        sel.append(cur)
        stack.extend(list(cur.children))
rt.select(sel)

# keys go through FBXExporterSetParam inside xio.export_fbx; key names are [verify]
common = {"Skin": True, "Shape": True, "Triangulate": False, "UpAxis": "Z"}  # Triangulate off as on frame f_00192
skin_rep = xio.export_fbx(os.path.join(ARGS["out"], f"SK_{ARGS['name']}_v001.fbx"),
                          preset=dict(common, Animation=False), selected=True)
anim_preset = dict(common, Animation=True, BakeAnimation=ARGS["bake"],
                   BakeFrameStart=first, BakeFrameEnd=last, BakeFrameStep=1)
anim_rep = xio.export_fbx(os.path.join(ARGS["out"], f"A_{ARGS['name']}_{ARGS['clip']}_v001.fbx"),
                          preset=anim_preset, selected=True)
readback = {k: str(rt.FBXExporterGetParam(k)) for k in anim_preset}  # getter documented in 2027; a wrong key shows here
result = {"skin": skin_rep, "anim": anim_rep, "readback": readback, "range": (first, last),
          "frame_rate": maxkit_anim.units_report()["frame_rate"], "exported_nodes": len(sel)}
```

Bake decision:

- Bake on when motion comes from constraints, IK solvers, wires, expressions, CAT, path constraints
  or layers not yet collapsed [added].
- The expert exported a keyed Biped with Bake Animation off and it played in Unreal (5M7jlvzGWQ4
  frame f_00238). Bake on is the safe default for an agent [added].
- In the dialog the same frame shows TurboSmooth on, Convert Deforming Dummies to Bones on, Preserve
  edge orientation on, Tangents and Binormals off (f_00192). Their script names are unknown here:
  set them in the GUI preset or check `FBXExporterGetParam` [verify].

Re-import check, in `batch` on an empty scene: run P1 on each exported file. Pass: same bone count
and names as the source, height within 2% of the source, range equals `(first, last)`, frame rate
equal. In Unreal, "bones missing from the bind pose" listing only Nub and Xtra end bones is about
unweighted end bones and is harmless; the engine suggests Use T0 as ref pose (f_00324).
