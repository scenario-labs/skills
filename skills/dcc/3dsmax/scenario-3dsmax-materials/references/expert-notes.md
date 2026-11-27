# Expert notes: materials and look-dev

Principles and judgment by source, with timestamps. Video IDs are YouTube IDs (URLs in
`sources.md`). Docs are named by their saved file. `[added]` marks a rule this skill adds. All
videos show 3ds Max 2022 to 2026 and V-Ray 6, Corona 7 to 13 or the Maya UI: values carry over, UI
labels may not.

## Color management and color spaces

### Jonas Noell, V-Ray ACEScg workflow (QuJe2j7SHZ0, 3ds Max 2024, V-Ray 6)

- Preparation is the whole job: switching to ACEScg is one click, but only after every bitmap
  declares its space (00:01:33, 00:15:17).
- A new VRayBitmap has transfer function Auto and primaries Default. In a normal-map slot V-Ray
  switches it to Raw and None by itself. In a roughness slot it changes nothing (00:02:39 to
  00:03:45).
- Two methods give identical renders (00:07:45):
  - Name tags with Auto and Default kept: `_srgb` for diffuse, `_raw` for normal and roughness,
    `_lin_srgb` for an HDRI (00:04:19 to 00:07:11).
  - Manual settings per bitmap: diffuse primaries sRGB and transfer sRGB; HDRI primaries sRGB and
    transfer None; data primaries Raw and transfer None.
- Deciding condition: tags for a library you control, manual settings for client files you cannot
  rename (00:07:45). This skill's `pbr_set.py tagged_copy` writes tagged copies to a new folder, so
  client files are never renamed [added].
- Before the OCIO switch, disable every VFB layer that changes range or display (Filmic tonemap,
  Exposure); keep White Balance (00:10:06).
- Once 3ds Max OCIO is on, V-Ray's own color management is grayed out until Gamma workflow returns
  (00:14:43).
- The 3ds Max color management also tone-maps the material editor. Untick the automatic option under
  Advanced (00:14:10).
- Judge by rendering tagged and manual columns: they must match exactly. Then compare sRGB with
  ACEScg for correctness, not sameness (00:07:45, 00:12:29).

### Autodesk, OCIO in 3ds Max 2024.1 (dlwDiLsPWgI)

- Set color management before materials and lights; changing it later forces a re-tweak of every
  texture (00:04:08, 00:07:40).
- With OCIO use no exposure control and no tone-mapping imager: the view transform does it
  (00:04:37).
- "Normal vectors are not colors and should not be managed" (00:07:40). An EXR normal map was
  auto-assigned scene-linear Rec.709, which is wrong: set Raw with the bitmap dialog's Data Image
  button (00:07:07).
- Input rules guess a file's space from extension or name; override per bitmap (00:02:52).

### HM Studio, ACES versus Gamma 2.2 (qt7FB4UU0qg, 3ds Max 2026, V-Ray)

- In 2026 OCIO with ACEScg is the default and texture conversion is automatic; the manual steps were
  for 2024 and 2025 (00:01:40).
- ACES output is already tone-mapped. A second tone mapper crushes highlights and shadows
  (00:07:35).

### Docs

- `scripting-pipeline__maxscript-bitmap-values-2027.md`: `openBitmap <file> colorSpace:<string>`
  requests a space and works only under OCIO; `gamma:` works only under Gamma workflow.
  `.colorSpace`, `.colorSpaceSource`, `.colorSpaceStatus` and `.colorSpaceRule` are read-only.
  `ColorPipelineMgr.GetFileIOColorSpaceList()` lists the config's names.
- `materials-lookdev__autodesk-pbr-materials.md`: the PBR materials set linear gamma 1.0 on
  roughness, glossiness, metalness and normal maps by themselves. Spec/Gloss does not guarantee
  physical plausibility; Metal/Rough mostly does.

## Material models

### Arnold, OpenPBR Surface overview (tEUiIBApw-U, Maya UI, same shader as 3ds Max)

- Layers: base (metal, translucent, subsurface or glossy-diffuse), thin film, coat, fuzz on top
  (00:01:12, 00:11:28).
