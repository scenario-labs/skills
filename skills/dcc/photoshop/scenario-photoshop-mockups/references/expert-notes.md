# Expert notes: product and brand mockups (the depth behind SKILL.md)

Each expert section is one person's or one channel's method, with the timestamps it rests on.
Timestamps are the start of the caption chunk that holds the words. Some videos name the models in
Photoshop's Generative Fill picker or the generator of a plate; this file uses capability words
instead:

- **Plate:** the product photo the design goes onto, without the design.
- **Placeholder:** the smart object fitted to the printable face; designs replace its contents.
- **Vector trace:** a raster logo turned into an editable SVG.
- **Cleanup fill:** a generative fill that removes or unifies something on the plate.

No rule here depends on one model: Photoshop's picker and the Scenario catalog both change.

## Measured: the toolkit on Photoshop 27.11

Setup: a 1000x800 document with one "product" layer of 40 px vertical gray strips (luminance 60 to
230), a quad `[[300,200],[700,240],[690,600],[310,560]]`, and flat or two-color designs made with
Pillow; a second white 1000x800 document for the fits, the cylinder and the colorways, with a white
and a black shirt (360x480, folds, made with Pillow) for the colorway colors. Fifteen tests, all
passing on macOS, plus one visual check of a flat, lit and displaced design on a generated tote
photo.

- **Fit.** `placeholder` lands every corner within 1 px of the quad, and `fit_check` stays under 0.5
  px. The rendered red was checked 5 px inside and 5 px outside each corner. A re-fit onto a second
  quad resets the warp first and passes the same thresholds.
- **Print size.** `placeholder(size=[800, 500])` on a quad whose box is 400x400 lands every corner
  within 1 px, then re-fits onto three more quads (one mirrored, one smaller) within 2.5 px
  rendered. A 1600x500 design with a dark band in its middle eighth comes back, after a `cover`
  replace, with the band from 0.375 to 0.625 of the face width: the 800x500 proportions held.
- **Placed results.** A result placed with `IO.place(..., fit="contain")` is a smart object placed
  from a file. `fit_quad` lands it within the thresholds and returns its new `id`.
- **Margins, clipping, selection.** A placed PNG with transparent margins keeps them through two
  fits (inner corners within 3.5 px rendered); a layer clipped above it stays clipped; an active
  selection is the same after the fit.
- **Cylinder.** `fit_cylinder(quad, 24, top_bulge=12, angle=120)` on an 800x400 checkerboard:
  corners within 2 px rendered, the bottom edge's middle 24 px below its corners and the top's 12
  px, column widths 44, 60, 70, 74, 74, 70, 60, 45 across (the edge columns 0.595 and 0.608 of the
  middle; sin over a 120 degree arc predicts 0.61).
- **Smart Filters.** A fit on a smart object with a Smart Filter is refused before any change.
- **Colorways.** Color mode alone (`match=False`) on eight gray strips keeps each strip's luminance
  within 2, so navy on a light strip reads pale blue and fails the swatch check. With the default
  Curves match, navy and forest land within Delta E 5 of the swatch, folds 0.9 or more, hue within 5
  degrees, the strips' order of lightness kept, the background and the print above unchanged, the
  document rendering identically afterwards. With a selection, only the selected strips change. On a
  white and a black shirt with folds (F7), navy, red and sand measured on the delivered PNGs: Delta
  E 0.12 to 0.48, folds 0.998 to 1.0; navy in Color mode alone on the white shirt: Delta E 75.
  Relative fold contrast on the white shirt: 0.23 before, 0.21 to 0.23 after; white there keeps the
  blank (no curve, mid-tones 228.2 to 228.3). On the black shirt, 0.58 before: navy 0.41 and red
  0.28 keep visible folds; sand 0.11 (faint folds) and white 0.004 (none) are flagged `flat`. The
  offset keeps the black shirt's fold depth in levels, which shrinks relative to a light swatch.
  `folds` is a correlation and reads 1.0 whatever the depth. The fixtures are synthetic; the same
  math on two frames from Anders [rrxTM5AZALU] (offline): a white tee kept 0.21 and the blank for
  white, a black sweatshirt fell from 1.13 to 0.57 (navy) and 0.39 (red), kept, and to 0.14 (sand)
  and 0.004 (white), flagged.
- **Replace.** A design swapped in moves no corner by more than 0.5 px; the content size does not
  change; Fill returns to 100; a left/right two-color design keeps its sides (no transposition).
