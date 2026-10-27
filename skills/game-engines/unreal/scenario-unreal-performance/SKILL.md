---
name: scenario-unreal-performance
description: 'Use when an Unreal Engine 5.8 project misses its frame rate or stutters: "optimize to 60 fps", "we run at 38 fps", CPU or GPU bound, game or render thread too long, hitches, traversal or shader stutter (PSO), GC spikes, camera-cut spikes, Lumen, Nanite, VSM, ray tracing, shadowed lights, foliage, crowds or Niagara too expensive, too many actors or draw calls, oversized or uncompressed textures, missing LODs, async compute, stat unit, CSV profiler, ProfileGPU, Unreal Insights traces read from the command line, snapshothitches, scalability and device profiles, dynamic resolution and TSR, streaming budgets, performance audits and fixes through Epic''s MCP toolsets, or proving a fix with before and after captures.'
license: MIT
---

# Performance engineering in Unreal Engine 5.8

Expert level here means milliseconds per stage, not frames per second: classify the bound with one
honest capture, explain the worst frame by the thread that works rather than the one that waits, fix
in the order of measured size, and prove the result with repeated runs on the same route and build,
hitches judged apart from the average. The performance engineer owns measurement, diagnosis and
proof; most fixes go back to the teammate who owns the content. If a sibling skill named here is
missing from your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.

**REQUIRED BACKGROUND:** scenario-unreal-expert (channels, review loop, 5.8 traps). For Niagara
authoring levers read Epic's in-editor NiagaraOptimization skill through
`ToolsetRegistry.AgentSkillToolset`; this skill keeps measurement, budgets and proof.

**Status (2026-10-21, run on 5.8.3, Apple Silicon Mac):** ran: the probe (P0), CSV captures from the
editor binary with `-game`, `ue_perf` on those CSVs and on traces read through the Insights command
line, `snapshothitches`, the in-editor audits, and the nine MCP recipes plus a measured before and
after (`tests/code/unreal-performance/live_mcp_recipes.py --measure`, all pass). **[not yet run]**:
packaged builds (BuildCookRun, Test config), devkit captures, ProfileGPU log parsing, PIE routes,
`apply_change_requests(apply=True)`, Instruments. The machine was shared and loaded: read ratios and
counters, not the third digit.

## Stance (the expert delta)

- **Milliseconds per stage, then the right tool.** At 60 fps the game thread, render thread and GPU
  each get 16.6 ms, pipelined game N, render N-1, GPU N-2 (W4R [00:05:17] [00:08:26]). Report ms,
  never fps (ARI22 [00:14:44]). `stat unit` or the CSV profiler classifies, Insights says where on
  the CPU, a GPU capture explains the GPU, a sampling profiler says why when instrumentation runs
  out (KEN [00:04:04]; NORSE [00:17:30]).
- **An honest capture before any fix.** Cooked Test or Development build on target hardware, fixed
  route; lock dynamic resolution (75%) and force async compute off only to attribute passes, never
  for the proof (NORSE [00:44:40] [00:45:12]). Lean capture for "are we on budget", rich
  (`-statnamedevents`, about 20% overhead) for "why" (NORSE [00:11:27]); `-NoVerifyGC` and
  `-handleensurepercent=0` remove fake Development hitches (NORSE [00:13:35] [00:16:23]).
- **The longest bar is often a wait, and waits are budget.** Follow the dependency to the working
  thread; a slow render frame N shows as game-thread waiting in frame N+1 (KEN [00:09:54]
  [00:16:30]). Run on 5.8.3: a 42 ms render thread was 26 ms of `EventWait/Shadows` while GPU
  ShadowDepths took 32 ms; read the `Exclusive/RenderThread/*` and `GPU/*` columns before naming the
  bound.
- **Epic scalability is the 30 fps mode.** High (2) is the 60 fps level, and nothing selects the 60
  fps device profile unless you build that (OZ26 [00:11:00] [00:16:50]; LVP). The resolution chain
  (dynres 800p to 1080p, TSR to 1440p, spatial upscale to 4K) is the biggest single rendering lever
  (OZ26 [00:14:41]; W4R [00:43:08]).
- **Budget each feature, measure by delta, follow its tree.** Lumen GI plus reflections is about 4
  ms at 60 fps, read as the frame delta with Lumen off (OZ24 [00:37:55]). Nanite: budget, then
  Evaluate WPO and Pixel Programmable views, Overdraw last; a view locates, it does not prove (OZ24
  [00:29:18] [00:32:13]). VSM: chase the larger of static and dynamic invalidations (OZ24
  [00:48:59]). Async compute is an A/B per feature (W4R [00:20:42] [00:21:48]).
