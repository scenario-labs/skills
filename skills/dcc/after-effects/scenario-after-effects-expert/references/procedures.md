# Procedures (lead)

Every job below is the body of a function for `ae.py run`. `ARGS` carries absolute paths. Jobs
marked `checked: live 27.0` ran in After Effects 27.0 on macOS through the bridge.

## P1 Connect

```bash
python3 scripts/ae.py doctor
python3 scripts/ae.py install-bridge      # once; then restart After Effects or run the file from File > Scripts > Run Script File
python3 scripts/ae.py run -e "return AEK.core.info();"
```

Check in the `doctor` output:

- `checks` holds three `ok` lines: startup bridge, the scripting preference, bridge alive.
- `ok` is false when any check reads `FAIL`. An unreadable preferences file gives
  `WARN scripting preference not readable`: check the setting by hand.
- `status.age_s` is under 6. Above that, After Effects is busy or a dialog is open.
- `windows` lists one main window. A second window is usually a dialog.

If the bridge cannot be installed, use `--channel handoff`: the runner writes one `.jsx` and names
the result file. The person runs it from File > Scripts > Run Script File.

## P2 Inspect, read-only

```bash
python3 scripts/ae.py info      # version, project path, dirty flag, bit depth, working space, expression engine, active comp
python3 scripts/ae.py audit     # findings: {severity, rule, where, message}
python3 scripts/ae.py stats     # counts per project and per comp
```

Audit rules: `project.unsaved`, `project.bpc`, `project.workingSpace`, `project.expressionEngine`,
`footage.missing`, `footage.unused`, `footage.cloud`, `comp.defaultName`, `comp.empty`,
`comp.oddSize`, `comp.mixedFrameRates`, `layer.frameRateMismatch`, `layer.upscaled`,
`effect.missing`, `expression.error`, `expression.disabled`, `fonts.missing`, `fonts.flagged`.

Read the errors first. An `effect.missing` or `fonts.missing` finding changes the plan before any
work starts.

## P3 Safety copy

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ARGS: {stamp: "20261125_1012"}. Copies the last SAVED state. The open project does not move.
var p = app.project, res = { saved: !!p.file, dirty: p.dirty, copy: "" };
if (p.file) {
    var name = decodeURI(p.file.name).replace(/\.aep$/i, ""), dst = new File(p.file.parent.fsName + "/" + name + "_before_agent_" + ARGS.stamp + ".aep");
    if (!dst.exists && p.file.copy(dst.fsName)) { res.copy = dst.fsName; }
}
return res;
```

- `dirty` false: the copy is the full state. Proceed.
- `dirty` true: the copy lacks the unsaved changes. Ask the person to run File > Increment and Save,
  or run it for them on their word: `app.executeCommand(3088)`. On 27.0 it wrote `<name> 2.aep`
  beside the original with no dialog and left the original file untouched. The open project then
  points at the new file.
- Never saved (`saved` false): there is no file to increment. Ask the person to save the project
  first, then take the copy.
- Never call `app.project.save()` on the person's file. It writes their unsaved changes without
  asking.

## P4 Change inside one undo step

Run with `--undo "Agent: swap PH placeholders, set title font"`. The whole job becomes one entry in
Edit > Undo.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ARGS: {footage: "<abs folder>", out: "<abs folder>", font: "AvenirNext-Regular", fontBold: "AvenirNext-Bold", from: "Georgia", fromBold: "Georgia-Bold"}
var R = {}, st = AEK.session.state(), before = AEK.stats.snapshot();
var found = AEK.session.named("PH_"), names = [], seen = {}, i, k, d, l, items = {}, map = {};
for (i = 0; i < found.length; i++) { k = found[i].name.substring(3); if (!seen[k]) { seen[k] = true; names.push(k); } }
var files = AEK.session.matchFiles(names, ARGS.footage);
R.swapped = []; R.skipped = [];
for (i = 0; i < found.length; i++) {
    k = found[i].name.substring(3);
    if (!files[k]) { R.skipped.push({ layer: found[i].name, comp: found[i].comp, why: "no file named " + k }); continue; }
    if (files[k].length > 1) { R.skipped.push({ layer: found[i].name, comp: found[i].comp, why: "several files match: " + files[k].join(", ") }); continue; }
    if (!items[k]) { d = AEK.xio.importFile(files[k][0], { bin: "agent_swap" }); items[k] = app.project.itemByID(d.id); }
    l = app.project.itemByID(found[i].compId).layer(found[i].index);
    R.swapped.push(AEK.session.swap(l, items[k], { fit: "cover", bin: "agent_swap" }));
}
if (!AEK.text.fontExists(ARGS.font) || !AEK.text.fontExists(ARGS.fontBold)) { throw new Error("Font not installed: " + ARGS.font + " / " + ARGS.fontBold); }
map[ARGS.from] = ARGS.font; map[ARGS.fromBold] = ARGS.fontBold;
R.fonts = AEK.session.setFont(ARGS.font, { map: map });
R.diff = AEK.stats.diff(before, AEK.stats.snapshot());
R.audit = AEK.audit.summary(AEK.audit.all());
var main = app.project.itemByID(st.activeId);
R.frames = AEK.capture.spread(main, 3, ARGS.out, "check");
R.restored = AEK.session.restore(st);
return R;
```

