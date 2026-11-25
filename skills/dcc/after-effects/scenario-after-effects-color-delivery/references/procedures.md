# Procedures: color and delivery

Every job is a function body for `ae.py run job.jsx --lib scripts/color_delivery.jsx`. Paths come
from `ARGS` and are absolute. In a person's session, take `AEK.session.state()` first and
`restore()` last (lead skill), and use `--undo`.

## 1. Read and set project color

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ae.py run job.jsx --lib color_delivery.jsx --undo "Agent: project color"
var before = AEX.delivery.state();
var names = app.project.listColorProfiles(), rec = [], i;
for (i = 0; i < names.length; i++) { if (/709|sRGB|ACES|P3|2020/.test(names[i])) { rec.push(names[i]); } }
var after = AEX.delivery.setColor({ engine: "adobe", bpc: 16, workingSpace: "Rec.709 Gamma 2.4", linearize: false, linearBlending: false });
return { before: before, after: after, candidates: rec };
```

Check: `after` equals the plan. `setColor` throws on an unknown name, because
`workingSpace = "<unknown>"` sets "None" with no error (measured: `"HDTV (Rec. 709)"` is not a 27.0
name). Valid SDR names seen: `Rec.709 Gamma 2.4`, `Rec. ITU-R BT.709-5`, `HDTV (Rec. 709) 16-235`,
`sRGB IEC61966-2.1`.

What a new project inherits from the project open before it (measured): bit depth, Linearize Working
Space, Blend Colors Using 1.0 Gamma, working gamma, Compensate for Scene-referred Profiles, the
color engine. The working space carries over in the Adobe engine; the OCIO config resets to
`ACES 1.2`. `AEK.core.fresh()` (test sessions) resets the engine to 0 first, then 8 bpc, working
space "None", linearize off, linear blending off, gamma 2.4. In a person's session nothing resets
it: set every field right after creating a project.

## 2. Switch to OCIO and pick a config

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ColorManagementSystem is undefined on 27.0: 0 = Adobe, 1 = OCIO
var s = AEX.delivery.setColor({ engine: "ocio", ocioConfig: ARGS.config || "ACES 2.0 CG v4.0", bpc: 32 });
return s;
```

Bit depth under OCIO (measured): setting the engine to 1 on an 8 bpc project raises no error and the
depth still reads 8. Under OCIO, `bitsPerChannel = 8` and `32` are accepted; `16` throws "Unable to
set bitsPerChannel. Value is 16. Not supported for OCIO color managed mode." and leaves the depth
unchanged. Set 32 for OCIO work and read it back; `setColor` refuses 16 under OCIO before After
Effects does. A new project made in the same session inherits the OCIO engine. Accepted config
names: `ACES 2.0 CG v4.0`, `ACES 2.0 Studio v4.0`, `ACES 1.3 CG v1.0`, `ACES 1.3 Studio v1.0`,
`ACES 1.2`, or an absolute path to a `.ocio` file. A wrong name throws "Invalid ocio configuration
used.". The working space, display space and footage media color spaces are not scriptable:
`workingSpace` keeps taking ICC names only (`ACEScg` read back "None"), and `FootageSource` has no
color field. Set those in the GUI (gui-paths.md) or start from a template project saved by a person.

## 3. Log intake without the GUI

Apply Color LUT (`ADBE Apply Color LUT2`) added by script opens a native "Choose LUT File..." panel.
Keys posted to the process do not close it; the session needed a restart. Convert before import
instead:

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
ffmpeg -i <in>/A001_log.mov -vf "lut3d=file=<luts>/camera_log_to_709.cube:interp=tetrahedral,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
  -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le <project>/footage/A001_709.mov
