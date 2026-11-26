# GUI paths

Menus, panels and settings for the procedures in this skill, for a person or a computer-use agent.
Menu names are those of After Effects 27.0 (English UI). Effect names are display names; scripts use
the match names in [procedures.md](procedures.md).

## Effects by menu

| Effect                                                                                              | Menu path                                             | Match name                                                                                                                 |
| --------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| CC Particle World                                                                                   | Effect > Simulation > CC Particle World               | `CC Particle World`                                                                                                        |
| CC Particle Systems II                                                                              | Effect > Simulation > CC Particle Systems II          | `CC Particle Systems II`                                                                                                   |
| CC Snowfall, CC Rainfall                                                                            | Effect > Simulation > CC Snowfall / CC Rainfall       | `CSSnowfall`, `CSRainfall`                                                                                                 |
| CC Pixel Polly, Shatter, Card Dance                                                                 | Effect > Simulation                                   | `CC Pixel Polly`, `APC Shatter`, `APC CardDanceCam`                                                                        |
| Fractal Noise, Turbulent Noise, Curl Noise                                                          | Effect > Noise & Grain                                | `ADBE Fractal Noise`, `ADBE AIF Perlin Noise 3D`, `ADBE Curl Noise`                                                        |
| Add Grain, Match Grain                                                                              | Effect > Noise & Grain                                | `VISINF Grain Implant`, `VISINF Grain Duplication`                                                                         |
| Turbulent Displace, Displacement Map, Polar Coordinates, Offset                                     | Effect > Distort                                      | `ADBE Turbulent Displace`, `ADBE Displacement Map`, `ADBE Polar Coordinates`, `ADBE Offset`                                |
| Advanced Lightning, Gradient Ramp, Beam, Grid, Stroke, Write-on                                     | Effect > Generate                                     | `ADBE Lightning 2`, `ADBE Ramp`, `ADBE Laser`, `ADBE Grid`, `ADBE Stroke`, `ADBE Write-on`                                 |
| CC Light Rays, CC Light Burst 2.5, CC Light Sweep                                                   | Effect > Generate                                     | `CC Light Rays`, `CC Light Burst 2.5`, `CC Light Sweep`                                                                    |
| Glow                                                                                                | Effect > Stylize > Glow                               | `ADBE Glo2`                                                                                                                |
| Radial Blur, CC Radial Fast Blur, Fast Box Blur, CC Vector Blur, Directional Blur, Camera Lens Blur | Effect > Blur & Sharpen                               | `ADBE Radial Blur`, `CC Radial Fast Blur`, `ADBE Box Blur2`, `CC Vector Blur`, `ADBE Motion Blur`, `ADBE Camera Lens Blur` |
| Echo, Posterize Time, Time Displacement, CC Wide Time, Timewarp                                     | Effect > Time                                         | `ADBE Echo`, `ADBE Posterize Time`, `ADBE Time Displacement`, `CC Wide Time`, `ADBE Timewarp`                              |
| Gradient Wipe, Linear Wipe                                                                          | Effect > Transition                                   | `ADBE Gradient Wipe`, `ADBE Linear Wipe`                                                                                   |
| Tint, Curves, Exposure, Levels, Colorama, Hue/Saturation                                            | Effect > Color Correction                             | `ADBE Tint`, `ADBE CurvesCustom`, `ADBE Exposure2`, `ADBE Easy Levels2`, `APC Colorama`, `ADBE HUE SATURATION`             |
| Unmult                                                                                              | Effect > Keying > Unmult                              | `ADBE Unmult`                                                                                                              |
| Solid Composite, Set Matte, Calculations                                                            | Effect > Channel                                      | `ADBE Solid Composite`, `ADBE Set Matte3`, `ADBE Calculations`                                                             |
| CC Toner                                                                                            | Effect > Color Correction > CC Toner (Tones: Pentone) | `CC Toner`                                                                                                                 |
| Gaussian Blur, Camera Lens Blur                                                                     | Effect > Blur & Sharpen                               | `ADBE Gaussian Blur 2`, `ADBE Camera Lens Blur`                                                                            |
| Optics Compensation                                                                                 | Effect > Distort > Optics Compensation                | `ADBE Optics Compensation`                                                                                                 |
| Shift Channels, Channel Mixer                                                                       | Effect > Channel / Effect > Color Correction          | `ADBE Shift Channels`, `ADBE CHANNEL MIXER`                                                                                |
| CC Vignette                                                                                         | Effect > Stylize > CC Vignette                        | `CS Vignette`                                                                                                              |
| Noise                                                                                               | Effect > Noise & Grain > Noise                        | `ADBE Noise`                                                                                                               |
| Slider Control                                                                                      | Effect > Expression Controls > Slider Control         | `ADBE Slider Control`                                                                                                      |

