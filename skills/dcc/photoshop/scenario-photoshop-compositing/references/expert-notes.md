# Expert notes: compositing and skin after an edit (the depth behind SKILL.md)

Each section is one expert's method, with the timestamps it rests on. Timestamps are the start of
the caption chunk that holds the words. Some videos name the generative models they used; this file
uses capability words instead (a generative upscaler, a relight, a fill model).

## What the live suites measured

Fixture: a sample photo with grain and a warm cast, plus a flat blue disc with a 3 px white fringe
(a classic pasted cutout). Photoshop 27.11, macOS.

- **Halo:** the fringed disc's `light_rim` started above 8. `fix_halo(px=3)` cut it to under a
  third, in one History state.
- **Shadows:** both layers landed under the element on Multiply; the cast was under 0.6 of the
  element's height; the ground under the base darkened by more than 3 levels.
- **Tone:** at strength 0.6, the color-cast distance to the scene ring fell under 0.7 of the start;
  luminance stayed within 12%.
- **Grain:** texture energy more than doubled and ended within 50% of the scene ring's.
- **Blend If:** an underlying-layer range on blue darkened the area by more than 5 levels; the reset
  restored it within 0.5.
- **Frequency separation:** at 8 and 16 bits, the group rebuilt the stamp within max 2 (8-bit); one
  History state; High Frequency on Linear Light; the retouch layer clipped.
- **Scaffolds:** the smoother and the dodge and burn layers left the composite unchanged (max 0)
  until a mask was painted. Revealing Dodge lifted the mean by more than 5; Burn lowered it by more
  than 5.

The lead's measured round trip applies here too: a Scenario image-edit result differed by a mean of
17 to 18 outside the edit before masking. Any relight or regenerated element changes more than the
brief names.

Not measured: a real portrait, hair, a relight or Harmonize result, a layer split.

## Colin Smith: Harmonize in depth (dWiOA5YZXwc, C2lo7ew8lHY, P0OsXyEeuvM, UorIb_rGZuc)

- Harmonize fixes light direction, shadows and color in one click, with three variations
  [dWiOA5YZXwc 01:36, 02:09].
- It does not keep transparency in glass [dWiOA5YZXwc 02:09].
- It regenerates the whole layer from the subject as a reference and masks what changed, at 1024 px
  in the 2025 beta [dWiOA5YZXwc 02:44, 03:19]. A hat lost detail at 200% [dWiOA5YZXwc 05:05].
- Shadows are baked into the same layer, so moving the subject moves them [dWiOA5YZXwc 05:43].
- His resolution workaround starts from the originals, with a selection loose enough to show the
  scene's light and color [dWiOA5YZXwc 06:16, 06:47].
- Natural scenes work; his painted, stylized lighting did not survive [dWiOA5YZXwc 11:47, 12:25].
- Luminosity copy for light, the color result brought back partway [C2lo7ew8lHY 06:33, 07:06].
- Relight Layer (beta): up to 3 lights, credits only on Done, the render replaces the preview at
  high resolution [P0OsXyEeuvM 02:58, 04:05].
- A generative upscaler smoothed acne bumps and altered the face around the eyes; he mixes upscale
  versions by mask, region by region [UorIb_rGZuc 08:16, 11:00, 11:33].

## Matt Kloskowski: variations and marks (JGbvUOytwX0, 1zdowFXxtac)

- Harmonize sits in the Contextual Task Bar with no options [JGbvUOytwX0 01:36]. He masked the
  subject's own shadow out before running it [JGbvUOytwX0 02:11].
- Scrolling the variations shows new textures, edges and hair on the subject [JGbvUOytwX0 02:46].
- Camera Raw's blemish removal treats moles and freckles apart; Fade keeps them partly, because
  people usually keep them [1zdowFXxtac 02:40, 03:11].

## Terry White and an Adobe guest: correcting Harmonize (seXzZzjG9HI, 2jMaaUSp0dM)

- White found every variation too dark and fixed it with a clipped Levels, which also lifted the
  generated shadow [seXzZzjG9HI 04:57, 05:29].
- The guest kept the plate's natural shadows so Harmonize could read them [2jMaaUSp0dM 03:45]. One
  run added a shadow on its own; he still fixed shadow issues after [2jMaaUSp0dM 04:17, 04:55].

## John Gress: the older filter and unifying grain (aawE1ZFxl78, 2023)

- The Harmonization Neural Filter came in at strength 75, "usually always too strong"; he used 50
  [aawE1ZFxl78 14:39].
- A split Blend If slider keeps painted color to the subject's midtones and highlights [aawE1ZFxl78
  15:51].
- One 50% gray Overlay layer with Add Noise unifies foreground and background [aawE1ZFxl78 16:21,
  16:56]. 2023: kept because noise on Overlay has not changed.

