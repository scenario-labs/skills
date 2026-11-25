---
name: scenario-after-effects-compositing
description: "Use when keying a green or blue screen, pulling or cleaning a matte, rotoscoping, cutting out a person or product with no screen behind it, removing a logo, wire, mic or object from footage, building a clean plate, using track mattes, Set Matte or Alpha Add, or making a foreground sit in a background with light wrap, grain match and level match. Also when someone says the key has a green edge, the hair disappears, the matte chatters or has holes, there is a halo or a dark ring, the white shirt is green, the composite looks pasted on, the grain does not match, Object Matte or Roto Brush, or Content-Aware Fill smears."
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
   (Leonard Wilkes K-uOFPoIm6U 00:01:12, 00:10:16; ActionVFX _0lcyyybbng 00:01:02). Measured mean
   alpha error: 0.28 at defaults, 0.0051 for garbage, soft and core with a holdout.
2. **Keylight View on Intermediate Result when Advanced Spill Suppressor follows** (Jake Bartlett
   tK_Z1dYgtxs 00:08:28). Final Result despills inside Keylight and leaves the suppressor nothing to
   do. Measured shirt luma: 0.880 with Keylight's despill, 0.929 (the plate's) with Ultra.
3. **Clean with Clip Black and Clip White in Status view, never Screen Gain** (tK_Z1dYgtxs
   00:09:34). Measured: Screen Gain 130 opened holes in 54 % of the core. Clip 35/75 kept hair at
   0.44 coverage against 0.53 truth; 40/60 started eating it.
4. **Screen Pre-blur is not free.** Bartlett starts near 0.3 (00:11:24). Measured on 1.4 px strands:
   Pre-blur 1 dropped hair coverage from 0.44 to 0.02 [added]. Keep it at 0 on thin hair.
5. **Fix spill on the color, not by choking the alpha.** Split the alpha plate from the color plate
   (K-uOFPoIm6U 00:02:17, 00:22:44). The suppressor darkens greens; Ultra disturbs luminance least
   (00:18:30, 00:19:02).
6. **Integration is three readings: levels per channel, grain per channel, a wrap you barely see**
   (Ryan Connolly vJ8X58uknsk 00:01:34, 00:02:40; Danasa Arsad ZFJ3AKC2q8k 00:02:42). Measured: 1.5
   % of comp height at 40 % Add lifted edges 4.7/255 against a window; 4 % at 100 % gave 20/255, a
   glow.
7. **One hero fix, propagated.** One cleaned frame tracked in (Anton Thallner 3tMsr8TRDP8 00:01:02),
   one pre-render reused everywhere (_0lcyyybbng 00:09:31). Try the one-click tool first, then build
   by hand (3tMsr8TRDP8 00:00:33).
8. **A script cannot paint a matte.** Object Matte, Roto Brush, Refine Edge strokes, Mocha shapes
   and Content-Aware Fill are GUI work. Object Matte added by script with no strokes renders alpha
   1.0. Substitutes: keyed masks, an imported matte as track matte, offset patches.

## Establish first

| Input                                       | Why it changes the plan                                                       | Default                                                                |
| ------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Shot type                                   | screen key, no-screen cutout, or removal                                      | ask                                                                    |
| Plate codec, chroma, fps, grain             | 4:2:0 and compression need Reduce Chatter; grain sets the match target        | `ae.py probe`, then step 1                                             |
| Background: plate, CG or generated          | sets level and grain targets                                                  | given                                                                  |
| Project bpc, working space, linear blending | a 50 % gray luma matte read 0.502 clean, 0.737 under inherited color settings | 16 bpc for keys (K-uOFPoIm6U frame 00:07:32); read `app.project` first |
| Alpha mode of every element                 | premultiplied read as straight leaves a dark ring                             | read `mainSource.alphaMode`                                            |
| Deliverable                                 | keyed comp with alpha, or the final                                           | ProRes 4444 `High Quality with Alpha`                                  |
| Channel                                     | bridge; strokes and panels go to a person                                     | bridge                                                                 |
| Generated inputs                            | backgrounds, clean frames, mattes from scenario-after-effects-generation      | ask before generating                                                  |

## Procedure

