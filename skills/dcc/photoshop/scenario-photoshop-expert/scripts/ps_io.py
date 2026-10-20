"""
ps_io: move pixels between the open Photoshop document and files, for a Scenario round trip.
Capture an input (merged image, one layer, the selection as a mask), then land a result as a
named smart object fitted to an exact rectangle, masked by the selection, with provenance.

Library (each call is one ps_run job):
  import ps_io as IO
  IO.selection()                                  # {"bounds": [l, t, r, b]} or {"bounds": None}
  IO.export_region(out_png, bounds=None, pad=0, layer=None, max_px=None, punch_selection=False)
      # merged visible pixels (or one layer by name) inside bounds (default: selection bounds,
      # else canvas), sRGB 8-bit PNG. punch_selection=True makes the selected area transparent
      # (for models that edit where the input is transparent). Returns {"path", "bounds", "scale"}.
  IO.export_mask(out_png, bounds=None, pad=0, invert=False, max_px=None)
      # the selection as a grayscale PNG, white = selected (invert=True flips it), cropped to the
      # same bounds as export_region so both files line up pixel for pixel.
  IO.place(path, name, bounds=None, fit="exact", mask_selection=False, xmp=None,
           undo="Scenario: Place")
      # place a file as an embedded smart object, resize it into bounds ("exact" stretches,
      # "contain" fits inside, "cover" fills and overflows), optionally add a layer mask from
      # the current selection, write provenance XMP, all as ONE history state named `undo`.
      # An active selection is still active afterwards. Returns {"id", "name", "bounds",
      # "masked", "selection_kept", "kind"}.
  IO.replace(layer_name, path, undo="Scenario: Replace")
      # new contents; the placed box stays only when the file has the old contents' pixel size
  IO.layer_xmp(layer_name)                       # the layer's provenance dict, or {}
Shell:
  python3 ps_io.py selection | export OUT.png [--pad N] [--punch] | mask OUT.png [--pad N]
  python3 ps_io.py place FILE NAME [--bounds l,t,r,b] [--fit exact|contain|cover] [--mask]

Read-only captures leave pixels, layers and the active History state as they found them: the mask
capture stores the selection in a temporary channel, then steps History back to the state it
started from. Those temporary states still count: at the History limit each one drops one of the
user's oldest undo steps.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ps_run  # noqa: E402

XMP_NS = "https://scenario.com/ns/photoshop/1.0/"

COMMON_JS = r"""
function psr_bounds(doc, given, pad) {
  var b = given;
  if (!b) { try { var s = doc.selection.bounds; b = [s[0].as("px"), s[1].as("px"), s[2].as("px"),
                                                     s[3].as("px")]; } catch (e) { b = null; } }
  if (!b) b = [0, 0, doc.width.as("px"), doc.height.as("px")];
  pad = pad || 0;
  return [Math.max(0, Math.floor(b[0] - pad)), Math.max(0, Math.floor(b[1] - pad)),
          Math.min(doc.width.as("px"), Math.ceil(b[2] + pad)),
          Math.min(doc.height.as("px"), Math.ceil(b[3] + pad))];
}
function psr_to_srgb8(d) {
  if (String(d.bitsPerChannel) === "BitsPerChannelType.THIRTYTWO") d.bitsPerChannel = BitsPerChannelType.SIXTEEN;
  if (String(d.mode) !== "DocumentMode.RGB") d.changeMode(ChangeMode.RGB);
  try { d.convertProfile("sRGB IEC61966-2.1", Intent.RELATIVECOLORIMETRIC, true, false); }
  catch (e) { psr_log("sRGB conversion skipped: " + e); }
  if (String(d.bitsPerChannel) !== "BitsPerChannelType.EIGHT") d.bitsPerChannel = BitsPerChannelType.EIGHT;
}
function psr_fit_max(d, maxpx) {
  var w = d.width.as("px"), h = d.height.as("px");
  if (!maxpx || Math.max(w, h) <= maxpx) return 1;
  var s = maxpx / Math.max(w, h);
  d.resizeImage(UnitValue(Math.round(w * s), "px"), UnitValue(Math.round(h * s), "px"), null,
                ResampleMethod.BICUBICSHARPER);
  return s;
}
function psr_crop(d, b) {
  d.crop([UnitValue(b[0], "px"), UnitValue(b[1], "px"), UnitValue(b[2], "px"), UnitValue(b[3], "px")]);
}
"""

SELECTION_JS = r"""
if (app.documents.length === 0) throw new Error("no document open");
var d = app.activeDocument;
try { var s = d.selection.bounds;
      return {bounds: [s[0].as("px"), s[1].as("px"), s[2].as("px"), s[3].as("px")],
              canvas: [d.width.as("px"), d.height.as("px")]}; }
