# Expert notes: color, finishing and delivery

Principles from the sources, grouped by expert, each with video id and timestamp. Lines marked
[added] are this skill's own additions, measured live on After Effects 27.0 unless said.

## Eran Stern (SternFX, FZ9yfCeZZMA): render settings and output modules

- Several output modules on one render item render the comp once and write every file: a ProRes
  master plus H.264 at 5 and 40 Mbps (00:10:28 to 00:12:05).
- Name outputs with the comp name and output module name tokens so each file says what it is
  (00:11:03, frame 00:11:44).
- Set the Frame Default render template to Best Settings: the stock Current Settings can export a
  single frame at reduced resolution (00:04:50, frame 00:03:44).
- Drop the Lossless output templates (Animation codec, 8 bpc, huge files); keep High Quality (ProRes
  422), High Quality with Alpha (ProRes 4444) and a PNG sequence for stills (00:07:29 to 00:09:13).
- A template that is still a default cannot be deleted: reassign the default first (00:08:05).
- Save All writes `.ars` and `.aom` files that move templates to another machine (00:05:25,
  00:09:47).
- Read the Render Queue summary lines as the pre-flight check: quality, resolution, proxy use, color
  depth, time span, format, channels, depth (frames 00:03:01, 00:03:44, 00:09:41).
- [added] On 27.0 `setSettings` refuses Format, Channels, Depth and Color ("read-only"): the
  template carries them. `saveAsTemplate` stores audio, crop, resize and naming changes, and
  `aerender -OMtemplate` sees the new name in the same session.
- [added] High Quality with Alpha writes ProRes 4444 `yuva444p12le`, premultiplied; High Quality
  writes ProRes 422 `yuv422p10le`; H.264 15 Mbps writes Main profile, `yuv420p`, BT.709 tags, moov
  atom first.

## ShiveringCactus (PS5nPDpVM0E): transparent export

- MP4 (H.264) carries no alpha: never export a green background to key later (00:00:30).
- ProRes 4444 with RGB + Alpha is the editing and streaming standard; ProRes 422 cannot hold alpha
  (00:01:38, 00:02:42).
- Straight or premultiplied both work if the receiving app interprets them correctly (00:03:22).
- Render the expensive effects once to ProRes, then make the other formats from that file
  (00:03:22).
- Separate RGB and alpha passes for an editor that cannot read ProRes, reassembled with a luminance
  track matte (00:04:20, 00:05:39).
- Image sequences (PNG, TIFF, Targa) with RGB + Alpha for 3D apps, engines and split renders
  (00:06:57).
- [added] A `.png` file name on a QuickTime output module is rewritten to `.mov`: the format comes
  only from the template.
- [added] The TIFF Sequence with Alpha template writes premultiplied 8-bit frames from `_00000`;
  ffmpeg `unpremultiply` makes straight PNG frames for engines.

## Jake Bartlett (Jake In Motion, y4fuhIPxmJg and FmSTOXu2V6I): Lumetri and grain

- Lumetri processes its sections top to bottom; a Look later in the stack can need Creative
  saturation rebalanced (y4fuhIPxmJg 00:10:24).
- Set the black point from the scope: lower Blacks until the darkest value touches 0 (y4fuhIPxmJg
  00:06:34).
- A hue-to-brightness curve (Lumetri Curves) on clipped highlights posterizes: fix exposure,
  highlights and whites first (y4fuhIPxmJg 00:16:20).
- HSL Secondary keys on H, S and L with softness; Refine > Blur softens the key edge (y4fuhIPxmJg
  00:20:58 to 00:24:46).
- CC Environment overwrites earlier effects, so Lumetri comes after it (y4fuhIPxmJg 00:01:48).
- Lumetri cost rises with sections in use: about 125 ms basic to 385 ms with HSL Secondary at 2K, 32
  bpc (frames 00:04:08 to 00:25:35).
- Add Grain previews a small box by default: switch Viewing Mode to Final Output before judging
  (FmSTOXu2V6I 00:00:41).
- Film blend mode puts grain in the shadows, Overlay in the midtones (FmSTOXu2V6I 00:04:27 to
  00:05:00).
- [added] Measured by script on 27.0: Blending Mode `VISINF Grain Implant-0014` reads 1 by default
  and that value puts grain mostly in the shadows; 3 spreads it evenly; 5 keeps it in the midtones.
  Confirm the label in Effect Controls.
- Match Grain (`VISINF Grain Duplication`) makes clean titles and vector graphics carry the plate's
  grain (FmSTOXu2V6I 00:10:21 to 00:13:55).
- Match Grain: pick the noise source layer, place samples on flat background, Compensate for
  Existing Noise 2 to 4 % (FmSTOXu2V6I 00:11:24 to 00:13:30).
