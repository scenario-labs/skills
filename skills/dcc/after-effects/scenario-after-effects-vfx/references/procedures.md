# Procedures

Agent procedures for built-in effects in After Effects 27.0. Every job is the body of a function for
`ae.py run job.jsx --lib <skill>/scripts/vfx.jsx`, uses the `AEK` kit and the `AEX.*` helpers, and
runs inside one undo step (`--undo "Agent: <what>"`). Paths come from `ARGS`. In a person's project,
drop `AEK.core.fresh()` and build inside their comp. Each procedure gives the goal, the steps, a
numbered gate and the trap that was hit while measuring it.

## 0. Match names (read live from `app.effects` and the property trees on 27.0)

Group headers inside CC effects (Producer, Physics, Particle) are flat entries in the effect:
address every property directly on the effect by its match name. Display names change with the
interface language and drift between versions; match names do not.

| Effect                       | Match name                 | Properties used here                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CC Particle World            | `CC Particle World`        | `-0004` Birth Rate, `-0005` Longevity (s), `-0007/8/9` Position X/Y/Z, `-0010/11/12` Radius X/Y/Z, `-0015` Animation (1 Explosive, 3 Cone Axis), `-0016` Velocity, `-0017` Inherit Velocity, `-0018` Gravity, `-0041` Resistance, `-0019` Extra, `-0020` Extra Angle, `-0095/96/97` Direction Axis X/Y/Z, `-0100/101/102` Gravity Vector X/Y/Z, `-0023` Particle Type, `-0045` Texture Layer, `-0024` Birth Size, `-0025` Death Size, `-0026` Size Variation, `-0027` Max Opacity, `-0028` Color Map (2 Birth to Death, 1 Custom), `-0029` Birth Color, `-0030` Death Color, `-0074` to `-0078` custom color stops, `-0039` Transfer Mode (1 Composite, 2 Screen, 3 Add, 4 Black Alpha), `-0104` Random Seed; guides `-0051` `-0052` `-0053` `-0055` `-0060` `-0061` |
| CC Particle Systems II       | `CC Particle Systems II`   | `-0001` Birth Rate, `-0002` Longevity, `-0004` Position (pixels), `-0010` Velocity, `-0012` Gravity, `-0018` Particle Type, `-0019` Birth Size, `-0020` Death Size                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| CC Toner                     | `CC Toner`                 | `-0005` Tones (3 Pentone), `-0003` Shadows, `-0007` Darktones, `-0002` Midtones, `-0006` Brights, `-0001` Highlights                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Gaussian Blur                | `ADBE Gaussian Blur 2`     | `-0001` Blurriness, `-0002` Blur Dimensions (1 both, 2 horizontal, 3 vertical), `-0003` Repeat Edge Pixels                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Exposure                     | `ADBE Exposure2`           | `-0003` Exposure (stops), `-0004` Offset, `-0005` Gamma, `-0022` Bypass Linear Light Conversion                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Solid Composite              | `ADBE Solid Composite`     | `-0001` Source Opacity, `-0002` Color (default white), `-0003` Opacity, `-0004` Blending Mode                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Glow                         | `ADBE Glo2`                | `-0002` Threshold (0 to 255), `-0003` Radius, `-0004` Intensity, `-0005` Composite Original, `-0006` Operation, `-0007` Colors                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Tint                         | `ADBE Tint`                | `-0001` Map Black To, `-0002` Map White To, `-0003` Amount                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Levels (Individual Controls) | `ADBE Easy Levels2`        | `-0003` Input Black, `-0004` Input White (reads 1 at 16 bpc), `-0005` Gamma, `-0007` Output White                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Fractal Noise                | `ADBE Fractal Noise`       | `-0001` Fractal Type, `-0002` Noise Type, `-0004` Contrast, `-0005` Brightness, `-0009` Uniform Scaling, `-0010` Scale, `-0011` Scale Width, `-0012` Scale Height, `-0013` Offset Turbulence, `-0015` Complexity, `-0017` Sub Influence, `-0018` Sub Scaling, `-0023` Evolution, `-0025` Cycle Evolution, `-0026` Cycle (revolutions), `-0027` Random Seed                                                                                                                                                                                                                                                                                                                                                                                                           |
| Turbulent Noise              | `ADBE AIF Perlin Noise 3D` | `-0020` Evolution, `-0022` Turbulence Factor; no Cycle Evolution                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Curl Noise (26.3)            | `ADBE Curl Noise`          | `-1017` Evolution, `-1018` Turbulence Speed, `-1019` Swirl, `-1025` Sample Count, `-1026` Sample Radius                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Turbulent Displace           | `ADBE Turbulent Displace`  | `-0002` Amount, `-0003` Size, `-0005` Complexity, `-0006` Evolution, `-0008` Cycle Evolution, `-0009` Cycle, `-0010` Random Seed, `-0012` Pinning                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Displacement Map             | `ADBE Displacement Map`    | `-0001` Map Layer, `-0002` Use For Horizontal (1 Red, 2 Green, 5 Luminance), `-0003` Max Horizontal, `-0004` Use For Vertical, `-0005` Max Vertical, `-0006` Behavior (1 Center Map), `-0007` Wrap Pixels Around, `-0008` Expand Output                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Polar Coordinates            | `ADBE Polar Coordinates`   | `-0001` Interpolation (0 to 1), `-0002` Type of Conversion (1 Rect to Polar, 2 Polar to Rect, default 2)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Offset                       | `ADBE Offset`              | `-0001` Shift Center To                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Advanced Lightning           | `ADBE Lightning 2`         | `-0001` Type (2 Strike), `-0002` Origin, `-0003` Direction, `-0004` Conductivity State, `-0006` Core Radius, `-0007` Core Opacity (0 to 100), `-0008` Core Color, `-0011` Glow Radius, `-0012` Glow Opacity (0 to 100), `-0016` Turbulence, `-0017` Forking (0 to 1), `-0022` Complexity, `-0024` Termination Threshold                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| CC Light Rays                | `CC Light Rays`            | `-0001` Intensity, `-0002` Center, `-0003` Radius, `-0004` Warp Softness                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| CC Radial Fast Blur          | `CC Radial Fast Blur`      | `-0001` Center, `-0002` Amount, `-0003` Zoom (2 Brightest)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Optics Compensation          | `ADBE Optics Compensation` | `-0001` Field Of View, `-0002` Reverse Lens Distortion                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Shift Channels               | `ADBE Shift Channels`      | `-0002/3/4` Take Red/Green/Blue From (2 Red, 3 Green, 4 Blue, 10 Full Off; 11 throws)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| CC Vignette                  | `CS Vignette`              | `-0001` Amount, `-0002` Angle of View, `-0003` Center                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Channel Mixer                | `ADBE CHANNEL MIXER`       | `-0001` Red-Red, `-0006` Green-Green, `-0011` Blue-Blue                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Add Grain                    | `VISINF Grain Implant`     | `-0021` Viewing Mode (3 Final Output), `-0008` Intensity, `-0007` Size, `-0005` Monochromatic                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Noise                        | `ADBE Noise`               | `-0001` Amount of Noise, `-0002` Noise Type (0 mono), `-0003` Clipping (keep 1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Camera Lens Blur             | `ADBE Camera Lens Blur`    | `-0001` Blur Radius                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| CC Vector Blur               | `CC Vector Blur`           | `-0002` Amount                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Fast Box Blur                | `ADBE Box Blur2`           | `-0001` Blur Radius, `-0002` Iterations, `-0003` Dimensions (3 vertical)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Gradient Ramp                | `ADBE Ramp`                | `-0001` Start, `-0002` Start Color, `-0003` End, `-0004` End Color, `-0005` Shape                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Gradient Wipe                | `ADBE Gradient Wipe`       | `-0001` Transition Completion (0 to 1), `-0002` Transition Softness (0 to 1), `-0003` Gradient Layer                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Echo                         | `ADBE Echo`                | `-0001` Echo Time (s), `-0002` Number Of Echoes, `-0003` Starting Intensity, `-0004` Decay, `-0005` Echo Operator                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Timewarp                     | `ADBE Timewarp`            | `-0003` Speed, `-0024` Enable Motion Blur, `-0025` Shutter Control, `-0026` Shutter Angle                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Slider Control               | `ADBE Slider Control`      | `-0001` Slider                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Others                       |                            | Posterize Time `ADBE Posterize Time`, CC Wide Time `CC Wide Time`, CC Snowfall `CSSnowfall`, Unmult (26.0) `ADBE Unmult`, Radial Blur `ADBE Radial Blur`, CC Force Motion Blur `CC Force Motion Blur`, Match Grain `VISINF Grain Duplication`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

Popup properties take numbers; `prop.maxValue` gives the item count (separators count).

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Dump every property of an effect (match name, display name, value) before scripting it
var c = AEK.build.comp("probe", { width: 960, height: 540, fps: 24, duration: 1 });
var s = AEK.build.solid(c, "s", [1, 1, 1]);
var fx = s.property("ADBE Effect Parade").addProperty(ARGS.matchName), out = [], i, p, v;
for (i = 1; i <= fx.numProperties; i++) {
    p = fx.property(i); v = null;
    if (p.propertyType !== PropertyType.PROPERTY) { continue; }
    try { if (p.propertyValueType !== PropertyValueType.NO_VALUE && p.propertyValueType !== PropertyValueType.CUSTOM_VALUE) { v = p.value; } } catch (e) {}
    out.push(p.matchName + " | " + p.name + " = " + String(v) + (p.hasMax ? " (max " + p.maxValue + ")" : ""));
}
return out;
```

Trap: `canAddProperty()` returns true even for an invented match name; only `addProperty()` throws.
Wrap it in try.

## 1. Bit depth

**Goal:** the same light on every renderer, with light added in predictable amounts.

Steps: `AEX.vfx.depth(16)`. It switches an OCIO project to Adobe color management (OCIO accepts 32
bpc only). In a person's OCIO project call `depth(32)` and redo every amount in this file by eye.

Why 16 and not 32: the total light after one Glow on a disc at 1.0 depends on the depth.

| Depth                 | Total light after one Glow (source 1x)          |
| --------------------- | ----------------------------------------------- |
| 16 bpc                | 1.1 to 1.4 x the source, whatever the threshold |
| 32 bpc, threshold 0   | x5 / x9.1 / x15.4 at intensity 0.25 / 0.5 / 1   |
| 32 bpc, threshold 153 | x1.9 to x4.7                                    |
| 32 bpc, threshold 230 | x1.3 to x2.3                                    |

So Glow settings tuned at 16 bpc do not carry to 32, and the reverse. The three-Glow stack clipped
4.1 % of the frame at 16 bpc and 64 % at 32 bpc. At 32 bpc CC Toner turned the core cyan on the
software renderer and drew dark rectangles on the GPU. At 8 bpc a ramp banded on the software
renderer (22 levels) and kept 83 levels on the GPU.

**GATE 1:** `{bpc: 16}` returned (32 in OCIO). Trap: `AEK.core.fresh()` resets to 8 bpc; at 32 bpc
`saveFrameToPng` writes values divided by 10 (read with `ae.py sheet ... --gain 10`). Advanced
Lightning renders 8 bpc internally (Adobe doc); its light still goes through the rig at 16.

## 2. Highlight control and glow: the light rig

**Goal:** a hot core that never burns to a flat blob, a colored falloff, light that adds in known
amounts.

Steps:

1. `AEX.light.rig(comp, name, o)` builds `<name>_light` (put gray light here), `<name>_sum` (black,
   the light in Add, the bloom copies) and a layer `<name>` in the comp carrying the map.
2. Make each element white or gray, put it in `<name>_light`, and set its level with
   `AEX.light.add(layer, lum)`: an Exposure with Bypass Linear Light Conversion (`-0022` = 1), which
   is an exact multiply at every depth (gain 0.5 at -1 stop read 0.2500). Stops = log2(gain). Levels
   that worked: rings and strokes 0.35 to 0.5, sparks 0.5 to 1, flame body 0.85.
3. Bloom: Gaussian Blur copies at doubling radii, each with Solid Composite black, Gaussian (`-0003`
   0), Exposure gain, Add. Gaussian Blur keeps energy: the light added is exactly sum(weights) x the
   source. Defaults (`AEX.glow.DEFAULTS`): r0 12 px, 5 copies (12, 24, 48, 96, 192), total 2.0, each
   0.75 x the previous (gains 0.66, 0.50, 0.37, 0.28, 0.21). Total 0.6 reads as no glow; 3.0 pushes
   thin strokes to the top tone. r0 24 gives a softer, bigger look.
4. Color once: CC Toner, Pentone (`-0005` 3), maps luminance 0, 0.25, 0.5, 0.75, 1 to shadow, dark,
   mid, bright, high. At 16 bpc the sum is clamped at 1.0 before the map, so the core lands on the
   high tone and stops.
5. Over the plate: rig layer in Screen. Add only over near-black.

Default tones (`AEX.light.TONES`): black, `#43150D`, `#E0452C`, `#FF8A5C`, `#F1E9D8`. For another
palette: dark = mid x 0.3 in the mid's hue (a navy dark tone under a coral mid turned dim sparks
lavender); top tone with no channel at 1.0 (see `AEX.bolt.ELECTRIC`, `AEX.rays.DAY`).

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// A ring of grey light in a rig: Gaussian bloom, CC Toner map, Screen over the plate
var c = AEK.core.comp(ARGS.comp);
AEX.vfx.depth(16);
var r = AEX.light.rig(c, "ENERGY", { bloom: AEX.glow.plan({ r0: 12, n: 5, total: 2.0, k: 0.75 }), tones: AEX.light.TONES });
var ring = AEK.build.shape(r.light, "RING", { name: "e", type: "ellipse", size: [500, 500], stroke: { color: [1, 1, 1], width: 8 } }, { position: [c.width / 2, c.height / 2] });
AEX.light.add(ring, 0.45);
r.layer.blendingMode = BlendingMode.SCREEN;
return AEX.vfx.cost(c, [0.5, 1, 1.5], ARGS.out, "rig");
```

**GATE 2:** 0 pixels at 255 in all three channels on 8 frames; the GPU frame and the software frame
identical; the core reads the high tone with the mid tone around it. Visual: the core has a radial
falloff (bright center, then the mid tone, then the dark tone) and is the brightest thing in frame.

Traps hit:

- A cap before the Glows fails: Glow adds its own light on top of the cap.
- HDR Highlight Compression gave different frames on GPU and software (over-range turned 0.75 gray
  on GPU).
- Exposure plus gamma as a roll-off gives neutral gray (saturation 0): color must come after the
  sum.
- Glow's tail is black by 200 px; Gaussian copies still carry light at 200 to 300 px.
- Fast Box Blur copies lose light outside the shape layer's bounds: use Gaussian.
- A linear working space spreads low light about 2.7x (frame mean luma 30 to 82): lower the wide
  bloom weights about 3x.
- Over a lit plate the rig in Add clipped up to 36,550 px; in Screen 0 on every frame of every
  construction.
- A comp name can be used once: a second `AEX.light.rig` with the same name throws.
- `AEX.glow.copies` clears the effects on its copies, so content drawn by an effect (CC Particle
  World sparks) does not bloom: 1,096 lit px against 13,803 with `keepEffects: true`.
  `AEX.glow.stack` says so in `warnings`; pass `keepEffects` or precompose.

## 3. Particle units and counts

**Goal:** set particles from on-screen targets (count, px, px/s), then read the effect values off a
formula.

CC Particle World, measured on a 1920 layer with the default Effect Camera, Explosive:

| Quantity               | Rule                                                                                                                                                                                                                                                                                                              |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Producer Position X, Y | 1 unit = the layer WIDTH on both axes, 0 = layer center                                                                                                                                                                                                                                                           |
| Alive particles        | 110 x Birth Rate x Longevity, at 24, 30, 60 fps and any layer size                                                                                                                                                                                                                                                |
| Burst held N frames    | about 4.4 x Birth Rate per frame at 30 fps: rate = count x fps / (132 x N)                                                                                                                                                                                                                                        |
| Diameter               | Birth Size x width x 0.075 px on screen (`AEX.pn.K.diamPerWidth`, used by `AEX.pn.sparks`; width / 10 overstates it 1.33x). `AEX.burst.plane`, `AEX.atmo.plane` and `AEX.smoke.embers` size with `K.sizePerWidth` 0.1, the constant their looks were tuned on: their px values are nominal, about 0.75x on screen |
| Speed                  | 0.58 x width x Velocity px/s at the burst edge (p95); median 0.62 of that                                                                                                                                                                                                                                         |
| Gravity                | 3.2 x width x Gravity px/s² with Resistance 0                                                                                                                                                                                                                                                                     |
| Resistance R           | speed decays exp(-0.7 R t); stop distance = speed / (0.7 R)                                                                                                                                                                                                                                                       |
| Resistance 10          | near constant fall of about 0.23 x Gravity x width px/s                                                                                                                                                                                                                                                           |

Smallest visible Birth Size on a 1920 layer (peak at least 0.15 on 90 % of particles):

| Particle Type   | Smallest Birth Size                          |
| --------------- | -------------------------------------------- |
| 2 Star          | 0.004                                        |
| 4, 5, 6 spheres | 0.015 (2.2 px); 0.02 for a peak above 0.6    |
| 7 Ring          | 0.03                                         |
| 11, 12, 16      | never vanish                                 |
| 1 Line          | ignores size, draws the motion of each frame |

Transfer Mode: 1 Composite keeps color at any density. 2 Screen turns neutral from about 150
particles per 100x100 px, 3 Add from about 50, whatever Max Opacity.

CC Particle Systems II: count about 2.4 x Birth Rate x Longevity; diameter about 130 x Birth Size
px; gravity about 2,100 x Gravity px/s². A rate held on frame 0 only emits nothing: start bursts on
frame 1.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// 400 sparks over 3 frames from 1 s, 6 px shrinking to 3, 900 px/s stopping in 300 px, falling 400 px/s²
var c = AEK.core.comp(ARGS.comp), s = AEK.build.solid(c, "SPARKS", [0, 0, 0]);
var r = AEX.pn.sparks(s, { count: 400, burstFrames: 3, at: 1, life: 1.2, diameter: 6, deathDiameter: 3, speed: 900, stop: 300, fall: 400,
    type: 5, color: [1, 0.9, 0.75], deathColor: [0.9, 0.35, 0.15], transfer: 1 });
return r;   // {birthRate, velocity, resistance, gravity, birthSize, deathSize, warnings}
```

