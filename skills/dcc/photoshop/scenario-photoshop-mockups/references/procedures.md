# Procedures (toolkit calls, in order)

Each procedure names the calls it runs and its status. "Verified live" means `test_mockup_live.py`
runs those calls on Photoshop 27.11 (macOS). Its first class uses a 1000x800 fixture of gray strips
(luminance 60 to 230) under a printable quad; its second (`MockupFitLive`, tests F1 to F7 below)
uses a white 1000x800 document. "Not tested" means the block was written from the toolkit's code and
Adobe's documentation but never run as shown. Every call is one ExtendScript job through `ps_run`:
read the error after each one.

Scenario steps appear as comments. They go through the Scenario MCP with the `scenario` skill
(connection, `recommend`, the price quote and the user's yes before every paid Scenario job, job
waiting), `scenario-image` (plates and scenes with no photo, new designs), `scenario-product-shots`
(restaging, relighting, colorway sets), `scenario-image-editing` (background removal, vectorize,
upscale), `scenario-brand-kit` (vector marks) and `scenario-textures` (seamless repeats). No
Scenario step is run by the suite.

Setup for every block:

```python
import json, os, sys
sys.path.insert(0, "<skills>/scenario-photoshop-mockups/scripts")
import ps_mockup as M             # also puts scenario-photoshop-expert/scripts on the path
import ps_run, ps_gates as G, ps_review as R, ps_audit as A, ps_io as IO
OUT = "/path/to/a/work/folder"    # never the folder of the user's PSD
DOC = "tote_shoot.psd"            # the document the brief names

# History: h0 = A.history() right before a call; A.history_gate(h0, undo) == [] after it, or
# A.history_gate(h0) == [] after a call that must leave History as it found it. Never the list length.
# A call that raises or times out: recover as scenario-photoshop-expert's Quality gates say.

def check_doc():
    assert A.doc_state()["name"] == DOC, "another document is active"
```

Layer arguments take a layer name or id. The placeholder's default name is "Place Design Here"; its
group is "Mockup: Place Design Here". Pass `name=` for a second face ("Front", "Side").

## P0. Session, brief, route

Status: `doc_state` is a lead call, tested by the lead's suite.

```python
s = A.doc_state()
assert s["name"] == DOC, s["name"]
print(s["width"], s["height"], s["mode"], s["profile"])
for L in s["layers"]:                 # top level; a group's layers are in its "children"
    print(L["kind"], L["path"], L["bounds"])
```

Route by the brief:

- **No product photo, a logo, new designs:** the Scenario steps of P9 first (plates, scenes,
  vectors, designs), then the route below.
- **Flat face, one or many designs** (tote, box, bag, poster, screen): P1, P2, P3, P5, P6 or P7,
  P10, P11.
- **Can, mug or straight bottle:** P1, P2, P3, then P4b instead of a flat fit, then P5 and P6. A
  tapered bottle or a pouch: the hand warp in [gui-paths.md](gui-paths.md), after the last fit.
- **Colorways of the product:** decide the blank here, before P1: light colorways (sand, pastels,
  white) from a dark garment come out flat, so they need a white or light-gray blank first (the
  user's, or P9's instruction edit). The fit, lighting and Displace map are built from that plate.
  P7b runs after the designs are in.
- **A Scenario result onto a screen or frame:** P8, then P5 if the surface has texture.
- **A logo that exists only as a small raster:** P9 before P6.

The product layer must be a pixel layer or a smart object. Lighting from a Background layer is not
tested: duplicate it first (Layer > Duplicate Layer, or Cmd-J) and name the copy "Product".

## P1. The printable area

Status: not tested by script (the live test made a rectangular selection). Select Subject by Action
Manager is measured on 27.11.

```python
js = """
var d = app.activeDocument;
d.activeLayer = d.artLayers.getByName("Product");
var desc = new ActionDescriptor();
desc.putBoolean(stringIDToTypeID("sampleAllLayers"), false);
executeAction(stringIDToTypeID("autoCutout"), desc, DialogModes.NO);
// leave out the lid and the base: subtract two rectangles (document px)
var lid = [[300, 120], [720, 120], [720, 190], [300, 190]];
var base = [[300, 600], [720, 600], [720, 680], [300, 680]];
d.selection.select(lid, SelectionType.DIMINISH);
d.selection.select(base, SelectionType.DIMINISH);
return 1;
"""
assert ps_run.run(js)["ok"]
IO.export_mask(OUT + "/area.png")         # white = printable; open it and look
print(IO.selection()["bounds"])
```

