"""render_metrics: judge saved renders with numbers (runner side, plain Python, never imports pymxs).

status: not yet run against 3ds Max output; the math is standard image statistics [added].
Needs numpy and Pillow. EXR input needs imageio with an EXR plugin, or convert first with
`magick in.exr out.tif`.

Library:
    load(path)                         -> float32 array HxWx3 in 0..1 (display) or linear (EXR)
    noise(path, tile=64)               -> {sigma, p95_tile, worst_tiles}
    exposure(path)                     -> {mean, median, p01, p99, clipped_pct, crushed_pct}
    detail_ratio(test, reference)      -> gradient energy of test / reference (denoiser smear check)
    flicker(paths)                     -> {means, jumps, temporal_noise}
    estimate(seconds, test_px, final_px, frames=1, noise_now=None, noise_target=None,
             machines=1, margin=1.25)  -> {hours_per_frame, hours_total}
    crops(path, out_dir, size=512)     -> [paths] 100 percent crops for visual review
    downscale(src, dst, factor=0.5)    -> dst

CLI: python render_metrics.py <command> <args...>   (prints JSON)
    noise IMG | exposure IMG | detail TEST REF | flicker IMG... | crops IMG OUTDIR
    estimate SECONDS TEST_W TEST_H FINAL_W FINAL_H [FRAMES] | downscale SRC DST [FACTOR]
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

_LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def load(path):
    if path.lower().endswith(".exr"):
        import imageio.v3 as iio  # optional dependency
        arr = np.asarray(iio.imread(path), dtype=np.float32)
    else:
        img = Image.open(path)
        if img.mode in ("I;16", "I;16B", "I"):
            arr = np.asarray(img, dtype=np.float32) / 65535.0
            arr = np.stack([arr] * 3, axis=-1)
        else:
            arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    return arr[..., :3]


def _luma(arr):
    return arr @ _LUMA


def _sigma(lum):
    """Immerkaer fast noise estimate on one channel (robust to smooth gradients)."""
    h, w = lum.shape
    if h < 3 or w < 3:
        return 0.0
    k = (lum[:-2, :-2] - 2 * lum[:-2, 1:-1] + lum[:-2, 2:]
         - 2 * lum[1:-1, :-2] + 4 * lum[1:-1, 1:-1] - 2 * lum[1:-1, 2:]
         + lum[2:, :-2] - 2 * lum[2:, 1:-1] + lum[2:, 2:])
    return float(math.sqrt(math.pi / 2) * np.abs(k).sum() / (6.0 * (w - 2) * (h - 2)))


def noise(path, tile=64):
    lum = _luma(load(path))
    h, w = lum.shape
    tiles = []
    for y in range(0, h - tile + 1, tile):
        for x in range(0, w - tile + 1, tile):
            tiles.append((_sigma(lum[y:y + tile, x:x + tile]), x, y))
    vals = np.array([t[0] for t in tiles]) if tiles else np.array([0.0])
    worst = sorted(tiles, reverse=True)[:5]
    return {"sigma": round(float(np.median(vals)), 5),
            "p95_tile": round(float(np.percentile(vals, 95)), 5),
            "worst_tiles": [{"sigma": round(s, 5), "x": x, "y": y, "size": tile} for s, x, y in worst]}


def exposure(path):
    lum = _luma(load(path))
    rgb = load(path)
    return {"mean": round(float(lum.mean()), 4), "median": round(float(np.median(lum)), 4),
            "p01": round(float(np.percentile(lum, 1)), 4),
            "p99": round(float(np.percentile(lum, 99)), 4),
            "clipped_pct": round(float((rgb.max(axis=-1) >= 0.995).mean() * 100), 3),
            "crushed_pct": round(float((lum <= 0.005).mean() * 100), 3)}


def _grad_energy(lum):
    gy, gx = np.gradient(lum)
    return float(np.mean(np.hypot(gx, gy)))


def detail_ratio(test, reference):
    """Below about 0.85 on the same crop means the denoiser removed texture or reflections."""
    a, b = _luma(load(test)), _luma(load(reference))
    if a.shape != b.shape:
        im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).resize(b.shape[::-1], Image.LANCZOS)
        a = np.asarray(im, dtype=np.float32) / 255.0
    ref = _grad_energy(b)
    return round(_grad_energy(a) / ref, 3) if ref else None


def flicker(paths):
    """Per-frame mean luminance and frame-to-frame differences. A jump is > 3x the median step.

    temporal_noise is only meaningful when the camera and objects do not move (a locked test)."""
    frames = [_luma(load(p)) for p in paths]
    means = [float(f.mean()) for f in frames]
    steps = [abs(means[i + 1] - means[i]) for i in range(len(means) - 1)]
    med = float(np.median(steps)) if steps else 0.0
    jumps = [i + 1 for i, s in enumerate(steps) if med > 0 and s > 3 * med]
    tn = [float(np.abs(frames[i + 1] - frames[i]).mean()) for i in range(len(frames) - 1)]
    return {"means": [round(m, 4) for m in means], "jumps": jumps,
            "temporal_noise": round(float(np.median(tn)), 5) if tn else 0.0}


def estimate(seconds, test_px, final_px, frames=1, noise_now=None, noise_target=None,
             machines=1, margin=1.25):
    """Time scales with pixel count; Monte Carlo noise falls with the square root of samples,
    so halving noise costs about 4x the time [added]. margin covers scene load and save."""
    t = seconds * (final_px / float(test_px))
    if noise_now and noise_target:
        t *= (noise_now / noise_target) ** 2
    per_frame = t * margin / 3600.0
    return {"hours_per_frame": round(per_frame, 3),
            "hours_total": round(per_frame * frames / max(1, machines), 2)}


def crops(path, out_dir, size=512):
    """Four corners, center and the brightest window of the image, at 100 percent."""
    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(path).convert("RGB")
    w, h = img.size
    s = min(size, w // 2, h // 2)
    lum = _luma(np.asarray(img, dtype=np.float32) / 255.0)
    by, bx = np.unravel_index(int(np.argmax(lum)), lum.shape)
    boxes = {"tl": (0, 0), "tr": (w - s, 0), "bl": (0, h - s), "br": (w - s, h - s),
             "center": ((w - s) // 2, (h - s) // 2),
             "brightest": (min(max(0, bx - s // 2), w - s), min(max(0, by - s // 2), h - s))}
    stem = os.path.splitext(os.path.basename(path))[0]
    out = []
    for key, (x, y) in boxes.items():
        p = os.path.join(out_dir, f"{stem}_crop_{key}.png")
        img.crop((x, y, x + s, y + s)).save(p)
        out.append(p)
    return out


def downscale(src, dst, factor=0.5):
    """Substitute for a frame buffer 'save at 50 percent'. Never overwrite src."""
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError("dst must differ from src")
    img = Image.open(src)
    w, h = img.size
    img.resize((max(1, round(w * factor)), max(1, round(h * factor))), Image.LANCZOS).save(dst)
    return dst


def _main(argv):
    cmd, args = argv[0], argv[1:]
    if cmd == "noise":
        res = noise(args[0])
    elif cmd == "exposure":
        res = exposure(args[0])
    elif cmd == "detail":
        res = {"detail_ratio": detail_ratio(args[0], args[1])}
    elif cmd == "flicker":
        res = flicker(args)
    elif cmd == "crops":
        res = crops(args[0], args[1])
    elif cmd == "estimate":
        s, tw, th, fw, fh = float(args[0]), *map(int, args[1:5])
        frames = int(args[5]) if len(args) > 5 else 1
        res = estimate(s, tw * th, fw * fh, frames)
    elif cmd == "downscale":
        res = {"out": downscale(args[0], args[1], float(args[2]) if len(args) > 2 else 0.5)}
    else:
        raise SystemExit(__doc__)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    _main(sys.argv[1:] or ["help"])
