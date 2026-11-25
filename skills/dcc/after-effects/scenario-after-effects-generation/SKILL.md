---
name: scenario-after-effects-generation
description: "Use when an After Effects project needs generated media from the Scenario MCP: style frames, transparent cutouts, parallax planes, depth maps, video plates, smoke on black, 3D models, HDRIs, voice, music or sound effects. Also when the AI image has a halo, the loop jumps, the clip flickers, the parallax tears, the GLB does not show, the voice clips, or someone asks where an asset came from."
license: MIT
---

# Generated media in After Effects: generate, land, prepare

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means every generated file is measured before it is trusted, lands with the right
alpha, frame rate, loop and size, and carries its provenance. If a sibling skill named here is
missing from your available skills, load it with `skill_get` (Scenario MCP) or ask the user to
install it (https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas
and flag the gap.

**REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit, version
traps).

## Stance (the expert delta)

1. **Lock the audio and the style frame first, then generate to them.** The voiceover fixes the cut
   length; the style frame fixes look and palette (agent walkthrough 3AIZ4FT61aw 00:18:51). Grade
   real footage before you export stills for generation (Stalman 4N_rE8N8O_M 00:01:30).
2. **Generate parts for the composite.** Ask for a slow or locked camera and empty graphic space
   (Jonathan Lam ZPajb_N6tBs 00:01:00), no camera move in the prompt (Mickmumpitz _n0ir5V5tX4
   00:10:49), the target aspect at the source (Tom Lulofs XsbXd4pirnE). Camera moves, parallax and
   type are added in After Effects.
3. **Measure what arrived; never trust the extension.** Measured on 27.0: a cutout's body alpha
   topped at 253, an upscaler dropped alpha, a 3D download was a .blend, a layer split had binary
   edges and holes. Probe before import [added].
4. **Use generation only for the impossible bit, then hide the seam.** Color match, a speed ramp
   near 400 %, motion blur and a whoosh hide the join (Stalman 4N_rE8N8O_M 00:02:51, 00:06:06 to
   00:08:55). Prompt "keep the camera speed constant" so your own ramp stays controllable (00:03:39
   to 00:04:27).
5. **Pixel-peep every generated frame.** Check compression artifacts, logo and object continuity
   between frames, hands and text (Jake In Motion QLZNiwaKqWg 00:08:28).
6. **Fix size with resolution, not Scale.** Upscale stills before image-to-video (Yaroflasher
   K67WetORDEo 00:04:20); in the comp use Detail-preserving Upscale rather than dragging Scale
   (Jonathan Lam ZPajb_N6tBs 00:12:10). Measured: twice the edge detail of a 200 % layer.
7. **Keep provenance on the asset.** Job id, model, prompt and seed go in `item.comment`,
   `layer.comment` and a sidecar file. A client or a later agent must be able to regenerate or
   replace the file [added].
8. **An agent can judge stills; ease needs a hand.** Generated motion arrives slow and evenly timed
   (Yaroflasher 00:09:42). Speed it up with Time Remap (stage 5), and leave easing and the edit to
   animation and motion-production (3AIZ4FT61aw 00:13:12).

## Establish first

| Input                           | Why it changes the plan                               | Default                                                                             |
| ------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Deliverable size, fps, length   | generation size, conform, loop length                 | 1920x1080, 24 fps                                                                   |
| Locked audio (voiceover, music) | cut length and cue frames                             | generate voiceover first                                                            |
| Style frame approved            | every later prompt references it                      | one style frame, signed off                                                         |
| Scenario team and project       | every Scenario MCP call needs both                    | ask which project receives the assets, or use the one already set; never create one |
| Which parts are generated       | everything else stays hand-made                       | list per shot                                                                       |
| Renderer                        | 3D models and environment light need Advanced 3D      | Classic for 2.5D, Advanced for models                                               |
| Channel                         | bridge for landing and checks; aerender for the final | bridge                                                                              |

## Procedure

Full jobs: [references/procedures.md](references/procedures.md). Helper:
[scripts/gen.jsx](scripts/gen.jsx) (`AEX.gen`), loaded with
`ae.py run job.jsx --lib <skill>/scripts/gen.jsx`.

### 1. Plan the generated parts

Goal: a shot list where each generated asset has a job, a target size and a fps. For multi-step
chains, run the catalog tool `plan_generation` (`scenario_tool_execute_read`), then `recommend`
(quality priority) per asset type. Pick the best and newest model it returns. For 3D, prefer the
newest first-party model it offers. Prompting and model craft live in the Scenario skills:
`scenario-image`, `scenario-image-editing`, `scenario-video`, `scenario-3d`, `scenario-skyboxes`,
`scenario-audio`. GATE: every asset row names its `recommend` call, target size, fps and the sibling
that takes it over.

### 2. Generate and download

