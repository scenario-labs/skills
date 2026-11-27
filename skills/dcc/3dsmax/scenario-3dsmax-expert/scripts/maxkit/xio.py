"""maxkit.xio: import and export with a report of what arrived or left (pymxs, main thread only).

Checked against
scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md (importFile and
exportFile with #noPrompt, quiet:, selectedOnly:, using:; plugin chosen by file suffix),
scripting-pipeline__gltf-import-2027.md, scripting-pipeline__gltf-export-2027.md and
scripting-pipeline__usd-import-export-2027.md.

    import_any(path, **opts) -> report
    export_fbx(path, preset=None, selected=False) -> report
    export_gltf(path, selected=False) -> report
    export_usd(path, selected=False) -> report
    gltf_precheck(data=None) -> [finding, ...]     pure over maxkit.stats.collect() records

Import report: path, ok, nodes (new node names), count, classes, materials, bbox_min, bbox_max,
size [x,y,z], system_unit. Export report: path, ok, bytes, nodes (what was exported), count,
system_unit.

Rules: every call passes #noPrompt, so the dialog is skipped and the importer or exporter uses
its last or default settings (options live in global state, not in the call). Export never
overwrites: an existing path gets a _v002 suffix. glTF and USD option names for scripting are
not in the saved docs: set them once in the dialog (GUI) or mark the call [verify].
"""
from __future__ import annotations

import os

try:
    from maxkit import stats as _stats
    from maxkit.capture import next_free
except ImportError:  # inlined by max_wrap
    import stats as _stats  # type: ignore
    from capture import next_free  # type: ignore


def _rt():
    from pymxs import runtime as rt
    return rt


def _handles(rt) -> dict:
    out = {}
    for o in list(rt.objects):  # [verify] objects collection
        try:
            out[int(rt.getHandleByAnim(o))] = o  # [verify] getHandleByAnim
        except Exception:
            out[id(o)] = o
    return out


def _report_nodes(rt, nodes, path, ok=True) -> dict:
    recs = [_stats._node_record(rt, o) for o in nodes]
    lo = hi = None
    for r in recs:
        if r.get("bbox_min") and r.get("bbox_max"):
            lo = r["bbox_min"] if lo is None else [min(a, b) for a, b in zip(lo, r["bbox_min"])]
            hi = r["bbox_max"] if hi is None else [max(a, b) for a, b in zip(hi, r["bbox_max"])]
    classes: dict = {}
    for r in recs:
        classes[r["cls"]] = classes.get(r["cls"], 0) + 1
    try:
        unit = str(rt.units.SystemType)  # [verify] units.SystemType
    except Exception:
        unit = None
    return {"path": path, "ok": bool(ok), "nodes": [r["name"] for r in recs], "count": len(recs),
            "classes": classes,
            "materials": sorted({f"{r['material']} ({r['material_class']})" for r in recs if r.get("material")}),
            "bbox_min": lo, "bbox_max": hi,
            "size": [b - a for a, b in zip(lo, hi)] if lo and hi else None,
            "system_unit": unit}


def import_any(path, **opts) -> dict:
    """Import any supported file (suffix picks the plugin). opts: using (importer class name).
    A .max is merged with mergeMAXFile #autoRenameDups #renameMtlDups #neverReparent quiet:true:
    no duplicate or reparent prompt, and an incoming "Wood" never replaces the scene's "Wood". .max-only opts: ignore_file_units (bool, 2027.1),
    layers (list of layer names, 2027), merge_nodes_by_layer (bool, 2027). Check units first:
    a Units Mismatch dialog blocks a live session and a script cannot close it."""
    rt = _rt()
    path = os.fspath(path)
    if not rt.doesFileExist(path):
        raise FileNotFoundError(path)
    before = _handles(rt)
    if path.lower().endswith(".max"):
        kw = {"quiet": True}
        if opts.get("ignore_file_units") is not None:
            kw["ignoreFileUnits"] = bool(opts["ignore_file_units"])
        if opts.get("layers"):
            kw["layers"] = list(opts["layers"])
        if opts.get("merge_nodes_by_layer") is not None:
            kw["mergeNodesByLayer"] = bool(opts["merge_nodes_by_layer"])
        ok = rt.mergeMAXFile(path, rt.Name("autoRenameDups"), rt.Name("renameMtlDups"),
                             rt.Name("neverReparent"), **kw)
    else:
        kw = {"quiet": True}
        if opts.get("using"):
            kw["using"] = getattr(rt, opts["using"])
        ok = rt.importFile(path, rt.Name("noPrompt"), **kw)
    after = _handles(rt)
    new = [o for h, o in after.items() if h not in before]
    return _report_nodes(rt, new, path, ok=bool(ok) if ok is not None else bool(new))


