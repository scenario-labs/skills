---
name: scenario-unreal-materials
description: 'Use when a UE5 task involves materials or textures: a master material and instances for a kit, Substrate or legacy, Blendable vs Adaptive GBuffer, glass, emissive screens, decals, edge wear and dirt, landscape layers and RVT, toon or cel shading, "too many shaders" or shader permutations, static switches, usage flags, texture compression (BC7, normal maps, ORM packing, sRGB), texture memory, or "is this material expensive". Also when a material compiles headless but renders the default material, a texture parameter breaks the compile, a Substrate material renders black, or MaterialTools and MaterialInstanceTools calls need their exact arguments.'
license: MIT
---

# Unreal materials (master materials, Substrate, textures, shader cost)

Expert level means a few master materials whose instances cover the kit, a known and budgeted
permutation count, a compile proven in a rendering process, cost proven in milliseconds on a fixed
camera, and physically plausible values before any artistic push. The graph is authored once
(scripted build or template); everything else is instances, Custom Primitive Data and textures that
follow a role policy. Instruction counts and a pretty preview are hints, not proof. If a sibling
skill named here is missing from your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.

**REQUIRED BACKGROUND:** scenario-unreal-expert (channels, review loop, 5.8 traps). Read Epic's
in-editor MaterialBasics skill first, through `ToolsetRegistry.AgentSkillToolset` (reuse existing
materials and functions, instance before authoring, group parameters, neutral normal (0, 0, 1));
this skill adds what it does not cover.

**Status (2026-10-21):** what ran in Unreal and what did not:
[`references/sources.md`](references/sources.md).

## Stance (the expert delta)

- **Permutations = usage flags x unique static parameter sets actually used (x quality levels with a
  Quality Switch), never 2^switches.** Epic's MaterialBasics counts 2 switches as 4 shaders; that is
  the ceiling. Run on 5.8.3: an instance with only scalar, vector or texture overrides shares its
  parent's shaders (asset tag `HasStaticPermutationResource` False); any switch override forks it
  (True), even one set to the value the parent already has; `set_parameter_override(override=false)`
  and a save undo it. A parent usage flag adds a shader row to every unique child (Lauf and Nadro,
  Fortnite [wobQ8ZKQpbc 00:24:25, 00:05:32]); parents carry the fewest flags, instances opt in with
  Usage Flag Overrides (`MaterialEditingLibrary.set_material_usage_override`, present in 5.8.3).
  Count the instances that would set a switch before adding it (`switch_ranking`).
- **A static switch should gate texture samples, or heavy math most instances skip.** Anything else
  is an If (parameter into A, 0.5 into B, A > B pin, never A == B), an Enum-bound scalar or a
  Channel Mask Parameter; the Static Component Mask Parameter is obsolete (Lauf [00:40:24, 00:40:56,
  00:42:35]).
- **A compile is proven only where shaders compile.** Under `-nullrhi` (headless editor, plain
  commandlet) `recompile` succeeds on a broken graph and statistics read 0 (run on 5.8.3). Prove it
  in an offscreen editor (MCP `recompile` then returns the compiler message) or a commandlet with
  `-AllowCommandletRendering` (`ue_run.run_python(..., render=True)`, about 26 s):
  `um.compile_check(material)` returns errors and instruction counts. Every texture parameter needs
  a default texture whose type matches its sampler (Normal: `FlatNormal`; Masks:
  `DefaultDiffuse_TC_Masks`; Color: `DefaultDiffuse`), or the master fails and the game draws the
  default material (run on 5.8.3; `um.default_texture_for`).
- **The instruction count is not cost.** Sine plus cosine read +2 but cost about 40 GCN cycles; a
  fetch waits about 200 (Swierad [y0QASid1v8w 00:20:57, 00:35:57]). Math independent of the fetch
  hides inside that wait [00:46:03]. Budget samples and transcendentals (`cost_census`), decide on
  ms at a fixed camera.
