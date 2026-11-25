---
name: scenario-after-effects-animation
description: "Use when animating in After Effects with keyframes: slide-ins, pops, product cards, UI and logo moves, bounces, overshoot, anticipation, overlap and stagger, follow-through, arcs, parenting to nulls, camera moves from nulls, motion blur, or retiming. Also when someone says my animation feels stiff, floaty, robotic or linear, everything moves at once, the ease looks default, Easy Ease is not enough, the layer drifts between two identical keyframes, the bounce looks wrong, the overshoot wobbles, motion blur does not show, give me the timings in frames, convert a CSS cubic-bezier to After Effects, copy this ease to every layer, or judge whether the motion is finished."
license: MIT
---

# After Effects keyframe animation

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means every move is planned in frames, every ease is a number that was measured,
and the motion is judged from sampled values and one contact sheet before anyone calls it finished.
The stance: timing first (key times), spacing second (eases), structure third (nulls, offsets), then
proof. If a sibling skill named here is missing from your available skills, load it with `skill_get`
(Scenario MCP) or ask the user to install it (https://github.com/scenario-labs/skills#install);
unattended, proceed from tool schemas and flag the gap.

**REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit, version
traps).

## Stance (the expert delta)

1. **Easy Ease is the starting point, never the result.** Every educator in the sources says so
   (Jake Bartlett 7pOCtlrrE3Y 00:04:21, Joey Korenman AG19fyRcOkA 00:27:27, Ben Marriott UVDpgP7sRbw
   00:04:02). Measured: Easy Ease on a 20-frame move peaks at frame 10 and settles on frame 19; it
   is symmetric and slow to leave. Entrances want a fast start and a long settle (`out_expo` settles
   on frame 13 of 20).
2. **Elements that appear ease hard into rest and little out of the first key** (7pOCtlrrE3Y
   00:20:19). In numbers: out influence 10 to 20 %, in influence 80 to 90 %, or a cubic-bezier such
   as (0.16, 1, 0.3, 1).
3. **Overshoot lives where the curve can go past the target.** Measured on 27.0: a back ease on
   combined Position does NOT overshoot (0 %), the path clamps at the key. The same ease on a
   separated X, on Scale or on Rotation overshoots 9.7 %. On combined Position, overshoot with a
   third key.
4. **Decide Separate Dimensions before easing.** Measured: separating Position resets every key to
   linear, and recombining resets them again (Jake Bartlett 7pOCtlrrE3Y 00:14:15 saw the second
   half).
5. **One curve, copied, makes one event** (Joey Korenman AG19fyRcOkA 00:29:47; Ben Marriott
   UVDpgP7sRbw 00:04:54). Animate the simplest element, then copy its ease (`copyEase`, the scripted
   form of pulling one handle on similar keys across layers, 7pOCtlrrE3Y 00:19:47) and offset list
   items 2 to 3 frames (Bricks PdHYC0gqIPA 00:10:44).
6. **Overlap is what reads as weight.** Secondary properties land 3 to 6 frames after the main one,
   and the next element starts before the previous one has settled (PdHYC0gqIPA 00:05:30). [added:
   the product card of procedure 2 lands rotation 4 frames after position and starts the first chip
   3 frames after the phone peaks.]
7. **Gravity never slows before impact** (Cameron, MotionXP HpVtzOtaHlg 00:03:26). Measured: a
   linear contact key after an eased apex makes the ball slow down before the ground (51 px per
   frame on the last frame against a 69 px peak). Contact keys need broken Bezier handles at full
   speed.
8. **Motion blur is two switches and a shutter,** never a keyed Directional Blur (Alan, -ZJKoNj4WpQ
   00:01:38). Measured: smear length is speed (px per frame) times angle / 360; phase -angle/2
   centers it.

## Establish first

