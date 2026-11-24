---
name: scenario-3dsmax-fx
description: "Use when doing FX or simulation in 3ds Max: tyFlow destruction, breaking a wall, fracture by impact, Voronoi debris, PhysX rigid bodies and glue binds, cloth drape on a bed or chair, cloth reveal, tearing, particles on a surface, scatter by texture, digging dirt or pouring sand, fire and smoke with tyFlow ZENITH or Inferno, tyCache or Alembic caches, rendering particles or volumes in Arnold or V-Ray, Hair and Fur that does not render, MassFX quick drops, or Phoenix questions. Also when a sim explodes, the wall falls on its own, debris looks like glass, cloth passes through the collider, the volume renders black, nothing renders, the cache will not load, or the sim is too slow."
license: MIT
---

# 3ds Max FX artist

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit.

**Status: not yet run in 3ds Max.** Nothing here has been executed in the application. Code is
checked against the cited documentation, and unconfirmed API names carry a bracketed `verify` mark:
confirm each in the live session first.

Expert FX work in 3ds Max is staging and gating, not one heavy solve: cheap stand-ins and tests
decide what simulates and when, detail arrives after a cache, and every look is judged on playback.
tyFlow is the main path; it is a third-party plugin whose event graph is built in its own editor, so
the agent prepares, specifies, measures and verifies, and hands graph wiring to a human or a
computer-use agent unless the installed build exposes more. If a sibling skill named here is missing
from your available skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit,
current-3ds-Max traps).

## Stance (the expert delta)

1. **Gate before you simulate.** Fracture particles stay out of PhysX until a Surface Test (distance
   to an activator proxy) sends them to the physics event; without the gate the wall collapses on
   its own. The test distance is the blast radius: 200 cm made a local hole, 700 cm dropped the
   whole wall (Jesse Pitela, GZMWapJe7eM 00:03:38, 00:17:47). CJ Aguilar holds pieces with PhysX
   Switch Kinematic until the test fires (U6pMAa2vckw, frames).
2. **One event per fracture tier.** Each tier is Voronoi Fracture + PhysX Shape + PhysX Collision; a
   Property Test (Velocity Magnitude 15, then 25; Radius 15) routes only fast or big pieces to the
   next tier. Each event has its own collider list: re-add the collider every time (GZMWapJe7eM
   00:07:09 to 00:12:50).
3. **Binds decide the look, and their stability.** Pure Voronoi reads as glass; Rigid (Glue) with a
   force break keeps some chunks whole. For degenerate glue the docs advise Rigid (Joint) with very
   high stiffness (millions are normal), Max breaks/frame 1 or 2, and more PhysX Position Iterations
   (physx-bind doc).
4. **Cheap first, detail after the cache.** Proxy colliders, low-res cloth, low displacement while
   testing. Cache the cheap fracture, reload it with Birth Flow, and Subdivide plus Displace only
   near the impact (U6pMAa2vckw frames).
5. **Cloth: time step before radius.** Fix collider penetration with time step 1/4 and time scale
   0.6 first (fabien escudero, Xf8q28fdRWk 00:01:50). Time step is the substep dial; Position
   Iterations are solver iterations, not substeps (physx-bind doc). Stiffness Solver Constrained
   keeps stiffness when step count changes (cloth-bind doc). When cloth resolution goes up, collide
   radius goes down; the docs put self-thickness below the minimum triangle spacing.
6. **Caches are formats, not files.** Particle Export caches load only in a tyCache object or Birth
   Flow; tyCache modifier caches only in a tyCache modifier (tycache doc). Re-import a baked Alembic
   before it feeds the next sim, or that sim is far slower (edstudios, tWhQLc5IDXQ 00:09:31).
7. **Render is a separate pipeline.** Particles need a Mesh operator in every rendered event
   (DokFcrFyln0 00:03:04). A ZENITH volume in Arnold needs a light, a first render to create its
   rollout, and a preset re-click after any display change (Svetlin Nikolov, d6Htujb3A0E).
8. **Tool status shapes the plan.** Phoenix is End-of-Support since April 2026 (frozen; inside V-Ray
   and Corona Premium and Collection only). ZENITH in tyFlow 2.x is the forward path for GPU fire
   and smoke. MassFX is a placement tool for archviz drops, not a hero solver (VizAcademy,
   TXTXLsDvCRo).

