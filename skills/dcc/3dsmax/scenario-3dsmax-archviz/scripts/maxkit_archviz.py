# channel: batch | bridge | handoff (prepended to a chunk by archviz_plan.chunk(), then max_wrap.wrap); mcp-safe uses scripts/mxs/archviz_audit.ms
# checked against pymxs-renderer-2027 doc (renderers, renderSceneDialog), archviz digests 1 to 4
"""Archviz helpers that run inside 3ds Max (pymxs, main thread only).

Read-only:  units_info, camera_report, scatter_inventory, pivot_base_report, spline_closed_report,
            anim_report, prop_dump
Changing:   make_camera, set_pivot_base, shadow_only, set_anim_output, anima_layer_prep
Every changing function must run inside the max_wrap undo record or its own pymxs.undo block.
max_wrap only inlines its own maxkit modules, so archviz_plan.chunk() pastes this file above the chunk:
call these functions by bare name (camera_report(), not ak.camera_report()).

Plugin property names (Forest Pack, RailClone, Chaos Scatter, Corona, V-Ray, Physical Camera) are not in
the saved docs. This module never guesses one silently: it looks names up with getPropNames and reports
which candidate matched, so the first run in a session tells the agent the real names.
"""
import math
import time

import pymxs

rt = pymxs.runtime

# Class names as printed by classOf. Only ChaosScatter appears in a doc (as a Create panel button name).
SCATTER_CLASSES = {
    "Forest_Pro": "forestpack",      # [verify]
    "Forest_Lite": "forestpack",     # [verify]
    "RailClone_Pro": "railclone",    # [verify]
    "RailClone_Lite": "railclone",   # [verify]
    "ChaosScatter": "chaosscatter",  # [verify] class string; button name from vray7-chaos-scatter doc
    "VRayProxy": "proxy",            # name in vray7-chaos-cosmos-browser doc
    "CProxy": "proxy",               # [verify] Corona proxy class
}

CAMERA_CANDIDATES = {
    "focal_mm": ("focal_length_mm", "focal_length", "focalLength"),          # [verify] all
    "film_mm": ("film_width_mm", "film_width", "filmWidth"),                 # [verify] all
    "auto_vtilt": ("auto_vertical_tilt_correction", "autoVerticalTilt",
                   "auto_vertical_tilt", "vertical_tilt_auto"),               # [verify] all
    "fov": ("fov",),                                                          # [verify]
    "targeted": ("targeted",),                                                # [verify]
    "use_dof": ("use_dof", "dof_enabled", "useDOF"),                          # [verify] all
    "f_number": ("f_number", "fnumber", "f_stop"),                            # [verify] all
}

UNIT_TO_M = {"inches": 0.0254, "feet": 0.3048, "miles": 1609.344, "millimeters": 0.001,
             "centimeters": 0.01, "meters": 1.0, "kilometers": 1000.0}


def units_info():
    system = str(rt.units.SystemType).lower()  # [verify] units.SystemType value spelling
    scale = float(getattr(rt.units, "SystemScale", 1.0))  # [verify] SystemScale
    return {"system_type": system, "system_scale": scale, "m_per_unit": UNIT_TO_M.get(system, 1.0) * scale}


def _m_per_unit():
    return units_info()["m_per_unit"]


def prop_dump(obj):
    """Property names of a node or its base object, to learn plugin names in this session."""
    names = [str(n) for n in rt.getPropNames(obj)]
    return sorted(names)


def _find(obj, key):
    names = {n.lower(): n for n in prop_dump(obj)}
    for cand in CAMERA_CANDIDATES.get(key, (key,)):
        if cand.lower() in names:
            return names[cand.lower()]
    return None


def _get(obj, prop):
    return rt.getProperty(obj, rt.name(prop))  # [verify] getProperty


def _set(obj, prop, value):
    rt.setProperty(obj, rt.name(prop), value)  # [verify] setProperty


