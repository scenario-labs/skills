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
// ARGS: {comp, title (optional)} ; grade sits below the titles so brand colors stay ungraded
var c = AEK.core.comp(ARGS.comp), t = ARGS.title ? c.layer(ARGS.title) : null;
var g = AEK.build.adjustment(c, "GRADE_base");
AEK.build.effect(g, "ADBE Lumetri", {});
var fx = g.property("ADBE Effect Parade").property(1);
fx.property("ADBE Lumetri-0011").setValue(ARGS.exposure || 0);    // Basic Correction > Exposure
fx.property("ADBE Lumetri-0012").setValue(ARGS.contrast || 0);    // Contrast
fx.property("ADBE Lumetri-0016").setValue(ARGS.blacks || 0);      // Blacks
fx.property("ADBE Lumetri-0020").setValue(ARGS.saturation || 100); // Saturation
if (t) { g.moveAfter(t); }   // no title: the grade stays on top of the plate
var f = AEK.capture.frame(c, ARGS.t || 0, ARGS.out + "/grade_check.png");
var order = [], i; for (i = 1; i <= c.numLayers; i++) { order.push(c.layer(i).name); }
return { order: order, frame: f.path };
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

## 4b. Protected colors: measure, then hold them

Name the colors that must survive the grade (brand swatch, product color, skin) as hex values.
Capture frames with every grade layer off, then on, at the same times, and compare the same pixels:

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
python3 scripts/color_protect.py before_f00060.png after_f00060.png --color cream=#F1E9D8 --color coral=#E0452C --color ink=#1E2A3A
```

The mask is every BEFORE pixel within delta E 25 (CIE76, Lab D65) of the swatch: the plate's own
version of that color, which a render rarely holds exactly. Per color it prints delta E, hue shift
in a*b* degrees and chroma change. It passes at delta E 5 or less and 4 hue degrees or less (hue
skipped under chroma 10). A color with fewer than 200 pixels fails: widen `--radius` or add `--box`.
For a delivered file, decode both the source and the file with section 10 and compare those.

Measured on a warm filmic grade of a product shot (Temperature 22, Faded Film 28): cream delta E
6.25, hue -12.2 degrees, chroma +31 % (fail); coral 2.5 (pass). Lowering Faded Film to 10 and one
Change Color on the cream brought it to delta E 0.86, hue -2.0. The web file against the source
decode read cream 2.67, coral 2.57, all pass.

Change Color as a scripted secondary on an adjustment layer above the base grade (Lumetri's HSL
Secondary is GUI only):

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS.protect: [{name, color: [r, g, b, 1] sampled on the GRADED frame, hue, light, sat, tol, soft}]
var c = AEK.core.comp(ARGS.comp), sec = AEK.build.adjustment(c, "GRADE_protect"), i, P, fx;
// added on top, so it sits above GRADE_base; keep any grain layer above it
for (i = 1; i <= c.numLayers; i++) { if (c.layer(i).name === "FINISH_grain") { sec.moveAfter(c.layer(i)); break; } }
for (i = 0; i < ARGS.protect.length; i++) {
    P = ARGS.protect[i];
    fx = AEK.build.effect(sec, "ADBE Change Color", {}, "protect " + P.name);
    fx.property("ADBE Change Color-0002").setValue(P.hue);    // Hue Transform, degrees: + moves toward higher HLS hue
    fx.property("ADBE Change Color-0003").setValue(P.light);  // Lightness
    fx.property("ADBE Change Color-0004").setValue(P.sat);    // Saturation
    fx.property("ADBE Change Color-0005").setValue(P.color);  // Color To Change
    fx.property("ADBE Change Color-0006").setValue(P.tol);    // Matching Tolerance, 0 to 100
    fx.property("ADBE Change Color-0007").setValue(P.soft);   // Matching Softness
    fx.property("ADBE Change Color-0008").setValue(1);        // Match Colors: 1 Using RGB, 2 Hue, 3 Chroma
}
return { layer: sec.name };
```

