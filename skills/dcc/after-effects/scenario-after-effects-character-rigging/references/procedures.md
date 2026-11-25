# Procedures

Every job is a function body for
`ae.py run job.jsx --lib <skill>/scripts/rig.jsx --undo "Agent: <what>" --args '<json>'`. Jobs that
build test scenes start with `AEK.core.fresh()`: never in a person's session. In a person's project,
drop that line, take `AEK.session.state()` first and `restore()` last (lead skill). Layer names are
the rig's API: expressions find layers by name, so keep them unique.

`AEX.rig` (scripts/rig.jsx), every function run on 27.0:

| Function                                                                        | Does                                                                     |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `limb(comp, name, length, width, color, pivot)`                                 | capsule shape layer, pivot at [0, 0], round ends centered on both joints |
| `part(comp, name, spec, pivot)`                                                 | any shape spec drawn around its pivot                                    |
| `pivot(layer, [x, y])`                                                          | anchor onto a comp point without moving the art (unparented layers)      |
| `chain([root, ..., tip])`                                                       | parents in order, keeps each layer on screen                             |
| `world(comp, layer, point or null, [seconds])`                                  | comp position of a layer point through a temporary `toComp()` probe      |
| `ik({upper, lower, tip, ctrl})`                                                 | two-bone IK expressions, Flip and Stretch checkboxes on the controller   |
| `orientTo(layer, ctrl)`                                                         | layer keeps the controller's world angle                                 |
| `keys(prop, comp, [[frame, value, in, out]])`                                   | keys in frames; ease 0 linear, a number = influence, "h" hold            |
| `loop(prop, "out" or "both" or "continue")`                                     | cycle after the last key, before the first key too, or travel            |
| `drag(prop, driver, frames, gain)`, `echo(prop, src, expr, frames, gain, rest)` | follow-through and delayed copies                                        |
| `swap(layers, ctrl, slider)`, `holdKeys(prop, comp, [[frame, value]])`          | one visible layer per slider value; stepped keys                         |
| `character(comp, o)`, `walk(comp, ch, o)`                                       | the test character and its 24-frame walk (reference build)               |

## 1. Pivots and the parent chain

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {"comp": "char", "pivots": {"R upper arm": [400, 242], "R forearm": [400, 362]}, "chains": [["torso", "R upper arm", "R forearm", "R hand"]]}
var c = AEK.core.comp(ARGS.comp), out = { pivots: [], chains: [], moved: [] }, k, i, l, before, after;
for (k in ARGS.pivots) {
    if (!ARGS.pivots.hasOwnProperty(k)) { continue; }
    l = AEK.core.layer(c, k);
    before = AEX.rig.world(c, l, [0, 0], [0])[0];          // a fixed art point, layer space
    out.pivots.push(AEX.rig.pivot(l, ARGS.pivots[k]));
    after = AEX.rig.world(c, l, [0, 0], [0])[0];
    out.moved.push(k + ": " + (Math.abs(after[0] - before[0]) + Math.abs(after[1] - before[1])) + " px");
}
for (i = 0; i < ARGS.chains.length; i++) {
    var list = [];
    for (k = 0; k < ARGS.chains[i].length; k++) { list.push(AEK.core.layer(c, ARGS.chains[i][k])); }
    out.chains.push(AEX.rig.chain(list));
}
return out;
```

Check: every `moved` value is 0. Joint positions come from a joint-marker layer or a table the
artist gives (Jake Bartlett's joint markers, zbrO6GrxtQg 00:24:47); never guess them from bounds
unless the art is drawn to a rule (round end of radius r at the top:
`AEK.build.anchor(layer, 0.5, r / height)`). Measured: a 60 x 300 PNG limb, anchor [30, 150] moved
to the joint [30, 30], art moved 0 px, its tip rotated 90 degrees landed on [760, 180] as computed.

## 2. Two-bone IK

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {"comp": "char", "limbs": [["R thigh", "R shin", "R foot", "CTRL_FOOT_R"], ["L thigh", "L shin", "L foot", "CTRL_FOOT_L"]], "orient": true}
var c = AEK.core.comp(ARGS.comp), out = [], i, s, L;
for (i = 0; i < ARGS.limbs.length; i++) {
    s = ARGS.limbs[i];
    L = { upper: AEK.core.layer(c, s[0]), lower: AEK.core.layer(c, s[1]), tip: AEK.core.layer(c, s[2]), ctrl: AEK.core.layer(c, s[3]) };
    AEX.rig.ik(L);
    if (ARGS.orient) { AEX.rig.orientTo(L.tip, L.ctrl); }
    var w = AEX.rig.world(c, L.tip, null, [0])[0], t = AEX.rig.world(c, L.ctrl, null, [0])[0];
    out.push({ limb: s[0], errPx: Math.sqrt(Math.pow(w[0] - t[0], 2) + Math.pow(w[1] - t[1], 2)) });
}
return { limbs: out, check: AEK.expr.check(c, 5) };
```

