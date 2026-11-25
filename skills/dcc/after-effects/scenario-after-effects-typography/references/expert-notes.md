# Expert notes: kinetic typography

Principles and judgment by expert. Source ids are YouTube video ids (see sources.md); times are
hh:mm:ss. [added] marks rules from the live tests of this skill, not from an expert.

## How a text animator thinks

- **The property holds the end state; the selector holds the motion.** Keyframes go on the range
  selector (Offset, or Start and End), never on the animator property. Jake Bartlett, NclmWZa4c_8
  00:01:42 and 00:02:48. Adobe's help agrees: "you don't need to set keyframes for the animator
  properties".
- **Animator values are relative offsets.** A character 100 % selected gets the full value, 50 %
  selected gets half. Build an unanimated "initial state" animator, then one animator per move with
  the opposite value. Joey Korenman, b1_p2qQf_Ts 00:09:44 and 00:19:02.
- **Stack single-purpose animators** with their selector keys a few frames apart, instead of one
  animator doing everything. Korenman, b1_p2qQf_Ts 00:05:13.
- **Name every animator for its job** ("in words pos opacity"), never "Animator 1": expressions and
  presets find animators by name. Stephan Zammit, c-Q06JnT6mE 00:01:31; Korenman 00:03:38.
- **Two settings make a reusable base animator:** Shape Ramp Up and Ease Low 100 %. Duplicate the
  selector, set Ramp Down, retime for the out. Bartlett, NclmWZa4c_8 00:04:34 to 00:08:02.
- **Offset runs -100 to 100 %,** so the range can sit entirely before or after the text: that is how
  a cascade enters and leaves. Bartlett, NclmWZa4c_8 00:04:00. [added] Measured: Ramp Up needs -100
  to 100; Square needs 0 to 100. Square from -100 starts with the text visible, hides it by 0, then
  reveals it.
- **Square gives one character at a time, no overlap; Ramp gives overlap.** With Ramp Down, Offset
  must end at 100 to finish. Korenman, b1_p2qQf_Ts 00:07:29 to 00:08:40.
- **Ease High and Ease Low.** Korenman reads Ease High as the ease into the final state and Ease Low
  as the ease out of the initial state; both at 100 misbehave, 50/50 works (b1_p2qQf_Ts 00:08:40 to
  00:11:21). Bartlett says either can mean in or out depending on the shape (Tjm3NxPYPqk 00:06:43).
  Deciding condition: when scripting, use Adobe's definition (High = fully to partially selected
  zone, Low = partially to unselected zone) and judge on frames.
- **Based On Words does nothing visible for scale or rotation** while Anchor Point Grouping is still
  Character: change both. Bartlett, NclmWZa4c_8 00:08:54. Grouping Alignment 0 %, -50 % for capitals
  and 0 %, -25 % for lowercase (Adobe help); Bartlett used 0, -44 %; Manuel does Motion about -40 %
  (R24oYxqk8C0 00:06:50).
- **Characters counts spaces,** which pauses the cascade between words: use Characters Excluding
  Spaces. Adobe help, Units and Based On.
- **Fix the anchor first** with an "anchor fix" animator; every later animator inherits it.
  Korenman, b1_p2qQf_Ts 00:14:39.

## Readability and choice of unit

- **Words or lines for sentences, characters for titles and logos.** Zammit animates by words for
  readability and keeps the sentence centered while it builds, so the eye does not chase it
  (c-Q06JnT6mE 00:04:42). Korenman's per-character default suits short titles.
- **Caption pacing for fast social content:** about 20 characters per caption, 1.2 s minimum, no
  gap, single line; pop scale 95, 105 (+3 frames), 100 (+2 frames). Ryan Connolly, ZCP2W_NTpLE
  00:00:14 and 00:01:21 (shown in Premiere Pro).
- **Video text** (Adobe help): horizontal strokes at least 3 px, a contrasting border over moving
  images, vertical scroll rates in multiples of the field rate for interlaced delivery.
- [added] At speech pace (about 3 words per second) half the words of a 27-word test voiceover were
  under 6 frames apart at 24 fps: a one-word-at-a-time swap would flash. Accumulate words inside a
  phrase layer and hold the phrase.

## Templates and retyping

- **Build for edited text.** The template must survive retyping: center through the Paragraph panel
  and align to the comp, or a shorter word sits off-center. Jordy, miiGiGtFuTU 00:00:43; Korenman
  00:12:59.
- **Over-travel** path margins far outside the canvas so longer text still enters and leaves
  cleanly. Jordy, miiGiGtFuTU 00:01:30 to 00:02:11.
- **`index` in a text-layer expression is the layer index,** so adding layers breaks index-based
  Start and End. Use a slider. Manuel does Motion, R24oYxqk8C0 00:11:29.
- **Pick the n-th word with one slider:** Based On Words, Units Index, Mode Subtract, Start
  `slider - 1`, End `slider`, Opacity 0. Zammit, c-Q06JnT6mE 00:06:54 to 00:12:30.
