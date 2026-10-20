# Expert notes: upscale and restore (the depth behind SKILL.md)

Each expert section is one person's method, with the timestamps it rests on. Timestamps are the
start of the caption chunk that holds the words. The videos name the models in Photoshop's picker
and in other apps; this file uses capability words instead:

- **Faithful upscaler:** a model built to keep real photographs real, with face recovery.
- **Creative upscaler:** a model with a Creativity setting that adds detail and reinterprets.
- **Adobe's own upscale model:** the default in Photoshop's Generative Upscale picker.
- **Instruction restore:** a general image-edit model given a restore or colorize prompt.

No rule here depends on one model: the picker and the Scenario catalog both change.

## Measured: two real Scenario 2x upscales against a rebuilt baseline

Setup: a detail-dense 512 px photo (an owl close-up), two Scenario upscale members at factor 2, plus
copies with a known defect each, made with Pillow. Figures are the worst-channel mean difference to
the scripted baseline that `build_stack` makes (likely Preserve Details 2.0).

| Candidate                      | At a 256 px long side | At source size | Detail vs baseline |
| ------------------------------ | --------------------- | -------------- | ------------------ |
| Real upscale A                 | 4.9                   | 9.5            | 0.95               |
| Real upscale B                 | 4.9                   | 9.4            | 1.00               |
| Bicubic                        | 0.5                   | 3.3            | 0.65               |
| Nearest neighbor               | 0.6                   | 2.5            | 0.81               |
| Shifted 8 px at 2x             | 16.8                  | 20.2           | 0.66               |
| Color cast (+45 red, -45 blue) | 38.5                  | 38.6           | 0.57               |
| Blurred 2 px at source         | 7.1                   | 11.6           | 0.08               |

- **Generative upscalers redraw texture.** At source size, each real upscale differs from the source
  by 9.4 and 9.5, three times a bicubic upscale (3.3) and near a 2 px blur (11.6), and the two
  differ from each other by 8.6. Neither shows a shift or a cast: the best integer offset is 0,0 and
  the mean colors agree within 0.5.
- **So identity is judged small.** At a 256 px long side the redrawn texture weighs little, while a
  shift, a cast or reframing still shows. `MATCH_SIZE = 256`, `MATCH_MEAN = 6.0`.
- **Detail is relative.** `detail_vs_base` separates a smoothed output (0.08) from real upscales
  (0.95 to 1.00). It cannot tell new detail from invented detail: only the crops can.
- One image and two members: authoring-time numbers. A smoother subject scores lower everywhere.

## Measured: one real Scenario restore and colorize

Setup: the same owl made sepia, blurred, low in contrast, with 14 scratches and 220 spots, then one
Scenario instruction-edit job (1024 px, low quality) asked to restore and colorize it.

- **It came back aligned.** The red/cyan overlay shows no fringe.
- **A plain difference cannot tell.** The colorize alone gives a mean of 29 at 256 px.
- **The tone-blind structure score can** (`G.structure`: 256 px, desaturate, median, Equalize, High
  Pass, mean difference inside a 6% inset):

| Candidate vs the damaged original | Score        |
| --------------------------------- | ------------ |
| Restore as returned               | 11.3         |
| Restore shifted 3 px              | 14.0         |
| Restore after a bad Auto-Align    | 15.1 to 29.6 |
| Copy drifted 3% and 8 px          | 22.7         |
| Drifted copy after Auto-Align     | 11.1 to 16.7 |

- **Auto-Align misreads a damaged original.** On the aligned restore it moved the layer 2.5 to 17 px
  over three runs, three different answers, and worsened the score every time. On the drifted copy
  it fixed most of the drift, leaving 2 to 3 px. Hence `U.align` keeps a result only on a drop of
  10% or more.
- **Auto-Align by script has traps:** the projection must be the charID `Auto` (the string ID `auto`
  aligns nothing); on a smart object it does nothing without an error; a Background it touches
  becomes "Layer 0"; afterwards both layers stay targeted, so a DOM duplicate copies both.
- **Stepping History back does not restore visibility,** with Photoshop's default History options.

