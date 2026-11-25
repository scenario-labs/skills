# Expert notes

Principles and judgment by expert, with source and timestamp. Numbers are as shown on screen in the
source. Items marked [added] are this skill's additions measured on After Effects 27.0. The second
half is grouped by subject (energy and light, particles, natural elements and distortion,
integration), then by channel.

## Andrew Kramer: lightning and plate integration (yxncS9gVDYI)

- Turn the effect's own glow off (Advanced Lightning Glow Opacity 0) and build glow from three
  stacked Glow effects at low intensity, radius about 25 to 30, about 100, and larger, plus
  Exposure, threshold 0 (00:19:38 to 00:20:49). Adobe's doc adds that Glow Opacity 0 "can speed up
  rendering time greatly".
- Blur fades a transparent element: add Solid Composite (black) before the blur, then Exposure to
  push the light back, and set the layer to Add (00:11:03 to 00:12:12). On screen: Fast Box Blur
  75.2 H, 67.3 V, iterations 3, Exposure 17.33.
- Termination Threshold about 5 % stops the bolt stretching when the origin leaves the layer; Alpha
  Obstacle plus a mask makes the bolt touch the ground (00:06:08).
- Reflections: duplicate the element four times (spec, diffuse, point, contact), each with its own
  blur and Exposure, luma-matted by a ground texture (00:15:06 to 00:17:55).
- Feed the plate into the effect: paste the footage inside the texture comp in Soft Light with
  Exposure (00:27:13). The effect then carries the plate's texture and color.
- Flicker with `wiggle(9,3)` on Exposure: "gets bright really fast" (00:26:40). Turbulent Displace
  before glow removes detail, after glow adds it back (00:26:40).
- Work at 32 bpc so Exposure can recover blurred light (project on screen). Advanced Lightning
  itself renders 8 bpc (Adobe doc).
- [added] Live 27.0: Fast Box Blur 30 on a transparent 4 px stroke left a 0.055 peak; Solid
  Composite black plus Exposure +3 brought it to 0.131. Solid Composite's default color is white:
  set black. `wiggle(9, 3)` on Exposure swung -3.46 to +3.19 stops over 48 frames.

## Andrew Kramer: shockwave (JYbgjCR8PMI)

- Build the shockwave flat: a Fractal Noise band that falls down the frame, then Polar Coordinates
  Rect to Polar at 100 % bends it into a ring. Found by reversing Polar to Rect on a real element
  (00:01:35, 00:05:07).
- Hide the polar seam with an Offset layer (Shift Center To half the width) and a feathered Subtract
  mask over the seam, placed below the Polar layer so Polar runs last (00:09:37 to 00:11:25).
- No two copies share a speed: different evolution multipliers (`time*150`, `time*250`), seeds,
  timing and feather (00:05:35 to 00:08:32).
- Retime the finished element: pull the climax keys in (frame 15 to about frame 6), ease the middle
  key, add a 25 % to 100 % scale ease for a fast start (00:11:50 to 00:13:58).
- CC Glass under Fractal Noise, Bump Map None, Displacement -190, chokes noise into a liquid shape
  (00:07:25).
- [added] Live 27.0: the polar ring needed the band in its own precomp; Polar Coordinates read back
  Type of Conversion 2 by default.

## Andrew Kramer: light rays (frXQxwMKh6c)

- Volumetric light is a 2D CC Radial Fast Blur (Zoom Brightest, Amount 86 to 95) on a Screen
  adjustment layer, its center driven by `thisComp.layer("Point").toComp([0,0,0])` (00:05:19 to
  00:08:01). The null's Z distance sets beam width and swoop.
- Curves before the radial blur is the threshold: only highlights make rays (00:06:56). Add bright
  fractal cards if rays are weak (00:11:54).
- Keep the title readable: a duplicate above the rays with Bevel Alpha (Edge 3.8, Light Angle -60,
  Intensity 0.40), Screen (00:12:28 to 00:14:50).
- On live action, the same center expression points at a 3D Camera Tracker null (00:17:09 to
  00:20:34).

## Brady, Texturelabs: native fire (ac9Wh6-4jH4)

- Everything moves up at different noise-offset speeds for parallax depth (Y 0 to -570, 540 to
  -1250, 540 to -540, 540 to -260).
