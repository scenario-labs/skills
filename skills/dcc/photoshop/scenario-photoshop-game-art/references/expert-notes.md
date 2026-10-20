# Expert notes: game art in Photoshop (the depth behind SKILL.md)

Each section is one source's method, with the timestamps it rests on. Timestamps are the start of
the caption chunk that holds the words. Where a video names a generative model, this file uses a
capability word instead ("an image model", "an image-edit model", "a tiling material model").

One video has a caption gap: AEXy7F5sJ7M's captions stop after the chunk at 14:18 and resume at
39:45. Its citations inside the gap are marked "frame" and rest on video frames read by eye, not on
words.

## The measured toolkit (real Scenario textures)

Two 1024 px cobblestone textures made with Scenario: one from a tiling material model, one from a
texture model with no tiling control. `test_gameart_live.py` runs every reading below on Photoshop
27.11 (macOS); the tiled previews were also read by eye.

- **Offset:** the Offset filter with Wrap Around, half the canvas each way, moves both seams to a
  cross in the middle. `GA.offset` runs it headless.
- **Seam ratio:** a blur clamped at the canvas edge invents a step at the wrap seam, and a seamless
  texture failed once that way. So `tile_check` offsets by half first, then divides the step across
  the middle column (and row) by the mean step between all other neighbors.
- **Patch range:** a 3x3 repeat is blurred by a 16th of its long side, the center is cropped, and
  the range of 4x4 cell means is read. It catches blotches that only show once the tile repeats.

| Texture                                        | Seam ratio x / y | Patch range |
| ---------------------------------------------- | ---------------- | ----------- |
| Tiling material model output                   | 1.07 / 0.89      | 9.75        |
| Texture model with no tiling control ("plain") | 2.03 / 3.09      | 4.28        |
| Plain, mirrored into a 2x2 block               | 0.04 / passes    | not read    |
| Plain, seam repaired (below)                   | 0.99 / 0.83      | passes      |
| Tiling output under a 40-level light falloff   | seams pass       | 26.78       |

Limits: seam ratio 1.5, patch range 12 (authoring-time; check them on your own images).

- **Channel packing:** Advanced Blending's channel restrictions, set on a layer copy, write its
  values into one channel unchanged: 40, 128, 77 and 220 read back. A mode change to Grayscale
  converts through the working gray profile instead, so `gray=True` uses Split Channels.
- **Alpha:** PNG keeps transparency, not alpha channels. A fourth channel needs TGA at 32 bits with
  alpha channels on; `pack_channels` refuses PNG with an alpha source.
- **Histograms** read visible channels only: an alpha channel raises an error until it is the only
  active channel.
- **ID passes:** Color Range on Lab bounds selects one flat ID color with its anti-aliased edge.
- **9-slice:** a smooth gradient stretches cleanly (0.97 against a limit of 1.0). Detail is flagged:
  rivets in the top edge 4.9, stone texture in the center 13.2 and 34.7.

## The seam repair shoot-out (plain texture, offset by half)

| Route                                                | Result                                                                  | Verdict                        |
| ---------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------ |
| Mask-edit model, white = edit, 96 px cross           | both outputs pixel-identical to the input; `GE.check` read `edited` off | a no-op, still charged         |
| Tiling material model, inpaint, 96 px cross          | style drift across the band, half stones on the seam                    | rejected by eye                |
| Image-edit model with reference and RGBA mask, 48 px | take 1: bias 2.5, residual 3.4, tile 0.99 / 0.83; take 2: residual 17.2 | take 1 kept                    |
| Tiling material model, img2img at strength 0.35      | tiles (0.97 / 0.93) but every pixel changes (mean 16), stones soften    | valid when the look may change |

- Outside the 48 px band and its 2 px feather, the repaired texture equals the source exactly (max 0
  past 32 px from the seam).
- `GE.check` caught the no-op and the re-laid take. Only the eye caught the style drift, which
  passed every number.
- Band width and model changed together between the 96 px and 48 px routes. The narrow band is the
  default because it worked and leaves the member less to invent; the width alone is not proven.

## Unmesh Dinda, PiXimperfect: a seamless pattern from a texture (9_36YihB8I4, 2024; CyJgXBJVHkU)

9_36YihB8I4 is from 2024. It stays because the technique (Offset, Pattern Preview, dodge and burn)
is unchanged in Photoshop 2026, and the 2026 video repeats its offset step.

- **See the seam first.** View > Pattern Preview shows the line between repeats [9_36YihB8I4 00:00].
  Fixes can happen inside Pattern Preview, but some tools do not work there, so the method is the
  "old-fashioned" offset [9_36YihB8I4 00:33, 01:05].
