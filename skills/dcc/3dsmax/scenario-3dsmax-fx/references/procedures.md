# Procedures (scenario-3dsmax-fx)

Names marked `[verify]` were not found in a saved doc; check them on the user's install (procedure 2
does this for tyFlow) before relying on them. Chunks set `result`; `scripts/fx_wrap.py` calls the
lead's `max_wrap.wrap()` with `kit=["maxkit_fx", ...]` and this skill's `scripts/` as `kit_dirs`;
`max_wrap` adds the undo record and the JSON result protocol (`rt`, `pymxs`, `log` and kit modules
are globals of the chunk). Recipe values assume 1 unit = 1 cm.

What is scriptable for tyFlow, per the saved tyFlow docs:

- `cache()` on a tyCache modifier (tycache doc); errors print to the MAXScript Listener.
- `enabledModifiersBelow` on a tyCache modifier exists since 2.101; its arguments are not documented
  here.
- Inferno Export modes through MAXScript: `[op].exportVDB()`, `[op].exportImages()`,
  `[op].exportFlipbook` (version history 2.100). How to get `[op]` from a flow is not in the saved
  docs.
- A MAXScript operator and a Script operator run code inside a flow; tyFlow ships a
  tyParticleObjectExt and tyVolumeObjectExt interface (version history). Their members are not in
  the saved docs.
- Everything else (events, operators, wiring, output side of a test, presets) is editor work. Never
  write `$tyFlow001.someOperator.someParam` from memory.

## 1. FX scene audit

Goal: know units, timeline, renderer, lights and every FX object before touching anything.

```python
# channel: bridge | batch | handoff
# note: wrapping checked on a runner against max_wrap.py 0.1.0 (script built and compiled)
# Runner side. fx_wrap passes maxkit_fx to max_wrap through kit_dirs.
import json
import sys

sys.path.insert(0, sys.argv[1])  # this skill's scripts folder
from fx_wrap import wrap_fx

CHUNK = 'result = {"fx": maxkit_fx.fx_audit(), "stats": stats.snapshot()}'
script = wrap_fx(CHUNK, expert_scripts=sys.argv[2], kit=["stats"], result_path=sys.argv[3])
with open(sys.argv[4], "w", encoding="utf-8") as fh:  # new file name per run
    fh.write(script)
print(json.dumps({"written": sys.argv[4]}))
```

Run the written script through the lead's `max_batch.run_batch()` with the scene (batch), through a
bridge, or hand it to the user (handoff). Every later Python chunk in this file is wrapped the same
way.

MAXScript twin for `mcp-safe` (read-only, no blocked commands):

```maxscript
-- channel: mcp-safe | bridge | handoff
-- checked against scripts/maxkit_fx.py; renderers from scripting-pipeline__pymxs-renderer-2027.md
rep = stringStream ""
format "units: % x %\n" units.SystemScale units.SystemType to:rep -- [verify] units.SystemScale, units.SystemType
format "fps: % range: % to %\n" frameRate animationRange.start animationRange.end to:rep -- [verify] frameRate, animationRange
format "renderer: %\n" (classOf renderers.current) to:rep
format "lights: %\n" lights.count to:rep
hints = #("tyflow", "tycache", "phoenix", "massfx", "mcloth", "hair")
for o in objects do (
    names = #(toLower ((classOf o) as string))
    for m in o.modifiers do append names (toLower ((classOf m) as string))
    for n in names do for h in hints where (findString n h) != undefined do
        format "fx: % | % | %\n" h o.name n to:rep
)
result = rep as string
```

Check in the result:

- System unit is not 1 cm: convert every recipe number before use; never change the unit in the
  scene.
- `phoenix` rows: legacy scene; plan new work on tyFlow ZENITH.
- tyFlow present, Arnold current, zero lights: a ZENITH render will be black.

## 2. Discover the tyFlow scripting surface on this install

Goal: list properties and interfaces the installed tyFlow build exposes, so later scripts use real
names.

```python
# channel: bridge | batch | handoff
# checked against scripting-pipeline__pymxs-using-2027.md (getPropNames)
from pymxs import runtime as rt

nodes = [o for o in rt.objects if "tyflow" in str(rt.classOf(o)).lower()]
result = [maxkit_fx.discover(n) for n in nodes[:5]]
```

Check: save the result JSON next to the scene as `fx_discovery_<date>.json`. Use a name from it only
if it appears there. If the interfaces text is empty, stay on GUI paths.

