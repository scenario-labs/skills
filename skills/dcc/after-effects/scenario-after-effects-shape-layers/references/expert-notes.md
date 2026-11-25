# Expert notes: shape layers and vector animation

Principles and judgment by expert, with source and timestamp. Video URLs are in
[sources.md](sources.md). Items marked [added] are this skill's own additions; items marked [live]
were measured in After Effects 27.0.

## Structure: one layer, groups as layers inside it

- One shape layer can hold a whole character or icon: each group carries its own Transform and blend
  mode, so a group is "a layer within a layer" (Alex Deaton, heYi6xLWvB0 00:02:37; Adobe shape
  overview).
- The first group in Contents draws on top. A full-size background group added first hides
  everything added after it [live].
- Inside a group, path operations run top to bottom before any paint; paint operations stack bottom
  to top (Adobe shape overview). Practical order: paths, then operators, then Stroke, then Fill
  [live].
- Operators act on every path above them in the same group, nothing else. Place each operator at the
  level that reaches the paths it must change (Sarah Wade, rtt-gGDxrZ4 00:15:36; Manuel, 748l7DIU4bQ
  00:01:07).
- Put Stroke, Taper, Wave and Trim Paths at Contents level after the groups so every group shares
  them; keep them inside a group when duplicates need their own width (Sarah Wade, rtt-gGDxrZ4
  00:16:44, 00:21:03; Evan Abrams, wOZwzLgJw9o).

## Parametric first, Bezier only when the path itself must move

- Rectangle, Ellipse and Polystar keep numeric Size, Roundness, Points: animate those and you need
  no path keys. Square to circle is one Roundness key pair (Megan Friesth, TVepzaUT6Dw 00:01:23).
- Size is not Scale: animating Size keeps the stroke weight, Scale thickens it (Megan Friesth,
  TVepzaUT6Dw 00:00:49).
- Convert to Bezier Path is one way: there is no route back to parametric (Megan Friesth,
  TVepzaUT6Dw 00:04:05). Duplicate the group before converting [added].
- Design files from Figma arrive parametric (rectangle Size, Roundness), Illustrator art arrives as
  expanded Bezier paths (Jake Bartlett, I6QlicggqtY 00:05:31).

## Trim Paths is a motion engine

- Draw-on: key End 0 to 100, offset Start keys behind it so they do not cancel, ease both in the
  Speed Graph (Manuel, 748l7DIU4bQ 00:00:30).
- A traveling dot: End = Start + 0.1 with a Round cap and a wide stroke (120 px in the video)
  (Manuel, 748l7DIU4bQ 00:03:03 to 00:03:36).
- Trim Multiple Shapes matters only when several paths sit above the Trim: Simultaneously trims each
  path by the same percent, Individually treats them as one sequence, top path first (Adobe
  operations doc; Manuel, 748l7DIU4bQ 00:01:07). Reorder groups to set who draws first.
- Trim above a Repeater trims the source before copying (all copies identical). Trim below a
  Repeater with Individually draws the copies one after another [live; resolves the conflict between
  speech and frame in 748l7DIU4bQ 00:02:51].
- A line that chases a ball: key End to the ball, copy End values into Start for the exit, and check
  the gap at every pause frame by frame (Abhishek Dubey, 7LW5mRTvNcY 00:11:12, 00:13:22).
- At End 0 with a Round cap nothing renders in 27.0: no leftover dot [live].

## Repeater

- 360 / Copies on Rotation gives a closed ring; zero the Repeater Position first or the ring spirals
  (Evan Abrams, wOZwzLgJw9o 00:05:01, 00:06:55).
- Copy n receives the Repeater transform n times: Scale 85 % makes copy 9 0.85^9 = 23 % (Evan
  Abrams, 00:04:28; Adobe operations doc; [live]).
- Arrive and leave on different properties (Size in, Scale out) so one curve serves both directions
  (Evan Abrams, 00:09:40).
- One set of keys can drive a duplicate feature: Copies 2, Position offset (Alex Deaton, heYi6xLWvB0
  00:08:06).
- Repeater listed above the Fill: the copies are filled as one compound (one gradient across all).
  Repeater below the Fill: each copy carries its own fill (Adobe operations doc; [live]).
- Wiggle Transform above the Repeater moves every copy the same; below, each copy moves on its own
  (Adobe operations doc).

## Merge Paths and the single-layer matte

- Merge Paths removes its inputs from rendering and needs a Fill or Stroke after it (Adobe
  operations doc).
- Merge (1) and Add (2) are two modes. Merge makes one compound path whose holes follow the Fill
  Rule; Add makes one union outline with no holes. With Non-Zero fill they render the same; with
  Even-Odd, Merge cuts overlaps and nested paths (Adobe operations doc; [live]).
