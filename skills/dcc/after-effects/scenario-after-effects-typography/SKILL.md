---
name: scenario-after-effects-typography
description: "Use when animating text in After Effects: kinetic type, captions or lyrics synced to a voiceover, text animators and range or expression selectors, per-letter overshoot, 3D flips, tracking-in, variable fonts, titles reflowed across 16:9, 9:16 and 1:1, localized versions. Also for 'text overflows', 'words appear too early', 'looks cheap', 'font missing', 'make it readable'."
license: MIT
---

# After Effects kinetic typography

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert kinetic type is built so the text and the timing can change without rebuilding anything:
animators hold end states, selectors hold motion, markers hold the voice, and in and out points hold
the in and out. An agent never times words by ear: it derives frames from a transcript with word
timestamps, places them by script, and proves readability with numbers before it looks at one
contact sheet. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit,
version traps).

## Stance (the expert delta)

1. **Keys go on the selector, never on the animator property.** The property holds the end offset;
   Offset, Start, End or Amount carries the motion (Jake Bartlett, NclmWZa4c_8 00:01:42). Values are
   relative: 50 % selected gets half (Joey Korenman, b1_p2qQf_Ts 00:09:44).
2. **Pair Shape with its Offset range.** Ramp Up plus Ease Low 100 animates Offset -100 to 100
   (Bartlett 00:04:34). Square animates Offset 0 to 100 [added, measured; procedure 4].
3. **Based On and Anchor Point Grouping change together.** Words with Character grouping scales
   letters, not words (Bartlett 00:08:54). Use Characters Excluding Spaces for letter cascades, or
   spaces add a pause (Adobe help).
4. **Sentences go by words or lines; titles go by characters.** Keep the sentence centered while it
   builds (Stephan Zammit, c-Q06JnT6mE 00:04:42). At speech pace words arrive 3 to 6 frames apart:
   accumulate them in a phrase layer, never swap one word for the next [added].
5. **Time from data, retime by moving data.** One layer marker per word drives an expression
   selector; one in and out expression reads `inPoint` and `outPoint` [added, both measured]. Moving
   a marker or trimming a layer is the whole retime.
6. **Build for the longest language first.** Fit by rebreaking lines at the designed size before
   shrinking; shrink below 80 % of the design size only with sign-off [added]. Templates center
   through Paragraph plus Align to comp so retyped text stays centered (Jordy, miiGiGtFuTU
   00:00:43).
7. **Variable fonts animate only through animators** (26.0+), from a thin base style (Bartlett,
   Tjm3NxPYPqk 00:02:02, 00:04:10).
8. **Name every animator** for its job; expressions and the reveal helpers find them by name (Zammit
   00:01:31).

## Establish first

- Deliverable and platform: social vertical (1080x1920), 16:9 (1920x1080), or broadcast; it sets the
  safe area and the minimum size.
- **Base rate:** frame counts in this skill assume 24 fps. For another rate, multiply by (target fps
  / 24) and round to whole frames: 30 to 24 is x 0.8, 24 to 30 is x 1.25.
- Voiceover file and its script, if there is one. Languages and who supplies the translated text.
- Fonts: the brief's face first; else `AEX.type.fontPair({text})` picks two weights of one installed
  family from a ranked macOS and Windows list, with a fallback (procedure 1). Confirm any name with
  `AEK.text.fontExists` and `hasGlyphsFor(text)` (25.1+).
- Template or one-off: a template that people retype needs named animators, centered paragraphs, and
  no index-based expressions.
