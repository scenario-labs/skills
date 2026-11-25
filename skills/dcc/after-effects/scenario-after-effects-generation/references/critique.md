# Critique: judging generated media inside a comp

Score every generated asset before it leaves this skill. A reject on any line sends the asset back:
fix it in After Effects, or regenerate once with the cause named in the prompt.

## Numbers (from the procedures)

| Check              | Pass                                                       | Reject                            | How                                                                  |
| ------------------ | ---------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------- |
| Alpha mode         | fringe under 1 level vs an exact composite                 | rim above 5 levels                | asset on black and on white, compare                                 |
| Body alpha         | body over white minus over black under 0.5 level           | 2 levels or more                  | Levels on alpha, Input White 0.98                                    |
| Size               | `AEX.gen.upscaled(comp)` empty                             | any enabled layer above 105 %     | replace with an upscaled file; the audit skips disabled layers       |
| Effect upscale     | edge detail judged on frames                               | soft edges at 100 % view          | the audit cannot see effect upscales                                 |
| Loop seam          | seam RMSE at or under a normal frame step                  | seam above 1.5 x the normal step  | two frames each side of the seam                                     |
| Frame rate         | footage fps = comp fps, or conformed on purpose            | audit `layer.frameRateMismatch`   | `AEK.audit.comp(c)`                                                  |
| Flicker            | mean luminance step under 0.5 % per frame                  | visible pumping                   | ffmpeg `signalstats` YAVG per frame; Echo gave no gain when measured |
| Grain              | Add Grain Viewing Mode Final Output                        | grain in a box with its outline   | `VISINF Grain Implant-0021` = 3                                      |
| Model motion blur  | smear along the move on a mid-move frame                   | sharp model on a fast turn        | CC Force Motion Blur on the precomp (Advanced 3D)                    |
| Voice and bed      | voice-only and bed-only renders measured and written down  | balance set from gain values only | ebur128 on each solo render                                          |
| Layer holes        | 0 near-black pixels at the extreme camera frame            | any                               | count pixels with all channels under 12                              |
| Depth displacement | no doubled edge at the maximum amount                      | doubled or cut objects            | crop the sharpest depth edge                                         |
| 3D model           | present on a frame after a warm-up frame; materials listed | empty frame, missing material     | `ADBE3D Material Parade` names                                       |
| Mix                | true peak at or under -1 dBTP on the rendered mix          | over -1 dBTP                      | ebur128 on the render                                                |
| Caption sync       | word on screen within 2 frames of the voice                | 3 frames or more                  | probe frames vs `silencedetect`                                      |
| Provenance         | item and layer comment hold job, model, prompt, seed       | missing                           | `item.comment`                                                       |

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

## Scoring

- Pass: every number passes and the sheet shows none of the items above.
- Fix in After Effects: edge, body alpha, loop, size, level and sync problems.
- Regenerate once: wrong subject, broken anatomy, garbled text, broken continuity. Name the defect
  in the new prompt. If the second take fails too, change the approach (another model from
  `recommend`, or make the part by hand).
