---
name: scenario-after-effects-3d
description: "Use when building 3D in After Effects: importing a GLB or FBX model, fitting it, product orbits, HDRI environment light, shadow catcher, floor and reflection, extruded text, camera rigs, depth of field, motion blur, choosing Classic or Advanced 3D, or 2.5D parallax from a still. Also when the model is off-center or missing, the shadow is gone, Geometry Options are grayed out, or it renders blurry."
license: MIT
---

# After Effects 3D: models, cameras, lights and 2.5D

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means the renderer is chosen on purpose, the model is fitted by numbers before
anything moves, the camera rides a null, and every shot is judged on rendered frames because the 3D
viewer lies. If a sibling skill named here is missing from your available skills, load it with
`skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

**REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit, version
traps).

## Stance (the expert delta)

1. **Set the renderer by its internal name, and know which name is which.** Measured on 27.0:
   `ADBE Advanced 3d` is Classic 3D, `ADBE Calder` is Advanced 3D, `ADBE Ernst` is Cinema 4D. A comp
   made by script is Classic 3D, and adding a model by script does not switch it. Geometry Options
   grayed out means the wrong renderer (Film Riot 0oS3FnBwOkI 00:00:08).
2. **Advanced 3D for models, extrusion, Substance and shadow color; Classic 3D for flat 2.5D
   layers.** Classic renders cut-out layers just as fast (254 against 255 ms per frame) and keeps
   layer motion blur [added, measured].
3. **Fit before you animate.** Real-world units decide how a 50 mm or 24 mm lens behaves (Evan
   Abrams M7v547PJ5Hk 00:04:35). By script, `sourceRectAtTime` gives the model's front footprint at
   scale 100; it ignores rotation and scale. Scale to a target height, put the anchor at the base,
   stand it on the floor.
4. **The camera rides a null: orbit and aim on the null, the push on the camera's own Z** (Abrams
   00:10:15, 00:12:56; Jake Bartlett iOZkdYZPVU0 00:07:07). Nothing is keyed on the model, on the
   camera's Position X and Y, or on its Point of Interest.
5. **The HDRI is the light; the spot is the shadow.** Environment light for reflections and form
   (Abrams 00:14:56), its own shadows off. A shadow-casting spot or parallel light for a readable
   contact shadow; a 3D solid with Accepts Shadows Only as catcher (Motion Nations wwsHGbZN6ZU
   00:05:38; Ryan Connolly 9LxKSsftUS4 00:03:07). Match both to the plate's sun side and color
   (wwsHGbZN6ZU 00:09:49).
6. **Focus on the middle of the subject, with a focus area.** Advanced 3D depth of field keeps only
   one plane sharp at Focus Area Width 0 (Jake Bartlett DK04C1mro-U 00:04:31). Measured: focus on
   the base left the product soft; the footprint middle with Focus Area Width 150 kept it sharp.
7. **Motion blur on a model goes through a precomp.** Advanced 3D has no native motion blur
   (Bartlett iOZkdYZPVU0 00:20:16); CC Force Motion Blur on the precomp, off until the final render.
   Measured on 27.0: Advanced 3D refuses the layer switch; a model in a Classic comp stays sharp.
8. **2.5D is depth plus scale compensation, and only what the camera reveals needs paint** (MDMZ
   7tVyu-rjHbg 00:15:42; Motion Science u3qluraimKY 00:06:06). Scale = base x (zoom + z) / zoom
   keeps a layer's framed size exactly (measured 1056 px at three depths).

## Establish first

| Input                               | Why it changes the plan                                                             | Default                                  |
| ----------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------- |
| Deliverable size, fps, length       | camera zoom, motion blur samples, render time                                       | 1920x1080, 24 or 30 fps; test at 960x540 |
| Source: model file, still, or plate | Advanced 3D model shot, or 2.5D in Classic 3D                                       | model: GLB; still: layers or depth map   |
| Live plate or graphic background    | tracked camera and shadow catcher, or free camera                                   | graphic background                       |
| Renderer needs                      | extrusion, shadow color, Substance, models: Advanced 3D; layer motion blur: Classic | Advanced 3D for models                   |
| Channel                             | bridge for build and frames; aerender for the final                                 | bridge                                   |
| Generated inputs                    | model, HDRI, plate, depth map from scenario-after-effects-generation                | ask before generating                    |

## Procedure

Full jobs are in [references/procedures.md](references/procedures.md). Helpers: `scripts/threed.jsx`
(`AEX.threeD`), loaded with `ae.py run job.jsx --lib <skill>/scripts/threed.jsx`.

### 1. Comp and renderer

Goal: the comp renders what the shot needs. Build it with
`AEK.build.comp(name, {renderer: "advanced"})`, or call `AEX.threeD.use(c, "advanced")` before
adding any model or light; both set `ADBE Calder`. In the GUI: Composition Settings > 3D Renderer.
GATE: `AEX.threeD.rendererName(c)` returns `advanced`; `ADBE Extrsn Depth` on a 3D text accepts a
value.

### 2. Bring the asset in

Goal: the model is a layer. `AEK.xio.importItem` returns the item; in a comp it becomes
`ADBE 3D Model Layer`.

- Units: set them in the GUI Model Settings dialog at import; centimeters against meters is a 100x
  error that breaks camera presets (Abrams 00:04:35). By script, `fitModel` sets the size.
- Heavy mesh: test at 960x540.
- Materials sit under `ADBE3D Material Parade` by name. On 27.0 Roughness, Metallic, Opacity,
  Emission and Ambient refuse `setValue`, keys and expressions ("hidden"). A product that reads as
  soft plastic: lower the hard parts' roughness in a copy of the GLB with
  [glb_material.py](scripts/glb_material.py) before import (procedure 13), or edit in Properties
  panel > Material. GATE: `matchName` is `ADBE 3D Model Layer`; `sourceRectAtTime(0, false)` is
  non-zero.

### 3. Fit and ground

Goal: right size, centered, standing on the floor.
`AEX.threeD.fitModel(layer, comp, {height, x, floorY, rotateY})`: anchor at the footprint's bottom
center, scale = height / rect height x 100. For scans with odd axes, parent to a null at the floor
point (Abrams 00:06:55). GATE: the base sits on the floor line on a rendered frame; widthPx and
heightPx fit the frame with a margin; the product's matte, not the null, is centered (a strap counts
in the footprint).

### 4. Light, shadow and catcher

Goal: believable shading and a contact shadow. Environment light:
`AEX.threeD.envLight(c, {intensity, source})`, source an EXR or HDR item. Key:
`AEX.threeD.keyLight(c, position, target, {type: "SPOT", darkness, diffusion})`. Catcher:
`AEX.threeD.shadowCatcher(c, floorY, {shadowColor})`, moved above the plate. Shadow Darkness 50 %
keeps shadows from going black (Abrams 00:13:50). Rotate the environment light to place highlights
(Motion Nations 65WsmkXZEso 00:10:48), then key its Y Rotation across the shot so they travel
(Bartlett iOZkdYZPVU0 00:19:26). Tint it to the plate's color cast with a tint inside a precomp of
its source (wwsHGbZN6ZU 00:09:49; procedure 11). Product on a visible floor (procedure 12):
`AEX.threeD.floor` in one flat color (the pool comes from the spot), `contactShadow` under the base
(Advanced 3D draws no ambient occlusion), `reflection` for a mirrored copy that blurs and fades with
distance. GATE: the shadow lands on the plate, falling away from its sun; no white floor visible; on
a floor, a dark contact band under the base. No far edge: tilt past half the vertical field of view
(11.4 degrees at 50 mm) and size the floor to reach the top ray (procedure 12). If no shadow appears
in the GUI, Renderer Options > Fit to Scene (wwsHGbZN6ZU 00:06:10).

### 5. 3D text behind the product

Goal: a title with depth that never cuts through the model. Text layer 3D, anchor at its base, Z
behind the product, `ADBE Extrsn Depth` 20 to 300 and `ADBE Bevel Styles` in Advanced 3D (Film Riot
uses 300 at 00:00:39). Lay out before animating the camera: write what must read at the first,
middle and last frame, then check it on mattes (procedure 15). GATE: `AEX.threeD.mattes` plus
[scripts/layout_check.py](scripts/layout_check.py) at those three frames: the title 90 % visible or
more and inside the frame; no letter intersects the model.

### 6. Camera rig and move

Goal: a smooth orbit and push.
`AEX.threeD.orbitRig(c, center, {focalLength, distance, tilt, from, to, push, influence | bezier})`:
a 3D null at the subject, a one-node camera parented to it, Y rotation on the null, the push on the
camera. Leave `height` out: the camera then sits at distance x tan(-tilt) and pushes along its view
line, so the subject stays centered (measured: height 0 at tilt -9 put it 211 px high).
`bezier: [0.25, 0, 0.35, 1]` spreads the move; [0.3, 0, 0.12, 1] spends it in the first two seconds.
Lens: 50 mm for objects, 24 mm for interiors (Abrams 00:19:07). Constant drift: Create Orbit Null
([gui-paths](references/gui-paths.md)). GATE: `AEX.threeD.screenPoint` of the null reads the comp
center at both ends; no linear key; no frame crops the product. `AEX.threeD.parallax` of the subject
against a far reference: 25 % of comp width or more over the shot, 3 % or more per 1 s window except
a final hold.

### 7. Depth of field

Goal: subject sharp, background soft, focus follows the subject.
`AEX.threeD.focusOn(camera, "product", {aperture, areaWidth})` writes a Focus Distance expression to
the middle of the footprint. Advanced 3D adds Focus Area Width and Near/Far Blur Level; Classic 3D
keeps Blur Level and iris. GATE: Focus Distance expression has no `expressionError`; the subject is
sharp on the middle frame. Text that must read: [scripts/focus_check.py](scripts/focus_check.py) on
its mattes with depth of field off and on, Gaussian radius 2 px or less at 1080 lines on every
sampled frame. Over it, rack the focus (`focusOn` option `rack`) or lower the aperture (procedure
15).

### 8. Motion blur

Goal: blur that matches the move. Advanced 3D: CC Force Motion Blur on the precomp layer in an outer
comp (samples 8, shutter 90 to 180, iOZkdYZPVU0 00:20:16), off while iterating. Classic 3D: layer
switch plus comp switch (7tVyu-rjHbg 00:24:26). GATE: a frame of the fastest move shows directional
smear; a frame of a still moment does not.

### 9. Render and judge

Goal: the shot holds on real frames. Render one warm-up frame and discard it (`AEX.threeD.warmUp`):
the first frame of a new scene can come back without the model. Then three frames on one sheet
(`ae.py sheet`), then `ae.py aerender` on the saved project. Grain over the render: `ADBE Noise`
with Clipping (`-0003`) at 1. Plate integration: [critique](references/critique.md) item 10. GATE:
checks in [references/critique.md](references/critique.md); `ae.py probe` on the output.

### 10. 2.5D from a still

Goal: a camera move from one image. Layers route: planes from scenario-after-effects-generation
(depth thresholds, clean plates behind) in a Classic 3D comp, each pushed in Z, scale by
`AEX.threeD.parallaxScale(base, z, zoom, 1.06 to 1.1)`, camera push with eased keys. Cap the push
with `AEX.threeD.maxPush` so the foreground stays in frame through the hold; sway a plane with Wave
Warp, Pinning 8 (procedure 14). Depth-map route: Displacement Map with the depth layer PRECOMPOSED
with its blur, amount keyed from the maximum back to 0 (Matt Dombrowski PfVBb4ZEhq8 00:04:11). GATE:
`screenRect` of every layer covers the frame at the last key; the foreground's inner edge stays 60
px inside it (`screenPoint`); no doubled edges at the maximum displacement.

## Numbers

Px values are for a 960 px comp: multiply by comp width / 960. The rest (lenses, camera height,
contact shadow, push cap, light, shadow, DoF, motion blur, displacement, frame time):
[critique](references/critique.md) section 4.

| Value          | Number                                  | Relative to                                  |
| -------------- | --------------------------------------- | -------------------------------------------- |
| Camera zoom    | comp width x focal length / 36          | 50 mm: 1333.3 px at 960 wide, 2666.7 at 1920 |
| Model fit      | height 40 to 60 % of comp height        | measured footprint at scale 100              |
| Orbit          | 30 to 70 degrees over 3 s               | null Y rotation, eased 33 to 50 % influence  |
| Push           | 150 to 300 px on camera Z over the shot | camera distance 900 to 1100 px               |
| Parallax scale | base x (zoom + z) / zoom x 1.1 overscan | camera at z = -zoom                          |

## Quality gates

Measurable: the GATE lines above and [critique](references/critique.md) section 1. Visual, on one
sheet: product centered and uncropped, title readable, base on its shadow, shadow and highlights on
the plate's sun side, no white catcher, no floor edge, subject sharp, smear only on fast frames.

## Common mistakes

More rows (fit by eye, focus at the base, scripted materials, Z push without scale):
[critique](references/critique.md) section 5.

| Mistake                                                    | Symptom                                                            | Fix                                                              |
| ---------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| Trusting `ADBE Advanced 3d` as Advanced 3D                 | no extrusion, shadow color ignored, first frame without the model  | `c.renderer = "ADBE Calder"`                                     |
| Environment light with a layer source in a Classic 3D comp | After Effects crashes at render (measured twice)                   | Advanced 3D first, then the source; the helper refuses otherwise |
| Layer motion blur in Advanced 3D                           | "Motion blur is not supported by the current composition renderer" | CC Force Motion Blur on a precomp                                |
| Keys on camera Position X or Point of Interest             | wobbly orbit, pivot drifts                                         | orbit on the null; push on the camera                            |
| Tilted camera at height 0                                  | subject high in frame, drifts during the push                      | `orbitRig` without `height`                                      |
| Product on a floor with spot shadows only                  | floats above the floor                                             | `contactShadow`; reflection for gloss                            |
| Push past `maxPush`                                        | the foreground leaves before the hold                              | cap the push or lower the camera                                 |

## Handoffs

- Receives models, HDRIs, plates, layer separations and depth maps from
  scenario-after-effects-generation.
- Receives a solved camera and track from scenario-after-effects-tracking (3D Camera Tracker is GUI
  work).
- Gives camera and null expression rigs to scenario-after-effects-expressions; easing detail to
  scenario-after-effects-animation.
- Gives the finished 3D precomp to scenario-after-effects-compositing (light wrap, grain, color
  match) and scenario-after-effects-color-delivery (output).
- 3D text design and per-character 3D: scenario-after-effects-typography.

## Version notes

- Advanced 3D gained spot and parallel shadows in 26.0, depth of field in 26.3; material scripting
  in the 27.1 beta. By version: [procedures](references/procedures.md) 16.

## References

- [references/procedures.md](references/procedures.md): every job, with channel, checked line and
  the check that follows; version table.
- [scripts/threed.jsx](scripts/threed.jsx) (`AEX.threeD`) and
  [scripts/glb_material.py](scripts/glb_material.py) (GLB material factors).
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps.
- [references/critique.md](references/critique.md): the self-review rubric with numbers and
  contact-sheet checks.
- [references/gui-paths.md](references/gui-paths.md): menus, panels, shortcuts and the settings
  scripts cannot reach.
- [references/sources.md](references/sources.md): every video and document used.
