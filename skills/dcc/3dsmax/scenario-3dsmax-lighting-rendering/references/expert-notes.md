# Expert notes: lighting and rendering

Principles by source, with timestamps. Video timestamps are hh:mm:ss; "frame" means a value read
from the video image. Doc file names point to the official pages listed in [sources.md](sources.md).
[added] marks this skill's own inference.

## Shared principles (several experts agree)

- Lighting and materials make the image; render settings buy time and cleanliness (Aga, _biqhqTpW5c
  00:00:33; Educk, 3IZ44a70BPw 00:00:15; V-Ray 7 render settings doc names the image sampler and GI
  engine as the two biggest levers).
- Light without materials first, then add materials (hPZvijDCV-M 00:03:41; x8H1CNNFPgc 00:02:58;
  4MeUNMFxiPE 00:01:36). The archviz "general feeling pass" (gray base, HDRI, two helper disks,
  tone) does the same before any texture (64vzHYEWedI 00:15:01).
- Preview and final are different setups: interactive with a fast AI denoiser and reduced
  resolution, final with a measured stop criterion (4MeUNMFxiPE 00:02:09, 00:06:53; 3IZ44a70BPw
  00:08:21).
- Isolate a contribution instead of guessing: Arnold RenderView isolate on lights (ZUEnTb6QnD4
  00:06:07), V-Ray LightMix solo with Alt-click (4MeUNMFxiPE 00:06:07), AOVs for noise (Arnold docs,
  Removing Noise).
- Render separable lights and masks, finish in the frame buffer or compositor (x8H1CNNFPgc 00:09:41;
  Corona LightMix doc; eMkwX86vdPs 00:11:22).
- Save float linear EXR for post: 32-bit stays linear, 8-bit embeds gamma 2.2 (7Q3GqtJ56OQ 00:02:25;
  vray7-vfb-frame-buffer.md).

## Color management

- Autodesk (dlwDiLsPWgI): set color management before materials and lights, or every texture
  assignment has to be redone (00:04:08, 00:07:40). With OCIO use no exposure control and no
  tone-mapping imager (00:04:39). Normal vectors are not colors: EXR normal maps get auto-tagged
  scene-linear, set Raw (00:07:07). Keep files in rendering space for compositing; bake a view only
  for direct delivery (00:03:26). Log and Raw views are diagnostics (00:02:00).
- HM Studio (qt7FB4UU0qg): in 3ds Max 2026 OCIO with ACEScg is the default and textures convert
  automatically (00:01:40); the version deltas date the OCIO default for new scenes to 2025. V-Ray
  frame buffer display correction: OCIO, input ACEScg, sRGB display, ACES 1.0 SDR-video, Save in
  image on (00:02:12 to 00:02:46). The ACES view is already tone mapped; a second tone mapper
  crushes highlights and shadows; to use your own, set the view transform to un-tone-mapped first
  (00:07:35). In a Gamma workflow the filmic layer sits above exposure (00:08:41). ACES does not
  improve renders by itself; it makes light behave (00:08:41).
- Jonas Noell (QuJe2j7SHZ0, materials cluster): tag every bitmap's color space before switching to
  ACEScg; Auto guesses differ between sRGB and ACEScg (00:08:19). Disable VFB tone mapping and
  exposure layers before the OCIO switch, keep White Balance (00:10:06). 3ds Max OCIO also tone-maps
  the material editor; untick the automatic option under Advanced (00:14:10).
- VizAcademy UK trainer (hz07nIgm7EA, fundamentals cluster): for Corona or V-Ray archviz he switches
  the mode to Gamma Workflow, display gamma 2.2, and says nothing prompts you (00:28:56); OCIO
  matters for USD and cross-renderer exchange (00:34:06). Per-camera tone mapping override: interior
  about -1 EV, exterior about -3 EV in one scene (01:13:41).
- **Disagreement, deciding condition:** OCIO ACEScg (Autodesk, HM Studio, Noell) versus Gamma 2.2
  (VizAcademy UK). Keep the scene's mode; new projects follow the studio standard; a multi-renderer
  or USD pipeline favors OCIO. Never mix: a gamma-era VFB filmic layer on an ACES view is the double
  tone-mapping trap [added].

## Noise and sampling