What to check in the result:

- Every `swapped` row has `changed: []`: in point, out point, start time, stretch, parent, effects,
  masks, key count and expression count are the same as before.
- `mode` is `direct` when the clip has the placeholder's size and covers its length. Otherwise
  `fitComp`: the clip sits in a comp named `FIT_<layer>_<comp>` at the placeholder's size, scaled to
  cover.
- `shortByFrames` above 0: the clip ends before the placeholder does. Report it. The choices (freeze
  the last frame, loop, slow down, shorten the layer) belong to the person.
- `upscaled` true (`scale` above 105): the clip is smaller than the placeholder. Report it, or route
  to scenario-after-effects-generation for an upscale.
- `skipped` lists placeholders with no file or several files. Never guess between two files.
- `fonts` rows give `from`, `to`, `widthBefore`, `widthAfter` and `growthPct`. A row above 0 % can
  overflow: check it with `AEK.text.inFrame(layer, comp, 0.05, t)` (margin as a fraction of the
  frame).
- A row with `keys` above 0 had its font set on every Source Text key. A row with `expression: true`
  may ignore the change: read the expression.
- `diff` shows the new items (imported clips, fit comps, one bin) and nothing else.

Measured on the test project (4 placeholders in 2 comps, 3 text layers, 3 frames): 1.2 s. Edit >
Undo once (`app.executeCommand(16)`) restored the solids, the fonts and the item count.

## P5 Frames and one contact sheet

```bash
python3 scripts/ae.py frames "MAIN_spot" --times 1,3,4.5 --out <review folder> --sheet
python3 scripts/ae.py sheet <review folder>/sheet.jpg <review folder>/a.png <review folder>/b.png --columns 3
```

- Capture at the beats (first frame of each element at rest, the peak of each move, the last hold),
  not at even spacing only.
- For motion, capture 6 to 8 consecutive frames around a settle and read the spacing.
- Read the sheet. A sheet that was not opened verifies nothing.
- Sheets are scaled down to 1600 px wide by default. Pass `--max-width 0` to keep full-size tiles
  when you need to inspect a detail.
- `saveFrameToPng` honors motion blur and works with the app in the background. It is asynchronous:
  `AEK.capture.frame` waits until the file exists and its size holds for 150 ms (a large 16-bit PNG
  can appear before it is complete).
- `ae.py frames` captures from the project open at that moment. On an After Effects shared by
  several agents, another job can open its own project between your build and your capture. Capture
  inside the job that opened or built the project:

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {aep: "<abs>.aep", comp: "MAIN", out: "<abs folder>"}. Open, check, capture and report in one job.
AEK.core.open(ARGS.aep);
var c = AEK.core.comp(ARGS.comp);
return { project: app.project.file.fsName, frames: AEK.capture.spread(c, 6, ARGS.out, "review") };
```

- From the terminal, `ae.py frames "MAIN" --out <folder> --project <abs>.aep` refuses to capture
  when another project is open. `ae.py templates "MAIN" --project <abs>.aep` does the same for the
  template list.
- The comp background is transparent in the PNG (alpha 0; the comp color stays in RGB at 8 bpc, RGB
  reads 0 at 16 bpc). `ae.py frames --sheet` flattens on it; for `ae.py sheet`, pass `--bg RRGGBB`
  (the `bg` field of each captured frame). Without it, feathered and glowing edges read too bright
  on the sheet. Before measuring pixels on a PNG yourself:
  `magick f.png -background '#<bg>' -flatten out.png`.
- From a delivered movie: `ae.py sheet <out>.jpg --video <file>.mp4 --at 0,12,30,74` cuts those
  frames (full range) and labels them.

## P6 Preview render without touching the person's queue

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ARGS: {comp: "MAIN_spot", out: "<abs file>.mp4"}
var st = AEK.session.state(), c = AEK.core.comp(ARGS.comp);
var r = AEK.capture.queue(c, ARGS.out, { template: "H.264 - Match Render Settings - 15 Mbps", start: c.workAreaStart, duration: c.workAreaDuration });
return { render: r, queueBefore: st.queue, queueAfter: AEK.session.state().queue };
```

