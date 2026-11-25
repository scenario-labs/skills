# Procedures (agent, with code)

Every job is the body of a function for `ae.py run` (scenario-after-effects-expert). Load this
skill's helpers with `--lib`:

```bash
python3 <expert>/scripts/ae.py run job.jsx --lib <this skill>/scripts/animation.jsx --undo "Agent: animate card"
```

`AEX.animation` (in `scripts/animation.jsx`): `EASES`, `move`, `overshoot`, `bounce`,
`springExpression`, `shiftKeys`, `stagger`, `animatedProps`, `copyEase`, `compPoint`, `motionCheck`.
Jobs below that start with `AEK.core.fresh()` are test cases: they close the open project without
saving. In a person's session, drop that line, work inside `--undo`, and never call `app.open()`
while the project has unsaved changes: After Effects raises a native Save panel that blocks every
later script. Use `AEK.core.open(path)` in tests only.

All numbers below were measured at 30 fps unless the case says otherwise.

## 1. Apply a named ease and measure it

Goal: turn a design ease (CSS cubic-bezier or influences) into keys and prove its spacing.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), l = AEK.core.layer(c, ARGS.layer);
var p = AEK.core.prop(l, ["ADBE Transform Group", "ADBE Position"]);
// frames, not seconds; ease: a name in AEX.animation.EASES, [x1, y1, x2, y2], or {out: 15, "in": 85}
AEX.animation.move(p, c, 0, [250, 540], 20, [1250, 540], "out_expo");
var s = AEK.motion.sample(p, c, 0, 30 * c.frameDuration);
return { peakPxPerFrame: s.peakSpeed / c.frameRate, peakFrame: s.peakFrame, overshootPct: s.overshoot, settleFrame: s.settleFrame,
    progressF5: (s.frames[5].value[0] - 250) / 10 };
