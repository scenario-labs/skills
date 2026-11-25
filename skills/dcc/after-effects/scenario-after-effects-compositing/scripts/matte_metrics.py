#!/usr/bin/env python3
"""Numbers for judging a composite from rendered PNG frames (numpy + Pillow).

  alpha  RENDER.png REF.png [--labels L.png]   matte error against a reference matte (white = opaque)
  spill  IMG.png --box x,y,w,h | --labels L.png --id N   green (or blue) excess: G - (R+B)/2
  grain  IMG.png --box x,y,w,h                 per-channel grain (std of the image minus a 5x5 box blur)
  tgrain A.png B.png --box x,y,w,h             moving grain from two neighboring frames: std of (A - B) / sqrt(2), 0-255 scale
  levels IMG.png --box x,y,w,h                 per-channel 1st / 50th / 99th percentile (black, mid, white)
  edge   IMG.png --row y --x0 a --x1 b         10-90 % transition width of a matte along one row, in px
  diff   A.png B.png [--box x,y,w,h]           mean absolute difference (0-255 scale) and max
  light  FG_RGBA.png BG.png [--alpha A.png]    light match: source direction, subject key direction, rim on the
                                               source side, rim hue against the source, subject and plate levels
  rim    OVER_BLACK.png OVER_WHITE.png         edge color against the solid color inside (1 = clean, <1 dark ring)
  holes  ALPHA.png [--erode 6]                 core holes and stray alpha with no reference matte
  wrapbins ON.png OFF.png BG.png ALPHA.png     light wrap change on the subject, binned by background luma

Values are 0-1 unless stated. A render of an alpha view (alpha as gray over black) is read from its red channel.
Prints one JSON object.
"""
import argparse
import json
import numpy as np
from PIL import Image


def load(p):
    a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255.0
    return a


def box(img, spec):
    x, y, w, h = [int(v) for v in spec.split(",")]
    return img[y:y + h, x:x + w]


def blur5(a):
    k = np.ones(5, np.float32) / 5.0
    a = np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 0, a)
    return np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 1, a)


def cmd_alpha(a):
    m = load(a.render)[..., 0]
    t = load(a.ref)[..., 0]
    err = np.abs(m - t)
    edge = (t > 0.02) & (t < 0.98)
    out = {
        "mae": round(float(err.mean()), 5),
        "mae_edge": round(float(err[edge].mean()), 4) if edge.any() else None,
        "stray_bg_pct": round(float(((t <= 0.02) & (m > 0.05)).sum() / max((t <= 0.02).sum(), 1) * 100), 3),
        "holes_core_pct": round(float(((t >= 0.98) & (m < 0.95)).sum() / max((t >= 0.98).sum(), 1) * 100), 3),
        "edge_px": int(edge.sum()),
    }
    if a.labels:
        lab = np.asarray(Image.open(a.labels))
        names = {0: "bg", 1: "shirt", 2: "skin", 3: "hair", 4: "veil", 5: "stand"}
        for k, n in names.items():
            sel = lab == k
            if sel.any():
                out["mean_" + n] = round(float(m[sel].mean()), 4)
                out["ref_" + n] = round(float(t[sel].mean()), 4)
    return out


def cmd_spill(a):
    img = load(a.img)
    if a.labels:
        sel = np.asarray(Image.open(a.labels)) == a.id
        px = img[sel]
    else:
        px = box(img, a.box).reshape(-1, 3)
    mean = px.mean(0)
    return {"rgb": [round(float(v), 4) for v in mean], "green_excess": round(float(mean[1] - (mean[0] + mean[2]) / 2), 4),
            "blue_excess": round(float(mean[2] - (mean[0] + mean[1]) / 2), 4), "luma": round(float(mean @ [0.2126, 0.7152, 0.0722]), 4)}


def cmd_grain(a):
    img = box(load(a.img), a.box)
    out = {}
    for i, n in enumerate("rgb"):
        ch = img[..., i]
        hp = (ch - blur5(ch))[3:-3, 3:-3]
        out[n] = round(float(hp.std()), 5)
    return out


def cmd_tgrain(a):
    d = (box(load(a.a), a.box) - box(load(a.b), a.box)) * 255 / np.sqrt(2)
    return {n: round(float(d[..., i].std()), 3) for i, n in enumerate("rgb")}


