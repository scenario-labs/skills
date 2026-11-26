---
name: scenario-after-effects-vfx
description: "Use when building effects in After Effects with built-in tools: glow, sparks, bursts, embers, dust, smoke, flame, shockwave rings, light rays, lightning, heat haze, lens finish, or when a glow burns to white, rays gray the frame, particles look like sand, or the effect does not sit in the plate."
license: MIT
---

# After Effects Effects with Built-in Tools

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means light that adds in known amounts and never burns to a flat blob, particles
set in pixels and counts, and an effect that lights, reflects in and dims its plate. Set amounts in
pixels and stops, render frames, count pixels. Every effect uses what ships with After Effects. If a
sibling skill named here is missing from your available skills, load it with `skill_get` (Scenario
MCP) or ask the user to install it (https://github.com/scenario-labs/skills#install); unattended,
proceed from tool schemas and flag the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert
(channels, review loop, toolkit, version traps).

## Stance (the expert delta)

- **Light is gray, summed, bloomed, colored once** [added, measured]. Build every bright element as
  gray light in one light comp, sum it in Add, bloom it with Gaussian Blur copies at doubling radii,
  then color the sum once with a five-tone luminance map (CC Toner, Pentone). The core lands on the
  top tone and stops there. Glow effects stacked on a colored layer clipped 4 % of the frame at 16
  bpc and 64 % at 32 bpc.
- **The rig goes over the plate in Screen.** Add only over near-black. In Add the rig clipped up to
  36,550 px over a lit plate; in Screen, none.
- **Amounts in pixels and stops, never raw effect values.** A light level is a gain (stops = log2
  gain) on an Exposure with Bypass Linear Light Conversion on, an exact multiply at every depth. A
  bloom is radii in px and a total gain. A particle is a diameter in px, a speed in px/s, a count on
  screen.
- **16 bpc, Adobe color management.** One Glow takes a disc at 1.0 to 1.1 to 1.4x its light at 16
  bpc and up to 15x at 32 bpc, so Glow settings do not carry between depths. 16 bpc gave identical
  GPU and software frames and bounded light; in an OCIO project (32 bpc only) redo the amounts.
- **Know which layer the effect sits on.** Optics Compensation goes on the scene layer, then its
  Scale. A Displacement Map ignores the map layer's effects: maps are precomps. Masks run before
  effects. Echo acts on what changes inside the layer.
- **Hierarchy before detail.** One hero, few large pieces, many small dim ones, 5 to 10x variation,
  a hot core with a radial falloff, dark air between. Draw the body of a burst as procedural streaks
  and keep particles as 30 to 150 accents; budget the light at the center across core, streaks,
  flash and sparks. A frame where every piece has the same size and brightness reads as sand or haze
  (Andrew Kramer, JYbgjCR8PMI 00:05:35; Texturelabs, ac9Wh6-4jH4).
- **Two rigs by depth, one envelope.** Light behind the subject goes in a BACK rig held out by the
  subject matte after its bloom; core, flash, front streaks and embers go in a FRONT rig. The matte
  is choked about 2 px, never blurred outward, and the BACK light comes back as a rim and a light
  wrap on the edges facing the source. Interactive light is the plate tinted toward the light color,
  fading with distance from the origin. One envelope null with sliders from one hit time drives
  light, reflection, pool, interactive light and shake (ActionVFX, HWNAGKi6apM 00:17:30).
- **A loop is exact: frame L equals frame 0.** Fractal Noise and Turbulent Displace with Cycle
  Evolution and whole revolutions; particles from two offset copies of a longer simulation (Jake
  Bartlett, kdttSozSLG4 00:03:20).

## Establish first

- **Plate:** size, rate, motion blur, black level (1st percentile per channel), grain std.
  `ae.py probe` and one frame.
- **Look in numbers:** palette (the mid tone and the top tone), core size in px, count on screen,
  speed in px/s, frames it holds, where the title sits.
- **Depth, color engine, plugins:** `bitsPerChannel`, `colorManagementSystem`, `app.effects` (no
  particle plugin: procedures section 21).

## Procedure

1. **Set up.** `AEX.vfx.depth(16)`; import the plate with `AEX.vfx.plate()`; dump the match names of
   any effect before scripting it (procedures section 0). GATE: `{bpc: 16}` (32 in OCIO); match
   names read live.

2. **Build the light rig.** `AEX.light.rig(comp, name, {bloom, tones})`. Bloom from
   `AEX.glow.plan()`: r0 12 px, 5 copies, total 2.0, each 0.75x the previous. Tones: shadow black,
   dark = mid x 0.3 in the mid's hue, mid, bright, high, every channel at 0.95 or less (`rig`
   warns). Rig layer in Screen (procedures section 2). GATE: 0 px at 255 in all channels on 8
   frames; GPU and software frames identical.

3. **Build each element as gray light** inside `<name>_light`, level set with
   `AEX.light.add(layer, lum)`:

| Ask                                | Built-in build                                                                                               | Helper, procedures section             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------- |
| Sparks from a point in the air     | CC Particle World from px targets, Composite; from an object on a plate, the pulse's streaks and embers (13) | `AEX.pn.sparks`, 3                     |
| Burst with direction               | radial noise streaks through Polar Coordinates, core cones, 30 to 150 sparks with Echo trails                | `AEX.burst.build`, 4                   |
| Embers, dust in a beam, title hole | few motes by depth, soft discs, slow rise, no swirl, exact loop                                              | `AEX.atmo.build`, `AEX.motes.build`, 5 |
| Smoke plume (stylized, accent)     | stringy noise through a narrow column and a wide leaning crown, swayed with height                           | `AEX.smoke.build`, 6                   |
| Flame (stylized, accent)           | fixed source pushed up by a one-sided map, three noise scales, one tone map, sharpen                         | `AEX.smoke.flame`, 7                   |
| Shockwave ring                     | stroke wake, polar band or noise wisps; refraction                                                           | `AEX.shock.*`, 8                       |
| Volumetric rays                    | CC Light Rays on the light only, under the foreground                                                        | `AEX.rays.rig`, 9                      |
| Lightning                          | Advanced Lightning core, envelope, spill                                                                     | `AEX.bolt.strike`, 10                  |
| Heat haze, glass ring              | red/green map precomps, padded plate, split                                                                  | `AEX.distort.apply`, 11                |
| Trail, snow, dissolve, loop, HUD   | shape path, three snow planes, Gradient Wipe                                                                 | 14 to 19                               |

**Routing rule for natural elements.** Built-in effects for stylized or energy looks, loops and
small accents, a realistic wisp included (`vfx_measure.py wisp`: 8 % of the frame tall, 10 levels
over the plate, 1 s). Realistic fire and smoke that fill the frame: an element on black from
scenario-after-effects-generation (model picked by the Scenario MCP `recommend` tool), landed with
`AEX.element.land` (procedures section 13). Dust stays built-in. GATE: each element reads in gray
over black on 3 frames; its peak sits at the level planned.

4. **Check the hierarchy.** Render start, peak and end. One hero, few large pieces, many small dim
   ones; sizes and brightness vary 5 to 10x; the core has a radial falloff; at least a third of the
   effect's area stays dark air. If not, remove pieces before adding any (critique.md gives what to
   do for each failure picture). GATE: the five visual checks pass on the peak frame.

5. **Integrate on the plate.** `AEX.pulse.build()` with `subjectBox`: subject matte (luma key on a
   dark plate, else a supplied `matte`), `ENV` null, FLOOR, BACK and FRONT rigs in Screen. The wave
   is a ring on the floor plane in perspective, its back half behind the subject; streaks and embers
   leave from the subject's outline. BACK is held out by the matte choked 2 px; rim, wrap,
   interactive light, pool, reflections, lens last. A moving plate: no end hold, origin and floor
   line on a tracked null. A daylight plate: procedures section 13. Without a subject in front,
   `AEX.integrate.build()`. GATE: `AEX.pulse.gateFrames` then `vfx_measure.py gates` (exit 0): 0 %
   clipped, contour ratio, far-side outline, blacks, grain, hold, hit strength 0.7 to 0.95 (under
   0.5 the hit does nothing, over 1.0 it burns).

6. **Lens and motion.** Optional lens finish (`AEX.lens.apply`): CA 0.15 % (2.7 px corners, 0
   center), halation above 0.75, CC Vignette 100 (-0.5 stop), Add Grain last at the plate's std over
   4.2 levels per unit (dark) or 2.2 (mid gray), only where the picture lost grain (procedures 13).
   Motion blur: shutter 90 on fast rings, the first 2 frames sharp (`AEX.shock.mbSplit`); the switch
   goes on the particle layer and on every comp and nested comp layer above it. GATE: corner fringe
   2 to 4 px; grain std within 10 % of the plate's, frame to frame or before the CA (channel-scale
   CA changes the spatial std).

7. **Loop, measure, render.** `AEX.vfx.loopNoise()` for noise; `AEX.atmo.loopPair()` for particles.
   `AEX.vfx.cost()` for frames, a render-queue job for ms per frame, `aerender` from the shell,
   `ae.py probe` (procedures section 20). GATE: frame L against frame 0 differs by 0; ms per frame
   recorded; probe matches the plan.

## Numbers

| Value                                  | Meaning                                                                                                       |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| stops = log2(gain)                     | Exposure with `-0022` Bypass Linear Light on: exact multiply (0.5 at -1 stop read 0.2500)                     |
| r0 12, x2, 5 copies, total 2.0, k 0.75 | default bloom; gains 0.66, 0.50, 0.37, 0.28, 0.21; total 0.6 reads as none, 3.0 burns thin strokes            |
| 0, 0.25, 0.5, 0.75, 1                  | CC Toner Pentone luminance of shadow, dark, mid, bright, high                                                 |
| 110 x rate x life                      | CC Particle World particles alive                                                                             |
| count x fps / (132 x frames)           | Birth Rate for a held burst                                                                                   |
| size x width x 0.075 px                | visible particle diameter (`AEX.pn.K.diamPerWidth`); smallest visible size 0.015 for spheres at 1920 (2.2 px) |
| 0.58 x width x Velocity                | px/s at the burst edge                                                                                        |
| 3.2 x width x Gravity                  | px/s² with Resistance 0; Resistance R decays speed as exp(-0.7 R t)                                           |
| 15 to 70 degrees                       | Cone Axis Extra Angle (emits on a cone at that angle; above 90 goes backwards)                                |
| 90 degrees, 2 sharp frames             | shutter for a ring moving about 100 px per frame                                                              |
| 4.2 / 2.2 levels per unit              | Add Grain frame-to-frame std near black / at mid gray                                                         |