Read the drift as numbers first: hue and saturation of the graded color against the ungraded one, in
HLS. Then set Hue Transform to the opposite of the hue drift and Saturation against the saturation
gain. Measured: a cream that drifted -7.7 HLS degrees and gained 29 % saturation took Hue +8,
Saturation -14, Lightness 3. Match Using RGB at Tolerance 6 and Softness 8 isolated the cream. Match
Using Hue or Chroma also caught the coral and the ink (coral delta E up to 22). Re-run
`color_protect.py` after every change: a dark navy can lose chroma (ink -54 % measured) and still
pass on delta E, so read the chroma column too.

## 5. Banding: measure, then dither

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// a dither layer on top: Noise with Clipping on (the default), then render one frame to an 8-bit file
var c = AEK.core.comp(ARGS.comp);
var d = AEK.build.adjustment(c, "FINISH_dither");
AEK.build.effect(d, "ADBE Noise", {});
d.property("ADBE Effect Parade").property(1).property("ADBE Noise-0001").setValue(ARGS.amount || 1.2);
d.property("ADBE Effect Parade").property(1).property("ADBE Noise-0003").setValue(1);   // 0 wraps highlights into cyan specks
var r = AEX.delivery.render(c, [{ template: "TIFF Sequence with Alpha", file: ARGS.out + "/band/band_[#####].tif" }], { start: ARGS.t || 0, duration: 1 / c.frameRate });
return r;
```

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
python3 scripts/band_check.py <out>/band/band_00000.tif 270
python3 scripts/band_check.py web_f00060.png 120 --max-run 16   # on the encoded web file, decoded per section 10
```

`--max-run 16` exits 1 when the median run is over 2 px or the widest run is over 16 px (one x264
macroblock). The encoder smooths grain in dark flats. Measured on a dark row: master widest run 6
px; web file at CRF 18 from it 16 px; web file from the After Effects H.264 template 32 px (fail). A
median alone passed all three. Gradient Ramp (`ADBE Ramp`) match names, dumped on 27.0: `-0001`
Start of Ramp (point), `-0002` Start Color, `-0003` End of Ramp, `-0004` End Color, `-0005` Ramp
Shape (1 linear, 2 radial), `-0006` Ramp Scatter, `-0007` Blend With Original.

Measured on a 0.02 to 0.10 ramp pushed +2 stops, 8-bit output: CPU 8 bpc 22 levels and 46 px bands;
16 bpc 83 levels, median run 2 px (the conversion to 8-bit output dithers); 16 bpc with Noise 1.2 %
median run 1 px. On the Metal GPU the 8 bpc render also gave 83 levels: do not take a clean GPU
preview at 8 bpc as proof. Noise Clipping (`ADBE Noise-0003`) defaults to 1. At 0, Noise 6 % over a
ramp from gray to white at 16 bpc wrapped 3,449 highlight pixels into cyan specks. At 1 there were
none, with the noise still present (channel spread up to 16 levels). Read banding on a full-size
frame: the same frame scaled to a quarter and saved as JPEG read a 16 px median run, against 1 px at
1:1 and on a quarter-size PNG. Add Grain is `VISINF Grain Implant`: Viewing Mode `-0021` defaults to
1 (Preview box); Intensity `-0008`, Size `-0007`, Monochromatic `-0005`, Blending Mode `-0014`,
Random Seed `-0013`.

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
read back. `High Quality with Alpha`: QuickTime ProRes 4444, RGB + Alpha, Millions of Colors+,
Premultiplied (Matted). `High Quality`: ProRes 422 standard, RGB (fourcc `apcn`, `yuv422p10le`,
about 139 Mbps at 1080p30), not 422 HQ; the opaque master. H.264: Main, yuv420p, AAC 48 kHz.
`TIFF Sequence with Alpha`: 8-bit RGBA premultiplied, numbered from `_00000`. Output Audio Auto
wrote the comp's audio into the ProRes files.