Before a full video render, preview the start frame and run small variations (ZPajb_N6tBs 00:03:30);
prompt detailed for control, short for variety (K67WetORDEo 00:08:11). Upscale the still first when
the clip is reframed or delivered above the generator's size (stance 6). Run `model_schema_get`,
`model_run`, `jobs_wait`, then `asset_download`. For a 3D asset, `asset_download` can return the
original source file (measured: a compressed .blend); take the GLB from the asset `url` from
`asset_get` and check its magic bytes (`glTF`). A speech model can return a second asset with word
timings: download both. For a supplied still, the depth map and the cutout have their own route
(procedure 11). GATE: `file` and `ffprobe` agree with the expected type; a sidecar `<asset>.json`
holds job id, asset id, model, prompt and seed.

### 3. Probe before import

```bash
ffprobe -v error -show_entries stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,nb_frames,color_transfer,sample_rate,channels -of compact plate.mov
magick identify -format "%wx%h %[channels] opaque=%[opaque]\n" cutout.png
ffmpeg -nostats -i vo.wav -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -A12 Summary
```

GATE: alpha, fps, frame count, color tags, sample rate, loudness and true peak written per file.

### 4. Land each file

`AEX.gen.land(path, {name, alpha, matte, fps, prov})` imports into a "generated" bin, sets the alpha
mode and the matte color, conforms the fps and writes the provenance comment.
`AEX.gen.place(comp, item, {fit, anchorPx, at, scale})` adds it and copies the comment to the layer.
Per type, what to ask for, what arrives and how to set it: the landing table in
[references/procedures.md](references/procedures.md). GATE: `AEK.audit.footage()` lists no missing
file; `AEX.gen.upscaled(comp)` is empty, or the layer is replaced by an upscaled file.

### 5. Prepare per type

Goal: the asset holds up in the composite. Fix alpha body, fringe, loop, scale, depth tearing and
levels per the table. Cases with numbers are in
[references/procedures.md](references/procedures.md).

- Slow clip: Time Remap, new end key first, then remove the old.
- Flicker: measure mean luminance per frame; Echo gave no gain.
- Grain: Add Grain at 0.6, mono, Screen, Viewing Mode Final Output (`VISINF Grain Implant-0021` =
  3).
- Planes for a camera push: cut them from the depth map by bands, the full frame as back plate. A
  push into an empty plate reveals nothing; rebuild hidden parts with a masked edit only when the
  move uncovers them (procedure 9).
