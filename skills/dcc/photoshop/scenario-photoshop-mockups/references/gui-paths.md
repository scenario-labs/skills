# GUI paths (for the user or a computer-use agent)

Menu paths for Photoshop 2026 on macOS (Ctrl for Cmd and Alt for Option on Windows). None of these
is run by the toolkit, and none was tested here; they come from the expert videos cited and
Photoshop's menus. Use them when the user works by hand, for shapes `fit_cylinder` does not model (a
tapered bottle, a pouch), and for the hand finish.

## Placeholder by hand

1. Draw a rectangle over the printable face with the Rectangle tool (U), then Layer > Smart Objects
   > Convert to Smart Object (Design Master [C3ZkcqB36xw 00:00]).
2. Lower the layer's opacity or Fill so the product shows through (Mockup Art [SKYL0FCOO04 05:31];
   WeJustClickme [-VM3ee1O_8U 01:06]).
3. Edit > Free Transform (Cmd-T), right-click, Distort: drag the four corners onto the face's
   corners (Mockup Art [SKYL0FCOO04 05:31]). On a box, Cmd-drag each corner "carefully" onto the
   face (GraphiqVibe [WeDJv63Wgjk 04:58]).
4. Rename the layer by role, such as "Place Design Here" (Quick Fix Up [boONV-waIUk 00:33]).
5. Opacity or Fill back to 100 once the design is in (Design Master [C3ZkcqB36xw 01:11];
   WeJustClickme [-VM3ee1O_8U 01:49]).

## Curved surfaces by hand (fallback to `fit_cylinder`)

- **Preset:** Edit > Transform > Warp, then the Warp menu in the Options bar: Cylinder for a can
  (Design Master [C3ZkcqB36xw 00:38]), Arc Lower for a bottle label (Hastie [70L2ngS8raY 03:21]).
- **Custom mesh:** in Warp, set the Grid to 4 x 4 and pull the mesh "without going inside the can"
  (Geller [0l2Ma_2B-A8 03:45]); the mesh follows the curve (Quick Fix Up [boONV-waIUk 01:05]).
  Mockup Art adds grid lines for the curved area (Mockup Art [SKYL0FCOO04 06:16]).
- Warp by hand after the last scripted fit: `fit_quad` and `fit_cylinder` replace any warp.

## Colorway by hand

Start from a white or light-gray blank, chosen before the fit: a much lighter color (sand, white) on
a dark garment loses its folds. With only a dark plate, ask the user for a light blank or make one
by instruction edit ([procedures.md](procedures.md) P9). A white colorway on a white blank needs no
Curves: the blank is that colorway.

1. Select the garment or product (Select > Subject, minus the print), then Layer > New Fill Layer >
   Solid Color: the selection becomes its mask.
2. Set the fill layer's blend mode to Color, so folds and highlights stay (WeJustClickme
   [i-hYHLXDheU 02:10]). Color keeps the garment's lightness: on a light blank, add a Curves
   adjustment layer under the fill, with the same mask, and pull the mid-tones down to the swatch's
   lightness, or navy stays pale blue on a white shirt. Check a deep fold at 100%.
3. Double-click its thumbnail to pick the next color (Quick Fix Up does it on a background
   [boONV-waIUk 02:47]), set the Curves again, and export each one (File > Export > Quick Export as
   PNG).

## The printable area as a group mask

1. Select the printable face: Select > Subject, or the Pen tool for hard rims; the Curvature Pen for
   a can's outline (Geller [0l2Ma_2B-A8 00:32]). Subtract the lid and base with Option held (Quick
   Fix Up [boONV-waIUk 01:39]; WeJustClickme [-VM3ee1O_8U 02:22]).
2. Select the group and click Add Layer Mask at the bottom of the Layers panel.
3. To reuse a mask on another group, Option-drag it there (Dinda [_VNqOhHJIm8 02:55]). One mask on
   the group, not one per layer (Dinda [_VNqOhHJIm8 02:22]).

## Displacement map by hand

1. Right-click the product layer > Duplicate Layer, Document: New (Dinda [_VNqOhHJIm8 05:06]; Dinda
   [sy1w5mTif-E 05:23]).
2. Image > Adjustments > Desaturate (Cmd-Shift-U).
3. Filter > Blur > Gaussian Blur: 1 px keeps a tote's texture (Dinda [_VNqOhHJIm8 05:39]); 3 px on a
   crushed can (Geller [0l2Ma_2B-A8 01:04]); 18 px keeps only big folds (Dinda [sy1w5mTif-E 05:54]).
4. File > Save a Copy as PSD, in a folder that stays with the project (Geller [0l2Ma_2B-A8 01:38];
   Dinda [_VNqOhHJIm8 06:11]).
5. On the design smart object: Filter > Distort > Displace. Horizontal and Vertical Scale, Stretch
   To Fit, Repeat Edge Pixels, OK, then pick the PSD (Geller [0l2Ma_2B-A8 05:24]).
6. To reuse it, Option-drag the Smart Filter onto another layer (Dinda [_VNqOhHJIm8 06:43]).

The filter re-reads the PSD on each re-render: moving or deleting it breaks the next Replace
Contents.

## Liquify instead of Displace

