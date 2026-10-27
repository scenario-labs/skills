# Import and asset hygiene through Epic's Unreal MCP toolsets

The argument shapes for the toolsets this skill owns, so `describe_toolset` is not needed, and what
each import tool really does on 5.8.3. Everything marked "run on 5.8.3" was executed through
`ue_mcp.Mcp` against an editor started with `ue_run.launch_editor(..., mcp_port=N)`. The recipes are
a runnable test: `python3 tests/code/unreal-pipeline-automation/live_mcp_recipes.py` (builds the
synthetic fixtures, starts and stops its own headless editor on a copy of the base project, exit 0
only if every recipe passes; FBX recipes need Blender on PATH to build their fixtures). Last run: 8
of 8 recipes pass call by call (77 tool calls), and the seven script forms (P1, P4, P5, P6, P7a,
P7b, P8) pass as written, one call each (2026-10-21).

**The one limit to know first:** `StaticMeshTools.import_file` and `SkeletalMeshTools.import_file`
go through the FBX factory and accept `.fbx` and `.obj` only; a `.glb` is refused
(`FbxFactory does not support ".glb" files. Allowed: ['fbx', 'obj']`, run on 5.8.3). glTF, WAV, MP3
and batch imports with a pipeline preset go through Python (`AssetImportTask` or
`InterchangeManager`, procedures P3 and P3b), either as a commandlet job or through a project-local
`run_python` tool. `ProgrammaticToolset.execute_tool_script` cannot help there: its sandbox refuses
`import unreal`.

## Intent map

| Intent                               | Toolset and tool                                                                                                                            | Notes                                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Import FBX or OBJ as a static mesh   | `StaticMeshTools.import_file`                                                                                                               | `combine_meshes`, `import_materials`, `import_textures`; Nanite off; materials come in as Materials, not instances |
| Import a skinned FBX                 | `SkeletalMeshTools.import_file`                                                                                                             | creates `<name>_Skeleton`; `create_physics_asset` produced none on a 2-bone fixture                                |
| Import an image (PNG, TGA, EXR, HDR) | `TextureTools.import_file`                                                                                                                  | `.hdr` becomes a TextureCube, `.exr` a Texture2D; flags need fixing after                                          |
| Read or fix texture flags            | `ObjectTools.get_properties` / `set_properties`                                                                                             | `SRGB`, `compressionSettings`, `LODGroup`, `virtualTextureStreaming`, `mipGenSettings`                             |
| Size, bounds, slots, triangles       | `StaticMeshTools.get_bounds`, `get_material_slots`, `get_triangle_count`, `get_lod_count`, `is_nanite_enabled`                              | read back after every import                                                                                       |
| LODs, collision, Nanite              | `generate_lods`, `generate_convex_collisions`, `set_nanite_enabled`, `set_lod_thresholds`                                                   | one call each per mesh; `generate_lods` with n percents gives n + 1 LODs                                           |
| Assign a material to a slot          | `StaticMeshTools.set_material`                                                                                                              | `slot_name` from `get_material_slots`                                                                              |
| Bones, sockets                       | `SkeletalMeshTools.get_bone_names`, `get_bone_parent`, `add_socket`, `get_socket_names`                                                     |                                                                                                                    |
| Find, move, rename, reference checks | `AssetTools.find_assets`, `move`, `exists`, `get_dependencies`, `get_referencers`, `get_asset_class`                                        | `move` is a rename too; dependency queries need a registry rescan for assets made this session (P7)                |
| Metadata for provenance              | `AssetTools.update_metadata_tags`, `get_metadata_tags`                                                                                      | for example `Source=generated`                                                                                     |
| Save                                 | `AssetTools.save_assets`                                                                                                                    | imports through MCP are saved only when asked                                                                      |
| Is an importer enabled               | `PluginToolset.ListDiscoveredPlugins`, then `IsEnabled`                                                                                     | `IsEnabled` errors on a plugin that is not installed                                                               |
| Project settings                     | `ConfigSettingsToolset.ListContainers`, `ListCategories`, `ListSections`, `GetSectionPropertyValues`, `SetSectionProperties`, `SaveSection` | discover names first; nothing is guessable                                                                         |

