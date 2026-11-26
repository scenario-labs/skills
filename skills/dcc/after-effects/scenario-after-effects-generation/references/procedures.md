# Procedures: generated media into After Effects

Every job below ran on After Effects 27.0 (build 27.0x78) through the bridge, on files generated
with the Scenario MCP. Jobs are function bodies for
`ae.py run job.jsx --lib <skill>/scripts/gen.jsx --args '{...}'`. In a person's open project, add
`--undo "Agent: <what>"` so the job is one undo step. Paths come from `ARGS` and are absolute.

## Landing table

What each generated type needs on arrival, measured on 27.0 with files from the Scenario MCP.

| Asset                                     | Ask for                                                    | What arrives (measured)                                                         | Import and settings                                                               | Check                                            | Next                          |
| ----------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------ | ----------------------------- |
| Style frame, plate still                  | target aspect, 1.5 to 2x comp size, no text                | PNG 8-bit sRGB, no alpha                                                        | `land`, `place` fit cover                                                         | audit under 105 %                                | compositing                   |
| Cutout (character, prop)                  | transparent background, margin, full figure                | PNG straight alpha; body alpha 252 to 253, stray alpha 1 pixels                 | alpha straight; Levels on alpha, Input White 0.98; anchor from the alpha bbox     | fringe on black and white                        | character-rigging             |
| Upscaled still                            | 2x of the largest on-screen size                           | RGB, alpha dropped, flattened on white                                          | put the 1x alpha back; Premultiplied, matte white                                 | halo on black                                    | compositing                   |
| Layer split                               | front-to-back planes, max 3 to 4                           | canvas-aligned PNGs, front first; binary alpha; back layer black where occluded | Z depth with scale compensation; the full frame as back plate                     | holes at the extreme camera frame                | 3d                            |
| Depth planes (procedure 9)                | depth map plus one masked edit per plane                   | near-binary alpha from depth bands; clean plates that drift outside the mask    | the original composited back outside each edit mask                               | holes and ghosts at the end of the push          | 3d                            |
| Element on black (procedure 10)           | pure black, locked camera, nothing else in frame           | tv range or lifted black (p99 2 to 12 / 255), audio track                       | `AEX.element.land` (vfx); audio off; darker luminance-matted fill over near white | corner lift, foot point, visibility on the plate | vfx                           |
| Depth map                                 | from the approved frame; of a supplied still: procedure 11 | 8-bit gray, white = near, same size                                             | precompose plus Box Blur before Displacement Map                                  | tear at the max amount                           | 3d                            |
| Cutout of a supplied still (procedure 11) | a background-removal model, no prompt                      | RGBA PNG at the input size; body alpha 255, colors unchanged inside             | alpha straight; no Levels lift when the body reads 255                            | fringe on black and white                        | compositing                   |
| Object seated in a plate (procedure 12)   | plate and object under one light                           | relit view from an edit model, recut                                            | scale from a real size; shadow along the plate's lines                            | `seat_check.py`, push gates                      | compositing                   |
| Video plate                               | locked camera, first and last frame = style frame          | MOV HEVC 4:4:4 10-bit, 24/1, 121 frames, bt709                                  | conform to comp fps if needed; `loopLayer` skipping the repeated last frame       | seam step vs normal step                         | compositing, color-delivery   |
| GLB model                                 | named parts, no text, real size                            | GLB, named PBR materials, meters; footage 1920x1080 30 fps                      | `renderer = "ADBE Calder"` first; fit by `sourceRectAtTime`                       | model present after a warm-up frame              | 3d                            |
| HDRI / skybox                             | 2:1 equirectangular, light sources in frame                | EXR and HDR linear, peak 2.4; PNG skybox 8-bit                                  | layer source of an Environment light (Advanced 3D only)                           | reflections, no crash                            | 3d                            |
| Voiceover                                 | WAV 48 kHz, word timings on                                | mono 48 kHz, -21.6 LUFS, -4.7 dBTP, JSON timings                                | cue in frames, gain capped by true peak                                           | rendered mix true peak                           | typography, motion-production |
| Music                                     | length = cut, BPM, no vocals                               | stereo 44.1 kHz, -14.1 LUFS                                                     | set the gain, then read voice and bed from solo renders                           | each stem and the mix, rendered                  | motion-production             |
| Sound effects                             | one event per file                                         | mono 48 kHz, peak -1.0 dBFS, 15 LU loudness spread                              | turn loud ones down, never quiet ones up past 0 dB                                | events count, mix peak                           | motion-production             |

## 0. Generate, download, keep provenance (Scenario MCP)

1. `recommend` with the need in plain words and `priority: "quality"`. Read `next_step`: on
   `proceed`, take the specialty or the top entry; on `ask_user`, present the options. For 3D,
   prefer the newest first-party model in the list. For a chain (style frame, then video, then
   voice), run `plan_generation` first; it is a catalog tool, called through
   `scenario_tool_execute_read`.
2. `model_schema_get`, then `model_run` with schema field names; `jobs_wait` on the returned
   `job_id`. For video:
   - Preview the start frame before the full render, and generate several small variations of the
     same shot (framing, spacing, movement), not new ideas (Jonathan Lam (Tuts+) ZPajb_N6tBs
     00:03:30).
   - Write two prompts per shot: a detailed one for control, a short one for variety (Yaroflasher
     K67WetORDEo 00:08:11).
   - Ask for a constant camera speed ("keep the camera speed constant through the whole shot") when
     you will ramp the speed yourself (Stalman 4N_rE8N8O_M 00:03:39 to 00:04:27).
   - Upscale the still before image-to-video when the clip is reframed or delivered above the
     generator's output size (K67WetORDEo 00:04:20 recommends 4K stills).
