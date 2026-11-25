# Critique rubric (lead)

Score a run before reporting it. Each line is pass or fail. One fail in "Safety" stops delivery.

## Safety (live session)

- [ ] `info` and `audit` ran before any change, and their findings were read.
- [ ] A safety copy exists, or the person declined one in writing.
- [ ] The change ran inside one named undo step per stage.
- [ ] No job called `alert`, `confirm`, `prompt`, a file dialog, `close`, `newProject`, `open`,
      `quit` or a cache purge.
- [ ] `dialogs` is empty in every result.
- [ ] The person's queued render items have the same status and render flag as before.
- [ ] Current time, work area and layer selection are back as found.
- [ ] No file of the person was overwritten or deleted. New files have new names.
- [ ] Locked layers that were unlocked are locked again, and the report says so.

## Numbers

- [ ] `stats.diff` shows only the intended items, comps and layers.
- [ ] Every touched layer prints `changed: []` against its earlier print (in, out, start, stretch,
      parent, effects, masks, keys, expressions).
- [ ] Audit: zero errors, or each error reported with its layer. No new `expression.error`,
      `fonts.missing`, `footage.missing` or `effect.missing`.
- [ ] Durations are stated in frames with the frame rate.
- [ ] No linear keys on anything that moves, unless asked (`AEK.motion.linearKeys(comp)` is empty).
- [ ] Text that changed font or content is inside the safe area (`AEK.text.inFrame`, margin 0.05).
- [ ] Footage is not enlarged past 105 percent without a note.
- [ ] Delivered files: `probe` matches codec, size, frame rate, frame count and alpha.

## Looking (one contact sheet, opened)

- [ ] The subject is present in every frame of the sheet.
- [ ] No empty or black frame inside a layer's span (a clip that ended early shows here).
- [ ] No text cut by the frame edge, no glow or shadow clipped by a layer edge.
- [ ] Swapped footage fills its placeholder: no bars, no stretched aspect.
- [ ] Fonts on the sheet are the ones asked for, weights kept (bold stays bold).
- [ ] Nothing unrelated moved: compare a frame from before the change when one exists.

## Editability (open the comp like the next person will)

- [ ] Layers and new comps are named by function.
- [ ] No stack of hold keys where a rule or a control would do.
- [ ] Agent-made items sit in their own bin.
- [ ] Controls the person will touch are on one control layer or in Essential Properties.

## Report

- [ ] The diff, the undo step name and the files written are listed.
- [ ] Skipped items are listed with the reason.
- [ ] Assumptions are listed.
- [ ] What the agent did not judge is named: motion feel at full frame rate, sound, style match.