## Measured: Image Size by script

- `ImgS` with the `Intr` key accepts any interpolation name without an error, even "notARealMethod".
  A typo silently runs another method.
- `deepUpscale` gave output distinct from bicubic, nearest neighbor and the made-up name. It is
  likely Preserve Details 2.0; not proven.

## Unmesh Dinda: restore and colorize without changing the photo (mSgSaisb6Kg, G5yuLhm0SdM, knYusnpB9zI)

Photoshop educator, PiXimperfect. Three 2025 and 2026 tutorials on the same goal: keep "the soul of
the photo" (Dinda [mSgSaisb6Kg 00:00]).

- **Ratio first.** Many generators have fixed ratios; an input in between "will shift a bit more
  likely than not" (Dinda [mSgSaisb6Kg 00:33]). He crops to 2:3 and picks 2:3 in the generator
  (Dinda [mSgSaisb6Kg 02:44]). For a colorize he extends to a square with black under the gap,
  because a square shifted less over "hundreds of images" (Dinda [G5yuLhm0SdM 05:58]; [G5yuLhm0SdM
  06:31]).
- **Prompt.** "Restore this photo to look as if it were taken today with high resolution modern
  digital camera", plus "in color" (Dinda [mSgSaisb6Kg 02:44]); a keep-clause, "without changing
  anything about the image. Just repair it, clean it and sharpen it" (Dinda [knYusnpB9zI 00:33]).
  Optional region hints for a colorize: "green chalkboard, black suit, dark blue vest, red tie,
  natural skin tone" (Dinda [G5yuLhm0SdM 07:35]). He asks for the highest resolution (Dinda
  [mSgSaisb6Kg 03:48]).
- **Two takes, pick the natural one.** "The second one is more cleaner, but the first one is more
  natural" (Dinda [mSgSaisb6Kg 04:22]); he keeps the first (Dinda [mSgSaisb6Kg 04:55]).
- **Align in Difference on the eyes.** Blend mode Difference, nudge with the arrow keys until the
  eyes are aligned; arms may stay off (Dinda [mSgSaisb6Kg 04:55]; [mSgSaisb6Kg 05:28]). "We just
  have to match the face. Clothes and stuff, they move a little and it's absolutely fine" (Dinda
  [knYusnpB9zI 01:06]). Liquify with Show Backdrop at about 74% opacity reshapes the face onto the
  original (Dinda [knYusnpB9zI 01:36]; [knYusnpB9zI 02:06]).
- **Auto-Align on raster layers,** Projection Automatic (Dinda [mSgSaisb6Kg 08:12]). Measured above:
  keep it only on a gain.
- **Lock with Color.** "If you want the exact same image without any of the generative AI stuff,
  simply change the blend mode from normal to color... This remains the exact same image" (Dinda
  [G5yuLhm0SdM 08:08]).
- **Faithful face, generated color.** Photoshop's Photo Restoration filter "does the face good, but
  not the rest of the body" (Dinda [knYusnpB9zI 05:17]). He paints that face over the generative
  restore through a negative mask, clips a Color copy of the restore above it, and puts Curves below
  the Color layers (Dinda [knYusnpB9zI 06:52]; [knYusnpB9zI 07:26]; [knYusnpB9zI 07:58]).
- **Finish.** Downloads come over-sharpened: blur 1 px, then 0.8; Stamp Visible, Camera Raw
  sharpening, grain 20 then 12 (Dinda [knYusnpB9zI 08:29]; [knYusnpB9zI 09:02]; [knYusnpB9zI
  09:35]). "AI by itself is right now not enough" (Dinda [knYusnpB9zI 09:35]).
- **Colorize fixes.** Skin through a Solid Color fill in Multiply, masked, opacity 60 then 72; color
  leaks painted back with sampled color (Dinda [G5yuLhm0SdM 04:22]; [G5yuLhm0SdM 08:41];
  [G5yuLhm0SdM 09:14]). Crop back by Cmd-clicking the original's thumbnail, then the Crop tool
  (Dinda [G5yuLhm0SdM 10:55]). Switch Grayscale to RGB first (Dinda [G5yuLhm0SdM 12:32]).
