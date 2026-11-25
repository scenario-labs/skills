---
name: scenario-after-effects-compositing
description: "Use when keying a green or blue screen, cleaning a matte, roto or Object Matte, a cutout with no screen, removing a logo, wire or object, a clean plate, track mattes, or matching a foreground to its background with light wrap, grain and levels. Also when the key has a green edge, hair disappears, the matte chatters or has holes, a halo or dark ring, or the composite looks pasted on."
license: MIT
---

# After Effects compositing: keys, mattes, roto, cleanup and integration

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means every matte is measured before it is admired: alpha rendered as gray, spill
as a number, levels and grain per channel from both layers. The stance: build the matte in pieces
and judge each piece in a matte view, fix color on color and never by choking alpha, and integrate
last with levels, a faint light wrap and grain. If a sibling skill named here is missing from your
available skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

**REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit, version
traps).

## Stance (the expert delta)

1. **Key in pieces: garbage, soft matte, core matte.** One Keylight is never enough for a hard plate
   (Leonard Wilkes K-uOFPoIm6U 00:01:12, 00:10:16; Danasa _0lcyyybbng 00:01:02).
2. **Keylight View on Intermediate Result when Advanced Spill Suppressor follows** (Jake Bartlett
   tK_Z1dYgtxs 00:08:28). Final Result despills first and leaves the suppressor nothing.
3. **Clean with Clip Black and Clip White in Status view, never Screen Gain** (tK_Z1dYgtxs
   00:09:34). Measured: Screen Gain 130 opened holes in 54 % of the core; Clip 40/60 started eating
   hair.
4. **Screen Pre-blur is not free** (Bartlett starts near 0.3, 00:11:24). Measured on 1.4 px strands:
   Pre-blur 1 dropped hair coverage from 0.44 to 0.02 [added].
5. **Fix spill on the color, not by choking the alpha.** Split the alpha plate from the color plate
   (K-uOFPoIm6U 00:02:17, 00:22:44). The suppressor darkens greens; Ultra disturbs luminance least
   (00:18:30, 00:19:02).
6. **Integration is three readings: levels per channel, grain per channel, a wrap you barely see**
   (Ryan Connolly vJ8X58uknsk 00:01:34, 00:02:40; Danasa Arsad ZFJ3AKC2q8k 00:02:42).
7. **One hero fix, propagated.** One cleaned frame tracked in (Anton Thallner 3tMsr8TRDP8 00:01:02),
   one pre-render reused everywhere (_0lcyyybbng 00:09:31).
8. **A script cannot paint a matte.** Object Matte, Roto Brush, Refine Edge, Mocha and Content-Aware
   Fill are GUI work (Object Matte with no strokes renders alpha 1.0). Substitutes: keyed masks, an
   imported matte, offset patches.

## Establish first

| Input                                       | Why it changes the plan                                                | Default                                                                |
| ------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Shot type                                   | screen key, no-screen cutout, or removal                               | ask                                                                    |
| Plate codec, chroma, fps, grain             | 4:2:0 and compression need Reduce Chatter; grain sets the match target | `ae.py probe`, then step 1                                             |
| Background: plate, CG or generated          | sets level and grain targets                                           | given                                                                  |
| Project bpc, working space, linear blending | inherited color settings shift a luma matte                            | 16 bpc for keys (K-uOFPoIm6U frame 00:07:32); read `app.project` first |
| Alpha mode of every element                 | premultiplied read as straight leaves a dark ring                      | read `mainSource.alphaMode`                                            |
| Deliverable                                 | keyed comp with alpha, or the final                                    | ProRes 4444 `High Quality with Alpha`                                  |
| Channel                                     | bridge; strokes and panels go to a person                              | bridge                                                                 |

## Procedure

Jobs: [references/procedures.md](references/procedures.md). Helpers:
[scripts/comp.jsx](scripts/comp.jsx) (`AEX.comp`: `sampleColor`, `keyChain`, `setView`, `alphaView`,
`overView`, `mask`, `lightWrap`, `rimLight`, `shadeLight`, `preRender`), loaded with
`ae.py run job.jsx --lib <skill>/scripts/comp.jsx`.
[scripts/matte_metrics.py](scripts/matte_metrics.py) reads rendered PNGs (procedure 3);
`integration_check.py` gates an element against its plate (6b).

