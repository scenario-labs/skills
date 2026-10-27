# Epic Unreal MCP for animation: toolsets, signatures, live recipes

Run on UE 5.8.3 (macOS) on 2026-10-21 against engine template content only (the Third Person and
Characters packs: SKM_Manny_Simple, SKM_Quinn_Simple, SK_Mannequin, CR_Mannequin_Body, the MM_*
clips) and Epic's FBX test file `Engine/Content/FbxEditorAutomation/AnimatedCharacter.fbx`.
`tests/code/unreal-animation/live_mcp_recipes.py` builds its own project, starts and stops its own
editor, runs every `# script:` block of this page as written plus the Python recipes, and exits 0
only if all pass. Object references are `{"refPath": "/Game/Folder/Asset.Asset"}`.

**Batch first.** Four or more toolset calls in a row go in one
`editor_toolset.toolsets.programmatic.ProgrammaticToolset.execute_tool_script {"script": "..."}`
call: the script defines `run()`, calls `execute_tool("<toolset>.<tool>", json_string)` (it returns
the result dict; read `["returnValue"]`), returns a dict (it comes back as a JSON string), and may
import only json, math, re, time, datetime and copy (no `unreal`). Change only the `ARGS` line of a
script below. A failing tool ends the script with its traceback and keeps what was created before
it, so keep calls that may fail (name probes) as single `call_tool` calls.

There is no Epic agent skill for animation in the 5.8.3 `AgentSkillToolset` list, so nothing here is
reconciled against one.

## Which tool for which intent

| Intent                                                       | Tool                                                                             | Notes (run on 5.8.3)                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bones, sockets, slots, LODs, morphs of a skeletal mesh       | `editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools`                        | script A1. `get_bone_names` lists the Skeleton asset's bones (161 for SK_Mannequin) even on SKM_Manny_Simple, whose own reference skeleton has 89 (Python `SkeletonModifier`); count mesh bones in Python                                                                                                 |
| Import a skeletal FBX with its animation and a physics asset | `SkeletalMeshTools.import_file`                                                  | `{"source_file", "folder_path", "asset_name", "import_animations": true, "create_physics_asset": true}`; bone names may come back renumbered (`ShoulderLeft4` where the Interchange import of the same file gave `ShoulderLeft1`), so clips imported one way do not fit a skeleton imported the other way |
| Physics asset from a mesh, bodies, shapes, constraints       | `PhysicsToolsets.PhysicsAssetToolset`                                            | script A2. `CreateFromMesh` `meshPath` is the PACKAGE path; on an existing `<Mesh>_PhysicsAsset` it returns that asset unchanged                                                                                                                                                                          |
| Control Rig asset: hierarchy, controls, forward-solve graph  | `animation_toolset.toolsets.controlrig.ControlRigTools`                          | script A3. A new rig's forward graph is empty: add the event node yourself                                                                                                                                                                                                                                |
| Animate a Control Rig in a Level Sequence                    | `animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools`       | script A4. Keys land only while the sequence is open (`SequencerTools.open_sequence`)                                                                                                                                                                                                                     |
| Raw channel keys on any section                              | `animation_toolset.toolsets.keyframing.SequencerKeyframingTools`                 | channel names `spine_03_ctrl.Rotation.Z` (yaw), `.Rotation.Y` (pitch); `get_keys` returns JSON text                                                                                                                                                                                                       |
| Sequence to AnimSequence, FBX in and out                     | `animation_toolset.toolsets.import_export.SequencerImportExportTools`            | `export_anim_sequence` needs an existing AnimSequence with the right skeleton (create it in Python); see the bake trap                                                                                                                                                                                    |
| Hand-keyed AnimSequence, montage, notifies, root motion      | Python (`ue_anim.create_keyed_sequence`, `create_montage`, `ensure_root_motion`) | no toolset writes AnimSequence keys; works headless and in a commandlet                                                                                                                                                                                                                                   |
| IK Rig, retargeter, batch retarget                           | Python (`create_ik_rig`, `create_retargeter`, `batch_retarget`)                  | no toolset; recipe P2                                                                                                                                                                                                                                                                                     |
| AnimBP flags, compile                                        | Python `animbp_settings`, `compile_and_scan`                                     | `BlueprintTools.compile_blueprint` also compiles an AnimBP                                                                                                                                                                                                                                                |

## Recipes as scripts (each ran as written on 5.8.3)

### A1. Inspect a skeletal mesh and add a socket (11 calls)

```python
# script: A1_skeletal_mesh
ARGS = {"mesh": "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple", "bone": "hand_r",
        "socket": "weapon_r", "offset": {"x": 5, "y": -2, "z": 0}}
import json
SK = "editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools."

def call(tool, **kw):
    return execute_tool(SK + tool, json.dumps(kw)).get("returnValue")

def run():
    m = {"refPath": ARGS["mesh"]}
    bones = call("get_bone_names", mesh=m)
    if ARGS["socket"] not in call("get_socket_names", mesh=m):
        call("add_socket", mesh=m, bone_name=ARGS["bone"], socket_name=ARGS["socket"])
    call("set_socket_transform", mesh=m, socket_name=ARGS["socket"],
         transform={"location": ARGS["offset"], "rotation": {"pitch": 0, "yaw": 90, "roll": 0}, "scale": {"x": 1, "y": 1, "z": 1}})
    return {"bones": len(bones), "skeleton": call("get_skeleton", mesh=m)["refPath"],
            "parent_of_bone": call("get_bone_parent", mesh=m, bone_name=ARGS["bone"]),
            "slots": call("get_material_slots", mesh=m), "morphs": call("get_morph_target_names", mesh=m),
            "lods": call("get_lod_count", mesh=m), "verts_lod0": call("get_vertex_count", mesh=m, lod_index=0),
            "physics": (call("get_physics_asset", mesh=m) or {}).get("refPath"),
            "socket_bone": call("get_socket_bone", mesh=m, socket_name=ARGS["socket"]),
            "socket_xf": call("get_socket_transform", mesh=m, socket_name=ARGS["socket"])}
```

