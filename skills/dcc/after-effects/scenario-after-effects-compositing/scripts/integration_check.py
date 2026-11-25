#!/usr/bin/env python3
"""integration_check.py: is an element lit, shadowed and finished like the plate it sits in?

Exact calls (all images the same size, PNG frames rendered from After Effects):

  python3 integration_check.py --comp COMP.png --plate PLATE.png \\
      --elem ELEM.png --matte MATTE.png --neutral NEUTRAL.png \\
      [--shadow SHADOW.png] [--sun X,Y] \\
      [--plate-shadow X,Y,W,H --plate-lit X,Y,W,H] [--plate-length RATIO] [--object-height PX] \\
      [--light back|side|front] [--rendered [--comp-rim]] [--no-shadow "REASON"]
      [--ground-shadow X,Y,W,H] [--ground-albedo 0.35]
      [--only light,shade,rim,density,hue,length,softness,contact,finish,material] [--out RESULT.json]

  python3 integration_check.py --selftest DIR      builds planted frames in DIR and runs every gate on them

Inputs
  --comp      the composite frame
  --plate     the plate alone, same frame (element and shadow layers off)
  --elem      the element alone over black, as lit in the composite (RGBA or RGB)
  --matte     the element's matte (alpha, or a gray alpha view); omitted: the alpha of --elem
  --neutral   the same element under flat light: the cutout before any relight, or the 3D model under ambient light only
  --shadow    the shadow layers alone as a matte (cast and contact combined); omitted: derived from comp / plate
              outside the element (darkening of the ground), reported as shadowSource "derived". Give it whenever the
              plate itself is derived from the composite (a registered or cleaned frame): the derived core then takes
              in every residual difference (a strip of the base read as shadow, density 0.585 on one such frame)
  --sun       the source in frame px, may lie outside the frame (x < 0, y < 0); omitted: centroid of the plate's
              brightest 0.5 %
  --plate-shadow, --plate-lit  two boxes on the plate: ground inside one of the plate's own cast shadows, and the
              same ground in the light beside it (density and hue gates)
  --plate-length  cast shadow length over object height for an object of the plate, measured by the agent
  --object-height the element's height in px when the matte's bounding box does not give it (a lying object)
  --no-shadow     the element casts no shadow inside the frame (held in the air, shadow off frame): the five shadow
              gates report "na" with the reason, and they do not count as skipped
  --rendered  the element's shading comes from a 3D render and --neutral is the same model under ambient light only
              (white, 100 %: the base color). The rim is then read, not gated: a sun 20 deg behind the view axis gives a
              physical rim 0.03 to 0.04 of the radius wide, below the width set on a keyed relight
  --comp-rim  with --rendered: a rim layer was added in the comp over the render; only its inner hardness is gated.
              The script cannot tell a rendered rim from a comp rim on the pixels; this flag says which
  --ground-shadow  a box on the plate's shadowed ground for the exposure reading; omitted: --plate-shadow
  --ground-albedo  that ground's albedo (default 0.35, concrete)
  --elem may be the composite itself when the element is opaque in its core: light and shade read only the core

Gates (value, limit, pass; values 0-1 unless stated)
  light     ratio = luma(elem) / luma(neutral) inside the matte core, plane fit: the gradient points to the light on
            screen. Albedo divides out. --light side: angle to the source <= 45 deg, change across the element >= 0.15.
            --light back: a sun behind the subject lights the edge facing it and the sky lights the top, so the
            gradient lies between the source's screen direction and straight up. Pass: <= 30 deg beyond that sector,
            change >= 0.15 (a rendered element may show none: sky and ground bounce balance), the core's center
            (0.6 of the largest distance to the edge or more) over the edge band facing the source <= 1.1, and, for a
            source clearly left or right, the far-side edge band over the source-side band <= 1.3. Lambert spheres and
            lying cylinders, sun 10 to 70 deg from straight behind, sky over sun 0.2 to 1, a ground bounce, read at
            most 26 deg beyond, 1.00 and 1.27. Within about 40 deg of straight behind the gradient points up and
            cannot tell left from right; the rim and the route carry that.
  shade     the third of the element facing away from the source over the third facing it (split along the source
            direction), mean of the ratio image. Pass: <= 0.75. Rendered under back light: a reading (the sun reaches
            only the edge, both thirds sit in sky light; Lambert references read 0.48 to 1.02).
  rim       back light: the ratio profiled inward from the edge points facing the source. Pass: peak over the core
            median >= 2.0 (one stop: sun on the edge against sky fill on the body; outdoors 3 to 8 times), half width
            at half maximum >= 0.12 of the local radius (half the chord inward), and inner hardness (largest 1 px
            drop of the normalized profile) <= 0.15. A stroke or halo is narrow and hard and fails; light on a
            turning surface is wide and fades. The band medians (1.5 % of the element) are reported as readings.
  --light   back (default: the source is behind the subject, as a sun in frame), side (rim reported, not gated), or
            front (the source behind the camera: light passes when the relight added no side light, strength < 0.15)
  density   cast shadow core: luma(comp) / luma(plate). Plate: luma(shadow box) / luma(lit box). Pass: gap <= 0.10.
  hue       blue-to-red shift of the cast shadow against the plate's own shadow. Pass: |ln gap| <= 0.10.
  length    cast length / object height against --plate-length. Pass: within 30 %. A shadow that leaves the frame
            gives a lower bound: it passes when the bound reaches 70 % of the expected length, or when the expected
            tip lies outside the frame and the shadow reaches the frame edge.
  softness  edge width of the cast shadow in its far third over its near third. Pass: >= 1.3.
  contact   worst gap in px between a resting column's lowest row and the shadow (pass <= 2), and darkening beyond the
            resting footprint on the side the shadow does not fall, over the element width (pass <= 0.04).
  material  in linear light, the light on the shade third (composite / neutral, per channel) for each material
            (five chroma clusters of the neutral, 2 % of the third or more). One light gives one value for every
            material. Pass: largest over smallest, worst channel, <= 4.0. A cream cap rendered olive-gray beside a
            fabric at the right level fails (6.3); a relight, a fitted plate and the planted sphere read 1.1 to 2.8.
  finish    element blacks (1st percentile luma) against the plate's blacks in the element's rows (pass: not below by
            more than 0.02); element edge width against the plate's sharpest edges near it (pass: >= 0.8 times).
            With --rendered, a ground box (--ground-shadow or --plate-shadow) and --plate: the neutral is an albedo, so
            a dark material may sit below the ground's darkest pixel. Plate reference: its black in a band from just
            above the base to 0.3 of the element below it (the subject's distance or closer, with its occlusion
            shadows). Crushed (fail): more than 0.02 below that black and either over 0.5 % of the core clipped at
            black or the 1st percentile of the light on albedo 0.05 or more under 0.05 of the shade light. Milky
            (fail), for a darkest albedo of 0.1 or less: above that albedo in full light (--plate-lit) plus the
            plate's near black, by more than 0.02. The value is then elemBlack minus plateBlackNear, a reading;
            blacksPass decides. Renders of dark and light albedo on grounds 0.2 to 0.6, hazy or clear, 2 m and 8 m,
            all pass (the plate-rows rule failed 20 of 36); a crushed and a milky render fail.

Readings (never gates)
  exposure  factor = the shade side's light (as above, luma) over the plate's shadowed ground light (linear luma of
            --ground-shadow over --ground-albedo). 1 means the shade side gets what the shadowed ground gets. It
            cannot gate: the ground's albedo (0.2 to 0.4 for concrete) and the shade side's orientation against the
            ground (about 0.5 to 1.2) each move it by up to 2x, the size of the error it would look for. For a keyed
            photograph the neutral's exposure is arbitrary, so the factor has no absolute meaning there.
            shadeHue = ln(B/R) of that light, groundShadowHue the same on the shadowed ground read as gray,
            groundShadowVsLitHue how much bluer the plate's shadow is than its sunlit ground.

For a keyed photograph there is no second render: the neutral is the keyed foreground before any relight, so light
and shade measure what the relight added, not the light baked into the photograph. The reading route reads that baked
light on the neutral alone, valid there because it is one photograph under one light. The core is split into five
chroma clusters and each pixel's luma is divided by its cluster's median (albedo out). The brightest 2 % of that
shading gives the highlight. On a rounded object the diffuse peak sits at sin(angle) of the radius from the center, so
angleFromCamera = asin(highlight offset over the half extent). The plate's source, from --light: front <= 45 deg from
the camera axis, side 90, back >= 135. Then route.gap = plate bound minus the foreground angle. Above 90 deg the
photograph's lit side has to become its shade side, the hard case for a relight (its baked highlights stay). The verdict
is then "plate": prefer a plate lit from the foreground's side, and relight in full when the plate is imposed. Otherwise
"relight". A reading, never a gate.

Prints one JSON object. Exit 0: every gate run passed. Exit 1: a gate failed. Exit 2: no gate failed but some were
skipped for a missing input (listed in "skipped").
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image

RIMQ = 0.5
PLATE_ANGLE = {"front": 45.0, "side": 90.0, "back": 135.0}   # bound of the plate source angle from the camera axis
ROUTE_GAP = 90.0
LIMITS = {"lightAngle": 45.0, "lightStrength": 0.15, "shade": 0.75, "density": 0.10, "hue": 0.10,
          "lengthTol": 0.30, "softness": 1.3, "gap": 2.0, "overhang": 0.04, "black": 0.02, "edge": 0.8, "rim": 2.0, "rimWidth": 0.12, "rimHard": 0.15,
          "material": 4.0, "backSector": 30.0, "faceOverEdge": 1.1, "sideOverSun": 1.3, "occFloor": 0.05, "darkAlbedo": 0.1, "clipShare": 0.005}


def rgb(path):
    im = Image.open(path)
    return np.asarray(im.convert("RGB"), np.float32) / 255.0


def matte_of(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA"):
        a = np.asarray(im.getchannel("A"), np.float32) / 255.0
        if a.min() < 0.999:
            return a
    return np.asarray(im.convert("RGB"), np.float32)[..., 0] / 255.0


def luma(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def box_sum(m, r):
    p = np.pad(m.astype(np.float64), r + 1, mode="edge")
    c = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return s[:m.shape[0], :m.shape[1]]


def dilate(mask, r):
    return box_sum(mask, r) > 0 if r > 0 else mask.copy()


def erode(mask, r):
    return box_sum(mask, r) >= (2 * r + 1) ** 2 - 1e-6 if r > 0 else mask.copy()


def blur(a, r, n=3):
    for _ in range(n):
        a = box_sum(a, r) / (2 * r + 1) ** 2
    return a.astype(np.float32)


def sample(img, xs, ys):
    h, w = img.shape
    xs = np.clip(xs, 0, w - 1.001)
    ys = np.clip(ys, 0, h - 1.001)
    x0, y0 = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fx, fy = xs - x0, ys - y0
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def edge_widths(img, pts, normals, reach=8, min_step=0.06):
    """Width of a step across each point along its normal: |step| / steepest 1 px change. 1.0 = a razor edge."""
    out = []
    offs = np.arange(-reach, reach + 1, 1.0)
    for (y, x), (ny, nx) in zip(pts, normals):
        prof = sample(img, x + offs * nx, y + offs * ny)
        step = abs(prof[:4].mean() - prof[-4:].mean())
        g = np.abs(np.diff(prof)).max()
        if step >= min_step and g > 1e-6:
            out.append(step / g)
    return out


def r3(v):
    return None if v is None else round(float(v), 3)


def gate(value, limit, ok, **extra):
    d = {"value": r3(value) if isinstance(value, (int, float, np.floating, np.integer)) else value, "limit": limit, "pass": bool(ok)}
    d.update(extra)
    return d


def skip(reason):
    return {"pass": None, "skipped": reason}


def boxmean(img, spec):
    x, y, w, h = [int(float(v)) for v in spec.split(",")]
    return img[y:y + h, x:x + w].reshape(-1, img.shape[-1]).mean(0) if img.ndim == 3 else img[y:y + h, x:x + w].mean()


def rim_profile(m, ratio, d, med, rng):
    """Profile of the ratio inward from the edge points facing the source: half width at half maximum (px), that width
    over the local radius (half the chord inward), and inner-edge hardness (largest 1 px drop of the normalized profile
    after its peak; a stroke drops at once, light on a turning surface fades)."""
    gy, gx = np.gradient(blur(m, 2))
    gn = np.hypot(gx, gy) + 1e-9
    iny, inx = gy / gn, gx / gn                                  # inward: alpha rises inside
    face = -(inx * d[0] + iny * d[1])                           # outward normal toward the source
    mb = m > 0.5
    pts = np.argwhere((((m > 0.4) & (m < 0.6)) | (mb & ~erode(mb, 1))) & (face > 0.6))
    if len(pts) > 400:
        pts = pts[rng.choice(len(pts), 400, replace=False)]
    widths, rel, hard, peaks = [], [], [], []
    for y, x in pts:
        ny, nx = iny[y, x], inx[y, x]
        steps = np.arange(0, 400, 1.0)
        ms = sample(m, x + steps * nx, y + steps * ny)
        out = np.nonzero(ms[3:] < 0.5)[0]
        chord = (out[0] + 3) if out.size else 400
        D = int(min(120, max(chord, 6)))
        dd = np.arange(2, D, 1.0)
        prof = sample(ratio, x + dd * nx, y + dd * ny)
        if prof.size < 6:
            continue
        top = int(np.argmax(prof[:max(3, len(prof) // 2)]))
        pk = prof[top]
        if pk - med < 0.2 * med:
            continue
        pn = (prof - med) / (pk - med)
        below = np.nonzero(pn[top:] < 0.5)[0]
        if not below.size:
            continue
        hw = float(top + below[0])
        widths.append(hw)
        peaks.append(pk / max(med, 1e-4))
        rel.append(hw / max(chord / 2.0, 1.0))
        seg = pn[top:min(len(pn), top + below[0] + 6)]
        hard.append(float(np.max(seg[:-1] - seg[1:])) if seg.size > 1 else 1.0)
    if not widths:
        return None
    return {"points": len(widths), "halfWidthPx": r3(np.median(widths)), "widthOverRadius": r3(np.median(rel)),
            "innerHardness": r3(np.median(hard)), "peakOverCore": r3(np.median(peaks))}


def srgb_lin(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def chroma_clusters(img, k=5):
    """k-means on chromaticity plus half the luma: one label per material (seeded, repeatable)."""
    c = np.c_[img / np.maximum(img.sum(1, keepdims=True), 1e-4), 0.5 * luma(img)[:, None]]
    cen = c[np.random.default_rng(0).choice(len(c), k, replace=False)]
    for _ in range(20):
        lab = np.argmin(((c[:, None] - cen[None]) ** 2).sum(-1), 1)
        cen = np.array([c[lab == j].mean(0) if (lab == j).any() else cen[j] for j in range(k)])
    return lab


def baked_light(img, core, cx, cy, ext, k=5):
    """Light baked into one photograph: shading = luma over its chroma cluster's median, highlight offset, plane fit."""
    lum = luma(img)
    ok = core & (lum > 0.03)
    yy, xx = np.nonzero(ok)
    if xx.size < 200:
        return None
    v = lum[ok]
    c = img[ok] / np.maximum(img[ok].sum(1, keepdims=True), 1e-4)
    cen = c[np.random.default_rng(0).choice(len(c), k, replace=False)]
    for _ in range(20):
        lab = np.argmin(((c[:, None] - cen[None]) ** 2).sum(-1), 1)
        cen = np.array([c[lab == j].mean(0) if (lab == j).any() else cen[j] for j in range(k)])
    sh = np.ones_like(v)
    for j in range(k):
        sel = lab == j
        if sel.any():
            sh[sel] = v[sel] / max(np.median(v[sel]), 1e-4)
    gv = np.linalg.lstsq(np.c_[xx - cx, yy - cy, np.ones_like(xx, float)], sh, rcond=None)[0][:2]
    hi = sh >= np.quantile(sh, 0.98)
    hx, hy = xx[hi].mean() - cx, yy[hi].mean() - cy
    off = min(1.0, math.hypot(hx, hy) / (ext / 2))
    return {"highlightOffset": r3(off), "highlightDir": [r3(hx / (math.hypot(hx, hy) + 1e-9)), r3(hy / (math.hypot(hx, hy) + 1e-9))],
            "angleFromCamera": round(math.degrees(math.asin(off)), 1), "shadingStrength": r3(np.linalg.norm(gv) * ext),
            "shadingContrast": r3(np.quantile(sh, 0.9) / max(np.quantile(sh, 0.1), 1e-4))}


