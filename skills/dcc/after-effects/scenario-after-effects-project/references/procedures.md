# Procedures: project intake, hygiene and speed

Every job is a function body for `ae.py run job.jsx --lib <skill>/scripts/project.jsx` (bridge), or
the same text saved as one `.jsx` for a person to run from File > Scripts > Run Script File
(handoff, with the kit and the helper pasted in front by `ae.py run --channel handoff`). Paths come
from `ARGS` and are absolute. Every job that changes the project runs inside one undo group
(`--undo "Agent: <stage>"`).

Session rule: never open, close or switch projects in a person's session unasked. With unsaved
changes, opening or creating a project raises a Save As panel that blocks After Effects. Save first,
then open.

## 1. Freeze the received project and take an inventory

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {main: "Comp 1", dir: "<project>/aep", base: "BrandFilm"}
var main = AEK.core.comp(ARGS.main);
var frozen = AEX.project.saveVersion(ARGS.dir, ARGS.base + "_received"); // _received_v001.aep, never overwritten
var inv = AEX.project.inventory(main);
var lines = [];
for (var i = 0; i < inv.findings.length; i++) { lines.push(inv.findings[i].severity + " " + inv.findings[i].rule + " @ " + inv.findings[i].where); }
inv.findings = lines;
inv.frozen = frozen.saved;
return inv;
```

Read in the result: `missing` (with `missingFootagePath`), `missingFonts`, `defaultNames`,
`compRates`, `nestedRateMismatch`, `collapseRisks`, `unusedComps`, `unusedFootage`, `maxDepth`,
`audit` counts, `bpc`, `workingSpace`. On a test project with four default-named comps, three comp
rates, one moved file and one uninstalled font, the inventory returned all of them; the kit audit
alone missed the font and both nested rate mismatches.

Then capture the before sheet:

```bash
python3 ae.py frames "Comp 1" --spread 6 --out <project>/qc/before --sheet
```

## 2. Relink missing footage by file name

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {main: "Comp 1", roots: ["/Volumes/Drive B/Job", "<project>/footage"]}
var res = AEX.project.relink(ARGS.roots);
res.stillMissing = AEX.project.inventory(AEK.core.comp(ARGS.main)).missing.length;
return res;
```

`relink` reads `FileSource.missingFootagePath`, searches that exact file name breadth first under
each root (6 levels), and calls `replace()` (or `replaceWithSequence()` for a numbered image file).
Read `relinked[].missingNow` (false) and `notFound`. Live: a clip moved to another folder after save
came back missing on reopen; relink found it and `footageMissing` turned false. Check the relinked
shot on the after sheet: same name does not mean same take.

## 3. Missing fonts

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {fallback: "Helvetica-Bold"}
var before = AEX.project.missingFonts();      // usedFonts[i].font.isSubstitute
var fixed = before.length ? AEX.project.fixFonts(ARGS.fallback) : { replaced: [] };
return { before: before, fixed: fixed };
```

Live: a text layer set to `BrandSans-Black` (not installed), saved and reopened.
`app.fonts.getFontsByPostScriptName("BrandSans-Black").length` returned 1 (a substitute object),
`isSubstitute` returned true. `Project.replaceFont(from, to)` returned true and `stillMissing`
read 0. Replace only with a fallback the user approved; a brand font is installed, not replaced.
`aerender` prints "Project has missing fonts" on a project that still has one: grep its log as a
second check.

## 4. Color and bit depth

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {bpc: 16, workingSpace: "Rec.709 Gamma 2.4", linearize: false}
return AEX.project.color({ bpc: ARGS.bpc, workingSpace: ARGS.workingSpace, linearize: ARGS.linearize });
```

Live read-backs: 16 bpc, `Rec.709 Gamma 2.4`, gamma 2.4; 32 bpc with linearize true kept the working
space. An unknown name assigned directly (`app.project.workingSpace = "Not A Profile"`) threw
nothing and read back "None": `color()` validates against `listColorProfiles()` and throws instead.
New projects do not have fixed color defaults in a shared session (read 8 and 16 bpc, sRGB, on two
`newProject()` calls): always set and read back.

