# Procedures: shape layers by script

Every job is the body of a function run by `ae.py run job.jsx --lib scripts/shapes.jsx` (the
AEX.shapes helper in this skill). Jobs marked `checked: live 27.0` were run in After Effects 27.0.
Jobs that build test content start from `AEK.core.fresh()`, which closes the open project without
saving: in a user's session, skip that line, work inside `--undo "<name>"`, and build on a
duplicate.

```bash
python3 <expert-skill>/scripts/ae.py run job.jsx --lib <this-skill>/scripts/shapes.jsx --undo "Agent: icon draw-on" --args '{"out": "<project>/review"}'
```

The job blocks below ship as files in `scripts/jobs/`: `inspect.jsx` (2), `icon_drawon.jsx` (3),
`stroke_audit.jsx` (4), `burst.jsx` (5), `matte_eye.jsx` (7), `taper_wave.jsx` (8), `morph_fix.jsx`
(9), `vector_intake.jsx` (11), `lottie_prep.jsx` (13). Each was run as shipped on test fixtures.

Two builders, one layer type. `AEK.build.shape(comp, name, spec | [specs])`
(scenario-after-effects-expert kit) makes a new layer of static groups in one call: rect, ellipse,
star or path, with fill, stroke and Trim; the first spec draws on top. `AEX.shapes` (this skill)
adds any item by match name at any depth: Repeater, Merge Paths, Offset Paths, Taper, Wave, nested
groups, and edits to a layer that already exists. Build the base with either, then add operators
with `AEX.shapes.add`.

Frame counts below are at 30 fps unless a case says otherwise; at 24 fps multiply by 0.8 and round.

## Contents

1. Match-name map (shape items, operators, stroke groups)
2. Inspect a shape layer (tree, order warnings)
3. Line icon with a staggered Trim Paths draw-on
4. Icon-set stroke audit against a house style
5. Radial burst (Trim chase plus Repeater)
6. Operator order: Trim and Repeater, Merge modes, Repeater and gradient fills
7. Single-layer matte: Merge Paths Intersect with a linked mask path
8. Stroke Taper and Wave
9. Path morph: first vertex, direction, vertex counts
10. Dot on a path and a follower (`pointOnPath` + `toComp`)
11. SVG and Illustrator intake, Create Shapes from Vector Layer
12. Resolution independence: Collapse Transformations and a constant on-screen stroke
13. Lottie readiness audit and export copy
14. Contact sheets for review
15. Concentric rings and ripples: Repeater Scale versus Offset Paths, a fade by radius, a seamless
    loop or one pass, keyed Repeater Offset
16. Set type to shapes: Create Shapes from Text by script
17. Where a path starts and which way it runs

## 1. Match-name map (dumped live from 27.0)

Add items with `addProperty(matchName)` on a `Contents` group (`ADBE Root Vectors Group` at layer
level, `ADBE Vectors Group` inside a group). `canAddProperty()` returned true for an invented name;
`addProperty()` then threw "asked to create unknown property". Trust the throw, not
`canAddProperty`.

