"""maxkit_materials: look-dev helpers that run INSIDE 3ds Max (pymxs, main thread only).

channel: batch | bridge | handoff (max_wrap kit=["maxkit_materials"], kit_dirs=[this folder]; mcp-safe uses mxs/materials_audit.ms)
checked against scripting-pipeline__maxscript-bitmap-values-2027.md,
        uv-baking-texturing__maxscript-baketotexture-utilityplugin-2027.md, scripting-pipeline__pymxs-using-2027.md

Stance on API names: only PhysicalMaterial, .base_color_map, Bitmaptexture filename:, openBitmap colorSpace:,
the read-only bitmap .colorSpace* properties, ColorPipelineMgr.GetFileIOColorSpaceList, uvwmap and
addModifier come from the saved docs. Every other class or property is RESOLVED AT RUN TIME
(class lookup by name fragment, property lookup by isProperty / getPropNames) and every resolution is
written to the result, so the first real run turns each [verify] into a known name.

Functions (all return plain dicts or lists, never raise on a missing property):
    discover(obj)                         -> sorted property names
    find_class(fragment, kind)            -> class value or None
    colorspace_for(role)                  -> OCIO color space name chosen for "color" or "data"
    load_texture(path, color_role)        -> (Bitmaptexture, report)
    build_material(target, maps, name)    -> (material, report); target in openpbr, physical, gltf, vray, corona
    box_map(node, size_cm)                -> report; UVW Map box at a real-world size
    general_feeling(groups, target)       -> report; one flat material per name group
    lookdev_rig(ball_radius_cm)           -> report; ball, floor, camera named LKD_*
    audit_textures()                      -> findings on texture color spaces and file tags
    audit_materials()                     -> findings on classes, debug red, pure white/black, empty layers
    audit_multisub(node)                  -> findings on face IDs without sub-materials
"""
# No "from __future__" import: max_wrap inlines this file into one generated script.
import fnmatch
import os
import re

from pymxs import runtime as rt

# --------------------------------------------------------------------------- generic

def _s(x) -> str:
    return str(x)


def discover(obj) -> list[str]:
    try:
        return sorted(_s(n) for n in rt.getPropNames(obj))  # [verify] getPropNames
    except Exception:
        return []


def _has(obj, name: str) -> bool:
    try:
        return bool(rt.isProperty(obj, name))  # [verify] isProperty
    except Exception:
        return False


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def find_prop(obj, candidates=(), tokens=(), want_map=False) -> tuple[str | None, str]:
    """Explicit candidates first, then the shortest property whose name holds every token.
    Returns (name, how) with how in explicit, fuzzy, none."""
    for c in candidates:
        if _has(obj, c):
            return c, "explicit"
    if not tokens:
        return None, "none"
    hits = []
    for p in discover(obj):
        n = _norm(p)
        if all(t in n for t in tokens):
            is_map = any(k in n for k in ("map", "shader", "texmap", "tex"))
            if is_map == want_map:
                hits.append(p)
    if hits:
        return min(hits, key=len), "fuzzy"
    return None, "none"


def set_prop(obj, name: str, value) -> bool:
    try:
        rt.setProperty(obj, name, value)  # [verify] setProperty
        return True
    except Exception:
        return False


def find_class(fragment: str, kind: str = "material"):
    """kind: material or texturemap. Returns the first class whose name contains fragment."""
    pool = rt.material.classes if kind == "material" else rt.textureMap.classes  # [verify] .classes
    frag = _norm(fragment)
    pool = list(pool)
    for c in pool:  # exact first, so "vraymtl" never returns VRayMtlWrapper
        if _norm(_s(c)) == frag:
            return c
    for c in pool:
        if frag in _norm(_s(c)):
            return c
    return None


# --------------------------------------------------------------------------- color space

_DATA_HINTS = ("raw", "data", "non-color", "utility")
_COLOR_HINTS = ("srgb",)


def colorspace_for(color_role: str) -> str | None:
    """Pick a name from the active OCIO config; never hard-code it (configs differ)."""
    try:
        names = [_s(n) for n in rt.ColorPipelineMgr.GetFileIOColorSpaceList()]
    except Exception:
        return None
    if color_role == "data":
        for h in _DATA_HINTS:
            for n in names:
                if h in n.lower():
                    return n
        return None
    for n in names:
        low = n.lower()
        if "srgb" in low and "lin" not in low and "scene" not in low:
            return n
    return None


