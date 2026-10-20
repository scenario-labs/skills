---
name: scenario-photoshop-key-art
description: "Use when building key art, ads, YouTube thumbnails, Steam store capsules, social posts, digital posters or campaign files in Adobe Photoshop around a Scenario image: a canvas per channel at the channel's size, a generated plate or subject that has to fill it, live headline and copy text from a copy sheet, a size set (16:9, 4:5, 9:16, store capsules) or campaign variants from one master, Variables and Data Sets, or an export under a file-size cap such as YouTube's 2 MB. Also when a headline is unreadable at phone size, copy hides under a duration badge or a story bar, Photoshop silently swaps a missing font, paragraph text is cut off without warning, a plate looks soft or cropped wrong in one format, or an export is over the size limit. Not for print: a printed poster goes to scenario-photoshop-upscale-restore's print path."
license: MIT
---

# Key art, ads and thumbnails (Photoshop 2026)

Expert key art is a layered file per channel that reads at the size people see it. A Scenario plate
fills the canvas around its focus point, the copy is live type from the user's copy sheet, nothing
that matters sits under the channel's own interface, and each export fits the channel's file-size
cap. Scenario makes the plates; Photoshop holds layout, type, checks and export. If a sibling skill
named here is missing from your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.

**REQUIRED BACKGROUND:** scenario-photoshop-expert (execution channel, round trip, gates).

**Status (2026-10-19):** in [`scripts/ps_keyart.py`](scripts/ps_keyart.py), `new_canvas`,
`type_layers` (fit, alignments, missing font), `check` and `export_under` are verified live on
Photoshop 27.11 (macOS) by `test_keyart_live.py` (6 tests on a YouTube thumbnail, previews checked
by eye, a canvas holding a Clarity layer included). `cover_bounds` is tested offline only. Not
tested: a cover plate past the canvas, layer styles on type, the contrast estimate, variant loops,
Variables and Data Sets, the `social` profile, a paid plate, Windows.

## Stance (the expert delta)

- **Copy, prices and logos stay live layers; the plate carries no lettering.** Morgan Hastie
  generates around blank bottles ("Don't change the bottles"), then drops the label art in as Smart
  Objects so a client revision is one swap [70L2ngS8raY 02:47, 03:21]. DGH styles the group "so it
  can be edited in the future" [BmqlEDGP-GY 01:02]. Text in a smart object or rasterized escapes
  `check`.
- **Judge text at display size, in pixels.** storezar zooms out to "about the size of a phone
  thumbnail" and holds a phone to the screen [BtzVLw67Ggs 25:20]. Measured on 27.11: a one-line
  subline fitted at 39 pt is 11 px when the 1280 px thumbnail shows 360 px wide; on two lines it
  stays at 60 pt, 17 px.
- **The channel's interface owns part of the canvas.** [added: no source video sets safe zones, and
  a duration badge or a story's reply bar hides what sits under it.] Presets draw these zones as
  guides; `check` flags text that touches one.
- **One canvas per channel, covered by a plate that is never enlarged.** Ira Ostrovska upscales a
  generated image "a little bit in higher resolution than your render" before compositing
  [Uvq85gcMSE0 03:29]. `cover_bounds` crops around the subject's focus point. [added]
  `export_under(size=)` resamples without cropping, so it only makes a smaller copy of the same
  aspect.
- **Type is read back, never assumed.** Measured on 27.11: a missing font raises nothing and the
  layer keeps Myriad Pro. Point text bounds are what renders (260 pt asked, 132 pt fits a 472 x 430
  box); a paragraph box hides overflow without an error. `type_layers` sets point text and reports
  `fits` and `font_used`.
- **Export at the highest quality under the cap.** storezar: "YouTube does not accept files larger
  than 2 megabytes", then he exports at about 1.6 MB [BtzVLw67Ggs 29:48, 30:19]. Measured: a 1280 x
  720 thumbnail weighs 477 KB at JPEG quality 12, so the cap bites on large canvases and tight ad
  caps. `export_under` steps down from 12.
