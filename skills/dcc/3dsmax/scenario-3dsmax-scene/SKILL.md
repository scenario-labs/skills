---
name: scenario-3dsmax-scene
description: "Use when setting up, cleaning or organizing a 3ds Max scene: system units and scale, wrong scale after import or merge, Units Mismatch dialog, objects far from the origin, camera jitter or flipped normals, layers and naming, Box001 and Object237 names, nested groups, Scene Explorer, instance versus copy versus reference, XRef scenes and XRef objects, containers, proxies, missing maps or missing textures, Asset Tracking, relink or collect files, the file is too big, scene is slow or the viewport is laggy, CAD, DWG, Revit, SketchUp or FBX import and link cleanup, a client file from several freelancers, Gaussian splats (PLY, SPZ, LCC), point objects and Point Instance, or what changed for scene work in 3ds Max 2025 to 2027.3."
license: MIT
---

# Scene Assembly in 3ds Max

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit.

Expert level here means a scene a team can open, measure and render anywhere: one system unit, work
near the origin, every node named and on a layer, repeats shared as instances or references, heavy
parts split into referenced files, and zero missing assets, all proven by an audit before and after.
Audit first, change on a versioned copy inside one undo record, and never fix scale by changing
units under existing geometry.

If a sibling skill named here is missing from your available skills, load it with `skill_get`
(Scenario MCP) or ask the user to install it (https://github.com/scenario-labs/skills#install);
unattended, proceed from tool schemas and flag the gap.

**REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit, current-3ds-Max
traps).

## Stance (the expert delta)

1. **System units are chosen once, before geometry; display units are free.** The same box reads 3
   ft, 40 ft or over 200,000 ft depending on the system unit (Autodesk, aPc02tZzj8c 04:49). Changing
   it under a populated scene rescales nothing correctly. Fix a wrong file by merging it into a
   correct template, which rescales it (P3).
2. **Distance from the origin is a bug, not a location.** Round-off grows with distance: camera
   twitching, viewport clipping and flipped normals while relative geometry is untouched
   (aPc02tZzj8c 08:04; System Unit Setup doc). Keep significant detail above one system unit, and
   move the whole site with one stored offset.
3. **File weight follows face count, not object size.** A 161,735-polygon vase outweighs the table
   under it (Master ArchViz, SRVCuw9aPI8 01:20). Rank nodes by faces before deciding anything.
4. **Instances, proxies and XRefs lighten the file and the viewport, not the render.** One test went
   from 331,973 KB to 147,649 KB with instances and 54,861 KB with proxies, while render time rose
   from 8m49s to 9m26s and 11m31s (SRVCuw9aPI8, single runs). Promise a lighter scene, never a
   faster render.
5. **Link what will change; import what is frozen.** Revit through Link FBX with Combine By Revit
   Material gave 49 objects against 384, and a client change becomes Reload (CGI Made Simple,
   cv7bIWciFU4 04:31). Combine cannot change on reload. Bind only when the design is frozen.
6. **Split by discipline and keep the master empty.** Interior and exterior as XRef scenes, lights
   and cameras in a master that carries no polygons, automatic update off (Jake Denham, 2Nqp9n95pzE
   02:12, 02:46). Finalize layout first: XRef scene content cannot be selected or moved.
7. **Order layers by importance, then verify by hiding.** Numbered layers sort technical first and
   decoration last (`100_cams` ... `600_dec`); hide a layer after filling it to spot leftovers
   (render.camp, FYRj1pCBQq8 05:17, 09:20). The scheme is one studio's logic; a team keeps one
   standard.
8. **Splats are points with attributes.** Classic modifiers deform them non-destructively; convert
   to Editable Point only for per-point edits; only Arnold renders them today (Eloi Andaluz,
   YB330UhrdOA 01:08 to 02:14).

## Establish first

- Deliverable and team: who opens the file, how many people edit at once, render farm or single
  machine.
- Project system unit and display unit. Default when unanswered: centimeters for archviz interiors;
  match the source tool for CAD or SketchUp intake (millimeters in sQiA1X4XlMw). Autodesk suggested
  feet for Revit or FBX interchange in 2014 (aPc02tZzj8c 04:13); treat that as context, not a rule.
