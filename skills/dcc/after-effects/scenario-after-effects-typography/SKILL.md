---
name: scenario-after-effects-typography
description: "Use when animating text in After Effects: kinetic typography, lyric or voiceover type synced to audio, captions or word-by-word reveals, text animators and range selectors (Offset, Ramp Up, Ease High and Low, Based On), expression selectors and stagger, per-character 3D flips, tracking-in, variable font weight animation, styling one word by script, text on a path, title sequences, or localized versions with longer words. Also when users say 'text does not fit', 'the German version overflows', 'words appear too early', 'my text animation looks cheap', 'the font is missing', 'make it readable', 'time the words to the voiceover'."
license: MIT
---

# After Effects kinetic typography

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert kinetic type is built so that the text can change and the timing can move without rebuilding
anything: animators hold end states, selectors hold motion, markers hold the voice, and in and out
points hold the in and out. An agent never times words by ear: it derives frames from a transcript
with word timestamps, places them by script, and proves readability with numbers before it looks at
one contact sheet. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit,
version traps).

## Stance (the expert delta)

1. **Keys go on the selector, never on the animator property.** The property holds the end offset;
   Offset, Start, End or Amount carries the motion (Jake Bartlett, NclmWZa4c_8 00:01:42). Values are
   relative: 50 % selected gets half (Joey Korenman, b1_p2qQf_Ts 00:09:44).
2. **Pair Shape with its Offset range.** Ramp Up plus Ease Low 100 animates Offset -100 to 100
   (Bartlett 00:04:34). Square animates Offset 0 to 100 [added, measured: from -100 the text starts
   visible, hides, then reveals].
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
- Frame rate: timing numbers are frames at 24 fps unless stated. At 30 fps multiply by 1.25.
- Voiceover file and its script, if there is one. Languages and who supplies the translated text.
- Fonts: confirm each PostScript name with `AEK.text.fontExists` and glyph coverage with
  `fontObject.hasGlyphsFor(text)` (25.1+).
- Template or one-off: a template that people retype needs named animators, centered paragraphs, and
  no index-based expressions.
- Renderer: the same per-character 3D flip rendered in Classic 3D (`ADBE Advanced 3d`, a scripted
  comp's default) and in Advanced 3D (`ADBE Calder`) [added, measured]. In Advanced 3D,
  `layer.motionBlur = true` throws: keep Classic 3D when letters need motion blur. Inter-Character
  Blending and Fill & Stroke options are unavailable on per-character 3D layers (Adobe help).
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
   `word_timings.py --fps 24 --lead 1 --silence silence.log`. GATE: `checks.increasing` true and
   `checks.silence_agrees` true (phrase onsets within 2 frames of a silence end). When they
   disagree, trust the silence boundary for the phrase start. If no transcript tool exists, Convert
   Audio to Keyframes runs by command id with no dialog and gives an amplitude curve (procedure 11).
   Measured on one synthetic 8.5 s voiceover (27 words, 7 phrases): it found 5 of 7 phrase onsets, 0
   to 2 frames late, and missed two pauses of about 5 frames. Use it for phrases, never words.

3. **Lay out phrases.** Goal: a phrase per layer, readable dwell. How:
   `AEX.type.phraseLayers(comp, data, {font, size, fill, position, tail})` creates one centered text
   layer per phrase (in point at the first word, out at the phrase end + `tail` frames), one marker
   per word, and a `reveal` animator driven by the marker expression selector. GATE: marker count
   equals word count, 0 marker-frame mismatches, no `expressionError`; on frames, 0 text pixels
   before the first word.

4. **Design the motion.** Goal: one reusable look per role. How: `AEK.text.animator` plus
   `AEX.type.selector` and `AEX.type.grouping` (procedure 4): character rise, Square one at a time,
   word pop, tracking-in (selector Amount, expo-out). Order the stack: an "Anchor Point Fix"
   animator first, which every later animator inherits (Korenman 00:14:39); an unanimated "initial
   state" animator; one animator per move holding the opposite value, keys 2 to 4 frames apart
   (Korenman 00:05:13, 00:09:44). To keep a sentence centered while words build, add a Position
   animator Based On Lines (Zammit 00:04:42). For a pause, add a middle Offset key at 50 % with a
   flat handle (Zammit 00:14:42). Moving type gets motion blur (Adobe help). GATE: settled frame
   identical to the static text (same `sourceRectAtTime`), keys only on selectors.

5. **Stagger and emphasis.** Goal: order and accents without hand keys. How: an expression selector
   with `textIndex` (procedure 5), a character range for one word's size, color or font (procedure
   7, 24.3+), or the word-picker slider with Units Index (Zammit 00:06:54, 00:07:59). Accent after
   the line lands: Gradient Ramp with Blend With Original keyed 100 to 0 (Zammit 00:16:03).
   Randomize Order needs a non-zero Random Seed to keep its order across duplicates (Adobe help).
   GATE: the emphasized word's range reads back the new font and size; no `index` (layer index) in
   text expressions.

