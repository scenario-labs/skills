# Critique rubric

Judge the rig, then the motion, then the face. Numbers first, then one contact sheet per check. The
person judges acting and appeal at full frame rate.

## Rig (numbers)

| Check                             | Pass                                                                                                                                            | How                                                         |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| names                             | unique, R and L from the character's side, controllers `CTRL_`                                                                                  | layer list                                                  |
| one parent per layer, root to tip | no cycles, feet controllers under the root                                                                                                      | `layer.parent` walk                                         |
| pivots on joints                  | parenting moved the art 0 px; a posed wrist matches the computed point under 0.01 px                                                            | `AEX.rig.world`                                             |
| IK                                | error under 0.01 px inside the reach ring; out of reach the limb points at the target                                                           | grid test (procedures 2)                                    |
| bend side                         | knees forward, elbows back for the view                                                                                                         | frame 0 and an extreme                                      |
| expressions                       | `AEK.expr.check` 0 failed at 10 or more times                                                                                                   | toolkit                                                     |
| controllers at rest               | every `CTRL_` under a `ZERO_` null, Position [0, 0] at rest; art, IK bones and zero nulls locked and shy; FK bones carry keys and stay unlocked | values read, `layer.locked`, `layer.shy`                    |
| proportions                       | limbs about 0.14 of the body width, hands about 1.4 x the arm width, shoulder pivots inside the body edge, arms visible at rest                 | measure the art                                             |
| pose test                         | rest, raised and gesture poses captured before any key; every elbow points away from the body in each                                           | elbow offset from the shoulder-to-hand line (procedures 2c) |
| squash                            | on the body art only; no limb ancestor with Scale X and Y more than 0.5 % apart                                                                 | `AEX.rig.check` `shear` empty, `ok` true                    |
| reach                             | every IK controller inside 0.9 of the reach over the shot                                                                                       | shoulder-to-controller distance per frame                   |
| limits                            | each limited joint has Min and Max controls; a key past the range reads the bound                                                               | `AEX.rig.limit`, value read                                 |

## Rig (contact sheet)

- Rotate each joint to its largest bend: no gap and no corner shows at the joint.
- Overlap order: far limbs behind the torso, near limbs in front; a raised near arm does not cover
  the face in a side view.
- Hand and foot art stays undistorted (Stretch also stretches children).
- Puppet: an arm crossing the torso stays in front (Overlap pin); the elbow does not warp (Starch
  pin beside it) (Fqls8BOZ-u0 00:01:54, 00:02:26).

## Walk and cycles (numbers)

| Check                 | Pass                                                                                                                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| frame rate and length | stated in frames: 24-frame cycle at 24 fps unless briefed                                                                                                                            |
| key frames            | contacts at 0 and N/2, down and up at the planned frames                                                                                                                             |
| planted foot          | world X and Y spread 0 px (under 0.5 px with travel by hand) during stance                                                                                                           |
| travel speed          | stride / step frames, on a separated X                                                                                                                                               |
| loop seam             | in the in-place cycle comp, frame 0 and frame N identical (`magick compare -metric AE` 0) and frame N-1 differs from N; with travel, compare after cropping by the travel per cycle  |
| loop file             | renders frames 0 to N-1 (frame N repeats frame 0)                                                                                                                                    |
| shot seam             | frame N of a Time Remap loop is not blank                                                                                                                                            |
| gestures              | every key on or before the clip's last frame (duration x fps - 1)                                                                                                                    |
| weight                | body rotation 1 frame ahead of the vertical bob; shoulders against the hips                                                                                                          |
| hips                  | keys on highs and lows only, looped before the first key                                                                                                                             |
| overlap               | each link 1 to 2 frames behind its driver; no two links keyed on the same frame                                                                                                      |
| anticipation          | every big gesture starts with a small move the other way (the wave dips 12 degrees over 4 frames) and overshoots before its hold                                                     |
| overlap on a gesture  | upper arm leads, forearm keys follow, hand drags 2 frames; the body leans with the gesture and settles past rest                                                                     |
| foot roll             | the lowest sole corner (heel and toe from `sourceRectAtTime`, through `AEX.rig.world`) never below the ground line; the corner on the ground moves at the travel speed, never faster |
| reach                 | `reachContact` 0.95 to 1.0 and `hipOverAnkle` 0.9 or more; lower reads as a crouched walk                                                                                            |
| stop                  | hip speed falls to 0 without a step up in acceleration; planted heels 0 px from the stop on; legs at 97 % of their length once standing                                              |
| hanging prop          | hangs straight (0 degrees world) at rest; swing under about 20 degrees in a walk; no tilt before the first move                                                                      |
| framing               | `AEX.rig.bounds` height about 60 to 75 % of the frame for a full-body hero shot, no limb cropped on any frame of the move [added]                                                    |

