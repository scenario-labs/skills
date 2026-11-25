---
name: scenario-after-effects-color-delivery
description: "Use when finishing or delivering from Adobe After Effects: color management, working space, OCIO or ACES, log footage, LUTs, Lumetri grade placement, bit depth, banding in gradients, grain, title and action safe, platform safe zones, render settings and output modules, export with transparent background, ProRes 4444 with alpha, straight or premultiplied, PNG sequence for a game engine, H.264 for YouTube, vertical and square versions, app store previews, loudness (LUFS, EBU R 128), color tags, checking files with ffprobe. Triggers: colors look washed out after export, my gradient has banding, export with alpha, the MP4 has no transparency, make the deliverables, YouTube upload settings, the vertical version cuts the title, render one master and many files, check the files before I send them."
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

- Render once, write many files. One render item carries several output modules, so the comp renders
  a single time (Eran Stern, FZ9yfCeZZMA 00:10:28). Derive web copies from the master afterwards
  (ShiveringCactus, PS5nPDpVM0E 00:03:22).
- Alpha never travels in MP4. ProRes 4444 with RGB + Alpha is the editing standard; ProRes 422 has
  no alpha (PS5nPDpVM0E 00:00:30, 00:02:42). Straight or premultiplied is fine if it is declared and
  handled downstream (00:03:22).
- The display transform is preview only. Export color comes from the output module, or from an
  in-comp transform with Preserve RGB, never both (InLightVFX, x2sx-P5f-iM 05:57, 06:45).
- Declare the color space of every input. The OCIO default of ACES2065-1 is wrong for almost every
  real clip (ActionVFX, pYzN_g-1N_w frame 06:29).
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
  linearize, linear blending, gamma and the color engine from the project open before it (measured
  on 27.0). `AEK.core.fresh()` resets the engine to 0 (Adobe), then 8 bpc and working space "None":
  set every field explicitly after it.
- **Templates:** list them with `ae.py templates COMP`. Format and alpha mode come only from
  templates. A template an agent saves stays in the person's preferences: name it with a clear
  prefix (`Agent - ...`) and report it.
- **Defaults when unstated:** 16 bpc, Rec.709 Gamma 2.4 working space for SDR, frame rate of the
  source, ProRes 4444 master, BT.709 tags, 48 kHz audio.

## Procedure

1. **Set and verify color.**
   `AEX.delivery.setColor({engine: "adobe", bpc: 16, workingSpace: "Rec.709 Gamma 2.4", linearize: false})`
   throws if a value did not hold. An unknown working space name silently turns color management off
   ("None"): the helper checks the name against `listColorProfiles()` first. GATE: `state()` matches
   the plan.
2. **OCIO when needed.** Script `colorManagementSystem = 1` (no enum exists in ExtendScript: 0
   Adobe, 1 OCIO) and `ocioConfigurationFile = "ACES 2.0 CG v4.0"`, then `bitsPerChannel = 32`.
   Switching to OCIO keeps the current depth without an error; OCIO then accepts 8 and 32 bpc and
   refuses 16 (measured): read the depth back. The next new project inherits the engine. The OCIO
   working space, display space and each footage media color space are GUI only: Project Settings >
   Color, and Interpret Footage > Main > Color > Override Media Color Space (Show All). Display
   Color Space is preview only; export color is the Output Module's Output Color Space (InLightVFX,
   x2sx-P5f-iM 05:23 to 06:12). GATE: a person confirms the GUI settings, or the project starts from
   a saved template `.aep`.
3. **Input transform.** Log footage: set one clip in Interpret Footage (GUI), then Remember
   Interpretation and Apply Interpretation to the other clips (ActionVFX, pYzN_g-1N_w 08:28).
   Scripted: convert before import with ffmpeg `lut3d`, import the result as Rec.709, keep the log
   original for the colorist. Never add Apply Color LUT (`ADBE Apply Color LUT2`) by script: it
   opens a file panel that blocks the application. GATE: midgray and black in a frame look right;
   PSNR or a scope reading against a reference when one exists.