- Arnold docs (Removing Noise): noise nearly always comes from insufficient sampling, but sampling
  the wrong rays raises time without removing noise. Camera (AA) is a multiplier; actual rays are
  the square of each setting; AA 4 gives 16 camera rays. DOF and motion blur noise show in the alpha
  channel and only AA fixes them. Zero-test: setting a type's samples to 0 removes that
  contribution; if the noise disappears, that type caused it. Light samples 3 to 4 suffice for most
  scenes. Starting AA 4 to 8. Fireflies: bright light on low-roughness glossy surfaces, or a light
  touching geometry: clamp (reduces dynamic range), light decay filter, or raise roughness. Noise
  can come from things behind the camera.
- Arnold docs (Sampling and Ray Depth): Global Light Sampling ignores per-light samples; Light
  Samples apply to primary rays; raise Indirect Light Samples when indirect AOVs are noisier than
  beauty, often faster than turning GLS off; GLS does not apply to environment, directional lights
  and volumes. Preview (AA) negative values subsample for fast feedback. Frame Time Limit stops a
  production render with a complete but noisier image; 0 means none; not applied in ActiveShade or
  RenderView.
- Eloi Andaluz (ZUEnTb6QnD4, MAXtoA 4.x): total rays per pixel in the UI is AA squared times sample
  squared per type (frame 00:18:02: 4 x 36 = 144 diffuse); ray depth 0 kills that type even with
  samples set; Arnold flags in Object Properties do nothing, use the Arnold Properties modifier
  (00:18:23); OptiX "apply on beauty" plus low samples for speed (00:18:01); Progressive and Preview
  off for sequences (00:11:04).
- Arvid Schneider (eMkwX86vdPs, Maya Arnold): Global Light Sampling helps above about 10 lights,
  about 2x at 100 and 3x at 1000 lights, needs adaptive sampling (00:12:17); volumes: keep ray depth
  low and get softness from scatter diffusion (00:09:23).
- Aga, Arch Viz Artist (_biqhqTpW5c, Corona 6): noise limit 3 percent finals, 2 for demanding
  (00:03:13); leave Performance values alone without a concrete problem (00:10:35, 00:14:07); UHD
  Cache for interiors, path tracing for exteriors (00:11:10); keep Lock sampling pattern on
  (00:12:11); untick Clear VFB between renders to resume (00:13:34); Reset settings also wipes the
  frame buffer (00:02:26); hidden lights need "Render hidden lights" (00:04:29); "Render only masks"
  saves a re-render for a forgotten mask (00:04:51).
- Corona docs (Performance tab): GI vs AA balance 2 to 64 (default 16); light samples multiplier
  2.0; Max Sample Intensity 20, 0 is unbiased and not production-ready; ray depth default advised;
  Conserve memory lowers peak up to 30 percent; displacement by screen size preferred; caustics need
  enabling and "Only in caustics element" keeps them out of the beauty.
- Educk (3IZ44a70BPw, V-Ray 7 in SketchUp, logic transfers): avoid quality High Plus (00:03:25);
  compare CPU, CUDA and RTX on your own scene (00:01:18); brute force over irradiance map,
  deprecated in V-Ray 7 (00:07:40).
- V-Ray 7 docs (image sampler): Bucket for finals and distributed rendering (less RAM, less lost on
  a failed node); Progressive for look-dev and time-boxed renders (most RAM). Right-click a spinner
  sets its minimum, Ctrl+right-click resets the default.

## Denoising and render big then downscale

- Chaos Corona (1bOmROFahXU, Corona 14 preview): 2x resolution, noise limit 20 to 30 percent (23 in
  frame), Intel CPU/GPU AI denoise amount 0.85 (default 0.65), image filter Tent because High
  Quality does not work with the AI denoiser, then Save 50%. 7 min against 41 min. Fine reflections
  on walls go first; about 15 percent noise limit brings them back. NVIDIA GPU AI is for fast
  previews.
- Chaos V-Ray (x8H1CNNFPgc): interactive denoisers are for look-dev, results can be inconsistent
  (00:04:05); delete the denoiser element when the final is clean (00:08:39); higher threshold plus
  denoiser is the speed trade, lower threshold without denoiser the quality trade (00:09:11).
- Chaos V-Ray (4MeUNMFxiPE): fast AI denoiser for IPR, default denoiser for the final as "more
  accurate" (00:06:53).
- **Disagreement, deciding condition:** denoise in the final or not depends on the deadline and the
  threshold: at 0.005 skip it; with a high threshold keep it (digest batch3). AI Enhancer size
  limits differ between Corona 13 (2048) and V-Ray 7 VFB doc (512 to 3840 upscaled to 4096):
  different product versions, unresolved.

## Light mix and light design

- V-Ray 7 VRayLightMix doc and Chaos blog: set lights white and bright before rendering; dim rather
  than brighten; 254 lights maximum, then Rest; "To Scene" only after the render stops; needs
  Consistent lighting elements; organize lights like circuit breakers; save recipes for reuse.
