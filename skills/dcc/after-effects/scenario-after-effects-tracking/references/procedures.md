# Tracking procedures (agent)

Every job is a function body for
`ae.py run job.jsx --lib <skill>/scripts/track.jsx --args '<json>'`. Paths come from `ARGS` and are
absolute. In a person's session, drop `AEK.core.fresh()`, take `AEK.session.state()` first, run with
`--undo "Agent: <what>"`, and `restore()` last (lead skill).

## What a script can and cannot do (measured on 27.0)

| Task                                                                           | Script | How                                                                                                                 |
| ------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------- |
| Add Warp Stabilizer, 3D Camera Tracker, Corner Pin, CC Power Pin, Mocha AE     | yes    | `addProperty("ADBE SubspaceStabilizer")`, `"ADBE 3D Tracker"`, `"ADBE Corner Pin"`, `"CC Power Pin"`, `"mochaAECC"` |
| Set Warp and tracker settings                                                  | yes    | by match name (table below)                                                                                         |
| Start, wait for or read the analysis                                           | no     | analysis runs only while the app is idle; poll rendered frames for the banner                                       |
| Read Average Error, Auto-scale percent, Method Used                            | no     | names stay "Average Error: -", "Auto-scale" after a finished analysis                                               |
| Select track points, Set Ground Plane and Origin, Create Camera, delete points | no     | GUI (gui-paths.md)                                                                                                  |
| Create a Motion Tracker and track points, write their keys                     | yes    | `ADBE MTrackers` > `ADBE MTracker` > `ADBE MTracker Pt`                                                             |
| Run Analyze Forward in the Tracker panel                                       | no     | no menu label; track outside After Effects                                                                          |
| Mocha AE track, Surface, Create Track Data, paste                              | no     | GUI; audit the pasted keys by script (P10)                                                                          |

### Match names

| Effect                                    | Property (match name)                                                                                                                   | Default and range                   |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| Warp Stabilizer `ADBE SubspaceStabilizer` | Result `-0019`, Smoothness `-0020`, Method `-0028`, Preserve Scale `-0044`                                                              | 1 (1-2), 50 (0-1000), 4 (1-4), 0    |
|                                           | Framing `-0022`, Maximum Scale `-0004`, Action-safe Margin `-0003`, Additional Scale `-0016`                                            | 3 (1-4), 150, 0, 100                |
|                                           | Detailed Analysis `-0036`, Fast Analysis `-0308`, Rolling Shutter Ripple `-0037`, Crop Less <-> Smooth More `-0023`                     | 0, 1, 1 (1-2), 50                   |
|                                           | Synthesis Input Range `-0038`, Synthesis Edge Feather `-0035`, crop Left/Top/Right/Bottom `-0031`..`-0034`                              | 0.5 s, 10, 0                        |
|                                           | Objective `-0047`, Target Layer `-0046`, Show Track Points `-0280`, Hide Warning Banner `-0026`                                         | 1 (1-6), layer index 0, 0, 0        |
| 3D Camera Tracker `ADBE 3D Tracker`       | Shot Type `-0403`, Horizontal Angle of View `-0414`, Show Track Points `-0405`, Render Track Points `-0406`                             | 1 (1-4), 0 (0-180), 2 (1-2), 0      |
|                                           | Track Point Size `-0407`, Target Size `-0409`, Solve Method `-0410`, Detailed Analysis `-0036`                                          | 100, 100, 1 (1-5), 0                |
|                                           | Auto-delete Points Across Time `-0306`, Hide Warning Banner `-0026`                                                                     | 1, 0                                |
| Corner Pin `ADBE Corner Pin`              | Upper Left `-0001`, Upper Right `-0002`, Lower Left `-0003`, Lower Right `-0004`                                                        | layer corners                       |
| Track point `ADBE MTracker Pt`            | `... Feature Center`, `... Feature Size`, `... Search Ofst`, `... Search Size`, `... Confidence`, `... Attach Pt`, `... Attach Pt Ofst` | [0,0], [20,20], [0,0], [40,40], 100 |

