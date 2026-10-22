# scenario-unreal-gameplay procedures (agent side)

Every procedure names its channel, its test path and its status. Status words: **offline-tested**
(ran with system python3, `tests/code/unreal-gameplay/test_gameplay_offline.py`), **run on 5.8.3**
(ran in Unreal Engine 5.8.3 on macOS on 2026-10-21, through the jobs, `live_mcp_recipes.py` or
`live_cpp_build.py`), **not yet run** (with the reason). Epic MCP argument shapes for every step a
toolset covers: `references/mcp-gameplay.md`. Helpers live in `scripts/ue_gameplay.py` (G) and
`scripts/ue_gameplay_cpp.py` (C); shared toolkit calls (`ue_run`, `ue_env`, `ue_review`,
`ue_remote`) come from scenario-unreal-expert.

Channel reminder (scenario-unreal-expert): asset authoring runs headless
(`ue_run.run_python(uproject, job)`, commandlet, no level loaded) unless an editor already holds the
project (then use Epic's MCP or `ue_remote.PythonRemote`; a commandlet that saves assets must never
run against a project an open editor has loaded). PIE, screenshots and anything that needs ticks run
in a latent job (`mode="latent"`) or the live editor.

The worked case throughout is scenario U4: third-person character with double jump and a dash with
cooldown, an enemy that patrols, chases and attacks, and a health bar. Every check below is written
for any character, ability, effect, tree or widget; U4 only supplies the example values.

---

## P0. Probe the engine once (API names, plugins, dumpticks sample)

- Channel: headless job `tests/code/unreal-gameplay/job_00_gameplay_probe.py` through
  `ue_run.run_python`.
- Output: `archive/tests/scenario-unreal-gameplay/<stamp>/probe.json` with `G.probe()` (classes, CDO
  properties, methods of `BlueprintEditorLibrary`, `BlueprintGraphEditor`, `EditorUtilityLibrary`,
  `LevelEditorSubsystem`, `StateTreeEditorData`), the console variables and commands matching
  `AbilitySystem.`, `StateTree`, `Slate.`, `EnhancedInput`, `Input.`, and the help text of
  `BlueprintGraphEditor`.
- Status: run on 5.8.3 (about 35 s headless). All classes in `G.PROBE_CLASSES` exist; three are
  C++-only (`G.SCRIPT_ONLY_CLASSES`: TargetTags and AssetTags GE components,
  LevelEditorPlaySettings); several Python names differ from C++ (`AbilitySystemLibrary`,
  `GameplayTagLibrary`, `WidgetLibrary`, `SystemLibrary`). The GE asset-tag cvar is
  `AbilitySystem.Fix.GameplayEffects.ReturnAssetTagsViaGetOwnedGameplayTags`, default 2 (0 = return
  asset tags as the function name says, 1 legacy, 2 legacy plus ensure, 3 legacy plus ensure every
  time; GameplayEffect.cpp), Shao 8bi0rnXnRj4 [00:21:43]. The console-name scan reads the
  commandlet's `-abslog`; `AbilitySystem.Ability.*`, `AbilitySystem.Effect.Apply/ListActive/Remove`
  and `AbilitySystem.Debug.*` exist.

```python
import sys; sys.path.insert(0, "<skill>/scripts"); sys.path.insert(0, "<expert>/scripts")
import ue_run
res = ue_run.run_python("/abs/MyGame/MyGame.uproject",
                        "/abs/tests/code/unreal-gameplay/job_00_gameplay_probe.py", timeout=900)
print(res["ok"], res["result"]["out"])
```

## P1. Decide the architecture (no editor)

- Channel: offline. Test: `Decisions.*` (offline-tested).
- Inputs: the Establish-first table in SKILL.md. `cpp` comes from P3 (True, False, None).

```python
import ue_gameplay as G
spec = dict(G.U4_SPEC, cpp=None)          # set True/False after the P3 probe build
rec = G.decide(spec)
print(G.decision_markdown(rec))            # paste into the report; answer rec["open_questions"]
```

U4 result: GAS (cooldown UI, tag blocking, damage through GEs, growth), ASC on the pawn, Mixed for
the player and Minimal for the enemy, StateTree with C++ tasks, Enhanced Input bound in C++ to
`TryActivateAbilitiesByTag`, C++ `UUserWidget` health bar, CharacterMovement. The decision flips to
plain components when C++ cannot build (GAS needs C++ for the ASC and attribute sets), and to a
Behavior Tree when the team already knows Behavior Trees (equally valid; the attack still delegates
to an ability with a timeout, Bruno XKQfMZOXFv0 [00:17:37]).

## P2. Project scaffolding: plugins, config, tags

- Channel: files on disk (editor closed). Test: `IniAndConfig.*` (offline-tested). Plugin
  identifiers `GameplayAbilities`, `StateTree`, `GameplayStateTree`, `PythonAutomationTest`,
  `EnhancedInput` loaded on 5.8.3 (live_util.make_project).

```python
import ue_env, ue_gameplay as G, ue_gameplay_cpp as C
up = "/abs/MyGame/MyGame.uproject"
plugs = C.plugins_for(C.FEATURES) + ["PythonAutomationTest"]   # + "CommonUI" for menu stacks
print(ue_env.enable_plugins(up, plugs))                          # backup under Saved/AgentBackups
cfg = "/abs/MyGame/Config/"
G.ini_set(cfg + "DefaultGame.ini", G.GAS_GLOBALS, "bUseDebugTargetFromHud", "True")  # tranek 6.1
# Designer tags as ini lines (native tags from the C++ scaffold need no ini):
G.add_gameplay_tags_ini(cfg + "DefaultGameplayTags.ini", [("Ability.Dash.Air", "designer tag")])
# After P0 names it: G.ini_set(cfg + "DefaultEngine.ini", "ConsoleVariables", "<AbilitySystem.Fix...>", "0")
print(G.config_verdict("/abs/MyGame", needs=("gas", "statetree", "tests"),
                       tags=[t for t, _ in C.NATIVE_TAGS]))
```