### 1. Inspect the plate

Goal: know the screen, noise and junk. In a test session, start with `AEK.core.fresh(aepPath)`, then
16 bpc. Strip a movie still's gAMA chunk before import ([procedure 1](references/procedures.md)):
After Effects renders it darker. Pick the hardest, most intricate frame.
`AEX.comp.sampleColor(comp, layer, [x, y], [halfW, halfH], t)` averages a box of clean screen.
`matte_metrics.py grain` reads grain per channel on a flat area. List stands, markers and frame-edge
junk. GATE: the screen sample has one dominant channel; grain recorded per channel.

### 2. Garbage matte

Goal: key only where the subject can be.
`AEX.comp.mask(layer, null, {keys: [{t, points}], feather: 20})`, mode `add` around the subject or
`subtract` on junk, keyed as the subject moves (K-uOFPoIm6U 00:16:11). Keep it loose: an exact
garbage matte becomes roto (keying doc). GATE: alpha 0 on the stand and screen edges at first,
middle and last frame.

### 3. Soft matte: the key chain

Goal: all the hair and motion blur, nothing of the screen.
`AEX.comp.keyChain(layer, {screen, clipBlack: 35, clipWhite: 75, cleaner: {chatter: true, contrast: 20}, spill: {method: "ultra", color: screen}})`
adds `Keylight 906`, `ADBE KeyCleaner`, `ADBE Spill2` in that order with View on Intermediate
Result. Tune clips on `setView(layer, idx, "status")` frames, then set it back. Uneven screen: a
second Keylight sampled from what is left (tK_Z1dYgtxs 00:13:37). Colored screen light: unlock
Despill Bias and Alpha Bias (00:17:30). Some settings act in Final Result only
([procedure 2](references/procedures.md)). GATE: on `alphaView`, a box of screen reads 0 and a box
inside the torso reads 1; hair shows as gray, never as gaps.

### 4. Core matte and holdouts

Goal: a solid core that never hardens the edge. Core: a duplicate of the plate, clip 40/60,
`ADBE Easy Levels2` on alpha (channel 5, input white 0.7), `ADBE Simple Choker` 3 to 5 so it stays
inside the edge (K-uOFPoIm6U 00:10:47 to 00:11:51). Subtract a mask on the core over
semi-transparent areas (veil, hair, motion-blurred edge) so the soft matte alone decides there
(00:16:11). Soften the core only inward: Channel Blur on alpha only (`ADBE Channel Blur-0004`, no
wider than the choke), with an unblurred duplicate of the core as its Alpha track matte (00:14:01;
[procedure 2b](references/procedures.md)). Never Box or Gaussian Blur there: they soften the core's
color too. Where hair and body mattes butt, set the upper one to Alpha Add, so a 15 px feather on
each is safe (00:09:10). GATE: core holes under 1 % (`matte_metrics.py holes` on alpha renders at
first, middle and last frame); core alpha 0 outside its unblurred edge; interior detail (high-pass)
equal to the unblurred core (Box Blur cuts it, 2b).

### 5. Precompose, check spill, pre-render

Goal: one keyed precomp, light to iterate on. `matte_metrics.py spill` on a white area: green excess
near 0 and luma within 1 % of the plate. Halo or spill left: recolor the color plate (stance 5).
Then `AEX.comp.preRender(keyComp, path, "High Quality with Alpha")` renders once, imports, and swaps
every use, names kept (_0lcyyybbng 00:09:31). GATE: live and pre-rendered alpha differ by 0; the
item reads `hasAlpha` true, `PREMULTIPLIED`.

### 6. Edges