The upper-limb Rotation expression it writes for the right leg (the lower limb's Rotation ends with
`radiansToDegrees(bend * (Math.PI - B) + r1 - r2) + value;`, the upper Scale with
`[value[0], value[1] * k];`):

```javascript
// expression (JavaScript engine): upper limb layer > Rotation
// checked: live 27.0
var c = thisComp.layer("CTRL_FOOT_R"), up = thisComp.layer("R thigh"), lo = thisComp.layer("R shin"), en = thisComp.layer("R foot");
var e = lo.transform.position, f = en.transform.position, L1 = length(e), L2 = length(f);
var S = up.hasParent ? up.parent.toComp(up.transform.position) : up.transform.position;
var T = c.toComp(c.transform.anchorPoint), D = sub(T, S), d = length(D);
var bend = c.effect("Flip")(1).value ? -1 : 1;
var k = (c.effect("Stretch")(1).value && d > L1 + L2) ? d / (L1 + L2) : 1;
var l1 = L1 * k, l2 = L2 * k, dd = Math.min(Math.max(d, Math.abs(l1 - l2) + 0.001), l1 + l2);
var A = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd))));
var B = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + l2 * l2 - dd * dd) / (2 * l1 * l2))));
var r1 = Math.atan2(e[1], e[0]), r2 = Math.atan2(f[1], f[0]);
var pr = 0;
if (up.hasParent) { var v = up.parent.toCompVec([1, 0]); pr = Math.atan2(v[1], v[0]); }
radiansToDegrees(Math.atan2(D[1], D[0]) - bend * A - r1 - pr) + value;
```

Why this shape: limb lengths are read from the rig (child positions), so art drawn in any direction
works; the parent's world angle comes from `toCompVec`, which includes every rotation above it; the
shoulder is read from the parent, never from the layer's own `toComp`, so the expression does not
read itself.

Measured (upper 160 px, lower 140 px, parent rotated 10 degrees, 80 controller positions): error
0.0000 px at radii 30 to 300; at 10 px (under the 20 px minimum reach) 10 px; at 320 and 400 the arm
points at the target with 0 degree error and falls short by 20 and 100 px; Flip moves every elbow to
the other side; Stretch reaches 400 px with upper Scale Y 133.3 %, and the hand under the forearm
stretches by the same 1.333.

Bend direction: with Flip off, a limb hanging down bends its middle joint toward +x. A character
facing +x gets forward knees with Flip off.

## 2b. Zero nulls, lock and shy

