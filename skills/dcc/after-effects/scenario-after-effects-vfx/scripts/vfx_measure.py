#!/usr/bin/env python3
"""Pixel gates for effects on a plate, read from PNG frames (needs numpy and Pillow).

Luma is Rec. 709 on the encoded values, 0 to 1 (levels = luma x 255). Frames from saveFrameToPng at 16 bpc load as 8 bits.

  vfx_measure.py clip IMG...                         share of pixels at 255 in all three channels, per frame
  vfx_measure.py luma IMG...                         mean luma per frame
  vfx_measure.py flash --calm IMG --peak IMG...      brightest mean luma, share of the calm headroom used, ratio, verdict
  vfx_measure.py contour --frame IMG --matte IMG     contour ratio: luma 1 to 3 px outside the matte over 6 to 14 px outside
  vfx_measure.py outline --frame IMG --matte IMG --origin X Y   far-side outline in levels: 1 to 3 px inside minus 6 to 12 px inside
  vfx_measure.py grain --plate A B --shot A B        frame-to-frame std on flat tiles the effect leaves alone, shot over plate
  vfx_measure.py blacks --plate IMG --shot IMG --origin X Y     p1 luma beyond --beyond px from the origin, shot over plate
  vfx_measure.py wisp --with IMG... --without IMG... --box X0 Y0 X1 Y1 [--fps 30]   smoke accent: contrast and height per frame, verdict
  vfx_measure.py gates MANIFEST.json                 every gate above from the manifest AEX.pulse.gateFrames writes, plus the hold

A gate that has nothing to measure (an empty band, region or tile set) is inconclusive, and an inconclusive gate fails.
"""
import argparse, json, math, os, re, sys


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("vfx_measure.py needs numpy and Pillow: python3 -m pip install numpy pillow")

# Gate limits (see procedures section 13, GATE 13). Flash: rise of the peak frame's mean luma over the calm frame, final comp.
# Flash: share of the calm frame's headroom (1 - calm mean luma) that the brightest frame after the hit uses, and peak over calm.
# Calibrated on a mid-dark hero plate, a bright plate and a dark wide plate: shots built as written used 1.5 to 4.4 % of the headroom
# and 1.05 to 1.37x the calm mean; the same shots with the old hot core and flash used 2.0 to 7.8 % and 1.10 to 1.49x.
LIMITS = {"clip": 0.0, "contour": 1.0, "contourPeak": 0.95, "outline": 20.0, "grain": 0.10, "blacks": 0.05, "blacksLevels": 1.0,
          "flashHeadroom": 0.06, "flashRatio": 1.45, "strengthMin": 0.5,
          "wispContrast": 10.0, "wispHeight": 0.08, "wispSeconds": 1.0, "holdMove": 0.25}
# Hold: largest mean absolute luma change between consecutive held frames of the camera comp (before grain), in levels. The scene
# is frozen by time remap there, so a camera push or shake still running in the hold is the only thing that moves it.
# Hit strength = max(headroom / flashHeadroom, (ratio - 1) / (flashRatio - 1)): 1.0 is the ceiling on either reading. A pulse below
# strengthMin does not light the scene (fails); aim for 0.7 to 0.95.
# Wisp: brightest 5 % of (with - without) luma inside the wisp's box, in levels, and its visible height (rows with 3 or more pixels
# 4 levels up) as a share of the frame height; it must read on frames spanning wispSeconds.


def load(path):
    im = Image.open(path)
    a = np.asarray(im.convert("RGBA" if "A" in im.getbands() else "RGB")).astype(np.float64)
    if a.max() > 255:
        a = a / 257.0
    return a / 255.0


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def clip_share(a):
    return float(np.all(a[..., :3] >= 254.5 / 255, axis=2).mean())


def matte_mask(path):
    a = load(path)
    m = luma(a)
    if a.shape[2] == 4 and m.max() < 0.01:   # a matte saved with alpha only
        m = a[..., 3]
    return m >= 0.5


def dilate(m):
    """One step of 8-neighbour dilation (chessboard distance grows by 1)."""
    p = np.pad(m, 1)
    out = np.zeros_like(m)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            out |= p[dy:dy + m.shape[0], dx:dx + m.shape[1]]
    return out


