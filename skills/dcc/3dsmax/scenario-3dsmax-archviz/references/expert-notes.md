# Expert notes: archviz production

Principles and judgment by expert, each with its source and timestamp. Items marked [added] are this
skill's, not an expert's. Numbers are as shown on screen or spoken; see sources.md for credentials.

## Arch Viz Artist (Agnieszka Klich and team): stills, interiors, aerials

Exterior start to finish, Corona 9 (IuQ7QnwSwL0):

- Eight steps behind every image: composition, camera, lighting, materials, planting, color balance,
  post, storytelling [00:00:20, 00:10:24].
- Camera: Field of View switched to Focal Length, 30 mm; target moved so main elements sit on
  thirds; automatic vertical tilt after moving the target; DOF f/4 [00:00:20 to 00:01:57].
- HDRI is steered by rotating the map on Z; an overexposed sun disc is checked with a diagnostic
  exposure, not fixed [00:02:19 to 00:03:31].
- Separate the lighting environment from the visible background: Direct visibility override and
  Reflections override take a darker corrected copy [00:04:27].
- Planting in six layers: hero trees by hand as proxies; out-of-frame trees for shadows that lead
  the eye; scatter for the back; a spline cutting the scatter for foreground plants; pots and hedge
  by hand; ivy grown last [00:08:51 to 00:09:52].
- "We have every color possible on the image. It doesn't look good!" Pick a harmony and hue-shift
  each material into it [00:10:24].
- Render with alpha, replace the background, add Z-depth haze, then motion blur and noise because
  renders are unnaturally sharp [00:11:16 to 00:12:23].

Interior start to finish, Corona 12 (f40Sszm3Bqk):

- Camera height about 1 m, focal 50 to 55 mm for intimacy, target slightly low for breathing room,
  f/5.6 (f/4 too blurry), clipping near plane to cut the wall [00:01:03 to 00:02:37].
- Light tests on white override materials, glass excluded, or no light enters [00:03:20].
- Sun placed by intent: what it highlights and how far it enters; larger sun and clouds for softness
  [00:03:50 to 00:04:57].
- Light Mix to lower the sun share for mood; tone mapping then fixes too dark or too orange
  [00:04:57 to 00:05:32].
- Asset placement is composition: painting off center, counterweight lamp opposite, books at uneven
  spacing, curtains to calm a bright side [00:08:49 to 00:09:52].
- Add a wire color element before the final and mask glass for window plates; alpha would show a
  horizon line [00:09:52, 00:10:52].

Exterior, Corona 13 (JmmgSQp6FYI):

- Camera 140 cm, 30 mm, automatic vertical tilt; rule-of-thirds script [00:00:11, 00:00:43].
- Sun target at ground level; lock the camera view in render settings before steering the sun in IPR
  [00:01:15].
- Season variants of trees mixed to fake a season change; exclude instances whose shadows hurt the
  image rather than redesigning the scatter [00:07:17, 00:10:03].
- Image darker after planting: fix with exposure and a tone curve, not light intensity [00:10:33].
- AI Enhancer element: noise limit 2%, render no larger than 2048 px (Corona 13 workflow figure)
  [00:11:20].

Aerial from a drone photo (iIYYzosZ1Mo):

- "Using drones in aerial visualizations it's a must"; CG-only aerials look fake for marketing
  [00:00:29].
- Early morning or late afternoon; RAW plus JPG [00:01:05].
- Output size equals photo size; focal 24 mm from the photo details with film width 35 mm; camera
  height equals drone altitude, 120 m [00:03:54 to 00:04:54]. Pairing the 35 mm-equivalent focal
  with a 36 mm film width is the exact form [added].
- Daylight System north aligned to the map, location, date and time from the photo [00:06:50].
- Surroundings only for shadows: Visible to Camera off [00:08:38].
- Composite: curves on render only, levels to paint shadows, motion blur, blur, noise, then sharpen
  once because drone software sharpens [00:09:00 to 00:10:41].

Walkthrough (e3g4boZKyFU):

- Walkthroughs are "boring and old-fashioned" but clients ask for them [00:00:00].
- Rounded corners, interpolation steps 16 then 200, Normalize Spline, eye level 160 cm, Auto
  tangents on rotation keys [00:01:29 to 00:08:32].

## render.camp (Ira Ostrovska): the general feeling stage (64vzHYEWedI)

- Before textures: gray base, HDRI from Cosmos rotated (minus 50 in the demo), two helper disks,
  flat color per area, tone mapping [00:04:23 to 00:40:04].
