# UE 5.8 traps that break remembered code and old tutorials

Load before writing Unreal code from memory, following a tutorial recorded before 5.8, or trusting a
doc page that still shows UE4 paths. Every line is old habit, then the 5.8 fact, then the source.
Source codes follow `sources/unreal-version-deltas.md` (rnXX = release notes of 5.X; py-ref, py-ed,
rc, mcp, mrq-cli, sub, mac-req and the others are the saved 5.8 doc pages). `[added]` = not stated
by a saved source; `[verify]` = check on the installed engine (the probe job
`tests/code/unreal-expert/jobs/job_00_probe.py` answers most of them).

## 1. Editor Python API

- **`unreal.EditorLevelLibrary.*` is the pre-subsystem API.** Use
  `unreal.get_editor_subsystem(unreal.EditorActorSubsystem)` for actors (spawn, list, select,
  destroy, duplicate, `convert_actors`), `LevelEditorSubsystem` for levels and PIE (`load_level`,
  `new_level(asset_path, is_partitioned_world=False)`, `save_current_level`,
  `save_all_dirty_levels`, `editor_play_simulate`, `editor_request_end_play`),
  `UnrealEditorSubsystem` for the editor world and primary viewport camera (py-ref; deltas, Python
  section). The old class may still run with deprecation warnings [verify with hasattr]. Epic's own
  5.8 samples still call it: the Python automation-test screenshot sample, the Control Rig samples,
  the Remote Control doc (tests; cr; rc).
- **`unreal.EditorAssetLibrary.*`: prefer `EditorAssetSubsystem`**, same operations (`list_assets`,
  `does_asset_exist`, `rename_asset`, `duplicate_asset`, `save_asset`, `delete_asset`,
  `find_package_referencers_for_asset`, `load_blueprint_class`). The 5.8 Python page still
  recommends the library (py-ed § Working with Assets), so both exist; subsystems are the direction.
- `EditorStaticMeshLibrary` becomes `StaticMeshEditorSubsystem`; `EditorSkeletalMeshLibrary` becomes
  `SkeletalMeshEditorSubsystem` [verify]; `EditorFilterLibrary.by_class` becomes `isinstance`
  (deltas, deprecated list).
- **Destructive calls with silent side effects** (5.8 API docstrings, py-ref): `load_level` closes
  the current level WITHOUT saving; `delete_asset`, `delete_loaded_asset(s)`, `delete_directory` are
  force deletes with no reference check, close asset editors and may clear the undo history;
  `consolidate_assets` deletes and saves; spawning selects the new actor; `get_all_level_actors`
  returns loaded actors only (World Partition cells not loaded are invisible).
- `AssetImportTask.result` is deprecated: use `task.get_objects()`. `destination_name` is ignored
  when Interchange handles the file: the name comes from the pipeline, so import into a per-asset
  folder and rename, or configure the pipeline (py-ref).
- `AssetTools.create_asset(..., overwrite_existing=False)` gained its overwrite flag in 5.8;
  `open_editor_for_assets` moved to `AssetEditorSubsystem` (py-ref; rn58-pipe).
- `@unreal.ufunction(ret=(a, b))` multi-returns are now packed in declared order (they came back
  reversed before 5.8); Optional properties read as None when unset; TraceType and ObjectType names
  were regenerated, old names are deprecated aliases (rn58-pipe § Scripting).
- Instantiating a BlueprintFunctionLibrary (`unreal.SomeLibrary()`) is deprecated since 5.5: call
  its classmethods. A Python-defined BlueprintFunctionLibrary exposed to Blueprint is no longer
  supported: use the Execute Python Script node (rn55; py-ed).
- Validators override `k2_can_validate`, `k2_can_validate_asset`, `k2_validate_loaded_asset` (old
  names deprecated), must call `asset_passes` on success, and Python validators must register
  themselves each session (py-ref). Scripted action utilities with empty SupportedClasses fail data
  validation in 5.8 (rn58-pipe).
- Slate tick callbacks for multi-tick work: use `unreal.register_ticker_callback` (5.7).
  `unreal.collect_garbage()` runs immediately and is commandlet-safe (5.6). Generated names changed
  from `lo_ds` to `lods` (5.6) (deltas, Python section).