def load_texture(path: str, color_role: str):
    """color_role: color or data. Requests the color space at load time (OCIO) and gamma 1.0 for
    data (gamma workflow); each keyword is ignored by the mode it does not belong to (doc)."""
    rep = {"path": path, "color_role": color_role}
    cs = colorspace_for(color_role)
    kw = {}
    if cs:
        kw["colorSpace"] = cs
    if color_role == "data":
        kw["gamma"] = 1.0
    bm = rt.openBitmap(path, **kw)
    if bm is None:
        rep["error"] = "file missing"
        return None, rep
    tex = rt.Bitmaptexture(filename=path)
    tex.name = os.path.splitext(os.path.basename(path))[0]
    try:
        tex.bitmap = bm  # [verify] Bitmaptexture .bitmap
        rep["bitmap_assigned"] = True
    except Exception as e:  # keep going; the audit below reports what Max decided
        rep["bitmap_assigned"] = f"failed: {e}"
    rep["requested"] = cs
    try:
        b = tex.bitmap  # [verify]
        rep["colorSpace"] = _s(b.colorSpace)
        rep["colorSpaceSource"] = _s(b.colorSpaceSource)
        rep["colorSpaceStatus"] = _s(b.colorSpaceStatus)
    except Exception as e:
        rep["colorSpace"] = f"unreadable: {e}"
    return tex, rep


# --------------------------------------------------------------------------- build

# role -> per target: (explicit candidates, fuzzy tokens). Only physical base_color_map is doc-confirmed.
SLOTS = {
    "openpbr": {
        "base_color": (("base_color_map", "base_color_shader"), ("base", "color")),
        "roughness": (("specular_roughness_map", "specular_roughness_shader"), ("specular", "roughness")),
        "metalness": (("base_metalness_map", "base_metalness_shader"), ("metalness",)),
        "normal": (("geometry_normal_map", "geometry_normal_shader", "normal_map"), ("normal",)),
        "opacity": (("geometry_opacity_map", "opacity_map"), ("opacity",)),
        "emission": (("emission_color_map",), ("emission", "color")),
    },
    "physical": {
        "base_color": (("base_color_map",), ("base", "color")),
        "roughness": (("roughness_map",), ("roughness",)),
        "metalness": (("metalness_map",), ("metalness",)),
        "normal": (("bump_map",), ("bump",)),
        "opacity": (("cutout_map", "opacity_map"), ("cutout",)),
        "emission": (("emit_color_map",), ("emi", "color")),
    },
    "gltf": {
        "base_color": ((), ("base", "color")),
        "roughness": ((), ("roughness",)),
        "metalness": ((), ("metal",)),
        "normal": ((), ("normal",)),
        "opacity": ((), ("alpha",)),
        "emission": ((), ("emissi",)),
    },
    "vray": {
        "base_color": (("texmap_diffuse",), ("diffuse",)),
        "roughness": (("texmap_reflectionGlossiness",), ("reflection", "gloss")),
        "gloss": (("texmap_reflectionGlossiness",), ("reflection", "gloss")),
        "metalness": (("texmap_metalness",), ("metalness",)),
        "normal": (("texmap_bump",), ("bump",)),
        "opacity": (("texmap_opacity",), ("opacity",)),
    },
    "corona": {
        "base_color": (("baseTexmap",), ("base",)),
        "roughness": (("baseRoughnessTexmap",), ("base", "rough")),
        "gloss": (("baseRoughnessTexmap",), ("base", "rough")),
        "metalness": (("metalnessTexmap",), ("metalness",)),
        "normal": (("baseBumpTexmap",), ("base", "bump")),
        "opacity": (("opacityTexmap",), ("opacity",)),
    },
}

MATERIAL_CLASS = {  # name fragments, resolved by find_class
    "openpbr": "openpbr", "physical": "physicalmaterial", "gltf": "gltf",
    "vray": "vraymtl", "corona": "coronaphysicalmtl",
}
NORMAL_NODE = {  # texture-map class fragments for the normal wrapper; glTF takes the bitmap directly
    "openpbr": "normalbump", "physical": "normalbump", "vray": "vraynormalmap", "corona": "coronanormal",
}


def _new_material(target: str, name: str):
    cls = rt.PhysicalMaterial if target == "physical" else find_class(MATERIAL_CLASS[target])
    if cls is None:
        return None
    m = cls()
    m.name = name
    return m