- **Read `r.Substrate` before choosing outputs.** In a legacy project (`r.Substrate` 0, the bare
  5.8.3 default) a Substrate slab, glass or kit compiles without error yet renders near black; with
  `r.Substrate=True` both kinds render (legacy graphs convert) and instruction counts rise about
  30%, glass about 2x (run on 5.8.3, offscreen captures, `live_builders_look.py`). With Substrate
  on, start from one slab (Morgan, Epic [SqPaL8HS_Lw 00:25:45]): a Slab or the Metalness helper, not
  a hand-added Substrate Shading Model node. **Blendable is a ceiling** for every platform, SM6
  included (5.7 article); **Adaptive falls back per platform** by itself and costs 20 to 80 B/px
  (663 MB at 4K), about +15% cook and forced DBuffer decals (Ben Cloward [P5I38f2O6W8 00:05:46,
  00:06:54]). `r.Substrate.ProjectGBufferFormat` reads 1 (Adaptive) when the ini is silent (run on
  5.8.3): set 0 explicitly for Blendable. Converting a material is one-way.
- **Metal next to paint is two slabs, not gray metallic** (gray reads as plaster, Ben [VrY_SSvWdQ4
  00:05:39]). With Use Parameter Blending a Horizontal Blend is near-lossless and one slab
  everywhere (Morgan [00:37:35]); "Mix exactly 0 or 1 evaluates one slab" holds only without it, on
  Adaptive [00:29:38]. Parameter blending on a Vertical Coat is lossy [00:38:08].
- **Detail comes from packing and tiling, not resolution.** Two samples per terrain layer (CR +
  NOH), a 2K game ceiling, compression by role, sRGB only on color, packed normals never as
  Normalmap, BC7 for unrelated channels (Ben [-UZlUUQSGgQ 00:12:36], [gjOO5g4cgng 00:11:02]; Sumo
  [SAr7oPKsgLE 00:29:20]). The importer does not know a packed mask: an ORM PNG lands sRGB,
  `TC_Default` (run on 5.8.3); read and fix the flags after every import
  (`audit_textures(apply=True)`). Memory truth is the Platforms panel and `listtextures` in a cooked
  build.
- **Glass:** Colored Transmittance only when tinted (Gray is cheaper), Surface Translucency Volume,
  Pixel Normal Offset for flat panes, slab Simple Volume with Transmittance-To-MFP (Ben [sf-K257zWh8
  00:01:39, 00:09:17]).
- **An RVT is a cache captured orthographically at time 0:** no Time, Panner, camera distance,
  parallax or MPC in the write pass; a page change redraws all its writers; each distinct RVT
  sampled has a large fixed cost (PrismaticaDev [RLEPA16QDRw 00:20:14, 00:11:59, 01:04:29]).
- **Per-actor variation through Custom Primitive Data reads 0 until set** (run on 5.8.3), not the
  parameter's default: design CPD scalars so 0 is the neutral look (offsets, "off" flags), as
  `build_screen` does.

## Establish first

| Input                    | What it changes                                                                                           | Default when silent                                   |
| ------------------------ | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Platforms and frame rate | GBuffer format (Blendable caps all), closures, samplers (16 on ES3.1)                                     | console 60 Hz and PC: Blendable, 1 closure            |
| Project Substrate state  | `r.Substrate` (MCP `SearchCVars`, or the ini, P1)                                                         | read it, never assume                                 |
| Style                    | PBR; Toon BSDF (per asset, experimental; `ToonProfile` asset); post-process EV cel                        | PBR                                                   |
| Architecture             | lean master or Material Layering System, by library size and projected permutations (`lauf_permutations`) | lean master, under 10 presets                         |
| World-wide values        | MPC: at most 2 per material; adding parameters recompiles every user                                      | one game-wide, one per level                          |
| Mesh types per family    | usage flags per mesh type                                                                                 | static + Nanite                                       |
| Texture sources          | packing, DirectX green, texel density, source size                                                        | ORM packed, DirectX, 2K                               |
| Budgets                  | samples, transcendentals, unique static sets, shaders, BasePass ms, texture pool                          | project decision; lint warns above 12 samples [added] |