## Signatures (catalog 5.8.3)

Generated with
`gen_toolset_map.py tests/arena/mcp-catalog-5.8.3 static_mesh skeletal_mesh texture asset.AssetTools ConfigSettings PluginToolset`.

```
StaticMeshTools
import_file(asset_name: str, combine_meshes?: bool, folder_path: str, import_materials?: bool, import_textures?: bool, source_file: str) -> [Ref<Object>]
generate_convex_collisions(hull_count?: int, hull_precision?: int, max_hull_verts?: int, mesh: Ref<StaticMesh>) -> bool
generate_lods(mesh: Ref<StaticMesh>, triangle_percents: [float]) -> int
get_bounds(mesh) -> {Box}            get_lod_count(mesh) -> int          get_lod_thresholds(mesh) -> [float]
get_material(mesh, slot_name: str) -> Ref<MaterialInterface>             get_material_slots(mesh) -> [str]
get_triangle_count(lod_index?: int, mesh) -> int                         get_vertex_count(lod_index?: int, mesh) -> int
is_nanite_enabled(mesh) -> bool      remove_collisions(mesh) -> bool     remove_lods(mesh) -> bool
set_lod_thresholds(mesh, thresholds: [float]) -> bool
set_material(material: Ref<MaterialInterface>, mesh, slot_name: str) -> bool
set_nanite_enabled(enabled: bool, mesh) -> None

SkeletalMeshTools (import side)
import_file(asset_name: str, create_physics_asset?: bool, folder_path: str, import_animations?: bool, import_materials?: bool, import_textures?: bool, skeleton?: Ref<Skeleton>, source_file: str) -> [Ref<Object>]
get_bone_names(mesh) -> [str]   get_bone_parent(bone_name: str, mesh) -> str   get_bone_children(bone_name: str, mesh) -> [str]
get_bounds(mesh) -> {BoxSphereBounds}   get_skeleton(mesh) -> Ref<Skeleton>   get_physics_asset(mesh) -> Ref<PhysicsAsset>
get_material_slots(mesh) -> [str]   get_morph_target_names(mesh) -> [str]   get_lod_count(mesh) -> int
add_socket(bone_name: str, mesh, socket_name: str) -> Ref<SkeletalMeshSocket>   get_socket_names(mesh) -> [str]
assign_physics_asset(mesh, physics_asset: Ref<PhysicsAsset>) -> bool

TextureTools
get_size(texture: Ref<Texture2D>) -> {IntPoint}
import_file(asset_name: str, folder_path: str, source_file: str) -> [Ref<Object>]

AssetTools
find_assets(asset_type?: Ref<Class>, folder_path: str, name: str, recursive?: bool, tags?: {..}) -> [str]
exists(path: str) -> bool   get_asset_class(asset_path: str) -> str   load_asset(asset_path: str) -> Ref<Object>
move(new_path: str, path: str) -> bool   duplicate(new_path: str, path: str) -> bool   delete(path: str) -> bool
create_folder(path: str) -> bool   list_folders(recursive?: bool, root_path: str) -> [str]
get_dependencies(asset_path: str) -> [str]   get_referencers(asset_path: str) -> [str]
get_asset_tags(asset_path: str) -> {..}   get_metadata_tags(asset_path: str) -> {..}
update_metadata_tags(asset_path: str, remove_tags?: [str], set_tags?: {..}) -> None
save_assets(asset_paths: [str]) -> bool   is_dirty(asset_path: str) -> bool

PluginToolset
IsEnabled(pluginName: str) -> bool   ListEnabledPlugins() -> [str]   GetPluginInfo(pluginName: str) -> {PluginToolsetInfo}
SetPluginEnabled(bEnabled: bool, pluginName: str) -> None

ConfigSettingsToolset
ListContainers() -> [str]   ListCategories(containerName: str) -> [str]   ListSections(categoryName: str, containerName: str) -> [str]
GetSectionSchema(categoryName, containerName, sectionName) -> str
GetSectionPropertyValues(categoryName: str, containerName: str, propertyNames: [str], sectionName: str) -> str
SetSectionProperties(categoryName: str, containerName: str, propertiesJson: str, sectionName: str) -> bool
SaveSection(categoryName: str, containerName: str, sectionName: str) -> bool
```