| Input                         | Why it changes the plan                                                                               | Default                                                            |
| ----------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Deliverable, platform, aspect | hook timing, hold length, safe area                                                                   | social 1080x1350 or 1080x1920                                      |
| Frame rate                    | every number here is in frames                                                                        | 30 fps (multiply frame counts by 0.8 for 24 fps)                   |
| Duration and beats            | entrance, hold, exit frame budget                                                                     | entrance 15 to 30 frames, hold 1.5 s or more, exit 15 to 20 frames |
| Who edits it later            | keys (editable) versus expressions (rig)                                                              | keys for approved shots                                            |
| Renderer                      | a comp made by script is on Classic 3D; Advanced 3D refuses the layer blur switch (see Version notes) | keep 2D layers 2D                                                  |
| Plugins                       | ease panels (EaseCopy, Flow) change how eases are copied, not what they are                           | scripted eases (this skill), no plugin assumed                     |
| Channel                       | bridge for scripted builds, handoff for a person                                                      | bridge                                                             |

## Procedure

Load the helpers with `ae.py run job.jsx --lib <this skill>/scripts/animation.jsx` (namespace
`AEX.animation`). Code for every stage is in [references/procedures.md](references/procedures.md).
In a person's session, work inside `--undo` and never call `app.open()` while the project has
unsaved changes: the native Save panel blocks every later script.

1. **Block the timing in frames.** Write a beat table: element, property, start frame, end frame,
   from, to, ease name. Key the poses as Hold keys first and ease only once the timing reads (Jess
   Riley 0N0NHlvMEWs 00:06:06); revisit the eases when every element moves (Ben Marriott UVDpgP7sRbw
   00:04:16). GATE: every element has a start frame; no two elements share one unless they are one
   object.
2. **Build the hierarchy.** One master null for anything that exits together; one null per camera
   move in a chain (PdHYC0gqIPA 00:05:30). Set the null's anchor and position so parent space is
   known, then parent with `child.parent = null` (keeps the layer on screen). GATE:
   `AEX.animation.compPoint(child, t)` returns the intended comp position.
3. **Key and ease each move** with `AEX.animation.move(prop, comp, f0, v0, f1, v1, ease)` where
   `ease` is a name from the table in Numbers, a cubic-bezier tuple, or `{out, in}` influences. Use
   `overshoot()` for landings that must pass the target on combined Position, `bounce()` for
   gravity. GATE: `AEK.motion.sample` gives the expected peak frame, overshoot % and settle frame.
4. **Add overlap and offsets.** Secondary properties (rotation, scale squash, child text) land 3 to
   6 frames later. Stagger lists with `stagger(layers, comp, frames, "keys")` (keeps in-points) or
   `"layer"` (moves in-points). Make a layer appear, swap or vanish inside the fastest frames of a
   move (UVDpgP7sRbw 00:06:27). Parenting passes no Opacity: a label parented to a fading chip pops
   at full opacity, so drive its Opacity from the parent or precompose the pair. GATE: the motion
   check reports no `lockstep`; every child of a fading parent reads the parent's opacity.
5. **Hold, then exit as one.** The hold starts on the last key frame of every entrance property,
   never on the settle of one property. Anticipate 3 to 6 frames on the master null, then accelerate
   (`in_cubic`) so it is still fast on the last visible frame. GATE: exit peak frame equals the last
   key frame.
6. **Motion blur.** `comp.motionBlur = true`, `layer.motionBlur = true` on moving layers,
   `shutterAngle` 180, `shutterPhase` -90. Shape layers and Classic 3D layers blur with Samples Per
   Frame (16 in a comp made by script); 2D layer motion uses the Adaptive Sample Limit (-ZJKoNj4WpQ
   00:05:30). GATE: the fastest frame shows a centered smear about `speed * 0.5` px long, without
   stepped copies.
7. **Check and judge.** Run [scripts/motion_report.jsx](scripts/motion_report.jsx) (numbers and
   findings), then capture consecutive frames around entrance, settle and exit and read ONE contact
   sheet; use [references/critique.md](references/critique.md). GATE: no unexplained finding, every
   row of the critique passes.

## Numbers

Measured on 27.0: a 1000 px move over 20 frames at 30 fps. Progress is percent of the travel; peak
is px per frame at the frame shown; settle is the first frame within 1 % of the end.

