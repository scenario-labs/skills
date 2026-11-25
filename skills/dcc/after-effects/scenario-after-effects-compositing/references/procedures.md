# Procedures: compositing by script

Every job is the body of a function run with
`ae.py run job.jsx --lib <skill>/scripts/comp.jsx --args '{...}'` (bridge), or written for a person
with `--channel handoff`. Paths come from `ARGS` and are absolute. In someone's project, run inside
one undo step (`--undo NAME`) and never delete: new layers and effects carry `_v001` or a clear
name, and the original stays. Test sessions start with `AEK.core.fresh()`.

The measured numbers below come from a synthetic 1280x720, 24 fps green screen plate with a known
truth matte: thin hair strands, a 45 % veil, a motion-blurred edge, a spilled white shirt and a
light stand.

## Contents

1. Inspect the plate: screen color, alpha mode, project color settings
2. Key a green screen: garbage, soft matte, core matte, holdout; Keylight controls by View; 2b core
   blurred inward
3. Read the matte as numbers (shell)
4. Track mattes: shared matte, boolean matte, Set Matte
5. Pre-render a heavy key and swap every use
6. Match levels per channel
7. Light wrap and grain
8. Cutout with no screen: external matte, Object Matte settings
9. Remove a logo from moving fabric: offset patch
10. Audit alpha interpretation

## 1. Inspect the plate

Use first on any keying shot. Pick a time where the screen is clean and the subject is busiest.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {plate, sequence, fps, screenBox: [x, y, halfW, halfH] in layer pixels, t (seconds)}
var A = ARGS, P = app.project;
var it = AEK.xio.importItem(A.plate, { sequence: A.sequence, fps: A.fps });
var c = AEK.build.comp("inspect_v001", { width: it.width, height: it.height, fps: A.fps, duration: it.duration });
var l = c.layers.add(it), b = A.screenBox;
// sampleColor moves comp.time to t and reads .value: sampleImage through valueAtTime alone returns zeros from a script
var s = AEX.comp.sampleColor(c, l, [b[0], b[1]], [b[2], b[3]], A.t);
var dom = (s[1] > s[0] && s[1] > s[2]) ? "green" : ((s[2] > s[0] && s[2] > s[1]) ? "blue" : "none");
return { item: it.name, frames: Math.round(it.duration * it.frameRate), fps: it.frameRate, hasAlpha: it.mainSource.hasAlpha,
    project: { bpc: P.bitsPerChannel, workingSpace: P.workingSpace, linearBlending: P.linearBlending },
    screen: [s[0], s[1], s[2]], dominant: dom };
