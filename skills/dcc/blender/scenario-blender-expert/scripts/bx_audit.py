"""
bx_audit: objective mesh checks an agent runs before calling a model done.

Works inside any Blender 5.x session (headless or GUI). Two ways to use it:

  # inside a running Blender (MCP bridge / Python console)
  import sys; sys.path.append("<skill>/scripts"); import bx_audit
  report = bx_audit.audit(bpy.data.objects["Head_retopo"])
  report = bx_audit.audit(low, high=bpy.data.objects["Head_sculpt"])  # adds fidelity

  # headless
  blender --background scene.blend --python bx_audit.py -- --object Head_retopo \
          [--high Head_sculpt] [--json out.json]

What the numbers mean. Reference values measured with this script on Blender Studio's
own production retopology (CC-BY retopo_examples.blend, Julien Kaspar): Rex head 3,890
faces, 99.9% quads, 38 e3 + 31 e5 poles, 3 valence-6; Snow body 9,402 faces, 99.96%
quads, 250 e3 + 258 e5; Rain body 16,526 faces, 99.98% quads, 241 e3 + 247 e5, 2 v6.
  quads_pct          deforming character mesh: studio work sits at 99.9+; below 98 = look why
  ngons              0 on anything that gets subdivided, deformed or exported to a game engine
  poles_e3 / poles_e5plus   valence-3 / valence-5+ interior vertices; fine in flat,
                     non-deforming areas, never on lip/lid rims or inside a fold
  valence_6plus      almost always a mistake (pinching, shading artifacts)
  non_manifold_edges / loose_verts / loose_edges    0 unless intentional
  boundary_loops     list of open borders (eye holes, neck cut); unexpected ones = holes
  zero_area_faces, duplicate_verts                 0
  flipped_faces      faces whose normal disagrees with neighbours (inconsistent winding)
  self_intersections face pairs that cross each other (ignores neighbours)
  edge_len_cv        coefficient of variation of edge length. NOT a quality score: studio
                     character retopo measures 0.6 to 0.8 because density is deliberately
                     higher around eyes, mouth and joints. Uniform remeshes read ~0.2 to 0.35.
                     Use it to tell an auto-remesh (low) from a hand-planned layout (high).
  pole density       (poles_e3 + poles_e5plus) / faces: ~2% on a studio head, ~5% on a body
  symmetry_pct       share of vertices with an X-mirror partner (characters: ~100)
  fidelity_*         distance from low-poly verts to the high-poly surface, in scene units
"""

__version__ = "0.1"  # Blender Expert Skills v0.1 (2026-09-24)
import json
import math
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _bm_from(obj, evaluated=False):
    bm = bmesh.new()
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get()
        eo = obj.evaluated_get(dg)
        me = eo.to_mesh()
        bm.from_mesh(me)
        eo.to_mesh_clear()
    else:
        bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    return bm


def _boundary_loops(bm):
    edges = {e for e in bm.edges if e.is_boundary}
    loops = []
    while edges:
        start = edges.pop()
        count, stack = 1, [start]
        while stack:
            e = stack.pop()
            for v in e.verts:
                for n in v.link_edges:
                    if n in edges:
                        edges.remove(n)
                        stack.append(n)
                        count += 1
        loops.append(count)
    return sorted(loops, reverse=True)


def _flipped(bm):
    bad = 0
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        f1, f2 = e.link_faces
        # consistent winding: the shared edge runs in opposite directions in the two faces
        l1 = next(l for l in e.link_loops if l.face == f1)
        l2 = next(l for l in e.link_loops if l.face == f2)
        if l1.vert == l2.vert:
            bad += 1
    return bad


def _self_intersections(bm, limit=200000):
    if len(bm.faces) > limit:
        return None  # too heavy, skip on dense sculpts
    tree = BVHTree.FromBMesh(bm)
    pairs = tree.overlap(tree)
    faces = bm.faces
    n = 0
    for a, b in pairs:
        if a >= b:
            continue
        va = {v.index for v in faces[a].verts}
        if va & {v.index for v in faces[b].verts}:
            continue
        n += 1
    return n


def _symmetry(bm, axis=0, tol=None):
    co = [v.co for v in bm.verts]
    if not co:
        return 0.0
    size = max((max(c[i] for c in co) - min(c[i] for c in co)) for i in range(3)) or 1.0
    tol = tol or size * 1e-3
    from mathutils.kdtree import KDTree
    kd = KDTree(len(co))
    for i, c in enumerate(co):
        kd.insert(c, i)
    kd.balance()
    hit = 0
    for c in co:
        m = c.copy()
        m[axis] = -m[axis]
        _, _, d = kd.find(m)
        if d is not None and d <= tol:
            hit += 1
    return 100.0 * hit / len(co)


