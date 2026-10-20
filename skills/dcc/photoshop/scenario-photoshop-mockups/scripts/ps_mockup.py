"""
ps_mockup: put a flat design (a Scenario result, a logo, a label) onto a product photo the way
mockup builders do it by hand: a placeholder smart object fitted to four corners or wrapped
around a cylinder, the design swapped in at the placeholder's proportions, lighting rebuilt from
the product's own pixels, creases through Displace, and a batch export per design or per
colorway. Every edit is one named History state; every fit reports where the corners landed.

Library:
  import ps_mockup as M
  M.placeholder(quad, name="Place Design Here", size=None, fill=60, mask_selection=True)
      # quad = [[x,y] TL, TR, BR, BL] in document px. A solid smart object inside group
      # "Mockup: <name>", warped onto the quad, Fill lowered so the product shows through while
      # fitting. `size` = the design's print size (default: the quad's mean edge lengths); it sets
      # the proportions replace_design crops to and rides in the layer's XMP. With a selection
      # active, the selection becomes the GROUP mask (the printable area).
  M.fit_quad(layer, quad)        # perspective warp of a smart object onto four corners
  M.fit_cylinder(layer, quad, bulge, top_bulge=None, angle=120)
      # a label around a can, bottle or mug: corners as in fit_quad, the bottom edge's middle
      # `bulge` px below the line between its corners (top edge: `top_bulge`, default the same),
      # `angle` = the label's visible arc in degrees (columns narrow toward the sides)
  M.corners(layer)               # where the corners are now: [[x,y] TL, TR, BR, BL]
  M.replace_design(layer, path, fit="cover")
      # the file cropped ("cover"), padded ("contain") or stretched ("exact") to the print
      # proportions, then swapped in at the content size: the warp is kept, Fill goes back to 100
  M.lighting(layer, product, shade=85, light=50)
      # two copies of the product pixels clipped above the design: Multiply keeps only what is
      # darker than the product's mean under the design, Screen only what is brighter
  M.displace(layer, product, scale=8, blur=None, map_dir=None)
      # displacement map from the product pixels under the design, applied as a Smart Filter.
      # The filter re-reads the map file on every re-render, so the map is kept: in
      # "<document> maps/" next to a saved document, else Documents/Scenario Photoshop/
      # displace maps/. Returns its path; never delete it while the filter exists.
  M.batch(layer, designs, out_dir, fit="cover")
      # one merged PNG per design file; pixels, layers and the active History state end as they
      # started (at the History limit the temporary states drop the oldest undo steps)
  M.colorways(product, colors, out_dir, match=True, check=True)
      # one merged PNG per product color: a Solid Color fill in Color mode above `product`,
      # masked by the active selection, else clipped to the product layer; colors =
      # {"name": (r, g, b), "#rrggbb" or {"lab": [L, a, b]}}; pixels, layers and the active
      # History state end as they started (at the History limit the temporary states drop the
      # oldest undo steps). match: a Curves under the fill brings the product's mid-tones to
      # the swatch's luminance first (Color mode alone keeps the product's, so navy on white
      # came out pale blue); a swatch at or past a light blank's lit fabric (white on a white
      # blank) gets no Curves: the blank stands. check: per colorway, the product's mid-tones
      # against the swatch ("delta_e", CIE76, against the Lab value when one is given),
      # "folds" (correlation of the luminance pattern: 1 = folds in the same places, blind to
      # their depth), "spread" (fold depth in levels, after over before), "contrast" (fold
      # depth relative to the mid-tones, (p90 - p10) / p50, before and after), "flat" (the
      # contrast after under 0.15 and under half the contrast before: the folds are gone, start
      # from a lighter blank) and "blank" (no Curves ran because the blank stands; delta_e then
      # measures the blank's own shading). match and check need Pillow.
  M.tone_curve(tones, rgb), M.is_blank(tones, rgb), M.swatch_check(base, result, rgb, lab=None),
  M.delta_e(a, b), M.lab_to_rgb(lab)
      # the pure math behind match and check
Every fit wraps the object once more (Convert to Smart Object) at the target's size: fit before
displace (Smart Filters refuse a fit), and keep layer masks on the group.
Shell:
  python3 ps_mockup.py placeholder X,Y,X,Y,X,Y,X,Y [--name N] [--size W,H] [--fill 60]
      | fit LAYER X,Y,X,Y,X,Y,X,Y | cylinder LAYER X,Y,X,Y,X,Y,X,Y --bulge N [--top N] [--angle 120]
      | corners LAYER | replace LAYER FILE [--fit cover]
      | light LAYER PRODUCT [--shade 85] [--light 50] | displace LAYER PRODUCT [--scale 8]
      | batch LAYER OUT_DIR FILE [FILE ...] | colorways PRODUCT OUT_DIR NAME=#RRGGBB [...]

Sources: mockup videos summarized in the skill (placeholder smart object first, lighting from
the product's own pixels, group mask for the printable area, Displace as a Smart Filter).
"""

import json
import math
import os
import struct
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scenario-photoshop-expert", "scripts"))
import ps_gates as G  # noqa: E402
import ps_io as IO  # noqa: E402
import ps_run  # noqa: E402

