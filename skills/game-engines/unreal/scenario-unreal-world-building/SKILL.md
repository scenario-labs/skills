---
name: scenario-unreal-world-building
description: 'Use when building or fixing an Unreal Engine 5 level or open world: World Partition, OFPA, Data Layers, Level Instances, Packed Level Actors, HLOD, landscape size, heightmap import or clipping, edit layers, terrain material rules, foliage and grass, a PCG forest or rock scatter, runtime GPU grass, Nanite and tessellation choices, modular kits, a river or village, streaming pop-in, cells not loading, landscape black spots, "PCG shows nothing in the editor", a world too heavy to hand to lighting, or repeated geometry (pillars, posts, fences, walls with gates) that must come out with the right count and positions, built as instanced meshes and audited from the level, by Python or through Epic''s MCP scene, actor, primitive and PCG toolsets.'
license: MIT
---

# Unreal world building (levels, open worlds, landscape, PCG)

Expert level here means a world sized by rule, placed by tier of importance, streamed and budgeted
from the first map, and changed by script region by region, never by hand-selecting thousands of
actors. The environment artist decides what stays manual, what is baked and what is generated at
runtime, then proves every choice with a count, a trace or a screenshot. Target: UE 5.8 on macOS
Apple Silicon. If a sibling skill named here is missing from your available skills, ask the user to
install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool
schemas and flag the gap.

**REQUIRED BACKGROUND:** scenario-unreal-expert (channels, review loop, 5.8 traps). Toolkit:
[`scripts/ue_world.py`](scripts/ue_world.py)
(`sys.path[:0] = ["<skills>/scenario-unreal-world-building/scripts", "<skills>/scenario-unreal-expert/scripts"]; import ue_world as W`)
with `ue_run`, `ue_review`, `ue_audit`, `ue_stat`. A written plan names the engine call behind each
`W.*` step (procedures P0 table). Epic's in-editor PCG skills and InstantLevelOperations skill, read
through `ToolsetRegistry.AgentSkillToolset`, agree on scripted graph building; where they assume
more, the 5.8.3 runs decide (see "Epic's PCG skills, checked").

**Status (2026-10-21):** what ran in Unreal and what did not:
[`references/sources.md`](references/sources.md).

## Stance (the expert delta)

- **Start from the integrated setup, then measure.** File > New Level > Open World gives World
  Partition, OFPA, Data Layers, HLOD and outdoor lighting: "just use the template" (Sam Deiter,
  EEf07ggFWRw [00:20:40]). One runtime grid: more grids "can negatively impact performance" (World
  Partition doc). WP and OFPA from day one (Sam Dark, AalP65lrtpo [00:19:20]).
- **Place by tier of importance.** Hero assets and key areas by hand; shrubs to trees and rocks
  pre-baked; only grass-class detail generated at runtime on the GPU (CD Projekt RED and Epic,
  icIFFlOyob4 [00:04:23]-[00:07:05]). Collision and far visibility force persistent placement
  (Unreal Sensei, 5ju7wyvZGBI [00:54:16]). Decide what stays manual first (Matt Oztalay, TbNZ4GKaTow
  [00:32:26]).
- **PCG is authored like materials.** Template graphs with parameters, Graph Instances per use
  (Oztalay [00:12:18]); Is Partitioned is "pretty mandatory" [00:22:34]. Output inherits the PCG
  actor's Data Layer and HLOD Layer: assign them before generating (PCG doc). Grids: unbounded for
  parameters, 128 m for landscape reads, 32 m for scatter; every CPU to GPU transfer costs; layer
  weights do not exist on the GPU (icIFFlOyob4 [00:08:04] [00:23:16] [00:24:12]). Pop-in is
  generation latency, judged in Test builds [00:27:10] [00:27:44]. Bad data must be loud: Warn on
  Data Missing Attribute (Oztalay frame 00:10:47).
