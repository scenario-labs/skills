"""maxkit_scene: scene-assembly helpers for 3ds Max 2027.3 (pymxs).

channel: batch | bridge | handoff (prepend to a chunk, then max_wrap.wrap())
checked against sources/docs
    (scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md,
    scripting-pipeline__maxscript-whats-new-2027.md, fundamentals-scene__*.md).

Runs inside 3ds Max only, on the main thread. Read functions never change the
scene. Write functions run inside one pymxs.undo record, take dry_run=True by
default and return what they would do. Names marked [verify] are not in the
saved 2027 docs; each call to them is wrapped so a wrong name becomes a finding
instead of a crash.
"""
import os
import re

try:
    import pymxs
    from pymxs import runtime as rt
except ImportError:  # offline compile check outside 3ds Max
    pymxs = None
    rt = None

# Generic default names left by creation tools (Box001, Object237, Line04...).
DEFAULT_NAME_RE = re.compile(
    r"^(Box|Object|Line|Plane|Cylinder|Sphere|GeoSphere|Rectangle|Circle|Arc|"
    r"Shape|Group|Mesh|Point|Dummy|Teapot|Tube|Cone|Torus|ChamferBox|"
    r"ChamferCyl|Text|Camera|Light|Omni|Spot)\s?\d{2,}$",
    re.IGNORECASE,
)
# render.camp numbered layer scheme (FYRj1pCBQq8 05:17): 100_cams ... 600_dec.
LAYER_NAME_RE = re.compile(r"^\d{3}_[a-z0-9_]+$")

# Centimeters per system unit type; the system scale multiplies it.
_CM_PER_UNIT = {
    "inches": 2.54, "feet": 30.48, "miles": 160934.4, "millimeters": 0.1,
    "centimeters": 1.0, "meters": 100.0, "kilometers": 100000.0,
}


def _name(value):
    return str(value).lstrip("#").lower()


def _try(fn, default=None):
    try:
        return fn()
    except Exception as exc:  # wrong or missing API name: report, never crash
        return default if default is not None else "error: %s" % exc


def _nodes():
    return list(rt.objects)


def _top_nodes():
    return [n for n in rt.objects if n.parent is None]


# ---------------------------------------------------------------- read only

def units_report():
    """System and display units plus the 2027.1 file unit rules."""
    sys_type = _try(lambda: _name(rt.units.SystemType))      # [verify]
    sys_scale = _try(lambda: float(rt.units.SystemScale))    # [verify]
    rep = {
        "system_type": sys_type,
        "system_scale": sys_scale,
        "display_type": _try(lambda: _name(rt.units.DisplayType)),  # [verify]
        "metric_type": _try(lambda: _name(rt.units.MetricType)),    # [verify]
        # doc-confirmed names (2027.1): default unit handling on load and merge
        "load_unit_behavior": _try(lambda: str(rt.maxOps.GetSceneFileUnitHandlingBehavior())),
        "merge_unit_behavior": _try(lambda: str(rt.maxOps.GetMergeUnitHandlingDefaultBehavior())),
    }
    if sys_type in _CM_PER_UNIT and isinstance(sys_scale, float):
        rep["cm_per_system_unit"] = _CM_PER_UNIT[sys_type] * sys_scale
    return rep


def cm_per_unit():
    rep = units_report()
    return rep.get("cm_per_system_unit", 1.0)


def node_bbox(node):
    """World bounding box as ((x, y, z), (x, y, z))."""
    try:
        bb = rt.nodeGetBoundingBox(node, rt.matrix3(1))       # [verify]
        lo, hi = bb[0], bb[1]
    except Exception:
        lo, hi = node.min, node.max                           # [verify]
    return (lo.x, lo.y, lo.z), (hi.x, hi.y, hi.z)


def origin_report(far_cm=100000.0):
    """Scene extents and nodes whose bbox center lies farther than far_cm."""
    k = cm_per_unit()
    far, lo_all, hi_all = [], [float("inf")] * 3, [float("-inf")] * 3
    for n in _nodes():
        lo, hi = node_bbox(n)
        lo_all = [min(a, b) for a, b in zip(lo_all, lo)]
        hi_all = [max(a, b) for a, b in zip(hi_all, hi)]
        c = [(a + b) / 2.0 for a, b in zip(lo, hi)]
        d_cm = (c[0] ** 2 + c[1] ** 2 + c[2] ** 2) ** 0.5 * k
        if d_cm > far_cm:
            far.append({"node": n.name, "distance_m": round(d_cm / 100.0, 2),
                        "class": str(rt.classOf(n))})
    far.sort(key=lambda r: -r["distance_m"])
    ext = None
    if lo_all[0] != float("inf"):
        ext = {"min": lo_all, "max": hi_all,
               "size_m": [round((b - a) * k / 100.0, 3) for a, b in zip(lo_all, hi_all)]}
    return {"extents": ext, "far_count": len(far), "far": far[:200]}


