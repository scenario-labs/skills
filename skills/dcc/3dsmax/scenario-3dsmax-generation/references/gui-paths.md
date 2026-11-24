# GUI paths: landing generated files by hand

For a human, or a computer-use agent, doing the same steps by hand. Labels come from the Autodesk
2027 docs and the videos named; third-party panels (Chaos, tyFlow) change often, so confirm on
screen. Paths with no source named are long-standing 3ds Max menus not re-read in the 2027 docs
[added]: confirm them on screen too. There is no Scenario plugin for 3ds Max: generation happens
through the Scenario MCP in the agent, and these paths only land the files.

## Import a generated model

- **GLB or glTF (2027.3 and later)**: File > Import > Import > Files of type > glTF 2.0
  (KHRglTFImporter_adsk) (*.glb, *.gltf). The Khronos glTF importer dialog opens.
- **Khronos glTF importer dialog** areas: Scale, Hide DummyObject, Show VertexColor, Avoid Duplicate
  Name, Instance; material type (Scanline Mtl, Physical Mtl, PBR Mtl, glTF Mtl, Arnold Mtl, USD Mtl,
  OpenPBR Mtl); Node Extra data (Custom Attributes, User Defined Properties); Animation; Color
  Management (Khronos PBR Neutral Tone Map); Texture (Make Texture unique, Use CompositeMap for
  Non-Albedo base_color mtl, Unpack Metal/Roug/Occ); Light; Scene (Import Default Scene, Deploy to
  Layers); Back Ground and Post Process.
- **Choose the material type once here** before batch imports: `#noPrompt` reuses the last settings.
  Pick the scene's class (OpenPBR Mtl for Arnold or an OpenPBR scene).
- **FBX (2025, 2026, or quads)**: File > Import > Import > FBX. In the FBX Importer dialog, check
  Units (Automatic or the file's unit) and Axis Conversion (Up Axis Z for 3ds Max).
- **Merge into a live scene** rather than replace: File > Import > Merge is for .max files only;
  generated files always come through Import.

## Fix scale, pivot and placement

- **Measure**: Tools > Measure Distance, or the Utilities panel > Measure for the object's
  dimensions.
- **Root**: Create panel > Helpers > Dummy (or Point). Select the imported meshes, Select and Link
  to the helper.
- **Pivot**: Hierarchy panel > Pivot > Affect Pivot Only > Center to Object or Align to World; move
  to the base.
- **Uniform scale**: Select and Uniform Scale on the root, typed in the transform type-in (F12).
- **Reset XForm** on meshes after scaling if they will be exported: Utilities panel > Reset XForm >
  Reset Selected, then collapse (z1ws_LOo9AU 00:01:06).
- **System unit**: Customize > Units Setup > System Unit Setup. Change it only at scene start, never
  to fix one asset.

## Layers and naming

- **Scene Explorer** > Layer Explorer, or the Layer toolbar: create layer `GEN_props`, `GEN_splats`,
  `GEN_textures`; drag nodes onto it.
- **Rename**: Tools > Rename Objects for a `GEN_<name>_` prefix on a selection.
- **Provenance by hand**: right-click the object > Object Properties > User Defined tab; paste the
  sidecar's model name, date and asset id. Scene-level: File > Properties (File Properties) > Custom
  tab.

## Gaussian splats (2027.2 and later)

- **Embed in the scene**: File > Import > Import, pick a PLY, SPZ or LCC file. Data is written into
  the .max.
- **Live reference**: create a Gaussian Splat object and set its File parameter; the splat data
  stays on disk and updates when the file changes.
- **Parameters rollout**: Type (Static or Sequence), File, Preset for PLY (Generic, Postshot,
  Substance 3D, WorldLabs), Up Axis, Units, Start Frame.
- **Display and Rendering, Gaussian Splats rollouts**: Color tint for render time; Display > Shader
  (2027.3) for a viewport closer to the render.
- **Edit points**: convert to Editable Point (loads the file once into the scene); convert back to a
  Gaussian Splat object from the points object when splat channels remain.
- **Render**: Arnold renders the native object. One expert reports V-Ray and Corona do not render it
  yet (YB330UhrdOA 01:08); V-Ray 7 and Corona 14 have their own splat loaders.

## Textures and color space

- **Bitmap color space**: in the Bitmap file dialog, Color Management group: Automatic (Recommended)
  or a Color Space dropdown; Data Image sets Raw in one click (dlwDiLsPWgI 00:07:06).
- **Rules table**: Rendering > Color Management (or Customize > Preferences > Color Management) >
  Input Image Files rules: add patterns such as `*_normal*`, `*_roughness*` to Raw.
- **Test tiling**: Slate Material Editor (M), open the map, set Tiling 2 x 2 and check the preview
  or a render of a plane.

## Sky and HDR environment

- **Environment map**: Rendering > Environment (8) > Background > Environment Map: drag the Bitmap
  (or a renderer's dome or sky map) here. For V-Ray use a VRayLight Dome with the texture; for
  Corona a CoronaBitmap in the Environment slot. Lighting setup belongs to
  scenario-3dsmax-lighting-rendering.
- **Rotate**: the bitmap's Coordinates rollout > Environ, Mapping Spherical Environment, U Offset.

## Viewport capture and renders for generation input

- **Grab viewport**: Tools > Grab Viewport > Create Animated Sequence File or Grab Active Viewport
  (saves to the frame buffer, then save).
- **Playblast** for video input: Tools > Preview > Create Preview (Make Preview), choose the frame
  range, size and output file.
- **Render**: Rendering > Render Setup (F10) > Common > Render Output > Save File; set the output
  size to the aspect the image or video model needs.
- **Clay or ID passes**: render elements in Render Setup > Render Elements (V-Ray Wirecolor or
  Corona masks) for the protect masks used in image edits (zARHVN_XN4U 00:31:19).

## Autodesk 3ds Max MCP server (mcp-safe channel)

- **Enable**: Customize > Preferences > MCP tab. Set MCP tools enabled (Read-only, Safe MAXScript
  and others). Turn on Show connectivity status to get the menu-bar MCP icon; click it to start or
  stop listening.
- **Studio lock**: administrators can fix these values; the controls then show grayed out.
- **Script approval**: the MCP client shows each proposed script; the user approves it in the client
  app.

## Running a handoff script

- **Scripting > Run Script** for a `.ms` or `.py` file the agent wrote; or Scripting > MAXScript
  Listener (F11), paste, and Ctrl+Enter.
- Check the Listener output for the JSON report the script prints, then send it back to the agent.

## In-Max AI tools (pointers only; facts in in-max-ai-tools.md)

- **Chaos AI Enhancer, Upscaler, Veras**: V-Ray Frame Buffer or Corona VFB toolbar; needs a Chaos
  account.
- **Cosmos AI Material Generator**: Chaos Cosmos browser > AI materials.
- **tyDiffusion**: tyFlow menu > tyDiffusion window (tyFlow installed with its AI component).
- **Autodesk Assistant**: its panel from the 3ds Max menu bar (2027 and later, sign-in required).
