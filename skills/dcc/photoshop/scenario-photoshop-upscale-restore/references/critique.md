# Critique: judging an upscale or a restore

Order of judgment:

1. The input file, before any paid run.
2. The code gates on each candidate (`build_stack` flags, or `place_result` and `G.structure`).
3. The crop grid at 100%, row by row, region type by region type.
4. For a restore: alignment on the overlay, then likeness against the original at 100%.
5. Locks and region blends at their edges, then the whole canvas for color.

A stage passes only when every code gate passes and every visual item that applies has been looked
at and noted. The numbers catch shifts, color casts, reframing, blur and wrong sizes. They never
catch a changed face, wrong letters or invented ornament: a real upscale that redrew the texture
still matched at 256 px. Every Photoshop expert in [sources.md](sources.md) judges at 100%: "Any
other zoom level can be misleading" (Ramirez [a7E4HlrAc3w 01:05]).

## 1. Before the run: the input

- `input.png` holds the whole subject. The padding is plain and outside the subject.
- `prep["ratio"]` is a ratio the member accepts; `prep["output"]` is within its input cap.
- The brief names what may change and what must not: faces, lettering, logos, the frame.
- For a colorize, the source mode is known. A Grayscale master needs RGB before any color shows.
- Source size: from a 300 px source, faces deformed in both upscalers one expert tested; from about
  1000 px, the same model was "sensational" (Hutchinson [XNCimyJ8aQk 12:21]; [XNCimyJ8aQk 12:56]).
  Set expectations before quoting.

## 2. Code gates

| Gate                     | Pass                                    | Fails on                                           |
| ------------------------ | --------------------------------------- | -------------------------------------------------- |
| `aspect_ok`              | the output's ratio matches the source's | reframing, a crop, padding left on the result      |
| `size_ok`                | output = source x factor, within 1 px   | another factor (review is still possible)          |
| `match["matches"]`       | worst-channel mean under 6 at 256 px    | shift, color cast, reframing                       |
| `detail_vs_base`         | near 1 or above                         | a smoothed or blurred output (blurred: 0.08)       |
| `texture_change`         | no threshold                            | information: high means the texture was redrawn    |
| `G.structure`, per take  | lowest of the takes; drops after a fix  | a shift or scale change (relative only)            |
| `U.align` `kept`         | true only on a drop of 10% or more      | the toolkit steps back on its own                  |
| `U.align` `uncovered`    | all zero, or cropped back               | a bare strip along an edge                         |
| `lock` `after`           | under `before`                          | the lock hit the wrong layer, or layers above it   |
| History                  | one new state per placement or lock     | a stray edit on the user's document                |
| `A.deliverable(profile)` | returns `[]`                            | size, mode, profile, hidden layers outside "Takes" |

Thresholds are authoring-time, from one 512 px photo and two real upscales. A smoother subject
scores lower everywhere. A candidate that fails `aspect_ok` or `match` is not judged further.

## 3. Upscale: every row of the crop grid, at 100%

Read each region type in every row, against the baseline row at the bottom.

- **Eyes and faces:** same eye shape, gaze, catchlights and expression. A face can be "altered a
  little bit" around the eyes (Smith [UorIb_rGZuc 11:33]), or eyes opened that were looking down
  (Smith [9YS0m69uhIk 06:24]). Any change of likeness rejects the take for that face.
- **Skin:** pores and fine texture survive. Upscalers "love to smooth out things they're not sure
  of" (Marsh [ZCTPo7M8Eyg 04:24]); one removed acne bumps the photo had (Smith [UorIb_rGZuc 11:00]).
  Smooth reads as plastic.
- **Smooth areas:** no cartoon look on cheeks, walls and fabric planes (Smith [UorIb_rGZuc 03:21]).
- **Lettering, labels, logos:** every letter as in the source. One upscale dropped two letters of a
  partly hidden "Made in Japan" (Dinda [p3JcJ99woGU 09:18]).