def build_material(target: str, maps: dict, name: str, flip_green: bool = False):
    """maps: role -> file path, roles from pbr_set.scan (base_color, roughness or gloss, metalness,
    normal, opacity, emission). AO and height are not wired here on purpose (see SKILL.md)."""
    rep = {"target": target, "name": name, "slots": {}, "warnings": []}
    m = _new_material(target, name)
    if m is None:
        rep["error"] = f"material class for {target} not found (renderer plugin missing?)"
        return None, rep
    rep["class"] = _s(rt.classOf(m))
    table = SLOTS[target]
    for role, path in maps.items():
        if role in ("ao", "height", "orm"):
            rep["warnings"].append(f"{role} not wired: decide per SKILL.md")
            continue
        color_role = "color" if role in ("base_color", "emission") else "data"
        tex, trep = load_texture(path, color_role)
        rep["slots"].setdefault(role, {})["texture"] = trep
        if tex is None:
            continue
        slot_role = role
        if role == "gloss" and target in ("openpbr", "physical", "gltf"):
            ok = set_prop(tex.output, "invert", True)  # [verify] Bitmaptexture .output.invert
            rep["warnings"].append(f"gloss map inverted for a roughness slot: {'done' if ok else 'FAILED, fix by hand'}")
            slot_role = "roughness"
        if role == "roughness" and target == "vray":
            p, how = find_prop(m, ("brdf_useRoughness",), ("use", "roughness"))
            rep["warnings"].append(f"VRayMtl roughness mode via {p} ({how}): {'set' if p and set_prop(m, p, True) else 'NOT SET'}")
        if target == "corona":
            p, how = find_prop(m, ("roughnessMode",), ("roughness", "mode"))
            rep["warnings"].append(f"Corona roughness mode property {p} ({how}); set it to match the {role} map by hand if not set")
        if role == "normal" and target in NORMAL_NODE:
            ncls = find_class(NORMAL_NODE[target], kind="texturemap")
            if ncls is None:
                rep["warnings"].append("normal wrapper class not found: normal left unwired")
                continue
            node = ncls()
            p, how = find_prop(node, ("normal_map", "normalMap"), ("normal",), want_map=True)
            if not (p and set_prop(node, p, tex)):
                rep["warnings"].append("could not plug the bitmap into the normal node")
                continue
            if flip_green:
                fp, _ = find_prop(node, ("flipgreen", "flipGreen", "flip_green"), ("flip", "green"))
                rep["warnings"].append(f"flip green via {fp}: {'set' if fp and set_prop(node, fp, True) else 'NOT SET'}")
            tex = node
        cand, tokens = table.get(slot_role, ((), ()))
        p, how = find_prop(m, cand, tokens, want_map=True)
        ok = bool(p) and set_prop(m, p, tex)
        rep["slots"][role].update({"property": p, "resolved": how, "connected": ok})
        if not ok:
            rep["warnings"].append(f"{role}: no map slot found on {rep['class']}")
        if role == "metalness":
            vp, _ = find_prop(m, ("base_metalness", "metalness"), ("metalness",), want_map=False)
            if vp:
                set_prop(m, vp, 1.0)  # the map does the switching; 0/1 values in the map
    return m, rep


def _unit_scale_to_cm() -> float:
    u = _s(rt.units.SystemType).lower()  # [verify] units.SystemType
    return {"millimeters": 10.0, "centimeters": 1.0, "meters": 0.01, "inches": 1 / 2.54,
            "feet": 1 / 30.48, "kilometers": 1e-5}.get(u.strip("#"), 1.0)


def box_map(node, size_cm: float) -> dict:
    """Box UVW Map whose box equals one texture repeat in real-world cm. Adds; never removes."""
    k = _unit_scale_to_cm()
    mod = rt.uvwmap()
    rep = {"node": _s(node.name), "size_cm": size_cm, "system_units_per_cm": k}
    for p, v in (("maptype", 4), ("length", size_cm * k), ("width", size_cm * k), ("height", size_cm * k)):
        rep[p] = set_prop(mod, p, v)  # [verify] maptype 4 = box, length/width/height
    rt.addModifier(node, mod)
    return rep


# --------------------------------------------------------------------------- look-dev passes

def _clamp_albedo(rgb):
    # never pure white or black (64vzHYEWedI 00:27:26); the 10..240 window is [added]
    return tuple(max(10, min(240, int(c))) for c in rgb)