catch (e) { return {bounds: null, canvas: [d.width.as("px"), d.height.as("px")]}; }
"""

EXPORT_JS = COMMON_JS + r"""
if (app.documents.length === 0) throw new Error("no document open");
var src = app.activeDocument, out = %OUT%, given = %BOUNDS%, pad = %PAD%, only = %LAYER%,
    maxpx = %MAX%, punch = %PUNCH%;
var b = psr_bounds(src, given, pad);
var hs0 = src.activeHistoryState, ch = null;
if (punch) {
  try { src.selection.bounds; } catch (e) { throw new Error("punch_selection needs an active selection"); }
  ch = src.channels.add(); ch.name = "psr_sel"; src.selection.store(ch);
}
var dup = psr_dup(src, "psr_export", false), res = null;
try {
  // History calls need the source frontmost; psr_dup made the copy frontmost.
  if (ch) { app.activeDocument = src; ch.remove(); src.activeHistoryState = hs0; }
  app.activeDocument = dup;
  if (only) {
    var found = false;
    var walk = function (c) {
      for (var i = 0; i < c.layers.length; i++) {
        var l = c.layers[i];
        if (l.name === only) { found = true; l.visible = true; continue; }
        if (l.typename === "LayerSet") walk(l); else l.visible = false;
      }
    };
    walk(dup);
    if (!found) throw new Error("layer not found: " + only);
  }
  try { dup.mergeVisibleLayers(); } catch (e) { psr_log("merge skipped: " + e); }
  if (punch) {
    var dl = dup.activeLayer;
    if (dl.isBackgroundLayer) dl.isBackgroundLayer = false;
    dup.selection.load(dup.channels.getByName("psr_sel"));
    dup.selection.clear();
    dup.selection.deselect();
  }
  try { dup.channels.getByName("psr_sel").remove(); } catch (e) {}
  psr_crop(dup, b);
  psr_to_srgb8(dup);
  var s = psr_fit_max(dup, maxpx);
  psr_export(dup, out, "png");
  res = {path: out, bounds: b, scale: s, width: dup.width.as("px"), height: dup.height.as("px")};
} finally { psr_close(dup); app.activeDocument = src; }
return res;
"""

MASK_JS = COMMON_JS + r"""
if (app.documents.length === 0) throw new Error("no document open");
var src = app.activeDocument, out = %OUT%, given = %BOUNDS%, pad = %PAD%, invert = %INVERT%,
    maxpx = %MAX%;