Result on SKM_Quinn_Simple: 161 bones, slots `Quinn_01`, `Quinn_02`, 3 LODs, 45,993 vertices on LOD
0, physics asset PA_Mannequin, no morph targets, the socket on `hand_r` read back at the offset
given. `set_socket_transform` returns null on success. `rename_socket`, `remove_socket`,
`set_material`, `assign_physics_asset` follow the same shapes (signatures below).

### A2. Physics asset: create, add a head sphere, pin the pelvis, limit the knee (10 to 12 calls)

```python
# script: A2_physics_asset
ARGS = {"mesh_package": "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple", "pinned": "pelvis", "head_radius": 11.0}
import json
PA = "PhysicsToolsets.PhysicsAssetToolset."

def call(tool, **kw):
    return execute_tool(PA + tool, json.dumps(kw)).get("returnValue")

def run():
    pa = call("CreateFromMesh", meshPath=ARGS["mesh_package"], bAssignToMesh=False)
    bodies = call("GetBodyNames", physicsAsset=pa)
    if "head" not in bodies:
        call("AddBody", physicsAsset=pa, boneName="head")
    call("SetSphere", physicsAsset=pa, boneName="head", shapeName="HeadSphere",
         center={"x": 10, "y": 2, "z": 0}, radius=ARGS["head_radius"])
    parent = next(b for b in ("neck_02", "neck_01", "spine_05") if b in bodies)   # auto bodies vary per mesh
    call("AddConstraint", physicsAsset=pa, bone1Name="head", bone2Name=parent)
    call("SetConstraintLimits", physicsAsset=pa, info={"bone1Name": "calf_l", "bone2Name": "thigh_l",
         "swing1Motion": "Locked", "swing1LimitDegrees": 0, "swing2Motion": "Limited", "swing2LimitDegrees": 70,
         "twistMotion": "Locked", "twistLimitDegrees": 0})
    call("SetBodyPhysicsMode", physicsAsset=pa, boneName=ARGS["pinned"], mode="Kinematic")
    cons = [c for c in call("GetConstraints", physicsAsset=pa) if c["bone1Name"] in ("calf_l", "head")]
    return {"physics_asset": pa["refPath"], "bodies": len(call("GetBodyNames", physicsAsset=pa)),
            "head": call("GetBodyShapes", physicsAsset=pa, boneName="head"),
            "head_parent": parent, "pinned_mode": call("GetBodyPhysicsMode", physicsAsset=pa, boneName=ARGS["pinned"]), "constraints": cons}
```

Result on Quinn: 13 generated bodies (pelvis, spine_02, spine_04, spine_05, neck_02, upperarm, hand,
thigh and calf per side) plus the added head, capsules on limbs (upperarm_l radius 8.64, length
29.0), every generated constraint Limited 45/45/45, a new constraint Free 45/45/45 until set.
Manny's generated set has no `neck_02` body, hence the parent lookup. Shapes: `SetCapsule` (center,
rotation, radius, length), `SetBox` (extentX, Y, Z), `SetSphere`. Modes: `Default`, `Kinematic`,
`Simulated`. Motions: `Free`, `Limited`, `Locked`.

### A3. Control Rig with imported bones, a control and a forward-solve graph (17 calls)

```python
# script: A3_control_rig
ARGS = {"path": "/Game/Rigs/CR_Script", "mesh": "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple",
        "bone": "hand_r", "control": "hand_r_ctrl"}
import json
CR = "animation_toolset.toolsets.controlrig.ControlRigTools."

def call(tool, **kw):
    return execute_tool(CR + tool, json.dumps(kw)).get("returnValue")

def run():
    cr = call("create", path=ARGS["path"])
    bones = call("import_bones_from_asset", control_rig=cr, skeletal_mesh={"refPath": ARGS["mesh"]})
    bone = {"type": "Bone", "name": ARGS["bone"]}
    ctrl = call("add_control", control_rig=cr, name=ARGS["control"], parent=bone)
    # put the control on the bone: initial global transform of the control = the bone's
    xf = call("get_global_transform", control_rig=cr, item=bone, initial=True)
    call("set_global_transform", control_rig=cr, item=ctrl, transform=xf, initial=True)
    g = call("get_forward_solve_graph", control_rig=cr)
    base = g["refPath"]
    ev = call("add_event_node", control_rig=cr, graph=g, event_type="FORWARD_SOLVE")
    get = call("create_node", control_rig=cr, graph=g, node_name="GetCtrl", node_type="RigUnit_GetTransform",
               position={"x": 200, "y": 0})
    put = call("create_node", control_rig=cr, graph=g, node_name="SetBone", node_type="RigUnit_SetTransform",
               position={"x": 500, "y": 0})
    pin = lambda node, p: {"refPath": node["refPath"] + "." + p}
    call("set_pin_value", control_rig=cr, graph=g, pin=pin(get, "Item"), value='(Type=Control,Name="%s")' % ARGS["control"])
    call("set_pin_value", control_rig=cr, graph=g, pin=pin(put, "Item"), value='(Type=Bone,Name="%s")' % ARGS["bone"])
    call("connect_pins", control_rig=cr, graph=g, source_pin=pin(get, "Transform"), target_pin=pin(put, "Value"))
    call("connect_pins", control_rig=cr, graph=g, source_pin=pin(ev, "ExecutePin"), target_pin=pin(put, "ExecutePin"))
    return {"rig": cr["refPath"], "bones": len(bones), "controls": call("get_all_controls", control_rig=cr),
            "control_global": call("get_global_transform", control_rig=cr, item=ctrl, initial=True),
            "nodes": [n["refPath"].rsplit(".", 1)[-1] for n in call("list_nodes", control_rig=cr, graph=g)],
            "set_item": call("get_pin_value", control_rig=cr, pin=pin(put, "Item")),
            "value_from": [p["refPath"].rsplit(":", 1)[-1] for p in call("get_connected_pins", control_rig=cr, pin=pin(put, "Value"))]}
```