4. **Grade stack.** Top to bottom: grain (finishing on top of everything, M7Ml1KoO4jY), titles,
   look, base grade, plates. Put Lumetri on adjustment layers below the titles (`moveAfter`). Script
   only scalar sliders (Exposure `ADBE Lumetri-0011`, Blacks `-0016`, Saturation `-0020`); curves,
   wheels, LUT and Look pickers are GUI. Set the black point from the scope: lower Blacks until the
   darkest value just touches the floor (Jake Bartlett, y4fuhIPxmJg 06:34). Fix Exposure, Highlights
   and Whites before any hue-to-brightness curve (16:20). GATE: titles keep their brand color in a
   captured frame; black floor and white ceiling measured (`levels` in step 9).
5. **Banding and grain.** Gradients and vignettes at 16 bpc, then dither: Noise or Add Grain on the
   top adjustment layer. Add Grain (`VISINF Grain Implant`): Viewing Mode `-0021` = 3 (Final Output;
   1 grains only a preview box), Film blending for grain heavier in the shadows (FmSTOXu2V6I 04:03).
   Titles under the grain carry it; for graphics on a grainy plate, Match Grain
   (`VISINF Grain Duplication`) with the plate as Noise Source Layer (10:21). GATE: `band_check.py`
   on a rendered frame shows a median flat run of 1 to 2 px; grain visible over the whole frame.
6. **Safe areas.** `AEX.delivery.safeCheck(comp, {all: 0.10}, times)` for title safe, plus the
   platform box per format. `AEX.delivery.guides` adds a guide layer that never renders. GATE: every
   row `ok`.
7. **Render the masters.** `AEX.delivery.render(comp, [{template, file}, ...])`: ProRes 4444 master,
   ProRes 422 or H.264 review, TIFF sequence with alpha for engines, all in one pass. `render` reads
   the render settings back and refuses proxies (Best Settings reads "Use No Proxies"). A colorist
   hand-off adds a version back in the camera log: Output Color Space = the footage's input
   transform (Show All), ProRes 4444 or EXR (pYzN_g-1N_w 09:32; x2sx-P5f-iM 07:52). For `aerender`,
   save a template with `AEX.delivery.saveTemplate`, save the project, then run
   `aerender -OMtemplate`. GATE: `render` status DONE and every module summary matches the plan; for
   `aerender`, the log ends with "Finished composition" and step 9 passes (a wrong `-comp` still
   exits 0).
8. **Post where After Effects stops.** ffmpeg: re-tag color, PNG from the TIFF sequence with
   `unpremultiply`, YouTube H.264 with `-movflags +faststart`, crops only after a reframe check,
   two-pass `loudnorm` to the target. GATE: next step.
9. **Check every file.** `python3 scripts/delivery_check.py spec.json`: expected versus measured per
   row, exit 1 on any fail. Its `levels` key reads the bit depth of each file and scales the legal
   range: 16 to 235 at 8 bits, 64 to 940 at 10, 256 to 3760 at 12 (ProRes 4444). Then one contact
   sheet: alpha over a checkerboard, each format, the safe review frame. GATE: all PASS and the
   sheet read.

## Numbers

| Value                                            | Meaning                                                                                                                                               |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 8, 16, 32                                        | `bitsPerChannel`; 16 is the default for delivery work                                                                                                 |
| 133                                              | ICC profile names from `listColorProfiles()` on 27.0, in both engines                                                                                 |
| 22 vs 83 levels                                  | same 8-bit ramp output: 8 bpc on the CPU versus 16 bpc (46 px bands versus a 2 px median run)                                                         |
| 127 vs 191                                       | 50 % green over red: gamma blending versus Blend Colors Using 1.0 Gamma or Linearize                                                                  |
| 10 % / 20 %                                      | After Effects HD defaults for action and title safe, as total inset of the frame (Preferences doc)                                                    |
| 1 to 3 px, 0.3 to 0.5                            | finishing blur and grain intensity (M7Ml1KoO4jY)                                                                                                      |
| -23.0 LUFS +/- 0.5 LU, -1 dBTP                   | EBU R 128 programme loudness and max true peak (R 128, V5)                                                                                            |
| 48 kHz, AAC-LC, BT.709, High Profile, moov first | YouTube recommended upload encoding (YouTube help)                                                                                                    |
| 15 to 30 s, 500 MB                               | App Store app preview length and file size (Apple)                                                                                                    |
| 886 x 1920                                       | App preview accepted portrait size for current Face ID iPhones (Apple)                                                                                |
| 16 to 235; 64 to 940; 256 to 3760                | broadcast (legal) Y (luminance) range at 8, 10 and 12 bits; signalstats reports in the file's bit depth (Adobe color management doc; scaling [added]) |

