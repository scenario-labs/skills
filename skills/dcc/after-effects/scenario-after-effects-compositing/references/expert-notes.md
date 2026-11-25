# Expert notes: compositing, keying, roto and cleanup

Principles by expert, with the video id and timestamp (hh:mm:ss). Lines marked [added] come from the
live measurements on After Effects 27.0, not from the expert. Where a measurement qualifies an
expert's number, both are given.

## Leonard Wilkes, Advanced Indie VFX (K-uOFPoIm6U)

- One Keylight is not enough for a hard plate: build several mattes and combine them (00:01:12).
- Split the key into an alpha plate and a color plate, joined by an alpha track matte. Fix halos and
  spill on the color plate, never by choking the alpha (00:02:17, 00:22:44).
- Hair gets its own key (00:08:05). Where two complementary mattes meet, set the upper one to Alpha
  Add; a 15 px feather on each is then safe (00:09:10). [added] Measured seam: 1.0 with Alpha Add,
  0.878 in Normal mode.
- Core matte: Levels on the alpha channel to crunch the white point, then Simple Choker 5 to 10 px,
  always inside the soft edge so the edge bleeds outside it (00:10:47 to 00:11:51). [added] Measured
  on a 1280x720 plate: Levels input white 0.7 and a choke of 3 filled the core (holes 3.0 % to 0.7
  %) without touching hair.
- Blur the core only inward: a duplicate of itself as its own alpha track matte, Gaussian Blur no
  larger than the choke, 5 px at most (00:14:01 to 00:15:39). [added] Measured with choke 4 and blur
  4: 0 px of alpha outside the hard core with the matte, 33,070 px without it (procedure 2b).
- Animated Subtract masks on the core reveal soft detail such as hair edges (00:16:11 to 00:17:16).
  [added] On a 45 % veil the holdout cut speckle from 0.171 to 0.058 standard deviation.
- Advanced Spill Suppressor darkens greens because it rebuilds green from red and blue; Ultra
  disturbs luminance less (00:18:30, 00:19:02). For hero shots he recolors the plate with Lumetri
  Hue vs Hue and local shapes in Color or Multiply mode (00:20:06, 00:22:13 to 00:26:43). [added]
  Measured on a white shirt: Standard luma 0.891, Ultra 0.929, plate 0.929.
- Edge Blur 2 to 3 px on the matted foreground, then Pixel Motion Blur at 45 to 90 degrees when the
  plate was shot with a fast shutter (00:27:58, 00:28:30). [added] Edge blur raised mean alpha error
  from 0.099 to 0.115 at 2 px: it matches a soft plate, it does not improve accuracy.
- Two light wraps: a normal one and a smaller, stronger one limited to highlights (00:29:36).
- A Difference Matte against a clean plate keys a screen nothing else can; the clean plate can be
  made by smearing edge pixels inward (00:30:48 to 00:32:27).
- Works at 16 bpc (frame 00:07:32).

## Danasa (_0lcyyybbng)

- Denoise and render the plate before keying; draw a garbage mask first (00:01:11). [added] An
  animated garbage matte took mean alpha error from 0.100 to 0.015 and removed the light stand.
- Core key, then region keys for edges, each limited by masks (00:02:44 to 00:14:33).
- Key in Intermediate Result; spill suppression comes last and stays off while edges are built
  (00:02:12, 00:07:42).
- Fill reflection holes with a softened duplicate of the key masked to the hole; repeat until opaque
  (00:03:15).
- Look at the key on black and on the transparency grid: pixels show on one and hide on the other
  (00:05:06).
- Key Cleaner after precomposing the keys: Reduce Chatter, radius 1 (0.1 for a tight cleaner), Alpha
  Contrast about 20 % (00:06:13, 00:07:42). [added] Measured: mean error 0.100 to 0.080.
- Pre-render the heavy matte comp with RGB and alpha and Import and Replace (00:09:31 to 00:10:02).
  [added] Frame time 1,503 ms to 263 ms, pixel identical.
- Refine Hard Matte on a duplicate below, the unrefined layer above in Stencil Alpha, then patch
  flicker with masks (00:10:24 to 00:12:06).