- `ae.py render` returns `ok: false` with `why: "probe"` when ffprobe cannot read the file.
- `queueBefore` and `queueAfter` must be equal. On 27.0 a person's `QUEUED` item stayed `QUEUED`
  with `render: true`, and its output file was not written.
- `renderQueue.render()` blocks the app until it ends. Keep previews short, or use P7.
- List the templates that exist on the machine with `ae.py templates "<comp>"`. Template names
  differ between installs. One built-in name has two spaces:
  `H.264 - Match Render Settings -  5 Mbps`.

## P7 Headless render of a saved project

```bash
python3 scripts/ae.py aerender --project <project>.aep --comp "MAIN_spot" --out <renders>/MAIN_spot.mp4 --template "H.264 - Match Render Settings - 15 Mbps"
python3 scripts/ae.py probe <renders>/MAIN_spot.mp4
```

- `aerender` reads the file on disk. Unsaved changes are not in the render: render from the safety
  copy or after the person saves.
- It runs while the GUI app is open on the same machine (measured: 60 frames of a 1080x1920 comp,
  13.2 s wall time, exit code 0).
- The last lines read "Finished composition" and "Total Time Elapsed". Any other ending is a failure
  even with a file on disk.
- `ae.py aerender` checks what a full disk breaks. Read `ok` and `why`:
  - `disk`: under `--min-free-gb` (default 10 GB) free on the output volume before the start, a
    "Disk Full", "output module failed" or "(9988)" line, or a volume left under 50 MB. Free space,
    then render again.
  - `stall`: no output line for `--stall` seconds (default 300). aerender, its child and
    aerendercore are stopped. Raise `--stall` above the slowest frame time for heavy comps.
  - `timeout`: the render ran past `--timeout` seconds (no limit by default) and was stopped.
    aerender is also stopped when `ae.py` is interrupted.
  - `short`: the movie holds fewer frames (`ffprobe -count_packets`) than expected, or none. The
    expected count is `--frames N`, else the span from the log header (`Duration` and `Frame Rate`),
    else the highest PROGRESS frame. Measured on 27.0: a ProRes file cut at 1 MB on a full volume
    while aerender printed "Finished composition" and exited 0. "Failed to write XMP metadata" in
    the same log points to the disk.
  - `render`: an error line or a non-zero exit code.
  - `missing`: no output file.
  - `folder`: the output folder cannot be created. A missing folder is created first and returned as
    `created_folder`.
- One `ae.py aerender` call writes one file from one output module template. Two deliverables of one
  comp are two renders, or one master render and a conversion with ffmpeg.
- `checks` names each check (`free_space`, `stall`, `timeout`, `log_errors`, `returncode`, `file`,
  `frames`) with `ok`, `failed: ...` or `skipped: ...`. Read it to see which one failed. An audio or
  image output reads `frames: not counted`.
- On `render`, `missing` or `short` only, the result carries `retry`: rerun once, alone. Two
  aerenders that write into one output folder at the same time collide: one exits 0 with "Can not
  create a file in directory ... Try checking write permissions" and no file. Measured on 27.0: 5 of
  6 pairs lost one render; with one output folder each, 6 of 6 rendered.
- `frames_rendered`, `frames_span`, `free_gb_before` and `free_gb_after` come back in every result.
  `--frames N` sets the count the file must hold.
- A whole render queue (no `--comp`) goes through the scripting skill's `render_guarded.sh`. Both
  treat as failed: an error line, a non-zero exit, a missing file, a movie that decodes short.
- `probe --count` returns codec, profile, size, frame rate, header and counted frames, pixel format,
  `alpha`, and `timecode` on a data track. Compare each with the brief.
- The "High Quality" output modules write a timecode track. Drop it in a later ffmpeg pass with
  `-map 0:v:0 -dn -write_tmcd 0`.

## P8 When After Effects stops answering

