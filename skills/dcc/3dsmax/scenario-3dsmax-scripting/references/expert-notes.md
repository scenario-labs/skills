# Expert notes: scripting and pipeline tools

Judgment from tutorials and Autodesk docs, by source. Timestamps are `hh:mm:ss` into the video.
Lines marked [added] are this skill's own reasoning, not the expert's. Videos older than 3ds Max
2025 show older Python and Qt: the grammar lessons hold, the version details do not (see SKILL.md
"Current 3ds Max notes").

## Alexander Richter, TD Academy (pipeline TD)

Video EiMNwO4buOQ (3ds Max Python, recent) and Fete0ClQ-3A (2017 era).

- Listener first: do the action by hand with the MacroRecorder on, copy the echoed MAXScript,
  translate it to pymxs (EiMNwO4buOQ 00:22:40 to 00:23:46; again 00:37:15). Reason: the docs rarely
  show the exact property a UI action sets.
- The MacroRecorder echo is the fastest way to learn names (Fete0ClQ-3A 00:05:14). Replace the
  recorded `$` selection paths with variables before reuse (00:06:24).
- Write in the Editor, not the Listener, once the code is longer than a line (Fete0ClQ-3A 00:02:29).
  Save as `.py` before running from the Editor (EiMNwO4buOQ 00:40:30).
- `rt.cube()` fails: the class is `box`. Error text: "runtime object has no attribute" (EiMNwO4buOQ
  00:41:06). The fix is discovery, not guessing.
- Python versus MAXScript: Python wins for packaging, libraries and Qt; MAXScript stays shorter for
  scene one-liners (EiMNwO4buOQ 00:26:34).
- Startup scripts load the studio tools at launch (EiMNwO4buOQ 00:35:00). In 2027 a package's
  post-start-up part does this without touching the user folders [added].
- `fileIn` runs a MAXScript file from another script (Fete0ClQ-3A 00:12:37); `sys.path` edits let
  Python find a tool folder (00:14:40). A package `PYTHONPATH` entry replaces per-script `sys.path`
  edits [added].
- The forest sample uses `random.randint` with float bounds; it raises TypeError on Python 3.12 and
  later [added from Python release notes].

## Paul Neale (rigging and tools TD)

Video ZW5RvjnjxqE (VS Code with MXSPyCOM).

- Edit in an external editor and send the file to 3ds Max through a COM bridge; clear the Listener
  before each run so the output is readable.
- The COM server needs `initialize_COM_server.ms` in the startup folder (00:07:13). It is a
  third-party route; through the Autodesk 3ds Max MCP server, startup scripts cannot be written
  [added from the MCP limits page].

## ArchViz Explained (production archviz)

Video xGm1OBHd50Y (batch converter for old scenes).

- Exporter and converter settings are remembered from the last dialog; a script that does not set
  them inherits whatever the last user chose (00:02:30, 00:05:28).
- Write converted files to a separate folder, append a version suffix, skip files already converted
  (00:03:03). This makes a crashed batch resumable.
- Print status counts at the end: converted, skipped, failed (00:03:50).
- Files saved by a newer 3ds Max do not open in an older one; catch the failure and continue
  (00:01:23, 00:04:21).

## Daniel Szalapski (plug-in developer)

Video 9tf-8Zwkq5I (install routes).

- Plug-ins install through package folders, the Plugins folder or a `plugin.ini` path; `.dlm` and
  other binary plug-ins are tied to one release.
- Packages are the route that survives updates and needs no admin rights when placed per user [added
  from the packaging doc].

## Arch Viz Artist (AI-assisted scripting)

Video c3acjyR7j7E (writing MAXScript with a chat model).

- Name the renderer in the request: render code differs per renderer (00:05:02).
- Ask the model to list its assumptions before code (00:04:28).
- Work on a copy of the scene (00:08:59). Know where autosave and crash recovery files are before
  running generated code (00:09:37).

## 3D GROUND (archviz tools)

Videos GQv8Y_8eiBU and XpWCMn9Nboc.

- Test a generated script by creating something visible and capturing the viewport right away
  (GQv8Y_8eiBU 00:01:08).
- Naming and layer conventions are what validation tools check; a script that renames must follow
  the studio list (XpWCMn9Nboc).

## Autodesk, Martin (product team)

Video ZoIY5lT6IV4 (MAXScript basics).

- The MacroRecorder is the starting point for any script (00:00:03).
- Delete or reset test objects before re-running a creation script, or copies pile up (00:01:40).
  Agents save to a new file instead of deleting user objects [added].
- `in coordsys parent` changes how a transform is read and written (00:05:22). State the coordinate
  system in transform code.

## Chaos (V-Ray team)

Video PqwD_pHSv9M (USD export from 3ds Max).

- Review the USD export settings every time (00:00:40). Up axis differs between 3ds Max (Z) and many
  USD consumers (Y); the video rotates -90 degrees to fix it. Check orientation on re-import.

## Autodesk documentation positions (not a person)

- pymxs: arrays 0-based, index arguments 1-based; `==` not `is`; `rt.Name`; no `$` or `max`
  commands; byref through `pymxs.byref` (pymxs using and differences pages).
- Threading: main thread only; `mxstoken` deprecated; threads for I/O only (threading page).
- Qt: `QWidget.find(rt.windows.getMAXHWND())` parents a window but it cannot dock; use
  `qtmax.GetQMaxMainWindow()` and `QDockWidget` (creating UIs page).
- Render: Render Setup pre and post scripts do not run on `render()`; use general callbacks; close
  Render Setup before changing settings (pymxs renderer page).
- Batch: debug in a GUI session first; MCP is not available in batch (3dsmaxbatch page; Autodesk MCP
  FAQ).
- MCP: modal dialogs block; Arnold renders can crash 3ds Max; blocked commands stay blocked for the
  session (MCP known limitations page).

## Community bridge pattern (not Autodesk)

- The open-source `max-mcp` bridge drains a queue with a 20 ms QTimer on the main thread so socket
  threads never call pymxs. This skill's `MainThreadPump` follows the same idea [added].

## Where sources disagree

- PySide version: the creating-UIs page says "PySide 6.0"; the version table says 6.8.3 for 2027.
  Trust the table; probe `PySide6.__version__` (P1).
- glTF export: one line says no animation, skin or morph data; the 2027.3 what's new lists
  animation. Re-import and check before promising animation.
- MCP script approval: the FAQ says preview cannot be turned off; the admin page documents
  `ADSK_3DSMAX_MCP_SKIP_PROPOSE=1`. Ask the admin which applies.
