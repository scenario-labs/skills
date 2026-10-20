"""
ps_generative: the Photoshop half of a selection-scoped Scenario edit (inpaint, instruction edit,
expand). Capture the selection with context around it, check each model result before it lands,
place it back through a mask rebuilt from the captured mask file, then prove that nothing outside
the mask changed. The model runs are Scenario MCP steps the agent takes between these calls.

Library:
  import ps_generative as GE
  cap = GE.capture(out_dir, margin=None, polarity="white", max_px=None)
      # the current selection plus a context margin (default: half the selection's long side, at
      # least 64 px, clipped to the canvas). Writes context.png (merged pixels), mask_edit.png
      # (white = edit) and the model's input: input.png and, per polarity, mask_model.png
      # ("white": white = edit; "black": black = edit; "alpha": an RGBA mask, transparent =
      # edit; "punch": no mask, input.png has the edit area transparent). Read the polarity off
      # the model's schema. Returns the capture dict, also saved as capture.json.
  GE.check(cap, result_path, ring=12, gap=2, blur=4)
      # a model result against the capture, in temporary documents: "inside" and "outside" the
      # change in and away from the mask; "seam" compares both images blurred by `blur` px in a
      # ring just outside the mask, split into "bias" (worst channel's mean tone shift) and
      # "residual" (mean difference once that shift is removed: misalignment, wrong scale).
      # Flags: aspect_ok, edited (inside mean >= 3), seam_ok (bias < 12 and residual < 6),
      # polarity_suspect (outside changed more than inside).
  GE.place_edit(cap, result_path, name, feather=2, xmp=None)
      # the result as an embedded smart object on the capture box, with a layer mask built from
      # mask_edit.png (so a selection lost meanwhile does not matter), feathered, one History
      # state. A layer that lands inside a hidden group moves above it ("moved_out_of": its
      # name). Returns {"id", "name", "bounds", "moved_out_of"}.
  GE.verify(cap, feather=2)
      # exports the composite at the capture box again and compares it with context.png:
      # "untouched" is true when the max difference outside the mask (past the feather) is <= 2;
      # "edited" is true when the composite inside the mask changed (mean >= 3).
  GE.expand(out_dir, left=0, top=0, right=0, bottom=0, overlap=32, max_px=None)
      # Canvas Size by those pixels (one History state), then a capture of the whole canvas with
      # the new area plus an overlap band as the edit area; original.png holds the old canvas
      # for models that take an image and a target size.
  GE.tile_plan(bounds, tile, overlap=64)
      # boxes of at most tile x tile px covering bounds, overlapping, for a region larger than
      # a model's output
Shell:
  python3 ps_generative.py capture OUT_DIR [--margin N] [--polarity white|black|alpha|punch] [--max N]
      | check CAPTURE.json RESULT | place CAPTURE.json RESULT NAME [--feather N]
      | verify CAPTURE.json | expand OUT_DIR --right N [--left N --top N --bottom N]
      | tiles l,t,r,b TILE [--overlap N]
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scenario-photoshop-expert", "scripts"))
import ps_io as IO  # noqa: E402
import ps_run  # noqa: E402

MIN_MARGIN = 64
EDITED_MEAN = 3.0
# Models re-render the whole frame, so raw pixels just outside the mask differ (mean 17 to 18 on
# an aligned real result) and the layer mask hides that. A seam shows when tone or alignment is
# off, which survives a blur. On two real takes: bias 6.4 and 7.3, residual 3.5 and 3.4. A 3 px
# shift: residual 8.8; 3% scale: 6.9; a +20/-20 tint: bias 20.6. Authoring-time thresholds.
SEAM_BLUR = 4
SEAM_BIAS = 12.0
SEAM_RESIDUAL = 6.0

HELPERS_JS = r"""
var ARGS = %ARGS%;
function pg_c(s) { return charIDToTypeID(s); }
function pg_s(s) { return stringIDToTypeID(s); }
function pg_open(path) {
  var f = new File(path);
  if (!f.exists) throw new Error("file not found: " + path);
  var d = app.open(f); __psr_created.push(d.id);
  return d;
}
function pg_rgb8(d) {
  app.activeDocument = d;
  try { d.flatten(); } catch (e) {}
  if (String(d.mode) !== "DocumentMode.RGB") d.changeMode(ChangeMode.RGB);
  if (String(d.bitsPerChannel) !== "BitsPerChannelType.EIGHT") d.bitsPerChannel = BitsPerChannelType.EIGHT;
}
function pg_fit(d, w, h) {
  app.activeDocument = d;
  if (d.width.as("px") !== w || d.height.as("px") !== h)
    d.resizeImage(UnitValue(w, "px"), UnitValue(h, "px"), null, ResampleMethod.BICUBIC);
}
// The mask file (white = edit), sized to box b, as an alpha channel of target. Grayscale canvas
// growth fills with the background color, so it is set to black for the time of the job.
function pg_mask_channel(target, path, b) {
  var m = pg_open(path);
  app.activeDocument = m;
  try { m.flatten(); } catch (e) {}
  if (String(m.mode) !== "DocumentMode.GRAYSCALE") m.changeMode(ChangeMode.GRAYSCALE);
  if (String(m.bitsPerChannel) !== "BitsPerChannelType.EIGHT") m.bitsPerChannel = BitsPerChannelType.EIGHT;
  var bw = b[2] - b[0], bh = b[3] - b[1];
  pg_fit(m, bw, bh);
  var W = target.width.as("px"), H = target.height.as("px");
  var bg = app.backgroundColor, k = new SolidColor();
  k.rgb.red = 0; k.rgb.green = 0; k.rgb.blue = 0;
  app.backgroundColor = k;
  try {
    if (b[0] > 0 || b[1] > 0) m.resizeCanvas(UnitValue(bw + b[0], "px"), UnitValue(bh + b[1], "px"), AnchorPosition.BOTTOMRIGHT);
    if (W > b[2] || H > b[3]) m.resizeCanvas(UnitValue(W, "px"), UnitValue(H, "px"), AnchorPosition.TOPLEFT);
  } finally { app.backgroundColor = bg; }
  var ch = m.channels[0].duplicate(target);
  psr_close(m);
  // Renaming a channel needs its own document frontmost.
  app.activeDocument = target;
  ch.name = "pg_mask";
  target.activeChannels = target.componentChannels;
  return ch;
}
function pg_has_selection(d) { try { d.selection.bounds; return true; } catch (e) { return false; } }
function pg_stats(d) {
  if (!pg_has_selection(d)) return null;
  var out = {mean: 0, p99: 0, max: 0, n: 0};
  for (var c = 0; c < 3; c++) {
    var h = d.channels[c].histogram, n = 0, s = 0, mx = 0;
    for (var i = 0; i < 256; i++) { n += h[i]; s += i * h[i]; if (h[i] > 0) mx = i; }
    if (n === 0) return null;
    var cum = 0, p99 = mx;
    for (var j = 0; j < 256; j++) { cum += h[j]; if (cum >= 0.99 * n) { p99 = j; break; } }
    out.mean = Math.max(out.mean, Math.round(s / n * 100) / 100);
    out.p99 = Math.max(out.p99, p99); out.max = Math.max(out.max, mx); out.n = n;
  }
  return out;
}
function pg_means(d) {
  var m = [];
  for (var c = 0; c < 3; c++) {
    var h = d.channels[c].histogram, n = 0, s = 0;
    for (var i = 0; i < 256; i++) { n += h[i]; s += i * h[i]; }
    m.push(n ? s / n : 0);
  }
  return m;
}
"""

# An RGBA mask from mask_edit.png: opaque where kept, transparent where edited (soft edges kept).
ALPHA_MASK_JS = r"""
var d = psr_new_doc(ARGS.size[0], ARGS.size[1], "pg_alpha", {fill: "transparent"});
var ch = pg_mask_channel(d, ARGS.mask, [0, 0, ARGS.size[0], ARGS.size[1]]);
d.selection.load(ch); d.selection.invert();
var k = new SolidColor(); k.rgb.red = 0; k.rgb.green = 0; k.rgb.blue = 0;
d.selection.fill(k); d.selection.deselect(); ch.remove();
var out = psr_export(d, ARGS.out, "png");
psr_close(d);
return out;
"""

# |A - B| inside the mask and outside it (past gap).
DIFF_FILES_JS = r"""
var A = pg_open(ARGS.a), res = {};
pg_rgb8(A);
var W = A.width.as("px"), H = A.height.as("px");
var B = pg_open(ARGS.b);
res.b_size = [B.width.as("px"), B.height.as("px")];
pg_rgb8(B);
pg_fit(B, W, H);
B.activeLayer.duplicate(A, ElementPlacement.PLACEATBEGINNING);
psr_close(B);
app.activeDocument = A;
A.layers[0].blendMode = BlendMode.DIFFERENCE;
A.flatten();
var ch = pg_mask_channel(A, ARGS.mask, [0, 0, W, H]), sel = A.selection;
sel.load(ch); res.inside = pg_stats(A);
sel.load(ch);
if (ARGS.gap > 0) sel.expand(UnitValue(ARGS.gap, "px"));
sel.invert(); res.outside = pg_stats(A);
sel.deselect();
res.size = [W, H];
psr_close(A);
return res;
"""

# Seam in a ring of width `ring` past gap: B keeps the context inside the mask (so the edit cannot
# blur into the ring), both are blurred, then B's mean tone shift is measured, removed, and what
# differs after that is the residual.
SEAM_JS = r"""
var A = pg_open(ARGS.a);
pg_rgb8(A);
var W = A.width.as("px"), H = A.height.as("px");
var B = pg_open(ARGS.b);
pg_rgb8(B);
pg_fit(B, W, H);
B.activeLayer.duplicate(A, ElementPlacement.PLACEATBEGINNING);
psr_close(B);
app.activeDocument = A;
var base = A.layers[A.layers.length - 1], top = A.layers[0];
var ch = pg_mask_channel(A, ARGS.mask, [0, 0, W, H]), sel = A.selection;
A.activeLayer = top;
sel.load(ch);
if (ARGS.gap > 0) sel.expand(UnitValue(ARGS.gap, "px"));
sel.clear(); sel.deselect();
base.duplicate(top, ElementPlacement.PLACEAFTER);
var M = top.merge();
base.applyGaussianBlur(ARGS.blur); M.applyGaussianBlur(ARGS.blur);
// A new channel becomes the only visible one, and histograms need the color channels.
var ring = A.channels.add(); ring.name = "pg_ring"; A.activeChannels = A.componentChannels;
sel.load(ch); sel.expand(UnitValue(ARGS.gap + ARGS.ring, "px")); sel.store(ring);
sel.load(ch);
if (ARGS.gap > 0) sel.expand(UnitValue(ARGS.gap, "px"));
sel.invert(); sel.load(ring, SelectionType.INTERSECT); sel.store(ring);
M.visible = false; var ma = pg_means(A);
M.visible = true; var mb = pg_means(A);
var bias = [], add = [], sub = [];
for (var c = 0; c < 3; c++) {
  var k = Math.round(mb[c] - ma[c]);
  bias.push(Math.round((mb[c] - ma[c]) * 100) / 100); sub.push(Math.max(0, k)); add.push(Math.max(0, -k));
}
sel.deselect();
function shift(rgb, mode) {
  if (rgb[0] + rgb[1] + rgb[2] === 0) return;
  A.activeLayer = M;
  var L = A.artLayers.add(), k = new SolidColor();
  k.rgb.red = rgb[0]; k.rgb.green = rgb[1]; k.rgb.blue = rgb[2];
  sel.selectAll(); sel.fill(k); sel.deselect();
  L.blendMode = mode;
  M = L.merge();
}
shift(sub, BlendMode.SUBTRACT); shift(add, BlendMode.LINEARDODGE);
M.blendMode = BlendMode.DIFFERENCE;
sel.load(ring);
var resid = pg_stats(A);
sel.deselect();
psr_close(A);
var worst = 0;
for (var j = 0; j < 3; j++) worst = Math.max(worst, Math.abs(bias[j]));
return {bias: Math.round(worst * 100) / 100, bias_rgb: bias, residual: resid ? resid.mean : null,
        n: resid ? resid.n : 0, blur: ARGS.blur, ring: ARGS.ring};
