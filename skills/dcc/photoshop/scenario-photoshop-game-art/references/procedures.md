# Procedures (toolkit calls, in order)

Each procedure names the calls it runs and its status. "Verified live" means a suite in the build
project runs those calls on Photoshop 27.11 (macOS): `test_gameart_live.py` for `ps_gameart`,
`test_generative_live.py` for `ps_generative`, the lead's suites for `ps_io`, `ps_gates`,
`ps_review` and `ps_audit`. "Not tested" means the block was written from the toolkit's code and
Adobe's or the engine's documentation but never run as shown. Every call is one `ps_run` job: read
the error after each one.

Scenario steps appear as comments. They go through the Scenario MCP with the `scenario` skill
(connection, `recommend`, the price quote and the user's yes before every paid run, job waiting),
`scenario-textures` (tiling textures, maps, tiling-safe upscale), `scenario-image` (inpaint and
edits with references, style passes) and `scenario-game-assets` (sprites, icons, UI parts).

Setup for every block:

```python
import json, os, sys
sys.path.insert(0, "<skills>/scenario-photoshop-game-art/scripts")
sys.path.insert(0, "<skills>/scenario-photoshop-generative-edit/scripts")
import ps_gameart as GA            # also puts scenario-photoshop-expert/scripts on the path
import ps_generative as GE
import ps_run, ps_io as IO, ps_gates as G, ps_review as R, ps_audit as A
OUT = "/path/to/a/work/folder"     # never the folder of the user's PSD
```

## P0. Session and route

Status: `doc_state` verified live (`test_audit_live.py`).

```python
s = A.doc_state()
assert s["name"] == "cobblestone.psd", s["name"]   # the document the brief names
W, H = s["width"], s["height"]
```

| Brief                                          | Route                                   | Procedure |
| ---------------------------------------------- | --------------------------------------- | --------- |
| A photo or texture that must tile              | read, then band repair                  | P1, P3    |
| A new tiling texture                           | generate with a tiling material model   | P2        |
| A tile whose look may change                   | re-render through a tiling model        | P4        |
| Blotches that repeat                           | locate, then paint by hand              | P5        |
| Maps from an approved albedo                   | extract, land, check                    | P6        |
| Engine-ready files, packed masks               | export and pack                         | P7        |
| A style or color pass on a render              | variant layers over the render          | P8, P10   |
| One object of a render                         | ID pass selection, then generative-edit | P9        |
| Sprites, icons, buttons with transparent edges | edge check and unflattened export       | P11       |
| A button or panel that stretches               | 9-slice guides and check                | P12       |

## P1. Read a tile

Status: verified live (`tile_check` and `tile_preview` on real Scenario textures; the tiling model's
output passes, the plain texture fails, a light falloff is flagged, a mirrored copy passes). `blur=`
and `layer=` are not run by the suite; `layer=` isolates the layer with the helper that
`export_texture(layer=...)` and `pack_channels` run there.

```python
t = GA.tile_check()                       # read only; layer=None reads the visible image
print(t["size"], t["pow2"], t["ratio_x"], t["ratio_y"], t["patch_range"], t["seam_ok"], t["patch_ok"])
GA.tile_preview(OUT + "/tile_3x3.png", n=3)   # open it with the image reader, every time
```

- `ratio_x` and `ratio_y`: the step across the seam over the mean step between other neighbors,
  after a half offset. About 1 is invisible; the limit is 1.5. Readings: a tiling model's output
  1.07 and 0.89, a plain texture 2.03 and 3.09, its repair 0.99 and 0.83.
- `patch_range`: the spread of 16 cell means on a wrap-blurred copy (blur a 16th of the long side).
  The limit is 12. A tiling model's output read 9.75; the same texture under a 40-level light
  falloff read 26.78 while its seams still passed.
- A grainy photo can read a high ratio from grain alone: `GA.tile_check(blur=1)` quiets it (not
  tested).

## P2. A new tiling texture

Status: the Scenario step is not run by any suite as written; `IO.place` is verified live (mockup
suite) and `tile_check` as in P1.

```python
# Scenario MCP (scenario-textures): recommend for a seamless texture in the user's words; a square
# power-of-two size (1024 unless the brief says otherwise); 2 to 4 outputs; references for a
# project style. Quote, yes, run, wait, download OUT + "/gen/take_1.png" and on.
L = IO.place(OUT + "/gen/take_1.png", "Albedo", bounds=[0, 0, W, H], undo="Scenario: Place texture")
t = GA.tile_check(layer=L["name"])
GA.tile_preview(OUT + "/gen/take_1_3x3.png", n=3, layer=L["name"])
```

GATE: `seam_ok`, `patch_ok`, and the preview read at fit-to-screen. A model's "tiling" claim is
checked like any other tile.

## P3. Seam repair in a narrow band

Status: `offset` and `seam_band` verified live; `capture`, `check`, `place_edit` and `verify`
verified live in generative-edit's suite. This chain ran once on a real plain texture (1024 px, 48
px band): take 1 passed every gate and is the suite's repaired fixture; take 2 failed `check`
(residual 17.2, stones re-laid). Not re-run as written.