- **Lighting.** Under a flat gray design, the composite got darker by more than 15 over a dark strip
  and brighter by more than 5 over a bright one. Outside the design, luminance stayed within 4 of
  its value: the copies stay clipped.
- **Displace.** At scale 100 with the default blur, a straight line across the design shifted by
  different amounts at two places more than 5 px apart. The map was saved as a PSD.
- **Batch.** Two designs gave two PNGs with the right colors. The document rendered identically
  before and after (difference 0) and the active History state was restored.
- **Group mask.** With a selection active, `placeholder` made it the group's mask: red inside the
  printable area, none outside.
- One fixture and one photo: authoring-time numbers. A real product with deep folds or gloss needs
  its own look.

## Measured: Photoshop 27.11 behaviors the toolkit works around

- **Custom warp.** Without `freeTransformCenterState` on the transform, a custom warp records
  nothing and changes nothing, with no error. It also needs `bounds` equal to the current box, 16
  mesh points (a 4 by 4 Bezier net in document pixels), and the box already moved onto the mesh's
  bounding box. A box far from the quad renders garbage or nothing.
- **Scale up, never down.** A custom warp lands on its points only when the smart object is scaled
  up from the box it was converted at. At that box or below, corners drift by up to 60 px, more as
  the quad's corners leave its bounding box. Each fit therefore wraps the object at 97% of the
  target's box (Convert to Smart Object), then scales it onto the box and warps.
- **Perspective.** The toolkit samples the perspective mapping of the unit square onto the quad at
  thirds for the 16 points. Corners land on the requested pixels.
- **Cylinder mesh.** The 16 points are Bezier control points, not samples. Across the label, x
  follows sin(theta) through a cubic Hermite whose inner controls sit 2a cos(a) / (3 sin(a))
  half-widths in from each side (a = half the arc). The top and bottom rows bow with controls at 4/3
  of the requested bulge, so each edge's middle lands exactly at it.
- **Re-fit.** `warpNone` can leave a transform the next fit rejects ("Numeric value expected"). A
  re-fit first applies a flat (identity) custom warp, which resets cleanly.
- **Wrapping.** Convert to Smart Object keeps only the opaque box: the toolkit adds a hidden frame
  layer the size of the box in a group first, so margins survive. Moving the layer into that group
  releases its clipping chain, and the conversion drops an active selection: both are put back.
- **Self-check.** After a good fit, `nonAffineTransform` equals the mesh's bounding box. A displaced
  corner shows there without reading pixels.
- **Print size.** Each fit replaces the object, so the print size rides in the layer's XMP
  (`scenario:printSize`) and `replace_design` reads it back.
- **Color mode.** The DOM constant for the Color blend mode is `BlendMode.COLORBLEND`;
  `BlendMode.COLOR` throws "Invalid enumeration value".
- **Replace Contents.** The new contents inherit the layer's transform: after a 50% scale, a 300x200
  replacement shows at 150x100, same center. The layer is renamed after the file.
- **Displace.** The Smart Filter keeps only the map's path and re-reads it on every re-render. Once
  the map is deleted, the next Replace Contents fails with "Could not complete the command because
  the file was not found."
- **History.** Deleting the active snapshot sends the document to its opening state; stepping back
  states does not.
- **Clipping.** A layer inserted between the base and its clipped layers releases the whole chain;
  add above the chain top, then clip.
- **Blend If.** Setting `blendRange` works on pixels, but reading the layer never reports it.
- **Placed bounds.** A placed PNG's layer bounds are its non-transparent box, not the placed canvas;
  the toolkit reads the smart object's transform instead.
- **Histograms** count only the selection on the active layer; the gates flatten a duplicate first.

## Unmesh Dinda: a design on a tote bag (_VNqOhHJIm8)

Photoshop educator (PiXimperfect). The deepest build in the sources: two designs on a canvas tote.

- Base first: load the saved selection, Hue/Saturation -64, "leaving a little bit of that in for
  more realism", then Curves, grouped as "base preparation" (Dinda [_VNqOhHJIm8 00:39]; [_VNqOhHJIm8
  01:13]; [_VNqOhHJIm8 01:48]).
- One mask on the group, "so that you don't have a copy of the same mask for multiple layers ...
  Otherwise, you will have some issues around the edge" (Dinda [_VNqOhHJIm8 02:22]); Option-drag it
  to the design group (Dinda [_VNqOhHJIm8 02:55]).
