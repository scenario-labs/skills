# Materials through Epic's Unreal MCP toolsets

Read this before calling a material toolset: it gives the argument shapes so `describe_toolset`
(about 8,600 tokens for MaterialTools alone) is not needed. Everything marked "run on 5.8.3" was
executed through `ue_mcp.Mcp` against an editor started with
`ue_run.launch_editor(..., mcp_port=N)`. The recipes are a runnable test:
`python3 tests/code/unreal-materials/live_mcp_recipes.py` (starts and stops its own offscreen editor
on a copy of the base project, exit 0 only if every recipe passes). Last run on 5.8.3: 6 of 6
recipes pass call by call (59 tool calls), and the five script forms (R1, R2, R3, R5, R6) pass as
written, one call each (2026-10-21).

For how to structure a material (search existing assets first, parent plus instances, parameter
groups), read Epic's in-editor MaterialBasics skill first, through
`ToolsetRegistry.AgentSkillToolset`. This file covers what it does not: exact calls, readbacks,
traps, and when Python is the better channel.

## Intent map

| Intent                                                             | Toolset and tool                                                            | Notes                                                                                                                 |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| New master                                                         | `MaterialTools.create_material`                                             | returns `{"refPath": "/Game/F/M_X.M_X"}`; fails on an existing name (no overwrite flag)                               |
| Add a node                                                         | `MaterialTools.add_expression`                                              | class as `{"refPath": "/Script/Engine.MaterialExpression<Name>"}`; find names with `list_expression_classes(search=)` |
| Set node fields (parameter name, group, default, sampler, texture) | `ObjectTools.set_properties`                                                | `values` is a JSON **string**; property names are camelCase (`parameterName`, `defaultValue`, `samplerType`)          |
| Wire nodes                                                         | `MaterialTools.connect_expressions`                                         | output `""` means the default output; pin names from `get_expression_input_names` / `get_expression_output_names`     |
| Wire to the material                                               | `MaterialTools.connect_to_output`                                           | `material_property` is `MP_BaseColor`, `MP_Roughness`, `MP_Normal`, `MP_EmissiveColor`, `MP_Opacity`, ...             |
| Compile                                                            | `MaterialTools.recompile`                                                   | returns an error with the compiler message in a rendering editor; silent no-op under `-nullrhi`                       |
| Read the graph back                                                | `get_property_input`, `get_expression_inputs`, `get_expressions`            | proof that the wiring is what you meant                                                                               |
| Parameters of a material                                           | `MaterialInstanceTools.list_parameters`                                     | `[{"type": "Scalar"                                                                                                   | "Vector" | "Texture" | "StaticSwitch", "name": ...}]` |
| Instance                                                           | `MaterialInstanceTools.create`, `set_*_parameter`, `get_*_parameter`        | unknown names are errors (good: no silent no-op)                                                                      |
| Remove one override                                                | `MaterialInstanceTools.set_parameter_override(override=false)`              | the only way to drop a static switch override                                                                         |
| Permutation check                                                  | `AssetTools.get_asset_tags`                                                 | tag `HasStaticPermutationResource` is `"True"` when the instance compiles its own shaders                             |
| Compile errors in the log                                          | `LogsToolset.GetLogEntries(category="LogMaterial", pattern=<asset>)`        | the line names the platform (`SF_METAL_SM6` on a Mac)                                                                 |
| Texture import and flags                                           | `TextureTools.import_file`, `ObjectTools.get_properties` / `set_properties` | `SRGB`, `compressionSettings`, `LODGroup`, `virtualTextureStreaming`, `mipGenSettings`                                |
| Substrate state                                                    | `EditorAppToolset.SearchCVars(name="r.Substrate")`                          | read before choosing legacy or Substrate outputs                                                                      |
| World values                                                       | `MaterialTools.create_parameter_collection` + `ObjectTools.set_properties`  | arrays `scalarParameters`, `vectorParameters`                                                                         |
| Batch many calls in one turn                                       | `ProgrammaticToolset.execute_tool_script`                                   | sandboxed: `json`, `math`, `re`, `time`, `copy`, `datetime` only, no `unreal`                                         |

