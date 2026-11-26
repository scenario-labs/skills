---
name: scenario-after-effects-shape-layers
description: "Use when building or fixing shape layers in After Effects: line icons, logo reveals from Illustrator or SVG, Trim Paths draw-ons, Repeater bursts, ripples and rings, Merge Paths, taper and wave, path morphs, Lottie exports. Also for 'stroke thickens when scaled', 'trim draws in the wrong order', 'the morph collapses', 'ring has a gap', 'pattern spills', 'blurry vector', 'Lottie looks different'."
license: MIT
---

# Shape Layers and Vector Animation

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means every vector stays editable, every stroke holds its specified width on
screen, and every operator sits where it acts on exactly the paths it should. The agent builds shape
layers by match name, proves structure with a dump and the look with one contact sheet, and plans a
Lottie export from the first group it draws. If a sibling skill named here is missing from your
available skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit,
version traps).

## Stance (the expert delta)

1. **Order is the program.** Inside a group, operators act on every path above them and nothing
   else; paint comes last. The first group in Contents, and the first item of an `AEK.build.shape`
   spec list, draws on top. Read the stack before changing values (Adobe shape docs; measured in
   27.0).
2. **Parametric until the path itself must move.** Animate Size, Roundness and Points; Size keeps
   the stroke weight where Scale thickens it. Convert to Bezier Path has no way back (Megan Friesth,
   TVepzaUT6Dw 00:00:49, 00:04:05).
3. **Trim Paths is an engine.** End = Start + 0.1 with a Round cap makes a traveling dot; Trim below
   a Repeater set to Individually draws the copies in sequence (Manuel, 748l7DIU4bQ 00:03:36;
   sequence measured in 27.0).
4. **One layer can hold the matte.** A linked mask path plus Merge Paths Intersect clips a pattern
   without a track matte; it clips fills only, and a Repeater inside needs its own Merge Paths set
   to Add (Alex Deaton, heYi6xLWvB0 00:02:37, 00:13:47, 00:18:50; both measured).
5. **Taper and Wave replace path keys** for brush strokes, hair and plants. The Width fields default
   to 0 %, so a Length alone makes a point (Sarah Wade, rtt-gGDxrZ4 00:07:28; default measured).
6. **Morphs are decided by vertex 1 and direction.** 27.0 adds missing vertices itself, but a first
   vertex two steps off collapsed the shape to a fifth of its width mid-morph. Lottie still demands
   equal counts (measured; LottieFiles compatibility doc).
7. **Plan Lottie from the first group.** Expressions, effects, cameras and adjustment layers drop.
   Basic text exports if the runtime has the font; text animators, text on a path, 3D and gradients
   are partial. Merge Paths, Taper, Wave and path wigglers are not in the compatibility matrix.
   Audit a duplicate before the panel export (LottieFiles docs; Daniel, HZ1_afAjVb0 00:02:48).

## Establish first

| Input                          | Why it changes the plan                                                        | Default                                                                                                |
| ------------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Deliverable                    | Video, Lottie (web or app), or both decides which features are allowed         | Video; ask before using Taper, Wave or Merge Paths if Lottie is possible                               |
| Stroke spec                    | Width on screen at delivery size, cap, join                                    | 2 px at 1080p, Round cap and join                                                                      |
| Icon grid                      | Coordinates and stroke scale                                                   | 24-unit grid, drawn at final pixel size                                                                |
| Frame rate                     | Stagger and draw lengths are in frames                                         | 30 fps                                                                                                 |
| Source art                     | SVG, Illustrator, Figma, or drawn by script                                    | SVG import (26.0+); Edit > Paste of Illustrator or SVG (26.3+); Illustrator text as text layers (27.0) |
| Lottie player and display size | web, iOS, Android: support differs; the player scales strokes with the display | Test in the target player at its display size                                                          |
| Project bit depth              | New projects inherit it; 32 bpc PNGs store values divided by 10                | 8 or 16 bpc, or `ae.py sheet --gain 10`                                                                |
| Channel                        | bridge, handoff, GUI for conversions                                           | bridge                                                                                                 |

