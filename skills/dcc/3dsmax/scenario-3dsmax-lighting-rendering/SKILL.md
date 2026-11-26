---
name: scenario-3dsmax-lighting-rendering
description: "Use when lighting or rendering in 3ds Max with Arnold, V-Ray 7 or Corona: \"my render is noisy\", fireflies, blotches, flicker in an animation, a render that takes too long, washed-out, crushed or yellow renders, blown-out windows, ACES or OCIO looking wrong, double tone mapping, HDRI or sun and sky setup, interior day or night lighting, studio or product lighting, LightMix or light groups, render elements and AOVs, Cryptomatte masks, which denoiser, rendering big and downscaling, render settings or test renders by script, or estimating render time and cost before a long render."
license: MIT
---

# 3ds Max lighting and rendering

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit.

Expert level here means light first and settings second, every noise problem traced to its cause,
one tone mapper, and every long render priced before it starts. The agent judges renders from saved
images with numbers (noise sigma, clipped percent, detail ratio, seconds per frame) and then by
looking at 100 percent crops. If a sibling skill named here is missing from your available skills,
load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit,
current-3ds-Max traps).

## Stance (the expert delta)

1. **Inherit the renderer and the color mode; never switch either silently.** A renderer switch
   leaves VRayMtl, Corona and Arnold materials and lights untranslated [added]. Color mode is a
   project decision: a Corona trainer runs Gamma 2.2 (VizAcademy UK, hz07nIgm7EA 00:28:56), HM
   Studio runs OCIO with ACEScg (qt7FB4UU0qg 00:01:40). Keep what the scene has; propose a change in
   the report.
2. **Light on clay first, glass still transparent.** Override every material with one gray material
   that preserves refraction and opacity, or the windows block the sun (Chaos, x8H1CNNFPgc 00:03:31;
   Arch Viz Artist, hPZvijDCV-M 00:03:41). Turn the override off before the final (4MeUNMFxiPE
   00:05:50).
3. **One tone mapper.** With OCIO the ACES view transform is already tone mapped: no exposure
   control, no filmic layer, no tone-map imager on top (Autodesk, dlwDiLsPWgI 00:04:39; qt7FB4UU0qg
   00:07:35). In a Gamma 2.2 scene the filmic layer sits above exposure (qt7FB4UU0qg 00:08:41).
   Exposure lives on the camera; auto exposure is for reading a value, then you type it in
   (x8H1CNNFPgc 00:05:47).
4. **Find the noise source before adding samples.** Arnold Camera (AA) multiplies every other sample
   count and rays are the square of the setting: AA 4 casts 16 camera rays (Arnold docs, Removing
   Noise). Isolate with AOVs or by zeroing one ray type; only DOF and motion blur need more AA. In
   Corona leave the Performance tab at defaults unless a named problem asks (Corona docs; Aga,
   _biqhqTpW5c 00:10:35).
5. **Render once, decide later, and only dim in the mix.** Set lights white and bright at render
   time; LightMix multiplies, so brightening there adds noise and artifacts (V-Ray 7 VRayLightMix
   docs; Chaos, 4MeUNMFxiPE 00:05:16). Change brightness on the light object. Enable every light
   before IPR or the render starts, or it never reaches the mix (4MeUNMFxiPE 00:04:43).
6. **Stop on a measured criterion and denoise only converged images.** Corona noise limit 3 percent
   for finals, 2 for demanding shots (_biqhqTpW5c 00:03:13); V-Ray noise threshold from 0.005 (Aga,
   7Q3GqtJ56OQ 00:01:22). For stills under time pressure, render at 2x with a 20 to 30 percent noise
   limit, Intel AI denoise, then halve the size: 7 min against 41 min in Chaos's demo (1bOmROFahXU).
   Walls lose fine reflections first.
7. **Animation is a flicker problem.** Anything moving besides the camera means brute force GI or a
   flicker-free cache; camera-only fly-throughs can reuse cached GI from file (7Q3GqtJ56OQ 00:00:39,
   00:04:13).
8. **Price the render before launching it.** Time one test frame at a known size and noise, scale by
   pixels and frames, and report hours against the budget before a final or a sequence [added].

## Establish first

- **Renderer in use**: `renderer_info()` from [scripts/maxkit_render.py](scripts/maxkit_render.py)
  reads `renderers.current` and classifies it as arnold, vray, corona or other. Arnold ships with
  3ds Max; the saved docs do not state which renderer a new scene defaults to.