- Metal: base color is F0, specular color is the F82 edge tint. The Arnold docs give F0 and F82
  tables in sRGB and ACEScg (00:02:17; frame 00:03:15: aluminum F0 sRGB 0.916 0.923 0.924, copper
  0.932 0.623 0.522, gold 1.059 0.773 0.307).
- Diffuse roughness (EON) at high values gives a flat dusty look (00:04:15). Specular roughness 0 is
  sharp, 1 matte, energy conserved (00:08:27).
- Subsurface: weight 1 with transmission 0; radius scale per channel, reddish for skin (00:04:44 to
  00:05:16).
- Transmission: weight 1 and metalness 0. Transmission color is Beer's law absorption over
  transmission depth; scatter for honey or murky water (00:06:18 to 00:06:51).
- Dispersion: Abbe 10 to 70, default 20; dispersion scale defaults to 0, so it is off (00:07:41 to
  00:08:13).
- Coat darkens the base on purpose; the coat darkening control turns that off (00:10:13).
- Fuzz weight is fiber density, fuzz roughness fiber shape (00:10:50).
- Thin film thickness is in micrometers, 0 to 1 typical; above 1 the colors wash out (00:12:04).
- Emission luminance is in nits, soft maximum 1000 (00:12:42).
- Thin-walled is for panes, bubbles, paper and leaves (00:13:36). Anisotropy needs tangents
  (00:09:04).
- Judging method: one slider at a time on a preview ball, against real references (00:07:46).

### Adobe OpenPBR FAQ (`materials-lookdev__adobe-openpbr-faq.md`)

- Priority: metalness 1 disables subsurface and transmission; transmission weight 1 removes
  subsurface; base color shows only when none of them is 1.
- A roughness map goes into specular roughness, not base diffuse roughness.
- A transmissive mesh that renders dark needs transmission depth at object scale.
- MaterialX support and OpenPBR support are different claims. Validate a round trip through USD with
  MaterialX, early in production, against the ASWF OpenPBR Shader Playground and a reference render.
  Agree up front which features (thin film, dispersion, subsurface) shared materials may use.

### Autodesk Physical Material (`materials-lookdev__autodesk-physical-material-parameters.md`)

- Reflection color and weight sit in Advanced mode because dielectrics vary in scattering, not
  reflectivity.
- Transparency depth 0 is classic CG transparency; non-zero enables absorption. Thin-walled removes
  refraction and depth.
- Thin-walled turns SSS into classic translucency.

### V-Ray 7 VRayMtl (`materials-lookdev__vray7-vraymtl.md`)

- Shading mode VRayMtl or OpenPBR. OpenPBR mode is not supported on V-Ray GPU, renames parameters,
  and inverts glossiness into roughness.
- Converting a VRayMtl to OpenPBR inside V-Ray is a Shading mode switch on the same material, not a
  new class. What changes (doc, Basic parameters, BRDF, Coat, Sheen):
  - Reflection Glossiness becomes Roughness, Refraction Glossiness becomes Roughness, Coat
    glossiness becomes Coat roughness, Sheen glossiness becomes Roughness. For each, "its values
    produce opposite results".
  - Refraction becomes Transmission, Self-Illumination becomes Emission, Sheen becomes Fuzz/Sheen;
    these work the same.
  - BRDF Type is forced to Microfacet GTR (GGX) and Use roughness is on.
  - The doc does not say whether the switch rewrites stored values or gloss maps. Snapshot values
    before and after (procedures P14) and compare renders; invert maps by hand if the readback shows
    unchanged numbers [added].
  - The switch does not produce the 3ds Max OpenPBR Material class. For USD or a hand-off to Arnold,
    build OpenPBR Material [added].
- Sheen glossiness (VRayMtl mode): 1.0 lets all light reach the diffuse; smaller values make the
  cloth glossier. In OpenPBR mode the renamed Roughness runs the other way: 0.0 lets no light reach
  the diffuse. The sources give no fabric value: set it by render against the reference.
- Anisotropy (BRDF rollout): range -0.99 to 0.99, 0 is isotropic; Rotation in degrees; orientation
  from Local axis (X, Y or Z) or a Map channel. Coat has its own Coat anisotropy and Anisotropy
  rotation. Script names are not in the saved docs: resolve them with `discover()` [verify].