## Workflow

**Channel.** Epic's toolsets first. Four or more toolset calls in a row go through one
`ProgrammaticToolset.execute_tool_script`:
[`references/mcp-materials.md`](references/mcp-materials.md) has each recipe as a script (a master
with parameters, instances: 1 call instead of 20 and 10); signatures stay for single calls. A
failing call ends a script, so keep expected failures outside. Full graphs, bulk audits and compile
statistics: Python ([`scripts/ue_materials.py`](scripts/ue_materials.py)). Compile checks run in an
offscreen editor.

0. **Probe and decide.** P0 `um.probe()` lists what 5.8 exposes; P1 reads `r.Substrate` and runs
   `um.choose_gbuffer_format(targets, needs)`, whose reasons state the ceiling and the fallback.
   GATE: the format decision written.
1. **Plan the family.** One master per domain and blend mode (surface, glass, screen, decals, UI,
   landscape) with its switches, presets, usage flags per mesh type, budgets, MPCs. GATE: every
   switch gates a texture and has a `switch_ranking` count.
2. **Textures** (P2): `pack_channels`, `import_textures`, `audit_textures(apply=True)`,
   `albedo_stats`. GATE: audit passes; resident size at most 2048; `lint_graph(g, textures=...)`
   finds no sampler mismatch; albedo sRGB 20 (50 rough) to 240, metals at least 180.
3. **Build masters** (P3, P4): `um.build_kit_surface` or a template: texture-gating switches, an If
   for the paint-mask source, Custom Primitive Data for per-actor wear and dirt, Specular = 0.5 x
   (1 - cavity) as specular occlusion. Substrate: the Metalness helper feeds a base slab, a
   bare-metal slab takes albedo 0 and a measured F0, a parameter-blended Horizontal Blend takes the
   wear mask. Decals: blend mode before domain, or the first compile fails (run on 5.8.3). GATE: no
   failed links; `lint_graph` free of fail and warn; `compile_check` ok in a rendering process; one
   closure.
4. **Instances** (P5, P6, P16): only `make_presets` sets static switches; children change values;
   Custom Primitive Data varies placed actors. GATE: unique sets at most the preset count;
   `HasStaticPermutationResource` True only on presets; `audit_instance_values_project` clean
   (dielectric F0 at most 0.08, metal albedo 0, Metallic 0 or 1).
5. **Usage flags and shaders** (P7): pin needs on instances, then clear the parent; auto usage off
   (`bAutomaticallySetMaterialUsageInEditorDefault` in `[/Script/Engine.RendererSettings]`, 5.8.3
   header); Used with Static Mesh off on decal, UI and Niagara-only materials (Nadro [00:18:38]);
   `shader_count` per root (an upper bound). 5.8 compiles only connected, non-zero outputs
   (`r.Material.UseShaderCompilationParameters` 1 on 5.8.3): deleting nodes to strip shaders is
   folklore. GATE: shaders within budget; no gray default material on any mesh type.
6. **Special families.** Screens: emissive calibrated with the lighter; TSR smearing on scrolling
   text gets the experimental Temporal Responsiveness node, masked, with
   `r.Velocity.TemporalResponsiveness.Supported=1` (0 by default on 5.8.3) and a small WPO on Nanite
   meshes. Decals (P14) end in Convert To Decal; overlapping DBuffer-expression decals do not blend;
   each receiver's Decal Response covers only the channels its decals write. Landscape P11, stylized
   P12 and P13, switch triage P8. GATE: [`references/critique.md`](references/critique.md) for the
   family.
7. **Cost A/B** (P9, live editor): fixed camera, `r.ScreenPercentage 100`, warm-up, CSV profile,
   medians of GPU and pass time, `cost_census` beside them. GATE: deltas within budget.
