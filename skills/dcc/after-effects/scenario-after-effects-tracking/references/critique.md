# Critique rubric: tracking and stabilization

Score each line pass or fail. A fail on a measurable line blocks delivery. Numbers assume the
footage's own frame rate and pixel size.

## Track data

| Check                   | Pass                                                    | How                                                                                |
| ----------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Keys cover the span     | keys on every frame of the layer span, all four corners | procedures P10 `everyFrame`                                                        |
| Data written as tracked | round-trip error under 0.01 px                          | `AEX.track.readCorners` versus the input                                           |
| Accuracy                | mean under 1 px, worst frame under 2 px                 | `track_external.py score`, or a re-registration of 3 frames (start, middle, worst) |
| No lost frames          | `inliers` above 8 on every frame                        | `plane.json`                                                                       |
| Drift                   | error at the last frame no more than 1.5x the mean      | per-frame list from `score`                                                        |
| Corner order            | UL, UR, LL, LR in Corner Pin                            | an insert with a visible grid is not twisted on the sheet                          |

## Background analyzers

| Check                           | Pass                                                                                     | How                                                |
| ------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Analysis finished               | `banner` reports `none` on a frame captured after the last setting change                | procedures P2                                      |
| No banner in a delivered render | middle band not blue or orange on 3 frames                                               | `track_external.py banner` on frames from the file |
| Solve quality (3D)              | Average Error under 1 px, read in the GUI and reported with Solve Method and Method Used | Effect Controls > Advanced                         |
| Solve check by frames           | slide of a proof solid against a ground feature under 1 px                               | P9 on the render                                   |
| Reference swapped back          | the sharpened `track_ref` precomp disabled, the original plate enabled                   | P13 return value                                   |
| Scene scale                     | the solved camera and ground do not sit at a huge scale; Normalize Track run if they did | camera Position values against the comp size       |

## Stabilization

| Check                  | Pass                                                                                            | How                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Residual jitter        | second-difference RMS under 0.2 px                                                              | P3 on the render                                              |
| Intended move kept     | residual path range close to the smoothed path (not zero) unless a lock was asked               | `shake` on the render                                         |
| Scale-up               | under the agreed limit (example: 110 % for HD from HD)                                          | `scaleNeeded`, or the ORB scale estimate for Warp             |
| Borders                | no black edge on any frame                                                                      | sheet at 4 frames plus the frame with the largest correction  |
| Warp artifacts         | straight lines stay straight, no wobble at the edges                                            | sheet; compare with Stabilize Only framing                    |
| Blur after stabilizing | no soft frames left where the shake was; Camera-Shake Deblur sits below Warp Stabilizer if used | sheet at the frames with the largest correction; effect order |
| Synthesized edges      | no tearing at the first frames or on fast moves                                                 | sheet at frames 0 to 5 and the fastest frame                  |

## Screen insert integration

| Check       | Pass                                                                                                                                                  | How                                                    |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Motion blur | `blurReady` true on moving inserts                                                                                                                    | P10                                                    |
| Size        | `cornerPin` route: plate unscaled in a comp at footage size, insert at the screen's aspect. Pasted Mocha data: insert precomp at tracked footage size | `comp.width`, plate scale, `item.width`, `item.height` |
| Black level | insert blacks within 5 levels of the plate's screen blacks (8 bpc)                                                                                    | sample 7x7 pixels on a flat area                       |
| Grain       | high-pass deviation within 25 % of the plate's                                                                                                        | P8 measurement                                         |
| Edges       | no edge sharper than the plate's bezel edge                                                                                                           | sheet at 400 % crop                                    |
| State       | `bitsPerChannel` and `linearBlending` recorded with every level number                                                                                | P8 return value                                        |

## Contact sheet (one per case)

Frames: first, middle, the slip frame and two frames around it, last. Look for:

- the insert or element swimming against the bezel, corners or ground texture;
- blue "Analyzing" or orange "Stabilizing" bands;
- black borders after stabilization, or a sudden zoom;
- a squashed or stretched insert on a front-on frame;
- a sharp insert on a blurred plate on fast frames;
- fingers or reflections cut by the insert (hand to scenario-after-effects-compositing).

## Report

State the tracker chosen and why, the error numbers, the scale-up, what was done in the GUI and by
whom, and what a person must still check at full frame rate (motion feel of a smoothed camera,
parallax of placed 3D elements).