def chess_dist(m, n):
    """Chessboard distance from the True region, capped at n + 1 (0 inside the region)."""
    d = np.full(m.shape, n + 1, dtype=np.int32)
    d[m] = 0
    cur = m.copy()
    for k in range(1, n + 1):
        nxt = dilate(cur)
        d[nxt & ~cur] = k
        cur = nxt
    return d


def contour(frame, matte):
    """Near-to-far luma ratio; None when either band has no pixel (inconclusive)."""
    m = matte_mask(matte)
    y = luma(load(frame))
    rows = np.where(m.any(axis=1))[0]
    if not len(rows):
        raise SystemExit("contour: the matte is empty")
    mid = (rows[0] + rows[-1]) // 2
    d = chess_dist(m, 14)
    upper = np.zeros_like(m)
    upper[:mid, :] = True
    near = (d >= 1) & (d <= 3) & upper
    far = (d >= 6) & (d <= 14) & upper
    if not near.any() or not far.any():
        return None
    return float(y[near].mean() / max(y[far].mean(), 1e-6))


def outline(frame, matte, origin, min_dist=300):
    m = matte_mask(matte)
    y = luma(load(frame)) * 255
    d = chess_dist(~m, 12)                     # distance from the background, inside the subject
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    far_side = np.hypot(xx - origin[0], yy - origin[1]) > min_dist
    edge = (d >= 1) & (d <= 3) & m & far_side   # d counts from 1 on the first pixel inside
    inner = (d >= 6) & (d <= 12) & m & far_side
    if not edge.any() or not inner.any():
        return None
    return float(y[edge].mean() - y[inner].mean())


def flat_tiles(y, size=24, keep=0.3):
    """Tiles of the plate with the least local detail (spatial std of a 3x3 high-pass), luma 0.02 to 0.9."""
    h, w = y.shape
    p = np.pad(y, 1, mode="edge")
    hp = y - sum(p[dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3)) / 9
    tiles = []
    for ty in range(0, h - size + 1, size):
        for tx in range(0, w - size + 1, size):
            t = y[ty:ty + size, tx:tx + size]
            if 0.02 < t.mean() < 0.9:
                tiles.append((float(hp[ty:ty + size, tx:tx + size].std() + t.std()), ty, tx))
    tiles.sort()
    return [(ty, tx) for _, ty, tx in tiles[:max(1, int(len(tiles) * keep))]], size


def temporal_std(a, b, tiles, size):
    d = luma(load(a)) - luma(load(b))
    return float(np.mean([d[ty:ty + size, tx:tx + size].std() for ty, tx in tiles]) / np.sqrt(2) * 255)


def highpass_std(a, tiles, size):
    y = luma(load(a))
    h, w = y.shape
    p = np.pad(y, 2, mode="edge")
    hp = y - sum(p[dy:dy + h, dx:dx + w] for dy in range(5) for dx in range(5)) / 25
    return float(np.mean([hp[ty:ty + size, tx:tx + size].std() for ty, tx in tiles]) * 255)


def grain(plate, shot):
    """Frame-to-frame std on the plate's flattest tiles, shot over plate. Only tiles whose mean the effect moved by under 1 level count,
    so the effect's own texture (haze, dust, rings) is not read as grain. A still plate (frame-to-frame std under 0.05 levels) has no
    temporal grain: then the high-pass std (luma minus its 5 x 5 mean) of one frame is compared instead."""
    tiles, size = flat_tiles(luma(load(plate[0])))
    yp, ys = luma(load(plate[0])), luma(load(shot[0]))
    tiles = [(ty, tx) for ty, tx in tiles if abs(ys[ty:ty + size, tx:tx + size].mean() - yp[ty:ty + size, tx:tx + size].mean()) * 255 < 1.0]
    if not tiles:
        return {"mode": None, "tiles": 0, "inconclusive": "no flat tile the effect leaves alone: grain not measured"}
    p = temporal_std(plate[0], plate[1], tiles, size)
    if p < 0.05:
        p, s, mode = highpass_std(plate[0], tiles, size), highpass_std(shot[0], tiles, size), "highpass"
    else:
        s, mode = temporal_std(shot[0], shot[1], tiles, size), "temporal"
    r = {"mode": mode, "plateStd": round(p, 3), "shotStd": round(s, 3), "change": round(s / max(p, 1e-6) - 1, 3), "tiles": len(tiles)}
    if len(tiles) < 20:
        r["note"] = "under 20 flat tiles the effect leaves alone: confirm grain on a 1:1 crop"
    return r


