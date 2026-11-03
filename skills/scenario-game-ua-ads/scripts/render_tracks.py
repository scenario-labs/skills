#!/usr/bin/env python3
"""Render every moving UI element of an ad into one transparent ProRes 4444 track each.

Usage: python3 render_tracks.py spec.json OUTDIR [--only NAME ...]

Each element becomes OUTDIR/<name>.mov, cropped to the box it moves in, and gets an entry in
OUTDIR/layers.json: a compose layer with string x, y, width, height, fit "fill", mute true, and
startTime and endTime floored to the millisecond from its frame numbers. Its "source" is the file
name until the upload: build_passes.py maps it to the asset id. --only re-renders the named
elements and keeps the other entries of layers.json.

Spec (paths relative to the spec; every time is a frame number at "fps", "_s" keys are seconds):
{
  "fps": 30, "canvas": [1080, 1920],
  "safe_zone": {"top": 270, "bottom": 1248, "left": 65, "right": 1015, "text_right": 940},
  "elements": [{"type": "counter", "name": "counter", ...}, ...]
}
safe_zone defaults to the 9:16 social zone above on a 1080x1920 canvas and to none elsewhere;
null turns the check off. Any element takes "safe": "text", "meaning" or "none" to override its
check, and "qscale" (ProRes -qscale:v, higher is smaller) to shrink a large track.

Element types, required keys first, defaults in parentheses:
  hand_tap     png, tip [x, y] (fingertip on the PNG), at [x, y], in, press, out; height (220),
               hold (7 frames on the target after the press), approach ([80, 100]), retreat ([60, 70])
  hand_drag    png, tip, keys [[frame, x, y], ...] (fingertip path, linear; a 4th item "out" eases
               into that key), press [frame for a 0.15 s tap, or [from, to] held]; height (220)
  counter      values [PNG per value], steps [frame of each new value], start, end; at ([0, 0],
               top-left of every PNG), bump (1.12), bump_s (0.15), glow ("#FFFFFF", null for none),
               bumps (a bumped PNG per value, drawn as given instead of scaling). A pop that would
               leave the safe zone is shifted inside it; layers.json then gives "bump_shift"
  progress     box [x, y, w, h], fractions [one per value], steps, start, end; colors {rim, track,
               fill_top, fill_bottom}, fill_s (0.27)
  floater      png, events [[frame, cx, cy], ...]; rise (120), dur_s (0.6)
  fly_to_hud   icon, frame, from [x, y], to [x, y]; count (3), icon_px (120), flight_s (0.4),
               stagger_s (0.045), spread (130), outline (7), seed (3). layers.json gives "land",
               the frame the first icon lands: step the counter on it
  burst        center [x, y], frame; scale (1.0), dur_s (0.42), colors, spikes (12), seed (1)
  stars        centers [[x, y], ...], size or sizes, fills [frame per star], end; show (frame the
               empty slots appear, for win stars; omit for stars that pop in), glint_s (null, 0.42
               on an end card), fill, stroke
  icon_pop     png (tight), x, y, frame; curve ([0.4, 0.82, 1.1, 1.05, 1.0]), until (frame: adds
               the still PNG layer from the pop's endTime, with no overlap frame)
  bounce_in    png, center [x, y], height, start, end; rise (260), dur_s (0.42), angle (0),
               hop_every_s (1.2), hop (22)
  label_pulse  png (tight), x, y, start, end; period_s (0.9), amp (0.035), sweeps [frames],
               sweep_s (0.5)
  rays         background (plain PNG), center [x, y], start, end; speed (7 deg/s), ray_deg (9),
               alpha (0.12). An opaque full-canvas H.264 .mp4, not a ProRes track
  group        elements [...]: children drawn into one track, to save compose layers. Their
               "land", "still" and "bump_shift" go under "parts" in layers.json
"""

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SOCIAL_9X16 = {"top": 270, "bottom": 1248, "left": 65, "right": 1015, "text_right": 940}
VISIBLE = 8  # alpha above this counts for the safe zone: a soft glow tail below it is invisible
PRORES = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16",
          "-vendor", "apl0"]


class SpecError(Exception):
    pass


