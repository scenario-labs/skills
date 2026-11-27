---
name: scenario-3dsmax-animation-rigging
description: "Use when animating or rigging in 3ds Max: keyframes by script, tangents, Curve Editor, camera walkthrough on a path, choppy or jerky camera, LookAt or Path constraint flips, part spins or flips when linked, Reset XForm before linking, bones and IK solvers, mechanical rig with pistons that come apart, excavator or linkage, collision between moving parts, Skin modifier, voxel or heat map weights, bad deformation at shoulders or fingers, skin transfer to a new rig, CAT or Biped, Morpher lip sync, wire parameters and custom attributes, Reaction Manager, animation layers, mocap cleanup, foot sliding, retarget animation to another skeleton, rigged character from a generator with odd bone names or wrong scale, export animation FBX to Unreal or Unity, bones missing from bind pose."
license: MIT
---

# 3ds Max animation and rigging

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit.

Expert level here means every rig is proven by numbers across its whole range: link lengths that
never drift, pistons that stay coaxial, feet that stay planted, weights that sum to one, an exported
clip that re-imports at the same height and length. The stance is to build controls apart from
geometry, solve the cheap automatic pass first, and spend the hand work on the last 5%. If a sibling
skill named here is missing from your available skills, load it with `skill_get` (Scenario MCP) or
ask the user to install it (https://github.com/scenario-labs/skills#install); unattended, proceed
from tool schemas and flag the gap. **REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels,
review loop, toolkit, current-3ds-Max traps).

## Stance (the expert delta)

1. **Reset XForm a part before a bone or child is linked to it.** A part that still carries a
   rotation or scale offset flips the moment it is linked (Lee Minardi, cm7OP3niwvI 00:06:46). Never
   Reset XForm a mesh that already has a Skin [added].
2. **LookAt Upnode follows the parent, not World.** With World, any out-of-plane motion spins
   pistons and pins. A LookAt cannot target the object that targets it: aim at another object that
   shares its pivot (cm7OP3niwvI 00:05:00, 00:08:17).
3. **Check the internal unit of what you drive.** Path percent is 0 to 1 internally while the panel
   shows 0 to 100, so a raw 0 to 100 wire jumps (Autodesk Learning Channel, ytW9dyEtxqc 00:07:21).
   Slider ranges are the real mechanical limits (door 170, window 90), so the control cannot break
   the model.
4. **Weight Solver first, hands last.** Voxel or Heatmap gives about 95%; fingers, head and neck
   take the rest by vertex (Kimn7CIZ5bI 00:04:10). Settings do nothing until Apply. Max Influence 0
   means 1 and -1 lets the solver decide in the current docs, contrary to the 2016 video.
5. **Never delete a Skin to change skeletons.** Extract the weights, add a Skin with only the new
   bones, then import and pair by name (Miloš Černý, G47NnPXsPHM 00:04:13). The import does nothing
   on a mesh without a Skin and bones.
6. **AI mocap gives timing and poses; contacts are your job.** Fix feet, then hands, then COM
   height, then timing with a Time Warp, then mix down (Norberto Aguilera, WUELGPaQu8o 00:03:04,
   00:39:21). Delete a sliding key and let Biped re-solve before touching handles.
7. **Layers, not destructive edits.** Corrections go on a named layer and are collapsed at the end
   (Simulation Lab, Pgzy2_HxH2w 00:50:10). In CAT an Absolute layer hides, not deletes, what is
   below; Local Weight 0 on one chain lets the lower layer through (0xKZ5hV4MK8 00:03:34).
8. **Smooth by spacing and tangents, not by more keys.** A choppy camera path needs Normalize Spline
   and Interpolation Steps raised to 200 (Arch Viz Artist, e3g4boZKyFU 00:03:56, 00:05:25). Constant
   speed needs linear tangents set before keying.

## Establish first

- **Release and channel.** 3ds Max 2027.3 by default. Run `max_env.doctor()`. Skin work needs the
  Modify panel, so it runs through `bridge` or `handoff`, not `batch`. Rig builds can go through
  `mcp-safe` as MAXScript.
- **Units and frame rate.** Run `maxkit_anim.units_report()`. Numbers here assume centimeters and
  the clip's authored rate. Set both before any key.