6. **Per-character 3D, when depth is the idea.** Goal: letters that flip or orbit. How:
   `layer.threeDPerChar = true`, THEN add `ADBE Text Rotation X` and a Z position to the animator,
   Grouping Alignment `[0, -50]`, a camera at an angle (procedure 6). For letters that orbit, push
   the anchor back first: a setup animator with `ADBE Text Anchor Point 3D` `[0, 0, 200]`, then Y
   Rotation (Korenman, b1_p2qQf_Ts 00:25:38). GATE: rest frame flat and readable; letters pivot at
   mid cap height.

7. **Variable font motion.** Goal: weight or width that moves. How: `addVariableFontAxis("wght")` on
   the animator properties (procedure 7); expressions read
   `text.animator("weight").property.fontAxisWght`. GATE: width changes across the move (measured
   with `sourceRectAtTime`).

8. **Reusable in and out.** Goal: an animation that follows the layer. How:
   `AEX.type.inOut(layer, {inFrames: 12, outFrames: 10})` puts an Offset expression on `inPoint` and
   `outPoint` (procedure 9). Saving it as a preset is GUI only: select the animator AND Grouping
   Alignment, never Source Text, which carries font and style (Bartlett, NclmWZa4c_8 00:10:34).
   GATE: after sliding and trimming the layer, Offset at `inPoint + 6` frames and `outPoint - 5`
   frames is unchanged.

9. **Localize.** Goal: every language inside title safe at a readable size. How: procedure 8:
   measure point text against 80 % of the frame width; first `AEX.type.balance(layer, maxWidth, 3)`
   (best 1 to 3 line breaks), then `AEK.text.fit` (font size), or a scale-to-fit expression. A
   paragraph box splits a word wider than the box at a wrong point: a 900 px box at 110 px Helvetica
   Bold broke "Geschwindigkeitsbegrenzungen" (1,675 px alone) into Geschwindigkeit / sbegrenzungen,
   `autoHyphenate` true, `boxOverflow` false [added, measured]. One test sentence at 110 px
   Helvetica Bold measured German 171 % and Finnish 139 % of the English width; measure your own
   copy. A second-language voiceover: rerun stage 2; the markers redo the timing. GATE:
   `AEK.text.inFrame(l, c, 0.1, t)` ok at mid-life of every layer; size at or above 80 % of design.

10. **Prove readability.** Goal: a report before any render. How:
    `AEX.type.readability(comp, {bg, minFrames: 18, minCapRatio: 0.035, safe: 0.1, minContrast: 4.5})`
    (procedure 10). GATE: no error findings; warnings justified in the delivery. Then one contact
    sheet per the rubric in [references/critique.md](references/critique.md).

## Numbers

| Item                      | Value                                                                                        | Relative to             |
| ------------------------- | -------------------------------------------------------------------------------------------- | ----------------------- |
| Word lead                 | 1 frame early (0 to 2)                                                                       | spoken onset, 24 fps    |
| Word reveal ease          | 4 frames                                                                                     | per word, 24 fps        |
| Phrase tail               | 6 to 8 frames after the last word                                                            | 24 fps                  |
| Minimum phrase dwell      | 18 frames, and about 6 frames per word                                                       | 24 fps                  |
| Caption pacing (social)   | about 20 characters, 1.2 s minimum, 0 gap, single line (Ryan Connolly, ZCP2W_NTpLE 00:00:14) | per caption             |
| Pop scale                 | 95, 105 (+3 frames), 100 (+2 frames) (Connolly 00:01:21)                                     | percent                 |
| Cap height, running text  | at least 3.5 % of comp height (38 px at 1080)                                                | comp height             |
| Contrast                  | 4.5:1 or more (WCAG ratio)                                                                   | fill vs flat background |
| Safe area for text        | 10 % margin each side                                                                        | comp width and height   |
| Localization shrink floor | 80 % of designed size                                                                        | designed font size      |
| Grouping Alignment        | 0, -50 % caps; 0, -25 % lowercase (Adobe help)                                               | character box           |
| Range Offset              | Ramp Up -100 to 100; Square 0 to 100                                                         | percent of the text     |
| Ease High / Low           | 50 / 50 safe start (Korenman 00:08:40); Ramp Up base: Low 100 (Bartlett)                     | percent                 |
| Variable font wave        | Triangle, End 25 %, Ease High and Low 60, 2 s loop (Bartlett, Tjm3NxPYPqk 00:06:08)          | percent, seconds        |
| Tracking-in               | Tracking 300 to 0 with expo-out (0.16, 1, 0.3, 1) over 20 frames [added]                     | 1/1000 em, 24 fps       |
| Per-character 3D flip     | X Rotation -90, Z -150 px, Offset -100 to 100 over 24 frames [added]                         | degrees, px, 24 fps     |