- **Cost.** A bad generation "counts against your limits" (Dinda [mSgSaisb6Kg 08:44]).

## Unmesh Dinda: what upscalers break (p3JcJ99woGU)

Same educator; the video carries sponsored links to the upscaler it favors, so read its ranking with
care and its failure cases as evidence.

- **Round-trip test:** downscale a high-resolution photo to 600 px wide, upscale it, compare with
  the original (Dinda [p3JcJ99woGU 00:33]).
- **Products:** "for product photography solely, I wouldn't recommend any of the AI upscalers"
  (Dinda [p3JcJ99woGU 08:46]). Lettering lost letters, an emboss appeared, a honeycomb gained shapes
  (Dinda [p3JcJ99woGU 09:18]; [p3JcJ99woGU 09:51]).
- **Plain areas and gradients:** "blotchy banding" (Dinda [p3JcJ99woGU 11:30]).
- **Ornament:** statues gained "monster details"; a clock's design merged into noise (Dinda
  [p3JcJ99woGU 12:03]).

## Colin Smith: baselines, partner upscalers, rejoining a layer (UorIb_rGZuc, 9YS0m69uhIk, iy0IxTpT4OY)

Photoshop trainer, photoshopCAFE.

- **The "Original" is weak.** Generative Upscale stacks an "original" (Smith [UorIb_rGZuc 02:12]).
  He rebuilt one with Image Size, Preserve Details 2.0, and found it sharper: "that's not a very
  good version of the original" (Smith [UorIb_rGZuc 03:54]; [UorIb_rGZuc 05:00]).
- **Ranking at the same spot:** upscale first, Preserve Details second, Super Zoom third, the
  "original" last (Smith [UorIb_rGZuc 07:43]).
- **Where upscales go wrong:** smooth areas turn "a little cartoony" (Smith [UorIb_rGZuc 03:21]);
  acne bumps removed (Smith [UorIb_rGZuc 11:00]); the face altered around the eyes (Smith
  [UorIb_rGZuc 11:33]); "less of a realistic result" (Smith [UorIb_rGZuc 12:06]).
- **Mix by mask:** Preserve Details on the wood, the upscale on the face (Smith [UorIb_rGZuc
  08:16]); "just mask out those different areas. And you can combine these" (Smith [UorIb_rGZuc
  12:40]).
- **Creative partner model:** one keeps it true, the other "tries to make it look as beautiful as
  possible", creativity default 5 (Smith [9YS0m69uhIk 05:20]). Faces come out smooth (Smith
  [9YS0m69uhIk 06:24]); at minimum creativity it opened the subject's eyes and turned her "into a
  different person" (Smith [9YS0m69uhIk 06:24]; [9YS0m69uhIk 06:58]). Better on landscapes (Smith
  [9YS0m69uhIk 08:36]). Partner models spend premium credits (Smith [9YS0m69uhIk 02:09]).
- **Rejoin a soft layer:** Harmonize loses resolution (Smith [iy0IxTpT4OY 02:09]). He upscales 2x
  into a new tab, drags the layer back, scales it to 50%, aligns in Difference until it reads black,
  and reuses the Harmonize mask (Smith [iy0IxTpT4OY 02:43]; [iy0IxTpT4OY 03:15]; [iy0IxTpT4OY
  03:47]; [iy0IxTpT4OY 04:20]).

## Julieanne Kost: models as layers, faces by mask (a2OIpxbuzKE)

Adobe Principal Digital Imaging Evangelist.

- Generative Upscale opens a new document: the original resized, and the generated layer (Kost
  [a2OIpxbuzKE 01:09]). Each model has a maximum; past it, Upscale is grayed out (Kost [a2OIpxbuzKE
  00:34]).
- She compares models and creativity values as layers (Kost [a2OIpxbuzKE 02:16]). A creative setting
  is "a bit too creative with the faces" but good on clothing (Kost [a2OIpxbuzKE 02:49]).