```

Check: the numbers match the table in SKILL.md (out_expo: 82.6 % at frame 5, settle frame 13). The
conversion is exact: out of key 1 `KeyframeEase((y1 / x1) * dv / dt, x1 * 100)`, into key 2
`KeyframeEase(((1 - y2) / (1 - x2)) * dv / dt, (1 - x2) * 100)`.

Measured rows (1000 px over 20 frames): linear peak 50 px per frame; Easy Ease 74.7 at frame 10,
settle 19; UI flick 80/80 205.5 at frame 10, settle 18; appear-on 15/85 138.3 at frame 3, settle 18;
CSS `ease` (0.25, 0.1, 0.25, 1) 113.3 at frame 5, settle 18; out_cubic settle 16; out_quint settle
14; out_expo 281.1 at frame 1, settle 13; in_out_cubic 137 at frame 10; in_cubic 143.6 on the last
frame; in_back on combined Position reached 1.1 % at frame 5 and never went backward.

**Trap (measured):** out_back on combined Position gave 0 % overshoot and settled on frame 16; on a
separated X it gave 9.7 % and settled on frame 19. A spatial property does not leave its path:
overshoot it with a third key, or separate first.

## 2. A product card (slide in, settle, chips, hold, exit as one)

Goal: a 6 s card at 30 fps (180 frames), 1080x1350, with every time in frames. The hold starts on
the last key frame of every entrance property, never on the settle of one property: here chip 3
Position X ends on 24 + 12 = 36.

| Element             | Frames            | Property and ease                                                                                                               |
| ------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Phone Y (separated) | 0 to 15 to 24     | 1990 to 651 (3 % past 690) to 690: out influence 10, peak speed 0 at 75/50, settle influence 80                                 |
| Phone rotation      | 0 to 19 to 28     | 8 to -2 to 0 degrees: lands 4 frames after the position peak                                                                    |
| Chips 1 to 3        | start 18, 21, 24  | Scale 0 to 100 in 10 frames out_back (peak 110); Position X +60 to 0 in 12 frames out_expo; Opacity 0 to 100 in 4 frames linear |
| Chip labels         | follow their chip | parented to the chip; Opacity driven from the chip (parenting passes no Opacity)                                                |
| Hold                | 36 to 150         | nothing keyed; starts on the last entrance key (chip 3 Position X, 24 + 12)                                                     |
| Master null         | 150 to 155 to 168 | anticipation 30 px down (out 50, in 70), then up 1530 px with in_cubic                                                          |
| Motion blur         | all               | comp and layer switches on, 180 degrees, phase -90                                                                              |

```javascript
// channel: bridge | handoff
// checked: live 27.0
AEK.core.fresh();
var c = AEK.build.comp("product_card", { width: 1080, height: 1350, fps: 30, duration: 6, bg: [0.93, 0.93, 0.95] });
function F(n) { return n * c.frameDuration; }
function T(l, mn) { return AEK.core.prop(l, ["ADBE Transform Group", mn]); }
var master = AEK.build.nullLayer(c, "CTRL_master");
T(master, "ADBE Anchor Point").setValue([0, 0]); T(master, "ADBE Position").setValue([0, 0]); // parent space = comp space
var phone = AEK.build.shape(c, "phone", [
    { name: "screen", type: "rect", size: [380, 800], roundness: 40, fill: [0.25, 0.55, 1] },
    { name: "body", type: "rect", size: [420, 860], roundness: 60, fill: [0.1, 0.1, 0.12] }
]);
T(phone, "ADBE Anchor Point").setValue([0, 0]);
phone.parent = master;
var pPos = T(phone, "ADBE Position"), pRot = T(phone, "ADBE Rotate Z");
pPos.dimensionsSeparated = true; // before any easing: separating resets eases to linear
var pX = pPos.getSeparationFollower(0), pY = pPos.getSeparationFollower(1);
pX.setValue(360);
AEX.animation.overshoot(pY, c, 0, 1990, 15, 24, 690, 3, 10, 80);
AEX.animation.overshoot(pRot, c, 0, 8, 19, 28, 0, 25, 10, 80);
var chips = [], labels = ["4K camera", "2 day battery", "Fast charge"], i;
for (i = 0; i < 3; i++) {
    var ch = AEK.build.shape(c, "chip_" + (i + 1), { type: "rect", size: [330, 104], roundness: 52, fill: [1, 1, 1] });
    T(ch, "ADBE Anchor Point").setValue([-165, 0]); // scale from the left edge
    ch.parent = master;
    var tx = AEK.text.add(c, labels[i], { size: 40, fill: [0.1, 0.1, 0.12], justify: "left" });
    tx.parent = ch;
    T(tx, "ADBE Position").setValue([-130, 14]);
    var f0 = 18 + i * 3, y = 470 + i * 150;
    AEX.animation.move(T(ch, "ADBE Position"), c, f0, [660, y], f0 + 12, [600, y], "out_expo");
    AEX.animation.move(T(ch, "ADBE Scale"), c, f0, [0, 0], f0 + 10, [100, 100], "out_back");
    AEX.animation.move(T(ch, "ADBE Opacity"), c, f0, 0, f0 + 4, 100, "linear");
    AEK.expr.set(T(tx, "ADBE Opacity"), "value * thisLayer.parent.transform.opacity / 100"); // parenting passes no Opacity
    chips.push(ch);
}
var mPos = T(master, "ADBE Position");
AEX.animation.move(mPos, c, 150, [0, 0], 155, [0, 30], { out: 50, "in": 70 });
AEK.motion.key(mPos, F(168), [0, -1500]);
AEK.motion.bezier(mPos, 2, 3, AEX.animation.EASES.in_cubic);
c.motionBlur = true; c.shutterAngle = 180; c.shutterPhase = -90;
for (i = 1; i <= c.numLayers; i++) { if (!c.layer(i).nullLayer) { c.layer(i).motionBlur = true; } }
var sY = AEK.motion.sample(pY, c, 0, F(40));
var times = [], fr = [0, 4, 8, 12, 15, 18, 21, 24, 27, 30, 90, 152, 155, 158, 161, 164];
for (i = 0; i < fr.length; i++) { times.push(F(fr[i])); }
return { phoneY: { overshootPct: sY.overshoot, settleFrame: sY.settleFrame }, check: AEX.animation.motionCheck(c),
    frames: AEK.capture.frames(c, times, ARGS.out, "card") };
