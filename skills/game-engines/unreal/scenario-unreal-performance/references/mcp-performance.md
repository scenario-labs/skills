# Performance through Epic's Unreal MCP toolsets

Read this before calling a toolset for performance work: it gives the argument shapes, so
`describe_toolset` is not needed. Everything marked "run on 5.8.3" was executed through `ue_mcp.Mcp`
against an editor started with `ue_run.launch_editor(..., mcp_port=N)` on a level built to be slow
(`tests/code/unreal-performance/live/job_build_heavy_scene.py`: 1,600 movable cubes, 60 movable
261k-triangle spheres with one LOD, 48 shadowed point lights with a 30 m radius, a 4096 px
uncompressed texture with no mips that never streams). The recipes are a runnable test:
`python3 tests/code/unreal-performance/live_mcp_recipes.py` (copies the base project, builds the
level, starts and stops its own headless editor on a new port, runs every script block of this file
as written, exit 0 only if all pass; `--measure` adds a before and after CSV capture and checks the
gains).

**Batch.** Four or more toolset calls in a row go through one
`ProgrammaticToolset.execute_tool_script`: define `run()`, call
`execute_tool("<toolset>.<tool>", json_string)["returnValue"]`, return a dict. Imports are limited
to `json`, `math`, `re`, `time`, `datetime`, `copy`; there is no `unreal` module. One failing call
ends the script, so keep calls that are expected to fail outside it. Recipe R4 set 1,660 component
properties and saved the level in one call (about 15 s); R6 merged 1,600 actors in 1 s.

## What MCP does and does not do for performance

| Task                                                             | Channel                                                                                                     | Why                                                                                                                              |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Read a cvar value, check a cvar name exists                      | MCP `EditorAppToolset.SearchCVars` (R1)                                                                     | substring search over console variables; commands such as `ProfileGPU`, `snapshothitches`, `fx.Niagara.Debug.Hud` are not listed |
| Change a project setting (ini)                                   | MCP `ConfigSettingsToolset` (R2)                                                                            | writes `Config/Default*.ini` at once                                                                                             |
| Audit and fix content: mobility, lights, merge, LODs, textures   | MCP scripts R3 to R8                                                                                        | `SceneTools`, `ObjectTools`, `StaticMeshTools`, `TextureTools`, `AssetTools`                                                     |
| Run an automation test                                           | MCP `AutomationTestToolset` (R9)                                                                            | `RunTests` blocks until the tests end and returns the results                                                                    |
| Run a console command (`stat`, `ProfileGPU`, `r.X 1` at runtime) | not MCP: no console tool in the 5.8.3 catalog                                                               | use `-ExecCmds` and `-DPCVars` on a capture run, or Python `unreal.SystemLibrary.execute_console_command`                        |
| Measure frame time, thread times, GPU passes                     | not MCP: a separate `-game` run with the CSV profiler                                                       | `ue_perf.capture_plan(..., csv_frames=500)`; see "Measure" below                                                                 |
| Read a trace                                                     | not MCP: Unreal Insights command line                                                                       | `ue_perf.insights_export` then `load_insights_events`                                                                            |
| Whole-project audit with estimates and change requests           | Python in a commandlet: `ue_perf.perf_audit_level`, `perf_audit_assets`, `texture_facts`, `change_requests` | one job, no editor needed                                                                                                        |

## Signatures (catalog 5.8.3)

Generated with `gen_toolset_map.py tests/arena/mcp-catalog-5.8.3`; only the tools used here.

