"""bake_check: read baked maps on the runner side (plain Python + Pillow, no pymxs).

Checks per file: size and mode, share of pixels in the diagnostic ray-miss color,
and for normal maps the mean color and the share of pixels with a negative Z
(blue under 0.5), which a tangent-space map should almost never have.

Usage:
    python bake_check.py MAP.png [MAP2.png ...] [--normal] [--diag 255,0,0] [--tol 8] [--bg 0,0,0]
16-bit PNGs are reduced to 8 bit by Pillow for these statistics.
Prints one JSON object per file.
"""

import argparse
import json
import sys


def sample(rgb, step):
    """Every step-th pixel in row-major order, one row in memory at a time."""
    w, h = rgb.size
    px = []
    for y in range(h):
        row = rgb.crop((0, y, w, y + 1)).tobytes()
        for x in range((-y * w) % step, w, step):
            px.append((row[3 * x], row[3 * x + 1], row[3 * x + 2]))
    return px


def check(path, diag=(255, 0, 0), tol=8, normal=False, bg=(0, 0, 0)):
    from PIL import Image  # Pillow
    im = Image.open(path)
    out = {"file": path, "size": list(im.size), "mode": im.mode}
    rgb = im.convert("RGB")
    w, h = rgb.size
    step = max(1, (w * h) // 1_000_000)  # sample up to about one million pixels
    px = sample(rgb, step)
    n = len(px)
    dr, dg, db = diag
    miss = sum(1 for r, g, b in px if abs(r - dr) <= tol and abs(g - dg) <= tol and abs(b - db) <= tol)
    out["diag_color_pct"] = round(100.0 * miss / n, 3)
    if normal:
        # unbaked background (Bg column, black by default) is not part of the map
        px = [p for p in px if p != bg] or px
        n = len(px)
        mr = sum(p[0] for p in px) / n / 255.0
        mg = sum(p[1] for p in px) / n / 255.0
        mb = sum(p[2] for p in px) / n / 255.0
        out["normal_mean"] = [round(mr, 3), round(mg, 3), round(mb, 3)]
        out["neg_z_pct"] = round(100.0 * sum(1 for p in px if p[2] < 128) / n, 3)
        flags = []
        if abs(mr - 0.5) > 0.08 or abs(mg - 0.5) > 0.08:
            flags.append("mean far from (0.5, 0.5): check space (tangent expected) or a tilted bake")
        if out["neg_z_pct"] > 0.5:
            flags.append("pixels with negative Z: ray misses, inverted normals or a non-tangent space")
        out["flags"] = flags
    if out["diag_color_pct"] > 0:
        out.setdefault("flags", []).append("diagnostic ray-miss color present")
    if w != h or (w & (w - 1)) != 0:
        out.setdefault("flags", []).append("not a square power of two (fine only if planned)")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--normal", action="store_true")
    ap.add_argument("--diag", default="255,0,0")
    ap.add_argument("--tol", type=int, default=8)
    ap.add_argument("--bg", default="0,0,0", help="background color excluded from normal stats")
    a = ap.parse_args(argv)
    diag = tuple(int(x) for x in a.diag.split(","))
    bg = tuple(int(x) for x in a.bg.split(","))
    ok = True
    for f in a.files:
        r = check(f, diag, a.tol, a.normal, bg)
        print(json.dumps(r))
        ok = ok and not r.get("flags")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
