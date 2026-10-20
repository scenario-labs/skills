"""
ps_upscale: the Photoshop side of upscaling and restoring with Scenario models. Prepare the
input a model accepts (aspect ratio padding, size cap, sRGB 8-bit), land results so they line
up with the original pixel for pixel, compare candidates the way upscale reviewers do (one named
layer per model over a rebuilt baseline, same 100% crops), and lock what must not change.
The model runs themselves are Scenario MCP steps the agent takes between these calls.

Library:
  import ps_upscale as U
  U.prepare_input(out_png, ratios=None, pad_color=(0, 0, 0), max_px=None, layer=None)
      # merged visible pixels (or one layer) padded to the nearest of `ratios` ("16:9", ...),
      # optionally capped at max_px. Returns {"path", "size", "padded", "pad": [l, t, r, b],
      # "ratio", "scale"}; keep it for place_result.
  U.place_result(path, name, prep=None, base=None, box=None)
      # place a model result as a smart object whose unpadded area covers the canvas exactly
      # (the padding falls outside the canvas). With base (a layer): "match", the difference
      # to it at a 256 px long side inside box, "matches" when its mean is under 6.
  U.build_stack(candidates, factor, name=None)
      # candidates = [{"path", "label"}]. A new document at source x factor: the original
      # resized with Preserve Details 2.0 as the baseline, then one layer per candidate named
      # "<label>, <N>x scale" with a white mask. Per candidate:
      #   size_ok, aspect_ok: the model's own output size against source x factor
      #   match: difference to the baseline at a 256 px long side; "matches" under 6. Catches
      #          a shift, a color cast, reframing; texture the model re-synthesized barely counts
      #   texture_change: the same difference at the source resolution, no threshold (real
      #          generative upscalers measured about 9 on a feather close-up, bicubic 3)
      #   detail: high-pass energy, and detail_vs_base as a ratio to the baseline's
  U.crops(out_dir, boxes=None, size=256)
      # the same 100% crops of every layer of the stack, plus one grid PNG: one labeled row
      # per layer, top layer first
  U.lock(layer, mode="color", base=None)
      # blend the result in Color (keep the original's tones, take its color) or Luminosity
      # (keep the original's color, take its detail); with base: difference before and after
  U.align(layer, base, name=None)
      # Auto-Align (content, auto projection) of a result onto the base layer, kept only when
      # ps_gates.structure drops by 10% or more; otherwise History steps back and the result
      # stays as it was ("kept": false). Auto-Align misreads a damaged base: it pushed an
      # aligned restore 7 px off (structure 11.3 to 19.7) and fixed a drifted one (22.7 to
      # 12.8). Runs in a temporary document, so the user's Background stays a Background.
      # The aligned copy lands as "<layer>, aligned" above the result, which is hidden.
      # Returns structure_before/after, kept, moved [dx, dy] (center, px), scale [sx, sy],
      # uncovered [l, t, r, b] (canvas px the aligned layer leaves bare).
  U.region_blend(layer, feather=8)
      # the current selection, feathered, becomes the layer's mask (replacing any old mask): one
      # candidate for the face, another for the rest. Returns the selection bounds and their
      # share of the canvas ("box_share").
Shell:
  python3 ps_upscale.py prep OUT.png [--ratios 1:1,16:9] [--max 2048]
      | place FILE NAME [--prep prep.json] [--base LAYER]
      | stack FACTOR LABEL=FILE [LABEL=FILE ...] | crops OUT_DIR [--size 256]
      | lock LAYER [--mode color|luminosity] [--base LAYER]
      | align LAYER BASE | region LAYER [--feather N]

Sources: upscale and restoration videos summarized in the skill (candidate stack with the
model name and factor in the layer name, a rebuilt Preserve Details 2.0 baseline, 100% crops,
Difference to check alignment, Color blend to keep the original's tones, pad then crop back).
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scenario-photoshop-expert", "scripts"))
import ps_gates as G  # noqa: E402
import ps_run  # noqa: E402

# Authoring-time calibration on a detail-dense 512 px photo, worst-channel mean against a Preserve
# Details 2.0 baseline at a 256 px long side: two real 2x upscalers 4.9, bicubic 0.5, blurred 7.1,
# an 8 px shift at 2x 16.8, a 45-level color cast 38.5. At source size the real ones score 9.4 to 9.5,
# three times bicubic: generative upscalers re-synthesize texture, so identity is judged small.
MATCH_SIZE = 256
MATCH_MEAN = 6.0

HELPERS_JS = r"""
var ARGS = %ARGS%;
function pu_c(s) { return charIDToTypeID(s); }
function pu_s(s) { return stringIDToTypeID(s); }
function pu_find(c, key) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if ((typeof key === "number" && l.id === key) || (typeof key === "string" && l.name === key)) return l;
    if (l.typename === "LayerSet") { var r = pu_find(l, key); if (r) return r; }
  }
  return null;
}
function pu_srgb8(d) {
  if (d.mode !== DocumentMode.RGB) d.changeMode(ChangeMode.RGB);
  if (d.bitsPerChannel !== BitsPerChannelType.EIGHT) d.bitsPerChannel = BitsPerChannelType.EIGHT;
  try { d.convertProfile("sRGB IEC61966-2.1", Intent.RELATIVECOLORIMETRIC, true, false); } catch (e) {}
}
// Image Size by Action Manager: "deepUpscale" is likely Preserve Details 2.0 (its output differs
// from bicubic, nearest neighbor and an unknown name; not proven). Photoshop silently accepts an
// unknown interpolation name, so a typo here would not fail: keep the string exact.
function pu_resize(d, w, h, method) {
  var desc = new ActionDescriptor();
  desc.putUnitDouble(pu_c("Wdth"), pu_c("#Pxl"), w);
  desc.putUnitDouble(pu_c("Hght"), pu_c("#Pxl"), h);
  desc.putBoolean(pu_c("CnsP"), false);
  desc.putEnumerated(pu_c("Intr"), pu_c("Intp"), pu_s(method));
  executeAction(pu_c("ImgS"), desc, DialogModes.NO);
}
function pu_white_mask() {
  var desc = new ActionDescriptor(); desc.putClass(pu_c("Nw  "), pu_c("Chnl"));
  var ref = new ActionReference(); ref.putEnumerated(pu_c("Chnl"), pu_c("Chnl"), pu_c("Msk "));
  desc.putReference(pu_c("At  "), ref);
  desc.putEnumerated(pu_c("Usng"), pu_c("UsrM"), pu_c("RvlA"));
  executeAction(pu_c("Mk  "), desc, DialogModes.NO);
}
function pu_so_size(l) {
  var r = new ActionReference(); r.putIdentifier(pu_c("Lyr "), l.id);
  var s = executeActionGet(r).getObjectValue(pu_s("smartObjectMore")).getObjectValue(pu_s("size"));
  return [s.getDouble(pu_s("width")), s.getDouble(pu_s("height"))];
}
function pu_place_exact(path, b) {
  var pd = new ActionDescriptor(); pd.putPath(pu_c("null"), new File(path));
  pd.putEnumerated(pu_c("FTcs"), pu_c("QCSt"), pu_c("Qcsa"));
  executeAction(pu_c("Plc "), pd, DialogModes.NO);
  var L = app.activeDocument.activeLayer;
  var r = new ActionReference(); r.putIdentifier(pu_c("Lyr "), L.id);
  var t = executeActionGet(r).getObjectValue(pu_s("smartObjectMore")).getList(pu_s("transform"));
  var x0 = Math.min(t.getDouble(0), t.getDouble(6)), y0 = Math.min(t.getDouble(1), t.getDouble(3));
  var x1 = Math.max(t.getDouble(2), t.getDouble(4)), y1 = Math.max(t.getDouble(5), t.getDouble(7));
  L.resize((b[2] - b[0]) / (x1 - x0) * 100, (b[3] - b[1]) / (y1 - y0) * 100, AnchorPosition.TOPLEFT);
  t = executeActionGet(r).getObjectValue(pu_s("smartObjectMore")).getList(pu_s("transform"));
  L.translate(UnitValue(b[0] - Math.min(t.getDouble(0), t.getDouble(6)), "px"),
              UnitValue(b[1] - Math.min(t.getDouble(1), t.getDouble(3)), "px"));
  return L;
}
if (app.documents.length === 0) throw new Error("no document open");
var d = app.activeDocument;
"""

PREP_JS = r"""
var dup = psr_dup(d, "scenario input", false);
app.activeDocument = dup;
if (ARGS.layer !== null) {
  var keepL = pu_find(dup, ARGS.layer);
  if (!keepL) throw new Error("layer not found: " + ARGS.layer);
  var hide = function (c) {
    var hit = false;
    for (var i = 0; i < c.layers.length; i++) {
      var x = c.layers[i];
      if (x.id === keepL.id) { x.visible = true; hit = true; }
      else if (x.typename === "LayerSet" && hide(x)) { x.visible = true; hit = true; }
      else x.visible = false;
    }
    return hit;
  };
  hide(dup);
}
dup.flatten();
pu_srgb8(dup);
var w = dup.width.as("px"), h = dup.height.as("px"), best = null;
for (var i = 0; i < ARGS.ratios.length; i++) {
  var p = ARGS.ratios[i].split(":"), r = Number(p[0]) / Number(p[1]);
  var cost = Math.abs(Math.log((w / h) / r));
  if (best === null || cost < best.cost) best = {r: r, name: ARGS.ratios[i], cost: cost};
}
var W = w, H = h;
if (best && best.cost > 1e-6) { if (w / h < best.r) W = Math.round(h * best.r); else H = Math.round(w / best.r); }
var l = Math.floor((W - w) / 2), t = Math.floor((H - h) / 2);
var bg = app.backgroundColor, c = new SolidColor();
c.rgb.red = ARGS.pad_color[0]; c.rgb.green = ARGS.pad_color[1]; c.rgb.blue = ARGS.pad_color[2];
app.backgroundColor = c;
try {
  // Two anchored steps place the source at exactly (l, t); one centered step would round
  // odd padding on its own.
  if (l > 0 || t > 0) dup.resizeCanvas(UnitValue(w + l, "px"), UnitValue(h + t, "px"), AnchorPosition.BOTTOMRIGHT);
  if (W > w + l || H > h + t) dup.resizeCanvas(UnitValue(W, "px"), UnitValue(H, "px"), AnchorPosition.TOPLEFT);
} finally { app.backgroundColor = bg; }
var s = 1;
if (ARGS.max_px && Math.max(W, H) > ARGS.max_px) {
  s = ARGS.max_px / Math.max(W, H);
  pu_resize(dup, Math.round(W * s), Math.round(H * s), "bicubicSharper");
}
var out = psr_export(dup, ARGS.out, "png");
var ow = dup.width.as("px"), oh = dup.height.as("px");
psr_close(dup);
app.activeDocument = d;
return {path: out, size: [w, h], padded: [W, H], pad: [l, t, W - w - l, H - h - t],
        ratio: best ? best.name : null, scale: s, output: [ow, oh], doc: d.name};