- **Offset.** Filter > Other > Offset with Wrap Around on, edges moved to the center both ways
  [9_36YihB8I4 01:05, 01:38].
- **Select loosely.** Lasso all edge areas at once, "a little random" [9_36YihB8I4 02:11].
- **Content-Aware Fill** did not join the lines on this texture [9_36YihB8I4 02:11]. Dinda still
  recommends it "with simpler textures": it reuses existing elements and keeps the resolution
  [9_36YihB8I4 02:45].
- **Generative Fill** joins the seam but drops resolution: "here's the original resolution and
  here's the one generated... it is terrible". The fix is to generate "little by little"
  [9_36YihB8I4 03:17]; the PiXimperfect panel fills 500 px boxes one at a time [9_36YihB8I4 03:51].
- **Clean up** with the Remove tool on a new layer, Sample All Layers on [9_36YihB8I4 04:24, 04:58].
- **Check again.** Stamp visible (Ctrl+Alt+Shift+E), Pattern Preview on, drag with the Move tool to
  offset, look for issues at the edges, fix them [9_36YihB8I4 04:58, 05:29].
- **Kill the repeat.** Zoomed out, a dark patch gives the pattern away [9_36YihB8I4 06:01]. A Soft
  Light layer named Dodge and burn, soft round brush, flow 1 to 2%, white or black; one stroke shows
  in every repeat [9_36YihB8I4 06:34, 07:08]. A Color layer at 5 to 10% flow, sampled from a
  neighbor, fixes a brick "standing out" [9_36YihB8I4 07:41].
- **Use it.** Edit > Define Pattern [9_36YihB8I4 08:14], then a Pattern fill layer with a blend mode
  [9_36YihB8I4 08:46, 09:20].
- **2026 update:** Generative Fill still has a resolution limit [CyJgXBJVHkU 00:00]. Smaller boxes
  give higher quality and take longer [CyJgXBJVHkU 02:08]. Offset to expose the edges [CyJgXBJVHkU
  07:37], lasso loosely and fill [CyJgXBJVHkU 08:11], check in Pattern Preview and fix leftovers "by
  offsetting again" [CyJgXBJVHkU 08:43]. The panel takes no prompt on purpose: a prompted "cloud"
  would appear "in every single box" [CyJgXBJVHkU 09:47].

Toolkit mapping: Offset is `GA.offset`; Pattern Preview's job is `GA.tile_preview`; "little by
little" is the narrow band; the zoomed-out patch is what `patch_range` measures.

## David Raskin: casual game UI button (vo7vwzzgDPk, 2025)

- **Squircle.** A Shift-dragged square, corner radius at maximum, then pulled back "until a straight
  line appears between the two points" [vo7vwzzgDPk 00:31]. The straight run is what Warp and a
  9-slice need.
- **Made for 9-slicing** by developers [vo7vwzzgDPk 02:04].
- **Value first.** Elements are built "in black and white with an emphasis on brightness values"
  [vo7vwzzgDPk 02:04]; a 30% gray copy, scaled down, clipped and blurred, makes the highlight
  [vo7vwzzgDPk 02:35].
- **Color by Gradient Map:** a deep color for shadow, a brighter one for highlight [vo7vwzzgDPk
  05:41], after an inner shadow on the base shape [vo7vwzzgDPk 05:10].
- **Shadows:** an outer shadow "very dark... not completely black" [vo7vwzzgDPk 09:21].
- **Colorways.** Hue/Saturation "looks ugly, the color transitions look bad, and only a few colors
  actually work". Keep the Gradient Map's stops and change their hue [vo7vwzzgDPk 09:52, 10:23].

## NoPoly: a PSX texture from photo pieces (QYUh8RuNZgw, 2026)

- **Work large.** A 1024 x 1024 canvas with the UV layout on top [QYUh8RuNZgw 07:15].
- **Build from pieces.** A reference image cut into about 30 pieces, placed on UV islands, masked,
  gaps filled with Clone Stamp, levels and contrast matched [QYUh8RuNZgw 10:30, 11:02].
- **Finish small.** Check at 128 or 256, undo, keep working; the final texture is 128 or 256,
  merged, with 1 to 2% noise and a Multiply color layer [QYUh8RuNZgw 11:34].
- **Engine side:** "closest" interpolation in Blender for the pixelated look [QYUh8RuNZgw 12:06].

Toolkit mapping: `GA.export_texture(out, size=128, resample="nearest")`, plus Closest or Point
filtering in the 3D app.

## AI2Play, host Ioan: match-3 graphics with an image model and Photoshop (AEXy7F5sJ7M, 2026)

Credential not stated; the host says game graphics were part of past work [AEXy7F5sJ7M 08:16].

