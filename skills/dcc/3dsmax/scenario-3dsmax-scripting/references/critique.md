# Critique: judging your own script, batch run, panel or package

Score each line pass or fail. One fail in "Blocking" means not done. Thresholds marked [added] are
this skill's defaults, not Autodesk numbers.

## Blocking: any script

| Check    | Pass                                                                                                                                                          |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Compiles | `python3 -m py_compile` under 3.13 passes; MAXScript brackets balance (`max_check`)                                                                           |
| Names    | every API name is in probe output or `api-names.txt`, or carries `[verify]`                                                                                   |
| Header   | first comments name channel and status                                                                                                                        |
| Threads  | no `rt.` inside a thread target or worker callback                                                                                                            |
| Undo     | one named undo record per user action (`wrap` or `pymxs.undo`)                                                                                                |
| Files    | no write to an input path; outputs under a folder from arguments                                                                                              |
| Dialogs  | every load, import, export, save uses `quiet` or `#noPrompt`; batch uses `-dm on`                                                                             |
| Result   | chunk sets `result`; returned JSON has `ok` true                                                                                                              |
| Units    | each hard number states its unit                                                                                                                              |
| Renderer | render code reads `rt.renderers.current` first                                                                                                                |
| mcp-safe | MAXScript only; no `dotNetObject`, `dotNetClass`, `macroScript`, UIAccessor, `windows.sendMessage`, `setINISetting`, `globalVars.remove`, file delete or copy |

## Idempotence

- Run the chunk twice: `stats.diff(before_second, after_second)` is empty, or the difference is the
  intended one (one more version file).
- Callbacks: count prints per event after two loads of the tool: one.
- Panel: `show()` twice gives one `QDockWidget` with the tool's `objectName`.

## Batch run

| Measure               | Pass                                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------------------- |
| `summary.total`       | equals the number of input files                                                                                |
| ok + skipped + failed | equals total                                                                                                    |
| Each `ok` file        | result JSON with `ok` true, export size above 0 bytes                                                           |
| Each `failed` file    | exit code and a listener-log line naming the cause                                                              |
| Retries               | only after -120 or a timeout; never after -100 or -130                                                          |
| Newer-version input   | listed as failed, run continues                                                                                 |
| Dialogs               | no file hangs on Units Mismatch or missing files: third-party scenes opened by `load_scene` with explicit units |
| Third-party scenes    | Safe Scene Script Execution on; blocked embedded scripts listed as findings, not silently run                   |
| Re-run                | all previous `ok` files skipped                                                                                 |
| Time per file         | under the `--timeout`; a file near the limit is flagged for a human [added]                                     |

## Exports

- Re-import in a fresh batch run: node count equal; bounding box size within 1% [added].
- FBX: `FBXExporterGetParam` readback equals the values set.
- glTF: hierarchy flattened and vertex colors dropped are expected; materials not glTF Material may
  lose maps.
- glTF: the pre-check (procedure 9) returns zero findings: glTF Material only, Bitmap Texture
  inputs, Multi/Sub nesting at most two, no empty slots, no same-name bitmaps of different type
  (gltf-export-2027).
- USD: up axis and scale checked on re-import (Chaos, PqwD_pHSv9M 00:00:40).

## Images (capture and render)

Use the lead's `max_review.image_checks`, then look.

| Measure                    | Pass                                                                                          |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| File                       | exists, size equals the requested size                                                        |
| Mean luminance             | between 0.05 and 0.95 of full scale [added]                                                   |
| Black or white frame       | fail: missing light, wrong camera, render not finished                                        |
| Magenta or flat gray areas | missing texture: run the lead's `audit.maps`                                                  |
| Framing                    | subject inside the frame, not clipped                                                         |
| Color                      | under OCIO the PNG was saved with an explicit `outputColorConversion:`; it matches the viewer |
| Batch Render               | no script reads a `batchRenderMgr` view camera (crashes 3ds Max)                              |

Look at a contact sheet, not single images: compare files side by side for the odd one out.

## Panel (dock widget)

| Measure                             | Pass                                              |
| ----------------------------------- | ------------------------------------------------- |
| Heartbeat gap during a network call | under 0.2 s [added]                               |
| Typing in a text field              | no 3ds Max hotkey fires                           |
| Close and reopen                    | works, no duplicate, no orphan callback           |
| Long loop                           | progress visible, cancel works, viewport repaints |

## Package

| Measure                                                       | Pass                                                                |
| ------------------------------------------------------------- | ------------------------------------------------------------------- |
| `package_lint.py --release <year>`                            | 0 errors                                                            |
| Clean start with `ADSK_APPLICATION_PLUGINS` set to the folder | no Plug-in Package Manager error; max.log clean                     |
| Macro                                                         | listed in Customize User Interface under its category               |
| Import                                                        | `import <tool>` works in the Listener                               |
| Uninstall                                                     | removing the folder removes the tool; nothing left in Program Files |

## Porting

- `port_scan.py` reports 0 errors; each warning read and either fixed or explained.
- The tool runs in the oldest and newest release it claims (`SeriesMin`, `SeriesMax`); vendored
  wheels match that Python minor version.

## Report honesty

- Say "not yet run in 3ds Max" until a run in a real 3ds Max returned `ok`.
- List every `[verify]` name the delivered code still uses.
- Never report a batch as done from the exit code alone: read the result files.
