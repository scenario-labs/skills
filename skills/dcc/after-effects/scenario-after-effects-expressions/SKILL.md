---
name: scenario-after-effects-expressions
description: "Use when writing, fixing, testing or speeding up After Effects expressions or expression rigs: a box that resizes to the text, sourceRectAtTime, lower-third template, second line follows the first, delay or follow-through from one controller, valueAtTime, loopOut, a loop that jumps, seamless wiggle loop, inertial bounce or overshoot, bounce back, counter with thousands separators, toLocaleString, dropdown menu control theme switch, sliders and controller nulls, wiggle that is the same on every layer, seedRandom, posterizeTime, toComp or fromComp, effect point does not follow the layer, text style expressions, highlight a word, JSON or CSV driven text, sourceData, expression error, orange warning banner, expression disabled, renamed layer broke my expressions, old expression does not work in the JavaScript engine, render is slow because of expressions, bake or convert expression to keyframes."
license: MIT
---

# After Effects Expressions

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means a rig that survives the person who edits it next: new text, another frame
rate, a scale, a rename, a nested copy. The agent writes every expression through `AEK.expr.set`,
proves it with numbers read back at several times, and looks at one contact sheet. An expression is
done when its failure cases were measured, not when it evaluates once. If a sibling skill named here
is missing from your available skills, load it with `skill_get` (Scenario MCP) or ask the user to
install it (https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas
and flag the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop,
toolkit, version traps).

## Stance (the expert delta)

- **One controller, every number on it.** A guide null carries Slider, Dropdown and Color controls;
  hidden constants move onto sliders so the next person sees them (Nol Honig and Zack Lovatt,
  VdaGqq4I0qM 00:19:14). Literals are fine only in a one-off.
- **Delays and periods in frames.** `valueAtTime` takes seconds; multiply frames by
  `thisComp.frameDuration` (Evan Abrams, xFT6W9uSwbY 00:06:08). Measured: a 3-frame lag stayed 3
  frames at 24, 30 and 60 fps; a 0.1 s lag became 2.4 frames at 24 fps. A loop period in seconds
  breaks only when `T * fps` is not an integer: 0.7 s repeated exactly at 30 fps and missed by 3.1
  px at 24 and 6.9 px at 25; 2 s was exact at all three [added, measured].
- **Every follower reads the one leader.** All-follow-leader sets each delay directly; chains
  accumulate lag and cost (xFT6W9uSwbY 00:08:34).
- **`sourceRectAtTime` needs left and top, one sample time, and scale.** The text anchor is the
  baseline, so the box position is `[left + width/2, top + height/2]`; width, height, left and top
  share one time; layer scale is not in the rect (Jake Bartlett, CVliDoNgoCg 00:07:50, 00:13:25,
  00:31:27). [added, measured] A parented box scales its padding too: divide padding by the text
  scale.
- **`toComp` survives parenting; `transform.position` does not.** Position is parent space once a
  parent exists (Jake Bartlett, gSq19gpWwSU 00:17:17).
- **Dropdowns return 1, 2, 3; arrays start at 0.** Clamp, then `arr[menu - 1]` (Nic and Kyle
  Hamrick, yG8UbiKKeYw 00:18:31).
- **A loop is judged at its seam, in numbers.** `loopOut("cycle")` jumps unless the last key equals
  the first; a wiggle wrapped in `time % T` jumps every T [added, measured].
- **Text animators run after style expressions.** An animator Fill Color on a range overrides a
  `setFillColor` theme there (Nic and Kyle Hamrick, yG8UbiKKeYw 00:26:08; measured in 27.0). A theme
  switch must drive that animator too.
- **A rename by script does not update expressions.** Measured in 27.0: the text keeps the old name
  and breaks. Rename through `AEX.expressions.renameLayer`, which rewrites the references.

## Establish first

- Expression engine: `app.project.expressionEngine` is `javascript-1.0` by default. A project
  switched to `extendscript` rejects `const` ("a redeclared").
- Frame rate of every comp the rig will be nested in, and whether the rig is duplicated or nested
  (names resolve inside the comp that holds the expression).
- Whether text animates on or off (decides the `sourceRectAtTime` sample time), and whether an
  animator sets Fill Color (decides where the theme color goes) and whether the text layer will be
  scaled or rotated (decides parented versus comp-space box).
- Who edits it: a template for editors needs Essential Properties and an INPUT text layer, never an
  expression-driven Source Text exposed directly (yG8UbiKKeYw 00:20:36).
- Fonts: the rig was measured with Helvetica and Helvetica Bold; check another font with
  `AEK.text.fontExists` before building.
- Channel: bridge by default; handoff produces the same job as one file for a person.

