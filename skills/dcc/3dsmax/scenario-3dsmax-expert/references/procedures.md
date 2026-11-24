# Procedures (lead)

Every block is a chunk for `max_wrap.wrap()` unless it says otherwise. Inside a chunk the kit
modules (`stats`, `audit`, `capture`, `xio`), `rt`, `pymxs`, `log()` and `result` are already bound.
Run `max_check.check(code=..., channel=...)` before sending. Names marked `[verify]` are not in the
saved docs.

## P1. Find the channel

Runner side. Goal: know what the agent can do before planning.

```python
# channel: runner (any OS)
# checked against scripting-pipeline__max-mcp-connect-external-client-2027-3.md
import sys
sys.path.insert(0, "<skill>/scripts")  # the skill's scripts folder, passed in by the caller
import max_env
info = max_env.doctor()
print(info["channel"], info["mcp_ports"], info["bridge"], info["notes"])
```

Check:

- `handoff` on macOS or Linux is expected. 3ds Max is Windows only.
- `mcp-safe` means a port answers. It does not mean this agent's client supports MCP Apps. Ask the
  user which client is connected.
- `bridge`: run a harmless create plus capture first (P4 on a scratch box, then undo).

## P2. Inspect (read only)

Goal: numbers and findings before any change.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-using-2027.md (rt, main thread)
snap = stats.snapshot()
rep = audit.all(expect={"units": "centimeters", "renderer": "Arnold", "max_faces": 2000000})
log("objects", snap["objects"], "errors", rep["tally"]["error"])
result = {"snapshot": snap, "audit": rep}
```

The same through mcp-safe, as MAXScript (wrap with `lang="maxscript", kit=["stats", "audit"]`):

```maxscript
-- channel: mcp-safe | batch | bridge | handoff
-- checked against scripting-pipeline__max-mcp-known-limitations-2027-3.md (no blocked command)
result = mxk_dict #(#("snapshot", mxk_stats_snapshot()), #("audit", mxk_audit_all expectUnits:"centimeters" expectRenderer:"Arnold"))
```

Check:

- `result.ok` is true and `max_version` names 2027.
- Read every `error` finding before planning. Units mismatch and missing maps change the plan.
- `save_required` true: the user has unsaved work. Ask before saving anything.

## P3. Save a new increment (never over the user's file)

Goal: a restore point that does not rename the open scene.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md
import os
folder, name = str(rt.maxFilePath), str(rt.maxFileName)
if not name:
    raise RuntimeError("scene was never saved; ask the user for a file name")
target = capture.next_free(os.path.join(folder, name))  # lobby.max -> lobby_v002.max when taken
ok = rt.saveMaxFile(target, useNewFile=False, quiet=True)
result = {"backup": target, "ok": bool(ok), "current_file": str(rt.maxFileName)}
```

Through mcp-safe, saving is not documented as allowed: propose it, and if refused ask the user to
use File > Save As (Copy). Check that `current_file` is still the user's name and that the backup
exists.

## P4. One staged change inside one undo record

Goal: the change, on its own layer, editable, reversible with one Ctrl+Z. Example: put placeholder
boxes `PH_*` on layers by room, taken from their name `PH_<Room>_<Item>`.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-using-2027.md; layer calls [verify]
before = stats.snapshot()
moved = []
for o in list(rt.objects):  # [verify] objects
    parts = str(o.name).split("_")
    if len(parts) < 3 or parts[0] != "PH":
        continue
    layer_name = "Furniture - " + parts[1]
    layer = rt.LayerManager.getLayerFromName(layer_name)  # [verify] LayerManager.getLayerFromName
    if layer is None:
        layer = rt.LayerManager.newLayerFromName(layer_name)  # [verify] LayerManager.newLayerFromName
    layer.addNode(o)  # [verify] layer.addNode
    moved.append([str(o.name), layer_name])