HELPERS_JS = r"""
var ARGS = %ARGS%;
function pm_c(s) { return charIDToTypeID(s); }
function pm_s(s) { return stringIDToTypeID(s); }
function pm_find(c, key) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if ((typeof key === "number" && l.id === key) || (typeof key === "string" && l.name === key)) return l;
    if (l.typename === "LayerSet") { var r = pm_find(l, key); if (r) return r; }
  }
  return null;
}
function pm_layer(key) {
  var l = pm_find(app.activeDocument, key);
  if (!l) throw new Error("layer not found: " + key);
  if (l.typename === "LayerSet") throw new Error("needs a layer, not a group: " + key);
  app.activeDocument.activeLayer = l;
  return l;
}
function pm_so(key) {
  var l = pm_layer(key);
  if (String(l.kind) !== "LayerKind.SMARTOBJECT") throw new Error("not a smart object: " + key);
  return l;
}
function pm_more(l) {
  var r = new ActionReference(); r.putIdentifier(pm_c("Lyr "), l.id);
  return executeActionGet(r).getObjectValue(pm_s("smartObjectMore"));
}
function pm_size(l) {
  var s = pm_more(l).getObjectValue(pm_s("size"));
  return [s.getDouble(pm_s("width")), s.getDouble(pm_s("height"))];
}
// Box of the smart object's current transform. layer.bounds would give the opaque pixels only.
function pm_box(l) {
  var t = pm_more(l).getList(pm_s("transform")), xs = [], ys = [];
  for (var i = 0; i < 8; i += 2) { xs.push(t.getDouble(i)); ys.push(t.getDouble(i + 1)); }
  return [Math.min.apply(null, xs), Math.min.apply(null, ys), Math.max.apply(null, xs), Math.max.apply(null, ys)];
}
function pm_warp_style(m) {
  try { return typeIDToStringID(m.getObjectValue(pm_s("warp")).getEnumerationValue(pm_s("warpStyle"))); }
  catch (e) { return "warpNone"; }
}
function pm_mesh(m) {
  var w = m.getObjectValue(pm_s("warp")), pts = w.getObjectValue(pm_s("customEnvelopeWarp")).getList(pm_s("meshPoints")), o = [];
  for (var i = 0; i < pts.count; i++) {
    var p = pts.getObjectValue(i);
    o.push([p.getUnitDoubleValue(pm_s("horizontal")), p.getUnitDoubleValue(pm_s("vertical"))]);
  }
  return o;
}
function pm_warp_bounds(m) {
  try {
    var b = m.getObjectValue(pm_s("warp")).getObjectValue(pm_s("bounds"));
    return [b.getDouble(pm_s("left")), b.getDouble(pm_s("top")), b.getDouble(pm_s("right")), b.getDouble(pm_s("bottom"))];
  } catch (e) { return null; }
}
// A smart object placed from a file keeps its warp in content pixels (bounds 0,0,w,h); one
// converted from a layer keeps it in document pixels.
function pm_placed_frame(l) {
  var m = pm_more(l), b = pm_warp_bounds(m), s = pm_size(l), box = pm_box(l);
  if (!b || b[0] !== 0 || b[1] !== 0 || Math.abs(b[2] - s[0]) > 0.01 || Math.abs(b[3] - s[1]) > 0.01) return false;
  return Math.abs(box[0]) > 0.01 || Math.abs(box[1]) > 0.01 || Math.abs(box[2] - s[0]) > 0.01 || Math.abs(box[3] - s[1]) > 0.01;
}
function pm_qbox(q) {
  var xs = [], ys = [];
  for (var i = 0; i < 4; i++) { xs.push(q[i][0]); ys.push(q[i][1]); }
  return [Math.min.apply(null, xs), Math.min.apply(null, ys), Math.max.apply(null, xs), Math.max.apply(null, ys)];
}
function pm_target(l) {
  app.activeDocument.activeLayer = l;
  var r = new ActionReference(); r.putEnumerated(pm_s("layer"), pm_s("ordinal"), pm_s("targetEnum"));
  var t = new ActionDescriptor(); t.putReference(pm_s("null"), r);
  // Without freeTransformCenterState the transform event records nothing and changes nothing.
  t.putEnumerated(pm_s("freeTransformCenterState"), pm_s("quadCenterState"), pm_s("QCSAverage"));
  return t;
}
// Convert to Smart Object keeps only the opaque pixels, so a transparent margin would be lost: a
// hidden layer filling `box` keeps the new object's box. Moving the layer into a group releases
// the layers clipped to it, so they are clipped again.
function pm_wrap(l, box) {
  var d = app.activeDocument, name = l.name, chain = [], p = l.parent, idx = -1;
  for (var i = 0; i < p.layers.length; i++) if (p.layers[i].id === l.id) { idx = i; break; }
  for (var j = idx - 1; j >= 0; j--) { var g0 = false; try { g0 = p.layers[j].grouped; } catch (e) {} if (!g0) break; chain.push(p.layers[j]); }
  var g = d.layerSets.add(); g.move(l, ElementPlacement.PLACEBEFORE); l.move(g, ElementPlacement.INSIDE);
  var fr = g.artLayers.add(); fr.name = "Frame";
  d.selection.select([[box[0], box[1]], [box[2], box[1]], [box[2], box[3]], [box[0], box[3]]]);
  var c = new SolidColor(); c.rgb.red = 0; c.rgb.green = 0; c.rgb.blue = 0;
  d.selection.fill(c); d.selection.deselect(); fr.visible = false;
  d.activeLayer = g;
  executeAction(pm_s("newPlacedLayer"), undefined, DialogModes.NO);
  var w = d.activeLayer; w.name = name;
  // grouped toggles the clip (measured): set it only where it is off.
  for (var k = 0; k < chain.length; k++) if (!chain[k].grouped) chain[k].grouped = true;
  d.activeLayer = w;
  return w;
}
function pm_align(l, b) {
  var c = pm_box(l);
  l.resize((b[2] - b[0]) / (c[2] - c[0]) * 100, (b[3] - b[1]) / (c[3] - c[1]) * 100, AnchorPosition.TOPLEFT);
  c = pm_box(l);
  l.translate(UnitValue(b[0] - c[0], "px"), UnitValue(b[1] - c[1], "px"));
}
// A custom warp is a bicubic Bezier patch: 16 control points, row by row from the top-left.
// Homography from the unit square onto the quad, sampled at thirds.
function pm_quad_mesh(q) {
  var x0=q[0][0],y0=q[0][1],x1=q[1][0],y1=q[1][1],x2=q[2][0],y2=q[2][1],x3=q[3][0],y3=q[3][1];
  var dx1=x1-x2,dx2=x3-x2,dy1=y1-y2,dy2=y3-y2,sx=x0-x1+x2-x3,sy=y0-y1+y2-y3,den=dx1*dy2-dx2*dy1;
  if (Math.abs(den) < 1e-9) throw new Error("degenerate quad");
  var g=(sx*dy2-dx2*sy)/den, h=(dx1*sy-sx*dy1)/den, o = [];
  for (var j = 0; j < 4; j++) for (var i = 0; i < 4; i++) {
    var u = i / 3, v = j / 3, z = 1 + g*u + h*v;
    o.push([(x0 + (x1-x0+g*x1)*u + (x3-x0+h*x3)*v) / z, (y0 + (y1-y0+g*y1)*u + (y3-y0+h*y3)*v) / z]);
  }
  return o;
}
// A label around a cylinder seen from slightly above. Across: x = sin(theta) for theta in
// [-a/2, a/2], as the cubic Hermite with the same end slopes, so columns narrow toward the sides.
// Top and bottom edges: arcs whose middle sits `top` and `bottom` px below the line between their
// corners (control points at 4/3 of the bulge put the curve's middle exactly there).
function pm_cyl_mesh(q, angle, top, bottom) {
  var a = angle * Math.PI / 360, k = 2 * a * Math.cos(a) / Math.sin(a) / 3;
  var X = [-1, -1 + k, 1 - k, 1], B = [0, 4 / 3, 4 / 3, 0], T = [], D = [], o = [];
  for (var i = 0; i < 4; i++) {
    var s = (X[i] + 1) / 2;
    T.push([q[0][0] + (q[1][0] - q[0][0]) * s, q[0][1] + (q[1][1] - q[0][1]) * s + top * B[i]]);
    D.push([q[3][0] + (q[2][0] - q[3][0]) * s, q[3][1] + (q[2][1] - q[3][1]) * s + bottom * B[i]]);
  }
  for (var j = 0; j < 4; j++) for (var c = 0; c < 4; c++)
    o.push([T[c][0] + (D[c][0] - T[c][0]) * j / 3, T[c][1] + (D[c][1] - T[c][1]) * j / 3]);
  return o;
}
function pm_ctl_box(p) {
  var b = [p[0][0], p[0][1], p[0][0], p[0][1]];
  for (var i = 1; i < p.length; i++) b = [Math.min(b[0], p[i][0]), Math.min(b[1], p[i][1]), Math.max(b[2], p[i][0]), Math.max(b[3], p[i][1])];
  return b;
}
function pm_apply(l, pts) {
  var mesh = new ActionList();
  for (var k = 0; k < 16; k++) {
    var pd = new ActionDescriptor();
    pd.putUnitDouble(pm_s("horizontal"), pm_s("pixelsUnit"), pts[k][0]);
    pd.putUnitDouble(pm_s("vertical"), pm_s("pixelsUnit"), pts[k][1]);
    mesh.putObject(pm_s("rationalPoint"), pd);
  }
  var b = pm_box(l), w = new ActionDescriptor(), bd = new ActionDescriptor(), t = pm_target(l);
  w.putEnumerated(pm_s("warpStyle"), pm_s("warpStyle"), pm_s("warpCustom"));
  bd.putDouble(pm_s("top"), b[1]); bd.putDouble(pm_s("left"), b[0]);
  bd.putDouble(pm_s("bottom"), b[3]); bd.putDouble(pm_s("right"), b[2]);
  w.putObject(pm_s("bounds"), pm_s("classFloatRect"), bd);
  var ce = new ActionDescriptor(); ce.putList(pm_s("meshPoints"), mesh);
  w.putObject(pm_s("customEnvelopeWarp"), pm_s("customEnvelopeWarp"), ce);
  t.putObject(pm_s("warp"), pm_s("warp"), w);
  executeAction(pm_s("transform"), t, DialogModes.NO);
}
// Reset a warp with a flat custom warp: warpNone leaves a NaN transform on some objects (27.11).
function pm_flat(l) {
  var b = pm_box(l);
  pm_apply(l, pm_quad_mesh([[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]]));
}
// The design's print size rides in the layer's XMP (scenario:printSize="WxH"), because after a fit
// the content is the quad's on-canvas size and replace_design needs the design's proportions.
function pm_xmp(l) { try { return l.xmpMetadata.rawData || ""; } catch (e) { return ""; } }
function pm_print_get(raw) {
  var m = /scenario:printSize="([\d.]+)x([\d.]+)"/.exec(raw || "");
  return m ? [Number(m[1]), Number(m[2])] : null;
}
function pm_xmp_put(l, raw, ps) {
  var a = 'scenario:printSize="' + Math.round(ps[0]) + "x" + Math.round(ps[1]) + '"';
  var ns = 'xmlns:scenario="https://scenario.com/ns/photoshop/1.0/"';
  if (/scenario:printSize="[^"]*"/.test(raw)) raw = raw.replace(/scenario:printSize="[^"]*"/, a);
  else if (/xmlns:scenario="[^"]*"/.test(raw)) raw = raw.replace(/xmlns:scenario="[^"]*"/, function (s) { return s + " " + a; });
  else if (raw.indexOf("</rdf:RDF>") >= 0) raw = raw.replace("</rdf:RDF>", '<rdf:Description rdf:about="" ' + ns + " " + a + "/></rdf:RDF>");
  else raw = '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">' +
    '<rdf:Description rdf:about="" ' + ns + " " + a + "/></rdf:RDF></x:xmpmeta>";
  l.xmpMetadata.rawData = raw;
}
function pm_plain(l) {
  var r = new ActionReference(); r.putIdentifier(pm_c("Lyr "), l.id);
  var x = executeActionGet(r);
  if (x.getObjectValue(pm_s("smartObject")).hasKey(pm_s("filterFX")))
    throw new Error("has Smart Filters: fit before displace (a fit would nest them under the new warp)");
  if (x.getBoolean(pm_s("hasUserMask")) || x.getBoolean(pm_s("hasVectorMask")))
    throw new Error("has a layer mask: put the mask on the group instead (a fit would warp it)");
}
// Fit a smart object onto a 16-point net. Measured on 27.11: a custom warp lands exactly only on
// an object scaled UP from the box it was converted at; at scale 1 or below, corners drift by up
// to 60 px depending on the quad's shape. So the object is reset with a flat warp, scaled to 97%
// of the net's box, wrapped (Convert to Smart Object), scaled onto the box, then warped. Each fit
// nests one level and keeps the box's resolution. Returns the layer (new id) and `check`: the
// largest gap between nonAffineTransform and the net's box, near 0 after a good fit.
var PM_SCALE = 0.97;
function pm_fit(l, pts) {
  pm_plain(l);
  var d = app.activeDocument, out = {reset: false}, ch = null;
  // The wrap and the warp drop an active selection: it is stored and loaded back.
  if (pm_has_selection(d)) { ch = d.channels.add(); d.selection.store(ch); d.selection.deselect(); d.activeChannels = d.componentChannels; }
  if (pm_warp_style(pm_more(l)) !== "warpNone") { pm_flat(l); out.reset = true; }
  var keep = {name: l.name, fill: l.fillOpacity, opacity: l.opacity, blend: l.blendMode, raw: pm_xmp(l)};
  out.print_size = pm_print_get(keep.raw) || pm_size(l);
  var box = pm_ctl_box(pts), w = Math.round(PM_SCALE * (box[2] - box[0])), h = Math.round(PM_SCALE * (box[3] - box[1]));
  var x0 = Math.round((box[0] + box[2] - w) / 2), y0 = Math.round((box[1] + box[3] - h) / 2), fr = [x0, y0, x0 + w, y0 + h];
  pm_align(l, fr);
  l.fillOpacity = 100; l.opacity = 100; l.blendMode = BlendMode.NORMAL;
  l = pm_wrap(l, fr);
  l.fillOpacity = keep.fill; l.opacity = keep.opacity; l.blendMode = keep.blend;
  pm_xmp_put(l, keep.raw, out.print_size);
  pm_align(l, box);
  pm_apply(l, pts);
  if (ch) { d.selection.load(ch); ch.remove(); d.activeChannels = d.componentChannels; d.activeLayer = l; }
  var na = pm_more(l).getList(pm_s("nonAffineTransform")), bc = [box[0], box[1], box[2], box[1], box[2], box[3], box[0], box[3]], e = 0;
  for (var i = 0; i < 8; i++) e = Math.max(e, Math.abs(na.getDouble(i) - bc[i]));
  out.layer = l;
  out.check = Math.round(e * 100) / 100;
  out.target = [pts[0], pts[3], pts[15], pts[12]];
  return out;
}
// Corners TL, TR, BR, BL in document pixels. The stored net sits in the frame of the box the
// object had when it was converted, so it is mapped from its own bounding box onto the current
// box. `consistent` is false when that mapping does not hold: nonAffineTransform disagrees with
// the box (a hand-made warp), or a content-pixel warp on a placed object.
function pm_corners(l) {
  var m = pm_more(l);
  if (pm_warp_style(m) !== "warpCustom") {
    var t = m.getList(pm_s("transform"));
    return {corners: [[t.getDouble(0), t.getDouble(1)], [t.getDouble(2), t.getDouble(3)],
                      [t.getDouble(4), t.getDouble(5)], [t.getDouble(6), t.getDouble(7)]], consistent: true};
  }
  var mesh = pm_mesh(m), n = mesh.length, side = Math.round(Math.sqrt(n)), idx = [0, side - 1, n - 1, n - side];
  var ab = pm_ctl_box(mesh), box = pm_box(l), na = m.getList(pm_s("nonAffineTransform")), e = 0, out = [];
  var bc = [box[0], box[1], box[2], box[1], box[2], box[3], box[0], box[3]];
  for (var k = 0; k < 8; k++) e = Math.max(e, Math.abs(na.getDouble(k) - bc[k]));
  var sx = (box[2] - box[0]) / (ab[2] - ab[0]), sy = (box[3] - box[1]) / (ab[3] - ab[1]);
  for (var q = 0; q < 4; q++) out.push([box[0] + (mesh[idx[q]][0] - ab[0]) * sx, box[1] + (mesh[idx[q]][1] - ab[1]) * sy]);
  return {corners: out, consistent: e < 1 && !pm_placed_frame(l)};
}
function pm_err(a, q) {
  var e = 0;
  for (var i = 0; i < 4; i++) e = Math.max(e, Math.sqrt(Math.pow(a[i][0] - q[i][0], 2) + Math.pow(a[i][1] - q[i][1], 2)));
  return Math.round(e * 100) / 100;
}
function pm_round(c) {
  var o = []; for (var i = 0; i < c.length; i++) o.push([Math.round(c[i][0] * 10) / 10, Math.round(c[i][1] * 10) / 10]);
  return o;
}
function pm_chain_top(l) {
  var p = l.parent, idx = -1;
  for (var i = 0; i < p.layers.length; i++) if (p.layers[i].id === l.id) { idx = i; break; }
  var top = l;
  for (var j = idx - 1; j >= 0; j--) {
    var x = p.layers[j], g = false;
    try { g = x.grouped; } catch (e) {}
    if (!g) break;
    top = x;
  }
  return top;
}
function pm_place(path) {
  var pd = new ActionDescriptor(); pd.putPath(pm_c("null"), new File(path));
  pd.putEnumerated(pm_c("FTcs"), pm_c("QCSt"), pm_c("Qcsa"));
  executeAction(pm_c("Plc "), pd, DialogModes.NO);
  return app.activeDocument.activeLayer;
}
function pm_replace(path) {
  var rd = new ActionDescriptor(); rd.putPath(pm_c("null"), new File(path));
  executeAction(pm_s("placedLayerReplaceContents"), rd, DialogModes.NO);
}
function pm_mask_from_selection() {
  var desc = new ActionDescriptor(); desc.putClass(pm_c("Nw  "), pm_c("Chnl"));
  var ref = new ActionReference(); ref.putEnumerated(pm_c("Chnl"), pm_c("Chnl"), pm_c("Msk "));
  desc.putReference(pm_c("At  "), ref);
  desc.putEnumerated(pm_c("Usng"), pm_c("UsrM"), pm_c("RvlS"));
  executeAction(pm_c("Mk  "), desc, DialogModes.NO);
}
function pm_has_selection(d) { try { d.selection.bounds; return true; } catch (e) { return false; } }
if (app.documents.length === 0) throw new Error("no document open");
var d = app.activeDocument;
"""

