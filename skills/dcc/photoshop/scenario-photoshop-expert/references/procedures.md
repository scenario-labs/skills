# Procedures (toolkit calls, in order)

Each procedure names the calls it runs and its status. "Verified live" means a live suite on
Photoshop 27.11 (macOS) runs those calls; "not tested" means the block was written from the
toolkit's code and Adobe's documentation but never run as shown. Every call below is one `ps_run`
job, so each is its own unit of failure. A toolkit call raises `RuntimeError` with the error, and
the line where the toolkit adds one (`ValueError` for a bad argument, before any job); a raw
`ps_run.run` returns `ok`, `error`, `exit` and `body_line` instead. After either, recover as the
SKILL.md's Quality gates say: `A.history_gate(h0, undo)` decides. `[]`: the call left its state, so
`A.step_back(h0, undo)`; "no new History state": nothing changed, so fix the cause and run it again;
anything else: stop. A name check alone can undo the previous call's finished edit when both share
one `undo`.

Setup for every block:

```python
import json, sys
sys.path.insert(0, "<this skill>/scripts")
import ps_run, ps_io as IO, ps_gates as G, ps_review as R, ps_audit as A
OUT = "/path/to/a/work/folder"   # never the folder of the user's PSD
```

## P1. Session start

Status: verified live (every suite starts this way).

```python
ps = ps_run.find_photoshop()            # {"path", "name", "version"}, or None (exit 5 on the shell)
r = ps_run.run("return {version: app.version, active: app.documents.length ? app.activeDocument.name : null};")
# r["exit"]: 3 not running (ps_run.py --launch starts it without stealing focus), 6 automation refused
s = A.doc_state()                       # name, path, saved, width, height, ppi, mode, bits, profile,
                                        # layers (tree with kind), selection, active_layer, history
```

- Check `s["name"]` against the brief before any edit. If the user names another document, ask them
  to bring it to the front; never switch documents under them.
- Record `s["saved"]`, `s["bits"]` and `s["profile"]`. At the end, `saved` must be unchanged by the
  agent.
- `s["history"]`, or `A.history()` alone, is the active History state:
  `{index, name, prev, id, prev_id, count, limit, full}`. Gate an edit on it: `h0 = A.history()`
  right before the call, then `A.history_gate(h0, undo) == []` after it. The gate passes when the
  active state is named as the job's `undo` and sits directly on top of `h0`: its `prev_id` is
  `h0["id"]` when Photoshop reports state ids, else its `prev` is `h0["name"]` and, below the limit,
  its index is one higher. Never gate on `count`: captures, previews and exports step History back
  and leave redo states in the list, and a selection is a state of its own. At the History limit
  (`full`) the oldest state drops and the index holds still, so the gate skips the index there
  (verified live at a lowered limit with state ids, `test_history_live.py`; the id-less fallback is
  not verified at the limit).
- `A.step_back(h0, undo)` undoes one named edit and checks that `h0`'s state is active again; it
  raises if the active state has another name. It steps first and compares with `h0` after, so a
  raise on that comparison comes after History moved: read `A.history()` before anything else. Use
  it for trials, never an index or the list length.
- `A.layer_find("Sky")` returns every layer with that exact name, with its path and kind. Two hits
  mean the name is ambiguous: rename or use the id.

## P2. Writing a job of your own

Status: the protocol is verified live; the example body is not tested.

```python
body = r"""
var d = app.activeDocument;
if (d.name !== "poster.psd") throw new Error("wrong document: " + d.name);
var l = d.activeLayer.duplicate();
l.name = "Sky, grade base";
return {id: l.id, name: l.name};
"""
assert ps_run.lint(body) == []          # refuses .save( .saveAs( .close( app.quit and save/close events
r = ps_run.run(body, undo="Scenario: Duplicate sky")
if not r["ok"]:
    print(r["error"], r.get("body_line"), r.get("jsx"))   # body_line counts from the body's first line
```

- The body is a function body: `return` a JSON-able value. UnitValues come back as pixels, zero
  included (verified live).