Traps: `import_bones_from_asset` brings the Skeleton's 161 bones, not the mesh's 89. `node_type`
takes the RigUnit struct name (`RigUnit_GetTransform`, `RigUnit_SetTransform`, also
`/Script/ControlRig.RigUnit_SetTransform`); node and pin refs are `<rig>:RigVMModel.<Node>.<Pin>`.
`set_pin_value` takes the struct text form `(Type=Bone,Name="hand_r")`. The event node is
`RigUnit_BeginExecution`, exec pin `ExecutePin`. Compile and save afterwards in Python:
`bp.recompile_vm()`, `EditorAssetLibrary.save_asset` (ran).

### A4. Key a Control Rig in a Level Sequence and read it back (about 15 calls)

```python
# script: A4_rig_keys
ARGS = {"folder": "/Game/Cine", "name": "LS_RigKeys", "mesh": "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple",
        "rig": "/Game/Characters/Mannequins/Rigs/CR_Mannequin_Body", "control": "spine_03_ctrl",
        "keys": [[0, 0.0], [30, 25.0]], "fps": 30, "end": 60}
import json
SEQ = "animation_toolset.toolsets.sequencer.SequencerTools."
SCR = "animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools."
ST = "editor_toolset.toolsets.scene.SceneTools."

def call(prefix, tool, **kw):
    return execute_tool(prefix + tool, json.dumps(kw)).get("returnValue")

def run():
    ls = call(SEQ, "create_level_sequence", asset_name=ARGS["name"], package_path=ARGS["folder"])
    call(SEQ, "set_display_rate", sequence=ls, numerator=ARGS["fps"], denominator=1)
    call(SEQ, "set_playback_range", sequence=ls, start_frame=0, end_frame=ARGS["end"])
    xf = {"location": {"x": 0, "y": 0, "z": 100}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0}, "scale": {"x": 1, "y": 1, "z": 1}}
    actor = call(ST, "add_to_scene_from_asset", asset_path=ARGS["mesh"], name="RigKeysActor", xform=xf)
    call(SEQ, "open_sequence", sequence=ls)          # Control Rig keys land only in the open sequence
    binding = call(SEQ, "add_actors", actors=[actor])[0]
    track = json.loads(call(SCR, "find_or_create_track", sequence=ls, binding=binding, control_rig_asset_path=ARGS["rig"]))
    names = [c["name"] for c in json.loads(call(SCR, "get_controls_info", sequence=ls, control_rig_asset_path=ARGS["rig"]))]
    if ARGS["control"] not in names:                  # setters return true for unknown names: check first
        return {"error": "no control " + ARGS["control"], "some_controls": names[:20]}
    for frame, yaw in ARGS["keys"]:
        call(SCR, "set_euler_transform", sequence=ls, control_rig_asset_path=ARGS["rig"], control_name=ARGS["control"],
             frame=frame, rotation_yaw=yaw, set_key=True)
    mid = (ARGS["keys"][0][0] + ARGS["keys"][-1][0]) // 2
    read = {f: json.loads(call(SCR, "get_euler_transform", sequence=ls, control_rig_asset_path=ARGS["rig"],
                               control_name=ARGS["control"], frame=f))["rotation"]["yaw"]
            for f in (ARGS["keys"][0][0], mid, ARGS["keys"][-1][0])}
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets", json.dumps({"asset_paths": [ARGS["folder"] + "/" + ARGS["name"]]}))
    return {"sequence": ls["refPath"], "binding": binding, "track": track["track"], "controls": len(names), "yaw_read": read}
```

Result: CR_Mannequin_Body has 148 controls (117 Euler transform, 23 bool, 6 float, 2 rotator);
`spine_03_ctrl` yaw read 0, 12.5, 25 at frames 0, 15, 30. Traps:

- Before `open_sequence`, every setter returns true and writes nothing; every getter returns zeros.
- The setters also return true for a control name that does not exist (`spine_03_fk_ctrl`,
  `hand_r_ctrl` on this rig): read `get_controls_info` first, as the script does.
- Euler-transform controls take `set_euler_transform`; `set_rotator` on them returns true and keys
  nothing.
- `SequencerKeyframingTools.add_key_float {"section", "channel_name": "spine_03_ctrl.Rotation.Z", "frame", "value", "interpolation": "cubic"}`
  keys the same channel directly and works without the open sequence; `bake_channel_keys` failed
  with the sequence closed.

### Bake trap (run on 5.8.3)