def footprint(m):
    """Resting columns: lowest matte row within 5 % of the element height of its lowest row (middle 80 % of width)."""
    ys, xs = np.nonzero(m)
    top, bot, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    mg = (x1 - x0) // 10
    pts = []
    for x in range(x0 + mg, x1 - mg + 1):
        col = np.nonzero(m[:, x])[0]
        if col.size and col.max() >= bot - 0.05 * (bot - top):
            pts.append((col.max(), x))
    return np.array(pts, float), (top, bot, x0, x1)


def run(a):
    res = {"inputs": {k: v for k, v in vars(a).items() if v is not None and k not in ("selftest",)}, "limits": LIMITS}
    comp = rgb(a.comp)
    H, W = comp.shape[:2]
    m = matte_of(a.matte or a.elem) if (a.matte or a.elem) else None
    plate = rgb(a.plate) if a.plate else None
    elem = rgb(a.elem) if a.elem else None
    neutral = rgb(a.neutral) if a.neutral else None
    only = set(a.only.split(",")) if a.only else None
    g = {}
    if m is None:
        res["error"] = "no matte: give --matte or an RGBA --elem"
        print(json.dumps(res))
        return 1
    mb = m > 0.5
    ys, xs = np.nonzero(mb)
    cy, cx = ys.mean(), xs.mean()
    ext = max(ys.max() - ys.min(), xs.max() - xs.min()) + 1
    core = erode(m > 0.98, max(2, int(0.03 * ext)))
    res["element"] = {"centroid": [round(cx, 1), round(cy, 1)], "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                      "corePx": int(core.sum())}

    # source direction on screen
    if a.sun:
        sx, sy = [float(v) for v in a.sun.split(",")]
        src = "given"
    elif plate is not None:
        lp = luma(plate)
        t = np.quantile(lp, 0.995)
        yy, xx = np.nonzero(lp >= t)
        sx, sy, src = xx.mean(), yy.mean(), "plate brightest 0.5 %"
    else:
        sx = sy = None
        src = None
    d = None
    if sx is not None:
        d = np.array([sx - cx, sy - cy])
        d = d / (np.linalg.norm(d) + 1e-9)
        res["source"] = {"xy": [round(sx, 1), round(sy, 1)], "from": src, "screenDir": [round(d[0], 3), round(d[1], 3)]}

    # 1, 2: light direction and shade side, from the ratio as lit / neutral
    if only is None or only & {"light", "shade", "rim"}:
        if elem is None or neutral is None or d is None:
            g["light"] = g["shade"] = g["rim"] = skip("needs --elem, --neutral and a source (--sun or --plate)")
        else:
            le, ln = luma(elem), luma(neutral)
            ok = core & (ln > 0.03)
            ratio = np.where(ok, le / np.maximum(ln, 1e-4), 0)
            yy, xx = np.nonzero(ok)
            rv = ratio[ok]
            A = np.c_[xx - cx, yy - cy, np.ones_like(xx, float)]
            coef = np.linalg.lstsq(A, rv, rcond=None)[0]
            gv = coef[:2]
            proj = (xx - cx) * d[0] + (yy - cy) * d[1]
            span = proj.max() - proj.min()
            strength = np.linalg.norm(gv) * span / max(rv.mean(), 1e-4)
            ang = math.degrees(math.acos(np.clip(np.dot(gv / (np.linalg.norm(gv) + 1e-12), d), -1, 1)))
            g["light"] = gate(ang, LIMITS["lightAngle"], ang <= LIMITS["lightAngle"] and strength >= LIMITS["lightStrength"],
                              strength=r3(strength), strengthLimit=LIMITS["lightStrength"],
                              ratioDir=[r3(gv[0] / (np.linalg.norm(gv) + 1e-12)), r3(gv[1] / (np.linalg.norm(gv) + 1e-12))],
                              ratioMean=r3(rv.mean()))
            facing, away = rv[proj > proj.max() - span / 3], rv[proj < proj.min() + span / 3]
            # rim: the opaque edge band facing the source, against the core (albedo divided out)
            op = m > 0.98
            bw = max(3, int(0.015 * ext))
            band = op & ~erode(op, bw) & (ln > 0.03)
            mgy, mgx = np.gradient(blur(m, 2))
            outn = -(mgx * d[0] + mgy * d[1]) / (np.hypot(mgx, mgy) + 1e-9)
            rat_all = le / np.maximum(ln, 1e-4)
            fb, ab = band & (outn > 0.5), band & (outn < -0.5)
            med = np.median(rv)
            rim_f = np.quantile(rat_all[fb], RIMQ) / max(med, 1e-4) if fb.sum() > 20 else None
            rim_a = np.quantile(rat_all[ab], RIMQ) / max(med, 1e-4) if ab.sum() > 20 else None
            sh = away.mean() / max(facing.mean(), 1e-4) if facing.size and away.size else None
            g["shade"] = gate(sh, LIMITS["shade"], sh is not None and sh <= LIMITS["shade"],
                              facingMean=r3(facing.mean() if facing.size else None), awayMean=r3(away.mean() if away.size else None))
            res["rimProfile"] = rim_profile(m, np.where(op & (ln > 0.03), rat_all, med), d, med, np.random.default_rng(1))
            rp = res["rimProfile"]
            if rp is None:
                g["rim"] = gate(None, LIMITS["rim"], False, note="no edge point facing the source carries light above the core")
            else:
                okr = (rp["peakOverCore"] >= LIMITS["rim"] and rp["widthOverRadius"] >= LIMITS["rimWidth"]
                       and rp["innerHardness"] <= LIMITS["rimHard"])
                g["rim"] = gate(rp["peakOverCore"], LIMITS["rim"], okr, widthOverRadius=rp["widthOverRadius"],
                                widthLimit=LIMITS["rimWidth"], innerHardness=rp["innerHardness"], hardLimit=LIMITS["rimHard"],
                                bandFacing=r3(rim_f), bandAway=r3(rim_a),
                                note="profile inward from the edge facing the source: peak over core, half width over local radius, hardness")
            if a.light == "back":
                # back light: the gradient lies between the source's screen direction and straight up (sun crescent
                # plus sky on the top), and the silhouette's center is no brighter than its edge facing the source
                gn = gv / (np.linalg.norm(gv) + 1e-12)
                sa = math.degrees(math.atan2(d[0] * gn[1] - d[1] * gn[0], d @ gn))          # source to gradient
                su = math.degrees(math.atan2(-d[0], -d[1]))                                  # source to screen up
                if sa * su >= 0 and abs(sa) <= abs(su):
                    beyond = 0.0
                elif sa * su >= 0:
                    beyond = abs(sa) - abs(su)
                else:
                    beyond = abs(sa)
                dist = np.zeros(m.shape, np.float32)
                cur, k9, step = op.copy(), 0, max(1, int(ext / 200))
                while cur.any():
                    dist[cur] = k9
                    cur = erode(cur, step)
                    k9 += step
                inner = op & (dist >= 0.6 * dist.max()) & (ln > 0.03)
                fe = band & (outn > 0.5)
                face = (float(np.median(rat_all[inner]) / max(np.median(rat_all[fe]), 1e-4))
                        if inner.sum() > 20 and fe.sum() > 20 else None)
                # side: the edge on the far side over the edge on the source's side, read only for a source clearly left or right
                ox = -mgx / (np.hypot(mgx, mgy) + 1e-9) * np.sign(d[0])
                ss, os_ = band & (ox > 0.5), band & (ox < -0.5)
                side = (float(np.median(rat_all[os_]) / max(np.median(rat_all[ss]), 1e-4))
                        if abs(d[0]) >= 0.5 and ss.sum() > 20 and os_.sum() > 20 else None)
                weak = strength < LIMITS["lightStrength"]
                side_ok = side is None or side <= LIMITS["sideOverSun"]
                dir_ok = beyond <= LIMITS["backSector"] or (weak and a.rendered)
                face_ok = face is None or face <= LIMITS["faceOverEdge"]
                str_ok = not weak or a.rendered
                g["light"] = gate(r3(beyond), LIMITS["backSector"], dir_ok and face_ok and side_ok and str_ok, angleToSource=r3(ang),
                                  sourceToUp=r3(su), sourceToGradient=r3(sa), strength=r3(strength),
                                  strengthLimit=LIMITS["lightStrength"], faceOverEdge=r3(face), faceLimit=LIMITS["faceOverEdge"],
                                  farSideOverSourceSide=r3(side), sideLimit=LIMITS["sideOverSun"],
                                  ratioDir=[r3(gn[0]), r3(gn[1])], ratioMean=r3(rv.mean()),
                                  note="back light: degrees beyond the sector from the source's screen direction to straight "
                                       "up; center over the edge facing the source; far-side edge over source-side edge; a rendered "
                                       "element may show no gradient")
                if a.rendered:
                    g["shade"]["note"] = "rendered, back light: a reading (the sun reaches only the edge; both thirds sit in sky light)"
                    g["shade"]["pass"] = None
                    g["shade"]["na"] = "rendered back light: shade read, not gated"
            if a.light == "front":
                st = np.linalg.norm(gv) * span / max(rv.mean(), 1e-4)
                g["light"] = gate(st, LIMITS["lightStrength"], st < LIMITS["lightStrength"],
                                  note="front light: the relight must add no side light; the baked light is the reading bakedLight")
                g["shade"] = {"pass": None, "na": "front light"}
                g["rim"] = {"pass": None, "na": "front light"}
            if a.rendered and a.light != "front":
                rg = g["rim"]
                rg["note"] = ("rendered: peak and width are readings (a physical rim is as wide as the sun's angle "
                              "behind the subject gives)")
                if a.comp_rim and rp is not None:
                    rg["pass"] = bool(rp["innerHardness"] <= LIMITS["rimHard"])
                    rg["note"] += "; --comp-rim: a rim layer added in the comp, gated on inner hardness only"
                else:
                    rg["pass"] = None
                    rg["na"] = "rendered: rim read, not gated (no --comp-rim)"
            elif a.light == "side":
                g["rim"]["note"] += "; side light: reported, gated only for back light"
                g["rim"]["pass"] = None
                g["rim"]["na"] = "side light"
            bl = baked_light(neutral, core, cx, cy, ext)
            if bl is not None:
                gap = PLATE_ANGLE[a.light] - bl["angleFromCamera"]
                res["route"] = dict(bl, plateLight=a.light, plateAngleBound=PLATE_ANGLE[a.light], gap=round(gap, 1),
                                    verdict="plate" if gap > ROUTE_GAP else "relight",
                                    note="reading on the neutral alone: above %d deg choose or generate the plate" % ROUTE_GAP)
            # readings only: luma plane fits confounded by albedo
            for name, img in (("bakedLight", ln), ("litLumaNoRatio", le)):
                c2 = np.linalg.lstsq(A, img[ok], rcond=None)[0][:2]
                a2 = math.degrees(math.acos(np.clip(np.dot(c2 / (np.linalg.norm(c2) + 1e-12), d), -1, 1)))
                res[name] = {"angleToSource": round(a2, 1), "dir": [r3(c2[0] / (np.linalg.norm(c2) + 1e-12)), r3(c2[1] / (np.linalg.norm(c2) + 1e-12))],
                             "note": "reading only: albedo moves it"}

    # shadow matte
    s = None
    if a.shadow:
        s = matte_of(a.shadow)
        res["shadowSource"] = "given"
    elif plate is not None:
        rr = luma(comp) / np.maximum(luma(plate), 1e-3)
        s = np.clip(1 - rr, 0, 1) * (~dilate(mb, 2))
        s[s < 0.03] = 0
        res["shadowSource"] = "derived"
    sn = None
    if s is not None and (s > 0).sum() > 50:
        pk = np.quantile(s[s > 0], 0.99)
        sn = np.clip(s / max(pk, 1e-4), 0, 1) * (~dilate(mb, 1))
    fp, (top, bot, x0, x1) = footprint(mb)
    objh = float(a.object_height) if a.object_height else float(bot - top + 1)
    elem_w = float(x1 - x0 + 1)
    u = None
    if sn is not None:
        sy_, sx_ = np.nonzero(sn > 0.25)
        wts = sn[sy_, sx_]
        fc = fp.mean(0)
        u = np.array([(sx_ * wts).sum() / wts.sum() - fc[1], (sy_ * wts).sum() / wts.sum() - fc[0]])
        u = u / (np.linalg.norm(u) + 1e-9)
        res["shadow"] = {"dir": [r3(u[0]), r3(u[1])], "px": int((sn > 0.25).sum())}

    # 3, 4: density and hue
    if only is None or "density" in only or "hue" in only:
        if sn is None or plate is None or not (a.plate_shadow and a.plate_lit):
            g["density"] = g["hue"] = skip("needs --plate, a shadow (given or derived) and --plate-shadow/--plate-lit boxes")
        else:
            sc = sn > 0.8
            if sc.sum() < 20:
                sc = sn > 0.5
            lc, lpl = luma(comp)[sc], luma(plate)[sc]
            dens = np.median(lc / np.maximum(lpl, 1e-3))
            ps, pl = boxmean(plate, a.plate_shadow), boxmean(plate, a.plate_lit)
            pdens = luma(ps[None, None])[0, 0] / max(luma(pl[None, None])[0, 0], 1e-4)
            g["density"] = gate(abs(dens - pdens), LIMITS["density"], abs(dens - pdens) <= LIMITS["density"],
                                cast=r3(dens), plate=r3(pdens), corePx=int(sc.sum()))
            cc, pc = comp[sc].mean(0), plate[sc].mean(0)
            cast_shift = (cc[2] / max(cc[0], 1e-4)) / (pc[2] / max(pc[0], 1e-4))
            plate_shift = (ps[2] / max(ps[0], 1e-4)) / (pl[2] / max(pl[0], 1e-4))
            hg = abs(math.log(cast_shift / plate_shift))
            g["hue"] = gate(hg, LIMITS["hue"], hg <= LIMITS["hue"], castBRshift=r3(cast_shift), plateBRshift=r3(plate_shift))

    # 5, 6: length and softness
    lengthinfo = None
    if sn is not None and u is not None:
        sy_, sx_ = np.nonzero(sn > 0.25)
        start = (fp[:, 1] * u[0] + fp[:, 0] * u[1]).mean()
        projs = sx_ * u[0] + sy_ * u[1]
        L = projs.max() - start
        edge = sn > 0.25
        clipped = bool(edge[:2].any() or edge[-2:].any() or edge[:, :2].any() or edge[:, -2:].any())
        lengthinfo = (start, L, projs, sy_, sx_, clipped)
    if only is None or "length" in only:
        if lengthinfo is None or not a.plate_length:
            g["length"] = skip("needs a shadow and --plate-length")
        else:
            start, L, _, _, _, clipped = lengthinfo
            ratio = L / objh
            exp = float(a.plate_length)
            if clipped:
                fc = fp.mean(0)
                tip = (fc[1] + u[0] * exp * objh, fc[0] + u[1] * exp * objh)
                tip_out = not (0 <= tip[0] < W and 0 <= tip[1] < H)
                ok = ratio >= exp * (1 - LIMITS["lengthTol"]) or tip_out
                g["length"] = gate(ratio, exp, ok, clipped=True, expectedTipOutside=tip_out,
                                   note="lower bound: the shadow reaches the frame edge")
            else:
                ok = abs(ratio / exp - 1) <= LIMITS["lengthTol"]
                g["length"] = gate(ratio, exp, ok, clipped=False, tolerance=LIMITS["lengthTol"])
    if only is None or "softness" in only:
        if lengthinfo is None:
            g["softness"] = skip("needs a shadow (--shadow, or --plate to derive it)")
        else:
            start, L, _, _, _, _ = lengthinfo
            yy, xx = np.mgrid[0:H, 0:W]
            pr = (xx * u[0] + yy * u[1] - start) / max(L, 1)
            hard = sn > 0.5
            bnd = hard & ~erode(hard, 1)
            band = (sn > 0.15) & (sn < 0.85)
            wd = []
            for lo, hi in ((0.0, 0.33), (0.67, 1.01)):
                z = (pr >= lo) & (pr < hi)
                nb = (bnd & z).sum()
                wd.append(band[z].sum() / nb if nb > 10 else None)
            ok = None not in wd and wd[1] / max(wd[0], 1e-3) >= LIMITS["softness"]
            g["softness"] = gate(wd[1] / max(wd[0], 1e-3) if None not in wd else None, LIMITS["softness"], ok,
                                 nearWidthPx=r3(wd[0]), farWidthPx=r3(wd[1]))
            if lengthinfo[5]:
                g["softness"]["note"] = "far third measured up to the frame edge"

    # 7: contact
    if only is None or "contact" in only:
        if sn is None or u is None:
            g["contact"] = skip("needs a shadow (--shadow, or --plate to derive it)")
        else:
            sfull = np.clip(s / max(np.quantile(s[s > 0], 0.99), 1e-4), 0, 1)
            gaps = []
            for yb, x in fp[::2]:
                yb, x = int(yb), int(x)
                col = np.nonzero(sfull[max(yb - 3, 0):, x] > 0.5)[0]
                if col.size:
                    gaps.append(col[0] - min(3, yb))
            gap = max(gaps) if gaps else None
            near = (sn > 0.25) & dilate(np.zeros_like(mb) | _pts_mask(fp, H, W), max(4, int(0.12 * objh)))
            ny, nx = np.nonzero(near)
            back = -u
            over = ((nx * back[0] + ny * back[1]).max() - (fp[:, 1] * back[0] + fp[:, 0] * back[1]).max()) if nx.size else 0.0
            over = max(over, 0.0) / elem_w
            ok = gap is not None and gap <= LIMITS["gap"] and over <= LIMITS["overhang"]
            g["contact"] = gate(gap, LIMITS["gap"], ok, overhang=r3(over), overhangLimit=LIMITS["overhang"],
                                columns=len(gaps), note="gap in px under resting columns; overhang beyond the footprint against the shadow direction, over element width")

    # 8: blacks and edges
    if only is None or "finish" in only:
        ref = plate if plate is not None else comp
        lc = luma(comp)
        eblack = np.quantile(lc[core], 0.01)
        rows = np.zeros_like(mb)
        rows[top:bot + 1] = True
        rows &= ~dilate(mb, 3)
        if sn is not None:
            rows &= ~(sn > 0.1)
        pblack = np.quantile(luma(ref)[rows], 0.002)
        # element edge: profiles across the matte boundary in the composite
        mbl = blur(m, 1)
        gy, gx = np.gradient(mbl)
        bpts = np.argwhere((m > 0.3) & (m < 0.7) | (mb & ~erode(mb, 1)))
        rng = np.random.default_rng(0)
        if len(bpts) > 600:
            bpts = bpts[rng.choice(len(bpts), 600, replace=False)]
        nrm = np.array([(gy[y, x], gx[y, x]) for y, x in bpts])
        nn = np.linalg.norm(nrm, axis=1) + 1e-9
        keep = nn > 1e-3
        ew = edge_widths(lc, bpts[keep], -(nrm[keep] / nn[keep, None]))
        # plate: sharpest edges in a ring around the element (same depth)
        lr = luma(ref)
        ring = dilate(mb, max(8, int(0.25 * ext))) & ~dilate(mb, 6)
        if sn is not None:
            ring &= ~(sn > 0.1)
        py, px = np.gradient(lr)
        mag = np.hypot(px, py) * ring
        thr = np.quantile(mag[ring], 0.98) if ring.sum() > 100 else 0
        ppts = np.argwhere(mag >= max(thr, 1e-6))
        if len(ppts) > 600:
            ppts = ppts[rng.choice(len(ppts), 600, replace=False)]
        pn = np.array([(py[y, x], px[y, x]) for y, x in ppts]) if len(ppts) else np.zeros((0, 2))
        pw = edge_widths(lr, ppts, pn / (np.linalg.norm(pn, axis=1)[:, None] + 1e-9)) if len(ppts) else []
        e_med = float(np.median(ew)) if ew else None
        p_sharp = float(np.quantile(pw, 0.2)) if pw else None
        ok_b = eblack >= pblack - LIMITS["black"]
        ok_e = e_med is not None and p_sharp is not None and e_med >= LIMITS["edge"] * p_sharp
        fval, extra = eblack - pblack, {"blacksRule": "plate rows"}
        gbox = a.ground_shadow or a.plate_shadow
        if a.rendered and neutral is not None and gbox and plate is not None:
            # a render on the ground: its blacks follow its own darkest albedo in the plate's light, so a navy part
            # may sit below the ground's darkest pixel. Floor: below both the plate's black at the subject's distance
            # or closer (a band from just above the base to 0.3 of the element below it, with its occlusion shadows)
            # and that albedo in the shade light at an occlusion of 0.1: crushed. Ceiling, for a dark material:
            # above that albedo in full light plus the plate's near black (haze and ground): milky.
            band = np.zeros_like(mb)
            band[max(0, bot - int(0.1 * ext)):min(H, bot + int(0.3 * ext) + 1)] = True
            band &= ~dilate(mb, 3)
            if sn is not None:
                band &= ~(sn > 0.1)
            plin = srgb_lin(ref)
            bp = float(srgb_lin(np.array(np.quantile(luma(ref)[band], 0.002)))) if band.sum() > 50 else float(srgb_lin(np.array(pblack)))
            dk = core & (lc <= eblack + 1e-6)
            a1 = float(np.median(luma(srgb_lin(neutral[dk]))))
            es = float(luma(boxmean(plin, gbox))) / a.ground_albedo
            el = float(luma(boxmean(plin, a.plate_lit))) / a.ground_albedo if a.plate_lit else None
            enc = lambda v: float(np.where(v <= 0.0031308, 12.92 * v, 1.055 * max(v, 0) ** (1 / 2.4) - 0.055))
            cl8 = luma(srgb_lin(comp[core]))
            nl8 = luma(srgb_lin(neutral[core]))
            lit_ok = nl8 >= 0.05
            q_light = float(np.quantile(cl8[lit_ok] / nl8[lit_ok], 0.01)) / es if lit_ok.sum() > 50 else None
            clip = float((lc[core] <= 1.5 / 255).mean())
            floor = enc(bp)
            crushed = eblack < floor - LIMITS["black"] and (clip > LIMITS["clipShare"] or (q_light is not None and q_light < LIMITS["occFloor"]))
            ceil = enc(a1 * el + bp) if el is not None and a1 <= LIMITS["darkAlbedo"] else None
            ok_b = not crushed and (ceil is None or eblack <= ceil + LIMITS["black"])
            fval = eblack - floor
            extra = {"blacksRule": "albedo (rendered)", "plateBlackNear": r3(enc(bp)), "elemAlbedoAtBlack": r3(a1),
                     "groundShadeLight": r3(es), "groundLitLight": r3(el), "blackFloor": r3(floor), "blackCeiling": r3(ceil),
                     "clippedShare": r3(clip), "darkLightOverShade": r3(q_light)}
        g["finish"] = gate(r3(fval), -LIMITS["black"], ok_b and ok_e, elemBlack=r3(eblack), plateBlack=r3(pblack),
                           blacksPass=bool(ok_b), elemEdgePx=r3(e_med), plateSharpEdgePx=r3(p_sharp), edgeFactor=LIMITS["edge"],
                           edgesPass=bool(ok_e), edgeSamples=[len(ew), len(pw)], **extra)

    # 9: material (gate), exposure and shade color (readings), in linear light, on the composite inside the core
    if (only is None or "material" in only) and neutral is not None:
        cl, nl = srgb_lin(comp[core]), srgb_lin(neutral[core])
        yy9, xx9 = np.nonzero(core)
        if d is not None and a.light != "front":
            pj = (xx9 - cx) * d[0] + (yy9 - cy) * d[1]
            shd = pj < pj.min() + (pj.max() - pj.min()) / 3
        else:
            shd = np.ones(len(xx9), bool)
        nlum = luma(nl)
        lab = chroma_clusters(neutral[core])
        mats = []
        for j in range(5):
            sel = (lab == j) & shd & (nlum > 0.02)
            if sel.sum() < max(100, 0.02 * shd.sum()):
                continue
            ech = []
            for ch in range(3):
                okc = sel & (nl[:, ch] > 0.02)
                ech.append(float(np.median(cl[okc, ch] / nl[okc, ch])) if okc.sum() > 100 else None)
            mats.append({"px": int(sel.sum()), "neutral": [r3(v) for v in np.median(neutral[core][sel], 0)],
                         "light": [r3(v) for v in ech]})
        spread = None
        for ch in range(3):
            vals = [mt["light"][ch] for mt in mats if mt["light"][ch] is not None]
            if len(vals) >= 2:
                sp = max(vals) / max(min(vals), 1e-4)
                spread = sp if spread is None else max(spread, sp)
        if spread is None:
            g["material"] = {"pass": None, "na": "one material on the shade side"}
        else:
            g["material"] = gate(r3(spread), LIMITS["material"], spread <= LIMITS["material"], materials=mats,
                                 note="light per channel (composite / neutral, linear) per material on the shade side; "
                                      "one light gives one value for every material")
        # exposure: shade-side light against the plate's shadowed ground over its stated albedo
        sel = shd & (nlum > 0.02)
        e_sh = float(np.median(luma(cl[sel]) / nlum[sel])) if sel.sum() > 100 else None
        gbox = a.ground_shadow or a.plate_shadow
        if gbox and plate is not None and e_sh is not None:
            gs = boxmean(srgb_lin(plate), gbox)
            e_ground = float(luma(gs)) / a.ground_albedo
            expo = {"shadeLight": r3(e_sh), "groundShadowLight": r3(e_ground), "groundAlbedo": a.ground_albedo,
                    "factor": r3(e_sh / max(e_ground, 1e-4)),
                    "note": "reading: 1 = the shade side gets the light of the plate's shadowed ground; the ground's "
                            "albedo (0.2 to 0.4 for concrete) and the shade side's orientation (0.5 to 1.2) each move "
                            "it by up to 2x"}
            sh_rgb = [float(np.median(cl[sel & (nl[:, ch] > 0.02), ch] / nl[sel & (nl[:, ch] > 0.02), ch])) for ch in range(3)]
            expo["shadeHue"] = r3(math.log(max(sh_rgb[2], 1e-4) / max(sh_rgb[0], 1e-4)))
            expo["groundShadowHue"] = r3(math.log(max(gs[2], 1e-4) / max(gs[0], 1e-4)))
            if a.plate_lit:
                gl = boxmean(srgb_lin(plate), a.plate_lit)
                expo["groundShadowVsLitHue"] = r3(math.log((max(gs[2], 1e-4) / max(gl[2], 1e-4)) / (max(gs[0], 1e-4) / max(gl[0], 1e-4))))
            expo["hueNote"] = ("ln(B/R) of the light on the shade side (composite / neutral) against the plate's shadowed "
                               "ground read as gray; groundShadowVsLitHue is how much bluer the plate's shadow is than its light")
            res["exposure"] = expo
        elif e_sh is not None:
            res["exposure"] = {"shadeLight": r3(e_sh), "note": "no ground box (--ground-shadow or --plate-shadow)"}

    if a.no_shadow:
        for k in ("density", "hue", "length", "softness", "contact"):
            if k in g:
                g[k] = {"pass": None, "na": a.no_shadow}
    res["gates"] = g
    failed = [k for k, v in g.items() if v.get("pass") is False]
    skipped = [k for k, v in g.items() if v.get("pass") is None and "na" not in v]
    res["failed"], res["skipped"] = failed, skipped
    res["verdict"] = "fail" if failed else ("incomplete" if skipped else "pass")
    txt = json.dumps(res, default=float)
    if a.out:
        with open(a.out, "w") as f:
            f.write(txt + "\n")
    print(txt)
    return 1 if failed else (2 if skipped else 0)


def _pts_mask(pts, H, W):
    mk = np.zeros((H, W), bool)
    mk[pts[:, 0].astype(int).clip(0, H - 1), pts[:, 1].astype(int).clip(0, W - 1)] = True
    return mk


# ---------------------------------------------------------------- planted inputs
def _save(path, a):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def _scene(variant):
    """A sphere on a textured ground, sun low on the left behind the scene. One plate post with its own shadow.
    variant: good, frontlit, pale, neutralhue, short, uniform, wide, crushed, stroke, offcolor."""
    W, H = 960, 540
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sun = (-80.0, 170.0)
    hz = 200
    plate = np.zeros((H, W, 3), np.float32)
    sky = np.clip(1 - np.hypot(xx - sun[0], yy - sun[1]) / 900, 0, 1)[..., None]
    plate[:] = np.array([0.95, 0.62, 0.35]) * (0.45 + 0.55 * sky)
    tex = blur(rng.random((H, W)).astype(np.float32), 2, 2)
    ground = (np.array([0.78, 0.62, 0.48]) * (0.75 + 0.25 * (tex[..., None] - 0.5) * 4)).astype(np.float32)
    ground *= (0.85 + 0.15 * (yy[..., None] - hz) / (H - hz))
    cracks = (np.abs(np.sin(xx * 0.05 + yy * 0.013)) < 0.012) & (yy > hz + 20)
    ground[cracks] = [0.02, 0.02, 0.02]
    plate[yy > hz] = ground[yy > hz]
    sun_px = np.hypot(xx - 30, yy - (hz - 15)) < 22
    plate[sun_px] = [1, 0.97, 0.85]
    u = np.array([0.93, 0.37])
    u = u / np.linalg.norm(u)
    shade_tint = np.array([0.42, 0.45, 0.56])      # plate shadow: luma ratio about 0.45, bluer than the lit ground

    def soft_shadow(hard, base, length, near_r, far_r):
        t = np.clip(((xx - base[0]) * u[0] + (yy - base[1]) * u[1]) / length, 0, 1)
        a = blur(hard.astype(np.float32), near_r)
        b = blur(hard.astype(np.float32), far_r)
        return a * (1 - t) + b * t

    # plate post: 120 px tall at x 760, shadow 2.2 x its height
    post_base = (760.0, 330.0)
    post_h = 120.0
    ps = np.zeros((H, W), bool)
    for k in np.linspace(0, 2.2 * post_h, 400):
        cx, cy = post_base[0] + u[0] * k, post_base[1] + u[1] * k
        ps |= np.hypot(xx - cx, yy - cy) < 14
    ps_soft = soft_shadow(ps, post_base, 2.2 * post_h, 1, 6)
    plate = plate * (1 - ps_soft[..., None] * (1 - shade_tint))
    plate[(np.abs(xx - post_base[0]) < 6) & (yy < post_base[1]) & (yy > post_base[1] - post_h)] = [0.05, 0.04, 0.04]
    plate = np.stack([blur(plate[..., c], 1, 2) for c in range(3)], -1)

    # the element: a sphere resting at (430, 400), radius 80; cream on its right (away from the sun), red elsewhere
    c = (430.0, 320.0)
    R = 80.0
    dx, dy = (xx - c[0]) / R, (yy - c[1]) / R
    inside = dx ** 2 + dy ** 2 < 1
    nz = np.sqrt(np.clip(1 - dx ** 2 - dy ** 2, 0, 1))
    cream = (dx > 0.1) & (dy < 0.35)                                         # a red band runs under the cream side
    alb = np.where(cream[..., None], np.array([0.92, 0.86, 0.74]), np.array([0.82, 0.18, 0.12])).astype(np.float32)
    alb[(dy < -0.55) & (np.abs(dx) < 0.35)] = [0.02, 0.02, 0.05]           # a black button on top
    neutral = alb * 0.8
    if variant == "frontlit":
        L = np.array([0.15, -0.35, 0.92])
    else:
        L = np.array([-0.78, -0.25, -0.57])                                  # left, a little up, behind the subject
    L = L / np.linalg.norm(L)
    ndl = np.clip(dx * L[0] + dy * L[1] + nz * L[2], 0, 1)
    sunc = np.array([1.0, 0.8, 0.55])
    lit = alb * (0.18 * np.array([0.75, 0.75, 0.85]) + 0.95 * ndl[..., None] * sunc)
    if variant == "offcolor":                                                # cream rendered at 0.15 of its albedo  
        lit = np.where(cream[..., None], lit * 0.15, lit)
    if variant == "stroke":                                                  # a weaker falloff plus a hard 4 px outline
        lit = alb * (0.18 * np.array([0.75, 0.75, 0.85]) + 0.6 * ndl[..., None] * sunc)
        ring = inside & (np.hypot(dx, dy) > 1 - 4 / R) & (dx * L[0] + dy * L[1] > 0.2)
        lit[ring] = (alb * sunc * 1.1)[ring]
    if variant != "crushed":
        lit = 0.05 + lit * 0.95                                              # blacks lifted to the plate's floor
    matte = inside.astype(np.float32)
    if variant != "crushed":
        matte = blur(matte, 1, 2)                                            # edge softness of the plate
    contact = (c[0], c[1] + R)
    # cast shadow of the sphere: an elongated ellipse from the contact away from the sun
    sl = 2.2 * 2 * R
    if variant == "short":
        sl *= 0.35
    vx, vy = xx - contact[0], yy - contact[1]
    along = vx * u[0] + vy * u[1]
    across = -vx * u[1] + vy * u[0]
    hard = ((along - sl / 2) / (sl / 2)) ** 2 + (across / (0.75 * R)) ** 2 < 1
    near_r, far_r = (6, 6) if variant == "uniform" else (1, 7)
    s = soft_shadow(hard, contact, sl, near_r, far_r)
    if variant == "wide":                                                    # a flat ellipse, wider than the footprint, below it
        ex = ((xx - contact[0] + 40) / (1.5 * R)) ** 2 + ((yy - contact[1] - 9) / 10) ** 2 < 1
        s = np.maximum(s * (yy > contact[1] + 3), blur(ex.astype(np.float32), 3))
    else:                                                                    # contact occlusion: as wide as the resting footprint
        occ = ((xx - contact[0]) / (0.42 * R)) ** 2 + ((yy - contact[1] + 3) / 12) ** 2 < 1
        s = np.maximum(s, blur(occ.astype(np.float32), 1))
    s *= 1 - matte
    tint = shade_tint.copy()
    if variant == "pale":
        tint = np.array([0.72, 0.8, 0.96])                                  # paler, same blue shift as the plate's shadow
    if variant == "neutralhue":
        g0 = luma(shade_tint[None, None])[0, 0]
        tint = np.array([g0, g0, g0])
    comp = plate * (1 - s[..., None] * (1 - tint))
    comp = comp * (1 - matte[..., None]) + lit * matte[..., None]
    elem = lit * matte[..., None]
    return {"comp": comp, "plate": plate, "elem": elem, "neutral": neutral * matte[..., None], "matte": matte, "shadow": s,
            "sun": "%d,%d" % sun, "plate_shadow": "%d,%d,8,8" % (post_base[0] + u[0] * 150 - 4, post_base[1] + u[1] * 150 - 4),
            "plate_lit": "%d,%d,8,8" % (post_base[0] + u[0] * 150 - 4 + 30 * u[1], post_base[1] + u[1] * 150 - 4 - 30 * u[0]), "plate_length": 2.2,
            "object_height": 2 * R}


def _physical(shape, theta, phi, sky, tilt, yaw, bounce=0.3, size=(360, 240)):
    """Lambert reference by construction: a sphere or a lying capsule, orthographic camera tilted down by tilt deg,
    sun at theta deg from straight behind the subject and phi deg of screen azimuth, a hemispherical sky (sky over
    sun irradiance) and a ground bounce. Returns encoded elem, neutral (albedo under white ambient), matte, sun dir."""
    W, H = size
    tl, th, ph = math.radians(tilt), math.radians(theta), math.radians(phi)
    U = np.array([0, -math.cos(tl), math.sin(tl)])
    L = np.array([math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), -math.cos(th)])
    if math.degrees(math.asin(float(np.clip(L @ U, -1, 1)))) < 0:
        return None
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    o = np.stack([(xs - W / 2) / 75.0, (ys - H / 2) / 75.0, np.full(xs.shape, 5.0, np.float32)], -1)
    if shape == "sphere":
        def sdf(q):
            return np.linalg.norm(q, axis=-1) - 1.0
    else:
        right = np.array([1.0, 0, 0])
        fwd = np.cross(U, right)
        fwd /= np.linalg.norm(fwd)
        ax = math.cos(math.radians(yaw)) * right + math.sin(math.radians(yaw)) * fwd

        def sdf(q):
            t = np.clip(q @ ax, -1.3, 1.3)
            return np.linalg.norm(q - t[..., None] * ax, axis=-1) - 0.6
    t = np.zeros(xs.shape, np.float32)
    hit = np.zeros(xs.shape, bool)
    for _ in range(100):
        q = o.copy()
        q[..., 2] -= t
        dd = sdf(q)
        hit |= dd < 1e-4
        t = np.where(hit, t, np.minimum(t + np.maximum(dd, 1e-4), 10.0))
    hit &= t < 9
    q = o.copy()
    q[..., 2] -= t
    e = 1e-3
    nrm = np.stack([sdf(q + np.array([e, 0, 0])) - sdf(q - np.array([e, 0, 0])), sdf(q + np.array([0, e, 0])) - sdf(q - np.array([0, e, 0])),
                    sdf(q + np.array([0, 0, e])) - sdf(q - np.array([0, 0, e]))], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-12
    nu = nrm @ U
    irr = np.clip(nrm @ L, 0, None) + sky * (1 + nu) / 2 + bounce * (max(0.0, float(L @ U)) + sky) * (1 - nu) / 2
    alb = 0.6

    def enc(x):
        x = np.clip(x, 0, 1)
        return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)
    elem = np.repeat((enc(alb * irr) * hit)[..., None], 3, -1)
    neutral = np.repeat((enc(np.full(irr.shape, alb)) * hit)[..., None], 3, -1)
    return elem, neutral, hit.astype(np.float32), (float(L[0]), float(L[1]))


