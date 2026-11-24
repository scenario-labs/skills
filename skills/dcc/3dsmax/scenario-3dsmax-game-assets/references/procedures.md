# Procedures: game assets in 3ds Max 2027.3

Every block here is **not yet run in 3ds Max**. Each names its channels and the source it was
checked against. Names not found in the saved docs carry `[verify]` on their line. Units:
centimeters unless a block says otherwise.

Common pattern (runner side): read the domain helper, prepend it to your chunk, wrap it with the
lead's `max_wrap.wrap`, run it with `max_batch.run_batch` or hand it to the bridge or the user, then
read the result JSON. If your `max_wrap` accepts domain modules in `kit=`, pass `"maxkit_game"`
there instead of prepending.

## Contents

1. Run a domain chunk through the toolkit
2. Audit an asset (read-only)
3. Discover modifier class and property names
4. Intake: imported, scanned or generated mesh to identity transform and real size
5. Cleanup pass in the expert's order
6. Dense mesh (scan, CAD, generated) to an engine mesh
7. Mid-poly finish: chamfer, one smoothing group, Weighted Normals
8. LOD chain
9. Collision hulls and sockets
10. Modular kit piece check
11. Vertex color masks by script
12. FBX export to Unreal or Unity
13. glTF or GLB export for a web viewer
14. Datasmith preparation
15. Engine-side checks (no code in 3ds Max)

---

## 1. Run a domain chunk through the toolkit

```python
# channel: runner side (any OS); produces scripts for batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scenario-3dsmax-expert/scripts/max_wrap.py (wrap signature)
import sys
from pathlib import Path

def build(chunk: str, skill_dir: Path, lead_scripts: Path, result_path: str, kit=("stats", "capture")) -> str:
    """Prepend maxkit_game to the chunk and wrap it in one undo record and the result protocol."""
    sys.path.insert(0, str(lead_scripts))
    from max_wrap import wrap
    helper = (skill_dir / "scripts" / "maxkit_game.py").read_text(encoding="utf-8")
    return wrap(helper + "\n\n" + chunk, lang="python", kit=list(kit), result_path=result_path,
                label="game-assets")
```

Check in the result: `ok` is true, `error` is null, `log` holds no "missing" entries you did not
expect.

## 2. Audit an asset (read-only)

MAXScript form, for every channel including `mcp-safe`: pass the file text of
`scripts/mxs/game_audit.ms` as the chunk to `wrap(code, lang="maxscript", undo=False)`, or have the
user run it. It changes nothing and writes no file; `result` is a JSON string.

Python form (batch, bridge, handoff), chunk for procedure 1:

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripts/mxs/game_audit.ms and scripting-pipeline__pymxs-using-2027.md
rep = game_audit()                      # maxkit_game.game_audit(): selection, or all objects if none selected
rep["snapshot"] = stats.snapshot()  # lead toolkit
result = rep
```

Runner side, after the result file arrives:

```python
# channel: runner side (any OS)
# status: runs offline; checked by archive tests on synthetic data, not on a real 3ds Max audit
import json
import subprocess
import sys

def gate(result_json: str, skill_scripts: str, target: str = "unreal", budgets=("LOD0=8000",)) -> list:
    cmd = [sys.executable, f"{skill_scripts}/game_rules.py", "report", result_json, "--target", target,
           "--budget", *budgets]
    out = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(out.stdout)
