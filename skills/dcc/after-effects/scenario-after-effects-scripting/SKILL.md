---
name: scenario-after-effects-scripting
description: "Use when an After Effects task needs a script or a pipeline: versions from a CSV, JSON or sheet, localized end cards in many ratios, a comp built from a data file, batch renders with named outputs, aerender or a render farm, a batch that crashed or filled the disk, MOGRT export by script, undo groups, ExtendScript errors, or choosing between a custom script, Templater, Plainly and nexrender."
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
   edits all of them. It also renames by incrementing the trailing number (`MASTER_16x9` became
   `MASTER_16x10`) [added, live 27.0]: rename at once, deep-copy every precomp that changes per row.
   When only text and media change, keep one precomp and set its Essential Properties per instance
   instead (`ADBE Layer Overrides`, media through `setAlternateSource`) [added, live 27.0].
3. **Never invent a render template name.** Templates differ per machine; a wrong name throws "X is
   not a valid template name". List them first (`AEK.capture.templates`) and check before
   `applyTemplate` [added, live 27.0].
4. **One row, one try/catch; the batch never stops.** Collect `{id, line, error}` per row, move a
   half-built version to a `_FAILED` bin, and keep going (Ov4Zd-Mgmbo 00:11:25 writes a per-run
   report).
5. **Refuse, do not shrink to unreadable.** Fit text down to a floor (60 % of the designed size),
   then fail the row with the measured width. A paragraph box reports `boxOverflow`;
   `sourceRectAtTime` does not show hidden lines [added, live 27.0].
6. **Three stress rows first.** Longest text, a missing asset, the most extreme ratio: build,
   render, look at one contact sheet, probe the files, then run the rest (SkIOeqJEKD0 00:00:31 tests
   3 and 303 characters; uo5k4_vu5Vk 00:33:14).
7. **Headless means saved project plus `aerender`, and never trust its exit code.** It exited 0 on a
   wrong comp name and on a full disk; one full-disk render left a truncated file and no error line
   [added, live 27.0]. Check free space first, read the log, decode the file. `aerender` never saves
   the project, so the `.aep` still reads QUEUED after a run (aerender doc; live 27.0): resume from
   the files on disk.
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
- Machine: After Effects version (`app.version`), output module and render settings templates, Allow
  Scripts to Write Files and Access Network on (required for any file write), free space on the
  output volume. Every render node runs the same preflight (procedures.md section 1).
- Channel: the bridge to build and check, `aerender` for the bulk render, `handoff` when a person
  runs the script.
- Defaults if nobody says: H.264 through `H.264 - Match Render Settings - 15 Mbps`, `Best Settings`,
  names `{id}_{lang}_{ratio}_v001.mp4`, three stress rows first.

## Procedure

1. **Preflight the project and the machine** (procedures.md section 1). Run `ae.py audit` (its
   `fonts.missing` rule also catches a substitute font after reopen), list templates, and refuse any
   comp on the Cinema 4D renderer (`ADBE Ernst`): `aerender` renders nothing from it (nexrender
   README).
   ```bash
   python3 ae.py templates "MASTER"
   ```
   GATE: every template the job names is in the list; zero missing or substitute fonts; no
   `ADBE Ernst` comp; the master comp exists once. Same result on every render node.
2. **Read and validate the data before any build.** `AEX.batch.readCsv(path)` handles quotes, line
   breaks inside quotes, CRLF and the BOM, and flags rows with the wrong cell count.
   `AEX.batch.validate(csv, {required, allowed, range, maxLength, unique})` returns every bad cell
   with its line (every rule optional); a missing required column stops at once. JSON lists:
   `AEX.batch.readJson(path)` gives the same shape. A row set aside before the build keeps the
   layout compact; one that fails during the build leaves a hole. Pass the path in `ARGS`, never
   `~`. GATE: zero validation problems (or the bad rows set aside with their reasons), every pattern
   field is a column, every asset path checked with `File.exists`.