3. `asset_download` per asset. Measured: for a 3D asset the URL served the original source file, a
   zstd-compressed .blend; the GLB was the asset `url` from `asset_get` (mimeType
   `model/gltf-binary`). A speech model with subtitles on returned a second asset: the word timings
   as JSON.
4. Write a sidecar next to each file.

```bash
# sidecar: one per downloaded file; the same text goes into item.comment by AEX.gen.land
cat > "<project>/footage/generated/plate.mov.json" <<'EOF'
{"job": "<job id>", "asset": "<asset id>", "model": "<model id from recommend>", "seed": "<seed or none>",
 "prompt": "<full prompt>", "recommend": "<capability and rank that chose the model>", "date": "<yyyy-mm-dd>"}
EOF
head -c 4 "<project>/footage/generated/model.glb"   # must print glTF
```

## 1. Probe before import

```bash
ffprobe -v error -show_entries stream=codec_name,profile,pix_fmt,width,height,r_frame_rate,nb_frames,color_range,color_transfer,color_primaries -of compact plate.mov
magick identify -format "%wx%h %[channels] opaque=%[opaque]\n" cutout.png
magick cutout.png -alpha extract -define histogram:unique-colors=true -format %c histogram:info:- | sort -nr | head -4
ffmpeg -nostats -i vo.wav -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -A12 Summary
ffmpeg -nostats -i vo.wav -af silencedetect=n=-45dB:d=0.15 -f null - 2>&1 | grep -o "silence_\(start\|end\): [0-9.]*"
```

Check: alpha type and the top alpha value (a body at 252 to 253 needs a lift), fps as a ratio, frame
count, color tags, sample rate, channels, integrated loudness, true peak, where speech starts.

A still cut from a clip with ffmpeg carries gAMA and cHRM chunks (measured: a frame of a bt709
H.264). After Effects applies gAMA and renders it darker than its pixels (a border of 6,10,18
rendered 0,1,4), so a feathered still shows its rectangle on a comp of the same color. Strip the
chunks before import: `magick in.png -define png:exclude-chunks=gAMA,cHRM,sRGB,iCCP out.png`. PNGs
downloaded from the Scenario MCP (a plate, two cutouts, two depth maps) carried none of these
chunks.

## 2. Land a transparent cutout (alpha, fringe, body, provenance, size, anchor)

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {cut, bbox:[left, top, width, height] of the alpha, measured outside, prov:{job, asset, model, seed, prompt}}
var A = ARGS, c = AEK.build.comp("place", { width: 1920, height: 1080, fps: 24, duration: 5 }), b = A.bbox;
var it = AEX.gen.land(A.cut, { name: "character", alpha: "straight", prov: A.prov });
// a generated cutout stops at alpha 252-253: lift the body to fully opaque
var s = 1080 * 0.8 / b[3] * 100;
// sourceRectAtTime on a footage layer returns the whole canvas: the feet anchor comes from the alpha bbox
var l = AEX.gen.place(c, it, { anchorPx: [b[0] + b[2] / 2, b[1] + b[3]], scale: s, at: [960, 1020] });
AEK.build.effect(l, "ADBE Easy Levels2", { "ADBE Easy Levels2-0001": 5, "ADBE Easy Levels2-0004": 0.98 }, "alpha lift");
return { scale: s, upscaled: AEX.gen.upscaled(c), itemComment: it.comment, layerComment: l.comment };
```

Check: `upscaled` empty (the audit flags Scale above 105 %). Measured: a close-up with the body at
twice the comp height put the 1024 px file at 144.8 %, flagged; the 2x file at 72.4 %, clean. Over
white and over black the body differs by 2.15 levels before the lift and 0.00 after. Read as
Premultiplied by mistake, the fringe is 7.6 levels off on average and up to 64.

### The upscaled file lost its alpha

Measured: the upscaler returned RGB flattened on white. Put the original alpha back, then read the
edges as premultiplied with white.

```bash
magick cutout_x2.png \( cutout.png -alpha extract -filter Lanczos -resize 2048x3072! \) -alpha off -compose CopyOpacity -composite cutout_x2_alpha.png
```

```javascript
// channel: bridge
// checked: live 27.0
var it2 = AEX.gen.land(ARGS.cutX2, { name: "character_x2", alpha: "premultiplied", matte: [1, 1, 1], prov: ARGS.prov });
return { premulColor: it2.mainSource.premulColor, hasAlpha: it2.mainSource.hasAlpha };
```

Check: fringe on black. Measured: 7.45 levels light halo as Straight, 5.27 as Premultiplied with
matte white. Add `ADBE Simple Choker` (`-0002` Choke Matte 1) if a rim remains.

## 3. Layer split into 2.5D parallax

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {layers:[front..back], plate: the full frame, z:[0, 600, 1500, 3000], push, truck, seconds, out}
var A = ARGS, W = 1920, H = 1080, zoom = W * 50 / 36, c = AEK.build.comp("parallax", { width: W, height: H, fps: 24, duration: A.seconds });
var list = A.layers.slice(0), i, it, l, s, tg, cam;
// the back layer of a split is black where the front layers sat: the full frame replaces it
list[list.length - 1] = A.plate;
for (i = list.length - 1; i >= 0; i--) {
    it = AEX.gen.land(list[i], { name: "L" + i });
    l = c.layers.add(it); l.threeDLayer = true; l.name = "L" + i;
    s = W / it.width * 100 * (zoom + A.z[i]) / zoom * 1.04;
    tg = l.property("ADBE Transform Group");
    tg.property("ADBE Position").setValue([W / 2, H / 2, A.z[i]]);
    tg.property("ADBE Scale").setValue([s, s, 100]);
}
cam = c.layers.addCamera("cam", [W / 2, H / 2]); cam.autoOrient = AutoOrientType.NO_AUTO_ORIENT;
cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(zoom);
tg = cam.property("ADBE Transform Group");
AEK.motion.key(tg.property("ADBE Position"), 0, [W / 2, H / 2, -zoom]);
AEK.motion.key(tg.property("ADBE Position"), A.seconds - 1 / 24, [W / 2 + A.truck, H / 2, -zoom + A.push]);
return { zoom: zoom, last: AEK.capture.frame(c, A.seconds - 1 / 24, A.out + "/parallax_last.png").path };
```

