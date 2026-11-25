"""maxkit_game: engine-asset helpers for scenario-3dsmax-game-assets (pymxs, runs inside 3ds Max).

channel: batch | bridge | handoff (prepend this file to the chunk given to max_wrap.wrap;
         procedures.md section 1). Named game_audit, not audit, so the lead's audit module stays reachable.
checked against notes/game-assets digests (rules and numbers),
        game-assets__unreal-fbx-static-mesh-pipeline.md (FBX 2020.2, UCX_, SOCKET_, pivot at origin),
        scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (exportFile flags),
        scripting-pipeline__maxscript-whats-new-2027.md (FBXExporterGetParam) and
        scenario-3dsmax-expert/references/api-names.txt. Names not in the saved docs carry [verify].

Call every function on the main thread only. Functions that change the scene open their own
pymxs.undo record (nesting inside the max_wrap record is fine). pymxs.undo rolls back and swallows
an exception raised inside it (pymxs module doc, 2027), so _undo re-raises it after the record closes. Nothing here saves over a user
file: export paths are versioned (_v002, _v003) when the target exists.

Public functions:
    game_audit()                               read-only JSON-ready dict (same rules as mxs/game_audit.ms)
    prop_names(obj)                       lower-case property names (getPropNames), for discovery
    set_props(obj, wanted)                {(candidate, ...): value} -> {"set": {}, "missing": []}
    normalize_intake(node, target_cm=None, measure="longest", pivot="bottom_center", up_fix=None)
    normalize_group(nodes, ...)           same for a multipart import: one shared rotation, scale and move
    make_lod(node, level, vertex_percent, base_name=None)
    add_box_collision(node, index=0, pad_cm=0.0)
    set_fbx_params(params)                set then read back each FBX exporter parameter
    export_fbx_game(path, nodes, target="unreal", extra=None)
    versioned(path)                       first free path: name.ext, name_v002.ext, ...
"""

import contextlib
import json
import os

import pymxs

rt = pymxs.runtime