## Batching: one `execute_tool_script` instead of many calls

Four or more toolset calls in a row go through one
`ProgrammaticToolset.execute_tool_script {"script": "<text>"}` call: the scripts below replace 6 to
20 round trips each. The single-call JSON stays for one-off fixes and as the signature reference.
Call `ProgrammaticToolset.get_execution_environment` once per session, before the first script. How
the sandbox behaves (run on 5.8.3):

- The script defines `run()` and returns a dict; the tool returns it as a JSON string in
  `returnValue`. Imports are limited to `json`, `math`, `re`, `time`, `datetime`, `copy`;
  `import unreal` is refused.
- `execute_tool("<full toolset path>.<tool>", json.dumps(args))` returns `{"returnValue": ...}`; the
  tool name is the full path, for example
  `editor_toolset.toolsets.material.MaterialTools.create_material`.
- A failing call ends the whole script with that tool's error text; `try`/`except` does not catch
  it, and what earlier calls created stays. Keep a call that may fail (an existing asset name, P2's
  refused `.glb`) outside the script, or check first (`AssetTools.exists`).
- Paths like `/abs/...` are placeholders for your files.

## Recipes (run on 5.8.3, `live_mcp_recipes.py`)

Toolset prefixes: `editor_toolset.toolsets.static_mesh.StaticMeshTools`,
`editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools`,
`editor_toolset.toolsets.texture.TextureTools`, `editor_toolset.toolsets.asset.AssetTools`,
`editor_toolset.toolsets.object.ObjectTools`, `PluginToolset.PluginToolset`,
`ConfigSettingsToolset.ConfigSettingsToolset`.

### P1. FBX static mesh from a meter, Y-up tool

```json
StaticMeshTools.import_file {"folder_path": "/Game/Props/Crate", "asset_name": "SM_Crate", "source_file": "/abs/crate.fbx",
                             "combine_meshes": true, "import_materials": true, "import_textures": true}
StaticMeshTools.get_bounds  {"mesh": {"refPath": "/Game/Props/Crate/SM_Crate.SM_Crate"}}
   -> {"min": {"x": -20, "y": -25, "z": 0}, "max": {"x": 80, "y": 25, "z": 200}}
StaticMeshTools.get_material_slots {"mesh": ...}  -> ["MI_Wood_Gen", "MI_Metal_Gen"]
StaticMeshTools.is_nanite_enabled  {"mesh": ...}  -> false
```

Fixture: a 1 x 2 x 0.5 m box, 2 m tall in Y-up, pivot at its base and 0.3 m off-center, exported
from Blender with Apply Unit Scale, forward -Z, up Y. It lands 100 x 50 x 200 cm, Z up, pivot kept,
two slots named after the source materials, Nanite off, one LOD (run on 5.8.3). Materials come in as
`Material` assets (not instances) named after the slots, textures as `Image_<n>`: plan on replacing
them with instances of your master.

As one script (run on 5.8.3, 1 call instead of 12):

```python
# execute_tool_script: P1 FBX static mesh, import and read back
import json

SM = "editor_toolset.toolsets.static_mesh.StaticMeshTools."
AT = "editor_toolset.toolsets.asset.AssetTools."
SOURCE = "/abs/crate.fbx"               # the file to import
FOLDER, NAME = "/Game/PipeScripts/Crate", "SM_Crate"


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def run():
    objs = call(SM + "import_file", folder_path=FOLDER, asset_name=NAME, source_file=SOURCE,
                combine_meshes=True, import_materials=True, import_textures=True)
    mesh = [o for o in objs if o["refPath"].endswith("/%s.%s" % (NAME, NAME))][0]
    b = call(SM + "get_bounds", mesh=mesh)
    assets = {p.rsplit("/", 1)[-1]: call(AT + "get_asset_class", asset_path=p)
              for p in call(AT + "find_assets", folder_path=FOLDER, name="", recursive=True)}
    return {"mesh": mesh, "extent_cm": [round(b["max"][k] - b["min"][k]) for k in "xyz"],
            "min_z": round(b["min"]["z"], 3), "slots": call(SM + "get_material_slots", mesh=mesh),
            "nanite": call(SM + "is_nanite_enabled", mesh=mesh), "assets": assets}
```

