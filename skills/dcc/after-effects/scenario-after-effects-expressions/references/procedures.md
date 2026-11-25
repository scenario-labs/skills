# Procedures: expression rigs

Jobs run through
`ae.py run job.jsx --lib skills/scenario-after-effects-expressions/scripts/expressions.jsx --args '{...}'`
(bridge), or as one handoff file a person runs from File > Scripts > Run Script File. Every job is
one undo step when run with `--undo "Agent: <what>"`. Expressions use the JavaScript engine (the
27.0 default). Every expression below was applied live with `AEK.expr.set` and its values read back
at several times.

The rig contract: a guide null `CTRL` with controls `Pad X`, `Pad Y`, `Gap`, `Lag (frames)`,
`Idle (frames)`, `Idle Amp`, `Count (s)`, dropdown `Theme`; text layers `TXT_1` (name) and `TXT_2`
(title); shape `BOX` parented to `TXT_1`; leader null `MOVE`; followers `Bar 1` to `Bar 5`; idle
`DOT`; counter `COUNT`.

## 1. Build the lower-third rig

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, name, title}. Needs --lib expressions.jsx. Adds layers; never removes any.
var c = AEK.core.comp(ARGS.comp);
var rep = AEX.expressions.rig(c, { name: ARGS.name, title: ARGS.title });
rep.check = AEK.expr.check(c, 5);
return rep;
```

Check: `rep.expressions` is 19 and `check.failed` is 0. Then run procedure 2.

The expressions it writes, one per property:

```javascript
// expression (JavaScript engine): BOX (shape, parented to TXT_1, anchor [0,0], position [0,0]) > Contents > Rectangle Path > Size
// checked: live 27.0
const t = thisComp.layer("TXT_1");
const c = thisComp.layer("CTRL");
const r = t.sourceRectAtTime(time, false);
const s = t.transform.scale / 100;
const w = r.width > 0 ? r.width + 2 * c.effect("Pad X")(1) / s[0] : 0;
const h = r.height > 0 ? r.height + 2 * c.effect("Pad Y")(1) / s[1] : 0;
[w, h]
```

```javascript
// expression (JavaScript engine): BOX > Contents > Rectangle Path > Position
// checked: live 27.0
const r = thisComp.layer("TXT_1").sourceRectAtTime(time, false);
[r.left + r.width / 2, r.top + r.height / 2]
```

Measured: margins 32 / 18 px on all sides for short text, long text, 80 px type, and the text layer
at 150 % scale. Without the `/ s` division, a parented box grew its padding to 48 / 27 px at 150 %.
Empty text returns a rect of 0, so the guard gives a 0 box instead of a 64 x 36 sliver.

Padding through Offset Paths (Jake Bartlett, CVliDoNgoCg 00:10:39, 00:16:54 to 00:18:03): the rect
hugs the ink with no padding in Size, Offset Paths adds the margin as one Amount, and the group's
Anchor Point and Position sit on the padded top-left so a Scale X build starts at the visible left
edge.

```javascript
// expression (JavaScript engine): BOX (shape, parented to TXT_1, anchor [0,0], position [0,0]) > Contents > plate > Transform > Anchor Point, and the same on Position
// checked: live 27.0
const r = thisComp.layer("TXT_1").sourceRectAtTime(time, false);
const o = content("plate").content("Offset Paths 1").amount;
[r.left - o, r.top - o]
```

Rect Size is `[r.width, r.height]` and Rect Position is
`[r.left + r.width / 2, r.top + r.height / 2]`. Measured with Amount 24: margins 24 on all four
sides; at group Scale [50, 100] the left margin stayed 24. With anchor and position left at [0, 0],
the group scaled around the text origin and the left margin moved to 13.97. Offset Paths gives one
value for both axes: keep the `Pad X` / `Pad Y` Size route when the padding differs per axis. The
Offset Paths match name is `ADBE Vector Filter - Offset`, Amount `ADBE Vector Offset Amount`.

When the text animates on or off, replace `time` with one fixed sample time in BOTH expressions
(width, height, left and top must share it), for example `t.inPoint + (t.outPoint - t.inPoint) / 2`.

Unparented alternative, axis-aligned in comp space (ignores the text's rotation, keeps padding
constant at any scale):

```javascript
// expression (JavaScript engine): BOX_COMP (shape, no parent, anchor [0,0], position [0,0]) > Contents > Rectangle Path > Size
// checked: live 27.0
const t = thisComp.layer("TXT_1");
const c = thisComp.layer("CTRL");
const r = t.sourceRectAtTime(time, false);
const a = t.toComp([r.left, r.top]), b = t.toComp([r.left + r.width, r.top + r.height]);
[Math.abs(b[0] - a[0]) + 2 * c.effect("Pad X")(1), Math.abs(b[1] - a[1]) + 2 * c.effect("Pad Y")(1)]
```

```javascript
// expression (JavaScript engine): BOX_COMP > Contents > Rectangle Path > Position
// checked: live 27.0
const t = thisComp.layer("TXT_1");
const r = t.sourceRectAtTime(time, false);
const a = t.toComp([r.left, r.top]), b = t.toComp([r.left + r.width, r.top + r.height]);
fromComp((a + b) / 2)
```

Second line under the ink of the first (any parent on TXT_2):

```javascript
// expression (JavaScript engine): TXT_2 (text) > Transform > Position
// checked: live 27.0
const a = thisComp.layer("TXT_1");
const gap = thisComp.layer("CTRL").effect("Gap")(1);
const r = a.sourceRectAtTime(time, false);
const x = a.toComp([0, 0])[0];
const y = a.toComp([0, r.top + r.height])[1] + gap;
const me = sourceRectAtTime(time, false);
const s = transform.scale / 100;
const p = [x + anchorPoint[0] * s[0], y + (anchorPoint[1] - me.top) * s[1]];
hasParent ? parent.fromComp(p) : p
```

Measured: gap 14.00 px for one line, two lines, descenders, 120 px type, a moved line 1, line 1 at
70 % scale, and TXT_2 parented to a moved null. Descenders in line 1 push line 2 down by the
descender depth (14 px at 72 px Helvetica Bold).

Baseline variant (line 2 does not move when line 1 gains descenders; needs Gap larger than the
descender depth):

```javascript
// expression (JavaScript engine): TXT_2 (text) > Transform > Position
// checked: live 27.0
const a = thisComp.layer("TXT_1");
const gap = thisComp.layer("CTRL").effect("Gap")(1);
const st = a.text.sourceText.style;
const lines = a.text.sourceText.value.split(/\r\n|\r|\n|\u0003/).length;
const lead = st.autoLeading ? st.fontSize * 1.2 : st.leading;
const base = a.toComp([0, (lines - 1) * lead]);
const me = sourceRectAtTime(time, false);
const s = transform.scale / 100;
const p = [base[0] + anchorPoint[0] * s[0], base[1] + gap + (anchorPoint[1] - me.top) * s[1]];
hasParent ? parent.fromComp(p) : p
```

Measured: line 2 top stayed at 500.4 px with and without descenders in a two-line name (last
baseline 486.4 + 14). The documented `isAutoLeading` reads `undefined` in 27.0; the live member is
`autoLeading`, and `leading` reads 0.01 under auto leading.

Follow-through, five followers from one leader:

```javascript
// expression (JavaScript engine): Bar 1 to Bar 5 (any layer whose name ends in its order number) > Transform > Position
// checked: live 27.0
const lead = thisComp.layer("MOVE").transform.position;
const lag = thisComp.layer("CTRL").effect("Lag (frames)")(1);
const i = parseInt(thisLayer.name.replace(/\D/g, ""), 10);
const d = i * Math.round(lag) * thisComp.frameDuration;
value + (lead.valueAtTime(time - d) - lead.valueAtTime(0))
```

Measured: lags 3, 6, 9, 12, 15 frames at 24, 30 and 60 fps. A duplicate of `Bar 5` is named `Bar 6`
by After Effects and takes 6 x Lag at once. The same rig with `time - i * 0.1` gave 2, 5, 7, 10, 12
frames at 24 fps.

Seamless idle (noise sampled on a circle, period in frames):

```javascript
// expression (JavaScript engine): DOT > Transform > Position
// checked: live 27.0
const T = thisComp.layer("CTRL").effect("Idle (frames)")(1) * thisComp.frameDuration;
const amp = thisComp.layer("CTRL").effect("Idle Amp")(1);
const a = 2 * Math.PI * (time - inPoint) / T, r = 1.2;
value + [noise([Math.cos(a) * r, Math.sin(a) * r, 0]), noise([Math.cos(a) * r, Math.sin(a) * r, 7])] * amp
```

Counter with separators:

```javascript
// expression (JavaScript engine): COUNT (text) > Text > Source Text
// checked: live 27.0
const end = 1250000;
const dur = thisComp.layer("CTRL").effect("Count (s)")(1);
const v = Math.round(ease(time - inPoint, 0, dur, 0, end));
String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ",")
```

Measured at 30 fps, 2 s count: frame 0 "0", frame 30 "625,000", frame 59 "1,248,970", frames 60
onward "1,250,000". Right-justify the layer: the ink width changed from 425 to 521 px when the
seventh digit arrived.

Theme from one dropdown (the menu returns 1, 2, 3; arrays start at 0):

```javascript
// expression (JavaScript engine): BOX > Contents > Fill 1 > Color (shape fills of bars and dot: .accent)
// checked: live 27.0
const th = thisComp.layer("CTRL").effect("Theme")("Menu");
const pal = [
  {bg: [0.96, 0.96, 0.94, 1], fg: [0.08, 0.09, 0.12, 1], accent: [0.93, 0.27, 0.13, 1]},
  {bg: [0.08, 0.09, 0.12, 1], fg: [0.96, 0.96, 0.94, 1], accent: [0.25, 0.75, 1, 1]},
  {bg: [0.93, 0.27, 0.13, 1], fg: [1, 1, 1, 1], accent: [0.08, 0.09, 0.12, 1]}
];
pal[Math.min(Math.max(th, 1), pal.length) - 1].bg
```

```javascript
// expression (JavaScript engine): TXT_1 and TXT_2 (text) > Text > Source Text (theme the text fill without an animator)
// checked: live 27.0
const th = thisComp.layer("CTRL").effect("Theme")("Menu");
const fg = [[0.08, 0.09, 0.12], [0.96, 0.96, 0.94], [1, 1, 1]][Math.min(Math.max(th, 1), 3) - 1];
text.sourceText.style.setApplyFill(true).setFillColor(fg)
```

Measured: `effect("Theme")("Menu")` and `effect("Theme")(1)` read the same index. Setting the
dropdown to 1, 2, 3 gave the three palettes, also with Fill switched off in the layer's own
document.

Text fill rules (text-style doc; measured in 27.0):

- `setFillColor` takes `[R, G, B]`, 0 to 1 (doc). A Color Control or a shape palette gives four
  values: pass `[c[0], c[1], c[2]]`. Measured: a four-value array was accepted and the fourth value
  dropped, so the doc form is the one to write.
- Fill must be on (`applyFill`). With Fill off in the layer, `setFillColor` alone showed nothing and
  reading `fillColor` threw "Can't get color, this text has no fill". `setApplyFill(true)` before it
  fixed both.
- Text animators run after style expressions (Nic and Kyle Hamrick, yG8UbiKKeYw 00:26:08). Measured:
  an animator Fill Color in red on a 0 to 50 % range turned the first half red over a blue
  `setFillColor` theme; the rest kept the theme. A theme switch on Source Text never reaches
  characters an animator Fill Color covers: drive that animator's color from the same dropdown, or
  remove its Fill Color.

## 2. Measure the rig (the numbers behind the gates)

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, t (a time where everything is on screen)}. Read-only apart from a temporary probe layer that it removes.
var c = AEK.core.comp(ARGS.comp), X = AEX.expressions, t = ARGS.t, i, lags = [];
var R = { margins: X.margins(X.compRect(c, "BOX", t), X.compRect(c, "TXT_1", t)) };
R.gap = Math.round((X.compRect(c, "TXT_2", t).top - X.compRect(c, "TXT_1", t).bottom) * 100) / 100;
var mp = AEK.core.layer(c, "MOVE").property("ADBE Transform Group").property("ADBE Position");
for (i = 1; i <= 5; i++) { lags.push(X.lagFrames(mp, AEK.core.layer(c, "Bar " + i).property("ADBE Transform Group").property("ADBE Position"), c, 30, 0, Math.round(c.frameRate * 1.5)).lag); }
R.lags = lags;
R.idle = X.seam(AEK.core.layer(c, "DOT").property("ADBE Transform Group").property("ADBE Position"), c, Math.round(c.frameRate * 2), 0);
var cs = AEK.core.layer(c, "COUNT").property("ADBE Text Properties").property("ADBE Text Document");
R.count = [cs.valueAtTime(0, false).text, cs.valueAtTime(c.duration - c.frameDuration, false).text];
R.check = AEK.expr.check(c, 5);
return R;
```