`SequencerImportExportTools.export_anim_sequence {"anim_sequence", "binding", "sequence", "world": {"refPath": "/Game/Map.Map"}, "create_link": true}`
returned true in a headless (`-nullrhi`) editor, but the AnimSequence held the rest pose at every
frame: the Control Rig is not evaluated without a viewport, and scrubbing with
`LevelSequenceEditorBlueprintLibrary.set_current_time` did not move the bound mesh either. Python
`SequencerTools.export_anim_sequence` of a spawnable with an animation track returned false
headless. In an offscreen editor (`-RenderOffscreen`, recipe a7 of `live_mcp_recipes.py`) the same
export returned true and the clip again held one pose (spine_03 yaw -10.95 at frames 0, 15 and 30
for keys 0 to 25). A bake from the GUI editor is not yet run. For clips an agent authors, write the
keys into the AnimSequence directly (`ue_anim.create_keyed_sequence`, offsets read back 0, 10, 20);
always read bone poses back (`AnimPoseExtensions.get_anim_pose_at_frame`) before trusting a bake.

## Python recipes (editor Python next to MCP, or a headless commandlet)

`A` is `ue_anim` (`scripts/ue_anim.py`). All ran on 5.8.3.

```python
# P1: a hand-keyed clip, a montage with a notify, root motion
A.create_keyed_sequence("/Game/Anims/A_Nod", "/Game/Characters/Mannequins/Meshes/SK_Mannequin", 20, 30,
                        {"head": [(20.0 * i / 20, 0, 0) for i in range(21)]})        # (pitch, yaw, roll) per key
A.create_montage("/Game/Anims/A_Nod", "/Game/Anims/AM_Nod", [("Hits", 0.4, "AnimNotify_PlaySound")])
A.set_montage_blend_out("/Game/Anims/AM_Nod", 0.0)
A.ensure_root_motion(["/Game/Anims/A_Death_Copy"], True, "ANIM_FIRST_FRAME")
```

Head pitch offsets read back 0, 10, 20 degrees at frames 0, 10, 20. A clip of N frames has N + 1
keys (`AnimationLibrary.get_num_frames` counts intervals: 33 for a 1.1 s clip at 30 fps); the rate
is on the data model (`seq.get_editor_property("data_model_interface").get_frame_rate()`), not on
`AnimationLibrary`. `unreal.Rotator` positional order is (roll, pitch, yaw): build it with keywords.
A montage from one clip has a `DefaultSlot` track, 0.25 s blend in and out, `blend_out_trigger_time`
-1.

```python
# P2: IK Rigs, retargeter, batch retarget from Manny to a skeleton with other names
A.create_ik_rig("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple", "/Game/Retarget/IK_Manny")       # template: 29 chains
A.create_ik_rig("/Game/Imported/AnimChar/SKM_AnimChar", "/Game/Retarget/IK_AnimChar")                  # template finds 0: plan from the mesh
A.create_retargeter("/Game/Retarget/RTG_Manny_AnimChar", "/Game/Retarget/IK_Manny", "/Game/Retarget/IK_AnimChar",
                    "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple", "/Game/Imported/AnimChar/SKM_AnimChar")
A.batch_retarget(["/Game/Characters/Mannequins/Anims/Death/MM_Death_Front_01"], "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple",
                 "/Game/Imported/AnimChar/SKM_AnimChar", "/Game/Retarget/RTG_Manny_AnimChar", folder="/Game/Retarget/Out")
```

On a skeleton the auto template does not know (Hips1, AbdoBottom1, ShoulderLeft4, ElbowLeft,
HeadEnd), `apply_auto_generated_retarget_definition` and `apply_auto_fbik` return without error and
leave zero chains; `create_ik_rig` then builds the plan from the mesh (7 chains: Spine to the chest
bone, Neck, Head, arms from the shoulder, legs). The default op stack is Pelvis Motion, FK Chains,
Run IK Rig, Root Motion, Remap Curves. `run_batch_retarget` takes `IKRetargetBatchOperationInputs`
with `assets_to_retarget` as AssetData, `ik_retarget_asset`, `target_path`; it returns AssetData.
The retargeted death clip moved the target's hips 126 cm, as the source does.

```python
# P3: imports with explicit options (Interchange)
A.import_character(fbx, "/Game/Imported/Char")                     # mesh, skeleton, physics asset, clip, materials
A.import_animations([fbx], "/Game/Imported/CharAnims", "/Game/Imported/Char/AnimatedCharacter_Skeleton")
```

A refused import returns an empty list to Python and no exception; the reason is only in the log,
which these helpers now return as `errors`. Two refusals seen: a clip that is not frame-aligned at a
forced rate ("Animation length 4.958 is not compatible with import frame-rate 30 fps"; leave
`sample_rate=None`, which sets `custom_bone_animation_sample_rate` 0, "find the best rate", and the
24 fps clip imported with 119 frames), and a file whose bones are missing from the target skeleton
("Unable to retrieve bone index for track").

## When to use Python or a commandlet instead

- **Python only**: AnimSequence keys, montages, notifies, curves, root motion flags, IK Rig and
  retargeter assets, batch retarget, Pose Search notify tags (`add_pose_search_tag`), AnimBP class
  settings, imports with explicit pipelines, facts for the offline checks (`skeletal_mesh_facts`,
  `anim_clip_facts`).
- **Headless commandlet** (`ue_run.run_python`): the same, plus audits and disk checks after an MCP
  session (`tests/code/unreal-animation/job_*.py`).
- **GUI editor** [not yet run]: anything that needs a Control Rig evaluated (bakes, snapping, visual
  review); offscreen did not evaluate it for a bake.

## Signatures (5.8.3 catalog, `gen_toolset_map.py`)

### `PhysicsToolsets.PhysicsAssetToolset` (17 tools, describe is about 6378 tokens)