Check the last frame on a contact sheet and count near-black pixels. Measured with a 300 px push and
a 120 px truck: front edge moved 256.9 px, back 84.9 px. With the split's own back layer, 1.5 % of
frame 0 was black holes; with the full frame as back plate, 0 %. Faint ghost edges remain where the
split was loose: keep moves small, or paint the reveal (scenario-after-effects-compositing). The
camera rig belongs to scenario-after-effects-3d.

## 4. Depth map into Displacement Map

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {frame, depth, amount}
var c = AEK.build.comp("depth push", { width: 1920, height: 1080, fps: 24, duration: 5 });
var p = AEX.gen.place(c, AEX.gen.land(ARGS.frame, { name: "frame" }), { fit: "cover", name: "photo" });
var d = AEX.gen.place(c, AEX.gen.land(ARGS.depth, { name: "depth" }), { fit: "cover", name: "depth" });
AEK.build.effect(d, "ADBE Box Blur2", { "ADBE Box Blur2-0001": 25 });
// effects on a displacement map layer are ignored unless that layer is precomposed
AEK.build.precompose(c, [d.index], "depth_map", true);
c.layer("depth_map").enabled = false;
p = c.layer("photo");
var fx = AEK.build.effect(p, "ADBE Displacement Map", { "ADBE Displacement Map-0005": 0, "ADBE Displacement Map-0007": 1 });
fx.property("ADBE Displacement Map-0001").setValue(c.layer("depth_map").index);
AEK.motion.key(fx.property("ADBE Displacement Map-0003"), 0, ARGS.amount);
AEK.motion.key(fx.property("ADBE Displacement Map-0003"), 5 - 1 / 24, 0);
return { mapIndex: c.layer("depth_map").index };
```

Check the frame at the maximum amount around the sharpest depth edge. Measured on a 1920 px frame:
the raw map splits neighbor pixels past 1 px from 2 px of displacement, doubles a tree at 40 px and
cuts a roof at 80 px; the blurred map stays clean to 40 px and bends slightly at 80 px. Find the
maximum, then key down to 0 (PfVBb4ZEhq8).

## 5. Video plate: conform, loop, flicker, size, grain

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {plate, fps, prov}
var A = ARGS, it = AEX.gen.land(A.plate, { name: "plate", fps: A.fps, prov: A.prov });
var c = AEK.build.comp("loops", { width: 1920, height: 1080, fps: A.fps, duration: 15 });
// first and last frame were anchored on the same image: skip the repeated last frame
var a = AEX.gen.loopLayer(c, it, 15, true);
// any other clip: a crossfade precomp, 6 frames of overlap, then the same loop
var xf = AEX.gen.loopCrossfade(it, 6, "plate xfade");
var b = AEX.gen.loopLayer(c, xf, 15, true); b.enabled = false;
return { fps: it.frameRate, frames: Math.round(it.duration * it.frameRate), exprA: a.property("ADBE Time Remapping").expressionError };
```

Check: capture the two frames on each side of the seam and two mid frames, and compare RMSE.
Measured: seam 0.0044 skipping the last frame, 0.0062 with the crossfade, 0.0057 for a normal step.
The plate imported at exactly 24 fps; still compare `it.frameRate` with `asset_get`
properties.frameRate and conform when they differ.

Flicker: measure mean luminance per frame first
(`ffmpeg -i plate.mov -vf signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=- -f null -`).
The measured plate varied 0.14 %: no flicker. Echo (`ADBE Echo`, -1 frame, operator 7) is not a
flicker fix here: it raised the frame step from 0.0057 to 0.0066 and gave no gain. On a plate that
does pump, regenerate it, or find the fix by test and keep it only if the YAVG step drops.