- **Subject.** Prop or mechanism: Bones, IK solvers and constraints. Creature or non-biped: CAT.
  Human with mocap or BIP: Biped (CAT is fine for humans) (Pgzy2_HxH2w 00:21:50).
- **Motion source.** Hand keys, procedural CATMotion cycle, AI video-to-mocap, optical mocap, a
  generated rigged character, or a library clip.
- **Deliverable.** Render in Max (camera, shot range) or engine clip (Unreal or Unity, FBX, in-place
  or root motion, influence limit). The sources give no Unreal root-bone or root-motion rule: ask
  the engine team, then prove it with one test import before batch export.
- **Third-party rigs.** SmartAnim, Anima or a studio rig may be installed; their scripting is
  unknown here. Ask before scripting them.

## Procedure

Full code for each stage is in [references/procedures.md](references/procedures.md) (P1 to P13).
Wrap Python chunks with `anim_wrap.wrap_anim`, MAXScript with `max_wrap.wrap(lang="maxscript")`, and
run `max_check.check` first.

**GUI-only steps:** every step with no script route (Weight Solver, finger and neck weights,
Walkthrough Assistant, CAT and Biped setup, Workbench, Mixer Time Warp, FBX checkboxes without a
known key) is handed over with its full menu path from
[references/gui-paths.md](references/gui-paths.md), never as "fix by hand". The section "GUI-only
steps" there lists them.

1. **Arrival check (P1).** Goal: know the skeleton, scale, bind pose, frame rate and clips before
   editing. How: `batch` import into an empty scene, `maxkit_anim.hierarchy()`, `height_report()`,
   `units_report()`, `capture.views()`. GATE: height within 5% of the expected size, one root, no
   bone with non-unit scale, no duplicate names, frame rate equal to the source, skeleton inside the
   mesh on the captures. A generated character goes back to `scenario-3dsmax-generation` when it
   fails on topology or missing skin; fix scale and names here.
2. **Plan the hierarchy and controls.** Goal: a written list of drivers, driven parts, constraints
   and limits before building. Name with side prefixes (`L_`, `R_`, `M_`), one master control,
   controls offset from the geometry (ThePolymonger, QRB-6wnDcPw 00:05:40). GATE: no circular
   reference in the plan; every driven part has exactly one driver.
3. **Build the rig.** Mechanism (P5): Reset XForm, bones pivot to pivot, HI solver, Dummy driver,
   LookAt pistons with the parent as Upnode. Eyes and aim controls (P4). Controls (P6): Attribute
   Holder, custom attributes, wires. Character: CAT or Biped through the GUI (gui-paths.md), Figure
   Mode to fit bones. LookAt that snaps on assignment: Keep Initial Offset, driven object picked
   first (QRB-6wnDcPw 00:06:40 to 00:07:48). GATE: P5 measures: drift under 0.01 units, piston
   `|dot|` above 0.9999, stroke in limits, no unconfirmed bounding-box hit.
4. **Skin (P7, P8).** Goal: clean deformation within the influence limit. How: Skin per mesh, Weight
   Solver pass in the GUI (Apply), scripted rigid weights, fingers and neck by hand in the Weight
   Table, DQ Skinning Toggle plus Blend Weights on twisting joints, `skin_report()`. GATE: zero
   unweighted vertices, zero over the limit, weights sum to 1, captures at extreme poses with no
   collapse at shoulders, elbows, knees, wrists or neck.
5. **Face (P9).** Two Morphers, phones on top, every channel keyed at each key time, neutral
   brackets. GATE: target vertex counts equal the base; no blink on a phone key frame; mouth
   captures at key frames.
6. **Animate (P2, P3, P12).** Keys in the animate context, tangents set before keying, ranges and
   out-of-range types set. GATE: `speed_profile()` step change under 5% for cameras, `loop_gap()`
   near zero for cycles, `contact_slide()` under 1 cm.
7. **Mocap and retarget (P10, P11).** Measure contacts first, clean in Biped in the order of stance
   rule 6, or constrain-and-bake between plain skeletons. GATE: P10 numbers, then a side-by-side
   contact sheet against the reference.
8. **Export (P13).** Skin file and clip files separately, bake when constraints or solvers drive the
   motion. In the FBX dialog: Convert Deforming Dummies to Bones on, Triangulate off (5M7jlvzGWQ4
   f_00192). GATE: P1 on each exported file matches the source in bone count, names, height within
   2% and frame range.

