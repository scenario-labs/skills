# Expert notes: generative edits inside a selection (the depth behind SKILL.md)

Each section is one expert's method, with the timestamps it rests on. Timestamps are the start of
the caption chunk that holds the words. The videos name the models in Photoshop's picker; this file
uses capability words instead:

- **Adobe's own fill model**: the Adobe model built for fill and expand, which reads the whole
  image.
- **Partner models**: the third-party models in the same picker, which receive only the selected
  area.

The picker's lineup changes between releases, so no rule here depends on one model.

## The measured round trip (one real Scenario inpaint)

Setup: a 512 px owl photo, an ellipse selection around the left iris, and
`GE.capture(out_dir, polarity="alpha")`. A Scenario inpaint member took the context as input and an
RGBA mask (transparent = edit), and returned 2 outputs at low quality for an ice-blue iris.

- **Output size:** 1254 px square for a 222 px input. `check` and `place_edit` fit any size with the
  capture's aspect into the capture box.
- **Whole-frame re-render:** mean difference 17 to 18 outside the mask. Feather texture was redrawn
  and the tone came out about 6 to 7 levels darker.
- **Masked placement hides it:** after `place_edit`, `verify` measured outside max 0. No seam at
  100% and at 4x.
- **The model fills the mask:** the ellipse was wider than the iris, and the new iris grew to fill
  it, over part of the dark eyelid rim.
- **Prompt drift inside the mask:** both takes enlarged the pupil against the prompt; take 1 lost
  the catchlight. Take 2 was kept, by eye.
- **Seam gate,** on images blurred by 4 px, ring 12 px past a 2 px gap. A raw ring difference
  (mean 17) failed both good takes.

| Result                          | Bias (worst channel) | Residual |
| ------------------------------- | -------------------- | -------- |
| Real take 1                     | 6.4                  | 3.5      |
| Real take 2                     | 7.3                  | 3.4      |
| Take 2 shifted 3 px             | 12.4                 | 8.8      |
| Take 2 scaled 103%              | 10.3                 | 6.9      |
| Take 2 tinted +20 red, -20 blue | 20.6                 | 3.9      |
| Take 2 darkened 15              | 18.7                 | 4.2      |

What it means for an agent:

- Any aligned image-to-image result can serve a selection-scoped edit. The layer mask does the
  protecting, so never place a result without it.
- The selection's shape is the result's shape. Draw it on the footprint of the change.
- A seam shows tone or alignment. Texture differences vanish under a 4 px blur, so a raw difference
  is the wrong gate.
- No code gate sees anatomy. The enlarged pupil and the lost catchlight passed every number.

## Jesús Ramirez: retouch, removal, rotation (Ot_h4s1mXas, fR0CI04XBpM, MvxUcebxhRc, -T5RVvMLUTs)

Entertainment poster artist (TV and film key art), Photoshop Training Channel; Ot_h4s1mXas is on
Adobe's own channel.

- **Context differs by model.** Adobe's own fill model looks "at the entire image for context";
  partner models "only see a square crop around your selection, and you must type in a prompt"
  [Ot_h4s1mXas 01:36]. He repeats it for a watch [fR0CI04XBpM 08:12] and for windshield reflections
  [-T5RVvMLUTs 04:52].
- **Art director, not operator.** Cycle the three variations and pick [Ot_h4s1mXas 02:11]; generate
  again for three more [02:44]; toggle the eye icon to compare with the original [03:17].
- **Sleeves without a prompt.** Select around the sleeve, generate with no prompt, keep the best fit
  [Ot_h4s1mXas 02:44].
- **Keep-clause.** On a composite he types "Keep the same scale and pose." [Ot_h4s1mXas 07:01].
- **Organization.** Name the layers and group the generated ones, then disable the group to compare
  [Ot_h4s1mXas 04:51].
- **Which model for which job.** Adobe's own model handles small details, removal and expansion
  well, at a fraction of a partner model's credits [fR0CI04XBpM 07:07].