- **Variants come from one master and change one thing each.** Badis Designs makes "two versions of
  the thumbnail, one with text and one without" to test [TuF4RMJtq-4 06:30]. Julieanne Kost turns
  one prompt into four seasons, 16 images, with a variable list [SXVB8X4P2LI 04:55]. Mike Hughes
  drives text, photo and visibility from one CSV whose headers match the variable names, case
  included [uUQ8pbysZsY 06:45].
- **Brief the plate for the layout, then fit its light.** Faces "create emotion, and that is what
  drives clicks" (Badis Designs [TuF4RMJtq-4 00:32]). storezar wants "a light source that logically
  falls on the face" [BtzVLw67Ggs 03:44]; his generated hand "undoes all our painstaking shadow
  work" [BtzVLw67Ggs 28:42]. Generated pieces get their light and shadows matched before type goes
  on.

## Establish first

| Input                 | Changes                            | Default when the user is silent                     |
| --------------------- | ---------------------------------- | --------------------------------------------------- |
| Channels              | presets, canvases, exports         | ask; a video cover: `youtube-thumbnail`             |
| Channel specs         | size, cap, unsafe zones            | the preset, checked against the channel's docs      |
| Copy sheet            | text layers                        | the user's exact words; none: no copy, ask          |
| Fonts and colors      | `font` (PostScript name), `color`  | the brand's; none: `Arial-BoldMT`, white, reported  |
| Plate                 | what fills each canvas             | a Scenario plate, quoted first; or the user's image |
| Focus and subject box | the crop per channel               | read off the plate by eye                           |
| Copy boxes            | `box` per item and channel         | opposite the subject, clear of unsafe zones         |
| Byte cap and format   | `export_under`                     | the preset's `max_bytes`, JPEG; none: ask           |
| Variants              | the loop, the quote                | one; a thumbnail test: with and without text        |
| Deliverable           | audit profile, files               | one export per channel plus a layered PSD copy      |
| Work folder           | where plates, previews, exports go | a new folder, never the PSD's own folder            |

## Workflow

`sys.path.insert(0, "<this skill>/scripts")`, then `import ps_keyart as K` (it puts the lead's
`scripts/` on the path) and `import ps_io as IO, ps_review as R, ps_audit as A`. Each call is one
`ps_run` job and acts on the active document; after one raises or times out, recover as the lead's
Quality gates say. Code: [procedures](references/procedures.md).

1. **Intake.** One preset per channel: `K.PRESETS[name]` holds `size`, `unsafe`, `display` and, for
   YouTube, `max_bytes`. A channel without a preset is a dict with the same keys. Presets are
   authoring-time specs: check each channel's own documentation before a campaign. GATE: every
   channel has a preset; the copy sheet matches the user's words letter for letter.
2. **Plate.** A Scenario MCP step: the price quote and the user's yes before every run (`scenario`),
   then the run (`scenario-image`; Handoffs names the other siblings). Prompt: no text or letters,
   the subject where the layout puts it, a quiet area for the copy, one light direction. GATE: quote
   approved; no lettering in the plate; on every canvas, the `cover_bounds` width over the plate
   width is 1 or less.
3. **Canvas.** `c = K.new_canvas("youtube-thumbnail", name="Owl campaign, YouTube")`: RGB 8-bit sRGB
   at 72 ppi, unsafe zones as guides; it becomes the active document. GATE: `c["size"]` equals the
   preset.
4. **Plate in.** `b = K.cover_bounds(pw, ph, W, H, focus=(0.7, 0.4))`, then
   `IO.place(plate, "Plate, owl", bounds=b, xmp={...})`. Map the subject box through `b`. GATE:
   returned bounds equal `b` within 1 px; the subject sits inside the canvas and off the unsafe
   zones. Else expand the plate (scenario-photoshop-generative-edit) or generate one for that
   aspect.