Pass: margins equal Pad X and Pad Y; gap equals Gap; lags `[L, 2L, 3L, 4L, 5L]`; idle `ratio` under
2.5 and `repeat` 0 (the period must match `Idle (frames)`); count ends on "1,250,000";
`check.failed` 0. Measured on the built rig: margins 32 / 18, gap 14, lags 3 to 15, idle ratio 0.78,
repeat 0.

## 3. Loops measured at the seam

`AEX.expressions.seam(prop, comp, periodFrames, startFrame)` returns the step across the loop point
and the median step inside it. Measured at 30 fps, three eased keys 0.5 s apart, period 30 frames:

| Expression                                          | Seam step / median | Reading                                                         |
| --------------------------------------------------- | ------------------ | --------------------------------------------------------------- |
| `loopOut("cycle")`, first and last key differ       | 596 px / 22 px     | jump                                                            |
| `loopOut("cycle")`, last key equals the first       | 4.0 / 22           | no jump, a hitch where both eases stop                          |
| `loopOut("pingpong")`                               | 4.0 / 22           | turns around at ease speed                                      |
| `loopOut("offset")`                                 | 4.0 / 22           | each cycle starts where the last ended (+600 px per cycle here) |
| `loopOut("continue")`                               | 0.04 / 22          | keeps the last velocity: 0 after an eased key, so it stops      |
| `wiggle(1, 60, 1, 0.5, time % T)`                   | 18.8 / 1.15        | jump every T                                                    |
| blended wiggle below                                | 3.5 / 1.5          | no jump; amplitude drops toward mid-loop (max offset 47 of 60)  |
| circular noise (procedure 1)                        | 7.7 / 9.9          | no jump, full amplitude (max offset 78)                         |
| `40 * Math.sin(2 * Math.PI * (time - inPoint) / T)` | 4.2 / 3.0          | exact loop                                                      |