## 3. Stand-ins: activator proxy, ground, airtight cutter check

Goal: cheap colliders and test objects before any sim (Jesse Pitela, GZMWapJe7eM 00:01:06;
edstudios, tWhQLc5IDXQ 00:04:44).

```python
# channel: bridge | handoff
# checked against GZMWapJe7eM notes; scene API names [verify]
import pymxs
from pymxs import runtime as rt

HERO = "car_body"          # from the user
PAD = 1.05                 # proxy 5% larger than the hero bounding box [added]

hero = rt.getNodeByName(HERO)
with pymxs.undo(True, "fx: activator proxy"):
    bb_min, bb_max = hero.min, hero.max  # [verify] node.min, node.max
    size = bb_max - bb_min
    proxy = rt.Box(length=size.y * PAD, width=size.x * PAD, height=size.z * PAD)  # [verify] Box params
    proxy.pos = rt.Point3((bb_min.x + bb_max.x) / 2, (bb_min.y + bb_max.y) / 2, bb_min.z)
    proxy.name = HERO + "_FX_activator"
    proxy.parent = hero        # link: the proxy follows the hero animation
    proxy.boxMode = True       # Display as Box
    proxy.renderable = False   # [verify]
result = {"proxy": str(proxy.name), "size_cm": [size.x, size.y, size.z]}
```

Airtight check for a cutter or collider (open edges must be 0):

```python
# channel: bridge | handoff
# checked against tWhQLc5IDXQ notes; polyop names [verify]
from pymxs import runtime as rt

CUTTER = "bucket_FX_cutter"   # from the user
node = rt.getNodeByName(CUTTER)
copy = rt.copy(node)              # measure on a copy, the user's object stays untouched
rt.convertToPoly(copy)            # [verify]
open_edges = rt.polyop.getOpenEdges(copy)  # [verify] returns a bitarray
count = int(open_edges.numberSet)          # [verify]
rt.delete(copy)
result = {"node": CUTTER, "open_edges": count, "airtight": count == 0}
```

Check: `airtight` true. If false, bridge the open edges on a copy (GUI, Edit Poly > Bridge) and
re-run.

## 4. Build sheets (graph work for a human or a computer-use agent)

The agent writes the sheet, a human or computer-use agent builds it (paths in gui-paths.md), and the
agent checks an editor capture against it. Values are starting points from the sources; tune one at
a time.

### 4a. Destruction: car or ball through a wall (GZMWapJe7eM; docs physx-bind, voronoi-fracture)

| Event                | Operators and values                                                                                                                                                                                                                                                                                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1 Wall (gray)        | Birth Objects (wall; hide the original) > Voronoi Fracture 1,000 points, variation 100%, Cap holes on, Override cap MatID 2, Generate cap UVs on (Weld after slicing on if high-resolution slices show artifacts, voronoi-fracture doc) > Display > Surface Test distance to activator proxy, 200 cm (700 cm for the whole wall) > to Event 2                            |
| 2 Active (blue)      | PhysX Shape (friction 0.8/0.8, restitution 0.15, mass relative to volume: target 1000, exponent 1.5, min 0.1, max 100) > PhysX Bind Rigid (Glue), Breakable, Force 15,000 and up, Max breaks/frame 1 or 2 > PhysX Collision (activator) > Property Test Velocity Magnitude >= 15 > Event 3; Surface Test distance to ground < 20 cm, output side switched > Ground event |
| 3 Tier 2 (orange)    | Voronoi 30 points, 50% (or 10, 20%) > PhysX Shape > PhysX Collision (activator again) > Property Test Velocity > 25 > Event 4                                                                                                                                                                                                                                            |
| 4 Tier 3 (pink)      | copy of Event 3 (pasted operators are instances: make unique before changing values, DokFcrFyln0 00:01:30), Voronoi 20 points > Property Test Radius > 15 > Event 5                                                                                                                                                                                                      |
| 5 Big chunks (green) | Voronoi 5 to 10 points, 50%                                                                                                                                                                                                                                                                                                                                              |
| Ground (white)       | Voronoi 5 points, 50%                                                                                                                                                                                                                                                                                                                                                    |
| All rendered events  | Mesh operator; final: swap the proxy for the hero parts in every PhysX Collision, Hull Type Mesh or SDF                                                                                                                                                                                                                                                                  |