- A selection made by Select Subject covers the whole product. Subtract what is not printed: lid,
  base, seams, straps, handles, a hand holding it.
- For hard rims, ask the user for a Pen path and make a selection from it (Cmd-Return in the Paths
  panel). Geller draws the can's outline with the Curvature Pen for the same reason (Geller
  [0l2Ma_2B-A8 00:32]).
- A cutout from `scenario-image-editing` (background removal) can be placed as a layer; Cmd-click
  its thumbnail loads its alpha as the selection.
- Keep the selection active for P3: `placeholder` turns it into the group mask.

## P2. The four corners

Status: not tested by a suite. The toolkit takes the corners as data; it does not find them.

The quad is `[[x, y] TL, TR, BR, BL]` in document pixels: the corners of the printed area as the
camera sees them.

From a 4-point path the user drew (the most reliable source):

```python
js = """
var p = app.activeDocument.pathItems.getByName(%s), sp = p.subPathItems[0], pts = [];
for (var i = 0; i < sp.pathPoints.length; i++) pts.push(sp.pathPoints[i].anchor);
return pts;
""" % json.dumps("Print area")
pts = ps_run.run(js)["result"]

def order(pts):                    # TL, TR, BR, BL from four points in any order
    top = sorted(sorted(pts, key=lambda p: p[1])[:2], key=lambda p: p[0])
    bot = sorted(sorted(pts, key=lambda p: p[1])[2:], key=lambda p: p[0])
    return [top[0], top[1], bot[1], bot[0]]

quad = order(pts)
```

- Under `ps_run` (ruler units in pixels) the anchors read back in pixels, at 72 ppi as at 300 ppi.
  Only a path made through the DOM's `PathPointInfo` takes points: pass pixels times 72 / resolution
  when you draw one by script.
- The sort fails on a face rotated about 45 degrees. Check the order on a preview.

From previews, when there is no path: read approximate corners on a fit-to-screen
`R.preview(OUT + "/whole.png")` (scale back by the preview's ratio), then refine each one on a 100%
crop around it:

```python
for x, y in quad:
    R.preview(OUT + "/corner_%d_%d.png" % (x, y), crop=[x - 60, y - 60, x + 60, y + 60], max_px=0)
```

Real proportions: measure the printed area's real width and height (the brief, a dieline, or a
straight-on photo) and pass them, or their ratio in pixels, as `size` in P3. GraphiqVibe starts a
box mockup from "the size that we used for the design" (GraphiqVibe [WeDJv63Wgjk 01:37]);
WeJustClickme measures the can first (WeJustClickme [-VM3ee1O_8U 00:00]). Without it,
`quad_size(quad)` uses the mean edge lengths, which are foreshortened.

## P3. Placeholder

Status: verified live (tests 1 and 7, F1). Corners within 1 px, `fit_check` under 0.5, one History
state named "Scenario: Mockup placeholder", Fill 60, `print_size` equal to `quad_size(quad)` by
default and to `size` when given (800x500 on a 400x400 box, rendered corners within 2.5 px), the
rendered red checked 5 px inside and outside each corner. With a selection active, `group_mask` true
and red only inside the selection. `color=` is not tested.

```python
check_doc()
quad = [[300, 200], [700, 240], [690, 600], [310, 560]]
h0 = A.history()                     # right before the call: a selection is a state of its own
P = M.placeholder(quad, name="Place Design Here", size=[800, 500])   # size: the real print size
print(P["group"], P["size"], P["print_size"], P["corner_error"], P["fit_check"], P["group_mask"])
assert P["corner_error"] < 1.0 and P["fit_check"] < 0.5
assert A.history_gate(h0, "Scenario: Mockup placeholder") == []
for x, y in quad:
    R.preview(OUT + "/fit_%d_%d.png" % (x, y), crop=[x - 40, y - 40, x + 40, y + 40], max_px=0)
```

- The placeholder is a solid color (default red) so its edges read against any product. Fill 60 lets
  the product show through while fitting, as builders lower opacity or Fill (Quick Fix Up
  [boONV-waIUk 00:33]; WeJustClickme [-VM3ee1O_8U 01:06]).