## Settings that matter, by recipe

- **Bit depth:** File > Project Settings > Color > Bit Depth 16 bits per channel for every effect in
  this skill (Engine: Adobe); Alt-click (Option-click on macOS) the bpc label at the bottom of the
  Project panel to cycle.
- **CC Particle World guides:** Effect Controls > Grid & Guides: untick Position, Radius, Motion
  Path, Grid, Horizon, Axis Box for a clean view.
- **CC Particle World producer on a layer:** Alt-click (Option-click) the stopwatch of Producer >
  Position X, type the expression from procedures.md; same for Position Y.
- **Pre-roll particles:** select the layer, drag it left in the timeline so its In point sits before
  0, or in the Timeline In column type a negative start.
- **Echo trail:** select the moving layer, Layer > Pre-compose (Ctrl+Shift+C, Cmd+Shift+C), "Move
  all attributes into the new composition", then Effect > Time > Echo on the precomp layer. Shape
  and text layers do not need it (continuous rasterization).
- **Fractal Noise loop:** Evolution Options > Cycle Evolution on, Cycle (in Revolutions) N; keyframe
  Evolution 0 at the loop start and N x 360 at the loop end; right-click both keys > Keyframe
  Interpolation > Linear.
- **Glow finish:** Effect > Channel > Solid Composite, Color black, first in the stack; Effect >
  Color Correction > Exposure last; Alt-click (Option-click) Exposure's stopwatch and type
  `wiggle(9, 3)`; layer mode Add.
- **Motion blur without retiming:** Effect > Time > Timewarp on the precomp layer, Speed 100, Motion
  Blur > Enable Motion Blur on, Shutter Control set to the first item (value 1 by script), Shutter
  Angle 180. Or Effect > Time > CC Force Motion Blur.
- **Before a long render:** in Effect Controls, a yellow warning icon marks an effect without
  Multi-Frame Rendering support.
- **Advanced Lightning:** Lightning Type Strike; Glow Settings > Glow Opacity 0; Core Color white;
  Expert Settings > Termination Threshold about 5; put the layer in the light comp of a rig and
  drive Conductivity State with the strike expression from procedures.md (held on twos).
- **Shockwave:** Composition > New Composition, square, side at least 2 x (end radius + thickness)
  for the band; then Effect > Distort > Polar Coordinates on the band precomp layer, Interpolation
  100 %, Type of Conversion Rect to Polar. Seam fix: a new adjustment layer inside the band comp
  with Effect > Distort > Offset (Shift Center To half the width) and two feathered masks at the
  edges. Composition > Composition Settings > Advanced > Shutter Angle 90, Shutter Phase -45.
- **Wave on the floor:** a shape layer with two Ellipse paths (outer and inner edge of the band),
  Add > Fill with Fill Rule Even-Odd. Transform: Group Scale Y at floorAspect x 100 %, Position at
  the floor point under the source, so the ring lies on the floor (the scripted path also widens its
  front half). Effect > Blur & Sharpen > Gaussian Blur 2 to 3 px. Put it under the subject with a
  track matte from the subject matte above the floor line.
