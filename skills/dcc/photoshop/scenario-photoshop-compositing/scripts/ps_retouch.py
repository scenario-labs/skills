"""
ps_retouch: non-destructive portrait retouch scaffolds for Photoshop, built the way retouchers
build them by hand, each as ONE named History state, each with a measurable check.

Library:
  import ps_retouch as RT
  RT.suggest_radius(region=None)   # blur radius where fine texture just disappears (energy curve)
  RT.frequency_separation(radius=None, source="visible")
                                   # group "Frequency Separation": Low Frequency (Color/Tone),
                                   # empty clipped "Retouch (tone)", High Frequency (Texture) in
                                   # Linear Light; Apply Image branch picked from the bit depth
  RT.verify_fs(group="Frequency Separation", reference=None)
                                   # |FS group - source| (max <= 2 at 8-bit, 0 to 1 at 16-bit)
  RT.highpass_smoother(r1=None, r2=None)
                                   # inverted High Pass stack: Smart Object, Vivid Light, High Pass
                                   # then Gaussian as Smart Filters, hide-all mask to paint in
  RT.dodge_burn()                  # "Dodge" and "Burn" Curves layers with black masks
  RT.skin_tone(region="selection") # mean color, vectorscope angle vs the 123 degree skin line
Shell:
  python3 ps_retouch.py radius [--region l,t,r,b|selection]
  python3 ps_retouch.py fs [--radius R] [--source visible|layer]
  python3 ps_retouch.py verify [--group NAME] [--reference NAME]
  python3 ps_retouch.py smoother [--r1 R] [--r2 R]
  python3 ps_retouch.py dodgeburn
  python3 ps_retouch.py skin [--region selection|l,t,r,b]

Sources: Apply Image values and the clipped Lighten retouch layer from Photoshop Training
Channel's frequency separation lesson; radii and the inverted High Pass stack from the retouching
videos summarized in the skill. Radii scale with pixel size and face size: always look.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scenario-photoshop-expert", "scripts"))
import ps_gates  # noqa: E402
import ps_run  # noqa: E402

HELPERS_JS = r"""
var ARGS = %ARGS%;
function pr_c(s) { return charIDToTypeID(s); }
function pr_s(s) { return stringIDToTypeID(s); }
function pr_bits(d) {
  return ({"BitsPerChannelType.EIGHT": 8, "BitsPerChannelType.SIXTEEN": 16,
           "BitsPerChannelType.THIRTYTWO": 32})[String(d.bitsPerChannel)];
}
// Stamp the visible image into a new top-of-stack pixel layer (Cmd+Opt+Shift+E).
function pr_stamp(d, name) {
  var top = d.layers[0];
  var l = d.artLayers.add(); l.move(top, ElementPlacement.PLACEBEFORE);
  d.activeLayer = l;
  var desc = new ActionDescriptor(); desc.putBoolean(pr_c("Dplc"), true);
  executeAction(pr_c("MrgV"), desc, DialogModes.NO);
  d.activeLayer.name = name;
  return d.activeLayer;
}
// Adjustment layers arrive with a white mask: invert it instead of making a second one.
function pr_black_existing_mask() {
  var r = new ActionReference(); r.putEnumerated(pr_c("Chnl"), pr_c("Chnl"), pr_c("Msk "));
  var dd = new ActionDescriptor(); dd.putReference(pr_c("null"), r);
  executeAction(pr_c("slct"), dd, DialogModes.NO);
  executeAction(pr_c("Invr"), new ActionDescriptor(), DialogModes.NO);
}
function pr_mask(hide) {
  var desc = new ActionDescriptor();
  desc.putClass(pr_c("Nw  "), pr_c("Chnl"));
  var ref = new ActionReference(); ref.putEnumerated(pr_c("Chnl"), pr_c("Chnl"), pr_c("Msk "));
  desc.putReference(pr_c("At  "), ref);
  desc.putEnumerated(pr_c("Usng"), pr_c("UsrM"), pr_c(hide ? "HdAl" : "RvlA"));
  executeAction(pr_c("Mk  "), desc, DialogModes.NO);
}
// Target the layer's color channels: with a layer mask targeted, Make adjustment layer is refused.
function pr_target_rgb() {
  var r = new ActionReference(); r.putEnumerated(pr_c("Chnl"), pr_c("Chnl"), pr_c("RGB "));
  var dd = new ActionDescriptor(); dd.putReference(pr_c("null"), r);
  try { executeAction(pr_c("slct"), dd, DialogModes.NO); } catch (e) {}
}
function pr_curves(name, mid_out) {
  pr_target_rgb();
  // Make with the default preset, then set the points: a Make carrying the points is refused.
  var desc = new ActionDescriptor(), ref = new ActionReference();
  ref.putClass(pr_c("AdjL")); desc.putReference(pr_c("null"), ref);
  var lay = new ActionDescriptor(), crv = new ActionDescriptor();
  crv.putEnumerated(pr_s("presetKind"), pr_s("presetKindType"), pr_s("presetKindDefault"));
  lay.putObject(pr_c("Type"), pr_c("Crvs"), crv);
  desc.putObject(pr_c("Usng"), pr_c("AdjL"), lay);
  executeAction(pr_c("Mk  "), desc, DialogModes.NO);
  var l = app.activeDocument.activeLayer; l.name = name;
  var sd = new ActionDescriptor(), sref = new ActionReference();
  sref.putEnumerated(pr_c("AdjL"), pr_c("Ordn"), pr_c("Trgt")); sd.putReference(pr_c("null"), sref);
  var c2 = new ActionDescriptor();
  c2.putEnumerated(pr_s("presetKind"), pr_s("presetKindType"), pr_s("presetKindCustom"));
  var adjs = new ActionList(), ca = new ActionDescriptor(), cref = new ActionReference();
  cref.putEnumerated(pr_c("Chnl"), pr_c("Chnl"), pr_c("Cmps")); ca.putReference(pr_c("Chnl"), cref);
  var pts = new ActionList(), xy = [[0, 0], [128, mid_out], [255, 255]];
  for (var i = 0; i < xy.length; i++) {
    var p = new ActionDescriptor();
    p.putDouble(pr_c("Hrzn"), xy[i][0]); p.putDouble(pr_c("Vrtc"), xy[i][1]);
    pts.putObject(pr_c("Pnt "), p);
  }
  ca.putList(pr_c("Crv "), pts); adjs.putObject(pr_c("CrvA"), ca);
  c2.putList(pr_c("Adjs"), adjs);
  sd.putObject(pr_c("T   "), pr_c("Crvs"), c2);
  executeAction(pr_c("setd"), sd, DialogModes.NO);
  return l;
}
if (app.documents.length === 0) throw new Error("no document open");
var d = app.activeDocument;
"""

RADIUS_JS = r"""
// Energy of fine detail (High Pass 1.5 px std) on a gray copy blurred at each candidate radius.
// The expert stop, "until pores just disappear", is read as the first radius that keeps under
// 25% of the unblurred fine-detail energy.
var src = d, t = psr_dup(src, "pr_radius", true), curve = [], base = null, pick = null;
app.activeDocument = t;
try {
  if (String(t.mode) !== "DocumentMode.RGB") t.changeMode(ChangeMode.RGB);
  if (pr_bits(t) !== 8) t.bitsPerChannel = BitsPerChannelType.EIGHT;
  t.activeLayer.desaturate();
  var r = ARGS.region;
  var hs = t.activeHistoryState;
  for (var i = 0; i < ARGS.radii.length; i++) {
    t.activeHistoryState = hs;
    var rad = ARGS.radii[i];
    if (rad > 0) t.activeLayer.applyGaussianBlur(rad);
    t.activeLayer.applyHighPass(1.5);
    if (r) t.selection.select([[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]]);
    var h = t.channels[0].histogram, n = 0, s = 0, s2 = 0;
    for (var k = 0; k < 256; k++) { n += h[k]; s += k * h[k]; s2 += k * k * h[k]; }
    var m = s / n, e = Math.sqrt(Math.max(0, s2 / n - m * m));
    if (rad === 0) base = e;
    var ratio = base ? Math.round(1000 * e / base) / 1000 : null;
    curve.push({radius: rad, energy: Math.round(e * 100) / 100, ratio: ratio});
    if (pick === null && rad > 0 && ratio !== null && ratio <= ARGS.stop) pick = rad;
    t.selection.deselect();
  }
} finally { psr_close(t); app.activeDocument = src; }
var shortSide = Math.min(src.width.as("px"), src.height.as("px"));
return {pick: pick, curve: curve, short_side: shortSide, stop_ratio: ARGS.stop};
"""

FS_JS = r"""
var bits = pr_bits(d);
if (bits === 32) throw new Error("32-bit documents: convert to 16-bit first (Apply Image recipe)");
var srcLayer;
if (ARGS.source === "layer") {
  srcLayer = d.activeLayer;
  if (srcLayer.typename === "LayerSet") throw new Error("select a pixel layer, not a group");
} else srcLayer = pr_stamp(d, "FS source (stamp visible)");
var radius = ARGS.radius;
if (!radius) {
  var ss = Math.min(d.width.as("px"), d.height.as("px"));
  radius = Math.max(2, Math.min(12, Math.round(ss / 600 * 10) / 10));
}
d.activeLayer = srcLayer;
var low = srcLayer.duplicate(); low.name = "Low Frequency (Color/Tone)";
var high = srcLayer.duplicate(); high.name = "High Frequency (Texture)";
try { low.rasterize(RasterizeType.ENTIRELAYER); high.rasterize(RasterizeType.ENTIRELAYER); } catch (e) {}
low.move(srcLayer, ElementPlacement.PLACEBEFORE);
high.move(low, ElementPlacement.PLACEBEFORE);
low.applyGaussianBlur(radius);
d.activeLayer = high;
var w = new ActionDescriptor(), ref = new ActionReference();
ref.putEnumerated(pr_c("Chnl"), pr_c("Chnl"), pr_c("RGB "));
ref.putIdentifier(pr_c("Lyr "), low.id);
w.putReference(pr_c("T   "), ref);
if (bits === 16) w.putBoolean(pr_c("Invr"), true);
w.putEnumerated(pr_c("Clcl"), pr_c("Clcn"), pr_c(bits === 16 ? "Add " : "Sbtr"));
w.putDouble(pr_c("Scl "), 2);
w.putInteger(pr_c("Ofst"), bits === 16 ? 0 : 128);
var ai = new ActionDescriptor(); ai.putObject(pr_c("With"), pr_c("Clcl"), w);
executeAction(pr_c("AppI"), ai, DialogModes.NO);
high.blendMode = BlendMode.LINEARLIGHT;
var g = d.layerSets.add(); g.name = ARGS.group;
g.move(high, ElementPlacement.PLACEBEFORE);
low.move(g, ElementPlacement.INSIDE);
high.move(g, ElementPlacement.INSIDE);
high.move(g, ElementPlacement.PLACEATBEGINNING);
var rt = null;
if (ARGS.retouch_layer) {
  rt = d.artLayers.add(); rt.name = "Retouch (tone)";
  rt.move(low, ElementPlacement.PLACEBEFORE);
  rt.grouped = true;
}
if (ARGS.source !== "layer") srcLayer.visible = false;
d.activeLayer = rt || low;
return {group: g.name, group_id: g.id, low: low.name, high: high.name,
        retouch: rt ? rt.name : null, source: srcLayer.name, source_id: srcLayer.id,
        radius: radius, bits: bits,
        recipe: bits === 16 ? "Apply Image: Add, Scale 2, Offset 0, Invert on"
                            : "Apply Image: Subtract, Scale 2, Offset 128"};