def camera_report():
    """One row per camera (targets excluded): class, height in m, lens values found and the names used."""
    m = _m_per_unit()
    rows = []
    for cam in rt.cameras:  # [verify] cameras collection
        if rt.superClassOf(cam) != rt.camera:  # [verify] superClassOf; the collection also holds targets
            continue
        row = {"name": str(cam.name), "class": str(rt.classOf(cam)),
               "height_m": round(float(cam.pos.z) * m, 3), "props": {}}
        for key in CAMERA_CANDIDATES:
            p = _find(cam, key)
            if p:
                try:
                    row["props"][key] = {"name": p, "value": str(_get(cam, p))}
                except Exception as exc:  # plugin props can throw on read
                    row["props"][key] = {"name": p, "error": str(exc)}
            else:
                row["props"][key] = None
        rows.append(row)
    return rows


def _look_at(pos, target):
    """Matrix3 for a camera at pos looking at target (camera looks down local -Z, world Z up)."""
    z = rt.normalize(pos - target)
    up = rt.point3(0, 0, 1)
    if abs(rt.dot(z, up)) > 0.999:  # straight down: pick world Y as up
        up = rt.point3(0, 1, 0)
    x = rt.normalize(rt.cross(up, z))
    y = rt.cross(z, x)
    return rt.matrix3(x, y, z, pos)


def make_camera(name, pos_m, target_m, focal_mm, film_mm=36.0, auto_vtilt=True, cls_name="Physical"):
    """Create a free camera from metric coordinates. Returns the report row plus the props it could not set.

    cls_name: "Physical" (3ds Max Physical Camera, class name [verify]); falls back to Freecamera.
    Renderer-native cameras (VRayPhysicalCamera, CoronaCam) are created only when cls_name names them [verify].
    """
    m = _m_per_unit()
    p = rt.point3(*(v / m for v in pos_m))
    t = rt.point3(*(v / m for v in target_m))
    cls = getattr(rt, cls_name, None) or rt.Freecamera
    cam = cls()  # Freecamera in api-names; Physical camera class [verify]
    cam.name = name
    unset = []
    tp = _find(cam, "targeted")
    if tp:
        _set(cam, tp, False)
    cam.transform = _look_at(p, t)
    for key, value in (("focal_mm", float(focal_mm)), ("film_mm", float(film_mm)), ("auto_vtilt", bool(auto_vtilt))):
        prop = _find(cam, key)
        if prop:
            _set(cam, prop, value)
        else:
            unset.append(key)
    if "focal_mm" in unset:  # Freecamera has only fov: derive it from focal and film width
        fov = _find(cam, "fov")
        if fov:
            _set(cam, fov, 2.0 * math.degrees(math.atan(film_mm / (2.0 * focal_mm))))
            unset.remove("focal_mm")
    return {"name": name, "class": str(rt.classOf(cam)), "unset": unset}


def scatter_inventory(dump_props=False):
    """Scatter, parametric and proxy objects by family, with layer and hidden state."""
    rows = []
    for obj in rt.objects:
        cls = str(rt.classOf(obj))
        fam = SCATTER_CLASSES.get(cls)
        if not fam:
            continue
        row = {"name": str(obj.name), "class": cls, "family": fam,
               "layer": str(obj.layer.name), "hidden": bool(obj.isHidden)}  # [verify] layer, isHidden
        if dump_props:
            row["props"] = prop_dump(obj)
        rows.append(row)
    return rows


def pivot_base_report(nodes, tol_m=0.01):
    """Scatter sources need the pivot at the base center (8s2gF4vb6yk 00:02:16; mbi-7pTItcU 00:53:06)."""
    m = _m_per_unit()
    bad = []
    for n in nodes:
        lo, hi = n.min, n.max  # world bounding box [verify] node.min/node.max
        cx, cy = (lo.x + hi.x) / 2.0, (lo.y + hi.y) / 2.0
        dz = (n.pivot.z - lo.z) * m
        dxy = (((n.pivot.x - cx) ** 2 + (n.pivot.y - cy) ** 2) ** 0.5) * m
        if abs(dz) > tol_m or dxy > tol_m:
            bad.append({"name": str(n.name), "pivot_above_base_m": round(dz, 3), "pivot_off_center_m": round(dxy, 3)})
    return bad


