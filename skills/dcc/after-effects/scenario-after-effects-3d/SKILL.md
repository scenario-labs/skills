---
name: scenario-after-effects-3d
description: "Use when building 3D in After Effects: importing a GLB, glTF, OBJ or FBX model, a product shot or orbit, fitting and centering a model, environment light from an HDRI or EXR, shadow catcher on a plate, spot or parallel shadows, extruded 3D text, cameras, null camera rigs, depth of field, motion blur on 3D, choosing Classic 3D, Advanced 3D or Cinema 4D renderer, materials, or 2.5D parallax from a still with layers or a depth map. Also when someone says the model is off-center or huge, the model does not show, the shadow is missing, Geometry Options are grayed out, motion blur does not work on my model, everything is blurry with depth of field, the HDRI does nothing, After Effects crashed on render, or make a camera move around the product."
license: MIT
---

# After Effects 3D: models, cameras, lights and 2.5D

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means the renderer is chosen on purpose, the model is fitted by numbers before
anything moves, the camera rides a null, and every shot is judged on rendered frames because the 3D
viewer lies. The stance: renderer first, scale second, light third, camera fourth, proof last. If a
sibling skill named here is missing from your available skills, load it with `skill_get` (Scenario
MCP) or ask the user to install it (https://github.com/scenario-labs/skills#install); unattended,
proceed from tool schemas and flag the gap.

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
   camera's Position X and Y, or on its Point of Interest. "Externalized control gives you much
   smoother movements" (Abrams 00:12:56).
5. **The HDRI is the light; the spot is the shadow.** Environment light for reflections and form
   (Abrams 00:14:56), a shadow-casting spot or parallel light for a readable contact shadow, a 3D
   solid with Accepts Shadows Only as catcher (Motion Nations wwsHGbZN6ZU 00:05:38; Ryan Connolly
   9LxKSsftUS4 00:03:07). Match the HDRI and the shadow to the plate's sun side and color
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

Full jobs are in [references/procedures.md](references/procedures.md). Helpers:
[scripts/threed.jsx](scripts/threed.jsx) (`AEX.threeD`), loaded with
`ae.py run job.jsx --lib <skill>/scripts/threed.jsx`.

### 1. Comp and renderer

Goal: the comp renders what the shot needs. Build it with
`AEK.build.comp(name, {renderer: "advanced"})`, or call `AEX.threeD.use(c, "advanced")` before
adding any model or light; both set `ADBE Calder`. In the GUI: Composition Settings > 3D Renderer.
GATE: `AEX.threeD.rendererName(c)` returns `advanced`; `ADBE Extrsn Depth` on a 3D text accepts a
value.

### 2. Bring the asset in

Goal: the model is a layer. `AEK.xio.importItem` returns the item; in a comp it becomes
`ADBE 3D Model Layer`. A generated model (scenario-after-effects-generation) is raw input that needs
this fit and a material check.

- Units: set them in the GUI Model Settings dialog at import; centimeters against meters is a 100x
  error that breaks camera presets (Abrams 00:04:35). By script, `fitModel` sets the size.
- Heavy mesh (about 750k triangles): a person blocks the move in Draft 3D (Abrams 00:06:18); a
  script cannot set it, so test at 960x540.
- Materials sit under `ADBE3D Material Parade` by name. Measured on 27.0, Advanced 3D: Roughness,
  Metallic, Opacity, Emission and Ambient refuse `setValue`, keys and expressions ("hidden");
  texture offset, rotation and scale accept values. Edit materials in Properties panel > Material.
  GATE: the layer's `matchName` is `ADBE 3D Model Layer`; `sourceRectAtTime(0, false)` returns a
  non-zero rect.

### 3. Fit and ground

Goal: right size, centered, standing on the floor.
`AEX.threeD.fitModel(layer, comp, {height, x, floorY, rotateY})`: anchor at the footprint's bottom
center, scale = height / rect height x 100. For scans with odd axes, parent to a null at the floor
point (Abrams 00:06:55). GATE: the base sits on the floor line on a rendered frame; widthPx and
heightPx fit the frame with a margin.

### 4. Light, shadow and catcher

Goal: believable shading and a contact shadow. Environment light:
`AEX.threeD.envLight(c, {intensity, source})`, source an EXR or HDR item. Key:
`AEX.threeD.keyLight(c, position, target, {type: "SPOT", darkness, diffusion})`. Catcher:
`AEX.threeD.shadowCatcher(c, floorY, {shadowColor})`, moved above the plate. Shadow Darkness 50 %
keeps shadows from going black (Abrams 00:13:50). Rotate the environment light to place highlights
(Motion Nations 65WsmkXZEso 00:10:48), then key its Y Rotation across the shot so they travel
(Bartlett iOZkdYZPVU0 00:19:26). Tint it to the plate's color cast with a tint inside a precomp of
its source (wwsHGbZN6ZU 00:09:49; procedure 11). GATE: the shadow lands on the plate, falling away
from its sun; no white floor visible. If no shadow appears in the GUI, Renderer Options > Fit to
Scene (wwsHGbZN6ZU 00:06:10).

### 5. 3D text behind the product

Goal: a title with depth that never cuts through the model. Text layer 3D, anchor at its base, Z
behind the product, `ADBE Extrsn Depth` 20 to 300 and `ADBE Bevel Styles` in Advanced 3D (Film Riot
uses 300 at 00:00:39). GATE: on frames at the start, middle and end of the move, no letter
intersects the model.

### 6. Camera rig and move

Goal: a smooth orbit and push.
`AEX.threeD.orbitRig(c, center, {focalLength, distance, height, tilt, from, to, push, influence})`:
a 3D null at the subject, a one-node camera parented to it, Y rotation on the null, only Z keyed on
the camera, all keys eased. Lens: 50 mm for objects, 24 mm for interiors (Abrams 00:19:07). Constant
drift under the main move: Layer > Camera > Create Orbit Null (GUI, iOZkdYZPVU0 00:12:41). GATE:
`AEK.motion.sample` on the null's Y rotation shows no linear key; no frame crops the product.

### 7. Depth of field

Goal: subject sharp, background soft, focus follows the subject.
`AEX.threeD.focusOn(camera, "product", {aperture, areaWidth})` writes a Focus Distance expression to
the middle of the footprint. Advanced 3D adds Focus Area Width and Near/Far Blur Level; Classic 3D
keeps Blur Level and iris (Fast Rectangle is fast, zgMHWFolli8 00:18:02). GATE: Focus Distance
expression has no `expressionError`; the subject is sharp on the middle frame.

### 8. Motion blur

Goal: blur that matches the move. Advanced 3D: precompose the 3D comp, put CC Force Motion Blur on
the precomp layer in an outer comp (samples 8, shutter 90 to 180, iOZkdYZPVU0 00:20:16), keep it off
while iterating. Classic 3D: layer switch plus comp switch (7tVyu-rjHbg 00:24:26). GATE: a frame of
the fastest move shows directional smear; a frame of a still moment does not.

### 9. Render and judge

Goal: the shot holds on real frames. Render one warm-up frame and discard it (`AEX.threeD.warmUp`):
the first frame of a new scene can come back without the model. Then three frames on one sheet
(`ae.py sheet`), then `ae.py aerender` on the saved project. Render Quality, Smoothness and the
casting box are GUI-only (Composition Settings > 3D Renderer > Options). Over a live plate, finish
the CG: Fast Box Blur 0.1 to 0.2, light grain, shadow RGB matched to the plate's shadows in the Info
panel (Max Novak QlbZDu2tZfE 00:10:18). GATE: checks in
[references/critique.md](references/critique.md); `ae.py probe` on the output.

### 10. 2.5D from a still

Goal: a camera move from one image. Layers route: cut-outs (foreground, middle, background) in a
Classic 3D comp, each pushed in Z, scale by `AEX.threeD.parallaxScale(base, z, zoom, 1.1)`, camera
push with eased keys, verify coverage with `AEX.threeD.screenRect`. Depth-map route: Displacement
Map on the image with the depth layer PRECOMPOSED with its blur, amount keyed from the maximum back
to 0 (Matt Dombrowski PfVBb4ZEhq8 00:04:11). A ground plane: anchor at the contact line, X Rotation
-90, stretch Y, Corner Pin out the remaining distortion (7tVyu-rjHbg 00:16:48 to 00:19:02). GATE:
every layer still covers the frame at the last key (screenRect left 0 or less, right comp width or
more); no doubled edges at the maximum displacement.

## Numbers

| Value                | Number                                                            | Relative to                                  |
| -------------------- | ----------------------------------------------------------------- | -------------------------------------------- |
| Camera zoom          | comp width x focal length / 36                                    | 50 mm: 1333.3 px at 960 wide, 2666.7 at 1920 |
| Lenses               | 50 mm product, 80 mm tight product, 24 mm interior                | 36 mm film back                              |
| Model fit            | height 40 to 60 % of comp height                                  | measured footprint at scale 100              |
| Orbit                | 30 to 70 degrees over 3 s                                         | null Y rotation, eased 33 to 50 % influence  |
| Push                 | 150 to 300 px on camera Z over the shot                           | camera distance 900 to 1100 px               |
| Environment light    | intensity 60 to 135 %                                             | Connolly 135 % (9LxKSsftUS4 00:02:28)        |
| Shadow Darkness      | 50 to 70 %                                                        | 50 % Abrams, 100 % default                   |
| Shadow Diffusion     | 10 to 20 px for a contact shadow                                  | spot or point light                          |
| DoF aperture         | 40 to 120 px with Focus Area Width 100 to 200                     | Advanced 3D, 960 px comp                     |
| CC Force Motion Blur | samples 8, shutter 90 to 180 degrees                              | per frame                                    |
| Parallax scale       | base x (zoom + z) / zoom x 1.1 overscan                           | camera at z = -zoom                          |
| Depth displacement   | 15 to 40 px, keyed to 0                                           | 960 px wide frame                            |
| Frame time           | first 2.4 to 4.1 s, then about 255 ms; aerender 72 frames in 99 s | 960x540, Advanced 3D                         |

## Quality gates

Measurable: renderer name, model count, fit numbers, catcher `ADBE Accepts Shadows` 2, key
`ADBE Casts Shadows` 1, eased keys with none on camera X, Y or Point of Interest, Focus Distance
without `expressionError`, motion blur path, output probe. Visual, on one sheet: product centered
and uncropped, base on its shadow, shadow and highlights on the plate's sun side, no white catcher,
no text through the model, subject sharp, smear only on fast frames.

## Common mistakes

| Mistake                                                                       | Symptom                                                            | Fix                                                              |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| Trusting `ADBE Advanced 3d` as Advanced 3D                                    | no extrusion, shadow color ignored, first frame without the model  | `c.renderer = "ADBE Calder"`                                     |
| Environment light with a layer source in a Classic 3D comp                    | After Effects crashes at render (measured twice)                   | Advanced 3D first, then the source; the helper refuses otherwise |
| Layer motion blur in Advanced 3D                                              | "Motion blur is not supported by the current composition renderer" | CC Force Motion Blur on a precomp                                |
| Focus on the anchor at the base                                               | whole product soft                                                 | aim at the footprint middle, Focus Area Width 100 to 200         |
| Model scaled by eye                                                           | off-center, huge                                                   | `fitModel` from `sourceRectAtTime`                               |
| Keys on camera Position X, Y or Point of Interest                             | wobbly orbit, pivot drifts                                         | orbit on the null; only Z on the camera                          |
| Material values set by script on 27.0                                         | "property is hidden" error                                         | Properties panel > Material                                      |
| Tinting the environment light by Light Color or an effect on its source layer | Color hidden in Advanced 3D; the effect is ignored                 | precompose the source, tint inside                               |
| Blur on the depth layer                                                       | doubled edges at 15 px displacement                                | precompose the depth layer with its blur                         |
| Z push without scale                                                          | layers shrink, frame edges show                                    | scale x (zoom + z) / zoom                                        |
| Judging the first frame                                                       | model missing                                                      | warm-up frame first                                              |
| 2D background in a lit 3D scene                                               | lights ignore it (0oS3FnBwOkI 00:02:20)                            | make it 3D, or keep it 2D at the bottom as a plate               |

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

- Advanced 3D final quality from 24.1; OBJ 24.2; shadow catcher and embedded animation 24.5; Accepts
  Lights 25.1; FBX and animated environment lights 25.2; spot and parallel shadows 26.0; parametric
  meshes 26.0 (script 26.3); DoF in Advanced 3D 26.3; Substance on text and shapes and layers as
  material sources 27.0; material scripting APIs arrive in the 27.1 beta.
- Picking a model's embedded animation clip is GUI-only on 27.0 (`ADBE ModelAnimName` is not a
  property).
- Tutorials before 25.2 say FBX cannot be imported; before 26.3 they fake DoF with Camera Lens Blur.

## References

- [references/procedures.md](references/procedures.md): every job, with channel, checked line and
  the check that follows.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps.
- [references/critique.md](references/critique.md): the self-review rubric with numbers and
  contact-sheet checks.
- [references/gui-paths.md](references/gui-paths.md): menus, panels, shortcuts and the settings
  scripts cannot reach.
- [references/sources.md](references/sources.md): every video and document used.