- Renderer in use (`rt.renderers.current`): it decides proxies, map classes and splat rendering.
- Source types: `.max` from others, DWG, RVT, FBX, SKP, PLY, SPZ, LCC, GLB from generation.
- Will the source change again? Yes means link or XRef; no means import, combine, bind.
- 3ds Max release: 2027.1 changed unit handling on load and merge; 2027.2 added splats and points;
  2027.3 added the splat viewport shader and the Autodesk 3ds Max MCP server.
- Channel from `max_env.doctor()`. Heavy client files go to `batch`; a live artist session gets
  read-only checks through `mcp-safe` first.

## Procedure

Full code, channels and checks: [procedures.md](references/procedures.md). Runner helpers:
`scripts/scene_run.py` (wraps `scripts/maxkit_scene.py` with the lead's `max_wrap`),
`scripts/scene_gate.py` (pass or fail on the audit JSON), `scripts/mxs/scene_audit.ms` (read-only
twin for `mcp-safe`).

1. **Protect and audit (P1).** Goal: facts before changes. How: copy the client file to a work
   folder, with Safe Scene Script Execution on; run `scene_run.py audit <scene> <out>` in `batch`,
   or propose `scene_audit.ms` in a live session; add the lead's `audit.all()` and
   `stats.snapshot()`. GATE: JSON saved with units, far nodes, group depth, default names, layer 0
   count, top faces, copy groups, missing maps, XRef files; the batch log lists missing plug-ins and
   XRefs.
2. **Template and units (P2, P3).** Goal: one system unit. How: set units on an empty scene, save a
   template, merge the client file into it with `ignoreFileUnits:false`, merge by layer when only
   part is needed (2027). GATE: `units_report()` matches the spec; three known dimensions (door,
   worktop, ceiling) within 1 cm [added tolerance].
3. **Origin (P4).** Goal: work near 0,0,0. How: `recenter()` dry run, then apply on the versioned
   copy; move the link helper for linked CAD or Revit. GATE: `far_count == 0`, measured from
   bounding-box centers, never pivots; offset stored on `REF_SiteOrigin`; animated nodes and
   isolated outliers listed for a human.
4. **Structure (P5).** Goal: flat groups, real names, numbered layers, unit scale. How:
   `flatten_groups()` records each group path, then explodes; `apply_layers()`; `rename_nodes()`
   refuses clashes; `reset_scale()` on every geometry node off (1,1,1). GATE: group depth at most 1,
   zero default names, zero nodes on layer 0, zero unexplained scale offenders; hide-each-layer
   captures show no strays.
5. **Repeats (P6).** Goal: one base object per repeated mesh. How: `copy_candidates()`, read the
   sample, `instance_copies()`. Reference where the top of the stack must differ. GATE:
   `removable_bases` drops to 0 for the accepted groups; file size measured after saving; a test
   render matches.
6. **Assets (P7).** Goal: zero missing files on every machine. How: `relink_maps()` to unique
   same-name files only; collect with the Resource Collector or `archiveMAXFile`. GATE: zero missing
   maps in the audit and in Asset Tracking; ambiguous matches reported to the user.
7. **Split (P8).** Goal: one owner per file. How: `split_to_xref()` per discipline; master holds
   lights, cameras, environment and render settings. GATE: every XRef file exists; master face count
   near zero; master render equals the pre-split render.
8. **Viewport (P9).** Goal: an interactive viewport, same render. How: delete what no camera, shadow
   or reflection sees (shot list first), smoothing viewport iterations 0, instances, attach static
   small parts, hide or freeze layers, proxies for heavy non-hero props, scatter instead of
   hand-placed rocks. GATE: `stats.diff` before and after; same-view captures; redraw time measured
   in a live session.
9. **Intake (P10, P11).** Goal: CAD, BIM, SketchUp, FBX and splats arrive light and at scale. How:
   link through Manage Links (GUI) when the source lives on, choosing Combine Entities at link time;
   otherwise `importFile` with the doc-confirmed importer class, then audit counts, lights and open
   shapes; splats through `PLYImport`, `SPZImport` or `LCCImport`. GATE: object count fits the
   combine choice; no flood of unique lights; closed CAD outlines; splat bounding box plausible in
   meters; renderer supports splats before a render is promised.
10. **Save and verify (P12).** Goal: proof. How: save `<name>_v00N.max` (never over the source),
    reopen fresh in `batch`, rerun P1, `scene_gate.py`, four captures as a contact sheet. GATE:
    every blocking gate passes; captures show nothing missing, no holes from exploded groups, no
    gray hero objects.

## Numbers

| Value                         | Relative to                                                         | Source                                              |
| ----------------------------- | ------------------------------------------------------------------- | --------------------------------------------------- |
| Detail above 1 system unit    | Smallest significant feature                                        | System Unit Setup doc                               |
| 1 km from origin              | Far-node flag in centimeter archviz scenes                          | [added] default; check with the accuracy calculator |
| 49 vs 384 objects             | Revit link By Material vs Do Not Combine                            | cv7bIWciFU4 04:31, frame                            |
| 10 segments, 15 degrees       | File Link Curved Objects Detail, Auto-Smooth angle (off by default) | File Link settings doc                              |
| 331,973 / 147,649 / 54,861 KB | Original / instances / proxies, one scene                           | SRVCuw9aPI8 frame                                   |
| 8m49s / 9m26s / 11m31s        | Render: original / instances / proxies, single runs                 | SRVCuw9aPI8 frame                                   |
| 5,000 faces                   | V-Ray proxy preview faces used                                      | SRVCuw9aPI8 06:31                                   |
| 0 viewport, 1 to 2 render     | TurboSmooth iterations; render only near camera                     | hz07nIgm7EA 00:16:18, 00:49:47                      |
| 3 GB                          | Scene bloated by hand-placed dense rocks                            | hz07nIgm7EA 00:14:29                                |
| About 5x                      | Array to points plus Point Instance vs mesh Array, small arrays     | YB330UhrdOA 06:39                                   |
| 30                            | Multi/Sub-Object samples shown (was 10), 2027.1                     | What's New 2027.1                                   |

## Quality gates

Measurable (rubric and thresholds: [critique.md](references/critique.md)):

- `scene_gate.py` blocking gates: system unit equals spec, no node beyond the far limit, zero
  missing maps, zero broken XRef files.
- Warnings to clear or justify: default names, duplicate names, group depth above 1, nodes on layer
  0, layer names off convention, copy groups not instanced, viewport smoothing above 0, faces per
  node above the project budget.
- Before and after `stats.diff`: objects, faces, unique meshes, file size (read after saving).

Visual (captures through the lead's `capture`):

- Four views plus each key camera: nothing missing, no misplaced furniture, no hole where a group
  exploded.
- Hide-each-layer sheet: leftovers visible on the wrong layer.
- Far-origin fix: camera playback or two frames show no jitter or z-fighting.
- Splats: shader view and an Arnold test render agree in color and scale.

## Common mistakes

| Mistake                                          | Symptom                                            | Fix                                                                |
| ------------------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------------ |
| Changing system units to "fix" a wrong import    | Everything else rescales wrongly                   | Undo; merge into a correct template (P3)                           |
| Scaling an object without Reset XForm            | Modifiers, noise, bump and UVs act in scaled space | Reset XForm after scaling (hz07nIgm7EA 00:21:31); modeling sibling |
| CAD left at survey coordinates                   | Jitter, clipping, flipped normals                  | P4, move the link helper                                           |
| Do Not Combine on a large Revit link             | Hundreds of objects, slow viewport                 | Relink By Revit Material or By Category                            |
| Revit FBX with lights                            | Every light instance unique, slow scene            | Lights off in the link; light in 3ds Max                           |
| Proxies sold as a render speedup                 | Render got slower                                  | Measure render time; proxies are for RAM and viewport              |
| Checking file size before saving                 | No change seen                                     | Save, then read size (SRVCuw9aPI8 03:37)                           |
| XRef auto update on                              | Session slows on every save of the source          | Manual Update Now                                                  |
| Removing a missing map to silence a warning      | Material loses its look                            | Relink or report; never remove                                     |
| Instance edited without warning                  | Every copy changes                                 | Check instances first; Make Unique only on purpose                 |
| Hidden exterior kept in an interior scene        | Slow viewport, heavy file                          | Separate scene, XRef if needed                                     |
| Layers hidden or frozen for speed, then rendered | Objects missing from the render                    | Hide and Freeze affect final rendering; restore or confirm each    |
| Far test on pivots                               | CAD 12 km out passes the audit                     | Bounding-box center (`origin_report()`)                            |
| `matchPattern` with `[0-9]` for default names    | Wrong counts                                       | Python `re` or `findString ... useRegex:true` (2027.2)             |
| Splat expected in V-Ray or Corona render         | Splat missing from render                          | Arnold today, or a mesh or capture alternative                     |

## Handoffs

- Receives from scenario-3dsmax-generation: generated GLB props, textures and splat worlds at
  arbitrary scale and origin; this skill normalizes unit, origin, naming and layers at import.
- Receives from scenario-3dsmax-scripting: batch runners for many files; this skill supplies the
  audit and gates per file.
- Delivers to scenario-3dsmax-modeling: Reset XForm and stack collapse on scaled pieces, CAD
  outlines to extrude, Boolean cleanup.
- Delivers to scenario-3dsmax-materials: missing or duplicate materials, flat-color maps, unused
  Multi/Sub-Object materials, name conflicts, Scene Converter work, renderer switch.
- Delivers to scenario-3dsmax-archviz: proxies, Forest Pack, RailClone and Chaos Scatter placement,
  Cosmos assets, client revision rounds.
- Delivers to scenario-3dsmax-lighting-rendering: the master scene for lights, cameras, test renders
  and splat rendering.
- Delivers to scenario-3dsmax-game-assets: clean, unit-correct assets for FBX, glTF or Datasmith
  export.
- Animated nodes skipped by P4 go to scenario-3dsmax-animation-rigging.

## Current 3ds Max notes

Checked against the team's version-delta table and the saved What's New pages.

- A `maxstart.max` with other units raises the Units Mismatch dialog at each start, which blocks
  renders started by Autodesk Assistant or an external client: align its units with the project (MCP
  known limitations, 2027.3).
- Open questions: the default system unit and the Units Setup menu path of a fresh 2027.3 install
  (the saved unit page is the 2017 help); whether containers, Populate and Civil View are still
  supported.
- 2025: OpenColorIO is the default color management for new scenes; older scenes keep their setup.
  Global Search and the Menu Editor changed.
- 2026: Return to stack position per object; Create panel search; Boolean, Array, Conform and
  Displace faster (retest old performance rules before applying them).
- 2027: `mergeMAXFile` takes `layers:` and `mergeNodesByLayer:`; `getMaxFileObjects` returns layer,
  group and class per node. Viewport grid and backgrounds refreshed. DirectX 9 removed.
- 2027.1: Preferences > Files holds Respect System Units in Files plus separate rules for scene
  load, merge, XRef Object and XRef Scene. Scripts read them with
  `maxOps.GetSceneFileUnitHandlingBehavior()` and `maxOps.GetMergeUnitHandlingDefaultBehavior()`;
  `loadMaxFile` and `mergeMAXFile` take `ignoreFileUnits:`. Before 2027.1 the single option sits in
  the System Unit Setup dialog (documented on the older help page).
- 2027.2: Gaussian Splat import (PLY, SPZ, LCC), Points objects, Point Select, Turn to Point, Point
  Instance, Array output to points; `findString` takes `useRegex:`.
- 2027.3: splat viewport shader (Display: Off by default), 4DGS sequences, PLY export and import
  segmentation, Point Grid and Point from Mesh, Khronos glTF importer and exporter built in, Mesh
  Cleaner Dead Vertices, faster Save To Previous with instanced Edit Poly, and the Autodesk 3ds Max
  MCP server (Tech Preview, not available in batch). Through `mcp-safe`, file delete and copy are
  blocked and modal dialogs stall the session; whether `importFile`, `mergeMAXFile` and saves pass
  is not documented: test on a copy, otherwise use `batch` or `handoff`. The glTF exporter flattens
  hierarchies and drops mesh vertex colors.

## References

- [references/procedures.md](references/procedures.md): P1 to P12 with full code, channels, source
  lines and what to check.
- [references/critique.md](references/critique.md): self-review rubric, thresholds and what to look
  for in captures.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with video ids and
  timestamps.
- [references/gui-paths.md](references/gui-paths.md): menus, dialogs and settings for the same
  steps.
- [references/sources.md](references/sources.md): every source with URL, credential and best
  timestamps.
- [scripts/maxkit_scene.py](scripts/maxkit_scene.py), [scripts/scene_run.py](scripts/scene_run.py),
  [scripts/scene_gate.py](scripts/scene_gate.py),
  [scripts/mxs/scene_audit.ms](scripts/mxs/scene_audit.ms).