# Same text as mxs/game_audit.ms up to its last two lines (kept identical by archive test).
MXS_AUDIT = r'''fn gaJsonStr s = (
    s = s as string
    local out = ""
    for i = 1 to s.count do (
        local c = s[i]
        if c == "\"" then out += "\\\""
        else if c == "\\" then out += "\\\\"
        else if c == "\n" then out += "\\n"
        else if c == "\r" then out += "\\r"
        else if c == "\t" then out += "\\t"
        else out += c
    )
    "\"" + out + "\""
)

fn gaJoin arr sep = (
    local out = ""
    for i = 1 to arr.count do (
        if i > 1 do out += sep
        out += arr[i]
    )
    out
)

fn gaNum v = (
    -- float to JSON number; MAXScript may print 1e-06 style, which JSON accepts
    local s = v as string
    if (findString s "#") != undefined then "null" else s   -- NaN or infinity prints with #
)

fn gaP3 p = "[" + (gaNum p.x) + "," + (gaNum p.y) + "," + (gaNum p.z) + "]"

-- Convexity of a collision hull: count vertices lying outside any face plane (tolerance in system units).
fn gaConvexViolations m tol = (
    local bad = 0
    local nf = getNumFaces m                              -- [verify]
    local nv = getNumVerts m                              -- [verify]
    for f = 1 to nf do (
        local fn3 = getFaceNormal m f                     -- [verify]
        local fv = getFace m f                            -- [verify] point3 of vertex indices
        local p0 = getVert m (fv.x as integer)            -- [verify]
        for v = 1 to nv do (
            if (dot fn3 ((getVert m v) - p0)) > tol do bad += 1   -- [verify] dot
        )
    )
    bad
)

fn gaAuditNode n faceCap:500000 = (
    local m = snapshotAsMesh n                            -- [verify] world-space TriMesh of the stack result
    local nf = getNumFaces m                              -- [verify]
    local nv = getNumVerts m                              -- [verify]
    local sg0 = -1
    if nf <= faceCap do (
        sg0 = 0
        for f = 1 to nf do if (getFaceSmoothGroup m f) == 0 do sg0 += 1   -- [verify]
    )
    local openE = (meshop.getOpenEdges m).numberSet       -- [verify]
    local isoV = (meshop.getIsoVerts m).numberSet         -- [verify]
    local maps = #()
    for ch = -2 to ((meshop.getNumMaps m) - 1) do (      -- [verify] -2 alpha, -1 illum, 0 vertex color, 1+ UV
        if (meshop.getMapSupport m ch) do append maps (ch as string)   -- [verify]
    )
    local ngons = -1
    if classOf n == Editable_Poly do (                    -- [verify] Editable_Poly class name
        ngons = 0
        for f = 1 to (polyop.getNumFaces n) do if (polyop.getFaceDeg n f) > 4 do ngons += 1   -- [verify]
    )
    local mn = n.min
    local mx = n.max
    local s = n.scale                                     -- [verify]
    local negScale = (s.x * s.y * s.z) < 0
    local mods = for md in n.modifiers collect gaJsonStr (classOf md)   -- [verify] node.modifiers
    local matCls = if n.material == undefined then "null" else gaJsonStr (classOf n.material)
    local subCount = 0
    if n.material != undefined and (classOf n.material) == Multimaterial do subCount = n.material.numsubs   -- [verify]
    local convexBad = -1
    if (matchPattern n.name pattern:"UCX_*") and nf <= 2000 do convexBad = gaConvexViolations m 0.01
    "{" + \
        "\"name\":" + (gaJsonStr n.name) + \
        ",\"class\":" + (gaJsonStr (classOf n)) + \
        ",\"tris\":" + (nf as string) + \
        ",\"verts\":" + (nv as string) + \
        ",\"ngons\":" + (ngons as string) + \
        ",\"open_edges\":" + (openE as string) + \
        ",\"iso_verts\":" + (isoV as string) + \
        ",\"sg0_faces\":" + (sg0 as string) + \
        ",\"map_channels\":[" + (gaJoin maps ",") + "]" + \
        ",\"bbox_min\":" + (gaP3 mn) + \
        ",\"bbox_max\":" + (gaP3 mx) + \
        ",\"pos\":" + (gaP3 n.pos) + \
        ",\"pivot\":" + (gaP3 n.pivot) + \
        ",\"scale\":" + (gaP3 s) + \
        ",\"rotation_identity\":" + ((n.rotation == (quat 0 0 0 1)) as string) + \
        ",\"negative_scale\":" + (negScale as string) + \
        ",\"parent\":" + (if n.parent == undefined then "null" else gaJsonStr n.parent.name) + \
        ",\"modifiers\":[" + (gaJoin mods ",") + "]" + \
        ",\"material_class\":" + matCls + \
        ",\"sub_materials\":" + (subCount as string) + \
        ",\"convex_violations\":" + (convexBad as string) + \
    "}"
)

fn gaAuditScene = (
    local sel = if selection.count > 0 then (selection as array) else (objects as array)
    local geo = #()
    local others = #()
    for n in sel do (
        if (superClassOf n == GeometryClass) and (canConvertTo n TriMeshGeometry) then (   -- [verify] canConvertTo
            append geo (gaAuditNode n)
        ) else (
            append others ("{\"name\":" + (gaJsonStr n.name) + ",\"class\":" + (gaJsonStr (classOf n)) + \
                ",\"pos\":" + (gaP3 n.pos) + ",\"parent\":" + \
                (if n.parent == undefined then "null" else gaJsonStr n.parent.name) + "}")
        )
    )
    "{\"units\":" + (gaJsonStr units.SystemType) + \
        ",\"system_scale\":" + (gaNum units.SystemScale) + \
        ",\"nodes\":[" + (gaJoin geo ",") + "]" + \
        ",\"helpers\":[" + (gaJoin others ",") + "]}"
)
'''

_mxs_ready = False