Wrecking ball variant [added]: the keyed ball is the activator; take the pendulum from
scenario-3dsmax-animation-rigging. Pre-modeled bricks: Birth Objects on the bricks, PhysX Bind by
proximity (Proximity Bind rollout, bind distance just above the mortar gap) instead of the first
Voronoi; keep the tier tests to break fast bricks. Glue degenerate: switch to Rigid (Joint) with
very high spring stiffness and raise PhysX Position Iterations (physx-bind doc).

Steps and iterations: the tyFlow object's time step sets the simulation substeps; PhysX Position
Iterations (tyFlow object, PhysX rollout) set solver accuracy for binds and are not substeps
(physx-bind doc). The saved sources give no substep value for rigid bodies: start at the default,
and lower the time step only when fast pieces pass through the collider in a capture [added].

Check before the full range: each event has its own display color and the playback shows particles
reaching the intended tier (GZMWapJe7eM 00:19:17); a Spline Paths operator in physics bindings mode
after the PhysX Bind shows where the wall will break (DokFcrFyln0 00:05:47). Remove both display
aids before rendering.

### 4b. Cache, then detail near the impact (U6pMAa2vckw frames; tycache doc)

| Flow             | Operators                                                                                                                                                   |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flow 1 Event 1   | Birth Objects > Voronoi (Cap MatID 2, cap UVs, normalize) > PhysX Shape Convex Hull > PhysX Switch Kinematic > Surface Test distance to activator > Event 2 |
| Flow 1 Event 2   | PhysX Shape > PhysX Collision > PhysX Bind Rigid (Joint), swing spring 100,000 damping 250, twist 7,500 damping 250                                         |
| Flow 1 Export    | Particle Export, type tyCache, range set to timeline, post-export action: create tyCache object                                                             |
| Flow 2 "details" | Birth Flow (the tyCache) + Flow Update > Surface Test distance to activator > Subdivide > Displace (Texmap, strength 2.54 cm, vertex normals)               |

### 4c. Cloth drape for a still: blanket and two pillows on a bed (Xf8q28fdRWk; cloth-bind doc)

| Step      | Settings                                                                                                                                                                                                                                                                                                                                                           |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Colliders | low-poly bed and mattress proxy; floor plane                                                                                                                                                                                                                                                                                                                       |
| Pillows   | cloth from closed meshes; raise Volume stiffness so they keep their volume (cloth-bind doc: volume bindings are internal struts that help cloth maintain volume; the doc gives no value, tune by preview); for seams that trip the CUDA solver, Collisions > Prevent coincident edges/faces with a very small threshold (cloth-bind doc); simulate and cache first |
| Blanket   | plane at real size, segments about 100 to 200 for blocking (300 for final), placed above the bed                                                                                                                                                                                                                                                                   |
| Flow      | Birth Objects > Cloth Bind (shape to cloth, Mass per-cloth so later subdivision keeps the mass ratio) > Force gravity -0.1 > Collision (bed proxy, pillows or their cache, floor), absolute radius 0.6                                                                                                                                                             |
| Solver    | tyFlow time step 1/4, time scale 0.6, before touching radii; Cloth Bind Stiffness Solver Constrained so stiffness stays roughly independent of step count (Simple depends on it; cloth-bind doc)                                                                                                                                                                   |
| NVIDIA    | CUDA collision solver on, self-collisions on, self-thickness below the minimum triangle spacing                                                                                                                                                                                                                                                                    |
| No CUDA   | Particle Physics, collision stiffness 0.5, collide radius 0.4 down to 0.145; lower it when segments go up                                                                                                                                                                                                                                                          |
| Folds     | Turbulence strength keyed 5 to 0 over 15 frames, scale 0.3 to 0.5                                                                                                                                                                                                                                                                                                  |
| Finish    | Cloth Bind Mesh rollout: Add shell to surface (outer about 0.04) or a Shell modifier; Relax or TurboSmooth on top                                                                                                                                                                                                                                                  |
| Still     | pick the settled frame, then procedure 8                                                                                                                                                                                                                                                                                                                           |

### 4d. Cloth reveal (Xf8q28fdRWk 00:07:00 to 00:09:19)

Animated Point helper over about 150 frames. In the cloth event: Object Test (distance to the point)
with a filter Event Age (Frames) > 90 > Object Bind (lock to object, pick the point) > Mass operator
with a very high value on the bound particles.

### 4e. Digging dirt (tWhQLc5IDXQ)

