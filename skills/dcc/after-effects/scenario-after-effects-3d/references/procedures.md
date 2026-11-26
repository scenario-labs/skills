# Procedures: 3D in After Effects by script

Every job is the body of a function run with `ae.py run job.jsx` (bridge) or written for a person
with `--channel handoff`. Jobs that call `AEX.threeD` need `--lib <skill>/scripts/threed.jsx`. Paths
come from `ARGS`. Test jobs start with `AEK.core.fresh()`; in a user's session, work in the open
project inside one undo step (`--undo NAME`).

## Contents

1. Read the renderer and what it exposes
2. Product shot on Advanced 3D
3. Orbit rig without the helper
4. Depth of field that follows the subject (expression)
5. Motion blur for a model (precomp and CC Force Motion Blur)
6. Lights by type
7. Render, judge, deliver
8. 2.5D from cut-out layers
9. 2.5D from a depth map
10. What cannot be scripted
11. Environment light that travels and takes the plate's tint
12. Product on a floor: flat floor, contact shadow, reflection
13. A generated model that reads as soft plastic
14. 2.5D: keep the foreground in frame, sway a plane
15. Layout before the camera move, and a move that reads
16. Version notes
17. A model seated in a still plate (low sun, push-in)

## 1. Read the renderer and what it exposes

Use before any 3D change in someone's project: the internal names are misleading on 27.0 and hidden
properties throw on `setValue`.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), out = { renderer: AEX.threeD.rendererName(c), raw: c.renderer, list: c.renderers, models: 0, lights: [] }, i, l;
for (i = 1; i <= c.numLayers; i++) {
    l = c.layer(i);
    if (l.matchName === "ADBE 3D Model Layer") { out.models++; }
    if (l instanceof LightLayer) { out.lights.push({ name: l.name, type: AEK.core.enumName(LightType, l.lightType), source: l.lightType === LightType.ENVIRONMENT && l.lightSource ? l.lightSource.name : null }); }
}
out.risk = out.renderer === "classic" && out.models > 0 ? "models in a Classic 3D comp: set ADBE Calder before any render" : "";
return out;
```

Check: `renderer` reads `advanced` for any comp with a model, extruded text or Substance material.
`ADBE Advanced 3d` is Classic 3D, `ADBE Calder` Advanced 3D, `ADBE Ernst` Cinema 4D (measured by
what each accepts: extrusion, Shadow Color, Light Transmission, the layer motion blur switch).
`AEX.threeD.settable(group)` lists every property of a group with `exposed` true or false for the
current renderer.

## 2. Product shot on Advanced 3D

Plate, fitted model, EXR environment light, spot shadow on a tinted catcher, extruded text behind,
null orbit with push, focus on the product, motion blur through an outer comp. Measured: warm-up 2.9
s, then about 255 ms per 960x540 frame; the outer comp frame 968 ms; aerender of 72 frames 99 s wall
clock, identical to GUI frames.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {model, hdri, plate, out, width, height, fps, seconds, title}
var A = ARGS, W = A.width || 960, H = A.height || 540, X = W / 2, FLOOR = H * 0.74;
AEK.xio.importMany([{ path: A.model }, { path: A.hdri }, { path: A.plate }]);
var name = function (p) { return p.replace(/^.*[\/\\]/, ""); };
var c = AEK.build.comp("product_3d", { width: W, height: H, fps: A.fps || 24, duration: A.seconds || 3, bg: [0, 0, 0] });
AEX.threeD.use(c, "advanced");                       // BEFORE the model and the light source
var plate = c.layers.add(AEK.core.item(name(A.plate))); plate.name = "plate";
var m = c.layers.add(AEK.core.item(name(A.model))); m.name = "product";
var fit = AEX.threeD.fitModel(m, c, { height: H * 0.4, x: X, floorY: FLOOR, rotateY: -20 });
var floor = AEX.threeD.shadowCatcher(c, FLOOR, { x: X, shadowColor: [0.18, 0.12, 0.08, 1] });
floor.moveBefore(plate);
var t = AEK.text.add(c, A.title || "AIR", { size: H * 0.4, fill: [0.95, 0.45, 0.2], justify: "center", name: "title" });
t.threeDLayer = true;
var r = t.sourceRectAtTime(0, false), tg = t.property("ADBE Transform Group");
tg.property("ADBE Anchor Point").setValue([r.left + r.width / 2, r.top + r.height, 0]);
tg.property("ADBE Position").setValue([X, FLOOR, 400]);
t.property("ADBE Extrsn Options Group").property("ADBE Extrsn Depth").setValue(40);
t.property("ADBE Extrsn Options Group").property("ADBE Bevel Styles").setValue(2);
AEX.threeD.envLight(c, { intensity: 80, source: AEK.core.item(name(A.hdri)) });
AEX.threeD.keyLight(c, [X - 500, FLOOR - 900, -300], [X, FLOOR - 100, 0], { intensity: 70, darkness: 60, diffusion: 15 });
var rig = AEX.threeD.orbitRig(c, [X, FLOOR - H * 0.2, 0], { focalLength: 50, distance: 1100, height: 150, tilt: -8, from: -35, to: 35, push: 250, influence: 50 });
var focus = AEX.threeD.focusOn(rig.camera, "product", { aperture: 60, areaWidth: 150 });
var fin = AEK.build.comp("product_final", { width: W, height: H, fps: A.fps || 24, duration: A.seconds || 3 });
var pl = fin.layers.add(c);
AEK.build.effect(pl, "CC Force Motion Blur", { "CC Force Motion Blur-0001": 8 });
pl.property("ADBE Effect Parade").property(1).enabled = false;   // on only for the final render
AEX.threeD.warmUp(c, A.out + "/warmup.png");
var frames = AEK.capture.frames(c, [0, c.duration / 2, c.duration - 0.1], A.out, "product");
return { fit: fit, focusAtStart: focus.value, frames: frames.length, renderer: AEX.threeD.rendererName(c) };
```

Check: `renderer` is `advanced`; fit height is 40 % of the frame; `focusAtStart` is a distance near
the camera distance (1110 px in the test). On the sheet: product sharp and standing on its shadow,
title soft behind it, shadow on the plate on the light side. Switch the CC Force Motion Blur effect
on before the final render.