- **Defaults favor ease; the big wins are content settings.** Complex collision everywhere, overlaps
  on load, translucency After DOF, DF shadows next to VSM, PDO or WPO foliage paying three times,
  overlapping shadowed local lights, props left Movable (NORSE [00:38:53] [00:49:03] [00:53:48]
  [00:49:35]; FFW [00:52:59]; ARG [00:11:54]). Run on 5.8.3: setting 1,660 movable props to Static
  took a test level from 42 to 13 ms.
- **Hitches are their own pass.** Hundreds of ms is almost certainly a blocking load; GC cost
  follows the UObject count; spawns are not incremental; camera cuts lose occlusion history;
  consoles have no runtime PSO hitches, PC and Mac are tested cold (HITCH [00:43:07] [00:38:31]
  [00:25:08] [00:35:50]; W4R [00:44:44]). Dynamic resolution cannot fix a hitch (W4R [00:43:38]).
- **Fix content before band-aids.** Async physics init, incremental GC and dynres hide growth (HITCH
  [00:22:56] [00:41:56]); throttle the one feature that spikes (W4R [00:38:55]).

## Establish first

| Input                                  | Changes                                                                                                                | Default when silent                                                                |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Target hardware and who captures on it | every number; this Mac cannot deploy to a devkit (PKG)                                                                 | ask; meanwhile Mac numbers labeled as proxy                                        |
| Frame target, output resolution        | stage budget, resolution chain                                                                                         | 60 fps; 4K output on console                                                       |
| Dynamic resolution policy              | lock while profiling; the shipped range                                                                                | on, 55 to 75% of the 1440p secondary (OZ26 [00:15:48])                             |
| Builds available                       | proof in Test; memory traces need Development (INS); a Launcher engine packages DebugGame, Development, Shipping (PKG) | Test from a source engine, else Development with the noise flags                   |
| The route                              | repeatability                                                                                                          | busiest scene, crowd, combat, top traversal speed, camera cuts, as BugIt waypoints |
| Quality bar, who signs trades          | parity gate                                                                                                            | the owner of the look (lighting, art)                                              |

## Workflow

**Channel.** Epic's toolsets first for reading and changing content and settings
([`references/mcp-performance.md`](references/mcp-performance.md)). Four or more toolset calls in a
row go through one `ProgrammaticToolset.execute_tool_script` (define `run()`, call
`execute_tool(name, json_string)`, return a dict; imports `json`, `math`, `re`, `time`, `datetime`,
`copy` only): the reference has the audit and each fix as one script (R3 read 1,700 properties in
one call, R4 set 1,660). Measuring is not MCP: captures are separate `-game` or packaged runs
(`P.capture_plan`), traces are read with `P.insights_export`, whole-project audits run as Python in
a commandlet (`P.perf_audit_level`, `P.perf_audit_assets`). `import ue_perf as P` on the agent side.

0. **Probe.** `job_probe_perf.py` or MCP R1 (`SearchCVars`) for every cvar a plan uses. GATE: every
   name printed a value.
1. **Frame the gap, write budgets.** 38 fps is 26.3 ms, 9.6 ms over 16.67.
   `P.budget_table(platform, fps, pass_budgets)` (OZ26 [00:45:55]). GATE: sources on every row,
   passes sum under the stage.
2. **Route and honest capture.** `P.route_from_bugit(log)`,
   `P.capture_plan("budget", csv_frames=500, ...)`, three runs; the log names the CSV
   (`P.csv_path_from_log`). GATE: three runs, spread known, identical hygiene.
3. **Classify.** `P.diagnose_bound(frames[250:], 16.67, context=...)` (skip boot frames),
   `P.csv_breakdown(csv)` for the pass or scope, `P.csv_counters(csv)` for instances, lights,
   texture memory; read back scalability. GATE: bound named from working time, not waits; gap in ms.
4. **Config first, one change per measurement.** Scalability 2 plus a selector; resolution chain
   (`P.day_one_60fps_cvars`, `P.device_profile_block`, `P.write_ini_section`, backups first);
   `P.day_one_engine_ini()` (Use Simple as Complex, also MCP R2; NeverUpdate overlaps while
   streaming); Lumen foliage threshold 0, roughness below 0.4 from Performance Overview (OZ26
   [00:41:56]); `r.GTSyncType 2` on Gen9. Log each in `P.ChangeLog`. GATE: read-back LastSetBy; each
   change measured.