- One-direction blur: CC Vector Blur, Direction Fading, vector map a plain solid, Angle Offset 180,
  Amount 140 (00:04:35).
- A displacement map limited to 0 to 50 % gray (Levels Output White 127) displaces one way only
  (00:11:01). Adobe doc: 128 gray is no displacement.
- Grade at the end: Colorama Fire at 30 % blend, Glow A FF6500 and B A91200, radius 300, intensity
  2, Unsharp Mask 100 (00:15:19 to 00:17:01).
- Calculations (Second Layer = source, Copy) makes a live copy of text without a precomp; it fails
  for imported vectors (00:09:22 to 00:10:27).

## Nikhil Pawar, Dope Motions: CC Particle World bursts (hv4r7WP9KwI)

- Burst: Birth Rate 0, keyed to 4 for four frames, back to 0; Longevity 4 (00:11:39 to 00:13:16).
- Floor: Floor Action Bounce, Bounciness 25, Random Bounciness 23, Bounce Spread 22, tuned for that
  scale (00:12:44).
- Velocity 1.5 was too much, 1.25 kept (00:13:48). Hue/Saturation Lightness -40 too dark, -30 kept
  (00:16:02).
- Unify color by copying one Hue/Saturation (Colorize) onto every particle, flare and spark layer
  (00:15:29, 00:17:52).
- Fake a reflective floor with a blurred, wiped duplicate of the particles: Fast Blur 25 horizontal,
  Linear Wipe 180, 70 %, feather 35 (00:16:26).

## Jake Bartlett, Jake In Motion: Fractal Noise (kdttSozSLG4)

- Loop with Cycle Evolution on and Cycle (in Revolutions) N, Evolution keyed over the loop
  (00:03:20).
- Contrast 266 with Soft Clamp gives smooth clouds; Contrast 701 with Wrap Back gives contour lines
  (00:01:41, 00:01:46). Unlink Uniform Scaling for streaks (00:02:08).
- Turbulent Noise is faster and has no Cycle controls: use Fractal Noise for loops (Adobe doc
  agrees). [added] Live 27.0: Turbulent Noise (`ADBE AIF Perlin Noise 3D`) exposes Turbulence Factor
  and no Cycle Evolution.

## Ignace Aleya: HUD (pnRRmlmZ6Z0)

- Build the HUD white, color it once: Tint (Map White To E5864D), Glow 1 (60 %, radius 10, intensity
  1.0, Behind, Add), Glow 2 (52.5 %, radius 250, intensity 1.0), an S-curve on green, then a black
  and white Tint at 50 % (00:27:53 to 00:28:59).
- Single-axis jitter: `[wiggle(2,270)[0], value[1]]`. Churning digits: Character Offset `time*24`
  (00:25:29 to 00:27:15).
- A 100 px circle comp tiled by Motion Tile on a 50 px grid aligns dots to cells (00:04:57).

## Harry Frank, Maxon: what a particle plugin changes (0MAfXAmrRXc and the Particular guide)

- Dynamic Form needs a fixed count and enables simulations; Classic Form allows animated counts and
  disables them. Anything with a birth event must be a finite-life system (00:02:24 to 00:04:35,
  00:20:50).
- Emit from Parent, At Parent End of Life spawns a particle when another dies: erosion turns into
  reveal. Set the source layer to opacity 0, not off, when a plugin reads it (00:17:32 to 00:20:50).
- Set Particles/sec to 0 before heavy edits: child systems multiply the count (00:17:32). Child
  Particles/sec is per parent particle (guide).
- Teams stop children eating their own source; Target Attraction works only inside Range of View
  (00:21:38 to 00:25:56).
- Particles sit in the comp's 3D world space and are seen through the comp camera (guide, Producer
  Position). [added] Live 27.0: CC Particle World also renders through the comp camera when one
  exists, and its Effect Camera is then ignored.
- Every render machine needs the plugin; a script cannot rely on third-party match names being
  present.
- Guide: Blend Mode Normal/Add over Life suits flames turning to smoke; Air Turbulence is fast but
  not compatible with Fluid physics or Classic Form; a Turbulence Field Flow Loop repeats, drop the
  frame at the loop time.

## Compositing sources: making an effect sit (HWNAGKi6apM, gomawnMPWEg, vJ8X58uknsk)

