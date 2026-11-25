# Expert notes: keyframe animation

Principles and judgment from the sources, by expert, with video id and timestamp. Full URLs are in
[sources.md](sources.md). Lines marked [added] are this skill's own additions or measurements;
measured values come from the live cases in [procedures.md](procedures.md).

## Where the experts agree

- Easy Ease (F9) is a starting point and never the finish. The work is in each key's handles.
  (AG19fyRcOkA 00:27:27; UVDpgP7sRbw 00:04:02; 0N0NHlvMEWs 00:06:06; 7pOCtlrrE3Y 00:04:21;
  6zrEKEuJGKs 00:01:11)
- Timing and spacing are separate knobs. Key times set timing; easing only redistributes the
  in-between frames. (7pOCtlrrE3Y 00:03:15)
- Fewer keys, with the curve doing the work. Two keys per move first; a third key only when two
  cannot make the shape. (AG19fyRcOkA 00:35:35; 6zrEKEuJGKs 00:08:07, 00:08:39)
- Reuse one curve across properties that belong to one event, so they read as one gesture.
  (AG19fyRcOkA 00:29:47; UVDpgP7sRbw 00:04:54)
- Block first with held poses, then ease. (0N0NHlvMEWs 00:05:05)
- Elements that appear ease hard into rest and little out of the first key. (7pOCtlrrE3Y 00:20:19;
  PdHYC0gqIPA 00:03:56; 6zrEKEuJGKs 00:02:55)
- Curves must be smooth: a crease or a hump in the value or speed graph is a flaw when the goal is
  smooth motion. (6zrEKEuJGKs 00:06:33; HpVtzOtaHlg 00:03:26)

## Jake Bartlett (Jake In Motion)

- The Graph Editor is "the single most important tool": identical key times give different motion
  when spacing changes. (7pOCtlrrE3Y 00:04:49)
- Speed graph for motion paths, continuous motion and slide-ins; value graph with separated
  dimensions for bounces, overshoots and anything you reason about in values. (7pOCtlrrE3Y 00:13:43,
  00:15:31)
- The value graph of combined Position is locked; separate dimensions or work in the speed graph.
  Recombining dimensions loses the easing. (7pOCtlrrE3Y 00:06:26, 00:14:15) [added: measured on
  27.0, separating AND recombining both reset every key to linear.]
- Path properties only show the speed graph. (7pOCtlrrE3Y 00:17:26)
- Lift keys off the zero baseline in the speed graph so continuous motion never stops. Peaks near
  3000 px/s, in-between keys near 500 to 600 px/s on screen. (7pOCtlrrE3Y 00:16:26, 00:16:35)
- Select similar keys on several layers in the speed graph and pull one handle: a whole scene
  upgrades at once. (7pOCtlrrE3Y 00:19:47) [added: the scripted equivalent is `copyEase` from one
  shaped reference.]
- Onion skin with Echo to judge spacing like a frame-by-frame animator: 30 echoes, starting
  intensity 1, decay 0.95, operator Composite In Front. (7pOCtlrrE3Y 00:02:42, frame 00:03:28)
  [added: measured recipe, Echo on a precomp of the moving layer, Echo Time -2 frames, 22 echoes.]
- Three tiers: F9 (beginner), Shift-dragged handles with strong ease out of the first key and into
  the second, then a slider offset curve on top. 99 % of the time a third key is enough.
  (6zrEKEuJGKs 00:01:11, 00:02:19, 00:03:49, 00:08:39)
- Drift: two identical Position keys can still move between them when neighboring keys have Bezier
  handles. Fix with a Hold key or linear spatial interpolation. (xUmMHgZ9YfI 00:00:00, 00:00:32,
  00:05:04)
- Set Preferences > General > Default Spatial Interpolation to Linear; add arcs on purpose.
  (xUmMHgZ9YfI 00:04:33) [added: keys created by script already have zero spatial tangents on 27.0,
  so scripted motion does not drift until someone pulls handles.]
- Do not separate dimensions when the motion path matters (camera moves, arcs): separation removes
  the path. (xUmMHgZ9YfI 00:01:04, 00:08:15)

## Joey Korenman (School of Motion)

- Bounce: each rebound is half the height and about half the duration of the last (16-frame fall,
  then 8, 4, 3, 2 at 24 fps); contact keys get no ease in; copy the first bounce's keys so handles
  carry over. (AG19fyRcOkA 00:16:59 to 00:22:33) [added: half time for half height is a cartoon
  rule; real gravity gives 0.71 of the time.]
- Cartoon hang: time-scale all keys with Option-drag, then pull out only the apex handles.
  (AG19fyRcOkA 00:23:06 to 00:24:43)
- Realistic defaults first (half-height bounces, normal anticipation), then break them on purpose.
  (AG19fyRcOkA 00:16:28)
- Impact wave from Trim Paths: End 50 %, Offset 90 degrees, Start to 50 with the same ease, copies 3
  to 4 frames apart. (AG19fyRcOkA 00:28:32 to 00:34:56)

## Ben Marriott

- Animate the simplest element first, then copy its speed and ease to the others. (UVDpgP7sRbw
  00:02:40, 00:04:16)
- Snappy ease: long ease out of the first key, very short ease into the last (cup top, 0 to 400 in
  about 10 frames at 25 fps). (UVDpgP7sRbw 00:04:02)
- Hide changes inside the fastest frames of a move, where the eye cannot follow. (UVDpgP7sRbw
  00:06:27)
- Use Size, not Scale, on stroked shapes: Scale thickens and thins the stroke. (UVDpgP7sRbw
  00:03:44) [added: measured, a child stroke under a null scaled to 50 % renders at half width.]