```

Measured: phone overshoot 3 %, at 651 px on frame 15, settled (within 1 %) on frame 20, at rest on
24; rotation overshoot 25 % (-2 degrees) on frame 19, settled on 26; chips peak at scale 110 (9.7
%); chip Scale settles on frames 28, 31, 34 and chip Position X on 26, 29, 32 (within 1 %), with the
last X keys on 30, 33, 36, so the hold starts on frame 36 (114 frames, 3.8 s); chip 1 starts 3
frames after the phone Y peak; each label reads 100 % opacity one frame after its chip starts
without the expression and 25 % with it (chip 25 %); exit fastest on its last frame (328 px per
frame); motion check: no finding; job 4.9 s with 16 frames. Contact sheet: the phone tilt resolves
after the landing, chip 1 starts while the phone still rotates, the exit smears vertically and the
chips leave with the phone. The first frame is empty: for a feed, start the phone at frame -3 (or
lower the start Y) so something shows by frame 3. The other fix for the label is to precompose chip
and label and key Opacity on the precomp layer: its Opacity applies to everything inside. Parenting
passes Position, Scale and Rotation only.

## 3. Motion check, then upgrade a default scene

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), before = AEX.animation.motionCheck(c);
var ref = AEK.core.prop(AEK.core.layer(c, ARGS.reference), ["ADBE Transform Group", "ADBE Position"]);
AEK.motion.ease(ref, 1, 33.33, 15); AEK.motion.ease(ref, 2, 85, 33.33); // appear-on: little out, strong in
var others = [], i;
for (i = 0; i < ARGS.layers.length; i++) {
    var l = AEK.core.layer(c, ARGS.layers[i]);
    AEX.animation.copyEase(ref, AEK.core.prop(l, ["ADBE Transform Group", "ADBE Position"]));
    others.push(l);
}
AEX.animation.stagger(others, c, 3, "keys"); // keeps in-points; "layer" mode moves startTime instead
return { before: before, after: AEX.animation.motionCheck(c) };
```

Rules in `motionCheck`: `linear` (both sides linear, opacity excepted), `drift` (equal neighbor keys
whose value moves between them), `pop` (speed through a middle key jumps from rest to over half the
segment peak), `lockstep` (3 or more layers start on one frame), `default-ease` (over 60 % of keys
at 33.33 % with speed 0). Measured on a beginner scene (4 linear moves on frame 0 plus F9 scale
keys): 4 `linear` and 1 `lockstep` before; none after the copy, the 3-frame stagger and an out_back
on the scale keys (first keys on frames 0, 3, 6, 9).

## 4. Spatial: drift, arcs, roving

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), p = AEK.core.prop(AEK.core.layer(c, ARGS.layer), ["ADBE Transform Group", "ADBE Position"]), k;
// drift fix: hold out of the first of two equal keys (or zero both keys' spatial tangents)
for (k = 1; k < p.numKeys; k++) {
    var a = p.keyValue(k), b = p.keyValue(k + 1);
    if (a[0] === b[0] && a[1] === b[1]) { p.setInterpolationTypeAtKey(k, p.keyInInterpolationType(k), KeyframeInterpolationType.HOLD); }
}
// arc between key 1 and 2: tangents are offsets from each key, in px
if (ARGS.arc) { p.setSpatialTangentsAtKey(1, [0, 0, 0], [400, -500, 0]); p.setSpatialTangentsAtKey(2, [-400, -500, 0], [0, 0, 0]); }
// even speed along a path: middle keys rove (first and last cannot)
if (ARGS.rove) { for (k = 2; k < p.numKeys; k++) { p.setRovingAtKey(k, true); } }
return AEK.motion.keys(p, c);
```

Measured: keys made by script have zero spatial tangents (no drift). With handles pulled through two
equal keys the pose drifted 53.8 px; Hold fixed it (0), zero tangents fixed it (0), linear temporal
interpolation did not (53.9). Tangents (400, -500) and (-400, -500) over a 1300 px move lifted the
arc 375 px. Roving on keys spaced 100, 900 and 200 px apart, 10 frames each: speed went from 10 to
90 px per frame to a constant 40, and keys 2 and 3 moved to frames 2.5 and 25.
`setRovingAtKey(1, true)` is ignored without an error.

## 5. Separate Dimensions without losing eases

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), p = AEK.core.prop(AEK.core.layer(c, ARGS.layer), ["ADBE Transform Group", "ADBE Position"]);
var before = AEK.motion.keys(p, c);
p.dimensionsSeparated = true; // every key becomes LINEAR here (measured): re-apply eases per dimension
var X = p.getSeparationFollower(0), Y = p.getSeparationFollower(1), i;
for (i = 0; i + 1 < before.length; i++) {
    AEK.motion.bezier(X, i + 1, i + 2, ARGS.easeX); AEK.motion.bezier(Y, i + 1, i + 2, ARGS.easeY);
}
return { x: AEK.motion.keys(X, c), y: AEK.motion.keys(Y, c) };
```

Measured: after separation the leader has 0 keys, X and Y are `OneD` with the same key times, all
linear. Different eases per axis (X out_cubic, Y out_expo) bent the path up to 158 px off the
straight line with no spatial handles. Recombining turned every key linear again.