- Layer > Layer Mask > Hide All, then paint the faithful faces in with white (Kost [a2OIpxbuzKE
  03:23]).

## Jesús Ramirez: judge at 100%, faithful versus creative (a7E4HlrAc3w)

Photoshop Training Channel, presenting on Adobe's channel.

- "Always work at 100% so you can accurately judge the details and sharpness. Any other zoom level
  can be misleading" (Ramirez [a7E4HlrAc3w 01:05]).
- The faithful model is for photographs, to "preserve natural detail rather than invent new ones";
  face recovery is "designed to restore, not change expressions, though minor variations can occur"
  (Ramirez [a7E4HlrAc3w 02:06]).
- Creativity: low stays faithful, high reinterprets (Ramirez [a7E4HlrAc3w 03:38]). The creative
  model "isn't meant to perfectly preserve original realism" (Ramirez [a7E4HlrAc3w 04:42]).

## Blue Lightning: filter restore, then a creativity sweep (cvF6BZArpYc)

Solo creator; name not stated.

- Photo Restoration neural filter to a new layer, small slider moves (Blue Lightning [cvF6BZArpYc
  00:33]). Color fixes by eyedropper and brush; "This is where a standard photo restoration would
  typically end, true to the original" (Blue Lightning [cvF6BZArpYc 03:52]).
- Past that, creativity "starts filling in details from pure imagination. And yes, that includes
  faces too" (Blue Lightning [cvF6BZArpYc 05:00]). Faces drift from the middle settings (Blue
  Lightning [cvF6BZArpYc 06:40]).
- Mix by mask: clothing from one setting, faces from another; an invented extra figure erased (Blue
  Lightning [cvF6BZArpYc 06:40]; [cvF6BZArpYc 07:14]).

## Marty Geller: whole-image restore, saturation, filters (jIvcJtPsJss, pNODFCbH9n8)

Photoshop educator, Photoshop Arthouse.

- Select All, then a restore and colorize prompt; he picks the model for keeping faces consistent
  with the original (Geller [jIvcJtPsJss 00:35]).
- Vibrance before Saturation; Saturation to -33 so skin stops looking garish (Geller [jIvcJtPsJss
  02:18]; [jIvcJtPsJss 02:56]).
- Partner upscale models are premium and cost more credits (Geller [pNODFCbH9n8 01:47]). Upscale,
  then Filter > AI Sharpen (Geller [pNODFCbH9n8 02:56]).

## Jafar Alwash: small moves after a filter restore (WwRbCKao7S4)

Photographer and video creator, partner creator on Adobe's channel.

- Photo Restoration sliders: scratch reduction, enhance face, photo enhancement (Alwash [WwRbCKao7S4
  00:33]). Saturation up a little "so it doesn't look too unnatural" (Alwash [WwRbCKao7S4 01:35]).
- Yellows toward orange for faces: "Small adjustments make a big difference" (Alwash [WwRbCKao7S4
  02:08]).

## Andy Hutchinson: source size decides (XNCimyJ8aQk)

Photographer and owner of a boutique design agency; the video tests a third-party plugin.

- The plugin shows the cost before each run (Hutchinson [XNCimyJ8aQk 03:58]) and lands the result as
  a smart object above the background (Hutchinson [XNCimyJ8aQk 07:18]).
- Round-trip test from a 300 px copy of a large original (Hutchinson [XNCimyJ8aQk 08:59]): faces
  deformed in both upscalers, "neither of them brilliant"; a landscape from 1000 px banded in the
  sky (Hutchinson [XNCimyJ8aQk 12:21]). From a 1000 px source, faces were "sensational" (Hutchinson
  [XNCimyJ8aQk 12:56]). One model did better at a larger upscale factor (Hutchinson [XNCimyJ8aQk
  08:25]).

## Lindsay Marsh: smoothed skin (ZCTPo7M8Eyg)

Graphic design teacher.

- An upscale smoothed skin: "AI models is they love to smooth out things they're not sure of" (Marsh
  [ZCTPo7M8Eyg 04:24]). She adds Camera Raw Texture, Clarity and Sharpening on the upscaled layer
  (Marsh [ZCTPo7M8Eyg 04:57]).
