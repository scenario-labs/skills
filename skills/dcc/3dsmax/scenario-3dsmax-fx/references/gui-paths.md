# GUI paths (scenario-3dsmax-fx)

For a human or a computer-use agent. Menus are from the sources' 3ds Max versions; check labels in
2027 menus. tyFlow editor actions are from tyFlow beta and 1.x videos plus the 2.x docs.

## tyFlow object and editor

- Create a flow: Create panel > Geometry > tyFlow > tyFlow, click in a viewport; Modify panel > Open
  Editor (or double-click the flow).
- Add an operator: Tab in the editor opens quick-type search, then double-click; or double-click it
  in the depot at the bottom.
- New event: drag an operator into empty graph space. Connect: drag the output dot of a test to the
  target event.
- Switch output side of a test: right-click the test operator > Switch output side.
- Duplicate: shift-drag. Linked copy: right-click > copy, then paste instanced; break the link with
  make unique.
- Re-seed one operator: right-click > reset selected.
- Preset flows: right-click > Preset Flows (simple icon, ivy, object, PhysX, scatter flows).
- Color an event: event display color; name each flow with Show name and give it its own object
  color.
- Simulation controls: tyFlow object rollout > Reset or Refresh simulation, time step, time scale;
  PhysX rollout > Position Iterations.
- Middle-click a spinner (2.000+): value stepper by orders of magnitude.
- Pick objects in operator lists (PhysX Collision, Surface Test, Birth Objects): Add or Pick, then H
  opens the select-by-name dialog.

## Destruction

- Voronoi Fracture > Voronoi rollout: Points, Variation %; Fractures rollout: Cap holes, Override
  cap MatID, Generate cap UVs, Normalize, Weld after slicing; Performance: Max fractures per frame.
- PhysX Shape > Dynamics: friction, restitution, damping, mass override relative to volume; shape
  type Convex Hull, Mesh or SDF (2.000+).
- PhysX Bind > Bind Type: Rigid (Glue) or Rigid (Joint); Bind Breaking: Breakable, Force, Torque,
  Max breaks/frame; Bind Display: Show connections, Show endpoints.
- Property Test > type Velocity Magnitude, Radius, Scale, Spin, Binds broken.
- Surface Test > Distance to surface, pick the activator; Inside volume for digging.
- Activator proxy: object properties > Display as Box; uncheck Renderable.

## Cloth

- Cloth Bind > Operation: Shape to cloth; Solver: Mass per-cloth, stiffness values, Stiffness Solver
  Constrained; Collisions: Enable CUDA collision solver, Thickness, Self-collisions, Self-thickness,
  Object collisions; Mesh: Add shell to surface, outer and inner amount and MatIDs; Tearing: Enable
  cloth tearing.
- Collision operator: pick colliders; absolute radius.
- Particle Physics operator: collision stiffness, collide radius.
- Force operator: gravity; Turbulence or built-in noise strength (key it with Auto Key).
- Reveal: Create > Helpers > Point, animate with Auto Key; Object Test > Filters tab > enable
  filter > Event Age (Frames) greater than 90; Object Bind > lock to object; Mass operator.

## Caches

- Particle Export > export type tyCache, Set to Timeline, output path, channels, Post-export action:
  create tyCache object; "auto-export on render" option.
- tyCache modifier: Modify panel > tyCache > Mode (save in .max or external file), Filename, Keep
  cache in RAM (leave on), Start/End frame, Time step; Timing rollout: Frame offset, Clamp, Retimer.
- Load a flow cache: Birth Flow (pick the tyCache object) plus Flow Update.
- Alembic: File > Export > Alembic; re-import with File > Import before using it in another sim.
- Snapshot of a flow: Mesh operator with Render Only off, then Tools > Snapshot.

## Fire and smoke (ZENITH, Inferno operators)

- Editor depot > Inferno group: Birth Inferno (voxel size, advection mode), Inferno Emitter, Inferno
  Density, Inferno Collider (emission thickness), Inferno Force (Advanced section), Inferno Spawn,
  Inferno Properties, Inferno Display, Inferno Export.
- Arnold: Rendering > Render Setup > Renderer: Arnold; render once; select the flow > Modify >
  Arnold Volume Parameters > Volume Shader Presets: Default (Blackbody), tyFlow Ramps, tyFlow Ramps
  (OSL), Include Fuel in Preset.
- Light: Create > Lights > Arnold > Arnold Light > Type Skydome.
- Shader edits: Slate Material Editor (M) shows the created "tyFlow ramps" Standard Volume or the
  OSL material.

## Render prep for particles

- Mesh operator in every rendered event; Instance Material > inherit from object; Material ID
  operator > Random with a randomized multi-material (Utilities > assign randomized multi-color
  material).
- Turn off Edged Faces before captures.

## Hair and Fur

- Modify > Modifier List > Hair and Fur (WSM); General Parameters: Hair Count, Scale, Root Thick,
  Tip Thick; Frizz, Kink and Multi Strand parameters for clumps.
- Rendering > Environment and Effects (8) > Effects > Add > Hair and Fur > Hair: Geometry (not
  Buffer).
- Styling: Styling rollout > Style Hair, comb, Finish Styling. GUI only.

## MassFX

- Show the toolbar: right-click the toolbar area > MassFX Toolbar.
- Set Selected as Dynamic, Kinematic or Static Rigid Body; mCloth: Set Selected as mCloth Object.
- Shape Type Custom or Original in the rigid body modifier; MassFX Tools > Multi-Object Editor >
  Physical Mesh type Convex.
- Start Simulation; MassFX Tools > Simulation Tools > Bake Selected.

## Phoenix (legacy scenes only)

- Create > Geometry > PhoenixFD > Fire/Smoke or Liquid simulator; Simulation rollout > Start; Output
  rollout > Backup interval, cache path; Scene Interaction rollout for include and exclude lists;
  Rendering > Volumetric options; save shading as a .tpr preset.
- Ocean texture: Slate > Maps > Phoenix FD > Ocean Texture in a VRayDisplacementMod slot.

## Viewport

- Materials not shown: Customize > Preferences > Viewports > Choose Driver > Nitrous Direct3D 11.
