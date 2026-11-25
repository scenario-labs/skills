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
- `saveFrameToPng` honors motion blur and works with the app in the background. It is asynchronous:
  `AEK.capture.frame` waits for the file.

## P6 Preview render without touching the person's queue

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// ARGS: {comp: "MAIN_spot", out: "<abs file>.mp4"}
var st = AEK.session.state(), c = AEK.core.comp(ARGS.comp);
var r = AEK.capture.queue(c, ARGS.out, { template: "H.264 - Match Render Settings - 15 Mbps", start: c.workAreaStart, duration: c.workAreaDuration });
return { render: r, queueBefore: st.queue, queueAfter: AEK.session.state().queue };
```

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
- `probe` returns codec, profile, size, frame rate, frame count, pixel format and an `alpha` flag.
  Compare each with the brief.

## P8 When After Effects stops answering

1. `ae.py doctor`: read `status.age_s` and `windows`.
2. One window and a recent job that renders: wait. The heartbeat stops during a render.
3. An extra window: `ae.py windows --shot <folder>`, then look at the picture.
4. A dialog drawn by After Effects (Crash Repair Options, the disk cache warning, the Home screen):
   `ae.py key return` or `ae.py key escape`.
5. A script alert, a save panel or a macOS privacy prompt: tell the person which window is open.
   Nothing closes it from outside when the app is in the background.
6. After a restart, read the result of the job that was running: it comes back with
   `interrupted: true` and is not run again. Check the project state before sending anything else.

## P9 Report

Give, in this order:

1. What changed: the diff in numbers, and the name of the undo step.
2. What was skipped and why (missing file, several matches, locked item left alone).
3. Findings that need the person: clips shorter than their placeholder, enlarged footage, text that
   grew, audit errors.
4. Files written: review frames, contact sheet, renders, safety copy.
5. Assumptions: frame rate, fit mode, font mapping, which comps were in scope.
6. Time taken per stage.