Also, when a live MCP session is wanted:
`ue_env.enable_plugins(up, ["ModelContextProtocol", "AllToolsets"])` (AllToolsets pulls in
EditorToolset, run on 5.8.3; Deiter k0tgmrBuIJc [00:06:00]); launch through
`ue_run.launch_editor(uproject, mcp_port=N)`.

## P3. C++ layer: Xcode gate, probe build, scaffold, build, lint

- Channel: shell (editor closed). Tests: `Cpp.*` and `Lint.*` (offline-tested). Run on 5.8.3: the
  full scaffold (all features) compiled with 0 errors and 0 warnings in 67 s with Xcode 26.6
  (`tests/code/unreal-gameplay/live_cpp_build.py`), after `patch_build_cs` added
  `PublicIncludePaths.Add(ModuleDirectory)`; without it every file failed with
  `'Gameplay/X.h' file not found`. A new module needs `Source/<Name>.Target.cs`,
  `<Name>Editor.Target.cs`, the module's Build.cs, a `.cpp` with `IMPLEMENT_PRIMARY_GAME_MODULE` and
  a `Modules` entry in the `.uproject` (the test writes all five).
- Why first: Xcode 26.6 is installed, Epic names 26.0 minimum, 26.1.1 recommended and 26.4
  incompatible; 26.6 is unlisted (macOS requirements doc).

```python
import subprocess, ue_env, ue_gameplay as G, ue_gameplay_cpp as C
xc = subprocess.run(["xcodebuild", "-version"], capture_output=True, text=True).stdout
gate = G.xcode_gate(xc)             # unlisted -> build the scaffold once and read the result
eng = ue_env.find_engine()
files = G.cpp_scaffold("MyGame")    # tags, health set, character base, hero, enemy, dash,
                                    # melee, AI controller, StateTree tasks, health widget
print(G.write_scaffold(files, "/abs/MyGame/Source/MyGame"))   # keeps different existing files
bc = "/abs/MyGame/Source/MyGame/MyGame.Build.cs"
text, added = G.patch_build_cs(open(bc).read(), C.modules_for(C.FEATURES))
G.write_text(bc, text)              # backup first
cmd = G.build_command(eng["root"], "/abs/MyGame/MyGame.uproject")
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.returncode, r.stdout[-3000:])
print(G.lint_verdict(G.cpp_lint("/abs/MyGame/Source")))       # GATE: ok and no warnings
```

- A Blueprint-only project first needs one C++ class to become a code project (Tools > New C++
  Class, or add a `Source/` module and a `Modules` entry in the `.uproject`), then project files
  regenerate.
- Close the editor for new classes, new `UPROPERTY`/`UFUNCTION`, and header changes. Live Coding on
  Mac was not tried here (not yet run: the test builds with UBT and the editor closed); the MCP doc
  notes Live Coding does not propagate new `UFUNCTION` declarations even where it works.
- ASC initialization is the first thing that breaks: `InitAbilityActorInfo` must run on the server
  AND on the owning client after possession. ASC on the pawn: server `PossessedBy`, client
  `AcknowledgePossession` on the PlayerController; ASC on the PlayerState: server `PossessedBy`,
  client `OnRep_PlayerState` (tranek 4.1.2). AI pawns only need the server side. A missing client
  init logs `Can't activate LocalOnly or LocalPredicted ability ... when not local` (tranek 9.1).
  The lint rule `ASC_CLIENT_INIT_MISSING` catches it statically; the scaffold ships
  `AGameplayPlayerController::AcknowledgePossession` for it (set it as the GameMode's
  `player_controller_class`, P4).
- What the scaffold encodes: ASC on the pawn with `bMinimalReplication` as a Python-settable default
  and init on both sides; Health, MaxHealth and a meta Damage attribute
  (`ATTRIBUTE_ACCESSORS_BASIC`, 5.6); BlueprintPure test getters (`GetHealth`,
  `HasGameplayTagByName`); a dash that commits (cooldown GE) and drives a constant-force root motion
  task; a melee ability that waits for the `Event.Attack.Hit` gameplay event and applies ONE damage
  GE with SetByCaller `Data.Damage`; an AI controller with `UStateTreeAIComponent` and sight
  perception sending StateTree events, which binds the pawn's `OnDied` delegate and stops the tree
  on death (one-way: the pawn never knows its listeners, Forsythe VMZftEVDuCE [00:19:25]; spawners,
  HUD and score bind the same delegate); three StateTree tasks (Find Patrol Point, Activate Ability
  By Tag with timeout, Set Debug State); a `BindWidget` health bar updated by delegate.
- Lint rules and sources: `G.LINT_RULES` (v2 adds `ASC_CLIENT_INIT_MISSING`, `WIDGET_TICK`,
  `COLLAPSED_TOGGLE`, `BEGINPLAY_REPEAT`). If the lint flags your own code, fix the code, not the
  rule.

## P4. Blueprint children and defaults from Python (data layer)

- Channel: headless job (or live editor). Test: in-engine
  `tests/code/unreal-gameplay/job_u4_assets.py`. Status: run on 5.8.3 against the compiled scaffold
  (module `Arena`): every default below applied, compiled and saved. A `{"soft": path}` slot takes
  the loaded object; a SoftObjectPath is refused (fixed in `set_defaults`). Python property names
  drop the `b` of bools (`orient_rotation_to_movement`); the C++ name (`bOrientRotationToMovement`)
  is accepted too.