| Item (GUI)         | Match name                       | Leaves (match names, default)                                                                                                                                                                                                                     |
| ------------------ | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Group              | `ADBE Vector Group`              | `ADBE Vector Blend Mode`, `ADBE Vectors Group` (Contents), `ADBE Vector Transform Group`, `ADBE Vector Materials Group`                                                                                                                           |
| Group Transform    | `ADBE Vector Transform Group`    | `ADBE Vector Anchor`, `ADBE Vector Position`, `ADBE Vector Scale`, `ADBE Vector Skew`, `ADBE Vector Skew Axis`, `ADBE Vector Rotation`, `ADBE Vector Group Opacity`                                                                               |
| Rectangle          | `ADBE Vector Shape - Rect`       | `ADBE Vector Shape Direction` 1, `ADBE Vector Rect Size` [100,100], `ADBE Vector Rect Position`, `ADBE Vector Rect Roundness` 0                                                                                                                   |
| Ellipse            | `ADBE Vector Shape - Ellipse`    | `ADBE Vector Ellipse Size` [100,100], `ADBE Vector Ellipse Position`                                                                                                                                                                              |
| Polystar           | `ADBE Vector Shape - Star`       | `ADBE Vector Star Type` 1/2, `... Points` 5, `... Position`, `... Rotation`, `... Inner Radius` 50, `... Outer Radius` 100, `ADBE Vector Star Inner Roundess`, `ADBE Vector Star Outer Roundess` (sic)                                            |
| Path               | `ADBE Vector Shape - Group`      | `ADBE Vector Shape` (a `Shape`, empty on creation)                                                                                                                                                                                                |
| Merge Paths        | `ADBE Vector Filter - Merge`     | `ADBE Vector Merge Type` 1 Merge, 2 Add, 3 Subtract, 4 Intersect, 5 Exclude Intersections                                                                                                                                                         |
| Offset Paths       | `ADBE Vector Filter - Offset`    | `ADBE Vector Offset Amount` 10, `... Line Join` 1, `... Miter Limit` 4, `... Copies` 1, `... Copy Offset` 1                                                                                                                                       |
| Pucker & Bloat     | `ADBE Vector Filter - PB`        | `ADBE Vector PuckerBloat Amount` 10                                                                                                                                                                                                               |
| Repeater           | `ADBE Vector Filter - Repeater`  | `ADBE Vector Repeater Copies` 1, `... Offset` 0, `ADBE Vector Repeater Order` 1/2, `ADBE Vector Repeater Transform`                                                                                                                               |
| Repeater Transform | `ADBE Vector Repeater Transform` | `ADBE Vector Repeater Anchor`, `... Position` [0,0], `... Scale`, `... Rotation`, `ADBE Vector Repeater Opacity 1` (Start), `ADBE Vector Repeater Opacity 2` (End)                                                                                |
| Round Corners      | `ADBE Vector Filter - RC`        | `ADBE Vector RoundCorner Radius` 10                                                                                                                                                                                                               |
| Trim Paths         | `ADBE Vector Filter - Trim`      | `ADBE Vector Trim Start` 0, `... End` 100, `... Offset` 0, `ADBE Vector Trim Type` 1 Simultaneously, 2 Individually                                                                                                                               |
| Twist              | `ADBE Vector Filter - Twist`     | `ADBE Vector Twist Angle` 10, `ADBE Vector Twist Center`                                                                                                                                                                                          |
| Wiggle Paths       | `ADBE Vector Filter - Roughen`   | `ADBE Vector Roughen Size` 10, `... Detail` 10, `... Points` 1/2, `ADBE Vector Temporal Freq` 2, `ADBE Vector Correlation` 50, `ADBE Vector Temporal Phase`, `ADBE Vector Spatial Phase`, `ADBE Vector Random Seed`                               |
| Wiggle Transform   | `ADBE Vector Filter - Wiggler`   | `ADBE Vector Xform Temporal Freq` 2, correlation, phases, seed, `ADBE Vector Wiggler Transform` (`... Wiggler Anchor`, `Position`, `Scale` [0,0], `Rotation`)                                                                                     |
| Zig Zag            | `ADBE Vector Filter - Zigzag`    | `ADBE Vector Zigzag Size` 5, `ADBE Vector Zigzag Detail` 10 (Ridges per segment), `ADBE Vector Zigzag Points` 1/2                                                                                                                                 |
| Stroke             | `ADBE Vector Graphic - Stroke`   | `ADBE Vector Composite Order`, `... Stroke Color`, `... Stroke Opacity`, `... Stroke Width` 2, `... Line Cap` 1 butt 2 round 3 projecting, `... Line Join` 1 miter 2 round 3 bevel, `... Miter Limit` 4                                           |
| Dashes             | `ADBE Vector Stroke Dashes`      | add `ADBE Vector Stroke Dash 1`, `ADBE Vector Stroke Gap 1` (and 2, 3), `ADBE Vector Stroke Offset`                                                                                                                                               |
| Taper              | `ADBE Vector Stroke Taper`       | `ADBE Vector Taper Length Units` 1/2, `... Start Length` 0, `... End Length` 0, `... Start Width` 0, `... End Width` 0, `... Start Ease`, `... End Ease`, hidden `ADBE Vector Taper StartWidthPx`, `EndWidthPx`                                   |
| Wave               | `ADBE Vector Stroke Wave`        | `ADBE Vector Taper Wave Amount` 0, `ADBE Vector Taper Wave Units` 1/2, `ADBE Vector Taper Wavelength` 100, `ADBE Vector Taper Wave Cycles` 10, `ADBE Vector Taper Wave Phase`                                                                     |
| Fill               | `ADBE Vector Graphic - Fill`     | `ADBE Vector Fill Rule` 1/2, `ADBE Vector Fill Color`, `ADBE Vector Fill Opacity`                                                                                                                                                                 |
| Gradient Fill      | `ADBE Vector Graphic - G-Fill`   | `ADBE Vector Grad Type` 1/2, `... Grad Start Pt`, `... Grad End Pt` [100,0], `... Grad HiLite Length`, `... Grad HiLite Angle`, `ADBE Vector Grad Scale`, `ADBE Vector Grad Rotation` (26.0+), `ADBE Vector Grad Colors` (not settable by script) |
| Gradient Stroke    | `ADBE Vector Graphic - G-Stroke` | the gradient leaves plus the stroke leaves, Dashes, Taper, Wave                                                                                                                                                                                   |

Enum labels follow the GUI menu order (1 = first entry). A shape layer reports
`collapseTransformation` true on creation.

