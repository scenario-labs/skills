# Expert notes

Principles and judgment by source, with timestamps. [added] marks a rule from the live tests or the
skill author, not from the expert.

## Jake Bartlett: designing characters for rigging (zbrO6GrxtQg)

- Decide the rig's job before drawing: several poses, waist-up, or only a walk cycle. "A simpler rig
  isn't going to need as much detail in all of the joints and extra layers" (00:01:05).
- Pick the style first: rubber hose or rigid, stretch or not. Rigid and no stretch means no Puppet
  tool (00:02:10).
- Design large: a 6000 x 6000 px artboard treated as the comp, so limbs can swing out and a crop to
  the chest stays sharp. Continuously rasterized vector scaled up "is going to break your rig"
  (00:08:29).
- Perfect circles at hips, knees, ankles, shoulders, elbows and wrists, centered on the limb,
  checked in Outline view; rotate the lower piece about the circle and look for a seam (00:17:27,
  00:18:01).
- Upper and lower segments of equal length is a fair default; limbs share thickness and axis so they
  swap easily (00:15:04, 00:20:44).
- Name sides from the character's point of view (00:16:22). Copy one of each joint circle to a top
  "joint markers" layer to align bones (00:24:47).
- His walk is precomposed at 12 fps for a stylized rigid look (00:26:55).

## Jake Bartlett: Duik Angela jumpstart (Y0RRBVnn2MA)

- Art prep comes first: separate, named layers, hidden areas extended, round joints (00:00:44 to
  00:06:34). Draw a slight bend into limbs so IK picks the right side by default (00:06:08).
- Anchors to joints before bones; snap with shapes from the Guides layer (00:16:21).
- Ctrl or Cmd click on a creation button parents the selection when it was selected root to tip
  (00:18:31).
- After Auto-rig, Add Zero on every controller not at zero so Position 0,0 is the rest pose
  (00:29:38). Hide bones, lock and shy everything but controllers (00:27:41, 00:30:43).
- Move the character only with the Body controller (00:33:38).
- Walk / Run: the cycle length is in Computation; the work area out is frames minus one; changing
  the stride changes the length, read it again (00:40:27 to 00:46:48).
- Knee pop: lower the Body controller and push it forward, about 86 px forward and 20 px down in his
  example (00:47:07).
- Walk to run: key the Walk and Run weights over about 1 s, then step amplitude, frequency, feet
  rotation and body pose (00:51:46).
- Native fallback [added, measured]: a parent chain with `AEX.rig.ik` on the legs, FK arms, keys on
  controllers. The Duik Body controller maps to `CTRL_BODY`; Add Zero maps to controllers parented
  under `CTRL_ROOT` with rest values at 0.

## Ben Marriott: subtle character animation (t6BXA3_TCH4)

- Block with hold keys on two layers that carry the story (body rotation, arm), solve timing there,
  ease later (00:01:38 to 00:02:43). "Spending the time to get your timing right in the blocking is
  gonna save you a ton of time later."
- Anticipation is a small bump in the curve opposite the move (00:03:24).
- 24 fps looked "too smooth and digital": Posterize Time 12 fps on an adjustment layer (00:03:55).
- Secondary motion reacts to the main motion: hair after the head, legs countering for balance
  (00:04:49).
- Boil made in After Effects, not Illustrator: Turbulent Displace Size 3, Amount 12, seed expression
  `time*4` (00:06:54).
- Send the blocking to the client: a finished idea the illustrator did not want cost him a morning
  (00:07:36).
- Retime a selection of keys by Alt-dragging the outer key so easing stays proportional (00:09:45).

## Evan Abrams: walk cycles (1DiKTiOmrHE)

- Richard Williams order: contact, down, passing, up. Counts are "descriptive, not prescriptive"
  (00:03:44).
- 24 fps, 16 frames contact to contact, passing 8 frames after contact (00:06:07).
- Legs first, then the body (00:04:53). Hips: delete contact and passing keys, keep highs and lows,
  ease them: "the fewer keyframes we have, the smoother" (00:07:32).
- Hips forward reads purposeful (00:08:12). Shoulders twist against the hips; arm swing widest on
  the down pose (00:09:08).
- In place to travel: markers at two left contacts, Time Remap keyed at the markers with
  `loopOut("cycle")`, then Position keyed at two contacts against a guide at the planted heel with
  `loopOut("continue")` (00:10:37, 00:11:10).
- Measured trap [added]: keys only on highs and lows start after frame 0; `loopOut()` then holds the
  first frames. Use `loopIn` before the first key.
