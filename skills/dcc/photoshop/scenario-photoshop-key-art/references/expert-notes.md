# Expert notes: key art, ads and thumbnails (the depth behind SKILL.md)

Each section is one expert's method, with the timestamps it rests on. Timestamps are the start of
the caption chunk that holds the words. Several videos run generative steps in third-party tools;
this file names the capability instead (an instruction edit, a relight, an upscale), and in this
skill those steps are Scenario MCP steps.

## The measured thumbnail (Photoshop 27.11, macOS)

The live suite builds one YouTube thumbnail: a 1280 x 720 canvas from the preset, a fixture plate
placed in a fixed box, a two-line headline and a two-line subline from a copy sheet.

- **Missing font:** asking for a font that is not installed raises nothing. The layer keeps Myriad
  Pro, and `font_used` is the only signal.
- **Point text versus paragraph text:** point text bounds are what renders, so a fit loop can
  measure them. Paragraph text hides overflow inside its box without an error.
- **Fit:** "NIGHT\nHUNTERS" in Impact, asked at 260 pt, fits its 472 x 430 box at 132 pt.
- **Legibility:** the subline on one line had to shrink to 39 pt, which is 11 px when the thumbnail
  shows 360 px wide. Split on two lines, it kept 60 pt, 17 px. `check` flags text under 12 px at the
  display width; both numbers are authoring-time.
- **Alignment bug:** ExtendScript groups chained ternaries from the left, so a left alignment came
  out right. The toolkit uses if/else.
- **Export sizes:** JPEG at quality 12 weighed 477 KB, 10 285 KB, 8 194 KB, 5 134 KB, 0 65 KB. A 2
  MB cap passes at 12, a 150 KB cap passes lower, a 20 KB cap never passes.

## storezar: the full YouTube thumbnail build

[BtzVLw67Ggs], 2025-06-13. Self-described video-editing course seller.

- Canvas from the Film and Video presets, HDTV 1080p: 1920 x 1080 at 72 ppi [00:31].
- The face is the focal point: "people look at faces. First of all, they look at the eyes" [02:07].
- He wants "a light source that logically falls on the face" [03:44].
- Shadows ground pasted pieces: a soft cast shadow [10:53], then a contact shadow, "which in the
  gaming world is also called ambient occlusion" [12:00]. The shadow "fits me into the scene a
  little bit, instead of just making me a giant" [20:05]; "just more realism. This is what we strive
  for" [21:39].
- Composition: a golden-ratio overlay, "everything is directed here, to this point" [13:06].
- Text effects copy from one layer to another with Alt-drag of the effects row [22:09, 22:41].
- Legibility check: zoom out to "about the size of a phone thumbnail", hold a phone to the screen
  [25:20].
- Finish: no "mega-contrast or excessive drama"; grain [25:51].
- On generated pieces: "it's hard to do previews with AI. It is always better to create resources
  yourself" [27:37]. A generated hand "undoes all our painstaking shadow work" [28:42].
- Export As JPEG: "YouTube does not accept files larger than 2" megabytes [29:48]; he raises quality
  until the file is about 1.6 MB [30:19].

## Badis Designs: a thumbnail with generated pieces

[TuF4RMJtq-4], 2025-12-07. No credential stated.

- Canvas 1280 x 720. "The closer the face is to the camera, the better because faces create emotion,
  and that is what drives clicks" [00:32].
- The face goes out for an instruction edit (new expression and clothes) in an external tool, comes
  back as a smart object resized to fit, then gets an external upscale [01:37].
- Camera Raw texture and exposure adjustments blend the pieces [02:40].
- "When things look unrealistic, the best solution is to darken and blend": shadows and one light
  source [04:19].
- "You can make two versions of the thumbnail, one with text and one without, and test" [06:30].

## Dill Toma: two looks, chosen by audience

[3eURUBIrhRY], 2026-02-16. Self-described YouTube thumbnail designer, 10+ years.

- Two styles: clean, colorful, flat light "built for speed" for a younger audience [00:32]; real
  skin texture "for viewers who value authenticity and storytelling". "The biggest difference here
  is the lighting" [01:05].
- Eyes first: "the eyes are the first thing that your brain sees" [06:02].
- Relight by instruction: "Don't change anything about the man... just change the lighting" to
  midday sun [11:07]; of four outputs he keeps the first [11:39].

## Morgan Hastie: generate around the product, keep the art live

[70L2ngS8raY], on Adobe's channel, 2025-12-04. Graphic designer.

- A selection over the bottles and a prompt to unify the scene [02:12]; "Don't change the bottles
  and add subtle shadows" [02:47].
- The label art goes in as smart objects, so a client revision is a swap, then Warp Arc Lower to
  follow the bottle [03:21].

## Posters and flyers: type, grids, clipped layers

- **DGH Graphic Design** [BmqlEDGP-GY], 2025-02-15, poster designer: the text stays live, "I can
  change it to anything and all the textures and effects will be preserved"; tracking opened up
  [00:31]. Effects go on the group "so it can be edited in the future" [01:02].
