# Critique: self-review of generated input landed in 3ds Max

Run this before showing anything. A generated file that fails one line goes back to the Scenario MCP
(new run, other model, or a local fix) or is declined; it is not handed over with a note. Thresholds
marked [added] are this skill's own starting points, not expert or vendor numbers: tighten them per
project.

## 1. Numbers

| Check                             | Pass                                                                                                             | Fail action                                                             | Basis                                      |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------ |
| Scale against the known dimension | measured size on the known axis within 2 percent of the brief value                                              | rescale the root, never parts                                           | [added]                                    |
| Unit mismatch signature           | `scale_factor` not close to 10, 100, 1000, 2.54 or 30.48 (or their inverses)                                     | fix the import unit or system unit, then land again                     | [added]                                    |
| Base height                       | `base_z_after` equals the floor or placement height within 1 mm                                                  | move the root, not the meshes                                           | [added]                                    |
| Distance from origin              | asset root at the placement point, not left far from 0,0,0                                                       | move the root                                                           | aPc02tZzj8c 00:08:04                       |
| Face count                        | total faces at or below the `faceBudget` asked, and within the scene's budget for that asset class               | rerun with a lower budget, or hand to modeling or game-assets           | Scenario schemas, read 2026-11-24          |
| Node count                        | one root, a small number of meshes; no stray cameras, lights or empty helpers from the file                      | delete strays inside the undo record                                    | [added]                                    |
| Material classes                  | every class in `materials` is the scene's class (OpenPBR, Physical, VRayMtl, Corona) or is listed for conversion | hand to scenario-3dsmax-materials                                       | c3acjyR7j7E 00:05:02                       |
| Color space per map               | base color sRGB; normal, roughness, metalness, height, AO Raw; HDR and EXR linear                                | set per bitmap, or hand to materials                                    | QuJe2j7SHZ0 00:06:39; dlwDiLsPWgI 00:07:07 |
| Texture size                      | power of two or multiple of 16 as the model delivered; not upscaled past the model's stated limit                | regenerate at the right size                                            | Scenario schemas, read 2026-11-24          |
| Sky aspect                        | exactly 2:1                                                                                                      | regenerate with a skybox model                                          | `scenario-skyboxes`                        |
| Sky seam ratio                    | `seam_ratio` below 0.3                                                                                           | seam-preserving upscale or regenerate                                   | [added]                                    |
| Splat extent                      | a known feature (door 2.0 to 2.1 m, room height, road width) within 5 percent after Units and Up Axis            | change Preset, Up Axis or Units, never scale the native object by guess | [added]                                    |
| Image edit size and aspect        | output pixels and aspect equal the source render                                                                 | regenerate with explicit size, or crop and composite                    | zARHVN_XN4U 00:26:33                       |
| Video length and frame rate       | length requested; frame rate matches the edit or is conformed with ffmpeg                                        | conform, do not stretch                                                 | [added]                                    |
| Seed                              | variants of a liked take share its seed, recorded in each sidecar                                                | rerun with the recorded seed                                            | zARHVN_XN4U 00:14:15                       |
| UV checker                        | checker on map channel 1 shows no strong stretch on visible faces                                                | unwrap again (uv-baking or the Scenario UV step)                        | O6G6taj5M14 00:12:46                       |
| Provenance                        | sidecar `<file>.scenario.json` exists; node user properties set where the channel allows                         | write the sidecar before anything else                                  | [added]                                    |
| Versions                          | no file overwritten; scene saved as `_v002` or next                                                              | restore the previous version, save as new                               | brief rule                                 |

## 2. Visual checks on captures

Use `capture.views` (front, side, top, perspective) beside a known object (a 1.8 m figure box, a
door, a 0.75 m table) and a render from the scene camera. Read one contact sheet, not each image.

- Silhouette reads as the brief's object from all four views; no missing back side.
- No holes, floating shells or doubled surfaces; turn on backface display or a face orientation
  check (O6G6taj5M14 00:03:35).
- Stands on the floor: contact points touch, no sinking, no hover.
- Proportions next to the known object look right to a person who knows the object, not only on the
  measured axis.
- Textures: no smeared projection on hidden faces, no baked lighting that fights the scene light, no
  text or logos invented by the model.
- Smoothing: no faceted look on curved surfaces, no black streaks from flipped normals.
- Placement: the orthographic top view with control dimensions agrees with the plan (kBo57xFC3ic
  00:08:50).

## 3. Textures and skies

- Tile sheet (2 x 2) shows no seam cross and no repeated blotch that draws the eye (i3UbOzrAgLk
  00:05:01).
- Height map has medium contrast: no clipped white plateaus (i3UbOzrAgLk 00:08:36).
- Maps derived locally from a color-only texture are labeled approximations in the sidecar.
- Sky: horizon level and straight, sun position matches the physical sun direction, no visible seam
  at the 0 and 360 degree join in a test render, no poles pinched into a point.
- If the sky is LDR, the scene light comes from a physical sun and sky, and the generated image is
  background only.

## 4. Image edits on renders

Compare source and result side by side at full size (`max_review.compare`), then a detail crop of
the protected areas.

- Geometry, mullions, window frames and the building outline match the source within a pixel or two
  after compositing (elm00WQ03vw 00:05:14).
- Glass and reflections come from the render, not from the model (elm00WQ03vw 00:07:05).
- Light direction in the added context matches the rendered shadows (elm00WQ03vw 00:04:05).
- People: hands, faces and contact with furniture look right at delivery size; far people only when
  in doubt (1A7uOdk9Sng 00:09:05).
- Materials the client chose (a named stone, a fabric sample) are unchanged.
- Glass, fabric, fog and foggy brick come from the render, not the edit (y2-zbS5n8Ps 00:05:07 to
  00:06:31).
- Pasted detail crops line up with the frame: no step or shift along their borders (elm00WQ03vw
  00:08:33).
- Shadows of a time-of-day variant come from a 3ds Max re-render, not from the edit (elm00WQ03vw
  00:04:05).
- The share of AI in the image is visible to the reviewer: deliver the raw render beside the result
  (I6QPVe8c7jU 13:43).

## 5. Video takes

Read a contact sheet of the take (one frame every half second) and play it once at full speed.

- Walls, windows and the building outline do not morph between first and last frame (1A7uOdk9Sng
  00:02:50).
- Camera move matches the request (crane, dolly, orbit) and keeps one lens; no sudden FOV change
  (1A7uOdk9Sng 00:01:20).
- No objects appearing or vanishing; no text artifacts; no cut the model inserted on its own
  (1A7uOdk9Sng 00:09:05).
- People move without sliding feet or merging with furniture.
- Start frame matches the playblast or render it came from.

## 6. Client and policy checks

- The brief does not name a catalog product, supplier sample or drawing-dimension part that
  generation would approximate.
- The studio or client has no rule against generated content (Chaos and tyFlow switches exist for
  this; ask).
- No customer name, logo or private reference image sent to a model without the user's approval.
- The handover note says which assets are generated, by which model, on which date (from the
  sidecars), and that they are raw input, not production-final.
