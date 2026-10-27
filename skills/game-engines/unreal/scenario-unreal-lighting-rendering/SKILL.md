---
name: scenario-unreal-lighting-rendering
description: 'Use when lighting or rendering in Unreal Engine 5.8: physical light units and exposure (EV100, lux, lumens), a sun, sunset or dusk rig, Lumen GI and reflections, MegaLights, virtual shadow maps, sky, fog and clouds, a generated or HDRI sky as sky light cubemap, post process and color grading, the path tracer, or Movie Render Graph stills, by Python or through Epic''s MCP toolsets. Triggers: "the frame is white" or black, "exposure does not match the sun", "Lumen is noisy", "MegaLights noise", "the interior is too dark", "light leaks", neon signs, "fireflies", "path tracer vs Lumen", "render a still", EXR settings. Also when a light property set through MCP fails or reads back wrong, a cvar name is unsure, or a frame must be measured rather than eyeballed.'
license: MIT
---

# Lighting and rendering in Unreal Engine 5.8

Expert lighting in Unreal is a calibrated camera, physical light values, and a renderer that sees
the same scene you do; everything else is art direction layered on top and listed as such. Each step
is proved with a representation view and a number before the lit image is trusted; noise is fixed in
the system that owns it. If a sibling skill named here is missing from your available skills, ask
the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed
from tool schemas and flag the gap.

**REQUIRED BACKGROUND:** scenario-unreal-expert (channels, review loop, 5.8 traps). Epic's in-editor
DefaultOutdoorLighting skill, read through `ToolsetRegistry.AgentSkillToolset`, agrees on the
component rule, the pitch convention and leaving the sunset color to the atmosphere; where it
differs, the 5.8.3 runs below decide (see "Epic's outdoor skill, checked").

**Status (2026-10-21):** what ran in Unreal and what did not:
[`references/sources.md`](references/sources.md).

## Stance (the expert delta)

- **Camera before lights.** Default auto exposure "childproofs" the engine: a 10 lux and a 100,000
  lux sun look alike. Chrome ball at the subject, Exposure Compensation 0, Min/Max EV100 clamped to
  the conditions, then lights; emissive last (Gobey nlbJwMoj1Dg [00:02:38] [00:11:40]; Faucher
  BGoaPyfZlYg [00:01:34]). Judge through Game Settings exposure, never the viewport EV100 override
  (Gobey [00:21:56]).
- **Physical values remove problems; cheats go on top and in the report.** Real lumens removed about
  80 percent of Lumen flicker (Argyriou Q1whHlGJB_o [00:14:41]); albedo is lighting, at most 0.8,
  floor 0.02 [added] (path tracer doc; Gobey [00:07:30]; Faucher X5zVhc5ahl0 [00:22:24]). Every
  light has a visible fixture and a source shaped like it (Faucher 0GYyHDuaPcg [00:15:14]
  [00:15:47]). Moons, fills and boosts are fine when listed (`cheat_inventory`); the path tracer
  ignores them.
- **Emissive is the look, lights do the lighting.** Small bright emissive is noisy, screen-space and
  clamped harder since 5.6 (`r.Lumen.ScreenProbeGather.MaxRayIntensity` 10): a neon sign gets a rect
  light fitted to its face, in front of it (Faucher 1e6oOiKh91U [00:12:30]; Gobey Q&A [00:37:33];
  MegaLights doc). Under Lumen, small emissive meshes get Emissive Light Source, optionally a
  Lumen-only boost of 5 to 10 through a Ray Tracing Quality Switch (not yet run) (Campbell
  BKaAzhMHJZ0 [00:14:09]); the path tracer ignores that switch and double counts a tube plus its
  light (path tracer doc).
- **The renderer sees a proxy; look at it.** Lumen Scene and Surface Cache (black = screen traces
  only, pink = no cards, often a one-mesh room), MegaLights shadow caster mismatch, VSM cached
  pages, each against the lit view from the same camera (Faucher [00:07:21] [00:06:42]; Lumen,
  MegaLights, VSM docs).