## 2. Inspect a shape layer

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), l = AEK.core.layer(c, ARGS.layer);
return { order: AEX.shapes.order(l), tree: AEX.shapes.dump(l) };
```

Check: `order` lists each Contents level top to bottom with warnings when a path sits below a paint
(that paint does not draw it) or an operator sits below a paint. `dump` gives every leaf with value,
expression and key count.

## 3. Line icon with a staggered Trim Paths draw-on

```javascript
// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, c = AEK.core.comp(ARGS.comp);
var l = c.layers.addShape(); l.name = ARGS.name || "icon_home";
l.property("ADBE Transform Group").property("ADBE Position").setValue([c.width / 2, c.height / 2]);
var U = (ARGS.size || 160) / 24; // 24-unit icon grid
function pts(a) { var o = [], i; for (i = 0; i < a.length; i++) { o.push([a[i][0] * U, a[i][1] * U]); } return o; }
var parts = [{ name: "roof", v: [[-10, -1], [0, -9], [10, -1]] }, { name: "walls", v: [[-7, -3], [-7, 9], [7, 9], [7, -3]] }, { name: "door", v: [[-2, 9], [-2, 3], [2, 3], [2, 9]] }];
var STAGGER = 3, DRAW = 12; // frames
for (var i = 0; i < parts.length; i++) {
  var gp = S.group(l, [], parts[i].name);
  S.path(l, gp, pts(parts[i].v), null, null, false);
  S.add(l, gp, "ADBE Vector Filter - Trim", "draw");     // operator after the path, before the paint
  S.stroke(l, gp, { color: [0.08, 0.08, 0.1, 1], width: 2, cap: "round", join: "round" });
  var end = S.contents(l, gp).property("draw").property("ADBE Vector Trim End");
  var f0 = i * STAGGER, k1 = AEK.motion.key(end, AEK.core.time(c, f0), 0), k2 = AEK.motion.key(end, AEK.core.time(c, f0 + DRAW), 100);
  AEK.motion.bezier(end, k1, k2, [0.2, 0, 0, 1]);
}
return { order: AEX.shapes.order(l), walls: AEK.motion.sample(S.contents(l, ["walls"]).property("draw").property("ADBE Vector Trim End"), c, 0, AEK.core.time(c, 20)) };
```

Check: each group reads `Path 1 > draw > Stroke 1`. Measured (30 fps): walls End peaks at frame 5
(920 % per second) and settles at frame 14; nothing renders at End 0 even with a Round cap. On the
sheet: roof first, walls 3 frames later, door last, no stroke wider than the others.

## 4. Icon-set stroke audit

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
return AEX.shapes.strokes(c, { width: 2, cap: "round", join: "round", scaleAware: true });
```

Check: one row per stroke with stored `width`, `onScreen` (width times layer and parent Scale) and
`issues`. Measured: a 2 px stroke on a layer at 200 % reported `onScreen` 4 and an issue; a 3 px
stroke and a Butt cap were flagged. Group Transform Scale is not included: keep group Scale at 100
in icons. Width is read with `valueAtTime` after any expression, so the constant on-screen
expression (procedure 12) is audited on its result. Measured on a layer at 400 %: the plain 2 px
stroke read `onScreen` 8 with an issue; with the expression it read width 0.5, `onScreen` 2,
`expression: true` and no issue. An expression error is still an issue.

## 5. Radial burst

```javascript
// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, c = AEK.core.comp(ARGS.comp), N = ARGS.copies || 12;
var l = c.layers.addShape(); l.name = "burst";
l.property("ADBE Transform Group").property("ADBE Position").setValue([c.width / 2, c.height / 2]);
var gp = S.group(l, [], "spoke");
S.path(l, gp, [[0, -50], [0, -170]], null, null, false);             // one spoke, pointing out from the center
S.add(l, gp, "ADBE Vector Filter - Trim", "chase");
S.add(l, gp, "ADBE Vector Filter - Repeater", "ring").property("ADBE Vector Repeater Copies").setValue(N);
S.contents(l, gp).property("ring").property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Rotation").setValue(360 / N);
S.stroke(l, gp, { color: [0.95, 0.35, 0.1, 1], width: 10, cap: "round" });
var e = S.contents(l, gp).property("chase").property("ADBE Vector Trim End");
AEK.motion.bezier(e, AEK.motion.key(e, 0, 0), AEK.motion.key(e, AEK.core.time(c, 8), 100), [0.2, 0.8, 0.2, 1]);
var s = S.contents(l, gp).property("chase").property("ADBE Vector Trim Start");
AEK.motion.bezier(s, AEK.motion.key(s, AEK.core.time(c, 4), 0), AEK.motion.key(s, AEK.core.time(c, 14), 100), [0.5, 0, 0.3, 1]);
return AEX.shapes.order(l);
```

Check: Copies x Rotation = 360; Repeater Position stays [0, 0]. Sheet at frames 0, 3, 6, 9, 12:
empty, spokes shooting out, full ring, spokes leaving outward, dots, gone. For a spiral, Repeater
Scale compounds: 85 % gives copy 9 at 0.85^9 = 23 %. For evenly spaced rings use Offset Paths
instead (procedure 15).

