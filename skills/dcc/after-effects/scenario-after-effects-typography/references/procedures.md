# Procedures: kinetic typography by script

Every job runs through `ae.py run job.jsx --lib <this skill>/scripts/typography.jsx`
(scenario-after-effects-expert toolkit). Jobs are ES3 function bodies: `ARGS` holds the `--args`
JSON, `return` sends the result. In a user's session, never call `AEK.core.fresh()` (it closes the
project): build into a new comp instead, and pass `--undo "Agent: <what>"` so the change is one undo
step.

Match names used below were all read back in 27.0: `ADBE Text Animators` > `ADBE Text Animator` >
`ADBE Text Selectors` (`ADBE Text Selector`, `ADBE Text Wiggly Selector`,
`ADBE Text Expressible Selector` > `ADBE Text Expressible Amount`) and
`ADBE Text Animator Properties`; More Options `ADBE Text More Options` >
`ADBE Text Anchor Point Option` (1 Character, 2 Word, 3 Line, 4 All),
`ADBE Text Anchor Point Align`; range Advanced `ADBE Text Range Advanced` >
`ADBE Text Selector Mode`, `ADBE Text Selector Max Amount` (Amount), `ADBE Text Range Shape`,
`ADBE Text Levels Max Ease`, `ADBE Text Levels Min Ease`, `ADBE Text Range Type2` (Based On).

## 1. Font inventory before choosing

Channel: bridge. Lists families, variable fonts with their axes, and glyph coverage for the
languages of the job.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var R = { families: 0, variable: [] }, all = app.fonts.allFonts, i, j, f;
R.families = all.length;
for (i = 0; i < all.length; i++) {
    for (j = 0; j < all[i].length; j++) {
        f = all[i][j];
        // designAxesData keys are name, tag, min, max, default (not minValue/maxValue)
        if (f.hasDesignAxes && R.variable.length < 20) { R.variable.push(f.postScriptName + " " + f.designAxesData[0].tag + " " + f.designAxesData[0].min + ".." + f.designAxesData[0].max); }
    }
}
var want = ARGS.fonts || ["Helvetica-Bold"], text = ARGS.text || "äöüßéñ";
R.check = {};
for (i = 0; i < want.length; i++) {
    var found = app.fonts.getFontsByPostScriptName(want[i]);
    R.check[want[i]] = found.length ? { installed: true, glyphs: found[0].hasGlyphsFor(text) } : { installed: false };
}
return R;
```

Check: `installed` true and `glyphs` true for every language string. A missing font is accepted
silently by `TextDocument.font` and substituted at render. On the test Mac: 191 family groups;
variable fonts Skia (wght 0.48 to 3.2, wdth 0.62 to 1.3), Kefa III and Noto Sans Syriac (wght);
Helvetica-Bold covers German and Polish, not Japanese.

## 2. Word timings from the voiceover, without listening

Channel: shell. Any speech-to-text run that writes word timestamps works (segments[].words[] with
word, start, end in seconds); for a known script, keep the script's words and only use the times.

```bash
# speech-to-text with word timestamps (example: a local recognizer), then a silence pass to cross-check
<speech-to-text> vo.wav --word_timestamps True --output_format json --output_dir <project>/align
ffmpeg -i vo.wav -af silencedetect=n=-35dB:d=0.12 -f null - 2> <project>/align/silence.log
python3 <skill>/scripts/word_timings.py <project>/align/vo.json --fps 24 --lead 1 --silence <project>/align/silence.log --out <project>/align/words.json
```

Output: `words[]` with `f0` (first frame, already `lead` frames early), `f1`, `frames`, `phrase`;
`phrases[]`; `checks`. A new phrase starts after a pause of 0.18 s or more, or after `.`, `!`, `?`.
Check: `checks.increasing` true, `checks.silence_agrees` true (phrase onsets within 2 frames of a
`silence_end`). Measured on a synthetic 8.5 s voiceover: 27 words, 7 phrases, onsets 0 to 1.1 frames
before the silence end. `checks.short` lists words held fewer than 6 frames before the next word: 15
of 27 at speech pace, which is why words accumulate inside a phrase instead of replacing each other.

## 3. Phrase layers with one marker per word and an expression-selector reveal

Channel: bridge. `ARGS`: `{data: <words.json>, audio: <abs path>}`.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var D = ARGS.data, fps = D.fps;
var c = AEK.build.comp("G4_sync", { width: 1920, height: 1080, fps: fps, duration: 8.5, bg: [0.06, 0.06, 0.08] });
var au = AEK.xio.importFile(ARGS.audio, {});
c.layers.add(AEK.core.itemById(au.id)).name = "VO"; // importFile returns a description: fetch the item by id
var rows = AEX.type.phraseLayers(c, D, { font: "Helvetica-Bold", size: 110, fill: [1, 1, 1], position: [960, 560], tail: 6 });
return rows;
```