## Signatures (MaterialTools, MaterialInstanceTools, TextureTools; catalog 5.8.3)

Generated with `gen_toolset_map.py tests/arena/mcp-catalog-5.8.3 material texture`.

```
MaterialTools
add_expression(expression_class: Ref<Class>, material_or_function: Ref<Object>, x?: int, y?: int) -> Ref<MaterialExpression>
connect_expressions(from_expression: Ref<MaterialExpression>, from_output_name: str, to_expression: Ref<MaterialExpression>, to_input_name: str) -> None
connect_to_output(expression: Ref<MaterialExpression>, material_property: enum(MP_EmissiveColor|MP_Opacity|MP_OpacityMask|+34), output_name: str) -> None
create_function(asset_name: str, folder_path: str) -> Ref<MaterialFunction>
create_material(asset_name: str, folder_path: str) -> Ref<Material>
create_parameter_collection(asset_name: str, folder_path: str) -> Ref<MaterialParameterCollection>
delete_expression(expression: Ref<MaterialExpression>, material_or_function: Ref<Object>) -> None
delete_parameter_group(group_name: str, material_or_function: Ref<Object>) -> None
delete_unused_expressions(material: Ref<Material>) -> None
disconnect_expressions(to_expression: Ref<MaterialExpression>, to_input_name: str) -> None
disconnect_from_output(material: Ref<Material>, material_property: enum(...)) -> None
get_expression_input_names(expression: Ref<MaterialExpression>) -> [str]
get_expression_inputs(expression: Ref<MaterialExpression>, material_or_function: Ref<Object>) -> [{MaterialInputSource}]
get_expression_output_names(expression: Ref<MaterialExpression>) -> [str]
get_expressions(material_or_function: Ref<Object>) -> [Ref<MaterialExpression>]
get_property_input(material: Ref<Material>, material_property: enum(...)) -> {MaterialInputSource}
get_referencing_materials(material_function: Ref<MaterialFunction>) -> [{AssetData}]
layout_expressions(material_or_function: Ref<Object>) -> None
list_expression_classes(material_or_function: Ref<Object>, search: str) -> [Ref<Object>]
list_parameter_groups(material_or_function: Ref<Object>) -> [str]
recompile(material_or_function: Ref<Object>) -> None
rename_parameter_group(material_or_function: Ref<Object>, new_name: str, old_name: str) -> None

MaterialInstanceTools
clear_parameters(instance: Ref<MaterialInstanceConstant>) -> None
create(asset_name: str, folder_path: str, parent: Ref<MaterialInterface>) -> Ref<MaterialInstanceConstant>
get_scalar_parameter(instance, name: str) -> float
get_static_switch_parameter(instance, name: str) -> bool
get_texture_parameter(instance, name: str) -> Ref<Texture>
get_vector_parameter(instance, name: str) -> {LinearColor}
list_parameters(material: Ref<MaterialInterface>) -> [{MaterialParameter}]
set_parameter_override(instance, name: str, override: bool) -> None
set_parent(instance, parent: Ref<MaterialInterface>) -> None
set_scalar_parameter(instance, name: str, value: float) -> None
set_static_switch_parameter(instance, name: str, value: bool) -> None
set_texture_parameter(instance, name: str, value: Ref<Texture>) -> None
set_vector_parameter(instance, name: str, value: {LinearColor}) -> None

TextureTools
get_size(texture: Ref<Texture2D>) -> {IntPoint}
import_file(asset_name: str, folder_path: str, source_file: str) -> [Ref<Object>]
```

## Batching: one `execute_tool_script` instead of many calls

Four or more toolset calls in a row go through one
`ProgrammaticToolset.execute_tool_script {"script": "<text>"}` call: the scripts below replace 6 to
20 round trips each. The single-call JSON stays for one-off fixes and as the signature reference.
How the sandbox behaves (run on 5.8.3):