- Chaos V-Ray (4MeUNMFxiPE): brightness on the light's own settings because the mix multiplies and
  can artifact (00:05:16); a light enabled after the IPR started is missing from the mix (00:04:43);
  dome invisible with the HDRI in Environment as a separately balanced background (00:04:02); moon
  as V-Ray Sun 0.02 intensity, 8.0 size, blue (frame 00:05:00); Directional like barn doors on a
  plane fill (frame 00:07:00); save .vfbl presets (00:07:35).
- Chaos V-Ray (x8H1CNNFPgc): sun position does not matter, only its angle (00:01:54); override color
  mode for neutral sun, size multiplier for soft shadows (00:06:20); off-camera casters (00:06:59);
  several dome HDRIs in one render, picked in LightMix (00:15:39); rotate HDRI on Z only (00:13:53).
- Corona LightMix doc: one CShading_LightMix plus one CShading_LightSelect per group; Rest cannot be
  denoised or saved unless a LightSelect includes unassigned lights; denoising must be on for all
  LightSelects to denoise the mix; multiple suns and environments without re-render; compose with
  additive blending.
- Aga (hPZvijDCV-M): key at about 90 degrees between light, subject and camera (00:02:10); fill
  larger and weaker, never its own shadow (00:05:14); key warm, fill and rim cold, background fill
  neutral (00:05:34 to 00:07:43); rim invisible and excluding the backdrop (00:08:55); rim is a
  cheat justified by photographers' masks (00:09:17).
- Aga (JmmgSQp6FYI, Corona 13 exterior): camera 140 cm, 30 mm (00:00:11); lock the camera view
  before moving the sun, target at ground level (00:01:15); exposure and tone curve after foliage
  darkens the image, not light intensity (00:10:33); exclude scatter trees that cast too many
  shadows, hand-place hero trees (00:10:03); AI Enhancer for people (00:11:20).
- Arch Viz Artist exteriors (archviz digest, IuQ7QnwSwL0): HDRI for a specific sky, sun and sky for
  direction and caustics (00:02:19, 00:08:05); caustics fix with a sun limited to water (00:07:31).

## Animation

- Aga (7Q3GqtJ56OQ, V-Ray 6): moving objects need brute force with Bucket; camera-only can use
  irradiance map multiframe incremental plus light cache animation, pre-pass every 25th frame
  outside, 5th to 10th inside, then From file (00:00:39 to 00:06:48); higher light cache subdivs
  reduce flicker (00:01:55); Bucket values min 1, max 24, threshold 0.005, bucket 48, min shading
  rate 6 (frame 1:28).
- V-Ray 7 image sampler doc: Lock noise pattern on keeps the same pattern each frame; off lets noise
  change over time. Corona keeps it on (Performance tab doc). **Deciding condition:** on for Corona
  and any per-frame post denoise; off only when frames are averaged later [added].
- Archviz digest batch 4: Corona animation 15 min per frame at 3 percent, 22.5 h for 90 frames
  locally (ZHCVMQeWPEg 00:09:01); Vantage about 26.5 s per frame at Ultra, 727 frames in 5.3 h
  (gMUKCmaeQhc frame 00:08:59). Vantage export belongs to scenario-3dsmax-archviz.

## Masks

- Tom, Chaos Corona (Jlxe5d1_bFg): Cryptomatte color previews are not mattes; rename .cxr to .exr;
  export a Cryptomatte holding only post objects plus a name variant (00:01:26 to 00:03:24);
  Cryptomatte beats object ID only on blurred edges (00:12:28). Keep post renders linear with no
  auto tone mapping (00:01:42).
- MAXtoA 5.9 doc: Cryptomatte `object_split_instances` off by default: instances share one hash and
  the manifest is smaller.

## Camera

- Chaos V-Ray (dB4975f2yRc): exposure value or ISO, f-number and shutter on the camera; auto
  exposure and auto white balance as reading aids (00:03:04 to 00:04:56); set focus by right-click
  in the VFB (00:05:28).
- **Disagreement, deciding condition:** EV for quick look-dev versus physical ISO, f-stop and
  shutter when DOF, motion blur or photo matching matter (digest batch3).
- The x8H1CNNFPgc frames show EV about 10.5 next to ISO 100, f/8, 1/200 (reading approximate). These
  are not the same exposure: EV100 = log2(N^2 / t) gives about 13.6 for that triple [added
  arithmetic]. Quote one mode, never the pair as equivalent.
