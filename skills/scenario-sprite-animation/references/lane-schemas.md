# Per-lane schema notes

Authoring-time observations from live catalog hits. Model availability differs per team and schemas change, so treat every name and number here as a starting point and confirm with `model_schema_get` before running.

## Purpose-trained animation models (pixel cycles and VFX)

Retro Diffusion Animation: a `style` enum picks the animation type and locks the canvas (`four_angle_walking` and `walking_and_idle` 48px, `small_sprites` 32px, `vfx` 24 to 96px). A requested 64px walk cycle is a schema violation, not a prompt problem: generate at the locked size and upscale after on a pixel-preserving route per `scenario-game-assets`.

`returnSpritesheet` flips the output from animated GIF to spritesheet PNG. Set an explicit `seed` on the preview run and repeat the identical payload with `returnSpritesheet` for the sheet, since a seedless preview cannot be re-run to match.

Judge the preview from the downloaded file (`asset_download` with `format="gif"`): `asset_display` shows a still, and the png default flattens it to one frame.

Never slice the GIF preview for engine frames: those come from the same-seed `returnSpritesheet` re-run, sliced on the grid you counted. Verify row order and facing before naming frames.

The `image` reference is converted to RGB without transparency, so flatten a transparent sprite onto a plain field deliberately.

Retro Diffusion Plus takes a reference palette image via `inputPalette` for palette-guided generation, which is the one palette control outside the pixel snapper's color count.

## Alpha and background removal

Prefer native transparency wherever the lane offers it: a model that emits alpha directly leaves no matte to clean up, while per-frame removal can leave a fringe that reads as a seam once the frames cycle. Search for an image model whose schema carries a background option and read it (`search` `"transparent background"`). At authoring time the GPT Image family exposed `background` with `auto`, `opaque`, and `transparent`, the transparent value marked Preview, so confirm it with `model_schema_get` and check one frame before committing a batch.

Where the lane has no native alpha, extract first, then run an image background remover on each frame (`search` `"background removal"`): the strongest hits are image models, and per-frame cutouts came back cleaner than the video-level pass in live runs. A remover's HD mode silently no-ops below its input floor, so upscale past it for better mattes on glows.

Removing at video level before extraction also works when the output format carries alpha (`mov`, not `mp4`).

A transparent request can come back stored in a container without alpha, which is why the frame check in step 4 is not optional.

## Video lanes

The live hits were keyframe pinning on a 24fps grid (FLUX.3 Keyframes), start plus end frames with an fps enum (LTX), and a style preset with a seed (PixVerse). Turn prompt rewriting off (expansion and optimizer toggles) when exact wording carries the character or motion script.

## Reading a deprecation tag

A deprecation tag names a replacement (`deprecated:model_x`) or stands bare, and the pointer can cross capabilities, so prefer the replacement only when its schema still covers the need.

## Packaging pixel frames

Snap each frame individually with the same color count and seed, never the assembled sheet: the snapper collapses a sheet to one global grid and loses per-frame detail.

Skip the pass altogether when the frames already sit on the art's native grid. The snapper re-detects a grid of its own, and on frames that were already pixel-native it regridded 384x288 down to 69x52 and took the scene with it. Probe one frame before running the set.

Where snapping does apply, the snapped frames land on their own native grids a few pixels apart and need rescaling to one common size before assembly, since padding without rescaling leaves the character pulsing in size across frames. Scenario Resize Image takes `width`, `height`, and `fit` and exposes no interpolation control, so check one rescaled frame rather than assuming it snapped cleanly.

## Assembler timing

GIF frame delays quantize to 10ms, so any fps that is not a divisor of 1000 is silently re-timed: a 12fps request lands at 100ms per frame, which is 10fps. Build the engine deliverable as mp4, which holds exact timing, and treat the GIF as a preview. Count the frames that came back, because the assembler trades frame accuracy to hold total duration and does it in both directions: one run returned 7 frames from 8 inputs, another returned 20 from 16, duplicating frames and re-timing an 8fps request to 100ms each.

## An aspect ratio the model ignored

A video model can ignore both `aspectRatio` and a resolution enum and snap to its own latent grid: a 4:3 720p request came back 1088x800, which is neither. Probing the delivered file is what catches it.

The geometric fix is a resize: Scenario Resize Video for clips and Scenario Resize Image for extracted frames take the same `width`, `height`, and `fit`. `fit: "cover"` scales the picture to fill the box and center-crops the overflow, so 1088x800 lands on an exact 384x288 with nothing squashed; `contain` (the default) fits inside the box without cropping, so the output can come back smaller than the box, and `stretch` forces the box size at the cost of geometry. Confirm with `model_schema_get`. There is no crop offset: the crop is centered, so a subject off to one side may need the aspect picked at generation time instead. Scenario Padding Remover trims uniform borders from images only. The reframe models recompose generatively instead of cropping, so they break frame-to-frame consistency and do not belong inside a sequence.

So `cover` is the answer for an exact ratio. The fallbacks, for when the crop would cut into the subject, are `stretch` with the distortion recorded (1088 against the 1066.67 that exact 4:3 wants is 2.0%) or `contain`, which keeps the whole picture but does not land the ratio (no bars are added; the output is simply smaller than the box). Either way, confirm the delivered canvas before any downstream work: every stride and seam number depends on it.

## Sourcing the still for a scene loop

The loop lanes assume a still already exists. Where it does not, treat it as a separate job with its own budget: it anchors every frame that follows, and no amount of animation work rescues a still that misses the brief.

Search for a pixel-art image model and read its ceiling before planning a canvas (`search` `"pixel art"`). At authoring time Retro Diffusion Plus capped `width` and `height` at 384, so the largest exact 4:3 it delivers is 384x288, and `removeBg` defaults to false. Confirm with `model_schema_get`.

Check subject-critical detail (counts, poses, who is holding what) against the brief before animating. These models are weak at exact counts: a five-child campfire came back as four across three prompting strategies (a count word, an explicit seating layout, then five children enumerated by shirt color), and the platform's own auto-caption confirmed the miss independently. Where a count or composition has to be exact, iterate the still per `scenario-refine-loop` and keep those attempts on their own budget line rather than spending the animation allowance on them.