- `size` is the print size (or its ratio in pixels). It rides in the layer's XMP as
  `scenario:printSize`, through every re-fit, and `replace_design` crops each design to it. `size`
  in the result is the content size Photoshop holds, which can differ.
- `mask_selection=False` ignores an active selection.
- Open each corner crop: the red edge meets the face's corner, with no gap and no overlap past the
  rim.

## P4. Re-fit and read the corners

Status: verified live (test 2, F1, F4, F5). Test 2: a second quad on the warped placeholder, `reset`
true, the same thresholds, `corners` `consistent` true. F1: three more re-fits in a row (one
smaller, one mirrored), rendered corners within 2.5 px, the print size kept, one History state
"Scenario: Fit to corners" each. F4: a placed PNG with transparent margins, a layer clipped above it
and an active selection, fitted twice: the margins, the clip and the selection kept. F5: a smart
object with a Smart Filter refuses the fit before any change.

```python
quad2 = [[340, 180], [720, 260], [660, 620], [280, 540]]
F = M.fit_quad("Place Design Here", quad2)
print(F["id"], F["reset"], F["corner_error"], F["fit_check"], F["print_size"])
C = M.corners("Place Design Here")
print(C["corners"], C["consistent"], C["size"], C["print_size"], C["fill"])
```

- A fit first flattens any warp (`reset` true), so a hand-made curve is lost. Re-fit before a hand
  curve, never after.
- Every fit wraps the object in a new smart object at 97% of the target's box, then scales it up and
  warps (a custom warp lands only on an object scaled up from its box). The layer keeps its name,
  Fill, opacity, blend mode and XMP; its `id` changes: use the returned one.
- Fit before P5's `displace`: a smart object with Smart Filters refuses a fit ("has Smart Filters:
  fit before displace"). A layer mask on the design is refused too: put it on the group.
- `corner_error` is the largest distance from a corner to its target; `fit_check` compares the
  stored warp with the mesh's box, without pixels.
- Move one corner a few pixels at a time and re-fit until the corner crops agree.

## P4b. Cylinder: cans, mugs, straight bottles

Status: verified live (F3) on an 800x400 checkerboard with
`fit_cylinder(quad, 24, top_bulge=12, angle=120)`: corners within 2 px rendered, the bottom edge's
middle 24 px below its corners and the top's 12 px (both within 2), column widths 44, 60, 70, 74,
74, 70, 60, 45 px across (the edge columns 0.595 and 0.608 of the middle, where a cylinder predicts
0.61; the test accepts 0.55 to 0.67), one History state "Scenario: Fit to cylinder".

```python
label = [[250, 200], [750, 200], [750, 520], [250, 520]]   # the label's corners, TL TR BR BL
F = M.fit_cylinder("Place Design Here", label, 24, top_bulge=12, angle=120)
print(F["corner_error"], F["fit_check"], F["consistent"])
assert F["corner_error"] < 1.0 and F["fit_check"] < 0.5
mid = [(label[2][0] + label[3][0]) / 2, (label[2][1] + label[3][1]) / 2 + 24]
R.preview(OUT + "/bottom_middle.png", crop=[mid[0] - 40, mid[1] - 40, mid[0] + 40, mid[1] + 40], max_px=0)
```

- `quad`: the label's four visible corners: where it ends, or the silhouette edges when it wraps
  past them.
- `bulge`: how far the bottom edge's middle sags below the line between its corners, in px; read it
  on the product's base or a label seam. `top_bulge` does the same for the top edge (default: the
  same). Seen from above, the bottom bows more than the top. Seen from below, the edges bow upward:
  negative values (not tested).
- `angle`: the label's visible arc in degrees, at most 180. A label wrapping past the silhouette
  shows close to 180, and its sides compress hard; one ending in front shows less. Start at 120 and
  compare the check design's side columns with the product's curve.
- A run of P6 designs keeps the cylinder: Replace Contents keeps the warp (not tested on a cylinder;
  tested on four-corner fits).
