# Critique: judge your own scene work

Use this after every stage and before reporting. Score each line pass, warn or fail. A fail on a
blocking line stops the handoff. Numbers come from `maxkit_scene.audit_scene()`, the lead's
`audit.all()` and `stats`, and `scripts/scene_gate.py`.

## 1. Blocking gates (fail stops the delivery)

| Check                        | Pass                                                                          | How to measure                                           |
| ---------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------- |
| System unit                  | Equals the project spec, type and scale                                       | `units_report()`                                         |
| Unit rules on load and merge | Recorded; the merge used rescale, not ignore                                  | `load_unit_behavior`, `merge_unit_behavior`; the P3 call |
| Far from origin              | No node beyond the agreed limit (1 km [added] default for centimeter archviz) | `origin_report()["far"]`                                 |
| Missing assets               | 0 missing maps, 0 missing splat files, 0 broken XRef files                    | `missing_maps_report()`, `xref_report()`, Asset Tracking |
| Client file untouched        | Source file hash or modified time unchanged; work saved as `_v00N`            | Runner-side check                                        |
| Known dimensions             | Three reference items within 1 cm [added tolerance]                           | Bounding boxes against the drawing                       |

## 2. Warnings (clear or justify in the report)

| Check                                 | Target                                                              | Why                                                                            |
| ------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Default names (`Box001`, `Object237`) | 0                                                                   | Nobody can find or script by them                                              |
| Duplicate names                       | 0                                                                   | Merge, XRef and scripts pick the wrong node                                    |
| Group nesting                         | Depth at most 1, ideally none                                       | Nested groups break selection and merges; Explode flattens (hLOkgefE0ts 00:57) |
| Nodes on layer 0                      | 0                                                                   | Unassigned content hides from layer logic                                      |
| Layer names                           | One studio convention, for example `^\d{3}_[a-z0-9_]+$`             | Sort order equals importance (FYRj1pCBQq8)                                     |
| Geometry scale not (1,1,1)            | 0, or listed with the reason                                        | Modifiers, noise and UVs act in scaled space (hz07nIgm7EA 00:21:31)            |
| Far test basis                        | Bounding-box center, not pivot                                      | CAD pivots often sit at 0,0,0 with geometry kilometers out                     |
| Layers hidden or frozen for speed     | Each one listed; restored or confirmed absent before a render       | Hide and Freeze affect final rendering (display performance doc)               |
| Copy groups not instanced             | 0, or listed with the reason (different stacks)                     | File and viewport weight (SRVCuw9aPI8)                                         |
| Viewport smoothing                    | Iterations 0 in viewport                                            | Top viewport killer (hz07nIgm7EA 00:16:18)                                     |
| Heaviest nodes                        | Each above the budget is a hero object, a proxy or a scatter source | File size follows faces (SRVCuw9aPI8 01:20)                                    |
| Lights after a Revit FBX link         | Few, intentional                                                    | FBX makes every light instance unique (file-link doc)                          |
| CAD outlines                          | All closed before extrusion                                         | Open shapes do not extrude cleanly (1pEqaqq8v_Y)                               |
| XRef update mode                      | Manual                                                              | Automatic slows the session (2Nqp9n95pzE 02:46)                                |
| Master scene faces                    | Near 0                                                              | The master holds only lights, cameras, settings (2Nqp9n95pzE 02:12)            |
| Splat Viewport Limit                  | Set on dense captures                                               | Viewport speed without touching the render                                     |

## 3. Before and after numbers to report

- Objects, geometry nodes, total faces, unique base objects (`stats.diff`).
- File size in MB, read after saving.
- Missing maps before and after, with what is still missing and who must supply it.
- Redraw time of one fixed view in a live session (`timestamp()` around `completeRedraw()`
  [verify]); batch has no viewport.
- Render time of one test camera, only if a render was run, with the sampling unchanged between
  runs. One run each is a hint, not a result (SRVCuw9aPI8 used single runs).

## 4. What to look for in captures

Use `capture.views()` and per-camera captures, then one contact sheet (`max_review.contact_sheet`).

- Top view: the whole project sits around the origin; no stray object far out (it shrinks everything
  else to a dot).
- Perspective and camera views: furniture where it was in the client draft; no hole where a group
  was exploded; no duplicate stacked copies (z-fighting flicker in two captures one frame apart).
- Gray objects in a textured scene: missing maps or a renderer mismatch; a gray viewport model is
  not proof of a missing texture, check the audit first (hz07nIgm7EA 01:24:37).
- Hide-each-layer sheet: the layer's content disappears completely; what stays visible is on the
  wrong layer.
- After recentering: the same camera frames the same content as before; camera playback shows no
  jitter.
- After instancing: a before and after capture of the same view is identical.
- Splats: Display set to Shader shows true color and correct up axis; ground plane level; scale
  against a known object (a door, a person proxy).

## 5. Honesty checks for the report

- Every code block that ran says which channel and whether it returned `ok`. Nothing is called
  "tested in 3ds Max" unless it ran there.
- Every number in the report comes from a result JSON or a measured file, with its unit.
- GUI-only steps (Manage Links presets, XRef update mode, Adaptive Degradation, Units Mismatch
  choice when prompts are on) are listed as done by a person or a computer-use agent, with the path
  from [gui-paths.md](gui-paths.md).
- Animated nodes skipped by the recenter, ambiguous map matches and names that could not be derived
  are listed, not hidden.
