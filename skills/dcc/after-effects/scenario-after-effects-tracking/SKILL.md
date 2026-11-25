---
name: scenario-after-effects-tracking
description: "Use when footage in After Effects must be tracked, stabilized or matchmoved: the track slips or drifts, the insert swims, replace a screen, corner pin a sign, stabilize handheld footage, Warp Stabilizer looks warped or crops too much, a 3D Camera Tracker solve, Mocha AE data, tracked text does not stick, no motion blur on a corner pinned insert, or outside tracking data must become keyframes."
license: MIT
---

# After Effects Tracking and Stabilization

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means choosing the tracker from the shot (point, planar, camera), proving the
result with a number in pixels, and checking the frames before anything rides on the data. An agent
without a mouse cannot draw a Mocha shape, click Analyze, pick track points or press Create Camera.
It can track outside After Effects, write every key itself, read results back, and measure slide on
rendered frames. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit,
version traps).

## Stance (the expert delta)

- Pick the tracker from the geometry. A flat target is a planar or corner pin job; a camera move
  with parallax is a 3D solve; a simple 2D follow is a point track (Ben Brownlee, TF3XVBy6sD4
  00:02:30; Film Riot, kFCNhHI5yOg). Warp Stabilizer is none of the three: it is a self-contained
  shake analyzer that smooths the camera path and gives no data to attach things to.
- Never apply data straight to content you still edit. Data goes on a null, a proof solid or a
  precomp (Film Riot, kFCNhHI5yOg 00:01:48; Mark Christiansen, C_dO9HGrYS8).
- The spline or search box is a search area; the Surface and the Grid show the data (Ben Brownlee,
  TF3XVBy6sD4 00:11:20, 00:11:51). Never fix drift by nudging the shape: find the cause and retrack
  (TF3XVBy6sD4 00:13:32).
- Average Error below 1 pixel is the solve target, and it must fall after every change (wiISCTB4s1Y
  00:02:07; m2bF4U6EBZU 00:01:46). A script cannot read it: measured on 27.0.
- Corner data is in tracked-footage pixels, so the insert must match the tracked footage size, not
  the comp size (Ben Brownlee, 1tWKdbjKLNE 00:04:05, 00:05:13). `AEX.track.cornerPin` meets this by
  mapping the insert's full frame onto comp pixels: the plate must sit unscaled in a comp at footage
  size.
- Chained frame-to-frame tracking drifts; registering each frame to one reference frame does not.
  Measured here: 2.84 px versus 1.11 px at frame 71 of a 72-frame shot [added].
- A Corner Pin is never motion blurred by the layer switch. Move the centroid on Position and pin
  relative to it, the same split Mocha's "Corner Pin (Support Motion Blur)" export makes (measured
  on 27.0; TF3XVBy6sD4 00:18:49).

## Establish first

- **Shot type:** flat target (screen, sign, wall), camera move with parallax, locked-off, handheld.
  It decides the tracker.
- **Footage:** size, frame rate, frame count, shutter (ffprobe through `ae.py probe`). The comp must
  match the footage (UkC9qKS7c0Y 00:00:44).
- **Deliverable:** stabilized plate, screen insert, element on the ground, or keys for another
  artist. Say what may be cropped and the maximum scale-up (example: 4K delivered in HD tolerates
  more).
- **Channel and session:** analysis effects need the app IDLE with the project open (see Procedure
  stage 2). On a shared or busy bridge, plan the scripted substitutes.
- **Tools available:** Python 3 with OpenCV for `scripts/track_external.py`; Mocha AE ships with
  After Effects; its tracking and export are GUI only.
- **Version:** 27.0 and 26.x. Mask Tracker speed changed in 26.3; shadow catchers since 24.5.

## Procedure

1. **Inspect and choose.** Probe the footage. Check `comp.frameRate` and size against it. Pick the
   route:

| Shot                                                                    | Route                                                                       | Agent path                                                                                     |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Phone, screen, sign                                                     | planar track to Corner Pin                                                  | `track_external.py plane` then `AEX.track.cornerPin`                                           |
| Simple 2D follow, a callout or pin on a surface                         | the point carried through the plane's homography                            | `plane`, then `AEX.track.pointsFromCorners` into `pointTracker`, or `nullFromCorners({point})` |
| Object that turns, with a flat rigid part (button panel, label, screen) | plane on that part, never on the curved body                                | `plane --mode ref` on the flat part; measured on an orbiting speaker: 0.89 px mean             |
| Object that turns with no flat part                                     | region similarity, slide-checked                                            | `shake --corners`, then `slide`; it slid 79 px by frame 60 on a speaker's fabric               |
| Handheld, keep the move                                                 | Warp Stabilizer (shake analyzer, no tracker), or smoothed counter-animation | stage 2, or `track_external.py shake` then `AEX.track.stabilize({smooth: 25})`                 |
| Locked-off result                                                       | locked counter-animation                                                    | `stabilize({smooth: 0, autoScale: true})`                                                      |
| Parallax, element on the ground                                         | 3D Camera Tracker                                                           | effect by script; points, ground plane and camera in the GUI                                   |

