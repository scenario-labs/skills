# GUI paths (for a person or a computer-use agent)

Shortcuts are macOS first, Windows in parentheses. Each row names the scripted substitute that this
skill ran.

## Keys and easing

| Task                                  | GUI path                                                                                                                                               | Scripted substitute                                                             |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| Easy Ease, In, Out                    | Select keys, F9; Shift+F9 (Ease In); Cmd+Shift+F9 (Ctrl+Shift+F9) (Ease Out)                                                                           | `AEX.animation.move(..., {out: 33.33, "in": 33.33})`                            |
| Exact influence and speed             | Right-click a key > Keyframe Velocity (Cmd+Shift+K, Ctrl+Shift+K)                                                                                      | `setTemporalEaseAtKey(k, [KeyframeEase(speed, influence)], [...])`              |
| Linear, Bezier, Hold                  | Right-click a key > Keyframe Interpolation; Cmd+Option-click (Ctrl+Alt-click) toggles linear and auto Bezier                                           | `setInterpolationTypeAtKey(k, in, out)`                                         |
| Graph Editor                          | Button above the layer list, or Shift+F3                                                                                                               | `AEK.motion.sample` (values and speed per frame)                                |
| Speed or value graph                  | Graph Editor > Choose graph type (bottom bar)                                                                                                          | sample speed (speed graph) or value (value graph)                               |
| Keep handles flat                     | Shift while dragging a handle                                                                                                                          | speed 0 in `KeyframeEase`                                                       |
| Break a handle                        | Option (Alt) on a handle                                                                                                                               | `setTemporalContinuousAtKey(k, false)`, then different in and out eases         |
| Add a key on the curve                | Cmd-click (Ctrl-click) the graph                                                                                                                       | `setValueAtTime(t, valueAtTime(t, true))`                                       |
| Post-expression graph                 | Graph Editor > Show Post-Expression Graph                                                                                                              | compare `valueAtTime(t, true)` with `valueAtTime(t, false)`                     |
| Time-reverse keys                     | Animation > Keyframe Assistant > Time-Reverse Keyframes; then re-ease (the ease reverses too)                                                          | re-create keys with values swapped, then ease                                   |
| Scale key timing                      | Option-drag (Alt-drag) the last selected key                                                                                                           | `shiftKeys` per key, or recompute times                                         |
| Reveal keyed properties               | U; UU for every changed property                                                                                                                       | `AEX.animation.animatedProps(layer)`                                            |
| Copy ease (EaseCopy panel or by hand) | Graph Editor handle drag on many keys at once                                                                                                          | `AEX.animation.copyEase(src, dst)`                                              |
| Group easing                          | Select the similar keys of several layers (U to reveal them), open the speed graph, pull one handle: every selected key follows (7pOCtlrrE3Y 00:19:47) | `copyEase` from one shaped reference to each layer                              |
| Block with holds                      | Select the pose keys, Animation > Toggle Hold Keyframe; ease after the timing reads (0N0NHlvMEWs 00:06:06)                                             | `setInterpolationTypeAtKey(k, HOLD, HOLD)`, then `move` or `bezier` per segment |

## Spatial

| Task                   | GUI path                                                                   | Scripted substitute                                                    |
| ---------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Linear spatial default | Settings (Preferences) > General > Default Spatial Interpolation to Linear | keys made by script already have zero tangents                         |
| Arc handles            | Pen tool or Convert Vertex on a key in the Composition panel               | `setSpatialTangentsAtKey(k, inTangent, outTangent)`                    |
| Separate Dimensions    | Right-click Position > Separate Dimensions                                 | `position.dimensionsSeparated = true`, `getSeparationFollower(0 or 1)` |
| Rove Across Time       | Right-click a key > Rove Across Time                                       | `setRovingAtKey(k, true)` on keys 2 to n-1                             |
| Hold a pose            | Animation > Toggle Hold Keyframe (Cmd+Option+H, Ctrl+Alt+H)                | `setInterpolationTypeAtKey(k, BEZIER, HOLD)`                           |

## Structure and motion blur

| Task                              | GUI path                                                                                                                                     | Scripted substitute                                                                                    |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Parent without moving             | Pick whip in the Parent column                                                                                                               | `child.parent = ctrlNull`                                                                              |
| Parent and jump into parent space | Shift while pick-whipping                                                                                                                    | `child.setParentWithJump(ctrlNull)`                                                                    |
| New null                          | Layer > New > Null Object (Cmd+Option+Shift+Y, Ctrl+Alt+Shift+Y)                                                                             | `AEK.build.nullLayer(c, name)`                                                                         |
| Motion blur switches              | Timeline: layer Motion Blur switch, comp Enable Motion Blur button                                                                           | `layer.motionBlur = true`, `comp.motionBlur = true`                                                    |
| Shutter angle and phase           | Composition > Composition Settings > Advanced                                                                                                | `comp.shutterAngle`, `comp.shutterPhase`, `motionBlurSamplesPerFrame`, `motionBlurAdaptiveSampleLimit` |
| Onion skin                        | Precompose (Cmd+Shift+C, Ctrl+Shift+C), Effect > Time > Echo: 30 echoes, decay 0.95, Echo Operator Composite In Front (7pOCtlrrE3Y 00:03:28) | `AEK.build.precompose` then `ADBE Echo`                                                                |
| Snapshot compare                  | Composition panel: Take Snapshot (Shift+F5), Show Snapshot (F5)                                                                              | save two PNGs with `AEK.capture.frames`, contact sheet                                                 |
| Contact sheet of spacing          | none native                                                                                                                                  | `ae.py sheet out.jpg frames...`                                                                        |
