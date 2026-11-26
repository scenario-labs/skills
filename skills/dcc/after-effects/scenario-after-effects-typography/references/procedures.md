# Procedures: kinetic typography by script

Every job runs through `ae.py run job.jsx --lib <this skill>/scripts/typography.jsx`
(scenario-after-effects-expert toolkit). Frame counts are at 24 fps unless a case says otherwise; at
30 fps multiply by 1.25 and round. Jobs are ES3 function bodies: `ARGS` holds the `--args` JSON,
`return` sends the result. In a user's session, never call `AEK.core.fresh()` (it closes the
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

### 1b. Picking a face and a pairing when the brief names none

The brief's or the brand's face always comes first. Without one, pick by role from what the render
machine has, in this order:

1. Installed on the machine that renders (`getFontsByPostScriptName`), with glyphs for every
   language of the job (`hasGlyphsFor`).
2. One family in two weights before two families: a heavy weight for the title, a medium one for the
   supporting line. The pair then shares proportions and x-height.
3. Several weights in the family, so a later accent or a third level needs no second family.
4. The cross-platform fallback (Arial) only when nothing above is installed. Report it: it is the
   last resort.

| Role                           | macOS (PostScript names)                               | Windows (PostScript names)         | Fallback on both                |
| ------------------------------ | ------------------------------------------------------ | ---------------------------------- | ------------------------------- |
| display (titles)               | AvenirNext-Bold, HelveticaNeue-Bold, Futura-Bold       | SegoeUI-Bold                       | Arial-BoldMT                    |
| text (supporting lines)        | AvenirNext-Medium, HelveticaNeue-Medium, Futura-Medium | SegoeUI-Semibold                   | ArialMT                         |
| condensed (long words in 9:16) | AvenirNextCondensed-Bold, HelveticaNeue-CondensedBold  | ArialNarrow-Bold (with Office)     | Arial-BoldMT                    |
| serif (editorial contrast)     | Georgia-Bold, Charter-Bold                             | Georgia-Bold, Cambria-Bold         | TimesNewRomanPS-BoldMT          |
| Japanese and Chinese           | HiraginoSans-W6                                        | YuGothic-Bold, MicrosoftYaHei-Bold | NotoSansCJKjp-Bold if installed |

`AEX.type.pickFont(role, {text, candidates})` returns the first installed candidate that covers
`text`, with `fallback` true when only the last one was found. `AEX.type.fontPair({text, pairs})`
returns the first one-family pair (Avenir Next, Helvetica Neue, Futura, Segoe UI, then Arial).

```javascript
// channel: bridge | handoff
// checked: live 27.0
var pair = AEX.type.fontPair({ text: ARGS.text || "äöüßé" });
var cjk = AEX.type.pickFont("cjk", { text: "日本語" });
return { pair: pair, cjk: cjk, condensed: AEX.type.pickFont("condensed").font };
```