| Step          | Settings                                                                                                                                                                                                                  |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Volume        | detach the ground patch the bucket touches, extrude to depth, make airtight (procedure 3 check)                                                                                                                           |
| Flow 1        | Birth Voxels (airtight volume, voxel 5 cm, cull duplicates) > Shape Cube > Surface Test inside the airtight bucket copy > Delete                                                                                          |
| Mesh          | tyMesher Blobmesh on the flow > tyConform to the hole and ground                                                                                                                                                          |
| Bake          | Alembic export, then re-import before any second sim                                                                                                                                                                      |
| Flow 2 debris | Birth Intersections (A bucket, B re-imported Alembic) > Shape (pebbles, stones; scale 100, variation 50%) > PhysX Shape convex > PhysX Collision (bucket, ground, Alembic; Hull Type Mesh), bounce 0.15, friction 0.5/0.5 |
| Budget        | particle Alembic reached about 116 GB: cap particle count before export                                                                                                                                                   |

### 4f. Sand pouring from a truck [added; no source covers a granular pour]

Use the parts the sources do cover:

- Fill: Birth Voxels from an airtight volume that fills the tipper bed (4e logic); a Fuse operator
  (radius) removes initial overlaps before the solve (DokFcrFyln0 00:03:28).
- Stream: Particle Physics with collide radius as the main dial (as in 4c without CUDA), Collision
  with the keyed truck bed and the ground.
- Pile: tyMesher Blobmesh, then tyConform onto the ground (4e).
- Hero grains: a few PhysX pebbles from Shape layers (4e), not the whole stream.
- Settle values by preview: count, radius and friction have no source value; state that in the
  report.

### 4g. Fire and smoke with ZENITH (BsMh7JpNmVk; d6Htujb3A0E; faq-zenith doc)

| Step      | Settings                                                                                                               |
| --------- | ---------------------------------------------------------------------------------------------------------------------- |
| Domain    | Birth Inferno; resolution is mostly voxel size (0.2 tested for detail); BFECC advection saves 30% VRAM (2.100)         |
| Units     | Normalized: 1 room temperature, 5+ fire; Kelvin if a VDB leaves 3ds Max                                                |
| Emission  | Inferno Emitter; a noise Texmap 0..1 needs strength 5 to ignite; moving emitter: Texmap on an explicit map channel     |
| Smoke     | Inferno Density, emission by temperature between 5 and 10 normalized                                                   |
| Colliders | Inferno Collider; lower emission thickness from 1 to close the gap; stir only: second Inferno Emitter with motion only |
| Particles | Inferno Spawn to another event, Inferno Properties to carry fluid velocity                                             |
| Render    | Arnold: procedure 9; VDB export and rendering need tyFlow PRO                                                          |

## 5. Time a preview and extrapolate

Goal: seconds per frame from a fresh pass, then a deadline check.

```python
# channel: bridge | handoff
# checked against scripts/maxkit_fx.py; snapshotAsMesh and attime [verify]
from pymxs import runtime as rt

FLOW = "tyFlow_wall"   # from the user; reset the simulation first (GUI: tyFlow rollout, Reset)
node = rt.getNodeByName(FLOW)
result = maxkit_fx.time_evaluation(node, 0, 30)
```

Then on the runner:
`python scripts/sim_budget.py estimate --sec-per-frame <mean> --frames 150 --load-ratio 4`. Check: a
second pass returning near-zero times means the frames came from tyFlow's RAM cache; reset and
re-measure. Re-measure after each doubling of load.

## 6. Cache a tyCache modifier by script

```python
# channel: bridge | batch | handoff
# checked against fx-simulation__tyflow-tycache.md (cache())
# Mode, filename and frame range must already be set on the modifier; pick a new file name.
from pymxs import runtime as rt

nodes = [rt.getNodeByName(n) for n in ["cloth_blanket"]]
result = maxkit_fx.cache_tycache_modifiers(nodes)
```

Check: at least one entry, every entry `ok`; Listener has no tyCache error; the `.tycm` file exists.
Leave Keep cache in RAM on: off re-reads the whole cache from disk at every evaluation (tycache
doc). Modifiers below can be disabled after caching (doc); on 2.101+ the modifier's
`enabledModifiersBelow` function reports or sets that state (version history; arguments not in the
saved docs, inspect with procedure 2 first). A Particle Export cache from a flow is written by the
operator (GUI or "auto-export on render"); this function does not cover it.

## 7. Verify a cache on disk