Speed up a slow generated clip (generated clips with simple actions run slow; Yaroflasher
K67WetORDEo 00:04:20, 00:09:42):

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {plate, k: speed factor, e.g. 1.5}
var it = AEX.gen.land(ARGS.plate, { name: "plate", fps: 24 }), k = ARGS.k, f = 1 / 24;
var c = AEK.build.comp("retime", { width: 1920, height: 1080, fps: 24, duration: it.duration });
var l = c.layers.add(it), n = Math.round(it.duration * 24), T = Math.round((n - 1) / k) * f, tr;
l.timeRemapEnabled = true; tr = l.property("ADBE Time Remapping");
// add the new end key before removing the default one: removing every key hides the property
tr.setValueAtTime(T, (n - 1) * f);
if (Math.abs(tr.keyTime(tr.numKeys) - T) > f / 10) { tr.removeKey(tr.numKeys); }
l.outPoint = T + f;
return { keys: tr.numKeys, frames: Math.round((l.outPoint - l.inPoint) * 24), srcAt2s: tr.valueAtTime(2, false) };
```

Check: measured on the 121-frame plate at 1.5x, 2 keys, 81 frames, source time 3.0 s at comp time
2.0 s. For a ramp, add keys between and ease them by hand (scenario-after-effects-animation).

```javascript
// channel: bridge
// checked: live 27.0
// 4K delivery from a 1080p plate: Detail-preserving Upscale instead of Scale 200 %
// ARGS: {plate}
var c = AEK.build.comp("uhd", { width: 3840, height: 2160, fps: 24, duration: 5 }), it = AEX.gen.land(ARGS.plate, { name: "plate", fps: 24 });
var l = AEX.gen.place(c, it, { scale: 100 });
AEK.build.effect(l, "ADBE Upscale", { "ADBE Upscale-0001": 200, "ADBE Upscale-0007": 50 });
// grain over the composite: Add Grain on a black solid in Screen, monochrome
// Viewing Mode (-0021) defaults to 1 Preview, which renders grain only inside a box and draws its outline: 3 is Final Output
var g = AEK.build.solid(c, "grain", [0, 0, 0], {});
AEK.build.effect(g, "VISINF Grain Implant", { "VISINF Grain Implant-0021": 3, "VISINF Grain Implant-0005": 1, "VISINF Grain Implant-0008": 0.6 });
g.blendingMode = BlendingMode.SCREEN;
return { upscaled: AEX.gen.upscaled(c) };
```

Check: edge detail on frames. Measured: Laplacian variance 14.6 with Detail-preserving Upscale vs
5.3 at Scale 200 %. The audit reads Scale only, so it stays silent on the effect. Grain raised the
frame-to-frame change from 0.45 to 0.95 levels.

## 6. GLB product model with a generated environment

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {glb, hdr, prov, out}
var A = ARGS, c = AEK.build.comp("product", { width: 1280, height: 720, fps: 24, duration: 4 });
// set Advanced 3D before the model or the light: a Classic comp raises a dialog and crashed with an environment light
c.renderer = "ADBE Calder";
var it = AEX.gen.land(A.glb, { name: "speaker", prov: A.prov }), m = c.layers.add(it);
m.comment = it.comment;
var r = m.sourceRectAtTime(0, false), tg = m.property("ADBE Transform Group"), s = 720 * 0.45 / r.height * 100;
tg.property("ADBE Anchor Point").setValue([r.left + r.width / 2, r.top + r.height / 2, 0]);
tg.property("ADBE Scale").setValue([s, s, s]);
tg.property("ADBE Position").setValue([640, 360, 0]);
var ry = tg.property("ADBE Rotate Y");
ry.setValueAtTime(0, 0); ry.setValueAtTime(4, 360);
ry.setInterpolationTypeAtKey(1, KeyframeInterpolationType.LINEAR); ry.setInterpolationTypeAtKey(2, KeyframeInterpolationType.LINEAR);
var env = c.layers.add(AEX.gen.land(A.hdr, { name: "env hdr" })); env.enabled = false;
var L = c.layers.addLight("env", [640, 360]); L.lightType = LightType.ENVIRONMENT; L.lightSource = env;
var mats = [], mp = m.property("ADBE3D Material Parade"), i;
for (i = 1; i <= mp.numProperties; i++) { mats.push(mp.property(i).name); }
AEK.capture.frame(c, 0, ARGS.out + "/warmup.png");
return { rect: [r.width, r.height], scale: s, materials: mats };
```

Check: four turntable frames on a sheet; the material names match the GLB. Measured: a 0.121 m model
gave a 117 x 37.5 footprint at scale 100 (origin at its base), fitted at 863 %. HDR and EXR rendered
identical frames; the 8-bit PNG skybox rendered 10 % brighter. Frames took 0.26 to 0.46 s, the first
1.28 s. Camera, shadows and depth of field go to scenario-after-effects-3d.

