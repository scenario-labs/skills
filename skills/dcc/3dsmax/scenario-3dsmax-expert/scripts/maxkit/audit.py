"""maxkit.audit: read-only scene audit with findings {severity, rule, node, message}.

The rules are pure Python over maxkit.stats.collect() records,
and only collect() touches pymxs (names marked [verify] there).

    all(expect=None, data=None) -> {"findings": [...], "tally": {"error", "warn", "info"}}
    units(data=None, expect=None)      names(...)      transforms(...)      geometry(...)
    materials(...)    maps(...)        layers(...)     render(...)          -> [finding, ...]

expect (all keys optional): units ("centimeters"), renderer (substring of the renderer class,
"Arnold", "V_Ray", "Corona"), far_limit (system units; default 1 km converted from units and system scale),
max_faces (per object), layer0_empty (default True).
Severity: error blocks delivery, warn needs a decision, info is context.
Sources for the rules: units and far origin (fundamentals-scene digests, system-unit-setup doc);
Reset XForm after scaling (hz07nIgm7EA 00:21:31); layer 0 empty and no generic names
(XpWCMn9Nboc frame 00:02:01); missing maps and units mismatch block renders
(max-mcp-known-limitations-2027-3).
"""
from __future__ import annotations

import math
import re

try:
    from maxkit import stats as _stats
except ImportError:  # inlined by max_wrap or run from scripts/maxkit
    import stats as _stats  # type: ignore

DEFAULT_NAME = re.compile(
    r"^(Box|Sphere|GeoSphere|Cylinder|Cone|Torus|Tube|Pyramid|Plane|Teapot|Object|Line|Rectangle|"
    r"Circle|Shape|Group|Camera|Dummy|Point|Text|Arc|Ellipse|Helix|Spot|Omni|Mesh|Poly|"
    r"[A-Za-z]+_Camera|Corona_Camera|VRayCam|Corona Light|VRayLight)\s*\d{2,}(\.Target)?$",
    re.I)
LEGACY_MATERIALS = {"standardmaterial", "standard", "architectural", "raytracematerial"}
RENDERER_FAMILIES = {  # renderer substring -> material class prefixes that belong to it [added]
    "v_ray": ("vray",), "vray": ("vray",), "corona": ("corona",),
    "arnold": ("openpbr", "physical", "ai_", "arnold", "standard_surface", "gltf"),
}
UNIT_PER_METER = {"millimeters": 1000.0, "centimeters": 100.0, "meters": 1.0, "kilometers": 0.001,
                  "inches": 39.3701, "feet": 3.28084, "miles": 0.000621371}


def _f(severity, rule, node, message):
    return {"severity": severity, "rule": rule, "node": node, "message": message}


def _data(data):
    return data if data is not None else _stats.collect()


def _unit_key(u):
    if not u:
        return None
    u = str(u).lstrip("#").lower()
    return u


def units(data=None, expect=None) -> list:
    d, e = _data(data), expect or {}
    sc = d.get("scene", {})
    out = []
    unit = _unit_key(sc.get("system_unit"))
    want = _unit_key(e.get("units"))
    if want and not unit:
        out.append(_f("error", "units", None, f"system unit could not be read; project expects {want}"))
    elif want and unit != want:
        out.append(_f("error", "units", None, f"system unit is {unit}, project expects {want}; "
                      "never change system units under existing geometry, rescale or merge into a clean file"))
    scale = sc.get("system_scale")
    if scale is not None and abs(float(scale) - 1.0) > 1e-9:
        out.append(_f("warn", "units", None, f"system scale is {scale}, expected 1.0"))
    far = e.get("far_limit")
    if far is None:
        far = 1000.0 * UNIT_PER_METER.get(unit or "centimeters", 100.0)  # 1 km [added]
        if scale is not None and float(scale) > 0:
            far /= float(scale)  # one system unit is scale x unit
    for n in d.get("nodes", []):
        lo, hi = n.get("bbox_min"), n.get("bbox_max")
        if lo and hi:
            c = [(a + b) / 2.0 for a, b in zip(lo, hi)]
            dist = math.sqrt(sum(v * v for v in c))
            if dist > far:
                out.append(_f("error", "units", n.get("name"), f"{dist:.0f} units from the origin "
                              f"(limit {far:.0f}): round-off, jitter and flipped normals; move to the origin "
                              "with a recorded offset helper"))
    return out


def names(data=None, expect=None) -> list:
    d = _data(data)
    out, seen = [], {}
    for n in d.get("nodes", []):
        name = n.get("name") or ""
        seen[name] = seen.get(name, 0) + 1
        if DEFAULT_NAME.match(name.strip()):
            out.append(_f("warn", "names", name, "generic default name; rename <Zone> - <Item> or by layer convention"))
        if any(ord(ch) > 127 for ch in name):
            out.append(_f("warn", "names", name, "non-ASCII characters break some exporters and engines"))
        if name != name.strip():
            out.append(_f("warn", "names", name, "leading or trailing spaces"))
    for name, count in seen.items():
        if count > 1:
            out.append(_f("warn", "names", name, f"{count} nodes share this name; FBX, glTF and engines rename or merge them"))
    return out


