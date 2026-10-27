---
name: scenario-unreal-expert
description: "Use when an agent drives Unreal Engine 5.8 on a Mac for any task: editing a project through Epic's Unreal MCP toolsets (list_toolsets, describe_toolset, call_tool), Editor Python in a headless or open editor, Remote Control, console commands and cvars; when a call or script breaks on 5.8 (huge describe_toolset payloads, execute_tool_script has no unreal module, Python Remote Execution finds no editor, EditorLevelLibrary, Substrate materials black); when work must be judged by numbers and a screenshot before it is called done; when generated assets must land in a project; or when a brief must go to the right scenario-unreal-* specialist. Works with Epic's own skills and the Scenario for Unreal plugin."
license: MIT
---

# Unreal expert (technical director and agent protocol)

Expert Unreal work is a loop run against numbers: set the budget, build one stage, measure it, look
at it, fix it, then advance. An agent without a mouse gets there by choosing the right channel for
each action, working like the Details panel (one transaction, explicit saves), paying for as little
tool schema as the task needs, and never trusting its own eyes alone. This skill is the protocol,
the shared toolkit in `scripts/`, and the map to the team. Target: UE 5.8 on macOS Apple Silicon. If
a sibling skill named here is missing from your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.

**Status (2026-10-21):** run live on UE 5.8.3 (macOS 26.5, Apple silicon): the MCP catalog (52
toolsets, 830 tools), Python Remote Execution, the project-local Python toolset, headless and
offscreen editor launches, screenshots, Remote Control, and the job protocol. Code in `references/`
that did not run is marked **[not yet run]**.

## 1. Pick the channel (details: [`references/channels.md`](references/channels.md))

| You need                                                                                                                                                    | Use                                                                                                                                                                                                                                                                                                                                                                    |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| structured edits an Epic toolset covers (actors, assets, material graphs and instances, Blueprints, UMG, Sequencer, PCG, Niagara, tests, logs, screenshots) | **Epic Unreal MCP**, section 2                                                                                                                                                                                                                                                                                                                                         |
| loops, audits, anything toolsets lack, with an editor open                                                                                                  | **Python in the running editor**: [`ue_remote.PythonRemote`](scripts/ue_remote.py) after [`ue_env.enable_remote_execution(project)`](scripts/ue_env.py) (on macOS and Linux it binds 0.0.0.0, which lets any host on the local network run code: say so first), or `ue_env.install_python_toolset(project)` for a `run_python` tool on the MCP server (opt-in, unsafe) |
| audits, imports, batch edits, validation, no editor open                                                                                                    | **headless commandlet**: [`ue_run.run_python(uproject, script)`](scripts/ue_run.py)                                                                                                                                                                                                                                                                                    |
| a rendered frame without a window                                                                                                                           | an editor you own: `ue_run.launch_editor(uproject, mcp_port=N, mode="offscreen")`, or `ue_run.run_python(..., mode="latent")`                                                                                                                                                                                                                                          |
| property batches on known objects, presets                                                                                                                  | Remote Control (calls refused by default in 5.8)                                                                                                                                                                                                                                                                                                                       |

Rules that hold for every channel: check `ue_run.editor_processes()` first and never start a second
editor on a project that is open; never kill or relaunch an editor you did not start; no windows and
no sound (the toolkit adds `-RenderOffscreen -nosound`); a new MCP port per launch; state on disk is
the truth, so save before stopping an editor.

## 2. Epic MCP protocol (5.8: Unreal MCP plus All Toolsets)

`tools/list` shows three meta-tools: `list_toolsets`, `describe_toolset(toolset_name)`,
`call_tool(toolset_name, tool_name, arguments)`. A bare `describe_toolset` is paid in tokens
(Niagara system 112,601, Sequencer 42,010, Control Rig 27,990, Blueprint 25,646, UMG 20,561, PCG
12,246; most others under 9,000). So:

1. **List once, then read the engine's own skill for the domain.** `list_toolsets` (names and
   one-line purposes). Then `ToolsetRegistry.AgentSkillToolset`: `ListSkills`, and
   `GetSkills(skillPaths=[...])` for the skill that matches the task. 5.8 ships in-editor skills for
   Niagara, PCG, Blueprints, materials, outdoor lighting and Dataflow. Their text is the engine's:
   read it, do not copy it. When Epic's own Claude Code plugin is installed, follow its MCP skill
   for the protocol and use this one for craft, budgets and checks.
2. **Signatures first.** [`references/mcp-toolsets.md`](references/mcp-toolsets.md) lists every
   toolset with its owner skill and common struct shapes; each specialist's
   `references/mcp-<domain>.md` has the call signatures. Call `describe_toolset` only for a toolset
   you cannot find there, and never on the large ones to browse. Regenerate the references after an
   engine update ([`ue_mcp.snapshot`](scripts/ue_mcp.py),
   [`gen_toolset_map.py`](scripts/gen_toolset_map.py)).
3. **Pass references as the engine returned them.** Object arguments are
   `{"refPath": "<path from a previous call>"}`; struct shapes are in the common-struct list.
   Results come as `{"returnValue": ...}`; errors have `isError: true` and a reason. Read
   `LogsToolset` before retrying a call that failed without a clear message.
4. **Batch.** Four or more toolset calls in a row go through one script (arena, run on 5.8.3: 13
   turns batched against 66 one call at a time for the same material kit). `ProgrammaticToolset`:
   call `get_execution_environment` once, then `execute_tool_script`. The sandbox script defines
   `run()` returning a dict and calls `execute_tool(fully_qualified_tool_name, json_string)`; it
   imports only `json, math, re, time, datetime, copy`, so there is no `unreal` module and no file
   writing (`get_execution_environment` says what else it allows). Use it for N similar calls in one
   round trip; use Python (section 1) for logic that needs the engine API.
5. **Save and verify from disk.** `AssetTools.save_assets` (and the level) before any stop; read the
   result back with `ObjectTools`, `SceneTools` or `ActorTools`; check logs; capture a frame
   (`EditorAppToolset.CaptureViewport` or [`ue_review.screenshot`](scripts/ue_review.py)) and run
   `ue_review.image_checks`. Calls from separate sessions run concurrently: serialize calls that
   depend on each other.
6. **When no toolset covers it**, switch channel (section 1) after the same error twice instead of
   looping. Material graphs, Blueprint graphs and Niagara modules have toolsets; landscape
   sculpting, foliage painting and Fracture Mode have none.

## 3. The expert loop

**Name the engine call behind every toolkit call**, in plans as in reports: a reader without
`scripts/` must be able to check each step. Write `ue_review.screenshot(p, 1920, 1080)`
(`AutomationLibrary.take_high_res_screenshot`, fallback `HighResShot 1920x1080`), cvars and console
commands literally, and close with **Verified** (what ran, with the number, log line or frame that
proves it) and **Assumed** (not run in Unreal, [verify] names, defaults taken). Mapping and
template: [`references/toolkit-map.md`](references/toolkit-map.md).

1. **Brief in numbers.** Platform and device class; frame budget in ms per thread and GPU (16.67 at
   60 fps, 33.3 at 30; Ari Arnbjornsson, GuIav71867E [00:03:53]); output resolution and upscaler;
   scale (world size, actors, NPCs); gameplay or cinematic; references. When silent, take the domain
   skill's default and write it down.
2. **Preflight.** `ue_env.preflight()` (chip, macOS, Xcode), `ue_env.find_project()` (plugins, path
   spaces), and the project settings that change the plan: `r.Substrate`, Lumen, VSM, Nanite,
   hardware ray tracing (`ue_env.read_ini_value`, or the probe). A bare project is not "new project"
   defaults: `r.Substrate` reads 0 without config. Upgraded projects keep old renderer settings.
3. **Build one stage** with small idempotent steps: get-or-create by path, mark what you create, one
   transaction per logical operation, explicit saves.