```
EditorToolset.EditorAppToolset
SearchCVars(name: str) -> str                      # JSON text {cvar: {"help", "value"}}
EditorToolset.LogsToolset
GetLogEntries(category?: str, maxEntries?: int, pattern: str) -> [str]
ConfigSettingsToolset.ConfigSettingsToolset
ListContainers() -> [str]
ListCategories(containerName: str) -> [str]
ListSections(categoryName: str, containerName: str) -> [str]
GetSectionSchema(categoryName: str, containerName: str, sectionName: str) -> str
GetSectionPropertyValues(categoryName: str, containerName: str, propertyNames: [str], sectionName: str) -> str
SetSectionProperties(categoryName: str, containerName: str, propertiesJson: str, sectionName: str) -> bool
AutomationTestToolset.AutomationTestToolset
DiscoverTests(bForceRediscover?: bool) -> str
ListTests(limit?: int, nameFilter: str, tagFilter: str) -> str
RunTests(testNames: [str]) -> str
RunTestsByFilter(filterExpression: str) -> str
GetTestStatus() -> str
GetTestResults() -> str
editor_toolset.toolsets.scene.SceneTools
find_actors(actor_type?: Ref<Class>, bounds?: {Box}, collision_channels: [enum], name: str, root?: Ref<Actor>, tag: str) -> [Ref<Actor>]
merge_actors(actors: [Ref<StaticMeshActor>], destroy_source_actors?: bool, name: str, output_path: str) -> Ref<StaticMeshActor>
editor_toolset.toolsets.object.ObjectTools
get_properties(instance: Ref<Object>, properties: [str]) -> str
set_properties(instance: Ref<Object>, values: str) -> bool
editor_toolset.toolsets.static_mesh.StaticMeshTools
generate_lods(mesh: Ref<StaticMesh>, triangle_percents: [float]) -> int
get_lod_count(mesh) -> int
get_lod_thresholds(mesh) -> [float]
set_lod_thresholds(mesh, thresholds: [float]) -> bool
get_triangle_count(lod_index?: int, mesh) -> int
is_nanite_enabled(mesh) -> bool
set_nanite_enabled(enabled: bool, mesh) -> None
generate_convex_collisions(hull_count?: int, hull_precision?: int, max_hull_verts?: int, mesh) -> bool
editor_toolset.toolsets.texture.TextureTools
get_size(texture: Ref<Texture2D>) -> {IntPoint}
editor_toolset.toolsets.asset.AssetTools
find_assets(asset_type?: Ref<Class>, folder_path: str, name: str, recursive?: bool, tags?: {..}) -> [str]
save_assets(asset_paths: [str]) -> bool
editor_toolset.toolsets.programmatic.ProgrammaticToolset
execute_tool_script(script: str) -> str
```

## Single calls (run on 5.8.3)

```json
{"toolset_name": "EditorToolset.EditorAppToolset", "tool_name": "SearchCVars", "arguments": {"name": "r.Shadow.Virtual.Stats"}}
{"toolset_name": "EditorToolset.LogsToolset", "tool_name": "GetLogEntries", "arguments": {"category": "", "pattern": "Hitch detected|LogStreaming", "maxEntries": 20}}
{"toolset_name": "editor_toolset.toolsets.object.ObjectTools", "tool_name": "get_properties", "arguments": {"instance": {"refPath": "/Game/Perf/L_Heavy.L_Heavy:PersistentLevel.PointLight_0.LightComponent0"}, "properties": ["CastShadows", "AttenuationRadius", "Mobility"]}}
{"toolset_name": "editor_toolset.toolsets.object.ObjectTools", "tool_name": "set_properties", "arguments": {"instance": {"refPath": "/Game/Perf/Tex/T_Noise4k.T_Noise4k"}, "values": "{\"CompressionSettings\": \"TC_Default\", \"MaxTextureSize\": 2048}"}}
{"toolset_name": "editor_toolset.toolsets.static_mesh.StaticMeshTools", "tool_name": "get_triangle_count", "arguments": {"mesh": {"refPath": "/Game/Perf/Mesh/SM_Dense.SM_Dense"}, "lod_index": 0}}
```

`SearchCVars` returns a JSON string: parse it, then match the name exactly (the search is a
substring match). `GetLogEntries` takes a regular expression and returns the last `maxEntries`
matching lines; pass `"category": ""` for all categories (the default is the category `LogsToolset`,
which does not exist, and the call fails). `get_properties` returns a JSON string of PascalCase
names (`Mobility`, `CastShadows`, `CompressionSettings`); `set_properties` takes the same names in a
JSON string.

## Recipes (each one execute_tool_script call, run on 5.8.3)

Paths are the test level's; change `LEVEL`, tags and folders for your project. Fix scripts save what
they changed; take the before capture first.

```python
# execute_tool_script: R1 check cvar names and read their values (one SearchCVars per name)
import json
NAMES = ["r.ShaderPrint", "r.ShaderPrintEnable", "r.Shadow.Virtual.Stats.Visible",
         "r.Shadow.Virtual.ShowStats", "r.Nanite.ShowMeshDrawEvents", "r.GPUCsvStatsEnabled",
         "r.DynamicGlobalIlluminationMethod", "r.ReflectionMethod", "t.HitchFrameTimeThreshold"]
def run():
    out = {}
    for n in NAMES:
        found = json.loads(execute_tool("EditorToolset.EditorAppToolset.SearchCVars",
                                        json.dumps({"name": n}))["returnValue"])
        exact = [k for k in found if k.lower() == n.lower()]
        out[n] = found[exact[0]]["value"] if exact else None
    return out
```

