# Critique rubric: kinetic type

Judge every piece with numbers first, then one contact sheet. Frame counts are at 24 fps; at 30 fps
multiply by 1.25 and round.

## Measurable (from a job)

| Check               | Pass                                                                                                                                                                   | How                                                                                                  |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Fonts               | Every `TextDocument.font` passes `AEK.text.fontExists`; `app.fonts.missingOrSubstitutedFonts` empty in a fresh session                                                 | `AEK.audit.fonts()`                                                                                  |
| Glyph coverage      | `fontObject.hasGlyphsFor(text)` true for every language version (25.1+)                                                                                                | job in procedures.md, case 1                                                                         |
| Sync                | One marker per word, marker k at word k's `f0`, frames strictly increasing; 0 mismatches                                                                               | case 3 check loop                                                                                    |
| Lead                | Words appear 0 to 2 frames before the spoken onset, never after                                                                                                        | `--lead` in `word_timings.py` (default 1)                                                            |
| Transcript vs audio | Phrase onsets within 2 frames of an ffmpeg `silence_end`                                                                                                               | `checks.silence_agrees`                                                                              |
| Dwell               | At least 18 settled frames (at rest, 100 % opacity) and about 6 per word; a word-synced phrase layer counts its time on screen                                         | `AEX.type.readability`, rule `dwell`; `AEX.type.settled`                                             |
| Size                | Cap height at least 3.5 % of the frame's short side (38 px at 1080, the same in 16:9, 9:16 and 1:1) for running text; titles larger                                    | rule `size`                                                                                          |
| Contrast            | Every color run vs background at least 4.5:1 (WCAG ratio) on flat backgrounds; over footage the worst sampled cell counts; add a stroke, shadow or plate when it fails | rule `contrast`, rows `runs` and `backdrop` (`sample: true`)                                         |
| Safe area           | Text bounds inside 80 % of the frame width and height (10 % margins) at mid-life of each layer                                                                         | rule `safe`, `AEK.text.inFrame(l, c, 0.1, t)` for 2D (parents count), `AEX.type.inFrame` for 3D text |
| Localization        | Every language fits at 80 % or more of the designed size, or was rebroken into at most 3 lines                                                                         | case 8                                                                                               |
| Overshoot           | Per-character overshoot passes rest by the set percent (8 % by default) and settles within the settle frames; no letter rests off its baseline                         | `sourceRectAtTime` per frame on a one-letter copy, procedures.md 5b                                  |
| Selector keys       | Keys sit on selectors (Offset, Start, End, Amount), not on animator properties; Square uses Offset 0 to 100, Ramp Up -100 to 100                                       | `AEK.motion.keys` on each selector                                                                   |
| Names               | No "Animator 1" or "Range Selector 1" left in a delivered template                                                                                                     | walk `ADBE Text Animators`                                                                           |
| Expressions         | `expressionError` empty on every selector and Amount after one `valueAtTime`                                                                                           | `AEK.expr.check(c, n)`                                                                               |
| Layout idea         | One sentence names what is biggest, what aligns to what, what moves last; a centered stack has a stated reason                                                         | `AEX.type.layout`, rule `stack`                                                                      |
| Scale contrast      | Title to supporting line 3:1 or more in type size                                                                                                                      | rule `scale`                                                                                         |
| Hold                | Something moves through the hold without unsettling the letters (parent push 2 to 4 %), unless the brief asks for a dead stop                                          | rule `hold`                                                                                          |
| Retime safety       | In and out animations read the same values at `inPoint + n` and `outPoint - n` after sliding and trimming the layer                                                    | case 9                                                                                               |

## Visual (one contact sheet)

Pick frames: just before the first word, at each word onset + 4 frames inside one phrase, the last
frame of each phrase, mid-exit.

- Reveal order matches reading order; no word appears more than 2 frames before it is spoken.
- Settled text sits on its baseline: no character left raised, rotated or transparent at rest.
- The sentence does not jump sideways while it builds (center alignment with words revealed in
  place).
- Scale and rotation pivot on each word or character, not on the line (Anchor Point Grouping matches
  Based On).
- Per-character 3D: letters rotate from their x-height with depth, no letter clipped or mirrored at
  rest.
- Tracking-in: the line ends at its designed tracking, letters never overlap during the move, and no
  letter leaves the frame on the first frames (`AEX.type.trackingFit`).
- Mixed formats: judge each aspect ratio on its own sheet, or at the same frame height. A 9:16 frame
  in a 16:9 tile shows at 56 % of the scale of a 16:9 frame (225 / 1920 against 400 / 1920), so its
  type looks smaller than it is. Size is measured, not judged by eye: cap against the short side.
- Longer language: no word hits the safe margin, line breaks fall between meaning units, no orphan
  single short word on the last line.
- Brightness sanity: the brightest text pixel is near the fill color. A dim frame means a capture or
  color-setting problem, not a design verdict: a 32 bpc project saves PNG frames at one tenth of
  their brightness (`pngScale` 0.1, see the frame check in procedures.md).
- Per-character 3D in an Advanced 3D comp (`ADBE Calder`) has no layer motion blur: judge mid-move
  frames for strobing, or switch to Classic 3D.
- Motion variety: letters do not all travel the same distance on the same curve (`order`, `vary` in
  `AEX.type.overshoot`), and the supporting line moves differently from the title.
- Accent: one accent is enough only when it lands on the idea of the line; an accent that is only a
  color on the last word reads as decoration.
- Pauses and accents: a phrase that holds before the rest (middle Offset key at 50 %) reads as a
  pause, not a stall; an accent lands after the line settles, not during the build.

## Severity

- error: text outside the safe area, contrast under 3:1, a word shown after it is spoken, missing
  font or glyph.
- warn: dwell under the minimum, size under the minimum, unnamed animators, contrast 3:1 to 4.5:1, a
  centered stack without a stated idea, scale under 3:1, a static hold.
- note: style choices (ease values, unit choice) that the brief did not fix.