```

Check: `dominant` is the screen color; frame count and fps match the plate as shot. Measured screen
on the test plate: [0.102, 0.576, 0.165]. If `workingSpace` or `linearBlending` is not what the
project owner chose, stop: inherited color settings changed a 50 % gray luma matte from 0.502 to
0.737.

## 2. Key a green screen

A precomp holding two keyed copies of the plate: the soft matte keeps hair and motion blur, the core
matte on top fills holes. The holdout mask removes the core from semi-transparent areas. On a noisy
plate, pull the matte from a denoised copy (Remove Grain, `VISINF Grain Removal`) and keep the grain
on the color layer (_0lcyyybbng 00:01:11).

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {plate, sequence, fps, screen: [r,g,b], garbage: [{t, points}], holdout: [{t, points}] or null,
//        soft: [clipBlack, clipWhite], core: [clipBlack, clipWhite], choke (px), out}
var A = ARGS, it = AEK.xio.importItem(A.plate, { sequence: A.sequence, fps: A.fps });
var key = AEK.build.comp("plate_key_v001", { width: it.width, height: it.height, fps: A.fps, duration: it.duration });
var soft = key.layers.add(it); soft.name = "soft matte";
AEX.comp.mask(soft, null, { keys: A.garbage, feather: 20, name: "garbage" });
var s = AEX.comp.keyChain(soft, { screen: A.screen, clipBlack: A.soft[0], clipWhite: A.soft[1],
    cleaner: { chatter: true, contrast: 20 }, spill: { method: "ultra", color: A.screen } });
var core = key.layers.add(it); core.name = "core matte";
AEX.comp.mask(core, null, { keys: A.garbage, feather: 20, name: "garbage" });
AEX.comp.keyChain(core, { screen: A.screen, clipBlack: A.core[0], clipWhite: A.core[1], spill: { method: "ultra", color: A.screen } });
if (A.holdout) { AEX.comp.mask(core, null, { keys: A.holdout, feather: 6, mode: "subtract", name: "soft detail holdout" }); }
// channel 5 = alpha; input white 0.7 crunches the core to solid
AEK.build.effect(core, "ADBE Easy Levels2", { "ADBE Easy Levels2-0001": 5, "ADBE Easy Levels2-0004": 0.7 }, "crunch alpha");
AEK.build.effect(core, "ADBE Simple Choker", { "ADBE Simple Choker-0002": A.choke }, "core inside edge");
var last = it.duration - 1 / A.fps;
var alpha = AEK.capture.frames(AEX.comp.alphaView(key, "plate_key_alpha"), [0, it.duration / 2, last], A.out, "alpha");
// Status view of the soft matte alone: the core on top would hide it
core.enabled = false; AEX.comp.setView(soft, s.keylight, "status");
var status = AEK.capture.frame(key, it.duration / 2, A.out + "/status_mid.png").path;
AEX.comp.setView(soft, s.keylight, "intermediate"); core.enabled = true;
return { comp: key.name, alpha: alpha, status: status };
```

Check with procedure 3. Measured: soft 35/75, core 40/60, choke 3 with the holdout gave mean alpha
error 0.0051, core holes 0.71 %, hair 0.44 against 0.53 truth. Without the holdout the veil speckled
(standard deviation 0.171 against 0.058). Status frame: white core, black screen, gray only at
edges. Spill read on the shirt: green excess +0.0017, luma 0.929 as on the plate.

Keylight controls by View (measured on the same plate, frame rendered over gray): in Intermediate
Result (10), Replace Method Source, Hard Colour and Soft Colour render pixel-identical, Edge Colour
Correction with Brightness 60 changes nothing, and an unlocked warm Despill Bias touches 0.2 % of
pixels. In Final Result (11), Hard against Soft Colour changes 17 % of pixels, Edge Brightness 60
changes 7 %, the same Despill Bias 24 %. Replace Method None differs in both Views. So the despill
and edge controls belong to a Keylight-only key on Final Result; with the suppressor chain, fix the
color on the suppressor (Ultra Desaturate, Luma Correction) or on a color plate.

### 2b. Soften the core only inward