- Thin-walled works only when Translucency is SSS; SSS color sets the backside color, SSS amount the
  translucency.
- Refraction Glossiness lower means frosted. "Use roughness" reads the inverse of Glossiness, so the
  Physical doc's frosted roughness 0.3 reads as glossiness about 0.7 [added: derived from the
  inverse, not a doc value].
- Metalness values between 0 and 1 "do not correspond to any physical material".
- Opacity mode Clip disables bump; load the opacity map through VRayBitmap as the workaround. Cutoff
  must never be 0.0.
- Fog color depends on object size unless Fog system units scaling is on. Depth (cm) replaced Fog
  multiplier.
- Volumetric SSS on low-poly meshes with a small scatter radius needs subdivision.
- Keep continuity is on by default for displacement from V-Ray 7 Update 3. With VRayDisplacementMod
  "Use obj mtl", keep the material's displacement defaults. Set displacement in one place only,
  material or modifier (materials digest batch 2 checklist).
- Use VRayMtl whenever possible: Light Cache and render elements are guaranteed only with V-Ray
  materials.
- CG Channel (`ai-workflows__cgchannel-vray7-update2-ai.md`): V-Ray 7 Update 2 added the OpenPBR
  shading mode and supports 3ds Max's OpenPBR material "on export". Whether V-Ray renders the 3ds
  Max OpenPBR Material as well as VRayMtl is not stated: test it, or build VRayMtl [added].

### Chaos Corona, Physical Material (E920CIq83Ws; `materials-lookdev__corona-physical-material.md`; `materials-lookdev__chaos-corona-physical-material-blog.md`)

- The Physical Material is the default. Legacy Material is only for re-rendering old scenes. The
  Corona Converter translates Legacy to Physical, with some manual tweaks for translucency and
  glass.
- One IOR only; the result depends on the surrounding medium (00:08:15).
- Thin shell (no inside) is a first decision, moved to the top of the UI (00:09:19). Translucency
  stays grayed out until Thin shell is on.
- Roughness mode is the default to match Substance and Quixel. Switching mode converts typed values
  but never maps: set the mode to match the map type.
- No reflection color slot. Tint reflections with Edge color (grazing only) or with a clear coat at
  IOR 1.001 whose Absorption tints what is below.
- To strengthen glass reflections at a settled IOR, add a higher-IOR clear coat (example: base IOR
  1.2, coat amount 0.6, coat IOR 1.52). A clear coat cannot reduce a high-IOR base reflection.
- Self-illumination is not a light source: use Corona Light Mtl.
- Recent Corona adds a Glints layer (the digest dates it Corona 15; the doc page gives no version)
  (density, sharpness, scaling, glint size, color ramp) for car paint, road, nail polish, sand and
  snow.

## Layering, masks and imperfection

### Chaos, realistic metal (D-tB0dJp9sU, V-Ray 6)

- Do not dirty the clean base; build a second VRayMtl and layer it with VRayBlendMtl (00:02:31).
- Base metal: metalness 1, reflection white, glossiness 0.7, diffuse about 35 percent gray (00:01:39
  to 00:02:14).
- Glossiness from a contrasty fractal noise (thresholds 0.55 and 0.45), with color 1 fed by a second
  noise so no spot reaches pure black (00:04:26 to 00:06:08). Never 100 percent gloss anywhere
  (00:05:34).
- Reuse the same noises for diffuse rust tint so gloss loss and rust register (00:06:46).
- Edge wear: VRayCurvature convex, radius 0.5, inverted, max color 5, Ignore bump on, combined with
  a Dent through VRayCompTex Maximum (00:07:45 to 00:09:56).
- Dirt: VRayDirt with colors swapped, Consider same object only, radius 2 (00:09:56 to 00:11:03).

### Chaos, layered wood with wear, dirt and dust (aHgu1dwjzSo, V-Ray 6)

- Use real grain from a photo or library set with its normal map; do not invent it (00:01:08).
- One VRayUVWRandomizer feeds every bitmap's mapping source: W rotation 90 for vertical grain,
  stochastic tiling, tile blend about 0.05 (00:01:41).
