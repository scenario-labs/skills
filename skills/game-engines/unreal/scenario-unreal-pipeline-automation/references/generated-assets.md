# Generated assets: what lands in Unreal 5.8 and what to fix, in order

Intake guide for files that come out of a generator rather than a DCC artist: meshes and textures
downloaded with Scenario MCP, files the Scenario for Unreal plugin brings into an open editor, or
output of any other image, 3D, sky or audio model. These files carry no studio conventions: no
`UCX_` collision, no sidecar, names like `crate.glb` or `image_0.png`, meters and Y-up for glTF,
packed maps that look like color. Everything marked "run on 5.8.3" was imported on Unreal 5.8.3 with
synthetic fixtures (`tests/code/unreal-pipeline-automation/make_generated_fixtures.py`) by
`in_engine/job_01_generated_assets_probe.py` and `job_02_pipeline_overrides.py`, in a commandlet and
in a headless editor, with identical results unless stated. When a plugin did the import for you,
start at step 2 on what it created.

## The order

1. **Pick the channel.** MCP `StaticMeshTools.import_file` and `SkeletalMeshTools.import_file` take
   `.fbx` and `.obj` only; `.glb` is refused (run on 5.8.3). `TextureTools.import_file` takes PNG,
   HDR and EXR. glTF, audio and any import with a preset go through Python: `AssetImportTask`
   (`automated`, `replace_existing`, `save`) or `InterchangeManager.import_asset` with
   `ImportAssetParameters` (`is_automated`, `override_pipelines`), as a commandlet job
   (`ue_run.run_python`) or through a project-local `run_python` tool in the editor. A commandlet
   imports everything an editor imports.
2. **Count and classes.** What did one file become? A glTF or FBX with two nodes became two static
   meshes (run on 5.8.3). Read the objects the import returns, or list the folder.
3. **Scale, axis, pivot.** `get_bounds` against the size you expect. glTF and FBX through
   Interchange arrive in centimeters, Z up, pivot kept; OBJ arrives unconverted (below).
4. **Names and folders.** Rename into the convention (`AssetTools.move`, which leaves no asset at
   the old path) or stage the file under its target name before import. `destination_name` is
   ignored for meshes.
5. **Materials.** Generated materials are instances of engine parents or plain Materials: replace
   them with instances of the project master (scenario-unreal-materials), or keep them for a quick
   look only.
6. **Texture flags.** Read `SRGB`, `compressionSettings`, `LODGroup` on every map and fix packed and
   data maps (ORM, height) and anything wrongly detected as a normal map.
7. **Nanite, collision, LODs.** Interchange turns Nanite on and builds one convex hull; decide per
   asset class (`P.mesh_rules`), and count collision from `body_setup.agg_geom`.
8. **Provenance.**
   `AssetTools.update_metadata_tags {"set_tags": {"Source": "generated", "Reviewed": "no"}}` so
   review can find them later (run on 5.8.3).
9. **Look.** A screenshot next to a mannequin, under a neutral light rig
   (scenario-unreal-lighting-rendering): scale, pivot, normals, texture on the right slot.

## Meshes

### glTF and GLB (Interchange, through Python)

Run on 5.8.3, default stack, a two-node textured crate exported in meters, Y up, pivot at the base
and 0.3 m off-center:

| Aspect         | What landed                                                                                                                                                           |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Scale and axis | meters to centimeters, Y up to Z up, pivot kept (bounds min `[-20, -25, 0]`)                                                                                          |
| Meshes         | one static mesh per glTF node (`Crate_Part0`, `Crate_Part1`), not combined                                                                                            |
| Folders        | nested `<dest>/<file>/StaticMeshes`, `/Materials`, `/Textures`                                                                                                        |
| Names          | node names; `destination_name` on the task ignored                                                                                                                    |
| Materials      | `MaterialInstanceConstant` per glTF material, named after it, parent `/InterchangeAssets/gltf/MaterialInstances/MI_Default_Opaque`                                    |
| Textures       | `crate_texture_<n>`; base color sRGB; metallic-roughness and occlusion linear `TC_Default`; normal `TC_Normalmap` with `flip_green_channel` on, texture group `World` |
| Build          | Nanite on, one convex hull (`agg_geom.convex_elems` = 1), 1 LOD, one UV channel                                                                                       |

