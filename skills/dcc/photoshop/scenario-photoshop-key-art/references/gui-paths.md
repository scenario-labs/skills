# GUI paths (for the user or a computer-use agent)

Steps no script reaches, or reaches only partly. None of these paths was run in testing; they come
from the expert videos and Adobe's help pages, on Photoshop 2026 (27.x). Menu names can move between
releases. Shortcuts are macOS first, Windows second.

## Fonts

- **A missing font on open:** Photoshop offers to activate it from Adobe Fonts (a blue sync icon
  shows while it activates), or to replace it. Replace uses a default font, Myriad Pro Regular for
  Roman text. After activation, the agent sets the type again (procedures P5) and compares
  `font_used`.
- **Find a font's PostScript name:** set one text layer in the font by hand, then read
  `textItem.font` on that layer. The font menu shows family names, not PostScript names.
- **Match Font:** Type > Match Font, with a marquee around text in an image, suggests installed and
  Adobe Fonts matches. Useful when the user has only a picture of the brand lettering.
- **Dynamic Text** (27.6, any path or shape since 27.10): presets Block, Circle, Arch, Bow; "Dynamic
  fit" resizes text to fill its path or shape. It has no script call. `type_layers` fits point text
  to a box instead.
- **Warp Text:** Type > Warp Text (Arc, Arc Lower, Bulge and others) stays editable. Morgan Hastie
  warps placed label art with Arc Lower to follow a bottle [70L2ngS8raY 03:21].

## Layer styles

- **Open:** right-click the text layer or group > Blending Options. Stroke (Position Outside), Drop
  Shadow, Outer Glow sit in the left list. Vince Opra adds a drop shadow to the text from there
  [uM8jVa_wJU4 10:33].
- **Copy effects to another layer:** hold Option or Alt and drag the fx row onto the other layer
  (storezar [BtzVLw67Ggs 22:09, 22:41]). Or Layer > Layer Style > Copy Layer Style, then Paste Layer
  Style.
- **Style the group, not the text,** so the copy can change without losing the effect (DGH
  [BmqlEDGP-GY 01:02]): select the type layers, Command-G or Control-G, then Blending Options on the
  group.
- After any style change, run `check` again: effects widen what renders.

## Layout aids

- **Layout guides:** View > Guides > New Guide Layout: columns, gutters and margins. DGH uses three
  columns with 100 px gutters and margins [OyNcu3HRXZY 00:31].
- **Hide or show guides:** View > Show > Guides, or Command-; or Control-;. `new_canvas` draws the
  unsafe zones as guides; leave them on while placing copy.
- **Composition overlay:** the Crop tool (C) has overlay options in the Options bar, among them Rule
  of Thirds and Golden Ratio. storezar aligns the subject to a golden-ratio overlay [BtzVLw67Ggs
  13:06].
- **A display-size view while editing:** Window > Arrange > New Window for the document, zoomed out
  to the channel's display width, next to the working view. storezar zooms out to "about the size of
  a phone thumbnail" [BtzVLw67Ggs 25:20].

## Variables and Data Sets (records from a CSV)

Mike Hughes's method [uUQ8pbysZsY]:

1. Prepare a CSV: one column per variable, one row per record. Photoshop imports data from a CSV
   only [01:08]. Lock the layers that never change [02:16].
2. Image > Variables > Define. For a text layer, check Text Replacement and give the variable the
   exact CSV header name, case included [06:13, 06:45].
3. For an image layer, check Pixel Replacement, the same header name, and a method: Fill with Center
   alignment for a photo inside a clipped circle [07:23, 07:58]. Other methods: Fit, As Is, Conform.
4. For a layer that shows per record, check Visibility; the CSV holds true or false [04:32].
5. Image > Variables > Data Sets > Import: the CSV, Use First Column For Data Set Names, and Replace
   Existing Data Sets when the CSV grew [09:37]. Step through records with the arrows.
6. File > Export > Data Sets as Files writes one PSD per record [11:15]. Keep a batch near 50
   records or fewer; Hughes prefers InDesign for larger data merges [10:42].

Text boxes do not refit per record. Long copy overflows or runs past its area. The scripted loop
(procedures P10) refits every record and runs `check` on each.

## Artboards

- Create: File > New with the Artboards box checked, the Artboard tool (grouped with Move), or
  right-click selected layers > Artboard from Layers.
- Export: File > Export > Artboards to Files, or Export As per artboard.
- The DOM has no artboard API; artboards by Action Manager are not tested here. The toolkit makes
  one document per channel instead; a user who wants one file with every size can drag the canvases'
  layers into artboards by hand.

## Export

- **Export As:** File > Export > Export As. JPG quality in percent, Image Size, Convert to sRGB; the
  file size shows in the dialog. storezar raises quality until the file is about 1.6 MB, under
  YouTube's 2 MB [BtzVLw67Ggs 29:48, 30:19].
- **Quick Export as PNG or JPG:** File > Export > Quick Export as, with stored preferences.
- **Save for Web (Legacy):** File > Export > Save for Web. Its dialog was modernized in 27.7.
- `export_under` replaces all three for a byte cap: it searches JPEG quality 12 down to 0 on a
  flattened sRGB copy.

## Photoshop's own generators

- **Generate Image:** in the Contextual Task Bar on an empty layer, or from the Generate Image
  workspace; text to image with optional style or composition references. Julieanne Kost uses a
  variable list in square brackets in the prompt to generate one image per value [SXVB8X4P2LI
  04:55].
- These have no script call and spend the user's Adobe credits. In this skill, plates come from
  Scenario through the `scenario` skill, priced and approved first.
