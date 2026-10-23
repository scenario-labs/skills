---
name: scenario-photoshop-upscale-restore
description: "Use when enlarging or repairing an image open in Photoshop with a Scenario model: upscaling a small photo, crop, scan or generated image for print or a larger display, comparing upscalers side by side against Photoshop's own enlargement (Image Size, Preserve Details 2.0) or Generative Upscale, mixing two upscales by mask, restoring a scratched, faded or torn old photo, colorizing a black-and-white photo while keeping it the same photo, or upscaling one changed layer to rejoin the image. Also when an upscale changes a face, smooths skin, invents texture, garbles product text or bands a sky, a restore or colorize comes back shifted or reframed, Auto-Align makes the alignment worse, Difference blend lights up everywhere after a colorize, a padded result lands offset, or an Image Size resample method seems ignored."
license: MIT
---

# Upscale and restore (Photoshop 2026)

Expert upscaling and restoration keep the photo the same photo. A generative upscaler redraws
texture across the frame, and a restore model redraws everything, sometimes a few pixels off. So
each result lands as a named layer over a rebuilt baseline, identity is measured at a small size,
texture is judged at 100%, and the original's tones or color are locked where they must not change.
Photoshop prepares the input and lands, aligns and blends the results; Scenario models supply the
pixels. If a sibling skill named here is missing from your available skills, ask the user to install
it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.

**REQUIRED BACKGROUND:** scenario-photoshop-expert (execution channel, round trip, gates).

**Status (2026-10-19):** every call in [`scripts/ps_upscale.py`](scripts/ps_upscale.py) is verified
live on Photoshop 27.11 (macOS). `test_upscale_live.py` (7 tests, two real Scenario 2x upscales as
fixtures) runs `prepare_input`, `build_stack`, `crops`, `lock` in Luminosity and Color modes,
`place_result` and the print resolution step. `test_restore_live.py` (5 tests, one real colorized
Scenario restore) runs `align`, `region_blend`, `G.structure` and `R.overlay`. Not tested:
`prepare_input(layer=)`, custom crop boxes, the shell commands, the changed-layer rejoin,
Photoshop's Generative Upscale and Neural Filters, Windows.

## Stance (the expert delta)

- **Rebuild the baseline; Photoshop's "Original" layer is not one.** Generative Upscale stacks an
  "Original" under its result; a Preserve Details 2.0 enlargement of the same source showed more
  detail: "that's not a very good version of the original" (Smith [UorIb_rGZuc 05:00]). A paid
  upscale has to beat the best free enlargement, which `build_stack` makes itself (by script, likely
  Preserve Details 2.0; not proven).
- **Judge identity small and texture at 100%, separately.** At full size, two real Scenario 2x
  upscales differed from the baseline by 9.4 and 9.5, near a 2 px blur (11.6), because the texture
  is redrawn. At a 256 px long side they scored 4.9, while an 8 px shift scored 16.8 and a color
  cast 38.5 [added: measured on the live fixture]. Texture is the other half: "Always work at 100%"
  (Ramirez [a7E4HlrAc3w 01:05]).
- **Faithful by default; creativity changes people.** The faithful route exists to "preserve natural
  detail rather than invent new ones" (Ramirez [a7E4HlrAc3w 02:06]). At minimum creativity a
  creative upscaler still turned a violinist "into a different person" (Smith [9YS0m69uhIk 06:58]),
  and more creativity invents details, faces included (Blue Lightning [cvF6BZArpYc 05:00]). Creative
  takes suit landscapes (Smith [9YS0m69uhIk 08:36]).
- **Mix candidates by region.** Kost compares models as layers, then paints the faces in from the
  faithful one through a Hide All mask (Kost [a2OIpxbuzKE 03:23]). Smith keeps Preserve Details on
  the violin's wood and the upscale on the face (Smith [UorIb_rGZuc 08:16]). `region_blend` turns a
  selection into one candidate's mask.
- **Know what a generative upscale breaks.** Product lettering lost letters and textures gained an
  emboss (Dinda [p3JcJ99woGU 09:18]; [p3JcJ99woGU 09:51]); plain areas and gradients banded (Dinda
  [p3JcJ99woGU 11:30]). "For product photography solely, I wouldn't recommend any of the AI
  upscalers" (Dinda [p3JcJ99woGU 08:46]). Skies band (Hutchinson [XNCimyJ8aQk 12:21]); skin gets
  smoothed (Marsh [ZCTPo7M8Eyg 04:24]). Keep the baseline on those regions.
