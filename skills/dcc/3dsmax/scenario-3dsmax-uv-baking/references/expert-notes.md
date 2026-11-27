# Expert notes: UVs, mapping and baking

Principles by source, with timestamps. Additions by this skill are marked [added]. Doc keys: BTT =
Baking to Texture 2027, HL = Bake high to low, PO = Projection Options, TS = Troubleshooting normal
maps, MBT = MAXScript BakeToTexture, MRT = MAXScript Render to Texture, CMR = Corona Mapping
Randomizer, CTP = Corona Triplanar, VTT = VRayTriplanarTex, VUR = VRayUVWRandomizer.

## Texel density and UV space

**Huge Menace (Tristan), sR1sAWWT2x8, Blender demo, theory is software-independent**

- Texel density is texture pixels per cm of surface, independent of screen pixels (00:00:47).
- It is not visual fidelity: same density, different look if the texture is blurry or wrongly scaled
  (00:05:05).
- Three levers change it: texture size, surface area and UV island scale (00:03:14).
- Targets: weapon 20.48, first person 10.24, third person 5.12, top-down 2.56 px/cm (00:12:28).
- Derive a target from the screen: a 100 cm plane covering 248 px at the closest distance gives 2.48
  px/cm (00:13:21).
- Many studios require at least 75% UV utilization (00:16:44).
- Under-used space has five remedies: strict density, soft density (scale up to fill), atlas, change
  object scale within reason, non-square maps such as 1024x512 (00:16:15 to 00:17:44).
- Delete faces nobody sees rather than optimize them (00:10:13).

**Abe Leal, 2gv1jYDAoJc, Maya and Painter, game environment artist**

- Seams generously on hard-surface: cut box corners; triplanar texturing later hides the extra seams
  (00:07:51).
- Uniform density through pre-scale that preserves 3D ratios; break it for heads, hands and signs on
  purpose (00:13:09, 00:22:20).
- Padding is never zero because mipmaps bleed: 8 px shell, 8 px tile at 2K (00:14:13 to 00:14:46).
- Third person about 4.8 to 5.12 px/cm is fine (00:16:23).
- A blurry bake is a density problem (00:21:47); a pixelated bake was a 1024 output for a 2048 set
  (00:21:12).
- One material on the low poly; a stray face with a second material made two texture sets
  (00:20:39).
- Cage: push until red disappears, not further, or neighbors bake in (00:19:36, 00:20:07). Painter
  frame: Max Frontal 0.0059, Rear 0.01, supersampling 16x (frame 00:21:18).
- A hard edge where two parts intersect stays visible after the normal map; merge, soften or accept
  (00:18:00, 00:23:26).
- Abe Leal says do not squeeze every pixel, leave room for later additions (00:15:51). Huge Menace
  asks for 75%. Deciding condition: shipped asset on a VRAM budget, or an asset still growing.

## Unwrap UVW in 3ds Max

**Arch Viz Artist (Aga), aMCWmnml0o0, 3ds Max 2019 UI, tools unchanged in 2027 per doc**

- Detach elements before unwrapping; seams on sewing lines and panel breaks (00:00:36).
- Sequence: seams, select all, Peel, Quick Peel, then Relax and Straighten (00:01:40 to 00:07:08).
- Relax By Polygon Angles, Iterations 100, Amount 1.0, Stretch 0.0. Edge Angles can do worse on some
  shapes, so compare (frame 00:03:09; 00:02:45 to 00:03:53).
- Straighten Selection fixes grid-like panels (00:06:33). The doc warns it suits grid layouts, not
  radial ones.
- Wood: scale and rotate shells to place grain, about four boards visible (00:08:18). Fabric: tile
  in the bitmap, do not scale UVs (00:10:34).
- Stitch, not hand alignment: selecting one edge highlights its twin because it is the same 3D edge
  (00:12:53).
- Abe Leal skips Straighten on complex shapes (2gv1jYDAoJc 00:11:02). Deciding condition: grid-like
  or radial layout.

**Jordan Younie, RcObIKoUTvE, 3ds Max 2023 and 2024**

- Peel has Unfold (default since 2023) and LSCM (legacy). Reset Peel with Unfold quick-peels each
  island and does not join them; LSCM restores the pre-2023 behavior (00:00:33).
- Peel and Quick Peel pack every time. Stop it with Tools > Pack UVs: method Recursive Packing, then
  Cancel, and the setting sticks (00:02:20).
- Unfold can still give slightly better islands; flip between solvers and compare (00:01:13).

**Autodesk Unwrap UVW doc (Edit UVWs rollouts)**

- Unfold3D: less distortion, best on organic shapes, no manual pins, always succeeds even with an
  undesirable result. Bad UV data is auto-corrected; if that fails, regenerate UVs or use LSCM.