PLACEHOLDER_JS = r"""
var ch = null;
if (ARGS.mask_selection && pm_has_selection(d)) { ch = d.channels.add(); ch.name = "pm_sel"; d.selection.store(ch); d.selection.deselect(); }
var top = d.layers[0];
var grp = d.layerSets.add();
grp.name = "Mockup: " + ARGS.name;
grp.move(top, ElementPlacement.PLACEBEFORE);
d.activeLayer = grp;
var L = pm_place(ARGS.path);
L.move(grp, ElementPlacement.INSIDE);
L.name = ARGS.name;
var fit = pm_fit(L, pm_quad_mesh(ARGS.quad));
L = fit.layer;
L.fillOpacity = ARGS.fill;
if (ch) {
  d.activeLayer = grp; d.selection.load(ch); pm_mask_from_selection(); d.selection.deselect();
  ch.remove(); d.activeChannels = d.componentChannels;
}
var c = pm_corners(L).corners;
return {id: L.id, name: L.name, group: grp.name, size: pm_size(L), print_size: fit.print_size, corners: pm_round(c),
        corner_error: pm_err(c, ARGS.quad), fit_check: fit.check, group_mask: !!ch};
"""

FIT_JS = r"""
var L = pm_so(ARGS.layer);
var pts = ARGS.angle ? pm_cyl_mesh(ARGS.quad, ARGS.angle, ARGS.top, ARGS.bottom) : pm_quad_mesh(ARGS.quad);
var fit = pm_fit(L, pts), c = pm_corners(fit.layer);
L = fit.layer;
return {id: L.id, corners: pm_round(c.corners), target: pm_round(fit.target), corner_error: pm_err(c.corners, fit.target),
        consistent: c.consistent, fit_check: fit.check, reset: fit.reset, print_size: fit.print_size};
"""