- **A restore is a geometry problem first.** Off-ratio inputs to fixed-ratio models shift (Dinda
  [mSgSaisb6Kg 00:33]), so Dinda pads to a square first (Dinda [G5yuLhm0SdM 05:58]) and checks with
  Difference (Dinda [mSgSaisb6Kg 04:55]). A colorize defeats that check: the measured restore was
  aligned, yet its plain difference was 29 at 256 px. Pad to the model's ratio, place through the
  padding, then judge with the tone-blind `G.structure` and the red/cyan overlay.
- **Auto-Align only on a measured gain.** Dinda runs Auto-Align Layers on a rasterized copy (Dinda
  [mSgSaisb6Kg 08:12]). Measured: on an already aligned restore it moved the layer 2.5 to 17 px and
  made alignment worse 3 runs out of 3; on a copy drifted 3% and 8 px it fixed most of the drift.
  `U.align` keeps it only when the structure score drops 10%.
- **Lock what must not change with a blend mode.** Color mode keeps the original's tones and takes
  the restore's color: "This remains the exact same image" (Dinda [G5yuLhm0SdM 08:08]). The face
  must match; clothes may move a little (Dinda [knYusnpB9zI 01:06]). Luminosity mode does the
  reverse.

## Establish first

| Input                      | Changes                                         | Default when silent                               |
| -------------------------- | ----------------------------------------------- | ------------------------------------------------- |
| Job                        | upscale, restore, colorize, or a mix            | read from the brief                               |
| Fidelity                   | faithful or creative capability for `recommend` | faithful; creative only when asked                |
| Risky content              | faces, product text, ornament, sky, gradients   | look for them; crop boxes go there                |
| Factor or target size      | `build_stack(factor)`; the member's own factor  | print inches x 300 over source pixels; else 2x    |
| Scope                      | whole image, one layer, one region              | whole image                                       |
| Candidates                 | layers to compare                               | baseline first; two takes on a crop; the winner   |
| Source mode and depth      | a Grayscale master shows no color               | ask before Image > Mode > RGB Color on the master |
| Output document            | where results live                              | the stack document; the master is never resized   |
| Model ratios and input cap | `prepare_input(ratios=..., max_px=...)`         | from the member's schema (`scenario`)             |

## Workflow

`sys.path.insert(0, "<this skill>/scripts")`, then `import ps_upscale as U` (it puts the lead's
`scripts/` on the path) and `import ps_io as IO, ps_gates as G, ps_review as R, ps_audit as A`. Each
call is one `ps_run` job; after one raises or times out, recover as the lead's Quality gates say.
Code: [procedures](references/procedures.md).

**Scenario for Photoshop.** When the plugin's tools are connected and signed in, run this skill's
image, edit, upscale, expand and background-removal steps through them, as the lead's Live channel
maps them, gates included; other Scenario steps stay on hosted Scenario MCP. Not tested end to end.
There, an upscale lands as a new document (`new_document`) in sRGB 8-bit, even from an Adobe RGB
16-bit source (measured through the panel): use it for a single upscale; converting back does not
restore gamut or depth. A stack (stages 2 to 5), which the plugin cannot land, stays on hosted
Scenario MCP and the toolkit.

1. **Intake.** `A.doc_state()`: name, size, mode, bits, profile, layers. Note faces, text, gradients
   and damage. For a colorize on a Grayscale master, ask before switching it to RGB (Dinda
   [G5yuLhm0SdM 12:32]). GATE: document read by name; job, fidelity and factor written.
2. **Prepare the input.** `prep = U.prepare_input(OUT + "/input.png", ratios=[...], max_px=n)`:
   merged pixels (or one layer) as sRGB 8-bit, padded with black to the nearest ratio, the source
   placed exactly, capped with Bicubic Sharper. Keep `prep`. For an upscale, also export the
   riskiest region: `IO.export_region(OUT + "/risk.png", bounds=box)`, at a ratio the member takes.
   GATE: `prep["ratio"]` is one the member takes; `prep["output"]` fits its input cap.
3. **Free baseline first (upscales).** `st = U.build_stack([], 2)`: a new document at source x
   factor holding the scripted baseline alone (likely Preserve Details 2.0), then
   `U.crops(OUT + "/base", boxes=[face, text, sky])`. GATE: the baseline read at 100%; if it holds,
   deliver it and quote nothing.
4. **Candidates on the riskiest crop (paid).** `scenario` for the connection, `recommend`, the quote
   and the user's yes; `scenario-image-editing` for upscale tool models, run on `risk.png`. Two
   candidates, one yes: an upscale is judged by comparison. Price the crop and the full frame first;
   when they quote the same, run the candidates on the full frame (P2b). GATE: one beats the
   baseline's crop at 100% (`R.sheet` of both), else stop at the baseline.
