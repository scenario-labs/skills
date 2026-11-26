#!/usr/bin/env python3
"""seat_check.py: does a cutout carry the light of the plate it will sit in?

Usage:
  python3 seat_check.py CUTOUT.png PLATE.png --floor-top ROW [--top 0.02]
  python3 seat_check.py --contact OBJECT.png SHADOW.png[,CONTACT.png] [--max-gap 2]

CUTOUT.png  the object with straight alpha (after any relight), at any size
PLATE.png   the plate it will be seated in
--floor-top first plate row of the lit ground (below the horizon), so the sky and the sun disc are left out
--top       fraction of brightest pixels taken as highlights (default 0.02)

Prints one JSON line:
  objectBR / plateBR   blue-to-red ratio of the brightest pixels of the object and of the plate's ground
  warmthGap            objectBR - plateBR (pass within 0.15: the highlights carry the same light color)
  highlightOffset      where the object's highlights sit, as an offset from its matte center in matte widths
                       (information only: a strap or a dark side fools it; the light direction is gated by the
                       compositing skill's integration_check.py)
Exit code 1 when the warmth check fails.

--contact reads two mattes of one frame written by AEX.threeD.mattes (the object alone, its shadow layers alone, comma-separated and combined). In every
column where the object rests (middle 80 % of its width, lowest row within 5 % of its height of the lowest) it measures the gap in px between the object's lowest matte row and the
shadow's first row (alpha over half the shadow's own peak), and gates on the worst column: above --max-gap (default 2)
the object floats there. Shadow must sit below 90 % of the resting columns or more; mattes of different sizes fail. Run it on the first and the last frame of the move. Needs ImageMagick 7 (`magick`) and Python 3 standard library only.
"""
import json
import subprocess
import sys

COVERAGE = 0.9   # share of resting columns that need shadow below them, as in integration_check.py


def magick(*args):
    return subprocess.run(["magick", *args], check=True, capture_output=True, text=True).stdout.strip()


def pixels(path, crop=None):
    """Return (w, h, [(r, g, b, a)]) of an image downscaled to 400 px wide at most, 8-bit RGBA."""
    args = [path]
    if crop:
        args += ["-crop", crop, "+repage"]
    args += ["-resize", "400x>", "-depth", "8", "-alpha", "on"]
    w, h = (int(v) for v in magick(*args, "-format", "%w %h", "info:").split())
    raw = subprocess.run(["magick", *args, "RGBA:-"], check=True, capture_output=True).stdout
    return w, h, [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)]


def top_pixels(px, w, frac, keep):
    lum = []
    for i, p in enumerate(px):
        if keep(p):
            lum.append((0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2], i, p))
    lum.sort(reverse=True)
    n = max(1, int(len(lum) * frac))
    return lum[:n], len(lum)


def br(sel):
    r = sum(p[2][0] for p in sel) or 1
    return sum(p[2][2] for p in sel) / float(r)


def alpha_rows(path):
    w, h = (int(v) for v in magick(path, "-format", "%w %h", "info:").split())
    raw = subprocess.run(["magick", path, "-alpha", "extract", "-depth", "8", "gray:-"], check=True, capture_output=True).stdout
    return w, h, raw


def contact(obj, shadow, max_gap):
    """Per column across the middle 80 % of the object's width: the object's lowest matte row (alpha over 50 %) and the
    shadow's first row below it (alpha over half the shadow's peak). Columns whose lowest row sits within 5 % of the object's
    height of its lowest row count: where it rests (a strap, a handle or a rounded end above the floor is left out). The
    resting columns come from the object matte alone. A resting column with no shadow below it has no contact: the gate
    needs shadow under 90 % of them or more, and the worst gap among those within --max-gap."""
    w, h, oa = alpha_rows(obj)
    sa = None
    for part in shadow.split(","):          # cast and contact shadow mattes, combined by their maximum
        pw, ph, a = alpha_rows(part)
        if (pw, ph) != (w, h):
            return fail("shadow matte %s is %dx%d, the object matte %dx%d" % (part, pw, ph, w, h))
        sa = a if sa is None else bytes(max(p, q) for p, q in zip(sa, a))
    peak = max(sa)
    if peak == 0:
        return fail("the shadow mattes are empty")
    cols = [x for x in range(w) if any(oa[y * w + x] > 127 for y in range(0, h, 2))]
    if not cols:
        return fail("the object matte is empty")
    x0, x1 = cols[0], cols[-1]
    m = (x1 - x0) // 10
    lows = {}
    for x in range(x0 + m, x1 - m + 1, 4):
        ys = [y for y in range(h) if oa[y * w + x] > 127]
        if ys:
            lows[x] = ys[-1]
    if not lows:
        return fail("no object column to sample")
    top = min(y for y in range(h) if any(oa[y * w + x] > 127 for x in range(x0, x1 + 1, 4)))
    bottom = max(lows.values())
    resting = [x for x in sorted(lows) if lows[x] >= bottom - 0.05 * (bottom - top)]
    gaps = []
    for x in resting:
        low = lows[x]
        sy = next((y for y in range(max(low - 3, 0), h) if sa[y * w + x] > peak / 2), None)
        if sy is not None:
            gaps.append(sy - low)
    cover = len(gaps) / float(len(resting))
    out = {"objectBottom": bottom, "restingColumns": len(resting), "columns": len(gaps), "coverage": round(cover, 3),
           "coverageLimit": COVERAGE, "gapMax": max(gaps) if gaps else None,
           "gapMedian": sorted(gaps)[len(gaps) // 2] if gaps else None, "shadowPeak": round(peak / 255.0, 3)}
    out["pass"] = bool(gaps) and out["gapMax"] <= max_gap and cover >= COVERAGE
    print(json.dumps(out))
    return 0 if out["pass"] else 1


def fail(reason):
    print(json.dumps({"pass": False, "error": reason}))
    return 1


def main(argv):
    if "--contact" in argv:
        i = argv.index("--contact")
        return contact(argv[i + 1], argv[i + 2], float(argv[argv.index("--max-gap") + 1]) if "--max-gap" in argv else 2)
    if len(argv) < 3 or "--floor-top" not in argv:
        print(__doc__)
        return 2
    cut, plate = argv[1], argv[2]
    floor_top = int(argv[argv.index("--floor-top") + 1])
    frac = float(argv[argv.index("--top") + 1]) if "--top" in argv else 0.02
    w, h, px = pixels(cut)
    obj_hi, n_obj = top_pixels(px, w, frac, lambda p: p[3] > 250)
    xs = [i % w for i, p in enumerate(px) if p[3] > 128]
    cx, mw = (min(xs) + max(xs)) / 2.0, float(max(xs) - min(xs) or 1)
    hx = sum(s[1] % w for s in obj_hi) / float(len(obj_hi))
    pw, ph = [int(v) for v in magick(plate, "-format", "%w %h", "info:").split()]
    _, _, ppx = pixels(plate, crop="%dx%d+0+%d" % (pw, ph - floor_top, floor_top))
    plate_hi, _ = top_pixels(ppx, 0, frac, lambda p: True)
    out = {"objectBR": round(br(obj_hi), 3), "plateBR": round(br(plate_hi), 3)}
    out["warmthGap"] = round(out["objectBR"] - out["plateBR"], 3)
    out["highlightOffset"] = round((hx - cx) / mw, 3)
    out["pass"] = abs(out["warmthGap"]) <= 0.15
    print(json.dumps(out))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
