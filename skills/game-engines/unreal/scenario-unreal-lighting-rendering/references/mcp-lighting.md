# Lighting through Epic's Unreal MCP (5.8.3)

Everything here ran on 5.8.3 (2026-10-21) unless a line says otherwise; signature lines come from
the 5.8.3 catalog. Runner: `tests/code/unreal-lighting-rendering/live_mcp_recipes.py` reads the
`# script:` blocks below from this file, runs each one through `execute_tool_script` in its own
offscreen editor, and exits 0 only if every recipe passes.

**Batch first.** Four or more toolset calls in a row go in one
`ProgrammaticToolset.execute_tool_script` call: the script defines `run()`, calls
`execute_tool("<toolset>.<tool>", json_string)`, returns a dict, and may import only json, math, re,
time, datetime and copy (no `unreal`). Read `get_execution_environment` once per session. A failing
tool inside the script aborts the whole script, and `try/except` around `execute_tool` did not catch
it on 5.8.3; actors created before the failure stay in the level. So keep calls that are expected to
fail (probes, traps) as single `call_tool` calls, and read the scene back before re-running a script
that failed halfway.

Short names: ST `editor_toolset.toolsets.scene.SceneTools`, AC `...actor.ActorTools`, OT
`...object.ObjectTools`, TT `...texture.TextureTools`, EA `EditorToolset.EditorAppToolset`, PT
`editor_toolset.toolsets.programmatic.ProgrammaticToolset`.

## 1. Intent to tool

| Intent                       | Tool                                                                                         | Notes (run on 5.8.3)                                                                                                                                               |
| ---------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| New level                    | Python `LevelEditorSubsystem.new_level` + `save_current_level`                               | `AssetTools.duplicate` of a map gives a dirty map: `save_assets` returns false and `load_level` refuses it                                                         |
| Place a light, sky, fog, PPV | ST `add_to_scene_from_class`                                                                 | `{"actor_type": {"refPath": "/Script/Engine.DirectionalLight"}, "name", "xform"}`; Blueprint classes work (`/HDRIBackdrop/Blueprints/HDRIBackdrop.HDRIBackdrop_C`) |
| Light settings               | AC `get_components`, then OT `set_properties` on the COMPONENT                               | on the actor: "the following properties could not be set: Intensity"                                                                                               |
| Sun direction                | AC `set_actor_transform`                                                                     | pitch 0 horizon, -90 overhead; pitch -5 is a 5 degree sunset                                                                                                       |
| Light color                  | OT `set_properties {"LightColor": {"r","g","b","a"}}`                                        | FColor: floats 0..1 are stored as bytes (0.2 reads 0.2000, i.e. 51/255, no linear conversion); 0-255 integers return true and saturate to 1                        |
| Exposure                     | OT `set_properties` on the PPV `{"bUnbound": true, "Settings": {...}}`                       | partial nested JSON merges; each value needs its `bOverride_*`; dotted `Settings.X` paths fail                                                                     |
| Read anything back           | OT `get_properties {"instance", "properties": [...]}`                                        | returns a JSON string; keys come back as requested at top level, camelCase inside structs (`autoExposureBias`), `bOverride_*` as is                                |
| Does a cvar exist            | EA `SearchCVars {"name"}`                                                                    | partial match: `r.MegaLights.Allow` returns `r.MegaLights.Allowed`; "{}" when absent; existence = exact key                                                        |
| Import an equirect sky       | TT `import_file`                                                                             | `.hdr` becomes a TextureCube; `.exr` and `.png` a long-lat Texture2D                                                                                               |
| Count lights before handover | ST `find_actors {"actor_type", "name": "", "tag": "", "collision_channels": []}`             | `name` matches label substrings                                                                                                                                    |
| Camera                       | EA `SetCameraTransform {"transform"}`, `GetCameraTransform`                                  |                                                                                                                                                                    |
| Frame to measure             | Python `AutomationLibrary.take_high_res_screenshot` with `r.BufferVisualizationDumpFrames 1` | EA `CaptureViewport` needs `annotations: {}`; offscreen it returned "Viewport has zero size." (or a 424x40 image in an earlier run): not a measuring tool          |
| Console toggles              | Python `SystemLibrary.execute_console_command`                                               | `viewmode <x>` changed nothing in a scripted screenshot; use `ShowFlag.<X> 1/2` (`ue_light.VIEW_MODES`)                                                            |