5. **Deep pass on the bound.** GPU: attributed `ProfileGPU` into `P.gpu_pass_table`,
   `P.lumen_delta`, `P.feature_budget_check`, `P.nanite_triage`, `P.vsm_triage`, async compute
   through `P.ab_plan`. CPU: `P.insights_export(P.insights_binary(engine), utrace, out)` then
   `P.analyze_trace(P.load_insights_events(...))` (non-wait timers, `game_wait`, `advice`),
   `P.spawn_bursts`. Streaming: per-cell cost, request-to-visible latency, `P.STREAMING_AB_VARIANTS`
   as A/B only. GATE: every over-budget bucket has a cause, asset and owner.
6. **Audit and route fixes.** MCP R3 or `P.perf_audit_level()` and `P.perf_audit_assets()`
   (mobility, shadowed lights, collision, WPO, Displacement Fade, textures),
   `P.change_requests(rows)` to owners; apply after agreement (R4 to R8). Parity from the same views
   (`P.parity_pair`). GATE: every pair judged by eye.
7. **Hitch pass.** `capture_plan("hitch")` cold then warm; `P.hitch_snapshots(dir)`, each trace
   through `insights_export` and `analyze_trace`; `P.camera_cut_spikes`. GATE: zero snapshots on the
   cold route, GC under 2 ms, UObjects under 500k.
8. **Prove and guard.** Same route, build, device; three runs each. `P.csv_step_table` for counters
   and ratios, `P.compare_runs`, `P.write_proof_report`; nightly automated test (MCP R9 runs one;
   OZ26 [00:47:43]). GATE: verdict `stable_at_target`, "not tested" filled in.

## Numbers

Talk numbers are for console hardware; this Mac cannot check them, so they stay targets with their
source.

| Item                     | Value                                                                                                             | Relative to, source                             |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Stage budget             | 16.67 ms each (33.3 at 30)                                                                                        | game, render, GPU, W4R [00:05:17]               |
| Lumen GI and reflections | about 4 ms at 60, 8 at 30                                                                                         | frame delta, console High, OZ24 [00:37:55]; LVP |
| Roughness threshold      | 0.4 default; 0.4 vs none 3x faster; foliage has its own cvar: read it at the target scalability level             | OZ26 [00:41:56]; W4R [00:33:42]; LVP            |
| HWRT scene               | under about 100,000 active instances; near field about 150 m (5.8.3 cull radius default 300 m, behind the camera) | consoles, LVP; W4R [00:29:30]                   |
| Async compute            | about 1.5 ms saved overall                                                                                        | PS5, W4R [00:20:42]                             |
| Resolution chain         | primary 800p to 1080p, secondary 1440p, dynres 55 to 75%                                                          | W4R [00:43:08]; OZ26 [00:15:48]                 |
| Streaming                | 5 ms default (5.8.3: 5); 2.5 to 1.5 ms unified; 0.8 ms final                                                      | OZ26 [00:25:25]; W4S [00:23:55]                 |
| Crowd                    | 300 to 200 NPCs: game thread 11.5 ms                                                                              | PS5, W4R [00:16:53]                             |
| UObjects, GC             | under 500k good, over 1M wrong; GC 1 ms fine, 2 ms isolate                                                        | HITCH [00:39:06] [00:39:39]                     |
| Hitch threshold          | 60 ms default `t.HitchFrameTimeThreshold`                                                                         | run on 5.8.3                                    |
| Test level, run on 5.8.3 | frame 42.1 to 8.3 ms, GPU 40.7 to 5.4, instances 1,665 to 66, non-streaming textures 105.7 to 41.7 MB             | Mac proxy, five steps, `mcp-performance.md`     |

## Quality gates

Measurable: stage medians and every lean-route frame under 16.67 ms (NORSE [00:29:51]), percentiles
and VSync-miss share (OZ26 [00:45:55]); zero hitch snapshots cold; every changed cvar read back;
deltas beyond run-to-run spread, same hygiene; on a noisy machine, counters (instances, lights,
texture MB) carry the proof and ms only as ratios. Visual: same-camera pairs for every trade;
snapshot screenshots. Rubric: [`references/critique.md`](references/critique.md).

## Common mistakes