## Quality gates

- Measurable: 0 px at 255 in all channels on the rig; clipped under 1 % after integration; loop
  difference 0; particle counts within 15 % of target; foreground lift 0 under rays; polar seam
  score under 0.5 (step at 12 o'clock over the median radial step); ms per frame recorded.
- Visual, on one contact sheet over the plate (start, peak, end):
  - **Hierarchy:** one element clearly dominates. Do instead: cut secondary elements to half their
    light.
  - **Few large elements:** 3 to 6 large pieces carry the shape. Do instead: move light from many
    small pieces into a few large ones.
  - **Variation 5 to 10x:** in size, speed and brightness. Do instead: widen Size Variation, split
    into speed tiers and planes.
  - **Core with a radial falloff:** the hottest point sits inside a colored falloff, with no flat
    disc at the attack of a hit. Do instead: budget the center across all elements; lower the source
    level so only the center reaches the top tone.
  - **Air:** dark gaps between streaks and wisps. Do instead: fewer particles, lower bloom total on
    the wide copies.
- Full rubric with the failure pictures: [references/critique.md](references/critique.md).

## Common mistakes

More rows (polar precomp, padding, ring sign, Optics Compensation, origin inside the subject, Cone
Axis angle, `canAddProperty`): critique.md, More mistakes.

| Mistake                                    | Symptom                                | Fix                                                            |
| ------------------------------------------ | -------------------------------------- | -------------------------------------------------------------- |
| Glow stack on a colored layer              | flat cream blob, clipped core          | light rig: gray light, Gaussian bloom, CC Toner map            |
| Rig in Add over a lit plate                | clipped highlights on the plate        | Screen; Add only over near-black                               |
| Rays built from the whole frame            | gray haze, lifted blacks               | rays from the light only, under the foreground                 |
| Shutter 180 or 360 on a fast ring          | ring smears to a disc                  | 90 degrees, first 2 frames sharp                               |
| Sparks in Add, dense                       | white mass, no color                   | Transfer Mode 1 Composite, one Add at the end                  |
| Death Size below the visible minimum       | sparks vanish mid-life                 | Death Size at least 0.015 (spheres at 1920)                    |
| Holdout matte blurred outward              | dark line between subject and glow     | choke 2 px, rim and wrap from the back light                   |
| One rig over and behind the subject        | glow ball, subject washed to cream     | BACK and FRONT rigs, BACK held out after bloom                 |
| Large flash or wide core                   | cream blob, flat disc                  | flash 0.16 over 380 px; cones 18, 90, 320 px; rig `headroom` 2 |
| Screen-facing ring on an object on a floor | a dome sitting on the subject          | `wave: "floor"`                                                |
| Streaks from `center`                      | sparks leave from one point at the top | `emit: "surface"` with `subjectBox`                            |

## Handoffs

- Receives from scenario-after-effects-tracking: a null on the real point. From
  scenario-after-effects-generation: elements on black and particle textures. From
  scenario-after-effects-project: comp and plate settings.
- Delivers to scenario-after-effects-compositing (mattes, grain matching),
  scenario-after-effects-color-delivery (grade, render), scenario-after-effects-3d (real 3D scenes),
  scenario-after-effects-expressions and scenario-after-effects-animation.

## Version notes

Version traps (Curl Noise, Unmult, Advanced Lightning at 8 bpc, OCIO, HDR Highlight Compression):
procedures section 22.

## References

- [references/procedures.md](references/procedures.md): match names, every procedure with goal,
  steps, gate and trap.
- [references/critique.md](references/critique.md): numeric gates and the failure pictures with what
  to do instead.
- [references/expert-notes.md](references/expert-notes.md): expert judgment by channel and
  timestamp.
- [references/gui-paths.md](references/gui-paths.md): Effect menu paths and settings per recipe.
- [references/sources.md](references/sources.md): every source with URL.
- Pixel gates: [scripts/vfx_measure.py](scripts/vfx_measure.py) (numpy, Pillow). Composite builders
  return names; the layer is `AEK.core.layer(comp, r.layer)`.
- Script: [scripts/vfx.jsx](scripts/vfx.jsx): `AEX.vfx`, `AEX.light`, `AEX.glow`, `AEX.pn`,
  `AEX.burst`, `AEX.atmo`, `AEX.smoke`, `AEX.fire`, `AEX.plume`, `AEX.motes`, `AEX.element`,
  `AEX.shock`, `AEX.rays`, `AEX.bolt`, `AEX.distort`, `AEX.lens`, `AEX.integrate`, `AEX.pulse`.