```

Check: no `error` findings before export. Warnings need a decision written down (for example, open
edges on a ground-hugging prop that is never seen from below).

## 3. Discover modifier class and property names

ProOptimizer, Retopology, Weighted Normals, Turn to Poly, Mesh Cleaner and Subdivide have no
property names in the saved docs. Never guess them: list them first. `getPropNames` is in the saved
pymxs doc.

```maxscript
-- channel: mcp-safe | bridge | batch | handoff
-- status: not yet run in 3ds Max; checked against scripting-pipeline__pymxs-using-2027.md (getPropNames)
-- Adds each candidate modifier to a temporary box, lists its properties, then deletes the box (a scene node, not a file).
local out = #()
local b = Box()
for cname in #("ProOptimizer", "Retopology", "Weighted_Normals", "WeightedNormals", "Turn_to_Poly", "Mesh_Cleaner", "Subdivide", "SmartBevelModifier", "Chamfer", "OpenSubdiv", "VertexPaint") do (
    local cls = execute cname                                      -- [verify] execute resolves a class name
    if cls != undefined do (
        try (
            local m = cls()
            addModifier b m
            append out (cname + ": " + ((getPropNames m) as string))
        ) catch (append out (cname + ": not creatable"))
    )
)
delete b
result = out
```

Check: record the exact names in your notes for the session; use them in later chunks through
`maxkit_game.set_props`, which reports any candidate that is missing.

## 4. Intake: imported, scanned or generated mesh to identity transform and real size

Before import (runner side), read a GLB without 3ds Max: its size in meters and its up axis tell you
the scale factor to expect. glTF is Y up and in meters by spec.

```python
# channel: runner side (any OS)
# status: runs offline; checked by archive tests on a synthetic GLB
import json
import sys
sys.path.insert(0, "SKILL_SCRIPTS_DIR")  # replace with the skill's scripts folder
from game_rules import glb_summary

info = glb_summary("path/to/asset.glb")
print(json.dumps(info, indent=1))
# size_m_xyz near [1.2, 0.8, 0.8] for a 120 cm crate means real scale already; [1, 1, 1] means normalized output
```

Inside 3ds Max (chunk for procedure 1). Import with the lead's `xio.import_any`, then normalize.
`target_cm` is the real size the user or the brief gives; never invent it.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against notes/game-assets digests (Ghost Pig z1ws_LOo9AU, MZONE3D 3PuxYRayJGE) and maxkit_game.py
import os
SRC = r"<path to the GLB or FBX>"
TARGET_CM = 120.0           # real size along MEASURE, from the brief
MEASURE = "longest"         # "longest", "height" or "width"
UP_FIX = None               # "y_up_to_z_up" only if the capture shows the model lying down
arrived = xio.import_any(SRC)
log("arrived:", arrived)
names = arrived.get("nodes", []) if isinstance(arrived, dict) else list(arrived)  # xio contract: what arrived
nodes = [rt.getNodeByName(str(n)) for n in names]
geo = [n for n in nodes if n is not None and rt.superClassOf(n) == rt.GeometryClass]  # [verify]
reports = []
for n in geo:
    reports.append(normalize_intake(n, target_cm=TARGET_CM if len(geo) == 1 else None,
                                    measure=MEASURE, pivot="bottom_center", up_fix=UP_FIX))
capture.views(os.path.join(os.path.dirname(SRC), "intake_views"))
result = {"arrived": arrived, "normalized": reports, "audit": game_audit()}
```

Check: `after.pos` is [0,0,0]; `after.min` z is 0 for a bottom-center pivot; the size along the
measured axis is within 1 percent of `TARGET_CM`. Look at the four captures: the model stands
upright, front faces +Y or the direction the team agreed. Multi-part imports keep their relative
scale: scale the group once (attach or link to a parent), not each part.

## 5. Cleanup pass in the expert's order

MZONE3D's order (3PuxYRayJGE): weld, isolated vertices, flipped normals, loose edges, duplicate
elements, Turn to Poly limit 4, Reset XForm, unhide all. This block works on one collapsed Editable
Poly.

