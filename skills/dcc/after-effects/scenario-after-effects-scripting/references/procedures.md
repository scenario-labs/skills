# Procedures: scripting and automation

Every job below is the body of a function for
`ae.py run job.jsx --lib scripts/batch.jsx --args '{...}'`. `ARGS` holds absolute paths. Jobs marked
`live 27.0` were run on After Effects 27.0 (build 27.0x78) on macOS; the test versions began with
`AEK.core.fresh()` and built their own master, the versions here open nothing and work on the open
project.

Rules for every job in a person's session:

- Never call `app.open()` or `app.newProject()` while the open project has unsaved changes: a native
  Save As panel blocks the app and nothing can close it from outside. A batch that switches projects
  closes the current one with an explicit `app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES)` or
  `SAVE_CHANGES`, and only with the owner's word.
- Never `alert`, `confirm`, `prompt` or a file dialog. Return messages.
- Build versions in new comps and bins; never edit or delete the master or a person's layers. Failed
  versions go to a `_FAILED` bin.

## 1. Preflight: templates, master, fonts, assets, renderer

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {master, om, rs, fonts: ["Helvetica-Bold"], assets: ["/abs/logo_en.png"]}
var m = AEK.core.comp(ARGS.master), r = { problems: [] }, i, all, f;
var t = AEK.capture.templates(m);
function has(list, name) { for (var k = 0; k < list.length; k++) { if (list[k] === name) { return true; } } return false; }
if (!has(t.outputModule, ARGS.om)) { r.problems.push("output module template missing: " + ARGS.om); }
if (!has(t.renderSettings, ARGS.rs)) { r.problems.push("render settings template missing: " + ARGS.rs); }
for (i = 0; i < ARGS.fonts.length; i++) {
    f = app.fonts.getFontsByPostScriptName(ARGS.fonts[i]);
    // after a reopen a missing font comes back as a substitute object (length 1)
    if (!f.length || f[0].isSubstitute) { r.problems.push("font not installed: " + ARGS.fonts[i]); }
}
r.flaggedFonts = app.fonts.missingOrSubstitutedFonts.length;
for (i = 0; i < ARGS.assets.length; i++) { if (!new File(ARGS.assets[i]).exists) { r.problems.push("asset missing: " + ARGS.assets[i]); } }
all = AEK.core.comps();
for (i = 0; i < all.length; i++) { if (all[i].renderer === "ADBE Ernst") { r.problems.push("Cinema 4D renderer under aerender: " + all[i].name); } }
var au = AEK.audit.all();
for (i = 0; i < au.length; i++) { if (au[i].severity === "error") { r.problems.push(au[i].rule + " " + au[i].where + ": " + au[i].message); } }
r.writeAllowed = app.preferences.getPrefAsLong("Main Pref Section v2", "Pref_SCRIPTING_FILE_NETWORK_SECURITY") === 1;
return r;
```

Check: `problems` is empty and `writeAllowed` is true. Run the same job on every render node: fonts,
effects and encoders must exist on each machine (aerender doc). Measured: with a font that is not
installed and one comp set to `ADBE Ernst`, `problems` held exactly "font not installed:
NoSuchFont-Bold" and "Cinema 4D renderer under aerender: EXTRUDED"; 62 ms. `ADBE Ernst` is the
Cinema 4D renderer; `ADBE Advanced 3d` is Classic 3D and `ADBE Calder` Advanced 3D, both safe under
`aerender` (nexrender README). On a clean 27.0 install the output module list holds
`H.264 - Match Render Settings -  5 Mbps` (two spaces), `H.264 - Match Render Settings - 15 Mbps`,
`H.264 - Match Render Settings - 40 Mbps`, `High Quality`, `High Quality with Alpha`, `Lossless`,
`Lossless with Alpha`, `Alpha Only`, `AIFF 48kHz`, `Multi-Machine Sequence`, `Photoshop`,
`TIFF Sequence with Alpha`. `AEK.capture.templates` adds a render queue item and removes it.

## 2. Read the data (CSV in ES3)

```javascript
// channel: bridge
// checked: live 27.0
var csv = AEX.batch.readCsv(ARGS.csv), bad = [], i;
for (i = 0; i < csv.rows.length; i++) { if (csv.rows[i]._error) { bad.push(csv.rows[i]._line + ": " + csv.rows[i]._error); } }
return { header: csv.header, rows: csv.rows.length, bad: bad, first: csv.rows[0], name: AEX.batch.fill("{id}_{lang}_{ratio}_v001", csv.rows[0]) };
```

Check: header names equal the column names the job uses, case included; `bad` is empty. Measured: a
file saved as UTF-8 with a BOM reads without the BOM through `File.read()` with
`encoding = "UTF-8"`. Quoted fields with commas, doubled quotes and an embedded line break came back
intact (`"""Le jeu"", sur iOS, Android"` read as `"Le jeu", sur iOS, Android`). `_line` is the
record number, not the physical line, when a field holds a line break. JSON data:
`AEK.json.parse(AEX.batch.readText(path))`. ExtendScript has no `JSON` object.

Validate before any build: controlled values and limits (Ov4Zd-Mgmbo 00:03:49; uo5k4_vu5Vk
00:16:06).

```javascript
// channel: bridge
// checked: live 27.0
var csv = AEX.batch.readCsv(ARGS.csv);
var problems = AEX.batch.validate(csv, {
    required: ["id", "status", "lang", "ratio", "title"],
    allowed: { status: ["ready", "done", "hold"], ratio: ["16x9", "9x16", "1x1"], lang: ["en", "fr", "de"] },
    maxLength: { title: 40 },
    unique: ["id"]
});
return { problems: problems };
```

Measured on a 5-row file: "status 'Ready' is not one of ready, done, hold" (case counts), "ratio
'4x5' is not one of 16x9, 9x16, 1x1", "lang 'es' ...", "title has 52 characters, limit 40", "Empty
title", "Duplicate id 'r01' (also line 2)". A header `TITLE` asked for on a file whose column is
`title` returned only "Missing column: TITLE" at line 1. Build only when `problems` is empty, or set
the listed rows aside with these reasons in the report.

ES3 facts measured on 27.0: `[].indexOf`, `"".trim`, `JSON` and `Date.prototype.toISOString` are
undefined; `toSource()`, `$.getenv("HOME")`, `generateRandomNumber()` and `String.replace` with a
function work; `app.isUISuppressed` is a Boolean property (false in the interactive app).

## 3. End-to-end versioning job

One master end card (BG solid, LOGO precomp holding the logo image, TITLE and SUB text). Per row:
deep copy, fill, swap the logo, resize to the ratio, fit and check text, queue with a named output.
Then render the first three and capture a frame of every version.

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {csv, assets, out, master, om, rs, rule: "short", renderFirst: 3}
var SIZES = { "16x9": [960, 540], "9x16": [540, 960], "1x1": [540, 540] };
var m = AEK.core.comp(ARGS.master), OUT = ARGS.out;
var rows = AEX.batch.readCsv(ARGS.csv).rows;
var cache = {}, bin = AEK.core.bin("VERSIONS"), failBin = AEK.core.bin("_FAILED"), queued = [], j, frames = [];
var rep = AEX.batch.eachRow(rows, function (row) {
    var size = SIZES[row.ratio], built = null;
    if (!size) { throw new Error("Unknown ratio '" + row.ratio + "'"); }
    try {
        built = AEX.batch.deepDuplicate(m, "_" + row.id, bin).comp;
        AEX.batch.setText(built.layer("TITLE"), row.title);
        AEX.batch.setText(built.layer("SUB"), row.subtitle);
        AEX.batch.swapImage(built.layer("LOGO").source.layer(1), AEX.batch.importOnce(ARGS.assets + "/" + row.logo, cache), [400, 400]);
        var rz = AEX.batch.resize(built, size[0], size[1], ["BG"], ARGS.rule);
        var res = { comp: built.name, size: [built.width, built.height], skipped: rz.skipped, text: {} }, names = ["TITLE", "SUB"], i, l, fit, inf, size0;
        for (i = 0; i < names.length; i++) {
            l = built.layer(names[i]);
            size0 = l.property("ADBE Text Properties").property("ADBE Text Document").value.fontSize;
            fit = AEK.text.fit(l, built.width * 0.84, { minSize: Math.round(size0 * 0.6), step: 2 });
            inf = AEK.text.inFrame(l, built, 0.05, 1.5);
            res.text[names[i]] = { size: fit.size, width: Math.round(fit.width), max: Math.round(fit.maxWidth), inFrame: inf.ok };
            if (fit.overflow || !inf.ok) { throw new Error("Text overflow on " + names[i] + ": " + Math.round(fit.width) + " px > " + Math.round(fit.maxWidth) + " px at the " + fit.size + " px floor"); }
        }
        res.file = OUT + "/" + AEX.batch.fill("{id}_{lang}_{ratio}_v001", row) + ".mp4";
        queued.push(AEX.batch.queue(built, res.file, { om: ARGS.om, rs: ARGS.rs }));
        return res;
    } catch (e) {
        if (built) { built.parentFolder = failBin; built.name = built.name + "_FAILED"; }
        throw e;
    }
});
var first = queued.slice(0, ARGS.renderFirst || 3);
var ren = AEX.batch.renderOnly(first);
for (j = 0; j < queued.length; j++) { frames.push(AEK.capture.frame(queued[j].comp, 1.5, OUT + "/f_" + queued[j].comp.name + ".png").path); }
var failed = AEK.core.items(function (it) { return it.parentFolder === failBin; });
for (j = 0; j < failed.length; j++) { frames.push(AEK.capture.frame(failed[j], 1.5, OUT + "/f_" + failed[j].name + ".png").path); }
AEX.batch.writeText(OUT + "/report.json", AEK.json.stringify({ ok: rep.ok, failed: rep.failed, render: ren }));
return { ok: rep.ok.length, failed: rep.failed, render: ren, frames: frames, stillQueued: queued.length - first.length };
```

Check:

- Live run, 6 rows (2 languages x 3 ratios): 4 built, 2 failed. `r04` "Text overflow on TITLE: 955
  px > 454 px at the 38 px floor" (a 53-character French title in 9:16), `r05` "Image not found:
  .../logo_missing.png". Three versions rendered DONE in 3.2 s; the fourth stayed QUEUED for the
  headless pass.
- The contact sheet shows the right logo per language, text inside the margin, and the failed rows'
  defects. `ae.py sheet OUT.jpg f1.png f2.png ...` fits frames of different sizes into one tile box
  (a 512x512, a 640x360 and a 360x640 frame came out on one 1944x652 sheet). ImageMagick `montage`
  fails on some machines without a default font: pass `-font` if you use it.
- Resize rule: with `"fit"` (each layer at the same fraction of the frame, scale `min(sx, sy)`) the
  9:16 version was a shrunken landscape strip with the title and subtitle far apart. With `"short"`
  (scale by the short side, offsets kept from the center) the block stayed compact and the title
  kept 60 of 64 px. For a portrait design that matters, author a portrait master and pick the master
  by ratio.

## 4. Render queue: names, settings, status

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {comp, out}
var c = AEK.core.comp(ARGS.comp), rq = app.project.renderQueue;
var rqi = rq.items.add(c), r = { statusNew: AEX.batch.statusName(rqi.status) };
var om = rqi.outputModule(1);
om.applyTemplate("H.264 - Match Render Settings - 15 Mbps");
AEK.core.ensureFolder(ARGS.out);
om = rqi.outputModule(1);
om.setSettings({ "Output File Info": { "Base Path": ARGS.out, "Subfolder Path": "", "File Template": "[compName]_[width]x[height].[fileExtension]" } });
om = rqi.outputModule(1);
r.file = om.file.fsName;
r.info = om.getSettings(GetSettingsFormat.STRING)["Output File Info"];
r.timeSpan = rqi.getSettings(GetSettingsFormat.STRING)["Time Span"];
rqi.skipFrames = 1;
var t0 = (new Date()).getTime();
rq.render();
r.blockedMs = (new Date()).getTime() - t0;
r.status = AEX.batch.statusName(rqi.status);
r.dupStatus = AEX.batch.statusName(rqi.duplicate().status);
return r;
```

Check and measured values:

- A new item is `NEEDS_OUTPUT` with output module `H.264 - Match Render Settings - 15 Mbps` already
  applied and an empty file.
- `[compName]_[width]x[height].[fileExtension]` resolved to `RQ_TEST_960x540.mp4`. Paths read back
  with a `/Volumes/<startup disk>` prefix on macOS.
- The Base Path folder is not created: without `ensureFolder`, `render()` threw "Error in output for
  render queue item 1, output module 1. Directory does not exist: ...".
- `render()` blocked 851 ms for 30 frames (skipFrames 1) of a 2 s 960x540 comp; status `DONE`;
  `rendering` false afterwards.
- `rqi.duplicate()` of a DONE item came back `NEEDS_OUTPUT` (the scripting doc says QUEUED). Set its
  file before rendering.
- `isValid(om)` stayed true after `applyTemplate` and `setSettings` on 27.0, but the renderqueue doc
  says the OutputModule object is invalidated after a setting change: re-fetch `rqi.outputModule(1)`
  after every change, as the job above does.
- Draft test render: `skipFrames = 1` renders every other frame (range 0 to 99); with a short
  `timeSpanDuration` it gives a fast look. Set `skipFrames = 0` and the full span back before the
  real render, or the file holds half the frames.
- Status values: WILL_CONTINUE 3012, NEEDS_OUTPUT 3013, UNQUEUED 3014 (`rqi.render = false`), QUEUED
  3015, RENDERING 3016, USER_STOPPED 3017, ERR_STOPPED 3018, DONE 3019.
- Render settings keys (STRING): `Quality`, `Resolution`, `Color Depth`, `Effects`, `Motion Blur`,
  `Frame Blending`, `Time Span`, `Time Span Start`, `Time Span Duration`, `Skip Existing Files`,
  `Proxy Use`, `Guide Layers`, `Solo Switches`, `Disk Cache`, `Frame Rate`.

Media Encoder:

```javascript
// channel: bridge
// checked: doc scripting-automation__ae-scripting-renderqueue-import.md
if (app.project.renderQueue.canQueueInAME === true) { app.project.renderQueue.queueInAME(false); }
```

`queueInAME` exists on 27.0 (typeof function, measured). `canQueueInAME` read false with only a
NEEDS_OUTPUT item and true once items were QUEUED (measured). The call launches Media Encoder, which
applies its most recently used preset; `true` also starts encoding. Prefer the native H.264 output
module (23.0+) for unattended runs.

## 5. Headless pass: save a copy, aerender, check

```javascript
// channel: bridge
// checked: live 27.0
app.project.save(new File(ARGS.out + "/batch.aep"));
return { saved: app.project.file.fsName, queued: app.project.renderQueue.numItems };
```

```bash
AER="/Applications/Adobe After Effects 2027/aerender"   # Windows: ...\Support Files\aerender.exe
# whole queue as saved: renders items QUEUED at save time with their own output modules; items DONE at save time are skipped
"$AER" -project "<project>/batch.aep" -mfr ON 100 -v ERRORS_AND_PROGRESS -log "<project>/aerender.log"
# the log separates lines with carriage returns: grep -c counts 1 for the whole file
grep -o "Finished composition" "<project>/aerender.log" | wc -l
grep -o "aerender ERROR[^.]*" "<project>/aerender.log" "<project>/stdout.txt"; grep -o "missing fonts" "<project>/aerender.log"
# one comp, one range, explicit output and template (through the runner)
python3 ae.py aerender --project "<project>/batch.aep" --comp "MASTER_r03" --out "<project>/renders/r03.mp4" --template "H.264 - Match Render Settings - 15 Mbps" --start 0 --end 29
for f in "<project>/renders/"*.mp4; do python3 ae.py probe "$f"; done
```

Measured:

- Whole-queue mode on the saved batch rendered only the one QUEUED item (60 frames, 540x540) in 6.1
  s wall time; the three DONE items were skipped. Progress lines go to `-log`, not stdout. After
  Effects also writes a `<project> Logs` folder next to the project.
- Output paths moved with the project: the item queued to `04b/r06...mp4` rendered to `05/r06...mp4`
  after the `.aep` was copied to `05/`. Queue items store paths relative to the project file.
- Single comp, frames 0 to 29 (`-e` is inclusive): 30 frames, 1.0 s, 5.1 s wall time.
- `-comp NO_SUCH_COMP` printed "aerender ERROR: No comp was found with the given name." and
  exited 0.
- The log uses carriage returns between lines: `grep -c "Finished composition"` returned 1 for a
  3-item run; `grep -o ... | wc -l` returned 3.
- `-mfr ON 100` was accepted in whole-queue mode (no error, 3 items in 2 s). The doc's whole-queue
  rule names only `-project`, `-log`, `-v`, `-mem_usage`, `-close` as used; MFR is on by default
  (22.0+). To know whether a CPU cap (`-mfr ON 50`) applies in whole-queue mode, time one heavy comp
  at 50 and at 100.
- Other flags (aerender doc): `-continueOnMissingFootage` logs and renders color bars in place of
  missing footage, so keep it out of a batch; `-reuse` renders in a running instance; `-sound ON`
  only plays a sound at the end.
- After a full run the saved `.aep` still read QUEUED on all three items: `aerender` closes with
  DO_NOT_SAVE_CHANGES, so a rerun renders everything again. Resume with section 11.
- `aerender` takes no script arguments. Build in the open app, save, then render. On macOS,
  `aerendercore` inside the app bundle is undocumented (Adobe Community answer); the bridge plus
  `aerender` covers the same need.

## 6. Shared precomps: deep copy or Essential Properties overrides

```javascript
// channel: bridge
// checked: live 27.0
var m = AEK.core.comp(ARGS.master), before = app.project.numItems;
var plain = m.duplicate();
var r = { plainName: plain.name, sharesPrecomp: plain.layer("LOGO").source === m.layer("LOGO").source };
plain.name = ARGS.master + "_plain";
var deep = AEX.batch.deepDuplicate(m, "_r01");
r.deepCopied = deep.copied; r.ownPrecomp = deep.comp.layer("LOGO").source !== m.layer("LOGO").source;
r.itemsAdded = app.project.numItems - before;
return r;
```

Measured: `duplicate()` added one item, kept 4 layers, the comp marker, the layer expression and the
Essential Graphics controller; nested precomp, solid source and footage were shared. An edit inside
the precomp showed in the master. The name became `MASTER_16x10` from `MASTER_16x9`, and the next
duplicate `MASTER_16x11`. `deepDuplicate` added 2 items (comp and `LOGO_PRE_r01`) and left the
footage shared, which is what a batch wants: one import per file.

When only text and media change, skip the copies: expose them on the precomp and set overrides per
instance.

```javascript
// channel: bridge
// checked: live 27.0
// CARD holds TITLE (text) and LOGO (footage layer); MAIN holds instances of CARD
var card = AEK.core.comp("CARD"), main = AEK.core.comp("MAIN");
card.layer("TITLE").property("ADBE Text Properties").property("ADBE Text Document").addToMotionGraphicsTemplateAs(card, "Title");
card.layer("LOGO").addToMotionGraphicsTemplateAs(card, "Logo");
// override names are the controller names given above, not localized display names
var inst = main.layer(ARGS.instance), ov = inst.property("ADBE Layer Overrides");
var tp = ov.property("Title"), td = tp.value; td.text = ARGS.text; tp.setValue(td);
var lp = ov.property("Logo");
if (lp.canSetAlternateSource) { lp.setAlternateSource(AEK.core.item(ARGS.logoItem)); }
return { title: ov.property("Title").value.text, logo: lp.alternateSource ? lp.alternateSource.name : null };
```

Measured: override match names are `ADBE EP Text Document` (text) and `ADBE Layer Source Alternate`
(media). Two instances of one precomp showed "Title" with the EN logo and "Jouez" with the FR logo;
the precomp's own text stayed "Title". `setAlternateSource` wraps the new footage in a one-layer
comp named `<controller>_<file>` (here `Logo_logo_fr`) inside a new `Media Replacement Comps`
folder: expect one extra comp per replaced file, and count items with that in mind.

## 7. Essential Graphics and MOGRT export

```javascript
// channel: bridge
// checked: live 27.0
var c = AEK.core.comp(ARGS.comp), t = c.layer("TITLE"), r = {};
var st = t.property("ADBE Text Properties").property("ADBE Text Document");
if (st.canAddToMotionGraphicsTemplate(c)) { r.title = st.addToMotionGraphicsTemplateAs(c, "Title"); }
AEK.build.effect(t, "ADBE Fill", {}, "Title Color");
r.color = t.property("ADBE Effect Parade").property("Title Color").property("ADBE Fill-0002").addToMotionGraphicsTemplateAs(c, "Title color");
if (c.layer("LOGO").canAddToMotionGraphicsTemplate(c)) { r.logo = c.layer("LOGO").addToMotionGraphicsTemplateAs(c, "Logo"); }
var mv = new MarkerValue("intro"); mv.duration = 0.5; mv.protectedRegion = true;
c.markerProperty.setValueAtTime(0, mv);
r.names = []; for (var i = 1; i <= c.motionGraphicsTemplateControllerCount; i++) { r.names.push(c.getMotionGraphicsTemplateControllerName(i)); }
c.motionGraphicsTemplateName = ARGS.name;
app.project.save(new File(ARGS.out + "/" + ARGS.name + "_src.aep"));
r.exported = c.exportAsMotionGraphicsTemplate(true, ARGS.out);
r.bytes = new File(ARGS.out + "/" + ARGS.name + ".mogrt").length;
return r;
```

Check: `exported` true and the file exists. Measured: no dialog when the project was saved first
(the scripting guide warns of a prompt otherwise); export took 1.2 s; 54 KB; the `.mogrt` is a zip
holding `project.aegraphic`, `definition.json`, `thumb.png`, `thumb.mp4`. Controller names came back
newest first (`Logo`, `Title color`, `Title`). The text color goes through a Fill effect
(`ADBE Fill-0002`, display name Color), as SkIOeqJEKD0 00:02:30 recommends. Without a folder
argument the file goes to the user's Essential Graphics folder.

## 8. Undo and errors in a batch

```javascript
// channel: bridge
// checked: live 27.0
app.beginUndoGroup("Batch: " + ARGS.rows.length + " rows");
var rep = AEX.batch.eachRow(ARGS.rows, function (row) {
    app.beginUndoGroup("row " + row.id);
    try { return { comp: AEK.build.comp("V_" + row.id, { width: 320, height: 180, duration: 1 }).name }; }
    finally { app.endUndoGroup(); }
});
app.endUndoGroup();
return rep;
```

Measured: nested groups collapse into the outer one; one Edit > Undo (`app.executeCommand(16)`)
removed the comps of all three rows. `ae.py run --undo NAME` gives the same single step without the
outer pair. A row that throws leaves what it already created: move it to `_FAILED`, never delete a
person's items. `app.project.replaceFont()` is not undoable (lead measurement): run it in its own
job after a saved copy.

Error messages measured on 27.0 (use them to classify failures):

| Call                                                | Result                                                                                                                               |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `comp.layer("NOPE")`                                | returns `null` (no throw); the next property access throws "null is not an object"                                                   |
| `importFile` on a missing path                      | "Path is not valid. Path: ..." (same with `beginSuppressDialogs`)                                                                    |
| `om.applyTemplate("unknown")`                       | "unknown is not a valid template name."                                                                                              |
| `layer.replaceSource(null, false)`                  | "Unable to call replaceSource because of parameter 1. null is not of the correct type."                                              |
| `items.addComp(name, 0, 0, ...)`                    | "Value 0 out of range 4 to 30000."                                                                                                   |
| `renderQueue.render()` with nothing queued          | returns at once                                                                                                                      |
| `boxAutoFitPolicy = BoxAutoFitPolicy.SHRINK_TO_FIT` | "Value is undefined": the enum is NONE, HEIGHT_CURSOR, HEIGHT_PRECISE_BOUNDS, HEIGHT_BASELINE (it grows the box, never shrinks text) |

## 9. Paragraph overflow without measuring

```javascript
// channel: bridge
// checked: live 27.0
var l = AEK.core.comp(ARGS.comp).layer(ARGS.layer), d = l.property("ADBE Text Properties").property("ADBE Text Document").value;
return { overflow: d.boxOverflow, boxSize: d.boxTextSize, inkHeight: l.sourceRectAtTime(0, false).height };
```

Measured: a 400x120 box at 48 px Helvetica Bold with 62 characters reported `boxOverflow` true while
`sourceRectAtTime` height was 102.6 px, inside the box; 15 characters reported false.

## 10. Hand the job to a person

`ae.py run batch_job.jsx --channel handoff --args '{...}'` writes one complete `.jsx`. The person
runs File > Scripts > Run Script File; the script writes `report.json` next to the renders. Use it
when the bridge is not installed on that machine.

## 11. Verify, write the status back, resume after a crash

The saved project cannot tell what rendered: `aerender` never saves it. The files on disk are the
truth, checked by decoding.

```bash
# per expected output: decoded frame count must equal the comp's (30 for 1 s at 30 fps)
for f in "<project>/renders/"*.mp4; do
  n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$f")
  echo "$(basename "$f") $n"
done
```

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {verified: ["v1.mp4"]} file names whose decode count passed; run on the saved batch copy
var res = AEX.batch.resumeQueue(ARGS.verified);
app.project.save();
return res;
```

Then run `aerender` on the same file again and decode-count the new files.

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {csv, out, done: ["r01", "r02"]} one status row per data row, next to the renders
var csv = AEX.batch.readCsv(ARGS.csv), rows = [], i, k, st;
for (i = 0; i < csv.rows.length; i++) {
    st = "failed";
    for (k = 0; k < ARGS.done.length; k++) { if (ARGS.done[k] === csv.rows[i].id) { st = "done"; } }
    rows.push({ id: csv.rows[i].id, status: st, file: AEX.batch.fill("{id}_{lang}_{ratio}_v001", csv.rows[i]) + ".mp4", reason: "" });
}
return AEX.batch.writeCsv(ARGS.out + "/status.csv", ["id", "status", "file", "reason"], rows);
```

Measured on 27.0 (3 items of 1 s, H.264, whole-queue `aerender`):

- After the first run the saved `.aep` read QUEUED, QUEUED, QUEUED.
- One output moved away and one cut to its first 3,000 bytes. `ae.py probe` on the cut file still
  reported 30 frames and 1.0 s from the header; `ffprobe -count_frames` gave N/A and
  `ffmpeg -i f -f null -` printed "partial file". The intact file decoded 30 frames.
- `resumeQueue(["v1.mp4"])` returned skipped `v1.mp4`, requeued `v2.mp4` and `v3.mp4`, renamed
  `v3.mp4.incomplete`; statuses UNQUEUED, QUEUED, QUEUED. The second `aerender` run finished V2 and
  V3 only; `v1.mp4` kept its modification time; all three decoded 30 frames.
- `writeCsv` quoted a reason holding a comma and quotes (`"... 955 px > 454 px, ""quoted"""`) and
  `readCsv` read it back intact.
- File names are compared without their folder because paths read back with a
  `/Volumes/<startup disk>` prefix on macOS; keep output names unique per row. To show the status in
  the person's sheet, they import or reference `status.csv` (the ledger pattern of Ov4Zd-Mgmbo
  00:11:25 to 00:11:57); set a row back to `ready` to rerun it.
