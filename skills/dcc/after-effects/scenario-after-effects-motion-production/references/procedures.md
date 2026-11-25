# Procedures: commercial motion production

Every job runs with `ae.py run <job>.jsx --lib <skill>/scripts/adprod.jsx --args '<json>'` (channel
bridge; the same file runs as a handoff script once `ARGS` is pasted at the top). The jobs below are
the ones that ran on After Effects 27.0; they start with `AEK.core.fresh()` because the test
sessions owned the project (it also resets bit depth, working space, color engine, linear blending
and gamma, so a job never inherits the previous project's color settings). In a person's project
drop that line and follow the live-session rules of scenario-after-effects-expert (state, one undo
step, restore).

`<skill>` in the commands below is the folder that holds this skill's SKILL.md; `<lead skill>` is
the scenario-after-effects-expert folder. Resolve both to absolute paths before running.

Helpers: [adprod.jsx](../scripts/adprod.jsx) (`AEX.ad`, inside After Effects) and
[adtools.py](../scripts/adtools.py) (beats, snapping, loudness, safe zone from a PNG, review
scorecard; Python standard library plus ffmpeg and ImageMagick).

Layer names are the contract the checks read: `SHOT_<id>`, `TXT_<id>`, `SFX_<id>_<kind>`, `MUSIC`,
`ENDCARD_BG`, `LOGO`, `CTA_PILL`, `CTA_TXT`, `BADGE_<n>`, `CHAR`, `GUIDE_<zone>`.

## 1. The beat sheet (the edit as data)

One JSON per cut. Frames, not seconds, at the sheet's `fps`. A variant, a shorter cut or another
format is a different sheet or a different layout key, never a hand edit of the comp.

```json
{
 "name": "UA_master_9x16",
 "fps": 30,
 "size": [
  540,
  960
 ],
 "frames": 600,
 "font": "Helvetica-Bold",
 "music": {
  "key": "music",
  "db": -4
 },
 "shots": [
  {
   "id": "hook",
   "f0": 0,
   "f1": 32,
   "clip": "gp_a",
   "src": 0,
   "text": "CAN YOU ESCAPE LEVEL 12?",
   "sfx": "impact",
   "db": -2,
   "textF1": 61
  },
  {
   "id": "loop1",
   "f0": 32,
   "f1": 61,
   "clip": "gp_b",
   "src": 0,
   "text": "TAP TO DASH",
   "sfx": "whoosh",
   "db": -8,
   "textF1": 71
  },
  {
   "id": "loop2",
   "f0": 61,
   "f1": 105,
   "clip": "gp_c",
   "src": 30
  },
  {
   "id": "...",
   "note": "one row per shot"
  }
 ],
 "endcard": {
  "f0": 482,
  "logo": "logo",
  "cta": "PLAY FREE",
  "badges": [
   "App Store",
   "Google Play"
  ],
  "sfx": "stinger",
  "db": -4
 },
 "layout": {
  "9x16": {
   "text": [
    270,
    250
   ],
   "textW": 400,
   "size": 40,
   "logo": [
    270,
    300
   ],
   "logoW": 300,
   "cta": [
    270,
    470
   ],
   "ctaW": 260,
   "badges": [
    [
     180,
     575
    ],
    [
     360,
     575
    ]
   ],
   "badgeW": 160,
   "char": [
    400,
    520
   ],
   "charH": 330
  }
 }
}
```

- `src`: first frame used inside the clip. `textF1`: the line holds past the shot's end (a line may
  cross a cut to reach its reading time).
- `db`: SFX level in dB on `ADBE Audio Levels`. `character: true` puts the character PNG in that
  shot.
- `layout`: positions per format key, in comp pixels. Text boxes are widths; `AEK.text.fit` and a
  two-line fallback keep lines inside them.

## 2. Build the master from the sheet

Channel: bridge, handoff. What it makes: one comp, a comp marker per shot (duration = shot length;
hook and end card as protected regions), shots trimmed by in and out point and cover-fitted,
captured game audio muted, text with a 4-frame scale pop, SFX placed from the sheet (a whoosh starts
0.35 s early so its peak lands on the cut), the end card (logo, CTA pill with a 100 to 104 %
breathing pulse, two badges), beat markers on `MUSIC`, the report, the first-second frames.