## Walk (contact sheet of frames 0, 3, 6, 9, 12 and the mirror)

- Contact: front heel down, toe up, back foot on its ball, legs at full stride.
- Down: lowest hips, front knee bent, weight on the front foot.
- Passing: support leg straight under the hips, swing foot clears the ground.
- Up: highest hips, back foot pushing off.
- Arms opposite to legs, widest on the down pose. Head bob lags the hips.
- No foot under the ground line, no knee popping straight between two frames.
- After a stop the figure stands with near-straight legs, feet side by side, a hanging prop settled.

## Face and lip sync

| Check      | Pass                                                                                                                                        |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| mouth keys | integer, hold interpolation, minimum gap 2 frames                                                                                           |
| silence    | closed mouth on silent frames and before the first word                                                                                     |
| lead       | mouth opens 1 frame before the sound                                                                                                        |
| blinks     | close over 2 frames, shut 2, open over 2 (`AEX.rig.blink`); irregular spacing, 1.25 s or more apart; none on the first frame of a head turn |
| phonemes   | B, M, P closed and F, V shapes placed by a person or an aligner when the shot is close                                                      |

Contact sheet: the frame of the widest vowel shows the open mouth; a blink frame shows closed eyes;
no default mouth peeks behind a replaced one.

## Look

- On twos: frame pairs identical (0 and 1, 2 and 3).
- Boil: the line wobble matches the illustration's own wobble, not larger (Ben Marriott 00:07:04).

## More mistakes

| Mistake                                                                   | Symptom                                        | Fix                                                                                                        |
| ------------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Stretch on with a hand under the forearm                                  | hand stretched with the arm                    | hand under a controller with `orientTo`, or accept                                                         |
| removing every Time Remap key                                             | "property is hidden" error                     | add the cycle-end key, remove the keys after it                                                            |
| one flat layer with pins for a hero shot                                  | warping at elbows                              | separate layers; flat plus Starch pins only for quick social pieces (Jordan Bertone, Fqls8BOZ-u0 00:00:23) |
| pinned arm crossing the torso                                             | arm hidden behind the body, elbow warps        | Overlap pin on the arm (00:01:54); Starch pin just under the elbow, beside the bend (00:02:26)             |
| travel on combined Position with `continue`                               | 0.57 px drift after two cycles                 | separate dimensions, loop X                                                                                |
| zero null created at the parent-space Position, then parented to the root | controller reads [476.9, 331.2] and moves      | `AEX.rig.zero` (null under the controller's own parent)                                                    |
| figure scaled with a layer above the rig while IK ignores scale           | foot misses its controller by 48.5 px at 150 % | scale `CTRL_ROOT`; the IK reads the parent's world scale                                                   |
| body squashed by scaling the layer the arms hang from                     | arm art sheared; `check` reports `shear`       | squash the body art, `attach` the shoulders (procedures 2c)                                                |
| side-view wave signs used in a front view                                 | elbow points in, hand swings across the face   | mirror the upper arm sign per arm; forearm positive once raised (procedures 5)                             |
| one IK Flip for an arm that reaches up and down                           | elbow swaps to the inside on the raised pose   | pose test first; key Flip between the poses                                                                |

## Version notes

- Puppet: the Advanced engine is the default since 15.1; projects saved earlier open on Legacy; do
  not switch engines after placing pins (Adobe Puppet tools doc).
- Rubberhose installs as a CEP extension; CEP is on a removal path and UXP is in beta in 27.1. Check
  the extension loads before planning on it.
- Duik Angela replaced Duik Bassel; tutorials naming "structures" are Bassel (Jake Bartlett,
  Y0RRBVnn2MA 00:14:07).
- Convert Audio to Keyframes is menu command 4218 on 27.0 and ran from a job with no dialog.

## Report

Fix by pose, then by timing, then by curve. More or less motion at the same timing: scale the key
values about their middle (Graph Editor transform box, School of Motion walk), by script
`AEX.rig.keys` at the same frames. Retime a set of keys by Alt-dragging its outer key so eases stay
proportional (Ben Marriott 00:09:45). A loop file plays frames 0 to N-1, 23 of 24 (School of Motion
walk; Duik work area out = N-1, Y0RRBVnn2MA 00:40:27).

State what was measured, what was left to the person (pin placement, acting, phonemes), the frame
rate and cycle length, and every plugin route not taken.