- Gloss map: desaturate the diffuse, add contrast, lower exposure, color space None (00:03:27 to
  00:03:59). Script substitute outside Max: ImageMagick grayscale plus contrast stretch [added].
- Base reflection glossiness 0.55; normal through VRayNormalMap into bump at 100 (00:01:41,
  00:02:51).
- States as VRayBlendMtl coats: scratched, dirty, dusty (00:06:11). Dirty surfaces reflect less,
  dust not at all (00:10:04, 00:13:23).
- Wear mask: VRayCurvature convex, max color 10, multiplied by two Dent maps at two scales (00:06:40
  to 00:08:23).
- Dirt mask: VRayDirt swapped, same object only, distribution 0, Bias Z 0.1, radius 1, a bitmap in
  the radius slot, plus concave curvature added at max color 2.5 (00:09:58 to 00:12:24).
- A mask stronger than 1.0 needs a VRayColor with RGB multiplier; a swatch clamps (00:10:38).
- Dust: Falloff Towards/Away on World Z, swapped, mix curve for contrast; gray, no reflection,
  slight sheen (00:12:24 to 00:13:23).

### Jonas Noell, procedural concrete (38-TGp5QCMY, V-Ray 6)

- No UVs and no baked dirt: every effect is a procedural mask, so one shader fits any object
  (00:00:48).
- VRayTriplanarTex "same texture on all axes", size 300, random offset; VRayUVWRandomizer with scale
  50 to 150, offset 0 to 1, rotation 0 (00:02:01 to 00:03:41). Triplanar also on every mask bitmap
  (00:07:59).
- Layers in one Composite in the diffuse slot (00:14:26):
  - Blotches: 40 percent.
  - Streaks: VRayDirt ambient occlusion, radius 150, Bias Z 0.9, radius driven by a streak bitmap,
    final 25 percent.
  - Edge dirt: inner occlusion, radius 10, final 20 percent.
  - Edge highlight: radius 4, distribution -5, same object only, 5500 K, final 5 then 3 percent.
- Raise each layer until it is too strong, then back off to about a quarter (00:04:47, 00:08:33).
- Reflection: white, glossiness 0.2, IOR 1.3, fed by a desaturated copy of the diffuse composite
  (RGB 250, gamma 0.8) so reflection is not flat (00:13:51 to 00:15:00).
- Bump composite: VRayEdges 3 cm (default 0.1 cm is too small), concrete bump, holes at 50, edge
  chips masked by the edge dirt mask at 25 (00:15:42 to 00:19:01).
- Judge a close crop and a distant crop (frame 00:19:21).

### ArchViz Explained, Corona Layered Material (rBBLMAtnbzQ, Corona 12)

- Base plus up to 10 layers, each with a mask; white shows the layer (00:00:49).
- Mask from an existing AO or displacement map through Corona Color Correct (frame 00:00:53:
  brightness -0.6, contrast 4.0, gamma 0.32).
- Mask weight below 100 biases toward the layer; layer weight lowers its opacity (00:01:19).
- Displacement modes: Blend all (default), Only from base, Add all (00:01:48).
- Empty base slot gives an error and a white or cyan render (frame 00:00:29).
- Heavy shaders inside layers slow the render; use one Physical Material or a Corona Decal for small
  details (00:02:13).
- Deciding condition, blend versus composite: a Blend or Layered material when layers need different
  shading models (clean metal versus rust); Composite maps when only color or bump differs (digest
  batch 1).

### Arch Viz Artist, library material workflow (870bbZJTRB0, Corona, sponsored)

- UVW Map box with Real World Map Size on for library sets (00:02:27).
- Base color = CoronaMix of color and AO for "gentle contact shadows" (frame 00:02:43). Deciding
  condition [added]: mix AO only when the camera is far and render time matters; otherwise the path
  tracer already shades contact, and AO stays a mask.
- Imperfection maps (smudges, fingerprints) go into roughness through a Mix amount (00:04:08 to
  00:05:15).
- Color-correct a close texture rather than hunting for the exact one (00:03:35).

## Look-dev order and judgment

### Ira Ostrovska, general feeling workflow (64vzHYEWedI, render.camp, Corona 13)