- **A landscape is sized, not picked.** Valid sizes (2017, 4033, never 2048), at most 1024
  components, 2x2 sections, edit layers (Landscape doc). Z scale and actor Z come from the exported
  heights (Z = span / 512, actor at the midpoint), never a declared relief: 250 m on paper reached
  314 m and clipped 123,356 pixels in our GREEN test [added]. The material contract, built by
  scenario-unreal-materials, is checked here: Opaque with Opacity Mask wired, one LB Alpha Blend
  base, a Layer Info per name (Landscape doc); triplanar only on the steep layer, anti-tiling on
  large layers, low specular (Sensei [00:11:12]-[00:15:36]).
- **Nanite by default, construction still matters.** "Enabled wherever possible" (Nanite doc), but
  porous kitbashes, hard-edge splits, seams and noisy vertex colors stop simplification: 250 MB vs
  12 MB, same look (Epic, 6igUsOp8FdA [00:02:46]-[00:08:04]). Distance culling does not apply to
  Nanite (Nanite doc). Tessellation has no collision: per layer, center 0.5 on ground, 1 on vertical
  rock; dicing rate 2 [00:22:58] [00:29:53].
- **Streaming structure follows content.** One HLOD layer per family: Instancing for foliage, Merged
  Mesh for buildings, Simplified when merged is still heavy (doc; Deiter [00:41:13]). Level Instance
  when content changes with gameplay, Packed Level Actor for static sets [00:30:59]. Runtime Data
  Layers only for gameplay state (doc). Teleport targets need a Streaming Source and, for runtime
  PCG, a generation source (doc; icIFFlOyob4 [00:36:44]).
- **World-scale work is scripted, regional and validated.** Scripts, never Outliner select-and-drag;
  whole-map jobs as builder commandlets region by region (Dark [00:20:23] [00:20:55]). Builders
  generate, then HLODs; generated actors stay out of changelists (Oztalay [00:26:23] [00:29:07]).
  Rules that documents only request become validators (Dark [00:23:04]).
- **Kits are commitments.** Footprint is the maximum extent, pivots frozen, standard door widths,
  core pieces first, hero last (Burgess and Purkeypile, QBAM27YbKZg [00:06:14] [00:07:51]
  [00:22:34]). Village paths join the nearest built path (Oztalay [00:20:01]); fences follow a
  spline grammar [00:18:51].

## Repeated geometry and the audit (run on 5.8.3)

Most build errors are arithmetic (11 pillars for 12, a wall half its length): plan the numbers,
build, read the level back, compare.

- **Numbers on the host:** `W.ring_layout(n, radius, centre)`, `W.line_layout(n, start, end)`,
  `W.wall_with_gate(length, gate_width, gate_centre)` (segments plus gate equal the wall).
- **One instanced component per repeated mesh,** never N actors. MCP: an `Actor`, `add_component`
  `InstancedStaticMeshComponent`, `set_properties` `StaticMesh` and `PerInstanceSMData` as matrices,
  `[{"transform": {"xPlane": {"x": sx, "y": 0, "z": 0, "w": 0}, "yPlane": {...sy...}, "zPlane": {...sz...}, "wPlane": {"x": tx, "y": ty, "z": tz, "w": 1}}}]`
  (`W.ism_matrix`), local to the component. A `{"Transform": {"Translation"...}}` form changes
  nothing. **A write that grows the array leaves its last new entry at the actor origin with the
  count still right: write the same array twice** (W1). Python: `W.add_instanced_mesh` (no such
  trap).
- **Audit from the level:** read `PerInstanceSMData` (or `W.instance_positions`) and run
  `W.position_audit(expected, actual, tol)` plus `W.count_audit(brief, W.level_counts(...))`; walls
  from component location and scale (the engine cube is 100 cm). `get_actor_bounds` includes a
  phantom 256 cm box at an empty root: never audit with it. `find_actors` `name` matches label
  substrings.

## Establish first

| Input                                    | Changes                                                 | Default when silent                                                     |
| ---------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------- |
| Platform, frame budget                   | Nanite, foliage path, layers; PCG time, grass density   | PC and consoles, Nanite on, 60 fps (scenario-unreal-performance)        |
| Size, quad size, height source           | layout, Z scale, actor Z                                | `W.plan_landscape`, 1 m quads; Z fitted to the heights                  |
| Fastest traversal, teleports             | loading range, streaming and generation sources         | ask gameplay; recorded as unknown                                       |
| Terrain features, Experimental tolerance | Landscape vs Mesh Terrain; Nanite Foliage, PVE, FastGeo | Landscape; no Experimental feature for shipping                         |
| Manual vs procedural, source control     | graph scope, who commits generated PCG                  | hand: village layout, river, roads, hero areas; builders own generation |