```

Measured on a synthetic log clip with its exact inverse LUT: PSNR against the source 15.7 dB before,
30.6 dB after. Keep the log original beside the converted file; the colorist hand-off uses the
original. In an OCIO project, an OCIO Color Space Transform effect
(`ADBE OCIO Color Space Transform`) can be added by script, but its Input and Output Color Space are
dropdowns whose entries come from the config: choose them in Effect Controls.

## 4. Grade stack with Lumetri on adjustment layers

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ARGS: {comp, title} ; grade sits below the titles so brand colors stay ungraded
var c = AEK.core.comp(ARGS.comp), t = c.layer(ARGS.title);
var g = AEK.build.adjustment(c, "GRADE_base");
AEK.build.effect(g, "ADBE Lumetri", {});
var fx = g.property("ADBE Effect Parade").property(1);
fx.property("ADBE Lumetri-0011").setValue(ARGS.exposure || 0);    // Basic Correction > Exposure
fx.property("ADBE Lumetri-0012").setValue(ARGS.contrast || 0);    // Contrast
fx.property("ADBE Lumetri-0016").setValue(ARGS.blacks || 0);      // Blacks
fx.property("ADBE Lumetri-0020").setValue(ARGS.saturation || 100); // Saturation
g.moveAfter(t);
var f = AEK.capture.frame(c, ARGS.t || 0, ARGS.out + "/grade_check.png");
return { order: [c.layer(1).name, c.layer(2).name, c.layer(3).name], frame: f.path };
```

Measured: Saturation 0 on an adjustment layer above a red title left 0 red title pixels; the same
layer below the title kept 4631. Scriptable Lumetri sliders (27.0): `-0007` Temperature, `-0008`
Tint, `-0011` Exposure, `-0012` Contrast, `-0013` Highlights, `-0014` Shadows, `-0015` Whites,
`-0016` Blacks, `-0020` Saturation, `-0026` Look Intensity, `-0028` Faded Film, `-0029` Sharpen,
`-0030` Vibrance, `-0051` Vignette Amount, `-0052` Midpoint, `-0053` Roundness, `-0054` Feather.
Curves, wheels, HSL Secondary and the Input LUT and Look pickers (`-0005`, `-0025`, dropdowns of the
installed lists) are GUI work.

Set the black point from the scope (Jake Bartlett, y4fuhIPxmJg 06:34): in the GUI, lower Blacks
until the darkest value touches the floor of the Lumetri Scopes waveform. Scripted, step Blacks
(`-0016`) and read the floor of a rendered frame with the check below. Fix Exposure, Highlights and
Whites before a hue-to-brightness curve, which posterizes clipped highlights (16:20).

Black floor and white ceiling of a rendered file, with the legal limits scaled to its bit depth:

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
f=<render>.mov
bits=$(ffprobe -v error -select_streams v:0 -show_entries stream=bits_per_raw_sample,pix_fmt -of default=nw=1:nk=1 "$f" | grep -Eo '^[0-9]+$|p[0-9]{2}(le|be)$' | grep -Eo '[0-9]+' | head -1)
bits=${bits:-8}; s=$(( 1 << (bits - 8) ))
echo "legal Y at ${bits}-bit: $((16 * s)) to $((235 * s))"
ffmpeg -hide_banner -i "$f" -vf "select=eq(n\,24),signalstats,metadata=print" -f null - 2>&1 | grep -E "signalstats\.(YMIN|YMAX)="
```

signalstats reports in the file's own bit depth: 0 to 255 at 8 bits (legal 16 to 235), 0 to 1023 at
10 bits (64 to 940), 0 to 4095 at 12 bits (256 to 3760, ProRes 4444 `yuva444p12le`). Measured on one
comp rendered three ways: lowest YMIN 250 in the 12-bit ProRes 4444, 59 in the 10-bit ProRes 422, 14
in the 8-bit H.264, the same black once scaled. `delivery_check.py` does this per file with its
`levels` key (section 10). `metadata=print` with two `key=` options prints only the last one.

## 5. Banding: measure, then dither

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// a dither layer on top: Noise without clipping, then render one frame to an 8-bit file
var c = AEK.core.comp(ARGS.comp);
var d = AEK.build.adjustment(c, "FINISH_dither");
AEK.build.effect(d, "ADBE Noise", {});
d.property("ADBE Effect Parade").property(1).property("ADBE Noise-0001").setValue(ARGS.amount || 1.2);
d.property("ADBE Effect Parade").property(1).property("ADBE Noise-0003").setValue(0);
var r = AEX.delivery.render(c, [{ template: "TIFF Sequence with Alpha", file: ARGS.out + "/band/band_[#####].tif" }], { start: ARGS.t || 0, duration: 1 / c.frameRate });
return r;
```

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
python3 scripts/band_check.py <out>/band/band_00000.tif 270
```

Measured on a 0.02 to 0.10 ramp pushed +2 stops, 8-bit output: CPU 8 bpc 22 levels and 46 px bands;
16 bpc 83 levels, median run 2 px (the conversion to 8-bit output dithers); 16 bpc with Noise 1.2 %
median run 1 px. On the Metal GPU the 8 bpc render also gave 83 levels: do not take a clean GPU
preview at 8 bpc as proof. Add Grain is `VISINF Grain Implant`: Viewing Mode `-0021` defaults to 1
(Preview box); Intensity `-0008`, Size `-0007`, Monochromatic `-0005`, Blending Mode `-0014`, Random
Seed `-0013`.

## 5b. Grain for finals: Add Grain and Match Grain

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// grain on the top adjustment layer, above the titles; Viewing Mode 1 (default) grains only a preview box
var c = AEK.core.comp(ARGS.comp);
var a = AEK.build.adjustment(c, "FINISH_grain");
AEK.build.effect(a, "VISINF Grain Implant", {});
var g = a.property("ADBE Effect Parade").property(1);
g.property("VISINF Grain Implant-0021").setValue(3);   // Final Output
g.property("VISINF Grain Implant-0014").setValue(ARGS.blend || 1);
return { viewingMode: g.property("VISINF Grain Implant-0021").value, blend: g.property("VISINF Grain Implant-0014").value };
```