What `phraseLayers` builds per phrase: a centered text layer, in point at the first word's `f0`, out
point at the phrase end + `tail` frames (capped at the next phrase), one layer marker per word
(comment = word), and an animator `reveal` (Opacity 0, Position y + 30 % of the size) whose only
selector is an expression selector, Based On Words:

```javascript
// expression (JavaScript engine): Text > Animator "reveal" > Expression Selector > Amount
// checked: live 27.0
var FR = 4;
var m = thisLayer.marker, k = textIndex;
if (k > m.numKeys) { 0; } else {
  var t0 = m.key(k).time;
  100 * (1 - ease(time, t0, t0 + FR * thisComp.frameDuration, 0, 1));
}
```

Retiming a word = moving its marker; nothing else changes. Check: 27 markers on 27 words, 0
mismatches between marker time and `f0`, no `expressionError`. Pixel check on rendered frames: 0
white pixels before the first word, then 9,792, 19,622 and 38,656 pixels above 200 at frames 5, 13
and 30 as words arrive.

## 4. Animator looks: rise, square, word pop, tracking-in

Channel: bridge. Keys go on the selector; the property holds the offset from the base style.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.build.comp("looks", { width: 1920, height: 1080, fps: 24, duration: 2 });
function sel(l, an) { return AEX.type.animatorByName(l, an).property("ADBE Text Selectors").property(1); }
// per-character rise: Ramp Up, Ease Low 100, Offset -100 -> 100
var a = AEK.text.add(c, "CHARACTER RISE", { font: "Helvetica-Bold", size: 96, fill: [1, 1, 1], justify: "center", position: [960, 200] });
AEK.text.animator(a, { name: "rise", properties: { opacity: 0, position: [0, 80] }, basedOn: "charactersExcludingSpaces", shape: "rampUp", easeLow: 100, offset: -100 });
AEX.type.grouping(a, "character", [0, -50]);
AEK.motion.key(sel(a, "rise").property("ADBE Text Percent Offset"), 0, -100); AEK.motion.key(sel(a, "rise").property("ADBE Text Percent Offset"), 20 / 24, 100);
// one character at a time: Square needs Offset 0 -> 100 (from -100 it starts visible, hides, then reveals)
var b = AEK.text.add(c, "SQUARE NO OVERLAP", { font: "Helvetica-Bold", size: 96, fill: [1, 1, 1], justify: "center", position: [960, 420] });
AEK.text.animator(b, { name: "square", properties: { opacity: 0, position: [0, 80] }, basedOn: "charactersExcludingSpaces", shape: "square", offset: 0 });
AEK.motion.key(sel(b, "square").property("ADBE Text Percent Offset"), 0, 0); AEK.motion.key(sel(b, "square").property("ADBE Text Percent Offset"), 20 / 24, 100);
// word pop: Based On Words AND Anchor Point Grouping Word, or the scale pivots on characters
var w = AEK.text.add(c, "word by word reveal", { font: "Helvetica-Bold", size: 96, fill: [1, 1, 1], justify: "center", position: [960, 660] });
AEK.text.animator(w, { name: "pop", properties: { opacity: 0, scale: [40, 40, 100] }, basedOn: "words", shape: "rampUp", easeLow: 100, offset: -100 });
AEX.type.grouping(w, "word", [0, -25]);
AEK.motion.key(sel(w, "pop").property("ADBE Text Percent Offset"), 0, -100); AEK.motion.key(sel(w, "pop").property("ADBE Text Percent Offset"), 20 / 24, 100);
// tracking-in: whole line selected, the selector Amount keyed 100 -> 0 with an expo-out curve
var t = AEK.text.add(c, "TRACKING IN", { font: "Helvetica-Bold", size: 96, fill: [1, 1, 1], justify: "center", position: [960, 900] });
AEK.text.animator(t, { name: "track", properties: { tracking: 300, opacity: 0 } });
var amt = function () { return sel(t, "track").property("ADBE Text Range Advanced").property("ADBE Text Selector Max Amount"); };
AEK.motion.key(amt(), 0, 100); AEK.motion.key(amt(), 20 / 24, 0);
AEK.motion.bezier(amt(), 1, 2, [0.16, 1, 0.3, 1]);
return AEK.capture.spread(c, 6, ARGS.out, "looks");
```

Check with `sourceRectAtTime` (it includes animator offsets and tracking): rise top moves 9 to -71
px over 20 frames; square top stays at 9 until a character is released; tracking width 3,622 px at
frame 0, 1,145 at frame 5, 622 at rest (expo-out finishes 83 % of the move in a quarter of the
time); word pop width 773 to 921 px. On the sheet: settled lines identical to the static text.

## 5. Expression selector: stagger by index

Channel: bridge. Amount is three-dimensional (`[x, y, z]`); a scalar return applies to all three.

```javascript
// expression (JavaScript engine): Text > Animator > Expression Selector > Amount (Based On Words or Characters)
// checked: live 27.0
var d = 3 * thisComp.frameDuration, t0 = inPoint + (textIndex - 1) * d;
selectorValue * (1 - ease(time, t0, t0 + 6 * thisComp.frameDuration, 0, 1));
```

Measured: Amount `0` leaves the text untouched, `100` applies the full animator value, `[0, 0, 0]`
equals `0`, the default `selectorValue * textIndex / textTotal` gives a partial gradient. Reading
`Amount.valueAtTime()` from a script returns `100,100,100` whatever the expression: it is evaluated
per character only at render. Judge an expression selector on frames, not on its script value.

## 6. Per-character 3D flip

Channel: bridge. Turn the switch on BEFORE adding X or Y rotation: those properties belong to
per-character 3D.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.build.comp("pc3d", { width: 1920, height: 1080, fps: 24, duration: 2 });
var l = AEK.text.add(c, "FLIP INTO PLACE", { name: "flip", font: "Helvetica-Bold", size: 140, fill: [1, 0.85, 0.3], justify: "center", position: [960, 600] });
l.threeDPerChar = true; // also makes the layer 3D
AEK.text.animator(l, { name: "flip", properties: { opacity: 0 }, basedOn: "charactersExcludingSpaces", shape: "rampUp", easeLow: 100, offset: -100 });
var ap = function () { return AEX.type.animatorByName(l, "flip").property("ADBE Text Animator Properties"); };
ap().addProperty("ADBE Text Rotation X"); ap().property("ADBE Text Rotation X").setValue(-90);
ap().addProperty("ADBE Text Position 3D"); ap().property("ADBE Text Position 3D").setValue([0, 0, -150]);
AEX.type.grouping(l, "character", [0, -50]); // pivot at mid cap height
var off = function () { return AEX.type.animatorByName(l, "flip").property("ADBE Text Selectors").property(1).property("ADBE Text Percent Offset"); };
AEK.motion.key(off(), 0, -100); AEK.motion.key(off(), 1, 100);
var cam = AEK.build.camera(c, "cam", { focalLength: 50 });
cam.property("ADBE Transform Group").property("ADBE Position").setValue([1300, 250, -2400]);
cam.property("ADBE Transform Group").property("ADBE Anchor Point").setValue([960, 600, 0]);
return AEK.capture.frames(c, [0, 0.25, 0.5, 0.75, 1.25], ARGS.out, "flip");
```

