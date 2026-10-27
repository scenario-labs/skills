# World building through Epic's Unreal MCP (5.8.3)

Everything here ran on 5.8.3 (2026-10-21) unless a line says otherwise; signature lines come from
the 5.8.3 catalog. Runner: `tests/code/unreal-world-building/live_mcp_recipes.py` reads the
`# script:` blocks below from this file, runs each one through `execute_tool_script` in its own
offscreen editor, audits the result on the host with `ue_world`, and exits 0 only if every recipe
passes.

**Batch first.** Four or more toolset calls in a row go in one
`ProgrammaticToolset.execute_tool_script` call: the script defines `run()`, calls
`execute_tool("<toolset>.<tool>", json_string)`, returns a dict, and may import only json, math, re,
time, datetime and copy (no `unreal`). Call `get_execution_environment` once per session, before the
first script. A failing tool aborts the whole script and `try/except` did not catch it on 5.8.3;
actors made before the failure stay, so read the level back before re-running. Keep calls expected
to fail as single `call_tool` calls. Do not `time.sleep` inside a script to wait for PCG generation
or a navmesh build: read the result in the next call.

Short names: ST `editor_toolset.toolsets.scene.SceneTools`, AC `...actor.ActorTools`, OT
`...object.ObjectTools`, PR `...primitive.PrimitiveTools`, AT `...asset.AssetTools`, PCG
`PCGToolset.PCGToolset`, SP `PCGToolset.PCGSpatialToolset`, PT
`editor_toolset.toolsets.programmatic.ProgrammaticToolset`.

## 1. Intent to tool

| Intent                                    | Tool                                                                                                                                                    | Notes (run on 5.8.3)                                                                                                                                                                                                                |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New level, open-world map                 | Python `LevelEditorSubsystem.new_level(path, is_partitioned_world=...)`, `ue_world.new_open_world_map`                                                  | `AssetTools.duplicate` of a map makes a dirty map that `save_assets` will not save and `load_level` refuses ("the level has unsaved changes")                                                                                       |
| Repeated geometry (pillars, posts, fence) | ST `add_to_scene_from_class` an `Actor`, AC `add_component` an `InstancedStaticMeshComponent`, OT `set_properties` `StaticMesh` and `PerInstanceSMData` | one actor, one draw per mesh; `PerInstanceSMData` takes the MATRIX form; a growing write drops the last entry to the origin, so write twice (W1)                                                                                    |
| Same from Python                          | `ue_world.add_instanced_mesh` (`SubobjectDataSubsystem.add_new_subobject`)                                                                              | `Actor.add_component_by_class` is not exposed; instances persist after save and reload; HISM works too                                                                                                                              |
| A wall, a slab, a block                   | PR `add_cube {"actor", "name", "dimensions", "local_transform"}`                                                                                        | dimensions in cm, centered on the local transform                                                                                                                                                                                   |
| Group and find                            | AC `add_tag`, ST `set_actor_folder`, `find_actors`, `get_actors_in_folder`                                                                              | `find_actors` `name` matches label substrings: "Pillar" also finds "PillarRing"                                                                                                                                                     |
| Audit what was built                      | OT `get_properties` `PerInstanceSMData`; ST `find_actors`                                                                                               | `get_actor_bounds` on an empty-root Actor includes a phantom 256 cm box at its origin (z -128 under a ring at z 150) and lagged behind instance edits in one probe: audit instance transforms and component sizes, not actor bounds |
| PCG graph                                 | PCG `CreateGraph`, `AddNode`, `ConnectNodePins`, `SpawnGraphInstance`, `ExecuteGraphInstance`                                                           | node types are display names with spaces ("Create Points Grid", "Static Mesh Spawner")                                                                                                                                              |
| World Partition grid                      | OT `get_properties` on `<map>:PersistentLevel.WorldSettings.WorldPartition_1.WorldPartitionRuntimeHashSet_0`                                            | Python cannot read `runtime_partitions`                                                                                                                                                                                             |
| Nav                                       | ST `add_to_scene_from_class` a `NavMeshBoundsVolume`, scale it                                                                                          | a RecastNavMesh-Default appears; `ue_world.nav_ready` (Python) answers once the build is done                                                                                                                                       |

