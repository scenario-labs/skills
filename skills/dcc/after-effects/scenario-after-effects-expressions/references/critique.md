# Critique: judge an expression rig before calling it done

Score every line. A rig ships only when every "must" passes. Numbers come from `AEX.expressions`
(scripts/expressions.jsx) and `AEK.expr`; pictures come from one contact sheet (`ae.py sheet`).

## Must pass (measured)

| Check                           | How                                                                                                                        | Pass                                                                                                                                              |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| No expression errors            | `AEK.expr.check(comp, 5)`                                                                                                  | `failed` is 0 at 5 times across the comp                                                                                                          |
| Errors after a structure change | rerun `AEK.expr.check` after any rename, precompose, duplicate, version load                                               | still 0                                                                                                                                           |
| Box margins                     | `AEX.expressions.margins(compRect(BOX), compRect(TXT_1))` with short text, long text, a bigger font size, text scale 150 % | each margin equals the padding control within 0.01 px                                                                                             |
| Empty text                      | set Source Text to ""                                                                                                      | box size 0 (or the box is hidden), never a padding-only sliver                                                                                    |
| Second line gap                 | `compRect(TXT_2).top - compRect(TXT_1).bottom` with one line, two lines, descenders                                        | equals Gap within 0.01 px                                                                                                                         |
| Follow-through                  | `AEX.expressions.lagFrames(leader, follower, ...)` per element, at the delivery frame rate and one other                   | N x Lag frames for element N at every frame rate                                                                                                  |
| Loop seam                       | `AEX.expressions.seam(prop, comp, periodFrames, start)`                                                                    | `ratio` (seam step / median step) under 2.5; `repeat` 0 for an idle that must loop exactly                                                        |
| Counter                         | Source Text at frame 0, at the end of the count, one frame before it, after it                                             | "0", "1,250,000" at and after the end, below it one frame before                                                                                  |
| Theme                           | set the dropdown to each item, read the fills                                                                              | one distinct palette per item; out-of-range index clamps                                                                                          |
| Text theme                      | read `TextDocument.fillColor` and `applyFill` per item; list the text animators with a Fill Color                          | three values per item, `applyFill` true; no animator Fill Color on a themed range, or that animator reads the same dropdown                       |
| Determinism                     | evaluate the same frame twice                                                                                              | identical values (no `Math.random`, `random()` seeded with `seedRandom(n, true)` when it must hold)                                               |
| Frame rate                      | rerun the timing checks at 24, 30, 60 fps                                                                                  | delays and loop periods stay whole frames                                                                                                         |
| Cost                            | `AEX.expressions.timeEval(prop, comp, 120)`                                                                                | no single property above about 50 ms for 120 evaluations; anything above it gets fewer samples or a bake (`posterizeTime` did not lower the cost) |
| Bake                            | `AEK.expr.bake` then compare `atFrames` before and after                                                                   | difference under 0.0001 px at whole frames; expression text kept, disabled                                                                        |

## Should pass (judgment)

- Every constant a designer may change is a named control on the guide null (Pad X, Pad Y, Gap, Lag
  (frames), Idle (frames), Theme), and every control name is referenced by name, never by index.
- Controls are renamed from "Slider Control 2" to a meaning.
- Text-driven boxes sample `sourceRectAtTime` at a time where the text is fully visible when the
  text animates on or off.
- Delays and periods are in frames on the controls; seconds appear only after
  `* thisComp.frameDuration`.
- No layer read by index (`thisComp.layer(3)`), no `thisComp.layer(index - 1)` chains on more than a
  handful of layers.
- The expression warning banner is on (Settings > Scripting & Expressions > Show Warning Banner)
  while a person reviews the rig: once dismissed it hides every later error in the app (GUSJhbPwpBE
  00:02:35). Scripted checks read `expressionError` and do not depend on it.
- Legacy syntax is rewritten when the rig is meant to be edited later (`var` to `const`, implicit
  globals declared), even though it still runs.

## Contact sheet (4 to 6 frames)

Take frames at: the first frame of the move, mid-move, the settle, a frame inside the idle, and the
last frame. Look for:

- the box hugging the ink with even padding on all four sides, descenders inside;
- the second line left-aligned on the first line's text origin, never overlapping it;
- bars arriving one after another, evenly spaced in time, no element arriving early;
- the idle dot not snapping between the last and the first frame of the loop (compare the last frame
  and the first);
- the counter right-aligned, separators in place, no clipped digit;
- theme colors legible: text against the plate, accent against the background.

## Red flags that fail the rig at once

- The orange error banner, or `expressionError` not empty on any property.
- A value that differs between two renders of the same frame.
- A box that collapses to padding when the text is empty, or that jumps on the first frames of a
  text animator.
- A rendered loop whose period in seconds is not a whole number of frames at the delivery rate
  (`T * fps` not an integer, for example 0.7 s at 24 or 25 fps): frame N differs from frame 0, so
  the file jumps at every repeat. A 2 s period is whole at 24, 25 and 30 fps.
- A theme switch that leaves some characters in the old color: a text animator Fill Color covers
  them, and animators run after style expressions.
