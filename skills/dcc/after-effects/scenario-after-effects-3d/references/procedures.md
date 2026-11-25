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
var ct = cam.property("ADBE Transform Group"), rt = rig.property("ADBE Transform Group"), d = ARGS.distance || 1100, h = ARGS.height || 150, k;
ct.property("ADBE Rotate X").setValue(-8);
AEK.motion.key(ct.property("ADBE Position"), 0, [0, -h, -d]);                       // only Z changes on the camera
AEK.motion.key(ct.property("ADBE Position"), c.duration, [0, -h, -d + (ARGS.push || 250)]);
AEK.motion.key(rt.property("ADBE Rotate Y"), 0, ARGS.from || -35);
AEK.motion.key(rt.property("ADBE Rotate Y"), c.duration, ARGS.to || 35);
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
    var env = AEX.threeD.envLight(c, { intensity: ARGS.envIntensity || 80, source: AEK.core.item(ARGS.hdri) });
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
AEK.motion.key(p, 0, [480, 270, -zoom]); AEK.motion.key(p, c.duration, [520, 260, -zoom + (A.push || 300)]);
AEK.motion.ease(p, 1, 40, 40); AEK.motion.ease(p, 2, 40, 40);
for (i = 0; i < A.layers.length; i++) { out.push({ name: A.layers[i].name, end: AEX.threeD.screenRect(c, AEK.core.layer(c, A.layers[i].name), c.duration - c.frameDuration) }); }
return out;
```

Check: at the last frame every layer has `left` 0 or less and `right` 960 or more; otherwise raise
the overscan or reduce the push. `screenRect` only means something for layers entirely in front of
the camera. Paint behind a cut-out only where the move reveals it (u3qluraimKY 00:06:06).

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
AEK.build.effect(photo, "ADBE Displacement Map", { "ADBE Displacement Map-0005": 0 });
var fx = photo.property("ADBE Effect Parade").property(1);
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

| Task                                                                                              | GUI path                                              | Scripted substitute                                                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Model units on import (cm against m is 100x)                                                      | Model Settings dialog at first import, under Advanced | `fitModel` from the footprint                                                                                                                                                                                                  |
| Embedded animation clip                                                                           | layer > Animation Options > Name                      | animate the layer transform                                                                                                                                                                                                    |
| Render Quality, Smoothness, shadow box, Fit to Scene                                              | Composition Settings > 3D Renderer > Options          | none; set once by a person                                                                                                                                                                                                     |
| Draft 3D for heavy meshes (about 750k triangles, M7v547PJ5Hk 00:06:18)                            | Composition panel toggle                              | none (`draft3d` is ignored); keep test comps at 960x540                                                                                                                                                                        |
| Create 3D Layer Instance, Create Orbit Null                                                       | Layer > Create; Layer > Camera                        | precomp plus effects; procedure 3                                                                                                                                                                                              |
| 3D Camera Tracker solve                                                                           | Effect > Perspective > 3D Camera Tracker              | scenario-after-effects-tracking                                                                                                                                                                                                |
| Substance material assignment                                                                     | Properties panel > Material                           | 27.1 beta API only                                                                                                                                                                                                             |
| Material values: Roughness, Metallic, Opacity, Emission, Emission Intensity, Ambient              | Properties panel > Material                           | none on 27.0: `setValue`, `setValueAtTime` and `expression` all throw "hidden" in Advanced 3D (measured); `ADBE3D Material Texturre Offset` (spelled so), `ADBE3D Material Rotation` and `ADBE3D Material Scale` accept values |
| Shift-parent new 3D text to the rig to snap it, push Z, unparent (M7v547PJ5Hk 00:15:57, 00:22:06) | Shift-drag the parent pick whip                       | `AEK.build.parent(text, rig, true)` (jump), Position `[0, 0, z]`, then `text.parent = null`: measured, the text lands at the rig's X and Y with Z added                                                                        |

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
    AEK.build.effect(inner, "ADBE Tint", {});
    var fx = inner.property("ADBE Effect Parade").property(1);
    fx.property(2).setValue(ARGS.tint);                 // Map White To
    fx.property(3).setValue(ARGS.amount || 20);         // Amount to Tint, percent
    out.source = env.lightSource.name; out.amount = fx.property(3).value;
}
return out;
```

Check: two Bezier keys on the light's Y Rotation; `source` ends in "tinted". On the sheet,
highlights sit in a different place on the first and last frame, and the model's color moves toward
the plate's cast without turning flat. Run only in an Advanced 3D comp (a layer source in a Classic
comp crashed 27.0). The shadow side has its own tint: Shadow Color on the catcher (procedure 2).