- 5.8 opens Blueprint graph editing to Python through `unreal.BlueprintGraphEditor` and new
  `BlueprintEditorLibrary` functions (rn58 § Blueprint). The scope is [verify]: do not promise graph
  authoring before the probe confirms it.
- Asset Registry filters take class paths (`TopLevelAssetPath`, `ARFilter.class_paths`), not class
  names (UE 5.1 change, py-ref § AssetRegistryHelpers; added).
- Python 2 syntax in saved Epic samples (`print "x"`, `xrange` in the Datasmith and latent-test
  pages) is a syntax error in the embedded Python 3.11.8 (py-ed; dsm; tests).
- `unreal.Rotator` positional order is roll, pitch, yaw (run on 5.8.3: `Rotator(1, 2, 3)` has roll
  1, pitch 2, yaw 3): pass keywords. `ue_review._rot` does.
- **Found by running v0.1 in 5.8.3 (2026-10-21):** `unreal.ObjectRedirector` does not exist: detect
  redirectors by the asset registry class name `ObjectRedirector`.
  `LevelEditorSubsystem.set_level_viewport_fov(fov, viewport_config_key)` needs the key from
  `get_active_viewport_config_key()`. `Actor.add_component_by_class` is not exposed to Python:
  `SubobjectDataSubsystem.add_new_subobject` adds a component and it persists.
  `PostProcessVolume.settings` returns a copy: assign it back after editing; `exposure_offset` is an
  alias of `auto_exposure_bias`. A spawned DirectionalLight is already the atmosphere sun (index 0).
  `MoviePipelineQueueSubsystem`, `MoviePipelinePrimaryConfig` and `MovieGraphConfig` exist only when
  the `MovieRenderPipeline` plugin is enabled in the project. The commandlet can exit 1 after
  printing a good `UE_RESULT` envelope: the envelope is the verdict. Renamed cvar:
  `r.Shadow.Virtual.ShowStats` is now `r.Shadow.Virtual.Stats.Visible`.

## 2. Headless and command line

- `UE4Editor-Cmd` is `UnrealEditor-Cmd`; cook platform `WindowsNoEditor` and `MacNoEditor` are
  `Windows` and `Mac` (deltas § Command line). On Mac `UnrealEditor-Cmd` is at
  `Engine/Binaries/Mac/UnrealEditor-Cmd` (found on 5.8.3 from the Launcher); `ue_env.find_engine`
  falls back to `UnrealEditor.app/Contents/MacOS/UnrealEditor` with `-run=` when it is missing. Add
  `-nosound` to every unattended run; a full editor with `-RenderOffscreen` shows no window and
  takes no focus on macOS (checked), a plain `UnrealEditor ... -ExecCmds=` launch opens a window.
- `-ExecCmds="py script.py"` at startup is discouraged: it can run before the editor is ready. Use
  `-run=pythonscript -script=` (headless, loads NO level) or `-ExecutePythonScript=` (full editor,
  shuts down right after the script) (py-ed § The Command Line). `ue_run` mode `latent` still uses
  `-ExecCmds py`, but only to register a ticker that waits for warm-up ticks.
- The Python commandlet loads fewer modules than the full editor (Aaron Carlisle, 0guOMTiwmhk
  [01:23:04]) and the Asset Registry may still be scanning: call
  `unreal.AssetRegistryHelpers.get_asset_registry().wait_for_completion()` before any registry
  query, as the 5.8 batch-processor example does (rn58-pipe). `ue_run`'s boot does it before every
  job and records it as `registry_wait`; call `ue_run.wait_for_registry()` yourself in code sent to
  a just-launched editor.
- 5.8 enables source control before the PythonScript commandlet runs the script, because Python
  cannot enable it (rn58-pipe § Scripting Bug Fix) [verify with Perforce and with no provider].
- 5.5: a failing `-ExecutePythonScript` now logs an error "to match the commandlet behavior", and
  `-ScriptErrorsAreFatal` makes it fatal (rn55 § Editor > Scripting); `ue_run` adds the flag in mode
  `editor`. The boot catches job exceptions, so the verdict is the envelope: `ue_run` passes a job
  only on the `UE_RESULT` envelope carrying its job id, never on the exit code (v0.1 took the last
  `UE_RESULT` line in the log, so a job that printed its own "ok" and then crashed the engine
  passed).