Goal: edges as soft as the plate, no ring. Read premultiplied files as premultiplied. An Edge Blur
of 2 to 3 px (K-uOFPoIm6U 00:27:58) is a look choice: it raises alpha error. Pixel Motion Blur
(`ADBE OFMotionBlur`) at 45 to 90 degrees matches a fast-shutter plate (00:28:30); add it last, it
is slow (HWNAGKi6apM 00:08:09). GATE: `matte_metrics.py rim` on the key over black and over white,
before any light layer: median 0.85 to 1.15 (below, a dark ring; above, a bright edge).

### 7. Integrate

Goal: the foreground shares the plate's light, levels and texture.

- Light first ([procedure 6b](references/procedures.md)). Route before building: the check's `route`
  reads the light baked into the foreground on the neutral alone. A gap above 90 degrees to the
  plate's source (a front-lit key on a backlit plate: 111) is the hard case. Prefer a plate lit from
  the foreground's side, its ground near the subject in that same light, then levels only
  (vJ8X58uknsk 00:01:05). Plate imposed, or gap under 90: relight inside a precomp of the
  foreground. Shade fill, `shadeLight` falloff, a sun-lit copy of the key through the `rimLight`
  matte (a falloff, never a stroke).
- Levels ([procedure 6](references/procedures.md)): a neutral pair in both layers: solve per
  channel. None (sunset, colored element): one luma gain for the three channels, from the subject's
  1st and 99th percentile to the plate's near it.
- Light wrap: `AEX.comp.lightWrap(comp, fg, bg, {radiusPct: 1.5, opacity: 40, mode: "add"})` copies
  both layers with transforms, masks and effects (ZFJ3AKC2q8k 00:02:14); precompose a parented layer
  first. Hero shots add a second, smaller, stronger wrap on highlights (K-uOFPoIm6U 00:29:36).
- Grain, last (vJ8X58uknsk 00:02:40). Measure both layers (`grain`, `tgrain`). Plate grainier: Add
  Grain (`VISINF Grain Implant`, Viewing Mode 3) on the element only; over the whole frame it
  doubles the plate's grain. Both far cleaner: one shared Add Grain on top
  ([procedure 7](references/procedures.md)). GATE:
  [scripts/integration_check.py](scripts/integration_check.py) exits 0 on the first and last frame
  (light, shade, rim, material, finish; shadow gates when grounded; `--rendered` for a 3D render).
  Levels: subject 1st percentile within 0.03 of the plate's, 99th no more than 0.02 above the
  plate's near the subject. Grain within 10 % per channel at the same tone; shared route: moving
  grain on both layers (`tgrain` on static areas only). Wrap: `matte_metrics.py wrapbins`, darkest
  background bin under half the brightest.

### 8. Product cutout with no screen

Goal: a matte without a screen. Routes ([procedure 8](references/procedures.md)): Object Matte
strokes by a person, then a script sets Feather, Shift Edge and Reduce Chatter (8b); Difference
Matte on a locked-off shot with a clean plate; unattended, an external matte from
scenario-after-effects-generation as a Luma or Alpha track matte (8a); a rigid product, a tracked
mask from scenario-after-effects-tracking. GATE: matte frame count equals plate frame count; alpha
at first, middle and last frame on one sheet. One frame of slip doubles the error (8a).

### 9. Logo removal on a moving T-shirt

Goal: no logo, fabric texture and grain intact. GUI: Content-Aware Fill. Scripted: the plate offset
by whole pattern periods under a tracked, feathered matte, or a cleaned hero frame corner pinned in
([procedure 9](references/procedures.md)). GATE: error inside the patch near the grain floor; no
ring; patch on every frame.

## Numbers

| Value                      | Number                                     | Relative to                                       |
| -------------------------- | ------------------------------------------ | ------------------------------------------------- |
| Keylight clips, soft matte | Clip Black 35, Clip White 75               | 0 to 100; start 14/61 per Bartlett frame 00:12:16 |
| Keylight clips, core       | 40/60 plus Levels input white 0.7          | alpha channel                                     |
| Simple Choker on core      | 3 to 5 px (Wilkes 5 to 10)                 | plate pixels                                      |
| Key Cleaner                | Reduce Chatter on, Alpha Contrast 20       | _0lcyyybbng 00:06:13                              |
| Garbage, holdout feather   | 20 px, 6 px                                | 1280x720 plate                                    |
| Light wrap                 | 1 to 1.5 % of comp height, 30 to 40 %, Add | 1.5 % = 11 px at 720                              |
| Grain match tolerance      | 10 % per channel                           | std of image minus 5x5 blur                       |
| Level match tolerance      | 2/255 per channel                          | 1st and 99th percentile                           |