- The script defines `run()` and returns a dict; the tool returns it as a JSON string in
  `returnValue`. Imports are limited to `json`, `math`, `re`, `time`, `datetime`, `copy`;
  `import unreal` is refused.
- `execute_tool("<full toolset path>.<tool>", json.dumps(args))` returns `{"returnValue": ...}`; the
  tool name is the full path, for example
  `editor_toolset.toolsets.material.MaterialTools.create_material`.
- A failing call ends the whole script with that tool's error text; `try`/`except` does not catch
  it, and what earlier calls created stays. Keep a call that may fail (an existing asset name, R4's
  broken compile) outside the script, or check first (`AssetTools.exists`).
- Paths like `/abs/...` are placeholders for your files.

## Recipes (run on 5.8.3, `live_mcp_recipes.py`)

Toolset prefixes: `MaterialTools` and the others are
`editor_toolset.toolsets.material.MaterialTools`,
`editor_toolset.toolsets.material_instance.MaterialInstanceTools`,
`editor_toolset.toolsets.object.ObjectTools`, `editor_toolset.toolsets.asset.AssetTools`,
`editor_toolset.toolsets.texture.TextureTools`, `EditorToolset.LogsToolset`,
`EditorToolset.EditorAppToolset`.

### R1. Master with parameters and a texture-gating switch (20 calls)

```json
MaterialTools.create_material      {"folder_path": "/Game/Mat", "asset_name": "M_Master"}
MaterialTools.add_expression       {"material_or_function": {"refPath": "/Game/Mat/M_Master.M_Master"},
                                    "expression_class": {"refPath": "/Script/Engine.MaterialExpressionVectorParameter"}, "x": -600, "y": 0}
ObjectTools.set_properties         {"instance": <tint>, "values": "{\"parameterName\": \"BaseTint\", \"group\": \"Surface\", \"defaultValue\": {\"r\": 0.5, \"g\": 0.5, \"b\": 0.5, \"a\": 1}}"}
ObjectTools.set_properties         {"instance": <texParam>, "values": "{\"parameterName\": \"BaseColorMap\", \"samplerType\": \"SAMPLERTYPE_Color\", \"texture\": {\"refPath\": \"/Engine/EngineMaterials/DefaultDiffuse.DefaultDiffuse\"}}"}
ObjectTools.set_properties         {"instance": <switch>, "values": "{\"parameterName\": \"UseBaseColorMap\", \"group\": \"Features\", \"defaultValue\": false}"}
MaterialTools.connect_expressions  {"from_expression": <texParam>, "from_output_name": "RGB", "to_expression": <multiply>, "to_input_name": "A"}
MaterialTools.connect_expressions  {"from_expression": <multiply>, "from_output_name": "", "to_expression": <switch>, "to_input_name": "True"}
MaterialTools.connect_to_output    {"expression": <switch>, "output_name": "", "material_property": "MP_BaseColor"}
MaterialTools.recompile            {"material_or_function": <material>}
MaterialTools.get_property_input   {"material": <material>, "material_property": "MP_BaseColor"}
MaterialInstanceTools.list_parameters {"material": <material>}
AssetTools.save_assets             {"asset_paths": ["/Game/Mat/M_Master"]}
```

Readback: `get_property_input` returns
`{"output_name", "expression": {"refPath": ...StaticSwitchParameter_0}, "input_name"}`;
`list_parameters` returns the four names with types. Traps: switch inputs are named `"True"` and
`"False"`; a TextureSampleParameter2D has outputs `RGB, R, G, B, A, RGBA` and inputs `UVs`,
`Apply View MipBias`; the vector parameter's default output `""` resolves to RGB. Nodes added by the
toolset are named `<Class>_<n>` inside the material
(`/Game/Mat/M_Master.M_Master:MaterialExpressionScalarParameter_0`).

The same recipe as one script (run on 5.8.3, 1 call instead of 20):