Blur the core for a softer transition without growing it: an unblurred duplicate of the core is its
Alpha track matte, so the blur can only fade the core inside its own edge (K-uOFPoIm6U 00:14:01 to
00:15:39). The core here is a layer, not a matte of a matte: its duplicate is the only matte.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, core (layer name, already keyed and choked), blur (px, no larger than the choke)}
var A = ARGS, c = AEK.core.comp(A.comp), core = AEK.core.layer(c, A.core);
// duplicate BEFORE the blur: the matte must keep the hard edge
var dup = core.duplicate(); dup.name = core.name + " inward matte_v001";
AEK.build.effect(core, "ADBE Box Blur2", { "ADBE Box Blur2-0001": A.blur, "ADBE Box Blur2-0004": 0 }, "inward blur_v001");
return AEK.build.matte(core, dup, "alpha");
```

Check: on `alphaView`, no alpha outside the unblurred core edge. Measured with choke 4 and blur 4: 0
px outside the core with the matte, 33,070 px of blur spill without it; the softening inside the
edge is the same.

Variants measured on the same frame (single Keylight, sampled screen, no garbage):

| Setting                          | Mean alpha error | Screen left (%) | Core holes (%) |
| -------------------------------- | ---------------- | --------------- | -------------- |
| defaults                         | 0.28             | 90              | 31.5           |
| clip 20/80                       | 0.100            | 28              | 0              |
| clip 30/70                       | 0.049            | 11              | 0              |
| clip 40/60                       | 0.027            | 2.8             | 0              |
| Screen Gain 130                  | 0.030            | 4.7             | 54             |
| clip 20/80 plus animated garbage | 0.015            | 1.8             | 2.3            |

## 3. Read the matte as numbers

Render the alpha view and a final over a flat color, then read numbers from the PNGs. With no
reference matte, read boxes: a box of screen must give a 99th percentile of 0, a box inside the body
a 1st percentile of 1.

```bash
M=<skill>/scripts/matte_metrics.py
python3 $M alpha alpha_f00024.png reference_f00024.png          # mean error, screen left %, core holes %, edge error
python3 $M levels alpha_f00024.png --box 60,60,200,200            # screen box: all three percentiles 0
python3 $M levels alpha_f00024.png --box 560,500,120,120          # body box: 1st percentile 1.0
python3 $M spill final_over_gray_f00024.png --box 600,560,80,60   # green_excess near 0, luma as on the plate
python3 $M grain plate_f00024.png --box 40,300,120,120            # grain per channel, flat area
python3 $M edge alpha_f00024.png --row 400 --x0 700 --x1 800      # 10-90 % edge width in px
python3 $M diff version_a.png version_b.png --box 500,250,300,220 # mean and max difference, 0-255
python3 skills/scenario-after-effects-expert/scripts/ae.py sheet sheet.jpg status_mid.png alpha_f00024.png final_f00024.png
```

Check: the numbers move the way the change intended; then read one sheet. A previous version of the
key is the reference when there is no truth matte.

## 4. Track mattes: shared matte, boolean matte, Set Matte

One matte can drive many layers. A matte's own track matte is ignored, so a boolean matte is built
inside a precomp. Set Matte reads a layer's source, so it must point at a precomp of the key.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {width, height, fps, out}
var A = ARGS, W = A.width, H = A.height;
var inner = AEK.build.comp("matte_ellipse_minus_bar_v001", { width: W, height: H, fps: A.fps, duration: 1 });
AEK.build.shape(inner, "M1", { name: "e", type: "ellipse", size: [H * 0.75, H * 0.75], fill: [1, 1, 1] }, { position: [W / 2, H / 2] });
AEK.build.shape(inner, "M2", { name: "r", type: "rect", size: [W, H / 4], fill: [1, 1, 1] }, { position: [W / 2, H / 2] });
inner.layer("M1").setTrackMatte(inner.layer("M2"), TrackMatteType.ALPHA_INVERTED);
var c = AEK.build.comp("shared_matte_v001", { width: W, height: H, fps: A.fps, duration: 1 });
AEK.build.solid(c, "black", [0, 0, 0]);
var m = c.layers.add(inner); m.name = "matte";
var t1 = AEK.build.solid(c, "target A", [1, 0.5, 0]), t2 = AEK.build.solid(c, "target B", [0, 0.5, 1]);
AEX.comp.mask(t2, [[0, 0], [W / 2, 0], [W / 2, H], [0, H]], { mode: "add" });
var r = [AEK.build.matte(c.layer("target A"), c.layer("matte"), "alpha"), AEK.build.matte(c.layer("target B"), c.layer("matte"), "alpha")];
// Set Matte on a solid, taking the matte from the precomp layer (index), not from a layer keyed in place
var sm = AEK.build.solid(c, "set matte from precomp", [1, 1, 1]);
AEK.build.effect(sm, "ADBE Set Matte3", { "ADBE Set Matte3-0001": c.layer("matte").index }, "set matte");
sm.enabled = false;
return { mattes: r, matteVisible: c.layer("matte").enabled, frame: AEK.capture.frame(c, 0, A.out + "/shared_matte.png").path };
```

Check: `matteVisible` false (`setTrackMatte` switches the matte's video off and it stays off after
`removeTrackMatte`); the frame shows the ellipse minus the bar in both targets. Measured traps:
effects on the matte apply before it is read (Simple Choker 20 moved the edge 7 px); a Set Matte
pointed at a layer carrying Keylight as an effect read alpha 1.0 everywhere, the same Set Matte on a
precomp of it read 0.229 against 0.215 truth.

