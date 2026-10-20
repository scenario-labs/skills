# GUI paths (for the user or a computer-use agent)

Steps no script reaches: brush work, Pattern Preview, hand selections, and the engine's import
settings. None of these paths was run in testing (not tested). They come from the expert videos,
Adobe's menus as of Photoshop 2026 (27.x) and the Unity documentation in [sources.md](sources.md).
Menu names can move between releases. Shortcuts are macOS first, Windows second.

## Seamless textures

- **Pattern Preview:** View > Pattern Preview. The canvas repeats around the document; edits show in
  every repeat [9_36YihB8I4 00:00]. Some tools do not work inside it, so repair on an offset copy
  and use Pattern Preview to look [9_36YihB8I4 00:33, 01:05].
- **Offset:** Filter > Other > Offset. Turn on Wrap Around and Preview, then set Horizontal and
  Vertical to about half the width and height [9_36YihB8I4 01:05]. The script route is `GA.offset`.
- **Loose selection of the seam:** Lasso tool, all edge areas at once, Shift to add; keep it
  irregular [9_36YihB8I4 02:11].
- **Content-Aware Fill:** Edit > Content-Aware Fill. Try it first on simple, grain-like textures: it
  reuses existing pixels and keeps the resolution [9_36YihB8I4 02:45].
- **Generative Fill on a seam:** select a small piece, Generative Fill in the Contextual Task Bar
  (Window > Contextual Task Bar if hidden), leave the prompt empty, Generate. Work piece by piece: a
  large selection comes back soft [9_36YihB8I4 03:17].
- **Remove tool:** new empty layer, Sample All Layers on, Remove After Each Stroke on; paint over a
  stray line [9_36YihB8I4 04:24, 04:58].
- **Stamp visible** (a merged copy on top): Command+Option+Shift+E, Ctrl+Alt+Shift+E [9_36YihB8I4
  04:58].
- **Check the repeat:** with Pattern Preview on, drag the stamped layer with the Move tool to offset
  it, then look along the edges [9_36YihB8I4 05:29].
- **Dodge and burn the blotches:** new layer, blend mode Soft Light, named "Dodge and burn". Soft
  round Brush, Flow 1 to 2%, white to brighten, black to darken, X to swap. Work zoomed far out
  [9_36YihB8I4 06:34].
- **Fix an off-color element:** new layer, blend mode Color, Brush Flow 5 to 10%, Option-click or
  Alt-click a neighbor to sample, paint over the element [9_36YihB8I4 07:41].
- **Save as a pattern:** Edit > Define Pattern [9_36YihB8I4 08:14].
- **PSX finish:** Filter > Noise > Add Noise at 1 to 2%, then a Multiply color layer to tint
  [QYUh8RuNZgw 11:34]. Image > Image Size with Resample set to Nearest Neighbor for the final 128 or
  256 [added: keeps pixels crisp; the script route is `export_texture(resample="nearest")`].

## Maps

- **Invert roughness to smoothness:** duplicate the layer (Command+J, Ctrl+J), then Image >
  Adjustments > Invert (Command+I, Ctrl+I) on the copy.
- **Write a layer into one channel by hand:** double-click the layer, Blending Options > Advanced
  Blending > Channels, keep only R, G or B checked. The script route is `GA.pack_channels`.
- **Check one channel:** Channels panel, click R, G, B or Alpha alone; click RGB to return.

## Paintover and style passes

- **Color ideas over a clay render:** a new layer in Color or Overlay blend mode over the gray
  render [gjkaYE8_MoE 09:19].
- **Base palette from values:** Layer > New Adjustment Layer > Gradient Map; dark stops for shadows,
  light stops for highlights [pAIYEsECSRw 20:24].
- **Value check:** a Solid Color fill layer, black, blend mode Color, at the top of the stack;
  toggle it on to read values [added: shows luminance without touching the layers below]. The script
  route is procedures P10.
- **Select one ID color:** Select > Color Range, Select: Sampled Colors, click the object in the ID
  pass with the eyedropper, set Fuzziness. The script route is `GA.id_select`.
- **Push shapes:** on a duplicate, Filter > Liquify, or Edit > Transform > Warp [j_czTAnOSCM 19:55].
- **Match Color:** Image > Adjustments > Match Color. Grayed out on a smart object: Layer >
  Rasterize > Smart Object on a copy first [vU-_9R-Tq18 16:06].

## Sprites, icons and UI

- **Squircle:** Rectangle tool, Shift-drag a square, Properties panel corner radius to maximum, then
  back off until a straight segment shows on each side [vo7vwzzgDPk 00:31].
- **Colorways:** Layer > New Adjustment Layer > Gradient Map. Click the gradient bar, keep the stops
  where they are, change their hue [vo7vwzzgDPk 05:41, 09:52].
- **Outer shadow:** Layer > Layer Style > Drop Shadow, a very dark color that is not pure black
  [vo7vwzzgDPk 09:21].
- **Holes in a cut-out:** fill a layer under it with a saturated color to see them. Pen tool around
  the area, Command-click or Ctrl-click the path or shape thumbnail to load it as a selection, fill
  the mask with black (Option+Delete or Alt+Backspace fills with the foreground color) [AEXy7F5sJ7M
  07:42].
- **One-pixel fringe:** Layer > Matting > Defringe, 1 px; or Remove White Matte or Remove Black
  Matte, by the old background's color [AEXy7F5sJ7M 08:16]. Apply the layer mask first (right-click
  the mask > Apply Layer Mask) [vU-_9R-Tq18 12:48].
- **Trim to content:** Image > Trim, Based On: Transparent Pixels [AEXy7F5sJ7M 08:48].
- **Export every layer as a file:** File > Export > Layers to Files. Set a prefix, PNG, Transparency
  on, Trim Layers off [vU-_9R-Tq18 13:23].
- **9-slice guides by hand:** View > Guides > New Guide, once per inset (Vertical at the left inset
  and at width minus the right inset; Horizontal likewise). The script route is `GA.nine_slice`.
- **Stretch test:** duplicate the layer, Edit > Free Transform, drag a side handle to twice the
  width, read the edges and center at 100%, then undo.

## Engine side (Unity documentation)

- **Texture import:** select the texture in the Project window; in the Inspector set Texture Type,
  sRGB (Color Texture) on for color and off for data, Alpha Is Transparency for sprites with soft
  edges, Non-Power of 2 for UI only.
- **Normal maps:** Texture Type: Normal map; Flip Green Channel when the map uses the other
  convention.
- **9-slice borders:** open the sprite in the Sprite Editor, set the L, R, T and B fields to the
  insets (or drag the green dots), Apply. In the sprite's import settings, Mesh Type: Full Rect.
- **9-slice drawing (Sprite Renderer):** Draw Mode: Sliced to stretch, Tiled to repeat. Resize with
  the Size property or the Rect Tool: the Transform scale bypasses 9-slicing. The UI Image
  component's equivalent was not checked in a page read here.
- **Atlases:** Assets > Create > 2D > Sprite Atlas, add the sprites or their folder; Padding
  defaults to 4 px. Allow Rotation and Tight Packing are options on the atlas.
- **Unreal and Godot:** set sRGB off and the mask or normal compression per texture in the engine's
  texture settings. The setting names were not confirmed in a documentation page read here: hand off
  to scenario-unreal-materials or scenario-godot-expert.
