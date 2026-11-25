---
name: scenario-after-effects-character-rigging
description: "Use when rigging or animating a 2D cut-out character in After Effects: preparing layered character art, anchor points at joints, parenting, IK for arms and legs, controllers, walk cycles and run cycles, waves and gestures, overlap and follow-through, hair or cloth delay, Puppet pins, mouth shapes and lip sync from a voice file, blinks, a face joystick, or the hand-drawn look on twos. Triggers: rig my character, the arm rotates around the wrong point, the joint shows a gap, the elbow bends the wrong way, the knee pops, the foot slides, the walk loop jumps, make it walk across the screen, lip sync to this audio, make him blink, Duik, Rubberhose, Limber, Puppet tool, the character moves like a robot."
license: MIT
---

# After Effects Character Rigging

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means a rig an animator can pose with a few controllers, built from art that was
split for motion, and motion proven with numbers: the planted foot does not slide, the loop has no
seam, the wrist lands on its controller. An agent builds the rig, the cycles and the lip-sync keys
by script and measures them. The acting and appeal are judged by a person at full frame rate. If a
sibling skill named here is missing from your available skills, load it with `skill_get` (Scenario
MCP) or ask the user to install it (https://github.com/scenario-labs/skills#install); unattended,
proceed from tool schemas and flag the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert
(channels, review loop, toolkit, version traps).

## Stance (the expert delta)

- The art decides the rig. One layer per moving segment, with "perfectly circular joints so that you
  can rotate joints around without having any kind of seam" (Jake Bartlett, zbrO6GrxtQg 00:21:48).
  Decide first what the rig is for: walk only, full body, waist up (00:01:05).
- Pivots before parents. Put each anchor on its joint with rotations at 0, then parent root to tip
  (Jake Bartlett, Y0RRBVnn2MA 00:16:21, 00:18:31). Measured: a pivot moved by script left the art 0
  px from where it was.
- IK on legs, FK on arms. Planted feet need IK; arm swings want FK arcs. Duik's procedural walk
  turns arm IK off for that reason (Duik Angela guide, Walk and Run).
- Block in poses with hold keys, on the layers that carry the story, then ease. Send the blocking to
  the client before polishing (Ben Marriott, t6BXA3_TCH4 00:01:38, 00:07:36).
- Fewer keys, smoother curves: hips keyed only on their highs and lows (Evan Abrams, 1DiKTiOmrHE
  00:07:32). Measured trap: then the first key is not on frame 0 and `loopOut()` alone holds frames
  0 to 2, a 14 px pop at the loop. Loop before the first key too.
- Feet X stays linear so the planted foot slides back at exactly the travel speed (School of Motion
  walk cycle). Measured: 0.000 px of foot slide over two cycles with a separated X dimension.
- Lip sync shows the main shapes, each held 2 to 3 frames: "there is no need to animate each letter"
  (Ihor, wUXO8FpzOPc 00:03:16). Amplitude gives open and closed; B, M, P and F, V need a person or
  an aligner [added].
- Puppet pin placement is GUI work. Measured: a script can add a Mesh, Deform and Overlap pins, but
  those pins carry Vertex Index -1 and deform nothing.

## Establish first

- **Rig purpose and view:** side, three-quarter or front; walk only or full acting; stretchy (hose)
  or rigid.
- **Art:** layered PSD or AI, one layer per segment, names R and L from the character's point of
  view, art drawn large (Jake Bartlett draws on a 6000 px artboard, zbrO6GrxtQg 00:08:29). Generated
  art arrives through scenario-after-effects-generation: ask for limb-separated layers with round
  joint overlaps.
- **Frame rate and look:** 24 fps cycles are the default in every source; on twos means Posterize
  Time 12 fps.
- **Cycle or shot:** a looping cycle (game, social loop) or a walk across a shot that stops.
- **Tools installed:** `app.effects` and the ScriptUI panels list. Duik, Rubberhose, Limber and
  Joysticks 'n Sliders are panels with no documented outside API: an agent builds the native rig
  below and names the plugin route for a person.
- **Audio:** the voice file, its frame rate target and language.

## Procedure

Helpers: [scripts/rig.jsx](scripts/rig.jsx) (`AEX.rig`, load with `--lib`) and
[scripts/audio_to_mouth.py](scripts/audio_to_mouth.py). Full jobs in
[references/procedures.md](references/procedures.md).

1. **Audit the art.** Import as a composition with layer sizes. List layers, check names, one layer
   per segment, and joint overlap. Hidden areas (torso under the arm, thigh tops) are painted in
   (Jake Bartlett, Y0RRBVnn2MA 00:00:44). GATE: every limb segment is its own layer with a unique
   name; the person confirms any missing segment before rigging. Joint circles are centered on the
   limb in Illustrator Outline view (zbrO6GrxtQg 00:17:27). Ask for a top "joint markers" layer
   copied from those circles: its circle centers are the pivot table for stage 2 (00:24:47).
2. **Pivots and parent chain.** `AEX.rig.pivot(layer, [x, y])` moves an anchor onto a comp point
   (unparented, before parenting); `AEK.build.anchor` does the same from fractions of the bounds.
   Shape-layer limbs from `AEX.rig.limb` are drawn with the pivot at [0, 0]. Then
   `AEX.rig.chain([root, ..., tip])`. Hierarchy: `CTRL_ROOT > CTRL_BODY > torso > head`; arms under
   the torso; legs under `CTRL_BODY`; foot controllers under `CTRL_ROOT`, never under the hips.
   GATE: `AEX.rig.world()` of every joint is unchanged after parenting; a posed wrist matches the
   hand-computed point (measured error 3e-14 px).
3. **Controllers and IK.** `AEX.rig.ik({upper, lower, tip, ctrl})` writes law-of-cosines expressions
   with a Flip checkbox (bend side) and a Stretch checkbox. `AEX.rig.orientTo(foot, ctrl)` keeps the
   foot at its controller's angle. Then zero and clean (Jake Bartlett, Y0RRBVnn2MA 00:29:38 to
   00:31:30): each controller under a `ZERO_` null at its rest position, so Position 0,0 is the rest
   pose; art, bones and zero nulls locked and shy, only `CTRL_` layers visible (procedures 2b). Lock
   guards against mouse edits only: a script still writes to locked layers (measured). GATE: a grid
   of 80 controller positions; inside the reach ring the wrist error is 0.0000 px, outside it the
   limb points at the target (0 degree error), Flip swaps the elbow side. Knees must bend forward on
   the first frame. Every controller reads Position [0, 0] at rest.