```python
import unreal, ue_gameplay as G
F = "/Game/Gameplay"
G.create_blueprint(F, "BP_Hero", "/Script/MyGame.HeroCharacter")
G.create_blueprint(F, "BP_Enemy", "/Script/MyGame.EnemyCharacter")
G.create_blueprint(F, "BP_GameMode", unreal.GameModeBase.static_class())
G.set_defaults(F + "/BP_Hero", {
    "jump_max_count": 2,                                  # ACharacter::JumpMaxCount
    "default_mapping_context": {"soft": "/Game/Input/IMC_Default.IMC_Default"},
    "move_action": {"asset": "/Game/Input/IA_Move"}, "look_action": {"asset": "/Game/Input/IA_Look"},
    "jump_action": {"asset": "/Game/Input/IA_Jump"}, "dash_action": {"asset": "/Game/Input/IA_Dash"},
    "attack_action": {"asset": "/Game/Input/IA_Attack"},
    "default_abilities": [G.load_class(F + "/GA_Dash_Hero"), G.load_class(F + "/GA_Melee_Hero")],
    "hud_widget_class": {"class": "/Game/UI/WBP_HUD"},
})
# Feel: tune to the user's targets, never ship defaults (Forsythe IaU2Hue-ApI [00:23:39]).
# jump_z_velocity sets the apex: h = v^2 / (2 * 980 * gravity_scale) cm.
G.set_component_defaults(F + "/BP_Hero", "character_movement",
                         {"jump_z_velocity": 700.0, "air_control": 0.35, "max_walk_speed": 500.0})
G.set_defaults(F + "/BP_Enemy", {"default_abilities": [G.load_class(F + "/GA_Melee_Enemy")],
    # the controller BLUEPRINT that holds the StateTree (P7), not the bare C++ class
    "ai_controller_class": {"class": "/Game/AI/BP_EnemyController"},
    "auto_possess_ai": unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED})   # run on 5.8.3
G.set_component_defaults(F + "/BP_Enemy", "character_movement", {"max_walk_speed": 200.0})
G.set_defaults(F + "/BP_GameMode", {"default_pawn_class": {"class": F + "/BP_Hero"},
    "player_controller_class": {"class": "/Script/MyGame.GameplayPlayerController"},  # client ASC init
    "hud_class": unreal.HUD.static_class()})   # showdebug needs a HUD
```

- The numbers above are placeholders to replace with the user's feel targets; the chase speed is a
  property the StateTree binds from the pawn or a data asset (P7).
- Any AI pawn, placed or spawned: `ai_controller_class` names the controller Blueprint that holds
  the tree and `auto_possess_ai` is `PLACED_IN_WORLD_OR_SPAWNED`, or spawner enemies get no
  controller (AI docs, Agent translation; BAU digest P4 step 4).
  `G.ai_setup_verdict(G.ai_setup_facts(bp))` checks both plus the tree reference and a
  NavMeshBoundsVolume.
- Components added in a Blueprint (not declared in C++) are not CDO properties:
  `G.blueprint_components(bp)` reaches them through `SubobjectDataSubsystem` (run on 5.8.3); their
  templates end in `_GEN_VARIABLE` and take `ObjectTools.set_properties`. Declare runtime-controlled
  components in C++ when you can (Forsythe [00:31:39]).