4. **Measure.** [`ue_audit.verdict`](scripts/ue_audit.py) for content; `stat unit` to classify
   (Frame, Game, Draw, GPU, RHIT), then Insights (lean capture for "are we on budget", rich with
   `-statnamedevents` for "why", about 20% overhead, C-AjCqjKRSs [00:11:27]);
   [`ue_stat.budget_check`](scripts/ue_stat.py) on CSV profiler or TraceQuery JSONL. Profile a
   cooked Development or Test build on target hardware; this Mac is a proxy for a console. Measure
   before any rewrite (VMZftEVDuCE [00:16:33]).
5. **Look AND check.** Screenshots from fixed camera bookmarks or an MRG still, opened with the
   image reader, plus `ue_review.image_checks`: Epic's lighting agent approved an all-white frame
   (lDf_y-YPELo [00:17:29]), and an empty map screenshots as all black. `review_images` gives flags
   and a contact sheet in one call. Judge with the domain skill's `references/critique.md`. After a
   render, look for 5.8's on-screen exposure-range warning; an MRG frame that differs from the
   viewport: suspect Game Overrides first (fVg5ihB8Wdc [00:03:33]).
6. **Fix before advancing**, one change at a time, with `ue_review.compare` for before and after
   parity from the same views.
7. **Deliver with evidence**: saved assets and levels, audit and stat JSON, the frames you looked at
   with their checks, the Verified and Assumed lists.

Never report a level, material, shot or build as done without numbers and a frame you looked at.

## 4. Generated assets and the Scenario plugin