- **One side at a time.** Expanding one side puts more pixels on that area [fR0CI04XBpM 09:16].
- **Square selections for partner models.** A perfect square marquee gives results "that match the
  background" [fR0CI04XBpM 14:43].
- **The selection sets the scale.** With a reference placed into the selected area, "the selection
  will determine the scale" of the object [fR0CI04XBpM 17:28].
- **Hard removals in parts.** Remove the straps first, then the bag [MvxUcebxhRc 02:06].
- **Clean plate.** When the object touches the subject, remove it to a clean plate first
  [MvxUcebxhRc 04:42]. Grow the object's selection about 4 px with Quick Mask and Filter > Other >
  Maximum [05:13].
- **Rotate Object replaces the layer.** The pixel layer becomes a rotatable object, so duplicate it
  first [-T5RVvMLUTs 01:05]. For a person, make a clean background plate first, then duplicate and
  rotate [05:23].

## Julieanne Kost: partner models and prompting (1bFcFVbbzjc)

Adobe Principal Digital Imaging Evangelist. Recorded on the 2025 beta.

- Photoshop sends the selected area to the cloud [00:32]. Partner models returned one result,
  rendered at 1K [01:05].
- **Fix spill on the mask.** Yellow rims she did not want: brush, black, on the layer mask [01:38].
- **Instruction prompts.** Partner models want "detailed instructional text prompts describing what
  you want the model to do" [02:13]. Her background swap adds "Do not alter the car in any way."
  [01:38]. An earlier layer, prompted "on" rather than "along" a dirt road and with no keep-clause,
  came out less accurate; Adobe's own models do better with a description of what to see [02:13].
- **Text.** Put the old text and the new text in quotes [03:19].
- **Correct in layers.** Oversaturated strawberries were fixed with Object Selection and a
  Hue/Saturation adjustment, not a new generation [05:34].
- **References and size.** A reference photo got the intended eggs [06:07]. A large selection is
  generated at 1K and needs upsampling, unlike a smaller selection [06:07].
- **Selection rules differ per model.** With Select All, Adobe's model filled the whole canvas with
  wing [07:13]; a generous selection around the gap worked [07:46]. Partner models failed on that
  selection for lack of context and succeeded with Select All [07:46, 08:18].

## Colin Smith: footprint, resolution, likeness (pgBjkr2X6wI, mGV_jkmPjcY, f-7wkNmAtDk, qeeAa8pnICc)

Photoshop trainer, photoshopCAFE.

- **The selection bounds the result.** For new sleeves: "It doesn't necessarily fill that area, but
  it can't generate outside of it." [pgBjkr2X6wI 02:45].
- **Keep hair in front of a swapped jacket.** Paint the selection with the Selection Brush, then
  hold Alt or Option to subtract the hair [pgBjkr2X6wI 11:04].
- **Resolution is a seam.** A 1K fill beside a fine-grain photo shows a visible line at zoom
  [mGV_jkmPjcY 05:26]. With the January 2026 model at up to 2K, the difference is hard to see at
  256% and gone at 100% [06:38].
- **Grain as an adjustment layer.** Amount, size and roughness; Darken or Lighten blend to keep only
  dark or light grain; opacity to dial it in [mGV_jkmPjcY 02:35, 03:08, 03:42].
- **A generative layer is replaced.** Generating again on it replaces the earlier edit; make a new
  selection for a new edit [f-7wkNmAtDk 02:05].
- **Text in quotes** keeps the font [qeeAa8pnICc 02:37].
- **Likeness.** He added "still looking like themselves" after people drifted [qeeAa8pnICc 04:13].
- **Color.** Add "Don't change colors"; a 16-bit image shifted colors a lot, so he works in 8-bit
  [qeeAa8pnICc 04:47].
- **Partner fills** were limited to 1K inside Photoshop at the time [qeeAa8pnICc 08:36].

## Brendan Williams: selection recipes (SB60EQG2HyE, 6zfce_gIfw0, 0h8lwK-shOY)

