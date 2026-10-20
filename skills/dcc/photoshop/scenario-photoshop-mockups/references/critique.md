# Critique: judging a mockup

Order of judgment:

1. The plate and the printable area, before any fit.
2. The code gates after each fit and each replace.
3. The corners at 100%.
4. The test design under light and creases.
5. Each real design, then the edges, then the whole frame at viewing size.

A stage passes only when every code gate passes and every visual item that applies has been looked
at and noted. The numbers catch a fit that missed, a warp that did nothing, a design that drifted or
came in at the wrong size, and a batch that changed the document. They never catch a design that
looks pasted on, a printable area that spills onto a lid, or a logo with a wrong letter.

## 1. Before the fit: plate and area

- The plate is sharp at 100% where the design goes. A soft plate makes a soft mockup: Anders
  upscales plates before the mockup (Anders [rrxTM5AZALU 00:34]).
- The product is clean: no old label showing through, no logo of another brand, no dust on the
  printable face. Fixes go to a plate cleanup before the mockup, never after.
- The printable area is drawn: lid, base, seams, straps, handles and hands are outside it (Quick Fix
  Up [boONV-waIUk 01:39]).
- The corners are known, from a path or from 100% crops, and the real proportions of the printed
  area are written down.
- The logo, if it came from a model, matches the original letter by letter at 100%.

## 2. Code gates

| Gate                       | Pass                                     | Fails on                                           |
| -------------------------- | ---------------------------------------- | -------------------------------------------------- |
| `corner_error`             | under 1 px                               | a warp that missed, or a quad given out of order   |
| `fit_check`                | under 0.5 px                             | a warp that did nothing or landed off its box      |
| `corners` `consistent`     | true                                     | stored corners that disagree with the box          |
| `group_mask`               | true when a selection was active         | the selection was lost before `placeholder`        |
| `drift`                    | under 0.5 px after each replace          | a replace that moved the warp                      |
| `content_size`             | unchanged across replaces                | a placeholder replaced outside the toolkit         |
| `fill`                     | 100 after a design goes in               | the fitting Fill left on a delivery                |
| `lighting` `layers`        | two, named Shading and Highlights        | a copy skipped, or the product layer wrong         |
| `displace` `map`           | the file exists                          | a map folder that cannot be written                |
| `A.history_gate(h0, undo)` | `[]` after each call                     | a stray edit on the user's document                |
| `batch` History            | `A.history_gate(h0) == []`               | a batch that left the last design in               |
| `colorways` History        | `A.history_gate(h0) == []`               | a colorway left on the document                    |
| `colorways` `check`        | `delta_e` 5 or less, `folds` 0.9 or more | Color mode alone, a wrong mask, gamut clipping     |
| `colorways` `flat`         | false                                    | a light colorway from a dark garment: folds gone   |
| `colorways` `blank`        | a 100% fold crop shown                   | white on a white blank: the blank stands as is     |
| `A.deliverable(profile)`   | returns `[]`                             | size, mode, profile, hidden layers outside "Takes" |

Thresholds are authoring-time, from striped and checkered fixtures. A fit that passes them can still
sit on the wrong corners when the quad itself is wrong: the corner crops decide.

## 3. Corners at 100%

- Each corner of the placeholder meets the face's corner: no gap of product color, no overlap past
  the rim.
- Edges run parallel to the face's edges along their whole length, not only at the corners. On a
  face that bulges, a straight edge between correct corners means the face needs `fit_cylinder` or a
  curve by hand.
- The perspective reads right: a design's grid lines converge where the product's edges converge.

## 4. The test design under light and creases

Use a ramp with a grid, or a check pattern: Dinda starts with a basic pattern "that way all of the
folds and the stretching will be more accurate" (Dinda [Z168F2BlAdA 15:36]), and a placeholder of
"both bright and dark color" (Dinda [sy1w5mTif-E 01:38]).

- **Dark end:** the highlights of the product still show on it. If they vanish, the Highlights copy
  is too weak.
- **Bright end:** the shadows and folds still show on it. If they vanish, the Shading copy is too
  weak.
- **Middle gray:** close to the design's own value where the product is evenly lit, so brand colors
  hold on flat areas.
- **Grid lines:** they bend along the folds, by about as much as the folds are deep. Straight lines
  across visible creases mean the Displace scale is too low; jagged or doubled lines mean it is too
  high or the map is too sharp.
- **No product texture printed on the design:** a map that is not blurred copies weave and noise.
  Maps "look best when they are slightly blurred" (Geller [0l2Ma_2B-A8 01:04]).

## 5. Each design

- **Light:** shading and highlights sit on the design the way they sit on the product around it. A
  design that is evenly lit on a creased product reads pasted on.
- **Color:** the design's color holds on flat, evenly lit areas. On a colored product, shadows can
  pick up the product's own color; Dinda desaturates them (Dinda [_VNqOhHJIm8 15:30]).
- **Dark garments:** the design does not sink into the shadows; Anders moves the bright side of the
  curve, not the dark side, which makes the design disappear (Anders [rrxTM5AZALU 04:58]). Fabric
  shows through a little (Anders [rrxTM5AZALU 06:38]).
- **Sharpness:** the design is no sharper than the product's surface at the same distance. "Real
  printed stuff is slightly blurred" (Dinda [sy1w5mTif-E 07:00]).
- **Letters:** every letter readable where the original is readable; nothing doubled by Displace.
- **Orientation:** the design is not mirrored or rotated; the top of the artwork is the top of the
  face.
- **Cylinder:** columns of a check or grid design narrow toward both sides; the bottom edge bows
  with the product's base and the top edge with its rim.
- **Colorway:** each colorway reads as its swatch at the garment's mid-tones (a navy shirt is navy,
  not pale blue); the folds and highlights sit where the original plate has them, as deep as on a
  real garment of that color; the print and the background did not change. `delta_e` and `folds`
  pass a light colorway made from a dark garment even when its folds are gone: `flat` catches it,
  and a white or light-gray blank chosen at intake avoids it. White on a white blank is the blank
  (`blank`): its folds are judged on a 100% crop.

## 6. Edges and frame

- The printable edge at 100%: no design on a lid, seam, handle or hand. One group mask, so no fringe
  between layers (Dinda [_VNqOhHJIm8 02:22]).
- The design's edge is as soft as the material: a hard pixel edge on fabric reads pasted.
- The whole frame at viewing size: the design's contrast and saturation match the photo's. A design
  that pops more than the product looks like an overlay.

## 7. Choosing and iterating

- Fix the quad before the light, and the light before the design. A change upstream invalidates
  every judgment below it.
- Change one value at a time: `shade`, `light`, the Displace scale, the map blur. Step back History
  between tries; a second `displace` stacks a second filter.
- When the plate's light fights every design (a hard shadow across the face, a hot reflection),
  change the plate, not the design.
- A design that fails only on one product color in a batch gets its own `shade` and `light` values
  in a second placeholder group, named for that variant.

## 8. Report

- The document, the group and layer names, the quad and its `corner_error` and `fit_check`.
- `lighting` `neutral` and opacities; `displace` scale, blur and the map path (it must stay on disk
  while the filter exists).
- Each design with its `drift` and output path; the sheet path.
- Each colorway with its output path, when the brief has colorways.
- What was not verified: hand warps, hand finishing, `contain` fits, anything judged only at
  fit-to-screen.