```javascript
// channel: bridge
// checked: live 27.0
// 01: beat sheet JSON -> master comp (markers, shots, texts, SFX, end card), beat markers on MUSIC, report, first-second frames.
// ARGS: {sheet, media: {key: abs path}, beats: [float frames], zones, out}
AEK.core.fresh();
var items = AEX.ad.importMedia(ARGS.media);
var b = AEX.ad.build(ARGS.sheet, items, "9x16", { protect: true });
var c = b.comp, R = { built: b.report };
R.beatMarkers = AEX.ad.beatMarkers(c.layers.byName("MUSIC"), ARGS.beats);
R.compMarkers = [];
for (var i = 1; i <= c.markerProperty.numKeys; i++) {
    var mv = c.markerProperty.keyValue(i);
    R.compMarkers.push(mv.comment + " f" + Math.round(c.markerProperty.keyTime(i) * 30) + " d" + Math.round(mv.duration * 30) + (mv.protectedRegion ? " P" : ""));
}
R.levels = { music: c.layers.byName("MUSIC").property("ADBE Audio Group").property("ADBE Audio Levels").value,
    hookShotAudio: c.layers.byName("SHOT_hook").audioEnabled };
R.report = AEX.ad.report(c, ARGS.zones);
R.guides = AEX.ad.guides(c, ARGS.zones, {});
R.frames = AEK.capture.frames(c, [0, 15 / 30, 1, 2, 7.5, 12, 15, 17], ARGS.out, "01");
var g = c.layers.byName("GUIDE_meta_reels_ads"); g.guideLayer = false;
R.guideFrame = AEK.capture.frame(c, 17, ARGS.out + "/01_guide_on_endcard.png");
g.guideLayer = true;
R.guideOffFrame = AEK.capture.frame(c, 17, ARGS.out + "/01_guide_flag_on.png");
return R;
```

Check: `report.zone_violations` empty, `fits` show no overflow, comp markers read `hook f0 d30 P`
... `endcard f480 d120 P`. Measured: 33 layers, 42 beat markers, 3.3 s including 10 PNG frames at
540x960. Sheet: frames 0, 15, 30 carry the hook line on moving gameplay; the end card sits inside
both safe zones.

## 3. Beats and cuts

Detect beats outside After Effects, snap the cuts in the sheet, then write the beats as layer
markers so the offsets are measured in the built comp.

```bash
python3 <skill>/scripts/adtools.py detect music.wav --fps 30 > beats.json       # full mix: tempo fit on an onset envelope
python3 <skill>/scripts/adtools.py detect kick.wav --method silence --fps 30      # a percussive stem with silence between hits
python3 <skill>/scripts/adtools.py grid --bpm 124 --offset 0.1 --seconds 20 --fps 30 > grid.json   # known tempo
python3 <skill>/scripts/adtools.py snap sheet.json beats.json --max 8 --min-shot 18 --out sheet_snapped.json
```

`detect` (default `--method onset`) reads 60 s from `--start`, builds an onset envelope in three
bands (low, mid, high), finds the tempo by autocorrelation within `--bpm-range` (default 70 to 180),
fits the beat phase, and returns `{bpm, offset, beats, frames, confidence, onsets}`. A mix with
steady drums reads `confidence` 0.3 or more. Under 0.2, or with onsets more than 25 ms from the
grid, it adds a `warning`: run it on a stem, past a voice-over, or narrow `--bpm-range` to the tempo
you hear (half or double tempo is the usual error), else use `grid` with the tempo from the brief.

Measured: on two music beds of 126 and 122 bpm (known click positions), the fitted tempo was within
0.02 bpm and every beat within 10 ms over 60 s; a 5 s excerpt read within 0.1 bpm. On a mix with
voice-over over the music, the tempo came back wrong with a `warning`. `--method silence` (ffmpeg
`silencedetect`) found 0 beats on a full mix whose level never drops below about -22 dB between
hits: it only fits a stem. On a 124 bpm stem it matched the grid within 0.01 frame on 42 beats. Ten
cuts placed by eye sat 2.0 to 6.4 frames off the beat; after `snap` the worst was 0.49 frame (frames
are whole, beats are not).

```javascript
// channel: bridge
// checked: live 27.0
// 02: snapped beat sheet -> master, cut-to-beat offsets, then the mix rendered to AIFF for an ebur128 reading.
// ARGS: {sheet, media, beats, zones, out, gainDb (0 on the first pass)}
AEK.core.fresh();
var items = AEX.ad.importMedia(ARGS.media);
var c = AEX.ad.build(ARGS.sheet, items, "9x16", { protect: true }).comp, R = {};
AEX.ad.beatMarkers(c.layers.byName("MUSIC"), ARGS.beats);
R.offsets = AEX.ad.beatOffsets(c);
// After Effects has no master fader: a correction is the same dB added to every audio layer
var n = 0, i, l, lv;
for (i = 1; i <= c.numLayers; i++) {
    l = c.layer(i);
    if (l.hasAudio && l.audioEnabled) {
        lv = l.property("ADBE Audio Group").property("ADBE Audio Levels");
        lv.setValue([lv.value[0] + ARGS.gainDb, lv.value[1] + ARGS.gainDb]); n++;
    }
}
R.audioLayers = n;
R.mix = AEK.capture.queue(c, ARGS.out + "/02_mix_gain" + ARGS.gainDb + ".aif", { template: "AIFF 48kHz" });
return R;
```

Check: every `offsets[].offset` within 1 frame. Convert Audio to Keyframes (command id 4218,
measured by the typography skill) is the fallback when only amplitude is wanted.