Dinda finds Displace "not very accurate" for an all-over pattern on fabric (Dinda [Z168F2BlAdA
07:09]) and warps it with Liquify over a backdrop instead (Dinda [Z168F2BlAdA 06:04]): Filter >
Liquify, Show Backdrop checked, Forward Warp tool. For a t-shirt print he still uses Displace for
the bumps, noting Liquify is more accurate (Dinda [sy1w5mTif-E 04:52]).

## Light and highlights by hand

- **Multiply copy:** duplicate the product (Cmd-J), move it above the design, Layer > Create
  Clipping Mask (Cmd-Option-G), blend mode Multiply, lower opacity "for a natural blend" (Design
  Master [C3ZkcqB36xw 01:47]).
- **Three copies:** Shadow in Multiply, Midtone in Linear Dodge (Add), Light in Screen, each with
  Levels (Cmd-L) (Mockup Art [SKYL0FCOO04 15:12]; [SKYL0FCOO04 15:47]).
- **Hard Light copy:** a product copy clipped in Hard Light, then Curves moving only the bright side
  (Anders [rrxTM5AZALU 04:25]; [rrxTM5AZALU 04:58]).
- **Metal cans:** the design in Linear Burn, then a product copy brightened in Camera Raw (Filter >
  Camera Raw Filter: Exposure down, Whites up), set to Screen with Fill lowered (Quick Fix Up
  [boONV-waIUk 02:15]; [boONV-waIUk 03:21]; WeJustClickme [-VM3ee1O_8U 03:29]).
- **Blend If:** double-click the layer > Blending Options > Blend If. Option-drag a slider to split
  it for a soft transition (Dinda [sy1w5mTif-E 07:32]; Geller [0l2Ma_2B-A8 07:39]). It has to read
  the product, not the design: "It needs to be based on the t-shirt and not the designs beneath it"
  (Dinda [sy1w5mTif-E 09:11]).
- **Channel mask:** in the Channels panel, Cmd-click RGB for a luminosity selection (Dinda
  [sy1w5mTif-E 09:44]), or use the channel that shows the folds best, often Blue (Dinda [_VNqOhHJIm8
  10:01]). Make it the mask of a Screen group, then Curves or Levels on the mask (Dinda [_VNqOhHJIm8
  10:35]; [_VNqOhHJIm8 11:08]).

## Hand finish

- **Ink blur:** select the design smart object, Filter > Blur > Gaussian Blur, 1 px on fabric (Dinda
  [_VNqOhHJIm8 07:17]); 0.6 px when the design has a fine stroke (Dinda [_VNqOhHJIm8 08:55]). In the
  Smart Filter list, keep the blur above Displace.
- **Shadow color:** a Hue/Saturation layer masked from the Blue channel, Saturation around -60, so
  the product's color does not "seep in" (Dinda [_VNqOhHJIm8 15:30]; [_VNqOhHJIm8 17:08];
  [_VNqOhHJIm8 18:13]).
- **Dark garment:** design opacity 90% (Anders [rrxTM5AZALU 06:38]).
- **Contrast:** a Curves layer at the top of the group (Dinda [_VNqOhHJIm8 14:25]).
- Step away and review later; every step stays editable (Dinda [_VNqOhHJIm8 17:41]).

## A logo cutout without a model

For a large, clean, flat logo on white (Williams [tNrV1XdZX0o 00:31]):

1. Check the logo is not already transparent (Williams [tNrV1XdZX0o 00:00]).
2. Channels panel: duplicate the channel with the most contrast, then Image > Adjustments > Levels
   to push it to black and white (Williams [tNrV1XdZX0o 01:03]).
3. Cmd-click the channel thumbnail to load it, invert if needed, add a layer mask (Williams
   [tNrV1XdZX0o 01:37]).
4. Export as PNG to keep the transparency (Williams [tNrV1XdZX0o 03:14]).

A small or blurry logo needs a vector trace instead (`scenario-image-editing` or
`scenario-brand-kit`).

## Template for reuse

1. Name the placeholder by role and leave it empty or at Fill 0 (Dinda [sy1w5mTif-E 11:21]).
2. File > Save As, format Photoshop Template (PSDT) (Dinda [sy1w5mTif-E 13:04]). "Every time you
   open it, it's going to create a new document" (Dinda [sy1w5mTif-E 13:35]).
3. To swap a design: double-click the placeholder's thumbnail, paste or place the design, save and
   close the contents file (Dinda [sy1w5mTif-E 11:55]).

## Plate cleanup with Generative Fill

Hastie warps artwork onto a raw photo first and judges it "fine. It's not great though" (Hastie
[70L2ngS8raY 00:33]), then cleans the product with Generative Fill and a cleanup prompt (Hastie
[70L2ngS8raY 01:04]): select the area, Edit > Generative Fill, pick the model in the picker. The
picker's partner models change; name the feature, not the model. Check that the shape and details
held (Hastie [70L2ngS8raY 01:36]). The label goes on afterwards as a smart object, never through the
model (Hastie [70L2ngS8raY 02:47]).

## Box faces by hand

One smart object per face, each named after it (GraphiqVibe [WeDJv63Wgjk 04:21]); fit each face by
its corners (GraphiqVibe [WeDJv63Wgjk 04:58]), then Layer Style > Gradient Overlay for light from
one side (GraphiqVibe [WeDJv63Wgjk 06:13]; [WeDJv63Wgjk 06:46]). Photoshop's 3D features were
removed in 2024, so older 3D mockup menus are gone.
