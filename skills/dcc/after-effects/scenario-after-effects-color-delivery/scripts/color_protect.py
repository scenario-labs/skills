#!/usr/bin/env python3
"""Protected colors: did a grade keep the named brand colors? Compares the same pixels before and after.

Usage:
  python3 color_protect.py BEFORE.png AFTER.png --color cream=#F1E9D8 --color coral=#E0452C
         [--radius 25] [--max-de 5] [--max-hue 4] [--box x,y,w,h] [--json out.json]

BEFORE is the ungraded frame, AFTER the graded frame at the same time (decode both with procedures.md section 10).
For each named color, the mask is every BEFORE pixel within `--radius` (CIE76 delta E, Lab D65) of the swatch: the
plate's own version of that color, which a render or a photo rarely holds exactly. The same pixels are then read in
AFTER. Reported per color: pixel count, mean Lab before and after, delta E 76, hue shift in degrees (a*b* angle),
chroma change in percent, and PASS when delta E <= --max-de and |hue shift| <= --max-hue (hue is not
judged on near-neutrals, chroma under 10). Exit 1 on any FAIL or on a
color with fewer than 200 pixels in the mask. Needs numpy and Pillow.
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image


def _write_json(path, data, **kw):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, **kw)



def srgb_to_lab(rgb):
    c = np.asarray(rgb, np.float64)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def hexrgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def load(p, box):
    a = np.asarray(Image.open(p).convert("RGB"), np.float64) / 255.0
    if box:
        x, y, w, h = [int(v) for v in box.split(",")]
        a = a[y:y + h, x:x + w]
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before"); ap.add_argument("after")
    ap.add_argument("--color", action="append", required=True, help="name=#RRGGBB")
    ap.add_argument("--radius", type=float, default=25.0)
    ap.add_argument("--max-de", type=float, default=5.0)
    ap.add_argument("--max-hue", type=float, default=4.0)
    ap.add_argument("--box"); ap.add_argument("--json")
    a = ap.parse_args()
    B, A = load(a.before, a.box), load(a.after, a.box)
    if B.shape != A.shape:
        sys.exit("before and after differ in size")
    LB, LA = srgb_to_lab(B), srgb_to_lab(A)
    rows, bad = [], False
    for spec in a.color:
        name, hx = spec.split("=")
        sw = srgb_to_lab(np.array(hexrgb(hx)))
        m = np.linalg.norm(LB - sw, axis=-1) <= a.radius
        n = int(m.sum())
        row = {"color": name, "swatch": hx, "pixels": n}
        if n < 200:
            row.update({"verdict": "FAIL", "why": "fewer than 200 pixels within radius %.0f: raise --radius or use --box" % a.radius})
            bad = True; rows.append(row); continue
        b, f = LB[m].mean(0), LA[m].mean(0)
        hb, hf = np.degrees(np.arctan2(b[2], b[1])), np.degrees(np.arctan2(f[2], f[1]))
        dh = (hf - hb + 180) % 360 - 180
        cb, cf = np.hypot(b[1], b[2]), np.hypot(f[1], f[2])
        de = float(np.linalg.norm(f - b))
        # hue is unstable on near-neutrals (chroma under 10): judge those by delta E alone
        ok = de <= a.max_de and (cb < 10 or abs(dh) <= a.max_hue)
        bad |= not ok
        row.update({"lab_before": [round(float(v), 2) for v in b], "lab_after": [round(float(v), 2) for v in f],
                    "source_vs_swatch_de": round(float(np.linalg.norm(b - sw)), 2), "de76": round(de, 2),
                    "hue_before": round(float(hb), 1), "hue_shift_deg": round(float(dh), 1),
                    "chroma_change_pct": round(float((cf - cb) / max(cb, 1e-6) * 100), 1),
                    "verdict": "PASS" if ok else "FAIL"})
        rows.append(row)
    for r in rows:
        print(json.dumps(r))
    if a.json:
        _write_json(a.json, rows, indent=1)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
