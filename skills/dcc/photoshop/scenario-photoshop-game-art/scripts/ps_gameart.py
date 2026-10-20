"""
ps_gameart: the Photoshop side of game art built with Scenario images. Seamless textures (a
wrap-around offset, the seam cross to inpaint, a seam and patch check, a tiled preview), texture
export (power-of-two sizes, color or data maps, packed channels), 9-slice UI frames (guides and a
stretch check), and selections from a 3D render's ID pass for paintover. Textures, sprites and
style passes are Scenario MCP steps the agent takes between these calls.

Library:
  import ps_gameart as GA
  GA.tile_check(layer=None, blur=0, grid=4)
      # read only. Seams: the mean step across the tile's left/right edge (seam_x) and top/bottom
      # edge (seam_y), measured after a half offset with wrap-around, each divided by the mean
      # step between any other neighbors (ratio_x, ratio_y; about 1 = invisible). blur (px)
      # quiets grain first. Patches: the range of cell means (patch_range, 0-255) on a grid x
      # grid split of a wrap-blurred copy (a 16th of the long side), the low-frequency blotches
      # that read as a pattern once the tile repeats. seam_ok and patch_ok against SEAM_RATIO
      # and PATCH_RANGE; also size and pow2.
  GA.offset(layer=None, dx=None, dy=None)
      # a copy of the layer (or of the visible image) shifted with wrap-around, half the canvas
      # by default, so the tile's edges cross in the middle. One History state. Offset the
      # repaired copy again by the same amount to put the edges back.
  GA.seam_band(width=64, dx=None, dy=None)
      # selects the cross where the edges meet after offset, `width` px wide on each seam, for
      # ps_generative.capture. One History state.
  GA.tile_preview(out, n=3, max_px=1600, layer=None)
      # an n x n repeat of the tile as a PNG, as the engine will tile it. Read only.
  GA.export_texture(out, size=None, fmt="png", resample="bicubic-auto", data=False, gray=False,
                    bits=8, layer=None)
      # a flattened copy at `size` ([w, h], or one int for a square). Color maps convert to
      # sRGB. Data maps (data=True: normal, roughness, masks) keep their values: no profile
      # conversion. gray=True writes one channel. fmt png, tga, tif. Returns {"path", "size",
      # "pow2"}.
  GA.pack_channels(out, r, g, b, a=None, size=None, fmt=None, resample="bicubic-auto")
      # one texture whose channels hold gray maps. Each source is a layer name (its luminance),
      # a number 0-255 (a constant), or None (black). With an alpha source the 4th channel is
      # written and fmt defaults to tga. Values are kept, never color-converted. Returns
      # {"path", "size", "pow2"}.
  GA.nine_slice(left, top, right, bottom)
      # guides on the four slice lines (insets in px from each edge). One History state.
  GA.nine_slice_check(left, top, right, bottom, layer=None, tol=1.0)
      # read only. Detail in a part that stretches smears: the mean step between neighbors
      # along x in the top and bottom edges, along y in the left and right edges, both in the
      # center (worst channel). ok when every part is under tol. A smooth gradient passes, since
      # it scales cleanly; a tiled draw mode repeats the part instead, so judge that with
      # tile_check on the part.
  GA.id_select(layer, rgb, fuzz=20)
      # selects one flat color of an ID pass layer (a render's object or material ID) in the
      # active document, to scope a paintover or a generative edit to one object. One History
      # state. Returns {"bounds", "share", "partial"} or {"bounds": None} when nothing matched.
  GA.pow2(n), GA.next_pow2(n)
Shell:
  python3 ps_gameart.py check [LAYER] | offset [LAYER] | band [WIDTH] | preview OUT [--n N]
      | export OUT [--size N] [--fmt F] [--data] [--gray] | pack OUT R G B [A] [--size N]
      | slice L T R B | slice-check L T R B | id LAYER R,G,B [--fuzz N]
  Pack sources on the shell: a layer name, a number, or "-" for black.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scenario-photoshop-expert", "scripts"))
import ps_run  # noqa: E402

# Authoring-time thresholds; see the live suite for the images they were measured on.
SEAM_RATIO = 1.5
PATCH_RANGE = 12.0

RESAMPLE = {"nearest": "NEARESTNEIGHBOR", "bilinear": "BILINEAR", "bicubic": "BICUBIC",
            "bicubic-auto": "BICUBICAUTOMATIC", "bicubic-sharper": "BICUBICSHARPER",
            "bicubic-smoother": "BICUBICSMOOTHER"}

HELPERS_JS = r"""
var ARGS = %ARGS%;
if (app.documents.length === 0) throw new Error("no document open");
function ga_c(s) { return charIDToTypeID(s); }
function ga_s(s) { return stringIDToTypeID(s); }
function ga_find(c, key) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if (l.name === key) return l;
    if (l.typename === "LayerSet") { var r = ga_find(l, key); if (r) return r; }
  }
  return null;
}
function ga_has(c, t) {
  for (var i = 0; i < c.layers.length; i++) {
    if (c.layers[i] === t) return true;
    if (c.layers[i].typename === "LayerSet" && ga_has(c.layers[i], t)) return true;
  }
  return false;
}
function ga_solo(c, t) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if (l === t) l.visible = true;
    else if (l.typename === "LayerSet" && ga_has(l, t)) { l.visible = true; ga_solo(l, t); }
    else l.visible = false;
  }
}
// A flattened copy of the visible image, or of one layer alone. Same profile as the source.
function ga_flat(src, key, name, bits) {
  app.activeDocument = src;
  var d;
  if (key === null || key === undefined) d = psr_dup(src, name, true);
  else {
    d = psr_dup(src, name, false);
    app.activeDocument = d;
    var L = ga_find(d, key);
    if (!L) throw new Error("layer not found: " + key);
    ga_solo(d, L);
  }
  app.activeDocument = d;
  d.flatten();
  if (bits === 16) d.bitsPerChannel = BitsPerChannelType.SIXTEEN;
  else if (d.bitsPerChannel !== BitsPerChannelType.EIGHT) d.bitsPerChannel = BitsPerChannelType.EIGHT;
  return d;
}
function ga_offset(dx, dy) {
  var o = new ActionDescriptor();
  o.putInteger(ga_c("Hrzn"), dx); o.putInteger(ga_c("Vrtc"), dy);
  o.putEnumerated(ga_c("Fl  "), ga_c("FlMd"), ga_c("Wrp "));
  executeAction(ga_c("Ofst"), o, DialogModes.NO);
}
function ga_rect(d, r, type) {
  d.selection.select([[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]], type);
}
// Mean per component channel inside r (null: whole image). Histograms count selected pixels.
function ga_means(d, r) {
  app.activeDocument = d;
  d.activeChannels = d.componentChannels;
  if (r) ga_rect(d, r); else d.selection.selectAll();
  var out = [], chs = d.componentChannels;
  for (var k = 0; k < chs.length; k++) {
    var h = chs[k].histogram, m = 0, n = 0;
    for (var j = 0; j < 256; j++) { m += j * h[j]; n += h[j]; }
    out.push(n ? m / n : 0);
  }
  d.selection.deselect();
  return out;
}
function ga_max(a) { var m = a[0]; for (var i = 1; i < a.length; i++) if (a[i] > m) m = a[i]; return m; }
// A copy of d whose pixels are |p(x) - p(x - 1)| (axis "x") or |p(y) - p(y - 1)| (axis "y"),
// wrapping at the edges, so column 0 (or row 0) holds the step across the tile's seam.
function ga_steps(d, axis, name) {
  var s = psr_dup(d, name, true);
  app.activeDocument = s;
  var top = s.activeLayer.duplicate();
  s.activeLayer = top;
  if (axis === "x") ga_offset(1, 0); else ga_offset(0, 1);
  top.blendMode = BlendMode.DIFFERENCE;
  s.flatten();
  return s;
}
function ga_r(v) { return Math.round(v * 100) / 100; }
"""

CHECK_JS = r"""
var src = app.activeDocument;
var g = ga_flat(src, ARGS.layer, "ga_tile");
var W = g.width.as("px"), H = g.height.as("px");
g.changeMode(ChangeMode.GRAYSCALE);
var out = {size: [W, H]};
// Patches: blur a 3 x 3 repeat and keep the middle, so the blur wraps like the tiled texture.
var p = psr_dup(g, "ga_patch", true);
app.activeDocument = p;
var base = p.activeLayer;
base.isBackgroundLayer = false;
p.resizeCanvas(UnitValue(3 * W, "px"), UnitValue(3 * H, "px"), AnchorPosition.MIDDLECENTER);
for (var ty = -1; ty <= 1; ty++) {
  for (var tx = -1; tx <= 1; tx++) {
    if (tx === 0 && ty === 0) continue;
    base.duplicate().translate(UnitValue(tx * W, "px"), UnitValue(ty * H, "px"));
  }
}
p.flatten();
p.activeLayer.applyGaussianBlur(Math.max(W, H) / 16);
p.crop([UnitValue(W, "px"), UnitValue(H, "px"), UnitValue(2 * W, "px"), UnitValue(2 * H, "px")]);
var n = ARGS.grid, cells = [];
for (var y = 0; y < n; y++) {
  for (var x = 0; x < n; x++) {
    cells.push(ga_r(ga_means(p, [Math.round(x * W / n), Math.round(y * H / n),
                                 Math.round((x + 1) * W / n), Math.round((y + 1) * H / n)])[0]));
  }
}
psr_close(p);
out.cells = cells;
// Seams: offset by half with wrap-around first, as an artist does, so the edges meet in the
// middle and any blur crosses them. A blur clamped at the canvas edge invents a step there.
var cx = Math.round(W / 2), cy = Math.round(H / 2);
app.activeDocument = g;
ga_offset(cx, cy);
if (ARGS.blur > 0) g.activeLayer.applyGaussianBlur(ARGS.blur);
var sx = ga_steps(g, "x", "ga_step_x");
var seam = ga_means(sx, [cx, 0, cx + 1, H])[0], all = ga_means(sx, null)[0];
out.seam_x = ga_r(seam); out.base_x = ga_r((all * W - seam) / (W - 1));
psr_close(sx);
var sy = ga_steps(g, "y", "ga_step_y");
seam = ga_means(sy, [0, cy, W, cy + 1])[0]; all = ga_means(sy, null)[0];
out.seam_y = ga_r(seam); out.base_y = ga_r((all * H - seam) / (H - 1));
psr_close(sy);
psr_close(g);
return out;
"""

OFFSET_JS = r"""
var d = app.activeDocument;
var W = d.width.as("px"), H = d.height.as("px");
var dx = ARGS.dx, dy = ARGS.dy;
if (dx === null) dx = Math.round(W / 2);
if (dy === null) dy = Math.round(H / 2);
var L, name;
if (ARGS.layer === null) {
  var t = psr_dup(d, "ga_stamp", true);
  app.activeDocument = t;
  L = t.activeLayer.duplicate(d, ElementPlacement.PLACEATBEGINNING);
  psr_close(t);
  app.activeDocument = d;
  name = "Tile";
} else {
  var S = ga_find(d, ARGS.layer);
  if (!S) throw new Error("layer not found: " + ARGS.layer);
  L = S.duplicate(S, ElementPlacement.PLACEBEFORE);
  d.activeLayer = L;
  try { L.rasterize(RasterizeType.ENTIRELAYER); } catch (e) {}
  name = S.name;
}
d.activeLayer = L;
L.name = name + ", offset";
ga_offset(dx, dy);
return {layer: L.name, id: L.id, dx: dx, dy: dy};
"""

BAND_JS = r"""
var d = app.activeDocument;
var W = d.width.as("px"), H = d.height.as("px");
var dx = ARGS.dx, dy = ARGS.dy, w = ARGS.width / 2;
if (dx === null) dx = Math.round(W / 2);
if (dy === null) dy = Math.round(H / 2);
ga_rect(d, [Math.max(0, dx - w), 0, Math.min(W, dx + w), H]);
ga_rect(d, [0, Math.max(0, dy - w), W, Math.min(H, dy + w)], SelectionType.EXTEND);
return {dx: dx, dy: dy, width: ARGS.width, size: [W, H]};
"""

PREVIEW_JS = r"""
var src = app.activeDocument;
var t = ga_flat(src, ARGS.layer, "ga_tile_preview");
var n = ARGS.n, W = t.width.as("px"), H = t.height.as("px");
// Tile at full size up to 8192 px, so the seams are the file's own, then shrink the whole.
var k = Math.min(1, 8192 / (n * Math.max(W, H)));
if (k < 1) {
  t.resizeImage(UnitValue(Math.round(W * k), "px"), UnitValue(Math.round(H * k), "px"), null,
                ResampleMethod.BICUBIC);
  W = t.width.as("px"); H = t.height.as("px");
}
var base = t.activeLayer;
base.isBackgroundLayer = false;
t.resizeCanvas(UnitValue(W * n, "px"), UnitValue(H * n, "px"), AnchorPosition.TOPLEFT);
for (var y = 0; y < n; y++) {
  for (var x = 0; x < n; x++) {
    if (x === 0 && y === 0) continue;
    var c = base.duplicate();
    c.translate(UnitValue(x * W, "px"), UnitValue(y * H, "px"));
  }
}
t.flatten();
var s = Math.min(1, ARGS.max_px / Math.max(W * n, H * n));
if (s < 1) t.resizeImage(UnitValue(Math.round(W * n * s), "px"), UnitValue(Math.round(H * n * s), "px"),
                         null, ResampleMethod.BICUBIC);