Measured on a black-to-white ramp at 16 bpc (mean grain difference in the dark, mid and bright
thirds, 8-bit units): Viewing Mode 1 left both outer thirds untouched (grain only in the center
box); 3 grained the whole frame. Blending Mode `-0014` read 1 by default and gave 1.8 / 1.0 / 0.2
(heavier in the shadows); 2 gave 0.2 / 1.0 / 1.8 (highlights); 3 gave 2.0 / 2.0 / 2.0 (even); 4
matched 1; 5 gave 0.4 / 1.9 / 0.4 (midtones). Jake Bartlett picks Film for realistic grain, more in
the shadows and less in the highlights (FmSTOXu2V6I 04:03 to 05:00): confirm the menu label in
Effect Controls before a final.

Match Grain is `VISINF Grain Duplication` (Remove Grain `VISINF Grain Removal`). It puts the plate's
grain on clean graphics: apply it to the title or graphic, Viewing Mode Final Output, Noise Source
Layer = the plate, samples on flat background, Compensate for Existing Noise 2 to 4 % (FmSTOXu2V6I
10:21 to 13:30). Choosing the Noise Source Layer is a GUI step here (gui-paths.md). When titles sit
under the top grain layer they already carry grain (Motion Science, M7Ml1KoO4jY: finishing goes on
top of everything).

## 6. Safe areas and guides

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ARGS.platform: per-side insets from the platform's current published spec
var c = AEK.core.comp(ARGS.comp), times = [0, c.duration / 2, c.duration - 1 / c.frameRate];
var title = AEX.delivery.safeCheck(c, { all: 0.10 }, times);
var platform = ARGS.platform ? AEX.delivery.safeCheck(c, ARGS.platform, times) : [];
var g = AEX.delivery.guides(c, [{ name: "action 5%", margins: { all: 0.05 }, color: [0, 1, 0] },
    { name: "title 10%", margins: { all: 0.10 }, color: [1, 0, 0] }]);
return { title: title, platform: platform, guide: g.name };
```

Check: every row `ok`. `safeCheck` measures text layers (or layers chosen by a test function) with
`sourceRectAtTime`, scale, anchor and position; it ignores parents and rotation. Measured on
540x960: the 10 % box is [54, 96, 486, 864]; a CTA at y 864 to 906 failed. The guide layer is absent
from renders; switch `guideLayer` off for a review frame and back on.

## 7. One render, several files

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), o = ARGS.out + "/" + ARGS.name;
var r = AEX.delivery.render(c, [
    { template: "High Quality with Alpha", file: o + "_PR4444_v001.mov" },
    { template: "High Quality", file: o + "_PR422_v001.mov" },
    { template: "H.264 - Match Render Settings - 15 Mbps", file: o + "_H264_v001.mp4", audio: "On" },
    { template: "TIFF Sequence with Alpha", file: ARGS.out + "/tiff/" + ARGS.name + "_[#####].tif" }
], { rs: "Best Settings" });
return r;
```

`render` reads the item's render settings back (`quality`, `resolution`, `proxyUse`, `colorDepth`)
and throws before rendering when Proxy Use is not "Use No Proxies": Best Settings passes, Draft
Settings ("Current Settings") is refused unless `allowProxies: true` (measured). Eran Stern also
sets the Frame Default render template to Best Settings so a single exported frame renders at full
resolution (FZ9yfCeZZMA 00:04:50); that default is set in Edit > Templates > Render Settings
(gui-paths.md).

