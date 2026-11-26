# Expert notes: 3D, cameras and lights

Principles from the sources, grouped by expert, each with video id and timestamp. Lines marked
[added] are this skill's own additions, measured live on After Effects 27.0 unless said.

## Evan Abrams (Adobe Live, M7v547PJ5Hk)

- Set the model units in the Model Settings dialog at import: centimeters against meters is a 100x
  error that breaks camera presets (00:04:35).
- Parent the camera to a null at the subject; animate the null's orientation and the camera's Z for
  a product orbit (00:10:15, 00:12:56).
- Scanned meshes arrive with wrong axes: parent them to a floor null instead of fighting the model's
  own rotation (00:06:55).
- Heavy meshes (about 750k triangles): work in Draft 3D (00:06:18).
- Environment light with an HDR or EXR source, Shadow Darkness around 50 %, then rotate the light to
  place the highlights (00:13:50, 00:14:56).
- Interiors: 24 mm one-node camera and small moves (00:19:07).
- Shift-parent new 3D text to the camera or a null to snap its transform, push it in Z, then
  unparent (00:15:57, 00:22:06).
- The camera's own keys carry only the distance (Z); the null carries orbit, aim and pivots, so
  nothing is keyed on the camera's X, Y or Point of Interest (00:10:15, 00:12:56).
- [added] Script substitute for the units dialog: fit from `sourceRectAtTime`, which on 27.0 ignores
  the layer's rotation and scale and returns the importer's normalized footprint (700x504 for one
  test model at any scale).

## Motion Nations, Abhishek Dubey (65WsmkXZEso, wwsHGbZN6ZU)

- Source the environment light from an EXR, Shadow Darkness about 50 % (65WsmkXZEso 00:02:01); scrub
  its Y rotation while watching reflections (00:03:07, 00:10:48).
- One speed-graph ease shape reused on every scene of a spot (00:04:28, 00:14:18).
- Spin trick for two objects turning the same way: offset one by 180 or 270 degrees (00:13:44).
- Shadow catcher: solid under the model, Accepts Shadows Only; if nothing appears, Fit to Scene in
  the renderer options (wwsHGbZN6ZU 00:05:38, 00:06:10).
- Tint the environment light to the plate's color cast rather than leaving it white (wwsHGbZN6ZU
  00:09:49).
- [added] Measured on 27.0 in Advanced 3D: the environment light's Color is hidden and a Tint on its
  source layer is ignored; a Tint inside a precomp of the source changes the light (procedure 11).
- Hand-animate when a camera track fails on motion blur (wwsHGbZN6ZU 00:08:11).

## Max Novak (QlbZDu2tZfE)

- Interpret the footage frame rate before judging a composite (00:09:12).
- CG over a plate: 0.1 to 0.2 px blur and light grain, shadows matched by sampling RGB in the Info
  panel (00:10:18).
- Pick the HDRI to match the plate before lighting anything (00:04:29).

## Motion Science, Cameron (zgMHWFolli8, u3qluraimKY)

- Move a null, not the camera, for pivots and drift (zgMHWFolli8 00:13:08).
- Camera shake from a null with Frequency and Amplitude sliders driving `wiggle` (00:14:22).
- Motion blur needs the layer switch and the comp switch, tuned in Composition Settings > Advanced
  (00:16:31).
- Fast Rectangle iris; other iris shapes render much slower (00:18:02).
- Link Focus Distance to Layer follows; Set Focus Distance to Layer is a one-time snapshot
  (00:19:15).
- Parallax: paint behind a cut-out only where the move will reveal it (u3qluraimKY 00:06:06).
- [added] In Advanced 3D (27.0) the Iris and Blur Level properties are hidden; Focus Area Width and
  Split Blur Level replace them.

## Ryan Connolly, Film Riot (0oS3FnBwOkI, 9LxKSsftUS4)

- Geometry Options grayed out means the comp is on Classic 3D: switch to Advanced 3D (0oS3FnBwOkI
  00:00:08).
- 3D elements need a 3D background layer to receive light; precompose the background to swap it
  later (0oS3FnBwOkI 00:02:20).