- Multiply, because the tote is brighter than the design: "whatever painting is going to happen
  there is only going to darken it" (Dinda [_VNqOhHJIm8 04:01]; [_VNqOhHJIm8 04:35]).
- Displacement: duplicate to a new document, desaturate, blur 1 to keep the texture, save as PSD,
  Displace 4 and 4 (Dinda [_VNqOhHJIm8 05:06]; [_VNqOhHJIm8 05:39]; [_VNqOhHJIm8 06:11]); the same
  filter Option-dragged to the second design (Dinda [_VNqOhHJIm8 06:43]).
- Ink: "whenever we print something on a piece of fabric like this, it is not that sharp. It's
  slightly blurred": 1 px, and the order of Displace and blur matters (Dinda [_VNqOhHJIm8 07:17]).
  The blur also softened the logo's stroke, so he wraps the layer in a smart object again and uses
  0.6 (Dinda [_VNqOhHJIm8 07:49]; [_VNqOhHJIm8 08:21]; [_VNqOhHJIm8 08:55]).
- Highlights: Blend If "also takes the design into consideration", so the mask comes from a channel
  (Dinda [_VNqOhHJIm8 09:28]); the Blue channel shows the folds best (Dinda [_VNqOhHJIm8 10:01]),
  then Curves or Levels on the mask (Dinda [_VNqOhHJIm8 10:35]; [_VNqOhHJIm8 11:08]).
- Per material: "each material is different", so each element gets its own clipped Curves (Dinda
  [_VNqOhHJIm8 11:43]; [_VNqOhHJIm8 12:15]).
- Finish: contrast Curves at the top (Dinda [_VNqOhHJIm8 14:25]); shadows desaturated through a
  Hue/Saturation masked from the Blue channel, -60 (Dinda [_VNqOhHJIm8 15:30]; [_VNqOhHJIm8 17:08]).
  He creates the adjustment with a selection active by mistake and keeps it in (Dinda [_VNqOhHJIm8
  16:02]).
- Review later, with every step editable (Dinda [_VNqOhHJIm8 17:41]). Without these steps, "the
  original colors would just seep in" (Dinda [_VNqOhHJIm8 18:13]).

## Unmesh Dinda: a drag-and-drop t-shirt template (sy1w5mTif-E)

- Three steps: make a placeholder, match it to the surface, place the design in it (Dinda
  [sy1w5mTif-E 01:07]).
- The placeholder holds "both bright and dark color" (Dinda [sy1w5mTif-E 01:38]): a red squiggle
  works in Multiply and fails in Screen, and a plain gray square hides the peaks and valleys (Dinda
  [sy1w5mTif-E 02:10]). His ramp has "all the shades and the grids" (Dinda [sy1w5mTif-E 02:43]),
  inside a smart object (Dinda [sy1w5mTif-E 03:15]).
- Liquify is more accurate; Displace is fine for the bumps (Dinda [sy1w5mTif-E 04:52]). Map:
  desaturated copy, Gaussian Blur 18 to keep only the folds, Displace 10, then 20 and 20 (Dinda
  [sy1w5mTif-E 05:23]; [sy1w5mTif-E 05:54]; [sy1w5mTif-E 06:27]).
- "Real printed stuff is slightly blurred": 1 px (Dinda [sy1w5mTif-E 07:00]).
- Multiply with Blend If split, then a copy with the opposite split (Dinda [sy1w5mTif-E 07:32];
  [sy1w5mTif-E 08:04]). On a white shirt, "you wouldn't have to do the next steps" (Dinda
  [sy1w5mTif-E 08:37]).
- Blend If on the design fails: "It needs to be based on the t-shirt and not the designs beneath it"
  (Dinda [sy1w5mTif-E 09:11]). A luminosity selection of RGB becomes the Screen group's mask, with
  Curves 170 and 44 (Dinda [sy1w5mTif-E 09:44]; [sy1w5mTif-E 10:16]; [sy1w5mTif-E 10:48]).
- The design layer sits on top at Fill 0, named "your design here" (Dinda [sy1w5mTif-E 11:21]); edit
  and save swaps it (Dinda [sy1w5mTif-E 11:55]). Saved as a PSDT, "Every time you open it, it's
  going to create a new document" (Dinda [sy1w5mTif-E 13:04]; [sy1w5mTif-E 13:35]).

## Unmesh Dinda: a pattern on fabric (Z168F2BlAdA)