Every stage runs the lead's loop: inspect, plan, change inside one undo, verify with numbers and
captures. Judge with [references/critique.md](references/critique.md).

## Numbers

| Value                         | Number                                                  | Relative to                           |
| ----------------------------- | ------------------------------------------------------- | ------------------------------------- |
| Camera eye height             | 160 cm                                                  | floor, not Z=0 (e3g4boZKyFU)          |
| Path Interpolation Steps      | 16, then 200 if choppy                                  | spline object (e3g4boZKyFU)           |
| Slower walkthrough            | End Time 1400, last key moved to the end                | 30 fps scene (e3g4boZKyFU)            |
| Path percent internal range   | 0 to 1                                                  | wire expressions (ytW9dyEtxqc)        |
| Slider limits                 | door 0 to 170, window 0 to 90                           | the model's real limits (ytW9dyEtxqc) |
| Voxel solver start            | Falloff 0.2, Max Resolution 64, Max Influence 3, 4 or 6 | Skin Weight Solver (Kimn7CIZ5bI)      |
| Max Influence 0 / -1          | treated as 1 / solver decides                           | current docs                          |
| Abs. Effect                   | 1.0 = only that bone                                    | Skin vertex weight                    |
| Smooth test cylinder          | 20 height segments                                      | Skin doc example                      |
| Lip sync example              | ~150 frames, 5 s, blinks 16/18/20                       | 30 fps (MMHfDujrGwo)                  |
| LookAt weight (single target) | 50                                                      | frame 00:08:44 (cm7OP3niwvI)          |
| CAT hub defaults              | Length 25, Width 20, Height 10                          | CAT units (R5NmiXpqBsQ)               |
| Influence limit               | 4 per vertex                                            | common engine limit [added]           |
| Foot slide pass               | under 1 cm per contact                                  | cm scene [added]                      |
| Rigid link drift pass         | under 0.01 units                                        | system units [added]                  |

## Quality gates

Measurable:

- `maxkit_anim.hierarchy()`: one root, no non-unit scale, no duplicate names.
- `skin_report()`: `over_limit`, `unweighted`, `bad_sum` all 0.
- `pivot_distance_drift()`, `axis_alignment()`, `bbox_overlaps()` across the full range (P5).
- `speed_profile()`, `loop_gap()`, `contact_slide()` (P3, P10, P12).
- Export: re-imported bone count, names, height, frame range and rate equal the source.

Visual (`capture.viewport`, `capture.views`, `max_review.contact_sheet`):

- Extreme poses from front and side with Edged Faces: no pinching, no volume loss on twist.
- Mechanism at both limits of every driver and twisted out of plane: no spin, no gap at pins.
- Camera contact sheet every 50 frames: no jump, level horizon, no wall in frame.
- Mocap next to the reference video: feet planted, hands touching the floor plane, timing.

## Common mistakes

| Mistake                                       | Symptom                                     | Fix                                                                          |
| --------------------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------- |
| Linking a bone to a part with an XForm offset | Parts flip on link                          | Undo, Reset XForm the part, relink (P5)                                      |
| Upnode left on World                          | Pins spin when the arm twists               | Upnode = parent arm                                                          |
| Outer piston aims at inner                    | Circular reference refused                  | Aim at the link sharing the inner pivot                                      |
| Slider 0 to 100 wired to path percent         | Jerky motion                                | Range 0 to 1 or expression `/100`                                            |
| Closing the solver dialog                     | Weights unchanged                           | Click Apply                                                                  |
| Deleting Skin before transfer                 | Weights lost                                | Extract first (P8)                                                           |
| Skinned mesh with an animated parent          | Unexpected deformation                      | Unlink the mesh; parent the skeleton                                         |
| Expressions Morpher above phones              | Lip sync washed out                         | Move it below the phones Morpher                                             |
| Animation layers enabled on a mixed object    | Motion Mixer maps break                     | Regenerate the XMM maps                                                      |
| Exporting glTF for an animated character      | Skin or clip may be missing (docs disagree) | FBX (P13)                                                                    |
| Bake off with constraints or IK               | Engine clip frozen or wrong                 | Bake on (P13)                                                                |
| AI mocap stops before the video ends          | Clip ends early                             | Extend the trajectory, key two frames before the end                         |
| Moving a skinned mesh or its bones            | Envelopes lost                              | Save, Always Deform off, transform, on (Skin doc)                            |
| Linear skinning on a twisting forearm or neck | Candy-wrapper collapse                      | DQ Skinning Toggle, Blend Weights (Skin doc)                                 |
| Rescaling a skinned character after import    | Skin breaks                                 | Fix scale at import (P1); else ask for a re-export at the right unit         |
| Renaming bones on the only copy               | Maps or transfer break                      | Rename on a copy, rerun P1 and `skin_report()` (no sourced rename procedure) |
| One clip per max file for related cycles      | Clips drift apart                           | Keep walk, trot, run as CAT layers in one file (0xKZ5hV4MK8 00:04:05)        |