Duik's Add Zero, then its cleanup, in native layers (Jake Bartlett, Y0RRBVnn2MA 00:29:38 to
00:31:30):

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {"comp": "char", "controllers": ["CTRL_FOOT_R", "CTRL_FOOT_L"], "root": "CTRL_ROOT"}
var c = AEK.core.comp(ARGS.comp), out = { zeroed: [], locked: 0 }, i, l, z, P;
for (i = 0; i < ARGS.controllers.length; i++) {
    l = AEK.core.layer(c, ARGS.controllers[i]);
    P = l.property("ADBE Transform Group").property("ADBE Position");
    z = AEK.build.nullLayer(c, "ZERO_" + l.name, { position: P.value });
    z.parent = AEK.core.layer(c, ARGS.root);
    z.moveAfter(l);
    l.parent = z;                                    // keeps the world position: Position now reads [0, 0]
    out.zeroed.push(l.name + " " + P.value.toString());
}
for (i = 1; i <= c.numLayers; i++) {
    l = c.layer(i);
    if (l.name.indexOf("CTRL_") === 0) { continue; }
    l.shy = true; l.locked = true; out.locked++;
}
c.hideShyLayers = true;
return out;
```

Check: every `zeroed` entry ends in `0,0,0`. Run it before any controller is keyed. Measured: the
controller read [0, 0, 0] after parenting; an expression on a locked art layer still followed its
controller; `setValue` on a locked layer's Opacity was accepted, so a script must not rely on the
lock to protect art.

## 3. Walk cycle in frames

```javascript
// channel: bridge | handoff
// checked: live 27.0
// The reference build: test character, 24-frame walk at 24 fps, stride 200 px, travel on CTRL_ROOT.
AEK.core.fresh();
var c = AEK.build.comp("walk", { width: 1280, height: 720, fps: 24, duration: 3, bg: [0.93, 0.93, 0.9] });
var ch = AEX.rig.character(c, { x: 300, ground: 600 });
var w = AEX.rig.walk(c, ch, { cycle: 24, stride: 200, travel: true, bodyLoop: "both" });
function fr(a, b) { var t = [], f; for (f = a; f <= b; f++) { t.push(f * c.frameDuration); } return t; }
var p = AEX.rig.world(c, ch.L.Rft, null, fr(0, 12)), xs = [], i;
for (i = 0; i < p.length; i++) { xs.push(p[i][0]); }
return { walk: w, plantedXFirst: xs[0], plantedXLast: xs[xs.length - 1], check: AEK.expr.check(c, 12),
    poses: AEK.capture.frames(c, [0, 3 / 24, 6 / 24, 9 / 24, 12 / 24], ARGS.out, "pose") };