- Project default GameMode:
  `[/Script/EngineSettings.GameMapsSettings] GlobalDefaultGameMode=/Game/Gameplay/BP_GameMode.BP_GameMode_C`
  in `DefaultEngine.ini` (run on 5.8.3: PIE spawned the GameMode's pawn), or World Settings GameMode
  Override per level.

## P5. Enhanced Input assets

- Channel: headless job. Offline part (`G.input_plan`, `G.input_verdict`) offline-tested; asset
  creation run on 5.8.3 (13 mappings with their modifiers and triggers, verified after a reload).
  5.8 keeps mappings in `default_key_mappings.mappings` (an `InputMappingContextMappingData`
  struct); writing only the top-level `mappings` copy silently drops modifiers and triggers.
  `apply_input_plan` writes the struct back.

```python
import ue_gameplay as G
plan = G.input_plan()                  # IA_Move/Look/Jump/Dash/Attack, IMC_Default
assert not [l for l in G.input_verdict(plan) if l.startswith("error")]
rep = G.apply_input_plan(plan, "/Game/Input")
print(rep["failed"])                    # empty on 5.8.3
```

- WASD: one Axis2D action; W Swizzle YXZ, A Negate, S Negate + Swizzle, D none (framework doc,
  Directional Input). Gamepad parity for every Boolean action. Hold trigger default 1.0 s
  (`UInputTriggerHold`, framework doc).
- Several contexts (walk, vehicle, menu): list the live ones per gameplay state in `plan["states"]`
  and keep them mutually exclusive; `input_verdict` flags a key mapped to different actions by two
  contexts live in the same state at the same priority (framework doc, Input Mapping Contexts). Add
  and remove contexts on state change.
- Fallback when `rep["failed"]` lists instanced modifiers: duplicate the template project's
  `IMC_Default` (`unreal.EditorAssetLibrary.duplicate_asset`) and only add or change keys with
  `map_key`.
- 5.8: no Combo trigger (deprecated), no `UPlayerMappableInputConfig` (deprecated 5.4); Enhanced
  Input and Common UI share input data.
- Verify at runtime: `showdebug enhancedinput` in PIE (screenshot) lists IMC_Default and the
  actions.

## P6. GAS data: tags, cooldown and damage effects, ability children

- Channel: headless job or editor Python, then Epic MCP `ObjectTools` for the fields Python cannot
  write. Status: run on 5.8.3 (`live_mcp_recipes.py` recipe 7). Duration policy and duration go
  through Python. The TargetTags and AssetTags component classes are not exposed to Python:
  `create_gameplay_effect` instantiates them with `unreal.load_class` and returns
  `rep["object_tools"]`, one `set_properties` call per component; then
  `G.finish_gameplay_effect(path)`. In a pure-Python setting (no MCP) the template route remains:
  duplicate a GE made once in the GUI.

```python
import ue_gameplay as G
F = "/Game/Gameplay"
# Cooldown: HasDuration + grants Cooldown.Ability.Dash (5.7 warns when a cooldown GE grants no tag)
cd = G.create_gameplay_effect(F, "GE_Cooldown_Dash", "HAS_DURATION", duration_s=1.2,
                              granted_tags=["Cooldown.Ability.Dash"])
print(cd["object_tools"])  # send each to ObjectTools.set_properties, then G.finish_gameplay_effect(...)
# Damage: instant, modifier Add on GameplayHealthSet.Damage with SetByCaller Data.Damage,
# asset tag Effect.Type.Damage. Modifiers are writable only through ObjectTools (JSON in
# mcp-gameplay.md recipe 7) or the GUI; the attribute must come from a C++ AttributeSet.
dmg = G.create_gameplay_effect(F, "GE_Damage", "INSTANT", template="/Game/Gameplay/GE_Template_Damage")
G.create_blueprint(F, "GA_Dash_Hero", "/Script/MyGame.GA_Dash")
G.set_defaults(F + "/GA_Dash_Hero", {"cooldown_gameplay_effect_class": {"class": F + "/GE_Cooldown_Dash"},
                                    "dash_speed": 3000.0, "dash_duration": 0.2})
G.create_blueprint(F, "GA_Melee_Hero", "/Script/MyGame.GA_MeleeAttack")
G.set_defaults(F + "/GA_Melee_Hero", {"damage_effect": {"class": F + "/GE_Damage"}, "damage": 10.0,
                                     "attack_montage": {"asset": "/Game/Characters/AM_Punch"}})
```

- Dash distance: `dash_speed * dash_duration` of root motion (600 cm here, placeholder) plus the
  coast after the exit clamp; test against `G.dash_expected_cm(...)` (P10), never a typed number.
  Air dash once per jump would be a tag cleared on landing (new reactive asset, not an edit of
  GA_Dash; Shao [00:47:35]).
- Hit timing: scenario-unreal-animation places the reusable `AN_SendGameplayEvent` notify
  (instance-editable `EventTag` = `Event.Attack.Hit`) on the swing frame (Shao [00:10:46]). Notify
  placement belongs to scenario-unreal-animation (its procedures say which route ran); the GUI path
  is the montage Notifies track.
- New behavior = new asset: a freeze on the fifth chill stack is a reactive ability plus a debuff
  GE, not an edit of the chill spell (Shao [00:47:35]). Query GE asset tags, not granted tags.
- Plan every GE as data first and check it: `G.ge_plan_verdict(G.U4_GE_PLANS)` (cooldown has a
  duration and a `Cooldown.*` tag; instant GEs grant no tags, Shao [00:33:04]; damage goes through a
  meta attribute with SetByCaller `Data.*` and a type in the ASSET tags; console-applied GEs carry
  no SetByCaller).
- Test pieces in isolation before the chain (Shao [00:08:34], [00:21:12]), with a FIXED-magnitude
  twin: a SetByCaller magnitude exists only when code sets it on the spec, so
  `AbilitySystem.Effect.Apply GE_Damage` from the console applies 0 and logs a missing SetByCaller
  magnitude [added, engine behavior, verify]. The talk's console test used a fixed GE. Build
  `GE_Damage_Debug` (same attribute path, Scalable Float magnitude):
  `G.make_fixed_magnitude_variant(F + "/GE_Damage", F + "/GE_Damage_Debug")` duplicates, then
  `ObjectTools.get_properties(Modifiers)`, `G.fixed_magnitude_values(..., 10.0)`,
  `ObjectTools.set_properties`, `G.compile_and_save` (run on 5.8.3; Python alone is refused: "cannot
  be edited on instances"). Then `AbilitySystem.Effect.Apply GE_Damage_Debug` (command exists on
  5.8.3; applies locally, `-Server` on the server, optional level; the apply itself not yet run: it
  needs a pawn with an ASC in PIE), then `showdebug abilitysystem` (3 pages: attributes, effects,
  abilities; `AbilitySystem.Debug.NextCategory`), then the gameplay debugger on the enemy (P11). The
  SetByCaller path itself is tested through the ability (the melee hit sets `Data.Damage`).
- Reactions query a GE's ASSET tags (what it is), not its granted tags (what it gives the target);
  set `AbilitySystem.Fix.GameplayEffects.ReturnAssetTagsViaGetOwnedGameplayTags=0` under
  `[ConsoleVariables]` in `DefaultEngine.ini` as Epic and Fortnite do (default 2 on 5.8.3; Shao
  [00:21:43], [00:22:17]); `G.config_verdict` warns while it is missing.
- Montages inside abilities: `PlayMontageAndWait`, never PlayMontage (it replicates and ends with
  the ability; tranek 9.3). Gameplay Cues are unreliable and cosmetic only: no gameplay state waits
  on a cue (GAS doc, Handling Cosmetic Effects).

## P7. StateTree enemy (patrol, chase, attack)

- Channel: asset by duplicating a template StateTree (Python cannot create one on 5.8.3:
  `StateTreeFactory` returns None without a schema and its schema field is unreachable from Python
  and ObjectTools); reading through `StateTreeTools` (read only); states and transitions on a new
  tree: one GUI pass from the spec, or the C++ builder (below). Parameters per enemy through
  `ObjectTools` (run on 5.8.3, value kept after reload). Spec check offline-tested
  (`RefactorV2.test_statetree_spec`). The engine's Combat, Shooter, SideScroller and TwinStick
  template variants ship AI trees to start from.
- Execution model to design for (Mononen YEmq4kcblj4): selection finds a leaf BEFORE any transition
  [00:11:22]; enter conditions are evaluated only when a transition requests selection, never polled
  like a Behavior Tree, so every condition that should end a state (target in range, target lost)
  needs an event or a transition on the running state; a state with no completion or failure
  transition falls back to its parent and then the root [00:13:39], [00:14:13]; transitions evaluate
  leaf to root, so shared ones sit on parents [00:06:44]; the tasks of one state run together, and
  since 5.6 Task Control Flow decides which of them complete the state.

```python
import ue_gameplay as G
tree = G.U4_ENEMY_TREE                       # the spec as data: states, tasks, transitions, parameters
lines = G.statetree_spec_verdict(tree)       # GATE: no error or warn lines
assert not [l for l in lines if l.startswith(("error", "warn"))], lines
print(G.statetree_outline(tree))             # text for the GUI pass or an MCP prompt
st = G.create_state_tree("/Game/AI", "ST_Enemy", template="/Game/Variant_Combat/Blueprints/AI/ST_CombatEnemy")
G.create_blueprint("/Game/AI", "BP_EnemyController", "/Script/MyGame.EnemyAIController")
G.set_defaults("/Game/AI/BP_EnemyController", {"sight_radius": 1500.0})
# after the tree is wired: per-enemy tuning as TREE PARAMETERS on the component's reference;
# returns the component template for ObjectTools get/set_properties (mcp-gameplay.md recipe 8)
print(G.set_state_tree_parameters("/Game/AI/BP_EnemyController", {"AttackRange": 180.0,
                                                                  "PatrolWait": 1.5}))
print(G.ai_setup_verdict(G.ai_setup_facts("/Game/Gameplay/BP_Enemy", tree_spec=tree)))
```

`statetree_outline(U4_ENEMY_TREE)` (abridged):

```
Root
  Combat | enter: ObjectIsValid(Controller.TargetActor)          on event AI.Event.TargetLost -> Patrol
    Attack | enter: DistanceCompare(pawn, target, Params.AttackRange)
      task SetDebugState "Attack" (does not complete); task ActivateAbilityByTag Ability.Attack.Melee, timeout Params.AttackTimeout
      on succeeded -> Combat; on failed -> Combat               (re-selects: Attack if still in range, else Chase)
    Chase
      task SetDebugState "Chase" (does not complete); task MoveTo(TargetActor, Params.ChaseAcceptance)
      on tick Distance <= Params.AttackRange -> Combat           (Attack's enter condition is not re-checked otherwise)
      on succeeded -> Combat; on failed -> Patrol                (path failure is part of the behavior, Mononen [00:06:04])
  Patrol  task SetDebugState "Patrol" (does not complete)        on event AI.Event.TargetSeen -> Combat
    Walk  task FindPatrolPoint (does not complete); task MoveTo(FindPatrolPoint.PatrolLocation)   on succeeded/failed -> Wait
    Wait  task Delay(Params.PatrolWait)                          on succeeded/failed -> Walk
```

- Why Walk and Wait are separate states: a Delay placed beside MoveTo in one state runs at the same
  time, it does not wait after arrival.
- Why Chase has an On Tick transition: nothing else asks for selection while it runs. An "in range"
  event (overlap sphere, perception) is cheaper where a sender exists (events are the most efficient
  transitions, Mononen [00:15:01]); On Tick transitions keep that state's tree awake under 5.6
  scheduled ticking [added]. Leave `StateTree.Component.ScheduledTickEnabled` on (5.6) so idle trees
  sleep.
- `statetree_spec_verdict` generalizes to any tree: one root; success and failure handling on every
  leaf and on any parent with a completing task (Mononen [00:07:18]); a re-selection trigger on
  every sibling of a state with dynamic enter conditions; no unbound Input (compile error,
  [00:18:19]); `Params.*` references that exist; each task says whether it completes the state
  (5.6); tuning numbers (range, radius, wait, speed, timeout) as tree parameters, not literals
  ([00:16:40]); every event has a sender.
- Per-enemy tuning: tree parameters set per enemy on the component's State Tree Reference (Mononen
  [00:16:40]; BAU digest P4 step 3). Property bags have no Python setters on 5.8.3
  (`InstancedPropertyBag` offers only import/export text); `ObjectTools.set_properties` with
  `G.state_tree_parameter_values` works and the value survives a reload. Fallback: bind from
  context-actor properties that Python sets on the CDO.
