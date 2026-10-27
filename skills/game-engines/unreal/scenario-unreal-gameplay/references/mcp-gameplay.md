# Epic Unreal MCP for gameplay: toolsets, signatures, live recipes

Run on UE 5.8.3 (macOS, headless editor started with `ue_run.launch_editor(..., mcp_port=N)`) on
2026-10-21. Every recipe below is in `tests/code/unreal-gameplay/live_mcp_recipes.py`, which builds
its own project from engine template content, starts and stops its own editor and exits 0 only when
every recipe, its script form and a disk reload check pass (last run: 14 of 14). Toolset names are
the full names `call_tool` wants. Object references are `{"refPath": "/Game/Folder/Asset.Asset"}`: a
package path without `.Asset` is refused ("not a valid object path").

**Batch first.** Four or more toolset calls in a row go in one
`editor_toolset.toolsets.programmatic.ProgrammaticToolset.execute_tool_script {"script": "..."}`
call: the script defines `run()`, calls `execute_tool("<toolset>.<tool>", json_string)` (it returns
the result dict; read `["returnValue"]`), returns a dict (it comes back as a JSON string), and may
import only json, math, re, time, datetime and copy (no `unreal`). Recipes 1, 2, 3, 8 and 9 below
are such scripts (`# script:` blocks; change the `ARGS` line only); `live_mcp_recipes.py` runs them
as written. A failing tool ends the script with its traceback and keeps what was created before it,
so keep calls that may fail (probes, name guesses) as single `call_tool` calls. The JSON lists show
the same calls one by one, for a single call or for reading the argument shapes.

Read Epic's in-editor BlueprintBasics skill first (through `ToolsetRegistry.AgentSkillToolset`) for
the DSL workflow; this page adds the argument shapes, the traps found live and the gameplay steps
the toolsets do not cover.

## Which tool for which intent

| Intent                                                           | Toolset and tool                                                                                    | Notes (run on 5.8.3 unless marked catalog)                                                            |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| New Blueprint class                                              | `BlueprintTools.create`                                                                             | `asset_type` is the parent class: `{"refPath": "/Script/Engine.Actor"}` or a Blueprint's `..._C`      |
| Variables, functions, params                                     | `add_variable`, `add_function_graph`, `add_function_param`                                          | `type_name` `float`, `bool`; the graph ref comes back as `/Game/X/BP.BP:FuncName`                     |
| Write or read logic                                              | `write_graph_dsl`, `read_graph_dsl`, `get_graph_dsl_docs`                                           | write compiles; errors list the real pin names                                                        |
| Find node ids and pins                                           | `find_node_types`, `get_node_type_pins`                                                             | never guess: `Math                                                                                    | Float | ToString`does not exist,`Utilities | String | ToString(Float)` does |
| Components on a Blueprint                                        | `ActorTools.add_component` with `owner` = the Blueprint                                             | returns `/Game/X/BP.BP_C:Name_GEN_VARIABLE`; configure it with `ObjectTools.set_properties`; recipe 9 |
| Event of a component (overlap, hit)                              | `BlueprintTools.add_component_bound_event`, then `write_graph_dsl`                                  | event header `OnComponentBeginOverlap(Trigger)`; recipe 9                                             |
| Read nodes and pins                                              | `find_nodes` (title `""` lists all), `get_node_infos`                                               | pin ids are `{"direction": "EGPD_Output", "index_id": N, "node": {"refPath": ...}}`                   |
| Compile                                                          | `compile_blueprint`                                                                                 | returns null on success, raises with the error list                                                   |
| Set Blueprint defaults                                           | `ObjectTools.set_properties` on the Blueprint path                                                  | sets the CDO; `values` is a JSON string                                                               |
| HUD and widgets                                                  | `UMGToolSet.CreateWidgetBlueprint`, `AddWidget`, `ToggleWidgetAsVariable`, `CompileWidgetBlueprint` | slots and widget properties through `ObjectTools`                                                     |
| Data tables                                                      | `DataTableTools.create`, `add_rows`, `set_rows`, `get_rows`, `search_row_structs`                   | schema = a row struct ref; keys come back lowerCamel                                                  |
| Gameplay tags                                                    | `GameplayTagsToolset.AddTag`, `ListTags`, `GetTagInfo`, `RemoveTag`, `RenameTag`                    | always pass `comment` and `tagSource: "DefaultGameplayTags.ini"`                                      |
| Automation tests                                                 | `AutomationTestToolset.DiscoverTests`, `ListTests`, `RunTests`                                      | synchronous; Python tests under `Content/Python/**/test_*.py`                                         |
| Play in editor                                                   | `EditorToolset.EditorAppToolset.StartPIE`, `IsPIERunning`, `StopPIE`                                | works in a headless (`-nullrhi`) editor                                                               |
| PIE players and net mode                                         | `ObjectTools.set_properties` on `/Script/UnrealEd.Default__LevelEditorPlaySettings`                 | the class is not exposed to Python                                                                    |
| GE component tags, GE modifiers                                  | `ObjectTools.set_properties` on the component or the GE CDO                                         | Python cannot write them (see recipe 7)                                                               |
| Read StateTrees                                                  | `StateTreeTools.get_root_states`, `get_children`, `get_tasks`, `get_transitions`                    | read only; no tool creates states                                                                     |
| StateTree parameters per enemy                                   | `ObjectTools.set_properties` on the component template (`..._GEN_VARIABLE`)                         | value survives compile, save and reload                                                               |
| Runtime GAS state                                                | `GASToolsets.AbilitySystemInspectorToolset`                                                         | catalog; needs a running PIE with an ASC [not yet run]                                                |
| Gameplay cues, attribute sets                                    | `GASToolsets.GameplayCueToolset`, `AttributeSetToolset`                                             | catalog [not yet run]: attribute sets are C++                                                         |
| Behavior Trees, conversations, data registries, world conditions | `BehaviorTreeTools`, `ConversationTools`, `DataRegistryTools`, `WorldConditionTools`                | catalog, read only [not yet run]                                                                      |
| Curve, string tables, data assets                                | `CurveTableTools`, `StringTableTools`, `DataAssetTools.create`                                      | catalog [not yet run]                                                                                 |
| Batch many calls                                                 | `ProgrammaticToolset.execute_tool_script`                                                           | a sandbox that calls toolsets; it has no `unreal` module                                              |
| Log lines                                                        | `EditorToolset.LogsToolset.GetLogEntries`                                                           | pass `category` explicitly (omitting it errored)                                                      |

Console commands, key injection and the GE or StateTree asset creation below need editor Python:
Epic's toolsets have no console tool. Use the project-local Python toolset
(`ue_env.install_python_toolset`, then `agent.AgentPythonToolset.run_python`) or Remote Execution;
both are described in scenario-unreal-expert `references/channels.md`.

## Recipes (arguments that worked)

### 1. Actor Blueprint with variables, a function and BeginPlay logic