## 3. Orbit rig without the helper

The same rig written out, for a person reading the job or a project that cannot load the helper.
One-node camera (`NO_AUTO_ORIENT`), parented to a 3D null at the subject. The null carries the orbit
and the aim; the camera keys only its own Z (the push). Its X, Y and Point of Interest stay unkeyed
(Abrams M7v547PJ5Hk 00:10:15, 00:12:56).

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), subject = AEK.core.layer(c, ARGS.subject);
var rig = AEK.build.nullLayer(c, "cam rig"); rig.threeDLayer = true;
rig.property("ADBE Transform Group").property("ADBE Position").setValue(subject.property("ADBE Transform Group").property("ADBE Position").value);
var cam = c.layers.addCamera("cam", [c.width / 2, c.height / 2]);
cam.autoOrient = AutoOrientType.NO_AUTO_ORIENT;                 // one-node: Point of Interest is hidden from here on
cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(c.width * (ARGS.focalLength || 50) / 36);
cam.parent = rig;
var ct = cam.property("ADBE Transform Group"), rt = rig.property("ADBE Transform Group"), d = ARGS.distance || 1100, h = ARGS.height === undefined ? 150 : ARGS.height, k;
ct.property("ADBE Rotate X").setValue(-8);
AEK.motion.key(ct.property("ADBE Position"), 0, [0, -h, -d]);                       // only Z changes on the camera
AEK.motion.key(ct.property("ADBE Position"), c.duration, [0, -h, -d + (ARGS.push === undefined ? 250 : ARGS.push)]);
AEK.motion.key(rt.property("ADBE Rotate Y"), 0, ARGS.from === undefined ? -35 : ARGS.from);
AEK.motion.key(rt.property("ADBE Rotate Y"), c.duration, ARGS.to === undefined ? 35 : ARGS.to);
for (k = 1; k <= 2; k++) { AEK.motion.ease(ct.property("ADBE Position"), k, 33, 33); AEK.motion.ease(rt.property("ADBE Rotate Y"), k, 33, 33); }
return { orbit: AEK.motion.keys(rt.property("ADBE Rotate Y"), c), camStart: ct.property("ADBE Position").keyValue(1), camEnd: ct.property("ADBE Position").keyValue(2), parent: cam.parent.name };
```

Check: both orbit keys `BEZIER` with influence 33; `camStart` and `camEnd` differ only in Z ([0,
-150, -1100] to [0, -150, -850] in the test); the parent is `cam rig`. For a long hold at the end,
add a third key and ease it at 80 % in (the scenario-after-effects-animation skill has the curves).

## 4. Depth of field that follows the subject

On the camera's Focus Distance. `t.sourceRectAtTime` works on a model layer inside an expression;
the point aimed at is the middle of the footprint, in the model's layer space.

```javascript
// expression (JavaScript engine): Camera > Camera Options > Focus Distance
// checked: live 27.0
var t = thisComp.layer("product");
var r = t.sourceRectAtTime(time, false);
length(toWorld([0, 0, 0]), t.toWorld([t.anchorPoint[0], r.top + r.height / 2, 0]));
```

Check: value at the first and last frame (1110.5 and 986.8 px in the test push). In Advanced 3D also
set `ADBE Camera Focus Area Width` (100 to 200 px for a product); at 0 the product went soft with
aperture 60. The documented shortcut for a two-node camera is `length(position, pointOfInterest)`
(Adobe cameras page).

## 5. Motion blur for a model

Advanced 3D refuses `layer.motionBlur = true` ("Motion blur is not supported by the current
composition renderer"). Precompose, then CC Force Motion Blur on the precomp layer.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var inner = AEK.core.comp(ARGS.comp);
var outer = AEK.build.comp(inner.name + "_mb", { width: inner.width, height: inner.height, fps: inner.frameRate, duration: inner.duration });
var l = outer.layers.add(inner);
AEK.build.effect(l, "CC Force Motion Blur", { "CC Force Motion Blur-0001": ARGS.samples || 8 });
var fx = l.property("ADBE Effect Parade").property(1);
fx.property("CC Force Motion Blur-0003").setValue(ARGS.shutter || 180);   // Shutter Angle; -0002 Override Shutter Settings is on by default
return AEK.build.effectProps(l, 1);
```

Check: a frame at the fastest moment shows smear along the move; the effect costs about 4x a plain
frame (968 ms against 255 ms). Classic 3D comps take the layer switch plus `comp.motionBlur = true`;
a 3D solid blurred there, a model layer did not.

## 6. Lights by type

