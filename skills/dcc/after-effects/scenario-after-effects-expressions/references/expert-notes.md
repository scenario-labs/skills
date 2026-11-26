# Expert notes: expressions

Principles and judgment by expert, with source and timestamp (`hh:mm:ss`). Lines marked [added] are
this skill's own reading. Lines marked [live 27.0] were measured in After Effects 27.0 and outrank
the video when they differ. Full URLs are in `sources.md`.

## Jake Bartlett: sourceRectAtTime (CVliDoNgoCg, 2018)

- `sourceRectAtTime()` is the only way to read the real bounds of a text layer: width, height, top,
  left [00:00:48].
- Left and top matter because the text anchor sits on the baseline origin, not on the box corner;
  the box position is `[w/2 + left, h/2 + top]` [00:07:50 to 00:10:06].
- Parent the box to the text, or compute scale yourself: the rect ignores layer scale [00:07:50],
  [00:31:27]. [live 27.0] A parented box also scales its padding: 32 px became 48 px at 150 %.
  Divide the padding by the text scale to keep it constant.
- Pass a fixed time when the text animates: the current time makes the box follow the animator
  [00:13:18]. Use the out point rather than a literal second [00:14:34]; when the text animates off,
  use the midpoint of in and out, with parentheses [00:20:22]. [added] The midpoint is
  `inPoint + (outPoint - inPoint) / 2`; the video's `(end - start) / 2` is a duration and only works
  for a layer starting at 0.
- Width, height, left AND top must use the same sample time or the box jumps [00:13:25].
- Prefer Offset Paths for a uniform margin, one amount and no code edits [00:10:39]. [added] Use two
  sliders when the lower third needs different horizontal and vertical padding.
- With Offset Paths the box grows outward from the ink, so set the group Anchor Point and Position
  to `[left - o, top - o]` (o the Offset Paths Amount) for a Scale X build that starts at the
  visible edge [00:16:54 to 00:18:03]. [live 27.0] Margins 24 on all sides at Amount 24; at group
  Scale X 50 % the left margin stayed 24 (13.97 with the anchor left at [0, 0]).
- Extents: `true` includes the stroke for shape layers; for text the video says it grows to the
  canvas [00:29:14 to 00:30:20]. [live 27.0] On a text layer with a 6 px stroke, `true` and `false`
  returned the same rect.
- Round only readouts; keep geometry as floats [00:28:06].

## Jake Bartlett: spaces and toComp (gSq19gpWwSU, 2021)

- Raster layers feed effect point controls in layer space; shape, text and continuously rasterized
  layers feed them in comp space. That is why Gradient Ramp points do not follow a moved text layer
  [00:03:08].
- `thisLayer.toComp([0,0,0]) + value` sticks a point to the layer and keeps it draggable [00:11:13].
- `transform.position` is parent space as soon as a parent exists; `toComp` survives parenting
  [00:17:17].
- Decide by whether the layer will be scaled or rotated: offsets break on scale, parented nulls
  survive it [00:12:52], [00:15:38].

## Evan Abrams: valueAtTime (xFT6W9uSwbY, 2019)

- `valueAtTime` reads any property at an absolute time in seconds, including a precomp's Time Remap
  [00:01:12], [00:11:21].
- A delay is `time - something`, the something from one slider so every follower changes together
  [00:08:34].
- Convert frames with `thisComp.frameDuration` [00:06:08]. [live 27.0] A 3-frame delay stayed 3, 6,
  9, 12, 15 frames at 24, 30 and 60 fps; a 0.1 s delay gave 2, 5, 7, 10, 12 frames at 24 fps.
- Chain-follow (`index - 1`) accumulates lag by layer order; all-follow-leader sets each delay
  directly [00:08:34]. [added] Point every follower at the one leader: a chain re-evaluates every
  link per frame.
- `linear(slider, 0, 100, 0, 4)` into `valueAtTime` turns a keyed path into a percent-along-path
  control [00:10:14].

## Nol Honig and Zack Lovatt: rigs (VdaGqq4I0qM, 2021)

- A rig is one guide null named Controller carrying Expression Controls that drive many layers
  [00:00:24].
- Name values as variables, then move hidden numbers onto sliders so the Effect Controls panel shows
  every constant [00:05:16], [00:19:14], [00:20:51].
- `linear()` is the translator between units, for example a slider of -200 to 200 to x from 550 to
  1370 [00:32:15].
- A 2D property cannot take a single number: return `[v, v]` [00:26:16].
- Checkbox is 1 or 0: test `> 0` [00:09:00].
- Learn the Expression Language menu and the post-expression graph before searching the web
  [00:15:59].