- **Presets:** when saving an animation preset, include changed More Options properties (Grouping
  Alignment) and exclude Source Text. Bartlett, NclmWZa4c_8 00:10:34.

## Selectors beyond the range selector

- **Wiggly selector in Intersect mode** stays inside the range selector; Min Amount 0 stops negative
  scale; Wiggles/Second 0 plus seed hold keys gives a stepped twitch. Korenman, b1_p2qQf_Ts 00:17:23
  to 00:21:55.
- **Expression selector for alternation:** `textIndex % 2 == 0 ? selectorValue : -selectorValue`;
  opacity then needs its own animator. Korenman, b1_p2qQf_Ts 00:33:50 to 00:38:48. `textIndex`,
  `textTotal`, `selectorValue` exist only in an expression selector (Adobe help).
- **Random font per letter:** keyframe Source Text styles one per second as a "font list" and pick
  one with `text.sourceText.getStyleAt(0, s)` under `seedRandom(index)` and `posterizeTime(4)`.
  Manuel does Motion, R24oYxqk8C0 00:07:50 to 00:09:36. Since 24.3 a script can style character
  ranges directly.

## Variable fonts (26.0 and later)

- **Axes have no stopwatch in the Character or Properties panel;** add them through Add Animator >
  Variable Font Axes and keyframe the animator value. Bartlett, Tjm3NxPYPqk 00:02:02.
- **The animator pushes from the base style:** set the base to the thin extreme or nothing visible
  happens. Bartlett, Tjm3NxPYPqk 00:04:10.
- **Wave through the text:** Shape Triangle, End about 25 %, Ease High and Low about 60, Offset
  looped over 2 s. Bartlett, Tjm3NxPYPqk 00:06:08 to 00:07:48.

## Per-character 3D

- **Put the anchor back in Z** (200 px), then rotate: letters orbit that anchor. Korenman,
  b1_p2qQf_Ts 00:25:38 to 00:27:51.
- Per-character 3D makes each character a 3D layer inside a collapsed precomp; converting back to 2D
  loses those values; Inter-Character Blending and Fill & Stroke options are unavailable (Adobe
  help).
- [added] Measured in 27.0: the same flip and an anchor-in-Z orbit render in Classic 3D
  (`ADBE Advanced 3d`) and Advanced 3D (`ADBE Calder`). Advanced 3D refuses the layer Motion Blur
  switch on the text layer.

## Retiming and accents

- **Keep a building sentence centered:** a second animator Based On Lines, Position only, keyed in
  from the edge and out the opposite way. Zammit, c-Q06JnT6mE 00:04:42 to 00:06:18.
- **Emphasis after the sentence lands:** Gradient Ramp on the special word, Blend With Original
  keyed 100 % to 0, Easy Ease. Zammit, c-Q06JnT6mE 00:16:03 to 00:17:10.
- **Random order that holds:** Randomize Order with a non-zero Random Seed keeps the same order on a
  duplicated animator group; seed 0 derives it from the group (Adobe help, Range selector
  properties).
- **Motion blur on moving text** smooths edges and motion (Adobe help, animating text).

## Title finishing (film-print look)

- **Break the vector edge:** Scatter 3.5, Fast Box Blur 0.2, Roughen Edges Scale 10, Border 0.5,
  Sharpness 2. Eric Demeusy, ZP_eglqgsYE 00:10:55.
- **Grain inside the letters** (texture at 40 % scale, CC RepeTile, Multiply, matted by the letter)
  and over the frame (scanned grain at Overlay). Demeusy, ZP_eglqgsYE 00:12:01 and 00:46:51.
- **Two copies of every glowing letter:** a grain copy and a heavily feathered "hot" copy in Add at
  45 to 75 %; glows Threshold 95 Radius 25 and Threshold 85 Radius 250 on the hot copy. Demeusy,
  ZP_eglqgsYE 00:16:30 and 00:19:12.
- **Film flaws:** Exposure `wiggle(24, 0.2)`, dust from Fractal Noise with Evolution `time * 2000`,
  hue wobble `wiggle(24, 100)` at Saturation 25 %, Screen 50 %. Demeusy, ZP_eglqgsYE 00:46:16 to
  00:51:48.
- **Stencil Alpha on the text** over stacked growth comps reveals a logo; a speed ramp (fast then
  slow) on growth reads organic. Ben Marriott, BEleJjwfkcc 00:01:48 and 00:03:26.
- **Retiming a reveal:** add a middle key at Offset 50 % and flatten its handle for a pause. Zammit,
  c-Q06JnT6mE 00:14:42.

## Where generated assets enter

Textures inside letters, grain, dust and glitch overlays, style frames for a title look, and the
voiceover itself can come from the Scenario MCP. Route the generation to
scenario-after-effects-generation; this skill takes the file once it lands.