def _ground_scene(g, albedo, haze, far, W=640, H=400):
    """Blacks reference by construction: a sphere resting on textured ground (albedo g, cracks at occlusion 0.05, a cast
    shadow box) under sun and sky; the sphere carries cavities at occlusion 0.25 and a contact occlusion. Haze adds
    x * t + 0.55 * (1 - t), t = exp(-distance / 15.7 m). Near: 2 m from the camera, far: 8 m. Linear in, encoded out."""
    rng = np.random.default_rng(7)
    f, h, y0 = 300.0, 1.6, 120
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    D = 15.7 if haze else 1e9
    t = np.exp(-np.where(ys > y0 + 0.5, f * h / np.maximum(ys - y0, 0.5), 1e3) / D)
    sky, sun_up = 0.35, 0.55
    tex = 0.8 + 0.4 * rng.random((H, W)).astype(np.float32)
    tex = (tex + np.roll(tex, 1, 0) + np.roll(tex, 1, 1)) / 3
    occ = np.ones((H, W), np.float32)
    for _ in range(120):
        yc, xc, n, an = rng.integers(y0 + 10, H), rng.integers(0, W), rng.integers(10, 60), rng.random() * math.pi
        for k in range(n):
            yy, xx = int(yc + k * math.sin(an)), int(xc + k * math.cos(an))
            if y0 < yy < H and 0 <= xx < W:
                occ[yy, xx] = 0.05
    shade = (xs > 30) & (xs < 140) & (ys > 330) & (ys < 380)
    plate = np.where(ys > y0, g * tex * np.where(shade, sky, sky + sun_up) * occ, 0.75 + 0.1 * (1 - ys / y0))
    plate = plate * t + 0.55 * (1 - t) * (ys > y0)
    zb = 8.0 if far else 2.0
    R = 0.45 * f / zb
    cx, cy = W * 0.6, y0 + f * h / zb - R
    dx, dy = (xs - cx) / R, (ys - cy) / R
    inside = dx ** 2 + dy ** 2 < 1
    nz = np.sqrt(np.clip(1 - dx ** 2 - dy ** 2, 0, 1))
    Lv = np.array([-0.5, -sun_up, 0.65])
    Lv /= np.linalg.norm(Lv)
    irr = (np.clip(dx * Lv[0] + dy * Lv[1] + nz * Lv[2], 0, None) * sun_up / -Lv[1] + sky * (1 - dy) / 2
           + g * (sun_up + sky) * (1 + dy) / 2) * (1 - 0.6 * np.exp(-(1 - dy) / 0.15))
    irr = np.where(rng.random((H, W)) < 0.04, irr * 0.25, irr)
    alb = {"dark": np.full((H, W), 0.02), "light": np.full((H, W), 0.5)}.get(albedo, np.where(dy > 0.1, 0.02, 0.45))
    zt = math.exp(-zb / D)
    el = alb * irr * zt + 0.55 * (1 - zt)

    def enc(x):
        x = np.clip(x, 0, 1)
        return np.repeat(np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)[..., None], 3, -1).astype(np.float32)
    return {"comp": enc(np.where(inside, el, plate)), "plate": enc(plate), "elem": enc(el * inside), "neutral": enc(alb * inside),
            "matte": inside.astype(np.float32), "plate_shadow": "40,335,90,40", "plate_lit": "180,335,90,40"}


