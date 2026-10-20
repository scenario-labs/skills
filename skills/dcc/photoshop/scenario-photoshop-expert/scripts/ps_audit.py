"""
ps_audit: read the live Photoshop document as data, and grade it against a delivery profile.
Every scenario-photoshop-* skill gates its stages on these numbers before looking at a preview.

Library (each call is one ps_run job, read only, no history state; step_back moves the active
History state and adds none):
  import ps_audit as A
  A.doc_state()                    # active document: size, ppi, mode, bits, profile, layer tree,
                                   # selection bounds, active layer, saved state, path, history
  A.doc_state(max_layers=400)      # cap on layers walked (big documents)
  A.history()                      # the active History state: {index, name, prev, id, prev_id,
                                   # count, limit, full}; prev is the name of the state below it
  A.history_gate(h0, undo)         # [] when the active state is the ONE new state a job named
                                   # `undo` added on top of h0 (taken right before the call);
                                   # undo=None: [] when the active state is h0 again
  A.step_back(h0, undo)            # the active state, named `undo`, steps back to the one below,
                                   # which must be h0's; raises otherwise
  A.layer_find(name)               # [{id, name, path, kind, bounds, visible}] for an exact name
  A.histogram_clip()               # % of pixels at 0 and 255 per channel on the merged image
  A.deliverable(profile)           # [] = pass, else a list of problems for "web", "print",
                                   # "social", "game-texture", "psd-handoff"; hidden layers in a
                                   # group named "Takes..." are kept takes, not a problem
Shell:
  python3 ps_audit.py state | history | find NAME | clip | deliverable PROFILE

History gates read the active state, never the list length: captures and gates step back and leave
redo states, and at the History limit the oldest state drops, so the index stops moving. The
Action Manager id of each state (`id`, `prev_id`) decides when it is readable; the name and, below
the limit, the index decide otherwise.

Kinds reported for layers: pixel, adjustment, fill, smart_object, text, shape, group, video,
other (from the Action Manager layerKind; the DOM kind misreads shapes and throws on some
adjustment layers). Bounds are [left, top, right, bottom] in pixels.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ps_run  # noqa: E402

KIND_JS = r"""
// Action Manager layerKind, not the DOM's LayerKind: the DOM reports shape layers as SOLIDFILL
// and throws "Internal error" on newer adjustment layers such as Clarity (27.11).
var KINDS = {1: "pixel", 2: "adjustment", 3: "text", 4: "shape", 5: "smart_object", 6: "video",
             7: "group", 9: "fill", 10: "fill", 11: "fill", 12: "pixel"};