## 2. Signatures (catalog 5.8.3, `gen_toolset_map.py tests/arena/mcp-catalog-5.8.3 EditorAppToolset actor.ActorTools object.ObjectTools scene.SceneTools texture.TextureTools programmatic`)

```
EA  CaptureViewport(annotations?: {ViewportAnnotationConfig}, bShowUI?: bool, captureTransform?: {ToolsetTransform}) -> {ViewportCapture}
EA  GetCameraTransform() -> {ToolsetTransform}
EA  SetCameraTransform(transform: {ToolsetTransform}) -> None
EA  SearchCVars(name: str) -> str
EA  GetVisibleActors() -> [Ref<Actor>]
AC  get_components(actor: Ref<Actor>, component_type?: Ref<Class>) -> [Ref<ActorComponent>]
AC  get_actor_transform(actor: Ref<Actor>) -> {ToolsetTransform}
AC  set_actor_transform(actor: Ref<Actor>, worldspace?: bool, xform: {ToolsetTransform}) -> bool
AC  look_at(actor: Ref<Actor>, target: {Vector}) -> None
AC  add_tag(actor: Ref<Actor>, tag: str) -> None
OT  get_class(instance: Ref<Object>) -> Ref<Class>
OT  get_properties(instance: Ref<Object>, properties: [str]) -> str
OT  list_properties(instance: Ref<Object>) -> str
OT  set_properties(instance: Ref<Object>, values: str) -> bool
OT  reset_properties(instance: Ref<Object>, properties: [str]) -> bool
ST  add_to_scene_from_class(actor_type: Ref<Class>, name: str, parent?: Ref<Actor>, snap_to_ground?: bool, xform: {ToolsetTransform}) -> Ref<Actor>
ST  add_to_scene_from_asset(asset_path: str, name: str, parent?: Ref<Actor>, snap_to_ground?: bool, xform: {ToolsetTransform}) -> Ref<Actor>
ST  find_actors(actor_type?: Ref<Class>, bounds?: {Box}, collision_channels: [enum], name: str, root?: Ref<Actor>, tag: str) -> [Ref<Actor>]
ST  set_actor_folder(actor: Ref<Actor>, folder_path: str) -> None
ST  load_level(level_path: str) -> None
ST  get_current_level() -> str
TT  import_file(asset_name: str, folder_path: str, source_file: str) -> [Ref<Object>]
PT  execute_tool_script(script: str) -> str
PT  get_execution_environment() -> {ProgrammaticApiExecutionEnvironmentInfo}
```

`ToolsetTransform` is
`{"location": {"x","y","z"}, "rotation": {"pitch","yaw","roll"}, "scale": {"x","y","z"}}`; a
reference is `{"refPath": "..."}` exactly as a tool returned it.

## 3. Recipes (scripts run live; `ARGS` is the one line the runner replaces)

### S1. Outdoor rig with exposure from the sun (1 call instead of 16)

Run on 5.8.3: the whole runner made 19 calls for what took about 60 as single calls. Defaults read
first (run on 5.8.3): a spawned DirectionalLight is 10 lux, Stationary, Use Temperature off (6500 K
stored), Atmosphere Sun Light on; a SkyLight captures the scene (SLS_CapturedScene). The host
computes `ev100` with `ue_light.ev100_for_sun(sun_lux, elevation)` (120,000 lux at 5 degrees gives
9.69) and the script writes it as a manual exposure.

