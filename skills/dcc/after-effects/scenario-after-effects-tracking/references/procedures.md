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
```

Corners are UL, UR, LR, LL on the reference frame. `ref` registers every frame to the reference
(warp back, measure the residual); `chain` is frame to frame; `hybrid` re-anchors every `--anchor`
frames. Measured on a 72-frame shot with blur and noise: `ref` 0.657 px mean, `hybrid` 0.695,
`chain` 1.414 (2.84 at the last frame). Shake: 0.43 px mean, 0.0014 degrees. `shake` rotation is
clockwise-positive, as After Effects Rotation. Check `inliers` per frame: 0 means the pose was held.

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
var l = AEK.core.comp(ARGS.comp).layer(ARGS.layer), fx = l.property("ADBE Effect Parade").property("Corner Pin");
var before = AEX.track.readCorners(l, fx.propertyIndex, ARGS.frames, 0);
AEX.track.reanchor(fx, ARGS.frame, ARGS.fixCorners, ARGS.ramp);
var after = AEX.track.readCorners(l, fx.propertyIndex, ARGS.frames, 0);
return { before: AEX.track.error(before, ARGS.reference), after: AEX.track.error(after, ARGS.reference) };
```

Check: measured 1.414 to 0.909 px mean with a 36-frame ramp at frame 71. `reanchor` fits drift that
grows steadily; a jump needs a split track (two tracks, new reference after the jump).

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
var c = AEK.core.comp(ARGS.comp), n = AEX.track.nullFromCorners(c, ARGS.plane, "screen_track", 0);
var t = AEK.core.layer(c, ARGS.child);
AEK.build.parent(t, n);
return AEK.capture.queue(c, ARGS.out + "/slide.mp4", { template: "H.264 - Match Render Settings - 15 Mbps" });
```

Measure the slide on the render: locate the child per frame (color threshold or
`track_external.py plane` on it) and compare with the tracked feature it should follow. Measured:
1.22 px mean, 1.86 max over 72 frames (a similarity transform on a mildly tilted screen). The same
frame test judges a 3D solve: a proof solid on the ground versus a ground feature.

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
var tr = AEX.track.pointTracker(l, "external", [{ name: "UL", centers: ARGS.points, startFrame: 0 }]);
return { keys: tr.property(1).property("ADBE MTracker Pt Feature Center").numKeys };
```

```javascript
// expression (JavaScript engine): Null > Position
// checked: live 27.0
thisComp.layer("plate").motionTracker("external")("UL").attachPoint
```

Check: measured 72 keys; the expression returned the tracked value at frame 48 exactly. Use it when
another artist expects data in the Tracker panel.

## P12. Mocha AE data (GUI, then audit)

A person or a computer-use agent tracks in Mocha AE (gui-paths.md), then Create Track Data, Export
Option "Corner Pin (Support Motion Blur)", Layer Export To the insert, Apply Export. The agent then
runs P10 and P8. Mocha's clip size, frame rate and pixel aspect must equal the footage, or the
exported data drifts (Boris FX doc, Export to After Effects). Mocha's Corner Pin values are written
in the target layer's own pixels, so the insert must be a precomp at the tracked footage size with
the art Fit to Comp inside (Ben Brownlee, 1tWKdbjKLNE 00:04:05). UHD footage scaled to 50 % in an HD
comp: make the precomp UHD and set the insert layer's scale to 50 % as well; the Support Motion Blur
export adds scale keys and breaks that case (1tWKdbjKLNE 00:05:13 to 00:06:18). To keep the true
screen aspect, pin a comp-size solid, then nest a precomp at the real screen size inside it (Javier
Mercedes, UkC9qKS7c0Y 00:12:48).

## P13. Sharpened tracking reference for the 3D Camera Tracker, then swap back

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