def group_report():
    """Group heads with their nesting depth (1 = outermost)."""
    heads = [n for n in _nodes() if _try(lambda n=n: bool(rt.isGroupHead(n)), False)]  # [verify]
    rows = []
    for h in heads:
        depth, p = 1, h.parent
        while p is not None:
            if _try(lambda p=p: bool(rt.isGroupHead(p)), False):
                depth += 1
            p = p.parent
        rows.append({"group": h.name, "depth": depth})
    return {"groups": len(rows), "max_depth": max([r["depth"] for r in rows] or [0]),
            "rows": rows[:500]}


def name_report():
    names = [n.name for n in _nodes()]
    seen, dups = set(), set()
    for s in names:
        (dups if s in seen else seen).add(s)
    default = [s for s in names if DEFAULT_NAME_RE.match(s)]
    return {"objects": len(names), "default_named": len(default),
            "default_sample": default[:50], "duplicate_names": sorted(dups)[:200]}


def poly_report(top=30):
    rows = []
    for n in _nodes():
        if rt.superClassOf(n) != rt.GeometryClass:            # [verify]
            continue
        pc = _try(lambda n=n: rt.getPolygonCount(n), None)    # [verify] returns #(faces, verts)
        if pc is None or isinstance(pc, str):
            continue
        rows.append({"node": n.name, "faces": int(pc[0]), "verts": int(pc[1])})
    rows.sort(key=lambda r: -r["faces"])
    return {"geometry_nodes": len(rows), "faces_total": sum(r["faces"] for r in rows),
            "top": rows[:top]}


def scale_report(tol=1e-4):
    """Geometry nodes whose transform scale is not (1,1,1) (FS1 checklist, hz07nIgm7EA 00:21:31)."""
    rows = []
    for n in _nodes():
        if rt.superClassOf(n) != rt.GeometryClass:            # [verify]
            continue
        s = _try(lambda n=n: n.scale, None)                   # [verify] node scale as Point3
        if s is None or isinstance(s, str):
            continue
        if any(abs(v - 1.0) > tol for v in (s.x, s.y, s.z)):
            rows.append({"node": n.name, "scale": [round(s.x, 4), round(s.y, 4), round(s.z, 4)],
                         "modifiers": len(list(n.modifiers))})
    return {"non_unit_scale": len(rows), "rows": rows[:500]}


def _signature(node, k):
    pc = _try(lambda: rt.getPolygonCount(node), None)         # [verify]
    if pc is None or isinstance(pc, str):
        return None
    try:  # local (object space) size, so rotated copies still match
        bb = rt.nodeGetBoundingBox(node, node.transform)      # [verify]
        size = [round(abs(bb[1][i] - bb[0][i]) * k * 10.0) for i in range(3)]  # 1 mm steps
    except Exception:
        return None
    mat = node.material.name if node.material is not None else ""
    return (str(rt.classOf(node.baseObject)), int(pc[0]), int(pc[1]), tuple(size), mat)


def copy_candidates(min_count=2):
    """Groups of nodes that look like copies of one mesh but share no base object."""
    k = cm_per_unit()
    groups = {}
    for n in _nodes():
        if rt.superClassOf(n) != rt.GeometryClass:
            continue
        sig = _signature(n, k)
        if sig is not None:
            groups.setdefault(sig, []).append(n)
    out = []
    for sig, nodes in groups.items():
        bases = []
        for n in nodes:  # count distinct base objects in the group
            if not any(n.baseObject == b for b in bases):     # MXS value equality [verify]
                bases.append(n.baseObject)
        if len(bases) >= min_count:
            out.append({"signature": [sig[0], sig[1], sig[2], list(sig[3]), sig[4]],
                        "nodes": [n.name for n in nodes], "distinct_bases": len(bases)})
    out.sort(key=lambda r: -r["distinct_bases"] * r["signature"][1])
    return {"groups": len(out), "removable_bases": sum(r["distinct_bases"] - 1 for r in out),
            "rows": out[:200]}