result = {"moved": moved, "diff": stats.diff(before, stats.snapshot())}
```

`max_wrap` puts the chunk inside `pymxs.undo(True, label)`. Check that the diff shows only `layers`
changed and that the moved count equals the `PH_*` count.

Replacing the placeholders with real assets is P7a, then P7b per placeholder. Keep the `PH_*` boxes
hidden on their layer until the user approves.

## P5. Verify by looking

Goal: four framed views, one contact sheet, read once.

```python
# channel: bridge | handoff (no viewport in batch)
# checked against scripting-pipeline__maxscript-viewport-drawing-methods-getviewportdib-2027.md
shots = capture.views(capture_dir, views=("persp", "front", "left", "top"), size=1024)  # capture_dir passed by the caller
result = {"captures": [s["path"] for s in shots]}
```

Then, runner side:

```python
# channel: runner (any OS)
# status: checked offline with generated images only
import max_review
paths = payload["result"]["captures"]  # payload: the parsed result JSON
flags = {p: max_review.image_checks(p)["flags"] for p in paths}
sheet = max_review.contact_sheet(paths, "review/sheet_v001.png", cols=2, thumb=600)
```

Check:

- No `all_black`, `uniform` or `low_contrast_center` flag.
- Open the sheet. The subject reads in every view, and the top view matches the plan dimensions.
- In batch, render through cameras with `capture.render()` instead.

## P6. Render test views through cameras

Goal: test images without touching Render Setup. Save first, because an Arnold render can crash 3ds
Max.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-renderer-2027.md (render outputFile)
out = []
for cam_name in cameras:  # list passed by the caller; never guess camera names
    out.append(capture.render(render_dir + "/test_" + cam_name + ".png", camera=cam_name, size=1280))
result = {"renders": out, "renderer": str(rt.classOf(rt.renderers.current))}
```

Check:

- Each file exists, and `image_checks` raises no flags.
- The render time is reported. A render that never returns usually means a modal dialog (missing
  maps, units mismatch).

## P7. Import an asset and report what arrived

```python
# channel: batch | bridge | handoff (mcp-safe: importFile in Safe mode not documented)
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md and scripting-pipeline__gltf-import-2027.md
rep = xio.import_any(asset_path)  # suffix picks the importer; #noPrompt and quiet pass
result = {"import": rep, "audit": audit.all(expect={"units": "centimeters"})}
```

Check:

- `count` is above 0, `size` is plausible in system units (a chair is about 80 to 100 cm), and the
  material classes are listed.
- Generated meshes are raw input. Send them to scenario-3dsmax-game-assets or scenario-3dsmax-scene
  for cleanup.
- A `.max` is merged with `#autoRenameDups #renameMtlDups #neverReparent quiet:true`: the defaults
  prompt for duplicates and reparenting. Options: `ignore_file_units`, `layers`,
  `merge_nodes_by_layer` (2027). Run P7a first.
- Preview a `.max` before merging: `getMAXFileObjectNames f quiet:true` lists names;
  `getMaxFileObjects` adds each node's layer (file-loading doc).

## P7a. Units preflight before a merge or load

Goal: no Units Mismatch dialog in a live session. "Respect System Units in Files" (on by default)
raises it on open, merge and XRef (fundamentals-scene__system-unit-setup.md). A script cannot close
it.

```python
# channel: batch (never in a live session: loadMaxFile replaces the scene without a prompt)
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (loadMaxFile useFileUnits: quiet: allowPrompts:)
ok = rt.loadMaxFile(asset_path, useFileUnits=True, quiet=True, allowPrompts=False)  # asset_path passed by the caller
result = {"ok": bool(ok), "unit": str(rt.units.SystemType), "scale": float(rt.units.SystemScale)}  # [verify] units.SystemType, units.SystemScale
```

Then compare with the live scene's unit and scale from `stats.snapshot()`:

- Equal: merge with `ignore_file_units=True`. Nothing needs rescaling, so nothing asks.
- Different: do not merge into the live scene. In batch, merge into a scene in the project's units,
  scale by the unit ratio, Reset XForm, save `<asset>_units.max`, then merge that (fundamentals
  `_digest_batch1` procedure 3).
- The saved docs do not say whether `quiet:true` alone suppresses the Units Mismatch dialog. Do not
  rely on it.
- Also compare `maxstart.max` units with the scene's: a mismatch shows the dialog at every start
  (max-mcp-known-limitations-2027-3.md).

## P7b. Fit a merged asset to a placeholder box

Goal: the asset on the box's base, centered, at the box's size and rotation. Count the box's scale
once: measure the box in its own frame with scale removed (the measured size then includes its
scale), and place in that same frame. Measuring `width * scale` and then applying `ph.transform`
applies the scale twice.