- **Order of a set:** logo sets the style, buttons the UI style, tiles the main look, the board is
  built to match the tiles, then panels and screens, backgrounds last [AEXy7F5sJ7M 01:06].
- **Check cut-outs on a contrasting fill.** Background removal "missed some spots inside the
  letters", visible only over a different color; the fix is a Pen path, its selection, black on the
  mask [AEXy7F5sJ7M 07:42].
- **Edges:** a one-pixel light or dark edge from the old background goes with Matting > Defringe, or
  Remove White or Black Matte [AEXy7F5sJ7M 08:16].
- **Export:** Image > Trim, PNG with transparency, smaller sizes so the game loads faster
  [AEXy7F5sJ7M 08:48].
- **Buttons:** generate one blank button and set the text in Photoshop, with free-license fonts
  [AEXy7F5sJ7M 12:08, 12:40]; Pen tool where background removal left soft edges [AEXy7F5sJ7M 13:13].
- **One PSD per screen** (frame, in the caption gap): Loading Screen, Main Menu Screen, Game Play
  Screen and High Score Screen, with layers such as loading_bar_full and Background [AEXy7F5sJ7M
  frame 35:35].
- **Named tile layers** (frame): tile_scarab, tile_pyramid, tile_lotus, tile_eye and tile_ank, each
  transformed into a board cell [AEXy7F5sJ7M frame 40:05]. An action resized all tiles to fit the
  board [AEXy7F5sJ7M 40:53].

## pixaroma: game design with a local generator and Photoshop (vU-_9R-Tq18, 2025)

- **Icon sheets:** the prompt gives the icon count and style, then each icon by position (top left,
  top right...), then the style again; about 1024 px, fixed seed [vU-_9R-Tq18 04:56].
- **Steer with paint.** Shapes, gradients or texture painted in Photoshop guide an img2img pass; a
  flat color resists change; lower denoise stays closer [vU-_9R-Tq18 10:35].
- **Cut-outs:** mask cleanup with a white brush, apply the mask, Matting > Defringe for "the one
  pixel dark contour", one document per icon, aligned [vU-_9R-Tq18 12:48, 13:23].
- **Export:** File > Export > Layers to Files, PNG with transparency, Trim Layers off, names
  category first [vU-_9R-Tq18 13:23].
- **Test in context** against existing buttons and icons before upscaling; a busy background lost
  the tiles [vU-_9R-Tq18 14:27].
- **Separate layers for separate jobs:** the tile background stays fixed while the scene background
  adapts to the screen ratio [vU-_9R-Tq18 15:32, 16:06].
- **Match Color** is grayed out on a smart object: rasterize first [vU-_9R-Tq18 16:06].
- **Blank buttons, text added by hand,** for consistency across many buttons [vU-_9R-Tq18 17:13].

## Octopunish: paintover on Blender renders (gjkaYE8_MoE, h1i3X0gqrQs, 2026)

Game concept artist and course author (self-described).

- **Reference ranking:** AI images sit at the base: "difficult to know how the objects are actually
  constructed, where the light comes from" [h1i3X0gqrQs 02:47].
- **Color over value.** The color sketch is painted over the black-and-white one in a blend mode
  [h1i3X0gqrQs 07:07]. Two sunset versions turned out "super similar"; a third, different idea won
  [h1i3X0gqrQs 07:39].
- **Render as a base.** Color ideas tested with blending modes over the 3D; the render cut into
  layers per object; parts re-rendered and dropped in when the 3D changes [gjkaYE8_MoE 09:19,
  09:53].
- **"The work should look finished at any stage"** [gjkaYE8_MoE 09:53].
- **Lived-in detail:** bent beams, uneven carpet, dirt, papers [gjkaYE8_MoE 12:36].
- **Grayscale review:** "the value structure matters much more than color"; a storage area blending
  in got more light [gjkaYE8_MoE 13:09]. A beetle "blending completely into the slope" got light
  under it [h1i3X0gqrQs 21:20, 21:54].
- **Break 3D gradients** with brushstrokes and rough areas [h1i3X0gqrQs 21:54]; paint from afar,
  zoom in only near the end [h1i3X0gqrQs 23:32].

## Jourdan Tuffan, Art Forge Academy: stylized overpaint (j_czTAnOSCM, 2025)

- **Shadows:** soft shadows flattened, because "so much gradation gives it that computer-generated
  look"; darker contact shadows where objects touch [j_czTAnOSCM 12:09].
- **The render is a guide map:** "don't be afraid to disrespect your original render"; it serves "as
  a reference" [j_czTAnOSCM 14:23].
- **Consistency:** an area that "looks very, very 3D" stands out against painted ones [j_czTAnOSCM
  17:06].