## 5. Pre-render a heavy key and swap every use

Render once with alpha, import, and point every layer that used the comp to the file. The comp stays
in the project for later changes.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, out}
var c = AEK.core.comp(ARGS.comp);
var r = AEX.comp.preRender(c, ARGS.out + "/" + c.name + "_prerender.mov", "High Quality with Alpha");
return r;
```

Check: `replacedLayers` equals the number of uses; `hasAlpha` true and `alphaMode` `PREMULTIPLIED`;
an alpha frame from before and after differs by 0 (`matte_metrics.py diff`). Measured: 48 frames
rendered in 4 to 8.6 s, ProRes 4444 `yuva444p12le`, frame time 1,503 ms down to 263 ms. In the GUI
the same is Composition > Pre-render, then Import and Replace Usage in the output module
(_0lcyyybbng 00:09:31).

## 6. Match levels per channel

Sample a dark and a bright patch of the element and of the plate, then solve Levels per channel so
element black lands on plate black and element white on plate white (vJ8X58uknsk 00:00:27; Levels
Output Black in gomawnMPWEg frame 00:14:20).

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, element, plate, elementBlack, elementWhite, plateBlack, plateWhite: [x, y, halfW, halfH] in each layer's own pixels, t}
var A = ARGS, c = AEK.core.comp(A.comp), el = AEK.core.layer(c, A.element), pl = AEK.core.layer(c, A.plate);
function rd(l, b) { return AEX.comp.sampleColor(c, l, [b[0], b[1]], [b[2], b[3]], A.t || 0); }
var eb = rd(el, A.elementBlack), ew = rd(el, A.elementWhite), pb = rd(pl, A.plateBlack), pw = rd(pl, A.plateWhite);
var idx = AEK.build.effect(el, "ADBE Pro Levels2", {}, "match levels_v001").propertyIndex;
var base = [14, 21, 28], set = [], i, g, ob, fx;
for (i = 0; i < 3; i++) {
    fx = el.property("ADBE Effect Parade").property(idx);
    g = (pw[i] - pb[i]) / (ew[i] - eb[i]);
    ob = pb[i] - eb[i] * g;
    fx.property("ADBE Pro Levels2-00" + base[i]).setValue(ob);          // Red, Green, Blue Output Black
    fx.property("ADBE Pro Levels2-00" + (base[i] + 1)).setValue(ob + g); // Output White
    set.push([ob, ob + g]);
}
return { outputBlackWhite: set, plate: { black: pb, white: pw }, after: { black: rd(el, A.elementBlack), white: rd(el, A.elementWhite) } };
```

Check: `after.black` and `after.white` equal the plate values within 2/255 per channel (measured:
exact). A dark plate patch must be a real shadow of the plate, not a black border. Light direction
cannot be graded (vJ8X58uknsk 00:01:05).

## 7. Light wrap and grain