Motion blur on the model: `layer.motionBlur = true` throws "Motion blur is not supported by the
current composition renderer" in an `ADBE Calder` comp. Precompose the model comp and blur the
precomp layer:

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {model: name of the Advanced 3D comp holding the animated model, out}
var m3 = AEK.core.comp(ARGS.model), o = AEK.build.comp("product blur", { width: m3.width, height: m3.height, fps: m3.frameRate, duration: m3.duration });
var p = o.layers.add(m3);
AEK.build.effect(p, "CC Force Motion Blur", { "CC Force Motion Blur-0001": 16 });
return { frame: AEK.capture.frame(o, 0.5, ARGS.out + "/blurred.png").path };
```

Check: a frame mid-turn against the same frame without the effect. Measured with a 360
degrees-per-second turn: visible smear along the turn, edge detail (Laplacian variance) halved. CC
Force Motion Blur also takes Shutter Angle (`-0003`) and Override Shutter (`-0002`).

## 7. Audio from a cue list, word markers, captions

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {cues:[{path, at (frames at 24 fps), gainDb, name, prov}], words:[sentences from the speech model], vo:"vo", seconds, out}
var A = ARGS, c = AEK.build.comp("mix", { width: 1920, height: 1080, fps: 24, duration: A.seconds });
var placed = AEX.gen.cues(c, A.cues);
var vo = AEK.core.layer(c, A.vo), n = AEX.gen.wordMarkers(vo, A.words, {});
var cap = c.layers.addText("x"); cap.name = "caption";
AEK.expr.set(cap.property("ADBE Text Properties").property("ADBE Text Document"),
    "var m = thisComp.layer(\"" + A.vo + "\").marker, s = \"\";\nfor (var i = 1; i <= m.numKeys; i++) { if (m.key(i).time <= time) { s = m.key(i).comment; } }\ns;");
cap.enabled = false;
var mix = AEK.capture.queue(c, A.out + "/mix.aif", { template: "AIFF 48kHz" });
return { placed: placed, markers: n, mix: mix.path };
```

```bash
ffmpeg -nostats -i mix.aif -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -A20 Summary | grep -E "I:|Peak:"
```