## 6. Operator order (measured on contact sheets)

| Stack inside one group                                                 | Result                                                                                                        |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Path > Trim (End 50) > Repeater 6 x 60 deg > Stroke                    | six identical half spokes                                                                                     |
| Path > Repeater > Trim (End 50, Simultaneously) > Stroke               | six identical half spokes                                                                                     |
| Path > Repeater > Trim (End 50, Individually) > Stroke                 | three full spokes: copies drawn one after another                                                             |
| Two ellipses > Merge 1 Merge or 2 Add > Fill (Non-Zero)                | same filled union                                                                                             |
| Concentric or overlapping ellipses > Merge 1 > Fill Even-Odd           | the inner circle or the overlap becomes a hole                                                                |
| Same > Merge 2 Add > Fill Even-Odd                                     | one union outline, no hole                                                                                    |
| Two ellipses > Merge 3 Subtract > Fill                                 | first path minus the second (crescent)                                                                        |
| Two ellipses > Merge 4 Intersect > Fill                                | lens                                                                                                          |
| Two ellipses > Merge 5 Exclude Intersections > Fill                    | both minus the overlap                                                                                        |
| Rect, Ellipse > Merge 4 > Stroke > Fill                                | the stroke follows the merged outline (not clipped)                                                           |
| Rect > Repeater 4 > Gradient Fill                                      | one gradient across all copies (compound)                                                                     |
| Rect > Gradient Fill > Repeater 4                                      | each copy carries its own gradient                                                                            |
| Ellipse > Stroke > Repeater 6 (Opacity Start 100, End 0)               | copies fade by index: 100, 84, 67, 50, 33, 17 % (measured brightness 255 to 43); End Opacity is never reached |
| Ellipse > Repeater 6 > Stroke (same Opacity values)                    | no fade: every copy at 100 % (the Stroke paints the merged copies once)                                       |
| Two groups in Contents, or two items in an `AEK.build.shape` spec list | the first one draws on top                                                                                    |

Merge (1) and Add (2) are separate modes. Merge keeps every input as a subpath of one compound path,
so the Fill Rule decides the holes (Even-Odd cuts nested paths and overlaps, like the counter of an
"e"). Add outputs one union outline, so no hole survives. Use Add to unite Repeater copies before a
clip (measured, `r_02`; Adobe operations doc).

To settle an order question, build each variant in its own 400 px comp, save one frame per comp with
`AEK.capture.frame`, and read them on one `ae.py sheet`.

## 7. Single-layer matte (Merge Paths Intersect)

```javascript
// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, c = AEK.core.comp(ARGS.comp);
var E = c.layers.addShape(); E.name = "eye"; E.property("ADBE Transform Group").property("ADBE Position").setValue([c.width / 2, c.height / 2]);
var V = [[-150, 0], [0, -90], [150, 0], [0, 90]], IT = [[0, 0], [-90, 0], [0, 0], [90, 0]], OT = [[0, 0], [90, 0], [0, 0], [-90, 0]];
var dg = S.group(E, [], "stripes");                      // first group draws on top
S.path(E, dg, V, null, null, true, "mask");
var eg = S.group(E, [], "eye white");
S.path(E, eg, V, IT, OT, true, "main");
S.fill(E, eg, [0.9, 0.9, 0.95, 1]);
AEK.expr.set(S.contents(E, ["stripes"]).property("mask").property("ADBE Vector Shape"), 'content("eye white").content("main").path', [0]);
var sg = S.group(E, ["stripes"], "design");
S.set(S.add(E, sg, "ADBE Vector Shape - Rect"), { "ADBE Vector Rect Size": [400, 14], "ADBE Vector Rect Position": [0, -80] });
S.add(E, sg, "ADBE Vector Filter - Repeater", "rows").property("ADBE Vector Repeater Copies").setValue(7);
S.contents(E, sg).property("rows").property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Position").setValue([0, 28]);
S.set(S.add(E, sg, "ADBE Vector Filter - Merge", "add"), { "ADBE Vector Merge Type": 2 });   // Add: the copies become one area before the clip
S.set(S.add(E, ["stripes"], "ADBE Vector Filter - Merge", "clip"), { "ADBE Vector Merge Type": 4 });
S.fill(E, ["stripes"], [0.95, 0.35, 0.1, 1]);
return AEX.shapes.order(E);
```

Check: `stripes` reads `mask > design > clip > Fill 1`; the mask Path carries the expression. On the
frame the stripes stop exactly at the eye outline. Strokes inside the clip are not clipped: draw
them as filled outlines.

## 8. Stroke Taper and Wave