The wrap is built from track mattes (no plugin); grain goes last, on whatever lacks it.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, fg (precomp layer of the key), bg, radiusPct, opacity, plateGrain: [r,g,b], grainAt1: [r,g,b], t, out}
var A = ARGS, c = AEK.core.comp(A.comp), fg = AEK.core.layer(c, A.fg), bg = AEK.core.layer(c, A.bg);
var w = AEX.comp.lightWrap(c, fg, bg, { radiusPct: A.radiusPct || 1.5, opacity: A.opacity || 40, mode: "add" });
// Add Grain: Viewing Mode 3 = Final Output; the default (Preview) grains only a box and renders its outline
var gi = AEK.build.effect(bg, "VISINF Grain Implant", { "VISINF Grain Implant-0021": 3 }, "match grain_v001").propertyIndex;
var fx = bg.property("ADBE Effect Parade").property(gi), k = ["0002", "0003", "0004"], set = [], i;
for (i = 0; i < 3; i++) {
    // per-channel intensity scales grain linearly: target / grain measured at intensity 1
    set.push(A.plateGrain[i] / A.grainAt1[i]);
    fx.property("VISINF Grain Implant-" + k[i]).setValue(set[i]);
}
return { wrap: w, grainIntensity: set, frame: AEK.capture.frame(c, A.t || 0, A.out + "/integrated.png").path };
```

Check: `matte_metrics.py grain` on a flat area of the background and of the plate, at the same tone:
within 10 % per channel (measured within 1 % on a midtone wall at luma 0.33: plate 0.0163, 0.0109,
0.0272; result 0.0163, 0.0110, 0.0275). First run once at intensity 1 to read `grainAt1` on that
tone (measured here 0.0080, 0.0088, 0.0098). Add Grain is tone dependent: with the same settings the
dark desk (0.12) got 0.0227 in red, 40 % more, and the bright window (0.93) about 0.0017. Calibrate
on the tone the subject sits against, then read shadows and highlights too. Wrap:
`matte_metrics.py diff` with and without the wrap on an edge crop: a few levels against bright
background, about 0 against dark, nothing outside the subject. Alternative grain: Match Grain,
`VISINF Grain Duplication`, `-0013` = the plate's layer index (the plate may stay hidden), `-0002`
Viewing Mode 5 (Final Output); measured within 3 to 5 %; mode 3 added no grain.

## 8. Cutout with no screen

### 8a. External matte as a track matte

The unattended route: a matte sequence made outside After Effects (segmentation, layer separation, a
person's roto), white = keep.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {plate, matte, fps, matteType: "luma" | "alpha", out}
var A = ARGS, p = AEK.xio.importItem(A.plate, { sequence: true, fps: A.fps }), m = AEK.xio.importItem(A.matte, { sequence: true, fps: A.fps });
var pf = Math.round(p.duration * p.frameRate), mf = Math.round(m.duration * m.frameRate);
if (pf !== mf) { throw new Error("matte has " + mf + " frames, plate " + pf + ": fix the matte before compositing"); }
var c = AEK.build.comp("cutout_v001", { width: p.width, height: p.height, fps: A.fps, duration: p.duration });
var ml = c.layers.add(m); ml.name = "matte (external)";
var pl = c.layers.add(p); pl.name = "plate";
var r = AEK.build.matte(c.layer("plate"), c.layer("matte (external)"), A.matteType || "luma");
var last = p.duration - 1 / A.fps;
return { matte: r, frames: pf, alpha: AEK.capture.frames(AEX.comp.alphaView(c, "cutout_alpha"), [0, p.duration / 2, last], A.out, "cutout_alpha") };
```

Check: frame counts equal; three alpha frames on one sheet; the edge sits on the object at every
frame. Measured: alpha error 0 against the source matte; a one-frame slip gave 0.0101 (edge error
0.12), twice the best key. Put each sequence in its own folder: an import sweeps every numbered file
of the folder (194 frames came in instead of 48).

### 8b. Object Matte settings after a person's selection

Object Matte (effect `ADBE Samurai`) needs strokes drawn in the Layer panel. A script reads the
strokes and sets the matte properties.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, layer, feather, shiftEdge, reduceChatter, out}
var A = ARGS, c = AEK.core.comp(A.comp), l = AEK.core.layer(c, A.layer), fx = l.property("ADBE Effect Parade"), om = null, i;
for (i = 1; i <= fx.numProperties; i++) { if (fx.property(i).matchName === "ADBE Samurai") { om = fx.property(i); } }
if (!om) { throw new Error("No Object Matte on " + l.name + ": a person draws the selection first (GUI)"); }
var strokes = om.property("ADBE Samurai Strokes Group").numProperties;
if (A.feather !== undefined) { om.property("/spatialsmoothing2").setValue(A.feather); }
if (A.shiftEdge !== undefined) { om.property("/rmshiftedges").setValue(A.shiftEdge); }
if (A.reduceChatter !== undefined) { om.property("/rmreducechatter").setValue(A.reduceChatter); }
return { strokes: strokes, warning: strokes === 0 ? "no strokes: the matte is alpha 1.0 everywhere" : "",
    feather: om.property("/spatialsmoothing2").value, shiftEdge: om.property("/rmshiftedges").value, reduceChatter: om.property("/rmreducechatter").value,
    alpha: AEK.capture.frame(AEX.comp.alphaView(c, "object_matte_alpha"), c.duration / 2, A.out + "/object_matte_alpha.png").path };