- **DGH Graphic Design** [OyNcu3HRXZY], 2025-02-01: View > Guides > Layout Guides, three columns,
  100 px gutters and margins [00:31].
- **WeJustClickme** (poster tutorials): part of the headline masked behind the subject [-fMxuEjV6dM
  03:04]; sponsor logos unified with a clipped Black and White layer [i-hYHLXDheU 05:41]; a photo
  texture clipped into the type [Ze2nUgmeYVI 03:29].
- **Dharnyelpeter** [i2N09bhDllE], 2025-07-08, self-described designer: the background group's
  opacity lowered so its details draw less attention [03:18]; a dark blurred rectangle behind text
  "so you have a good contrast level" [04:57]; the headline words grouped and stroked [07:07].
- **Genius Graphics** [hSCzvk9Xucg], 2025-06-11: a menu item's text and shape become one smart
  object [06:53]. Each item's layers are grouped and named [08:02]. A merged copy named "final" goes
  on top [11:35].

## Older thumbnail methods, kept for one point each

- **Vince Opra** [uM8jVa_wJU4], 2023-02-14. Kept because it is the only source on the full-HD canvas
  against YouTube's 720p display: 1920 x 1080, "YouTube actually will lower it down... to 720p
  thumbnails" [00:34] (300 ppi in the dialog, frame at 00:48). Selection flaws are "not going to be
  visible" at thumbnail size [03:56]. A drop shadow on the text [11:06]; logos placed with a white
  outer glow "so it pops out more from the background" [11:39]. Closing checklist: contrast between
  subject, text and background, few colors [15:32].
- **Pixolid** [XXAcCHrQ6J0], 2024-04-08, self-described thumbnail designer. Kept for the Action as
  layer setup [03:12] and the stance: "They may not be very realistic, but they're highly clickable"
  [13:45].

## Variants and data sets

- **Julieanne Kost** [SXVB8X4P2LI], 2025-05-20, Adobe Principal Digital Imaging Evangelist: one
  prompt with a variable list (spring, summer, winter, fall) generates 16 images [04:55]. That is
  Photoshop's own generator; this skill makes plates through Scenario and varies them in the loop.
- **Mike Hughes** [uUQ8pbysZsY], 2025-01-02, print and prepress (channel Mike The Print Man):
  - Data comes from a CSV only [01:08]. Static layers are locked [02:16].
  - Text replacement variables [06:13] are named exactly like the CSV headers, case included
    [06:45].
  - Photos use pixel replacement [07:23], with Fill and center alignment [07:58].
  - Replace existing data sets when the CSV grows [09:37].
  - Keep a batch to about 50 records; InDesign is better for data merges [10:42].
  - Output through File > Export > Data Sets as Files [11:15].
- **Ira Ostrovska** [Uvq85gcMSE0], 2025-10-28, CG artist and art director (render.camp): upscale a
  generated image "a little bit in higher resolution than your render" before Photoshop [03:29].

## Disagreements and deciders

- **Realistic or clickable.** storezar strives for realism [BtzVLw67Ggs 21:39]; Pixolid accepts "not
  very realistic, but highly clickable" [XXAcCHrQ6J0 13:45]; Dill Toma picks by audience
  [3eURUBIrhRY 00:32]. Decider: the user's channel and audience. Ask once, note it in the brief.
- **Generated pieces or own material.** storezar says it is "always better to create resources
  yourself" after a generated hand failed [BtzVLw67Ggs 27:37]; Badis Designs builds from generated
  edits [TuF4RMJtq-4 01:37]. Decider: the plate's light and anatomy at 100% (critique, part 1). A
  piece that breaks the light goes to compositing or gets regenerated.
- **Canvas size for YouTube.** Badis Designs works at 1280 x 720 [TuF4RMJtq-4 00:32]; storezar
  [BtzVLw67Ggs 00:31] and Vince Opra [uM8jVa_wJU4 00:34] at 1920 x 1080. Decider: the 2 MB cap and
  the plate. The preset is 1280 x 720; a 1920 x 1080 build is a dict preset with the same zones
  scaled by 1.5, and needs a larger plate.
- **Resolution value.** storezar 72 ppi, Vince Opra 300 ppi, same pixels. Pixels decide; `check`
  converts points at any resolution.
- **Effects on the group or on the text.** DGH and Dharnyelpeter style the group; Vince Opra styles
  the text layer. Decider: copy that changes per variant keeps its effects on a group, or the
  effects are reapplied after each `type_layers` run (procedures P5).
- **Variables and Data Sets or a scripted loop.** Variables need no code but keep fixed text boxes,
  and Mike Hughes caps them near 50 records. The loop (procedures P10) refits every record and runs
  `check` on each. Decider: copy that varies in length goes through the loop.

## Not covered by any source [added]

- Unsafe zones under a channel's interface. The presets' zones are authoring-time guesses at the
  duration badge and a story's top and bottom bars.
- Display widths per channel and the 12 px floor.
- Store capsule sizes: from Steamworks' graphical assets page (resized in August 2024), not from a
  video.
- Byte caps other than YouTube's.