## Establish first

- **tyFlow build and license.** 2.x expected (2.101 of 2026-10-08 is the latest in the saved docs).
  FREE simulates everything including ZENITH; PRO is needed for ZENITH rendering, VDB export,
  advanced volume interfaces and full file I/O (faq-zenith doc). No tyFlow: say so and offer MassFX
  or keyframes.
- **GPU.** CUDA 12.8 minimum for tyFlow 2.x; the cloth CUDA collision solver and ZENITH need NVIDIA.
  Eloi Andaluz Fullà gives RTX with over 6 GB VRAM for ZENITH.
- **Units and scale.** Read them, never change them: Autodesk warns not to change the system unit in
  an existing scene. Recipe numbers here assume 1 unit = 1 cm; convert them otherwise.
- **Deliverable.** A still needs one good frame; a shot needs a stable cache, motion blur data and a
  frame range.
- **Renderer.** Arnold (bundled), V-Ray or Corona; it changes the volume and particle render path.
- **Channel.** `bridge` or `handoff` for pymxs; `mcp-safe` gets the MAXScript twins; `batch` for
  caching and renders that need no UI.
- **Phoenix installed?** Only matters for legacy scenes and ocean textures.

## Procedure

Full code, build sheets and result checks live in [procedures.md](references/procedures.md); menu
paths in [gui-paths.md](references/gui-paths.md).

1. **Inspect.** Run `maxkit_fx.fx_audit()` plus the lead's `stats.snapshot()`, wrapped by
   `scripts/fx_wrap.py` (`max_wrap` with `kit_dirs`). Run `maxkit_fx.discover()` on each tyFlow
   object to read what this build exposes. GATE: units, fps, range, renderer, light count and FX
   objects reported; no `error` findings left unexplained.
2. **Scale and stand-ins.** Build proxies: an activator box linked to the hero mover (Display as
   Box, not renderable), a ground plane, a closed cutter for voxel digging. Do it in one undo. GATE:
   proxy open-edge count 0; proxy face count under 5% of the hero mesh [added]; a capture shows the
   proxy covering the hero.
3. **Build the flow.** Write a build sheet (events, operators, values, connections) from the
   procedures.md recipes. A human or computer-use agent builds it in the tyFlow editor, or the agent
   loads a template. Script only what `discover()` proved exists. GATE: the editor capture matches
   the sheet event by event; every rendered event has a Mesh operator; pasted operators made unique
   before separate tuning.
4. **Preview and iterate.** Low resolution, short range, one variable per run. Check tiers with one
   display color per event, binds with Spline Paths (procedures 4a). Time a fresh pass with
   `maxkit_fx.time_evaluation()`, then extrapolate with `scripts/sim_budget.py estimate`. GATE:
   playback capture at the key frames passes [critique.md](references/critique.md); the budget
   estimate fits the deadline before raising resolution.
5. **Cache.** Particle Export to tyCache for flows; `cache()` on tyCache modifiers for meshes;
   Alembic for other apps. Save under new names, never over a loaded cache. GATE:
   `sim_budget.py cache` reports every frame present, no zero-byte file, size logged; the cache
   plays in a fresh scene without the live flow.
6. **Detail pass.** Second flow on the cache: Birth Flow, then a Surface Test near the impact, then
   Subdivide and Displace. Cap faces carry their own MatID. GATE: a capture shows extra detail only
   inside the test radius.
7. **Render.** Mesh operators with Instance material "inherit from object", materials (cap MatID for
   inner faces), lights. Motion blur needs subframe cache data (procedure 12). Render one low-res
   frame per key moment before the sequence. Hand render setup to
   scenario-3dsmax-lighting-rendering. GATE: frames are not black or empty; no gaps at colliders;
   render matches the viewport look.

## Numbers