- Read the result on a check design (P5's ramp has a grid): the columns narrow toward both sides,
  and the grid's horizontals bow with the rim and the base.

## P5. Test design, lighting, creases

Status: `lighting` verified live (test 4): a flat gray design got darker by more than 15 over a dark
strip of the product and brighter by more than 5 over a bright one; outside the design the image
stayed within 4 of its luminance; one History state. `displace` verified live (test 5) at
`scale=100` with an explicit `map_dir` and the default blur: the map file exists, one History state,
a straight line in the design bent differently at two places. `prefix=`, the default map folder and
lighting from a Background layer are not tested.

Make a test design at the placeholder's content size (Pillow), with a gray ramp and a grid:

```python
from PIL import Image, ImageDraw
w, h = M.corners("Place Design Here")["size"]
ramp = Image.new("RGB", (w, h))
d = ImageDraw.Draw(ramp)
for x in range(w):
    v = int(255 * x / max(1, w - 1))
    d.line([(x, 0), (x, h)], fill=(v, v, v))
for x in range(0, w, 40):
    d.line([(x, 0), (x, h)], fill=(220, 40, 40))
for y in range(0, h, 40):
    d.line([(0, y), (w, y)], fill=(220, 40, 40))
ramp.save(OUT + "/ramp.png")

M.replace_design("Place Design Here", OUT + "/ramp.png", fit="exact")
Lt = M.lighting("Place Design Here", "Product")
print(Lt["neutral"], Lt["layers"], Lt["product_under_design"]["luminance"])
D = M.displace("Place Design Here", "Product", scale=8, map_dir=OUT + "/maps")
print(D["map"], D["map_box"], D["blur"], D["scale"])
assert os.path.exists(D["map"])
R.preview(OUT + "/ramp_lit.png")
```

- `lighting` measures the product's mean luminance under the design (`neutral`). The "Shading
  (product)" copy is Multiply with Levels 0 to `neutral`: only what is darker than the mean darkens.
  The "Highlights (product)" copy is Screen with Levels `neutral` to 255: only what is brighter
  lightens. Both are desaturated and clipped above the top of the design's clipping chain.
- Lower `shade` or `light` (percent opacity) when the fabric reads heavier than the photo; set one
  to 0 to skip that copy.
- `displace` crops the product's pixels to the design's bounds, desaturates and blurs them, saves
  the map as a PSD, and applies Displace as a Smart Filter (Stretch To Fit, Repeat Edge Pixels).
  Default blur: max(1, document width / 1500). Without `map_dir`, the map goes in "<document> maps/"
  next to a saved document, else in Documents/Scenario Photoshop/displace maps/.
- Scale is in pixels of displacement. Start at the toolkit's 8 and look; experts used 4 on a 4000
  px-wide fabric scene, 15 on a crushed can, 10 to 20 on a t-shirt (Dinda [_VNqOhHJIm8 06:11];
  Geller [0l2Ma_2B-A8 05:24]; Dinda [sy1w5mTif-E 06:27]).
- Re-running `displace` adds a second filter. Step back History first to change the scale.
- Look at the ramp: the grid lines bend along the folds, the dark end still shows the highlights,
  the bright end still shows the shadows. If one end goes flat, adjust that copy's opacity.

## P6. Replace the design

Status: verified live (test 3) with `fit="exact"`: `drift` under 0.5, `content_size` unchanged, Fill
back to 100, one History state, a left/right two-color design keeps its orientation. `cover` (F2): a
1600x500 design on an 800x500 print size keeps its middle 800 px, a band at 3/8 to 5/8 of the face
landing within 1.5% of it. `contain` is not tested.

```python
r = M.replace_design("Place Design Here", "/path/to/design.png", fit="cover")
print(r["content_size"], r["source_size"], r["scale"], r["drift"], r["fill"])
assert r["drift"] < 0.5
```

- `cover` scales the file to fill the print size and crops the overflow, centered; `contain` pads it
  (transparent) to fit inside; `exact` stretches it. The result is then stretched to the content
  size, so the print proportions come back on the product.
- The layer keeps its name; Photoshop's own Replace Contents would rename it after the file.
- The lighting copies and the Displace filter stay; the new design takes them on re-render. With the
  map deleted, this call fails with "the file was not found": re-run P5's `displace`.
- `reset_fill=False` keeps the fitting Fill, for a quick check before the final design.

## P7. Batch: one export per design

Status: verified live (test 6) with two designs: each PNG shows its own design's color, the document
renders identically before and after (difference 0), and the active History state is restored.

```python
designs = ["/designs/sunrise.png", "/designs/wave.png", "/designs/logo_on_white.png"]
h0 = A.history()
res = M.batch("Place Design Here", designs, OUT + "/mockups", fit="cover")
for r in res:
    print(os.path.basename(r["out"]), r["drift"])
assert A.history_gate(h0) == []      # h0's state is active again; redo states may follow it
R.sheet([r["out"] for r in res], OUT + "/mockups sheet.jpg",
        labels=[os.path.basename(r["design"]) for r in res])
```

- Each design is one History state named "Scenario: Batch design", exported from a merged temporary
  copy, then stepped back. Deleting a snapshot instead would send the document to its opening state.
- Output names are "<design file stem> mockup.png", at the document's full size.
- Plates from different photos give the same design at different apparent sizes; Stanik's second mug
  came out "way smaller" (Stanik [QTS-IWB3MKY 13:35]). Batch one plate at a time.

## P7b. Colorways

Status: verified live (F6, F7) on synthetic fixtures; no product photo was shot for the test. F6:
navy and forest over eight gray strips, clipped to the product layer: two PNGs named "<name>
colorway.png", each within Delta E 5 of its swatch with folds 0.9 or more, hue within 5 degrees, the
strips' order of lightness kept, the background and a print above unchanged, the document rendering
identically afterwards, `A.history_gate(h0) == []`. Color mode alone (`match=False`) keeps each
strip's luminance within 2 and fails the check. With a selection active, a red colorway masked to
it: only the selected strips change, and the selection is still active afterwards. F7: navy, red,
sand and white on a white and a black shirt drawn with folds, measured independently on the
delivered PNGs. Navy, red and sand: mid-tones within Delta E 0.12 to 0.48 of the swatch, folds 0.998
to 1.0 (the toolkit's own check: 0.11 to 0.46). On the white shirt the folds keep their depth
(relative fold contrast 0.23 before, 0.21 to 0.23 after), and white is the blank: no curve,
mid-tones 228.2 before and 228.3 after, contrast unchanged, `blank` true. On the black shirt (0.58
before), navy keeps 0.41 and red 0.28, folds still visible, not `flat`; sand falls to 0.11 (faint
folds) and white to 0.004 (none), both `flat` (asserted). Color mode alone turns navy on the white
shirt into (221, 228, 255), Delta E 75. `M.lab_to_rgb` and a Lab swatch (`{"lab": ...}`) are tested
offline only. The same math ran offline on two frames from Anders [rrxTM5AZALU]: a white tee kept
its relative fold contrast (0.21) for navy, red and sand, and kept the blank for white; a black
sweatshirt fell from 1.13 to 0.57 (navy) and 0.39 (red), both kept, and to 0.14 (sand) and 0.004
(white), both `flat` ([sources.md](sources.md)).

```python
check_doc()
import time
from PIL import Image
# On the blank chosen at P0. Select the garment or product without its background (P1's Select
# Subject, minus the print).
h0 = A.history()                      # after the selection, so the mark holds it
UNDO = "Scenario: Colorway"
colors = {"navy": "#1e3278", "red": (176, 32, 32), "sand": "#e6d2a0", "white": "#ffffff",
          "brand blue": {"lab": [38, 12, -48]}}     # Lab: tested offline only
FOLD = [420, 610, 620, 760]           # a deep fold, document px
try:
    res = M.colorways("Product", colors, OUT + "/colorways")
except Exception:                     # RuntimeError from a job; ValueError or a Pillow OSError too
    # The lead's recovery (Quality gates). A timed-out job may still finish: wait until History
    # stops moving, then let the gate decide, never the state's name alone.
    a, b = None, A.history()
    while a != b:
        time.sleep(3)
        a, b = b, A.history()
    p = A.history_gate(h0, UNDO)
    if p == []:                       # one colorway left on top of the mark
        A.step_back(h0, UNDO)         # back to the mark, selection included
    elif not any("no new History state" in x for x in p):
        print("History moved since the mark: stop and tell the user", p)
    raise                             # fix what the error names, then run again from the mark
for r in res:
    c = r["check"]                    # mid-tones of the product against the swatch
    print(r["colorway"], os.path.basename(r["out"]), r["curve"], c["delta_e"], c["folds"],
          c["contrast"], c["flat"], c["blank"])
    assert not c["flat"], (r["colorway"], c)        # folds gone: a lighter blank (P0, P9)
    if c["blank"]:                    # no Curves: the blank is this colorway; show a fold at 100%
        Image.open(r["out"]).crop(FOLD).save(OUT + "/fold %s.png" % r["colorway"])
    else:
        assert c["delta_e"] <= 5 and c["folds"] >= 0.9, (r["colorway"], c)
assert A.history_gate(h0) == []
R.sheet([r["out"] for r in res], OUT + "/colorways sheet.jpg", labels=list(colors))
```

- Each colorway is a Solid Color fill layer named "Colorway: <name>", in Color mode, just above the
  product layer. Color mode takes the swatch's hue and saturation and keeps the luminance below it,
  so on its own a white shirt stays near white and a black one near black. So, when the product's
  mid-tones sit more than 3 levels from the swatch's luminance, a Curves layer "Colorway tone:
  <name>" goes under the fill first, with the same mask. The mockup group above is not recolored.
- The curve: a darker swatch scales the luminance (gain = swatch over mid-tones, at least 0.05), so
  the folds darken in proportion; a lighter swatch lifts it (an offset), its slope lowered so the
  brightest 1% stays at 250 or under. Mid-tones: the mean of the 25th to 75th percentile of the
  product's luminance under the mask. `M.tone_curve(tones, rgb)` returns the points, `None` within 3
  levels.
- No curve when the blank stands (`M.is_blank`): the swatch is so light that the slope would fall
  under 0.5, and the blank is already within 25% of it. White on a white blank is the blank: a curve
  there would clip every fold to white (relative contrast 0.23 to 0.008, measured offline before
  this rule). On a dark blank the rule never applies, so white is curved and comes out `flat`.
- Why a light blank: the offset keeps a dark garment's folds at their depth in levels, so relative
  to a light swatch they shrink to about mid-tones over swatch. A gain instead clips the highlights
  and lifts noise out of the black. No curve turns a black blank into a credible light colorway.
- The check exports the product with only its colorway layers, reads the pixels under the mask at a
  400 px long side, and returns:
  - `mean`, the mid-tones' color, and `delta_e`: CIE76 against the swatch, or against its Lab value
    when one is given; 5 or less passes (authoring-time). It reads the same mid-tones the curve
    targets, so it mainly proves the math and catches gamut clipping. A brand spec is checked on a
    print or a calibrated photo, not here.
  - `folds`: the correlation of the luminance pattern before and after (0.9 or more). 1 means the
    folds sit in the same places; it is blind to their depth.
  - `spread`: fold depth in levels, after over before. Below 1 on a darker swatch, about 1 on a
    lighter one.
  - `contrast`: fold depth relative to the mid-tones, (p90 - p10) / p50, before and after.
  - `flat`: true when the contrast after is under 0.15 and under half the contrast before
    (authoring-time: colorways that kept visible folds measured 0.21 to 0.57, those that lost them
    0.008 to 0.14). The folds are gone: go back to a lighter blank.
  - `blank`: true when no curve ran because the blank stands. `delta_e` then measures the blank's
    own shading, not an error, so show a deep fold at 100% instead.
- `match=False` keeps Color mode alone, for a hue-only change on a mid-tone product; `check=False`
  skips the measurement. Matching and the check need Pillow.
- With a selection active, the selection is its mask. Without one it is clipped to the product
  layer, which recolors everything on that layer, background included: select the garment first when
  the product layer is the whole photo.
- Each colorway is one History state, exported from a merged copy, then stepped back, like P7. At
  the History limit the temporary states drop the user's oldest undo steps (the lead's traps,
  section 5). Designs times colorways is not one call: add the fill layer by hand
  ([gui-paths.md](gui-paths.md)), run P7, then pick the next color (not tested).
- A colorway that changes the material (heather, wash, another weave): an instruction edit per color
  on the plate (`scenario-product-shots`, quoted first), each result placed with `IO.place` under
  the mockup group and shown one at a time (not tested).

## P8. A placed Scenario result on four corners

Status: verified live (test 8): a result placed with `IO.place(..., fit="contain")`, then
`fit_quad`, gives `fit_check` under 0.5 and `corner_error` under 1, and the rendered red checked
inside and outside each corner.

```python
# Scenario MCP: the screen art, poster or label from scenario-image; download to OUT
p = IO.place(OUT + "/screen_art.png", "Scenario result", bounds=[50, 50, 450, 300], fit="contain")
screen = [[412, 188], [868, 210], [860, 470], [405, 452]]
F = M.fit_quad("Scenario result", screen)
print(F["id"], F["corner_error"], F["fit_check"])
```

- The fit wraps the placed object in a new smart object, as every fit does: use the returned `id`.
- For a screen, skip `lighting` and `displace`, or use a light `shade`, since a screen emits light.
  A glossy screen may want a reflection layer by hand.
- Use P3's `placeholder` instead when several results will follow: one fit, then `batch`.

## P9. Scenario inputs: plate, scene, design, logo

Status: not tested (no Scenario job runs in the suite).

```python
# Scenario MCP, each job quoted first, with the user's yes (the `scenario` skill):
#   no product photo: scenario-image, a blank product plate on a plain backdrop, or a lifestyle
#     scene, straight-on to the printable face (a flat face is easier to fit)
#   a real product to restage or relight: scenario-product-shots
#   light colorways wanted and only a dark garment: scenario-product-shots, an instruction edit to
#     a white or light-gray blank, same folds, light and framing; it becomes the product layer
#     before P1, since the fit, lighting and Displace map are built from it
#   a new design: scenario-image at the print size's ratio; a seamless repeat: scenario-textures
#   a raster logo: scenario-image-editing (vectorize, recommend with the user's words)
#     or scenario-brand-kit: trace an existing mark to editable SVG, do not regenerate it
#   asset_get the result; save its url with curl -L (asset_download returns a raster)
import subprocess
size = M.corners("Place Design Here")["size"]
subprocess.run(["rsvg-convert", "-w", str(size[0] * 2), "-o", OUT + "/logo.png",
                OUT + "/logo.svg"], check=True)    # librsvg; any SVG renderer works
```

- A generated plate goes in as the document's product layer: open it, duplicate it as "Product", and
  start at P0. Ask for the printable face straight-on or at a gentle angle, and for no print on it:
  a blank face fits and lights cleanly.
- Render the logo at least the placeholder's content size; twice that costs nothing and survives a
  later larger placeholder.
- Compare the trace with the original at 100%: letter shapes, counters, thin strokes, corners. A
  trace that changed a letter is redone, never patched in the mockup.
- Keep the SVG as the master. A recolor is a fill edit in the SVG, then a new render.
- Without a model: a large, clean, flat logo on white can be cut out by channel, which "keeps nice
  sharp edges" (Williams [tNrV1XdZX0o 00:31]); see [gui-paths.md](gui-paths.md). A small or blurry
  logo needs the vector.
- Brand color: Multiply under `lighting` keeps the color at the product's mean. Check the brand
  color on the sheet where the face is flat and evenly lit.

## P10. Hand finish

Status: not tested as written. The fit suite applies `applyGaussianBlur(1)` to a smart object, and
the next fit finds it as a Smart Filter (F5); its order after Displace is not tested. The menu steps
are in [gui-paths.md](gui-paths.md).

```python
js = """
var d = app.activeDocument;
var L = d.layerSets.getByName("Mockup: Place Design Here").artLayers.getByName("Place Design Here");
d.activeLayer = L;
L.applyGaussianBlur(1.0);       // on a smart object it is expected to land as a Smart Filter
return 1;
"""
print(ps_run.run(js, undo="Scenario: Ink blur"))
```

- If the call throws on the smart object, apply Filter > Blur > Gaussian Blur by hand
  ([gui-paths.md](gui-paths.md)).
- Check the Layers panel or a preview: the blur must sit above Displace in the Smart Filter list, so
  the design blurs after it bends (Dinda [_VNqOhHJIm8 07:17]).
- 1 px for fabric; 0.6 px when the design has a fine stroke (Dinda [_VNqOhHJIm8 08:55]).

## P11. Deliver

Status: `R.sheet` and `A.deliverable` are lead calls, both verified live by the lead's suites
(`test_io_live.py` runs `sheet`; `test_audit_live.py` runs `deliverable`).

```python
print(A.deliverable("psd-handoff"))  # the active document, before a layered handoff; [] = pass
```

- Look at the sheet: every design, every corner, the printable edge.
- Report: the layer and group names, `corner_error` and `fit_check`, each design's `drift`, the map
  path (it must stay on disk while the filter exists), the output folders for designs and colorways,
  and what was not verified.
