"""maxkit_render: in-Max helpers for lighting and render work (pymxs, main thread only).

channel: batch | bridge | handoff (inline with max_wrap.wrap(..., kit=[...]); for mcp-safe use mxs/render_audit.ms)
status: not yet run in 3ds Max; checked against scripting-pipeline__pymxs-renderer-2027.md,
scripting-pipeline__maxscript-bitmap-values-2027.md and the lighting-rendering digests.

Stance encoded here: read before you write. Renderer property names differ between Arnold,
V-Ray and Corona builds and none is confirmed by a saved doc, so every setter only touches
names that `getPropNames` returned on this scene's renderer, and dry_run is the default.

    renderer_info()                      -> {class, family, production_class}
    prop_dump(obj, keywords=None)        -> {name: str(value)} for matching property names
    set_props(obj, mapping, dry_run=True)-> {set, missing, before, after}
    render_elements()                    -> [{index, class, name}]
    add_element(class_name, dry_run=True)-> {added, class, error}
    lights_report(keywords=None)         -> [{name, class, props}]
    color_report()                       -> {displays, views, file_io_spaces, interface_props}
    bitmap_color_spaces(limit=2000)      -> [{file, color_space, source, status, data_guess}]
    output_settings()                    -> {width, height, output_file, save_file}
    resolve(obj, concept)                -> first candidate property name that exists, or None
    test_render(path, camera=None, size=None) -> {path, seconds, size}

Inline by prepending this file's text to the chunk passed to max_wrap.wrap (no __future__
import here on purpose, so the concatenated chunk still compiles).
"""
import os
import time

from pymxs import runtime as rt

# Keywords that find the settings an agent usually needs, across the three renderers.
SETTING_KEYWORDS = (
    "noise", "sample", "subdiv", "denois", "override", "limit", "time", "filter",
    "threshold", "adaptiv", "depth", "light", "gi_", "secondary", "primary", "lock",
    "exposure", "tone", "progressive", "bucket", "clamp", "intensity",
)

# Candidate property names per concept and renderer family, taken only from expert notes that
# mark them [verify]; no saved doc confirms them. resolve() returns a name only when getPropNames
# found it on this scene's object. A concept with no candidate (Corona override, time limits,
# Arnold light samples) is found with prop_dump(obj, keywords) and confirmed by reading values.
CANDIDATES = {  # [verify] every name in this table
    "noise_target": {"vray": ["progressive_noise_threshold"], "corona": ["progressive_noiseLevelLimit"]},
    "override_on": {"vray": ["options_overrideMtl_on"]},
    "override_mtl": {"vray": ["options_overrideMtl_mtl"]},
    "dont_render_image": {"vray": ["options_dontRenderImage"]},
    "light_cache_subdivs": {"vray": ["lightcache_subdivs"]},
    "aa_samples": {"arnold": ["AA_samples"]},
    "diffuse_samples": {"arnold": ["GI_diffuse_samples"]},
    "specular_samples": {"arnold": ["GI_specular_samples"]},
    "transmission_samples": {"arnold": ["GI_transmission_samples"]},
    "sss_samples": {"arnold": ["GI_sss_samples"]},
    "volume_samples": {"arnold": ["GI_volume_samples"]},
    "diffuse_depth": {"arnold": ["GI_diffuse_depth"]},
    "specular_depth": {"arnold": ["GI_specular_depth"]},
}

DATA_MAP_HINTS = ("normal", "nrm", "rough", "gloss", "metal", "height", "disp", "bump",
                  "ao", "occlusion", "opacity", "mask", "spec")


def _names(obj):
    try:
        return [str(n) for n in rt.getPropNames(obj)]
    except Exception:
        return []


def resolve(obj, concept, family=None):
    """First candidate name for a concept that really exists on obj (case-insensitive)."""
    family = family or renderer_info()["family"]
    existing = {n.lower(): n for n in _names(obj)}
    for cand in CANDIDATES.get(concept, {}).get(family, []):
        if cand.lower() in existing:
            return existing[cand.lower()]
    return None


def renderer_info():
    """Identify the production renderer without needing any renderer class name."""
    r = rt.renderers.current
    cls = str(rt.classOf(r))
    low = cls.lower()
    if "arnold" in low:
        family = "arnold"
    elif "corona" in low:
        family = "corona"
    elif "v_ray" in low or "vray" in low:
        family = "vray"
    elif "scanline" in low:
        family = "scanline"
    else:
        family = "other"
    return {"class": cls, "family": family,
            "production_class": str(rt.classOf(rt.renderers.production))}


def prop_dump(obj, keywords=None):
    """Names and current values; filter by substrings (case-insensitive) when keywords given."""
    out = {}
    keys = tuple(k.lower() for k in keywords) if keywords else None
    for name in _names(obj):
        if keys and not any(k in name.lower() for k in keys):
            continue
        try:
            out[name] = str(getattr(obj, name))
        except Exception as exc:  # some properties are write-only or need a context
            out[name] = f"<unreadable: {exc}>"
    return out