def general_feeling(groups: dict, target: str = "openpbr") -> dict:
    """groups: {"Wall*": (145, 140, 132), "Floor*": (...)} with 8-bit display values.
    One flat material per group, no textures yet. Existing materials are recorded, not deleted."""
    rep = {"assigned": [], "previous": {}}
    color_props = {"openpbr": ("base_color",), "physical": ("base_color",), "gltf": ("baseColor",),
                   "vray": ("diffuse",), "corona": ("baseColor", "basecolor")}
    for pattern, rgb in groups.items():
        m = _new_material(target, "GF_" + re.sub(r"[^A-Za-z0-9]", "", pattern))
        if m is None:
            rep["error"] = f"no class for {target}"
            return rep
        p, how = find_prop(m, color_props[target], ("color",) if target != "vray" else ("diffuse",))
        c = _clamp_albedo(rgb)
        rep.setdefault("color_property", {})[pattern] = (p, how, c)
        if p:
            set_prop(m, p, rt.color(*c))
        for o in rt.objects:
            if fnmatch.fnmatch(_s(o.name), pattern):
                rep["previous"][_s(o.name)] = _s(o.material.name) if o.material else None
                o.material = m
                rep["assigned"].append(_s(o.name))
    return rep


def lookdev_rig(ball_radius_cm: float = 25.0) -> dict:
    """Ball, floor and camera named LKD_*; light and environment come from the lighting sibling."""
    k = _unit_scale_to_cm()
    r = ball_radius_cm * k
    ball = rt.Sphere(radius=r, segs=64, pos=rt.Point3(0, 0, r), name="LKD_ball")  # [verify] segs
    floor = rt.Plane(length=r * 16, width=r * 16, pos=rt.Point3(0, 0, 0), name="LKD_floor")  # [verify]
    tgt = rt.Targetobject(pos=rt.Point3(0, 0, r))  # [verify]
    cam = rt.Targetcamera(pos=rt.Point3(0, -r * 8, r * 2.2), target=tgt, name="LKD_cam")  # [verify]
    return {"ball": _s(ball.name), "floor": _s(floor.name), "camera": _s(cam.name), "radius_units": r}


# --------------------------------------------------------------------------- audits

_DATA_WORDS = ("rough", "gloss", "metal", "normal", "nrm", "height", "disp", "bump", "ao", "occlusion",
               "opacity", "mask", "alpha", "orm", "arm")
_COLOR_WORDS = ("basecolor", "albedo", "diffuse", "diff", "col", "color", "colour", "emissi")


def _role_from_name(path: str) -> str | None:
    toks = [t for t in re.split(r"[_\-. ]+", os.path.splitext(os.path.basename(path))[0].lower()) if t]
    for t in reversed(toks):
        if any(t.startswith(w) for w in _DATA_WORDS):
            return "data"
        if any(t.startswith(w) for w in _COLOR_WORDS):
            return "color"
    return None


def audit_textures() -> list[dict]:
    out = []
    for tex in rt.getClassInstances(rt.Bitmaptexture):  # [verify] getClassInstances
        fn = _s(tex.filename) if tex.filename else ""
        role = _role_from_name(fn)
        if not fn or not os.path.exists(fn):
            out.append({"severity": "error", "rule": "missing_map", "node": _s(tex.name), "message": fn})
            continue
        try:
            b = tex.bitmap  # [verify]
            cs, src, st = _s(b.colorSpace), _s(b.colorSpaceSource), _s(b.colorSpaceStatus)
        except Exception as e:
            out.append({"severity": "warn", "rule": "colorspace_unreadable", "node": _s(tex.name), "message": str(e)})
            continue
        low = cs.lower()
        if "forceddefault" in st.lower() or "invalid" in st.lower():
            out.append({"severity": "error", "rule": "colorspace_failed", "node": _s(tex.name), "message": f"{fn}: {st}"})
        if role == "data" and not any(h in low for h in _DATA_HINTS):
            out.append({"severity": "error", "rule": "data_map_as_color", "node": _s(tex.name),
                        "message": f"{os.path.basename(fn)} is {cs} ({src}); data maps must be Raw"})
        if role == "color" and any(h in low for h in _DATA_HINTS):
            out.append({"severity": "error", "rule": "color_map_as_data", "node": _s(tex.name),
                        "message": f"{os.path.basename(fn)} is {cs}"})
        if role is None:
            out.append({"severity": "info", "rule": "role_unknown", "node": _s(tex.name),
                        "message": f"{os.path.basename(fn)} is {cs} ({src}); check the slot it feeds"})
    vb = find_class("vraybitmap", kind="texturemap")
    if vb is not None:
        for t in rt.getClassInstances(vb):
            p, _ = find_prop(t, ("HDRIMapName",), ("file",))  # [verify] HDRIMapName
            fn = _s(rt.getProperty(t, p)) if p else ""  # [verify] getProperty
            stem = os.path.splitext(os.path.basename(fn))[0].lower()
            role = _role_from_name(fn)
            tagged = stem.endswith(("_raw", "_srgb", "_lin_srgb", "_acescg"))
            if not tagged:
                out.append({"severity": "warn", "rule": "vraybitmap_untagged", "node": _s(t.name),
                            "message": f"{os.path.basename(fn)}: Auto/Default only guesses (QuJe2j7SHZ0 00:08:19)"})
            elif role == "data" and not stem.endswith("_raw"):
                out.append({"severity": "error", "rule": "vraybitmap_data_not_raw", "node": _s(t.name), "message": fn})
    return out