- Deciding condition against the ACE video: literals inside the code are fine for a one-off; a
  reusable rig exposes every number.

## Dan Ebberts, via ACE: inertia and bounce (qXPzt3nNJRI, 2018)

- Inertial Bounce defaults amp 0.05, freq 4, decay 8; effect window 1 s after the last key
  [00:01:18]. Smaller decay lasts longer; freq is bounces per second [00:01:52].
- Bounce Back defaults e 0.7 (elasticity), g 5000 (gravity), nMax 9 [00:04:04]. g 2000 floats, 7000
  lands like a rock [00:05:06].
- The bounce energy comes from the velocity at the last key, so key spacing sets the overshoot
  [added, from the code]. Bring keys closer when the bounce looks late [00:06:17].
- Pair them: Bounce Back on the property that hits (Position), Inertial Bounce on the reaction
  (Scale) [00:05:42].
- [live 27.0] The verbatim 2018 code with implicit globals runs unchanged in the JavaScript engine
  and gives the same numbers as a `const`/`let` rewrite and a 26.0 `previousKey` rewrite: overshoot
  10.9 % at 24 fps, 10.2 % at 60 fps.

## Sergey Prokopenko: JavaScript engine changes (GUSJhbPwpBE, 2018)

- The JavaScript engine is stricter: one-line if/else without braces, a function called before its
  declaration, `this.name`, `sourceText[i]` without `.value`, and `reflect` break [00:06:19 to
  00:12:24].
- Dismissing the error banner hides future errors app-wide until Show Warning Banner is turned back
  on in Preferences [00:02:35].
- Layer > Switches > Disable Expressions works on many selected layers at once [00:00:49].

## Nic, Kyle Hamrick and John Colombo: text style expressions (yG8UbiKKeYw, 2025)

- Ranges are (value, startIndex, length); without length the range runs to the end [00:10:42].
- Spaces count as characters; so do manual line breaks, while text animators ignore line breaks
  [00:11:12], [00:29:29].
- Split words on `/\s/`, not `" "`, so breaks and tabs count [00:40:34].
- Guard slider-driven picks: below 1 return plain text, clamp to the word count, or
  `undefined.length` kills the expression [00:44:01].
- Wrap slider reads in `Math.round` or `Math.floor`: style ranges snap, animators interpolate
  [00:34:18].
- Dropdown menus return 1-based numbers; arrays are 0-based: `arr[menu - 1]`; labels never reach the
  expression [00:06:56], [00:18:31].
- `setJustification` must be the last call (as of February 2025) [00:19:34]. [live 27.0] Before or
  after `setText`, the result was centered in both orders.
- Never put an expression-driven Source Text into Essential Graphics; use an INPUT TEXT layer and
  `.setText(...)` [00:20:36].
- Text animators run after style expressions: an animator fill overrides the expression fill on the
  same range [00:26:08]. [live 27.0] A red animator Fill Color on 0 to 50 % turned the first half
  red over a blue `setFillColor`; the rest kept the blue.
- Chained style methods are the slowest text route; panel settings are fastest [00:15:17].
- Read a font's exact name from the Expression Language menu Text > Font..., never guess it
  [00:05:56].

## mamoworld: JSON-driven text (i8ag-Z8w4Bk, 2018)

- Keep content in a JSON file imported as footage so many variants render without opening the
  project [00:00:20].
- Texts not updating: save the file, then Reload Footage [00:02:37]. [live 27.0] A rewritten file
  showed the old value until `mainSource.reload()`.

## Typography cluster: stepped randomness

- Manuel does Motion: `posterizeTime(4); seedRandom(index); wiggle(3, 15)` gives a stepped,
  stop-motion jitter at 24 fps [R24oYxqk8C0 00:05:08 to 00:05:57].
- Eric Demeusy: film flaws are wiggles at the frame rate, `wiggle(24, 0.2)` on exposure, `time*2000`
  on Fractal Noise evolution [ZP_eglqgsYE 00:46:16].

## Docs (docsforadobe expression reference)

- `loopOut` types: cycle (default), pingpong, offset, continue; `continue` takes no arguments; loops
  do not work on Source Text or path properties [doc property].
- `previousKey(time)` and `nextKey(time)` arrived in 26.0, JavaScript engine only [doc property].
- Comp and world space are identical for 2D layers; for 3D layers comp space depends on the active
  camera [doc layer-space-transforms].
- Paragraph setters take no index and must come after `setText()` when both are used [doc
  text-style].