def transforms(data=None, expect=None) -> list:
    d = _data(data)
    out = []
    heads = 0
    for n in d.get("nodes", []):
        s = n.get("scale")
        if n.get("group_head"):
            heads += 1
        if not s:
            continue
        if any(v < 0 for v in s):
            out.append(_f("warn", "transforms", n.get("name"), f"negative scale {s}: mirrored, normals flip on export; Reset XForm"))
        elif max(s) - min(s) > 1e-4:
            out.append(_f("warn", "transforms", n.get("name"), f"non-uniform scale {s}: Reset XForm before modifiers, UVs or export"))
        elif abs(s[0] - 1.0) > 1e-4:
            out.append(_f("info", "transforms", n.get("name"), f"uniform scale {s[0]:.4g}: Reset XForm before export or skinning"))
    if heads:
        out.append(_f("info", "transforms", None, f"{heads} group heads; nested groups break merges and selection"))
    return out


def geometry(data=None, expect=None) -> list:
    d, e = _data(data), expect or {}
    out = []
    budget = e.get("max_faces")
    for n in d.get("nodes", []):
        if n.get("superclass") != _stats.GEOMETRY:
            continue
        faces = int(n.get("faces") or 0)
        if faces == 0:
            out.append(_f("warn", "geometry", n.get("name"), "geometry with 0 faces"))
        if budget and faces > budget:
            out.append(_f("warn", "geometry", n.get("name"), f"{faces} faces over the {budget} budget; proxy, instance or optimize"))
    return out


def materials(data=None, expect=None) -> list:
    d, e = _data(data), expect or {}
    out = []
    want = (e.get("renderer") or "").lower()
    family = next((v for k, v in RENDERER_FAMILIES.items() if k in want), None) if want else None
    for n in d.get("nodes", []):
        if n.get("superclass") != _stats.GEOMETRY:
            continue
        mc = (n.get("material_class") or "").lower()
        if not n.get("material"):
            out.append(_f("warn", "materials", n.get("name"), "no material"))
            continue
        if mc in LEGACY_MATERIALS:
            out.append(_f("warn", "materials", n.get("name"), f"legacy {n.get('material_class')}; convert with Scene Converter"))
        elif family and mc and mc not in ("multimaterial", "multi_sub_object", "shell_material") \
                and not mc.startswith(family):
            out.append(_f("info", "materials", n.get("name"),
                          f"{n.get('material_class')} under a {e.get('renderer')} project; check it renders as intended"))
    return out


def maps(data=None, expect=None) -> list:
    d = _data(data)
    sc = d.get("scene", {})
    files = sorted({b["file"] for b in sc.get("bitmaps") or [] if not b.get("exists")})
    out = [_f("error", "maps", None, f"missing map: {f} (a modal dialog can block renders)") for f in files]
    if sc.get("bitmaps_error"):
        out.append(_f("error", "maps", None, f"bitmaps could not be listed: {sc['bitmaps_error']}"))
    return out


def layers(data=None, expect=None) -> list:
    d, e = _data(data), expect or {}
    out = []
    counts: dict = {}
    for n in d.get("nodes", []):
        counts[n.get("layer") or "?"] = counts.get(n.get("layer") or "?", 0) + 1
    zero = counts.get("0", 0) + counts.get("0 (default)", 0)
    if e.get("layer0_empty", True) and zero:
        out.append(_f("warn", "layers", None, f"layer 0 holds {zero} nodes; keep it empty, sort by type or zone"))
    for name in d.get("scene", {}).get("layer_names") or []:
        if name not in ("0", "0 (default)") and counts.get(name, 0) == 0:
            out.append(_f("info", "layers", name, "empty layer"))
    return out


def render(data=None, expect=None) -> list:
    d, e = _data(data), expect or {}
    sc = d.get("scene", {})
    out = []
    want = (e.get("renderer") or "").lower()
    have = (sc.get("renderer") or "")
    if want and want not in have.lower():
        out.append(_f("error", "render", None, f"renderer is {have or 'unknown'}, project expects {e.get('renderer')}"))
    if sc.get("save_required"):
        out.append(_f("info", "render", None, "unsaved changes in the open scene; save a new increment before risky work"))
    return out


RULES = (units, names, transforms, geometry, materials, maps, layers, render)


def all(expect=None, data=None) -> dict:  # noqa: A001 (contract name)
    """Run every rule on one collect() pass. Read-only."""
    d = _data(data)
    findings = []
    for rule in RULES:
        findings.extend(rule(d, expect))
    tally = {"error": 0, "warn": 0, "info": 0}
    for f in findings:
        tally[f["severity"]] = tally.get(f["severity"], 0) + 1
    return {"findings": findings, "tally": tally}