## 4. Loudness through a mix bus

After Effects has no master fader and no loudness (LUFS) meter; the Audio panel shows peak levels
during preview only. Render the mix to AIFF, read it with ffmpeg, correct, render again.

```bash
python3 <skill>/scripts/adtools.py loud mix.aif          # integrated LUFS, LRA, true peak dBTP (ebur128=peak=true)
```

Measured: the raw mix read -21.7 LUFS, -2.6 dBTP. +7.7 dB on every layer reached -14.2 LUFS but +0.1
dBTP (over). The working route is a bus: nest the master, put `ADBE Aud Compressor` on the nested
layer, raise Makeup Gain, keep Output Limit below the ceiling. A plain level change is enough when
the gain you need is smaller than the headroom: the measured true peak plus the gain stays at or
under -1 dBTP. Measured on a single music bed: -17.6 LUFS, -6.9 dBTP, +3.6 dB on the music read
-14.0 LUFS, -3.3 dBTP.

A spot under 10 s cannot hold 75 frames of end card and two beats of picture: `review` switches to
45-frame end-card and CTA holds below 10 s, and scales the cuts window to the length.

```javascript
// channel: bridge
// checked: live 27.0
// 03: a mix bus for loudness: nest the master in a delivery comp, Compressor on the nested layer
// (After Effects has no master fader; effects on a precomp layer process the precomp's summed audio).
// ARGS: {sheet, media, out, comp: {threshold, ratio, attack, release, makeup, limit}, tag}
AEK.core.fresh();
var items = AEX.ad.importMedia(ARGS.media), R = {};
var m = AEX.ad.build(ARGS.sheet, items, "9x16", { name: "AD_master_9x16" }).comp;
var d = AEK.build.comp("DELIVERY_9x16", { width: m.width, height: m.height, fps: m.frameRate, duration: m.duration });
var l = d.layers.add(m); l.name = "MASTER";
var k = ARGS.comp;
AEK.build.effect(l, "ADBE Aud Compressor", { "ADBE Aud Compressor-0001": k.threshold, "ADBE Aud Compressor-0002": k.ratio,
    "ADBE Aud Compressor-0004": k.attack, "ADBE Aud Compressor-0005": k.release, "ADBE Aud Compressor-0006": 0,
    "ADBE Aud Compressor-0007": k.makeup, "ADBE Aud Compressor-0008": k.limit }, "BUS_COMP");
R.props = AEK.build.effectProps(l, "BUS_COMP");
R.mix = AEK.capture.queue(d, ARGS.out + "/03_bus_" + ARGS.tag + ".aif", { template: "AIFF 48kHz" });
return R;
```

Compressor match names (measured): `-0001` Threshold (dB, default -16), `-0002` Ratio (3), `-0003`
Knee (15), `-0004` Attack ms (6), `-0005` Release ms (440), `-0006` Auto Release (1), `-0007` Makeup
Gain (0), `-0008` Output Limit (dB, -1). Passes at threshold -20, ratio 4, attack 1, release 100,
limit -1.5: makeup 8 gave -20.3 LUFS; 14.3 gave -15.2 / -1.7 dBTP; 15.5 gave -14.3 / -1.6 dBTP.
Makeup is not dB for dB once the limiter works: step, measure, step. Other audio effects present on
27.0: `ADBE Aud BT`, `ADBE Aud Deesser`, `ADBE Aud Delay`, `ADBE Aud Distortion`, `ADBE Aud_Flange`,
`ADBE Aud Gate`, `ADBE Aud HiLo`, `ADBE Aud Stereo Mixer`, `ADBE Aud Modulator`, `ADBE Aud Reverb`,
`ADBE Aud Reverse`, `ADBE Aud Tone`. No limiter and no loudness meter among them.

## 5. Safe zones per network

Zones are fractions of the frame, each with its source and retrieval date, so one file serves every
size.

```json
{
 "meta_reels_ads": {"top": 0.14, "bottom": 0.35, "left": 0.06, "right": 0.06, "source": "Meta Ads Guide, Instagram Reels ad specs (facebook.com/business/ads-guide), retrieved 2026-11-25"},
 "tiktok_infeed_measured": {"top": 0.125, "bottom": 0.34375, "left": 0.1111, "right": 0.1111, "source": "240/660/120 px at 1080x1920, a third-party measurement of TikTok's in-feed safe-zone file; TikTok publishes the file, not numbers (ads.tiktok.com help, retrieved 2026-11-25)"}
}
```

When a network publishes an overlay file instead of numbers (TikTok, Google), derive the rectangle
from the PNG: the safe area is the transparent hole.

```bash
python3 <skill>/scripts/adtools.py zone tiktok_overlay_1080x1920.png --name tiktok_infeed --source "TikTok in-feed safe zone file, <date>"
```