- Measured trap [added]: his Time Remap keyed at the two markers with `loopOut("cycle")` rendered
  the first seam frame blank on 27.0; `framesToTime(timeToFrames(time) % N)` on Time Remap renders
  every seam.

## School of Motion: walk cycle with the Jenny LeClue rig (doc)

- 24 frames at 24 fps, keys at 0, 6, 12, 24; the loop duplicates frame 0, so play 23 frames.
- Feet X linear so the layer speed can match; foot Y eases out of the ground, hangs at the top and
  falls without ease in: "walking is controlled falling".
- Center of gravity down at contact, up at mid-step; its rotation leads the vertical by one frame
  ("only one frame preceding the walk"), a 2D stand-in for the weight shift.
- Arms FK, upper, lower and hand each delayed 1 to 2 frames; never two keys on the same frame down a
  chain.
- Change the amount of a motion without changing its timing by scaling the keys in the Graph
  Editor's transform box.
- A stop is a separate one-step timeline swapped in.

## Jordan Bertone, SonduckFilm: Puppet pins (Fqls8BOZ-u0)

- One flat layer with pins is "easier and more flexible", the result "isn't quite as good" as
  separate parts (00:00:23).
- Record a pin with Ctrl or Cmd drag, raise Smoothing, loop with `loopOut("pingpong")` (00:00:55,
  00:01:28).
- Overlap pin for an arm in front of the body (00:01:54); Starch pin just under the elbow so it does
  not warp (00:02:26); Advanced pin in the palm moves, rotates and scales and does not record
  (00:02:56).
- Measured [added]: a script adds a Mesh and pins but cannot place them on the mesh; placement stays
  GUI work.

## Ihor, Motion Design School: lip sync (wUXO8FpzOPc)

- 12 mouth shapes from a common chart is enough for motion design (00:00:24).
- Mouth comp: one shape per second, stacked end to end; Time Remap on the precomp driven by a slider
  named MOUTH, so the slider value is the shape index (00:01:25, 00:02:28).
- A background shape inside the mouth comp hides the default mouth (00:01:56).
- "Each stage should be shown at least for two or three frames so the viewer will be able to read
  it" (00:03:16).
- Measured [added]: amplitude from ffmpeg to 3 shapes with a 2-frame minimum hold gives 24 keys for
  a 3.9 s line.

## Anthony Possobon: hair rig (oiEjz_-8wfk) and Liquify head turn (EP8OaGisJr0)

- Hair: one sine wave with a per-strand offset and a per-bone delay, master sliders for frequency,
  amplitude and offset (00:01:34, 00:10:19).
- Gust: frequency keys first, amplitude keys slid later; amplitude 0.3 base, 0.8 at the peak, 1.0
  was too much (00:28:16, 00:30:24).
- Extend strands toward the root in the art so rotation never reveals a gap (00:20:13).
- Head turn: Liquify distortion percentage animated 0 to 100 by a controller null of 100 px so its
  position reads as a percent; followers use multipliers near 0.3 (EP8OaGisJr0 00:03:18, 00:15:14,
  00:18:32). The sculpting itself is GUI work.

## Plugin routes and the native fallback that was run

| Tool                 | What it adds (from its docs or the notes)                                                                                                                                                              | Native fallback run on 27.0                                                                               |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| Duik Angela          | bones, Link Art, Auto-rig with IK, foot roll, IK/FK switch, procedural Walk / Run (any rig, FK arms, cycle duration in Computation), Swink, Wiggle, X-Sheet (duik guide)                               | `AEX.rig.ik` legs, FK arms, `AEX.rig.walk` keys, loop expressions, Posterize Time for X-Sheet style holds |
| Rubberhose 3         | hose limbs with bend and auto-flop for foreshortening, RubberRig from a 3-layer parent chain, RubberPin on raster layers only; Legacy Puppet engine with resolution raised preferred (Rubberhose docs) | rigid capsule limbs with IK and Stretch; a bendy hose look needs a shape path, not covered here           |
| Limber               | IK limbs for shape layers, ankle controllers free with foot shapes parented to them (Evan Abrams 00:01:36)                                                                                             | foot under `CTRL_FOOT` with `orientTo`, IK expressions                                                    |
| Joysticks 'n Sliders | a pose controller for faces and heads; no saved doc covers it                                                                                                                                          | joystick null clamped to a 200 x 200 box driving `linear()` offsets and a head tilt                       |
| Puppet (built in)    | mesh deformation, Deform, Overlap, Starch, Advanced and Bend pins (Adobe doc)                                                                                                                          | mesh and pins by script do not bind; place by hand, then key and loop by script                           |