| Ease             | cubic-bezier or influence | Progress f5 / f10 / f15 | Peak (frame) | Settle           |
| ---------------- | ------------------------- | ----------------------- | ------------ | ---------------- |
| Linear           | 0, 0, 1, 1                | 25 / 50 / 75            | 50 (all)     | 20               |
| Easy Ease (F9)   | 33.33 / 33.33, speed 0    | 15.6 / 50 / 84.4        | 75 (10)      | 19               |
| UI flick         | 80 / 80, speed 0          | 4.8 / 50 / 95.2         | 206 (10)     | 18               |
| Appear-on        | out 15, in 85             | 52.4 / 83.9 / 96.7      | 138 (3)      | 18               |
| out_cubic        | 0.33, 1, 0.68, 1          | 57.7 / 87.2 / 98.3      | 144 (1)      | 16               |
| out_quint        | 0.22, 1, 0.36, 1          | 76.5 / 96.1 / 99.7      | 215 (1)      | 14               |
| out_expo         | 0.16, 1, 0.3, 1           | 82.6 / 97.2 / 99.8      | 281 (1)      | 13               |
| in_out_cubic     | 0.65, 0, 0.35, 1          | 7.1 / 50 / 92.9         | 137 (10)     | 18               |
| in_cubic (exits) | 0.32, 0, 0.67, 0          | 1.7 / 12.8 / 42.3       | 144 (20)     | arrives at speed |
| out_back         | 0.34, 1.56, 0.64, 1       | 1D: overshoot 9.7 %     | 216 (1)      | 19               |

| Rule                     | Value                                                                                     | Relative to                 |
| ------------------------ | ----------------------------------------------------------------------------------------- | --------------------------- |
| Overshoot, product or UI | 3 to 10 % of travel, one crossing back                                                    | travel distance             |
| Pop scale overshoot      | about 110 % before 100 (Josh Noel lTJxtwMrWyE 00:06:23)                                   | final scale                 |
| Impact overshoot key     | about 3 frames after the hit (HpVtzOtaHlg 00:02:20)                                       | 30 fps                      |
| Stagger, list items      | 2 to 3 frames (PdHYC0gqIPA 00:10:44)                                                      | 30 fps                      |
| Secondary lag            | 3 to 6 frames                                                                             | the main property's landing |
| Bounce                   | half the height and half the time per rebound (AG19fyRcOkA 00:16:59), 16-frame first fall | 24 fps                      |
| Elastic                  | first peak 120, keys 6 frames apart, decaying (HpVtzOtaHlg 00:07:32)                      | 30 fps                      |
| Flick ease               | 80 % influence both sides (Cameron Perry wNFHUvtogOE 00:05:01)                            | key influence               |
| Shutter                  | 180 degrees, phase -90; blur length = px per frame x angle / 360                          | frame rate                  |
| Hold                     | 1.5 s or more, counted from the last entrance key                                         | comp time                   |

## Quality gates

- **Measurable:** `motion_report.jsx` returns no finding you cannot justify (`linear`, `lockstep`,
  `drift`, `pop`, `default-ease`). Per move: peak frame, overshoot %, settle frame in the ranges
  above. Expressions: `expressionError` empty. Blur: comp and layer switches true, angle and phase
  as planned.
- **Visual:** one contact sheet of consecutive frames (entrance every 3 frames, settle every frame,
  exit every 3 frames). Spacing shrinks smoothly into rest; the next element moves before the
  previous one has settled; blur smears along travel, centered; nothing pops on between two frames;
  the exit keeps the layout. Optional onion skin (Echo on a precomp) for spacing in one image.

## Common mistakes

