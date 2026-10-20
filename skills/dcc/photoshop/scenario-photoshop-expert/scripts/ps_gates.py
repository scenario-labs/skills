"""
ps_gates: measurable quality gates computed inside Photoshop from histograms of temporary copies.
Pixels, layers and the active History state stay as they were: every gate works on duplicates the
job closes, and a stored selection is stepped back out of History (at the History limit, those
temporary states drop the user's oldest undo steps). No Python packages needed.

Library (each call is one ps_run job):
  import ps_gates as G
  G.diff(a, b, region=None, size=None)
                                     # |A - B| per channel: mean, p99, max (0-255). a and b are a
                                     # layer name or id, or None for the visible composite. size
                                     # [w, h] resamples both copies first (bicubic), so a check at
                                     # a lower resolution ignores fine detail and keeps shifts
  G.stats(layer=None, region=None)   # per-channel mean and std, luminance, skin-line hue angle
  G.texture(layer=None, region=None, radius=2)
                                     # high-pass energy: std of a desaturated High Pass (128 = flat)
  G.halo(layer, band=2)              # edge rim check of a cut-out over black and over white
  G.structure(a, b, region=None, size=256)
                                     # tone-blind alignment: both copies at a `size` px long
                                     # side, desaturated, equalized, high-passed, then |A - B|
                                     # mean. Survives a colorize, a relight, a restore of a
                                     # damaged photo; a shift or a scale change raises it.
                                     # Region defaults to the copy inset by 6% per side
Regions: None (whole image), [left, top, right, bottom] in pixels, "selection" (the current
selection), "outside" (its inverse), or a layer's shape: {"alpha": layer} (its opaque pixels,
mask included), {"alpha": layer, "contract": px} (an inner core), {"alpha": layer, "ring": px,
"gap": px} (a band of that width around it, gap px away: the element's surroundings).

Reading the numbers (authoring-time thresholds, check them on your own images):
  diff:     max <= 2 means identical up to rounding; outside-mask edits should stay there.
  stats:    hue_angle is the mean color's angle on a UV vectorscope; the skin-tone line sits near
            123 degrees, so skin_line_delta (-180 to 180; negative toward red, magenta and blue,
            positive toward yellow, green and cyan) within about +-10 reads as natural skin.
  texture:  compare before and after: a ratio under about 0.6 on skin means texture was lost.
  halo:     light_rim > 8 means a bright fringe shows on dark backgrounds; dark_rim > 8 means a dark
            fringe shows on light ones.
  structure: relative only, since damage and content set the floor. On one restore of a
            damaged photo: as returned 11.3, shifted 3 px 14.0, after a bad Auto-Align 15.1 to
            29.6 (values move a little between runs). Compare candidates or before and after a
            fix, never against a fixed number.

Shell:
  python3 ps_gates.py diff A B [--region selection|outside|l,t,r,b|alpha:LAYER[:ring:N:gap:M]]
                               [--size W,H]  (A or B may be "composite")
  python3 ps_gates.py stats [--layer NAME] [--region ...]
  python3 ps_gates.py texture [--layer NAME] [--region ...] [--radius 2]
  python3 ps_gates.py halo LAYER [--band 2]
  python3 ps_gates.py structure A B [--region ...] [--size 256]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ps_run  # noqa: E402

COMMON_JS = r"""
var ARGS = %ARGS%;
function psg_cid(s) { return charIDToTypeID(s); }
function psg_find(c, key) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if ((typeof key === "number" && l.id === key) || (typeof key === "string" && l.name === key))
      return l;
    if (l.typename === "LayerSet") { var r = psg_find(l, key); if (r) return r; }
  }
  return null;
}
function psg_contains(set, t) {
  for (var i = 0; i < set.layers.length; i++) {
    var l = set.layers[i];
    if (l === t) return true;
    if (l.typename === "LayerSet" && psg_contains(l, t)) return true;
  }
  return false;
}
// Hide every layer outside the target's subtree, keep its ancestors visible.
function psg_solo(c, t) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if (l === t) { l.visible = true; continue; }
    if (l.typename === "LayerSet" && psg_contains(l, t)) { l.visible = true; psg_solo(l, t); }
    else l.visible = false;
  }
}
function psg_8bit_rgb(d) {
  if (String(d.mode) !== "DocumentMode.RGB") d.changeMode(ChangeMode.RGB);
  if (String(d.bitsPerChannel) !== "BitsPerChannelType.EIGHT")
    d.bitsPerChannel = BitsPerChannelType.EIGHT;
}
function psg_load_alpha(d, key) {
  var t = psg_find(d, key);
  if (!t) throw new Error("region layer not found: " + key);
  var desc = new ActionDescriptor(), ref = new ActionReference();
  ref.putProperty(psg_cid("Chnl"), psg_cid("fsel")); desc.putReference(psg_cid("null"), ref);
  var r2 = new ActionReference();
  r2.putEnumerated(psg_cid("Chnl"), psg_cid("Chnl"), psg_cid("Trsp"));
  r2.putIdentifier(psg_cid("Lyr "), t.id);
  desc.putReference(psg_cid("T   "), r2);
  executeAction(psg_cid("setd"), desc, DialogModes.NO);
  // Intersect with the layer mask when there is one.
  try {
    var mi = new ActionDescriptor(), mref = new ActionReference();
    mref.putEnumerated(psg_cid("Chnl"), psg_cid("Chnl"), psg_cid("Msk "));
    mref.putIdentifier(psg_cid("Lyr "), t.id);
    mi.putReference(psg_cid("null"), mref);
    var wref = new ActionReference(); wref.putProperty(psg_cid("Chnl"), psg_cid("fsel"));
    mi.putReference(psg_cid("With"), wref);
    executeAction(psg_cid("Intr"), mi, DialogModes.NO);
  } catch (e) {}
}
// Shape regions become the "psg_sel" alpha channel of the copy, which survives flattening.
function psg_shape_channel(d) {
  var r = ARGS.region;
  if (!r || r.alpha === undefined) return;
  psg_load_alpha(d, r.alpha);
  var has = true; try { d.selection.bounds; } catch (e) { has = false; }
  if (!has) throw new Error("region layer has no opaque pixels: " + r.alpha);
  var ch = d.channels.add(); ch.name = "psg_sel";
  if (r.ring) {
    var a = d.channels.add(); a.name = "psg_tmp"; d.selection.store(a);
    d.selection.expand(UnitValue((r.gap || 0) + r.ring, "px")); d.selection.store(ch);
    d.selection.load(a, SelectionType.REPLACE);
    if (r.gap) d.selection.expand(UnitValue(r.gap, "px"));
    d.selection.store(ch, SelectionType.DIMINISH);
    a.remove();
  } else {
    if (r.contract) d.selection.contract(UnitValue(r.contract, "px"));
    d.selection.store(ch);
  }
  d.activeChannels = d.componentChannels;
  d.selection.deselect();
}
// A flattened 8-bit RGB copy showing one layer (key) or the visible composite (key null).
// matte: "white" (flatten default) or "black" (a black layer under the target first).
function psg_isolate(src, key, matte) {
  app.activeDocument = src;
  var d = psr_dup(src, "psg_iso", false);
  app.activeDocument = d;
  psg_shape_channel(d);
  if (key !== null && key !== undefined) {
    var t = psg_find(d, key);
    if (!t) throw new Error("layer not found: " + key);
    psg_solo(d, t);
  }
  if (matte === "black") {
    var last = d.layers[d.layers.length - 1];
    if (last.isBackgroundLayer && !last.visible) last.isBackgroundLayer = false;
    if (!last.isBackgroundLayer) {
      var m = d.artLayers.add();
      m.move(last, ElementPlacement.PLACEAFTER);
      d.activeLayer = m;
      d.selection.selectAll();
      var k = new SolidColor(); k.rgb.red = 0; k.rgb.green = 0; k.rgb.blue = 0;
      d.selection.fill(k); d.selection.deselect();
    }
  }
  d.flatten();
  psg_8bit_rgb(d);
  return d;
}
function psg_region(d) {
  var r = ARGS.region;
  if (r === null || r === undefined) { d.selection.deselect(); return; }
  if (r === "selection" || r === "outside" || r.alpha !== undefined) {
    d.selection.load(d.channels.getByName("psg_sel"), SelectionType.REPLACE);
    if (r === "outside") d.selection.invert();
    return;
  }
  d.selection.select([[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]]);
}
function psg_hstats(h) {
  var n = 0, s = 0, s2 = 0, mn = -1, mx = -1;
  for (var i = 0; i < 256; i++) {
    n += h[i]; s += i * h[i]; s2 += i * i * h[i];
    if (h[i] > 0) { if (mn < 0) mn = i; mx = i; }
  }
  if (n === 0) return {n: 0};
  var mean = s / n, cum = 0, p99 = mx;
  for (var j = 0; j < 256; j++) { cum += h[j]; if (cum >= 0.99 * n) { p99 = j; break; } }
  var r2 = function (x) { return Math.round(x * 100) / 100; };
  return {n: n, mean: r2(mean), std: r2(Math.sqrt(Math.max(0, s2 / n - mean * mean))),
          min: mn, max: mx, p99: p99};
}
// The current selection travels to the copies as an alpha channel, then leaves src's History.
var src = app.activeDocument, psg_hs0 = src.activeHistoryState, psg_stored = false;
if (ARGS.region === "selection" || ARGS.region === "outside") {
  var psg_has = true;
  try { src.selection.bounds; } catch (e) { psg_has = false; }
  if (!psg_has) throw new Error("region '" + ARGS.region + "' needs an active selection");
  var psg_ch = src.channels.add(); psg_ch.name = "psg_sel"; src.selection.store(psg_ch);
  src.activeChannels = src.componentChannels;
  psg_stored = true;
}
function psg_restore() {
  if (!psg_stored) return;
  app.activeDocument = src;
  try { src.channels.getByName("psg_sel").remove(); } catch (e) {}
  src.activeHistoryState = psg_hs0;
}
"""

DIFF_JS = r"""
var dA = null, dB = null, out = null;
try {
  dA = psg_isolate(src, ARGS.a, "white");
  dB = psg_isolate(src, ARGS.b, "white");
  psg_restore();
  if (ARGS.size) {
    var r = ARGS.region, kx = ARGS.size[0] / dA.width.as("px"), ky = ARGS.size[1] / dA.height.as("px");
    var docs = [dA, dB];
    for (var q = 0; q < 2; q++) {
      app.activeDocument = docs[q];
      docs[q].resizeImage(UnitValue(ARGS.size[0], "px"), UnitValue(ARGS.size[1], "px"), null, ResampleMethod.BICUBIC);
    }
    if (r instanceof Array) ARGS.region = [r[0] * kx, r[1] * ky, r[2] * kx, r[3] * ky];
  }
  app.activeDocument = dB;
  dB.activeLayer.duplicate(dA, ElementPlacement.PLACEATBEGINNING);
  app.activeDocument = dA;
  dA.layers[0].blendMode = BlendMode.DIFFERENCE;
  dA.flatten();
  psg_region(dA);
  var names = ["red", "green", "blue"];
  out = {worst: {mean: 0, p99: 0, max: 0}};
  for (var c = 0; c < 3; c++) {
    var s = psg_hstats(dA.channels[c].histogram);
    out[names[c]] = {mean: s.mean, p99: s.p99, max: s.max};
    if (s.n === 0) { out.empty_region = true; continue; }
    if (s.mean > out.worst.mean) out.worst.mean = s.mean;
    if (s.p99 > out.worst.p99) out.worst.p99 = s.p99;
    if (s.max > out.worst.max) out.worst.max = s.max;
  }
  out.pixels = psg_hstats(dA.channels[0].histogram).n;
} finally {
  psg_restore();
  if (dB) psr_close(dB);
  if (dA) psr_close(dA);
  app.activeDocument = src;
}
return out;
"""

STATS_JS = r"""
var d = null, out = {};
try {
  d = psg_isolate(src, ARGS.layer, "white");
  psg_restore();
  app.activeDocument = d;
  psg_region(d);
  var names = ["red", "green", "blue"], m = [];
  for (var c = 0; c < 3; c++) {
    var s = psg_hstats(d.channels[c].histogram);
    out[names[c]] = {mean: s.mean, std: s.std};
    m.push(s.mean);
  }
  out.pixels = psg_hstats(d.channels[0].histogram).n;
  out.luminance = psg_hstats(d.histogram).mean;
  // UV vectorscope angle of the mean color (BT.601): the skin-tone line sits near 123 degrees.
  var y = 0.299 * m[0] + 0.587 * m[1] + 0.114 * m[2];
  var u = 0.492 * (m[2] - y), v = 0.877 * (m[0] - y);
  var ang = Math.atan2(v, u) * 180 / Math.PI; if (ang < 0) ang += 360;
  out.hue_angle = Math.round(ang * 10) / 10;
  var dl = ang - 123; if (dl >= 180) dl -= 360;   // -180 to 180: minus toward red, magenta, blue
  out.skin_line_delta = Math.round(dl * 10) / 10;
  out.chroma = Math.round(Math.sqrt(u * u + v * v) * 10) / 10;
  var mx = Math.max(m[0], m[1], m[2]), mn = Math.min(m[0], m[1], m[2]);
  out.saturation = mx > 0 ? Math.round(100 * (mx - mn) / mx) : 0;
} finally {
  psg_restore();
  if (d) psr_close(d);
  app.activeDocument = src;
}
return out;
"""

TEXTURE_JS = r"""
var d = null, out = {};
try {
  d = psg_isolate(src, ARGS.layer, "white");
  psg_restore();
  app.activeDocument = d;
  d.activeLayer.desaturate();
  d.activeLayer.applyHighPass(ARGS.radius);
  psg_region(d);
  var s = psg_hstats(d.channels[0].histogram);
  out = {energy: s.std, mean: s.mean, pixels: s.n, radius: ARGS.radius};
} finally {
  psg_restore();
  if (d) psr_close(d);
  app.activeDocument = src;
}
return out;
"""

STRUCTURE_JS = r"""
var dA = null, dB = null, out = null;
try {
  dA = psg_isolate(src, ARGS.a, "white");
  dB = psg_isolate(src, ARGS.b, "white");
  psg_restore();
  var W0 = dA.width.as("px"), H0 = dA.height.as("px"), k = Math.min(1, ARGS.size / Math.max(W0, H0));
  var w = Math.max(1, Math.round(W0 * k)), h = Math.max(1, Math.round(H0 * k));
  var docs = [dA, dB];
  for (var q = 0; q < 2; q++) {
    var d = docs[q];
    app.activeDocument = d;
    d.resizeImage(UnitValue(w, "px"), UnitValue(h, "px"), null, ResampleMethod.BICUBIC);
    d.activeLayer.desaturate();
    d.activeLayer.applyMedianNoise(1);
    // Equalize maps both images to the same tone distribution, so a colorize or a new
    // exposure stops counting; what is left after the High Pass is where the edges sit.
    d.activeLayer.equalize();
    d.activeLayer.applyHighPass(ARGS.radius);
    d.activeLayer.applyGaussianBlur(1);
  }
  var r = ARGS.region;
  if (r instanceof Array) ARGS.region = [r[0] * k, r[1] * k, r[2] * k, r[3] * k];
  else if (r === null || r === undefined) {
    var ix = Math.round(w * 0.06), iy = Math.round(h * 0.06);
    ARGS.region = [ix, iy, w - ix, h - iy];
  }
  app.activeDocument = dB;
  dB.activeLayer.duplicate(dA, ElementPlacement.PLACEATBEGINNING);
  app.activeDocument = dA;
  dA.layers[0].blendMode = BlendMode.DIFFERENCE;
  dA.flatten();
  psg_region(dA);
  var s = psg_hstats(dA.channels[0].histogram);
  out = {score: s.mean, p99: s.p99, pixels: s.n, at: [w, h]};
} finally {
  psg_restore();
  if (dB) psr_close(dB);
  if (dA) psr_close(dA);
  app.activeDocument = src;
}
return out;
"""

HALO_JS = r"""
// Rings around the target's alpha edge: the edge band straddles it, the inner ring sits just
// inside. Over black a light fringe lifts the band above the inner ring; over white a dark fringe
// drops it below.
var d = null, out = {band: ARGS.band};
try {
  app.activeDocument = src;
  d = psr_dup(src, "psg_halo", false);
  psg_restore();
  app.activeDocument = d;
  var t = psg_find(d, ARGS.layer);
  if (!t) throw new Error("layer not found: " + ARGS.layer);
  if (t.typename === "LayerSet") throw new Error("halo needs a layer, not a group");
  psg_solo(d, t);
  // Merge the target alone (an empty layer below gives mergeDown a partner), masks applied.
  var e = d.artLayers.add(); e.move(t, ElementPlacement.PLACEAFTER);
  d.activeLayer = t; t = t.merge();
  d.activeLayer = t;
  var ref = new ActionReference(), desc = new ActionDescriptor();
  ref.putProperty(psg_cid("Chnl"), psg_cid("fsel")); desc.putReference(psg_cid("null"), ref);
  var r2 = new ActionReference(); r2.putEnumerated(psg_cid("Chnl"), psg_cid("Chnl"), psg_cid("Trsp"));
  desc.putReference(psg_cid("T   "), r2);
  executeAction(psg_cid("setd"), desc, DialogModes.NO);
  var a = d.channels.add(); a.name = "psg_a"; d.selection.store(a);
  d.activeChannels = d.componentChannels;
  var B = UnitValue(ARGS.band, "px");
  d.selection.load(a, SelectionType.REPLACE); d.selection.expand(B);
  var edge = d.channels.add(); edge.name = "psg_edge"; d.selection.store(edge);
  d.selection.load(a, SelectionType.REPLACE); d.selection.contract(B);
  d.selection.store(edge, SelectionType.DIMINISH);
  var inner = d.channels.add(); inner.name = "psg_inner"; d.selection.store(inner);
  d.selection.load(a, SelectionType.REPLACE); d.selection.contract(UnitValue(3 * ARGS.band, "px"));
  d.selection.store(inner, SelectionType.DIMINISH);
  d.activeChannels = d.componentChannels;
  d.selection.deselect();
  var bottom = d.artLayers.add(); bottom.move(t, ElementPlacement.PLACEAFTER);
  var hs = d.activeHistoryState, res = {};
  var mattes = [["black", 0], ["white", 255]];
  for (var k = 0; k < 2; k++) {
    d.activeHistoryState = hs;
    d.activeLayer = bottom;
    var col = new SolidColor(); col.rgb.red = col.rgb.green = col.rgb.blue = mattes[k][1];
    d.selection.selectAll(); d.selection.fill(col); d.selection.deselect();
    d.flatten();
    psg_8bit_rgb(d);
    d.selection.load(d.channels.getByName("psg_edge"), SelectionType.REPLACE);
    var se = psg_hstats(d.histogram);
    d.selection.load(d.channels.getByName("psg_inner"), SelectionType.REPLACE);
    var si = psg_hstats(d.histogram);
    res[mattes[k][0]] = {edge: se.mean, inner: si.mean, edge_px: se.n, inner_px: si.n};
  }
  out.over_black = res.black; out.over_white = res.white;
  out.light_rim = Math.round((res.black.edge - res.black.inner / 2) * 10) / 10;
  out.dark_rim = Math.round((res.white.inner / 2 + 127.5 - res.white.edge) * 10) / 10;
} finally {
  psg_restore();
  if (d) psr_close(d);
  app.activeDocument = src;
}
return out;
"""


def _key(v):
    if v is None or v == "composite":
        return None
    if isinstance(v, int):
        return v
    s = str(v)
    return int(s) if s.isdigit() else s


def _run(js, args, timeout=180):
    body = COMMON_JS.replace("%ARGS%", json.dumps(args)) + js
    res = ps_run.run(body, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError(res.get("error"))
    return res["result"]


def diff(a, b, region=None, size=None):
    return _run(DIFF_JS, {"a": _key(a), "b": _key(b), "region": region,
                          "size": [int(size[0]), int(size[1])] if size else None})


def stats(layer=None, region=None):
    return _run(STATS_JS, {"layer": _key(layer), "region": region})


def texture(layer=None, region=None, radius=2):
    return _run(TEXTURE_JS, {"layer": _key(layer), "region": region, "radius": float(radius)})


def structure(a, b, region=None, size=256):
    # High Pass radius 6 at 256 px matches edges a few pixels wide; scale it with size.
    return _run(STRUCTURE_JS, {"a": _key(a), "b": _key(b), "region": region, "size": int(size),
                               "radius": round(6 * size / 256.0, 1)})


def halo(layer, band=2):
    return _run(HALO_JS, {"layer": _key(layer), "region": None, "band": int(band)})


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        i = argv.index(flag)
        return cast(argv[i + 1])
    return default


def _region(s):
    if s is None or s in ("selection", "outside"):
        return s
    if s.startswith("alpha:"):
        parts = s.split(":")
        out = {"alpha": _key(parts[1])}
        for k, v in zip(parts[2::2], parts[3::2]):
            out[k] = int(v)
        return out
    return [int(float(x)) for x in s.split(",")]


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, region = argv[0], _region(_opt(argv, "--region"))
    try:
        if cmd == "diff":
            size = _opt(argv, "--size")
            out = diff(argv[1], argv[2], region, [int(v) for v in size.split(",")] if size else None)
        elif cmd == "stats":
            out = stats(_opt(argv, "--layer"), region)
        elif cmd == "texture":
            out = texture(_opt(argv, "--layer"), region, _opt(argv, "--radius", float, 2))
        elif cmd == "halo":
            out = halo(argv[1], _opt(argv, "--band", int, 2))
        elif cmd == "structure":
            out = structure(argv[1], argv[2], region, _opt(argv, "--size", int, 256))
        else:
            print("unknown command: " + cmd, file=sys.stderr)
            return 2
    except RuntimeError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    print(json.dumps({"ok": True, "result": out}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