```

What `walk()` keys, right contact on frame 0, left on 12:

| Controller       | Keys (frame: value)                        | Interpolation                                           |
| ---------------- | ------------------------------------------ | ------------------------------------------------------- |
| right foot X     | 0: +100, 12: -100, 24: +100                | linear, `loopOut("cycle")`                              |
| right foot Y     | 0: 0, 12: 0, 18: -50, 24: 0                | ease out of the ground at 12, eased top, linear landing |
| right foot angle | 0: -10, 3: 0, 9: 0, 12: 18, 18: 0, 24: -10 | heel strike, flat, heel off                             |
| left foot        | the same, 12 frames later                  |                                                         |
| hips Y           | 3: +14, 9: -14, 15: +14, 21: -14, 27: +14  | eased, loop before and after                            |
| upper arms       | 3: +22, 15: -22, 27: +22 (left opposite)   | eased, loop before and after                            |
| forearms         | `drag` 2 frames, gain 0.6, rest -12        | expression                                              |
| head             | `echo` of hips Y, 2 frames, gain 0.25      | expression                                              |
| root X           | 0: x, 24: x + 400                          | linear, `loopOut("continue")` on the separated X        |

Checks measured on 27.0: IK foot error 3e-13 px over 48 frames; planted foot spread 0.000 px in X
and Y over frames 0 to 12, 12 to 24 and 24 to 36; in place (travel off), frame 0 and frame 24
identical, frame 48 identical, frames 23 and 24 differ by 24,000 pixels. Same rig with `loopOut()`
only on the hips: frames 0 to 3 all hold -226, frame 24 reads -240, frames 0 and 24 differ by 31,858
pixels.

The loop before the first key:

```javascript
// expression (JavaScript engine): any looped property whose first key is after frame 0 > Rotation, Position X/Y
// checked: live 27.0
time < key(1).time ? loopIn("cycle") : loopOut("cycle");
```

The pixel-identical seam holds only where nothing travels. A character that travels 400 px per cycle
is compared after cropping both frames by that offset (measured 0 pixels differ on a 1280 px shot).
Frame N repeats frame 0, so a loop file renders frames 0 to N-1 (School of Motion walk: "I actually
only want to play the first 23 frames").

Compare frames outside After Effects:

```bash
magick compare -metric AE <out>/place_f00000.png <out>/place_f00024.png null:   # in place: 0 = seamless
magick <out>/shot_f00000.png -crop 600x720+0+0 +repage a.png; magick <out>/shot_f00024.png -crop 600x720+400+0 +repage b.png
magick compare -metric AE a.png b.png null:                                    # travel 400 px per cycle: 0 = seamless
python3 <lead>/scripts/ae.py sheet <out>/poses.jpg <out>/pose_f0000{0,3,6,9}.png <out>/pose_f00012.png
```

## 4. Cycle into a shot (Time Remap and travel)

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {"shot": "shot", "cycleComp": "walk_inplace", "cycleFrames": 24, "stride": 200, "start": [100, 360]}
var c = AEK.core.comp(ARGS.shot), wl = c.layers.add(AEK.core.comp(ARGS.cycleComp));
wl.timeRemapEnabled = true;
var tr = wl.property("ADBE Time Remapping");
// loopOut("cycle") on Time Remap keyed 0 to N rendered frame N blank: count frames instead
AEK.expr.set(tr, "framesToTime(timeToFrames(time) % " + ARGS.cycleFrames + ");");
wl.outPoint = c.duration;
var pos = wl.property("ADBE Transform Group").property("ADBE Position");
pos.dimensionsSeparated = true;
var X = pos.getSeparationFollower(0);
pos.getSeparationFollower(1).setValue(ARGS.start[1]);
AEX.rig.keys(X, c, [[0, ARGS.start[0], 0, 0], [ARGS.cycleFrames, ARGS.start[0] + 2 * ARGS.stride, 0, 0]]);
AEX.rig.loop(X, "continue");
return { remapFrames: [tr.valueAtTime(23 / 24, false) * 24, tr.valueAtTime(1, false) * 24, tr.valueAtTime(25 / 24, false) * 24], x3s: X.valueAtTime(3, false) };
```

`cycleFrames` is N, the frames between two contacts of the same foot (Evan Abrams drops markers on
them, 1DiKTiOmrHE 00:10:37). The cycle precomp may be exactly N frames long. Measured with a
24-frame cycle: remap frames 23, 0, 1 at shot frames 23, 24, 25; shot frame 24 equals frame 0
shifted 400 px (0 pixels differ); X 1300.000 at 3 s. With Evan Abrams' setup (Time Remap keyed 0 and
1 s, `loopOut("cycle")`) the script read 1.0 s at frame 24, but frame 24 rendered blank at the first
seam and correct at frame 48, with a 1 s and with a 2 s cycle comp. Keys at 0 and 23 frames with
`loopOut("cycle")` skipped inner frame 0 instead. The same travel on combined Position with
`loopOut("continue")` read 1299.43 at 3 s instead of 1300: separate the dimensions. A stop or a turn
is a separate one-step timeline swapped in (School of Motion walk).

## 5. Overlap, follow-through, hair

```javascript
// expression (JavaScript engine): hand or forearm layer > Rotation
// checked: live 27.0
var r = thisComp.layer("R forearm").transform.rotation, n = 3 * thisComp.frameDuration;
value + 0.5 * (r.valueAtTime(time - n) - r);
```