Result on a Blank-template project: `r.ShaderPrint` 0, `r.ShaderPrintEnable` None (renamed),
`r.Shadow.Virtual.Stats.Visible` false, `r.Shadow.Virtual.ShowStats` None (deprecated: typing it
fires an ensure), `r.Nanite.ShowMeshDrawEvents` None (gone in 5.8.3), `r.GPUCsvStatsEnabled` 0, GI
method 0, reflection method 2, hitch threshold 60. A None is a name to fix before it goes into a
capture command.

```python
# execute_tool_script: R2 read, set and read back a project setting (default collision complexity)
import json
CS = "ConfigSettingsToolset.ConfigSettingsToolset."
SEC = {"containerName": "Project", "categoryName": "Engine", "sectionName": "Physics"}
def get():
    a = dict(SEC, propertyNames=["defaultShapeComplexity"])
    return json.loads(execute_tool(CS + "GetSectionPropertyValues", json.dumps(a))["returnValue"])
def run():
    before = get()
    a = dict(SEC, propertiesJson=json.dumps({"defaultShapeComplexity": "CTF_UseSimpleAsComplex"}))
    ok = execute_tool(CS + "SetSectionProperties", json.dumps(a))["returnValue"]
    return {"before": before, "set": ok, "after": get()}
```

Result: `CTF_UseSimpleAndComplex` (engine default) to `CTF_UseSimpleAsComplex`;
`DefaultShapeComplexity=CTF_UseSimpleAsComplex` is in `Config/DefaultEngine.ini` at once, no
`SaveSection` needed. It applies to meshes created after the change; existing meshes keep their own
setting.

```python
# execute_tool_script: R3 performance audit of the loaded level and its heavy assets (read only)
import json
ST = "editor_toolset.toolsets.scene.SceneTools."
OT = "editor_toolset.toolsets.object.ObjectTools."
SM = "editor_toolset.toolsets.static_mesh.StaticMeshTools."
TT = "editor_toolset.toolsets.texture.TextureTools."
def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]
def actors(cls):
    return call(ST + "find_actors", {"actor_type": {"refPath": cls}, "name": "", "tag": "",
                                     "collision_channels": []})
def props(ref, names):
    return json.loads(call(OT + "get_properties", {"instance": {"refPath": ref}, "properties": names}))
def run():
    out = {"static_mesh_actors": 0, "non_static_mesh": 0, "meshes": {}, "lights": 0,
           "shadowed_lights": 0, "big_radius_lights": 0, "textures": {}}
    for a in actors("/Script/Engine.StaticMeshActor"):
        out["static_mesh_actors"] += 1
        p = props(a["refPath"] + ".StaticMeshComponent0", ["Mobility", "StaticMesh"])
        if p["Mobility"] != "Static":
            out["non_static_mesh"] += 1
        mesh = (p.get("StaticMesh") or {}).get("refPath")
        if mesh and mesh not in out["meshes"]:
            out["meshes"][mesh] = {
                "lods": call(SM + "get_lod_count", {"mesh": {"refPath": mesh}}),
                "lod0_triangles": call(SM + "get_triangle_count", {"mesh": {"refPath": mesh}, "lod_index": 0}),
                "nanite": call(SM + "is_nanite_enabled", {"mesh": {"refPath": mesh}})}
    for a in actors("/Script/Engine.PointLight"):
        p = props(a["refPath"] + ".LightComponent0", ["CastShadows", "AttenuationRadius"])
        out["lights"] += 1
        out["shadowed_lights"] += 1 if p["CastShadows"] else 0
        out["big_radius_lights"] += 1 if p["AttenuationRadius"] > 1000 else 0
    for t in ["/Game/Perf/Tex/T_Noise4k.T_Noise4k"]:
        size = call(TT + "get_size", {"texture": {"refPath": t}})
        out["textures"][t] = dict(props(t, ["CompressionSettings", "MipGenSettings", "NeverStream",
                                            "MaxTextureSize", "LODGroup"]), size=size)
    return out
```