- Hair against a screen of similar hue: rotate hue with Color Balance (HLS), Tint, Curves, Shift
  Channels alpha from Luminance; Shift Channels ignores the layer's mask, so mask a separate solid
  that uses the key as alpha matte (00:12:58 to 00:14:33).

## Jake Bartlett, Jake In Motion (tK_Z1dYgtxs)

- Keylight first for chroma work (00:00:39). The eyedropper reads the displayed image: set View to
  Source before re-sampling; Cmd or Ctrl widens and averages the sample (00:02:58, 00:07:56).
- Order: Keylight, Key Cleaner, Advanced Spill Suppressor (00:05:36). Intermediate Result switches
  off Keylight's own despill; without it the suppressor has nothing to remove (00:08:28). [added]
  Measured: Final Result plus the suppressor gave the same shirt luma loss as Keylight alone
  (0.880).
- Ultra spill method on uneven screens wants Tolerance near 100; Desaturate works from the edge
  inward, about 50; Luma Correction crushes chattering semi-transparent pixels (00:03:31 to
  00:05:08).
- Clean the matte with Clip Black and Clip White in Status view, where stray pixels show that Screen
  Matte hides; then Screen Pre-blur about 0.3; avoid Screen Gain because it hardens edges (00:09:01,
  00:11:24). Demo values 14 and 61 (frame 00:12:16). [added] Screen Gain 130 opened holes in 54 % of
  the core; Pre-blur 1 erased 1.4 px hair strands (coverage 0.44 to 0.02).
- Uneven screen: a first Keylight pushed out with Screen Shrink/Grow in Intermediate Result, a
  second sampled from what remains (00:13:37).
- Replace Method: Soft Colour by default; Hard Colour fixes edge artifacts on a shirt (00:15:48).
  [added] It acts in Final Result only: in Intermediate Result, Source, Hard and Soft Colour
  rendered pixel-identical; in Final Result, Hard against Soft changed 17 % of pixels. With the
  suppressor chain on Intermediate Result, Hard Colour is not the fix: work on the suppressor or a
  color plate.
- Unlock Despill Bias and Alpha Bias when the screen is lit by colored light (00:17:30). [added] A
  warm Despill Bias changed 24 % of pixels in Final Result and 0.2 % in Intermediate Result.
- Colour Correction Edges view shows the band edge correction touches; raising Edge Brightness acts
  as a quick light wrap (00:23:17 to 00:24:10). [added] Edge Brightness 60 changed 7 % of pixels in
  Final Result and nothing in Intermediate Result: a quick wrap for a Keylight-only key.
- Source Crops remove stands and compressed borders; they fill with black unless Edge Colour alpha
  is 0 (00:25:28).
- The Adobe preset sets View to Intermediate and leaves the suppressor off until the screen color is
  sampled (00:28:34).

## Adobe keying documentation (keylight-keying-effects doc)

- Tune on the most intricate frame; with constant light those settings hold for the shot.
- Keyframes on keying properties: Linear when only one property is keyed, Hold when several
  interacting properties are keyed; check frame by frame, because intermediate values give
  unexpected results.
- A static background goes transparent with Difference Matte against a clean plate, refined with
  Simple Choker. It needs a locked-off camera (Wilkes makes the clean plate by smearing edge pixels
  inward, K-uOFPoIm6U 00:30:48 to 00:32:27).
- A hold-out matte is a masked duplicate of the keyed layer placed directly above it.

## Danasa Arsad (ZFJ3AKC2q8k): light wrap

- Light from the background wraps around the foreground edge (00:00:06). Build it once and save it
  as a preset (00:02:42).
- Set Channels with all four sources on the background (Effects & Masks), Set Matte inverted from
  the foreground, Fast Box Blur with Repeat Edge Pixels, Set Matte from the foreground, Add mode
  (00:01:10 to 00:02:14).
- The wrap must inherit the foreground's masks, or it lingers where the subject is masked out
  (00:02:14).
