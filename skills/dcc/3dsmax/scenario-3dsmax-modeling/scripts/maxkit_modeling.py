"""maxkit_modeling: modeling helpers for scenario-3dsmax-modeling (pymxs, runs inside 3ds Max).

channel: batch | bridge | handoff (inlined through max_wrap.wrap(kit=[...]))
checked against scripting-pipeline__pymxs-using-2027.md,
        scenario-3dsmax-expert/references/api-names.txt and the poly-modeling notes and digests.

Names marked [verify] were not found in the saved docs. The helpers resolve modifier classes and
properties by probing (getPropNames) instead of assuming them, and report what they could not find.
Call every function on the main thread only. Wrap scene changes in pymxs.undo (max_wrap does).

Public functions:
    find_class(*names)                 first runtime class among candidate names, or None
    prop_names(obj)                    lower-case property names of a modifier or object
    set_props(obj, wanted)             set {candidate tuple: value}; returns {"set": {}, "missing": []}
    add_mod(node, class_names, wanted=None, before=None)   add a modifier, return (mod, report)
    stack(node)                        modifiers bottom to top as dicts
    stack_audit(node)                  findings {severity, rule, node, message} for stack order rules
    mesh_checks(node, weld_tol=0.001)  counts on a temporary collapsed copy: faces, tris, quads, ngons, open edges
    voxel_ratio(node, voxel_size)      largest bounding box side divided by the OpenVDB voxel size
    mirror_seam_check(node, axis=0, tol=0.01)   verts close to but not on the mirror plane
"""

import pymxs

rt = pymxs.runtime


# ---------------------------------------------------------------- class and property discovery

def find_class(*names):
    """Return the first runtime class found among candidate names, else None."""
    for name in names:
        try:
            cls = getattr(rt, name)
        except AttributeError:
            continue
        if cls is not None:
            return cls
    return None


def prop_names(obj):
    try:
        return [str(n).lower() for n in list(rt.getPropNames(obj))]
    except Exception:  # getPropNames refuses some wrapped values
        return []


def set_props(obj, wanted):
    """wanted maps a tuple of candidate property names (or one name) to a value.

    The first candidate that exists on obj is set. Missing candidates are reported, never guessed.
    """
    have = prop_names(obj)
    report = {"set": {}, "missing": [], "errors": {}}
    for candidates, value in (wanted or {}).items():
        if isinstance(candidates, str):
            candidates = (candidates,)
        hit = next((c for c in candidates if c.lower() in have), None)
        if hit is None:
            report["missing"].append("/".join(candidates))
            continue
        try:
            setattr(obj, hit, value)
            report["set"][hit] = value
        except Exception as exc:  # wrong type or enum value: report it
            report["errors"][hit] = str(exc)
    return report


def add_mod(node, class_names, wanted=None, before=None):
    """Instantiate the first resolvable modifier class and add it on top (or before an index).

    before: MAXScript-style index into node.modifiers (1 = top). [verify] keyword on addModifier.
    """
    if isinstance(class_names, str):
        class_names = (class_names,)
    cls = find_class(*class_names)
    if cls is None:
        return None, {"error": "no class among " + ", ".join(class_names)}
    mod = cls()
    if before is None:
        rt.addModifier(node, mod)
    else:
        rt.addModifier(node, mod, before=before)  # [verify] before: keyword
    report = set_props(mod, wanted)
    report["class"] = str(rt.classOf(mod))
    return mod, report


# ---------------------------------------------------------------- stack reading and audit

