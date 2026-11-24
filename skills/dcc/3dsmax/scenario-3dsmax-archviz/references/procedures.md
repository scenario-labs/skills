# Archviz procedures (agent side)

How a chunk reaches 3ds Max (lead contract, as implemented in scenario-3dsmax-expert
`scripts/max_wrap.py`):

- `max_wrap.wrap(code, lang="python", kit=[...])` adds one undo record and the result protocol; the
  chunk sets `result`.
- `wrap()` inlines only the lead's maxkit modules (`stats`, `capture`, `audit`, `xio`, `result`) and
  binds them as globals: call `stats.snapshot()`, `capture.render(...)` without importing them.
- This skill's helpers are pasted above the chunk by `archviz_plan.chunk(code, args)`: it writes an
  `ARGS` dict literal, then `scripts/maxkit_archviz.py`, then the code, and compiles the result on
  the runner. Call helpers by bare name (`camera_report()`).
- Paths always come from `ARGS`; never type a user path into a chunk.

```python
# channel: runner (produces a script for batch | bridge | handoff)
# status: runner-side; chunk() compiled locally; wrap() signature read from scenario-3dsmax-expert scripts/max_wrap.py
import archviz_plan as ap
import max_wrap
script = max_wrap.wrap(ap.chunk(CODE, {"out_dir": out_dir}), lang="python", kit=["stats", "capture"],
                       result_path=out_dir + "/result.json")
```

Names marked `[verify]` are not in the saved docs; the helpers look plugin property names up with
`getPropNames` and report what they found, so read the first result before writing settings.

Runner-side Python (`archviz_plan.py`) was executed locally with python3 against the source numbers
(727 x 26.5 s = 5.35 h; 90 x 900 s = 22.5 h).

## P0. Revit and DWG link decisions (GUI)

Goal: the link-time choices that decide lighting, exposure and material work later. General cleanup
(units, layers, origin, CAD cleanup, XRefs) stays with scenario-3dsmax-scene. The saved docs give no
script control for link presets: treat this as GUI work (archviz digest 1, GUI section) and record
each choice in the intake report.

Revit (RVT or FBX), from `archviz-production__file-link-revit-fbx-settings.md` and cv7bIWciFU4:

1. In Revit, export the FBX from a 3D view (a floor plan view grays the export out); heavy families
   such as people, cars and plumbing fixtures slow it (cv7bIWciFU4 00:00:50, 00:02:00).
2. File > Import > Link Revit or Link FBX > Manage Links > Presets tab: create or Modify a preset
   before attaching. Combine Entities is set only here; a reload cannot change it.
   - By Revit Material: fewest objects (49 against 384 in cv7bIWciFU4 00:04:31); Multi/Sub-Object
     information is lost.
   - By Revit Category or By Family Type: Multi/Sub-Object kept, Family and Category visible in
     Scene Explorer.
   - As One Object: massing or shadow studies. Do Not Combine: avoid on a large model.
3. Lights: off when the source is a Revit FBX. The export turns every light instance into a unique
   light object, which can wreck performance; light in 3ds Max instead (doc warning; cv7bIWciFU4
   00:06:16).
4. Daylight System: when it links, 3ds Max prompts to turn on exposure control. Answer Yes, or
   renders come out overexposed. The saved page (2023) names the exposure types for Scanline and
   Quicksilver only; with Arnold, V-Ray or Corona, check the active exposure in a test render and
   hand the setting to scenario-3dsmax-lighting-rendering.
5. Material group: Use Scene Material Assignments on Reload (default off) keeps 3ds Max assignments
   when the link reloads; off, a reload re-applies the Revit materials. Turn it on before any
   texturing if the link will reload (cv7bIWciFU4 frame 00:06:39). Use Scene Material Definitions
   (default off) uses material definitions from the 3ds Max scene instead of the Revit drawing's.
6. Bind only when the design is frozen; binding removes the link and with it Reload (cv7bIWciFU4
   00:07:52). Other defaults on the same page: Curved Objects Detail 10; Auto-Smooth off, 15 degrees
   when on; Create Helper at Model Origin on (not available on reload).

