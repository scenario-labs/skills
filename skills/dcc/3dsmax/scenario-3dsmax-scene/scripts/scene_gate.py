"""scene_gate: runner-side pass/fail verdict for a scene audit (plain Python 3.10+).

Reads the JSON that the intake audit chunk returns (maxkit_scene.audit_scene()
inside the max_wrap result protocol) and a project spec, prints one line per
gate, and exits 1 when a blocking gate fails. Never imports pymxs.

    python scene_gate.py result.json [spec.json]

spec.json keys (all optional; defaults in DEFAULT_SPEC):
    system_type, system_scale, max_far_m, max_default_named, max_group_depth,
    max_on_layer_0, max_missing_maps, max_copy_groups, max_viewport_smooth,
    max_faces_per_node, max_file_mb
The audit must carry the units, origin, maps and xrefs sections, and its far cutoff
(origin.far_cm, set by audit_scene(far_cm=...)) must not exceed max_far_m: run the
audit with far_cm = max_far_m x 100. A missing section, a larger cutoff, an unreadable
map or an unreadable XRef record fails a blocking gate.
status: logic run on sample JSON.
"""
import json
import sys

REQUIRED_SECTIONS = ("units", "origin", "maps", "xrefs")

DEFAULT_SPEC = {
    "system_type": "centimeters",   # project choice, not a 3ds Max default
    "system_scale": 1.0,
    "max_far_m": 1000.0,            # [added] archviz default; raise for site models
    "max_default_named": 0,
    "max_group_depth": 1,
    "max_on_layer_0": 0,
    "max_missing_maps": 0,
    "max_copy_groups": 0,
    "max_viewport_smooth": 0,
    "max_faces_per_node": None,     # set per project; None skips the gate
    "max_file_mb": None,
}


def _load(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    # accept the raw audit dict or the max_wrap envelope {ok, result, ...}
    if isinstance(data, dict) and "result" in data and isinstance(data["result"], dict):
        data = data["result"]
    if isinstance(data, dict) and "scene" in data and isinstance(data["scene"], dict):
        data = data["scene"]
    return data


def gates(audit, spec):
    """Return a list of (name, ok, measured, limit, blocking)."""
    s = dict(DEFAULT_SPEC, **(spec or {}))
    rows = []
    absent = [k for k in REQUIRED_SECTIONS if not isinstance(audit.get(k), dict)]
    if absent:
        rows.append(("audit sections present", False, "missing " + ", ".join(absent),
                     ", ".join(REQUIRED_SECTIONS), True))
    u = audit.get("units") or {}
    rows.append(("system unit", u.get("system_type") == s["system_type"]
                 and abs(float(u.get("system_scale") or 0) - s["system_scale"]) < 1e-9,
                 "%s x %s" % (u.get("system_type"), u.get("system_scale")),
                 "%s x %s" % (s["system_type"], s["system_scale"]), True))
    origin = audit.get("origin") or {}
    far = origin.get("far", [])
    far_max = max([r.get("distance_m", 0) for r in far] or [0])
    cutoff = origin.get("far_cm")
    if not isinstance(cutoff, (int, float)) or cutoff / 100.0 > s["max_far_m"]:
        rows.append(("far from origin", False, "audit cutoff %s cm" % cutoff,
                     "cutoff <= %s cm" % (s["max_far_m"] * 100.0), True))
    else:
        rows.append(("far from origin", far_max <= s["max_far_m"], far_max, s["max_far_m"], True))
    n = audit.get("names", {})
    rows.append(("default names", n.get("default_named", 0) <= s["max_default_named"],
                 n.get("default_named", 0), s["max_default_named"], False))
    rows.append(("duplicate names", not n.get("duplicate_names"),
                 len(n.get("duplicate_names", [])), 0, False))
    g = audit.get("groups", {})
    rows.append(("group depth", g.get("max_depth", 0) <= s["max_group_depth"],
                 g.get("max_depth", 0), s["max_group_depth"], False))
    lay = audit.get("layers", {})
    rows.append(("nodes on layer 0", lay.get("on_layer_0", 0) <= s["max_on_layer_0"],
                 lay.get("on_layer_0", 0), s["max_on_layer_0"], False))
    rows.append(("layer names off convention", not lay.get("off_convention"),
                 len(lay.get("off_convention", [])), 0, False))
    m = audit.get("maps") or {}
    unread = m.get("unreadable", 0)
    rows.append(("maps inspected", unread == 0, "%s unreadable" % unread, 0, True))
    rows.append(("missing maps", m.get("missing_count", 0) <= s["max_missing_maps"],
                 m.get("missing_count", 0), s["max_missing_maps"], True))
    xr = audit.get("xrefs") or {}
    x = xr.get("xref_scenes", [])
    broken = [r for r in x if r.get("exists") is False]
    rows.append(("XRef records inspected", not xr.get("errors"), len(xr.get("errors", [])), 0, True))
    rows.append(("broken XRef files", not broken, len(broken), 0, True))
    sc = audit.get("scale", {})
    rows.append(("geometry scale not (1,1,1)", sc.get("non_unit_scale", 0) == 0,
                 sc.get("non_unit_scale", 0), 0, False))
    c = audit.get("copies", {})
    rows.append(("copy groups not instanced", c.get("groups", 0) <= s["max_copy_groups"],
                 c.get("groups", 0), s["max_copy_groups"], False))
    sm = audit.get("smooth", {}).get("viewport_iter_above_0", [])
    rows.append(("viewport smoothing above 0", len(sm) <= s["max_viewport_smooth"],
                 len(sm), s["max_viewport_smooth"], False))
    if s["max_faces_per_node"]:
        top = audit.get("polys", {}).get("top", [])
        worst = top[0]["faces"] if top else 0
        rows.append(("faces per node", worst <= s["max_faces_per_node"], worst,
                     s["max_faces_per_node"], False))
    if s["max_file_mb"] and isinstance(audit.get("file_size_mb"), (int, float)):
        rows.append(("file size MB", audit["file_size_mb"] <= s["max_file_mb"],
                     audit["file_size_mb"], s["max_file_mb"], False))
    return rows


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    audit = _load(argv[1])
    spec = {}
    if len(argv) > 2:
        with open(argv[2], encoding="utf-8") as fh:
            spec = json.load(fh)
    failed_blocking = False
    for name, ok, measured, limit, blocking in gates(audit, spec):
        tag = "PASS" if ok else ("FAIL" if blocking else "WARN")
        failed_blocking |= (not ok and blocking)
        print("%-4s %-30s measured=%s limit=%s" % (tag, name, measured, limit))
    return 1 if failed_blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
