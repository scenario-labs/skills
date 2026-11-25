# GUI paths: shape layers

For a person, or an agent driving the interface, doing the same work as the procedures. macOS
shortcuts first, Windows in parentheses.

## Build and organize

| Task                                    | Path                                                                                                              |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| New shape layer                         | Layer > New > Shape Layer                                                                                         |
| Draw a parametric shape                 | Rectangle tool (Q, cycles Rounded Rectangle, Ellipse, Polygon, Star); drag with no layer selected for a new layer |
| Draw a Bezier path                      | Pen tool (G); Convert Vertex tool to toggle smooth and corner points                                              |
| Add an item to a group                  | Timeline > shape layer > Contents > Add menu (arrow button), or the Add menu in the Tools panel                   |
| Add an operator at the end of the group | Option-click (Alt-click) the item in the Add menu                                                                 |
| Group shapes                            | Select the items in Contents, Cmd+G (Ctrl+G); ungroup Cmd+Shift+G (Ctrl+Shift+G)                                  |
| Reorder items                           | Drag in Contents: paths above operators, operators above Stroke and Fill                                          |
| Convert parametric to Bezier            | Right-click the Rectangle, Ellipse or Polystar path > Convert To Bezier Path (one way)                            |
| Set the first vertex                    | Select one vertex with the Pen or Selection tool, right-click > Mask and Shape Path > Set First Vertex            |
| Reverse direction                       | Click the Reverse Path Direction button on the path item in Contents                                              |
| Open a closed path                      | Pen tool, Option-click (Alt-click) a segment to delete it, or delete one vertex                                   |

## Operators and strokes

| Task                              | Path                                                                                                              |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Trim Paths draw-on                | Add > Trim Paths; key End 0 to 100 %; Trim Multiple Shapes: Simultaneously or Individually                        |
| Repeater ring                     | Add > Repeater; Copies N; Transform: Repeater > Position 0,0, Rotation 360 / N                                    |
| Merge Paths                       | Add > Merge Paths; Mode: Merge, Add, Subtract, Intersect, Exclude Intersections                                   |
| Taper and Wave                    | Stroke > Taper (Start and End Length, Width, Ease) and Stroke > Wave (Amount, Units, Wavelength or Cycles, Phase) |
| Dashes                            | Stroke > Dashes > the plus button adds a Dash and Gap pair (up to three)                                          |
| Link a mask path to the main path | Option-click (Alt-click) the mask Path stopwatch, pick-whip to the main Path                                      |
| Easy Ease                         | Select keys, F9; Graph Editor Shift+F3; right-click > Keyframe Velocity for numbers                               |

## Intake

| Task                                  | Path                                                                                                                                          |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Import SVG as shape layers            | File > Import > File, choose the SVG, Import As: Composition - Retain Layer Sizes (26.0+)                                                     |
| Paste vector art                      | Copy in Illustrator, Edit > Paste in After Effects (26.3+): native shape layers. Before 26.3 a paste onto a solid gives Difference-mode masks |
| Illustrator text as editable text     | 27.0: steps on Adobe's Import SVG files help page, section on editable text layers                                                            |
| Import Illustrator layers             | File > Import > File, Import As: Composition - Retain Layer Sizes                                                                             |
| Convert Illustrator footage to shapes | Select the layer, Layer > Create > Create Shapes from Vector Layer (also on right-click > Create)                                             |
| Convert text to shapes                | Select the text layer, Layer > Create > Create Shapes from Text                                                                               |
| Release Illustrator sublayers         | In Illustrator: Layers panel menu > Release to Layers (Sequence), then drag the new layers out of the parent                                  |
| Sharp vector footage above 100 %      | Turn on the Continuously Rasterize switch (the sun icon) in the timeline Switches column                                                      |

## Lottie

| Task             | Path                                                                                                                                |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Bake expressions | Select the property, Animation > Keyframe Assistant > Convert Expression to Keyframes                                               |
| Export           | Bodymovin: Window > Extensions > Bodymovin, select the comp, Settings, Render. LottieFiles plugin: its panel in Window > Extensions |
| Check            | Preview the JSON in the target player and compare with an After Effects frame at the same time                                      |

Bodymovin and the LottieFiles plugin are third-party CEP panels; neither exposes a scripting
interface, so the export is a GUI step.