- **Color mode and rendering space**: OCIO (ACEScg rendering space) is the default for new scenes
  since 2025; older or studio-standard scenes may be Gamma 2.2. Read it, do not assume it.
- **Release and versions**: 3ds Max update, MAXtoA, V-Ray or Corona build, GPU vendor and driver
  (Arnold GPU and OptiX need an NVIDIA driver newer than 582.16/580.126).
- **Deliverable**: still or sequence, final pixel size, format (EXR for post, PNG or JPEG for direct
  delivery), deadline, render budget per frame, local or farm.
- **Scene scale**: light sizes and distances below assume centimeters; check the system unit
  (scenario-3dsmax-scene).
- **Channel**: batch for unattended audits and renders; bridge for live work inside one undo;
  mcp-safe for read-only audits with [scripts/mxs/render_audit.ms](scripts/mxs/render_audit.ms)
  (whether `render` passes Safe MAXScript is not documented); handoff otherwise.

## Procedure

1. **Inspect.** Run `renderer_info`, `output_settings`,
   `prop_dump(renderers.current, SETTING_KEYWORDS)`, `render_elements`, `lights_report`,
   `color_report` through `max_wrap.wrap(..., kit=["audit"])` with the domain module inlined.
   Renderer property names are not in any saved doc (Corona and V-Ray included): discover them here
   and set only names this dump returned (`set_props`, dry run first). Read the camera class with
   `classOf` (procedures.md 5). GATE: JSON report holds renderer family, size, color mode evidence,
   element list and every light with its on state. Unknown names are listed, not guessed.
2. **Color pipeline before materials and lights.** Confirm mode, rendering space and output policy:
   EXR stays in rendering space for compositing; bake a view transform only for direct delivery
   (dlwDiLsPWgI 00:03:26). List data maps (normal, roughness, height) whose color space is not Raw
   and hand them to scenario-3dsmax-materials. GATE: no exposure control or tone-map layer on top of
   an OCIO view; zero data maps tagged as color.
3. **Lighting pass on clay.** Enable the renderer's material override (keep refraction and opacity),
   pick the recipe in [references/procedures.md](references/procedures.md): interior day, interior
   night (dim large blue sun as moon, warm practicals), exterior (sun and sky for direction and
   caustics, HDRI for a specific sky), studio. A low sun is warm: sun color mode override gives
   neutral light, the size multiplier softens shadows (x8H1CNNFPgc 00:06:20); rotate an HDRI on Z
   only (00:13:53). Several looks from one scene (day, low sun, dusk): procedures.md 4f. Render 960
   px tests with `test_render`. GATE: `render_metrics.py exposure`: clipped under 1 percent outside
   windows and practicals, crushed under 2 percent, median luminance 0.18 to 0.45 on the display
   image [added thresholds]. Visual: one shadow direction, sun patch where intended.
4. **Exposure and white balance on the camera.** Read auto exposure once, type the rounded value
   onto the camera, keep white balance there; no second tone mapper. GATE: same exposure numbers on
   a second test; whites read neutral at 100 percent.
5. **Render elements.** Light mix (V-Ray `VRayLightMix`; Corona one `CShading_LightMix` plus one
   `CShading_LightSelect` per group; Arnold light-group AOVs), Cryptomatte, the denoiser element
   when the final needs it, data passes the compositor asked for. Save layers through the renderer's
   own output (V-Ray layers are lost through the Common tab output). Cryptomatte rules (previews are
   not mattes, `.cxr` is EXR, ID masks suffice without blur): procedures.md 10. Once the mix is
   approved, write it back to the lights (V-Ray To Scene after the render stops; Corona LightMix
   bake button) so scene and image agree. GATE: `render_elements()` lists each; every light belongs
   to a group or to Rest.
6. **Noise triage at the problem area.** Render a region or a 1/4-size test; measure `noise` per AOV
   or per crop; raise only the setting tied to the cause (table in
   [references/procedures.md](references/procedures.md)); repeat at most three times [added], then
   change approach (light the dark area, enlarge the light, raise roughness). GATE: worst-tile sigma
   within 1.5x the median tile sigma, no isolated fireflies in the brightest crop [added
   thresholds].