try { src.selection.bounds; } catch (e) { throw new Error("no active selection to export as a mask"); }
var b = psr_bounds(src, given, pad);
var hs0 = src.activeHistoryState;
var ch = src.channels.add(); ch.name = "psr_sel"; src.selection.store(ch);
var dup = psr_dup(src, "psr_mask", true), res = null;
try {
  // History calls need the source frontmost; psr_dup made the copy frontmost.
  app.activeDocument = src; ch.remove(); src.activeHistoryState = hs0;
  app.activeDocument = dup;
  var black = new SolidColor(); black.rgb.red = black.rgb.green = black.rgb.blue = 0;
  var white = new SolidColor(); white.rgb.red = white.rgb.green = white.rgb.blue = 255;
  try { dup.flatten(); } catch (e) {}
  dup.selection.selectAll(); dup.selection.fill(invert ? white : black);
  dup.selection.load(dup.channels.getByName("psr_sel"));
  dup.selection.fill(invert ? black : white);
  dup.selection.deselect();
  try { dup.channels.getByName("psr_sel").remove(); } catch (e) {}
  psr_crop(dup, b);
  if (String(dup.bitsPerChannel) !== "BitsPerChannelType.EIGHT") dup.bitsPerChannel = BitsPerChannelType.EIGHT;
  dup.changeMode(ChangeMode.GRAYSCALE);
  var s = psr_fit_max(dup, maxpx);
  psr_export(dup, out, "png");
  res = {path: out, bounds: b, scale: s, width: dup.width.as("px"), height: dup.height.as("px"),
         polarity: invert ? "black = selected" : "white = selected"};
} finally { psr_close(dup); app.activeDocument = src; }
return res;
"""

PLACE_JS = COMMON_JS + r"""
if (app.documents.length === 0) throw new Error("no document open");
var doc = app.activeDocument, path = %PATH%, name = %NAME%, given = %BOUNDS%, fit = %FIT%,
    useMask = %MASK%, xmp = %XMP%;
var f = new File(path);
if (!f.exists) throw new Error("file not found: " + path);
var b = given ? given : [0, 0, doc.width.as("px"), doc.height.as("px")];
var ch = null, hasSel = true;
try { doc.selection.bounds; } catch (e) { hasSel = false; }
if (useMask && !hasSel) throw new Error("mask_selection needs an active selection");
if (hasSel) {
  // The selection is stored, then dropped while the layer is placed, resized and moved (a
  // transform with a live selection is not what this call measures), and comes back at the end:
  // the outside gate that follows a placement needs it.
  ch = doc.channels.add(); ch.name = "psr_place_sel"; doc.selection.store(ch);
  // channels.add() leaves only the new alpha channel active, which sends transforms to it.
  doc.activeChannels = doc.componentChannels;
  doc.selection.deselect();
}
var pd = new ActionDescriptor();
pd.putPath(charIDToTypeID("null"), f);
pd.putEnumerated(charIDToTypeID("FTcs"), charIDToTypeID("QCSt"), charIDToTypeID("Qcsa"));
var od = new ActionDescriptor();
od.putUnitDouble(charIDToTypeID("Hrzn"), charIDToTypeID("#Pxl"), 0);
od.putUnitDouble(charIDToTypeID("Vrtc"), charIDToTypeID("#Pxl"), 0);
pd.putObject(charIDToTypeID("Ofst"), charIDToTypeID("Ofst"), od);
executeAction(charIDToTypeID("Plc "), pd, DialogModes.NO);
var L = doc.activeLayer;
function box(layer) {
  var r = new ActionReference(); r.putIdentifier(charIDToTypeID("Lyr "), layer.id);
  var t = executeActionGet(r).getObjectValue(stringIDToTypeID("smartObjectMore"))
            .getList(stringIDToTypeID("transform"));
  var xs = [t.getDouble(0), t.getDouble(2), t.getDouble(4), t.getDouble(6)];
  var ys = [t.getDouble(1), t.getDouble(3), t.getDouble(5), t.getDouble(7)];
  return [Math.min.apply(null, xs), Math.min.apply(null, ys), Math.max.apply(null, xs), Math.max.apply(null, ys)];
}
var c = box(L), cw = c[2] - c[0], ch_ = c[3] - c[1], tw = b[2] - b[0], th = b[3] - b[1];
var sx = tw / cw, sy = th / ch_;
if (fit === "contain") { sx = sy = Math.min(tw / cw, th / ch_); }
else if (fit === "cover") { sx = sy = Math.max(tw / cw, th / ch_); }
if (Math.abs(sx - 1) > 1e-6 || Math.abs(sy - 1) > 1e-6)
  L.resize(sx * 100, sy * 100, AnchorPosition.TOPLEFT);
