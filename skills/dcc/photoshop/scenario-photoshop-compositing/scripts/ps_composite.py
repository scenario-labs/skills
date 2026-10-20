"""
ps_composite: put an element (a cut-out photo or a Scenario result) into a scene the way
compositors do it by hand: mask, edge clean-up, contact and cast shadows, tone and grain matched
to the surroundings. Every edit is one named History state; every match reports before and after.

Library:
  import ps_composite as C
  C.subject_mask(layer)                 # Select Subject on that layer, as its layer mask
  C.channel_pick(keep, drop)            # channel (gray, red, green, blue) that best separates two
                                        # regions ([l,t,r,b] each), for Blend If or a channel mask
  C.blend_if(layer, channel="gray", this=None, under=None)
                                        # Blend If sliders: (black_lo, black_hi, white_lo, white_hi)
  C.fix_halo(layer, px=1)               # Minimum on the layer mask (made from transparency if
                                        # missing); returns halo numbers before and after
  C.shadows(layer, angle=135, contact=True, cast=True, color=(20, 18, 16))
                                        # Multiply layers under the element; angle = light from
  C.match_tone(layer, strength=0.5)     # clipped Curves moving the element's color cast toward
                                        # the scene ring around it, luminance kept
  C.match_grain(layer, name=None)       # clipped Overlay noise until texture energy matches the
                                        # ring (only adds, never removes grain); trials step
                                        # back, so one named state remains (checked, else raises).
                                        # Layer "Grain match: <layer>", one per element; a layer
                                        # of that name clipped to another element raises
Shell:
  python3 ps_composite.py mask LAYER | pick L,T,R,B L,T,R,B | blendif LAYER [--channel gray]
      [--this a,b,c,d] [--under a,b,c,d] | halo LAYER [--px 1] | shadows LAYER [--angle 135]
      | tone LAYER [--strength 0.5] | grain LAYER

Sources: compositing videos summarized in the skill (contact then cast shadow, Minimum on the
mask for fringes, Blend If by the channel with the most contrast, grain clipped to AI patches).
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scenario-photoshop-expert", "scripts"))
import ps_audit as A  # noqa: E402
import ps_gates as G  # noqa: E402
import ps_run  # noqa: E402

HELPERS_JS = r"""
var ARGS = %ARGS%;
function pc_c(s) { return charIDToTypeID(s); }
function pc_s(s) { return stringIDToTypeID(s); }
function pc_find(c, key) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if ((typeof key === "number" && l.id === key) || (typeof key === "string" && l.name === key)) return l;
    if (l.typename === "LayerSet") { var r = pc_find(l, key); if (r) return r; }
  }
  return null;
}
function pc_layer(key) {
  var l = pc_find(app.activeDocument, key);
  if (!l) throw new Error("layer not found: " + key);
  if (l.typename === "LayerSet") throw new Error("needs a layer, not a group: " + key);
  app.activeDocument.activeLayer = l;
  return l;
}
function pc_has_mask() {
  var r = new ActionReference(); r.putEnumerated(pc_c("Lyr "), pc_c("Ordn"), pc_c("Trgt"));
  return executeActionGet(r).getBoolean(pc_s("hasUserMask"));
}
function pc_target(chan) {
  var r = new ActionReference(); r.putEnumerated(pc_c("Chnl"), pc_c("Chnl"), pc_c(chan));
  var d = new ActionDescriptor(); d.putReference(pc_c("null"), r);
  executeAction(pc_c("slct"), d, DialogModes.NO);
}
function pc_mask_from_selection() {
  var desc = new ActionDescriptor(); desc.putClass(pc_c("Nw  "), pc_c("Chnl"));
  var ref = new ActionReference(); ref.putEnumerated(pc_c("Chnl"), pc_c("Chnl"), pc_c("Msk "));
  desc.putReference(pc_c("At  "), ref);
  desc.putEnumerated(pc_c("Usng"), pc_c("UsrM"), pc_c("RvlS"));
  executeAction(pc_c("Mk  "), desc, DialogModes.NO);
}
function pc_select_transparency(id) {
  var desc = new ActionDescriptor(), ref = new ActionReference();
  ref.putProperty(pc_c("Chnl"), pc_c("fsel")); desc.putReference(pc_c("null"), ref);
  var r2 = new ActionReference(); r2.putEnumerated(pc_c("Chnl"), pc_c("Chnl"), pc_c("Trsp"));
  r2.putIdentifier(pc_c("Lyr "), id);
  desc.putReference(pc_c("T   "), r2);
  executeAction(pc_c("setd"), desc, DialogModes.NO);
}
// A layer mask hides pixels the transparency still holds, so a silhouette cut from transparency
// alone keeps them: a full-frame plate under a subject mask cast a rectangular shadow.
function pc_intersect_user_mask(id) {
  var r = new ActionReference(); r.putIdentifier(pc_c("Lyr "), id);
  var ld = executeActionGet(r);
  if (!ld.getBoolean(pc_s("hasUserMask"))) return false;
  if (ld.hasKey(pc_s("userMaskEnabled")) && !ld.getBoolean(pc_s("userMaskEnabled"))) return false;
  var desc = new ActionDescriptor(), ref = new ActionReference();
  ref.putEnumerated(pc_c("Chnl"), pc_c("Chnl"), pc_c("Msk ")); ref.putIdentifier(pc_c("Lyr "), id);
  desc.putReference(pc_c("null"), ref);
  var w = new ActionReference(); w.putProperty(pc_c("Chnl"), pc_c("fsel"));
  desc.putReference(pc_c("With"), w);
  executeAction(pc_c("Intr"), desc, DialogModes.NO);
  return true;
}
// Topmost layer of l's clipping stack. A layer inserted between l and its clipped layers
// unclips them all, so new clipped layers go above this one.
function pc_chain_top(l) {
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
// The base of a clipped layer: the first layer below it that is not clipped.
function pc_clip_base(x) {
  var p = x.parent, idx = -1;
  for (var i = 0; i < p.layers.length; i++) if (p.layers[i].id === x.id) { idx = i; break; }
  for (var j = idx + 1; j < p.layers.length; j++) {
    var y = p.layers[j], g = false;
    try { g = y.grouped; } catch (e) {}
    if (!g) return y;
  }
  return null;
}
function pc_bounds(l) {
  return [l.bounds[0].as("px"), l.bounds[1].as("px"), l.bounds[2].as("px"), l.bounds[3].as("px")];
}
function pc_fill(rgb) {
  var c = new SolidColor(); c.rgb.red = rgb[0]; c.rgb.green = rgb[1]; c.rgb.blue = rgb[2];
  app.activeDocument.selection.fill(c);
}
if (app.documents.length === 0) throw new Error("no document open");
var d = app.activeDocument;
"""

MASK_JS = r"""
var l = pc_layer(ARGS.layer);
if (pc_has_mask()) throw new Error("layer already has a mask: apply or delete it first");
var desc = new ActionDescriptor(); desc.putBoolean(pc_s("sampleAllLayers"), false);
executeAction(pc_s("autoCutout"), desc, DialogModes.NO);
var ok = true; try { d.selection.bounds; } catch (e) { ok = false; }
if (!ok) throw new Error("Select Subject found nothing on " + l.name);
pc_mask_from_selection();
d.selection.deselect();
return {layer: l.name, id: l.id};
"""

BLEND_IF_JS = r"""
var l = pc_layer(ARGS.layer);
var chans = {gray: "Gry ", red: "Rd  ", green: "Grn ", blue: "Bl  "};
if (!chans[ARGS.channel]) throw new Error("channel must be gray, red, green or blue");
var desc = new ActionDescriptor(), ref = new ActionReference();
ref.putEnumerated(pc_c("Lyr "), pc_c("Ordn"), pc_c("Trgt")); desc.putReference(pc_c("null"), ref);
var lyr = new ActionDescriptor(), list = new ActionList(), br = new ActionDescriptor();
var cref = new ActionReference(); cref.putEnumerated(pc_c("Chnl"), pc_c("Chnl"), pc_c(chans[ARGS.channel]));
br.putReference(pc_c("Chnl"), cref);
var t = ARGS.this_, u = ARGS.under;
br.putInteger(pc_s("srcBlackMin"), t[0]); br.putInteger(pc_s("srcBlackMax"), t[1]);
br.putInteger(pc_s("srcWhiteMin"), t[2]); br.putInteger(pc_s("srcWhiteMax"), t[3]);
br.putInteger(pc_s("destBlackMin"), u[0]); br.putInteger(pc_s("destBlackMax"), u[1]);
br.putInteger(pc_s("destWhiteMin"), u[2]); br.putInteger(pc_s("destWhiteMax"), u[3]);
list.putObject(pc_s("blendRange"), br);
lyr.putList(pc_s("blendRange"), list);
desc.putObject(pc_c("T   "), pc_c("Lyr "), lyr);
executeAction(pc_c("setd"), desc, DialogModes.NO);
// The layer descriptor never reports blend ranges: check the effect with ps_gates instead.
return {layer: l.name, channel: ARGS.channel, this_: t, under: u};
"""

HALO_FIX_JS = r"""
var l = pc_layer(ARGS.layer), made = false;
if (!pc_has_mask()) {
  pc_select_transparency(l.id);
  pc_mask_from_selection();
  d.selection.deselect();
  made = true;
}
pc_target("Msk ");
var m = new ActionDescriptor(); m.putUnitDouble(pc_c("Rds "), pc_c("#Pxl"), ARGS.px);
m.putEnumerated(pc_s("preserveShape"), pc_s("preserveShape"), pc_s("roundness"));
executeAction(pc_c("Mnm "), m, DialogModes.NO);
pc_target("RGB ");
return {layer: l.name, mask_made_from_transparency: made, minimum_px: ARGS.px};
"""

SHADOWS_JS = r"""
var l = pc_layer(ARGS.layer), b = pc_bounds(l), h = b[3] - b[1], out = {layer: l.name, made: []};
if (h <= 0) throw new Error("layer is empty: " + l.name);
// The contact shadow hugs the base; the cast shadow falls away from the light.
function silhouette(name) {
  var s = d.artLayers.add(); s.name = name;
  s.move(l, ElementPlacement.PLACEAFTER);
  d.activeLayer = s;
  pc_select_transparency(l.id);
  out.masked = pc_intersect_user_mask(l.id);
  pc_fill(ARGS.color); d.selection.deselect();
  s.blendMode = BlendMode.MULTIPLY;
  return s;
}
var rad = ARGS.angle * Math.PI / 180;
if (ARGS.cast) {
  var c = silhouette(ARGS.prefix + "Shadow (cast)");
  // Squash toward the base, then skew away from the light: one free transform.
  var t = new ActionDescriptor(), ref = new ActionReference();
  ref.putEnumerated(pc_c("Lyr "), pc_c("Ordn"), pc_c("Trgt")); t.putReference(pc_c("null"), ref);
  t.putEnumerated(pc_c("FTcs"), pc_c("QCSt"), pc_c("Qcs6"));
  t.putUnitDouble(pc_c("Hght"), pc_c("#Prc"), ARGS.cast_height * 100);
  t.putUnitDouble(pc_c("Wdth"), pc_c("#Prc"), 100);
  var sk = new ActionDescriptor();
  var lean = Math.max(-70, Math.min(70, -Math.cos(rad) * ARGS.cast_lean));
  sk.putUnitDouble(pc_c("Hrzn"), pc_c("#Ang"), lean); sk.putUnitDouble(pc_c("Vrtc"), pc_c("#Ang"), 0);
  t.putObject(pc_c("Skew"), pc_c("Pnt "), sk);
  executeAction(pc_c("Trnf"), t, DialogModes.NO);
  c.applyGaussianBlur(Math.max(1, Math.round(h * ARGS.cast_blur * 10) / 10));
  c.opacity = ARGS.cast_opacity;
  out.made.push({name: c.name, id: c.id, bounds: pc_bounds(c), lean_deg: Math.round(lean)});
}
if (ARGS.contact) {
  var k = silhouette(ARGS.prefix + "Shadow (contact)");
  k.translate(0, Math.max(1, Math.round(h * 0.01)));
  k.applyGaussianBlur(Math.max(1, Math.round(h * ARGS.contact_blur * 10) / 10));
  k.opacity = ARGS.contact_opacity;
  out.made.push({name: k.name, id: k.id, bounds: pc_bounds(k)});
}
d.activeLayer = l;
out.element_bounds = b;
return out;
"""

CURVES_JS = r"""
var l = pc_layer(ARGS.layer);
pc_target("RGB ");
d.activeLayer = pc_chain_top(l);
var desc = new ActionDescriptor(), ref = new ActionReference();
ref.putClass(pc_c("AdjL")); desc.putReference(pc_c("null"), ref);
var lay = new ActionDescriptor(), crv = new ActionDescriptor();
crv.putEnumerated(pc_s("presetKind"), pc_s("presetKindType"), pc_s("presetKindDefault"));
lay.putObject(pc_c("Type"), pc_c("Crvs"), crv);
lay.putBoolean(pc_c("Grup"), true);
desc.putObject(pc_c("Usng"), pc_c("AdjL"), lay);
executeAction(pc_c("Mk  "), desc, DialogModes.NO);
var a = d.activeLayer; a.name = ARGS.name;
var sd = new ActionDescriptor(), sref = new ActionReference();
sref.putEnumerated(pc_c("AdjL"), pc_c("Ordn"), pc_c("Trgt")); sd.putReference(pc_c("null"), sref);
var c2 = new ActionDescriptor();
c2.putEnumerated(pc_s("presetKind"), pc_s("presetKindType"), pc_s("presetKindCustom"));
var adjs = new ActionList(), ids = {red: "Rd  ", green: "Grn ", blue: "Bl  "};
for (var ch in ARGS.points) {
  var ca = new ActionDescriptor(), cref = new ActionReference();
  cref.putEnumerated(pc_c("Chnl"), pc_c("Chnl"), pc_c(ids[ch])); ca.putReference(pc_c("Chnl"), cref);
  var pts = new ActionList(), xy = [[0, 0], ARGS.points[ch], [255, 255]];
  for (var i = 0; i < xy.length; i++) {
    var p = new ActionDescriptor();
    p.putDouble(pc_c("Hrzn"), xy[i][0]); p.putDouble(pc_c("Vrtc"), xy[i][1]);
    pts.putObject(pc_c("Pnt "), p);
  }
  ca.putList(pc_c("Crv "), pts); adjs.putObject(pc_c("CrvA"), ca);
}
c2.putList(pc_c("Adjs"), adjs);
sd.putObject(pc_c("T   "), pc_c("Crvs"), c2);
executeAction(pc_c("setd"), sd, DialogModes.NO);
var clipped = false; try { clipped = a.grouped; } catch (e) {}
return {layer: a.name, id: a.id, clipped_to: l.name, clipped: clipped};
"""

# Reuse only this element's own grain layer (a rerun). A layer of that name clipped to another
# element is that element's grain: refilling it would change finished work.
GRAIN_CHECK_JS = r"""
var l = pc_layer(ARGS.layer);
var g = pc_find(d, ARGS.name);
if (g) {
  var gb = null, gc = false;
  try { gc = g.grouped; } catch (e) {}
  if (gc) gb = pc_clip_base(g);
  if (!gb || gb.id !== l.id)
    throw new Error("layer '" + ARGS.name + "' exists and is not clipped to '" + l.name +
                    "': pass another name=");
}
"""

GRAIN_JS = GRAIN_CHECK_JS + r"""
if (!g) {
  // Directly above the chain top, moved there: artLayers.add() lands at the top of the stack
  // (measured on 27.11), where the clip would take whatever layer is on top.
  var chainTop = pc_chain_top(l);
  g = d.artLayers.add(); g.name = ARGS.name;
  g.move(chainTop, ElementPlacement.PLACEBEFORE);
  d.activeLayer = g;
  // Moved inside a clipping chain, the layer is clipped already, and setting grouped toggles the
  // clip (measured): set it only when false, then check.
  if (!g.grouped) g.grouped = true;
  if (!g.grouped) throw new Error("could not clip " + ARGS.name + " to " + l.name);
  g.blendMode = BlendMode.OVERLAY;
}
d.activeLayer = g;
d.selection.selectAll(); pc_fill([128, 128, 128]); d.selection.deselect();
if (ARGS.amount > 0) g.applyAddNoise(ARGS.amount, NoiseDistribution.GAUSSIAN, true);
return {layer: g.name, id: g.id, amount: ARGS.amount};
"""


def _run(js, args, undo=None, timeout=240):
    body = HELPERS_JS.replace("%ARGS%", json.dumps(args)) + js
    res = ps_run.run(body, undo=undo, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError("%s (line %s)" % (res.get("error"), res.get("line")))
    return res["result"]


def _key(v):
    return int(v) if isinstance(v, str) and v.isdigit() else v


def subject_mask(layer, undo="Scenario: Subject mask"):
    return _run(MASK_JS, {"layer": _key(layer)}, undo=undo)


def channel_pick(keep, drop):
    """Separation per channel: |mean_keep - mean_drop| / pooled std. Higher separates better."""
    a, b = G.stats(None, keep), G.stats(None, drop)
    scores = {}
    for ch in ("red", "green", "blue"):
        pooled = math.sqrt((a[ch]["std"] ** 2 + b[ch]["std"] ** 2) / 2) or 1.0
        scores[ch] = round(abs(a[ch]["mean"] - b[ch]["mean"]) / pooled, 2)
    lum_gap = abs(a["luminance"] - b["luminance"])
    best = max(scores, key=scores.get)
    return {"best": best, "scores": scores, "luminance_gap": round(lum_gap, 1),
            "keep_mean": [a[c]["mean"] for c in ("red", "green", "blue")],
            "drop_mean": [b[c]["mean"] for c in ("red", "green", "blue")]}


def blend_if(layer, channel="gray", this=None, under=None, undo="Scenario: Blend If"):
    this = list(this or (0, 0, 255, 255))
    under = list(under or (0, 0, 255, 255))
    return _run(BLEND_IF_JS, {"layer": _key(layer), "channel": channel, "this_": this,
                              "under": under}, undo=undo)


def fix_halo(layer, px=1, band=2, undo="Scenario: Clean edge"):
    before = G.halo(layer, band)
    out = _run(HALO_FIX_JS, {"layer": _key(layer), "px": float(px)}, undo=undo)
    after = G.halo(layer, band)
    out["before"] = {"light_rim": before["light_rim"], "dark_rim": before["dark_rim"]}
    out["after"] = {"light_rim": after["light_rim"], "dark_rim": after["dark_rim"]}
    return out


def shadows(layer, angle=135, contact=True, cast=True, color=(20, 18, 16), cast_height=0.35,
            cast_lean=45, cast_blur=0.03, cast_opacity=45, contact_blur=0.008,
            contact_opacity=80, prefix="", undo="Scenario: Shadows"):
    """angle: where the light comes from, in degrees (0 = right, 90 = top, 135 = top left).
    The silhouette is the layer's transparency cut by its layer mask when the mask is on."""
    return _run(SHADOWS_JS, {"layer": _key(layer), "angle": angle, "contact": contact,
                             "cast": cast, "color": list(color), "cast_height": cast_height,
                             "cast_lean": cast_lean, "cast_blur": cast_blur,
                             "cast_opacity": cast_opacity, "contact_blur": contact_blur,
                             "contact_opacity": contact_opacity, "prefix": prefix}, undo=undo)


def _measure(layer, ring, gap):
    el = G.stats(layer, {"alpha": _key(layer), "contract": 2})
    sc = G.stats(None, {"alpha": _key(layer), "ring": ring, "gap": gap})
    return el, sc


def match_tone(layer, strength=0.5, ring=40, gap=4, name="Tone match",
               undo="Scenario: Match tone"):
    """Moves the element's color cast (each channel's ratio to luminance) toward the scene ring's
    cast by `strength`. Luminance and contrast stay: grade those by eye toward the key light."""
    el, sc = _measure(layer, ring, gap)
    points, chans = {}, ("red", "green", "blue")
    for ch in chans:
        m = el[ch]["mean"]
        el_ratio = m / max(el["luminance"], 1.0)
        sc_ratio = sc[ch]["mean"] / max(sc["luminance"], 1.0)
        target = m * (1 + strength * (sc_ratio / max(el_ratio, 1e-3) - 1))
        points[ch] = [round(min(max(m, 1), 254), 1), round(min(max(target, 1), 254), 1)]
    out = _run(CURVES_JS, {"layer": _key(layer), "points": points, "name": name}, undo=undo)
    after = G.stats(None, {"alpha": _key(layer), "contract": 2})

    def cast(s):
        return [round(s[c]["mean"] / max(s["luminance"], 1.0), 3) for c in chans]
    out.update({"strength": strength, "points": points, "cast_before": cast(el),
                "cast_after": cast(after), "cast_scene": cast(sc),
                "luminance_before": el["luminance"], "luminance_after": after["luminance"]})
    return out


def match_grain(layer, ring=40, gap=4, name=None, amounts=(1.5, 3, 5, 8, 12),
                radius=1.5, undo="Scenario: Match grain"):
    """Grain for one element: an Overlay noise layer clipped to it, named "Grain match: <layer>"
    unless `name` is given. A rerun on the same element reuses its layer; a layer of that name
    clipped to another element raises. `end` is the chosen trial's energy (the final apply draws
    new noise of the same amount)."""
    k = _key(layer)
    name = name or "Grain match: %s" % layer
    inside = {"alpha": k, "contract": 3}
    outside = {"alpha": k, "ring": ring, "gap": gap}
    target = G.texture(None, outside, radius)["energy"]
    start = G.texture(None, inside, radius)["energy"]
    out = {"target": target, "start": start, "tries": []}
    if start >= 0.9 * target:
        out["action"] = "none: the element already has at least the scene's grain"
        return out
    _run(GRAIN_CHECK_JS + "return true;", {"layer": k, "name": name})   # refuses before any state
    # Each trial is one state on top of the mark, measured, then stepped back by state (never by
    # list length or index: gates leave redo states, and the index stops moving at the History
    # limit). The final pick is the one state left.
    h0 = A.history()
    best = None
    for a in amounts:
        _run(GRAIN_JS, {"layer": k, "name": name, "amount": a}, undo=undo)
        e = G.texture(None, inside, radius)["energy"]
        A.step_back(h0, undo)
        out["tries"].append([a, e])
        if best is None or abs(e - target) < abs(best[1] - target):
            best = (a, e)
        if e >= target:
            break
    _run(GRAIN_JS, {"layer": k, "name": name, "amount": best[0]}, undo=undo)
    probs = A.history_gate(h0, undo)
    if probs:
        raise RuntimeError("match_grain left History wrong: " + "; ".join(probs))
    out.update({"amount": best[0], "end": best[1], "layer": name})
    return out


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        return cast(argv[argv.index(flag) + 1])
    return default


def _quad(s):
    return [int(x) for x in s.split(",")] if s else None


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    try:
        if cmd == "mask":
            out = subject_mask(argv[1])
        elif cmd == "pick":
            out = channel_pick(_quad(argv[1]), _quad(argv[2]))
        elif cmd == "blendif":
            out = blend_if(argv[1], _opt(argv, "--channel", str, "gray"),
                           _quad(_opt(argv, "--this")), _quad(_opt(argv, "--under")))
        elif cmd == "halo":
            out = fix_halo(argv[1], _opt(argv, "--px", float, 1))
        elif cmd == "shadows":
            out = shadows(argv[1], _opt(argv, "--angle", float, 135))
        elif cmd == "tone":
            out = match_tone(argv[1], _opt(argv, "--strength", float, 0.5))
        elif cmd == "grain":
            out = match_grain(argv[1])
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