def cmd_levels(a):
    img = box(load(a.img), a.box).reshape(-1, 3)
    return {n: [round(float(np.percentile(img[:, i], q)), 4) for q in (1, 50, 99)] for i, n in enumerate("rgb")}


def cmd_edge(a):
    row = load(a.img)[a.row, a.x0:a.x1, 0]
    lo, hi = row.min(), row.max()
    if hi - lo < 0.2:
        return {"width_px": None, "range": [float(lo), float(hi)]}
    n = (row - lo) / (hi - lo)
    i10 = np.argmax(n >= 0.1) if n[0] < n[-1] else np.argmax(n <= 0.9)
    i90 = np.argmax(n >= 0.9) if n[0] < n[-1] else np.argmax(n <= 0.1)
    return {"width_px": int(abs(i90 - i10)), "min": round(float(lo), 3), "max": round(float(hi), 3)}


def cmd_diff(a):
    x, y = load(a.a), load(a.b)
    if a.box:
        x, y = box(x, a.box), box(y, a.box)
    d = np.abs(x - y) * 255
    return {"mean": round(float(d.mean()), 3), "max": round(float(d.max()), 1)}


LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def load_rgba(p):
    return np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255.0


def shift_or(m, r):
    """Binary dilation by a (2r+1) square (numpy only)."""
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def erode(m, r):
    return ~shift_or(~m, r)


def depth_in(m, rmax):
    """Distance in px (square metric) from the outside of mask m, capped at rmax."""
    d = np.zeros(m.shape, np.int32)
    cur = m.copy()
    for k in range(1, rmax + 1):
        cur = erode(cur, 1)
        d[cur] = k
        if not cur.any():
            break
    return d


def hue_deg(rgb):
    r, g, b = rgb
    mx, mn = max(rgb), min(rgb)
    if mx - mn < 1e-6:
        return None
    if mx == r:
        h = (g - b) / (mx - mn) % 6
    elif mx == g:
        h = (b - r) / (mx - mn) + 2
    else:
        h = (r - g) / (mx - mn) + 4
    return float(h * 60.0)


def hue_gap(a, b):
    if a is None or b is None:
        return None
    d = abs(a - b) % 360
    return round(min(d, 360 - d), 1)


def local_mean(v, m, k):
    """Mean of v over mask m in a (2k+1) window around each pixel (nan where m is empty), sampled every 2 px."""
    num = np.zeros_like(v); den = np.zeros_like(v)
    vm = np.where(m, v, 0).astype(np.float32); mm = m.astype(np.float32)
    for dy in range(-k, k + 1, 2):
        for dx in range(-k, k + 1, 2):
            num += np.roll(np.roll(vm, dy, 0), dx, 1)
            den += np.roll(np.roll(mm, dy, 0), dx, 1)
    return np.where(den > 0, num / np.maximum(den, 1), np.nan)


