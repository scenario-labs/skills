# Expert notes: generated media in an After Effects project

Principles and judgment by source, with timestamps. Generator names from the videos are replaced by
"a generative model". [added] marks what the live tests on 27.0 added.

## Agent walkthrough (3AIZ4FT61aw): an agent building motion graphics in After Effects

- Lock the audio first; the voiceover length sets the cut [00:18:51].
- The agent can check still frames; it does not feel ease or rhythm, so timing stays with a person
  [00:13:12, 00:18:51].
- Quote on-screen text exactly in the prompt; anything paraphrased comes back wrong [00:12:39].
- Ask for options when unsure (the top three music picks) [00:09:21].
- A reference image that was too large crashed After Effects during the session: resize references
  before import [00:10:31].

## Jonathan Lam (ZPajb_N6tBs): finishing a generated video in After Effects

- Generate plates with a slow camera move and empty graphic space for type [00:01:00].
- Generate several variations of the same scene with small changes in framing, spacing or movement,
  and run a Start Frame preview before the full clip: one frame is quicker to fix than a render
  [00:03:30].
- Enlarge with Detail-preserving Upscale and Fit to Comp, not by dragging Scale [00:12:10].
- Vignette: a black solid with an inverted, feathered mask at about 50 % opacity [00:16:49 to
  00:18:26].
- Grain: Add Grain on a black solid, Viewing Mode Final Output, blending mode Screen, Monochromatic
  [00:18:45 to 00:20:25]. Left on Preview, only a center square shows [00:19:21].
- [added] Match names: Detail-preserving Upscale is `ADBE Upscale`; Add Grain is
  `VISINF Grain Implant`. Measured: Laplacian variance 14.6 vs 5.3 for Scale 200 %; grain added 0.5
  levels of frame-to-frame change at intensity 0.6.

## Jake Bartlett, Jake In Motion (QLZNiwaKqWg): testing a generative motion-design tool

- Pixel-peep generated plates: compression artifacts and logo continuity break first [00:08:28].
- Keep the design under control: tell the tool "do not generate any assets" and supply your own
  [00:03:29].
- Generated timing comes as even, uneased motion; hold-key stacks and real easing are hand work
  [00:09:00].

## A video automation company's presenter (bEO3z86mtbI): an agent driving After Effects

- Back up the project before an agent edits it [00:02:03].
- Expect a linear first pass from the agent; refine motion afterwards [00:04:39].

## Tyler Stalman (4N_rE8N8O_M): generated transitions between real shots

- Grade the real footage first, then export the stills that seed the generation [00:01:30].
- Use generation only for the impossible bit of a shot [00:02:51].
- The prompt ends "keep the camera speed constant through the whole shot" so the editor's own speed
  ramp stays controllable; a prompt that lets the model slow down breaks the ramp [00:03:39 to
  00:04:27].
- Hide the seam with a color match, a speed ramp near 400 %, motion blur and a whoosh [00:06:06 to
  00:08:55].

## Yaroflasher (K67WetORDEo): image-to-video for motion design

- Upscale stills to 4K before image-to-video [00:04:20].
- Chain shots by feeding the last frame of one clip as the first frame of the next [00:05:25].
- Generated clips with simple actions run slow: time remap them faster in After Effects [00:04:20,
  00:09:42].
- Two prompts per shot: a detailed one for control, a short one for variety [00:08:11].
- [added] Measured: a 121-frame plate at 1.5x through Time Remap became 81 frames; add the new end
  key before removing the default one.
- [added] With the first and last frame anchored on the same still, frame 120 matched frame 0 at 41
  dB PSNR, and skipping it gave a seam step smaller than a normal step (0.0044 vs 0.0057 RMSE).

## Mickmumpitz (_n0ir5V5tX4): a generative VFX pipeline

- In an inpainting mask, white means "change this" [00:06:30].
- No camera move in the prompt; the camera is added in compositing [00:10:49].

## Dan, Lines To Designs (eMDDDdoUgT4): Roto Brush plus generated plates

- Generate on a static frame, then put motion back with a planar track [00:07:37, 00:09:30].
- Match with Lumetri and the scopes, not by eye alone [00:08:25].
- Pre-render the frozen roto before using it as a generation input [00:04:55].

## flomotion (JZGqZWDSVPg): generated elements composited on live footage

- Use the first and last frames of the live shot as generation anchors [00:01:35, 00:03:21].
- Generate at native size; aspect and color still needed manual fixes [00:03:54].

## Vlad Sateev (_k8rOBob6k8): the After Effects AI Assistant

- Restate durations in frames; the assistant flagged an fps mismatch [00:01:37].

## Tom Lulofs, TomsProject (XsbXd4pirnE): parallax from a generated image

- Two layers, a camera push, Z separation and rescale are enough; the separation need not be perfect
  [00:02:25].
- Expand the selection 1 px before the fill so no edge line survives [00:03:32].
- Generate at 16:9 at the source rather than cropping later.
- [added] A generated 4-layer split had binary alpha and holes; the back layer was black where the
  front layers sat. The full original frame as back plate removed every black pixel; faint ghost
  edges stayed.

## Matt Dombrowski (PfVBb4ZEhq8): depth map displacement on a still

- Near must be white in the depth map.
- Blur the depth map before displacing.
- Find the maximum displacement first, then animate back to 0; keep amounts small.
- [added] Generated depth arrived white = near. On a 1920 px frame: raw map doubled a tree at 40 px;
  a precomposed Box Blur 25 map stayed clean to 40 px and bent slightly at 80 px. Effects on the map
  layer only count when it is precomposed.

## Where experts disagree, and the deciding condition

- Generate at native size (flomotion 00:03:54) vs upscale before image-to-video (Yaroflasher
  00:04:20): upscale when the clip is reframed or delivered above the generator's output size;
  otherwise generate at the delivery size.
- Clean separation (Lulofs: need not be perfect) vs layer holes measured here: imperfect separation
  works while the reveal stays under the overlap; with a generated split, put the full frame behind.