def _is_rgb(v, rgb) -> bool:
    try:
        return int(v.r) == rgb[0] and int(v.g) == rgb[1] and int(v.b) == rgb[2]
    except Exception:
        return False


def audit_materials() -> list[dict]:
    out, counts = [], {}
    for m in rt.sceneMaterials:  # [verify] sceneMaterials
        cname = _s(rt.classOf(m))
        counts[cname] = counts.get(cname, 0) + 1
        n = _norm(cname)
        if n in ("standardmaterial", "standard") or "legacy" in n:
            out.append({"severity": "warn", "rule": "legacy_class", "node": _s(m.name), "message": cname})
        for p in discover(m):
            pn = _norm(p)
            if not any(k in pn for k in ("color", "diffuse")) or "map" in pn:
                continue
            try:
                v = rt.getProperty(m, p)  # [verify] getProperty
            except Exception:
                continue
            if _is_rgb(v, (255, 0, 0)):
                out.append({"severity": "error", "rule": "debug_red_left", "node": _s(m.name), "message": p})
            if ("base" in pn or "diffuse" in pn) and (_is_rgb(v, (255, 255, 255)) or _is_rgb(v, (0, 0, 0))):
                out.append({"severity": "warn", "rule": "pure_white_or_black_albedo", "node": _s(m.name), "message": p})
        if "layered" in n:
            bp, _ = find_prop(m, ("baseMtl", "base_material"), ("base",))
            if bp and rt.getProperty(m, bp) is None:  # [verify] getProperty
                out.append({"severity": "error", "rule": "layered_empty_base", "node": _s(m.name),
                            "message": "renders white/cyan in Corona (rBBLMAtnbzQ frame 00:00:29)"})
    out.append({"severity": "info", "rule": "class_counts", "node": "", "message": counts})
    return out


def audit_multisub(node) -> list[dict]:
    """Face IDs without a sub-material render black (multi-sub-object-material-2027)."""
    m = node.material
    if m is None or "multi" not in _norm(_s(rt.classOf(m))):
        return []
    ids = set()
    try:
        mesh = rt.snapshotAsMesh(node)  # [verify]
        for f in range(1, mesh.numfaces + 1):
            ids.add(int(rt.getFaceMatID(mesh, f)))  # [verify]
        rt.delete(mesh)  # a temporary TriMesh copy, never a scene node
    except Exception as e:
        return [{"severity": "warn", "rule": "multisub_unreadable", "node": _s(node.name), "message": str(e)}]
    try:
        id_list = [int(i) for i in m.materialIDList]  # [verify]
        subs = list(m.materialList)  # [verify]
        have = set(id_list)
    except Exception as e:
        return [{"severity": "warn", "rule": "multisub_unreadable", "node": _s(node.name), "message": str(e)}]
    out = []
    for i in sorted(ids - have):
        out.append({"severity": "error", "rule": "face_id_without_submaterial", "node": _s(node.name), "message": i})
    for i, sub in zip(id_list, subs):
        if sub is None and i in ids:
            out.append({"severity": "error", "rule": "empty_submaterial_used", "node": _s(node.name), "message": i})
    unused = sorted(have - ids)
    if unused:
        out.append({"severity": "info", "rule": "unused_submaterials", "node": _s(node.name), "message": unused})
    return out