- `AddBody(boneName: str, physicsAsset: Ref<PhysicsAsset>) -> None`
- `AddConstraint(bone1Name: str, bone2Name: str, physicsAsset: Ref<PhysicsAsset>) -> None`
- `CreateFromMesh(bAssignToMesh: bool, meshPath: str) -> Ref<PhysicsAsset>`
- `GetBodyMassScale(boneName: str, physicsAsset: Ref<PhysicsAsset>) -> float`
- `GetBodyNames(physicsAsset: Ref<PhysicsAsset>) -> [str]`
- `GetBodyPhysicsMode(boneName: str, physicsAsset: Ref<PhysicsAsset>) -> enum(Default|Kinematic|Simulated)`
- `GetBodyShapes(boneName: str, physicsAsset: Ref<PhysicsAsset>) -> [{PhysicsShapeInfo}]`
- `GetConstraints(physicsAsset: Ref<PhysicsAsset>) -> [{PhysicsConstraintInfo}]`
- `RemoveBody(boneName: str, physicsAsset: Ref<PhysicsAsset>) -> None`
- `RemoveConstraint(bone1Name: str, bone2Name: str, physicsAsset: Ref<PhysicsAsset>) -> None`
- `RemoveShape(boneName: str, physicsAsset: Ref<PhysicsAsset>, shapeName: str) -> None`
- `SetBodyMassScale(boneName: str, massScale: float, physicsAsset: Ref<PhysicsAsset>) -> None`
- `SetBodyPhysicsMode(boneName: str, mode: enum(Default|Kinematic|Simulated), physicsAsset: Ref<PhysicsAsset>) -> None`
- `SetBox(boneName: str, center: {Vector}, extentX: float, extentY: float, extentZ: float, physicsAsset: Ref<PhysicsAsset>, rotation: {Rotator}, shapeName: str) -> None`
- `SetCapsule(boneName: str, center: {Vector}, length: float, physicsAsset: Ref<PhysicsAsset>, radius: float, rotation: {Rotator}, shapeName: str) -> None`
- `SetConstraintLimits(info: {PhysicsConstraintInfo}, physicsAsset: Ref<PhysicsAsset>) -> None`
- `SetSphere(boneName: str, center: {Vector}, physicsAsset: Ref<PhysicsAsset>, radius: float, shapeName: str) -> None`

### `animation_toolset.toolsets.controlrig.ControlRigTools` (44 tools, describe is about 27990 tokens)