## Workflow

**MCP first:** actors, instanced meshes, primitives, tags, folders, PCG graphs and every read-back
go through the toolsets with the JSON in
[`references/mcp-world-building.md`](references/mcp-world-building.md); four or more toolset calls
in a row go through ONE `ProgrammaticToolset.execute_tool_script` script (define `run()`, call
`execute_tool(name, json_string)`, return a dict; imports json, math, re, time, datetime, copy
only), as its W1 to W4 scripts do (36 calls for all nine recipes). A failing tool aborts the script
and cannot be caught inside it: keep expected failures as single calls, and read results that need
editor ticks (PCG output, navmesh) in the next call. Level and map creation, World Partition, Data
Layer, HLOD and nav helpers go through editor Python (`import ue_world as W`; code in
[`references/procedures.md`](references/procedures.md), P-numbers).

1. **Brief as a world spec** (P1), like `W.U1_EXAMPLE_SPEC`; `W.probe()` once per install. GATE:
   `W.check_world_spec(spec)["ok"]`, info findings answered.
2. **Map** (P2). `W.new_open_world_map(path)` from `/Engine/Maps/Templates/OpenWorld` (run on
   5.8.3); old levels through `W.convert_args(..., report_only=True)` first. GATE:
   `W.wp_facts_check(W.world_facts())` clean; PIE screenshot with
   `wp.Runtime.ToggleDrawRuntimeHash2D`.
3. **Terrain** (P3, P4). DCC heightmap or the blockout `W.valley_heightmap`; `W.export_heightmap`
   fits Z and actor Z to the real range. Creation is one Landscape mode step (Location Z =
   `actor_z_cm`, Scale Z = `z_scale`) (the 5.8.3 MCP catalog has no landscape tool). Edit layers
   Base, Sculpt Details, Paint, Splines, Patches. River (Water Body River or a Splines-layer spline)
   before heavy painting. Then the landscape builder. GATE: `W.heightmap_clip_gate` empty (0 clipped
   pixels) before import; `W.landscape_facts()` matches plan, scale and location;
   `W.landscape_material_check` clean; Layer Debug, cliff close-up, grass in sun, mannequin at 2, 10
   and 100 m.
4. **Organization** (P5, P6). Editor Data Layers per family; HLOD layers from `W.hlod_plan`;
   Streaming Source components at teleport targets. GATE: `W.data_layer_check`, `W.hlod_actor_check`
   clean.
5. **Village and kits** (P7, P7b). Repeated pieces as instanced components, audited (section above).
   `W.kit_piece_check`, `W.door_width_check`; houses as Level Instances or Packed Level Actors;
   clutter as tagged assemblies (`W.tag_actors`); paths by `W.village_paths` into landscape splines;
   fences by grammar strings. Version the map before breaking an instance. GATE: no kit errors; no
   z-fighting or obvious repetition from the paths.
6. **Nanite** (P8). `W.nanite_construction_check(W.obj_construction_stats(obj))` on DCC exports;
   `W.batch_nanite(paths, dry_run=True)`, read, run; `W.tessellation_check` with per-layer centers.
   GATE: no translucent Nanite mesh; Overdraw over the canopy; feet on displaced ground.
7. **Baked PCG: forest and rocks** (P9). Template graph (layer filter warning on missing data, slope
   density, Extents Modifier into Difference for paths, Distance thinning at banks, understory
   differenced against trees, Self Pruning, species table, collision on trunks only), checked by
   `W.pcg_graph_lint`; `W.spawn_pcg_volume(..., hlod_layer=, data_layer=)`. Debug one volume (D)
   first. GATE: `W.pcg_component_check` clean; counts against `W.expected_points`; top-down and
   gameplay-height shots, nothing on paths or curated areas.
