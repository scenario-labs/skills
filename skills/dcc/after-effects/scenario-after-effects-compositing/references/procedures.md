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
6. Match levels per channel; 6b match the light (key direction, rim, levels against the plate)
7. Light wrap and grain
8. Cutout with no screen: external matte, Object Matte settings
9. Remove a logo from moving fabric: offset patch
10. Audit alpha interpretation

## 1. Inspect the plate

Use first on any keying shot. Pick a time where the screen is clean and the subject is busiest.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {aep, plate, sequence, fps, screenBox: [x, y, halfW, halfH] in layer pixels, t (seconds)}
// test session: a new project saved at ARGS.aep, at 16 bpc; in a person's project, drop this line and read the settings
AEK.core.fresh(ARGS.aep); app.project.bitsPerChannel = 16;
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

Stills cut from a movie: a PNG written by ffmpeg carries a gAMA chunk, which After Effects applies,
so the still renders darker than its pixels (a 6, 10, 18 border rendered 0, 1, 4). Strip it before
import: `magick in.png -define png:exclude-chunks=gAMA,cHRM,sRGB,iCCP out.png`.

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
// ARGS: {aep, plate, sequence, fps, screen: [r,g,b], garbage: [{t, points}], holdout: [{t, points}] or null,
//        soft: [clipBlack, clipWhite], core: [clipBlack, clipWhite], choke (px), out}
AEK.core.fresh(ARGS.aep); app.project.bitsPerChannel = 16;   // test session only (16 bpc for keys); end with AEK.core.save()
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

Blur the core's alpha for a softer transition without growing it: an unblurred duplicate of the core
is its Alpha track matte, so the blur can only fade the core inside its own edge (K-uOFPoIm6U
00:14:01 to 00:15:39). Blur the alpha channel only. The core is a keyed copy of the plate, color
included, so a Box Blur or Gaussian Blur softens the whole interior. The core here is a layer, not a
matte of a matte: its duplicate is the only matte.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, core (layer name, already keyed and choked), blur (px, no larger than the choke)}
var A = ARGS, c = AEK.core.comp(A.comp), core = AEK.core.layer(c, A.core);
// duplicate BEFORE the blur: the matte must keep the hard edge
var dup = core.duplicate(); dup.name = core.name + " inward matte_v001";
// Channel Blur -0004 = Alpha Blurriness; red, green and blue stay at 0, so the core's color stays sharp
AEK.build.effect(core, "ADBE Channel Blur", { "ADBE Channel Blur-0004": A.blur }, "inward alpha blur_v001");
return AEK.build.matte(core, dup, "alpha");
```

Check: on `alphaView`, no alpha outside the unblurred core edge; over gray, the high-pass of the
interior equals the unblurred core. Measured on a generated 1912x1084 plate at half size (choke 4,
blur 4): interior detail 8.37 (standard deviation of the high-pass, 0 to 255) unblurred, 8.37 with
Channel Blur on alpha, 0.45 with a Box Blur; 0 px of alpha outside the core with the matte, 6,063 px
without it. On a synthetic plate the Box Blur version spilled 33,070 px without its matte.

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
python3 $M holes alpha_f00024.png --erode 6                       # holes inside the eroded core, stray alpha outside
python3 $M rim key_over_black.png key_over_white.png              # edge color against the surface just inside: median 0.85 to 1.15
python3 skills/scenario-after-effects-expert/scripts/ae.py sheet sheet.jpg status_mid.png alpha_f00024.png final_f00024.png
```

Check: the numbers move the way the change intended; then read one sheet. A previous version of the
key is the reference when there is no truth matte. With no reference, `holes` replaces the body box:
it erodes the matte 6 px (alpha above 0.5) and counts pixels under 0.95 inside, so a moving subject
never puts the box across an edge. Measured on a 4:2:0 plate: 0.0 % holes, stray alpha at most
0.0005 % on frames 0, 48 and 95. `rim` derives alpha from the two versions and compares each edge
pixel's color with the surface 4 px inside. Measured on synthetic edges: clean 1.00, dark ring 0.50,
bright rim 1.61; a real key 1.07 median. Run it on the key alone: a rim light added later reads as a
bright edge by design.

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

The Silhouette Alpha blending mode is spelled `BlendingMode.SILHOUETE_ALPHA` in the API. Check:
`matteVisible` false (`setTrackMatte` switches the matte's video off and it stays off after
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
exact). A dark plate patch must be a real shadow of the plate, not a black border.

Picking the patches. The per-channel solve needs a neutral pair: a gray or white object and a shadow
in both layers. A sunset or colored plate has none. Measured on a sunset: a plate white sampled next
to the sun set Blue Output White to 0.77 and turned a navy strap teal. A colored element black (a
red shadow) gave a negative Red Output Black. With no neutral pair, solve on luma: one gain and one
offset for the three channels, from the subject's 1st and 99th luma percentiles to the plate's 1st
and its 99th near the subject (`matte_metrics.py light` prints all four). The element keeps its own
color; the light match (6b) handles the warmth.