Feature Size, Search Offset and Search Size cannot vary over time (`canVaryOverTime` false). Other
effects: Rolling Shutter Repair `ADBE Rolling Shutter`, Camera-Shake Deblur
`ADBE CameraShakeDeblur`, Gaussian Blur `ADBE Gaussian Blur 2` (Blurriness `-0001`, Repeat Edge
Pixels `-0003`), Noise `ADBE Noise` (Amount `-0001`, Clipping `-0003`). `ADBE Fast Box Blur` is not
a valid match name here.

## P1. Dump an effect's properties

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), l = c.layer(ARGS.layer), rows, i, e;
e = l.property("ADBE Effect Parade").addProperty(ARGS.matchName);
rows = AEK.build.effectProps(l, e.propertyIndex);
for (i = 0; i < rows.length; i++) {
    var p = l.property("ADBE Effect Parade").property(e.propertyIndex).property(i + 1);
    try { if (p.propertyValueType === PropertyValueType.OneD) { rows[i].min = p.minValue; rows[i].max = p.maxValue; } } catch (er) { rows[i].rangeError = String(er); }
}
return rows;
```

Check: unnamed `NO_VALUE` rows are buttons and group ends; they cannot be pressed. A row whose
`value` is null has no readable value (Gradient Ramp `ADBE Ramp-0008`, unnamed, measured on 27.0).
Measured names for the tracking reference (P13): Levels `ADBE Easy Levels2` Input Black `-0003`,
Input White `-0004` (0 to 1 at 8 bpc), Gamma `-0005`; Unsharp Mask `ADBE Unsharp Mask2` Amount
`-0001`, Radius `-0002`, Threshold `-0003`.

## P2. Background analysis (Warp Stabilizer or 3D Camera Tracker)

Measured on 27.0: the analysis does not advance while any job runs, during `$.sleep`, or during
render-queue renders. It completed in under 23 s while the app idled between short jobs. Changing
Smoothness or Method later needs another idle pass (orange "Stabilizing" band); Framing changes
apply at once. The analysis is saved in the project and survives a reopen.

Warp Stabilizer judgment:

- A banner "To avoid extreme cropping..." means Smoothness is above what the framing allows: lower
  it, or diagnose with Stabilize Only (Jake Bartlett, 28L2XalNr5A 00:02:24).
- Stabilize, Synthesize Edges avoids the zoom but can tear at the first frames and fast moves
  (28L2XalNr5A 00:05:40, 00:04:01).
- Stabilizing never removes baked-in blur: add Camera-Shake Deblur (`ADBE CameraShakeDeblur`) below
  Warp Stabilizer, never on the unstabilized plate (28L2XalNr5A 00:01:36, 00:19:38).

Job A adds the effect and returns at once. The app must then stay idle with the project open.

```javascript
// channel: bridge
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), l = c.layer(ARGS.layer);
var fx = AEK.build.effect(l, "ADBE SubspaceStabilizer", {
    "ADBE SubspaceStabilizer-0020": ARGS.smoothness,   // set everything that needs analysis BEFORE returning
    "ADBE SubspaceStabilizer-0028": ARGS.method,
    "ADBE SubspaceStabilizer-0036": ARGS.detailed ? 1 : 0
}, "Warp Stabilizer");
return { effect: fx.name, layer: l.name };
```

Job B, sent every few seconds, captures one frame and nothing else:

```javascript
// channel: bridge
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
return AEK.capture.frame(c, ARGS.seconds, ARGS.png);
```

```bash
python3 <skill>/scripts/track_external.py banner <out>/poll.png   # "analyzing" | "stabilizing" | "none"
```

Check: render only after `none`. Measured: blue band (blue minus red about 179) while analyzing,
orange (about -137) after a Smoothness or Method change, no band after Framing changes. A 72-frame
720p shot finished in under 23 s of idle gaps. Any job, `$.sleep` or render-queue render inside a
job, and `aerender`, do not advance it. The banner check was measured on 1280x720 frames.

## P3. Measure a stabilization from the render

```bash
python3 ae.py render "<comp>" --out <out>/stab.mp4 --template "H.264 - Match Render Settings - 15 Mbps"
python3 <skill>/scripts/track_external.py shake <out>/stab.mp4 --out <out>/stab_motion.json
python3 - <<'EOF'
import json, numpy as np
w = np.array(json.load(open("<out>/stab_motion.json"))["shake"])
d = np.diff(w[:, :2], 2, axis=0)
print("range px", np.ptp(w[:, 0]), np.ptp(w[:, 1]), "jitter", np.sqrt((d ** 2).sum(1).mean()))
EOF
```

Check: jitter (second difference RMS) under 0.2 px. Measured: source 8.17, Warp Stabilizer defaults
0.03, key smoothing 25 frames 0.15. The scale-up is the similarity scale between a source frame and
the render (ORB matches plus `estimateAffinePartial2D`): Warp auto-scale measured 105.9 %.

## P4. Track outside After Effects

```bash
python3 <skill>/scripts/track_external.py plane <shot.mp4> --corners "x,y x,y x,y x,y" --ref 0 --mode ref --out plane.json
python3 <skill>/scripts/track_external.py shake <shot.mp4> --ref 0 --out shake.json
python3 <skill>/scripts/track_external.py score plane.json truth.json     # when a known path exists
python3 <skill>/scripts/track_external.py point plane.json --point 812,431 --out button.json   # carry a point
python3 <skill>/scripts/track_external.py slide <shot.mp4> --track plane.json --point 812,431  # independent slide check
```

Pick the reference corners on a flat rigid part of the subject: the four corners of a button panel,
a label, a screen bezel. Each corner sits on a high-contrast point (a panel corner, a printed mark),
never on fabric, a reflection or an edge that turns away from camera.

`slide` warps each frame back to the reference with the track's own map, then re-finds a 240 px
patch around the point within a 128 px search (template match). It counts frames over 3 px and
reports `jumps`: runs of 3 or more frames over 3 px, the sign of a track that moved to another
feature. A repeated feature (a row of identical buttons) can give a single false spike at a small
patch: keep the 240 px default. Measured on a 150-frame plate of a speaker turning in depth.
`shake --corners` on the button panel: 71.4 px mean, 144.9 max, one jump from frame 11 to the end
(79 px at frame 60). `plane --mode ref` on the same panel: 0.89 mean, 4.24 max, no jumps. Gate: mean
under 1.5 px and `jumps` empty. Corners are UL, UR, LR, LL on the reference frame.
`shake --corners "<quad>"` keeps only features inside that quad: the motion of one object about the
frame center, for object stabilization (P15). A curved surface that turns (bottle, cylinder speaker)
is not a plane. On a real 121-frame plate, the `plane` quad on a speaker's fabric skewed into a
trapezoid (corners 94 px apart in x on one side). Track a flat rigid part of the object instead; use
`shake --corners` only when it has none, and run `slide` on the result. `ref` registers every frame
to the reference (warp back, measure the residual); `chain` is frame to frame; `hybrid` re-anchors
every `--anchor` frames. Measured on a 72-frame shot with blur and noise: `ref` 0.657 px mean,
`hybrid` 0.695, `chain` 1.414 (2.84 at the last frame). Shake: 0.43 px mean, 0.0014 degrees. `shake`
rotation is clockwise-positive, as After Effects Rotation. Check `inliers` per frame: 0 on any frame
but the reference means the pose was held; the reference frame always reads 0 in `plane`.

## P5. Screen insert with Corner Pin

Corners from `track_external.py` are in footage pixels. The plate sits unscaled in a comp at footage
size; `cornerPin` sets the insert's anchor, position and scale so layer pixels equal comp pixels,
then maps the insert's full frame onto the four corners. The insert's own pixel size is free: a
520x960 insert held on a 1280x720 plate (measured). Give it the screen's real aspect so the art is
not stretched.

```javascript
// channel: bridge
// checked: live 27.0
// --lib track.jsx; ARGS: comp, insert (item name), plane (corners per frame), startFrame
var c = AEK.core.comp(ARGS.comp), it = AEK.core.item(ARGS.insert);
var l = c.layers.add(it); l.name = "insert_pinned";
var fx = AEX.track.cornerPin(l, ARGS.plane, { motionBlur: true, startFrame: ARGS.startFrame });
var back = AEX.track.readCorners(l, fx.propertyIndex, ARGS.plane.length, ARGS.startFrame);
return { keys: fx.property(1).numKeys, roundTrip: AEX.track.error(back, ARGS.plane), motionBlur: l.motionBlur && c.motionBlur };
```

Check: `roundTrip.maxPx` under 0.01 (data written as tracked); keys equal frames. Measured: a plain
Corner Pin with the layer and comp motion blur switches on rendered identical pixels to blur off
(mean difference 0.0); the split version differed by 1.56 levels on average, the blur.

## P6. Drift fix at a frame

```javascript
// channel: bridge
// checked: live 27.0
// ARGS.fixCorners: UL, UR, LR, LL at ARGS.frame from a re-registration of that one frame
// the effect by match name: its display name changes with the install language
var l = AEK.core.layer(AEK.core.comp(ARGS.comp), ARGS.layer), fx = AEX.track.effect(l, "ADBE Corner Pin");
var before = AEX.track.readCorners(l, fx.propertyIndex, ARGS.frames, 0);
AEX.track.reanchor(fx, ARGS.frame, ARGS.fixCorners, ARGS.ramp);
var after = AEX.track.readCorners(l, fx.propertyIndex, ARGS.frames, 0);
return { before: AEX.track.error(before, ARGS.reference), after: AEX.track.error(after, ARGS.reference) };
```

Check: measured 1.414 to 0.909 px mean with a 36-frame ramp at frame 71. On a real 121-frame plate
with a linear drift of up to 6.7 px, a 60-frame ramp at the last frame gave 3.35 to 1.66 px mean:
the ramp covers only the frames it spans, so set it to the length of the drift. `reanchor` fits
drift that grows steadily; a jump needs a split track (two tracks, new reference after the jump).

## P7. Stabilize by keys

```javascript
// channel: bridge
// checked: live 27.0
// ARGS.shake from track_external.py shake; smooth 0 = locked, 25 = keep the move
var l = AEK.core.comp(ARGS.comp).layer(ARGS.layer);
return AEX.track.stabilize(l, ARGS.shake, { smooth: ARGS.smooth, autoScale: true, margin: 0 });
```

Check: `scaleNeeded` against the delivery limit. Measured: locked 118.65 % (residual 0.03 px),
25-frame two-pass smoothing 105.37 % (residual 0.15 px), one-pass 9 frames 103.54 % with 0.99 px
jitter left. A locked result inherits the reference frame's tilt: pick a level reference frame. Keys
go on Position and Rotation with the anchor at the layer center; a layer that already has keys there
needs a precomp first.

## P8. Integration stack for a screen insert

```javascript
// channel: bridge
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), it = AEK.core.item(ARGS.insert), l = c.layers.add(it);
l.name = "insert_pinned";
AEX.track.cornerPin(l, ARGS.plane, { motionBlur: true });
AEK.build.effect(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 0.8, "ADBE Gaussian Blur 2-0003": 0 }, "edge soften");
AEK.build.effect(l, "ADBE Noise", { "ADBE Noise-0001": ARGS.grain }, "grain");
var v = c.layers.addSolid([1, 1, 1], "glass veil", it.width, it.height, 1, c.duration);
AEX.track.cornerPin(v, ARGS.plane, { motionBlur: true });
v.blendingMode = BlendingMode.SCREEN;
v.property("ADBE Transform Group").property("ADBE Opacity").setValue(ARGS.veil);
return { bpc: app.project.bitsPerChannel, linearBlending: app.project.linearBlending };
```

Check: insert black level and grain against the plate. Measured at 8 bpc, linear blending off: navy
(70, 40, 25) became (85, 57, 43) with an 8 % veil, exactly the Screen formula; Noise 2.5 % gave a
high-pass deviation of 1.66 against 1.98 in the plate's flat screen. Read `bpc` and `linearBlending`
with every level measurement: a run in an inherited project state gave (102, 88, 83).
`AEK.core.fresh()` now resets the color engine, linear blending and gamma for test jobs; a person's
open project keeps its own settings, so record them there too.

## P9. Null from a track and a slide test

```javascript
// channel: bridge
// checked: live 27.0
// ARGS.point: the attach point on the reference frame, in footage pixels
var c = AEK.core.comp(ARGS.comp), n = AEX.track.nullFromCorners(c, ARGS.plane, "button_track", 0, { point: ARGS.point });
var t = AEK.core.layer(c, ARGS.child);   // a pure-color proof marker centered on its anchor
AEK.build.parent(t, n); t.property("ADBE Transform Group").property("ADBE Position").setValue([0, 0, 0]);
return AEK.capture.queue(c, ARGS.out + "/proof.mp4", { template: "H.264 - Match Render Settings - 15 Mbps" });
```

The null sits on `point` carried through each frame's homography; Rotation and Scale come from the
homography's local derivative at that point. Measure the proof render:

```bash
python3 <skill>/scripts/track_external.py point plane.json --point 812,431 --out path.json
python3 <skill>/scripts/track_external.py locate proof.mp4 --path path.json --color 0,255,0 --tol 45
```

Measured on a speaker turning in depth (120 frames, 1920x1080): 0.74 px mean, 1.03 max. The former
null (corner centroid, top-edge angle and length) with a child on the button gave 10.0 mean, 19.9
max: a similarity is wrong under perspective, and the error grows with the distance from the
centroid. On a mildly tilted screen with the child at the center, the similarity gave 1.22 mean,
1.86 max over 72 frames. Under perspective, give every element its own point instead of parenting it
away from one null. Keep `--tol` low enough that the marker color is not found in the plate. The
same frame test judges a 3D solve: a proof solid on the ground versus a ground feature.

## P10. Audit pinned inserts and trackers (after a Mocha paste or a script)

```javascript
// channel: bridge | handoff
// checked: live 27.0
var comp = AEK.core.comp(ARGS.comp), rows = [], i, j, k, l, e, keys, span, pk, mt;
for (i = 1; i <= comp.numLayers; i++) {
    l = comp.layer(i);
    if (!(l instanceof AVLayer)) { continue; }
    span = Math.round((Math.min(l.outPoint, comp.duration) - Math.max(l.inPoint, 0)) * comp.frameRate);
    for (j = 1; j <= l.property("ADBE Effect Parade").numProperties; j++) {
        e = l.property("ADBE Effect Parade").property(j);
        if (e.matchName !== "ADBE Corner Pin" && e.matchName !== "CC Power Pin") { continue; }
        keys = []; for (k = 1; k <= 4; k++) { keys.push(e.property(k).numKeys); }
        pk = l.property("ADBE Transform Group").property("ADBE Position").numKeys;
        rows.push({ layer: l.name, keys: keys, framesInSpan: span, everyFrame: keys[0] >= span,
            blurReady: l.motionBlur && comp.motionBlur && pk > 1, switchOnly: l.motionBlur && pk <= 1 });
    }
    mt = l.property("ADBE MTrackers");
    if (mt && mt.numProperties) { rows.push({ layer: l.name, motionTrackers: mt.numProperties }); }
}
return rows;
```

Check: `everyFrame` true, `switchOnly` false on moving inserts. Measured: it flagged a pin keyed on
60 of 72 frames and a switch-only blur.

## P11. Store a track in a Motion Tracker

```javascript
// channel: bridge
// checked: live 27.0
var l = AEK.core.comp(ARGS.comp).layer(ARGS.layer);
// ARGS.plane: corners per frame; ARGS.point: the attach point on the reference frame
var pts = AEX.track.pointsFromCorners(ARGS.plane, ARGS.point);
var tr = AEX.track.pointTracker(l, "external", [{ name: "UL", centers: pts, startFrame: 0 }]);
return { keys: tr.property(1).property("ADBE MTracker Pt Feature Center").numKeys };
```

```javascript
// expression (JavaScript engine): Null > Position
// checked: live 27.0
thisComp.layer("plate").motionTracker("external")("UL").attachPoint
```

Check: measured 72 keys; the expression returned the tracked value at frame 48 exactly. Use it when
another artist expects data in the Tracker panel. `pointsFromCorners` is the same homography as
`track_external.py point` (they agree within 0.001 px); measured on the speaker shot through the
Motion Tracker: 0.80 px mean, 1.29 max on the proof render.

**Tracked callout.** Only the dot rides the track: Position from the `attachPoint` expression. The
label stays still where the plate behind it is clean, joined by a leader whose path expression reads
the tracked point: `createPath([[p[0], p[1]], [ex, ey], [lx, ly]], [], [], false)`, with `p` the
dot's Position. Write constant arrays into the expression element by element: an array concatenated
whole into the string threw "invalid numeric result" on 27.0. Gate the label with
scenario-after-effects-typography procedure 10 (`AEX.type.readability`). Cap height is at least 3.5
% of the short side; contrast is at least 4.5:1 against the plate sampled behind the text. Then
check on every frame that the label box covers no bright or busy plate detail.

## P12. Mocha AE data (GUI, then audit)

What `plane` cannot do: it samples every feature inside the quad and has no exclusion hole.
Reflections crossing the glass, fingers, or screen content that changes need Mocha AE: an Add-spline
hole over the reflections, a layer above for fingers, the stable bezel tracked, then the Surface
moved to the screen corners (TF3XVBy6sD4 00:04:33; UkC9qKS7c0Y 00:04:42).

A person or a computer-use agent tracks in Mocha AE (gui-paths.md), then Create Track Data, Export
Option "Corner Pin (Support Motion Blur)", Layer Export To the insert, Apply Export. The agent then
runs P10 and P8. Mocha's clip size, frame rate and pixel aspect must equal the footage, or the
exported data drifts (Mocha AE doc, Export to After Effects). Mocha's Corner Pin values are written
in the target layer's own pixels, so the insert must be a precomp at the tracked footage size with
the art Fit to Comp inside (Ben Brownlee, 1tWKdbjKLNE 00:04:05). UHD footage scaled to 50 % in an HD
comp: make the precomp UHD and set the insert layer's scale to 50 % as well; the Support Motion Blur
export adds scale keys and breaks that case (1tWKdbjKLNE 00:05:13 to 00:06:18). To keep the true
screen aspect, pin a comp-size solid, then nest a precomp at the real screen size inside it (Javier
Mercedes, UkC9qKS7c0Y 00:12:48).

## P13. Sharpened tracking reference for the 3D Camera Tracker, then swap back

Camera solve rules (stage 8):

- Track a sharpened copy: Levels and Unsharp Mask (Amount 100, Radius 2) in a precomp, the tracker
  on it, the original swapped back after Create Camera (wiISCTB4s1Y 00:01:04, 00:06:55).
- In the GUI, set Ground Plane and Origin before creating anything. Create Shadow Catcher, Camera
  and Light gives a contact shadow (m2bF4U6EBZU frame 00:06:00).
- A solved scene that looks huge needs the free Normalize Track script (wiISCTB4s1Y 00:04:08;
  m2bF4U6EBZU 00:06:44).
- Move a placed title's anchor to its base before making it 3D (`AEK.build.anchor(layer, 0.5, 1)`),
  so scale grows from the ground (wiISCTB4s1Y 00:05:18).
- A failed solve can come out better on a second run: retrack before deeper surgery (m2bF4U6EBZU
  00:02:25).

Log or soft footage gives the solver little contrast. Track a graded, sharpened copy; it is never
rendered (Guerrilla Filmmaking, wiISCTB4s1Y 00:01:04, 00:06:55). Set Input Black and White to where
the histogram starts and ends (0 to 1 at 8 bpc).

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), plate = AEK.core.layer(c, ARGS.layer), ref = plate.duplicate();
ref.name = "track_ref";
AEK.build.effect(ref, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": ARGS.black, "ADBE Easy Levels2-0004": ARGS.white }, "track levels");
AEK.build.effect(ref, "ADBE Unsharp Mask2", { "ADBE Unsharp Mask2-0001": 100, "ADBE Unsharp Mask2-0002": 2 }, "track sharpen");
AEK.build.precompose(c, [ref.index], "track_ref", true);   // layer references taken before are invalid after this
var refL = AEK.core.layer(c, "track_ref");
AEK.core.layer(c, ARGS.layer).enabled = false;
refL.property("ADBE Effect Parade").addProperty("ADBE 3D Tracker");
return { ref: refL.name, effects: refL.source.layer(1).property("ADBE Effect Parade").numProperties };
```

