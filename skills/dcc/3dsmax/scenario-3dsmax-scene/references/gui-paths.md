# GUI paths: scene assembly in 3ds Max 2027.3

For a human or a computer-use agent doing the same steps as [procedures.md](procedures.md). Paths
come from the 2027 help pages saved in the sources unless marked otherwise. Older video UIs are
noted where the label may differ.

## Units (P2, P3)

- Units Setup: Customize > Units Setup (Standard menu); Customize > Customization > Units Setup
  (Enhanced menu).
- System unit: Units Setup > System Unit Setup > System Unit Scale. Change it only in an empty
  scene.
- Accuracy calculator: System Unit Setup > Origin slider, Distance from Origin, Resulting Accuracy.
  Press Enter after typing a distance; Tab does not recalculate. It changes no setting.
- Unit rules on load, merge and XRef (2027.1 and later): Customize > Preferences > Files > unit
  handling section: Respect System Units in Files, plus scene load, merge, XRef Object and XRef
  Scene behavior.
- File Load: Units Mismatch dialog: choose Rescale the file objects to the system unit scale for a
  team template; Adopt the file's unit scale only when that file defines the project.
- Rescale World Units utility (named in the System Unit Setup doc): Utilities panel > More > Rescale
  World Units [verify path] (whole scene or selection). Use on a staging copy only.

## Origin (P4)

- Move a linked CAD or Revit model: select the Point helper named after the linked file (created
  when Create Helper at Model Origin is on), then move it.
- Working pivot and construction grids: Tools > Snap Working Pivot tools; Alt+Shift+S places a
  Selection Pivot (i-d-h2Isojg 05:44).

## Structure (P5)

- Scene Explorer: Tools > Scene Explorer; Main Toolbar > Toggle Scene Explorer; Alt menu: Scene >
  Manage Scene Content > Scene Explorer. Alt+Ctrl+O reopens the last closed explorer.
- Sort modes: Scene Explorer Selection toolbar > Sort By Layer or Sort By Hierarchy.
- Layer Explorer: dock it as a tab beside the Command Panel (FYRj1pCBQq8 00:36). Create layer with
  "+"; a new layer created while another is active becomes nested.
- Move nodes to a layer: select nodes, make the layer active, Add to Active Layer (toolbar button).
- Select a layer's objects: fast double-click on the layer. Rename: slow double-click or
  right-click > Rename.
- Groups: Group > Ungroup removes one level; Group > Explode flattens all levels (hLOkgefE0ts
  00:57).
- Batch property edits: Scene Explorer columns, multi-select, edit the cell.
- Lock a delivered camera: Hierarchy panel > Link Info > Locks (Freeze does not stop movement in a
  camera view, hLOkgefE0ts 04:29).

## Repeats (P6)

- Clone: Edit > Clone (Ctrl+V) offers Copy, Instance, Reference; Shift+drag with Move also sets the
  number of copies.
- Break a link: Modify panel > right-click the base object in the stack > Make Unique.
- Reference bar: modifiers below the bar are shared, above it local; bold stack entries are shared.
- Substitute modifier: swaps many placeholders (for example chairs) for one source object, with an
  option to carry its material (hLOkgefE0ts 13:04).
- V-Ray proxy: right-click > V-Ray mesh export (or `vrayMeshExport()` in the Listener when the menu
  entry is missing), then Create > Geometry > V-Ray > VRayProxy (SRVCuw9aPI8 06:00).

## Assets (P7)

- Asset Tracking: File > References > Asset Tracking Toggle (Shift+T) [verify]. The Paths menu
  repaths files whose materials still point to an old location (Asset Tracking doc); item names such
  as Set Path and Make Path Relative [verify].
- Configure search paths: Customize > Configure User and System Paths > External Files [verify].
- Resource Collector (named in the 3DGS doc): Utilities panel > More > Resource Collector [verify
  path]; gathers maps and splat files with the scene.
- Archive: File > Archive [verify path] (ZIP of scene and maps; script `archiveMAXFile`,
  doc-confirmed).

## Split (P8)

- XRef Scenes: File > References > XRef Scene. Dialog: Add, Convert Selected, Remove; Enabled,
  Overlay, Merge; Update File Automatic (keep off) and Update Now; Display Visible or Box; Ignore
  Lights, Cameras, Shapes, Helpers, Animation; Match Layers by Name and Parent (2Nqp9n95pzE frames,
  2019 to 2020 UI).
- XRef Objects: File > References > XRef Objects. Proxy Object rollout swaps a light stand-in.
- Save part of a scene: select, File > Save Selected.
- Containers: Create > Helpers > Container; Tools > Containers. Close a container before moving on;
  definitions save as `.maxc` (LXcoWMxPDrs, 2010 UI).

## Viewport (P9)

- Statistics overlay: key 7, or viewport "+" menu > xView > Show Statistics; selection stats in
  "+" > Configure Viewports > Statistics > Total + Selection.
- Adaptive Degradation and Progressive Display: Customize > Preferences > Viewports (doc); Viewport
  Configuration > Display Performance [verify].
- Object display: right-click > Object Properties > Display Properties (only when By Object is set,
  not By Layer).
- Hide or freeze: Display panel, quad menu, Scene Explorer, Layer Explorer.
- Maximize a viewport: Alt+W.

## CAD, Revit, SketchUp, FBX (P10)

- Link: File > Import > Link Revit, Link FBX or Link AutoCAD; or File > References > Manage Links >
  Attach > Files > choose a Preset > Attach This File.
- Presets: Manage Links > Presets tab > Modify: Combine Entities (By Revit Material, By Revit
  Category, By Revit Family Type, As One Object, Do Not Combine), Create Helper at Model Origin,
  Lights, Daylight System, Cameras, Curved Objects Detail (10), Auto-Smooth (15 degrees, off), Use
  Scene Material Definitions, Use Scene Material Assignments on Reload.
- Reload after a client change: Manage Links > Files tab > select the flagged file > Show Reload
  Options > Reload. Combine Entities is locked on reload.
- Bind: Manage Links > Files > Bind (link removed, geometry editable).
- DWG or DXF: Manage Links > Attach > Rescale and Incoming File Units.
- Revit side: File > Export > FBX from a 3D view only (cv7bIWciFU4 00:50).
- AutoCAD side: build closed outlines with BPOLY > Pick Points on new `3D-` layers (1pEqaqq8v_Y
  04:54).
- SketchUp side: Window > Model Info > Units (Decimal, mm); group parts per material before export
  (sQiA1X4XlMw). The video's "save as SketchUp 8" rule was for the 2020 importer; check the
  supported version in the 2027 importer.
- Plain import: File > Import > Import (choose the file type).

## Splats and points (P11)

- Import: File > Import > Import, Files of Type: All Formats, pick a PLY, SPZ or LCC file; each type
  has its own Import Options window.
- Live reference: create a Gaussian Splat object and set its File parameter (Parameters rollout:
  Type Static or Sequence, File, Preset, Up Axis, Units, Start Frame, Splat Count).
- Display and Rendering rollout: Display Points size, Viewport Limit %, Render Limit %, Instance
  Display, Display Limit.
- Gaussian Splats rollout: Affect Camera, Shadows, Reflections, Refractions, Matte Shadows; Color,
  Intensity, RGB; Display Off or Shader (2027.3).
- Convert back after point edits: right-click in the stack > Convert To > GaussianSplat.
- Scatter: Turn to Point on a surface, then Point Instance with the source objects; Array modifier
  output set to points.