7. **Estimate, then final.** `render_metrics.py estimate` from the test time; if over budget, choose
   render big plus AI denoise plus downscale, a higher noise limit, or a time limit. Render the
   final to a new versioned file; save the renderer's layered file too. Corona: untick "Clear VFB
   between renders" before a time-budgeted final you may stop and resume (_biqhqTpW5c 00:13:34).
   Memory for large and 2x finals: procedures.md 8. GATE: estimate within budget before launch;
   after: `detail_ratio` of denoised against a low-noise crop at least 0.85 [added]; crops of four
   corners, center and brightest area reviewed.
8. **Animation only.** Choose GI by motion, lock or unlock the noise pattern deliberately, render a
   10-frame test at low size and run `flicker`. GATE: `jumps` empty; walls and ceilings do not crawl
   when the frames are played.

## Numbers

| Value                       | Setting                                                                                   | Relative to                          |
| --------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------ |
| Corona noise limit          | 3 percent final, 2 demanding, 20 to 30 with 2x render and Intel AI                        | Corona 6 to 14                       |
| Corona denoise amount       | 0.65 default, 0.85 for the 2x method                                                      | Intel CPU/GPU AI mode                |
| Corona Performance defaults | GI vs AA 16 (range 2 to 64), light samples 2.0, MSI 20, ray depth 25                      | Corona docs; _biqhqTpW5c frame 10:45 |
| V-Ray noise threshold       | 0.005 start, test per scene                                                               | Bucket or Progressive                |
| V-Ray Bucket example        | min subdivs 1, max 24, bucket 48, min shading rate 6                                      | 7Q3GqtJ56OQ frame 1:28               |
| V-Ray light cache           | 2000 subdivs still (x8H1CNNFPgc), 1500 animation (7Q3GqtJ56OQ)                            | V-Ray 6 to 7                         |
| Arnold Camera (AA)          | 4 to 8; DOF example AA 15 with diffuse 1, specular 1                                      | rays = setting squared               |
| Arnold light samples        | 3 to 4 usually enough                                                                     | per light or GLS                     |
| Moon (V-Ray Sun)            | intensity mult 0.02, size mult 8, blue filter                                             | 4MeUNMFxiPE frame 00:05:00           |
| Studio key / fill / rim     | 60 at 60x60 cm / 10 at 100x100 cm / 200 at 35x35 cm, 8000 K                               | Corona units, hPZvijDCV-M            |
| Day interior camera         | EV about 10.5 in EV mode; ISO 100, f/8, 1/200 is EV100 13.6, a different setting: use one | x8H1CNNFPgc frames; EV math [added]  |
| GI pre-pass spacing         | every 25th frame exterior, 5th to 10th interior                                           | V-Ray IM plus LC fly-through         |

## Quality gates

- **Measurable:** renderer family unchanged unless the user asked; override off for final; render
  hidden lights and render-only-masks off; output size and path versioned; noise criterion set
  (limit, threshold or time limit) and not 0 for finals; Intel AI denoiser never with the High
  Quality image filter (Corona needs Tent); elements present; estimate logged against budget; sigma,
  clipped and crushed percentages within the procedure gates.
- **Visual (open the saved files, not the frame buffer):** 100 percent crops of corners, center and
  brightest area: fireflies on glossy metal, smeared wood grain or fabric after denoise, lost
  reflections on walls, blown windows, black corners, double shadows from the fill, rim card visible
  in frame, banding in the sky. For sequences, a contact sheet of every 10th frame plus the locked
  flicker test.

## Common mistakes

| Mistake                                       | Symptom                             | Fix                                                                                                                             |
| --------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Filmic or exposure layer over an ACES view    | crushed highlights and shadows      | remove it, or set view to un-tone-mapped first                                                                                  |
| Override material without preserve refraction | dark interior, no sun through glass | preserve refraction and opacity, or exclude glass                                                                               |
| Raising AA for GI noise                       | time up, noise unchanged            | raise the sample type the AOV points to                                                                                         |
| Brightening in LightMix                       | noise, artifacts                    | brighten the light, re-render, dim in mix                                                                                       |
| Light enabled after IPR start                 | missing from LightMix               | stop, enable, restart                                                                                                           |
| Denoising an unconverged render               | smudges, lost texture               | lower noise limit, keep amount below max                                                                                        |
| Visible sky lights the window view            | flat white or overbright view       | V-Ray: dome Invisible, HDRI in Environment; Corona: Scene tab environment override for direct visibility (_biqhqTpW5c 00:09:29) |
| Fill as strong as the key                     | double shadows                      | fill larger, about one sixth of key, no own shadow (hPZvijDCV-M 00:05:14)                                                       |
| Relighting to fix brightness                  | balance lost                        | exposure and tone curve; material brightness via ColorCorrection map (JmmgSQp6FYI 00:03:24)                                     |
| Irradiance map with moving objects            | flicker, blotches                   | brute force or flicker-free cache                                                                                               |
| Saving through Common tab with V-Ray          | layers missing                      | save through the V-Ray output (EXR or vrimg)                                                                                    |
| Stopping Corona with Clear VFB on             | passes lost, no resume              | untick Clear VFB between renders first                                                                                          |
| Reset settings between scene states           | frame buffer wiped                  | reopen the scene instead                                                                                                        |