Check: `threeDPerChar` and `threeDLayer` read true, renderer `ADBE Advanced 3d` (Classic 3D). Pixel
count above 150: 0, 9,266, 40,813, 58,339, 58,117 at frames 0, 6, 12, 18, 30 (settled by frame 18).
On the sheet: letters swing up from their mid-height in perspective, flat at rest. Switching
`threeDPerChar` back to false leaves `threeDLayer` true and resets X Rotation to 0 (Adobe documents
the loss).

Advanced 3D: the same job with `c.renderer = "ADBE Calder";` after `AEK.build.comp` rendered the
same flip (pixels above 150 on the flip line: 0, 14,300, 47,577, 59,810, 59,483 at frames 0, 6, 12,
18, 30; flat at rest on the sheet). In that comp `l.motionBlur = true` throws "Motion blur is not
supported by the current composition renderer": keep Classic 3D for blurred letters, or blur a
precomp with CC Force Motion Blur (scenario-after-effects-3d).

Orbit instead of flip: push the anchor back in Z in an unanimated setup animator, then rotate on Y
through the selector (Korenman, b1_p2qQf_Ts 00:25:38 to 00:27:51; he uses 200 px).

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.build.comp("orbit", { width: 1920, height: 1080, fps: 24, duration: 2 });
c.renderer = "ADBE Calder"; // Advanced 3D; per-character 3D also renders in Classic 3D
var m = AEK.text.add(c, "ORBIT", { name: "orbit", font: "Helvetica-Bold", size: 140, fill: [1, 1, 1], justify: "center", position: [960, 320] });
m.threeDPerChar = true;
m.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator").name = "setup";
AEX.type.animatorByName(m, "setup").property("ADBE Text Animator Properties").addProperty("ADBE Text Anchor Point 3D");
AEX.type.animatorByName(m, "setup").property("ADBE Text Animator Properties").property("ADBE Text Anchor Point 3D").setValue([0, 0, 200]);
AEK.text.animator(m, { name: "rot", properties: { opacity: 0 }, basedOn: "charactersExcludingSpaces", shape: "rampUp", easeLow: 100, offset: -100 });
var rp = function () { return AEX.type.animatorByName(m, "rot").property("ADBE Text Animator Properties"); };
rp().addProperty("ADBE Text Rotation Y"); rp().property("ADBE Text Rotation Y").setValue(-120);
var off = AEX.type.animatorByName(m, "rot").property("ADBE Text Selectors").property(1).property("ADBE Text Percent Offset");
AEK.motion.key(off, 0, -100); AEK.motion.key(off, 1, 100);
var cam = AEK.build.camera(c, "cam", { focalLength: 50 });
cam.property("ADBE Transform Group").property("ADBE Position").setValue([1300, 250, -2400]);
cam.property("ADBE Transform Group").property("ADBE Anchor Point").setValue([960, 500, 0]);
return AEK.capture.frames(c, [0, 0.25, 0.5, 0.75, 1.25], ARGS.out, "orbit");
```

Measured in an Advanced 3D comp (`ADBE Calder`), 140 px Helvetica Bold "ORBIT": pixels above 150 at
frames 0, 6, 12, 18, 30 read 0, 12,946, 26,239, 31,438, 31,429; on the sheet letters swing in around
a point behind them, widely spaced mid-move, and settle flat.

## 7. One word styled by character range; variable font weight

Channel: bridge. CharacterRange needs 24.3+, `addVariableFontAxis` 26.0+.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.build.comp("ranges", { width: 1920, height: 1080, fps: 24, duration: 2 });
var a = AEK.text.add(c, "Make it BOLD today", { name: "range", font: "Helvetica", size: 100, fill: [1, 1, 1], justify: "center", position: [960, 300] });
var p = a.property("ADBE Text Properties").property("ADBE Text Document"), d = p.value, s = d.text.indexOf("BOLD");
var cr = d.characterRange(s, s + 4);
cr.fillColor = [1, 0.45, 0.1]; cr.fontSize = 130; cr.font = "Helvetica-Bold";
p.setValue(d); // ranges edit the TextDocument copy: write it back
d = p.value;
var check = { first: d.characterRange(0, 1).font, word: d.characterRange(s, s + 4).font + " " + d.characterRange(s, s + 4).fontSize, docFont: d.font };
// variable font: the axis animator; the base style stays at its default instance
var b = AEK.text.add(c, "Variable weight", { name: "vf", font: "Skia-Regular", size: 140, fill: [1, 1, 1], justify: "center", position: [960, 700] });
b.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator").name = "weight";
var ax = AEX.type.animatorByName(b, "weight").property("ADBE Text Animator Properties").addVariableFontAxis("wght");
var mn = ax.matchName; // "ADBE Text VF Axis 1", display name "Font Axis Weight"
var w = function () { return AEX.type.animatorByName(b, "weight").property("ADBE Text Animator Properties").property(mn); };
AEK.motion.key(w(), 0, 0); AEK.motion.key(w(), 1, 2.2);
check.widths = [b.sourceRectAtTime(0, false).width, b.sourceRectAtTime(1, false).width];
return check;
```