def _kind(mod):
    """Coarse family of a modifier from its class name, so audits do not depend on exact names."""
    c = str(rt.classOf(mod)).lower()
    for key, kind in (
        ("creaseset", "crease"), ("crease", "crease"), ("opensubdiv", "subdiv"),
        ("turbosmooth", "subdiv"), ("meshsmooth", "subdiv"), ("ffd", "ffd"),
        ("smartbevel", "smartbevel"), ("boolean", "boolean"), ("chamfer", "chamfer"),
        ("poly_select", "polyselect"), ("polyselect", "polyselect"), ("mesh_select", "polyselect"),
        ("retopology", "retopo"), ("conform", "conform"), ("symmetry", "symmetry"),
        ("slice", "slice"), ("subdivide", "subdivide"), ("weighted", "wnormals"),
        ("displace", "displace"), ("shell", "shell"), ("smooth", "smooth"),
        ("edit_poly", "editpoly"), ("editpoly", "editpoly"),
    ):
        if key in c:
            return kind
    return c


def stack(node):
    """Modifiers bottom to top: [{i, cls, name, kind, enabled}] with i = 0 at the bottom."""
    mods = list(node.modifiers)  # top first, as in MAXScript
    out = []
    for i, m in enumerate(reversed(mods)):
        try:
            enabled = bool(m.enabled)  # [verify] modifier .enabled
        except Exception:
            enabled = None
        out.append({"i": i, "cls": str(rt.classOf(m)), "name": str(m.name),
                    "kind": _kind(m), "enabled": enabled, "mod": m})
    return out


def _finding(sev, rule, node, msg):
    return {"severity": sev, "rule": rule, "node": str(node.name), "message": msg}


def stack_audit(node):
    """Order rules from the experts (see references/critique.md for the sources)."""
    s = stack(node)
    kinds = [e["kind"] for e in s]
    f = []

    def first(kind):
        return kinds.index(kind) if kind in kinds else None

    sub = first("subdiv")
    for e in s:
        if e["kind"] == "crease" and sub is not None and e["i"] > sub:
            f.append(_finding("error", "crease-below-subdiv", node,
                              e["name"] + " sits above the subdivision modifier; OpenSubdiv only reads creases from below"))
        if e["kind"] == "ffd" and sub is not None and e["i"] > sub:
            f.append(_finding("warn", "ffd-before-smooth", node,
                              e["name"] + " is above the smoothing modifier; put FFD below it for broad soft moves"))
        if e["enabled"] is False:
            f.append(_finding("info", "disabled-modifier", node, e["name"] + " is disabled"))

    # Boolean > Chamfer > (no Poly Select) > Boolean: the next Chamfer re-bevels old edges
    for a, b in zip(range(len(s)), range(1, len(s))):
        if kinds[a] == "boolean" and kinds[b] == "chamfer":
            f.append(_finding("info", "chamfer-after-boolean", node,
                              "Chamfer directly above a Boolean: in 2027 consider Smart Bevel above the Boolean"))
    last_chamfer = None
    for i, k in enumerate(kinds):
        if k == "chamfer":
            last_chamfer = i
        elif k == "polyselect":
            last_chamfer = None
        elif k == "boolean" and last_chamfer is not None:
            f.append(_finding("warn", "selection-not-cleared", node,
                              "a Chamfer passes its edge selection into a later Boolean; insert an empty Poly Select"))
            last_chamfer = None

    for e in s:
        m = e["mod"]
        if e["kind"] == "subdiv":
            it = _get(m, ("iterations",))
            if it is not None and it > 2:
                f.append(_finding("warn", "viewport-iterations", node,
                                  "%s viewport iterations %s; keep 1 to 2 and use render iterations" % (e["name"], it)))
        if e["kind"] == "retopo":
            target = _get(m, ("facecount", "face_count", "targetfacecount"))  # [verify] property name
            if target:
                below = _faces_below(node, e["i"])
                if below is not None and below < 2 * target:
                    f.append(_finding("warn", "retopo-source-too-simple", node,
                                      "source has %d faces for a %d face target; give it at least 2x" % (below, target)))
        if e["kind"] == "chamfer" and sub is not None and e["i"] < sub:
            mit = _get(m, ("mitertype", "mitering"))  # [verify] property name and enum
            if mit is not None and "tri" in str(mit).lower():
                f.append(_finding("warn", "tri-miter-under-subdiv", node,
                                  "Chamfer Tri mitering under subdivision causes smoothing issues (Chamfer doc)"))
    if "symmetry" in kinds and "slice" in kinds and kinds.index("slice") > kinds.index("symmetry"):
        f.append(_finding("warn", "slice-after-symmetry", node, "Slice sits above Symmetry; halve first, then mirror"))
    return f