```javascript
// expression (JavaScript engine): any 1D or 2D property > blended wiggle loop, period T in frames
// checked: live 27.0
const T = 60 * thisComp.frameDuration;
const t = time % T;
linear(t, 0, T, wiggle(1, 60, 1, 0.5, t), wiggle(1, 60, 1, 0.5, t - T))
```

A period set in seconds fails only when it is not a whole number of frames at the comp rate
(`T * fps` not an integer). Measured with the circular noise at period 0.7 s: 16.8 frames at 24 fps
(frame N against frame 0 off by 3.1 px), 17.5 at 25 fps (6.9 px), 21 at 30 fps (0 px). A 2 s period
is whole at 24, 25 and 30 fps and repeated exactly at all three. The seam ratio stayed under 1 in
every case: playback inside After Effects shows no jump; a rendered loop file of `round(T * fps)`
frames does, at every repeat. A period control in frames is whole at any rate.

## 4. Inertia and bounce from the last key

Needs two or more keys. Measured on Scale keyed 0 to 100 over 8/24 s: overshoot 10.9 % at 24 fps
(settles at frame 17) and 10.2 % at 60 fps (frame 40): the same 0.7 s, because the expression works
in seconds. The 2018 code with implicit globals, the `const`/`let` version below and the
`previousKey` version gave identical values.