| Mistake                                               | Symptom                                                        | Fix                                                                                                                                                           |
| ----------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F9 on every key                                       | "plain", floaty, everything feels the same                     | shape eases from the Numbers table; `copyEase` from one reference                                                                                             |
| Back ease on combined Position                        | no overshoot at all (measured 0 %)                             | separate dimensions before easing, or a third key with `overshoot()`                                                                                          |
| Separating or recombining after easing                | every key turns linear                                         | separate first, ease after; re-ease after recombining                                                                                                         |
| Handles pulled through two equal keys                 | the held pose drifts (measured 54 px)                          | Hold out of the first key, or zero spatial tangents; linear temporal does not fix it. By hand: Default Spatial Interpolation to Linear (xUmMHgZ9YfI 00:04:33) |
| Linear contact keys on a bounce                       | ball slows before the ground                                   | broken Bezier contacts at speed 2h/d, `bounce()`                                                                                                              |
| Everything starts on one frame                        | robotic, lockstep                                              | stagger list items 2 to 3 frames; vary when the group is organic                                                                                              |
| Label parented to a chip that fades                   | the label shows at full opacity on the chip's first frames     | label Opacity `value * thisLayer.parent.transform.opacity / 100`, or precompose chip and label                                                                |
| Stagger by `startTime` on layers that must show early | layers vanish before their in-point                            | stagger by keys (`"keys"` mode)                                                                                                                               |
| Exit eased to a stop off screen                       | wasted frames, a sluggish end                                  | `in_cubic`, last key outside the frame                                                                                                                        |
| Motion blur switch on the comp only                   | no blur                                                        | layer switches too; nulls need none                                                                                                                           |
| Keyed Directional Blur                                | blur in the wrong direction on arcs                            | real motion blur                                                                                                                                              |
| Spring expression on a product                        | 10 crossings, jelly                                            | keyed overshoot (2 crossings) or decay 8 or more                                                                                                              |
| Scale on stroked shapes, or inside a scaled parent    | strokes thin out (measured half width at 50 %) and vanish at 0 | animate Size on the shape (UVDpgP7sRbw 00:03:44), or keep the parent at 100 %                                                                                 |

## Handoffs

- Receives: a built comp and layer structure from scenario-after-effects-project; vector layers from
  scenario-after-effects-shape-layers; text layers and animators from
  scenario-after-effects-typography; generated stills, cutouts and clips land through
  scenario-after-effects-generation (alpha, frame rate and size are fixed there, before keys go on).
- Delivers: keyed comps with a motion report and a contact sheet to
  scenario-after-effects-motion-production for creative review; rigs that need controllers or loops
  to scenario-after-effects-expressions; character walk and IK work to
  scenario-after-effects-character-rigging; real camera moves with depth of field to
  scenario-after-effects-3d; renders to scenario-after-effects-color-delivery.

## Version notes

- `nextKey()` and `previousKey()` in expressions: 26.0 and later, JavaScript engine only.
- `keyLabel` and `setLabelAtKey`: 22.6 and later.
- Copying keys across layers and reverse paste: 24.4 and later; earlier, use Time-Reverse Keyframes
  and re-ease.
- Motion blur on 3D layers: Classic 3D (`comp.renderer` `ADBE Advanced 3d`, the start value of a
  comp made by script) takes the layer switch and renders the same smear as 2D (measured on 27.0).
  Advanced 3D (`ADBE Calder`) and Cinema 4D (`ADBE Ernst`) throw on `layer.motionBlur = true` for a
  3D layer: wrap it in try, read it back, and blur a precomp instead (scenario-after-effects-3d).
- New comps made by script: Motion Blur off, shutter 180, phase 0, 16 samples, adaptive limit 128
  (measured). Set phase -90 explicitly.

## References

- [references/procedures.md](references/procedures.md): every job with its channel, checked line and
  what to check.
- [references/critique.md](references/critique.md): the self-review rubric with thresholds and what
  to look for on a contact sheet.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with video ids and
  timestamps.
- [references/gui-paths.md](references/gui-paths.md): menus, shortcuts and the scripted substitute
  for each.
- [references/sources.md](references/sources.md): every source with URL and best timestamps.
- [scripts/animation.jsx](scripts/animation.jsx) (`AEX.animation`) and `scripts/motion_report.jsx`.