- 5.6 lazy Python initialization: with `Engine.Python.IsEnabledByDefault` false, the commandlet and
  `-ExecutePythonScript` force-enable Python; otherwise pass `-EnablePython` (rn56 § Scripting).
- Cooking inside the editor process is deprecated in 5.7 and removed in 5.9: cook with the
  CookCommandlet or UAT. `-DDC=None` was removed in 5.8. Zen is the cooked output store by default
  for new 5.8 projects; where cooked data lands is [verify] (the packaging page still shows
  `Saved/Sandboxes/Cooked-<Platform>`). Set `[Zen.AutoLaunch] LimitProcessLifetime=false` for CI
  (rn57; rn58 § Developer Iteration). Incremental cook for content iteration:
  `BuildCookRun -cookincremental` (Experimental 5.6, Beta 5.7 and 5.8, against Zen); the packaging
  page only knows `-iterate` (deltas, Incremental and multi-process cook).
- Cook-time validation: `-RunAssetValidation -RunMapValidation -ValidationErrorsAreFatal`; without
  the last flag errors become warnings (rn54). `ue_run.build_buildcookrun` adds them. 5.8 adds
  `DataValidation.ReportCookValidationStats` (per-validator duration, on by default) and
  `DataValidation.LoadExternalObjectsForCookValidation` (on) (dval): they name the slow validator in
  a long cook.
- Source control from headless jobs: `ResavePackages` needs `-autocheckout` (`-autocheckin` for
  automated runs) under Perforce, or read-only files are not resaved (naming doc). OFPA changelists
  must be validated and submitted from inside the editor: partial submits leave dangling references,
  and changelist support requires Perforce (World Partition doc, Using OFPA With Source Control).
  Content a builder regenerates on CI, such as PCG partition actors, is not checked in (TbNZ4GKaTow
  [00:26:23]).
- Profiling: the Session Frontend profiler and `stat startfile` are legacy; Unreal Insights plus
  `-trace=` channels; 5.8 adds `TraceQuery` (utrace to JSONL) and `snapshothitches -start`
  (Saved/Profiling/Hitches, needs `stat default`) (rn58 § Insights, Dev Tools). Set cvars at launch
  with `-DPCVars=` (applies before init, can override read-only cvars), not `-ExecCmds` (C-AjCqjKRSs
  [00:14:13]). 5.8 adds World Partition Insights (Spatial Profiler tab, trace channel
  `WorldStreaming` [verify]) for per-cell streaming cost (Looman part 2). When instrumentation
  cannot explain a hitch, add a sampling profiler: sampling is Beta inside Insights since 5.7; the
  talk's standalone samplers (PIX, Superluminal) are Windows tools [added] (C-AjCqjKRSs [00:17:30]
  to [00:18:58]).

## 3. Remote Control and MCP

- **Remote Control server is off until started**: `WebControl.StartServer` (or
  `WebControl.EnableServerOnStartup`); off in packaged and `-game` builds unless
  `-RCWebControlEnable -RCWebInterfaceEnable`; binds 127.0.0.1; HTTP 30010, WebSocket 30020 (rc).
