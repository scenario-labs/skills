# Critique: judging generated media inside a comp

Score every generated asset before it leaves this skill. A reject on any line sends the asset back:
fix it in After Effects, or regenerate once with the cause named in the prompt.

## Numbers (from the procedures)

| Check                       | Pass                                                                                                         | Reject                                                  | How                                                                           |
| --------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Alpha mode                  | fringe under 1 level vs an exact composite                                                                   | rim above 5 levels                                      | asset on black and on white, compare                                          |
| Body alpha                  | body over white minus over black under 0.5 level                                                             | 2 levels or more                                        | Levels on alpha, Input White 0.98                                             |
| Size                        | `AEX.gen.upscaled(comp)` empty                                                                               | any enabled layer above 105 %                           | replace with an upscaled file; the audit skips disabled layers                |
| Effect upscale              | edge detail judged on frames                                                                                 | soft edges at 100 % view                                | the audit cannot see effect upscales                                          |
| Loop seam                   | seam RMSE at or under a normal frame step                                                                    | seam above 1.5 x the normal step                        | two frames each side of the seam                                              |
| Frame rate                  | footage fps = comp fps, or conformed on purpose                                                              | audit `layer.frameRateMismatch`                         | `AEK.audit.comp(c)`                                                           |
| Flicker                     | mean luminance step under 0.5 % per frame                                                                    | visible pumping                                         | ffmpeg `signalstats` YAVG per frame; Echo gave no gain when measured          |
| Grain                       | Add Grain Viewing Mode Final Output                                                                          | grain in a box with its outline                         | `VISINF Grain Implant-0021` = 3                                               |
| Model motion blur           | smear along the move on a mid-move frame                                                                     | sharp model on a fast turn                              | CC Force Motion Blur on the precomp (Advanced 3D)                             |
| Voice and bed               | voice-only and bed-only renders measured and written down                                                    | balance set from gain values only                       | ebur128 on each solo render                                                   |
| Layer holes                 | 0 near-black pixels at the extreme camera frame                                                              | any                                                     | count pixels with all channels under 12                                       |
| Depth displacement          | no doubled edge at the maximum amount                                                                        | doubled or cut objects                                  | crop the sharpest depth edge                                                  |
| 3D model                    | present on a frame after a warm-up frame; materials listed                                                   | empty frame, missing material                           | `ADBE3D Material Parade` names                                                |
| Mix                         | true peak at or under -1 dBTP on the rendered mix                                                            | over -1 dBTP                                            | ebur128 on the render                                                         |
| Caption sync                | word on screen within 2 frames of the voice                                                                  | 3 frames or more                                        | probe frames vs `silencedetect`                                               |
| Provenance                  | item and layer comment hold job, model, prompt, seed                                                         | missing                                                 | `item.comment`                                                                |
| Clean plate drift           | original pixels outside every edit mask                                                                      | edited pixels kept outside the mask                     | difference against the original, masked (procedure 9)                         |
| Element on black            | corner lift under 1 level over gray                                                                          | veil of several levels                                  | Levels Input Black, then Screen; corner mean over a gray solid (procedure 10) |
| Seated object light         | object highlights within 0.15 blue-to-red of the plate's lit ground                                          | studio-cool highlights on a warm plate (+0.32 measured) | `scripts/seat_check.py` before the build                                      |
| Seated object integration   | `integration_check.py` exit 0 on the first and last frame (light, shade, rim, shadow, contact, finish)       | any gate failing                                        | compositing skill's script, procedure 12 step 8                               |
| Seated object scale         | width = real length x (base row - horizon row) / camera height                                               | sized by eye, small in frame                            | procedure 12                                                                  |
| Cast shadow                 | runs from the base away from the plate's shadow meeting point; a round object casts its model's shadow       | own angle; mirrored silhouette under a round object     | procedure 12 routes                                                           |
| Contact                     | gap from the object's lowest row to the shadow's first row 2 px or less where it rests, first and last frame | 9 to 12 px median: the object floats                    | `seat_check.py --contact` on mattes, procedure 12                             |
| Push-in (2.5D)              | front plane grows 1.35 times or more; subject-to-back parallax 5 % of width or more                          | growth 1.25 and parallax 2.25 % read as a still         | `screenRect` and `parallax` (3D skill)                                        |
| Element over a bright plate | element changes the plate by 10 levels or more where it is dense                                             | it vanishes (under 5 levels)                            | darker fill with the element as luminance matte (procedure 10)                |

## Contact sheet: what to look for

- Edges: a light or dark line around a cutout on black or white; stair-stepped edges from binary
  alpha.
- Anatomy: a wrong finger count, eyes out of line, detached limbs; a prop with the right number of
  parts.
- Text: any letters inside generated pixels. Garbled text rejects; replace it with live type.
- Continuity across frames: logo, product shape, color and the count of objects stay fixed.
- Compression: blocking in gradients, mosquito noise around edges, banding in skies.
- Motion: boiling texture, objects that appear or vanish, a camera move that was not asked for.
- Parallax and depth: holes, halos, ghost copies of trees or buildings, stretched edges.
- Style: the palette and line weight match the approved style frame.
- Rebuilt patches behind a plane, at 1:1: no ghost of the removed object, no seam where the original
  takes over.
- An element in Screen: no gray veil in the corners; it still reads over the brightest part of the
  plate.

## Scoring

- Pass: every number passes and the sheet shows none of the items above.
- Fix in After Effects: edge, body alpha, loop, size, level and sync problems.
- Regenerate once: wrong subject, broken anatomy, garbled text, broken continuity. Name the defect
  in the new prompt. If the second take fails too, change the approach (another model from
  `recommend`, or make the part by hand).