**GATE 3:** `warnings` empty; a counted frame within 15 % of the target count; diameters measured
within 1 px. Traps: sparks vanish mid-life when Death Size falls below the table minimum; Extra does
nothing in Explosive; Birth Rate below 0.05 can emit nothing for seconds (`AEX.pn.sparks` warns: 2
motes over 7 s gave 0.0026); comp motion blur applies to CC Particle World (light x3.7) only when
the switch is on the particle layer itself; with the particles two or more comps deep it needs the
switch on every comp in the chain and on every nested comp layer. Cone Axis (Animation 3) emits on a
cone SHELL at Extra Angle from the Direction Axis (Y is screen-down positive): keep Extra Angle
between 15 and 70 degrees; above 90 the burst goes backwards.

### Follow a moving layer

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Particles shed by a moving null "HAND"; producer wired by expression (units = layer widths)
var c = AEK.core.comp(ARGS.comp);
var sp = AEK.build.solid(c, "SPARKS", [0, 0, 0]);
var fx = AEX.vfx.pw(sp, { birthRate: 14, longevity: 0.7, velocity: 0.08, gravity: 0.05, rx: 0.003, ry: 0.003, rz: 0.003,
    type: 5, birthSize: 0.03, deathSize: 0.02, sizeVar: 40, maxOpacity: 100, birthColor: [1, 0.9, 0.7], deathColor: [1, 0.35, 0.1], transfer: 1 }, "PW sparks");