## Quality gates

- Measurable: every stage GATE above, plus `AEK.audit.summary(AEK.audit.all())` clean for fonts.
- Visual (one contact sheet): words appear in reading order and not before they are spoken; settled
  text sits on its baseline; sentences do not slide while building; pivots on words or characters as
  intended; no word touches the safe margin; the brightest text pixel matches the fill. A 32 bpc
  project saves frames at one tenth of their brightness: read `pngScale` from `AEK.capture.frame`,
  then `ae.py sheet --gain 10`.

## Common mistakes

| Mistake                                              | Symptom                                                                    | Fix                                                                                                                                              |
| ---------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Keyframes on the animator property                   | Retyped text breaks, cascade impossible                                    | Key the selector Offset or Amount                                                                                                                |
| Square with Offset -100 to 100                       | Text visible at frame 0, vanishes, then reveals                            | Square: Offset 0 to 100                                                                                                                          |
| Based On Words, grouping Character                   | Word "scale" shrinks each letter in place                                  | `AEX.type.grouping(l, "word", [0, -25])`                                                                                                         |
| Based On Characters for a cascade                    | Pause at every space                                                       | Characters Excluding Spaces                                                                                                                      |
| One layer per word at speech pace                    | Words flash for 3 to 5 frames                                              | Phrase layers that accumulate words                                                                                                              |
| Timing by eye on a waveform                          | Drift by several frames                                                    | Transcript word times plus silence check                                                                                                         |
| `index` in a text expression                         | It is the layer index: breaks when layers are added (R24oYxqk8C0 00:11:29) | Use a slider or `textIndex`                                                                                                                      |
| Layer motion blur on per-character 3D in Advanced 3D | "Motion blur is not supported by the current composition renderer"         | Classic 3D, or CC Force Motion Blur on a precomp                                                                                                 |
| Shrinking German to fit                              | Tiny type next to the English cut                                          | Rebreak first (`AEX.type.balance`), shrink last                                                                                                  |
| Box text for long compounds                          | The compound is split at a wrong point, `boxOverflow` stays false          | Point text plus `AEX.type.balance`, or a manual break at a morpheme with a hyphen                                                                |
| Missing font accepted silently                       | Substitute font at render                                                  | `AEK.text.fontExists` before writing                                                                                                             |
| Font swap with `app.project.replaceFont`             | Not undoable; the next Undo reverts an earlier change                      | `AEK.session.setFont(ps, {map})` keeps bold runs bold; recheck widths (Georgia to Avenir Next at the same size: -7.4 % to +1.7 % on three lines) |
| Reading an expression selector from a script         | Always 100,100,100                                                         | Judge on frames                                                                                                                                  |
| Turning per-character 3D off and on                  | Layer stays 3D; X and Y rotations reset to 0                               | Keep it on, or rebuild the animator                                                                                                              |
| Variable font animator on a heavy base               | Nothing moves                                                              | Set the base style to the thin end first                                                                                                         |

## Handoffs

- Receives voiceover or music from scenario-after-effects-generation (Scenario MCP), and brief,
  beats and copy from scenario-after-effects-motion-production.
- Receives project and comp settings from scenario-after-effects-project; sends font lists for
  collect and missing-font checks back to it.
- Sends rigs that outgrow a selector (boxes that resize to text, counters) to
  scenario-after-effects-expressions; batch language versions from CSV go to
  scenario-after-effects-scripting as a master comp plus the word JSON.
- Sends 3D text with extrusion and lights to scenario-after-effects-3d; sends easing curves on
  non-text layers to scenario-after-effects-animation.
- Delivers comps to scenario-after-effects-color-delivery for safe areas, render and loudness
  checks.
- Textures inside letters, grain, dust and glitch overlays come from
  scenario-after-effects-generation; this skill mattes them by the text.

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
- [scripts/typography.jsx](scripts/typography.jsx): `AEX.type` helpers (selectors, grouping, word
  markers, phrase layers, in and out, line balance, readability).
- [scripts/word_timings.py](scripts/word_timings.py): transcript word timestamps to frame timings
  with a silence cross-check.