- **5.8: remote UFUNCTION execution is disabled by default**, re-allowable in Remote Control project
  settings, with an allow list (rn58 § Motion Design, Virtual Production). Every 2022-era
  `/remote/object/call` example fails on a fresh 5.8 project. The refusal reads "not allowed by
  remote control settings (see 'Custom Allowed Remote Function Calls' or 'Allow Any Remote Function
  Call')" (HTTP 400, run on 5.8.3). Property reads and transactional writes through
  `/remote/object/property` worked.
- Remote Control uses C++ names (`bSweep`, not `Sweep`), needs public EditAnywhere properties in the
  editor (BlueprintVisible in PIE and -game), calls static functions on the CDO
  (`/Script/Module.Default__Class`, Python classes at `/Engine/PythonTypes.Default__Class`), and PIE
  objects carry a `UEDPIE_N_` map prefix (rc). 5.5 made per-preset transactions and change events
  opt-in and added an option to block console commands over the web API (rn55).
- **Epic Unreal MCP is Experimental** (plugin `ModelContextProtocol`); it has no tools alone: enable
  `AllToolsets`, which pulls in `EditorToolset` (Epic's webinar called the Editor Toolset "missing
  from the online documentation", k0tgmrBuIJc [00:06:00]; on 5.8.3 nothing extra is needed). Auto
  Start Server is false by default; `127.0.0.1:8000/mcp`, HTTP and SSE only, no auth; Tool Search is
  on and `tools/list` returns exactly three tools (`list_toolsets`, `describe_toolset`, `call_tool`,
  1,377 bytes). Run on 5.8.3 with AllToolsets: 52 toolsets, 830 tools. Calls from separate sessions
  run concurrently (four parallel 2 s scripts finished in 2.2 s; v0.1 said "serial on the game
  thread", which was wrong): serialize calls that depend on each other. `describe_toolset` payloads
  are large: Niagara system 112,601 tokens, Sequencer 42,010, Control Rig 27,990, Blueprint 25,646,
  UMG 20,561, PCG 12,246 (estimates at 4 bytes per token). `ProgrammaticToolset.execute_tool_script`
  is a sandbox (imports only json, math, re, time, datetime, copy; no `unreal` module): it batches
  `execute_tool(fully_qualified_name, json_string)` calls inside a `run()` function and is not a way
  to run editor Python.
- **A port freed by a hard-killed editor can refuse to bind again** ("HttpListener unable to bind"):
  use a new `-ModelContextProtocolPort` for each launch. A headless
  `UnrealEditor-Cmd -ModelContextProtocolStartServer ... -nullrhi -unattended -nosound` listens
  about 30 s after the launch.
- **Python Remote Execution on macOS needs bind address 0.0.0.0 in the editor and the client.**
  Epic's default `127.0.0.1` finds no editor there (an editor socket bound to one unicast address
  never receives datagrams sent to the multicast group). `ue_env.enable_remote_execution(project)`
  writes the editor side, `ue_remote.PythonRemote` the client side (run on 5.8.3 with Epic's
  `remote_execution.py` and with our fallback client). Without multicast:
  `ue_env.install_python_toolset(project)` adds `run_python` to the MCP server (a project-local
  `unreal.ToolsetDefinition`, registered from `Content/Python/init_unreal.py`; opt-in and unsafe).
- `[HTTPServer.Listeners] DefaultBindAddress=0.0.0.0` (the RC LAN recipe) is read by the MCP
  listener too, so it likely exposes the unauthenticated MCP server [added inference, verify with
  `ue_remote.loopback_only(8000)`].
- Community MCP servers: chongdashu/unreal-mcp is unmaintained since April 2025; prebuilt bridge
  binaries are engine-version locked; Monolith listens on all interfaces (mcp-comm). Install none
  without the user's approval.
- The 5.7 in-editor AI Assistant panel is not an MCP server (rn57).

## 4. Rendering defaults an agent must read before acting

- **Substrate**: Production Ready and on by default for NEW projects since 5.7; projects upgraded to
  5.7+ keep the legacy path until Project Settings > Rendering > Substrate materials is enabled
  (restart). Read `r.Substrate` in `Config/DefaultEngine.ini` (`ue_env.read_ini_value`) before
  authoring. Substrate materials render black with Substrate off; "Convert to Substrate" is one-way;
  the Slab has no Metallic input (Diffuse Albedo, F0, F90); the default GBuffer is Blendable;
  Adaptive needs SM6 on Mac; the Substrate page lists Mac among paths with known issues; the Path
  Tracer page still calls Substrate experimental (sub; rn57; deltas Conflicts 4).
- Global illumination: Lumen; Lumen Lite at Medium scalability is Beta in 5.8; Ray Tracing GI
  removed (5.4); SSGI deprecated (5.8); Lumen mesh SDF detail tracing deprecated
  (`r.Lumen.TraceMeshSDFs 0` default since 5.7). Projects converted from UE4 keep their old renderer
  settings: read `r.DynamicGlobalIlluminationMethod`, `r.ReflectionMethod`,
  `r.Shadow.Virtual.Enable` first [added] (deltas, Lighting).
- MegaLights is Production Ready in 5.8 (Experimental 5.5, Beta 5.7); the sun stays on deferred plus
  VSM unless `r.MegaLights.DirectionalLights 1` (ml).
- Static lighting is off in new templates (`r.AllowStaticLighting=False`, 5.5): UE4 "Build Lighting"
  steps do not apply (rn55).
- Exposure: EV100 with "Extend default luminance range", "Exposure Compensation" (not "Exposure
  Bias"), `r.EyeAdaptation.Focus` removed (4.25). The viewport EV100 override bypasses the post
  process volume, so screenshots taken with it do not match the game view (expo).
- 5.8 unified cached-lighting pre-exposure as `r.EyeAdaptation.CachedLightingPreExposure` (default
  4); guides naming `r.Lumen.CachedLightingPreExposure` or
  `r.SkyLight.RealTimeReflectionCapture.PreExposure` are stale. The editor now shows an on-screen
  warning when exposure leaves the supported range and lighting would clip (5.6 moved Lumen's cached
  range; the console help on 5.8.3 gives -8 to 12 at the default of 4, run on 5.8.3 by the lighting
  agent): look for it after every render and screenshot, and grep the log (expo; lighting digest,
  exposure range guard; exact warning text [verify]).
- Deprecated cvars now ensure, warn or assert when used (5.8) (rn58 § Core): do not set cvars from
  memory; read the list in the domain skill.

## 5. Movie Render Queue and Movie Render Graph

- MRG is Production Ready in 5.8 and "new features will be graph-only"; MRQ presets are legacy; the
  5.8 queue defaults to a "Basic" config type; Quick Render exists since 5.6 (rn58 § Production
  Rendering Pipeline; rn56). The saved MRG page still shows "Movie Render Graph (Beta)" [verify the
  menu label].
- `MoviePipelineMasterConfig` is `MoviePipelinePrimaryConfig`; graph jobs use
  `job.get_graph_preset()` / `set_graph_preset()`, not `get_configuration()`; keep the PIE executor
  referenced (module-level); callbacks subclass `unreal.MovieGraphScriptBase`; the 5.8 Execute
  Script node needs "Editor Only" mode for Python (mrq-cli; rn58).
- Command line: `-LevelSequence=<seq> -MoviePipelineConfig=<Primary Config preset>` or
  `-MoviePipelineConfig=<saved queue>`, with `-game`; the legacy Render Movie arguments are gone
  (mrq-cli). End frames are exclusive (0 to 50 renders 0 to 49). The path tracer in MRQ ignores the
  PPV samples per pixel (spatial x temporal samples instead) (seq-tips; pt).
- Mac output: the H.264 node is Windows only; ProRes on Mac conflicts between sources [verify]
  (rn56; mrg). Disable the tone curve for EXR output or the grade is baked in (Bardoux, MjjkWH0eT3U
  [00:37:22]).
- Game Overrides act invisibly: legacy MRQ configs apply them even when the setting was never added;
  in MRG only while the Global Game Overrides node is connected. They are the first suspect when a
  render differs from the viewport (William Faucher, fVg5ihB8Wdc [00:03:33]; rendering digest,
  consensus 6 and delta 7; MRG doc, Globals).
- Command-line renders take `-notexturestreaming`, present in every example of the MRQ command line
  doc (`ue_review.build_render_command` adds it). Unattended multi-shot renders need a farm manager
  (Deadline for Unreal): a crash in plain MRQ loses the queue (Glitch Productions, uzTo5vQchkk
  [00:40:14]). A PIE executor that is not kept in a global reference can be garbage collected
  mid-render (mrq-cli).

## 6. Mac

- 5.8 renders on Apple Silicon only (Intel rendering removed). Lumen SWRT and TSR on M1+; Nanite and
  VSM Beta on M2+; Lumen HWRT and MegaLights Experimental on M2+; path tracing through Metal ray
  shaders with macOS 26.4 or later advised (mac-req; rn58 § All Apple). Check the machine with
  `ue_env.preflight()` before relying on any of these.
- Xcode: Epic's macOS page says 26.0 minimum, 26.1.1 recommended, 26.4 not compatible; the 5.8 SDK
  table disagrees (Xcode 15.x for macOS hosts); this Mac has Xcode 26.6, which neither lists. A C++
  or code-plugin build is [verify] (mac-req; rn58; deltas Conflicts 1). Blueprint-only projects need
  no Xcode.
- Docs use `UnrealEditor-Cmd.exe`, `RunUAT.bat`, `C:\` paths and Ctrl shortcuts: on Mac use the
  binaries under `Engine/Binaries/Mac`, `RunUAT.sh`, POSIX paths, and usually Cmd [verify] (uat;
  added). DX11, DX12 and Vulkan cvars and tips do not apply: Metal only. RenderDoc does not support
  Metal: use Xcode's Metal debugger [added]. Unreal Insights memory callstacks are not listed for
  Mac (ins).
- Keep the Unreal project in a path without spaces (Allar 2.1.2): this project's folders contain
  spaces [added suggestion; verify whether spaces break cook or UAT]. The toolkit stages its own
  jobs in a space-free folder regardless.
- A MacBook keyboard has no numpad: the Gameplay Debugger's category keys (Abilities on numpad 3)
  need rebinding (tranek GAS guide 6.2, cited in deltas § GAS). Sampling profiler on Mac:
  Instruments Time Profiler [added].

## 7. First-run checklist for the toolkit (run 2026-10-21 on 5.8.3: items 1, 2, 4 and 5 answered, results in `tests/arena/V1_LIVE_FINDINGS.md`; item 3 partly)

1. `python3 ue_env.py --find`: engine root, version 5.8.x, which `editor_cmd` exists.
2. `tests/code/unreal-expert/run_all.sh --live` with `UE_TEST_PROJECT` set: probe (commandlet and
   editor), protocol, planted error, audit, latent review. Read
   `archive/tests/scenario-unreal-expert/<stamp>/results/test_ue_live.py314.json` and
   `live/probe_*.json`.
3. Confirm or correct: `-abslog=` and `-stdout` on Mac; UE's Mac launcher quoting of argv with
   spaces; `-ExecCmds=py` plus ticker in mode `latent`; `SystemLibrary.quit_editor`;
   `AutomationLibrary.take_high_res_screenshot` keywords and where the file lands;
   `executor.execute(queue)` on a transient queue; graph variable override API; the Rotator order;
   `get_console_variable_string_value`.
4. `run_all.sh --remote` (PREPARE=1 once): MCP health and loopback, PythonRemote discovery (run live
   2026-10-21 with bind 0.0.0.0, see toolkit-map), Remote Control 5.8 call refusal and its setting
   names (confirmed live), the toolset plugin identifiers (confirmed: ModelContextProtocol,
   AllToolsets, EditorToolset, RemoteControl).
5. `ue_run` v0.2: a planted boot failure in mode `editor` exits non-zero with
   `-ScriptErrorsAreFatal`; `AssetRegistry.wait_for_completion` exists (else the
   `search_all_assets(True)` fallback); an editor opened from the Launcher and from the Finder shows
   its `.uproject` in `ps -axo pid=,command=` (the write-lock check depends on it); the
   exposure-range warning text, to grep it.

## 8. Version changes in other domains that the blind test caught

Listed here because code written from memory hits them; the owner skill carries the procedure.

- scenario-unreal-materials: a Blendable GBuffer is a ceiling (every platform becomes Blendable, SM6
  included), Adaptive falls back per platform (5.7; material updates note). 5.8 compiles only
  connected, non-zero outputs (`r.Material.UseShaderCompilationParameters`), so "delete the node to
  strip shaders" is obsolete (wobQ8ZKQpbc [00:13:13]). Static Component Mask Parameter is obsolete:
  Channel Mask Parameter, or a dot product with a float3 of 1s and 0s (wobQ8ZKQpbc [00:42:35]). The
  Temporal Responsiveness node (5.7) is Experimental and needs
  `r.Velocity.TemporalResponsiveness.Supported=1`; sampler type errors after a texture swap: Clean
  Graph > Fixup Mismatched Samplers (5.7) (material updates note).
- scenario-unreal-world-building: `landscape.ForceLayersUpdate` is deprecated in 5.8: use the
  command `landscape.ForceLayersFullUpdate` (rn58 via deltas).
- scenario-unreal-performance: VSM receiver masks are the default for directional lights since 5.7;
  5.8 adds `r.Shadow.Virtual.DeferredInvalidationBudget`; 5.7 adds experimental `r.Nanite.PrimeHZB`
  passes against the camera-cut GPU hitch (optimization digest; Looman part 2).

## 9. Import and asset traps found by running the pipeline and materials skills (run on 5.8.3, 2026-10-21)

The owner skills carry the procedures; these are the ones an agent hits before it opens a skill.

- Interchange glTF and FBX arrive in centimeters, Z-up, with Nanite on, one convex hull and one mesh
  per node; `destination_name` is ignored for meshes (they land in `<dest>/<name>/StaticMeshes/`).
  OBJ arrives unconverted. `StaticMeshTools.import_file` takes only FBX and OBJ and refuses glTF;
  the legacy GLTFImporter plugin is not in 5.8.
- A preset duplicated from `DefaultAssetsPipeline` turns glTF materials into plain Materials;
  duplicate `DefaultGLTFAssetsPipeline` to keep material instances. In a commandlet duplicate with
  `AssetTools.duplicate_asset` (`EditorAssetSubsystem.duplicate_asset` fails on plugin content).
- Texture intake: an ORM map lands with sRGB on; an LDR equirectangular sky is detected as a normal
  map; `.exr` becomes a cube only when the preset lists it.
- A commandlet's asset registry does not know `/Engine` or `/Interchange` content: load those by
  path. `get_dependencies` and `get_referencers` fail for assets created in the same session until
  the registry rescans, and no toolset tool triggers a rescan; use the Python registry call or a
  second process.
- Mesh facts: there is no mesh subsystem in a commandlet. Read LODs with `get_num_lods` and
  collision from `body_setup.agg_geom`; `get_simple_collision_count` reads 0 in the editor and -1 in
  a commandlet. Setting `lod_group` rebuilds LODs even in a commandlet. An OBJ without UVs logs an
  ensure.
- `ProgrammaticToolset` scripts cannot `import unreal`: batch toolset calls there, run Python
  through a channel that has `unreal`.
- The arena base project logs a GameFeatureData error at startup, which makes `DataValidation` and
  the exit code of any commandlet report failure while the script succeeded. Judge by the output
  file, as in section 2.
- `ue_run` makes the `.uproject` path absolute (a relative one resolves against
  `Engine/Binaries/Mac`); keep log and boot paths free of spaces, since quoting of `-abslog=` with
  spaces is still **[not yet run]**.

## 10. Epic MCP tool traps found while writing the cinematics and VFX recipes (run on 5.8.3, 2026-10-21)

Signatures are in `mcp-toolsets.md` and each domain's `mcp-<domain>.md`; these are the surprises
behind them.

- `SequencerTools.add_actors` returns `[]` until the sequence is open (`open_sequence`), then binds.
  It creates a transform track with one infinite section whose defaults are the actor's location. A
  second transform track or section overlaps that one and is weight-blended with it, so the keys
  read right and the played path is wrong (a path keyed -1000 to 1000 played as -1000, 8, 1000 only
  after the extra track was removed). Read the evaluated transform at several frames, not the keys.
- `SequencerTools.set_camera_cut_binding` builds `unreal.Guid(str)`, which 5.8.3 rejects. Set
  `CameraBindingID` through `ObjectTools.set_properties` instead.
- Two `unreal.Guid` objects for the same id are not `==` in 5.8.3 Python: compare `to_string()`.
- `EditorAppToolset.CaptureViewport` wants its "optional" `captureTransform` and `annotations`
  passed. An offscreen editor's viewport is 424 x 40, so a capture without a camera follows that
  size; set the camera and resolution first.
- A Niagara `GetStackIssues` call refuses to run while a compile is in flight: wait until
  `bIsCompiling` is false. Setting a user parameter with a wrong type silently adds a stray
  override; check the name and type first.
- In a commandlet, plugin content needs `scan_paths_synchronous` before it is found, and the 57
  Niagara templates need `scan_paths` first.
- Duplicating `/Engine/Maps/Entry` with AssetTools gives a level that cannot be saved; create the
  level with `new_level` in a commandlet.
- The cvar is `r.HeterogeneousVolumes.Allowed`; the `fx.Niagara.Debug.*` names are console commands,
  not cvars. Search cvars with `SearchCVars` rather than scanning the console log.
- Inside an `execute_tool_script` script, a failing `execute_tool` call stops the whole script with
  that error; `try` does not catch it. Keep a call that is expected to fail (a compile check, a
  refused import) as its own `call_tool`. Keys of one `ObjectTools.set_properties` apply in order:
  moving a texture off `TC_Normalmap` turns sRGB back off, so set compression first and sRGB after.
- A cvar exists only if `ConsoleHelp` knows it exactly; `SearchCVars` matches prefixes and returns
  near misses. Check the exact name before setting it.
- Scripted screenshots: the HDR capture is taken after tone mapping, so for linear data use
  `r.BufferVisualizationDumpFrames`; `viewmode` commands do not change a scripted shot, use ShowFlag
  overrides. `ProfileGPU` now prints a box-drawn table and may open a window: run it only in an
  editor you started offscreen.
- `set_properties` that grows `PerInstanceSMData` leaves the last new instance at the actor origin
  while the count looks right; write the array a second time and read positions back, not just the
  count. Actor bounds include a phantom 256 cm box around an empty root, so audit placement from
  instance transforms. A duplicated map cannot be saved with `save_assets`.
- Niagara: a broken HLSL expression written right after a switch-enum change was seen once never to
  compile and to save as UpToDate. After an edit, confirm `bIsCompiling` went true before saving,
  then read the compile state. Editor Python sees no emitter handles or scripts of a Niagara system,
  only names and renderer materials; no Niagara tool creates a level. `load_level` refuses while the
  open level has unsaved changes. A refused toolset call inside `execute_tool_script` fails the
  script even in try/except.

## 11. Traps from the performance, gameplay and animation upgrades (run on 5.8.3, 2026-10-21)

- Performance data: with the launcher editor binary and `-game`, CSV profiles and hitch snapshots
  land in the engine's per-user Saved folder, not the project's; the log names the file.
  `GPU/<pass>` CSV columns need `r.GPUCsvStatsEnabled=1`; draw-call counters read 0 on Metal.
  `snapshothitches` needs `stat default` or `stat game`. `TraceQuery` is not in the launcher build:
  read `.utrace` files through the UnrealInsights command line. Renamed or gone:
  `r.ShaderPrintEnable` is now `r.ShaderPrint`; `r.Shadow.Virtual.ShowStats` is replaced by
  `r.Shadow.Virtual.Stats.Visible` (typing the old name fires an ensure);
  `r.Nanite.ShowMeshDrawEvents` is gone.
- `AutomationTestToolset.RunTests` blocks until done, and a test that creates a world crashed a
  `-nullrhi` editor. `merge_actors` ignores `name`. `spawn_actor_from_object` returns None in a
  commandlet. `GetLogEntries` needs `"category": ""`.
- Blueprint DSL: members of a Blueprint made in the same session are not listed by
  `find_node_types`; write `Class|BPHero|GetCoins` (the Blueprint name without underscores). A
  function with the same name in a second Blueprint binds to the first one's; `read_graph_dsl` can
  print the wrong class name. Integer add is `(+ a b)` or `Utilities|Operators|Add`, which reads
  back as `Math|Integer|int+int` (not writable). A trigger's radius scales with its parent's
  smallest axis.
- Sequencer Control Rig needs the sequence open and returns true for unknown control names, so check
  the control exists first. A Control Rig bake through `export_anim_sequence` holds one pose at
  every frame, headless and offscreen: key agent-made clips directly with a keyed sequence.
- PIE runs headless (a coin pickup test went from 0 to 3 in a headless PIE); Control Rig is not
  evaluated there for a bake.