## 2. Signatures (catalog 5.8.3, `gen_toolset_map.py tests/arena/mcp-catalog-5.8.3 scene.SceneTools actor.ActorTools object.ObjectTools primitive PCGToolset programmatic`)

```
ST  add_to_scene_from_class(actor_type: Ref<Class>, name: str, parent?: Ref<Actor>, snap_to_ground?: bool, xform: {ToolsetTransform}) -> Ref<Actor>
ST  add_to_scene_from_asset(asset_path: str, name: str, parent?: Ref<Actor>, snap_to_ground?: bool, xform: {ToolsetTransform}) -> Ref<Actor>
ST  find_actors(actor_type?: Ref<Class>, bounds?: {Box}, collision_channels: [enum], name: str, root?: Ref<Actor>, tag: str) -> [Ref<Actor>]
ST  get_actors_in_folder(folder_path: str, recursive?: bool) -> [Ref<Actor>]
ST  set_actor_folder(actor: Ref<Actor>, folder_path: str) -> None
ST  get_current_level() -> str
ST  load_level(level_path: str) -> None
ST  merge_actors(actors: [Ref<StaticMeshActor>], destroy_source_actors?: bool, name: str, output_path: str) -> Ref<StaticMeshActor>
ST  remove_from_scene(actor: Ref<Actor>) -> bool
ST  trace_world(end: {Vector}, start: {Vector}) -> float
AC  add_component(component_type: Ref<Class>, name: str, owner: Ref<Object>) -> Ref<ActorComponent>
AC  add_tag(actor: Ref<Actor>, tag: str) -> None
AC  get_actor_bounds(actor: Ref<Actor>) -> {Box}
AC  get_components(actor: Ref<Actor>, component_type?: Ref<Class>) -> [Ref<ActorComponent>]
AC  set_actor_transform(actor: Ref<Actor>, worldspace?: bool, xform: {ToolsetTransform}) -> bool
OT  get_properties(instance: Ref<Object>, properties: [str]) -> str
OT  set_properties(instance: Ref<Object>, values: str) -> bool
OT  list_properties(instance: Ref<Object>) -> str
PR  add_cube(actor: Ref<Actor>, dimensions?: {Vector}, local_transform?: {ToolsetTransform}, name: str) -> Ref<StaticMeshComponent>
PR  add_cylinder(actor: Ref<Actor>, height?: float, local_transform?: {ToolsetTransform}, name: str, radius?: float) -> Ref<StaticMeshComponent>
PCG CreateGraph(name: str, path?: str) -> Ref<PCGGraph>
PCG AddNode(graph: Ref<PCGGraph>, jsonParams: str, nativeNodeType: str, nodeComment: str, nodeName: str, nodeTitle: str, xPositionIdx?: int, yPositionIdx?: int) -> Ref<PCGNode>
PCG GetNodeInfo(node: Ref<PCGNode>) -> {PCGNodeInfo}
PCG ConnectNodePins(fromNode: Ref<PCGNode>, fromPinLabel: str, toNode: Ref<PCGNode>, toPinLabel: str) -> [Ref<PCGNode>]
PCG GetGraphStructure(graph: Ref<PCGGraph>) -> {PCGGraphStructure}
PCG SpawnGraphInstance(graph: Ref<PCGGraph>, jsonParams: str, name: str, transform: {ToolsetTransform}) -> {PCGGraphInstanceInfo}
PCG ExecuteGraphInstance(pCGVolume: Ref<PCGVolume>) -> [{PCGNodeExecutionMessage}]
PCG GetNodeDataView(attributeName: str, endIndex?: int, node: Ref<PCGNode>, pCGVolume: Ref<PCGVolume>, pinLabel?: str, startIndex?: int) -> str
PCG ListNativeNodes(bCommonOnly?: bool) -> [str]
PCG ListAvailableSubgraphs() -> [str]
SP  RunPCGInstantGraph(graph: Ref<PCGGraph>, params: {..}) -> [{PCGNodeExecutionMessage}]
PT  execute_tool_script(script: str) -> str
PT  get_execution_environment() -> {ProgrammaticApiExecutionEnvironmentInfo}
```