- The pattern sits in a smart object, warped with extra splits for each fold (Dinda [Z168F2BlAdA
  02:43]; [Z168F2BlAdA 03:17]; [Z168F2BlAdA 04:24]), then Liquify with Show Backdrop (Dinda
  [Z168F2BlAdA 06:04]).
- Displace is "not very accurate" for an all-over pattern: it moves unrelated areas (Dinda
  [Z168F2BlAdA 07:09]).
- Swapping the pattern goes through the smart object (Dinda [Z168F2BlAdA 15:04]). Start with a basic
  check pattern, "that way all of the folds and the stretching will be more accurate" (Dinda
  [Z168F2BlAdA 15:36]).

## Marty Geller: a label on a crushed can (0l2Ma_2B-A8)

Photoshop educator (Photoshop Arthouse).

- Goal: replace the label later without repeating a step (Geller [0l2Ma_2B-A8 00:01]).
- Select Subject, then the Curvature Pen removes the top and bottom, saved as a channel (Geller
  [0l2Ma_2B-A8 00:32]).
- "Displacement maps look best when they are slightly blurred": 3 px, saved as a copy in PSD (Geller
  [0l2Ma_2B-A8 01:04]; [0l2Ma_2B-A8 01:38]).
- A smart object at lower opacity, warped on a 4 by 4 mesh "without going inside the can" (Geller
  [0l2Ma_2B-A8 03:12]; [0l2Ma_2B-A8 03:45]); the label pasted inside it (Geller [0l2Ma_2B-A8
  04:23]).
- Multiply, then Displace "15 pixels, stretch to fit, and repeat edge pixels" (Geller [0l2Ma_2B-A8
  05:24]).
- The alpha channel becomes the mask, "white reveals and black conceals", shared with a Levels
  layer: midtones 1.06, white input 217 (Geller [0l2Ma_2B-A8 05:59]; [0l2Ma_2B-A8 06:31];
  [0l2Ma_2B-A8 07:06]).
- Blend If on the underlying white slider, split with Option, lets the can's brightest tones show
  through the label (Geller [0l2Ma_2B-A8 07:39]).

## Morgan Hastie: bottles with Generative Fill (70L2ngS8raY)

Graphic designer, on Adobe's Photoshop channel.

- A direct warp on the raw photo is "fine. It's not great though" (Hastie [70L2ngS8raY 00:33]).
- A cleanup fill with a partner model removes the old labels and "preserved all the details in the
  shape from the bottle" (Hastie [70L2ngS8raY 01:04]; [70L2ngS8raY 01:36]); a second model unifies
  two bottles side by side (Hastie [70L2ngS8raY 02:12]).
- The prompt protects the product: "Don't change the bottles and add subtle shadows". The label
  artwork comes "in SVG form" (Hastie [70L2ngS8raY 02:47]).
- Labels become smart objects "to not only switch out that artwork if it gets changed, or if my
  client has any revisions", warped with Arc Lower (Hastie [70L2ngS8raY 03:21]), then set to
  Multiply (Hastie [70L2ngS8raY 03:53]).
- Rough is acceptable for a quick client visual (Hastie [70L2ngS8raY 04:28]).

## Philip Anders: a t-shirt on a generated plate (rrxTM5AZALU)

Print-on-demand seller. The plate is a generated image.

- "You will need to upscale your mockups before importing them into Photoshop", 4x (Anders
  [rrxTM5AZALU 00:34]).
- Liquify is optional (Anders [rrxTM5AZALU 01:38]). Inside it, the backdrop set to the background
  layer at 5 to 7 opacity shows the creases to push the design along (Anders [rrxTM5AZALU 02:11]).
  Don't go overboard (Anders [rrxTM5AZALU 02:43]; [rrxTM5AZALU 03:16]).
- A plate copy clipped in Hard Light, then Curves (Anders [rrxTM5AZALU 04:25]). The dark slider
  makes the design disappear; move the bright side and find "the sweet spot" between shadow and
  highlight (Anders [rrxTM5AZALU 04:58]; [rrxTM5AZALU 05:31]).
- Design opacity 90%, so the fabric shows through (Anders [rrxTM5AZALU 06:38]; [rrxTM5AZALU 07:10]).

## Can and package builders (C3ZkcqB36xw, boONV-waIUk, -VM3ee1O_8U, SKYL0FCOO04)

Short channel tutorials, the same skeleton four times.

