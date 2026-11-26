# Sources

## Videos

| Expert                           | Credential                                          | URL                                         | Best for                                                                                              | Best timestamps                                            |
| -------------------------------- | --------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Jake Bartlett (Jake In Motion)   | After Effects educator, School of Motion instructor | https://www.youtube.com/watch?v=7pOCtlrrE3Y | Speed graph versus value graph, bounce from identical keys, shared handle edits, onion skin with Echo | 00:03:15, 00:06:26, 00:14:15, 00:16:35, 00:19:47, 00:20:19 |
| Jake Bartlett (Jake In Motion)   | same                                                | https://www.youtube.com/watch?v=6zrEKEuJGKs | Three tiers of easing, third key versus slider offset curve                                           | 00:01:11, 00:02:19, 00:04:21, 00:06:33, 00:08:07           |
| Jake Bartlett (Jake In Motion)   | same                                                | https://www.youtube.com/watch?v=xUmMHgZ9YfI | Spatial interpolation, drift between equal keys, linear default                                       | 00:00:32, 00:01:04, 00:04:33, 00:05:04                     |
| Joey Korenman (School of Motion) | School of Motion founder, motion designer           | https://www.youtube.com/watch?v=AG19fyRcOkA | Animation curves, bounce ratios, cartoon hang, minimal keys                                           | 00:08:46, 00:16:59, 00:23:06, 00:28:32, 00:35:35           |
| Ben Marriott                     | Motion designer and educator                        | https://www.youtube.com/watch?v=UVDpgP7sRbw | Snappy ease, copying one ease to many elements, hiding changes in fast frames                         | 00:02:40, 00:04:02, 00:06:27                               |
| Ben Marriott                     | same                                                | https://www.youtube.com/watch?v=ythBGTLjot8 | Match cuts, subtle scale before the cut                                                               | 00:01:12, 00:01:47                                         |
| Cameron (MotionXP)               | Motion designer and educator                        | https://www.youtube.com/watch?v=HpVtzOtaHlg | Falling, impact overshoot, elastic, roving keys, time remap trick                                     | 00:02:20, 00:03:26, 00:07:32, 00:09:12, 00:11:23           |
| Bricks                           | Motion designer and editor                          | https://www.youtube.com/watch?v=PdHYC0gqIPA | Camera moves from a chain of nulls, overlapping moves, stagger                                        | 00:05:30, 00:10:44, 00:17:49                               |
| Jess Riley (Tuts+)               | Graphic and motion designer                         | https://www.youtube.com/watch?v=0N0NHlvMEWs | Principles: timing, easing, anticipation, follow-through, design first                                | 00:02:16, 00:04:33, 00:05:05                               |
| Alan (itsalantime)               | Motion designer, video producer                     | https://www.youtube.com/watch?v=-ZJKoNj4WpQ | Shutter angle and phase, the two motion blur switches                                                 | 00:01:38, 00:05:28, 00:06:58                               |
| Cameron Perry (Spark Point)      | UI and UX motion designer                           | https://www.youtube.com/watch?v=wNFHUvtogOE | 80 % influence for a flick, reversing keys                                                            | 00:05:01, 00:06:39                                         |
| Josh Noel (SonduckFilm)          | Motion designer and educator                        | https://www.youtube.com/watch?v=lTJxtwMrWyE | Overshoot pop, depth stagger                                                                          | 00:06:23, 00:08:02                                         |
| Evan Abrams (ECAbrams)           | Motion designer and educator                        | https://www.youtube.com/watch?v=EG7m3j1X9hQ | Overshoot to 110 on an animate-off                                                                    | 00:06:35                                                   |
| Evan Abrams (ECAbrams)           | same                                                | https://www.youtube.com/watch?v=1DiKTiOmrHE | Walk timing in frames, fewer hip keys                                                                 | 00:06:07, 00:07:32                                         |

## Documentation

| Page                            | URL                                                            | Used for                                                                                                     |
| ------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Scripting: Property (keyframes) | https://ae-scripting.docsforadobe.dev/property/property/       | `setTemporalEaseAtKey`, spatial tangents, roving, `dimensionsSeparated`, `getSeparationFollower`, key labels |
| Scripting: KeyframeEase         | https://ae-scripting.docsforadobe.dev/other/keyframeease/      | `KeyframeEase(speed, influence)`, influence 0.1 to 100, one ease per dimension                               |
| Scripting: CompItem             | https://ae-scripting.docsforadobe.dev/item/compitem/           | `motionBlur`, `shutterAngle` 0 to 720, `shutterPhase` -360 to 360, samples 2 to 64, adaptive limit 16 to 256 |
| Expressions: interpolation      | https://ae-expressions.docsforadobe.dev/general/interpolation/ | `linear`, `ease`, `easeIn`, `easeOut`                                                                        |
| Expressions: Property           | https://ae-expressions.docsforadobe.dev/objects/property/      | `valueAtTime`, `velocityAtTime`, `nearestKey`, `nextKey` and `previousKey` (26.0+), loops                    |

## Live measurements

Every number marked "measured" in this skill comes from a case run on After Effects 27.0 through the
scenario-after-effects-expert bridge; the jobs are reproduced in [procedures.md](procedures.md).
