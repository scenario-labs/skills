# Procedures: generated media into After Effects

Every job below ran on After Effects 27.0 (build 27.0x78) through the bridge, on files generated
with the Scenario MCP. Jobs are function bodies for
`ae.py run job.jsx --lib <skill>/scripts/gen.jsx --args '{...}'`. In a person's open project, add
`--undo "Agent: <what>"` so the job is one undo step. Paths come from `ARGS` and are absolute.

## 0. Generate, download, keep provenance (Scenario MCP)

1. `recommend` with the need in plain words and `priority: "quality"`. Read `next_step`: on
   `proceed`, take the specialty or the top entry; on `ask_user`, present the options. For 3D,
   prefer the newest first-party model in the list. For a chain (style frame, then video, then
   voice), `plan_generation` first.
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
// ARGS: {layers:[front..back], plate: the full frame, z:[0, 600, 1500, 3000], push, truck, seconds}
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
// ARGS: {glb, hdr, prov}
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

Check: four turntable frames on a sheet; the material names match the GLB. Measured: a 0.121 m model
gave a 117 x 37.5 footprint at scale 100 (origin at its base), fitted at 863 %. HDR and EXR rendered
identical frames; the 8-bit PNG skybox rendered 10 % brighter. Frames took 0.26 to 0.46 s, the first
1.28 s. Camera, shadows and depth of field go to scenario-after-effects-3d.

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
