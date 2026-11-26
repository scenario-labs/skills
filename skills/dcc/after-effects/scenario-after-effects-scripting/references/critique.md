# Critique: judge a batch tool and its output

Score each line pass or fail. A batch ships only when every "must" passes on the three stress rows
and on the full run.

## The script (read the code)

| Check         | Must                                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------------------ |
| ES3           | `ae_check.py job.jsx` returns 0 errors: no `let`, arrow functions, template strings, `JSON`, `indexOf` on arrays, `trim` |
| Inputs        | Every path comes from `ARGS` or the data file, absolute; no `~`, no dialog                                               |
| Master safety | No `setValue`, `remove` or rename on the master or a person's layers; versions go to their own bin                       |
| Precomps      | Per-row precomp edits happen in deep copies or through Essential Properties overrides, never in a shared precomp         |
| Names         | `name` set right after every `duplicate()`; output names from one pattern, unique per row                                |
| Templates     | Each `applyTemplate` name is checked against `om.templates` or `rqi.templates` first                                     |
| Errors        | One `try/catch` per row; each failure recorded with id, record number and message; the loop continues                    |
| Undo          | One outer undo group (or `--undo`); `endUndoGroup` reached in the error path (`finally`)                                 |
| Projects      | No `app.open()` or `app.newProject()` over unsaved changes; switching projects closes with explicit `CloseOptions`       |
| Output module | `rqi.outputModule(1)` fetched again after every `applyTemplate` or `setSettings`                                         |
| Renderer      | No comp in the render queue uses `ADBE Ernst` (Cinema 4D) when `aerender` renders it                                     |

## The report (read the JSON)

| Check    | Must                                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Coverage | `ok + failed` equals the number of data rows                                                                                      |
| Reasons  | Each failure names the field and the measured cause (path, px over the limit, template name)                                      |
| Fit      | Every ok row's text width is at most the limit (84 % of comp width by default) and its size is at least 60 % of the designed size |
| Frame    | `AEK.text.inFrame(layer, comp, 0.05, holdTime).ok` true for every text layer                                                      |
| Queue    | One QUEUED item per ok row before rendering; DONE after                                                                           |
| Data     | `AEX.batch.validate` returned no problem before the build (allowed values, required columns, limits, unique ids)                  |
| Status   | `status.csv` holds one row per data row; `done` only where the decode count passed                                                |
| Resume   | A rerun after a crash renders only rows without a verified file; verified files keep their modification time                      |

## The files (ffprobe through `ae.py probe`)

| Check        | Must                                                                                                                                                            |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Count        | One file per ok row, none for failed rows                                                                                                                       |
| Size         | Width and height equal the ratio's size (H.264 needs even numbers)                                                                                              |
| Timing       | fps equals the comp; frames equal work area x fps (60 for 2 s at 30 fps); `-e` inclusive when using `aerender` ranges                                           |
| Codec        | The codec the output module promises (H.264 Main, `yuv420p` for the 15 Mbps template)                                                                           |
| aerender log | One "Finished composition" per item, counted with `grep -o` (lines end in carriage returns); no "aerender ERROR" and no "missing fonts", whatever the exit code |
| Decode       | `ffprobe -count_frames` equals the comp's frames: header values survive a truncated file                                                                        |

## The contact sheet (one image of every version at the hold frame, failed rows included)

Look for, per tile:

- Text inside the margin, no clipped glyph, no collision between title and subtitle.
- The right language string and the right logo per row (FR row, FR logo).
- Portrait and square tiles read as designed layouts: the title block is not a small strip in the
  middle of a tall frame. If it is, switch the resize rule or use a portrait master.
- Background covers the whole frame in every ratio (no comp color showing at the edges).
- Failed tiles show the defect the report names (clipped long title, master logo still in place).
  Mixed ratios: `ae.py sheet sheet.jpg f1.png f2.png ...` fits frames of different sizes into one
  tile box. ImageMagick `montage` fails on some machines without `-font`.

## The template's picture (before the batch)

A batch multiplies the template: a plain card becomes six plain cards. Check the master once, on
frames and numbers.

| Check          | Must                                                                                              | How                                                                             |
| -------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Hierarchy      | Second line at least 0.6 of the first line's font size; at most 0.75, or the two lines compete    | `fontSize` of both text documents                                               |
| Exit           | No frame where the plate is open (scale 90 % or more) and a line is under 5 % opacity             | sample plate Scale and text Opacity at every frame from the end of the entrance |
| Order          | The exit runs the entrance backwards; the plate starts leaving within 2 frames of the text        | first frame each layer leaves                                                   |
| One controller | Every timing reads one null (frames on sliders), so a longer version moves every element together | `AEK.expr.list` on the master                                                   |
| Hold frame     | Text, plate and accent all at rest; the longest data row still inside 60 % of the width           | the stress rows' sheet                                                          |

Measured on a 1920x1080 lower third built this way (procedures.md section 14): role 0.6 of the name,
0 empty-plate frames over frames 30 to 119. The plate closes from frame 96 and is gone at 108,
taking the text with it. The text sits inside the plate through an alpha track matte, a copy of the
plate (`layer.setTrackMatte(matte, TrackMatteType.ALPHA)`).

## Before the full run

- Three stress rows passed every "must" above.
- The master comp reads back unchanged (title text, precomp values).
- Disk space: frames x versions x bitrate fits; a 2 s 540p H.264 version was 0.07 to 0.17 MB.

## More mistakes

| Mistake                                                          | Symptom                                                               | Fix                                                                                        |
| ---------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Changing `comp.width` and `height` only                          | Layers stay at old pixel positions                                    | `AEX.batch.resize` (moves and scales layers)                                               |
| Proportional `min(sx, sy)` resize to 9:16                        | Tiny layout, title and subtitle far apart                             | Short-side rule around the center, or an authored portrait master                          |
| `sourceRectAtTime` on box text                                   | Overflowing lines go unnoticed                                        | Read `textDocument.boxOverflow` (24.6+)                                                    |
| Free text in data cells                                          | Misspelled values, rework                                             | `AEX.batch.validate` with `allowed` lists before the build                                 |
| Reusing an `OutputModule` after `setSettings` or `applyTemplate` | Invalid object (documented)                                           | Re-fetch `rqi.outputModule(1)` after each change                                           |
| `app.open()` or `app.newProject()` over unsaved changes          | A native Save As panel blocks the app; nothing closes it from outside | `app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES)` first, only with the owner's word    |
| `alert()` or a file dialog in a batch                            | Every later job waits on a modal                                      | Return messages; paths from `ARGS`                                                         |
| ES5 in ExtendScript                                              | `undefined is not a function` on `indexOf`, `trim`, `JSON`            | ES3 loops, `AEK.json`, `replace(/^\s+\|\s+$/g, "")`                                        |
| `item instanceof AVItem`                                         | Always false                                                          | Test `CompItem` or `FootageItem` (scripting doc)                                           |
| Output module left at its default in a batch                     | 26 AIFF files and no video (uo5k4_vu5Vk 00:22:39)                     | `AEX.batch.queue` with a checked `om` template                                             |
| A plate that holds open after its text fades                     | Empty colored box for several frames on the way out                   | Close the plate over the text (alpha track matte), or start it within 2 frames of the text |
