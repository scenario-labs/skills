"""Pillow fallback for text-layer payloads when no browser is available.

Plain typography only: font, size, color, alignment, line height, letter
spacing, and the overflow modes are honored, but none of the HTML/CSS a
browser render offers, and rich layers are out of reach entirely. Fonts
resolve in order: font_url (.ttf/.otf download), font_family via Google
Fonts (TrueType variant), then a local system font as a last resort.

Requires Pillow (pip install pillow).
"""

import re
import sys
import tempfile
import urllib.request
from pathlib import Path

from html_render import MIN_SHRINK_SIZE, google_fonts_url

_FONT_FETCH_TIMEOUT_S = 20

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
_BIDI_CONTROLS_RE = re.compile(r"[\u061C\u200E\u200F\u202A-\u202E\u2066-\u2069]")
_L1_IGNORABLE = frozenset(("BN", "LRE", "RLE", "LRO", "RLO", "PDF"))
_L1_WHITESPACE = frozenset(("WS", "FSI", "LRI", "RLI", "PDI"))
_L1_BREAK = frozenset(("B", "S"))
_BIDI_DEBUG_RE = re.compile(
    r"original_classes:\s*\[(.*?)\],\s*levels:\s*\[(.*?)\],\s*paragraphs:\s*\[(.*?)\],\s*\}\s*\Z",
    re.S,
)
_BIDI_CLASS_RE = re.compile(r"([A-Z]+),")
_BIDI_LEVEL_RE = re.compile(r"Level\(\s*(\d+),\s*\)")
_BIDI_PARA_RE = re.compile(r"range:\s*(\d+)\.\.(\d+),\s*level:\s*Level\(\s*(\d+),\s*\)")

_SYSTEM_FONT_CANDIDATES = (
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)

_ARABIC_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/GeezaPro.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)

_ARABIC_RESHAPER = None


def _has_raqm():
    from PIL import features

    return bool(features.check("raqm"))


def _uses_raqm(font):
    if font is None:
        return False
    from PIL import ImageFont

    raqm = getattr(getattr(ImageFont, "Layout", None), "RAQM", None)
    return raqm is not None and getattr(font, "layout_engine", None) == raqm


def _get_arabic_reshaper():
    global _ARABIC_RESHAPER
    if _ARABIC_RESHAPER is None:
        import importlib

        arabic_reshaper = importlib.import_module("arabic_reshaper")
        # Keep vowel marks and pre-shift them so visual-order reversal leaves
        # each combining mark after its base glyph.
        _ARABIC_RESHAPER = arabic_reshaper.ArabicReshaper(
            configuration={"delete_harakat": False, "shift_harakat_position": True}
        )
    return _ARABIC_RESHAPER


def _apply_l1_levels(classes, levels, para_level):
    reset = True
    for idx in range(len(classes) - 1, -1, -1):
        cls = classes[idx]
        if cls in _L1_BREAK:
            levels[idx] = para_level
            reset = True
        elif reset and (cls in _L1_WHITESPACE or cls in _L1_IGNORABLE):
            levels[idx] = para_level
        elif cls in _L1_IGNORABLE:
            pass
        else:
            reset = False
    after_break = False
    for idx, cls in enumerate(classes):
        if cls in _L1_BREAK:
            after_break = True
        elif after_break and cls in _L1_IGNORABLE:
            levels[idx] = para_level
        else:
            after_break = False


