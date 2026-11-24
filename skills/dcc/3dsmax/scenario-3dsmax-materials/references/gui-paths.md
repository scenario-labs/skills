# GUI paths: materials and look-dev

For a human, or a computer-use agent, doing the same work by hand. Labels come from the 2026 and
2027 docs and the videos named. Third-party UIs (V-Ray, Corona) change between versions: confirm on
screen.

## Editors

- **Slate Material Editor**: M key, or Rendering > Material Editor > Slate (-FwvV-1NhUU). Slate 2
  (Qt, 2024 and later) is dockable through the Dockable checkbox in its menu.
- **Create nodes**: right-click in the view > Materials or Maps > General, V-Ray, Corona, OSL. Or
  double-click an input slot to open the browser and auto-connect the pick (-FwvV-1NhUU 00:07:12).
- **Assign**: drag the material's output slot onto the object, or select objects and use Assign
  Material to Selection.
- **Slate shortcuts** (-FwvV-1NhUU 00:01:33 to 00:09:26):
  - L lays out the graph; Z zooms to the selection; H shows hidden slots.
  - Ctrl-drag a node onto a wire to insert it (870bbZJTRB0 00:03:35).
  - Drop an output on another output to move all its connections.
  - Start dragging a node, then hold Alt, to delete it and keep the wires.
  - Alt-drag between material outputs swaps the materials.
- **Compounds**: select nodes, right-click > Package nodes in compound. Double-click to enter;
  right-click > Unpackage compound to undo. To expose a parameter: H, drag the slot into empty
  space, Expose as input parameter. A compound saves to a material library like any material.
- **Material Explorer**: Utilities menu toggle (2026 Menu Editor). With Select children on,
  right-click a material to select every object using it.
- **UI colors for Slate**: Customize > Customize User Interface > Elements: SME.

## Color management

- **Mode and rendering space**: Rendering > Color Management, or Customize > Preferences > Color
  Management. Modes: Gamma Workflow, OCIO (default config), OCIO (custom config). Rendering space:
  ACEScg default, sRGB, P3, Rec 2020 (dlwDiLsPWgI 00:00:34 to 00:02:00).
- **Input rules**: the same page holds the Input Image Files rules table (pattern, extension, color
  space) (QuJe2j7SHZ0 frame 00:00:32).
- **Material editor tone mapping off**: Color Management > Advanced settings > untick the automatic
  option and mark the editor as not tone-mapped (QuJe2j7SHZ0 00:14:10).
- **Per bitmap**: in the Bitmap Texture's file dialog, Color Management group: Automatic
  (Recommended) or a Color Space dropdown. **Data Image** sets Raw in one click (dlwDiLsPWgI
  00:07:06).
- **VRayBitmap**: parameters > Color space transfer function (None, Inverse gamma, sRGB, From 3ds
  Max, Auto) and RGB primaries (Default, sRGB, Raw and others) (aHgu1dwjzSo frame 00:04:18;
  QuJe2j7SHZ0 00:05:30).
- **V-Ray frame buffer before an OCIO switch**: Layers panel, disable Filmic tonemap and Exposure,
  keep White Balance. Display correction layer: OCIO, input ACEScg, display sRGB, view ACES 1.0
  SDR-video (QuJe2j7SHZ0 00:10:06; qt7FB4UU0qg 00:02:12).

## Material classes

- **OpenPBR Material**: Material/Map Browser > Materials > General (first in the 2026 list,
  -FwvV-1NhUU frame 00:00:25). Arnold parameters appear in its rollouts only after one render
  (`materials-lookdev__arnold-openpbr-surface-2027.md`).
- **Physical Material** and **PBR Material (Metal/Rough, Spec/Gloss)**: Materials > General. The PBR
  materials accept bitmaps dragged straight from Windows Explorer onto their map buttons. Utilities
  hold an Import PBR Material utility (`materials-lookdev__autodesk-pbr-materials.md`).