Full jobs are in [references/procedures.md](references/procedures.md). Helpers:
[scripts/comp.jsx](scripts/comp.jsx) (`AEX.comp`: `sampleColor`, `keyChain`, `setView`, `alphaView`,
`overView`, `mask`, `lightWrap`, `preRender`), loaded with
`ae.py run job.jsx --lib <skill>/scripts/comp.jsx`.
[scripts/matte_metrics.py](scripts/matte_metrics.py) reads rendered PNGs: alpha error against a
reference, spill, grain, levels, edge width, difference.

### 1. Inspect the plate

Goal: know the screen, noise and junk. Pick the hardest frame (keying doc: tune on one intricate
frame). `AEX.comp.sampleColor(comp, layer, [x, y], [halfW, halfH], t)` averages a box of clean
screen. `matte_metrics.py grain` reads grain per channel on a flat area. List stands, markers and
frame-edge junk. Trap: from a script, `sampleImage` returns `[0,0,0,0]` unless read at the comp's
current time; the helper moves `comp.time` and restores it. GATE: the screen sample has one dominant
channel; grain recorded per channel.

### 2. Garbage matte

Goal: key only where the subject can be.
`AEX.comp.mask(layer, null, {keys: [{t, points}], feather: 20})`, mode `add` around the subject or
`subtract` on junk, keyed as the subject moves (K-uOFPoIm6U 00:16:11). Keep it loose: an exact
garbage matte becomes roto (keying doc). GATE: alpha 0 on the stand and screen edges at first,
middle and last frame. Measured: mean error 0.100 to 0.015, stand gone.

### 3. Soft matte: the key chain

Goal: all the hair and motion blur, nothing of the screen.
`AEX.comp.keyChain(layer, {screen, clipBlack: 35, clipWhite: 75, cleaner: {chatter: true, contrast: 20}, spill: {method: "ultra", color: screen}})`
adds `Keylight 906`, `ADBE KeyCleaner`, `ADBE Spill2` in that order with View on Intermediate
Result. Tune clips with `setView(layer, idx, "status")` frames, then set it back. Uneven screen: a
second Keylight sampled from what is left (tK_Z1dYgtxs 00:13:37); Ultra Tolerance near 100
(00:03:31). Screen lit by colored light: unlock Despill Bias and Alpha Bias (00:17:30). Replace
Method, Despill Bias and Edge Colour Correction act in Final Result only (in Intermediate Result,
Hard and Soft Colour render identical): with the suppressor, fix shirt artifacts on the color plate
(step 5). Keyed keying properties: Hold when several interact (keying doc). GATE: on `alphaView`, a
box of screen reads 0 and a box inside the torso reads 1; hair shows as gray, never as gaps.

### 4. Core matte and holdouts

Goal: a solid core that never hardens the edge. Core: a duplicate of the plate, clip 40/60,
`ADBE Easy Levels2` on alpha (channel 5, input white 0.7), `ADBE Simple Choker` 3 to 5 so it stays
inside the edge (K-uOFPoIm6U 00:10:47 to 00:11:51). Subtract a mask on the core over
semi-transparent areas (veil, hair, motion-blurred edge) so the soft matte alone decides there
(00:16:11). Soften the core only inward: blur no wider than the choke, with an unblurred duplicate
of the core as its Alpha track matte (00:14:01; [procedure 2b](references/procedures.md)). Where
hair and body mattes butt, set the upper one to Alpha Add, so a 15 px feather on each is safe
(00:09:10). GATE: core holes under 1 %; core alpha 0 outside its unblurred edge. Measured: holdout
speckle 0.171 to 0.058 standard deviation; Alpha Add seam 1.0 against 0.878 in Normal; inward blur 0
px outside the core, 33,070 px without the matte.

### 5. Precompose, check spill, pre-render

Goal: one keyed precomp, light to iterate on. `matte_metrics.py spill` on a white area: green excess
near 0 and luma within 1 % of the plate. Halo or spill left: recolor a color plate held by the key's
Alpha track matte, never choke the alpha (K-uOFPoIm6U 00:02:17, 00:22:44). Then
`AEX.comp.preRender(keyComp, path, "High Quality with Alpha")` renders once, imports, and swaps
every use, names kept (_0lcyyybbng 00:09:31). GATE: live and pre-rendered alpha differ by 0; the
item reads `hasAlpha` true, `PREMULTIPLIED`. Measured: 1,503 ms down to 263 ms per frame.

