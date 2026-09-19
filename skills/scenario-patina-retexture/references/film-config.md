# Film configuration and commands

`film.py` drives Blender and ffmpeg locally and makes no Scenario calls. Requirements: Blender 4.2 or newer with EEVEE ray tracing (written against 5.x), Python 3 with Pillow and numpy, ffmpeg and ffprobe with libx264.

```sh
python3 scripts/film.py config.json pilot
python3 scripts/film.py config.json run
python3 scripts/film.py config.json status
python3 scripts/film.py config.json assemble
```

`--blender PATH` names the executable; otherwise the config `blender` key, the `BLENDER` environment variable, `blender` on `PATH`, and the macOS application bundle are tried in that order.

## Modes

- `pilot` renders the first and last frame of every shot for both passes at half resolution, writes `Pilot Contact.jpg` (before above after, per shot), and a `pilot_estimate.json` whose time figure scales the pilot by the pixel ratio and includes process startup: a rough estimate, not a promise.
- `run` renders every source frame at native resolution in bounded Blender batches, skipping frames that already exist and decode, saves `Original Camera Animation.blend` and `Patina Camera Animation.blend` (the editable scenes), then assembles and verifies.
- `assemble` repeats the assembly and verification after an interrupted encode.
- `status` writes and prints `status.json`: stage, frames rendered per pass, frames required, run folder.

## Configuration

Copy [example-config.json](example-config.json) and replace everything that describes the asset. `project_root` is relative to the JSON file; `before` and `after` are relative to `project_root`. Both scenes must hold the same mesh geometry, transforms, and object names (only the materials differ): the run compares a geometry hash and a camera hash between the two passes and stops on a mismatch.

| Field                                  | Default                                                       | Effect                                                                                                            |
| -------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `before`, `after`                      | required                                                      | The two packed `.blend` scenes                                                                                    |
| `shots`                                | required                                                      | Ordered list, see below                                                                                           |
| `title`, `before_label`, `after_label` | `PBR MATERIAL STUDY`, `Original materials`, `PATINA textures` | Caption text on the stacked master                                                                                |
| `width`, `height`                      | `2368`, `1332`                                                | Native panel resolution; the stacked master adds padding and captions (2560x3200 at these)                        |
| `fps`, `source_fps`                    | `24`, `12`                                                    | Delivery cadence and rendered cadence; 12 is interpolated to 24, 24 renders every frame                           |
| `shot_seconds`, `transition`           | `5.5`, `0.5`                                                  | Raw shot length and crossfade overlap                                                                             |
| `samples`                              | `24`                                                          | EEVEE render samples                                                                                              |
| `workers`                              | `1`                                                           | Simultaneous Blender processes, 1 or 2; two only with measured memory headroom                                    |
| `rig_scale`, `rig_origin`              | `1`, `[0, 0, 0]`                                              | Scale and ground-level center of the light rig: the asset's height divided by about ten, and its footprint center |
| `environment`                          | Blender's bundled studio HDRI                                 | Path to a local HDRI for reflections                                                                              |
| `output`                               | `video/automatic`                                             | Parent of the fingerprinted run folders                                                                           |
| `font`, `bold_font`                    | first found system font                                       | Caption fonts for Pillow                                                                                          |
| `blender`, `ffmpeg`, `ffprobe`         | see above, `ffmpeg`, `ffprobe`                                | Executables; none of the three enters the run fingerprint                                                         |

Final duration is `shots x shot_seconds - (shots - 1) x transition`: twelve default shots make 60.5 seconds.

### Shots

Each shot has `name`, `detail` (caption), `start`, and `end`. An endpoint is `[target_xyz, viewing_direction_xyz, visible_width]`: the point the 85 mm camera looks at, the direction from the target toward the camera (not normalized), and how wide the frame is at the target in scene units. Target and width ease smoothly between the endpoints. A narrow reflection strip light sweeps across the subject during every shot, sized from `rig_scale`, so roughness and normal response move on screen.

Take targets from `inventory.json` bounds; check both endpoints on the pilot sheet for clipping and occlusion. The example plan opens wide, spends ten shots on one material each (glazed ceramic, brass, roof tiles, timber, plaster, canvas, a mixed shopfront, paving, painted metal, signage), and closes with a pullback. Its coordinates were framed for one public street diorama and fit nothing else.

## Fast preset and its cost

The scripts set EEVEE with ray-traced reflections at half resolution, denoised, one shadow ray and six shadow steps, AgX view transform, no depth of field, a packed studio environment plus a warm grazing key, a cool rim, a soft fill, and the moving strip. Rendering 12 fps sources for slow moves and interpolating to 24 fps halves render time at the price of motion detail; keep `source_fps` 24 for fast motion. Fewer samples leave more noise in close-ups, so read the sweep sheet before delivery.

## Run folder and resume

The run folder name is a fingerprint of the two input files, the scripts, and the config (minus `workers`, executables, and `output`). Resume works only while nothing in that set changes; a packed `.blend` is what makes texture edits part of the fingerprint. Partial or corrupt frames and clips are moved to an `archive/` folder before replacement, never overwritten in place.

Outputs in the run folder: `PATINA Comparison.mp4` (stacked master), `PATINA Comparison Share.mp4` (1440 wide), `Original Matched Camera.mp4` and `Patina Matched Camera.mp4` (the two landscape passes), the two editable scenes, `review/` (one mid-shot still per shot, `Sweep Contact.jpg` sampled at 2 fps across the master, `Final Contact.jpg`), `verification.json` (frame counts and durations from ffprobe for every movie, and the sweep path), and the frame and clip caches.

Keep the movies, scenes, source assets, textures, manifests, and verification files. When asked to clean up, move `frames/`, `clips/`, `sequence/`, pilots, and old runs to an archive outside the delivery folder; archiving keeps files, it frees nothing, so say so.