```python
t = GA.tile_check()
W, H = t["size"]
o = GA.offset()                              # a stamped copy, shifted by half with wrap-around
band = max(16, max(W, H) * 48 // 1024)       # about 5% of the side: 48 px on 1024
GA.seam_band(band)                           # the cross where the edges now meet, selected
cap = GE.capture(OUT + "/seam", polarity="alpha")
# polarity from the member's mask field (scenario-image): "alpha" was the measured RGBA mask.
# The cross spans the canvas, so the capture box is the whole tile.
```

GATE: open `cap["context"]` and `cap["mask_edit"]`: the white is the cross and nothing else.

```python
# Scenario MCP (scenario-image): recommend an image edit with a reference image and a mask.
#   Upload cap["input"] and cap["mask_model"]; the offset tile is also the reference image.
#   Prompt, texture only, never an object: "Continue the cobblestones across the masked band:
#   same stone size, color and light as the rest. No new objects." [added wording]
#   Quote, yes, run 2 outputs, wait, download OUT + "/seam/take_1.png", take_2.png.
passed = []
for i in (1, 2):
    p = OUT + "/seam/take_%d.png" % i
    r = GE.check(cap, p)
    ok = (r["aspect_ok"] and r["edited"] and not r["polarity_suspect"] and r["seam_ok"]
          and r["b_size"][0] >= W)
    print(i, ok, r["seam"])
    if ok:
        passed.append(p)
```

- `edited` false: the member returned its input. Measured once with a mask-edit model, both outputs,
  still billed. Follow the lead's rule for a take equal to its input (scenario-photoshop-expert,
  Quality gates).
- A residual of 6 or more: the stones moved. Re-run; never nudge a take into place.
- `b_size` smaller than the tile: the band comes back soft, the resolution step Dinda shows
  [9_36YihB8I4 03:17].

```python
best = passed[0]                             # the take chosen by eye at 100% on the cross
L = GE.place_edit(cap, best, "Seam repair, take 1", feather=2,
                  xmp={"modelId": "<member id>", "assetId": "<asset id>", "prompt": "<prompt>"})
v = GE.verify(cap)
assert v["untouched"], v["outside"]          # past the band and its feather, the source is exact
t2 = GA.tile_check()
assert t2["seam_ok"] and t2["patch_ok"], t2
GA.tile_preview(OUT + "/seam/repaired_3x3.png", n=3)
c = [W // 2 - 128, H // 2 - 128, W // 2 + 128, H // 2 + 128]
R.preview(OUT + "/seam/cross_100.png", crop=c, max_px=0)
```

GATE: the cross at 100% shows whole stones, no half objects, no soft band; the 3x3 preview at fit
shows no grid. The seam numbers passed a take the eye rejected for style drift, so the look is the
last word.

