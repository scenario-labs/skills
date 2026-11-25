# GUI paths: landing generated media by hand (After Effects 27.0)

For a person, or a computer-use agent, doing the same steps as the procedures.

## Import and interpret

- Import: File > Import > File (Cmd+I / Ctrl+I). A JSON file imports as footage too.
- Alpha: select the footage in the Project panel > File > Interpret Footage > Main (Cmd+Alt+G /
  Ctrl+Alt+G) > Alpha: Straight - Unmatted, or Premultiplied - Matted With Color (pick white for a
  file flattened on white).
- Frame rate: same dialog > Frame Rate > Assume this frame rate.
- Provenance: Project panel > Comment column (right-click the column header > Columns > Comment); on
  a layer, the Comment column of the Timeline panel.

## Cutouts

- Body alpha lift: Effect > Color Correction > Levels (Individual Controls) > Channel: Alpha > Alpha
  Input White 0.98 (about 250 of 255).
- Edge: Effect > Matte > Simple Choker > Choke Matte 1.
- Anchor at the feet: Pan Behind tool (Y), Cmd-drag snaps to layer edges; or the Anchor Point values
  in the Transform group.
- Size check: Window > Info shows the layer size; Scale above 105 % means enlarged pixels.

## Upscale and finish

- Effect > Distort > Detail-preserving Upscale > Fit to Comp Width or Height.
- Grain: Layer > New > Solid (black) > Effect > Noise & Grain > Add Grain > Viewing Mode: Final
  Output, Monochromatic on; Mode column: Screen.
- Vignette: black solid > Ellipse tool double-click > mask Inverted, Feather about 30 % of the
  width > Opacity about 50 %.

## Loops and time

- Time remap: Layer > Time > Enable Time Remapping (Cmd+Alt+T / Ctrl+Alt+T). Alt-click the
  stopwatch > `loopOut("cycle")`.
- Crossfade loop: duplicate the layer, slide the copy so its tail covers the first frames, fade its
  Opacity out over 6 frames, precompose both.
- Frame blending for slow clips: Layer > Frame Blending > Pixel Motion.
- Speed up a slow clip: Layer > Time > Time Stretch (a flat factor), or Time Remapping with the end
  key moved earlier.
- Echo: Effect > Time > Echo (measured: no gain on flicker).

## Parallax and depth

- Layer split: make each layer 3D (cube switch), set Position Z, Layer > New > Camera (50 mm).
- Depth: depth layer > Effect > Blur & Sharpen > Box Blur > Layer > Pre-compose; photo layer >
  Effect > Distort > Displacement Map > Displacement Map Layer: the precomp, Max Horizontal
  Displacement keyed down to 0.

## 3D models

- Composition > Composition Settings > 3D Renderer > Advanced 3D, BEFORE dragging the model into the
  comp.
- Environment light: Layer > New > Light > Light Type: Environment > Source: the HDR or EXR layer.
- Embedded model animation: Properties panel on the model layer (not reachable by script on 27.0).
- Materials: twirl the model layer > Materials.
- Motion blur on a model in Advanced 3D: precompose, then Effect > Time > CC Force Motion Blur on
  the precomp layer (the layer switch is refused by this renderer).

## Audio

- Levels: select the layer, press L (Audio Levels); LL shows the waveform.
- Markers: Layer > Markers > Add Marker (numpad *), double-click to type the word.
- Audio-only render: Composition > Add to Render Queue > Output Module: AIFF 48kHz.
- Loudness: Window > Audio shows peaks only; measure integrated loudness on the render with ffmpeg
  ebur128.