Check: renders, never the gain values. Measured: voice +5 dB over a -4.7 dBTP file clipped the mix
at +0.1 dBTP. With the layer gains set to voice +3.5 dB and music -14 dB, the voice rendered alone
read -15.0 LUFS, the music alone -28.8 LUFS, and the two together -14.9 LUFS at -1.3 dBTP; with the
sound effects added, -15.0 LUFS at -0.4 dBTP. The mono voice reads 3 LU louder once rendered to
stereo than its file does. Cap each gain at -1 dBTP minus the file's true peak, then limit or lower
the bed. No source gives a voice-to-bed target: render the voice alone and the bed alone (switch the
other layer's `audioEnabled` off), read both with ebur128, record the two numbers, and judge the
balance by listening. The sound effects arrived peak-normalized to -1 dBFS with a 15 LU loudness
spread: turn the loud ones down. Loudness targets per platform:
scenario-after-effects-color-delivery.

The timings JSON also imports as footage and drives text directly:

```javascript
// expression (JavaScript engine): Text layer > Source Text
// checked: live 27.0
const data = footage("vo_words.json").sourceData;
let s = "";
for (const sentence of data) { for (const w of sentence.words) { if (/[A-Za-z0-9]/.test(w.word) && w.startTime <= time) { s = w.word; } } }
s;
```

Check: words at probe frames. Measured at 0.1, 0.5, 1.8, 3.5, 8.5 s: Meet, Orbi, speaker, It, on.
Sentence starts in the JSON were up to 0.29 s early against `silencedetect`: shift those words to
the audio. Without timings from the generator, run whisper with word timestamps or use silence
boundaries. Caption design: scenario-after-effects-typography.

## 8. Land a whole delivery at once

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {files:[{path, name, alpha, matte, fps, prov}]}
var A = ARGS, out = { landed: [], failed: [] }, i;
for (i = 0; i < A.files.length; i++) {
    try { out.landed.push(AEK.xio.describe(AEX.gen.land(A.files[i].path, A.files[i]))); }
    catch (e) { out.failed.push({ path: A.files[i].path, error: e.toString() }); }
}
out.audit = AEK.audit.footage();
return out;
```

Check: `failed` empty and each row's size, fps and alpha against the probe. Measured: 16 files
landed. A GLB reads as 1920x1080, 30 s, 30 fps footage; EXR and HDR as 2048x1024 stills; the timing
JSON as a 0x0 still.

## 9. Depth planes with clean plates behind them

A model layer split arrived with binary edges and holes (procedure 3). Planes cut from the depth map
by bands, with the area each plane hides rebuilt by a masked edit, give clean layers for a camera
push. A straight push-in into an empty plate uncovers nothing behind the planes: there, the bands
plus the full frame as back plate are enough, and steps 3 and 4 are skipped.

1. Find each band on the depth map (white = near): sample rows with
   `magick depth.png -crop 2048x10+0+Y +repage -format "%[fx:mean]" info:` and pick the gray range
   of each object.
2. Run the block below to make the mattes and the edit masks.
3. Pick the edit model at run time: `recommend` with capability `img2img` and feature `mask`,
   quality priority. Read the mask field in `model_schema_get` first: the convention (white = edit,
   or edit where transparent) differs between models. Run one edit per edit mask on the full frame,
   with a prompt that continues the background behind the object.
4. Run the rest of the block to rebuild each plane from the original plus the edit.

```bash
# depth bands, white = near: -level LO%,HI% gives a near-binary matte with a soft edge of 1 to 2 %
magick depth.png -colorspace gray -level 54%,56% mask_front.png
magick depth.png -colorspace gray -level 6.8%,8% mask_mid.png
# edit masks for the clean plates: white = rebuild, dilated 14 px past the object
magick mask_front.png -threshold 50% -morphology Dilate Disk:14 edit_front.png
magick mask_mid.png -threshold 50% -morphology Dilate Disk:14 edit_mid.png
# Scenario MCP, one masked edit of the full frame per edit mask: clean_mid.png (edit_front), clean_back.png (edit_mid)
# planes: the original pixels everywhere no edit was asked for
magick frame.png mask_front.png -alpha off -compose CopyOpacity -composite plane_front.png
magick frame.png clean_mid.png edit_front.png -composite \( mask_mid.png \) -alpha off -compose CopyOpacity -composite plane_mid.png
magick frame.png clean_back.png edit_mid.png -composite plane_back.png
# drift: how much the edit model changed outside its mask (the reason the original goes back on top)
magick frame.png clean_back.png -compose difference -composite -colorspace gray d_back.png
magick edit_mid.png -negate keep_back.png
magick d_back.png keep_back.png -compose multiply -composite -format "back drift mean %[fx:mean*255] max %[fx:maxima*255]\n" info:
for p in front mid; do magick plane_$p.png -format "plane_$p %wx%h alpha mean %[fx:mean.a]\n" info:; done
```

Check: measured on a 2048x1152 frame, bands 54 to 56 % (foreground grass) and 6.8 to 8 % (everything
nearer than the far sky and lake) gave alpha means 0.189 and 0.492. The edit model changed pixels
outside its mask by up to 39 levels (back) and 67 (mid), so the original goes back on top outside
each edit mask. Inspect every rebuilt patch at 1:1 for a ghost of the removed object. Where a flat
sky has to be continued, rebuild it row by row from the sky color at each row's edges instead of
asking the edit model. The planes then go to scenario-after-effects-3d (procedures 8 and 14) for the
push, the coverage check and a sway.

## 10. A generated element on black (fire, smoke)

Realistic fire or smoke that fills the frame is generated here as a clip on pure black, then landed
by scenario-after-effects-vfx. Its routing rule sends that case here: stylized looks, loops, small
accents and dust stay built-in effects.

1. **Pick the model by the look, at run time.** `recommend` with capability `txt2video`, quality
   priority, in plain words ("a realistic flame on pure black for Screen compositing"); `search`
   with `target: "models"` for newer entries. The first picks differ in kind: one gave a perfect
   black (0.01 / 255) with stylized, symmetric shapes; another gave realistic stock-like fire and a
   natural plume with a lifted black. For a realistic element, run the first two picks on one prompt
   and judge on a full frame, never the thumbnail. Turn generated sound off where the schema allows,
   and take a 10-bit MOV when offered.
2. **Prompt for a clean black.** "VFX stock footage element: <element>, isolated on a pure solid
   black background. Locked-off static camera, no camera movement.
   <motion and color in one sentence>. Nothing else in frame: no ground, no fuel, no logs, no smoke,
   no sparks, no reflections, no text. Shot on a black stage for compositing, deep black everywhere
   outside the <element>." Both picks kept the camera locked and the background black with it. What
   still failed: a dark fuel shape at a flame's foot, a flame base running off the bottom edge,
   smoke starting at the bottom edge, and a bright source point at a smoke column's foot. Plan the
   frame so the source sits off screen or behind an object, and hide the foot with a mask (step 4).
3. **Probe before import** (procedure 1): range, frame rate, audio, and the background 99th
   percentile. Measured: an H.264 smoke clip (1080p, 24 fps, 96 frames) arrived tv range with an
   sRGB tag and an AAC track, YMIN 9 to 15, corner YAVG 17.4 to 18.3; After Effects read that corner
   at 2.2 mean (max 14); a 10-bit MOV fire clip had a background p99 of 2.2 / 255, a MOV smoke clip
   12.2 / 255. Turn the layer's audio off (`audioEnabled = false`). A 24 fps clip in a 30 fps comp:
   conform it (plays 1.25x faster, still reads as fire), or keep 24 and accept repeated frames.
4. **Land it with the effects skill:** `AEX.element.land` in scenario-after-effects-vfx, procedures
   section 13, "Generated element on black". It sets the foot mask, the black level (Levels Input
   Black at the background p99), the palette, the glow, the light thrown on the plate, the heat haze
   and the grain. Do not repeat those steps here.
5. **Choose the blend by the plate under the element.** Screen only adds light, and nothing above
   about 230 has room left. Over a plate near white, use a fill darker than the plate in Normal,
   with the element as its luminance track matte. The job below compares the options.

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {clip, plate, blackIn, footRow, feather, out, bright: optional RGB of a solid used instead of the plate, tag}; needs --lib gen.jsx
app.project.bitsPerChannel = 8;
var A = ARGS, out = { frames: {} }, tag = A.tag || "g13";
var el = AEX.gen.land(A.clip, { name: "smoke", fps: 24 });
var pl = AEX.gen.land(A.plate, { name: "plate" });
function foot(l) {
    // mask over the clip that ends half a feather above the source point, feather on the vertical only
    var W = l.source.width, y = A.footRow - A.feather / 2, s = new Shape();
    var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    s.vertices = [[-50, -50], [W + 50, -50], [W + 50, y], [-50, y]]; s.closed = true;
    m.property("ADBE Mask Shape").setValue(s);
    m.property("ADBE Mask Feather").setValue([0, A.feather]);
}
function element(c, masked) {
    var l = AEX.gen.place(c, el, { fit: "cover", name: "smoke" });
    l.audioEnabled = false;
    AEK.build.effect(l, "ADBE Easy Levels2", { "ADBE Easy Levels2-0003": A.blackIn });
    if (masked) { foot(l); }
    return l;
}
function variant(name) {
    var c = AEK.build.comp("v " + name, { width: 960, height: 540, fps: 24, duration: 4, bg: [0, 0, 0] });
    if (name !== "alone" && name !== "alone_nomask") {
        if (A.bright) { AEK.build.solid(c, "plate", A.bright, {}); } else { AEX.gen.place(c, pl, { fit: "cover", name: "plate" }); }
    }
    if (name === "plate") { out.frames[name] = AEK.capture.frame(c, 2, A.out + "/" + tag + "_" + name + ".png").path; return; }
    var l = element(c, name !== "alone_nomask");
    if (name === "screen") { l.blendingMode = BlendingMode.SCREEN; }
    if (name === "unmult") { AEK.build.effect(l, "ADBE Unmult", {}); }
    if (name === "fill_cream" || name === "fill_gray") {
        var col = name === "fill_cream" ? [0.96, 0.94, 0.9] : [0.62, 0.64, 0.68];
        var f = AEK.build.solid(c, "fill", col, {});
        f.moveBefore(l);
        f.setTrackMatte(l, TrackMatteType.LUMA);
    }
    var t = [0.5, 2, 3.5], i;
    for (i = 0; i < t.length; i++) { out.frames[name + "_" + i] = AEK.capture.frame(c, t[i], A.out + "/" + tag + "_" + name + "_" + i + ".png").path; }
}
var v = ["plate", "alone", "alone_nomask", "screen", "unmult", "fill_cream", "fill_gray"], k;
for (k = 0; k < v.length; k++) { variant(v[k]); }
return out;
```

Check: per variant, the mean signed change against the plate on the pixels where the element is
denser than 0.15.

- Over gray 102 (earlier run): Screen as is lifted the corner 1.3 levels mean, 8 at most; Levels
  Input Black 0.03 first brought it to 0.0 (max 4), and the smoke body gain fell from 9.15 to 6.5
  levels. Unmult: corner 103.0, min 100. Set Input Black just above the measured black, no higher.
- Over the illustrated plate, sky at luminance 202: Screen +15.9, Unmult in Normal +9.5, cream fill
  +10.6, gray fill (0.62, 0.64, 0.68) -10.9. Over its dark ground: Screen +33.3, gray fill +14.1.
  Screen stays the right choice there.
- Over a warm white solid (luminance 237): Screen +4.4, Unmult in Normal -1.4, cream fill +0.3. All
  three nearly vanish. The gray fill with the smoke as luminance matte read at -17.2 and looked like
  smoke on the frame.
- Foot: without the mask, the source point peaked at luminance 179 to 194 in the bottom 40 rows; a
  mask ending half a feather above it (feather 120 px, vertical only) left 11 to 18.
- No newly clipped pixel in any variant.

## 11. Depth map and cutout of a supplied still

The still comes from the client or another tool, so nothing was generated with a transparent
background or a depth pass. Upload it (`upload_asset`, then `upload_asset_complete`) into the
project already set for the job, then find each route at run time.

1. **Depth map.** `recommend` with img2img wording ("depth map of this photo") came back `no_match`;
   the route is the catalog tool `asset_detect` (write lane, `scenario_tool_execute_write`). Find it
   with `scenario_tools_search` query "detect depth", or the model with `search` `target: "models"`,
   query "depth", sorted by `createdAt:desc` (look for a detection or ControlNet tool that takes one
   `image` and a modality).
2. Call it with `modality: "depth"` and `remove_background: false`. The default `true` strips the
   background, and a plane cut needs the whole frame.
3. **Cutout.** `recommend` with the words "remove the background from this product photo", quality
   priority. Also run `search` query "remove background" sorted by `createdAt:desc` for newer
   entries. In the schema, look for a single `image` file input, no prompt, and an alpha output at
   the input size.
4. Download both, write the sidecars, probe: the depth map is gray, white = near, at the input size;
   the cutout is RGBA.

```bash
# depth ordering: mean of a 1-row strip from top to bottom should rise (white = near)
for y in 100 600 1200 1800; do magick depth.png -crop 3840x1+0+$y +repage -colorspace gray -format "$y %[fx:mean]\n" info:; done
# cutout: body alpha and color drift inside the body against the source
magick cutout.png -alpha extract -threshold 99% -format "body pixels at 255+: %[fx:mean]\n" info:
magick cutout.png -alpha extract -format "alpha bbox %@\n" info:
```

Check, measured on a 3840x2160 terrace plate and an 880x400 product still: `asset_detect` returned
the same depth map on two runs, rows 100 to 2100 rising from 0.077 to 0.956. The top `recommend`
cutout pick returned body alpha 254 to 255 with RGB identical to the source inside the body, so the
Levels lift of procedure 2 was not needed. Model names change; the task words and the schema shape
are what to search for.

## 12. Seat a supplied object in a generated plate

Studio light on a golden-hour plate reads pasted however good the shadow is. Route by what exists,
then light, scale, shadow, move, and the gate:

| Route                  | When                                                                                      | Shadow and shading come from                                                     |
| ---------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1. Model               | a GLB exists, or image-to-3D through the Scenario MCP can make one (`recommend`, quality) | one sun in Advanced 3D: the 3D skill's procedure 17                              |
| 2. Still only          | no model is wanted; the product's own pixels must stay                                    | the object relit to the plate (steps 2 and 3), a neutral copy kept for the check |
| 3. Mirrored silhouette | a flat object (a card, a sticker), or a small, far one                                    | step 5 below; never for a round object near the camera                           |

The compositing skill's `integration_check.py` is the gate for every route, on the first and last
frame (step 8). Hand it the comp, the plate alone, the element over black, its neutral and the
shadow layers alone.

1. **One light for both.** Either prompt the plate with the light the object already has (direction,
   softness, color), or relight the object to the plate. Write the plate prompt with what scale and
   shadows need: lens, camera height above the floor, level camera, horizon row, sun side and
   height, an empty lit patch for the object.
2. **Relight through an edit model (route 2).** `recommend` with "relight this product to match the
   lighting of the reference scene", quality priority. Pass the object view and the plate as
   references, and state the sun side, the warm rim and the brightness of the light parts. A first
   take came back too dark (cream end caps gray): say how bright they stay. Ask for the largest size
   offered. Cut the relit view out again with the route of procedure 11; keep the studio cutout as
   the neutral.
3. **Gate the warmth before building.** `scripts/seat_check.py CUT.png PLATE.png --floor-top ROW`
   compares the blue-to-red ratio of the object's brightest 2 % with the plate's lit ground. It
   fails above a 0.15 gap. Measured: a studio-lit cutout on a sunset plate failed at +0.32 (cooler);
   the relit view passed at -0.15. Direction, shade and rim are gated by `integration_check.py`
   (step 8).
4. **Scale from a stated real size.** For a level camera, pixels per meter at the object's base row
   = (base row - horizon row) / camera height. Object width on screen = real length x that.
   Measured: horizon at row 235, base at 850, camera 0.12 m: 5125 px/m, so a 0.16 m speaker is 820
   px wide.
5. **Shadow along the plate's own shadows.** Extend two shadow lines already in the plate (a railing
   post, a wall edge) to where they meet near the horizon below the sun. The object's shadow runs
   from its base away from that point. Route 1 places the sun there and renders the shadow. Route 3
   builds it from the silhouette: Fill dark warm brown, Corner Pin mirrored about the base line and
   slanted along that direction, blur growing with distance, Multiply, plus a contact band. Start
   the mirror line inside the body: the blur erodes the shadow's top edge.