- Grain masking layers ignore layer transforms: precompose first (FmSTOXu2V6I 00:08:47).
- [added] Script reaches only Lumetri's scalar sliders (Exposure `ADBE Lumetri-0011`, Saturation
  `-0020`); curves, wheels and the Look and LUT pickers are GUI.
- [added] Grade placement measured: an adjustment layer above the title turned the red title gray (0
  red pixels); below it, 4631 red pixels stayed.

## Cameron (Motion Science, M7Ml1KoO4jY): finishing touches

- Finishing comes last and stays subtle: Gaussian blur 1 to 3 px, glow well below the plugin
  default, grain 0.3 to 0.5.
- Put grain on its own adjustment layer because the preview misleads otherwise (00:03:34).

## InLightVFX (x2sx-P5f-iM) and ActionVFX (pYzN_g-1N_w): OCIO and ACES

- The display color space is preview only; export color comes from the output module's Output Color
  Space (x2sx-P5f-iM 00:05:57 to 00:06:12).
- A top adjustment layer with an OCIO transform plus a display transform double-converts: set
  Display to None and tick Preserve RGB in the output module (x2sx-P5f-iM 00:06:45).
- Display-referred stills and Rec.709 video enter ACES as an "Output - sRGB" or "ACES/Rec.709" input
  (x2sx-P5f-iM 00:02:26; pYzN_g-1N_w 00:07:57).
- The Interpret Footage default in an ACES project is ACES2065-1, wrong for almost every real clip
  (pYzN_g-1N_w frame 00:06:29).
- Remember and Apply Interpretation set a project-wide input standard (pYzN_g-1N_w 00:08:28).
- For a colorist, render back to the camera space in a lossless format: EXR, DPX or ProRes 4444
  (pYzN_g-1N_w 00:09:32; x2sx-P5f-iM 00:07:52).
- [added] OCIO mode refuses 16 bpc: `bitsPerChannel = 16` throws "Not supported for OCIO color
  managed mode". 8 and 32 are accepted, and switching the engine keeps the current depth: read it
  back and set 32 for ACES work.
- [added] Config names a script accepts: ACES 2.0 CG v4.0, ACES 2.0 Studio v4.0, ACES 1.3 CG v1.0,
  ACES 1.3 Studio v1.0, ACES 1.2, or an absolute `.ocio` path. The OCIO working space, display space
  and each footage media color space are not exposed to scripts.
- [added] A new project inherits the color engine, bit depth, linearize, linear blending and gamma
  from the project open before it; the OCIO config resets to ACES 1.2.

## Adobe Care (zqz7WGK2pCo): washed-out exports

- Washed-out export in an Adobe-managed project: working space Rec.709 Gamma 2.4 and display color
  management off before exporting (00:00:05 to 00:00:40).

## Adobe Video (G8BAjmaVaDg): render cost

- The Composition Profiler shows per-layer and per-effect time; purge the cache for honest numbers
  (00:00:21 to 00:02:07).
- Camera Lens Blur at radius 150 costs over 300 ms where Gaussian Blur costs 13 ms and gets most of
  the way there (00:02:39 to 00:03:11).

## Measured on 27.0 [added]

- An unknown working space name silently becomes "None", which turns color management off.
- The same 8 bpc gradient banded on the CPU renderer (22 levels, 46 px bands) and stayed smooth on
  the Metal GPU (83 levels); 16 bpc with noise gave a median flat run of 1 px.
- 50 % green over red reads 127 with gamma blending and 191 with Blend Colors Using 1.0 Gamma or
  Linearize Working Space.
- `saveFrameToPng` in a 32 bpc project writes value divided by 10 and keeps over-range values
  (2.0785 written as 0.2078); in a linearized project it writes linear values, so render queue
  frames are the ones to judge.
- After Effects passed the audio level through (-27.8 LUFS); two-pass ffmpeg `loudnorm` brought it
  to -23.0 LUFS.
- ProRes renders at 960x540 carried SD tags (smpte170m primaries and matrix); 540x960 carried
  BT.709. The tag follows the frame size: read your own file's tags, then re-tag a ProRes with
  `-c copy` or an encode with the `setparams` filter.
- signalstats reports Y in the file's bit depth: the legal range is 16 to 235 at 8 bits, 64 to 940
  at 10, 256 to 3760 at 12 (ProRes 4444). One comp's black read 14, 59 and 250 in its H.264, ProRes
  422 and ProRes 4444 renders.
- `AEX.delivery.render` refuses render settings that use proxies: Best Settings reads "Use No
  Proxies", Draft Settings "Current Settings".
- Adding Apply Color LUT (`ADBE Apply Color LUT2`) by script opens a file chooser that blocks the
  session.
