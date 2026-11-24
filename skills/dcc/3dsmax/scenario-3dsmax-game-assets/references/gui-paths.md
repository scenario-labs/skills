# GUI paths: game assets

For a human or a computer-use agent. Menu names follow the 3ds Max 2027 docs where saved; paths seen
only in older tutorials are marked with the video and its 3ds Max version. Hotkeys are defaults and
may be remapped.

## Inspect

- Viewport statistics (polys, tris, verts): press 7, or viewport label menu > Configure Viewports >
  Statistics, Total plus Selection (HhUMdy-0kSI, 2021).
- Edged Faces: F4. Backface culling: Object Properties > Display Properties > Backface Cull
  (SKXrtpTIsNI).
- Inspect normals: Modifier List > Edit Normals (shows normals; Unify and Break buttons).
- Vertex colors in the viewport: Object Properties > Vertex Channel Display [added].

## Units, pivot, transforms

- Units: Customize > Units Setup > System Unit Setup: 1 Unit = 1.0 Centimeters. Since 2027.1 also
  Customize > Preferences > Files: Respect System Units in Files.
- Pivot: Hierarchy panel > Pivot > Affect Pivot Only, then type 0, 0, 0 in the Move Transform
  Type-In (status bar fields), then turn Affect Pivot Only off (z1ws_LOo9AU).
- Reset XForm: Utilities panel > More > Reset XForm > Reset Selected, then right-click the stack >
  Collapse All (3PuxYRayJGE).
- Snaps for kits: right-click the Snaps Toggle > Grid and Snap Settings > Options > Enable Axis
  Constraints (J1lnlTbMtKs, 2015).

## Cleanup

- Weld: Editable Poly, Vertex level, Ctrl+A, Edit Vertices > Weld settings (gear), threshold 0.001.
- Isolated vertices: Edit Vertices > Remove Isolated Vertices.
- Flip: Polygon or Element level, right-click > Flip Normals; or Modifier List > Normal > Flip
  Normals, then collapse.
- Hidden faces: Edit Geometry > Unhide All.
- Turn to Poly: Modifier List > Turn to Poly: Limit Polygon Size on, Max Size 4, Remove Mid-Edge
  Vertices on (frame 00:07:25 in 3PuxYRayJGE).
- Mesh Cleaner: Modifier List > Mesh Cleaner (Dead Vertices option since 2027.3).
- OBJ round trip: File > Export > Export Selected, OBJ, Faces: Triangles, Precision 6; then File >
  Import.

## Shading

- Smoothing groups: Editable Poly > Polygon level > Polygon: Smoothing Groups rollout, Clear All,
  then button 1; Auto Smooth with a threshold.
- Chamfer modifier: Modifier List > Chamfer; Segments 0 for mid-poly; Filter By group: From
  Smoothing (Unsmoothed Edges after Retopology, HhUMdy-0kSI), Min. Angle, Max. Angle; Limit Effect
  off after Tri mitering (Chamfer doc).
- Symmetry modifier: Threshold 0.01 instead of the 0.1 cm default (tP7FD4l-qus 01:05:28).
- Smart Bevel (2027): Modifier List > Smart Bevel, above the Boolean; Selected Edges or Use
  Unsmoothed Edges; presets in the preset list (lDpcfhxP3qU).
- Weighted Normals: Modifier List > Weighted Normals: Weighting Area and Angle, Use Convex Corner
  Angle, Blending 1.0; Hard Edge Detection from smoothing groups, UV map or edge angle.

## Retopology and reduction

- Modifier List > ProOptimizer: Keep Textures, Keep UV Boundaries (and Keep Material Boundaries,
  Keep Normals) before Calculate; then Vertex %.
- Modifier List > Retopology: Face Count, Regularize, Adaptivity, Auto Edge (Smoothing Groups, By
  Angle 30), then Compute.
- Modifier List > Subdivide: Variable Curvature, Preserve Sharp Edges 30 (for triangulated CAD,
  Pg2Nm-fwyME).
- Make a modifier unique per object: right-click the modifier > Make Unique.

## LODs, collision, sockets

- LOD copy: Edit > Clone > Copy; rename `<mesh>_LOD1`.
- Collision: Create > Geometry > Box around the part, rename `UCX_<mesh>_00`, convert to Editable
  Mesh or Poly.
- Socket: Create > Helpers > Dummy, rename `SOCKET_<mesh>_00`.

## Vertex color

- Modifier List > VertexPaint; Painter Interface floater; Channel group: Vertex Color, Vertex Illum,
  Vertex Alpha or Map Channel (aQIQH0hZkDg, 2022).

## Export

- FBX: File > Export > Export Selected, type Autodesk (*.fbx). Include > Geometry: Smoothing Groups
  on, Triangulate on, Preserve edge orientation on, TurboSmooth off. Advanced Options > Units:
  Centimeters; Axis Conversion: Up Axis Z. FBX File Format: version 2020 family (Epic: FBX 2020.2).
  Read the Warnings dialog (CM3GwvoOSP4).
- glTF (2027.3): File > Export, Save as type GL Transmission Format (*.glb, *.gltf). Khronos
  options: Export File type glb, Apply scale with system unit, Metal/Rough/Occ Map building, Draco
  Compress, Keep Instance structure.
- Datasmith: ribbon > Datasmith tab > Export or Direct Link Synchronize; Datasmith > Settings >
  Limit Texture Resolution. Metadata: right-click object > Object Properties > User Defined:
  `key = value` with spaces.

## Engine side

- Unreal FBX import dialog: Import LODs on (when LODs are in the FBX); Auto Generate Collision off
  with UCX meshes; Normal Import Method: Import Normals [added]; Combine Meshes off for separate
  assets [added].
- Unreal Static Mesh Editor: Details > LOD Picker; Show > Collision; Approx Size in the viewport
  overlay.
- Unreal Datasmith: Datasmith > Direct Link Import; Window > Output Log for conversion messages;
  select children and Ctrl+G to group (qsV4k09kPV8).
- Unity: select the FBX in Project > Inspector > Model tab: Convert Units, Bake Axis Conversion,
  Apply; drag into the Hierarchy to read the Transform (z1ws_LOo9AU).
