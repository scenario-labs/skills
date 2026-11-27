---
name: scenario-3dsmax-archviz
description: "Use when producing an architectural visualization in 3ds Max from an architect's model to delivered stills or animation: exterior or interior renders, a Revit, SketchUp or DWG model to turn into marketing images, camera angles and composition, two-point perspective, \"my render looks fake\" or \"looks CG\", a client brief or revision round, material or season variants, scattering trees and grass with Forest Pack, RailClone or Chaos Scatter, lawns, entourage from Chaos Cosmos, people with Anima, matching a drone photo for an aerial, a walkthrough or Chaos Vantage animation, render time per frame, or a heavy exterior scene that no longer moves in the viewport."
license: MIT
---

# 3ds Max Archviz Production

Target line: 3ds Max 2027.3 on Windows, driven through the scenario-3dsmax-expert channels and
toolkit.

Expert level here means running a commission like a studio: every image answers a brief, the camera
is signed off before anything is dressed, and every heavy step is budgeted in numbers before it
runs. This skill owns production order, decisions and checks; lighting, materials and scene cleanup
detail go to the siblings. If a sibling skill named here is missing from your available skills, load
it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-3dsmax-expert (channels, review loop, toolkit,
current-3ds-Max traps).

## Stance (the expert delta)

1. **Camera and story first, dressing last.** Both Arch Viz Artist start-to-finish videos run
   composition, camera, light, materials, planting, color balance, post in that order (IuQ7QnwSwL0
   00:00:20; f40Sszm3Bqk 00:00:31). Silver Colored Lens: pick the angle for its meaning and expect
   about ten bad angles before the good one (oKYzIh7KfH0 00:01:39, 00:02:08). Never populate an
   unapproved view.
2. **Block the "general feeling" before any texture.** One gray base material, HDRI plus two helper
   lights, flat color per big area, tone mapping (render.camp, 64vzHYEWedI 00:15:01). Walls and
   floor set warmth and contrast because they fill the frame (00:20:10). No pure white or pure black
   albedo: the brightest surface becomes the focus (00:27:26).
3. **Compare to photographs, not renders** (64vzHYEWedI 02:11:14). Renders are unnaturally sharp;
   finish with slight motion blur and noise (IuQ7QnwSwL0 00:12:23).
4. **Few species, one palette.** Pick visually similar trees and unify hue, saturation and value
   before scattering (Chaos, 8s2gF4vb6yk 00:01:43). Push every material into one color harmony
   (IuQ7QnwSwL0 00:10:24).
5. **Many small scatters, driven by guide splines.** One scatter per purpose (forest, lawn, wild
   grass, cars, road edge), each with include and exclude splines, managed in a lister (8s2gF4vb6yk
   00:14:01). Scatter for mass and background; hand placement for foreground and hero plants
   (IuQ7QnwSwL0 00:08:51).
6. **For distance, scale the source, not the count.** Enlarge grass patches with random scale and
   trim them at area borders (8s2gF4vb6yk 00:08:45). In Forest Pack, fill large areas with a dense
   map and higher density value rather than a sparse map (forestpack-rendering-best-practice doc).
7. **Real plates beat CG for aerials.** Match the drone photo from its metadata; add surroundings
   only for their shadows (Arch Viz Artist, iIYYzosZ1Mo 00:00:29, 00:08:38).
8. **Measure frame one, then decide the engine.** Frames x seconds per frame before pressing render:
   727 frames at 26.5 s in Vantage is about 5.3 h; 90 frames at 15 min in Corona is 22.5 h
   (renderdrop gMUKCmaeQhc 00:08:59; Ross Plemya ZHCVMQeWPEg 00:09:01).

## Establish first

Ask in one round, then run:

- **Deliverables:** number of stills, aspect and pixel size, animation length and fps, real-time or
  offline, delivery date, number of revision rounds included.
- **Brief and references:** mood, time of day, season, target buyer; two or three real photos per
  view. With no references, ask before proceeding unattended.
- **Model source:** Revit, SketchUp, DWG, FBX; linked or frozen.
- **Renderer and plugins installed:** V-Ray 7, Corona, Arnold; Forest Pack, RailClone, Chaos
  Scatter, Chaos Cosmos, Anima, Vantage. Plugins decide the scatter and entourage path; Arnold is
  bundled.
