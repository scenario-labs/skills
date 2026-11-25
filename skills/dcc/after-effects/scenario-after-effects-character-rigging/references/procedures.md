# Procedures

Every job is a function body for
`ae.py run job.jsx --lib <skill>/scripts/rig.jsx --undo "Agent: <what>" --args '<json>'`. Jobs that
build test scenes start with `AEK.core.fresh()`: never in a person's session. In a person's project,
drop that line, take `AEK.session.state()` first and `restore()` last (lead skill). Layer names are
the rig's API: expressions find layers by name, so keep them unique.

`AEX.rig` (scripts/rig.jsx), every function run on 27.0:

| Function                                                                        | Does                                                                                                      |
| ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `limb(comp, name, length, width, color, pivot)`                                 | capsule shape layer, pivot at [0, 0], round ends centered on both joints                                  |
| `part(comp, name, spec, pivot)`                                                 | any shape spec drawn around its pivot                                                                     |
| `pivot(layer, [x, y])`                                                          | anchor onto a comp point without moving the art (unparented layers)                                       |
| `chain([root, ..., tip])`                                                       | parents in order, keeps each layer on screen                                                              |
| `world(comp, layer, point or null, [seconds])`                                  | comp position of a layer point through a temporary `toComp()` probe                                       |
| `ik({upper, lower, tip, ctrl})`                                                 | two-bone IK expressions, Flip and Stretch checkboxes on the controller                                    |
| `orientTo(layer, ctrl)`                                                         | layer keeps the controller's world angle                                                                  |
| `keys(prop, comp, [[frame, value, in, out]])`                                   | keys in frames; ease 0 linear, a number = influence, "h" hold                                             |
| `loop(prop, "out" or "both" or "continue")`                                     | cycle after the last key, before the first key too, or travel                                             |
| `drag(prop, driver, frames, gain)`, `echo(prop, src, expr, frames, gain, rest)` | follow-through and delayed copies                                                                         |
| `swap(layers, ctrl, slider)`, `holdKeys(prop, comp, [[frame, value]])`          | one visible layer per slider value; stepped keys                                                          |
| `character(comp, o)`, `walk(comp, ch, o)`                                       | the test character (`scale` through CTRL_ROOT) and its walk: foot roll, torso ahead of the hips, `stopAt` |
| `zero(ctrl, root)`                                                              | controller under a `ZERO_` null at its rest pose: Position [0, 0], world unchanged                        |
| `hang(layer, o)`                                                                | damped pendulum on Rotation for a hanging prop                                                            |
| `bounds(comp, t)`                                                               | comp box of the visible art, with its height in % of the frame                                            |
| `cycleCode(N, stop)`                                                            | the cycle expression head: keys repeat before and after, own keys from the stop                           |

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

