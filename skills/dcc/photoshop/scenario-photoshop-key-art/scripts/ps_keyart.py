"""
ps_keyart: the Photoshop side of key art, ads and thumbnails built around Scenario images. A
canvas per channel with its unsafe zones as guides, live type laid out from a copy sheet and
shrunk to fit its box, checks that read what a viewer will see (text inside the canvas and out of
unsafe zones, text size at the size people see it), and an export under a byte cap. The plates
and subjects are Scenario MCP steps the agent takes between these calls.

Library:
  import ps_keyart as K
  K.PRESETS["youtube-thumbnail"]
      # {"size": [w, h], "max_bytes", "unsafe": [[l, t, r, b], ...], "display": px wide as
      # most viewers see it}. Sizes are the channels' published specs at authoring time
      # (2026-10); check the channel before a campaign.
  K.new_canvas(preset, name=None)
      # a new RGB 8-bit sRGB document at the preset size, unsafe zones drawn as guides.
  K.cover_bounds(src_w, src_h, w, h, focus=(0.5, 0.5))
      # [l, t, r, b] that covers a w x h canvas with a src_w x src_h image, aspect kept,
      # the focus point (fractions of the source) as close to the center as the crop allows.
      # Pass it to ps_io.place.
  K.type_layers(copy, fit=True)
      # copy = [{"name", "text", "box": [l, t, r, b], "font": PostScript name ("Arial-BoldMT"),
      #   "size": max pt, "color": "#RRGGBB", "align": "left"|"center"|"right",
      #   "valign": "top"|"middle"|"bottom"}]; "\n" breaks lines. Live point text, shrunk until
      #   it fits its box, then aligned in it. One History state. Per layer: size, bounds,
      #   fits, font_used (Photoshop keeps its default when a font is missing).
  K.check(preset=None, unsafe=None, display=None, min_px=12)
      # every visible text layer: inside the canvas, clear of unsafe zones, and its font size
      # in px once the canvas shows at `display` px wide ("small": under min_px).
  K.export_under(out, max_bytes, fmt="jpg", size=None, min_quality=0)
      # a flattened sRGB 8-bit copy, resized to size [w, h] when given, saved at the highest
      # JPEG quality (12 down to min_quality) under max_bytes. Returns {"path", "bytes",
      # "quality", "fits"}.
Shell:
  python3 ps_keyart.py presets | canvas PRESET | check [PRESET] | export OUT MAX_BYTES [--size W,H]
      | type COPY.json
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scenario-photoshop-expert", "scripts"))
import ps_run  # noqa: E402

# Published channel specs at authoring time (2026-10). Unsafe zones are where the channel's own
# interface covers the image: the duration badge on a YouTube thumbnail, the profile and reply
# bars on a story. "display" is a common on-screen width, for the legibility check.
PRESETS = {
    "youtube-thumbnail": {"size": [1280, 720], "max_bytes": 2000000,
                          "unsafe": [[1080, 620, 1280, 720]], "display": 360},
    "instagram-portrait": {"size": [1080, 1350], "unsafe": [], "display": 390},
    "instagram-story": {"size": [1080, 1920], "unsafe": [[0, 0, 1080, 250], [0, 1580, 1080, 1920]],
                        "display": 390},
    "x-post": {"size": [1600, 900], "unsafe": [], "display": 500},
    "linkedin-post": {"size": [1200, 627], "unsafe": [], "display": 550},
    "steam-header": {"size": [920, 430], "unsafe": [], "display": 460},
    "steam-small": {"size": [462, 174], "unsafe": [], "display": 231},
    "steam-main": {"size": [1232, 706], "unsafe": [], "display": 616},
    "steam-vertical": {"size": [748, 896], "unsafe": [], "display": 374},
    "steam-library-capsule": {"size": [600, 900], "unsafe": [], "display": 300},
    "steam-library-hero": {"size": [3840, 1240], "unsafe": [], "display": 1920, "no_text": True},
}

HELPERS_JS = r"""
var ARGS = %ARGS%;
if (app.documents.length === 0 && !ARGS.allow_no_doc) throw new Error("no document open");
function pk_box(L) { var b = L.bounds; return [b[0].as("px"), b[1].as("px"), b[2].as("px"), b[3].as("px")]; }
function pk_hits(a, b) { return a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3]; }
// Action Manager layerKind (3 = text): the DOM's layer.kind throws "Internal error" on a
// Clarity adjustment layer (27.11).
function pk_is_text(l) {
  if (l.typename !== "ArtLayer") return false;
  try {
    var r = new ActionReference(); r.putIdentifier(charIDToTypeID("Lyr "), l.id);
    return executeActionGet(r).getInteger(stringIDToTypeID("layerKind")) === 3;
  } catch (e) { return false; }
}
function pk_texts(c, out) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if (!l.visible) continue;
    if (l.typename === "LayerSet") pk_texts(l, out);
    else if (pk_is_text(l)) out.push(l);
  }
  return out;
}
"""

CANVAS_JS = r"""
var d = app.documents.add(UnitValue(ARGS.size[0], "px"), UnitValue(ARGS.size[1], "px"), 72, ARGS.name,
                          NewDocumentMode.RGB, DocumentFill.WHITE, 1, BitsPerChannelType.EIGHT);
