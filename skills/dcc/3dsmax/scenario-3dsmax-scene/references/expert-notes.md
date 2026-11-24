# Expert notes: scene assembly

Grouped by expert. Each line gives the claim, then the source and timestamp. [added] marks a rule of
this skill, not of the expert. URLs are in [sources.md](sources.md).

## Autodesk (official videos and 2027 help)

Units, Part 1 (aPc02tZzj8c, 3ds Max 2015 UI):

- Display units are safe to switch at any time; system units are set at the start and not changed
  (02:07, 02:16).
- The same box reads about 3 ft under Inches, about 40 ft under Feet, over 200,000 ft under Miles
  (04:49 to 06:05).
- Changing system units on an existing scene turns a 3 ft box into 36 m per side when switching
  inches to meters (02:33).
- Pick the system unit from the project size: small units for toys and phones, feet or meters for
  buildings, miles or kilometers only for terrain (03:07).
- For Revit or FBX interchange the presenter suggests feet as system unit (04:13). Later archviz
  videos show centimeters or millimeters grids; the shared rule is never to change it mid-project.
- Far from the origin, a camera on a path twitches and normals flip although relative geometry is
  unchanged; imported and merged models are the usual cause (06:27 to 08:37).
- The Origin slider, Distance from Origin and Resulting Accuracy fields are a calculator, not a
  setting (06:27).

System Unit Setup doc:

- Change the system unit before you import or create geometry; never in an existing scene.
- Keep the scene roughly centered on the origin; keep significant detail above one generic unit.
  Symptoms of round-off: navigation too fast or slow, viewport clipping, flipped normals.
- Respect System Units in Files (default on) raises the Units Mismatch dialog on open, merge, XRef
  and drag and drop. In 2027.1 the rules moved to Preferences > Files with separate choices for
  load, merge, XRef Object and XRef Scene.

XRef Objects doc (2027):

- With Modifiers set to XRef or Ignore, the stack shows only "XRef Object"; world-space modifiers
  are always merged.
- An XRef object can only be animated if its transform controller was merged; an offset applies to
  the whole animation.
- Objects that influence each other (path constraints, space warps, particle emitters) must be in
  the same XRef record. Render effects do not travel.
- Merging an XRef object whose source links a DWG drops the DWG link.
- Proxies: a simplified clone, a box, or an early-stage save of the model stands in for heavy
  geometry.

File Link settings doc (2023 page, same dialog in 2027):

- Combine Entities: By Revit Material (one object and one layer per material, Multi/Sub-Object
  lost), By Category or By Family Type (Family and Category visible in Scene Explorer,
  Multi/Sub-Object kept), As One Object (massing and shadow studies), Do Not Combine (performance
  suffers on large files).
- Combine cannot change on reload. Create Helper at Model Origin is on by default and the geometry
  is linked to it.
- Revit FBX turns light instances into unique lights; add lighting in 3ds Max when linking FBX.
- A linked daylight system asks for exposure control; answer Yes or renders overexpose (text written
  for Scanline and Quicksilver).

AutoCAD cleanup (1pEqaqq8v_Y, AutoCAD 2012):

- A good layer system is the most important part of CAD management (01:07).
- Build new closed polylines on separate `3D-` layers with BPOLY instead of editing the 2D drawing
  (04:54); gaps make BPOLY fail (05:59).

Containers (LXcoWMxPDrs, 2010 UI):

- A container is a helper that groups content into one block, saved as `.maxc`, lockable against
  edits (00:00).
- Place it where the content should insert (01:02); close it before moving on so content cannot be
  selected (02:54).
- [added] For discipline splits the 2027 docs and later experts use XRef scenes; keep containers for
  locked hand-off blocks and re-check 2027 behavior.

3DGS doc (2027.2, 2027.3):

- A Gaussian Splat object reads its file as a live reference; overwriting the file updates the
  object and keeps name, transform and stack. File > Import embeds the data instead.
- PLY Preset (Generic, Postshot, Substance 3D, WorldLabs) sets the expected up axis; fix rotation
  with Up Axis, not by re-importing.