```python
# channel: handoff (runner side, any OS)
# checked against scripts/sim_budget.py
import json
import subprocess
import sys

out = subprocess.run(
    [sys.executable, "scripts/sim_budget.py", "cache", sys.argv[1],
     "--pattern", sys.argv[2], "--first", sys.argv[3], "--last", sys.argv[4]],
    capture_output=True, text=True, check=True)
print(json.loads(out.stdout))
```

Check: `ok` true; `total_gb` logged in the report; reload in a fresh scene (tyCache object for
Particle Export caches) plays the full range.

## 8. Freeze the best cloth frame for a still

Simulation Lab (Pgzy2_HxH2w 01:10:13) bakes a flow with a Mesh operator (Render Only off) and
Tools > Snapshot.

```python
# channel: bridge | handoff
# checked against Pgzy2_HxH2w notes; snapshot and sliderTime [verify]
import pymxs
from pymxs import runtime as rt

FLOW, FRAME = "tyFlow_blanket", 92   # from the user after reviewing captures
node = rt.getNodeByName(FLOW)
with pymxs.undo(True, "fx: freeze cloth frame"):
    rt.sliderTime = FRAME            # [verify]
    frozen = rt.snapshot(node)       # [verify] needs the Mesh operator with Render Only off
    frozen.name = FLOW + "_f%03d" % FRAME
result = {"frozen": str(frozen.name)}
```

Check: face count matches the flow at that frame; capture from below shows no penetration; then
disable the live flow (do not delete it).

## 9. Render ZENITH in Arnold (d6Htujb3A0E)

```python
# channel: bridge | handoff (an Arnold render can crash 3ds Max: save first)
# checked against scripting-pipeline__pymxs-renderer-2027.md (render outputFile)
import pymxs
from pymxs import runtime as rt

OUT = rt.maxFilePath + "zenith_test_v001.exr"   # next to the saved scene; bump the version per run
if "arnold" not in str(rt.classOf(rt.renderers.current)).lower():
    rt.renderers.current = rt.Arnold()          # [verify] Arnold class name
if len(list(rt.lights)) == 0:
    with pymxs.undo(True, "fx: skydome for volume"):
        sky = rt.ArnoldLight()                  # [verify] class; set type Skydome in GUI if no property
rt.render(outputFile=OUT)
result = {"rendered": OUT}
```

Then GUI: select the flow, Modify > Arnold Volume Parameters (appears after this first render), pick
Default (Blackbody) only for untouched defaults, tyFlow Ramps for a tuned look, tyFlow Ramps (OSL)
when the render still differs from the viewport. After any Inferno Display change, click the preset
again and render again. Check: not black; compare with a viewport capture through
`max_review.compare`.

## 10. Hair and Fur render check (MnJhmI35554)

GUI work: Rendering > Environment and Effects > Effects > Add > Hair and Fur; set the hair render
mode to Geometry (Buffer renders nothing in V-Ray or Arnold [added: mental ray Prim is gone]).
Scripted check only: run procedure 1 and confirm a `hair` row; effect access by script is not in a
saved doc. Test with 10,000 hairs and a region render, then 50,000. In Geometry mode the fibers take
the base mesh material.

## 11. MassFX placement drop (TXTXLsDvCRo)

GUI work (MassFX script names are not in a saved doc): MassFX toolbar, set props as Dynamic Rigid
Body, container as Static with Shape Type Original, switch many props to Convex in MassFX Tools >
Multi-Object Editor, Start Simulation, then Bake Selected before saving (Ctrl+Z resets an unbaked
sim). Check: capture at the settled frame, no intersections; keys exist on the props after baking.

## 12. Motion blur on cached sims

GUI and renderer work; no script names for these options are in a saved doc.

- tyCache from Particle Export: export with subframes (tyFlow 2.000+ supports subframe tyCache
  export and loading for motion blur, version history).
- tyCache modifier: Timing rollout, "Round to nearest frame" off, or deformation motion blur stops
  (tycache doc). A modifier time step below 1 caches subframes and makes larger files.
- Cloth simulated at a time scale other than 1.0 (0.6 in 4c) gave wrong cloth motion blur before
  tyFlow 2.100 (version history): check the build.
- Arnold: motion blur noise is cured only by Camera (AA) samples, usually 4 to 8, lowering the other
  samples to compensate; check the alpha channel for it
  (lighting-rendering__arnold-removing-noise.md). Renderer motion blur switches and shutter go to
  scenario-3dsmax-lighting-rendering.
- The saved sources give no particle-specific V-Ray or Corona motion blur values. Check: a frame at
  peak debris speed shows streaks on debris and none on the static wall; the alpha channel is clean.