## Jesús Ramirez: cutouts, frequency separation, skin color (mectUNmeOz8, Wkti_IX3Qzk, \_PNUQDm6lrA, REt264jFvqE, oZAC8R6zL8A, eOo99mWh15E)

- **Blend If cutout:** find the channel with the most contrast; hide the white sky with the white
  point slider [mectUNmeOz8 02:04]. A gray solid fill at the bottom shows the result [mectUNmeOz8
  02:36]. Blend If reads brightness live, so a smart object freezes the transparency while staying
  editable [mectUNmeOz8 03:07, 03:38].
- **Against Remove Background:** on his tree it lost the ground, thickened branches, filled gaps and
  left a blue halo [mectUNmeOz8 04:09]. He adds that Remove Background is often sufficient
  [mectUNmeOz8 04:41].
- **Blend If sliders:** split a slider with Option or Alt for a gradual transition [Wkti_IX3Qzk
  02:44]; channel ranges work per color [Wkti_IX3Qzk 08:19].
- **Three-step cutout:** Smooth and Shift Edge in Select and Mask [\_PNUQDm6lrA 04:27, 05:00]. Paint
  what cannot be selected [\_PNUQDm6lrA 09:20]. Match edge blur to the plate [\_PNUQDm6lrA 11:34].
  Minimum with roundness on the mask removes a remaining outline [\_PNUQDm6lrA 12:07].
- **Frequency separation by Apply Image:** pick the radius where pores disappear; it differs per
  image [REt264jFvqE 01:40]. 8-bit and 16-bit need different settings; 16-bit uses Add, Invert,
  offset 0 [REt264jFvqE 04:24, 04:56]. Paint the tone layer at 25% flow, building up [REt264jFvqE
  07:07]; set it to Lighten to keep texture through it [REt264jFvqE 08:16].
- **Skin line:** all skin tones share one hue and differ in saturation and brightness [oZAC8R6zL8A
  01:44]. Point Color moves skin toward it [oZAC8R6zL8A 03:23]. Keep saturation below the
  vectorscope's midpoint [oZAC8R6zL8A 03:58].
- **Camera Raw blemishes:** Apply, then Refine to restore or remove; Amount and Fade [eOo99mWh15E
  00:00, 00:31, 01:02, 01:35]. For a generative skin pass he selects a square around the face, so
  the generation spends its pixels there [eOo99mWh15E 03:40].

## Brendan Williams: hair and quick frequency separation (2Z0CFC7rg8U, l2h3J0VDqDE)

- Select Subject in Cloud mode, then Select and Mask on black, Refine Hair or the Refine Edge Brush,
  Object Aware for hair [2Z0CFC7rg8U 00:33, 01:39, 02:13, 02:46].
- The fringe left after Select and Mask goes with a clipped Solid Color fill, masked by the inverted
  subject mask, in the hair's color [2Z0CFC7rg8U 03:50, 04:24, 04:56, 05:29]. It fixes the color of
  the edge without shrinking it.
- Frequency separation: around 10 px blur on his portrait, Apply Image scale 2 offset 128, Linear
  Light [l2h3J0VDqDE 03:17, 03:50].

## PHLEARN: edges, blemishes, skin color, blend modes (p36McKBhQe8, sjX06wve7tw, H7HqYscQdpQ, o6jabPY-GPs)

- Enhance Edge looked right on white and failed on black, which is why a cutout is judged on more
  than one background [p36McKBhQe8 02:03]. It spends credits on every run and makes a new layer
  [p36McKBhQe8 03:37]; it carries inside colors outward and leaves the mask unchanged [p36McKBhQe8
  05:11].
- Camera Raw blemishes run in about 3 seconds and spend no credits [sjX06wve7tw 01:04]. Permanent
  marks are toned down, not erased, unless the client asks [sjX06wve7tw 01:35].
- On people, Vibrance instead of Saturation; Saturation turns skin orange [H7HqYscQdpQ 05:56,
  06:28].
- Aaron Nace: Screen drops a black background, Multiply a white one; Levels makes a near-white
  background disappear fully under Multiply [o6jabPY-GPs 04:22, 06:35, 07:09].

## Nour Art: shadows in painted composites (INmkd2ztW4c, BrMuLGNoPhs)

- Contact shadow first, dense at every contact point; then the cast, lighter, soft in shade
  [INmkd2ztW4c 35:10, 35:44].
- In direct sun the shadow is sharp and follows the subject's shape [INmkd2ztW4c 50:23].
- Cast from the subject's selection: Solid Color in the shadow color, Multiply, transformed onto the
  ground [BrMuLGNoPhs 31:00]; then the contact shadow painted under the subject [BrMuLGNoPhs 31:42].

## Julieanne Kost: shadows, grain, skin line (bMXJwZuzP14, YaTBt6nLOd0, Aj_xqQI3gs0)