- **Push shapes last** with Liquify and Warp, on a duplicate [j_czTAnOSCM 19:55].

## Gavin Manners, principal concept artist at id Software (eJN6aLNSnyc, 2026)

- **Variants are the deliverable:** "four different approaches to the same design problem", a wild
  card among them, and sometimes the wild card wins [eJN6aLNSnyc 19:16, 19:47].

## Grady Frederick, game concept artist: gray 3D to color (pAIYEsECSRw, 2025)

- **Layers by depth:** foreground, middle ground, background, sky; local values adjusted on the one
  gray material [pAIYEsECSRw 19:47].
- **Gradient Map for a base palette,** then paint on a new layer [pAIYEsECSRw 20:24].
- **Compare side by side,** not by toggling a layer [pAIYEsECSRw 26:55].

## Engine conventions (documentation, not the video corpus)

No video in the corpus covers delivery formats. These rest on the pages in [sources.md](sources.md),
read 2026-10-19.

- **Unity:** power-of-two sizes are ideal; non-power-of-two is meant for GUI. Unity reads PNG, PSD
  and TGA and flattens a PSD on import.
- **Unity import settings:** sRGB on for color textures, off for data. Alpha Is Transparency dilates
  color under transparent pixels against filtering artifacts. The normal map type has a Flip Green
  Channel option.
- **Unity HDRP mask map:** R metallic, G ambient occlusion, B detail mask, A smoothness; sRGB off.
- **Unity 9-slicing (Sprite Renderer):** left, right, top and bottom borders in the Sprite Editor;
  Mesh Type Full Rect; Draw Mode Sliced or Tiled. Scaling the Transform bypasses 9-slicing.
- **Unity Sprite Atlas:** padding defaults to 4 px; Allow Rotation and Tight Packing options.
- **Unreal:** power-of-two textures get mipmaps and streaming; non-power-of-two textures get
  neither. Some GPUs cap textures at 8192. Packing grayscale maps into channels saves texture
  samples; roughness may sit in alpha.
- **PNG specification:** "PNG does not use premultiplied alpha."
- **Not confirmed in documentation:** which engine expects which normal map green direction (read
  the shader's import option, or ask); Unreal's per-texture sRGB and compression page (it did not
  render); Godot's import settings (not checked). ORM (occlusion, roughness, metallic in R, G, B) is
  a common layout in practice [added], not a rule from these pages.

## Disagreements and the deciding condition

- **Content-Aware Fill or generative fill for a seam.** Dinda: Content-Aware on simple textures, as
  it keeps resolution [9_36YihB8I4 02:45]; generative fill on structured ones, in small pieces
  [9_36YihB8I4 03:17]. Decide by texture: grain-like surfaces (sand, grass, plaster) try
  Content-Aware first; structured ones (stones, bricks, planks) go to the band repair. Measured: the
  band repair with a reference image passed on cobblestone.
- **Band repair or re-render.** Decide by the brief: a texture that must stay gets the band; a
  texture whose look may change can be re-rendered through a tiling material model, which tiles but
  changes every pixel.
- **Hue/Saturation or Gradient Map for colorways.** Raskin rejects Hue/Saturation [vo7vwzzgDPk
  09:52]. Decide by the source: a Gradient Map on a value-built element; Hue/Saturation only on a
  flat single-hue part.
- **Generated images as reference or as the asset.** Octopunish ranks AI images lowest as reference
  [h1i3X0gqrQs 02:47]; AI2Play and pixaroma generate the assets themselves. Decide by role: a
  generated asset is judged as an asset; for light and construction, the 3D render stays the
  reference.
- **Keep the render or push past it.** Tuffan pushes shapes with Liquify [j_czTAnOSCM 19:55]; the
  style-pass gate keeps silhouettes aligned. Decide by use: a game asset or a paintover that must
  match the 3D keeps the layout; concept art may move it, on a duplicate.
- **Work large or at final size.** NoPoly paints at 1024 and finishes at 128 or 256 [QYUh8RuNZgw
  11:34]. Decide by look: pixel art and PSX downsize with `nearest`; other textures export at the
  engine size with `bicubic-auto`.

## Gaps in the sources

- No video measures a seam: Pattern Preview is judged by eye. The ratio and patch numbers are this
  toolkit's.
- No video shows channel packing, power-of-two export, TGA alpha, premultiplied alpha or atlases:
  those come from documentation.
- No video shows map extraction, a normal map edited in Photoshop, or a style pass gated for
  alignment.
- AEXy7F5sJ7M's screen-per-PSD layout and named tile layers are read from frames, not words.
- Nothing here was tested on Windows.
