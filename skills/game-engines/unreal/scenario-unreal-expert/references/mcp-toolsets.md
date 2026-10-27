# Epic Unreal MCP toolsets in 5.8.3: what exists, who owns it, what a call looks like

Source: a snapshot of `list_toolsets` and `describe_toolset` on UE 5.8.3 (launcher build, plugins
ModelContextProtocol and AllToolsets), 52 toolsets and 830 tools. Names, argument names and types
below come from that snapshot; the purpose lines are ours. Regenerate after an engine update:
`ue_mcp.snapshot(m, dir)`, then `gen_toolset_map.py <dir>`. A `describe_toolset` call is paid in
tokens: sizes are in the table, so read this file and call `describe_toolset` only for one small
toolset you need or when a signature here fails.

How to call: `call_tool(toolset_name, tool_name, arguments)`; `toolset_name` is the full name in the
first column, `tool_name` the short name. Arguments are a JSON object. Object references are
`{"refPath": "/Game/Maps/L.L:PersistentLevel.Actor_0"}` (use the path a previous call returned).
Results arrive as `{"returnValue": ...}`. Errors have `isError: true` and a text reason.

## All toolsets

| Toolset (full name)                                                        | Tools | Describe size (tokens) | Owner skill         | What it is for                                                                                                                                                                |
| -------------------------------------------------------------------------- | ----- | ---------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ToolsetRegistry.AgentSkillToolset`                                        | 4     | 1,083                  | lead                | list, read, create and update the engine's in-editor Agent Skills (Niagara, PCG, materials, lighting, Blueprints): call ListSkills first, GetSkills for the one you need      |
| `editor_toolset.toolsets.actor.ActorTools`                                 | 17    | 6,016                  | world-building      | actor labels, tags, transforms, bounds, components, look-at                                                                                                                   |
| `editor_toolset.toolsets.scene.SceneTools`                                 | 20    | 8,338                  | world-building      | the loaded level: find, spawn from asset or class, folders, merge, level instances, load a level, a line trace                                                                |
| `editor_toolset.toolsets.asset.AssetTools`                                 | 21    | 4,196                  | pipeline-automation | assets on disk: find, create folders, duplicate, move, delete, save, dependencies, referencers, metadata tags, read and write files                                           |
| `editor_toolset.toolsets.object.ObjectTools`                               | 6     | 1,874                  | lead                | generic property read and write on any UObject (the way to set light intensity, post process values, component settings); list_properties first                               |
| `editor_toolset.toolsets.primitive.PrimitiveTools`                         | 4     | 3,500                  | world-building      | add cube, sphere, cylinder, cone components to an actor                                                                                                                       |
| `editor_toolset.toolsets.programmatic.ProgrammaticToolset`                 | 2     | 918                    | lead                | batch many tool calls in one sandboxed script (no unreal module); call get_execution_environment once first                                                                   |
| `EditorToolset.EditorAppToolset`                                           | 21    | 7,512                  | lead                | editor state: console variable search, screenshots (viewport, editor, asset), camera, selection, content browser, start and stop PIE                                          |
| `EditorToolset.LogsToolset`                                                | 4     | 837                    | lead                | read the output log by category, set verbosity: the first place to look when a call fails quietly                                                                             |
| `AutomationTestToolset.AutomationTestToolset`                              | 7     | 1,590                  | performance         | discover, run and read automation tests, by name or filter                                                                                                                    |
| `ConfigSettingsToolset.ConfigSettingsToolset`                              | 8     | 2,055                  | pipeline-automation | project and editor settings sections: list, schema, read, set, save                                                                                                           |
| `PluginToolset.PluginToolset`                                              | 17    | 5,529                  | pipeline-automation | list, enable and disable plugins, read descriptors and dependencies, create a plugin                                                                                          |
| `SemanticSearchToolset.SemanticSearchToolset`                              | 2     | 1,593                  | lead                | search assets by meaning and find similar assets                                                                                                                              |
| `SlateInspectorToolset.SlateInspectorToolset`                              | 14    | 3,312                  | lead                | drive the editor UI like a browser (snapshot, click, type, screenshot): last resort when no toolset covers an action                                                          |
| `editor_toolset.toolsets.material.MaterialTools`                           | 22    | 8,583                  | materials           | material and function graphs: create, add expressions, connect to outputs, recompile                                                                                          |
| `editor_toolset.toolsets.material_instance.MaterialInstanceTools`          | 13    | 4,248                  | materials           | material instances: create, set parent, scalar, vector, texture and static switch parameters                                                                                  |
| `editor_toolset.toolsets.texture.TextureTools`                             | 2     | 646                    | pipeline-automation | import a texture file, read its size (import settings are not here: use Python)                                                                                               |
| `editor_toolset.toolsets.static_mesh.StaticMeshTools`                      | 16    | 5,484                  | pipeline-automation | static meshes: import a file, bounds, triangle count, LODs, collision, Nanite toggle, material slots                                                                          |
| `editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools`                  | 22    | 8,480                  | animation           | skeletal meshes: import, bones, sockets, morph targets, materials, physics asset                                                                                              |
| `PhysicsToolsets.PhysicsAssetToolset`                                      | 17    | 6,378                  | animation           | physics assets: create from a mesh, bodies, shapes, constraints, mass                                                                                                         |
| `editor_toolset.toolsets.blueprint.BlueprintTools`                         | 53    | 25,646                 | gameplay            | Blueprint authoring: create, variables, functions, events, graph nodes and pins, compile                                                                                      |
| `UMGToolSet.UMGToolSet`                                                    | 23    | 20,561                 | gameplay            | widget Blueprints: create, add and move widgets, slots, bind events, compile                                                                                                  |
| `editor_toolset.toolsets.data_table.DataTableTools`                        | 10    | 2,859                  | gameplay            | data tables: create, rows, schema, import                                                                                                                                     |
| `editor_toolset.toolsets.curve_table.CurveTableTools`                      | 9     | 2,819                  | gameplay            | curve tables: create, rows, keys, import                                                                                                                                      |
| `editor_toolset.toolsets.data_asset.DataAssetTools`                        | 1     | 427                    | gameplay            | create a data asset of a class                                                                                                                                                |
| `editor_toolset.toolsets.string_table.StringTableTools`                    | 8     | 2,177                  | gameplay            | string tables: create, entries, import                                                                                                                                        |
| `GameplayTagsToolset.GameplayTagsToolset`                                  | 6     | 1,360                  | gameplay            | gameplay tags: list, add, remove, rename, referencers                                                                                                                         |
| `GASToolsets.AbilitySystemInspectorToolset`                                | 4     | 1,710                  | gameplay            | runtime state of an ability system component (effects, tags, attributes, abilities)                                                                                           |
| `GASToolsets.AttributeSetToolset`                                          | 2     | 910                    | gameplay            | attribute set classes and their attributes                                                                                                                                    |
| `GASToolsets.GameplayCueToolset`                                           | 8     | 2,520                  | gameplay            | gameplay cues and notify assets                                                                                                                                               |
| `state_tree_toolset.toolsets.state_tree.StateTreeTools`                    | 9     | 9,079                  | gameplay            | read StateTree assets (read only)                                                                                                                                             |
| `aimodule_toolset.toolsets.behavior_tree.BehaviorTreeTools`                | 7     | 2,221                  | gameplay            | read Behavior Tree assets (read only)                                                                                                                                         |
| `conversation_toolset.toolsets.conversation.ConversationTools`             | 7     | 2,778                  | gameplay            | read conversation graphs (read only)                                                                                                                                          |
| `WorldConditionsToolset.WorldConditionTools`                               | 2     | 1,078                  | gameplay            | describe world condition queries (read only)                                                                                                                                  |
| `DataRegistryToolset.DataRegistryTools`                                    | 7     | 2,819                  | gameplay            | read data registries (read only)                                                                                                                                              |
| `GameFeaturesToolset.GameFeaturesToolset`                                  | 7     | 1,417                  | pipeline-automation | game feature plugins: list, activate, deactivate                                                                                                                              |
| `animation_toolset.toolsets.sequencer.SequencerTools`                      | 140   | 42,010                 | cinematics          | level sequences: create, bindings, tracks, sections, cameras, markers, folders (140 tools)                                                                                    |
| `animation_toolset.toolsets.keyframing.SequencerKeyframingTools`           | 22    | 6,464                  | cinematics          | keys on sequencer channels and the curve editor                                                                                                                               |
| `animation_toolset.toolsets.outliner.SequencerOutlinerTools`               | 18    | 3,870                  | cinematics          | sequencer outliner state: mute, solo, lock, expand                                                                                                                            |
| `animation_toolset.toolsets.conditions.SequencerConditionTools`            | 9     | 2,456                  | cinematics          | runtime conditions on tracks and sections                                                                                                                                     |
| `animation_toolset.toolsets.custom_bindings.SequencerCustomBindingTools`   | 8     | 3,969                  | cinematics          | convert bindings between possessable, spawnable and custom                                                                                                                    |
| `animation_toolset.toolsets.import_export.SequencerImportExportTools`      | 6     | 3,612                  | cinematics          | FBX and animation sequence import and export for sequences                                                                                                                    |
| `animation_toolset.toolsets.controlrig.ControlRigTools`                    | 44    | 27,990                 | animation           | Control Rig assets: hierarchy, controls, graphs, nodes, variables                                                                                                             |
| `animation_toolset.toolsets.controlrig_sequencer.SequencerControlRigTools` | 72    | 22,245                 | animation           | animating with Control Rig in sequencer: layers, baking, spaces, selection, values                                                                                            |
| `DataflowAgent.DataflowAgentToolset`                                       | 22    | 6,089                  | vfx                 | Dataflow graph editing (cloth, destruction setups)                                                                                                                            |
| `NiagaraToolsets.NiagaraToolset_System`                                    | 46    | 112,601                | vfx                 | Niagara systems: create, emitters, modules, renderers, parameters, stack inputs, schemas (46 tools, 112k tokens to describe: use the signatures in references/mcp-niagara.md) |
| `NiagaraToolsets.NiagaraToolset_Component`                                 | 4     | 11,416                 | vfx                 | set Niagara component variables on a placed system                                                                                                                            |
| `NiagaraToolsets.NiagaraToolset_Assets`                                    | 3     | 2,586                  | vfx                 | find Niagara module scripts and read their digest                                                                                                                             |
| `NiagaraToolsets.NiagaraToolset_Blueprint`                                 | 2     | 1,045                  | vfx                 | wrap a system or component in a Blueprint                                                                                                                                     |
| `NiagaraToolsets.NiagaraToolset_Info`                                      | 1     | 288                    | vfx                 | enum info for Niagara types                                                                                                                                                   |
| `PCGToolset.PCGToolset`                                                    | 30    | 12,246                 | world-building      | PCG graphs: create, nodes, pins, parameters, subgraphs, graph instances and execution                                                                                         |
| `PCGToolset.PCGSpatialToolset`                                             | 1     | 426                    | world-building      | run a PCG graph instantly on an area                                                                                                                                          |

## Common struct shapes

- `Vector {x: float, y: float, z: float}` (used 70 times)
- `MovieSceneBindingProxy {bindingId: str, sequence: Ref<MovieSceneSequence>}` (used 51 times)
- `ToolsetNiagaraTypeDefinition {classStructOrEnum: Ref<Object>}` (used 34 times)
- `NiagaraExt_StackItemReference {emitterName: str, inputNameStack: [str], moduleName: str, rendererIndex: int, scriptName: str, system: Ref<NiagaraSystem>}`
  (used 29 times)
- `Rotator {pitch: float, roll: float, yaw: float}` (used 28 times)
- `PinID {direction: enum(EGPD_Input|EGPD_Output), index_id: int, node: Ref<EdGraphNode>}` (used 25
  times)
- `RigElementKey {name: str, type: enum(None|Bone|Null|+12)}` (used 24 times)
- `ToolsetTransform {location: {Vector}, rotation: {Rotator}, scale: {Vector}}` (used 24 times)
- `FInstancedStruct {_structType: str}` (used 21 times)
- `LinearColor {a: float, b: float, g: float, r: float}` (used 18 times)
- `SequencerViewModelScriptingStruct {type: str}` (used 18 times)
- `NiagaraToolsetInstancedValue {struct: Ref<ScriptStruct>, value: any}` (used 15 times)
- `NiagaraExt_StackInputTopology {bIsDynamic: bool, bIsEditable: bool, bIsStaticSwitch: bool, bIsVisible: bool, name: str, type: {ToolsetNiagaraTypeDefinition}}`
  (used 14 times)
- `NiagaraExt_ModuleTopology {bIsSetParametersModule: bool, enabled: bool, inputs: [{NiagaraExt_StackInputTopology}], moduleName: str, moduleScript: Ref<NiagaraScript>}`
  (used 13 times)

## Signatures of the toolsets every task touches

### `AutomationTestToolset.AutomationTestToolset` (7 tools, describe is about 1590 tokens)

- `DiscoverTests(bForceRediscover?: bool) -> str`
- `GetTestResults() -> str`
- `GetTestStatus() -> str`
- `ListTests(limit?: int, nameFilter: str, tagFilter: str) -> str`
- `RunTests(testNames: [str]) -> str`
- `RunTestsByFilter(filterExpression: str) -> str`
- `StopTests() -> bool`

### `ConfigSettingsToolset.ConfigSettingsToolset` (8 tools, describe is about 2055 tokens)

- `GetSectionPropertyValues(categoryName: str, containerName: str, propertyNames: [str], sectionName: str) -> str`
- `GetSectionSchema(categoryName: str, containerName: str, sectionName: str) -> str`
- `ListCategories(containerName: str) -> [str]`
- `ListContainers() -> [str]`
- `ListSections(categoryName: str, containerName: str) -> [str]`
- `ResetSectionToDefaults(categoryName: str, containerName: str, sectionName: str) -> bool`
- `SaveSection(categoryName: str, containerName: str, sectionName: str) -> bool`
- `SetSectionProperties(categoryName: str, containerName: str, propertiesJson: str, sectionName: str) -> bool`

### `EditorToolset.EditorAppToolset` (21 tools, describe is about 7512 tokens)

- `CaptureAssetImage(assetPath: str) -> {ToolsetImage}`
- `CaptureEditorImage() -> {ToolsetImage}`
- `CaptureViewport(annotations?: {ViewportAnnotationConfig}, bShowUI?: bool, captureTransform?: {ToolsetTransform}) -> {ViewportCapture}`
- `FocusOnActors(actors: [Ref<Actor>]) -> None`
- `GetCameraTransform() -> {ToolsetTransform}`
- `GetContentBrowserPath() -> str`
- `GetOpenAssets() -> [str]`
- `GetSelectedActors() -> [Ref<Actor>]`
- `GetSelectedAssets() -> [str]`
- `GetVisibleActors() -> [Ref<Actor>]`
- `IsPIERunning() -> bool`
- `OpenEditorForAsset(assetPath: str) -> None`
- `ScreenCoordsToWorld(coords: {Vector2D}, traceDistance?: float) -> {Vector}`
- `SearchCVars(name: str) -> str`
- `SelectActors(actors: [Ref<Actor>]) -> None`
- `SelectAssets(assetPaths: [str]) -> null`
- `SetCameraTransform(transform: {ToolsetTransform}) -> None`
- `SetContentBrowserPath(path: str) -> None`
- `StartPIE(options: {PIESessionOptions}) -> null`
- `StopPIE() -> null`
- `WorldPosToScreenCoords(position: {Vector}) -> {Vector2D}`

### `EditorToolset.LogsToolset` (4 tools, describe is about 837 tokens)

- `GetLogCategories(filter: str) -> [str]`
- `GetLogEntries(category?: str, maxEntries?: int, pattern: str) -> [str]`
- `GetVerbosity(category?: str) -> str`
- `SetVerbosity(category?: str, verbosity: str) -> None`

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

### `ToolsetRegistry.AgentSkillToolset` (4 tools, describe is about 1083 tokens)

- `CreateSkill(assetName: str, description: str, details: {AgentSkillDetails}, folderPath: str) -> str`
- `GetSkills(skillPaths: [str]) -> {..}`
- `ListSkills() -> {..}`
- `UpdateSkill(description: str, details: {AgentSkillDetails}, skillPath: str) -> bool`

### `editor_toolset.toolsets.actor.ActorTools` (17 tools, describe is about 6016 tokens)

- `add_component(component_type: Ref<Class>, name: str, owner: Ref<Object>) -> Ref<ActorComponent>`
- `add_tag(actor: Ref<Actor>, tag: str) -> None`
- `get_actor_bounds(actor: Ref<Actor>) -> {Box}`
- `get_actor_transform(actor: Ref<Actor>) -> {ToolsetTransform}`
- `get_component_actor(component: Ref<ActorComponent>) -> Ref<Actor>`
- `get_components(actor: Ref<Actor>, component_type?: Ref<Class>) -> [Ref<ActorComponent>]`
- `get_label(actor: Ref<Actor>) -> str`
- `get_parent_component(component: Ref<SceneComponent>) -> Ref<SceneComponent>`
- `get_root_component(actor: Ref<Actor>) -> Ref<SceneComponent>`
- `get_tags(actor: Ref<Actor>) -> [str]`
- `has_tag(actor: Ref<Actor>, tag: str) -> bool`
- `look_at(actor: Ref<Actor>, target: {Vector}) -> None`
- `remove_component(component: Ref<ActorComponent>) -> bool`
- `remove_tag(actor: Ref<Actor>, tag: str) -> None`
- `set_actor_transform(actor: Ref<Actor>, worldspace?: bool, xform: {ToolsetTransform}) -> bool`
- `set_label(actor: Ref<Actor>, label: str) -> bool`
- `set_parent_component(component: Ref<SceneComponent>, parent?: Ref<SceneComponent>) -> bool`

### `editor_toolset.toolsets.asset.AssetTools` (21 tools, describe is about 4196 tokens)

- `can_edit_asset(asset_path: str) -> bool`
- `create_folder(path: str) -> bool`
- `delete(path: str) -> bool`
- `duplicate(new_path: str, path: str) -> bool`
- `exists(path: str) -> bool`
- `find_assets(asset_type?: Ref<Class>, folder_path: str, name: str, recursive?: bool, tags?: {..}) -> [str]`
- `get_asset_class(asset_path: str) -> str`
- `get_asset_tags(asset_path: str) -> {..}`
- `get_dependencies(asset_path: str) -> [str]`
- `get_metadata_tags(asset_path: str) -> {..}`
- `get_plugin_content_paths(include_engine?: bool) -> [str]`
- `get_referencers(asset_path: str) -> [str]`
- `is_checked_out(asset_path: str) -> bool`
- `is_dirty(asset_path: str) -> bool`
- `list_folders(recursive?: bool, root_path: str) -> [str]`
- `load_asset(asset_path: str) -> Ref<Object>`
- `move(new_path: str, path: str) -> bool`
- `read_file(file_path: str) -> str`
- `save_assets(asset_paths: [str]) -> bool`
- `update_metadata_tags(asset_path: str, remove_tags?: [str], set_tags?: {..}) -> None`
- `write_file(content: str, file_path: str) -> None`

### `editor_toolset.toolsets.data_asset.DataAssetTools` (1 tools, describe is about 427 tokens)

- `create(asset_name: str, asset_type: Ref<Class>, folder_path: str) -> Ref<DataAsset>`

### `editor_toolset.toolsets.object.ObjectTools` (6 tools, describe is about 1874 tokens)

- `get_class(instance: Ref<Object>) -> Ref<Class>`
- `get_properties(instance: Ref<Object>, properties: [str]) -> str`
- `list_properties(instance: Ref<Object>) -> str`
- `reset_properties(instance: Ref<Object>, properties: [str]) -> bool`
- `search_subclasses(base_class: Ref<Class>, class_name: str) -> [Ref<Object>]`
- `set_properties(instance: Ref<Object>, values: str) -> bool`

### `editor_toolset.toolsets.programmatic.ProgrammaticToolset` (2 tools, describe is about 918 tokens)

- `execute_tool_script(script: str) -> str`
- `get_execution_environment() -> {ProgrammaticApiExecutionEnvironmentInfo}`

### `editor_toolset.toolsets.scene.SceneTools` (20 tools, describe is about 8338 tokens)

- `add_to_scene_from_asset(asset_path: str, name: str, parent?: Ref<Actor>, snap_to_ground?: bool, xform: {ToolsetTransform}) -> Ref<Actor>`
- `add_to_scene_from_class(actor_type: Ref<Class>, name: str, parent?: Ref<Actor>, snap_to_ground?: bool, xform: {ToolsetTransform}) -> Ref<Actor>`
- `can_edit(actor: Ref<Actor>) -> bool`
- `commit_level_instance(discard?: bool, level_instance: Ref<LevelInstance>) -> None`
- `create_level_instance(level_path: str, name: str, parent?: Ref<Actor>, xform: {ToolsetTransform}) -> Ref<LevelInstance>`
- `delete_folder(folder_path: str) -> int`
- `edit_level_instance(level_instance: Ref<LevelInstance>) -> None`
- `find_actors(actor_type?: Ref<Class>, bounds?: {Box}, collision_channels: [enum(ObjectTypeQuery1|ObjectTypeQuery2|ObjectTypeQuery3|+61)], name: str, root?: Ref<Actor>, tag: str) -> [Ref<Actor>]`
- `get_actors_in_folder(folder_path: str, recursive?: bool) -> [Ref<Actor>]`
- `get_collision_channels() -> [enum(ObjectTypeQuery1|ObjectTypeQuery2|ObjectTypeQuery3|+61)]`
- `get_current_level() -> str`
- `get_folders() -> [str]`
- `is_checked_out(actor: Ref<Actor>) -> bool`
- `load_level(level_path: str) -> None`
- `merge_actors(actors: [Ref<StaticMeshActor>], destroy_source_actors?: bool, name: str, output_path: str) -> Ref<StaticMeshActor>`
- `remove_from_scene(actor: Ref<Actor>) -> bool`
- `rename_folder(new_path: str, old_path: str) -> int`
- `save_actor(actor: Ref<Actor>) -> None`
- `set_actor_folder(actor: Ref<Actor>, folder_path: str) -> None`
- `trace_world(end: {Vector}, start: {Vector}) -> float`