5. **Winner on the full frame (paid).** Quote the winner on `prep["path"]`. In the stack,
   `L = U.place_result(p, "<label>, 2x scale", prep=prep, base=st["base"])`, then `U.crops` again.
   GATE: `L["match"]["matches"]` (mean under 6 at 256 px); its `G.texture` near the baseline's or
   above; every grid row read against [critique](references/critique.md). Stages 3 to 5 in this
   order are not tested; P2 tests a stack built with two candidates.
6. **Restore: land and align.** `scenario-image` runs the instruction restore or colorize, quoted,
   with a keep-clause such as "without changing anything about the image" (Dinda [knYusnpB9zI
   00:33]). `L = U.place_result(path, "Restore, take 1", prep=prep, base="Background")`: the source
   area covers the canvas; `L["match"]` is the 256 px difference, which a colorize fails by design.
   Then `G.structure(layer, "Background")` per take (lower is better, relative only) and
   `R.overlay(out, "Background", layer)`: gray where aligned, red and cyan fringes where not. On
   visible drift, `r = U.align(layer, "Background")`. GATE: no fringe on the eyes; `r["kept"]` read;
   `r["uncovered"]` all zero or cropped back.
7. **Lock and blend.** `U.lock(layer, "color", base="Background")` keeps the original's tones under
   a colorize; `"luminosity"` keeps the original's color under an upscale. For a region mix, select
   it (Select Subject, a marquee, or the user), then `U.region_blend(layer, feather=8)`. GATE:
   `after` under `before` (tested in both modes); inside the region the chosen take, outside it the
   layer below; the edge checked at 100%.
8. **Finish and deliver.** Downloads can come over-sharpened: blur 0.8 to 1 px, sharpen once, add
   grain (Dinda [knYusnpB9zI 08:29]; [knYusnpB9zI 09:35]). Tone down hot color with Vibrance or
   Saturation (Geller [jIvcJtPsJss 02:56]). For print: 300 ppi, no resampling (procedures P10).
   `A.deliverable(profile)` returns `[]`. GATE: no halo or crunch at 100%; the report names takes,
   gate numbers and what was not verified.

**Changed layer (not tested).** A layer that Harmonize or a generation left soft rejoins at full
resolution: Smith upscales it, scales it back into the document, nudges it in Difference until it
reads black, and reuses its mask (Smith [iy0IxTpT4OY 03:15]; [iy0IxTpT4OY 03:47]; [iy0IxTpT4OY
04:20]). Here: `IO.export_region(layer=)`, the upscale, `IO.place(bounds=)` on the layer's bounds, a
256 px `G.diff`, the old mask.

## Numbers

| Value                                                        | Relative to                     | Source                                              |
| ------------------------------------------------------------ | ------------------------------- | --------------------------------------------------- |
| Match: worst-channel mean under 6                            | baseline, 256 px long side      | toolkit, calibrated live                            |
| Real 2x upscales: 4.9 at 256 px; 9.4 to 9.5 at source        | the scripted baseline           | measured, two Scenario upscales                     |
| 8 px shift at 2x: 16.8; color cast: 38.5; 2 px blur: 7.1     | same, at 256 px                 | measured, made defects                              |
| `detail_vs_base`: 0.95 to 1.00 real, 0.08 blurred            | baseline high-pass energy       | measured                                            |
| Colorize: plain difference 29 on an aligned restore          | damaged original, 256 px        | measured, one restore                               |
| Structure: 11.3 returned, 14.0 shifted 3 px, 22.7 drifted    | damaged original, relative only | measured, one restore                               |
| Bad Auto-Align: structure 15.1 to 29.6, moved 2.5 to 17 px   | same                            | measured, three runs                                |
| Keep an align: score drop 10% or more (`gain=0.9`)           | structure before                | toolkit default                                     |
| From 300 px, faces deform; from about 1000 px, "sensational" | upscaler source size            | Hutchinson [XNCimyJ8aQk 12:21]; [XNCimyJ8aQk 12:56] |

Toolkit thresholds are authoring-time, from one 512 px photo: check them on your own images.

## Quality gates

- **Code:** `prep["ratio"]` and `prep["output"]` fit the member; per stack layer `size_ok`,
  `aspect_ok`, `match["matches"]`, `detail_vs_base`; restore takes ranked by `G.structure`; an align
  kept only on its gain, `uncovered` read; `lock` `after` under `before`; `region_blend` returns its
  `selection`; `A.deliverable(profile)` returns `[]`.