Result: 1,660 static mesh actors, all 1,660 not Static; SM_Dense 1 LOD, 261,120 triangles, Nanite
off; 48 lights, 48 shadowed, 48 over 10 m; the texture 4096 x 4096, `TC_EditorIcon`,
`TMGS_NoMipmaps`, never streamed. About 15 s for 1,700 calls in one round trip. Component names:
`StaticMeshComponent0` on a StaticMeshActor, `LightComponent0` on a PointLight.

```python
# execute_tool_script: R4 set Mobility Static on static mesh actors nothing moves, then save the level
import json
LEVEL = "/Game/Perf/L_Heavy"
TAGS = ["PerfCube", "PerfDense"]  # actors you checked are never moved by Sequencer or Blueprint
def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]
def run():
    n, failed = 0, []
    for tag in TAGS:
        for a in call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                      {"name": "", "tag": tag, "collision_channels": []}):
            comp = a["refPath"] + ".StaticMeshComponent0"
            ok = call("editor_toolset.toolsets.object.ObjectTools.set_properties",
                      {"instance": {"refPath": comp}, "values": json.dumps({"Mobility": "Static"})})
            n += 1
            if not ok:
                failed.append(comp)
    saved = call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [LEVEL]})
    return {"set_static": n, "failed": failed[:5], "saved": saved}
```

Result: 1,660 set, 0 failed, level saved. This one change took the measured frame from 42 to 13 ms
(see "Measure"): static primitives under movable shadowed point lights use cached shadow maps.

```python
# execute_tool_script: R5 tighten point light radii and keep shadows on one light in eight
import json
LEVEL = "/Game/Perf/L_Heavy"
def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]
def run():
    lights = call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                  {"actor_type": {"refPath": "/Script/Engine.PointLight"}, "name": "", "tag": "",
                   "collision_channels": []})
    for i, a in enumerate(lights):
        call("editor_toolset.toolsets.object.ObjectTools.set_properties",
             {"instance": {"refPath": a["refPath"] + ".LightComponent0"},
              "values": json.dumps({"AttenuationRadius": 1200, "CastShadows": i % 8 == 0})})
    saved = call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [LEVEL]})
    return {"lights": len(lights), "shadowed": len(lights[::8]), "saved": saved}
```

Result: 48 lights, 6 shadowed, saved. Which lights keep shadows is the lighting owner's call (a
change request, then this script).

```python
# execute_tool_script: R6 merge many small static mesh actors into one, read back, save
import json
LEVEL = "/Game/Perf/L_Heavy"
def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]
def run():
    cubes = call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                 {"name": "", "tag": "PerfCube", "collision_channels": []})
    merged = call("editor_toolset.toolsets.scene.SceneTools.merge_actors",
                  {"actors": cubes, "destroy_source_actors": True, "name": "CubesMerged",
                   "output_path": "/Game/Perf/CubesMerged"})
    p = json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                        {"instance": {"refPath": merged["refPath"] + ".StaticMeshComponent0"},
                         "properties": ["StaticMesh", "Mobility"]}))
    mesh = p["StaticMesh"]["refPath"]
    tris = call("editor_toolset.toolsets.static_mesh.StaticMeshTools.get_triangle_count",
                {"mesh": {"refPath": mesh}, "lod_index": 0})
    left = call("editor_toolset.toolsets.scene.SceneTools.find_actors",
                {"name": "", "tag": "PerfCube", "collision_channels": []})
    saved = call("editor_toolset.toolsets.asset.AssetTools.save_assets",
                 {"asset_paths": [LEVEL, mesh.split(".")[0]]})
    return {"merged_from": len(cubes), "actor": merged["refPath"], "mesh": mesh,
            "mobility": p["Mobility"], "triangles": tris, "tagged_left": len(left), "saved": saved}
```

Result: 1,600 actors merged in about 1 s into one Static actor with a 76,800-triangle mesh and one
LOD; `name` is ignored, the mesh is `/Game/Perf/SM_CubesMerged` (the last part of `output_path` with
an `SM_` prefix, in its parent folder). The source actors are gone and their tags too. Merging
trades culling for draw calls: one mesh is drawn whole when any part is visible, so merge what is
seen together (or use instances; world-building owns that choice).