function kindOf(l) {
  if (l.typename === "LayerSet") return "group";
  try {
    var r = new ActionReference(); r.putIdentifier(charIDToTypeID("Lyr "), l.id);
    var k = executeActionGet(r).getInteger(stringIDToTypeID("layerKind"));
    if (KINDS[k]) return KINDS[k];
  } catch (e) {}
  return "other";
}
"""

HISTORY_JS = r"""
// The active History state. Steps backward leave redo states in the list, so its length is no gate.
// At the History limit the oldest state drops and the index stops moving; the Action Manager id of
// each state does not change, so it decides when readable.
function psa_history(d) {
  var hs = d.historyStates, a = d.activeHistoryState, hi = -1, snaps = 0;
  for (var q = hs.length - 1; q >= 0; q--) if (hs[q] == a) { hi = q; break; }
  for (var s = 0; s < hs.length; s++) { try { if (hs[s].snapshot) snaps++; } catch (e) {} }
  var lim = null; try { lim = app.preferences.numberOfHistoryStates; } catch (e) {}
  var h = {index: hi, name: a.name, prev: hi > 0 ? hs[hi - 1].name : null, id: null, prev_id: null,
           count: hs.length, limit: lim,
           full: lim !== null && hi === hs.length - 1 && hs.length - snaps >= lim};
  try {
    var kid = stringIDToTypeID("ID"), kix = stringIDToTypeID("itemIndex");
    var r = new ActionReference();
    r.putProperty(charIDToTypeID("HstS"), charIDToTypeID("CrnH"));   // (Ordn, CrnH) throws on 27.11
    var cur = executeActionGet(r);
    if (cur.hasKey(kid)) h.id = cur.getInteger(kid);
    if (cur.hasKey(kix) && cur.getInteger(kix) > 1) {
      var r2 = new ActionReference(); r2.putIndex(charIDToTypeID("HstS"), cur.getInteger(kix) - 1);
      var pd = executeActionGet(r2);
      if (pd.hasKey(kid)) h.prev_id = pd.getInteger(kid);
    }
  } catch (e) {}
  return h;
}
"""

HIST_ONLY_JS = HISTORY_JS + r"""
if (app.documents.length === 0) throw new Error("no document open");
return psa_history(app.activeDocument);
"""

STEP_BACK_JS = HISTORY_JS + r"""
if (app.documents.length === 0) throw new Error("no document open");
var d = app.activeDocument, h = psa_history(d);
if (h.name !== %UNDO%) throw new Error("step_back: the active History state is '" + h.name + "', not '" + %UNDO% + "'");
if (h.index < 1) throw new Error("step_back: no state below the active one");
d.activeHistoryState = d.historyStates[h.index - 1];
return psa_history(d);
"""

STATE_JS = KIND_JS + HISTORY_JS + r"""
var MAXL = %MAX%;
var count = 0, truncated = false;
function walk(container, path) {
  var out = [];
  for (var i = 0; i < container.layers.length; i++) {
    if (count >= MAXL) { truncated = true; break; }
    var l = container.layers[i]; count++;
    var b = null;
    try { b = [l.bounds[0].as("px"), l.bounds[1].as("px"), l.bounds[2].as("px"),
               l.bounds[3].as("px")]; } catch (e) {}
    var item = {id: l.id, name: l.name, path: path + "/" + l.name, kind: kindOf(l),
                visible: l.visible, opacity: Math.round(l.opacity), blend: String(l.blendMode)
                  .replace("BlendMode.", "").toLowerCase(), bounds: b};
    try { item.locked = l.allLocked; } catch (e) {}
    try { if (l.isBackgroundLayer) item.background = true; } catch (e) {}
    try { if (l.grouped) item.clipped = true; } catch (e) {}
    if (l.typename === "LayerSet") item.children = walk(l, item.path);
    out.push(item);
  }
  return out;
}
if (app.documents.length === 0) return {open: false};
var d = app.activeDocument;
var sel = null;
try { var sb = d.selection.bounds; sel = [sb[0].as("px"), sb[1].as("px"), sb[2].as("px"),
                                          sb[3].as("px")]; } catch (e) { sel = null; }
var prof = null; try { prof = d.colorProfileName; } catch (e) { prof = "untagged"; }
var path = null; try { path = d.fullName.fsName; } catch (e) {}
var al = null; try { al = {id: d.activeLayer.id, name: d.activeLayer.name}; } catch (e) {}
var hist = psa_history(d);
return {open: true, name: d.name, id: d.id, path: path, saved: d.saved, width: d.width.as("px"),
        height: d.height.as("px"), ppi: d.resolution, mode: String(d.mode).replace("DocumentMode.", "")
          .toLowerCase(), bits: ({"BitsPerChannelType.ONE": 1, "BitsPerChannelType.EIGHT": 8,
          "BitsPerChannelType.SIXTEEN": 16, "BitsPerChannelType.THIRTYTWO": 32})[String(d.bitsPerChannel)],
        profile: prof, layers: walk(d, ""), layer_count_walked: count, truncated: truncated,
        selection: sel, active_layer: al, history: hist, documents_open: app.documents.length};