What `setSettings` can and cannot change (27.0): Format, Channels, Depth and Color (straight or
premultiplied) are read-only. Audio (Output Audio, rate, depth, channels), Crop, Resize, Include
Project Link, Include Source XMP Metadata, Output File Info and Post-Render Action are settable. A
`.png` file name on a QuickTime module is rewritten to `.mov`. A straight-alpha ProRes or a PNG
sequence template needs one GUI pass (gui-paths.md), then `saveAsTemplate`.

Export color: the Display Color Space (OCIO) and View > Use Display Color Management (Adobe) change
the viewer only; the export behaves as if the display transform were None (InLightVFX, x2sx-P5f-iM
05:23 to 06:12). The file's color comes from Output Module > Color > Output Color Space (OCIO) or
Output Profile (Adobe), set in the GUI.

Camera-log version for a colorist (pYzN_g-1N_w 09:32 to 10:37; InLightVFX, x2sx-P5f-iM 07:52 to
08:58): one more output module whose Output Color Space is the input transform used on the footage
(Show All), in ProRes 4444, EXR or DPX, without the look layers. It lets the colorist reuse the
grade of the other shots. The color space menus are GUI work; once set, save the module as a
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

Read the matrix tag of your own master first (`ffprobe -show_entries stream=color_space`). After
Effects 27.0 encodes the frame size, not the project, into the matrix: at 960x540 both ProRes and
H.264 came out BT.601-encoded and tagged smpte170m; at 1920x1080, 1080x1920 and 1080x1080 BT.709 and
tagged bt709. The SD tag is correct: re-tagging it to bt709 with `-c copy`, or relabeling with
`setparams`, makes every decoder read the pixels with the wrong matrix (measured on color patches:
39 levels off, pure red decoded with green 24). Convert the matrix instead:

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
sp=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_space -of csv=p=0 SPOT_PR4444_v001.mov)
conv=""; [ "$sp" = "smpte170m" ] && conv="scale=in_color_matrix=bt601:out_color_matrix=bt709:in_range=tv:out_range=tv:flags=accurate_rnd+full_chroma_int,"
ffmpeg -i SPOT_PR4444_v001.mov -map 0:v:0 -write_tmcd 0 -vf "${conv}setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le SPOT_PR4444_v001_709.mov
```

Measured: this block wrote ProRes 4444 (`yuva444p12le` read back) tagged bt709. The converted
960x540 file decoded as BT.709 within 1 level of the source colors, in H.264 and in ProRes 422;
`scale=out_color_matrix=bt709` with the input matrix left to auto-detection read 4 levels off.
Render at an HD frame size when the spec allows it, and the step goes away.

YouTube H.264 from the master, loudness in two passes (first pass prints the measurement):

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
ffmpeg -i SPOT_PR4444_v001.mov -af loudnorm=I=-23:TP=-1:LRA=7:print_format=json -f null -
ffmpeg -i SPOT_PR4444_v001.mov -map 0:v:0 -map 0:a:0 -write_tmcd 0 \
  -vf "${conv}setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -bf 2 -g 12 \
  -af "loudnorm=I=-23:TP=-1:LRA=7:measured_I=<I>:measured_TP=<TP>:measured_LRA=<LRA>:measured_thresh=<thr>:offset=<off>:linear=true,aresample=48000" \
  -c:a aac -b:a 384k -ar 48000 -movflags +faststart SPOT_16x9_YT_v001.mp4
```

`-g` is half the frame rate (closed GOP per the YouTube page); `-b:a 384k` is its stereo figure. Use
the loudness target of the brief: -23 LUFS is EBU R 128 broadcast; a streaming target comes from the
platform. Measured: -27.8 LUFS in, -23.0 out. `-color_primaries` as an output option alone left
smpte170m primaries inherited from the frames; `setparams` fixed it. Dropping the alpha of a
premultiplied master is already a composite over black: do not premultiply again. `${conv}` is the
matrix conversion above (empty for an HD master).

The "High Quality" and "High Quality with Alpha" templates write a QuickTime timecode track
(`tmcd`). ffmpeg rewrites it into the MP4 even with `-map 0:v:0`; `-write_tmcd 0` drops it
(measured: `-map 0:v:0` alone kept it, `-write_tmcd 0` alone removed it). `"no_data": true` in the
check catches it.