### 6. Edges

Goal: edges as soft as the plate, no ring. Read premultiplied files as premultiplied. An Edge Blur
of 2 to 3 px (K-uOFPoIm6U 00:27:58) is a look choice: alpha error rose from 0.099 to 0.115 at 2 px.
Pixel Motion Blur (`ADBE OFMotionBlur`) at 45 to 90 degrees matches a plate shot with a fast shutter
(00:28:30); add it last, it is slow (ActionVFX HWNAGKi6apM 00:08:09). GATE: over white and over
black, no dark or bright rim.

### 7. Integrate

Goal: the foreground shares the plate's light, levels and texture.

- Levels: sample the element's and the plate's black and white, solve `ADBE Pro Levels2` output
  black and white per channel ([procedure 6](references/procedures.md)). Light direction cannot be
  graded (vJ8X58uknsk 00:01:05): flag it to the user.
- Light wrap: `AEX.comp.lightWrap(comp, fg, bg, {radiusPct: 1.5, opacity: 40, mode: "add"})`. It
  reads the foreground precomp, so masks on the foreground carry (ZFJ3AKC2q8k 00:02:14). Hero shots
  add a second, smaller and stronger wrap limited to highlights (K-uOFPoIm6U 00:29:36).
  Keylight-only key: Edge Brightness in Final Result is a quick wrap (tK_Z1dYgtxs 00:23:17).
- Grain, last (vJ8X58uknsk 00:02:40): Add Grain (`VISINF Grain Implant`) with Viewing Mode Final
  Output (3) and per-channel intensity = plate grain / grain at intensity 1; or Match Grain
  (`VISINF Grain Duplication`) from the plate, Viewing Mode 5. GATE: blacks and whites within 2/255
  per channel of the plate; grain within 10 % per channel at the same tone; the wrap shows only
  against bright background.

### 8. Product cutout with no screen

Goal: a 120-frame matte without a screen. Object Matte, run by a person: toolbar Object Matte tool
(the former Roto Brush slot), double-click the layer, click the product, Space, Freeze
([gui-paths](references/gui-paths.md)). Locked-off camera with a clean plate: Difference Matte
(Effect > Keying) is the alternative (K-uOFPoIm6U 00:30:48; keying doc). A script then sets Feather,
Shift Edge and Reduce Chatter by match name and pre-renders
([procedure 8b](references/procedures.md)). Unattended substitute: an external matte (segmentation
or layer separation through scenario-after-effects-generation), imported at the plate rate as a Luma
or Alpha track matte. A rigid product can take a tracked mask (track from
scenario-after-effects-tracking). GATE: matte frame count equals plate frame count; alpha at first,
middle and last frame on one sheet. Measured: an external matte reproduced the reference exactly;
one frame of slip doubled the best key's error (0.0101, edge 0.12).

### 9. Logo removal on a moving T-shirt

Goal: no logo, fabric texture and grain intact. GUI path: Subtract mask around the logo, Window >
Content-Aware Fill, Fill Method Surface, Alpha Expansion, Lighting Correction when light shifts
(Content-Aware Fill doc). Scripted substitute: the plate offset by whole pattern periods under a
tracked, feathered ellipse matte. Hero-frame route: clean one frame (paint, or an edit through
scenario-after-effects-generation), track it in with a corner pin, add a masked Levels for lighting
drift (3tMsr8TRDP8 00:01:02, 00:06:07). The patch mask sits before the pin, so it lines up on the
hero frame only: key it on other frames (00:05:31). GATE: error inside the patch near the grain
floor; no ring; patch present on every frame. Measured: 30.4 down to 3.45 against a 2.88 floor. A
sub-pixel offset softened the grain (inner error 4.67 to 6.05): use whole pixels.

## Numbers

