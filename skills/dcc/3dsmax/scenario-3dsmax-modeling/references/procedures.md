# Modeling procedures (full code)

Every block is a chunk for `max_wrap.wrap(code, lang=..., kit=[...], result_path=...)` from
scenario-3dsmax-expert: the chunk sets `result`, the wrapper adds one undo record and the result
protocol. Python chunks use the helper module `scripts/maxkit_modeling.py` (pass its path in `kit`;
on a bridge without the wrapper, add the skill's `scripts` folder to `sys.path`). The MAXScript twin
`scripts/mxs/maxkit_modeling.ms` serves `mcp-safe`.

Units: every number assumes centimeters as the system unit unless the block says otherwise. Read the
scene's units first (scenario-3dsmax-scene owns units) and scale the numbers.

Naming rule for this file: a name followed by `[verify]` was not found in the saved Autodesk docs.
P1 exists to replace those guesses with the real names from the running 3ds Max before anything else
runs.

## P1. Probe class, property and interface names

Run this first in any new session, for every modifier class a later procedure uses. It costs one
round trip and turns `[verify]` guesses into facts for this build.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-using-2027.md (getPropNames), api-names.txt
import pymxs
rt = pymxs.runtime

CANDIDATES = {
    "boolean": ("BooleanMod", "Boolean_Modifier", "Boolean"),  # [verify] macro recorder showed BooleanMod (TEz7tBiRrXc 00:00:25)
    "smartbevel": ("SmartBevelModifier",),  # documented in MAXScript 2027.3
    "chamfer": ("Chamfer",),  # [verify]
    "opensubdiv": ("OpenSubdiv",),  # [verify]
    "turbosmooth": ("TurboSmooth",),  # [verify]
    "crease": ("Crease",),  # [verify]
    "creaseset": ("CreaseSet", "Crease_Set"),  # [verify]
    "retopology": ("Retopology",),  # [verify]
    "subdivide": ("Subdivide",),  # [verify]
    "conform": ("Conform", "ConformModifier"),  # [verify]
    "symmetry": ("Symmetry",),  # [verify]
    "slice": ("SliceModifier", "Slice"),  # [verify]
    "poly_select": ("Poly_Select",),  # [verify]
    "array": ("Array", "ArrayModifier"),  # [verify] outputType property is documented (2027.2)
    "displace": ("Displace",),  # [verify]
    "shell": ("Shell",),  # [verify]
    "ffd": ("FFD_4x4x4", "FFDBox"),  # [verify]
    "spline_chamfer": ("Spline_Chamfer", "SplineChamfer"),  # [verify] UseRadius, AutoWeld are documented (2027)
    "sweep": ("Sweep",),  # [verify]
    "noise_plus": ("NoisePlusModifier",),  # documented in MAXScript 2027
    "weighted_normals": ("Weighted_Normals", "WeightedNormals"),  # [verify]
}

found = {}
for key, names in CANDIDATES.items():
    entry = {"class": None, "props": [], "interfaces": ""}
    for n in names:
        try:
            cls = getattr(rt, n)
        except AttributeError:
            cls = None
        if cls is None:
            continue
        try:
            inst = cls()
        except Exception as exc:
            entry["class"] = n + " (not creatable: %s)" % exc
            break
        entry["class"] = n
        entry["props"] = [str(p) for p in list(rt.getPropNames(inst))]
        try:
            ss = rt.StringStream("")  # [verify]
            rt.showInterfaces(inst, to=ss)  # [verify] to: keyword
            entry["interfaces"] = str(ss)[:4000]
        except Exception as exc:
            entry["interfaces"] = "showInterfaces failed: %s" % exc
        break
    found[key] = entry

result = found
```

Check in the result:

- `class` is not None for each family you need; a None means the name list is wrong for this build,
  so search with `apropos` in the Listener (GUI) or ask the user to add the modifier once with the
  macro recorder on (P1b).
- Copy the property names you need into the `NAMES` dictionaries of P2 to P8. Enum values (Boolean
  method, Chamfer selection mode) are integers whose meaning the property list does not show: set
  one in the GUI, read it back with P1c.

P1b, names from the macro recorder (handoff, GUI): ask the user to open Scripting > MAXScript
Listener, check that the macro recorder is on (2027 adds the read-only `macroRecorderEnabled` and
the settable `macroRecorderEmitterEnabled`), do the step once by hand (add the operand, pick the
Chamfer selection mode), and paste back the Listener lines. TEz7tBiRrXc shows such lines at 00:00:25
(`modPanel.addModToSelection (BooleanMod ...)`) and 00:03:25
(`$.modifiers[#Boolean].AppendOperand`).

P1c, read current values of one modifier (MAXScript, safe for `mcp-safe`):

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against api-names.txt (getPropNames, classOf)
(
	local node = selection[1]
	local out = #()
	for i = 1 to node.modifiers.count do
	(
		local m = node.modifiers[i]
		local pairs = for p in getPropNames m collect (p as string + "=" + ((getProperty m p) as string))
		append out ((i as string) + " " + ((classOf m) as string) + " " + m.name + " :: " + (pairs as string))
	)
	out
)
```

## P2. Hard-surface cut chain (Boolean, then Smart Bevel or Poly Select plus Chamfer)

Goal: a base with cutters subtracted, bevels on the intersection edges only, every step live.
Source: TEz7tBiRrXc 00:04:10 to 00:05:48 (chain), lDpcfhxP3qU 00:01:07 to 00:03:00 (Smart Bevel
above Boolean), fXI2MJ7Bw2k 00:02:57 (cutter segments), boolean doc (operand hygiene).

```python
# channel: batch | bridge | handoff
# checked against poly-modeling__boolean-modifier.md, poly-modeling__smart-bevel-2027.md,
#         TEz7tBiRrXc frames 00:04:35 and 00:06:50, lDpcfhxP3qU frame 00:02:12
import pymxs
rt = pymxs.runtime
try:
    mm = maxkit_modeling  # inlined by max_wrap
except NameError:
    import maxkit_modeling as mm

ARGS = {
    "base": "GEO_Body",                  # node name; must be closed, welded, unscaled
    "cutters": ["CUT_Vent_01", "CUT_Vent_02"],
    "bevel": "smart",                    # "smart" (2027+) or "chamfer"
    "widths": [0.3, 0.2, 0.2, 0.1],      # cm, one per cutter, descending with feature size (TEz7tBiRrXc)
    "segments": 1,
    "depth": 0.5,
    "subdivide_later": False,            # True: cutters keep 6 to 8 sides
}
NAMES = {  # fill from P1
    "boolean": ("BooleanMod", "Boolean"),                                    # [verify]
    "append_operand": "AppendOperand",                                       # [verify] arguments unknown
    "chamfer_amount": ("amount",),                                           # [verify]
    "chamfer_segments": ("segments",),                                       # [verify]
    "chamfer_selection": ("selectiontype", "selection"),                     # [verify]
    "chamfer_selection_selected_edges": 2,                                   # [verify] enum value
    "sb_width": ("width",),                                                  # [verify]
    "sb_segments": ("segments",),                                            # [verify]
    "sb_depth": ("depth",),                                                  # [verify]
}

base = rt.getNodeByName(ARGS["base"])
log = []
with pymxs.undo(True, "modeling: boolean chain"):
    for i, cname in enumerate(ARGS["cutters"]):
        cutter = rt.getNodeByName(cname)
        # cutter hygiene: one height segment; few sides only if the result is subdivided (fXI2MJ7Bw2k 00:03:30)
        log.append(mm.set_props(cutter.baseObject, {("heightsegs",): 1}))  # [verify] baseObject on primitives
        if ARGS["subdivide_later"]:
            log.append(mm.set_props(cutter.baseObject, {("sides",): 8}))  # [verify]
        b, rep = mm.add_mod(base, NAMES["boolean"])
        log.append(rep)
        if b is None:
            break
        appended = False
        for call in ((base, cutter), (base, cutter, False), (cutter,)):
            try:
                getattr(b, NAMES["append_operand"])(*call)
                appended = True
                break
            except Exception as exc:
                log.append("AppendOperand%r failed: %s" % (tuple(str(c) for c in call), exc))
        if not appended:
            log.append("operand not added: add it in the GUI (Operands rollout > Add Operands) or fix NAMES from P1b")
            break
        w = ARGS["widths"][min(i, len(ARGS["widths"]) - 1)]
        if ARGS["bevel"] == "smart":
            sb, rep = mm.add_mod(base, ("SmartBevelModifier",), {
                NAMES["sb_width"]: w, NAMES["sb_segments"]: ARGS["segments"], NAMES["sb_depth"]: ARGS["depth"]})
            log.append(rep)
        else:
            # the Boolean outputs its intersection edges as a selection; Poly Select passes it up (TEz7tBiRrXc 00:04:10)
            mm.add_mod(base, ("Poly_Select",))  # [verify]
            ch, rep = mm.add_mod(base, ("Chamfer",), {  # [verify]
                NAMES["chamfer_amount"]: w, NAMES["chamfer_segments"]: ARGS["segments"],
                NAMES["chamfer_selection"]: NAMES["chamfer_selection_selected_edges"]})
            log.append(rep)
            # Chamfer outputs its own edges: an empty Poly Select stops the next Chamfer re-beveling them
            mm.add_mod(base, ("Poly_Select",))  # [verify]

result = {"log": log, "stack": [(e["cls"], e["name"]) for e in mm.stack(base)], "audit": mm.stack_audit(base)}
```

Check in the result:

- Every `set_props` report has an empty `missing` list. A missing name means the guess was wrong:
  fix `NAMES` from P1 and rerun on a fresh copy (Edit > Undo first, or rebuild from the saved file).
- The stack reads, bottom to top, base, then Boolean, Smart Bevel per cutter (or Boolean, Poly
  Select, Chamfer, Poly Select). `stack_audit` returns no `selection-not-cleared`.
- Then run P9 (verify). Capture with Edged Faces: look for pinching at corners and uneven bevel
  width (lDpcfhxP3qU 00:00:42).
- Chamfer route: turn Limit Effect on, so a large Amount cannot push chamfered edges through each
  other. On a Chamfer from before 2023.2, run `$.modifiers[N].SetVersion #VerLatest`. Never pick the
  Legacy amount type on a new model (chamfer doc). The Limit Effect property name is not in the
  saved docs: find it with P1.
- Flat hard-surface kit that must keep clean loops: build the loops around the cut zone first and
  cut without edge removal (Arrimus, fXI2MJ7Bw2k 00:02:26), or turn on Imprint, which inserts
  intersection edges without removing faces (boolean doc).
- Hole integrity after any push-through or floater cut: `mesh_checks` must return `weldable_verts` 0
  and `open_edges` 0. Doubled edges show as 3 versus 7 edges around the ring and must be welded
  before OpenSubdiv (Todd D, yx-lpHy8yPs 00:04:55). The GUI test is a Ctrl-double-click on the
  polygon ring: a full circle means welded (00:04:23).
- Round openings (spout, aerator, ear cup): Loop Regularizer turns the face ring into a circle, then
  Set Flow fits the loops to the curvature (Igor Mota, 0jXxaGKuW6Y 00:03:30). Both are GUI only
  (Modeling ribbon); no script equivalent is documented.

GUI fallback for the operand step: Modify panel > Boolean > Operands rollout > Add Operands, pick
the cutter. Decide Capture or Live Reference before picking; it cannot be switched later
(TEz7tBiRrXc 00:03:43). Full path list in gui-paths.md.

P2 for `mcp-safe` (MAXScript, same chain, Smart Bevel route):

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against poly-modeling__smart-bevel-2027.md, MAXScript what's new 2027.3 (SmartBevelModifier)
(
	local base = getNodeByName "GEO_Body"
	local cutters = #("CUT_Vent_01", "CUT_Vent_02")
	local widths = #(0.3, 0.2)
	local log = #()
	undo "modeling: boolean chain" on
	(
		for i = 1 to cutters.count do
		(
			local c = getNodeByName cutters[i]
			local b = BooleanMod() -- [verify] class name
			addModifier base b
			try (b.AppendOperand base c) catch (append log ("AppendOperand failed: " + getCurrentException())) -- [verify] arguments
			local sb = SmartBevelModifier()
			addModifier base sb
			if isProperty sb #width then sb.width = widths[i] else append log "SmartBevel width name unknown" -- [verify] width
		)
	)
	log
)
```

## P3. Organic merge: OpenVDB Boolean, Retopology, Conform back

Goal: melt parts into one watertight form, rebuild even quads, recover edges. Source: uDfhmKCdR0U
00:11:30 to 00:18:13 (voxel scale, reset per Boolean, 8,197-face result), sRLKiz4HSgA 00:08:22 to
00:09:30 (VDB 0.2, Retopology 25,000, Conform Closest Point to the original), boolean doc (Voxel
Size, ESC aborts).

```python
# channel: bridge | handoff (batch if the Retopology compute call is found in P1)
# checked against poly-modeling__boolean-modifier.md, uDfhmKCdR0U, sRLKiz4HSgA notes
import pymxs
rt = pymxs.runtime
try:
    mm = maxkit_modeling
except NameError:
    import maxkit_modeling as mm

ARGS = {"base": "GEO_Swirl", "operands": ["GEO_Plug_01"], "original": "GEO_Swirl_SRC",
        "voxel": None, "face_target": 8000}
NAMES = {
    "boolean": ("BooleanMod", "Boolean"),           # [verify]
    "method": ("method",), "method_openvdb": 1,     # [verify] property and enum
    "voxel": ("voxelsize", "voxel_size"),           # [verify]
    "union": ("operation",), "union_value": 1,      # [verify] per-operand data is scriptable since 2027
    "retopo_faces": ("facecount", "targetfacecount"),  # [verify]
    "conform_target": ("target", "targetnode"),     # [verify]
}

base = rt.getNodeByName(ARGS["base"])
log = []
bb = rt.nodeGetBoundingBox(base, rt.matrix3(1))  # [verify]
side = max(float(bb[1][k] - bb[0][k]) for k in range(3))
voxel = ARGS["voxel"] or round(side / 100.0, 4)  # [added] start near 1/100 of the largest side
log.append(mm.voxel_ratio(base, voxel))
with pymxs.undo(True, "modeling: vdb merge"):
    for op in ARGS["operands"]:
        b, rep = mm.add_mod(base, NAMES["boolean"])
        # every new Boolean starts at Method Mesh and voxel 1.0: set both each time (uDfhmKCdR0U 00:12:38)
        rep2 = mm.set_props(b, {NAMES["method"]: NAMES["method_openvdb"], NAMES["voxel"]: voxel})
        log += [rep, rep2]
        try:
            b.AppendOperand(base, rt.getNodeByName(op))  # [verify]
        except Exception as exc:
            log.append("add operand in the GUI: %s" % exc)
    r, rep = mm.add_mod(base, ("Retopology",), {NAMES["retopo_faces"]: ARGS["face_target"]})  # [verify]
    log.append(rep)
    if ARGS["original"]:
        c, rep = mm.add_mod(base, ("Conform", "ConformModifier"),  # [verify]
                            {NAMES["conform_target"]: rt.getNodeByName(ARGS["original"])})
        log.append(rep)

result = {"voxel": voxel, "log": log, "audit": mm.stack_audit(base)}
```

Check in the result and the scene:

- `voxel_ratio.verdict` is `ok`. A very small voxel can freeze 3ds Max; the doc says ESC aborts and
  restores the last value. On `bridge`, never set a voxel under 1/500 of the largest side without
  telling the user first.
- Retopology computes only when its Compute button is pressed unless P1 found a compute method (none
  is documented in the saved docs). Ask the user to press Modify panel > Retopology > Compute, or
  call the method P1 listed. After any edit below a computed Retopology, press Reset, then Compute
  (uDfhmKCdR0U 00:14:52).
- Conform direction: set Shrink Wrap with Closest Point for detail recovery (sRLKiz4HSgA 00:09:30);
  it is the slowest mode, so Cache the Conform before saving on heavy meshes (00:05:10).
- P9: no holes (open edges 0), face count within about 10 percent of the target [added], silhouette
  against the reference.

## P4. Retopology prerequisites for CAD, scan or generated meshes

Goal: a source that ReForm can turn into clean quads, then the finishing stack. Source: sKEu2Gs3G_U
00:00:21 to 00:03:58, HhUMdy-0kSI 00:01:10 to 00:04:44, Pg2Nm-fwyME frames 00:13:53 to 00:16:35,
fXI2MJ7Bw2k 00:17:00 (source complexity ceiling).

```python
# channel: batch | bridge | handoff (compute: see P3)
# checked against sKEu2Gs3G_U, HhUMdy-0kSI, Pg2Nm-fwyME notes (frames)
import pymxs
rt = pymxs.runtime
try:
    mm = maxkit_modeling
except NameError:
    import maxkit_modeling as mm

ARGS = {"node": "GEO_Part", "symmetric": True, "face_target": 6000, "smooth_angle": 30.0,
        "subdivide_edge_length": 2.0, "finish": "chamfer_opensubdiv"}
NAMES = {
    "smooth_auto": ("autosmooth",), "smooth_threshold": ("threshold",),      # [verify]
    "slice_remove": ("slice_type", "slicetype"), "slice_remove_bottom": 3,   # [verify] enum
    "subdiv_method": ("method",), "subdiv_adaptive": 1,                      # [verify] enum
    "subdiv_edge": ("edgelength", "size"),                                   # [verify]
    "retopo_faces": ("facecount", "targetfacecount"),                        # [verify]
    "retopo_regularize": ("regularize",), "retopo_adaptivity": ("adaptivity",),  # [verify]
    "chamfer_from_smoothing": ("filterbysmoothing", "fromsmoothing"), "unsmoothed": 2,  # [verify]
    "chamfer_miter": ("mitertype", "mitering"), "radial": 3,                 # [verify]
    "osd_iterations": ("iterations",),                                       # [verify]
}

node = rt.getNodeByName(ARGS["node"])
before = mm.mesh_checks(node)
log = []
with pymxs.undo(True, "modeling: retopo stack"):
    # smoothing groups drive ReForm's edge flow (sKEu2Gs3G_U 00:00:21)
    log.append(mm.add_mod(node, ("Smooth",), {NAMES["smooth_auto"]: True,  # [verify]
                                              NAMES["smooth_threshold"]: ARGS["smooth_angle"]})[1])
    if ARGS["symmetric"]:
        # half the mesh: faster compute and exact symmetry; place the Slice plane on the mirror plane
        log.append(mm.add_mod(node, ("SliceModifier", "Slice"), {NAMES["slice_remove"]: NAMES["slice_remove_bottom"]})[1])
    # even triangles: ReForm "really likes" uniform input (sKEu2Gs3G_U 00:02:22)
    log.append(mm.add_mod(node, ("Subdivide",), {NAMES["subdiv_method"]: NAMES["subdiv_adaptive"],
                                                  NAMES["subdiv_edge"]: ARGS["subdivide_edge_length"]})[1])
    log.append(mm.add_mod(node, ("Retopology",), {NAMES["retopo_faces"]: ARGS["face_target"],
                                                   NAMES["retopo_regularize"]: 1.0,
                                                   NAMES["retopo_adaptivity"]: 0.0})[1])
    if ARGS["symmetric"]:
        log.append(mm.add_mod(node, ("Symmetry",))[1])  # [verify]; check axis and zero the gizmo
    if ARGS["finish"] == "chamfer_opensubdiv":
        log.append(mm.add_mod(node, ("Smooth",), {NAMES["smooth_auto"]: True, NAMES["smooth_threshold"]: 35.0})[1])
        log.append(mm.add_mod(node, ("Chamfer",), {NAMES["chamfer_from_smoothing"]: NAMES["unsmoothed"],
                                                    NAMES["chamfer_miter"]: NAMES["radial"]})[1])
        log.append(mm.add_mod(node, ("OpenSubdiv",), {NAMES["osd_iterations"]: 2})[1])

result = {"before": before, "log": log, "audit": mm.stack_audit(node)}
```

Check before computing:

- `before.faces` is at least twice `face_target` [added from fXI2MJ7Bw2k 00:17:00]. If not, raise
  the Subdivide density first: "the complexity of the beginning is your limit".
- CAD input with sliver faces: Compute may report "Calculation failed" (sKEu2Gs3G_U frame 00:01:21).
  Relax the slivers (Relax modifier as the scripted stand-in for the Freeform Soften brush) and
  re-smooth by angle.
- After Compute: crooked loops mean raise Regularize, lower Anisotropy or Adaptivity (sKEu2Gs3G_U
  00:03:26, HhUMdy-0kSI 00:02:35). One part too coarse: make its Retopology unique and give it its
  own face count (HhUMdy-0kSI 00:04:44).
- Generated meshes from scenario-3dsmax-generation enter here. Static props that must keep detail
  and UVs may be better decimated than retopologized; that call belongs to
  scenario-3dsmax-game-assets.

## P5. Subdivision cage with creases

Goal: sharp edges on a subdivided form without support loops, and a stretch test. Source:
UpBbEXkqeuw 00:00:38 to 00:05:42, QIPOLr4j3lM 00:12:41 to 00:13:15, opensubdiv doc (Iterations 0 to
6, Render Iterations 0 to 10, Crease Uniform or Chaikin), chamfer doc (By Crease Weight).

```python
# channel: batch | bridge | handoff
# checked against poly-modeling__opensubdiv-modifier.md, UpBbEXkqeuw and QIPOLr4j3lM notes
import pymxs
rt = pymxs.runtime
try:
    mm = maxkit_modeling
except NameError:
    import maxkit_modeling as mm

ARGS = {"node": "GEO_Shell", "hard_angle": 60.0, "crease": 1.0, "iterations": 1, "render_iterations": 2}
NAMES = {"crease_channel": 1}  # [verify] edge data channel used by Crease in Editable Poly

node = rt.getNodeByName(ARGS["node"])
po = rt.polyop
log = []
with pymxs.undo(True, "modeling: crease cage"):
    # crease by rule: edges whose face angle exceeds hard_angle stand in for a hand edge selection
    hard = []
    for e in range(1, int(po.getNumEdges(node)) + 1):  # [verify]
        faces = list(po.getEdgeFaces(node, e))  # [verify]
        if len(faces) != 2:
            continue
        n1 = po.getFaceNormal(node, faces[0])  # [verify]
        n2 = po.getFaceNormal(node, faces[1])
        ang = rt.acos(max(-1.0, min(1.0, rt.dot(n1, n2))))  # [verify] acos and dot in degrees
        if ang > ARGS["hard_angle"]:
            hard.append(e)
    if hard:
        sel = rt.execute("#{%s}" % ",".join(str(e) for e in hard))
        po.setEdgeData(node, NAMES["crease_channel"], sel, ARGS["crease"])  # [verify]
    osd, rep = mm.add_mod(node, ("OpenSubdiv",), {("iterations",): ARGS["iterations"],  # [verify]
                                                  ("renderiterations",): ARGS["render_iterations"],
                                                  ("userenderiterations",): True})
    log.append(rep)

result = {"creased_edges": len(hard), "log": log, "audit": mm.stack_audit(node)}
```

Check:

- `creased_edges` is not zero and not every edge. Creasing every edge of a box with no extra loops
  gives a stretched "squashed sphere" (UpBbEXkqeuw 00:01:42): add a few loops and recrease, because
  new loops start at crease 0 (00:02:20).
- The node must be an Editable Poly base (the block edits the base object). On a live stack, use the
  Crease or CreaseSet modifier instead, placed between the base and OpenSubdiv (QIPOLr4j3lM
  00:12:41). Its "All Edges" mode is scriptable through properties from P1; named edge sets in
  CreaseSet need an edge selection, which is GUI work or an Edit Poly selection made by script below
  it.
- Multi-edge creases with different weights: set OpenSubdiv Crease to Chaikin (opensubdiv doc).
- Several edge groups: one named CreaseSet per group, each with its own value. Named sets avoid
  support loops and give ready seam candidates for UVW unwrap (Adam Z, UpBbEXkqeuw 00:05:42).
- Support loops where a crease is not enough: select the polygon ring and Extrude with Local Normal
  at 0 (right-click the spinner). It gives a closed loop in one step (Todd D, yx-lpHy8yPs 00:06:35).
  Scripted substitute: `polyop.extrudeFaces` with height 0 [verify].
- P9 captures at iterations 1 and 2: look for stretching on flat faces and soft corners.

## P6. Spline modeling: tube frames, pipes, lathes, lofts

Goal: frames and pipes as live splines with real bend radii, swept or rendered as mesh. Source:
3dJ1VLgeKmM 00:00:08 to 00:03:35 (Shift extends a spline, Corner knots, Spline Chamfer, Radial
thickness 5.0 and 16 sides), whatsnew-2027 (Spline Chamfer fixed radius), MAXScript what's new 2027
(`UseRadius`, `AutoWeld`, `Extrude_Direction`), tP7FD4l-qus 00:32:08 (spline to poly with 6 sides).

```python
# channel: batch | bridge | handoff
# checked against 3dJ1VLgeKmM note, poly-modeling__whatsnew-2027.md, maxscript-whats-new-2027.md
import pymxs
rt = pymxs.runtime
try:
    mm = maxkit_modeling
except NameError:
    import maxkit_modeling as mm

ARGS = {
    "name": "SPL_Frame",
    "points": [(0, 0, 0), (0, 0, 38), (55, 0, 38), (70, 0, 85)],  # cm, path knots (corners)
    "closed": False,
    "bend_radius": 6.0,      # cm; about 2.5x a 2.4 cm tube [added], match the product photo
    "tube_diameter": 2.4,    # cm
    "sides": 16,             # 16 for close-ups (3dJ1VLgeKmM frame 00:03:35); fewer for distant props
    "mode": "renderable",    # "renderable" or "sweep"
}

with pymxs.undo(True, "modeling: spline frame"):
    shp = rt.SplineShape(name=ARGS["name"])  # [verify]
    s = rt.addNewSpline(shp)  # [verify]
    for p in ARGS["points"]:
        rt.addKnot(shp, s, rt.Name("corner"), rt.Name("line"), rt.Point3(*p))  # [verify] Corner knots avoid odd bends
    if ARGS["closed"]:
        rt.close(shp, s)  # [verify]
    rt.updateShape(shp)  # [verify]
    # Spline Chamfer with a fixed radius gives constant round corners (2027); AutoWeld and UseRadius are documented
    sc, rep_sc = mm.add_mod(shp, ("Spline_Chamfer", "SplineChamfer"),  # [verify] class name
                            {("UseRadius",): True, ("AutoWeld",): True, ("radius", "amount"): ARGS["bend_radius"]})
    if ARGS["mode"] == "renderable":
        rep_r = mm.set_props(shp, {("render_displayRenderMesh", "displayrendermesh"): True,  # [verify]
                                   ("render_renderable", "renderable"): True,               # [verify]
                                   ("render_thickness", "thickness"): ARGS["tube_diameter"],  # [verify]
                                   ("render_sides", "sides"): ARGS["sides"]})               # [verify]
    else:
        sw, rep_r = mm.add_mod(shp, ("Sweep",), {})  # [verify] set the built-in section from P1 names
    rep_steps = mm.set_props(shp, {("steps",): 8, ("optimize",): False})  # [verify] interpolation for round bends

result = {"spline_chamfer": rep_sc, "mesh": rep_r, "steps": rep_steps}
```

Check:

- Corner radius reads round in a capture at the hero distance; interpolation steps too low show
  facets.
- Tube ends need caps and a small chamfer: collapse a copy for the joints only; keep the spline live
  (baseline G2 kept the spline live, which matches 3dJ1VLgeKmM 00:00:41).
- Helix, Star and Loft (uDfhmKCdR0U): build `Helix` and `Star` primitives by script, Loft by GUI
  (Create > Compound Objects > Loft > Get Path). Loft Scale and Twist curves are GUI dialogs; the
  scripted substitute is a spline whose radius is computed per knot [added].
- Tapered spout or horn: Loft a circle along the spout path, then Deformations > Scale: two points
  near the tip pulled down for the taper, one at the base held wider, Bezier smoothing (Todd D,
  uDfhmKCdR0U 00:07:07). The Scale dialog is GUI only; the scripted substitute is the per-knot
  radius spline above [added].
- Lathe for turned parts (stand bases, knobs): profile spline plus Lathe modifier, Align Min, then
  Weld Core (Igor Mota, 0jXxaGKuW6Y 00:12:28). The Lathe property names, Weld Core included, are not
  in the saved docs: they keep `[verify]` until P1 lists them.
- Spline Chamfer names: `UseRadius` and `AutoWeld` are documented in the MAXScript 2027 what's new
  page; only the modifier class name and the radius property stay `[verify]`.

### P6b. Even-thickness shells

Goal: a part of constant wall thickness (a molded shell, a cup, a tablecloth) from a one-sided
surface. Source: QIPOLr4j3lM 00:12:06 (Cloth, then Shell, then TurboSmooth 2; frame 00:12:20 Inner
0.0 cm, Outer 0.4 cm, value marked unsure), 0jXxaGKuW6Y frames 00:16:55 and 00:17:20 (Shell over a
thin part, then Chamfer).

- Model the outer skin only, as an open surface with no faces where the opening will be.
- Stack: Editable Poly or Edit Poly, Shell (Inner 0, Outer the wall thickness), then Chamfer or
  OpenSubdiv above it. Keep Shell below the smoother so the rim rounds with the rest.
- The class and property names (`Shell`, `innerAmount`, `outerAmount`) are not in the saved docs:
  probe them with P1 (`shell` is in its candidate list) [verify].
- Check: open edges 0 after Shell; the rim reads as one even band in an Edged Faces capture.

## P7. Displace wrinkles and Conform drapes (fabric and soft detail)

Goal: fabric wrinkles painted with stacked Displace gizmos, model stack untouched. Source:
ALiGLb6TsS4 00:01:03 to 00:07:04; 75_n7o0u8sw 00:05:13 to 00:07:58 (Noise on a face selection, FFD
before TurboSmooth).

```python
# channel: bridge | handoff (batch works but gives no visual check)
# checked against ALiGLb6TsS4 note (stack frame 00:05:59), api-names.txt (bitmaptexture)
import pymxs
rt = pymxs.runtime
try:
    mm = maxkit_modeling
except NameError:
    import maxkit_modeling as mm

ARGS = {"nodes": ["GEO_Cushion", "GEO_Piping"], "wrinkle_map": None,  # path to a height image, given by the user
        "regions": [{"pos": (0, -20, 45), "rot_z": 0, "strength": 1.5},
                    {"pos": (25, -20, 30), "rot_z": 90, "strength": 1.0}],
        "blur": 2.0}
NAMES = {"strength": ("strength",), "decay": ("decay",), "blur": ("blur",),
         "lumcenter": ("luminancecenterenable", "lumcenter"), "map": ("map",), "usemap": ("usemap",)}  # [verify] all

tex = rt.bitmaptexture(filename=ARGS["wrinkle_map"]) if ARGS["wrinkle_map"] else None
log = []
with pymxs.undo(True, "modeling: displace wrinkles"):
    for name in ARGS["nodes"]:
        node = rt.getNodeByName(name)
        for r in ARGS["regions"]:
            d, rep = mm.add_mod(node, ("Displace",), {  # [verify]
                NAMES["strength"]: r["strength"], NAMES["decay"]: 1.0, NAMES["blur"]: ARGS["blur"],
                NAMES["lumcenter"]: True, NAMES["usemap"]: tex is not None})
            if tex is not None:
                rep["map"] = mm.set_props(d, {NAMES["map"]: tex})  # one shared map = instance behavior
            try:
                d.gizmo.position = rt.Point3(*r["pos"])  # [verify] gizmo sub-anim access
                d.gizmo.rotation = rt.eulerAngles(0, 0, r["rot_z"])  # [verify]
            except Exception as exc:
                rep["gizmo"] = "place the gizmo in the GUI: %s" % exc
            log.append(rep)

result = {"log": log}
```

Check:

- The receiving mesh is dense enough: Displace moves vertices, so add TurboSmooth or OpenSubdiv
  below the Displace stack when wrinkles look blocky (ALiGLb6TsS4 00:06:30).
- Hard outline at the gizmo border: raise Decay first, then plug a radial Gradient Ramp into the Mix
  Amount and lower the Mix's white color (00:02:14 to 00:03:50). That map work belongs to
  scenario-3dsmax-materials if it grows.
- Multi-part objects (cushion plus piping): paste the same Displace onto each part and move its
  gizmo; the block above does this through `ARGS["nodes"]` (00:05:57).
- Subtle "lived-in" sag on a cushion or seat: Affect Region at low strength instead of more Displace
  (Jake Denham, QIPOLr4j3lM 00:00:33).
- Deciding condition: Displace stacks for fabric detail and speed; real drape over a form is a Cloth
  simulation, then Shell, then TurboSmooth, owned by scenario-3dsmax-fx (digest batch3,
  disagreements).
- Judge on a render, not the viewport (ALiGLb6TsS4 00:04:21).
- The wrinkle image can come from scenario-3dsmax-generation (a tileable height map); this procedure
  only consumes the file path.

## P8. Array on a retopologized surface

Goal: scatter studs, rivets or sprinkles on even triangles. Source: TEz7tBiRrXc 00:09:32 to 00:10:38
(Retopology preprocess 2,000 faces as the distribution source, remove 75 percent, circular
dependency fix), EMaI6o162Cs 00:03:23 to 00:11:30 (order distribute, transform, randomize; Transform
Before Projection; Create Objects).

```python
# channel: batch | bridge | handoff
# checked against TEz7tBiRrXc and EMaI6o162Cs notes; maxscript-whats-new-2027.md (Array outputType)
import pymxs
rt = pymxs.runtime
try:
    mm = maxkit_modeling
except NameError:
    import maxkit_modeling as mm

ARGS = {"element": "GEO_Stud", "surface": "GEO_Column_RetopoRef", "remove_percent": 75, "seed": 12345}
NAMES = {"distribution": ("distribution",), "surface_mode": 4,   # [verify] enum
         "surface_node": ("surfaceobject", "distributionobject"),  # [verify]
         "remove": ("removepercent", "remove"), "seed": ("seed",),  # [verify]
         "tbp": ("transformbeforeprojection",)}  # [verify]

el = rt.getNodeByName(ARGS["element"])
with pymxs.undo(True, "modeling: array on surface"):
    a, rep = mm.add_mod(el, ("Array", "ArrayModifier"), {  # [verify]
        NAMES["distribution"]: NAMES["surface_mode"],
        NAMES["surface_node"]: rt.getNodeByName(ARGS["surface"]),
        NAMES["remove"]: ARGS["remove_percent"], NAMES["seed"]: ARGS["seed"], NAMES["tbp"]: True})

result = {"array": rep}
```

Check:

- The surface source is a Reference copy of the base with its own Retopology (preprocess, about
  2,000 faces), never the Boolean result that the array then cuts: that loop is a circular
  dependency (TEz7tBiRrXc 00:10:08). Subtract the array with a second Boolean above the Reference.
- Material ID or UV outputs on the Array break instancing for Create Objects (EMaI6o162Cs 00:11:30).
  A parameter that does not refresh: change Phase and cancel (00:08:34).
- Stitching on upholstery: select the seam edge loop, Create Shape From Selection, then an Array
  modifier on a stitch element distributed along that spline, Position 0.7, axis Y (Jake Denham,
  QIPOLr4j3lM 00:00:52). This keeps stitches as geometry that follows later edits, instead of a
  normal map or hand-placed dashes. Create Shape From Selection is an Edit Poly edge-level button
  (GUI); the spline distribution property names are `[verify]`.

## P9. Verify a modeled part (numbers, then captures)

Goal: the gate every procedure ends with.

```python
# channel: bridge | handoff (batch: numbers only, no captures)
# checked against the toolkit contract (capture.viewport, stats.snapshot)
import os
import pymxs
rt = pymxs.runtime
try:
    mm = maxkit_modeling
except NameError:
    import maxkit_modeling as mm

ARGS = {"node": "GEO_Body", "out_dir": None, "expect_open_edges": 0, "max_ngons": 0}

node = rt.getNodeByName(ARGS["node"])
checks = mm.mesh_checks(node)
audit = mm.stack_audit(node)
shots = []
if ARGS["out_dir"] and not rt.maxops.isInNonInteractiveMode():
    rt.select(node)
    try:
        rt.viewport.SetShowEdgeFaces(True)  # [verify]
    except Exception:
        pass
    osd = [e["mod"] for e in mm.stack(node) if e["kind"] == "subdiv"]
    for it in (1, 2):
        for m in osd:
            m.iterations = it  # [verify]
        rt.redrawViews()
        for view in ("persp", "front", "left", "top"):
            path = os.path.join(ARGS["out_dir"], "%s_it%d_%s.png" % (ARGS["node"], it, view))
            capture.viewport(path, view=view)  # lead toolkit; [verify] view names
            shots.append(path)

fails = []
if checks["open_edges"] > ARGS["expect_open_edges"]:
    fails.append("open edges %d" % checks["open_edges"])
if checks["ngons"] > ARGS["max_ngons"]:
    fails.append("ngons %d" % checks["ngons"])
if checks["weldable_verts"]:
    fails.append("unwelded verts %d" % checks["weldable_verts"])
fails += [f["message"] for f in audit if f["severity"] in ("error", "warn")]
result = {"checks": checks, "audit": audit, "shots": shots, "pass": not fails, "fails": fails}
```

Then on the runner: `max_review.contact_sheet(shots, out)` and read one sheet, not each image. Judge
with critique.md. Leave `iterations` where the user had them, or set them back to 1 for viewport
work.

P9 for `mcp-safe`: load `scripts/mxs/maxkit_modeling.ms` content into the proposed script, then:

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against scripts/mxs/maxkit_modeling.ms
(
	local node = getNodeByName "GEO_Body"
	#(mm.meshChecks node, mm.stackAudit node)
)
```

## P10. Reference planes and silhouette check (product and furniture)

Goal: model against real dimensions and compare the silhouette by numbers, not by eye alone. Source:
tP7FD4l-qus 00:00:00 to 00:04:24 (planes at the image aspect, scaled to one known real dimension),
0jXxaGKuW6Y 00:00:28 (front and side planes), 75_n7o0u8sw 00:02:28 (photos from several angles).

```python
# channel: bridge | handoff
# checked against api-names.txt (Plane, PhysicalMaterial, bitmaptexture, base_color_map)
import pymxs
rt = pymxs.runtime

ARGS = {"image": None, "view": "front", "px": (2000, 800), "known_px": 1758, "known_cm": 87.9, "name": "REF_Front"}
# known_px: pixel length of one dimension you know in real life (overall length from the maker's page)

cm_per_px = ARGS["known_cm"] / float(ARGS["known_px"])
w = ARGS["px"][0] * cm_per_px
h = ARGS["px"][1] * cm_per_px
with pymxs.undo(True, "modeling: reference plane"):
    p = rt.Plane(name=ARGS["name"], length=h, width=w, lengthsegs=1, widthsegs=1)  # [verify] Plane property names
    if ARGS["view"] == "front":
        p.rotation = rt.eulerAngles(90, 0, 0)  # [verify] axis order; check in the capture
    elif ARGS["view"] == "left":
        p.rotation = rt.eulerAngles(90, 0, 90)
    mat = rt.PhysicalMaterial(name=ARGS["name"] + "_MAT")
    if ARGS["image"]:
        mat.base_color_map = rt.bitmaptexture(filename=ARGS["image"])  # [verify] bitmaptexture filename keyword
    p.material = mat
    p.isFrozen = True  # [verify]
    p.backfacecull = True  # [verify] one-sided reference (tP7FD4l-qus 00:01:04)

result = {"plane": ARGS["name"], "size_cm": (round(w, 2), round(h, 2)), "cm_per_px": cm_per_px}
```

Check:

- The plane size matches the image aspect and one known real measurement; everything else is modeled
  to it.
- Silhouette gate: capture the orthographic view with the reference hidden, threshold both images to
  masks, and compare on the runner with `max_review.compare` [added]. Look at the difference image:
  a band along one edge means a proportion is off; noise along all edges is fine.
- A generated front or side view (image from scenario-3dsmax-generation) works the same way, but its
  proportions are not measured: anchor it to one real dimension and say so to the user.