Then return control (P2), and in the GUI set the ground plane and create the camera. Swap back by
script once the camera exists:

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
AEK.core.layer(c, "track_ref").enabled = false;
AEK.core.layer(c, ARGS.layer).enabled = true;
var t = AEK.core.layer(c, ARGS.title);   // a 2D title placed on the solve: anchor to its base before it becomes 3D
var a = AEK.build.anchor(t, 0.5, 1, 0);
t.threeDLayer = true;
return { anchor: t.property("ADBE Transform Group").property("ADBE Anchor Point").value, bounds: a.bounds };
```

Check: the reference precomp holds 2 effects, the original is enabled and the reference disabled
after the swap; the title's anchor Y equals the bottom of its bounds (measured: bounds top -86,
height 86, anchor Y 0, the baseline of a caps title). A huge solved scene: run the free Normalize
Track script on the camera and solids after the ground plane is set; it needs a solid named
"ground", "floor" or "wall" (wiISCTB4s1Y 00:04:08, 00:04:41).

## P14. Corner Pin from four nulls

Four tracked points, four nulls from a tracker, or a Mocha export to nulls: `cornerNulls` writes one
null per corner (`<prefix>UL`, `UR`, `LR`, `LL`, anchor [0, 0], keyed on every frame);
`pinFromNulls` puts a Corner Pin whose four expressions read each null with `toComp` and convert to
the pinned layer with `fromComp`. The pinned layer may be scaled or moved; the pin follows any later
edit of the nulls.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// --lib track.jsx; ARGS: comp, insert (layer name), plane (corners per frame, UL UR LR LL), startFrame
var c = AEK.core.comp(ARGS.comp), l = AEK.core.layer(c, ARGS.insert);
var names = AEX.track.cornerNulls(c, ARGS.plane, "trk_", ARGS.startFrame || 0);
var pin = AEX.track.pinFromNulls(l, names), err = "", k;
for (k = 1; k <= 4; k++) { if (pin.property(k).expressionError) { err += pin.property(k).expressionError; } }
return { nulls: names, expressionError: err };
```