```maxscript
-- channel: mcp-safe | bridge | batch | handoff
-- status: not yet run in 3ds Max; checked against notes/game-assets/3PuxYRayJGE (order and 0.001 weld); function names not in saved docs
-- Changes the mesh: run on a copy or inside the wrapper's undo record.
local n = selection[1]
local rep = #()
if n == undefined then rep = #("select one object") else (
    convertToPoly n                                                  -- [verify]
    local v0 = polyop.getNumVerts n                                  -- [verify]
    polyop.unHideAllFaces n                                          -- [verify]
    polyop.weldVertsByThreshold n #{1..v0}                           -- [verify] uses the object's weld threshold
    local v1 = polyop.getNumVerts n
    polyop.deleteIsoVerts n                                          -- [verify]
    local v2 = polyop.getNumVerts n
    ResetXForm n                                                     -- [verify]
    collapseStack n                                                  -- [verify]
    rep = #("verts before " + v0 as string, "after weld " + v1 as string, "after iso " + v2 as string)
)
result = rep
```

Set the weld threshold to 0.001 first: Editable Poly > Edit Vertices > Weld settings (GUI) or the
object's weld threshold property found by procedure 3. Flipped normals and duplicate elements need a
capture: look for black patches and for flicker under a moving camera. A Normal modifier with Flip
Normals, then collapse, fixes a flipped element. If nothing helps, export the object as OBJ and
import it back, or attach it to a fresh box (3PuxYRayJGE 00:09:32 to 00:12:16).

Then Turn to Poly with Limit Polygon Size on, Max Size 4, Remove Mid-Edge Vertices on (frame
00:07:25), and Reset XForm (GUI paths in [gui-paths.md](gui-paths.md)).

Symmetric pieces: the Symmetry modifier shows a default Threshold of 0.1 cm (tP7FD4l-qus frame
00:10:29); ChamferZone advises 0.01 and a re-check of every vertex on the mirror plane (01:05:28).
The modifier's threshold property name is not in the saved docs: read it with procedure 3, or set it
in the GUI. Audit: every vertex within 0.001 of the plane must sit at exactly 0.