- Wiring (`ai_setup_verdict`): the enemy CDO's `ai_controller_class` is `BP_EnemyController` (the
  Blueprint that holds `ST_Enemy`), `auto_possess_ai` `PLACED_IN_WORLD_OR_SPAWNED`, a
  NavMeshBoundsVolume in the level. The C++ controller starts the tree on possess and stops it on
  the pawn's `OnDied`.
- Compile gate: the tree compiles with no unbound Inputs (StateTree editor or the compile log).
- 5.8: start a tree in a given state by gameplay tag (tests, restoring saved AI; Shao KBn62trwkLw
  [00:26:53] uses ForceTransition for the same need).
- Debug: `statetree.startdebuggertraces` / `statetree.stopdebuggertraces`, StateTree debugger or the
  Rewind Debugger track (5.7); `GAMEPLAY_TRACE` log lines from Set Debug State (and `Dead` from the
  controller) parse with `G.parse_trace_lines`; the trace must show no unplanned root entry.
- Navigation: a NavMeshBoundsVolume over the play space before AI tests; check coverage with
  `show Navigation` and a screenshot (Lombardo, Lyra [00:31:36]). The nav agent radius matches the
  enemy capsule; two or three sizes use one supported agent each, many sizes need Bruno's width
  flags (XKQfMZOXFv0 [00:03:04], [00:05:17]).
- C++ builder option [added, verify]: the engine's own StateTree tests build trees in C++ through
  `UStateTreeEditorData` (add sub-tree, child states, tasks, transitions) and compile them. A small
  editor-module function taking the spec as JSON gives an agent full text authoring of trees; read
  `Engine/Plugins/Runtime/StateTree/Source/StateTreeTestSuite` on the installed engine before
  writing it.
- Fallback when neither MCP nor GUI is available: a small C++ state machine in the controller
  (Patrol, Chase, Attack with the same tasks' logic), testable, less designer-friendly; say so in
  the report.

## P8. Health bar Widget Blueprint

- Channel: headless job, or `UMGToolSet` (mcp-gameplay.md recipe 2). Status: run on 5.8.3:
  `build_widget_tree` through `EditorUtilityLibrary.add_source_widget` (root parent `"None"`) built
  both trees, compiled and saved; widgets found again after a reload.

```python
import ue_gameplay as G
hud = G.create_widget_blueprint("/Game/UI", "WBP_HUD", "/Script/MyGame.HealthBarWidget")
print(G.build_widget_tree(hud, G.HEALTH_BAR_TREE_HUD))           # Root canvas, HealthBar, HealthText
bar = G.create_widget_blueprint("/Game/UI", "WBP_EnemyBar", "/Script/MyGame.HealthBarWidget")
print(G.build_widget_tree(bar, G.HEALTH_BAR_TREE_OVERHEAD))      # SizeBox root, HealthBar
G.set_defaults("/Game/UI/WBP_EnemyBar", {"hide_when_full": True})   # Python drops the b of bools; "bHideWhenFull" also works
```

- Names must match the C++ `BindWidget` members; compile errors say which is missing.
- Enemy bar widget class: set `widget_class` on the enemy's `OverheadWidget` component (component
  defaults, P4; `WidgetComponent.widget_class` read on 5.8.3, also `draw_size`, `space`).