| Item                              | Value                                                                             | Relative to                        |
| --------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------- |
| Wall Voronoi                      | 1,000 points, 100% variation                                                      | brick wall, cm scene (GZMWapJe7eM) |
| Activation distance               | 200 cm local, 700 cm whole wall                                                   | car about 400 cm                   |
| Glue force break                  | 15,000 then about 177,000 (heard)                                                 | tyFlow beta; retest on 2.x         |
| Tier tests                        | Velocity >= 15, > 25; Radius > 15                                                 | cm and cm per frame                |
| Tier Voronoi                      | 30 to 10 points; 5 points for big chunks                                          | per particle                       |
| Debris weight                     | friction 0.8/0.8, mass relative to volume: target 1000, exp 1.5, min 0.1, max 100 | PhysX Shape                        |
| Restitution, damping              | 0.15; 0.05                                                                        | PhysX Shape                        |
| Max breaks/frame                  | 1 or 2                                                                            | PhysX Bind doc                     |
| Joint bind                        | swing 100,000 / damping 250; twist 7,500 / 250                                    | U6pMAa2vckw frames                 |
| Cloth time step, time scale       | 1/4, 0.6                                                                          | chair collider                     |
| Cloth gravity                     | -0.1                                                                              | tyFlow Force, Xf8q28fdRWk          |
| Cloth radii without CUDA          | Collision 0.6; Particle Physics 0.4 to 0.145                                      | 200x200 plane, cm                  |
| Cloth folds                       | Turbulence 5 to 0 over 15 frames                                                  | settle                             |
| Shell on cloth                    | 0.04                                                                              | cm                                 |
| Reveal gate                       | Event Age > 90                                                                    | frames                             |
| Voxel dig                         | voxel size 5                                                                      | cm, excavator                      |
| Pebble collisions                 | bounce 0.15, friction 0.5/0.5                                                     | PhysX                              |
| ZENITH fire                       | normalized 5+; noise strength 5 to ignite                                         | 1 = room temp                      |
| Smoke from fire                   | emission by temperature 5 to 10                                                   | normalized                         |
| Hair and Fur rug                  | count 10,000 then 50,000; scale 20 to 30; root 5, tip 0                           | rug                                |
| ZENITH speed                      | 320 frames, 189 M voxels in 44 s                                                  | RTX 3080 (pjwGWsS3GIg)             |
| Particle Alembic                  | about 116 GB                                                                      | excavator debris                   |
| Sand pour count, radius, friction | none sourced                                                                      | tune by preview; report it         |
| Camera (AA) for motion blur       | 4 to 8                                                                            | Arnold doc; lower other samples    |

## Quality gates

Measurable:

- `fx_audit()` has no `error`; units and range match the build sheet.
- Proxies closed (open edges 0); final colliders are the hero (Hull Type Mesh or SDF).
- Fragment count per tier logged from the editor; no tier above the budget set in stage 4.
- Cache complete: frames present, sizes logged, reload in a fresh scene works.
- Seconds per frame measured; sim total within the deadline with a 1.5x margin. Visual (captures,
  contact sheet through `max_review.contact_sheet`):
- Destruction: fragments grow away from the impact; some whole chunks; nothing moves before contact;
  debris settles, not slides.
- Cloth: no penetration (capture from below and at grazing angle); folds at real cloth scale; no
  black backfaces.
- Volumes: fire turns to smoke at a plausible height; no collider gap; render matches the viewport
  shader.

## Common mistakes

| Mistake                               | Symptom                                     | Fix                                                           |
| ------------------------------------- | ------------------------------------------- | ------------------------------------------------------------- |
| No gate before PhysX                  | wall collapses at frame 0                   | Surface Test or PhysX Switch Kinematic upstream               |
| Collider not re-added                 | new tier passes through the car             | add the collider to each PhysX Collision                      |
| Uniform Voronoi                       | glass look                                  | Glue bind with force break; fewer points for big chunks       |
| High-res fracture artifacts           | slivers, bad caps                           | Voronoi "Weld after slicing" (slower)                         |
| Pasted tier still instanced           | tuning one tier changes another             | make unique first                                             |
| One Surface Test output               | grounded and airborne pieces share an event | switch the test's output side                                 |
| Grains overlap at birth               | pops at frame 1                             | Fuse operator radius before the solve                         |
| Glue degenerate                       | jitter, explosions                          | Joint with very high stiffness; raise Position Iterations     |
| One particle loses all binds          | single pieces pop out                       | Max breaks/frame 1 or 2                                       |
| Hero mesh as collider                 | slow iteration                              | proxy box; swap at the end                                    |
| Thin part on the collider             | over-fracture (car antenna)                 | remove it or collide it separately                            |
| Cloth through chair                   | penetration                                 | time step 1/4, time scale 0.6, then radii                     |
| Collide radius kept after subdividing | cloth puffs or repels itself                | lower radius below vertex spacing                             |
| CUDA solver errors at seams           | pillow seams fail                           | Prevent coincident edges/faces, tiny threshold                |
| Open cutter mesh                      | voxel islands left                          | bridge edges on a copy; airtight cutter                       |
| No Mesh operator                      | nothing renders                             | Mesh operator in every rendered event                         |
| Mesh operator on default material     | cached debris loses materials               | Instance material "inherit from object"                       |
| Wrong cache loader                    | cache will not load                         | Particle Export to tyCache object; modifier cache to modifier |
| ZENITH in Arnold, no light            | black volume                                | add an Arnold Skydome light                                   |
| Edited Inferno Display                | render unchanged                            | re-click the shader preset, render again                      |
| Hair and Fur left on Buffer           | no hair in render                           | Effects entry, render mode Geometry                           |