- **Design Master (soda can):** a rectangle converted to a smart object "for easy editing", lower
  opacity, the Cylinder warp preset, clipped (Design Master [C3ZkcqB36xw 00:00]; [C3ZkcqB36xw
  00:38]). Opacity back to 100, design pasted inside (Design Master [C3ZkcqB36xw 01:11]). A can copy
  clipped in Multiply "for a realistic shadow", lowered "for a natural blend" (Design Master
  [C3ZkcqB36xw 01:47]); more copies for highlights and shadows, then Levels and an Overlay copy
  (Design Master [C3ZkcqB36xw 02:17]; [C3ZkcqB36xw 02:49]).
- **Quick Fix Up (tin can):** the smart object lets you "insert and edit your design
  non-destructively", renamed "place design here", warped (Quick Fix Up [boONV-waIUk 00:33];
  [boONV-waIUk 01:05]). "Leave out the lid and the lower part" with a group mask (Quick Fix Up
  [boONV-waIUk 01:39]). Linear Burn "to blend the design with the can's natural highlights and
  textures" (Quick Fix Up [boONV-waIUk 02:15]); a Camera Raw copy, darker with brighter whites, in
  Screen with Fill lowered (Quick Fix Up [boONV-waIUk 03:21]).
- **WeJustClickme (can for beginners):** measures the can first, 736 px high and 418 px wide
  (WeJustClickme [-VM3ee1O_8U 00:00]); Fill lowered, warp "as close as possible to the can"
  (WeJustClickme [-VM3ee1O_8U 01:06]); Pen selection "excluding the top section" as a group mask
  (WeJustClickme [-VM3ee1O_8U 02:22]); Linear Burn, then a darker Camera Raw copy in Screen
  (WeJustClickme [-VM3ee1O_8U 02:54]; [-VM3ee1O_8U 03:29]).
- **Mockup Art (coffee bag):** a front rectangle as a smart object, opacity lowered, Distort on four
  points, then Warp with grid lines for the curved area (Mockup Art [SKYL0FCOO04 04:56];
  [SKYL0FCOO04 05:31]; [SKYL0FCOO04 06:16]). The bag's masks combined, then three background copies:
  Shadow in Multiply, Midtone in Linear Dodge (Add), Light in Screen, each with Levels (Mockup Art
  [SKYL0FCOO04 14:35]; [SKYL0FCOO04 15:12]; [SKYL0FCOO04 15:47]). Captions are machine-made and
  partly garbled; only the steps shown are used.

## GraphiqVibe: from dieline to box mockup (WeDJv63Wgjk)

Packaging design channel.

- Start from "the size that we used for the design" (GraphiqVibe [WeDJv63Wgjk 01:37]).
- Each face gets its own color and name, then becomes a smart object at lower opacity, its corners
  Cmd-dragged onto the box "carefully" (GraphiqVibe [WeDJv63Wgjk 04:21]; [WeDJv63Wgjk 04:58]).
- After editing the contents, "it's not placed properly", so adjust; a gradient overlay sets light
  from one side (GraphiqVibe [WeDJv63Wgjk 05:37]; [WeDJv63Wgjk 06:13]; [WeDJv63Wgjk 06:46]).
- The mockup is reused by duplicating the file and changing the design (GraphiqVibe [WeDJv63Wgjk
  07:50]).

## Brendan Williams: outlining a logo (tNrV1XdZX0o)

Photoshop educator.

- Check for existing transparency first (Williams [tNrV1XdZX0o 00:00]).
- A channel cutout "keeps nice sharp edges": duplicate the channel with the most contrast, Levels,
  Cmd-click, mask (Williams [tNrV1XdZX0o 00:31]; [tNrV1XdZX0o 01:03]; [tNrV1XdZX0o 01:37]).
- Export as PNG to keep the transparency (Williams [tNrV1XdZX0o 03:14]).

## Aidan Stanik: mockups through an agent connector (QTS-IWB3MKY)

Tests an agent driving Adobe tools; no Photoshop document is built by hand.

- Two mug photos taken from the internet gave the same design at different sizes: "the second mug is
  way smaller" (Stanik [QTS-IWB3MKY 13:35]); he blames the camera distance (Stanik [QTS-IWB3MKY
  14:07]).

## Disagreements and the deciding condition

