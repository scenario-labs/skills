# Critique: judging a rig, a skin, a clip or an export

Use this after every stage. A stage passes only when its numbers pass and its captures have been
looked at. Thresholds marked [added] are this skill's defaults; the source experts judge by eye.

## Arrival (P1)

| Check                      | Pass              | Fail means                                             |
| -------------------------- | ----------------- | ------------------------------------------------------ |
| Height ratio to expected   | 0.95 to 1.05      | Unit mismatch (0.01, 0.394, 2.54, 100): fix at import  |
| Skeleton roots             | 1                 | Stray helper or split skeleton                         |
| Bones with non-unit scale  | 0                 | Scale baked into bones: fix in the source or re-export |
| Duplicate bone names       | 0                 | Rename before any map or transfer                      |
| Frame rate                 | equals the source | Keys land between frames                               |
| Skinned mesh with a parent | 0                 | Unexpected deformation (Skin doc)                      |

Captures (persp, front, left): the skeleton sits inside the mesh, the pose is T or A, no joint
outside the limb.

## Rig and mechanism (P4, P5, P6)

Numbers:

- Rigid link drift under 0.01 system units over the full range [added].
- Piston halves `min_abs_dot` above 0.9999 and `max_offset` under 0.01 system units [added].
- Stroke distance inside the barrel and rod limits at every frame.
- Every slider at min, default and max gives the expected target value within 0.001.
- No LookAt Upnode on World where the parent rotates.

Captures:

- Each driver at both limits, from the Front view (the mechanism plane) and from a perspective.
- The whole assembly twisted out of plane: no part spins (cm7OP3niwvI 00:08:17).
- Every remaining `bbox_overlaps` hit at its listed frames: a visible gap, or contact that is by
  design (a pin in its hole).

## Skin (P7, P8)

Numbers from `skin_report`: `unweighted` 0, `over_limit` 0, `bad_sum` 0, `unused_bones` only nubs
and helpers.

Captures, Edged Faces on, front and side, for each pose:

- Arms up, arms down, arms forward: shoulders keep volume, no folding into the chest.
- Elbows and knees at 120 degrees: the inside crease does not collapse to a line.
- Forearm and neck twisted 90 degrees: no candy-wrapper pinch (DQ if it does).
- Head turned and tilted: skull rigid, base of neck moves with clavicles (Kimn7CIZ5bI 00:07:47).
- Fingers curled: no finger pulls neighbor vertices.
- Transfer (P8): the same three poses on old and new rigs look the same.

## Animation (P2, P3, P12)

Numbers:

- Camera `speed_profile`: `max_step_change_ratio` under 0.05 [added]; height above floor within 2 cm
  of the target eye level.
- Cycle `loop_gap`: position gap under 0.1 cm and `min_axis_dot` above 0.999 [added].
- Cycle on a path: `contact_slide` under 1 cm per phase [added].
- Tangent types as planned: linear where constant speed was asked, Auto on camera rotation keys.

Captures:

- Camera contact sheet every 50 frames: no jump between neighbors, level horizon, no wall or door
  frame filling the view.
- Character on the path: a frame at each foot plant; the planted foot sits at the same spot across
  its phase.

## Face (P9)

- Every phone channel keyed at each key time; neutral keys at phrase start and end.
- Phones Morpher above expressions; no blink key on a phone key frame.
- Mouth captures at each key frame match the planned shape; the upper face moves somewhere in the
  shot.

## Mocap (P10)

Numbers: worst foot slide under 1 cm per contact, contact height jitter under 0.5 cm [added]; hand
contacts present where the reference shows them; clip length equals the reference length.

Captures: side-by-side sheet of the cleaned clip and the reference video at the same frames; a
ground plane in view to show penetration (WUELGPaQu8o 00:16:24).

## Export (P13)

| Check                          | Pass                                                                                |
| ------------------------------ | ----------------------------------------------------------------------------------- |
| Two files                      | skin file in bind pose, one file per clip                                           |
| Re-import bone count and names | equal to the source                                                                 |
| Re-import height               | within 2% of the source                                                             |
| Range and frame rate           | equal to the source                                                                 |
| Bake                           | on whenever constraints, IK, wires, CAT or layers drive the motion                  |
| FBX dialog                     | Convert Deforming Dummies to Bones on, Triangulate off (f_00192)                    |
| Root motion                    | engine test import moves or holds the character as the team asked (no sourced rule) |
| Engine log                     | only Nub or Xtra end bones listed as missing from the bind pose                     |

## Red flags that stop the work

- A gate passed on numbers but no capture was looked at.
- A GUI-only step handed to the user without its menu path from gui-paths.md ("fix by hand" is not
  an instruction).
- A skin or rig edited on the only copy of a delivered file: save `_v002` first.
- A weight or bone count that changed without a planned cause.
- An API name marked `[verify]` that returned nothing or an error: stop and report, do not guess
  another name.