```javascript
// expression (JavaScript engine): any keyed property (Scale, Rotation, Position) > inertial bounce after each key
// checked: live 27.0
const amp = 0.05, freq = 4, decay = 8;
let n = 0;
if (numKeys > 0) {
  n = nearestKey(time).index;
  if (key(n).time > time) n--;
}
if (n > 0 && time - key(n).time < 1) {
  const t = time - key(n).time;
  const v = velocityAtTime(key(n).time - thisComp.frameDuration / 10);
  value + v * amp * Math.sin(freq * t * 2 * Math.PI) / Math.exp(decay * t);
} else {
  value;
}
```

```javascript
// expression (JavaScript engine): any keyed property > inertial bounce with the 26.0 previousKey()
// checked: live 27.0
const amp = 0.05, freq = 4, decay = 8;
if (numKeys < 2 || time < key(1).time) {
  value;
} else {
  const k = thisProperty.previousKey(time);
  const t = time - k.time;
  const v = velocityAtTime(k.time - thisComp.frameDuration / 10);
  t < 1 ? value + v * amp * Math.sin(freq * t * 2 * Math.PI) / Math.exp(decay * t) : value;
}
```

```javascript
// expression (JavaScript engine): Position of a falling layer (last key = floor contact) > bounce back
// checked: live 27.0
const e = 0.7, g = 5000, nMax = 9;
let n = 0;
if (numKeys > 0) {
  n = nearestKey(time).index;
  if (key(n).time > time) n--;
}
if (n > 0) {
  const t = time - key(n).time;
  const v = -velocityAtTime(key(n).time - 0.001) * e;
  let vl = length(v);
  const vu = (value instanceof Array) ? (vl > 0 ? normalize(v) : [0, 0, 0]) : (v < 0 ? -1 : 1);
  let tCur = 0, segDur = 2 * vl / g, tNext = segDur, nb = 1;
  while (tNext < t && nb <= nMax) {
    vl *= e; segDur *= e; tCur = tNext; tNext += segDur; nb++;
  }
  if (nb <= nMax) {
    const delta = t - tCur;
    value + vu * delta * (vl - g * delta / 2);
  } else {
    value;
  }
} else {
  value;
}
```