5. **Type.** `t = K.type_layers(copy)`: live point text per item, shrunk to fit its box, aligned in
   it, one History state. Split lines before letting a line shrink. Stroke, shadow or a dark band
   behind small copy: procedures P5 (not tested). GATE: every `fits`; every
   `font_used == font_asked`, else report the font and stop.
6. **Check.** `r = K.check("youtube-thumbnail")` after the last change to type or styles. Then
   `R.preview(out, max_px=...)` at display size and `R.preview(out)`, and open both. `max_px` is a
   long edge: for a portrait canvas pass display x height / width. GATE: `r["problems"] == []`; at
   display size the subject and the headline read first and every line is legible
   ([critique](references/critique.md)).
7. **Export.** `e = K.export_under(out, max_bytes)`: a flattened sRGB 8-bit copy at the highest JPEG
   quality under the cap. Pass `size=[w, h]` only for a smaller copy of the same aspect. GATE:
   `e["fits"]`; `e["size"]` equals the channel's size; the quality goes in the report.
8. **Deliver.** `A.deliverable("social")` for social canvases, `"web"` for store capsules, and
   `"psd-handoff"` before a layered copy goes out (procedures P8). Expected findings: a cover plate
   extends past the canvas; a 462 px capsule is under the `web` minimum. GATE: no other finding; the
   report names the expected ones.
9. **More channels and variants.** Stages 3 to 8 per channel, from the same plate with its own focus
   and copy boxes. A variant changes one thing: the copy (remove the type layers, run `type_layers`
   again), the plate (`IO.replace` keeps the box only for a plate of the same pixel size), or one
   layer's visibility. Quote all plate jobs of the set once. GATE: each variant passes stages 6 to 8
   and differs from the master in the intended layer only. CSV data sets run through Photoshop's
   Variables ([gui-paths](references/gui-paths.md)).

## Numbers

| Value                                                 | Relative to                      | Source                    |
| ----------------------------------------------------- | -------------------------------- | ------------------------- |
| YouTube 1280 x 720, cap 2 MB, badge zone 200 x 100 px | canvas, bottom right             | preset, secondary sources |
| Story 1080 x 1920, unsafe top 250 px, bottom 340 px   | canvas                           | preset, authoring-time    |
| Steam: 920x430, 462x174, 1232x706, 748x896, 600x900   | store and library capsules       | Steamworks (August 2024)  |
| Steam library hero 3840 x 1240, no text               | canvas                           | Steamworks                |
| Display width 360 (thumbnail), 390 (phone feed)       | canvas width as seen             | preset, authoring-time    |
| Text under 12 px is flagged                           | font size at display width       | authoring-time            |
| 39 pt on one line = 11 px; 60 pt on two lines = 17 px | 1280 px canvas shown 360 px wide | measured                  |
| JPEG q12 477 KB, q10 285, q8 194, q5 134, q0 65       | one 1280 x 720 thumbnail         | measured                  |
| Plate scale 1 or less                                 | plate px per canvas px           | [added] after Ostrovska   |
| Contrast 4.5:1 small text, 3:1 large text             | text color vs mean color behind  | WCAG 2, as an estimate    |

Authoring-time numbers: check them on your own channels and images.

## Quality gates

Code gates, in order:

- Plate scale 1 or less on every canvas; placed bounds equal `cover_bounds` within 1 px.
- `type_layers`: every `fits`, every `font_used == font_asked`.
- `check(preset)["problems"] == []`, run after the last type or style change.
- `export_under`: `fits`, size equal to the channel's.
- `A.deliverable(profile)` returns only the expected findings.

Visual gates:

- The plate at 100%: no letters, hands and faces intact, light from one side.
- The display-size preview: subject first, then the headline; every line legible; few colors.
- Spelling against the copy sheet, letter by letter.
- Per channel: the crop keeps the subject; nothing important under a guide zone.

## Common mistakes