Check: every `moved` value is 0. Joint circles are centered on the limb in Illustrator Outline view
(Jake Bartlett, zbrO6GrxtQg 00:17:27); a top "joint markers" layer copied from those circles gives
the pivot table. Joint positions come from a joint-marker layer or a table the artist gives (Jake
Bartlett's joint markers, zbrO6GrxtQg 00:24:47); never guess them from bounds unless the art is
drawn to a rule (round end of radius r at the top: `AEK.build.anchor(layer, 0.5, r / height)`).
Measured: a 60 x 300 PNG limb, anchor [30, 150] moved to the joint [30, 30], art moved 0 px, its tip
rotated 90 degrees landed on [760, 180] as computed.

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
var S = up.transform.position, Tw = c.toComp(c.transform.anchorPoint);
var T = up.hasParent ? up.parent.fromComp(Tw) : Tw, D = sub(T, S), d = length(D);
var bend = c.effect("Flip")(1).value ? -1 : 1;
var k = (c.effect("Stretch")(1).value && d > L1 + L2) ? d / (L1 + L2) : 1;
var l1 = L1 * k, l2 = L2 * k, dd = Math.min(Math.max(d, Math.abs(l1 - l2) + 0.001), l1 + l2);
var A = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd))));
var B = Math.acos(Math.min(1, Math.max(-1, (l1 * l1 + l2 * l2 - dd * dd) / (2 * l1 * l2))));
var r1 = Math.atan2(e[1], e[0]), r2 = Math.atan2(f[1], f[0]);
radiansToDegrees(Math.atan2(D[1], D[0]) - bend * A - r1) + value;
```

Why this shape: the triangle is solved in the parent's own space. The controller is brought there
with `parent.fromComp`, where the shoulder is the layer's Position and the limb lengths are the
children's Positions. Every transform above the limb, rotation, scale or a non-uniform squash, is
then inside the same space, so the tip lands on its controller in all cases. Limb lengths are read
from the rig, so art drawn in any direction works, and the expression never reads its own layer.

Measured (upper 160 px, lower 140 px, parent rotated 10 degrees, 80 controller positions): error
0.0000 px at radii 30 to 300, and 10 px at 10 px (under the 20 px minimum reach). At 320 and 400 the
arm points at the target with 0 degree error and falls short by 20 and 100 px. Flip moves every
elbow to the other side. Stretch reaches 400 px with upper Scale Y 133.3 %, and the hand under the
forearm stretches by the same 1.333. Under a body squashed by its parent's Scale (108/92, 92/108,
110/90 with a 6 degree tilt, root at 140 %), 12 targets each: 0 px. The earlier comp-space solver
missed by 14.2 to 16.7 px there.

Bend side: with Flip off, the middle joint sits on the left of the shoulder-to-target direction, as
seen by someone walking toward the target. Reaching down, that is +x: a character facing +x gets
forward knees with Flip off. Reaching up, it is -x: the same arm's elbow swaps side. Measured on a
front-view arm with Flip off: elbow 68 px out with the hand on the hip, 48 px in with the hand
raised. Run the pose test (2c) before keying: an arm that both reaches up and rests on the hip needs
Flip keyed between the two.

## 2b. Zero nulls, lock and shy

Duik's Add Zero, then its cleanup, in native layers (Jake Bartlett, Y0RRBVnn2MA 00:29:38 to
00:31:30):

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {"comp": "char", "controllers": ["CTRL_FOOT_R", "CTRL_FOOT_L"], "root": "CTRL_ROOT"}
var c = AEK.core.comp(ARGS.comp), root = AEK.core.layer(c, ARGS.root), out = { zeroed: [], locked: 0 }, i, l;
for (i = 0; i < ARGS.controllers.length; i++) {
    out.zeroed.push(AEX.rig.zero(AEK.core.layer(c, ARGS.controllers[i]), root));   // {zero, parent, position}
}
for (i = 1; i <= c.numLayers; i++) {
    l = c.layer(i);
    if (l.name.indexOf("CTRL_") === 0) { continue; }
    l.shy = true; l.locked = true; out.locked++;
}
c.hideShyLayers = true;
return out;
```

Check: every `zeroed` entry has position [0, 0]. Run it before any controller is keyed. `zero()`
puts the `ZERO_` null under the controller's current parent (or the root when it has none), at the
controller's Position, with anchor [0, 0], rotation 0 and scale 100. Measured: a controller under a
parent moved to [500, 300] and rotated 20 degrees read [0, 0] after `zero()`, moved 0 px in the comp
and kept its own 15 degree rotation. The earlier recipe (null created at the parent-space Position,
then parented to the root) gave the controller [476.9, 331.2] and moved it. An expression on a
locked art layer still followed its controller; `setValue` on a locked layer's Opacity was accepted,
so a script must not rely on the lock to protect art.

## 2c. Character setup: proportions, squash, limits, pose test, rig check

Ask before rigging, and measure on the art. Limb width about 0.14 of the body width (thinner reads
as sticks), hand about 1.4 x the arm width. Reach (upper + lower) about 0.4 of the body height for a
mascot. Shoulder pivots 20 to 40 px inside the body edge, arms drawn behind the body. A front-view
arm hanging straight down hides behind a wide body: rest it 15 to 20 degrees out.