Measured: a drop of 800 px in 0.5 s rebounds to 125 px above the floor, 7 hops at 24 fps, 8 at 60
fps, never below the floor.

## 5. Random that holds still, steps, or repeats

| Expression                                         | Measured over 24 frames at 24 fps                                             |
| -------------------------------------------------- | ----------------------------------------------------------------------------- |
| `wiggle(2, 50)` on two layers                      | different per layer (seeded by layer and property), repeatable frame by frame |
| `seedRandom(7, true); wiggle(2, 50)` on two layers | identical on both, still moving (22 changes)                                  |
| `random(0, 100)`                                   | 23 changes                                                                    |
| `seedRandom(index, true); random(0, 100)`          | 0 changes: one value per layer for the whole layer                            |
| `posterizeTime(4); wiggle(3, 50)`                  | 3 changes: holds 6 frames                                                     |
| `posterizeTime(0); wiggle(3, 50)`                  | 0 changes in 48 frames: frozen                                                |

```javascript
// expression (JavaScript engine): any layer property > stepped jitter, different per layer, same on every render
// checked: live 27.0
posterizeTime(4);
seedRandom(index, true);
wiggle(3, 50)
```

## 6. Spaces: toComp, fromComp, toWorld

Measured: a null at [200, 0] under a parent at [500, 400], rotated 30, scaled 50 %:
`transform.position` reads [200, 0]; `toComp(anchorPoint)` gives [586.6, 450]; `fromComp` returns
[0, 0]. A 3D null at [960, 540, 300]: moving the camera by 200 px changed `toComp` (960 to 980.1)
and left `toWorld` at [960, 540, 300].