What each type exposes, measured with `AEX.threeD.settable` (Classic comp unless said): Parallel:
Intensity, Color, Falloff, Casts Shadows, Shadow Darkness. Spot: all of those plus
`ADBE Light Cone Angle`, `ADBE Light Cone Feather 2`, `ADBE Light Shadow Diffusion`. Point: no cone.
Ambient: Intensity and Color only. Environment in Advanced 3D: Intensity, Casts Shadows, Shadow
Darkness, Source; `ADBE Light Color` hidden. `ADBE Light Falloff Start` and
`ADBE Light Falloff Distance` stay hidden while Falloff is None (1).

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, position, target, type, hdri (name of an imported HDR item, optional), envIntensity}
var c = AEK.core.comp(ARGS.comp);
var key = AEX.threeD.keyLight(c, ARGS.position, ARGS.target, { type: ARGS.type || "SPOT", intensity: 80, darkness: 60, diffusion: 15, cone: 70 });
var out = { key: AEK.core.enumName(LightType, key.lightType), options: AEX.threeD.settable(key.property("ADBE Light Options Group")) };
if (ARGS.hdri) {
    if (AEX.threeD.rendererName(c) !== "advanced") { return { error: "switch the comp to Advanced 3D first: a layer source in a Classic comp crashed 27.0" }; }
    var env = AEX.threeD.envLight(c, { intensity: ARGS.envIntensity === undefined ? 80 : ARGS.envIntensity, source: AEK.core.item(ARGS.hdri) });
    out.env = env.lightSource.name;
}
return out;
```

Check: `ADBE Casts Shadows` is 1 on the key; the catcher's `ADBE Accepts Shadows` is 2. A light set
as an adjustment layer lights only the layers below it (Adobe cameras page).

## 7. Render, judge, deliver

Warm up, three frames, one sheet, then aerender on the saved project.

```javascript
// channel: bridge
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), out = { ms: [] }, t0, i, times = [0, c.duration / 2, c.duration - c.frameDuration * 2];
out.warmUpMs = AEX.threeD.warmUp(c, ARGS.out + "/warmup.png");
for (i = 0; i < times.length; i++) { t0 = new Date().getTime(); AEK.capture.frame(c, times[i], ARGS.out + "/check_" + i + ".png"); out.ms.push(new Date().getTime() - t0); }
app.project.save(new File(ARGS.project));
return out;
```

```bash
python3 ae.py sheet <out>/sheet.jpg <out>/check_0.png <out>/check_1.png <out>/check_2.png
python3 ae.py aerender --project <project>.aep --comp product_final --out <out>/product_v001.mp4 --template "H.264 - Match Render Settings - 15 Mbps"
python3 ae.py probe <out>/product_v001.mp4
```

Check: no frame is missing the model; probe shows the expected size, fps and frame count (72 frames
for 3 s at 24 fps). Render Quality, Smoothness and the shadow casting box are set in the GUI only.

## 8. 2.5D from cut-out layers

Layers 1920x1080 with alpha in a 960x540 Classic 3D comp (scale 50 means "fills the frame at z 0").
Measured: compensated layers kept 1056 px (960 x 1.1) at z 2000, 600 and -300; after a 300 px push
the foreground grew to 1488 px, the background to 1160 px.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {layers: [{name, file, z}], base, overscan, push, seconds}
var A = ARGS, c = AEK.build.comp("parallax", { width: 960, height: 540, fps: 24, duration: A.seconds || 3, bg: [0, 0, 0] }), i, l, s, out = [];
AEX.threeD.use(c, "classic");
var cam = AEK.build.camera(c, "cam", { focalLength: 50 }); cam.autoOrient = AutoOrientType.NO_AUTO_ORIENT;
var zoom = cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").value;
for (i = 0; i < A.layers.length; i++) {
    AEK.xio.importFile(A.layers[i].file);
    l = c.layers.add(AEK.core.item(A.layers[i].file.replace(/^.*[\/\\]/, ""))); l.name = A.layers[i].name; l.threeDLayer = true;
    s = AEX.threeD.parallaxScale(A.base || 50, A.layers[i].z, zoom, A.overscan || 1.1);
    l.property("ADBE Transform Group").property("ADBE Position").setValue([480, 270, A.layers[i].z]);
    l.property("ADBE Transform Group").property("ADBE Scale").setValue([s, s, s]);
}
cam.moveToBeginning();
var p = cam.property("ADBE Transform Group").property("ADBE Position");
AEK.motion.key(p, 0, [480, 270, -zoom]); AEK.motion.key(p, c.duration, [520, 260, -zoom + (A.push === undefined ? 300 : A.push)]);
AEK.motion.ease(p, 1, 40, 40); AEK.motion.ease(p, 2, 40, 40);
for (i = 0; i < A.layers.length; i++) { out.push({ name: A.layers[i].name, end: AEX.threeD.screenRect(c, AEK.core.layer(c, A.layers[i].name), c.duration - c.frameDuration) }); }
return out;
```

Check: at the last frame every layer has `left` 0 or less and `right` 960 or more; otherwise raise
the overscan or reduce the push. A ground plane in 2.5D: anchor at the contact line, X Rotation -90,
stretch Y, then Corner Pin out the remaining distortion (7tVyu-rjHbg 00:16:48 to 00:19:02).
`screenRect` only means something for layers entirely in front of the camera. Paint behind a cut-out
only where the move reveals it (u3qluraimKY 00:06:06).

## 9. 2.5D from a depth map