# FBX exporter parameter names follow the FBX dialog; none is in the saved docs. set_fbx_params
# reads each one back with FBXExporterGetParam and reports the ones that did not stick.
FBX_PRESETS = {
    # Unreal: FBX 2020.2 per Epic's static mesh pipeline doc; Z up; cm; smoothing groups on.
    "unreal": {
        "SmoothingGroups": True,            # [verify] CM3GwvoOSP4 dialog; Epic doc
        "Triangulate": True,                # [verify] mesh is already triangulated on the export copy
        "PreserveEdgeOrientation": True,    # [verify] CM3GwvoOSP4 00:01:45 turned-edges warning
        "SmoothMeshExport": False,          # [verify] TurboSmooth result not baked into the low poly
        "TangentSpaceExport": False,        # [verify] [added] let the engine compute MikkTSpace tangents
        "Animation": False,                 # [verify]
        "Cameras": False,                   # [verify]
        "Lights": False,                    # [verify]
        "EmbedTextures": False,             # [verify]
        "UpAxis": "Z",                      # [verify]
        "ConvertUnit": "cm",                # [verify]
        "FileVersion": "FBX202000",         # [verify] value string for the 2020 file format
    },
    # Unity: Up Axis Z then Bake Axis Conversion in Unity's model importer (Ghost Pig z1ws_LOo9AU 00:04:16).
    "unity": {
        "SmoothingGroups": True,            # [verify] Ghost Pig Game Exporter frame 00:04:56
        "Triangulate": True,                # [verify]
        "PreserveEdgeOrientation": True,    # [verify]
        "SmoothMeshExport": False,          # [verify]
        "Animation": False,                 # [verify]
        "Cameras": False,                   # [verify]
        "Lights": False,                    # [verify]
        "EmbedTextures": True,              # [verify] Embed Media ticked in Ghost Pig's dialog
        "UpAxis": "Z",                      # [verify]
        "ConvertUnit": "cm",                # [verify]
    },
}


@contextlib.contextmanager
def _undo(label):
    err = []
    with pymxs.undo(True, label):
        try:
            yield
        except Exception as exc:
            err.append(exc)
            raise
    if err:
        raise err[0]


# ---------------------------------------------------------------- discovery

def prop_names(obj):
    """Lower-case property names of a modifier or object (getPropNames is in the saved docs)."""
    try:
        return [str(p).lower() for p in rt.getPropNames(obj)]
    except Exception:
        return []


def set_props(obj, wanted):
    """Set the first existing candidate name for each value. Report what could not be set."""
    names = prop_names(obj)
    report = {"set": {}, "missing": []}
    for candidates, value in wanted.items():
        if isinstance(candidates, str):
            candidates = (candidates,)
        hit = next((c for c in candidates if c.lower() in names), None)
        if hit is None:
            report["missing"].append("/".join(candidates))
            continue
        try:
            setattr(obj, hit, value)
            report["set"][hit] = value
        except Exception as exc:  # wrong type or read-only
            report["missing"].append(f"{hit} ({exc})")
    return report


def _find_class(*names):
    for name in names:
        cls = getattr(rt, name, None)
        if cls is not None:
            return cls
    return None


# ---------------------------------------------------------------- audit

def game_audit():
    """Run the MAXScript audit on the selection (or all objects) and return the parsed dict."""
    global _mxs_ready
    if not _mxs_ready:
        rt.execute(MXS_AUDIT)  # [verify] pymxs.runtime.execute evaluates MAXScript source
        _mxs_ready = True
    return json.loads(str(rt.gaAuditScene()))


# ---------------------------------------------------------------- intake

def _is_cm():
    """Centimeters with a 1.0 multiplier: 1 system unit = 1 cm."""
    if str(rt.units.SystemType).lower() != "centimeters":  # [verify] units.SystemType
        return False
    return abs(float(rt.units.SystemScale) - 1.0) < 1e-6  # [verify] units.SystemScale


def _p3(v):
    return [float(v.x), float(v.y), float(v.z)]