```json
{
  "toolset": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "calls": [
    [
      "create",
      {
        "folder_path": "/Game/Recipes",
        "asset_name": "BP_Pickup",
        "asset_type": { "refPath": "/Script/Engine.Actor" }
      }
    ],
    [
      "add_variable",
      {
        "blueprint": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup" },
        "name": "HealAmount",
        "type_name": "float"
      }
    ],
    [
      "add_variable",
      {
        "blueprint": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup" },
        "name": "bUsed",
        "type_name": "bool"
      }
    ],
    [
      "add_function_graph",
      {
        "blueprint": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup" },
        "graph_name": "ScaledHeal"
      }
    ],
    [
      "add_function_param",
      {
        "graph": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup:ScaledHeal" },
        "param_name": "Multiplier",
        "param_type": "float",
        "input_param": true
      }
    ],
    [
      "add_function_param",
      {
        "graph": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup:ScaledHeal" },
        "param_name": "Result",
        "param_type": "float",
        "input_param": false
      }
    ],
    [
      "find_node_types",
      {
        "graph": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup:ScaledHeal" },
        "type_id_filter": "Variables|Default|",
        "context_pins": []
      }
    ],
    [
      "write_graph_dsl",
      {
        "graph": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup:ScaledHeal" },
        "code": "(fn ScaledHeal (Multiplier)\n  (return (Math|Float|Clamp(Float) (* (Variables|Default|GetHealAmount) Multiplier) 0.0 100.0)))"
      }
    ],
    [
      "write_graph_dsl",
      {
        "graph": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup:EventGraph" },
        "code": "(event EventBeginPlay\n  (if (not (Variables|Default|GetUsed))\n    (Development|PrintString (Utilities|String|ToString(Float) (CallFunction|ScaledHeal :Multiplier 2.0)))))"
      }
    ],
    [
      "compile_blueprint",
      {
        "blueprint": { "refPath": "/Game/Recipes/BP_Pickup.BP_Pickup" },
        "warnings_as_errors": true
      }
    ]
  ]
}
```

Then
`ObjectTools.set_properties {"instance": {"refPath": "/Game/Recipes/BP_Pickup.BP_Pickup"}, "values": "{\"HealAmount\": 25.0}"}`
and `AssetTools.save_assets {"asset_paths": ["/Game/Recipes/BP_Pickup"]}`. The same as one script
(12 calls, 1 turn, run on 5.8.3):

```python
# script: G1_blueprint
ARGS = {"folder": "/Game/Recipes", "name": "BP_Pickup", "heal": 25.0, "function": "ScaledHeal"}
import json
BP = "editor_toolset.toolsets.blueprint.BlueprintTools."

def bp_call(tool, **kw):
    return execute_tool(BP + tool, json.dumps(kw)).get("returnValue")

def run():
    path = ARGS["folder"] + "/" + ARGS["name"]
    bp = {"refPath": path + "." + ARGS["name"]}
    fn = {"refPath": bp["refPath"] + ":" + ARGS["function"]}
    bp_call("create", folder_path=ARGS["folder"], asset_name=ARGS["name"], asset_type={"refPath": "/Script/Engine.Actor"})
    bp_call("add_variable", blueprint=bp, name="HealAmount", type_name="float")
    bp_call("add_variable", blueprint=bp, name="bUsed", type_name="bool")
    bp_call("add_function_graph", blueprint=bp, graph_name=ARGS["function"])
    bp_call("add_function_param", graph=fn, param_name="Multiplier", param_type="float", input_param=True)
    bp_call("add_function_param", graph=fn, param_name="Result", param_type="float", input_param=False)
    bp_call("write_graph_dsl", graph=fn, code="(fn %s (Multiplier)\n  (return (Math|Float|Clamp(Float) "
            "(* (Variables|Default|GetHealAmount) Multiplier) 0.0 100.0)))" % ARGS["function"])
    bp_call("write_graph_dsl", graph={"refPath": bp["refPath"] + ":EventGraph"},
            code="(event EventBeginPlay\n  (if (not (Variables|Default|GetUsed))\n    (Development|PrintString "
                 "(Utilities|String|ToString(Float) (CallFunction|%s :Multiplier 2.0)))))" % ARGS["function"])
    bp_call("compile_blueprint", blueprint=bp, warnings_as_errors=True)
    execute_tool("editor_toolset.toolsets.object.ObjectTools.set_properties",
                 json.dumps({"instance": bp, "values": json.dumps({"HealAmount": ARGS["heal"]})}))
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets", json.dumps({"asset_paths": [path]}))
    got = execute_tool("editor_toolset.toolsets.object.ObjectTools.get_properties",
                       json.dumps({"instance": bp, "properties": ["HealAmount"]}))["returnValue"]
    return {"blueprint": bp["refPath"], "heal": json.loads(got),
            "fn": bp_call("read_graph_dsl", graph=fn), "event": bp_call("read_graph_dsl", graph={"refPath": bp["refPath"] + ":EventGraph"})}
```

Traps (run on 5.8.3):

- The getter of `bUsed` is `Variables|Default|GetUsed` (the `b` is dropped); your own function is
  `CallFunction|ScaledHeal`.
- **Pass pins by keyword on member calls.** A positional literal on `CallFunction|ScaledHeal` binds
  to the hidden `self` pin first and the value is lost (the call ran with 0.0).
- An unknown pin name fails the write with `Unknown input pin ... Input pins: [...]`: read the list,
  fix, rewrite.
- A type mismatch does not fail: the DSL inserts a conversion (a Rotator wired to a Vector pin
  became `GetRotationXVector`). Read the graph back after writing.
- `read_graph_dsl` is a view, not always valid input: it printed the bool getter as `(|GetbUsed)`
  and the call positionally.
- A new Actor Blueprint's event graph holds unconnected (ghost) BeginPlay,
  `Collision|EventActorBeginOverlap` and Tick nodes; writing `(event EventBeginPlay ...)` reuses
  BeginPlay, and `read_graph_dsl` lists the other two.
- In Python, Blueprint variables keep their exact names (`cdo.get_editor_property("HealAmount")`,
  `"bUsed"`; `heal_amount` and `used` fail), unlike C++ bools, which drop the `b`.
- `set_properties` with `values` as a JSON object instead of a string returns ok with `false` and
  sets nothing; a package path without `.Name` is refused.