def _reorder_and_mirror(text, get_display, mirrored):
    if not text or not mirrored or not any(ch in mirrored for ch in text):
        return get_display(text)
    # python-bidi 0.6.x wraps unicode_bidi::reorder_line, which skips UAX #9 L4
    # glyph mirroring; read its resolved levels so odd-level brackets mirror.
    dbg = get_display(text, debug=True)
    idx_cls = dbg.rfind("\n    original_classes: [") if isinstance(dbg, str) else -1
    match = _BIDI_DEBUG_RE.search(dbg, idx_cls) if idx_cls >= 0 else None
    if match is None:
        return get_display(text)
    byte_classes = _BIDI_CLASS_RE.findall(match.group(1))
    byte_levels = [int(raw) for raw in _BIDI_LEVEL_RE.findall(match.group(2))]
    paras = [
        (int(start), int(end), int(level))
        for start, end, level in _BIDI_PARA_RE.findall(match.group(3))
    ]
    chars = list(text)
    byte_to_char = {}
    char_byte_start = []
    pos = 0
    for idx, ch in enumerate(chars):
        byte_to_char[pos] = idx
        char_byte_start.append(pos)
        pos += len(ch.encode("utf-8"))
    byte_to_char[pos] = len(chars)
    if pos != len(byte_levels) or pos != len(byte_classes):
        return get_display(text)

    parts = []
    for start_b, end_b, para_level in paras:
        c_start, c_end = byte_to_char[start_b], byte_to_char[end_b]
        p_chars = chars[c_start:c_end]
        levels = [byte_levels[char_byte_start[i]] for i in range(c_start, c_end)]
        classes = [byte_classes[char_byte_start[i]] for i in range(c_start, c_end)]
        _apply_l1_levels(classes, levels, para_level)
        p_chars = [
            mirrored.get(ch, ch) if (levels[i] & 1) else ch for i, ch in enumerate(p_chars)
        ]
        if levels:
            max_lv = max(levels)
            min_odd = min((lv for lv in levels if lv & 1), default=None)
            if min_odd is not None:
                for lv in range(max_lv, min_odd - 1, -1):
                    run_start = None
                    for idx, clv in enumerate(levels):
                        if clv >= lv:
                            if run_start is None:
                                run_start = idx
                        elif run_start is not None:
                            p_chars[run_start:idx] = reversed(p_chars[run_start:idx])
                            run_start = None
                    if run_start is not None:
                        p_chars[run_start:] = reversed(p_chars[run_start:])
        parts.append("".join(p_chars))
    return "".join(parts)


def _bidi_display(text):
    import importlib

    bidi = importlib.import_module("bidi")
    get_display = getattr(bidi, "get_display", None)
    if get_display is not None:
        try:
            mirrored = getattr(importlib.import_module("bidi.algorithm"), "MIRRORED", None)
        except ImportError:
            mirrored = None
        if not isinstance(mirrored, dict):
            mirrored = {}
        try:
            visual = _reorder_and_mirror(text, get_display, mirrored)
        except TypeError:
            visual = get_display(text)
        except AssertionError:
            try:
                visual = get_display(_BIDI_CONTROLS_RE.sub("", text))
            except AssertionError:
                return text
        return _BIDI_CONTROLS_RE.sub("", visual)

    legacy_get_display = importlib.import_module("bidi.algorithm").get_display
    try:
        visual = legacy_get_display(text)
    except AssertionError:
        # Legacy bidi.algorithm asserts on U+2066..U+2069 isolate controls.
        try:
            visual = legacy_get_display(_BIDI_CONTROLS_RE.sub("", text))
        except AssertionError:
            return text
    return _BIDI_CONTROLS_RE.sub("", visual)


def _shape_arabic_if_needed(text, font=None):
    if not _ARABIC_RE.search(text) or _uses_raqm(font):
        return text
    try:
        reshaper = _get_arabic_reshaper()
        return _bidi_display(reshaper.reshape(text))
    except ImportError:
        return text


def _download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "python-urllib"})
    with urllib.request.urlopen(request, timeout=_FONT_FETCH_TIMEOUT_S) as response:
        return response.read()


def _cache_font(data, suffix):
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
    return handle.name


def resolve_font_file(payload):
    """Return a local font path for the payload, or None for a system font.

    The Google Fonts css2 endpoint serves TrueType URLs to non-browser
    user agents, which is what Pillow can read.
    """
    font_url = payload.get("font_url")
    if font_url:
        if not font_url.lower().endswith((".ttf", ".otf")):
            raise SystemExit(
                "the fallback engine reads only .ttf/.otf font_url files; "
                "use a browser engine for woff/woff2"
            )
        return _cache_font(_download(font_url), Path(font_url).suffix)
    try:
        css_url = google_fonts_url(
            payload["font_family"], payload["font_weight"], payload["font_style"]
        )
        css = _download(css_url).decode("utf-8")
        match = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+\.ttf)\)", css)
        if match:
            return _cache_font(_download(match.group(1)), ".ttf")
        detail = "no TrueType URL in the css2 response"
    except OSError as error:
        detail = error
    print(
        f"warning: could not fetch Google Font {payload['font_family']!r} "
        f"({detail}); falling back to a system font",
        file=sys.stderr,
    )
    return None


