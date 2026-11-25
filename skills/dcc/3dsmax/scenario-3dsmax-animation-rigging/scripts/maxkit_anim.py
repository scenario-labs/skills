"""maxkit_anim: measurement and bake helpers for rigs and animation in 3ds Max (pymxs).

channel: batch | bridge | handoff (inline with max_wrap.wrap(code, kit=["maxkit_anim"]))
checked against notes/animation-rigging digests 1 to 3 and
sources/docs (pymxs-using-2027, maxscript-bitmap-values-2027 for the animate and time contexts).

Rules:
- Main thread only. Every function reads the scene except apply_world_samples(), which writes
  keys and must run inside the caller's pymxs.undo block.
- Distances are in system units (check units_report() first). Frames are integers.
- Names marked [verify] are not in the saved docs; they come from expert notes or common use.
- skin_report() needs the Modify panel, so it does not work through 3dsmaxbatch [verify].
"""
import math

import pymxs

rt = pymxs.runtime

BONE_CLASSES = {"BoneGeometry", "Biped_Object", "CATBone", "HubObject", "Dummy", "Point"}  # [verify] class names


def _p3(p):
    return (float(p.x), float(p.y), float(p.z))


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    length = math.sqrt(_dot(a, a)) or 1.0
    return (a[0] / length, a[1] / length, a[2] / length)


def frame_range():
    """Current animation range as (start, end) integer frames."""
    rng = rt.animationRange  # [verify] .start/.end are Time values
    return int(round(float(rng.start.frame))), int(round(float(rng.end.frame)))  # [verify] Time.frame


def units_report():
    return {
        "system_type": str(rt.units.SystemType),  # [verify]
        "system_scale": float(rt.units.SystemScale),  # [verify]
        "frame_rate": int(rt.frameRate),  # [verify]
        "range": frame_range(),
    }


def world_pos(node, frame):
    with pymxs.attime(frame):  # [verify] pymxs twin of MAXScript "at time"
        return _p3(node.transform.position)  # [verify] Matrix3.position


def world_axis(node, frame, axis=0):
    """Unit vector of the node's local X (0), Y (1) or Z (2) axis in world space."""
    with pymxs.attime(frame):  # [verify]
        tm = node.transform
        row = (tm.row1, tm.row2, tm.row3)[axis]  # [verify] Matrix3.row1..row3
        return _norm(_p3(row))


def hierarchy(nodes=None):
    """Roots, depth and class counts of the skeleton-like nodes in the scene."""
    nodes = list(nodes) if nodes is not None else [n for n in rt.objects if str(rt.classOf(n)) in BONE_CLASSES]
    names = {str(n.name) for n in nodes}
    roots, depth, classes, odd_scale = [], {}, {}, []
    for n in nodes:
        classes[str(rt.classOf(n))] = classes.get(str(rt.classOf(n)), 0) + 1
        d, p = 0, n.parent
        while p is not None:
            d += 1
            p = p.parent
        depth[str(n.name)] = d
        if n.parent is None or str(n.parent.name) not in names:
            roots.append(str(n.name))
        s = _p3(n.scale)
        if max(abs(c - 1.0) for c in s) > 1e-3:
            odd_scale.append((str(n.name), s))
    dupes = sorted({x for x in [str(n.name) for n in nodes] if [str(m.name) for m in nodes].count(x) > 1})
    return {"count": len(nodes), "roots": roots, "max_depth": max(depth.values(), default=0),
            "classes": classes, "non_unit_scale": odd_scale, "duplicate_names": dupes}


def height_report(meshes):
    """World bounding-box height of the given meshes at the current frame (system units)."""
    lo, hi = None, None
    for m in meshes:
        mn, mx = _p3(m.min), _p3(m.max)  # [verify] world-space bbox corners
        lo = mn if lo is None else tuple(min(a, b) for a, b in zip(lo, mn))
        hi = mx if hi is None else tuple(max(a, b) for a, b in zip(hi, mx))
    if lo is None:
        return None
    return {"min": lo, "max": hi, "height": hi[2] - lo[2]}


def find_skin(node):
    for mod in node.modifiers:
        if str(rt.classOf(mod)) == "Skin":
            return mod
    return None


def skin_report(node, limit=4, tol=1e-3):
    """Per-vertex influence count, weight sum and unweighted vertices of the node's Skin.

    Every weight above 0 counts as an influence; tol applies to the weight sum only.

    Needs a UI session (bridge or handoff): skinOps reads the modifier shown in the Modify panel.
    """
    skin = find_skin(node)
    if skin is None:
        return {"node": str(node.name), "skin": False}
    rt.select(node)
    rt.execute("max modify mode")  # pymxs has no "max" keyword; run it through MAXScript
    rt.modPanel.setCurrentObject(skin)  # [verify]
    nverts = int(rt.skinOps.GetNumberVertices(skin))  # [verify]
    nbones = int(rt.skinOps.GetNumberBones(skin))  # [verify]
    over, unweighted, bad_sum, used = [], [], [], set()
    for v in range(1, nverts + 1):
        count = int(rt.skinOps.GetVertexWeightCount(skin, v))  # [verify]
        total = 0.0
        live = 0
        for i in range(1, count + 1):
            w = float(rt.skinOps.GetVertexWeight(skin, v, i))  # [verify]
            if w > 0.0:
                live += 1
                used.add(int(rt.skinOps.GetVertexWeightBoneID(skin, v, i)))  # [verify]
            total += w
        if live == 0:
            unweighted.append(v)
        if live > limit:
            over.append(v)
        if live and abs(total - 1.0) > tol:
            bad_sum.append(v)
    bone_names = [str(rt.skinOps.GetBoneName(skin, b, 0)) for b in range(1, nbones + 1)]  # [verify]
    unused = [bone_names[b - 1] for b in range(1, nbones + 1) if b not in used]
    return {"node": str(node.name), "skin": True, "verts": nverts, "bones": nbones,
            "over_limit": len(over), "unweighted": len(unweighted), "bad_sum": len(bad_sum),
            "unused_bones": unused, "first_bad": (over + unweighted + bad_sum)[:20]}


