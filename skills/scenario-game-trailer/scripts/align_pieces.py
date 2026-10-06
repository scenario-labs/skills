#!/usr/bin/env python3
"""Put logo pieces extracted by an image edit back exactly where they sit in the original logo.

Usage: python3 align_pieces.py <logo.png> <pieces_dir> <out_dir> [--force]

Every PNG with transparency in <pieces_dir> is searched over scale (0.5 to 1.4) and position against the logo,
first coarsely with an FFT match, then refined pixel by pixel at full resolution. Each piece is written to <out_dir>
on a transparent canvas the size of the logo, ready to layer over it; a piece whose error passes 0.05 is flagged
"redrawn" (the edit changed it, so cut that piece from the original logo instead). <out_dir> must differ from <pieces_dir>; with --force, the pieces a previous run
listed in <out_dir>/align.json are removed first, so no stale piece survives. Needs numpy and Pillow.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

REDRAWN = 0.05  # faithful pieces score about 0.000 to 0.003; a recolored interior scored 0.18


def usage(code=1):
    print(__doc__.strip())
    sys.exit(code)


def clean(im):
    alpha = np.asarray(im.getchannel("A"))
    out = im.copy()
    out.putalpha(Image.fromarray(np.where(alpha < 40, 0, alpha).astype(np.uint8)))
    box = out.getbbox()
    return out.crop(box) if box else None


def ssd_map(piece, mask, target):
    """Weighted squared difference of the piece at every offset over the target, via FFT."""
    h, w = target.shape[:2]
    fft = np.fft.rfft2

    def ifft(a):
        return np.fft.irfft2(a, s=(h, w))
    mask_f = fft(mask, s=(h, w))
    total = np.zeros((h, w), np.float32)
    for ch in range(3):
        t, p = target[..., ch], piece[..., ch]
        total += ifft(fft(t * t) * np.conj(mask_f)) - 2 * ifft(fft(t) * np.conj(fft(mask * p, s=(h, w)))) + (mask * p * p).sum()
    return total / max(mask.sum(), 1)


def arrays(im):
    rgb = np.asarray(im.convert("RGB"), np.float32) / 255.0
    mask = (np.asarray(im.getchannel("A"), np.float32) / 255.0) ** 2
    return rgb, mask


def align(piece, target, size):
    tw, th = size
    best, ds = None, 4
    # box-average the target so it matches the Lanczos-shrunk piece; plain decimation aliases thin strokes
    hh, ww = target.shape[0] // ds * ds, target.shape[1] // ds * ds
    small = target[:hh, :ww].reshape(hh // ds, ds, ww // ds, ds, 3).mean((1, 3))
    for s in np.arange(0.50, 1.40, 0.02):
        w, h = int(piece.width * s / ds), int(piece.height * s / ds)
        if w < 4 or h < 4 or w >= small.shape[1] or h >= small.shape[0]:
            continue
        rgb, mask = arrays(piece.resize((w, h), Image.LANCZOS))
        valid = ssd_map(rgb, mask, small)[: small.shape[0] - h, : small.shape[1] - w]
        y, x = np.unravel_index(np.argmin(valid), valid.shape)
        if best is None or valid[y, x] < best[0]:
            best = (valid[y, x], s, x * ds, y * ds)
    if best is None:
        return None
    _, s0, x0, y0 = best
    fine = None
    for s in np.arange(s0 - 0.02, s0 + 0.021, 0.005):
        w, h = int(piece.width * s), int(piece.height * s)
        rgb, mask = arrays(piece.resize((w, h), Image.LANCZOS))
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                x, y = x0 + dx, y0 + dy
                if x < 0 or y < 0 or x + w > tw or y + h > th:
                    continue
                err = (((target[y:y + h, x:x + w] - rgb) ** 2).sum(-1) * mask).sum() / mask.sum()
                if fine is None or err < fine[0]:
                    fine = (float(err), float(s), int(x), int(y), w, h)
    return fine


def main():
    args = [a for a in sys.argv[1:] if a != "--force"]
    if len(args) != 3:
        usage()
    logo_path, pieces_dir, out_dir = args
    if not os.path.isfile(logo_path):
        sys.exit(f"not found: {logo_path}")
    if not os.path.isdir(pieces_dir):
        sys.exit(f"not a folder: {pieces_dir}")
    if os.path.realpath(out_dir) == os.path.realpath(pieces_dir):
        sys.exit("<out_dir> is the pieces folder; choose another folder")
    if os.path.exists(out_dir) and os.listdir(out_dir) and "--force" not in sys.argv:
        sys.exit(f"{out_dir} is not empty; pass --force to overwrite")
    os.makedirs(out_dir, exist_ok=True)
    previous = os.path.join(out_dir, "align.json")
    if os.path.exists(previous):
        with open(previous, encoding="utf-8") as f:
            for name in json.load(f):
                stale = os.path.join(out_dir, os.path.basename(name))
                if os.path.exists(stale):
                    os.remove(stale)
        os.remove(previous)
    logo = Image.open(logo_path).convert("RGBA")
    gray = Image.new("RGBA", logo.size, (128, 128, 128, 255))
    gray.alpha_composite(logo)
    target = np.asarray(gray.convert("RGB"), np.float32) / 255.0
    report = {}
    for name in sorted(os.listdir(pieces_dir)):
        if not name.lower().endswith(".png"):
            continue
        piece = clean(Image.open(os.path.join(pieces_dir, name)).convert("RGBA"))
        if piece is None:
            sys.exit(f"{name}: fully transparent; the edit returned no piece")
        found = align(piece, target, logo.size)
        if found is None:
            sys.exit(f"{name}: no placement fits inside the logo; check that it is a piece of this logo")
        err, s, x, y, w, h = found
        placed = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        placed.alpha_composite(piece.resize((w, h), Image.LANCZOS), (x, y))
        placed.save(os.path.join(out_dir, name))
        redrawn = err > REDRAWN
        report[name] = {"error": round(err, 4), "redrawn": redrawn, "scale": round(s, 3), "x": x, "y": y, "w": w, "h": h}
        note = "  redrawn: cut this piece from the original logo instead" if redrawn else ""
        print(f"{name}: error {err:.3f}, scale {s:.3f}, at ({x}, {y}){note}")
    with open(os.path.join(out_dir, "align.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
