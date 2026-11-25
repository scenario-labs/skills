# GUI paths for the same procedures (After Effects 27.0, macOS shortcuts; Windows: Cmd = Ctrl, Opt = Alt)

## Renderer and quality

- Renderer: Composition > Composition Settings > 3D Renderer tab > Renderer: Classic 3D, Advanced
  3D, Cinema 4D. The menu shows these display names; a script sees `ADBE Advanced 3d` (Classic 3D),
  `ADBE Calder` (Advanced 3D), `ADBE Ernst` (Cinema 4D).
- Advanced 3D render options: Composition Settings > 3D Renderer > Options: Render Quality slider;
  Shadows: Resolution Half (2 MB), Full (16 MB), Double (128 MB); Smoothness 1 to 32 (default 3;
  keep low, raise Render Quality first); Casting Box Size and Center (a larger box spreads the
  shadow resolution, so shadows get softer); Fit to Scene (use when shadows do not appear). Not
  reachable by script.
- Draft 3D: toggle in the Composition panel toolbar; use it while blocking a heavy mesh (about 750k
  triangles, M7v547PJ5Hk 00:06:18); gives 3D Ground Plane and Extended Viewer. Work in Draft 3D
  while animating, turn it off to judge DoF and shadows (DK04C1mro-U 00:05:33). Not settable by
  script.
- Fast Previews > Adaptive Resolution also applies to 3D.

## Models

- File > Import > File (Cmd+I) for GLB, glTF, OBJ, FBX. Dragging onto the timeline opens Model
  Settings at first import: Object Scale, Make Comp Size, units under Advanced, axis flip
  (M7v547PJ5Hk 00:04:35). If a dialog says 3D models require the Advanced 3D renderer, accept the
  switch.
- Embedded animation: layer > Animation Options > Name (pick the clip).
- Materials: Properties panel > Material (Roughness, Metallic, Emission, Opacity, projection,
  texture offset, rotation, scale). Substance: import a .sbsar, then Properties panel > Material, or
  Layer > Material > Get Substance Community Assets. Duplicate and Assign Material for a per-layer
  change. On 27.0 this panel is the only way to change Roughness, Metallic, Opacity, Emission and
  Ambient: a script reads them but cannot set, key or drive them by expression.
- Effects on a model: Layer > Create > Create 3D Layer Instance (2D layer with CC Composite on the
  hidden 3D layer, iOZkdYZPVU0 00:14:12), or Layer > Pre-compose with lights, nulls and HDRI layers
  included (9LxKSsftUS4 00:02:37).
- Parametric meshes: the Parametric Mesh tool in the toolbar (cube, sphere, cylinder, cone, torus,
  plane).

## Lights

- Layer > New > Light (Cmd+Opt+Shift+L): Light Type Parallel, Spot, Point, Ambient, Environment;
  Casts Shadows checkbox.
- Environment: Light Options > Source = the HDR, EXR, video or comp layer (the layer's visibility
  turns off). Layer > Light > Create Environment Light Background Layer makes a solid with CC
  Environment and a 5 px Fast Box Blur.
- Rotate the environment light: select it, R, scrub Y Rotation while watching reflections
  (65WsmkXZEso 00:03:07); keyframe it over about 5 s so highlights travel (iOZkdYZPVU0 00:19:26).
- Tint the environment light to the plate: Light Color is hidden for it in Advanced 3D; precompose
  its source layer, add Effect > Color Correction > Tint inside at a low amount (about 20 %), and
  point Light Options > Source at the precomp (wwsHGbZN6ZU 00:09:49).
- Layer > Light > Control Light with Camera.
- Material Options on a layer: AA reveals them; Opt+Shift+C toggles Casts Shadows; Accepts Shadows
  On, Off, Only (shadow catcher); Accepts Lights off for screens and neon.

## Cameras

- Layer > New > Camera (Cmd+Opt+Shift+C): One-Node or Two-Node, presets 15, 20, 24, 28, 35, 50, 80,
  135, 200 mm, Film Size 36 mm, Depth of Field, Focus Distance, Aperture, F-Stop, Blur Level.
- Shift-parent: Shift-drag a new 3D text's parent pick whip to the camera or rig null to snap it
  there, push it in Z, then set Parent to None (M7v547PJ5Hk 00:15:57, 00:22:06).
- Layer > Camera: Link Focus Distance to Point of Interest, Link Focus Distance to Layer (follows),
  Set Focus Distance to Layer (one time), Create Orbit Null, Create Stereo 3D Rig.
- Camera tools: C cycles Orbit, Track XY, Track Z; Shift+C twice for Orbit around Point of Interest;
  Shift-drag with Pan moves position and point of interest together; apostrophe shows the comp
  center (iOZkdYZPVU0 00:02:21, 00:09:30).
- Views: Composition panel > 3D View popup (Active Camera, Front, Left, Top, Custom Views); 2 Views
  or 4 Views layout; View > Look at Selected Layers; View > Reset 3D View.
- Layer > Transform > Auto-Orient (Opt+Cmd+O): Off makes a one-node camera; Orient Along Path;
  Orient Towards Point of Interest.

## Motion blur

- Layer switch (the Motion Blur column) plus the comp Motion Blur button; Composition Settings >
  Advanced: Shutter Angle, Shutter Phase, Samples Per Frame, Adaptive Sample Limit (zgMHWFolli8
  00:16:31). Advanced 3D refuses the layer switch: Effect > Time > CC Force Motion Blur on a
  precomp.

## Depth tools

- Effect > 3D Channel > 3D Channel Extract, Depth Matte, Depth of Field, Fog 3D on a precomp of the
  3D scene.
- Effect > Blur & Sharpen > Camera Lens Blur with Blur Map Layer = depth layer, source Effects and
  Masks (9LxKSsftUS4 00:03:39).
- Effect > Distort > Displacement Map: Displacement Map Layer popup has a Source / Effects and Masks
  choice (PfVBb4ZEhq8 00:03:39); scripts cannot set it, so precompose the map instead.

## 2.5D

- File > Import > File, Import As: Composition, Retain Layer Sizes for a layered PSD.
- 3D Layer switch on each layer; Anchor Point tool (Y) to put the anchor at the ground contact
  (7tVyu-rjHbg 00:20:12); Effect > Distort > Corner Pin to fix a ground plane; a red solid
  underneath to check cut-out edges (7tVyu-rjHbg 00:04:07).
- Rendering: Composition > Add to Render Queue (Ctrl+M on Windows, Cmd+Ctrl+M on macOS), or aerender
  on a saved project.
