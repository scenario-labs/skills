"""game_rules: offline gates for engine assets (plain Python 3.10+, any OS, never imports pymxs).

status: runs outside 3ds Max; the rules are checked against notes/game-assets digests and
        game-assets__unreal-fbx-static-mesh-pipeline.md. The audit JSON it reads comes from
        maxkit_game.game_audit() or mxs/game_audit.ms.

    check_report(report, target="unreal", budgets=None) -> findings list
    check_names(names, helpers=(), target="unreal")     -> findings list
    check_lods(tris_by_level, max_ratio=0.67)            -> findings list
    fbx_header(path)    -> {"kind": "binary"|"ascii"|"unknown", "version": int|None}
    glb_summary(path)   -> sizes in meters, triangles, materials, images, vertex colors, extensions

CLI:
    python game_rules.py report audit.json [--target unreal|unity|gltf] [--budget LOD0=8000 ...]
    python game_rules.py fbx file.fbx
    python game_rules.py glb file.glb
A finding is {"severity": "error"|"warn"|"info", "rule": str, "node": str, "message": str}.
"""
from __future__ import annotations

import json
import re
import struct
import sys

COLLISION_PREFIXES = ("UCX_", "UBX_", "USP_", "UCP_")  # UCX in the saved Epic doc; others [added] from Epic docs
LOD_RE = re.compile(r"^(?P<base>.+)_LOD(?P<n>\d+)$", re.IGNORECASE)
CRY_LOD_RE = re.compile(r"^\$lod(?P<n>\d+)_(?P<base>.+)$", re.IGNORECASE)
SOCKET_RE = re.compile(r"^SOCKET_(?P<base>.+?)(_\d+)?$")
TOL_ORIGIN = 1e-4  # cm; Ghost Pig: 1e-06 residue shows in Unity, re-enter 0 (z1ws_LOo9AU 00:07:30)


def _f(sev, rule, node, msg):
    return {"severity": sev, "rule": rule, "node": node, "message": msg}


def _base_of_collision(name):
    for p in COLLISION_PREFIXES:
        if name.startswith(p):
            rest = name[len(p):]
            return re.sub(r"_\d+$", "", rest), rest
    return None, None


def check_names(names, helpers=(), target="unreal"):
    """Collision, socket, LOD and duplicate-name rules."""
    out = []
    names = list(names)
    seen = set()
    for n in names + list(helpers):
        if n in seen:
            out.append(_f("error", "names.duplicate", n, "duplicate node name; engines and glTF rename duplicates"))
        seen.add(n)
    render = [n for n in names if _base_of_collision(n)[0] is None]
    render_set = set(render)
    for n in names:
        base, rest = _base_of_collision(n)
        if base is None:
            continue
        if target == "gltf":
            out.append(_f("warn", "collision.in_gltf", n, "collision mesh selected for a glTF export"))
        if base not in render_set and rest not in render_set:
            out.append(_f("error", "collision.no_render_mesh", n,
                          f"no render mesh named '{base}' (Epic: RenderMeshName must be identical)"))
    sockets = [h for h in helpers if h.startswith("SOCKET_")]
    socket_bases = set()
    for s in sockets:
        base = SOCKET_RE.match(s).group("base")
        rest = s[len("SOCKET_"):]
        cands = [r for r in render if rest == r or re.fullmatch(re.escape(r) + r"_\d+", rest)]
        if not cands:
            out.append(_f("error", "socket.no_render_mesh", s, f"no render mesh matches '{base}'"))
        socket_bases.update(cands)
    if sockets and len([r for r in render if not LOD_RE.match(r)]) > 1:
        out.append(_f("error", "socket.single_mesh", ",".join(sockets),
                      "an FBX with sockets must hold a single render mesh (Epic doc): split the export"))
    for n in names:
        if CRY_LOD_RE.match(n) and target != "cryengine":
            out.append(_f("info", "lod.cry_naming", n, "$lodN_ naming is the CRYENGINE convention"))
    return out