def set_pivot_base(nodes):
    for n in nodes:
        lo, hi = n.min, n.max  # [verify]
        n.pivot = rt.point3((lo.x + hi.x) / 2.0, (lo.y + hi.y) / 2.0, lo.z)  # [verify] pivot assignment
    return len(nodes)


def spline_closed_report(shapes):
    """Guide and area splines must be closed (8s2gF4vb6yk 00:04:38). Reports open sub-splines."""
    out = []
    for s in shapes:
        try:
            count = int(rt.numSplines(s))  # [verify] numSplines
            open_ids = [i for i in range(1, count + 1) if not rt.isClosed(s, i)]  # isClosed in api-names
        except Exception as exc:  # non-editable shapes may need an Edit Spline first
            out.append({"name": str(s.name), "error": str(exc)})
            continue
        if open_ids:
            out.append({"name": str(s.name), "open_splines": open_ids})
    return out


def shadow_only(nodes):
    """Surroundings that only cast shadows (iIYYzosZ1Mo 00:08:38). Renderer support [verify] per renderer."""
    for n in nodes:
        n.primaryVisibility = False  # [verify] Object Properties > Visible to Camera
        n.castShadows = True         # [verify]
    return [str(n.name) for n in nodes]


def anim_report():
    r = rt.animationRange  # [verify]
    return {"fps": float(rt.frameRate), "range": [int(r.start.frame), int(r.end.frame)],  # [verify] frameRate, .frame
            "rendTimeType": int(rt.rendTimeType), "rendSaveFile": bool(rt.rendSaveFile),  # [verify] both
            "rendOutputFilename": str(rt.rendOutputFilename),  # [verify]
            "size": [int(rt.renderWidth), int(rt.renderHeight)],  # [verify] both
            "renderer": str(rt.classOf(rt.renderers.current))}


def set_anim_output(fps, first, last, out_path, width=None, height=None):
    """fps, range and numbered output. Close Render Setup first (pymxs-renderer-2027 doc)."""
    if rt.renderSceneDialog.isOpen():
        rt.renderSceneDialog.close()  # [verify] close
    rt.frameRate = int(fps)  # [verify]
    rt.animationRange = rt.interval(first, last)  # [verify] interval
    rt.rendTimeType = 3          # range, per ZHCVMQeWPEg agent notes [verify] value
    rt.rendStart = first         # [verify]
    rt.rendEnd = last            # [verify]
    rt.rendSaveFile = True  # [verify]
    rt.rendOutputFilename = out_path  # [verify]
    if width and height:
        rt.renderWidth = int(width)  # [verify]
        rt.renderHeight = int(height)  # [verify]
    return anim_report()


def time_test_frame(camera_name, frame, out_path):
    """Render one frame to a new file and return seconds (feed archviz_plan.render_budget)."""
    cam = rt.getNodeByName(camera_name)
    t0 = time.perf_counter()
    rt.render(camera=cam, frame=frame, outputFile=out_path, vfb=False)  # [verify] camera/frame/vfb args
    return round(time.perf_counter() - t0, 2)


def anima_layer_prep(keep_layers, fps=30, layer_name="Anima"):
    """Anima round trip prep (ZHCVMQeWPEg 00:04:06, 00:06:36): layer, fps 30, hide all but kept layers."""
    lay = rt.LayerManager.getLayerFromName(layer_name)  # [verify] getLayerFromName
    if lay is None:
        lay = rt.LayerManager.newLayerFromName(layer_name)  # [verify]
    keep = set(keep_layers) | {layer_name}
    hidden = []
    for i in range(rt.LayerManager.count):  # [verify] count and getLayer(0-based)
        L = rt.LayerManager.getLayer(i)
        if str(L.name) not in keep:
            L.on = False  # [verify] layer.on
            hidden.append(str(L.name))
    rt.frameRate = int(fps)  # [verify]
    return {"layer": layer_name, "hidden_layers": hidden, "fps": fps}
