# Critique rubric: archviz production

Use after each stage. Measurable lines come from P0 to P11 results; visual lines come from one
contact sheet or one full-size render (read a single image at full size only to inspect a detail). A
stage passes when every measurable line passes and no visual line scores "fail".

## Intake (P0, P1)

Measurable:

- Link preset recorded: Combine Entities choice, Lights flag, Daylight System flag, Use Scene
  Material Assignments on Reload decided before texturing.
- Light count per class after a Revit FBX link: no long list of unique copies of one fixture.
- Exposure control on when a daylight system linked; one test render not overexposed.
- DWG linked with Rescale and the right incoming units.

## Brief and cameras

Measurable:

- One brief per view: story, feature, light, season, palette, 2 to 3 real photo references.
- Each view camera: focal set (not FOV-only), auto vertical tilt on for exteriors, height in band:
  interior about 1.0 m, exterior eye 1.4 to 1.7 m, aerial equals drone altitude.
- 4 to 8 candidates rendered per view before sign-off. Visual:
- Verticals parallel to the frame edge (two-point perspective) unless the brief asks for drama.
- Main feature on a third line or deliberately centered (centered only for straight, symmetric, wide
  interiors per f40Sszm3Bqk).
- Horizon placed on purpose; no tangents where a roof edge touches the frame.
- The angle carries the story: low for power, aerial for context, wide for space.

## General feeling

Measurable:

- No base color at 0 or 255 per channel (audit owned by scenario-3dsmax-materials).
- HDRI rotation recorded; two helper lights at most at this stage. Visual (squint test at thumbnail
  size):
- The brightest area is the intended focus.
- Light and dark masses match the reference photo.
- Walls and floor carry the intended warmth.

## Materials and light (order checks only)

- Foreground textured before background; ceiling and far rooms kept simple.
- Bump and displacement judged on a pre-final render, not the denoised interactive preview.
- Nothing reads as a render-to-render comparison: compare with the reference photo side by side.

## Vegetation and scatter

Measurable:

- Every scatter object on a named layer; sources pass the pivot check (base center, 1 cm tolerance);
  area splines closed.
- Viewport display capped (Max instances, Max Items, previz type) so orbiting stays usable.
- Large scatters use camera clipping with an Extend view where shadows or reflections matter.
- Species count per scatter: 2 to 3 similar species with frequency weights.
- Proxies only where RAM is short; otherwise scattered meshes (Forest Pack instances them natively).
- Forest materials set through Material Override; background plants with reflection Max Depth about
  1 and no refraction plus opacity. Visual:
- No grid look, no visible tile repeat in lawns, no hard density edge at area borders.
- No instances floating or sunk; no trees on steep slopes or in roads; cars face along lanes.
- Species hue, saturation and value in one family; season variants intentional.
- Foreground plants hand placed; shadows from out-of-frame trees lead the eye.
- Alpha-map leaves at 100%: no halo or fringe at leaf edges.

## Entourage and people

- Scale: people against a 2.1 m door read 1.6 to 1.9 m [added].
- Feet on the ground; no duplicate person visible twice in one frame [added].
- In animation: people far from camera, speeds and motion phases varied.

## Aerial match

- Render size equals photo size; focal equals EXIF 35 mm-equivalent.
- Overlay at 50%: roads, shorelines and corners coincide within a few pixels at review size [added].
- Shadows continuous across the model boundary; shadow-only surroundings absent from beauty.
- Render softness and grain match the photo after blur, noise and one sharpen.

## Animation

Measurable:

- fps identical in 3ds Max, Anima and Vantage; range equals seconds x fps.
- One test frame timed on the heaviest frame; `render_budget` hours with margin under the deadline.
- Vantage: lights re-enabled one by one after conversion; memory estimate under GPU memory before
  launch.
- Output: numbered sequence, lossless (PNG or EXR) when grading follows, JPEG only for farm drafts.
  Visual:
- 10 consecutive frames: no flicker on static walls and foliage, no fireflies.
- Moves: steady speed, linear where the shot continues, eased where it starts or ends, a pause after
  cuts.
- No popping at scatter borders or camera clipping edges.

## Revision and delivery

- Every round saved as a new numbered file; approved versions untouched.
- Before and after sheet shows only the requested change.
- Final files: agreed size, names `<project>_<view>_v###`, opened at 100%, no missing textures (pink
  or black areas), no denoiser smearing on fine detail.
- Render elements present for post: Cryptomatte, wire color, Z-depth, light mix or light select.
- Farm package: zero missing assets; farm 3ds Max version equal to or newer than the scene's.

## Scoring

- pass: meets the line; warn: visible only at 100% or fixable in post; fail: visible at review size
  or breaks the brief.
- Two or more fails in one stage: return to that stage, do not patch downstream.