- A supplied object seated in a plate: match the light first (plate prompted to the object's light,
  or the object relit to the plate's). Then real-world scale, the plate's shadow direction and a
  push sized by the gates (procedure 12).
- Element on black (realistic fire, smoke): pick the model by the look with `recommend`, prompt for
  a clean black, land it with the effects skill's `AEX.element.land`. Over a plate near white, a
  darker fill with the element as luminance matte instead of Screen (procedure 10).
- Model motion blur: `layer.motionBlur` throws under `ADBE Calder`; use CC Force Motion Blur on its
  precomp. GATE: the numbers in Quality gates pass, and the contact sheet shows no halo, hole, jump
  or garbled detail.

### 6. Review and hand off

Goal: one `ae.py sheet` per asset: the asset on black and on white, the loop seam, the extreme
parallax and depth frames. Score it with [references/critique.md](references/critique.md), then hand
the comp to the sibling that owns the next step. GATE: no reject item open. Reject a take with
broken anatomy, garbled text or the wrong subject, and regenerate it once.

## Numbers

| What                            | Value                                                   | Relative to                                  |
| ------------------------------- | ------------------------------------------------------- | -------------------------------------------- |
| Upscale trigger                 | layer Scale above 105 %                                 | footage pixels                               |
| Cutout body lift                | Levels alpha Input White 0.98                           | 8-bit alpha 252 to 253                       |
| Wrong alpha mode                | 7.6 levels mean, 64 max fringe error                    | straight PNG read as premultiplied           |
| Loop seam                       | 0.0044 RMSE vs 0.0057 normal step                       | 1080p plate, 24 fps                          |
| Crossfade loop overlap          | 6 frames                                                | 24 fps                                       |
| Depth Displacement, raw map     | split past 1 px from 2 px; doubling visible at 40 px    | 1920 px wide frame                           |
| Depth Displacement, blurred map | clean to 40 px, bend at 80 px                           | Box Blur 25, precomposed                     |
| Layer-split parallax            | 172 px front-to-back on a 300 px push plus 120 px truck | 50 mm, zoom 2666.7, 1920 px                  |
| Voice gain ceiling              | -1 dBTP minus measured true peak                        | per file                                     |
| Mix sum                         | +0.8 dB over the loudest stem peak                      | voice plus music                             |
| Voice and bed, rendered         | -15.0 and -28.8 LUFS from gains +3.5 and -14 dB         | mono voice reads 3 LU louder rendered stereo |
| Depth band                      | 2 % of gray (54 to 56 %) for a near-binary edge         | 8-bit depth map                              |
| Edit mask dilation              | 14 px past the plane's matte                            | 2048 px wide frame                           |
| Element black level             | YMIN 9 to 15, Input Black 0.03                          | H.264 tv range, 8-bit                        |

## Quality gates

- Measurable: `AEX.gen.upscaled(comp)` empty; fringe under 1 level against an exact composite; loop
  seam step at or under a normal frame step; zero near-black pixels from layer holes; true peak at
  or under -1 dBTP on the rendered mix; caption words match the voice at probe frames; every
  generated item has a comment. A seated object passes
  [scripts/seat_check.py](scripts/seat_check.py) (light, then `--contact` at 2 px or less on the
  first and last frame); a push grows the front plane at least 1.35 times with subject-to-back
  parallax of at least 5 % of the width.
- Visual: on the contact sheet, no light or dark edge on black and white, no doubled object at the
  depth extreme, no ghost at the loop seam, readable product and logo across frames, no wrong finger
  count, no garbled text.

## What stays hand-made

- Timing and easing: generated motion is evenly paced; retime, ease and hold keys by hand (Jake In
  Motion QLZNiwaKqWg 00:09:00; agent walkthrough 3AIZ4FT61aw 00:13:12).
- Typography: set titles, prices and legal lines as live text, never generated pixels (3AIZ4FT61aw
  00:12:39; Jake In Motion 00:03:29 keeps "do not generate any assets" for the design).
- The edit: shot order, length and cuts follow the locked audio (3AIZ4FT61aw 00:18:51).
- Final color: grade the composite as one, with Lumetri and scopes (Dan, Lines To Designs
  eMDDDdoUgT4 00:08:25).

## Common mistakes

| Mistake                                            | Symptom                                                            | Fix                                                                           |
| -------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| Cutout read as premultiplied                       | bright or dark rim                                                 | alpha straight; check on black and white                                      |
| Body alpha left at 253                             | background shows through by 2 levels                               | Levels on alpha, Input White 0.98 (skip when the body measures 255)           |
| Upscaled PNG used as is                            | white box or white halo                                            | put the 1x alpha back, Premultiplied with matte white                         |
| Layer split used raw                               | black holes, orange halos                                          | depth planes with clean plates (procedure 9), or the full frame as back plate |
| Clean plate taken whole from the edit model        | the scene shifts outside the mask, up to 67 levels                 | composite the original back outside the edit mask                             |
| Element on black screened as is                    | gray veil over the frame, up to 8 levels                           | Levels Input Black at the measured black, then Screen                         |
| Element in Screen over a plate near white          | it vanishes: +4.4 levels at luminance 237                          | darker fill, element as luminance matte, Normal                               |
| Loop includes the repeated last frame              | one-frame hold at the seam                                         | `loopLayer(c, item, s, true)`                                                 |
| Raw depth map on Displacement Map                  | doubled trees, torn edges                                          | precompose, Box Blur 25, stay under 40 px                                     |
| Detail-preserving Upscale counted as safe          | audit stays silent                                                 | judge sharpness on frames; the audit reads Scale only                         |
| GLB added to a Classic comp                        | modal dialog, or a crash with an environment light                 | set `ADBE Calder` before adding                                               |
| Voice raised by loudness alone                     | true peak over 0 dBFS                                              | cap gain by true peak; measure the mix                                        |
| Word timings trusted blindly                       | caption 7 frames early                                             | check sentence starts against silencedetect (measured up to 0.29 s early)     |
| Layer motion blur on a model in Advanced 3D        | "Motion blur is not supported by the current composition renderer" | CC Force Motion Blur on a precomp                                             |
| Studio-lit product still dropped on a sunset plate | pasted look, cool highlights on a warm scene                       | relight to the plate, then `seat_check.py`                                    |
| Add Grain left on Preview                          | grain in a box, outline drawn in the frame                         | Viewing Mode Final Output                                                     |

## Handoffs

- Receives: the brief, beats and audio lock from scenario-after-effects-motion-production; asset
  needs from any sibling.
- Delivers landed, tagged items to: scenario-after-effects-compositing (cutouts, plates, grain,
  color match, the light-match gate on a seated object), scenario-after-effects-3d (layer splits,
  depth maps, GLB, HDRI; it owns the camera rig and renderer),
  scenario-after-effects-character-rigging (character parts), scenario-after-effects-typography
  (word timings for captions), scenario-after-effects-color-delivery (final grade, loudness and
  delivery checks).

## Version notes

- Advanced 3D (`ADBE Calder`) and GLB import: 24.1. OBJ import and EXR environment lights: 24.2. FBX
  import and animated environment light sources: 25.2. Measured here on 27.0.
- `ADBE Pixel Motion Blur` and `ADBE Remove Grain` cannot be added by script on 27.0.

## References

- [references/procedures.md](references/procedures.md): the landing table, then the jobs that were
  run, with what to check in each result.
- [references/expert-notes.md](references/expert-notes.md): expert judgment by source, with
  timestamps.
- [references/critique.md](references/critique.md): the rubric for generated media in a comp.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for the same steps.
- [references/sources.md](references/sources.md): every source and what it is best for.