8. **Runtime grass** (P10). `W.grass_rings()` (dense to 128 m on 32 m cells, sparse to 256 m on 128
   m cells, far edge recolored); mask from grass types without meshes through Generate Grass Maps; a
   placeholder in every asset array; editor viewport as generation source; landscape cache;
   `pcg.FrameTime` set. GATE: `W.runtime_grass_check` and `W.find_gpu_transfers` clean;
   `W.generation_lead_check` with latency measured on a Test build.
9. **Builds** (P11).
   `for name, args in W.build_pipeline(map, graphs): ue_run.run_commandlet(uproject, name, args)`:
   landscape, PCG, HLOD. GATE: exit 0 each; HLOD actors per layer counted; `W.changelist_check`,
   then submit from the editor.
10. **Review and handoff** (P12 to P14). `W.tour(...)` with `W.REVIEW_CONSOLE` passes,
    `ue_review.image_checks` on every shot, then look;
    `W.world_rules_check(W.world_census(), vocab)`; `W.budget_sheet`, `W.lighting_handoff`. GATE:
    critique rubric passes; nothing reported done without a capture.

## Numbers

| Value                   | Setting                                                 | Relative to / source                                                                   |
| ----------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Landscape 2 km          | 2017 x 2017, 63 quads, 2x2, 256 of max 1024 components  | 1 m quads (Landscape doc)                                                              |
| Z scale                 | span cm / 512 x 1.02; actor Z at the span midpoint      | 16-bit heights (doc); headroom [added]                                                 |
| Template grid           | cell 25,200 cm, range 76,800 cm                         | MainGrid RuntimePartitionLHGrid, run on 5.8.3 (the 5.1 talk said 25,600)               |
| PCG partition grid      | 25,600 cm                                               | PCG World Actor `partition_grid_size` (Oztalay frame 00:23:16; 5.8.3 default not read) |
| Hierarchical grids      | unbounded, 128 m, 32 m                                  | runtime grass (icIFFlOyob4 [00:08:39])                                                 |
| Grass rings             | dense to 128 m, sparse to 256 m                         | icIFFlOyob4 [00:15:30]                                                                 |
| Instances per 32 m cell | 10k to 20k fine                                         | base PS5, 5.6 demo [00:30:26]                                                          |
| `pcg.FrameTime`         | 5 ms default; 2 ms in the demo                          | 5.6 notes; base PS5 [00:26:24]                                                         |
| Height upload           | about 0.5 ms game thread per 32 m cell                  | base PS5 [00:24:12]                                                                    |
| Streamed instances      | 16 million hard limit                                   | Nanite doc                                                                             |
| Nanite construction     | 250 MB vs 12 MB, same look                              | 6igUsOp8FdA [00:02:46]                                                                 |
| Nanite Assemblies       | 5 to 10% of asset size; 200 to 1,000 wind bones         | aZr-mWAzoTg [00:07:13] [00:09:51]                                                      |
| Dicing rate             | 2; slower below 2 and above about 5 or 6                | 6igUsOp8FdA [00:29:53]                                                                 |
| Displacement center     | 0.5 ground, 1 vertical rock, per layer                  | collision surface [00:22:58]                                                           |
| Terrain specular        | 0.02 (Sensei); 0.5 as a cavity-driven ceiling (Cloward) | 5ju7wyvZGBI [00:11:12]; 0L5Azq6ugyo [00:01:19]                                         |
| Tick aggregation        | above 10 to 15 placed instances                         | Dark [00:23:04]                                                                        |
| Mobile landscape        | 3 layers, 16 samplers                                   | ES3.1 (doc)                                                                            |

## Quality gates

- **Measurable:** the workflow checks (all `W.*_check`, `heightmap_clip_gate`, `pcg_graph_lint`,
  `find_gpu_transfers`); `ue_audit` on imports; builders exit 0; `stat unit`, `stat gpu` per
  viewpoint; PCG time in Insights on a Test build; `-trace=WorldStreaming`; `wp.Runtime.HLOD 0/1`
  A/B.
