# Execution channels: which door into the engine, and how to open it safely

Status: run on UE 5.8.3 (macOS 26.5, Apple silicon) on 2026-10-21 unless an entry says "not yet
run". The v0.1 text of this list moved here from SKILL.md; v0.2 corrects what the live runs
disproved.

## Choose in this order

1. **Is an editor already open on this project?** Check with `ue_run.editor_processes()`. If yes,
   never start a second one on it and never kill it: use its MCP server or its Python channel. If
   you did not start it, you do not stop it.
2. **Editor closed, edits and audits only:** headless commandlet (`ue_run.run_python`). No window,
   no GPU, about 15 to 20 s per job on this Mac.
3. **Editor closed, you need Epic's toolsets or a rendered frame:** start one you own with
   `ue_run.launch_editor(uproject, mcp_port=N, mode="headless" | "offscreen")`. `offscreen` renders
   without a window and without taking focus; `headless` has no renderer (no screenshots, no lit
   viewport). Use a new port each launch. Save before `stop_editor`.
4. **Something no toolset covers:** Python in the running editor (below), or a headless job.

Never open a visible window, play sound, send keystrokes, or `kill` a process you did not start. A
plain `UnrealEditor ... -ExecCmds=...` launch opens a window; the toolkit adds
`-RenderOffscreen -nosound` for you, so go through `ue_run`.

## The channels

Each channel: what it is for, then its rules.

- **Epic Unreal MCP** (plugin `ModelContextProtocol`, Experimental; toolsets from `AllToolsets`,
  which pulls in `EditorToolset`), your MCP client via `.mcp.json`.
  - For structured edits covered by shipped toolsets (actors, scene, assets, materials, Blueprints,
    UMG, Sequencer, PCG, Niagara, animation), in the open editor.
  - `tools/list` shows three meta-tools: `list_toolsets`, `describe_toolset`, `call_tool`.
  - Start with `-ModelContextProtocolStartServer -ModelContextProtocolPort=N` (listening about 30 s
    after a headless launch) or the console command `ModelContextProtocol.StartServer`. Port 8000 is
    the default; pick another when anything else may run.
  - Calls from separate sessions run concurrently (4 parallel 2 s scripts finished in 2.2 s):
    serialize calls that depend on each other.
  - Loopback only, no authentication. Protocol, batching, sizes: SKILL.md section 2 and
    `references/mcp-toolsets.md`.
- **Python Remote Execution** (`ue_remote.PythonRemote`).
  - For loops, audits, anything toolsets lack, screenshots, in the open editor.
  - Run live: both Epic's `remote_execution.py` and our fallback client connect, execute statements
    and files, report failure. Full `unreal` API; the editor ticks between calls. One call = one
    named transaction that reports what it did.
  - Needs `ue_env.enable_remote_execution(project)` (writes `bRemoteExecution`, bind address and TTL
    0 to `Config/DefaultEngine.ini`, with a backup) and an editor restart.
  - The multicast bind address must match the OS, in the editor and in the client. Windows: Epic's
    default `127.0.0.1`. macOS and Linux: `0.0.0.0`, since a socket bound to `127.0.0.1` never
    receives the group's datagrams (editor run on macOS; socket test on Linux).
  - **Security.** Any local process that can reach the multicast group can run code in the editor.
    With `0.0.0.0` the editor also listens on the network interface, so any host on the local
    network can run code in it: TTL 0 limits what the editor sends, not what it receives. Opt in per
    project, say so to the user, and use it only on a trusted network or behind a firewall that
    drops inbound UDP 6766 from other hosts. Prefer the MCP channels (loopback) when they are
    enough.
- **Project-local Python toolset on the MCP server** (`ue_env.install_python_toolset`).
  - For the same work as Python Remote Execution, when no multicast setup is wanted, or one
    connection must do everything.
  - Adds `agent.AgentPythonToolset` with `run_python(code)`: persistent namespace, captured output,
    `result` variable, traceback on error. Run live in a headless editor.
  - Editor restart needed after install; 5.8 only (the toolset registry does not exist in 5.6 or
    5.7).
  - Unsafe by design (arbitrary code over an unauthenticated loopback port): throwaway or trusted
    projects only; say so before installing.