## Procedure

Helper module: `scripts/expressions.jsx` (`AEX.expressions`), loaded with
`ae.py run job.jsx --lib skills/scenario-after-effects-expressions/scripts/expressions.jsx`. It
holds the rig builder, the rig's expressions (`AEX.expressions.CODE`) and the measuring tools:
`probe` (evaluates any expression body and returns JSON), `compRect`, `margins`, `lagFrames`,
`seam`, `atFrames`, `timeEval`, `renameLayer`.

1. **Inspect.** Run the error report (procedures 9): every expression, its error, the engine, plus
   `AEK.expr.check(comp, 5)`. GATE: a list of existing failures before you touch anything.
2. **Build the controller.** `AEK.expr.controls(ctrl, [...])` on a null with `guideLayer = true`;
   name every control. Dropdown items go through the kit (it handles `setPropertyParameters`). GATE:
   no control named "Slider Control 2".
3. **Write each expression with `AEK.expr.set(prop, code, [times])`.** It throws with the engine's
   message, because a broken expression never throws at assignment. For a lower third,
   `AEX.expressions.rig(comp, {name, title})` writes all 19 expressions (procedures 1). GATE:
   `failed` 0.
4. **Measure against the contract (procedures 2).** Box margins with short text, long text, a bigger
   size and 150 % scale; second-line gap with one and two lines; `lagFrames` per follower; `seam` on
   every loop; counter at its first, last and after-last frame; each dropdown item. GATE: the
   numbers in Quality gates.
5. **Break it on purpose.** Change the comp frame rate (or build the rig at 24 and 60), duplicate a
   follower, nest the comp twice with different Theme values through Essential Properties, empty the
   text. GATE: the same numbers; `check` still 0.
6. **Look once.** `AEK.capture.frames` at the move start, mid-move, settle, inside the idle, last
   frame; `ae.py sheet`. GATE: the contact-sheet list in `references/critique.md`.
7. **Cost and baking.** `timeEval` on any property with a loop over samples; bake with
   `AEK.expr.bake` only for delivery targets that cannot run expressions or when evaluation
   dominates render time (procedures 10). GATE: baked values equal the live values at whole frames.
8. **Report** the controls, the layer-name contract, the measured numbers, and any fallback chosen.

## Numbers

| Value           | Measured or source                                                             | Relative to                                                     |
| --------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| Box padding     | 32 px x, 18 px y on all sides                                                  | comp pixels, constant at any text scale with the `/ s` division |
| Second line gap | 14 px from line 1 ink bottom                                                   | comp pixels; descenders add their depth (14 px at 72 px type)   |
| Follow lag      | 3 frames per element                                                           | any frame rate                                                  |
| Inertial bounce | amp 0.05, freq 4, decay 8, window 1 s; 10 to 11 % overshoot, settles in 0.7 s  | seconds after the last key (qXPzt3nNJRI 00:01:18)               |
| Bounce back     | e 0.7, g 5000, nMax 9; 800 px drop rebounds 125 px, 7 to 8 hops                | pixels per second squared (qXPzt3nNJRI 00:04:04)                |
| Seam ratio      | under 2.5 passes; cycle with open keys 27, naive wiggle 16, circular noise 0.8 | median step inside the loop                                     |
| Stepped jitter  | `posterizeTime(4)` holds 6 frames                                              | 24 fps comp (R24oYxqk8C0 00:05:08)                              |
| Film flicker    | `wiggle(24, 0.2)` on exposure                                                  | 24 fps (ZP_eglqgsYE 00:46:16)                                   |
| Evaluation cost | 60-sample loop 48 ms, `smooth(1, 61)` 14 ms, one `valueAtTime` 4 ms            | 120 frames, first pass; cached passes under 1 ms                |
| Auto leading    | `fontSize * 1.2`                                                               | text style `autoLeading` true                                   |

## Quality gates

Measurable:

- `AEK.expr.check(comp, 5)` failed 0, before and after every structure change.
- Box margins equal the padding controls within 0.01 px in four text states; empty text gives a 0
  box.
- `lagFrames` gives N x Lag for follower N at two frame rates.
- `seam` ratio under 2.5 and `repeat` 0 for every idle loop, at the delivery frame rate.
- Counter: "0" at the in point, "1,250,000" from the end of the count onward.
- Dropdown: one palette per item; out-of-range index clamped.
- Same frame evaluated twice gives the same value.
- Baked versus live: under 0.0001 px difference at whole frames.

Visual (one contact sheet): box hugging the ink with even padding, descenders inside; line 2 aligned
on line 1's origin; followers arriving in order; no snap between the last and first frame of a loop;
counter right-aligned with separators; theme colors legible.