`toCompVec` and `fromCompVec` did not match the point difference: on the parent above,
`toCompVec([100, 0])` returned [173.2, 100] while `toComp([100, 0]) - toComp([0, 0])` returned
[43.3, 25], and `fromCompVec` returned what the point difference of `fromComp` should give. Use
point differences for vectors.

```javascript
// expression (JavaScript engine): an effect Point property (Gradient Ramp Start, CC Bend It Start) on a text or shape layer > stays on the layer and stays draggable
// checked: note gSq19gpWwSU 00:11:13
thisLayer.toComp([0, 0, 0]) + value
```

```javascript
// expression (JavaScript engine): any 2D Position > the comp-space position of a parented layer (survives re-parenting)
// checked: live 27.0
const L = thisComp.layer("CHILD");
L.toComp(L.anchorPoint)
```

## 7. Text style expressions (25.0 and later)

Evaluation order: the layer's own Character and Paragraph settings, then style expressions on Source
Text, then text animators (Nic and Kyle Hamrick, yG8UbiKKeYw 00:08:36, 00:26:08). An animator
property on a range overrides the style expression there; the text fill rules under procedure 1 give
the measured case.

Word highlight from a slider, text taken from a hidden INPUT layer (the editable field for Essential
Graphics):

```javascript
// expression (JavaScript engine): TITLE (text) > Text > Source Text
// checked: live 27.0
const src = thisComp.layer("INPUT").text.sourceText.value;
const w = Math.round(thisComp.layer("CTRL").effect("Word")(1));
const col = thisComp.layer("CTRL").effect("Highlight")(1);
const words = src.split(/\s/);
let st = text.sourceText.style.setText(src);
if (w >= 1 && w <= words.length) {
  let start = 0;
  for (let i = 0; i < w - 1; i++) start += words[i].length + 1;
  st = st.setFillColor([col[0], col[1], col[2]], start, words[w - 1].length).setFontSize(90, start, words[w - 1].length);
}
st
```

Measured with `TextDocument.characterRange(i, i + 1).fillColor`: word 3 colored characters 15 to 19,
word 5 characters 27 to 31, Word 0 and Word 99 left plain text, and a word after a line break landed
exactly (the return counts as one character).

```javascript
// expression (JavaScript engine): FOLLOW (text) > Text > Source Text (inherit another layer's style, change only the words)
// checked: live 27.0
thisComp.layer("TITLE").text.sourceText.getStyleAt(0, 0).setText("Inherited style")
```