Near is white. The Displacement Map reads the map layer's source: blur on the map layer is ignored
(hard edges doubled the subject at 15 px). Precompose the depth layer with its blur.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, depth (map layer name), image (photo layer name), blur, max}
var c = AEK.core.comp(ARGS.comp), depth = AEK.core.layer(c, ARGS.depth), photo = AEK.core.layer(c, ARGS.image);
AEK.build.effect(depth, "ADBE Box Blur2", { "ADBE Box Blur2-0001": ARGS.blur || 25 });
var pre = AEK.build.precompose(c, [depth.index], ARGS.depth + "_soft", true);
var map = AEK.core.layer(c, ARGS.depth + "_soft"); map.enabled = false;
photo = AEK.core.layer(c, ARGS.image);
var fx = AEK.build.effect(photo, "ADBE Displacement Map", { "ADBE Displacement Map-0005": 0 });   // the photo may carry a grade already
fx.property("ADBE Displacement Map-0001").setValue(map.index);
var amt = fx.property("ADBE Displacement Map-0003");
AEK.motion.key(amt, 0, ARGS.max || 40); AEK.motion.key(amt, c.duration, 0);
AEK.motion.ease(amt, 1, 40, 40); AEK.motion.ease(amt, 2, 40, 40);
return { map: fx.property("ADBE Displacement Map-0001").value, keys: AEK.motion.keys(amt, c) };
```

Match names: `-0001` map layer, `-0002` use for horizontal, `-0003` max horizontal, `-0004` use for
vertical, `-0005` max vertical, `-0006` map behavior, `-0007` edge behavior, `-0008` expand output.
Check at the maximum: no doubled edges; a notch can still appear where a near edge crosses a bright
far shape, so keep the maximum at 15 to 40 px on a 960 px frame and scale the image 5 to 10 % up to
hide the edges.

## 10. What cannot be scripted (and the substitute that ran)

| Task                                                                                              | GUI path                                              | Scripted substitute                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Model units on import (cm against m is 100x)                                                      | Model Settings dialog at first import, under Advanced | `fitModel` from the footprint                                                                                                                                          |
| Embedded animation clip                                                                           | layer > Animation Options > Name                      | animate the layer transform                                                                                                                                            |
| Render Quality, Smoothness, shadow box, Fit to Scene                                              | Composition Settings > 3D Renderer > Options          | none; set once by a person                                                                                                                                             |
| Draft 3D for heavy meshes (about 750k triangles, M7v547PJ5Hk 00:06:18)                            | Composition panel toggle                              | none (`draft3d` is ignored); keep test comps at 960x540                                                                                                                |
| Create 3D Layer Instance, Create Orbit Null                                                       | Layer > Create; Layer > Camera                        | precomp plus effects; procedure 3                                                                                                                                      |
| 3D Camera Tracker solve                                                                           | Effect > Perspective > 3D Camera Tracker              | scenario-after-effects-tracking                                                                                                                                        |
| Substance material assignment                                                                     | Properties panel > Material                           | 27.1 beta API only                                                                                                                                                     |
| Material values: Roughness, Metallic, Opacity, Emission, Emission Intensity, Ambient              | Properties panel > Material                           | none on 27.0: `setValue`, keys and expressions throw "hidden" (measured); texture `ADBE3D Material Texturre Offset` (spelled so), `Rotation` and `Scale` accept values |
| Shift-parent new 3D text to the rig to snap it, push Z, unparent (M7v547PJ5Hk 00:15:57, 00:22:06) | Shift-drag the parent pick whip                       | `AEK.build.parent(text, rig, true)` (jump), Position `[0, 0, z]`, then `text.parent = null`: measured, the text lands at the rig's X and Y with Z added                |

## 11. Environment light that travels and takes the plate's tint

Key the environment light's Y Rotation so highlights travel across the product (Bartlett iOZkdYZPVU0
00:19:26). Tint the light to the plate's color cast (wwsHGbZN6ZU 00:09:49). Measured on 27.0 in
Advanced 3D: `ADBE Light Color` on an environment light is hidden, and a Tint on the source layer
itself left the frame unchanged (RMSE 0.00003). The light reads the source's pixels, so precompose
the source and tint inside: Tint at 100 % turned a model fully pink (RMSE 0.049), 20 % gave a light
cast.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, light (environment light name), from, to, seconds, tint ([r, g, b], optional), amount (percent)}
var c = AEK.core.comp(ARGS.comp), env = AEK.core.layer(c, ARGS.light), out = {};
var ry = env.property("ADBE Transform Group").property("ADBE Rotate Y");
AEK.motion.key(ry, 0, ARGS.from || 0);
AEK.motion.key(ry, ARGS.seconds || c.duration, ARGS.to === undefined ? 90 : ARGS.to);
AEK.motion.ease(ry, 1, 33, 33); AEK.motion.ease(ry, 2, 33, 33);
out.rotY = AEK.motion.keys(ry, c);
if (ARGS.tint && env.lightSource) {
    var srcName = env.lightSource.name;                 // the layer reference dies with precompose
    var pre = AEK.build.precompose(c, [env.lightSource.index], srcName + " tinted", true);
    var holder = AEK.core.layer(c, srcName + " tinted"); holder.enabled = false;
    env.lightSource = holder;
    var inner = pre.layer(1); inner.enabled = true;
    var fx = AEK.build.effect(inner, "ADBE Tint", {});    // the source may carry effects already
    fx.property(2).setValue(ARGS.tint);                 // Map White To
    fx.property(3).setValue(ARGS.amount === undefined ? 20 : ARGS.amount);   // Amount to Tint, percent
    out.source = env.lightSource.name; out.amount = fx.property(3).value;
}
return out;
```

Check: two Bezier keys on the light's Y Rotation; `source` ends in "tinted". On the sheet,
highlights sit in a different place on the first and last frame, and the model's color moves toward
the plate's cast without turning flat. Run only in an Advanced 3D comp (a layer source in a Classic
comp crashed 27.0). The shadow side has its own tint: Shadow Color on the catcher (procedure 2).

## 12. Product on a floor: flat floor, contact shadow, reflection