- **Ornament, engraving, statues:** no new emboss, honeycomb shapes or "monster details" (Dinda
  [p3JcJ99woGU 09:51]; [p3JcJ99woGU 12:03]).
- **Flat areas, gradients, sky:** no blotchy banding (Dinda [p3JcJ99woGU 11:30]; Hutchinson
  [XNCimyJ8aQk 12:21]).
- **Hair, fur, feathers, foliage:** detail is new but plausible, not a repeating pattern.
- **Edges and thin lines:** no halos, no doubled edges, no stair-stepping.
- **Over-sharpening:** crunchy edges and white halos mean the result needs a slight blur before any
  sharpening (Dinda [knYusnpB9zI 08:29]).

## 4. Restore and colorize: alignment and likeness

- **Overlay first.** `R.overlay(out, "Background", take)`: gray where aligned. Red and cyan fringes
  on the eyes mean a shift; fringes growing toward the edges mean a scale change. Plain Difference
  is useless after a colorize: the measured aligned restore scored a mean of 29.
- **Eyes are the anchor.** Experts align on the eyes and tolerate small movement in arms and clothes
  (Dinda [mSgSaisb6Kg 05:28]; [knYusnpB9zI 01:06]).
- **Same person.** "Not even the same person anymore" is the failure Dinda opens with (Dinda
  [knYusnpB9zI 00:00]). Toggle the take against the original at 100%: eye shape, nose, mouth,
  hairline, age.
- **Nothing invented.** No extra figure (Blue Lightning [cvF6BZArpYc 07:14]), no new jewelry, text
  or background objects. In one creativity sweep, faces changed from the middle settings up (Blue
  Lightning [cvF6BZArpYc 06:40]).
- **Damage gone, character kept.** Scratches, spots and tears are gone; grain, period clothing and
  the photo's softness are kept. Adobe's faithful route warns that minor variations can occur
  (Ramirez [a7E4HlrAc3w 02:06]).
- **Frame:** nothing cropped from the source's edges; `uncovered` all zero after an align.

## 5. Color after a colorize

- Skin falls in a natural range: not orange, not gray. Shifting Yellows toward orange fixes faces
  (Alwash [WwRbCKao7S4 02:08]); pale skin takes a masked Multiply fill (Dinda [G5yuLhm0SdM 08:41]).
- No color leaks: lipstick onto skin and teeth, hair into foliage (Dinda [G5yuLhm0SdM 04:22]; Blue
  Lightning [cvF6BZArpYc 03:52]).
- Saturation reads as a photograph, not a poster: "Small adjustments make a big difference" (Alwash
  [WwRbCKao7S4 02:08]). Garish skin gets Saturation down, around -33 (Geller [jIvcJtPsJss 02:56]).
- In Color mode, the original's lightness is kept exactly: the composite's tones match the original.

## 6. Blends and the canvas

- Every `region_blend` edge at 100%: no step in sharpness, grain or color across it.
- Grain is even across regions mixed from different takes. Restores often need grain added back:
  Dinda adds 20, then lowers it to 12 (Dinda [knYusnpB9zI 09:35]).
- The whole canvas, fit to screen: one light, one color temperature, no patch that reads newer than
  the rest.

## 7. Choosing between candidates

- A candidate that changes identity loses, whatever its detail score.
- Between two faithful candidates, prefer the one with fewer invented details at 100%, then the
  higher `detail_vs_base`.
- When each wins somewhere, mix them by region (P4) instead of choosing one.
- When no candidate beats the baseline on a region, the baseline stays there. A cleaner upscale can
  still give "less of a realistic result" (Smith [UorIb_rGZuc 12:06]).
- A creative candidate is fine for landscapes and textures (Smith [9YS0m69uhIk 08:36]), not for
  people the user knows.

## 8. Report

- The candidates, by layer name, with `match`, `texture_change` and `detail_vs_base`, or the restore
  takes with `G.structure`.
- What was chosen where, and why, in one line per region.
- The crop grid path and the overlay paths.
- What was not verified: Color mode, a padded restore end to end, Neural Filters, anything judged
  only at fit-to-screen.