def selftest(d):
    os.makedirs(d, exist_ok=True)
    expect = {"good": [], "frontlit": ["light", "shade", "rim"], "pale": ["density"], "neutralhue": ["hue"], "short": ["length"],
              "uniform": ["softness"], "wide": ["contact"], "crushed": ["finish"], "stroke": ["rim"], "offcolor": ["material"],
              "stroke rendered": [], "stroke rendered comp-rim": ["rim"]}
    rows, ok_all = [], True
    for v, should in expect.items():
        base_v = v.split(" ")[0]
        sc = _scene(base_v)
        paths = {}
        for k in ("comp", "plate", "elem", "neutral", "matte", "shadow"):
            paths[k] = os.path.join(d, "%s_%s.png" % (base_v, k))
            _save(paths[k], sc[k])
        ns = argparse.Namespace(comp=paths["comp"], plate=paths["plate"], elem=paths["elem"], matte=paths["matte"],
                                neutral=paths["neutral"], shadow=paths["shadow"], sun=sc["sun"], plate_shadow=sc["plate_shadow"],
                                plate_lit=sc["plate_lit"], plate_length=sc["plate_length"], object_height=sc["object_height"],
                                only=None, no_shadow=None, light="back", out=os.path.join(d, "%s.json" % v.replace(" ", "_")),
                                selftest=None, rendered="rendered" in v, comp_rim="comp-rim" in v, ground_shadow=None,
                                ground_albedo=0.35)
        saved = sys.stdout
        with open(os.devnull, "w") as sink:
            sys.stdout = sink
            try:
                run(ns)
            finally:
                sys.stdout = saved
        with open(ns.out) as f:
            r = json.load(f)
        got = sorted(r["failed"])
        good = got == sorted(should)
        ok_all &= good
        rows.append({"variant": v, "expectedFail": should, "failed": got, "asExpected": good,
                     "values": {k: g.get("value") for k, g in r["gates"].items()}})
    # route reading: the lit renders read as photographs, back light from the limb, front light from the face
    route = {}
    for v, back in (("good", True), ("frontlit", False)):
        el, mt = rgb(os.path.join(d, "%s_elem.png" % v)), rgb(os.path.join(d, "%s_matte.png" % v))[..., 0]
        ys, xs = np.nonzero(mt > 0.5)
        ext = max(np.ptp(ys), np.ptp(xs)) + 1
        bl = baked_light(el, erode(mt > 0.98, max(2, int(0.03 * ext))), xs.mean(), ys.mean(), ext)
        good = bl is not None and (bl["angleFromCamera"] >= 45) == back
        ok_all &= good
        route[v] = {"angleFromCamera": bl and bl["angleFromCamera"], "expected": ">= 45" if back else "< 45", "asExpected": good}
    # physical references: correct by construction, every one must pass the light gate under back light;
    # a low side sun declared on the mirrored side, or the render flipped upside down, must fail it
    # (within about 40 degrees of straight behind the gradient points up and cannot tell left from right)
    def light_of(tag, el, ne, mt, sdir):
        for k, im in (("elem", el), ("neutral", ne), ("matte", mt)):
            _save(os.path.join(d, "%s_%s.png" % (tag, k)), im)
        ys, xs = np.nonzero(mt > 0.5)
        sn = np.array(sdir) / (np.hypot(*sdir) + 1e-9)
        ns = argparse.Namespace(comp=os.path.join(d, tag + "_elem.png"), plate=None, elem=os.path.join(d, tag + "_elem.png"),
                                matte=os.path.join(d, tag + "_matte.png"), neutral=os.path.join(d, tag + "_neutral.png"),
                                shadow=None, sun="%.1f,%.1f" % (xs.mean() + 3000 * sn[0], ys.mean() + 3000 * sn[1]),
                                plate_shadow=None, plate_lit=None, plate_length=None, object_height=None, only="light",
                                no_shadow=None, light="back", out=os.path.join(d, tag + ".json"), selftest=None,
                                rendered=True, comp_rim=False, ground_shadow=None, ground_albedo=0.35)
        saved = sys.stdout
        with open(os.devnull, "w") as sink:
            sys.stdout = sink
            try:
                run(ns)
            finally:
                sys.stdout = saved
        with open(ns.out) as f:
            return json.load(f)["gates"]["light"]

    phys, wrong, n_ok, worst = [], [], 0, {"beyond": 0.0, "faceOverEdge": 0.0, "farSideOverSourceSide": 0.0}
    for shape, yaw in (("sphere", 0), ("capsule", 0), ("capsule", 45), ("capsule", 80)):
        for theta in (10, 20, 40, 70):
            for phi in (-90, -135, -45, 180):
                for sky in (0.2, 0.5, 1.0):
                    sc = _physical(shape, theta, phi, sky, 7, yaw)
                    if sc is None:
                        continue
                    tag = "phys_%s%d_%d_%d_%s" % (shape, yaw, theta, phi, sky)
                    lg = light_of(tag, *sc)
                    n_ok += bool(lg["pass"])
                    if lg["strength"] >= LIMITS["lightStrength"]:
                        worst["beyond"] = max(worst["beyond"], lg["value"])
                    worst["faceOverEdge"] = max(worst["faceOverEdge"], lg.get("faceOverEdge") or 0)
                    worst["farSideOverSourceSide"] = max(worst["farSideOverSourceSide"], lg.get("farSideOverSourceSide") or 0)
                    if not lg["pass"]:
                        phys.append({"case": tag, "light": lg})
                    if theta == 70 and phi == -135 and sky == 0.5 and yaw in (0, 45):
                        el, ne, mt, (sx, sy) = sc
                        for kind, args in (("mirrored", (el, ne, mt, (-sx, sy))), ("flipped", (el[::-1], ne[::-1], mt[::-1], (sx, sy)))):
                            lw = light_of("wrong_%s_%s%d" % (kind, shape, yaw), *args)
                            wrong.append({"case": "%s %s%d" % (kind, shape, yaw), "beyond": lw["value"], "failed": not lw["pass"]})
    ok_all &= not phys and bool(wrong) and all(w["failed"] for w in wrong)

    # blacks: dark and light renders on grounds of albedo 0.2, 0.35, 0.6, with and without haze, near and far, must
    # pass; the same render with crushed blacks, or with milky blacks on a dark material over a plate with true blacks,
    # must fail
    def blacks_of(tag, sc):
        for k in ("comp", "plate", "elem", "neutral", "matte"):
            _save(os.path.join(d, "%s_%s.png" % (tag, k)), sc[k])
        ns = argparse.Namespace(**{k: os.path.join(d, "%s_%s.png" % (tag, k)) for k in ("comp", "plate", "elem", "neutral", "matte")},
                                shadow=None, sun=None, plate_shadow=sc["plate_shadow"], plate_lit=sc["plate_lit"], plate_length=None,
                                object_height=None, only="finish", no_shadow=None, light="back", out=os.path.join(d, tag + ".json"),
                                selftest=None, rendered=True, comp_rim=False, ground_shadow=None, ground_albedo=0.35)
        saved = sys.stdout
        with open(os.devnull, "w") as sink:
            sys.stdout = sink
            try:
                run(ns)
            finally:
                sys.stdout = saved
        with open(ns.out) as f:
            return json.load(f)["gates"]["finish"]

    bl_bad, bl_n, planted = [], 0, []
    for gg in (0.2, 0.35, 0.6):
        for alb in ("dark", "light", "mixed"):
            for hz in (0, 1):
                for far in (False, True):
                    tag = "blk_%s_%s_%s_%s" % (gg, alb, "haze" if hz else "clear", "far" if far else "near")
                    fz = blacks_of(tag, _ground_scene(gg, alb, hz, far))
                    bl_n += 1
                    if not fz["blacksPass"]:
                        bl_bad.append({"case": tag, "finish": fz})
    sc = _ground_scene(0.35, "mixed", 0, False)
    sc["comp"] = np.where(sc["matte"][..., None] > 0.5, np.clip((sc["comp"] - 0.12) / 0.88, 0, 1), sc["comp"])
    planted.append(("crushed", blacks_of("blk_crushed", sc)))
    sc = _ground_scene(0.35, "dark", 0, False)
    sc["comp"] = np.where(sc["matte"][..., None] > 0.5, sc["comp"] * 0.7 + 0.3, sc["comp"])
    planted.append(("milky", blacks_of("blk_milky", sc)))
    planted_rows = [{"case": k, "elemBlack": fz["elemBlack"], "floor": fz.get("blackFloor"), "ceiling": fz.get("blackCeiling"),
                     "failed": not fz["blacksPass"]} for k, fz in planted]
    ok_all &= not bl_bad and all(r["failed"] for r in planted_rows)
    print(json.dumps({"selftest": rows, "route": route, "physical": {"cases": n_ok + len(phys), "failed": phys, "worst": worst},
                      "wrongSide": wrong,
                      "blacks": {"cases": bl_n, "failed": bl_bad, "planted": planted_rows}, "pass": bool(ok_all)}))
    return 0 if ok_all else 1


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--comp")
    p.add_argument("--plate")
    p.add_argument("--elem")
    p.add_argument("--matte")
    p.add_argument("--neutral")
    p.add_argument("--shadow")
    p.add_argument("--sun")
    p.add_argument("--plate-shadow")
    p.add_argument("--plate-lit")
    p.add_argument("--plate-length")
    p.add_argument("--object-height")
    p.add_argument("--only")
    p.add_argument("--no-shadow")
    p.add_argument("--light", choices=["back", "side", "front"], default="back")
    p.add_argument("--rendered", action="store_true")
    p.add_argument("--comp-rim", action="store_true")
    p.add_argument("--ground-shadow")
    p.add_argument("--ground-albedo", type=float, default=0.35)
    p.add_argument("--out")
    p.add_argument("--selftest")
    # "--sun -80,170": argparse on some Python versions reads a value that starts with a minus sign as a flag
    argv = list(sys.argv[1:] if argv is None else argv)
    merged, i = [], 0
    while i < len(argv):
        nxt = argv[i + 1] if i + 1 < len(argv) else ""
        if argv[i] in ("--sun", "--plate-shadow", "--plate-lit", "--ground-shadow") and re.match(r"^-\d", nxt):
            merged.append(argv[i] + "=" + nxt)
            i += 2
        else:
            merged.append(argv[i])
            i += 1
    a = p.parse_args(merged)
    if a.selftest:
        return selftest(a.selftest)
    if not a.comp:
        p.error("--comp is required")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
