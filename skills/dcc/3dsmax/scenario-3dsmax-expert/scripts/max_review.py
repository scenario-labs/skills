#!/usr/bin/env python3
"""max_review: offline checks on PNGs captured or rendered from 3ds Max (maxkit.capture, a
manual screenshot, or a render). Runner side; never imports pymxs.

System python3. Uses Pillow when installed; otherwise a pure-Python PNG reader (8-bit, non-interlaced) so the checks still run. contact_sheet needs Pillow or
ImageMagick (`montage`).

    image_checks(path, sample=256) -> dict
    compare(a, b, sample=256) -> dict
    contact_sheet(paths, out, cols=4, thumb=400, labels=True) -> str (a new file, never overwritten)

image_checks keys: width, height, mean_luma (0..1), std_luma, clipped (fraction > 0.98), crushed
(fraction < 0.02), center_luma, surround_luma, center_contrast (|center - surround|), unique_colors
(on the sample), alpha_mean, flags (all_black, all_white, uniform, mostly_clipped, mostly_crushed,
transparent, low_contrast_center), histogram (16 luma bins).
Thresholds are [added] defaults, tuned to catch an empty or broken render, not to judge art.
"""
from __future__ import annotations

__version__ = "0.1.0"

import math
import os
import re
import shutil
import struct
import subprocess
import zlib
from pathlib import Path

try:
    from PIL import Image, ImageDraw  # type: ignore
    HAVE_PIL = True
except Exception:  # pragma: no cover
    HAVE_PIL = False


# ---------------------------------------------------------------- pure-Python PNG reader