- No property bindings, no widget Tick; text changes only when the shown number changes (layout
  invalidation, Albert [00:13:56]).
- Under Global Invalidation widget Tick is called by Paint: a widget that does not repaint does not
  tick, so any per-frame logic in a widget (fades, timers, polling) freezes (Albert [00:10:09]);
  drive it from events or a material. Visibility cost: Visible to Collapsed invalidates layout,
  Visible to Hidden only repaints, so a widget toggled often (enemy bar hidden at full health, hit
  markers) uses Hidden; Collapsed is for rarely shown widgets whose space must be reclaimed
  ([00:12:53]). Lint: `WIDGET_TICK`, `COLLAPSED_TOGGLE`.
- Anchors and layout: `ObjectTools.set_properties` on `<WBP>:WidgetTree.<Panel>.CanvasPanelSlot_<k>`
  with `LayoutData` (offsets, anchors, alignment; run on 5.8.3, JSON in mcp-gameplay.md), then a
  screenshot at the target resolution and two other aspect ratios (offscreen editor; not yet run for
  this skill).

## P9. Automated gameplay tests (automation framework)

- Channel: PythonAutomationTest in the project (CI and headless) and the latent job of P10 (agent
  loop). Discovery and runs through `AutomationTestToolset` run on 5.8.3 in a headless editor
  (mcp-gameplay.md recipe 5): tests under `Content/Python/**/test_*.py` are named
  `Editor.Python.<Project>.<dotted path>`, a failing assert comes back with its traceback. The
  generated U4 test file is not yet run (it needs the U4 level and content).

```python
import ue_gameplay as G
G.write_python_automation_test(
    "/abs/MyGame/Content/Python/Tests/test_gameplay_u4.py",
    overrides={"enemy_patrol_chase_attack": {"enemy_class": "/Game/Gameplay/BP_Enemy",
                                             "places": {"far": [0, 6000, 200], "in_sight": [600, 0, 200]}},
               "health_bar": {"widget_class": "/Game/UI/WBP_HUD"}},
    params={"dash_cooldown": {"cooldown_s": 1.2, "dash_speed": 3000.0, "dash_duration": 0.2,
                              "exit_speed": 600.0}})   # the dash expectation is derived, not typed
```

Run (Automation doc; flags `[verify]`, rendering needed for screenshots so no `-nullrhi`):

```
"<engine>/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" /abs/MyGame/MyGame.uproject \
  -ExecCmds="Automation RunTest Editor.Python;Quit" -ReportExportPath=/abs/MyGame/Saved/Automation/Report -unattended
```

- Test design (Automation doc guidelines): no assumed state, clean before and after, one scenario
  per latent command; keep tests in a plugin when they should ship with builds.
- Gauntlet for packaged builds:
  `RunUAT.sh RunUnreal -test=UE.TargetAutomation -runtest=<prefix> -project=<uproject> -build=<staged>`
  `[verify on Mac]`.
- C++ functional tests (`AFunctionalTest`: PrepareTest, IsReady, OnTestStart, FinishTest) are the
  option when a scenario must live in a test map with Observation Points; the Python route needs no
  compile.

## P10. PIE scenario in a latent job (the agent's own loop)

- Channel: `ue_run.run_python(..., mode="latent")` with `tests/code/unreal-gameplay/job_u4_pie.py`,
  or the same generator through `ue_remote.PythonRemote` in a live editor. Status: `pie_scenario`
  run on 5.8.3 in a headless editor through `G.start_on_tick` (a Third Person jump: apex 127.4 cm at
  JumpZVelocity 500, gravity 980; theory 127.6 cm), and the analyzers offline-tested (`Traces.*`,
  `TestsAndHandoffs.test_scenario_verdicts`). `job_u4_pie.py` itself is not yet run: it needs the U4
  level (enemy, navmesh, tree states from the GUI pass).

```python
import ue_run
res = ue_run.run_python("/abs/MyGame/MyGame.uproject", "/abs/tests/code/unreal-gameplay/job_u4_pie.py",
                        args={"map": "/Game/Maps/L_Test", "scenarios": ["double_jump", "dash_cooldown"],
                              "enemy_class": "/Game/Gameplay/BP_Enemy", "widget_class": "/Game/UI/WBP_HUD",
                              "places": {"far": [0, 6000, 200], "in_sight": [600, 0, 200]}},
                        mode="latent", timeout=900)
for name, r in res["result"]["verdicts"].items():
    print(name, r["ok"], r["lines"])
```

How it works (`G.pie_scenario`): `LevelEditorSubsystem.editor_request_begin_play()`, wait for
`UnrealEditorSubsystem.get_game_world()` and the player pawn, then per step `Input.+key <Key>` /
`Input.-key <Key>` through `SystemLibrary.execute_console_command` on the PIE world (framework doc,
Injecting Input), one sample per tick (location, velocity, `jump_current_count`, falling,
`get_health()`, `has_gameplay_tag_by_name("Cooldown.Ability.Dash")`, enemy location and
`debug_state_name`, widget `get_displayed_percent()`), screenshots through `ue_review.screenshot`,
then `editor_request_end_play()`.

What the analyzers check:

- `analyze_jump`: CharacterMovement sets `Velocity.Z = max(Velocity.Z, JumpZVelocity)` per jump
  [added], so total rise after the second press = rise at that press + `v^2 / 2g`; a second press at
  the apex doubles the height; a third press adds nothing with `JumpMaxCount = 2`.
- `analyze_dash` and `analyze_cooldown`: displacement within 10 percent of the DERIVED expectation
  `G.dash_expected_cm(speed, duration, exit_speed, props)`: root motion `speed * duration` plus the
  coast after the ClampVelocity exit under CharacterMovement braking (`coast_distance_cm`, braking
  values read from the pawn in PIE) [added, engine behavior, verify]; blocked inside the cooldown
  with the cooldown tag present, works again after it. An air dash has no braking by default, so
  give it its own expectation. Every threshold a test emits comes from the movement parameters,
  never from a guess (U4 grade: a 70 percent double-jump oracle failed a correct build).