- Viewport Limit and Render Limit are separate random percentages.
- Gaussian Splat objects do not support instances unless converted back from a Points object.
- Splat files appear in Asset Tracking, relink if moved, and are gathered by the Resource Collector;
  a missing file reports as a missing asset.

## VizAcademy UK, host Mike (hz07nIgm7EA, Corona archviz)

- Unit mismatch is a top beginner trap (00:17:33).
- After scaling any object, Reset XForm: modifiers, noise, bump and UVs work in the scaled object
  space (00:21:31 to 00:24:52). He types 39.37 or 254 percent to rescale models in the scene
  (00:19:13); the doc route is Rescale in the Units Mismatch dialog when merging.
- A 3 GB scene came from hand-placed dense rocks (3.5 GB); scatter or proxy instead (00:14:29).
- Excessive TurboSmooth is the top performance killer: viewport iterations 0, render 1 or 2 only
  near camera; one extra chamfer segment beats a smoothing level (00:16:18, 00:49:47).
- Keep the exterior as its own scene; hiding still carries millions of polygons (01:15:28).
- Model to the shot list: detail only where a camera sees it (00:52:56, 00:55:48).
- A gray viewport model often has its textures, unconnected or with wrong paths (01:24:37).
- Downloaded commercial models are triangulated or proxified on purpose; do not "fix" them
  (00:48:38).

## Jake Denham, Luxury Visuals Academy

XRef scenes (2Nqp9n95pzE):

- Split a heavy scene into interior and exterior files and assemble them in a master (00:00:33 to
  00:02:12).
- A lighting master with only XRefs carries no polygons of its own: "This is saving a lot of memory"
  (02:12).
- Keep Automatic update off; use Update Now after saving the source (02:46).
- Do not save the selection back over the source and re-reference; keep separate scenes (03:21).

Tips (hLOkgefE0ts):

- Group > Explode flattens nested groups; Ungroup removes one level (00:57).
- Lock cameras with Hierarchy > Link Info; Freeze does not stop movement in a camera view (04:29).
- The Substitute modifier swaps many placeholders for one asset and asks about the material (13:04).

## Master ArchViz (SRVCuw9aPI8, V-Ray)

- File weight follows polygon count: the 161,735-polygon vase outweighs the table (01:20, frame
  01:50).
- Find heavy objects with Show Statistics (key 7) first (01:46).
- Measured in one scene: original 331,973 KB; instances 147,649 KB; proxies 54,861 KB; XRef main
  file smaller, the XRef file 278,592 KB (frame 02:50).
- Render time rose: 8m49s original, 9m26s instances, 11m31s proxies, 9m27s XRef (frame f_00175,
  single runs). The methods lighten file and viewport, not the render (02:24).
- File size changes only after saving (03:37).
- Proxy gotchas: store materials first, Reset XForm if scaled, attach with Match Material IDs to
  Material, `vrayMeshExport()` if the menu is missing, 5,000 preview faces (04:50 to 06:31).
- XRef scene content cannot be moved or selected: finalize the layout before splitting (07:48).

## CGI Made Simple (cv7bIWciFU4, Revit to 3ds Max)

- Link FBX instead of Import, so a client change is re-export plus Reload (05:06).
- Combine By Revit Material: 49 objects (48 in the frame) against 384 with Do Not Combine; layers
  come named by material (04:31, frames 03:37 and 08:23).
- Export FBX from a 3D view only; FBX 2015 format is enough (00:50).
- Linked geometry cannot be deleted or edited; Bind when the design is frozen, which removes the
  link (07:52, 08:22).
- Turn lights and daylight off on reload when you light in 3ds Max (06:16).
- Deciding condition against the render.camp lighting course (64vzHYEWedI), which says always
  remodel: link when the BIM stays live, remodel or bind when the design is frozen and texturing
  needs clean UVs.

## render.camp (FYRj1pCBQq8, interior archviz)

- Number layer names so alphabetical order equals importance: `100_cams`, `101_light`,
  `200_ceiling_base`, `201_ceiling_int`, `300_walls`, `301_doors`, `400_floor`, `500_lamps`,
  `600_dec` (05:17, frame 13:04).