### P2. The glTF limit

```json
StaticMeshTools.import_file {"folder_path": "/Game/Props/Glb", "asset_name": "SM_Crate", "source_file": "/abs/crate.glb"}
   -> error: FbxFactory does not support ".glb" files. Allowed: ['fbx', 'obj'].
```

Use Python for glTF (`references/generated-assets.md` lists what lands).

### P3. OBJ: no unit or axis conversion

```json
StaticMeshTools.import_file {"folder_path": "/Game/Props/Obj", "asset_name": "SM_CrateObj", "source_file": "/abs/crate_plain.obj"}
StaticMeshTools.get_bounds  -> {"min": {"x": -0.2, "y": -2, "z": -0.25}, "max": {"x": 0.8, "y": 0, "z": 0.25}}
```

The same 2 m box written as OBJ in meters lands 1 x 2 x 0.5 **units** (centimeters) and lying along
-Y (run on 5.8.3): no meter to centimeter scale and no Y-up to Z-up rotation on this path.
`StaticMeshTools.import_file` has no scale or rotation argument: convert OBJ to FBX or glTF before
import, or import through Python with a preset that sets the generic pipeline's top-level
`import_offset_*` properties (uniform scale, rotation) [not yet run]; check `get_bounds` either way.

### P4. LODs, convex collision, Nanite

```json
StaticMeshTools.generate_lods              {"mesh": <m>, "triangle_percents": [0.5, 0.25, 0.125]}
StaticMeshTools.get_lod_count              {"mesh": <m>}                       -> 4
StaticMeshTools.get_triangle_count         {"mesh": <m>, "lod_index": 2}
StaticMeshTools.generate_convex_collisions {"mesh": <m>, "hull_count": 1}      -> true
StaticMeshTools.set_nanite_enabled         {"mesh": <m>, "enabled": true}
AssetTools.save_assets                     {"asset_paths": ["/Game/Props/Crate/SM_Crate"]}
```

Run on 5.8.3: `generate_lods` keeps LOD0 and adds one LOD per entry, so three percents give four
LODs (passing `[1.0, 0.5, 0.25]` also gave four). The fixture box kept 24 triangles at every level:
there is nothing to reduce on a box, so check `get_triangle_count` per LOD on real meshes.
`get_lod_thresholds` read 0 for every LOD right after `generate_lods`; set screen sizes with
`set_lod_thresholds` **[not yet run]**.

As one script (run on 5.8.3, 1 call instead of 11):

```python
# execute_tool_script: P4 LODs, convex collision, Nanite
import json

SM = "editor_toolset.toolsets.static_mesh.StaticMeshTools."
MESH = {"refPath": "/Game/PipeScripts/Crate/SM_Crate.SM_Crate"}


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def run():
    n = call(SM + "generate_lods", mesh=MESH, triangle_percents=[0.5, 0.25, 0.125])
    lods = call(SM + "get_lod_count", mesh=MESH)
    tris = [call(SM + "get_triangle_count", mesh=MESH, lod_index=i) for i in range(lods)]
    hull = call(SM + "generate_convex_collisions", mesh=MESH, hull_count=1)
    call(SM + "set_nanite_enabled", mesh=MESH, enabled=True)
    call("editor_toolset.toolsets.asset.AssetTools.save_assets", asset_paths=[MESH["refPath"].split(".")[0]])
    return {"generate_lods": n, "lods": lods, "tris": tris, "hull": hull,
            "nanite": call(SM + "is_nanite_enabled", mesh=MESH)}
```

### P5. Texture intake: read, then fix

