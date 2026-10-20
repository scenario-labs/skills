# Procedures (toolkit calls, in order)

Each procedure names the calls it runs and its status. "Verified live" means `test_upscale_live.py`
or `test_restore_live.py` runs those calls on Photoshop 27.11 (macOS). "Not tested" means the block
was written from the toolkit's code and Adobe's documentation but never run as shown. Every call is
one `ps_run` job: read the error after each one.

Scenario steps appear as comments. They go through the Scenario MCP with the `scenario` skill
(connection, `recommend`, the price quote and the user's yes before every paid run, job waiting),
`scenario-image-editing` (upscale and enhance tool models) and `scenario-image` (instruction restore
and colorize).

Setup for every block:

```python
import json, os, sys
sys.path.insert(0, "<skills>/scenario-photoshop-upscale-restore/scripts")
import ps_upscale as U            # also puts scenario-photoshop-expert/scripts on the path
import ps_run, ps_gates as G, ps_review as R, ps_audit as A, ps_io as IO
OUT = "/path/to/a/work/folder"    # never the folder of the user's PSD

def select_box(b):                # a rectangular selection [l, t, r, b] on the active document
    js = ("var b = %s; app.activeDocument.selection.select([[b[0], b[1]], [b[2], b[1]], "
          "[b[2], b[3]], [b[0], b[3]]]); return 1;" % json.dumps(b))
    assert ps_run.run(js)["ok"]
```

## P0. Session, brief, route

Status: `doc_state` verified live (`test_audit_live.py`).

```python
s = A.doc_state()
assert s["name"] == "family_1952.psd", s["name"]   # the document the brief names
canvas = [s["width"], s["height"]]
print(s["mode"], s["bits"], s["profile"], canvas)
h0 = A.history()                  # the active History state; gates read it, never the list length
```

Route by the job:

- **Upscale** (more pixels, same picture): P1, P2, P3, then P4 or P5 as needed, P10.
- **Restore or colorize** (repair, new color, same person): P1, P6, P7, P8 only on drift, P9, P10.
- **Changed layer** (one soft layer inside a finished image): P11.
- **Mixed** (restore, then upscale the restored master): finish the restore through P9, then run the
  upscale route on a flattened copy the user approves.

Write the brief as two lines: what may change (resolution, damage, color) and what must not (faces,
lettering, the frame). For a colorize on a Grayscale or Bitmap master, ask before converting it:
Image > Mode > RGB Color is one History state on the user's document, and a color layer placed into
Grayscale shows no color (Dinda [G5yuLhm0SdM 12:32]).

## P1. Prepare the input

Status: `prepare_input` with `ratios` and `max_px` verified live (test 1): 16:9 padding with black,
the source not shifted inside the padding (worst pixel 2 or less), the cap applied, and the active
History state, pixels and layers as before. `layer=` and `pad_color` are not tested.

```python
# Scenario MCP: read the member's schema for its accepted ratios and largest input side
prep = U.prepare_input(OUT + "/input.png", ratios=["1:1", "4:3", "3:4", "16:9", "9:16"],
                       max_px=2048)
json.dump(prep, open(OUT + "/prep.json", "w"))
print(prep["ratio"], prep["padded"], prep["pad"], prep["scale"], prep["output"])
assert A.history_gate(h0) == []   # h0's state is still the active one (temporary states may
                                  # follow it; at the History limit they drop the oldest steps)
```

- `ratios=None` exports at the source ratio, with no padding. Use it only when the member accepts
  any ratio.
- The padding is split evenly, with the odd pixel on the right or bottom; `pad` is `[l, t, r, b]` at
  source size.
- The cap resamples with Bicubic Sharper and reports `scale`. Keep the input under the member's cap;
  what a member does with a larger input is not tested here.
- `layer="Restore base"` exports one layer (its group stays visible) instead of the merged image.
  Not tested.
- Open `input.png` and look: the whole subject inside, padding plain black.

Dinda pads to a square and fills the gap with black before a colorize, because a square input
shifted less over "hundreds of images" (Dinda [G5yuLhm0SdM 05:58]; [G5yuLhm0SdM 06:31]). Off-ratio
inputs "will shift a bit more likely than not" (Dinda [mSgSaisb6Kg 00:33]).

## P2. Upscale candidates as a stack

Status: verified live (test 2) with two real Scenario 2x upscales and made defects: both real
upscales, bicubic and nearest neighbor match; the shifted and tinted copies fail; the wrong aspect
fails `aspect_ok` and `size_ok`; a blurred copy scores under a third of bicubic's detail.

```python
# Scenario MCP:
#   recommend with the capability ("faithful photo upscale", "creative upscale") and the
#   user's words; two members or two settings, one quote for both, the user's yes
#   upload prep["path"]; factor 2; wait; download to OUT + "/up_a.png" and "/up_b.png"
cands = [{"path": OUT + "/up_a.png", "label": "<member A>"},
         {"path": OUT + "/up_b.png", "label": "<member B>"}]
st = U.build_stack(cands, 2)
print(st["doc"], st["size"], st["base"], "base detail", st["base_detail"])
for L in st["layers"]:
    print(L["name"], L["size_ok"], L["aspect_ok"], L["match"]["mean"], L["match"]["matches"],
          "texture", L["texture_change"], "detail vs base", L["detail_vs_base"])
```

- The stack is a new document named "<source>, 2x candidates". The user's document is not resized.
- Layers, top first: one per candidate in the order given, each "<label>, 2x scale" with a white
  mask, then "Original, Preserve Details 2.0, 2x scale". Use the member's name as the label, so the
  layer carries model and factor.
- When the input was padded, crop the padding off the result first (Pillow), or the stack fits the
  padded frame into the source's size and `aspect_ok` fails.

Reading the numbers:

- **`size_ok` false, `aspect_ok` true:** the member used another factor. Fine for review; the layer
  is fitted to the stack.
- **`aspect_ok` false:** reframed or cropped. Reject.
- **`match["matches"]` false:** shift, color cast or reframing (mean 6 or more at 256 px). Real
  upscales measured 4.9; an 8 px shift 16.8; a color cast 38.5. Reject or fix color with P5.
- **`texture_change`:** information only. Real generative upscales measured 9.4 to 9.5, bicubic 3.3:
  a high value means the texture was redrawn, so look at it.
- **`detail_vs_base`:** real upscales 0.95 to 1.00, bicubic 0.65, a 2 px blur 0.08. Far under 1
  means the member smoothed the image; over 1 can be new detail or invented detail. Only the crops
  tell which.

## P2b. Cheapest proof first: baseline, then a crop, then the winner

Status: not tested in this order. P2 (two candidates in one stack) and P3 are verified live;
`build_stack` with no candidates and `place_result` into a stack document are not.

```python
box = [600, 260, 856, 516]                       # the face, text or texture most likely to fail
IO.export_region(OUT + "/risk.png", bounds=box)  # on the source, before the stack exists
st = U.build_stack([], 2)                        # the scripted baseline alone; now the active document
base = U.crops(OUT + "/base", boxes=[[2 * v for v in box]])   # stack pixels: the box at 2x
# Look at the baseline crop at 100%. If it holds, deliver it: no paid run.
# Scenario MCP: dry-run each candidate on risk.png and on prep["path"]. Same price: run both on the
# full frame, stack them (P2), crop the same box. Cheaper crop: both on risk.png, one quote, a yes.
R.sheet(base["files"] + [OUT + "/risk_a.png", OUT + "/risk_b.png"], OUT + "/risk sheet.jpg",
        labels=["baseline", "<member A>", "<member B>"])
# The winner only, on the full frame (quoted): prep["path"] as in P1.
L = U.place_result(OUT + "/up_win.png", "<member A>, 2x scale", prep=prep, base=st["base"])
print(L["match"])                                # mean under 6 at 256 px
```

- Dry-run each candidate on the crop and on the full frame before the quote. Some upscalers price by
  output size; others charge one flat price for any input up to a size. When the crop quotes the
  same as the full frame, run both candidates on the full frame (`prep["path"]`) and compare them on
  the same crops: two paid jobs, not three.
- The crop shows the failure that matters: a face, lettering or a gradient. When it is cheaper, pay
  for the full frame only when the baseline fails at 100% and one candidate beats it there.
- Each candidate is judged against the baseline's crop of the same area, at the same scale.

## P3. The crop grid

Status: verified live with the default boxes (test 3): 9 layers x 3 boxes, the grid's size, the
layer order restored. Custom `boxes` are not tested.

```python
face, label, sky = [1180, 520, 1436, 776], [300, 1500, 556, 1756], [1800, 80, 2056, 336]
g = U.crops(OUT + "/crops", boxes=[face, label, sky], size=256)
print(g["grid"], g["rows"])
```

- Boxes are in stack pixels. Without `boxes`, the crops sit at the center and at the 1/3 and 2/3
  points of the diagonal.
- Every layer is shown alone for its crops, then visibility is put back. Text layers label the rows.
- Open `crops grid.png` with the image reader. Read it row by row against
  [critique.md](critique.md), then open single crops at full size where two rows are close.
- Smith ranked his candidates the same way, side by side at the same spot (Smith [UorIb_rGZuc
  07:43]).

## P4. Mix two upscales by region

Status: `region_blend` verified live on a marquee with feather 8 (restore test 4: inside matches the
chosen layer, outside the layer below, each under 1). On a stack document not tested.

```python
select_box([1100, 420, 1520, 860])               # or Select Subject (P9), or the user's own
r = U.region_blend("<member A>, 2x scale", feather=8)
print(r["selection"], r["box_share"])
ps_run.run("app.activeDocument.selection.deselect(); return 1;")
R.preview(OUT + "/mix_face.png", crop=[1040, 360, 1580, 920], max_px=0)
```

- `region_blend` feathers the current selection and makes it the layer's mask, replacing the old
  mask. The layer shows only inside it; the layer below shows elsewhere.
- Typical mixes: the faithful take on faces and lettering, the more detailed take on fabric and
  foliage, the baseline on skies and gradients. Kost paints the faces in through a Hide All mask
  (Kost [a2OIpxbuzKE 03:23]); Smith paints the mask black where Preserve Details looks more natural
  (Smith [UorIb_rGZuc 08:16]).
- Look at the region's edge at 100%: a step in sharpness or grain shows as a halo. Raise `feather`
  or move the edge to a natural boundary.

## P5. Keep the original's color under an upscale

Status: verified live (test 4): Luminosity on a tinted layer cut the composite's difference to the
baseline by more than half, in one History state.

```python
L = "<member B>, 2x scale"
r = U.lock(L, "luminosity", base="Original, Preserve Details 2.0, 2x scale")
print(r["blend"], r["before"]["worst"]["mean"], "->", r["after"]["worst"]["mean"])
```

- Use it when a candidate's detail is right but its color drifted. The baseline's color shows
  through; the candidate's lightness carries the detail.
- The composite is measured with whatever is visible: hide the layers above `L` first.

## P6. Restore or colorize: generate and land through the padding

Status: `place_result` with `prep` verified live (upscale test 5): placed through the padding it
matches the source at 256 px; without `prep` it fails the match and the padding shows. The restore
suite placed its real restore with `IO.place` on a square source, so a padded restore end to end is
not tested.

```python
# Scenario MCP (scenario-image, an instruction-edit member):
#   upload prep["path"]; prompt with the change and the keep, for example
#   "Restore this photo: remove scratches, dust and fading, in color. Keep the faces,
#    expressions, pose and framing exactly as they are."
#   Dinda's keep-clause: "without changing anything about the image. Just repair it, clean it
#   and sharpen it" (Dinda [knYusnpB9zI 00:33])
#   two outputs, one quote, the user's yes; download take_1.png and take_2.png
takes = []
for i in (1, 2):
    L = U.place_result(OUT + "/take_%d.png" % i, "Restore, take %d" % i, prep=prep,
                       base="Background")
    print(L["name"], L["content_size"], L["match"])
    takes.append(L["name"])
```

- Each placement is one History state, "Scenario: Place result", with the smart object's source area
  on the canvas and the padding outside it.
- `match` uses the plain difference at 256 px. A restore without a colorize may pass it; a colorize
  fails it by design (mean 29 on an aligned restore). Read P7 for alignment.
- A bad generation still spends credits (Dinda [mSgSaisb6Kg 08:44]): judge both takes before asking
  for more.

## P7. Prove alignment across a colorize

Status: verified live (restore tests 1 and 5): structure ranks the restore (11.3) under a 3 px shift
(14.0) under a drifted copy (22.7); the plain difference of the aligned restore is over 20; the
overlay shows less fringe on the restore than on the drifted copy, with no History state.

```python
for t in takes:
    st = G.structure(t, "Background")["score"]
    plain = G.diff(t, "Background", size=[256, 256])["worst"]["mean"]
    print(t, "structure", st, "plain", plain)
    R.overlay(OUT + "/overlay %s.png" % t, "Background", t)
```

- `G.structure` desaturates, equalizes and high-passes both at a 256 px long side, so color and tone
  do not count; a shift or a scale change does. Compare takes with each other and before and after a
  fix, never with a fixed number: the damage sets the floor.
- The overlay draws the first layer's lightness in red and the second's in cyan. Gray means aligned.
  Red and cyan fringes on the eyes mean a shift; fringes growing toward the edges mean a scale
  change.
- Dinda aligns on the eyes and accepts movement in the arms (Dinda [mSgSaisb6Kg 05:28]). Read the
  overlay on the eyes first.

## P8. Auto-Align, kept only on a gain

Status: verified live (restore tests 2 and 3): the drifted copy improved and was kept as "Drifted,
aligned" (structure 22.7 down to 12.8, 19.2 and 20.0 over the three stored runs) with Background
still a Background and no temporary layers left; on the aligned restore the align was not kept and
the layers were unchanged.

```python
r = U.align("Restore, take 1", "Background")      # gain=0.9: keep on a 10% drop or more
print(r["kept"], r["structure_before"], "->", r["structure_after"], r["moved"], r["scale"],
      r["uncovered"])
if r["kept"] and any(r["uncovered"]):
    print("crop back or mask the bare edge:", r["uncovered"])
```

- Run it only when P7 shows drift. On an already aligned restore it moved the layer 2.5 to 17 px
  over three runs and worsened the score every time; the call then steps History back.
- Run it on a take without padding. A take placed through the padding (P6) has bounds past the
  canvas, which Auto-Align reads as a shift and a scale, so it is not kept. Crop the padding off the
  downloaded result first (P2) and place it with the source's bounds.
- When kept, "Restore, take 1, aligned" lands above the result and the result is hidden; before a
  layered handoff, move it into a group named "Takes" (`psd-handoff` flags hidden layers elsewhere).
- `uncovered` is the bare margin, in canvas pixels, that the aligned layer leaves on each side. Crop
  back (Dinda [G5yuLhm0SdM 10:55]) or let the original show there.
- When Auto-Align fails, nudge by hand in Difference on the eyes (Dinda [mSgSaisb6Kg 05:28]), or
  re-run the member with a better ratio.

## P9. Lock the original's tones and blend the face

Status: `lock` in Color mode verified live (upscale test 4b: luminance from the base within 3
levels, hue from the candidate within 5 degrees). Select Subject (`autoCutout`) verified live in the
compositing suite. `region_blend` verified live (restore test 4).

```python
r = U.lock("Restore, take 1", "color", base="Background")
print(r["blend"], r["before"]["worst"]["mean"], "->", r["after"]["worst"]["mean"])

SUBJECT = r"""
var d = app.activeDocument;
d.activeLayer = d.layers.getByName("Background");      // Select Subject reads the active layer
var desc = new ActionDescriptor();
desc.putBoolean(stringIDToTypeID("sampleAllLayers"), false);
executeAction(stringIDToTypeID("autoCutout"), desc, DialogModes.NO);
try { return app.activeDocument.selection.bounds.toString(); } catch (e) { return null; }
"""
# the people from take 2 over take 1: select them on the original, then mask take 2 to it
ps_run.run(SUBJECT, undo="Scenario: Select subject")   # or select_box(face) for one face
U.region_blend("Restore, take 2", feather=8)
ps_run.run("app.activeDocument.selection.deselect(); return 1;")
```

- Color mode keeps the original's lightness, so every pore, crease and catchlight stays the
  original's: "This remains the exact same image" (Dinda [G5yuLhm0SdM 08:08]). It also keeps the
  damage, so it fits a colorize of a clean scan better than a restore of a scratched one.
- For a damaged photo, Dinda paints a faithfully recovered face over the restore, clips a Color copy
  of the restore above it so the face takes the restore's color, and puts Curves below the Color
  layers (Dinda [knYusnpB9zI 06:52]; [knYusnpB9zI 07:26]; [knYusnpB9zI 07:58]).
- Gate by eye: toggle the restore on and off at 100% on the eyes and mouth.
- Skin that came out pale: a Solid Color fill in Multiply, masked to the skin, at opacity about 60
  to 72 (Dinda [G5yuLhm0SdM 08:41]; [G5yuLhm0SdM 09:14]). Color that leaks (lipstick onto skin and
  teeth) is painted back with a sampled color (Dinda [G5yuLhm0SdM 04:22]).

## P10. Finish and deliver

Status: `A.deliverable` verified live (`test_audit_live.py`); the 300 ppi step verified live as
written (`test_upscale_live.py`, a 2400 x 1600 px document at 72 ppi). The finishing filters are by
hand ([gui-paths.md](gui-paths.md)); not tested by script.

```python
# Print, on the delivered document (never the master): 300 ppi without resampling first. The pixels
# stay; the print size becomes pixels / 300 (2400 px prints 8 in). A target print size in inches x
# 300 gives the pixels the upscale must reach.
h0 = A.history()
r = ps_run.run("var d = app.activeDocument; d.resizeImage(undefined, undefined, 300, ResampleMethod.NONE);"
               " return [d.width.as('px'), d.height.as('px'), d.resolution];",
               undo="Scenario: Print resolution")
assert r["ok"] and A.history_gate(h0, "Scenario: Print resolution") == []
print(A.deliverable("print"))     # or "web" (sRGB 8-bit, long edge 4096 or less), "psd-handoff"
R.preview(OUT + "/final.png")
R.preview(OUT + "/final_face.png", crop=face, max_px=0)
```

- A downloaded restore can arrive over-sharpened: Dinda blurs a copy 1 px, then 0.8, then sharpens
  the Stamp Visible layer once and adds grain at 20, lowered to 12 (Dinda [knYusnpB9zI 08:29];
  [knYusnpB9zI 09:02]; [knYusnpB9zI 09:35]).
- Hot color after a colorize: Geller lowers Saturation to -33 and prefers Vibrance for skin (Geller
  [jIvcJtPsJss 02:18]; [jIvcJtPsJss 02:56]); Alwash shifts Yellows toward orange for faces (Alwash
  [WwRbCKao7S4 02:08]).
- Smoothed skin after an upscale: Camera Raw Texture, Clarity and Sharpening on the upscaled layer
  (Marsh [ZCTPo7M8Eyg 04:57]), or hand it to scenario-photoshop-compositing.
- The "web" profile caps the long edge at 4096: a 4x upscale for print fails it by design.
- Losing takes stay hidden inside a group named "Takes", where `A.deliverable("psd-handoff")`
  accepts them; it flags hidden layers anywhere else. Ask before removing any.

## P11. Rejoin one changed layer at full resolution

Status: not tested. Built from `IO.export_region`, `IO.place` and `G.diff`, each verified live in
the lead's suites.

```python
name = "Harmonized subject"
info = A.layer_find(name)[0]
b = info["bounds"]
ex = IO.export_region(OUT + "/layer.png", bounds=b, layer=name)
# Scenario MCP: upscale ex["path"] 2x (scenario-image-editing), quote and yes first;
#   download OUT + "/layer_2x.png"
new = IO.place(OUT + "/layer_2x.png", name + ", upscaled 2x", bounds=b, fit="exact",
               xmp={"source": name, "factor": 2})
w, h = b[2] - b[0], b[3] - b[1]
k = 256.0 / max(w, h)
print(G.diff(new["name"], name, region=b, size=[int(w * k), int(h * k)])["worst"])  # under 6
```

- Smith brought the 2x result back into the document, scaled it 50%, nudged it in Difference until
  it read black, and reused the Harmonize mask (Smith [iy0IxTpT4OY 03:15]; [iy0IxTpT4OY 03:47];
  [iy0IxTpT4OY 04:20]). `IO.place` with the layer's bounds does the fitting.
- Reuse the mask: Cmd-click the old layer's mask thumbnail to load it as a selection, then
  `U.region_blend(new["name"], feather=0)`, and hide the old layer.
- A layer with transparent edges exports merged pixels inside its bounds; check the edge at 100%.