"""

SMOOTHER_JS = r"""
var base = pr_stamp(d, "Smoother (inverted High Pass)");
var ss = Math.min(d.width.as("px"), d.height.as("px"));
var r1 = ARGS.r1 || Math.max(8, Math.round(ss / 100));
var r2 = ARGS.r2 || Math.max(1, Math.round(r1 / 8 * 10) / 10);
base.invert();
d.activeLayer = base;
executeAction(pr_s("newPlacedLayer"), new ActionDescriptor(), DialogModes.NO);
var so = d.activeLayer;
so.blendMode = BlendMode.VIVIDLIGHT;
so.applyHighPass(r1);
so.applyGaussianBlur(r2);
pr_mask(true);
return {layer: so.name, id: so.id, r1: r1, r2: r2,
        next: "fill the mask white at 20 to 50% through a skin selection (minus eyes, brows, lips, hair)"};
"""

DODGE_BURN_JS = r"""
var top = d.activeLayer;
var burn = pr_curves("Burn", ARGS.burn_mid); pr_black_existing_mask();
var dodge = pr_curves("Dodge", ARGS.dodge_mid); pr_black_existing_mask();
return {dodge: dodge.name, dodge_id: dodge.id, burn: burn.name, burn_id: burn.id,
        next: "paint or fill the black masks at low flow; Dodge lifts, Burn lowers"};