- **Rays:** precompose the light source alone (sun disc, window, lamp and what it shines through);
  on that precomp layer Effect > Generate > CC Light Rays, Radius 120 or 1.2 x the sun disc's radius
  if larger, Intensity 100 (about 60 with a large radius); mode Screen (F4 shows the Mode column);
  drag the layer just below the foreground layer. For soft beams, Gaussian Blur the source a little
  before the rays and 6 px after.
- **Grain:** Effect > Noise & Grain > Add Grain on a top adjustment layer, Viewing Mode Final Output
  (the default Preview shows only a box), Intensity 1.5 to 2. Or Effect > Noise & Grain > Noise 2 %,
  Use Color Noise off, Clipping on.
- **Track matte (23.0+):** Track Matte column, pick the matte layer from the menu, then the Alpha or
  Luma icon and the invert icon.
- **Render time:** Composition > Composition Profiler... is a menu label not found by script
  (command id 0 on 27.0); read the render time in the Render Queue panel after a render, or the Info
  panel during a preview.
- **Light rig:** Composition > New Composition `<name>_light` (gray light only); a second comp
  `<name>_sum` with a black solid, the light comp in Add, and five duplicates each with Effect >
  Channel > Solid Composite (Color black), Effect > Blur & Sharpen > Gaussian Blur (12, 24, 48, 96,
  192, Repeat Edge Pixels off), Effect > Color Correction > Exposure (Bypass Linear Light Conversion
  on, Exposure = log2 of the copy's gain), mode Add. In the shot comp: the sum comp, Effect > Color
  Correction > CC Toner, Tones Pentone, the five tone colors; mode Screen.
- **Light level of an element:** Effect > Color Correction > Exposure, tick Bypass Linear Light
  Conversion, Exposure in stops (-1 = half).
- **Particle burst in CC Particle World:** Physics > Animation Cone Axis; Direction Axis X and Y set
  to the direction; Birth Rate keyed with hold keys for 2 or 3 frames; Particle > Transfer Mode
  Composite.
- **Embers color fade:** Particle > Color Map Custom, the five stops black, color, hot, color,
  black; Transfer Mode Add while sparse.
- **Lens distortion:** Effect > Distort > Optics Compensation on the scene layer itself, Field Of
  View 12; then the layer's Scale 102 %.
- **Chromatic aberration:** three copies of the scene precomp, Effect > Channel > Shift Channels
  keeping one channel each (others Full Off), Scale 100.3 / 100.15 / 100 %, all in Add over black.
- **Vignette:** Effect > Stylize > CC Vignette on an adjustment layer, Amount 100 for -0.5 stop in
  the corners.
- **Heat haze map:** a map comp with two Fractal Noise solids tinted pure red and pure green over a
  [128, 128, 0] solid; on the plate (padded) Effect > Distort > Displacement Map, Use For Horizontal
  Red, Vertical Green, Displacement Map Behavior Center Map.
- **Interactive light:** duplicate the plate above itself, Effect > Color Correction > Tint (Map
  Black To black, Map White To the light color), an ellipse mask with a large feather, mode Add;
  Alt-click Opacity and link it to the envelope slider.
- **Reflection:** duplicate the effect precomp, Scale -100 % in Y, move it below the floor line,
  Effect > Blur & Sharpen > Fast Box Blur 18, Blur Dimensions Vertical, opacity 24 to 30 %, alpha
  matte to a floor solid.

## Things only a person can do

- Drawing masks by hand around a hand or an object: scripted substitute is a `Shape` mask or a shape
  layer from points.
- Tracking the real hand (Tracker panel, Track Motion, Analyze Forward): GUI analysis; the scripted
  substitute is a keyed null (this skill's tests), and the tracking sibling owns the real track.
- A third-party particle plugin's designer window, if one is installed.
- Judging the five visual gates (hierarchy, few large elements, variation, core falloff, air) at
  viewing size.
- Judging motion feel: RAM preview at full frame rate (Spacebar or Numpad 0).