def _load_font(font_path, size, is_arabic=False):
    from PIL import ImageFont

    if is_arabic and not font_path:
        candidates = list(_ARABIC_FONT_CANDIDATES)
    elif is_arabic and font_path and not _has_raqm():
        # Without libraqm, arabic_reshaper emits U+FE70..U+FEFF presentation
        # forms that Google Fonts .ttf subsets omit; try system Arabic fonts first.
        candidates = list(_ARABIC_FONT_CANDIDATES) + [font_path]
    else:
        candidates = [font_path] if font_path else list(_SYSTEM_FONT_CANDIDATES)
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            if font_path and candidate == font_path:
                raise SystemExit(f"cannot load font {font_path!r}")
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _line_width(draw, line, font, letter_spacing):
    shaped = _shape_arabic_if_needed(line, font=font)
    width = draw.textlength(shaped, font=font)
    if letter_spacing and len(shaped) > 1 and not _ARABIC_RE.search(line):
        width += letter_spacing * (len(shaped) - 1)
    return width


def _wrap(draw, text, font, max_width, letter_spacing):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            trial = f"{current} {word}".strip()
            if _line_width(draw, trial, font, letter_spacing) <= max_width:
                current = trial
                continue
            if current:
                lines.append(current)
            # A word wider than the box breaks across lines, matching the
            # browser engine's overflow-wrap:break-word.
            current = word
            while _line_width(draw, current, font, letter_spacing) > max_width and len(current) > 1:
                head = current
                while len(head) > 1 and _line_width(draw, head, font, letter_spacing) > max_width:
                    head = head[:-1]
                lines.append(head)
                current = current[len(head):]
        lines.append(current)
    return lines


def _draw_line(draw, x, y, line, font, color, letter_spacing):
    shaped = _shape_arabic_if_needed(line, font=font)
    if not letter_spacing or _ARABIC_RE.search(line):
        draw.text((x, y), shaped, font=font, fill=color)
        return
    for char in shaped:
        draw.text((x, y), char, font=font, fill=color)
        x += draw.textlength(char, font=font) + letter_spacing


def _layout(draw, payload, text, size, font_path):
    font = _load_font(font_path, size, is_arabic=bool(_ARABIC_RE.search(text)))
    lines = _wrap(draw, text, font, payload["bbox"][0]["w"], payload["letter_spacing"])
    line_height = round(size * payload["line_height"])
    return font, lines, line_height


def _shrink_size(draw, payload, text, font_path):
    """Binary-search the largest size in [MIN_SHRINK_SIZE, size] that fits."""
    box = payload["bbox"][0]

    def height_at(size):
        # Some fonts cannot be measured at tiny sizes (Pillow raises
        # OSError); treat those sizes as not fitting.
        try:
            _, lines, line_height = _layout(draw, payload, text, size, font_path)
        except OSError:
            return None
        return line_height * len(lines)

    lo, hi = MIN_SHRINK_SIZE, payload["size"]
    floor = None
    for size in range(lo, hi + 1):
        floor = height_at(size)
        if floor is not None:
            lo = size
            break
    if floor is None or floor > box["h"]:
        raise SystemExit(
            f"text cannot fit in bbox ({box['w']}x{box['h']}) even at size {lo}"
        )
    while lo < hi:
        mid = (lo + hi + 1) // 2
        height = height_at(mid)
        if height is not None and height <= box["h"]:
            lo = mid
        else:
            hi = mid - 1
    return lo


def render_text_payload(payload, rendered_text):
    """Render a validated text-layer payload to a transparent RGBA image."""
    from PIL import Image, ImageDraw

    canvas = Image.new(
        "RGBA", (payload["canvas_width"], payload["canvas_height"]), (0, 0, 0, 0)
    )
    draw = ImageDraw.Draw(canvas)
    font_path = resolve_font_file(payload)
    box = payload["bbox"][0]

    size = payload["size"]
    if payload["overflow"] == "shrink":
        size = _shrink_size(draw, payload, rendered_text, font_path)
    font, lines, line_height = _layout(draw, payload, rendered_text, size, font_path)

    clip = payload["overflow"] == "clip"
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0)) if clip else canvas
    layer_draw = ImageDraw.Draw(layer)
    y = box["y"]
    for line in lines:
        width = _line_width(layer_draw, line, font, payload["letter_spacing"])
        if payload["align"] == "center":
            x = box["x"] + (box["w"] - width) / 2
        elif payload["align"] == "right":
            x = box["x"] + box["w"] - width
        else:
            x = box["x"]
        _draw_line(layer_draw, x, y, line, font, payload["color"], payload["letter_spacing"])
        y += line_height
    if clip:
        region = (box["x"], box["y"], box["x"] + box["w"], box["y"] + box["h"])
        canvas.paste(layer.crop(region), region)
    return canvas