def _export(path, selected, using=None) -> dict:
    rt = _rt()
    path = next_free(os.fspath(path))
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    nodes = list(rt.selection) if selected else list(rt.objects)  # [verify] selection, objects
    kw = {"selectedOnly": bool(selected)}
    if using:
        kw["using"] = getattr(rt, using)
    ok = rt.exportFile(path, rt.Name("noPrompt"), **kw)
    rep = _report_nodes(rt, nodes, path, ok=bool(ok) if ok is not None else os.path.exists(path))
    rep["bytes"] = os.path.getsize(path) if os.path.exists(path) else 0
    rep["ok"] = rep["ok"] and rep["bytes"] > 0
    return rep


def export_fbx(path, preset=None, selected=False) -> dict:
    """FBX export. preset: dict of FBX exporter parameter -> value, applied before export
    (FBXExporterSetParam is [verify]; FBXExporterGetParam is in the 2027 what's new page).
    Not settable through mcp-safe if the exporter keeps them in INI files (setINISetting is blocked)."""
    rt = _rt()
    applied = {}
    if preset:  # the exporter's parameters exist only once the plug-in is loaded
        try:
            loaded = rt.pluginManager.loadClass(rt.FBXEXP)  # [verify] pluginManager.loadClass, FBXEXP
        except Exception as exc:
            raise RuntimeError(f"FBX exporter plug-in could not be loaded: {exc}") from exc
        if loaded is False:
            raise RuntimeError("FBX exporter plug-in could not be loaded")
    for key, value in (preset or {}).items():
        rt.FBXExporterSetParam(key, value)  # [verify] FBXExporterSetParam
        applied[key] = value
    rep = _export(path, selected, using="FBXEXP")
    rep["preset"] = applied
    return rep


def export_gltf(path, selected=False) -> dict:
    """glTF 2.0 (.glb or .gltf) through the 2027.3 Khronos exporter, picked by suffix.
    Run gltf_precheck first: flattened hierarchy, no vertex colors, two-level material limit."""
    if not os.fspath(path).lower().endswith((".glb", ".gltf")):
        raise ValueError("glTF path must end in .glb or .gltf")
    return _export(path, selected)


def export_usd(path, selected=False) -> dict:
    """USD (.usd, .usda, .usdc, .usdz export only) picked by suffix; options [verify]."""
    if not os.fspath(path).lower().endswith((".usd", ".usda", ".usdc", ".usdz")):
        raise ValueError("USD path must end in .usd, .usda, .usdc or .usdz")
    return _export(path, selected)


def gltf_precheck(data=None) -> list:
    """Pure over collect() data: limits from gltf-export-2027.md (duplicate names get _1 suffixes,
    hierarchy flattened, multi/sub-object nesting past two levels, glTF Material works best)."""
    d = data if data is not None else _stats.collect()
    out, seen = [], {}
    for n in d.get("nodes", []):
        seen[n.get("name")] = seen.get(n.get("name"), 0) + 1
        if n.get("superclass") == _stats.GEOMETRY:
            mc = (n.get("material_class") or "").lower()
            if mc and "gltf" not in mc:
                out.append({"severity": "info", "rule": "gltf", "node": n.get("name"),
                            "message": f"{n.get('material_class')}: glTF Material exports best"})
            if n.get("parent"):
                out.append({"severity": "info", "rule": "gltf", "node": n.get("name"),
                            "message": "has a parent: hierarchies may be flattened on export"})
    for name, c in seen.items():
        if c > 1:
            out.append({"severity": "warn", "rule": "gltf", "node": name,
                        "message": f"{c} nodes share the name: exporter adds _1, _2 suffixes"})
    files = {}
    for b in d.get("scene", {}).get("bitmaps", []):
        stem = os.path.splitext(os.path.basename(b["file"]))[0].lower()
        files.setdefault(stem, set()).add(b["file"].lower())
    for stem, fs in files.items():
        if len(fs) > 1:
            out.append({"severity": "warn", "rule": "gltf", "node": None,
                        "message": f"bitmaps with the same name and different type ({sorted(fs)}): only one exports"})
    return out