| Mistake                                          | What it looks like                                                | Fix                                                                       |
| ------------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Profiling PIE                                    | Blueprint and CPU costs inflated                                  | cooked build; editor `-game` for triage (FFW [00:04:29])                  |
| GPU ms with dynres on                            | GPU stays near budget while resolution drops                      | lock 75% (NORSE [00:44:40])                                               |
| Blaming the longest bar                          | GameThreadWaitForTask or render EventWait                         | follow to the working thread (KEN [00:16:30])                             |
| Epic scalability on a 60 fps target              | `sg.*` print 3                                                    | level 2 in device profiles (OZ26 [00:12:01])                              |
| `sg.ResolutionQuality=2`                         | 2% resolution                                                     | it is a percentage [added]                                                |
| Nanite Overdraw view first                       | chasing white pixels                                              | budget, Evaluate WPO, Pixel Programmable, Overdraw last (OZ24 [00:32:13]) |
| PSO tested warm                                  | stutter "fixed" on the second run                                 | cold runs off-console (HITCH [00:35:50])                                  |
| Camera-cut spike                                 | overdraw after a cut                                              | `r.Nanite.PrimeHZB` 1 or 2 (W4R [00:44:44])                               |
| Many changes, one measurement                    | gains cannot be attributed                                        | `ChangeLog`, one change per run                                           |
| "Static" props left Movable                      | 1,000 meshes cost 20% (ARG [00:11:54]); 1,660 cost 29 ms on 5.8.3 | mobility audit; confirm nothing moves them                                |
| 4K texture uncompressed, no mips, never streamed | 64 MB resident; generic audits pass it                            | `texture_facts` or R8; per-texture setting                                |
| Merging everything                               | one mesh drawn whole when any part shows                          | merge what is seen together (R6)                                          |
| LODs generated, screen sizes left                | thresholds 0 or nearly equal                                      | set them (R7)                                                             |

## Handoffs

Delivers a diagnosis report plus JSON change requests with measured deltas and parity screenshots:
scenario-unreal-world-building (component counts, merging and instancing, mobility, collision,
HLOD), scenario-unreal-materials (masked, PDO, WPO, Displacement Fade, shading bins, After DOF),
scenario-unreal-lighting-rendering (Lumen thresholds, RT scene, VSM, shadowed lights; signs off
quality trades), scenario-unreal-gameplay (ticks, spawns, blocking loads, overlaps),
scenario-unreal-animation (Budget Allocator, MetaHuman LODs), scenario-unreal-vfx (Effect Types,
pooling), scenario-unreal-cinematics (cut hitches), scenario-unreal-pipeline-automation (texture
settings, device profiles, validators, packaged builds, nightly perf test).

## UE 5.8 notes (run on 5.8.3)

- **Renamed or gone:** `r.ShaderPrintEnable` is `r.ShaderPrint`; `r.Shadow.Virtual.ShowStats` is
  deprecated (typing it fires an ensure), use `r.Shadow.Virtual.Stats.Visible`;
  `r.Nanite.ShowMeshDrawEvents` is gone. `r.RHISetGPUCaptureOptions` is a command: `-ExecCmds`,
  never `-DPCVars`. `r.PSOPrecache.Validation` exists only in packaged builds; `a.Budget.*` only
  with its plugin.
- **CSV profiler:** `-csvCaptureFrames=N -ExitAfterCsvProfiling`; with the launcher editor binary
  and `-game` on a Mac the file lands in the engine's per-user `Saved/Profiling/CSV`, named in the
  log. `GPU/<pass>` columns need `r.GPUCsvStatsEnabled=1`; `RHI/DrawCalls` and `DrawCall/*` read 0
  on Metal, count `GPUSceneInstanceCount`.
- **Traces:** the launcher build ships no TraceQuery; Insights exports with no window
  (`P.insights_export`, under a second for 219,000 events).
- **snapshothitches:** needs a stat group (`stat default` or `stat game`; `stat unit` alone gave
  none); writes `Frame-<N>.utrace` and `.png` per hitch.
- **MCP:** no console tool; `SearchCVars` lists variables only; `GetLogEntries` needs
  `"category": ""`; `merge_actors`: same value in `name` and at the end of `output_path`, read the
  mesh path back; `RunTests` blocks, and a world test crashed a `-nullrhi` editor.
- Mac: Nanite and VSM Beta, Lumen HWRT and MegaLights Experimental (M2+); Insights has no
  ContextSwitch; GPU "why" in Xcode and Instruments (MOB).

## References

- `references/mcp-performance.md`: intents, signatures, single calls, nine live recipes as scripts,
  measured before and after, traps.
- [`references/procedures.md`](references/procedures.md): P0 to P11 with full code, test path and
  status.
- [`references/expert-notes.md`](references/expert-notes.md): principles by expert, disagreements,
  deciding conditions.
- `references/critique.md`, [`references/gui-paths.md`](references/gui-paths.md),
  [`references/sources.md`](references/sources.md): rubric, GUI paths, sources.
- [`scripts/ue_perf.py`](scripts/ue_perf.py): plans, captures, CSV and Insights readers, diagnosis,
  suspect trees, config writers, proof, audits.