Photoshop educator, Brendan Williams Creative.

- **Removal selection.** Select "just outside of the object" to give overlap, loosely, including the
  shadow [SB60EQG2HyE 03:49]. No prompt; three variations to choose from [04:21].
- **Smaller pieces.** Working in small pieces gives a higher-quality result than one big selection
  [SB60EQG2HyE 05:57].
- **Extending one layer.** Disable the layer below "to prevent the AI from becoming confused"
  [6zfce_gIfw0 19:24]. Expect to generate several times [20:26].
- **Gray selection as strength.** A channel darkened with Curves to about 25%, loaded as a
  selection, limits how far the fill departs from the photo [0h8lwK-shOY 01:03]. Photoshop warns
  that no pixels are more than 50% selected, and the fill still runs [01:34].

## Steve Patterson: extending an image (S-03awqbtqs, 2023)

Photoshop trainer, Photoshop Essentials. Kept despite its age: the overlap and empty-prompt rules do
not depend on the model.

- **Overlap.** Include some of the image in the selection, or a seam shows where new and original
  meet [01:40].
- **Empty prompt** when extending [02:10].
- **Judge by light.** The good result continues the sunset and the long shadows; the new content
  stays on its own layer [03:14].
- **Transparent, not white.** Unlock the Background so the new canvas is transparent; a white canvas
  reads as part of the image [08:09].

## Unmesh Dinda: tiled fills (CyJgXBJVHkU)

Photoshop educator and maker of the PiXimperfect Compositing panel he demonstrates.

- **The problem.** A large generated area is visibly lower resolution than the photo [00:00].
- **Expand without generating first.** Crop tool with a transparent fill, then fill the empty area
  [01:03].
- **Box size.** 500, 1000 or 2000 px boxes, filled one at a time: smaller is slower and can be
  sharper [02:08].
- **No object prompt per box.** A prompt such as a cloud would appear "in every single box" [09:47].

## Terry White: what the model changes on its own (MsX4_p_BbSQ, seXzZzjG9HI)

Principal Director and Photography Evangelist at Adobe.

- Partner models usually return one variation; Adobe's own return three [MsX4_p_BbSQ 01:40].
- Details the prompt did not name (purse, sunglasses) came and went between runs: name them
  [MsX4_p_BbSQ 04:24].
- Distraction removal swapped a car he had not selected [seXzZzjG9HI 14:11]. Check what must not
  change.
- An extended shadow got cut off: make the selection bigger than you think [seXzZzjG9HI 27:15].

## Lindsay Marsh: whole subject for partner models (ZCTPo7M8Eyg)

Graphic design teacher.

- With partner models, selecting the whole person and asking for the change beat a small hand-drawn
  selection [10:27].

## PHLEARN: references (7zE6s7_nmIs) and Aaron Nace (nmvewzc6MG4)

PHLEARN instructor (Photoshop and photography training company); Aaron Nace, PHLEARN.

- **Swap beats Place** for a shirt; an object reference takes no prompt [7zE6s7_nmIs 03:14].
- **Pre-cut the reference.** A bracelet photo with a hand brought the hand along. He opened the
  photo, selected the bracelet alone with Object Selection and saved it [11:25, 12:29]; the next
  generation placed only the bracelet [13:01].
- **The Remove tool spends no generative credits** [nmvewzc6MG4 00:13].

## Adobe Live: masks, angles, rotation (jXpi5NJANXg, 4YyrlB12m5I, I-rtmS9Xxa0)

- **Object masks** (presenter not named): a global prompt changed the bumper slightly [jXpi5NJANXg
  02:04]; with the car masked, "this only affected the object inside the mask" [02:35].
- **Ted Chin** (surreal composite artist) relays another instructor's tip: perfect square selections
  give better control with partner models [4YyrlB12m5I 17:34]. For an angle he cannot describe, he
  turns the object with Rotate Object, then uses that render as the reference for a fill [28:26].