4. **Block the cycle.** Contact, down, passing, up with `AEX.rig.walk` or `AEX.rig.keys` (frames,
   not seconds), loop expressions by `AEX.rig.loop`: `"out"` when keys start on frame 0, `"both"`
   otherwise. Body rotation keys sit 1 frame before the vertical keys, and shoulders twist against
   the hips (School of Motion walk; Evan Abrams 00:09:08). GATE: planted-foot world X and Y spread 0
   px during each stance. In the in-place cycle comp (no travel), frame 0 and frame N render
   pixel-identical (ImageMagick `compare -metric AE` = 0) and frames N-1 and N differ. With travel
   on, frame N equals frame 0 shifted by the travel per cycle (crop both by that offset, then
   compare). Frame N repeats frame 0: a loop file plays frames 0 to N-1, 23 of 24 (School of Motion
   walk; Duik work area out = N-1, Y0RRBVnn2MA 00:40:27).
5. **Overlap and secondary motion.** `AEX.rig.drag` (child rotation from the driver's change over n
   frames), `AEX.rig.echo` (delayed copy, the head after the hips), a sine with a per-segment delay
   for hair (Anthony Possobon, oiEjz_-8wfk 00:10:19). Gestures such as a wave are key lists relative
   to their start frame. The reference wave spans 48 frames (procedures 5): its last key must land
   on or before the clip's last frame (duration x fps - 1). To fit a shorter window, shorten the
   hold first, then scale the other key frames [added]. GATE: measured lags match the plan (head nod
   peak 2 frames after the hips' low; hair peaks 5, 7, 9, 11 for a 2-frame delay); no key past the
   last frame.
6. **Into the shot.** Walk in place inside a precomp; N = the frames between two contacts of the
   same foot (Evan Abrams marks them, 00:10:37). In the shot, Time Remap by the expression
   `framesToTime(timeToFrames(time) % N)`. Measured: `loopOut("cycle")` on Time Remap keyed 0 to N
   rendered frame N blank. Travel on a separated X with `loopOut("continue")` at stride / step
   frames, or travel `CTRL_ROOT` directly. GATE: frame N of the shot is not blank and equals frame 0
   shifted by the travel; travel speed equals stride / step frames; the planted foot holds against
   the ground.
7. **Face.** Mouth shapes switched by `AEX.rig.swap` (opacity from a slider), or a mouth precomp
   with one shape per second whose Time Remap reads one Slider, so one slider unit is one shape
   (Ihor, wUXO8FpzOPc 00:01:25, 00:02:28; expression in procedures 6). Mouth keys from
   `audio_to_mouth.py` as hold keys (`AEX.rig.holdKeys`). Blink 3 frames, irregular spacing. A
   joystick null with `linear()` drives look direction. GATE: slider keys integer, minimum gap 2
   frames, mouth closed on silence; blink runs of 3 frames, 1.25 s or more apart with a 2.5 s
   window.
8. **Look.** Posterize Time 12 fps and a boil (Turbulent Displace, seed stepped every 2 frames) on
   adjustment layers (Ben Marriott 00:03:55, 00:06:54). GATE: frame pairs 0 and 1, 2 and 3 render
   identical.
9. **Review.** Contact sheet of the key poses plus the in-between frames; a person watches the loop
   at full rate. Fix by pose, then by timing, then by curve. More or less motion at the same timing:
   scale the key values about their middle (Graph Editor transform box, School of Motion walk), by
   script `AEX.rig.keys` at the same frames. Retime a set of keys by Alt-dragging its outer key so
   eases stay proportional (Ben Marriott 00:09:45).

## Numbers

| Value                                                                          | Relative to                          | Source                                                                                   |
| ------------------------------------------------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------- |
| 24 frames per cycle, 12 per step: contact 0, down 3, passing 6, up 9           | 24 fps                               | School of Motion walk; measured rig                                                      |
| 32 frames per cycle, 16 per step, passing at 8                                 | 24 fps, slower walk                  | Evan Abrams 00:03:44, 00:06:07                                                           |
| foot speed in stance = stride / step frames (200 px / 12 = 16.67 px per frame) | comp pixels                          | measured                                                                                 |
| hips 14 px down at down, 14 px up at up                                        | 262 px leg                           | measured rig                                                                             |
| arm swing about 22 degrees, widest on the down pose                            | FK upper arm                         | Evan Abrams 00:09:08; measured rig                                                       |
| overlap delay 1 to 2 frames per link (shoulder, elbow, hand)                   | 24 fps                               | School of Motion walk                                                                    |
| body rotation 1 frame before the vertical bob                                  | 24 fps                               | School of Motion walk                                                                    |
| wave: anticipation 4, peak 10, settle 14, hold to 40, rest 48                  | frames from the wave's start, 24 fps | measured rig                                                                             |
| mouth shape hold 2 to 3 frames minimum                                         | 24 fps                               | Ihor 00:03:16                                                                            |
| blink closed 3 frames                                                          | 24 fps                               | measured expression [added]                                                              |
| hip-to-ankle distance at contact under the leg length                          | leg length                           | measured: 260 of a 262 px leg reached; past the reach the foot stops short by the excess |
| Posterize Time 12                                                              | 24 fps comp                          | Ben Marriott 00:03:55                                                                    |
| boil: Turbulent Displace Size 3, Amount 12, seed every 2 to 4 frames           | 1280 px art                          | Ben Marriott 00:06:54                                                                    |

## Quality gates

- Measurable: `AEK.expr.check` 0 failed; IK error under 0.01 px inside reach; planted foot spread 0
  px; in the in-place cycle comp frame 0 equals frame N pixel for pixel; key frames at the planned
  frames; mouth key gaps 2 frames or more; no two keys on one frame in a chain.
- Visual: joints show no seam at the largest bend; knees and elbows bend the right way in every
  pose; feet sit on the ground line; the passing pose reads (one leg straight under the hips); arms
  opposite to legs; no limb crossing the face. Read
  [references/critique.md](references/critique.md).

## Common mistakes

| Mistake                                      | Symptom                                       | Fix                                                                                                        |
| -------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| anchor left at the layer center              | limb swings around its middle                 | `AEX.rig.pivot` before parenting                                                                           |
| parented before pivots                       | art jumps when the anchor moves               | unparent, set pivots, parent again                                                                         |
| foot controllers under the hips              | feet bob with the body                        | controllers under `CTRL_ROOT`                                                                              |
| contact distance longer than the leg         | knee straight, foot floats off its controller | raise the hips or shorten the stride                                                                       |
| `loopOut()` with the first key after frame 0 | pop at the loop (14 px measured)              | `AEX.rig.loop(p, "both")`                                                                                  |
| travel on combined Position with `continue`  | 0.57 px drift after two cycles                | separate dimensions, loop X                                                                                |
| removing every Time Remap key                | "property is hidden" error                    | add the cycle-end key, remove the keys after it                                                            |
| Stretch on with a hand under the forearm     | hand stretched with the arm                   | hand under a controller with `orientTo`, or accept                                                         |
| mouth keys from raw amplitude                | flicker every frame                           | min hold 2 frames, 1-frame lead                                                                            |
| Puppet pins added by script                  | pins exist, art does not move                 | place pins in the Layer panel by hand                                                                      |
| one flat layer with pins for a hero shot     | warping at elbows                             | separate layers; flat plus Starch pins only for quick social pieces (Jordan Bertone, Fqls8BOZ-u0 00:00:23) |
| pinned arm crossing the torso                | arm hidden behind the body, elbow warps       | Overlap pin on the arm (00:01:54); Starch pin just under the elbow, beside the bend (00:02:26)             |
| `loopOut("cycle")` on Time Remap             | blank frame at the first seam                 | `framesToTime(timeToFrames(time) % N)`                                                                     |
| loop file rendered with frame N              | hitch: frame 0 plays twice                    | render frames 0 to N-1                                                                                     |

## Handoffs

- Receives: layered character art from scenario-after-effects-generation (generated art is raw
  input: split, extended joints, checked) or from the person; the project and comp settings from
  scenario-after-effects-project.
- Delivers to scenario-after-effects-animation: blocked poses on hold keys and cycles, for easing
  and graph work. To scenario-after-effects-expressions: rig expressions to bake (`AEK.expr.bake`)
  before export. To scenario-after-effects-motion-production: the cycle precomp and its loop length
  in frames.
- Voice and music come through scenario-after-effects-generation; this skill turns the voice file
  into mouth keys.

## Version notes

- Puppet: the Advanced engine is the default since 15.1; projects saved earlier open on Legacy; do
  not switch engines after placing pins (Adobe Puppet tools doc).
- Rubberhose installs as a CEP extension; CEP is on a removal path and UXP is in beta in 27.1. Check
  the extension loads before planning on it.
- Duik Angela replaced Duik Bassel; tutorials naming "structures" are Bassel (Jake Bartlett,
  Y0RRBVnn2MA 00:14:07).
- Convert Audio to Keyframes is menu command 4218 on 27.0 and ran from a job with no dialog.

## References

- [references/procedures.md](references/procedures.md): jobs for each stage, with channel, checked
  line and what to check.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps,
  plugin routes and their native fallbacks.
- [references/critique.md](references/critique.md): the rubric with numbers and what to look for on
  a contact sheet.
- [references/gui-paths.md](references/gui-paths.md): menus, tools and shortcuts for the same
  stages.
- [references/sources.md](references/sources.md): every source with URL.
- Helpers: [scripts/rig.jsx](scripts/rig.jsx),
  [scripts/audio_to_mouth.py](scripts/audio_to_mouth.py).