- One `undo` name per user-visible edit, starting "Scenario: ". Read-only jobs take none.
- Try a new Action Manager descriptor on a document the job creates first:
  `var d = psr_new_doc(512, 512, "scratch", {fill: "white"}); try { ... } finally { psr_close(d); }`.
  Then measure its effect with a gate or a preview (P7, P8): a silent success proves nothing.
- Find a descriptor by recording an Action and using Actions panel flyout > Copy As JavaScript
  (Developer Mode on). Translate `batchPlay` JSON to `ActionDescriptor` calls, or keep
  `executeAction` with the same string IDs.
- Traps that break remembered code: [photoshop-2026-traps.md](photoshop-2026-traps.md).

## P3. The local edit round trip

Status: verified live. `test_io_live.py` runs this block on a fixture photo, from `export_region` on
(the test makes the selection; `export_mask` runs in the generative-edit suite): a brightened result
placed with `mask_selection=True`, `xmp=` and `undo=`, then `masked` and `selection_kept` true, the
capture's bounds, `A.history_gate` passing for that name, the outside unchanged (`G.diff` max 2 or
less), the inside changed, and `layer_xmp` reading the provenance back. For a selection-scoped edit
with seam and outside checks, the generative-edit specialist's `capture`, `check`, `place_edit` and
`verify` wrap these calls.

```python
sel = IO.selection()["bounds"]          # None: no selection; ask, or use a layer or the canvas
cap = IO.export_region(OUT + "/input.png", pad=32)        # merged pixels, selection + 32 px, sRGB 8-bit
msk = IO.export_mask(OUT + "/mask.png", bounds=cap["bounds"])   # same box: the files line up
# Scenario MCP (the scenario skill): recommend for the capability, upload input.png and mask.png,
# price the exact payload, get the user's yes, run, wait, download OUT + "/result.png".
h0 = A.history()                        # right before the call
L = IO.place(OUT + "/result.png", "Window, tiki hut, take 1", bounds=cap["bounds"],
             mask_selection=True, undo="Scenario: Edit window",
             xmp={"assetId": "...", "jobId": "...", "prompt": "...", "createdAt": "2026-10-19"})
assert L["bounds"] == cap["bounds"] and L["masked"] and L["selection_kept"]
assert A.history_gate(h0, "Scenario: Edit window") == []   # one new state, with that name
print(IO.layer_xmp(L["name"]))          # the provenance, read back from the layer
```

- `pad`: context for the model. The selection stays tight to what should change, because the model
  fills the mask.
- `mask_selection=True` needs the selection still active, and leaves it active for P4's outside gate
  (`selection_kept`). If the user may have changed it, place without the mask and use the
  generative-edit `place_edit`, which rebuilds the mask from the file.
- `export_region(layer="Hero")` captures one layer instead of the composite; `max_px=` caps the long
  side for a model's input limit; `punch_selection=True` makes the selected area transparent for
  models that edit where the input is transparent.
- `fit`: `"exact"` stretches into the box (same aspect as the capture), `"contain"` fits inside,
  `"cover"` fills and overflows.
- Whole-image edits (restyle, relight, colorize): `IO.export_region(OUT + "/input.png")` with no
  selection captures the canvas; place with `bounds=[0, 0, w, h]` and no mask.

## P4. Gates after landing

