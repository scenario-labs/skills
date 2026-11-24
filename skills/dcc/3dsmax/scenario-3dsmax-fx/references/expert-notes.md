# Expert notes (scenario-3dsmax-fx)

Principles and judgment by expert, with video id and timestamp. `[frame]` means read from a video
frame; `[doc]` means a saved tyFlow or Chaos page; `[added]` is this skill's own addition. Values
from tyFlow beta builds (0.16xxx, 2019 to 2022) are starting points: tyFlow 2.x changed bind
stiffness (2.004) and Property Test comparisons (2.100, 2.101).

## Jesse Pitela, RedefineFX (tyFlow and Phoenix trainer)

Car through a wall, GZMWapJe7eM (2019, tyFlow beta):

- Iterate against a proxy activator box linked to the car; swap in the real car parts at the end
  with Hull Type Mesh. A full-res car slows even tyFlow [00:01:06, 00:20:25].
- Nothing simulates until a Surface Test (distance to the activator) hands wall particles to the
  PhysX event; otherwise the wall falls on its own [00:03:38, 00:04:18].
- The test distance is the blast radius: 200 cm gave a local hole; 500 cm was not enough for the
  wall; 700 cm brought the whole wall down [00:05:28, 00:17:47].
- Glue binds with a force break give a mix of whole chunks and shattered ones; pure Voronoi looks
  like glass. Force is "a random number that you have to play with": 15,000, then about 177,000
  [00:05:28, 00:06:02].
- One event per fragmentation tier, each with its own Voronoi, PhysX Shape and PhysX Collision.
  Property Test thresholds are art-direction dials: Velocity Magnitude 15, then 25; Radius 15 (10
  sends more pieces on) [00:07:09 to 00:12:50].
- Re-add the collider to every new event's PhysX Collision [00:08:09].
- Heavy debris comes from friction 0.8, not from mass alone [00:08:09]. Panel values [frame
  f_00554]: restitution 0.15, damping 0.05, mass relative to volume with target 1000, exponent 1.5,
  min 0.1, max 100; convex hull max verts 255.
- Big chunks get few Voronoi points (5 to 10) with 50% variation; reusing one Voronoi setup makes
  tiers look alike [00:15:34].
- Ground hits: Surface Test distance to the ground (10 cm was not enough, 20 cm worked) with the
  output side switched [00:13:24 to 00:16:07].
- A thin part of the collider (a car antenna) injects velocity and over-fractures: remove it or
  collide it separately [00:20:57].
- Color each event to read the graph during playback; render needs a Mesh operator under every event
  [00:19:17].

33 tyFlow tips, DokFcrFyln0 (2023, tyFlow 1.011):

- No Mesh operator, no render; Instance Material set to inherit from object carries materials
  [00:02:37, 00:03:04].
- Fuse radius removes intersections; Position Object separation spreads particles evenly [00:03:28].
- Texture-driven scatter: Position Object density by texture and Scale by texmap; white maps to 0%,
  black to 100% [00:06:46 to 00:07:18].
- Paste instanced operators share settings; "make unique" separates them [00:01:30].
- Cloth Bind "add shell to surface" gives thickness and outer, inner and edge material IDs
  [00:04:46].
- Physics Bind plus Spline Paths in physics bindings mode shows the bind network [00:05:47].

## CJ Aguilar, IMAHIKA VFX

Detail by impact, U6pMAa2vckw (2020, no speech, frames only):

- Keep the dynamic sim cheap; cache it with Export Particles (now Particle Export) to tyCache,
  reload with Birth Flow in a second flow, then Subdivide and Displace only where a Surface Test
  says the activator is near [frames 00:04:37 to 00:06:35].
- Wall held with PhysX Switch Kinematic until the Surface Test fires [frame f_00160].
- Rigid (Joint) bind: swing spring 100,000, damping 250; twist 7,500, damping 250; scale with
  particles on [frame f_00160].
- Voronoi cap faces: Override cap MatID 2, Generate cap UVs, Normalize, Smooth cap faces, Optimize
  slice borders [frame f_00117].
- Displace strength 2.54 cm along vertex normals [frame f_00373].

## fabien escudero (3D and motion artist)

Cloth and reveal, Xf8q28fdRWk (2022, tyFlow beta):

