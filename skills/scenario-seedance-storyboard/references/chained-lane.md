# Chained per-shot runs

Per-shot detail for the second lane in `SKILL.md`. Read it when the sequence runs past one job's
duration cap, when each shot needs its own control, or when the sequence must open on an exact pose.

## The chain

Draw the board first when the image budget allows: it is the cheap place to catch a broken chain. It
is the first thing to drop when the budget is tight, because the board is never passed to the video
model in this lane and the set review below covers the same ground; keep one image slot in reserve for
re-rendering a drifted still instead. Then render each boundary pose as a still and run each shot in
first and last frame mode, so shot N takes `image` = boundary still N-1 and `lastFrameImage` = boundary
still N. Adjacent shots share the still, so every cut lands on a frame both sides already agree on.
N shots cost N+1 stills and N runs, plus one plate per character.

This mode excludes `referenceImages` (mutually exclusive with `image`), so the stills are the only
identity a shot gets. `aspectRatio` is ignored here too: the output adapts to the first frame, so the
stills set the delivered shape.

## Rendering the boundary stills

The sheet makes each still plausible on its own, not identical to the next. Three disciplines close
that gap, and all three are cheaper than a re-run:

- **One baseline prompt, one varying clause.** Keep the prompt byte-identical across the set and
  change only the pose clause (see `scenario-consistency`).
- **Pin screen position, not just pose.** A named pose is not a named position: say which side of
  frame each character holds in every still. A mirrored still asks two fighters to swap sides
  mid-shot, which breaks the cut as hard as a wrong limb.
- **Hold the framing.** A shot whose camera travels cannot land on a boundary drawn from the anchor
  framing. Pick continuity over camera variety, or move the camera inside a single shot only.

Then review the whole set together before spending one video run. Costume detail drifts still to
still, a mask, a helmet crest, a metal finish, and because the stills sit on the boundaries, every
drift lands on a cut. Regenerate the offending still, not the delivered shot.

## Verifying the joins

Free, and exact: `asset_get` returns each clip's `firstFrame` and `lastFrame` as their own asset ids,
so `asset_display` the outgoing `lastFrame` against the incoming `firstFrame`, one pair per join. Both
must read as the same pose. When a delivered ending beats the drawn one, pass that clip's `lastFrame`
asset id as the next shot's `image` instead of the drawn still.

## When a shot is refused

A per-shot run can be rejected on its generated audio rather than its picture, which reads as a
content refusal on a fight that is fine to look at. Re-run that shot with `generateAudio: false`. Do
not leave some shots scored and one silent: lay the master picture-only and score the assembled cut,
which is the rule anyway.

## Repairing one shot

Render the shot's two boundary stills, split the master at its timecodes, regenerate the shot between
them, and rejoin (`scenario-video-editing`, `scenario-video-assembly`). Score once over the assembled
cut, never per shot: the sound lanes are in `scenario-seedance`.