def contact_slide(node, start, end, ground_z=0.0, height_tol=2.0):
    """Foot or hand contact phases and the slide distance inside each phase.

    A frame is in contact when the node is within height_tol of ground_z (system units), above or
    below it.
    """
    phases, current = [], []
    for f in range(start, end + 1):
        p = world_pos(node, f)
        if abs(p[2] - ground_z) <= height_tol:
            current.append((f, p))
        elif current:
            phases.append(current)
            current = []
    if current:
        phases.append(current)
    out = []
    for ph in phases:
        x0, y0 = ph[0][1][0], ph[0][1][1]
        slide = max(math.hypot(p[0] - x0, p[1] - y0) for _, p in ph)
        lift = max(p[2] for _, p in ph) - min(p[2] for _, p in ph)
        out.append({"frames": (ph[0][0], ph[-1][0]), "slide": slide, "height_jitter": lift})
    return out


def pivot_distance_drift(pairs, start, end, step=1):
    """Mechanism invariant: distance between two pivots that a rigid link joins must not change."""
    out = []
    for a, b in pairs:
        d0 = math.dist(world_pos(a, start), world_pos(b, start))
        worst, at = 0.0, start
        for f in range(start, end + 1, step):
            d = math.dist(world_pos(a, f), world_pos(b, f))
            if abs(d - d0) > worst:
                worst, at = abs(d - d0), f
        out.append({"pair": (str(a.name), str(b.name)), "rest": d0, "max_drift": worst, "frame": at})
    return out


def axis_alignment(pairs, start, end, axis=1, step=1):
    """Piston halves must stay coaxial over the range.

    min_abs_dot: smallest |dot| of their aim axes (parallel). max_offset: largest distance from
    b's pivot to a's axis line (same line), in system units.
    """
    out = []
    for a, b in pairs:
        worst, at, offset, off_at = 1.0, start, 0.0, start
        for f in range(start, end + 1, step):
            ua = world_axis(a, f, axis)
            d = abs(_dot(ua, world_axis(b, f, axis)))
            if d < worst:
                worst, at = d, f
            v = _sub(world_pos(b, f), world_pos(a, f))
            along = _dot(v, ua)
            sep = math.sqrt(max(_dot(v, v) - along * along, 0.0))
            if sep > offset:
                offset, off_at = sep, f
        out.append({"pair": (str(a.name), str(b.name)), "min_abs_dot": worst, "frame": at,
                    "max_offset": offset, "offset_frame": off_at})
    return out


def bbox_overlaps(nodes, start, end, step=1, allow=()):
    """Candidate collisions between moving parts: world bounding boxes that overlap.

    Bounding boxes are conservative: confirm each hit with a capture or a mesh test.
    allow lists name pairs that touch by design (parts sharing a pin).
    """
    allowed = {frozenset(p) for p in allow}
    hits = {}
    nodes = list(nodes)
    for f in range(start, end + 1, step):
        with pymxs.attime(f):  # [verify]
            boxes = [(str(n.name), _p3(n.min), _p3(n.max)) for n in nodes]  # [verify]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                na, amin, amax = boxes[i]
                nb, bmin, bmax = boxes[j]
                if frozenset((na, nb)) in allowed:
                    continue
                if all(amin[k] <= bmax[k] and bmin[k] <= amax[k] for k in range(3)):
                    hits.setdefault((na, nb), []).append(f)
    return [{"pair": k, "frames": (v[0], v[-1]), "count": len(v)} for k, v in hits.items()]


def speed_profile(node, start, end):
    """Per-frame speed of a node (camera, root). Smooth motion has a low step-to-step change."""
    pts = [world_pos(node, f) for f in range(start, end + 1)]
    speeds = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    if not speeds:
        return None
    mean = sum(speeds) / len(speeds)
    jumps = [abs(speeds[i + 1] - speeds[i]) for i in range(len(speeds) - 1)]
    return {"mean": mean, "min": min(speeds), "max": max(speeds),
            "max_step_change_ratio": (max(jumps) / mean) if jumps and mean else 0.0,
            "path_length": sum(speeds)}


def loop_gap(nodes, first, last):
    """Pose difference between the first and last frame of a cycle (position and axis drift)."""
    out = []
    for n in nodes:
        dp = math.dist(world_pos(n, first), world_pos(n, last))
        dots = [_dot(world_axis(n, first, k), world_axis(n, last, k)) for k in range(3)]
        out.append({"node": str(n.name), "pos_gap": dp, "min_axis_dot": min(dots)})
    return out


def sample_world(nodes, start, end):
    """World transforms per frame, parents first, for baking before constraints are removed."""
    ordered = sorted(nodes, key=_depth)
    samples = {}
    for f in range(start, end + 1):
        with pymxs.attime(f):  # [verify]
            samples[f] = [(n, rt.copy(n.transform)) for n in ordered]  # [verify] copy of Matrix3
    return samples


def apply_world_samples(samples):
    """Write sampled world transforms as keys. Caller wraps this in pymxs.undo and has
    already replaced constraint controllers with plain PRS controllers."""
    with pymxs.animate(True):  # [verify] pymxs twin of MAXScript "animate on"
        for f in sorted(samples):
            with pymxs.attime(f):  # [verify]
                for n, tm in samples[f]:
                    n.transform = tm


def _depth(n):
    d, p = 0, n.parent
    while p is not None:
        d += 1
        p = p.parent
    return d
