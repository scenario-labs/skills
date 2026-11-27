# GUI paths

For a human or a computer-use agent. Paths come from the docs and videos named; video UIs are 2019
to 2024, so labels may have moved in 2027. Check the 2027 panel before clicking.

## Unwrap UVW (P3, P4 and the hand workflow)

- Add: select the object > Modify panel > Modifier List > Unwrap UVW. Map channel: the modifier's
  Channel group (1 to 99).
- Open the editor: Unwrap UVW > Edit UVs rollout > Open UV Editor.
- Before peeling in 2023 and later (RcObIKoUTvE):
  - Peel rollout, solver drop-down at the top left: Unfold (default) or LSCM. Use LSCM when Reset
    Peel must join islands.
  - Tools > Pack UVs: set the method drop-down from Unfold 3D to Recursive Packing and click Cancel.
    This stops the auto-pack on every peel.
- Seams: edge sub-object > select edges (Loop helps) > Peel rollout seam tools (Edit Seams,
  Point-to-Point Seams), or convert an edge selection to seams.
- Peel: polygon level, select all > Quick Peel. Peel Mode keeps it interactive; Reset Peel re-peels
  the selection. Detach and Avoid Overlap toggles sit in the Peel rollout.
- Pins (LSCM): Pins group > Pin Selected, Unpin Selected, Auto-Pin Moved Vertices, Select Pinned
  Verts.
- Relax: Tools > Relax (Relax Tool dialog): Relax By Polygon Angles, Iterations 100, Amount 1.0,
  Stretch 0.0, Start Relax, Apply (aMCWmnml0o0 frame 00:03:09). Relax Until Flat is the one-click
  variant.
- Straighten: Align/Space tools > Straighten Selection, for grid-like shells only.
- Stitch: edge level > select a seam edge (its twin highlights) > Stitch rollout > Stitch to Target,
  Average or Source, or Stitch Custom with the Stitch Tool dialog.
- Shared sub-objects: Display > Show Shared Sub-Objects.
- Flatten: Explode rollout > Flatten by Polygon Angle, by Smoothing Group or by Material ID; Flatten
  Settings under Flatten: Custom.
- Pack: Arrange Elements rollout > Pack Together or Pack Normalize, with Rescale, Rotate and
  Padding. Padding 0.02 appears in the Painter demo (xuLRnFBvLyI frame 00:04:48); convert pixels
  with `td_plan.py`.
- Groups: polygon level > Group Selected > Rescale Priority (0 to 1), then pack.
- Flip a flared shell: select the shell > Flip Horizontal in the editor's transform tools (TS doc).
- Weld: Weld Selected Subobject (Threshold 0.01), Weld All Selected Seams.
- Checker: the editor's texture drop-down shows a checker in the editor. For the viewport, use P2 or
  assign a checker material.

## UVW Map (P5)

- Modifier List > UVW Map > Parameters: Mapping type (Planar, Cylindrical with Cap, Spherical,
  Shrink Wrap, Box, Face, XYZ to UVW).
- Length, Width, Height and U, V, W Tile; Flip.
- Real-World Map Size check box: also tick Use Real-World Scale in the bitmap's Coordinates rollout
  and type the real Width and Height there.
- Channel group: Map Channel (1 to 99) or Vertex Color Channel. Changing it copies edits to the
  target channel silently, so save first.
- Alignment: X, Y, Z, Fit, Center, Bitmap Fit, Normal Align, View Align, Region Fit, Reset, Acquire.
- Restrict to polygons: put Edit Poly below with a polygon selection, then UVW Map above it.
- Material side: in each bitmap, Coordinates rollout > Map Channel must equal the modifier's channel
  when it is not 1.

## Bake to Texture (P6, P7)

- Open: Rendering > Bake to Texture. Also Rendering > Tools in the Rendering set, or the 0 key quad
  menu.
- Renderer: Render Setup (F10 in the 2027 page) > Renderer. Arnold for Common Maps; Scanline for
  Scanline elements.
- Select the low poly > Add Maps to Selected Object > pick maps (Common Maps, Arnold or Scanline
  elements). Ctrl+A selects all rows to edit them together.
- Columns:
  - Projected From: Self, Projection, Pick from Scene, Pick from List. Pick the high poly.
  - UV Channel, with Configure UV Channel for UDIM, Mudbox or ZBrush tiles.
  - Image Size (unlock for non-square), Padding, Bg, File Name, File Type.
  - Output To: Files Only, Original material, Duplicate Original material, Create new material. At
    map level: File Only or Material Input slot.
- Projection Options: Method Cage, Raytrace or UV Match; Max Ray Distance (eyedropper in the
  viewport); Resolve Hit Closest or Furthest; Hit Only Matching Material ID; Ray Miss Color
  Background, Self or Use Color For Diagnostic.
- Cage: on the Projection modifier > Cage rollout > Reset, then Push Amount or Percent until the
  cage encloses the high poly (-SMLc0od_5Y frame 00:01:42).
- Normal options per map:
  - Normal Map Space (Tangent for engines), Sync With, X (Red), Y (Green).
  - MikkT for Tangent, Calculate bitangent per pixel, Output into Normal Bump.
- Viewport pair: Customize > Preferences > General > Normal Bump Mode: same MikkT and per-pixel
  settings as the bake.
- Color: OCIO mode > Automatic, or Data Image for normals and masks. Gamma Workflow mode >
  Automatic.
- Curvature or IDs: Add Maps > Override (Scanline) or Arnold_map_override, then pick the map in its
  options.
- Bake Options: Rendered Frame Window toggle; Bake opens the Baking Progress dialog.
- After the bake: High Quality viewport to judge. For export, select the object > Shell material >
  keep the baked material, or use `BakeToTexture.clearShellKeepBaked` (P6).

## Render to Texture, legacy (P8)

- Rendering > Render To Texture. The Projection Options dialog holds the legacy defaults: Raytrace,
  Use Cage on, Offset 10.0, Resolve Hit Furthest, Ray miss color red, Tangent Red Right and Green
  Down.

## Randomizers and triplanar (P10)

- V-Ray: Slate Material Editor > Map Browser > Maps > V-Ray > VRayTriplanarTex or VRayUVWRandomizer.
  - Plug the randomizer into the Mapping Source of the master VRayBitmap.
  - Link the other VRayBitmaps' Mapping Source to the master.
  - Bitmap to VRayBitmap conversion: viewport right-click converter (6FalgHWkhKE 00:02:09).
- Corona: Slate > Maps > Corona > Corona Mapping Randomizer and Corona Triplanar. The randomizer
  goes into the triplanar.
- Corona decals: Create panel or Corona toolbar > Corona Decal.
  - Set width, height and depth, Max angle limit (90 removes back faces), and the include or exclude
    list.
- Judge all of these with Interactive rendering (ActiveShade, V-Ray IPR, Corona Interactive), not
  the viewport.

## Substance Painter hand-off (P11)

- Compact or Slate Material Editor: one material per texture set, named for the set, each with a
  distinct color.
- Vertex Paint for ID maps: Modifier List > VertexPaint > Fill or Paint with a palette. Turn the
  vertex color display off before leaving.
- Painter New Project: Normal Map Format and Compute Tangent Space Per Fragment as the target needs.
  Auto-unwrap options regenerate cut, unfold or pack per set.