8. **Look review** (P10, P15): preset board under the level lighting, buffer visualizations,
   Substrate views (Window > Substrate first, Morgan [00:12:51]); `ue_review.review_images` before
   anyone looks. GATE: critique rubric passes.
9. **Cooked check and handoff** (P17): `listtextures`, `stat streaming` and `r.Streaming.PoolSize`
   (1000 on 5.8.3) through `texture_memory_findings`; hand over reports, captures, open items.

## Numbers

| Value                                                                                      | Relative to                               | Source                                                                    |
| ------------------------------------------------------------------------------------------ | ----------------------------------------- | ------------------------------------------------------------------------- |
| F0 = 0.08 x Specular: Specular 0.5 = F0 0.04, 1.0 = F0 0.08 (IOR about 1.79)               | legacy dielectric                         | `DielectricSpecularToF0`, 5.8.3 shader source; Ben [fePsD_8p9vM 00:12:09] |
| F0 under 0.02 (Specular under 0.25) is read as specular occlusion: F90 = saturate(50 x F0) | Schlick in BRDF.ush                       | 5.8.3 shader source                                                       |
| Dielectric F0 at most 0.08; gems, carbon fiber up to about 0.18                            | Substrate slab                            | Morgan [00:09:30]                                                         |
| Metal: albedo 0, F0 average at least 0.5 (doc) or 0.6 (Ben)                                | Substrate slab                            | Ben [a94Lpu1_4dg 00:16:16]                                                |
| Base color sRGB 20 to 240, floor 50 when rough; metals at least 180                        | 8-bit sRGB                                | Ben [fePsD_8p9vM 00:05:28, 00:22:48]                                      |
| Glass IOR 1.5, MFP thickness 0.02; frosted roughness 0.2 to 1                              | rough refraction on (`r.Refraction.Blur`) | Ben [sf-K257zWh8 00:11:02, 00:17:16]                                      |
| 10 shaders, 20 with Skeletal, 27 with Niagara mesh, 186 with every flag                    | one material, project-dependent           | Nadro [00:06:28, 00:07:05]                                                |
| Fetch about 200 cycles; sine about 20                                                      | AMD GCN ranking                           | Swierad                                                                   |
| BC1 2048 = 2.66 MiB with mips; BC3, BC5, BC7 double; BC6H one eighth of RGBA16F            | GPU memory                                | textures doc                                                              |

## Quality gates

- **Measurable:** `lint_graph` free of fail and warn; `compile_check` ok in a rendering process (or
  MCP `recompile` without error offscreen); census within presets; `audit_textures` and
  `audit_instance_values_project` pass; `shader_count` per root; BasePass, Translucency, DBuffer ms
  A/B; Substrate Material Count 1 on Blendable; cooked `texture_memory_findings` clean; no blank
  frame.
- **Visual** (`references/critique.md`): transitions read as two materials; wear on edges, dirt in
  cavities; no tiling from far; glass free of silhouette seams; screens neither clipped nor smeared;
  no gray fallback; toon bands stable under a sun sweep.

## Common mistakes

