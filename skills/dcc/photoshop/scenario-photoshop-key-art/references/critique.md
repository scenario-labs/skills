# Critique: judging key art, ads and thumbnails

Order of judgment:

1. The plate, before it goes into any canvas (stage 2).
2. The code gates on each canvas (`type_layers`, `check`, `export_under`, `deliverable`).
3. The display-size preview, then the full-size preview (stage 6).
4. The set: every channel and variant side by side (stage 9).

A stage passes only when every code gate passes and every visual item below was looked at and noted.
The code gates catch size, position, fonts and bytes. They never catch spelling against the brief, a
face that reads wrong, a subject cut by the crop, or a headline lost in a busy plate.

## 1. The plate at 100%

- No letters, logos, watermarks or fake interface anywhere. Generated lettering is replaced, never
  retouched into words.
- The subject matches the brief: face, expression, product, colors. Hands, eyes and edges hold up at
  100%. storezar looks at the face first and the eyes first [BtzVLw67Ggs 02:07]; Dill Toma checks
  the eyes before anything else [3eURUBIrhRY 06:02].
- One light direction across the plate and every pasted element. A pasted face lit from the other
  side goes to scenario-photoshop-compositing before any type.
- Room for the copy: a quiet area where the layout puts the headline.
- Resolution: the plate scale is 1 or less on every planned canvas (procedures P2). Ira Ostrovska
  upscales a generated image "a little bit in higher resolution than your render" before compositing
  [Uvq85gcMSE0 03:29].
- Realism or punch is the user's call per channel (see expert-notes, Disagreements). Small flaws are
  invisible at display size (Vince Opra [uM8jVa_wJU4 03:56]); a wrong face is not.

## 2. Code gates

| Gate                        | Pass                                | Fails on                                    |
| --------------------------- | ----------------------------------- | ------------------------------------------- |
| Plate scale                 | 1 or less on every canvas           | a plate enlarged into a large canvas        |
| `IO.place` bounds           | equal `cover_bounds` within 1 px    | a placement or transform error              |
| Subject box                 | inside the canvas, off unsafe zones | a crop that cuts the subject                |
| `type_layers` `fits`        | true for every item                 | a box too small at 4 pt, after 6 tries      |
| `font_used == font_asked`   | true for every item                 | a missing font, swapped for Myriad Pro      |
| `check(preset)["problems"]` | `[]`                                | off canvas, under an unsafe zone, too small |
| `export_under` `fits`       | true, at the channel's size         | a cap below what quality 0 reaches          |
| `A.deliverable(profile)`    | only the expected findings          | wrong mode, bit depth, profile, layer names |

`check` reads only visible, live text layers. Text in a smart object, rasterized text and text
painted into the plate pass it unread: look for them in the preview.

## 3. The display-size preview

Open the preview made at the channel's display width (procedures P6) and judge it at that size,
never zoomed in. storezar zooms out to "about the size of a phone thumbnail" and holds a phone to
the screen [BtzVLw67Ggs 25:20].

- **Read order:** the subject reads first, the headline second, everything else after. Vince Opra's
  checklist closes on contrast and few colors [uM8jVa_wJU4 15:32].
- **Every line legible:** no line under 12 px at display width (`check` flags it); thin strokes and
  script fonts need more.
- **Contrast:** the copy separates from the plate. A busy area behind small copy gets a stroke, a
  shadow or a dark band (procedures P5). storezar warns against "mega-contrast" and adds grain
  [BtzVLw67Ggs 25:51].
- **Faces:** expression readable at that size. Badis Designs: "the closer the face is to the camera,
  the better" [TuF4RMJtq-4 00:32].
- **Clear of the interface:** nothing important under the guide zones (the duration badge, a story's
  bars), the subject included.
- **Spelling:** every word against the copy sheet, letter by letter. Prices, dates and names twice.

Then the full-size preview: edges of the type, halos from effects, banding in gradients, seams of
pasted pieces.

## 4. The set

Read every channel's display preview in one contact sheet (`R.sheet`).

- The same subject, copy and colors across the set. A size set changes framing, never the message.
- Each crop keeps the subject whole and the focus where the layout wants it.
- Each variant differs from the master in its one intended change. Dill Toma's two looks for two
  audiences differ most in their lighting [3eURUBIrhRY 01:05]; Badis Designs tests a version with
  text and one without [TuF4RMJtq-4 06:30].
- Each export is under its cap, at the channel's size, with its JPEG quality in the report.

## Report

Per channel: the canvas size, the export path, bytes and JPEG quality, the `check` result, fonts
used, the expected `deliverable` findings, and what was judged by eye only.