```json
TextureTools.import_file    {"folder_path": "/Game/Props/Tex", "asset_name": "T_Crate_ORM", "source_file": "/abs/T_Crate_ORM.png"}
ObjectTools.get_properties  {"instance": <t>, "properties": ["SRGB", "compressionSettings", "LODGroup"]}
   -> {"SRGB": true, "compressionSettings": "TC_Default", "LODGroup": "TEXTUREGROUP_World"}
ObjectTools.set_properties  {"instance": <t>, "values": "{\"SRGB\": false, \"compressionSettings\": \"TC_Masks\"}"}
TextureTools.import_file    {"folder_path": "/Game/Sky", "asset_name": "HDR_Sky", "source_file": "/abs/sky.hdr"}
AssetTools.get_asset_class  {"asset_path": "/Game/Sky/HDR_Sky"}   -> "TextureCube"
```

Run on 5.8.3: a packed ORM lands sRGB color; a tangent-space normal map is detected from its pixels
(`TC_Normalmap`, `TEXTUREGROUP_WorldNormalMap`); a sky-blue equirect PNG was detected as a normal
map too, so fix it back to color; `.hdr` becomes a TextureCube with `TC_HDR_Compressed` (BC6H);
`.exr` stays a Texture2D with `TC_HDR_Compressed`. `values` is a JSON string; enum spellings are the
reflected ones (`TC_Masks`, not `TC_MASKS`).

As one script (run on 5.8.3, 1 call instead of 20). Inside one `set_properties`, keys apply in order
and leaving `TC_Normalmap` resets `SRGB`: put `compressionSettings` before `SRGB` (the sky fix above
lost its sRGB that way).

```python
# execute_tool_script: P5 texture intake, read then fix
import json

OT = "editor_toolset.toolsets.object.ObjectTools."
AT = "editor_toolset.toolsets.asset.AssetTools."
FOLDER = "/Game/PipeScripts/Tex"
FILES = {"T_Gen_ORM": "/abs/T_Gen_ORM.png", "T_Gen_Normal": "/abs/T_Gen_Normal.png",
         "T_Gen_Sky_Equirect": "/abs/T_Gen_Sky_Equirect.png", "HDR_Gen_Sky": "/abs/HDR_Gen_Sky.hdr"}
FIXES = {"T_Gen_ORM": {"SRGB": False, "compressionSettings": "TC_Masks"},            # packed masks: linear
         "T_Gen_Sky_Equirect": {"compressionSettings": "TC_Default", "SRGB": True,   # taken for a normal map;
                                "LODGroup": "TEXTUREGROUP_World"}}                     # compression before SRGB
KEYS = ["SRGB", "compressionSettings", "LODGroup"]


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def flags(t):
    return json.loads(call(OT + "get_properties", instance=t, properties=KEYS))


def run():
    tex, imported = {}, {}
    for name, src in FILES.items():
        tex[name] = call("editor_toolset.toolsets.texture.TextureTools.import_file",
                         folder_path=FOLDER, asset_name=name, source_file=src)[0]
        imported[name] = dict(flags(tex[name]), cls=call(AT + "get_asset_class", asset_path=FOLDER + "/" + name))
    for name, values in FIXES.items():
        call(OT + "set_properties", instance=tex[name], values=json.dumps(values))
    call(AT + "save_assets", asset_paths=[FOLDER + "/" + n for n in FILES])
    return {"imported": imported, "fixed": {n: flags(tex[n]) for n in FIXES}}
```

### P6. Skinned FBX

```json
SkeletalMeshTools.import_file  {"folder_path": "/Game/Chars/Tube", "asset_name": "SK_Tube", "source_file": "/abs/tube_skinned.fbx", "import_animations": false}
SkeletalMeshTools.get_bone_names {"mesh": {"refPath": "/Game/Chars/Tube/SK_Tube.SK_Tube"}}  -> ["Rig", "root", "tip"]
SkeletalMeshTools.add_socket   {"mesh": <sk>, "bone_name": "tip", "socket_name": "Muzzle"}
```