def blacks(plate, shot, origin, beyond=900):
    """p1 luma beyond `beyond` px from the origin, shot against plate. On a plate whose p1 is under 2 levels a percentage means nothing:
    the change is then given in 8-bit levels (`levels`) and the gate allows LIMITS["blacksLevels"]."""
    yp, ys = luma(load(plate)), luma(load(shot))
    yy, xx = np.mgrid[0:yp.shape[0], 0:yp.shape[1]]
    far = np.hypot(xx - origin[0], yy - origin[1]) > beyond
    if not far.any():
        return {"inconclusive": "no pixel beyond %g px from the origin: pass a smaller --beyond" % beyond}
    p1p, p1s = float(np.percentile(yp[far], 1)), float(np.percentile(ys[far], 1))
    r = {"plateP1": round(p1p, 4), "shotP1": round(p1s, 4), "levels": round((p1s - p1p) * 255, 2)}
    r["change"] = None if p1p < 2 / 255 else round(p1s / p1p - 1, 3)
    return r


def flash(calm, peaks, max_headroom, max_ratio):
    """Brightest final frame among `peaks` (every frame of the 15 after the hit: the peak comes 5 to 10 frames late) against the calm frame.
    headroom = (peak - calm) / (1 - calm): the share of the light still available that the hit uses. Pass: headroom and ratio within limits."""
    if not (isinstance(max_headroom, (int, float)) and math.isfinite(max_headroom) and max_headroom > 0):
        raise SystemExit("flash: max headroom must be a finite number above 0, got %r" % (max_headroom,))
    if not (isinstance(max_ratio, (int, float)) and math.isfinite(max_ratio) and max_ratio > 1):
        raise SystemExit("flash: max ratio must be a finite number above 1, got %r" % (max_ratio,))
    if not peaks:
        raise SystemExit("flash: no peak frame to measure")
    c = float(luma(load(calm)).mean())
    vals = [(float(luma(load(p)).mean()), p) for p in peaks]
    pk, path = max(vals)
    rise, ratio, head = pk - c, pk / max(c, 1e-6), (pk - c) / max(1 - c, 1e-6)
    st = max(head / max_headroom, (ratio - 1) / (max_ratio - 1))
    return {"calm": round(c, 4), "peak": round(pk, 4), "peakFrame": os.path.basename(path), "rise": round(rise, 4), "headroom": round(head, 4),
            "ratio": round(ratio, 3), "strength": round(st, 3), "pass": bool(LIMITS["strengthMin"] <= st <= 1.0)}


def wisp(withs, withouts, box, fps=30):
    """Each pair: the same frame with and without the wisp. Contrast = p95 of the luma rise inside box (levels); height = rows of the box with
    3 or more pixels risen 4 levels, over the frame height. Frame numbers are read from the file names (last number); both lists must
    hold the same frame numbers, once each, and frames are paired by number."""
    def by_frame(paths, side):
        out = {}
        for p in paths:
            n = re.findall(r"(\d+)", os.path.basename(p))
            if not n:
                raise SystemExit("wisp: no frame number in the %s file name %s" % (side, os.path.basename(p)))
            if int(n[-1]) in out:
                raise SystemExit("wisp: frame %d appears twice in the %s frames" % (int(n[-1]), side))
            out[int(n[-1])] = p
        return out
    fw, fo = by_frame(withs, "--with"), by_frame(withouts, "--without")
    if set(fw) != set(fo):
        raise SystemExit("wisp: --with and --without hold different frames (only with: %s; only without: %s)"
                         % (sorted(set(fw) - set(fo)), sorted(set(fo) - set(fw))))
    x0, y0, x1, y1 = [int(v) for v in box]
    rows = []
    for fr in sorted(fw):
        a, b = fw[fr], fo[fr]
        ya, yb = luma(load(a)), luma(load(b))
        d = (ya - yb)[y0:y1, x0:x1] * 255
        h = int(((d >= 4).sum(axis=1) >= 3).sum())
        rows.append({"frame": fr, "contrast": round(float(np.percentile(d, 95)), 2), "height": round(h / ya.shape[0], 3)})
    ok = [r["frame"] for r in rows if r["contrast"] >= LIMITS["wispContrast"] and r["height"] >= LIMITS["wispHeight"] and r["frame"] is not None]
    span = (max(ok) - min(ok)) / fps if ok else 0.0
    return {"frames": rows, "readsFor": round(span, 2), "pass": bool(span >= LIMITS["wispSeconds"])}


