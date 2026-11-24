# Critique rubric (judge your own run before reporting)

Score each line pass or fail. Any fail in sections A to C blocks a "done" report: fix it, or report
it as open.

## A. Safety

- [ ] The channel was established (`doctor()` or the user) and named in the report.
- [ ] `stats.snapshot()` and `audit.all()` ran before the first change.
- [ ] The user's file was not overwritten. A `_v002` (or later) exists before destructive work.
- [ ] Each stage ran inside one undo record with a readable label.
- [ ] No render, plugin install, farm submission or file deletion happened unless asked.
- [ ] In mcp-safe, `max_check(channel="mcp-safe")` showed zero errors before each proposal.

## B. Numbers

- [ ] `stats.diff(before, after)` shows only the intended keys. Unexpected deltas (faces, materials,
      missing maps) are explained.
- [ ] The audit after the change has no new `error` findings.
- [ ] Counts match the request, for example every `PH_*` box handled, or N cameras created.
- [ ] Sizes are stated in system units, with the unit named. A chair at 80 to 100 cm, a door at
      about 200 to 210 cm [added] are sanity anchors, not rules.
- [ ] Batch: exit code 0 and `result.ok` true. Any other code is reported with its meaning.
- [ ] Before any merge or load, the file's units were compared with the scene's and
      `ignoreFileUnits:` was passed explicitly (procedures P7a).
- [ ] Merges used `#renameMtlDups`: no scene material was replaced by a same-named incoming one.
- [ ] Assets fitted to placeholders: the box scale counted once (P7b), base and fitted axis within
      tolerance, all three size ratios reported.

## C. Looking

- [ ] Four views or the camera renders were captured to new files.
- [ ] `image_checks` raised none of `all_black`, `all_white`, `uniform`, `mostly_clipped`,
      `low_contrast_center`.
- [ ] One contact sheet was read (not each image), and what it shows was described in one line per
      view.
- [ ] Top and front views were checked against plan dimensions when geometry changed.
- [ ] Cameras were captured with Safe Frame on.

## D. Report

- [ ] The assumptions list covers renderer, units, release, channel, and any guessed name or
      dimension.
- [ ] Files written, with full paths: backup, captures, exports, result JSON.
- [ ] Open findings and GUI-only steps left for the user.
- [ ] Minutes per stage.
- [ ] No "tested in 3ds Max" or "verified" wording for anything not run and looked at.

## What to look for in a capture

- Persp: the subject is present, framed, and not clipped by the near plane.
- Top: alignment to walls and grid, overlaps, spacing, rotation of placed assets.
- Front and left: floor contact (no floating, no sinking), heights against references.
- Renders: no black frame (missing light or a blocked render), no blown sky (exposure), no gray
  placeholder material left.