## 3. Recipes (scripts run live; `ARGS` is the one line the runner replaces)

### W1. Instanced colonnade: one actor, N instances, read back (1 call instead of 9)

Mistakes this prevents: 11 pillars where 12 were asked, one pillar left at the origin, separate
actors where one instanced component does the job. Positions are computed in the script; the host
audits the read-back with `ue_world.count_audit` and `position_audit` against
`ring_layout(12, 1000)` or `line_layout(...)`.

```python
# script: W1_instanced_ring
ARGS = {"name": "Colonnade", "n": 12, "radius": 1000.0, "z": 150.0, "scale": [0.6, 0.6, 3.0], "mesh": "/Engine/BasicShapes/Cylinder.Cylinder", "tag": "colonnade", "folder": "Build/Colonnade"}
import json, math
ST = "editor_toolset.toolsets.scene.SceneTools."
AC = "editor_toolset.toolsets.actor.ActorTools."
OT = "editor_toolset.toolsets.object.ObjectTools."

def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]

def matrix(x, y, z, sx, sy, sz):   # PerInstanceSMData wants an FMatrix: scale on the diagonal, translation in wPlane
    return {"xPlane": {"x": sx, "y": 0, "z": 0, "w": 0}, "yPlane": {"x": 0, "y": sy, "z": 0, "w": 0},
            "zPlane": {"x": 0, "y": 0, "z": sz, "w": 0}, "wPlane": {"x": x, "y": y, "z": z, "w": 1}}

def run():
    actor = call(ST + "add_to_scene_from_class", {"actor_type": {"refPath": "/Script/Engine.Actor"}, "name": ARGS["name"],
        "xform": {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0}, "scale": {"x": 1, "y": 1, "z": 1}}})
    ism = call(AC + "add_component", {"component_type": {"refPath": "/Script/Engine.InstancedStaticMeshComponent"},
                                      "name": "Pillars", "owner": actor})
    sx, sy, sz = ARGS["scale"]
    inst = []
    for i in range(ARGS["n"]):
        a = 2 * math.pi * i / ARGS["n"]
        inst.append({"transform": matrix(ARGS["radius"] * math.cos(a), ARGS["radius"] * math.sin(a), ARGS["z"], sx, sy, sz)})
    call(OT + "set_properties", {"instance": ism, "values": json.dumps({"StaticMesh": {"refPath": ARGS["mesh"]},
                                                                         "PerInstanceSMData": inst})})
    # a write that grows the array leaves its LAST new entry at identity (origin): write the same array again
    call(OT + "set_properties", {"instance": ism, "values": json.dumps({"PerInstanceSMData": inst})})
    back = json.loads(call(OT + "get_properties", {"instance": ism, "properties": ["PerInstanceSMData"]}))["PerInstanceSMData"]
    call(AC + "add_tag", {"actor": actor, "tag": ARGS["tag"]})
    call(ST + "set_actor_folder", {"actor": actor, "folder_path": ARGS["folder"]})
    pts = [[b["transform"]["wPlane"]["x"], b["transform"]["wPlane"]["y"], b["transform"]["wPlane"]["z"]] for b in back]
    return {"actor": actor, "ism": ism, "count": len(back), "positions": pts}
```

Read-back on 5.8.3: 12 instances at radius 1000. The positions are local to the component; with the
actor at the origin they are world positions. **Trap, run on 5.8.3:** every `set_properties` that
grows `PerInstanceSMData` (empty to 12, 4 to 6, 4 plus 1) stores the last new entry as identity, at
the actor origin, while the count is right: 12 pillars reported, 11 in the ring and one in the
middle. A second write of the same array (same size) fixes it; shrinking writes are exact. Hence the
double write and the position read-back, never the count alone. Other trap (single call): the
`{"PerInstanceSMData": [{"Transform": {"Translation", "Rotation", "Scale3D"}}]}` form changes
nothing (one run returned true, another an error; both left the 12 instances as they were).

### W2. Wall with a centered gate, checked (1 call instead of 7)