Measured on the test Mac: pair AvenirNext-Bold and AvenirNext-Medium (rank 1); `cjk`
HiraginoSans-W6; condensed AvenirNextCondensed-Bold; serif Georgia-Bold. No pair covers Japanese:
`fontPair({text: "日本語"})` returns nulls, so Japanese lines take the `cjk` role. Segoe UI, Inter,
Montserrat and SF Pro were absent there. The Windows names are the fonts' PostScript names; check
them on the Windows render machine with the same call. Size the pair 3:1 or more (title to
supporting line, procedure 13).

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
`silence_end`). `silence_agrees` reads null when nothing was compared (one phrase, or no
`silence_end` in the log). Two words on one first frame are listed in `checks.same_frame` and the
script exits 1: merge them in the transcript. Measured on a synthetic 8.5 s voiceover: 27 words, 7
phrases, onsets 0 to 1.1 frames before the silence end. `checks.short` lists words held fewer than 6
frames before the next word: 15 of 27 at speech pace, which is why words accumulate inside a phrase
instead of replacing each other.

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
AEK.text.animator(t, { name: "track", properties: { tracking: 300, opacity: 0 }, amount: 100 });
AEX.type.trackingFit(t, "track", c, { margin: 0.05, t: 0 }); // 300 makes a 3,622 px line in a 1920 comp; fitted: 110
var amt = function () { return AEX.type.amount(t, "track"); };
AEK.motion.key(amt(), 0, 100); AEK.motion.key(amt(), 20 / 24, 0);
AEK.motion.bezier(amt(), 1, 2, [0.16, 1, 0.3, 1]);
return AEK.capture.spread(c, 6, ARGS.out, "looks");
```

The range selector Amount is not a child of the selector: it is `ADBE Text Range Advanced` >
`ADBE Text Selector Max Amount`. `AEK.text.animator(..., {amount})` sets it and returns `amount`;
that handle goes stale after later `addProperty` calls, so
`AEX.type.amount(layer, animatorName, selectorIndex)` fetches it fresh. Its range is -100 to 100;
`setValue(-150)` throws "Value -150 out of range -100 to 100".

Stack order for a look that people retype (Korenman, b1_p2qQf_Ts 00:05:13, 00:09:44, 00:14:39;
Zammit, c-Q06JnT6mE):

- An "Anchor Point Fix" animator first; every later animator inherits its anchor.
- An unanimated "initial state" animator, then one animator per move holding the opposite value,
  keys 2 to 4 frames apart.
- To keep a sentence centered while words build, a second animator Based On Lines, Position only
  (00:04:42).
- For a pause, a middle Offset key at 50 % with a flat handle (00:14:42).

Check with `sourceRectAtTime` (it includes animator offsets and tracking): rise top moves 9 to -71
px over 20 frames; square top stays at 9 until a character is released; with the unfitted 300,
tracking width 3,622 px at frame 0, 1,145 at frame 5, 622 at rest (expo-out finishes 83 % of the
move in a quarter of the time); word pop width 773 to 921 px. On the sheet: settled lines identical
to the static text.

Tracking-in width. Animator Tracking (`ADBE Text Tracking Amount`) adds 1 px per unit to every gap
between characters, at any font size. Measured on "TRACKING IN" (11 characters, 10 gaps): 622, 1,622
and 3,622 px at Tracking 0, 100 and 300 at 96 px; 1,425, 2,425 and 4,425 at 220 px. So the start
line is `rest width + (characters - 1) x Tracking` wide.
`AEX.type.trackingFit(layer, animatorName, comp, {margin: 0.05, t})` lowers an unkeyed Tracking
until the line at time `t` fits the frame minus the margin. Measured: 300 became 110 for the 96 px
line (width 1,722 px); 180 became 31 for "LAUNCH DAY" at 220 px, a title that already filled 73 % of
the width. A tracking-in needs a line well inside the frame; frames 0 to 8 stayed in frame after the
fit.

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

Accents (procedure stage 6): accent after the line lands with Gradient Ramp on the word, Blend With
Original keyed 100 to 0 (Zammit 00:16:03). Randomize Order needs a non-zero Random Seed to keep its
order across duplicates (Adobe help).

## 5b. Per-character overshoot (expression selector below 0)

Channel: bridge. A range selector cannot give a staggered overshoot. Its Amount accepts -100 to 100
and a negative Amount applies the animator values inverted, but Amount scales every selected
character at once. An Offset sweep selects each character from 0 to 100 % and never past it. An
expression selector can: its Amount is computed per character, and a value below 0 inverts the
offset for that character only. It clamps at -100 like the range selector.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.build.comp("overshoot", { width: 1920, height: 1080, fps: 30, duration: 3 });
var w = AEK.text.add(c, "TONDA", { name: "word", font: "Helvetica-Bold", size: 260, fill: [1, 1, 1], justify: "center", position: [960, 600] });
AEX.type.grouping(w, "character", [0, -50]);
// frames from the layer in point: unit k starts at start + (k - 1) * stagger, peaks at + peak, rests at + settle
AEX.type.overshoot(w, { properties: { position: [0, 200], opacity: 0 }, start: 2, stagger: 3, peak: 10, settle: 20, overshoot: 8 });
return AEK.capture.frames(c, [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 1], ARGS.out, "os");
```