```python
# execute_tool_script: R1 master with parameters
import json

MT = "editor_toolset.toolsets.material.MaterialTools."
OT = "editor_toolset.toolsets.object.ObjectTools."
FOLDER, NAME = "/Game/MatScripts", "M_Script_Master"


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def node(mat, cls, x, y, **props):
    e = call(MT + "add_expression", material_or_function=mat,
             expression_class={"refPath": "/Script/Engine." + cls}, x=x, y=y)
    if props:
        call(OT + "set_properties", instance=e, values=json.dumps(props))
    return e


def wire(a, out, b, inp):
    call(MT + "connect_expressions", from_expression=a, from_output_name=out, to_expression=b, to_input_name=inp)


def run():
    mat = call(MT + "create_material", folder_path=FOLDER, asset_name=NAME)
    tint = node(mat, "MaterialExpressionVectorParameter", -600, 0, parameterName="BaseTint", group="Surface",
                defaultValue={"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0})
    rough = node(mat, "MaterialExpressionScalarParameter", -600, 300, parameterName="Roughness",
                 group="Surface", defaultValue=0.5)
    tex = node(mat, "MaterialExpressionTextureSampleParameter2D", -900, -250, parameterName="BaseColorMap",
               group="Surface", samplerType="SAMPLERTYPE_Color",
               texture={"refPath": "/Engine/EngineMaterials/DefaultDiffuse.DefaultDiffuse"})
    mul = node(mat, "MaterialExpressionMultiply", -350, -150)
    sw = node(mat, "MaterialExpressionStaticSwitchParameter", -150, 0, parameterName="UseBaseColorMap",
              group="Features", defaultValue=False)
    wire(tex, "RGB", mul, "A")
    wire(tint, "", mul, "B")
    wire(mul, "", sw, "True")
    wire(tint, "", sw, "False")
    call(MT + "connect_to_output", expression=sw, output_name="", material_property="MP_BaseColor")
    call(MT + "connect_to_output", expression=rough, output_name="", material_property="MP_Roughness")
    call(MT + "recompile", material_or_function=mat)
    pin = call(MT + "get_property_input", material=mat, material_property="MP_BaseColor")
    params = call("editor_toolset.toolsets.material_instance.MaterialInstanceTools.list_parameters", material=mat)
    call("editor_toolset.toolsets.asset.AssetTools.save_assets", asset_paths=[FOLDER + "/" + NAME])
    return {"material": mat, "base_color_from": pin, "parameters": sorted([p["type"], p["name"]] for p in params)}
```

### R2. Instances, overrides, readback

```json
MaterialInstanceTools.create               {"folder_path": "/Game/Mat", "asset_name": "MI_Red", "parent": <material>}
MaterialInstanceTools.set_vector_parameter {"instance": <mi>, "name": "BaseTint", "value": {"r": 0.6, "g": 0.05, "b": 0.04, "a": 1}}
MaterialInstanceTools.set_scalar_parameter {"instance": <mi>, "name": "Roughness", "value": 0.35}
MaterialInstanceTools.get_scalar_parameter {"instance": <mi>, "name": "Roughness"}            -> 0.35
MaterialInstanceTools.set_static_switch_parameter {"instance": <mi2>, "name": "UseBaseColorMap", "value": true}
MaterialInstanceTools.set_texture_parameter {"instance": <mi2>, "name": "BaseColorMap", "value": {"refPath": "/Engine/EngineMaterials/DefaultWhiteGrid.DefaultWhiteGrid"}}
```

A misspelt name is an error, for example
`Parameter "NoSuchParam" is not a <MaterialParameterType.Scalar: 0> parameter on the material.` (run
on 5.8.3). The Python setters return False instead, which scripts often ignore.

As one script (run on 5.8.3, 1 call instead of 10; the misspelt-name check stays a single call
because a failing call ends a script):