A product standing on a visible floor (no plate) needs three things the Advanced 3D renderer does
not draw by itself. They are a floor that takes the key's pool of light, a contact shadow (the
renderer has no ambient occlusion), and a reflection. The environment light keeps its shadows off
(`envLight` sets `ADBE Casts Shadows` 0 by default); the key spot casts the only shadow.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {glb, hdri, out}. Advanced 3D, 960x540, 24 fps, 3 s.
var W = 960, H = 540, X = W / 2, FLOOR = 380;
var c = AEK.build.comp("hero3d", { width: W, height: H, fps: 24, duration: 3, bg: [0.05, 0.06, 0.08] });
AEX.threeD.use(c, "advanced");
var m = c.layers.add(AEK.xio.importItem(ARGS.glb, {})); m.name = "product";
var r = m.sourceRectAtTime(0, false), fit = AEX.threeD.fitModel(m, c, { height: W * 0.5 * r.height / r.width, x: X, floorY: FLOOR, rotateY: -25 });
var env = AEX.threeD.envLight(c, { intensity: 90, source: AEK.xio.importItem(ARGS.hdri, {}) });
AEX.threeD.keyLight(c, [X - 520, FLOOR - 700, -500], [X, FLOOR - 40, 0], { intensity: 85, darkness: 55, diffusion: 20, cone: 60, color: [0.95, 0.91, 0.85] });
var rim = AEX.threeD.keyLight(c, [X + 600, FLOOR - 500, 700], [X, FLOOR - 60, 0], { name: "rim", intensity: 60, cone: 50 });
rim.property("ADBE Light Options Group").property("ADBE Casts Shadows").setValue(0);
AEX.threeD.floor(c, FLOOR, { color: [0.09, 0.11, 0.16], opacity: 82, scale: 300 });      // flat color; partly transparent for the reflection
AEX.threeD.contactShadow(c, FLOOR, fit.widthPx * 0.9, { depth: fit.widthPx * 0.42, opacity: 88 });
var rig = AEX.threeD.orbitRig(c, [X, FLOOR - fit.heightPx / 2, 0], { focalLength: 50, distance: 1150, tilt: -12, from: 22, to: -28, push: 220, bezier: [0.3, 0, 0.12, 1] });
AEX.threeD.focusOn(rig.camera, "product", { aperture: 30, areaWidth: 150 });
var contactY = AEX.threeD.screenPoint(c, m, m.property("ADBE Transform Group").property("ADBE Anchor Point").value, 1.5)[1];
var R = AEX.threeD.reflection(c, "product", { blur: 14, contactY: contactY, fadeTo: 150, backdrop: [0.05, 0.06, 0.08], name: "hero3d_final" });
var g = AEK.build.adjustment(R.comp, "grain");
AEK.build.effect(g, "ADBE Noise", { "ADBE Noise-0001": 1.2, "ADBE Noise-0002": 0, "ADBE Noise-0003": 1 });   // Clipping on: off wraps 16 bpc highlights into cyan specks
AEX.threeD.warmUp(c, ARGS.out + "/warmup.png");
return { fit: fit, camHeight: rig.height, center: AEX.threeD.screenPoint(c, rig.rig, [0, 0, 0], 2.95), frames: AEK.capture.frames(R.comp, [0, 1, 2, 2.95], ARGS.out, "hero") };
```

Check, measured on 27.0 with a generated speaker GLB at 960x540:

- `center` stays at [480, 270] at both ends of the orbit and push (tilt -12, camera height 244 then
  198 px).
- Frames of the final comp took 254 to 408 ms; `aerender` wrote 72 frames in 34 to 36 s with launch
  included.
- Render noise on the flat floor, high-pass standard deviation: 0.34 levels without grain, 0.53 in
  the H.264 file with grain 1.2.
- On the sheet: the base sits in a dark contact band, the reflection fades and softens away from the
  base, no floor edge or horizon shows, the product is never cropped.

Scaling and the floor's far edge:

- Every px value here is for a 960 px comp: multiply distances, light positions, contact shadow,
  blur and aperture by comp width / 960. At 1920, aperture 130 to 180 replaces 60 to 90.
- The horizon of an infinite floor sits in frame while the camera's tilt is smaller than half the
  vertical field of view (11.4 degrees at 50 mm, 16:9). Then no floor size hides the far edge: tilt
  further, or match the backdrop to the far floor color.
- With the tilt past half the field of view, the top ray meets the floor at camera height /
  tan(tilt - half field of view) in front of the camera. The floor's half size (2000 px x scale
  / 100) must reach past it, with margin for the orbit. Measured at 1920: tilt -16, camera 790 px
  above the floor, scale 550 kept the edge 46 to 75 px above the frame.
- Gate: `AEX.threeD.screenPoint(c, floor, [floor.source.width / 2, 0, 0], t)[1] < 0` at nine times
  across the shot. That point is the far edge; [width / 2, height, 0] lies behind the camera and
  reads wrongly.
- Render noise, the command for the critique check (run it on a frame captured before the grain
  layer):
  `magick f.png -crop 240x60+X+Y +repage -colorspace gray \( +clone -blur 0x3 \) -compose Mathematics -define compose:args=0,1,-1,0.5 -composite -format "%[fx:standard_deviation*255]" info:`.
- `fitModel` anchors the footprint, and the footprint counts parts such as a strap loop: the body
  can sit 45 px off center while the rig null reads exactly centered. Center from the product's
  matte (procedure 15).

What the helpers build, so a person can edit it:

- `floor`: a 3D solid lying flat (`ADBE Orientation` [270, 0, 0]), Accepts Shadows On (1), one flat
  color. Light the pool with the spot; do not paint a gradient on the floor.
- `contactShadow`: a black 3D solid 1 px above the floor with a feathered elliptical mask (feather
  40 % of its depth), Accepts Lights off, opacity 70 to 90 %. Size it from `fit.widthPx`.
- `reflection`: a duplicate of the 3D comp ("<comp> refl") where only the model, the lights, the
  camera and its null stay on; the model is mirrored by a negative Y scale about its base anchor. An
  outer comp stacks the backdrop, the reflection with Compound Blur (`ADBE Compound Blur`, `-0001`
  blur layer, `-0002` maximum blur) driven by a ramp precomp, a luminance inverted fade from the
  same ramp, then the 3D comp. The Gradient Ramp is `ADBE Ramp` (`-0001` start point, `-0002` start
  color, `-0003` end point, `-0004` end color, `-0005` shape). The ramp sits in its own precomp
  because a blur map reads the layer's source, not its effects.
- Mask mode by script is `mask.maskMode = MaskMode.SUBTRACT`; `property("ADBE Mask Mode")` returns
  null. Mask properties: `ADBE Mask Shape`, `ADBE Mask Feather`, `ADBE Mask Opacity`,
  `ADBE Mask Offset`.

## 13. A generated model that reads as soft plastic

Broad, soft highlights come from the file's roughness. On 27.0 a script cannot change Roughness or
Metallic on the model layer (procedure 10), but the importer reads the glTF factors, so edit them in
a copy of the GLB before import with [glb_material.py](../scripts/glb_material.py).

```bash
python3 glb_material.py list speaker.glb
python3 glb_material.py set speaker.glb speaker_v002.glb --material Rubber_Navy --material Rubber_Cream --roughness 0.22
```

Check: the `list` output shows each material's `roughness`, `metallic` and whether a texture drives
them (a factor multiplies the texture, so `--roughness-scale 0.5` works on textured materials).
Measured: caps at roughness 0.52 and 0.62 rendered broad soft highlights; at 0.22 they showed small
crisp speculars from the same HDRI and key. Change hard parts (caps, plastic, metal) and leave
fabric alone. The script refuses to overwrite any existing file and stops on a file that is not a
GLB.

## 14. 2.5D: keep the foreground in frame, sway a plane

A push grows a plane at depth z by (zoom + z) / (zoom + z - push). The foreground's inner edge (the
top of the grass band, `edgeOffset` px below frame center at the start) leaves the frame when that
growth carries it past the frame edge. `AEX.threeD.maxPush(zoom, z, edgeOffset, H / 2, keep)` gives
the largest push that keeps `keep` px of it visible; plan at 90 % of it.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// after procedure 8 built the planes (comp "parallax", a plane named "front"); ARGS: {edgeRow (source row of the inner edge), push}
var c = AEK.core.comp("parallax"), front = AEK.core.layer(c, "front"), cam = AEK.core.layer(c, "cam");
var zoom = cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").value;
var sF = front.property("ADBE Transform Group").property("ADBE Scale").value[0] / 100;
var zF = front.property("ADBE Transform Group").property("ADBE Position").value[2];
var edgeOffset = (ARGS.edgeRow - front.source.height / 2) * sF * zoom / (zoom + zF);   // on screen, at the plane's depth
var push = Math.min(ARGS.push, AEX.threeD.maxPush(zoom, zF, edgeOffset, c.height / 2, 60) * 0.9);
var p = cam.property("ADBE Transform Group").property("ADBE Position");
while (p.numKeys > 0) { p.removeKey(1); }                 // replaces the push of procedure 8
AEK.motion.key(p, 0, [c.width / 2, c.height / 2, -zoom]);
AEK.motion.key(p, c.duration - 15 * c.frameDuration, [c.width / 2 + 60, c.height / 2, -zoom + push]);
AEK.motion.bezier(p, 1, 2, [0.3, 0, 0.15, 1]);
// sway: Wave Warp on the foreground plane; Pinning 8 holds its bottom edge
AEK.build.effect(front, "ADBE Wave Warp", { "ADBE Wave Warp-0001": 2, "ADBE Wave Warp-0002": 3, "ADBE Wave Warp-0003": 120, "ADBE Wave Warp-0004": 90, "ADBE Wave Warp-0005": 0.4, "ADBE Wave Warp-0006": 8 });
return { push: push, edgeYEnd: AEX.threeD.screenPoint(c, front, [front.source.width / 2, ARGS.edgeRow, 0], c.duration - c.frameDuration)[1] };
```