```javascript
// expression (JavaScript engine): Text > Animator "overshoot" > Expression Selector > Amount (what AEX.type.overshoot writes)
// checked: live 27.0
var f = thisComp.frameDuration, t0 = inPoint + (2 + (textIndex - 1) * 3) * f;
var tp = t0 + 10 * f, t1 = t0 + 20 * f, o = 8 / 100;
var e = time < tp ? easeOut(time, t0, tp, 0, 1 + o) : ease(time, tp, t1, 1 + o, 1);
100 * (1 - e);
```

Measured at 30 fps with a one-letter layer (`sourceRectAtTime` follows expression selectors):
Position offset 120 px, `overshoot: 8`: the letter passed its rest by 9.6 px (8.0 %) on frame 10 and
settled on frame 17. On "TONDA" (offset 200 px) the highest letter passed by 16 px, the set 8 %.
Fixed expression values -10 and -100 moved a letter 10 and 100 px past rest; -150 gave the same as
-100. Opacity offset 0 cannot pass 100 %. Position, Scale and Rotation pass.

Order and distance. `order: "center"` starts the middle letter first and works outward; `"right"`
starts from the last letter. `vary: 0.5` gives the last letter to move half the offset of the first
(linear in between), so the letters stop sharing one distance and one landing. A one-letter probe
with `order: "center", vary: 0.5` still passed rest by 16 px of 200 (8 %) and settled by frame 20 at
24 fps; expressions clean on "TONDA".

For an overshoot of the whole line at once, a range selector is enough: key Amount 100, -8, 0
(frames 0, 10, 18) with `AEX.type.amount`. Measured: the line rose 12 px past rest with a 150 px
offset (8 %).

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

Inter-Character Blending and Fill & Stroke options are unavailable on per-character 3D layers (Adobe
help).

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
`app.project.replaceFont` is not undoable. Recheck widths after a swap: Georgia to Avenir Next at
the same size changed three lines by -7.4 %, -2.9 % and +1.7 %.

## 8. Fitting three languages, or three formats, in title safe

Channel: bridge. Order of remedies: rebreak at the designed size, then shrink to no less than 80 %,
then scale-to-fit. The same order reflows one title across 16:9, 9:16 and 1:1: safe width is 80 % of
each comp width.

Measure safe areas of 2D text with `AEK.text.measure` and `AEK.text.inFrame`: they walk the parent
chain (anchor, scale, Z rotation, position). For 3D text, or a 3D parent, use
`AEX.type.compBounds(layer, t)`: it reads the four corners of `sourceRectAtTime` through `toComp` (a
temporary Point Control), so X and Y rotation, orientation and the camera count.
`AEX.type.inFrame(layer, comp, margin, t)` calls the kit for 2D chains and `compBounds` otherwise,
and reports `via`.

Measured against the rendered pixel box (ImageMagick trim of the saved frame):

- 2D text under a null at 60 % scale and 30 degrees Z: kit and `compBounds` both [1026, 621, 1701,
  743], equal to the pixels.
- 3D text turned 60 degrees in Y: pixels 343 px wide from x 809; `compBounds` [809, 407, 1152, 544];
  kit [626, 421, 1301, 543], the unturned layer.
- 3D text turned -50 degrees in X under a 3D null moved 400 px in Z: pixels 587 x 66 from (530,
  441); `compBounds` [530, 442, 1118, 507]; kit off by 64 px and 56 px in height.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.build.comp("fit", { width: 1920, height: 1080, fps: 24, duration: 1 });