Measured: `d.font` and `d.fontSize` report the FIRST character (Helvetica 100) while the range reads
Helvetica-Bold 130; line width 886 to 982 px. `characterRange(0, -1)` reaches the last character
(tracking 20 read back). Skia axes: wght 0.48 to 3.2 (default 1), wdth 0.62 to 1.3. The weight
animator keyed 0 to 2.2 widened the line 888, 998, 1,060 px at 0, 0.5, 1 s. Use axis values inside
`min..max` from `designAxesData`.

```javascript
// expression (JavaScript engine): any layer > any property that should follow the weight
// checked: live 27.0
thisComp.layer("vf").text.animator("weight").property.fontAxisWght
```

Measured: returns 2.2 at 1 s. For a project-wide font swap use `AEK.session.setFont(ps, {map})` and
`AEK.session.fontRuns(doc)` from the scenario-after-effects-expert kit (each run keeps its weight);
`app.project.replaceFont` is not undoable.

## 8. Fitting three languages in title safe

Channel: bridge. Order of remedies: rebreak at the designed size, then shrink to no less than 80 %,
then scale-to-fit.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.build.comp("fit", { width: 1920, height: 1080, fps: 24, duration: 1 });
var maxW = c.width * 0.8, out = {}, k;
var L = { en: "Make every frame readable", de: "Mach jedes Einzelbild lesbar und verständlich", fi: "Tee jokaisesta kuvaruudusta luettava" };
for (k in L) {
    if (!L.hasOwnProperty(k)) { continue; }
    var l = AEK.text.add(c, L[k], { name: k, font: "Helvetica-Bold", size: 110, fill: [1, 1, 1], justify: "center", position: [960, 540] });
    var row = { width: Math.round(AEK.text.measure(l, 0).comp.width) };
    var s1 = l.duplicate(); row.shrink = AEK.text.fit(s1, maxW, { minSize: 60 }); s1.enabled = false;
    row.balanced = AEX.type.balance(l, maxW, 3); // edits l in place: point text with \r line breaks
    row.safe = AEK.text.inFrame(l, c, 0.1, 0).ok;
    out[k] = row;
}
return out;
```

Measured at 110 px Helvetica Bold, safe width 1,536 px: English 1,395 px (fits); German 2,387 px
(171 %): shrink to 70 px (64 %, too small) or 2 lines at 110 px, 1,220 px wide; Finnish 1,937 px:
shrink to 87 px (79 %) or 2 lines at 110 px, 1,157 px. `sourceRectAtTime(t, true)` equaled
`(t, false)` on unstroked point text.

```javascript
// expression (JavaScript engine): Text layer > Transform > Scale (scale-to-fit, never above 100 %)
// checked: live 27.0
var w = sourceRectAtTime(time, false).width, m = 1536;
var s = Math.min(100, 100 * m / Math.max(w, 1));
[s, s]
```

Measured: 64.3 % for the German line, 79.3 % for Finnish. Scale keeps tracking and leading ratios
but makes stroke widths and drop shadows shrink with it.

Box text (procedure 12): a 900 px box with "Geschwindigkeitsbegrenzungen gelten" (the word alone is
1,675 px at 110 px) composed three lines "Geschwindigkeit", "sbegrenzungen", "gelten": a split at a
wrong point, `autoHyphenate` true, `boxOverflow` false. Read lines with
`d.composedLineRange(i, i + 1)` (`characterStart`, `characterEnd`).

## 9. Reusable in and out driven by the layer's in and out points

Channel: bridge. `AEX.type.inOut(layer, {inFrames, outFrames, properties, basedOn, shape, easeLow})`
adds the animator and this Offset expression:

```javascript
// expression (JavaScript engine): Text > Animator "in-out" > Range Selector 1 > Offset (Ramp Up, Ease Low 100)
// checked: live 27.0
var f = thisComp.frameDuration, a = 12 * f, b = 10 * f;
if (time < outPoint - b) { linear(time, inPoint, inPoint + a, -100, 100); }
else { linear(time, outPoint - b, outPoint, 100, -100); }
```

Measured: on a layer 0 to 48 frames, Offset at in, in + 6, in + 12, middle, out - 5 frames read
-100, 0, 100, 100, 0. After sliding the layer 12 frames later and trimming it to 42 frames, the same
probes read the same values. The out runs the in backwards (last character leaves first); for a
left-to-right exit add a second animator keyed the same way. Save the result as an animation preset
only through the GUI (gui-paths.md); by script, rebuild it with `AEX.type.inOut`.

## 10. Readability report

Channel: bridge. Read-only on the comp.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var rep = AEX.type.readability(c, { bg: ARGS.bg, minFrames: 18, minCapRatio: 0.035, safe: 0.1, minContrast: 4.5 });
return rep;
```

