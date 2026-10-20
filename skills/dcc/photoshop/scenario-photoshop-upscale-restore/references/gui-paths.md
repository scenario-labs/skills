# GUI paths (for the user or a computer-use agent)

Menu paths for Photoshop 2026 on macOS (Ctrl for Cmd and Alt for Option on Windows). None of these
is run by the toolkit, and none was tested by script here; they come from Adobe's documentation and
the expert videos cited. Use them when the user works by hand, when a route has no script
(Generative Upscale, Neural Filters), or to repeat a toolkit step by eye.

## Preserve Details 2.0 enlargement (the baseline by hand)

1. Image > Duplicate, so the master keeps its size (Smith [UorIb_rGZuc 03:54]).
2. Image > Image Size. Check Resample, pick Preserve Details 2.0, set the new width or a percentage.
3. Reduce Noise appears for Preserve Details 2.0; leave it at 0 for a baseline.
4. Drag the enlarged layer onto the candidate document with Shift held, so it lands centered (Smith
   [UorIb_rGZuc 05:00]).

Automatic picks a method for you; Dinda uses it for a quick 4096 px document (Dinda [mSgSaisb6Kg
07:40]). For a comparison baseline, pick Preserve Details 2.0 by name. Adobe lists a "Preserve
Details 2.0 Upscale" setting under Preferences > Technology Previews, on by default; with it off,
the method may differ.

## Generative Upscale (Photoshop's own route)

1. Image > Generative Upscale.
2. Pick the model. Adobe's own model and partner models appear in the picker; partner models spend
   premium generative credits (Smith [9YS0m69uhIk 02:09]; Geller [pNODFCbH9n8 01:47]).
3. Pick 2x or 4x. Each model has a maximum output; past it, Upscale is grayed out (Kost [a2OIpxbuzKE
   00:34]).
4. Model options: face recovery on the faithful partner model; a Creativity slider on the creative
   one, low staying faithful and high adding detail (Ramirez [a7E4HlrAc3w 02:06]; [a7E4HlrAc3w
   03:38]).
5. The result opens as a new document with two layers: "Original", resized without generative AI,
   and the generated layer (Kost [a2OIpxbuzKE 01:09]; Ramirez [a7E4HlrAc3w 01:05]).
6. Set the view to 100% (Zoom tool, 100% in the Options bar) before judging (Ramirez [a7E4HlrAc3w
   01:05]).

To compare it with Scenario candidates, drag its generated layer into the stack document from
`build_stack`, Shift held, and name it "<model>, 2x scale". Its "Original" layer is not the
baseline: the stack already has a scripted one (likely Preserve Details 2.0).

## Bringing a result back into the master

1. Drag the layer to the master's tab, down into the canvas, and release with Shift held (Smith
   [iy0IxTpT4OY 03:15]).
2. Edit > Free Transform (Cmd-T) and scale to fit; for a 2x result into the original size, 50%.
3. Set the blend mode to Difference, zoom to 100% on the eyes, and nudge with the arrow keys until
   the frame reads black or close to it (Smith [iy0IxTpT4OY 03:47]; Dinda [mSgSaisb6Kg 05:28]).
4. Set the blend mode back to Normal, or to Color for a colorize.

## Auto-Align Layers

1. Duplicate the result (Cmd-J) as a backup.
2. Layer > Rasterize > Layer on the copy: Auto-Align works only on raster layers (Dinda [mSgSaisb6Kg
   08:12]).
3. Select both the copy and the original (Cmd-click in the Layers panel).
4. Edit > Auto-Align Layers, Projection: Auto, OK.
5. Check in Difference or with the overlay. If it moved an aligned result, Edit > Undo.

Auto-Align turns a Background layer into "Layer 0", and on a damaged original it can make an aligned
result worse; `U.align` measures before keeping it.

## Blend modes, masks and clipping

- **Color or Luminosity:** the blend mode menu at the top of the Layers panel. Color keeps the
  layers below for lightness; Luminosity keeps them for color.
- **Clip to the layer below:** Option-click the line between the two layers (Dinda [knYusnpB9zI
  07:26]).
- **Paint one take in:** Layer > Layer Mask > Hide All, then paint with white (B, white foreground)
  over the faces (Kost [a2OIpxbuzKE 03:23]). Black hides, white shows.
- **Curves under the Color layers:** add the Curves adjustment below them, or the contrast fix
  shifts the colors (Dinda [knYusnpB9zI 07:58]).

## Crop back after padding or alignment

1. Cmd-click the original layer's thumbnail to load its bounds as a selection.
2. Press C for the Crop tool; it crops to the selection. Press Return to commit (Dinda [G5yuLhm0SdM
   10:55]).

## Image mode before a colorize

Image > Mode > RGB Color. In Grayscale, no color shows (Dinda [G5yuLhm0SdM 12:32]). This changes the
user's document: ask first, and keep a copy.

## Neural Filters (status in 27.11 not tested)

- Filter > Neural Filters > Photo Restoration: Scratch Reduction, Enhance Face, Photo Enhancement,
  and adjustments; output to a New Layer (Blue Lightning [cvF6BZArpYc 00:33]; Alwash [WwRbCKao7S4
  00:33]). It "does the face good, but not the rest of the body" (Dinda [knYusnpB9zI 05:17]).
- Filter > Neural Filters > Colorize, applied as a smart filter on a copy (Dinda [G5yuLhm0SdM
  01:04]).
- Super Zoom is one of Photoshop's older upscale routes (Smith [UorIb_rGZuc 05:32]).

## Finishing by hand

- **Over-sharpened download:** duplicate the layer, Filter > Blur > Gaussian Blur at 1 px or 0.8 px
  (Dinda [knYusnpB9zI 08:29]; [knYusnpB9zI 09:02]).
- **Bring it together:** Cmd-Option-Shift-E for a Stamp Visible layer, Filter > Convert for Smart
  Filters, then Filter > Camera Raw Filter: Detail > Sharpening, then a little grain (Dinda
  [knYusnpB9zI 09:02]; [knYusnpB9zI 09:35]).
- **Skin after an upscale:** Camera Raw Filter on the upscaled layer, Texture, Clarity and
  Sharpening (Marsh [ZCTPo7M8Eyg 04:57]).
- **Sharpen after an upscale:** Filter > AI Sharpen (Geller [pNODFCbH9n8 02:56]), or a High Pass
  layer in Linear Light, grouped for a before and after (Bharathy [SER_4Rqn7P4 24:07]).
- **Saturation:** a Vibrance adjustment layer; Saturation down to about -33 when skin looks garish
  (Geller [jIvcJtPsJss 02:18]; [jIvcJtPsJss 02:56]). Hue/Saturation with Yellows shifted toward
  orange for faces (Alwash [WwRbCKao7S4 02:08]).