- `add_backward_solve_graph(control_rig: Ref<ControlRigBlueprint>, name?: str) -> Ref<RigVMGraph>`
- `add_bone(control_rig: Ref<ControlRigBlueprint>, name: str, parent?: {RigElementKey}, transform?: {ToolsetTransform}) -> {RigElementKey}`
- `add_control(control_rig: Ref<ControlRigBlueprint>, name: str, parent?: {RigElementKey}, settings?: {RigControlSettings}) -> {RigElementKey}`
- `add_element(control_rig: Ref<ControlRigBlueprint>, element_type: str, name: str, parent?: {RigElementKey}, transform?: {ToolsetTransform}) -> {RigElementKey}`
- `add_event_graph(control_rig: Ref<ControlRigBlueprint>, event_type: enum(FORWARD_SOLVE|BACKWARD_SOLVE|INTERACTION), name?: str) -> Ref<RigVMGraph>`
- `add_event_node(control_rig: Ref<ControlRigBlueprint>, event_type: enum(FORWARD_SOLVE|BACKWARD_SOLVE|INTERACTION), graph: Ref<RigVMGraph>, position?: {Vector2D}) -> Ref<RigVMNode>`
- `add_graph(control_rig: Ref<ControlRigBlueprint>, name: str) -> Ref<RigVMGraph>`
- `add_interaction_graph(control_rig: Ref<ControlRigBlueprint>, name?: str) -> Ref<RigVMGraph>`
- `add_null(control_rig: Ref<ControlRigBlueprint>, name: str, parent?: {RigElementKey}, transform?: {ToolsetTransform}) -> {RigElementKey}`
- `add_variable(control_rig: Ref<ControlRigBlueprint>, default_value: str, is_public?: bool, is_read_only?: bool, name: str, type_path: str) -> None`
- `add_variable_node(control_rig: Ref<ControlRigBlueprint>, graph: Ref<RigVMGraph>, is_getter?: bool, position?: {Vector2D}, variable_name: str) -> Ref<RigVMNode>`
- `change_variable_type(control_rig: Ref<ControlRigBlueprint>, name: str, new_type: str) -> None`
- `connect_pins(control_rig: Ref<ControlRigBlueprint>, graph: Ref<RigVMGraph>, source_pin: Ref<RigVMPin>, target_pin: Ref<RigVMPin>) -> None`
- `create(path: str) -> Ref<ControlRigBlueprint>`
- `create_node(control_rig: Ref<ControlRigBlueprint>, graph: Ref<RigVMGraph>, node_name: str, node_type: str, position?: {Vector2D}) -> Ref<RigVMNode>`
- `delete_node(control_rig: Ref<ControlRigBlueprint>, graph: Ref<RigVMGraph>, node: Ref<RigVMNode>) -> None`
- `disconnect_pins(control_rig: Ref<ControlRigBlueprint>, graph: Ref<RigVMGraph>, source_pin: Ref<RigVMPin>, target_pin: Ref<RigVMPin>) -> None`
- `get_all_bones(control_rig: Ref<ControlRigBlueprint>) -> [{RigElementKey}]`
- `get_all_controls(control_rig: Ref<ControlRigBlueprint>) -> [{RigElementKey}]`
- `get_all_nulls(control_rig: Ref<ControlRigBlueprint>) -> [{RigElementKey}]`
- `get_backward_solve_graph(control_rig: Ref<ControlRigBlueprint>) -> Ref<RigVMGraph>`
- `get_children(control_rig: Ref<ControlRigBlueprint>, item: {RigElementKey}, recursive?: bool) -> [{RigElementKey}]`
- `get_connected_pins(control_rig: Ref<ControlRigBlueprint>, pin: Ref<RigVMPin>) -> [Ref<RigVMPin>]`
- `get_elements(control_rig: Ref<ControlRigBlueprint>, element_type?: enum(None|Bone|Null|+12)) -> [{RigElementKey}]`
- `get_event_graph(control_rig: Ref<ControlRigBlueprint>, event_type: enum(FORWARD_SOLVE|BACKWARD_SOLVE|INTERACTION)) -> Ref<RigVMGraph>`
- `get_forward_solve_graph(control_rig: Ref<ControlRigBlueprint>) -> Ref<RigVMGraph>`
- `get_global_transform(control_rig: Ref<ControlRigBlueprint>, initial?: bool, item: {RigElementKey}) -> {ToolsetTransform}`
- `get_graph(control_rig: Ref<ControlRigBlueprint>, graph_name: str) -> Ref<RigVMGraph>`
- `get_interaction_graph(control_rig: Ref<ControlRigBlueprint>) -> Ref<RigVMGraph>`
- `get_local_transform(control_rig: Ref<ControlRigBlueprint>, initial?: bool, item: {RigElementKey}) -> {ToolsetTransform}`
- `get_node_position(control_rig: Ref<ControlRigBlueprint>, node: Ref<RigVMNode>) -> {Vector2D}`
- `get_parent(control_rig: Ref<ControlRigBlueprint>, item: {RigElementKey}) -> {RigElementKey}`
- `get_pin_value(control_rig: Ref<ControlRigBlueprint>, pin: Ref<RigVMPin>) -> str`
- `get_variable(control_rig: Ref<ControlRigBlueprint>, name: str) -> {RigVMGraphVariableDescription}`
- `import_bones_from_asset(control_rig: Ref<ControlRigBlueprint>, skeletal_mesh: Ref<SkeletalMesh>) -> [{RigElementKey}]`
- `list_graphs(control_rig: Ref<ControlRigBlueprint>) -> [Ref<RigVMGraph>]`
- `list_nodes(control_rig: Ref<ControlRigBlueprint>, graph: Ref<RigVMGraph>) -> [Ref<RigVMNode>]`
- `list_pins(control_rig: Ref<ControlRigBlueprint>, node: Ref<RigVMNode>) -> [Ref<RigVMPin>]`
- `list_variables(control_rig: Ref<ControlRigBlueprint>) -> [{RigVMGraphVariableDescription}]`
- `remove_variable(control_rig: Ref<ControlRigBlueprint>, name: str) -> None`
- `set_global_transform(control_rig: Ref<ControlRigBlueprint>, initial?: bool, item: {RigElementKey}, transform: {ToolsetTransform}) -> None`
- `set_local_transform(control_rig: Ref<ControlRigBlueprint>, initial?: bool, item: {RigElementKey}, transform: {ToolsetTransform}) -> None`
- `set_node_position(control_rig: Ref<ControlRigBlueprint>, graph: Ref<RigVMGraph>, node: Ref<RigVMNode>, position: {Vector2D}) -> None`
- `set_pin_value(control_rig: Ref<ControlRigBlueprint>, graph: Ref<RigVMGraph>, pin: Ref<RigVMPin>, value: str) -> None`

### `animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools` (72 tools, describe is about 22245 tokens)