- LSCM: pins hold, Peel Mode shows violet, at least two pinned vertices.
- Pack Together keeps scale; Pack Normalize scales all clusters to fit 0-1. Both respect Rescale,
  Rotate and Padding; Padding works best "relatively low". Pack may rotate 90 degrees even with
  Rotate off.
- Groups keep clusters together through packing; Rescale Priority 0.0 to 1.0 scales a group (0.5 =
  half size).
- Flatten defaults: angle 60, spacing 0.02, normalize on, rotate on, fill holes off. Flatten by
  Smoothing Group needs clusters fully enclosed by hard edges.
- Weld Threshold default 0.01 in UV space.

**RenderRam (Vjeko), 9RVvRvFb_vs, UVReactor beta (third-party)**

- Get density from a reference polygon, Set it on the whole shell (00:07:39).
- In UVReactor, set Break after every cut and extrude, because an extrude reconnects shells
  (00:05:59). Beta limits: bare Editable Poly only (00:02:12).

**3dio, Ud4tkFZ35xk, Unwrella 3.1 promo (vendor claims)**

- Automated unwrap and pack with a texel density input and automatic distribution across UV tiles,
  for 3ds Max and Maya 2027 (00:01:08).

## UVW Map and real-world size

**Arch Viz Artist (Saga), zLDLOSx-qL0**

- Turn Real-World Map Size on in both material and modifier. With it on, some modifier fields stop
  working (00:04:35, 00:05:09).
- Compute the tile size from real dimensions: 56 courses x 7 cm ≈ 400 cm, type 4000 in a millimeter
  scene. Verify with a plane carrying the same material (00:08:33, 00:09:40).
- A polygon selection below UVW Map restricts the mapping (00:10:03).
- A second UVW Map on channel 2 scales one map in a Mix without moving the others (00:11:15).

**UVW Map doc (2016 page, behavior assumed unchanged)**

- Seven types: Planar, Cylindrical (Cap), Spherical, Shrink Wrap, Box, Face, XYZ to UVW.
- 99 channels. Changing a modifier's channel copies its edits to the new channel silently, which can
  overwrite edits there.
- Modifier tiling and material tiling multiply (2 x 3 = 6).
- Primitives carry built-in coordinates; imported meshes have none until mapped.
- One UVW Map on a multi-selection makes one big gizmo unless Use Pivot Points is on.

**Arch Viz Artist, fundamentals-scene digest**

- Adding UVW Map over a textured model destroys the existing UVs; inspect first.

## Baking in 3ds Max

**Ken LaRue (Autodesk), -SMLc0od_5Y, 3ds Max 2021, Scanline era**

- BTT normal options and Preferences > Normal Bump Mode must match (00:03:19).
- Destination decides MikkT and per-pixel; he uses MikkT with per-pixel off (00:02:13, 00:02:45).
- Aligned meshes: Raytrace, Max Ray Distance 10.0 "works in most cases"; cage otherwise (00:01:38).
- Create New Material as PBR Metal/Rough, normal straight into norm_map, Output into Normal Bump off
  (00:02:13).

**Ken LaRue (Autodesk), 2IhYmRsKZ4Q, 3ds Max 2021, Arnold**

- Bake Arnold albedo, metalness, roughness and AO, not a beauty pass (00:01:12).
- Shell material keeps the original for edits and re-bakes (00:02:30).
- Procedural sources show black in the viewport; judge with ActiveShade (00:00:36).
- Defaults on screen: 2048, padding 2, PNG, UV channel 1, Projected From Self (frame 00:01:46).

**BTT doc (2027)**

- Arnold gives the most-used maps and the best performance for metalness, roughness, AO and GI. Keep
  ray depth and sampling minimal and check the filter to avoid blurry maps.
- Projected From: Self, Projection, Pick from Scene, Pick from List. Picking creates a Projection
  modifier.
- Methods: Cage, Raytrace (perfect world alignment), UV Match (UVs must line up exactly, same map
  channel on the high, no spatial overlap needed).
- Override and Arnold_map_override bake any Map Browser map (Material ID, vertex color, curvature,
  OSL) with no material required.
- Calculate bitangent per pixel: Unity has it disabled.
- Data Image sets Raw color space for non-color data.

**HL doc**

- Most engines use per-pixel bitangent, so usually on. This contradicts -SMLc0od_5Y. Deciding
  condition: the destination app; Unity off per BTT. No source names Unreal's setting: bake both
  variants on a test bevel when the target is unstated.
- HL says Scanline and F1; BTT 2027 says F10 and Arnold. Follow BTT.

**PO doc (legacy dialog)**

- Include Working Model is a quick fix for misses but fails when the low occludes the high; it suits
  lattices.
- Tangent space suits deforming characters. World space makes moving objects "swim".
- Normal Bump has red and green flips: fix a mismatch there instead of rebaking.

