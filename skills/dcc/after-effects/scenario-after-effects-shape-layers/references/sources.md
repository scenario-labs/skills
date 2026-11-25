# Sources

Every expert claim in this skill points to one of these. Timestamps are `hh:mm:ss` in the video.

## Videos

| Expert                              | Credential                                   | URL                                         | Best for                                                                                              | Best timestamps                                                      |
| ----------------------------------- | -------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Sarah Wade (School of Motion)       | Motion designer, School of Motion instructor | https://www.youtube.com/watch?v=rtt-gGDxrZ4 | Stroke Taper and Wave values, sharing one stroke across groups, Create Nulls From Paths               | 00:01:40, 00:03:39, 00:07:28, 00:12:22, 00:16:44, 00:21:03, 00:23:45 |
| Manuel (Manuel does Motion)         | Motion designer                              | https://www.youtube.com/watch?v=748l7DIU4bQ | Trim Paths coupling (End = Start + 0.1), `pointOnPath` followers, tapered arrows                      | 00:01:07, 00:02:17, 00:03:03, 00:04:43, 00:05:54, 00:06:46           |
| Evan Abrams (ECAbrams)              | Motion designer, independent educator        | https://www.youtube.com/watch?v=wOZwzLgJw9o | Repeater logic: 360 / Copies, compounding transforms, arrive and leave on different properties        | 00:02:23, 00:04:28, 00:05:01, 00:06:55, 00:09:40                     |
| Abhishek Dubey (Motion Nations)     | Motion designer                              | https://www.youtube.com/watch?v=7LW5mRTvNcY | Line follows ball: path pasted to Position, Trim chase checked frame by frame                         | 00:00:33, 00:05:20, 00:06:40, 00:11:12, 00:13:22                     |
| Alex Deaton (School of Motion)      | Motion designer                              | https://www.youtube.com/watch?v=heYi6xLWvB0 | Mask-through-shape in one layer with Merge Paths Intersect, operator order, its limits                | 00:02:37, 00:08:06, 00:11:27, 00:13:47, 00:18:50, 00:21:00           |
| Megan Friesth (Animation Explained) | Motion designer, instructor                  | https://www.youtube.com/watch?v=qV3KXRrGm-A | Illustrator prep and import, Retain Layer Sizes, Dynamic Link limits, Create Shapes from Vector Layer | 00:03:57, 00:09:27, 00:12:10, 00:14:55, 00:18:04, 00:21:24           |
| Megan Friesth (Animation Explained) | Motion designer, instructor                  | https://www.youtube.com/watch?v=TVepzaUT6Dw | Parametric versus Bezier, Size versus Scale, Convert to Bezier Path is one way                        | 00:00:49, 00:01:23, 00:02:39, 00:04:05                               |
| Jake Bartlett (Jake In Motion)      | Motion designer, instructor                  | https://www.youtube.com/watch?v=I6QlicggqtY | Design-file hand-off (Overlord), parametric data from Figma, scaling small mobile frames              | 00:03:30, 00:05:31, 00:08:55, 00:11:17                               |
| Ben Marriott                        | Motion designer, instructor                  | https://www.youtube.com/watch?v=3EGuLX6PsQ4 | Morph hidden in a cut at peak speed, anticipation, separate dimensions                                | 00:00:30, 00:01:02, 00:03:21, 00:05:39                               |
| Daniel (Design Break)               | Web and UI motion designer                   | https://www.youtube.com/watch?v=HZ1_afAjVb0 | Illustrator vectors for Lottie: shapes over pasted masks, Difference masks lose counters              | 00:02:48, 00:06:01, 00:07:24, 00:09:24                               |

## Documentation

| Source                                                        | URL                                                                                     | Best for                                                                                      |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Adobe: shape layers, paths and vector artwork                 | https://helpx.adobe.com/after-effects/using/overview-shape-layers-paths-vector.html     | Render order inside a group, parametric versus Bezier paths, grouping                         |
| Adobe: shape attributes, paint operations and path operations | https://helpx.adobe.com/after-effects/using/shape-attributes-paint-operations-path.html | Every operator, Repeater above or below paint, Wiggle Transform placement, fill rules, dashes |
| After Effects Scripting Guide: shape layer match names        | https://ae-scripting.docsforadobe.dev/matchnames/layer/shapelayer/                      | Match names (cross-check with the live table in procedures.md)                                |
| After Effects expression reference: Path property             | https://ae-expressions.docsforadobe.dev/objects/path-property/                          | `points()`, `pointOnPath()`, `tangentOnPath()`, `createPath()`, group-anchor space            |
| LottieFiles: Lottie compatibility                             | https://docs.lottiefiles.com/en/integrations/after-effects/09_lottie-compatibility.md   | What converts, partially converts or drops                                                    |
| Overlord documentation (Illustrator)                          | https://battleaxe.co/overlord/docs/illustrator                                          | What transfers from Illustrator, Split versus Push versus Single Layer                        |

## Measured

Live tests on After Effects 27.0 (build 27.0x78, macOS): match names, enum ranges, operator order,
morph behavior, vector import and conversion, resolution checks. The procedures that carry
`checked: live 27.0` were run there.