def set_props(obj, mapping, dry_run=True):
    """Set only properties that exist on obj. Never guess: unknown names come back in `missing`."""
    existing = {n.lower(): n for n in _names(obj)}
    report = {"set": [], "missing": [], "before": {}, "after": {}}
    for name, value in mapping.items():
        real = existing.get(name.lower())
        if real is None:
            report["missing"].append(name)
            continue
        report["before"][real] = str(getattr(obj, real))
        if not dry_run:
            setattr(obj, real, value)
            report["after"][real] = str(getattr(obj, real))
        report["set"].append(real)
    return report


def _element_mgr():
    return rt.maxOps.GetCurRenderElementMgr()  # [verify] research report section 8, 2022 help


def render_elements():
    mgr = _element_mgr()
    out = []
    for i in range(mgr.NumRenderElements()):  # [verify] method name
        el = mgr.GetRenderElement(i)  # [verify] method name and 0-based index
        out.append({"index": i, "class": str(rt.classOf(el)),
                    "name": str(getattr(el, "elementName", el))})  # [verify] elementName
    return out


def add_element(class_name, dry_run=True):
    """Add one render element by class name if the class exists in this install.

    Arnold AOVs are not render elements: use the Arnold AOV manager (GUI) or a MAXtoA API."""
    if not hasattr(rt, class_name):
        return {"added": False, "class": class_name, "error": "class not in this install"}
    if any(e["class"].lower() == class_name.lower() for e in render_elements()):
        return {"added": False, "class": class_name, "error": "already present"}
    if dry_run:
        return {"added": False, "class": class_name, "error": "dry_run"}
    el = getattr(rt, class_name)()
    _element_mgr().AddRenderElement(el)  # [verify] method name
    return {"added": True, "class": class_name, "error": None}


def lights_report(keywords=("on", "enabled", "multiplier", "intensity", "power", "color",
                            "temperature", "kelvin", "invisible", "visible", "size",
                            "sampl", "exposure", "mode")):
    out = []
    for node in rt.lights:  # includes targets on some classes; filter by superclass if noisy
        out.append({"name": str(node.name), "class": str(rt.classOf(node)),
                    "props": prop_dump(node, keywords)})
    return out


def color_report():
    """OCIO state. Only the three list functions are documented; the mode property is not."""
    mgr = rt.ColorPipelineMgr
    rep = {"displays": [], "views": {}, "file_io_spaces": [], "interface_props": {}}
    try:
        rep["displays"] = [str(d) for d in mgr.GetDisplayList()]
        for d in rep["displays"]:
            rep["views"][d] = [str(v) for v in mgr.GetViewList(d)]
        rep["file_io_spaces"] = [str(s) for s in mgr.GetFileIOColorSpaceList()]
    except Exception as exc:
        rep["error"] = str(exc)
    rep["interface_props"] = prop_dump(mgr)  # [verify] getPropNames on a core interface
    return rep


def bitmap_color_spaces(limit=2000):
    """Read-only list of bitmap color spaces, with a guess of which files hold data."""
    out = []
    for tex in list(rt.getClassInstances(rt.BitmapTexture))[:limit]:  # [verify] getClassInstances
        fname = str(getattr(tex, "filename", ""))
        try:
            bmp = tex.bitmap  # loads the file; missing files raise
            cs, src, status = str(bmp.colorSpace), str(bmp.colorSpaceSource), str(bmp.colorSpaceStatus)
        except Exception as exc:
            cs, src, status = "", "", f"<unreadable: {exc}>"
        base = fname.replace("\\", "/").rsplit("/", 1)[-1].lower()
        data_guess = any(h in base for h in DATA_MAP_HINTS)
        out.append({"file": fname, "color_space": cs, "source": src, "status": status,
                    "data_guess": data_guess})
    return out


def output_settings():
    return {"width": int(rt.renderWidth), "height": int(rt.renderHeight),  # [verify] globals
            "output_file": str(rt.rendOutputFilename),  # [verify]
            "save_file": bool(rt.rendSaveFile)}  # [verify]


def test_render(path, camera=None, size=None):
    """Render one frame to a new file and time it. Close Render Setup first (pymxs renderer doc).

    path: a new file name (never an existing user file). size: (w, h) or None for scene size.
    V-Ray layers and Corona CXR are not written by this route: only the beauty bitmap."""
    if os.path.exists(path):
        raise FileExistsError(f"{path} exists: pass a new versioned name")
    if rt.renderSceneDialog.isOpen():
        rt.renderSceneDialog.close()  # [verify] close() is in the struct help, not the saved page
    kwargs = {"outputFile": path, "vfb": False}
    if camera is not None:
        kwargs["camera"] = camera
    if size is not None:
        kwargs["outputSize"] = rt.Point2(int(size[0]), int(size[1]))
    t0 = time.perf_counter()
    rt.render(**kwargs)
    return {"path": path, "seconds": round(time.perf_counter() - t0, 2),
            "size": list(size) if size else None}
