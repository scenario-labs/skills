---
name: scenario-3dsmax-scripting
description: "Use when writing, fixing or shipping pymxs or MAXScript code for 3ds Max: a script fails with \"runtime object has no attribute\", an index is off by one, a name value or by-reference argument will not translate, a tool freezes 3ds Max or crashes from a thread, a PySide6 or qtmax dock panel, callbacks that fire twice, 3dsmaxbatch jobs over many .max files and their exit codes, import or export by script (FBX, OBJ, glTF, GLB, USD, PLY) without dialogs, viewport capture or render to file, pre-render callbacks, bitmaps that eat memory, PackageContents.xml plug-in packages, startup scripts and macroScripts, pip in the 3ds Max Python, or porting old MaxPlus, PySide2 or Python 2 tools to 3ds Max 2027."
license: MIT
---

# Scripting and Pipeline Tools in 3ds Max

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit. Code status: not yet run in 3ds Max.

Expert level here means code that runs the same way twice: names discovered in the Listener before
they are written, every scene change in one named undo record, every callback removable by id, no
dialog that can block a batch, and no save that overwrites a user file. pymxs is a thin wrapper over
MAXScript, so the MAXScript reference is the API reference for both; Python adds packaging, Qt and
the standard library. A tool ships as a package that installs by copying one folder.

If a sibling skill named here is missing from your available skills, load it with `skill_get`
(Scenario MCP) or ask the user to install it (https://github.com/scenario-labs/skills#install);
unattended, proceed from tool schemas and flag the gap.

**REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit, current-3ds-Max
traps).

## Stance (the expert delta)

1. **Discover in the Listener, then write the file.** Do the action once with the MacroRecorder on,
   read the echoed MAXScript, then translate only the grammar (Alexander Richter, EiMNwO4buOQ
   00:22:40 to 00:23:46). Headless, inspect with `getpropnames` and `showinterface` (P2). A guessed
   name costs a batch run.
2. **pymxs is MAXScript with Python syntax, not a Python API.** `rt.cube()` fails with "runtime
   object has no attribute" because the class is `box` (Richter, EiMNwO4buOQ 00:41:06). `$` paths,
   `max` commands and by-reference arguments have no Python form; route them through `rt.execute`
   (P3).
3. **Arrays are 0-based in Python, index arguments stay 1-based.** `rt.meditMaterials[0]` but
   `setMeditMaterial(1, mat)` and `viewport.getType(index=1)` (pymxs doc). Compare nodes with `==`,
   never `is`: each access builds a new wrapper.
4. **One thread touches 3ds Max.** pymxs calls from any other thread are unsupported and `mxstoken`
   does not work (threading doc). Workers do network and disk only and post results to a main-thread
   queue (P6). The viewport repaints only when the script ends or calls `rt.redrawViews()`.
5. **Every save goes to a new name.** `saveMaxFile` and `saveNodes` overwrite silently,
   `loadMaxFile` discards unsaved changes without asking (file loading doc). Batch converters write
   to a separate folder, append a version and skip files already done (ArchViz Explained,
   xGm1OBHd50Y 00:03:03).
6. **Exporter settings are global state.** The last dialog settings drive the next quiet export
   (xGm1OBHd50Y 00:02:30). Set them every run and read them back (`FBXExporterGetParam`); never
   assume.
7. **Batch first, debug in the GUI.** 3dsmaxbatch has no viewport and no MCP; write the job so it
   runs in a GUI session too, debug it there, then run it headless (3dsmaxbatch doc; Autodesk MCP
   FAQ).
8. **Ship as a package, never into Program Files.** `PackageContents.xml` in `ApplicationPlugins`
   loads scripts, macros, icons and `PYTHONPATH` with no installer (packaging doc; Daniel Szalapski,
   9tf-8Zwkq5I).

## Establish first

- 3ds Max release and Python: 2027 ships Python 3.13.9 and PySide 6.8.3; 2025 and 2026 ship 3.11.
  Probe with P1 before writing version-sensitive code.