## 6. Overshoot: curve, keys or expression

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), l = AEK.core.layer(c, ARGS.layer), s = AEK.core.prop(l, ["ADBE Transform Group", "ADBE Scale"]);
if (ARGS.method === "curve") { AEX.animation.move(s, c, 0, [0, 0], 12, [100, 100], "out_back"); }
if (ARGS.method === "keys") { AEX.animation.overshoot(s, c, 0, [0, 0], 8, 14, [100, 100], 10, 10, 80); }
if (ARGS.method === "spring") {
    AEX.animation.move(s, c, 0, [0, 0], 6, [100, 100], { out: 10, "in": 10 });
    AEK.expr.set(s, AEX.animation.springExpression(2.5, 6, 0.06));
    if (ARGS.bake) { AEK.expr.bake(s, c, 0, 60 * c.frameDuration); }
}
return AEK.motion.sample(s, c, 0, 60 * c.frameDuration);
```

```javascript
// expression (JavaScript engine): any layer > Scale or Rotation (overshoot after the LAST key)
// checked: live 27.0
var f=2.5,d=6,a=0.06;
var n=0; if (numKeys>0){ n=nearestKey(time).index; if (key(n).time>time) n--; }
if (n===0 || n<numKeys) { value; } else {
  var t=time-key(n).time; var v=velocityAtTime(key(n).time-thisComp.frameDuration/10);
  value + v*a*Math.sin(f*t*2*Math.PI)/Math.exp(d*t); }
```

Measured (Scale 0 to 100): curve peak 109.8 on frame 7, settle 11, 2 crossings; keys peak 110 on
frame 8, settle 12, 2 crossings; spring peak 109.1 on frame 8, settle 17, 10 crossings. Baking the
spring wrote 61 keys and disabled the expression with the same values. Keys for product work; the
spring for a deliberately elastic style.

## 7. Stagger: startTime, keys or a delay expression

```javascript
// expression (JavaScript engine): item N > Scale (item 0 carries the keys)
// checked: live 27.0
var lead = thisComp.layer("expr_0").transform.scale;
lead.valueAtTime(time - 3 * 3 * thisComp.frameDuration);
```

Measured: the three methods give identical values on every frame (4 items, 3 frames apart).
`"layer"` mode moves in-points to frames 0, 3, 6, 9 and the keys with them; `"keys"` mode keeps
every in-point at 0 and keeps the eases. Use the expression when one controller must drive many
copies that a person will retime once.

## 8. Parent to a null and scale the group

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), nul = AEK.build.nullLayer(c, "CTRL_group", { position: ARGS.pivot }), i;
for (i = 0; i < ARGS.layers.length; i++) { AEK.core.layer(c, ARGS.layers[i]).parent = nul; } // stays on screen
var s = AEK.core.prop(nul, ["ADBE Transform Group", "ADBE Scale"]);
AEX.animation.move(s, c, ARGS.f0, [100, 100], ARGS.f1, [50, 50], "in_out_cubic");
return { a: AEX.animation.compPoint(AEK.core.layer(c, ARGS.layers[0]), ARGS.f1 * c.frameDuration) };
```

Measured: a new null's anchor is [0, 0]. Children at x 300 and 900 under a null at 600 scaled to 50
% land at 450 and 750. `parent = null` kept a layer at its comp position (position rewritten to
[-500, -300]); `setParentWithJump` kept the numbers and moved it to the null's space. A stroked
child under the 50 % null renders its stroke at half width.

