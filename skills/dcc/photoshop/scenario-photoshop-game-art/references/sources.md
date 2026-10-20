# Sources behind scenario-photoshop-game-art

Videos were read through their auto-generated captions. Timestamps are caption chunk starts. Titles
that name a generative model are paraphrased and marked "(paraphrased)". Credentials come from the
channel and the video itself; "not stated" means neither gives one.

## Videos

| Video                                                      | Title (date, length)                                                                                 | Expert and credential                                                  | Best for                                              | Timestamps                                                                  |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------- |
| [9_36YihB8I4](https://www.youtube.com/watch?v=9_36YihB8I4) | Turn Any Texture Into Seamless Pattern in Photoshop! (2024-06-19, 12:17)                             | Unmesh Dinda, Photoshop educator, PiXimperfect                         | offset, seam fill, dodge and burn of repeats          | 00:00, 01:05, 02:11, 02:45, 03:17, 04:58, 05:29, 06:01, 06:34, 07:41, 08:14 |
| [CyJgXBJVHkU](https://www.youtube.com/watch?v=CyJgXBJVHkU) | No Credits, Infinite Resolution: I HACKED Photoshop's Gen Fill (2026-07-22, 10:59)                   | Unmesh Dinda, Photoshop educator, PiXimperfect (makes the panel shown) | tiled fills, re-check by offsetting, no object prompt | 00:00, 02:08, 07:37, 08:11, 08:43, 09:47                                    |
| [vo7vwzzgDPk](https://www.youtube.com/watch?v=vo7vwzzgDPk) | Casual Game UI Button, Photoshop tutorial (2025-02-25, 12:15)                                        | David Raskin, casual-game UI channel; credential not stated            | squircle, value-first UI, Gradient Map colorways      | 00:31, 02:04, 02:35, 05:41, 09:21, 09:52, 10:23                             |
| [QYUh8RuNZgw](https://www.youtube.com/watch?v=QYUh8RuNZgw) | How To Make Retro PSX Weapons (Blender/Photoshop Tutorial) (2026-07-11, 12:49)                       | NoPoly, indie 3D artist, about 3 years (self-described)                | texture from photo pieces, 128 or 256 finish          | 07:15, 10:30, 11:02, 11:34, 12:06                                           |
| [AEXy7F5sJ7M](https://www.youtube.com/watch?v=AEXy7F5sJ7M) | Match-3 game design start to finish in 8 hours (paraphrased) (2026-03-26, 43:24)                     | AI2Play, host Ioan; credential not stated                              | asset order, cut-out cleanup, one PSD per screen      | 01:06, 07:42, 08:16, 08:48, 12:08, 13:13, frames 35:35 and 40:05, 40:53     |
| [vU-_9R-Tq18](https://www.youtube.com/watch?v=vU-_9R-Tq18) | ComfyUI Tutorial Series Ep 30: Game Design with AI and Photoshop (2025-01-21, 29:43)                 | pixaroma; credential not stated                                        | icon sheets, Defringe, Layers to Files, test in place | 04:56, 10:35, 12:48, 13:23, 14:27, 15:32, 16:06, 17:13                      |
| [gjkaYE8_MoE](https://www.youtube.com/watch?v=gjkaYE8_MoE) | How I make interior concept art with Blender + Photoshop (2026-09-02, 16:55)                         | Octopunish, game concept artist and course author (self-described)     | render cut into layers, grayscale value check         | 09:19, 09:53, 12:36, 13:09                                                  |
| [h1i3X0gqrQs](https://www.youtube.com/watch?v=h1i3X0gqrQs) | How I made an entire fantasy village in Blender + Photoshop (2026-07-29, 25:38)                      | Octopunish, game concept artist and course author (self-described)     | AI as reference, distinct variants, values            | 02:47, 07:07, 07:39, 21:20, 21:54, 23:32                                    |
| [j_czTAnOSCM](https://www.youtube.com/watch?v=j_czTAnOSCM) | From Blender to Photoshop: Stylized Concept Art Overpainting with Jourdan Tuffan (2025-03-31, 21:48) | Jourdan Tuffan, concept artist, Art Forge Academy                      | render as guide, no 3D leftovers, Liquify last        | 12:09, 14:23, 17:06, 19:55                                                  |
| [eJN6aLNSnyc](https://www.youtube.com/watch?v=eJN6aLNSnyc) | CODA Open Lab, Designing Ticket Machine with Gavin Manners, Photoshop & Blender (2026-04-08, 58:41)  | Gavin Manners, principal concept artist at id Software                 | several approaches to one problem                     | 19:16, 19:47                                                                |
| [pAIYEsECSRw](https://www.youtube.com/watch?v=pAIYEsECSRw) | Environment Concept Art, Sketching, Architecture Design, Illustration (2025-12-05, 36:29)            | Grady Frederick, professional game concept artist                      | gray 3D to Gradient Map palette, side-by-side review  | 19:47, 20:24, 26:55                                                         |

- **9_36YihB8I4 is from 2024.** It stays because Offset, Pattern Preview and dodge and burn are
  unchanged in Photoshop 2026, and CyJgXBJVHkU (2026) repeats the offset step.
- **AEXy7F5sJ7M has a caption gap.** Captions stop after the chunk at 14:18 and resume at 39:45. Two
  citations inside the gap rest on frames read by eye: at 35:35, one PSD per screen with layers such
  as loading_bar_full and Background; at 40:05, tile layers named tile_scarab, tile_pyramid,
  tile_lotus, tile_eye and tile_ank, transformed into a board cell.
- **No video covers delivery formats** (power of two, packing, sRGB, TGA, premultiplied alpha,
  atlases). Those rules rest on the documentation below.

## Documentation

All pages accessed 2026-10-19 and read for the facts listed.

| Page                                                                                                                                                    | Version         | Used for                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | --------------------------------------------------------------------------- |
| [Importing Textures](https://docs.unity3d.com/2022.3/Documentation/Manual/ImportingTextures.html)                                                       | Unity 2022.3    | power of two ideal, non-power-of-two for GUI; PNG, PSD, TGA; PSD flattened  |
| [Default texture type](https://docs.unity3d.com/Manual/texture-type-default.html)                                                                       | Unity 6.6       | sRGB (Color Texture), Alpha Is Transparency dilation, Non Power of 2        |
| [Normal map texture type](https://docs.unity3d.com/Manual/texture-type-normal-map.html)                                                                 | Unity 6.6       | Flip Green Channel (the page names no convention)                           |
| [Mask and detail maps](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/Mask-Map-and-Detail-Map.html)           | HDRP 17.0       | R metallic, G AO, B detail mask, A smoothness; sRGB off; linear composite   |
| [9-slicing](https://docs.unity3d.com/2022.3/Documentation/Manual/9SliceSprites.html)                                                                    | Unity 2022.3    | L, R, T, B borders; Full Rect; Sliced or Tiled; Transform scale bypasses it |
| [Sprite Atlas properties reference](https://docs.unity3d.com/2022.3/Documentation/Manual/class-SpriteAtlas.html)                                        | Unity 2022.3    | menu path, padding 4 px default, Allow Rotation, Tight Packing              |
| [Textures in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/textures-in-unreal-engine)                                      | Unreal 5.8      | power of two mipmapped and streamed, 8192 GPU cap, packing, roughness alpha |
| [Texture format support and settings](https://dev.epicgames.com/documentation/en-us/unreal-engine/texture-format-support-and-settings-in-unreal-engine) | Unreal 5.8      | supported sizes up to 8192                                                  |
| [PNG Specification, Third Edition](https://www.w3.org/TR/png-3/)                                                                                        | W3C, 2025-06-24 | section 6.2: "PNG does not use premultiplied alpha"                         |

Not usable at access time: Unreal's texture properties and texture compression settings pages
rendered empty, and an older Unreal texture page refused access. So Unreal's per-texture sRGB and
compression setting names, and which engine expects which normal map green direction, are not stated
as fact in this skill. Godot's import documentation was not checked.

## Measured

- **`test_gameart_live.py`** (15 tests, Photoshop 27.11, macOS, 2026-10-19): tile check on two real
  Scenario textures (a tiling material model's output and a texture model's output with no tiling
  control), the second one seam-repaired, under a light falloff and mirrored; offset and seam band;
  gray data export; power-of-two resize; channel pack with alpha to TGA and PNG refused; exports
  into a folder that does not exist yet; 9-slice check on flat, gradient and detailed frames;
  ID-color selection. Tiled previews read by eye.
- **Seam repair shoot-out** (real Scenario jobs on the plain texture, offset by half, 2026-10-19):
  four routes, results in [expert-notes.md](expert-notes.md). The kept take is the live suite's
  repaired fixture.
- **`test_generative_live.py`** (scenario-photoshop-generative-edit) runs `capture`, `check`,
  `place_edit` and `verify`; **`test_audit_live.py`** runs `deliverable("game-texture")`.