- Over bright plates, remove black with Unmult, not Screen or Add, so the element does not brighten
  what is behind (HWNAGKi6apM 00:08:23). Unmult is native since 26.0.
- Fake light wrap: a backplate copy, Fast Blur 12, luma matte to the rim, Add (HWNAGKi6apM
  00:17:30).
- Match blacks with Levels per channel after placing an element (ProductionCrate, gomawnMPWEg frames
  00:12:20 to 00:14:20). Black level mismatch is the hidden reason a composite feels off
  (vJ8X58uknsk 00:01:34).
- Interaction light on the plate: a warm solid in Add with a large feathered mask (feather 733 then
  406 px on a 4K plate) and a heat-distortion Turbulent Displace (Amount 31, Size 172) on a Screen
  layer (gomawnMPWEg frames 00:20:42, 00:26:50).
- Finish in a separate top comp (bloom, grade, shake) so the composite stays editable (gomawnMPWEg
  00:19:50).

## ShootaTime: time remap (2VhJgv1xGL8)

- Easy Ease both Time Remap keys; handle steepness is speed; put the last key one frame before the
  layer end (00:01:34 to 00:02:41).
- Frame Blending fixes jitter on a 30 fps remap; shoot 60 fps for ramps (00:02:42).

## Energy and light

### Michael Ponch: glow without a plugin (62bVEViJmeA, LP7_547bllU)

- Glow that keeps its color: a ladder of blurred copies with the original composited back at every
  stage; each stage's radius divided by a falloff to imitate inverse-square decay (62bVEViJmeA
  00:03:16 to 00:07:40, 00:06:01).
- Two Glows with gray A and B colors and thresholds far apart (75 % radius 60, 15 % radius 300),
  then one Tritone to color (LP7_547bllU 00:02:03 to 00:02:34).
- Electric stroke: Fractal Noise Contrast 350, Complexity 3, Wrap Back, Turbulent Displace above the
  color, negative Exposure then re-lift (LP7_547bllU 00:05:19 to 00:07:11).
- [added] The skill's rig keeps the idea (gray light, ladder, color once) and measures it: Gaussian
  copies at doubling radii, weights summing to 2.0, CC Toner Pentone as the single color step.

### Adobe Video x Film Riot: lightsaber (g7B281yPWaw)

- Beam glow as a feather ladder: six copies of a masked solid at feather 5, 30, 60, 90, 120 and 240
  px, precomposed over black, Screen, one Color Balance (00:02:05 to 00:03:08).
- Heat warp: Turbulent Displace amount 5 with `wiggle(6,50)` on Evolution (00:03:13). Spill: a
  Curves adjustment layer matted by a feathered solid parented to the tracking null (00:04:03).

### Jake Bartlett, Jake In Motion: Glow, Advanced Lightning, CC Light Burst 2.5 (t40ZTEBr_M0, YJ8jXYU9lYs, rNJ5SRrWqyo)

- Glow Colors A and B with Triangle A>B>A keeps the core in color B (t40ZTEBr_M0 00:03:20); Color
  Phase and Loops animate the glow color (00:05:32).
- Advanced Lightning strikes animate through Decay and Core Drain keys (YJ8jXYU9lYs 00:11:02);
  Composite on Original with an alpha obstacle wraps the bolt around a shape (00:06:37);
  `time*index` gives each copy its own motion (00:18:39).
- [added] By script on 27.0 Forking takes 0 to 1 and Core and Glow Opacity 0 to 100. CC Light Burst
  2.5 made no beams on a light-only layer.

### Lendon Bracewell, Wizard VFX: surface lightning, energy wave (vfovjUAzYLc, AIYp8w4tOQc)

- Exposure before Glow at 32 bpc, three Glows at radius 10, 58 to 75 and 250 (vfovjUAzYLc 00:10:35);
  a Subtract pre-pass with a blurred copy evens the glow (00:12:11); Levels clipped to output black
  removes negative values under Screen at 32 bpc (00:09:30).
- CC Plastic with the footage as bump lights wrinkles under the bolt (00:14:52 to 00:18:23).
- Grain 0.1 after the glows hides banding; Median between blur and glow gives a fluid sharp edge
  (AIYp8w4tOQc 00:11:40, 00:08:23).