- The repaired tile stays offset by half. A wrapped tile repeats the same either way; run
  `GA.offset()` again only when a UV layout or decal expects the original placement.
- A wider band gives the member more to invent. On the same texture a 96 px band through a tiling
  material model's inpaint drifted in style; the model also changed, so the width alone is not
  proven.

## P4. Re-render through a tiling material model

Status: measured once (strength 0.35: ratios 0.97 and 0.93, mean change 16, stones softened); not
run as written.

```python
# Scenario MCP (scenario-textures): a tiling material model in img2img with the tile as the image,
# strength low (0.35 measured), 1 or 2 outputs. Quote, yes, run, wait, download.
L = IO.place(OUT + "/rerender/take_1.png", "Re-render, take 1", bounds=[0, 0, W, H],
             undo="Scenario: Place re-render")
t = GA.tile_check(layer=L["name"])
d = G.diff(L["name"], "Albedo")              # how far the look moved
print(t["seam_ok"], t["patch_ok"], d["worst"]["mean"])
GA.tile_preview(OUT + "/rerender/take_1_3x3.png", n=3, layer=L["name"])
```

GATE: P2's gate, plus the user sees the old and new tile side by side
(`R.before_after(old, new, out)`, not tested) and accepts the change.

## P5. Blotches that repeat

Status: locating is arithmetic on `tile_check`'s verified output; the painting is a GUI step
([gui-paths.md](gui-paths.md)), not tested.

```python
t = GA.tile_check()
n, cells = 4, t["cells"]                     # row-major cell means of the wrap-blurred tile
mean = sum(cells) / len(cells)
worst = max(range(len(cells)), key=lambda i: abs(cells[i] - mean))
row, col = divmod(worst, n)
W, H = t["size"]
box = [col * W // n, row * H // n, (col + 1) * W // n, (row + 1) * H // n]
print("darker" if cells[worst] < mean else "brighter", box)
```

Tell the user which cell is off and by how much. Dinda's fix: Pattern Preview on, zoomed out, a Soft
Light layer painted white or black at 1 to 2% flow, then a Color layer at 5 to 10% flow over one
off-color stone [9_36YihB8I4 06:34, 07:41]. A light falloff baked into the source shows as a ramp of
cells from one side to the other; a re-render (P4) or a flatter source fixes it faster. GATE:
`patch_range` under 12, preview read again.

## P6. Maps from the approved albedo

Status: `IO.place` and `tile_check(layer=...)` paths verified live; map extraction and the invert
job are not tested.

```python
# Scenario MCP (scenario-textures): extract maps from the exported albedo (P7 first export).
# Ask for normal, roughness or smoothness, metallic, height. Confirm which one the extractor
# returned: a roughness request can come back labeled smoothness.
maps = {"Normal": OUT + "/maps/normal.png", "Roughness": OUT + "/maps/roughness.png",
        "Metallic": OUT + "/maps/metallic.png", "Height": OUT + "/maps/height.png"}
for name, path in maps.items():
    IO.place(path, name, bounds=[0, 0, W, H], undo="Scenario: Place " + name)
    r = GA.tile_check(layer=name)
    print(name, r["ratio_x"], r["ratio_y"], r["seam_ok"])
```