try { t.convertProfile("sRGB IEC61966-2.1", Intent.RELATIVECOLORIMETRIC, true, false); } catch (e) {}
var p = psr_export(t, ARGS.out, "png");
var size = [t.width.as("px"), t.height.as("px")];
psr_close(t);
return {path: p, size: size, n: n};
"""

EXPORT_JS = r"""
var src = app.activeDocument;
var t = ga_flat(src, ARGS.layer, "ga_texture", ARGS.bits);
if (ARGS.data) t.colorProfileType = ColorProfile.NONE;
else {
  try { t.convertProfile("sRGB IEC61966-2.1", Intent.RELATIVECOLORIMETRIC, true, false); } catch (e) {}
}
if (ARGS.size) t.resizeImage(UnitValue(ARGS.size[0], "px"), UnitValue(ARGS.size[1], "px"), null,
                             ResampleMethod[ARGS.resample]);
var size = [t.width.as("px"), t.height.as("px")];
var out = t;
if (ARGS.gray) {
  // Split Channels copies the red channel's values as they are; a mode change to Grayscale
  // would run them through the working gray profile.
  t.activeLayer.desaturate();
  var before = {};
  for (var i = 0; i < app.documents.length; i++) before[app.documents[i].id] = true;
  executeAction(ga_c("SplC"), new ActionDescriptor(), DialogModes.NO);
  var made = [];
  for (var j = 0; j < app.documents.length; j++) {
    if (!before[app.documents[j].id]) { made.push(app.documents[j]); __psr_created.push(app.documents[j].id); }
  }
  if (made.length === 0) throw new Error("Split Channels made no documents");
  out = made[0];
  for (var m = 1; m < made.length; m++) psr_close(made[m]);
  out.colorProfileType = ColorProfile.NONE;
}
var p = psr_export(out, ARGS.out, ARGS.fmt);
psr_close(out);
return {path: p, size: size};
"""

PACK_JS = r"""
var src = app.activeDocument;
var p = ga_flat(src, null, "ga_pack");
if (p.mode !== DocumentMode.RGB) p.changeMode(ChangeMode.RGB);
var W = p.width.as("px"), H = p.height.as("px");
var black = new SolidColor(); black.rgb.red = 0; black.rgb.green = 0; black.rgb.blue = 0;
p.selection.selectAll(); p.selection.fill(black); p.selection.deselect();
function gray(v) { var k = new SolidColor(); k.rgb.red = v; k.rgb.green = v; k.rgb.blue = v; return k; }
// A full-canvas layer in p holding the source's luminance, or a constant.
function source_layer(v) {
  var L;
  if (typeof v === "number") {
    app.activeDocument = p;
    L = p.artLayers.add();
    p.selection.selectAll(); p.selection.fill(gray(v)); p.selection.deselect();
    return L;
  }
  var t = ga_flat(src, v, "ga_pack_src");
  t.activeLayer.desaturate();
  L = t.activeLayer.duplicate(p, ElementPlacement.PLACEATBEGINNING);
  psr_close(t);
  app.activeDocument = p;
  return L;
}
var keys = {r: "Rd  ", g: "Grn ", b: "Bl  "}, order = ["r", "g", "b"];
for (var i = 0; i < 3; i++) {
  var v = ARGS[order[i]];
  if (v === null) continue;
  var L = source_layer(v);
  p.activeLayer = L;
  // Advanced Blending: the layer writes one channel only.
  var desc = new ActionDescriptor(), ref = new ActionReference();
  ref.putEnumerated(ga_c("Lyr "), ga_c("Ordn"), ga_c("Trgt"));
  desc.putReference(ga_c("null"), ref);
  var lyr = new ActionDescriptor(), list = new ActionList();
  list.putEnumerated(ga_c("Chnl"), ga_c(keys[order[i]]));
  lyr.putList(ga_s("channelRestrictions"), list);
  desc.putObject(ga_c("T   "), ga_c("Lyr "), lyr);
  executeAction(ga_c("setd"), desc, DialogModes.NO);
}
p.flatten();
if (ARGS.a !== null) {
  var A = source_layer(ARGS.a);
  // The alpha source's luminance, copied over as a channel. Loading it as a selection instead
  // fails ("Set is not currently available") when no pixel is above 50%, a constant 128 included.
  var t2 = psr_dup(p, "ga_pack_a", false);
  app.activeDocument = t2;
  ga_solo(t2, t2.layers[0]);
  t2.flatten();
  var ac = t2.channels[0].duplicate(p);
  psr_close(t2);
  app.activeDocument = p;
  A.remove();
  ac.name = "Alpha 1";
  p.activeChannels = p.componentChannels;
}
if (ARGS.size) p.resizeImage(UnitValue(ARGS.size[0], "px"), UnitValue(ARGS.size[1], "px"), null,
                             ResampleMethod[ARGS.resample]);