```python
# execute_tool_script: R7 generate LODs on a dense mesh, set explicit screen sizes, read back
import json
MESH = {"refPath": "/Game/Perf/Mesh/SM_Dense.SM_Dense"}
SM = "editor_toolset.toolsets.static_mesh.StaticMeshTools."
def call(tool, args):
    return execute_tool(SM + tool, json.dumps(args))["returnValue"]
def run():
    lods = call("generate_lods", {"mesh": MESH, "triangle_percents": [0.5, 0.25, 0.1]})
    auto = call("get_lod_thresholds", {"mesh": MESH})
    call("set_lod_thresholds", {"mesh": MESH, "thresholds": [1.0, 0.5, 0.25, 0.1]})
    tris = [call("get_triangle_count", {"mesh": MESH, "lod_index": i}) for i in range(lods)]
    saved = execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets",
                         json.dumps({"asset_paths": ["/Game/Perf/Mesh/SM_Dense"]}))["returnValue"]
    return {"lods": lods, "auto_thresholds": auto, "thresholds": call("get_lod_thresholds", {"mesh": MESH}),
            "triangles": tris, "saved": saved}
```

Result: 4 LODs (261,120, 130,560, 65,280, 26,112 triangles: the percents are of LOD0); thresholds
read back as 0 right after `generate_lods` (another run gave 2, 1.78, 1.77, 1.76: nearly equal
screen sizes), so always set them. For a mesh that should be Nanite, `set_nanite_enabled` is the
other answer; LODs are for non-Nanite meshes, skeletal meshes and platforms without Nanite.

```python
# execute_tool_script: R8 audit every texture in a folder and fix the four costly settings
import json
ROOT = "/Game/Perf"
MAX = 2048
FIX = {"CompressionSettings": "TC_Default", "MipGenSettings": "TMGS_FromTextureGroup",
       "NeverStream": False, "MaxTextureSize": MAX}
def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]
def facts(t):
    p = json.loads(call("editor_toolset.toolsets.object.ObjectTools.get_properties",
                        {"instance": {"refPath": t}, "properties": list(FIX) + ["LODGroup"]}))
    p["size"] = call("editor_toolset.toolsets.texture.TextureTools.get_size", {"texture": {"refPath": t}})
    return p
def findings(p):
    f = []
    if max(p["size"]["x"], p["size"]["y"]) > MAX and not p["MaxTextureSize"]:
        f.append("oversized")
    if p["CompressionSettings"] in ("TC_EditorIcon", "TC_HDR", "TC_VectorDisplacementmap", "TC_HDR_F32"):
        f.append("uncompressed")
    if p["MipGenSettings"] == "TMGS_NoMipmaps":
        f.append("no_mips")
    if p["NeverStream"]:
        f.append("never_streamed")
    return f
def run():
    found = call("editor_toolset.toolsets.asset.AssetTools.find_assets",
                 {"asset_type": {"refPath": "/Script/Engine.Texture2D"},
                  "folder_path": ROOT, "name": "", "recursive": True})
    out = {}
    for pkg in found:  # package paths: /Game/F/T_X; the object path adds .T_X
        t = pkg + "." + pkg.rsplit("/", 1)[1]
        before = facts(t)
        f = findings(before)
        if f and before.get("LODGroup") != "TEXTUREGROUP_UI":
            call("editor_toolset.toolsets.object.ObjectTools.set_properties",
                 {"instance": {"refPath": t}, "values": json.dumps(FIX)})
            call("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [pkg]})
        out[t] = {"findings": f, "after": findings(facts(t))}
    return out
```

Result: the 4K texture had all four findings and none after; non-streaming texture memory in the
next capture fell from 105.7 to 41.7 MB. `TextureTools.get_size` reads the source size:
`MaxTextureSize` does not change it, so judge the fix by the setting or by the capture. A blanket
`TC_Default` is wrong for normal maps, masks and HDR: in a real project choose the setting per
texture (the materials owner decides), this script is the shape of the batch.

```python
# execute_tool_script: R9 discover, list and run an automation test, then read its result
import json
AT = "AutomationTestToolset.AutomationTestToolset."
def call(tool, args):
    return json.loads(execute_tool(AT + tool, json.dumps(args))["returnValue"])
def run():
    call("DiscoverTests", {})
    names = call("ListTests", {"nameFilter": "System.Core.Time.FrameRate", "tagFilter": "",
                               "limit": 5})["tests"]
    res = call("RunTests", {"testNames": names[:1]})  # blocks until the tests finish
    return {"tests": names[:1], "passed": res["passed"], "failed": res["failed"],
            "states": [t["state"] for t in res["tests"]], "status": call("GetTestStatus", {})}
```

