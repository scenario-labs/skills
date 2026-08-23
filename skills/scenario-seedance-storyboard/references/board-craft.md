# Board craft and the coherence gate

Drawing the board, then proving it is fit to spend a video run on. Read this before generating panels.

## Drawing the panels

Draw them as pencil line art and let the photographic plates carry the surfaces. The board's job is
the plan, not the look: a drawn board's numbering and captions are discarded as notation, while a
photoreal board burns them into the delivery. Measured on one sequence, prompt held byte-identical
and only the board's register changed: the photoreal board leaked its panel numeral into 6 of 8
shots, the pencil board into none, and the pencil delivery was fully filmic, since the plate supplied
the surfaces the drawing did not.

So numbering is safe on a pencil board, in frame or under it. Motion arrows are not, and they are the
one marking to keep off the art entirely. An arrow can render into the delivery as a real arrow
floating in shot, it does so on some panels and not others with nothing in the board to predict which,
and no negative clause stops it: across two runs on one board, an arrow beside an extended hand
transferred both times, arrows beside a spinning skirt once, and three arrows in open space never.
Naming arrows in a "no arrows in frame" clause changed only how one rendered, from crisp white to
dark red, not whether it appeared. Put motion in the prompt's per-beat timeline instead, where it
works: sleeve lag, a dust burst on heel contact, and a train settling late all rendered from prose
alone.

Check the delivery for leaks by sweeping the whole clip at about two frames a second, not one sample
per shot. A leaked marking can fade in part-way through a shot, so a single well-timed sample reports
a false clean.

Give each character its own plate rather than a combined sheet. Seedance 2.5 takes up to 30
`referenceImages` and the prompt binds them by index, so `@image1` is fighter A and `@image2` is
fighter B, each at full canvas and unambiguous. A pencil board carries no surfaces of its own, so in
the scripted lane the plates do double duty: holding the cast steady while the board is drawn, then
supplying identity and material to the video run.

Pick the plate and board model for legible in-image text, strict grid adherence, and `referenceImages`
input so panels lock to the plates; shortlist with `search` (at authoring time
`model_openai-gpt-image-2` did all three), since `recommend` can answer this step with style LoRAs.
A board is a large canvas: it can exceed an unstated total-pixel ceiling even inside the schema's
per-axis limits, and a height like 1080 can miss the schema's `step`, so read the error and adjust.

Generate the panels as individual images rather than one grid, then compose the grid. One bad panel
then costs one panel instead of the board, which is the same reason `scenario-storyboards` runs one
`model_run` per panel.

## Filing, before anything is generated

A sequence produces dozens of assets: a plate per character, a panel per shot, a repair per failure, a
composed board, then the video. Loose in a project they are unrecoverable a week later, and the panel
you need to re-repair is indistinguishable from the one it replaced.

So create the collection first and add each artifact as it lands, rather than tidying up at the end.
The collection tools are catalog-only, so route them through `scenario_tools_search` once for the
schemas and then `scenario_tool_execute_write`:

- `collection_create` takes a `name` only, there is no description field, so put the sequence and the
  date in the name.
- `collection_add_assets` takes `collection_id` and an `asset_ids` array; batch each stage's output in
  one call.
- `collection_update` accepts a `thumbnail` asset id: point it at the composed board so the collection
  is recognizable in a list.

The payoff is retrieval: `search` with `target="assets"` accepts `filters.collection_ids`, so the whole
sequence comes back in one call, and a repaired panel sits next to the panel it replaced.

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

   Keep the composed board's own aspect ratio between 0.4 and 2.5. Seedance rejects a reference image
   outside that range, and the run fails on an opaque internal error whose `hint` is the only place the
   range appears. A grid of 16:9 panels reaches it fast: four columns by two rows is 3.56 and fails,
   while three by three is 1.78 and passes. Choose the grid for the ratio, not for the panel count.

4. Re-gate the replaced panel before spending the video run.

The economics are the argument: a repaired panel cost 47 CU against the 2730 CU video run it protects,
and a board that reaches the video model with a broken panel spends the whole run on a sequence that
cannot be delivered.

## What transfers from a panel to the video, and what does not

Not every panel flaw survives into the render, so know which classes to spend a repair on.

**Transfers.** Marks the video model reads as depicted objects rather than notation. On a photoreal
board that included a numbered badge, which burned into all 20 seconds of a delivered clip; on a
pencil board it is the drawn motion arrow, which is why arrows stay off the art. So does anything that
is a plan error rather than a rendering error, because the video obeys the plan: a mismatched livery, a
character on the wrong side of frame, a shot order that contradicts the script.

**Often does not.** Prop and limb geometry that the video model re-derives from scratch. A staff duel
whose panels were flagged five times over for hands merging into wood and staffs bending or breaking
still delivered a clean 24 seconds: rigid staffs, four distinct hands at the bind. The panels were the
worst of three sequences and the video was not.

So the gate is worth its cost for the classes that transfer and for proving the plan before a video
run, and a panel whose only defect is local prop geometry is worth one repair attempt, not three.