- General feeling stage before any texture: one gray base, HDRI and two helper lights, then flat
  color per big area (00:15:01, 00:17:18). Skipping it means "you cannot expect a cool final image"
  (01:56:04).
- Never pure white or pure black albedo: pure white becomes the brightest spot and steals attention
  (00:27:26).
- Walls and floor are the largest areas and set warmth and contrast; walls about 145 of 255, warm
  (00:20:10, 00:20:48).
- Fabric and carpet: no reflections, lower IOR; sheen from the start (00:22:39, 00:23:12).
- Texture by importance: foreground first, background little, ceiling none. Start with the
  reflection or roughness slot, then diffuse (00:38:12).
- Weaken maps with the slot percentage (00:59:08). Floor planks: MultiMap with Mesh Element on, or
  one board repeats (00:55:15).
- Bump is the commonest beginner mistake; strong bump and displacement also darken color (01:13:51,
  01:18:10).
- Bump shows under directional light, not overcast (01:33:52). Check bump on a pre-final render of
  10 to 15 minutes; the denoised interactive preview hides it (00:45:59).
- Compare to photos, not to other renders (02:11:14). Squint: the brightest spot must be the focal
  point (00:28:00).

### Gor_cgi, car paint (CxHKVjeycv0, Corona 10)

- Solid paint: color picked from the reference then darkened (the photo was overexposed), roughness
  0.8, clear coat 0.85 with a slight blue absorption (00:01:33 to 00:03:18).
- Orange peel: Composite of Noise (size 0.35 on a 50 cm ball, not 1) and inverted fractal Cellular
  chips with Screen, bump 0.1 solid, 0.06 metallic. Real expensive cars show very little (00:03:46
  to 00:07:42, 00:16:00).
- Metallic: Layered Material with base, two flake layers and a clear coat. Flakes from an OSL map
  through Corona Triplanar (no UVs), normal 0.1. Flake roughness is a desaturated copy of the flake
  map. The second layer is sparser at scale 1500 versus 2500 (00:08:47 to 00:15:17).
- The OSL flakes are superseded by the Glints layer of recent Corona (Corona doc).
- Match camera tone, bloom and glare to the reference before judging; star highlights come from
  optics, not the shader (00:17:19).

### Chaos, V-Ray materials basics (un44xZgc_os)

- Gray reflect color is the norm; color it only for gold or car paint (00:01:13).
- Glass: diffuse black, reflect white, refraction white, refraction glossiness lower for frosted
  (00:01:13 to 00:03:01). Fog color tints by thickness and depends on object size (00:03:37).
- Metal presets use roughness and metalness; switch BRDF to Use roughness for a metal from scratch
  (00:05:15 to 00:06:23).
- Normal maps need VRayNormalMap before the bump slot (00:08:27). Triplanar on every bitmap's
  mapping source, one scale for all (frame 00:10:27: 15 cm, blend 0.1).

### Autodesk, Slate tips and compounds (-FwvV-1NhUU, 3ds Max 2026)

- Compounds package a node tree into one map or material with exposed inputs, and save to material
  libraries (00:01:00, 00:04:17). No scripting API for compounds is documented: an agent builds
  plain node trees by script [verify].
- Expose a hidden parameter later: H shows hidden slots, drag the slot into empty space, Expose as
  input parameter (00:02:40). Noise 3D has no seed: expose Phase (00:03:44).
- OpenPBR Material is first in the 2026 Slate list, with defaults base weight 1.0, metalness 0,
  specular weight 1.0, IOR 1.5, roughness 0.3 (frames 00:00:25, 00:09:30).

### Chaos Cosmos AI Material Generator (xtNmC3eHops, Ciro Sannino)

- A beta Cosmos panel turns one diffuse image (jpg, png or webp, up to 2K square) into a material
  with generated normal, bump and surface values; toggles preserve colors and make tileable
  (00:00:46, frame 00:01:00).
- Used for drafts: compare directions quickly, then tune roughness and bump by hand (00:01:48,
  00:03:04).
- Lesson for any generated set [added]: the generator cannot know physical scale or the renderer's
  roughness convention, so the arrival check in SKILL.md stage 2 applies in full.