"""

FIND_JS = KIND_JS + r"""
var target = %NAME%, hits = [];
function walk(c, path) {
  for (var i = 0; i < c.layers.length; i++) {
    var l = c.layers[i];
    if (l.name === target) {
      var b = null;
      try { b = [l.bounds[0].as("px"), l.bounds[1].as("px"), l.bounds[2].as("px"),
                 l.bounds[3].as("px")]; } catch (e) {}
      hits.push({id: l.id, name: l.name, path: path + "/" + l.name, kind: kindOf(l),
                 bounds: b, visible: l.visible});
    }
    if (l.typename === "LayerSet") walk(l, path + "/" + l.name);
  }
}
if (app.documents.length === 0) return [];
walk(app.activeDocument, "");
return hits;
"""

CLIP_JS = r"""
// Channel.histogram reads the active layer, so measure a flattened copy of the whole image.
if (app.documents.length === 0) throw new Error("no document open");
var src = app.activeDocument, out = {};
var d = psr_dup(src, "psr_clip", true);
app.activeDocument = d;
try {
  try { d.flatten(); } catch (e) {}
  if (String(d.mode) !== "DocumentMode.RGB") out.skipped = "mode " + d.mode;
  else {
    var names = ["red", "green", "blue"];
    for (var c = 0; c < 3; c++) {
      var h = d.channels[c].histogram, total = 0;
      for (var i = 0; i < 256; i++) total += h[i];
      out[names[c]] = {black_pct: Math.round(1000 * h[0] / total) / 10,
                       white_pct: Math.round(1000 * h[255] / total) / 10};
    }
  }
} finally { psr_close(d); app.activeDocument = src; }
return out;
"""

PROFILES = {
    # name: (color mode, bits, profile substring or None, max long edge, min long edge, ppi)
    "web": ("rgb", 8, "sRGB", 4096, 600, None),
    "social": ("rgb", 8, "sRGB", 4096, 1080, None),
    "print": (None, None, None, None, 2400, 300),
    "game-texture": ("rgb", 8, None, 8192, 256, None),
    "psd-handoff": (None, None, None, None, None, None),
}


def _run(js, **kw):
    res = ps_run.run(js, timeout=kw.pop("timeout", 120), **kw)
    if not res.get("ok"):
        raise RuntimeError(res.get("error"))
    return res["result"]


def doc_state(max_layers=400):
    return _run(STATE_JS.replace("%MAX%", str(int(max_layers))))


def history():
    return _run(HIST_ONLY_JS)


def _full(h):
    return bool(h.get("full")) or bool(h.get("limit") and h.get("count", 0) >= h["limit"])


def history_problems(h0, h1, undo=None):
    """[] when h1 is the one state a job named `undo` added on top of h0; with undo=None, [] when
    h1 is h0's state again. Pure function over two history() results."""
    probs = []
    ids = h0.get("id") is not None and h1.get("id") is not None
    if undo is None:
        if ids:
            if h1["id"] != h0["id"]:
                probs.append("active state %r is not the marked state %r" % (h1["name"], h0["name"]))
        elif (h1["name"], h1.get("prev")) != (h0["name"], h0.get("prev")):
            probs.append("active state %r is not the marked state %r" % (h1["name"], h0["name"]))
        elif not (_full(h0) or _full(h1)) and h1["index"] != h0["index"]:
            probs.append("active index %s, the marked state was at %s" % (h1["index"], h0["index"]))
        return probs
    if h1["name"] != undo:
        probs.append("active state is %r, expected %r" % (h1["name"], undo))
    if ids and h1["id"] == h0["id"]:
        probs.append("no new History state: the marked state is still active")
    elif ids and h1.get("prev_id") is not None:
        if h1["prev_id"] != h0["id"]:
            probs.append("the state below the active one is not the marked state: more than one "
                         "state was added, or History moved")
    else:
        if h1.get("prev") != h0["name"]:
            probs.append("the state below the active one is %r, not the marked %r"
                         % (h1.get("prev"), h0["name"]))
        # At the History limit the oldest state drops and the index stops moving.
        if not (_full(h0) or _full(h1)) and h1["index"] != h0["index"] + 1:
            probs.append("active index %s, expected %s" % (h1["index"], h0["index"] + 1))
    return probs


def history_gate(h0, undo=None):
    return history_problems(h0, history(), undo)


