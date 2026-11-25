---
name: scenario-after-effects-color-delivery
description: "Use when finishing or delivering from After Effects: color management, OCIO or ACES, log footage, LUTs, grade order, bit depth, banding, grain, safe zones, output modules, ProRes 4444 with alpha, PNG sequences, H.264 for YouTube, vertical and square versions, legal range, loudness, color tags, ffprobe checks. Also when exports look washed out, a gradient bands, or the MP4 lost its alpha."
license: MIT
---

# After Effects Color and Delivery

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means a finishing artist who declares every color space, grades in a known order,
renders the expensive pass once, and proves every file with numbers before it leaves. The agent sets
what scripting can reach, says plainly what only the GUI can set, and never trusts a template, a tag
or a loudness level it has not measured. If a sibling skill named here is missing from your
available skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit,
version traps).

## Stance (the expert delta)

- Render once, write many files. In the GUI queue, one render item carries several output modules
  (Eran Stern, FZ9yfCeZZMA 00:10:28). Out of process, `aerender` takes one template: render the
  master once and derive web copies from it with ffmpeg (ShiveringCactus, PS5nPDpVM0E 00:03:22).
- Alpha never travels in MP4. ProRes 4444 with RGB + Alpha is the editing standard; ProRes 422 has
  no alpha (PS5nPDpVM0E 00:00:30, 00:02:42). Straight or premultiplied is fine if it is declared and
  handled downstream (00:03:22).
- The display transform is preview only. Export color comes from the output module, or from an
  in-comp transform with Preserve RGB, never both (InLightVFX, x2sx-P5f-iM 05:57, 06:45).
- Declare the color space of every input. The OCIO default of ACES2065-1 is wrong for almost every
  real clip (pYzN_g-1N_w frame 06:29).
- Grade in a known order: input transform, exposure and balance, look, secondaries. Lumetri sections
  process top to bottom, so a Look can need saturation rebalanced (Jake Bartlett, y4fuhIPxmJg
  10:24). Fix exposure before a hue-to-brightness curve (Lumetri Curves) on clipped highlights
  (16:20).
- Finishing is subtle and last: blur 1 to 3 px, grain 0.3 to 0.5 on its own adjustment layer, judged
  at full view (Motion Science, M7Ml1KoO4jY; Jake Bartlett, FmSTOXu2V6I 00:41).
- Work at 16 or 32 bpc. GPU effects differ at 8 bpc (Adobe render doc), and measured here the same 8
  bpc ramp banded on the CPU and not on the GPU [added]: only 16 bpc gives the same answer
  everywhere.
- A file is delivered when its numbers pass: codec, size, frame count, alpha, color tags, loudness
  [added].

## Establish first

- **Deliverables:** list each file: use, codec, size, frame rate, duration in frames, alpha, audio,
  loudness target, naming. Ask for the receiving app (editor, engine, platform), and whether a
  colorist grades after you (then a camera-log version is a deliverable too).
- **Source:** camera log or display-referred, frame rate, bit depth. Generated media is
  display-referred (Rec.709 or sRGB).
- **Color engine:** Adobe (ICC) for SDR web and editorial; OCIO with an ACES config for multi-source
  VFX, EXR, or a colorist hand-off.
- **Project state:** read it with `AEX.delivery.state()`. A new project inherits bit depth,
  linearize, blending, gamma and engine from the project open before it, and `AEK.core.fresh()`
  resets the engine, depth and working space (procedure 1): set every field explicitly.
- **Templates:** list them with `ae.py templates COMP`. Format and alpha mode come only from
  templates. A template an agent saves stays in the person's preferences: name it with a clear
  prefix (`Agent - ...`) and report it.
- **Defaults when unstated:** 16 bpc, Rec.709 Gamma 2.4 working space for SDR, frame rate of the
  source, BT.709 tags, 48 kHz audio. Master: "High Quality" (ProRes 422, 10-bit) when opaque, "High
  Quality with Alpha" (ProRes 4444) only with alpha.

