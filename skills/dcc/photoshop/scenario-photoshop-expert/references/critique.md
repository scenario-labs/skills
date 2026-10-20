# Critique rubric (every gate)

The checks every Photoshop stage passes before the next one starts. Code gates come first, because
they are cheap and exact; the look comes second, because a gate can pass on a result that looks
wrong. Thresholds are authoring-time: check them on your own images. Specialists add their own
rubric on top (seam, edge, skin, type, texture); this one applies to every stage.

## How to look

1. Whole canvas first: `R.preview(OUT + "/stage.png")` (long edge 1600 px). Read composition,
   balance, and anything that jumps out at viewing size.
2. Then 100% crops: `R.preview(path, crop=[l, t, r, b], max_px=0)` around every seam, mask edge,
   face, hand, line of text and logo. Any other zoom level misleads on detail and sharpness.
3. Candidates side by side: one preview per take with `layers_only`, then `R.sheet` for the lineup
   and `R.before_after` for the finalist against the original.
4. Alignment after a tone change: `R.overlay` of the result over the base. Gray means aligned; red
   and cyan fringes mean a shift or a scale change.
5. Open every image with the image reader. A file that was written but not opened was not checked.

Write the verdict as pass, fix (what and where) or reject (why), with the crops it rests on. "Looks
good" with no crop listed is not a verdict.

## Code gates (pass/fail)

| Check                     | Call                                                      | Pass                               | Fail means                                             |
| ------------------------- | --------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------ |
| Right document            | `A.doc_state()["name"]`                                   | equals the brief                   | the user switched documents: stop and ask              |
| Capture and mask line up  | `export_region` and `export_mask` bounds                  | identical                          | the mask was cut from another box                      |
| Result fits the capture   | result size against the capture                           | same aspect (scale may differ)     | the model reframed: re-run or pad to its ratio         |
| Landing box               | `IO.place(...)["bounds"]`                                 | equals the capture bounds          | the layer is offset or scaled                          |
| One state per edit        | `A.history_gate(h0, undo)`, `h0 = A.history()` before     | `[]`: one new active state, named  | a job ran without `undo=`, ran twice, or History moved |
| Outside untouched         | `G.diff(None, base, region="outside")`                    | `worst.max` <= 2                   | the mask leaks or the stack above changed              |
| Texture kept              | `G.texture` after / before, same region                   | ratio >= 0.6                       | generated or smoothed skin, plastic surfaces           |
| No halo                   | `G.halo(layer)`                                           | `light_rim` and `dark_rim` <= 8    | a fringe shows on dark or light backgrounds            |
| Skin on the skin line     | `G.stats(layer, region)["skin_line_delta"]`               | within +-10 degrees                | a color cast on skin                                   |
| Alignment, tone-blind     | `G.structure(a, b)["score"]`                              | the lower of two candidates        | shift or scale change: compare, never absolute         |
| Identity after an upscale | `G.diff(a, b, size=[256, 256])` or the specialist's match | mean under 6 at a 256 px long side | the upscaler changed content, not only detail          |
| Clipping                  | `A.histogram_clip()`                                      | no unintended 0 or 255 piles       | blown highlights or crushed shadows                    |
| Delivery                  | `A.deliverable(profile)`                                  | `[]`                               | size, mode, depth, profile or layer hygiene            |
| User's file untouched     | `doc_state()["saved"]`, the file's mtime                  | unchanged by the agent             | a save slipped through: tell the user at once          |

## Visual rubric

**Landing**

- The new layer sits exactly over what it replaces: no doubled edges, no half-pixel shift.
- The original is visible underneath and named; the result is on top and named for what it is.

**Seams and the mask edge**

- No visible line, tone step or color step where the mask meets the original. A seam shows when tone
  or alignment is off, rarely because texture differs.
- The mask is not wider than the change: the model fills the mask, so a loose selection grows the
  subject or adds objects at the edge.

**Detail and resolution**

- Generated areas hold the same sharpness, grain and noise as the surroundings at 100%. A soft,
  smeared or "pixel-y" patch next to a sharp original is the most common failure of a region
  generated at a lower resolution than the document.
- No repeated texture blocks, tiling marks or painted-over grain.

**Content**

- What the brief said must not change did not change: face, product, logo, text, pose.
- Anatomy holds: hands, fingers, teeth, eyes and catchlights, ears, hairline.
- Objects make physical sense: contact shadows, reflections, perspective and scale against
  neighbors, light direction matching the scene.
- Generated text is legible and correct, or absent; live type stays a type layer.

**Tone and color**

- Black and white points match the surroundings; the generated area does not float brighter or
  flatter than its neighbors.
- No color cast introduced across the whole frame; skin reads as skin.

**Layer hygiene (before any handoff)**

- Every layer the agent made is named; candidates that lost are hidden and named, not deleted.
- Provenance is on generated layers (`IO.layer_xmp` returns it).
- No empty layers, no layers past the canvas unless the user's design needs them.

## Severity

- **Reject:** outside pixels changed, identity or a must-keep element changed, anatomy broken, the
  user's file written. Remove nothing: hide the layer, say why, and re-run or stop.
- **Fix:** a seam, halo, soft patch, grain mismatch or tone step that a gate or a crop shows. Fix it
  on a new named layer, then re-run the same gate and crop.
- **Note:** taste calls (crop, color mood, variant choice). Present them to the user; do not decide
  them silently.