Fixes that ran on 5.8.3, all through a preset passed in `override_pipelines`
(`P.ensure_pipeline_preset`, then `P.import_source(path, folder, pipeline=...)`):

- **One mesh per file:**
  `mesh_pipeline.combine_static_meshes_behavior = InterchangeCombineStaticMeshesBehavior.ALL` gave
  one mesh `crate`, 100 x 50 x 200 cm. The older bool `combine_static_meshes` raises a
  DeprecationWarning.
- **Keep material instances with a custom preset:** duplicate
  `/Interchange/Pipelines/DefaultGLTFAssetsPipeline`, not `DefaultAssetsPipeline`. From the generic
  one, glTF materials became plain `Material` assets in a flat folder; from the glTF one, instances
  stayed (parent `/InterchangeAssets/Materials/PBRSurfaceMaterial_MR`) in the nested folders.
- **Nanite and collision decided later:** `mesh_pipeline.build_nanite = False` and
  `mesh_pipeline.collision = False` gave Nanite off and no convex hull.

### FBX

| Path                                                    | What landed (run on 5.8.3, Blender export with Apply Unit Scale, forward -Z, up Y)                                                                                                                        |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AssetImportTask` (Interchange)                         | centimeters, Z up, pivot kept; one mesh per node; flat folder; `destination_name` ignored; instances parented to `/InterchangeAssets/Materials/FBXLegacyPhongSurfaceMaterial`; Nanite on; one convex hull |
| MCP `StaticMeshTools.import_file` with `combine_meshes` | one mesh, 100 x 50 x 200 cm; `Material` assets (not instances) named after the slots; textures `Image_<n>`; Nanite off                                                                                    |

Skinned FBX (a two-bone Blender tube): the skeleton lands as `<name>_Skeleton`; the armature object
became an extra root bone (`Rig`, then `root`, `tip`); the MCP import with `create_physics_asset`
made no physics asset, the Interchange task made `<name>_PhysicsAsset` but the mesh's
`physics_asset` read None. Check `get_bone_names`, then hand the mesh to scenario-unreal-animation.
Assigning the physics asset (`SkeletalMeshTools.assign_physics_asset`) is [not yet run].

### OBJ

No unit or axis conversion on either path (run on 5.8.3): a 2 m box written in meters landed 1 x 2 x
0.5 units, lying along -Y. The task path turned Nanite on, built a convex hull and used
`WorldGridMaterial`; the MCP path named the slot `defaultMat`. An OBJ without `vt` lines triggered a
handled ensure in the OBJ translator (`UVs.IsValidIndex`), logged as errors, and still imported.
Prefer glTF or FBX from the generator; otherwise scale and rotate before use, and check
`get_bounds`.

## Textures

Run on 5.8.3, `AssetImportTask` and `TextureTools.import_file` alike:

| File                        | Landed as                                                         | Fix                                                                                                                                                                     |
| --------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| base color PNG              | sRGB, `TC_Default`                                                | none                                                                                                                                                                    |
| tangent normal PNG          | detected: `TC_Normalmap`, `TEXTUREGROUP_WorldNormalMap`, sRGB off | check the green channel convention (OpenGL from many generators: `flip_green_channel`)                                                                                  |
| packed ORM PNG              | sRGB **on**, `TC_Default`                                         | `SRGB` false, `compressionSettings` `TC_Masks` (ran through `ObjectTools.set_properties`)                                                                               |
| 16-bit height PNG           | sRGB on, `TC_Default`                                             | `SRGB` false and a single-channel compression [not yet run]                                                                                                             |
| equirect sky PNG (sky blue) | detected as a **normal map** (`TC_Normalmap`)                     | `compressionSettings` `TC_Default` first, then `SRGB` true (in the other order the compression change turned sRGB off again, run on 5.8.3), or import as a cube (below) |

A single PNG did take the task's `destination_name`. Fix through MCP:
`ObjectTools.set_properties {"instance": <t>, "values": "{\"SRGB\": false, \"compressionSettings\": \"TC_Masks\"}"}`
(a JSON string, reflected enum spellings); in Python, `P.apply_texture_role(tex, role)`.

## Skies and HDR images

| File                         | Default (run on 5.8.3)                    | With a texture-pipeline preset (run on 5.8.3)                                                                                                                         |
| ---------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Radiance `.hdr` equirect     | `TextureCube`, `TC_HDR_Compressed` (BC6H) | already a cube                                                                                                                                                        |
| `.exr` equirect              | `Texture2D`, `TC_HDR_Compressed`          | `TextureCube` with `material_pipeline.texture_pipeline.file_extensions_to_import_as_long_lat_cubemap = ["hdr", "exr"]`                                                |
| LDR PNG equirect, 1024 x 512 | `Texture2D`, wrongly a normal map         | `detect_long_lat_cubemap = True` alone: a `TextureCube` that is still `TC_Normalmap`; add `detect_normal_map_texture = False`: a `TextureCube`, `TC_Default`, sRGB on |

Long-lat detection needs an image at least 512 pixels high
(`Interchange.Textures.MinCubeMapDetection`, engine source 5.8.3). Importing an `.exr` with the same
base name as an existing cube in the same folder failed with "nothing to import" (run on 5.8.3):
give each sky its own name or folder. Using the cube in a Sky Light or an HDRI backdrop is
scenario-unreal-lighting-rendering's step [not yet run here].

## Audio

WAV (mono 48 kHz, stereo 44.1 kHz), MP3, OGG and FLAC each became a `SoundWave` with the right
duration, channel count and sample rate (run on 5.8.3, `AssetImportTask`), `looping` off,
`SOUNDGROUP_DEFAULT`. An ambience loop needs `looping` on and a seam check by ear [not yet run];
sound classes and attenuation belong to the game's audio setup.

## Headless commandlet: what it can and cannot do

Run on 5.8.3 with `ue_run.run_python` (plain commandlet, `-nullrhi` not needed for imports):

- **Can:** every import above, with the same results as a headless editor; presets duplicated with
  `AssetTools.duplicate_asset(name, folder, unreal.load_asset(source))`;
  `StaticMesh.get_num_lods()`; setting the `lod_group` property (it rebuilt 1 LOD into 4 for
  `LargeProp`); Nanite through the `nanite_settings` property; reading `body_setup.agg_geom`; Python
  validators and `EditorValidatorSubsystem.validate_assets_with_settings`.
- **Cannot:** `StaticMeshEditorSubsystem` is None; the deprecated `EditorStaticMeshLibrary` returns
  -1 for `get_lod_count`, `set_lods`, `add_simple_collisions` and `get_simple_collision_count`, and
  [] for `get_lod_screen_sizes`. Explicit LOD chains and added collision need an editor (MCP
  `generate_lods`, `generate_convex_collisions`, or the latent mode).
- **Registry:** a commandlet's registry misses `/Engine` and `/Interchange` content
  (`EditorAssetSubsystem.duplicate_asset` of `/Interchange/Pipelines/...` failed with an Error);
  `unreal.load_asset` finds it. In a headless editor, `AssetTools.get_dependencies` and
  `get_referencers` failed for assets made in the same session until
  `AssetRegistry.scan_paths_synchronous(paths, True)` (`references/mcp-pipeline.md`, P7).
- **Shaders:** no material compiles in a plain commandlet; a material check needs an editor or
  `-AllowCommandletRendering` (scenario-unreal-materials).