def audit(obj, high=None, evaluated=False, symmetry_axis=0, max_listed=25):
    """Return a dict of topology/geometry metrics for a mesh object (world space)."""
    bm = _bm_from(obj, evaluated)
    faces = bm.faces
    tris = sum(1 for f in faces if len(f.verts) == 3)
    quads = sum(1 for f in faces if len(f.verts) == 4)
    ngons = [f.index for f in faces if len(f.verts) > 4]
    val = {}
    poles3, poles5 = [], []
    for v in bm.verts:
        if v.is_boundary or not v.link_faces:
            continue
        k = len(v.link_edges)
        val[k] = val.get(k, 0) + 1
        if k == 3:
            poles3.append(v)
        elif k >= 5:
            poles5.append(v)
    lengths = [e.calc_length() for e in bm.edges]
    mean_len = sum(lengths) / len(lengths) if lengths else 0.0
    cv = (math.sqrt(sum((l - mean_len) ** 2 for l in lengths) / len(lengths)) / mean_len) if mean_len else 0.0
    dup = 0
    if bm.verts:
        from mathutils.kdtree import KDTree
        kd = KDTree(len(bm.verts))
        for v in bm.verts:
            kd.insert(v.co, v.index)
        kd.balance()
        eps = max(mean_len * 1e-3, 1e-6)
        for v in bm.verts:
            if len(kd.find_range(v.co, eps)) > 1:
                dup += 1
    r = {
        "object": obj.name,
        "verts": len(bm.verts), "edges": len(bm.edges), "faces": len(faces),
        "tris_equivalent": sum(len(f.verts) - 2 for f in faces),
        "tris": tris, "quads": quads, "ngons": len(ngons),
        "quads_pct": round(100.0 * quads / len(faces), 2) if faces else 0.0,
        "valence_hist_interior": dict(sorted(val.items())),
        "poles_e3": len(poles3), "poles_e5plus": len(poles5),
        "valence_6plus": sum(c for k, c in val.items() if k >= 6),
        "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary),
        "boundary_loops": _boundary_loops(bm),
        "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
        "loose_edges": sum(1 for e in bm.edges if not e.link_faces),
        "zero_area_faces": sum(1 for f in faces if f.calc_area() < 1e-12),
        "duplicate_verts": dup,
        "flipped_faces": _flipped(bm),
        "self_intersections": _self_intersections(bm),
        "edge_len_mean": round(mean_len, 6), "edge_len_cv": round(cv, 3),
        "symmetry_pct": round(_symmetry(bm, symmetry_axis), 2),
        "dimensions": [round(d, 4) for d in obj.dimensions],
        "ngon_faces_sample": ngons[:max_listed],
        "pole_e5_sample": [[round(c, 4) for c in v.co] for v in poles5[:max_listed]],
        "pole_e3_sample": [[round(c, 4) for c in v.co] for v in poles3[:max_listed]],
    }
    if high is not None:
        r.update(fidelity(bm, high))
    bm.free()
    return r


def fidelity(low_bm_or_obj, high):
    """Distance from each low-poly vertex to the high-poly surface (world space)."""
    own = not isinstance(low_bm_or_obj, bmesh.types.BMesh)
    bm = _bm_from(low_bm_or_obj) if own else low_bm_or_obj
    hb = _bm_from(high, evaluated=True)
    tree = BVHTree.FromBMesh(hb)
    d = []
    for v in bm.verts:
        hit = tree.find_nearest(v.co)
        if hit[0] is not None:
            d.append(hit[3])
    hb.free()
    if own:
        bm.free()
    d.sort()
    if not d:
        return {"fidelity_mean": None}
    size = max(high.dimensions) or 1.0
    return {
        "fidelity_mean": round(sum(d) / len(d), 6),
        "fidelity_p95": round(d[int(0.95 * (len(d) - 1))], 6),
        "fidelity_max": round(d[-1], 6),
        "fidelity_max_pct_of_size": round(100.0 * d[-1] / size, 3),
    }


def verdict(r, deforming=True):
    """Short list of human-readable problems, empty when the mesh is clean."""
    out = []
    if r["ngons"]:
        out.append(f"{r['ngons']} n-gons")
    if deforming and r["quads_pct"] < 95:
        out.append(f"only {r['quads_pct']}% quads")
    if r["valence_6plus"]:
        out.append(f"{r['valence_6plus']} vertices with 6+ edges")
    for k in ("non_manifold_edges", "loose_verts", "loose_edges", "zero_area_faces",
              "duplicate_verts", "flipped_faces"):
        if r[k]:
            out.append(f"{r[k]} {k.replace('_', ' ')}")
    if r.get("self_intersections"):
        out.append(f"{r['self_intersections']} self-intersecting face pairs")
    if r.get("fidelity_max_pct_of_size", 0) > 1.0:
        out.append(f"max deviation from high poly {r['fidelity_max_pct_of_size']}% of size")
    return out


def _cli():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = dict(zip(argv[::2], argv[1::2]))
    obj = bpy.data.objects[args["--object"]]
    high = bpy.data.objects[args["--high"]] if "--high" in args else None
    r = audit(obj, high=high)
    r["problems"] = verdict(r)
    text = json.dumps(r, indent=1)
    if "--json" in args:
        open(args["--json"], "w").write(text)
    print(text)


if __name__ == "__main__":
    _cli()