## 5. Conform comp frame rates

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {fps: 25, keepLow: ["PC_Stopmotion"]}
var list = [], comps = AEK.core.comps(), i, j, keep;
for (i = 0; i < comps.length; i++) {
    keep = false;
    for (j = 0; j < ARGS.keepLow.length; j++) { if (comps[i].name === ARGS.keepLow[j]) { keep = true; } }
    if (keep) { comps[i].preserveNestedFrameRate = true; } else { list.push(comps[i]); }
}
return { conformed: AEX.project.conformComps(ARGS.fps, list), nested: AEX.project.nestedRates() };
```

Read `keysBetweenFrames` per comp. Live: keys on frames 15, 20, 30 of a 30 fps comp sat at 12.5,
16.67 and 25 after the conform to 25 fps (`keysBetweenFrames` 2). Re-snap them (move each key to the
nearest whole frame by the animation's intent) or retime with the animator; never ship a comp with
keys between frames. Footage keeps its own rate: a 30 fps clip in a 25 fps comp is reported by the
audit and accepted when it is real-speed footage.

## 6. Names and bins

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {main: "Comp 1", mainName: "MAIN_BrandFilm_25"}
var main = AEK.core.comp(ARGS.main);
var renamed = AEX.project.rename(main, ARGS.mainName);
var bins = AEX.project.fileItems(main, { main: "01_Main", precomps: "02_Precomps", footage: "03_Footage", solids: "04_Solids", unused: "99_Unused" });
return { renamed: renamed, bins: bins, defaultsLeft: AEX.project.inventory(main).defaultNames };
```

Live: `Comp 1`, `Pre-comp 12`, `Comp 3`, `Comp 2` became `MAIN_BrandFilm_25`,
`PC_BrandFilm_25_logo`, `PC_BrandFilm_25_logo_bg_2398`, `UNUSED_Comp2`; 13 items filed, 0 left at
the root. The precomp names are placeholders built from the tree: look at each precomp's frame and
rename by role (`PC_SC010_LogoReveal`). Renaming and filing changed 0 pixels on the before and after
frames.