```python
# execute_tool_script: R2 instances, overrides, readback
import json

MI = "editor_toolset.toolsets.material_instance.MaterialInstanceTools."
FOLDER = "/Game/MatScripts"
MASTER = {"refPath": "/Game/MatScripts/M_Script_Master.M_Script_Master"}


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def run():
    red = call(MI + "create", folder_path=FOLDER, asset_name="MI_Script_Red", parent=MASTER)
    call(MI + "set_vector_parameter", instance=red, name="BaseTint", value={"r": 0.6, "g": 0.05, "b": 0.04, "a": 1.0})
    call(MI + "set_scalar_parameter", instance=red, name="Roughness", value=0.35)
    tex = call(MI + "create", folder_path=FOLDER, asset_name="MI_Script_Textured", parent=MASTER)
    call(MI + "set_static_switch_parameter", instance=tex, name="UseBaseColorMap", value=True)
    call(MI + "set_texture_parameter", instance=tex, name="BaseColorMap",
         value={"refPath": "/Engine/EngineMaterials/DefaultWhiteGrid.DefaultWhiteGrid"})
    call("editor_toolset.toolsets.asset.AssetTools.save_assets",
         asset_paths=[FOLDER + "/MI_Script_Red", FOLDER + "/MI_Script_Textured"])
    return {"roughness": call(MI + "get_scalar_parameter", instance=red, name="Roughness"),
            "tint": call(MI + "get_vector_parameter", instance=red, name="BaseTint"),
            "switch": call(MI + "get_static_switch_parameter", instance=tex, name="UseBaseColorMap")}
```

### R3. Which instances fork the shader map

```json
AssetTools.get_asset_tags {"asset_path": "/Game/Mat/MI_Red"}       -> {"HasStaticPermutationResource": "False", ...}
AssetTools.get_asset_tags {"asset_path": "/Game/Mat/MI_Textured"}  -> {"HasStaticPermutationResource": "True", ...}
MaterialInstanceTools.set_parameter_override {"instance": <mi>, "name": "UseBaseColorMap", "override": false}
```

Run on 5.8.3: scalar and vector overrides leave the tag False (the instance shares the parent's
shaders); any static switch override sets it True, **including a switch set to the value it already
has by default**; `set_parameter_override(override=false)` and a save bring it back to False.
`ObjectTools.get_properties` cannot read `bHasStaticPermutationResource`; the registry tag can. Save
before reading the tag.

As one script (run on 5.8.3, 1 call instead of 9):

```python
# execute_tool_script: R3 which instances fork the shader map
import json

MI = "editor_toolset.toolsets.material_instance.MaterialInstanceTools."
AT = "editor_toolset.toolsets.asset.AssetTools."
FOLDER = "/Game/MatScripts"
MASTER = {"refPath": "/Game/MatScripts/M_Script_Master.M_Script_Master"}
INSTANCES = ["MI_Script_Red", "MI_Script_Textured"]


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def forks(name):   # registry tag; save before reading it
    return call(AT + "get_asset_tags", asset_path=FOLDER + "/" + name).get("HasStaticPermutationResource")


def run():
    out = {n: forks(n) for n in INSTANCES}
    mi = call(MI + "create", folder_path=FOLDER, asset_name="MI_Script_SwitchAtDefault", parent=MASTER)
    call(MI + "set_static_switch_parameter", instance=mi, name="UseBaseColorMap", value=False)
    call(AT + "save_assets", asset_paths=[FOLDER + "/MI_Script_SwitchAtDefault"])
    out["switch_set_to_default"] = forks("MI_Script_SwitchAtDefault")
    call(MI + "set_parameter_override", instance=mi, name="UseBaseColorMap", override=False)
    call(AT + "save_assets", asset_paths=[FOLDER + "/MI_Script_SwitchAtDefault"])
    out["after_clearing_override"] = forks("MI_Script_SwitchAtDefault")
    return out
```

### R4. Prove the compile, catch the failure

```json
MaterialTools.recompile        {"material_or_function": <material>}
LogsToolset.GetLogEntries      {"category": "LogMaterial", "maxEntries": 5, "pattern": "M_Broken"}
```