CORNERS_JS = r"""
var L = pm_so(ARGS.layer), c = pm_corners(L);
return {id: L.id, corners: pm_round(c.corners), consistent: c.consistent, size: pm_size(L),
        print_size: pm_print_get(pm_xmp(L)) || pm_size(L), fill: L.fillOpacity};
"""

REPLACE_JS = r"""
var L = pm_so(ARGS.layer);
var sz = pm_size(L), raw = pm_xmp(L), ps = pm_print_get(raw) || sz, before = pm_corners(L).corners;
var src = app.open(new File(ARGS.path));
__psr_created.push(src.id);
if (src.layers.length > 1) src.mergeVisibleLayers();
if (src.activeLayer.isBackgroundLayer) src.activeLayer.isBackgroundLayer = false;
// Cropped or padded to the print proportions, then stretched to the content size: the fit maps
// the content box onto the quad, so the print proportions come back on the product.
var W = src.width.as("px"), H = src.height.as("px"), sx = ps[0] / W, sy = ps[1] / H;
if (ARGS.fit === "cover") sx = sy = Math.max(sx, sy);
else if (ARGS.fit === "contain") sx = sy = Math.min(sx, sy);
sx *= sz[0] / ps[0]; sy *= sz[1] / ps[1];
var rw = Math.max(1, Math.round(W * sx)), rh = Math.max(1, Math.round(H * sy));
if (rw !== W || rh !== H)
  src.resizeImage(UnitValue(rw, "px"), UnitValue(rh, "px"), null, ResampleMethod.BICUBICAUTOMATIC);
if (rw !== sz[0] || rh !== sz[1])
  src.resizeCanvas(UnitValue(sz[0], "px"), UnitValue(sz[1], "px"), AnchorPosition.MIDDLECENTER);
psr_export(src, ARGS.tmp, "png");
psr_close(src);
app.activeDocument = d;
d.activeLayer = L;
var keep = L.name;
pm_replace(ARGS.tmp);
L = d.activeLayer;
// Replace Contents renames the layer after the file; scripts find layers by name.
L.name = keep;
if (raw && pm_xmp(L) !== raw) L.xmpMetadata.rawData = raw;
if (ARGS.reset_fill) L.fillOpacity = 100;
var after = pm_corners(L).corners;
return {id: L.id, content_size: sz, print_size: ps, source_size: [W, H], scale: [Math.round(sx * 1000) / 1000, Math.round(sy * 1000) / 1000],
        corners: pm_round(after), drift: pm_err(after, before), fill: L.fillOpacity};
"""

