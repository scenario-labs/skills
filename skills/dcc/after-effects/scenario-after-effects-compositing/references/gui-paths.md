# GUI paths: compositing

For a person, or a computer-use agent, doing the steps a script cannot do or doing the scripted
steps by hand. Shortcuts are macOS first, Windows in parentheses. Menu command ids were read with
`app.findMenuCommandId` on 27.0; use them only to find or check an item, never to open a panel or
dialog unattended.

## What a script cannot do

| Task                                                                | Why                                  | Scripted substitute (run on 27.0)                                      |
| ------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------- |
| Object Matte, Quick Selection, Selection Brush, Refine Edge strokes | strokes are drawn in the Layer panel | imported matte as a track matte (procedure 8a); keyed or tracked masks |
| Roto Brush strokes in older projects                                | same                                 | same                                                                   |
| Content-Aware Fill                                                  | panel with Generate Fill Layer       | offset patch (procedure 9); hero frame with a corner pin               |
| Keylight eyedropper                                                 | samples the viewer                   | `AEX.comp.sampleColor` on a box of screen                              |
| Mocha AE planar track, Track Mask analysis, 3D Camera Tracker       | analysis runs in panels              | track data from scenario-after-effects-tracking, applied as keys       |
| Mask Feather tool (variable feather)                                | drawn per vertex                     | uniform `ADBE Mask Feather`, or a blurred matte layer                  |
| Lumetri Hue vs Hue curve on spill                                   | curve drawn in the panel             | Advanced Spill Suppressor Ultra; Color Balance (HLS) on a matted copy  |

## Keying

- Preset chain: Effects & Presets > Animation Presets > Image - Utilities > Keylight + Key Cleaner +
  Advanced Spill Suppressor. The suppressor arrives off so the screen color can be sampled first
  (keying doc).
- Keylight: Effect > Keying > Keylight (1.2). Screen Colour eyedropper; Cmd (Ctrl) widens the sample
  (tK_Z1dYgtxs 00:07:56). Set View to Source before re-sampling: the eyedropper reads what the
  viewer shows (00:02:58).
- View menu: Screen Matte, Status, Intermediate Result, Final Result, Colour Correction Edges. Clean
  in Status (00:09:01), deliver on Intermediate Result when the suppressor follows (00:08:28).
- Which control acts in which View (measured on 27.0): the Screen Matte group (clips, Shrink/Grow,
  Softness, Despot) shapes the alpha in every View. Replace Method, Replace Colour, Despill Bias and
  the Edge Colour Correction group change the image in Final Result only; in Intermediate Result,
  Hard and Soft Colour render identical. With the suppressor chain, leave them alone and fix the
  color on the suppressor or a color plate.
- Screen Matte group: Clip Black, Clip White, Clip Rollback, Screen Shrink/Grow, Screen Softness,
  Screen Despot Black and White, Replace Method, Replace Colour.
- Inside Mask and Outside Mask: point Keylight at a mask layer for holdout and garbage.
- Despill Bias and Alpha Bias: untick Lock Biases Together when the screen was lit by colored light,
  then pick the bias from a subject area (00:16:56 to 00:18:02).
- Edge Colour Correction: tick Enable Edge Colour Correction, set View to Colour Correction Edges to
  see the band, raise Brightness for a quick light wrap; Final Result only (00:22:13 to 00:24:10).
- Keyframed keying properties: one property keyed, Linear; several that interact, Hold (select the
  keys, Animation > Toggle Hold Keyframe); then step frame by frame (keying doc).
- Difference Matte: Effect > Keying > Difference Matte, Difference Layer = a clean plate of the
  locked-off shot; refine with Simple Choker (keying doc; K-uOFPoIm6U 00:30:48).
- Source Crops: crop junk at the frame border; it fills with black, set Edge Colour alpha to 0 for
  transparency (00:25:28).
- Key Cleaner: Effect > Keying > Key Cleaner; Reduce Chatter, Alpha Contrast.
- Advanced Spill Suppressor: Effect > Keying > Advanced Spill Suppressor; Method Standard or Ultra;
  Ultra exposes Key Color, Tolerance, Desaturate, Spill Range, Spill Color Correction, Luma
  Correction.
- Look at the key on black and on the transparency grid (_0lcyyybbng 00:05:06): toggle Transparency
  Grid at the bottom of the Composition panel.
- Channel views: Composition panel > Show Channel > Alpha (Option+4 (Alt+4)), Red, Green, Blue for
  per-channel color match (vJ8X58uknsk 00:00:27).

## Masks and mattes

- New mask: Layer > Mask > New Mask (id 2367), or Pen tool (G). Modes in the Timeline mask row:
  None, Add, Subtract, Intersect, Lighten, Darken, Difference. Mode cannot be keyframed.
- Mask Feather tool: hold the Pen tool (G toggles), click on the path to add feather points; Layer >
  Mask > Feather Falloff Smooth or Linear (masks doc; vJ8X58uknsk 00:02:04).