AEX.vfx.follow(fx, "HAND");
var px = AEX.vfx.pwProp(fx, "x");
return { x: px.valueAtTime(1, false), error: px.expressionError };
```

The expression `AEX.vfx.follow` writes:

```javascript
// expression (JavaScript engine): Solid > Effects > CC Particle World > Producer > Position X
// checked: live 27.0
var L = thisComp.layer("HAND");
var p = fromComp(L.toComp(L.anchorPoint));
(p[0] - width / 2) / width;
// Position Y: (p[1] - height / 2) / width;   (divide by width, not height)
```

Check: at 1 s the null sat at (467.9, 223.0) and the producer read X -0.0126, Y -0.0490, which is
(467.9 - 480) / 960 and (223.0 - 270) / 960. Particle Type values: 1 line, 2 star, 4 hard sphere, 5
Faded Sphere, 6 darker soft dot, 7 ring, 11 triangles, 12 quads, 16 cubes, 18 to 22 lens types (they
refract the host layer: black on a black solid). With a comp camera present the particles render
through it and the Effect Camera settings change nothing.

## 4. Energy burst with direction

**Goal:** a hit that leaves a point in one direction: a small hot point that flashes for two frames,
a fan of fine streaks of uneven length thrown one way, a few sparks with trails, a decay over about
1.5 s.

The body is procedural streaks; particles are the accent only (30 to 150 on screen). A burst made of
particles alone read as a firework over a ball of sand.

Steps (`AEX.burst.build(host, o)`, all gray light in one `AEX.light` rig, bloom radii 10 to 320 with
total 1.0):

1. **Streaks** (`AEX.burst.streaks`). In a square comp of side D = 2 x 700 x scale: two Fractal
   Noise column layers with Uniform Scaling off (thin: Scale Width 2.2, Height 260, contrast 420,
   brightness -95; wide: 9 x 900, contrast 330, brightness -75 at 75 % in Add), offset scrolled
   outward with an eased deceleration.
2. Multiply an angle comp: an omni floor of 0.08 plus a feathered column 0.32 D wide at x = D / 2.
   That column becomes the cone; the layer is rotated `dir - 90`.
3. Multiply a front comp: a tail-to-head ramp, a cut just ahead of the head, a fixed rim fade from
   0.6 D to 0.92 D (no streak ends on the comp edge).
4. In the polar comp: Displacement Map, vertical only, 0.2 x D, from a column-noise precomp (Scale
   Height 10,000: ragged lengths); then Polar Coordinates Rect to Polar (the TOP row goes to the
   center, the bottom row to the rim at half the width; x runs counterclockwise from 12 o'clock);
   then CC Radial Fast Blur 30.
5. **Core** (`AEX.burst.core`): three radial Gradient Ramp cones, 34 / 110 / 320 px at light 1.05 /
   0.30 / 0.07 x energy, scale 35 to 125 to 70 %, opacity on the hit envelope (attack 2 frames,
   hold, decay).
6. **Accent** (`AEX.burst.sparks`): leaders (14, 2,600 px/s, stop 900 px, cone 18 degrees), body
   (55, 1,100 px/s, 6 px, size variation 85, cone 40), arcs (12, gravity 520 px/s², cone 55), far
   (24 tiny hard spheres, 55 %), linger (16 slow, rising, flickering), near (3 discs 70 to 110 px,
   Camera Lens Blur 26, 10 %). Composite inside, white to gray over life. Speed tiers still apply
   here: one speed draws a hollow shell. Line type carries far more light per Birth Rate unit (99 %
   of the burst's light at the same rate): scale its rate by 0.1 if you use it.
7. **Trails:** Echo on the sparks precomp layer, FIRST in its effect stack, Maximum operator
   (`-0005` 2: a bright head and a fading tail without stacking), step 1/120 s x 16, decay 0.89. A
   1/60 s step leaves beads at 1,100 px/s. Echo costs 2 to 5 times the frame.
8. **Air** (`AEX.burst.airGlow`): Fractal Noise haze in the light comp through a 460 px radial luma
   matte, light 0.14, on the envelope.
9. **Motion blur:** on every comp in the chain (sparks, light, sum, host) and on every nested comp
   layer; shutter 270 in the sparks comp.
10. **Budget the center.** At the attack the core, the converging streaks, the flash and the sparks
    all sum at one point. Plan their levels together so the sum at the center stays near 1.0, and
    put the rig in Screen over a lit plate (in Add, the map's cream top plus a navy plate overflows
    to pure white).

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// An energy hit aimed up-right at 0.2 s, rig in Screen over the plate
var c = AEK.core.comp(ARGS.comp);
var r = AEX.burst.build(c, { name: "HIT", center: [820, 620], dir: -28, scale: 1, energy: 1, seed: 4, at: 0.2, trail: "echo" });
c.layer(r.layer).blendingMode = BlendingMode.SCREEN;
return { hit: r, frames: AEX.vfx.cost(c, [0.233, 0.3, 0.4, 0.533, 1.4, 2.1], ARGS.out, "hit") };
```

**GATE 4:** pixels at 255 in all channels under 1 % on every frame (0.18 to 0.30 % on the first
three frames after the hit, 0 from +25); light-weighted direction within 15 degrees of `dir` at +3
frames; mean change per frame positive on every frame of the first 12 (no dead or repeated frame).
Visual: **no flat disc at the attack**: the core shows a falloff (bright center, then hot coral,
then coral) on the first three frames; streaks of uneven length with heads brighter than tails;
sparks read as a few accents.

Traps hit:

- The attack frames showed a flat cream-to-white disc about 70 px wide: the core plus converging
  streaks plus sparks summed past 1.0. Do instead: lower the tight cone at the attack, or subtract a
  small radial hole from the streak comp so their convergence does not stack on the core, and Screen
  the rig.
- An omni floor of 0.28 gave a sea urchin; air light 0.32 over 620 px with a wide core cone washed
  the area in a flat pink cloud. Floor 0.08, air 0.14 over 460 px, wide cone 0.07, bloom total 1.0.
- A perfectly round front and streaks ending on the square comp edge: fixed by the column-noise
  displacement and the fixed rim fade.
- Cone Axis at 120 to 200 degrees threw a burst aimed right to the left.
- CC Time Blend gave no trails in frames rendered one by one by script (the same frame whatever the
  render order): it cannot be checked or delivered that way. CC Wide Time gave a faint smear with no
  head-to-tail falloff. CC Light Burst 2.5 on a noisy disc gave a spiky star around the core with no
  reach.
- `ADBE Rotation` returns null on a 2D layer: use `ADBE Rotate Z`. Fractal Noise Scale Height
  refuses values over 10,000.
- Render: 2 to 6 s per frame at 1080p for the full graph; Echo plus motion blur four comps deep is
  the cost.

### Particle-only burst (inside another rig)

`AEX.burst.planes(host, o)` keeps the particle-only build: far plane, three follower speed tiers (1,
0.6, 0.35 of the top speed; Cone Axis at 40 and 70 degrees), Line leaders at rate x 0.1, embers,
near bokeh, a 4-frame flash at most 26 % on a feathered disc whose solid is larger than its feather.
Everything Composite inside, the precomp in Add once with a blurred copy at about 30 % (0 inside a
light rig). It is the burst `AEX.integrate` lights the plate with. Measured: under 0.2 % clipped on
the peak frame.

## 5. Embers and dust, with the loop

**Goal:** sparse floating particles in three depths that loop exactly, with an empty zone for a
title.

Steps (`AEX.atmo.build(host, o)`):

1. Planes far, mid, near for embers (3.4, 6.5, 30 px) and dust (2.4, 4.5, 22 px); counts from the
   alive-particle rule (section 3); near planes blurred.
2. Custom color map from black to black (`-0028` 1, stops `-0074` to `-0078`): each particle fades
   in and out by itself. Transfer Mode 3 Add is safe while density stays under 50 per 100x100 px.
3. Turbulent Displace for drift. It dims small dots: 2.4 px lose 40 %, 4 px lose 9 %.
4. Flicker `a + b * noise()` averages `a`: keep `a` near 85.
5. Loop: the simulation comp is P + L long. Copy A starts at -P; copy B starts at L - P and shows
   over the last F seconds; A fades out and B in. Frame L equals frame 0 exactly.
6. Title zone: an alpha matte (white solid with a Subtract ellipse at 1 - `titleDensity`, 70 % by
   default) gives 2.5 to 8x fewer visible particles there; it dims more than it removes. For a
   cleaner zone lower `titleDensity`.
7. Dust only inside a light beam: luma-matte the dust to the beam shape; put the visible beam in the
   host so the title hole does not cut it.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// 4 s looping embers and dust, dust only in a beam, a hole for the title
var c = AEK.core.comp(ARGS.comp);
var r = AEX.atmo.build(c, { name: "ATMO", L: 4, P: 4, F: 1, embers: 1, dust: 1, beam: [1300, 260, 900, 900], beamOpacity: 16,
    warm: 0.8, title: [960, 500, 520, 160], titleDensity: 0.3, glow: 70, seed: 2 });
return { atmo: r, frames: AEX.vfx.cost(c, [0, 2, 4], ARGS.out, "atmo") };
```

**GATE 5:** frame L against frame 0 differs by 0; visible particles (peak above 0.06) inside the
title ellipse at least 2.5x fewer than outside per area at `titleDensity` 0.3 (2.5 to 8x by layout);
lower `titleDensity` for more. Visual: a few near embers clearly larger and brighter than the far
field.

Trap: the faint version read as nothing (dust lost in the beam). Do instead: raise the near plane,
keep the far field dim, and judge the frame at viewing size.

## 6. Smoke

**Goal:** procedural smoke lit from one side that loops.

Steps (`AEX.smoke.build(host, o)`):

1. Density precomp: two Fractal Noise scales (900 and 260 px), Turbulent Displace, CC Vector Blur 6
   to 12, Fast Box Blur 5 to 7, radial matte.
2. Every noise uses Cycle Evolution with whole revolutions over the same L (`AEX.vfx.loopNoise`):
   the loop is exact.
3. Body: density multiplied first by a ramp from 1 on the light side to `shade` (0.3) on the far
   side (`<name>_SHADED` precomp), tinted warm gray, Screen, about 75 %.
4. Light pass: a ramp from the light side through the density as luma matte, Add, about 55 %.
5. Lit edge: density minus itself shifted 20 to 30 px toward the light (Subtract), Box Blur 5,
   Exposure +2.4 stops, tinted, Add.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var r = AEX.smoke.build(c, { name: "SMOKE", L: 4, center: [960, 600], size: [520, 380], light: [1, -0.3], edge: 30, edgeGain: 2.4, wisp: 8, seed: 4 });
return { smoke: r, frames: AEX.vfx.cost(c, [0, 2, 4], ARGS.out, "smoke") };
```

**GATE 6:** frame L against frame 0 differs by 0; mean luma on the lit side at least 1.15x the far
side (1.17 to 1.39 with `shade` 0.3 across seeds and frames; 1.01 to 1.29 without the shading). For
a stronger side light lower `shade` (0.2 gave 1.20 to 1.34 on four seeds) and pick the seed: the
ratio moves per seed. Traps: without the shaded body one seed gave 0.95 (no visible side light). CC
Vector Blur above about 12 combs smoke into hair.

## 7. Flame