def hold_motion(paths):
    """Largest mean absolute luma change between consecutive frames, in levels."""
    ys = [luma(load(p)) for p in paths]
    return float(max(np.abs(a - b).mean() for a, b in zip(ys, ys[1:])) * 255)


def gates(manifest):
    """Manifest from AEX.pulse.gateFrames: {version, origin, at, plate: [A, B], calm, peaks: [...], scene: {t: path}, matte: {t: path},
    outs: [...], hold: [A, B], holdFrames: [...], holdCount, peakTimes: [...], pngScale}. Every path absolute. A manifest written before
    version 2 (no pngScale, no holdFrames) is read as scale 1 and its hold is not measured; a note says so."""
    M = _read_json(manifest)
    notes = []
    scale = M.get("pngScale")
    if scale is None:
        notes.append("manifest without pngScale (before version 2): frames read as scale 1")
    elif scale != 1:
        raise SystemExit("gates: frames written at pngScale %s (a 32 bpc project): the limits are set on 8 and 16 bpc frames; "
                         "capture again at 16 bpc" % scale)
    o = M["origin"]
    R = {"clip": {}, "contour": {}, "outline": {}}
    clipped = {}
    for p in M["outs"]:
        clipped[os.path.basename(p)] = clip_share(load(p))
        R["clip"][os.path.basename(p)] = round(clipped[os.path.basename(p)] * 100, 4)
    for t, p in sorted(M["scene"].items(), key=lambda kv: float(kv[0])):
        peak = t in [str(x) for x in M.get("peakTimes", [])]
        ratio = contour(p, M["matte"][t])
        R["contour"][t] = {"ratio": None if ratio is None else round(ratio, 3), "peak": peak}
        ol = outline(p, M["matte"][t], o)
        R["outline"][t] = None if ol is None else round(ol, 1)
    R["flash"] = flash(M["calm"], M["peaks"], LIMITS["flashHeadroom"], LIMITS["flashRatio"])
    if M.get("plate") and M.get("hold"):
        R["grain"] = grain(M["plate"], M["hold"])
    if M.get("plateFrame") and M.get("calmScene"):
        R["blacks"] = blacks(M["plateFrame"], M["calmScene"], o)
    if "holdFrames" not in M:
        notes.append("manifest without holdFrames (before version 2): the hold is not measured")
    elif len(M["holdFrames"]) >= 2:
        R["hold"] = {"move": round(hold_motion(M["holdFrames"]), 3), "frames": len(M["holdFrames"])}
    elif M.get("holdCount", 0) > 1:
        R["hold"] = {"inconclusive": "%d held frames asked, %d captured" % (M["holdCount"], len(M["holdFrames"]))}
    fails = []
    if not clipped:
        fails.append("clip (inconclusive: no final frame)")
    elif max(clipped.values()) > LIMITS["clip"]:
        fails.append("clip")
    for t, v in R["contour"].items():
        if v["ratio"] is None:
            fails.append("contour " + t + " (inconclusive: a band around the matte is empty)")
        elif v["ratio"] < (LIMITS["contourPeak"] if v["peak"] else LIMITS["contour"]):
            fails.append("contour " + t)
    for t, v in R["outline"].items():
        if v is not None and v > LIMITS["outline"] and t in [str(x) for x in M.get("peakTimes", [])]:
            fails.append("outline " + t)
    if not R["flash"]["pass"]:
        fails.append("flash")
    if "grain" in R:   # on a still plate (high-pass mode) only added grain fails: a lower high-pass std is texture softened by the CA
        g = R["grain"]
        if "inconclusive" in g:
            fails.append("grain (inconclusive)")
        elif (g["mode"] == "temporal" and abs(g["change"]) > LIMITS["grain"]) or (g["mode"] == "highpass" and g["change"] > LIMITS["grain"]):
            fails.append("grain")
    if "blacks" in R:
        b = R["blacks"]
        if "inconclusive" in b:
            fails.append("blacks (inconclusive)")
        elif (b["change"] is None and abs(b["levels"]) > LIMITS["blacksLevels"]) or (b["change"] is not None and abs(b["change"]) > LIMITS["blacks"]):
            fails.append("blacks")
    if "hold" in R:
        h = R["hold"]
        if "inconclusive" in h:
            fails.append("hold (inconclusive)")
        elif h["move"] > LIMITS["holdMove"]:
            fails.append("hold")
    if all(v is None for v in R["outline"].values()):
        R["outlineNote"] = "no matte edge beyond 300 px from the origin: the far-side outline does not apply"
    if notes:
        R["notes"] = notes
    R["limits"] = LIMITS
    R["fails"] = fails
    return R


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("clip"); s.add_argument("img", nargs="+")
    s = sp.add_parser("luma"); s.add_argument("img", nargs="+")
    s = sp.add_parser("flash"); s.add_argument("--calm", required=True); s.add_argument("--peak", nargs="+", required=True)
    s.add_argument("--max-headroom", type=float, default=LIMITS["flashHeadroom"]); s.add_argument("--max-ratio", type=float, default=LIMITS["flashRatio"])
    s = sp.add_parser("contour"); s.add_argument("--frame", required=True); s.add_argument("--matte", required=True)
    s = sp.add_parser("outline"); s.add_argument("--frame", required=True); s.add_argument("--matte", required=True)
    s.add_argument("--origin", type=float, nargs=2, required=True); s.add_argument("--min-dist", type=float, default=300)
    s = sp.add_parser("grain"); s.add_argument("--plate", nargs=2, required=True); s.add_argument("--shot", nargs=2, required=True)
    s = sp.add_parser("blacks"); s.add_argument("--plate", required=True); s.add_argument("--shot", required=True)
    s.add_argument("--origin", type=float, nargs=2, required=True); s.add_argument("--beyond", type=float, default=900)
    s = sp.add_parser("wisp"); s.add_argument("--with", dest="withs", nargs="+", required=True); s.add_argument("--without", nargs="+", required=True)
    s.add_argument("--box", type=float, nargs=4, required=True); s.add_argument("--fps", type=float, default=30)
    s = sp.add_parser("gates"); s.add_argument("manifest")
    a = ap.parse_args()
    if a.cmd == "clip":
        out = {os.path.basename(p): round(clip_share(load(p)) * 100, 4) for p in a.img}
    elif a.cmd == "luma":
        out = {os.path.basename(p): round(float(luma(load(p)).mean()), 4) for p in a.img}
    elif a.cmd == "flash":
        out = flash(a.calm, a.peak, a.max_headroom, a.max_ratio)
    elif a.cmd == "contour":
        r = contour(a.frame, a.matte)
        out = {"contourRatio": None if r is None else round(r, 3)}
        if r is None:
            out["inconclusive"] = "a band around the matte is empty"
    elif a.cmd == "outline":
        out = {"outlineLevels": outline(a.frame, a.matte, a.origin, a.min_dist)}
    elif a.cmd == "grain":
        out = grain(a.plate, a.shot)
    elif a.cmd == "wisp":
        out = wisp(a.withs, a.without, a.box, a.fps)
    elif a.cmd == "blacks":
        out = blacks(a.plate, a.shot, a.origin, a.beyond)
    else:
        out = gates(a.manifest)
    print(json.dumps(out, indent=1))
    if (a.cmd == "gates" and out["fails"]) or (a.cmd in ("wisp", "flash") and not out["pass"]) or "inconclusive" in out:
        sys.exit(1)


if __name__ == "__main__":
    main()