- Remove All Masks: Layer > Mask > Remove All Masks (id 2369). Version the layer first.
- Track Mask: select a mask, right-click > Track Mask (id 10311), then Tracker panel analyze.
- Track matte picker: Timeline > Track Matte column, in the Modes view (F4 toggles Switches and
  Modes); pick any layer with the pick whip; alpha or luma and invert icons sit next to it. One
  matte can feed many layers (0hevduJDDjg 00:00:52).
- Set Matte: Effect > Channel > Set Matte. Take Matte From Layer must name a layer whose source
  holds the alpha: a precomp of the key.
- Alpha Add: Timeline > Mode > Alpha Add on the upper of two complementary mattes (K-uOFPoIm6U
  00:09:10).
- Simple Choker: Effect > Matte > Simple Choker; Matte Choker, Refine Hard Matte, Refine Soft Matte
  in the same menu.

## Rotoscoping (26.2 and later)

- Toolbar: the former Roto Brush slot holds the Object Matte tool; click and hold for Quick
  Selection, Selection Brush, Refine Edge (e14kElpKaQo 00:00:32, frame 00:01:19). On 25.x and
  earlier the same slot is the Roto Brush tool.
- Object Matte: double-click the layer to open the Layer panel, hover and click the object, confirm,
  press Space to propagate. Fix misses with Quick Selection. Freeze at the foot of the Layer panel
  locks the result (roto doc).
- Roto Brush in older projects: Alt/Option+W selects the tool group per the doc; start with one
  stroke through the middle, Option (Alt) for background strokes, Cmd (Ctrl)-drag to resize the
  brush.
- Layer panel views: Option+4 Alpha, Option+5 Alpha Boundary, Option+6 Alpha Overlay (Alt on
  Windows).
- Effect Controls > Object Matte: Version (4), Feather, Contrast, Shift Edge, Reduce Chatter; Refine
  Edge Matte group; Use Motion Blur; Decontaminate Edge Colors.
- Work at Full resolution and with the comp frame rate equal to the footage rate (roto doc).

## Cleanup

- Content-Aware Fill: Window > Content-Aware Fill (id 5022), a panel docked with the others. Draw a
  Subtract mask around the object with room to spare, then in the panel: Alpha Expansion, Fill
  Method (Object for moving objects, Surface for flat surfaces like a logo on a shirt, Edge Blend
  for textureless static areas), Lighting Correction (start Strong, back off to Moderate or Subtle
  if it flickers), Range (work area or comp), Create Reference Frame (opens a frame in Photoshop),
  Generate Fill Layer. The fill is a new layer of image frames above the source.
- Hero frame clean plate: export one frame (Composition > Save Frame As > File), clean it, reimport,
  track with Animation > Track in Boris FX Mocha (id 5008), export Corner Pin; mask the patch, add a
  second masked Levels for lighting drift (3tMsr8TRDP8 00:03:51 to 00:06:07). The patch mask is
  applied before the pin, so it lines up on the hero frame only: check its edge at the first and
  last frames and key the mask where it pokes out (00:05:31).
- Freeze Frame: Layer > Time > Freeze Frame (id 3695).

## Integration

- Light wrap, manual: new solid, Set Channels (all sources = background, Effects & Masks), Set Matte
  inverted from the foreground, Fast Box Blur with Repeat Edge Pixels, Set Matte from the
  foreground, mode Add, low opacity; save as an animation preset (ZFJ3AKC2q8k 00:01:10 to 00:03:14).
  Hero shots: a second, smaller and stronger wrap limited to highlights (K-uOFPoIm6U 00:29:36).
- Core blurred inward: duplicate the core, add Gaussian or Fast Box Blur (no larger than the choke)
  to the lower copy, set the upper unblurred copy as its Alpha track matte (K-uOFPoIm6U 00:14:01 to
  00:15:39).
- Color plate: a copy of the plate with the key's precomp as its Alpha track matte; recolor it with
  Lumetri Color > Curves > Hue vs Hue (green toward the subject's hue) or Color Balance (HLS)
  (K-uOFPoIm6U 00:20:06).
- Levels: Effect > Color Correction > Levels (Individual Controls) for per-channel output black and
  white.
- Grain: Effect > Noise & Grain > Add Grain or Match Grain; set Viewing Mode to Final Output before
  rendering.
- Unmult for elements on black: Unmult (26.0 and later; find it with the Effects & Presets search);
  older route Shift Channels alpha from Lightness plus Remove Color Matting (HWNAGKi6apM 00:08:23).
- Interpret Footage: select the item, File > Interpret Footage > Main, Alpha: Straight or
  Premultiplied (Matted With Color).

## Pre-render

- Composition > Pre-render (id 2780) adds the comp to the Render Queue with Post-Render Action
  Import & Replace Usage. Output module template High Quality with Alpha.
