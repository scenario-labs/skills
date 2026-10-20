"""
ps_review: make the images an agent looks at before it calls a stage done. Previews come from a
merged duplicate the job owns, so the user's document gets no history state and no edit.

Library:
  import ps_review as R
  R.preview("/tmp/review/stage1.png")                  # whole canvas, long edge <= 1600 px, sRGB
  R.preview(path, max_px=2400)                         # bigger look
  R.preview(path, crop=[l, t, r, b], max_px=0)         # 100% crop: edges, halos, seams, grain
  R.preview(path, layers_only=["Hero", "Shadow"])      # only these layers visible in the copy
  R.sheet([p1, p2, p3], "/tmp/review/sheet.jpg", labels=["before", "v1", "v2"])
  R.before_after(p_before, p_after, out)               # side by side, same height
  R.overlay(out, a, b, crop=None, max_px=1600)         # alignment overlay: layer a's luminance
                                                       # in red, b's in cyan. Gray where they
                                                       # line up, red/cyan fringes where they
                                                       # do not, whatever the colors
Shell:
  python3 ps_review.py preview OUT.png [--max 1600] [--crop l,t,r,b]
  python3 ps_review.py sheet OUT.jpg IMG [IMG ...]
  python3 ps_review.py overlay OUT.png LAYER_A LAYER_B [--crop l,t,r,b]

Always open the result with the image reader and look at it. The preview is converted to sRGB
8-bit so what the agent sees matches what a browser shows; a 16-bit or CMYK master is untouched.
A 32-bit document is reduced through 16-bit first; if Photoshop refuses, the error says so.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ps_run  # noqa: E402

PREVIEW_JS = r"""
if (app.documents.length === 0) throw new Error("no document open");
var src = app.activeDocument, out = %OUT%, maxpx = %MAX%, crop = %CROP%, only = %ONLY%;
var dup = psr_dup(src, "psr_preview", false);
app.activeDocument = dup;
try {
  if (only) {
    var keep = {};
    for (var i = 0; i < only.length; i++) keep[only[i]] = true;
    var hideAll = function (c) {
      for (var j = 0; j < c.layers.length; j++) {
        var l = c.layers[j];
        if (l.typename === "LayerSet") { if (!keep[l.name]) hideAll(l); }
        else if (!keep[l.name]) l.visible = false;
      }
    };
    hideAll(dup);
  }
  try { dup.mergeVisibleLayers(); } catch (e) { psr_log("merge skipped: " + e); }
  if (crop) dup.crop([UnitValue(crop[0], "px"), UnitValue(crop[1], "px"),
                      UnitValue(crop[2], "px"), UnitValue(crop[3], "px")]);
  if (String(dup.bitsPerChannel) === "BitsPerChannelType.THIRTYTWO")
    dup.bitsPerChannel = BitsPerChannelType.SIXTEEN;
  if (String(dup.mode) !== "DocumentMode.RGB") dup.changeMode(ChangeMode.RGB);
  try { dup.convertProfile("sRGB IEC61966-2.1", Intent.RELATIVECOLORIMETRIC, true, false); }
  catch (e) { psr_log("sRGB conversion skipped: " + e); }
  if (String(dup.bitsPerChannel) !== "BitsPerChannelType.EIGHT")
    dup.bitsPerChannel = BitsPerChannelType.EIGHT;
  var w = dup.width.as("px"), h = dup.height.as("px"), s = 1;
  if (maxpx > 0 && Math.max(w, h) > maxpx) {
    s = maxpx / Math.max(w, h);
    dup.resizeImage(UnitValue(Math.round(w * s), "px"), UnitValue(Math.round(h * s), "px"), null,
                    ResampleMethod.BICUBICSHARPER);
  }
  var fmt = /\.jpe?g$/i.test(out) ? "jpg" : "png";
  psr_export(dup, out, fmt, {quality: 10});
  var res = {path: out, width: dup.width.as("px"), height: dup.height.as("px"), scale: s,
             source: {name: src.name, width: src.width.as("px"), height: src.height.as("px")}};
} finally {
  psr_close(dup);
  app.activeDocument = src;
}
return res;
"""


OVERLAY_JS = r"""
var ARGS = %ARGS%;
function rv_c(s) { return charIDToTypeID(s); }
function rv_has(set, t) {
  for (var i = 0; i < set.layers.length; i++) {
    var l = set.layers[i];
    if (l === t || (l.typename === "LayerSet" && rv_has(l, t))) return true;
  }
  return false;
}
function rv_solo(c, t) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if (l === t) l.visible = true;
    else if (l.typename === "LayerSet" && rv_has(l, t)) { l.visible = true; rv_solo(l, t); }
    else l.visible = false;
  }
}
function rv_find(c, key) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if ((typeof key === "number" && l.id === key) || l.name === key) return l;
    if (l.typename === "LayerSet") { var r = rv_find(l, key); if (r) return r; }
  }
  return null;
}
// A flattened, cropped, desaturated, equalized copy showing one layer. Equalizing gives both
// sides the same tone spread, so a faded base does not tint the overlay; cropping first keeps
// the spread to the area under review.
function rv_gray(src, key, crop) {
  app.activeDocument = src;
  var d = psr_dup(src, "psr_overlay", false);
  app.activeDocument = d;
  var t = rv_find(d, key);
  if (!t) throw new Error("layer not found: " + key);
  rv_solo(d, t);
  d.flatten();
  if (String(d.mode) !== "DocumentMode.RGB") d.changeMode(ChangeMode.RGB);
  if (String(d.bitsPerChannel) !== "BitsPerChannelType.EIGHT") d.bitsPerChannel = BitsPerChannelType.EIGHT;
  if (crop) d.crop([UnitValue(crop[0], "px"), UnitValue(crop[1], "px"), UnitValue(crop[2], "px"), UnitValue(crop[3], "px")]);
  d.activeLayer.desaturate();
  d.activeLayer.equalize();
  return d;
}
if (app.documents.length === 0) throw new Error("no document open");
var src = app.activeDocument, dA = null, dB = null, out = null;
try {
  dA = rv_gray(src, ARGS.a, ARGS.crop);
  dB = rv_gray(src, ARGS.b, ARGS.crop);
  dB.activeLayer.duplicate(dA, ElementPlacement.PLACEATBEGINNING);
  psr_close(dB); dB = null;
  app.activeDocument = dA;
  // Advanced Blending: the top layer writes only green and blue, so red keeps layer a.
  var desc = new ActionDescriptor(), ref = new ActionReference();
  ref.putEnumerated(rv_c("Lyr "), rv_c("Ordn"), rv_c("Trgt"));
  desc.putReference(rv_c("null"), ref);
  var lyr = new ActionDescriptor(), list = new ActionList();
  list.putEnumerated(rv_c("Chnl"), rv_c("Grn "));
  list.putEnumerated(rv_c("Chnl"), rv_c("Bl  "));
  lyr.putList(stringIDToTypeID("channelRestrictions"), list);
  desc.putObject(rv_c("T   "), rv_c("Lyr "), lyr);
  executeAction(rv_c("setd"), desc, DialogModes.NO);
  dA.flatten();
  var w = dA.width.as("px"), h = dA.height.as("px"), k = ARGS.max_px > 0 ? Math.min(1, ARGS.max_px / Math.max(w, h)) : 1;
  if (k < 1) dA.resizeImage(UnitValue(Math.round(w * k), "px"), UnitValue(Math.round(h * k), "px"), null, ResampleMethod.BICUBIC);
  out = {path: psr_export(dA, ARGS.out, "png"), width: dA.width.as("px"), height: dA.height.as("px")};
} finally {
  if (dB) psr_close(dB);
  if (dA) psr_close(dA);
  app.activeDocument = src;
}
return out;
"""


def overlay(out_path, a, b, crop=None, max_px=1600, timeout=300):
    """Alignment overlay of two layers (names or ids): a in red, b in cyan."""
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    args = {"out": out_path, "a": a, "b": b, "crop": crop, "max_px": int(max_px)}
    res = ps_run.run(OVERLAY_JS.replace("%ARGS%", json.dumps(args)), timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError(res.get("error"))
    return res["result"]


def preview(out_path, max_px=1600, crop=None, layers_only=None, timeout=300):
    """Export a review image of the active document. Returns {"path", "width", "height", ...}."""
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    js = (PREVIEW_JS.replace("%OUT%", json.dumps(out_path)).replace("%MAX%", str(int(max_px)))
          .replace("%CROP%", json.dumps(crop)).replace("%ONLY%", json.dumps(layers_only)))
    res = ps_run.run(js, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError(res.get("error"))
    return res["result"]


def sheet(paths, out_path, labels=None, cols=None, tile=800):
    """Tile images into one contact sheet (needs Pillow). Returns the sheet path."""
    from PIL import Image, ImageDraw  # optional dependency, only for sheets

    ims = [Image.open(p).convert("RGB") for p in paths]
    cols = cols or min(3, len(ims))
    rows = (len(ims) + cols - 1) // cols
    th = max(int(im.height * tile / im.width) for im in ims)
    canvas = Image.new("RGB", (cols * tile, rows * (th + 28)), (24, 24, 24))
    draw = ImageDraw.Draw(canvas)
    for i, im in enumerate(ims):
        im = im.resize((tile, int(im.height * tile / im.width)))
        x, y = (i % cols) * tile, (i // cols) * (th + 28)
        canvas.paste(im, (x, y + 28))
        label = labels[i] if labels and i < len(labels) else os.path.basename(paths[i])
        draw.text((x + 6, y + 6), label, fill=(255, 220, 0))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    canvas.save(out_path, quality=88)
    return out_path


def before_after(before, after, out_path, tile=800):
    return sheet([before, after], out_path, labels=["before", "after"], cols=2, tile=tile)


def main(argv):
    if len(argv) >= 2 and argv[0] == "preview":
        max_px, crop = 1600, None
        if "--max" in argv:
            max_px = int(argv[argv.index("--max") + 1])
        if "--crop" in argv:
            crop = [int(v) for v in argv[argv.index("--crop") + 1].split(",")]
        print(json.dumps(preview(argv[1], max_px=max_px, crop=crop)))
        return 0
    if len(argv) >= 4 and argv[0] == "overlay":
        crop = None
        if "--crop" in argv:
            crop = [int(v) for v in argv[argv.index("--crop") + 1].split(",")]
        print(json.dumps(overlay(argv[1], argv[2], argv[3], crop=crop)))
        return 0
    if len(argv) >= 3 and argv[0] == "sheet":
        print(sheet(argv[2:], argv[1]))
        return 0
    print(__doc__)
    return 0 if argv[:1] in (["-h"], ["--help"]) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