**Base rate:** frame counts in this skill assume 30 fps. For another rate, multiply by (target fps
/ 30) and round to whole frames: 30 to 24 is x 0.8, 24 to 30 is x 1.25.

## Procedure

Code for every stage is in [procedures.md](references/procedures.md); shipped jobs in
`scripts/jobs/`, helpers in `scripts/shapes.jsx` (`AEX.shapes`).

1. **Inspect.** Goal: know the stack before touching it. Run `inspect.jsx` (`AEX.shapes.order` and
   `dump`). GATE: no order warnings, or each one explained.
2. **Intake vector art.** Routes by version are in [procedures.md](references/procedures.md)
   section 11. SVG: `vector_intake.jsx` imports it as one native shape layer, one group per element,
   colors kept. Illustrator: import as footage or as Composition - Retain Layer Sizes, then Create
   Shapes from Vector Layer. By script it converts only some of the time: `vector_intake.jsx`
   reports `converted` and hands a person the GUI step when false. Illustrator text imports as
   editable text layers (27.0). Set type becomes shapes with Create Shapes from Text, which runs by
   script when the comp is open in the viewer (procedure 16). Prepare the `.ai` first (sublayers out
   of their parent, spare empty layers). For generated artwork entering here, see
   scenario-after-effects-generation. GATE: one shape layer per element to animate; group names
   meaningful; source layer kept and off.
3. **Build or rebuild structure.** One group per moving part; paths, then operators, then Stroke,
   then Fill. `AEK.build.shape` builds static groups from a spec (rect, ellipse, star, path, fill,
   stroke, Trim); use `AEX.shapes` for other operators, nested groups and edits to an existing
   layer. Shared Stroke, Taper, Wave or Trim go at Contents level after the groups when every group
   should inherit them (Sarah Wade, 00:16:44). Re-fetch references after every `addProperty`:
   `AEX.shapes.add` does it. GATE: `order` matches the plan.
4. **Animate the draw.** `icon_drawon.jsx`: Trim End 0 to 100 per group, 12 frames, 3-frame stagger,
   `cubic-bezier(0.2, 0, 0, 1)` through `AEK.motion.bezier`. Bursts: `burst.jsx`, Copies x Rotation
   = 360, Trim End then Start chasing. Arrive and leave on different properties (Size in, Scale out)
   so one curve serves both (Evan Abrams, wOZwzLgJw9o 00:09:40). A Repeater with Copies 2 and a
   Position offset duplicates an animated part with one set of keys (Alex Deaton, heYi6xLWvB0
   00:08:06). Rings that spread evenly: `AEX.shapes.ripple` (Offset Paths, a feathered matte by
   radius; looping, or `once` for one pass; `matte: "shape"` keeps it shape layers only; procedure
   15). A wordmark comes from set type converted to shapes, never letters drawn by hand unless the
   brief asks; size the lockup to 50 to 70 % of the safe width. GATE: `AEK.motion.sample` shows no
   linear keys and the settle frame inside the plan; sheet shows the intended draw order.
5. **Clip, taper, morph.** Clip patterns with `matte_eye.jsx`. Brush strokes with `taper_wave.jsx`.
   Taper lengths meet at 100 (64 + 36); a gap leaves a lump (Sarah Wade, 00:06:22). Reverse Path
   Direction flips the fat end and the wave: drop the minus in the Phase expression (00:12:22).
   Square to circle needs only Roundness keys (Megan Friesth, 00:01:23). Other morphs go through
   `morph_fix.jsx` (resample to equal counts, rotate the first vertex, reverse direction); a morph
   that still looks hard hides in a cut at peak speed with anticipation and overshoot (Ben Marriott,
   3EGuLX6PsQ4 00:03:21). GATE: mid-morph width stays near the end states; no spill outside the
   clip.