- **Visual:** runtime hash overlay without failed cells; Layer Debug without black spots; HLOD
  silhouettes; pop-in on frame-by-frame video; nothing on paths. Full rubric:
  [`references/critique.md`](references/critique.md).

## Common mistakes

Full table: `references/critique.md`.

| Mistake                                             | What it looks like                   | Fix                                             |
| --------------------------------------------------- | ------------------------------------ | ----------------------------------------------- |
| Hand-placed repeats, count never read back          | 11 pillars for 12; one at the origin | instanced component, `position_audit`           |
| Z scale from a declared relief                      | plateaus and pits after import       | fitted export, `W.heightmap_clip_gate`          |
| 2048 heightmap                                      | import refuses or resamples          | 2017 or 4033                                    |
| All layers height-blended; layer without Layer Info | black patches; layer never paints    | base layer Alpha Blend; Layer Info, same name   |
| Second runtime grid                                 | streaming cost, no gain              | one grid, HLOD for distance                     |
| PCG volume without HLOD or Data Layer               | baked forest missing at distance     | assign both before generating                   |
| Layer weights in a GPU graph                        | empty grass mask                     | grass types without meshes, Generate Grass Maps |
| Cull or draw distance on Nanite                     | no thinning, rings do not hand over  | HLOD, generation radius per ring                |
| Select-all edits on a big map                       | editor stalls                        | `W.region_batch` or a builder                   |

## Epic's PCG skills, checked (run on 5.8.3)

- Scripted graph building in one `execute_tool_script`: agreed (W4). Native node names carry spaces
  ("Create Points Grid"); add a Static Mesh Spawner with `"{}"` and set its mesh on the selector
  object `GetNodeInfo` names.
- Primitive subgraphs and instant graphs need the PCGPrimitives plugin: off in a blank project,
  `ListAvailableSubgraphs` returns `[]`. Enabled, it lists the subgraphs and 13 instant graphs; ask
  before enabling it in someone's project.
- `RunPCGInstantGraph` returned ok with Error messages and still spawned an actor: read its messages
  and list the level.

## Handoffs

Receives meshes and heightmaps from scenario-unreal-pipeline-automation, landscape materials from
scenario-unreal-materials; delivers the map and `W.lighting_handoff` to
scenario-unreal-lighting-rendering, `W.budget_sheet` to scenario-unreal-performance. Details:
`references/procedures.md`, Handoffs.

## UE 5.8 notes

- New WP maps use the runtime hash with partitions (5.4): Python cannot read them on 5.8.3;
  `world_facts()` returns the RuntimeHashSet path, read `runtimePartitions`, then the `mainLayer`
  object's `cellSize` and `loadingRange` with `ObjectTools.get_properties` (run on 5.8.3). No
  `unreal.LevelInstanceSubsystem` in 5.8.3 Python.
- PCG on by default; PCG Python Data Processor, PCG Builder Volume; landscape cache opt-in since 5.6
  (runtime CPU reads fail without it).
- Edit layers mandatory (5.7); `landscape.ForceLayersFullUpdate` replaces `ForceLayersUpdate`;
  `WorldPartitionLandscapeBuilder` (5.7); water brushes force a global merge.
- HLOD: Build HLOD for Selection or Region, `bForceRayTracingFarField`, Custom HLOD actors (5.7);
  `HLODLayerType.MESH_APPROXIMATE` exists on 5.8.3 though the saved doc lists three types.
- Experimental: Mesh Terrain, Nanite Foliage, PVE, FastGeo, World Streaming Insights. Mac: Nanite
  and VSM Beta on M2 or newer; cook platform `Mac`.

## References

- [`references/expert-notes.md`](references/expert-notes.md): judgment by expert, with timestamps.
- `references/mcp-world-building.md`: intent table, signatures, W1 to W4 scripts run on 5.8.3,
  traps, Epic PCG skills checked.
- `references/procedures.md`: P0 to P14, full code, engine calls behind the toolkit, tests, status,
  handoffs.
- `references/critique.md`: the rubric for each gate, full common-mistakes table.
- [`references/gui-paths.md`](references/gui-paths.md): editor menus for every procedure.
- `references/sources.md`: sources, credentials, URLs, timestamps, revision history.