```javascript
// expression (JavaScript engine): Corner Pin > Upper Left (pinFromNulls writes one per corner)
// checked: live 27.0
var n = thisComp.layer("trk_UL");
fromComp(n.toComp(n.anchorPoint));
```

Check: `expressionError` empty; each pinned corner read back in comp space equals its null. Measured
on a 121-frame plate with the insert scaled 50 % and moved: 0.000 px maximum. An expression pin has
no Position motion, so the layer motion blur switch does not blur it: for a moving insert use
`cornerPin(..., {motionBlur: true})` with the same corners, or bake the expressions
(`AEK.expr.bake`).

## P15. Object stabilization and a stabilized insert

Track the object, lock it, place the insert on the still frame, then give the motion back. The
insert then rides on the object and the plate pixels return unchanged.

```bash
python3 <skill>/scripts/track_external.py shake <shot.mp4> --corners "x,y x,y x,y x,y" --ref 0 --out object.json
```

```javascript
// channel: bridge
// checked: live 27.0
// --lib track.jsx; ARGS: plate (abs path), shake (object.json "shake" array), insertPos [x, y] on the reference frame
var it = AEK.xio.importItem(ARGS.plate, {}), n = ARGS.shake.length, fps = it.frameRate, D = n / fps;
var st = AEK.build.comp("STAB_plate_v001", { width: it.width, height: it.height, fps: fps, duration: D });
var pl = st.layers.add(it); pl.name = "plate";
var s = AEX.track.stabilize(pl, ARGS.shake, { smooth: 0, autoScale: false });
var badge = AEK.build.shape(st, "INSERT_v001", { name: "b", type: "rect", size: [96, 40], fill: [0.97, 0.93, 0.85] }, { position: ARGS.insertPos });
var m = AEK.build.comp("MAIN_insert_v001", { width: it.width, height: it.height, fps: fps, duration: D });
var sl = m.layers.add(st);
var r = AEX.track.restoreMotion(sl, ARGS.shake, {});   // also switches Collapse Transformations on
sl.motionBlur = true; m.motionBlur = true;
return { stabilize: s, restore: r };
```

Check: re-track the stabilized precomp's render with `shake --corners` on the same quad; render the
main comp and count black pixels (0). Measured on a generated hand-held plate (960x544, 121 frames,
the object moving 98 px): stabilized residual 1.55 px maximum and 0.74 px second-difference jitter
(a turning cylinder keeps some), black pixels 0 with Collapse Transformations and 95,000 without,
the plate after the round trip within 0.74 levels of the source, the insert within 1.15 px mean
(2.32 max) of the tracked path. The 0.2 px jitter gate of stage 6 is for camera shake on a static
scene; an object that turns in depth stays above it.
