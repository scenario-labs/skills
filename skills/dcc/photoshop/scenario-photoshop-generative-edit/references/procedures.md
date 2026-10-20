# Procedures (toolkit calls, in order)

Each procedure names the calls it runs and its status. "Verified live" means
`test_generative_live.py` (or another live suite named) runs those calls on Photoshop 27.11 (macOS).
"Not tested" means the block was written from the toolkit's code and Adobe's documentation but never
run as shown. Every call is one `ps_run` job: read the error after each one.

Scenario steps appear as comments. They go through the Scenario MCP with the `scenario` skill
(connection, `recommend`, the price quote and the user's yes before every paid run, job waiting) and
`scenario-image` (the member, its mask field, its reference fields).

Setup for every block:

```python
import json, os, sys
sys.path.insert(0, "<skills>/scenario-photoshop-generative-edit/scripts")
import ps_generative as GE        # also puts scenario-photoshop-expert/scripts on the path
import ps_run, ps_io as IO, ps_review as R, ps_audit as A
OUT = "/path/to/a/work/folder"    # never the folder of the user's PSD

def around(b, pad, canvas):       # a box grown by pad, clipped to the canvas
    return [max(0, b[0] - pad), max(0, b[1] - pad),
            min(canvas[0], b[2] + pad), min(canvas[1], b[3] + pad)]
```

## P0. Session, brief, route

Status: `doc_state` verified live (`test_audit_live.py`); `IO.selection` runs in every suite.

```python
s = A.doc_state()
assert s["name"] == "street.psd", s["name"]      # the document the brief names
canvas = [s["width"], s["height"]]
sel = IO.selection()["bounds"]                   # None: build one (P1)
change = "the parked car and its shadow"
keep = "the cyclist, the curb, the light"
```

Route by the edit:

| Edit                                      | Route                                        | Procedure |
| ----------------------------------------- | -------------------------------------------- | --------- |
| Small cleanup, user at the keyboard       | suggest Photoshop's Remove tool              | gui-paths |
| Replace, add, recolor or remove an object | Scenario inpaint or instruction edit         | P2, P3    |
| Swap from a reference (clothing, product) | Scenario edit with references                | P4        |
| Extend the canvas                         | expand tool model or inpaint                 | P5        |
| Area larger than one output               | tiles                                        | P6        |
| New angle of an object                    | instruction edit, orbit views, Rotate Object | P7        |
| Red notes drawn on the image              | instruction edit with a markup reference     | P8        |
| Trained style inside a selection          | the trained model                            | P9        |

## P1. Selections by script

Status: Select Subject (`autoCutout`) is verified live in the compositing suite. The DOM selection
calls below are standard but not tested as shown.

```python
SEL = r"""
var d = app.activeDocument, a = %ARGS%;
function rect(b) { return [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]]; }
if (a.subject) {                                       // Select Subject on the active layer
  var desc = new ActionDescriptor();
  desc.putBoolean(stringIDToTypeID("sampleAllLayers"), false);
  executeAction(stringIDToTypeID("autoCutout"), desc, DialogModes.NO);
}
if (a.box) d.selection.select(rect(a.box), a.subject ? SelectionType.INTERSECT : SelectionType.REPLACE);
if (a.minus) d.selection.select(rect(a.minus), SelectionType.DIMINISH);
if (a.grow) d.selection.expand(UnitValue(a.grow, "px"));
try { return d.selection.bounds; } catch (e) { return null; }
"""
args = {"subject": False, "box": [610, 380, 940, 620], "minus": None, "grow": 4}
r = ps_run.run(SEL.replace("%ARGS%", json.dumps(args)), undo="Scenario: Select car")
```

- The selection is the footprint of the result. A removal includes the shadow and a few pixels
  around the object. New sleeves or a longer shadow need room to grow into.
- Subtract what must stay in front (hair over a swapped jacket) with `minus`, or ask the user to
  paint it out with the Selection Brush in Subtract mode.
- `subject` plus `box` keeps one subject among several.
- Hand-drawn selections (Selection Brush, Object Selection, Quick Mask) are the user's job:
  [gui-paths.md](gui-paths.md).
- A gray (partial) selection exports its density into `mask_edit.png`. Not tested with a Scenario
  member.

## P2. Inpaint or instruction edit: the round trip

Status: `capture`, `check`, `place_edit` and `verify` verified live (`test_generative_live.py`; the
seam gate on two takes of a real Scenario inpaint; `place_edit` gated with `A.history_gate` as
below). `R.sheet` verified live in the lead's `test_io_live.py`. The take loop is not tested as
written.

```python
cap = GE.capture(OUT + "/car", polarity="white")
# polarity comes from the member's mask field (scenario-image): "white" (white = edit), "black",
# "alpha" (an RGBA mask, transparent = edit) or "punch" (no mask; input.png is transparent where
# the member should edit). For more context raise margin=; never grow the selection for context.
box = cap["bounds"]
box_w = box[2] - box[0]
```

GATE: open `cap["context"]` and `cap["mask_edit"]` with the image reader. The change sits inside the
white and nothing else does.

```python
# Scenario MCP:
#   recommend with the capability ("inpaint" or "instruction edit") and the user's own words
#   upload cap["input"] and, unless polarity is "punch", cap["mask_model"]; references (P4)
#   prompt: the change, then the keep: "Remove the parked car and its shadow. Keep the cyclist,
#   the curb and the light unchanged."
#   quote the exact payload, get the user's yes, run, wait, download: 1 output by default,
#   3 here because the user asked for a choice, OUT + "/car/take_1.png" to take_3.png
passed = []
for i in (1, 2, 3):
    p = OUT + "/car/take_%d.png" % i
    r = GE.check(cap, p)
    r["res_ok"] = r["b_size"][0] >= box_w
    ok = (r["aspect_ok"] and r["edited"] and not r["polarity_suspect"] and r["seam_ok"]
          and r["res_ok"])
    print(i, ok, r["seam"], "outside mean", r["outside"]["mean"])
    if ok:
        passed.append(p)
R.sheet([cap["context"]] + passed, OUT + "/car/takes.jpg",
        labels=["context"] + [os.path.basename(p) for p in passed])
```

Reading a failed take:

- **`aspect_ok` false:** the member returned another ratio. Recapture with a margin that gives a
  supported ratio. Never crop or stretch the take to fit.
- **`edited` false:** the take equals its input. Follow the lead's rule for a take equal to its
  input (scenario-photoshop-expert, Quality gates).
- **`polarity_suspect`:** the member read the mask inverted. Recapture with the other polarity.
- **Seam bias 12 or more:** a tone shift at the edge. Re-run, or place it and match tone with the
  compositing skill when the take is otherwise the best.
- **Seam residual 6 or more:** the take moved or changed scale. Re-run; never nudge it into place.
- **`res_ok` false:** the take is coarser than the photo. Use tiles (P6), a member with a larger
  output, or upscale the take with the upscale-restore skill before placing it.
- An outside mean above 10 on a passing take is normal: the member re-rendered the frame.

Then open `takes.jpg`, and each passing take at 100% inside the mask, against
[critique.md](critique.md). A take that fails a code gate is never placed.

```python
best = passed[0]                                  # the take chosen by eye
prompt = "Remove the parked car and its shadow. Keep the cyclist, the curb and the light unchanged."
h0 = A.history()                                  # right before the call
L = GE.place_edit(cap, best, "Car removed, take 1", feather=2,
                  xmp={"assetId": "<asset id>", "modelId": "<member id>", "prompt": prompt,
                       "createdAt": "2026-10-19"})
assert L["bounds"] == box
assert A.history_gate(h0, "Scenario: Generative edit") == []   # one new state; never the list length
v = GE.verify(cap)                                # composite at the box against context.png
assert v["untouched"] and v["edited"], v          # outside max 2 or less past 2 x feather + 2 px; inside changed
R.preview(OUT + "/car/canvas.png")
seam = R.preview(OUT + "/car/seam_100.png", crop=around(box, 32, canvas), max_px=0)
```

- `place_edit` adds one History state, "Scenario: Generative edit", and refuses when the canvas size
  changed since the capture.
- For a 200% look, enlarge the 100% crop with nearest-neighbor resampling (Pillow, `Image.NEAREST`)
  and open it.
- A residual between 4 and 6 is borderline:
  `R.overlay(OUT + "/car/overlay.png", L["name"], "Background", crop=box)` shows gray where the take
  lines up with the base and red or cyan fringes where it does not. Not tested on a placed take.

## P3. Removal and the clean plate

Status: the round trip is P2 (verified live). The selection and mask steps are not tested.

- **Selection:** the object, its shadow and a few pixels around it (P1 with `grow`).
- **Prompt:** empty, or what lies behind ("wet asphalt, painted curb"), for an inpaint member. For
  an instruction member: "Remove the car and its shadow. Fill with the street behind it. Keep
  everything else unchanged."
- **Hard removals in parts:** remove the thin parts (straps, wires) first, then the body, each its
  own capture and layer.
- **Object touching a subject** (a bag against a body): grow the object's selection about 4 px, run
  P2, then give the subject's own edge back by masking the subject out of the placed layer:

```python
EDGE = r"""
var d = app.activeDocument, a = %ARGS%;
d.activeLayer = d.layers.getByName(a.base);
var desc = new ActionDescriptor();
desc.putBoolean(stringIDToTypeID("sampleAllLayers"), false);
executeAction(stringIDToTypeID("autoCutout"), desc, DialogModes.NO);     // the subject
d.activeLayer = d.layers.getByName(a.layer);
var r = new ActionReference();
r.putEnumerated(charIDToTypeID("Chnl"), charIDToTypeID("Chnl"), charIDToTypeID("Msk "));
var s = new ActionDescriptor(); s.putReference(charIDToTypeID("null"), r);
executeAction(charIDToTypeID("slct"), s, DialogModes.NO);                // target the layer mask
var black = new SolidColor(); black.rgb.red = 0; black.rgb.green = 0; black.rgb.blue = 0;
d.selection.fill(black);
d.selection.deselect();
return a.layer;
"""
ps_run.run(EDGE.replace("%ARGS%", json.dumps({"base": "Background", "layer": L["name"]})),
           undo="Scenario: Keep subject edge")
```

GATE: `GE.verify(cap)["untouched"]` still holds; the subject's edge at 100% shows no halo and no
leftover of the object.

- A cleanup the user can do in seconds (a sign, a wire, a spot) goes to Photoshop's Remove tool,
  which spends no generative credits ([gui-paths.md](gui-paths.md)).

## P4. References: clothing, a product, a likeness

Status: not tested. `export_region` is verified live for the composite; its `layer=` argument has no
live test.

```python
ref = A.layer_find("Jacket ref")[0]              # a layer pre-cut to the one object
r = IO.export_region(OUT + "/refs/jacket.png", bounds=ref["bounds"], layer="Jacket ref")
ps_run.run('app.activeDocument.layers.getByName("Jacket ref").visible = false; return 1;')
cap = GE.capture(OUT + "/jacket", polarity="white")   # the reference is out of the context now
# Scenario MCP: upload cap["input"], cap["mask_model"] and refs/jacket.png; the member's
# reference fields come from scenario-image, several references and identities from
# scenario-consistency. Prompt names each reference's role: "Replace his jacket with the jacket
# in the reference image, same color, stitching and buttons. Keep his pose, hands and hair."
```

- Pre-cut each reference to one object, with Select Subject and a layer mask. A hand or a second
  object in the reference comes along into the result.
- Without bounds, `export_region` crops the layer to the selection or the canvas, so pass the
  layer's bounds.
- Draw the selection at the size the object should be: the selection sets the scale.
- Hide the reference layer before `capture`, which exports merged visible pixels.
- For a person, add a keep-clause for likeness ("still looking like himself") and compare the face
  against the original at 100%.

## P5. Expand the canvas

Status: `expand` verified live (one History state "Scenario: Expand canvas", the edit mask with its
32 px band, `original.png`, then `place_edit` and `verify` on a synthetic fill). No real expand
member has been run.

```python
cap = GE.expand(OUT + "/expand_right", right=400, overlap=32)
# cap["canvas"] new size; cap["old"] where the old canvas sits; cap["keep"] the real pixels
# outside the edit; cap["input"] the new canvas with the edit area transparent; cap["mask_model"]
# white = edit; cap["original"] the canvas before, for members that take an image and a size
# Scenario MCP: an expand tool model (scenario-image-editing) with cap["original"] and the target
# size, or an inpaint member with cap["input"] and cap["mask_model"]; prompt empty or a short
# continuation of the scene
r = GE.check(cap, OUT + "/expand_right/take_1.png")
r["res_ok"] = r["b_size"][0] >= cap["canvas"][0]
```

- Send `input.png`, not `context.png`. The new area in the context holds the background color, which
  a member reads as content.
- A member that moves or rescales the source fails `aspect_ok` or the residual. Where expand members
  put the source is not tested; on a failure, switch to an inpaint member with the input and mask,
  which fix the source's position.
- Wide additions go one side per pass: `GE.expand(OUT + "/expand_left", left=400)` after the right
  side is placed and verified. Each pass is one History state.
- When the new canvas exceeds the member's output, `res_ok` fails. Tile the new strip (P6).

## P6. Tiles for a large area

Status: `tile_plan` verified live; the loop is not tested end to end.

```python
TILE_MARGIN = 128
out_side = 1024                                   # the member's output side, from its schema
tile = out_side - 2 * TILE_MARGIN                 # tile plus both margins fits one output
area = IO.selection()["bounds"]                   # the whole edit area, selected
STORE = r"""
var d = app.activeDocument;
var ch = d.channels.add(); ch.name = "Scenario edit area";
d.activeChannels = d.componentChannels;
d.selection.store(ch);
return ch.name;
"""
TILE = r"""
var d = app.activeDocument, b = %BOX%;
d.selection.load(d.channels.getByName("Scenario edit area"), SelectionType.REPLACE);
d.selection.select([[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]], SelectionType.INTERSECT);
try { d.selection.bounds; return true; } catch (e) { return false; }
"""
ps_run.run(STORE, undo="Scenario: Store edit area")

def gap_to(t, keep):                              # 0 when the tile touches the real pixels
    return max(keep[0] - t[2], t[0] - keep[2], 0) + max(keep[1] - t[3], t[1] - keep[3], 0)

keep = cap["keep"]                                # after P5; else the box of the untouched area
tiles = sorted(GE.tile_plan(area, tile, overlap=64), key=lambda t: gap_to(t, keep))
# Count the tiles that touch the edit area before any paid run: one quote for the set.
doc = A.doc_state()
IO.export_mask(OUT + "/area.png", bounds=[0, 0, doc["width"], doc["height"]])   # the area, canvas size
from PIL import Image
with Image.open(OUT + "/area.png") as m:
    tiles = [t for t in tiles if m.convert("L").crop(tuple(t)).getbbox()]
takes = 1
print(len(tiles), "tiles x", takes, "take(s): quote this once, get the user's yes")
for i, t in enumerate(tiles):
    ps_run.run(TILE.replace("%BOX%", json.dumps(t)), undo="Scenario: Tile selection")
    c = GE.capture(OUT + "/tiles/%02d" % i, margin=TILE_MARGIN, polarity="white")
    # Scenario MCP: the same member and settings for every tile; prompt empty or texture only
    # check (P2 gates), then:
    # GE.place_edit(c, take, "Sky fill, tile %02d" % i); assert GE.verify(c)["untouched"]
    # Tile 1 (i == 0) is the proof: it passes P2's gates and a 100% look before tile 2 runs.
    # If it fails, stop and re-plan (member, prompt, tile size) before spending on the rest.
ps_run.run('app.activeDocument.channels.getByName("Scenario edit area").remove(); return 1;',
           undo="Scenario: Remove edit area")
```

- Pass `margin` explicitly. The default (half the selection's long side) would double the box.
- Tiles nearest the real pixels go first, so later tiles see placed tiles as context.
- Never put an object in a tile prompt: it appears in every tile.
- Group the tile layers afterwards (`d.layerSets.add()`, then move each layer inside).

GATE: every tile passes P2's gates; at fit-to-screen, no repeated object and no grid pattern; the
joins between tiles at 100%.

## P7. A new angle of an object

Status: not tested.

- **In place, by instruction:** select the object with room for its new silhouette (a box around
  it), capture, and prompt the change with a keep: "Rotate the car so its rear is three-quarters
  visible. Keep the floor, the light and the reflections." Run P2. Then tighten the mask on the
  placed layer by hand.
- **A whole subject seen from elsewhere:** `scenario-orbit-views` from a pre-cut reference (P4
  export). Clean-plate the old subject first (P3) when it must disappear, place the new view with
  `IO.place`, and finish with the compositing skill.
- **Photoshop's Rotate Object as a reference:** the user duplicates the layer and turns it with
  Rotate Object ([gui-paths.md](gui-paths.md)). Its render becomes the reference for a Scenario edit
  (P4). It works best on objects; faces may warp.

GATE: perspective follows the scene's horizon; contact shadows and reflections match the new pose.

## P8. Annotation-driven edit

Status: not tested as a whole. Verified live (`test_4b_markup_group_and_edited`): with a hidden
"Scenario markup" group holding the active layer, `place_edit` moves the take out of the group
(`moved_out_of`, parent the document), and `verify` returns `edited` true for a changed inside and
false for an unchanged one.

```python
cap = GE.capture(OUT + "/markup", polarity="white")   # first: making text layers drops the selection
MARKUP = r"""
var d = app.activeDocument, a = %ARGS%, was = d.activeLayer;
var red = new SolidColor(); red.rgb.red = 230; red.rgb.green = 20; red.rgb.blue = 20;
var g = d.layerSets.add(); g.name = "Scenario markup";
for (var i = 0; i < a.notes.length; i++) {
  var n = a.notes[i], l = g.artLayers.add();
  l.kind = LayerKind.TEXT; l.name = "note " + (i + 1);
  l.textItem.contents = n.text; l.textItem.size = n.pt; l.textItem.color = red;
  l.textItem.position = [UnitValue(n.x, "px"), UnitValue(n.y, "px")];
}
g.visible = false;
d.activeLayer = was;              // the next placement lands beside it, not in the markup group
return g.name;
"""
notes = [{"text": "leather jacket", "pt": 36, "x": 820, "y": 410}]
ps_run.run(MARKUP.replace("%ARGS%", json.dumps({"notes": notes})), undo="Scenario: Markup")
ps_run.run('app.activeDocument.layerSets.getByName("Scenario markup").visible = true; return 1;')
IO.export_region(OUT + "/markup/annotated.png", bounds=cap["bounds"])   # same box, notes visible
ps_run.run('app.activeDocument.layerSets.getByName("Scenario markup").visible = false; return 1;')
# Scenario MCP: an instruction-edit member with cap["input"], the mask, and annotated.png as a
# reference. Prompt: "Apply the red notes in the reference image to the input image. Do not draw
# any red marks or text."
```

- A member that takes one image only gets `annotated.png` as its input, with "Follow the red notes,
  then remove every red mark". `check` still compares against the clean context.
- The user may draw the notes and arrows instead; the capture order stays the same.
- Place and verify as P2. `place_edit` refuses nothing here: a take aimed inside the hidden group is
  moved out (`moved_out_of`). `verify` must return `edited` true as well as `untouched`.
- GATE: P2's gates, and no red mark or letter survives inside the mask.
- The markup group stays hidden; `A.deliverable("psd-handoff")` flags it. Ask the user whether to
  keep it.

## P9. A trained style inside a selection

Status: not tested; alignment of a trained model's output is not measured.

- Model training is a separate Scenario step. Start from the trained model the user names.
- A trained style runs on its base. `model_schema_get` on the trained model returns a `run_with`
  block: call `model_run` on that base, with the trained model in `loras`.
- Pick the route from the base's inputs, read off its schema:
  - **Route A:** the base takes a `mask`. Run P2 with it. No current base read at authoring time
    did.
  - **Route B:** the base takes an `image` with `strength`. Pass `cap["context"]` as the image at
    low strength. The member restyles the whole box; the layer mask keeps the style inside the
    selection. Raise strength only while `check`'s residual stays under 6.
  - **Route C:** the base takes `referenceImages` and no strength (the edit bases). Pass the capture
    as the first reference and say in the prompt what to change and what to keep.
- A restyle changes tone outside the mask too, so seam bias measures the style, not a seam. Judge
  the edge by eye at 100%, and raise `feather` when the change is strong.

## P10. Takes as layers

Status: `place_edit` verified live; the visibility job is not tested.

```python
names = []
for i, p in enumerate(passed, 1):
    L = GE.place_edit(cap, p, "Car removed, take %d" % i, xmp={"prompt": prompt})
    names.append(L["name"])
SHOW = r"""
var d = app.activeDocument, a = %ARGS%;
for (var i = 0; i < a.names.length; i++)
  d.artLayers.getByName(a.names[i]).visible = (a.names[i] === a.keep);
return a.keep;
"""
crops = []
for n in names:
    ps_run.run(SHOW.replace("%ARGS%", json.dumps({"names": names, "keep": n})))
    assert GE.verify(cap)["untouched"]
    crops.append(R.preview(OUT + "/car/%s.png" % n, crop=around(box, 32, canvas), max_px=0)["path"])
R.sheet(crops, OUT + "/car/takes_in_place.jpg", labels=names)
```

- Each placed take is one History state. Visibility changes are not History states by default.
- The user picks; the other takes stay hidden inside a group named "Takes", where
  `A.deliverable("psd-handoff")` accepts them; it flags hidden layers anywhere else. The grouping
  job below is not tested:

```python
GROUP = r"""
var d = app.activeDocument, a = %ARGS%, g = d.layerSets.add();
g.name = "Takes";
for (var i = 0; i < a.names.length; i++)
  if (a.names[i] !== a.keep) d.artLayers.getByName(a.names[i]).move(g, ElementPlacement.INSIDE);
return g.name;
"""
ps_run.run(GROUP.replace("%ARGS%", json.dumps({"names": names, "keep": names[0]})),
           undo="Scenario: Group takes")
```

- To swap a take's pixels and keep its box, `IO.replace(name, path)`. Otherwise place each new take
  as its own layer.
