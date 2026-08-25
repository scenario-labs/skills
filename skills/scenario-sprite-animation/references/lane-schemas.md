# Per-lane schema notes

Authoring-time observations from live catalog hits. Model availability differs per team and schemas change, so treat every name and number here as a starting point and confirm with `model_schema_get` before running.

## Purpose-trained animation models (pixel cycles and VFX)

Retro Diffusion Animation: a `style` enum picks the animation type and locks the canvas (`four_angle_walking` and `walking_and_idle` 48px, `small_sprites` 32px, `vfx` 24 to 96px). A requested 64px walk cycle is a schema violation, not a prompt problem: generate at the locked size and upscale after on a pixel-preserving route per `scenario-game-assets`.

`returnSpritesheet` flips the output from animated GIF to spritesheet PNG. Set an explicit `seed` on the preview run and repeat the identical payload with `returnSpritesheet` for the sheet, since a seedless preview cannot be re-run to match.

Judge the preview from the downloaded file (`asset_download` with `format="gif"`): `asset_display` shows a still, and the png default flattens it to one frame.

The `image` reference is converted to RGB without transparency, so flatten a transparent sprite onto a plain field deliberately.

Retro Diffusion Plus takes a reference palette image via `inputPalette` for palette-guided generation, which is the one palette control outside the pixel snapper's color count.

## Alpha and background removal

Extract first, then run an image background remover on each frame (`search` `"background removal"`): the strongest hits are image models, and per-frame cutouts came back cleaner than the video-level pass in live runs. A remover's HD mode silently no-ops below its input floor, so upscale past it for better mattes on glows.

Removing at video level before extraction also works when the output format carries alpha (`mov`, not `mp4`).

A transparent request can come back stored in a container without alpha, which is why the frame check in step 4 is not optional.

## Video lanes

The live hits were keyframe pinning on a 24fps grid (FLUX.3 Keyframes), start plus end frames with an fps enum (LTX), and a style preset with a seed (PixVerse). Turn prompt rewriting off (expansion and optimizer toggles) when exact wording carries the character or motion script.

## Reading a deprecation tag

A deprecation tag names a replacement (`deprecated:model_x`) or stands bare, and the pointer can cross capabilities, so prefer the replacement only when its schema still covers the need.