def _bounds(nodes):
    lo = [min(_p3(n.min)[k] for n in nodes) for k in range(3)]
    hi = [max(_p3(n.max)[k] for n in nodes) for k in range(3)]
    return lo, hi


def _reset(nodes):
    for n in nodes:
        rt.ResetXForm(n)     # [verify]
        rt.collapseStack(n)  # [verify]


def normalize_group(nodes, target_cm=None, measure="longest", pivot="bottom_center", up_fix=None):
    """Reset transforms, optionally rotate up axis, scale uniformly to a real size, set the pivot,
    move to the origin. Every step uses the shared bounds of all nodes, so the parts of a multipart
    import keep their relative placement. Each node's pivot ends on the shared pivot, at the origin.
    Refuses unless 1 system unit is 1 cm.

    measure: "longest", "height" (Z) or "width" (X). pivot: "bottom_center" or "corner" (min x, y, z).
    up_fix: None, "y_up_to_z_up" (+90 deg about X). Returns before/after numbers."""
    nodes = list(nodes)
    if not nodes:
        raise ValueError("no nodes to normalize")
    if not _is_cm():
        raise RuntimeError("system unit is not 1 cm (type centimeters, scale 1); set units first "
                           "(scenario-3dsmax-scene)")
    lo, hi = _bounds(nodes)
    rep = {"names": [str(n.name) for n in nodes], "before": {"min": lo, "max": hi}}
    with _undo("game: normalize intake"):
        if up_fix == "y_up_to_z_up":
            c = rt.Point3(*[(lo[k] + hi[k]) / 2.0 for k in range(3)])
            for n in nodes:
                n.pivot = c  # [verify] node.pivot
                rt.rotate(n, rt.angleaxis(90, rt.Point3(1, 0, 0)))  # [verify] rotate, angleaxis
        _reset(nodes)
        if target_cm:
            lo, hi = _bounds(nodes)
            dims = [hi[k] - lo[k] for k in range(3)]
            cur = {"longest": max(dims), "height": dims[2], "width": dims[0]}[measure]
            if cur <= 0:
                raise RuntimeError("zero size along the measured axis")
            f = float(target_cm) / cur
            c = rt.Point3((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2])
            for n in nodes:
                n.pivot = c
                n.scale = rt.Point3(f, f, f)  # uniform only: non-uniform scale breaks UBX/USP and Datasmith instances
            _reset(nodes)
            rep["scale_factor"] = f
        lo, hi = _bounds(nodes)
        if pivot == "corner":
            p = rt.Point3(lo[0], lo[1], lo[2])
        else:
            p = rt.Point3((lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, lo[2])
        for n in nodes:
            n.pivot = p
            n.pos = rt.Point3(0, 0, 0)
    lo, hi = _bounds(nodes)
    rep["after"] = {"min": lo, "max": hi, "pos": _p3(nodes[0].pos), "pivot": _p3(nodes[0].pivot)}
    return rep


def normalize_intake(node, target_cm=None, measure="longest", pivot="bottom_center", up_fix=None):
    """normalize_group for one node; same arguments. Returns before/after numbers."""
    rep = normalize_group([node], target_cm, measure, pivot, up_fix)
    rep["name"] = rep.pop("names")[0]
    return rep


# ---------------------------------------------------------------- LODs and collision

def make_lod(node, level, vertex_percent, base_name=None):
    """Copy node as <base>_LOD<level> and reduce it with ProOptimizer (Keep Textures and Keep UV
    Boundaries before Calculate, Crytek s_RShJy4k-g 00:05:44). Property names are probed."""
    base = base_name or str(node.name)
    report = {"lod": f"{base}_LOD{level}"}
    cls = _find_class("ProOptimizer")  # [verify] class name
    if cls is None:
        report["error"] = "ProOptimizer class not found; use Modifier List > ProOptimizer"
        return report
    with _undo(f"game: LOD{level}"):
        lod = rt.copy(node)
        lod.name = report["lod"]
        mod = cls()
        rt.addModifier(lod, mod)
        report["flags"] = set_props(mod, {
            ("KeepUV",): True,        # [verify] Keep Textures (ProOptimizer MAXScript page, 2027)
            ("LockUV",): True,        # [verify] Keep UV Boundaries (same page)
            ("KeepNormals",): True,   # [verify] same page
            ("LockMat",): True,       # [verify] Keep Material Boundaries (same page)
        })
        report["percent"] = set_props(mod, {("VertexPercent", "OptLevel"): float(vertex_percent)})  # [verify]
        report["calculate"] = set_props(mod, {("Calculate",): True})  # [verify] if missing: GUI Calculate
        rt.collapseStack(lod)  # [verify]
    report["tris"] = int(rt.getNumFaces(rt.snapshotAsMesh(lod)))  # [verify]
    return report


def add_box_collision(node, index=0, pad_cm=0.0):
    """Box hull around node's world bounding box, named UCX_<node>_<index:02d>, converted to mesh.
    Leave gaps between several hulls (Epic doc). Assumes centimeters."""
    with _undo("game: UCX box"):
        mn, mx = node.min, node.max
        w = (mx.x - mn.x) + 2 * pad_cm
        d = (mx.y - mn.y) + 2 * pad_cm
        h = (mx.z - mn.z) + 2 * pad_cm
        box = rt.Box(width=w, length=d, height=h)  # [verify] Box keyword args
        box.pos = rt.Point3((mn.x + mx.x) / 2.0, (mn.y + mx.y) / 2.0, mn.z - pad_cm)
        box.name = f"UCX_{node.name}_{index:02d}"
        rt.convertToMesh(box)
    return {"name": str(box.name), "size_cm": [w, d, h]}


# ---------------------------------------------------------------- export

def versioned(path):
    """Return path if free, else name_v002.ext, name_v003.ext ... (never overwrite)."""
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    i = 2
    while os.path.exists(f"{stem}_v{i:03d}{ext}"):
        i += 1
    return f"{stem}_v{i:03d}{ext}"


def set_fbx_params(params):
    """Set FBX exporter parameters, read each back, return {"ok": {...}, "mismatch": {...}}."""
    out = {"ok": {}, "mismatch": {}}
    rt.FBXExporterSetParam("ResetExport")  # [verify] resets the exporter to defaults first
    for key, value in params.items():
        try:
            rt.FBXExporterSetParam(key, value)  # [verify]
            back = rt.FBXExporterGetParam(key)  # FBXExporterGetParam is in maxscript-whats-new-2027
            if str(back).lower() == str(value).lower():
                out["ok"][key] = str(back)
            else:
                out["mismatch"][key] = {"wanted": str(value), "got": str(back)}
        except Exception as exc:
            out["mismatch"][key] = {"wanted": str(value), "error": str(exc)}
    return out


def export_fbx_game(path, nodes, target="unreal", extra=None):
    """Export triangulated copies of nodes (names kept exactly, so UCX_ and SOCKET_ still match)
    with the target preset, then remove the copies. The work nodes are left untouched."""
    params = dict(FBX_PRESETS[target])
    params.update(extra or {})
    path = versioned(path)
    report = {"path": path, "params": set_fbx_params(params), "exported": []}
    copies = []
    with _undo("game: FBX export copies"):
        try:
            for n in nodes:
                c = rt.copy(n)
                c.name = n.name  # duplicate names only while exporting; the copies are deleted below
                if rt.superClassOf(c) == rt.GeometryClass:  # [verify]
                    rt.convertToMesh(c)  # triangulate in Max (Epic doc: best done in the 3D app)
                copies.append(c)
            rt.select(copies)
            ok = rt.exportFile(path, rt.Name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)
            report["ok"] = bool(ok)
            report["exported"] = [str(c.name) for c in copies]
        finally:
            for c in copies:
                rt.delete(c)
    report["exists"] = os.path.exists(path)
    report["bytes"] = os.path.getsize(path) if report["exists"] else 0
    return report