Assets made with Scenario (through the Scenario MCP or the Scenario for Unreal plugin,
https://github.com/scenario-labs/unreal-plugin) arrive as GLB or FBX meshes, PNG or EXR textures,
equirectangular skies and audio. They are finished in this team's skills, not in the generator:
scale and axes on import, texture roles and sRGB flags, collision, LODs and Nanite, naming and
folders. Route them to `scenario-unreal-pipeline-automation` (import and validation), then
`scenario-unreal-materials` (PBR hookup, masked or packed maps),
`scenario-unreal-lighting-rendering` (skies, HDRIs) or `scenario-unreal-world-building` (placement).
With the plugin installed, the `scenario-unreal` skill covers its local MCP server (price, generate,
import, place, save). Generation spends credits: quote first (`estimate_cost`), tell the user the
price, and ask before `generate`. The plugin asks for approval in the editor only when 'Approve each
spend here' is on (off by default), or when the call comes through Epic's Unreal MCP (toolset
`ScenarioToolsets.ScenarioToolset` on 5.8). Read its tool results before polishing: they say what
was imported and where. Intake rules and what a commandlet can and cannot import:
`scenario-unreal-pipeline-automation/references/generated-assets.md`; generated skies:
`scenario-unreal-lighting-rendering/references/generated-skies.md`.

## 5. Persona pipelines

| Brief                      | Chain                                                                                                                                       | Deliverable                            |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| Open world or level        | scenario-unreal-world-building, scenario-unreal-materials (landscape, RVT), scenario-unreal-lighting-rendering, scenario-unreal-performance | streamed level, HLODs, budget report   |
| Material kit               | scenario-unreal-materials, then scenario-unreal-lighting-rendering (test bench), scenario-unreal-performance (shader cost)                  | masters, instances, permutation audit  |
| Lit interior or hero still | scenario-unreal-lighting-rendering (scenario-unreal-materials for emissives), scenario-unreal-cinematics for MRG output                     | gameplay lighting at budget, EXR still |
| Gameplay prototype         | scenario-unreal-gameplay, scenario-unreal-animation, scenario-unreal-vfx for abilities, scenario-unreal-performance                         | playable map, automation tests         |
| Character from Maya        | scenario-unreal-pipeline-automation (import), scenario-unreal-animation, scenario-unreal-gameplay                                           | retargeted, locomotion-ready character |
| Trailer                    | scenario-unreal-cinematics (scenario-unreal-animation, scenario-unreal-lighting-rendering)                                                  | Sequencer shots, reviewed renders      |
| VFX or destruction         | scenario-unreal-vfx, scenario-unreal-performance                                                                                            | systems within budget                  |
| Batch import and build     | scenario-unreal-pipeline-automation, scenario-unreal-performance (packaging)                                                                | report, validated package              |
| Frame-rate rescue          | scenario-unreal-performance, routing fixes to owners                                                                                        | proof capture, parity frames           |

**Handoff contract:** saved assets in a named folder, the `ue_audit.verdict` for the receiver's
profile with no error, stat or trace numbers when performance matters, the frames the sender looked
at with their `image_checks`, each toolkit call with its engine call, and the Verified and Assumed
lists. Units are centimeters, Z-up. Sister teams: scenario-maya-expert (1 unit = 1 cm, Y-up in
Maya), scenario-zbrush-expert, scenario-blender-expert (FBX through scenario-blender-export);
scenario-3d for generated meshes to finish.

## 6. Shared toolkit (`scripts/`)

Import: `import sys; sys.path.insert(0, "<this skill>/scripts")`. `PythonRemote.call` adds that
folder in the editor for one call.

- `ue_env.py`: `find_engine(version=None)` (editor, editor_cmd, uat, version; `UE_ROOT` override),
  `find_project(path)`, `preflight()`, `plan_plugins` / `enable_plugins` (timestamped backup),
  `enable_remote_execution`, `install_python_toolset`, `set_ini_values` (backup first),
  `read_ini_value`, `xcode_status`.
- `ue_run.py`:
  `run_python(uproject, script, args=None, map=None, timeout=1800, mode="commandlet"|"editor"|"latent", strict=False, lock_check="warn")`
  returns the `UE_RESULT` envelope plus log scan and `warnings`; job side `result(obj)`, `args()`,
  `in_commandlet()`, `to_jsonable()`, `wait_for_registry()`; `run_commandlet`, `run_uat`,
  `build_buildcookrun`, `launch_editor(mcp_port=, mode="headless"|"offscreen"|"window")`,
  `stop_editor`, `editor_processes`, `scan_log`, `parse_ue_result`.
- `ue_remote.py`: `PythonRemote().open/exec/call/close`,
  `RemoteControl(host, port).info/describe/get_property/set_property/call/batch/search_assets/console`
  (errors carry fix hints), `McpHttp().health()`, `loopback_only(port)`, `multicast_self_test()`,
  `pie_path`, `cdo_path`.
- `ue_mcp.py`: a client for Epic's MCP server (`Mcp().connect/toolsets/describe/call`),
  `snapshot(m, dir)`, `diff(old, new)`, `big_toolsets(index)`, `reachable(m)`. Use it for scripted
  checks and catalog snapshots; your own MCP client does the normal work.
- `gen_toolset_map.py`: turns a snapshot into signature lines
  (`name(arg: type, optional?: type) -> return`).
- `ue_review.py`: in editor `set_camera`, `screenshot`, `wait_screenshot`, `screenshot_views`,
  `camera_views_from_actors`, `render_still` (MRG or MRQ preset, own queue), `wait_render`; offline
  `image_checks`, `image_verdict`, `compare`, `contact_sheet`, `review_images`, `wait_for_file`,
  `build_render_command`.
- `ue_audit.py`: in editor `audit_assets(paths, rules, profile)`, `collect_facts`; anywhere
  `evaluate`, `build_report`, `verdict(report, "game"|"cinematic"|"mobile"|"prototype")`; Epic
  prefixes, texture size and compression, Nanite, collision, LODs, slots, instance parents, Custom
  HLSL, After-DOF translucency, redirectors.
- `ue_stat.py`: `parse_stat_unit`, `parse_csv_profile` + `csv_frames`, `parse_jsonl` +
  `sniff_schema` + `trace_frames` + `timer_totals`, `budget_check(frames, target_ms)`, `bound_by`,
  `summarize`.

Domain skills add `scripts/ue_<domain>.py`; they never copy these. The engine call behind each
function: `references/toolkit-map.md`.

## 7. Top 5.8 traps (full list: [`references/ue-5.8-traps.md`](references/ue-5.8-traps.md))

- **`EditorLevelLibrary` and `EditorAssetLibrary` are the old API**: `EditorActorSubsystem`,
  `LevelEditorSubsystem`, `UnrealEditorSubsystem`, `EditorAssetSubsystem` via
  `unreal.get_editor_subsystem`. `unreal.ObjectRedirector` does not exist in 5.8 (match the asset
  class name `ObjectRedirector`). `set_level_viewport_fov` needs the key from
  `get_active_viewport_config_key()`. `unreal.Rotator(1, 2, 3)` is roll, pitch, yaw. `load_level`
  discards unsaved changes; `delete_asset` force-deletes and may clear undo; `destination_name` is
  ignored under Interchange.
- **Substrate defaults depend on project age**: on for projects created in 5.7+, legacy for upgraded
  ones until opted in; Substrate materials render black with it off; no Metallic pin. Read
  `r.Substrate` before authoring.
- **Plugins decide which classes exist**: `MoviePipelineQueueSubsystem`,
  `MoviePipelinePrimaryConfig`, `MovieGraphConfig` are missing without the `MovieRenderPipeline`
  plugin; `ue_env.plan_plugins` first.
- **Mac feature support**: Apple Silicon only; Nanite and VSM Beta on M2+; Lumen HWRT and MegaLights
  Experimental on M2+; path tracing via Metal, macOS 26.4+. Xcode: Epic lists 26.0 minimum, 26.1.1
  recommended, 26.4 incompatible; Xcode 26.6 is unlisted, verify a C++ build.
- **MRG renames**: Movie Render Graph Production Ready, new features graph-only, MRQ presets legacy,
  queue default "Basic"; `set_graph_preset()` for graph jobs; end frames exclusive; H.264 node
  Windows only.
- **Remote Control defaults**: the server may start with the editor ('Auto Start Web Server'), so
  probe 30010 before `WebControl.StartServer`; a `-nullrhi` editor may not run it. Remote function
  calls and console commands are refused until allowed. HTTP binds 127.0.0.1; the WebSocket bind
  address is its own setting. Opening `DefaultBindAddress` to the LAN likely exposes the
  unauthenticated MCP server too.

## 8. macOS specifics

- Launcher installs land in `/Users/Shared/Epic Games/UE_5.8/`; the editor is
  `Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor`, the headless binary
  `Engine/Binaries/Mac/UnrealEditor-Cmd`; UAT is `RunUAT.sh`; cook platform `Mac`.
- Keep the Unreal project in a path without spaces (Allar style guide); the toolkit stages jobs in a
  space-free folder anyway.
- Metal only: DX11, DX12 and Vulkan tips do not apply; RenderDoc does not support Metal, use Xcode's
  Metal debugger; Metal System Trace shows shader compiles and thermal throttling that invalidate
  captures (ufPtQEtk-RQ [00:14:06], [00:18:17]). Insights memory callstacks are not listed for Mac.
  Outside Insights, the Mac sampling profiler is Instruments Time Profiler.
- Docs show Ctrl shortcuts and Windows paths: translate to Cmd and POSIX paths. A MacBook has no
  numpad: rebind the Gameplay Debugger's numpad category keys.
- Never kill an editor you did not launch; save before stopping one you did.

## References

- `references/channels.md`: the channels with rules, the capability matrix, write locks, ports and
  cleanup.
- `references/mcp-toolsets.md`: the 52 toolsets of 5.8.3 with owner skill, common struct shapes and
  signatures of the core toolsets.
- `references/ue-5.8-traps.md`: every 5.8 change that breaks remembered code or old tutorials, with
  sources, and the first-run checklist. Load before writing code from memory.
- `references/toolkit-map.md`: the engine call, command or cvar behind every toolkit function, and
  the report format (engine call per step, Verified and Assumed).
- [`references/python-reliability.md`](references/python-reliability.md): `unreal` module idioms and
  procedures (subsystems, paths, transactions, saving, get-or-create, marking what you create, the
  write lock and source control, latent work, imports, raw screenshot loop).
- [`references/sources.md`](references/sources.md): every source, with credentials, URLs and best
  timestamps.
- [`scripts/agent_python_toolset.py`](scripts/agent_python_toolset.py): a project-local MCP toolset
  that runs Python in the open editor.