## 6b. Match the light

Levels cannot move a light (vJ8X58uknsk 00:01:05). Measure it first, on the foreground alone
(rendered with its alpha, PNG RGBA) and the plate at the same frame:

```bash
python3 <skill>/scripts/matte_metrics.py light fg_alone.png plate.png --ring 6
```

It reports the plate's source: the brightest 0.5 %, its direction from the subject, its color, and
whether it is in frame. The subject's key direction comes from a plane fit of luma over its solid
core. `rim_facing` and `rim_away` compare edge pixels with the same surface just inside, on the half
toward and away from the source. Last come the rim hue against the source, and subject and plate
luma 1st and 99th percentiles.

Gate, when the source is in frame. These two readings separated the good composites from the bad
ones on every case below:

| Reading                   | Pass                                               |
| ------------------------- | -------------------------------------------------- |
| `key_strength`            | 0.3 or more (under it the subject is flat-lit)     |
| `rim_facing`, `rim_away`  | facing at least 1.15, and 0.1 above away           |
| subject luma p1 (levels)  | within 0.03 of plate p1                            |
| subject luma p99 (levels) | no more than 0.02 above plate p99 near the subject |

Readings to report and judge on the frame. `key_vs_source_deg` compares the subject's key with the
source direction. It means something on a front or side-lit subject whose far side has no dark part
(a strap, a dark cap). A backlit subject is lit mostly by its rim, and its key direction then points
elsewhere. `rim_hue_vs_source_deg` compares the rim color with the source color. A sun disc clipped
near white has no reliable hue, and a warm rim against it can read 18 degrees off while looking
right.

Measured, all over sunset or golden-hour plates with the sun in frame (the verdict is what the frame
shows):

| Composite                                | key_strength | rim facing / away | key vs source | rim hue | Frame                 |
| ---------------------------------------- | ------------ | ----------------- | ------------- | ------- | --------------------- |
| keyed speaker, front-lit, levels matched | 0.228        | 1.075 / 1.013     | 102.8         | 8.1     | pasted on             |
| same key, before light match             | 0.244        | 1.030 / 0.987     | 103.5         | 2.1     | pasted on             |
| same key after this procedure            | 0.332        | 1.176 / 1.017     | 45.4          | 4.1     | lit from the sun side |
| generated product, studio-lit            | 0.136        | 1.022 / 0.968     | 53.2          | 2.4     | pasted on             |
| studio-lit cutout seated on a terrace    | 0.140        | 1.017 / 0.980     | 79.4          | 5.7     | pasted on             |
| same view relit by an edit model         | 1.034        | 1.308 / 1.065     | 75.3          | 18.1    | seated                |

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS from `light`: angle = source_dir_deg, center = subject_center, radius = subject_radius, rimColor = source_rgb;
//   eb, ew = subject luma p1, p99; tb, tw = plate p1, plate near p99; shadeColor: the plate's shadow tint
var A = ARGS, c = AEK.core.comp(A.comp), fg = AEK.core.layer(c, A.fg), bg = AEK.core.layer(c, A.bg), i;
var g = (A.tw - A.tb) / (A.ew - A.eb), ob = A.tb - A.eb * g, base = [14, 21, 28];
var fx = AEK.build.effect(fg, "ADBE Pro Levels2", {}, "match levels_v001");
for (i = 0; i < 3; i++) {   // luma solve: one gain for the three channels
    fx.property("ADBE Pro Levels2-00" + base[i]).setValue(ob);
    fx.property("ADBE Pro Levels2-00" + (base[i] + 1)).setValue(ob + g);
}
var shade = AEX.comp.shadeLight(c, fg, { angle: A.angle, center: A.center, radius: A.radius, color: A.shadeColor, opacity: 100 });
// look the layer up again after each helper: they add layers and comps
var rim = AEX.comp.rimLight(c, AEK.core.layer(c, A.fg), { angle: A.angle, widthPx: 10, blurPx: 8, color: A.rimColor, opacity: 75 });
var wrap = AEX.comp.lightWrap(c, AEK.core.layer(c, A.fg), bg, { radiusPct: 1.0, opacity: 22, mode: "add" });
return { levels: [ob, ob + g], shade: shade, rim: rim, wrap: wrap };
```

`shadeLight` is a Gradient Ramp in Multiply clipped to the foreground's alpha: white on the source
side, `color` on the far side. `rimLight` builds a crescent: the foreground minus a copy shifted
away from the light by `widthPx`, blurred, clipped to the foreground, then a solid of `color` in
Screen. Both copy the layer with `copyToComp`, so a parented layer throws: precompose it first.
Measured, 1920x1080: angle -151.7 degrees, radius 345 px, rim 10 px wide with 8 px blur at 75 %.
Then re-run `light` on the lit foreground (light layers on, plate and grain off) and read the gates.

Some foregrounds cannot be relit this way: a hard key light on the wrong side, a strong cast shadow.
Then, in order: pick another plate whose source agrees with the subject's key, or regrade the plate
(flip it if nothing in it reads as mirrored). Add the rim alone, so the edge facing the source
glows. Flag what remains to the user with the `light` numbers.

## 7. Light wrap and grain

The wrap is built from track mattes (no plugin). `lightWrap` copies the foreground and background
layers into its source comp with `copyToComp`, so their scale, position, masks, effects and start
times carry. A parented layer makes it throw: precompose it first. Measured with a background scaled
160 % and moved: the old helper (it added the layer's source) wrapped pixels that differed from the
visible background by 37.6 levels on average; the fixed helper by 0.00.

Grain goes last, and only after both layers are measured. Read it two ways on the flattest static
patches of each layer (on a moving subject, `tgrain` reads motion: measured 10.9 levels on a moving
cap; read the plate on its screen or a static area):

- **Spatial:** `matte_metrics.py grain` (high-pass of one frame). It also counts texture and noise
  baked into a still.
- **Moving:** `matte_metrics.py tgrain A.png B.png` on two neighboring frames. A still background
  reads 0 here, whatever its spatial noise.

Then pick the route:

- **The plate carries real grain:** match grain only where an element replaced or covered the plate.
  Put Add Grain on the element layer itself (its alpha limits it), or use an adjustment layer with
  the element as Alpha or Luma track matte. Never over the whole frame: the plate keeps its own
  grain, and independent grain adds to it. Measured on a clean element over a grainy plate, with
  numpy grain at the plate's level (0.925 moving grain on untouched background). Over the whole
  frame: background 1.309 (+42 %), element 0.925. Masked by the element's alpha: background 0.925,
  element 0.924.
- **Both layers far cleaner than the grain you add** (generated plates often are): one shared Add
  Grain on a top adjustment layer over the composite. Measured on a generated plate over a generated
  still: moving grain 0.23 and 0 levels; grain on the background only gave 0.23 and 0.49 (inverted);
  one shared grain at intensity 0.5 gave 0.76 and 0.61.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp, intensity}; shared route: one grain over everything, the top layer of the comp
var c = AEK.core.comp(ARGS.comp), adj = AEK.build.adjustment(c, "FINISH_grain");
adj.moveToBeginning();
AEK.build.effect(adj, "VISINF Grain Implant", { "VISINF Grain Implant-0021": 3, "VISINF Grain Implant-0008": ARGS.intensity }, "shared grain");
return { top: c.layer(1).name };
```