var maxW = c.width * 0.8, out = {}, k;
var L = { en: "Make every frame readable", de: "Mach jedes Einzelbild lesbar und verständlich", fi: "Tee jokaisesta kuvaruudusta luettava" };
for (k in L) {
    if (!Object.prototype.hasOwnProperty.call(L, k)) { continue; }
    var l = AEK.text.add(c, L[k], { name: k, font: "Helvetica-Bold", size: 110, fill: [1, 1, 1], justify: "center", position: [960, 540] });
    var row = { width: Math.round(AEK.text.measure(l, 0).comp.width) };
    var s1 = l.duplicate(); row.shrink = AEK.text.fit(s1, maxW, { minSize: 60 }); s1.enabled = false;
    row.balanced = AEX.type.balance(l, maxW, 3); // edits l in place: point text with \r line breaks
    row.safe = AEX.type.inFrame(l, c, 0.1, 0).ok;
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
if (time < outPoint - b) { easeOut(time, inPoint, inPoint + a, -100, 100); }
else { easeIn(time, outPoint - b, outPoint, 100, -100); }
```

The in starts fast and settles (`easeOut`); the out accelerates to the last frame (`easeIn`). Two
exit orders, set with `exit`:

- `"reverse"` (default): the same Ramp Up swept back, so the last character leaves first.
- `"forward"`: the first animator holds Offset at 100 after the in, and a second animator
  `<name> out` (Ramp Down, Ease Low 100, same properties or `outProperties`) sweeps Offset -100 to
  100 with `easeIn`. Ramp Down at -100 selects nothing; moving right, it selects the first character
  first.

```javascript
// expression (JavaScript engine): Text > Animator "in-out out" > Range Selector 1 > Offset (Ramp Down, Ease Low 100)
// checked: live 27.0
var b = 12 * thisComp.frameDuration;
easeIn(time, outPoint - b, outPoint, -100, 100);
```

Measured at 24 fps on a layer 0 to 48 frames, `inFrames` and `outFrames` 12: in Offset -100, 25, 100
at in, in + 6, in + 12; out Offset -100, -25, 82 at out - 13, out - 6, out - 1. After sliding the
layer 12 frames later and trimming it, the probes read the same values. Bright pixels on frames 39
to 45, left half against right half (percent of the half): `"reverse"` 9.0 / 8.0, 8.8 / 5.9, 6.9 /
0.8 (right side leaves first); `"forward"` 8.9 / 8.0, 6.1 / 7.7, 0.3 / 5.6 (left side leaves first).
Save the result as an animation preset only through the GUI (gui-paths.md); by script, rebuild it
with `AEX.type.inOut`.

## 10. Readability report

Channel: bridge. The report changes nothing it leaves behind, but it is not read-only while it runs:
it adds and removes a temporary "H" text layer per text layer (cap height), a temporary Point
Control (3D bounds) and a temporary duplicate per layer (settled dwell). In a person's session run
it inside `--undo` so the history shows one step.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
var rep = AEX.type.readability(c, { bg: ARGS.bg, minFrames: 18, minCapRatio: 0.035, safe: 0.1, minContrast: 4.5 });
return rep;
```

Each row: words, frames on screen, `settled` frames with `settledFrom` and `settledTo`, font, size,
cap height in px (from a temporary "H" in the same font, parented to the layer with a jump and read
through `toComp` at mid-life, so the layer's and its parents' scales count) and as a ratio of the
frame's short side (1080 in 16:9, 9:16 and 1:1 alike; a 46 px cap reads 4.2 % in all three), the
lowest WCAG contrast and `runs` (contrast of every color run against `bg`), `inSafe` at mid-life,
tracking, leading ratio.

Contrast per run. `TextDocument.fillColor` is the first character only, so a colored word escapes a
check that reads it. `AEX.type.colorRuns(doc)` reads `characterRange(i, i + 1)` per character and
groups runs of one fill. Measured on "Sound, anywhere." with "anywhere." in a dark red: the document
fill read 15.87:1 (cream on ink), the runs read 15.87:1 and 1.88:1, and the report raised a
`contrast` error on that run. Under 3:1 is an error, 3:1 to 4.5:1 a warning.

Settled dwell. `AEX.type.settled(layer, comp, {restFrame})` counts the longest run of frames where
the text is at rest and the layer is at 100 % Opacity. It probes a temporary duplicate: each
animator gets a Position of [0, 1000 x its index], so any selector still selecting a character
changes `sourceRectAtTime`. Rest is the state at `restFrame`, or else the most frequent state at
full opacity among frames where no animator selects a character. A state an animator hides (a reveal
holding the text at 0 % for 60 frames) is then never rest, however long it lasts. When an animator
selects text on every frame, rest falls back to the most frequent state at full opacity; `settledBy`
in the row reads `frequency` then. Parent motion (a push-in null) is not counted against rest. The
`dwell` rule needs at least `minFrames` settled frames and `minPerWord` (6) per word. A word-synced
phrase layer (more than one marker) is read while it builds, so its dwell stays its time on screen.
Measured on a title with a staggered overshoot in (settles on frame 35) and a per-character exit
from frame 94: 116 frames on screen, 60 settled (35 to 94), and the same 60 under a null pushing 100
to 104 %. A tagline in at 28 with a 14-frame in and a 12-frame out, out at 110: 82 on screen, 63
settled (39 to 101). `inSafe` comes from `AEX.type.inFrame`, so parented layers are measured where
they render. Measured on the synced piece: 7 phrases, 22 to 38 frames each, 6.4 to 8.3 frames per
word, cap 79 px (7.3 % of 1080), contrast 19.07:1, all in safe. Built-to-fail layers raised: `safe`
error (a 120 px line wider than 80 %), `contrast` error 1.85:1 (gray 0.25 on 0.06), `size` warn (cap
20 px, 1.9 %), `dwell` warn (10 frames). Contrast over footage cannot be computed from colors:
sample the rendered frame.

Over footage. `AEX.type.readability(c, {sample: true})` (or
`{sample: {frames: [..], grid: [4, 2]}}`) replaces `bg` with what lies under each text box. It
switches every text layer off, nests the comp in a temporary comp, and reads the mean color of each
grid cell of the box with `sampleImage()` at 5 frames across the layer's life (or the frames given).
Each run's contrast is the worst against every cell. The row's `backdrop` gives the darkest and
lightest cell with its frame. Text layers are switched back on, and the temporary comp, its null and
that null's solid are removed. `sampleImage()` reads back from a script only after the comp has
rendered at that time, so the helper saves one frame per sampled time to the temp folder first;
without that render the value read 0, 0, 0, 0. Measured on a 5-second 1920 x 1080 render of a
product turning on a dark floor, 3 labels, 40 cells each: a cream label over the product read
17.39:1 against a passed black and 1.6:1 sampled (darkest cell 156, 63, 51; error raised); a cream
label over the dark backdrop read 16.1:1 sampled; ink text read 1.03:1. In a probe, a sampled mean
matched the mean of the same 400 x 400 crop of the rendered PNG within 0.002 per channel. 7.7 s for
the 3 layers; project item count unchanged.

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

## 13. Layout check: an idea, not a default stack

Channel: bridge. `AEX.type.layout(comp, {t, hold: [f0, f1]})` returns each text layer's comp bounds
at `t` (seconds) and three warnings:

- `stack`: every text layer centered on the vertical axis (within 2 % of the width). State the idea,
  or align to a grid line (flush left on the safe line), cut one word in scale, or crop a word at
  the frame edge.
- `scale`: largest to smallest type size under 3:1. A title and a tagline at the same weight and a
  2:1 ratio read as one block.
- `hold`: no layer or parent moves between the hold frames. Add a secondary action that keeps the
  letters settled: a parent null pushing 2 to 4 % over the hold.

```javascript
// channel: bridge | handoff
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp);
return AEX.type.layout(c, { t: 60 / c.frameRate, hold: [40, 90] });
```

Measured on a reader's title card (TONDA at 250 px over "Sound, anywhere." at 84 px, both centered):
`stack` and `scale` (2.98:1) raised; `hold` not raised because a push-in null scaled 100 to 104 %,
reported in `moving`. Motion variety is judged on the sheet: if every unit rises the same distance
on the same curve, use `order` and `vary` on `AEX.type.overshoot` (procedure 5b) or give the
secondary line a different move.