GATE: route stated with the reason; frame rate and size match; `slide` run on the chosen track
(stage 4).

2. **Background analyzers (Warp Stabilizer, 3D Camera Tracker).** Add `ADBE SubspaceStabilizer` or
   `ADBE 3D Tracker` by script, set the settings by match name, then return control. The analysis
   runs only while the app idles between jobs; `aerender` never analyzes and renders the blue
   "Analyzing in background" banner into the output. Poll with short jobs that capture one frame and
   test it with `track_external.py banner` ([P2](references/procedures.md), where the Warp
   Stabilizer judgment calls also live). GATE: `banner` reports `none` on a captured frame before
   any render.

3. **Track outside After Effects when the GUI is out of reach.**
   `track_external.py plane SHOT --corners "x,y x,y x,y x,y" --ref N --mode ref` registers every
   frame to frame N. Pick N on the largest, clearest view (Mocha AE doc, "Track from the largest,
   clearest point"). The four reference corners come from the person, a marker or a detector.
   `shake` returns per-frame `[dx, dy, rot]` for a static scene. Corners go on a flat rigid part
   (P4). Reflections, fingers or changing screen content need Mocha AE in the GUI
   ([P12](references/procedures.md)). GATE: `inliers` above 8 on every frame but the reference (it
   reads 0 by design); no held pose.

4. **Apply the data.** Load `scripts/track.jsx` with `--lib`.
   `AEX.track.cornerPin(layer, corners, {motionBlur: true})` keys all four corners on every frame. A
   point that must stick (a callout, a pin): `pointsFromCorners(corners, [x, y])` carries it through
   each frame's homography into `pointTracker`, or
   `nullFromCorners(comp, corners, name, 0, {point})` puts a null on it
   ([P9, P11](references/procedures.md)). Under perspective, give each element its own point. Four
   tracked points: `cornerNulls` then `pinFromNulls` ([P14](references/procedures.md)). GATE:
   `numKeys` equals the frame count; `track_external.py slide` on the attach point gives mean under
   1.5 px and no `jumps` (P4); a proof render's `locate` reads under 1 px mean (P9).

5. **Fix a slip at a frame.** Measure the error per frame first (`score` or `readCorners` against a
   re-track). If one region slips, re-register that frame to the reference and call
   `AEX.track.reanchor(effect, frame, corners, ramp)`. If the error grows from the start, retrack in
   `ref` mode or split the shot at the slip with a new reference. GATE: worst frame under 1 px;
   check frames on both sides of the fix on a sheet.

6. **Stabilize by keys.** `AEX.track.stabilize(layer, shake, {smooth, autoScale, margin})`
   counter-animates Position and Rotation about the frame center. It returns the scale that hides
   every border. Lock to a level frame: a locked result keeps the reference frame's tilt. Stabilized
   insert: lock the plate in a precomp, add the insert there, then `AEX.track.restoreMotion` on the
   precomp layer gives the motion back ([P15](references/procedures.md)). GATE: re-track the render
   with `shake`; residual second difference under 0.2 px (camera shake); scale within the
   deliverable's limit; no black border after `restoreMotion`.

7. **Integrate a screen insert.** Size the insert by the data's source. With `AEX.track.cornerPin`,
   any pixel size works (a 520x960 insert held on a 1280x720 plate, measured): give it the screen's
   real aspect so the art is not stretched. Pasted Mocha data needs the insert precomp at the
   tracked footage size (P12). Then Corner Pin with the motion blur split, Gaussian Blur 0.5 to 1 px
   with Repeat Edge Pixels off, a white veil in Screen at a few percent for glass, Noise matched to
   the plate grain. Hand finger mattes and key cleanup to scenario-after-effects-compositing. GATE:
   insert black level and grain measured against the plate; a contact sheet at four times.

8. **Solve and judge a camera.** Track a sharpened copy (P13), then in the GUI set the ground plane
   and origin before Create Text and Camera, Null and Camera, or Shadow Catcher, Camera and Light
   (m2bF4U6EBZU frame 00:06:00). Read Average Error in Effect Controls (GUI only). Place a proof
   solid on the ground, render, and track a feature of it and a plate feature next to it with
   `track_external.py`: their distance over time is the slide. Scale, anchor and retrack rules:
   [P13](references/procedures.md). GATE: slide under 1 px over the shot; no step at a cut.

## Numbers

| Value                      | Meaning                                                                                                          |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| < 1 px                     | Average Error target for a 3D solve; also the slide target for anything placed on a track                        |
| 0.657 px mean, 1.41 max    | measured: four screen corners, `ref` mode, 72 frames at 1280x720, blur and noise                                 |
| 1.414 px mean, 2.84 at f71 | measured: same shot, frame-to-frame chaining; 0.909 after `reanchor` (P6)                                        |
| 0.74 px mean, 1.03 max     | measured: marker on `nullFromCorners({point})`, button panel of a speaker turning in depth, 120 frames 1920x1080 |
| 10.0 px mean, 19.9 max     | the same shot with the former centroid null and a child on the button (top-edge rotation and scale only)         |
| 118.65 % / 105.37 %        | measured: scale to hide borders, locked versus 25-frame two-pass smoothing                                       |
| 50, 150, 3                 | Warp defaults: Smoothness, Maximum Scale, Framing (Stabilize, Crop, Auto-scale)                                  |
| 20, 40 px                  | point tracker defaults: Feature Size, Search Size                                                                |

## Quality gates

- Measurable: keys on every frame of the range; error against a re-track under 1 px mean; no frame
  but the reference with `inliers` 0; `banner` is `none` before a render; stabilized residual under
  0.2 px; scale under the agreed limit; the layer motion blur switch and `comp.motionBlur` on for a
  moving insert, with Position keys present.
- Visual: one contact sheet at the start, the middle, the slip frame and the end. Look for swim
  against the bezel or corners, black borders, the blue or orange banner, a squashed insert, missing
  blur on fast frames, edges brighter or sharper than the plate.

## Common mistakes

| Mistake                                                            | Symptom                                                                  | Fix                                                             |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------ | --------------------------------------------------------------- |
| Analyzer added and rendered in the same job, or by `aerender`      | blue "Analyzing in background" band in the output                        | return control, poll frames with `banner`, render after `none`  |
| Corner Pin with only the layer motion blur switch                  | sharp insert on a blurred plate (identical pixels to blur off, measured) | `cornerPin(..., {motionBlur: true})`                            |
| Corner order copied from a tracker                                 | twisted insert                                                           | Corner Pin is UL, UR, LL, LR; tracks are usually UL, UR, LR, LL |
| Region track on a turning object with a flat part                  | the point slides to a neighbor feature (79 px by frame 60)               | `plane` on the flat part; `slide` catches it                    |
| Planar track on a curved body                                      | quad skews into a trapezoid                                              | `plane` on a flat part, or `shake --corners` and `slide`        |
| Element parented far from a null under perspective                 | slide grows as the plane turns                                           | its own point through `pointsFromCorners`                       |
| Stabilized precomp restored without Collapse Transformations       | black bands where the plate moved                                        | `restoreMotion` switches it on (P15)                            |
| Frame-to-frame track only                                          | slow drift, worst on the last frame                                      | register to a reference frame, or `reanchor`                    |
| Locking a handheld shot completely                                 | 118 % scale-up, soft image                                               | smooth instead; keep the intended move                          |
| Smoothing with one moving average                                  | residual jitter (0.99 px measured)                                       | two passes (`smoothPath`)                                       |
| Mocha data on an insert sized to the comp                          | wrong scale or squashed logo                                             | precomp at tracked footage size (P12), or `cornerPin`           |
| Reading Average Error or Auto-scale by script                      | property names stay "Average Error: -" and "Auto-scale"                  | read them in the GUI; measure from frames                       |
| Changing Solve Method or Shot Type by script and rendering at once | no banner, old solve points still drawn (measured)                       | let the app idle, then re-check; or re-analyze from the GUI     |

## Handoffs

- Receives from scenario-after-effects-project: a comp that matches the footage. From
  scenario-after-effects-generation: insert art at the screen's aspect, treated as raw input.
- Delivers to scenario-after-effects-compositing: the pinned insert and the track (null or Motion
  Tracker) for finger mattes, keys, light wrap and grain. Labels riding a track:
  scenario-after-effects-typography readability gate (procedure 10), contrast sampled from the plate
  behind the label. To scenario-after-effects-3d: a camera and ground plane for models, lights and
  shadow catchers (Advanced 3D is `ADBE Calder`). To scenario-after-effects-animation and
  scenario-after-effects-typography: a null to parent titles to.
- To scenario-after-effects-expressions: `motionTracker()` links when a rig must read the track
  live.

## Version notes

- Warp Stabilizer and the 3D Camera Tracker need idle time; an "Adobe Analysis Server" process runs
  beside the app [added]. No script call starts or waits for the analysis.
- Mocha AE is the effect `mochaAECC`. Its tracking and export run in its own window. It does not
  solve cameras.
- Shadow catchers: 24.5. Mask Tracker up to 5x faster: 26.3. Warp Stabilizer is not allowed in a
  MOGRT that must run without After Effects.

## References

- [references/procedures.md](references/procedures.md): full jobs and commands for every stage, with
  checked lines.
- [references/expert-notes.md](references/expert-notes.md): expert judgment by source and timestamp.
- [references/critique.md](references/critique.md): the rubric with numbers and contact-sheet
  checks.
- [references/gui-paths.md](references/gui-paths.md): Tracker panel, Warp Stabilizer, 3D Camera
  Tracker and Mocha AE in the GUI.
- [references/sources.md](references/sources.md): every source with URL.
- Scripts: [scripts/track.jsx](scripts/track.jsx) (`AEX.track`),
  [scripts/track_external.py](scripts/track_external.py) (OpenCV tracker, point carry, slide and
  marker checks, scorer, banner check).