Measured on a synthetic 1080x1920 overlay with a 840x1020 hole at +120+240: top 0.125, bottom
0.34375, sides 0.11111. `AEX.ad.zoneCheck(comp, zones)` measures every `TXT_`, `LOGO`, `CTA_` and
`BADGE_` layer 4 frames after its in point and on its last frame (parented layers through the
parent's position and scale) against every zone. `AEX.ad.guides(comp, zones, {render})` paints the
unsafe bands as guide layers.

- Measured: a guide layer is skipped by `saveFrameToPng` (frame identical to the frame without it).
  For review frames build the guides with `render: true` (or set `guideLayer = false`), and disable
  them before the delivery render.
- Measured: the zone check caught a logo whose out point had slid to 36 s and whose pop reset its
  scale to 100 %; both were helper bugs, fixed in `adprod.jsx` (`toEnd`, `pop` relative to the
  current scale).

## 6. Variants through Essential Properties

One master, five comps that each hold one instance of it with overrides: hook line, hook clip (media
replacement), CTA. Naming: `<Game>_UA_<ratio>_<length>_H<hook>_C<cta>_v<version>`.

```javascript
// channel: bridge
// checked: live 27.0
// 04: five test cells from one master through Essential Properties (hook line, hook clip, CTA), named by convention.
// Each override is measured IN the master and line-broken before it is written: an override replaces the whole text document.
// Override names are the controller names given at export, so they do not depend on the application language.
// ARGS: {sheet, media, zones, cells: [{h, c, hook, clip, cta}], out, game}
AEK.core.fresh();
var items = AEX.ad.importMedia(ARGS.media), S = ARGS.sheet, W = S.layout["9x16"].textW, R = { cells: [] };
var m = AEX.ad.build(S, items, "9x16", { name: "AD_master_9x16", protect: true }).comp;
var hookTxt = m.layers.byName("TXT_hook"), ctaTxt = m.layers.byName("CTA_TXT"), hookShot = m.layers.byName("SHOT_hook");
function doc(l) { return l.property("ADBE Text Properties").property("ADBE Text Document"); }
doc(hookTxt).addToMotionGraphicsTemplateAs(m, "Hook Text");
doc(ctaTxt).addToMotionGraphicsTemplateAs(m, "CTA");
hookShot.addToMotionGraphicsTemplateAs(m, "Hook Clip");
R.controllers = m.motionGraphicsTemplateControllerCount;
var v = AEK.core.bin("03_variants"), i, k, cell, vc, inst, ov, td, row;
for (i = 0; i < ARGS.cells.length; i++) {
    k = ARGS.cells[i];
    row = { name: ARGS.game + "_UA_9x16_20s_H" + k.h + "_C" + k.c + "_v001", hook: AEX.ad.lineFor(hookTxt, k.hook, W), cta: AEX.ad.lineFor(ctaTxt, k.cta, S.layout["9x16"].ctaW - 40) };
    if (!row.hook.fits || row.cta.lines > 1) { row.rejected = "copy too long for the box: rewrite it, do not shrink one variant"; R.cells.push(row); continue; }
    vc = AEK.build.comp(row.name, { width: m.width, height: m.height, fps: m.frameRate, duration: m.duration, bin: v });
    inst = vc.layers.add(m); inst.name = "MASTER";
    ov = inst.property("ADBE Layer Overrides");
    td = ov.property("Hook Text").value; td.text = row.hook.text; ov.property("Hook Text").setValue(td);
    td = ov.property("CTA").value; td.text = row.cta.text; ov.property("CTA").setValue(td);
    if (k.clip) { ov.property("Hook Clip").setAlternateSource(items[k.clip]); }
    row.readBack = [ov.property("Hook Text").value.text, ov.property("CTA").value.text, ov.property("Hook Clip").alternateSource ? ov.property("Hook Clip").alternateSource.name : "master"];
    row.first = AEK.capture.frame(vc, 0, ARGS.out + "/04_" + (i + 1) + "_f0.png").path;
    row.end = AEK.capture.frame(vc, 18.5, ARGS.out + "/04_" + (i + 1) + "_end.png").path;
    R.cells.push(row);
}
R.masterHookText = doc(hookTxt).value.text;
R.projectItems = app.project.numItems;
return R;
```

Measured: run 1 wrote the hook strings as typed. Every override came back one line wide, 500 to
1,037 px in a 400 px box: an override replaces the whole text document, so the master's line break
and fit do not reach it. `AEX.ad.lineFor` measures in the master, breaks into two balanced lines and
refuses copy that still does not fit (run 2 rejected a 39-character hook at 521 px; the rewrite
"NOBODY SAW THIS COMBO" fit at 284 px). Hook clip overrides land in a `Media Replacement Comps`
folder as `Hook Clip_<file>` comps. 3.5 s for 5 cells with 10 frames. Test-cell design (AppLovin):
change one variable per cell. Here H1 to H4 share C1; H1 C2 changes only the CTA.

## 7. Other aspect ratios from the same sheet

```javascript
// channel: bridge
// checked: live 27.0
// 05: 1:1 and 16:9 from the same beat sheet: layout reflows from the sheet, gameplay crop is measured.
// ARGS: {sheet, media, zones, out}
AEK.core.fresh();
var items = AEX.ad.importMedia(ARGS.media), S = ARGS.sheet, R = {}, f, c, rep, i, fm = [["9x16", [540, 960]], ["1x1", [540, 540]], ["16x9", [960, 540]]];
for (f = 0; f < fm.length; f++) {
    c = AEX.ad.build(S, items, fm[f][0], { name: "UA_" + fm[f][0], size: fm[f][1] }).comp;
    rep = AEX.ad.report(c, { frame5: { top: 0.05, bottom: 0.05, left: 0.05, right: 0.05 } });
    var sh = c.layers.byName("SHOT_hook"), sc = sh.property("ADBE Transform Group").property("ADBE Scale").value[0] / 100;
    R[fm[f][0]] = { fits: rep.texts.length, frameViolations: rep.zone_violations,
        // share of the 9:16 capture that survives a cover fit
        keptWidth: Math.round(Math.min(1, c.width / (540 * sc)) * 1000) / 10, keptHeight: Math.round(Math.min(1, c.height / (960 * sc)) * 1000) / 10,
        frames: AEK.capture.frames(c, [0.5, 12, 18.5], ARGS.out, "05_" + fm[f][0]) };
}
return R;
```

Measured: text reflows from the layout (the 16:9 hook fits on one line, 9:16 and 1:1 break to two);
zero frame violations at 5 % margins. A 9:16 capture cover-fitted into 1:1 keeps 56.3 % of its
height, into 16:9 31.6 %: those shots need a reframe by hand (pick the action per shot with a
Position key) or a capture in the target ratio. The 16:9 end card came out left-weighted from the
layout row: layout rows per format are a design pass, not a formula.

## 7b. One master in several formats (end card, brand spot, product mark)

A brand or product spot cut to music: `AEX.ad.build` with `sheet.style = {preset: "brand"}`. The
preset drops the game-ad defaults (purple end card, white type with a black stroke, 112 % text pop,
85 % logo pop, CTA pill with a pulse, badges): type in a light brand color without stroke, the CTA
as a line of text that enters `ctaDelay` frames after the logo, a soft dark scrim under the hook
line. Override any key in `sheet.style` (`endcardBg`, `textFill`, `cta`, `scrim`; list in
`adprod.jsx`). Tag the shot that shows the product `product: true`. A logo that is a comp starts at
the end-card frame, so its own animation plays on the card; to have it already drawing on the cut,
set the layer's `startTime` a few frames earlier.

`adtools.py review --picture cell.mp4` reads the rendered movie: it fails a run of near-empty frames
longer than 9 frames (under 3 % of the frame differs from its median) and an end card whose median
content is under 8 %. `adtools.py contrast frame.png --box x,y,w,h --fill RRGGBB` measures text
contrast against the frame behind it.

For a master that is not cut from shots (an end card, a product mark), build the master once as a
comp and give each format its own layout row: the master nested, scaled and placed per format, its
own text sizes and positions, its own zones. A crop of one frame is never a format.

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {aep, out}. Master PC_TONE_mark (1000x1000, 90 frames) built before this block in the same job.
var zones5 = { frame5: { top: 0.05, bottom: 0.05, left: 0.05, right: 0.05, source: "5 % title safe" } };
var zones916 = { frame5: zones5.frame5, reels: { top: 0.14, bottom: 0.35, left: 0.06, right: 0.06, source: "Meta Reels ads safe zone" } };
var t = function (name, text, size, pos, at) { return { name: name, text: text, font: "Helvetica-Bold", size: size, fill: [0.96, 0.93, 0.87], position: pos, width: 900, inPoint: at }; };
var layouts = [
    { fmt: "16x9", name: "TONE_EC_16x9_3s_v001", size: [1920, 1080], scale: 78, position: [600, 540], zones: zones5, texts: [t("TXT_name", "TONE", 170, [1330, 520])] },
    { fmt: "9x16", name: "TONE_EC_9x16_3s_v001", size: [1080, 1920], scale: 80, position: [540, 700], zones: zones916, texts: [t("TXT_name", "TONE", 150, [540, 1110])] },
    { fmt: "1x1", name: "TONE_EC_1x1_3s_v001", size: [1080, 1080], scale: 62, position: [540, 440], zones: zones5, texts: [t("TXT_name", "TONE", 130, [540, 900])] }];
var R = AEX.ad.reformat(AEK.core.comp("PC_TONE_mark"), layouts, { bg: [0.05, 0.06, 0.08] }), k, c;
for (k in R) { if (R.hasOwnProperty(k)) { c = app.project.itemByID(R[k].id); R[k].frames = AEK.capture.frames(c, [0.3, 1.0, 2.9], ARGS.out, k); } }
app.project.save(AEK.core.abs(ARGS.aep));
return R;
```

- Each row returns `fits` (font size used, overflow) and `zoneViolations` from `AEX.ad.zoneCheck`,
  which reads every `TXT_`, `LOGO`, `CTA_` and `BADGE_` layer 4 frames after its in point and on its
  last frame.
- Measured: a tagline at y 1240 in 9:16 ended at 1252, 4 px into the Reels bottom band (limit 1248):
  reported on frames 22 and 89. Moved up 65 px, all three formats read zero violations.
- Capture the review frames in the same job, then render each format out of process:
  `ae.py aerender --project <aep> --comp TONE_EC_9x16_3s_v001 --out <file>.mp4 --frames 90` returned
  90 counted frames per format.
- Read one sheet with the three formats at the same times (`ae.py sheet` fits each frame into a
  common tile; a 9:16 frame shows small in a 16:9 tile).
- Legal range, color tags and bit-rate caps of the deliverables belong to
  scenario-after-effects-color-delivery.

## 8. Shorter cuts

Two routes, both measured.

- **Rebuild from a derived sheet** (preferred for a 10 s or 6 s cut): keep the hook, the clearest
  loop shot, the twist, the payoff, the end card; re-snap. Measured 10 s cut: 5 shots, cuts 0.03 to
  0.38 frame from the beat, end card 79 frames, no zone violations.
- **Compress a finished master** with Time Remap keys that play the hook and the end card at speed 1
  (the scripted equivalent of protected regions):

```javascript
// channel: bridge
// checked: live 27.0
// 06c: two ways to a shorter cut. (a) Time Remap keys that hold the hook and the end card at speed 1 and compress only
// the middle (the scripted equivalent of protected regions). (b) A 10 s cut rebuilt from a derived beat sheet.
// ARGS: {sheet, sheet10, media, beats, zones, out}
AEK.core.fresh();
var items = AEX.ad.importMedia(ARGS.media), S = ARGS.sheet, R = {}, fps = 30;
var m = AEX.ad.build(S, items, "9x16", { name: "AD_master_9x16", protect: true }).comp;
var cut = AEK.build.comp("UA_9x16_15s_remap", { width: 540, height: 960, fps: fps, duration: 15 });
var a = cut.layers.add(m); a.name = "MASTER";
a.timeRemapEnabled = true;
var tr = a.property("ADBE Time Remapping"), hook = S.shots[0].f1 / fps, ec = (S.frames - S.endcard.f0) / fps, D = m.duration, d = cut.duration;
// keys added by script are linear: that is what a constant-speed middle needs
tr.setValueAtTime(0, 0); tr.setValueAtTime(hook, hook); tr.setValueAtTime(d - ec, D - ec); tr.setValueAtTime(d, D);
a.outPoint = d;
R.remapKeys = tr.numKeys; R.middleSpeed = Math.round(((D - ec) - hook) / ((d - ec) - hook) * 1000) / 1000;
R.remap = AEK.capture.frames(cut, [20 / fps, (d * fps - 33) / fps, (d * fps - 1) / fps], ARGS.out, "06c_remap");
R.master = AEK.capture.frames(m, [20 / fps, (D * fps - 33) / fps, (D * fps - 1) / fps], ARGS.out, "06c_master");
var c10 = AEX.ad.build(ARGS.sheet10, items, "9x16", { name: "UA_cut10_9x16" }).comp;
AEX.ad.beatMarkers(c10.layers.byName("MUSIC"), ARGS.beats);
R.cut10 = AEX.ad.report(c10, ARGS.zones);
R.cut10Frames = AEK.capture.frames(c10, [0, 2, 4, 6, 8, 9.5], ARGS.out, "06c_cut10");
return R;
```

Measured: frames 20, 417 and 449 of the 15 s cut were pixel-identical to frames 20, 567 and 599 of
the master (RMSE 0); the middle plays at 1.5x. Enabling Time Remap adds keys at 0 and at the source
end: 5 keys after the job, the extra one past the out point.

- Measured traps: setting `outPoint` on the nested layer trims (stretch stays 100, end card lost);
  `layer.stretch = 75` stretches everything uniformly (hook frame 20 differs, RMSE 0.12); protected
  regions made by script did not appear as layer markers on the nested layer, and
  `app.findMenuCommandId("Update Markers from Source")` returned 0. Protected regions act when a
  person drags the out point in the timeline or in Premiere Pro with a MOGRT.

## 9. Review like a creative lead

The report reads the built comp, not the sheet. The scorecard adds loudness from the rendered mix
and lists what a person must judge.

```javascript
// channel: bridge
// checked: live 27.0
// 08: the same pass after the review notes were fixed in the beat sheet (text lines hold across the next cut: textF1).
// Then the review frames with the safe-zone overlay rendered, the variant rendered small (first 90 frames, H.264) and the mix to AIFF.
// ARGS: {sheet, media, beats, zones, cell: {h, c, hook, clip, cta}, game, bus: {threshold, ratio, attack, release, makeup, limit}, out}
AEK.core.fresh();
var items = AEX.ad.importMedia(ARGS.media), S = ARGS.sheet, R = {};
var m = AEX.ad.build(S, items, "9x16", { name: "AD_master_9x16", protect: true }).comp;
AEX.ad.beatMarkers(m.layers.byName("MUSIC"), ARGS.beats);
var hook = m.layers.byName("TXT_hook").property("ADBE Text Properties").property("ADBE Text Document");
hook.addToMotionGraphicsTemplateAs(m, "Hook Text");
m.layers.byName("CTA_TXT").property("ADBE Text Properties").property("ADBE Text Document").addToMotionGraphicsTemplateAs(m, "CTA");
m.layers.byName("SHOT_hook").addToMotionGraphicsTemplateAs(m, "Hook Clip");
var k = ARGS.cell, name = ARGS.game + "_UA_9x16_20s_H" + k.h + "_C" + k.c + "_v001";
var v = AEK.build.comp(name, { width: 540, height: 960, fps: 30, duration: 20 });
var inst = v.layers.add(m), ov = inst.property("ADBE Layer Overrides"), td;
var hookLine = AEX.ad.lineFor(m.layers.byName("TXT_hook"), k.hook, S.layout["9x16"].textW);
td = ov.property("Hook Text").value; td.text = hookLine.text; ov.property("Hook Text").setValue(td);
td = ov.property("CTA").value; td.text = k.cta; ov.property("CTA").setValue(td);
ov.property("Hook Clip").setAlternateSource(items[k.clip]);
// mix bus: the Compressor on the variant's master layer, settings from the loudness pass (case 03)
var B = ARGS.bus;
AEK.build.effect(inst, "ADBE Aud Compressor", { "ADBE Aud Compressor-0001": B.threshold, "ADBE Aud Compressor-0002": B.ratio,
    "ADBE Aud Compressor-0004": B.attack, "ADBE Aud Compressor-0005": B.release, "ADBE Aud Compressor-0006": 0,
    "ADBE Aud Compressor-0007": B.makeup, "ADBE Aud Compressor-0008": B.limit }, "BUS_COMP");
// the report reads the master with the variant's own hook text in place
var d0 = hook.value, d1 = hook.value; d1.text = hookLine.text; hook.setValue(d1);
R.report = AEX.ad.report(m, ARGS.zones);
hook.setValue(d0);
AEX.ad.guides(v, ARGS.zones, { render: true });
R.review = AEK.capture.frames(v, [0, 0.5, 1, 7.5, 12, 18.5], ARGS.out, "08_review");
v.layers.byName("GUIDE_meta_reels_ads").enabled = false; v.layers.byName("GUIDE_tiktok_infeed_measured").enabled = false;
R.video = AEK.capture.queue(v, ARGS.out + "/" + name + "_f0-89.mp4", { template: "H.264 - Match Render Settings - 15 Mbps", start: 0, duration: 3 });
R.mix = AEK.capture.queue(v, ARGS.out + "/" + name + "_mix.aif", { template: "AIFF 48kHz" });
R.name = name;
return R;
```

```bash
python3 <skill>/scripts/adtools.py review 08_review_after_fix.out.json --render <variant>_mix.aif > scorecard.json
python3 <lead skill>/scripts/ae.py probe <variant>_f0-89.mp4
```

Measured on variant H3 C1: first pass 13 of 17 (hook line 32 frames for 5 words, two lines under
their reading time, 3 cuts in the second 10 s). Fix in the sheet: `textF1` lets each line hold
across the next cut. Second pass 16 of 17; the remaining "3 cuts in 300-600" is the 3 s payoff hold,
a creative call left to the person. Render: 90 frames, H.264 Main yuv420p 540x960 30 fps, AAC 48 kHz
stereo, 6.8 MB; the "15 Mbps" template measured 18.9 Mbps on this noisy footage (check size limits
on the file, not the template name). Mix: -14.3 LUFS, -1.6 dBTP.

## 10. Data-driven sound design (inside step 2)

- One `SFX_` layer per sheet row with a `sfx` kind; levels in dB set by script on
  `ADBE Audio Group` > `ADBE Audio Levels` (`[db, db]`).
- `SFX_LEAD` in `adprod.jsx` holds per-kind lead times (whoosh 0.35 s). Impacts and ticks start on
  the cut.
- Captured game audio is muted (`audioEnabled = false`) and re-laid as designed sound.
- Layer hits by frequency (deep, mid, high) instead of one perfect whoosh (Herman Huang, tzfzkTAQsnE
  00:00:34). Generated SFX and music enter through scenario-after-effects-generation.
- Music exit and entry (Herman Huang, tzfzkTAQsnE 00:05:17 to 00:06:33): cut the bed before the next
  beat and let the last beat ring out through a reverb tail; to enter, reverse the first beat as a
  riser. A fade "slams the brakes". Prepare the bed with ffmpeg, then import it as `MUSIC`:

```bash
# exit: body up to the last beat, the last beat (5.423 to 5.90 s, cut before the beat at 5.907 s) padded 1.5 s and echoed
ffmpeg -i music.wav -filter_complex "[0]atrim=0:5.423,asetpts=PTS-STARTPTS[a];[0]atrim=5.423:5.90,asetpts=PTS-STARTPTS,apad=pad_dur=1.5,aecho=0.8:0.9:60|150|300|500|800:0.6|0.5|0.4|0.3|0.2[b];[a][b]concat=n=2:v=0:a=1[o]" -map "[o]" music_exit.wav
# entry: the first beat reversed as a riser, then the track from the second beat
ffmpeg -i music.wav -filter_complex "[0]atrim=0.1:0.584,asetpts=PTS-STARTPTS,areverse,afade=t=in:d=0.3[r];[0]atrim=0.584,asetpts=PTS-STARTPTS[m];[r][m]concat=n=2:v=0:a=1[o]" -map "[o]" music_entry.wav
```

Measured on a 124 bpm bed: the last beat peaked at -4.2 dBFS; the tail read -15 dBFS peak in its
first 0.5 s, -37 dBFS in the next 0.5 s, silent after 1 s. Take the beat times from
`adtools.py detect` or `grid`. Inside After Effects, `ADBE Aud Reverb` and `ADBE Aud Reverse` exist
on 27.0, but a layer's audio stops at its out point: the tail needs a precomp longer than the music
it holds [added].

## 11. Delivery render and the file gate

Render each cell with the default H.264 module (writes `.mp4` whatever extension is given; moov
before mdat, so fast start without a setting). The template name is not a bit-rate cap: 18.9 Mbps
measured on noisy footage. `aerender` exits 0 when the comp name is wrong, with only "aerender
ERROR: No comp was found with the given name." in its log, so the gate is the output file, never the
exit code.

```bash
ae.py aerender --project <project>/AD_cells.aep --comp "<Game>_UA_9x16_20s_H1_C1_v001" \
  --out <project>/renders/<Game>_UA_9x16_20s_H1_C1_v001.mp4 --template "H.264 - Match Render Settings - 15 Mbps"
F=<project>/renders/<Game>_UA_9x16_20s_H1_C1_v001.mp4
test -s "$F" || echo "FAIL: no file (check the comp name, the folder exists, the log)"
python3 <lead skill>/scripts/ae.py probe "$F" --count    # codec, size, fps, counted frames, audio, bit rate, file size
```

`ae.py aerender` itself fails with `why` on a full disk, a stalled render or a file shorter than the
frames rendered; pass `--frames` with the cell's length. Measured on 27.0 with a saved 1 s 540x960
comp: a comp name one character off returned exit 0 and no file; the right name returned exit 0 and
an H.264 540x960 30 fps file of 30 frames. Compare bit rate and file size with each network's cap
from the brief or its spec page (Apple App Store previews: 500 MB). Over the cap, re-encode with
ffmpeg (`-maxrate`, `-bufsize`, `+faststart`) through scenario-after-effects-color-delivery. For a
Render Queue render by script, create the folder first: `render()` throws "Directory does not
exist".

## 12. File and comp naming

One pattern for every deliverable: `<Brand>_<Type>_<ratio>_<length>_v<###>`, the same string for the
comp, the render and the file. Ratio as `16x9`, `9x16`, `1x1`, `4x5`; length in whole seconds (`5s`,
`20s`); version with three digits.

| Type           | Use                                       | Example                         |
| -------------- | ----------------------------------------- | ------------------------------- |
| `UA_H<n>_C<n>` | user acquisition test cell: hook n, CTA n | `Game_UA_9x16_20s_H1_C2_v001`   |
| `EC`           | end card or packshot alone                | `Brand_EC_9x16_5s_v001`         |
| `SPOT`         | brand or product spot                     | `Brand_SPOT_16x9_15s_v003`      |
| `CUT<n>`       | shorter cut derived from a master         | `Brand_SPOT_CUT10_1x1_10s_v001` |

- A new version raises `v<###>` on every file of the set, even the formats that did not change, so a
  set always shares one number.
- The master comp and its precomps keep the project skill's prefixes (`MAIN_`, `PC_`); only
  delivered comps carry this pattern.

## Version notes

- Essential Properties carry that name since 17.5 (October 2020; earlier builds say Master
  Properties). `Property.essentialPropertySource` since 22.0.
- Any layer as a track matte since 23.0; H.264 from the Render Queue since 23.0.
- Audio Compressor, Gate and Distortion arrived in 26.0, De-esser in 27.0: on 25.x the mix bus has
  no compressor, so render stems and mix outside After Effects.
- Protected regions (Responsive Design - Time): set by script with `MarkerValue.protectedRegion`,
  but on 27.0 a scripted out-point change or `stretch` ignored them (Procedure 8).