Check, measured at 960x540, 50 mm (zoom 1333.3): the band edge started 163.5 px below center;
`maxPush` gave 295 px, the job pushed 266 px, and the edge ended at y 474.2, the planned 60 px
inside the frame. Coverage (`screenRect`) held for every plane at both ends; zero near-black pixels
on four frames. Lowering the camera during the push also keeps the band in frame; `maxPush` does not
count it, so check with `screenPoint`.

- Wave Warp match names: `-0001` type, `-0002` height (px), `-0003` width (px), `-0004` direction
  (degrees), `-0005` speed (cycles per second), `-0006` pinning, `-0007` phase. Measured on the 2048
  px plane: pinning 8 kept the bottom 8 rows still (0.05 levels of change) while the band moved 4.1
  levels. Pinning 2 also held the edges but damped the sway; 1, 3, 4, 6, 7 and 9 tore the bottom
  edge (bottom row alpha 0.53).
- Glow over a bright sky: read the sky's channel maxima first
  (`magick plate.png -crop <sky box> -format "%[fx:maxima.r*255]" info:`). The test plate had 29 %
  of its sky at red 250 or more; a Screen glow there clips red and draws a flat warm patch. Keep the
  glow at 10 to 12 % or grade the sky down first.

## 15. Layout before the camera move, and a move that reads

A title placed behind a product and a camera animated first left a third of the title hidden for the
whole shot, with a move of 18 % parallax that stopped after two seconds. Plan the read, check it on
mattes, then size the move.

1. **Write the read plan** for the first, middle and last frame: what must read (title, product,
   logo) and where. A title standing behind the product clears it on screen when its baseline
   projects above the product's top: further back (z 1500 behind a 2300 px camera at tilt -16 did
   it), smaller, or offset to one side.
2. **Build the layout, then animate.** Run the move once without rendering and write the mattes:
   `AEX.threeD.mattes(c, ["title", "product"], [0, mid, last], dir, "lay")` writes one PNG per layer
   and time with only that layer drawn, cameras and lights as they were.
3. **Measure:** `python3 layout_check.py lay_title_0.png lay_product_0.png` for each time. It prints
   the visible fraction of the title, whether it stays inside the frame with a 2 % margin, and the
   product matte's offset from the frame center. Pass: 0.9 or more, inside, offset within 2 % of the
   comp width. Shift the model by the offset and rerun.
4. **Size the move:**
   `AEX.threeD.parallax(c, {layer: product, point: anchor}, {layer: title, point: anchor}, t0, t1)`
   returns how far the two separate on screen (`relPct` of comp width). Pass: 25 % or more over the
   shot, 3 % or more in every 1 s window except a final hold second. Front-loaded beziers such as
   [0.3, 0, 0.12, 1] spend the move in two seconds; [0.25, 0, 0.35, 1] spreads it.
5. **Check focus on what must read.** Occlusion and framing say nothing about depth of field. Write
   the title's mattes with depth of field on, then off, and compare them with
   `python3 focus_check.py sharp_title_95.png dof_title_95.png`. It returns the Gaussian radius that
   turns one into the other. Pass for text that must read: 2 px or less at 1080 lines on every
   sampled frame.
6. **Two fixes.** Rack the focus with the move:
   `focusOn(cam, "product", {aperture, areaWidth, rack: {layer: "title", from: 0.5, to: 2.5, amount: 0.45}})`
   eases Focus Distance that share of the way toward the title. Or lower the aperture.
7. Render frames, then the final.

```javascript
// channel: bridge
// checked: live 27.0, after the procedure 12 build at 1920x1080 (layers "product" and "title"; title anchor at its baseline center)
// ARGS: {comp, out, product, title}; the title layer must exist already (procedure 12 builds none)
var c = AEK.core.comp(ARGS.comp), m = AEK.core.layer(c, ARGS.product || "product"), t = AEK.core.layer(c, ARGS.title || "title");
var T = [0, c.duration / 2, c.duration - c.frameDuration], R = {}, i;
R.mattes = AEX.threeD.mattes(c, ["title", "product"], T, ARGS.out, "lay");
var near = { layer: m, point: m.property("ADBE Transform Group").property("ADBE Anchor Point").value };
var far = { layer: t, point: t.property("ADBE Transform Group").property("ADBE Anchor Point").value };
R.total = AEX.threeD.parallax(c, near, far, T[0], T[2]).relPct;
R.windows = [];
for (i = 0; i < 4; i++) { R.windows.push(AEX.threeD.parallax(c, near, far, i, Math.min(i + 1, T[2])).relPct); }
return R;
```

Check, measured at 1920x1080 on a generated speaker GLB:

- Before: title z 700, orbit 10 to -12 degrees, push 380, bezier [0.3, 0, 0.12, 1]. Title visible
  0.62 to 0.68, product matte 21 to 45 px left of center, parallax 18.3 % (windows 7.1, 7.8, 2.7,
  0.7 %).
- After: title z 1500 at size 380, offset 160 px left, product shifted 25 px; orbit 14 to -14, push
  450, tilt -16, bezier [0.25, 0, 0.35, 1]. Title visible 1.0 and inside the frame at all three
  times, product offset -20 to 16 px, parallax 27.4 % (windows 7.7, 11.7, 6.3, 1.8 %).
