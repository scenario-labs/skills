"""Turn the raw Scenario renders into game-ready sprites and layers.

- cut:   split a transparent sprite sheet into one PNG per sprite (connected components),
         reading order = rows top to bottom, then left to right.
- key:   magenta (#FF00FF) background -> soft alpha + despill (HD cartoon, no pixelation).
- tile:  make a layer repeat horizontally without a seam (cross-fade its two ends).

  python3 prep_assets.py cut sheet.png out_dir name1,name2,... [--force]
  python3 prep_assets.py key in.png out.png [--force]
  python3 prep_assets.py tile in.png out.png [fade_px] [--force]

cut: names are given in reading order; sprites smaller than 4000 opaque px are dropped as specks, and pieces
closer than CUT_GROW px (environment variable, default 12) are kept together. Ask for wide gaps on the sheet.
tile: the seam is moved to the stretch where the layer's silhouette is lowest, then fade_px (default 256) of the
two ends are cross-faded, so the output is fade_px narrower than the input.
Existing outputs are kept unless --force is given. Needs Python 3 with Pillow, NumPy and SciPy.
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage


def cut(sheet, out_dir, names, pad=6):
    im = np.asarray(Image.open(sheet).convert("RGBA"))
    a = im[..., 3] > 16
    grown = ndimage.binary_dilation(a, iterations=int(os.environ.get("CUT_GROW", "12")))
    lab, n = ndimage.label(grown)
    boxes = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        area = int((a[sl] & (lab[sl] == i)).sum())
        if area < 4000:                      # stray specks
            continue
        boxes.append((ys.start, ys.stop, xs.start, xs.stop, i))
    # rows: group by vertical center, then sort by x
    boxes.sort(key=lambda b: (b[0] + b[1]) / 2)
    rows, cur = [], []
    for b in boxes:
        if cur and (b[0] + b[1]) / 2 - (cur[-1][0] + cur[-1][1]) / 2 > 0.5 * (b[1] - b[0]):
            rows.append(cur); cur = []
        cur.append(b)
    rows.append(cur)
    ordered = [b for r in rows for b in sorted(r, key=lambda b: b[2])]
    os.makedirs(out_dir, exist_ok=True)
    for name, (y0, y1, x0, x1, i) in zip(names, ordered):
        if os.path.exists(os.path.join(out_dir, name + ".png")) and not FORCE:
            sys.exit(f"error: {os.path.join(out_dir, name + '.png')} exists (pass --force to replace it)")
        y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
        y1, x1 = min(im.shape[0], y1 + pad), min(im.shape[1], x1 + pad)
        crop = im[y0:y1, x0:x1].copy()
        crop[..., 3] = np.where(lab[y0:y1, x0:x1] == i, crop[..., 3], 0)
        Image.fromarray(crop).save(os.path.join(out_dir, name + ".png"))
        print(name, crop.shape[1], "x", crop.shape[0])
    if len(ordered) != len(names):
        print("WARNING: found", len(ordered), "sprites for", len(names), "names")


def key_rgb(rgb, protect=True):
    f = rgb.astype(np.float32) / 255
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mag = np.minimum(r, b) - g                       # > 0 where red and blue both beat green
    close = np.abs(r - b) < 0.45
    t = np.clip((mag - 0.10) / (0.30 - 0.10), 0, 1) * close
    alpha = (1 - t)
    alpha = ndimage.grey_erosion(alpha, size=(3, 3))   # eat the 1px magenta fringe
    out = rgb.astype(np.float32)
    spill = np.clip(np.minimum(out[..., 0], out[..., 2]) - out[..., 1], 0, None) * 0.7
    out[..., 0] -= spill
    out[..., 2] -= spill
    if protect:
        # pinkish colors enclosed by the figure (inner ears, tongues) are part of the character, not the
        # background: inside the filled silhouette, anything that is not near-pure magenta keeps its color
        solid = alpha > 0.5
        inside = ndimage.binary_fill_holes(solid) & ~solid
        keep = ndimage.binary_dilation(inside & (mag < 0.35), iterations=1) & ndimage.binary_fill_holes(solid)
        alpha = np.where(keep, 1.0, alpha)
        out = np.where(keep[..., None], rgb.astype(np.float32), out)
    return np.dstack([np.clip(out, 0, 255), alpha * 255]).astype(np.uint8)


def key(src, dst):
    Image.fromarray(key_rgb(np.asarray(Image.open(src).convert("RGB")))).save(dst)


def tile(src, dst, fade=256):
    im = np.asarray(Image.open(src).convert("RGBA")).astype(np.float32)
    w = im.shape[1]
    # put the repeat seam where the silhouette is lowest (plain foliage, open sea), never through a
    # landmark: roll the image so that stretch sits at the edges, then cross-fade only there
    a = im[..., 3] > 128
    top = np.where(a.any(0), a.argmax(0), a.shape[0])          # first opaque row per column (bigger = lower)
    win = 2 * fade
    score = np.array([top[np.arange(x, x + win) % w].min() for x in range(0, w, 8)])
    best = int(np.argmax(score)) * 8                            # window whose tallest feature is lowest
    im = np.roll(im, -(best + fade), axis=1)                    # its center becomes the left/right edge
    out = im[:, :w - fade].copy()
    t = np.linspace(0, 1, fade)[None, :, None]
    out[:, :fade] = im[:, w - fade:] * (1 - t) + im[:, :fade] * t   # left edge continues the right edge
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)


FORCE = "--force" in sys.argv

if __name__ == "__main__":
    argv = [a for a in sys.argv if a != "--force"]
    need = {"cut": 5, "key": 4, "tile": 4}
    if len(argv) < 2 or argv[1] not in need or len(argv) < need[argv[1]]:
        sys.exit(__doc__)
    sys.argv = argv
    cmd = sys.argv[1]
    if not os.path.isfile(sys.argv[2]):
        sys.exit(f"error: {sys.argv[2]} not found")
    if cmd in ("key", "tile"):
        if os.path.abspath(sys.argv[3]) == os.path.abspath(sys.argv[2]):
            sys.exit("error: the output would overwrite the input")
        if os.path.exists(sys.argv[3]) and not FORCE:
            sys.exit(f"error: {sys.argv[3]} exists (pass --force to replace it)")
    if cmd == "cut":
        cut(sys.argv[2], sys.argv[3], sys.argv[4].split(","))
    elif cmd == "key":
        key(sys.argv[2], sys.argv[3])
    elif cmd == "tile":
        tile(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 256)