def floor_ms(frame, fps):
    """Compose time of a frame. Rounded up (185 / 30 as 6.167), a layer starts one frame late."""
    return frame * 1000 // fps / 1000


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def ease_in_out(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def back_out(u, s=1.70158):
    u = min(1.0, max(0.0, u)) - 1
    return u * u * ((s + 1) * u + s) + 1


def hexrgb(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def scaled(im, s):
    if abs(s - 1) < 1e-3:
        return im
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def faded(im, a):
    if a >= 1:
        return im
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return out


def paste(canvas, im, x, y):
    x, y = round(x), round(y)
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(im.width, canvas.width - x), min(im.height, canvas.height - y)
    if ex > sx and ey > sy:
        canvas.alpha_composite(im, (x + sx, y + sy), (sx, sy, ex, ey))


def paste_center(canvas, im, cx, cy):
    paste(canvas, im, cx - im.width / 2, cy - im.height / 2)


def visible_bbox(im, alpha=0):
    a = im.getchannel("A")
    return a.point([0] * (alpha + 1) + [255] * (255 - alpha)).getbbox() if alpha else a.getbbox()


def ring(canvas, cx, cy, r, width, color, alpha):
    if alpha <= 0 or r <= 0:
        return
    S = 2
    size = int(2 * (r + width) + 4)
    c = size * S / 2
    big = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse([c - r * S, c - r * S, c + r * S, c + r * S],
                                outline=tuple(color[:3]) + (int(255 * alpha),), width=max(1, int(width * S)))
    paste_center(canvas, big.resize((size, size), Image.LANCZOS), cx, cy)


_sparkles = {}


def sparkle(size, color=(255, 255, 255), angle=0.0, alpha=1.0):
    key = (max(4, int(size)), tuple(color[:3]))
    if key not in _sparkles:
        S, R = 4, key[0] * 2
        D = int(key[0] * 1.6)
        c, w = D * S / 2, R * 0.16
        big = Image.new("RGBA", (D * S, D * S), (0, 0, 0, 0))
        glow = Image.new("RGBA", big.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([c - R * .55, c - R * .55, c + R * .55, c + R * .55], fill=key[1] + (150,))
        big.alpha_composite(glow.filter(ImageFilter.GaussianBlur(R * 0.25)))
        ImageDraw.Draw(big).polygon([(c, c - R), (c + w, c - w), (c + R, c), (c + w, c + w), (c, c + R),
                                     (c - w, c + w), (c - R, c), (c - w, c - w)], fill=key[1] + (255,))
        _sparkles[key] = big.resize((D, D), Image.LANCZOS)
    im = _sparkles[key]
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return faded(im, alpha)


def star(size, fill="#FFD93B", stroke="#6A3A00", empty=False):
    S = 4
    sw, dy = (max(4, size // 26), 0) if empty else (max(4, size // 22), max(4, size // 25))
    D = size + 2 * (sw + dy + 4)
    big = Image.new("RGBA", (D * S, D * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c, R = D * S / 2, size * S / 2

    def points(cx, cy, r_out, r_in):
        return [(cx + (r_out if k % 2 == 0 else r_in) * math.sin(k * math.pi / 5),
                 cy - (r_out if k % 2 == 0 else r_in) * math.cos(k * math.pi / 5) + r_out * 0.06) for k in range(10)]

    p = points(c, c, R, R / 2)
    if empty:
        d.line(p + [p[0]], fill=(255, 255, 255, 235), width=sw * S * 2, joint="curve")
        d.polygon(p, fill=(10, 20, 60, 150))
    else:
        shadow = [(x, y + dy * S) for x, y in p]
        d.line(shadow + [shadow[0]], fill=hexrgb(stroke), width=sw * S * 2, joint="curve")
        d.polygon(shadow, fill=hexrgb(stroke))
        d.line(p + [p[0]], fill=hexrgb(stroke), width=sw * S * 2, joint="curve")
        d.polygon(p, fill=hexrgb(fill))
        # ImageDraw replaces pixels instead of blending, so the gloss needs its own layer
        gloss = Image.new("RGBA", big.size, (0, 0, 0, 0))
        ImageDraw.Draw(gloss).polygon(points(c - R * 0.08, c - R * 0.12, R * 0.55, R * 0.275), fill=(255, 255, 255, 80))
        big.alpha_composite(gloss)
    return big.resize((D, D), Image.LANCZOS)


def shine_band(size, pos, width, alpha, angle=24):
    w, h = size
    S = 2
    big = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(big)
    off = math.tan(math.radians(angle)) * h
    for k, a in ((1.0, alpha * 0.45), (0.45, alpha)):
        half = width * k / 2
        d.polygon([((pos - half) * S, h * S), ((pos + half) * S, h * S), ((pos + half + off) * S, 0),
                   ((pos - half + off) * S, 0)], fill=int(255 * a))
    return big.resize((w, h), Image.LANCZOS)


class Ctx:
    def __init__(self, spec, base):
        self.fps = spec.get("fps", 30)
        self.size = tuple(spec.get("canvas", (1080, 1920)))
        self.base = base
        self.safe = spec["safe_zone"] if "safe_zone" in spec else (SOCIAL_9X16 if self.size == (1080, 1920) else None)
        self._png = {}

    def png(self, path):
        if path not in self._png:
            self._png[path] = Image.open(self.base / path).convert("RGBA")
        return self._png[path]

    def frames(self, seconds):
        return max(1, int(seconds * self.fps + 0.5))

    def zone(self, el, default):
        kind = el.get("safe", default)
        if not self.safe or kind == "none":
            return None
        s = self.safe
        return s["left"], s["top"], s["text_right"] if kind == "text" else s["right"], s["bottom"]


# Each renderer returns (first frame, end frame exclusive, draw(canvas, frame), meta).

def r_hand_tap(el, ctx):
    x, y = el["at"]
    ax, ay = el.get("approach", (80, 100))
    rx, ry = el.get("retreat", (60, 70))
    press, out = el["press"], el["out"]
    release = press + el.get("hold", 7)
    keys = [[el["in"], x + ax, y + ay], [press - 1, x, y, "out"], [release, x, y], [out, x + rx, y + ry, "out"]]
    return r_hand_drag({**el, "keys": keys, "press": [press], "fade": el.get("fade", [3, out - release])}, ctx)


def r_hand_drag(el, ctx):
    src = ctx.png(el["png"])
    k = el.get("height", 220) / src.height
    hand, (tip_x, tip_y) = scaled(src, k), (el["tip"][0] * k, el["tip"][1] * k)
    keys = el["keys"]
    first, last = keys[0][0], keys[-1][0]
    if any(b[0] <= a[0] for a, b in zip(keys, keys[1:])):
        raise SpecError(f"{el['name']}: keys need strictly increasing frames")
    tap = ctx.frames(0.15)
    presses = [(p, p + tap) if isinstance(p, (int, float)) else tuple(p) for p in el.get("press", [])]
    if any(not first <= p0 <= last for p0, _ in presses):
        raise SpecError(f"{el['name']}: every press must fall between the first and last key")
    fade_in, fade_out = el.get("fade", [3, 6])

    def pos(n):
        for a, b in zip(keys, keys[1:]):
            if a[0] <= n <= b[0]:
                u = (n - a[0]) / (b[0] - a[0])
                if len(b) > 3 and b[3] == "out":
                    u = ease_out(u)
                return a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u

    def draw(canvas, n):
        if el.get("ring", True):
            for p0, _ in presses:
                u = (n - p0) / (0.3 * ctx.fps)
                if 0 <= u <= 1:
                    ring(canvas, *pos(p0), 18 + 77 * ease_out(u), 9, (255, 255, 255), (1 - u) ** 1.3)
        s = 0.92 if any(p0 <= n < p1 for p0, p1 in presses) else 1.0
        # Squared: a plain ramp leaves a ghost glove on screen for the last frames of the retreat.
        a = min(1.0, (n - first + 1) / fade_in if fade_in else 1.0, ((last - n) / fade_out) ** 3 if fade_out else 1.0) ** 2
        x, y = pos(n)
        paste(canvas, faded(scaled(hand, s), a), x - tip_x * s, y - tip_y * s)

    return first, last + 1, draw, {}


def clamp_into(im, x, y, zone):
    """Shift a placed image so its visible pixels stay inside zone (left, top, right, bottom)."""
    bb = visible_bbox(im, VISIBLE)
    if not bb or not zone:
        return x, y
    left, top, right, bottom = zone
    x += max(0, left - (x + bb[0])) - max(0, x + bb[2] - right)
    y += max(0, top - (y + bb[1])) - max(0, y + bb[3] - bottom)
    return x, y


def bump_image(im, ox, oy, scale, glow, zone):
    bb = im.getbbox()
    big = scaled(im.crop(bb), scale)
    pad = 40 if glow else 0
    out = Image.new("RGBA", (big.width + 2 * pad, big.height + 2 * pad), (0, 0, 0, 0))
    if glow:
        mask = Image.new("L", out.size, 0)
        mask.paste(big.getchannel("A"), (pad, pad))
        halo = Image.new("RGBA", out.size, hexrgb(glow))
        halo.putalpha(mask.filter(ImageFilter.GaussianBlur(12)).point(lambda v: min(255, 2 * v) * 3 // 4))
        out.alpha_composite(halo)
    out.alpha_composite(big, (pad, pad))
    x = round(ox + (bb[0] + bb[2]) / 2 - out.width / 2)
    y = round(oy + (bb[1] + bb[3]) / 2 - out.height / 2)
    cx, cy = clamp_into(out, x, y, zone)
    return out, (cx, cy), (cx - x, cy - y)


def r_counter(el, ctx):
    ox, oy = el.get("at", (0, 0))
    rest = [ctx.png(p) for p in el["values"]]
    steps, bumps = el.get("steps", []), el.get("bumps")
    if len(steps) != len(rest) - 1 or (bumps and len(bumps) != len(rest)):
        raise SpecError(f"{el['name']}: give one step frame per value after the first, and one bump PNG per value")
    zone = ctx.zone(el, "text")
    if bumps:
        bumped = [bump_image(ctx.png(p), ox, oy, 1.0, None, zone) for p in bumps]
    else:
        bumped = [bump_image(im, ox, oy, el.get("bump", 1.12), el.get("glow", "#FFFFFF"), zone) for im in rest]
    hold = ctx.frames(el.get("bump_s", 0.15))

    def draw(canvas, n):
        v = sum(n >= s for s in steps)
        if v and n - steps[v - 1] < hold:
            im, (x, y), _ = bumped[v]
            paste(canvas, im, x, y)
        else:
            paste(canvas, rest[v], ox, oy)

    shift = max((b[2] for b in bumped), key=lambda d: abs(d[0]) + abs(d[1]))
    return el["start"], el["end"], draw, {"bump_shift": list(shift)} if any(shift) else {}


def bar_image(w, h, frac, colors, flash):
    S, pad = 3, 8
    im = Image.new("RGBA", ((w + 2 * pad) * S, (h + 2 * pad) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def box(x0, y0, x1, y1):
        return x0 * S, y0 * S, x1 * S, y1 * S

    d.rounded_rectangle(box(pad, pad + 5, pad + w, pad + h + 5), h * S // 2, fill=(0, 0, 0, 90))
    d.rounded_rectangle(box(pad, pad, pad + w, pad + h), h * S // 2, fill=hexrgb(colors["rim"]))
    rim = max(2, h // 6)
    inner_h, x0, y0, x1 = h - 2 * rim, pad + rim, pad + rim, pad + w - rim
    d.rounded_rectangle(box(x0, y0, x1, y0 + inner_h), inner_h * S // 2, fill=hexrgb(colors["track"]))
    if frac > 0:
        mask = Image.new("L", im.size, 0)
        fill_w = max(inner_h, (x1 - x0) * min(1.0, frac))
        ImageDraw.Draw(mask).rounded_rectangle(box(x0, y0, x0 + fill_w, y0 + inner_h), inner_h * S // 2, fill=255)
        top, bottom = (np.array(hexrgb(colors[k])[:3], np.float32) for k in ("fill_top", "fill_bottom"))
        k = np.clip((np.arange(im.height) / S - y0) / inner_h, 0, 1)[:, None]
        rows = top + (bottom - top) * k
        rows[(k[:, 0] > 0.12) & (k[:, 0] < 0.32)] += 50
        rows += (255 - rows) * flash
        fill = np.repeat(np.clip(rows, 0, 255).astype(np.uint8)[:, None, :], im.width, 1)
        im.paste(Image.fromarray(fill, "RGB"), (0, 0), mask)
    return im.resize((w + 2 * pad, h + 2 * pad), Image.LANCZOS)


def r_progress(el, ctx):
    x, y, w, h = el["box"]
    fractions, steps = el["fractions"], el.get("steps", [])
    if len(steps) != len(fractions) - 1:
        raise SpecError(f"{el['name']}: give one step frame per fraction after the first")
    colors = {"rim": "#FFFFFF", "track": "#1B2450", "fill_top": "#C6FF5E", "fill_bottom": "#4CB817",
              **el.get("colors", {})}
    grow = ctx.frames(el.get("fill_s", 0.27))

    def draw(canvas, n):
        v = sum(n >= s for s in steps)
        since = n - steps[v - 1] if v else 10 ** 6
        frac = fractions[v - 1] + (fractions[v] - fractions[v - 1]) * ease_out(since / grow) if since < grow else fractions[v]
        flash = (0.7, 0.45, 0.2)[since] if since < 3 else 0.0
        pop = (1.14, 1.09, 1.05, 1.02)[since] if since < 4 else 1.0
        paste_center(canvas, scaled(bar_image(w, h, frac, colors, flash), pop), x + w / 2, y + h / 2)

    return el["start"], el["end"], draw, {}


def r_floater(el, ctx):
    im, events = ctx.png(el["png"]), el["events"]
    dur, rise, pop = ctx.frames(el.get("dur_s", 0.6)), el.get("rise", 120), (0.7, 1.08, 1.0)

    def draw(canvas, n):
        for f0, cx, cy in events:
            k = n - f0
            if 0 <= k < dur:
                u = k / dur
                a = 1.0 if u < 2 / 3 else 3 * (1 - u)
                paste_center(canvas, faded(scaled(im, pop[k] if k < len(pop) else 1.0), a), cx, cy - rise * ease_out(u))

    return min(e[0] for e in events), max(e[0] for e in events) + dur, draw, {}


def outlined(icon, width):
    """White rim around an icon, so a small one reads over any board."""
    pad = Image.new("RGBA", (icon.width + 4 * width, icon.height + 4 * width), (0, 0, 0, 0))
    pad.paste(icon, (2 * width, 2 * width))
    rim = pad.getchannel("A").filter(ImageFilter.MaxFilter(2 * width + 1)).filter(ImageFilter.GaussianBlur(1))
    out = Image.new("RGBA", pad.size, (255, 255, 255, 0))
    out.putalpha(rim)
    out.alpha_composite(pad)
    return out


def r_fly_to_hud(el, ctx):
    icon = ctx.png(el["icon"])
    icon = icon.crop(icon.getbbox())
    icon = scaled(icon, el.get("icon_px", 120) / max(icon.size))
    if el.get("outline", 7):
        icon = outlined(icon, el.get("outline", 7))
    (sx, sy), (tx, ty) = el["from"], el["to"]
    count, flight, stagger = el.get("count", 3), el.get("flight_s", 0.4), el.get("stagger_s", 0.045)
    spread, color = el.get("spread", 130), hexrgb(el.get("sparkle", "#FFE95C"))[:3]
    rnd = random.Random(el.get("seed", 3))
    dx, dy = tx - sx, ty - sy
    length = math.hypot(dx, dy) or 1.0
    paths = []
    for k in range(count):
        side = (-1) ** k * (0.6 + 0.4 * rnd.random())
        ctrl = ((sx + tx) / 2 - dy / length * spread * side, (sy + ty) / 2 + dx / length * spread * side)
        jitter = (rnd.uniform(-30, 30), rnd.uniform(-10, 20))
        paths.append(((sx + jitter[0], sy + jitter[1]), ctrl, k * stagger, rnd.uniform(-25, 25)))
    f0 = el["frame"]

    def bezier(p0, pc, q):
        return ((1 - q) ** 2 * p0[0] + 2 * (1 - q) * q * pc[0] + q ** 2 * tx,
                (1 - q) ** 2 * p0[1] + 2 * (1 - q) * q * pc[1] + q ** 2 * ty)

    def draw(canvas, n):
        t = (n - f0) / ctx.fps + 1e-6
        u0 = t / 0.25
        if u0 <= 1:
            ring(canvas, sx, sy, 20 + 70 * ease_out(u0), 8 * (1 - u0) + 2, (255, 255, 255), 1 - u0)
            for m in range(5):
                ag, rr = -math.pi / 2 + (m - 2) * 0.55, 30 + 80 * ease_out(u0)
                paste_center(canvas, sparkle(26 * (1 - .5 * u0), color, 40 * m, 1 - u0),
                             sx + math.cos(ag) * rr, sy + math.sin(ag) * rr)
        for p0, pc, delay, rot in paths:
            p = (t - delay) / flight
            if 0 <= p <= 1:
                for lag, alpha in ((0.10, .7), (0.20, .45), (0.30, .25)):
                    if p > lag:
                        paste_center(canvas, sparkle(20, color, 0, alpha), *bezier(p0, pc, ease_in_out(p - lag)))
                q = ease_in_out(p)
                s = 0.6 + 0.55 * min(1, p * 4) if p < 0.25 else 1.15 - 0.65 * (p - .25) / .75
                paste_center(canvas, scaled(icon, s).rotate(rot * (1 - q), resample=Image.BICUBIC, expand=True),
                             *bezier(p0, pc, q))
            elif 1 < p <= 1 + 0.2 / flight:
                v = (p - 1) * flight / 0.2
                ring(canvas, tx, ty, 30 + 40 * v, 6 * (1 - v) + 1, (255, 255, 255), 1 - v)
                paste_center(canvas, sparkle(44 * (1 - v) + 8, color, 90 * v, 1 - v), tx + 26, ty - 26)

    end = f0 + ctx.frames((count - 1) * stagger + flight + 0.24)
    return f0, end, draw, {"land": f0 + ctx.frames(flight)}


def r_burst(el, ctx):
    (cx, cy), scale = el["center"], el.get("scale", 1.0)
    colors = [hexrgb(c) for c in el.get("colors", ("#FFFFFF", "#FFE55C", "#FF9A2E"))]
    spikes, f0 = el.get("spikes", 12), el["frame"]
    n = ctx.frames(el.get("dur_s", 0.42)) + 1
    rnd = random.Random(el.get("seed", 1))
    angles = [k * 2 * math.pi / spikes + rnd.uniform(-.18, .18) for k in range(spikes)]
    lengths = [rnd.uniform(.75, 1.15) for _ in range(spikes)]
    sparks = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(.7, 1.1), rnd.uniform(26, 40) * scale, rnd.uniform(0, 90))
              for _ in range(9)]
    R, S = int(400 * scale), 2

    def draw(canvas, frame):
        i = frame - f0
        u = i / (n - 1)
        local = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
        big = Image.new("RGBA", (4 * R, 4 * R), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        a = 1.0 if u < 0.45 else max(0.0, 1 - (u - 0.45) / 0.55)
        for k, (ag, ln) in enumerate(zip(angles, lengths)):
            r_in = (30 + 150 * ease_out(u)) * scale * ln
            r_out = (80 + 250 * ease_out(min(1, u * 1.7))) * scale * ln
            if r_out <= r_in:
                continue
            w = (30 * (1 - u) + 4) * scale
            px, py = -math.sin(ag), math.cos(ag)
            base = (R + math.cos(ag) * r_in, R + math.sin(ag) * r_in)
            d.polygon([((base[0] + px * w) * S, (base[1] + py * w) * S), ((base[0] - px * w) * S, (base[1] - py * w) * S),
                       ((R + math.cos(ag) * r_out) * S, (R + math.sin(ag) * r_out) * S)],
                      fill=colors[k % 2][:3] + (int(255 * a),))
        local.alpha_composite(big.resize(local.size, Image.LANCZOS))
        if i <= 2:  # the flash core stays small and translucent, so the contact point stays readable
            core = Image.new("RGBA", local.size, (0, 0, 0, 0))
            rr = 60 * scale * (1 - i / 3)
            ImageDraw.Draw(core).ellipse([R - rr, R - rr, R + rr, R + rr], fill=(255, 255, 255, int(150 * (1 - i / 3))))
            local.alpha_composite(core.filter(ImageFilter.GaussianBlur(6)))
        if u < .75:
            k = u / .75
            ring(local, R, R, (40 + 220 * ease_out(k)) * scale, (20 * (1 - k) + 3) * scale, colors[0], 1 - k)
        for ag, speed, size, rot in sparks:
            rr = (60 + 230 * ease_out(u) * speed) * scale
            alpha = 1.0 if u < .55 else max(0.0, 1 - (u - .55) / .45)
            paste_center(local, sparkle(size * (1 - .5 * u), colors[1], rot + 200 * u, alpha),
                         R + math.cos(ag) * rr, R + math.sin(ag) * rr)
        paste(canvas, local, cx - R, cy - R)

    return f0, f0 + n, draw, {}


def r_stars(el, ctx):
    centers, fills, show = el["centers"], el["fills"], el.get("show")
    sizes = el.get("sizes") or [el["size"]] * len(centers)
    if not len(centers) == len(fills) == len(sizes):
        raise SpecError(f"{el['name']}: centers, fills and sizes need one entry per star")
    fill, stroke = el.get("fill", "#FFD93B"), el.get("stroke", "#6A3A00")
    full = [star(s, fill, stroke) for s in sizes]
    empty = [star(s, empty=True) for s in sizes] if show is not None else None
    curve = (1.55, 1.25, 0.92, 1.04) if show is not None else (0.3, 0.8, 1.22, 1.08)
    burst = el.get("burst", show is not None)
    glint = el.get("glint_s")
    g0 = max(fills) + ctx.frames(0.3)
    order = list(range(len(centers)))
    random.Random(el.get("seed", 5)).shuffle(order)

    def draw(canvas, n):
        g = gu = None
        if glint and n >= g0:
            t = (n - g0) / ctx.fps
            g, gu = order[int(t // glint) % len(centers)], (t % glint) / 0.34
        for k, ((cx, cy), f, size) in enumerate(zip(centers, fills, sizes)):
            if n < f:
                j = n - show - 2 * k if show is not None else -1
                if j >= 0:
                    paste_center(canvas, scaled(empty[k], (0.3, 0.75, 1.1)[j] if j < 3 else 1.0), cx, cy)
                continue
            j = n - f
            s = curve[j] if j < len(curve) else 1.0
            if g == k and gu <= 1:
                s *= 1 + 0.08 * math.sin(math.pi * gu)
            u = j / (0.32 * ctx.fps)
            if burst and u <= 1:
                ring(canvas, cx, cy, size * (0.35 + 0.55 * ease_out(u)), 10 * (1 - u) + 2, (255, 255, 255), 1 - u)
            paste_center(canvas, scaled(full[k], s), cx, cy)
            if burst and u <= 1:
                for m in range(6):
                    ag, rr = m * math.pi / 3 + 0.3, size * (0.3 + 0.55 * ease_out(u))
                    paste_center(canvas, sparkle(30 * (1 - .6 * u), (255, 240, 150), 60 * u, 1 - u ** 2),
                                 cx + math.cos(ag) * rr, cy + math.sin(ag) * rr)
            if g == k and gu <= 1:
                paste_center(canvas, sparkle(size * 0.62 * math.sin(math.pi * gu) + 4, (255, 255, 255), 90 * gu),
                             cx + size * 0.28, cy - size * 0.3)

    return show if show is not None else min(fills), el["end"], draw, {}


def r_icon_pop(el, ctx):
    im, x, y, f0 = ctx.png(el["png"]), el["x"], el["y"], el["frame"]
    curve = el.get("curve", [0.4, 0.82, 1.1, 1.05, 1.0])
    cx, cy = x + im.width / 2, y + im.height / 2

    def draw(canvas, n):
        s = curve[n - f0]
        if abs(s - 1) < 1e-3:  # the last frame matches the still layer pixel for pixel
            paste(canvas, im, x, y)
        else:
            paste_center(canvas, scaled(im, s), cx, cy)

    end, meta = f0 + len(curve), {}
    if "until" in el:
        if abs(curve[-1] - 1) > 1e-3:
            raise SpecError(f"{el['name']}: a pop that hands over to the still must end on scale 1.0")
        meta["still"] = {"type": "image", "source": Path(el["png"]).name, "x": str(x), "y": str(y),
                         "width": str(im.width), "height": str(im.height), "fit": "fill",
                         "startTime": floor_ms(end, ctx.fps), "endTime": floor_ms(el["until"], ctx.fps)}
    return f0, end, draw, meta


def r_bounce_in(el, ctx):
    im = ctx.png(el["png"])
    im = im.crop(im.getbbox())
    h = el["height"]
    im = im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)
    if el.get("angle"):
        im = im.rotate(el["angle"], resample=Image.BICUBIC, expand=True)
    (cx, cy), f0 = el["center"], el["start"]
    rise, dur, hop_every, hop = el.get("rise", 260), el.get("dur_s", 0.42), el.get("hop_every_s", 1.2), el.get("hop", 22)

    def draw(canvas, n):
        t = (n - f0) / ctx.fps + 1e-6
        sx = sy = a = 1.0
        dy = 0.0
        if t < dur:
            u = t / dur
            dy, a = rise * (1 - back_out(u, 2.2)), min(1.0, u * 4)
            sx, sy = 1 - 0.06 * (1 - u), 1 + 0.10 * (1 - u)
        elif t - dur < 0.16:
            v = math.sin(math.pi * (t - dur) / 0.16)
            sx, sy = 1 + 0.12 * v, 1 - 0.10 * v
        else:
            j = t - dur
            phase = (j - 0.16) % hop_every
            if j > 0.6 and phase < 0.3:
                v = phase / 0.3
                dy = -hop * math.sin(math.pi * v)
                if v > .8:
                    sx, sy = 1.06, 0.94
        frame = im.resize((max(1, round(im.width * sx)), max(1, round(im.height * sy))), Image.LANCZOS)
        paste_center(canvas, faded(frame, a), cx, cy + dy + im.height * (1 - sy) / 2)

    return f0, el["end"], draw, {}


def r_label_pulse(el, ctx):
    im, x, y, f0 = ctx.png(el["png"]), el["x"], el["y"], el["start"]
    cx, cy = x + im.width / 2, y + im.height / 2
    period, amp = el.get("period_s", 0.9), el.get("amp", 0.035)
    sweep, sweeps = ctx.frames(el.get("sweep_s", 0.5)), el.get("sweeps", [])
    rgba = np.asarray(im, np.float32)
    alpha = rgba[..., 3] / 255
    slant = math.tan(math.radians(24)) * im.height

    def draw(canvas, n):
        base = im
        for s0 in sweeps:
            u = (n - s0) / sweep
            if 0 <= u <= 1:
                band = np.asarray(shine_band(im.size, -140 - slant + (im.width + 280 + slant) * ease_in_out(u), 140, 0.55),
                                  np.float32) / 255 * alpha
                arr = rgba.copy()
                arr[..., :3] += (255 - arr[..., :3]) * band[..., None]
                base = Image.fromarray(arr.astype(np.uint8), "RGBA")
        i = n - f0
        s = (0.6, 0.92, 1.08, 1.0)[i] if i < 4 else 1 + amp * (0.5 - 0.5 * math.cos(2 * math.pi * (i - 4) / ctx.fps / period))
        paste_center(canvas, scaled(base, s), cx, cy)

    return f0, el["end"], draw, {}


RENDERERS = {
    "hand_tap": (r_hand_tap, "none"), "hand_drag": (r_hand_drag, "none"), "counter": (r_counter, "text"),
    "progress": (r_progress, "meaning"), "floater": (r_floater, "text"), "fly_to_hud": (r_fly_to_hud, "none"),
    "burst": (r_burst, "none"), "stars": (r_stars, "meaning"), "icon_pop": (r_icon_pop, "meaning"),
    "bounce_in": (r_bounce_in, "meaning"), "label_pulse": (r_label_pulse, "text"),
}


def capture(ctx, first, end, draw):
    """Draw each frame on a full canvas and keep only its visible crop and offset."""
    frames = []
    for n in range(first, end):
        canvas = Image.new("RGBA", ctx.size, (0, 0, 0, 0))
        draw(canvas, n)
        bb = canvas.getbbox()
        frames.append((canvas.crop(bb), bb[:2]) if bb else (None, (0, 0)))
    return frames


def union(frames, alpha=0):
    boxes = []
    for im, (x, y) in frames:
        bb = visible_bbox(im, alpha) if im is not None else None
        if bb:
            boxes.append((x + bb[0], y + bb[1], x + bb[2], y + bb[3]))
    if not boxes:
        return None
    return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)


def safe_warnings(name, bb, zone):
    if not bb or not zone:
        return []
    left, top, right, bottom = zone
    checks = [(bb[1] < top, f"reaches y {bb[1]}, above the safe top {top}"),
              (bb[3] > bottom, f"reaches y {bb[3]}, below the safe bottom {bottom}"),
              (bb[0] < left, f"reaches x {bb[0]}, left of the safe edge {left}"),
              (bb[2] > right, f"reaches x {bb[2]}, right of the safe edge {right}")]
    return [f"{name}: {text}" for hit, text in checks if hit]


def render(el, ctx):
    """Frames of one element: (first, crops with offsets, meta, warnings)."""
    name, kind = el.get("name", el.get("type")), el.get("type")
    try:
        if kind == "group":
            children = [(c.get("name", c.get("type")), c) for c in el["elements"]]
            parts = [(child, render({**c, "name": f"{name}/{child}"}, ctx)) for child, c in children]
            first = min(p[0] for _, p in parts)
            end = max(p[0] + len(p[1]) for _, p in parts)

            def draw(canvas, n):
                for _, (start, frames, _, _) in parts:
                    if start <= n < start + len(frames) and frames[n - start][0] is not None:
                        im, (x, y) = frames[n - start]
                        canvas.alpha_composite(im, (x, y))

            meta = {child: p[2] for child, p in parts if p[2]}
            warnings = [w for _, p in parts for w in p[3]]
            return first, capture(ctx, first, end, draw), {"parts": meta} if meta else {}, warnings
        if kind not in RENDERERS:
            raise SpecError(f"{name}: unknown type {kind!r}")
        renderer, default_safe = RENDERERS[kind]
        first, end, draw, meta = renderer({**el, "name": name}, ctx)
        if end <= first:
            raise SpecError(f"{name}: ends before it starts")
        frames = capture(ctx, first, end, draw)
        return first, frames, meta, safe_warnings(name, union(frames, VISIBLE), ctx.zone(el, default_safe))
    except KeyError as e:
        raise SpecError(f"{name}: missing key {e}") from None


def even_box(bb, size):
    x0, y0 = bb[0] // 2 * 2, bb[1] // 2 * 2
    x1, y1 = min(size[0], -(-bb[2] // 2) * 2), min(size[1], -(-bb[3] // 2) * 2)
    return x0, y0, x1 - x0, y1 - y0


def encode_track(name, first, frames, ctx, outdir, qscale=None):
    bb = union(frames)
    if not bb:
        raise SpecError(f"{name}: nothing visible on any frame")
    x0, y0, w, h = even_box(bb, ctx.size)
    # A fresh directory per render: frames left over from a longer earlier build would be encoded too.
    with tempfile.TemporaryDirectory(prefix=f"{name}-") as tmp:
        tmp = Path(tmp)
        for i, (im, (x, y)) in enumerate(frames):
            frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            if im is not None:
                frame.paste(im, (x - x0, y - y0))
            frame.save(tmp / f"{i:05d}.png", compress_level=1)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(ctx.fps), "-i", str(tmp / "%05d.png"), *PRORES]
        if qscale:
            cmd += ["-qscale:v", str(qscale)]
        subprocess.run(cmd + [str(tmp / "out.mov")], check=True)
        shutil.move(tmp / "out.mov", outdir / f"{name}.mov")
    return {"type": "video", "source": f"{name}.mov", "x": str(x0), "y": str(y0), "width": str(w), "height": str(h),
            "fit": "fill", "mute": True, "startTime": floor_ms(first, ctx.fps),
            "endTime": floor_ms(first + len(frames), ctx.fps)}


def render_rays(el, ctx, outdir):
    name, (W, H) = el["name"], ctx.size
    bg = np.asarray(ctx.png(el["background"]).convert("RGB").resize((W, H)), np.float32)
    cx, cy = el["center"]
    speed, ray, alpha = el.get("speed", 7.0), el.get("ray_deg", 9.0), el.get("alpha", 0.12)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    theta = np.degrees(np.arctan2(yy - cy, xx - cx))
    px_per_deg = (np.hypot(xx - cx, yy - cy) + 1) * math.pi / 180
    with tempfile.TemporaryDirectory(prefix=f"{name}-") as tmp:
        out = Path(tmp) / "out.mp4"
        enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", str(ctx.fps), "-i", "-", "-c:v", "libx264", "-crf", "14",
                                "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                               stdin=subprocess.PIPE)
        for i in range(el["end"] - el["start"]):
            dist = np.abs(((theta + speed * i / ctx.fps) % (2 * ray)) - ray / 2)
            cover = np.clip((ray / 2 - dist) * px_per_deg + 0.5, 0, 1)  # a 1 px soft edge
            enc.stdin.write((bg + (255 - bg) * (alpha * cover)[..., None]).astype(np.uint8).tobytes())
        enc.stdin.close()
        if enc.wait():
            raise SpecError(f"{name}: ffmpeg failed")
        shutil.move(out, outdir / f"{name}.mp4")
    return {"file": f"{name}.mp4", "frames": [el["start"], el["end"]],
            "layer": {"type": "video", "source": f"{name}.mp4", "x": "0", "y": "0", "width": str(W),
                      "height": str(H), "fit": "cover", "mute": True, "startTime": floor_ms(el["start"], ctx.fps),
                      "endTime": floor_ms(el["end"], ctx.fps)}}


def build(el, ctx, outdir):
    if el.get("type") == "rays":
        try:
            return render_rays(el, ctx, outdir)
        except KeyError as e:
            raise SpecError(f"{el['name']}: missing key {e}") from None
    first, frames, meta, warnings = render(el, ctx)
    layer = encode_track(el["name"], first, frames, ctx, outdir, el.get("qscale"))
    entry = {"file": f"{el['name']}.mov", "frames": [first, first + len(frames)], "layer": layer, **meta}
    if warnings:
        entry["warnings"] = warnings
    return entry


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--only", nargs="+", metavar="NAME", help="render only these elements")
    args = ap.parse_args(argv)
    spec = json.loads(args.spec.read_text())
    ctx = Ctx(spec, args.spec.parent)
    elements = spec.get("elements", [])
    names = [el.get("name") for el in elements]
    if None in names or len(set(names)) != len(names):
        print("every element needs a unique name", file=sys.stderr)
        return 2
    args.outdir.mkdir(parents=True, exist_ok=True)
    index_path = args.outdir / "layers.json"
    index = {"fps": ctx.fps, "canvas": list(ctx.size), "layers": {}}
    if args.only and index_path.exists():
        index["layers"] = json.loads(index_path.read_text()).get("layers", {})
    try:
        for el in elements:
            if args.only and el["name"] not in args.only:
                continue
            entry = build(el, ctx, args.outdir)
            index["layers"][el["name"]] = entry
            lay = entry["layer"]
            extra = "".join(f", {k} {entry[k]}" for k in ("land", "bump_shift") if k in entry)
            print(f"{el['name']}: frames {entry['frames'][0]}-{entry['frames'][1] - 1}, box {lay['x']},{lay['y']} "
                  f"{lay['width']}x{lay['height']}, {lay['startTime']}-{lay['endTime']} s{extra}")
            for w in entry.get("warnings", []):
                print(f"WARN {w}", file=sys.stderr)
            if "bump_shift" in entry:
                print(f"NOTE {el['name']}: the pop moves {entry['bump_shift']} px to stay in the safe zone; "
                      "move the counter inward for a centered pop", file=sys.stderr)
    except SpecError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    index_path.write_text(json.dumps(index, indent=1) + "\n")
    print(f"wrote {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