```

Check: `strokes` greater than 0; the alpha frame shows the object only. Measured with no strokes:
alpha 1.0 everywhere. Defaults on 27.0: Version 4, Feather 5 (`/spatialsmoothing2`), Shift Edge 0,
Reduce Chatter 0; the Refine Edge group has its own Feather and Shift Edge (`/HBspatialsoftness2`,
`/HBspatialchoke`). Pre-render the result (procedure 5) before building on it.

## 9. Remove a logo from moving fabric: offset patch

The plate itself, shifted so clean fabric covers the logo, shown only through a feathered matte that
follows the logo. Use whole pixels and whole pattern periods.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, plate (layer name), offset: [dx, dy] whole px, size (px), feather (px), track: [{t, pos: [x, y]}] in comp space, out}
var A = ARGS, c = AEK.core.comp(A.comp), pl = AEK.core.layer(c, A.plate);
var patch = pl.duplicate(); patch.name = "patch_v001 (offset " + A.offset[0] + "," + A.offset[1] + ")";
var pp = patch.property("ADBE Transform Group").property("ADBE Position"), v = pp.value;
// the plate's Position must be unkeyed; a sub-pixel offset resamples and softens the grain
pp.setValue([v[0] - A.offset[0], v[1] - A.offset[1]]);
var m = AEK.build.shape(c, "patch matte_v001", { name: "e", type: "ellipse", size: [A.size, A.size], fill: [1, 1, 1] }, { position: A.track[0].pos });
var mp = m.property("ADBE Transform Group").property("ADBE Position"), i;
for (i = 0; i < A.track.length; i++) { mp.setValueAtTime(A.track[i].t, A.track[i].pos); }
AEK.build.effect(m, "ADBE Box Blur2", { "ADBE Box Blur2-0001": A.feather, "ADBE Box Blur2-0004": 0 }, "matte feather");
var r = AEK.build.matte(c.layer(patch.name), c.layer("patch matte_v001"), "alpha");
var last = c.duration - 1 / c.frameRate;
return { patch: r, frames: AEK.capture.frames(c, [0, c.duration / 2, last], A.out, "patched") };
```

Check: `matte_metrics.py diff` of the patched frame against a clean neighbor area, and against the
plate inside the patch box: the patch error near the plate's grain floor; no ring at the feather.
Measured: 30.4 down to 3.45 against a 2.88 floor (offset 170 px, 2 stripe periods, ellipse 170 px,
feather 12). Offset 169.65 with feather 24: inner error 6.05 against 4.67. Track data comes from
scenario-after-effects-tracking; on folding fabric use the Content-Aware Fill panel (Surface) or a
hero frame with a corner pin ([gui-paths](gui-paths.md)).

## 10. Audit alpha interpretation

A premultiplied file read as straight makes a dark ring; run this on intake.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: none
var out = [], i, it, ms;
for (i = 1; i <= app.project.numItems; i++) {
    it = app.project.item(i);
    if (!(it instanceof FootageItem) || !it.mainSource || !it.mainSource.hasAlpha) { continue; }
    ms = it.mainSource;
    out.push({ name: it.name, alphaMode: AEK.core.enumName(AlphaMode, ms.alphaMode) });
}
return out;
```

Check: every file rendered by a 3D package, After Effects (`High Quality with Alpha` writes
premultiplied) or a generator with a black matte reads `PREMULTIPLIED`. Over white, the edge of a
wrongly read premultiplied disk fell to luma 0.79; the three other combinations were clean. Fix in
the GUI with File > Interpret Footage > Main, or with
`AEK.xio.importFile(path, {alpha: "premultiplied"})` on reimport.