## Handoffs

- Receives from `scenario-3dsmax-generation`: rigged or animated characters (FBX or GLB) and meshes
  to rig. Run P1 on arrival; send topology, missing skin or broken mesh back with the P1 report.
- Receives from `scenario-3dsmax-modeling` and `scenario-3dsmax-game-assets`: meshes with clean
  pivots, T-pose, separate eyes, teeth and tongue.
- Receives from `scenario-3dsmax-scene`: units, layers and an imported CAD mechanism with its
  pivots.
- Delivers to `scenario-3dsmax-game-assets`: skinned mesh FBX and clip FBX for Unreal or Unity, with
  the P13 re-import report.
- Delivers to `scenario-3dsmax-archviz` and `scenario-3dsmax-lighting-rendering`: animated cameras
  and shot ranges.
- Delivers to `scenario-3dsmax-fx`: animated colliders and characters for tyFlow.
- Asks `scenario-3dsmax-scripting` for batch tools that run P1 or P13 over many files.
- Generated motion (text or video to motion, auto-rig) is requested through
  `scenario-3dsmax-generation`, which uses `scenario-3d`.

## Current 3ds Max notes

From the project's version-deltas table and the saved docs.

- 2027.3: native glTF import with Import Animation and "Match the animation range to the file"; its
  options have no documented script interface. The glTF export page says no animation, skin or
  morpher data leaves, while the what's new says animation is supported: export animated characters
  as FBX until checked.
- 2027.3: the Autodesk 3ds Max MCP server (Tech Preview) runs Safe MAXScript at level 10; it is not
  available in batch. Biped `scaleFootprints` through the MCP server or Assistant crashes 3ds Max:
  do it in the Biped UI.
- Custom attributes and script controllers are embedded scripts that Safe Scene Script Execution
  scans when a scene opens.
- 2027.3: Skin weight display no longer lags when switching bones. 2027.1: `skinOps.reloadIni()`.
  2027.2: `FBXExporterGetParam` and `FBXImporterGetParam` gained keywords, so read parameters back
  after setting them.
- 2026: Biped loads BIP files by exact name; MAXScript `#extraBonesNameMatch` keeps extra-bone
  animation. CAT motion-layer cloning and paste copy all subcomponents and keep footprints valid.
  Mesh and Skin evaluation is multithreaded.
- 2026.1: the XForm modifier has a new interface with modes; check Reset XForm results on first use
  [verify].
- CAT and Biped get fixes, not redesigns: 2010 to 2018 tutorials match the logic, not the UI.
  SmartAnim is listed for 2020 to 2026 only.
- Python 3.13.9 in 2027: `MaxPlus` is gone since 2022; pymxs on the main thread only.

## References

- [references/procedures.md](references/procedures.md): P1 to P13 with full code, channel, source
  line and checks.
- [references/expert-notes.md](references/expert-notes.md): principles and judgment by expert, with
  timestamps.
- [references/critique.md](references/critique.md): the rubric for judging a rig, a skin, a clip or
  an export.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for the same work; name these
  paths for every GUI-only step.
- [references/sources.md](references/sources.md): every source, what it is best for and its key
  timestamps.
- [scripts/maxkit_anim.py](scripts/maxkit_anim.py): measurement and bake helpers that run inside 3ds
  Max (contacts, drift, coaxiality, collisions, speed, loops, skin weights).
- [scripts/anim_wrap.py](scripts/anim_wrap.py): `wrap_anim(code, kit=[...])`, a thin call to the
  lead's `max_wrap.wrap` with `maxkit_anim` as a sibling kit.