## Handoffs

- **Receives** from scenario-3dsmax-scene: units, cleaned hierarchy, missing maps resolved. From
  scenario-3dsmax-materials: materials in the scene's renderer with correct color spaces. From
  scenario-3dsmax-archviz: camera, composition and the shot list.
- **Delivers** to scenario-3dsmax-archviz: EXR with light mix and Cryptomatte, metrics JSON, time
  estimate. To scenario-3dsmax-scripting: farm or batch render tooling requests.
- **Generated inputs**: an HDRI or 360 sky enters through scenario-3dsmax-generation (Scenario MCP
  with `scenario-skyboxes`); light it here like any HDRI. Image edits, relights or upscales of a
  render go out the same way, with a Cryptomatte matte as the mask.
- **FX**: volumes and tyFlow renders come from scenario-3dsmax-fx; this skill owns their sampling.

## Current 3ds Max notes

From `sources/3dsmax-version-deltas.md` and the saved docs.

- **Color:** OCIO is the default for new scenes since 2025; Gamma Workflow stays selectable and is a
  studio choice, with no prompt when OCIO is active. OCIO 2.5.1 in 2027, 2.5.2 in 2027.2; a missing
  OCIO config keeps saved settings (2027.2); bitmap `colorSpace:` works only under OCIO. HM Studio
  shows automatic texture conversion in 2026 (qt7FB4UU0qg 00:01:40).
- **Arnold Viewport (2027.3, MAXtoA 5.9.5.0):** Arnold inside a viewport label, GPU with DLSS and
  CPU fallback, 1/2 resolution by default, settings in `MAXtoA.ini`; imagers (denoise, tone map) not
  applied; no region render; one interactive Arnold session at a time. Not in 2025 or 2026: use
  ActiveShade or RenderView there.
- **MAXtoA 5.9.x (2027 to 2027.3):** per-light `sampling_mode` local; `asset_searchpath` replaces
  texture and procedural search paths; simple bloom deprecated; Cryptomatte `object_split_instances`
  off by default; Live Report; Frame Time Limit, pause and resume, custom AOVs (5.9.5.0); ARNOL_2027
  licensing. 2026 (5.8.0) added `transmission_shadow_density` for glass shadows.
- **V-Ray 7:** irradiance map called deprecated, brute force plus light cache is the path; Light Mix
  consolidates Cosmos luminaires (7 Update 2). **Corona:** several LightMix elements since Corona
  12; "Save 50%" is a Corona 14 preview label.
- **Gaussian splats (2027.2+):** Arnold renders and relights them; V-Ray and Corona do not yet.
- **Script renders:** close Render Setup first; a modal dialog (including a Units Mismatch from
  `maxstart.max`) blocks a scripted render; an Arnold render can crash 3ds Max, so save a versioned
  copy first. In 3dsmaxbatch 2027.3 every Arnold render crashed: render Arnold in a live session.

## References

- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps,
  disagreements and their deciding conditions.
- [references/procedures.md](references/procedures.md): full code for inspect, color audit, clay
  pass, recipes, elements, noise triage, estimate, final, animation.
- [references/critique.md](references/critique.md): rubric with thresholds and what to look for in
  crops and sheets.
- [references/gui-paths.md](references/gui-paths.md): menus and frame buffer panels for the same
  work.
- [references/sources.md](references/sources.md): every video and doc with credentials and best
  timestamps.
- [scripts/maxkit_render.py](scripts/maxkit_render.py),
  [scripts/render_metrics.py](scripts/render_metrics.py),
  [scripts/mxs/render_audit.ms](scripts/mxs/render_audit.ms).
