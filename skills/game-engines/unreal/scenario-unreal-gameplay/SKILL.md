---
name: scenario-unreal-gameplay
description: 'Use when building or debugging UE5 gameplay: a character with double jump or dash, abilities with cooldowns, enemy AI that patrols, chases and attacks, a health bar or HUD; Blueprint graphs through Epic''s MCP BlueprintTools DSL, UMG widgets, data tables, gameplay tags, Gameplay Effects, StateTree parameters, PIE and automation tests from an agent; choosing Blueprint vs C++, GAS or not, StateTree vs Behavior Tree; Enhanced Input, replication, save games; "Blueprints are slow", Tick, casts and hard references; "ability won''t activate", "enemy ignores the player"; or gameplay tests with injected input.'
license: MIT
---

# Unreal Gameplay (framework, Blueprint vs C++, input, GAS, AI, UI)

Expert level means every piece of data lives in the class whose lifetime and network presence match
it, logic is text (C++, or Blueprint DSL read back after writing) under data-only Blueprints that
scripts configure, and every mechanic is proven in isolation (injected input, debug commands,
traces) before it is judged in play. If a sibling skill named here is missing from your available
skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`);
unattended, proceed from tool schemas and flag the gap.

**REQUIRED BACKGROUND:** scenario-unreal-expert (channels, review loop, 5.8 traps). Read Epic's
in-editor BlueprintBasics skill (through `ToolsetRegistry.AgentSkillToolset`) before writing graphs.

**Status (2026-10-21):** what ran in Unreal and what did not:
[`references/sources.md`](references/sources.md).

## Stance (the expert delta)

- **Place data by lifetime and network presence.** GameMode is server-only rules; GameState and
  PlayerState replicate to all; PlayerController is owner-only; the Pawn is a respawnable body;
  GameInstance subsystems outlive maps (Forsythe IaU2Hue-ApI [00:13:26]). State goes in replicated
  properties with RepNotify, never multicast; C++ RepNotify does not fire on the server (JOJP0CvpB8w
  [00:10:50], [00:14:48]). Under World Partition BeginPlay can run several times: keep it idempotent
  (Shao KBn62trwkLw [00:07:29]).
- **C++ base, data-only Blueprint child; Blueprint may depend on C++, never the reverse** (Forsythe
  VMZftEVDuCE [00:24:10]). Tuning is `EditDefaultsOnly`, asset choices `TSubclassOf` slots,
  cosmetics `BlueprintImplementableEvent` hooks. Broadcasters fire one-way delegates (`OnDied`) that
  controllers, spawners and HUD bind ([00:19:25]). Small Blueprint logic is fine as DSL; profile
  before porting.
- **Blueprint cost is per node; the real cost is hard references.** Tick overhead is noise next to a
  CharacterMovement update; casting to a Blueprint class keeps it loaded with the caster
  (Arnbjornsson S2olUc9zcB8 [00:06:07], [00:28:01]). Move to C++ only what an Insights trace puts in
  the hot set (Forsythe [00:16:33]).
- **Effects are what, abilities are when.** New features are new reactive assets listening through
  tags; reactions query a GE's asset tags; one damage GE with SetByCaller; Wait Delay, not Delay;
  always End Ability; `PlayMontageAndWait`; Gameplay Cues cosmetic only (Shao 8bi0rnXnRj4
  [00:19:25], [00:47:35], [00:21:43], [00:49:12], [00:13:02]; tranek 9.3). Console isolation tests
  use a fixed-magnitude twin, since a SetByCaller value exists only when code sets it [added].
- **Wire the ASC on both sides.** On the pawn unless attributes survive respawn (then PlayerState);
  `InitAbilityActorInfo` on the server in `PossessedBy` and on the owning client in
  `AcknowledgePossession` (or `OnRep_PlayerState`); Mixed for players, Minimal for AI; never predict
  damage (tranek 4.1, 4.1.2, 7.3, 4.10).
- **Input is data with indirection.** Input Action to input tag to ability (Noland, Lyra Fj1zCsYydD8
  [00:34:33]); mapping contexts mutually exclusive per gameplay state.
- **StateTree selects a leaf before any transition and re-checks enter conditions only when a
  transition asks** (Mononen YEmq4kcblj4 [00:11:22]). Every condition that should end a state needs
  an event or a transition; every state gets explicit success and failure ways out ([00:14:13]);
  tuning as tree parameters ([00:16:40]); actions delegate to a Gameplay Ability with a timeout
  (Bruno XKQfMZOXFv0 [00:17:37]).
- **UI updates by events, never property bindings; Global Invalidation on, then hunt frozen
  widgets** (Albert VxX1aah6TZM [00:24:09]). Widget Tick runs from Paint; Hidden repaints where
  Collapsed relayouts ([00:10:09], [00:12:53]).

## Establish first

| Input                                             | Why it changes the plan                                                                          | Default when silent                                                                                       |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| Single player or multiplayer, listen or dedicated | ASC placement, replication mode, prediction, test matrix                                         | single player, authority checks from day one                                                              |
| C++ toolchain                                     | Xcode 26.6 built a 5.8.3 code project (run); Epic lists 26.1.1 as recommended, 26.4 incompatible | C++ when Xcode is present; else Blueprint DSL plus data                                                   |
| Channel                                           | an open editor with Epic's MCP, or none                                                          | MCP toolsets for assets and graphs, headless jobs for bulk and audits                                     |
| Scale                                             | tens of actors vs hundreds of interactables vs thousands of movers                               | actors; Instanced Actors, then Mass (KBn62trwkLw [00:01:06])                                              |
| Feel targets                                      | jump height, dash distance, cooldown, speeds                                                     | ask; untouched CharacterMovement defaults "feel like an Unreal tutorial project" (IaU2Hue-ApI [00:23:39]) |
| Character and level inputs                        | skeleton, montages, notifies; nav bounds, player starts                                          | from scenario-unreal-animation and scenario-unreal-world-building                                         |

## Authoring surfaces (run on 5.8.3)

- **Epic MCP first** for Blueprints (`BlueprintTools`: create, variables, functions,
  `write_graph_dsl`, compile), widgets (`UMGToolSet`), data tables, gameplay tags, automation tests,
  PIE start and stop, and any property Python refuses (`ObjectTools.set_properties`). Four or more
  toolset calls in a row go through one `ProgrammaticToolset.execute_tool_script` (recipes 1, 2, 3,
  8 and 9 of [`references/mcp-gameplay.md`](references/mcp-gameplay.md); recipe 9 is a pickup with
  components, overlap, cast, int variables and DestroyActor, with node ids and pins that work).
  Argument JSON, traps, signatures: same file; do not `describe_toolset` (BlueprintTools alone is
  about 26k tokens).
- **Python** (headless `ue_run.run_python`, or the Python toolset next to MCP) for Blueprint
  children and CDO defaults, Enhanced Input with modifiers, widget trees, CSV tables, audits,
  console commands and `Input.+key` injection, and creating GE and StateTree assets. Epic's toolsets
  have no console tool.
- **Hybrid steps:** GE tag components and modifiers, StateTree parameters and PIE player count are
  writable only through `ObjectTools`; the helpers return the exact calls (`rep["object_tools"]`,
  `configure_play`, `state_tree_parameter_values`).
- **No API found:** states and transitions of a new StateTree. Duplicate a template tree (the
  engine's Combat, Shooter, SideScroller and TwinStick variants ship them) or do one GUI pass from
  the spec.

## Workflow

1. **Probe once per engine.** `job_00_gameplay_probe.py` (headless, about 35 s): classes,
   properties, Python names, cvars. GATE: `probe.json`; every `PROBE_CLASSES` entry true.
2. **Decide.** `ue_gameplay.decide(spec)`: data placement, Blueprint vs C++, GAS or not, AI system,
   ASC placement, replication, UI. GATE: every datum has owner, replication and survival (respawn,
   map change, streaming).
3. **Scaffold project and config.** `ue_env.enable_plugins`; tags through
   `GameplayTagsToolset.AddTag` (always pass `comment` and `tagSource: "DefaultGameplayTags.ini"`)
   or `add_gameplay_tags_ini`;
   `AbilitySystem.Fix.GameplayEffects.ReturnAssetTagsViaGetOwnedGameplayTags=0` under
   `[ConsoleVariables]` (default 2). GATE: `config_verdict` clean.
4. **C++ layer.** `cpp_scaffold()`, `patch_build_cs()` (adds the modules and
   `PublicIncludePaths.Add(ModuleDirectory)`, without which every scaffold include fails),
   `build_command()` with the editor closed. GATE: UBT exit 0; `cpp_lint` without errors.
5. **Data layer.** Blueprint children and defaults (`set_defaults`: `{"class"}`, `{"asset"}`,
   `{"soft"}` slots), movement, `JumpMaxCount`, every AI pawn's `ai_controller_class` = the
   controller Blueprint holding the tree, `auto_possess_ai` placed or spawned; `apply_input_plan`;
   GE assets then their `object_tools` calls; widgets. GATE: `ge_plan_verdict`, `audit_gameplay()`,
   `ai_setup_verdict` clean.
6. **Graphs.** Small logic: `BlueprintTools` DSL, then `read_graph_dsl` and `compile_blueprint`.
   Trees: spec checked by `statetree_spec_verdict`, template duplicated, parameters per enemy. GATE:
   Blueprints compile with `warnings_as_errors`; read-back matches intent.
7. **Test in isolation, then the chain.** Fixed-magnitude GE from the console
   (`AbilitySystem.Effect.Apply`), `showdebug abilitysystem`, the gameplay debugger on each AI,
   `gas_log_triage`; then `pie_scenario` (latent job, or `start_on_tick` in a running editor) and
   Python tests run by `AutomationTestToolset.RunTests`, judged by analyzers with thresholds derived
   from the parameters (`analyze_jump`, `dash_expected_cm`, `analyze_cooldown`,
   `state_sequence_verdict`, `health_bar_verdict`). GATE: every scenario passes; no stuck ability;
   no unplanned root entry.
8. **Persist and check from disk.** `AssetTools.save_assets` before stopping the editor; a headless
   job that reloads and asserts the values. GATE: the reload agrees.
9. **Evidence and measure.** Screenshots (offscreen editor), `stat game`, `dumpticks`
   (`tick_verdict`), `stat slate` with Global Invalidation off and on, an Insights trace before any
   rewrite (`rewrite_gate`). GATE: tick census justified; rewrites only for hot-set functions.

## Live traps (run on 5.8.3)

- Object refs need the object path: `/Game/X/BP.BP`, not `/Game/X/BP`. A Blueprint's graph is
  `/Game/X/BP.BP:GraphName`; a Blueprint-added component template is `...BP_C:Name_GEN_VARIABLE`.
- A new Actor Blueprint holds unconnected BeginPlay, `Collision|EventActorBeginOverlap` and Tick
  nodes: write into them, do not add duplicates.
- DSL: another Blueprint's members are `Class|BPHero|GetCoins` (`:self` the cast result). Function
  names resolve across Blueprints: name them uniquely. Pass pins by keyword on member calls (a
  positional literal binds to `self` and is lost); an unknown pin errors with the real pin list; a
  type mismatch silently inserts a conversion; `read_graph_dsl` output is not always valid input;
  the bool `bUsed` getter is `Variables|Default|GetUsed`; widget getters appear only after
  `ToggleWidgetAsVariable` and a compile; `remove_variable` turns getters into literal 0 and still
  compiles.
- Python names differ from C++: `AbilitySystemLibrary`, `GameplayTagLibrary`, `WidgetLibrary`,
  `SystemLibrary`; C++ bool properties drop the `b` (`orient_rotation_to_movement`), Blueprint
  variables keep their exact names (`HealAmount`, `bUsed`). TargetTags and AssetTags GE components
  and `LevelEditorPlaySettings` are not exposed (`unreal.load_class` finds them; `ObjectTools`
  writes them).
- `ObjectTools.set_properties` wants `values` as a JSON string: a JSON object returns ok with
  `false` and sets nothing.
- A sphere's scaled radius uses the smallest scale axis (a TriggerSphere of 40 at scale 2, 2, 0.5
  reads 20): attach triggers to an unscaled root.
- No MCP tool creates a level (the catalog has `load_level` and `create_level_instance`): make
  levels in Python, graphs over MCP.
- Enhanced Input 5.8 keeps mappings in `default_key_mappings.mappings`: write the struct back or
  modifiers and triggers vanish silently.
- GE modifier magnitudes refuse Python writes ("cannot be edited on instances"); `ObjectTools`
  accepts the lowerCamel JSON that `get_properties` returns.
- `StateTreeFactory` cannot get a schema outside the GUI: Python `create_asset` returns None.
  Property bags have no Python setters.
- `GameplayTagsToolset.AddTag` without `comment` writes the tool's own description as DevComment; an
  unknown `tagSource` creates nothing and returns null.
- PIE runs in a headless (`-nullrhi`) editor: `StartPIE {"options": {"warmupSeconds": 2.0}}`, then
  `Input.+key SpaceBar` on the game world jumps the character; two players by setting
  `PlayNumberOfClients` and `PlayNetMode` through `ObjectTools`.
- A commandlet can exit 1 after a good run: judge by its result envelope.

## Numbers

| Value                                                                                                  | Relative to                                       | Source                                   |
| ------------------------------------------------------------------------------------------------------ | ------------------------------------------------- | ---------------------------------------- |
| Tick overhead per actor: BP 3.59 us editor, 1.84 us packaged; C++ about 0.64 to 0.70 us                | 100,000 actors, UE 5.4                            | Arnbjornsson [00:05:00]                  |
| CMC 241 us, PlayerController 125 us per frame                                                          | same Lyra frame                                   | Arnbjornsson [00:06:07]                  |
| BP node 0.1 us packaged (0.5 editor); C++ call 0.7 us (0.8 editor)                                     | per call                                          | Arnbjornsson [00:18:48]                  |
| Print String 88.8 to 272.5 us per call                                                                 | Development build                                 | Arnbjornsson slides 00:20:10             |
| GetAllActorsOfClass fine for a few dozen results per frame; WithTag and WithInterface scan every actor | world size                                        | Arnbjornsson [00:37:17], [00:38:56]      |
| 20 active enemies cap; async path offset 0.2 to 0.5 s; 1 dangerous or up to 3 weak attackers           | Lords of the Fallen, per player                   | Bruno [00:16:25], [00:15:20], [00:38:40] |
| Lyra modal push repainted 207 widgets; 25 after the fix                                                | paint count                                       | Albert [00:35:03]                        |
| Jump apex h = v^2 / 2g: 127.6 cm at JumpZVelocity 500, gravity 980; measured 127.4 cm in headless PIE  | Third Person template                             | physics, run on 5.8.3                    |
| Ground dash = speed x duration + exit coast (about 24 cm from 600 cm/s)                                | GroundFriction 8, BrakingDecelerationWalking 2048 | engine model [added, verify]             |
| Scaffold build 67 s; probe 35 s; MCP recipes 116 s with editor start                                   | this Mac, load about 90                           | run on 5.8.3                             |

## Quality gates

- **Measurable:** `cpp_lint`; `ge_plan_verdict`; `statetree_spec_verdict`; `ai_setup_verdict`;
  `audit_gameplay` (tick census, hard-reference closure, cooldown tags, widget bindings); Blueprints
  compile with warnings as errors; scenario verdicts with derived thresholds; automation tests
  `Success`; `gas_log_triage` empty; StateTree trace without unplanned root entry; a reload job
  agrees with what the session set; `rewrite_gate` behind every rewrite.
- **Visual:** jump arc and dash from a fixed camera; enemy facing and spacing; health bar and
  cooldown UI in sync; no frozen widget with Global Invalidation on; two-client screenshots agree in
  multiplayer.

## Common mistakes

| Mistake                                      | What it looks like                                              | Fix                                                      |
| -------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------- |
| Transient client data on the GameMode        | clients see nothing                                             | GameState or PlayerState                                 |
| Multicast for a door state                   | late joiners see it closed                                      | replicated property + RepNotify                          |
| Cast from the player to optional Blueprints  | long loads, memory resident                                     | C++ base, interface, IsA (Soft)                          |
| ASC initialized only in `PossessedBy`        | "Can't activate LocalOnly or LocalPredicted ability" on clients | `AcknowledgePossession` or `OnRep_PlayerState`           |
| Ability never ends; Delay inside it          | cannot re-trigger                                               | End Ability on every path; Wait Delay                    |
| SetByCaller GE applied from the console      | zero damage                                                     | fixed-magnitude twin                                     |
| Querying GE granted tags                     | reactions fire on wrong effects                                 | asset tags; asset-tag cvar at 0                          |
| Cooldown tags set on the deprecated GE field | no component, no tag granted                                    | TargetTags component through `ObjectTools`               |
| Enter conditions trusted to be polled        | enemy keeps chasing inside attack range                         | event or On Tick transition on the running state         |
| C++ controller class on the enemy CDO        | enemy stands still                                              | controller Blueprint holding the tree; placed or spawned |
| Guessed node ids or pin names                | tool errors, silent conversions                                 | `find_node_types`, `get_node_type_pins`, read back       |
| UMG property binding, widget Tick            | per-frame cost; frozen under invalidation                       | events from the attribute delegate                       |
| Editor stopped before saving                 | work lost                                                       | `save_assets`, then a reload check                       |
| Rewrite from a stat hunch                    | effort, no gain                                                 | Insights trace, `rewrite_gate`                           |
| Hand-picked test threshold                   | a correct build fails                                           | derive it from the parameters                            |

## Handoffs

- **Receives** from scenario-unreal-animation: the character Blueprint child, AnimBP variable
  contract, montages with root motion and warp targets, the `AN_SendGameplayEvent` notify on hit
  frames; from scenario-unreal-world-building: levels with nav bounds, player starts, streaming
  ranges.
- **Delivers** to scenario-unreal-vfx: an event contract (`vfx_event_contract`; cues cosmetic only);
  to scenario-unreal-performance: a Development build, the worst-case scenario as an automation
  test, its Insights trace, tick census (`perf_handoff`); to scenario-unreal-animation: the tuned
  movement model before motion matching data (DeVoe FLDXtAV7qsw [00:07:01]); to
  scenario-unreal-pipeline-automation: the automation tests for CI.

## UE 5.8 notes

- Replicated properties auto-register (5.6); Iris Production Ready for licensees, generic
  replication still default; Mover still Experimental.
- Enhanced Input unified with Common UI; Combo trigger deprecated; `UPlayerMappableInputConfig`
  deprecated (5.4).
- GAS: NonInstanced abilities deprecated (5.5); cooldown GE validation (5.7,
  `AbilitySystem.WarnCooldownEffectWithoutTags` default 1); debug commands under
  `AbilitySystem.Ability` and `AbilitySystem.Effect`.
- StateTree: Task Control Flow and scheduled ticks (5.6); Rewind Debugger track (5.7); start state
  by tag (5.8); `StateTreeTools` reads trees over MCP.
- Blueprint: IsA (Soft) (5.5); empty Tick free (5.6); `BlueprintGraphEditor` and `BlueprintTools`
  DSL (5.8).

## References

- `references/mcp-gameplay.md`: Epic MCP intent table, nine live recipes with JSON and scripts,
  traps, when to use Python, signatures, BlueprintBasics reconciliation.
- [`references/procedures.md`](references/procedures.md): code, test path and status per procedure;
  authoring surfaces (P15).
- [`references/expert-notes.md`](references/expert-notes.md): principles by expert, with timestamps.
- [`references/critique.md`](references/critique.md): the rubric for the agent's own output.
- [`references/gui-paths.md`](references/gui-paths.md): editors and menus for the GUI residue.
- `references/sources.md`: every source with best timestamps.
- [`scripts/ue_gameplay.py`](scripts/ue_gameplay.py): decisions, scaffolds, lint, verdicts, trace
  analysis, in-editor helpers (run on 5.8.3);
  [`scripts/ue_gameplay_cpp.py`](scripts/ue_gameplay_cpp.py): C++ templates (compiled on 5.8.3).