`rename` returns `{renamed, rewritten, exprErrors}`. A rename by script does not update expressions
that name the comp or layer: the next evaluation fails with "layer named 'X' is missing" and the
expression is disabled. `rename` records each old name (including a precomp layer that follows its
comp's name) and rewrites `comp("X")` and `layer("X")`, both quote styles, then evaluates every
expression at three times. Live: `thisComp.layer("Pre-comp 12")` and `comp('Pre-comp 12')` became
`PC_Test_25_logo`, 2 rewritten, 0 errors, values unchanged (Opacity 50, X 320). Names built from
variables or string concatenation are not rewritten: they show up in `exprErrors`; hand those to
scenario-after-effects-expressions. When you give final names by role, rename by script and then
call
`AEX.project.rewriteRefs([{kind: "comp", from, to}, {kind: "layer", from, to, scope: parentComp.id}])`:
it rewrites and returns `{rewritten, exprErrors}`.

## 7. Collapse Transformations audit

```javascript
// channel: bridge | handoff
// checked: live 27.0
return AEX.project.collapseRisks();
```

Each finding names the parent comp and layer, and the rule: `collapse.effect`, `collapse.mask`,
`collapse.style`, `collapse.adjustment`. Live (Classic 3D, three 3D cards at z -300, 0, 300 in a
collapsed precomp, an outside 3D plane at z 0, camera at z -2000): collapsed, the front card drew
over the plane; with a Glow on the precomp layer all three cards drew behind it; with the Glow
disabled, still behind; with the Glow removed, 0 pixels different from the clean collapsed frame.
Fix by deleting the effect from the precomp layer (or moving it onto the inner layers), or by
turning collapse off when the effect must follow the layer.

To keep 3D through a precomp:

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {comp: "SC010", indices: [2, 3, 4], name: "PC_SC010_Cards"}
var c = AEK.core.comp(ARGS.comp);
var pc = AEK.build.precompose(c, ARGS.indices, ARGS.name, true);
var L = null, i;
for (i = 1; i <= c.numLayers; i++) { if (c.layer(i).source === pc) { L = c.layer(i); } }
L.threeDLayer = true;
if (L.canSetCollapseTransformation) { L.collapseTransformation = true; }
return { precomp: pc.name, size: [pc.width, pc.height], collapsed: L.collapseTransformation, risks: AEX.project.collapseRisks().length };
```

`precompose` returns a comp at the parent comp's size. The camera stays in the parent comp; a camera
inside the precomp is ignored once collapsed (Jake Bartlett, Ns41v75th_I 00:05:59).

## 8. Proxies

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {item: "uhd_25.mp4", dir: "<project>/proxies"}
var it = AEK.core.item(ARGS.item);
var p = AEX.project.makeProxy(it, ARGS.dir, 0.5, "High Quality");   // half-size ProRes 422 .mov, then setProxy(); omit the template for H.264
return p;
```

Live: a 2 s UHD H.264 clip gave a 1920x1080 proxy in 7.3 s; one frame with caches purged took 277 ms
with the proxy on and 570 ms with it off (a second run: 269 and 365 ms). `useProxy` reads true after
`setProxy`; `proxySource.file` holds the proxy path. The H.264 template rewrites the extension to
`.mp4`. ProRes 422 is the expert choice over the Animation codec (Motion Science, y3Qgs2N5z1Y
00:00:55). In 27.0 no output module template is named ProRes; the template "High Quality" writes
ProRes 422 (ffprobe: `prores`, profile Standard, `yuv422p10le`, `.mov`): a 720p clip gave a 640x360
proxy in 1.4 s [live 27.0]. List the templates with `AEK.capture.templates(comp)` first: studios
rename and add them.

Guard every final queue item:

```javascript
// channel: bridge | handoff
// checked: live 27.0
var rq = app.project.renderQueue, out = [], i, r;
for (i = 1; i <= rq.numItems; i++) {
    r = rq.item(i);
    if (r.status === RQItemStatus.DONE) { continue; } // new items read NEEDS_OUTPUT and render false until an output file is set
    if (r.getSetting("Proxy Use-str") !== "Use No Proxies") { r.setSetting("Proxy Use", "Use No Proxies"); }
    out.push({ comp: r.comp.name, proxyUse: r.getSetting("Proxy Use-str") });
}
return out;
```

Live read-backs: a new queue item "Use No Proxies"; after `applyTemplate("Best Settings")` "Use No
Proxies"; after `applyTemplate("Draft Settings")` "Current Settings".

## 9. Find what is slow (scripted Composition Profiler substitute)

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {comp: "MAIN_BrandFilm_25", seconds: 12.0, dir: "<project>/qc/profile"}
var c = AEK.core.comp(ARGS.comp);
return AEX.project.profile(c, ARGS.seconds, ARGS.dir, 10);
```

`profile` renders the same 10 frames through the render queue with caches purged: all layers off,
all on, then each video layer off in turn. `costMsPerFrame = (full - without) / frames`, `costShare`
is the share of the layers' total. Live on a 3840x2160, 25 fps comp: 166 ms per frame against a 40
ms budget; Camera Lens Blur on a half-opacity plate cost 132 ms per frame (79 %), Fractal Noise 14
ms (8 %), the rest within the noise of about plus or minus 13 ms. One `saveFrameToPng` per layer is
too coarse to time this: the kit polls every 100 ms and its readings came back flat (254 to 265 ms
for every layer).

What the Composition Profiler shows that this does not: the time per effect, mask and layer style
inside a layer, the cached asterisk, the preview-resolution cost, and the cost of a matte layer
charged to the effect that references it. Use it when someone can open the Timeline (gui-paths.md).

Multi-Frame Rendering for one render, set by script (reset after the script ends):

```javascript
// channel: bridge
// checked: live 27.0
// ARGS: {comp: "MAIN_BrandFilm_25", dir: "<project>/qc"}
var c = AEK.core.comp(ARGS.comp), t = {};
app.setMultiFrameRenderingConfig(false, 100);
t.off = AEK.capture.queue(c, ARGS.dir + "/mfr_off.mp4", { template: "H.264 - Match Render Settings - 15 Mbps", start: 1, duration: 1 }).ms;
app.purge(PurgeTarget.ALL_CACHES);
app.setMultiFrameRenderingConfig(true, 100);
t.on = AEK.capture.queue(c, ARGS.dir + "/mfr_on.mp4", { template: "H.264 - Match Render Settings - 15 Mbps", start: 1, duration: 1 }).ms;
return t;
```

Live, the same UHD comp, 25 frames: 9.9 s with MFR off, 6.7 s with MFR on (1.5x, Apple Silicon,
other jobs sharing the machine). On a light 1080p comp the two were within 10 % of each other: MFR
pays on heavy frames.

## 10. Remove unused footage and reduce

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {main: "MAIN_BrandFilm_25", dir: "<project>/aep", base: "BrandFilm"}
var main = AEK.core.comp(ARGS.main);
var archived = AEX.project.saveVersion(ARGS.dir, ARGS.base + "_beforeReduce");
var out = { archived: archived.saved, before: app.project.numItems };
out.removedFootage = app.project.removeUnusedFootage();
out.removedByReduce = app.project.reduceProject([main]);
out.consolidated = app.project.consolidateFootage();
out.after = app.project.numItems;
out.audit = AEK.audit.summary(AEK.audit.all());
return out;
```

Live: 13 items; Remove Unused Footage removed 1 (a still used nowhere; the solid inside an unused
comp stayed, because that comp still used it); Reduce Project on the main comp removed 3 more (the
unused comp and what only it used); Consolidate removed 0 (no duplicates). The main comp's frames
were identical before and after (0 pixels different).

## 11. Versioned save

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {dir: "<project>/aep", base: "BrandFilm_main"}
return AEX.project.saveVersion(ARGS.dir, ARGS.base);
```

Live: three calls wrote `_v001`, `_v002`, `_v003`; `dirty` false after each; the open project is the
newest file. Never write over an existing version.

## 12. Collect Files substitute

Collect Files opens a modal dialog: never trigger it from a script. The scripted substitute copies
the sources of everything reachable from the main comp and relinks to the copies.

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {dest: "<delivery>/BrandFilm_collected", main: "MAIN_BrandFilm_25", name: "BrandFilm_collected"}
var main = AEK.core.comp(ARGS.main);
app.project.removeUnusedFootage();
var res = AEX.project.collect(ARGS.dest, main, ARGS.name);
var outside = [], i, it;
for (i = 1; i <= app.project.numItems; i++) {
    it = app.project.item(i);
    if (it instanceof FootageItem && it.file && it.file.fsName.indexOf(ARGS.dest + "/") !== 0) { outside.push(it.name); }
}
res.outside = outside;
return res;
```

Live: 6 sources from four folders copied (7.1 MB), `outside` empty, project saved in the delivery
folder, `dirty` false. Then prove it renders headless:

```bash
mkdir -p <delivery>/check
python3 ae.py aerender --project "<delivery>/BrandFilm_collected/BrandFilm_collected.aep" --comp "MAIN_BrandFilm_25" --out "<delivery>/check/main.mp4" --template "H.264 - Match Render Settings - 15 Mbps"
python3 ae.py probe "<delivery>/check/main.mp4"
```

Live: exit code 0 in 7.1 s, 1920x1080, 25 fps, 125 frames, audio AAC 48 kHz. `aerender` fails with
"Directory does not exist" when the output folder is missing: create it first. Its log warns
"Project has missing fonts" when one is left.

## 13. Essential Properties for variants

```javascript
// channel: bridge | handoff
// checked: live 27.0
// ARGS: {rig: "PC_ChipRig", main: "MAIN_Chips"}
var rig = AEK.core.comp(ARGS.rig), main = AEK.core.comp(ARGS.main);
var chip = rig.layer("Chip"), label = rig.layer("Label");
var fill = chip.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color");
AEX.project.expose(rig, fill, "Chip Color");
AEX.project.expose(rig, label.property("ADBE Text Properties").property("ADBE Text Document"), "Label Text");
AEX.project.expose(rig, chip.property("ADBE Transform Group").property("ADBE Scale"), "Chip Scale");
var a = main.layers.add(rig), b = main.layers.add(rig);
var g = b.essentialProperty;                       // match name "ADBE Layer Overrides"; its children carry the names given at exposure, not localized names
g.property("Chip Color").setValue([0.95, 0.35, 0.2, 1]);
var tp = g.property("Label Text"), td = tp.value; td.text = "FAST"; tp.setValue(td);
return { a: AEX.project.overrides(a), b: AEX.project.overrides(b), count: rig.motionGraphicsTemplateControllerCount };
```

Live: three controls exposed (count 1, 2, 3); instance b read "FAST" and the orange color, instance
a and the source comp kept "FEATURE" and blue, and `essentialPropertySource` named the source
property on each. `getMotionGraphicsTemplateControllerName(i)` is 1-based (index 0 returned null).
The essentialProperty group lists the controls in reverse order of exposure: address them by name.
An overridden text that grows past the precomp frame is cropped at the precomp bounds (seen on the
frame): size the rig comp for the longest text.