- An orbit of 22 to -22 degrees measured 44 % but carried the title off the frame edge at both ends:
  the in-frame check catches it where the visible fraction does not.
- Focus, aperture 130, Focus Area Width 300, focus on the product: title radius 0.5, 1.0, 2.5, 5.0,
  7.0 and 9.5 px at 0, 0.5, 1, 1.5, 2 and 3.96 s, so too soft from about 1 s on. A rack of 0.45 from
  0.5 to 2.5 s: title 0.5 px at 0, 2, 3 and 3.96 s, product 0 px throughout. Aperture 60 without a
  rack: title 0 to 0.5 px.
- `AEX.threeD.dofBlur(c, cam, layer, point, t)` gives aperture x zoom x |d - focus| / (d x focus)
  from the camera's values. It ranks frames but does not give the rendered radius: 54, 56, 61, 67,
  72 and 79 px for the six measures above. Here the radius stayed under 1 px below about 56 and grew
  about 0.35 px per unit above it. Gate on the measured radius.

## 16. Version notes

- Advanced 3D final quality from 24.1; OBJ 24.2; shadow catcher and embedded animation 24.5; Accepts
  Lights 25.1; FBX and animated environment lights 25.2.
- Spot and parallel shadows 26.0; parametric meshes 26.0 (script 26.3); depth of field in Advanced
  3D 26.3.
- Substance on text and shapes, and layers as material sources: 27.0. Material scripting APIs arrive
  in the 27.1 beta.
- Picking a model's embedded animation clip is GUI-only on 27.0 (`ADBE ModelAnimName` is not a
  property).
- Tutorials before 25.2 say FBX cannot be imported; before 26.3 they fake depth of field with Camera
  Lens Blur.

## 17. A model seated in a still plate (low sun, push-in)

A cutout with a mirrored silhouette is never the shadow of a round object. When a model exists, or
image-to-3D can make one, the shadow and the shading come from one light in Advanced 3D. Lights are
calibrated on the plate's own ground, never guessed: guessed fills turned cream caps olive-gray and
a navy strap charcoal. The model's colors are checked before any light is set.

0. **Model colors first.** Two traps, both measured on 27.0. In a linearized project, Advanced 3D
   shades with the sRGB-encoded value of a glTF base color: textures as stored, factors encoded. A
   coral fabric (linear luminance 0.19) rendered as 0.41, a 0.35 floor as 0.63. Write a copy with
   [glb_material.py](../scripts/glb_material.py) `linear-store`, and the calibration floor too. For
   a branded product, `list --brand MATERIAL=#RRGGBB` reports each material's mean base color in
   linear light and its distance to the brand color; `tint` scales the texture per channel in linear
   light so the mean matches and the weave stays. Correct the texture, never the comp's grade.
   Measured: the generated fabric sat 14 Delta E from the brand coral, a little orange.

1. **Linear project.** `app.project.bitsPerChannel = 16`, working space `sRGB IEC61966-2.1`,
   `linearizeWorkingSpace = true`. Frames saved by script are then linear: encode them to sRGB
   before any check. Solid colors are linear values here: a Multiply shadow solid takes the plate's
   shadow over lit ratio per channel in linear light.
2. **Camera from the plate.** Horizon row, lens, camera height and tilt from the plate's prompt or
   its own lines. Zoom = comp width x focal length / 36. Real size: px per m at the base row = (base
   row - horizon row) / camera height in m.
3. **Sun direction from the plate's shadows.** Extend two shadow lines already in the plate (a
   railing post, a wall edge) to where they meet near the horizon, at screen x `xv`. Azimuth =
   atan((xv - comp width / 2) / zoom); elevation from the sun disc's height above the horizon.
   Measured on a terrace plate: lines met at x 127 to 161, azimuth -17, sun disc 3 to 4 degrees up.
4. **Environment from the plate.** [env_from_plate.py](../scripts/env_from_plate.py) maps the plate
   onto the part of the sphere the camera sees and clamps the sun disc (the parallel light carries
   it). It extends the sky by the plate's own horizon profile around the sun, and puts the plate's
   lit and shadowed ground below. Map orientation, measured with probe maps on a model: top is up, u
   0.75 looks into the plate, u 0.5 left, u 0 right, u 0.25 toward the camera. The zenith is solved
   so an up-facing floor gets the hue of the sky the calibration needs.