## Quality gates

Run [references/critique.md](references/critique.md). Measurable: chain order and View 10; no Status
view left on; track mattes resolved; frame counts equal; spill, holes, rim, levels, grain and wrap
within the step gates; `integration_check.py` exit 0; `ae.py probe` on alpha renders. Visual, on
full-size frames: hair as gray, no core holes, no outline on the shade side.

## Common mistakes

| Mistake                                              | Symptom                                     | Fix                                                                                                                        |
| ---------------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Final Result plus Spill2                             | suppressor does nothing, shirt darker       | View Intermediate Result                                                                                                   |
| Hard Colour or Despill Bias with View Intermediate   | no change in the render                     | they act in Final Result; fix on the color plate                                                                           |
| Screen Gain to clean the screen                      | holes in the core, hard hair                | Clip Black and White in Status view                                                                                        |
| Set Matte pointed at a layer keyed in place          | alpha 1.0 everywhere: it reads the source   | point at a precomp of the key                                                                                              |
| Matte of a matte                                     | the inner track matte is ignored            | build the boolean inside a precomp                                                                                         |
| Effects on the matte forgotten                       | edge moves (Simple Choker 20 moved it 7 px) | the matte is read after its own effects                                                                                    |
| Add Grain left in Preview                            | grain only in a box, its outline rendered   | Viewing Mode Final Output                                                                                                  |
| Premultiplied read as straight                       | dark ring                                   | Interpret Footage > Premultiplied                                                                                          |
| Luma matte under inherited color settings            | 50 % gray reads 0.737                       | test sessions: `AEK.core.fresh()` resets engine, bpc, working space, linear blending, gamma; a person's project: read them |
| Relight layers matted in the main comp               | light outline on the shade-side edge        | relight inside a precomp of the foreground, solids on Preserve Underlying Transparency (6b)                                |
| Light judged on the frame or by "better than before" | front-lit subject passes review             | `integration_check.py` on the first and last frame; its ratio divides out albedo (6b)                                      |
| Rim drawn as a stroke                                | pale line of constant width, hard inside    | sun-lit copy of the key through a directional matte; the rim gate reads width and hardness (6b)                            |

## Handoffs

- Receives plates and track data from scenario-after-effects-tracking (point, planar or camera solve
  for masks, patches and corner pins).
- Receives generated backgrounds, clean frames, mattes and elements through
  scenario-after-effects-generation: raw input that needs level, grain and alpha checks here. Its
  seated objects and 3D renders pass `integration_check.py` too.
- Receives 3D precomps from scenario-after-effects-3d, procedural elements from
  scenario-after-effects-vfx.
- Gives keyed and pre-rendered precomps to scenario-after-effects-color-delivery (grade, output with
  alpha) and scenario-after-effects-project (pre-render naming, collect).
- Matte rigs driven by expressions: scenario-after-effects-expressions.

## Version notes

- 26.2: Object Matte replaces the Roto Brush tool; its effect is `ADBE Samurai` (Obsolete in
  `app.effects` on 27.0).
- 23.0: track matte picker, any layer as matte. 26.0: native Unmult (`ADBE Unmult`); Color Key and
  Luma Key obsolete.

## References

- [references/procedures.md](references/procedures.md): every job with channel, checked line and the
  check that follows.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps.
- [references/critique.md](references/critique.md): the self-review rubric with numbers and
  contact-sheet checks.
- [references/gui-paths.md](references/gui-paths.md): menus, panels, shortcuts, and what scripts
  cannot reach.
- [references/sources.md](references/sources.md): every video and document used.