- **Visual:** the crop grid row by row at 100% (eyes, skin texture, lettering, edges, flat areas,
  gradients); the overlay on the eyes; the restore toggled against the original at 100% for
  likeness; the whole canvas for color and saturation. Rubric: [critique](references/critique.md).

## Common mistakes

| Mistake                                      | Looks like                                | Fix                                                |
| -------------------------------------------- | ----------------------------------------- | -------------------------------------------------- |
| Photoshop's "Original" as the baseline       | every upscale looks like a big win        | `build_stack`'s scripted baseline                  |
| Identity difference at full size             | good upscales fail like a shift           | `match` at 256 px; `texture_change` is information |
| Plain Difference after a colorize            | an aligned restore lights up everywhere   | `G.structure` and `R.overlay`                      |
| Auto-Align by default                        | an aligned restore moves several pixels   | `U.align`, kept only on a 10% gain                 |
| Off-ratio input to a fixed-ratio member      | the result comes back shifted or reframed | `prepare_input(ratios=...)`                        |
| Result placed without `prep`                 | padding shows; the image lands offset     | `place_result(prep=prep)`                          |
| Creative upscale on faces                    | another person looks back                 | the faithful take on the face, by mask             |
| Generative upscale on lettering or gradients | wrong letters, invented emboss, banding   | keep the baseline there                            |
| Colorize placed into a Grayscale document    | the color disappears                      | RGB mode first, with the user's yes                |
| Restore left in Normal mode                  | small changes to eyes and mouth           | Color mode over the original (`lock`)              |
| Curves above the Color layers                | the contrast fix shifts the colors        | Curves below them (Dinda [knYusnpB9zI 07:58])      |

## Handoffs

- **Receives** from scenario-photoshop-expert: routing and document state; from
  scenario-photoshop-generative-edit: soft takes to upscale before placing; from
  scenario-photoshop-compositing: changed layers to rejoin at full resolution.
- **Delivers** a stack document of named, masked candidates over the scripted baseline, or restore
  layers aligned and locked over the untouched original, with the gate numbers and the crop grid.
  Skin texture, grain and tone matching after an upscale go to scenario-photoshop-compositing;
  enlarged art for posters and thumbnails to scenario-photoshop-key-art; the final audit to
  scenario-photoshop-expert.
- **Scenario siblings:** `scenario` (connection, `recommend`, quote, Scenario job waiting),
  `scenario-image-editing` (upscale and enhance tool models), `scenario-image` (instruction restore
  and colorize), `scenario-asset-analysis` (a written verdict against the brief),
  `scenario-model-comparison` (a bake-off for a default upscaler), `scenario-refine-loop`
  (re-prompt, retry or change member after a failed gate).

## Photoshop 2026 notes

- Image Size by script accepts any resample name without error, even a made-up one. `deepUpscale`
  gave output distinct from Bicubic, Nearest Neighbor and a made-up name, so it is likely Preserve
  Details 2.0; not proven.
- Adobe lists a "Preserve Details 2.0 Upscale" Technology Preview setting. With it off, the baseline
  may differ (not tested).
- Generative Upscale opens a new document holding "Original" and the generated layer. Its partner
  models spend premium credits (Smith [9YS0m69uhIk 02:09]). UXP's `Document.generativeUpscale`
  (27.2) reaches only Adobe's own model at 2x or 4x; this toolkit has no call for it
  ([gui-paths](references/gui-paths.md)).
- Auto-Align by Action Manager needs the projection charID `Auto` (the string ID `auto` aligns
  nothing), does nothing on a smart object, and turns a Background into "Layer 0". `U.align` works
  on rasterized copies in a temporary document.
- Neural Filters (Colorize, Photo Restoration, Super Zoom) appear in recent videos (Dinda
  [G5yuLhm0SdM 01:04]; Alwash [WwRbCKao7S4 00:33]); not tested here.

## References

- [`references/expert-notes.md`](references/expert-notes.md): the measured calibration, each
  expert's method, disagreements and deciders. Load when a case is not covered above.
- [`references/procedures.md`](references/procedures.md): code per job. Load before writing a job.
- [`references/critique.md`](references/critique.md): the rubric. Load at stages 3 to 8.
- [`references/gui-paths.md`](references/gui-paths.md): Photoshop's own upscale, restore and
  alignment routes by menu, for the user or a computer-use agent.
- [`references/sources.md`](references/sources.md): videos, credentials, URLs, docs.
- [`scripts/ps_upscale.py`](scripts/ps_upscale.py): the toolkit (docstring lists every call), on top
  of the lead's scripts.