```javascript
// expression (JavaScript engine): hair segment i (chained) > Rotation
// checked: live 27.0
var i = 2, amp = 6 + 4 * i, fq = 1.2, dl = 2 * i * thisComp.frameDuration;
value + 20 + amp * Math.sin(2 * Math.PI * fq * (time - dl));
```

Measured: the drag term follows the driver's speed, so it peaks while the driver moves fastest and
returns to 0 on its holds (hand range plus or minus 21.8 degrees on a 50-degree forearm wave); the
head echo peaked on frame 29 for a hip low on 27; hair segments peaked on frames 5, 7, 9, 11.
Anthony Possobon drives every strand from master sliders (frequency, amplitude, offset) and animates
the gust as frequency first, amplitude keys slid later (oiEjz_-8wfk 00:28:16).

Wave with anticipation (upper arm, FK), frames relative to the wave's start:
`[[0, 0], [4, 8], [10, -133], [14, -125], [40, -125], [48, 0]]` measured overshoot 6.4 %, peak speed
frame 7. Add the start frame to each key; the last key (start + 48) must be on or before the clip's
last frame, duration x fps - 1 (frame 95 for 4 s at 24 fps). In a shorter window, cut the hold (14
to 40) first: a wave starting on frame 56 of a 96-frame clip holds to 32 and returns 32 to 39
(relative). Only then scale the other keys [added]; the forearm keyed plus or minus 25 degrees on a
10-frame period. Raise a side-view arm forward and up (about -125 degrees): at -150 the arm crossed
the face on the contact sheet.

## 6. Mouth shapes from a voice file

```bash
python3 <skill>/scripts/audio_to_mouth.py voice.wav --fps 24 --shapes 3 --min-hold 2 --lead 1 > mouth.json
python3 <lead>/scripts/ae.py run face.jsx --lib <skill>/scripts/rig.jsx --args "{\"comp\": \"char\", \"mouth\": $(cat mouth.json)}"
```

```javascript
// channel: bridge | handoff
// checked: live 27.0
// Mouth layers "mouth 0 closed", "mouth 1 mid", "mouth 2 open" under the head; slider "Mouth" on CTRL_FACE.
var c = AEK.core.comp(ARGS.comp), face = AEK.core.layer(c, "CTRL_FACE");
var mouths = [AEK.core.layer(c, "mouth 0 closed"), AEK.core.layer(c, "mouth 1 mid"), AEK.core.layer(c, "mouth 2 open")];
AEX.rig.swap(mouths, face, "Mouth");
var s = face.property("ADBE Effect Parade").property("Mouth").property(1), i, gap = 999;
AEX.rig.holdKeys(s, c, ARGS.mouth.keys);
for (i = 2; i <= s.numKeys; i++) { gap = Math.min(gap, Math.round((s.keyTime(i) - s.keyTime(i - 1)) * c.frameRate)); }
return { keys: s.numKeys, minGapFrames: gap, check: AEK.expr.check(c, 5) };
```

Measured on a 3.9 s voice line (macOS `say`, 48 kHz): 95 frames, 16 silent, threshold between mid
and open -20.45 dB RMS, 24 hold keys, minimum gap 2 frames, the right mouth visible on 8 probed
frames. The precomp route (one mouth per second, Time Remap from the slider, Ihor 00:02:28) gave the
same shapes:

```javascript
// expression (JavaScript engine): mouth precomp layer > Time Remap
// checked: live 27.0
Math.round(effect("Mouth")(1)) * 1 + 0.5 * thisComp.frameDuration;
```

The half frame keeps the remap inside the shape's second. Convert Audio to Keyframes (menu id 4218
on 27.0, look it up by label) ran from a job with no dialog: comp open in the viewer, audio layer
selected, `app.executeCommand(id)`; it made "Audio Amplitude" with Left Channel, Right Channel and
Both Channels sliders, one key per frame (97 keys for 96 frames), peak 24.7. Its keys still need
thresholds and a minimum hold before they drive mouths.