- **glTF Material**: Materials > General; feed it Bitmap Texture maps only.
- **VRayMtl**: Materials > V-Ray > VRayMtl. Shading mode dropdown (VRayMtl or OpenPBR) at the top;
  Preset dropdown under Basic. Switching to OpenPBR renames gloss parameters to roughness with
  reversed meaning (procedures P14). Anisotropy, Rotation, Local axis and Map channel sit in the
  BRDF rollout; Fog system units scaling in Options; Thin-walled next to Affect shadows, active only
  with Translucency SSS.
- **VRayBlendMtl**: Materials > V-Ray; Base material plus Coat 1 to 9 with Blend amount 1 to 9
  (aHgu1dwjzSo frame 00:06:20).
- **Corona Physical Material**: Materials > Corona > Physical Material. Thin shell (no inside) and
  Metalness sit at the top; Roughness mode is under Advanced options.
- **Corona Layered Material**: Materials > Corona > Layered Material. Connect Base material first;
  Layer 1 to 10 each with a Mask; displacement mode dropdown (rBBLMAtnbzQ).
- **Instance Duplicate Maps**: a utility named in the Multi/Sub-Object doc; it finds duplicate
  Bitmap maps scene-wide and offers to instance them.
- **Multi/Sub-Object**: Materials > General. It shows in the browser only if the active renderer
  supports it (`materials-lookdev__multi-sub-object-material-2027.md`). Set face IDs with Edit Poly
  (Polygon level, Set ID) or a Material modifier. Remove unused sub-materials with the Clean
  MultiMaterial utility (Utilities panel).

## Masks and mapping

- **VRayDirt**: Maps > V-Ray > VRayDirt. Swap Occluded and Unoccluded colors; Mode Ambient occlusion
  or Inner occlusion; Radius (with a map slot); Distribution; Bias Z; Consider same object only.
- **VRayCurvature**: Maps > V-Ray; Mode Convex or Concave; Output max color; Ignore bump.
- **VRayCompTex**: Source A, Source B, Operator (Add, Multiply, Maximum).
- **Falloff**: Maps > General > Falloff; Falloff Type Towards/Away; Falloff Direction World Z-Axis;
  swap colors; Mix Curve.
- **Triplanar**: VRayTriplanarTex (texture mode "same texture on all axes", size, blend, random
  offset) or Corona Triplanar. Plug it into each bitmap's Mapping source.
- **Randomizers**: VRayUVWRandomizer (stochastic tiling, scale, rotation, offset) in the bitmap's
  Mapping source; Corona Mapping Randomizer after the bitmap and before the triplanar.
- **Real-world size**: Modifier List > UVW Map, Box, Real-World Map Size on, then set the size on
  the bitmap (870bbZJTRB0 00:02:27).
- **Corona MultiMap**: Batch Load, mode Mesh Element for planks (64vzHYEWedI 00:55:15).

## Converters and deliverables

- **Scene Converter**: Rendering > Scene Converter (alt menus: Rendering > Tools, Scene > Tools).
  Build source-to-target rules in the dialog. mental ray nodes are removed, not converted.
- **Corona Converter** (Legacy to Physical): Corona menu > Converter.
- **V-Ray Scene Converter**: V-Ray menu > Converters.
- **glTF import material type**: File > Import > glTF dialog, Material type (Scanline, Physical,
  PBR, glTF, Arnold, USD, OpenPBR) and Texture options (Unpack Metal/Roug/Occ)
  (`scripting-pipeline__gltf-import-2027.md`).
- **OpenPBR viewport quality**: add `[OpenPBR]` with `UseSimplifiedViewportShader=0` to
  `CurrentDefaults.ini`, then restart.

## Libraries and generators

- **Material library**: Material/Map Browser options > Open or New Material Library; drag materials
  or compounds into it; browser Groups act as bookmarks (-FwvV-1NhUU 00:06:21).
- **Chaos Cosmos Browser**: V-Ray or Corona toolbar button. Materials > AI Material Generator
  (beta): drop an image up to 2K square, set Preserve colors, Make tileable, Normal and Roughness,
  then Generate, Download and drag onto the object (xtNmC3eHops).