**TS doc**

- Parallel rays lose detail: move the cage end out and scale it in, or Break low-res vertices.
- Tangent flares (reddish right, bluish left) mean flipped UVs: Flip Horizontal.
- Mirrored overlapping UVs: move half on W; the bake uses the higher W.
- Never put Edit Normals on the low poly.

**MBT doc**

- `getCompatibleMapTypes()` is incomplete until the utility is initialized (`showDialog()`).
- Reading `projectionMethod` when Projected From is Self raises a runtime error.

**Arrimus, 7h4EHmNhe8A (high-poly prep feeding the bake)**

- Smoothing-group-aware UV islands go with the low (00:18:05).
- Optimize Face Thresh 4.0 to 6.4 before ProOptimizer; too high ruins baking (00:16:22).
- The poly budget is a production decision (00:16:42).

**Game-assets digest (jjbigley, SKXrtpTIsNI)**

- A UV seam on every hard edge cancels the normal-map residue (00:37:06).
- A Marmoset bake with Mikk tangent space looked cleaner than the 3ds Max default on the same mesh
  (00:44:58).

**Engine side (game-assets cluster)**

- Datasmith import, Advanced options: enable lightmap generation only if lighting will be baked;
  disable it for Lumen with fully dynamic lighting (qsV4k09kPV8 00:03:32).
- Datasmith doc: Unreal adds two lightmap UV channels on import; a Datasmith Attributes Modifier or
  Light Map Coordinate Index selects a hand-made channel instead.
- Unreal FBX static mesh doc: only Color and Normal connect automatically; Specular is imported
  unconnected; AO is not imported.
- The sources state no green-channel or per-pixel bitangent setting for Unreal. Decide by the
  target's documentation or a test bevel.

## Triplanar, randomizers, decals

**Jonas Noell, 6FalgHWkhKE, V-Ray 5 era**

- Repetition is the easiest tell of CG (00:00:00).
- On a collapsed mesh, vary at render time, not by editing UVs (00:00:57).
- Use VRayBitmap; link all maps to one master mapping source; blur transfers, so lower it on the
  normal (00:04:26, 00:13:02).
- No UV rotation on a randomizer that feeds a normal map (00:07:43).
- Triplanar Blend 0.1 default, raise if seams show (00:09:36). Chain the randomizer into the
  triplanar for per-element scale (00:11:55).
- Stochastic tiling needs Mirror Tile and a tile blend such as 0.2 (00:17:27).

**Chaos Corona, 4o3j7PBHLrQ (now Corona Mapping Randomizer)**

- Keep bitmap coordinates at default and fit the UVW Map to the geometry first (00:02:37).
- Whole-number offsets show nothing; a wider range is only differently random (00:06:32).
- Directional wood: rotation 0 to 180 with Step 180; 0 to 360 with Step 180 under-rotates
  (00:09:11).
- "Same as U" off for flips, or you get a 180 degree rotation (00:05:16).
- Keep channels in sync with linked parameters or a saved node (00:07:42).
- Noell (no rotation with normals) and Corona (rotation 0 or 180 for wood) differ. Deciding
  condition: if the normal map shares the randomizer, check the render lighting, or drop rotation.

**CMR and CTP docs**

- The randomizer depends on UVs. With bad UVs, feed it into Corona Triplanar; triplanar overrides
  downstream mapping.
- Step is an increment in Corona (Step = 1 / rows), but a number of steps in V-Ray's VUR. Do not
  copy values between renderers.
- High quality blending is on by default and can double render time.
- Renaming objects or materials changes results in name-based modes.

**Chaos Corona (Jake Denham), O3_8wv-voK0**

- Decals place graphics, cracks and potholes with no UVs. Max angle limit 90 removes back faces; use
  depth limit and an exclude list (00:01:50 to 00:03:20).

## Substance Painter hand-off

**Adobe Substance 3D, xuLRnFBvLyI**

- The material name becomes the texture set; one material per object is best (00:00:54, 00:04:15).
- Pack per texture set; Painter can cut, unfold and pack per set if needed (00:00:54, 00:02:51).
- ID maps come from vertex colors (turn the display off before leaving Vertex Paint) or a baked
  color ID (00:05:15).
- Object names become geometry mask entries (00:06:19).

## Generated meshes

**ai-workflows digest (O6G6taj5M14, j2qd-kLQY1Q)**

- AI UVs are the weakest part of a generated model; manual seams plus angle-based unwrap and pack is
  the proper fix (O6G6 00:12:46).
- After any mesh rework, re-generate or re-bake the texture (O6G6 00:20:13).
- tyDiffusionTexGen replaces UV channel 1 with its own unwrap: move the original mapping to channel
  2 first (j2qd 00:04:49).