## Common mistakes

| Mistake                                                    | Symptom                                            | Fix                                                               |
| ---------------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------- |
| Box position `[w/2, h/2]` only                             | box drifts when font size or justification changes | add `left` and `top` (CVliDoNgoCg 00:09:32)                       |
| `sourceRectAtTime(time)` on animated text                  | box breathes with the animator                     | fixed sample time, same for all four values                       |
| Box parented, padding in pixels                            | padding grows with text scale                      | divide padding by `scale / 100`                                   |
| Delay `time - 0.1`                                         | lag changes with frame rate                        | frames times `thisComp.frameDuration`                             |
| `loopOut()` on keys that do not close                      | jump at every loop                                 | make the last key equal the first, or `pingpong`                  |
| `wiggle(..., time % T)`                                    | jump every T                                       | blended wiggle or circular noise (procedures 3)                   |
| `random()` without `seedRandom(n, true)`                   | value changes every frame                          | seed with `true` for a value held for the whole layer             |
| `posterizeTime` to save render time                        | no saving measured                                 | bake, or reduce samples                                           |
| `setFillColor(c)` with a four-value color                  | outside the documented `[R, G, B]` form            | pass `[c[0], c[1], c[2]]` (text-style doc)                        |
| `setFillColor` on a layer with Fill off                    | no color; reading `fillColor` throws               | `setApplyFill(true).setFillColor(...)`                            |
| Theme on Source Text, animator Fill Color on the same text | some characters keep the old color                 | read the dropdown in the animator's Fill Color too                |
| Padding needed on a box that scales on                     | box builds from the wrong edge                     | Offset Paths, group anchor `[left - o, top - o]` (procedures 1)   |
| Expression banner dismissed                                | later errors never show for a person               | Show Warning Banner back on in Preferences (GUSJhbPwpBE 00:02:35) |
| `toCompVec` for a direction                                | wrong length on a scaled parent                    | point difference `toComp(b) - toComp(a)`                          |
| One-line `if (...) a else b`                               | SyntaxError in the JavaScript engine               | braces or a ternary (GUSJhbPwpBE 00:08:31)                        |
| `sourceText[0]`                                            | silently wrong value                               | `sourceText.value[0]` (GUSJhbPwpBE 00:10:46)                      |
| `layer.name = ...` by script                               | "layer named ... is missing"                       | `AEX.expressions.renameLayer`                                     |
| Precomposing a referenced layer                            | same error in the parent comp                      | point at the precomp layer, or keep references inside one comp    |
| Reading `isAutoLeading`                                    | `undefined`                                        | `autoLeading`                                                     |
| CSV `sourceData`                                           | null                                               | `dataValue([column, row])`, row 0 under the header                |
| Edited JSON shows old text                                 | no refresh                                         | Reload Footage (`mainSource.reload()`)                            |
| `toLocaleString()` without a locale                        | separator depends on the machine                   | pass `"en-US"` or use the regex formatter                         |

## Handoffs

- Receives keyed motion from scenario-after-effects-animation (the leader null, the keys inertia
  reads); returns rigs whose output it can judge in motion.
- Receives text layers and type specs from scenario-after-effects-typography; text animators and
  range selectors stay there, text style expressions are here.
- Shape construction (Offset Paths, Trim Paths, Repeater) comes from
  scenario-after-effects-shape-layers.
- scenario-after-effects-scripting owns CSV and JSON batch versioning, MOGRT export and render
  queues; this skill gives it the rig contract (layer and control names).
- scenario-after-effects-character-rigging uses these patterns for controllers; puppet and IK stay
  there.
- Data rows that need artwork or copy per variant: generated images enter through
  scenario-after-effects-generation.

## Version notes

- `text.sourceText.style` for the whole layer: 17.0. Per-character ranges and most setters: 25.0.
- `previousKey()` and `nextKey()`: 26.0, JavaScript engine only.
- The JavaScript engine is the default since 16.0; Legacy ExtendScript is still selectable in 27.0.
- 27.0 lists no expression changes. Its AI Assistant can explain, write and fix expressions and
  update references after renames; a script rename does not.
- Old expressions with implicit globals (2018 Inertial Bounce) still run unchanged in 27.0.

## References

- [references/procedures.md](references/procedures.md): every job and expression, with what was
  measured.
- [references/critique.md](references/critique.md): the rubric, numbers and contact-sheet checks.
- [references/expert-notes.md](references/expert-notes.md): principles by expert, with timestamps.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for the same steps.
- [references/sources.md](references/sources.md): videos and docs.
- [scripts/expressions.jsx](scripts/expressions.jsx): `AEX.expressions` helpers and the rig builder.