3. **Build each version from the master** (procedures.md section 3): `deepDuplicate`, rename,
   `setText`, `importOnce` plus `swapImage` inside the copied precomp, `resize`, then `AEK.text.fit`
   and `AEK.text.inFrame`. Each row runs in `try/catch` inside its own undo group, the batch inside
   one outer group (one Undo removes it all). A failed comp moves to `_FAILED` with its reason. To
   build one comp from the rows (a chart, a list), see procedures.md section 12. GATE: report lists
   every row as ok or failed with a reason; master unchanged (its text and precomp values read back
   equal).
4. **Queue with checked templates and a naming pattern.** `AEX.batch.queue(comp, file, {om, rs})`
   checks both template names, creates nothing it cannot name, and leaves the item QUEUED. Create
   the output folder first: a missing folder only fails at `render()` with "Directory does not
   exist". GATE: `renderQueue.numItems` equals the number of ok rows; each item status QUEUED; each
   file name unique.
5. **Render three rows, look, probe.** For a draft look, set `rqi.skipFrames = 1` and a short
   `timeSpanDuration`, then reset both (procedures.md section 4). `AEX.batch.renderOnly(firstThree)`
   renders those only (it blocks) and restores the queue. Capture one frame per version, failed ones
   included, and read one `ae.py sheet`. Probe each file; its size per frame sets the disk estimate
   for stage 6. When every row must pass the guarded render, run the driver of procedures.md section
   14 instead (`only` = the stress rows). GATE: status DONE; ffprobe size, fps, frame count and
   duration equal the comp; text inside the 5 % margin on the sheet; the right logo per language.
6. **Check the disk, save, render the rest headless.**
   `AEX.batch.diskCheck(outFolder, bytesPerFrame x frames x rows, 2)` must pass: space and a
   writable folder. One comp: `ae.py aerender` (expert P7). A whole queue:
   `AEX.batch.renderManifest`, save a copy, then
   [scripts/render_guarded.sh](scripts/render_guarded.sh) with the manifest (procedures.md sections
   5 and 13). Both fail an error line, a non-zero exit, a missing file, a short movie. Never add
   `-continueOnMissingFootage`: it renders color bars in place of missing footage (aerender doc).
   GATE: `RESULT ok` (every file at its frame count) or `ok` true from `ae.py aerender`; no "missing
   fonts"; one file per ok row. Concurrent aerenders: one output folder each.
7. **Verify by decoding, write the status back, resume.** Count decoded frames per file
   (`ffprobe -count_frames`): truncated files keep the frame count of their header [added, live
   27.0]. Write one status row per data row ([scripts/ledger.py](scripts/ledger.py) from the guard's
   output, or `AEX.batch.writeCsv`: id, `done` or `failed`, file, reason) next to the renders, never
   over the person's data file. After a crash or a full disk, `AEX.batch.resumeQueue(verifiedNames)`
   on the saved copy requeues only what failed; save, rerun (procedures.md section 11). GATE:
   decoded frames equal the comp for every `done` row; `ok + failed = rows`; a resumed run renders
   only the missing rows and leaves verified files untouched.

## Numbers