```javascript
// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, l = AEK.core.layer(AEK.core.comp(ARGS.comp), ARGS.layer), gp = ARGS.group ? [ARGS.group] : [];
var st = S.contents(l, gp).property("ADBE Vector Graphic - Stroke");
S.set(st.property("ADBE Vector Stroke Taper"), { "ADBE Vector Taper Start Length": 64, "ADBE Vector Taper End Length": 36,
  "ADBE Vector Taper Start Width": 25, "ADBE Vector Taper End Width": 0, "ADBE Vector Taper Start Ease": 9, "ADBE Vector Taper End Ease": 59 });
st = S.contents(l, gp).property("ADBE Vector Graphic - Stroke");
S.set(st.property("ADBE Vector Stroke Wave"), { "ADBE Vector Taper Wave Amount": 31, "ADBE Vector Taper Wavelength": 186 });
st = S.contents(l, gp).property("ADBE Vector Graphic - Stroke");
AEK.expr.set(st.property("ADBE Vector Stroke Wave").property("ADBE Vector Taper Wave Phase"), "time * -100", [0, 1]);
return S.dump(S.contents(l, gp).property("ADBE Vector Graphic - Stroke"));
```

Check: the widths default to 0 %, so setting only the lengths gives two sharp points. Values from
Sarah Wade (rtt-gGDxrZ4 00:07:28). Reversing the path flips the taper. Wave Units 2 (Cycles) with
`ADBE Vector Taper Wave Cycles` fixes the count of waves along the path regardless of its length.
For a loop, key Phase instead of the expression.

## 9. Path morph

```javascript
// channel: bridge | handoff
// checked: live 27.0
var S = AEX.shapes, l = AEK.core.layer(AEK.core.comp(ARGS.comp), ARGS.layer);
var p = S.contents(l, [ARGS.group]).property(ARGS.path).property("ADBE Vector Shape");
var a = p.keyValue(1), b = p.keyValue(2), report = { countA: a.vertices.length, countB: b.vertices.length };
var n = Math.max(a.vertices.length, b.vertices.length);
if (a.vertices.length < n) { p.setValueAtKey(1, S.resample(a, n)); }      // straight segments only
if (b.vertices.length < n) { p.setValueAtKey(2, S.resample(b, n)); }
if (ARGS.firstVertex) { p.setValueAtKey(2, S.firstVertex(p.keyValue(2), ARGS.firstVertex)); }
if (ARGS.reverse) { p.setValueAtKey(2, S.reverse(p.keyValue(2))); }
report.mid = p.valueAtTime((p.keyTime(1) + p.keyTime(2)) / 2, false).vertices.length;
return report;
```

Check (measured, square to circle, 20 frames): first vertices matched, the mid frame is a rounded
square 180 px wide; first vertex off by two, the shape collapses to 33 px at the mid frame; reversed
direction, it pinches into a bow tie. Triangle (3) to square (4) without resampling morphed cleanly:
After Effects inserted the vertex itself, and the result matched an explicit resample. Lottie still
needs equal counts: resample before export.

## 10. Dot on a path and a follower

```javascript
// expression (JavaScript engine): Shape Layer > Contents > Trim Paths 1 > End
// checked: live 27.0
content("Trim Paths 1").start + 0.1
```

```javascript
// expression (JavaScript engine): any layer > Transform > Position
// checked: live 27.0
var L = thisComp.layer("point"); var g = L.content("Shape 1"); var P = g.content("Path 1").path;
var pct = thisComp.layer("CTRL").effect("Progress")("Slider") / 100;
// group Position minus group Anchor; group Scale and Rotation are not handled
L.toComp(P.pointOnPath(pct) + g.transform.position - g.transform.anchorPoint);
```

Check: drive Trim Start with the same slider. Measured with the group offset by 50 px: the naive
`L.toComp(P.pointOnPath(pct))` sat 50 px off the dot; the compensated one sat within 0.3 px.

## 11. SVG and Illustrator intake

Job file: `scripts/jobs/vector_intake.jsx`.

```javascript
// channel: bridge | handoff
// checked: live 27.0
function imp(path, as) {
  var io = new ImportOptions(new File(path)); if (as) { io.importAs = as; }
  app.beginSuppressDialogs(); try { return app.project.importFile(io); } finally { app.endSuppressDialogs(false); }
}
var R = {}, seen = {}, i;
// SVG as native shape layers: COMP_CROPPED_LAYERS is the only comp mode it accepts, and importFile returns null.
// Project items are not in creation order: compare ids to find the new comp.
for (i = 1; i <= app.project.numItems; i++) { seen[app.project.item(i).id] = true; }
imp(ARGS.svg, ImportAsType.COMP_CROPPED_LAYERS);
for (i = 1; i <= app.project.numItems; i++) { if (!seen[app.project.item(i).id] && app.project.item(i) instanceof CompItem) { R.svgComp = app.project.item(i).name; R.svgLayer = app.project.item(i).layer(1).matchName; } }
// Illustrator file as footage, then try Create Shapes from Vector Layer on that one selected layer
var c = AEK.core.comp(ARGS.comp), foot = imp(ARGS.ai, ImportAsType.FOOTAGE), src = c.layers.add(foot);
for (i = 1; i <= app.project.numItems; i++) { app.project.item(i).selected = false; }
var n0 = c.numLayers, v = c.openInViewer();
if (v) { v.setActive(); }
for (i = 1; i <= c.numLayers; i++) { c.layer(i).selected = false; }
src.selected = true;
app.executeCommand(app.findMenuCommandId("Create Shapes from Vector Layer"));   // id 3973 in 27.0: no dialog, but often no effect
R.converted = c.numLayers > n0;
if (!R.converted) { R.next = "GUI step: select '" + src.name + "' in comp '" + c.name + "', Layer > Create > Create Shapes from Vector Layer"; return R; }
R.newLayer = c.layer(src.index - 1).name; R.srcEnabled = src.enabled;
R.order = AEX.shapes.order(c.layer(src.index - 1));
return R;
```