def _get(obj, candidates):
    have = prop_names(obj)
    for c in candidates:
        if c in have:
            try:
                return getattr(obj, c)
            except Exception:
                return None
    return None


def _faces_below(node, index_from_bottom):
    """Face count of the stack result just below a modifier, by disabling it and those above. [verify]"""
    s = stack(node)
    saved = [(e["mod"], e["enabled"]) for e in s[index_from_bottom:]]
    try:
        for m, _ in saved:
            m.enabled = False  # [verify]
        return int(rt.getPolygonCount(node)[0])  # [verify] returns #(faces, verts)
    except Exception:
        return None
    finally:
        for m, was in saved:
            if was is not None:
                m.enabled = was


# ---------------------------------------------------------------- mesh measurements

def mesh_checks(node, weld_tol=0.001):
    """Measure a collapsed temporary copy; the user's node and stack are not touched.

    weld_tol is in system units: the count of verts that weld at that distance flags unwelded seams.
    """
    tmp = rt.copy(node)
    try:
        rt.convertToPoly(tmp)  # [verify]
        po = rt.polyop
        nf = int(po.getNumFaces(tmp))  # [verify]
        nv = int(po.getNumVerts(tmp))  # [verify]
        degs = [int(po.getFaceDeg(tmp, i)) for i in range(1, nf + 1)]  # [verify] 1-based index
        open_edges = len(list(po.getOpenEdges(tmp)))  # [verify] returns a bitarray
        all_verts = rt.execute("#{1..%d}" % nv)
        po.weldVertsByThreshold(tmp, all_verts)  # [verify] uses the object's weld threshold
        welded = nv - int(po.getNumVerts(tmp))
        bb = rt.nodeGetBoundingBox(node, rt.matrix3(1))  # [verify]
        size = [float(bb[1][k] - bb[0][k]) for k in range(3)]
    finally:
        rt.delete(tmp)
    return {
        "node": str(node.name), "faces": nf, "verts": nv,
        "tris": degs.count(3), "quads": degs.count(4), "ngons": sum(1 for d in degs if d > 4),
        "quad_ratio": round(degs.count(4) / nf, 3) if nf else 0.0,
        "open_edges": open_edges, "weldable_verts": welded, "weld_tol": weld_tol,
        "bbox_size": size,
    }


def voxel_ratio(node, voxel_size):
    """Largest bbox side / voxel size. About 100 is a starting point [added]; flag under 50 or over 500."""
    bb = rt.nodeGetBoundingBox(node, rt.matrix3(1))  # [verify]
    side = max(float(bb[1][k] - bb[0][k]) for k in range(3))
    ratio = side / float(voxel_size)
    verdict = "ok" if 50 <= ratio <= 500 else ("too coarse" if ratio < 50 else "too fine, may freeze")
    return {"largest_side": side, "voxel": voxel_size, "ratio": round(ratio, 1), "verdict": verdict}


def mirror_seam_check(node, axis=0, tol=0.01):
    """Count verts within 10*tol of the mirror plane that are not on it.

    Assumes the mirror plane passes through the world origin on `axis` (pivot at 0 on that axis).
    """
    tmp = rt.copy(node)
    try:
        rt.convertToPoly(tmp)  # [verify]
        po = rt.polyop
        off = []
        for i in range(1, int(po.getNumVerts(tmp)) + 1):  # [verify]
            p = po.getVert(tmp, i)  # [verify] world space unless node: is passed
            v = float((p.x, p.y, p.z)[axis])
            if tol < abs(v) < 10 * tol:
                off.append(i)
    finally:
        rt.delete(tmp)
    return {"node": str(node.name), "axis": "xyz"[axis], "near_plane_off_by_more_than_tol": len(off)}