| Mistake                                                                        | What it looks like                                  | Fix                                           |
| ------------------------------------------------------------------------------ | --------------------------------------------------- | --------------------------------------------- |
| "It compiled" from a headless run                                              | default material in game, `get_statistics` all zero | offscreen `compile_check` or MCP `recompile`  |
| Texture parameter without a default, or the wrong type                         | master fails to compile                             | `default_texture_for(sampler)`                |
| Substrate graph in a legacy project (or the reverse)                           | near-black spheres with a highlight                 | read `r.Substrate` first                      |
| Budgeting pixel instructions                                                   | "under 200" passes, the frame is still slow         | samples and transcendentals, measured ms      |
| Switch for a UV channel, tint or mask channel                                  | a shader map per unique instance                    | If, Enum or Channel Mask                      |
| Switch override left "at default"                                              | instance still forks                                | `set_parameter_override(override=false)`      |
| Parent flag "just in case"; decal or UI material keeping Used with Static Mesh | every unique child compiles another row             | instance overrides, auto usage off            |
| Deleting nodes "to strip shaders"                                              | no change in 5.8                                    | check ListShaders                             |
| Gray metallic wear                                                             | chalky, plaster edges                               | two slabs, parameter-blended Horizontal Blend |
| Adaptive on a 60 Hz console game                                               | up to 5x GBuffer memory, forced DBuffer             | Blendable                                     |
| Packed ORM left as imported; packed NOH as Normalmap                           | shifted roughness, flat terrain                     | Masks or BC7, sRGB off                        |
| CPD parameter whose neutral value is not 0                                     | placed actors dark or off until scripted            | offsets with 0 neutral                        |
| Time, Panner or MPC in the RVT write pass                                      | frozen or stale pages                               | read pass or RVT Replace                      |
| Python setter on a misspelt parameter                                          | returns False, nothing changes                      | check the return, or MCP (an error)           |

## Handoffs

- **Receives:** textures from scenario-maya-lookdev, scenario-zbrush-paint-render,
  scenario-blender-texturing-shading or Substance (role suffixes, DirectX normals), or through
  scenario-unreal-pipeline-automation (Interchange); meshes with slots named by family; exposure
  targets from scenario-unreal-lighting-rendering.
- **Delivers:** to scenario-unreal-world-building, masters, presets and instances (paths,
  parameters, CPD indices), the landscape master, RVT writer rules, decals and receivers' Decal
  Response. To scenario-unreal-lighting-rendering, emissive and glass materials, Substrate state and
  GBuffer format, albedo in range. To scenario-unreal-vfx, Niagara materials (flag on the instance).
  To scenario-unreal-performance, census, lint, texture and cooked-memory reports. To
  scenario-unreal-pipeline-automation, `audit_rules()` and the permutation gate.

## UE 5.8 notes

- Run on 5.8.3: no `r.Substrate.MaxClosureCount` (use `r.Substrate.ClosuresPerPixel`,
  `ProjectClosuresPerPixel`); `MaterialEditingLibrary.get_expressions` and
  `get_material_function_used_textures` absent (`get_material_expressions` exists); Toon BSDF
  classes `MaterialExpressionSubstrateToonBSDF` and `ToonProfile` present; unattended `create_asset`
  on an existing path returns None unless `overwrite_existing=True`; the commandlet's asset registry
  misses `/Engine` content for `EditorAssetLibrary.load_asset` (use `unreal.load_asset`).
- Substrate is on for new projects from templates, Blendable by default (Adaptive in the Automotive
  and Architectural templates); upgraded and bare projects stay legacy. 5.8 adds EON rough diffuse,
  approximates F90 on Blendable, ships the experimental Toon BSDF.
- ListShaders and Total Shaders are upper bounds; ISMs need no flag on GPU Scene platforms. Older
  version notes: [`references/expert-notes.md`](references/expert-notes.md) (end).
- Mac: Adaptive needs SM6; the editor compiles for `SF_METAL_SM6`; advanced Substrate visualization
  is Win64 DX12 only.

## References

- `references/mcp-materials.md`: toolset intents, signatures, six live recipes with JSON, when to
  use Python.
- [`references/procedures.md`](references/procedures.md): P0 to P17 with full code, test path and
  status.
- `references/critique.md`: the self-review rubric per material family.
- `references/expert-notes.md`: principles and judgment by expert, with source and timestamp.
- [`references/gui-paths.md`](references/gui-paths.md): editors, menus and settings for a
  computer-use agent.
- `references/sources.md`: every source, URL, best timestamps, revision history.
- `scripts/ue_materials.py`: texture policy, value checks, cost census, graph lint, permutation
  census, Substrate ini, builders, compile check, cooked texture memory, probe.