"""

PLACE_JS = r"""
if (app.documents.length === 0) throw new Error("no document open");
var d = app.activeDocument, b = ARGS.bounds;
if (d.width.as("px") !== ARGS.canvas[0] || d.height.as("px") !== ARGS.canvas[1])
  throw new Error("canvas is " + d.width.as("px") + "x" + d.height.as("px") + ", the capture was " +
                  ARGS.canvas[0] + "x" + ARGS.canvas[1]);
var ch = pg_mask_channel(d, ARGS.mask, b);
var pd = new ActionDescriptor(); pd.putPath(pg_c("null"), new File(ARGS.path));
pd.putEnumerated(pg_c("FTcs"), pg_c("QCSt"), pg_c("Qcsa"));
executeAction(pg_c("Plc "), pd, DialogModes.NO);
var L = d.activeLayer;
// Place lands above the active layer, inside its group. A hidden group would hide the edit while
// verify still passes, so the layer moves above the outermost hidden group.
var moved = null, hid = null;
for (var p = L.parent; p && p.typename === "LayerSet"; p = p.parent) if (!p.visible) hid = p;
if (hid) { moved = hid.name; L.move(hid, ElementPlacement.PLACEBEFORE); d.activeLayer = L; }
function box() {
  var r = new ActionReference(); r.putIdentifier(pg_c("Lyr "), L.id);
  var t = executeActionGet(r).getObjectValue(pg_s("smartObjectMore")).getList(pg_s("transform"));
  return [Math.min(t.getDouble(0), t.getDouble(6)), Math.min(t.getDouble(1), t.getDouble(3)),
          Math.max(t.getDouble(2), t.getDouble(4)), Math.max(t.getDouble(5), t.getDouble(7))];
}
var c = box();
L.resize((b[2] - b[0]) / (c[2] - c[0]) * 100, (b[3] - b[1]) / (c[3] - c[1]) * 100, AnchorPosition.TOPLEFT);
c = box();
L.translate(UnitValue(b[0] - c[0], "px"), UnitValue(b[1] - c[1], "px"));
L.name = ARGS.name;
d.selection.load(ch);
if (ARGS.feather > 0) d.selection.feather(UnitValue(ARGS.feather, "px"));
var md = new ActionDescriptor(); md.putClass(pg_c("Nw  "), pg_c("Chnl"));
var mr = new ActionReference(); mr.putEnumerated(pg_c("Chnl"), pg_c("Chnl"), pg_c("Msk "));
md.putReference(pg_c("At  "), mr);
md.putEnumerated(pg_c("Usng"), pg_c("UsrM"), pg_c("RvlS"));
executeAction(pg_c("Mk  "), md, DialogModes.NO);
ch.remove();
d.activeChannels = d.componentChannels;
if (ARGS.xmp) L.xmpMetadata.rawData = ARGS.xmp;
c = box();
return {id: L.id, name: L.name, bounds: [Math.round(c[0]), Math.round(c[1]), Math.round(c[2]), Math.round(c[3])],
        moved_out_of: moved};