def check_lods(tris_by_level, max_ratio=0.67, target_ratio=0.5, base="asset"):
    """tris_by_level: {0: 8000, 1: 4100, ...}. Crytek: about 50 percent per step, warn above 67."""
    out = []
    levels = sorted(tris_by_level)
    if levels and levels != list(range(levels[0], levels[0] + len(levels))):
        out.append(_f("error", "lod.gap", base, f"LOD levels not contiguous: {levels}"))
    for a, b in zip(levels, levels[1:]):
        ta, tb = tris_by_level[a], tris_by_level[b]
        if ta <= 0:
            continue
        r = tb / ta
        if r > max_ratio:
            out.append(_f("error", "lod.ratio", f"{base}_LOD{b}",
                          f"{tb} tris is {r:.0%} of LOD{a} ({ta}); keep under {max_ratio:.0%}, aim {target_ratio:.0%}"))
        elif r < 0.2:
            out.append(_f("warn", "lod.big_jump", f"{base}_LOD{b}", f"{r:.0%} of LOD{a}: check popping"))
    return out


def _group_lods(nodes):
    groups = {}
    for n in nodes:
        m = LOD_RE.match(n["name"])
        if m:
            groups.setdefault(m.group("base"), {})[int(m.group("n"))] = n["tris"]
    for n in nodes:  # an unsuffixed node is LOD0 of a group that has LOD1+
        if n["name"] in groups and 0 not in groups[n["name"]]:
            groups[n["name"]][0] = n["tris"]
    return groups