LIGHT_JS = r"""
var L = pm_so(ARGS.layer), P = pm_layer(ARGS.product), top = pm_chain_top(L), made = [];
function copy(name, mode, lo, hi, opacity) {
  d.activeLayer = P;
  var c = P.duplicate(top, ElementPlacement.PLACEBEFORE);
  d.activeLayer = c;
  if (String(c.kind) !== "LayerKind.NORMAL") c.rasterize(RasterizeType.ENTIRELAYER);
  c.name = name;
  c.desaturate();
  c.adjustLevels(lo, hi, 1.0, 0, 255);
  c.blendMode = mode;
  c.opacity = opacity;
  if (!c.grouped) c.grouped = true;     // a copy placed inside the chain is clipped already
  top = c;
  made.push({id: c.id, name: c.name});
}
var m = Math.max(2, Math.min(253, Math.round(ARGS.neutral)));
if (ARGS.shade > 0) copy(ARGS.prefix + "Shading (product)", BlendMode.MULTIPLY, 0, m, ARGS.shade);
if (ARGS.light > 0) copy(ARGS.prefix + "Highlights (product)", BlendMode.SCREEN, m, 255, ARGS.light);
return {neutral: m, layers: made};
"""

DISPLACE_JS = r"""
var L = pm_so(ARGS.layer), P = pm_layer(ARGS.product);
// The Smart Filter keeps only the map's path and re-reads it on every re-render (a later content
// replace fails with "file was not found" once it is gone), so the map is kept on disk.
var dir = ARGS.map_dir ? new Folder(ARGS.map_dir) : null;
if (!dir) {
  try { dir = new Folder(d.path.fsName + "/" + d.name.replace(/\.[^.]+$/, "") + " maps"); }
  catch (e) { dir = new Folder(Folder.myDocuments.fsName + "/Scenario Photoshop/displace maps"); }
}
if (!dir.exists && !dir.create()) throw new Error("cannot create " + dir.fsName);
var stem = (d.name.replace(/\.[^.]+$/, "") + " " + L.name).replace(/[\\\/:*?"<>|]/g, "_");
var map = new File(dir.fsName + "/" + stem + " displace.psd");
for (var n = 2; map.exists; n++) map = new File(dir.fsName + "/" + stem + " displace " + n + ".psd");
var b = [Math.max(0, L.bounds[0].as("px")), Math.max(0, L.bounds[1].as("px")),
         Math.min(d.width.as("px"), L.bounds[2].as("px")), Math.min(d.height.as("px"), L.bounds[3].as("px"))];
var t = psr_dup(d, "displace map", false);
app.activeDocument = t;
function keep(c) {
  var hit = false;
  for (var i = 0; i < c.layers.length; i++) {
    var x = c.layers[i];
    if (x.id === P.id) { x.visible = true; hit = true; }
    else if (x.typename === "LayerSet" && keep(x)) { x.visible = true; hit = true; }
    else x.visible = false;
  }
  return hit;
}
if (!keep(t)) throw new Error("product layer not found in the copy");
t.flatten();
t.crop([UnitValue(b[0], "px"), UnitValue(b[1], "px"), UnitValue(b[2], "px"), UnitValue(b[3], "px")]);
t.activeLayer.desaturate();
var r = ARGS.blur;
if (r === null) r = Math.max(1, Math.round(d.width.as("px") / 1500 * 10) / 10);
if (r > 0) t.activeLayer.applyGaussianBlur(r);
psr_export(t, map.fsName, "psd");
psr_close(t);
app.activeDocument = d;
d.activeLayer = L;
var dd = new ActionDescriptor();
dd.putInteger(pm_c("HrzS"), ARGS.scale);
dd.putInteger(pm_c("VrtS"), ARGS.scale);
dd.putEnumerated(pm_c("DspM"), pm_c("DspM"), pm_c("StrF"));
dd.putEnumerated(pm_c("UndA"), pm_c("UndA"), pm_c("RptE"));
dd.putPath(pm_c("DspF"), map);
executeAction(pm_c("Dspl"), dd, DialogModes.NO);
return {id: L.id, map: map.fsName, map_box: b, blur: r, scale: ARGS.scale};
"""