Squash a body on its ART layer, never on a layer that limbs hang from. The arms ride the squash
through `attach`: their Position follows a point of the body art through `toComp`, and they keep
their shape. `check` fails the rig on a sheared limb parent.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {"comp": "char"}. Layers: CTRL_ROOT > CTRL_BODY (bounce keys) > body (art, anchor on its base); arms under CTRL_BODY;
// shoulders at [-160, -300] and [160, -300] in the body art; IK on the L arm to CTRL_HAND_L. Needs --lib rig.jsx.
var c = AEK.core.comp(ARGS.comp), L = function (n) { return AEK.core.layer(c, n); }, FD = c.frameDuration, T = [], i;
AEX.rig.attach(L("R upper arm"), L("body"), [-160, -300]);
AEX.rig.attach(L("L upper arm"), L("body"), [160, -300]);
AEX.rig.squash(L("body"), L("CTRL_BODY"), { stretch: 0.5, squash: 1.6, max: 10 });   // volume kept, X = 10000 / Y
AEX.rig.limit(L("R upper arm").property("ADBE Transform Group").property("ADBE Rotate Z"), L("CTRL_ROOT"), -20, 135);
for (i = 0; i < c.duration / FD; i += 3) { T.push(i * FD); }
return AEX.rig.check(c, { ik: [["L hand", "CTRL_HAND_L"]], limbs: ["L upper arm", "R upper arm"], times: T });
```

Order: `limit` before keys is fine; it throws when the property already has an expression (end that
expression with `clamp` instead). Keyed 140 degrees, the limited arm read 135. `check` returns
`dupNames`, `ikError` (px per tip over the times), `shear` (limb ancestors whose Scale X and Y
differ by more than 0.5 %), `restOff` (controllers not at [0, 0]) and `ok`. Measured: squash on
CTRL_BODY (108/92) gave `shear` on CTRL_BODY and `ok` false, with the IK still at 0 px. Squash on
the body art with attached arms gave `ok` true and IK 0 px over 32 times. Body Scale went from
111/90 at contact to 94/106 on the rise.

A bounce for a character that does not walk: keys on CTRL_BODY Y only (separated), contact 0, top 9
to 15 (the hang), contact 24, eased 70 % at the top. Loop it with `cycleCode(24)`, and scale the
shadow down to 78 % at the top. Measured: frame 0 and frame 96 render identical (0 pixels differ).

Keep each IK controller inside 0.9 of the reach through the whole shot, bounce, squash and lean
included: past the reach the hand stops short by design. Measured on a hip controller: 1.04 of the
reach during a 5 degree lean put the hand 11.7 px off; moved 30 px in, 0.88 and 0 px.

Pose test before any key: set rest, arms up and the gesture's extreme pose (hand on hip, reach) with
`setValue`, capture each with `AEK.capture.frame`, and read the elbow side as the offset of the
elbow from the shoulder-to-hand line. Each elbow must point away from the body in every pose; the
measure catches a wrong Flip or a forearm sign before any animation is keyed.

## 3. Walk cycle in frames

```javascript
// channel: bridge | handoff
// checked: live 27.0
// The reference build: test character, 24-frame walk at 24 fps, stride 200 px, travel on CTRL_ROOT. ARGS: {"out": "<folder>"}
AEK.core.fresh();
var c = AEK.build.comp("walk", { width: 1280, height: 720, fps: 24, duration: 3, bg: [0.93, 0.93, 0.9] });
var ch = AEX.rig.character(c, { x: 300, ground: 600 });
var w = AEX.rig.walk(c, ch, { cycle: 24, travel: true });
function fr(a, b) { var t = [], f; for (f = a; f <= b; f++) { t.push(f * c.frameDuration); } return t; }
var r = ch.L.Rft.sourceRectAtTime(0, false), heel = AEX.rig.world(c, ch.L.Rft, [r.left, r.top + r.height], fr(24, 33)), xs = [], i;
for (i = 0; i < heel.length; i++) { xs.push(heel[i][0]); }
return { walk: w, heelSpread: Math.max.apply(null, xs) - Math.min.apply(null, xs), check: AEK.expr.check(c, 12),
    poses: AEK.capture.frames(c, [0, 3 / 24, 6 / 24, 9 / 24, 12 / 24], ARGS.out, "pose") };