- **Site data:** north, address or coordinates, survey levels, drone photos and their EXIF.
- **Channel:** from `max_env.doctor()`. Default to `handoff` when no 3ds Max is reachable. Defaults:
  system unit centimeters or millimeters as the architect delivered (do not rescale silently);
  stills 3000 px on the long side for review and the agreed size for finals [added]; 25 or 30 fps,
  matched to every external tool.

## Procedure

Unattended, every client GATE stops the run: return the pending approval request and start no later
step.

**1. Brief and reference board.** Write a one-page brief per view: story, feature to show, light,
season, palette. Gather real photographs as references. Concept or mood variants from a clay render
go to scenario-3dsmax-generation (one line in the brief: which views, which mood). GATE: the client
approves the brief and the view list in writing.

**2. Intake.** General hygiene (units, layers, origin, CAD cleanup, XRefs) goes to
scenario-3dsmax-scene. The link-time decisions stay here (P0; GUI only, no documented script
control):

- Revit: FBX from a 3D view; set Combine Entities in the preset before attaching (a reload cannot
  change it).
- Daylight System prompt for exposure control: answer Yes, or renders come out overexposed.
- Revit FBX turns light instances into unique lights: link with Lights off and light in 3ds Max.
- Use Scene Material Assignments on Reload: decide before texturing; off, a reload re-applies Revit
  materials.
- DWG: Rescale with the incoming units set; closed polylines on their own layers. Then run the
  archviz audit (P1; `archviz_audit.ms` on mcp-safe). GATE: units match the source, object count at
  the scene skill's target, zero missing maps, light count recorded, exposure control on if a
  daylight system arrived.

**3. Cameras and the angle method.** For each view: analyze the feature, define the story, choose
the angle by meaning (low for power, aerial for context, wide for space), then iterate
(oKYzIh7KfH0). Script 4 to 8 candidates per view with `maxkit_archviz.make_camera` (metric
positions, focal, auto vertical tilt), render clay previews with `capture.render`, and build one
contact sheet with `max_review.contact_sheet` (P2). Use the heights and focal lengths in Numbers.
GATE (visual): verticals straight, main feature on a third line, horizon placed on purpose, nothing
cropped awkwardly. GATE (client): camera sign-off on clay frames.

**4. General feeling pass.** Clay plus mood: HDRI rotated before adding helper lights, one gray
base, flat colors per area, tone mapping. Material and light settings come from
scenario-3dsmax-materials and scenario-3dsmax-lighting-rendering. GATE (visual): squint test; the
brightest area is the intended focus; light and dark masses read like the reference.

**5. Light and materials.** Siblings own the settings. This skill enforces order: hero and
foreground first, background barely, ceiling last (64vzHYEWedI 00:38:12); rugs and displacement last
(01:42:58). GATE: pre-final render at higher resolution before judging bump and displacement
(64vzHYEWedI 00:45:59).

**6. Site, vegetation and scatter.** Build planting in layers: hero trees by hand as proxies,
background masses by scatter, a spline cutting the scatter where foreground plants go, hedges and
pots by hand, climbers last (IuQ7QnwSwL0 00:08:51). For each scatter: pivots at base
(`pivot_base_report`), guide splines closed (`spline_closed_report`), Normal versus Z at 1 for
trees, slope limit, edge trimming at hardscape, camera clipping on large areas (P4). Lawns: a large
base preset, cloned overlay layers with high density values, stripes by map in midground and by
geometry only in close-up (iToo, _0MeIRhEQI4). Plant species, textures and HDRIs that would be
bought: hand generation to scenario-3dsmax-generation, then pivot and scale checks here. GATE
(measurable): scatter inventory complete, viewport display capped, sources as meshes unless RAM is
short. GATE (visual): no grid look, no hard edge at area borders, no trees on cliffs or in roads,
species colors harmonious.

**7. Entourage and people.** Library assets from Chaos Cosmos (geometry arrives as VRayProxy, HDRIs
as a Dome Light) or an asset manager such as Connecter; Replace Target swaps a placed chair for
another in place (mbi-7pTItcU 01:29:37). People sit on a third line and stay far from camera in
animation (JmmgSQp6FYI 00:11:04; ZHCVMQeWPEg 00:11:32). For Anima: send only architecture and
ground, match fps, re-sync after every path change (P9). GATE: people scale against a 2.1 m door
[added], feet on ground, speeds varied.