6. **Gate the contact.** Write mattes of the object and of its shadow layers at the first and last
   frame (`AEX.threeD.mattes`), then run
   `python3 seat_check.py --contact obj.png cast.png,contact.png`. In every column where the object
   rests, it measures the gap from the object's lowest row to the shadow's first row. Pass: 2 px or
   less, with shadow below at least 90 % of those columns (a column with none floats).
7. **A push that reads.** On 2.5D planes at z 4000 / 1600 / 600 with a 50 mm camera, a 650 px push
   read as a still (front plane grew 1.25 times). 850 px plus a 120 px truck grew it 1.35 times with
   9 % subject-to-back parallax. A push alone shows little parallax near the frame center; the truck
   adds it.

```javascript
// channel: bridge
// checked: live 27.0
// gates in the job (AEX.threeD from scenario-after-effects-3d, loaded with a second --lib)
var g0 = AEX.threeD.screenRect(c, front, 0), g1 = AEX.threeD.screenRect(c, front, c.duration - c.frameDuration);
R.frontGrowth = g1.width / g0.width;                       // at least 1.35
R.parallax = AEX.threeD.parallax(c, { layer: speaker, point: baseAnchor }, { layer: back, point: horizonPoint }, 0, c.duration - c.frameDuration).relPct;   // at least 5
```

