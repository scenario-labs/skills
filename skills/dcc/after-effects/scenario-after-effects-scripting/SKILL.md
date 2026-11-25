---
name: scenario-after-effects-scripting
description: "Use when an After Effects task needs a script or a pipeline: make five (or five hundred) versions from a spreadsheet, CSV or JSON, localize an end card into many languages and aspect ratios, swap text and images per row, batch render with the right output module and file names, render without opening the interface (aerender, render farm, nexrender), resume a batch render that crashed, mark rows done in the sheet, queue to Media Encoder, export a MOGRT or Essential Graphics template by script, or debug ExtendScript (ES3 errors, undo groups, dialogs that block a script, render queue status, \"template is not a valid template name\", \"Directory does not exist\"). Also when choosing between a custom script, Templater, Plainly or nexrender, or asking about UXP, CEP and the C++ SDK."
license: MIT
---

# After Effects scripting and automation

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means a batch tool that a studio can run unattended every month: it reads data,
builds versions that never touch the master, refuses rows it cannot build cleanly, names every
output from a pattern, and returns a report that says what failed and why. The stance: test the
template with its worst rows before the batch, measure every version with numbers, and treat any API
name you have not run as a guess. If a sibling skill named here is missing from your available
skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap. **REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit,
version traps).

## Stance (the expert delta)

1. **Design the template so variable data cannot break it, then automate.** Layout driven by
   content, few exposed controls, limits enforced in the template and in the data (Joey Korenman,
   School of Motion, uo5k4_vu5Vk 00:03:52; Sergei Prokhnevsky, ukramedia, Ov4Zd-Mgmbo 00:01:38).
2. **`comp.duplicate()` is shallow.** It copies layers, markers, expressions and Essential
   Properties, but nested precomps and footage stay shared, so editing a logo precomp in one version
   edits all of them. It also renames by incrementing the trailing number: `MASTER_16x9` became
   `MASTER_16x10` [added, live 27.0]. Rename at once and deep-copy every precomp that changes per
   row. When only text and media change, keep one precomp and set its Essential Properties per
   instance instead (`ADBE Layer Overrides`, media through `setAlternateSource`) [added, live 27.0].
3. **Never invent a render template name.** Templates differ per machine; a wrong name throws "X is
   not a valid template name". List them first (`AEK.capture.templates`) and check before
   `applyTemplate` [added, live 27.0]. Forgetting the output module once produced 26 AIFF files
   (uo5k4_vu5Vk 00:22:39).
4. **One row, one try/catch; the batch never stops.** Collect `{id, line, error}` per row, move a
   half-built version to a `_FAILED` bin, and keep going (Ov4Zd-Mgmbo 00:11:25 writes a per-run
   report).
5. **Refuse, do not shrink to unreadable.** Fit text down to a floor (60 % of the designed size),
   then fail the row with the measured width. A paragraph box reports `boxOverflow`;
   `sourceRectAtTime` does not show hidden lines [added, live 27.0].
6. **Three stress rows first.** Longest text, a missing asset, the most extreme ratio: build,
   render, look at one contact sheet, probe the files, then run the rest (SkIOeqJEKD0 00:00:31 tests
   3 and 303 characters; uo5k4_vu5Vk 00:33:14).
7. **Headless means saved project plus `aerender`, and never trust its exit code.** A wrong comp
   name printed "aerender ERROR: No comp was found with the given name." and exited 0 [added, live
   27.0]. Read the log and probe the file. `aerender` never saves the project (`-close` defaults to
   DO_NOT_SAVE_CHANGES, aerender doc): after a full run the `.aep` still read QUEUED on every item
   [added, live 27.0]. Resume from the files on disk.
8. **Data headers equal layer names, case included; values come from fixed lists; the sheet is a
   ledger.** A wrong header silently does nothing (uo5k4_vu5Vk 00:19:20). Controlled values replace
   free text (the top cause of rework); limits such as 40 characters are checked before the build
   (Ov4Zd-Mgmbo 00:03:49; uo5k4_vu5Vk 00:16:06). A status column gates rows (`ready`) and gets
   `done` written back per row after the render (uo5k4_vu5Vk 00:30:29; Ov4Zd-Mgmbo 00:11:25 to
   00:11:57).