- **MegaLights noise is stolen samples, not light count.** Hidden lights take up to 20 percent of
  samples (50 after failed reprojection), a directional up to 50. Tight radius, cones, barn doors,
  no light inside geometry, clusters merged, the sun on deferred plus VSM (Narkowicz and Costa
  dmmN8_c8Tb0 [00:10:37] [00:16:40]).
- **Shadow method follows what moves.** Local lights stay ray traced in gameplay: every character
  crossing a VSM local light invalidates its pages, while ray tracing pays per visible pixel with
  free penumbras (Campbell [00:26:25] [00:31:42]). VSM for the sun and for content ray tracing
  cannot represent, with a written reason.
- **A dark interior is a tone-mapper problem first; light before you grade.** Toe 0.55 to 0.3 and
  Local Exposure Shadow Contrast 0.6 before any fill (Gobey [00:14:58] [00:15:32]); then the ladder:
  direct light, one light's indirect boost, Diffuse Color Boost, global exposure last (Faucher
  0GYyHDuaPcg [00:08:14] [00:13:42]).
- **For the still, the path tracer is ground truth and samples are its only quality knob.** On the
  deferred path, samples buy motion blur and anti-aliasing only; Lumen or shadow noise is fixed at
  the light or the PPV (Faucher X5zVhc5ahl0 [00:07:43]; fVg5ihB8Wdc [00:09:15]; Comly,
  demystifying-mrq).

## Establish first

| Input                                            | Changes                                               | Default when silent                                                                                                           |
| ------------------------------------------------ | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Platform, frame rate                             | Lumen scalability, MegaLights, HWRT                   | console 60 fps: Lumen High; budgets from scenario-unreal-performance; Mac numbers are proxies                                 |
| What this Mac runs (probe)                       | every plan                                            | Apple silicon, macOS 26.5.1: Lumen HWRT and MegaLights Experimental, Nanite and VSM Beta, path tracer supported (deltas file) |
| Deliverable                                      | exposure mode, still plan                             | gameplay plus one still; direct delivery (tone-mapped PNG plus EXR)                                                           |
| Conditions the player walks between              | EV100 bracket                                         | `CONDITIONS`: interior 4, blue hour 6.5 [added], low sun 7, moonlit 1                                                         |
| Style                                            | physical vs art-directed moon and sun                 | physical base; film moon and a 15 degree sun floor only for readability (Faucher; Oakley rX0wZZxpB-U [00:19:16])              |
| Key cameras; glass and emissive fixtures in shot | fog scattering, cheats, glass and double-count audits | bookmarks from the brief; front layer only in a PPV around hero glass                                                         |

## Workflow

**MCP first:** lights, sky, fog, PPV, cvar checks and read-backs go through the toolsets with the
JSON in [`references/mcp-lighting.md`](references/mcp-lighting.md); four or more toolset calls in a
row go through ONE `ProgrammaticToolset.execute_tool_script` script (define `run()`, call
`execute_tool(name, json_string)`, return a dict; imports json, math, re, time, datetime, copy
only), as its S1 to S5 scripts do. A failing tool aborts the script and cannot be caught inside it:
keep expected failures as single calls. Level creation, console variables, screenshots and the frame
meter go through editor Python (`import ue_light as L`; full code in
[`references/procedures.md`](references/procedures.md)). Screenshots are latent: one capture per
call, and turn each view off before the next.

0. **Sun and exposure, measured (P3b; mcp-lighting S1, section 4).** Predict EV100 from the sun with
   the transmittance measured on 5.8.3: `ev100_for_sun(lux, elevation)` (120,000 lux: 14.4 at 45
   degrees, 9.7 at 5), lint with `exposure_check`, write Manual with EV100 = minus the compensation,
   capture with `VIEW_MODES["buffer_dump"]`, read the ground on the host with
   `meter_pretonemap(<shot>_PreTonemapHDRColor.exr, ev100, regions)`, set the measured EV100,
   capture again. Sunset color: the atmosphere reddens a low sun by itself (ground light at 5
   degrees measured (0.24, 0.10, 0.026)), so the light's own tint stays mild: when the brief asks
   for warm light, Use Temperature on at 4,500 to 5,500 K (never 6,500 or white, never deep orange);
   read it back. GATE: gray card within half a stop, no `all_white` or `all_black`, one sun, one sky
   light, one unbound PPV (counted with `find_actors`).