```python
# script: S1_outdoor_rig
ARGS = {"sun_lux": 120000.0, "elevation": 5.0, "yaw": 30.0, "ev100": 9.69, "temperature": 5000.0}   # temperature None: white, off
import json
ST = "editor_toolset.toolsets.scene.SceneTools."
AC = "editor_toolset.toolsets.actor.ActorTools."
OT = "editor_toolset.toolsets.object.ObjectTools."

def xf(loc=(0, 0, 0), rot=(0, 0, 0)):
    return {"location": dict(zip("xyz", loc)), "rotation": dict(zip(("pitch", "yaw", "roll"), rot)),
            "scale": {"x": 1, "y": 1, "z": 1}}

def spawn(cls, name, rot=(0, 0, 0)):
    return execute_tool(ST + "add_to_scene_from_class", json.dumps(
        {"actor_type": {"refPath": "/Script/Engine." + cls}, "name": name, "xform": xf((0, 0, 500), rot)}))["returnValue"]

def comp(actor, cls):
    return execute_tool(AC + "get_components", json.dumps(
        {"actor": actor, "component_type": {"refPath": "/Script/Engine." + cls}}))["returnValue"][0]

def setp(obj, values):
    return execute_tool(OT + "set_properties", json.dumps({"instance": obj, "values": json.dumps(values)}))["returnValue"]

def getp(obj, names):
    return json.loads(execute_tool(OT + "get_properties", json.dumps({"instance": obj, "properties": names}))["returnValue"])

def run():
    sun = spawn("DirectionalLight", "Sun", (-ARGS["elevation"], ARGS["yaw"], 0))
    spawn("SkyAtmosphere", "SkyAtmosphere")
    sky = spawn("SkyLight", "SkyLight")
    spawn("ExponentialHeightFog", "HeightFog")
    ppv = spawn("PostProcessVolume", "PPV_Global")
    sun_c, sky_c = comp(sun, "DirectionalLightComponent"), comp(sky, "SkyLightComponent")
    defaults = getp(sun_c, ["Intensity", "Mobility", "bUseTemperature", "Temperature", "bAtmosphereSunLight"])
    warm = ARGS["temperature"] is not None                              # mild tint on top of the atmosphere's own reddening
    setp(sun_c, {"Intensity": ARGS["sun_lux"], "bUseTemperature": warm, "Temperature": ARGS["temperature"] or 6500.0,
                 "LightColor": {"r": 1, "g": 1, "b": 1, "a": 1}})
    setp(sky_c, {"Mobility": "Movable", "bRealTimeCapture": True})
    setp(ppv, {"bUnbound": True, "Settings": {
        "bOverride_AutoExposureMethod": True, "AutoExposureMethod": "AEM_Manual",
        "bOverride_AutoExposureApplyPhysicalCameraExposure": True, "AutoExposureApplyPhysicalCameraExposure": False,
        "bOverride_AutoExposureBias": True, "AutoExposureBias": -ARGS["ev100"]}})   # manual, no physical camera: EV100 = -bias
    s = getp(ppv, ["Settings"])["Settings"]
    return {"sun": sun, "sun_c": sun_c, "sky": sky, "sky_c": sky_c, "ppv": ppv, "defaults": defaults,
            "after": getp(sun_c, ["Intensity", "bUseTemperature", "Temperature", "LightColor"]),
            "sky_light": getp(sky_c, ["Mobility", "bRealTimeCapture", "SourceType"]),
            "bias": s["autoExposureBias"], "bias_override": s["bOverride_AutoExposureBias"]}
```

Read-back on 5.8.3: Intensity 120000, Use Temperature on at 5000 K, LightColor (1, 1, 1, 1),
SkyLight Movable and SLS_CapturedScene, bias -9.69 with its override true. The PPV Settings
read-back holds 463 keys: ask for `Settings` only when you need it.

### S2. Sun color and position read-back, plus the scene audit (1 call instead of 14)

```python
# script: S2_colour_and_audit
ARGS = {"sun": {"refPath": "<from S1>"}, "sun_c": {"refPath": "<from S1>"}, "elevation": 5.0, "yaw": 30.0}
import json
ST = "editor_toolset.toolsets.scene.SceneTools."
AC = "editor_toolset.toolsets.actor.ActorTools."
OT = "editor_toolset.toolsets.object.ObjectTools."

def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]

def colour(values):
    call(OT + "set_properties", {"instance": ARGS["sun_c"], "values": json.dumps({"LightColor": values})})
    return json.loads(call(OT + "get_properties", {"instance": ARGS["sun_c"], "properties": ["LightColor"]}))["LightColor"]

def count(cls):
    return len(call(ST + "find_actors", {"actor_type": {"refPath": "/Script/Engine." + cls}, "name": "", "tag": "",
                                          "collision_channels": []}))

def run():
    call(AC + "set_actor_transform", {"actor": ARGS["sun"], "xform": {
        "location": {"x": 0, "y": 0, "z": 500}, "rotation": {"pitch": -ARGS["elevation"], "yaw": ARGS["yaw"], "roll": 0},
        "scale": {"x": 1, "y": 1, "z": 1}}})
    rot = call(AC + "get_actor_transform", {"actor": ARGS["sun"]})["rotation"]
    floats = colour({"r": 1.0, "g": 0.2, "b": 0.2, "a": 1.0})   # stored as bytes: reads 0.2000 (51/255)
    bytes_ = colour({"R": 255, "G": 128, "B": 51, "A": 255})    # returns true, saturates: reads 1, 1, 1
    white = colour({"r": 1, "g": 1, "b": 1, "a": 1})
    counts = {c: count(c) for c in ("DirectionalLight", "SkyLight", "SkyAtmosphere", "PostProcessVolume", "ExponentialHeightFog")}
    return {"pitch": rot["pitch"], "floats": floats, "bytes_written": bytes_, "white": white, "counts": counts}
```