**Goal:** a small flame standing on a point: a dense foot, three or four tongues licking upward and
tearing off, cream only in the foot, coral body, ember-red tips, rising embers, heat haze above, a
seamless loop.

Steps (`AEX.smoke.flame(host, o)`, gray light in an `AEX.light` rig with bloom radii 6 to 96, total
0.45, and the FIRE map: black, `#5A160C`, `#E0452C`, `#FF8A5C`, `#F1E9D8`):

1. **Noise** (`AEX.smoke.flameNoise`): two Fractal Noise layers, Basic, Invert on, contrast 140,
   brightness -15, Uniform Scaling off (70 x 150 and 28 x 70 px), offset scrolled upward at 240 and
   408 px/s (parallax), evolution `time * 140` and `time * 260`, the fine one Add at 55 %.
2. **Density:** the noise, Screen a vertical ramp at 45 % (noise x (1 - ramp) + ramp: a solid foot,
   a noise-eaten top), Multiply a shape comp: an opaque black ground, a body ellipse low and wide, a
   narrower softer plume above it in Screen at 75 %, a taper ramp to 1.2 x the height. A Multiply
   layer over transparency composites as itself: the shape comp needs the opaque ground.
3. **Flame comp:** Turbulent Displace "Licks" (amount 22, size 55, complexity 2, 3 revolutions per
   loop) and "Sway" (16, 260, 1 revolution); Levels as a soft threshold (Input Black 0.28, Input
   White 0.72); CC Radial Fast Blur 22 centered 2,200 px below the flame (a one-direction smear
   upward); Fast Box Blur 1.
4. **Heat ramp** in Multiply, 1.0 at the foot to 0.42 at the top, BEFORE the luminance map: the
   hottest tone stays at the foot (78 % of the cream pixels then sit in the lower 40 % of the
   flame).
5. **Light:** the flame at 0.8; a radial pool of light 0.06 around the foot, flicker 92 + 8 x noise.
6. **Embers** (`AEX.smoke.embers`): three planes (far 14 on screen at 4.5 px, mid 10 at 8 px
   shrinking to 4.5, near 3 at 16 px with Camera Lens Blur 6), emitted from the body, rising by
   negative gravity 230 to 380 px/s² against Resistance 1.6 to 2.2 (terminal speed about 150 to 340
   px/s), Turbulent Displace drift 34 / 170, flicker 80 + 20 x noise, light 1.1.
7. **Loop:** upward-scrolling noise does not loop by Cycle Evolution. Every moving source (noise,
   embers, heat map) lives in a comp P + L long; copy A starts at -P, copy B at L - P and fades in
   over the last 0.8 s (Add for light, B over A for opaque maps; linear opacity keys, it is a mix).
8. **Heat haze** (`AEX.smoke.heat`): `AEX.distort.hazeMap` (noise scale 90, rising 160 px/s) in a
   feathered band from 260 px above the flame top down to its lower quarter, read by a Displacement
   Map adjustment layer at the TOP of the host, 0.08 x 90 = 7.2 px: it bends the tips, the embers
   and the plate haze together.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// A 380 px flame looping over 4 s, embers and heat haze, rig in Screen over the plate
var c = AEK.core.comp(ARGS.comp);
var r = AEX.smoke.flame(c, { name: "FLAME", base: [960, 860], height: 380, width: 150, scale: 1, seed: 6, L: 4, F: 0.8 });
c.layer(r.layer).blendingMode = BlendingMode.SCREEN;
return { flame: r, frames: AEX.vfx.cost(c, [0, 1, 2, 3, 4], ARGS.out, "flame") };
```

**GATE 7:** frame L against frame 0: 0 levels (the pool flicker loops over L, a `noise` on a circle
of period L); pixels at 255 in all channels under 0.5 %; separate tongues above the foot on 3
frames; motion per frame even over a 12-frame strip (0.22 to 0.27 levels, no stall, no jump).
Visual: **cream only as a thin core at the foot**: at most about 15 % of the flame's area at the top
tone, with coral around it. At 35.6 % of the flame at cream or white, the lower half reads as a soft
white egg with coral edges. Do instead: a heat ramp that peaks at 0.9 instead of 1.0, a tighter
second Levels masked to the lower third, and the rig in Screen.

Traps hit:

- Base fill, threshold window and gain are coupled: base fill 70 % with threshold 0.26 to 0.80 and
  gain 1.0 gave a flat cream egg; 25 % with 0.32 to 0.64 gave holes and rings in the body; 45 % with
  0.28 to 0.72 and gain 0.8 holds.
- CC Vector Blur with Direction Fading and a flat black map (the usual one-direction blur) changed
  nothing visible: CC Radial Fast Blur centered far below the flame does the job.
- Fractal Type 5 at contrast 140 ate the flame down to a small blob; Basic with Invert kept the
  tongues.
- Render: 0.2 to 0.6 s per frame at 1080p, embers and heat included.

## 8. Shockwave ring

**Goal:** an expanding ring that decelerates, keeps a hot edge with a soft wake, and bends the
plate.

Timing (`AEX.shock.DEFAULTS`): radius eases out with power 3 from 10 to 1150 px over 1 s (half the
distance in 21 % of the time); opacity fades with u² to 25 %.

Three ring builds (all go into a light rig):

1. `polar`: a Fractal Noise band in a SQUARE precomp of side S, through Polar Coordinates Rect to
   Polar. Row y lands at radius y / 2, so a ring leaving 1920x1080 needs S at least 2 x (r1 +
   thickness): 2,204 minimum, 2,400 used. A 16:9 precomp caps the radius at H / 2.
2. `stroke`: a hot edge stroke plus a wake of 6 overlapping strokes, each 2.5 % of r wide, each 0.7x
   fainter inward, blurred by 0.6 x a step. Thin separate strokes read as concentric lines.
3. `ring`: a thin edge plus Fractal Noise wisps (contrast 220, brightness -45, level 0.5) inside a
   wide soft stroke, Turbulent Displace over both. Fractal type 6 gave stripes.

Refraction: two Displacement Maps (`-0002`/`-0004` 5 luminance) on an adjustment layer over the
plate, Wrap Pixels Around (`-0007`) on; the map comps carry the same Turbulent Displace as the
wisps.

Seam fix for `polar`: an ADJUSTMENT layer inside the band comp with Offset (half the width) and two
feathered edge masks; or put the displacement and blur after Polar.

Motion blur on a ring moving about 100 px per frame:

| Shutter | Edge peak kept                                    |
| ------- | ------------------------------------------------- |
| 180     | half                                              |
| 90      | 70 to 96 %                                        |
| 360     | the ring smears into a disc on the first 3 frames |

Use 90 degrees, and `AEX.shock.mbSplit(layer, comp, 2)` to keep the first 2 frames sharp (the motion
blur switch cannot be keyed).

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Stroke ring in a light rig, refraction on the plate, shutter 90 with 2 sharp frames
var c = AEK.core.comp(ARGS.comp), o = { center: [960, 560], t0: 0.5, dur: 1.0, r0: 10, r1: 1150 };
var rig = AEX.light.rig(c, "SHOCK", { bloom: AEX.glow.plan({ r0: 12, total: 1.6 }) }), cs = [c, rig.light, rig.sum], k;
for (k = 0; k < cs.length; k++) { cs[k].shutterAngle = 90; cs[k].shutterPhase = -45; }   // shutter is per comp: set it in every comp
rig.layer.blendingMode = BlendingMode.SCREEN;
var s = AEX.shock.stroke(rig.light, o);
AEX.shock.mbSplit(s.edge, rig.light, 2); AEX.shock.mbSplit(s.wake, rig.light, 2);
AEX.shock.refraction(c, AEX.vfxu.merge(o, { amount: 60 }));
return AEX.vfx.cost(c, [0.55, 0.7, 1.0, 1.4], ARGS.out, "shock");
```

**GATE 8:** seam score under 0.5 (the luma step across the 12 o'clock line divided by the median
step across other radial lines; 7.2 with the seam open, 0.33 with the fix, 0.16 with displacement
after Polar); the ring fully round at r1 (no straight edges); edge peak on frame 3 at least 70 % of
frame 2. Visual: one hot edge with a falloff inward, the ring the brightest element while it is
fast.

Traps: a masked duplicate of the band for the seam failed because a layer's masks run before its
effects. Coarse noise or flat-domain displacement makes the seam. Without a light rig the polar ring
read as smoky orange patches with no edge: build the ring as light.

## 9. Volumetric rays

**Goal:** rays from a light that pass behind the foreground without lifting its blacks.

Steps:

1. Build the rays from a light-only comp (the source and what it shines through), never from the
   whole frame.
2. `AEX.rays.fromLight(comp, lightComp, {under: foreground})` or
   `AEX.rays.rig(comp, lightComp, {under: foreground})`: CC Light Rays (or CC Radial Fast Blur),
   Screen, placed under the foreground layer.
3. CC Light Rays Radius is the emitting circle: 120 gave beams through every gap, 30 almost none.
   Intensity is about linear (+3.8, +7.6, +15.2 levels at 50, 100, 200).
4. In a rig with the DAY map (top tone 0.96) the sun disc maps to the top tone instead of clipping.
5. Only a flattened plate: `AEX.rays.fromPlate` keeps what is above a threshold (Levels Input Black
   `-0003` = thr x Input White `-0004`). The rays then cross the foreground edge.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), fg = c.layer(ARGS.foreground), light = AEK.core.comp(ARGS.lightComp);
