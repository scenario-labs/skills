# Procedures (toolkit calls, in order)

Each procedure names the calls it runs and its status. "Verified live" means
`test_composite_live.py`, `test_retouch_live.py` or another live suite named runs those calls on
Photoshop 27.11 (macOS). "Not tested" means the block was written from the toolkit's code and
Adobe's documentation but never run as shown. Every call is one `ps_run` job: read the error after
each one.

Scenario steps appear as comments. They go through the Scenario MCP with the `scenario` skill
(connection, `recommend`, the price quote and the user's yes before every paid run, job waiting),
`scenario-image` (plates, subjects, instruction edits) and `scenario-image-editing` (background
removal, relight, split into layers).

Setup for every block:

```python
import json, math, os, sys
sys.path.insert(0, "<skills>/scenario-photoshop-compositing/scripts")
import ps_composite as C          # also puts scenario-photoshop-expert/scripts on the path
import ps_retouch as RT
import ps_run, ps_io as IO, ps_gates as G, ps_review as R, ps_audit as A
OUT = "/path/to/a/work/folder"    # never the folder of the user's PSD

# History: h0 = A.history() right before a call; A.history_gate(h0, undo) == [] after it (one new
# state, named); A.step_back(h0, undo) to undo a trial. Never the list length or a bare index.
# A call that raises or times out: recover as scenario-photoshop-expert's Quality gates say.

def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
```

## P0. Session and brief

Status: `doc_state` verified live (`test_audit_live.py`).

```python
s = A.doc_state()
assert s["name"] == "beach.psd", s["name"]          # the document the brief names
canvas = [s["width"], s["height"]]
EL, PLATE = "Bottle", "Plate, beach"                 # element and plate layer names
light = 135          # degrees the key light comes from: 0 right, 90 top, 135 top left
keep = "label text, cap shape, the model's face"     # masked back after any regeneration
```

Read the light from the plate's own shadows: they point away from the light. No visible shadows: ask
the user.

## P1. Plate or element from Scenario, then placed

Status: `IO.place` verified live (`test_mockup_live.py`, `test_keyart_live.py`,
`test_restore_live.py`); the Scenario steps are not run here.

```python
# Scenario: quote, then the user's yes, before each run.
#   plate   -> scenario-image: "beach at golden hour, sun low from the left, empty foreground"
#   element -> scenario-product-shots or scenario-image, lit from the same side as the plate
#   cutout  -> scenario-image-editing: background removal returns a PNG with transparency
L = IO.place(OUT + "/bottle_cut.png", EL, bounds=[820, 560, 1180, 1300], fit="contain",
             xmp={"modelId": "<model id>", "assetId": "<asset id>", "prompt": "<prompt>"})
R.preview(OUT + "/p1_canvas.png")   # scale against the plate, horizon, camera height
```

A cutout PNG with transparency serves every later step, `shadows` included. A full-frame element
needs P2 or P3 first.

## P2. Cutout by Select Subject

Status: verified live (`test_7_subject_mask`, on a photo of an owl). Not tested on hair or a person.

```python
C.subject_mask(EL)       # Select Subject on that layer alone, as its layer mask; one History state
# Refuses when the layer already has a mask. Hair: Select and Mask by the user (gui-paths.md).
```

Segmentation by a Scenario model (not tested). `scenario-image` (step 4) finds segmentation models
through `recommend` with `capability="img2img"` and the need in words; they take a short noun phrase
or a box and return one mask per object. Quote, then the user's yes.

```python
full = [0, 0, canvas[0], canvas[1]]
IO.export_region(OUT + "/el.png", bounds=full, layer=EL)     # upload this file as the input
# Scenario: the segmentation run on "the bottle"; download its mask as OUT + "/mask.png".
from PIL import Image
im = Image.open(OUT + "/el.png").convert("RGBA")
m = Image.open(OUT + "/mask.png").convert("L").resize(im.size)  # white = object; check the schema
im.putalpha(m)
im.save(OUT + "/el_cut.png")
IO.place(OUT + "/el_cut.png", EL + ", cut", bounds=full, fit="exact")   # then hide the original
```

## P3. Cutout by channel and Blend If, frozen in a smart object

Status: `channel_pick` and `blend_if` verified live (`test_6_channel_pick`, `test_5_blend_if`). The
freeze uses `newPlacedLayer`, verified inside `RT.highpass_smoother`; the slider heuristic below is
not tested.

```python
keep_box, drop_box = [400, 300, 520, 420], [60, 40, 260, 160]   # tree, sky (on the element)
p = C.channel_pick(keep_box, drop_box)        # {"best": "blue", "scores": {...}, ...}
i = ("red", "green", "blue").index(p["best"])
k, dr = p["keep_mean"][i], p["drop_mean"][i]
lo, hi = sorted([k + 0.4 * (dr - k), k + 0.7 * (dr - k)])
lo, hi = int(lo), int(hi)
if dr > k:     # background brighter than the subject: the white slider hides it, split for softness
    C.blend_if(EL, p["best"], this=(0, 0, lo, hi))
else:          # background darker: the black slider hides it
    C.blend_if(EL, p["best"], this=(lo, hi, 255, 255))
ps_run.run('app.activeDocument.activeLayer = app.activeDocument.layers.getByName("%s");'
           ' executeAction(stringIDToTypeID("newPlacedLayer"), new ActionDescriptor(),'
           ' DialogModes.NO); return app.activeDocument.activeLayer.name;' % EL,
           undo="Scenario: Freeze Blend If")
```

`executeActionGet` never reports Blend If: check the effect with P4, not the descriptor. `getByName`
finds top-level layers only; inside a group, select the layer first.

## P4. Halo gate, Minimum on the mask, and three backgrounds

Status: `G.halo` and `C.fix_halo` verified live (`test_1_halo`: a 3 px fringe dropped to under a
third). The three-background preview is not tested.

```python
h = G.halo(EL)                                  # light_rim, dark_rim over a 2 px band
if max(h["light_rim"], h["dark_rim"]) > 8:
    h0 = A.history()
    r = C.fix_halo(EL, px=1)                    # Minimum, roundness, on the mask; mask made from
    print(r["before"], r["after"])              # transparency when the layer has none
    assert A.history_gate(h0, "Scenario: Clean edge") == []
    # Still above 8: A.step_back(h0, "Scenario: Clean edge"), then px=2, then 3. Each call erodes the
    # current mask, so passes left in place add up (1 then 2 is 3 px). Past 3 px the subject thins:
    # fix the mask by hand.

BACKDROP = r"""
var d = app.activeDocument, e = d.layers.getByName(%NAME%);
var k = d.artLayers.add(); k.name = "Edge check"; k.move(e, ElementPlacement.PLACEAFTER);
var c = new SolidColor(); c.rgb.red = %V%; c.rgb.green = %V%; c.rgb.blue = %V%;
d.selection.selectAll(); d.selection.fill(c); d.selection.deselect(); return true;
"""
box = [800, 540, 1200, 1320]                     # element bounds plus a margin
for tag, v in (("black", 0), ("white", 255), ("gray", 128)):
    mark = A.history()
    ps_run.run(BACKDROP.replace("%NAME%", json.dumps(EL)).replace("%V%", str(v)), undo="Scenario: Edge check")
    assert A.history_gate(mark, "Scenario: Edge check") == []
    R.preview(OUT + "/p4_%s.png" % tag, crop=box, max_px=0, layers_only=[EL, "Edge check"])
    A.step_back(mark, "Scenario: Edge check")   # raises unless the marked state is active again
R.sheet([OUT + "/p4_%s.png" % t for t in ("black", "white", "gray")], OUT + "/p4_edges.jpg",
        labels=["black", "white", "gray"])
```

Open the sheet: no rim, no see-through fur, no stair-stepped edge on any of the three.

## P5. Light

Status: not tested (Harmonize has no script call; the relight is a Scenario step). The texture gate
uses `G.texture`, verified live on noise against flat (`test_gates_live.py`).

```python
# Route A, Photoshop: the user runs Harmonize on a pixel copy of the element (gui-paths.md),
#   keeps one of three variations, names the result "Bottle, harmonized".
# Route B, Scenario: quote, yes, then a relight tool model through scenario-image-editing on the
#   cutout with the light direction in words; IO.place the result over EL as "Bottle, relit".
LIT = "Bottle, harmonized"
# Texture before the split: G.texture reads a layer at its own opacity, so at 50% it reads half.
ratio = (G.texture(LIT, {"alpha": EL, "contract": 3})["energy"]
         / G.texture(EL, {"alpha": EL, "contract": 3})["energy"])
assert ratio >= 0.6, ratio          # under 0.6: mask the original back over the soft parts
LUMA = r"""
var d = app.activeDocument, h = d.layers.getByName(%LIT%);
var y = h.duplicate(); y.name = h.name + " (luminosity)"; y.blendMode = BlendMode.LUMINOSITY;
h.opacity = 50;                      // color from the result, partway (Smith brings it back by eye)
return {luma: y.name, color: h.name};
"""
ps_run.run(LUMA.replace("%LIT%", json.dumps(LIT)), undo="Scenario: Light split")
```

Then mask the original back over the `keep` list (P9 `RESTORE`). Moving the element afterward means
running the light again: the result's shadows and reflections are baked in.

## P6. Shadows

Status: `C.shadows` verified live (`test_2_shadows`: both layers Multiply under the element, cast
under 0.6 of the element's height, ground under the base darker by more than 3 levels;
`test_8_shadows_follow_layer_mask`: a masked plate casts the mask's shape).

```python
base = [820, 1290, 1180, 1310]                   # a strip of ground just under the element
before = G.stats(None, base)["luminance"]
r = C.shadows(EL, angle=light)                   # sun: cast_blur=0.01; overcast: cast_blur=0.05
after = G.stats(None, base)["luminance"]
assert after < before - 3, (before, after)
R.preview(OUT + "/p6.png")                       # cast direction against the plate's own shadows
```

`shadows` cuts the silhouette from the layer's transparency and from its layer mask when the mask is
on, so an element cut by a mask (P2, or a full-frame smart object) casts its own shape (verified
live, `test_8_shadows_follow_layer_mask`). A vector mask is not read: convert it to a layer mask
first.

The user then paints the cast's mask to fade it with distance (gui-paths.md).

## P7. Tone

Status: verified live (`test_3_tone`: at strength 0.6 the cast distance to the scene fell under 0.7
of the start, luminance within 12%, Curves clipped).

```python
t = C.match_tone(EL, strength=0.5)               # clipped "Tone match" Curves at the chain top
assert dist(t["cast_after"], t["cast_scene"]) < dist(t["cast_before"], t["cast_scene"])
assert abs(t["luminance_after"] - t["luminance_before"]) <= 0.12 * t["luminance_before"]
```

`match_tone` moves color only. Brightness and contrast against the key light are a clipped Levels or
Curves by eye; White fixes too-dark variations that way.

## P8. Grain

Status: verified live (`test_4_grain`: texture energy more than doubled and ended within 50% of the
scene's; `test_4c`: a second element got its own layer, the first element's grain pixels unchanged,
and a name clipped to another element raised). The patch call is the same call on another layer.

```python
g = C.match_grain(EL)              # clipped Overlay noise in "Grain match: Bottle", one per element
if "action" not in g:
    assert abs(g["end"] - g["target"]) <= 0.5 * g["target"], g
R.preview(OUT + "/p8_100.png", crop=box, max_px=0)  # then a 200% look at the edge
PATCH = "Generative edit, sand"                  # a generated patch inside the plate
g2 = C.match_grain(PATCH)                        # its own layer, "Grain match: Generative edit, sand"
```

Each element or patch gets its own grain layer, named `"Grain match: " + layer` unless `name=` says
otherwise. A rerun on the same element reuses its layer. A layer of that name clipped to another
element raises: pass another `name=`. Never add grain to the whole frame to hide one smooth patch.

## P9. Skin after a generative edit

Status: `G.texture` and `G.stats` skin line verified live on synthetic patches
(`test_gates_live.py`); `RT.frequency_separation`, `RT.verify_fs`, `RT.suggest_radius`,
`RT.highpass_smoother` and `RT.dodge_burn` verified live (`test_retouch_live.py`). `RT.skin_tone` on
a real face, `RESTORE` and `TEXTURE` are not tested.

```python
ORIG, NEW = "Background", "Face, edited"         # the pre-edit layer and the result over it
face = [520, 560, 860, 980]                      # the whole face, for crops and overlays
cheek = [610, 820, 700, 900]                     # flat skin: no eyes, brows, lips or hair
ratio = G.texture(NEW, cheek)["energy"] / G.texture(ORIG, cheek)["energy"]
tone = RT.skin_tone(cheek, layer=NEW)            # skin_line_delta, reading
print(round(ratio, 2), tone["skin_line_delta"], tone["reading"])
R.before_after(OUT + "/orig_face.png", OUT + "/new_face.png", OUT + "/p9_ba.jpg")
```

Export the two face crops first with `IO.export_region(path, bounds=face, layer=...)`. Compare eyes,
teeth, moles and hairline; any change there is restored, whatever the numbers say.

Restore identity from the original, under the user's eye:

```python
RESTORE = r"""
var d = app.activeDocument, o = d.layers.getByName(%ORIG%), top = d.layers.getByName(%NEW%);
var c = o.duplicate(top, ElementPlacement.PLACEBEFORE); c.name = %NAME%;
c.visible = true; d.activeLayer = c;
var boxes = %BOXES%, first = true;
for (var i = 0; i < boxes.length; i++) {
  var b = boxes[i], cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2, rx = (b[2] - b[0]) / 2,
      ry = (b[3] - b[1]) / 2, p = [];
  for (var j = 0; j < 72; j++) { var a = j * Math.PI / 36; p.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]); }
  d.selection.select(p, first ? SelectionType.REPLACE : SelectionType.EXTEND); first = false;
}
d.selection.feather(%FEATHER%);
var m = new ActionDescriptor(); m.putClass(charIDToTypeID("Nw  "), charIDToTypeID("Chnl"));
var r = new ActionReference(); r.putEnumerated(charIDToTypeID("Chnl"), charIDToTypeID("Chnl"), charIDToTypeID("Msk "));
m.putReference(charIDToTypeID("At  "), r);
m.putEnumerated(charIDToTypeID("Usng"), charIDToTypeID("UsrM"), charIDToTypeID("RvlS"));
executeAction(charIDToTypeID("Mk  "), m, DialogModes.NO);
d.selection.deselect(); return c.name;
"""
eyes = [[560, 640, 660, 700], [720, 640, 820, 700]]
ps_run.run(RESTORE.replace("%ORIG%", json.dumps(ORIG)).replace("%NEW%", json.dumps(NEW))
           .replace("%NAME%", json.dumps("Original eyes")).replace("%BOXES%", json.dumps(eyes))
           .replace("%FEATHER%", "6"), undo="Scenario: Restore eyes")
```

`RESTORE` and `TEXTURE` duplicate straight into place: a copy made above a clipping base and moved
later releases the whole clipping chain. If `NEW` already has clipped layers, put the chain top's
name in `%NEW%`.

Check alignment first: `R.overlay(OUT + "/p9_align.png", NEW, ORIG, crop=face)` must read gray. A
shifted result cannot take the original's eyes or texture; place it again aligned, or regenerate.

Restore texture lost on aligned skin (Dinda's method: the original's High Pass in Linear Light):

```python
r0 = RT.suggest_radius(cheek)["pick"] or 2       # the radius where pores disappear
TEXTURE = r"""
var d = app.activeDocument, o = d.layers.getByName(%ORIG%), top = d.layers.getByName(%NEW%);
var t = o.duplicate(top, ElementPlacement.PLACEBEFORE); t.name = "Original texture (High Pass)";
t.visible = true; d.activeLayer = t;
executeAction(stringIDToTypeID("newPlacedLayer"), new ActionDescriptor(), DialogModes.NO);
t = d.activeLayer; t.applyHighPass(%R%); t.blendMode = BlendMode.LINEARLIGHT; t.opacity = 50;
var m = new ActionDescriptor(); m.putClass(charIDToTypeID("Nw  "), charIDToTypeID("Chnl"));
var r = new ActionReference(); r.putEnumerated(charIDToTypeID("Chnl"), charIDToTypeID("Chnl"), charIDToTypeID("Msk "));
m.putReference(charIDToTypeID("At  "), r);
m.putEnumerated(charIDToTypeID("Usng"), charIDToTypeID("UsrM"), charIDToTypeID("HdAl"));
executeAction(charIDToTypeID("Mk  "), m, DialogModes.NO);
return t.name;
"""
ps_run.run(TEXTURE.replace("%ORIG%", json.dumps(ORIG)).replace("%NEW%", json.dumps(NEW))
           .replace("%R%", str(r0)), undo="Scenario: Original texture")
# The user paints the black mask white on skin only (gui-paths.md); then the ratio again.
```

Linear Light doubles the High Pass, so 50% opacity adds the original's detail once. Dinda uses 80%
by eye. Unaligned skin, or no original: `C.match_grain(NEW)` adds monochrome grain instead.

Frequency separation for blotches and tone, then the scaffolds:

```python
pick = RT.suggest_radius(cheek)["pick"]
fs = RT.frequency_separation(radius=pick)        # group "Frequency Separation", one History state
v = RT.verify_fs()                               # |group - stamp|
assert v["worst"]["max"] <= 2, v                 # 8-bit; 0 to 1 at 16-bit
# The user paints "Retouch (tone)" (clipped, Lighten for dark circles) at low flow.
sm = RT.highpass_smoother()                      # Vivid Light smart object, hidden behind a black mask
db = RT.dodge_burn()                             # "Dodge" and "Burn" Curves with black masks
# All three start invisible: G.diff(None, ORIG) max 0 until a mask is painted.
```

After any retouch: the ratio again on the same cheek (at least 0.6 against the original) and the
skin line within 10.

## P10. Split a flat image into layers

Status: not tested.

```python
# Scenario: quote, yes, then the split-into-layers capability (scenario-image-editing) on the
#   flattened image; download every returned piece.
pieces = [("Sky", OUT + "/l0.png"), ("Castle", OUT + "/l1.png"), ("Hero", OUT + "/l2.png")]
for name, path in pieces:                        # bottom first, so the last lands on top
    IO.place(path, name, bounds=[0, 0, canvas[0], canvas[1]], fit="exact",
             xmp={"modelId": "<model id>", "assetId": "<asset id>"})
GROUP = r"""
var d = app.activeDocument, g = d.layerSets.add(); g.name = "Split layers";
var names = %NAMES%;
for (var i = 0; i < names.length; i++) d.layers.getByName(names[i]).move(g, ElementPlacement.INSIDE);
return g.name;
"""
ps_run.run(GROUP.replace("%NAMES%", json.dumps([n for n, _ in pieces])), undo="Scenario: Group split")
print(G.diff("Split layers", "Background"))     # small mean: the pieces rebuild the source
# Check the stacking order inside the group after the moves: the first piece belongs at the bottom.
```

Hide one piece at a time and look at 100%: the piece below must be filled where the upper one sat,
or moving the upper one opens a hole.

## P11. Deliver

Status: `A.deliverable("psd-handoff")` verified live (`test_audit_live.py`).

```python
assert A.deliverable("psd-handoff") == []
R.preview(OUT + "/final.png")
R.sheet([OUT + "/p4_edges.jpg", OUT + "/p6.png", OUT + "/p8_100.png"], OUT + "/final_crops.jpg")
```

The report lists each layer made, its History state name, every gate number and what was not
verified. Nothing is saved over the user's file.