p.colorProfileType = ColorProfile.NONE;
var size = [p.width.as("px"), p.height.as("px")];
var path = psr_export(p, ARGS.out, ARGS.fmt, {alpha: ARGS.a !== null});
psr_close(p);
return {path: path, size: size};
"""

SLICE_JS = r"""
var d = app.activeDocument;
var W = d.width.as("px"), H = d.height.as("px");
d.guides.add(Direction.VERTICAL, UnitValue(ARGS.left, "px"));
d.guides.add(Direction.VERTICAL, UnitValue(W - ARGS.right, "px"));
d.guides.add(Direction.HORIZONTAL, UnitValue(ARGS.top, "px"));
d.guides.add(Direction.HORIZONTAL, UnitValue(H - ARGS.bottom, "px"));
return {x: [ARGS.left, W - ARGS.right], y: [ARGS.top, H - ARGS.bottom], size: [W, H]};
"""

SLICE_CHECK_JS = r"""
var src = app.activeDocument;
var t = ga_flat(src, ARGS.layer, "ga_slice");
var W = t.width.as("px"), H = t.height.as("px");
var l = ARGS.left, tp = ARGS.top, x2 = W - ARGS.right, y2 = H - ARGS.bottom;
if (l >= x2 || tp >= y2) throw new Error("the slice lines cross: no stretchable middle left");
var sx = ga_steps(t, "x", "ga_slice_x"), sy = ga_steps(t, "y", "ga_slice_y");
// A step along x at column x compares x with x - 1, so each band starts one past its line.
function part(s, r) { if (r[0] >= r[2] || r[1] >= r[3]) return null; return ga_r(ga_max(ga_means(s, r))); }
var out = {
  top: part(sx, [l + 1, 0, x2, tp]),
  bottom: part(sx, [l + 1, y2, x2, H]),
  left: part(sy, [0, tp + 1, l, y2]),
  right: part(sy, [x2, tp + 1, W, y2]),
  center_x: part(sx, [l + 1, tp, x2, y2]),
  center_y: part(sy, [l, tp + 1, x2, y2]),
  size: [W, H]
};
psr_close(sx); psr_close(sy); psr_close(t);
return out;
"""

ID_JS = r"""
var d = app.activeDocument;
var t = ga_flat(d, ARGS.layer, "ga_id");
var W = t.width.as("px"), H = t.height.as("px");
var k = new SolidColor(); k.rgb.red = ARGS.rgb[0]; k.rgb.green = ARGS.rgb[1]; k.rgb.blue = ARGS.rgb[2];
function lab(c) {
  var x = new ActionDescriptor();
  x.putDouble(ga_c("Lmnc"), c.lab.l); x.putDouble(ga_c("A   "), c.lab.a); x.putDouble(ga_c("B   "), c.lab.b);
  return x;
}
var cr = new ActionDescriptor();
cr.putInteger(ga_c("Fzns"), ARGS.fuzz);
cr.putObject(ga_c("Mnm "), ga_c("LbCl"), lab(k));
cr.putObject(ga_c("Mxm "), ga_c("LbCl"), lab(k));
cr.putInteger(ga_s("colorModel"), 0);
var any = true;
try { executeAction(ga_c("ClrR"), cr, DialogModes.NO); } catch (e) { any = false; }
var out = {bounds: null, share: 0, partial: 0};
if (any) {
  try { t.selection.bounds; } catch (e2) { any = false; }
}
if (any) {
  var ch = t.channels.add(); ch.name = "ga_id_sel";
  t.selection.store(ch);
  t.selection.deselect();
  t.activeChannels = [ch];
  var h = ch.histogram, sum = 0, part = 0;
  t.activeChannels = t.componentChannels;
  for (var i = 0; i < 256; i++) { sum += i * h[i]; if (i > 0 && i < 255) part += h[i]; }
  out.share = ga_r(100 * sum / 255 / (W * H));
  out.partial = ga_r(100 * part / (W * H));
  app.activeDocument = d;
  var r = new ActionReference(); r.putProperty(ga_c("Chnl"), ga_c("fsel"));
  var ld = new ActionDescriptor(); ld.putReference(ga_c("null"), r);
  var s = new ActionReference(); s.putName(ga_c("Chnl"), "ga_id_sel"); s.putName(ga_c("Dcmn"), t.name);
  ld.putReference(ga_c("T   "), s);
  executeAction(ga_c("setd"), ld, DialogModes.NO);
  var b = d.selection.bounds;
  out.bounds = [b[0].as("px"), b[1].as("px"), b[2].as("px"), b[3].as("px")];
}
psr_close(t);
app.activeDocument = d;
return out;
"""


def _run(js, args, undo=None, timeout=300):
    body = HELPERS_JS.replace("%ARGS%", json.dumps(args)) + js
    res = ps_run.run(body, undo=undo, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError("%s (line %s)" % (res.get("error"), res.get("line")))
    return res["result"]


def pow2(n):
    n = int(n)
    return n > 0 and n & (n - 1) == 0


def next_pow2(n):
    n = int(n)
    if n < 1:
        raise ValueError("size must be positive, got %d" % n)
    p = 1
    while p < n:
        p *= 2
    return p


def _size(size):
    if size is None:
        return None
    if isinstance(size, int):
        size = [size, size]
    size = [int(size[0]), int(size[1])]
    if size[0] < 1 or size[1] < 1:
        raise ValueError("size must be positive, got %r" % (size,))
    return size


def _resample(name):
    if name not in RESAMPLE:
        raise ValueError("unknown resample %r; known: %s" % (name, ", ".join(sorted(RESAMPLE))))
    return RESAMPLE[name]


def _out(path):
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def tile_check(layer=None, blur=0, grid=4):
    r = _run(CHECK_JS, {"layer": layer, "blur": blur, "grid": int(grid)})
    r["ratio_x"] = round(r["seam_x"] / max(r["base_x"], 0.5), 2)
    r["ratio_y"] = round(r["seam_y"] / max(r["base_y"], 0.5), 2)
    r["patch_range"] = round(max(r["cells"]) - min(r["cells"]), 2)
    r["seam_ok"] = r["ratio_x"] < SEAM_RATIO and r["ratio_y"] < SEAM_RATIO
    r["patch_ok"] = r["patch_range"] < PATCH_RANGE
    r["pow2"] = pow2(r["size"][0]) and pow2(r["size"][1])
    return r


def offset(layer=None, dx=None, dy=None, undo="Scenario: Offset tile"):
    return _run(OFFSET_JS, {"layer": layer, "dx": dx, "dy": dy}, undo=undo)


def seam_band(width=64, dx=None, dy=None, undo="Scenario: Select tile seams"):
    if width < 2:
        raise ValueError("width must be at least 2 px")
    return _run(BAND_JS, {"width": int(width), "dx": dx, "dy": dy}, undo=undo)


def tile_preview(out, n=3, max_px=1600, layer=None):
    if n < 2:
        raise ValueError("n must be at least 2 to show the seams")
    return _run(PREVIEW_JS, {"out": _out(out), "n": int(n), "max_px": int(max_px), "layer": layer})


def export_texture(out, size=None, fmt="png", resample="bicubic-auto", data=False, gray=False,
                   bits=8, layer=None):
    if fmt not in ("png", "tga", "tif"):
        raise ValueError("fmt must be png, tga or tif")
    if bits not in (8, 16) or (bits == 16 and fmt == "tga"):
        raise ValueError("bits must be 8, or 16 for png and tif")
    size = _size(size)
    r = _run(EXPORT_JS, {"out": _out(out), "size": size, "fmt": fmt, "resample": _resample(resample),
                         "data": bool(data), "gray": bool(gray), "bits": bits, "layer": layer})
    r["pow2"] = pow2(r["size"][0]) and pow2(r["size"][1])
    return r


def _source(v):
    if v is None or isinstance(v, str):
        return v
    if isinstance(v, (int, float)) and 0 <= v <= 255:
        return int(round(v))
    raise ValueError("a pack source is a layer name, a number 0-255 or None, got %r" % (v,))


def pack_channels(out, r, g, b, a=None, size=None, fmt=None, resample="bicubic-auto"):
    if fmt is None:
        fmt = "tga" if a is not None else "png"
    if a is not None and fmt == "png":
        raise ValueError("PNG keeps no alpha channel: use tga or tif for a 4-channel pack")
    if fmt not in ("png", "tga", "tif"):
        raise ValueError("fmt must be png, tga or tif")
    res = _run(PACK_JS, {"out": _out(out), "r": _source(r), "g": _source(g), "b": _source(b),
                         "a": _source(a), "size": _size(size), "fmt": fmt,
                         "resample": _resample(resample)})
    res["pow2"] = pow2(res["size"][0]) and pow2(res["size"][1])
    return res


def _insets(left, top, right, bottom):
    vals = [int(left), int(top), int(right), int(bottom)]
    if min(vals) < 1:
        raise ValueError("slice insets must be at least 1 px, got %r" % (vals,))
    return vals


def nine_slice(left, top, right, bottom, undo="Scenario: 9-slice guides"):
    left, top, right, bottom = _insets(left, top, right, bottom)
    return _run(SLICE_JS, {"left": left, "top": top, "right": right, "bottom": bottom}, undo=undo)


def nine_slice_check(left, top, right, bottom, layer=None, tol=1.0):
    left, top, right, bottom = _insets(left, top, right, bottom)
    r = _run(SLICE_CHECK_JS, {"left": left, "top": top, "right": right, "bottom": bottom,
                              "layer": layer})
    parts = ("top", "bottom", "left", "right", "center_x", "center_y")
    r["over"] = [p for p in parts if r[p] is not None and r[p] >= tol]
    r["ok"] = not r["over"]
    return r


def id_select(layer, rgb, fuzz=20, undo="Scenario: Select ID color"):
    rgb = [int(c) for c in rgb]
    if len(rgb) != 3 or min(rgb) < 0 or max(rgb) > 255:
        raise ValueError("rgb must be three values 0-255, got %r" % (rgb,))
    if not 0 <= fuzz <= 200:
        raise ValueError("fuzz must be 0-200 (Color Range fuzziness)")
    return _run(ID_JS, {"layer": layer, "rgb": rgb, "fuzz": int(fuzz)}, undo=undo)


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        i = argv.index(flag)
        v = cast(argv[i + 1])
        del argv[i:i + 2]
        return v
    return default


def _pack_arg(v):
    if v == "-":
        return None
    try:
        return int(v)
    except ValueError:
        return v


def main(argv):
    argv = list(argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd = argv.pop(0)
    if cmd == "check":
        r = tile_check(argv[0] if argv else None)
    elif cmd == "offset":
        r = offset(argv[0] if argv else None)
    elif cmd == "band":
        r = seam_band(int(argv[0]) if argv else 64)
    elif cmd == "preview":
        n = _opt(argv, "--n", int, 3)
        r = tile_preview(argv[0], n=n)
    elif cmd == "export":
        size = _opt(argv, "--size", int)
        fmt = _opt(argv, "--fmt", str, "png")
        data, gray = "--data" in argv, "--gray" in argv
        argv = [a for a in argv if a not in ("--data", "--gray")]
        r = export_texture(argv[0], size=size, fmt=fmt, data=data, gray=gray)
    elif cmd == "pack":
        size = _opt(argv, "--size", int)
        srcs = [_pack_arg(v) for v in argv[1:5]]
        while len(srcs) < 4:
            srcs.append(None)
        r = pack_channels(argv[0], srcs[0], srcs[1], srcs[2], srcs[3], size=size)
    elif cmd == "slice":
        r = nine_slice(*[int(v) for v in argv[:4]])
    elif cmd == "slice-check":
        r = nine_slice_check(*[int(v) for v in argv[:4]])
    elif cmd == "id":
        fuzz = _opt(argv, "--fuzz", int, 20)
        r = id_select(argv[0], [int(c) for c in argv[1].split(",")], fuzz=fuzz)
    else:
        print(__doc__)
        return 2
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