Invert a copy when the shader wants the other convention (Unity's HDRP mask map stores smoothness):

```python
INV = r"""
var d = app.activeDocument, a = %ARGS%, src = null;
for (var i = 0; i < d.layers.length; i++) if (d.layers[i].name === a.src) src = d.layers[i];
if (!src) throw new Error("layer not found at the top level: " + a.src);
var L = src.duplicate(src, ElementPlacement.PLACEBEFORE);
d.activeLayer = L;
L.rasterize(RasterizeType.ENTIRELAYER);
L.invert();
L.name = a.name;
return {name: L.name, id: L.id};
"""
args = json.dumps({"src": "Roughness", "name": "Smoothness"})
res = ps_run.run(INV.replace("%ARGS%", args), undo="Scenario: Invert map")
assert res["ok"], res
```

GATE: every map has the albedo's size and passes the seam ratio; a map that fails was not extracted
from the tile as it wraps, so re-extract rather than repair it.

## P7. Export and pack

Status: verified live: a gray data export keeps 10, 64, 128, 200, 250 exactly; a 100x60 image
resized to 128x64 with `nearest`; a pack with alpha to TGA reads back (40, 128, 77) and 220 within
1; PNG with an alpha source is refused; `export_texture` and `pack_channels` create a missing output
folder. Color export runs in the offset test. Not tested: `tif`, `bits=16`, normal maps.

```python
print(A.deliverable("game-texture"))         # [] on the master: RGB 8-bit, 256-8192, power of two
d = GA.export_texture(OUT + "/out/cobble_albedo_1024.png", size=1024, layer="Albedo")
n = GA.export_texture(OUT + "/out/cobble_normal_1024.png", size=1024, data=True, layer="Normal")
r = GA.export_texture(OUT + "/out/cobble_rough_1024.png", size=1024, data=True, gray=True,
                      layer="Roughness")
# Unity HDRP mask map: R metallic, G ambient occlusion, B detail mask, A smoothness (HDRP manual).
# No AO bake here: 255 is no occlusion. No detail map: 0.
m = GA.pack_channels(OUT + "/out/cobble_mask_1024.tga", "Metallic", 255, 0, a="Smoothness",
                     size=1024)
assert all(x["pow2"] for x in (d, n, r, m)), (d, n, r, m)
```

- Sources for `pack_channels` are layer names (their luminance), numbers 0-255, or None (black). The
  pack flattens the visible document first, then fills it black: what is visible does not leak in.
- Color maps convert to sRGB; `data=True` writes values with no profile; `gray=True` writes one
  channel through Split Channels, which copies values as they are.
- `resample="nearest"` for pixel art and PSX textures, as NoPoly finishes at 128 or 256 [QYUh8RuNZgw
  11:34] and sets Closest sampling in the 3D app [QYUh8RuNZgw 12:06].
- `deliverable` reads the open master; an export smaller than 256 (PSX) fails its minimum on
  purpose, so audit the master and read each export's `pow2`.

Read back, as the suite does (Pillow):

```python
from PIL import Image
with Image.open(m["path"]) as im:
    print(im.mode, im.size, im.getpixel((W // 4, H // 4)))   # "RGBA" for a pack with alpha
s = GA.export_texture(OUT + "/check/smooth.png", size=1024, data=True, gray=True, layer="Smoothness")
with Image.open(s["path"]) as g, Image.open(m["path"]) as im:
    xy = (W // 4, H // 4)
    assert abs(g.getpixel(xy) - im.getpixel(xy)[3]) <= 1     # alpha equals the source map
```

Engine side (documentation, not tested here): Unity keeps sRGB on for color textures and off for
data, and its HDRP mask map needs sRGB off; Unreal mipmaps and streams power-of-two sizes only.
Write the layout, the sRGB flag per file and the normal map's green-channel convention in the
handoff.

## P8. Style pass on a render

Status: not tested. `IO.place`, `IO.export_region`, `G.structure` and `R.overlay` are verified live
in other suites; `R.sheet` is verified live in `test_io_live.py`.

```python
s = A.doc_state()                            # the render open as the document, layer "Render"
W, H = s["width"], s["height"]
for name, path in (("ID", OUT + "/passes/id.png"), ("Clay", OUT + "/passes/clay.png")):
    IO.place(path, name, bounds=[0, 0, W, H], undo="Scenario: Place " + name)

HIDE = r"""
var d = app.activeDocument, a = %ARGS%;
function has(list, x) { for (var k = 0; k < list.length; k++) if (list[k] === x) return true; return false; }
for (var i = 0; i < d.layers.length; i++) if (has(a.hide, d.layers[i].name)) d.layers[i].visible = false;
return true;
"""
ps_run.run(HIDE.replace("%ARGS%", json.dumps({"hide": ["ID", "Clay"]})))
cap = IO.export_region(OUT + "/style/render.png", layer="Render", bounds=[0, 0, W, H])
```

ExtendScript is ES3: arrays have no `indexOf`, hence `has`. Visibility changes are left out of
History by Photoshop's default preference.

```python
# Scenario MCP (scenario-image): recommend an image edit or the project's trained style model.
#   The render as the input or reference image; a style reference from approved art.
#   Prompt: the look, then the keep: "Repaint as hand-painted stylized concept art. Keep the camera,
#   the layout, every silhouette and the light direction."
#   3 or 4 takes made deliberately different (palette, time of day), as Manners shows four
#   approaches to one problem [eJN6aLNSnyc 19:16]. Quote, yes, run, wait, download.
from PIL import Image
takes = []
for i in (1, 2, 3, 4):
    p = OUT + "/style/take_%d.png" % i
    with Image.open(p) as im:
        assert abs(im.size[0] / im.size[1] - W / H) <= 0.01 * W / H, p   # same aspect
    L = IO.place(p, "Style pass, take %d" % i, bounds=cap["bounds"], undo="Scenario: Style pass")
    sc = G.structure("Render", L["name"])
    R.overlay(OUT + "/style/overlay_%d.png" % i, L["name"], "Render")
    takes.append((L["name"], sc))
print(takes)
R.sheet([cap["path"]] + [OUT + "/style/take_%d.png" % i for i in (1, 2, 3, 4)],
        OUT + "/style/takes.jpg", labels=["render", "1", "2", "3", "4"])
```

GATE: compare structure scores between takes only (the lowest moved the least), never against a
fixed value. The overlay is gray where a take lines up with the render, red or cyan where a
silhouette moved. A style pass changes tone everywhere, so a plain difference reads high on a good
take (a colorized restore read a mean of 29 while aligned). Then the critique's style-pass section.

## P9. One object through the ID pass

Status: `id_select` verified live (a 256 px anti-aliased ID image at fuzz 40: bounds exact, share
within 0.6 points; no match returns None); the chain to generative-edit is not tested.

```python
sel = GA.id_select("ID", [0, 255, 0], fuzz=40)     # the object's flat ID color
assert sel["bounds"] is not None, "no pixel of that color: read the ID pass colors again"
print(sel["share"], sel["partial"])                 # % of the canvas; % only partly selected (edge)
cap = GE.capture(OUT + "/barrel", polarity="white")
# Scenario MCP (scenario-image): inpaint or instruction edit of that object, the style reference,
# a keep-clause for everything else. Then GE.check, GE.place_edit, GE.verify as in P3.
```

- Fuzziness 40 kept the anti-aliased edge in the suite (the default is 20). Lower it when two ID
  colors are close and the selection spills into the neighbor.
- `partial` large compared with `share`: the ID pass is blurred or JPEG-compressed. Ask for a
  lossless pass.
- The same call selects one flat color of a UI layout or a color-coded mockup.

## P10. Value check in grayscale

Status: not tested.

```python
GRAY = r"""
var src = app.activeDocument;
var d = psr_dup(src, "value_check", true);
app.activeDocument = d;
if (d.bitsPerChannel !== BitsPerChannelType.EIGHT) d.bitsPerChannel = BitsPerChannelType.EIGHT;
d.changeMode(ChangeMode.GRAYSCALE);
var w = d.width.as("px"), h = d.height.as("px"), s = Math.min(1, 1600 / Math.max(w, h));
if (s < 1) d.resizeImage(UnitValue(Math.round(w * s), "px"), UnitValue(Math.round(h * s), "px"),
                         null, ResampleMethod.BICUBIC);
var p = psr_export(d, %OUT%, "png");
psr_close(d);
return p;
"""
res = ps_run.run(GRAY.replace("%OUT%", json.dumps(OUT + "/style/values.png")))
```

Run it with one take visible at a time. Octopunish found a storage area "blending in too much" this
way and added light [gjkaYE8_MoE 13:09]; the beetle merged with the slope [h1i3X0gqrQs 21:20].

## P11. Sprites, icons and UI parts

Status: `G.halo` verified live (gates suite). The export job is not tested.

```python
h = G.halo("Icon Scarab")                    # rims over black and over white
print(h)                                     # light_rim > 8: bright fringe; dark_rim > 8: dark fringe
```

A fringe gets Defringe 1 px or Remove White or Black Matte by hand ([gui-paths.md](gui-paths.md)),
then `G.halo` again. Then export one top-level layer or group as a padded PNG with transparency:

```python
SPRITE = r"""
var src = app.activeDocument, a = %ARGS%;
var d = psr_dup(src, "sprite_export", false);
app.activeDocument = d;
var keep = null;
for (var i = d.layers.length - 1; i >= 0; i--) {
  var l = d.layers[i];
  if (l.name === a.layer) keep = l; else l.remove();
}
if (!keep) throw new Error("layer not found at the top level: " + a.layer);
keep.visible = true;
d.trim(TrimType.TRANSPARENT, true, true, true, true);
var w = d.width.as("px") + 2 * a.pad, h = d.height.as("px") + 2 * a.pad;
d.resizeCanvas(UnitValue(w, "px"), UnitValue(h, "px"), AnchorPosition.MIDDLECENTER);
var p = psr_export(d, a.out, "png");
psr_close(d);
return {path: p, size: [w, h]};
"""
args = {"layer": "Icon Scarab", "out": OUT + "/ui/icon_scarab.png", "pad": 8}
res = ps_run.run(SPRITE.replace("%ARGS%", json.dumps(args)))
assert res["ok"], res
```

- `pad` covers the drop shadow's reach plus a few pixels, so the engine's filtering never samples
  the edge of the canvas [added].
- PNG stores straight alpha, never premultiplied (PNG specification). Unity's Alpha Is Transparency
  dilates color under transparent pixels to avoid edge artifacts (Unity import settings).
- Name files category first, as pixaroma exports icons with Layers to Files [vU-_9R-Tq18 13:23].
  AI2Play keeps one PSD per screen, tile layers named per asset [AEXy7F5sJ7M frame 40:05].
- Atlases are packed in the engine (Unity Sprite Atlas padding defaults to 4 px), not in Photoshop.

## P12. 9-slice buttons and panels

Status: verified live (guides on a flat frame; check passes a flat and a gradient frame, flags
rivets in the top edge and stone texture in the center, leaves the plain left edge alone).

```python
g = GA.nine_slice(28, 28, 28, 28)            # guides at the insets, one History state
r = GA.nine_slice_check(28, 28, 28, 28)      # read only; layer= for one layer
print(r["ok"], r["over"], {k: r[k] for k in ("top", "bottom", "left", "right", "center_x",
                                             "center_y")})
json.dump({"left": 28, "top": 28, "right": 28, "bottom": 28},
          open(OUT + "/ui/button_9slice.json", "w"))
```

- A part in `over` holds detail that smears when stretched (rivets read 4.9, stone 13.2 and 34.7
  against a limit of 1.0; a smooth gradient 0.97). Move that inset past the detail, or make the part
  flat.
- The insets need a straight run on every edge: Raskin backs the corner radius off until "a straight
  line appears" [vo7vwzzgDPk 00:31].
- A Tiled draw mode repeats the edge and center instead of stretching them (Unity 9-slicing manual):
  crop a copy to the part and read it with `tile_check` (not tested).
- The engine reads the insets as its border fields (Unity: L, R, T, B in the Sprite Editor).
