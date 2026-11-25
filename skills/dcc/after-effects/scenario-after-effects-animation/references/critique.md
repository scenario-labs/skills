# Critique rubric: judge the motion before calling it finished

Run the numbers first (`scripts/motion_report.jsx`), then look at ONE contact sheet of consecutive
frames. Every threshold says what it is relative to. Frame counts assume 30 fps unless stated; scale
them with the frame rate (24 fps: multiply by 0.8).

## 1. Numbers (from motion_report.jsx or AEK.motion.sample)

| Check                                                    | Pass                                                                                             | Fail means                                                  |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------- |
| Motion check findings                                    | none, or each one justified in the plan                                                          | linear moves, lockstep starts, drift, speed pops            |
| Share of keys at Easy Ease (33.33 % both sides, speed 0) | under 60 % of keys                                                                               | the scene looks "plain", default curves everywhere          |
| Linear segments                                          | only on opacity fades, mechanical moves, or a deliberate constant-speed path                     | hard starts and stops                                       |
| Entrance peak frame                                      | in the first 30 % of the move for a slide-in (out_expo peaks on frame 1 of 20)                   | the element creeps in, then rushes the landing              |
| Entrance settle (within 1 % of travel)                   | 60 to 85 % of the move's frames (out_expo 13 of 20, out_quint 14 of 20)                          | it either stops dead or drifts on                           |
| Overshoot on a pop or landing                            | 3 to 10 % of the travel; one clear overshoot, at most one small return                           | flat landing (0 %) or wobble (several crossings)            |
| Overshoot crossings of the target                        | 2 (one out, one back) for product and UI                                                         | 4 or more crossings read as jelly                           |
| Spring expression crossings                              | measured 10 for a 6 % amplitude, 2.5 Hz, decay 6: tune decay up for product work                 | elastic on everything                                       |
| Stagger between list items                               | 2 to 3 frames (PdHYC0gqIPA 00:10:44); up to 4 when the items are large or few                    | lockstep (0) or a slow trickle (over 8)                     |
| Hold start                                               | on or after the last key frame of every entrance property                                        | the "hold" still has a layer moving                         |
| Children of a fading parent                              | Opacity driven from the parent, or the group precomposed                                         | a label pops at full opacity while its chip fades in        |
| Speed graph of an appear-on move                         | one tall spike near the first key that falls to 0 at the rest key (7pOCtlrrE3Y 00:20:19)         | a centered bell: the default ease                           |
| Secondary property lag                                   | rotation or follow-through settles 3 to 6 frames after the main property                         | everything stops on one frame, stiff                        |
| Exit                                                     | anticipation 3 to 6 frames, then acceleration that is still fast on the last visible frame       | an exit that eases to a stop off screen wastes frames       |
| Hold length                                              | at least 1.5 s of fully settled frames for a read (social card: chips readable for 2 s or more)  | the viewer cannot read the content                          |
| Bounce contacts                                          | speed on the last frame before contact is the segment maximum                                    | a hump: the ball slows before hitting the ground            |
| Drift between equal keys                                 | 0 px                                                                                             | the held pose moves                                         |
| Motion blur                                              | comp switch on, layer switches on moving layers, angle 180, phase -90 (or a stated style choice) | no blur on fast moves, or blur leading the object (phase 0) |
| First frame                                              | something on screen by frame 3 for social feeds                                                  | an empty first frame loses the scroll                       |

## 2. Frames (one contact sheet)

Capture consecutive frames around the decisive moments: frames 0 to 30 every 3 frames for the
entrance, every frame around a settle, and every 3 frames through the exit. Make one sheet with
`ae.py sheet`. Read it once.

Look for:

- **Spacing.** Gaps between positions of the same element shrink smoothly into rest. Equal gaps mean
  linear; one huge gap then tiny ones means a jump.
- **Overlap.** At the frame the main element lands, the next element is already moving. At least one
  secondary motion is still settling.
- **Arcs.** Organic moves trace a curve; UI and mechanical moves trace a line. A loop or a kink at a
  held key is drift.
- **Weight.** The heavier element moves less and settles later. A large card should not bounce like
  a small chip.
- **Blur.** Smear along the direction of travel, centered on the object, length proportional to
  speed (measured: px per frame times angle / 360). No smear at all on the fastest frame means a
  switch is off.
- **Pops.** No element appears at full size or full opacity between two frames unless it is a
  deliberate cut.
- **Hidden changes.** A layer that appears, swaps or vanishes does it inside the fastest frames of a
  move, where the eye cannot follow (UVDpgP7sRbw 00:06:27).
- **Readability during motion.** Text is legible on the first settled frame, not three frames later.
- **The exit leaves as one.** All parts keep their layout while leaving (shared parent), unless
  follow-through is planned.

## 3. Onion skin (optional, one image)

Precompose the moving layer, put Echo on the precomp layer (Echo Time -2 frames, 20 or more echoes,
decay 0.97; the expert rig uses 30 echoes, decay 0.95 and Composite In Front, 7pOCtlrrE3Y 00:03:28)
and save one late frame. Spacing reads at a glance: dense near rest, sparse at speed, symmetric arcs
on a bounce.

## 4. Verdict format

Report: the numbers table (per moving element: keys, peak frame, overshoot %, settle frame), the
findings and what was changed, the contact sheet path, and one sentence on how it reads. Fix and
re-run before reporting when a "Fail" row applies.