**8. Aerial photo match.** Render size equals the photo size; focal from EXIF; camera height equals
drone height above the site; north from the map; sun date and time from EXIF; surroundings
shadow-only (P6, `archviz_plan.py exif`). GATE: render overlaid on the photo with shadows continuous
at the seam.

**9. Animation.** Shot grammar from Simeon Balabanov: pan or tilt, truck or pedestal (linear), dolly
(Quad In for an opening), zoom (focal only), focus pull (ease in and out), a pause after a cut
(uyQi4YIwVag). In 3ds Max, walkthroughs ride a normalized spline with high interpolation steps
(e3g4boZKyFU). In Vantage, looks live in sub-states bundled into Scene States, and a moving sun is a
different environment state on the end camera, not keys (gMUKCmaeQhc 00:05:56). Time math with
`archviz_plan.py shots` and `budget` (P7, P8). Before Vantage: relight one light at a time at about
half intensity; check the memory estimate. GATE: one test frame timed, total budget accepted, 10
consecutive frames checked for flicker.

**10. Revisions and variants.** Save every round as a new numbered file; never overwrite an approved
state. Material, season and palette variants are separate scene states or files rendered from the
same cameras (P10). Image-level variants for a quick client choice go to scenario-3dsmax-generation.
GATE: before and after contact sheet per change, client choice recorded with the image version.

**11. Delivery.** Final settings, render elements for post (Cryptomatte, wire color for glass masks,
Z-depth, light mix), output names, archive (P11). GATE: no modal dialog risk (missing files, unit
mismatch), final frames opened and inspected at 100%.

## Numbers

| Item                   | Value                                                                                    | Relative to               |
| ---------------------- | ---------------------------------------------------------------------------------------- | ------------------------- |
| Interior camera height | about 1 m                                                                                | f40Sszm3Bqk 00:01:03      |
| Interior focal         | 50 to 55 mm, f/5.6                                                                       | Corona Camera, 36 mm film |
| Exterior eye camera    | 1.4 m, 30 mm                                                                             | JmmgSQp6FYI 00:00:11      |
| Exterior hero (pool)   | 30 mm, f/4                                                                               | IuQ7QnwSwL0 00:00:50      |
| Walkthrough eye level  | 1.6 m, spline steps 16 to 200                                                            | e3g4boZKyFU               |
| Vertical social video  | 40 mm, 1080 x 1920                                                                       | gMUKCmaeQhc 00:01:02      |
| Aerial                 | EXIF 35 mm-equivalent focal, altitude (120 m example)                                    | iIYYzosZ1Mo               |
| Chaos Scatter trees    | Normal vs Z 1; collisions spacing 40%                                                    | 8s2gF4vb6yk               |
| Cars on 1D spline      | spacing 10 m, jitter 80%                                                                 | scene in meters           |
| Camera clipping extend | 5 m example                                                                              | Chaos Scatter doc         |
| Forest Pack lawn       | 60 cm patches, never rotated; mown Z 40 to 50%                                           | _0MeIRhEQI4               |
| Striped lawn map       | 150 cm real-world                                                                        | planar world XYZ          |
| Noise limit            | 5% still; 2% before AI Enhancer; 3 to 4% animation                                       | Corona                    |
| Vantage animation      | 250+ samples, GI 4, refl/refr 15, flicker reduction on; 26.5 s/frame is GPU, not offline | gMUKCmaeQhc               |

## Quality gates

Measurable:

- `camera_report()`: every view camera has a set focal, auto vertical tilt on (exteriors), height in
  its band.
- `scatter_inventory()`: every scatter on a named layer; sources pass `pivot_base_report`; area
  splines pass `spline_closed_report`.
- `anim_report()`: fps equals Anima or Vantage fps; range equals the agreed length; numbered output
  path set.
- Budget: `render_budget` hours under the deadline with margin.
- Asset tracking clean before any batch render (modal dialogs stop scripted renders). Visual (from
  `capture.render` and contact sheets):
- Composition on thirds, verticals straight, focus is the brightest area.
- Vegetation: no repetition, no floating or sunken instances, edges trimmed, palette unified.
- Aerial: shadow continuity and matched sharpness and grain.
- Animation: no flicker on static areas, steady move speed, no pops at scatter borders. The full
  rubric is in [critique.md](references/critique.md).

## Common mistakes