1. **Probe and settings (P0, P1).** `probe()`, `render_settings_report`, `ini_patch` after a backup;
   extended luminance range only in a new project. Read
   `r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange` first: it depends on how the project
   was made (0 in the 5.8.3 test project). At 0, Auto Min/Max Brightness are luminance (defaults
   0.03 and 8), not EV100, so EV100 numbers written there blow the frame out (arena h03: 9.5 to
   11.5, floor 20 times too bright). Then use Manual, or Min = Max = 2^EV100 (engine source, not
   metered). GATE: probe JSON read.
2. **Calibrate the camera (P2).** `spawn_calibrator` at the subject, then one unbound `PPV_Global`:
   `apply_exposure(ppv, exposure_plan("gameplay", ("interior", "blue_hour")))`, `apply_look` (Local
   Exposure mandatory with Lumen GI; Film only here). GATE: `ppv_lint` no fail; HDR view shows each
   target inside the clamps.
3. **Exterior (P3).** `build_exterior_rig(exterior_rig_plan("blue_hour", key_camera_forward=...))`:
   Sky Atmosphere, sun at 120,000 lux below the horizon, real-time Sky Light, volumetric fog with
   black inscattering, Scattering Distribution from the key camera's angle to the light (0.9 into
   it, 0 from the side: Faucher 1LfiYtKDsac [00:16:06]). Steady lamps scatter above 1 for halos,
   flickering ones 0. GATE: `scene_lint` clean; sun out of MegaLights.
4. **Practicals, neon, openings (P4, P5).** `FIXTURES` lumens and kelvin, radius from
   `tight_attenuation_radius` capped by the room, source shaped like the fixture, one rect per
   shelf, `neon_sign_light`, `opening_rect_light`; emissive via `emissive_for_stops` and
   `emissive_strategy`. GATE: `light_lint` no warn, or a written reason.
5. **Does the renderer see it (P7 to P9).** Lumen views vs lit; `room_shell_lint` on pink;
   MegaLights dump and mismatch view; masked casters; VSM cached pages. GATE: no black or pink where
   light must bounce; no hidden light in the dump; VSM red share near 0; noise judged in motion.
6. **Look (P10).** Ambient shape first, then the focal hue, then "the promise of more": light
   leaving the frame, a lit side street (Oakley [00:07:34] [00:09:19] [00:08:44]); the shadow-lift
   ladder in order; grade last; white-balance direction by A/B screenshot. GATE: `frame_report` B3
   to B8.
7. **Review loop (P11, P12).** Per bookmark: `log_mark`, capture,
   `frame_report(frame, brief, log_text=log_since(...))` on the host, one change, logged in
   `iterations.jsonl`; glossy regions hold a highlight; walk the player path for adaptation.
   Timings: P12's measure preset, `profilegpu_passes`, to scenario-unreal-performance. GATE: no
   fail.
8. **The still (P13).** Audit first: `albedo_check` on `<shot>_BaseColor.exr`,
   `emissive_fixture_pairs` (A/B `r.PathTracing.EnableEmissive 0`), `glass_lint`. Then
   `still_plan(...)`, `mrg_lint` clean, `set_cine_camera_exposure`, `queue_mrg_still`; still-only
   cheats on their own lighting channel (`still_only_light_plan`). Offline: gray card within 1/3
   stop, `compare_ground_truth`; a render unlike the viewport walks `RENDER_DIFF_TRIAGE`. GATE: C1
   to C11 of critique.md.