Streaming loudness and the platform UI safe zones are not in the saved sources: read the platform's
current spec and pass the numbers as parameters.

## Quality gates

- Measurable: `setColor` returned without error; render status DONE; `delivery_check.py` all PASS
  (codec, profile, size, fps, frame count, duration, pix_fmt, alpha, color tags, Y levels, fast
  start, audio rate, LUFS, true peak, size); `band_check.py` median run 1 to 2 px; `safeCheck` all
  `ok`; PNG sequence without gaps.
- Visual: one contact sheet of alpha over a checkerboard (no dark fringe), every aspect ratio
  (subject and titles inside), the grade with titles (brand colors intact), and a contrast-stretched
  gradient (no bands).

## Common mistakes

| Mistake                                          | Symptom                                                              | Fix                                                                         |
| ------------------------------------------------ | -------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Working space name not in the list               | color management silently "None"                                     | `AEX.delivery.setColor` checks the name                                     |
| New project assumed clean                        | dark or linear-looking frames                                        | set every color field after creating a project                              |
| 16 bpc set in an OCIO project                    | "Not supported for OCIO color managed mode"                          | `engine: "adobe"` first, or 32 bpc                                          |
| Legal range limits of another bit depth          | every frame of a 12-bit ProRes "fails" 64 to 940                     | `delivery_check.py` `levels`: limits scaled to the file                     |
| Changing format or alpha mode with `setSettings` | "Property is read-only"                                              | pick or save a template                                                     |
| `.png` file name on a QuickTime module           | file written as `.mov`                                               | use a sequence template, then convert                                       |
| Apply Color LUT added by script                  | "Choose LUT File..." blocks the app                                  | LUT in the GUI, or ffmpeg `lut3d` before import                             |
| Premultiplied frames saved as PNG                | dark halos in the engine                                             | ffmpeg `unpremultiply` to straight alpha                                    |
| Output tags trusted or assumed                   | SD tags (smpte170m) on a 960x540 ProRes; bt709 at 540x960 (measured) | read your own file's tags; re-tag with `-c copy` when wrong                 |
| Add Grain left in Preview                        | grain only in a box in the frame center                              | Viewing Mode `-0021` = 3 (Final Output)                                     |
| Template saved and forgotten                     | stray templates in the person's preferences                          | prefix `Agent - `, list them in the report                                  |
| `-color_primaries` alone in an ffmpeg encode     | primaries still smpte170m                                            | `setparams` in the filter chain                                             |
| Grade above the titles                           | brand colors graded                                                  | grade adjustment below the titles                                           |
| Center crop of the 16:9 master                   | side content lost                                                    | reframe per format or separate comps                                        |
| saveFrameToPng used to judge a linear project    | frames look darker than the render                                   | judge render queue frames                                                   |
| Export color judged from the viewer              | washed-out or shifted export                                         | output module color, display transform off when an in-comp transform exists |

## Handoffs

- Receives from scenario-after-effects-project (project and comp settings, collected footage),
  scenario-after-effects-compositing (plates, grain match, alpha),
  scenario-after-effects-motion-production (deliverable list, variants, platforms),
  scenario-after-effects-generation (generated media, tagged Rec.709 or sRGB).
- Delivers to scenario-after-effects-scripting (templates and the `render` call for batch versions),
  scenario-after-effects-motion-production (checked files and the report), and the person (files,
  check report, assumptions).

## Version notes

- OCIO and ACES since 23.2; ACES 2.0 CG v4.0 and Studio v4.0 with OCIO 2.5.1 since 26.5. On 25.x and
  earlier use the ACES 1.3 or 1.2 config names.
- Native H.264 in the Render Queue since 23.0; H.264 in MOV since 24.2. Media Encoder is optional.
- PNG Compression control new in 27.0: no `getSettings` key, set it in the GUI.
- Unmult is a native effect (`ADBE Unmult`) since 26.0.
- Multi-Frame Rendering since 22.0: `app.setMultiFrameRenderingConfig(on, maxCpu)` for the next
  render, `aerender -mfr ON 50`.

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
