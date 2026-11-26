# Procedures: scenario-3dsmax-scripting

Each block names its channel (see the channel table in scenario-3dsmax-expert) and the saved doc it
was checked against. A name followed by `[verify]` was not found in the saved docs: check it in a
live session (procedure 2) before relying on it.

Python blocks are chunks for `max_wrap.wrap(code, lang="python", kit=[...])` unless they say
"module". A chunk sets `result`; the wrapper adds the undo record and the result file. A `# kit:`
line lists what the chunk expects as globals: `audit`, `xio`, `capture`, `stats` go to `max_wrap` as
kit names; `maxkit_scripting` (this skill's `scripts/maxkit_scripting.py`) is not a `max_wrap` kit
name, so prepend its source to the chunk (`batch_many.py` does this) or import it from a package.
MAXScript blocks marked `mcp-safe` avoid the Safe Scene Script Execution block list (`dotNetObject`,
`dotNetClass`, `macroScript`, `UIAccessor`, `windows.sendMessage`, `setINISetting`, file delete and
copy). Placeholders written `<<NAME>>` are filled by the agent from the user's request; never
hard-code a user path.

Contents

1. Probe the session
2. Discover a name before using it
3. pymxs translation rules in code
4. Undo and animate contexts
5. Callbacks with cleanup
6. Worker threads and the main-thread pump
7. Dockable PySide6 panel
8. 3dsmaxbatch job over many files
9. Import and export by script
10. Scene files without data loss
11. Bitmaps and viewport capture
12. Render calls and pre-render callbacks
13. Plug-in package
14. Startup scripts and macroScripts
15. pip in the 3ds Max interpreter
16. Port an old tool (MaxPlus, PySide2, Python 2)
17. G10 assembled: studio validation tool, and how to test it

---

## 1. Probe the session

Goal: know the Python, PySide and mode before writing anything version-sensitive.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__python-api-whats-new-2027.md, scripting-pipeline__3dsmaxbatch-2020.md, scripting-pipeline__pymxs-renderer-2027.md
import sys
from pymxs import runtime as rt

info = {"python": sys.version.split()[0],
        "batch": bool(rt.maxOps.isInNonInteractiveMode()),
        "renderer": str(rt.renderers.current),
        "scene": str(rt.maxFilePath) + str(rt.maxFileName),
        "objects": int(rt.objects.count)}
try:
    import PySide6
    info["pyside"] = PySide6.__version__
except ImportError:
    info["pyside"] = None
result = info
```

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against scripting-pipeline__3dsmaxbatch-2020.md, scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md
(
    #( "batch=" + ((maxOps.isInNonInteractiveMode()) as string), \
       "renderer=" + (renderers.current as string), \
       "scene=" + maxFilePath + maxFileName, \
       "objects=" + (objects.count as string) )
)
```

Check: 2027 reports Python 3.13.9 and PySide 6.8.3; 2026 reports 3.11.9; 2025 reports 3.11.4 and
PySide 6.5.3. A different value means another release: re-read the "Current 3ds Max notes" in
SKILL.md.

## 2. Discover a name before using it

Goal: never guess a class, property or interface name.

GUI route (live session, human or computer-use agent): Scripting > MAXScript Listener >
MacroRecorder > Enable, do the action once, read the echoed MAXScript, translate the grammar only
(Richter, EiMNwO4buOQ 00:22:40 to 00:23:46). In 2027, `macroRecorderEmitterEnabled` gets or sets
that echo by script.

Headless route (batch, bridge): inspect.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-using-2027.md, scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md, scripting-pipeline__maxscript-python-interop-2027.md
from pymxs import runtime as rt

def prop_names(cls_or_obj):
    return [str(x) for x in list(rt.getpropnames(cls_or_obj))]

def has_global(name):
    try:
        getattr(rt, name)
        return True
    except AttributeError:  # "runtime object has no attribute": the name does not exist
        return False

wanted = ["box", "OpenPBRMaterial", "glTFMaterial", "FBXExporterSetParam", "LayerManager"]  # last four [verify]
result = {"Box": prop_names(rt.box),
          "exists": {n: has_global(n) for n in wanted},
          "importers": [str(c) for c in rt.importerPlugin.classes],
          "exporters": [str(c) for c in rt.exporterPlugin.classes]}
# interface listings print to the Listener; in batch read them from the -listenerlog file
rt.execute("showinterface python")
```

Check: every name the next script uses appears in `result` or in the listener log. Add confirmed
names to the lead's `references/api-names.txt` so `max_check` stops flagging them.

## 3. pymxs translation rules in code

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-using-2027.md, scripting-pipeline__pymxs-renderer-2027.md, scripting-pipeline__pymxs-differences-2027.md, scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md
from pymxs import runtime as rt

# MAXScript name literals: #world -> rt.Name("world")
coordsys = rt.Name("world")

# arrays cross over in the receiver's base: 0-based in Python...
first_slot = rt.meditMaterials[0]
# ...but index ARGUMENTS stay 1-based
for v in range(1, rt.viewport.numviews + 1):
    print(v, rt.viewport.getType(index=v))

# identity: wrappers differ for the same node, so compare with ==, never `is`
def same_node(a, b):
    return a == b

# scene nodes can be dict keys and set members (2019.1+)
seen = set(rt.objects)

# `max ...` commands and `$` pathnames exist only in MAXScript: go through execute
rt.execute("max tool zoomextents all")
placeholders = list(rt.execute("$PH_* as array"))

# by-reference arguments: wrap the call in a tiny MAXScript function that returns an array
rt.execute("""fn _scr_load f = (
    local miss = #()
    local ok = loadMaxFile f quiet:true missingExtFilesAction:#logmsg missingExtFilesList:&miss
    #(ok, miss)
)""")
# res = rt._scr_load(path); ok, missing = bool(res[0]), [str(m) for m in res[1]]

result = {"placeholders": [str(n.name) for n in placeholders]}
```

Check: no `is` between nodes, no `rt.max(...)`, no `rt.$`, no 0-based index passed as an argument.

## 4. Undo and animate contexts

Rule: one undo record per user-visible action, named in the user's words. The lead's `wrap()`
already opens one record around the chunk; open your own only inside tools and panels.

```python
# channel: bridge | handoff
# checked against the toolkit contract (pymxs.undo); context managers are not in the saved docs
import pymxs
from pymxs import runtime as rt

nodes = list(rt.execute("$PH_* as array"))
with pymxs.undo(True, "Rename placeholders"):  # [verify] signature in 2027
    for i, n in enumerate(nodes, 1):
        n.name = "PH_%03d" % i

node = nodes[0] if nodes else None
if node is not None:
    with pymxs.animate(True):      # [verify]
        with pymxs.attime(10):     # [verify]
            node.pos = rt.Point3(0, 0, 50)
result = {"renamed": len(nodes)}
```

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against scripting-pipeline__maxscript-bitmap-values-2027.md (animate on at time); undo context syntax not in the saved docs
(
    local nodes = $PH_* as array
    undo "Rename placeholders" on   -- [verify]
    (
        for i = 1 to nodes.count do nodes[i].name = "PH_" + (formattedPrint i format:"03d")   -- formattedPrint [verify]
    )
    if nodes.count > 0 do animate on at time 10 (nodes[1].pos = [0, 0, 50])
    nodes.count
)
```

Check: Edit > Undo once removes the whole action; a key exists at frame 10 only where intended.

## 5. Callbacks with cleanup

Rules: every callback carries a tool-specific id; remove by that id before registering and when the
tool closes. Never make tool callbacks persistent: persistent callbacks are embedded scripts that
Safe Scene Script Execution scans in every scene that carries them.

```python
# channel: bridge | handoff
# checked against scripting-pipeline__pymxs-renderer-2027.md, scripting-pipeline__maxscript-whats-new-2027.md
from pymxs import runtime as rt

CB_ID = rt.Name("studioTools_render")

def on_pre_render():
    # 2027: callbacks.notificationEvent() names the event inside the handler
    print("pre-render", rt.callbacks.notificationEvent())

rt.callbacks.removeScripts(id=CB_ID)          # idempotent: a re-run never stacks a second copy
rt.callbacks.addScript(rt.Name("preRender"), on_pre_render, id=CB_ID)

def unregister():                              # call from the panel's closeEvent and on tool reload
    rt.callbacks.removeScripts(id=CB_ID)

result = {"registered": str(CB_ID)}
```

Viewport drawing callbacks (Nitrous draws `gw` calls only inside a redraw callback):

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against scripting-pipeline__maxscript-viewport-drawing-methods-getviewportdib-2027.md
(
    unregisterRedrawViewsCallback GW_studioLabels
    fn GW_studioLabels =
    (
        gw.setTransform (matrix3 1)
        for o in objects where not o.isHiddenInVpt do gw.text o.pos o.name color:yellow
        gw.enlargeUpdateRect #whole
    )
    registerRedrawViewsCallback GW_studioLabels
    -- remove with: unregisterRedrawViewsCallback GW_studioLabels
    ok
)
```

Check: after reload, the handler fires once per event (count prints). After closing the tool,
`removeScripts` leaves no handler (render once, no print).

## 6. Worker threads and the main-thread pump

Rules (scripting-pipeline__python-threading-2027.md): no pymxs call, and no use of an object made
with pymxs, in any thread. `pymxs.mxstoken()` does not work. Threads and asyncio are for I/O only.
The doc gives no worker-to-main bridge; the QTimer queue below is a community pattern (seen in the
`max-mcp` bridge).

```python
# channel: bridge | handoff
# checked against scripting-pipeline__python-threading-2027.md, scripting-pipeline__python-creating-uis-qtmax-2027.md
# kit: maxkit_scripting (MainThreadPump)
import json
import threading
import urllib.request

import qtmax
from pymxs import runtime as rt

API_URL = "<<API_URL>>"
pump = MainThreadPump(parent=qtmax.GetQMaxMainWindow())

def apply_result(data):          # runs on the main thread: pymxs allowed
    rt.redrawViews()
    print("received", len(data))

def report_error(msg):
    print("API error:", msg)

def fetch():                     # worker: plain Python only, no rt.*
    try:
        with urllib.request.urlopen(API_URL, timeout=30) as r:
            data = json.load(r)
        pump.post(apply_result, data)
    except Exception as exc:
        pump.post(report_error, repr(exc))

threading.Thread(target=fetch, daemon=True).start()
result = {"started": True}
```

Check: the viewport stays interactive during the request (heartbeat in procedure 17); `grep` the
worker function for `rt.`: zero hits.

## 7. Dockable PySide6 panel

```python
# channel: bridge | handoff
# checked against scripting-pipeline__python-creating-uis-qtmax-2027.md, scripting-pipeline__pymxs-renderer-2027.md
# module: studio_tools/ui.py inside the package (PYTHONPATH from PackageContents.xml)
import json
import os

import qtmax
from PySide6 import QtCore, QtWidgets
from pymxs import runtime as rt

OBJECT_NAME = "StudioToolsDock"


class StudioPanel(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(OBJECT_NAME)               # lets show() find the existing instance
        self.setWindowTitle("Studio Tools")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        qtmax.DisableMaxAcceleratorsOnFocus(self, True)  # typing in the panel does not fire Max hotkeys
        body = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(body)
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["severity", "node", "message"])
        btn_load = QtWidgets.QPushButton("Load batch report")
        btn_load.clicked.connect(self.load_report)
        btn_select = QtWidgets.QPushButton("Select node")
        btn_select.clicked.connect(self.select_row_node)
        lay.addWidget(self.table)
        lay.addWidget(btn_load)
        lay.addWidget(btn_select)
        self.setWidget(body)

    def load_report(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Report", "", "JSON (*.json)")
        if not path or not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as fh:
            rep = json.load(fh)
        rows = (rep.get("result") or rep).get("findings", [])
        self.table.setRowCount(len(rows))
        for r, f in enumerate(rows):
            for c, key in enumerate(("severity", "node", "message")):
                self.table.setItem(r, c, QtWidgets.QTableWidgetItem(str(f.get(key, ""))))

    def select_row_node(self):
        item = self.table.item(self.table.currentRow(), 1)
        node = rt.getNodeByName(item.text()) if item else None
        if node is not None:
            rt.select(node)
            rt.redrawViews()                          # the UI does not refresh while Python runs

    def closeEvent(self, event):
        # unregister callbacks and stop timers here (procedures 5 and 6)
        super().closeEvent(event)


def show():
    main = qtmax.GetQMaxMainWindow()
    dock = main.findChild(QtWidgets.QDockWidget, OBJECT_NAME)
    if dock is None:
        dock = StudioPanel(main)                      # parented: Qt owns it, no garbage collection
        main.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
    dock.show()
    dock.raise_()
    return dock
```

Check: running `show()` twice gives one panel; the panel docks; closing and reopening works; capture
the UI with the lead's `capture` or a screenshot and look at it. A widget parented with
`QWidget.find(rt.windows.getMAXHWND())` works but never docks.

## 8. 3dsmaxbatch job over many files

Goal: one job, many scenes, no dialog, a JSON result per file, a summary that adds up.

The job chunk (inlined with the lead toolkit; `audit`, `xio`, `capture` are the lead's modules):

```python
# channel: batch
# checked against scripting-pipeline__3dsmaxbatch-2020.md, scripting-pipeline__3ds-max-batch-about-2027.md, toolkit contract
# kit: audit, xio, capture, maxkit_scripting
import os
from pymxs import runtime as rt

args = cmd_args()
out_dir = str(args.get("outdir", ""))
stem = str(args.get("stem", "scene"))
if not out_dir:
    raise RuntimeError("missing -mxsString outdir")
log("job start %s" % stem)

aud = audit.all()                                  # {"findings": [...], "tally": {"error", "warn", "info"}}
exports = {
    "glb": xio.export_gltf(os.path.join(out_dir, stem + ".glb")),
    "usd": xio.export_usd(os.path.join(out_dir, stem + ".usd")),
}
# no viewport in batch: the thumbnail is a render, never a viewport grab
thumb = capture.render(os.path.join(out_dir, stem + "_thumb.png"), camera=None, size=(512, 512))
result = {"scene": str(rt.maxFilePath) + str(rt.maxFileName),
          "errors": aud["tally"].get("error", 0),
          "findings": aud["findings"], "exports": exports, "thumbnail": thumb}
log("job end %s" % stem)
```

Run it over a folder from the runner:

```python
# channel: batch (runner side, plain Python)
# checked against scripting-pipeline__3dsmaxbatch-2020.md and the toolkit contract
import subprocess
import sys

cmd = [sys.executable, "scripts/batch_many.py",
       "--job", "<<JOB_CHUNK_PY>>", "--kit", "audit,xio,capture,maxkit_scripting",
       "--out", "<<OUT_DIR>>", "--workers", "2", "--timeout", "1800",
       "<<SCENES_FOLDER>>"]
proc = subprocess.run(cmd, capture_output=True, text=True)
print(proc.stdout[-2000:])
```

What `max_batch.run_batch` must put on the command line (for a hand-written run, from
scripting-pipeline__3dsmaxbatch-2020.md):

```bat
REM channel: batch
REM checked against scripting-pipeline__3dsmaxbatch-2020.md
"C:\Program Files\Autodesk\3ds Max 2027\3dsmaxbatch.exe" "<<JOB_PY>>" -sceneFile "<<SCENE_MAX>>" -mxsString outdir:"<<OUT_DIR>>" -mxsString stem:"<<STEM>>" -listenerlog "<<OUT_DIR>>\_logs\<<STEM>>_listener.log" -log "<<OUT_DIR>>\_logs\<<STEM>>_max.log" -dm on -v 3
```

`max_batch.command()` builds this list. 3dsmaxbatch 2027.3 puts each `-mxsString` value in quotes
itself, as a regular MAXScript string, so `command()` passes it unquoted with backslashes doubled;
it refuses a value holding a double quote, which 3dsmaxbatch drops. Typed by hand,
`outdir:"C:\renders"` reaches MAXScript as `"C:\renders"`, where `\r` is a carriage return: double
the backslashes or use forward slashes. The batch options come from the 2020 page; the 2027 page is
an overview only.

Exit codes: 0 success; -100 bad arguments (fix the command, do not retry); -110 Max could not start
(license, install); -120 lost contact with Max (retry once); -130 Max reported an error while
running (read the listener log, do not retry blindly). A job can end with its own code:
`quitMax quiet:true exitCode:<int>` (printed only at `-v 5`).

Modal dialogs and third-party scenes:

- `-sceneFile` only prints missing plug-ins and XRefs to the console; a Units Mismatch dialog
  (including one caused by `maxstart.max` units) or a missing-file dialog can still stop the run.
  For scenes you did not make, pass no `-sceneFile`, read the path from `-mxsString` and open it in
  the chunk with `load_scene(path, use_file_units=..., ignore_file_units=...)` so units and missing
  items are decided in code (scripting-pipeline__3dsmaxbatch-2020.md;
  scripting-pipeline__max-mcp-known-limitations-2027-3.md).
- Safe Scene Script Execution scans scripts embedded in a scene (script controllers, persistent
  callbacks, custom attributes and others). For third-party scenes set `ADSK_3DSMAX_SAFE_SCENE=1` in
  the batch process environment; `-safescene ON` is a `3dsmax.exe` switch that the 3dsmaxbatch
  option list does not show [verify that 3dsmaxbatch honors either]
  (scripting-pipeline__safe-scene-script-execution-2027.md;
  scripting-pipeline__command-line-options-2024.md).
- The docs give no scripted read of the blocked-command counter. Report blocks found in the listener
  log and `max.log` as a `security` finding per file [verify the log wording on the first run]; a
  block does not prove the scene is malicious.
- Progress: `rt.logsystem.logEntry("text", broadcast=True)` writes to the session log next to the
  listener log (3dsmaxbatch doc); the `log()` helper is the place to call it.

Check: summary `total` equals the input count; every `ok` file has a result JSON and a non-empty
export; every `failed` file has a log line; a file saved by a newer 3ds Max fails to load and is
listed, not retried.

## 9. Import and export by script

Rules: always `quiet:true` (or `#noPrompt`) so no dialog blocks; pick the class with `using:` when
two plug-ins share an extension; read what arrived by diffing the node set; exporter settings are
global state, so set and read them back every run.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md, scripting-pipeline__maxscript-whats-new-2027.md, scripting-pipeline__python-api-whats-new-2027.md
# kit: maxkit_scripting (exporter_for, log)
import os
from pymxs import runtime as rt

def import_any(path, using=None):
    before = set(rt.objects)
    kw = {"quiet": True}
    if using is not None:
        kw["using"] = using
    rt.importFile(path, **kw)
    new = [n for n in rt.objects if n not in before]
    return {"file": path, "count": len(new), "nodes": [str(n.name) for n in new[:200]]}

def export_by_suffix(path, selected_only=False):
    ext = os.path.splitext(path)[1].lstrip(".")
    cls = exporter_for(ext)                       # None: no installed exporter claims this suffix
    if cls is None:
        return {"file": path, "ok": False, "error": "no exporter for .%s" % ext}
    rt.exportFile(path, quiet=True, selectedOnly=selected_only, using=cls)
    ok = os.path.exists(path) and os.path.getsize(path) > 0
    return {"file": path, "ok": ok, "using": str(cls)}

def export_fbx(path, params, selected_only=True):
    # FBX options are global exporter state: set every run, then read back
    for key, value in params.items():
        rt.FBXExporterSetParam(key, value)        # [verify] SetParam is not in the saved docs
    readback = {k: str(rt.FBXExporterGetParam(k)) for k in params}  # GetParam: documented (2027.2 keywords)
    rt.exportFile(path, quiet=True, selectedOnly=selected_only, using=rt.FBXEXP)
    return {"file": path, "ok": os.path.exists(path), "params": readback}

result = {"exporters_for_glb": str(exporter_for("glb")), "exporters_for_usd": str(exporter_for("usd"))}
```

Format notes:

- glTF and GLB: native import and export (Khronos plug-ins) in 2027.3. No scripted option interface
  is documented, so a quiet export uses the plug-in defaults or last-used settings [verify which].
  glTF Material gives the best export; hierarchies flatten; vertex colors drop. Run the pre-check
  below first.
- USD (`.usd`, `.usda`, `.usdc`; `.usdz` export only): Python automation exists per Autodesk; the
  option names are on the MAXScript USD pages (help.autodesk.com, MAXDEV,
  `MaxScript_USD_overview_html`), not saved here [verify every name]. Until checked, export with
  `exportFile ... using:` and read the result back (up axis, scale, material target) on re-import.

glTF export pre-check (scripting-pipeline__gltf-export-2027.md): glTF Material on exported meshes;
Bitmap Texture is its only supported map input; Multi/Sub-Object nesting at most two levels; no
empty Multi/Sub slots; no two bitmaps with the same name and different type (`red.png` and `red.jpg`
export as one). A scene converted to OpenPBR still fails this check: convert to glTF Material for a
glTF target.

```maxscript
-- channel: mcp-safe | batch | bridge | handoff
-- checked against scripting-pipeline__gltf-export-2027.md (rules); traversal names not in the saved docs
(
    local findings = #()
    fn walk m depth findings =
    (
        if m == undefined then (append findings #("empty_slot", "", depth); return ok)
        local c = (classOf m) as string
        if depth > 2 do append findings #("nesting_over_2", m.name, depth)
        local n = getNumSubMtls m                                    -- [verify]
        if n > 0 then for i = 1 to n do walk (getSubMtl m i) (depth + 1) findings   -- [verify]
        else if not (matchPattern c pattern:"*gltf*") do append findings #("not_gltf_material", m.name, c)   -- class name [verify]
    )
    for o in geometry where o.material != undefined do walk o.material 1 findings
    local seen = #()
    for b in (getClassInstances Bitmaptexture) where b.filename != undefined do   -- getClassInstances [verify]
    (
        local stem = toLower (getFilenameFile b.filename)
        local ext = toLower (getFilenameType b.filename)
        for s in seen where s[1] == stem and s[2] != ext do append findings #("same_name_bitmaps", stem, ext)
        append seen #(stem, ext)
    )
    findings
)
```

Check: zero findings before a glTF export; an `empty_slot` inside a Multi/Sub-Object is a fail;
`not_gltf_material` lists what needs converting (scenario-3dsmax-materials owns the conversion).

- OBJ (`ObjImp`, `ObjExp`) and FBX (`FBXIMP`, `FBXEXP`) are in the documented class list. OBJ
  options live in an INI; `setINISetting` is blocked through `mcp-safe`, so set them before a batch
  run, by hand or from a batch script [verify INI keys].
- Gaussian splats (2027.2+): `PLYImport`, `PLYExport`, `LCCImport`, `SPZImport` filters are
  documented.

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md; whether importFile passes Safe Scene Script Execution is not documented
(
    local f = @"<<ASSET_PATH>>"
    if not (doesFileExist f) then #("missing", f) else
    (
        local before = objects.count
        importFile f #noPrompt
        #("imported", objects.count - before)
    )
)
```

Check: imported count above zero; names, units and material classes read back (the lead's
`xio.import_any` returns them); for an export, re-import into a reset scene in a separate batch run
and compare node count and bounding size.

## 10. Scene files without data loss

`saveMaxFile` and `saveNodes` overwrite silently; `loadMaxFile` replaces the scene without the save
prompt. Every save goes to a new name.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md
# kit: maxkit_scripting (save_copy, versioned_path, load_scene)
import os
from pymxs import runtime as rt

src = "<<SCENE_MAX>>"
out_dir = "<<OUT_DIR>>"

# units decided in code: the 2027.1 defaults follow maxOps.GetSceneFileUnitHandlingBehavior()
loaded = load_scene(src, use_file_units=False)    # quiet, allowPrompts false, missing items logged
saved = None
if loaded["ok"]:
    base = os.path.join(out_dir, os.path.splitext(os.path.basename(src))[0] + "_work.max")
    saved = save_copy(base)                       # _work_v001.max, _v002 ... never overwrites
    # save-down: which saveAsVersion years 2027 accepts is not in the saved docs
    down = versioned_path(base.replace("_work", "_2025"))
    rt.saveMaxFile(down, saveAsVersion=2025, useNewFile=False, quiet=True)  # [verify] 2025 accepted

# merge only some layers from another file (2027): preview first, without loading
lib = "<<LIBRARY_MAX>>"
preview = []
if os.path.exists(lib):
    # getMaxFileObjects rows: name, level, handle, parent handle, then (2027+) layer, bone,
    # group head, group member, superclass, influenced nodes, color as int, color
    rows = rt.getMaxFileObjects(lib, quiet=True)
    preview = [(str(r[0]), str(r[4]) if len(r) > 4 else None) for r in rows]
    # mergeNodesByLayer=True merges the nodes on those layers; False brings only the layers
    rt.mergeMAXFile(lib, rt.Name("autoRenameDups"), rt.Name("useSceneMtlDups"),
                    rt.Name("neverReparent"), quiet=True,
                    layers=["Furniture"], mergeNodesByLayer=True)
    merged = [str(n.name) for n in rt.getLastMergedNodes()]
else:
    merged = []
result = {"loaded": loaded, "saved": saved, "preview": preview[:200], "merged": merged}
```

`getMAXFileObjectNames <file> quiet:true` returns names only (any release; case sensitive for
`mergeMAXFile`); `getMaxFileObjects` adds layer, group and color from 2027. Both read the file
without merging it.

Check: the source file's size and modified time are unchanged; the new file exists and `isMaxFile`
is true; every merged name was in the preview.

## 11. Bitmaps and viewport capture

Rules: set format options before `.filename`; gamma and pixel aspect are fixed at creation; `close`
every bitmap you saved or rendered in a loop; the viewport capture exists only in a UI session (none
in batch).

```python
# channel: bridge | handoff
# checked against scripting-pipeline__pymxs-renderer-2027.md, scripting-pipeline__maxscript-bitmap-values-2027.md
import os
from pymxs import runtime as rt

def capture_active(path, alpha=False, jpeg_quality=None):
    dib = rt.viewport.getViewportDib(captureAlpha=alpha)   # active viewport, gamma corrected
    if jpeg_quality is not None:
        rt.jpeg.setQuality(jpeg_quality)                   # BEFORE .filename or it is ignored
    dib.filename = path
    size = (int(dib.width), int(dib.height))
    ok = bool(rt.save(dib))
    rt.close(dib)                                          # frees the frame buffer now
    return {"ok": ok and os.path.exists(path), "path": path, "size": size}

def same_image(a_path, b_path, tolerance_px=50, variation=8):
    return bool(rt.CompareBitmaps(a_path, b_path, tolerance_px, variation, useAlpha=False))

result = capture_active(os.path.join("<<OUT_DIR>>", "view_v001.png"))
```

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against scripting-pipeline__maxscript-viewport-drawing-methods-getviewportdib-2027.md, scripting-pipeline__maxscript-bitmap-values-2027.md; whether `save` passes Safe Scene Script Execution is not documented
(
    local dib = gw.getViewportDib captureAlpha:false gammaCorrect:true
    dib.filename = @"<<OUT_DIR>>\view_v001.png"
    local ok = save dib
    local wh = [dib.width, dib.height]
    close dib
    #(ok, wh)
)
```

Color management: under OCIO, `save` takes `outputColorConversion:` (`#automatic`, `#noConversion`,
`#colorSpaceConversion` with `outputColorSpace:`, `#displayViewTransform` with `outputDisplay:` and
`outputViewTransform:`). A thumbnail or review PNG wants the display view transform so it matches
the viewer; a data map wants `#noConversion`. `colorSpace:` on `bitmap` and `openBitmap` works only
under OCIO, `gamma:` only under gamma management
(scripting-pipeline__maxscript-bitmap-values-2027.md).

Memory in long loops: render into one reused bitmap with `to:`, `close` after `save`, then
`gc light:true`; `freeSceneBitmaps()` drops the map cache. Pixel work: `getPixels` and `setPixels`
work on one row; `pasteBitmap ... type:#function` is 3 to 5 times faster than per-pixel loops.

Check: file exists, size equals the viewport size, mean luminance not near 0 or 255 (use the lead's
`max_review.image_checks`), then look at it.

## 12. Render calls and pre-render callbacks

Rules: Render Setup pre and post scripts run only from the UI render button; `render()` fires
`#preRender` and `#postRender` callbacks. Change settings with Render Setup closed. Save before an
Arnold render: it can crash 3ds Max.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-renderer-2027.md, scripting-pipeline__pymxs-bitmaps-2027.md, uv-baking-texturing__maxscript-render-to-texture-2027.md (outputSize, vfb)
# kit: maxkit_scripting (save_copy, CallbackSet)
import os
from pymxs import runtime as rt

out = os.path.join("<<OUT_DIR>>", "thumb_v001.png")
if rt.renderSceneDialog.isOpen():
    raise RuntimeError("Render Setup is open: close it before changing render settings")
renderer = str(rt.classOf(rt.renderers.current))
if not rt.maxOps.isInNonInteractiveMode() and rt.getSaveRequired():
    save_copy(os.path.join("<<OUT_DIR>>", "before_render.max"))    # crash insurance, new name

cbs = CallbackSet("studioTools_thumb").reset()
cbs.register("preRender", lambda: print("rendering with", renderer))
try:
    cams = [c for c in rt.cameras if rt.classOf(c) != rt.TargetObject]   # rt.cameras [verify]
    kw = {"outputFile": out, "vfb": False, "outputSize": rt.Point2(512, 512)}  # outputSize on camera renders [verify]
    if cams:
        kw["camera"] = cams[0]
    rt.render(**kw)
finally:
    cbs.unregister()
result = {"renderer": renderer, "file": out, "exists": os.path.exists(out)}
```

Check: the callback printed once; the file exists at the requested size; the image is not black
(scenes without lights or with a missing camera often are).

Batch Render: reading a Batch Render view's camera through `batchRenderMgr` crashes 3ds Max
(scripting-pipeline__max-mcp-known-limitations-2027-3.md). Script only writes to the views [verify
the property names], never read the camera back, and check the result in Rendering > Batch Render or
in a saved copy.

## 13. Plug-in package

Layout for a Python tool:

```
StudioTools/
  PackageContents.xml
  Contents/
    python/studio_tools/__init__.py, ui.py, core.py
    scripts/studio_tools_startup.py      post-start-up (Python allowed, UI in place)
    scripts/StudioTools.mcr              macroscripts parts
    vendor/                              pip --target wheels (cp313 for 2027)
```

```xml
<?xml version="1.0" encoding="utf-8"?>
<!-- checked against scripting-pipeline__packagecontents-format-2026.md, scripting-pipeline__packaging-plugins-2025.md -->
<ApplicationPackage SchemaVersion="1.0" AutodeskProduct="3ds Max" ProductType="Application"
    Name="Studio Tools" AppVersion="1.0.0"
    UpgradeCode="{6f1c2a4e-8b3d-4c1e-9a7f-2d5e8b9c0a11}"
    ProductCode="{a2b3c4d5-e6f7-4a8b-9c0d-1e2f3a4b5c6d}">
  <CompanyDetails Name="Studio" />
  <EnvironmentVariables>
    <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2027" SeriesMax="2027" />
    <EnvironmentVariable Name="PYTHONPATH" Value="\+;.\Contents\python" Type="path" />
    <EnvironmentVariable Name="PYTHONPATH" Value="\+;.\Contents\vendor" Type="path" />
  </EnvironmentVariables>
  <Components Description="post-start-up scripts parts">
    <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2027" SeriesMax="2027" />
    <ComponentEntry ModuleName="./Contents/scripts/studio_tools_startup.py" />
  </Components>
  <Components Description="macroscripts parts">
    <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2027" SeriesMax="2027" />
    <ComponentEntry ModuleName="./Contents/scripts/StudioTools.mcr" />
  </Components>
  <!-- folder holding ConversionPresets/<name>_preset.ms and ConversionScripts; ComponentEntry form for a folder [verify] -->
  <Components Description="scene converter folders parts">
    <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2027" SeriesMax="2027" />
    <ComponentEntry ModuleName="./Contents/SceneConverter" />
  </Components>
</ApplicationPackage>
```

Shipping the studio's conversion rules (for example legacy to OpenPBR) as a Scene Converter preset
in the package means the artist in Rendering > Scene Converter and the batch job apply the same
rules (scripting-pipeline__packagecontents-format-2026.md).

Generate fresh GUIDs per tool (`python -c "import uuid; print(uuid.uuid4())"`); keep `UpgradeCode`
forever, change `ProductCode` with every `AppVersion`. Vendored wheels are built for one Python
minor version, so `SeriesMin` and `SeriesMax` stay on one release per `Components` block (2025 and
2026 are 3.11, 2027 is 3.13).

Lint, then test:

```python
# channel: handoff (runner side, plain Python)
# status: lint runs offline; checked against scripting-pipeline__packaging-plugins-2025.md
import os
import subprocess
import sys

pkg = "<<PACKAGE_DIR>>"
lint = subprocess.run([sys.executable, "scripts/package_lint.py", pkg, "--release", "2027"],
                      capture_output=True, text=True)
print(lint.stdout)
# test load without installing: ADSK_APPLICATION_PLUGINS may point at one package folder (2022.2+)
env = dict(os.environ, ADSK_APPLICATION_PLUGINS=pkg)
print("start 3ds Max with this environment, then read max.log for package errors")
```

One-step install for artists: copy the folder to `%APPDATA%\Autodesk\ApplicationPlugins\StudioTools`
(per user, no admin) or `%ALLUSERSPROFILE%\Autodesk\ApplicationPlugins\StudioTools` (all users).
Autodesk App Store submission needs the ADN `.msi` route instead.

Check: `package_lint` 0 errors; 3ds Max starts with no Plug-in Package Manager error; the macro
appears in Customize User Interface under its category; `import studio_tools` works in the Listener.

## 14. Startup scripts and macroScripts

The post-start-up Python file of the package:

```python
# channel: handoff (file shipped in the package)
# checked against scripting-pipeline__packagecontents-format-2026.md, scripting-pipeline__maxscript-python-interop-2027.md
import sys

from pymxs import runtime as rt

if not rt.maxOps.isInNonInteractiveMode():       # no UI work in 3ds Max Batch
    try:
        import studio_tools                       # found through the package PYTHONPATH
        print("studio_tools", getattr(studio_tools, "__version__", "?"), "on Python", sys.version.split()[0])
    except Exception as exc:
        rt.logsystem.logEntry("studio_tools failed to import: %r" % (exc,), broadcast=True)
```

The macroScript (ships as a file in "macroscripts parts"; `macroScript` definitions are blocked
through `mcp-safe`):

```maxscript
-- channel: handoff (file shipped in the package)
-- checked against scripting-pipeline__maxscript-python-interop-2027.md (python.Execute); macroScript header keywords not in the saved docs
macroScript StudioTools_Open category:"Studio Tools" buttonText:"Studio Tools" tooltip:"Open the Studio Tools panel"   -- [verify] header keywords
(
    python.Execute "import studio_tools.ui as ui; ui.show()"
)
```

A plain user startup script (no package), for example to take the Python load time at startup:

```maxscript
-- channel: handoff (file in the user scripts\startup folder)
-- checked against scripting-pipeline__maxscript-python-interop-2027.md
(
    python.Init()
    format "python ready: %\n" (python.GetLastError() == "")
)
```

Through `mcp-safe` the client cannot add menus, toolbar buttons, hotkeys or startup scripts; write
the file, tell the user to place it (or confirm the path) and restart 3ds Max.

## 15. pip in the 3ds Max interpreter

Rules: install with the interpreter that ships with 3ds Max, never a system Python; never write into
Program Files from a tool; Autodesk gives no support for third-party packages.

```bat
REM channel: handoff (run by the user in a terminal)
REM note: path and flags from the 2027 Extension Libraries page as summarized in reports/research/01 (page not saved) [verify]
"C:\Program Files\Autodesk\3ds Max 2027\Python\python.exe" -m pip install --user requests
REM shipped tools: vendor wheels into the package instead, with the same interpreter
"C:\Program Files\Autodesk\3ds Max 2027\Python\python.exe" -m pip install --target "<<PACKAGE_DIR>>\Contents\vendor" requests
```

Check inside 3ds Max: `import requests; print(requests.__file__)` resolves to the user site or the
package `vendor` folder; `sys.version` is 3.13.x on 2027.

## 16. Port an old tool (MaxPlus, PySide2, Python 2)

1. Run `python scripts/port_scan.py <tool_folder>`; fix every `error`, read every `warning`.
2. Apply the table below; compile with Python 3.13 (`python3.13 -m py_compile`).
3. Run the tool in a live session through `handoff`; then its batch part through `batch`.

| Old                                              | 3ds Max 2027                                                     |
| ------------------------------------------------ | ---------------------------------------------------------------- |
| `MaxPlus.FileManager.Open(p)` / `.Save(p)`       | `rt.loadMaxFile(p, quiet=True)` / `rt.saveMaxFile(p)` (new name) |
| `MaxPlus.Core.EvalMAXScript(s).Get()`            | `rt.execute(s)`                                                  |
| `MaxPlus.GetQMaxWindow()`, `MakeQWidgetDockable` | `qtmax.GetQMaxMainWindow()` + `QDockWidget`                      |
| `MaxPlus.CUIFrame.Create()`                      | PySide6 widget                                                   |
| `from PySide2 import ...`                        | `from PySide6 import ...`                                        |
| `dialog.exec_()`                                 | `dialog.exec()` [added]                                          |
| `QtWidgets.QAction`                              | `QtGui.QAction` [added]                                          |
| `QRegExp`                                        | `QtCore.QRegularExpression` [added]                              |
| `print "x"`, `xrange`, `iteritems`               | `print("x")`, `range`, `items`                                   |
| `random.randint(0.0, 1.0)`                       | `random.randint(0, 1)` or `random.uniform(0.0, 1.0)`             |
| `setmxsprop("pos.x", v)` (seen in a video)       | `node.pos = rt.Point3(x, y, z)`                                  |
| `sys.path.append(...)` in every script           | package `PYTHONPATH` environment entry                           |

Check: `port_scan` reports 0 errors; the panel opens, docks and closes in 2027; a batch run returns
exit code 0.

## 17. G10 assembled: studio validation tool, and how to test it

Structure (one package, three parts sharing one core):

- `core/` pure pymxs logic, no Qt: calls the lead's `audit.all()` (its `units`, `names`, `maps`
  checks cover the studio rules; rules themselves come from scenario-3dsmax-scene), `xio.*`,
  `capture.render`; material conversion to OpenPBR comes from scenario-3dsmax-materials. A `VRayMtl`
  can switch to its OpenPBR shading mode (V-Ray 7, not on V-Ray GPU;
  materials-lookdev__vray7-vraymtl.md): count it as convertible, not manual. The OpenPBR class name
  is discovered at run time (procedure 2) and kept in the tool's config.
- Security: the batch runs with Safe Scene Script Execution on (procedure 8) and lists blocked
  embedded scripts as findings.
- glTF output runs the pre-check (procedure 9) and reports what is not glTF Material.
- `batch` job chunk (procedure 8) driven by `batch_many.py`; one 3dsmaxbatch process per file; each
  process takes a license and RAM, so size `--workers` to both.
- `ui.py` dock panel (procedure 7) that reads reports and calls the web API through the pump
  (procedure 6); heavy work goes to a batch run on a saved copy, never inside the panel.
- Package (procedure 13) with a post-start-up script and a macroScript.

Responsiveness probe for the panel test:

```python
# channel: bridge | handoff
# checked against scripting-pipeline__python-creating-uis-qtmax-2027.md; threshold [added]
import time

import qtmax
from PySide6 import QtCore


class Heartbeat(QtCore.QObject):
    def __init__(self, parent=None, interval_ms=50):
        super().__init__(parent)
        self.last = time.perf_counter()
        self.max_gap = 0.0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(interval_ms)

    def _tick(self):
        now = time.perf_counter()
        self.max_gap = max(self.max_gap, now - self.last)
        self.last = now


hb = Heartbeat(qtmax.GetQMaxMainWindow())
# trigger the panel's API call now; read hb.max_gap after it returns: pass below 0.2 s
result = {"started": True}
```

Test ladder (stop at the first failure):

1. Offline: `python3.13 -m py_compile` on every `.py`; `port_scan` 0 errors; `package_lint` 0
   errors; the lead's `max_check` on every chunk (and `channel="mcp-safe"` on MAXScript meant for
   it).
2. Seven fixture scenes through `batch_many.py` (clean, wrong units, missing bitmap, wrong renderer,
   bad names, newer-version file, a script controller with a blocked command): each report flags
   exactly its planted defect; the newer-version file is `failed` with a log line; no run hangs on a
   dialog; summary total equals 7.
3. Exports: each `.glb` and `.usd` exists and is non-empty; re-import in a fresh batch run gives the
   same node count.
4. Thumbnails: contact sheet with the lead's `max_review.contact_sheet`, then look: not black,
   subject framed.
5. Live session (`handoff` or `bridge`; the Autodesk 3ds Max MCP server runs only MAXScript at level
   10 and Python at admin level 20, needs an MCP Apps client, and keeps a blocked command blocked
   until restart): `ui.show()` twice gives one dock; heartbeat gap below 0.2 s during an API call;
   closing the panel leaves no callback (procedure 5 check).
6. Install: copy the package to `%APPDATA%\Autodesk\ApplicationPlugins`, restart, macro present,
   panel opens.