```maxscript
-- channel: bridge | handoff | mcp-safe (mergeMAXFile under Safe mode not documented)
-- checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (mergeMAXFile flags, mergedNodes:, ignoreFileUnits:); bounds and matrix calls [verify]
-- Inputs: phName, assetFile; P7a found equal units. The asset's front faces the box's local -Y [added].
fn fitBounds nodes tm = (  -- union of the nodes' bounds in frame tm
    local lo, hi
    for n in nodes do (
        local bb = nodeGetBoundingBox n tm  -- [verify] nodeGetBoundingBox
        if lo == undefined then (lo = bb[1]; hi = bb[2]) else (
            lo = [amin lo.x bb[1].x, amin lo.y bb[1].y, amin lo.z bb[1].z]  -- [verify] amin
            hi = [amax hi.x bb[2].x, amax hi.y bb[2].y, amax hi.z bb[2].z]))  -- [verify] amax
    #(lo, hi)
)
ph = getNodeByName phName  -- [verify] getNodeByName
xf = ph.transform  -- [verify] transform
xf.row1 = normalize xf.row1; xf.row2 = normalize xf.row2; xf.row3 = normalize xf.row3  -- [verify] row1, normalize
merged = #()
ok = mergeMAXFile assetFile #autoRenameDups #renameMtlDups #neverReparent quiet:true ignoreFileUnits:true mergedNodes:&merged
tops = for n in merged where n.parent == undefined collect n
pb = fitBounds #(ph) xf  -- box size, its scale counted here and only here
ab = fitBounds merged (matrix3 1)  -- asset in world space, as merged
pS = pb[2] - pb[1]; aS = ab[2] - ab[1]
ratios = [pS.x / aS.x, pS.y / aS.y, pS.z / aS.z]
s = ratios.z  -- fit by height unless the brief names another axis
root = Point name:(phName + "_FIT") pos:[(ab[1].x + ab[2].x) / 2, (ab[1].y + ab[2].y) / 2, ab[1].z]  -- [verify] Point
for n in tops do n.parent = root
root.transform = (scaleMatrix [s, s, s]) * (transMatrix [(pb[1].x + pb[2].x) / 2, (pb[1].y + pb[2].y) / 2, pb[1].z]) * xf  -- [verify] scaleMatrix, transMatrix
fb = fitBounds merged xf
wa = fitBounds merged (matrix3 1); wp = fitBounds #(ph) (matrix3 1)
result = #(ok, merged.count, ratios, fb[1] - pb[1], fb[2] - pb[2], wa[1] - wp[1], wa[2] - wp[2])
```

Check:

- `ok` is true and the merged count matches the preview.
- In the box frame, the base offset `fb[1].z - pb[1].z` is under 0.1 cm and the fitted axis under 1
  cm [added].
- World space: for a box rotated by a multiple of 90 degrees about Z, the asset's world bounds match
  the box's within 1 cm per side [added].
- Report all three `ratios`. Two that disagree mean an approximate box, a units problem or a wrong
  front axis; ask before forcing a non-uniform scale.
- Top and front orthographic captures (P5) with the boxes shown. Then hide the `PH_*` layer.

## P8. Batch over many files (headless)

Runner side. Goal: the same script on each file, originals untouched, one process per file.

```python
# channel: batch (runner side, Windows)
# checked against scripting-pipeline__3dsmaxbatch-2020.md (options, exit codes)
import max_batch, max_wrap
job = max_wrap.wrap(chunk, kit=["audit", "xio"])  # chunk reads out_dir from maxOps.mxsCmdLineArgs
reports = []
for scene in scenes:  # list of .max paths given by the user
    r = max_batch.run_batch(job, scene=scene, args={"out_dir": out_dir}, timeout=1800, log_dir=log_dir)
    reports.append({"scene": scene, "ok": r["ok"], "meaning": r["meaning"], "seconds": r["seconds"]})
```

Check:

- Exit code -130 means 3ds Max reported an error. Read `listener_log`.
- Files saved in a newer 3ds Max fail to open. Report them, do not retry.
- Exporter options are global state: set them in the chunk (FBX) or record them in the report.

## P9. Handoff

Goal: the user runs the script and sends back evidence.

1. `wrap(chunk, kit=[...], result_path=None)`. In handoff the script prints `MXK_RESULT <json>` to
   the Listener. Give a `result_path` the user chooses if a file is easier.
2. Tell the user: Scripting > Run Script, pick the file, then send the result JSON or the Listener
   line, plus captures.
3. Parse the JSON. Never assume the script ran: no JSON means no evidence.