- Halo left by a selection: paint black on the mask [bMXJwZuzP14 07:46]. A shadow from a Selection
  Brush area and a Curves layer, feathered when the edge is too sharp [bMXJwZuzP14 08:20].
- A drop shadow's angle dragged to match the scene [bMXJwZuzP14 19:58].
- Generative fills read smoother than the photo at 100% and 200% [YaTBt6nLOd0 03:17, 03:50]. Grain
  goes on the generated layers only, through a group and a clipped Grain layer [YaTBt6nLOd0 04:24].
- The 123 degree skin tone line on the vectorscope [Aj_xqQI3gs0 07:24].

## Blake Rudis: the Light adjustment layer (m6nSl2-t-iQ)

- It recalculates from the layers below and pauses while they are edited; use it late in the stack
  [m6nSl2-t-iQ 07:19, 07:52].

## Skin after generative edits (3eURUBIrhRY, 0cjjRoQ9M4E, SER_4Rqn7P4, p3JcJ99woGU, 0q_GxbuEr_M, qUUyJ6VwQZM, 5TaYvLfk2QQ)

- **Dill Toma** (thumbnail designer, self-described): a promptless generative fill removed his
  blemishes but changed his eyes; he painted the originals back [3eURUBIrhRY 05:28]. Smoothing on
  eyes, teeth or hair looks fake [3eURUBIrhRY 09:59].
- **Badis** (thumbnail designer): an outside upscaler altered face details; he put the original face
  layer under the result [0cjjRoQ9M4E 08:02].
- **Chandru Bharathy** (wedding and portrait photographer): a generative restore ran at about 1024
  px on a file near 8K [SER_4Rqn7P4 21:16].
- **Unmesh Dinda:** upscaling can make "an entirely different person"; he tests by downscaling a
  sharp original, upscaling it and comparing [p3JcJ99woGU 00:00, 00:33]. His quick skin: Overlay
  noise near 30%, uniform and monochromatic [0q_GxbuEr_M 03:19], blurred around 1.8 px [0q_GxbuEr_M
  03:53]. Detail comes back from the original's High Pass at the same radius [0q_GxbuEr_M 04:26],
  Blend If keeps it off highlights and shadows [0q_GxbuEr_M 05:32], texture at 80% [0q_GxbuEr_M
  06:38]. Edges are its weak point [0q_GxbuEr_M 07:12].
- **Marty Geller:** inverted High Pass smoother: Vivid Light smart object, High Pass 40 px, Gaussian
  5 px, black mask painted on skin [qUUyJ6VwQZM 00:35, 01:09, 01:41, 02:13].
- **grapexels channel** (presenter unnamed): dodge and burn as two Curves layers with inverted masks
  [5TaYvLfk2QQ 06:15].

## Disagreements and the deciding condition

- **Grain on the patch or on everything.** Kost clips grain to generated layers; Gress unifies the
  whole frame. Decider: one smooth patch in a real photo gets clipped grain. Sources that all differ
  (several photos, a generated plate) can share one layer on top, after each patch is matched.
- **Blend If or Remove Background.** Ramirez prefers Blend If on fine branches against a uniform sky
  and calls Remove Background often sufficient. Decider: gaps and twigs against a plain background
  go to Blend If; people and products to Select Subject or a background-removal tool model.
- **Minimum or a color fill for a fringe.** Minimum shrinks the mask; the color fill recolors the
  edge. Decider: solid edges take Minimum; hair and fur take the clipped color fill or Enhance Edge.
- **Harmonize or by hand.** Smith: natural scenes yes, stylized light no. White: keep a variation
  and correct it with Levels. Decider: a natural match with no fine detail to protect goes to
  Harmonize; brand text, faces in close-up or painted light go by hand or through a relight with the
  original masked back.
- **Harmonization strength.** Gress lowered the older filter from 75 to 50. The newer Harmonize has
  no strength slider; the Luminosity copy and opacity play that role.
- **Shadow softness.** Nour paints sharp shadows in sun and soft ones in shade. The toolkit default
  (blur 3% of the element's height) is the shade case.

## What reads as composited

- A light or dark rim on one of three backgrounds.
- An element sharper or smoother than the plate at the same depth.
- No contact shadow, or a cast pointing against the plate's shadows.
- A color cast from the old background on the element's edges.
- Grain missing inside the element or a fill at 100%.
- Skin without pores beside a sharp eyelash; changed eyes; missing moles.

## Gaps in the sources

- No expert gives a number for texture loss; the 0.6 ratio is an authoring-time gate.
- No source covers splitting a flat image into layers inside Photoshop; procedures P10 is untested.
- Harmonize's working resolution in 27.11 was not re-measured; the 1024 px figure is from 2025.
- The skin line was checked on one flat patch; dark and very light skin under colored light were not
  tested.
- No Windows run.