- Mask-through-shape in one layer: duplicate the main path into the design group, link it by
  expression, then Merge Paths Intersect (Alex Deaton, heYi6xLWvB0 00:02:37 to 00:04:15).
- Intersect clips fills only: a stroke after the Merge strokes the merged outline, it is not
  clipped. Draw strokes as filled outlines inside a clip (Alex Deaton, 00:18:50; [live]).
- A Repeater inside an Intersect group needs its own Merge Paths (Add) inside the sub-group so the
  copies merge before the clip (Alex Deaton, 00:13:47; [live]).
- Layer effects (blur) apply to the whole layer, mask and design together: use a separate layer when
  one element needs an effect (Alex Deaton, 00:21:00).
- Zig Zag: odd Ridges per segment give a wavering stripe, even values align peaks (Alex Deaton,
  00:11:27).

## Taper and Wave

- Taper and Wave are native Stroke groups: a tapered, waving stroke from one path with no path keys
  (Sarah Wade, rtt-gGDxrZ4 00:01:40, 00:07:28).
- Values from the fern: Taper Start Length 64, End Length 36, Start Width 25, End Width 0, Start
  Ease 9, End Ease 59; Wave Amount 31, Wavelength 186, Phase `time * -100` (Sarah Wade, rtt-gGDxrZ4
  frame at 00:07:28).
- Lengths may meet (64 + 36 = 100); a gap between them leaves a lump at full width (Sarah Wade,
  00:03:39, 00:06:22).
- Reverse Path Direction flips taper and wave direction; drop the minus sign in the Phase expression
  to keep the wave traveling outward (Sarah Wade, 00:12:22).
- An expression phase never loops cleanly; key Phase 0 to N and back when the loop must close (Sarah
  Wade, 00:14:00).
- The Width fields default to 0 %: set a Length alone and the end becomes a full point [live].

## Morphing

- Hide a hard morph inside a cut at peak speed, with anticipation before and overshoot after (Ben
  Marriott, 3EGuLX6PsQ4 00:03:21).
- Separate Position dimensions before easing a morph move so the graph shows one curve per axis (Ben
  Marriott, 00:01:02).
- In 27.0 a path key pair with different vertex counts still morphs: After Effects adds the missing
  vertices itself [live]. The first-vertex mapping and the path direction decide whether the shape
  collapses through its center [live].
- Lottie requires equal vertex counts on morphing paths (LottieFiles compatibility doc): resample
  explicitly before export [added].
- Roundness alone morphs a square into a circle; no path keys, so nothing to resample (Megan
  Friesth, TVepzaUT6Dw 00:01:23).

## Illustrator and design hand-off

- Prepare the AI file: one element per layer, Release to Layers then drag the sublayers out, since
  released layers stay nested (Megan Friesth, qV3KXRrGm-A 00:03:57).
- Import as Composition - Retain Layer Sizes, or every layer's bounds equal the comp (Megan Friesth,
  00:12:10).
- Dynamic Link cannot receive new layers: leave spare empty layers in the AI file (Megan Friesth,
  00:09:27, 00:19:40).
- Turn on Continuously Rasterize on imported vector footage that scales above 100 % (Megan Friesth,
  00:14:55).
- For Lottie, convert Illustrator art to shape layers; pasted Illustrator paths become masks in
  Difference mode and the counters of letters vanish after export (Daniel, HZ1_afAjVb0 00:02:48,
  00:09:24).
- Overlord Push turns each Illustrator group into one shape layer; Split recreates the hierarchy
  with many layers and parents (Overlord docs; Jake Bartlett, I6QlicggqtY 00:09:54).
- Bringing a Figma mobile frame into After Effects through Overlord: the frame is small (393 x 852),
  so double the comp to 786 x 1704 with Scale art to comp width on, or run Scale Composition after
  the transfer (Jake Bartlett, I6QlicggqtY 00:11:17 to 00:13:24). This sizes the After Effects comp
  for a video master; it is not a rule for the size of a Lottie export (see procedures 13).

## Path followers

- `pointOnPath()` takes 0 to 1 by arc length: divide a percent slider by 100 (Manuel, 748l7DIU4bQ
  00:05:54).
- Shape path points live in group space: `toComp()` alone misses the group Transform. Add the group
  Position minus Anchor (Expression Path property doc; [live]).
- Prefer `pointOnPath` to Create Nulls From Paths when the object must be retimed from one slider
  (Manuel, 00:04:10).
- A tapered, trimmed arrow bends with the path; a layer on a motion path does not (Manuel,
  00:06:28).