- **Jack Faulkner** (graphic designer and visual artist): Rotate Object works best on non-human
  objects; faces may warp [I-rtmS9Xxa0 11:36].

## Marty, Photoshop Arthouse: angle by instruction (ZbT6oMMITMg)

Tutorial channel, no credential stated.

- Select all, then "rotate the angle of the car so the rear is 3/4 visible" [03:24].
- A camera change carries a keep instruction: "Place the car in the same position on the floor"
  [03:57].

## Adobe Learn, written tutorial (2026-08-07): no memory, annotations

Jesús Ramirez on Photoshop on the web.

- **No memory between generations.** Each prompt refers to the original image, not the last result.
  Re-prompting without a new selection brings the original back.
- **Annotation trick.** Write notes and arrows in red on a new layer, select all, prompt "Follow the
  red prompts in the image", and ask to remove the red annotations, or they stay in the output.
- Adobe's Markup tool (27.10) turns the same idea into a feature of Prompt to edit.

## Disagreements and the deciding condition

- **Generous or tight selection?** Ramirez, Kost, Marsh, Williams and White select generously:
  partner models see only the selection, and shadows need room. The measured job says tight: the
  model fills the mask. Decide by separating the two inputs. `capture`'s margin carries context; the
  mask is the footprint of the result, shadows and room for a new shape included. Never widen the
  mask to give context.
- **Photoshop's own tool or a Scenario model?** Photoshop wins small cleanups (the Remove tool is
  free of credits), protects outside the selection natively, and its own fill model reads the whole
  image and returns three variations. Scenario wins when the agent runs unattended, when the edit
  needs several references or a trained style, or when the output must exceed what Photoshop's fill
  returns. Adobe documents no script call for Generative Fill and the toolkit has none. A forum
  reports an undocumented batchPlay descriptor (not tested), and Adobe's generative AI guidelines
  may cover automated use, so the toolkit does not reach for it.
- **All sides at once or one side at a time?** Patterson selects both sides in one pass [S-03awqbtqs
  01:40]; Ramirez does one side at a time [fR0CI04XBpM 09:16]. Decide by output size: one pass when
  the whole new area fits the member's output at the photo's pixel density, else one side per pass,
  or tiles.
- **Empty prompt, description, or instruction?** Removal and extension run with an empty prompt
  (Patterson, Williams). Adobe's own model wants a description; instruction models want the change
  and the keep (Kost). Decide by the member: inpaint members fill from context with an empty or
  descriptive prompt; instruction-edit members need both clauses. Tiles never get an object.
- **Gray selection or a strength parameter?** Williams' 25% gray selection works in Photoshop's own
  fill. A Scenario member with a strength field takes a binary mask and the strength; the gray
  selection then only softens the layer mask. Gray masks with Scenario members are not tested.
- **Square or shaped selection?** Ramirez and Chin square the selection for partner models; Marsh
  selects the whole subject. With `capture`, the box the model sees comes from the margin and can be
  squared, while the mask keeps the shape.
- **Big selection or resolution?** Kost: a large selection comes back at 1K and needs upsampling.
  Decide with the resolution gate: result width at least the capture box width, else tiles, a
  larger-output member, or an upscale of the take.

## What reads as generated

- A softness cliff or a grain change at the edge (Smith, Dinda).
- The new object grown past what was meant (measured).
- Eyes: pupil size, catchlight (measured).
- An object repeated in every tile (Dinda).
- Something outside the brief changed: a car, a pose, a color (White, Ramirez, Smith).
- Light direction or shadows that stop at the edge (Patterson).
- A face warped after a rotation (Faulkner).

## Gaps in the sources

- Only the measured job quantifies how much a model changes outside the mask.
- Every expert works by hand in the GUI; none scripts the round trip.
- No source shows a prompted tile loop or a trained style inside a selection.
- No source tests gray selections with a model other than Photoshop's own.
- All demonstrations are on desktop Photoshop; the scripted round trip here ran on macOS only.