def check_report(report, target="unreal", budgets=None):
    """Gates on the audit dict from maxkit_game.game_audit() / mxs/game_audit.ms."""
    out = []
    budgets = budgets or {}
    unit = str(report.get("units", "")).lower()
    if target in ("unreal", "unity") and unit != "centimeters":
        out.append(_f("error", "units.system", "scene", f"system unit is {unit or '?'}; use centimeters"))
    scale = report.get("system_scale")
    if target in ("unreal", "unity") and scale is not None and abs(float(scale) - 1.0) > 1e-6:
        out.append(_f("error", "units.scale", "scene", f"system unit scale is {scale}; use 1 unit = 1 cm"))
    nodes = report.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        out.append(_f("error", "report.no_nodes", "scene", "audit lists no render mesh: nothing was checked"))
        nodes = []
    helpers = report.get("helpers", [])
    out += check_names([n["name"] for n in nodes], [h["name"] for h in helpers], target)
    by_name = {n["name"]: n for n in nodes}
    for n in nodes:
        name = n["name"]
        is_col = _base_of_collision(name)[0] is not None
        if n.get("negative_scale"):
            out.append(_f("error", "xform.negative_scale", name, "mirrored transform: Reset XForm, then check normals"))
        sc = n.get("scale") or [1, 1, 1]
        if any(abs(s - 1.0) > 1e-4 for s in sc):
            out.append(_f("warn", "xform.scale", name, f"scale {sc}: Reset XForm and collapse before export"))
        if not n.get("rotation_identity", True):
            out.append(_f("warn", "xform.rotation", name, "node rotation is not identity"))
        if not is_col and n.get("parent") is None:
            pos = n.get("pos") or [0, 0, 0]
            off = [p for p in pos if abs(p) > TOL_ORIGIN]
            if off and not LOD_RE.match(name):
                out.append(_f("warn", "pivot.origin", name, f"pos {pos}: FBX pivot is the origin (Epic doc)"))
            elif any(0 < abs(p) <= TOL_ORIGIN for p in pos):
                out.append(_f("warn", "pivot.residue", name, f"pos {pos}: sub-precision residue, re-enter 0"))
        if n.get("open_edges", 0) > 0:
            sev = "error" if is_col else "warn"
            out.append(_f(sev, "mesh.open_edges", name, f"{n['open_edges']} open edges"))
        if n.get("iso_verts", 0) > 0:
            out.append(_f("warn", "mesh.isolated_verts", name, f"{n['iso_verts']} isolated vertices"))
        if n.get("ngons", -1) > 0:
            out.append(_f("info", "mesh.ngons", name, f"{n['ngons']} ngons: triangulate by hand where shading matters"))
        if not is_col:
            sg0, tris = n.get("sg0_faces", -1), n.get("tris", 0)
            if tris and sg0 == tris:
                out.append(_f("warn", "normals.sg0", name, "every face in smoothing group 0: faceted unless normals are explicit"))
            maps = [int(c) for c in n.get("map_channels", [])]
            uvs = [c for c in maps if c >= 1]
            if not uvs:
                out.append(_f("error", "uv.none", name, "no UV channel"))
            elif 1 not in uvs:
                out.append(_f("error", "uv.channel1", name, f"no UVs in map channel 1 (channels {uvs})"))
            if target == "unreal" and len(uvs) > 8:
                out.append(_f("error", "uv.count", name, f"{len(uvs)} UV channels; Unreal keeps 8"))
            if target == "datasmith" and len(uvs) > 6:
                out.append(_f("error", "uv.count", name, f"{len(uvs)} UV channels; Datasmith keeps 6"))
            if target == "gltf" and 0 in maps:
                out.append(_f("warn", "vc.gltf", name, "vertex colors: the 3ds Max glTF exporter does not export them"))
        else:
            cv = n.get("convex_violations", -1)
            if cv > 0:
                out.append(_f("error", "collision.convex", name, f"{cv} vertex/plane violations: hull is not convex"))
            elif cv < 0 and name.startswith("UCX_"):  # the audit measures UCX hulls only
                out.append(_f("error", "collision.convex_unknown", name,
                              "convexity not measured (over 2000 faces or missing): split or simplify the hull"))
        m = LOD_RE.match(name)
        level = int(m.group("n")) if m else (None if is_col else 0)  # an unsuffixed render mesh is LOD0
        for key, limit in budgets.items():
            km = re.fullmatch(r"LOD(\d+)", key, re.IGNORECASE)
            if key == name or (km and level is not None and int(km.group(1)) == level):
                if n.get("tris", 0) > limit:
                    out.append(_f("error", "budget.tris", name, f"{n['tris']} tris over budget {limit}"))
    for base, levels in _group_lods(nodes).items():
        out += check_lods(levels, base=base)
        mats = {by_name.get(base if lv == 0 else f"{base}_LOD{lv}", {}).get("material_class") for lv in levels}
        mats.discard(None)
        if len(mats) > 1:
            out.append(_f("info", "lod.materials", base, f"LOD material classes differ: {sorted(mats)}"))
    if target == "unity":
        out.append(_f("info", "unity.axis", "scene", "after import: Model tab, Bake Axis Conversion on, rotation 0,0,0"))
    return out


# ---------------------------------------------------------------- files

def fbx_header(path):
    """Binary FBX starts 'Kaydara FBX Binary  \\x00' then a uint32 version at byte 23.
    7700 is the 2019/2020 family; Epic's pipeline asks for FBX 2020.2 [added: header layout]."""
    with open(path, "rb") as fh:
        head = fh.read(27)
    if head[:20] == b"Kaydara FBX Binary  ":
        return {"kind": "binary", "version": struct.unpack("<I", head[23:27])[0]}
    if head[:1] in (b";", b"F") or b"FBXHeaderExtension" in head:
        return {"kind": "ascii", "version": None}
    return {"kind": "unknown", "version": None}


def _read_glb(path):
    with open(path, "rb") as fh:
        data = fh.read()
    magic, version, length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF":
        raise ValueError("not a GLB file")
    off = 12
    js, binc = None, None
    while off < min(length, len(data)):
        clen, ctype = struct.unpack("<I4s", data[off:off + 8])
        chunk = data[off + 8:off + 8 + clen]
        if ctype == b"JSON":
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == b"BIN\x00":
            binc = chunk
        off += 8 + clen
    return version, js, binc