| Mistake                                                             | Symptom                                    | Fix                                                |
| ------------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------- |
| Dressing before camera sign-off                                     | rework of planting and props               | clay sign-off first                                |
| Default field of view, no tilt fix                                  | converging verticals                       | focal set, auto vertical tilt                      |
| Many species, raw colors                                            | vegetation reads fake                      | 2 to 3 similar species, unify HSV                  |
| One huge scatter                                                    | slow, hard to edit                         | one scatter per purpose                            |
| Trees follow slope                                                  | leaning trunks                             | Normal vs Z 1                                      |
| Open guide spline                                                   | scatter ignores the area                   | Edit Poly test, weld                               |
| Camera clipping without extend                                      | missing shadows and reflections            | Extend view                                        |
| Viewport count read as render count                                 | density surprise                           | test render (Max Items caps display)               |
| Animated sun by keys in Vantage                                     | jumps, rework                              | end-camera scene state                             |
| Still settings reused for animation                                 | flicker                                    | per-engine flicker settings, no foliage reflection |
| fps differs between tools                                           | timestamp warning, drift                   | one fps everywhere                                 |
| Proxy every scattered mesh                                          | render time up (8m49s to 11m31s, one test) | meshes unless RAM is short                         |
| Material on the Forest object                                       | ignored                                    | Geometry rollout > Material Override               |
| Details and sources: [expert-notes.md](references/expert-notes.md). |

## Handoffs

- **Receives** from scenario-3dsmax-scene: a clean scene (units, layers, origin, XRefs, missing-map
  report); link presets are set here (P0).
- **Delegates** look settings to scenario-3dsmax-materials and scenario-3dsmax-lighting-rendering
  (render elements, light mix, sampling).
- **Delegates** walkthrough camera rigs beyond a path to scenario-3dsmax-animation-rigging.
- **Delegates** generated plants, furniture, people, HDRIs, backplates, textures and mood variants
  to scenario-3dsmax-generation; this skill checks pivot, scale and palette on arrival.
- **Delivers** stills, sequences and a per-view sheet (camera, focal, height, version) to the user,
  and scripted batch renders through scenario-3dsmax-scripting when the job is large.

## Current 3ds Max notes

From `sources/3dsmax-version-deltas.md` and the archviz digests.

- 2027.3 MCP server limits: a modal dialog (missing files, units mismatch, including a
  `maxstart.max` in other units) stops scripted renders; reading a Batch Render view's camera
  crashes 3ds Max; an Arnold render can crash it: save first.
- 2027.2 adds the Point Instance modifier (render-time instancing; 2027.3 adds viewport and render
  limits), a native option when no scatter plugin is installed.
- 2027.2 imports Gaussian splats; only Arnold renders them, so splat backgrounds need Arnold or a
  baked plate.
- OpenPBR is the default material since 2026; VRayMtl's OpenPBR shading mode is not supported on
  V-Ray GPU, which matters for the Vantage route.
- Corona 8 converts legacy Corona Scatter to Chaos Scatter (renders may differ); edge trimming needs
  Corona 12. Corona 13 adds Scatter clusters, tree season variants, the AI Enhancer element and
  Vantage Animation Export.
- V-Ray 7 exports Chaos Scatter procedurally to `.vrscene`. Phoenix reached end of support in April
  2026: do not plan new volumetric scatter sources on it.
- RailClone's saved page lists 3ds Max 2013 to 2024; confirm 2027 builds of RailClone, Forest Pack
  and Anima before quoting a schedule. A farm needs the same or a newer 3ds Max.

## References

- [expert-notes.md](references/expert-notes.md): principles and judgment by expert, with timestamps.
- [procedures.md](references/procedures.md): P0 to P11 with full code, channel, source line and
  result checks.
- [critique.md](references/critique.md): the self-review rubric with numbers and capture checks.
- [gui-paths.md](references/gui-paths.md): menus and panels for the same steps, for a human or
  computer-use agent.
- [sources.md](references/sources.md): every source with URL, credential and best timestamps.
- [scripts/maxkit_archviz.py](scripts/maxkit_archviz.py): in-Max helpers (cameras, scatter
  inventory, pivots, splines, animation output, Anima prep).
- [scripts/mxs/archviz_audit.ms](scripts/mxs/archviz_audit.ms): read-only MAXScript audit for the
  mcp-safe channel.
- [scripts/archviz_plan.py](scripts/archviz_plan.py): runner-side frame ranges, render budget, drone
  EXIF to camera.