def layer_report():
    """Nodes per layer, read from the node side (no by-reference calls)."""
    per = {}
    for n in _nodes():
        lname = _try(lambda n=n: n.layer.name, "?")           # [verify]
        per[lname] = per.get(lname, 0) + 1
    layer_names = []
    count = _try(lambda: int(rt.LayerManager.count), 0)      # [verify]
    for i in range(count if isinstance(count, int) else 0):
        layer_names.append(_try(lambda i=i: rt.LayerManager.getLayer(i).name, "?"))  # [verify]
    empty = [s for s in layer_names if s not in per]
    bad = [s for s in layer_names if s != "0" and not LAYER_NAME_RE.match(s)]
    return {"layers": len(layer_names), "on_layer_0": per.get("0", 0), "per_layer": per,
            "empty_layers": empty, "off_convention": bad}


def xref_report():
    """XRef scene records and XRef object record count; existence of each file."""
    scenes = []
    n = _try(lambda: int(rt.xrefs.getXRefFileCount()), 0)    # [verify]
    for i in range(1, (n if isinstance(n, int) else 0) + 1):
        x = _try(lambda i=i: rt.xrefs.getXRefFile(i), None)  # [verify]
        if x is None or isinstance(x, str):
            continue
        f = _try(lambda x=x: str(x.filename), "?")           # [verify]
        scenes.append({"file": f, "exists": bool(rt.doesFileExist(f)) if f != "?" else None,
                       "disabled": _try(lambda x=x: bool(x.disabled), "?")})  # [verify]
    obj_records = _try(lambda: int(rt.objXRefMgr.recordCount), "?")  # [verify]
    return {"xref_scenes": scenes, "xref_object_records": obj_records}


def turbosmooth_report():
    rows = []
    for n in _nodes():
        for m in list(n.modifiers):
            if str(rt.classOf(m)) in ("TurboSmooth", "OpenSubdiv"):
                rows.append({"node": n.name, "modifier": str(rt.classOf(m)),
                             "iterations": _try(lambda m=m: int(m.iterations), "?"),  # [verify]
                             "render_iterations": _try(lambda m=m: int(m.renderIterations), "?")})  # [verify]
    return {"count": len(rows), "viewport_iter_above_0": [r for r in rows if r["iterations"] not in (0, "?")][:200]}


def point_report():
    """Gaussian Splat and Editable Point objects (2027.2 and later)."""
    rows = []
    for n in _nodes():
        cls = str(rt.classOf(n.baseObject))
        if cls in ("GaussianSplat", "Editable_Point"):        # class names doc-confirmed
            rows.append({"node": n.name, "class": cls})
    return {"point_objects": len(rows), "rows": rows}


def bitmap_nodes():
    """(map, property, path) for file-based maps of the common renderers."""
    found = []
    for cls_name, prop in (("BitmapTexture", "filename"),    # [verify] each pair
                           ("VRayBitmap", "HDRIMapName"),
                           ("CoronaBitmap", "filename"),
                           ("ai_image", "filename")):
        cls = getattr(rt, cls_name, None)
        if cls is None:
            continue
        for m in _try(lambda cls=cls: list(rt.getClassInstances(cls)), []):  # [verify]
            path = _try(lambda m=m, prop=prop: str(getattr(m, prop)), "")
            found.append((m, prop, path))
    return found


def missing_maps_report():
    missing = sorted({p for _, _, p in bitmap_nodes() if p and p != "None" and not rt.doesFileExist(p)})
    return {"checked": len(bitmap_nodes()), "missing_count": len(missing), "missing": missing[:500]}


def audit_scene(far_cm=100000.0):
    """One dict with every scene-assembly finding. Pair it with audit.all()."""
    return {
        "file": os.path.join(str(rt.maxFilePath), str(rt.maxFileName)),
        "file_size_mb": _try(lambda: round(os.path.getsize(os.path.join(
            str(rt.maxFilePath), str(rt.maxFileName))) / 1048576.0, 1), "?"),
        "units": units_report(), "origin": origin_report(far_cm), "groups": group_report(),
        "names": name_report(), "polys": poly_report(), "scale": scale_report(),
        "copies": copy_candidates(),
        "layers": layer_report(), "xrefs": xref_report(), "smooth": turbosmooth_report(),
        "points": point_report(), "maps": missing_maps_report(),
    }


# ---------------------------------------------------------------- write (undo, dry_run)