Each row: words, frames on screen, frames per word, font, size, cap height in px (from a temporary
"H" in the same font, scaled like the layer) and as a ratio of comp height, WCAG contrast of fill vs
`bg`, `inSafe` at mid-life, tracking, leading ratio. Measured on the synced piece: 7 phrases, 22 to
38 frames each, 6.4 to 8.3 frames per word, cap 79 px (7.3 % of 1080), contrast 19.07:1, all in
safe. Built-to-fail layers raised: `safe` error (a 120 px line wider than 80 %), `contrast` error
1.85:1 (gray 0.25 on 0.06), `size` warn (cap 20 px, 1.9 %), `dwell` warn (10 frames). Contrast over
footage cannot be computed from colors: sample the rendered frame.

## 11. Onsets from Convert Audio to Keyframes (no transcript available)

Channel: bridge. The menu command runs with no dialog when the audio layer is selected and the comp
is open in the viewer.

```javascript
// channel: bridge
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), al = AEK.core.layer(c, ARGS.audioLayer), i;
var cmd = app.findMenuCommandId("Convert Audio to Keyframes");
if (!cmd) { return "command not found"; }
c.openInViewer();
for (i = 1; i <= c.numLayers; i++) { c.layer(i).selected = false; }
al.selected = true;
app.executeCommand(cmd);
var both = AEK.core.layer(c, "Audio Amplitude").property("ADBE Effect Parade").property("Both Channels").property(1);
var v = [], mx = 0, k, quiet = 0, onsets = [];
for (k = 1; k <= both.numKeys; k++) { v.push(both.keyValue(k)); if (v[k - 1] > mx) { mx = v[k - 1]; } }
// onset: first frame above 25 % of max after 4 or more frames under 10 %
for (k = 0; k < v.length; k++) { if (v[k] < 0.1 * mx) { quiet++; } else { if (v[k] > 0.25 * mx && (quiet >= 4 || !onsets.length)) { onsets.push(k); } quiet = 0; } }
return { keys: both.numKeys, onsetFrames: onsets };
```