COLORWAY_JS = r"""
var P = pm_layer(ARGS.product), sel = pm_has_selection(d), tmp = null, T = null;
if (sel) {
  tmp = d.channels.add(); tmp.name = "pm_colorway_sel"; d.selection.store(tmp);
  d.activeChannels = d.componentChannels;
}
d.activeLayer = P;
if (ARGS.curve) {
  // Curves under the color: Color mode keeps the base's luminance, so the base is first mapped
  // to the swatch's (a gain when darkening, an offset when lightening); the folds keep their pattern.
  var desc = new ActionDescriptor(), ref = new ActionReference(), lay = new ActionDescriptor(),
      crv = new ActionDescriptor();
  ref.putClass(pm_c("AdjL")); desc.putReference(pm_c("null"), ref);
  crv.putEnumerated(pm_s("presetKind"), pm_s("presetKindType"), pm_s("presetKindDefault"));
  lay.putObject(pm_c("Type"), pm_c("Crvs"), crv);
  lay.putBoolean(pm_c("Grup"), !sel);
  desc.putObject(pm_c("Usng"), pm_c("AdjL"), lay);
  executeAction(pm_c("Mk  "), desc, DialogModes.NO);
  T = d.activeLayer; T.name = "Colorway tone: " + ARGS.name;
  var sd = new ActionDescriptor(), sref = new ActionReference();
  sref.putEnumerated(pm_c("AdjL"), pm_c("Ordn"), pm_c("Trgt")); sd.putReference(pm_c("null"), sref);
  var c2 = new ActionDescriptor(), adjs = new ActionList(), ca = new ActionDescriptor(),
      cref = new ActionReference(), pts = new ActionList();
  c2.putEnumerated(pm_s("presetKind"), pm_s("presetKindType"), pm_s("presetKindCustom"));
  cref.putEnumerated(pm_c("Chnl"), pm_c("Chnl"), pm_c("Cmps")); ca.putReference(pm_c("Chnl"), cref);
  for (var i = 0; i < ARGS.curve.length; i++) {
    var pt = new ActionDescriptor();
    pt.putDouble(pm_c("Hrzn"), ARGS.curve[i][0]); pt.putDouble(pm_c("Vrtc"), ARGS.curve[i][1]);
    pts.putObject(pm_c("Pnt "), pt);
  }
  ca.putList(pm_c("Crv "), pts); adjs.putObject(pm_c("CrvA"), ca);
  c2.putList(pm_c("Adjs"), adjs); sd.putObject(pm_c("T   "), pm_c("Crvs"), c2);
  executeAction(pm_c("setd"), sd, DialogModes.NO);
  if (sel) d.selection.load(tmp, SelectionType.REPLACE);
  d.activeLayer = T;
}
// A fill layer made while a selection is active takes the selection as its mask.
var desc = new ActionDescriptor(), ref = new ActionReference(), lay = new ActionDescriptor(),
    fill = new ActionDescriptor(), col = new ActionDescriptor();
ref.putClass(pm_s("contentLayer")); desc.putReference(pm_c("null"), ref);
col.putDouble(pm_c("Rd  "), ARGS.rgb[0]); col.putDouble(pm_c("Grn "), ARGS.rgb[1]); col.putDouble(pm_c("Bl  "), ARGS.rgb[2]);
fill.putObject(pm_c("Clr "), pm_c("RGBC"), col);
lay.putObject(pm_c("Type"), pm_s("solidColorLayer"), fill);
desc.putObject(pm_c("Usng"), pm_s("contentLayer"), lay);
executeAction(pm_c("Mk  "), desc, DialogModes.NO);
var F = d.activeLayer;
F.name = "Colorway: " + ARGS.name;
F.blendMode = BlendMode.COLORBLEND;
// Above a clipped Curves the fill is clipped already, and grouped toggles: set it only when off.
if (!sel && !F.grouped) F.grouped = true;
if (!sel && !F.grouped) throw new Error("could not clip the colorway to " + P.name);
if (tmp) tmp.remove();
return {id: F.id, tone_id: T ? T.id : null, masked: sel, clipped: F.grouped};
"""

# The product (and its colorway layers) alone, in the document's own color space: what the swatch
# check reads, without the print above it.
SOLO_EXPORT_JS = r"""
function pm_keep(c, keep) {
  var any = false;
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i], k = false;
    for (var j = 0; j < keep.length; j++) if (l.name === keep[j]) k = true;
    if (!k && l.typename === "LayerSet") k = pm_keep(l, keep);
    l.visible = k;
    if (k) any = true;
  }
  return any;
}
var pl = pm_find(d, ARGS.product);
if (!pl) throw new Error("layer not found: " + ARGS.product);
var keep = [pl.name].concat(ARGS.keep), s = psr_dup(d, d.name + " check", false);
try {
  app.activeDocument = s;
  if (!pm_keep(s, keep)) throw new Error("layer not found: " + pl.name);
  try { s.mergeVisibleLayers(); } catch (e) {}
  psr_export(s, ARGS.path, "png");
} finally { psr_close(s); app.activeDocument = d; }
return ARGS.path;
"""

# One design = one replace state; the export works on a temporary copy and adds none. Stepping
# back from the active state (checked by name, never by list length) therefore returns to the
# document as it was, even at the History limit. (Deleting
# an active snapshot instead sends History to the opening state: measured.)
EXPORT_JS = r"""
var c = psr_dup(d, d.name + " export", true);
var p = psr_export(c, ARGS.out, "png");
psr_close(c);
app.activeDocument = d;
var hs = d.historyStates, a = d.activeHistoryState, i = -1;
for (var q = hs.length - 1; q >= 0; q--) if (hs[q] == a) { i = q; break; }
if (a.name !== ARGS.state || i < 1) throw new Error("unexpected History state: " + a.name);
d.activeHistoryState = hs[i - 1];
return p;
"""


