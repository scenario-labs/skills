"""maxkit_uv: UV layout audit for scenario-3dsmax-uv-baking (runs inside 3ds Max).

channel: batch | bridge | handoff (inline with max_wrap(code, kit=["maxkit_uv"]))
checked against notes/uv-baking-texturing digests
        (texel density method from sR1sAWWT2x8, padding rule from 2gv1jYDAoJc,
        overlap and mirrored-UV rules from the Autodesk normal map troubleshooting page).

Entry point:
    uv_audit(node, channel=1, tex_size=2048, target_td=None, tol=0.15,
             raster=1024, min_pad_px=8, min_util=None) -> dict

The analysis half (shell building, texel density, raster coverage, overlap,
padding gap) is pure Python and runs anywhere; only extract_faces() touches pymxs.
pymxs names marked [verify] were not found in the saved docs.
"""

import math
from collections import deque

# 3ds Max system unit names to centimeters (System Unit Setup: 1 unit = scale x type).
UNIT_TO_CM = {
    "inches": 2.54,
    "feet": 30.48,
    "miles": 160934.4,
    "millimeters": 0.1,
    "centimeters": 1.0,
    "meters": 100.0,
    "kilometers": 100000.0,
}


# ----------------------------------------------------------------------------
# pymxs side
# ----------------------------------------------------------------------------

def system_unit_to_cm():
    """Centimeters per system unit."""
    from pymxs import runtime as rt
    unit = str(rt.units.SystemType).lower().lstrip("#")  # [verify] units.SystemType
    scale = float(rt.units.SystemScale)  # [verify] units.SystemScale
    return UNIT_TO_CM[unit] * scale


def extract_faces(node, channel=1):
    """Return (faces, warnings). faces = [(world_area_units2, [map_vert_ids], [(u, v), ...])].

    Works on a temporary Editable Poly copy so the user's stack is untouched;
    the copy is removed before returning. Must run on the main thread.
    """
    from pymxs import runtime as rt
    warnings = []
    s = node.scale
    if abs(s.x - 1) > 1e-4 or abs(s.y - 1) > 1e-4 or abs(s.z - 1) > 1e-4:
        # polyop areas are object space: node scale is not applied.
        warnings.append("node scale is not 1,1,1: run Reset XForm first or areas are wrong")
    tmp = rt.copy(node)
    try:
        rt.convertToPoly(tmp)  # [verify] convertToPoly
        if not rt.polyop.getMapSupport(tmp, channel):  # [verify] polyop.getMapSupport
            return [], warnings + ["map channel %d has no support (no UVs)" % channel]
        faces = []
        nf = rt.polyop.getNumFaces(tmp)  # [verify] polyop.getNumFaces
        for f in range(1, nf + 1):
            area = float(rt.polyop.getFaceArea(tmp, f))  # [verify] polyop.getFaceArea
            ids = [int(i) for i in rt.polyop.getMapFace(tmp, channel, f)]  # [verify] polyop.getMapFace
            uvs = []
            for i in ids:
                p = rt.polyop.getMapVert(tmp, channel, i)  # [verify] polyop.getMapVert
                uvs.append((float(p.x), float(p.y)))
            faces.append((area, ids, uvs))
        return faces, warnings
    finally:
        rt.delete(tmp)


def uv_audit(node, channel=1, tex_size=2048, target_td=None, tol=0.15,
             raster=1024, min_pad_px=8, min_util=None):
    """Audit one node's UV channel. Returns a dict with metrics and findings."""
    faces, warnings = extract_faces(node, channel)
    report = analyze(faces, system_unit_to_cm(), tex_size=tex_size, target_td=target_td,
                     tol=tol, raster=raster, min_pad_px=min_pad_px, min_util=min_util)
    report["node"] = str(node.name)
    report["channel"] = channel
    for w in warnings:
        report["findings"].insert(0, {"severity": "error", "rule": "uv.precondition",
                                      "node": str(node.name), "message": w})
    for f in report["findings"]:
        f["node"] = str(node.name)
    return report


# ----------------------------------------------------------------------------
# pure analysis (no pymxs)
# ----------------------------------------------------------------------------