In an offscreen (rendering) editor, a TextureSampleParameter2D with `samplerType` Normal and no
texture makes `recompile` return an error:
`Material failed to compile: (Node TextureSampleParameter2D) Sampler type is Normal, should be Color for /Engine/EngineResources/DefaultTexture.DefaultTexture`,
and the log holds
`Failed to compile Material for platform SF_METAL_SM6, Default Material will be used in game.`
Setting `texture` to `/Engine/EngineMaterials/FlatNormal.FlatNormal` fixes it (run on 5.8.3). R4
stays as single calls: its point is a failing call, which would end a script. Under `-nullrhi`
(`mode="headless"`) the same call returns success and compiles nothing: a headless pass proves
wiring, never compilation.

Default textures that match each sampler type (run on 5.8.3): Color
`/Engine/EngineMaterials/DefaultDiffuse`, Normal `/Engine/EngineMaterials/FlatNormal`, Masks
`/Engine/EngineMaterials/DefaultDiffuse_TC_Masks`, Linear grayscale
`/Engine/EngineMaterials/BaseFlattenGrayscaleMap` (`TC_Grayscale`, `SRGB` false), Linear color
`/Engine/EngineMaterials/BaseFlattenLinearColor`. A Grayscale sampler needs `TC_Grayscale` with
`SRGB` true, and no engine texture was verified for it. Assign the real texture, or read a
candidate's `SRGB` and `compressionSettings` with `ObjectTools.get_properties` (R5) before using it.

### R5. Texture import flags (packed ORM)

```json
TextureTools.import_file    {"folder_path": "/Game/Mat/Tex", "asset_name": "T_Crate_ORM", "source_file": "/abs/T_Crate_ORM.png"}
ObjectTools.get_properties  {"instance": <tex>, "properties": ["SRGB", "compressionSettings", "LODGroup", "virtualTextureStreaming", "mipGenSettings"]}
   -> {"SRGB": true, "compressionSettings": "TC_Default", "LODGroup": "TEXTUREGROUP_World", "virtualTextureStreaming": false, "mipGenSettings": "TMGS_FromTextureGroup"}
ObjectTools.set_properties  {"instance": <tex>, "values": "{\"SRGB\": false, \"compressionSettings\": \"TC_Masks\"}"}
TextureTools.get_size       {"texture": <tex>}  -> {"x": 256, "y": 256}
```

The importer does not recognize a packed mask by name or content: it lands as sRGB color (run on
5.8.3). Normal maps are detected from the pixels (`TC_Normalmap`, `TEXTUREGROUP_WorldNormalMap`); a
blue-dominant color image can be detected as a normal map too, so read the flags after every import.
Enum values through ObjectTools use the reflected spelling (`TC_Masks`, `TC_Normalmap`), which
differs from the Python enum (`TC_MASKS`).

As one script (run on 5.8.3, 1 call instead of 6). Inside one `set_properties`, keys apply in order,
and an `SRGB` set while the texture is still `TC_Normalmap` was lost when the compression changed:
put `compressionSettings` before `SRGB`.

```python
# execute_tool_script: R5 texture import flags (packed ORM)
import json

OT = "editor_toolset.toolsets.object.ObjectTools."
SOURCE = "/abs/T_Crate_ORM.png"          # the file to import
FOLDER, NAME = "/Game/MatScripts/Tex", "T_Script_ORM"
KEYS = ["SRGB", "compressionSettings", "LODGroup", "virtualTextureStreaming", "mipGenSettings"]


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def flags(t):   # get_properties returns a JSON string
    return json.loads(call(OT + "get_properties", instance=t, properties=KEYS))


def run():
    t = call("editor_toolset.toolsets.texture.TextureTools.import_file",
             folder_path=FOLDER, asset_name=NAME, source_file=SOURCE)[0]
    before = flags(t)
    call(OT + "set_properties", instance=t, values=json.dumps({"SRGB": False, "compressionSettings": "TC_Masks"}))
    call("editor_toolset.toolsets.asset.AssetTools.save_assets", asset_paths=[FOLDER + "/" + NAME])
    return {"before": before, "after": flags(t),
            "size": call("editor_toolset.toolsets.texture.TextureTools.get_size", texture=t)}
```