def set_units_on_empty_scene(system_type="centimeters", scale=1.0, display="metric",
                             metric="centimeters"):
    """Refuses on a scene with objects: never change system units under geometry."""
    if len(_nodes()) > 0:
        return {"changed": False, "reason": "scene has %d objects" % len(_nodes())}
    rt.units.SystemType = rt.Name(system_type)                # [verify]
    rt.units.SystemScale = float(scale)                       # [verify]
    rt.units.DisplayType = rt.Name(display)                   # [verify]
    rt.units.MetricType = rt.Name(metric)                     # [verify]
    return {"changed": True, "units": units_report()}


def recenter(offset=None, helper_name="REF_SiteOrigin", dry_run=True):
    """Move every top-level node by -offset (system units). Animated nodes are skipped
    and listed. The offset is stored on a Point helper so updates can be re-placed."""
    if offset is None:  # default: center of the scene extents, z kept
        ext = origin_report(far_cm=float("inf"))["extents"]
        offset = [(ext["min"][0] + ext["max"][0]) / 2.0, (ext["min"][1] + ext["max"][1]) / 2.0, 0.0]
    moved, skipped = [], []
    for n in _top_nodes():
        animated = _try(lambda n=n: bool(n.isAnimated), False)  # [verify]
        (skipped if animated else moved).append(n)
    plan = {"offset": offset, "move": [n.name for n in moved][:500], "move_count": len(moved),
            "skipped_animated": [n.name for n in skipped]}
    if dry_run:
        return plan
    with pymxs.undo(True, "scene: recenter"):
        d = rt.Point3(-offset[0], -offset[1], -offset[2])
        for n in moved:
            n.position = n.position + d                       # [verify] world position
        h = rt.Point(name=helper_name)                        # Point helper at 0,0,0
        rt.setUserProp(h, "original_offset", "%r" % (list(offset),))  # [verify]
    plan["helper"] = helper_name
    return plan


def reset_scale(names=None, collapse=False, dry_run=True):
    """Reset XForm on non-unit-scale geometry (FS1 candidate procedure 1).
    collapse=True also collapses the stack: only for nodes whose modifiers are not needed;
    otherwise hand the node to the modeling sibling."""
    rows = scale_report()["rows"]
    if names is not None:
        rows = [r for r in rows if r["node"] in set(names)]
    plan = {"nodes": [r["node"] for r in rows], "count": len(rows), "collapse": collapse,
            "with_modifiers": [r["node"] for r in rows if r["modifiers"]]}
    if dry_run:
        return plan
    done, errors = [], []
    with pymxs.undo(True, "scene: reset scale"):
        for r in rows:
            n = rt.getNodeByName(r["node"])                   # [verify]
            if n is None:
                continue
            try:
                rt.ResetXForm(n)                              # [verify]
                if collapse:
                    rt.collapseStack(n)                       # [verify]
                done.append(r["node"])
            except Exception as exc:
                errors.append({"node": r["node"], "error": str(exc)})
    plan.update(done=done, errors=errors)
    return plan


def flatten_groups(dry_run=True):
    """Write each member's group path to a user prop, then explode outermost groups."""
    heads = [n for n in _nodes() if _try(lambda n=n: bool(rt.isGroupHead(n)), False)]  # [verify]
    def has_group_ancestor(node):
        p = node.parent
        while p is not None:
            if _try(lambda p=p: bool(rt.isGroupHead(p)), False):
                return True
            p = p.parent
        return False

    outer = [h for h in heads if not has_group_ancestor(h)]
    plan = {"group_heads": len(heads), "outermost": [h.name for h in outer]}
    if dry_run:
        return plan

    def path_of(node):
        parts, p = [], node.parent
        while p is not None:
            if _try(lambda p=p: bool(rt.isGroupHead(p)), False):
                parts.append(p.name)
            p = p.parent
        return "/".join(reversed(parts))

    with pymxs.undo(True, "scene: flatten groups"):
        for n in _nodes():
            gp = path_of(n)
            if gp:
                rt.setUserProp(n, "group_path", gp)           # [verify]
        for h in outer:
            rt.explodeGroup(h)                                # [verify]
    plan["remaining_group_heads"] = group_report()["groups"]
    return plan