- Renderer: per-character 3D renders in Classic 3D (`ADBE Advanced 3d`, a scripted comp's default)
  and Advanced 3D (`ADBE Calder`); only Classic 3D takes layer motion blur (procedure 6).
- Channel: bridge by default; `handoff` for a person to run.

## Procedure

Full code in [references/procedures.md](references/procedures.md); helpers in
[scripts/typography.jsx](scripts/typography.jsx) (`AEX.type`) and
[scripts/word_timings.py](scripts/word_timings.py).

1. **Inventory fonts.** Goal: fonts installed on the render machine, covering every language. How:
   procedure 1 lists families, variable fonts with axes (`designAxesData` keys `name`, `tag`, `min`,
   `max`, `default`) and glyph coverage. GATE: every chosen PostScript name installed,
   `hasGlyphsFor` true for each language string.

2. **Get word timings without listening.** Goal: one frame number per word. How: a speech-to-text
   run with word timestamps, an ffmpeg `silencedetect` pass, then
   `word_timings.py --fps 24 --lead 1 --silence silence.log`. When they disagree, trust the silence
   boundary for the phrase start. Without a transcript, Convert Audio to Keyframes (procedure 11)
   finds phrases, never words. GATE: `checks.increasing` and `checks.silence_agrees` true (phrase
   onsets within 2 frames of a silence end).

3. **Lay out.** Write the layout idea in one sentence first: what is biggest, what aligns to what,
   what moves last. A centered stack needs a stated reason (`AEX.type.layout`, procedure 13).
   Phrases: goal a phrase per layer, readable dwell. How:
   `AEX.type.phraseLayers(comp, data, {font, size, fill, position, tail})`: one centered layer per
   phrase (in at the first word, out at the phrase end + `tail` frames), one marker per word, a
   `reveal` animator on a marker expression selector. GATE: marker count equals word count, 0
   marker-frame mismatches, no `expressionError`; 0 text pixels before the first word.

4. **Design the motion.** Goal: one reusable look per role. How: `AEK.text.animator`,
   `AEX.type.selector` and `AEX.type.grouping` (procedure 4): character rise, Square one at a time,
   word pop. Tracking-in keys the range selector Amount (`AEK.text.animator` option `amount`;
   `AEX.type.amount` re-fetches it). Fit the start Tracking with `AEX.type.trackingFit` (1 px per
   unit per gap, at any size). Stack order and pauses: procedure 4. Moving type gets motion blur:
   `comp.motionBlur` and `layer.motionBlur` true, shutter 180, phase -90 (a scripted comp reads 0).
   GATE: settled frame identical to the static text (same `sourceRectAtTime`), keys only on
   selectors.

5. **Overshoot per character.** Goal: letters that pass their rest position and settle, staggered.
   How: a range selector cannot (procedure 5b). Use
   `AEX.type.overshoot(layer, {properties, start, stagger, peak, settle, overshoot, order, vary})`,
   an expression selector whose Amount goes below 0. `order: "center"` starts from the middle;
   `vary` shortens the travel of later letters, so they stop sharing one distance. Position, Scale
   and Rotation pass their rest; Opacity cannot. GATE: one-letter probe through `sourceRectAtTime`:
   overshoot equals the set percent of the offset, settle on the `settle` frame.

6. **Stagger and emphasis.** Goal: order and accents without hand keys. How: an expression selector
   with `textIndex` (procedure 5), a character range for one word's size, color or font (procedure
   7, 24.3+), or the word-picker slider with Units Index (Zammit 00:06:54, 00:07:59). Accent
   recipes: procedure 5. GATE: the emphasized range reads back the new font and size; no `index`
   (layer index) in text expressions.

7. **Per-character 3D, when depth is the idea.** Goal: letters that flip or orbit. How:
   `layer.threeDPerChar = true`, THEN add `ADBE Text Rotation X` and a Z position to the animator,
   Grouping Alignment `[0, -50]`, a camera at an angle (procedure 6). Orbit: a setup animator with
   `ADBE Text Anchor Point 3D` `[0, 0, 200]`, then Y Rotation (Korenman, b1_p2qQf_Ts 00:25:38).
   GATE: rest frame flat and readable; letters pivot at mid cap height.

8. **Variable font motion.** How: `addVariableFontAxis("wght")` on the animator properties
   (procedure 7); expressions read `text.animator("weight").property.fontAxisWght`. GATE: width
   changes across the move (`sourceRectAtTime`).