### R6. Substrate state and a parameter collection

```json
EditorAppToolset.SearchCVars  {"name": "r.Substrate"}
   -> {"r.Substrate": {"value": 0}, "r.Substrate.ProjectGBufferFormat": {"value": 1}, "r.Substrate.BytesPerPixel": {"value": 80}, "r.Substrate.ClosuresPerPixel": {"value": 4}, ...}
MaterialTools.create_parameter_collection {"folder_path": "/Game/Mat", "asset_name": "MPC_World"}
ObjectTools.set_properties {"instance": <mpc>, "values": "{\"scalarParameters\": [{\"parameterName\": \"Wetness\", \"defaultValue\": 0}], \"vectorParameters\": [{\"parameterName\": \"WindDir\", \"defaultValue\": {\"r\": 1, \"g\": 0, \"b\": 0, \"a\": 0}}]}"}
```

`SearchCVars` returns a JSON string: parse it. `r.Substrate.MaxClosureCount` does not exist in
5.8.3.

As one script (run on 5.8.3, 1 call instead of 5):

```python
# execute_tool_script: R6 Substrate state and a parameter collection
import json

OT = "editor_toolset.toolsets.object.ObjectTools."
FOLDER, NAME = "/Game/MatScripts", "MPC_Script_World"


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def run():
    cv = json.loads(call("EditorToolset.EditorAppToolset.SearchCVars", name="r.Substrate"))   # a JSON string
    mpc = call("editor_toolset.toolsets.material.MaterialTools.create_parameter_collection",
               folder_path=FOLDER, asset_name=NAME)
    call(OT + "set_properties", instance=mpc, values=json.dumps({
        "scalarParameters": [{"parameterName": "Wetness", "defaultValue": 0.0}],
        "vectorParameters": [{"parameterName": "WindDir", "defaultValue": {"r": 1, "g": 0, "b": 0, "a": 0}}]}))
    call("editor_toolset.toolsets.asset.AssetTools.save_assets", asset_paths=[FOLDER + "/" + NAME])
    back = json.loads(call(OT + "get_properties", instance=mpc, properties=["scalarParameters"]))
    return {"r.Substrate": cv["r.Substrate"]["value"],
            "r.Substrate.ProjectGBufferFormat": cv["r.Substrate.ProjectGBufferFormat"]["value"],
            "scalar_parameters": [p["parameterName"] for p in back["scalarParameters"]]}
```

## When to use Python or a commandlet instead

- **Graphs of more than a few nodes, or the same graph for several masters:**
  `scripts/ue_materials.py` builders through `ue_run.run_python` or the project-local `run_python`
  tool. One job replaces 20 to 60 tool calls and carries the lint and the compile check.
- **Compile proof with numbers:** `um.compile_check(material)` in an offscreen editor, or in a
  commandlet started with `-AllowCommandletRendering` (`ue_run.run_python(..., render=True)`): the
  same 342 pixel instructions for a gray surface as the offscreen editor, in about 26 s including
  boot (run on 5.8.3, `tests/code/unreal-materials/in_engine/job_compile_in_commandlet.py`). A plain
  commandlet or `-nullrhi` editor reads zeros and returns empty lists from `get_used_textures`. In
  the rendering commandlet a failed compile showed as `num_samplers` -1 and 0 instructions before
  its log line was flushed, which `compile_check` treats as a failure.
- **Bulk instance edits, texture audits over a folder, static switch census:** Python
  (`audit_textures`, `switch_census`), because each MCP call is one property on one asset.
- **Usage flag overrides per instance:** `MaterialEditingLibrary.set_material_usage_override` /
  `has_material_usage_override` exist in 5.8.3 Python; no toolset covers them.
- **Asset creation that may overwrite:** `create_material` refuses an existing name. In Python,
  unattended `create_asset` on an existing path returns None ("CanCreateAsset cannot ask the user");
  pass `overwrite_existing=True` (5.8) or delete first (run on 5.8.3).
