"""maxkit.stats: scene numbers before and after a change (pymxs, main thread only).

Checked against scripting-pipeline__pymxs-using-2027.md and
scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md. Names not in
the saved docs carry [verify] on their line.

    collect() -> {"nodes": [record, ...], "scene": {...}}      reads the live scene
    aggregate(data) -> snapshot dict                             pure
    snapshot() -> aggregate(collect())
    diff(a, b) -> {key: {"before", "after", "delta"}}            pure

Snapshot keys: objects, geometry, faces, vertices, instances (nodes sharing a base object with
another node), modifiers, materials, missing_maps (list), file_size (bytes or None), layers
(name -> node count), classes (class -> count), system_unit, system_scale, renderer, file,
save_required.

A record (one per node): name, cls, superclass, layer, faces, verts, base_id, modifiers,
material, material_class, pos [x,y,z], scale [x,y,z], bbox_min, bbox_max, parent, hidden,
group_head. Tests feed fake records to aggregate() and the audit rules.
"""
from __future__ import annotations

import os

GEOMETRY = "GeometryClass"


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _vec(v):
    try:
        return [float(v.x), float(v.y), float(v.z)]
    except Exception:
        return None


def _node_record(rt, o) -> dict:
    sup = _safe(lambda: str(rt.superClassOf(o)), "")  # [verify] superClassOf
    rec = {
        "name": _safe(lambda: str(o.name), "?"),
        "cls": _safe(lambda: str(rt.classOf(o)), "?"),
        "superclass": sup,
        "layer": _safe(lambda: str(o.layer.name), None),  # [verify] node.layer
        "faces": 0,
        "verts": 0,
        "base_id": _safe(lambda: int(rt.getHandleByAnim(o.baseObject)), None),  # [verify] getHandleByAnim, baseObject
        "modifiers": _safe(lambda: len(list(o.modifiers)), 0),  # [verify] node.modifiers
        "material": _safe(lambda: str(o.material.name) if o.material is not None else None, None),  # [verify] node.material
        "material_class": _safe(lambda: str(rt.classOf(o.material)) if o.material is not None else None, None),
        "pos": _safe(lambda: _vec(o.pos), None),  # [verify] node.pos
        "scale": _safe(lambda: _vec(o.scale), None),  # [verify] node.scale
        "bbox_min": None,
        "bbox_max": None,
        "parent": _safe(lambda: str(o.parent.name) if o.parent is not None else None, None),
        "hidden": _safe(lambda: bool(o.isHidden), False),  # [verify] node.isHidden
        "group_head": _safe(lambda: bool(rt.isGroupHead(o)), False),  # [verify] isGroupHead
    }
    if sup == GEOMETRY:
        counts = _safe(lambda: list(rt.getPolygonCount(o)), [0, 0])  # [verify] getPolygonCount -> #(faces, verts)
        rec["faces"], rec["verts"] = int(counts[0]), int(counts[1])
        bb = _safe(lambda: list(rt.nodeGetBoundingBox(o, rt.matrix3(1))), None)  # [verify] nodeGetBoundingBox, matrix3
        if bb:
            rec["bbox_min"], rec["bbox_max"] = _vec(bb[0]), _vec(bb[1])
    return rec


def _bitmap_files(rt) -> list[dict]:
    out = []
    for cls_name in ("BitmapTexture",):  # renderer bitmaps (VRayBitmap, CoronaBitmap) need their own pass [verify]
        cls = _safe(lambda: getattr(rt, cls_name), None)
        if cls is None:
            continue
        for b in _safe(lambda: list(rt.getClassInstances(cls)), []):  # [verify] getClassInstances
            fn = _safe(lambda: str(b.filename), "")  # [verify] BitmapTexture.filename
            if fn:
                out.append({"file": fn, "exists": bool(_safe(lambda: rt.doesFileExist(fn), False))})
    return out


