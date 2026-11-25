"""maxkit_fx: FX helpers that run inside 3ds Max (pymxs), inlined by max_wrap.

channel: batch | bridge | handoff (mcp-safe: use the MAXScript twin in references/procedures.md)
checked against scripting-pipeline__pymxs-using-2027.md
        (getPropNames, Name, render), fx-simulation__tyflow-tycache.md (cache()),
        and the fx-simulation digests. Names marked [verify] are not in a saved doc.

Functions
- fx_audit() -> list of findings {severity, rule, node, message}
- discover(node, max_props=200) -> dict of class, property names and values, interfaces text
- cache_tycache_modifiers(nodes=None) -> list of {node, ok, error}; None means every scene node
- time_evaluation(node, start, end) -> dict with seconds per frame and face counts

tyFlow is a third-party plugin. Its operator graph has no documented scripting API in the
saved docs, so nothing here creates events or operators. discover() reads what the installed
tyFlow build exposes so the agent never guesses a property name.
"""
import contextlib
import time

import pymxs
from pymxs import runtime as rt

FX_CLASS_HINTS = {
    "tyflow": "tyFlow object",
    "tycache": "tyCache object or modifier",
    "phoenix": "Chaos Phoenix (End-of-Support since April 2026)",
    "massfx": "MassFX",
    "mcloth": "MassFX mCloth",
    "hair": "Hair and Fur",
}

RECIPE_UNIT = "centimeters"  # recipe numbers in this skill assume 1 unit = 1 cm


def _cls(obj):
    return str(rt.classOf(obj))


def _finding(severity, rule, node, message):
    return {"severity": severity, "rule": rule, "node": node, "message": message}


def _all_nodes():
    return list(rt.objects)


def _modifiers(node):
    """Modifier list of a node. Raises when the stack cannot be read: callers report it."""
    return list(node.modifiers)


def fx_audit():
    """Read-only audit of the FX-relevant state of the open scene."""
    out = []
    try:
        sys_type = str(rt.units.SystemType)  # [verify] units.SystemType
        sys_scale = float(rt.units.SystemScale)  # [verify] units.SystemScale
        sev = "info" if (sys_type == RECIPE_UNIT and abs(sys_scale - 1.0) < 1e-6) else "warn"
        out.append(_finding(sev, "units", None,
                            "system unit %s x %s; recipe values assume 1 unit = 1 cm" % (sys_scale, sys_type)))
    except Exception as exc:
        out.append(_finding("warn", "units", None, "could not read units: %s" % exc))

    try:
        rng = rt.animationRange  # [verify] animationRange
        fps = rt.frameRate  # [verify] frameRate
        out.append(_finding("info", "timeline", None,
                            "fps %s, range %s to %s" % (fps, rng.start, rng.end)))
    except Exception as exc:
        out.append(_finding("warn", "timeline", None, "could not read timeline: %s" % exc))

    renderer = _cls(rt.renderers.current)
    out.append(_finding("info", "renderer", None, renderer))

    try:
        light_count = len(list(rt.lights))
    except Exception:
        light_count = -1

    found = {}
    for node in _all_nodes():
        try:
            mods = _modifiers(node)
        except Exception as exc:
            out.append(_finding("error", "modifiers", str(node.name), "could not read modifiers: %s" % exc))
            mods = []
        names = [_cls(node).lower()] + [_cls(m).lower() for m in mods]
        for key, label in FX_CLASS_HINTS.items():
            if any(key in n for n in names):
                found.setdefault(key, []).append(str(node.name))
                if key == "phoenix":
                    out.append(_finding("warn", "phoenix-eos", str(node.name),
                                        "Phoenix is End-of-Support: frozen, no fixes; plan a tyFlow ZENITH route for new work"))

    for key, nodes in found.items():
        out.append(_finding("info", "fx-objects", None,
                            "%s: %d (%s)" % (FX_CLASS_HINTS[key], len(nodes), ", ".join(nodes[:20]))))

    if found.get("tyflow") and "arnold" in renderer.lower() and light_count == 0:
        out.append(_finding("error", "volume-light", None,
                            "Arnold with tyFlow and no light: ZENITH volumes render black without a light"))
    if not found:
        out.append(_finding("info", "fx-objects", None, "no FX objects found"))
    return out


def discover(node, max_props=200):
    """List what the installed plugin exposes on one node. Read-only."""
    info = {"node": str(node.name), "class": _cls(node), "props": {}, "interfaces": None}
    names = [str(n) for n in list(rt.getPropNames(node))][:max_props]
    for name in names:
        try:
            value = rt.getProperty(node, rt.Name(name))  # [verify] getProperty
            info["props"][name] = str(value)[:200]
        except Exception as exc:
            info["props"][name] = "<unreadable: %s>" % exc
    try:
        stream = rt.StringStream("")  # [verify] StringStream
        rt.showInterfaces(node, to=stream)  # [verify] showInterfaces to:
        info["interfaces"] = str(stream)[:20000]
    except Exception as exc:
        info["interfaces"] = "<not available: %s>" % exc
    try:
        mods = _modifiers(node)
    except Exception as exc:
        info["modifiers_error"] = str(exc)
        mods = []
    for mod in mods:
        info.setdefault("modifiers", []).append(
            {"class": _cls(mod), "props": [str(n) for n in list(rt.getPropNames(mod))][:max_props]})
    return info


def cache_tycache_modifiers(nodes=None):
    """Call the documented cache() function on every tyCache modifier of the given nodes.

    The tyCache doc states that cache() exports the modifier cache and prints errors to the
    MAXScript Listener. Mode, filename and frame range must already be set on the modifier.
    """
    results = []
    for node in (_all_nodes() if nodes is None else nodes):
        try:
            mods = _modifiers(node)
        except Exception as exc:
            results.append({"node": str(node.name), "ok": False, "error": "could not read modifiers: %s" % exc})
            continue
        for mod in mods:
            if _cls(mod).lower() != "tycache":  # [verify] modifier class name string
                continue
            try:
                mod.cache()
                results.append({"node": str(node.name), "ok": True, "error": None})
            except Exception as exc:
                results.append({"node": str(node.name), "ok": False, "error": str(exc)})
    return results


def time_evaluation(node, start, end):
    """Step a fresh simulation frame by frame and time each evaluation.

    Valid only on the first pass after a simulation reset: tyFlow keeps simulated frames in
    RAM, so a second pass returns cached frames and measures nothing.
    """
    per_frame = []
    faces = []
    for frame in range(int(start), int(end) + 1):
        t0 = time.perf_counter()
        with pymxs.attime(frame):  # [verify] pymxs.attime
            mesh = rt.snapshotAsMesh(node)  # [verify] snapshotAsMesh forces evaluation
        per_frame.append(time.perf_counter() - t0)
        try:
            faces.append(int(mesh.numfaces))  # [verify] numfaces
        except Exception:
            faces.append(-1)
        with contextlib.suppress(Exception):
            rt.delete(mesh)  # TriMesh value from snapshotAsMesh, not a scene node [verify]
    total = sum(per_frame)
    return {
        "node": str(node.name),
        "frames": len(per_frame),
        "total_s": round(total, 3),
        "mean_s_per_frame": round(total / max(len(per_frame), 1), 4),
        "max_s_per_frame": round(max(per_frame) if per_frame else 0.0, 4),
        "faces_first_last": [faces[0], faces[-1]] if faces else [],
    }