Result: 1 passed, state `Success`, about 8 ms. Every return value of this toolset is JSON text. In a
headless (`-nullrhi`) editor a test that creates a world (for example `Input.Modifiers.Performance`)
ran and then crashed the editor while the call was still blocking: run world tests (functional and
performance tests) in an offscreen editor or from the command line
(`-ExecCmds="Automation RunTests <name>"`), and keep the client timeout above the test length.

## Measure (outside MCP)

The proof is a capture, and captures are separate processes:

```python
import ue_perf as P, ue_run
plan = P.capture_plan("budget", platform="mac", build="Development", csv_frames=500,
                      trace=False)  # CSV only; GPU/<pass> columns are switched on for budget runs
h = ue_run.launch_editor("/abs/Game.uproject", map="/Game/Perf/L_Heavy", mode="offscreen",
                         log_path="/abs/game.log", extra=["-game", "-windowed", "-ResX=1280", "-ResY=720"] + plan["args"])
h["process"].wait()
csv = P.csv_path_from_log(open("/abs/game.log").read(), "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac")
P.csv_step_table([("before", "/abs/before.csv"), ("after", csv)], tail=250)
```

Measured on 5.8.3 (Mac, editor binary with `-game`, offscreen 1280 x 720, VSync off, median of the
last 250 of 500 frames; the machine was shared and loaded, so read the ratios and counters, not the
third digit):

| Step                    | Frame | Game | Render | GPU  | GPU ShadowDepths | Instances | Non-streaming tex MB |
| ----------------------- | ----- | ---- | ------ | ---- | ---------------- | --------- | -------------------- |
| before                  | 42.1  | 2.5  | 42.1   | 40.7 | 32.0             | 1,665     | 105.7                |
| R4 mobility Static      | 13.2  | 1.4  | 13.4   | 12.5 | 3.0              | 1,665     | 105.7                |
| R5 lights               | 10.8  | 1.4  | 10.8   | 10.4 | 3.9              | 1,665     | 105.7                |
| R6 merge                | 9.1   | 1.6  | 8.8    | 9.5  | 3.8              | 66        | 105.7                |
| R7 LODs and R8 textures | 8.3   | 1.4  | 8.3    | 5.4  | 0.4              | 66        | 41.7                 |

The before frame was classified "render" by `diagnose_bound`, but 26 ms of the 42 ms render thread
was `EventWait/Shadows` and GPU ShadowDepths took 32 ms: `P.csv_breakdown(csv)` lists the
`Exclusive/RenderThread/*` and `GPU/*` columns that say which.

## Traps (run on 5.8.3)

- `SearchCVars` lists variables only; console commands (`ProfileGPU`, `snapshothitches`,
  `NaniteStats`, `fx.Niagara.Debug.Hud`, `r.RHISetGPUCaptureOptions`) never appear, and plugin cvars
  (`a.Budget.*`) appear only with the plugin enabled.
- `GetLogEntries` without `"category": ""` fails ("Log category 'LogsToolset' not found").
- `merge_actors` ignores `name`; the asset is `SM_` plus the last part of `output_path`.
- `generate_lods` leaves screen sizes at 0 or nearly equal: set them.
- `find_assets` returns package paths; tools that take an object want `/Game/F/T_X.T_X`.
- `RunTests` blocks; a world-creating test in a `-nullrhi` editor crashed it.
- RHI/DrawCalls, RHI/PrimitivesDrawn and DrawCall/* CSV columns read 0 on Metal; count with
  `GPUSceneInstanceCount`. `GPU/<pass>` columns need `r.GPUCsvStatsEnabled=1`.
- With the launcher editor binary and `-game`, CSV files and hitch snapshots land under the engine's
  per-user `Saved/Profiling` on a Mac, not the project's; the log names the CSV.

## Epic's in-editor skills

Read through `ToolsetRegistry.AgentSkillToolset`. For Niagara cost, read Epic's in-editor
NiagaraOptimization skill first: it covers the authoring levers (sim target, emitter consolidation,
bounds, Effect Types, pooling, burst spawning). This skill keeps the measurement
(`stat NiagaraOverview`, per-system cost in Insights without named events) and the budgets. No other
engine skill in 5.8.3 covers frame budgets, captures or proof.