| Value                      | Number                                     | Relative to                                       |
| -------------------------- | ------------------------------------------ | ------------------------------------------------- |
| Keylight clips, soft matte | Clip Black 35, Clip White 75               | 0 to 100; start 14/61 per Bartlett frame 00:12:16 |
| Keylight clips, core       | 40/60 plus Levels input white 0.7          | alpha channel                                     |
| Simple Choker on core      | 3 to 5 px (Wilkes 5 to 10)                 | plate pixels                                      |
| Key Cleaner                | Reduce Chatter on, Alpha Contrast 20       | _0lcyyybbng 00:06:13                              |
| Garbage feather            | 20 px                                      | 1280x720 plate                                    |
| Holdout feather            | 6 px                                       | same                                              |
| Light wrap                 | 1 to 1.5 % of comp height, 30 to 40 %, Add | 1.5 % = 11 px at 720                              |
| Grain match tolerance      | 10 % per channel                           | std of image minus 5x5 blur                       |
| Level match tolerance      | 2/255 per channel                          | 1st and 99th percentile                           |

## Quality gates

Run [references/critique.md](references/critique.md). Measurable: chain order and View 10; no Status
view left on; track mattes resolved; matte and plate frame counts equal; spill, levels and grain
within tolerance; `ae.py probe` on alpha renders. Visual, one sheet per shot: hair as gray, no core
holes, no rim over black or white, wrap invisible on dark areas.

## Common mistakes

| Mistake                                            | Symptom                                                    | Fix                                                                                                                        |
| -------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Final Result plus Spill2                           | suppressor does nothing, shirt darker                      | View Intermediate Result                                                                                                   |
| Hard Colour or Despill Bias with View Intermediate | no change in the render                                    | they act in Final Result; fix on the color plate                                                                           |
| Screen Gain to clean the screen                    | holes in the core, hard hair                               | Clip Black and White in Status view                                                                                        |
| Set Matte pointed at a layer keyed in place        | alpha 1.0 everywhere: it reads the source                  | point at a precomp of the key                                                                                              |
| Matte of a matte                                   | the inner track matte is ignored                           | build the boolean inside a precomp                                                                                         |
| Effects on the matte forgotten                     | edge moves (Simple Choker 20 moved it 7 px)                | the matte is read after its own effects                                                                                    |
| Add Grain left in Preview                          | grain only in a box, its outline rendered                  | Viewing Mode Final Output                                                                                                  |
| Add Grain at default intensity                     | about half the plate grain; 40 % more in shadows than mids | calibrate per channel on the subject's tone                                                                                |
| Premultiplied read as straight                     | dark ring                                                  | Interpret Footage > Premultiplied                                                                                          |
| Luma matte under inherited color settings          | 50 % gray reads 0.737                                      | test sessions: `AEK.core.fresh()` resets engine, bpc, working space, linear blending, gamma; a person's project: read them |
| Sequence import in a shared folder                 | every numbered file joins                                  | one folder per sequence                                                                                                    |

## Handoffs

- Receives plates and track data from scenario-after-effects-tracking (point, planar or camera solve
  for masks, patches and corner pins).
- Receives generated backgrounds, clean frames, mattes and elements through
  scenario-after-effects-generation: raw input that needs level, grain and alpha checks here.
- Receives 3D precomps from scenario-after-effects-3d; procedural elements from
  scenario-after-effects-vfx.
- Gives keyed and pre-rendered precomps to scenario-after-effects-color-delivery (grade, output with
  alpha) and scenario-after-effects-project (pre-render naming, collect).
- Matte rigs driven by expressions: scenario-after-effects-expressions.

## Version notes

- 26.2: Object Matte replaces the Roto Brush tool in the toolbar; its effect is `ADBE Samurai`,
  listed under Obsolete in `app.effects` on 27.0, Version 4 by default. Tutorials that start with
  the Roto Brush tool predate it.
- 23.0: track matte picker; any layer can be the matte, shared by many layers. Tutorials before it
  say "the layer above".
- 26.0: native Unmult (`ADBE Unmult`). Color Key and Luma Key are obsolete; use Keylight first.
- The enum is spelled `BlendingMode.SILHOUETE_ALPHA` in the API.

## References

- [references/procedures.md](references/procedures.md): every job with channel, checked line and the
  check that follows.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps.
- [references/critique.md](references/critique.md): the self-review rubric with numbers and
  contact-sheet checks.
- [references/gui-paths.md](references/gui-paths.md): menus, panels, shortcuts, and what scripts
  cannot reach.
- [references/sources.md](references/sources.md): every video and document used.
