# Render-to-real finish of a seated object

A calibrated 3D seat (procedure 12, route 1) gets the light direction, the shadow and the contact
right, yet the object can still read as CG: flat fabric, clean caps, a hard terminator. The finish
keeps the 3D scene for what it does well (camera, plate, cast shadow) and lets an image edit model
draw the materials. The composite frame becomes the edit's layout guide; only the masked region
comes back. A relight on the card then corrects what the edit got wrong about the light.

## 1. Guide and mask

The guide is a frame of the composite as delivered (8-bit, display-referred), the first frame of the
move. Write the mask from the element's own matte:

```bash
python3 scripts/finish_putback.py mask comp_f000.png elem_f000.png edit/ --dilate 22 --blur 3
```

It writes `region.png` (the matte dilated and blurred), `guide.png` (padded at the right and bottom
to a multiple of 16) and `mask.png` (the padded guide, alpha 0 over the region: transparent is
edited). Both steps refuse an output that is one of their inputs. They rewrite their own earlier
outputs, and replace any other existing file only with `--replace`. An empty element or region
writes nothing and exits 1.

The dilation is a per-model test. The edit fills the region it is given, and the room around the
outline is also where it draws contact and bounce. Measured on the terrace shot (the object about
250 px tall):

| Model            | Dilation and light line            | Result                                                                                            |
| ---------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------- |
| first edit model | 22 px, light described per face    | outline kept (6 % wider, 10 % taller than the model); contact and bounce drawn; form in the shade |
| its successor    | 6 px, shade asked to be even       | outline kept; flatter body, even orange, flat caps                                                |
| its successor    | 14 px, form asked for in the shade | proportions changed (the far cap oversized)                                                       |

Stay under a fifth of the object's smaller dimension, and read every take's outline against the
matte before anything else.

## 2. Model and references

Choose the model at run time: `recommend` (image-to-image edit, quality priority) plus `search`
sorted by creation date. Take the best recent edit model that accepts a mask and reference images,
then load its family skill before the run. Skip members the catalog tags as deprecated. References,
in order: the padded guide, then the product reference (a studio view of the real product). Pass the
mask, the guide's size and two outputs.

## 3. Prompt pattern

Four parts, in this order:

| Part            | What it states                                                                                                                                                                    | Example (a speaker on a terrace at sunset)                                                                                                        |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Keep            | everything outside the mask, the camera, the object's size, pose and position, the cast shadow                                                                                    | keep the photo, the speaker's size, angle and place, and its long shadow                                                                          |
| Materials       | each material as the product reference shows it                                                                                                                                   | coral woven fabric with a visible weave, matte cream end caps, navy rubber loop                                                                   |
| Light           | form in the shade: surfaces darken as they turn from sky to ground; the face looking away from the source sits below the sunlit ground; a thin soft rim on edges turned toward it | low sun behind on the left: the fabric darkens toward the ground, the right cap's face below the sunlit concrete, a thin warm rim on the left cap |
| Must not appear | the defects of the render and of edits in general                                                                                                                                 | no glow, no studio reflections, no second shadow, no text, no extra buttons                                                                       |

Never ask for "even" or "uniform" shade: the model flattens the whole object, and the result reads
like the render it was meant to fix.

## 4. Pick a take

Keep the masked takes; an unmasked take repaints the plate. Put each one back and measure how much
the model redrew outside the mask:

```bash
python3 scripts/finish_putback.py putback comp_f000.png take.png edit/region.png finished_f000.png \
    --elem elem_f000.png --finish-matte take_matte.png
```

`finishOutsideDiff` measured 0.019 to 0.025 (the model redraws the whole frame a little).
`outsideDiff` after the put-back: 0. `iou` compares the finished silhouette with the model's matte.

The gates are necessary conditions. Between takes that pass them, the full-size read decides: the
last frame beside a real photograph of a similar object under similar light, the weave, the cap
color, the loop, the form in the shade. A take that measures better while it looks flatter loses.
Measured: a take with an even, glowing body passed light, contact and material, and lost to a take
with form in the shade that failed light by a margin a relight fixed (section 6).

## 5. The moving shot: the finished element on a card

The 3D scene keeps the camera move, the plate, the shadow catcher and the cast shadow. The visible
model, its rim, bloom and veil, and its contact pass go off. The finished element goes on as a 2D
layer.

1. **Cut it with its own matte.** Seed a three-zone map from the model's matte (inside: eroded 8 px;
   unknown: out to 16 px) and cut by color. Add what differs from the scene without the object above
   its floor line: a light trim strip and a sunlit rim match sunlit ground in color and drop out of
   a color cut. Dark neutral pixels near the floor line leave the matte (they belong to the
   contact). Smooth the contour: a cut through a contact gradient steps. Read the cut at 2x over the
   plate: a dropped pixel inside a dark part shows as a light speck.