The host splits the wall with `ue_world.wall_with_gate(4000, 600, gate_center_cm=0)`: two 1,700 cm
segments centered at -1,150 and +1,150. The script builds them with PrimitiveTools and reads each
component's size back.

```python
# script: W2_wall_with_gate
ARGS = {"name": "WallNorth", "y": -2000.0, "height": 400.0, "thickness": 50.0, "segments": [{"center_cm": -1150.0, "length_cm": 1700.0}, {"center_cm": 1150.0, "length_cm": 1700.0}], "tag": "wall"}
import json
ST = "editor_toolset.toolsets.scene.SceneTools."
AC = "editor_toolset.toolsets.actor.ActorTools."
OT = "editor_toolset.toolsets.object.ObjectTools."

def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]

def xf(x=0.0, y=0.0, z=0.0):
    return {"location": {"x": x, "y": y, "z": z}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0}, "scale": {"x": 1, "y": 1, "z": 1}}

def run():
    actor = call(ST + "add_to_scene_from_class", {"actor_type": {"refPath": "/Script/Engine.Actor"}, "name": ARGS["name"],
                                                  "xform": xf(0, ARGS["y"], 0)})
    parts = []
    for i, seg in enumerate(ARGS["segments"]):
        c = call("editor_toolset.toolsets.primitive.PrimitiveTools.add_cube", {
            "actor": actor, "name": "Seg%d" % i,
            "dimensions": {"x": seg["length_cm"], "y": ARGS["thickness"], "z": ARGS["height"]},
            "local_transform": xf(seg["center_cm"], 0, ARGS["height"] / 2.0)})
        p = json.loads(call(OT + "get_properties", {"instance": c, "properties": ["RelativeLocation", "RelativeScale3D"]}))
        parts.append({"component": c, "location": p["RelativeLocation"], "scale": p["RelativeScale3D"]})
    call(AC + "add_tag", {"actor": actor, "tag": ARGS["tag"]})
    return {"actor": actor, "parts": parts}
```

Read-back on 5.8.3: each segment is the 100 cm engine cube scaled (17, 0.5, 4) at x = -1150 and
+1150, so length = 100 x scale.x. The host rebuilds the span (-2000 to -300, 300 to 2000) and checks
the gap: 600 cm centered on 0. Do not audit with `get_actor_bounds`: for this wall at y = -2000 it
returned y -2128 to -1872 and z -128 to 400, the 256 cm phantom box of the empty root around the
actor origin, not the 50 cm thick wall. The `name` argument sets the label; the object path stays
`Actor_N` (run on 5.8.3).

### W3. Level audit before handover (1 call instead of 6 or more)

Counts per tag, per folder, per class, and instance counts of every instanced component found: the
numbers `count_audit` compares with the brief.

```python
# script: W3_level_audit
ARGS = {"tags": ["colonnade", "wall"], "folders": ["Build"], "classes": ["/Script/Engine.StaticMeshActor", "/Script/Engine.PointLight"], "instanced_actors": ["Colonnade"]}
import json
ST = "editor_toolset.toolsets.scene.SceneTools."
AC = "editor_toolset.toolsets.actor.ActorTools."
OT = "editor_toolset.toolsets.object.ObjectTools."

def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]

def find(**kw):
    a = {"name": "", "tag": "", "collision_channels": []}
    a.update(kw)
    return call(ST + "find_actors", a)

def run():
    out = {"tags": {t: len(find(tag=t)) for t in ARGS["tags"]},
           "folders": {f: len(call(ST + "get_actors_in_folder", {"folder_path": f, "recursive": True})) for f in ARGS["folders"]},
           "classes": {c.split(".")[-1]: len(find(actor_type={"refPath": c})) for c in ARGS["classes"]}, "instances": {}}
    for label in ARGS["instanced_actors"]:
        for actor in find(name=label):
            for comp in call(AC + "get_components", {"actor": actor, "component_type": {"refPath": "/Script/Engine.InstancedStaticMeshComponent"}}):
                data = json.loads(call(OT + "get_properties", {"instance": comp, "properties": ["PerInstanceSMData"]}))["PerInstanceSMData"]
                out["instances"][comp["refPath"].split(".")[-1]] = len(data)
    return out
```