## 9. Motion blur by script, and what the smear measures

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), i, l;
c.motionBlur = true; c.shutterAngle = 180; c.shutterPhase = -90; // a new comp reads phase 0
for (i = 1; i <= c.numLayers; i++) { l = c.layer(i); if (!l.nullLayer && !l.isTrackMatte) { l.motionBlur = true; } }
return { angle: c.shutterAngle, phase: c.shutterPhase, samples: c.motionBlurSamplesPerFrame, limit: c.motionBlurAdaptiveSampleLimit };
```

Measured on a 100 px square at 30 px per frame (row of pixels read with ImageMagick): either switch
off gives a hard edge; 180 / -90 gives a 15 px ramp centered on each edge; 180 / 0 puts the whole 15
px ramp ahead of the object; 360 gives 30 px, 720 gives 60 px. New comps by script: switch off,
angle 180, phase 0, 16 samples, adaptive limit 128.

Samples: `motionBlurSamplesPerFrame` (2 to 64) sets the samples for Classic 3D layers, shape layers
and some effects; 2D layer motion adds samples up to `motionBlurAdaptiveSampleLimit` (16 to 256)
(doc `scripting-compitem-shutter`; -ZJKoNj4WpQ frame 00:05:30 shows 64 and 128). A fast shape layer
at the 16 samples of a scripted comp can show stepped copies instead of a smooth smear: look at the
fastest frame on the contact sheet and raise the samples until the steps merge.

## 10. Bounce and an onion skin (24 fps)

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), l = AEK.core.layer(c, ARGS.layer);
var p = AEK.core.prop(l, ["ADBE Transform Group", "ADBE Position"]);
p.dimensionsSeparated = true;
var Y = p.getSeparationFollower(1);
var keys = AEX.animation.bounce(Y, c, 0, 800, 600, 16, 4); // ground y 800, drop 600 px, 16-frame fall, 4 rebounds
// onion skin: Echo needs the motion inside a precomp; every layer reference is invalid after precompose
var idx = l.index, nm = l.name;
AEK.build.precompose(c, [idx], nm + "_onion", true);
AEK.build.effect(c.layer(idx), "ADBE Echo", {}, "onion");
var e = c.layer(idx).property("ADBE Effect Parade").property(1);
e.property(1).setValue(-2 * c.frameDuration); // ADBE Echo-0001 Echo Time (seconds)
e.property(2).setValue(22);                    // ADBE Echo-0002 Number Of Echoes
e.property(4).setValue(0.97);                  // ADBE Echo-0004 Decay
return keys;
```

Measured: apexes at frames 0, 24, 36, 42, 45 with heights 600, 300, 150, 75, 37.5; contacts at 16,
32, 40, 44, 46. With linear contact keys the ball slowed before two contacts (51 against 69 px per
frame); with broken Bezier contacts at speed 2h/d and influence 33.33 every contact frame is the
fastest of its fall. Echo match names: `ADBE Echo-0001` Echo Time (seconds), `-0002` Number Of
Echoes, `-0003` Starting Intensity, `-0004` Decay, `-0005` Echo Operator. Work on a duplicate comp
for the onion skin: precomposing changes the layer structure. Jake Bartlett's GUI rig uses 30
echoes, decay 0.95 and Echo Operator Composite In Front (7pOCtlrrE3Y 00:02:42, frame 00:03:28); this
block leaves the operator at its default, so set it in the Effect Controls panel when the current
frame must sit on top.

## 11. Motion blur per renderer

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), out = [], i, l;
for (i = 1; i <= c.numLayers; i++) {
    l = c.layer(i);
    if (l.nullLayer || !l.threeDLayer) { continue; }
    try { l.motionBlur = true; out.push({ layer: l.name, blur: true }); }
    catch (e) { out.push({ layer: l.name, blur: false, error: e.toString() }); } // the renderer refuses it
}
return { renderer: c.renderer, layers: out };
```

Measured: in a comp set to `ADBE Advanced 3d` (Classic 3D, the start value of a comp made by
script), a 3D solid took the layer switch and rendered the same 15 px centered smear as a 2D layer
(180 / -90, 30 px per frame). With `ADBE Calder` or `ADBE Ernst` as `comp.renderer`, setting
`layer.motionBlur` on a 3D layer threw "Motion blur is not supported by the current composition
renderer"; the comp switch still read true. Saving a frame of that comp with `ADBE Ernst` stalled
for over 60 s: keep review frames on the default renderer. Always wrap the layer switch in try and
read the result back.

## 12. Motion report (read-only review)

```bash
python3 <expert>/scripts/ae.py run <this skill>/scripts/motion_report.jsx --lib <this skill>/scripts/animation.jsx --args '{"comp": "product_card"}'
```

Returns per layer and animated transform property: keys (frame, in/out type, influences), peak speed
per frame, peak frame, overshoot %, settle frame; then `motionCheck` and the blur settings.
Separated Position followers are included. Measured on the product card: 124 ms; the separated phone
Y is reported as `ADBE Position_1` (X is `ADBE Position_0`) with keys "0 b/b in 17 out 10", "15 b/b
in 75 out 50", "24 b/b in 80 out 17", peak 207.7 px per frame, overshoot 3 %, settle frame 20; chips
scale overshoot 9.7 %, settle 28, 31, 34; no findings. Read-only: safe in a person's session (pass
no `open`).

## 13. Frames and the contact sheet

```bash
python3 <expert>/scripts/ae.py frames "product_card" --times 0,0.133,0.267,0.4,0.5,0.6,0.7,0.8,0.9,1,3,5.067,5.167,5.267,5.367,5.467 --out <project>/review/card --sheet
```

Times are seconds: at 30 fps frame N is N / 30. Read the one sheet; judge with
[critique.md](critique.md).