def apply_layers(plan, dry_run=True):
    """plan: {layer_name: [node names]}. Creates missing layers, moves nodes."""
    missing_nodes = [s for names in plan.values() for s in names
                     if rt.getNodeByName(s) is None]
    out = {"layers": len(plan), "nodes": sum(len(v) for v in plan.values()),
           "missing_nodes": missing_nodes[:100]}
    if dry_run:
        return out
    with pymxs.undo(True, "scene: layers"):
        for lname, names in plan.items():
            layer = rt.LayerManager.getLayerFromName(lname)   # [verify]
            if layer is None:
                layer = rt.LayerManager.newLayerFromName(lname)  # [verify]
            for s in names:
                n = rt.getNodeByName(s)
                if n is not None:
                    layer.addNode(n)                          # [verify]
    out["after"] = layer_report()
    return out


def rename_nodes(mapping, dry_run=True):
    """mapping: {old: new}. Refuses if a new name collides with another node."""
    existing = {n.name for n in _nodes()}
    clashes = [v for k, v in mapping.items() if v in existing and v not in mapping]
    if clashes or dry_run:
        return {"renames": len(mapping), "clashes": clashes[:100]}
    with pymxs.undo(True, "scene: rename"):
        for old, new in mapping.items():
            n = rt.getNodeByName(old)
            if n is not None:
                n.name = new
    return {"renamed": len(mapping), "after": name_report()}


def instance_copies(groups, dry_run=True):
    """groups: rows from copy_candidates(). First node of each row becomes the master."""
    todo = [(g["nodes"][0], g["nodes"][1:]) for g in groups]
    out = {"masters": len(todo), "replaced": sum(len(c) for _, c in todo)}
    if dry_run:
        return out
    with pymxs.undo(True, "scene: copies to instances"):
        for master_name, copies in todo:
            master = rt.getNodeByName(master_name)
            for s in copies:
                n = rt.getNodeByName(s)
                if n is not None and master is not None:
                    rt.instanceReplace(n, master)             # [verify]
    return out


def relink_maps(search_dirs, dry_run=True):
    """Repath missing maps to a unique same-name file found under search_dirs."""
    index = {}
    for root_dir in search_dirs:
        for root, _dirs, files in os.walk(root_dir):
            for f in files:
                index.setdefault(f.lower(), []).append(os.path.join(root, f))
    fixed, ambiguous, still = [], [], []
    todo = []
    for m, prop, path in bitmap_nodes():
        if not path or path == "None" or rt.doesFileExist(path):
            continue
        hits = index.get(os.path.basename(path.replace("\\", "/")).lower(), [])
        if len(hits) == 1:
            todo.append((m, prop, path, hits[0]))
            fixed.append({"from": path, "to": hits[0]})
        elif hits:
            ambiguous.append({"from": path, "candidates": hits[:5]})
        else:
            still.append(path)
    if not dry_run:
        with pymxs.undo(True, "scene: relink maps"):
            for m, prop, _old, new in todo:
                setattr(m, prop, new)
    return {"relinked": fixed[:300], "ambiguous": ambiguous[:100],
            "still_missing": sorted(set(still))[:300], "dry_run": dry_run}


def smooth_viewport_off(dry_run=True):
    """TurboSmooth/OpenSubdiv: viewport iterations 0; keep a render value."""
    rows = turbosmooth_report()["viewport_iter_above_0"]
    if dry_run:
        return {"would_change": len(rows), "rows": rows[:100]}
    with pymxs.undo(True, "scene: smooth viewport off"):
        for r in rows:
            n = rt.getNodeByName(r["node"])
            for m in list(n.modifiers):
                if str(rt.classOf(m)) == r["modifier"]:
                    if r["render_iterations"] in (0, "?"):
                        m.useRenderIterations = True          # [verify]
                        m.renderIterations = int(r["iterations"])  # [verify]
                    m.iterations = 0                          # [verify]
    return {"changed": len(rows)}


def split_to_xref(node_names, out_path, dry_run=True):
    """Save nodes to a new .max (never over an existing file), remove them from this
    scene, then reference that file as an XRef scene."""
    nodes = [rt.getNodeByName(s) for s in node_names]
    nodes = [n for n in nodes if n is not None]
    out = {"nodes": len(nodes), "file": out_path, "exists": bool(rt.doesFileExist(out_path))}
    if dry_run or out["exists"]:
        return out
    ok = rt.saveNodes(nodes, out_path, quiet=True)           # doc-confirmed; overwrites silently
    if not ok:
        out["error"] = "saveNodes failed"
        return out
    with pymxs.undo(True, "scene: split to xref"):
        rt.delete(nodes)
        rt.xrefs.addNewXRefFile(out_path)                     # [verify]
    out["xrefs"] = xref_report()
    return out