Expected on 5.8.3: pitch -5, floats g 0.2000, the 0-255 write reads (1, 1, 1, 1), counts one of
each. Write a tint as floats in 0..1, then read it back; for a temperature tint keep LightColor
white and set `bUseTemperature` and `Temperature`.

### S3. Exposure check against the sun, then the measured correction

Host side, before any frame: `ue_light.exposure_check(sun_lux, elevation, pp)` returns problems; on
the arena failure (a physical camera near EV100 9.9 plus a compensation of 13) it reported
"overexposed by 12.8 stops". After a capture (section 4) the correction is one call:

```
OT set_properties {"instance": <ppv>, "values": "{\"Settings\": {\"bOverride_AutoExposureBias\": true, \"AutoExposureBias\": -10.69}}"}
```

### S4. cvar existence for every name the plan uses (1 call instead of 6)

```python
# script: S4_cvars_exist
ARGS = {"names": ["r.MegaLights.Allowed", "r.EyeAdaptation.CachedLightingPreExposure", "r.Shadow.Virtual.Stats.Visible", "r.BufferVisualizationDumpFrames", "r.MegaLights.Allow", "r.Shadow.Virtual.ShowStats"]}
import json

def run():
    out = {}
    for n in ARGS["names"]:
        found = json.loads(execute_tool("EditorToolset.EditorAppToolset.SearchCVars", json.dumps({"name": n}))["returnValue"] or "{}")
        out[n] = {"exact": any(k.lower() == n.lower() for k in found), "matches": sorted(found)[:3]}
    return out
```

On 5.8.3 the first four are exact; `r.MegaLights.Allow` only partially matches
`r.MegaLights.Allowed`; `r.Shadow.Virtual.ShowStats` is absent (now
`r.Shadow.Virtual.Stats.Visible`). `ue_light.cvar_search_hit` does the same check host side.

### S5. Generated equirect as the sky light's cubemap, sun aimed at the panorama's sun (1 call instead of 10)

The host writes the panorama as Radiance `.hdr` (`ue_light.write_radiance_hdr`), finds its sun
(`find_sun_in_equirect`) and computes `angle = cubemap_angle_for_forward(0)` (270: image center at
+X) and the light rotation `sun_light_rotation(az, el, angle)`. Full method and checks:
`generated-skies.md`.

```python
# script: S5_generated_sky
ARGS = {"hdr": "/abs/path/sky.hdr", "sky_c": {"refPath": "<from S1>"}, "sun": {"refPath": "<from S1>"}, "angle": 270.0, "sun_rot": [-19.86, 269.82, 0.0], "backdrop": True}
import json
OT = "editor_toolset.toolsets.object.ObjectTools."

def call(name, args):
    return execute_tool(name, json.dumps(args))["returnValue"]

def run():
    tex = call("editor_toolset.toolsets.texture.TextureTools.import_file",
               {"folder_path": "/Game/Sky", "asset_name": "T_Sky", "source_file": ARGS["hdr"]})[0]
    cls = call(OT + "get_class", {"instance": tex})
    call(OT + "set_properties", {"instance": ARGS["sky_c"], "values": json.dumps({
        "SourceType": "SLS_SpecifiedCubemap", "Cubemap": tex, "SourceCubemapAngle": ARGS["angle"], "bRealTimeCapture": False})})
    p, y, r = ARGS["sun_rot"]
    call("editor_toolset.toolsets.actor.ActorTools.set_actor_transform", {"actor": ARGS["sun"], "xform": {
        "location": {"x": 0, "y": 0, "z": 500}, "rotation": {"pitch": p, "yaw": y, "roll": r}, "scale": {"x": 1, "y": 1, "z": 1}}})
    out = {"texture": tex, "class": cls,
           "sky_light": json.loads(call(OT + "get_properties", {"instance": ARGS["sky_c"],
                                                                 "properties": ["SourceType", "Cubemap", "SourceCubemapAngle"]}))}
    if ARGS["backdrop"]:   # needs the HDRIBackdrop plugin; its own SkyLight then duplicates yours: keep one
        hb = call("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_class", {
            "actor_type": {"refPath": "/HDRIBackdrop/Blueprints/HDRIBackdrop.HDRIBackdrop_C"}, "name": "HDRIBackdrop",
            "xform": {"location": {"x": 0, "y": 0, "z": 0}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0}, "scale": {"x": 1, "y": 1, "z": 1}}})
        call(OT + "set_properties", {"instance": hb, "values": json.dumps({"Cubemap": tex})})
        out["backdrop"] = json.loads(call(OT + "get_properties", {"instance": hb, "properties": ["Cubemap", "Intensity", "Size"]}))
    return out
```