9. **Handoff (P14).** `lighting_manifest(path, ctx)`: lights, PPVs, lint, cheats, emissive pairs,
   masked casters, cvars.

## Numbers

| Item                                               | Value                                                                                                                                                                                 | Relative to, source                                 |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Sun, moon                                          | 120,000 lux at zenith (0.545 degrees); moon 0.26 lux                                                                                                                                  | Epic sky doc                                        |
| Look targets (EV100)                               | sunlit 14, cloudy 10, low sun 7, interior 4, moonlit 1, moonless -2                                                                                                                   | Gobey chart [00:12:02]; targets, not meter readings |
| Fixtures                                           | candle 12 lm 1,900 K; decorative 300; interior 1,000; exterior 10,000; street 2,500 to 10,000 lm                                                                                      | Gobey chart; Argyriou [00:13:36]                    |
| Units                                              | 1 cd = 625 unitless = 12.6 lm (point) = 3.14 lm (rect) = 1.76 lm (spot, 44 degrees)                                                                                                   | exposure doc                                        |
| Exposure                                           | Manual: EV100 = camera EV - compensation, camera EV = log2(N^2 / t x 100 / ISO) or 0 without physical camera; PreTonemapHDRColor pixel = L / 2^EV100 x 0.99; default compensation 1.0 | exposure doc; run on 5.8.3                          |
| Sun on the ground (SkyAtmosphere, 120,000 lux sun) | 101,700 lux at 90 degrees, 68,000 at 45, 18,500 at 15, 2,600 at 5, 450 at 2; the real-time sky light added about 1 stop at 5 degrees                                                  | run on 5.8.3 (`SUN_TRANSMITTANCE_583`)              |
| Defaults                                           | spawned sun 10 lux, Stationary, temperature off; 10 lux at 35 degrees gives 4.96 lux on a 0.18 floor                                                                                  | run on 5.8.3                                        |
| Cached lighting range                              | `r.EyeAdaptation.CachedLightingPreExposure` 4 covers EV100 about -8 to 12, 8 covers -4 to 16                                                                                          | 5.8.3 console help                                  |
| Auto exposure                                      | Low 70 to 80, High 80 to 95 percent; Speed Up 3 above Speed Down 1                                                                                                                    | exposure doc; Gobey frame [00:21:52]                |
| Albedo                                             | 0.02 [added] to 0.8 path traced, 0.9 Lumen                                                                                                                                            | path tracer doc; Faucher 1e6oOiKh91U [00:13:35]     |
| MegaLights                                         | 20 percent of samples to hidden lights (50 after failed reprojection); sun up to 50                                                                                                   | SIGGRAPH [00:10:37] [00:16:40]                      |
| Path-traced still                                  | 1 temporal, spatial 256 draft to 1024 or more final; glass 10 bounces; Max Path Intensity default                                                                                     | path tracer doc; Faucher X5zVhc5ahl0 [00:16:47]     |

## Quality gates

- **Measurable:** `ppv_lint`, `light_lint`, `scene_lint`, `glass_lint`, `room_shell_lint`,
  `mrg_lint`, `cvar_lint` without fail; `frame_report` on every bookmark with the log since capture
  (blank frames and the exposure-range warning fail); `albedo_check` on the Base Color buffer; gray
  card from linear EXRs; `compare_ground_truth` within a stop outside listed cheats; `red_fraction`
  on the VSM cache view; `temporal_flicker` on warm-ups.
- **Visual:** each bookmark full size and as a thumbnail beside its representation views; a camera
  move for noise; inner corners for leaks; glossy highlights; the still at 100 percent; in the order
  of [`references/critique.md`](references/critique.md).

## Common mistakes