Check (measured): the SVG comp held one `ADBE Vector Layer` with one group per element (Path, Fill)
and correct colors. `ImportAsType.COMP` is refused for SVG; `FOOTAGE` gives a 200 x 200 raster
still. An Illustrator file imported with `COMP_CROPPED_LAYERS` gives a comp with one footage layer
per Illustrator layer.

Create Shapes from Vector Layer by command id never opened a dialog, but it converted in only 8 of
35 attempts across 12 jobs. It failed silently in the other runs with the comp active and only the
layer selected, so the cause is GUI state a script cannot see. When it worked, it added
`<name> Outlines` above the source with the source Scale, one group per path (Path + Fill or Path +
Stroke), and colors kept. It also switched the source off; the source did not become a guide. Treat
the conversion as a GUI step: run the job, read `converted`, and hand `next` to a person when it is
false. For SVG art, the native SVG comp import is the reliable scripted route.

Intake routes by version (Adobe What's New pages, 26.0 to 27.0):

| Source                                      | Route                                                                                                                                                       | Version          | Result                                                                                                  |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------- |
| SVG file                                    | Import, `COMP_CROPPED_LAYERS` (scripted above)                                                                                                              | 26.0+            | native shape layer, one group per element                                                               |
| SVG file                                    | Import as comp or as footage                                                                                                                                | 26.2+            | footage is a raster still: avoid for animation                                                          |
| Illustrator or SVG content on the clipboard | Edit > Paste in a comp (GUI)                                                                                                                                | 26.3+            | native, editable shape layers                                                                           |
| `.ai` layers                                | Import, Composition - Retain Layer Sizes, then Create Shapes from Vector Layer                                                                              | all              | footage layers, then shapes (conversion is a GUI step, see above)                                       |
| Figma frame                                 | Overlord transfer; for a mobile frame (393 x 852) double the comp first (Jake Bartlett, I6QlicggqtY 00:11:17)                                               | plugin           | shape layers, video master only                                                                         |
| Illustrator text                            | Import as editable text layers: fonts, size, fills, positions, styles and variable font settings kept (Adobe help, Import SVG files > editable text layers) | 27.0             | text layers for scenario-after-effects-typography                                                       |
| Illustrator paths, before 26.3              | Paste onto a selected solid                                                                                                                                 | 26.2 and earlier | mask paths in Difference mode: letter counters vanish in a Lottie export (Daniel, HZ1_afAjVb0 00:02:48) |

Prepare the `.ai` before import (Megan Friesth, qV3KXRrGm-A):

- One element per layer. Release to Layers leaves the new layers nested inside the parent: drag them
  out, or they import as one (00:03:57).
- Leave a few empty spare layers: a linked Illustrator file never receives new layers (00:09:27).
  Remove unused layers in the comp, not in the `.ai` (00:19:08).

## 12. Resolution independence

```javascript
// expression (JavaScript engine): Shape Layer > Contents > Group > Stroke > Stroke Width
// checked: live 27.0
// constant on-screen width through layer and parent scale (not through group Transform scale)
var px = 2;
var s = length(toComp([0, 0]), toComp([1, 0]));
s > 0 ? px / s : value;
```

Check (measured at 400 %): the plain stroke rendered 8 px; with the expression 2 px, also under a
parent at 200 % and a layer at 200 % (stored value 0.5). A shape layer is vector at any scale. A
precomp layer at 400 % with Collapse Transformations off rendered soft edges (8 to 16 transition
pixels); on, crisp (0). SVG footage at 200 % was soft with the switch off and crisp with it on. Set
it by script: `layer.collapseTransformation = true`.

## 13. Lottie readiness audit

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var before = AEX.shapes.lottie(c);
var dup = c.duplicate(); dup.name = c.name + "_lottie";          // never fix the master
for (var i = 1; i <= dup.numLayers; i++) {
  AEK.core.walk(dup.layer(i), function (p) {
    if (p.propertyType === PropertyType.PROPERTY && p.canSetExpression && p.expression && p.expressionEnabled) { AEK.expr.bake(p, dup, 0, dup.duration); }
  });
}
return { before: before, after: AEX.shapes.lottie(dup) };
```

Check: findings `{severity, where, what}`, by severity:

- `drop`: camera, light, adjustment, guide, audio, expressions, most effects.
- `partial`: 3D, luminance track matte, text animators, text on a path, gradients, time remap.
- `check`: every text layer (basic text is supported, but the font is referenced by name: it must
  exist in the runtime, or outline it with Create Shapes from Text); Merge Paths, Taper, Wave and
  path operators, which the compatibility matrix does not list.
- `size`: stills embed as base64.

Measured: a test comp gave 13 findings; after baking one expression (61 keys for 2 s at 30 fps) and
switching off the adjustment, camera and guide layers, the `drop` rows were gone. Basic, animated
and on-path text layers returned one `check` each, plus one `partial` for the animator and one for
the path. The export itself runs in the Bodymovin or LottieFiles panel (GUI). Compare the player
against an After Effects frame at the same time.

Size: no source gives a pixel size for a Lottie comp. The player scales the vector, so a stroke
changes width with the display size. Find the size the app shows the animation at, set the comp to
it (or a whole multiple), and check the 2 px stroke on a device capture.

## 14. Contact sheets

```bash
python3 <expert-skill>/scripts/ae.py frames "icon_home" --times 0,0.067,0.133,0.233,0.333,0.6 --out <project>/review --sheet
```

Check: in a 32 bpc project, `saveFrameToPng` wrote colors far too dark (0.95, 0.4, 0.1 came out 24,
10, 2). Every value is divided by 10 in a 32 bpc PNG (white reads 0.1). Review frames from an 8 or
16 bpc project, build the sheet with `ae.py sheet ... --gain 10`, or render through the render
queue. A new project inherits the bit depth of the one before it.

## 15. Concentric rings and ripples

Channel: bridge. Two ways to make rings from one ellipse, measured on 27.0 with a 48 px radius:

- Repeater Scale 125 % gives radii 48, 61, 77, 96, 121, 151: each copy is the last times 1.25, so
  the gaps grow. Repeater Offset 1.5 scaled every radius by 1.25^1.5.
- Offset Paths, Amount 30, Copies 6, gives radii 48, 78, 108, 138 and on: even 30 px gaps. Copy
  Offset reads 1 by default, has no min or max, and moves every ring by Amount times its change (0.5
  moved them 15 px).

Repeater opacity fades by copy index, never by radius, and only when the paint sits above the
Repeater (procedure 6). For a fade by radius, matte the rings with a feathered mask. A mask feather
of F spreads the edge about F px on each side of the path. Radius 200 and feather 50 measured alpha
255 at 140 px and less, about 46 % at 200 px, about 0 at 240 px. A Subtract mask gives the inverse.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
// rings every 30 px from radius 50, 7 copies, 1 ring per second outward, faded over 30 px at both ends
var r = AEX.shapes.ripple(c, "waves", { center: [300, 300], r0: 50, spacing: 30, copies: 7, width: 4, ringsPerSecond: 1, fade: 30 });
return { ripple: r, matteOn: AEK.core.layer(c, "waves_fade").enabled };
```

`ripple()` builds an ellipse, Offset Paths (Amount = spacing, Copies) and a Stroke, with the Copy
Offset expression `(time * ringsPerSecond) % 1`. The matte is a solid `<name>_fade` with an outer
feathered mask at `rMax - fade` and an inner Subtract mask at `r0 + fade`, where
`rMax = r0 + copies * spacing`. `setTrackMatte` switches the matte layer off by itself (`matteOn`
false). Returns `{layer, matte, rMin, rMax, spacing, loopFrames}`.

Measured at 30 fps: even 30 px spacing; frame 0 and frame 30 byte-identical, so the loop is seamless
at `loopFrames` 30; rings fade in at the center and out at the rim. In a logo build with spacing 46
and 0.5 rings per second, `loopFrames` read 60.

One pass instead of a loop, and a matte that is itself a shape layer:

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
// rings leave once over 36 frames from frame 0; Copy Offset keyed 0 -> 7 (every ring passes the rim), no expression
var r = AEX.shapes.ripple(c, "waves", { center: [400, 400], r0: 50, spacing: 40, copies: 7, width: 6, fade: 40, matte: "shape", once: { start: 0, frames: 36 } });
return r;
```

`once: {start, frames, travel}` keys Copy Offset from 0 to `travel` (default `copies`) with (0.2, 0,
0, 1); `loopFrames` returns null. `matte: "shape"` builds the matte as a shape layer: an outer
ellipse at `rMax - fade`, an inner one at `r0 + fade`, Merge Paths Subtract, a white Fill and
Gaussian Blur (`ADBE Gaussian Blur 2`, Blurriness = `fade`, Repeat Edge Pixels off). Measured along
a radius with `fade` 40: solid matte alpha 26, 155, 251 at 80, 100, 120 px and 237, 127, 15 at 260,
280, 300 px; shape matte 12, 180, 255 and 255, 162, 8 at the same radii. `matte: "none"` adds no
matte.

Keyed Repeater Offset. Measured with 3 copies at Repeater Scale 160 %, no motion blur, one frame per
row: an Offset keyed upward through 0 to 0.06 drew a fourth copy (the copy at index Copies, at full
brightness) on every third frame. Fixed values in that range drew three copies, and so did keys
between 0.2 and 0.224, between 0.99 and 1.024, and below 0. Under motion blur only some samples
carry the extra copy, so it reads as a faint ghost ring. Two fixes: key the Ellipse Size and the
Repeater Scale instead (Size 190 to 400 with Scale 160 to 185 %: 3 rings on each of the 29 frames
across the move, counted along a radius without blur), or keep the keyed Offset at 0.1 or above
(values from 0.074 to 1.45 measured clean).

Trim Paths with Start and End equal draws nothing, at 0 and at 50 alike, with Round, Butt or
Projecting caps (measured, 24 px stroke). A draw that starts on frame 0 with motion blur at phase
-90 still shows a faint stub on frame 0: the shutter samples half a frame ahead, into the move.
Measured on a both-ways ring draw (Start 50 to 0, End 50 to 100, 22 frames, (0.2, 0, 0, 1)): 480 px
lit, peak 112 of 255, at phase -90; nothing with blur off or at phase -180. Start the draw on frame
1 when frame 0 must be empty.

## 16. Set type to shapes: Create Shapes from Text

Channel: bridge. The menu command (id 3781 in 27.0) runs with no dialog on the selected text layer.
It needs the comp open in the viewer and active: measured, 16 of 16 conversions with
`openInViewer()` and `setActive()`, 0 of 3 without.

```javascript
// channel: bridge
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), t = AEK.core.layer(c, ARGS.layer), i;
var v = c.openInViewer(); if (v) { v.setActive(); }   // without the active viewer the command does nothing, silently
for (i = 1; i <= c.numLayers; i++) { c.layer(i).selected = false; }
t.selected = true;
var n0 = c.numLayers;
app.executeCommand(app.findMenuCommandId("Create Shapes from Text"));
if (c.numLayers === n0) { return { converted: false, next: "GUI step: select '" + t.name + "', Layer > Create > Create Shapes from Text" }; }
var s = c.layer(t.index - 1);   // the new layer sits right above the source
return { converted: true, layer: s.name, sourceOn: t.enabled, order: AEX.shapes.order(s) };
```

Measured on "TONDA" in Avenir Next Bold 200 px: a layer `<text layer> Outlines`
(`ADBE Vector Layer`) above the source, at the source Position, with the same `sourceRectAtTime`
bounds; the source switched off. One group per character, named by the letter; each holds its
outline paths (two for O, D and A, with Merge Paths for the counter), then Stroke, then Fill. The
text stops being editable: keep the source layer, off. "Create Masks from Text" (id 2933) gives one
solid with 8 masks for the same word. Every group is a normal shape group: Trim the Stroke for a
draw-on, then fade in the Fill.

Draw-on on these outlines. Add Trim Paths to each letter group and move it just above the Stroke
(`trim.moveTo(strokeIndex)`), so it trims the merged outline; key End 0 to 100, then the Fill
Opacity 0 to 100 about 10 frames later. Hold each group's Opacity at 0 (Hold keys) until its draw
starts: at Trim End 0 a merged letter outline still left a 3 px speck on frame 4 (the D and the A),
and so did Repeater copies trimmed Individually. With the hold, frame 4 read clean. Measured in the
rebuilt TONDA lockup: 5 letter groups (T, O, N, D, A), stroke 3 px round, fill fading from 10 frames
after each draw start; the word measured 673 px wide at Avenir Next Demi Bold sized to fit, the
lockup 922 px (60 % of the safe width).

## 17. Where a path starts and which way it runs

Trim Paths reads from the path's first vertex in its direction. Measured with Trim End 10 on a 20 px
stroke:

- Ellipse: starts at the top (12 o'clock) and runs clockwise; the first 10 % covered x 0 to 122 px
  right of center at the top.
- Shape Direction 3 (reversed) on the same Ellipse: starts at the top and runs counterclockwise.
- Rectangle 400 x 400: starts at the top-right corner and runs down the right edge (159 px for 10 %
  of 1,600).
- Polygon (Polystar Type 2, 6 points): starts at the top vertex and runs clockwise.

So an arc centered on the right of an ellipse is Start 12.5 to End 37.5 (3 o'clock at 25 %), and
Start 50 to 0 with End 50 to 100 draws an ellipse both ways from the bottom (6 o'clock at 50 %).
Rotate the group 180 degrees to start from the top.