Read-back on 5.8.3: class TextureCube, SourceType SLS_SpecifiedCubemap, angle 270; the backdrop
takes the cubemap (Intensity 1, Size 150). Rotating the HDRIBackdrop actor did not rotate its sky:
rotate the image instead (`rotate_equirect`).

### Single calls kept single (they are expected to fail, or stand alone)

```
OT set_properties {"instance": <sun actor>, "values": "{\"Intensity\": 5}"}        -> error: could not be set: Intensity
OT set_properties {"instance": <component>, "values": "{\"NoSuchProp\": 1}"}       -> error: could not be set: NoSuchProp
OT set_properties {"instance": <ppv>, "values": "{\"Settings.AutoExposureBias\": 0}"} -> error
EA CaptureViewport {"captureTransform": {...}}                                      -> "annotations" needs a default value
EA CaptureViewport {"captureTransform": {...}, "annotations": {}, "bShowUI": false} -> offscreen: "Viewport has zero size."
```

## 4. The measurement loop (Python for the frame, host for the numbers)

MCP has no high-resolution capture that worked offscreen, and the editor's Python has no numpy, so
the frame step is one `run_python` (or editor console) call and the numbers are read on the host:

1. Predict: `ev = ue_light.ev100_for_sun(sun_lux, elevation)`; write it with S1 (or the S3 call).
2. Capture, one call: `execute_console_command` for each of `ue_light.VIEW_MODES["buffer_dump"][0]`
   (`r.BufferVisualizationDumpFrames 1`, `r.BufferVisualizationDumpFramesAsHDR 1`), then
   `AutomationLibrary.take_high_res_screenshot(960, 540, path, force_game_view=True)`. The file
   lands after the call returns, with `<stem>_PreTonemapHDRColor.exr`, `_BaseColor.exr`,
   `_SceneColor.exr` and a dozen more beside it. Next call: the off list.
3. Meter on the host:
   `ue_light.meter_pretonemap(<stem>_PreTonemapHDRColor.exr, ev, {"ground": {"box": [0.3, 0.82, 0.7, 0.97]}})`
   returns cd/m2, lux for a 0.18 surface and the EV100 that puts it on mid gray (calibrated with an
   emissive card: 1.0 reads 0.248 at EV100 2, set as compensation -2). The buffer carries the
   compensation: pass the EV100 that S1 wrote (compensation = -EV100, physical camera off).
4. Correct and capture again; check `ue_review.image_checks(png)` is neither `all_white` nor
   `all_black`.

Run on 5.8.3 with a 120,000 lux sun at 5 degrees over a 0.18 floor: predicted EV100 9.69 from the
direct sun, metered 10.69 (5,185 lux: the real-time sky light added one stop at that elevation),
corrected to 10.69, re-metered 10.69. `albedo_check` on `_BaseColor.exr` read 0.181 for the 0.18
material.

## 5. When to use Python or a commandlet instead

- Level creation and saving, open-world maps, anything with `LevelEditorSubsystem` (no MCP tool
  creates a clean level).
- Screenshots and console variables (`execute_console_command`), the measurement loop above.
- `LightComponent.set_light_color(LinearColor)` when the color is LINEAR: it converts to the stored
  sRGB FColor ((1, 0.5, 0.2) linear is stored as (255, 188, 124)).
  `set_editor_property("light_color", LinearColor)` raises "Cannot nativize"; an `unreal.Color`
  works.
- Material and texture asset authoring for calibration (scenario-unreal-materials owns the masters).
- Movie Render Graph stills (`ue_light.queue_mrg_still`, not yet run end to end).
- Headless (`-nullrhi`) jobs for settings and lint only: nothing renders there.
