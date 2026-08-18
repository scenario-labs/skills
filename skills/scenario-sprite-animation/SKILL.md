---
name: scenario-sprite-animation
description: "Use when animating 2D game art with Scenario: character walk cycles, idle animations, sprite sheets, animated GIFs, frame-by-frame pixel art animation, VFX loops such as fire, smoke, or sparks, turning an existing character sprite into animation frames, or slicing a sprite sheet into engine-ready frames for Unity, Godot, or Unreal. Keywords: sprite sheet, spritesheet, walk cycle, idle animation, animation frames, pixel art animation, VFX sprites, GIF."
license: MIT
---

# Scenario Sprite Animation

## Overview

Prompting a generic image model for "a sprite sheet, walk cycle, 8 frames" returns a picture of a sprite sheet: uneven cells, poses that do not tween, a character that mutates across frames. Real frame sequences come from two lanes: purpose-trained animation models that return an animated GIF or a true sheet in one run, and image-to-video plus frame extraction when the art is larger than pixel scale. Statics, cleanup, and export: `scenario-game-assets`. The video lane: `scenario-video` and `scenario-video-editing`. Connection and the core loop: see the `scenario` skill. If a sibling skill named here is missing from your available skills, ask the user to install it (`npx skills add scenario-labs/skills --skill <name>`); unattended, proceed from tool schemas and flag the gap.

## Quick reference

| Need                    | Route                                                                                             |
| ----------------------- | ------------------------------------------------------------------------------------------------- |
| Find the animation lane | `search` with `target="models"`, `query="sprite animation"`, `public=true`                        |
| Read the contract       | `model_schema_get`: styles, locked sizes, and output toggles are all per model                    |
| Frames from a sheet     | `search` `"slice"`: a grid slicer returns each cell as its own file (up to 6x6 at authoring time) |
| Larger sprites          | Image-to-video on the still, then frame extraction (`scenario-video-editing`)                     |
| Pixel cleanup           | `search` `"pixel"`: grid snapping and palette reduction, per `scenario-game-assets`               |

The authoring-time hit for the first lane (Retro Diffusion Animation; re-discover rather than hardcode) shows why the schema is the contract. A `style` enum picks the animation type (`four_angle_walking`, `walking_and_idle`, `small_sprites`, `vfx`), and each style locks its canvas: the walking styles only support 48, `small_sprites` only 32, `vfx` 24 to 96. A requested 64px walk cycle is a schema violation, not a prompt problem: generate at the locked size and upscale after. `returnSpritesheet` flips the output from animated GIF to a spritesheet PNG, a `seed` makes a run reproducible, and the optional `image` reference is converted to RGB without transparency, so flatten a transparent sprite onto a plain field deliberately before referencing it.

## Worked example: a knight walk cycle for a pixel RPG

1. `search` for the lane as above, confirm the pick with the user (unattended, take it from the task instructions, else the top hit), then `model_schema_get` it.
2. If an approved static knight exists (made per `scenario-game-assets`), flatten it onto a plain background and `upload_asset` it as the `image` reference. Describe the knight in the `prompt` anyway: the reference steers, the words decide.
3. `model_run` with the walking style, `returnSpritesheet=true`, and a noted `seed`, then `jobs_wait` as usual.
4. `asset_display` the sheet and count its grid, then run the slicer with that grid to get one PNG per frame.
5. Per-frame finishing per `scenario-game-assets`: background removal where frames need alpha, pixel cleanup for grid and palette, upscaling on a pixel-preserving route, `asset_download` with `format="png"`.
6. Verify the cycle two ways: step the frames in order, and compare each frame's alpha bounding box, since a foot escaping the box makes the sprite hop in engine.

## Common mistakes

- One prompt at a generic model for the whole sheet: purpose-trained animation models return frame sequences; everything else returns an illustration of one.
- Fighting a locked canvas size: per-style sizes are contracts; upscale after generation, never in the request.
- Slicing the GIF for frames: the GIF is the preview format; when the engine needs frames, run with the spritesheet toggle on (a kept `seed` makes the re-run reproducible) and slice that.
- Referencing a transparent sprite as-is: the reference input drops transparency during conversion, leaving a background you did not choose behind the character.
- Photo upscalers on pixel art frames: they invent texture; use the pixel-preserving routes in `scenario-game-assets`.
- Accepting the cycle frame by frame without playing it: tween errors live between frames; the GIF output exists exactly for that preview.
- Ping-pong loops assembled blind: decide whether the style loops forward or bounces by watching the GIF before wiring engine playback.