- `add_layer_from_selection() -> int`
- `bake_space(control_names: [str], control_rig_asset_path: str, end_frame: int, reduce_keys?: bool, sequence: Ref<LevelSequence>, start_frame: int, tolerance?: float) -> bool`
- `bake_to_control_rig(binding: {MovieSceneBindingProxy}, control_rig_asset_path: str, reduce_keys?: bool, reset_controls?: bool, sequence: Ref<LevelSequence>, tolerance?: float) -> bool`
- `blend_values_on_selected(blend_value: float, operation: str, sequence: Ref<LevelSequence>) -> bool`
- `clear_selection() -> bool`
- `collapse_anim_layers(control_rig_asset_path: str, reduce_keys?: bool, sequence: Ref<LevelSequence>, tolerance?: float) -> bool`
- `delete_anim_layer(index: int) -> bool`
- `delete_space(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> bool`
- `duplicate_anim_layer(index: int) -> int`
- `export_fbx_from_rig(ascii?: bool, control_rig_asset_path: str, export_file_path: str, sequence: Ref<LevelSequence>) -> bool`
- `find_or_create_track(binding: {MovieSceneBindingProxy}, control_rig_asset_path: str, is_layered?: bool, sequence: Ref<LevelSequence>) -> str`
- `frame_selection() -> bool`
- `get_actor_transform_at_frame(actor_name: str, frame: int, sequence: Ref<LevelSequence>) -> str`
- `get_anim_layers() -> str`
- `get_anim_mode_gizmo_scale() -> float`
- `get_anim_mode_hide_manips() -> bool`
- `get_anim_mode_hierarchy() -> bool`
- `get_anim_mode_local_spaces() -> bool`
- `get_anim_mode_nulls() -> bool`
- `get_anim_mode_only_rig_sel() -> bool`
- `get_bool(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> bool`
- `get_control_rigs(sequence: Ref<LevelSequence>) -> str`
- `get_controls_info(control_rig_asset_path: str, sequence: Ref<LevelSequence>) -> str`
- `get_controls_mask(control_name: str, section: Ref<MovieSceneSection>) -> bool`
- `get_euler_transform(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> str`
- `get_float(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> float`
- `get_int(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> int`
- `get_position(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> str`
- `get_priority_order(control_rig_asset_path: str, sequence: Ref<LevelSequence>) -> int`
- `get_rotator(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> str`
- `get_scale(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> str`
- `get_selected_controls(control_rig_asset_path: str, sequence: Ref<LevelSequence>) -> [str]`
- `get_transform(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> str`
- `get_vector2d(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> str`
- `get_world_transform(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>) -> str`
- `hide_all_controls(section: Ref<MovieSceneSection>) -> bool`
- `import_fbx_to_rig(control_rig_asset_path: str, import_file_path: str, selected_controls: [str], sequence: Ref<LevelSequence>) -> bool`
- `is_fk_control_rig(control_rig_asset_path: str, sequence: Ref<LevelSequence>) -> bool`
- `is_layered_control_rig(control_rig_asset_path: str, sequence: Ref<LevelSequence>) -> bool`
- `key_controls(control_names: [str], section: Ref<MovieSceneSection>) -> bool`
- `key_controls_at_frames(control_names: [str], frames: [int], section: Ref<MovieSceneSection>) -> bool`
- `load_anim_into_rig(anim_sequence_path: str, cr_section: Ref<MovieSceneSection>, key_reduce?: bool, reset_controls?: bool, start_frame?: int, tolerance?: float) -> bool`
- `merge_anim_layers(indices: [int]) -> bool`
- `mirror_selected_controls() -> bool`
- `move_space(control_name: str, control_rig_asset_path: str, new_frame: int, old_frame: int, sequence: Ref<LevelSequence>) -> bool`
- `reorder_anim_layers(new_index: int, old_index: int) -> bool`
- `select_control(control_name: str, control_rig_asset_path: str, selected?: bool, sequence: Ref<LevelSequence>) -> bool`
- `select_mirrored_controls() -> bool`
- `set_anim_mode_gizmo_scale(scale: float) -> bool`
- `set_anim_mode_hide_manips(hide: bool) -> bool`
- `set_anim_mode_hierarchy(enabled: bool) -> bool`
- `set_anim_mode_local_spaces(enabled: bool) -> bool`
- `set_anim_mode_nulls(enabled: bool) -> bool`
- `set_anim_mode_only_rig_sel(only_rig: bool) -> bool`
- `set_bool(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>, set_key?: bool, value: bool) -> bool`
- `set_controls_mask(control_names: [str], section: Ref<MovieSceneSection>, visible: bool) -> bool`
- `set_euler_transform(control_name: str, control_rig_asset_path: str, frame: int, location_x?: float, location_y?: float, location_z?: float, rotation_pitch?: float, rotation_roll?: float, rotation_yaw?: float, scale_x?: float, scale_y?: float, scale_z?: float, sequence: Ref<LevelSequence>, set_key?: bool) -> bool`
- `set_float(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>, set_key?: bool, value: float) -> bool`
- `set_int(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>, set_key?: bool, value: int) -> bool`
- `set_layered_mode(control_rig_asset_path: str, is_layered: bool, sequence: Ref<LevelSequence>) -> bool`
- `set_position(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>, set_key?: bool, x?: float, y?: float, z?: float) -> bool`
- `set_priority_order(control_rig_asset_path: str, order: int, sequence: Ref<LevelSequence>) -> bool`
- `set_rotator(control_name: str, control_rig_asset_path: str, frame: int, pitch?: float, roll?: float, sequence: Ref<LevelSequence>, set_key?: bool, yaw?: float) -> bool`
- `set_scale(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>, set_key?: bool, x?: float, y?: float, z?: float) -> bool`
- `set_space(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>, space_target: str, space_type: str) -> bool`
- `set_transform(control_name: str, control_rig_asset_path: str, frame: int, location_x?: float, location_y?: float, location_z?: float, rotation_pitch?: float, rotation_roll?: float, rotation_yaw?: float, sequence: Ref<LevelSequence>, set_key?: bool) -> bool`
- `set_vector2d(control_name: str, control_rig_asset_path: str, frame: int, sequence: Ref<LevelSequence>, set_key?: bool, x?: float, y?: float) -> bool`
- `set_world_transform(control_name: str, control_rig_asset_path: str, frame: int, location_x?: float, location_y?: float, location_z?: float, rotation_pitch?: float, rotation_roll?: float, rotation_yaw?: float, sequence: Ref<LevelSequence>, set_key?: bool) -> bool`
- `show_all_controls(section: Ref<MovieSceneSection>) -> bool`
- `snap_control_rig(control_names: [str], control_rig_asset_path: str, end_frame: int, keep_offset?: bool, sequence: Ref<LevelSequence>, snap_position?: bool, snap_rotation?: bool, snap_scale?: bool, start_frame: int, target_actor_name: str) -> bool`
- `tween_control_rig(control_rig_asset_path: str, sequence: Ref<LevelSequence>, tween_value: float) -> bool`
- `zero_transforms(include_channels?: bool, selection_only?: bool) -> bool`

### `editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools` (22 tools, describe is about 8480 tokens)