## Procedure

1. **Set and verify color.**
   `AEX.delivery.setColor({engine: "adobe", bpc: 16, workingSpace: "Rec.709 Gamma 2.4", linearize: false})`
   throws if a value did not hold. An unknown working space name silently turns color management off
   ("None"): the helper checks the name against `listColorProfiles()` first. GATE: `state()` matches
   the plan.
2. **OCIO when needed.**
   `AEX.delivery.setColor({engine: "ocio", ocioConfig: "ACES 2.0 CG v4.0", bpc: 32})`: OCIO accepts
   8 and 32 bpc and refuses 16 (procedure 2). The OCIO working space, display space and each footage
   media color space are GUI only (gui-paths.md). Display Color Space is preview only; export color
   is the Output Module's Output Color Space (InLightVFX, x2sx-P5f-iM 05:23 to 06:12). GATE: a
   person confirms the GUI settings, or the project starts from a saved template `.aep`.
3. **Input transform.** Log footage: set one clip in Interpret Footage (GUI), then Remember
   Interpretation and Apply Interpretation to the other clips (pYzN_g-1N_w 08:28). Scripted: ffmpeg
   `lut3d` before import, the log original kept for the colorist. Never add Apply Color LUT
   (`ADBE Apply Color LUT2`) by script: it opens a file panel that blocks the application. GATE:
   midgray and black in a frame look right; PSNR or a scope reading against a reference when one
   exists.
4. **Grade stack.** Top to bottom: grain (finishing on top of everything, M7Ml1KoO4jY), titles,
   look, base grade, plates. Put Lumetri on adjustment layers below the titles (`moveAfter`). Script
   only scalar sliders (Exposure `ADBE Lumetri-0011`, Blacks `-0016`, Saturation `-0020`; full list
   in procedure 4); curves, wheels, LUT and Look pickers are GUI. Set the black point from the scope
   (y4fuhIPxmJg 06:34). Name the protected colors first (brand, product, skin) and capture frames
   with the grade off and on at the same times. `color_protect.py` reads each color's own pixels
   before and after. A color that drifts gets a Change Color secondary (Match Colors RGB, tight
   tolerance) or a lighter look ([procedure 4b](references/procedures.md)). GATE: every protected
   color within delta E 5 and 4 hue degrees; titles keep their color; black floor and white ceiling
   measured (step 9).
5. **Banding and grain.** Gradients and vignettes at 16 bpc, then dither: Noise or Add Grain on the
   top adjustment layer. Keep Noise Clipping (`ADBE Noise-0003`) at 1: at 0, highlights wrap into
   cyan specks. Add Grain (`VISINF Grain Implant`): Viewing Mode `-0021` = 3 (Final Output; 1 grains
   only a preview box), Film blending for grain heavier in the shadows (FmSTOXu2V6I 04:03). Titles
   under the grain carry it; for graphics on a grainy plate, Match Grain
   (`VISINF Grain Duplication`) with the plate as Noise Source Layer (10:21). GATE:
   `band_check.py --max-run 16` on a full-size frame of the encoded file: median flat run 1 to 2 px,
   widest run 16 px or less (one macroblock); grain over the whole frame.
6. **Safe areas.** `AEX.delivery.safeCheck(comp, {all: 0.10}, times)` for title safe, plus the
   platform box per format. `AEX.delivery.guides` adds a guide layer that never renders. GATE: every
   row `ok`.
7. **Render the masters.** `AEX.delivery.render(comp, [{template, file}, ...])` writes master,
   review and TIFF sequence in one pass, but blocks the app while it renders. Out of process,
   `ae.py aerender` the master alone, then derive the web file in step 8. `render` reads the render
   settings back and refuses proxies. A colorist hand-off adds a camera-log version, and `aerender`
   needs a saved template and project (procedures 7 and 8). GATE: `render` status DONE and every
   module summary matches the plan; for `aerender`, the log ends with "Finished composition" and
   step 9 passes (a wrong `-comp` still exits 0).