- Order from most essential to least: delete decorations and the apartment still exists; delete
  walls and it does not (12:06).
- After moving objects to a layer, hide it to find leftovers (09:20).
- Layer 0 cannot be renamed or deleted (02:52). A layer created while another is active becomes
  nested (12:44).
- "That's my logic, you might have your own" (11:46): a team picks one standard.

## Kory Bieg (Y-zZn8bo1cE, clones)

- Copy is independent; Instance shares everything; Reference shares the base and modifiers below the
  bar, with local modifiers above it (00:24, 03:30, 04:17).
- Editing a reference's base parameters changes the instance it came from (03:09).
- Bold stack entries mean shared data; links can be broken (Make Unique), never added later (02:37).

## Arch Viz Artist (VN2qUrEHDPo)

- A template file with units, renderer and preferences removes setup repetition (05:10).
- Delete objects invisible to camera, shadows and reflections (07:27).
- Attach beats groups; proxies cut file size and viewport load but not render time (08:20).

## studioGAD Architecture (sQiA1X4XlMw, SketchUp)

- Same units in both programs (mm, Decimal) before import (00:33, 01:37).
- Group furniture parts per material in SketchUp so they arrive as separate objects; one exploded
  object with many materials is hard to retexture or unwrap (00:33 to 01:05, 03:23).
- "Save as SketchUp 8" was a 2020 importer limit; check the 2027 importer instead.

## VizCourse (mbi-7pTItcU, Connecter asset manager)

- Library assets in centimeters with the pivot at the base center, in both the asset and the preview
  studio file (00:53:06).
- In Manage External Files, Remove strips the map from the `.max`; use Replace, Rename or Set Path
  (00:15:03).
- Moving a library file outside the manager breaks its tags (00:08:54).
- Replace Target swaps a placed object for another asset at the same position (01:29:37).

## Eloi Andaluz Fulla (3ds Max news, 2026 to 2027.2)

2027.2 points and splats (YB330UhrdOA):

- A splat is a native class; only Arnold renders it with relighting and shadows; V-Ray and Corona
  would need to adopt the API (01:08).
- Classic modifiers (Bend, XForm, Squash, Melt) deform splats non-destructively (01:42).
- Edit with Point Select plus modifiers; convert to Editable Point only for per-point edits (02:14).
- Point Instance instances meshes, lights, groups with their lights, and other instances at any
  depth (04:59, 07:43).
- Point modifiers target all, selected, soft selection, a color, or a named selection set; assign
  named sets at distribution time (05:33).
- Array output as points feeding Point Instance: about 5 times faster on small arrays, more on heavy
  scenes (06:39 to 07:10).
- Before points this was Forest Pack, tyFlow or Particle Flow work; Point Instance is the native
  base (20:20). Deciding condition [added]: distribution controls, culling and wind favor the
  plugins.
- A material audit tool shown relinks missing maps, strips flat maps, instances duplicate maps and
  removes unused multi-materials (13:31, frame).

2027 (pjwGWsS3GIg) and 2026 (I6QPVe8c7jU):

- New MAXScript functions query and merge by layer from other `.max` files (09:04); the 2027
  MAXScript docs confirm `layers:` and `mergeNodesByLayer:`.
- Autodesk Assistant (2027 Tech Preview) was slow and refused MAXScript for the reviewer (06:27);
  2027.3 added "Do work for me".
- 2026 sped up Displace, Conform, Boolean and Array; retest older performance caution before
  applying it (01:38).
- Return to stack position (2026) keeps the modifier you were editing per object (00:33).

## Miled Rizk (i-d-h2Isojg, Snap Working Pivot)

- Each transform tool remembers its own coordinate system; after placing the working pivot set Move,
  Rotate and Scale to Working (01:39).
- Alt+Shift+S places a Selection Pivot on a face normal (05:44); Create Grid From Working Pivot
  builds a persistent construction plane (10:17).
- [added] Scripted substitute: build the frame from a face normal and center, and create a Grid
  helper aligned to it.
