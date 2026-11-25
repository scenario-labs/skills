# Procedures: scene assembly in 3ds Max 2027.3

Each block names its channels and the source it was checked against. Names that are not in the saved
2027 docs carry `[verify]` on the same line; the helpers in `scripts/maxkit_scene.py` wrap those
calls so a wrong name returns a finding instead of stopping the run.

Conventions:

- Runner side: `scripts/scene_run.py` prepends `maxkit_scene.py` to your chunk and calls the lead's
  `max_wrap.wrap()`. The chunk sets `result`; the wrapper writes
  `{ok, result, error, log, max_version}` as JSON.
- Inside 3ds Max: `rt` and `pymxs` are globals of the chunk (the lead's wrapper binds them). The
  wrapper puts the whole chunk in one undo record; the write helpers open their own
  `pymxs.undo(True, "label")` inside it so they stay safe when called outside the wrapper.
- UPPERCASE names in a chunk (`SOURCE_PATH`, `OUT_PATH`, `STEP`...) are values the runner fills in
  before `make()`, for example `body.replace("SOURCE_PATH", repr(path))`. Never hard-code a user
  path.
- Write helpers default to `dry_run=True`. Run dry, read the plan, then run with `dry_run=False` on
  a versioned copy.
- Lengths assume the system unit the audit reports. Helpers convert to centimeters through
  `cm_per_unit()`: centimeters per unit times `units.SystemScale` [verify]. Exact factors: inches
  2.54, feet 30.48, miles 160,934.4, millimeters 0.1, centimeters 1, meters 100, kilometers 100,000.
  A file at 1 unit = 1 inch that reads 2.54 times too small in a centimeter scene has had its unit
  ignored, not rescaled.
- Name patterns: test with Python `re` or MAXScript `findString <name> <regex> useRegex:true`
  (2027.2 and later, `maxscript-whats-new-2027.md`). The saved docs do not describe `matchPattern`;
  do not rely on it for character classes such as `[0-9]` [verify].
- Never save over the client file. Work on `<name>_v002.max` beside it, or in a sibling `work/`
  folder.

## P1. Intake audit, read only

Goal: know units, origin, structure, weight and missing files before touching anything. Channels:
`batch` first (the heavy file never opens in an artist's session), `bridge` or `handoff` second,
`mcp-safe` for the short MAXScript twin.

```python
# channel: batch | handoff
# checked against the toolkit contract of scenario-3dsmax-expert and scripting-pipeline__3dsmaxbatch-2020.md
import sys
sys.path.insert(0, sys.argv[1])            # this skill's scripts/ folder
import os
from scene_run import audit_exit_code, audit_script
from max_batch import run_batch            # lead toolkit, found by scene_run

scene, out_dir = sys.argv[2], sys.argv[3]  # never hard-code paths
envelope = os.path.join(out_dir, "scene_audit.json")  # must not exist yet
res = run_batch(audit_script(out_dir, far_cm=100000.0), scene=scene, log_dir=out_dir, timeout=3600)
print("audit ok" if audit_exit_code(res, envelope) == 0 else "audit failed")
```

`far_cm` is the spec's `max_far_m` x 100: the gate fails when the audit cutoff is larger. Then judge
it offline: `python scripts/scene_gate.py <out_dir>/scene_audit.json spec.json`.

`-sceneFile` already prints missing plug-ins and XRefs to the console log (`3dsmaxbatch-2020.md`);
keep that log with the JSON. Opening a client file headless also keeps Safe Scene Script Execution
between embedded scripts and the artist's session; leave it enabled
(`safe-scene-script-execution-2027.md`). Before anyone opens a file from outside the team in a live
session, keep Safe Scene Script Execution on and Scene Security Tools installed: Scene Security
Tools removes only known malicious scripts, Safe Scene Script Execution blocks unsafe commands of
new ones (same doc).

Live session through the Autodesk 3ds Max MCP server (`mcp-safe`): propose
`scene_run.mxs_audit_script()` (the audit inside the lead's MAXScript result protocol, undo off), or
`scripts/mxs/scene_audit.ms` as is. It changes nothing and avoids dotNet, INI and file-write calls.
It returns one string. It covers `BitmapTexture` plus `VRayBitmap`, `CoronaBitmap` and `ai_image`
when those renderers are installed (class and property names `[verify]`); the pymxs audit is the
fuller check.

Check in the result:

- `units.system_type` and `system_scale` against the project spec; `load_unit_behavior` and
  `merge_unit_behavior` (2027.1 rules).
- `origin.far`: every node whose bounding-box center is farther than 1 km [added default]; a site
  model may justify more, decide with the System Unit Setup accuracy calculator. The test uses the
  bounding-box center, not the pivot: CAD linework often keeps its pivot at 0,0,0 while its geometry
  sits kilometers out.
- `scale.non_unit_scale`: geometry nodes whose scale is not (1,1,1) (FS1 checklist).
- `groups.max_depth`, `names.default_named`, `names.duplicate_names`, `layers.on_layer_0`.
- `polys.top`: the heaviest nodes. File size follows face count, not object size (Master ArchViz,
  SRVCuw9aPI8 01:20).
- `copies.removable_bases`: how many meshes instancing would remove.
- `maps.missing`, `xrefs.xref_scenes[].exists`, `points.rows`, `smooth.viewport_iter_above_0`.

## P2. Project template and units

Goal: one system unit for the whole team, set before any geometry exists. Rule: never change the
system unit in a populated scene; the helper refuses (`fundamentals-scene__system-unit-setup.md`).

```python
# channel: batch | bridge | handoff
# checked against fundamentals-scene__system-unit-setup.md and scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md
# Chunk body (scene_run.make prepends maxkit_scene). template_path comes from the runner.
template_path = TEMPLATE_PATH              # set by the runner, e.g. via .format() or an args file
if len(rt.objects) > 0 or rt.getSaveRequired():  # live session with work in it: refuse, never reset
    result = {"changed": False, "reason": "session holds objects or unsaved changes"}
else:
    rt.resetMaxFile(rt.Name("noPrompt"))
    result = set_units_on_empty_scene("centimeters", 1.0, "metric", "centimeters")
if result["changed"]:
    if rt.doesFileExist(template_path):
        result["saved"] = False
        result["reason"] = "template exists; choose a new name"
    else:
        result["saved"] = bool(rt.saveMaxFile(template_path, quiet=True))
```

Same thing for `mcp-safe` (a blank session only):

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against fundamentals-scene__system-unit-setup.md
if objects.count == 0 then
(
	units.SystemType = #centimeters -- [verify]
	units.SystemScale = 1.0 -- [verify]
	units.DisplayType = #metric -- [verify]
	units.MetricType = #centimeters -- [verify]
	"units set: " + (units.SystemType as string)
)
else "refused: scene has " + (objects.count as string) + " objects"
```

Check: `units_report()` shows the target values. Display units may change at any time; only the
system unit is frozen (Autodesk, aPc02tZzj8c 02:16).

## P3. Rebuild into the template by merge

Goal: bring a mixed-unit scene into the template with the right size, instead of changing units
under it. Why: merge rescales the incoming file to the current system unit when `ignoreFileUnits` is
false (doc). A file saved in inches merged into a centimeter template keeps its real size.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (mergeMAXFile flags, layers:, ignoreFileUnits:, getLastMergedNodes, getMaxFileObjects)
source_path = SOURCE_PATH                  # set by the runner
layers_wanted = LAYERS                     # [] for everything; layer names otherwise (2027+)
before = len(list(rt.objects))
peek = rt.getMaxFileObjects(source_path, quiet=True)      # 2027: per-node layer, group and class data
kw = dict(quiet=True, ignoreFileUnits=False)              # rescale to the template's system unit
if layers_wanted:
    kw.update(layers=layers_wanted, mergeNodesByLayer=True)
with pymxs.undo(True, "scene: merge source"):
    ok = rt.mergeMAXFile(source_path, rt.Name("autoRenameDups"), rt.Name("renameMtlDups"),
                         rt.Name("neverReparent"), rt.Name("noRedraw"), **kw)
merged = list(rt.getLastMergedNodes())
result = {"ok": bool(ok), "source_nodes": len(peek), "merged": len(merged),
          "objects_after": len(list(rt.objects)), "objects_before": before,
          "units": units_report(), "origin": origin_report()}
```

Check:

- `merged` equals the nodes you expected from `peek`.
- Measure three known items (door leaf, worktop height, ceiling) from their bounding boxes: within 1
  cm of the drawing [added tolerance].
- A wrong-size piece from one freelancer (a 3 m wall reading 3 cm or 300 m) is scaled alone, then
  Reset XForm, never by changing units (VizAcademy, hz07nIgm7EA 00:21:31). Hand Reset XForm to the
  modeling sibling if the stack matters.

GUI equivalent: keep Respect System Units in Files on; pick Rescale in the File Load: Units Mismatch
dialog.

## P4. Recenter far geometry

Goal: the work area near 0,0,0. Far from the origin you get camera jitter, viewport clipping and
flipped normals (system-unit-setup doc; aPc02tZzj8c 08:04).

```python
# channel: batch | bridge | handoff
# checked against fundamentals-scene__system-unit-setup.md; isAnimated, setUserProp [verify]
plan = recenter(offset=None, helper_name="REF_SiteOrigin", dry_run=True)
result = {"plan": plan}
# Read plan["offset"] (system units) and plan["skipped_animated"], then on the versioned copy:
# result["done"] = recenter(offset=plan["offset"], dry_run=False)
```

Rules:

- Move everything together (geometry, cameras, targets, lights, helpers) by one offset. A partial
  move breaks alignment.
- Animated nodes are skipped and listed. Move them by hand or route them to
  scenario-3dsmax-animation-rigging.
- A linked Revit or FBX file has a Point helper at the model origin when "Create Helper at Model
  Origin" was on (default). Move that helper instead of the linked objects (file-link settings doc).
- Store the offset (`REF_SiteOrigin` user property and the result JSON) so an updated DWG or survey
  lands in the same place.
- Outliers: a node far from every other node is usually stray CAD linework or a leftover, and it
  drags the scene center. List it separately; delete it only after the user confirms, and only if no
  camera, shadow or reflection needs it (VN2qUrEHDPo 00:07:27) [added rule].
- Precision check: before choosing the work area, type the largest remaining distance into the
  System Unit Setup accuracy calculator; the smallest significant detail must stay above the
  Resulting Accuracy and above one system unit (aPc02tZzj8c 00:06:27; System Unit Setup doc).

Check: `origin_report()["far_count"] == 0`; capture the camera views (P12) and look for jitter or
z-fighting.

## P5. Groups, names and layers

Goal: no nested groups, no default names, every node on a meaningful layer.

```python
# channel: batch | bridge | handoff
# checked against fundamentals-scene__scene-explorer-2027.md; isGroupHead, explodeGroup, LayerManager, layer.addNode [verify]
step = STEP                                # "plan" or "apply", set by the runner
plan_groups = flatten_groups(dry_run=(step == "plan"))

def layer_for(node):
    """Numbered layers after render.camp (FYRj1pCBQq8 05:17); adjust to the studio standard."""
    sc = str(rt.superClassOf(node))
    if sc == "camera":
        return "100_cams"
    if sc == "light":
        return "101_light"
    if sc == "shape" and node.name.upper().startswith(("CAD", "A-", "3D-")):
        return "102_cad"
    return None                            # architecture, furniture, decor: decided from names below

layer_plan = {}
for n in rt.objects:
    lname = layer_for(n)
    if lname:
        layer_plan.setdefault(lname, []).append(n.name)
result = {"groups": plan_groups,
          "layers": apply_layers(layer_plan, dry_run=(step == "plan")),
          "names": name_report()}
```

Then rename:

- Build `{old: new}` from the recorded `group_path` user property, the material name and the layer,
  for example `300_walls` holds `WALL_Living_01`.
- Call `rename_nodes(mapping, dry_run=True)`; it refuses any clash.
- List the names you could not derive for a human pass; never invent meaning.

Layer scheme (render.camp, FYRj1pCBQq8 frame 13:04): `100_cams`, `101_light`, `200_ceiling_base`,
`201_ceiling_int`, `300_walls`, `301_doors`, `400_floor`, `500_lamps`, `600_dec`. Most essential
first, decoration last. Layer 0 cannot be renamed or deleted; leave it empty.

Check: `group_report()["max_depth"] <= 1`, `name_report()["default_named"] == 0`,
`layer_report()["on_layer_0"] == 0`. Visual: hide each layer in turn and capture; leftovers show
what was missed (FYRj1pCBQq8 09:20).

### P5b. Scene-wide scale audit

Every geometry node should carry scale (1,1,1), not only the pieces you rescaled in P3 (FS1
checklist and candidate procedure 1). A scaled node makes modifiers, noise, bump and UVs act in
scaled space (VizAcademy, hz07nIgm7EA 00:21:31).

```python
# channel: batch | bridge | handoff
# checked against fundamentals-scene/_digest_batch1.md (candidate procedure 1) and hz07nIgm7EA 00:21:31; node.scale, ResetXForm, collapseStack, getNodeByName [verify]
plan = reset_scale(dry_run=True)
result = {"plan": plan, "report": scale_report()}
# Nodes in plan["with_modifiers"] keep their stack: reset_scale(names=..., collapse=False, dry_run=False)
# Collapse only nodes with no modifier worth keeping: reset_scale(names=..., collapse=True, dry_run=False)
```

Rules:

- Reset XForm adds an XForm modifier; collapse bakes it. Collapse only where the stack is not
  needed; otherwise route the node to scenario-3dsmax-modeling.
- Instances share one base object: resetting one instance with a collapse makes it unique. Check
  instances first.
- Check: `scale_report()["non_unit_scale"] == 0`, or every remaining offender listed with its
  reason.

## P6. Copies to instances

Goal: one base object per repeated mesh. Instances cut file size and viewport load (SRVCuw9aPI8:
331,973 KB to 147,649 KB in one test).

```python
# channel: batch | bridge | handoff
# checked against SRVCuw9aPI8 (method) and Y-zZn8bo1cE (semantics); instanceReplace, getPolygonCount [verify]
cands = copy_candidates(min_count=2)
# Keep only rows whose nodes really are the same model: same signature AND same material.
safe = [g for g in cands["rows"] if g["signature"][4] and len(g["nodes"]) >= 2]
result = {"candidates": cands["groups"], "removable_bases": cands["removable_bases"],
          "plan": instance_copies(safe, dry_run=True), "sample": safe[:10]}
# After reading the sample: instance_copies(safe, dry_run=False)
```

Rules:

- The signature is class, face and vertex counts, object-space size to 1 mm, and material. Vertex
  order is not compared; capture a few groups before and after.
- Copies with different modifiers above the base become wrong instances. Use Reference when the base
  must be shared and the top of the stack must differ (Kory Bieg, Y-zZn8bo1cE 03:30).
- Links can be broken later (Make Unique) but never added. Decide before editing.
- An instance edit propagates to every instance. Warn the user before editing shared props.

- Static small parts in one room (skirting pieces, sockets, fixings) that never move apart: attach
  them into fewer objects; 3ds Max handles fewer objects better, and attach beats groups
  (VN2qUrEHDPo 00:08:20). Attach by material so the result stays editable [added].
- Repeated assets (trees, chairs, boxes) placed as separate copies: rebuild them as Point Instance
  on points (2027.2 and later; P11) or a scatter plugin. Scatter audit: count identical-geometry
  copies that are not instances and any Array output as meshes above a project threshold (FS3
  scatter checklist, YB330UhrdOA).

Proxies (V-Ray `.vrmesh`, Corona proxy) are renderer-specific; hand the export to
scenario-3dsmax-archviz. Before any proxy export (Master ArchViz, SRVCuw9aPI8 04:50 to 06:31):

- Store the materials in Material Editor slots first; a proxy does not hold them.
- Reset XForm if the object was scaled, or the proxy comes in at the original scale.
- Attach parts with Match Material IDs to Material (the dialog default).
- Set the preview faces (5,000 in the video); `vrayMeshExport()` [verify] runs the export when the
  menu entry is missing (06:00).

Check: `stats.diff(before, after)` shows fewer unique meshes; file size measured after saving, not
before (SRVCuw9aPI8 03:37); a test render matches the original.

## P7. Missing maps: relink, collect, archive

Goal: zero missing assets on every team machine.

```python
# channel: batch | bridge | handoff
# checked against fundamentals-scene__asset-tracking-2027.md; getClassInstances and map path properties [verify]
search_dirs = SEARCH_DIRS                  # list of folders, from the user
report = relink_maps(search_dirs, dry_run=True)
result = {"relink_plan": report, "missing_before": missing_maps_report()["missing_count"]}
# Apply only unique matches: relink_maps(search_dirs, dry_run=False)
```

Rules:

- Relink only to a unique file with the same name. Report ambiguous matches with their candidates;
  never pick one silently.
- Never remove a map reference to clear a warning; a removed map is a lost look (Connecter note,
  mbi-7pTItcU 15:03).
- Renderer bitmaps (VRayBitmap, CoronaBitmap, Arnold image) use other property names; the helper
  probes them `[verify]`. Asset Tracking (Shift+T [verify]) shows every asset class and is the
  cross-check.
- Splat files loaded through a Gaussian Splat object are tracked assets too (3DGS doc).
- Material cleanup after relinking, in the style of a Material Auditor pass (YB330UhrdOA 13:31,
  frame): strip maps that are only a flat or solid color, replace duplicate bitmap maps with one
  instanced map, delete unused Multi/Sub-Object materials, fix material name conflicts. Hand this
  list to scenario-3dsmax-materials; leftover Standard or Physical materials go through Scene
  Converter (Rendering > Scene Converter, `scene-converter-2027.md`) there.

Collect and hand off:

- GUI: Asset Tracking > Paths menu repaths; Resource Collector gathers files.
- Script: `rt.archiveMAXFile(zip_path, quiet=True)` zips the scene and its maps (2019.1 and later,
  doc-confirmed). Check that `zip_path` does not exist first.

Check: `missing_maps_report()["missing_count"] == 0` and Asset Tracking shows no Missing status.

## P8. Split into XRef scenes

Goal: two people never edit the same objects; the lighting scene stays light.

```python
# channel: batch | bridge | handoff
# checked against fundamentals-scene__xref-objects-2027.md and 2Nqp9n95pzE; saveNodes doc-confirmed; xrefs.addNewXRefFile [verify]
names = NODE_NAMES                         # e.g. every node on 300_walls and 400_floor
out_path = OUT_PATH                        # new file, e.g. <project>/APT_Arch.max
result = split_to_xref(names, out_path, dry_run=True)
# On the versioned working copy: split_to_xref(names, out_path, dry_run=False)
```

Structure (Jake Denham, 2Nqp9n95pzE 02:02): one file per discipline (interior, exterior), and a
master render scene that holds lights, cameras, environment and render settings and only XRefs the
rest. The master carries no polygons of its own.

Rules:

- Finalize layout first: XRef scene content cannot be selected or moved in the master (SRVCuw9aPI8
  07:48).
- Automatic update off; Update Now after the source is saved (2Nqp9n95pzE 02:46). The update flag is
  set in the XRef Scenes dialog; its script name is not in the saved docs.
- Do not merge an XRef back and re-save it over its source (2Nqp9n95pzE 03:21).
- Objects that depend on others (path constraints, space warps, emitters) must share one XRef
  record; render effects do not travel (XRef Objects doc).
- Merging an XRef object that links a DWG drops the DWG link (XRef Objects doc).
- File locking between team members: the sources give no convention. The sourced rule is structural:
  one owner per XRef file, and the master only references. Agree who saves which file before work
  starts [added].
- Use XRef Objects when one asset is reused across scenes; use XRef Scenes for discipline splits.
  Containers (`.maxc`, Create > Helpers > Container) suit locked, hand-off blocks; the source is a
  2010 video, so re-check behavior in 2027.

Check: `xref_report()` lists each file with `exists: true`; `poly_report()` of the master is near
zero; one render of the master matches the pre-split render.

## P9. Viewport performance pass

Goal: an interactive viewport without changing the render.

```python
# channel: batch | bridge | handoff
# checked against fundamentals-scene__controlling-display-performance-2027.md and hz07nIgm7EA 00:16:18; TurboSmooth property names [verify]
result = {"smooth": smooth_viewport_off(dry_run=True), "top": poly_report(top=20)["top"],
          "points": point_report()}
# apply: smooth_viewport_off(dry_run=False)
```

Order of effect, cheapest first: 0. Delete what no camera, shadow or reflection sees (VN2qUrEHDPo
00:07:27), and keep detail only where the shot list needs it: placeholders first, detail near camera
(VizAcademy, hz07nIgm7EA 00:55:48). Get the camera list from the user before deleting anything.

1. TurboSmooth or OpenSubdiv viewport iterations to 0, render iterations 1 or 2 only near camera
   (VizAcademy, hz07nIgm7EA 00:16:18, 00:49:47).
2. Copies to instances (P6); repeated scatter through Point Instance (P11) or the scatter plugin.
3. Hide or freeze layers not being worked on. Hide and Freeze also affect final rendering (display
   performance doc): record every layer you hid, and unhide it or confirm it is meant to be absent
   before any render.
4. Heavy non-hero props as proxies (P6); dense rocks or plants placed by hand belong in a scatter
   (hz07nIgm7EA 00:14:29: a 3 GB scene from manual rocks).
5. Separate exterior and interior scenes; hidden objects still load (hz07nIgm7EA 01:15:28).
6. Adaptive Degradation and Progressive Display (GUI, Viewport preferences); splat Viewport Limit
   percentage (P11).

Measure: `stats.snapshot()` before and after; time a full redraw with `rt.timestamp()` around
`rt.completeRedraw()` `[verify]` in a live session (no viewport in batch); capture the same view
before and after with `capture.viewport()`.

## P10. CAD, Revit, SketchUp and FBX intake

Goal: few meaningful objects at the right scale, and a link that survives client revisions.

Decide first:

- Live design (revisions expected): link through File > References > Manage Links (GUI; no
  documented script API). Revit or FBX: Combine Entities By Revit Material for look-dev speed (49
  objects against 384 with Do Not Combine, CGI Made Simple, cv7bIWciFU4 04:31); By Category or
  Family Type when you need Family and Category in Scene Explorer or Multi/Sub-Object data. Combine
  cannot change on reload: choose at link time.
- Frozen design: import headless, combine by material in script, accept that the link is gone.

Headless import (`batch`, `bridge`, `handoff`); importer class names are doc-confirmed, their option
names are not:

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (importFile, importer classes); FBXImporterSetParam keys [verify]
src = SOURCE_PATH                          # .fbx, .rvt, .skp, .dwg
ext = src.lower().rsplit(".", 1)[-1]
importer = {"fbx": rt.FBXIMP, "rvt": rt.Revit_importer, "skp": rt.sketchUp,
            "dwg": rt.AutoCADImport, "dxf": rt.AutoCADImport}[ext]
if ext == "fbx":
    rt.FBXImporterSetParam("ConvertUnit", "cm")           # [verify] key and value
    rt.FBXImporterSetParam("Lights", False)                # [verify] Revit FBX lights become unique lights
before = set(n.name for n in rt.objects)
with pymxs.undo(True, "scene: import " + ext):
    ok = rt.importFile(src, rt.Name("noPrompt"), using=importer)
new = [n for n in rt.objects if n.name not in before]
multi = [n.name for n in new if n.material is not None and str(rt.classOf(n.material)) == "Multimaterial"]
lights = [n.name for n in new if rt.superClassOf(n) == rt.light]
open_shapes, uninspected = [], []
for n in new:
    if rt.superClassOf(n) == rt.shape:
        try:
            count = int(rt.numSplines(n))                    # [verify]
            if count == 0 or not all(rt.isClosed(n, i) for i in range(1, count + 1)):
                open_shapes.append(n.name)
        except Exception:  # not an editable spline: inspect after an Edit Spline
            uninspected.append(n.name)
result = {"ok": bool(ok), "new_objects": len(new), "multi_material_objects": len(multi),
          "lights": len(lights), "open_shapes": open_shapes[:100], "uninspected_shapes": uninspected[:100],
          "units": units_report(), "origin": origin_report()}
```

Check:

- Object count against the combine choice; one-object imports with many materials mean the source
  was not grouped (studioGAD, sQiA1X4XlMw 03:23).
- `lights`: many unique lights from a Revit FBX hurt performance; light the scene in 3ds Max instead
  (file-link doc).
- A linked Daylight System prompts for exposure control; answer Yes or renders overexpose (file-link
  doc, written for Scanline and Quicksilver).
- `open_shapes` and `uninspected_shapes` both empty before extruding CAD outlines: closed polylines
  on separate `3D-` layers are prepared in AutoCAD (Autodesk, 1pEqaqq8v_Y 04:54).
- Units: SketchUp and 3ds Max in the same unit (mm in sQiA1X4XlMw 00:33); DWG link has Rescale and
  Incoming File Units (Revit link doc).
- Origin: survey-coordinate CAD sits kilometers away; run P4 on the link helper.

## P11. Gaussian splats and point objects (2027.2 and later)

Goal: a splat capture at the right scale and orientation, light in the viewport, rendered by a
renderer that supports it.

```python
# channel: batch | bridge | handoff
# checked against fundamentals-scene__gaussian-splat-3dgs-in-3ds-max-2027.md and scripting-pipeline__maxscript-whats-new-2027.md (PLYImport, SPZImport, LCCImport, GaussianSplat class names); property names read at run time
src = SOURCE_PATH                          # .ply, .spz or .lcc
ext = src.lower().rsplit(".", 1)[-1]
importer = {"ply": rt.PLYImport, "spz": rt.SPZImport, "lcc": rt.LCCImport}[ext]
before = set(n.name for n in rt.objects)
with pymxs.undo(True, "scene: import splat"):
    ok = rt.importFile(src, rt.Name("noPrompt"), using=importer)
new = [n for n in rt.objects if n.name not in before]
splats = [n for n in new if str(rt.classOf(n.baseObject)) in ("GaussianSplat", "Editable_Point")]
result = {"ok": bool(ok), "splats": [n.name for n in splats],
          "props": [[str(p) for p in rt.getPropNames(n.baseObject)] for n in splats[:1]],
          "bbox_m": [origin_report(far_cm=float("inf"))["extents"]],
          "renderer": str(rt.classOf(rt.renderers.current))}
```

Then, using the property names that `props` returned (do not guess them):

- Units and Up Axis: set from the capture source; the PLY Preset (Generic, Postshot, Substance 3D,
  WorldLabs) sets the up axis that software expects. Fix a wrong rotation with Up Axis, not by
  re-importing.
- Viewport Limit percentage on dense captures; Render Limit separately. Both pick points at random.
- Display: Off (default) or Shader (2027.3), which sorts back to front and matches render color more
  closely, at a viewport cost.

Rules:

- File > Import embeds the splat data in the scene. A Gaussian Splat object with its File parameter
  keeps a live reference: the file can be swapped or updated, and it is tracked by Asset Tracking
  and the Resource Collector. Choose by file size and update needs.
- Editable Point loads the file once into its own data; edits stay in the scene.
- Non-destructive edits: Point Select plus any modifier (Bend, XForm work on splats); convert to
  Editable Point only for per-point edits (Eloi Andaluz, YB330UhrdOA 01:42, 02:14). Convert back
  with Convert To > GaussianSplat.
- Gaussian Splat objects do not support instances (3DGS doc). Scatter splats through Turn to Point
  plus Point Instance.
- Rendering: Arnold renders splats with relighting and shadows; V-Ray and Corona only if they adopt
  the API (YB330UhrdOA 01:08). Check `renderer` before promising a render; route lighting to
  scenario-3dsmax-lighting-rendering.
- Array modifier output set to points, fed to Point Instance: about 5 times faster on small arrays
  (YB330UhrdOA 06:39). `outputType` is the documented Array property name.

Generated splat worlds (Scenario MCP) arrive through scenario-3dsmax-generation; this procedure
takes over at import.

Check: bounding box size in meters plausible for the capture; captures from four views
(`capture.views`); an Arnold test render only when Arnold is the project renderer.

## P12. Save the version and verify

Goal: a clean `_v00N` file with numbers and captures that prove it. Build it with
`make(body, kit=("audit", "stats", "capture"))` so the capture module is inlined.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (saveMaxFile overwrites silently, doesFileExist)
out_path = OUT_PATH                        # <name>_v002.max, never the client file
if rt.doesFileExist(out_path):
    result = {"saved": False, "reason": "exists"}
else:
    saved = bool(rt.saveMaxFile(out_path, quiet=True, useNewFile=False))
    result = {"saved": saved, "scene": audit_scene()}
    try:
        result["stats"] = stats.snapshot()
        capture.views(OUT_DIR)             # lead toolkit: persp, front, left, top
    except NameError:
        result["kit"] = "lead maxkit not inlined"
```

Check:

- `scene_gate.py` passes every blocking gate on the saved file, opened fresh (P1 on `out_path`).
- File size read after saving.
- Contact sheet of captures (`max_review.contact_sheet`): nothing missing, no exploded-group holes,
  no gray untextured hero objects.
- One test render per key camera compared with the client draft (lighting sibling renders it).
- The file opens on a second machine or a fresh batch run with no missing assets.