def _read_png(path) -> tuple[int, int, int, list[bytes]]:
    """Return (width, height, channels, rows) for an 8-bit non-interlaced PNG (gray, GA, RGB, RGBA, palette)."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    pos, idat, plte, trns = 8, b"", None, None
    w = h = depth = ctype = interlace = 0
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif typ == b"PLTE":
            plte = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
    if depth != 8 or interlace:
        raise ValueError("only 8-bit non-interlaced PNG supported without Pillow")
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * ch
    rows, prev = [], bytearray(stride)
    i = 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if f == 1:
            for x in range(ch, stride):
                line[x] = (line[x] + line[x - ch]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x - ch] if x >= ch else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - ch] if x >= ch else 0
                b = prev[x]
                c = prev[x - ch] if x >= ch else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        rows.append(bytes(line))
        prev = line
    if ctype == 3 and plte:
        alpha = trns or b""
        pal = [plte[j:j + 3] + bytes([alpha[j // 3] if j // 3 < len(alpha) else 255])
               for j in range(0, len(plte), 3)]
        rows = [b"".join(pal[v] for v in r) for r in rows]
        ch = 4
    elif ctype in (0, 2) and trns:  # one fully transparent gray level or color (8-bit: low bytes)
        key = bytes(trns[1::2][:ch])
        rows = [b"".join(r[x:x + ch] + (b"\x00" if r[x:x + ch] == key else b"\xff")
                         for x in range(0, len(r), ch)) for r in rows]
        if ch == 1:
            rows = [b"".join(r[x:x + 1] * 3 + r[x + 1:x + 2] for x in range(0, len(r), 2)) for r in rows]
        ch = 4
    return w, h, ch, rows


def _samples(path, sample: int):
    """Yield (r, g, b, a) floats 0..1 on a grid of at most sample x sample, plus (w, h, grid_w, grid_h)."""
    if HAVE_PIL:
        im = Image.open(path).convert("RGBA")
        w, h = im.size
        gw, gh = min(sample, w), min(sample, h)
        small = im.resize((gw, gh), Image.BILINEAR) if (gw, gh) != (w, h) else im
        px = list(small.get_flattened_data() if hasattr(small, "get_flattened_data") else small.getdata())
        return w, h, gw, gh, [(p[0] / 255.0, p[1] / 255.0, p[2] / 255.0, p[3] / 255.0) for p in px]
    w, h, ch, rows = _read_png(path)
    gw, gh = min(sample, w), min(sample, h)
    out = []
    for gy in range(gh):
        row = rows[min(h - 1, int((gy + 0.5) * h / gh))]
        for gx in range(gw):
            x = min(w - 1, int((gx + 0.5) * w / gw)) * ch
            if ch == 1:
                v = row[x] / 255.0
                out.append((v, v, v, 1.0))
            elif ch == 2:
                v = row[x] / 255.0
                out.append((v, v, v, row[x + 1] / 255.0))
            elif ch == 3:
                out.append((row[x] / 255.0, row[x + 1] / 255.0, row[x + 2] / 255.0, 1.0))
            else:
                out.append((row[x] / 255.0, row[x + 1] / 255.0, row[x + 2] / 255.0, row[x + 3] / 255.0))
    return w, h, gw, gh, out


def _next_free(path: str) -> str:
    """path if free, else the first stem_v002.ext, stem_v003.ext ... that does not exist."""
    if not Path(path).exists():
        return path
    stem, ext = os.path.splitext(path)
    m = re.match(r"^(.*)_v(\d{3,})$", stem)
    base, n = (m.group(1), int(m.group(2))) if m else (stem, 1)
    while True:
        n += 1
        cand = f"{base}_v{n:03d}{ext}"
        if not Path(cand).exists():
            return cand


def _luma(p) -> float:
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


def image_checks(path, sample: int = 256) -> dict:
    """Numbers and flags that catch broken renders: black, white, uniform, clipped, crushed, empty center."""
    w, h, gw, gh, px = _samples(path, sample)
    lum = [_luma(p) for p in px]
    n = len(lum)
    mean = sum(lum) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in lum) / n)
    clipped = sum(1 for v in lum if v > 0.98) / n
    crushed = sum(1 for v in lum if v < 0.02) / n
    cx0, cx1, cy0, cy1 = gw // 4, gw - gw // 4, gh // 4, gh - gh // 4
    center, surround = [], []
    for y in range(gh):
        for x in range(gw):
            (center if (cx0 <= x < cx1 and cy0 <= y < cy1) else surround).append(lum[y * gw + x])
    cm = sum(center) / max(1, len(center))
    sm = sum(surround) / max(1, len(surround))
    uniq = len({(int(p[0] * 63), int(p[1] * 63), int(p[2] * 63)) for p in px})
    alpha = sum(p[3] for p in px) / n
    hist = [0] * 16
    for v in lum:
        hist[min(15, int(v * 16))] += 1
    flags = []
    if mean < 0.02 and std < 0.01:
        flags.append("all_black")
    if mean > 0.98 and std < 0.01:
        flags.append("all_white")
    if std < 0.005 or uniq <= 1:
        flags.append("uniform")
    if clipped > 0.25:
        flags.append("mostly_clipped")
    if crushed > 0.5:
        flags.append("mostly_crushed")
    if alpha < 0.05:
        flags.append("transparent")
    if abs(cm - sm) < 0.01 and std < 0.03:
        flags.append("low_contrast_center")
    return {"path": str(path), "width": w, "height": h, "mean_luma": round(mean, 4), "std_luma": round(std, 4),
            "clipped": round(clipped, 4), "crushed": round(crushed, 4), "center_luma": round(cm, 4),
            "surround_luma": round(sm, 4), "center_contrast": round(abs(cm - sm), 4), "unique_colors": uniq,
            "alpha_mean": round(alpha, 4), "histogram": [round(c / n, 4) for c in hist], "flags": flags,
            "ok": not any(f in flags for f in ("all_black", "all_white", "uniform", "transparent"))}


def _regrid(px, gw, gh, tw, th):
    """Nearest-neighbour resample of a gw x gh pixel list onto tw x th."""
    return [px[min(gh - 1, int((y + 0.5) * gh / th)) * gw + min(gw - 1, int((x + 0.5) * gw / tw))]
            for y in range(th) for x in range(tw)]


def compare(a, b, sample: int = 256) -> dict:
    """Mean absolute difference (0..1) and changed-pixel fraction (> 0.1) between two images on a grid.

    Images of different sizes are compared on a common grid and are never "identical".

    Use it to prove an edit changed the render (or that a refactor did not)."""
    wa, ha, gwa, gha, pa = _samples(a, sample)
    wb, hb, gwb, ghb, pb = _samples(b, sample)
    same_size = (wa, ha) == (wb, hb)
    if (gwa, gha) != (gwb, ghb):  # resample both onto one grid so no pixel is dropped
        gw, gh = min(gwa, gwb), min(gha, ghb)
        pa, pb = _regrid(pa, gwa, gha, gw, gh), _regrid(pb, gwb, ghb, gw, gh)
    diffs = [abs(_luma(x) - _luma(y)) for x, y in zip(pa, pb)]
    cdiff = [max(abs(x[i] - y[i]) for i in range(3)) for x, y in zip(pa, pb)]
    n = max(1, len(diffs))
    return {"a": str(a), "b": str(b), "mean_abs_luma_diff": round(sum(diffs) / n, 4),
            "changed_fraction": round(sum(1 for d in cdiff if d > 0.1) / n, 4),
            "max_channel_diff": round(max(cdiff) if cdiff else 0.0, 4),
            "same_size": same_size, "identical": same_size and all(d < 1e-6 for d in cdiff)}


def contact_sheet(paths, out, cols: int = 4, thumb: int = 400, labels: bool = True) -> str:
    """One PNG grid of thumbnails (read this instead of many images). Pillow, else ImageMagick montage.

    Never overwrites: an existing out gets a _v002 style name. Returns the path written."""
    paths = [str(p) for p in paths]
    out = _next_free(str(out))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    if HAVE_PIL:
        ims = [Image.open(p).convert("RGB") for p in paths]
        th = []
        for im in ims:
            s = thumb / max(im.size)
            th.append(im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.BILINEAR))
        cw = max(t.size[0] for t in th)
        chh = max(t.size[1] for t in th) + (16 if labels else 0)
        rows = math.ceil(len(th) / cols)
        sheet = Image.new("RGB", (cw * min(cols, len(th)), chh * rows), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        for i, (t, p) in enumerate(zip(th, paths)):
            x, y = (i % cols) * cw, (i // cols) * chh
            sheet.paste(t, (x, y))
            if labels:
                d.text((x + 4, y + t.size[1] + 2), Path(p).name[:48], fill=(220, 220, 220))
        sheet.save(out)
        return out
    mont = shutil.which("montage")
    if mont:
        cmd = [mont, *paths, "-tile", f"{cols}x", "-geometry", f"{thumb}x{thumb}+4+4", "-background", "#181818"]
        if labels:
            cmd[1:1] = ["-label", "%f"]
        subprocess.run(cmd + [out], check=True, capture_output=True)
        return out
    raise RuntimeError("contact_sheet needs Pillow (pip install pillow) or ImageMagick montage")