8. **Post where After Effects stops.** ffmpeg, per procedure 9: read the master's matrix tag first.
   After Effects encodes SD frame sizes (960x540) with BT.601 and tags them smpte170m: convert with
   `scale=in_color_matrix=bt601:out_color_matrix=bt709`, never re-tag (39 levels off on pure red).
   Map `-map 0:v:0 -write_tmcd 0`, or the timecode track lands in the MP4. Broadcast-legal: a soft
   knee before x264; a hard clip at 235 comes back at 245. Also `unpremultiply` for PNG,
   `+faststart`, two-pass `loudnorm`. GATE: next step.
9. **Check every file.**
   `python3 scenario-after-effects-color-delivery/scripts/delivery_check.py spec.json`: expected
   versus measured per row, exit 1 on any fail; `no_data` fails a timecode track. Its `levels` key
   scales the legal range to each file's bit depth (16 to 235 at 8 bits, 64 to 940 at 10, 256 to
   3760 at 12). Grain leaves a few pixels outside after any knee: `"max_out_pct": 0.01` judges the
   share of the frame out of range instead (procedure 10). Then one contact sheet: alpha over a
   checkerboard, each format, the safe review frame. Measure from frames decoded with the file's
   matrix and `in_range=tv` (procedure 10; the default decode reads white at 253). Judge banding at
   1:1, never on a downscaled sheet. GATE: all PASS and the sheet read.

## Numbers

| Value                                            | Meaning                                                                                                                                               |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 8, 16, 32                                        | `bitsPerChannel`; 16 is the default for delivery work                                                                                                 |
| 133                                              | ICC profile names from `listColorProfiles()` on 27.0, in both engines                                                                                 |
| 22 vs 83 levels                                  | same 8-bit ramp output: 8 bpc on the CPU versus 16 bpc (46 px bands versus a 2 px median run)                                                         |
| 127 vs 191                                       | 50 % green over red: gamma blending versus Blend Colors Using 1.0 Gamma or Linearize                                                                  |
| 10 % / 20 %                                      | After Effects HD defaults: action safe 10 %, title safe 20 % of the frame, so 5 % and 10 % on each side (Preferences doc)                             |
| 1 to 3 px, 0.3 to 0.5                            | finishing blur and grain intensity (M7Ml1KoO4jY)                                                                                                      |
| -23.0 LUFS +/- 0.5 LU, -1 dBTP                   | EBU R 128 programme loudness and max true peak (R 128, V5)                                                                                            |
| 48 kHz, AAC-LC, BT.709, High Profile, moov first | YouTube recommended upload encoding (YouTube help); the After Effects H.264 template writes Main, the ffmpeg line of procedure 9 writes High          |
| delta E 5, 4 degrees                             | protected-color tolerance (CIE76, a*b* hue) between grade off and on                                                                                  |
| 15 to 30 s, 500 MB                               | App Store app preview length and file size (Apple)                                                                                                    |
| 205 / 220, 32 / 22                               | soft knee (start / clip) for Y highlights and shadows before x264; encoded Y 23 to 229 (measured)                                                     |
| 16 to 235; 64 to 940; 256 to 3760                | broadcast (legal) Y (luminance) range at 8, 10 and 12 bits; signalstats reports in the file's bit depth (Adobe color management doc; scaling [added]) |

Streaming loudness and the platform UI safe zones are not in the saved sources: read the platform's
current spec and pass the numbers as parameters.

## Quality gates

- Measurable: `setColor` returned without error; render status DONE; `delivery_check.py` all PASS;
  `color_protect.py` all PASS; `band_check.py --max-run 16` passes; `safeCheck` all `ok`; PNG
  sequence without gaps.
- Visual: one contact sheet of alpha over a checkerboard (no dark fringe), every aspect ratio
  (subject and titles inside), the grade with titles (brand colors intact), and a contrast-stretched
  gradient (no bands).