| Mistake                                                                             | Looks like                           | Fix                                                 |
| ----------------------------------------------------------------------------------- | ------------------------------------ | --------------------------------------------------- |
| Sun lux and a compensation from a table, no frame read                              | white or black frame                 | `ev100_for_sun`, Manual, meter, correct (step 0)    |
| Sunset tinted hard on top of the atmosphere, or left white when the brief says warm | over-saturated orange, or a cold sun | 4,500 to 5,500 K; read it back                      |
| Lighting under default auto exposure                                                | any value "looks fine"; flicker      | `exposure_plan`, comp 0, then physical lights       |
| Neon lit by emissive only                                                           | splotchy, crawling GI                | rect light per sign; Emissive Light Source          |
| Many small lights, big radii, a sun indoors under MegaLights                        | noise and ghosting in motion         | tight bounds, merge clusters, sun on VSM            |
| One mesh for the whole room                                                         | pink surface cache, screen-space GI  | split walls, floors, ceilings; Max Lumen Mesh Cards |
| Fill lights to rescue a dark interior; grading first                                | flat, view-dependent GI              | toe and local exposure, then the ladder; grade last |
| Render differs from the viewport, cvars pasted                                      | "the render is broken"               | `RENDER_DIFF_TRIAGE`: Global Game Overrides first   |

Full table: `references/critique.md`.

## Epic's outdoor skill, checked (run on 5.8.3)

- **Default sun.** Its "Unreal defaults about 100 to 150 lux": a spawned DirectionalLight is 10 lux.
- **Sunset sun.** Its 300 to 1,000 lux reads as the sun's Intensity. With a SkyAtmosphere the
  atmosphere already dims a low sun (transmittance 0.25 at 5 degrees), so dimming the light as well
  darkens twice: keep the sun near its zenith value and meter the ground (a 120,000 lux sun at 5
  degrees gave about 5,200 lux on the floor, sky included).
- **Exposure without Min/Max.** Its table pairs a direct sun with compensation -10 to -14. In an
  extended-range project with auto exposure and no Min/Max, -10 to -14 rendered black; the same
  compensation with Manual is EV100 10 to 14, which matches only a high sun. Derive EV100 from the
  sun and meter instead of using a table.
- **Agreed:** properties on the component, never the actor (the actor call fails); pitch 0 horizon,
  -90 overhead; a mild temperature at sunset because the atmosphere does the reddening.

## Handoffs

Receives the level, room volumes (`room`), fixture tags (`fixture:<name>`) and emissive masters;
delivers `lighting_manifest.json`, the exposure plan and still presets to
scenario-unreal-cinematics, light counts and passes to scenario-unreal-performance. Full list:
`references/procedures.md`, Handoffs.

## UE 5.8 notes

- Python: the Rotator's positional order is roll, pitch, yaw (run on 5.8.3), so `ue_light` passes
  keywords.
- Scripted captures: `viewmode <x>` did nothing in a `take_high_res_screenshot`; ShowFlag overrides
  did (`VIEW_MODES`, off is `2`). `r.BufferVisualizationDumpFrames 1` writes BaseColor (linear),
  PreTonemapHDRColor and a dozen G-buffer files beside the shot. ProfileGPU prints a box table to
  LogRHI (`profilegpu_passes` reads it).
- More 5.8 notes (MegaLights, Lumen Lite, ACES 2.0, MRG):
  [`references/expert-notes.md`](references/expert-notes.md).

## References

- `references/mcp-lighting.md`: intent to tool, signatures, the S1 to S5 scripts with their
  read-backs, the measurement loop, when Python instead. Load before any MCP call.
- [`references/generated-skies.md`](references/generated-skies.md): an equirect panorama as
  TextureCube, sky light and backdrop; orientation table, cubemap angle, sun light, seam and
  exposure checks.
- `references/procedures.md`: P0 to P14, full code, each block with its test id and status. Load
  before writing lighting code.
- `references/critique.md` (rubrics, load at every gate, full mistakes table), `expert-notes.md`
  (per expert, 5.8 notes), [`gui-paths.md`](references/gui-paths.md) (menus), `sources.md`.
- [`scripts/ue_light.py`](scripts/ue_light.py): the toolkit; its docstring lists every call.