def step_back(h0, undo):
    h1 = _run(STEP_BACK_JS.replace("%UNDO%", json.dumps(undo)))
    probs = history_problems(h0, h1)
    if probs:
        raise RuntimeError("step_back: " + "; ".join(probs))
    return h1


def layer_find(name):
    return _run(FIND_JS.replace("%NAME%", json.dumps(name)))


def histogram_clip():
    return _run(CLIP_JS)


def _flat(layers):
    for layer in layers or []:
        yield layer
        yield from _flat(layer.get("children"))


def _in_takes(layer):
    """True for a group named "Takes..." and every layer inside one (paths are "/A/B/name")."""
    parts = layer.get("path", "").split("/")[1:]
    groups = parts if layer.get("kind") == "group" else parts[:-1]
    return any(g.lower().startswith("takes") for g in groups)


def deliverable(profile, state=None):
    """Problems for a delivery profile ([] = pass). Pure function over doc_state() output."""
    if profile not in PROFILES:
        return ["unknown profile %r (known: %s)" % (profile, ", ".join(PROFILES))]
    s = state if state is not None else doc_state()
    if not s.get("open"):
        return ["no document open"]
    mode, bits, prof, max_edge, min_edge, ppi = PROFILES[profile]
    probs = []
    long_edge = max(s["width"], s["height"])
    if mode and s["mode"] != mode:
        probs.append("mode is %s, expected %s" % (s["mode"], mode))
    if bits and s["bits"] != bits:
        probs.append("bit depth is %s, expected %s" % (s["bits"], bits))
    if prof and prof.lower() not in str(s.get("profile", "")).lower():
        probs.append("profile is %r, expected %s" % (s.get("profile"), prof))
    if max_edge and long_edge > max_edge:
        probs.append("long edge %d px exceeds %d" % (long_edge, max_edge))
    if min_edge and long_edge < min_edge:
        probs.append("long edge %d px below %d" % (long_edge, min_edge))
    if ppi and s["ppi"] < ppi:
        probs.append("resolution %s ppi below %s" % (s["ppi"], ppi))
    layers = list(_flat(s.get("layers")))
    if profile == "game-texture":
        w, h = s["width"], s["height"]
        if w & (w - 1) or h & (h - 1):
            probs.append("size %dx%d is not a power of two" % (w, h))
    if profile == "psd-handoff":
        unnamed = [ly["name"] for ly in layers if ly["name"].startswith(("Layer ", "Group "))]
        if unnamed:
            probs.append("%d default layer names (e.g. %r)" % (len(unnamed), unnamed[0]))
        # Losing takes are kept hidden on purpose, inside a group named "Takes" (or "Takes: ...").
        hidden = [ly["name"] for ly in layers if not ly.get("visible") and not _in_takes(ly)]
        if hidden:
            probs.append("%d hidden layers left in the file (e.g. %r); keep losing takes in a "
                         "\"Takes\" group" % (len(hidden), hidden[0]))
        empty = [ly["name"] for ly in layers
                 if ly.get("bounds") == [0, 0, 0, 0] and ly["kind"] != "group"]
        if empty:
            probs.append("%d empty layers" % len(empty))
        outside = [ly["name"] for ly in layers if ly.get("bounds") and ly["kind"] != "group" and
                   (ly["bounds"][0] < 0 or ly["bounds"][1] < 0 or ly["bounds"][2] > s["width"] or
                    ly["bounds"][3] > s["height"])]
        if outside:
            probs.append("%d layers extend past the canvas (e.g. %r)" % (len(outside), outside[0]))
    return probs


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd = argv[0]
    if cmd == "state":
        out = doc_state()
    elif cmd == "history":
        out = history()
    elif cmd == "find":
        out = layer_find(argv[1])
    elif cmd == "clip":
        out = histogram_clip()
    elif cmd == "deliverable":
        out = deliverable(argv[1])
    else:
        print(__doc__)
        return 2
    print(json.dumps(out, indent=1))
    return 0 if not (cmd == "deliverable" and out) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