- **Headless commandlet** (`ue_run.run_python`, `UnrealEditor-Cmd <uproject> -run=pythonscript`).
  - For audits, imports, batch edits, validation, CI, when no editor has the project open.
  - No level loaded (`map=` loads one), fewer modules, no rendering.
  - The boot waits for the Asset Registry (`get_asset_registry().wait_for_completion()`); a job
    passes only on its boot's job-id `UE_RESULT` line, never on the exit code (a good run can exit
    1).
  - A commandlet that saves must not touch a project an open editor has loaded: the editor holds a
    write lock (Jamie Dale, 0guOMTiwmhk [01:17:18]). `-nosound` is added by `ue_run`.
- **Full editor, one shot** (`mode="editor"`: `-ExecutePythonScript`; `mode="latent"`: ticking boot
  that quits after).
  - For jobs needing full modules; latent: screenshots and renders without a running editor.
  - `-ExecutePythonScript` shuts down right after the script, so nothing ticks; `ue_run` adds
    `-ScriptErrorsAreFatal` (5.5) so a failing script fails the process.
  - Latent jobs are generators: `yield` = one tick. Both run with `-RenderOffscreen` unless
    `window=True`.
- **Remote Control API** (`ue_remote.RemoteControl`, 127.0.0.1:30010).
  - For batched property writes on known objects, live presets, `-game` builds.
  - The server may start with the editor (setting 'Auto Start Web Server'): probe with
    `RemoteControl().info()`, then `WebControl.StartServer` only if nothing answers. A `-nullrhi`
    (headless) editor may not start it at all: launch offscreen for this channel.
  - HTTP binds 127.0.0.1 by default. The WebSocket server has its own bind address setting
    (`RemoteControlWebsocketServerBindAddress`): read it before assuming loopback.
  - **5.8 refuses remote function calls by default** (HTTP 400, "not allowed by remote control
    settings"); allow them under 'Custom Allowed Remote Function Calls' or 'Allow Any Remote
    Function Call'. `ExecuteConsoleCommand` also needs 'Allow Console Command Remote Execution', a
    separate setting.
  - Property reads and transactional writes worked live. C++ names, `WRITE_TRANSACTION_ACCESS` for
    undo, public EditAnywhere properties only.
- **Console and cvars**.
  - For stats, view modes, quality switches, `HighResShot`.
  - From Python `unreal.SystemLibrary.execute_console_command(world, cmd)`;
    `EditorAppToolset.SearchCVars` over MCP; at launch `-DPCVars=` (before init, overrides read-only
    cvars; Profiling with Purpose, C-AjCqjKRSs [00:14:13]), not `-ExecCmds`.
  - Restore what you change. `r.Shadow.Virtual.ShowStats` was renamed
    `r.Shadow.Virtual.Stats.Visible`.
- **Commandlets and UAT** (`ue_run.run_commandlet`, `run_uat`).
  - For `DataValidation`, `ResavePackages -fixupredirects`, `WorldPartitionBuilderCommandlet`,
    `BuildCookRun`.
  - Headless; parse the log (`ue_run.scan_log`). Not yet run here except through
    `-run=pythonscript`.

## Capability matrix (what each channel can do in 5.8.3)

Rows marked "toolset" were read from the live `describe_toolset` catalog (52 toolsets, 830 tools);
behavior is run where the domain skill's recipe says so.

| Action                                         | MCP                                                         | Python, running editor                                                                        | Headless commandlet                                 | Remote Control                 |
| ---------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------ |
| read and edit actors, assets, properties       | `ActorTools`, `SceneTools`, `AssetTools`, `ObjectTools`     | yes                                                                                           | yes (load the level first)                          | public EditAnywhere properties |
| material instances and parameters              | `MaterialInstanceTools`                                     | yes                                                                                           | yes                                                 | properties only                |
| material graphs                                | `MaterialTools` (22 tools)                                  | `MaterialEditingLibrary`, partial: some pins unexposed (Matt Oztalay, m6mJ9r7ytks [00:13:39]) | same                                                | no                             |
| Blueprint graphs, widgets                      | `BlueprintTools` (53), `UMGToolSet` (23)                    | `BlueprintGraphEditor` subsystem [scope not yet run]                                          | same                                                | no                             |
| Niagara emitters and modules                   | `NiagaraToolset_System` (46 tools, 112k-token describe)     | no emitter or module editing                                                                  | no                                                  | user parameters                |
| PCG graphs                                     | `PCGToolset` (30), `PCGSpatialToolset`                      | graph API [not yet run]                                                                       | yes                                                 | no                             |
| Sequencer                                      | `SequencerTools` (140) and 5 sibling toolsets               | `LevelSequence` API                                                                           | yes                                                 | no                             |
| screenshots, MRG stills, PIE                   | `EditorAppToolset.CaptureViewport`, PIE tools [not yet run] | yes (offscreen editor, run live: a lit scene returns a normal frame)                          | no (use `mode="latent"` or `-game` render CLI)      | no                             |
| landscape sculpt, foliage paint, Fracture Mode | no                                                          | no                                                                                            | no                                                  | no                             |
| cook, package, validate                        | no                                                          | not the cook (in-editor cook removed in 5.9)                                                  | yes, UAT                                            | no                             |
| run automation tests                           | `AutomationTestToolset` (7)                                 | the toolset, or the console command `Automation RunTests <name>` [not yet run]                | `-ExecCmds="Automation RunTests ..."` [not yet run] | no                             |

## Graph editors and viewport tools, substitutes

Blueprints: logic in C++ (code project, Xcode) with data-only Blueprints, or `BlueprintTools` when
the graph is the deliverable; template Blueprints duplicated and their defaults set; never 150 Delay
nodes or unjustified Event Tick (k0tgmrBuIJc [00:56:45], [00:57:19]). Materials: instances of
approved masters; node graphs through `MaterialTools`, never a whole-HLSL Custom node unless
required (k0tgmrBuIJc [00:39:27]). Niagara: duplicate template systems, set user parameters; the
toolset can build emitters (read the engine's Niagara skills through `AgentSkillToolset` first).
PCG: compose Epic's primitives and example graphs (lDf_y-YPELo [00:05:20]). Control Rig: its "Copy
Python Script". Sculpting, painting, fracturing: heightmap import, PCG, Dataflow graphs, or a human
step, said plainly.

## Write locks and source control

`ue_run` lists UnrealEditor processes holding the project (`ps`); pass `lock_check="refuse"` for
jobs that save. 5.8's PythonScript commandlet enables source control before the script, so saves can
check out [verify with Perforce]; `ResavePackages` needs `-autocheckout` (redirectors doc). Stop
when a file you must edit is not checked out (Bardoux, MjjkWH0eT3U [00:55:27]). OFPA changelists are
submitted from inside the editor: partial submits leave dangling references (World Partition doc).
Content a builder regenerates, such as PCG partition actors, stays out of changelists (TbNZ4GKaTow
[00:26:23]).

## Ports, processes, cleanup

- One MCP port per launch (a port freed by a killed editor can refuse to bind again: "HttpListener
  unable to bind"). `launch_editor` returns a handle; `stop_editor(handle)` sends SIGTERM to its
  group, SIGKILL only after a timeout.
- A headless MCP editor is about 3 to 5 GB of RAM: stop it when the task is done.
- State on disk is the truth: an editor stopped before saving loses its work. Save through
  `AssetTools.save_assets` (MCP) or `EditorAssetLibrary`/`EditorAssetSubsystem.save_loaded_assets`
  (Python) and the level through `LevelEditorSubsystem.save_current_level`.
- Headless PIE works (gameplay checked by running it, run on 5.8.3); Control Rig is not evaluated
  for a bake in a headless or offscreen editor.