"""

PLACE_JS = r"""
var L = pu_place_exact(ARGS.path, ARGS.bounds);
L.name = ARGS.name;
return {id: L.id, name: L.name, content_size: pu_so_size(L), bounds: ARGS.bounds};
"""

STACK_JS = r"""
var W = Math.round(d.width.as("px") * ARGS.factor), H = Math.round(d.height.as("px") * ARGS.factor);
var s = psr_dup(d, ARGS.name, true);
app.activeDocument = s;
pu_srgb8(s);
pu_resize(s, W, H, "deepUpscale");
var base = s.activeLayer;
if (base.isBackgroundLayer) base.isBackgroundLayer = false;
base.name = ARGS.base_name;
var made = [];
for (var i = ARGS.candidates.length - 1; i >= 0; i--) {
  var cnd = ARGS.candidates[i];
  s.activeLayer = s.layers[0];
  var L = pu_place_exact(cnd.path, [0, 0, W, H]);
  L.name = cnd.label + ", " + ARGS.factor_label + "x scale";
  pu_white_mask();
  made.unshift({id: L.id, name: L.name, content_size: pu_so_size(L)});
}
return {doc: s.name, size: [W, H], base: base.name, layers: made};
"""

CROPS_JS = r"""
var names = [], vis = [];
for (var i = 0; i < d.layers.length; i++) { names.push(d.layers[i].name); vis.push(d.layers[i].visible); }
var W = d.width.as("px"), H = d.height.as("px"), S = ARGS.size, boxes = ARGS.boxes, files = [];
if (!boxes) {
  var pts = [[W / 2, H / 2], [W / 3, H / 3], [2 * W / 3, 2 * H / 3]];
  boxes = [];
  for (var p = 0; p < pts.length; p++) {
    var x0 = Math.max(0, Math.min(W - S, Math.round(pts[p][0] - S / 2))), y0 = Math.max(0, Math.min(H - S, Math.round(pts[p][1] - S / 2)));
    boxes.push([x0, y0, Math.min(W, x0 + S), Math.min(H, y0 + S)]);
  }
}
try {
  for (var li = 0; li < d.layers.length; li++) {
    for (var k = 0; k < d.layers.length; k++) d.layers[k].visible = (k === li);
    for (var b = 0; b < boxes.length; b++) {
      var c = psr_dup(d, "crop", true), bx = boxes[b];
      c.crop([UnitValue(bx[0], "px"), UnitValue(bx[1], "px"), UnitValue(bx[2], "px"), UnitValue(bx[3], "px")]);
      var f = ARGS.out_dir + "/" + String(li + 1) + " " + names[li].replace(/[\\\/:*?"<>|]/g, "_") + " box" + (b + 1) + ".png";
      files.push(psr_export(c, f, "png"));
      psr_close(c);
      app.activeDocument = d;
    }
  }
} finally {
  for (var v = 0; v < d.layers.length; v++) d.layers[v].visible = vis[v];
}
var cw = 0, ch = 0;
for (var q = 0; q < boxes.length; q++) { cw = Math.max(cw, boxes[q][2] - boxes[q][0]); ch = Math.max(ch, boxes[q][3] - boxes[q][1]); }
var gap = 8, lab = 22, gw = boxes.length * cw + (boxes.length + 1) * gap;
var gh = names.length * (ch + lab) + (names.length + 1) * gap;
var g = psr_new_doc(gw, gh, "crops grid", {fill: "white"});
var ink = new SolidColor(); ink.rgb.red = 0; ink.rgb.green = 0; ink.rgb.blue = 0;
for (var rw = 0; rw < names.length; rw++) {
  var t = g.artLayers.add(); t.kind = LayerKind.TEXT;
  var ti = t.textItem;
  try { ti.font = "ArialMT"; } catch (e) {}
  ti.size = new UnitValue(13, "pt"); ti.color = ink; ti.contents = names[rw];
  ti.position = [UnitValue(gap, "px"), UnitValue(gap + rw * (ch + lab + gap) + 15, "px")];
}
for (var n = 0; n < files.length; n++) {
  var row = Math.floor(n / boxes.length), col = n % boxes.length;
  var bb = boxes[col], x = gap + col * (cw + gap), y = gap + row * (ch + lab + gap) + lab;
  pu_place_exact(files[n], [x, y, x + bb[2] - bb[0], y + bb[3] - bb[1]]);
}
var grid = psr_export(g, ARGS.out_dir + "/crops grid.png", "png");
psr_close(g);
app.activeDocument = d;
return {rows: names, boxes: boxes, files: files, grid: grid};
"""

LOCK_JS = r"""
var L = pu_find(d, ARGS.layer);
if (!L) throw new Error("layer not found: " + ARGS.layer);
// The layer blend constant for Color is COLORBLEND: reading BlendMode.COLOR throws "Invalid
// enumeration value" on 27.11 (COLOR belongs to ColorBlendMode, the enum for fills).
L.blendMode = ARGS.mode === "luminosity" ? BlendMode.LUMINOSITY : BlendMode.COLORBLEND;
return {id: L.id, blend: String(L.blendMode)};
"""


# Auto-Align moves the unlocked layer onto the locked one. It converts a Background it touches
# into "Layer 0" and silently does nothing on a smart object, so it runs on rasterized copies
# in a temporary document of the same size; a layer duplicated back keeps its position.
ALIGN_JS = r"""
function pu_box(L) { var b = L.bounds; return [b[0].as("px"), b[1].as("px"), b[2].as("px"), b[3].as("px")]; }
function pu_select(name, add) {
  var r = new ActionReference(); r.putName(pu_c("Lyr "), name);
  var desc = new ActionDescriptor(); desc.putReference(pu_c("null"), r);
  if (add) desc.putEnumerated(pu_s("selectionModifier"), pu_s("selectionModifierType"), pu_s("addToSelection"));
  desc.putBoolean(pu_c("MkVs"), false);
  executeAction(pu_c("slct"), desc, DialogModes.NO);
}
var L = pu_find(d, ARGS.layer);
if (!L) throw new Error("layer not found: " + ARGS.layer);
var W = d.width.as("px"), H = d.height.as("px");
var B = pu_find(d, ARGS.base);
if (!B) throw new Error("base layer not found: " + ARGS.base);
var t = psr_new_doc(W, H, "pu_align", {fill: "transparent"});
app.activeDocument = d;
var tb = B.duplicate(t, ElementPlacement.PLACEATBEGINNING);
var tl = L.duplicate(t, ElementPlacement.PLACEATBEGINNING);
app.activeDocument = t;
if (tb.isBackgroundLayer) tb.isBackgroundLayer = false;
tb.name = "pu_base"; tl.name = "pu_cand"; tl.visible = true; tb.visible = true;
tb.positionLocked = true;
t.activeLayer = tl;
try { tl.rasterize(RasterizeType.ENTIRELAYER); } catch (e) {}
var before = pu_box(tl);
pu_select("pu_base", false); pu_select("pu_cand", true);
var a = new ActionDescriptor(), r = new ActionReference();
r.putEnumerated(pu_c("Lyr "), pu_c("Ordn"), pu_c("Trgt"));
a.putReference(pu_c("null"), r);
a.putEnumerated(pu_c("Usng"), pu_c("ADSt"), pu_s("ADSContent"));
// charID "Auto"; the string ID "auto" is accepted and aligns nothing.
a.putEnumerated(pu_c("Aply"), pu_s("projection"), pu_c("Auto"));
a.putBoolean(pu_s("vignette"), false); a.putBoolean(pu_s("radialDistort"), false);
var err = null;
try { executeAction(pu_c("Algn"), a, DialogModes.NO); } catch (e) { err = String(e); }
tl = t.layers.getByName("pu_cand");
var after = pu_box(tl), out = {before: before, after: after, error: err};
if (!err) {
  // Both layers are still targeted after the align, and setting activeLayer keeps both:
  // duplicate would copy the pair.
  pu_select("pu_cand", false);
  var back = tl.duplicate(L, ElementPlacement.PLACEBEFORE);
  app.activeDocument = d;
  back.name = ARGS.name; L.visible = false;
  out.name = back.name; out.id = back.id;
}
psr_close(t);
app.activeDocument = d;
out.canvas = [W, H];
return out;
"""

REGION_JS = r"""
var L = pu_find(d, ARGS.layer);
if (!L) throw new Error("layer not found: " + ARGS.layer);
var sb;
try { sb = d.selection.bounds; } catch (e) { throw new Error("select the region first"); }
if (ARGS.feather > 0) d.selection.feather(UnitValue(ARGS.feather, "px"));
d.activeLayer = L;
try {
  var dr = new ActionReference(); dr.putEnumerated(pu_c("Chnl"), pu_c("Chnl"), pu_c("Msk "));
  var dd = new ActionDescriptor(); dd.putReference(pu_c("null"), dr);
  executeAction(pu_c("Dlt "), dd, DialogModes.NO);
} catch (e) {}
var desc = new ActionDescriptor(); desc.putClass(pu_c("Nw  "), pu_c("Chnl"));
var ref = new ActionReference(); ref.putEnumerated(pu_c("Chnl"), pu_c("Chnl"), pu_c("Msk "));
desc.putReference(pu_c("At  "), ref);
desc.putEnumerated(pu_c("Usng"), pu_c("UsrM"), pu_c("RvlS"));
executeAction(pu_c("Mk  "), desc, DialogModes.NO);
var W = d.width.as("px"), H = d.height.as("px");
var bw = sb[2].as("px") - sb[0].as("px"), bh = sb[3].as("px") - sb[1].as("px");
return {id: L.id, name: L.name, selection: [sb[0].as("px"), sb[1].as("px"), sb[2].as("px"), sb[3].as("px")],
        box_share: Math.round(bw * bh / (W * H) * 1000) / 1000};
"""


def _run(js, args, undo=None, timeout=300):
    body = HELPERS_JS.replace("%ARGS%", json.dumps(args)) + js
    res = ps_run.run(body, undo=undo, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError("%s (line %s)" % (res.get("error"), res.get("line")))
    return res["result"]


def _key(v):
    return int(v) if isinstance(v, str) and v.isdigit() else v


def _coarse(w, h):
    k = min(1.0, MATCH_SIZE / float(max(w, h)))
    return [max(1, int(round(w * k))), max(1, int(round(h * k)))]


def _match(layer, base, w, h, box=None):
    """At a 256 px long side, texture an upscaler re-synthesizes weighs little, while a shift
    past about long side / 256 px, a color cast or reframing still shows."""
    size = _coarse(w, h)
    d = G.diff(layer, _key(base), region=box, size=size)["worst"]
    return {"mean": d["mean"], "p99": d["p99"], "matches": d["mean"] < MATCH_MEAN, "at": size}


def prepare_input(out_png, ratios=None, pad_color=(0, 0, 0), max_px=None, layer=None):
    out_png = os.path.abspath(out_png)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    return _run(PREP_JS, {"out": out_png, "ratios": list(ratios or []), "pad_color": list(pad_color),
                          "max_px": max_px, "layer": _key(layer) if layer is not None else None})


def place_result(path, name, prep=None, base=None, box=None, undo="Scenario: Place result"):
    """The result covers the padded canvas, so its unpadded area lands on the canvas exactly."""
    doc = ps_run.run("var d = app.activeDocument; return [d.width.as('px'), d.height.as('px')];")
    if not doc.get("ok"):
        raise RuntimeError(doc.get("error"))
    W, H = doc["result"]
    bounds = [0, 0, W, H]
    if prep:
        w, h = prep["size"]
        l, t, r, b = prep["pad"]
        kx, ky = W / float(w), H / float(h)
        bounds = [-l * kx, -t * ky, (w + r) * kx, (h + b) * ky]
    out = _run(PLACE_JS, {"path": os.path.abspath(path), "name": name, "bounds": bounds}, undo=undo)
    if base is not None:
        out["match"] = _match(name, base, W, H, box)
    return out


def build_stack(candidates, factor, name=None, base_name=None):
    label = ("%g" % factor)
    res = ps_run.run("return app.activeDocument.name;")
    if not res.get("ok"):
        raise RuntimeError(res.get("error"))
    doc = res["result"]
    args = {"candidates": [{"path": os.path.abspath(c["path"]), "label": c["label"]} for c in candidates],
            "factor": float(factor), "factor_label": label,
            "name": name or "%s, %sx candidates" % (os.path.splitext(doc)[0], label),
            "base_name": base_name or "Original, Preserve Details 2.0, %sx scale" % label}
    out = _run(STACK_JS, args)
    W, H = out["size"]
    src = [int(round(W / float(factor))), int(round(H / float(factor)))]
    base_tex = G.texture(layer=out["base"])["energy"]
    out["base_detail"] = base_tex
    for L in out["layers"]:
        nw, nh = L["content_size"]
        L["size_ok"] = abs(nw - W) <= 1 and abs(nh - H) <= 1
        L["aspect_ok"] = abs(nw / float(nh) - W / float(H)) <= 1.0 / min(W, H) * 2
        L["match"] = _match(L["name"], out["base"], W, H)
        L["texture_change"] = G.diff(L["name"], out["base"], size=src)["worst"]["mean"]
        L["detail"] = G.texture(layer=L["name"])["energy"]
        L["detail_vs_base"] = round(L["detail"] / base_tex, 2) if base_tex else None
    return out


def crops(out_dir, boxes=None, size=256):
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    return _run(CROPS_JS, {"out_dir": out_dir, "boxes": boxes, "size": int(size)})


def lock(layer, mode="color", base=None, undo="Scenario: Fidelity lock"):
    if mode not in ("color", "luminosity"):
        raise ValueError("mode must be color or luminosity")
    before = G.diff(None, _key(base)) if base is not None else None
    out = _run(LOCK_JS, {"layer": _key(layer), "mode": mode}, undo=undo)
    if base is not None:
        out["before"] = before
        out["after"] = G.diff(None, _key(base))
    return out


# Stepping History back removes the aligned copy but not a visibility change (Photoshop does not
# record those by default), so the result is shown again by hand.
STEP_BACK_JS = r"""
var h = d.historyStates, a = d.activeHistoryState, i = -1;
for (var q = h.length - 1; q >= 0; q--) if (h[q] == a) { i = q; break; }
if (a.name !== ARGS.undo || i < 1) throw new Error("active History state is not " + ARGS.undo);
d.activeHistoryState = h[i - 1];
var L = pu_find(d, ARGS.layer);
if (L) L.visible = ARGS.visible;
return d.activeHistoryState.name;
"""


def align(layer, base, name=None, gain=0.9, undo="Scenario: Align result"):
    name = name or "%s, aligned" % layer
    before = G.structure(_key(layer), _key(base))["score"]
    vis = _run("var L = pu_find(d, ARGS.layer); return L ? L.visible : true;", {"layer": _key(layer)})
    out = _run(ALIGN_JS, {"layer": _key(layer), "base": _key(base), "name": name}, undo=undo)
    if out.get("error"):
        raise RuntimeError("Auto-Align failed: " + out["error"])
    after = G.structure(out["id"], _key(base))["score"]
    out["structure_before"], out["structure_after"] = before, after
    out["kept"] = after <= before * gain
    if not out["kept"]:
        _run(STEP_BACK_JS, {"undo": undo, "layer": _key(layer), "visible": bool(vis)})
    b0, b1 = out["before"], out["after"]
    W, H = out["canvas"]
    out["moved"] = [round((b1[0] + b1[2] - b0[0] - b0[2]) / 2.0, 1), round((b1[1] + b1[3] - b0[1] - b0[3]) / 2.0, 1)]
    out["scale"] = [round((b1[2] - b1[0]) / float(b0[2] - b0[0]), 4), round((b1[3] - b1[1]) / float(b0[3] - b0[1]), 4)]
    out["uncovered"] = [max(0, b1[0]), max(0, b1[1]), max(0, W - b1[2]), max(0, H - b1[3])]
    return out


def region_blend(layer, feather=8, undo="Scenario: Region blend"):
    return _run(REGION_JS, {"layer": _key(layer), "feather": float(feather)}, undo=undo)


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        i = argv.index(flag)
        return cast(argv[i + 1])
    return default


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    try:
        if cmd == "prep":
            r = _opt(argv, "--ratios")
            out = prepare_input(argv[1], r.split(",") if r else None, max_px=_opt(argv, "--max", int))
        elif cmd == "place":
            p = _opt(argv, "--prep")
            prep = json.load(open(p)) if p else None
            out = place_result(argv[1], argv[2], prep, _opt(argv, "--base"))
        elif cmd == "stack":
            cands = []
            for a in argv[2:]:
                if "=" not in a:
                    continue
                lab, path = a.split("=", 1)
                cands.append({"label": lab, "path": path})
            out = build_stack(cands, float(argv[1]))
        elif cmd == "crops":
            out = crops(argv[1], size=_opt(argv, "--size", int, 256))
        elif cmd == "lock":
            out = lock(argv[1], _opt(argv, "--mode", str, "color"), _opt(argv, "--base"))
        elif cmd == "align":
            out = align(argv[1], argv[2])
        elif cmd == "region":
            out = region_blend(argv[1], _opt(argv, "--feather", float, 8))
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