Measured (960x540, 24 fps, 48 frames, alpha and audio): 3.0 s for the four files. Template contents
read back: `High Quality with Alpha` QuickTime ProRes 4444, RGB + Alpha, Millions of Colors+,
Premultiplied (Matted); `High Quality` ProRes 422, RGB; H.264 Main yuv420p with AAC 48 kHz;
`TIFF Sequence with Alpha` 8-bit RGBA premultiplied, numbered from `_00000`. Output Audio Auto wrote
the comp's audio into the ProRes files.

What `setSettings` can and cannot change (27.0): Format, Channels, Depth and Color (straight or
premultiplied) are read-only. Audio (Output Audio, rate, depth, channels), Crop, Resize, Include
Project Link, Include Source XMP Metadata, Output File Info and Post-Render Action are settable. A
`.png` file name on a QuickTime module is rewritten to `.mov`. A straight-alpha ProRes or a PNG
sequence template needs one GUI pass (gui-paths.md), then `saveAsTemplate`.

Export color: the Display Color Space (OCIO) and View > Use Display Color Management (Adobe) change
the viewer only; the export behaves as if the display transform were None (InLightVFX, x2sx-P5f-iM
05:23 to 06:12). The file's color comes from Output Module > Color > Output Color Space (OCIO) or
Output Profile (Adobe), set in the GUI.

Camera-log version for a colorist (ActionVFX, pYzN_g-1N_w 09:32 to 10:37; InLightVFX, x2sx-P5f-iM
07:52 to 08:58): one more output module whose Output Color Space is the input transform used on the
footage (Show All), in ProRes 4444, EXR or DPX, without the look layers. It lets the colorist reuse
the grade of the other shots. The color space menus are GUI work; once set, save the module as a
template and reuse it with `render`.

## 8. Templates and aerender

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
// the template stays in the person's preferences: prefixed name, listed in the report
var t = AEX.delivery.saveTemplate(c, "H.264 - Match Render Settings - 15 Mbps", "Agent - H264 NoAudio", { "Output Audio": "Off" });
app.project.save(new File(ARGS.aep));   // aerender reads the saved file only
return t;
```

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
aerender -project <project>/spot_delivery.aep -comp SPOT_9x16 -RStemplate "Best Settings" -OMtemplate "Agent - H264 NoAudio" \
  -output <project>/renders/SPOT_9x16_H264_v001.mp4 -mfr ON 50
```

Measured: the template saved in the session was found by `aerender` at once; `-mfr ON 50` and
`-mfr OFF 100` both rendered. A saved template stays in the person's output module templates after
the job ends. Name it with a clear prefix (`Agent - `), list every template you created in the
report, and leave removal to the person (Edit > Templates > Output Module). `aerender` has no queue
status: read its log for "Finished composition", then check the file (a wrong `-comp` prints an
error and still exits 0). `.aom` template files load only through the GUI. Multi-Frame Rendering
from a job: `app.setMultiFrameRenderingConfig(true, 60)` applies to the next render only. Its
preferences are `["Concurrent Frame Rendering"]` `Enable Concurrent Frame Renders`,
`Number of Concurrent Frame Renders` (-1 = automatic), `Reserved CPU Power` (10).

## 9. Post steps with ffmpeg

PNG sequence with straight alpha for a game engine, from the TIFF sequence (premultiplied):

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
ffmpeg -start_number 0 -i <out>/tiff/SPOT_%05d.tif -vf "unpremultiply=inplace=1" -start_number 0 <out>/png/SPOT_%05d.png
```

Read the tags of your own file first
(`ffprobe -show_entries stream=color_primaries,color_transfer,color_space`): After Effects tagged a
960x540 ProRes smpte170m primaries and matrix, and a 540x960 ProRes bt709: the tag follows the frame
size. Re-tag without re-encoding when they are wrong:

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
ffmpeg -i SPOT_PR4444_v001.mov -c copy -color_primaries bt709 -color_trc bt709 -colorspace bt709 SPOT_PR4444_v001_tagged.mov
```