Measured: command id 4218, a new layer "Audio Amplitude" with Left, Right and Both Channels sliders,
one key per frame (205 for 8.5 s). Onsets 0, 100, 132, 158, 182 against transcript phrases 0, 38,
75, 98, 130, 157, 180: 5 of 7 found, 0 to 2 frames late; pauses of about 0.23 s (5 frames) between
short phrases were missed. Use it to place phrases, not words; delete nothing: disable the "Audio
Amplitude" layer after reading it.

## 12. Frame check before judging a contact sheet

Channel: shell. In a 32 bpc project, `comp.saveFrameToPng` writes a 16-bit PNG with every value
divided by 10 (white reads about 10 %); at 8 and 16 bpc white reads 255. A new project inherits the
bit depth of the one open before it, so a dim frame usually means the project was 32 bpc.
`AEK.capture.frame` returns `bpc` and `pngScale` (0.1 or 1); build the sheet with
`ae.py sheet OUT.jpg frames... --gain 10` when `pngScale` is 0.1. Check the brightest pixel before
judging contrast or design.

```bash
ffmpeg -loglevel error -i frame.png -pix_fmt gray -f rawvideo - | python3 -c "import sys; b = sys.stdin.buffer.read(); print('max', max(b), 'px>200', sum(1 for x in b if x > 200))"
```

Check: `max` near the fill brightness (255 for white). If not, read `pngScale` and the project bit
depth before drawing any conclusion.
