# Critique: judging a composite and skin after an edit

Order of judgment:

1. The element alone: edges on black, white and gray at 100%.
2. The code gates after each toolkit call.
3. The element in the scene: light, shadows, tone, grain.
4. Skin and identity, when a person was regenerated, relit or upscaled.
5. The canvas at fit-to-screen, then the handoff.

A stage passes only when every code gate passes and every visual item for it has been looked at and
noted. The numbers catch rims, casts, missing grain and lost texture. They never catch a wrong light
direction, a floating object, a changed face or a cast shadow on the wrong side.

## 1. The cutout

- **Edges on three backgrounds:** no light or dark rim, no background color left in hair or fur, no
  see-through holes in solid parts, no stair steps (P4 sheet).
- **Fine structure:** branches and hair keep their gaps open; thin parts are not thickened or
  merged. Remove Background tends to fill gaps on fine branches.
- **Edge softness:** matches the plate at the same distance from the focus plane. A razor edge on a
  soft background reads as pasted; a soft edge on a sharp product reads as a mask error.
- **What touches the ground:** feet, wheels or a base are complete, not clipped by the mask.

## 2. Code gates

| Gate                           | Pass                                      | Fails on                                     |
| ------------------------------ | ----------------------------------------- | -------------------------------------------- |
| `G.halo(layer)`                | `light_rim` and `dark_rim` 8 or less      | a fringe from the old background             |
| `fix_halo` before and after    | after lower than before; px 3 or less     | a rim the Minimum filter cannot reach        |
| `shadows` ground luminance     | under the base darker by more than 3      | silhouette from the wrong layer, empty layer |
| `match_tone` cast distance     | after closer to the scene than before     | a cast that is light, not color              |
| `match_tone` luminance         | within 12% of before                      | a Curves point clipped at 1 or 254           |
| `match_grain` end              | within 50% of target, or action none      | grain larger than the noise sizes tried      |
| Texture ratio                  | at least 0.6, same region, after / before | regenerated or smoothed skin and surfaces    |
| `skin_line_delta`              | within 10 degrees                         | orange, magenta or green skin                |
| `RT.verify_fs`                 | max 2 or less (8-bit), 0 to 1 (16-bit)    | wrong Apply Image recipe, edited source      |
| `A.history_gate(h0, undo)`     | `[]` after each toolkit call              | a stray edit on the user's document          |
| `A.deliverable("psd-handoff")` | returns `[]`                              | empty layers, or hidden ones outside "Takes" |

Thresholds are authoring-time: the halo and texture numbers come from the lead's gates, the tone and
grain bounds from the live suite on one sample photo. Check them on your own images.

## 3. The element in the scene

- **Light direction:** highlights on the element face the plate's key light; the shadow side faces
  away from it.
- **Light quality:** hard light gives a hard terminator and a sharp cast; overcast gives soft both.
- **Contact:** the darkest shadow sits where the element touches the ground, densest at the contact
  points; nothing floats.
- **Cast:** points the same way as the plate's own shadows, at a plausible length; it fades and
  softens with distance from the contact.
- **Tone:** blacks and highlights of the element match the plate's at fit-to-screen; no colored rim
  of the old background's light.
- **Grain:** the same size and strength inside and outside the edge at 100% and 200%, including on
  generated patches inside the plate.
- **Perspective and scale:** the element's horizon and camera height match the plate's.
- **Reflections:** a reflective floor or water shows the element where the plate would.

## 4. After Harmonize or a relight

- **Identity:** face, hair, logo, text and product shape against the original. Any change is masked
  back from the original.
- **Detail:** at 200%, the result keeps the original's fine detail. Generated light often softens
  it; the texture ratio flags it.
- **Color:** the Luminosity copy keeps the original color; the color copy is only partway.
- **Baked shadows:** shadows the result painted move with the element; move it, then run the light
  again.

## 5. Skin after a generative edit

- **Texture:** pores visible at 100% on the cheeks, nose and forehead; no waxy, airbrushed patch.
  The ratio against the original is at least 0.6.
- **Eyes:** pupil size, iris pattern, catchlights and eyelids as in the original.
- **Teeth and lips:** shape and count unchanged. Smoothing stays off eyes, teeth and hair, where it
  reads as fake (Toma [3eURUBIrhRY 09:59]).
- **Marks:** moles, freckles and scars the person keeps are still there, faded at most.
- **Hairline and brows:** strands continue across the edit; no smeared transition.
- **Skin line:** `skin_line_delta` within 10; saturation below the vectorscope's midpoint.
- **Frequency separation:** after retouching, the texture layer still carries pores across the
  painted area; Lighten on the tone layer kept the texture visible.

## 6. Canvas and handoff

- Look at fit-to-screen for the overall read: one light, one tone, one grain.
- Layers are named, the element is a masked smart object, the matches are clipped to it, and the
  retouch scaffolds start behind black masks.
- The report lists the gate numbers, the crops looked at and what was not verified.