6. **Hold resolution and stroke width.** Shape layers stay vector at any scale. Turn Collapse
   Transformations on for precomps and vector footage scaled above 100 %. Where a layer or parent
   scales uniformly, drive Stroke Width with the constant on-screen expression; under non-uniform
   scale, rebuild at delivery size. Then run `stroke_audit.jsx` with `scaleAware: true`. GATE: every
   stroke at spec on screen.
7. **Review.** Capture from an 8 or 16 bpc project with `ae.py frames ... --sheet`; read one sheet
   against [critique.md](references/critique.md). GATE: every visual row passes.
8. **Prepare Lottie.** `lottie_prep.jsx` duplicates the comp and its nested comps, bakes every
   expression in the copies and returns the findings before and after. Remove or flatten what
   remains, then export in the Bodymovin or LottieFiles panel (GUI). GATE: no `drop` rows; `check`
   rows tested in the target player against an After Effects frame at the same time.

## Numbers

| Value                                                                                                                              | Relative to                          | Source                            |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | --------------------------------- |
| 2 px stroke, Round cap and join                                                                                                    | delivery frame (1080p)               | house style for line icons        |
| 24-unit grid, icon drawn 160 px wide                                                                                               | icon comp                            | [added]                           |
| Draw 12 frames, stagger 3 frames (24 fps: 10 and 2)                                                                                | 30 fps                               | measured reference icon           |
| Path start: Ellipse and Polystar at the top, Rectangle at its top-right corner; clockwise, counterclockwise with Shape Direction 3 | Trim Start and End                   | measured                          |
| Repeater Rotation = 360 / Copies                                                                                                   | ring                                 | Evan Abrams, wOZwzLgJw9o 00:05:01 |
| Copy n scale = s^n (85 % gives 23 % at copy 9); gaps grow, so use Offset Paths for even rings                                      | Repeater Scale                       | Evan Abrams 00:04:28; measured    |
| Repeater Opacity: copy k at Start + (End - Start) x k / Copies, End never reached                                                  | copy index, paint above the Repeater | measured                          |
| Mask feather F: edge spreads about F px each side of the path                                                                      | mask path                            | measured                          |
| Trim dot: End = Start + 0.1, stroke 120 px                                                                                         | percent of path                      | Manuel, 748l7DIU4bQ 00:03:03      |
| Taper 64 / 36 length, 25 / 0 width, ease 9 / 59                                                                                    | percent of path and stroke           | Sarah Wade, rtt-gGDxrZ4 00:07:28  |
| Wave Amount 31, Wavelength 186, Phase `time * -100`                                                                                | pixels                               | Sarah Wade 00:07:28               |
| Zig Zag ridges: odd wavers, even aligns                                                                                            | per segment                          | Alex Deaton, heYi6xLWvB0 00:11:27 |
| Merge Type 1 Merge (compound; Fill Rule sets holes), 2 Add (union, no holes), 3 Subtract, 4 Intersect, 5 Exclude                   | `ADBE Vector Merge Type`             | measured; Adobe operations doc    |
| Trim Type 1 Simultaneously, 2 Individually                                                                                         | `ADBE Vector Trim Type`              | measured                          |
| Line Cap 1 butt, 2 round, 3 projecting; Join 1 miter, 2 round, 3 bevel                                                             | stroke enums                         | measured                          |
| Miter limit 4: miter turns bevel past 4 x stroke weight                                                                            | stroke                               | Adobe operations doc              |

## Quality gates

- Measurable: `order` without warnings; `strokes` without issues; Copies x Rotation = 360; equal
  vertex counts on morph keys; `AEK.expr.check` clean; Collapse Transformations on for scaled
  precomps and vector footage; Lottie audit without `drop` rows on the export copy.
- Visual: draw order and stagger; equal stroke weight across icons; crisp edges at delivery scale;
  no collapse or bow tie mid-morph; pattern stops at the clip edge; burst ring closed; tapered tips
  without lumps.