- Helper lights are copies, not instances, so intensities can differ; disks for emphasis instead of
  a sun when the mood is not sunny [00:12:09, 00:13:14].
- Big areas (walls, floor) control the warmth and contrast of the whole image [00:20:10].
- No pure white or black albedo; brightness hierarchy is composition [00:27:26, 00:28:00].
- Weaken a texture by lowering its amount, never by editing the bitmap [00:59:08].
- Bump and displacement darken color and read only under directional light; re-tune color after
  [01:18:10, 01:33:52].
- Texture by importance: foreground first, background little, ceiling none; rugs last [00:38:12,
  01:42:58].
- Judge bump and displacement only on a pre-final render (10 to 15 min) [00:45:59].
- "Don't compare to other renders, compare to photos" [02:11:14]. Save numbered versions because
  clients change designs [02:17:55].
- She says never import SketchUp or Revit and always remodel [02:16:16]; this is her school's rule.
  The Revit link sources disagree (see CGI MADE SIMPLE). Deciding condition: link when the BIM stays
  live, remodel when frozen and texturing needs clean geometry.

## Chaos (V-Ray channel): complex exteriors with Chaos Scatter (8s2gF4vb6yk)

- Few similar species, unified hue, saturation and value [00:01:43].
- Source pivots at trunk base; Align to minimum Z [00:02:16].
- Normal versus Z 1 keeps trees upright on slopes; small X and Y tilt; random scale under 100%
  [00:03:21, 00:03:58].
- Closed splines for include and exclude; Edit Poly test for closure; Near equal to Far expands
  without falloff [00:04:30, 00:05:36].
- Per-square distribution keeps density constant when the target changes; avoid collisions trades
  spacing for density (40% forest) [00:06:57, 00:07:17].
- Far grass: enlarge the patch by random scale instead of multiplying count; edge trimming at roads
  [00:08:45, 00:09:18].
- Grass color from a Surface Color texture, kept low and blended with the original [00:09:55].
- Cars: 1D scatter on splines, spacing 10 m, jitter 80%, direction rotation about 90, reverse wrong
  segments [00:11:53 to 00:13:32].
- Lister to manage about 14 scatters [00:14:01].
- Cryptomatte plus an exposure layer in the VFB fixes one species or the cars after render
  [00:14:53].
- Horizon: duplicate the forest scatter onto copied ground and enable camera clipping [00:15:59,
  00:16:36].
- Before instancing Volume Grids, disable volume light cache and big-grid optimization [00:19:54].

## iToo Software: lawns with Forest Pack (_0MeIRhEQI4) and the rendering best-practice doc

- Layered lawns: base plus cloned overlays; intersections are seldom visible [00:05:29].
- Large presets (60 cm patches) for most work, never rotated; Detail presets for close-ups
  [00:03:12, 00:12:36].
- Higher Density value thins an overlay [00:07:39]. Mown: Z 40 to 50% [00:09:19].
- Stripes are a reflection effect: map in midground (150 cm, planar world), geometry in close-up
  [00:09:38 to 00:13:38].
- Raise or zero Max Items for Detail presets [00:15:50].
- Doc: fill large areas with dense maps and higher density values; pre-composed larger patches for
  huge scenes; viewport Max Items caps display; material in Material Override; background plants
  with reflection depth about 1; avoid refraction with opacity; proxies only when RAM is short;
  randomize X and Y translation against a grid look; alpha leaves: opacity filtering off for stills,
  alpha slightly smaller than the diffuse against halos; Edge mode needs a Forest Edge map in
  Opacity for Corona and Arnold (forestpack-rendering-best-practice).

## renderdrop: Vantage animation (gMUKCmaeQhc)

- Corona scene to V-Ray via the Scene Converter, then to Vantage [00:00:10].
- Relight for animation: all lights off, back one by one, about half intensity [00:02:12].
- Read the memory estimate in the Vantage render dialog before launch (about 3.1 GB on a 9.2 GB
  card) [frame 00:08:15].
- Every look as a sub-state (environment, lighting, color) bundled in Scene States [00:02:49].
- Soft interior: CIE Overcast sky 2.25, sun 0.05 [00:01:35].
- Linear transitions and a consistent Move Speed [00:05:12]; the sun moves through the end camera's
  scene state [00:05:56].
- Render: Ultra, 250 samples, GI 4 bounces, reflections and refractions 15, firefly filter off,
  motion blur off, Reduce flickering on, PNG sequence; 727 frames at 26.5 s on one GPU [00:07:54 to
  00:08:59].