9. **Reusable in and out.** How: `AEX.type.inOut(layer, {inFrames: 12, outFrames: 10, exit})` drives
   Offset from `inPoint` and `outPoint`, ease out in and ease in out (procedure 9).
   `exit: "reverse"` leaves last character first; `"forward"` adds a Ramp Down animator so the first
   leaves first. Presets are GUI only (gui-paths.md). GATE: after sliding and trimming the layer,
   Offset at `inPoint + 6` and `outPoint - 5` frames is unchanged.

10. **Localize and reflow.** Goal: every language and every format (16:9, 9:16, 1:1) inside title
    safe at a readable size. How: procedure 8: measure point text against 80 % of the frame width;
    `AEX.type.balance(layer, maxWidth, 3)` first (1 to 3 lines at the designed size), then
    `AEK.text.fit` (size), or scale-to-fit. A second-language voiceover reruns stage 2. GATE:
    `AEK.text.inFrame(l, c, 0.1, t)` ok at mid-life of every 2D layer, parents included (3D text:
    `AEX.type.inFrame`); size at or above 80 % of design.

11. **Prove readability.** How:
    `AEX.type.readability(comp, {bg, minFrames: 18, minCapRatio: 0.035, safe: 0.1, minContrast: 4.5})`
    (procedure 10; over footage `sample: true` replaces `bg`): contrast per color run, dwell on
    settled frames (at rest, fully opaque). GATE: no errors; warnings justified in the delivery.
    Then one contact sheet per [references/critique.md](references/critique.md).

## Numbers

| Item                      | Value                                                                                        | Relative to                               |
| ------------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Word lead                 | 1 frame early (0 to 2)                                                                       | spoken onset, 24 fps                      |
| Word reveal ease          | 4 frames                                                                                     | per word, 24 fps                          |
| Phrase tail               | 6 to 8 frames after the last word                                                            | 24 fps                                    |
| Minimum dwell             | 18 settled frames, and about 6 per word; word-synced phrases count time on screen            | 24 fps                                    |
| Caption pacing (social)   | about 20 characters, 1.2 s minimum, 0 gap, single line (Ryan Connolly, ZCP2W_NTpLE 00:00:14) | per caption                               |
| Pop scale                 | 95, 105 (+3 frames), 100 (+2 frames) (Connolly 00:01:21)                                     | percent                                   |
| Cap height, running text  | at least 3.5 % (38 px at 1080)                                                               | short side of the frame, in every format  |
| Per-character overshoot   | `overshoot` 8 by default, peak 10, settle 18 frames [added]                                  | animator offset, frames                   |
| Contrast                  | 4.5:1 or more (WCAG ratio)                                                                   | fill vs flat background                   |
| Safe area for text        | 10 % margin each side                                                                        | comp width and height                     |
| Localization shrink floor | 80 % of designed size                                                                        | designed font size                        |
| Grouping Alignment        | 0, -50 % caps; 0, -25 % lowercase (Adobe help)                                               | character box                             |
| Range Offset              | Ramp Up -100 to 100; Square 0 to 100                                                         | percent of the text                       |
| Ease High / Low           | 50 / 50 safe start (Korenman 00:08:40); Ramp Up base: Low 100 (Bartlett)                     | percent                                   |
| Variable font wave        | Triangle, End 25 %, Ease High and Low 60, 2 s loop (Bartlett, Tjm3NxPYPqk 00:06:08)          | percent, seconds                          |
| Tracking-in               | Start value from `trackingFit`, to 0 with expo-out (0.16, 1, 0.3, 1) over 20 frames [added]  | px per character gap, frame width, 24 fps |
| Per-character 3D flip     | X Rotation -90, Z -150 px, Offset -100 to 100 over 24 frames [added]                         | degrees, px, 24 fps                       |

## Quality gates

- Measurable: every stage GATE above, plus `AEK.audit.summary(AEK.audit.all())` clean for fonts.
- Visual (one contact sheet, rows in critique.md): reading order, baselines at rest, pivots, safe
  margins, a layout idea and a moving hold. Dim frames from a 32 bpc project: procedure 12.

## Common mistakes

