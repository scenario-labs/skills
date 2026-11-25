#!/usr/bin/env python3
"""focus_check.py: how soft a layer that must read is on a frame, from two mattes of that layer.

Usage:
  python3 focus_check.py SHARP.png SOFT.png [--limit 2.0] [--height 1080]

SHARP.png  the layer's matte at the time, written by AEX.threeD.mattes with the camera's Depth of Field off
SOFT.png   the same matte with Depth of Field on (as rendered)
--limit    the largest Gaussian radius (sigma, px at 1080 lines) that still passes (default 2.0)
--height   the frame height the mattes were written at; the result is scaled to 1080 lines

Finds the Gaussian sigma that turns the sharp matte into the soft one (least RMSE over the layer's box, padded),
prints one JSON line: sigma in px, sigma at 1080 lines, the fit error, and pass. Exit code 1 over the limit.
Needs ImageMagick 7 (`magick`) on the PATH and the Python 3 standard library.
"""
import json
import os
import tempfile
import subprocess
import sys


def magick(*args):
    return subprocess.run(["magick", *args], check=True, capture_output=True, text=True)


def rmse(sharp_a, soft_a, sigma, tmp):
    src = sharp_a
    if sigma > 0:
        src = os.path.join(tmp, "b.png")
        magick(sharp_a, "-blur", "0x%.2f" % sigma, src)
    r = subprocess.run(["magick", "compare", "-metric", "RMSE", src, soft_a, "null:"], capture_output=True, text=True)
    return float(r.stderr.split("(")[1].split(")")[0])


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    sharp, soft = argv[1], argv[2]
    limit = float(argv[argv.index("--limit") + 1]) if "--limit" in argv else 2.0
    height = float(argv[argv.index("--height") + 1]) if "--height" in argv else 1080.0
    w, h = (int(v) for v in magick(sharp, "-format", "%w %h", "info:").stdout.split())
    geo = magick(sharp, "-alpha", "extract", "-threshold", "50%", "-format", "%@", "info:").stdout.strip()
    bw, bh = (int(v) for v in geo.split("+")[0].split("x"))
    bx, by = int(geo.split("+")[1]), int(geo.split("+")[2])
    pad = 40
    x0, y0 = max(0, bx - pad), max(0, by - pad)
    crop = "%dx%d+%d+%d" % (min(w - x0, bw + 2 * pad), min(h - y0, bh + 2 * pad), x0, y0)
    tmp = tempfile.mkdtemp()
    sa, so = os.path.join(tmp, "s.png"), os.path.join(tmp, "o.png")
    magick(sharp, "-alpha", "extract", "-crop", crop, "+repage", sa)
    magick(soft, "-alpha", "extract", "-crop", crop, "+repage", so)
    best = (rmse(sa, so, 0, tmp), 0.0)
    s = 0.5
    while s <= 30:
        e = rmse(sa, so, s, tmp)
        if e < best[0]:
            best = (e, s)
        elif s > best[1] + 3:
            break
        s += 0.5
    sig = best[1] * 1080.0 / height
    out = {"sharp": sharp, "soft": soft, "sigmaPx": best[1], "sigma1080": round(sig, 2), "fitRmse": round(best[0], 4),
           "limit": limit, "pass": sig <= limit}
    print(json.dumps(out))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