## Establish first

- Deliverables: list of versions (languages x ratios x durations), codec and container, frame rate,
  sizes, naming pattern, where files go.
- Data: CSV, JSON or sheet export; encoding (UTF-8; Excel "CSV UTF-8" adds a BOM); header names; a
  status column; asset paths absolute or relative to one root.
- Master: which comp, which layers change, which precomps change per row, fonts (PostScript names),
  whether a per-ratio master exists.
- Machine: After Effects version (`app.version`), installed output module and render settings
  templates, Allow Scripts to Write Files and Access Network on (required for any file write), free
  disk.
- Render machines: each needs the same fonts, effects and encoders, plug-ins copied locally, never
  shared over the network (aerender doc). Preflight every node.
- Channel: the bridge for building and checking; `aerender` for the bulk render; `handoff` when a
  person must run the script.
- Defaults if nobody says: H.264 through `H.264 - Match Render Settings - 15 Mbps`, `Best Settings`,
  names `{id}_{lang}_{ratio}_v001.mp4`, three stress rows first.

## Procedure

1. **Preflight the project and the machine** (procedures.md section 1). Run `ae.py audit` (its
   `fonts.missing` rule also catches a substitute font after reopen, `isSubstitute`), list
   templates, and refuse any comp on the Cinema 4D renderer (`comp.renderer === "ADBE Ernst"`):
   `aerender` can render nothing from it (nexrender README).
   ```bash
   python3 ae.py templates "MASTER"
   ```
   GATE: every template the job names is in the list; zero missing or substitute fonts; no
   `ADBE Ernst` comp; the master comp exists once. Same result on every render node.
2. **Read and validate the data before any build.** `AEX.batch.readCsv(path)` handles quoted fields,
   `""`, commas and line breaks inside quotes, CRLF and the BOM; it flags rows whose cell count
   differs from the header. `AEX.batch.validate(csv, {required, allowed, maxLength, unique})`
   returns every bad cell with its line; a missing required column stops at once. Pass the path in
   `ARGS`, never `~`. GATE: zero validation problems (or the bad rows set aside with their reasons),
   every pattern field is a column, every asset path checked with `File.exists`.
3. **Build each version from the master** (procedures.md, "End-to-end versioning job"):
   `deepDuplicate`, rename, `setText`, `importOnce` plus `swapImage` inside the copied precomp,
   `resize` to the ratio, then `AEK.text.fit` and `AEK.text.inFrame` per text layer. Wrap each row
   in `try/catch`; on failure move the comp to `_FAILED` and record why. GATE: report lists every
   row as ok or failed with a reason; master unchanged (its text and precomp values read back
   equal).
4. **Queue with checked templates and a naming pattern.** `AEX.batch.queue(comp, file, {om, rs})`
   checks both template names, creates nothing it cannot name, and leaves the item QUEUED. Create
   the output folder first: a missing folder only fails at `render()` with "Directory does not
   exist". GATE: `renderQueue.numItems` equals the number of ok rows; each item status QUEUED; each
   file name unique.
5. **Render three rows, look, probe.** For a draft look first, set `rqi.skipFrames = 1` (every other
   frame: 30 of 60 frames blocked 0.85 s, live 27.0) and a short `timeSpanDuration`; reset both
   before the real render (renderqueue doc). `AEX.batch.renderOnly(firstThree)` unqueues the others,
   renders (it blocks), restores them. Capture one frame per version, failed ones included, and read
   one `ae.py sheet` (it fits mixed ratios into one tile box). Probe each file. GATE: status DONE;
   ffprobe size, fps, frame count and duration equal the comp; text inside the 5 % margin on the
   sheet; the right logo per language.
6. **Save and render the rest headless.** Save a copy of the project, then
   `aerender -project copy.aep -mfr ON 100 -v ERRORS_AND_PROGRESS -log run.log` with no `-comp`: it
   renders every item that was QUEUED when the file was saved, with its own output module and path.
   Items already DONE at save time are skipped. Never add `-continueOnMissingFootage` to a batch: it
   renders color bars in place of missing footage (aerender doc). GATE: one "Finished composition"
   per item, counted with `grep -o` (the log separates lines with carriage returns, so `grep -c`
   returned 1 for 3 items, live 27.0); no "aerender ERROR"; no "missing fonts"; one file per ok row.