"""

EXPAND_JS = r"""
if (app.documents.length === 0) throw new Error("no document open");
var d = app.activeDocument, w = d.width.as("px"), h = d.height.as("px");
var l = ARGS.left, t = ARGS.top, r = ARGS.right, bo = ARGS.bottom, o = ARGS.overlap;
if (l > 0 || t > 0) d.resizeCanvas(UnitValue(w + l, "px"), UnitValue(h + t, "px"), AnchorPosition.BOTTOMRIGHT);
if (r > 0 || bo > 0) d.resizeCanvas(UnitValue(w + l + r, "px"), UnitValue(h + t + bo, "px"), AnchorPosition.TOPLEFT);
var W = w + l + r, H = h + t + bo;
// Edit area: everything outside the old canvas, plus an overlap band inside it on expanded sides.
var x0 = l + (l > 0 ? o : 0), y0 = t + (t > 0 ? o : 0), x1 = l + w - (r > 0 ? o : 0), y1 = t + h - (bo > 0 ? o : 0);
d.selection.selectAll();
d.selection.select([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], SelectionType.DIMINISH);
return {canvas: [W, H], old: [l, t, l + w, t + h], keep: [x0, y0, x1, y1]};
"""


def _run(js, args, undo=None, timeout=300):
    body = HELPERS_JS.replace("%ARGS%", json.dumps(args)) + js
    res = ps_run.run(body, undo=undo, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError("%s (line %s)" % (res.get("error"), res.get("line")))
    return res["result"]


def _load(cap):
    if isinstance(cap, str):
        with open(cap) as f:
            return json.load(f)
    return cap


def _canvas():
    r = ps_run.run("var d = app.activeDocument; return [d.width.as('px'), d.height.as('px')];")
    if not r.get("ok"):
        raise RuntimeError(r.get("error"))
    return r["result"]


def default_margin(sel_bounds):
    l, t, r, b = sel_bounds
    return max(MIN_MARGIN, int(round(max(r - l, b - t) / 2.0)))


def capture(out_dir, margin=None, polarity="white", max_px=None):
    if polarity not in ("white", "black", "alpha", "punch"):
        raise ValueError("polarity must be white, black, alpha or punch")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    sel = IO.selection()["bounds"]
    if not sel:
        raise RuntimeError("capture needs an active selection around the area to edit")
    pad = default_margin(sel) if margin is None else int(margin)
    ctx = IO.export_region(os.path.join(out_dir, "context.png"), pad=pad, max_px=max_px)
    b = ctx["bounds"]
    edit = IO.export_mask(os.path.join(out_dir, "mask_edit.png"), bounds=b, max_px=max_px)
    cap = {"bounds": b, "selection": sel, "margin": pad, "scale": ctx["scale"],
           "size": [ctx["width"], ctx["height"]], "canvas": _canvas(), "polarity": polarity,
           "max_px": max_px, "context": ctx["path"], "mask_edit": edit["path"], "dir": out_dir}
    if polarity == "punch":
        cap["input"] = IO.export_region(os.path.join(out_dir, "input.png"), bounds=b, max_px=max_px,
                                        punch_selection=True)["path"]
        cap["mask_model"] = None
    elif polarity == "alpha":
        cap["input"] = cap["context"]
        cap["mask_model"] = _run(ALPHA_MASK_JS, {"mask": edit["path"], "size": cap["size"],
                                                 "out": os.path.join(out_dir, "mask_model.png")})
    else:
        cap["input"] = cap["context"]
        cap["mask_model"] = edit["path"] if polarity == "white" else IO.export_mask(
            os.path.join(out_dir, "mask_model.png"), bounds=b, invert=True, max_px=max_px)["path"]
    with open(os.path.join(out_dir, "capture.json"), "w") as f:
        json.dump(cap, f, indent=1)
    return cap


def _diff_files(a, b, mask, gap):
    return _run(DIFF_FILES_JS, {"a": os.path.abspath(a), "b": os.path.abspath(b),
                                "mask": os.path.abspath(mask), "gap": int(gap)})


def check(cap, result_path, ring=12, gap=2, blur=SEAM_BLUR):
    cap = _load(cap)
    r = _diff_files(cap["context"], result_path, cap["mask_edit"], gap)
    w, h = cap["size"]
    bw, bh = r["b_size"]
    inside, outside = r.get("inside"), r.get("outside")
    r["aspect_ok"] = abs(bw / float(bh) - w / float(h)) <= 0.01 * (w / float(h))
    r["edited"] = bool(inside and inside["mean"] >= EDITED_MEAN)
    r["polarity_suspect"] = bool(inside and outside and outside["mean"] > inside["mean"] and
                                 outside["mean"] >= EDITED_MEAN)
    seam = None
    if ring > 0:
        seam = _run(SEAM_JS, {"a": os.path.abspath(cap["context"]), "b": os.path.abspath(result_path),
                              "mask": os.path.abspath(cap["mask_edit"]), "gap": int(gap),
                              "ring": int(ring), "blur": float(blur)})
    r["seam"] = seam
    r["seam_ok"] = bool(seam is None or seam["residual"] is None or
                        (seam["bias"] < SEAM_BIAS and seam["residual"] < SEAM_RESIDUAL))
    return r


def place_edit(cap, result_path, name, feather=2, xmp=None, undo="Scenario: Generative edit"):
    cap = _load(cap)
    if isinstance(xmp, dict):
        xmp = IO.provenance_xmp(xmp)
    return _run(PLACE_JS, {"path": os.path.abspath(result_path), "name": name, "bounds": cap["bounds"],
                           "canvas": cap["canvas"], "mask": cap["mask_edit"], "feather": float(feather),
                           "xmp": xmp}, undo=undo)


def verify(cap, feather=2):
    cap = _load(cap)
    after = IO.export_region(os.path.join(cap["dir"], "after.png"), bounds=cap["bounds"],
                             max_px=cap.get("max_px"))
    gap = int(round(feather * 2)) + 2
    r = _diff_files(cap["context"], after["path"], cap["mask_edit"], gap)
    out, inside = r.get("outside"), r.get("inside")
    r["untouched"] = bool(out is None or out["max"] <= 2)
    # A take that landed hidden (or under an opaque layer) leaves the composite as it was.
    r["edited"] = bool(inside and inside["mean"] >= EDITED_MEAN)
    r["after"] = after["path"]
    return r


def expand(out_dir, left=0, top=0, right=0, bottom=0, overlap=32, max_px=None,
           undo="Scenario: Expand canvas"):
    if min(left, top, right, bottom) < 0 or not (left or top or right or bottom):
        raise ValueError("give at least one side to expand, in positive pixels")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    pre = _canvas()
    original = IO.export_region(os.path.join(out_dir, "original.png"), bounds=[0, 0, pre[0], pre[1]],
                                max_px=max_px)
    e = _run(EXPAND_JS, {"left": int(left), "top": int(top), "right": int(right),
                         "bottom": int(bottom), "overlap": int(overlap)}, undo=undo)
    full = [0, 0, e["canvas"][0], e["canvas"][1]]
    ctx = IO.export_region(os.path.join(out_dir, "context.png"), bounds=full, max_px=max_px)
    inp = IO.export_region(os.path.join(out_dir, "input.png"), bounds=full, max_px=max_px,
                           punch_selection=True)
    edit = IO.export_mask(os.path.join(out_dir, "mask_edit.png"), bounds=full, max_px=max_px)
    cap = {"bounds": full, "selection": None, "margin": 0, "scale": ctx["scale"],
           "size": [ctx["width"], ctx["height"]], "canvas": e["canvas"], "polarity": "punch",
           "max_px": max_px, "context": ctx["path"], "mask_edit": edit["path"], "input": inp["path"],
           "mask_model": edit["path"], "original": original["path"], "old": e["old"], "keep": e["keep"],
           "dir": out_dir}
    with open(os.path.join(out_dir, "capture.json"), "w") as f:
        json.dump(cap, f, indent=1)
    return cap


def tile_plan(bounds, tile, overlap=64):
    l, t, r, b = [int(v) for v in bounds]
    tile, overlap = int(tile), int(overlap)
    if tile <= overlap:
        raise ValueError("tile must be larger than overlap")

    def starts(a, z):
        if z - a <= tile:
            return [a]
        n = -(-(z - a - overlap) // (tile - overlap))
        step = (z - a - tile) / float(n - 1)
        return [a + int(round(i * step)) for i in range(n)]

    return [[x, y, min(r, x + tile), min(b, y + tile)] for y in starts(t, b) for x in starts(l, r)]


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        return cast(argv[argv.index(flag) + 1])
    return default


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd = argv[0]
    try:
        if cmd == "capture":
            out = capture(argv[1], _opt(argv, "--margin", int), _opt(argv, "--polarity", str, "white"),
                          _opt(argv, "--max", int))
        elif cmd == "check":
            out = check(argv[1], argv[2])
        elif cmd == "place":
            out = place_edit(argv[1], argv[2], argv[3], _opt(argv, "--feather", float, 2))
        elif cmd == "verify":
            out = verify(argv[1], _opt(argv, "--feather", float, 2))
        elif cmd == "expand":
            out = expand(argv[1], _opt(argv, "--left", int, 0), _opt(argv, "--top", int, 0),
                         _opt(argv, "--right", int, 0), _opt(argv, "--bottom", int, 0),
                         _opt(argv, "--overlap", int, 32), _opt(argv, "--max", int))
        elif cmd == "tiles":
            out = tile_plan([int(v) for v in argv[1].split(",")], int(argv[2]),
                            _opt(argv, "--overlap", int, 64))
        else:
            print("unknown command: " + cmd, file=sys.stderr)
            return 2
    except (RuntimeError, ValueError) as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    print(json.dumps({"ok": True, "result": out}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