- Subtlety is the whole point: small blur, low opacity (00:02:42). [added] Measured: 1.5 % of comp
  height at 40 % Add lifted edges by 4.7/255 against a bright window and about 0 against a dark
  desk, reaching about 20 px inward; 4 % at 100 % lifted 20/255.

## Stock effects studio team (HWNAGKi6apM): elements over plates

- Remove black from elements over bright plates with Unmult, not Screen or Add, which brighten what
  is behind (00:08:23).
- Anchor an explosion at its base so scale grows from the ground (00:02:49); an interactive shadow
  is a 3D duplicate laid on the terrain, masked and blurred, with a warm Curves adjustment matted to
  it (00:02:49 to 00:03:50).
- Tint to ground blacks and whites, then back off the amount (00:07:00).
- Pixel Motion Blur goes last because it slows the comp (00:08:09).
- Time-stretch elements to the plate's speed and freeze the last frame so nothing vanishes
  (00:05:48, 00:10:47).
- EXR passes: linearize, EXtractoR with Unmult, Shift Channels Full On to inspect RGB, restore alpha
  with a Stencil Alpha duplicate (00:16:27 to 00:19:06). Fake rim wrap: blurred backplate copy, luma
  matted to a rim pass, Add (00:17:30).

## ProductionCrate (gomawnMPWEg): building explosion (frames only, no narration)

- Track first, then build: every element parented to the tracked null (frame 00:04:29).
- A sky matte in its own precomp (Keylight, Combined Matte view) used as the track matte so debris
  sits behind the building (frames 00:08:41, 00:12:20).
- Black level matched with Levels, RGB then per channel, before glow (frame 00:14:20).
- Bloom, god rays, distortion and shake in a separate finishing comp (frame 00:19:50).

## Ryan Connolly, Adobe Video x Film Riot (vJ8X58uknsk, eoOIrdb_0ko)

- Match color per channel: view one channel, adjust the same channel in Curves (vJ8X58uknsk
  00:00:27).
- Light direction cannot be fixed in the grade (00:01:05). Mismatched black levels are the hidden
  reason a composite feels off; read the scopes (00:01:34).
- Variable feather for subjects with hard and soft edges (00:02:04). Grain is the last step
  (00:02:40).
- Roto Brush works in the Layer panel; propagate, Freeze to protect the result, Refine Edge only for
  hair (eoOIrdb_0ko 00:00:52, 00:01:58, 00:02:40).

## Anton Thallner (3tMsr8TRDP8): clean plates

- Try the one-click tool first, then build by hand (00:00:33).
- One hero frame cleaned, tracked in with a planar track expanded to the whole frame, applied as a
  corner pin (00:01:02, 00:03:51).
- The patch mask sits before the pin, so it aligns on the hero frame only; a second masked Levels
  with its own keys handles lighting drift (00:05:31, 00:06:07).
- With parallax, 3D Camera Tracker solids and plane stamps often find clean pixels in other frames
  (00:12:02, 00:13:44).
- [added] The scripted offset patch: whole-pixel offsets keep the plate's grain (patch error 3.45
  against a 2.88 grain floor); a sub-pixel offset resampled it (inner error 6.05 against 4.67).

## Tymon Reynders, After Effects Basics (e14kElpKaQo): Object Matte

- In 26.2 the Roto Brush toolbar slot holds Object Matte: hover, click, Space to propagate
  (00:00:32). Quick Selection is the old brush, Refine Edge is for hair (00:01:05).
- Effect defaults: Version 4.0, Feather 5, Contrast 80 %, Shift Edge 0, Reduce Chatter 0; Refine
  Edge Reduce Chatter 50 % (frame 00:01:19). [added] Same defaults read by script on 27.0; with no
  strokes the effect renders alpha 1.0.
- Object Matte still runs the full propagation, heavy for simple masks (00:01:37).

## Manuel Gonzalez, Manuel does Motion (0hevduJDDjg): track mattes

- Any layer can be the matte; one matte can serve many layers (00:00:52, 00:04:00).
- A matte of a matte with inversion makes boolean shapes (00:06:43). [added] On 27.0 a matte's own
  track matte was ignored in the render; the same boolean built inside a precomp worked.