- Result over elegance: hacking a few layers for a few frames is fine. (UVDpgP7sRbw 00:08:02)

## Cameron (MotionXP)

- Impact: an overshoot key about 3 frames after the hit, nudged, eased. Falling keys 10 frames
  apart. (HpVtzOtaHlg 00:02:20)
- Gravity rule: a falling value curve must not slow down before impact; remove the hump.
  (HpVtzOtaHlg 00:03:26) [added: a linear contact key after an eased apex makes exactly this hump;
  measured 51 px per frame on the last frame against a 69 px peak.]
- Elastic: first overshoot to 120, then keys 6 frames apart with decaying amplitude; better on
  rotation than on scale; never on everything. (HpVtzOtaHlg 00:07:32, 00:08:05)
- Roving keys: a pasted path or uneven key spacing gets even speed with Rove Across Time.
  (HpVtzOtaHlg 00:09:12, 00:09:45) [added: measured, speed from 10 to 90 px per frame became a
  constant 40.]

## Bricks (camera moves with nulls)

- One null per camera move in a parent chain; key the next move before the previous ends so the
  moves blend. (PdHYC0gqIPA 00:05:30 to 00:07:12)
- Spin transition: the outgoing scene ramps up with no slow-down; the incoming scene starts fast and
  ramps down; same direction. (PdHYC0gqIPA 00:17:49, 00:20:11)
- Stagger list items 2 to 3 frames apart and fade everything in. (PdHYC0gqIPA 00:10:44, 00:03:56)
- In 3D, hide layers by moving them in Z, not by fading. (PdHYC0gqIPA 00:14:33)

## Jess Riley

- No good motion without good graphic design first: hierarchy, balance, contrast, negative space,
  rhythm. (0N0NHlvMEWs 00:02:16)
- Timing is hierarchy in time: how long a beat stays on screen changes legibility. (0N0NHlvMEWs
  00:04:33)
- Equal-width stair-step scene lengths are the failure case; vary them. (0N0NHlvMEWs 00:05:45 frame)
- Block the key poses as Hold keys first, then add easing. (0N0NHlvMEWs 00:06:06) Ben Marriott
  revisits the easing once the other elements exist. (UVDpgP7sRbw 00:04:16)

## Alan (itsalantime): motion blur

- 180 degree shutter with phase -90 (minus half the angle) is the realistic default; 0 is no blur;
  up to 720. (-ZJKoNj4WpQ 00:05:28 to 00:07:10)
- Phase shifts the blur behind or ahead of the object. (-ZJKoNj4WpQ 00:06:58) [added: measured,
  phase 0 puts the whole smear ahead in the direction of travel; -90 centers it.]
- Two switches: the layer switch and the comp switch. Keyframing Directional Blur instead is the
  beginner mistake. (-ZJKoNj4WpQ 00:01:38, 00:02:09)
- Samples Per Frame drives the blur of Classic 3D layers, shape layers and some effects; 2D layer
  motion adds samples on its own up to the Adaptive Sample Limit. The dialog in the video shows 64
  and 128. (-ZJKoNj4WpQ frame 00:05:30; doc `scripting-compitem-shutter`) [added: a comp made by
  script starts at 16 samples, so shape layers get fewer samples than in that dialog.]

## Commercial motion, character and UI sources (numbers animators state)

- Default Easy Ease is too weak for a thumb flick: 80 % influence on both sides of the stopping key.
  (Cameron Perry, wNFHUvtogOE 00:05:01 to 00:05:35)
- Time-Reverse Keyframes keeps the reversed ease: clear and re-ease afterwards. (wNFHUvtogOE
  00:06:39)
- Pop with overshoot: a key just before the last one above 100 % (about 110), then settle. (Josh
  Noel, lTJxtwMrWyE 00:06:23; Evan Abrams, EG7m3j1X9hQ 00:06:35)
- Stagger groups by depth (foreground, midground, background). (lTJxtwMrWyE 00:08:02)
- Match cut: scale 100 to 105 % in the last frames before the cut; "be subtle". (Ben Marriott,
  ythBGTLjot8 00:01:12, 00:01:47)
- Walk: contacts 16 frames apart, passing poses on the 8; keep hip keys on highs and lows only.
  (Evan Abrams, 1DiKTiOmrHE 00:06:07, 00:07:32)

## Disagreements and the deciding condition

| Choice              | Side A                                           | Side B                                                    | Decide by                                                                                            |
| ------------------- | ------------------------------------------------ | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Graph               | Value graph only (AG19fyRcOkA 00:08:13)          | Speed graph for paths (7pOCtlrrE3Y, xUmMHgZ9YfI 00:05:38) | Value graph for one-dimensional shape (bounce, overshoot); speed graph for a combined path           |
| Separate Dimensions | Separate to shape X and Y (AG19fyRcOkA 00:08:46) | Avoid, the path is lost (xUmMHgZ9YfI 00:01:04)            | Need different X and Y timing or a temporal overshoot on Position: separate, before easing           |
| Overshoot           | Extra key past the target (HpVtzOtaHlg 00:02:20) | Curve above target (7pOCtlrrE3Y 00:21:56)                 | Curve on 1D values; keys when the frame count of the overshoot must be fixed or Position is combined |
| Extra control       | Slider plus expression (6zrEKEuJGKs 00:03:49)    | Third key (6zrEKEuJGKs 00:08:39)                          | Third key first; expression only when keys cannot sculpt it                                          |
| Build               | Minimal keys (AG19fyRcOkA)                       | Hacks per shot (UVDpgP7sRbw 00:08:02)                     | Template that others edit: minimal keys. One-off hero shot: whatever reads                           |