- Enemy: `DebugStateName` sequence Patrol, Chase, Attack with Chase within 1 s of sight; without the
  debug task the phases are inferred from motion (`infer_ai_phases`); player health must drop.
- Health bar: displayed percent equals Health/Max within one frame.

Then look: `ue_review.review_images(res_screenshots, sheet=...)`, which runs `image_checks` (rejects
all-white or all-black frames) before you judge the jump arc, enemy spacing and the HUD.

## P11. Debug evidence for the report

- Channel: live editor or latent job during PIE. Status: not yet run (needs a level with an
  ASC-carrying pawn and a focused PIE window for the gameplay debugger; the `AbilitySystem.*` and
  `showdebug` commands exist on 5.8.3).
- `showdebug abilitysystem` then `AbilitySystem.Debug.NextCategory` twice, a screenshot per page
  (needs the GameMode HUD class; tranek 6.1).
- `showdebug enhancedinput`, `showdebug devices` (framework doc).
- Gameplay debugger on each AI with an ASC: apostrophe key in a focused PIE window while looking at
  the enemy (Shao [00:24:08]); Abilities category: blue = granted and active, yellow = granted but
  inactive ([00:35:38]); it shows tags, effects and abilities on other characters, not attribute
  current values (tranek 6.2). On a MacBook the numpad category keys need rebinding (tranek 6.2;
  version deltas); console toggle `EnableGDT` `[verify]`.
- `log LogAbilitySystem VeryVerbose` before the scenario, then `G.gas_log_triage(open(log).read())`:
  maps `Can't activate LocalOnly or LocalPredicted ability` to the missing client ASC init (tranek
  9.1), a missing SetByCaller magnitude to a SetByCaller GE applied without its value,
  `ScriptStructCache` to `InitGlobalData`, `MarkPropertyDirty` to NetCore (tranek 9.2, 9.5).
- `statetree.startdebuggertraces` before the scenario, `statetree.stopdebuggertraces` after; open
  the trace in the StateTree debugger or Rewind Debugger (human) and parse `GAMEPLAY_TRACE` lines
  (agent).
- Visual Logger for AI decisions (`vislog` `[verify]`).

## P12. Audits before handoff

- Channel: offline (lint, parsers) and headless job (asset facts). Offline parts offline-tested.

```python
import ue_gameplay as G
print(G.lint_verdict(G.cpp_lint("/abs/MyGame/Source")))
rep = G.audit_gameplay(["/Game/Gameplay", "/Game/UI"],                 # in the editor
                       always_loaded=["/Game/Gameplay/BP_Hero", "/Game/Gameplay/BP_GameMode", "/Game/UI/WBP_HUD"])
# runtime tick census in PIE or a Development build: run `dumpticks`, read the log, then
census = G.parse_dumpticks(open("/abs/MyGame/Saved/Logs/MyGame.log").read())
print(G.tick_verdict(census, justified=("BP_Hero",)))
# Blueprint graphs as JSON (5.5): console `snapshotblueprints audit`, then
print(G.scan_blueprint_snapshot("/abs/MyGame/Saved/<snapshot folder>"))   # folder [verify]
```

- Tick census: count and justify; aggregate hundreds of ticking actors into a manager with instanced
  meshes or Mass (Arnbjornsson [00:11:35]); empty Ticks are free from 5.6.
- Hard references from always-loaded classes (player, GameMode, HUD, game instance) to optional
  heavy Blueprints: C++ base class, interface, IsA (Soft) or soft references (Arnbjornsson
  [00:28:01]).
- Cook rules: Asset Manager Map rule Always Cook with Is Editor Only off (Arnbjornsson [00:44:27])
  belongs to scenario-unreal-pipeline-automation; flag it if missing.