| Mistake                              | Looks like                            | Fix                                                 |
| ------------------------------------ | ------------------------------------- | --------------------------------------------------- |
| Lettering generated in the plate     | misspelled words, a font nobody chose | prompt "no text or letters"; set type in Photoshop  |
| Paragraph text box                   | copy cut off, no error                | point text through `type_layers`; read `fits`       |
| Trusting the font                    | headline in Myriad Pro                | compare `font_used` and `font_asked`                |
| Shrinking copy until it fits         | an 11 px subline on a phone           | split lines, shorten with the user, or a larger box |
| Copy under the channel's interface   | the duration badge over the price     | the preset's zones; `check`                         |
| `size=` to another aspect            | stretched faces in the square version | a canvas per channel                                |
| Plate smaller than the canvas        | soft plate at 100%                    | scale 1 or less; upscale first or generate larger   |
| Centered crop of a side subject      | head cut off in 9:16                  | `cover_bounds` focus; expand for that aspect        |
| Text in a smart object or rasterized | `check` reports nothing for it        | keep copy as live text layers                       |
| Styles added after the check         | a shadow now touches the badge zone   | run `check` last                                    |
| Judging at 100% only                 | a headline nobody reads on a phone    | preview at display width                            |

## Handoffs

- **Receives** from scenario-photoshop-expert: routing, document state, round-trip rules; from
  scenario-photoshop-compositing: a subject composited into the plate with matched light; from the
  user: channels, copy sheet, fonts, brand colors, plates or approval to generate them.
- **Delivers** one canvas per channel with named plate and type layers, one export per channel under
  its cap, the `check` and `deliverable` results, and what was not verified.
- **Sends** a soft or small plate to scenario-photoshop-upscale-restore; a crop that cuts the
  subject to scenario-photoshop-generative-edit (expand); a pasted-on subject, relight, shadows or a
  face retouch to scenario-photoshop-compositing; key art onto a product or screen photo to
  scenario-photoshop-mockups; print (canvases here are 72 ppi screen files) to the print path of
  scenario-photoshop-upscale-restore (its procedures P10).
- **Scenario siblings:** `scenario` (connection, `recommend`, quote, Scenario job waiting),
  `scenario-image` (plates, instruction edits), `scenario-thumbnails` (a video cover's concept),
  `scenario-consistency` (one character across plates), `scenario-formats` (a size set made on the
  platform when nobody needs a PSD). When nobody needs a layered file, scenario-text-overlay sets
  the text on the platform instead. A brand kit (scenario-brand-kit) supplies the copy sheet's fonts
  and colors.

## Photoshop 2026 notes

- A missing font raises nothing and the layer keeps Myriad Pro. Adobe Fonts activation has no script
  call: the user activates the font, then the agent sets the type again.
- Dynamic Text (27.6, any shape since 27.10) has no script call; `type_layers` fitting replaces it.
- Type size is in points: px = pt x ppi / 72, equal at the toolkit's 72 ppi. `check` converts at any
  resolution.
- The DOM has no artboard API; artboards by Action Manager are not tested here. One document per
  channel replaces them.
- Photoshop's Generate Image has no toolkit call; scripted plates come from Scenario.
- `export_under` saves a flattened duplicate through `psr_export`: JPEG quality 0 to 12; PNG skips
  the cap search.
- A Clarity layer makes the DOM's `layer.kind` throw "Internal error": `check` reads the layer kind
  through Action Manager, and so should your own jobs.

## References

- [references/procedures.md](references/procedures.md): P1 to P11, code per stage with its test
  status. Read before the first job.
- [references/critique.md](references/critique.md): the rubric for stages 2, 6 and 9.
- [references/gui-paths.md](references/gui-paths.md): menu paths for steps with no script call.
- [references/expert-notes.md](references/expert-notes.md): each source's method, disagreements and
  deciders.
- [references/sources.md](references/sources.md): videos, credentials, URLs, documentation.
- [scripts/ps_keyart.py](scripts/ps_keyart.py): the toolkit; its docstring lists every call and
  `PRESETS` holds sizes, caps, unsafe zones and display widths.