```

What `walk()` keys, right contact on frame 0, left on 12 (frames for a 24-frame cycle; other cycles
scale them):

| Controller       | Keys (frame: value)                        | Interpolation                                                          |
| ---------------- | ------------------------------------------ | ---------------------------------------------------------------------- |
| right foot X     | 0: +100, 12: -100, 24: +100                | linear, cycled                                                         |
| right foot Y     | 0: 0, 12: 0, 18: -50, 24: 0                | ease out of the ground at 12, eased top, linear landing                |
| right foot angle | 0: -10, 3: 0, 9: 0, 12: 18, 18: 0, 24: -10 | heel strike, flat, heel off                                            |
| foot roll        | X and Y expressions add `c - R(angle) c`   | pivot on the toe while the heel is up, on the heel while the toe is up |
| left foot        | the same, 12 frames later                  |                                                                        |
| hips Y           | 3: +14, 9: -14, 15: +14, 21: -14, 27: +14  | eased, cycled before and after                                         |
| torso rotation   | 2: lean + tilt, 8: lean - tilt, 14, 20, 26 | 1 frame before the hips; lean 4, tilt 2 degrees                        |
| upper arms       | 3: +22, 15: -22, 27: +22 (left opposite)   | eased, cycled before and after                                         |
| forearms         | `drag` 2 frames, gain 0.6, rest -12        | expression                                                             |
| head             | `echo` of hips Y, 2 frames, gain 0.25      | expression                                                             |
| root X           | 0: x, 24: x + 400 x root scale             | linear, `loopOut("continue")` on the separated X                       |

Cycled means the expression from `AEX.rig.cycleCode(N, stop)`:
`valueAtTime(k1 + (((t - k1) % T) + T) % T)`, the keys repeating before the first key and after the
last, then the property's own keys from the stop frame on. Stride, lift and bob scale with `o.leg`
(hip to ankle, straight; defaults are for 262 px). `walk()` returns `reachContact` (hip-to-ankle
distance at contact over the leg length) and `hipOverAnkle`: under 0.9 the walk reads crouched, over
1 the foot leaves its controller.

Checks measured on 27.0: IK foot error 0 px over 48 frames at root scale 100, 150 and 60 %, and heel
and toe corners never below the ground line. During heel-off and heel strike the corner on the
ground moves at the travel speed (16.67 px per frame) and stays on the ground. Torso keys sit at
frames 2, 8, 14, 20, 26 against hips at 3, 9, 15, 21, 27. Every controller is equal at frames 0, 24
and 48; in place (travel off), frame 0 and frame 24 render identical. Before foot roll the toe went
18.1 px under the ground at frame 12 and slid 9 px during heel-off. Same rig with `loopOut()` only
on the hips: frames 0 to 3 all hold -226, frame 24 reads -240, frames 0 and 24 differ by 31,858
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

## 3b. Walk that stops, a hanging prop, framing

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {"out": "<folder>"}. 1920x1080 shot, figure scaled 1.4 through CTRL_ROOT, two cycles, stop at 48, bag on the back.
AEK.core.fresh();
var c = AEK.build.comp("WALK_STOP", { width: 1920, height: 1080, fps: 24, duration: 5, bg: [0.93, 0.92, 0.88] });
var ch = AEX.rig.character(c, { x: 240, ground: 860, scale: 1.4 });
var w = AEX.rig.walk(c, ch, { cycle: 24, travel: true, stopAt: 48 });
var piv = AEX.rig.world(c, ch.L.torso, [-50, -150], [0])[0];
var bag = AEX.rig.part(c, "BAG", { name: "art", type: "rect", size: [44, 56], roundness: 8, position: [0, 40], fill: [0.9, 0.35, 0.3] }, piv);
bag.parent = ch.L.torso; bag.moveToEnd();
var hang = AEX.rig.hang(bag, { length: 56, pxPerMeter: 406 });
return { walk: w, hang: hang, frame0: AEX.rig.bounds(c, 0), frame100: AEX.rig.bounds(c, 100 / 24), check: AEK.expr.check(c, 10),
    frames: AEK.capture.frames(c, [0, 30 / 24, 48 / 24, 60 / 24, 100 / 24], ARGS.out, "stop") };
```