- **Multiply or Linear Burn.** Most builders use Multiply (Dinda [_VNqOhHJIm8 04:35]; Geller
  [0l2Ma_2B-A8 05:24]; Hastie [70L2ngS8raY 03:53]); can builders use Linear Burn with a Screen copy
  for the shine (Quick Fix Up [boONV-waIUk 02:15]; WeJustClickme [-VM3ee1O_8U 02:54]). Decider:
  Multiply keeps brand color on a bright product; Linear Burn suits bright metal and always needs
  the Screen copy. The toolkit's Shading and Highlights copies cover both, relative to the mean.
- **Preset, mesh or corners.** Cylinder and Arc Lower presets (Design Master [C3ZkcqB36xw 00:38];
  Hastie [70L2ngS8raY 03:21]), a 4 by 4 mesh (Geller [0l2Ma_2B-A8 03:45]), or Distort on four points
  (Mockup Art [SKYL0FCOO04 05:31]). Decider: a flat face takes four corners (`fit_quad`); a regular
  cylinder takes `fit_cylinder`, or the preset by hand; a crushed, tapered or irregular surface
  takes the mesh by hand.
- **Displace or Liquify.** Dinda rejects Displace for an all-over pattern (Dinda [Z168F2BlAdA
  07:09]) and keeps it for a print's bumps (Dinda [sy1w5mTif-E 04:52]). Decider: a print on a face
  takes Displace; an all-over pattern across deep folds takes warp splits and Liquify by hand.
- **Displace strength and map blur.** 4 with a 1 px blur on a tote (Dinda [_VNqOhHJIm8 06:11]), 15
  with 3 px on a crushed can (Geller [0l2Ma_2B-A8 05:24]), 10 to 20 with 18 px on a t-shirt (Dinda
  [sy1w5mTif-E 06:27]). Decider: crease depth and pixel width; start at the toolkit's default and
  read the ramp's grid.
- **Mask source.** The Pen for hard rims (WeJustClickme [-VM3ee1O_8U 02:22]), Select Subject for
  speed (Geller [0l2Ma_2B-A8 00:32]), a saved channel for reuse (Geller [0l2Ma_2B-A8 01:04]).
  Decider: the rim's hardness and whether the mockup is a template.
- **Highlight recovery.** Blend If (Dinda [sy1w5mTif-E 07:32]), a channel mask (Dinda [_VNqOhHJIm8
  09:28]), a Camera Raw copy in Screen (Quick Fix Up [boONV-waIUk 03:21]), or several copies (Mockup
  Art [SKYL0FCOO04 15:12]). Decider: whatever reads the product, never the design (Dinda
  [sy1w5mTif-E 09:11]).
- **Colorway: Photoshop or a model.** WeJustClickme recolors a t-shirt with a Solid Color layer
  clipped to it in Color mode (WeJustClickme [i-hYHLXDheU 02:10]); Quick Fix Up recolors the
  background with a Solid Color layer in Linear Burn and re-picks its color later by double-click
  (Quick Fix Up [boONV-waIUk 02:47]). Color mode alone keeps the garment's luminance, so a white
  shirt cannot turn navy (measured below); `colorways` puts a Curves layer under the fill first.
  Decider: a dye or a flat color stays a Solid Color layer (`colorways`, checked against the
  swatch), on a white or light-gray blank; a change of material (heather, wash, a different weave),
  or light colors wanted from only a dark garment, is an instruction edit on the plate. [added] No
  source shows a dark garment turned light.
- **Logo cutout.** A channel for a large flat logo (Williams [tNrV1XdZX0o 00:31]); a vector for
  print (Hastie [70L2ngS8raY 02:47]). Decider: a small, blurry or photographed logo needs a vector
  trace.

## What reads as pasted on

- A design evenly lit on a creased or curved product.
- Straight lines in the design across visible folds.
- A design sharper than the fabric under it.
- Corners that float off the face, or an edge that runs onto a lid, seam or hand.
- Brand color shifted toward the product's color in the lit areas, or a design lost in the shadows
  of a dark garment.
- Product grain or weave printed onto the design (a map with no blur).
- The same design at different scales across products in one set.

## Gaps in the sources

- No expert measures a fit; the corner and drift thresholds come from the live tests above.
- No source shows scripting; every build is by hand.
- No source covers reflective screens, glass, or embroidery.
- A vector logo for print is mentioned (an SVG label) but not shown; the vector route comes from
  `scenario-image-editing` and `scenario-brand-kit`.
- No source covers Windows, 16-bit masters or print color modes for mockups.