- `add_socket(bone_name: str, mesh: Ref<SkeletalMesh>, socket_name: str) -> Ref<SkeletalMeshSocket>`
- `assign_physics_asset(mesh: Ref<SkeletalMesh>, physics_asset: Ref<PhysicsAsset>) -> bool`
- `get_bone_children(bone_name: str, mesh: Ref<SkeletalMesh>) -> [str]`
- `get_bone_names(mesh: Ref<SkeletalMesh>) -> [str]`
- `get_bone_parent(bone_name: str, mesh: Ref<SkeletalMesh>) -> str`
- `get_bounds(mesh: Ref<SkeletalMesh>) -> {BoxSphereBounds}`
- `get_lod_count(mesh: Ref<SkeletalMesh>) -> int`
- `get_material(mesh: Ref<SkeletalMesh>, slot_name: str) -> Ref<MaterialInterface>`
- `get_material_slots(mesh: Ref<SkeletalMesh>) -> [str]`
- `get_morph_target_names(mesh: Ref<SkeletalMesh>) -> [str]`
- `get_physics_asset(mesh: Ref<SkeletalMesh>) -> Ref<PhysicsAsset>`
- `get_section_count(lod_index?: int, mesh: Ref<SkeletalMesh>) -> int`
- `get_skeleton(mesh: Ref<SkeletalMesh>) -> Ref<Skeleton>`
- `get_socket_bone(mesh: Ref<SkeletalMesh>, socket_name: str) -> str`
- `get_socket_names(mesh: Ref<SkeletalMesh>) -> [str]`
- `get_socket_transform(mesh: Ref<SkeletalMesh>, socket_name: str) -> {ToolsetTransform}`
- `get_vertex_count(lod_index?: int, mesh: Ref<SkeletalMesh>) -> int`
- `import_file(asset_name: str, create_physics_asset?: bool, folder_path: str, import_animations?: bool, import_materials?: bool, import_textures?: bool, skeleton?: Ref<Skeleton>, source_file: str) -> [Ref<Object>]`
- `remove_socket(mesh: Ref<SkeletalMesh>, socket_name: str) -> bool`
- `rename_socket(mesh: Ref<SkeletalMesh>, new_name: str, old_name: str) -> bool`
- `set_material(material: Ref<MaterialInterface>, mesh: Ref<SkeletalMesh>, slot_name: str) -> bool`
- `set_socket_transform(mesh: Ref<SkeletalMesh>, socket_name: str, transform: {ToolsetTransform}) -> None`

### `animation_toolset.toolsets.import_export.SequencerImportExportTools` (6 tools, describe is about 3612 tokens)

- `export_anim_sequence(anim_sequence: Ref<AnimSequence>, binding: {MovieSceneBindingProxy}, create_link?: bool, sequence: Ref<LevelSequence>, world: Ref<World>) -> bool`
- `export_fbx(bindings: [{MovieSceneBindingProxy}], fbx_file_path: str, override_options?: Ref<FbxExportOption>, sequence: Ref<LevelSequence>, world: Ref<World>) -> bool`
- `get_linked_anim_sequences(sequence: Ref<LevelSequence>) -> [str]`
- `get_linked_level_sequence(anim_sequence: Ref<AnimSequence>) -> str`
- `import_fbx(bindings: [{MovieSceneBindingProxy}], fbx_file_path: str, import_settings: Ref<MovieSceneUserImportFBXSettings>, sequence: Ref<LevelSequence>, world: Ref<World>) -> bool`
- `link_anim_sequence(anim_sequence: Ref<AnimSequence>, binding: {MovieSceneBindingProxy}, sequence: Ref<LevelSequence>) -> bool`

### `animation_toolset.toolsets.keyframing.SequencerKeyframingTools` (22 tools, describe is about 6464 tokens)

- `add_key_bool(channel_name: str, frame: int, section: Ref<MovieSceneSection>, value: bool) -> bool`
- `add_key_float(channel_name: str, frame: int, interpolation: str, section: Ref<MovieSceneSection>, value: float) -> bool`
- `add_key_integer(channel_name: str, frame: int, section: Ref<MovieSceneSection>, value: int) -> bool`
- `add_key_string(channel_name: str, frame: int, section: Ref<MovieSceneSection>, value: str) -> bool`
- `bake_channel_keys(channel_name: str, end_frame: int, section: Ref<MovieSceneSection>, start_frame: int) -> [float]`
- `close_curve_editor() -> bool`
- `curve_editor_empty_selection() -> bool`
- `curve_editor_select_keys(channel: {SequencerChannelProxy}, indices: [int]) -> bool`
- `get_channel_names(section: Ref<MovieSceneSection>) -> [str]`
- `get_curve_editor_selected_keys(channel: {SequencerChannelProxy}) -> [int]`
- `get_default_value(channel_name: str, section: Ref<MovieSceneSection>) -> float`
- `get_keys(channel_name: str, section: Ref<MovieSceneSection>) -> str`
- `get_keys_by_index(channel_name: str, indices: [int], section: Ref<MovieSceneSection>) -> str`
- `get_selected_channels() -> [{SequencerChannelProxy}]`
- `get_selected_key_channels() -> [{SequencerChannelProxy}]`
- `is_curve_editor_open() -> bool`
- `is_curve_shown(channel: {SequencerChannelProxy}) -> bool`
- `open_curve_editor() -> bool`
- `remove_key_at_frame(channel_name: str, frame: int, section: Ref<MovieSceneSection>) -> bool`
- `select_channels(channels: [{SequencerChannelProxy}]) -> bool`
- `set_default_value(channel_name: str, section: Ref<MovieSceneSection>, value: float) -> bool`
- `show_curve(channel: {SequencerChannelProxy}, show: bool) -> bool`