var r = AEX.rays.rig(c, light, { method: "lr", center: [1300, 220], intensity: 100, radius: 120, bloom: 1.2, under: fg });
return AEX.vfx.cost(c, [0, 1, 2], ARGS.out, "rays");
```

**GATE 9:** foreground pixels and the frame's 5th percentile lifted by 0; 0 pixels clipped with
`AEX.rays.rig` (plain `AEX.rays.rays` at gain 1.5 added 0.9 % clipped: keep its gain near 1 or use
the rig). Visual: rays fall off with distance from the source (bright near it, gone before the frame
edge).

Traps: whole-frame methods lifted foreground blacks 2.7 to 13.2 levels; a CC Radial Fast Blur copy
of the scene lifted the haze median by 61.7. CC Radial Fast Blur on the light gives a starburst and
clipped 25,000 to 50,000 px at gain 2. CC Light Burst 2.5 made no beams. The rays alone had no
falloff (haze midtones +16 to 23): add a radial mask or a ramp on the rays layer so they die out.

## 10. Lightning

**Goal:** a bolt with a white core, a colored glow that never clips, strikes that redraw, and light
on the ground.

Steps:

1. `AEX.bolt.strike(comp, o)`: Advanced Lightning (Type 2 Strike, Origin `-0002`, Direction `-0003`,
   core white, Glow Opacity `-0012` 0) on black, in a light rig with the ELECTRIC map, Screen.
2. One envelope expression on the bolt's Exposure: each strike decays as exp(-f / 2.5), times a
   flicker held on twos. Core, glow and spill follow it together (correlation 0.94).
3. Conductivity State: +37 at each strike (a new bolt), +0.15 every 2 frames (even 0.15 replaces 62
   to 81 % of the core).
4. Spill: `AEX.bolt.spill(comp, rig, surfaceLayer, o)`: the summed light, Gaussian 260, Tint to the
   mid tone, gain 8, luma-matted by the ground.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var r = AEX.bolt.strike(c, { name: "BOLT", from: [700, 0], to: [1100, 760], strikes: [0, 9, 20], forking: 0.3 });
AEX.bolt.spill(c, r, c.layer(ARGS.ground), { name: "BOLT" });
return AEX.vfx.cost(c, [0, 4 / 24, 9 / 24, 20 / 24], ARGS.out, "bolt");
```

**GATE 10:** 0 pixels clipped in all three channels outside the strike point; up to about 120 px
(0.006 %) on the strike frame; the bolt shape changes at each strike and holds between. Visual: one
main bolt clearly brighter than its forks.

Traps: the naive build (own glow, tint, three Glows) clipped 7,344 to 30,483 px in all channels.
Forking takes 0 to 1 by script (30 threw out of range); Core and Glow Opacity take 0 to 100. A blue
tone at 1.0 clipped the blue channel on up to 45,697 px: no channel at 1.0 in the map. There is no
sky flash in this build: for a storm, add the envelope to a large soft layer over the sky.

## 11. Distortion and heat haze

**Goal:** the plate bends like air or glass without melting and without dark edges.

Steps:

1. Maps are precomps: the map layer's own effects and masks are ignored. Red = X, green = Y, 0.5 =
   no shift.
2. `AEX.distort.hazeMap`: two blurred Fractal Noise fields tinted red and green over [0.5, 0.5, 0],
   drifting up.
3. `AEX.distort.ringMap`: ramps through a ring matte in a SQUARE comp 2 x (radius + width) wide (a
   host-sized comp cropped the ring into straight edges). A ring map displaces 0.93x the amount.
4. Make the ring bipolar, like glass: `apply` adds a second ring map `<name>_IN` at radius - `inner`
   x width (default 0.8) with `innerAmount` (default -amount); a negative Max is accepted. A
   one-sign ring moved 99.5 % of the matched points outward, so the picture slides; the bipolar ring
   moved 48 % out and 52 % in. `inner: 0` gives the old one-sign ring. Keep the amount at about
   0.075 x the band width (±8 px over 110): `apply` warns above 0.1 x.
5. Pad the plate (`AEX.distort.padded`, mode "mirror", the default): one layer with Motion Tile,
   output width and height 100 x (W + 2 pad) / W + 1 %, Mirror Edges on, so the border continues the
   picture. Mode "scale" keeps the old 112 % copy, whose border pixels pull in a picture that does
   not continue the edge.
6. Time: `envelope` on a ring or on the haze multiplies Max by an expression of `time` (string) or
   by linear keys `[[t, v], ...]`. The map layer's opacity is ignored, so strength over time must
   come from Max. `ring` takes an array for several rings in one call.
7. Chromatic split: three Channel Mixer copies with multipliers 0.88 / 1 / 1.14 (about 9 px of
   split).
8. Keep haze off the hero with a feathered band (`region`), and place it over texture (grass, rock,
   foliage): over sky or a flat ridge it moves the picture without showing it.

Amounts: Displacement Map p95 shift is about 0.68 x Max Displacement, the mean about 0.33x. It reads
as air while Max is at most 0.1 x the noise scale and melts from 0.2x.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), plate = AEK.core.item(ARGS.plate);
var r = AEX.distort.apply(c, plate, { pad: 48,
    haze: { scale: 200, amount: 18, region: [0, 600, 1920, 1080], feather: 160, rise: 90 },
    ring: { center: [960, 540], radius: 420, width: 70, at: 0.5, frames: 20, fade: 10, amount: 40 } });
return AEX.vfx.cost(c, [0.5, 0.7, 1.0], ARGS.out, "distort");
```

Bipolar ring with an envelope on the haze (keys: off before 0.8 s, full at 0.93 s, fading out from
2.5 to 4.5 s):

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), plate = AEK.core.item(ARGS.plate);
var r = AEX.distort.apply(c, plate, { pad: 64, split: [1, 1, 1],
    ring: { name: "RING", center: [946, 414], radius: 1100, width: 110, at: 0.8, frames: 40, fade: 16, amount: 8 },
    haze: { name: "HAZE", scale: 90, amount: 8, region: [0, 640, 1920, 1080], feather: 120, envelope: [[0.8, 0], [0.93, 1], [2.5, 1], [4.5, 0]] } });
return { maps: r.maps, warnings: r.warnings };
```

Measured on a 1080p daylight plate: the ring's p95 shift 8.1 px; the haze's mean change 0.25 levels
before its envelope opens (5.0 without one), 5.1 at full, 3.3 at 3.3 s. **GATE 11:** no pixel under
4 levels in a 16 px border where the plate has none (a pad gap is black; more dark pixels than the
plate there is plate content pulled in, check a 1:1 crop); haze Max at most 0.1 x the noise scale;
ring Max at most about 0.075 x the band width; split under 8 px. Trap: above about 8 px the split
tears fine texture. A ring over flat areas is invisible: refraction reads only on texture, so place
it over detail or add a faint light edge.

## 12. Lens

**Goal:** a lens finish measured in pixels and stops: distortion, chromatic aberration, halation,
streak, vignette, grain.

Steps (`AEX.lens.apply(comp, sceneComp, o)`, in this order):

1. Optics Compensation on the scene layer, then that layer's Scale (transforms run after effects):
   FOV 12 needs 102 %, FOV 30 needs 108 %. On an adjustment layer the corners stay black.
2. Chromatic aberration: three channel copies via Shift Channels, scaled red 1 + 2c, green 1 + c,
   blue 1. c = 0.15 % gives 0 px at the center and 2.7 px in the corners; 0.3 % gives 5.3 px. Keep
   every channel at 100 % or above, or the frame edge loses that channel. A 2 px shift gives 3 to 4
   px everywhere.
3. Halation: highlights above 0.75, Gaussian 18, red-orange, gain 0.8, Screen.
4. Streak: highlights above 0.8, Gaussian 160 horizontal only (`-0002` 2), 339 px half length,
   tinted, gain 0.6.
5. Vignette: CC Vignette amount (corner against center): 30 = -0.13 stop, 60 = -0.28, 100 = -0.5,
   200 = -1.27, 400 = black corners.
6. Grain last (otherwise the vignette darkens it): Add Grain, Viewing Mode 3. Its frame-to-frame std
   is 4.2 levels per unit of intensity on flat patches near 10/255 and 2.2 at mid gray. Over a
   plate, intensity = the plate's std / that slope (0.17 for a dark plate at 0.73 levels); 1.5 to 2
   is a film look on clean CG.