Matching route:

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
`matte_metrics.py wrapbins wrap_on.png wrap_off.png plate.png alpha.png` bins the mean change on the
subject by blurred background luma (0 to 0.25, to 0.5, to 0.75, to 1). An Add wrap over a dark but
not black background is never 0: pass when the darkest bin is under half the brightest and nothing
changes outside the subject. Measured at 1.0 % and 22 %: 1.64, 2.54, 3.10, 5.37 levels. Alternative
grain: Match Grain, `VISINF Grain Duplication`, `-0013` = the plate's layer index (the plate may
stay hidden), `-0002` Viewing Mode 5 (Final Output); measured within 3 to 5 %; mode 3 added no
grain.

## 8. Cutout with no screen

Routes, by shot:

- **Object Matte (GUI):** toolbar Object Matte tool (the former Roto Brush slot), double-click the
  layer, click the product, Space, Freeze (gui-paths.md). A script then sets Feather, Shift Edge and
  Reduce Chatter by match name and pre-renders (8b).
- **Difference Matte:** locked-off camera with a clean plate, Effect > Keying > Difference Matte
  (K-uOFPoIm6U 00:30:48; keying doc).
- **External matte (unattended):** segmentation or layer separation through
  scenario-after-effects-generation, imported at the plate rate as a Luma or Alpha track matte (8a).
  Measured: it reproduced the reference matte exactly.
- **Rigid product:** a mask driven by a track from scenario-after-effects-tracking.

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

Routes:

- **GUI:** Subtract mask around the logo, Window > Content-Aware Fill, Fill Method Surface, Alpha
  Expansion, Lighting Correction when light shifts (Content-Aware Fill doc).
- **Hero frame:** clean one frame (paint, or an edit through scenario-after-effects-generation),
  track it in with a corner pin, add a masked Levels for lighting drift (3tMsr8TRDP8 00:01:02,
  00:06:07). The patch mask sits before the pin, so it lines up on the hero frame only: key it on
  other frames (00:05:31).
- **Scripted (below):** the plate itself as the patch.

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