### Stephan Zammit: volumetric light (JOQ5UtZuaEg)

- A mist matte restricts where the radial blur makes rays (00:08:03); CC Composite Add Alpha after
  the radial blur keeps the design (00:02:59).

### StahlFerro: energy ring (2ztxKAm_rnM)

- Polar Coordinates, Radial Blur 94 to 96 (not 100), Polar back (00:02:49); fade the energy through
  Fractal Noise Brightness -100, not opacity (00:06:46).

### Film Riot: energy on an actor, portal (tbRoNQv4vpU, AqIGTxUgSm4)

- Compound or Vector Blur with the energy layer as the map, on an adjustment layer below
  (tbRoNQv4vpU 00:03:13); Motion Tile Mirror Edges, output height 110 to hide blur edges (00:03:46).
- Portal: dark smoke comp and bright energy comp kept apart, glow only on the bright part
  (AqIGTxUgSm4 00:08:20 to 00:10:23); spill as a Curves layer matted to the tracking null (00:10:55
  to 00:11:59).

### Maxon Red Giant, Cheap Tricks (d1nUfkmLGaY)

- Small distortions first, large after (00:04:50). Comp energy over a darker background (00:43:30);
  a Brightness and Contrast adjustment under the blast darkens the scene on impact (00:43:30 to
  00:47:26). Small hot lights go above the global glow so they do not blow out (00:26:14).

### Ben Marriott: reactive light (nuN5FqBOvHg)

- Shadows that answer a light: dark fill, CC Radial Fast Blur Amount 90 Zoom Brightest centered on
  the light layer, CC Composite (00:00:32 to 00:01:38).

### SonduckFilm: lens flares (uPa-5UmDEec)

- Flares and streaks as additive elements driven by one null and one slider, streaks with feather 30
  and Glow radius 80 (00:03:43 to 00:06:51).

## Particles

### Jake Bartlett, Jake In Motion: CC Particle Systems II and World, Rainfall, Snowfall, Shatter (7Fp9207Ds5I, c2TT33Vn0OU, UJI7cbilZYA, qzzEy76cCXo)

- Fractal Uni, Direction and Cone animations for bursts that are not spheres (7Fp9207Ds5I 00:55:38,
  00:54:33); bursts of 1 to 3 frames of birth rate (00:56:10).
- Add turns a yellow core white: choose a red core (7Fp9207Ds5I 00:37:10). Inherit Velocity about
  -60 sends particles opposite the producer (00:10:30). Hold Particle Release keeps particles at
  birth for part of their life (01:12:30).
- Producer units: subtract half the size and divide by comp width (7Fp9207Ds5I 00:48:55). [added]
  Measured: divide both axes by the particle layer's width.
- Rain and snow take brightness from the pixels behind (Background Reflection 80 %); Variation of
  Wind is a percentage of Wind (c2TT33Vn0OU 00:04:29, 00:03:56).
- Shatter ignores motion blur: add CC Force Motion Blur (UJI7cbilZYA 00:08:05). Particle Playground:
  wide random spreads, direction 29 and velocity 76 (qzzEy76cCXo 00:07:42).

### Texturelabs: endless Particle World (awCqRPTasBc)

- A flat producer slab (Radius X 0.200, Y 0.020, Z 0.500) and high Velocity 3 with Resistance 5 and
  Gravity 0.25 read as scale (00:00:27, 00:02:09). Echo with Composite in Back and Echo Time equal
  to the loop makes a particle loop (00:06:10 to 00:08:20).
- [added] The skill loops particles with two offset copies of a longer simulation instead: frame L
  equals frame 0 exactly.

### Surfaced Studio: sparks (gQoSJhbmqqo)

- Spark Birth Size 0.1, Death 0.075, Max Opacity 100, Longevity 0.6; near-white birth color; Glow
  threshold raised so only young sparks glow (00:01:43 to 00:03:49).
- One blurred duplicate in Add for the halo while the crisp layer stays (00:10:07); Hue/Saturation
  -50 % removes candy colors (00:10:31); 32 bpc before tuning Glow (00:04:21).

### Ignace Aleya: atmospheric particles, sand (34VLajDswtA, 36OeLwyfXX4)