1. `ae.py doctor`: read `status.age_s` and `windows`.
2. One window and a recent job that renders: wait. The heartbeat stops during a render and during
   another agent's long job.
3. An extra window: `ae.py windows --shot <folder>`, then look at the picture.
4. A dialog drawn by After Effects (Crash Repair Options, the disk cache warning, the Home screen):
   `ae.py key return` or `ae.py key escape`.
5. A script alert, a Save As or file panel, or a macOS privacy prompt: keys posted to a background
   app do not close it. In a person's session, tell them which window is open and wait.
6. Unattended test session only (no person works in this After Effects), heartbeat older than 180 s:
   `ae.py restart --test-session`. The operator who sets up the session also sets
   `AE_AGENT_TEST_SESSION=1` in the environment; an agent never sets it. It refuses without it,
   while the heartbeat is younger, while another agent restarts (lock folder in the bridge folder)
   and within 5 minutes of the last restart. It stops the app, relaunches it in the background
   (`open -g`, no focus taken), answers Crash Repair with Return and waits for the heartbeat.
   Measured end to end: 13 s from stop to the first heartbeat (new process at 1 s, Return at 10 s),
   front app unchanged, next job ok. It waits for the old process to exit before `open -g` (an
   `open` sent right after the stop starts nothing) and retries `open` up to three times. Unsaved
   work in the open project is lost: never in a person's session.
7. After a restart, read the result of the job that was running: it comes back with
   `interrupted: true` and is not run again. Check the project state before sending anything else.
8. `interrupted: true` while the After Effects process did not change: an instance started by
   `aerender` ran the bridge's startup sweep (bridge before 1.5.0). The runner keeps waiting for the
   job's own result and marks it `recovered_after_sweep`. Bridge 1.5.0 does not start inside an
   `aerender` instance; reinstall it with `ae.py install-bridge` and restart After Effects when no
   job runs.

### Several agents on one After Effects

A Save As panel raised by one job stops every agent. Rules for test sessions where several agents
share one application:

- Each job is self-contained: it opens its own project with `AEK.core.open(path)` or starts one with
  `AEK.core.fresh(path)`. Both close whatever is open WITHOUT saving, whoever left it dirty, so no
  panel can open.
- `fresh(path)` saves the new project at once: it has a file and no unsaved changes.
- Every job ends with `AEK.core.save(path)` (or `AEK.core.save()` on a project that has a file). A
  job that leaves an untitled project with unsaved changes gets a `warning` in its result.
- Never call `app.open`, `app.newProject` or `app.project.save()` directly: `ae_check.py` reports
  them as errors and `ae.py run` refuses to send the job (`--no-preflight` overrides, for a person
  who has saved).
- Capture frames, read templates and save inside the job that opened the project. Between two calls
  another agent's project is open.
- Never close or save a project another agent opened, outside the open and fresh routes above. A
  person's session follows the Live session rules: no open, close or new project unasked.
- Renders run out of process (`ae.py aerender`), each into its own output folder.

## P9 Report

Give, in this order:

1. What changed: the diff in numbers, and the name of the undo step.
2. What was skipped and why (missing file, several matches, locked item left alone).
3. Findings that need the person: clips shorter than their placeholder, enlarged footage, text that
   grew, audit errors.
4. Files written: review frames, contact sheet, renders, safety copy.
5. Assumptions: frame rate, fit mode, font mapping, which comps were in scope.
6. Time taken per stage.

## P10 Starting curves and settle

Linear keys read as unfinished (Stance). Before handing motion to scenario-after-effects-animation,
these CSS cubic-bezier values through `AEK.motion.bezier(prop, k1, k2, [x1, y1, x2, y2])` give a
clean first pass:

| Move                      | Curve            | Note                        |
| ------------------------- | ---------------- | --------------------------- |
| Wipe, bar, line draw      | 0.65, 0, 0.35, 1 | ease in and out, symmetric  |
| Entrance, rise, scale up  | 0.16, 1, 0.3, 1  | fast start, long settle     |
| Exit                      | 0.7, 0, 0.84, 0  | slow start, leaves at speed |
| Tracking or blur settling | 0.22, 1, 0.36, 1 | long tail                   |

`AEK.motion.sample(prop, comp, t0, t1)` reads the move back per frame. `settleFrame` is the first
frame from which the value stays within 1 % of the travel from its end value. An eased move enters
that band before its last key: a rise keyed to frame 40 read `settleFrame` 31. Compare keys with
keys; use `settleFrame` for what the eye sees as stopped.
