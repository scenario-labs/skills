# scenario-unreal-vfx and Epic's in-editor Niagara and Dataflow skills

Unreal 5.8 ships Agent Skills inside the editor. Read them through
`ToolsetRegistry.AgentSkillToolset`: `ListSkills` once, then
`GetSkills {"skillPaths": ["<path from ListSkills>"]}` for the one the task needs. Their text is
Epic's: read it there, this file only says how it fits with `scenario-unreal-vfx`. Compared on
2026-10-21 against the 5.8.3 install; facts marked "run on 5.8.3" were tested with
`tests/code/unreal-vfx/live_mcp_recipes.py`.

| Epic skill                   | Read it first when                                                                                                                | What scenario-unreal-vfx adds                                                                                    |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| NiagaraFundamentalsSkill     | editing any stack: module order, namespaces, linked parameter paths, coordinate spaces, collision, random ranges, material basics | gameplay truth (radius from gameplay), timing plan, capture review, budgets                                      |
| NiagaraRenderersSkill        | choosing or wiring a renderer, flipbook SubUV wiring, dynamic material parameters, visibility tags, sort mode                     | value and color rules, premultiplied flipbooks, strobing                                                         |
| NiagaraOptimizationSkill     | sim target, emitter consolidation, bounds modes, Effect Type axes, pooling, Require Current Frame Data                            | per-thread numbers by source (Kiraly), lever check per thread, budget oscillation, NDC and stateless spawn table |
| NiagaraBlueprintInteropSkill | spawning from Blueprints, binding User parameters, pooling on the spawn node                                                      | `set_user_params` typed by the system's declaration, gameplay handoff                                            |
| NiagaraCleanupSkill          | removing unused modules, parameters, Data Interface initializers                                                                  | nothing: follow it, and confirm with the user before removing                                                    |
| NiagaraCustomHLSLSkill       | writing an HLSL expression input                                                                                                  | R9 compile check                                                                                                 |
| NiagaraLevelPlacementSkill   | the user asks to put an existing effect in a level                                                                                | nothing: follow it (search, present, wait for a pick; do not author unless asked)                                |
| DataflowGraphEditingSkill    | editing a Dataflow graph node by node (its node catalog is large; read only the part you need)                                    | destruction recipe: pattern by material, levels, damage model, removal, `harden_gc`                              |

## Contradictions, tested

| Epic text says                                                                        | 5.8.3 did                                                                                                                                                                                                   | What scenario-unreal-vfx teaches                                                               |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Stack errors surface only with the Niagara editor open (Fundamentals, "Verify State") | `GetStackIssues` returned the GPU plus Light renderer error, and `ApplyStackIssueFix` fixed it, in a headless editor with no asset editor open; it refuses only while a compile is in flight (run on 5.8.3) | check issues in a headless editor, never a commandlet, after `bIsCompiling` turns false        |
| Pass the bare parameter name, no `User.` prefix (BlueprintInterop)                    | from Python and MCP, "Radius" and "User.Radius" both reached the same parameter (run on 5.8.3); Blueprint nodes were not tested                                                                             | either form in Python and MCP; bare name in Blueprints, as Epic says                           |
| A wrong-type set is a silent no-op (BlueprintInterop)                                 | from Python and MCP it is silent but not a no-op: it adds a stray override of the wrong type under that name (run on 5.8.3)                                                                                 | read `GetUserVariables` back; `set_user_params` refuses unknown names and types by declaration |

## Duplicates (kept short in scenario-unreal-vfx, pointing here)

- CPU vs GPU and the CPU-only renderers: Epic's Optimization and Renderers skills cover the rules;
  the Light renderer forcing CPU was confirmed live (R2). scenario-unreal-vfx keeps only "small
  counts stay on CPU" and the per-thread measurement.
- Bounds modes and Require Current Frame Data: Epic's Optimization skill; scenario-unreal-vfx keeps
  `fixed_bounds_check` (speed x lifetime for world-space trails).
- Pooling: both agree (auto release for fire-and-forget, manual when gameplay owns the lifetime;
  pooling below a spawn rate costs more than it saves).
- Effect Types: both. Epic adds a rule scenario-unreal-vfx now follows: an Effect Type is a shared
  asset, so list the existing ones and ask before creating a new one.

## Gaps Epic's skills fill (read them instead of guessing)

Stack order (forces, collision, then one velocity solve), namespaces and linked-parameter paths,
World Space as the default, Position vs Vector for world anchors, hue shift needing a non-white
base, GPU depth-buffer collision self-hits, SubUV wiring and Renderer Info Data Interfaces,
visibility tags vs the Meshes array, sort mode None, Dataflow node catalog.

## Gaps scenario-unreal-vfx fills

Gameplay-driven radius and timing, value and color budget, strobing, capture series with clean
plates and a scored rubric, per-thread budgets at the target core count, budget oscillation, Chaos
destruction recipe and cost order, Effect Type presets with numbers, and the MCP call shapes in
`mcp-niagara.md`.

## Limits

- Epic's Fundamentals skill says the Niagara toolset does not handle Lightweight Emitters or Data
  Channels; not tested here. Use templates or the GUI and say so.
- Epic's Fundamentals and LevelPlacement skills name `/NiagaraToolsets/` as a template folder; on
  5.8.3 the templates used here came from `/Niagara/DefaultAssets/Templates/`, and
  `NiagaraToolset_Assets.GetAssetDiscoveryInfo` returned an empty list. Search both.