def collect() -> dict:
    """Read every node and scene setting. Main thread only; read-only."""
    from pymxs import runtime as rt
    nodes = [_node_record(rt, o) for o in list(rt.objects)]  # [verify] objects collection
    path = _safe(lambda: str(rt.maxFilePath) + str(rt.maxFileName), "")
    scene = {
        "file": path or None,
        "file_size": _safe(lambda: os.path.getsize(path), None) if path else None,
        "save_required": _safe(lambda: bool(rt.getSaveRequired()), None),
        "system_unit": _safe(lambda: str(rt.units.SystemType), None),  # [verify] units.SystemType
        "system_scale": _safe(lambda: float(rt.units.SystemScale), None),  # [verify] units.SystemScale
        "renderer": _safe(lambda: str(rt.classOf(rt.renderers.current)), None),
        "bitmaps": _bitmap_files(rt),
        "layer_names": _safe(lambda: [str(rt.LayerManager.getLayer(i).name)  # [verify] LayerManager
                                      for i in range(int(rt.LayerManager.count))], None),
        "scene_materials": _safe(lambda: len(list(rt.sceneMaterials)), None),  # [verify] sceneMaterials
    }
    return {"nodes": nodes, "scene": scene}


def aggregate(data: dict) -> dict:
    """Pure: totals from collect() output (or fake data in tests)."""
    nodes = data.get("nodes", [])
    scene = data.get("scene", {})
    geo = [n for n in nodes if n.get("superclass") == GEOMETRY]
    bases: dict = {}
    for n in nodes:
        if n.get("base_id") is not None:
            bases[n["base_id"]] = bases.get(n["base_id"], 0) + 1
    instances = sum(c for c in bases.values() if c > 1)
    layers: dict = {}
    for name in scene.get("layer_names") or []:
        layers.setdefault(name, 0)
    for n in nodes:
        key = n.get("layer") or "?"
        layers[key] = layers.get(key, 0) + 1
    classes: dict = {}
    for n in nodes:
        classes[n.get("cls", "?")] = classes.get(n.get("cls", "?"), 0) + 1
    mats = {(n.get("material"), n.get("material_class")) for n in nodes if n.get("material")}
    missing = sorted({b["file"] for b in scene.get("bitmaps", []) if not b.get("exists")})
    return {
        "objects": len(nodes),
        "geometry": len(geo),
        "faces": sum(int(n.get("faces") or 0) for n in geo),
        "vertices": sum(int(n.get("verts") or 0) for n in geo),
        "instances": instances,
        "modifiers": sum(int(n.get("modifiers") or 0) for n in nodes),
        "materials": scene.get("scene_materials") if scene.get("scene_materials") is not None else len(mats),
        "missing_maps": missing,
        "file_size": scene.get("file_size"),
        "layers": layers,
        "classes": classes,
        "system_unit": scene.get("system_unit"),
        "system_scale": scene.get("system_scale"),
        "renderer": scene.get("renderer"),
        "file": scene.get("file"),
        "save_required": scene.get("save_required"),
    }


def snapshot() -> dict:
    """Numbers for the current scene. Main thread only; read-only."""
    return aggregate(collect())


def diff(a: dict, b: dict) -> dict:
    """Pure: what changed between two snapshots. Numbers get a delta; lists and dicts get
    added and removed items; other values appear only when they differ."""
    out: dict = {}
    for key in sorted(set(a) | set(b)):
        va, vb = a.get(key), b.get(key)
        if va == vb:
            continue
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            out[key] = {"before": va, "after": vb, "delta": vb - va}
        elif isinstance(va, list) or isinstance(vb, list):
            sa, sb = set(va or []), set(vb or [])
            out[key] = {"added": sorted(sb - sa), "removed": sorted(sa - sb)}
        elif isinstance(va, dict) or isinstance(vb, dict):
            da, db = va or {}, vb or {}
            out[key] = {k: {"before": da.get(k), "after": db.get(k)}
                        for k in sorted(set(da) | set(db)) if da.get(k) != db.get(k)}
        else:
            out[key] = {"before": va, "after": vb}
    return out