## Handoffs

- Receives from scenario-3dsmax-scene: units, scale, layers; from scenario-3dsmax-modeling: wall or
  prop meshes, airtight cutters; from scenario-3dsmax-animation-rigging: keyed movers (car, wrecking
  ball pendulum, excavator).
- Delivers to scenario-3dsmax-lighting-rendering: tyCache or Alembic caches, Mesh-operator flows,
  volume shader presets, the motion blur state; to scenario-3dsmax-materials: cap MatID and shell
  MatIDs for inner materials; to scenario-3dsmax-scripting: batch cache jobs.
- scenario-3dsmax-generation supplies debris or hero meshes, concrete and cap-face PBR textures,
  HDRIs, and video restyles of a gray playblast. A generated mesh is raw input: it needs scale,
  closed colliders and cleanup before it enters a flow.
- scenario-3dsmax-game-assets takes flipbooks or vertex-animation exports for engines.

## Current 3ds Max notes

Checked against the version-delta file and the saved tyFlow and Chaos docs.

- tyFlow on 3ds Max 2027 needs 2.004 or later. 2.000 (2026-03-03) brought ZENITH, CUDA 12.8 minimum,
  SDF shapes for PhysX Shape and Collision, a MAXScript operator and subframe tyCache export for
  motion blur.
- Export operators are now Particle Export, Terrain Export, Inferno Export, VDB Export (renamed in
  2.009). Old tutorials say Export Particles.
- Arnold renders tyFlow volumes from 3ds Max 2027.1 (MAXtoA 5.9.2.0). On 2025 and 2026, export a VDB
  (tyFlow PRO) and render it as a volume instead.
- MAXtoA 5.9.5.0 (2027.3) can render a VDB as an implicit surface or points. MAXtoA 5.9.0 adds
  `scattering_mode` on standard hair.
- tyFlow 2.100 and 2.101: Inferno Export modes callable as `[op].exportVDB()`, `exportImages()`,
  `exportFlipbook`; splat import and export (Max 2027+); Property Test comparison fixes, so retest
  old thresholds.
- A tyFlow 2.004 fix restored PhysX bind stiffness after a 1.128 regression: bind numbers from older
  builds may not transfer.
- 3ds Max 2027.1 adds unit rules in Preferences > Files and `ignoreFileUnits:` on load and merge:
  check them before merging cached or simulated assets.
- Phoenix: final releases support 3ds Max 2027 and nothing later.
- Hair and Fur: mental ray Prim is gone; use the Geometry render mode [added].
- DirectX 9 is removed in 2027: viewport driver advice from old videos means Nitrous Direct3D 11.
- Safe MAXScript cannot overwrite a re-imported `.abc` cache, and an Arnold render can crash 3ds Max
  (MCP server limitations): write new names and save before rendering.

## References

- [expert-notes.md](references/expert-notes.md): principles and judgment by expert, with timestamps.
- [procedures.md](references/procedures.md): audit, discovery, proxies, build sheets for each
  recipe, timing, caching, render checks, with code.
- [critique.md](references/critique.md): self-review rubric with numbers and what to look for in
  captures.
- [gui-paths.md](references/gui-paths.md): menus, editor actions and rollouts for every GUI step.
- [sources.md](references/sources.md): every video and doc, what it is best for, best timestamps.
- [maxkit_fx.py](scripts/maxkit_fx.py) (inside 3ds Max), [fx_wrap.py](scripts/fx_wrap.py) and
  [sim_budget.py](scripts/sim_budget.py) (runner side).