Check: `iso_verts` 0 and `open_edges` unchanged or lower in a new audit; vertex count drops only by
welded duplicates (MZONE3D's rifle: 5,916 to 5,794 vertices).

## 6. Dense mesh (scan, CAD, generated) to an engine mesh

Stack order shown by Eloi Andaluz Fullà (Pg2Nm-fwyME): ProOptimizer, then Retopology (ReForm), then
Weighted Normals. Triangulated CAD first gets Subdivide (even density) and Mesh Cleaner. Keep the
dense original hidden as the bake source.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against notes/game-assets/Pg2Nm-fwyME and HhUMdy-0kSI (values from frames); class and property names [verify], probed at run time
SRC_NAME = "<dense mesh node name>"
FACES = 6000                       # target from the budget; HhUMdy-0kSI uses 6000, small parts 150
src = rt.getNodeByName(SRC_NAME)
hi = rt.copy(src)
hi.name = SRC_NAME + "_high"
hi.isHidden = True                 # [verify] node.isHidden
lo = src
steps = []
for cls_names, wanted in (
    (("ProOptimizer",), {("KeepUV", "KeepUVBoundaries"): True, ("VertexPercent",): 30.0, ("Calculate",): True}),   # [verify]
    (("Retopology",), {("FaceCount", "TargetFaceCount"): FACES, ("Regularize",): 1.0, ("Adaptivity",): 0.0}),     # [verify]
    (("Weighted_Normals", "WeightedNormals"), {}),                                                                  # [verify]
):
    cls = _find_class(*cls_names)
    if cls is None:
        steps.append({"modifier": cls_names[0], "error": "class not found; see procedure 3"})
        continue
    mod = cls()
    rt.addModifier(lo, mod)
    steps.append({"modifier": cls_names[0], "props": set_props(mod, wanted)})
tris = int(rt.getNumFaces(rt.snapshotAsMesh(lo)))  # [verify]
result = {"steps": steps, "tris": tris, "high": str(hi.name)}
```

The Retopology modifier computes on a button press in the GUI; a scripted compute method is not
documented. If `tris` still equals the input count, press Compute (Modify panel) or ask the user to.
Then hand `lo` and `<name>_high` to scenario-3dsmax-uv-baking for UVs and a tangent normal bake
(Pg2Nm-fwyME: 2048 px, MikkT, frames 00:11:58 to 00:12:28).

On Boolean results, Martin Coven's full stack is Slice, Subdivide (Adaptive, edge length 2),
Retopology (Face Count 6000, Regularize 1, Adaptivity 0), Symmetry, Smooth (Auto Smooth 35), Chamfer
(From Smoothing: Unsmoothed Edges, Radial mitering), OpenSubdiv 2 (HhUMdy-0kSI 00:01:10 to
00:04:44). A part that shades badly gets its Retopology made unique with its own face count (150 on
screen, 00:04:44).

Normal bake settings for the hand-off: Bake to Texture (the 2027 tool; legacy Render To Texture is
superseded, deltas), Projection modifier on the low mesh picking the high, tangent space MikkT. Test
at 256 or 512 px with padding 64 first (SKXrtpTIsNI frames 00:26:57, 00:27:49), then the final size.
jjbigley's Marmoset bake with MikkT was cleaner than the old 3ds Max default (SKXrtpTIsNI 00:44:58).
The bake itself belongs to scenario-3dsmax-uv-baking.

For props where retopology loses too much detail, a plain reduction that keeps UVs and the texture
is the expert's choice (Top 3D AI, O6G6taj5M14 00:12:24): ProOptimizer alone with Keep Textures and
Keep UV Boundaries.

Check: `tris` within 10 percent of the target; wireframe capture shows even quads that follow the
form; no holes at thin parts (Instant Mesh left holes in Pg2Nm-fwyME frame 00:02:23, ReForm did
not).

## 7. Mid-poly finish: chamfer, one smoothing group, Weighted Normals

Next Level Game Art's recipe (cGQJBU2RYPA): chamfer every hard edge with 0 segments, clear smoothing
groups to 1, add Weighted Normals with no setting changes. After a Boolean in 2027, use Smart Bevel
above the Boolean instead of Chamfer (lDpcfhxP3qU).

Segments: the 0-segment value comes from the Chamfer recipe. The only Smart Bevel values in the
sources are Autodesk's on-screen start values: Width 2.38 (world units), Segments 1, Depth 0.5,
Selected Edges plus Use Unsmoothed Edges, Output Smooth Bevel Only, Smooth to Adjacent, Threshold 30
(lDpcfhxP3qU frame 00:02:12). Whether Smart Bevel at 0 segments gives the same mid-poly result is
not in the sources: test it on a box and compare glossy captures before relying on it.

Weighted Normals on the Autodesk 2027 stack: Area plus Angle, Use Convex Corner Angle on, Blending
1.0, Iterations 10 (lDpcfhxP3qU frame 00:03:00). Hard Edge Detection (Use Smoothing Groups, Use UV
Map, By Edge Angle) keeps deliberate hard edges, for example the ones on UV seams of a baked part
(WN doc).

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against game-assets__autodesk-weighted-normals-modifier.md (parameters) and notes cGQJBU2RYPA, lDpcfhxP3qU; names [verify]
NAME = "<prop node name>"
CHAMFER_CM = 0.5                        # [added] start value for a 100 cm prop; judge in the capture
n = rt.getNodeByName(NAME)
after_boolean = any("boolean" in str(rt.classOf(m)).lower() for m in n.modifiers)   # [verify] node.modifiers
if after_boolean:
    bev = _find_class("SmartBevelModifier")      # class name documented in maxscript-whats-new-2027
    mod = bev()
    rt.addModifier(n, mod)
    bevel = set_props(mod, {("Width",): CHAMFER_CM, ("Segments",): 1, ("Depth",): 0.5})   # [verify] property names; values from lDpcfhxP3qU frame 00:02:12
else:
    mod = _find_class("Chamfer")()               # [verify] Chamfer modifier class
    rt.addModifier(n, mod)
    bevel = set_props(mod, {("Amount",): CHAMFER_CM, ("Segments",): 0})  # [verify]
    for m in n.modifiers:                                                   # [verify] node.modifiers
        if "chamfer" in str(rt.classOf(m)).lower():
            m.SetVersion(rt.Name("VerLatest"))  # doc: upgrades Chamfers from before 2023.2; pymxs call form [verify]
sg = _find_class("Smooth")()                     # [verify] Smooth modifier: all faces in one group
rt.addModifier(n, sg)
sg_rep = set_props(sg, {("AutoSmooth",): False, ("SmoothingBits",): 1})   # [verify]
wn = _find_class("Weighted_Normals", "WeightedNormals")()                  # [verify]
rt.addModifier(n, wn)
wn_rep = set_props(wn, {("Blending",): 1.0, ("Iterations",): 10})          # [verify] property names
result = {"bevel": bevel, "smooth": sg_rep, "weighted": wn_rep,
          "tris": int(rt.getNumFaces(rt.snapshotAsMesh(n)))}               # [verify]
capture.views("<output folder>/midpoly")
```

Edge choice is a modifier parameter, not a GUI-only step. The Chamfer modifier's Filter By group has
From Smoothing (Off, Smoothed Edges, Unsmoothed Edges), From Material ID, and Min. Angle and Max.
Angle (Chamfer doc). Smart Bevel has Selected Edges and Use Unsmoothed Edges. Their script property
names are not in the saved docs: list them with procedure 3, then pass them to `set_props`. If
`bevel.missing` is not empty, open the modifier in the GUI ([gui-paths.md](gui-paths.md)).

Chamfer traps (Chamfer doc): a Chamfer applied before 3ds Max 2023.2 keeps the old Limit Effect
until `$.modifiers[N].SetVersion #VerLatest` upgrades it (no self-intersections after). With Tri
mitering, Limit Effect is always on and stays on after you switch to another mitering: turn it off
explicitly. Bevels make long thin triangles that cost render time (Polycount wiki): remove edges on
flat faces (tP7FD4l-qus 01:23:46) and check the triangulation by hand before export (Epic doc).

Check: a box goes from 12 to about 26 tris; in a glossy capture, flats show one clean highlight and
bevels a soft roll. Compare with the same mesh without Weighted Normals (disable the modifier,
capture again).

## 8. LOD chain

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against notes s_RShJy4k-g (50 and 67 percent, Keep Textures and Keep UV Boundaries) and maxkit_game.make_lod
LOD0 = rt.getNodeByName("<LOD0 node name>")
PLAN = [(1, 55.0), (2, 30.0), (3, 15.0)]   # vertex percent of LOD0, tuned until each step is about 50 percent of the previous
reports = [make_lod(LOD0, level, pct) for level, pct in PLAN]
for i, r in enumerate(reports):
    node = rt.getNodeByName(r["lod"])
    if node is not None:
        node.pos = rt.Point3(LOD0.pos.x + 200.0 * (i + 1), LOD0.pos.y, LOD0.pos.z)  # side by side for the capture only
result = {"lod0_tris": int(rt.getNumFaces(rt.snapshotAsMesh(LOD0))), "lods": reports}   # [verify]
capture.views("<output folder>/lods", views=("front",))
```

ProOptimizer's "77 percent" (Crytek 00:05:44) is the Vertex % spinner value kept on one demo LOD,
where artifacts began. It is not a general floor and not a ratio between LODs; the ratio rule is 50
percent, warning above 67.

Before export, move the LODs back to the origin (same pivot and space as LOD0, Epic doc). Delete
parts that vanish at distance before reducing (Crytek removes floor planks at LOD4). Unreal imports
LODs from the FBX (Import LODs on) or one file per LOD in the Static Mesh Editor (Epic doc). How 3ds
Max writes several LODs into one FBX is not in the saved sources: default to one FBX per LOD named
`<mesh>_LOD1.fbx`, each imported through the Static Mesh Editor LOD picker. To test the one-file
route, export a two-LOD test and check the LOD picker after import. Re-apply Weighted Normals on
each LOD, with the same origin and pivot as LOD0. Unity reads `_LOD0`, `_LOD1` name suffixes into a
LOD Group [added].

Check: `game_rules` `lod.ratio` and `lod.gap` clean; the front capture shows matching silhouettes;
ProOptimizer flags `missing` list empty (else the UVs may be broken).

## 9. Collision hulls and sockets

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against game-assets__unreal-fbx-static-mesh-pipeline.md (UCX_, SOCKET_, convex, gaps) and maxkit_game.add_box_collision
BODY = rt.getNodeByName("SM_Crate_A")
hull = add_box_collision(BODY, index=0)
sock = rt.Dummy()                                # [verify] Dummy helper class
sock.name = "SOCKET_SM_Crate_A_00"
sock.pos = rt.Point3(0, 0, BODY.max.z)           # top center, for attaching a lid or pickup
result = {"hull": hull, "socket": str(sock.name), "audit": game_audit()}
```

Moving parts. Unreal imports only the first mesh's custom collision when several meshes with custom
collision share one FBX, and an FBX with sockets holds one render mesh (Epic doc). So a hinged lid,
a door or a drawer is its own render mesh (`SM_Crate_A_Lid`) in its own FBX with its own
`UCX_SM_Crate_A_Lid_00` and sockets. Put its pivot on the hinge line and that line at the origin
before export, since FBX exports the pivot at the origin [added]. The body file keeps a socket where
the lid attaches.

For concave shapes (a crate with an open lid, a doorway), build several convex boxes or hand-made
convex pieces and leave a gap between them. Collision primitives UBX and USP fail on non-uniformly
scaled meshes; UCX works (Epic doc). Datasmith takes custom collision through a Datasmith Attributes
Modifier instead of names (Epic Datasmith doc).

Check: the audit shows `convex_violations` 0 and `open_edges` 0 on every `UCX_` node; `game_rules`
reports no `collision.*` or `socket.*` error.

## 10. Modular kit piece check

CtrlAultDel's kit (J1lnlTbMtKs): 256 unit cells, 240 pieces, pivot on a grid corner, every vertex on
the grid step.

```python
# channel: batch | bridge | handoff (read-only)
# status: not yet run in 3ds Max; checked against notes/game-assets/J1lnlTbMtKs (cell 256, step 8, pivot -128,-128)
GRID = 8.0
CELL = 256.0
TOL = 0.001
out = []
for n in rt.selection:
    m = rt.snapshotAsMesh(n)                                       # [verify]
    off = 0
    for i in range(1, int(rt.getNumVerts(m)) + 1):                 # [verify]
        v = rt.getVert(m, i)                                       # [verify]
        for c in (v.x, v.y):
            if abs(c / GRID - round(c / GRID)) * GRID > TOL:
                off += 1
                break
    piv = n.pivot                                                  # [verify]
    on_cell = all(abs(c / CELL - round(c / CELL)) * CELL <= TOL for c in (piv.x, piv.y))
    out.append({"name": str(n.name), "verts_off_grid_xy": off, "pivot_on_cell_corner": on_cell})
result = out
```

Name pieces by wall and door count plus a description (`wall2_door0_hallway`, J1lnlTbMtKs 00:13:36).
Share one UV region across wall variants so one texture swap re-themes the kit (00:36:38).

Check: `verts_off_grid_xy` 0 on walls and floors (trim and detail pieces may be exempt); every pivot
on a cell corner; two pieces placed side by side show no flicker in a capture.

## 11. Vertex color masks by script

Painting with a brush is GUI work (VertexPaint modifier, Painter Interface). A scripted mask, for
example a height gradient for dirt or moss blending:

```maxscript
-- channel: mcp-safe | bridge | batch | handoff
-- status: not yet run in 3ds Max; checked against notes/game-assets/aQIQH0hZkDg (channels: Vertex Color, Illum, Alpha); polyop names [verify]
-- Writes a bottom-to-top gradient into map channel 0 (vertex color) on one Editable Poly.
local n = selection[1]
convertToPoly n                                                     -- [verify]
polyop.setMapSupport n 0 true                                       -- [verify]
local zmin = n.min.z
local h = n.max.z - zmin
local nv = polyop.getNumVerts n                                     -- [verify]
for i = 1 to nv do (
    local t = if h > 0 then ((polyop.getVert n i).z - zmin) / h else 0.0   -- [verify]
    local g = 255 * (1.0 - t)
    polyop.setVertColor n 0 #{i} (color g g g)                      -- [verify] channel 0; -2 is alpha
)
result = #(n.name, nv)
```

Check: the audit lists channel `0` in `map_channels`; a viewport capture with vertex color display
shows the gradient. glTF export from 3ds Max drops vertex colors (gltf-export-2027 known
limitations): ship vertex-color assets by FBX.

## 12. FBX export to Unreal or Unity

Work file stays untouched: `export_fbx_game` exports triangulated copies with the exact node names,
then deletes the copies.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against game-assets__unreal-fbx-static-mesh-pipeline.md, notes CM3GwvoOSP4 and z1ws_LOo9AU, maxscript-file-loading-saving-importfile-exportfile-2027.md (exportFile flags)
OUT = r"<export folder>\SM_Crate_A.fbx"
names = ["SM_Crate_A", "UCX_SM_Crate_A_00", "SOCKET_SM_Crate_A_00"]
nodes = [rt.getNodeByName(x) for x in names]
missing = [x for x, n in zip(names, nodes) if n is None]
if missing:
    raise RuntimeError(f"nodes not found: {missing}")
pre = game_audit()
rep = export_fbx_game(OUT, nodes, target="unreal")      # or target="unity"
result = {"pre_audit": pre, "export": rep}
```

Runner side, on the written file:

```python
# channel: runner side (any OS)
# status: runs offline; header layout [added], checked by archive tests on a synthetic header
import sys
sys.path.insert(0, "SKILL_SCRIPTS_DIR")  # replace with the skill's scripts folder
from game_rules import fbx_header

h = fbx_header(r"<export folder>\SM_Crate_A.fbx")
assert h["kind"] == "binary" and h["version"] == 7700, h   # 7700 = FBX 2019/2020 file family
```

`mcp-safe` form (MAXScript). Whether `exportFile` passes Safe Scene Script Execution is not
documented: propose it, and fall back to `handoff` if it is blocked.

```maxscript
-- channel: mcp-safe | bridge | batch | handoff
-- status: not yet run in 3ds Max; checked against maxscript-file-loading-saving-importfile-exportfile-2027.md (exportFile, #noPrompt, selectedOnly, using:) and maxscript-whats-new-2027.md (FBXExporterGetParam)
-- Exports the current selection as is: triangulate and Reset XForm on the export copy beforehand.
local outPath = @"<export folder>\SM_Crate_A_v002.fbx"
FBXExporterSetParam "ResetExport"                     -- [verify]
FBXExporterSetParam "SmoothingGroups" true            -- [verify]
FBXExporterSetParam "Triangulate" true                -- [verify]
FBXExporterSetParam "PreserveEdgeOrientation" true    -- [verify]
FBXExporterSetParam "SmoothMeshExport" false          -- [verify]
FBXExporterSetParam "Animation" false                 -- [verify]
FBXExporterSetParam "UpAxis" "Z"                      -- [verify]
FBXExporterSetParam "ConvertUnit" "cm"                -- [verify]
FBXExporterSetParam "FileVersion" "FBX202000"         -- [verify]
local back = for k in #("SmoothingGroups", "Triangulate", "UpAxis", "FileVersion") collect (k + "=" + ((FBXExporterGetParam k) as string))
local ok = exportFile outPath #noPrompt selectedOnly:true using:FBXEXP
result = #(ok, back)
```

Read the exporter's Warnings dialog (CM3GwvoOSP4 frame 00:02:08). A "Turned Edges" warning means
Editable Poly edges were turned: Preserve edge orientation converts the affected Editable Poly to
Editable Mesh and triangulates it (CM3GwvoOSP4 00:01:45 to 00:02:21). Export a copy, so the work
object stays Editable Poly.

Check: `params.mismatch` empty; `exists` true and `bytes` above zero; header version 7700; for
Unity, remind the user of Bake Axis Conversion (or pre-rotate the pivot X 90 when the importer lacks
it, z1ws_LOo9AU 00:05:24).

## 13. glTF or GLB export for a web viewer

The 2027.3 Khronos exporter chooses its plug-in by file suffix; its options (glb, Apply scale with
system unit, Draco, Metal/Rough/Occ map building) have no documented script interface. Set them once
in File > Export, then export by script.

```maxscript
-- channel: mcp-safe | bridge | batch | handoff
-- status: not yet run in 3ds Max; checked against scripting-pipeline__gltf-export-2027.md and maxscript-file-loading-saving-importfile-exportfile-2027.md
-- Select LOD0 render meshes only: no UCX_, no SOCKET_, no LODs.
local outPath = @"<export folder>\Crate_A_v002.glb"
local ok = exportFile outPath #noPrompt selectedOnly:true
result = ok
```

Runner side: `python game_rules.py glb <file>` must give `size_m_xyz` equal to the real size in
meters (1.2 for a 120 cm crate) and `height_axis_guess` "Y". The exporter flattens hierarchies,
drops vertex colors and reads only Bitmap Texture maps into the glTF Material (doc known
limitations). Duplicate node or material names get `_1`, `_2` suffixes.

## 14. Datasmith preparation

Export is a ribbon action (Datasmith tab); no export call is in the saved sources. Prepare the scene
by script, export in the GUI or ask the user.

```maxscript
-- channel: mcp-safe | bridge | batch | handoff
-- status: not yet run in 3ds Max; checked against game-assets__datasmith-3dsmax-translation.md (metadata format, StatSync, UV and pivot rules)
Datasmith_SetExportOption_StatSync true                 -- documented: statistics for Direct Link Sync
local rep = #()
for n in selection do (
    setUserProp n "AssetType" "Prop"                    -- [verify] writes "AssetType = Prop"; Datasmith needs spaces around =
    local s = n.scale
    if (s.x != s.y or s.y != s.z) do append rep (n.name + ": non-uniform scale, Reset XForm before export")
)
result = rep
```

Datasmith does not import instances that have both different pivots and non-uniform scale: run Reset
XForm on them before export (Datasmith doc). Custom lightmap UVs: set the channel index with a
Datasmith Attributes Modifier before export, or change it in the Static Mesh Editor after import
(Datasmith doc). Datasmith keeps 6 UV channels, adds 2 for lightmaps, replaces instances with one
mesh and many placements, drops 3ds Max LODs, and bakes procedural maps to TGA. Split heavy scenes
into layers and export each with Export Selected (Unreal ArchWizard, qsV4k09kPV8 00:08:10). On
re-import, untick everything but geometry (00:09:17).

Check: the Unreal Output Log after import; Show > Collision for custom collision.

## 15. Engine-side checks (no code in 3ds Max)

Ask the user, or an engine-side agent, for these numbers and screenshots after import:

- Unreal Static Mesh Editor: Approx Size equals the real size in cm; LOD picker cycles every LOD;
  Show > Collision draws the UCX hulls; the material shows Color and Normal connected (others need
  wiring).
- Unreal import dialog: Import LODs on when LODs ride in the FBX; Auto Generate Collision off when
  UCX meshes exist; Normal Import Method set to import normals so weighted normals survive [added].
- Unity: Model tab Convert Units shows "1cm (File) to 0.01m (Unity)"; Bake Axis Conversion ticked;
  dragged into the Hierarchy, Transform reads position 0, rotation 0, scale 1 (z1ws_LOo9AU).
- Web viewer: the Khronos glTF Validator reports zero errors [added]; size on the grid matches.