DWG or DXF (`archviz-production__revit-file-link-2027.md`; 1pEqaqq8v_Y):

- File > Import > Link AutoCAD: turn on Rescale and set Incoming File Units when the drawing unit
  differs.
- Closed polylines (BPOLY) on their own 3D layers, gaps fixed in CAD first; 3ds Max side spline
  checks belong to scenario-3dsmax-scene.

Terrain from survey contours: no saved source covers it. Hand the build to scenario-3dsmax-scene or
scenario-3dsmax-modeling and confirm the tool in the 3ds Max 2027 help before quoting a method.

Check: the P1 report lists lights per class (a long list of unique lights after a Revit FBX is a
fail); one test render is not overexposed; the preset name and its Combine Entities choice are
written in the intake report.

## P1. Archviz intake audit (read-only)

Goal: know cameras, units, scatter objects, animation and output settings before planning. Run after
scenario-3dsmax-scene has cleaned the model.

```python
# channel: batch | bridge | handoff
# checked against archviz digests 1 to 4, pymxs-renderer-2027 doc

from collections import Counter
result = {
    "units": units_info(),
    "lights": dict(Counter(str(rt.classOf(l)) for l in rt.lights if rt.superClassOf(l) == rt.light)),  # [verify] superClassOf filter
    "cameras": camera_report(),
    "scatter": scatter_inventory(dump_props=False),
    "anim": anim_report(),
    "stats": stats.snapshot(),
}
```

mcp-safe: propose `scripts/mxs/archviz_audit.ms` through `wrap(code, lang="maxscript")`; it prints
the same facts as text.

Check in the result:

- `units.system_type` equals what the architect delivered; never rescale here.
- Each camera row: `props.focal_mm` present (not FOV-only); `auto_vtilt` value true on exteriors; a
  `None` entry means the name list missed the real property: rerun with `prop_dump(node)` and record
  the real name.
- `scatter` lists every Forest Pack, RailClone, Chaos Scatter and proxy object. An empty list on a
  planted scene means the class strings differ: dump `str(rt.classOf(obj))` for a known scatter and
  update `SCATTER_CLASSES`.
- `stats` face count against the budget the scene skill set.
- `lights` per class: after a Revit FBX link, many light objects of one class means the export made
  every instance unique; relink with Lights off (P0).

## P2. Camera candidates and the contact sheet

Goal: 4 to 8 numeric candidates per view, compared side by side, before anything is dressed
(oKYzIh7KfH0; f40Sszm3Bqk 00:01:03 to 00:02:37; JmmgSQp6FYI 00:00:11).

```python
# channel: batch | bridge | handoff
# checked against oKYzIh7KfH0, f40Sszm3Bqk, JmmgSQp6FYI notes; Physical camera props [verify] via maxkit_archviz

# view spec in meters, world Z up; values come from the brief, not from these examples
CANDIDATES = [
    {"name": "CAM_V01_a", "pos": (12.0, -18.0, 1.4), "target": (0.0, 0.0, 3.0), "focal": 30},
    {"name": "CAM_V01_b", "pos": (10.0, -20.0, 1.4), "target": (0.0, 0.0, 2.5), "focal": 35},
    {"name": "CAM_V01_c", "pos": (16.0, -14.0, 0.6), "target": (0.0, 0.0, 5.0), "focal": 24},
]
OUT_DIR = ARGS["out_dir"]  # passed by the runner; never a hard-coded path

made = []
for c in CANDIDATES:
    row = make_camera(c["name"], c["pos"], c["target"], c["focal"], film_mm=36.0, auto_vtilt=True)
    row["png"] = capture.render(f"{OUT_DIR}/{c['name']}.png", camera=c["name"], size=(1200, 800))["path"]
    made.append(row)
result = made
```

`ARGS` comes from `archviz_plan.chunk(code, {"out_dir": ...})`. `capture.render` writes to the next
free file name and returns a dict with `path`.

Runner side, after the chunk returns:

```python
# channel: runner
# status: runner-side; max_review signatures read from scenario-3dsmax-expert scripts/max_review.py
import json
import max_review
payload = json.load(open(out_dir + "/result.json", encoding="utf-8"))  # {ok, result, error, log, max_version}
pngs = [r["png"] for r in payload["result"]]
max_review.contact_sheet(pngs, out_dir + "/V01_candidates.png")
for p in pngs:
    print(p, max_review.image_checks(p))
```

Check:

- `unset` empty for every camera; if `auto_vtilt` is unset, verticals converge: set it in the GUI
  (gui-paths) and record the property name.
- Contact sheet read once (one image, not each render). Reject candidates with tilted verticals, the
  main feature centered by default, or the horizon cutting the building at mid-height.
- Keep the two best per view for the client; rename the winner `CAM_V01` after sign-off.

## P3. General feeling pass (order and checks only)

Goal: gray base, HDRI, two helper lights, flat area colors, tone mapping (64vzHYEWedI 00:04:23 to
00:40:04). Settings belong to scenario-3dsmax-materials and scenario-3dsmax-lighting-rendering; this
skill runs the order:

1. Renderer check (`rt.renderers.current`), displacement enabled if any will be used.
2. HDRI in the environment, rotated before any helper light (demo rotation minus 50 degrees).
3. One base material, warm mid gray, slight reflection; assigned for real, not by override.
4. Two helper area lights as copies (not instances) for emphasis.
5. Copy the base per area (walls, floor, ceiling, cabinets); change color only. Walls and floor
   first.
6. Tone mapping: contrast up, exposure down slightly, a little desaturation, vignette.
7. Optional: clay render to scenario-3dsmax-generation for mood variants when the brief is open
   (64vzHYEWedI 00:36:43). Check: `capture.render` of each approved camera at review size, then the
   squint test in critique.md.

## P4. Scatter setup checks (Forest Pack, Chaos Scatter, RailClone)

Goal: every scatter is cheap in the viewport, correct at render, and editable. Scatter creation and
most settings are GUI (gui-paths); code checks the inputs.

```python
# channel: batch | bridge | handoff
# checked against 8s2gF4vb6yk 00:02:16 and 00:04:38, mbi-7pTItcU 00:53:06

SOURCES = ARGS["source_names"]       # scatter source objects
AREAS = ARGS["area_spline_names"]    # include and exclude splines
src = [rt.getNodeByName(n) for n in SOURCES]
spl = [rt.getNodeByName(n) for n in AREAS]
result = {
    "pivots_off": pivot_base_report([n for n in src if n], tol_m=0.01),
    "open_splines": spline_closed_report([s for s in spl if s]),
    "missing": [n for n, o in zip(SOURCES + AREAS, src + spl) if o is None],
    "scatter": scatter_inventory(dump_props=True),
}
```

Fix chunk, only after the report and only on listed nodes:

```python
# channel: batch | bridge | handoff
# checked against 8s2gF4vb6yk 00:02:16 (pivot to base)
nodes = [rt.getNodeByName(n) for n in ARGS["fix_pivots"]]
result = {"fixed": set_pivot_base([n for n in nodes if n])}
```

Check in the result, then in the plugin UI:

- `pivots_off` empty. A proxy source cannot take a pivot edit the same way: fix the source mesh and
  re-export [added].
- `open_splines` empty. GUI fallback test from the expert: add Edit Poly; a closed spline turns into
  a polygon, an open one vanishes; weld with a tiny threshold.
- With `dump_props=True`, record the real names of count, max limit, seed, camera clipping and edge
  mode for this plugin build before any scripted edit. Without them, set values in the GUI.
- Settings to confirm per scatter (GUI or recorded names): Normal versus Z 1 for trees; slope limit;
  per-square distribution; avoid collisions; edge trimming (Chaos Scatter) or Boundary Checking Edge
  plus a Forest Edge map in Opacity for Corona and Arnold (Forest Pack); camera clipping with Extend
  view; viewport previz capped (Max instances or Max Items).
- Real density only from a test render, never from the viewport count.