Broadcast-legal levels: tagging range tv does not legalize. Light type on a dark ground plus grain
overshoots 16 to 235 in the H.264, and x264 ringing on hard edges re-creates overshoots after any
clip. Put a soft knee after `format=yuv420p`, before the encoder, then measure the encoded file:

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
KNEE="lutyuv=y='clip(if(gt(val\,205)\,205+(val-205)*0.5\,if(lt(val\,32)\,32-(32-val)*0.5\,val))\,22\,220)':u='clip(val\,16\,240)':v='clip(val\,16\,240)'"
ffmpeg -i SPOT_16x9_PR422_v001.mov -map 0:v:0 -an -write_tmcd 0 \
  -vf "${conv}setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p,${KNEE}" \
  -c:v libx264 -preset slow -crf 18 -profile:v high -movflags +faststart SPOT_16x9_v001.mp4
```

Measured at CRF 18 (8-bit Y of the encoded file, every frame): no legalizer read 15 to 245. A hard
clip at 16 to 235 read 233 to 235 before x264 and 245 after. A knee from 215 clipped at 228 read 14
to 239 on pure white type. This knee (205 halved, clipped at 220; shadows below 32 halved, floor 22)
read 23 to 229 on three formats. The knee dims a 235 white to 220: use it only when the spec asks
for legal range, and say so in the report.

App Store app preview portrait size accepted for current Face ID iPhones: 886 x 1920 (Apple).
Vertical and square from a 16:9 master only for a quick look: the center crop lost both side patches
on the test frame. Deliver vertical and square from their own comps or a per-shot reframe.

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
ffmpeg -i SPOT_16x9_YT_v001.mp4 -map 0:v:0 -map '0:a?' -write_tmcd 0 -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:flags=lanczos,setsar=1,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
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
`min8` and `max8` change the limits in 8-bit units. Grain overshoots a knee on single pixels:
measured Y 11 to 237 on a kneed web file, from 15 pixels in 120 frames.
`"levels": {"every": 1, "max_out_pct": 0.01}` reports Y min and max for information and passes on
area instead: the worst frame's share of pixels outside the legal range (signalstats BRNG).
Measured: 0.00014 % on that file (pass), 1.75 % on a stretched copy (fail). Add `"no_data": true` to
fail a timecode or other data stream. Measured on 7 test deliverables: the check failed the 960x540
After Effects ProRes on its smpte170m tags (convert the matrix as in section 9, never re-tag). It
also failed the After Effects H.264 on loudness (-27.8 for a -23 target); every derived file passed.
After Effects H.264 already has the moov atom first. On three formats from one design (16:9, 9:16,
1:1, 90 frames each), the section 9 recipe passed every row; the old recipe failed Y levels (15
to 245) and the data stream (`tmcd`).

Decode frames for measurement with the file's matrix and range, never ffmpeg's default RGB
conversion:

```bash
# checked: live 27.0 (ffmpeg 8, macOS)
ffmpeg -i SPOT_16x9_v001.mp4 -vf "select=eq(n\,89),scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int,format=rgb24" -frames:v 1 f089.png
```

Measured on color patches: the default decode read mid gray 125.5 for 127.5 and white 253 for 255 in
H.264 and ProRes; this line read every patch within 1 level. If a frame comes from the default
decode, count clipped white at 252 and above, not 255. OpenCV ignores the tags: decode with ffmpeg
first.

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

## Version notes

- OCIO and ACES since 23.2; ACES 2.0 CG v4.0 and Studio v4.0 with OCIO 2.5.1 since 26.5. On 25.x and
  earlier use the ACES 1.3 or 1.2 config names.
- Native H.264 in the Render Queue since 23.0; H.264 in MOV since 24.2. Media Encoder is optional.
- PNG Compression control new in 27.0: no `getSettings` key, set it in the GUI.
- Unmult is a native effect (`ADBE Unmult`) since 26.0.
- Multi-Frame Rendering since 22.0: `app.setMultiFrameRenderingConfig(on, maxCpu)` for the next
  render, `aerender -mfr ON 50`.