- Match the HDRI to the plate's sun side; rotate the environment light to it (9LxKSsftUS4 00:01:44,
  00:02:15).
- Effects on a model: precompose it with its lights and nulls (00:02:37); depth blur from 3D Channel
  Extract on a duplicate into Camera Lens Blur, map source Effects and Masks (00:03:39).
- Budget the model: plan the shot around the detail the model actually has (00:00:13).

## MDMZ, Mohamed Mehrez (7tVyu-rjHbg)

- Check cut-out edges over a solid red layer (00:04:07).
- Push a layer back in Z, then scale it up until it fills the frame again (00:15:42).
- Anchor at the ground contact, ground plane X Rotation -90, Corner Pin to remove distortion
  (00:16:48 to 00:20:12).
- Motion blur on at both layer and comp level (00:24:26).
- [added] Exact compensation: scale = base x (zoom + z) / zoom, times 1.05 to 1.1 overscan.
  Measured: three layers at z 2000, 600 and -300 all framed at exactly 1056 px (960 x 1.1).

## Jake Bartlett, Jake In Motion (iOZkdYZPVU0, DK04C1mro-U)

- Move the camera rig, not the scene: parent the model to a null, keep the model for local offset
  only (iOZkdYZPVU0 00:07:07).
- Create 3D Layer Instance gives a 2D copy (CC Composite) that takes ordinary effects; renders
  slower (00:14:12).
- Edit the base color texture in an image editor; After Effects reloads it (00:03:58).
- Create Orbit Null for constant drift under the main move (00:12:41).
- Animate the environment light's Y rotation so highlights travel (00:19:26).
- Advanced 3D has no native motion blur: CC Force Motion Blur at 90 to 120 degrees, off until the
  final render (00:20:16).
- Camera tool shortcuts: C cycles, Shift+C twice for Orbit around Point of Interest (00:02:21,
  00:09:30).
- 26.3: Draft 3D for speed while animating, off to judge DoF and shadows (DK04C1mro-U 00:05:33).
- [added] Measured on 27.0: `layer.motionBlur = true` throws in an Advanced 3D comp; CC Force Motion
  Blur on the precomp blurred the model (RMSE 0.146 against the sharp frame).

## Matt Dombrowski (PfVBb4ZEhq8) and TomsProject, Tom Lulofs (XsbXd4pirnE)

- Displacement Map from a depth image: near is white, so invert a map whose near side is dark
  (PfVBb4ZEhq8 00:01:44); blur the map or the background distorts (00:03:07), and choose Effects and
  Masks as the map source so the blur is read (00:03:39).
- Find the largest acceptable stretch, key it, then animate back to zero so the end state is the
  clean image; small amounts are enough (PfVBb4ZEhq8 00:04:11).
- Cut-layer parallax from a still: one-node 50 mm camera, layers separated in Z, the front layer
  rescaled to refill the frame (XsbXd4pirnE 00:05:35 to 00:06:43); smoke and flare as 3D layers at
  the front layer's Z so they move with the scene (00:08:46).
- [added] A script cannot pick Effects and Masks: on 27.0 the effect read the map's source and
  ignored its blur (doubled edges at 15 px). Precompose the blurred depth layer instead.

## Own additions [added]

- Renderer internal names on 27.0: `ADBE Advanced 3d` is Classic 3D, `ADBE Calder` is Advanced 3D,
  `ADBE Ernst` is Cinema 4D. A comp made by script starts on Classic 3D, and adding a model does not
  switch it.
- Set Advanced 3D before adding an environment light with a layer source: the same setup on Classic
  3D crashed the application twice.
- Warm up: the first frame rendered after building a scene can come back without the model; render
  one throwaway frame first (2.4 to 4.1 s), later frames about 255 ms at 960x540.
- Focus on the middle of the subject's footprint, not its anchor at the base; give Focus Area Width
  about 150 so the whole product stays sharp.
- Materials of a model on 27.0 (measured in Advanced 3D): Roughness, Metallic, Opacity, Emission,
  Emission Intensity and Ambient are readable, but `setValue`, keys and expressions throw "hidden";
  texture offset, rotation and scale accept values. Material edits are GUI work until the material
  scripting APIs of the 27.1 beta ship.