| Mistake                                              | Symptom                                                                    | Fix                                                                 |
| ---------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Keyframes on the animator property                   | Retyped text breaks, cascade impossible                                    | Key the selector Offset or Amount                                   |
| Square with Offset -100 to 100                       | Text visible at frame 0, vanishes, then reveals                            | Square: Offset 0 to 100                                             |
| Based On Words, grouping Character                   | Word "scale" shrinks each letter in place                                  | `AEX.type.grouping(l, "word", [0, -25])`                            |
| Based On Characters for a cascade                    | Pause at every space                                                       | Characters Excluding Spaces                                         |
| One layer per word at speech pace                    | Words flash for 3 to 5 frames                                              | Phrase layers that accumulate words                                 |
| Timing by eye on a waveform                          | Drift by several frames                                                    | Transcript word times plus silence check                            |
| `index` in a text expression                         | It is the layer index: breaks when layers are added (R24oYxqk8C0 00:11:29) | Use a slider or `textIndex`                                         |
| Layer motion blur on per-character 3D in Advanced 3D | "Motion blur is not supported by the current composition renderer"         | Classic 3D, or CC Force Motion Blur on a precomp                    |
| Shrinking German to fit                              | Tiny type next to the English cut                                          | Rebreak first (`AEX.type.balance`), shrink last                     |
| Font swap with `app.project.replaceFont`             | Not undoable; the next Undo reverts an earlier change                      | `AEK.session.setFont(ps, {map})`, then recheck widths (procedure 7) |
| Range selector keyed for a per-letter overshoot      | Letters stop dead, or all overshoot together                               | `AEX.type.overshoot`                                                |
| Tracking-in from a fixed value                       | Letters off the frame edge on the first frames                             | `AEX.type.trackingFit` at the first key                             |

## Handoffs

- Receives voiceover, music, letter textures and overlays (matted by the text here) from
  scenario-after-effects-generation (Scenario MCP); brief, beats and copy from
  scenario-after-effects-motion-production.
- Receives project and comp settings from scenario-after-effects-project; sends font lists for
  collect and missing-font checks back to it.
- Sends rigs that outgrow a selector (boxes that resize to text, counters) to
  scenario-after-effects-expressions; batch language versions from CSV go to
  scenario-after-effects-scripting as a master comp plus the word JSON.
- Sends a wordmark that must become paths to scenario-after-effects-shape-layers (Create Shapes from
  Text, scripted there).
- Sends 3D text with extrusion and lights to scenario-after-effects-3d; sends easing curves on
  non-text layers to scenario-after-effects-animation.
- Delivers comps to scenario-after-effects-color-delivery for safe areas, render and loudness
  checks.

## Version notes

- 24.3: `TextDocument.characterRange()` and paragraph ranges by script. Earlier: whole-layer styling
  or Source Text keys.
- 24.6: box auto-fit and overflow attributes (`boxAutoFitPolicy`, `boxOverflow`).
- 25.0: per-character style setters in expressions (`text.sourceText.style`, `createStyle`,
  `getStyleAt`); `isPointText` and `isParagraphText`.
- 25.1: `FontObject.hasGlyphsFor()`.
- 26.0: variable font axes in text animators and `addVariableFontAxis`; expression path
  `fontAxisWght`. On 25.x and earlier, variable fonts are static styles only.
- 27.0: Illustrator text imports as editable text layers with fonts and variable-font settings;
  Substance materials apply to 3D text. Text animator match names are the same as in 2026.

## References

- [references/procedures.md](references/procedures.md): every job and expression, with channel,
  checked line and what to check.
- [references/critique.md](references/critique.md): the self-review rubric, numbers and
  contact-sheet checks.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for the same procedures.
- [references/sources.md](references/sources.md): videos and docs, what each is best for.
- [scripts/typography.jsx](scripts/typography.jsx): `AEX.type` helpers (selectors, Amount,
  overshoot, grouping, word markers, phrase layers, in and out, line balance, 3D-aware bounds,
  tracking fit, readability).
- [scripts/word_timings.py](scripts/word_timings.py): transcript word timestamps to frame timings
  with a silence cross-check.