| Value                      | Meaning                                                                                                  |
| -------------------------- | -------------------------------------------------------------------------------------------------------- |
| 60 % of designed font size | fit floor before a row fails (relative to the master's size)                                             |
| 84 % of comp width         | max text width used in the live job (8 % margin per side)                                                |
| 5 % of frame               | `AEK.text.inFrame` margin for title-safe checks                                                          |
| 3 rows                     | stress rows rendered before the batch                                                                    |
| 2 x estimate               | free space needed on the output volume (estimate = bytes per frame of the stress render x frames x rows) |
| 120 s                      | no log output before the watchdog stops `aerender`                                                       |
| 0.6                        | second text line size over the first, at least, in a card or lower third                                 |

## Quality gates

Measurable:

- Report: `ok + failed = rows`; each failure has a reason a person can act on ("Image not found:
  path", "Text overflow on TITLE: 955 px > 454 px at the 38 px floor").
- Queue: one item per ok row, status QUEUED before the render and DONE after; `isValid(om)` before
  reuse.
- Files: `ae.py probe` per output: codec, width, height, fps, frames equal the comp and work area;
  then a decoded frame count (`ffprobe -count_frames`) equal to the comp, because header values
  survive a truncated file.
- `aerender`: `RESULT ok` or `ok` true; each file decodes its full frame count; the exit code alone
  proves nothing.
- Status file: one row per data row, `done` only where the decode count passed.
- Master: text, precomp and footage of the master read back unchanged after the batch. Visual (one
  contact sheet of every built version at the hold frame, failed rows included):
- Text inside the margin, nothing clipped, no line collision; the right language and logo per row.
- Portrait and square versions read as designed layouts, not a shrunken landscape strip.
- Failed rows show the defect the report names.
- Cards and lower thirds: the plate leaves with its text (no frame of an open plate without it); the
  template's picture checks in [references/critique.md](references/critique.md).

## Common mistakes

| Mistake                                                   | Symptom                                                               | Fix                                                                 |
| --------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Editing a precomp inside a plain `duplicate()`            | Every version and the master change                                   | `AEX.batch.deepDuplicate` (copies nested comps, relinks layers)     |
| Trusting the duplicate's name                             | `MASTER_16x10` appears                                                | Set `name` right after `duplicate()`                                |
| Template name from memory or another machine              | "is not a valid template name"                                        | Check `om.templates` and `rqi.templates` first                      |
| Output folder not created                                 | `render()` throws "Directory does not exist"                          | `AEK.core.ensureFolder` before queueing                             |
| Shrinking text until it fits                              | Unreadable 18 px titles                                               | Floor at 60 %, then fail the row                                    |
| Reading `aerender` exit code                              | Bad comp name or full disk reported as success                        | Grep the log, decode the file                                       |
| Rendering without a free-space check                      | Exit 0 and a short or empty file                                      | `AEX.batch.diskCheck` first, then `render_guarded.sh`               |
| Rerunning the saved `.aep` to resume                      | Every item renders again: `aerender` never writes DONE back           | `AEX.batch.resumeQueue` with the files that passed the decode count |
| A Cinema 4D renderer comp (`ADBE Ernst`) under `aerender` | No file, or "Couldn't find a result file"                             | Switch to Classic 3D or Advanced 3D (`ADBE Calder`) before saving   |
| A render node without the project's fonts                 | Substitute font in the output; "Project has missing fonts" in the log | Preflight on each node, test `font.isSubstitute`                    |

More rows (resize, data cells, ES3, dialogs, output modules):
[references/critique.md](references/critique.md), "More mistakes".

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

## Version notes

- Native H.264 in the Render Queue since 23.0; Media Encoder is optional.
  `renderQueue.queueInAME(bool)` exists (14.0); `canQueueInAME` is false until an item is QUEUED; it
  sends items with Media Encoder's last used preset.
- `TextDocument.boxOverflow` and `boxAutoFitPolicy` 24.6; `app.fonts` 24.0; `characterRange` 24.3;
  `Layer.id` 22.0; guide enums changed integers in 26.5 (compare constants).
- MFR is on by default since 22.0; `-mfr ON|OFF max_cpu_percent` sets it per `aerender` run
  (procedures.md section 5).
- UXP is a public beta in After Effects (Beta) 27.1; CEP is off by default from December 2028;
  ExtendScript and ScriptUI keep working. The C++ SDK is for native effects, not pipelines.

## References

- [references/procedures.md](references/procedures.md): full jobs (CSV, versioning, render queue,
  aerender, MOGRT, deep duplicate), channel, checked line, what to check.
- [references/expert-notes.md](references/expert-notes.md): principles by expert with timestamps,
  and Templater, Plainly and nexrender compared.
- [references/critique.md](references/critique.md): rubric with numbers and the contact sheet
  checklist.
- [references/gui-paths.md](references/gui-paths.md): menus and panels for the same steps.
- [references/sources.md](references/sources.md): every source, best timestamps.
- [scripts/batch.jsx](scripts/batch.jsx): `AEX.batch` helpers (readCsv, readJson, validate,
  deepDuplicate, setText, importOnce, swapImage, resize, queue, renderOnly, resumeQueue, eachRow,
  fill, writeText, writeCsv, freeSpace, diskCheck, renderManifest).
- [scripts/ledger.py](scripts/ledger.py): status file from the build report and the guard's per-file
  frame counts.
- [scripts/render_guarded.sh](scripts/render_guarded.sh): whole-queue `aerender` with a free-space
  floor, a stall watchdog, and a per-file frame count against the log span or the manifest.