- Cloth quality comes from time step, collision radius and a second physics layer more than from the
  CUDA solver [00:02:30, 00:03:45].
- Chair penetrations: time step 1/4 and time scale 0.6 first (lower for complex meshes) [00:01:50].
  Gravity -0.1 [00:01:18].
- No CUDA: Collision absolute radius 0.6 and Particle Physics (stiffness 0.5, collide radius 0.5 to
  0.4 to 0.145) [00:03:36 to 00:04:56].
- "If you increase the subdivision don't forget to decrease your collide radius" [00:06:46].
- Turbulence strength keyed 5 to 0 over about 15 frames gives organic folds that then settle
  [00:05:42].
- Black backfaces: Shell about 0.04, not flipped normals [00:06:15].
- Reveal: Object Test with Event Age > 90, Object Bind to an animated Point, Mass operator with a
  very high value to stop distortion [00:07:34 to 00:09:19].

Ocean with foam, 6Y0VwM0mnHE (2023, Phoenix textures, V-Ray):

- No simulation: Phoenix Ocean Texture as V-Ray displacement on a 5,000 m plane; units in meters
  first [00:00:04, 00:02:51].
- Change Rate of Change whenever Wind Speed control changes (0.5 halves speed) [00:03:56].
- Foam is a VRayBlendMtl coat over the water; foam amount is mostly Birth Threshold (0.5 to 0.1);
  Pattern Strength 0.85; underwater foam 0 [00:05:20 to 00:08:23].
- HDRI plus VRayEnvironmentFog (distance 2000, height 100 m) adds depth [00:10:38].
- Phoenix is End-of-Support [doc]: these textures work in 3ds Max 2027 but are frozen. MaxFluids got
  about 10% faster in 3ds Max 2026; no 2027 statement exists (version-delta file).

## edstudios (tyFlow and motion-graphics tutor)

Excavator digging, tWhQLc5IDXQ (2022):

- Simulate only the patch the bucket touches [00:01:39].
- Fake digging with Birth Voxels from an airtight volume, a Surface Test (inside the bucket) and
  Delete [00:04:12]. Open cutters leave voxel islands; bridge the edges on a copy [00:04:44].
- tyMesher Blobmesh, then tyConform to the ground; dense retopology before conforming [00:05:35 to
  00:08:05].
- Re-import a baked Alembic before using it in the next sim, otherwise it is "dramatically slower"
  [00:09:31].
- Debris: Birth Intersections, Shape layers, PhysX with Hull Type Mesh; bounce 0.15, friction
  0.5/0.5 [frame 00:11:06].
- Particle Alembic reached about 116 GB [00:14:09].

## Eloi Andaluz Fullà (VFX artist, monthly 3ds Max news)

ZENITH and Inferno overview, BsMh7JpNmVk (2026-03, tyFlow PRO 2.000):

- Temperature units Normalized: 0 absolute zero, 1 room temperature, 5+ fire; Kelvin when the data
  leaves 3ds Max [00:02:40, 00:03:14].
- Resolution is mostly voxel size in Birth Inferno [00:08:21]. Hardware: CUDA RTX, over 6 GB VRAM;
  spilling to RAM slows hard [00:00:34].
- A 0..1 noise needs strength 5 to ignite [00:12:45]. Smoke from fire: Inferno Density by
  temperature, threshold 5 to 10 [00:14:01].
- Collider emission thickness 1 leaves a gap; lower it [00:15:40]. Stir without blocking with a
  motion-only emitter [00:17:31].
- Forces scale by density, temperature or velocity, so wind can hit fire and spare smoke [00:20:10].
- Particles cannot be processed in the Inferno event: Inferno Spawn to another event, Inferno
  Properties for fluid velocity [00:24:30, 00:25:35].
- Sticky emission on a moving object needs a Texmap on an explicit map channel [00:33:13].

3ds Max 2027 news, pjwGWsS3GIg (2026-03): ZENITH demo of 320 frames and 189 million voxels in 44 s
on an RTX 3080 [frame 00:14:07]; free tyFlow has no VDB export, but previews, flipbooks and particle
advection work [00:19:11].

## Svetlin Nikolov (ZENITH developer, formerly Phoenix)

Arnold native rendering, d6Htujb3A0E (2026-08, Max 2027.1, tyFlow 2.010):