## 7. Blink and joystick

```javascript
// expression (JavaScript engine): CTRL_FACE > Effects > Eyes > Slider
// checked: live 27.0
var f = timeToFrames(time), period = Math.round(2.5 / thisComp.frameDuration), w = Math.floor(f / period);
seedRandom(w, true);
var start = w * period + Math.floor(random(0.25, 0.75) * period);
(f >= start && f < start + 3) ? 1 : 0;
```

Measured: closed runs of 3 frames starting at 40, 77, 136, 200 (24 fps). Key blinks by hand where
the acting needs them (before a head turn, on a thought).

```javascript
// expression (JavaScript engine): eye or mouth layer > Position (joystick knob "JOY" parented to a 200 x 200 box)
// checked: live 27.0
var j = thisComp.layer("JOY").transform.position, x = clamp(j[0], -100, 100), y = clamp(j[1], -100, 100);
value + [linear(x, -100, 100, -48, 0), linear(y, -100, 100, -16, 16)];
```

Measured: the eyes moved 48 px between knob right and left, the head tilted -8 degrees at the top
edge, a knob keyed to [150, 150] clamped to [100, 100]. Anthony Possobon's controller null is 100 px
so its position reads as a percentage (EP8OaGisJr0 00:15:14).

## 8. Puppet by script: what works

```javascript
// channel: bridge
// checked: live 27.0
var l = AEK.core.layer(AEK.core.comp(ARGS.comp), ARGS.layer);
var fx = l.property("ADBE Effect Parade").addProperty("ADBE FreePin3");
var mg = l.property("ADBE Effect Parade").property(fx.propertyIndex).property("ADBE FreePin3 ARAP Group").property("ADBE FreePin3 Mesh Group");
mg.addProperty("ADBE FreePin3 Mesh Atom");
var mesh = mg.property(1);
return { density: mesh.property("ADBE FreePin3 Mesh Tri Density").value, triangles: mesh.property("ADBE FreePin3 Mesh Tri Count").value };
```

Measured tree under `ADBE FreePin3 Mesh Atom`: `ADBE FreePin3 Mesh`, `Mesh Tri Count` (350),
`Mesh Tri Density` (10), `Mesh Expansion` (3), `ADBE FreePin3 PosPins` (Deform),
`ADBE FreePin3 HghtPins` (Overlap), `ADBE FreePin3 StarchPins` (Stiffness).
`ADBE FreePin3 PosPin Atom` and `ADBE FreePin3 HghtPin Atom` can be added; no Starch name tried was
accepted. A scripted pin has Vertex Index -1; `setValue` on its `ADBE FreePin3 PosPin Position`
throws "invalid numeric result", `setValueAtTime` is accepted, and the frames before and after
differ by 0 pixels. Use: place pins by hand, then key, record and loop them by script
(`loopOut("pingpong")` on recorded pins, Jordan Bertone 00:01:28).

## 9. Look: on twos and boil

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var twos = AEK.build.adjustment(c, "on twos");
AEK.build.effect(twos, "ADBE Posterize Time", { "ADBE Posterize Time-0001": 12 });
var boil = AEK.build.adjustment(c, "boil");
AEK.build.effect(boil, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 12, "ADBE Turbulent Displace-0003": 3 });
AEK.expr.set(boil.property("ADBE Effect Parade").property(1).property("ADBE Turbulent Displace-0010"), "Math.floor(timeToFrames(time) / 2);");
return AEK.capture.frames(c, [0, 1 / 24, 2 / 24, 3 / 24], ARGS.out, "look");
```

Measured: frames 0 and 1 identical, 1 and 2 differ, 2 and 3 identical. Turbulent Displace lists two
properties named "Random Seed": `-0010` takes the value and the expression, `-0011` has no value and
refuses an expression. Ben Marriott's `time*4` changes the seed 4 times a second, about every 6
frames at 24 fps [added].