Measuring a plate: read it the way After Effects decodes it. On an H.264 plate, ffmpeg's default
decode read 2.0 levels darker than the frame After Effects rendered; ffmpeg with
`-vf scale=in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int` matched it within 0.13
levels. Channel-scale CA resamples the frame and changes the spatial grain: high-pass std 0.75 to
0.40 levels without grain, 1.14 to 0.94 with grain 0.3, while the frame-to-frame std stayed at 1.28.
Measure grain frame to frame, or before the CA.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), scene = AEK.core.comp(ARGS.scene);
var r = AEX.lens.apply(c, scene, { fov: 12, fill: 102, ca: 0.0015, halation: 0.8, streak: 0.6, vignette: 100, grain: 1.5 });
return AEX.vfx.cost(c, [0, 1], ARGS.out, "lens");
```

**GATE 12:** corner fringe 2 to 4 px and center 0; corners -0.3 to -0.6 stop; grain std within 10 %
of the plate's own, frame to frame on flat patches (on a held frame, where the plate has no
frame-to-frame grain, its high-pass std on a flat patch before the CA: 0.75 against 0.73 frame to
frame on the same dark plate). Trap: the whole finish at these values reads as subtle: that is the
target. Judge it against the bare frame side by side.

## 13. Integration on a plate

**Goal:** the effect sits in the plate: it passes behind and in front of the subject, lights the
subject's edges that face it, lights and reflects in the floor, and leaves the plate's blacks and
grain as they were.

Steps (`AEX.pulse.build(plateItem, o)`, one scene comp, every light layer in **Screen** over the
plate):

1. **Subject matte.** On a dark plate, a luma key (black below 0.12, white above 0.2), cut above the
   floor reflection. On any other plate the luma key selects the wrong pixels: pass `matte` (a
   footage or comp item from a key, roto or 3D pass, white = subject; `matteMode: "alpha"` reads its
   alpha). It is fitted to the frame; a supplied PNG came out of the matte comp unchanged (0.0
   levels), a matte video followed its source within 0.2 levels.
2. **One envelope null.** A guide null `ENV` with Slider expressions of time from one hit time `at`:
   `hit` (0.75 on the hit frame, 1.0 one frame later, then exp(-t / 0.55 s)), `core` (tau 0.3 s),
   `flash` (exp(-t / 1.1 frames): 1, 0.40, 0.16, 0.07), `haze` (attack 4 frames, decay 0.8
   e^(-t/33) + 0.2 e^(-t/90) frames), `shake` (exp(-t / 3.5 frames)), `pre` (breathing 0.12 + 0.04
   sin and an inhale in the 9 frames before the hit). Light, flash, reflection, pool, interactive
   light, haze and shake all read these sliders.
3. **Two light rigs split by depth.** BACK (bloom r0 16, 5 copies, total 0.7) holds what lives
   behind and around the subject: rings, floor ring, back streaks, lit haze, rays, lit dust. FRONT
   (bloom r0 10, 6 copies, total 0.9, k 0.72) holds what sits on or in front of it: core cones,
   flash, front and near streaks, embers. Each rig is its own `AEX.light.rig`, one CC Toner map, its
   layer in Screen.
4. **Hold out the BACK rig after its bloom** with the choked matte: blur the matte 4 px, Levels
   black 0.82 / white 0.98 (the edge moves about 2 px inward), feather 1.5 px, matte layer at 94 %.
   Never blur the holdout outward.
5. **Rim and light wrap from the BACK light.** Rim: the BACK gray sum above `rimThr` 0.35 (so only
   rings and streaks passing behind light it), mapped, blur 6, gain 2.4, through the matte minus its
   eroded copy (a band about 3 px inside the edge, feathered 1 px). Wrap: the same sum, blur 30,
   gain 3.5, through matte x inverted 26 px blurred matte, weighted 1.0 at the origin to 0.3 at 760
   px. When the origin sits inside the subject every edge faces it: the choke and the rim fade to
   nothing at `edgeReach` (640 px; the unchoked matte takes over in Lighten through a radial ramp),
   so the far edges keep the full holdout. Far-side outline at the peak: 41 levels without this, 20
   with it; `edgeReach: 0` turns it off.
6. **Core and flash, small.** Core cones 18 / 90 / 320 px at 0.7 / 0.1 / 0.04 and flash 0.12 over a
   380 px cone. The light at the center on the attack is cones + flash + FRONT bloom (about 0.9x the
   wide light again) + plate, all in Screen: budget them together. Flat disc (luma at 0.98 x the top
   tone) on frames 0 to 3 after the hit: 22, 21, 13, 6 px (the old 28 / 100 / 320 at 1.0 / 0.25 /
   0.06 with flash 0.42 gave 159, 63, 48, 40). The flash moves the disc most: 0.2 gave 30 px, 0.28
   gave 38. The breathing glow reads `breath` (2.5) x `pre` on the soft cones only; the tight cone
   reads `core`. 6b. **Embers around the subject.** Shape-layer embers born on an ellipse around the
   subject (`subjectBox` [x0, y0, x1, y1] or `emberBand` half axes), diameters 3 to 16 px
   stratified, life 3.2 to 5.4 s, rising with drift and flicker; 40 % (`emberBack`) in the BACK rig
   at 0.8x size. Measured: 2.3 to 14.8 px in front (6.6x), 1.6 to 11.6 px behind (7.3x), 0 % of
   their light on the subject. `emberMode: "particles"` keeps the CC Particle World burst.
7. **Shockwave drawn twice.** The circle against the background (`AEX.shock.stroke`, r 30 to 1400
   over 1.25 s, light 0.55, a second ring 0.3 s later at 0.3, a Fractal Noise break matte through
   Polar keyed from 150 to -28) and its ellipse on the floor around the floor point under the
   origin: h = floorY - center y, rx = sqrt(r² - h²), ry = floorAspect x rx (0.28 here, the sine of
   the camera tilt). Give the floor ring its own slower travel (r1 1050, 2.6 s, fade (1 - u)^1.4),
   an edge plus one soft band, dashes whose gap opens from 2 to 262 px with age, and the inverted
   subject matte (its back half passes behind).
8. **Tapered streaks in both rigs.** Each streak is two strokes on one decelerating, slightly
   falling expression path: a body tapered to 0 at the tail and a head 1.7x wider and 1.25x
   brighter. 20 in front (2 to 9 px, gain 1.8), 16 behind (1.5 to 6 px, light 0.45 to 0.85), 5 near
   the lens (16 to 30 px, Gaussian Blur 9, gain 0.9). Born past the subject's face (d0 200 to 420
   px). Layer and comp motion blur on, 180 degrees, 16 samples.
9. **Interactive light that fades with distance.** The plate tinted 35 % from coral toward cream,
   times a radial ramp from the origin (white to black at 760 px), Screen, 22 % x (hit + 0.3 flash).
10. **Floor.** Pool: an ellipse under the source at 22 % on `hit`. Reflections of both rig sums,
    mapped, flipped about floorY, Box Blur 16, alpha-matted to the floor, 25 %. Refraction:
    Displacement Map 24 px riding ring 1, hidden before the hit.
11. **Air.** Ambient navy haze 45 %, behind the subject, masked by `ambientMask` (ellipse [820, 520,
    420] px around the origin) so the corners keep their black (plate blacks +2.6 to 3.9 % outside
    the peak; the old mask gave +6.2 to 8.3 %); a soft beam 12 % with dust inside it; lit haze and
    rays from the BACK rig only, cut below the floor line.
12. **Halation and lens streak** from the FRONT sum: threshold 0.7, blur 22, red-orange tint, 0.4;
    threshold 0.85, horizontal blur 240, scale 120 x 10 %, 0.8.
13. **Camera comp.** Time remap `Math.min(time, holdStart)` on the scene layer, Motion Tile 112 %
    mirror, push 100 to 104 %, shake 9 px and 0.35 degrees on `shake`.
14. **Lens last** (`AEX.lens.apply`): CA 0.0015, vignette 70, Add Grain 0.17 (the plate's 0.73
    levels over 4.2 per unit, section 12), mono off, size 1.0. `refract: 0` leaves the refraction
    layer out. `tones` overrides the five tones for every map of the shot; `r.warnings` lists a tone
    channel above 0.95.

**A moving plate.** The builder reads the origin, the floor line and the matte at build time and
works on a held frame. On a moving plate, either hold one frame for the hit, or supply a matte video
(it follows the video) and tie the origin and the floor line to a tracked null from
scenario-after-effects-tracking by hand.

**Daylight variant (bright plate).** A subject held over a sunlit landscape: no luma key, no core
cone, the effect mostly as refraction. Holdout from a matte taken from the source before compositing
(a green-screen key: d = G - max(R, B), alpha 1 below 40, 0 above 110), a clean background behind
the subject so refraction pulls landscape, `AEX.distort.apply` with a bipolar ring (±8 px over 110
px) on the mirrored pad, haze over texture, a warm face light from one `AEX.light.rig` at 0.16 to
0.24 with bloom r0 24, lens CA 0.0015 and grain 0.3 with no vignette or halation. Gates on that
plate: 0 % clipped; blacks (p1 luma beyond 900 px from the subject) never below the plate and above
it by at most one 8-bit code value; grain (high-pass std of a flat sky box) +3.1 % mean, +9.7 % max;
top-1 % saturation measured outside the subject box, so the subject's own colors do not count.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var plate = AEK.core.item(ARGS.plate);
var r = AEX.pulse.build(plate, { name: "PULSE", center: [960, 520], floorY: 765, floorAspect: 0.28, s: 1, at: 0.8, seed: 7 });
return { layers: r.layers, rigs: r.rig, frames: AEX.vfx.cost(r.finalComp, [0.7, 0.8, 0.97, 1.2, 1.8, 3.5, 4.97], ARGS.out, "pulse") };
```

**GATE 13:**

- Pixels at 255 in all channels: 0 % on every frame, flash included.
- Contour ratio: mean luma of the pixels 1 to 3 px outside the matte edge over the mean of those 6
  to 14 px outside (chessboard distance from the matte at 0.5), rows above the matte's vertical
  midpoint, scene comp before the lens. Below 1.0 is a dark contour. At least 1.0 outside the peak;
  on the 20 peak frames at least 0.95 with `edgeReach` (0.96 measured; 1.02 with `edgeReach: 0`,
  which keeps the far-side outline). A 6 px outward holdout blur gave 0.76.
- Far-side outline: mean luma 0 to 3 px inside the edge minus 6 to 12 px inside, more than 300 px
  from the origin: at most about 20 levels at the peak.
- Flash frame: mean luma at most about 0.2 against 0.14 calm (0.7 over 700 px gave 0.35 and a cream
  blob).
- Plate blacks (p1 luma beyond 900 px from the origin) within 5 % of the plate on the scene comp
  outside the peak frame (+0.9 %); measure before the lens, since vignette 70 lowers p1 about 20 %.
- Grain: frame-to-frame std within 10 % of the plate's on flat patches (on a held frame, the plate's
  high-pass std; section 12).
- The last 15 frames differ by 0 levels before grain.
- Element counts returned by the job match the plan (layers, streaks, rings).
- Visual: the subject keeps its own colors and reads through the flash; a thin rim on the edges
  facing the source and none on the far side; streaks pass both in front of and behind the subject;
  the floor ring stays inside the frame and breaks into wisps.

Traps hit:

- A layer shifted earlier for pre-roll keeps its old end: a new layer in a 5 s comp shifted by -5 s
  ended at 0 s. Reset `outPoint` after the shift.
- Rings from `AEX.shock.stroke` fade from 100 % before their start time and sit on the subject at
  r0: hide them before the hit with an opacity expression.
- A stray `//` comment inside a built expression string swallowed the next statement and every
  streak vanished with no error: have each job return element counts and compare them with the plan.
- `final` is a reserved word in ExtendScript.
- ExtendScript read `a ? X : b ? Y : Z` as `(a ? X : b) ? Y : Z`: put the inner ternary in
  parentheses.
- Haze in the BACK rig glowed on the floor in front of the subject: cut it below the floor line.
- Four wake strokes on the floor ring read as record grooves: edge plus one soft band.
- CC Particle World embers emitted from inside the subject stay over it and render smaller than
  their nominal diameter (13 px read as 2 to 4 px points at 1080p; 72 % of their light fell on the
  subject): the default is now shape-layer embers born around it.
- The interactive light is a 2D ramp on a tinted plate: faces turned away brighten too. A normals
  pass from the 3D source is the real fix.

### Simple integration without a holdout

`AEX.integrate.build(host, plateItem, o)` for an effect fully in front of its plate: one light rig
(`AEX.burst.planes`), interactive light from the tinted plate with a radial mask (reach 560 to 760,
feather 0.9x reach), a floor pool, the reflection flipped about the floor line (vertical Box Blur
18, 24 to 30 %), a dim toward `black`, the plate's own 1st-percentile RGB (a required input: without
it the builder adds no dim), one `sampleImage` envelope divided by `envRef`, grain last (Noise 2 %,
mono, Clipping 1). Set `envRef` from a rendered effect-only frame (read from a script, `sampleImage`
returns 0); the 0.25 default is a placeholder. Gate: nearest lit surface +30 % or more on the peak:
+29.6 % with envRef 0.25, +31.2 % with the measured 0.19; lower `envRef` or raise `interactive` to
reach it. Clipped under 1 % (0.36 to 0.59 % beside a cream surface). Dimming toward a palette ink
raised two plates' blacks 6.4 and 9 %.

### Worked example: a pulse leaving a product