Status: verified live (`test_gates_live.py`, `test_restore_live.py`; the outside gate right after
P3's placement in `test_io_live.py`).

```python
out = G.diff(None, "Background", region="outside")       # composite vs the base, outside the selection
assert out["worst"]["max"] <= 2
skin_before = G.texture("Background", region="selection")["energy"]
skin_after = G.texture(L["name"], region="selection")["energy"]
texture_ok = skin_after / skin_before >= 0.6
h = G.halo(L["name"])                    # light_rim and dark_rim must stay at or under 8
s = G.stats(L["name"], region={"alpha": L["name"], "contract": 4})   # skin_line_delta within +-10
st = G.structure(L["name"], "Background")["score"]   # tone-blind; compare candidates, never a fixed value
```

- Regions: `None` (whole image), `[l, t, r, b]`, `"selection"`, `"outside"`, `{"alpha": layer}`,
  `{"alpha": layer, "contract": px}` (its core), `{"alpha": layer, "ring": px, "gap": px}` (its
  surroundings).
- `diff(None, base, region="outside")` holds only when nothing above the base changes the composite.
  On a stack with adjustment layers on top, compare captured files instead (the generative-edit
  `verify` does).
- `diff(a, b, size=[256, 256])` compares at a small size: identity and shifts survive, fine texture
  does not. Use it after an upscale or a whole-frame edit.
- After a colorize, relight or restore, a plain difference flags everything. Use `structure` and the
  overlay (P7).
- Gates leave pixels, layers and the active History state as they were: they measure on duplicates
  the job closes, and a stored selection steps back out of History (verified live). The temporary
  states still count: at the History limit each one drops one of the user's oldest undo steps
  ([traps](photoshop-2026-traps.md), section 5).

## P5. A new take on the same layer

Status: verified live (`test_io_live.py`): a file of the same pixel size keeps the box; a file of
another size changes it.

```python
IO.replace("Window, tiki hut, take 1", OUT + "/result_2.png")   # same pixel size: same box; name restored
```

- The new contents inherit the layer's transform, not its box: a 50% scaled layer shows a 300x200
  file at 150x100, same center. A take of another pixel size lands at another size: place it as a
  new layer (P6) or fit it again.
- Replace only when the user wants the old take gone. To compare takes, place each as its own layer
  (P6): generating again on a generated layer replaces the earlier take.

## P6. Candidates as layers, then a sheet

Status: verified live (`test_io_live.py` runs `preview`, `sheet` and `before_after`: tile sizes,
labels band, and the edited area differing between the two tiles; Pillow is required).

```python
paths, labels = [], []
for i, res in enumerate(results, 1):
    name = "Sky, take %d" % i
    IO.place(res, name, bounds=cap["bounds"], mask_selection=True, undo="Scenario: Place " + name)
    p = R.preview("%s/take_%d.png" % (OUT, i), crop=cap["bounds"], max_px=0,
                  layers_only=["Background", name])
    paths.append(p["path"]); labels.append(name)
R.sheet(paths, OUT + "/takes.jpg", labels=labels)
R.before_after(paths[0], paths[1], OUT + "/a_b.jpg")
```

- `layers_only` hides every other layer in the preview copy only; the document is untouched.
- Open the sheet, then each finalist at 100%. Keep the losing takes hidden, named, in a group named
  "Takes" until the user decides (`psd-handoff` accepts hidden layers there); deleting them is the
  user's call.

## P7. Alignment after a tone change

Status: verified live (`test_restore_live.py`).

```python
scores = {n: G.structure(n, "Background")["score"] for n in ("Restored", "Restored, take 2")}
R.overlay(OUT + "/overlay.png", "Background", "Restored", crop=[90, 120, 430, 300])
```

- The overlay shows the first layer's luminance in red, the second's in cyan: gray where they line
  up, red and cyan fringes where they do not, whatever the colors.
- Auto-Align misreads a damaged base. The upscale-restore specialist's `align` keeps it only when
  the structure score drops 10% or more, and steps History back otherwise.

## P8. Look

Status: verified live (`preview` in the key-art suite, crops and `overlay` in the restore suite).

```python
R.preview(OUT + "/stage.png")                              # whole canvas, long edge 1600 px, sRGB 8-bit
R.preview(OUT + "/seam_1.png", crop=[300, 220, 560, 400], max_px=0)   # 100%: seams, halos, grain
```

- Open every image with the image reader and judge it with [critique.md](critique.md). A gate that
  passes on a result that looks wrong is a failed stage.
- Crop at 100% around every seam, edge, face, hand and line of text. Downscaled previews hide halos,
  soft generated texture and grain mismatch.

## P9. Deliver

Status: `deliverable` profiles web, game-texture, print and psd-handoff verified live
(`test_audit_live.py`); social not run; the PSD copy job not tested.

```python
probs = A.deliverable("psd-handoff")    # [] = pass
clip = A.histogram_clip()               # % of pixels at 0 and 255 per channel, on a merged copy
R.preview(OUT + "/final.png", max_px=0) # full-size sRGB 8-bit copy of the whole canvas (.jpg: quality 10 of 12)
ps_run.run('return psr_export(app.activeDocument, %s, "psd");' % json.dumps(OUT + "/poster_v2.psd"))
```

- The document itself is the deliverable (a PSD handoff, a print master): `deliverable(profile)`
  must return `[]`.
- An exported copy is the deliverable (web, social): the export converts to sRGB 8-bit, so mode,
  depth and profile findings on a 16-bit or wide-gamut master are expected. Size findings are not.
- `psr_export(doc, path, fmt, opts)` writes a copy as png, jpg, tif, psd or tga and refuses the
  document's own file. The user saves their own PSD.
- An alpha channel survives only in TGA: `{alpha: true}` writes 32-bit, otherwise 24-bit (verified
  live in the game-art packing test). PNG keeps layer transparency, not alpha channels.
- Profiles: `web` RGB 8-bit sRGB, long edge 600 to 4096 px; `social` the same, from 1080; `print`
  300 ppi or more, long edge 2400 or more; `game-texture` RGB 8-bit, power-of-two sides, 256 to 8192
  px; `psd-handoff` no default layer names, no hidden layers outside a group named "Takes", no empty
  layers, no layers past the canvas.

## P10. The same edit over many files

Status: not tested as a loop. The open-and-own pattern (`__psr_created.push`) is the one the mockups
and generative-edit toolkits use.

1. Prove the recipe on one file through P1 to P9. Keep the job bodies as files: they are the recipe,
   replayable and reviewable.
2. Quote the whole batch once through the Scenario MCP (every paid run, same payload shape), and get
   the user's yes for the total.
3. Run one job per file, and stop at the first failure:

```python
RECIPE = open("recipe.jsx").read()      # a body proven on one file; it edits the document `d`
for src, dst in pairs:
    body = r"""
var f = new File(%s), name = f.name;
for (var i = 0; i < app.documents.length; i++) {
  var p = null; try { p = app.documents[i].fullName.fsName; } catch (e) {}
  if (p === f.fsName) throw new Error("open in Photoshop, skipped: " + p);
}
var d = app.open(f);
__psr_created.push(d.id);
try {
%s
  psr_export(d, %s, "png");
} finally { psr_close(d); }
return name;
""" % (json.dumps(src), RECIPE, json.dumps(dst))
    r = ps_run.run(body, timeout=300)
    if not r["ok"]:
        break                            # report the file and the error; never skip silently
```

- A file the user has open is refused, so the job never closes their unsaved work.
- Registering the opened file makes `psr_close` close it without saving; the source on disk is never
  written.
- Scenario generations in a batch: capture every file first, run the jobs, then land and gate each
  one. A saved Scenario workflow as the recipe goes through `scenario-workflows`.
- Template variants from one PSD (Variables and Data Sets) belong to the key-art specialist.

## P11. Play one of the user's Actions

Status: not tested.

Skip an Action that holds one of Photoshop's generative steps (Generative Fill, Expand, Prompt to
edit): Adobe's generative AI guidelines may cover automated use, so the user plays it by hand.

```python
ps_run.run('app.doAction("Sharpen for web", "Studio"); return true;', undo="Scenario: Action Sharpen for web")
```

- The lint cannot see inside an Action: a recorded Save As or Close runs anyway. Read the steps in
  the Actions panel first, or play it on a duplicate the job owns.
- Actions that need pixels fail or merge layers on a smart object. Play them on a duplicate or a
  stamped copy.

## P12. Image to video

Status: not tested inside Photoshop.

```python
R.preview(OUT + "/first_frame.png", max_px=0)   # or IO.export_region(..., layer="Hero")
```

- The clip is generated through `scenario-video` (first frame, optional last frame) and stays
  outside Photoshop. Placing it back as a video layer is not tested.
- For a loop, export the same frame as first and last.