On 5.8.3 after W1 and W2: tags colonnade 1, wall 1; folder Build 1; Pillars 12.

### W4. PCG grid built, spawned and executed (1 call instead of 9; read the result next call)

Epic's in-editor PCG skills also ask for scripted graph building. Native node names carry spaces;
`GetNativeNodeSchema("CreatePointsGrid")` fails. Adding a Static Mesh Spawner with mesh entries in
`jsonParams` fails ("Failed to set graph params. Node not added."): add it with `"{}"` and set the
selector object that `GetNodeInfo` names.

```python
# script: W4_pcg_grid
ARGS = {"path": "/Game/WB/PCG", "name": "PCG_Grid", "extent": 1000.0, "cell": 500.0, "mesh": "/Engine/BasicShapes/Cube.Cube", "at": [0.0, -6000.0, 0.0], "volume_scale": [20.0, 20.0, 2.0]}
import json
PCG = "PCGToolset.PCGToolset."

def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]

def node(graph, kind, name, x, params):
    return call(PCG + "AddNode", {"graph": graph, "nativeNodeType": kind, "nodeName": name, "nodeTitle": name,
                                  "nodeComment": "", "xPositionIdx": x, "yPositionIdx": 0, "jsonParams": json.dumps(params)})

def run():
    g = call(PCG + "CreateGraph", {"name": ARGS["name"], "path": ARGS["path"]})
    e, c = ARGS["extent"], ARGS["cell"]
    grid = node(g, "Create Points Grid", "Grid", 0, {"gridExtents": {"x": e, "y": e, "z": 0}, "cellSize": {"x": c, "y": c, "z": 100},
                                                     "coordinateSpace": "LocalComponent", "bCullPointsOutsideVolume": False,
                                                     "pointPosition": "CellCenter"})
    sp = node(g, "Static Mesh Spawner", "Spawner", 1, {})
    sel = call(PCG + "GetNodeInfo", {"node": sp})["paramOverrides"]["meshSelectorParameters"]
    call("editor_toolset.toolsets.object.ObjectTools.set_properties", {"instance": sel, "values": json.dumps(
        {"meshEntries": [{"weight": 1, "descriptor": {"staticMesh": {"refPath": ARGS["mesh"]}}}]})})
    call(PCG + "ConnectNodePins", {"fromNode": grid, "fromPinLabel": "Out", "toNode": sp, "toPinLabel": "In"})
    out = [n for n in call(PCG + "GetGraphStructure", {"graph": g})["nodes"] if n["name"] == "DefaultOutputNode"][0]
    call(PCG + "ConnectNodePins", {"fromNode": sp, "fromPinLabel": "Out", "toNode": {"refPath": out["path"]}, "toPinLabel": "Out"})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [ARGS["path"] + "/" + ARGS["name"]]})
    x, y, z = ARGS["at"]
    sx, sy, sz = ARGS["volume_scale"]
    inst = call(PCG + "SpawnGraphInstance", {"graph": g, "jsonParams": "{}", "name": ARGS["name"] + "_Volume", "transform": {
        "location": {"x": x, "y": y, "z": z}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0}, "scale": {"x": sx, "y": sy, "z": sz}}})
    msgs = call(PCG + "ExecuteGraphInstance", {"pCGVolume": inst["actor"]})
    edges = call(PCG + "GetGraphStructure", {"graph": g})["edges"]
    return {"graph": g, "volume": inst["actor"], "edges": len(edges), "messages": msgs}
```

The script also wires the Spawner's `Out` to the graph's own `DefaultOutputNode` (pin `Out`; its ref
comes from `GetGraphStructure`): the spawner generates without it, but the graph then has no output
(2 edges, 16 instances unchanged, run on 5.8.3). Next call: W3 with
`"instanced_actors": ["PCG_Grid_Volume"]` (or `get_components` on the volume): 16 instances of the
cube on an `ISM_Cube_0` component, at ±250 and ±750 cm around the volume center: LocalComponent
space ignored the volume scale of 20 (run on 5.8.3, offscreen). `GetNodeDataView` on the grid's
`Out` pin answered "was executed but produced no data" even after generation. The volume's trigger
read GENERATE_ON_LOAD.