A pocket speaker on a dark reflective floor, a still plate held for 5 s at 30 fps; a pulse of sound
energy leaves it on frame 24. Order of operations:

1. Probe the plate: size, rate, black level, grain std. Write the target frame: what the eye sees
   first, the hero shape, what is sharp and soft, how it dies.
2. Pick the origin (the speaker's center), the floor line under it, the floor aspect (0.28), the hit
   time (0.8 s), the hold (last 15 frames).
3. Key the subject matte; cut its reflection below the floor line.
4. Build the `ENV` null and its sliders from the hit time.
5. Plate, then the ambient haze masked to the source and held out by the matte.
6. Beam and dust inside it.
7. Interactive light through the ramp from the origin; floor pool.
8. Refraction riding ring 1, hidden before the hit.
9. Reflections of both rig sums on the floor.
10. BACK rig: rings, floor ellipse, back streaks, lit haze, rays, lit dust; held out by the choked
    matte after its bloom.
11. Light wrap, then rim, from the BACK sum, weighted toward the origin.
12. FRONT rig: core cones, flash, front and near streaks, embers.
13. Halation and lens streak from the FRONT sum.
14. Camera comp: time remap hold, Motion Tile mirror, push, shake; final comp: CA, vignette, grain
    last.
15. Render frames before, at and after the hit, a 12-frame strip from the hit and a 1:1 crop of the
    peak; run the gates above; fix the worst failure picture in critique.md first.

## 14. Energy trail following a moving point

A stroked path drawn from the null's position history is the most controllable trail; Echo is the
quickest. The glow here is the quick Glow stack; for a final look build the trail inside an
`AEX.light.rig` (section 2) and drop `tint` and `glowStack`.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Stroked path from the null's position history, tapered, crackled, motion blur
var c = AEK.core.comp(ARGS.comp);
var s = AEK.build.shape(c, "TRAIL", [{ type: "path", vertices: [[0, 0], [10, 10]], stroke: { color: [1, 1, 1], width: 9, cap: "round", join: "round" } }]);
s.property("ADBE Transform Group").property("ADBE Position").setValue([0, 0]);
var grp = s.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group");
AEK.expr.set(grp.property("ADBE Vector Shape - Group").property("ADBE Vector Shape"),
    "var L = thisComp.layer(\"HAND\"), n = 16, step = thisComp.frameDuration * 0.75, pts = [];\n" +
    "for (var i = 0; i < n; i++) { var t = Math.max(0, time - i * step); pts.push(fromComp(L.toComp(L.anchorPoint.valueAtTime(t), t))); }\n" +
    "createPath(pts, [], [], false);");
var tp = grp.property("ADBE Vector Graphic - Stroke").property("ADBE Vector Stroke Taper");
tp.property("ADBE Vector Taper End Width").setValue(0);
tp.property("ADBE Vector Taper End Length").setValue(100);
var td = AEK.build.effect(s, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 25, "ADBE Turbulent Displace-0003": 18, "ADBE Turbulent Displace-0005": 2 });
AEK.expr.set(s.property("ADBE Effect Parade").property(td.propertyIndex).property("ADBE Turbulent Displace-0006"), "time * 720");
AEX.vfx.tint(s, [1, 0.6, 0.3]);
AEX.vfx.glowStack(s, [{ radius: 8, intensity: 1.5 }, { radius: 40, intensity: 1 }, { radius: 140, intensity: 0.6 }], 0);
s.blendingMode = BlendingMode.ADD;
s.motionBlur = true; c.motionBlur = true;
return { expr: AEK.expr.check(c, 10), frames: AEX.vfx.cost(c, [0.6, 1.3, 2.2], ARGS.out, "trail") };
```

**GATE 14:** `expr.failed` 0; a tapered streak on the null at two different times. Render was 139 ms
per frame against 97 ms for the bare plate (960x540, 16 bpc).

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Echo trail: Echo sees only change INSIDE a layer. Precompose a solid moved by its transform first; shape and text layers echo directly.
var c = AEK.core.comp(ARGS.comp);
var dot = AEK.build.shape(c, "DOT", [{ type: "ellipse", size: [14, 14], fill: [1, 1, 1] }]);
AEK.expr.set(dot.property("ADBE Transform Group").property("ADBE Position"), "thisComp.layer(\"HAND\").toComp([0, 0, 0]);");
var pc = c.layers.precompose([dot.index], "DOT_pre", true), pl = c.layer("DOT_pre");
AEK.expr.set(pc.layer(1).property("ADBE Transform Group").property("ADBE Position"), "comp(\"" + c.name + "\").layer(\"HAND\").toComp([0, 0, 0]);");
AEK.build.effect(pl, "ADBE Echo", { "ADBE Echo-0001": -1 / 96, "ADBE Echo-0002": 40, "ADBE Echo-0003": 1, "ADBE Echo-0004": 0.93, "ADBE Echo-0005": 4 });
pl.blendingMode = BlendingMode.ADD;
return AEX.vfx.cost(c, [1.25, 2.75], ARGS.out, "echo");
```

Trap: Echo Time -1/24 with 14 echoes broke the trail into beads; a solid with Echo applied directly
showed no trail at all. The precompose moves the dot's expression inside: point it back at the
parent comp.

### Finish: keep the light on a transparent element, crackle, flicker, motion blur

From Andrew Kramer's lightning stack (yxncS9gVDYI 00:11:03 to 00:12:12, 00:26:40) and Adobe's time
effects doc.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Solid Composite black so blur keeps its light; Turbulent Displace before and after; Exposure flicker; Timewarp motion blur on a precomp
var c = AEK.core.comp(ARGS.comp), l = c.layer(ARGS.layer);
AEK.build.effect(l, "ADBE Solid Composite", { "ADBE Solid Composite-0002": [0, 0, 0] });   // default color is white
var td = { "ADBE Turbulent Displace-0002": 3, "ADBE Turbulent Displace-0003": 2, "ADBE Turbulent Displace-0005": 2 };
AEK.build.effect(l, "ADBE Turbulent Displace", td, "TD before");
AEK.build.effect(l, "ADBE Gaussian Blur 2", { "ADBE Gaussian Blur 2-0001": 12, "ADBE Gaussian Blur 2-0003": 0 });
AEK.build.effect(l, "ADBE Turbulent Displace", td, "TD after");
AEK.build.effect(l, "ADBE Exposure2", {}, "Flicker");
AEK.expr.set(l.property("ADBE Effect Parade").property("Flicker").property("ADBE Exposure2-0003"), "wiggle(9, 3);");
l.blendingMode = BlendingMode.ADD;
var pl = c.layer(ARGS.pre);
AEK.build.effect(pl, "ADBE Timewarp", { "ADBE Timewarp-0003": 100, "ADBE Timewarp-0024": 1, "ADBE Timewarp-0025": 1, "ADBE Timewarp-0026": 180 });
return AEK.expr.check(c, 10);
```

Check: a 4 px stroke under a 30 px blur alone peaked at 0.055; with Solid Composite black and
Exposure +3 at 0.131. Timewarp Shutter Control 1 at 180 degrees gave a 10 px smear on a square
moving 20 px per frame; Shutter Control 2 (default) gave none. CC Force Motion Blur at its defaults
also works.

## 15. Snow with depth

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Three CC Particle World layers, far / mid / near; terminal speeds from Resistance 10; wind from the Gravity Vector; pre-roll
var c = AEK.core.comp(ARGS.comp);
var L = [["SNOW_far", 3.0, 0.03, 0.18, 60, 0], ["SNOW_mid", 1.0, 0.06, 0.36, 80, 1.5], ["SNOW_near", 0.2, 0.15, 0.7, 90, 6]], i, s;
for (i = 0; i < L.length; i++) {
    s = AEK.build.solid(c, L[i][0], [0, 0, 0], { duration: c.duration + ARGS.preroll });
    s.startTime = -ARGS.preroll;
    s.outPoint = c.duration;   // a layer longer than the comp is cut at the comp end when created: reset the out point after moving it
    AEX.vfx.pw(s, { birthRate: L[i][1], longevity: 8, y: -0.33, rx: 0.65, rz: 0.2, velocity: 0, extra: 0.15, gravity: L[i][3], resistance: 10,
        gravityX: 0.3, gravityY: 1, type: 5, birthSize: L[i][2], deathSize: L[i][2], sizeVar: 50, maxOpacity: L[i][4],
        birthColor: [0.92, 0.95, 1], deathColor: [0.92, 0.95, 1], transfer: 1, seed: 11 * (i + 1) });
    if (L[i][5]) { AEK.build.effect(s, "ADBE Box Blur2", { "ADBE Box Blur2-0001": L[i][5], "ADBE Box Blur2-0002": 2 }); }
}
return AEX.vfx.cost(c, [0, c.duration / 2, c.duration - c.frameDuration], ARGS.out, "snow");
```

**GATE 15:** flake count within 10 % between the first and last frame. Pre-roll at least frame
height / slowest fall speed (the far layer fell about 40 px/s and needed 13 s to fill 540 px). Trap:
without the out-point reset the layers ended before frame 0. CC Snowfall (`CSSnowfall`, Influence
`-0021` 0, Scene Depth `-0004` 5000) gives one flat look from frame 0 with no pre-roll; its default
Influence 80 % renders dark flakes on a black solid.

## 16. Logo that disintegrates into dust