YouTube H.264 from the master, loudness in two passes (first pass prints the measurement):

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
ffmpeg -i SPOT_PR4444_v001.mov -af loudnorm=I=-23:TP=-1:LRA=7:print_format=json -f null -
ffmpeg -i SPOT_PR4444_v001.mov -map 0:v:0 -map 0:a:0 \
  -vf "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -bf 2 -g 12 \
  -af "loudnorm=I=-23:TP=-1:LRA=7:measured_I=<I>:measured_TP=<TP>:measured_LRA=<LRA>:measured_thresh=<thr>:offset=<off>:linear=true,aresample=48000" \
  -c:a aac -b:a 384k -ar 48000 -movflags +faststart SPOT_16x9_YT_v001.mp4
```

`-g` is half the frame rate (closed GOP per the YouTube page); `-b:a 384k` is its stereo figure. Use
the loudness target of the brief: -23 LUFS is EBU R 128 broadcast; a streaming target comes from the
platform. Measured: -27.8 LUFS in, -23.0 out. `-color_primaries` as an output option alone left
smpte170m primaries inherited from the frames; `setparams` fixed it. Dropping the alpha of a
premultiplied master is already a composite over black: do not premultiply again.

Vertical and square from a 16:9 master only for a quick look: the center crop lost both side patches
on the test frame. Deliver vertical and square from their own comps or a per-shot reframe.

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
ffmpeg -i SPOT_16x9_YT_v001.mp4 -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:flags=lanczos,setsar=1,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
  -c:v libx264 -crf 18 -profile:v high -c:a copy -movflags +faststart SPOT_9x16_quick.mp4
```

## 10. Check every file

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
python3 scripts/delivery_check.py deliveries.json --json report.json
```

```json
[
 {"file": "<out>/SPOT_PR4444_v001_tagged.mov", "codec": "prores", "profile": "4444", "width": 1920, "height": 1080, "fps": 25, "frames": 750,
  "pix_fmt": "yuva444p12le", "alpha": true, "color": {"primaries": "bt709", "trc": "bt709", "space": "bt709"}},
 {"file": "<out>/SPOT_16x9_YT_v001.mp4", "codec": "h264", "profile": "High", "fps": 25, "frames": 750, "pix_fmt": "yuv420p",
  "color": {"primaries": "bt709", "trc": "bt709", "space": "bt709", "range": "tv"}, "faststart": true,
  "audio": {"codec": "aac", "rate": 48000, "channels": 2, "lufs": -23, "lufs_tol": 0.5, "true_peak_max": -1.0}},
 {"file": "<out>/png/SPOT_%05d.png", "width": 1920, "height": 1080, "frames": 750, "pix_fmt": "rgba", "alpha": true, "sequence_start": 0}
]
```

Add `"levels": {"every": 6}` to a row to check the Y (luminance) floor and ceiling against the legal
range scaled to that file's bit depth (16 to 235 at 8 bits, 64 to 940 at 10, 256 to 3760 at 12);
`min8` and `max8` change the limits in 8-bit units. Measured on 7 test deliverables: the check
failed the 960x540 After Effects ProRes on its smpte170m tags and the After Effects H.264 on
loudness (-27.8 for a -23 target); every derived file passed. After Effects H.264 already has the
moov atom first.

## 11. Look at the files

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
magick <out>/png/SPOT_00024.png \( -size 1920x1080 pattern:checkerboard -colorspace sRGB \) -compose dst-over -composite PNG24:<out>/alpha_check.png
python3 ae.py sheet <out>/delivery_sheet.jpg <out>/alpha_check.png <out>/v916.png <out>/sq.png <out>/safe_review.png
```

Read the sheet: clean alpha edges over the checkerboard, subject and titles inside every format,
guides only on the review frame.

## Traps measured on 27.0

- `saveFrameToPng` in a linearized working space writes linear working values (a 50 % mix read 127;
  the render queue wrote 191). At 32 bpc it writes value / 10 and keeps over-range. Judge color from
  render queue output.
- Exposure (`ADBE Exposure2`) works in linear light unless `-0022` Bypass Linear Light Conversion
  is 1.
- Effects added one by one without trouble: Exposure2, Ramp, Noise, Broadcast Colors, Color Profile
  Converter (`ADBE ProfileToProfile`), Add Grain, Unmult, Lumetri, the OCIO Color Space, Display,
  Look and CDL Transforms. Apply Color LUT (`ADBE Apply Color LUT2`) opened a blocking file panel:
  never add it from a job. Treat OCIO File Transform (`ADBE OCIO FILE Transform`) like it and apply
  it in the GUI.