- Before any Blueprint-to-C++ rewrite or "Blueprints are slow" claim: an Unreal Insights trace of
  the repeatable scenario in a Development build (`-trace=default -tracefile=<abs>.utrace` [verify],
  or scenario-unreal-performance's capture plan), timers exported with TraceQuery, then

```python
import ue_stat
tot = ue_stat.timer_totals(ue_stat.parse_jsonl("/abs/scenario_timers.jsonl"))
print(G.rewrite_gate(tot, ["BP_Enemy", "UpdateAim"])["candidates"])   # rewrite only what is hot
```

Forsythe: 80 percent of the time sits in 20 percent of the code; often one function in C++ equals a
system rewrite (VMZftEVDuCE [00:16:33], [00:17:06]); Arnbjornsson's tick numbers only matter at
scale (S2olUc9zcB8 [00:06:07]). Stat commands alone do not decide it.

## P13. Multiplayer smoke test (when multiplayer is in scope)

- Channel: editor with Epic's MCP. Status: two-player listen-server PIE run on 5.8.3 in a headless
  editor (two PIE worlds, the server one with the GameMode, two characters in each); the replication
  checks below not yet run (they need a replicated test level). `LevelEditorPlaySettings` is not
  exposed to Python, so `configure_play` returns `ObjectTools.set_properties` arguments.

```python
import ue_gameplay as G
args = G.configure_play(num_players=2, net_mode="PIE_ListenServer")   # -> ObjectTools.set_properties(**args)
# then EditorAppToolset.StartPIE; reset with G.configure_play(1, "PIE_Standalone")
# add latency on the client: console "NetEmulation.PktLag 150" (cvar exists on 5.8.3, effect not yet run)
# run the same scenarios; assert in the log that Server RPCs run with authority and RepNotifies
# fire on clients; screenshot both windows: same health, same enemy state
```

- Checklist: state in replicated properties with RepNotify, never multicast; C++ OnRep called
  manually on the server; Server RPCs only on actors the client owns; Reliable only for rare
  critical calls (Forsythe JOJP0CvpB8w; networking doc). Replicated properties auto-register since
  5.6; conditions still need the macros. Iris is Production Ready for licensees in 5.8, generic
  replication still the default.

## P14. World Partition persistence regression

- Channel: latent job. Status: not yet run (needs a World Partition level with streaming state).
- Steps (Shao KBn62trwkLw [00:07:29]): change state (open a door), teleport the player beyond the
  streaming range, run `obj gc` `[verify]` (forces the reload-from-disk path), return and compare;
  repeat without GC (reuse path, BeginPlay runs again); then save with `AsyncSaveGameToSlot`, end
  PIE, start PIE, load, compare a logged list of values; screenshot on return to catch pops.
- Code rules: idempotent BeginPlay and EndPlay (lint `BEGINPLAY_REPEAT` flags non-unique
  `AddDynamic`, `SpawnActor`, `GiveAbility` and effect application in BeginPlay); restore before
  BeginPlay (world "actors initialized", `UWorldSubsystem::OnWorldBeginPlay`); Blueprint-added
  components receive restored values after BeginPlay, so use a PostRestore hook; write your own
  version header; never restore GEs that an equipped item re-grants.

## P15. Authoring surfaces and graph residue: what only a graph editor reaches

Authoring surfaces (moved here from SKILL.md in v2):

| Target                         | Scriptable without a graph                                                                                                                                                                                                                                                                                                                             | Needs a graph editor, Epic's MCP toolsets, or one GUI pass                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Logic                          | C++ classes (text, built with UBT; Xcode 26.6 built 5.8.3 code, run); `UBlueprintFunctionLibrary` statics; Blueprint event and function graphs through `BlueprintTools.write_graph_dsl` (run on 5.8.3, mcp-gameplay.md recipe 1)                                                                                                                       | nothing required; read the DSL back after writing                                                                           |
| Blueprint classes              | create with a parent (5.5 `CreateBlueprintAssetWithParent` or `BlueprintFactory`), reparent, 5.5 `AddMemberVariable`, CDO defaults (including `ai_controller_class`, `auto_possess_ai`, `player_controller_class`), compile, save (run on 5.8.3); Blueprint-added component templates through `SubobjectDataSubsystem` (`G.blueprint_components`, run) | none                                                                                                                        |
| Data                           | data assets, data tables from CSV or JSON, Primary Asset rules, config ini                                                                                                                                                                                                                                                                             | instanced-struct rows: duplicate a template                                                                                 |
| Enhanced Input                 | Input Actions, Mapping Contexts, `map_key`, modifiers and triggers as instanced objects written back through `default_key_mappings` (run on 5.8.3)                                                                                                                                                                                                     | none                                                                                                                        |
| GAS                            | native tags (C++) and `DefaultGameplayTags.ini`; GE Blueprints (duration from Python; component tags and modifiers through `ObjectTools`, run on 5.8.3); fixed-magnitude debug twins; ability children of parameterized C++ abilities; ASC, attribute sets, init and executions are C++ only                                                           | without MCP: one template GE per shape, then duplicate. `GASToolsets` inspect runtime state and cues (catalog, not yet run) |
| StateTree                      | asset by duplicating a template, tree parameters on the component reference through `ObjectTools` (run on 5.8.3), reading through `StateTreeTools`, C++ tasks and conditions, the spec as data (`U4_ENEMY_TREE`) checked offline; 5.8 start state by gameplay tag                                                                                      | states, transitions, bindings on a new tree: StateTree editor, or a C++ editor builder [added, not yet run]                 |
| Behavior Tree, Blackboard, EQS | assets and references                                                                                                                                                                                                                                                                                                                                  | node graphs; custom EQS tests are C++ only                                                                                  |
| UMG                            | Widget Blueprint with a C++ `BindWidget` parent; tree via `EditorUtilityLibrary.add_source_widget` or `UMGToolSet` (both run on 5.8.3); slot layout via `ObjectTools`                                                                                                                                                                                  | widget animations                                                                                                           |

Graph residue:

- Order of preference: (1) do not need a graph (C++ base plus data-only child; a prebuilt parent
  that already owns the graph, as Lyra's `GA_WeaponFire` children do, Lombardo [00:50:07]); (2)
  `BlueprintTools` DSL with the arguments in mcp-gameplay.md (no `describe_toolset` needed; name the
  Blueprint asset, not the placed actor, Deiter k0tgmrBuIJc [00:24:52]; no Delay chains or Event
  Tick, [00:56:45]); (3) 5.8 `unreal.BlueprintGraphEditor` from Python (`list_nodes_with_errors`,
  `add_call_function_node`, run on 5.8.3 for error listing only); (4) a precise GUI request from
  `gui-paths.md`.
- Always recompile and rerun P9 after graph edits.

## P16. Handoffs

- Channel: offline. Test: `TestsAndHandoffs.test_handoffs` (offline-tested).

```python
import ue_gameplay as G
vfx = G.vfx_event_contract([
    {"tag": "GameplayCue.Dash", "trigger": "GA_Dash activation", "payload": ["location", "direction"],
     "radius_source": None, "gameplay_window_s": 0.2, "max_rate_hz": 1, "spawn": "gameplay_cue"},
    {"tag": "Event.Attack.Hit", "trigger": "AN_SendGameplayEvent", "payload": ["location", "normal", "instigator"],
     "radius_source": "GA_MeleeAttack.HitRadius", "gameplay_window_s": 0.3, "critical": True, "spawn": "pool"},
])
print(G.vfx_contract_verdict(vfx))
perf = G.perf_handoff(build="/abs/Builds/Mac/MyGame.app", scenario_test="Editor.Python.MyGame.test_gameplay_u4",
                      insights_trace="/abs/Saved/Traces/scenario.utrace", tick_census=census, ai_count=1, asc_count=2, spawns_and_pools="none yet",
                      overlaps_per_frame="melee sphere per hit only", umg_bindings=0,
                      statetree_scheduled_tick=True)
print(perf["missing"])
```

- scenario-unreal-vfx reads gameplay numbers from the contract (radius, window, rate) and never
  hand-matches them; cosmetic feedback may ride Gameplay Cues, gameplay state never waits on them
  (GAS doc, Handling Cosmetic Effects).
- scenario-unreal-performance gets a Development build and the scenario that reproduces the worst
  case, not a description of it.