def cmd_light(a):
    """Light match of a foreground against its plate. FG: the foreground alone, straight RGBA (or RGB plus --alpha);
    BG: the plate alone, same frame size. The source is the plate's brightest 0.5 %; its direction from the subject is
    compared with the subject's key (direction of the luma slope fitted over the subject), the rim on the edge facing
    the source, the rim color against the source color, and subject levels against plate levels."""
    f = load_rgba(a.fg)
    al = load(a.alpha)[..., 0] if a.alpha else f[..., 3]
    rgb = f[..., :3]
    bg = load(a.bg)
    S = al > 0.9
    ys, xs = np.nonzero(S)
    cx, cy = xs.mean(), ys.mean()
    rad = np.sqrt(S.sum() / np.pi)
    L = rgb @ LUMA
    # key: plane fit of luma over the subject's solid core (ring excluded so a rim does not count twice)
    dep = depth_in(S, int(a.ring) * 3)
    core = dep >= int(a.ring) * 3
    if core.sum() < 50:
        core = S
    cy_, cx_ = np.nonzero(core)
    A_ = np.c_[np.ones(len(cx_)), (cx_ - cx) / rad, (cy_ - cy) / rad]
    coef = np.linalg.lstsq(A_, L[cy_, cx_], rcond=None)[0]
    key = np.array(coef[1:]); key_strength = float(np.linalg.norm(key) / max(coef[0], 1e-6))
    # source: brightest 0.5 % of the plate
    BL = bg @ LUMA
    thr = np.percentile(BL, 99.5)
    sy, sx = np.nonzero(BL >= thr)
    src = np.array([sx.mean() - cx, sy.mean() - cy])
    halo = (BL >= np.percentile(BL, 97)) & (BL < thr)
    src_rgb = bg[halo].mean(0) if halo.any() else bg[BL >= thr].mean(0)
    def ang(v):
        return float(np.degrees(np.arctan2(v[1], v[0])))
    key_gap = hue_gap(ang(key), ang(src)) if np.linalg.norm(key) > 1e-6 else None
    # rim: ring 1..ring px inside the edge, on the half facing the source, against the core
    ring = (dep >= 1) & (dep <= int(a.ring)) & (al > 0.5)
    yy, xx = np.nonzero(ring)
    u = src / max(np.linalg.norm(src), 1e-6)
    facing = ((xx - cx) * u[0] + (yy - cy) * u[1]) > 0.3 * rad
    away = ((xx - cx) * u[0] + (yy - cy) * u[1]) < -0.3 * rad
    # each ring pixel against the same surface just inside it (local mean of the band ring+2 to 2*ring+2 px deep),
    # so a cream cap next to red fabric does not read as a rim
    band = (dep >= int(a.ring) + 2) & (dep <= 2 * int(a.ring) + 2)
    ref = local_mean(L, band, 2 * int(a.ring) + 3)
    rr = L[yy, xx] / np.maximum(ref[yy, xx], 1e-3)
    ok = ~np.isnan(ref[yy, xx])
    rim_f = float(np.median(rr[facing & ok])) if (facing & ok).any() else None
    rim_a = float(np.median(rr[away & ok])) if (away & ok).any() else None
    if facing.any():
        lf = L[yy[facing], xx[facing]]
        top = lf >= np.percentile(lf, 75)
        rim_rgb = rgb[yy[facing][top], xx[facing][top]].mean(0)
    else:
        rim_rgb = None
    # levels: the subject against the plate around it (its box grown 50 % per side), the source excluded
    h, w = BL.shape
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    gx, gy = (x1 - x0) // 2, (y1 - y0) // 2
    near = np.zeros_like(S); near[max(y0 - gy, 0):min(y1 + gy, h), max(x0 - gx, 0):min(x1 + gx, w)] = True
    diffuse = near & (BL < thr)
    out = {
        "subject_center": [round(float(cx), 1), round(float(cy), 1)], "subject_radius": round(float(rad), 1),
        "source_dir_deg": round(ang(src), 1), "source_rgb": [round(float(v), 3) for v in src_rgb],
        "source_in_frame": bool(thr > 0.9),
        "key_dir_deg": round(ang(key), 1) if key_gap is not None else None, "key_strength": round(key_strength, 3),
        "key_vs_source_deg": key_gap,
        "rim_facing": round(rim_f, 3) if rim_f else None, "rim_away": round(rim_a, 3) if rim_a else None,
        "rim_rgb": [round(float(v), 3) for v in rim_rgb] if rim_rgb is not None else None,
        "rim_hue_vs_source_deg": hue_gap(hue_deg(list(rim_rgb)), hue_deg(list(src_rgb))) if rim_rgb is not None else None,
        "subject_luma_p1_p99": [round(float(np.percentile(L[S], q)), 3) for q in (1, 99)],
        "plate_luma_p1_p99": [round(float(np.percentile(BL[BL < thr], q)), 3) for q in (1, 99)],
        "plate_near_luma_p1_p99": [round(float(np.percentile(BL[diffuse], q)), 3) for q in (1, 99)],
    }
    return out