- **Function names are looked up across Blueprints.** (For calls on another Blueprint's instance,
  see recipe 9.) With `BP_Pickup` already holding `ScaledHeal`, the same script for a second
  Blueprint `BP_PickupS` compiled, but its BeginPlay read back as `(Class|BPPickup|ScaledHeal 2.0)`:
  the call bound to the other class's function. Give each Blueprint's functions distinct names (the
  script's `function` argument) and read the graph back. With two classes both named `BP_Dup` in
  different folders, `Variables|BP_Dup|Get...` was "does not exist" for both.
- `remove_variable` replaced the variable's getters with a literal 0 and the Blueprint still
  compiled clean: grep the graphs before removing.
- Compile errors in Python: `bp.get_editor_property("status")` is `BS_ERROR`, and
  `unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp, "EventGraph").list_nodes_with_errors()`
  names the nodes.

### 2. HUD widget with a health bar and an update function

```json
{
  "toolset": "UMGToolSet.UMGToolSet",
  "calls": [
    [
      "CreateWidgetBlueprint",
      {
        "assetName": "WBP_HUD",
        "folderPath": "/Game/Recipes",
        "parentClass": { "refPath": "/Script/UMG.UserWidget" }
      }
    ],
    [
      "AddWidget",
      {
        "widgetBlueprint": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD" },
        "widgetClass": { "refPath": "/Script/UMG.CanvasPanel" },
        "widgetDisplayName": "Root"
      }
    ],
    [
      "AddWidget",
      {
        "widgetBlueprint": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD" },
        "widgetClass": { "refPath": "/Script/UMG.ProgressBar" },
        "widgetDisplayName": "HealthBar",
        "parentWidget": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD:WidgetTree.Root" }
      }
    ],
    [
      "AddWidget",
      {
        "widgetBlueprint": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD" },
        "widgetClass": { "refPath": "/Script/UMG.TextBlock" },
        "widgetDisplayName": "HealthText",
        "parentWidget": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD:WidgetTree.Root" }
      }
    ],
    [
      "ToggleWidgetAsVariable",
      {
        "widgetBlueprint": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD" },
        "widget": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD:WidgetTree.HealthBar" },
        "bIsVariable": true
      }
    ],
    [
      "CompileWidgetBlueprint",
      { "widgetBlueprint": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD" } }
    ]
  ]
}
```

Layout and values through `ObjectTools.set_properties`:

```json
{
  "instance": { "refPath": "/Game/Recipes/WBP_HUD.WBP_HUD:WidgetTree.Root.CanvasPanelSlot_0" },
  "values": "{\"LayoutData\": {\"offsets\": {\"left\": 40, \"top\": 40, \"right\": 400, \"bottom\": 32}, \"anchors\": {\"minimum\": {\"x\": 0, \"y\": 0}, \"maximum\": {\"x\": 0, \"y\": 0}}, \"alignment\": {\"x\": 0, \"y\": 0}}}"
}
```

With point anchors, `right` and `bottom` are width and height. The whole HUD, layout and update
function as one script (16 calls, run on 5.8.3; one compile after both `ToggleWidgetAsVariable`
calls is enough for the getters):

```python
# script: G2_hud
ARGS = {"folder": "/Game/Recipes", "name": "WBP_HUD", "bar": {"left": 40, "top": 40, "right": 400, "bottom": 32}}
import json
UMG = "UMGToolSet.UMGToolSet."
BP = "editor_toolset.toolsets.blueprint.BlueprintTools."
OT = "editor_toolset.toolsets.object.ObjectTools."

def call(prefix, tool, **kw):
    return execute_tool(prefix + tool, json.dumps(kw)).get("returnValue")

def run():
    path = ARGS["folder"] + "/" + ARGS["name"]
    wbp = {"refPath": path + "." + ARGS["name"]}
    tree = wbp["refPath"] + ":WidgetTree."
    call(UMG, "CreateWidgetBlueprint", assetName=ARGS["name"], folderPath=ARGS["folder"], parentClass={"refPath": "/Script/UMG.UserWidget"})
    call(UMG, "AddWidget", widgetBlueprint=wbp, widgetClass={"refPath": "/Script/UMG.CanvasPanel"}, widgetDisplayName="Root")
    for cls, name in (("ProgressBar", "HealthBar"), ("TextBlock", "HealthText")):
        call(UMG, "AddWidget", widgetBlueprint=wbp, widgetClass={"refPath": "/Script/UMG." + cls}, widgetDisplayName=name,
             parentWidget={"refPath": tree + "Root"})
        call(UMG, "ToggleWidgetAsVariable", widgetBlueprint=wbp, widget={"refPath": tree + name}, bIsVariable=True)
    call(UMG, "CompileWidgetBlueprint", widgetBlueprint=wbp)
    layout = {"LayoutData": {"offsets": ARGS["bar"], "anchors": {"minimum": {"x": 0, "y": 0}, "maximum": {"x": 0, "y": 0}},
                             "alignment": {"x": 0, "y": 0}}}
    call(OT, "set_properties", instance={"refPath": tree + "Root.CanvasPanelSlot_0"}, values=json.dumps(layout))
    fn = call(BP, "add_function_graph", blueprint=wbp, graph_name="UpdateHealth")
    for p in ("Current", "Max"):
        call(BP, "add_function_param", graph=fn, param_name=p, param_type="float", input_param=True)
    call(BP, "write_graph_dsl", graph=fn, code=(
        "(fn UpdateHealth (Current Max)\n  (bind pct (/ Current Max))\n"
        "  (Progress|SetPercent :self (Variables|%s|GetHealthBar) :InPercent pct)\n"
        "  (Widget|SetText(Text) :self (Variables|%s|GetHealthText) :InText (Utilities|Text|ToText(Float) :Value Current)))"
        % (ARGS["name"], ARGS["name"])))
    call(UMG, "CompileWidgetBlueprint", widgetBlueprint=wbp)
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets", json.dumps({"asset_paths": [path]}))
    return {"widget": wbp["refPath"], "slot": json.loads(call(OT, "get_properties", instance={"refPath": tree + "Root.CanvasPanelSlot_0"},
                                                               properties=["LayoutData"])),
            "fn": call(BP, "read_graph_dsl", graph=fn)}
```

The update function alone, after `add_function_graph` on the widget Blueprint and two float inputs:

```
(fn UpdateHealth (Current Max)
  (bind pct (/ Current Max))
  (Progress|SetPercent :self (Variables|WBP_HUD|GetHealthBar) :InPercent pct)
  (Widget|SetText(Text) :self (Variables|WBP_HUD|GetHealthText) :InText (Utilities|Text|ToText(Float) :Value Current)))
```

Traps: widget getters (`Variables|WBP_HUD|GetHealthBar`) exist only after `ToggleWidgetAsVariable`
and a compile. `Class|ProgressBar|SetPercent` is the property setter (pin `Percent`);
`Progress|SetPercent` is the function (pin `InPercent`). The k-th child's slot is
`CanvasPanelSlot_<k>` under the panel.

### 3. Data table from an engine row struct

```json
{
  "toolset": "editor_toolset.toolsets.data_table.DataTableTools",
  "calls": [
    [
      "create",
      {
        "asset_name": "DT_AttributeDefaults",
        "folder_path": "/Game/Recipes",
        "schema": { "refPath": "/Script/GameplayAbilities.AttributeMetaData" }
      }
    ],
    [
      "add_rows",
      {
        "data_table": { "refPath": "/Game/Recipes/DT_AttributeDefaults.DT_AttributeDefaults" },
        "row_names": ["HealthSet.Health", "HealthSet.MaxHealth"]
      }
    ],
    [
      "set_rows",
      {
        "data_table": { "refPath": "/Game/Recipes/DT_AttributeDefaults.DT_AttributeDefaults" },
        "values": "{\"HealthSet.Health\": {\"BaseValue\": 100.0, \"MinValue\": 0.0, \"MaxValue\": 100.0}, \"HealthSet.MaxHealth\": {\"BaseValue\": 100.0, \"MinValue\": 1.0, \"MaxValue\": 500.0}}"
      }
    ],
    [
      "get_rows",
      {
        "data_table": { "refPath": "/Game/Recipes/DT_AttributeDefaults.DT_AttributeDefaults" },
        "row_names": ["HealthSet.Health"]
      }
    ]
  ]
}
```

```python
# script: G3_data_table
ARGS = {"folder": "/Game/Recipes", "name": "DT_AttributeDefaults", "schema": "/Script/GameplayAbilities.AttributeMetaData",
        "rows": {"HealthSet.Health": {"BaseValue": 100.0, "MinValue": 0.0, "MaxValue": 100.0},
                 "HealthSet.MaxHealth": {"BaseValue": 100.0, "MinValue": 1.0, "MaxValue": 500.0}}}
import json
DT = "editor_toolset.toolsets.data_table.DataTableTools."

def call(tool, **kw):
    return execute_tool(DT + tool, json.dumps(kw)).get("returnValue")

def run():
    call("create", asset_name=ARGS["name"], folder_path=ARGS["folder"], schema={"refPath": ARGS["schema"]})
    dt = {"refPath": "%s/%s.%s" % (ARGS["folder"], ARGS["name"], ARGS["name"])}
    call("add_rows", data_table=dt, row_names=list(ARGS["rows"]))
    call("set_rows", data_table=dt, values=json.dumps(ARGS["rows"]))
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets", json.dumps({"asset_paths": [ARGS["folder"] + "/" + ARGS["name"]]}))
    return {"table": dt["refPath"], "rows": json.loads(call("get_rows", data_table=dt, row_names=list(ARGS["rows"])))}
```

`search_row_structs {}` lists the row structs; a `struct_name` filter returned nothing for "Row" and
"GameplayTag". A new row struct is C++ (`USTRUCT` deriving `FTableRowBase`): Python creates
`UserDefinedStruct` assets but has no member editing. From a CSV in Python:
`G.fill_data_table_from_csv(table, csv)` (run).

### 4. Gameplay tags

```json
{
  "toolset": "GameplayTagsToolset.GameplayTagsToolset",
  "calls": [
    [
      "AddTag",
      {
        "tagName": "Cooldown.Ability.Dash",
        "tagSource": "DefaultGameplayTags.ini",
        "comment": "dash cooldown"
      }
    ],
    ["ListTags", { "parentTag": "Cooldown" }],
    ["GetTagInfo", { "tagName": "Cooldown.Ability.Dash" }]
  ]
}
```

Traps: without `comment`, the tool's own description text is written as the tag's DevComment. An
unknown `tagSource` (for example `"Gameplay"`) returns null, creates nothing and raises no error;
`GetTagInfo` then says the tag does not exist. Tags land in `Config/DefaultGameplayTags.ini` under
`[/Script/GameplayTags.GameplayTagsSettings]` as `+GameplayTagList=(Tag="...",DevComment="...")` and
are usable in the same session.

### 5. Automation tests discovered and run

Put tests in `Content/Python/Tests/test_*.py` (plain asserts; the PythonAutomationTest plugin must
be on). Name = `Editor.Python.<ProjectName>.<dotted path>`.

```json
{
  "toolset": "AutomationTestToolset.AutomationTestToolset",
  "calls": [
    ["DiscoverTests", { "bForceRediscover": true }],
    ["ListTests", { "nameFilter": "Editor.Python.Arena", "tagFilter": "", "limit": 20 }],
    [
      "RunTests",
      {
        "testNames": [
          "Editor.Python.Arena.Tests.test_recipe_smoke",
          "Editor.Python.Arena.Tests.test_recipe_fail"
        ]
      }
    ]
  ]
}
```

`RunTests` returns when done with
`{"tests": [{"name", "state": "Success" | "Fail", "duration", "errors": [traceback lines]}]}`; it
ran in a headless editor. Epic ships its own toolset tests the same way
(`Editor.Python.EditorToolset...`).

### 6. PIE in a headless editor, injected input, two players (Python toolset for the console)

```json
["EditorToolset.EditorAppToolset", "StartPIE", { "options": { "warmupSeconds": 2.0 } }]
```

Then in editor Python:
`w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()`,
`unreal.SystemLibrary.execute_console_command(w, "Input.+key SpaceBar")`, later
`Input.-key SpaceBar`. The Third Person character rose 122 cm in 0.4 s; `pie_scenario` driven by
`start_on_tick` measured an apex of 127.4 cm at JumpZVelocity 500 and gravity 980 (theory v^2/2g =
127.6 cm). `StopPIE {}` ends it. Options: `bSimulate`, `playMode`, `startTransform`, `warmupSeconds`
(catalog).

Two players, listen server, then back:

```json
[
  "editor_toolset.toolsets.object.ObjectTools",
  "set_properties",
  {
    "instance": { "refPath": "/Script/UnrealEd.Default__LevelEditorPlaySettings" },
    "values": "{\"PlayNumberOfClients\": 2, \"PlayNetMode\": \"PIE_ListenServer\"}"
  }
]
```

`unreal.EditorLevelLibrary.get_pie_worlds(False)` then returned two worlds, the server one with a
GameMode, each with two characters. `G.configure_play(n, mode)` builds these arguments. Reset to `1`
and `PIE_Standalone`.

### 7. Cooldown Gameplay Effect with tags, and a fixed-magnitude twin (Python plus ObjectTools)

Python cannot reach the GE tag components (the classes are not exposed) or modifier magnitudes
("cannot be edited on instances"); ObjectTools can. In editor Python:

```python
REP = G.create_gameplay_effect("/Game/Recipes", "GE_Cooldown_Dash", "HAS_DURATION", 1.5,
                               granted_tags=["Cooldown.Ability.Dash"], asset_tags=["Ability.Dash"])
```

`REP["object_tools"]` holds one `set_properties` argument set per component, for example:

```json
{
  "instance": {
    "refPath": "/Game/Recipes/GE_Cooldown_Dash.Default__GE_Cooldown_Dash_C:TargetTagsGameplayEffectComponent_0"
  },
  "values": "{\"InheritableGrantedTagsContainer\": {\"added\": {\"gameplayTags\": [{\"tagName\": \"Cooldown.Ability.Dash\"}]}}}"
}
```

Send each to `ObjectTools.set_properties`, then `G.finish_gameplay_effect(path)` compiles and saves;
`combinedTags` fills in on compile and both components survive a reload. Asset tags use
`InheritableAssetTags`. Setting the deprecated `inheritable_owned_tags_container` does not create a
component on a new asset (the upgrade runs only for pre-5.3 data; GameplayEffect.cpp).

Fixed-magnitude twin of a SetByCaller damage GE: `G.make_fixed_magnitude_variant(src, dst)`
duplicates and returns `rep["cdo"]`;
`ObjectTools.get_properties {"instance": cdo, "properties": ["Modifiers"]}`,
`G.fixed_magnitude_values(that, 25.0)`, `ObjectTools.set_properties`, `G.compile_and_save`. The
lowerCamel JSON from `get_properties` is accepted back unchanged. Writing a modifier from scratch:

```json
{
  "Modifiers": [
    {
      "ModifierOp": "AddBase",
      "ModifierMagnitude": {
        "MagnitudeCalculationType": "SetByCaller",
        "SetByCallerMagnitude": { "DataTag": { "TagName": "Data.Damage" } }
      }
    }
  ]
}
```

A modifier needs an attribute from a C++ AttributeSet to do anything at runtime; a Blueprint-only
project has none.

### 8. StateTree from a template, read back, tuned per enemy

`StateTreeFactory` cannot get a schema from Python or ObjectTools, so `create_state_tree` returns
`created: false` unless you pass `template=`. The engine's Third Person Combat, Shooter,
SideScroller and TwinStick variants ship AI trees
(`Templates/TemplateResources/Standard/Variant_Combat/Content/Blueprints/AI/ST_CombatEnemy`, mounted
at `/Game/Variant_Combat`).

```python
G.create_state_tree("/Game/AI", "ST_Enemy", template="/Game/Variant_Combat/Blueprints/AI/ST_CombatEnemy")
SET = G.set_state_tree_parameters("/Game/Variant_Combat/Blueprints/AI/BP_CombatAIController", {"targetMeleeDistance": 150})
```

```json
["state_tree_toolset.toolsets.state_tree.StateTreeTools", "get_root_states", {"state_tree": {"refPath": "/Game/AI/ST_Enemy.ST_Enemy"}}]
["state_tree_toolset.toolsets.state_tree.StateTreeTools", "get_children", {"state": {"refPath": "/Game/AI/ST_Enemy.ST_Enemy:StateTreeEditorData_0.StateTreeState_0"}}]
["editor_toolset.toolsets.object.ObjectTools", "get_properties", {"instance": {"refPath": "/Game/Variant_Combat/Blueprints/AI/BP_CombatAIController.BP_CombatAIController_C:StateTreeAI_GEN_VARIABLE"}, "properties": ["StateTreeRef"]}]
```

`G.state_tree_parameter_values(that, {"targetMeleeDistance": 150})` gives the `values` for
`set_properties`; compile and save the controller. After the Python step that duplicates the tree,
the read-back and the per-enemy tuning are one script (run on 5.8.3):

```python
# script: G8_state_tree_tune
ARGS = {"tree": "/Game/Recipes/ST_Enemy.ST_Enemy", "controller": "/Game/Variant_Combat/Blueprints/AI/BP_CombatAIController",
        "component": "StateTreeAI_GEN_VARIABLE", "params": {"targetMeleeDistance": 150}}
import json
STT = "state_tree_toolset.toolsets.state_tree.StateTreeTools."
OT = "editor_toolset.toolsets.object.ObjectTools."

def call(prefix, tool, **kw):
    return execute_tool(prefix + tool, json.dumps(kw)).get("returnValue")

def run():
    tree = {"refPath": ARGS["tree"]}
    roots = call(STT, "get_root_states", state_tree=tree)
    kids = call(STT, "get_children", state=roots[0])
    name = ARGS["controller"].rsplit("/", 1)[1]
    comp = {"refPath": "%s.%s_C:%s" % (ARGS["controller"], name, ARGS["component"])}
    cur = json.loads(call(OT, "get_properties", instance=comp, properties=["StateTreeRef"]))
    ref = cur["StateTreeRef"]
    missing = [k for k in ARGS["params"] if k not in ref["parameters"]]
    if missing:   # names come back lowerCamel; a wrong name would be ignored silently
        return {"error": "unknown parameters %s" % missing, "known": sorted(ref["parameters"])}
    ref["parameters"].update(ARGS["params"])
    ref.pop("propertyOverrides", None)
    call(OT, "set_properties", instance=comp, values=json.dumps({"StateTreeRef": ref}))
    call("editor_toolset.toolsets.blueprint.BlueprintTools.", "compile_blueprint",
         blueprint={"refPath": "%s.%s" % (ARGS["controller"], name)}, warnings_as_errors=False)
    execute_tool("editor_toolset.toolsets.asset.AssetTools.save_assets", json.dumps({"asset_paths": [ARGS["controller"]]}))
    after = json.loads(call(OT, "get_properties", instance=comp, properties=["StateTreeRef"]))
    return {"roots": len(roots), "children": [k["refPath"].rsplit(".", 1)[-1] for k in kids],
            "parameters": after["StateTreeRef"]["parameters"], "tree_used": after["StateTreeRef"]["stateTree"]}
```

The value held after a reload. Parameter names come back lowerCamel (`targetMeleeDistance` for
`TargetMeleeDistance`). A component added in the Blueprint is not a CDO property:
`G.blueprint_components(bp)` finds it through `SubobjectDataSubsystem`.

### 9. Pickup: components, overlap event with a cast, variables, integer add, DestroyActor

One script (17 calls, 1 turn) makes a collector Character Blueprint with an int `Coins`, then a
pickup with a mesh, a sphere trigger, an int `Score` and this graph: on the trigger's begin overlap,
cast the other actor to the collector, add `points` to its `Coins` and to `Score`, destroy the
pickup. Run on 5.8.3, then played in a headless PIE: the collector teleported onto the pickup went
from 0 to 3 coins, `Score` read 3 and the pickup was gone.

```python
# script: G9_pickup
ARGS = {"folder": "/Game/Recipes", "name": "BP_Coin", "target": "BP_Collector", "target_var": "Coins", "make_target": True,
        "points": 1, "radius": 120.0, "mesh": "/Engine/BasicShapes/Cylinder.Cylinder", "mesh_scale": [0.5, 0.5, 0.1]}
import json
BP = "editor_toolset.toolsets.blueprint.BlueprintTools."
ACTOR = "editor_toolset.toolsets.actor.ActorTools."
OBJ = "editor_toolset.toolsets.object.ObjectTools."


def t(tool, **kw):
    return execute_tool(tool, json.dumps(kw)).get("returnValue")


def run():
    folder, name, target, var = ARGS["folder"], ARGS["name"], ARGS["target"], ARGS["target_var"]
    bp = {"refPath": "%s/%s.%s" % (folder, name, name)}
    graph = {"refPath": bp["refPath"] + ":EventGraph"}
    if ARGS["make_target"]:
        hero = {"refPath": "%s/%s.%s" % (folder, target, target)}
        t(BP + "create", folder_path=folder, asset_name=target, asset_type={"refPath": "/Script/Engine.Character"})
        t(BP + "add_variable", blueprint=hero, name=var, type_name="int")
        t(BP + "compile_blueprint", blueprint=hero, warnings_as_errors=True)
    t(BP + "create", folder_path=folder, asset_name=name, asset_type={"refPath": "/Script/Engine.Actor"})
    t(BP + "add_variable", blueprint=bp, name="Score", type_name="int")
    # owner = the Blueprint attaches to its DefaultSceneRoot; owner = a component attaches under that component
    mesh = t(ACTOR + "add_component", owner=bp, component_type={"refPath": "/Script/Engine.StaticMeshComponent"}, name="Mesh")
    trig = t(ACTOR + "add_component", owner=bp, component_type={"refPath": "/Script/Engine.SphereComponent"}, name="Trigger")
    sx, sy, sz = ARGS["mesh_scale"]
    t(OBJ + "set_properties", instance=mesh, values=json.dumps({
        "StaticMesh": ARGS["mesh"], "RelativeScale3D": {"X": sx, "Y": sy, "Z": sz},
        "BodyInstance": {"CollisionProfileName": "NoCollision"}}))
    t(OBJ + "set_properties", instance=trig, values=json.dumps({"SphereRadius": ARGS["radius"]}))
    t(BP + "add_component_bound_event", component=trig, event_name="OnComponentBeginOverlap", graph=graph)
    other = "Class|%s|" % target.replace("_", "")          # members of another Blueprint
    code = ("(event OnComponentBeginOverlap(Trigger) (OverlappedComponent OtherActor OtherComp OtherBodyIndex bFromSweep SweepResult)\n"
            "  (bind hero (Utilities|Casting|CastTo%s :Object OtherActor)\n"
            "    (:then\n"
            "      (%sSet%s :self hero :%s (+ (%sGet%s :self hero) %d))\n"
            "      (Variables|Default|SetScore (+ (Variables|Default|GetScore) %d))\n"
            "      (Actor|DestroyActor))\n"
            "    (:CastFailed)))") % (target, other, var, var, other, var, ARGS["points"], ARGS["points"])
    t(BP + "write_graph_dsl", graph=graph, code=code)
    t(BP + "compile_blueprint", blueprint=bp, warnings_as_errors=True)
    paths = ["%s/%s" % (folder, name)] + (["%s/%s" % (folder, target)] if ARGS["make_target"] else [])
    t("editor_toolset.toolsets.asset.AssetTools.save_assets", asset_paths=paths)
    cdo = {"refPath": "%s/%s.Default__%s_C" % (folder, name, name)}
    return {"blueprint": bp["refPath"], "mesh": mesh["refPath"], "trigger": trig["refPath"],
            "components": [c["refPath"].split(":")[-1] for c in t(ACTOR + "get_components", actor=cdo)],
            "trigger_parent": t(ACTOR + "get_parent_component", component=trig)["refPath"].split(":")[-1],
            "radius": json.loads(t(OBJ + "get_properties", instance=trig, properties=["SphereRadius"])),
            "graph": t(BP + "read_graph_dsl", graph=graph)}
```

Node ids and pins that worked (run on 5.8.3; `get_node_type_pins` prints pins without adding a
node):

| Node                                     | Type id to write                                                                                                                                                        | Pins                                      |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Component overlap event                  | `add_component_bound_event` first, then `(event OnComponentBeginOverlap(Trigger) (OverlappedComponent OtherActor OtherComp OtherBodyIndex bFromSweep SweepResult) ...)` | `list_component_events` names the events  |
| Actor overlap event                      | `(event Collision                                                                                                                                                       | EventActorBeginOverlap (OtherActor) ...)` | already in a new Actor graph; a cast, int add and DestroyActor under it compiled |
| Cast                                     | `Utilities                                                                                                                                                              | Casting                                   | CastToCharacter`, `CastTo<BlueprintName>`                                        | in `Object`; exec out `then`, `CastFailed`; data out `As<Class>` (`AsCharacter`); in the DSL, `bind` names it |
| Own variable                             | `Variables                                                                                                                                                              | Default                                   | GetScore`, `Variables                                                            | Default                                                                                                       | SetScore` | setter input pin = the variable name                             |
| Another Blueprint's variable or function | `Class                                                                                                                                                                  | <NameWithoutUnderscores>                  | GetCoins`, `SetCoins`, `AddCoins` (`BP_Hero`gives`BPHero`)                       | pass `:self` the cast result                                                                                  |
| Integer add                              | DSL `(+ a b)`; node `Utilities                                                                                                                                          | Operators                                 | Add`                                                                             | reads back as `Math                                                                                           | Integer   | int+int`(pins`A`, `B`, `ReturnValue`); that id cannot be written |
| Destroy                                  | `Actor                                                                                                                                                                  | DestroyActor`                             | `self` defaults to the owner                                                     |

Traps (run on 5.8.3):

- `find_node_types` did not list members or casts of a Blueprint created in the same session without
  a context pin. With the cast's `As` pin as `context_pins` it listed `Variables|Default|GetCoins`
  and `CallFunction|AddCoins`, but those ids are refused by `create_node` and `write_graph_dsl` (no
  context there). The `Class|BPHero|...` form worked in both.
- With two Blueprints holding a variable of the same name, `read_graph_dsl` printed the other class
  (`Class|BPHero|SetCoins` on a graph written with `Class|BPCollectorT|SetCoins`); PIE showed the
  right class's value changing. Check behavior in PIE, not the read-back label.
- `add_component` with `owner` = the Blueprint attaches under `DefaultSceneRoot`; with `owner` or
  `ActorTools.set_parent_component` = another component, it attaches under that one. A trigger
  attached under a mesh scaled (0.5, 0.5, 0.1) read radius 120 unscaled and 12 scaled: keep triggers
  off scaled meshes.
- `ActorTools.get_components` takes the class default object (`/Game/X/BP.Default__BP_C`).
- Template edits (collision profile, scale) showed on newly placed instances; one placed before the
  edit still read `BlockAllDynamic` and radius 120 after a compile. Re-place or check placed copies.
- Node level, when the DSL cannot express a node:
  `create_node {"graph", "type_id", "pos": {"x", "y"}}` returns the node;
  `connect_pins {"input_pin": PinID, "output_pin": PinID}` with PinIDs from `get_node_infos`; a
  wildcard `Utilities|Operators|Add` became Integer once wired. Exec-unconnected nodes do not show
  in `read_graph_dsl`; `find_nodes` with title `""` lists them.

## When to use Python or a commandlet instead

- **Headless commandlet** (`ue_run.run_python`, no editor open): Blueprint children of C++ classes
  and their defaults (`set_defaults` for class, object, soft and enum slots;
  `set_component_defaults`), Enhanced Input assets with modifiers and triggers (`apply_input_plan`),
  widget trees (`build_widget_tree` through `EditorUtilityLibrary.add_source_widget`), data tables
  from CSV, audits (`audit_gameplay`, `ai_setup_facts`) and disk checks after an MCP session. All
  run on 5.8.3.
- **Editor Python next to MCP**: console commands, `Input.+key` injection, PIE sampling
  (`pie_scenario` with `start_on_tick`), GE and StateTree assets (then ObjectTools for their
  fields).
- **C++**: attribute sets, ASC wiring, abilities' logic, StateTree tasks, row structs.
  `ue_gameplay_cpp.scaffold()` compiled with 0 errors and 0 warnings on 5.8.3 with Xcode 26.6
  (`tests/code/unreal-gameplay/live_cpp_build.py`, 67 s) once the Build.cs has
  `PublicIncludePaths.Add(ModuleDirectory)` (`patch_build_cs` adds it).
- **New levels**: no toolset creates one (the catalog has `load_level` and `create_level_instance`);
  use Python, then MCP for the graphs.
- **GUI, no API found**: StateTree states, tasks and transitions on a new tree; Behavior Tree nodes.
  Duplicate a template or do one precise GUI pass (`references/gui-paths.md`).

## Reconciliation with Epic's BlueprintBasics skill

Agrees with ours: read graphs as DSL first, look up node types and pins before writing, compile once
per logical unit, casting to a Blueprint is a hard load dependency (ours adds the cost numbers,
Arnbjornsson S2olUc9zcB8 [00:28:01]). Epic covers and we do not repeat: pure-node re-evaluation per
wire, compile before structural changes reach the CDO, Movable mobility for physics. v0.1 said graph
content was GUI or template work; on 5.8.3 `BlueprintTools.write_graph_dsl` writes event and
function graphs, so v0.2 treats graphs as scriptable and keeps C++ for logic that profiles hot or
must be reviewed as text. Ours adds the DSL traps of recipe 1, the gameplay architecture, GAS and
StateTree content, and the test loop.

## Signatures (generated with gen_toolset_map.py from the 5.8.3 catalog)

### `AutomationTestToolset.AutomationTestToolset` (7 tools, describe is about 1590 tokens)

- `DiscoverTests(bForceRediscover?: bool) -> str`
- `GetTestResults() -> str`
- `GetTestStatus() -> str`
- `ListTests(limit?: int, nameFilter: str, tagFilter: str) -> str`
- `RunTests(testNames: [str]) -> str`
- `RunTestsByFilter(filterExpression: str) -> str`
- `StopTests() -> bool`

### `DataRegistryToolset.DataRegistryTools` (7 tools, describe is about 2819 tokens)

- `GetItems(itemNames: [str], registryName: str) -> {..}`
- `GetRegistryInfo(registryName: str) -> {DataRegistryInfo}`
- `GetSchema(registryName: str) -> str`
- `ListDataSources(registryName: str) -> [{DataRegistrySourceSummary}]`
- `ListItems(registryName: str) -> [str]`
- `ListRegistries(structFilter?: Ref<ScriptStruct>) -> [str]`
- `ListRuntimeSources(registryName: str) -> [{DataRegistrySourceSummary}]`

### `GASToolsets.AbilitySystemInspectorToolset` (4 tools, describe is about 1710 tokens)

- `GetActiveEffects(actor: Ref<Actor>) -> [{ActiveEffectInfo}]`
- `GetActiveTags(actor: Ref<Actor>) -> [str]`
- `GetAttributeValues(actor: Ref<Actor>) -> [{RuntimeAttributeValue}]`
- `GetGrantedAbilities(actor: Ref<Actor>) -> [{GrantedAbilityInfo}]`

### `GASToolsets.AttributeSetToolset` (2 tools, describe is about 910 tokens)

- `FindAttributeSetClasses() -> [{AttributeSetClassInfo}]`
- `ListAttributes(className: str) -> [{GameplayAttributeInfo}]`

### `GASToolsets.GameplayCueToolset` (8 tools, describe is about 2520 tokens)

- `AddCueTag(comment?: str, cueTag: str) -> bool`
- `CreateCueNotifyAsset(assetName: str, bIsActor: bool, cueTag: str, packagePath: str) -> str`
- `ExecuteCueOnSelectedActor(cueTag: str, location: {Vector}, normal: {Vector}, normalizedMagnitude: float) -> bool`
- `FindCueNotifyAssets(parentTag: str) -> [{GameplayCueNotifyInfo}]`
- `FindCueTagsWithoutNotifies() -> [str]`
- `GetCueInfo(cueTag: str) -> {GameplayCueInfo}`
- `ListCues(parentTag: str) -> [str]`
- `RemoveCueTag(cueTag: str) -> bool`

### `GameplayTagsToolset.GameplayTagsToolset` (6 tools, describe is about 1360 tokens)

- `AddTag(comment?: str, tagName: str, tagSource: str) -> None`
- `FindReferencersByTag(tagName: str) -> [str]`
- `GetTagInfo(tagName: str) -> {GameplayTagInfo}`
- `ListTags(parentTag: str) -> [str]`
- `RemoveTag(tagName: str) -> None`
- `RenameTag(newTagName: str, oldTagName: str) -> None`

### `UMGToolSet.UMGToolSet` (23 tools, describe is about 20561 tokens)

- `AddUIComponent(componentClass: Ref<UIComponent>, widgetBlueprint: Ref<WidgetBlueprint>, widgetName: str) -> {UMGWidgetInfo}`
- `AddWidget(childIndex?: int, parentWidget?: Ref<Widget>, widgetBlueprint: Ref<WidgetBlueprint>, widgetClass: Ref<Widget>, widgetDisplayName: str) -> {UMGWidgetInfo}`
- `BindToEventProperty(eventName: str, propertyClass: Ref<Object>, propertyName: str, widgetBlueprint: Ref<WidgetBlueprint>) -> bool`
- `CompileWidgetBlueprint(widgetBlueprint: Ref<WidgetBlueprint>) -> bool`
- `CreateWidgetBlueprint(assetName: str, folderPath: str, parentClass: Ref<UserWidget>) -> Ref<WidgetBlueprint>`
- `GetNamedSlots(widgetBlueprint: Ref<WidgetBlueprint>) -> [{UMGNamedSlotEntry}]`
- `GetWidgetClassInfo(widgetClass: Ref<Widget>) -> {UMGWidgetClassEntry}`
- `GetWidgetDescription(maxDepth?: int, startWidget?: Ref<Widget>, widgetBlueprint: Ref<WidgetBlueprint>) -> {UMGWidgetDescriptionResult}`
- `GetWidgetTreeDepth(startWidget?: Ref<Widget>, widgetBlueprint: Ref<WidgetBlueprint>) -> int`
- `GetWidgets(widgetBlueprint: Ref<WidgetBlueprint>) -> {UMGWidgetTreeInfo}`
- `ListWidgetBlueprints(folderPath: str) -> [Ref<Object>]`
- `ListWidgetClasses(filter: str) -> [{UMGWidgetClassEntry}]`
- `MoveUIComponent(bMoveAfter: bool, componentClassToMove: Ref<UIComponent>, relativeToComponentClass: Ref<UIComponent>, widgetBlueprint: Ref<WidgetBlueprint>, widgetName: str) -> bool`
- `MoveWidget(childIndex?: int, newParent: Ref<PanelWidget>, widget: Ref<Widget>, widgetBlueprint: Ref<WidgetBlueprint>) -> {UMGWidgetInfo}`
- `RemoveUIComponent(componentClass: Ref<UIComponent>, widgetBlueprint: Ref<WidgetBlueprint>, widgetName: str) -> bool`
- `RemoveWidget(widget: Ref<Widget>, widgetBlueprint: Ref<WidgetBlueprint>) -> bool`
- `RenameWidget(newDisplayName: str, widget: Ref<Widget>, widgetBlueprint: Ref<WidgetBlueprint>) -> {UMGWidgetInfo}`
- `ReplaceWidgetWithChild(widgetBlueprint: Ref<WidgetBlueprint>, widgetToReplace: Ref<Widget>) -> bool`
- `ReplaceWidgetWithNamedSlot(namedSlot: str, widgetBlueprint: Ref<WidgetBlueprint>, widgetToReplace: Ref<Widget>) -> bool`
- `ReplaceWidgetWithTemplate(templateClass: Ref<Widget>, widgetBlueprint: Ref<WidgetBlueprint>, widgetToReplace: Ref<Widget>) -> {WidgetReplacementReport}`
- `SetNamedSlotContent(hostWidget: Ref<Widget>, slotName: str, widgetBlueprint: Ref<WidgetBlueprint>, widgetClass: Ref<Widget>, widgetName: str) -> {UMGWidgetInfo}`
- `ToggleWidgetAsVariable(bIsVariable: bool, widget: Ref<Widget>, widgetBlueprint: Ref<WidgetBlueprint>) -> None`
- `WrapWidgets(widgetBlueprint: Ref<WidgetBlueprint>, widgets: [Ref<Widget>], wrapperClass: Ref<PanelWidget>) -> [{UMGWidgetInfo}]`

### `WorldConditionsToolset.WorldConditionTools` (2 tools, describe is about 1078 tokens)

- `GetConditionDescription(condition: {FInstancedStruct}) -> str`
- `GetQueryDescription(queryDefinition: {WorldConditionQueryDefinition}) -> str`

### `aimodule_toolset.toolsets.behavior_tree.BehaviorTreeTools` (7 tools, describe is about 2221 tokens)

- `get_blackboard(behavior_tree: Ref<BehaviorTree>) -> Ref<BlackboardData>`
- `get_children(composite: Ref<BTCompositeNode>) -> [Ref<BTNode>]`
- `get_node_depth(behavior_tree: Ref<BehaviorTree>, node_index: int) -> int`
- `get_node_depths(behavior_tree: Ref<BehaviorTree>) -> [int]`
- `get_root_decorators(behavior_tree: Ref<BehaviorTree>) -> [Ref<BTDecorator>]`
- `get_subtree(node: Ref<BTNode>) -> Ref<BehaviorTree>`
- `list_nodes(behavior_tree: Ref<BehaviorTree>) -> [Ref<BTNode>]`

### `conversation_toolset.toolsets.conversation.ConversationTools` (7 tools, describe is about 2778 tokens)

- `get_all_nodes(conversation: Ref<ConversationDatabase>) -> [Ref<ConversationNode>]`
- `get_node_by_guid(conversation: Ref<ConversationDatabase>, guid: str) -> Ref<ConversationNode>`
- `get_node_connections(node: Ref<ConversationNodeWithLinks>) -> [str]`
- `get_node_guids(conversation: Ref<ConversationDatabase>) -> [str]`
- `get_sub_nodes(node: Ref<ConversationTaskNode>) -> [Ref<ConversationSubNode>]`
- `list_entry_points(conversation: Ref<ConversationDatabase>) -> [{ConversationEntryList}]`
- `list_speakers(conversation: Ref<ConversationDatabase>) -> [{CommonDialogueBankParticipant}]`

### `editor_toolset.toolsets.blueprint.BlueprintTools` (53 tools, describe is about 25646 tokens)

- `add_component_bound_event(component: Ref<ActorComponent>, event_name: str, graph: Ref<EdGraph>) -> Ref<EdGraphNode>`
- `add_event(blueprint: Ref<Blueprint>, event_name: str, position?: {IntPoint}) -> Ref<EdGraphNode>`
- `add_event_dispatcher(blueprint: Ref<Blueprint>, name: str) -> Ref<EdGraph>`
- `add_function_graph(blueprint: Ref<Blueprint>, graph_name: str) -> Ref<EdGraph>`
- `add_function_param(container_type?: enum(ARRAY|SET|MAP), graph: Ref<EdGraph>, input_param: bool, param_name: str, param_type: str) -> {PinID}`
- `add_node_pin(node: Ref<EdGraphNode>) -> {PinID}`
- `add_object_function_param(container_type?: enum(ARRAY|SET|MAP), graph: Ref<EdGraph>, input_param: bool, object_class: Ref<Class>, param_name: str) -> {PinID}`
- `add_object_variable(blueprint: Ref<Blueprint>, container_type?: enum(ARRAY|SET|MAP), graph?: Ref<EdGraph>, name: str, object_class: Ref<Class>) -> None`
- `add_struct_function_param(container_type?: enum(ARRAY|SET|MAP), graph: Ref<EdGraph>, input_param: bool, param_name: str, struct_type: Ref<ScriptStruct>) -> {PinID}`
- `add_struct_variable(blueprint: Ref<Blueprint>, container_type?: enum(ARRAY|SET|MAP), graph?: Ref<EdGraph>, name: str, struct_type: Ref<ScriptStruct>) -> None`
- `add_variable(blueprint: Ref<Blueprint>, container_type?: enum(ARRAY|SET|MAP), graph?: Ref<EdGraph>, name: str, type_name: str) -> None`
- `arrange_nodes(nodes: [Ref<EdGraphNode>]) -> None`
- `break_pins(input_pin: {PinID}, output_pin: {PinID}) -> None`
- `compile_blueprint(blueprint: Ref<Blueprint>, warnings_as_errors?: bool) -> None`
- `connect_pins(input_pin: {PinID}, output_pin: {PinID}) -> None`
- `create(asset_name: str, asset_type: Ref<Class>, folder_path: str) -> Ref<Blueprint>`
- `create_node(declaring_class?: Ref<Class>, graph: Ref<EdGraph>, pos: {IntPoint}, type_id: str) -> Ref<EdGraphNode>`
- `delete_node(node: Ref<EdGraphNode>) -> None`
- `find_node_categories(category_filter: str, context_pins: [{PinID}], graph: Ref<EdGraph>) -> [str]`
- `find_node_types(context_pins: [{PinID}], graph: Ref<EdGraph>, type_id_filter: str) -> [str]`
- `find_nodes(entry_points_only?: bool, graph: Ref<EdGraph>, node_class?: Ref<Class>, title: str) -> [Ref<EdGraphNode>]`
- `get_connected_subgraph(node: Ref<EdGraphNode>) -> [{NodeInfo}]`
- `get_create_event_function(node: Ref<K2Node_CreateDelegate>) -> str`
- `get_default_object(blueprint: Ref<Blueprint>) -> Ref<Object>`
- `get_graph(blueprint: Ref<Blueprint>, graph_name: str) -> Ref<EdGraph>`
- `get_graph_dsl_docs() -> str`
- `get_node_infos(nodes: [Ref<EdGraphNode>]) -> [{NodeInfo}]`
- `get_node_type_pins(graph: Ref<EdGraph>, type_id: str) -> {NodeInfo}`
- `get_parent(blueprint: Ref<Blueprint>) -> Ref<Class>`
- `get_pin_value(pin: {PinID}) -> str`
- `get_variable_category(blueprint: Ref<Blueprint>, variable_name: str) -> str`
- `get_variable_replication(blueprint: Ref<Blueprint>, variable_name: str) -> enum(None|Replicated|RepNotify)`
- `list_compatible_event_functions(node: Ref<K2Node_CreateDelegate>) -> [str]`
- `list_component_events(component: Ref<ActorComponent>) -> [str]`
- `list_event_dispatchers(blueprint: Ref<Blueprint>) -> [Ref<EdGraph>]`
- `list_events(blueprint: Ref<Blueprint>) -> [{BlueprintFunctionInfo}]`
- `list_functions(blueprint: Ref<Blueprint>) -> [{BlueprintFunctionInfo}]`
- `list_graphs(blueprint: Ref<Blueprint>) -> [Ref<EdGraph>]`
- `list_variables(blueprint: Ref<Blueprint>, graph?: Ref<EdGraph>) -> [str]`
- `read_graph_dsl(graph: Ref<EdGraph>) -> str`
- `remove_function_graph(blueprint: Ref<Blueprint>, graph_name: str) -> None`
- `remove_function_param(graph: Ref<EdGraph>, input_param: bool, param_name: str) -> None`
- `remove_node_pin(node: Ref<EdGraphNode>, pin: {PinID}) -> None`
- `remove_variable(blueprint: Ref<Blueprint>, graph?: Ref<EdGraph>, name: str) -> None`
- `retarget_node_class(new_class: Ref<Class>, node: Ref<EdGraphNode>, old_class: Ref<Class>) -> None`
- `set_create_event_function(function_name: str, node: Ref<K2Node_CreateDelegate>) -> None`
- `set_node_position(node: Ref<EdGraphNode>, pos: {IntPoint}) -> None`
- `set_parent(blueprint: Ref<Blueprint>, parent_class: Ref<Class>) -> None`
- `set_pin_value(pin: {PinID}, value: str) -> None`
- `set_variable_category(blueprint: Ref<Blueprint>, category: str, variable_name: str) -> None`
- `set_variable_instance_editable(blueprint: Ref<Blueprint>, instance_editable: bool, variable_name: str) -> None`
- `set_variable_replication(blueprint: Ref<Blueprint>, replication: enum(None|Replicated|RepNotify), variable_name: str) -> None`
- `write_graph_dsl(code: str, graph: Ref<EdGraph>) -> None`

### `editor_toolset.toolsets.curve_table.CurveTableTools` (9 tools, describe is about 2819 tokens)

- `add_key(curve_table: Ref<CurveTable>, key: {SimpleCurveKey}, row_name: str) -> bool`
- `add_row(curve_table: Ref<CurveTable>, default_value?: float, row_name: str) -> None`
- `create(asset_name: str, folder_path: str) -> Ref<CurveTable>`
- `get_keys(curve_table: Ref<CurveTable>, row_name: str) -> [{SimpleCurveKey}]`
- `import_file(asset_name: str, folder_path: str, interp_mode: enum(RCIM_Linear|RCIM_Constant|RCIM_Cubic|RCIM_None), source_file: str) -> [Ref<Object>]`
- `list_rows(curve_table: Ref<CurveTable>) -> [str]`
- `remove_row(curve_table: Ref<CurveTable>, row_name: str) -> None`
- `rename_row(curve_table: Ref<CurveTable>, new_row_name: str, row_name: str) -> None`
- `set_keys(curve_table: Ref<CurveTable>, keys: [{SimpleCurveKey}], row_name: str) -> bool`

### `editor_toolset.toolsets.data_asset.DataAssetTools` (1 tools, describe is about 427 tokens)

- `create(asset_name: str, asset_type: Ref<Class>, folder_path: str) -> Ref<DataAsset>`

### `editor_toolset.toolsets.data_table.DataTableTools` (10 tools, describe is about 2859 tokens)

- `add_rows(data_table: Ref<DataTable>, row_names: [str]) -> None`
- `create(asset_name: str, folder_path: str, schema: Ref<ScriptStruct>) -> Ref<DataTable>`
- `get_rows(data_table: Ref<DataTable>, row_names: [str]) -> str`
- `get_schema(data_table: Ref<DataTable>) -> str`
- `import_file(asset_name: str, folder_path: str, schema: Ref<ScriptStruct>, source_file: str) -> [Ref<Object>]`
- `list_rows(data_table: Ref<DataTable>) -> [str]`
- `remove_rows(data_table: Ref<DataTable>, row_names: [str]) -> None`
- `rename_rows(data_table: Ref<DataTable>, renames: {..}) -> None`
- `search_row_structs(struct_name?: str) -> [Ref<ScriptStruct>]`
- `set_rows(data_table: Ref<DataTable>, values: str) -> None`

### `editor_toolset.toolsets.string_table.StringTableTools` (8 tools, describe is about 2177 tokens)

- `create(asset_name: str, folder_path: str) -> Ref<StringTable>`
- `get_entry(key: str, string_table: Ref<StringTable>) -> str`
- `get_namespace(string_table: Ref<StringTable>) -> str`
- `get_table_id(string_table: Ref<StringTable>) -> str`
- `import_file(asset_name: str, folder_path: str, source_file: str) -> [Ref<Object>]`
- `list_keys(string_table: Ref<StringTable>) -> [str]`
- `remove_entry(key: str, string_table: Ref<StringTable>) -> None`
- `set_entry(key: str, string_table: Ref<StringTable>, value: str) -> None`

### `state_tree_toolset.toolsets.state_tree.StateTreeTools` (9 tools, describe is about 9079 tokens)

- `get_children(state: Ref<StateTreeState>) -> [Ref<StateTreeState>]`
- `get_editor_data(state_tree: Ref<StateTree>) -> Ref<StateTreeEditorData>`
- `get_enter_conditions(state: Ref<StateTreeState>) -> [{StateTreeEditorNode}]`
- `get_evaluators(state_tree: Ref<StateTree>) -> [{StateTreeEditorNode}]`
- `get_global_tasks(state_tree: Ref<StateTree>) -> [{StateTreeEditorNode}]`
- `get_node_description(node: {StateTreeEditorNode}, state_tree: Ref<StateTree>) -> str`
- `get_root_states(state_tree: Ref<StateTree>) -> [Ref<StateTreeState>]`
- `get_tasks(state: Ref<StateTreeState>) -> [{StateTreeEditorNode}]`
- `get_transitions(state: Ref<StateTreeState>) -> [{StateTreeTransition}]`
