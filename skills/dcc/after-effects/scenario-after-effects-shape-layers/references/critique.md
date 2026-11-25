# Critique: judge your own shape work before showing it

Run the measurable checks first, then read one contact sheet. A result that fails a measurable gate
is not shown.

## Measurable (numbers from jobs)

| Check                | How                                                                         | Pass                                                                                                                                                |
| -------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Structure            | `AEX.shapes.order(layer)`                                                   | No warning; each group reads paths, operators, then paint                                                                                           |
| Draw order           | First group in Contents                                                     | The group meant to be on top is listed first                                                                                                        |
| Stroke style         | `AEX.shapes.strokes(comp, {width, cap, join, scaleAware: true})`            | Every row has empty `issues`; on-screen width equals the spec (for example 2 px at 1080p)                                                           |
| Group scale in icons | `dump` rows `ADBE Vector Scale`                                             | [100, 100] unless a stroke compensation covers it                                                                                                   |
| Trim draw-on         | `AEK.motion.sample(End)`                                                    | 0 then 100, eased (no linear keys), settles inside the planned frames; stagger between groups as planned (3 frames at 30 fps in the reference icon) |
| Trim dot             | End expression `start + 0.1`; cap                                           | Round cap; dot length 0.1 %                                                                                                                         |
| Repeater ring        | Copies x Rotation                                                           | Exactly 360; Repeater Position [0, 0]                                                                                                               |
| Repeater scale       | 0.85^n style check                                                          | Smallest copy still visible at delivery size                                                                                                        |
| Even rings           | Offset Paths Amount, or `ripple().spacing`                                  | Equal gaps between rings; Repeater Scale gives growing gaps (s^n)                                                                                   |
| Ripple loop          | Frame 0 against frame `loopFrames`                                          | Byte-identical, or no visible jump on the sheet                                                                                                     |
| Merge clip           | `order` of the clip group                                                   | mask path, design sub-group (with its own Merge Paths set to Add, 2, if it holds a Repeater), Merge Intersect, Fill                                 |
| Taper                | Lengths and widths                                                          | Widths set (default 0 % gives points); for a full brush stroke Start + End Length = 100 (64 + 36); less leaves a full-width section                 |
| Wave loop            | Phase                                                                       | Keyed with first value = last value when the clip loops                                                                                             |
| Morph                | `morph_fix` report                                                          | Equal vertex counts on both keys; mid-frame width close to the end states (a collapse to a fraction means first vertex or direction is wrong)       |
| Expressions          | `AEK.expr.check(comp, 5)`                                                   | No errors                                                                                                                                           |
| Resolution           | `layer.collapseTransformation`                                              | true on precomps and vector footage scaled above 100 %; shape layers report true by default                                                         |
| Lottie               | `AEX.shapes.lottie(exportCopy)`                                             | No `drop` rows; every `check` row tested in the target player or removed                                                                            |
| Lockup size          | Union of the lockup layers' `sourceRectAtTime` through `toComp` at the hold | 50 to 70 % of the safe width (80 % of the frame), unless the brief sets a size; under 50 % reads as a small mark lost in the frame                  |
| Wordmark letters     | Source of the letter paths                                                  | Converted from set type (procedure 16), with the face named; letters drawn by hand only when the brief asks for custom lettering                    |
| Repeater copies      | Rings counted on every frame of a keyed Repeater, from the frames           | Never more than Copies; a keyed Offset stays at 0.1 or above (procedure 15)                                                                         |
| Hold                 | Frames after the last draw                                                  | The resolved lockup holds at least 1.5 s with a secondary action (dot breathing 2 to 4 %, a slow ring) or a clean stop the brief asks for           |

## Visual (one contact sheet)

Capture from an 8 or 16 bpc project: in 32 bpc, `saveFrameToPng` writes every value divided by 10
(white reads 0.1). If the project must stay at 32 bpc, build the sheet with
`ae.py sheet ... --gain 10`. A new project inherits bit depth from the one before it: set
`app.project.bitsPerChannel` first.

| Look for                                                             | Means                                                                                                                  |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Stroke weights differ between icons of one set                       | Layer or parent scale changed the stroke; use the constant-width expression or build at final size                     |
| A stroke edge is soft or stair-stepped at large scale                | A precomp or vector footage with Collapse Transformations off                                                          |
| A morph passes through a thin sliver or a bow tie                    | First vertex or path direction mismatch                                                                                |
| Stripes or pattern spill outside the mask                            | Merge order wrong, or the Intersect sees the copies unmerged                                                           |
| The pattern disappears entirely inside a clip                        | A Repeater without its own Merge Paths inside the clip group                                                           |
| A stroke outlines the clipped shape                                  | Expected: Intersect clips fills only; draw the stroke as a filled outline                                              |
| A burst ring has a gap or a double spoke                             | Copies x Rotation is not 360, or Repeater Position is not 0                                                            |
| A tapered end shows a lump                                           | A gap between Start Length and End Length (Sarah Wade, rtt-gGDxrZ4 00:06:22)                                           |
| Fat and thin ends swapped, wave runs inward                          | Reverse Path Direction flipped the path: drop the minus sign in the Phase expression (Sarah Wade, 00:12:22)            |
| A hole appears or disappears after Merge Paths                       | Merge (1) follows the Fill Rule (Even-Odd cuts overlaps); Add (2) never leaves a hole                                  |
| A dot or line lags the object it follows                             | Follower ignores the group Transform; add group Position minus Anchor                                                  |
| Line ends look square on a draw-on                                   | Cap is Butt; icon sets usually want Round                                                                              |
| Copies fade in the wrong direction                                   | Start and End Opacity swapped, or Composite Above versus Below                                                         |
| Repeater copies do not fade at all                                   | The Stroke or Fill sits below the Repeater; move the paint above it, or matte by radius                                |
| A faint extra ring outside the last Repeater copy for a frame or two | A keyed Repeater Offset between 0 and 0.06: key Size and Repeater Scale instead                                        |
| An arc or partial ring sits on the wrong side                        | Path start or direction assumed: Ellipse starts at the top and runs clockwise (procedure 17)                           |
| Letters look like plain geometry (circle O, triangle A)              | Drawn by hand: convert set type with Create Shapes from Text                                                           |
| A 3 px speck where a letter or ring will draw, frames early          | Trim End 0 on a merged outline or a trimmed Repeater: hold the group Opacity at 0 until its draw starts (procedure 16) |
| A faint stub shows on frame 0 of a Trim draw that starts on frame 0  | Motion blur at phase -90 samples half a frame into the move; start the draw on frame 1                                 |

## Severity

- Block: a `drop` Lottie row on an export copy, an expression error, a stroke off spec in an icon
  set, a morph that collapses.
- Fix before review: linear keys on a draw-on, a ring gap, a soft edge at delivery size.
- Note: `check` rows still awaiting a playback comparison in the target player.