## Material recipes (cross-source, with deciding conditions)

- **Glass pane**: one face means thin-walled (OpenPBR, Physical) or Thin shell (Corona). Solid glass
  means IOR 1.52 with refraction or transmission 1. If it renders dark, raise transmission depth to
  object scale (Adobe FAQ). Frosted means refraction roughness above 0 (Physical doc: 0.3 and 0.6
  shown). V-Ray: Affect shadows for a cheap caustic.
- **Car paint**: see Gor_cgi above. Recent Corona uses Glints for flakes. OpenPBR uses coat weight
  with coat darkening on, and base metalness for the metallic layer only under a flake mask [added].
- **Oiled or varnished wood**: real grain, gloss derived from the diffuse, shared randomizer.
  Varnish is a coat: Corona clear coat, OpenPBR coat, VRayMtl coat. Wear, dirt and dust states as
  above.
- **Brushed metal**: metalness 1, F0 color and F82 tint, anisotropy with a known tangent direction
  (tEUiIBApw-U 00:09:04). VRayMtl: Anisotropy plus Rotation, oriented by Local axis or Map channel
  (V-Ray 7 doc). Wear and dirt per D-tB0dJp9sU.
- **Brass or other alloys**: the saved F0/F82 frame lists aluminum, copper and gold only. No source
  gives brass values: take F0 and F82 from the Arnold docs table, or match a reference photo, and
  say which.
- **Arnold-native wear and dirt masks**: no saved source covers an Arnold curvature or occlusion
  shader. Bake curvature and AO through scenario-3dsmax-uv-baking, or use OSL maps (below).
- **Fabric**: no or very low reflection, sheen or fuzz for the rim, calm bump (64vzHYEWedI 01:13:51;
  tEUiIBApw-U 00:10:50). VRayMtl: Sheen glossiness lower is glossier; never copy an OpenPBR sheen
  roughness into it.
- **Tinted or frosted glass in V-Ray**: Translucency None, Fog color with Depth (cm), Fog system
  units scaling on so the tint follows real thickness (V-Ray 7 doc; un44xZgc_os 00:03:37).
  Single-face pane: Thin-walled with Translucency SSS.
- **Concrete**: triplanar, randomizer, VRayDirt layers, reflection from the diffuse copy, VRayEdges
  3 cm (Noell).

### OSL maps as the renderer-neutral substitute (`materials-lookdev__osl-map-2027.md`)

- UVW Randomizer (2D, map channel 1 by default; 3D, object space) applies random scale, offset and
  rotation, and takes a seed such as NodeID for per-object variation. It stands in for
  VRayUVWRandomizer.
- Bitmap Random Tiling, Color Correction, Noise, UberNoise and Node Handle cover tiling breakup,
  color variation and per-object seeds.
- The digest calls these renderer-independent; the saved doc only says "a supported renderer".
  Test-render one in the target renderer before building a library on them [added].

### Multi/Sub-Object (`materials-lookdev__multi-sub-object-material-2027.md`)

- A face ID with no matching sub-material renders black; a sub-material switched off is black too.
- The Instance Duplicate Maps utility turns duplicate bitmaps into instances, which cuts video-card
  load on per-plank or per-object variation.

## Disagreements and deciding conditions

| Topic                              | Positions                                                                                 | Decide by                                                     |
| ---------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Procedural versus library maps     | Noell procedural dirt; Arch Viz Artist buys sets                                          | bespoke wear on a hero asset versus generic surfaces at speed |
| Blend material versus Composite    | Chaos VRayBlendMtl coats; Noell one Composite                                             | different shading models per layer versus color or bump only  |
| Corona Layered versus one material | Layered for masked variation; costly                                                      | many large variations versus small details (use Decal)        |
| Gamma 2.2 versus OCIO              | Some trainers keep Gamma 2.2 for Corona and V-Ray; Autodesk and HM Studio default to OCIO | the project's color pipeline; never switch mid-job            |
| AO in base color                   | Arch Viz Artist mixes it; path tracers shade contact anyway                               | camera distance and render budget [added]                     |
| Flakes                             | OSL plus triplanar (Corona 10) versus Glints (recent Corona)                              | Corona version in the scene                                   |