## Common mistakes

| Mistake                                                 | Symptom                                               | Fix                                                                         |
| ------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------- |
| Working space name not in the list                      | color management silently "None"                      | `AEX.delivery.setColor` checks the name                                     |
| New project assumed clean                               | dark or linear-looking frames                         | set every color field after creating a project                              |
| 16 bpc set in an OCIO project                           | "Not supported for OCIO color managed mode"           | `engine: "adobe"` first, or 32 bpc                                          |
| Legal range limits of another bit depth                 | every frame of a 12-bit ProRes "fails" 64 to 940      | `delivery_check.py` `levels`: limits scaled to the file                     |
| Changing format or alpha mode with `setSettings`        | "Property is read-only"                               | pick or save a template                                                     |
| Apply Color LUT added by script                         | "Choose LUT File..." blocks the app                   | LUT in the GUI, or ffmpeg `lut3d` before import                             |
| Premultiplied frames saved as PNG                       | dark halos in the engine                              | ffmpeg `unpremultiply` to straight alpha                                    |
| SD render re-tagged bt709 with `-c copy` or `setparams` | reds and greens shift; pure red decodes with green 24 | convert the matrix with `scale` (procedure 9); the tag was right            |
| Timecode track copied into the MP4                      | a `tmcd` data stream beside the video                 | `-map 0:v:0 -write_tmcd 0`; `no_data` in the check                          |
| Hard clip before x264 for legal range                   | Y max 245 after encoding (ringing)                    | soft knee with margin, then measure the encoded file                        |
| Add Grain left in Preview                               | grain only in a box in the frame center               | Viewing Mode `-0021` = 3 (Final Output)                                     |
| Template saved and forgotten                            | stray templates in the person's preferences           | prefix `Agent - `, list them in the report                                  |
| `-color_primaries` alone in an ffmpeg encode            | primaries still smpte170m                             | `setparams` in the filter chain, after any matrix conversion                |
| Grade above the titles                                  | brand colors graded                                   | grade adjustment below the titles                                           |
| Center crop of the 16:9 master                          | side content lost                                     | reframe per format or separate comps                                        |
| Export color judged from the viewer                     | washed-out or shifted export                          | output module color, display transform off when an in-comp transform exists |

## Handoffs

- Receives from scenario-after-effects-project (project and comp settings, collected footage),
  scenario-after-effects-compositing (plates, grain match, alpha),
  scenario-after-effects-motion-production (deliverable list, variants, platforms),
  scenario-after-effects-generation (generated media, tagged Rec.709 or sRGB).
- Delivers to scenario-after-effects-scripting (templates and the `render` call for batch versions),
  scenario-after-effects-motion-production (checked files and the report), and the person (files,
  check report, assumptions).

## Version notes

OCIO and ACES since 23.2 (ACES 2.0 configs since 26.5), native H.264 since 23.0, `ADBE Unmult` since
26.0: the full list is in procedures.md, Version notes.

## References

- [references/procedures.md](references/procedures.md): every job and command, with channel, checked
  line and what to check.
- [references/expert-notes.md](references/expert-notes.md): what each expert does and why, with
  timestamps.
- [references/critique.md](references/critique.md): the rubric for judging a delivery.
- [references/gui-paths.md](references/gui-paths.md): menus and dialogs for what scripts cannot
  reach.
- [references/sources.md](references/sources.md): every source with URL.
- [scripts/color_delivery.jsx](scripts/color_delivery.jsx): `AEX.delivery` (`state`, `setColor`,
  `render`, `saveTemplate`, `safeCheck`, `guides`).
- [scripts/delivery_check.py](scripts/delivery_check.py): expected versus measured per deliverable.
- [scripts/band_check.py](scripts/band_check.py): levels and flat runs on a rendered frame.
- [scripts/color_protect.py](scripts/color_protect.py): protected colors before and after a grade.