- The Arnold Volume Parameters rollout appears only after Arnold is the renderer and one render ran
  [00:00:33].
- No light, black volume; an Arnold Skydome light is enough [00:01:07, 00:08:52].
- Presets: Default (Blackbody) only for untouched defaults; tyFlow Ramps builds a Standard Volume;
  tyFlow Ramps (OSL) matches the viewport best and may be slower [00:03:55, 00:05:37].
- Presets do not refresh: after an Inferno Display change, click the preset again and render
  [00:06:27].

## Chaos (official channel)

Phoenix basics part 1, LZpv4QdkCJU (2022, Phoenix 5):

- Simulation and render settings are separate; caches hold only simulation data; save shading as a
  .tpr preset [00:08:50, 00:20:42].
- Minimum setup: simulator, source, emitter (liquids can fill a grid or geometry) [00:12:47].
- Simulations are sequential: no jumping to the last frame, no distributing over machines
  [00:05:25]. Restore continues from the backup frame [00:06:07].
- Geometry inside a simulator is an obstacle by default [00:14:31]. Status [doc]: End-of-Support
  since April 2026; still inside V-Ray Premium and Collection and Corona Premium and Collection;
  final releases support 3ds Max 2027.

## Michal Wojcie, VizAcademy UK

MassFX quick sims, TXTXLsDvCRo (2021):

- Use MassFX for natural placement (logs, books, blankets), not as final animation [00:05:24].
- Concave containers: Shape Type Custom, then Original; Convex intersects [00:03:12 to 00:04:17].
- Multi-Object Editor switches many props from Capsule to Convex [00:06:59].
- Bake Selected writes keys; Ctrl+Z resets an unbaked sim [00:04:17].
- mCloth panel [frame 00:03:25]: density 50, damping 0.5, friction 0.5, self collision thickness
  about 2.27.

## Denis Keman, dkcgi

Rugs with Hair and Fur, MnJhmI35554 (2015):

- Hair and Fur renders only through an Effects entry with a render mode other than Buffer
  [00:02:05].
- Rug fiber: root thickness 5, tip 0, scale 20 to 30, count 10,000 then 50,000; clump 80 at 0.6; 5%
  mutant color [00:04:20 to 00:11:58].
- Region render to test, full render to confirm [00:06:35]. Comb fibers up out of the floor, never
  down [00:14:29].
- Geometry mode takes the base mesh material; the modifier's colors apply only in the old mental ray
  Prim mode [00:17:59]. [added] mental ray is gone, so Geometry is the route now.

## Andrew Krivulya for Ephere (Ornatrix 9)

TTlRWRjisXw (2025-11): Create Brush hairstyles need Collapse To Baked Guides before clumping by
guides; Ox Filter (Precision Even) cuts guide count while keeping the shape [00:00:08 to 00:01:30].
Ornatrix compatibility with 3ds Max 2027 is not confirmed in the saved sources.

## Kyle, Simulation Lab

Rigging crash course, Pgzy2_HxH2w (2021): tyFlow hair that follows a body uses Object Bind lock to
surface; a static copy is a Mesh operator (Render Only off), Tools > Snapshot, then Skin Wrap
[01:09:09 to 01:11:48].

## Arch Viz Artist (Anna)

Satisfying loop, uBw0nmIYHok (2022): loops are keyframes, not sims. 24 fps, 4 s, end frame 95; key
to frame 96 then set the end back to 95; Ping-Pong for swings, Relative Repeat for spins [00:01:04
to 00:04:55]. Hand loop rigs to scenario-3dsmax-animation-rigging.

## Where experts disagree, and the deciding condition

- Glue or Joint: Pitela uses Glue with force break; Aguilar uses Joint; the PhysX Bind doc prefers
  Joint with very high stiffness when Glue goes degenerate. Decide by stability at the fragment
  count you need.
- CUDA cloth or Particle Physics: CUDA when an NVIDIA GPU and time allow; Particle Physics with a
  small radius when iteration speed matters (Xf8q28fdRWk 00:02:30).
- Proxy or real collider: proxy during setup, Mesh hull (or SDF since 2.000) for the final.
- Ocean: displacement texture for open water; a simulator only when objects interact with it
  (Phoenix guide). Phoenix is frozen either way.
- ZENITH units: Normalized inside 3ds Max, Kelvin for export.