c = box(L);
var tx = b[0] + (tw - (c[2] - c[0])) / 2 - c[0], ty = b[1] + (th - (c[3] - c[1])) / 2 - c[1];
if (Math.abs(tx) > 1e-6 || Math.abs(ty) > 1e-6) L.translate(UnitValue(tx, "px"), UnitValue(ty, "px"));
L.name = name;
if (ch && useMask) {
  doc.selection.load(ch);
  var md = new ActionDescriptor();
  md.putClass(charIDToTypeID("Nw  "), charIDToTypeID("Chnl"));
  var mr = new ActionReference();
  mr.putEnumerated(charIDToTypeID("Chnl"), charIDToTypeID("Chnl"), charIDToTypeID("Msk "));
  md.putReference(charIDToTypeID("At  "), mr);
  md.putEnumerated(charIDToTypeID("Usng"), charIDToTypeID("UsrM"), charIDToTypeID("RvlS"));
  executeAction(charIDToTypeID("Mk  "), md, DialogModes.NO);
}
if (ch) {
  // Making a mask from the selection consumes it; reload it so the caller still has it.
  doc.selection.load(ch);
  ch.remove();
  doc.activeChannels = doc.componentChannels;
}
if (xmp) L.xmpMetadata.rawData = xmp;
var fb = box(L);
return {id: L.id, name: L.name, bounds: [Math.round(fb[0]), Math.round(fb[1]), Math.round(fb[2]), Math.round(fb[3])],
        masked: !!(ch && useMask), selection_kept: !!ch, kind: String(L.kind)};
"""

REPLACE_JS = r"""
if (app.documents.length === 0) throw new Error("no document open");
var doc = app.activeDocument, name = %NAME%, path = %PATH%, L = null;
function find(c) { for (var i = 0; i < c.layers.length && !L; i++) { var l = c.layers[i];
  if (l.name === name) L = l; else if (l.typename === "LayerSet") find(l); } }
find(doc);
if (!L) throw new Error("layer not found: " + name);
if (String(L.kind) !== "LayerKind.SMARTOBJECT") throw new Error("not a smart object: " + name);
doc.activeLayer = L;
var d = new ActionDescriptor(); d.putPath(charIDToTypeID("null"), new File(path));
executeAction(stringIDToTypeID("placedLayerReplaceContents"), d, DialogModes.NO);
// Replace Contents can rename the layer after the file; keep the name callers look it up by.
doc.activeLayer.name = name;
return {id: doc.activeLayer.id, name: doc.activeLayer.name};
"""

XMP_GET_JS = r"""
if (app.documents.length === 0) throw new Error("no document open");
var doc = app.activeDocument, name = %NAME%, L = null;
function find(c) { for (var i = 0; i < c.layers.length && !L; i++) { var l = c.layers[i];
  if (l.name === name) L = l; else if (l.typename === "LayerSet") find(l); } }