- A producer slab wide in X, thin in Y, deep in Z for ambient depth (34VLajDswtA 00:03:11); start
  the layer before frame 0 (00:04:35).
- Directional animation for sand (36OeLwyfXX4 00:13:24); `wiggle(10,30)` on Direction, a different
  value per layer (00:14:29).

### VFX Studio Koliba: sand disintegration (wFH3oxTzHcc)

- Several layers with their own seed, rate and velocity (00:05:38); Max Opacity 75 then 40 %; a
  noise luma matte makes emission patchy (00:05:05).

### Manuel does Motion: CC Mr. Mercury explosion, Turbulent Noise (kElBx9dRB80, WyHxDK45wmo)

- Layered emitters with different velocity, birth peak and 1 to 2 frame offsets (kElBx9dRB80
  00:02:47 to 00:04:26); Echo trails -0.007 s, 85 echoes, decay 0.97 (00:05:00).
- Noise as a luma matte for partial blur; Time Displacement through a mosaic noise map (WyHxDK45wmo
  00:03:14, 00:05:53).

### SonduckFilm: particles along a path, floor bounce (-m1TRt4pubM, 4TpoAxhS2M4)

- Radius Z 0.4, Volume Shade 40 and Depth Cue Fade (-m1TRt4pubM 00:05:52); Noise 5 to 6 % mono on an
  adjustment layer glues particles to the plate (00:08:02).
- Radius Z about 1 and Size Variation 100 %; a Compound Blur floor with sharp duplicates above
  (4TpoAxhS2M4 00:01:30 to 00:04:44).

### Others on particles

- Michael Tierney: real depth of field on particle shapes, aperture 500 to 800, focus distance
  animated with `loopOut("pingpong")` (mD_tzQc5Bu0 00:02:08 to 00:02:40).
- Creation Effects: producer larger than the view with the camera inside for floating dust
  (Ia_Z8xE8QHo 00:04:33).
- Beta-1 Studios: enlarge the solid or particles clip at the layer edge (_IeCk4OuvAo 00:09:17).
- Glitter and Motion: Cone Axis for confetti, several low-rate layers (kvIxSduLeRM 00:07:04,
  00:12:27).

## Natural elements and distortion

### ProductionCrate: heat distortion (fbjaIXq3TRg)

- The map in its own comp, Turbulent Noise rising (Offset Y 1080 to about -5902), Evolution
  `time*200`; Displacement Map H -10 (red), V -100 (green), Center Map, Expand Output; Motion Tile
  Mirror Edges above.