5. **Calibrate on the plate's ground.** Read the plate's sunlit and shadowed ground in linear light,
   per channel, in two boxes side by side. Render a GLB floor of a stated albedo (0.35, plain
   diffuse, roughness 1) under the same camera, with a vertical quad casting the sun's shadow on it.
   Set the environment intensity so the floor in shadow equals the shadowed ground. Then set the
   sun's intensity and color so the lit floor equals the sunlit ground. Iterate: intensity and color
   do not map linearly to the render (measured: the floor value grew about 1.4 times faster than the
   environment intensity, and a sun's gain flattened past about 1000 %). Gate: residual under 5 %
   per channel on both boxes, rechecked after any change to the map. Then remove the floor: the
   catcher passes take the shadow.
6. **Kicker for the sun-side edge.** A sun close behind the subject lights a thin edge only (table
   below). A cinematographer adds a kicker: a parallel light at the sun's azimuth or a little wider,
   higher (10 to 25 degrees), same color, shadows on. Name it "kicker" in the comp. Then render the
   lit pass with the kicker off and compare the camera-facing material: it must not move. Measured:
   an unshadowed kicker reached camera-facing fabric through its normal map and tripled its level
   (0.06 to 0.18); with shadows on, the facing band held at 0.074 to 0.079.
7. **One Advanced 3D comp per pass, the same camera keys in each.**
   - lit: the calibrated sun and the kicker (shadows on), the plate environment.
   - sun only: the sun and the kicker, blooming in the main comp above a threshold (Levels Input
     Black 0.6), so only what clips blooms.
   - shadow: the model with Casts Shadows Only, the sun, a catcher.
   - contact: the model with Casts Shadows Only, a parallel light from straight above (elevation
     89.9), a catcher.
   - neutral: the model under one white ambient light at 100 % (its base color), the `--neutral` of
     `integration_check.py --rendered`.
8. **Main comp, bottom to top.** Plate. The shadow pass as alpha matte of a Multiply solid, and the
   contact pass the same way. The lit pass, a light Add veil matted to the model (the plate's haze),
   bloom (Add) and grain.
9. **Plate move for the push.** A plate is one flat image: cut it at the wall's base. Key a Corner
   Pin on each part, every frame, from the homography of its own plane (floor, wall) through the
   same camera. Four floor points and four wall points, projected per frame, solved as 8x8.
10. **Finish to the plate.** Key the model's blur with the push: the enlarged plate softens.
    Measured: 2.7 to 4.0 px matched the plate's edges and kept the fabric weave readable. Grow the
    shadow's softness with distance: Compound Blur through a radial ramp keyed at the base.
11. **Gate.** Capture comp, plate alone, element over black, neutral through the same stack and the
    shadow layers alone at the first and last frame. Build the shadow matte from the linear capture
    (encoding it thins the soft far end). Run the compositing skill's
    `integration_check.py --rendered` with `--sun`, the plate's shadow and lit boxes and
    `--plate-length`.

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {glb, env (plate environment PNG), envI, lights: [{name, az, el, i, color, shadows}], az, el, catcher}
app.project.bitsPerChannel = 16; app.project.workingSpace = "sRGB IEC61966-2.1"; app.project.linearizeWorkingSpace = true;
var W = 1920, H = 1080, FY = 1000, tgt = [W / 2 - 40, FY, 820];
var glbItem = AEK.xio.importItem(ARGS.glb, {}), envItem = AEK.xio.importItem(ARGS.env, {});
function comp3d(name) { var c = AEK.build.comp(name, { width: W, height: H, fps: 24, duration: 4, bg: [0, 0, 0] }); AEX.threeD.use(c, "advanced"); return c; }
function model(c, castOnly) {
    var m = c.layers.add(glbItem); m.property("ADBE Transform Group").property("ADBE Position").setValue(tgt);   // fitted as in procedure 2
    if (castOnly) { m.property("ADBE Compositing Options Group").property("ADBE Casts Shadows").setValue(2); }   // 2 = Only
    return m;
}
var cS = comp3d("lit"); model(cS, false);
for (var i = 0; i < ARGS.lights.length; i++) {          // the calibrated sun, then the kicker (both cast shadows)
    var L = ARGS.lights[i];
    AEX.threeD.sunLight(cS, tgt, L.az, L.el, { intensity: L.i, color: L.color, shadows: L.shadows, name: L.name });
}
AEX.threeD.envLight(cS, { intensity: ARGS.envI, source: envItem });
var cH = comp3d("shadow"); model(cH, true);
AEX.threeD.sunLight(cH, tgt, ARGS.az, ARGS.el, { color: [1, 1, 1] });
AEX.threeD.shadowCatcher(cH, FY, { size: ARGS.catcher, x: tgt[0], z: tgt[2] });   // 2000 px, centered on the model
var cC = comp3d("contact"); model(cC, true);
AEX.threeD.sunLight(cC, tgt, 0, 89.9, { color: [1, 1, 1] });
AEX.threeD.shadowCatcher(cC, FY, { size: ARGS.catcher, x: tgt[0], z: tgt[2] });
var cN = comp3d("neutral"); model(cN, false);
var amb = cN.layers.addLight("ambient", [W / 2, H / 2]); amb.lightType = LightType.AMBIENT;
amb.property("ADBE Light Options Group").property("ADBE Light Intensity").setValue(100);
return { passes: [cS.name, cH.name, cC.name, cN.name] };
```

Measured on the terrace plate, in linear light: sunlit ground 0.316 / 0.205 / 0.147, shadowed 0.147
/ 0.134 / 0.133. With the model and floor written `linear-store` and the map from the plate:
environment 217 %, sun 1100 % with color [1, 0.58, 0.21]. Residual: -2.4 to -0.5 % lit, +1.4 to +3.2
% shadow. Kicker: azimuth -50, elevation 14, 700 %, shadows on. Camera-facing fabric in shade: 0.074
linear (target 0.08 to 0.10 for a 0.20 coral beside a 0.35 ground in shadow), its top 0.25, its
underside 0.083.

What the renderer did, measured on 27.0 with a 16 cm speaker GLB, 1920x1080:

| Need              | Result                                                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Shadow catcher    | Accepts Shadows Only works. A 10000 px catcher drew a second shadow wedge far away; 2000 px centered did not             |
| Catcher edge      | the far edge drew a thin line near the horizon: mask both shadow mattes from the wall's base row down                    |
| Cast only         | Casts Shadows Only (2) on the model: the shadow without the model, in a pass of its own                                  |
| Softness          | a parallel light's shadow is hard; Compound Blur through a distance ramp gave 18 px near and 44 px far                   |
| Ambient           | no ambient occlusion: the contact pass (light from straight above) gives the dark band under the base                    |
| Shadow color      | the pass as matte of a Multiply solid at the plate's shadow over lit ratio, linear: hue within 0.02                      |
| Environment light | a white upper half lit an upward floor, a white lower half did not: top is up. Around the horizon, unsettled             |
| Output range      | the render clamps at 1.0 per channel; a 3D comp saved at 32 bpc came back in steps of 1/25: work at 16 bpc               |
| Neutral           | one white ambient light at 100 % renders the base color as the renderer reads it (encoded unless written `linear-store`) |
| Base color        | textures taken as stored, factors encoded: coral fabric 0.19 rendered 0.41; `linear-store` gave 0.204 and caps 0.765     |
| Dark materials    | a navy rubber (albedo 0.02) took a gray specular sheen of about 0.015 from the environment; roughness 1 kept it navy     |
| No light          | a comp with no light renders a default headlight; a sun alone from behind leaves the front black                         |
| Sun rim           | a sun about 20 degrees off the view axis lights an edge band of about 1 - cos 20 = 0.06 of the radius                    |
| Cap shadow        | a shadowed kicker along the body's axis lets the end cap shade the near part of the top                                  |

Check, `integration_check.py --rendered` on the first and last frame: shade 0.72 and 0.69, density
gap 0.005 and 0.003, contact 0 and -3 px, blacks within 0.04 of the plate's, material 3.7 (limit 4).
