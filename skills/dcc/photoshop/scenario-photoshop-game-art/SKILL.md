---
name: scenario-photoshop-game-art
description: "Use when making or finishing game art in Photoshop with Scenario: a seamless or tileable texture that shows a seam, a grid or repeating blotches when tiled, a photo turned into a tile, PBR maps (normal, roughness, metallic, AO, height) to export, channel packing (a mask map, ORM, smoothness in alpha), power-of-two sizes, TGA with alpha, data maps that come out washed out or shifted, a paintover or style pass on a Blender or Maya render, an ID or material pass used to select one object, sprites, icons or UI kits with fringes, halos or holes in the cut-out, 9-slice buttons and panels that smear when stretched, or UI colorways. Also when a texture looks seamless in Photoshop but tiles badly in Unity, Unreal or Godot, or a packed map loses its alpha on export."
license: MIT
---

# Game art in Photoshop: textures, render passes, UI (Photoshop 2026)

Expert game art in Photoshop ships pixels an engine can use: a tile whose edges and blotches vanish
when repeated, maps whose values survive export, sprites and UI parts that stretch and filter
cleanly. Scenario supplies the pixels; Photoshop repairs, measures, packs and exports them. If a
sibling skill named here is missing from your available skills, ask the user to install it
(`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and
flag the gap.

**REQUIRED BACKGROUND:** scenario-photoshop-expert (execution channel, round trip, gates).

**Status (2026-10-19):** every call in [`scripts/ps_gameart.py`](scripts/ps_gameart.py) is verified
live on Photoshop 27.11 (macOS) by `test_gameart_live.py` (15 tests; tile checks on real Scenario
textures, one of them seam-repaired), and `ps_audit.deliverable("game-texture")` by
`test_audit_live.py`. Not tested: a style pass on a render, maps landed in a PSD, sprite export with
transparency, `tif` and 16-bit exports, every GUI path, Windows.

## Stance (the expert delta)

- **Offset by half before judging or fixing a seam.** Offset with Wrap Around moves the invisible
  edge to a cross in the middle (Dinda [9_36YihB8I4 01:05], [CyJgXBJVHkU 07:37]). Measured: a blur
  clamped at the canvas edge invents a step at the wrap seam, so `tile_check` offsets first.
- **A tile that passes at the seam can still fail as a pattern.** "Even if you cannot see the edges
  when you zoom in, there might be some repeating patterns" (Dinda [9_36YihB8I4 06:01]). Measured: a
  tiling texture under a 40-level light falloff kept its seams but scored patch range 26.8 (limit
  12), and the seam numbers passed a repair the eye rejected for style drift. Read the tiled preview
  every time.
- **Repair the seam in a narrow band, keep every other pixel, check every take.** Generative fill
  loses resolution on a wide seam, so Dinda fills small pieces [9_36YihB8I4 03:17]; a prompted
  object repeats "in every single box" [CyJgXBJVHkU 09:47]. Measured on one plain texture: a 48 px
  cross (about 5% of 1024) through an image-edit model with a reference and a mask passed both
  gates, with the source unchanged past 32 px from the seam. A 96 px cross through a tiling material
  model's inpaint drifted in style; a mask-edit model returned its input unchanged. Band and model
  changed together, so narrow is only a default.
- **Re-render through a tiling material model only when the look may change.** Measured: at img2img
  strength 0.35 it tiled (ratios 0.97 and 0.93) but changed every pixel (mean 16) and softened the
  stones.
- **Maps are data: no color conversion may touch them.** [added: engine documentation, not the video
  corpus] Unity wants mask maps with sRGB off, composited linear (HDRP manual). Measured: Advanced
  Blending writes a layer into one channel exactly (40, 128, 77, 220 read back); a mode change to
  Grayscale converts through the gray profile. PNG saves no fourth channel, so a packed alpha goes
  to TGA.
- **Value first, color by Gradient Map.** Raskin builds UI "in black and white with an emphasis on
  brightness values" [vo7vwzzgDPk 02:04] and makes colorways from Gradient Map stops, because
  Hue/Saturation "looks ugly" [vo7vwzzgDPk 09:52]. Paintovers follow the same order: gray render,
  Gradient Map, then paint (Frederick [pAIYEsECSRw 20:24]); "the value structure matters much more
  than color" (Octopunish [gjkaYE8_MoE 13:09]).
- **A style pass is a variant layer; the render stays the map.** Tuffan uses "my original render a
  bit as a reference" [j_czTAnOSCM 14:23]; Manners shows "four different approaches to the same
  design problem" [eJN6aLNSnyc 19:16]. Octopunish ranks AI images lowest as reference: you cannot
  tell "where the light comes from" [h1i3X0gqrQs 02:47]. Each Scenario pass lands above the
  untouched render, gated for alignment, judged against it.

## Establish first

| Input                        | Changes                                       | Default when silent                                  |
| ---------------------------- | --------------------------------------------- | ---------------------------------------------------- |
| Asset                        | workflow A, B or C                            | read from the brief                                  |
| Engine and shader            | pack layout, sRGB flags, normal green channel | ask; meanwhile separate maps, nothing packed         |
| Must the texture stay as is? | band repair or re-render                      | stays: band repair                                   |
| Size                         | export size                                   | 1024 square; 2048 for hero surfaces                  |
| Look                         | resample method                               | `bicubic-auto`; `nearest` for pixel art and PSX      |
| Map set                      | maps to request and export                    | albedo, normal, roughness                            |
| Roughness or smoothness      | invert a copy before packing                  | the shader's: Unity HDRP mask alpha holds smoothness |
| Style reference              | references for generation and style passes    | approved assets of the same project                  |
| ID pass                      | object-scoped passes on renders               | ask for one; else Select Subject                     |
| Work folder                  | captures, takes, exports                      | a new folder, never the PSD's own                    |

## Workflow

`sys.path.insert(0, "<this skill>/scripts")`, then `import ps_gameart as GA` (it puts the lead's
`scripts/` on the path) and `import ps_io as IO, ps_gates as G, ps_review as R, ps_audit as A`. The
seam repair also imports `ps_generative as GE` from scenario-photoshop-generative-edit. Each call is
one `ps_run` job; after one raises or times out, recover as the lead's Quality gates say. Code:
[procedures](references/procedures.md).

**Scenario for Photoshop.** When the plugin's tools are connected and signed in, run this skill's
image, edit, upscale, expand and background-removal steps through them, as the lead's Live channel
maps them, gates included; other Scenario steps stay on hosted Scenario MCP. Not tested end to end.
In stage 3's seam repair, `inspect_result_previews` replaces `GE.check`, `edit_selection` replaces
`GE.place_edit`, the Live channel's outside gate replaces `GE.verify`, and `GA.offset` stays a
toolkit step.

**A. Seamless texture with maps**

1. **Read the tile.** `A.doc_state()`, `t = GA.tile_check()`, `GA.tile_preview(out, n=3)`. GATE:
   size, `pow2`, both ratios and `patch_range` recorded; preview opened.
2. **Get a tile.** With no texture yet, generate one with a tiling material model
   (`scenario-textures`), place it, then repeat stage 1. GATE: `seam_ok` and `patch_ok`; no grid or
   repeated blotch in the preview at fit-to-screen.
3. **Repair the seam** when it fails and the texture must stay. `GA.offset()`, `GA.seam_band(width)`
   at about 5% of the side (48 on 1024), `cap = GE.capture(out, polarity=p)`. Scenario: an
   image-edit model with the offset tile as reference and a mask (`scenario-image`), a texture-only
   prompt, 2 takes (in the shoot-out one of two re-laid the stones). Per take `GE.check`,
   `GE.place_edit`, `GE.verify`, then `GA.offset` the repaired layer back, or `tile_check` reads its
   interior and always passes. GATE: `check` flags pass; `untouched`; `tile_check` passes; the cross
   read at 100% and the 3x3 preview at fit.
4. **Re-render instead** when the look may change: a tiling material model at low img2img strength
   (`scenario-textures`), placed as its own layer. GATE: stage 2's gate; the user accepts the look.
5. **Blotches** (`patch_ok` false): `t["cells"]` locates the dark or bright cell; Dinda paints a
   Soft Light layer at 1 to 2% flow and a Color layer at 5 to 10% [9_36YihB8I4 06:34, 07:41]
   ([gui-paths](references/gui-paths.md)). GATE: `patch_range` under 12, preview read again.
6. **Maps.** Extract maps from the approved albedo (`scenario-textures`); `IO.place` each as a layer
   named by role. Plan the pack from the member's `maps` values, not from the engine's slots: the
   members read at authoring time return base color, normal, roughness, metalness and height, and no
   AO. Fill an AO slot with 255 (no occlusion) and say so, unless the user supplies a bake. Confirm
   roughness or smoothness and invert a copy if the shader wants the other. GATE: every map the
   albedo's size; `GA.tile_check(layer=name)` passes per map [added: an extractor can break the
   wrap].
7. **Export.** `A.deliverable("game-texture")` on the master; color maps
   `GA.export_texture(out, size=1024)`; data maps `data=True` (`gray=True` for one channel); packs
   `GA.pack_channels(out, r, g, b, a=...)`, TGA when `a` is set. GATE: `[]`; every result `pow2`;
   values read back equal their sources.

**B. Paintover and style pass on a render**

1. **Land the passes.** The render as the base, `IO.place` for the ID pass (hidden) and a gray clay
   render for color work; Octopunish cuts the render into layers per object [gjkaYE8_MoE 09:19].
   GATE: every pass the render's size, named.
2. **Whole-frame pass.** `cap = IO.export_region(out)`; Scenario: an image-edit or trained style
   model with the render as input or reference and a keep-the-layout clause (`scenario-image`), 3 or
   4 deliberately different takes, quoted as such (different approaches are the point);
   `IO.place(take, "Style pass, take 2", bounds=cap["bounds"])`, one layer per take. GATE: take
   aspect equals the render's; `G.structure("Render", name)` compared across takes; `R.overlay`
   shows no red or cyan fringe on silhouettes.
3. **One object.** `GA.id_select("ID", [r, g, b], fuzz=40)`, then generative-edit's capture, check,
   place and verify. GATE: `bounds` not None; `partial` only the edge; `untouched`.
4. **Judge.** `R.sheet` of the takes beside the render (Frederick compares side by side [pAIYEsECSRw
   26:55]); a grayscale copy for values; no area left "very, very 3D" (Tuffan [j_czTAnOSCM 17:06]).
   GATE: a verdict per take; losing takes hidden and named, in a group named "Takes".

**C. Sprites, icons and UI kits.** Generation (sprites, icon sets, buttons, transparent backgrounds,
style batches) goes to `scenario-game-assets`. Photoshop finishes:

1. **Edges.** `G.halo(layer)` over black and white; Defringe 1 px by hand (pixaroma [vU-_9R-Tq18
   12:48]). Remove Background "missed some spots inside the letters", seen only on a contrasting
   fill (AI2Play [AEXy7F5sJ7M 07:42]). GATE: both rims 8 or less; no holes on a saturated fill.
2. **Text** as live type on a blank generated button [AEXy7F5sJ7M 12:08]; fitting through
   scenario-photoshop-key-art. GATE: font read back.
3. **9-slice.** Keep a straight run in each edge [vo7vwzzgDPk 00:31]; `GA.nine_slice(l, t, r, b)`,
   `GA.nine_slice_check(l, t, r, b)`. GATE: `ok`; else move the insets past the detail. Record the
   insets for the engine's border fields.
4. **Export** one named layer per asset as an unflattened PNG copy, padded past its shadow; atlases
   are packed in the engine. GATE: size, transparency present, rims checked on the file.

Delivery rules (power of two, packing, sRGB, TGA, alpha, atlases) rest on engine documentation and
the PNG specification ([sources](references/sources.md)).

## Numbers

| Value                                      | Relative to                                       | Source                               |
| ------------------------------------------ | ------------------------------------------------- | ------------------------------------ |
| seam ratio < 1.5                           | step across the seam over the mean step elsewhere | measured: tiling 1.07, plain 3.09    |
| patch range < 12                           | 4x4 cell means of a wrap-blurred tile, 0-255      | measured: tiling 9.75, falloff 26.78 |
| band about 5% of the side (48 on 1024)     | tile side                                         | measured, one texture                |
| bias < 12, residual < 6                    | `GE.check` seam ring                              | measured; repair take 2.5 and 3.4    |
| strength 0.35, every pixel moves (mean 16) | tiling material model re-render                   | measured, one texture                |
| 9-slice tol 1.0                            | mean neighbor step per stretched part             | measured: gradient 0.97, rivets 4.9  |
| 256 to 8192 px, power of two, RGB 8-bit    | `game-texture` audit                              | toolkit                              |
| 8192 px                                    | largest texture some GPUs accept                  | Unreal docs                          |
| 4 px                                       | Unity Sprite Atlas padding default                | Unity docs                           |
| Soft Light flow 1-2%, Color 5-10%          | blotch and outlier layers                         | Dinda [9_36YihB8I4 06:34, 07:41]     |
| 1024 working, 128 or 256 final             | PSX texture                                       | NoPoly [QYUh8RuNZgw 07:15, 11:34]    |

Toolkit thresholds are authoring-time: check them on your own images.

## Quality gates

- **Code:** `tile_check` `seam_ok`, `patch_ok`, `pow2`; `GE.check` flags and `GE.verify` `untouched`
  on a repair; `deliverable("game-texture") == []`; every export `pow2`; packed and gray values read
  back exact (alpha within 1); `nine_slice_check` `ok`; `G.halo` rims; `G.structure` relative
  between takes only.
- **Visual:** the 3x3 preview at fit and the cross at 100% (stones or bricks whole across the seam,
  no soft patch, no repeated blotch); each map tiled; style takes beside the render and in
  grayscale; sprites over black, white and a saturated color. Rubric:
  [critique](references/critique.md).

## Common mistakes

| Mistake                              | Looks like                                   | Fix                                    |
| ------------------------------------ | -------------------------------------------- | -------------------------------------- |
| Judging a seam without an offset     | a seamless tile fails, or a seam goes unseen | `GA.tile_check` (offsets first)        |
| Wide band or object prompt           | half stones on the seam, repeated objects    | 5% band, texture-only prompt           |
| Placing an unchecked take            | a no-op, or stones re-laid                   | `GE.check` every take                  |
| Data map exported as color           | roughness or normal values shift             | `data=True`                            |
| Grayscale mode for one channel       | values pass through the gray profile         | `gray=True` or `pack_channels`         |
| PNG for a 4-channel pack             | the alpha map is gone                        | TGA (`pack_channels` refuses PNG)      |
| Smoothness packed where roughness is | shiny where it should be matte               | invert a copy before packing           |
| Non-power-of-two texture             | no mipmaps or streaming in Unreal            | export at a power of two               |
| Hue/Saturation for colorways         | ugly color transitions                       | Gradient Map stop hues                 |
| Detail in a stretched part           | smeared rivets or texture                    | `nine_slice_check`, move the insets    |
| `export_texture` on a sprite         | transparency lost (it flattens)              | unflattened PNG copy                   |
| Style pass pasted over the render    | the render is gone, no comparison            | one variant layer per take             |
| Generic upscaler on a tile           | the repeat breaks at the edges               | tiling-safe upscale, then `tile_check` |

## Handoffs

- **Receives** from scenario-photoshop-expert: document state and round-trip rules; renders and ID
  passes from scenario-blender-lighting-rendering or scenario-maya-lighting-rendering; bakes from
  scenario-blender-uv-baking.
- **Delivers** power-of-two textures and packs, with the layout, sRGB flags and normal convention
  written down, to scenario-unity-expert, scenario-unreal-materials or scenario-godot-expert;
  sprites and 9-slice insets to scenario-unity-ui or scenario-godot-ui. Local fixes go to
  scenario-photoshop-generative-edit, soft takes to scenario-photoshop-upscale-restore, type to
  scenario-photoshop-key-art.
- **Scenario siblings:** `scenario` (connection, `recommend`, quote, Scenario job waiting),
  `scenario-textures` (tiling textures, maps, tiling-safe upscale), `scenario-game-assets` (sprites,
  icons, UI parts, transparent backgrounds), `scenario-image` (inpaint and edits with references,
  style passes).

## Photoshop 2026 notes

- Pattern Preview has no toolkit call, so `tile_preview` writes the repeat as a file.
- Histograms read visible channels only: an alpha channel's raises an error until it is the only
  active channel.
- PNG keeps transparency, not alpha channels; TGA at 32 bits with `alphaChannels` keeps a fourth.
- Color Range on Lab bounds selects one flat ID color with its anti-aliased edge.
- Match Color is grayed out on a smart object; rasterize a copy first [vU-_9R-Tq18 16:06].

## References

- [`references/procedures.md`](references/procedures.md): code for workflows A to C with test
  status. Load before the first job.
- [`references/critique.md`](references/critique.md): the rubric for tiles, maps, style passes and
  UI. Load at every visual gate.
- [`references/expert-notes.md`](references/expert-notes.md): each source's method, the measured
  shoot-out, engine conventions, disagreements. Load when a case is not covered above.
- [`references/gui-paths.md`](references/gui-paths.md): Photoshop and engine menu paths for brush
  work and import settings. Load when a step has no script.
- [`references/sources.md`](references/sources.md): videos, credentials, documentation.
- [`scripts/ps_gameart.py`](scripts/ps_gameart.py): the toolkit (docstring lists every call), on top
  of the lead's scripts.