- Channel (lead's table): `batch` for many files, `bridge` or `handoff` for Python and Qt,
  `mcp-safe` for MAXScript in a live session. Python through the Autodesk 3ds Max MCP server needs
  admin level 20; its scripting feature needs a client with MCP Apps support, and a blocked command
  stays blocked until 3ds Max restarts (MCP limitations doc).
- Deliverable: one-off chunk, batch job, dock panel, or installable package. Default: a chunk
  through `max_wrap`.
- Inputs and outputs as paths from arguments; output folder separate from the source folder.
- Renderer (`rt.renderers.current`) if the code renders, bakes or captures.
- System unit if the code writes positions or sizes; state the unit next to each number.
- Who runs it: an artist (needs a panel and undo) or a farm (needs exit codes and logs).

## Procedure

Full code, channels and checks for every stage: [procedures.md](references/procedures.md). Scripts:
[maxkit_scripting.py](scripts/maxkit_scripting.py) (in-Max helpers: `cmd_args`, `log`, `save_copy`,
`load_scene`, `exporter_for`, `CallbackSet`, `MainThreadPump`, `run_chunked`),
[batch_many.py](scripts/batch_many.py) (one job over many files),
[package_lint.py](scripts/package_lint.py) (offline package check),
[port_scan.py](scripts/port_scan.py) (porting scan).

1. **Probe the session.** Goal: know Python, PySide, batch mode, renderer. How: P1 through any
   channel. GATE: versions match the release; `isInNonInteractiveMode()` matches the channel.
2. **Discover names.** Goal: every class, property and interface name is real. How: MacroRecorder in
   a live session (2027: `macroRecorderEmitterEnabled`); `getpropnames`, `showinterface`,
   `importerPlugin.classes` headless (P2). GATE: each name used appears in the probe output or the
   lead's `references/api-names.txt`; the rest carry `[verify]`.
3. **Write the chunk.** Goal: correct pymxs. How: `rt` alias, `rt.Name("x")` for `#x`, 1-based index
   arguments, `rt.execute` for `$`, `max` and `&` (P3); one `pymxs.undo(True, "label")` per user
   action; `animate` and `attime` contexts for keys (P4). GATE: the lead's `max_check` passes;
   `python3 -m py_compile` passes under 3.13.
4. **Wire events.** Goal: callbacks that fire once and leave cleanly. How:
   `callbacks.removeScripts(id=...)` then `addScript` with a tool id; redraw callbacks for `gw`
   drawing; never persistent (P5). GATE: run the tool twice, the handler fires once; close it,
   nothing fires.
5. **Build the UI when an artist needs one.** Goal: a dock that never freezes 3ds Max. How:
   `QDockWidget` parented to `qtmax.GetQMaxMainWindow()`, `objectName` singleton,
   `DisableMaxAcceleratorsOnFocus`, network on a worker with the pump, long loops in timer slices
   (P6, P7). GATE: `show()` twice gives one dock; heartbeat gap under 0.2 s during a request
   [added].
6. **Batch over files.** Goal: N files in, N results out, none lost. How: job chunk with lead
   `audit`, `xio`, `capture`; `batch_many.py` runs one 3dsmaxbatch per file with `-sceneFile`,
   `-mxsString`, `-listenerlog`, `-dm on`, skip-existing and one retry (P8). Third-party scenes: set
   `ADSK_3DSMAX_SAFE_SCENE=1` for the batch process [verify batch honors it], open them in the chunk
   with `load_scene`, and report blocked embedded scripts as findings (safe scene doc). Progress
   lines: `logsystem.logEntry <string> broadcast:true` (3dsmaxbatch doc). GATE: summary total equals
   input count; each failure names an exit code and a log line.
7. **Import and export.** Goal: no dialog, known settings, verified output. How:
   `importFile`/`exportFile` with `quiet:true` and `using:` from `exporter_for(ext)`; diff
   `set(rt.objects)` for what arrived; FBX params set and read back (P9). Before glTF export, run
   the glTF pre-check (P9). glTF and USD have no option names in the saved docs: a quiet export
   takes defaults or last-used settings [verify which]. GATE: file size above zero; re-import in a
   fresh run gives the same node count.
8. **Scene files.** Goal: no data loss. How: `load_scene` (`allowPrompts:false`,
   `missing*Action:#logmsg`, units passed explicitly with `useFileUnits:` or 2027.1
   `ignoreFileUnits:`), `save_copy` (`_v###`). Before a merge, preview with `getMAXFileObjectNames`
   or `getMaxFileObjects` (2027: layer, group, color per node), then `mergeMAXFile` with `layers:`
   and `mergeNodesByLayer:` (P10). GATE: source file size and date unchanged.
9. **Images.** Goal: captures and renders that exist and are not black. How:
   `viewport.getViewportDib` in a UI session; `render(outputFile=..., vfb=False)` in batch;
   `#preRender` callback, Render Setup closed, save before Arnold; `close` bitmaps in loops; under
   OCIO pass `outputColorConversion:` to `save` (P11, P12). Never read a Batch Render view's camera
   through `batchRenderMgr`: it crashes 3ds Max (MCP limitations doc). GATE: the lead's
   `max_review.image_checks`, then look at a contact sheet.
10. **Package.** Goal: copy-one-folder install. How: `PackageContents.xml` with `UpgradeCode`,
    `CompanyDetails`, `SeriesMin`/`SeriesMax` per `Components`, `PYTHONPATH` entry, post-start-up
    `.py`, `.mcr` macro; Scene Converter rules as `ConversionPresets/<name>_preset.ms` in a
    `scene converter folders parts` component (P13, P14). GATE: `package_lint.py --release 2027` 0
    errors; clean start with `ADSK_APPLICATION_PLUGINS` pointing at the folder shows no package
    error.
11. **Port old tools.** How: `port_scan.py`, then the table in P16. GATE: 0 errors; the panel docks
    in 2027.

## Numbers

| Value                           | Meaning                                                                                                      | Source                           |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------- |
| Python 3.13.9, PySide 6.8.3     | 3ds Max 2027                                                                                                 | Python what's new                |
| Python 3.11.4 / 3.11.8 / 3.11.9 | 2025 / 2025.1 / 2026                                                                                         | Python what's new                |
| 0                               | exit code: success                                                                                           | 3dsmaxbatch doc                  |
| -100, -110, -120, -130          | bad args, no start, lost contact, Max error                                                                  | 3dsmaxbatch doc                  |
| `-v 0` to `5`                   | batch verbosity; user exit codes print at 5                                                                  | 3dsmaxbatch doc                  |
| 10, 20                          | MCP levels: Safe MAXScript, Python (admin)                                                                   | MCP admin doc                    |
| 27200 to 27209                  | Autodesk 3ds Max MCP server ports                                                                            | MCP connect doc                  |
| 3 to 5x                         | `pasteBitmap` speed over pixel loops                                                                         | bitmap doc                       |
| 20 ms, 50 jobs                  | pump interval and budget per tick                                                                            | community bridge pattern [added] |
| 200 items                       | `run_chunked` slice per tick                                                                                 | [added]                          |
| 0.2 s                           | max heartbeat gap for a responsive panel                                                                     | [added]                          |
| 1800 s                          | runner-side kill timeout per file (`run_batch`, `batch_many.py --timeout`); 3dsmaxbatch documents no timeout | toolkit default [added]          |

## Quality gates

- Offline: `py_compile` under 3.13; `max_check` (with `channel="mcp-safe"` for MAXScript meant for
  it); `port_scan` 0 errors; `package_lint` 0 errors.
- Every chunk returns JSON `{ok, result, error, log}`; `ok` false is never reported as done.
- Idempotence: run twice, same scene state (`stats.diff` empty after the second run) and one
  callback per id.
- Batch: `summary.json` counts add up; every `ok` file has a non-empty export and a result JSON.
- Visual: capture or render after scene changes, contact sheet, look for black frames, missing
  textures (magenta or gray), framing.
- Rubric and thresholds: [critique.md](references/critique.md).

## Common mistakes

| Mistake                                                     | Symptom                                             | Fix                                                      |
| ----------------------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------- |
| Guessed class name                                          | "runtime object has no attribute"                   | MacroRecorder or `getpropnames` (P2)                     |
| 0-based index argument                                      | wrong viewport, material slot or "out of range"     | arguments are 1-based                                    |
| `node is other`                                             | identical nodes compare unequal                     | `==`                                                     |
| `rt.max(...)`, `rt.$Box*`                                   | attribute error                                     | `rt.execute("max ...")`, `rt.execute("$Box* as array")`  |
| pymxs in a thread                                           | random crash or hang                                | worker posts to `MainThreadPump`                         |
| `addScript` without `removeScripts`                         | handler fires twice after reload                    | remove by id first (`CallbackSet.reset`)                 |
| Render Setup pre-render script                              | never fires on `render()`                           | `#preRender` callback                                    |
| Format option after `.filename`                             | JPEG quality ignored                                | set options first                                        |
| Bitmaps not closed in a loop                                | memory climbs to a crash                            | `close`, reuse `to:`, `gc light:true`                    |
| `saveMaxFile` on the input path                             | user file overwritten                               | `save_copy` to `_v###`                                   |
| Export without `quiet:true`                                 | batch hangs on a dialog                             | `quiet:true`, `-dm on`                                   |
| Relying on `-sceneFile` for third-party scenes              | Units Mismatch or missing-file dialog hangs the run | `load_scene` in the script with explicit units (P10)     |
| Reading `batchRenderMgr` view cameras                       | 3ds Max crashes                                     | write only; check in Rendering > Batch Render            |
| glTF export of OpenPBR, Physical or VRayMtl                 | maps lost, wrong materials                          | glTF Material with Bitmap Texture inputs; pre-check (P9) |
| Code typed with `__name__` or a coding line run by Evaluate | error in Editor                                     | save as `.py`, Scripting > Run Script                    |
| `AppName` in `PackageContents.xml`, no `SeriesMax`          | package ignored                                     | `Name`, `SeriesMax`, run `package_lint`                  |
| `random.randint(0.0, 1.0)` from an older tutorial           | TypeError on 3.12+                                  | integers or `random.uniform` [added]                     |

## Handoffs

- From scenario-3dsmax-expert: channel choice, `max_wrap`, `max_batch`, `max_check`, `max_review`,
  in-Max `audit`, `stats`, `capture`, `xio`. Use them; add domain helpers here only.
- To every sibling: correct pymxs patterns, batch harness, panel and package skeletons. Domain logic
  stays with its owner.
- scenario-3dsmax-scene: units, naming, layers and missing-asset rules a validation tool checks; the
  checks run through the lead's `audit.units`, `audit.names`, `audit.maps` (P17).
- scenario-3dsmax-materials: OpenPBR conversion rules (Physical to OpenPBR mapping) and Scene
  Converter steps a batch job calls. The OpenPBR material's MAXScript class name is not in the saved
  docs: discover it (P2) before writing it. A V-Ray 7 `VRayMtl` has an OpenPBR shading mode (not on
  V-Ray GPU): a mode switch, not a rebuild (Chaos VRayMtl doc).
- scenario-3dsmax-game-assets and scenario-3dsmax-uv-baking: FBX and glTF export targets, bake jobs.
- scenario-3dsmax-lighting-rendering: render settings before a batch render.
- scenario-3dsmax-generation: Scenario MCP calls from a panel go through a worker thread and the
  pump.

## Current 3ds Max notes

From the Autodesk what's-new, MAXScript and MCP pages listed in [sources.md](references/sources.md).

- 2022 removed MaxPlus and Python 2; 2025 moved to PySide6; 2027 runs Python 3.13.9 and Qt 6.8.3, so
  `randint` with floats and PySide2 code break.
- 2027 adds `macroRecorderEmitterEnabled`, bitmap `copy ... quality:`,
  `#BitmapPreSave`/`#BitmapPostSave`, node data on `#preRender`, `mergeMAXFile layers:`,
  `maxOps.SetSceneSaveDirectory`, `suppressStartupDialogs`.
- 2027.1: `ignoreFileUnits:` on `loadMaxFile` and `mergeMAXFile`; unit rules in Preferences > Files.
- 2027.2: `FBXExporterGetParam` gains `to:` and `enumAsString:`; PLY, LCC and SPZ splat import.
- 2027.3: Khronos glTF importer and exporter with no documented script options or class name;
  `.usdz` is export only; the Autodesk 3ds Max MCP server (tech preview) blocks `dotNetObject`,
  `macroScript`, `setINISetting`, `globalVars.remove`, file delete and copy, and cannot add menus or
  startup scripts.
- The 3dsmaxbatch option list is confirmed on the 2020 page only; treat changes in 2027 as possible.
- A Units Mismatch dialog from `maxstart.max` blocks MCP renders; batch needs `-dm on`.

## References

- [procedures.md](references/procedures.md): 17 procedures with full code, channels and checks.
- [expert-notes.md](references/expert-notes.md): judgment by expert, with video ids and timestamps.
- [critique.md](references/critique.md): rubric for reviewing a script, a batch run, a panel and a
  package.
- [gui-paths.md](references/gui-paths.md): Editor, Listener, MacroRecorder, Customize, Preferences,
  package folders.
- [sources.md](references/sources.md): every doc page and video with what it is best for.
