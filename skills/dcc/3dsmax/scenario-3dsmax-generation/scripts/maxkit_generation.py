"""maxkit_generation: land a Scenario-generated file in a 3ds Max scene (pymxs, main thread).

Inlined into a wrapped script by the lead's max_wrap (kit list), like the shared maxkit modules.
Runs through batch, bridge or handoff. For mcp-safe use the MAXScript in references/procedures.md.

Status: not yet run in 3ds Max; checked against
scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (importFile, #noPrompt,
fileProperties.addProperty), scripting-pipeline__maxscript-whats-new-2027.md (PLYImport, SPZImport),
scripting-pipeline__gltf-import-2027.md (glTF importer). Names marked [verify] are not in the saved docs.

    snapshot() -> set                                  keys of the nodes in the scene now
    import_file(path) -> list                          imports with #noPrompt, returns the new nodes
    extent(nodes) -> dict                              world bounding box in system units
    system_unit_in_meters() -> float                   meters per system unit
    land_model(path, name, layer, ...) -> dict         import, root, scale, floor, layer, provenance
    land_splat(path, name, layer, ...) -> dict         import a PLY/SPZ/LCC splat, report
    tag(nodes, record) -> None                         provenance on nodes and in file properties

Every function changes the scene only inside the caller's undo record (max_wrap opens it).
"""
from __future__ import annotations

_UNIT_M = {  # meters per unit for units.SystemType names [verify enum spelling]
    "inches": 0.0254, "feet": 0.3048, "miles": 1609.344, "millimeters": 0.001,
    "centimeters": 0.01, "meters": 1.0, "kilometers": 1000.0,
}


def _rt():
    from pymxs import runtime as rt
    return rt


def _key(node):
    rt = _rt()
    try:
        return int(rt.getHandleByAnim(node))  # [verify] stable per-session id
    except Exception:
        return id(node)


def snapshot() -> set:
    rt = _rt()
    return {_key(o) for o in rt.objects}


def import_file(path: str) -> list:
    """importFile picks the importer by suffix; #noPrompt uses "the default configuration" (importFile
    doc). Whether that follows the last dialog choice (glTF material type, splat up axis) is not
    documented: check the material classes in the report after the first #noPrompt import."""
    rt = _rt()
    before = snapshot()
    ok = rt.importFile(path, rt.Name("noPrompt"))
    if not ok:
        raise RuntimeError(f"importFile returned false for {path}")
    return [o for o in rt.objects if _key(o) not in before]


def system_unit_in_meters() -> float:
    rt = _rt()
    unit = str(rt.units.SystemType).lower().lstrip("#")  # [verify] returns a name like #centimeters
    scale = float(rt.units.SystemScale)  # [verify]
    if unit not in _UNIT_M:
        raise ValueError(f"unknown system unit {unit}")
    return _UNIT_M[unit] * scale


def extent(nodes) -> dict:
    """World bounding box from node.min and node.max (system units)."""
    mins = [n.min for n in nodes]
    maxs = [n.max for n in nodes]
    lo = [min(p.x for p in mins), min(p.y for p in mins), min(p.z for p in mins)]
    hi = [max(p.x for p in maxs), max(p.y for p in maxs), max(p.z for p in maxs)]
    return {"min": lo, "max": hi, "size": [hi[i] - lo[i] for i in range(3)]}


def _faces(node) -> int:
    rt = _rt()
    try:
        return int(rt.getPolygonCount(node)[0])  # [verify] returns #(faces, verts)
    except Exception:
        return -1


def _layer(name: str):
    rt = _rt()
    lay = rt.LayerManager.getLayerFromName(name)  # [verify]
    if lay is None:
        lay = rt.LayerManager.newLayerFromName(name)  # [verify]
    return lay


def tag(nodes, record: dict) -> None:
    """Provenance: per-node user properties [verify setUserProp] plus one scene-level custom file
    property (doc-confirmed), so the record survives even if node properties are lost on export."""
    rt = _rt()
    keys = ("model_name", "model_id", "prompt", "generated_on", "asset_id", "sidecar")
    for n in nodes:
        for k in keys:
            if k in record and record[k] is not None:
                rt.setUserProp(n, "scenario_" + k, str(record[k])[:1000])  # [verify]
    label = "scenario:" + str(record.get("name", "asset"))
    rt.fileProperties.addProperty(rt.Name("custom"), label, str(record.get("sidecar", record.get("model_name", ""))))


def land_model(path: str, name: str, layer: str = "GEN_props", known_axis: int = 2,
               known_size_m: float | None = None, place_at=None, record: dict | None = None) -> dict:
    """Import one generated model and make it a scene asset.

    known_axis: 0 = X, 1 = Y, 2 = Z (height). known_size_m: the real dimension in meters taken from
    the brief, schedule or reference; None leaves scale untouched and reports the measured size.
    place_at: (x, y, z) in system units for the base center; None leaves it at the origin."""
    rt = _rt()
    new = import_file(path)
    if not new:
        return {"ok": False, "reason": "no new nodes"}
    new_keys = {_key(n) for n in new}
    roots = [n for n in new if n.parent is None or _key(n.parent) not in new_keys]
    before = extent(new)
    root = rt.Dummy()  # [verify] helper used as the asset root
    root.name = f"GEN_{name}_root"
    base = rt.Point3((before["min"][0] + before["max"][0]) / 2,
                     (before["min"][1] + before["max"][1]) / 2, before["min"][2])
    root.position = base
    for n in roots:
        n.parent = root
    factor = 1.0
    if known_size_m:
        target = known_size_m / system_unit_in_meters()
        measured = before["size"][known_axis]
        if measured <= 0:
            raise ValueError("measured size is zero on the known axis")
        factor = target / measured
        root.scale = rt.Point3(factor, factor, factor)
    root.position = rt.Point3(*(place_at or (0.0, 0.0, 0.0)))
    lay = _layer(layer)
    for n in [root] + new:
        lay.addNode(n)  # [verify]
    for i, n in enumerate(new):
        if not str(n.name).startswith("GEN_"):
            n.name = f"GEN_{name}_{i:02d}"
    after = extent(new)
    if record:
        rec = dict(record, name=name)
        tag([root] + new, rec)
    mats = {}
    for n in new:
        m = getattr(n, "material", None)
        if m is not None:
            mats[str(m.name)] = str(rt.classOf(m))
    return {
        "ok": True, "root": str(root.name), "nodes": [str(n.name) for n in new],
        "faces_total": sum(max(_faces(n), 0) for n in new),
        "size_before": before["size"], "size_after": after["size"], "scale_factor": factor,
        "base_z_after": after["min"][2], "materials": mats,
        "system_unit_m": system_unit_in_meters(),
    }


def land_splat(path: str, name: str, layer: str = "GEN_splats", record: dict | None = None) -> dict:
    """Import a PLY, SPZ or LCC splat (2027.2+). File > Import embeds the data in the scene; the
    Gaussian Splat object's File parameter keeps a live reference instead (GUI path in gui-paths.md)."""
    rt = _rt()
    new = import_file(path)
    lay = _layer(layer)
    for i, n in enumerate(new):
        n.name = f"GEN_{name}_splat{i:02d}"
        lay.addNode(n)  # [verify]
    if record:
        tag(new, dict(record, name=name))
    box = extent(new) if new else None
    return {"ok": bool(new), "nodes": [str(n.name) for n in new],
            "classes": [str(rt.classOf(n)) for n in new], "extent": box,
            "system_unit_m": system_unit_in_meters()}
