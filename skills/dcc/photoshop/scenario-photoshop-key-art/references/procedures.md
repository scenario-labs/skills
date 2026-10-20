# Procedures (toolkit calls, in order)

Each procedure names its calls and their status. "Verified live" means `test_keyart_live.py` runs
those calls on Photoshop 27.11 (macOS): a 1280 x 720 canvas from the `youtube-thumbnail` preset, a
fixture plate placed into a fixed box, type set, checked, exported, previews read by eye. "Not
tested" means the block was written from the toolkit's code and Adobe's documentation but never run
as shown. Every call is one `ps_run` job: read the error after each one.

Scenario steps appear as comments. They go through the Scenario MCP with the `scenario` skill
(connection, `recommend`, the price quote and the user's yes before every paid run, job waiting) and
`scenario-image` (the member and its fields).

Setup for every block:

```python
import json, os, sys
sys.path.insert(0, "<skills>/scenario-photoshop-key-art/scripts")
import ps_keyart as K             # also puts scenario-photoshop-expert/scripts on the path
import ps_run, ps_io as IO, ps_review as R, ps_audit as A, ps_gates as G
OUT = "/path/to/a/work/folder"    # never the folder of the user's PSD

def job(js, undo=None):           # one ExtendScript body; raises on a Photoshop error
    r = ps_run.run(js, undo=undo)
    if not r["ok"]:
        raise RuntimeError("%s (line %s)" % (r["error"], r.get("body_line", r.get("line"))))
    return r["result"]
```

## P1. Channels, copy sheet, fonts

Status: `PRESETS` and string presets verified live; a dict preset and the font pre-check not tested.

```python
CHANNELS = ["youtube-thumbnail", "instagram-story", "steam-header"]
for name in CHANNELS:
    print(name, K.PRESETS[name])          # size, unsafe zones, display width, max_bytes if any

# A channel with no preset: the same keys, from the channel's own documentation.
BANNER = {"size": [1500, 500], "unsafe": [[0, 380, 300, 500]], "display": 600}

COPY_YT = [   # the test's copy sheet: exact words, PostScript font names, boxes in canvas px
    {"name": "Headline", "text": "NIGHT\nHUNTERS", "box": [48, 70, 520, 500],
     "font": "Impact", "size": 260, "color": "#FFD23F", "align": "left"},
    {"name": "Subline", "text": "How owls see\nin the dark", "box": [48, 500, 520, 650],
     "font": "Arial-BoldMT", "size": 60, "color": "#FFFFFF", "align": "left"},
]

FONTS = r"""
var want = %WANT%, have = {}, out = {};
for (var i = 0; i < app.fonts.length; i++) have[app.fonts[i].postScriptName] = true;
for (var j = 0; j < want.length; j++) out[want[j]] = !!have[want[j]];
return out;
"""
want = sorted({c.get("font", "Arial-BoldMT") for c in COPY_YT})
missing = [f for f, ok in job(FONTS.replace("%WANT%", json.dumps(want))).items() if not ok]
# missing: ask the user to install or activate it (gui-paths), or to pick another. Never let
# Photoshop substitute silently.
```

- `name` is the layer name and stays the same across channels and variants, so checks and swaps find
  it.
- The `box` is the area the copy may use. Leave a margin to the canvas edge and to every unsafe
  zone: `check` fails text that touches either.
- `size` is the largest point size wanted. `type_layers` only shrinks.

## P2. Plate brief and scale

Status: `cover_bounds` tested offline (unit tests); the rest is arithmetic.

```python
# Scenario: price quote, the user's yes, then the run (scenario, scenario-image).
# Prompt parts: the subject and its action; where it sits in the frame ("on the right third");
# "a dark, quiet area on the left for text"; one light direction; "no text, no letters, no logos".
PLATE, pw, ph = OUT + "/plate_owl.png", 2048, 1152     # read the size from the downloaded file

for name in CHANNELS:
    W, H = K.PRESETS[name]["size"]
    b = K.cover_bounds(pw, ph, W, H, focus=(0.7, 0.4))
    k = (b[2] - b[0]) / pw                             # canvas px per plate px
    print(name, b, round(k, 2))                        # over 1: the plate is enlarged there
```

- Over 1 on any channel: upscale the plate first (scenario-photoshop-upscale-restore), or ask for a
  larger plate. A 9:16 story from a 16:9 plate needs a plate at least 1920 px tall.
- One plate across 16:9, 4:5 and 9:16 only works when the subject sits near the focus point with
  room on every side. Otherwise brief one plate per aspect, or expand it (P4).

## P3. Canvas

Status: verified live (guides counted, size read back).

```python
c = K.new_canvas("youtube-thumbnail", name="Owl, youtube-thumbnail")
assert c["size"] == K.PRESETS["youtube-thumbnail"]["size"], c
# c["guides"]: one guide per inner edge of each unsafe zone (2 for the YouTube badge)
```

- The canvas is RGB 8-bit at 72 ppi, converted to sRGB when Photoshop allows, and becomes the active
  document. At 72 ppi a point equals a pixel.
- It stays open and unsaved. The PSD copy is written in P8.

## P4. Plate in, subject inside

Status: `IO.place` into a fixed box verified live; a cover box larger than the canvas not tested.

```python
W, H = K.PRESETS["youtube-thumbnail"]["size"]
b = K.cover_bounds(pw, ph, W, H, focus=(0.7, 0.4))
p = IO.place(PLATE, "Plate, owl", bounds=b,
             xmp={"assetId": "<asset id>", "prompt": "<prompt>", "createdAt": "2026-10-19"})
assert all(abs(x - y) <= 1 for x, y in zip(p["bounds"], b)), p

def map_box(fr, box):          # subject box in plate fractions -> canvas px
    w, h = box[2] - box[0], box[3] - box[1]
    return [box[0] + fr[0] * w, box[1] + fr[1] * h, box[0] + fr[2] * w, box[1] + fr[3] * h]

def hits(a, z):
    return a[0] < z[2] and z[0] < a[2] and a[1] < z[3] and z[1] < a[3]

subject = map_box((0.55, 0.15, 0.9, 0.95), b)      # read off the plate by eye
assert subject[0] >= 0 and subject[1] >= 0 and subject[2] <= W and subject[3] <= H, subject
assert not any(hits(subject, z) for z in K.PRESETS["youtube-thumbnail"]["unsafe"]), subject
assert not any(hits(subject, c["box"]) for c in COPY_YT), "subject under the copy"
```

- Placed bounds come from the smart object's transform, so a cover plate reports bounds past the
  canvas. That is expected.
- A headline partly behind the subject is a deliberate look (WeJustClickme masks part of a headline
  behind the subject [-fMxuEjV6dM 03:04]). Then drop the last assert and mask the type by hand.
- The subject cut by the crop: move `focus` toward it. Still cut: expand the plate for that aspect
  (scenario-photoshop-generative-edit), then place the expanded file.

## P5. Type, styles, contrast

Status: `type_layers` verified live (fit, left, center and right alignment, missing font). Layer
styles, the dark band and the contrast estimate not tested.

```python
t = K.type_layers(COPY_YT)
for x in t:
    assert x["fits"], x
    assert x["font_used"] == x["font_asked"], "font missing: %s" % x["font_asked"]
    print(x["name"], x["size"], "pt")     # the fitted size, rounded
```

- Measured: "NIGHT\nHUNTERS" asked at 260 pt in Impact fits its 472 x 430 box at 132 pt.
- A line that shrinks below what reads at display size (P6) needs a line break, shorter copy agreed
  with the user, or a larger box. Never a smaller minimum.
- A missing font keeps Myriad Pro and raises nothing: the `font_used` comparison is the only signal.
- A text layer scaled with Free Transform may report its size before the scale (not tested): change
  sizes through `type_layers`.
- To change copy, remove the layers (P10) and run `type_layers` again. Editing contents in place
  skips the fit.

Stroke and drop shadow on a text layer (replaces the layer's existing effects):

```python
FX = r"""
var a = %ARGS%, d = app.activeDocument, cTID = charIDToTypeID;
d.activeLayer = d.artLayers.getByName(a.layer);
function rgb(hex) {
  var c = new SolidColor(); c.rgb.hexValue = hex; var r = new ActionDescriptor();
  r.putDouble(cTID("Rd  "), c.rgb.red); r.putDouble(cTID("Grn "), c.rgb.green);
  r.putDouble(cTID("Bl  "), c.rgb.blue); return r;
}
var ref = new ActionReference(), desc = new ActionDescriptor(), fx = new ActionDescriptor();
ref.putProperty(cTID("Prpr"), cTID("Lefx"));
ref.putEnumerated(cTID("Lyr "), cTID("Ordn"), cTID("Trgt"));
desc.putReference(cTID("null"), ref);
fx.putUnitDouble(cTID("Scl "), cTID("#Prc"), 100);
var st = new ActionDescriptor();
st.putBoolean(cTID("enab"), true);
st.putEnumerated(cTID("Styl"), cTID("FStl"), cTID("OutF"));
st.putEnumerated(cTID("PntT"), cTID("FrFl"), cTID("SClr"));
st.putEnumerated(cTID("Md  "), cTID("BlnM"), cTID("Nrml"));
st.putUnitDouble(cTID("Opct"), cTID("#Prc"), 100);
st.putUnitDouble(cTID("Sz  "), cTID("#Pxl"), a.stroke_px);
st.putObject(cTID("Clr "), cTID("RGBC"), rgb(a.stroke));
fx.putObject(cTID("FrFX"), cTID("FrFX"), st);
var sh = new ActionDescriptor();
sh.putBoolean(cTID("enab"), true);
sh.putEnumerated(cTID("Md  "), cTID("BlnM"), cTID("Mltp"));
sh.putObject(cTID("Clr "), cTID("RGBC"), rgb("000000"));
sh.putUnitDouble(cTID("Opct"), cTID("#Prc"), a.shadow_opacity);
sh.putBoolean(cTID("uglg"), false);
sh.putUnitDouble(cTID("lagl"), cTID("#Ang"), 90);
sh.putUnitDouble(cTID("Dstn"), cTID("#Pxl"), a.shadow_px);
sh.putUnitDouble(cTID("blur"), cTID("#Pxl"), a.shadow_px * 2);
fx.putObject(cTID("DrSh"), cTID("DrSh"), sh);
desc.putObject(cTID("T   "), cTID("Lefx"), fx);
executeAction(cTID("setd"), desc, DialogModes.NO);
return a.layer;
"""
args = {"layer": "Subline", "stroke": "000000", "stroke_px": 4, "shadow_opacity": 60, "shadow_px": 6}
job(FX.replace("%ARGS%", json.dumps(args)), undo="Scenario: Type styles")
```

- Dharnyelpeter groups the headline words and strokes the group from Blending Options [i2N09bhDllE
  07:07]. Vince Opra puts a drop shadow on the text [uM8jVa_wJU4 11:06] and a white outer glow on a
  placed logo "so it pops out more from the background" [uM8jVa_wJU4 11:39].
- Effects widen the rendered text. Run `check` (P6) after styles, never before.
- DGH styles the group instead of the text so the effect survives copy edits [BmqlEDGP-GY 01:02].
  `getByName` above reads top-level layers only.

A dark blurred band behind copy on a busy plate (Dharnyelpeter [i2N09bhDllE 04:57]):

```python
BAND = r"""
var a = %ARGS%, d = app.activeDocument, b = a.box;
var t = d.artLayers.getByName(a.text), L = d.artLayers.add();
L.name = a.name;
d.selection.select([[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]]);
var c = new SolidColor(); c.rgb.hexValue = a.color;
d.selection.fill(c);
d.selection.deselect();
L.opacity = a.opacity;
L.applyGaussianBlur(a.blur);
L.move(t, ElementPlacement.PLACEAFTER);
return {name: L.name, id: L.id};
"""
args = {"text": "Subline", "name": "Band, subline", "box": [32, 490, 540, 662],
        "color": "000000", "opacity": 55, "blur": 40}
job(BAND.replace("%ARGS%", json.dumps(args)), undo="Scenario: Band")
```

Contrast estimate, for the report only (the mean hides a busy background):

```python
def lin(v):
    v /= 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def lum(rgb):
    r, g, b = (lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

s = G.stats(layer="Plate, owl", region=[48, 500, 520, 650])     # the plate under the subline box
bg = [s[ch]["mean"] for ch in ("red", "green", "blue")]
fg = [int("FFFFFF"[i:i + 2], 16) for i in (0, 2, 4)]
hi, lo = sorted([lum(fg), lum(bg)], reverse=True)
ratio = (hi + 0.05) / (lo + 0.05)                 # WCAG: 4.5 small text, 3 large text
busy = max(s[ch]["std"] for ch in ("red", "green", "blue"))     # high: add a band or stroke
```

- `G.stats` on the plate layer ignores a band above it. With a band, judge by eye at display size.

## P6. Check and previews

Status: verified live (clean pass, badge zone, tiny text, text off the canvas; previews at 1280 and
360 px read by eye).

```python
name = "youtube-thumbnail"
P = K.PRESETS[name]
W, H = P["size"]
r = K.check(name)
assert not r["problems"], r["problems"]
for x in r["texts"]:
    print(x["name"], x["font_px"], "px,", x["px_at_display"], "px at", P["display"], "wide")
R.preview(OUT + "/yt_display.png", max_px=round(P["display"] * max(W, H) / W))
R.preview(OUT + "/yt_full.png", max_px=0)        # 0: full size
```

- Problems read "Subline: 11.0 px at 360 px wide", "Headline: under the channel's interface (zone
  [0])", "Price: leaves the canvas", or "this asset takes no text" (`steam-library-hero`).
- `check` reads visible text layers, inside groups too. A hidden layer, text in a smart object and
  rasterized text are not read.
- `check(unsafe=..., display=..., min_px=...)` overrides one value of the preset.
- Open both previews and grade them with [critique](critique.md). The display preview is the one
  that decides.

## P7. Export under a cap

Status: verified live (2 MB at quality 12, 150 KB fits below 12, 20 KB never fits, `size` resize).

```python
e = K.export_under(OUT + "/owl_youtube.jpg", P["max_bytes"])
assert e["fits"] and e["size"] == P["size"], e
print(e["quality"], e["bytes"], e["tried"])      # tried: [quality, bytes] per attempt

small = K.export_under(OUT + "/owl_youtube_640.jpg", 500000, size=[640, 360])   # same aspect only
```

- Measured on one 1280 x 720 thumbnail: quality 12 477 KB, 10 285 KB, 8 194 KB, 5 134 KB, 0 65 KB. A
  cap under the quality 0 size returns `fits: False`: report it, never ship it.
- A channel with no cap in its preset: ask the user, or take the channel's documented limit.
- `fmt="png"` saves one PNG and does not search; `fits` tells whether it passed.
- The export flattens a duplicate and converts it to sRGB 8-bit. The canvas is not changed.

## P8. Deliver

Status: `web` and `psd-handoff` profiles verified live in the lead's audit suite; `social` not run;
the PSD copy not tested here (the lead's P9 job).

```python
probs = A.deliverable("social")         # canvases for social feeds; "web" for store capsules
handoff = A.deliverable("psd-handoff")
ps_run.run('return psr_export(app.activeDocument, %s, "psd");' % json.dumps(OUT + "/owl_youtube.psd"))
```

- Expected findings: "layers extend past the canvas" for a cover plate; "long edge 462 px below 600"
  for `steam-small` under `web`. Name them in the report; any other finding is a failure.
- `psd-handoff` also flags default layer names, hidden layers outside a group named "Takes", and
  empty layers. Name every layer.
- The report lists per channel: size, export path, bytes, JPEG quality, `check` result, fonts used,
  and what was not verified.

## P9. A size set from one plate

Status: not tested as a loop; each call inside is verified live except a cover placement.

```python
PLAN = {   # per channel: focus point and copy (built like COPY_YT, boxes in that canvas's px)
    "youtube-thumbnail": {"focus": (0.7, 0.4), "copy": COPY_YT},
    "instagram-story": {"focus": (0.6, 0.45), "copy": COPY_STORY},
    "steam-header": {"focus": (0.7, 0.4), "copy": COPY_STEAM},
}
CAPS = {"instagram-story": 1000000, "steam-header": 1000000}   # from the user or channel docs
report = {}
for name, ch in PLAN.items():
    P = K.PRESETS[name]
    W, H = P["size"]
    b = K.cover_bounds(pw, ph, W, H, focus=ch["focus"])
    assert (b[2] - b[0]) / pw <= 1, (name, "plate enlarged")
    K.new_canvas(name, name="Owl, " + name)
    IO.place(PLATE, "Plate, owl", bounds=b)
    if not P.get("no_text"):
        t = K.type_layers(ch["copy"])
        assert all(x["fits"] and x["font_used"] == x["font_asked"] for x in t), (name, t)
    r = K.check(name)
    assert not r["problems"], (name, r["problems"])
    R.preview("%s/%s_display.png" % (OUT, name), max_px=round(P["display"] * max(W, H) / W))
    e = K.export_under("%s/%s.jpg" % (OUT, name), P.get("max_bytes") or CAPS[name])
    assert e["fits"] and e["size"] == [W, H], (name, e)
    report[name] = {"quality": e["quality"], "bytes": e["bytes"]}
```

- Copy boxes are laid out per canvas: a 9:16 story stacks the copy above the reply bar, a 920 x 430
  header puts it beside the subject. Never scale one channel's boxes to another.
- Every canvas stays open. Write its PSD copy (P8) before the user closes them.
- Read every display preview in one contact sheet: `R.sheet(paths, OUT + "/set.png", labels=...)`.
- To switch back to an open canvas:
  `job("app.activeDocument = app.documents.getByName(%s); return 1;" % json.dumps("Owl, steam-header"))`.

## P10. Variants from one master

Status: `REMOVE` beside a Clarity layer verified live (`test_keyart_live.py`); `IO.replace` keeping
the box at the same pixel size verified live (the lead's `test_io_live.py`); the whole loop not
tested.

```python
REMOVE = r"""
var d = app.activeDocument, names = %NAMES%, n = 0;
function isText(l) {   // layer.kind throws "Internal error" on a Clarity layer (27.11)
  try { var r = new ActionReference(); r.putIdentifier(charIDToTypeID("Lyr "), l.id);
        return executeActionGet(r).getInteger(stringIDToTypeID("layerKind")) === 3; } catch (e) { return false; }
}
for (var i = d.layers.length - 1; i >= 0; i--) {
  var l = d.layers[i];
  if (l.typename !== "ArtLayer" || !isText(l)) continue;
  for (var j = 0; j < names.length; j++) if (l.name === names[j]) { l.remove(); n++; break; }
}
return n;
"""
VARIANTS = {"A": COPY_YT, "B": COPY_YT_B, "no-text": []}   # B: another headline, same boxes
for v, copy in VARIANTS.items():
    job(REMOVE.replace("%NAMES%", json.dumps(["Headline", "Subline"])), undo="Scenario: Remove copy")
    if copy:
        t = K.type_layers(copy)
        assert all(x["fits"] and x["font_used"] == x["font_asked"] for x in t), (v, t)
    assert not K.check("youtube-thumbnail")["problems"], v
    e = K.export_under("%s/owl_youtube_%s.jpg" % (OUT, v), 2000000)
    assert e["fits"], (v, e)
```

- One change per variant: the copy, the plate, or one layer's visibility. Badis Designs tests a
  version with text and one without [TuF4RMJtq-4 06:30].
- `type_layers` makes new layers, so P5's styles (`FX`) are gone: re-run `FX` on them before
  `check`. A variant with no copy also hides P5's band (`Band, subline`), or it shows as an empty
  stripe.
- A new plate of the same pixel size: `IO.replace("Plate, owl", path)` keeps the placed box, since
  Replace Contents keeps the layer's transform. Any other size: a new canvas (P3, P4) for that
  variant, so no hidden plate stays in the delivered PSD.
- Plates for a variant set: quote all the jobs at once, then one yes from the user.
- Many records from a spreadsheet (names, prices, photos): Photoshop's Variables and Data Sets
  ([gui-paths](gui-paths.md)). Fixed text boxes there do not refit per record; this loop does.

## P11. Shell use

Status: the shell commands call the same functions; the live suite runs the library calls.

```bash
python3 ps_keyart.py presets
python3 ps_keyart.py canvas youtube-thumbnail
python3 ps_keyart.py type copy.json # the copy sheet as a JSON list (P1)
python3 ps_keyart.py check youtube-thumbnail
python3 ps_keyart.py export /path/out.jpg 2000000 --size 640,360
```

Each prints `{"ok": true, "result": ...}` or `{"ok": false, "error": ...}` and exits 1 on an error.
