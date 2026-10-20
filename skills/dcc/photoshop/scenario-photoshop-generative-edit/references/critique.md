# Critique: judging a generative edit

Order of judgment:

1. The capture files, before any paid run.
2. The code gates on each take (`GE.check`).
3. Each passing take inside the mask at 100%, against the brief.
4. The placement and the outside check (`place_edit` bounds, `GE.verify`).
5. The seam at 100% and 200%, then the canvas as a whole.

A stage passes only when every code gate passes and every visual item for the edit type has been
looked at and noted. The numbers catch misplacement, tone shifts and leaks. They never catch
anatomy, likeness, text or a wrong object: the measured job's enlarged pupil passed every gate.

## 1. Before the run: the capture

- `context.png` shows the change and enough surroundings to continue light, texture and perspective.
- `mask_edit.png` is white on the footprint of the result and black elsewhere. Shadows to remove are
  inside it; hair or hands that must stay in front are outside it.
- The box's long side is no larger than the member's output. If it is, plan tiles or a larger output
  before quoting the run.
- References are pre-cut to one object each and hidden from the context.

## 2. Code gates

| Gate                       | Pass                                  | Fails on                                        |
| -------------------------- | ------------------------------------- | ----------------------------------------------- |
| `aspect_ok`                | take ratio within 1% of the capture's | a fixed-ratio member, a cropped or padded take  |
| `edited`                   | inside mean 3 or more                 | prompt or mask ignored                          |
| `polarity_suspect`         | false                                 | mask read inverted: outside changed, not inside |
| `seam_ok`                  | bias under 12 and residual under 6    | tone shift (bias), shift or rescale (residual)  |
| Resolution                 | take width at least the box width     | a soft patch beside sharp pixels                |
| `place_edit` bounds        | equal `cap["bounds"]`                 | a placement or transform error                  |
| `A.history_gate(h0, undo)` | `[]`: one new named state per take    | a stray edit on the user's document             |
| `verify()["untouched"]`    | outside max 2 or less                 | a missing or wrong layer mask                   |
| `A.deliverable(...)`       | returns `[]`                          | profile problems, hidden takes outside "Takes"  |

Thresholds are authoring-time, from two real takes of one image. A take that fails a code gate is
never placed. An outside mean of 10 or more on a passing take is expected: the member re-rendered
the frame, and the mask hides it.

## 3. Every take, inside the mask, at 100%

- **The brief:** the named change happened, and only that. Nothing listed as "keep" moved.
- **Footprint:** the new object stops where it should. A selection wider than the subject makes the
  subject grow into its neighbors.
- **Light:** direction, color and hardness match the scene. Shadows fall the same way as the photo's
  shadows and continue across the edge.
- **Texture and grain:** noise, grain size and sharpness match the surrounding photo. A smooth,
  plastic patch reads as generated.
- **Perspective and scale:** lines converge to the scene's vanishing points; the object's size fits
  its distance.
- **Small structure:** eyes (pupil size, catchlights), hands (finger count, joints), teeth, text,
  logos, edges of thin objects.

## 4. By edit type

- **Object replacement or addition:** contact shadows under the object; reflections where the
  surface reflects; the object's color holds under the scene's light.
- **Removal:** no ghost of the object or its shadow; the background's structure (tiles, bricks,
  horizon lines) continues straight through; no repeated patch of texture.
- **Recolor:** only the named part changed color; highlights and shading kept their shape; no color
  bleeds onto edges.
- **Swap from a reference:** the reference's design survives (pattern, stitching, logo, buttons);
  nothing extra from the reference photo came along (a hand, a second object).
- **Text replacement:** spelling letter by letter, the font's weight and slant, perspective on the
  surface.
- **People:** likeness against the original face at 100%; age, skin tone and expression unchanged
  unless asked; hairline and ears intact.
- **Expand:** the horizon and the light direction continue; no mirrored or repeated elements; the
  new area's grain matches; the source did not move (the residual says so).
- **Tiles:** at fit-to-screen, no object repeated per tile and no grid; at 100%, no join between
  tiles.
- **New angle:** the object's perspective matches the scene's horizon; contact shadows and
  reflections follow the new pose; the object's identity (shape, markings) is kept.
- **Annotation edit:** each note was applied; no red mark or letter survives.
- **Trained style:** the style reads inside the selection; the transition at the mask edge is
  gradual where the brief wants it, clean where it does not.

## 5. The seam and the canvas

- **100% crop** of the box plus 32 px: no line, no tone step, no halo along the mask edge.
- **200%** (the 100% crop enlarged with nearest-neighbor): grain continues across the edge. This is
  where a resolution seam shows first.
- **Overlay** when the residual is between 4 and 6: gray where the take lines up with the base, red
  or cyan fringes where it does not.
- **Canvas preview** at fit-to-screen: the edit belongs to the picture; the eye does not go to it
  first.

## 6. Choosing between takes

1. Drop every take that fails a code gate.
2. Rank the rest on the brief first, then light, then texture.
3. Between close takes, prefer the lower seam residual, then the lower bias.
4. Place the best take; place the runners-up as hidden layers, in a group named "Takes", only when
   the user wants to compare.

## 7. Report

One block per edit:

- **Verdict:** placed, or not placed and why.
- **Evidence:** the take kept and its `check` numbers (bias, residual, size against the box);
  `verify` outside max; paths to the takes sheet, the 100% seam crop and the canvas preview.
- **Rejected takes:** one line each, the gate or the visual item that failed.
- **Not verified:** what no gate covers here (likeness judged by eye only, a member's alignment not
  measured, Windows).