- **Stop.** `stopAt` is a multiple of the cycle after its first cycle. From that frame each cycled
  property plays its own keys. The right foot plants and the left foot steps beside it in one step
  (lift 0.7). The body slows at a constant rate to 0 over the same step (bezier, influence 33.333 %,
  leaving at the walk speed). The hips rise until the legs reach 97 % of their length
  (`stop.standRise`), and the torso and arms settle by frame stop + 22. Measured: hip speed 16.67 px
  per frame falling linearly to 0 over 12 frames, and hip Y acceleration at the stop no higher than
  inside the cycle (3.81). Planted heels moved 0 px from the stop to the end, both feet end side by
  side.
- **Hanging prop.**
  `AEX.rig.hang(layer, {length, pxPerMeter, damping: 0.3, window: 48, gain: 1, rest: 0})` writes a
  damped pendulum on Rotation, driven by the pivot's horizontal acceleration over the last 48
  frames, minus the parent's world angle. The layer needs a parent and its anchor on the hanging
  point. Parenting wrote the parent's angle into the prop's Rotation (a -5 degree tilt at rest):
  `hang()` resets it. Measured: world angle -14 to 16.9 degrees in the walk, -30.8 to 11.1 on the
  stop, 0 at rest; 137 ms per 120 frames. Damping 0.15 swung ±30 degrees in the walk.
- **Framing.** `AEX.rig.bounds(comp, t)` returns the comp box of every visible shape or footage
  layer (controllers, zero nulls and the ground skipped). The test character is 556 px tall at scale
  1; `scale: 1.4` filled 72.2 to 74.3 % of a 1080 px frame. Scale the figure through `CTRL_ROOT`:
  the IK reads the parent's world scale, and the travel and the ground line follow it.
- Measured on 27.0 with this job: IK error 0 px at scale 1.4, planted heels 0 px in every stance,
  soles never below the ground, 27 expressions with 0 errors. The in-place copy at the same scale
  gave frames 0, 24 and 48 identical (`compare -metric AE` = 0).

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
`loopOut("continue")` read 1299.43 at 3 s instead of 1300: separate the dimensions. A stop is keyed
inside the same rig with `walk({stopAt})` (section 3b); a turn is a separate timeline swapped in
(School of Motion walk).

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

Front view: a limb drawn along +y (hanging) raises out and up with positive Rotation on the
screen-left arm and negative on the screen-right arm, so the side-view keys are mirrored per arm.
The forearm bends the hand toward the body with negative Rotation on the screen-left arm while it
hangs, and toward the head with positive Rotation once the arm is raised. Measured wave on the
screen-left arm, rest at 18 degrees, start frame 20. Upper:
`[[0, 18], [4, 6], [10, 140], [14, 128], [40, 128], [48, 18]]`, the dip to 6 is the anticipation.
Forearm:
`[[0, -14], [10, 40], [15, 10], [20, 45], [25, 10], [30, 45], [35, 10], [40, 35], [48, -14]]`. Hand:
`drag` 2 frames. The elbow stayed 9 to 40 px out on every hold frame. With the forearm signs of the
side view the elbow pointed in. Overlap: the body leans 2 degrees against the anticipation, -5 into
the wave and settles 1.5 past rest; the mouth opens with the raised arm.

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
the acting needs them (before a head turn, on a thought). A keyed blink that reads on a contact
sheet: `AEX.rig.blink(eye.property("ADBE Transform Group").property("ADBE Scale"), comp, [8, 54])`,
hold keys at Scale Y 100, 45, 8, 8, 50, 100 (6 frames). Measured: 12 keys per eye for two blinks;
the half-closed and the shut frames each hold 1 to 2 frames, so a sheet frame inside the blink shows
it.

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
