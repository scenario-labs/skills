#!/usr/bin/env python3
"""Render a text card as a transparent PNG for video-ad overlays.

Text cards (taglines, CTAs, legal supers, the AI-disclosure mark) must be
verbatim and sit inside platform safe zones, so they are rendered
deterministically here and composited as image layers, never generated.

Portrait canvases clear the top 14%, bottom 35%, and 8% per side, the
composite 9:16 safe zone; landscape canvases keep a 10% title-safe margin.

Usage:
  card.py --size 9:16 --text "Night, distilled." --out card.png
  card.py --size 1920x1080 --text "EPA-estimated 310 mi" --position bottom \
      --font-size 40 --backing --badge "AI-generated" --out super.png

Requires Pillow (pip install pillow).
"""

import argparse
import sys

PRESETS = {"9:16": (1080, 1920), "16:9": (1920, 1080)}
FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
MIN_FONT_SIZE = 16


def parse_size(value):
    if value in PRESETS:
        return PRESETS[value]
    try:
        w, h = value.lower().split("x")
        w, h = int(w), int(h)
    except ValueError:
        raise SystemExit(f"invalid --size {value!r}: use 9:16, 16:9, or WIDTHxHEIGHT")
    if w <= 0 or h <= 0:
        raise SystemExit(f"invalid --size {value!r}: dimensions must be positive")
    return w, h


def safe_box(width, height):
    """Return (left, top, right, bottom) of the text-safe region."""
    if height > width:
        return (
            round(width * 0.08),
            round(height * 0.14),
            round(width * 0.92),
            round(height * 0.65),
        )
    margin_w, margin_h = round(width * 0.10), round(height * 0.10)
    return (margin_w, margin_h, width - margin_w, height - margin_h)


def load_font(path, size):
    from PIL import ImageFont

    candidates = [path] if path else FONT_CANDIDATES
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            if path:
                raise SystemExit(f"cannot load font {path!r}")
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def wrap_lines(draw, text, font, max_width):
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_text(draw, text, font_path, box, requested_size):
    left, top, right, bottom = box
    max_width, max_height = right - left, bottom - top
    size = requested_size or max(MIN_FONT_SIZE, max_height // 8)
    while size >= MIN_FONT_SIZE:
        font = load_font(font_path, size)
        lines = wrap_lines(draw, text, font, max_width)
        line_height = round(size * 1.25)
        block_height = line_height * len(lines)
        widest = max(draw.textlength(line, font=font) for line in lines)
        if block_height <= max_height and widest <= max_width:
            return font, lines, line_height
        if requested_size:
            raise SystemExit(
                f"--font-size {requested_size} does not fit the safe zone; "
                "lower it or shorten the text"
            )
        size -= 2
    raise SystemExit("text does not fit the safe zone even at the minimum size")


def render(args):
    from PIL import Image, ImageDraw

    width, height = parse_size(args.size)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    box = safe_box(width, height)
    left, top, right, bottom = box

    font, lines, line_height = fit_text(draw, args.text, args.font, box, args.font_size)
    block_height = line_height * len(lines)
    if args.position == "top":
        y = top
    elif args.position == "bottom":
        y = bottom - block_height
    else:
        y = top + (bottom - top - block_height) // 2

    if args.backing:
        pad = line_height // 2
        widest = max(draw.textlength(line, font=font) for line in lines)
        x0 = (width - widest) // 2 - pad
        draw.rounded_rectangle(
            (x0, y - pad, width - x0, y + block_height + pad),
            radius=pad,
            fill=(0, 0, 0, 153),
        )

    for index, line in enumerate(lines):
        line_width = draw.textlength(line, font=font)
        draw.text(
            ((width - line_width) // 2, y + index * line_height),
            line,
            font=font,
            fill=args.color,
            stroke_width=0 if args.backing else max(1, font.size // 24),
            stroke_fill=(0, 0, 0, 200),
        )

    if args.badge:
        badge_font = load_font(args.font, max(MIN_FONT_SIZE, height // 48))
        draw.text((left, top), args.badge, font=badge_font, fill=args.color,
                  stroke_width=1, stroke_fill=(0, 0, 0, 200))

    image.save(args.out, "PNG")
    return image


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--size", required=True, help="9:16, 16:9, or WIDTHxHEIGHT")
    parser.add_argument("--text", required=True, help="card text, rendered verbatim")
    parser.add_argument("--out", required=True, help="output PNG path")
    parser.add_argument("--font", help="path to a .ttf/.ttc font file")
    parser.add_argument("--font-size", type=int, help="fixed size; errors if it cannot fit")
    parser.add_argument("--color", default="#FFFFFF", help="text color, hex")
    parser.add_argument("--position", choices=["top", "center", "bottom"], default="center")
    parser.add_argument("--backing", action="store_true", help="dark backing box behind the text")
    parser.add_argument("--badge", help="small corner text, e.g. an AI-disclosure mark")
    args = parser.parse_args(argv)
    if not args.text.strip():
        raise SystemExit("--text must not be empty")
    render(args)
    print(args.out)


if __name__ == "__main__":
    main()