Gradient Wipe driven by a ramp plus noise map, the just-eaten edge band in its own precomp (a track
matte applies after the layer's effects), particles on the wipe front, births gated by the
completion.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ARGS: {logoComp, out}. WIPE_MAP drives Gradient Wipe; EDGE_pre holds the eaten band; dust rides the front.
var lc = AEK.core.comp(ARGS.logoComp), W = lc.width, H = lc.height, FPS = lc.frameRate, DUR = lc.duration;
var mc = AEK.build.comp("WIPE_MAP", { width: W, height: H, fps: FPS, duration: DUR });
var ramp = AEK.build.solid(mc, "ramp", [0, 0, 0]);
AEK.build.effect(ramp, "ADBE Ramp", { "ADBE Ramp-0001": [W * 0.15, H / 2], "ADBE Ramp-0002": [0, 0, 0], "ADBE Ramp-0003": [W * 0.85, H / 2], "ADBE Ramp-0004": [1, 1, 1] });
var nz = AEK.build.solid(mc, "noise", [0, 0, 0]);
AEK.build.effect(nz, "ADBE Fractal Noise", { "ADBE Fractal Noise-0004": 160, "ADBE Fractal Noise-0010": 40, "ADBE Fractal Noise-0015": 5 });
nz.property("ADBE Transform Group").property("ADBE Opacity").setValue(35);
var c = AEK.build.comp("dust_main", { width: W, height: H, fps: FPS, duration: DUR });
var map = c.layers.add(mc); map.enabled = false;
var logo = c.layers.add(lc); logo.name = "LOGO";
AEK.build.effect(logo, "ADBE Gradient Wipe", { "ADBE Gradient Wipe-0002": 0.06, "ADBE Gradient Wipe-0003": map.index });
var comp = logo.property("ADBE Effect Parade").property(1).property("ADBE Gradient Wipe-0001");
comp.setValueAtTime(12 / FPS, 0); comp.setValueAtTime(60 / FPS, 1);   // 0 to 1 by script; the logo reads 12 frames, goes in 48
AEK.motion.ease(comp, 1, 33, 33); AEK.motion.ease(comp, 2, 60, 33);
var ep = AEK.build.comp("EDGE_pre", { width: W, height: H, fps: FPS, duration: DUR });
var mapIn = ep.layers.add(mc); mapIn.enabled = false;
var keep = ep.layers.add(lc); keep.name = "KEEP";
var band = ep.layers.add(lc); band.name = "BAND";
var pair = [[keep, ""], [band, " - 0.06"]], i;
for (i = 0; i < 2; i++) {
    AEK.build.effect(pair[i][0], "ADBE Gradient Wipe", { "ADBE Gradient Wipe-0002": 0.06, "ADBE Gradient Wipe-0003": mapIn.index });
    AEK.expr.set(pair[i][0].property("ADBE Effect Parade").property(1).property("ADBE Gradient Wipe-0001"), "comp(\"dust_main\").layer(\"LOGO\").effect(1)(1)" + pair[i][1] + ";");
}
ep.layer("BAND").setTrackMatte(ep.layer("KEEP"), TrackMatteType.ALPHA_INVERTED);
var edge = c.layers.add(ep); edge.name = "EDGE";
var td = AEK.build.effect(edge, "ADBE Turbulent Displace", { "ADBE Turbulent Displace-0002": 40, "ADBE Turbulent Displace-0003": 12, "ADBE Turbulent Displace-0005": 3 });
AEK.expr.set(edge.property("ADBE Effect Parade").property(td.propertyIndex).property("ADBE Turbulent Displace-0006"), "time * 540");
AEX.vfx.tint(edge, [1, 0.55, 0.2]);
AEX.vfx.glowStack(edge, [{ radius: 6, intensity: 1.5 }, { radius: 40, intensity: 0.8 }], 0);
edge.blendingMode = BlendingMode.ADD;
var dust = AEK.build.solid(c, "DUST", [0, 0, 0]);
var pw = AEX.vfx.pw(dust, { birthRate: 0, longevity: 1.6, ry: 0.11, rz: 0.05, velocity: 0.15, gravity: -0.08, resistance: 2,
    gravityX: 1, gravityY: -0.4, type: 5, birthSize: 0.04, deathSize: 0.02, sizeVar: 60, maxOpacity: 90, birthColor: [1, 0.7, 0.4], deathColor: [0.5, 0.5, 0.55], transfer: 1 }, "PW dust");
AEK.expr.set(AEX.vfx.pwProp(pw, "x"), "var c = thisComp.layer(\"LOGO\").effect(1)(1);\nvar px = linear(c, 0, 1, width * 0.15, width * 0.85);\n(px - width / 2) / width;");
AEK.expr.set(AEX.vfx.pwProp(pw, "birthRate"), "var c = thisComp.layer(\"LOGO\").effect(1)(1);\n(c > 0.02 && c < 0.98) ? 20 : 0;");
dust.blendingMode = BlendingMode.ADD;
return { expr: AEK.expr.check(c, 30), frames: AEX.vfx.cost(c, [0.25, 0.9, 1.4, 1.9, 2.4], ARGS.out, "dust") };
```

**GATE 16:** the logo clean on the first 12 frames (no glowing outline), a broken front moving left
to right, nothing left after frame 60. Trap: displacing a track-matted copy in the main comp put a
glowing outline around the whole logo from frame 0. For the final look, route the edge and dust into
a light rig (section 2).

## 17. Fractal Noise loop

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// 2 revolutions over 48 frames at 24 fps; the frame at the loop length equals frame 0, so the loop is frames 0 to 47
var c = AEK.core.comp(ARGS.comp), s = AEK.build.solid(c, "NOISE", [0, 0, 0]);
var fx = AEK.build.effect(s, "ADBE Fractal Noise", { "ADBE Fractal Noise-0015": 6 });
var r = AEX.vfx.loopNoise(fx, c, 2, 2);
s.outPoint = r.loopFrames / c.frameRate;
return r;
```

**GATE 17:** frame 0 against frame 48: mean and max difference 0 (frame 47 differs 5.0; without
Cycle Evolution frame 48 differs 34.5). Turbulent Displace loops the same way (`-0006`, `-0008`,
`-0009`); Turbulent Noise has no Cycle controls.

## 18. Time effects

- Posterize Time on a solid moved by its transform does not step the motion: it acts on content and
  effects. Put it on an adjustment layer above, or on the precomp. A key on its Frame Rate becomes
  HOLD by itself.
- CC Wide Time on a moving solid gave no smear: same rule as Echo.
- Time Displacement: luminance 128 is no displacement (Adobe doc).

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var adj = AEK.build.adjustment(c, "POSTERIZE");
AEK.build.effect(adj, "ADBE Posterize Time", { "ADBE Posterize Time-0001": 8 });
var fr = adj.property("ADBE Effect Parade").property(1).property("ADBE Posterize Time-0001");
fr.setValueAtTime(1, 12);
return { interpolation: AEK.core.enumName(KeyframeInterpolationType, fr.keyOutInterpolationType(1)) };   // "HOLD"
```

## 19. HUD

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// HUD ring built white: trims, a 60-tick Repeater, rotation and counter by expression, colored once on an adjustment layer
var c = AEK.core.comp(ARGS.comp), W = c.width, H = c.height;
var ring = AEK.build.shape(c, "HUD_ring", [
    { name: "outer", type: "ellipse", size: [300, 300], stroke: { color: [1, 1, 1], width: 3 }, trim: { start: 0, end: 70 } },
    { name: "inner", type: "ellipse", size: [240, 240], stroke: { color: [1, 1, 1], width: 10 }, trim: { start: 10, end: 35 } },
    { name: "tick", type: "rect", size: [3, 14], position: [0, -175], fill: [1, 1, 1] }], { position: [W / 2, H / 2] });
var tg = ring.property("ADBE Root Vectors Group").property("tick").property("ADBE Vectors Group");
tg.addProperty("ADBE Vector Filter - Repeater");
var rep = tg.property("ADBE Vector Filter - Repeater");
rep.property("ADBE Vector Repeater Copies").setValue(60);
rep.property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Position").setValue([0, 0]);
rep.property("ADBE Vector Repeater Transform").property("ADBE Vector Repeater Rotation").setValue(6);
AEK.expr.set(ring.property("ADBE Root Vectors Group").property("outer").property("ADBE Vector Transform Group").property("ADBE Vector Rotation"), "time * 90;");
AEK.text.add(c, "000", { size: 40, fill: [1, 1, 1], justify: "center", position: [W / 2, H / 2 + 14] });
AEK.expr.set(c.layer("000").property("ADBE Text Properties").property("ADBE Text Document"), "Math.round(linear(time, 0, 2, 0, 100)) + \"%\";");
var adj = AEK.build.adjustment(c, "HUD_color");
AEX.vfx.tint(adj, [0.3, 0.85, 1]);
return AEK.expr.check(c, 10);
```

**GATE 19:** 0 expression errors; the counter reads 25 % at 0.5 s and 75 % at 1.5 s; ticks evenly
spaced. For the glow, precompose the HUD into `<rig>_light` (section 2): thin lines need r0 12 and a
total near 2.

## 20. Render cost and headless render

```bash
python3 <skills>/scenario-after-effects-expert/scripts/ae.py run cost.jsx --lib <skills>/scenario-after-effects-vfx/scripts/vfx.jsx --args '{"comp": "int_trail", "out": "<project>/renders"}'
python3 <skills>/scenario-after-effects-expert/scripts/ae.py aerender --project <project>/integrate.aep --comp int_trail --out <project>/renders/trail.mp4
python3 <skills>/scenario-after-effects-expert/scripts/ae.py probe <project>/renders/trail.mp4
```

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ms per frame from a real render: saveFrameToPng timing is quantized by the 100 ms poll
var c = AEK.core.comp(ARGS.comp);
var r = AEK.capture.queue(c, ARGS.out + "/" + c.name + "_cost.mp4", { template: "H.264 - Match Render Settings - 15 Mbps" });
return { frames: r.frames, ms: r.ms, msPerFrame: Math.round(r.ms / r.frames) };
```

**GATE 20:** ms per frame recorded against a plate-only comp in the same job; probe shows the
planned codec, size, rate and frame count.

## 21. Particle plugins and the built-in route

A third-party particle plugin (Trapcode Particular, from Maxon) is where many artists would go for
emit-from-parent, aux systems and fluid physics. From Maxon's guide and Harry Frank's walkthrough
(0MAfXAmrRXc): its particles live in the comp's 3D world space and are seen through the comp camera;
Child Particles/sec is per parent, so set the parent rate to 0 before heavy edits; every render node
needs the plugin; a script can only set its property values. The built-in route used in this skill:
emitter on a moving point = CC Particle World by expression (section 3); birth tied to an event =
Birth Rate by expression (section 16); erosion into reveal = Gradient Wipe front plus particles
(section 16); depth = planes with their own size, speed, blur and opacity (sections 4, 5, 15). There
is no built-in emit-from-parent or fluid solver: say so when the brief needs one.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Decide the route before building: plugin present or built-in CC Particle World
var want = ["Particular", "Form", "Element", "Stardust", "Plexus"], found = [], i, j, e, nativeOk = false;
for (i = 0; i < app.effects.length; i++) {
    e = app.effects[i];
    if (e.matchName === "CC Particle World") { nativeOk = true; }
    for (j = 0; j < want.length; j++) { if (e.displayName.indexOf(want[j]) >= 0) { found.push(e.matchName + " | " + e.displayName); } }
}
return { plugins: found, route: found.length ? "plugin" : "built-in", ccParticleWorld: nativeOk };
```
