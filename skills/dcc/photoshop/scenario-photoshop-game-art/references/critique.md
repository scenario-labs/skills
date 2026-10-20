# Critique: judging game art

Order of judgment:

1. The code gates on the master and on every take.
2. The tiled or in-context view at fit-to-screen: the asset as a player sees it.
3. 100% crops where the eye fails first: the seam cross, edges of cut-outs, stretched parts.
4. Maps and exports read back as files, not as layers.
5. A verdict per take, written down, before anything is delivered.

A stage passes only when every code gate passes and every visual item for the asset type has been
looked at and noted. The numbers catch seams, blotches, value drift and misalignment. They never
catch style drift, a wrong material or an ugly shape: the seam gate passed a repair take that the
eye rejected for style drift.

## 1. Code gates

| Gate                            | Pass                                      | Fails on                                        |
| ------------------------------- | ----------------------------------------- | ----------------------------------------------- |
| `tile_check` `seam_ok`          | both ratios under 1.5                     | an edge that steps; grain read as a step        |
| `tile_check` `patch_ok`         | `patch_range` under 12                    | a light falloff, a dark patch, a hot spot       |
| `tile_check` `pow2`             | true on a texture                         | a size the engine will not mipmap or stream     |
| `GE.check` per take             | `edited`, `aspect_ok`, `seam_ok`          | a no-op take, a moved stone, a tone shift       |
| Take resolution                 | `b_size` at least the capture box         | a soft band between sharp pixels                |
| `GE.verify` `untouched`         | true                                      | a missing band mask, a stray edit               |
| `A.deliverable("game-texture")` | `[]` on the master                        | CMYK, 16-bit, an odd size                       |
| Export results                  | `pow2` true, size as asked                | a resize to the wrong size                      |
| Packed and gray values          | read back equal the sources (alpha ±1)    | a color conversion on a data map                |
| `nine_slice_check` `ok`         | every stretched part under 1.0            | detail in an edge or the center                 |
| `G.halo` rims                   | `light_rim` and `dark_rim` 8 or less      | a matte fringe from the old background          |
| `id_select` `bounds`            | not None; `partial` small next to `share` | a missed color; a blurred or compressed ID pass |
| `G.structure` on style takes    | compared between takes only               | read against a fixed number                     |

Thresholds are authoring-time, measured on one texture set and synthetic frames. A take that fails a
code gate is never placed.

## 2. Tiles

Read the 3x3 preview at fit-to-screen first, then at a smaller size, then the cross at 100%.

- **No grid.** No line, step or brightness change where tiles meet. Dinda re-checks in Pattern
  Preview after every repair and fixes what remains "by offsetting again" [CyJgXBJVHkU 08:43].
- **No repeat.** Zoomed far out, nothing marks the tile: no dark patch, no bright patch, no lone
  element that draws the eye. "When you zoom out even a lot you cannot tell that it's a pattern"
  [9_36YihB8I4 06:01]. A single off-color brick or stone counts [9_36YihB8I4 07:41].
- **Whole objects on the cross.** Stones, bricks, planks and tiles continue across the seam at their
  normal size. No half stone, no doubled mortar line, no smeared joint.
- **Same resolution.** The band is as sharp and as grainy as its neighbors. A soft band means the
  member's output was smaller than the box [9_36YihB8I4 03:17].
- **Same style.** Shapes, edge wear and color in the band match the rest. A band that reads as
  another material fails even when every number passes.
- **Light is flat.** No baked direction strong enough to reveal the repeat: a texture lit from one
  side tiles as stripes.
- **Re-render only:** shown beside the original; the user accepted the change of look.

## 3. Maps

- Every map has the albedo's size and tiles: read each one's 3x3 preview, not only its numbers.
- **Normal map:** mostly lavender-blue, details reading as raised where they are raised. Lit in the
  engine, bumps should catch light from the light's side; inverted bumps mean the green channel
  convention is the other one. Write the convention down; never guess it.
- **Roughness or smoothness:** dark means smooth in roughness, rough in smoothness. Wet or polished
  areas read correctly for the map's convention.
- **Height and ambient occlusion:** crevices dark, raised areas light, no lighting baked from the
  albedo's shadows that contradicts the geometry.
- **Packed texture:** each channel opened on its own matches its source layer; alpha present on a
  TGA; the layout written in the handoff with sRGB off.
- **Pixel art and PSX:** resized with `nearest`; pixels square and crisp at 100%, with no blur and
  no ringing.

## 4. Style passes and paintovers on renders

Judge each take beside the render and beside the other takes (`R.sheet`), never by toggling one
layer. Frederick finds it "easier to see the differences objectively" side by side [pAIYEsECSRw
26:55].

- **Alignment.** The overlay is gray where silhouettes match; red or cyan fringes mean the member
  moved the layout. Compare `G.structure` scores across takes; the lowest kept the most.
- **Values.** A grayscale copy keeps the focal object separate from its background. Octopunish found
  a beetle "blending completely into the slope" this way and added light under it [h1i3X0gqrQs
  21:20, 21:54].
- **Variety.** The takes differ in palette, time of day or mood. Two takes that only shift hue are
  one idea twice [h1i3X0gqrQs 07:39].
- **No 3D left over.** Smooth computer gradients broken up; no area left "very, very 3D" next to
  painted ones [j_czTAnOSCM 17:06]. Soft shadows flattened, contact shadows darker where objects
  touch [j_czTAnOSCM 12:09].
- **Believable wear.** Imperfections, dirt and lived-in detail where the brief allows them
  [gjkaYE8_MoE 12:36].
- **Finished at every stage.** The image reads as complete at its current level of detail
  [gjkaYE8_MoE 09:53]; detail is added from afar, then closer [h1i3X0gqrQs 23:32].
- **Kept the render's facts.** Light direction, camera, scale and object count unchanged, unless the
  brief asked for a change.

## 5. Sprites, icons and UI parts

- **Edges on contrasting fills.** View every cut-out over black, white and a saturated color.
  AI2Play found holes "inside the letters" only on a different background [AEXy7F5sJ7M 07:42], and a
  one-pixel light or dark edge from the old background [AEXy7F5sJ7M 08:16].
- **Padding.** The canvas holds the whole drop shadow plus a margin; nothing touches the edge.
- **Shadows.** Outer shadows dark but "not completely black" [vo7vwzzgDPk 09:21].
- **Readability at size.** Icons read at the size the game draws them: export a copy at that size
  and look at it at 100%.
- **Set consistency.** Every icon of a set shares light direction, outline weight, palette and
  framing. Test new assets against the existing buttons and backgrounds, as pixaroma does before
  upscaling [vU-_9R-Tq18 14:27].
- **Colorways.** Each variant keeps the original's value structure; transitions stay smooth
  (Gradient Map hues, not Hue/Saturation) [vo7vwzzgDPk 09:52].
- **Text.** Live type, font present, the same font and size for one control type across the kit.

## 6. 9-slice parts

- `nine_slice_check` passes, or the user accepts a part that tiles instead of stretching.
- Stretch a copy to twice and four times the width in Photoshop (Free Transform on a duplicate,
  corners excluded) or in the engine: corners keep their radius, edges stay clean.
- Corner insets cover the whole rounded corner and any rivet or ornament.

## 7. Verdict

Write one line per take: pass or fail, the gate or item that decided it, and what to change. Hide
and name losing takes ("Style pass, take 3, rejected: values"). Deliver nothing that has only passed
the numbers.