- A luminance map driving Camera Lens Blur sells depth haze.
- [added] Measured: Displacement Map p95 shift 0.68 x Max; it reads as air while Max is at most 0.1
  x the noise scale. A padded plate replaced Motion Tile for edges (dark edge pixels down to the
  plate's own).

### LOBO Films: foot stomp shockwave (M778MmkD-uU)

- A shockwave as a blurred ring map laid flat in 3D and scaled (00:00:22 to 00:05:42); heat wave
  after impact by Turbulent Displace ramped from the stop (00:10:25); a wiggle shake 0 to about 27
  to 0.

### Stock effects studio tutorials: fire, explosion and debris (Fga78PEHC2E, wQHwO4U7AiM)

- Fire on a plate: Screen, Levels to crush blacks, Tint plus Curves, then three Glows (threshold 15
  radius 120, radius 600, threshold 90 radius 80) (Fga78PEHC2E). An adjustment layer brightening the
  environment sells the fire's light.
- An explosion needs debris flying outward and a ground reflection (wQHwO4U7AiM 00:13:03, 00:23:43);
  Glow goes above every element (00:20:09); Shift Channels Take Alpha From Luminance beats Screen
  for dust (00:25:20).

### Flat Pack FX: 2D explosion (oI3HwfGClL0)

- CC Particle Systems II, Lens Convex, Birth Rate 0, 20, 0 at frames 0, 4, 6; four duplicates with
  different seeds make it read bigger.
- [added] Measured: a CC Particle Systems II rate held on frame 0 alone emits nothing; start bursts
  on frame 1.

### Texturelabs: burn (tgLHKw_BmLs)

- One transition matte comp drives burn, fire, smoke, embers and heat (00:05:02); CC Wide Time
  backward 20 for smoke, 60 for embers.

### IndependentVFX: muzzle flash (WSNKuNwrblw)

- A one-frame flash plus a one-frame relit copy of the actor and an orange Screen light at 15 %
  (00:08:46, 00:12:10). Smoke drops to 10 to 15 % after 3 frames.

### Ignace Aleya: atmospheric fog (6jYqFBehSmE)

- Three Fractal Noise layers at 5 %, 3 % and 2 % on Screen over a ramp, offsets at different speeds
  (00:03:14).

### Others on elements

- Jake Bartlett: Wave World height map into Caustics; Caustics ignores masks on its layer, so
  precompose (20keMi3bDqc). Turbulent Displace Pinning and Cycle Evolution (HiKTFo-PYAg).
- Mike Murphy: Evolution keyed in whole revolutions with Cycle Evolution; check the loop with a
  snapshot (_I8M3xlMYjs).
- flomotion: Pixel Motion frame blending and Time Warp for slowed stock (igt_9pBiVZ8).
- Creative Dojo: glitch blocks gated by `random(0,100)<25` (uthf6vWhEu0 00:02:07). Surfaced Studio:
  inspect Keylight's Screen Matte view when removing black (a-zJKSIbHtU 00:07:04).

## Integration and lens

### ProductionCrate: advanced explosions (vMtUELG7iS4)

- Illumination map: colored solids masked by depth tier, the plate as luminance track matte, opacity
  keyed to the blast (00:07:12 to 00:11:23). Light wrap from the fire layer, then cut to about 50 %
  (00:11:56). Fire (emissive, Add) and smoke (lit, graded) kept apart.
- [added] The skill's interactive light uses the same principle: a copy of the plate tinted toward
  the light, so only lit surfaces brighten (+36.7 % against +20.5 % for a flat warm disc).

### Film Riot with Olaf Blomeis: photorealism (AaBiE4gT4bw)

- A 0.5 px blur on a clean render before grain; grain matched per channel from plate luminance
  (00:10:20); contact cards where the element meets the ground (00:07:16); redistort CG with the
  plate's lens distortion (00:08:53).

### InLightVFX: reflections (PVSVVUChRP0)

- A reflection of an added object must cover the plate's reflection; adding works only on dark
  floors (00:04:55). Push the reflection matte from about 0.3 to 1 and clamp it (00:13:15). Match
  numbers at raised exposure: floor highlights about 0.85, blacks about 0.006 (00:15:27).

### Jake Bartlett, Jake In Motion: Camera Lens Blur, Pixel Motion Blur (EPw0nMrhP8E, DZAakVlJoGU)

- Bokeh highlights need values above 1.0 to bloom; Highlight Saturation 0 pushes them to white, 100
  keeps the light's color (EPw0nMrhP8E 00:10:40, 00:16:08). The blur map layer set to Effects and
  Masks and hidden; black in focus (00:05:26).
- Motion blur in post: shutter 180, 6 samples preview, 16 render (DZAakVlJoGU 00:00:40 to 00:04:01).

### Manning Moore: halation (S-yhF6gXw2s)

- Copy, isolate highlights, Channel Blur red 50 to 60, Add (00:02:35 to 00:04:19). [added] Measured
  route: highlights above 0.75, Gaussian 18, red-orange tint, gain 0.8, Screen.

### Anamorphic Cookbook: lens look (4yoq1rPTLEs)

- Distortion pulls the corners inward and scales with focal length (00:06:08 to 00:07:15); oval
  bokeh from a custom Lens Blur shape (00:08:30).

### Stock effects studio tutorial: camera shake (jgw-aIsWT5Y)

- Shake as a decaying spike: a slider keyed 0, about 80 at the hit, 0 with a small tail, `wiggle`
  frequency 11 (00:02:34 to 00:06:20). Hide the edges with Motion Tile 120 % Mirror Edges or a scale
  of 102.6 to 105.9 % eased back (00:07:25).

### Creative COW: light wrap (uU-1tFFyoSI)

- Background copy on top with Set Matte inverted and not inverted, Fast Box Blur, Simple Choker;
  dark values Brightness -147, Blur 133, Choke -1.40, opacity 85 % (frame 00:06:30).

### Paul Del Vecchio: title light (f8ibv0YfIZE)

- Volumetric light behind type: a masked white core, Radial Fast Blur Zoom Brightest, Screen
  (00:01:23); light that lights the text must also light the particles in front (00:09:10); source
  flicker Smooth, speed 2, amount 25 (00:02:25).

### Others on integration

- Michael Stark: grain copied from the plate by subtracting a denoised copy in 32-bit linear
  (8o--SIlDr4o 00:04:03 to 00:08:36).
- NBC motion: per-channel Levels found with the R, G, B views (mRmbBMXkads 00:02:20 to 00:03:58).
- Hamza N. Meo: two adjustment states crossfaded for light that changes (_T_3hMirhjw 00:10:26); mist
  pass, small vignette, dust in light shafts (00:11:33).
- Cullen Kelly: exposure gain in linear behaves like the iris; return to log before LUTs
  (FpcE-mlB6Q4 00:08:29, 00:18:21).
- Adobe motion blur doc: shutter phase minus half the angle for tracked composites; 90 degrees at 24
  fps is 1/96 s.

## Where experts disagree

| Topic             | Option A                                                                                                                                                       | Option B                                                                                             | Deciding condition                                                                                                                                                                                                                                                                                                                                                    |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bit depth         | 32 bpc or linear for glow (Kramer; Wizard VFX vfovjUAzYLc 00:10:35; Surfaced Studio gQoSJhbmqqo 00:04:21; ProductionCrate vMtUELG7iS4; Adobe color basics doc) | 16 bpc                                                                                               | [added] Measured on 27.0: one Glow brings a 1.0 disc to 1.1 to 1.4x its light at 16 bpc and up to 15x at 32 bpc; the Glow stack clipped 4 % at 16 bpc and 64 % at 32; CC Toner at 32 bpc tinted the core cyan on software and drew dark blocks on GPU. This skill takes 16 bpc with the light rig, and 32 only inside a person's OCIO project with the amounts redone |
| Glow              | Stacked Glow passes plus Exposure (Kramer) or Glow A/B colors (Texturelabs, Jake Bartlett)                                                                     | Blur ladder of copies, colored once (Michael Ponch 62bVEViJmeA; Adobe Video x Film Riot g7B281yPWaw) | [added] The ladder wins on measurement: Gaussian copies add exactly sum(weights) x the source and carry light to 300 px. The skill's rig is a Gaussian ladder plus one CC Toner map                                                                                                                                                                                   |
| Noise             | Fractal Noise (loops)                                                                                                                                          | Turbulent Noise or Curl Noise (speed, fluid look)                                                    | A seamless loop needs Fractal Noise                                                                                                                                                                                                                                                                                                                                   |
| Black removal     | Screen or Add                                                                                                                                                  | Unmult                                                                                               | Unmult when the plate behind is bright; the light rig goes in Screen                                                                                                                                                                                                                                                                                                  |
| Pre-render        | Pre-render heavy noise stacks (Kramer)                                                                                                                         | Keep live precomps (Aleya)                                                                           | Noise-heavy stacks versus light vector parts                                                                                                                                                                                                                                                                                                                          |
| Particle transfer | Composite, glow on one blurred Add copy (Texturelabs, VFX Studio Koliba, Surfaced Studio)                                                                      | Add on every layer                                                                                   | [added] Add turns neutral from about 50 particles per 100x100 px, Screen from 150; Composite keeps color at any density                                                                                                                                                                                                                                               |
| Grain amount      | Noise 5 to 6 % mono (SonduckFilm -m1TRt4pubM 00:08:02)                                                                                                         | Grain matched per channel from the plate (Michael Stark 8o--SIlDr4o; Film Riot AaBiE4gT4bw)          | [added] Measure the plate's grain std and match it: Noise 2 % gave std 0.006 against 0.002 on a clean CG plate; Add Grain gives 2.2 levels per unit                                                                                                                                                                                                                   |
| Rays              | Radial Fast Blur on a Screen adjustment layer (Kramer frXQxwMKh6c; Paul Del Vecchio f8ibv0YfIZE)                                                               | Rays restricted by a mist or light matte (Stephan Zammit JOQ5UtZuaEg 00:08:03)                       | [added] Whole-frame rays lifted foreground blacks 2.7 to 13.2 levels; rays from the light only lifted them 0                                                                                                                                                                                                                                                          |