- Round trip on a bird she shrank on purpose, compared with the 4000 px original's feathers (Marsh
  [ZCTPo7M8Eyg 05:31]; [ZCTPo7M8Eyg 07:11]).

## Glyn Dewis: credits and timing (LlmQJO03tTY)

Photographer and retoucher.

- A partner upscale costs 10 or 20 credits a run depending on output size (Dewis [LlmQJO03tTY
  07:16]).
- In Lightroom, Generative Upscale writes a separate file, and Adobe recommends it "closer to the
  end of your edit" (Dewis [LlmQJO03tTY 06:45]).

## Chandru Bharathy: upscale, then High Pass (SER_4Rqn7P4)

Wedding and portrait photographer. Auto-captions are garbled; only the steps shown are used.

- A second pass to "bring back the details and sharpen it" (Bharathy [SER_4Rqn7P4 08:57]).
- Generative Upscale 2x, then High Pass in Linear Light, grouped for a before and after (Bharathy
  [SER_4Rqn7P4 21:55]; [SER_4Rqn7P4 24:07]).

## Disagreements and the deciding condition

- **Upscale everything, or not products.** Most videos upscale whole frames; Dinda advises against
  generative upscalers for product photos (Dinda [p3JcJ99woGU 08:46]). Decider: content with exact
  structure (lettering, logos, product geometry, ornament) keeps the baseline by mask.
- **True or beautiful.** Smith and Ramirez describe a faithful and a creative route (Smith
  [9YS0m69uhIk 05:20]; Ramirez [a7E4HlrAc3w 03:38]). Decider: people the user knows get the faithful
  route; landscapes and textures may take the creative one.
- **Difference for alignment.** Dinda and Smith align in Difference (Dinda [mSgSaisb6Kg 04:55];
  Smith [iy0IxTpT4OY 03:47]). Decider: Difference works when tones match; after a colorize or a
  relight, use the structure score and the overlay.
- **Auto-Align.** Dinda runs it (Dinda [mSgSaisb6Kg 08:12]); measured, it worsened an aligned
  restore every time. Decider: run it on visible drift, keep it on a measured gain.
- **Filter restore or generative restore.** The filter keeps the face but leaves the rest (Dinda
  [knYusnpB9zI 05:17]; Blue Lightning [cvF6BZArpYc 03:52]); a generative restore fixes everything
  and may change the face (Dinda [knYusnpB9zI 00:00]). Decider: combine them by mask, face from the
  faithful source, color from the restore.
- **Upscale early or late.** Adobe recommends late (Dewis [LlmQJO03tTY 06:45]); Smith upscales a
  layer mid-edit (Smith [iy0IxTpT4OY 02:43]). Decider: upscale after edits that change pixels,
  except a soft layer that has to match the rest now.
- **Restore at high resolution or upscale after.** Dinda asks the generator for its highest
  resolution (Dinda [mSgSaisb6Kg 03:48]) and leaves upscaling optional (Dinda [knYusnpB9zI 09:35]).
  Decider: restore at the member's native size, check alignment, then upscale the approved restore.

## What reads as generated

- Plastic skin, missing pores, removed blemishes the person has.
- Cartoon-smooth planes on cheeks, walls and fabric.
- Letters dropped or reshaped; new embossing, patterns or ornament.
- Blotchy banding on skies and gradients.
- Eyes opened, gaze changed, expression softened.
- An extra figure, object or jewelry.
- Uniform sharpness and no grain across a photo that had depth of field and film grain.

## Gaps in the sources

- No expert measures identity with numbers; the 256 px rule and its threshold come from the live
  calibration above, on one image.
- No source names Scenario members; the skill routes by capability.
- No source covers Windows, a 16-bit master, or a print color mode.
- Historically accurate color is not addressed beyond Dinda's region hints (Dinda [G5yuLhm0SdM
  07:35]).
- The 2026 status of the Neural Filters is unclear in the sources and not tested here.