Run on 5.8.3: the skeleton lands as `SK_Tube_Skeleton` beside the mesh; the Blender armature object
(named "Rig" here) became an extra root bone. Naming the armature object "Armature" is the usual
workaround **[not yet run]**; check `get_bone_names` either way. `create_physics_asset: true`
produced no physics asset for this 2-bone, 2 m tube (`get_physics_asset` errors "has no physics
asset assigned").

As one script (run on 5.8.3, 1 call instead of 8):

```python
# execute_tool_script: P6 skinned FBX, bones, socket
import json

SK = "editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools."
SOURCE = "/abs/tube_skinned.fbx"        # the file to import
FOLDER, NAME = "/Game/PipeScripts/Tube", "SK_Tube"


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def run():
    objs = call(SK + "import_file", folder_path=FOLDER, asset_name=NAME, source_file=SOURCE, import_animations=False)
    mesh = [o for o in objs if o["refPath"].endswith("/%s.%s" % (NAME, NAME))][0]
    bones = call(SK + "get_bone_names", mesh=mesh)
    call(SK + "add_socket", mesh=mesh, bone_name="tip", socket_name="Muzzle")
    call("editor_toolset.toolsets.asset.AssetTools.save_assets", asset_paths=[FOLDER + "/" + NAME])
    return {"bones": bones, "parents": {b: call(SK + "get_bone_parent", mesh=mesh, bone_name=b) for b in bones},
            "skeleton": call(SK + "get_skeleton", mesh=mesh), "half_extent_cm": call(SK + "get_bounds", mesh=mesh)["boxExtent"],
            "sockets": call(SK + "get_socket_names", mesh=mesh)}
```

### P7. Rename into the convention, check references, tag provenance

```json
AssetTools.create_folder       {"path": "/Game/Props/Final"}
AssetTools.move                {"path": "/Game/Props/Crate/SM_Crate", "new_path": "/Game/Props/Final/SM_Prop_Crate"}
AssetTools.exists              {"path": "/Game/Props/Final/SM_Prop_Crate"}   -> true
AssetTools.save_assets         {"asset_paths": ["/Game/Props/Final/SM_Prop_Crate"]}
AssetTools.get_dependencies    {"asset_path": "/Game/Props/Final/SM_Prop_Crate"}
   -> error: 'NoneType' object is not iterable          (asset made in this session)
run_python: unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(["/Game/Props"], True)
AssetTools.get_dependencies    {"asset_path": "/Game/Props/Final/SM_Prop_Crate"}
   -> ["/Script/NavigationSystem", "/Game/Props/Crate/MI_Wood_Gen", "/Game/Props/Crate/MI_Metal_Gen"]
AssetTools.get_referencers     {"asset_path": "/Game/Props/Crate/MI_Wood_Gen"}   -> ["/Game/Props/Final/SM_Prop_Crate"]
AssetTools.update_metadata_tags {"asset_path": "/Game/Props/Final/SM_Prop_Crate", "set_tags": {"Source": "generated", "Reviewed": "no"}}
AssetTools.get_metadata_tags   {"asset_path": "/Game/Props/Final/SM_Prop_Crate"}
```

Run on 5.8.3, headless editor: `get_dependencies` and `get_referencers` fail with "'NoneType' object
is not iterable" for assets imported, moved or saved in the same session, even after `save_assets`;
the asset registry has no dependency data for them yet. No MCP tool rescans, so the recipe runs one
`scan_paths_synchronous(paths, force_rescan=True)` through the project-local `run_python` tool, then
both queries answer. `move` leaves no asset at the old path (`exists` is false).

As two scripts around the rescan (run on 5.8.3, 3 calls instead of 13). In an offscreen editor the
dependency queries answered without the rescan; in a `-nullrhi` editor they needed it.

```python
# execute_tool_script: P7a rename into the convention, tag provenance
import json

AT = "editor_toolset.toolsets.asset.AssetTools."
SRC, DST = "/Game/PipeScripts/Crate/SM_Crate", "/Game/PipeScripts/Props/SM_Prop_Crate"


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def run():
    call(AT + "create_folder", path=DST.rsplit("/", 1)[0])
    moved = call(AT + "move", path=SRC, new_path=DST)
    call(AT + "update_metadata_tags", asset_path=DST, set_tags={"Source": "generated", "Reviewed": "no"})
    call(AT + "save_assets", asset_paths=[DST])
    return {"moved": moved, "old_exists": call(AT + "exists", path=SRC), "new_exists": call(AT + "exists", path=DST),
            "tags": call(AT + "get_metadata_tags", asset_path=DST)}
```

```python
# execute_tool_script: P7b dependencies and referencers (after a registry rescan)
import json

AT = "editor_toolset.toolsets.asset.AssetTools."
SM = "editor_toolset.toolsets.static_mesh.StaticMeshTools."
MESH = "/Game/PipeScripts/Props/SM_Prop_Crate"


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def run():
    ref = {"refPath": MESH + "." + MESH.rsplit("/", 1)[-1]}
    out = {"dependencies": call(AT + "get_dependencies", asset_path=MESH), "referencers": {}}
    for slot in call(SM + "get_material_slots", mesh=ref):
        mat = call(SM + "get_material", mesh=ref, slot_name=slot)["refPath"].split(".")[0]
        out["referencers"][mat] = call(AT + "get_referencers", asset_path=mat)
    return out
```

### P8. Importers and settings

```json
PluginToolset.ListDiscoveredPlugins {}
PluginToolset.IsEnabled            {"pluginName": "Interchange"}         -> true
ConfigSettingsToolset.ListContainers {}
ConfigSettingsToolset.ListCategories {"containerName": "Project"}
```

Run on 5.8.3, base project: Interchange, InterchangeEditor, GLTFExporter, PythonScriptPlugin and
DataValidation are enabled; the legacy `GLTFImporter` plugin is not installed (glTF import is
Interchange's own translator). `IsEnabled` on a name that is not installed errors, so list first.
Containers: `Editor`, `InputBinding`, `Project`; `Project` holds the categories `Editor`, `Engine`,
`Game`, `Platforms`, `Plugins`, `Project`.

As one script (run on 5.8.3, 1 call instead of 10):

```python
# execute_tool_script: P8 importers and settings
import json

PT = "PluginToolset.PluginToolset."
CS = "ConfigSettingsToolset.ConfigSettingsToolset."
WANTED = ["Interchange", "InterchangeEditor", "GLTFImporter", "GLTFExporter", "PythonScriptPlugin", "DataValidation"]


def call(tool, **args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None


def run():
    found = call(PT + "ListDiscoveredPlugins")
    plugins = {n: (call(PT + "IsEnabled", pluginName=n) if n in found else "not installed") for n in WANTED}
    containers = call(CS + "ListContainers")
    return {"plugins": plugins, "containers": containers,
            "categories": {k: call(CS + "ListCategories", containerName=k) for k in containers}}
```

## When to use Python or a commandlet instead

- **glTF, audio, and anything with an import preset:** Python only (`AssetImportTask` with
  `automated`, `replace_existing`, `save`; or `InterchangeManager.import_asset` with
  `ImportAssetParameters`). In an editor session, a project-local `run_python` tool reaches the same
  API.
- **More than a handful of files:** the headless job (`ue_pipeline_job.py import`), chunks of 25,
  one report; one MCP call per property per asset does not scale.
- **Mesh edits in a commandlet:** `StaticMeshEditorSubsystem` is None there, and the deprecated
  `EditorStaticMeshLibrary` refuses: `get_lod_count`, `set_lods` and `add_simple_collisions` return
  -1 and `get_lod_screen_sizes` returns [] (run on 5.8.3). What works in a commandlet:
  `StaticMesh.get_num_lods()`, setting the `lod_group` property (a `LargeProp` group rebuilt 1 LOD
  into 4), reading `body_setup.agg_geom`. Build explicit LOD chains and add collision in an editor
  (these MCP tools, or `ue_run` latent mode).
- **Collision counts:** `get_simple_collision_count` read 0 (editor) and -1 (commandlet) on a mesh
  that had one convex hull in `body_setup.agg_geom.convex_elems` (run on 5.8.3); count `agg_geom`
  elements instead.