def _run(js, args, undo=None, timeout=240):
    body = HELPERS_JS.replace("%ARGS%", json.dumps(args)) + js
    res = ps_run.run(body, undo=undo, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError("%s (line %s)" % (res.get("error"), res.get("line")))
    return res["result"]


def _key(v):
    return int(v) if isinstance(v, str) and v.isdigit() else v


def _check_quad(quad):
    if len(quad) != 4 or any(len(p) != 2 for p in quad):
        raise ValueError("quad needs four [x, y] corners: TL, TR, BR, BL")
    return [[float(x), float(y)] for x, y in quad]


def _solid_png(path, w, h, rgb):
    row = b"\x00" + bytes(rgb) * w
    raw = zlib.compress(row * h, 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", raw) + chunk(b"IEND", b""))
    return path


def _tmp(suffix):
    fd, p = tempfile.mkstemp(prefix="scenario_mockup_", suffix=suffix)
    os.close(fd)
    return p


def quad_size(quad):
    q = _check_quad(quad)

    def dist(a, b):
        return math.hypot(b[0] - a[0], b[1] - a[1])

    return (max(1, round((dist(q[0], q[1]) + dist(q[3], q[2])) / 2)),
            max(1, round((dist(q[0], q[3]) + dist(q[1], q[2])) / 2)))


def placeholder(quad, name="Place Design Here", size=None, fill=60, color=(214, 72, 72),
                mask_selection=True, undo="Scenario: Mockup placeholder"):
    q = _check_quad(quad)
    w, h = size or quad_size(q)
    png = _solid_png(_tmp(".png"), int(w), int(h), color)
    try:
        return _run(PLACEHOLDER_JS, {"quad": q, "name": name, "path": png, "fill": fill,
                                     "mask_selection": bool(mask_selection)}, undo=undo)
    finally:
        os.remove(png)


def fit_quad(layer, quad, undo="Scenario: Fit to corners"):
    return _run(FIT_JS, {"layer": _key(layer), "quad": _check_quad(quad), "angle": None}, undo=undo)


def fit_cylinder(layer, quad, bulge, top_bulge=None, angle=120, undo="Scenario: Fit to cylinder"):
    if not 0 < float(angle) <= 180:
        raise ValueError("angle is the label's visible arc in degrees, above 0 and up to 180")
    top = bulge if top_bulge is None else top_bulge
    return _run(FIT_JS, {"layer": _key(layer), "quad": _check_quad(quad), "angle": float(angle),
                         "top": float(top), "bottom": float(bulge)}, undo=undo)


def corners(layer):
    return _run(CORNERS_JS, {"layer": _key(layer)})


def replace_design(layer, path, fit="cover", reset_fill=True, undo="Scenario: Replace design"):
    if fit not in ("cover", "contain", "exact"):
        raise ValueError("fit must be cover, contain or exact")
    tmp = _tmp(".png")
    try:
        return _run(REPLACE_JS, {"layer": _key(layer), "path": os.path.abspath(path), "fit": fit,
                                 "tmp": tmp, "reset_fill": bool(reset_fill)}, undo=undo)
    finally:
        os.remove(tmp)


def lighting(layer, product, shade=85, light=50, prefix="", undo="Scenario: Product lighting"):
    under = G.stats(layer=_key(product), region={"alpha": _key(layer)})
    out = _run(LIGHT_JS, {"layer": _key(layer), "product": _key(product), "shade": shade,
                          "light": light, "prefix": prefix, "neutral": under["luminance"]},
               undo=undo)
    out["product_under_design"] = under
    return out


def displace(layer, product, scale=8, blur=None, map_dir=None, undo="Scenario: Displace"):
    return _run(DISPLACE_JS, {"layer": _key(layer), "product": _key(product), "scale": int(scale),
                              "blur": blur, "map_dir": map_dir}, undo=undo)


def batch(layer, designs, out_dir, fit="cover"):
    os.makedirs(out_dir, exist_ok=True)
    state = "Scenario: Batch design"
    results = []
    for path in designs:
        r = replace_design(layer, path, fit=fit, undo=state)
        base = os.path.splitext(os.path.basename(path))[0]
        out = os.path.abspath(os.path.join(out_dir, base + " mockup.png"))
        r["out"] = _run(EXPORT_JS, {"out": out, "state": state})
        r["design"] = path
        results.append(r)
    return results


def _rgb(c):
    if isinstance(c, dict):
        if "lab" not in c or len(c["lab"]) != 3:
            raise ValueError("a Lab color needs {\"lab\": [L, a, b]}")
        return lab_to_rgb(c["lab"])
    if isinstance(c, str):
        h = c.lstrip("#")
        if len(h) != 6:
            raise ValueError("color needs #rrggbb or (r, g, b): " + c)
        return [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    if len(c) != 3:
        raise ValueError("color needs (r, g, b)")
    return [int(v) for v in c]


def _lum(rgb):
    # Photoshop's luminosity weights, the ones its Color blend mode keeps.
    return 0.3 * rgb[0] + 0.59 * rgb[1] + 0.11 * rgb[2]


def _pct(sorted_vals, p):
    return sorted_vals[min(len(sorted_vals) - 1, int(p / 100.0 * len(sorted_vals)))]


def garment_tones(lums):
    """The product's luminance under the colorway: mid (mean of the 25th to 75th percentile), p99."""
    v = sorted(lums)
    if not v:
        raise ValueError("no product pixels in the colorway area")
    lo, hi = _pct(v, 25), _pct(v, 75)
    mid = [x for x in v if lo <= x <= hi]
    return {"mid": round(sum(mid) / len(mid), 2), "p25": lo, "p75": hi, "p99": _pct(v, 99),
            "pixels": len(v)}


# A swatch so light that a curve keeping the 99th percentile at 250 would keep under half the
# folds' depth, on a blank already within 25% of it (white on a white blank): no curve, the blank
# stands as that colorway. Authoring-time.
BLANK_SLOPE = 0.5
BLANK_RATIO = 1.25


def is_blank(tones, rgb, margin=3):
    """True when the swatch is at or past the blank's lit fabric and the blank is already within
    25% of it: no Curves runs, and the blank's own shading is the colorway."""
    target, mid, p99 = _lum(rgb), tones["mid"], tones["p99"]
    if target <= mid + margin or p99 <= mid:
        return False
    return (250.0 - target) / (p99 - mid) < BLANK_SLOPE and target <= BLANK_RATIO * mid


def tone_curve(tones, rgb, margin=3):
    """Curves points (composite channel) that bring the mid-tones to the swatch's luminance, or
    None when they are within `margin` or the blank stands (is_blank). Darker swatch: a gain
    (L * target / mid, at least 0.05), so folds scale with the color. Lighter swatch: an offset,
    its slope lowered so the 99th percentile stays at 250 or under."""
    target, mid = _lum(rgb), tones["mid"]
    if abs(target - mid) <= margin or mid <= 0 or is_blank(tones, rgb, margin):
        return None
    if target < mid:
        k = max(target / mid, 0.05)
    else:
        k = 1.0
        if tones["p99"] > mid:
            k = min(1.0, (250.0 - target) / (tones["p99"] - mid))
        k = max(k, 0.05)
    y0 = max(0.0, target - k * mid)
    x1 = (255.0 - y0) / k
    if x1 >= 255:
        return [[0, round(y0, 2)], [255, round(y0 + 255 * k, 2)]]
    return [[0, round(y0, 2)], [round(x1, 2), 255]]


def _lab(c):
    """CIE Lab (D65) of an sRGB color (0 to 255)."""
    def lin(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, bl = (lin(float(x)) for x in c)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * bl) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * bl
    z = (0.0193 * r + 0.1192 * g + 0.9505 * bl) / 1.08883

    def f(t):
        return t ** (1.0 / 3) if t > 0.008856 else 7.787 * t + 16.0 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def lab_to_rgb(lab):
    """sRGB (0 to 255, rounded, clipped to the gamut) of a CIE Lab (D65) color."""
    L, a, b = (float(v) for v in lab)
    fy = (L + 16) / 116.0
    fx, fz = fy + a / 500.0, fy - b / 200.0

    def finv(t):
        return t ** 3 if t ** 3 > 0.008856 else (t - 16.0 / 116) / 7.787
    x, y, z = finv(fx) * 0.95047, finv(fy), finv(fz) * 1.08883
    lin = (3.2406 * x - 1.5372 * y - 0.4986 * z, -0.9689 * x + 1.8758 * y + 0.0415 * z,
           0.0557 * x - 0.2040 * y + 1.0570 * z)

    def enc(v):
        v = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        return max(0, min(255, round(v * 255)))
    return [enc(v) for v in lin]


def delta_e(a, b):
    """CIE76 color difference of two sRGB colors (0 to 255)."""
    return round(math.dist(_lab(a), _lab(b)), 2)


# "flat": the result's relative fold contrast under FLAT_FLOOR and under FLAT_SHARE of the
# original's. Authoring-time, from synthetic shirts and two corpus frames: colorways that kept their
# folds measured 0.21 to 0.57, flat ones 0.008 to 0.14.
FLAT_FLOOR = 0.15
FLAT_SHARE = 0.5


def _rel_contrast(v):
    mid = _pct(v, 50)
    return round((_pct(v, 90) - _pct(v, 10)) / mid, 3) if mid else None


def swatch_check(base, result, rgb, lab=None):
    """The colorway's mid-tones against the swatch. base and result: the same product pixels
    [(r, g, b)] before and after. Returns the mid-tones' mean color; delta_e (CIE76) to the
    swatch, or to `lab` when given; folds (correlation of the luminance pattern: 1 = folds in the
    same places, blind to their depth); spread (p90 - p10 of the luminance, after over before);
    contrast ((p90 - p10) / p50, before and after); flat (the contrast after is under FLAT_FLOOR
    and under FLAT_SHARE of the contrast before); blank (is_blank: the blank stands as the
    colorway, so delta_e measures its own shading)."""
    if len(base) != len(result) or not base:
        raise ValueError("base and result need the same, non-empty pixel list")
    lb, lr = [_lum(p) for p in base], [_lum(p) for p in result]
    v = sorted(lr)
    lo, hi = _pct(v, 25), _pct(v, 75)
    mids = [p for p, x in zip(result, lr) if lo <= x <= hi]
    mean = [round(sum(p[i] for p in mids) / len(mids), 1) for i in range(3)]
    mb, mr = sum(lb) / len(lb), sum(lr) / len(lr)
    sb = math.sqrt(sum((x - mb) ** 2 for x in lb))
    sr = math.sqrt(sum((x - mr) ** 2 for x in lr))
    folds = sum((x - mb) * (y - mr) for x, y in zip(lb, lr)) / (sb * sr) if sb and sr else 0.0
    vb = sorted(lb)
    before = _pct(vb, 90) - _pct(vb, 10)
    after = _pct(v, 90) - _pct(v, 10)
    target = _lab(rgb) if lab is None else [float(x) for x in lab]
    c0, c1 = _rel_contrast(vb), _rel_contrast(v)
    flat = c0 is not None and c1 is not None and c1 < min(FLAT_FLOOR, FLAT_SHARE * c0)
    return {"mean": mean, "swatch": list(rgb), "delta_e": round(math.dist(_lab(mean), target), 2),
            "folds": round(folds, 3), "spread": round(after / before, 2) if before else None,
            "contrast": [c0, c1], "flat": flat, "blank": is_blank(garment_tones(lb), rgb),
            "pixels": len(lr)}


def _area_pixels(path, mask, size=400):
    """[(r, g, b)] under the mask (white = in), both scaled to a `size` px long side. The same
    mask gives the same pixels in the same order for every image of one canvas."""
    from PIL import Image  # optional dependency, only for colorway matching and checks
    with Image.open(path) as im, Image.open(mask) as m:
        k = min(1.0, float(size) / max(im.size))
        dims = (max(1, round(im.width * k)), max(1, round(im.height * k)))
        px = im.convert("RGB").resize(dims, Image.BOX).tobytes()
        mk = m.convert("L").resize(dims, Image.BOX).tobytes()
    return [tuple(px[i * 3:i * 3 + 3]) for i in range(len(mk)) if mk[i] >= 128]


def colorways(product, colors, out_dir, match=True, check=True):
    os.makedirs(out_dir, exist_ok=True)
    state = "Scenario: Colorway"
    work = tempfile.mkdtemp(prefix="scenario_colorways_")
    mask, tones, base = os.path.join(work, "area.png"), None, None
    if match or check:
        from PIL import Image  # optional dependency, only for colorway matching and checks
        sel = IO.selection()
        bp = _run(SOLO_EXPORT_JS, {"product": _key(product), "keep": [],
                                   "path": os.path.join(work, "base.png")})
        if sel["bounds"]:
            IO.export_mask(mask, bounds=[0, 0] + sel["canvas"])
        else:
            # Clipped to the product: the colorway covers the product's opaque pixels.
            with Image.open(bp) as im:
                im.convert("RGBA").getchannel("A").point(lambda a: 255 if a >= 128 else 0).save(mask)
        base = _area_pixels(bp, mask)
        tones = garment_tones([_lum(p) for p in base])
    results = []
    for name, color in colors.items():
        rgb = _rgb(color)
        lab = list(color["lab"]) if isinstance(color, dict) else None
        curve = tone_curve(tones, rgb) if match else None
        r = _run(COLORWAY_JS, {"product": _key(product), "name": name, "rgb": rgb, "curve": curve},
                 undo=state)
        out = os.path.abspath(os.path.join(out_dir, "%s colorway.png" % name))
        if check:
            keep = ["Colorway: " + name, "Colorway tone: " + name]
            cp = _run(SOLO_EXPORT_JS, {"product": _key(product), "keep": keep,
                                       "path": os.path.join(work, name + ".png")})
            r["check"] = swatch_check(base, _area_pixels(cp, mask), rgb, lab=lab)
        r["out"] = _run(EXPORT_JS, {"out": out, "state": state})
        r.update({"colorway": name, "curve": curve, "tones": tones})
        results.append(r)
    return results


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        i = argv.index(flag)
        return cast(argv[i + 1])
    return default


def _quad(s):
    v = [float(x) for x in s.split(",")]
    if len(v) != 8:
        raise ValueError("quad needs 8 numbers: TLx,TLy,TRx,TRy,BRx,BRy,BLx,BLy")
    return [v[0:2], v[2:4], v[4:6], v[6:8]]


def _pair(s):
    return tuple(int(x) for x in s.split(",")) if s else None


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    try:
        if cmd == "placeholder":
            out = placeholder(_quad(argv[1]), _opt(argv, "--name", str, "Place Design Here"),
                              _pair(_opt(argv, "--size")), _opt(argv, "--fill", float, 60))
        elif cmd == "fit":
            out = fit_quad(argv[1], _quad(argv[2]))
        elif cmd == "cylinder":
            out = fit_cylinder(argv[1], _quad(argv[2]), _opt(argv, "--bulge", float, 0),
                               _opt(argv, "--top", float), _opt(argv, "--angle", float, 120))
        elif cmd == "corners":
            out = corners(argv[1])
        elif cmd == "replace":
            out = replace_design(argv[1], argv[2], _opt(argv, "--fit", str, "cover"))
        elif cmd == "light":
            out = lighting(argv[1], argv[2], _opt(argv, "--shade", float, 85),
                           _opt(argv, "--light", float, 50))
        elif cmd == "displace":
            out = displace(argv[1], argv[2], _opt(argv, "--scale", int, 8))
        elif cmd == "batch":
            out = batch(argv[1], argv[3:], argv[2])
        elif cmd == "colorways":
            out = colorways(argv[1], dict(a.split("=", 1) for a in argv[3:]), argv[2])
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
