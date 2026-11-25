# Critique: judging a 3D shot before anyone sees it

In a 32 bpc project, saved PNG frames read at one tenth of their brightness: build the sheet with
`ae.py sheet ... --gain 10`. Run the numeric checks first, then look at ONE contact sheet: a warm-up
frame discarded, then start, middle and end frames, plus the fastest moment of the move. Judge the
picture honestly; a passing number never excuses a wrong frame.

## 1. Numbers (from a job)

| Check                    | Pass                                                                                                                                  | How                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Renderer                 | `ADBE Calder` (Advanced 3D) for models, extrusion, Substance, shadow color; `ADBE Advanced 3d` (Classic 3D) only for flat 2.5D        | procedure 1                               |
| Environment light source | a layer source only in an Advanced 3D comp                                                                                            | procedure 1 `lights[].source`             |
| Model fit                | footprint height x scale / 100 between 35 and 65 % of comp height                                                                     | `fitModel` result                         |
| Base on floor            | anchor Y equals footprint bottom; layer Y equals the catcher's Y                                                                      | read `ADBE Anchor Point`, `ADBE Position` |
| Catcher                  | `ADBE Accepts Shadows` 2, `ADBE Casts Shadows` 0, layer 3D, above the plate                                                           | read Material Options                     |
| Shadow light             | at least one light with `ADBE Casts Shadows` 1 (spot or parallel, or the environment light in Advanced 3D)                            | `AEX.threeD.settable`                     |
| Camera keys              | no LINEAR key on the rig null or camera; influence 33 to 80 %; camera keys change only Z, none on its Point of Interest               | `AEK.motion.keys`                         |
| Zoom                     | comp width x focal length / 36 (50 mm: 1333.3 px at 960 wide)                                                                         | read `ADBE Camera Zoom`                   |
| Focus                    | expression on Focus Distance with empty `expressionError`; value within 10 % of the camera to subject distance on every sampled frame | `valueAtTime` at 3 times                  |
| Focus area (Advanced 3D) | `ADBE Camera Focus Area Width` above 0 when the subject has depth                                                                     | read                                      |
| Motion blur path         | Advanced 3D: CC Force Motion Blur on the precomp layer, enabled for the final; Classic: layer switch and `comp.motionBlur` both true  | read                                      |
| Parallax coverage        | `screenRect` left 0 or less, right comp width or more, at the last frame, for every layer                                             | procedure 8                               |
| Depth displacement       | max 15 to 40 px at 960 wide, keyed to 0; the map layer is a precomp                                                                   | procedure 9                               |
| Environment light        | Y Rotation keyed when the product has glossy parts; tinted through a precomp of its source when the plate has a cast                  | procedure 11                              |
| Frame time               | first frame 2 to 4 s is normal; later frames above 2 s at 960x540 mean a heavy mesh or DoF samples                                    | job timing                                |
| Output                   | `ae.py probe`: size, fps, frame count as planned                                                                                      | probe                                     |

## 2. The contact sheet

Look for each item, in this order.

1. **The model is there in every frame.** A missing model on the first frame means no warm-up; on
   later frames, the wrong renderer.
2. **Recognizable and centered.** The product reads as itself, its silhouette is not cropped at the
   closest point of the push, and it does not drift off the third it was framed in.
3. **Grounded.** The base touches its shadow; there is no gap of light under it. Abrams and Motion
   Nations look at the contact area first (wwsHGbZN6ZU 00:06:42).
4. **Shadow logic.** The shadow falls away from the brightest side of the plate and the HDRI
   highlight sits on the same side (9LxKSsftUS4 00:02:15). Shadow edge softness matches the plate's
   own shadows. Its color is a darker plate color, never pure black (Shadow Darkness 50 to 70 %,
   tinted Shadow Color in Advanced 3D). The model's light carries the plate's cast too: a white HDRI
   on a pink room reads pasted on (wwsHGbZN6ZU 00:09:49).
5. **No white floor.** A white rectangle means Accepts Shadows is On, not Only.
6. **Reflections move.** On glossy parts, highlights travel across the surface during the orbit or
   the environment rotation (iOZkdYZPVU0 00:19:26). Flat, static shading means the environment light
   is missing or at 0.
7. **Text and model never intersect.** Check start, middle and end; the orbit changes what overlaps.
8. **Focus.** The subject is sharp on every frame; the text behind is soft; the floor goes soft with
   distance. A soft subject means focus on the base or Focus Area Width 0.
9. **Motion blur only where the move is fast.** Smear along the direction of travel on the fastest
   frame, none on held frames; no stepped ghost copies (raise samples).
10. **Plate integration.** Black levels of the model and its shadow sit near the plate's darkest
    areas; the model is not sharper than the plate (Max Novak QlbZDu2tZfE 00:10:18 adds 0.1 to 0.2
    px Fast Box Blur and light grain, and matches shadow RGB to the plate's shadows in the Info
    panel).
11. **2.5D.** No frame edge, no hole behind a cut-out, no doubled edge from displacement, no layer
    that slides against its own shadow.

## 3. Severity

- Blocker: missing model, wrong renderer for the content, crash risk (layer source in a Classic
  comp), white catcher, subject out of focus, text through the product, frame edge visible.
- Fix before delivery: shadow direction against the plate, black shadow, linear camera keys, stepped
  motion blur, reflections static.
- Note only: render time high but within budget, small DoF grain (raise quality in Renderer Options,
  GUI).
