# Niagara and Dataflow through Epic's Unreal MCP (5.8.3)

Lookup file for `scenario-unreal-vfx`. Read the table, copy the JSON. Every recipe below ran on
5.8.3 (2026-10-21) through `ue_mcp.Mcp` in `tests/code/unreal-vfx/live_mcp_recipes.py` (it copies
the arena project, saves a review level and one Effect Type with a headless Python job, starts its
own editor, runs R1 to R10, saves, stops; exit 0 only if all pass). It passed headless (49 s) and
offscreen (103 s). Nothing here needs `describe_toolset`: `NiagaraToolset_System` alone costs about
112,601 tokens to describe.

Toolset names (full): `NiagaraToolsets.NiagaraToolset_System`,
`NiagaraToolsets.NiagaraToolset_Component`, `NiagaraToolsets.NiagaraToolset_Assets`,
`NiagaraToolsets.NiagaraToolset_Blueprint`, `NiagaraToolsets.NiagaraToolset_Info`,
`DataflowAgent.DataflowAgentToolset`. Placement and saving use
`editor_toolset.toolsets.scene.SceneTools`, `...actor.ActorTools`, `...object.ObjectTools`,
`...asset.AssetTools`.

## 1. Intent to tool

| Intent                                          | Toolset and tool                                                                                          | Notes (run on 5.8.3 unless marked)                                                                                                                                                                                                      |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New system from a template                      | System `CreateNiagaraSystem`                                                                              | templates under `/Niagara/DefaultAssets/Templates/Systems/` (RadialBurst, DirectionalBurst, SimpleExplosion, AttributeReaderTrails, ...); emitter templates under `.../Templates/Emitters/` (Fountain, SimpleSpriteBurst, Minimal, ...) |
| What is in a system                             | System `GetSystemSummary`, `GetEmitterSummary`                                                            | small; `GetEmitterTopology` returned about 52 KB per emitter, use it only to find module and input names                                                                                                                                |
| Add an emitter                                  | System `AddEmitter`                                                                                       | `templateEmitter` is an emitter asset, not a system                                                                                                                                                                                     |
| Add a renderer                                  | System `AddRenderer`, then `SetRendererData`                                                              | returns `rendererIndex`; renderer classes `/Script/Niagara.Niagara<Kind>RendererProperties`                                                                                                                                             |
| Module input value                              | System `SetStackInputData` / `GetStackInputData` / `GetModuleInputValues`                                 | typed value, see section 3; hidden inputs are refused                                                                                                                                                                                   |
| User parameter                                  | System `AddUserVariables`, `GetUserVariables`                                                             | "Radius" and "User.Radius" both land as `User.Radius`                                                                                                                                                                                   |
| Bind an input to a parameter                    | System `SetStackInputData` with `NiagaraExt_StackInputData_Linked`                                        | linking to a name that does not exist silently creates that User parameter                                                                                                                                                              |
| Sim target, bounds, pool, Effect Type           | System `SetEmitterData`, `SetSystemData`                                                                  | `propertyValues` is a JSON string; a partial object merges                                                                                                                                                                              |
| Errors after an edit                            | System `GetSystemCompileState`, `GetStackIssues`, `ApplyStackIssueFix`                                    | in a headless editor too, never a commandlet; wait until `bIsCompiling` is false                                                                                                                                                        |
| Find a module or dynamic input                  | Assets `FindNiagaraScripts`, `GetNiagaraScriptDigest`; System `GetModuleSchemaFromAsset`                  | `name` is a substring ("Curl" finds CurlNoiseForce)                                                                                                                                                                                     |
| Enum names                                      | Info `UEnum_Info`                                                                                         | gives `NewEnumerator0`-style names and display names                                                                                                                                                                                    |
| Place in a level                                | SceneTools `add_to_scene_from_asset`; ActorTools `get_components`                                         | spawns a NiagaraActor with `NiagaraComponent0`                                                                                                                                                                                          |
| Set a parameter on a placed effect              | Component `SetVariable` / `GetVariable` / `GetUserVariables`                                              | wrong type or unknown name: accepted, adds a stray override                                                                                                                                                                             |
| Effect Type caps (cull distance, instance caps) | ObjectTools `get_properties` / `set_properties` on the Effect Type                                        | Python cannot reach these fields (R8, section 6)                                                                                                                                                                                        |
| Blueprint wrapper                               | Blueprint `ConstructNiagaraBPWrapperFromSystem`                                                           | ran once in a probe, not in the recipe file                                                                                                                                                                                             |
| Geometry Collection with a Dataflow             | Dataflow `ListDataflowTemplatesForAssetClass`, `CreateDataflowCompatibleAssetFromTemplate`, `SetVariable` | outputs are JSON text: parse them                                                                                                                                                                                                       |
| Save                                            | AssetTools `save_assets`                                                                                  | `asset_paths` are package paths, no `.Name` suffix                                                                                                                                                                                      |