def signed_area(uvs):
    a = 0.0
    n = len(uvs)
    for i in range(n):
        x1, y1 = uvs[i]
        x2, y2 = uvs[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def build_shells(faces):
    """Union faces that share a map vertex. Returns list of face-index lists."""
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for _, ids, _ in faces:
        for i in ids:
            parent.setdefault(i, i)
        r0 = find(ids[0])
        for i in ids[1:]:
            r = find(i)
            if r != r0:
                parent[r] = r0
    groups = {}
    for fi, (_, ids, _) in enumerate(faces):
        groups.setdefault(find(ids[0]), []).append(fi)
    return list(groups.values())


def texel_density(tex_size, uv_area, world_area_cm2):
    """px/cm for a square texture of tex_size (sR1sAWWT2x8 definition)."""
    if world_area_cm2 <= 0 or uv_area <= 0:
        return 0.0
    return tex_size * math.sqrt(uv_area / world_area_cm2)


def _raster_triangles(tris, res, owner, shell_id, stats):
    for (ax, ay), (bx, by), (cx, cy) in tris:
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-14:
            continue
        x0 = max(int(math.floor(min(ax, bx, cx) * res)), -res)
        x1 = min(int(math.ceil(max(ax, bx, cx) * res)), 2 * res)
        y0 = max(int(math.floor(min(ay, by, cy) * res)), -res)
        y1 = min(int(math.ceil(max(ay, by, cy) * res)), 2 * res)
        for j in range(y0, y1):
            py = (j + 0.5) / res
            for i in range(x0, x1):
                px = (i + 0.5) / res
                w1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d
                w2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d
                w3 = 1.0 - w1 - w2
                if w1 < 0 or w2 < 0 or w3 < 0:
                    continue
                if not (0 <= i < res and 0 <= j < res):
                    stats["outside"] += 1
                    continue
                k = j * res + i
                cur = owner[k]
                if cur == -1:
                    owner[k] = shell_id
                elif cur != shell_id and cur != -2:
                    owner[k] = -2  # cross-shell overlap
                    stats["overlap"] += 1


def min_gap(owner, res):
    """Smallest gap in raster cells between two different shells (BFS, 4-neighbour)."""
    label = list(owner)
    dist = [0 if v >= 0 or v == -2 else -1 for v in owner]
    q = deque(k for k, v in enumerate(owner) if v >= 0)
    best = None
    while q:
        k = q.popleft()
        i, j = k % res, k // res
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if not (0 <= ni < res and 0 <= nj < res):
                continue
            n = nj * res + ni
            if label[n] == -2:
                continue
            if dist[n] == -1:
                dist[n] = dist[k] + 1
                label[n] = label[k]
                q.append(n)
            elif label[n] != label[k] and label[n] >= 0:
                gap = dist[k] + dist[n]  # empty cells between the two shells
                if best is None or gap < best:
                    best = gap
    return best


def analyze(faces, unit_to_cm, tex_size=2048, target_td=None, tol=0.15,
            raster=1024, min_pad_px=8, min_util=None):
    findings = []
    out = {"faces": len(faces), "shells": 0, "findings": findings}
    if not faces:
        findings.append({"severity": "error", "rule": "uv.missing",
                         "message": "no UV faces on this channel"})
        return out
    cm2 = unit_to_cm * unit_to_cm
    shells = build_shells(faces)
    out["shells"] = len(shells)
    flipped = 0
    mirrored = 0
    tds = []
    owner = [-1] * (raster * raster)
    stats = {"outside": 0, "overlap": 0}
    total_world = 0.0
    total_uv = 0.0
    for sid, shell in enumerate(shells):
        w = 0.0
        uv = 0.0
        neg = 0
        tris = []
        for fi in shell:
            area, _, uvs = faces[fi]
            sa = signed_area(uvs)
            if sa < 0:
                neg += 1
            w += area * cm2
            uv += abs(sa)
            for t in range(1, len(uvs) - 1):
                tris.append((uvs[0], uvs[t], uvs[t + 1]))
        flipped += neg
        if neg * 2 > len(shell):
            mirrored += 1
        total_world += w
        total_uv += uv
        tds.append((texel_density(tex_size, uv, w), w, sid))
        _raster_triangles(tris, raster, owner, sid, stats)

    covered = sum(1 for v in owner if v != -1)
    out["coverage_pct"] = round(100.0 * covered / (raster * raster), 2)
    out["overlap_pct"] = round(100.0 * stats["overlap"] / (raster * raster), 3)
    out["outside_0_1_samples"] = stats["outside"]
    out["flipped_faces"] = flipped
    out["mirrored_shells"] = mirrored
    out["world_area_cm2"] = round(total_world, 2)
    out["td_object"] = round(texel_density(tex_size, total_uv, total_world), 3)
    vals = sorted(t[0] for t in tds if t[1] > 0)
    if vals:
        out["td_min"] = round(vals[0], 3)
        out["td_max"] = round(vals[-1], 3)
        out["td_median"] = round(vals[len(vals) // 2], 3)
    gap = min_gap(owner, raster)
    out["min_gap_tex_px"] = None if gap is None else round(gap * tex_size / raster, 1)

    ref = target_td or out.get("td_median", 0.0)
    outliers = []
    for td, w, sid in tds:
        if ref and w > 0 and abs(td - ref) / ref > tol:
            outliers.append({"shell": sid, "td": round(td, 3), "world_cm2": round(w, 1)})
    outliers.sort(key=lambda o: -abs(o["td"] - ref))
    out["td_outliers"] = outliers[:20]
    out["td_outlier_count"] = len(outliers)

    if stats["overlap"]:
        findings.append({"severity": "error", "rule": "uv.overlap",
                         "message": "%.3f%% of the sheet has overlapping shells (bake target needs none, unless mirrored halves are offset on purpose)" % out["overlap_pct"]})
    if stats["outside"]:
        findings.append({"severity": "warning", "rule": "uv.outside_0_1",
                         "message": "UVs outside 0-1 (fine for UDIM or tiling, wrong for a single-tile bake)"})
    if flipped:
        findings.append({"severity": "warning", "rule": "uv.flipped",
                         "message": "%d flipped UV faces, %d mirrored shells: check tangent-space seams" % (flipped, mirrored)})
    if outliers:
        findings.append({"severity": "warning", "rule": "uv.texel_density",
                         "message": "%d shells deviate more than %d%% from %.2f px/cm" % (len(outliers), int(tol * 100), ref)})
    if gap is not None and out["min_gap_tex_px"] < min_pad_px:
        findings.append({"severity": "warning", "rule": "uv.padding",
                         "message": "closest shells %.1f px apart at %d px (want >= %d)" % (out["min_gap_tex_px"], tex_size, min_pad_px)})
    if min_util is not None and out["coverage_pct"] < min_util:
        findings.append({"severity": "info", "rule": "uv.utilization",
                         "message": "UV coverage %.1f%% below %.0f%%" % (out["coverage_pct"], min_util)})
    return out