2. **Keep its contact.** The finish's own pixels under the body, alpha falling to zero over 16 px.
   Measured: a contact rebuilt as a multiply of the finish's darkening came out gray under the body.
   It also printed a light seam at the matte edge.
3. **Pin the card to a plane that moves like the model.** Corner Pin keyed per frame from a vertical
   plane through the model, projected by the comp camera at the first frame and at frame t. Fit the
   plane's yaw and depth so that its homography carries the model's matte of the first frame onto
   the model's matte of the last frame.
4. **Match the plate's edge width, nothing more.** Measure the element's edge width and the plate's
   sharpest edges near it at both ends with the check's finish reading. Key a Gaussian Blur only
   where the card is sharper than the plate (here 0 at the first frame, 2.0 at the last). Read the
   loop and the weave at 2x after it: a blur past the plate's width smears them.

Measured on a 200 px push (50 mm, the object 820 units away):

| Pin plane                                                                 | Card growth over the move | Model growth | At the last frame                     |
| ------------------------------------------------------------------------- | ------------------------- | ------------ | ------------------------------------- |
| through the floor line fitted from the matte's lowest pixels              | 1.30                      | 1.33 to 1.36 | the card slid 15 px against the model |
| yaw and depth fitted on the model's mattes (yaw -25 deg, 20 units nearer) | 1.32 to 1.34              | 1.33 to 1.36 | model matte carried at IoU 0.988      |

The floor-line fit failed because the rounded caps sit above the floor, so their lowest pixels cast
to the wrong depth. A card carries a push or a truck; it cannot turn with an orbit or a rotating
object.

## 6. Relight the card

Correct the light on the card, keeping the take. Work in linear light, on the element's own matte
only (the contact pixels stay as drawn):

1. **An exposure ramp across the body**, multiplicative so the form shading and the rim stay: down
   toward the face that looks away from the source, which sees ground in the object's own shadow.
2. **A small lift on the shade of the source-side end**, which sees sunlit ground. Apply it only
   under a luminance threshold so the rim is untouched.
3. **A highlight shoulder** on the brightest channel from 0.9 display: identity below, approaching
   1.0 above, hue kept. No global darkening.

Stop at the smallest correction that passes the light gate. Measured on the terrace shot (far side
over source side, first and last frame, limit 1.3):

| Ramp toward the far cap | Lift on the near cap's shade | Reading     |
| ----------------------- | ---------------------------- | ----------- |
| none                    | none                         | 1.57 / 1.63 |
| 0.3 stops               | none                         | 1.39 / 1.52 |
| 0.5 stops               | none                         | 1.30 / 1.42 |
| 0.7 stops               | 0.15 stops                   | 1.18 / 1.26 |

The shoulder took the clipped pixels from 133 to 0. Before tuning, find which pixels drive the
reading. Here 55 % of the far-side band was the dark loop, read against a neutral that a single
scale fit placed off the finished loop. The cream cap's far edge alone read 0.92 to 1.00.

## 7. Gates, on the first and last frame

| Gate        | How                                                                                                                                                     | Measured on the terrace shot                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Integration | the compositing skill's `integration_check.py --rendered`; neutral: the model under ambient light only, scaled and shifted onto the finished silhouette | all pass at the first frame; at the last, contact reads 3 px at 1 of 98 columns, where a rounded cap lifts off the floor |
| Plate       | mean absolute difference against the 3D build outside the element region, 40 px around both silhouettes                                                 | plate layer 0 at both ends; composite 0.00004 at the first frame (limit 0.004)                                           |
| Silhouette  | IoU of the finished element against the model's matte                                                                                                   | 0.82 (a reading: the outline is judged on the frame)                                                                     |
| Brand color | hue of the shaded camera-facing fabric against the brand color                                                                                          | 3.5 deg from the brand coral                                                                                             |
| Clipping    | channels at 255 on the element                                                                                                                          | 0 after the shoulder                                                                                                     |

Leave the finish's black level as the edit drew it: it was drawn over the veiled composite.
Measured: the seat's additive veil (0.012 linear) on the finish pushed the fabric's per-channel
light to 4.03 (material gate, limit 4.0). A toe lift up to the plate's darkest pixels grayed the
fabric (display 103 to 140) and flattened its weave.

## 8. Reading 16-bit captures

Pillow opens a 16-bit RGBA PNG as 8-bit. A linear capture quantized to 8 bits before the sRGB encode
loses its darks: one linear step near black becomes up to 13 display levels. Read 16-bit captures
with a reader that keeps the depth (OpenCV `IMREAD_UNCHANGED`, or a PNG decoder), encode, then write
the 8-bit frames the checks take.