Decisions and settings from `archviz-production__forestpack-rendering-best-practice.md` (digest 1 #1
to #8) and SRVCuw9aPI8:

- Meshes or proxies: Forest Pack turns scattered meshes into native instances, so proxies save
  memory, not time. In one SRVCuw9aPI8 test, proxies raised render time from 8m49s to 11m31s. Use
  proxies only when system RAM is short; on a huge scene, test both.
- Proxy export (SRVCuw9aPI8 00:05:26 to 00:06:31): store the material first; Reset XForm if the
  object was scaled; attach the pieces with Match Material IDs to Material; about 5,000 preview
  faces; `vrayMeshExport()` when the menu entry is missing (arguments [verify]).
- Large areas: keep a dense or solid distribution map and raise the density value; a sparse map is
  the wrong tool. Randomize X and Y translation against a grid look. For huge scenes, scatter
  pre-composed larger patches.
- Material: Geometry rollout > Material Override on the Forest object. Without an override the
  source object's material is used; a material dropped on the Forest object in the Material Editor
  is not the path.
- Background and midground plants: reflection Max Depth about 1, glossy reflections or reflections
  off in the background, never refraction and opacity together.
- Alpha-map leaves: mesh leaves render faster because ray tracers are slow on transparency. If alpha
  maps are used, turn filtering off on opacity bitmaps for stills (animation may flicker without
  it), make the alpha slightly smaller than the diffuse to avoid halos, and cut away empty plane
  area.

## P5. Lawn build (Forest Pack, GUI with numeric checks)

Order from iToo (_0MeIRhEQI4):

1. Terrain: Subdivide, then a mild Noise; keep borders flat with soft selection under the Noise.
2. Library Browser > Layered Lawns > Large > a base preset; Boundary Checking Edge near paving.
3. Overlays as Copy clones of the base object, each loading an overlay preset; raise the Density
   value to thin them.
4. Mown: Transform, separate axes, Z 40 to 50%.
5. Stripes: midground by a solid Gradient Ramp, planar world XYZ, 150 cm, into diffuse or
   reflection; close-up by Detail presets with X rotation driven by a black and white map.
6. Max Items or Max Objects raised or 0 for Detail presets; Z Offset up if rotated plants sink.
   Check: test render at the hero camera; overlays subtle, no repeating patch pattern, no grass on
   paving.

## P6. Aerial photo match

Goal: a render that drops onto a drone photo (iIYYzosZ1Mo 00:03:24 to 00:10:41). Runner side:

```python
# channel: runner
# status: runner-side; executed locally with fixed numbers; exif_camera needs exiftool installed
import archviz_plan as ap
plan = ap.exif_camera(photo_path)   # or ap.aerial_camera(8064, 6048, 24, 120) from read values
print(plan)
```

In Max:

```python
# channel: batch | bridge | handoff
# checked against iIYYzosZ1Mo notes; primaryVisibility and camera props [verify]

plan = ARGS["plan"]           # dict from archviz_plan.exif_camera
site_xy = ARGS["site_xy_m"]   # site center in scene meters
rt.renderWidth = plan["render_width"]  # [verify]
rt.renderHeight = plan["render_height"]  # [verify]
cam = make_camera("CAM_AERIAL", (site_xy[0], site_xy[1] - 1.0, plan["camera_height_m"]),
                  (site_xy[0], site_xy[1], 0.0), plan["focal_mm"], film_mm=plan["film_width_mm"],
                  auto_vtilt=False)
shadow = [rt.getNodeByName(n) for n in ARGS["shadow_only_names"]]
result = {"camera": cam, "shadow_only": shadow_only([n for n in shadow if n])}
```

Then by hand or computer use: photo as viewport background, camera and target grouped and moved
until the map overlay lines up; Daylight System north aligned to the map, date, time and location
from EXIF (Motion panel); render EXR with alpha. The starting position above is a placeholder:
alignment is visual. Check:

- Render size equals photo size; focal never changed during alignment.
- Overlay at 50% opacity: roads, shorelines and building corners coincide.
- Shadow-only trees cast onto the site and are absent from the beauty pass.
- Post: blur, noise, then one sharpen; shared color correction (critique.md).

## P7. Animation settings and budget

Goal: one fps everywhere, numbered output, measured frame time.

```python
# channel: batch | bridge | handoff
# checked against ZHCVMQeWPEg 00:06:36 and 00:08:44, pymxs-renderer-2027 doc
a = ARGS
report = set_anim_output(a["fps"], a["first"], a["last"], a["out_path"], a.get("width"), a.get("height"))
sec = time_test_frame(a["camera"], a["test_frame"], a["test_png"])  # pick the heaviest frame
result = {"anim": report, "test_frame_seconds": sec}
```

Runner side:

```python
# channel: runner
# status: runner-side; executed locally
import json
import archviz_plan as ap
print(ap.shot_ranges([4, 3, 5, 4, 4], fps=25))
payload = json.load(open(result_path, encoding="utf-8"))
print(ap.render_budget(frames=500, sec_per_frame=payload["result"]["test_frame_seconds"], nodes=1))
```

Check: fps equals Anima or Vantage; range length equals seconds x fps; budget hours with margin
under the deadline, else change engine, resolution or node count before launch. Save the scene
before any Arnold render (MCP limits page).

## P8. Vantage route

Max side (V-Ray scene): renderer is V-Ray (check `rt.renderers.current`); a Corona scene goes
through the V-Ray Scene Converter first (gMUKCmaeQhc 00:00:10), and in Corona 13 the Vantage
Animation Export button in Render Setup sends animated objects (JmmgSQp6FYI 00:12:20). Export or
Live Link is a menu action; no export function name is in the saved docs [verify]. Inside Vantage
everything is GUI: build sub-states (environment, lighting, color), bundle them into Scene States,
two camera snapshots per shot in the Video Editor, linear transitions for steady moves, a different
environment state on the end camera to move the sun. Render with the settings in Numbers;
first-frame time feeds `render_budget`. Before the first Vantage render (gMUKCmaeQhc 00:02:12, frame
00:08:15):

1. Turn every light off after conversion, then back on one by one at about half intensity, checking
   each.
2. Read the memory estimate in the Vantage render dialog (about 3.1 GB on a 9.2 GB card in the
   source) and launch only if it fits the GPU. Check: light list before and after conversion, memory
   estimate under card memory, 10 consecutive PNGs compared for flicker.

## P9. Anima round trip prep

```python
# channel: batch | bridge | handoff
# checked against ZHCVMQeWPEg 00:04:06 and 00:06:36; layer API [verify]
result = anima_layer_prep(keep_layers=ARGS["keep_layers"], fps=30)
```

Then GUI: Anima menu > Import project, send only architecture and ground, draw paths in Anima,
Synchronize, Apply materials. Check after each sync: actor feet on ground (compare helper children Z
to ground), speeds varied, actors far from camera, fps unchanged.

## P10. Revision round

1. Save the approved state as a new numbered file before touching anything (`saveMaxFile` with
   `_v###`, scene skill naming).
2. Apply the change list; one change per item, logged.
3. Render every affected camera at review size with `capture.render`; build a before and after sheet
   with `max_review.compare` and `contact_sheet`.
4. Variants (materials, season, palette, furniture swap): one scene state or file per variant, same
   cameras, same size. Image-only variants for a fast pick: scenario-3dsmax-generation. Check:
   `stats.diff` shows only the intended nodes changed; the sheet shows only the requested change.

## P11. Delivery

1. Render elements per scenario-3dsmax-lighting-rendering: Cryptomatte, wire color for glass masks,
   Z-depth, light mix or light select.
2. Final noise target and size; output names `<project>_<view>_v###`.
3. Batch views: set each view's camera in the Batch Render dialog. `batchRenderMgr` is named on the
   2027.3 MCP limits page, which states that reading a view's camera through it crashes 3ds Max; its
   write properties are not in the saved docs [verify]. Verify by the rendered files.
4. Asset tracking zero missing and units consistent, so no modal dialog stops a scripted render.
5. Farm hand-off (ZHCVMQeWPEg 00:10:36): archive through scenario-3dsmax-scene with zero missing
   assets; the farm's 3ds Max version must be equal to or newer than the scene's (the source's "2024
   or earlier" was for a 2024 scene). Check: every file opened at 100%, sizes and names match the
   delivery sheet, one contact sheet of all finals.