find(doc);
if (!L) throw new Error("layer not found: " + name);
var raw = ""; try { raw = L.xmpMetadata.rawData; } catch (e) { raw = ""; }
return raw;
"""


def _run(js, **kw):
    res = ps_run.run(js, timeout=kw.pop("timeout", 180), **kw)
    if not res.get("ok"):
        raise RuntimeError("%s (line %s)" % (res.get("error"), res.get("body_line")))
    return res["result"]


def _esc(v):
    return (str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


# One schema for Scenario layer metadata: camelCase keys, schema 1.
# Older snake_case names are accepted and renamed, so a layer reads the same whoever placed it.
XMP_ALIASES = {"asset_id": "assetId", "asset": "assetId", "job_id": "jobId", "model": "modelId",
               "model_id": "modelId", "date": "createdAt", "cost": "cuCharged",
               "cost_cu": "cuCharged"}


def _xmp_key(k):
    k = XMP_ALIASES.get(k, k)
    head, *rest = k.split("_")
    return head + "".join(w[:1].upper() + w[1:] for w in rest)


def provenance_xmp(fields):
    """XMP packet carrying Scenario provenance: assetId, jobId, modelId, prompt, cuCharged,
    createdAt and any other field, keys in camelCase (snake_case is renamed), plus schema 1."""
    out = {"schema": "1"}
    for k, v in fields.items():
        if v is not None and str(k).replace("_", "").isalnum():
            out[_xmp_key(str(k))] = v
    attrs = " ".join('scenario:%s="%s"' % (k, _esc(v)) for k, v in out.items())
    return ('<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about="" '
            'xmlns:scenario="%s" %s/></rdf:RDF></x:xmpmeta>' % (XMP_NS, attrs))


def parse_xmp(raw):
    import re
    import html

    return {k: html.unescape(v) for k, v in re.findall(r'scenario:(\w+)="([^"]*)"', raw or "")}


def selection():
    return _run(SELECTION_JS)


def export_region(out_png, bounds=None, pad=0, layer=None, max_px=None, punch_selection=False):
    out_png = os.path.abspath(out_png)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    js = (EXPORT_JS.replace("%OUT%", json.dumps(out_png)).replace("%BOUNDS%", json.dumps(bounds))
          .replace("%PAD%", str(int(pad))).replace("%LAYER%", json.dumps(layer))
          .replace("%MAX%", json.dumps(max_px)).replace("%PUNCH%", json.dumps(bool(punch_selection))))
    return _run(js)


def export_mask(out_png, bounds=None, pad=0, invert=False, max_px=None):
    out_png = os.path.abspath(out_png)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    js = (MASK_JS.replace("%OUT%", json.dumps(out_png)).replace("%BOUNDS%", json.dumps(bounds))
          .replace("%PAD%", str(int(pad))).replace("%INVERT%", json.dumps(bool(invert)))
          .replace("%MAX%", json.dumps(max_px)))
    return _run(js)


def place(path, name, bounds=None, fit="exact", mask_selection=False, xmp=None,
          undo="Scenario: Place"):
    if fit not in ("exact", "contain", "cover"):
        raise ValueError("fit must be exact, contain or cover")
    if isinstance(xmp, dict):
        xmp = provenance_xmp(xmp)
    js = (PLACE_JS.replace("%PATH%", json.dumps(os.path.abspath(path)))
          .replace("%NAME%", json.dumps(name)).replace("%BOUNDS%", json.dumps(bounds))
          .replace("%FIT%", json.dumps(fit)).replace("%MASK%", json.dumps(bool(mask_selection)))
          .replace("%XMP%", json.dumps(xmp)))
    return _run(js, undo=undo)


def replace(layer_name, path, undo="Scenario: Replace"):
    js = (REPLACE_JS.replace("%NAME%", json.dumps(layer_name))
          .replace("%PATH%", json.dumps(os.path.abspath(path))))
    return _run(js, undo=undo)


def layer_xmp(layer_name):
    return parse_xmp(_run(XMP_GET_JS.replace("%NAME%", json.dumps(layer_name))))


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        return cast(argv[argv.index(flag) + 1])
    return default


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd = argv[0]
    bounds = _opt(argv, "--bounds", lambda s: [int(v) for v in s.split(",")])
    if cmd == "selection":
        out = selection()
    elif cmd == "export" and len(argv) > 1:
        out = export_region(argv[1], bounds=bounds, pad=_opt(argv, "--pad", int, 0),
                            layer=_opt(argv, "--layer"), max_px=_opt(argv, "--max", int),
                            punch_selection="--punch" in argv)
    elif cmd == "mask" and len(argv) > 1:
        out = export_mask(argv[1], bounds=bounds, pad=_opt(argv, "--pad", int, 0),
                          invert="--invert" in argv, max_px=_opt(argv, "--max", int))
    elif cmd == "place" and len(argv) > 2:
        out = place(argv[1], argv[2], bounds=bounds, fit=_opt(argv, "--fit", str, "exact"),
                    mask_selection="--mask" in argv)
    else:
        print(__doc__)
        return 2
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