Not covered by the toolset (Epic's in-editor NiagaraFundamentalsSkill says so; not tested here):
Lightweight Emitters and Niagara Data Channels. Use templates, the GUI (`gui-paths.md`) or say so.

## 2. Signature lines

Generated with
`python3 <skills>/scenario-unreal-expert/scripts/gen_toolset_map.py tests/arena/mcp-catalog-5.8.3 Niagara Dataflow`.
`Ref<X>` is `{"refPath": "/Path/Asset.Asset"}`; `?` marks an optional argument.

### `DataflowAgent.DataflowAgentToolset` (22 tools, describe is about 6089 tokens)

- `AddCommentBox(color?: {LinearColor}, comment?: str, graph: Ref<Dataflow>, nodes: [Ref<DataflowEdNode>]) -> str`
- `AddNode(graph: Ref<Dataflow>, jsonParams: str, nodeName: str, typeName: str, x?: int, y?: int) -> Ref<DataflowEdNode>`
- `AddVariable(graph: Ref<Dataflow>, name: str, type: str) -> bool`
- `AssignDataflowTemplate(asset: Ref<Object>, templateId: str) -> bool`
- `ConnectNodePins(fromNode: Ref<DataflowEdNode>, fromPin: str, toNode: Ref<DataflowEdNode>, toPin: str) -> bool`
- `CreateDataflowCompatibleAsset(className: str, name: str, path?: str) -> str`
- `CreateDataflowCompatibleAssetFromTemplate(className: str, name: str, path: str, templateId: str) -> str`
- `CreateGraph(name: str, path: str) -> str`
- `DisconnectNodePins(fromNode: Ref<DataflowEdNode>, fromPin: str, toNode: Ref<DataflowEdNode>, toPin: str) -> None`
- `GetGraphStructure(graph: Ref<Dataflow>) -> str`
- `GetNodeInfo(node: Ref<DataflowEdNode>) -> str`
- `GetNodeTypeSchema(typeName: str) -> str`
- `ListDataflowCompatibleAssetTypes() -> str`
- `ListDataflowTemplatesForAssetClass(bIncludeBlank?: bool, className: str) -> str`
- `ListNodeTypes(bCommonOnly?: bool) -> str`
- `ListVariables(graph: Ref<Dataflow>) -> str`
- `RemoveCommentBox(commentId: str, graph: Ref<Dataflow>) -> None`
- `RemoveNode(graph: Ref<Dataflow>, node: Ref<DataflowEdNode>) -> None`
- `RemoveVariable(graph: Ref<Dataflow>, name: str) -> None`
- `RepositionNode(node: Ref<DataflowEdNode>, x: int, y: int) -> None`
- `SetVariable(graph: Ref<Dataflow>, name: str, value: str) -> bool`
- `UpdateNode(jsonParams: str, node: Ref<DataflowEdNode>) -> None`

### `NiagaraToolsets.NiagaraToolset_Assets` (3 tools, describe is about 2586 tokens)

- `FindNiagaraScripts(bIncludeDeprecated: bool, bRecursive: bool, folderPath: str, moduleUsageBitmask: int, name: str, usages: [enum(Function|Module|DynamicInput|+10)], visibilities: [enum(Invalid|Unexposed|Library|Hidden)]) -> [{AssetData}]`
- `GetAssetDiscoveryInfo() -> [{NiagaraToolsetAssetDiscoveryGroup}]`
- `GetNiagaraScriptDigest(objectPath: str) -> {NiagaraExt_ScriptDigest}`

### `NiagaraToolsets.NiagaraToolset_Blueprint` (2 tools, describe is about 1045 tokens)

- `ConstructNiagaraBPWrapperFromComponent(component: Ref<NiagaraComponent>, newAssetPath: str, parentClass: Ref<Object>) -> Ref<Blueprint>`
- `ConstructNiagaraBPWrapperFromSystem(newAssetPath: str, parentClass: Ref<Object>, system: Ref<NiagaraSystem>) -> Ref<Blueprint>`

### `NiagaraToolsets.NiagaraToolset_Component` (4 tools, describe is about 11416 tokens)

- `GetUserVariables(component: Ref<NiagaraComponent>) -> [{NiagaraExt_VariableInst}]`
- `GetVariable(component: Ref<NiagaraComponent>, var: {NiagaraExt_Variable}) -> {NiagaraExt_VariableInst}`
- `SetSystem(bResetExistingOverrideParameters: bool, niagaraComponent: Ref<NiagaraComponent>, system: Ref<NiagaraSystem>) -> None`
- `SetVariable(component: Ref<NiagaraComponent>, variable: {NiagaraExt_VariableInst}) -> None`

### `NiagaraToolsets.NiagaraToolset_Info` (1 tools, describe is about 288 tokens)

- `UEnum_Info(enum: Ref<Enum>) -> str`

### `NiagaraToolsets.NiagaraToolset_System` (46 tools, describe is about 112601 tokens)

- `AddEmitter(emitterName: str, system: Ref<NiagaraSystem>, templateEmitter: Ref<NiagaraEmitter>) -> {NiagaraExt_EmitterTopology}`
- `AddModule(moduleAsset: Ref<NiagaraScript>, moduleLocationRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_ModuleTopology}`
- `AddRenderer(newRendererLocation: {NiagaraExt_StackItemReference}, rendererClass: Ref<NiagaraRendererProperties>) -> {NiagaraExt_RendererRef}`
- `AddSetParameterEntry(entry: {NiagaraExt_SetParameterEntry}, moduleRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_ModuleTopology}`
- `AddSetParametersModule(moduleLocationRef: {NiagaraExt_StackItemReference}, parameters: [{NiagaraExt_SetParameterEntry}]) -> {NiagaraExt_ModuleTopology}`
- `AddUserVariables(system: Ref<NiagaraSystem>, variablesToAdd: [{NiagaraExt_UserVariable}]) -> None`
- `ApplyStackIssueFix(fixId: str, issueId: str, system: Ref<NiagaraSystem>) -> {NiagaraToolset_ApplyStackIssueFixResult}`
- `CreateNiagaraSystem(assetName: str, assetPath: str, templateSystem: Ref<NiagaraSystem>) -> Ref<NiagaraSystem>`
- `GetAvailableDynamicInputs(type: {ToolsetNiagaraTypeDefinition}) -> [Ref<NiagaraScript>]`
- `GetDataInterfaceSchema(dataInterfaceClass: Ref<NiagaraDataInterface>) -> {NiagaraExt_DataInterfaceSchema}`
- `GetDynamicInputChain(stackInputRef: {NiagaraExt_StackItemReference}) -> {NiagaraToolsetInstancedValue}`
- `GetDynamicInputSchema(dynamicInputReference: {NiagaraExt_StackItemReference}) -> {NiagaraExt_DynamicInputSchema}`
- `GetDynamicInputSchemaFromAsset(dynamicInputAsset: Ref<NiagaraScript>) -> {NiagaraExt_DynamicInputSchema}`
- `GetEmitterData(emitterRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_EmitterData}`
- `GetEmitterInputValues(emitterRef: {NiagaraExt_StackItemReference}) -> [{NiagaraExt_ModuleInputValues}]`
- `GetEmitterSchema() -> {NiagaraExt_EmitterSchema}`
- `GetEmitterSummary(emitterRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_EmitterSummary}`
- `GetEmitterTopology(emitterRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_EmitterTopology}`
- `GetModuleInputValues(moduleRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_ModuleInputValues}`
- `GetModuleSchema(moduleReference: {NiagaraExt_StackItemReference}) -> {NiagaraExt_ModuleSchema}`
- `GetModuleSchemaFromAsset(moduleAsset: Ref<NiagaraScript>) -> {NiagaraExt_ModuleSchema}`
- `GetModuleTopology(moduleRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_ModuleTopology}`
- `GetRendererData(rendererRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_RendererData}`
- `GetRendererSchema(rendererClass: Ref<NiagaraRendererProperties>) -> {NiagaraExt_RendererSchema}`
- `GetScriptStackInputValues(scriptRef: {NiagaraExt_StackItemReference}) -> [{NiagaraExt_ModuleInputValues}]`
- `GetScriptStackTopology(scriptRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_ScriptStackTopology}`
- `GetStackInputData(stackInputRef: {NiagaraExt_StackItemReference}) -> {NiagaraToolsetInstancedValue}`
- `GetStackInputSchema(inputReference: {NiagaraExt_StackItemReference}) -> {NiagaraExt_StackInputSchema}`
- `GetStackInputTopology(stackInputRef: {NiagaraExt_StackItemReference}) -> {NiagaraExt_StackInputTopology}`
- `GetStackIssues(system: Ref<NiagaraSystem>) -> {NiagaraExt_StackIssues}`
- `GetSystemCompileState(system: Ref<NiagaraSystem>) -> {NiagaraExt_SystemCompileState}`
- `GetSystemData(system: Ref<NiagaraSystem>) -> {NiagaraExt_SystemData}`
- `GetSystemDependencies(system: Ref<NiagaraSystem>) -> {NiagaraExt_SystemDependencies}`
- `GetSystemSchema() -> {NiagaraExt_SystemSchema}`
- `GetSystemSummary(system: Ref<NiagaraSystem>) -> {NiagaraExt_SystemSummary}`
- `GetUserVariables(system: Ref<NiagaraSystem>) -> {NiagaraExt_UserVariables}`
- `RemoveEmitter(emitterToRemove: {NiagaraExt_StackItemReference}) -> None`
- `RemoveModule(moduleToRemove: {NiagaraExt_StackItemReference}) -> None`
- `RemoveRenderer(rendererToRemove: {NiagaraExt_StackItemReference}) -> None`
- `RemoveSetParameterEntry(moduleRef: {NiagaraExt_StackItemReference}, parameterName: str) -> None`
- `RemoveUserVariables(system: Ref<NiagaraSystem>, variablesToRemove: [{NiagaraExt_Variable}]) -> None`
- `SetEmitterData(emitter: {NiagaraExt_StackItemReference}, emitterData: {NiagaraExt_EmitterData}) -> None`
- `SetModuleEnabled(bEnabled: bool, moduleRef: {NiagaraExt_StackItemReference}) -> None`
- `SetRendererData(renderer: {NiagaraExt_StackItemReference}, rendererData: {NiagaraExt_RendererData}) -> None`
- `SetStackInputData(inputData: {NiagaraToolsetInstancedValue}, stackInputRef: {NiagaraExt_StackItemReference}) -> {NiagaraToolsetInstancedValue}`
- `SetSystemData(system: Ref<NiagaraSystem>, systemData: {NiagaraExt_SystemData}) -> None`

Struct shapes used above:

- `NiagaraExt_StackItemReference {system: Ref, emitterName, scriptName, moduleName, inputNameStack: [str], rendererIndex: int}`:
  send only the keys the call needs. Script names: `SystemSpawnScript`, `SystemUpdateScript`,
  `EmitterSpawnScript`, `EmitterUpdateScript`, `ParticleSpawnScript`, `ParticleUpdateScript`.
- `NiagaraToolsetInstancedValue {struct: Ref<ScriptStruct>, value: {...}}`: the struct names the
  value type (section 3).
- `ToolsetNiagaraTypeDefinition {classStructOrEnum: Ref}`, for example
  `{"classStructOrEnum": {"refPath": "/Script/Niagara.NiagaraFloat"}}`.
- `NiagaraExt_UserVariable {name, type, description, defaultValue: InstancedValue}`;
  `NiagaraExt_VariableInst {name, type, value}`.
- `NiagaraExt_StackIssues {issues: [{issueId, severity: Error|Warning|Info, shortDescription, longDescription, fixes: [{fixId, description, style}], location}], numErrors, numWarnings, numInfos}`.
- `NiagaraExt_SystemCompileState {aggregateStatus: Unknown|Dirty|Error|UpToDate|..., bHasErrors, bHasWarnings, bIsCompiling, bIsStale, scripts: [{scriptName, emitterName, lastCompileStatus, errorSummary, compileEvents: [{severity, message}]}]}`.

## 3. Value shapes for SetStackInputData (all run on 5.8.3)

```json
{"struct": {"refPath": "/Script/Niagara.NiagaraInt32"}, "value": {"value": 40}}
{"struct": {"refPath": "/Script/Niagara.NiagaraFloat"}, "value": {"value": 0.6}}
{"struct": {"refPath": "/Script/Niagara.NiagaraBool"}, "value": {"value": 1}}
{"struct": {"refPath": "/Script/CoreUObject.LinearColor"}, "value": {"r": 4.0, "g": 1.2, "b": 0.2, "a": 1.0}}
{"struct": {"refPath": "/Script/NiagaraEditor.NiagaraExt_StackInputData_Enum"},
 "value": {"enum": {"refPath": "/Niagara/Enums/ENiagara_LifetimeMode.ENiagara_LifetimeMode"}, "enumName": "ENiagara_LifetimeMode::NewEnumerator0"}}
{"struct": {"refPath": "/Script/NiagaraEditor.NiagaraExt_StackInputData_Linked"},
 "value": {"linkedVariable": {"name": "User.Radius", "type": {"classStructOrEnum": {"refPath": "/Script/Niagara.NiagaraFloat"}}}}}
{"struct": {"refPath": "/Script/NiagaraEditor.NiagaraExt_StackInputData_HlslExpression"}, "value": {"hlslExpression": "Engine.Owner.Velocity.z * 0.01"}}
```

The `NiagaraBool` line and the valid HLSL expression were not run (R9 ran a broken one); the others
were. Read the current value first (`GetStackInputData`) when unsure: it returns the same shape,
including the enum asset for an enum input. `UEnum_Info` on that enum lists
`NewEnumerator0 = Direct Set`, `NewEnumerator1 = Random` for the lifetime mode.

## 4. Recipes (run live, `live_mcp_recipes.py`)

Shorthand: `SYS = {"refPath": "/Game/VFX/Recipes/NS_Recipe.NS_Recipe"}`; `ref(...)` is a
`NiagaraExt_StackItemReference` with `system: SYS` plus the keys shown.

**R1. System from a template, then its summary** (2 calls).

```json
NiagaraToolset_System.CreateNiagaraSystem {"assetName": "NS_Recipe", "assetPath": "/Game/VFX/Recipes",
  "templateSystem": {"refPath": "/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst"}}
NiagaraToolset_System.GetSystemSummary {"system": SYS}
```

Returns the new `refPath`; the summary lists emitters RibbonTrailFollower, OmnidirectionalBurst,
Ribbon_Trail_Leader, all CPUSim.

**R2. Add an emitter and a Light renderer; GPU breaks it; fix from the stack** (11 calls).

```json
AddEmitter {"system": SYS, "emitterName": "Sparks", "templateEmitter": {"refPath": "/Niagara/DefaultAssets/Templates/Emitters/Fountain.Fountain"}}
AddRenderer {"newRendererLocation": {"system": SYS, "emitterName": "Sparks"}, "rendererClass": {"refPath": "/Script/Niagara.NiagaraLightRendererProperties"}}
SetRendererData {"renderer": {"system": SYS, "emitterName": "Sparks", "rendererIndex": 1}, "rendererData": {"propertyValues": "{\"RadiusScale\": 0.5}"}}
SetEmitterData {"emitter": {"system": SYS, "emitterName": "Sparks"}, "emitterData": {"propertyValues": "{\"SimTarget\": \"GPUComputeSim\"}"}}
GetSystemCompileState {"system": SYS}            (repeat until bIsCompiling is false)
GetStackIssues {"system": SYS}
ApplyStackIssueFix {"system": SYS, "issueId": "<issues[i].issueId>", "fixId": "<issues[i].fixes[0].fixId>"}
```

The error is "Renderer incompatible with chosen Sim Target in Emitter Properties." and its fix
"Change Sim Target to CPUSim"; after it, `postFixIssues.numErrors` is 0 and `GetEmitterSummary` says
CPUSim.

**R3. Module inputs: int, enum, then the float it unhides, color** (9 calls).

```json
SetStackInputData {"stackInputRef": ref(emitterName="OmnidirectionalBurst", scriptName="EmitterUpdateScript", moduleName="SpawnBurst_Instantaneous", inputNameStack=["Spawn Count"]), "inputData": <NiagaraInt32 40>}
SetStackInputData {"stackInputRef": ref("Sparks", "ParticleSpawnScript", "InitializeParticle", ["Lifetime Mode"]), "inputData": <Enum NewEnumerator0>}
SetStackInputData {"stackInputRef": ref("Sparks", "ParticleSpawnScript", "InitializeParticle", ["Lifetime"]), "inputData": <NiagaraFloat 0.6>}
SetStackInputData {"stackInputRef": ref("Sparks", "ParticleSpawnScript", "InitializeParticle", ["Color"]), "inputData": <LinearColor>}
GetModuleInputValues {"moduleRef": ref("Sparks", "ParticleSpawnScript", "InitializeParticle")}
```

Setting `Lifetime` before the mode is refused: "Refusing to set input 'Lifetime': input is hidden by
static-switch / conditional logic ...". An Int32 value on that float input is refused: "Type
mismatch for input 'Lifetime': expected 'NiagaraFloat' but got 'NiagaraInt32'".

**R4. User parameters and a linked input** (4 calls).

```json
AddUserVariables {"system": SYS, "variablesToAdd": [
  {"name": "Radius", "type": {"classStructOrEnum": {"refPath": "/Script/Niagara.NiagaraFloat"}}, "description": "damage radius, cm",
   "defaultValue": {"struct": {"refPath": "/Script/Niagara.NiagaraFloat"}, "value": {"value": 300.0}}},
  {"name": "Tint", "type": {"classStructOrEnum": {"refPath": "/Script/CoreUObject.LinearColor"}}, "description": "",
   "defaultValue": {"struct": {"refPath": "/Script/CoreUObject.LinearColor"}, "value": {"r": 1, "g": 0.4, "b": 0.1, "a": 1}}}]}
SetStackInputData {"stackInputRef": ref("OmnidirectionalBurst", "ParticleSpawnScript", "ShapeLocation", ["Sphere Radius"]), "inputData": <Linked User.Radius>}
```

`GetUserVariables` then lists `User.Radius`, `User.Tint`.

**R5. System properties in one merge** (3 calls).

```json
SetSystemData {"system": SYS, "systemData": {"propertyValues": "{\"bFixedBounds\": true, \"FixedBounds\": {\"min\": {\"x\": -400, \"y\": -400, \"z\": -50}, \"max\": {\"x\": 400, \"y\": 400, \"z\": 400}, \"isValid\": true}, \"MaxPoolSize\": 8, \"bRequireCurrentFrameData\": false, \"EffectType\": \"/Game/VFX/EffectTypes/NET_OneShotCritical.NET_OneShotCritical\"}"}}
GetSystemData {"system": SYS}
AssetTools.save_assets {"asset_paths": ["/Game/VFX/Recipes/NS_Recipe"]}
```

`GetSystemData.propertyValues` is JSON text; defaults seen on a new system: MaxPoolSize 32,
PoolPrimeSize 0, WarmupTime 0, bRequireCurrentFrameData true, EffectType None.

**R6. Place it, drive it from the level, save the level** (8 calls).

```json
SceneTools.load_level {"level_path": "/Game/Maps/L_VFXReview"}
SceneTools.add_to_scene_from_asset {"asset_path": "/Game/VFX/Recipes/NS_Recipe", "name": "FX_Recipe",
  "xform": {"location": {"x": 0, "y": 0, "z": 100}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0}, "scale": {"x": 1, "y": 1, "z": 1}}}
ActorTools.get_components {"actor": <actor ref>}
NiagaraToolset_Component.SetVariable {"component": <...NiagaraComponent0>, "variable": {"name": "User.Radius",
  "type": {"classStructOrEnum": {"refPath": "/Script/Niagara.NiagaraFloat"}}, "value": {"struct": {"refPath": "/Script/Niagara.NiagaraFloat"}, "value": {"value": 450.0}}}}
NiagaraToolset_Component.GetVariable {"component": <...>, "var": {"name": "User.Radius", "type": {...NiagaraFloat}}}
AssetTools.save_assets {"asset_paths": ["/Game/Maps/L_VFXReview"]}
```

A typo (`Radiuss`) is accepted with no error and shows up in the component's `GetUserVariables` next
to `Radius` and `Tint`: read the list back after setting.

**R7. Geometry Collection from a Dataflow template** (7 calls).

```json
DataflowAgentToolset.ListDataflowTemplatesForAssetClass {"className": "GeometryCollection", "bIncludeBlank": true}
DataflowAgentToolset.CreateDataflowCompatibleAssetFromTemplate {"className": "GeometryCollection", "name": "GC_Recipe", "path": "/Game/VFX/Recipes",
  "templateId": "/GeometryCollectionPlugin/DataflowTemplates/DF_GC_Template_StaticMesh.DF_GC_Template_StaticMesh"}
DataflowAgentToolset.GetGraphStructure {"graph": {"refPath": "/Game/VFX/Recipes/GC_Recipe.GC_Recipe:EmbeddedDataflow"}}
DataflowAgentToolset.SetVariable {"graph": {...same...}, "name": "SourceStaticMesh", "value": "/Engine/BasicShapes/Cylinder.Cylinder"}
```

Templates for GeometryCollection: Blank, DF_GC_Template_Source, DF_GC_Template_StaticMesh. The
StaticMesh template's nodes: GetDataflowVariable, StaticMeshToCollection_v2, UniformFracture,
GeometryCollectionTerminal_v2. The new GC has Nanite off, the user-defined damage model and
thresholds [500000, 50000, 5000]: run `ue_vfx.harden_gc` or set them before shipping.

**R8. Effect Type caps** (4 calls).

```json
ObjectTools.set_properties {"instance": {"refPath": "/Game/VFX/EffectTypes/NET_OneShotCritical.NET_OneShotCritical"},
  "values": "{\"SystemScalabilitySettings\": {\"settings\": [{\"platforms\": {\"qualityLevelMask\": -1}, \"bCullByDistance\": true, \"maxDistance\": 5000.0, \"bCullMaxInstanceCount\": true, \"maxInstances\": 30, \"bCullPerSystemMaxInstanceCount\": true, \"maxSystemInstances\": 15}]}}"}
ObjectTools.get_properties {"instance": {...}, "properties": ["UpdateFrequency", "CullReaction", "SystemScalabilitySettings"]}
```

A new Effect Type had `settings: []`; after the write the entry also carries the defaults
(cullProxyMode None, maxSystemProxies 32, visibility culling off, budget scaling off).

**R9. Real compile errors** (6 calls). Put a broken expression on an input
(`{"hlslExpression": "this_is_not_hlsl(("}`), wait for `bIsCompiling` false, read
`GetSystemCompileState`: `aggregateStatus` "Error", `bHasErrors` true, the message starts "The
Vector VM compile failed". Seen headless and offscreen. Restore the input, wait, `UpToDate` again.

**R10. CVar names** (`EditorToolset.EditorAppToolset.SearchCVars {"name": "fx.Budget"}`, substring
search, JSON text out). Present on 5.8.3: `r.HeterogeneousVolumes` (1),
`r.HeterogeneousVolumes.Allowed` (not `.Allow`), `fx.Budget.Enabled` (0),
`fx.Budget.EnabledInEditor` (0), `fx.Budget.GameThread` (2 ms), `fx.Budget.AdjustedUsageDecayRate`
(0.1), `fx.Niagara.QualityLevel` (3), `t.OverrideFPS` (0). `fx.Niagara.Debug.Hud` and
`fx.Niagara.Debug.PlaybackMode` are console commands (their names are in the 5.8.3 Niagara module),
so SearchCVars does not list them.

## 5. Traps (run on 5.8.3)

- `GetStackIssues` fails with "Cannot collect stack issues while a compile is in flight" right after
  an edit: poll `GetSystemCompileState` until `bIsCompiling` is false. The issues come back without
  opening the Niagara editor (Epic's NiagaraFundamentalsSkill says opening it is needed; on 5.8.3
  headless it was not).
- Compile state right after an edit can still say UpToDate: wait as above before trusting it.
  UpToDate does not prove the edit compiled: a broken HLSL expression written right after switching
  the controlling enum left the system UpToDate for 120 s with no compile, and it saved and reloaded
  UpToDate; writing a plain value first, waiting, then the expression gave Error within 2.4 s (seen
  once each, offscreen, `live_niagara_disk_facts.py`). Check that `bIsCompiling` went true after the
  edit, or that the change shows in `GetModuleInputValues`, before saving.
- A system saved with a compile error reloads with it: in a new editor session the loaded asset
  answered `aggregateStatus` Error, `bHasErrors` true at once. On loaded systems
  `GetSystemCompileState` and `GetStackIssues` answered in 0.1 to 0.8 s, offscreen and headless (no
  hang seen).
- Hidden inputs are refused, not ignored: switch the controlling enum or bool first.
- `SetStackInputData` with a Linked value to an unknown `User.X` creates `User.X` silently: check
  `GetUserVariables` against your contract.
- Component `SetVariable` with the wrong type or name returns success and adds a stray override the
  effect never reads (Python's `set_variable_*` does the same).
- `GetEmitterTopology` is about 52 KB per emitter. Prefer `GetEmitterSummary`,
  `GetModuleInputValues`, `GetStackInputTopology`.
- Engine template folders are invisible to a fresh commandlet's asset registry until scanned
  (`ue_vfx.scan_paths`); in an editor they list normally.
- `EditorAppToolset.CaptureViewport` needs `captureTransform` and `annotations` although the catalog
  marks them optional, and an offscreen editor's viewport was 424 x 40. For frames of an effect use
  the latent Python capture (`live_capture_series.py`: CameraActor plus `take_high_res_screenshot`),
  not the MCP capture.

## 6. When Python or a commandlet is the better channel

- Creating a level or an Effect Type: no MCP tool does it (no Niagara tool creates anything but a
  Niagara system; `AssetTools.duplicate` of an engine map gave a level that would not save);
  `job_review_level.py`, `ue_vfx.create_effect_type` (Effect Type caps then via R8).
- Batches over many systems (assign one Effect Type to 40 systems, audit every system): one headless
  `ue_run` job. The same Niagara toolset calls are reachable from Python:
  `ue_vfx.niagara_tool("GetSystemData", system)` calls
  `unreal.get_default_object(unreal.NiagaraToolset_System).call_method(...)` (CreateNiagaraSystem,
  GetSystemSummary and GetSystemData ran this way in a commandlet). So "Python cannot author
  Niagara" (v0.1) no longer holds on 5.8. Plain editor Python, without the toolset, cannot read
  stack contents: `NiagaraSystem` exposes no emitter handles or scripts, and
  `NiagaraFunctionLibrary.get_all_emitters` returns only name, enabled, lightweight and renderer
  materials and meshes (`get_all_user_parameters` for User parameters). Modules, inputs and renderer
  settings come only from the toolset (run on 5.8.3, `job_niagara_python_reach.py`).
- Toolset edits in a commandlet **[not yet run]**: never call `GetStackIssues` there, and never
  trust its UpToDate. Reopen the system in an editor, set one input again so `bIsCompiling` goes
  true, wait for it to clear, then check that particles move between two `capture_ages` frames.
- Deterministic frames at fixed ages: latent Python job (`capture_ages`), not MCP.
- Geometry Collection hardening (Nanite, removal, damage model): `ue_vfx.harden_gc` in a commandlet
  (`job_gc_harden.py`, run on 5.8.3).
- Four or more toolset calls in a row in a live session: one
  `ProgrammaticToolset.execute_tool_script` call (section 7), not one MCP call per step.

## 7. Batched recipes: one `execute_tool_script` call each

Four or more toolset calls in a row go through one
`editor_toolset.toolsets.programmatic.ProgrammaticToolset.execute_tool_script {"script": "<text>"}`
call: the script defines `run()`, calls `execute_tool("<toolset>.<Tool>", json_string)` (full dotted
name; it returns a dict with `returnValue`), and returns a dict, which comes back as JSON text in
`returnValue`. Imports are limited to json, math, re, time, datetime, copy. `time.sleep` inside the
script lets the editor keep compiling between calls. A refused call inside the script (a hidden
input, a wrong type) failed the whole `execute_tool_script` call on 5.8.3 even inside
`try`/`except`: the Niagara tool reports through the script log, not as a Python exception. So a
script holds calls that should succeed; do the order right (switch first, then the input) and probe
doubtful calls one at a time. The scripts below are the same recipes as section 4, on their own
assets; each ran live as written (`live_mcp_recipes.py` extracts and runs every block that starts
with `# script:`). Run N1 first: the others edit its system. Paths are the test project's: change
them for yours.

```python
# script: N1  (R1 + R2) system from a template, emitter, Light renderer, GPU error fixed
import json, time
NS = "NiagaraToolsets.NiagaraToolset_System."
SYS = {"refPath": "/Game/VFX/Batch/NS_Batch.NS_Batch"}

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def em(name, **extra):
    d = {"system": SYS, "emitterName": name}
    d.update(extra)
    return d

def wait_issues(timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not t(NS + "GetSystemCompileState", {"system": SYS})["bIsCompiling"]:
            return t(NS + "GetStackIssues", {"system": SYS})   # never while compiling: it would fail
        time.sleep(1.0)
    raise RuntimeError("still compiling")

def run():
    t(NS + "CreateNiagaraSystem", {"assetName": "NS_Batch", "assetPath": "/Game/VFX/Batch",
        "templateSystem": {"refPath": "/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst"}})
    t(NS + "AddEmitter", {"system": SYS, "emitterName": "Sparks",
        "templateEmitter": {"refPath": "/Niagara/DefaultAssets/Templates/Emitters/Fountain.Fountain"}})
    idx = t(NS + "AddRenderer", {"newRendererLocation": em("Sparks"),
        "rendererClass": {"refPath": "/Script/Niagara.NiagaraLightRendererProperties"}})["rendererIndex"]
    t(NS + "SetRendererData", {"renderer": em("Sparks", rendererIndex=idx),
        "rendererData": {"propertyValues": json.dumps({"RadiusScale": 0.5})}})
    t(NS + "SetEmitterData", {"emitter": em("Sparks"),
        "emitterData": {"propertyValues": json.dumps({"SimTarget": "GPUComputeSim"})}})
    errs = [i for i in wait_issues()["issues"] if i["severity"] == "Error" and i["fixes"]]
    fix = t(NS + "ApplyStackIssueFix", {"system": SYS, "issueId": errs[0]["issueId"],
        "fixId": errs[0]["fixes"][0]["fixId"]})
    sim = t(NS + "GetEmitterSummary", {"emitterRef": em("Sparks")})["simTarget"]
    names = [e["emitterName"] for e in t(NS + "GetSystemSummary", {"system": SYS})["emitters"]]
    return {"ok": bool(fix["applyResult"]["bApplied"]) and sim == "CPUSim", "emitters": names,
            "error": errs[0]["shortDescription"], "sim": sim}
```

```python
# script: N3  (R3 + R4) stack inputs, a hidden input switched on, User parameters and a link
import json
NS = "NiagaraToolsets.NiagaraToolset_System."
SYS = {"refPath": "/Game/VFX/Batch/NS_Batch.NS_Batch"}
F32 = {"refPath": "/Script/Niagara.NiagaraFloat"}
T_FLOAT = {"classStructOrEnum": F32}

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def inp(emitter, script, module, *names):
    return {"system": SYS, "emitterName": emitter, "scriptName": script, "moduleName": module,
            "inputNameStack": list(names)}

def put(ref, struct, value):
    return t(NS + "SetStackInputData", {"stackInputRef": ref,
        "inputData": {"struct": {"refPath": struct}, "value": value}})

def run():
    put(inp("OmnidirectionalBurst", "EmitterUpdateScript", "SpawnBurst_Instantaneous", "Spawn Count"),
        "/Script/Niagara.NiagaraInt32", {"value": 40})
    life = inp("Sparks", "ParticleSpawnScript", "InitializeParticle", "Lifetime")
    mode = inp("Sparks", "ParticleSpawnScript", "InitializeParticle", "Lifetime Mode")
    enum = t(NS + "GetStackInputData", {"stackInputRef": mode})["value"]["enum"]
    put(mode, "/Script/NiagaraEditor.NiagaraExt_StackInputData_Enum",
        {"enum": enum, "enumName": "ENiagara_LifetimeMode::NewEnumerator0"})     # Direct Set
    put(life, F32["refPath"], {"value": 0.6})      # hidden (refused) until the switch above
    put(inp("Sparks", "ParticleSpawnScript", "InitializeParticle", "Color"),
        "/Script/CoreUObject.LinearColor", {"r": 4.0, "g": 1.2, "b": 0.2, "a": 1.0})
    t(NS + "AddUserVariables", {"system": SYS, "variablesToAdd": [
        {"name": "Radius", "type": T_FLOAT, "description": "damage radius, cm",
         "defaultValue": {"struct": F32, "value": {"value": 300.0}}}]})
    radius = inp("OmnidirectionalBurst", "ParticleSpawnScript", "ShapeLocation", "Sphere Radius")
    put(radius, "/Script/NiagaraEditor.NiagaraExt_StackInputData_Linked",
        {"linkedVariable": {"name": "User.Radius", "type": T_FLOAT}})
    vals = {i["name"]: i["value"] for i in t(NS + "GetModuleInputValues", {"moduleRef": {
        "system": SYS, "emitterName": "Sparks", "scriptName": "ParticleSpawnScript",
        "moduleName": "InitializeParticle"}})["inputs"]}
    link = t(NS + "GetStackInputData", {"stackInputRef": radius})["value"]["linkedVariable"]["name"]
    users = [u["name"] for u in t(NS + "GetUserVariables", {"system": SYS})["userVariables"]]
    ok = (abs(vals["Lifetime"]["value"]["value"] - 0.6) < 1e-5
          and link == "User.Radius" and "User.Radius" in users)
    return {"ok": ok, "link": link, "users": users}
```

```python
# script: N5  (R5 + R8) system properties, Effect Type caps, save
import json
NS = "NiagaraToolsets.NiagaraToolset_System."
OT = "editor_toolset.toolsets.object.ObjectTools."
SYS = {"refPath": "/Game/VFX/Batch/NS_Batch.NS_Batch"}
EFT = {"refPath": "/Game/VFX/EffectTypes/NET_OneShotCritical.NET_OneShotCritical"}

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def run():
    t(NS + "SetSystemData", {"system": SYS, "systemData": {"propertyValues": json.dumps({
        "bFixedBounds": True,
        "FixedBounds": {"min": {"x": -400, "y": -400, "z": -50}, "max": {"x": 400, "y": 400, "z": 400},
                        "isValid": True},
        "MaxPoolSize": 8, "EffectType": EFT["refPath"]})}})
    d = json.loads(t(NS + "GetSystemData", {"system": SYS})["propertyValues"])
    t(OT + "set_properties", {"instance": EFT, "values": json.dumps({"SystemScalabilitySettings": {
        "settings": [{"platforms": {"qualityLevelMask": -1}, "bCullByDistance": True, "maxDistance": 5000.0,
                      "bCullMaxInstanceCount": True, "maxInstances": 30,
                      "bCullPerSystemMaxInstanceCount": True, "maxSystemInstances": 15}]}})})
    caps = json.loads(t(OT + "get_properties", {"instance": EFT,
        "properties": ["SystemScalabilitySettings"]}))["SystemScalabilitySettings"]["settings"][0]
    t("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [
        "/Game/VFX/Batch/NS_Batch", "/Game/VFX/EffectTypes/NET_OneShotCritical"]})
    ok = d["MaxPoolSize"] == 8 and "NET_OneShotCritical" in str(d["EffectType"]) and caps["maxSystemInstances"] == 15
    return {"ok": ok, "pool": d["MaxPoolSize"], "effect_type": str(d["EffectType"]), "caps": caps}
```

```python
# script: N6  (R6) place in a saved level, set and read component variables, save the level
import json
NC = "NiagaraToolsets.NiagaraToolset_Component."
T_FLOAT = {"classStructOrEnum": {"refPath": "/Script/Niagara.NiagaraFloat"}}

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def run():
    t("editor_toolset.toolsets.scene.SceneTools.load_level", {"level_path": "/Game/Maps/L_VFXReview"})
    actor = t("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_asset", {
        "asset_path": "/Game/VFX/Batch/NS_Batch", "name": "FX_Batch",
        "xform": {"location": {"x": 300, "y": 0, "z": 100}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
                  "scale": {"x": 1, "y": 1, "z": 1}}})
    comps = t("editor_toolset.toolsets.actor.ActorTools.get_components", {"actor": actor})
    comp = [c for c in comps if "NiagaraComponent" in c["refPath"]][0]
    t(NC + "SetVariable", {"component": comp, "variable": {"name": "User.Radius", "type": T_FLOAT,
        "value": {"struct": {"refPath": "/Script/Niagara.NiagaraFloat"}, "value": {"value": 450.0}}}})
    got = t(NC + "GetVariable", {"component": comp, "var": {"name": "User.Radius", "type": T_FLOAT}})
    saved = t("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": ["/Game/Maps/L_VFXReview"]})
    radius = got["value"]["value"]["value"]
    return {"ok": abs(radius - 450.0) < 1e-4 and saved is True, "radius": radius, "component": comp["refPath"]}
```

```python
# script: N7  (R7) Geometry Collection from the StaticMesh Dataflow template
import json
DF = "DataflowAgent.DataflowAgentToolset."

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def run():
    tpls = json.loads(t(DF + "ListDataflowTemplatesForAssetClass",
                        {"className": "GeometryCollection", "bIncludeBlank": True}))
    tid = [x["templateId"] for x in tpls if x["templateId"].endswith("DF_GC_Template_StaticMesh")][0]
    path = t(DF + "CreateDataflowCompatibleAssetFromTemplate", {"className": "GeometryCollection",
        "name": "GC_Batch", "path": "/Game/VFX/Batch", "templateId": tid})
    graph = {"refPath": path + ":EmbeddedDataflow"}
    nodes = [n["type"] for n in json.loads(t(DF + "GetGraphStructure", {"graph": graph}))["nodes"]]
    t(DF + "SetVariable", {"graph": graph, "name": "SourceStaticMesh",
                           "value": "/Engine/BasicShapes/Cylinder.Cylinder"})
    t("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": [path.split(".")[0]]})
    return {"ok": "FUniformFractureDataflowNode" in nodes, "asset": path, "nodes": nodes}
```

```python
# script: N9  (R9) a compile error read back, then the input restored
import json, time
NS = "NiagaraToolsets.NiagaraToolset_System."
SYS = {"refPath": "/Game/VFX/Batch/NS_Batch.NS_Batch"}
LIFE = {"system": SYS, "emitterName": "Sparks", "scriptName": "ParticleSpawnScript",
        "moduleName": "InitializeParticle", "inputNameStack": ["Lifetime"]}   # unhidden by N3

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def settle(want_error=False, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = t(NS + "GetSystemCompileState", {"system": SYS})
        if not s["bIsCompiling"] and (s["bHasErrors"] or not want_error):
            return s
        time.sleep(1.0)
    return s

def run():
    settle()
    t(NS + "SetStackInputData", {"stackInputRef": LIFE, "inputData": {
        "struct": {"refPath": "/Script/NiagaraEditor.NiagaraExt_StackInputData_HlslExpression"},
        "value": {"hlslExpression": "this_is_not_hlsl(("}}})
    bad = settle(want_error=True)
    errors = [e["message"][:120] for s in bad["scripts"] for e in s["compileEvents"] if e["severity"] == "Error"]
    t(NS + "SetStackInputData", {"stackInputRef": LIFE, "inputData": {
        "struct": {"refPath": "/Script/Niagara.NiagaraFloat"}, "value": {"value": 0.6}}})
    good = settle()
    return {"ok": bool(bad["bHasErrors"]) and not good["bHasErrors"], "status_with_error": bad["aggregateStatus"],
            "errors": errors[:2], "status_after_fix": good["aggregateStatus"]}
```