7. **Verify by decoding, write the status back, resume.** Count decoded frames per file
   (`ffprobe -count_frames`): a truncated file still reported 30 frames from its header; only the
   decode count (N/A) caught it [added, live 27.0]. Write one status row per data row
   (`AEX.batch.writeCsv`: id, `done` or `failed`, file, reason) next to the renders, never over the
   person's data file. After a crash, `AEX.batch.resumeQueue(verifiedNames)` on the saved copy
   unqueues items whose file passed, renames other existing outputs to `.incomplete` and requeues
   the rest; save, rerun `aerender` (procedures.md section 11). GATE: decoded frames equal the comp
   for every `done` row; `ok + failed = rows`; a resumed run renders only the missing rows and
   leaves verified files untouched.

## Numbers

| Value                      | Meaning                                                                                                                             |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 60 % of designed font size | fit floor before a row fails (relative to the master's size)                                                                        |
| 84 % of comp width         | max text width used in the live job (8 % margin per side)                                                                           |
| 5 % of frame               | `AEK.text.inFrame` margin for title-safe checks                                                                                     |
| 3 rows                     | stress rows rendered before the batch                                                                                               |
| 3.0 to 3.2 s               | three 2 s versions at 540p, 30 fps, H.264, rendered in the open app (live 27.0)                                                     |
| 5 to 6 s                   | `aerender` wall time for one 2 s 540p comp, about 5 s of it launch (live 27.0)                                                      |
| 3012 to 3019               | `RQItemStatus` values WILL_CONTINUE, NEEDS_OUTPUT 3013, UNQUEUED 3014, QUEUED 3015, RENDERING, USER_STOPPED, ERR_STOPPED, DONE 3019 |

## Quality gates

Measurable:

- Report: `ok + failed = rows`; each failure has a reason a person can act on ("Image not found:
  path", "Text overflow on TITLE: 955 px > 454 px at the 38 px floor").
- Queue: one item per ok row, status QUEUED before the render and DONE after; `isValid(om)` before
  reuse.
- Files: `ae.py probe` per output: codec, width, height, fps, frames equal the comp and work area;
  then a decoded frame count (`ffprobe -count_frames`) equal to the comp, because header values
  survive a truncated file.
- `aerender`: no "aerender ERROR"; one "Finished composition" per item (`grep -o`); the exit code
  alone proves nothing.
- Status file: one row per data row, `done` only where the decode count passed.
- Master: text, precomp and footage of the master read back unchanged after the batch. Visual (one
  contact sheet of every built version at the hold frame, failed rows included):
- Text inside the margin, nothing clipped, no line collision; the right language and logo per row.
- Portrait and square versions read as designed layouts, not a shrunken landscape strip.
- Failed rows show the defect the report names.

## Common mistakes

| Mistake                                                          | Symptom                                                               | Fix                                                                                     |
| ---------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Editing a precomp inside a plain `duplicate()`                   | Every version and the master change                                   | `AEX.batch.deepDuplicate` (copies nested comps, relinks layers)                         |
| Trusting the duplicate's name                                    | `MASTER_16x10` appears                                                | Set `name` right after `duplicate()`                                                    |
| Template name from memory or another machine                     | "is not a valid template name"                                        | Check `om.templates` and `rqi.templates` first                                          |
| Output folder not created                                        | `render()` throws "Directory does not exist"                          | `AEK.core.ensureFolder` before queueing                                                 |
| Changing `comp.width` and `height` only                          | Layers stay at old pixel positions                                    | `AEX.batch.resize` (moves and scales layers)                                            |
| Proportional `min(sx, sy)` resize to 9:16                        | Tiny layout, title and subtitle far apart                             | Short-side rule around the center, or an authored portrait master                       |
| Shrinking text until it fits                                     | Unreadable 18 px titles                                               | Floor at 60 %, then fail the row                                                        |
| `sourceRectAtTime` on box text                                   | Overflowing lines go unnoticed                                        | Read `textDocument.boxOverflow` (24.6+)                                                 |
| Reading `aerender` exit code                                     | Bad comp name reported as success                                     | Grep the log for "aerender ERROR", probe the file                                       |
| Rerunning the saved `.aep` to resume                             | Every item renders again: `aerender` never writes DONE back           | `AEX.batch.resumeQueue` with the files that passed the decode count                     |
| Free text in data cells                                          | Misspelled values, rework                                             | `AEX.batch.validate` with `allowed` lists before the build                              |
| Reusing an `OutputModule` after `setSettings` or `applyTemplate` | Invalid object (documented)                                           | Re-fetch `rqi.outputModule(1)` after each change                                        |
| A Cinema 4D renderer comp (`ADBE Ernst`) under `aerender`        | No file, or "Couldn't find a result file"                             | Switch to Classic 3D or Advanced 3D (`ADBE Calder`) before saving                       |
| A render node without the project's fonts                        | Substitute font in the output; "Project has missing fonts" in the log | Preflight on each node, test `font.isSubstitute`                                        |
| `app.open()` or `app.newProject()` over unsaved changes          | A native Save As panel blocks the app; nothing closes it from outside | `app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES)` first, only with the owner's word |
| `alert()` or a file dialog in a batch                            | Every later job waits on a modal                                      | Return messages; paths from `ARGS`                                                      |
| ES5 in ExtendScript                                              | `undefined is not a function` on `indexOf`, `trim`, `JSON`            | ES3 loops, `AEK.json`, `replace(/^\s+                                                   | \s+$/g, "")` |
| `item instanceof AVItem`                                         | Always false                                                          | Test `CompItem` or `FootageItem` (scripting doc)                                        |

## Handoffs

- Receives a validated master comp and its layer names from scenario-after-effects-project; the
  version matrix and end card design from scenario-after-effects-motion-production.
- Sends text that fails the fit floor to scenario-after-effects-typography (wrapping, line breaks,
  font choice per script); content-driven rigs (`sourceRectAtTime` boxes, controls) to
  scenario-after-effects-expressions.
- Sends codec, color tags and platform specs to scenario-after-effects-color-delivery (H.264 at
  540x540 was tagged `smpte170m`, at 540x960 `bt709`).
- Per-row generated images, voice or music arrive through scenario-after-effects-generation; this
  skill only swaps the files in.
- Uses the runner and channels of scenario-after-effects-expert; does not re-document them.

## Version notes

- Native H.264 in the Render Queue since 23.0; Media Encoder is optional.
  `renderQueue.queueInAME(bool)` exists (14.0); `canQueueInAME` is false until an item is QUEUED; it
  sends items with Media Encoder's last used preset.
- `TextDocument.boxOverflow` and `boxAutoFitPolicy` 24.6; `app.fonts` 24.0; `characterRange` 24.3;
  `Layer.id` 22.0; guide enums changed integers in 26.5 (compare constants).
- File name templates such as `[compName]_[width]x[height].[fileExtension]` are settable by script
  through `"Output File Info"` (live 27.0).
- Comps using the Cinema 4D renderer (`ADBE Ernst`) can render nothing under `aerender` (nexrender
  README). On 27.0 `ADBE Advanced 3d` is Classic 3D, what a comp made by script starts on.
- MFR is on by default since 22.0; `-mfr ON|OFF max_cpu_percent` sets it per `aerender` run
  (procedures.md section 5 on whole-queue mode).
- UXP is a public beta in After Effects (Beta) 27.1; CEP is disabled by default from December 2028;
  standalone ExtendScript and ScriptUI are expected to keep working. Hybrid C++ plugins in UXP are
  not supported yet; the C++ SDK is for native effects, not pipelines.

## References

- [references/procedures.md](references/procedures.md): full jobs (CSV, versioning, render queue,
  aerender, MOGRT, deep duplicate), channel, checked line, what to check.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps,
  and Templater, Plainly and nexrender compared.
- [references/critique.md](references/critique.md): rubric with numbers and the contact sheet
  checklist.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for the same steps.
- [references/sources.md](references/sources.md): every source, best timestamps.
- [scripts/batch.jsx](scripts/batch.jsx): `AEX.batch` helpers (readCsv, validate, deepDuplicate,
  setText, importOnce, swapImage, resize, queue, renderOnly, resumeQueue, eachRow, fill, writeText,
  writeCsv).