def _mat4(node):
    if "matrix" in node:
        m = node["matrix"]  # column-major
        return [[m[0], m[4], m[8], m[12]], [m[1], m[5], m[9], m[13]], [m[2], m[6], m[10], m[14]], [0, 0, 0, 1]]
    t = node.get("translation", [0, 0, 0])
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    s = node.get("scale", [1, 1, 1])
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[r[i][0] * s[0], r[i][1] * s[1], r[i][2] * s[2], t[i]] for i in range(3)] + [[0, 0, 0, 1]]


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def glb_summary(path):
    """World-space bounds (meters, glTF is Y up), triangle count, materials, images, vertex
    colors, extensions. Bounds use accessor min/max corners through node transforms."""
    version, js, _ = _read_glb(path)
    acc = js.get("accessors", [])
    meshes = js.get("meshes", [])
    nodes = js.get("nodes", [])
    tris, has_color, prims = 0, False, 0
    for m in meshes:
        for p in m.get("primitives", []):
            prims += 1
            if p.get("mode", 4) != 4:
                continue
            if "indices" in p:
                tris += acc[p["indices"]]["count"] // 3
            elif "POSITION" in p.get("attributes", {}):
                tris += acc[p["attributes"]["POSITION"]]["count"] // 3
            if "COLOR_0" in p.get("attributes", {}):
                has_color = True
    lo, hi = [float("inf")] * 3, [float("-inf")] * 3
    scenes = js.get("scenes", [{"nodes": list(range(len(nodes)))}])
    roots = scenes[js.get("scene", 0)].get("nodes", []) if scenes else []
    stack = [(i, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) for i in roots]
    while stack:
        i, parent = stack.pop()
        nd = nodes[i]
        world = _mul(parent, _mat4(nd))
        if "mesh" in nd:
            for p in meshes[nd["mesh"]].get("primitives", []):
                a = acc[p["attributes"]["POSITION"]]
                mn, mx = a.get("min"), a.get("max")
                if not mn or not mx:
                    continue
                for cx in (mn[0], mx[0]):
                    for cy in (mn[1], mx[1]):
                        for cz in (mn[2], mx[2]):
                            v = [sum(world[r][c] * q for c, q in enumerate((cx, cy, cz, 1))) for r in range(3)]
                            lo = [min(lo[k], v[k]) for k in range(3)]
                            hi = [max(hi[k], v[k]) for k in range(3)]
        stack += [(c, world) for c in nd.get("children", [])]
    size = [hi[k] - lo[k] for k in range(3)] if lo[0] != float("inf") else None
    return {
        "glb_version": version,
        "generator": js.get("asset", {}).get("generator"),
        "size_m_xyz": [round(s, 4) for s in size] if size else None,
        "min_m": [round(v, 4) for v in lo] if size else None,
        "height_axis_guess": None if not size else "Y" if size[1] >= max(size[0], size[2]) else "other",  # longest side only
        "triangles": tris,
        "primitives": prims,
        "nodes": len(nodes),
        "materials": [m.get("name", f"material_{i}") for i, m in enumerate(js.get("materials", []))],
        "images": len(js.get("images", [])),
        "vertex_colors": has_color,
        "extensions_used": js.get("extensionsUsed", []),
        "skins": len(js.get("skins", [])),
        "animations": len(js.get("animations", [])),
    }


def _main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, path = argv[1], argv[2]
    if cmd == "fbx":
        print(json.dumps(fbx_header(path), indent=1))
        return 0
    if cmd == "glb":
        print(json.dumps(glb_summary(path), indent=1))
        return 0
    if cmd == "report":
        target, budgets = "unreal", {}
        rest = argv[3:]
        for i, a in enumerate(rest):
            if a == "--target":
                target = rest[i + 1]
            if a == "--budget":
                for kv in rest[i + 1:]:
                    if kv.startswith("--"):
                        break
                    k, v = kv.split("=")
                    budgets[k] = int(v)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if "result" in data and isinstance(data["result"], (dict, str)):  # max_wrap envelope
            data = data["result"]
            if isinstance(data, str):
                data = json.loads(data)
        findings = check_report(data, target, budgets)
        print(json.dumps(findings, indent=1))
        return 1 if any(f["severity"] == "error" for f in findings) else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
