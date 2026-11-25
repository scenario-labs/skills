#!/usr/bin/env python3
"""Numbers for judging a composite from rendered PNG frames (numpy + Pillow).

  alpha  RENDER.png REF.png [--labels L.png]   matte error against a reference matte (white = opaque)
  spill  IMG.png --box x,y,w,h | --labels L.png --id N   green (or blue) excess: G - (R+B)/2
  grain  IMG.png --box x,y,w,h                 per-channel grain (std of the image minus a 5x5 box blur)
  levels IMG.png --box x,y,w,h                 per-channel 1st / 50th / 99th percentile (black, mid, white)
  edge   IMG.png --row y --x0 a --x1 b         10-90 % transition width of a matte along one row, in px
  diff   A.png B.png [--box x,y,w,h]           mean absolute difference (0-255 scale) and max

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


def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    q = s.add_parser("alpha"); q.add_argument("render"); q.add_argument("ref"); q.add_argument("--labels")
    q = s.add_parser("spill"); q.add_argument("img"); q.add_argument("--box"); q.add_argument("--labels"); q.add_argument("--id", type=int, default=1)
    q = s.add_parser("grain"); q.add_argument("img"); q.add_argument("--box", required=True)
    q = s.add_parser("levels"); q.add_argument("img"); q.add_argument("--box", required=True)
    q = s.add_parser("edge"); q.add_argument("img"); q.add_argument("--row", type=int, required=True)
    q.add_argument("--x0", type=int, required=True); q.add_argument("--x1", type=int, required=True)
    q = s.add_parser("diff"); q.add_argument("a"); q.add_argument("b"); q.add_argument("--box")
    a = p.parse_args()
    print(json.dumps(globals()["cmd_" + a.cmd](a)))


if __name__ == "__main__":
    main()
