# Board craft and the coherence gate

Drawing the board, then proving it is fit to spend a video run on. Read this before generating panels.

## Drawing the panels

Draw them in the register you want delivered: photoreal panels return filmic footage, while pencil
panels leave the model to invent every surface and drift. Keep panel numbers small and low contrast,
or under the frame: a large in-frame badge can burn into the render for a whole clip, a negative
clause does not reliably suppress it, and the delivered corners are worth checking.

Give each character its own plate rather than a combined sheet. Seedance 2.5 takes up to 30
`referenceImages` and the prompt binds them by index, so `@image1` is fighter A and `@image2` is
fighter B, each at full canvas and unambiguous. A photoreal board carries identity by itself in the
scripted lane, which puts the plates' real work upstream: holding the cast steady while the board is
drawn.

Pick the plate and board model for legible in-image text, strict grid adherence, and `referenceImages`
input so panels lock to the plates; shortlist with `search` (at authoring time
`model_openai-gpt-image-2` did all three), since `recommend` can answer this step with style LoRAs.
A board is a large canvas: it can exceed an unstated total-pixel ceiling even inside the schema's
per-axis limits, and a height like 1080 can miss the schema's `step`, so read the error and adjust.

Generate the panels as individual images rather than one grid, then compose the grid. One bad panel
then costs one panel instead of the board, which is the same reason `scenario-storyboards` runs one
`model_run` per panel.

## Why the gate takes two passes

A board-level verdict hides panel defects. Three 12-panel boards each scored 88 and `pass` while one
of them carried a physically impossible frame: four gauntlets for two fighters, an unattached glove,
and a hilt guard floating with no blade through it. Twelve panels average their defects away.

Scoring the offending panel alone does not fix that by itself. The isolated broken-car panel came back
at 92 and `pass`, and the report praised the "chrome rims" that were the defect: two different wheels,
one without the whitewall its plate specifies, neither sitting in a wheel arch. The AI-quality gate
detects artifacts, not disagreements with a reference it has never seen.

So run both passes on every panel, and require both:

1. **Artifacts.** `asset_quality_gate_run` per panel (see `scenario-quality-gate`): 1 CU per new
   analysis, image assets only, an Enterprise add-on, so degrade to `asset_analyze` when it is not
   entitled. It reliably finds melted finger joints, warped dial numerals, and doubled blade edges.
2. **Differences.** Compare the panel with its plate, item by item. The baseline enumeration is the
   checklist, so read it as a spot-the-difference:
   - **Count**: hands, fingers per hand, arms, blades, wheels, headlights. Every one attached to a
     single body, and every hand to a single arm.
   - **Part to whole**: a wheel sits inside an arch, a hilt guard sits on its own blade, wheelbase and
     door length match the plate's silhouette, a reflection sits under the limb that casts it.
   - **Livery and costume**: every named detail, the whitewalls, the gold edging, the chain.
   - **Screen side**: the character stands where the script pinned them.

A panel fails if either pass fails. Do not average, and do not accept a board-level `pass` as the bar.

The score is a weak signal for whether a repair worked. The broken wheel panel and its corrected
replacement both scored 92: what changed was the flaw list, from praising the mismatched rims to
naming a taillight housing. So judge a repair on the differences checklist and on the new `reasons`,
never on the number moving.

## Repairing one panel without re-rolling the others

1. If the board is already a single image, slice it: `model_scenario-image-slicer` with
   `xSubdivisions` and `ySubdivisions` (up to 6 each), 1 CU, returning the cells in reading order.
2. Regenerate only the failing panel, with the plates as references and the correction stated as a
   positive requirement rather than a prohibition. "Both wheels the same rim design with whitewall
   tires, each inside a wheel arch, the wheelbase of a full-size hardtop" fixes what "not deformed"
   does not. Keep the panel's caption text in the prompt so the replacement carries its own label.
3. Recompose with `model_scenario-compose-image` (Image Studio): one `layers` entry per panel with
   explicit `x`, `y`, `width` and `height`, `canvasMode: "custom"`, and the canvas size of the board.
   Approved panels are pasted, not regenerated, so they survive unchanged.
4. Re-gate the replaced panel before spending the video run.

The economics are the argument: a repaired panel cost 47 CU against the 2730 CU video run it protects,
and a board that reaches the video model with a broken panel spends the whole run on a sequence that
cannot be delivered.