### Single calls kept single

```
AC add_component {"component_type": {"refPath": "/Script/Engine.InstancedStaticMeshComponent"}, "name": "Pillars", "owner": <actor>}
OT set_properties {"instance": <ism>, "values": "{\"PerInstanceSMData\": [{\"Transform\": {...}}]}"}  -> no change (true or an error)
PCG GetNativeNodeSchema {"nodeName": "CreatePointsGrid"}                                            -> error: use "Create Points Grid"
PCG ListAvailableSubgraphs {}                                                                        -> [] without the PCGPrimitives plugin
OT get_properties {"instance": {"refPath": "<map>:PersistentLevel.WorldSettings.WorldPartition_1.WorldPartitionRuntimeHashSet_0"}, "properties": ["runtimePartitions"]}
```

The last one, on a map made from the Open World template: MainGrid of class RuntimePartitionLHGrid;
its `cellSize` read 25,200 cm and `loadingRange` 76,800 cm.

Whole recipe set on 5.8.3: 36 calls in 78 s over two editor sessions (`live_mcp_recipes.py`, the
second with PCGPrimitives), the four scripts included. `find_actors {"name": "Fence"}` returned the
actor labeled FencePosts (substring). After a NavMeshBoundsVolume, `nav_ready` said off the navmesh
in the same call and on it (z 10 over a floor top at 0) a few calls later; a RecastNavMesh actor
appeared on its own.

## 4. Epic's in-editor PCG skills, checked (run on 5.8.3)

Epic ships PCG skills (graph generation, instancing on a mesh actor, biome refinement and others)
and an instant-operations skill, read through `ToolsetRegistry.AgentSkillToolset`. Where they meet
this skill:

- **Scripted graph building:** they also prefer one `execute_tool_script` for a whole graph. Agreed;
  W4 is that script.
- **Primitive subgraphs and instant graphs need the PCGPrimitives plugin** (Experimental, in the
  engine's Plugins folder, off in a blank project). Without it `ListAvailableSubgraphs` returned
  `[]` and `/PCGPrimitives/Instants/` does not exist; with it enabled in the .uproject the editor
  booted in about 25 s, listed the subgraphs (Write, Trace, Subdivide, Fill and more) and 13 instant
  graphs (Create, Place, Transform, Spawn). Enabling it is a project change: ask before you add it
  to someone's project. Native nodes (W4) need no plugin.
- **Instant graphs report through messages.**
  `SP RunPCGInstantGraph {"graph": {"refPath": "/PCGPrimitives/Instants/Create/Instant_Create_Spline_Line.Instant_Create_Spline_Line"}, "params": {}}`
  with nothing selected returned ok, two Error messages ("No Actor Selected", invalid target actor),
  and still left a SplineActor in the level. Read the messages and list the level after each instant
  call; read a graph's inputs with `GetGraphStructure` first, as Epic's skill also says.
- **"Execute, do not chase warnings":** fine for an agent's own graph. For production graphs this
  skill keeps Warn on Data Missing Attribute on (stance in SKILL.md), so bad data shows; the two do
  not conflict.
- **Asset references:** their instancing skill loads assets before referencing them. The recipes
  here passed `/Engine/BasicShapes/...` refPaths without a load step and they resolved; a project
  asset not yet loaded is [not yet run].

## 5. When to use Python or a commandlet instead

- Creating and saving levels (no MCP tool makes a clean one), open-world maps
  (`new_open_world_map`), Data Layers and HLOD layer assets (`create_data_layer_asset`,
  `create_hlod_layer`, `assign_data_layer`, `set_streaming`: run on 5.8.3).
- Instancing from code you already run in Python: `add_instanced_mesh`, `instance_positions`,
  `level_counts` (run on 5.8.3 by the runner).
- Navigation readiness: `nav_ready` (`project_point_to_navigation` returns None while the build
  runs; there is no build call: `RebuildNavigation` console command).
- Commandlets for batch work over many maps; nothing renders under `-nullrhi`.