"""


def _run(js, args, undo=None, timeout=240):
    body = HELPERS_JS.replace("%ARGS%", json.dumps(args)) + js
    res = ps_run.run(body, undo=undo, timeout=timeout)
    if not res.get("ok"):
        raise RuntimeError("%s (line %s)" % (res.get("error"), res.get("line")))
    return res["result"]


def suggest_radius(region=None, radii=(0, 1, 2, 3, 4, 6, 8, 10, 12, 16), stop=0.25):
    if isinstance(region, str):
        region = list(_selection_bounds())
    return _run(RADIUS_JS, {"region": region, "radii": list(radii), "stop": stop})


def _selection_bounds():
    res = ps_run.run("var b = app.activeDocument.selection.bounds;"
                     " return [b[0].as('px'), b[1].as('px'), b[2].as('px'), b[3].as('px')];")
    if not res.get("ok"):
        raise RuntimeError("no active selection: " + str(res.get("error")))
    return res["result"]


def frequency_separation(radius=None, source="visible", group="Frequency Separation",
                         retouch_layer=True, undo="Scenario: Frequency separation"):
    return _run(FS_JS, {"radius": radius, "source": source, "group": group,
                        "retouch_layer": retouch_layer}, undo=undo)


def verify_fs(group="Frequency Separation", reference=None):
    """reference: the layer the FS was built from (default: the stamp FS made)."""
    if reference is None:
        reference = "FS source (stamp visible)"
    return ps_gates.diff(group, reference)


def highpass_smoother(r1=None, r2=None, undo="Scenario: High Pass smoother"):
    return _run(SMOOTHER_JS, {"r1": r1, "r2": r2}, undo=undo)


def dodge_burn(dodge_mid=150, burn_mid=106, undo="Scenario: Dodge and burn layers"):
    return _run(DODGE_BURN_JS, {"dodge_mid": dodge_mid, "burn_mid": burn_mid}, undo=undo)


def skin_tone(region="selection", layer=None):
    s = ps_gates.stats(layer, region)
    s["reading"] = ("on the skin line" if abs(s["skin_line_delta"]) <= 10 else
                    "toward red, magenta or blue" if s["skin_line_delta"] < -10 else
                    "toward yellow, green or cyan")
    return s


def _opt(argv, flag, cast=str, default=None):
    if flag in argv:
        return cast(argv[argv.index(flag) + 1])
    return default


def _region(s):
    if s is None or s in ("selection", "outside"):
        return s
    return [int(float(x)) for x in s.split(",")]


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    try:
        if cmd == "radius":
            out = suggest_radius(_region(_opt(argv, "--region")))
        elif cmd == "fs":
            out = frequency_separation(_opt(argv, "--radius", float), _opt(argv, "--source", str, "visible"))
        elif cmd == "verify":
            out = verify_fs(_opt(argv, "--group", str, "Frequency Separation"), _opt(argv, "--reference"))
        elif cmd == "smoother":
            out = highpass_smoother(_opt(argv, "--r1", float), _opt(argv, "--r2", float))
        elif cmd == "dodgeburn":
            out = dodge_burn()
        elif cmd == "skin":
            out = skin_tone(_region(_opt(argv, "--region", str, "selection")))
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
