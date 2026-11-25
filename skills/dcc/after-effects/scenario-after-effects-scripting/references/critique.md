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

## Before the full run

- Three stress rows passed every "must" above.
- The master comp reads back unchanged (title text, precomp values).
- Disk space: frames x versions x bitrate fits; a 2 s 540p H.264 version was 0.07 to 0.17 MB.