Check: front growth, parallax, every plane covering the frame at the last frame (`screenRect`),
`AEX.gen.upscaled(c)` empty, the contact gate on the first and last frame, and the warmth gate.
Measured on the rebuild: growth 1.35, parallax 8.97 %, upscaled empty.

- Contact, cast shadow mirrored at the base with blur 70 source px: median gap 9 px at the first
  frame and 12 at the last, worst column 34 and 44. The gap grew with the object (x 1.35, the push
  growth): one transform, so the cause was the mirror line, not parenting. Anchor moved 160 source
  px into the body: -3 px (tucked under) at both frames, worst column included.

8. **Gate the integration.** On the first and last frame:

```bash
python3 <compositing skill>/scripts/integration_check.py --comp comp.png --plate plate.png \
    --elem elem.png --neutral neutral.png --shadow shadow.png --sun X,Y \
    --plate-shadow X,Y,W,H --plate-lit X,Y,W,H --plate-length RATIO --light back --out check.json
```

Route 1 adds `--rendered` (the rim is read, not gated) and a neutral of the same model under one
white ambient light. Before that, check the model's base colors against the product's brand colors
and correct them in a copy of the texture. Then calibrate the sun and an environment built from the
plate on the plate's own lit and shadowed ground (3D skill, procedure 17): residual under 5 % per
channel. Exit 0 passes. Measured on the terrace shot: a mirrored-silhouette build with a relit
cutout failed contact (6 px gap, overhang 0.065), shadow density and hue, blacks (0.11 against the
plate's 0.34) and rim. The model under guessed lights passed the shadow gates, but its cream caps
read olive-gray. Calibrated, caps read cream; with the base colors written for the renderer and a
shadowed kicker, the camera-facing coral fabric fell from 0.20 to 0.074 linear, red instead of
orange.

When the seat passes its shadow gates and still reads as CG, finish it with an image edit guided by
the render: [render-to-real.md](render-to-real.md).