- AI video for architecture (1A7uOdk9Sng): start and end frames must share identical geometry; see
  scenario-3dsmax-generation.

## Simeon Balabanov: camera grammar (uyQi4YIwVag)

- Five moves: pan or tilt, truck or pedestal, dolly, zoom, focus [00:11:11].
- Linear for truck and pedestal; chains of linear moves suggest scale; Quad In for an opening dolly;
  ease in and out for focus [00:04:34 to 00:09:48].
- Level the camera before saving a shot [00:02:16]. Small zooms: render big and crop in post
  [00:08:23]. A pause after a cut [00:10:21].

## Ross Plemya: Anima people (ZHCVMQeWPEg)

- Animated people read as fake close up: keep them at distance [00:01:01].
- Hide everything except architecture and ground before sending to Anima [00:04:06].
- Same fps (30) in both tools; re-sync after every change; nudge drift in top view [00:06:36,
  00:07:10].
- Noise limit 3 to 4% for animation; strip reflection from foliage and metal to stop flicker
  [00:08:07, 00:11:11].
- Vary speed and motion phase [00:11:32]. Budget: frames x minutes per frame / 60 [00:09:01].
- Speaker sells a farm and a course; treat farm times as vendor claims.

## Silver Colored Lens: the camera-angle method (oKYzIh7KfH0)

- Analyse the feature, define the story, select the angle by meaning, iterate [00:00:00 to
  00:02:23].
- "Sometimes the best shot comes after 10 bad ones" [00:02:08].

## VizCourse: Connecter asset manager (mbi-7pTItcU)

- Naming drives the library: same base name stacks formats, `_V1` stacks versions, map-role words
  fill PBR slots [00:28:30 to 00:42:16].
- Preview studio and assets in the same unit with the pivot at base center [00:53:06].
- Never Remove in Manage External Files; Replace, Rename or Set Path [00:15:03].
- Replace Target swaps a placed object in place for a client's other chair [01:29:37].

## Intake sources (detail in scenario-3dsmax-scene)

- CGI MADE SIMPLE (cv7bIWciFU4): Link FBX combined by Revit material, 49 objects versus 384; Reload
  survives client changes; bind only when frozen [00:04:31, 00:05:06, 00:07:52]. Keep 3ds Max
  material assignments on reload before texturing [frame 00:06:39]; light in 3ds Max rather than
  import Revit lights [00:06:16].
- Revit and FBX link settings doc (`file-link-revit-fbx-settings`): Combine Entities is set only in
  a preset, never on reload; the Daylight System link prompts for exposure control and No gives
  overexposed renders; Revit FBX export makes every light instance unique.
- Master ArchViz (SRVCuw9aPI8): instances, proxies and XRefs cut file size but raised render time in
  single runs (8m49s to 11m31s for proxies) [frame 00:01:50, f_00175]. Proxy export: store
  materials, Reset XForm if scaled, attach with Match Material IDs to Material, about 5,000 preview
  faces [00:05:26 to 00:06:31].
- studioGAD (sQiA1X4XlMw): group SketchUp parts and match millimeters before export [00:00:33 to
  00:03:25].

## Chaos Corona: AI concept loop (2WmOd4C5r7s)

- AI images from a rough render feed a mood board; the 3D scene is still built by hand and not
  copied exactly [00:02:10]. Architecture must not change in prompts [00:01:04]. Generation belongs
  to scenario-3dsmax-generation.

## Disagreements and deciding conditions

| Question                      | Choice A                            | Choice B                                        | Decide by                                |
| ----------------------------- | ----------------------------------- | ----------------------------------------------- | ---------------------------------------- |
| HDRI or Sun and Sky           | HDRI for a specific sky             | Sun for direction, caustics, photo-matched time | IuQ7QnwSwL0, iIYYzosZ1Mo                 |
| Window background             | alpha plus photo                    | wire color glass mask                           | interior glazing shows a horizon         |
| Real plate or CG aerial       | drone photo                         | full CG                                         | marketing image versus landscape concept |
| Chaos Scatter or Forest Pack  | Chaos-only pipeline, Cosmos presets | masterplans, biomes, wider tools                | studio pipeline and cost                 |
| Vantage or offline animation  | GPU fits, look survives conversion  | full material fidelity, farm                    | GPU memory and conversion loss           |
| Meshes or proxies for scatter | meshes when RAM allows              | proxies when RAM is short                       | Forest Pack doc                          |