try { d.convertProfile("sRGB IEC61966-2.1", Intent.RELATIVECOLORIMETRIC, true, false); } catch (e) {}
for (var i = 0; i < ARGS.unsafe.length; i++) {
  var z = ARGS.unsafe[i];
  if (z[0] > 0) d.guides.add(Direction.VERTICAL, UnitValue(z[0], "px"));
  if (z[2] < ARGS.size[0]) d.guides.add(Direction.VERTICAL, UnitValue(z[2], "px"));
  if (z[1] > 0) d.guides.add(Direction.HORIZONTAL, UnitValue(z[1], "px"));
  if (z[3] < ARGS.size[1]) d.guides.add(Direction.HORIZONTAL, UnitValue(z[3], "px"));
}
return {name: d.name, id: d.id, size: [d.width.as("px"), d.height.as("px")], guides: d.guides.length};
"""

# Point text, not paragraph text: a paragraph box hides overflow without an error, while point
# text bounds show exactly what renders, so the fit loop can measure it.
TYPE_JS = r"""
var d = app.activeDocument, out = [];
var just = {left: Justification.LEFT, center: Justification.CENTER, right: Justification.RIGHT};
for (var i = 0; i < ARGS.copy.length; i++) {
  var it = ARGS.copy[i], b = it.box, bw = b[2] - b[0], bh = b[3] - b[1];
  var L = d.artLayers.add();
  L.kind = LayerKind.TEXT;
  L.name = it.name;
  var t = L.textItem;
  t.contents = String(it.text).replace(/\n/g, "\r");
  t.font = it.font || "Arial-BoldMT";
  var col = new SolidColor(); col.rgb.hexValue = String(it.color || "#FFFFFF").replace("#", "");
  t.color = col;
  t.justification = just[it.align || "center"];
  var size = it.size || 120;
  t.size = size;
  t.position = [b[0], b[1] + size];
  var bx = pk_box(L), tries = 0;
  while (ARGS.fit && tries < 6) {
    var w = bx[2] - bx[0], h = bx[3] - bx[1];
    var k = Math.min(bw / w, bh / h);
    if (k >= 1) break;
    size = Math.max(4, Math.floor(size * k * 0.98 * 10) / 10);
    t.size = size;
    bx = pk_box(L);
    tries++;
  }
  var w2 = bx[2] - bx[0], h2 = bx[3] - bx[1];
  // ExtendScript groups chained ternaries from the left (a left alignment came out right),
  // so the branches are plain if/else.
  var x = b[0] + (bw - w2) / 2, y = b[1] + (bh - h2) / 2;
  if (it.align === "left") x = b[0];
  else if (it.align === "right") x = b[2] - w2;
  if (it.valign === "top") y = b[1];
  else if (it.valign === "bottom") y = b[3] - h2;
  L.translate(UnitValue(x - bx[0], "px"), UnitValue(y - bx[1], "px"));
  bx = pk_box(L);
  out.push({name: L.name, id: L.id, size: Math.round(t.size.as ? t.size.as("pt") : t.size), bounds: bx,
            font_used: t.font, font_asked: it.font || "Arial-BoldMT",
            fits: bx[0] >= b[0] - 1 && bx[1] >= b[1] - 1 && bx[2] <= b[2] + 1 && bx[3] <= b[3] + 1});
}
return out;
"""

CHECK_JS = r"""
var d = app.activeDocument, W = d.width.as("px"), H = d.height.as("px"), res = d.resolution;
var layers = pk_texts(d, []), out = [];
for (var i = 0; i < layers.length; i++) {
  var L = layers[i], bx = pk_box(L), t = L.textItem, zones = [];
  for (var z = 0; z < ARGS.unsafe.length; z++) if (pk_hits(bx, ARGS.unsafe[z])) zones.push(z);
  var pt = t.size.as ? t.size.as("pt") : t.size, px = pt * res / 72;
  var r = {name: L.name, bounds: bx, inside: bx[0] >= 0 && bx[1] >= 0 && bx[2] <= W && bx[3] <= H,
           unsafe_zones: zones, font_px: Math.round(px * 10) / 10};
  if (ARGS.display) {
    r.px_at_display = Math.round(px * ARGS.display / W * 10) / 10;
    r.small = r.px_at_display < ARGS.min_px;
  }
  out.push(r);
}
return {canvas: [W, H], texts: out};
"""

EXPORT_JS = r"""
var src = app.activeDocument, c = psr_dup(src, "pk_export", true), out = null;
try {
  app.activeDocument = c;
  try { c.flatten(); } catch (e) {}
  if (String(c.mode) !== "DocumentMode.RGB") c.changeMode(ChangeMode.RGB);
  if (String(c.bitsPerChannel) !== "BitsPerChannelType.EIGHT") c.bitsPerChannel = BitsPerChannelType.EIGHT;
  try { c.convertProfile("sRGB IEC61966-2.1", Intent.RELATIVECOLORIMETRIC, true, false); } catch (e) {}
  if (ARGS.size) c.resizeImage(UnitValue(ARGS.size[0], "px"), UnitValue(ARGS.size[1], "px"), null, ResampleMethod.BICUBIC);
  var tried = [];
  for (var q = 12; q >= ARGS.min_quality; q--) {
    var p = psr_export(c, ARGS.out, ARGS.fmt, {quality: q});
    var n = new File(p).length;
    tried.push([q, n]);
    out = {path: p, bytes: n, quality: q, fits: n <= ARGS.max_bytes, size: [c.width.as("px"), c.height.as("px")]};
    if (out.fits || ARGS.fmt === "png") break;
  }
  out.tried = tried;
} finally {
  psr_close(c);
  app.activeDocument = src;
}
return out;
"""


def _run(js, args, undo=None, timeout=300):
    body = HELPERS_JS.replace("%ARGS%", json.dumps(args)) + js
    res = ps_run.run(body, undo=undo, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError("%s (line %s)" % (res.get("error"), res.get("line")))
    return res["result"]


def _preset(preset):
    if preset is None:
        return None
    if isinstance(preset, dict):
        return preset
    if preset not in PRESETS:
        raise ValueError("unknown preset %r; known: %s" % (preset, ", ".join(sorted(PRESETS))))
    return PRESETS[preset]


def new_canvas(preset, name=None):
    p = _preset(preset)
    return _run(CANVAS_JS, {"size": p["size"], "unsafe": p.get("unsafe", []),
                            "name": name or (preset if isinstance(preset, str) else "key art"),
                            "allow_no_doc": True})


def cover_bounds(src_w, src_h, w, h, focus=(0.5, 0.5)):
    k = max(w / float(src_w), h / float(src_h))
    sw, sh = src_w * k, src_h * k
    left = min(0.0, max(w - sw, w / 2.0 - focus[0] * sw))
    top = min(0.0, max(h - sh, h / 2.0 - focus[1] * sh))
    return [round(left, 2), round(top, 2), round(left + sw, 2), round(top + sh, 2)]


def type_layers(copy, fit=True, undo="Scenario: Type layers"):
    for c in copy:
        if not all(k in c for k in ("name", "text", "box")):
            raise ValueError("each copy item needs name, text and box")
        if c.get("align", "center") not in ("left", "center", "right"):
            raise ValueError("align must be left, center or right")
    return _run(TYPE_JS, {"copy": copy, "fit": bool(fit)}, undo=undo)


def check(preset=None, unsafe=None, display=None, min_px=12):
    p = _preset(preset) or {}
    unsafe = unsafe if unsafe is not None else p.get("unsafe", [])
    display = display if display is not None else p.get("display")
    out = _run(CHECK_JS, {"unsafe": unsafe, "display": display, "min_px": float(min_px)})
    problems = []
    for t in out["texts"]:
        if not t["inside"]:
            problems.append("%s: leaves the canvas" % t["name"])
        if t["unsafe_zones"]:
            problems.append("%s: under the channel's interface (zone %s)" % (t["name"], t["unsafe_zones"]))
        if t.get("small"):
            problems.append("%s: %s px at %s px wide" % (t["name"], t["px_at_display"], display))
    if p.get("no_text") and out["texts"]:
        problems.append("this asset takes no text")
    out["problems"] = problems
    return out


def export_under(out, max_bytes, fmt="jpg", size=None, min_quality=0):
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if fmt not in ("jpg", "png"):
        raise ValueError("fmt must be jpg or png")
    return _run(EXPORT_JS, {"out": out, "max_bytes": int(max_bytes), "fmt": fmt, "size": size,
                            "min_quality": int(min_quality)})


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return cast(argv[i + 1])
    return default


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    try:
        if cmd == "presets":
            out = PRESETS
        elif cmd == "canvas":
            out = new_canvas(argv[1])
        elif cmd == "check":
            out = check(argv[1] if len(argv) > 1 and not argv[1].startswith("--") else None)
        elif cmd == "export":
            size = _opt(argv, "--size")
            out = export_under(argv[1], int(argv[2]), size=[int(v) for v in size.split(",")] if size else None)
        elif cmd == "type":
            with open(argv[1]) as f:
                out = type_layers(json.load(f))
        else:
            print("unknown command: " + cmd, file=sys.stderr)
            return 2
    except (RuntimeError, ValueError, OSError) as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    print(json.dumps({"ok": True, "result": out}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