## 8. Data from JSON and CSV footage

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, json (absolute path), layer (an existing text layer)}. Imports the file once and links the layer's Source Text.
var c = AEK.core.comp(ARGS.comp);
var info = AEK.xio.importFile(ARGS.json);
var sp = AEK.core.layer(c, ARGS.layer).property("ADBE Text Properties").property("ADBE Text Document");
var r = AEK.expr.set(sp, 'const d = footage("' + info.name + '").sourceData;\nd.title + ": " + d.total.toLocaleString("en-US")', [0]);
return { footage: info.name, text: sp.valueAtTime(0, false).text };
```

```javascript
// expression (JavaScript engine): any text layer > Source Text, from a JSON row
// checked: live 27.0
const d = footage("data.json").sourceData;
d.rows[1].name + " " + d.rows[1].v
```

```javascript
// expression (JavaScript engine): any text layer > Source Text, from a CSV cell [column, row], row 0 = first row under the header
// checked: live 27.0
footage("data.csv").dataValue([1, 0])
```

Measured: JSON `sourceData` returns the parsed object; `JSON.parse(footage("data.json").sourceText)`
works too. CSV `sourceData` returns null; `dataValue([0, 1])` gave "South", `dataValue([1, 0])` gave
12 (a number). `dataValue` on JSON, `dataKeyCount` and `dataKeyName` failed. After the file was
rewritten, the old value stayed until `item.mainSource.reload()` (Reload Footage). A missing key
reads `undefined` and fails only when used; a missing footage name fails with "couldn't find footage
named".

## 9. Error report, safe renames, structure changes

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp}. Read-only: every expression with its error, then an evaluation pass at 5 times.
var c = AEK.core.comp(ARGS.comp);
var all = AEK.expr.list(c), bad = [], i;
for (i = 0; i < all.length; i++) { if (all[i].error !== "") { bad.push(all[i]); } }
return { engine: app.project.expressionEngine, expressions: all.length, withError: bad, check: AEK.expr.check(c, 5) };
```

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, from, to}. Renames a layer and rewrites layer("from") in every expression of the project; returns the edited properties.
var c = AEK.core.comp(ARGS.comp);
var r = AEX.expressions.renameLayer(c, ARGS.from, ARGS.to);
r.check = AEK.expr.check(c, 3);
return r;
```

Measured: `layer.name = "..."` by script left the expression text unchanged; the expression broke
("layer named 'CTRL' is missing"), and the first read after the rename returned 0 with an empty
`expressionError`. Renaming an effect by script also left its references. Precomposing a referenced
layer broke `thisComp.layer("TXT_1")` in the main comp. A failed expression keeps
`expressionEnabled` true and returns 0 on Opacity. `renameLayer` matches `layer("name")` in every
comp: use it only when the old name is unique in the project.

## 10. Cost and baking

`AEX.expressions.timeEval(prop, comp, 120)` evaluates at 120 distinct frames. Measured, first pass:
a 60-sample `valueAtTime` average 47.8 ms, `smooth(1, 61)` 13.9 ms, one `valueAtTime` 4.1 ms; second
pass 0.9 ms (After Effects caches results per frame). `posterizeTime(6)` in front of the 60-sample
loop did not reduce the first-pass cost (49.4 ms): it changes which time is shown, not how many
frames get evaluated.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, layer}. Bakes Position to one key per frame; the expression text is kept and switched off (switch it back on to undo).
var c = AEK.core.comp(ARGS.comp);
var p = AEK.core.layer(c, ARGS.layer).property("ADBE Transform Group").property("ADBE Position");
var frames = [0, 7, 17, 45, Math.round(c.duration * c.frameRate) - 1];
var before = AEX.expressions.atFrames(p, c, frames);
var r = AEK.expr.bake(p, c, 0, c.duration - c.frameDuration);
var after = AEX.expressions.atFrames(p, c, frames), maxd = 0, i;
for (i = 0; i < frames.length; i++) { maxd = Math.max(maxd, Math.abs(before[i][0] - after[i][0]) + Math.abs(before[i][1] - after[i][1])); }
r.maxDiff = maxd; r.enabled = p.expressionEnabled;
return r;
```

Measured: 120 keys for 4 s at 30 fps, difference 0 and 0.00001 px at whole frames in two runs,
linear between frames.

## 11. JavaScript engine hazards (measured in 27.0)

| Expression text                                      | Result                                                              |
| ---------------------------------------------------- | ------------------------------------------------------------------- |
| `if (time > 1) 100 else 50`                          | SyntaxError: Unexpected token 'else'                                |
| `if (time > 1) { 100 } else { 50 }` or a ternary     | works                                                               |
| `this.name.length`                                   | TypeError (this is not the layer); `thisLayer.name` works           |
| a function declaration as the last statement         | "Object of type found where a Number, Array, or Property is needed" |
| `x = 40; x + 1` (implicit global)                    | works                                                               |
| `thisComp.layer("T").text.sourceText[0]`             | no error, wrong value (undefined); `.value[0]` works                |
| `[50, 50]` on Opacity                                | "expression result must be of dimension 1, not 2"                   |
| `const` in a project switched to Legacy ExtendScript | "a redeclared"                                                      |

`app.project.expressionEngine` reads `javascript-1.0`; `"extendscript"` can still be set in 27.0.

## 12. Locale formatting in this engine

Measured: `typeof Intl` is "object"; `(1250000).toLocaleString()` gave "1,250,000", `("fr-FR")` "1
250 000" with narrow no-break spaces (U+202F), `("de-DE")` "1.250.000". Pass the locale explicitly:
the default depends on the machine. The regex formatter in procedure 1 gives the same output
everywhere.