def cmd_rim(a):
    """Edge rim from two renders of the same frame, over black and over white. Alpha is recovered per pixel
    (1 - (white - black)), the edge color unpremultiplied (black / alpha) and compared with the solid color
    `--inner` px inside. Ratio 1 = clean; under 1 dark ring; over 1 bright rim."""
    B = load(a.black); W = load(a.white)
    al = np.clip(1 - (W - B) @ LUMA, 0, 1)
    S = al > 0.98
    dep = depth_in(S, a.inner + 2)
    edge = (al > 0.15) & (al < 0.85)
    inner = (dep >= a.inner) & (dep <= a.inner + 2)
    Lb = B @ LUMA
    Ls = np.where(S, Lb, 0)
    # inner reference per edge pixel: mean of the inner band in a local window
    k = a.inner + 3
    num = np.zeros_like(Lb); den = np.zeros_like(Lb)
    for dy in range(-k, k + 1, 2):
        for dx in range(-k, k + 1, 2):
            num += np.roll(np.roll(np.where(inner, Ls, 0), dy, 0), dx, 1)
            den += np.roll(np.roll(inner.astype(np.float32), dy, 0), dx, 1)
    ref = np.where(den > 0, num / np.maximum(den, 1), np.nan)
    sel = edge & ~np.isnan(ref) & (ref > 0.02)
    ratio = (Lb[sel] / al[sel]) / ref[sel]
    if not sel.any():
        return {"edge_px": 0}
    return {"edge_px": int(sel.sum()), "median": round(float(np.median(ratio)), 3),
            "p10": round(float(np.percentile(ratio, 10)), 3), "p90": round(float(np.percentile(ratio, 90)), 3)}


def cmd_holes(a):
    """Core holes and stray alpha with no reference matte, from an alpha view render: inside = alpha above 0.5
    shrunk `--erode` px, holes = alpha under 0.95 there; outside = alpha under 0.5 grown `--erode` px, stray = alpha
    above 0.05 there."""
    m = load(a.img)[..., 0]
    inside = erode(m > 0.5, a.erode)
    outside = ~shift_or(m > 0.5, a.erode)
    return {"holes_pct": round(float((inside & (m < 0.95)).sum() / max(inside.sum(), 1) * 100), 3),
            "stray_pct": round(float((outside & (m > 0.05)).sum() / max(outside.sum(), 1) * 100), 4),
            "inside_px": int(inside.sum())}


def cmd_wrapbins(a):
    """Light wrap by background brightness: mean change (0-255) between renders with and without the wrap, on the
    subject (alpha view above 0.5), binned by the background's luma blurred 9 px."""
    on, off, bg = load(a.on), load(a.off), load(a.bg)
    m = load(a.alpha)[..., 0] > 0.5
    d = np.abs(on - off).mean(2) * 255
    bl = bg @ LUMA
    for _ in range(2):
        bl = blur5(bl)
    out = {"outside_mean": round(float(d[~m].mean()), 3)}
    edges = [0, 0.25, 0.5, 0.75, 1.01]
    for lo, hi in zip(edges, edges[1:]):
        sel = m & (bl >= lo) & (bl < hi) & (d > 0.01)
        out["bg_%.2f_%.2f" % (lo, min(hi, 1))] = round(float(d[sel].mean()), 2) if sel.sum() > 20 else None
    return out


def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    q = s.add_parser("alpha"); q.add_argument("render"); q.add_argument("ref"); q.add_argument("--labels")
    q = s.add_parser("spill"); q.add_argument("img"); q.add_argument("--box"); q.add_argument("--labels"); q.add_argument("--id", type=int, default=1)
    q = s.add_parser("grain"); q.add_argument("img"); q.add_argument("--box", required=True)
    q = s.add_parser("tgrain"); q.add_argument("a"); q.add_argument("b"); q.add_argument("--box", required=True)
    q = s.add_parser("levels"); q.add_argument("img"); q.add_argument("--box", required=True)
    q = s.add_parser("edge"); q.add_argument("img"); q.add_argument("--row", type=int, required=True)
    q.add_argument("--x0", type=int, required=True); q.add_argument("--x1", type=int, required=True)
    q = s.add_parser("diff"); q.add_argument("a"); q.add_argument("b"); q.add_argument("--box")
    q = s.add_parser("light"); q.add_argument("fg"); q.add_argument("bg"); q.add_argument("--alpha"); q.add_argument("--ring", type=int, default=6)
    q = s.add_parser("rim"); q.add_argument("black"); q.add_argument("white"); q.add_argument("--inner", type=int, default=4)
    q = s.add_parser("holes"); q.add_argument("img"); q.add_argument("--erode", type=int, default=6)
    q = s.add_parser("wrapbins"); q.add_argument("on"); q.add_argument("off"); q.add_argument("bg"); q.add_argument("alpha")
    a = p.parse_args()
    print(json.dumps(globals()["cmd_" + a.cmd](a)))


if __name__ == "__main__":
    main()