## Common mistakes

| Mistake                                                       | Symptom                                                                                   | Fix                                                                                    |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Path below the Stroke or Fill                                 | Path invisible                                                                            | Move it above the paint                                                                |
| Background group added first                                  | Everything else hidden                                                                    | The first group draws on top: move it last                                             |
| Layer or parent Scale on a stroked icon                       | Stroke 8 px instead of 2 at 400 %                                                         | Build at final size or use the constant-width expression                               |
| Trim above the Repeater when a sequence was wanted            | All copies draw at once                                                                   | Trim below the Repeater, Individually                                                  |
| Repeater inside an Intersect group                            | Pattern vanishes                                                                          | Add Merge Paths, mode Add (2), under the Repeater in its own sub-group                 |
| Merge (1) used where Add (2) was meant                        | Overlaps or nested paths turn into holes under Even-Odd                                   | Mode 2 Add for a union                                                                 |
| Repeater above the Fill when each copy needs its own gradient | One gradient across all copies                                                            | Put the Repeater below the Fill                                                        |
| Repeater Opacity with the paint below the Repeater            | Copies do not fade                                                                        | Paint above the Repeater; for a fade by radius, a feathered matte (`ripple`)           |
| Only Taper lengths set                                        | Both ends become sharp points                                                             | Set Start and End Width                                                                |
| Morph keys with mismatched first vertex                       | Shape collapses mid-morph                                                                 | `AEX.shapes.firstVertex`, or Set First Vertex                                          |
| `pointOnPath` with only `toComp`                              | Follower off by the group offset                                                          | Add group Position minus Anchor                                                        |
| Precomp scaled up, Collapse Transformations off               | Soft edges                                                                                | Turn the switch on                                                                     |
| Keyed Repeater Offset rising from 0                           | An extra copy (index = Copies) on some frames between 0 and 0.06; faint under motion blur | Key Ellipse Size and Repeater Scale, or keep the Offset at 0.1 or above (procedure 15) |

## Handoffs

- Receives from scenario-after-effects-project: comp settings, naming, bins. From
  scenario-after-effects-generation: generated vector-style art or SVG, already cleaned, as files to
  import.
- Delivers to scenario-after-effects-animation: built shape rigs whose timing and easing it refines.
  To scenario-after-effects-expressions: path and Trim rigs that need controllers. To and from
  scenario-after-effects-typography: set type converted with Create Shapes from Text (procedure 16).
  To scenario-after-effects-color-delivery: comps ready to render, or the Lottie export copy with
  its audit. To scenario-after-effects-motion-production: icon sets and logo reveals as named comps.

## Version notes

- SVG import as native shape layers: 26.0; as comp or footage: 26.2; paste from Illustrator or SVG
  with Edit > Paste: 26.3. On 25.x and earlier, SVG needs a round trip through Illustrator.
- Gradient Scale and Rotation on shape gradients (`ADBE Vector Grad Scale`,
  `ADBE Vector Grad Rotation`): 26.0.
- Illustrator text imports as editable text: 27.0.
- The 27.0 AI Assistant can add, remove and reorder shape operators and stroke dashes from a prompt;
  verify its result with `inspect.jsx`.

## References

- [references/procedures.md](references/procedures.md): the live match-name map and every job, with
  checks.
- [references/critique.md](references/critique.md): measurable and visual rubric, severity.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps.
- [references/gui-paths.md](references/gui-paths.md): menus, panels and shortcuts for the same work.
- [references/sources.md](references/sources.md): videos and docs with what each is best for.
- [scripts/shapes.jsx](scripts/shapes.jsx): `AEX.shapes` helpers (`add`, `group`, `path`, `stroke`,
  `fill`, `dump`, `order`, `strokes` (reads widths after expressions), `ripple`, `resample`,
  `firstVertex`, `reverse`, `lottie`).
- [scripts/jobs/](scripts/jobs/): the shipped jobs named in the procedure.
