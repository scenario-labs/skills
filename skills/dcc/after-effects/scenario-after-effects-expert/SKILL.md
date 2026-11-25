---
name: scenario-after-effects-expert
description: "Use when an agent must connect to, inspect, change or render from Adobe After Effects (27.0 and 2026) through a script, or when an After Effects request spans several crafts and needs routing. Triggers: connect to After Effects, run a script in my open project, the script did nothing, After Effects is not responding to scripts, a dialog is blocking, DoScriptFile times out, work in my live project without breaking it, undo what the agent did, swap placeholders for footage, change the font everywhere, check my project, audit the project, what changed, render preview frames, contact sheet, aerender, headless render, ExtendScript error, match name not found, which After Effects skill handles this."
license: MIT
---

# After Effects Expert (lead)

Target line: After Effects 27.0 and 2026 (26.x) on macOS and Windows, driven through the channels
and toolkit below.

Expert level here means a technical director's discipline in someone else's open project: find a
channel that cannot hang, inspect before touching, change inside one undo step, prove the result
with numbers and rendered frames, and report what was assumed. The agent wires, measures and checks.
Taste, motion feel and sound stay with the person, or go to the craft siblings. If a sibling skill
named here is missing from your available skills, load it with `skill_get` (Scenario MCP) or ask the
user to install it (https://github.com/scenario-labs/skills#install); unattended, proceed from tool
schemas and flag the gap.

## Stance (the expert delta)

- A dialog stops every script. Close open dialogs before a run and never open one from a job
  (workflow demo, 3AIZ4FT61aw 00:04:22; measured on 27.0).
- Protect the project first: "It's operating on your live project file and undo does not always save
  you" (Plainly, bEO3z86mtbI 00:02:03).
- Wiring is the agent's strength: rigs, renames, versions and checks. "The expression on its own is
  never the problem. It's the rig built around it" (bEO3z86mtbI 00:04:17).
- A first agent pass moves like a slideshow: "Linear movement, no overshoot, no anticipation"
  (bEO3z86mtbI 00:04:39). Never ship linear keys; route motion to scenario-after-effects-animation.
- The agent sees stills, not motion. Ease and timing are judged by a person at full frame rate
  (3AIZ4FT61aw 00:18:51).
- Restate every duration in frames and flag a frame rate mismatch before building (Vlad Sateev,
  _k8rOBob6k8 frame 00:01:37).
- Ask for numbers and ask clarifying questions before a costly build (Aidan Stanik, YTOwQj-n7ME
  00:08:01; Jake In Motion, QLZNiwaKqWg 00:05:56).
- The result must stay editable: "if the client has any notes, then you're going to be the one who
  has to dig through this" (QLZNiwaKqWg 00:09:00). No stacks of hold keys, no unnamed layers.
- Look properties up by match name so a script survives a non-English install (NT Productions,
  DTBtfFiyjNU 00:31:59).

## Establish first

- **Channel:** run `ae.py doctor`. It reports the install, the bridge heartbeat, the scripting
  preference and any extra window.
- **Version:** `app.version`. 27.0 and 26.x assumed. See Version notes for what older builds lack.
- **Whose session:** a person's open project (rules in Live session) or a project the agent owns.
- **Saved or not:** `app.project.file` and `app.project.dirty`. They decide the safety copy.
- **Deliverable:** frames to review, a render, a cleaned project, a template. Frame rate, size and
  duration in frames.
- **Fonts and plugins:** check that a font or an effect exists before using it
  (`AEK.text.fontExists`, false for a missing font and for its stand-in;
  `effects.canAddProperty(matchName)`, false for an unknown effect).

## Channel decision

| Channel            | Use it when                                         | Limits                                                                   |
| ------------------ | --------------------------------------------------- | ------------------------------------------------------------------------ |
| `bridge` (default) | After Effects is open on the same machine           | One job at a time on the main thread. A modal dialog stops it.           |
| `osascript`        | macOS, the terminal holds the Automation permission | Without the permission the call times out (-1712) with no message.       |
| `exe`              | Windows, `AfterFX.exe -r job.jsx`                   | On macOS the binary with `-r` starts a second instance and runs nothing. |
| `aerender`         | Rendering a saved project, no GUI needed            | Reads the file on disk, never the unsaved state. Runs no script.         |
| `handoff`          | No channel works                                    | A person runs one `.jsx` from File > Scripts > Run Script File.          |

- The bridge is `ae_bridge.jsx` in the user `Scripts/Startup` folder. It polls a mailbox folder with
  `app.scheduleTask` and writes a heartbeat every 2 s. It works with the app in the background and
  the screen locked.
- Setup: `ae.py install-bridge`, then restart After Effects or run the file once from File >
  Scripts > Run Script File. Settings > Scripting & Expressions > "Allow Scripts to Write Files and
  Access Network" must be on.
- A stale heartbeat with a job waiting means a long render or an open dialog.
  `ae.py windows --shot <dir>` shows which.
- Dialogs drawn by After Effects (crash repair, disk cache warning, the Home screen) accept
  `ae.py key return`. A script's own `alert()` does not: nothing closes it from outside.
- The runner shadows `alert`, `confirm` and `prompt` inside every job. Their text comes back in
  `dialogs`.
- A job that was running when the app stopped is never run twice. It returns `interrupted: true`.

## The expert loop

1. **Inspect.** `ae.py info`, `ae.py audit`, `ae.py stats`. Read the findings before planning.
   Nothing changes.
2. **State assumptions:** channel, version, frame rate, durations in frames, fonts, what will not be
   touched.
3. **Safety copy.** Saved and clean: copy the `.aep` on disk. Unsaved changes: ask for File >
   Increment and Save, or run it (command 3088) on the person's word. Never `save()` over their
   file.
4. **Change inside one undo step.** `ae.py run job.jsx --undo "Agent: <what>"`. One job, one stage,
   one Undo.
5. **Verify with numbers:** `AEK.stats.diff`, `AEK.audit.all`, and a print of every touched layer
   (`AEK.session.print`, `changed`).
6. **Verify by looking:** capture frames at the beats, build one contact sheet, read it. Check
   clipping, cut-off text, empty frames.
7. **Report:** the diff, what was skipped and why, files written, open findings, assumptions, how to
   undo.

```javascript
// channel: bridge | osascript | exe | handoff
// checked: live 27.0
// Job body for: ae.py run job.jsx --undo "Agent: swap PH placeholders" --args '{"footage": "<abs folder>", "out": "<abs folder>"}'
var st = AEK.session.state(), before = AEK.stats.snapshot(), found = AEK.session.named("PH_"), names = [], i, k, d, l, done = [], skipped = [], items = {};
for (i = 0; i < found.length; i++) { names.push(found[i].name.substring(3)); }
var files = AEK.session.matchFiles(names, ARGS.footage);
for (i = 0; i < found.length; i++) {
    k = found[i].name.substring(3);
    if (!files[k] || files[k].length !== 1) { skipped.push({ layer: found[i].name, comp: found[i].comp, files: files[k] }); continue; }
    if (!items[k]) { d = AEK.xio.importFile(files[k][0], { bin: "agent_swap" }); items[k] = app.project.itemByID(d.id); }
    l = app.project.itemByID(found[i].compId).layer(found[i].index);
    done.push(AEK.session.swap(l, items[k], { fit: "cover", bin: "agent_swap" }));
}
var frames = AEK.capture.spread(app.project.itemByID(st.activeId), 3, ARGS.out, "check");
AEK.session.restore(st);
return { swapped: done, skipped: skipped, diff: AEK.stats.diff(before, AEK.stats.snapshot()), frames: frames };
```

Each `swapped` row must show `changed: []`. `shortByFrames` and `upscaled` go into the report.

## Toolkit (scripts/)

Runner, Python standard library, any OS: [ae.py](scripts/ae.py).

- `doctor`, `install-bridge`, `info`, `audit`, `stats`.
- `run job.jsx | -e code [--undo NAME] [--args JSON] [--lib helper.jsx] [--kit all|none|a,b] [--timeout S] [--channel ...]`.
- `frames COMP --times a,b | --spread N --out DIR [--sheet]`, `sheet OUT.jpg IMG...`,
  `render COMP --out FILE --template T`, `templates COMP`.
- `aerender --project P --comp C --out FILE [--template T]`, `probe FILE` (ffprobe summary with
  alpha detection).
- `windows [--shot DIR]`, `key return|escape|tab`.

A job is the body of a function in ExtendScript (ES3). `return` sends a value back. `ARGS` holds the
`--args` JSON. The result is
`{ok, result | error + line + source, log, dialogs, ms, project, dirty}`.

Inside After Effects, namespace `AEK` ([aekit/](scripts/aekit/)):

- `AEK.core`: `comp`, `item`, `itemById`, `layer`, `prop(base, [matchNames])`, `walk`, `abs`, `bin`,
  `frame`, `time`, `enumName`, `info`.
- `AEK.stats`: `snapshot`, `diff`, `comp`. `AEK.audit`: `all`, `summary`, `project`, `footage`,
  `comps`, `comp`, `fonts`.
- `AEK.capture`: `frame`, `frames`, `spread`, `queue`, `templates`. `AEK.xio`: `importFile`,
  `importItem`, `importMany`, `replace`, `addToComp`, `describe`.
- `AEK.motion`: `key`, `ease`, `bezier` (exact CSS cubic-bezier), `keys`, `sample`, `linearKeys`.
- `AEK.build`: `comp`, `solid`, `adjustment`, `nullLayer`, `shape`, `shapeGroup`, `effect`,
  `effectProps`, `parent`, `matte`, `precompose`, `anchor`, `camera`.
- `AEK.text`: `add`, `style`, `measure`, `fit`, `inFrame`, `animator`, `fontExists`. `AEK.expr`:
  `set`, `list`, `check`, `bake`, `controls`.
- `AEK.session`: `state`, `restore`, `print`, `changed`, `named`, `matchFiles`, `swap`, `setFont`,
  `fontRuns`.

Run [ae_check.py](scripts/ae_check.py) on every job before sending it. It flags ES3 traps, dialogs,
`~` paths, display-name lookups and expression traps (`--expr`).

## Live session

- Take `AEK.session.state()` first and call `restore()` last. It puts back the current time, the
  work area, the layer selection and the render flags of the queue.
- Never call `app.project.close()`, `app.newProject()`, `app.open()`, `app.quit()` or
  `app.purge(PurgeTarget.ALL_CACHES)` in a person's session. The purge also empties their disk
  cache.
- Never start the person's queued renders. `renderQueue.render()` renders every queued item.
  `AEK.capture.queue` switches theirs off for the run and back on after it.
- Prefer `saveFrameToPng` frames for checks. They need no queue item. The call is asynchronous: wait
  for the file.
- A placeholder swap keeps the layer: `AEK.session.swap` replaces the source directly when size and
  length match. Otherwise it wraps the clip in a fit comp of the placeholder's size and length.
- Change fonts through the text document (`AEK.session.setFont`), never `app.project.replaceFont()`
  in a live session. It cannot be undone, and the next Undo removes an earlier change of the person.
- Locked layers: unlock, change, lock again, and say so. Shy, solo and guide flags stay as found.
- Paths: absolute only. `~` in ExtendScript can resolve to a cloud-synced folder. Write agent files
  to a folder the person named.
- If the app stops answering for more than 90 s with an extra window on screen, look at it
  (`windows --shot`) and tell the person. Never stop the app with a signal: it is treated as a
  crash.

## Numbers

| Value     | Meaning                                                                    |
| --------- | -------------------------------------------------------------------------- |
| about 1 s | bridge round trip for a small job (poll 0.3 s)                             |
| 1.2 s     | measured: 4 placeholder swaps, 3 text layers restyled, 3 PNG frames, 1080p |
| 100 ms    | one `saveFrameToPng` frame of a simple 1080p comp                          |
| 13 s      | `aerender`, 60 frames of a 1080x1920 comp to H.264, GUI app open           |
| 19 s      | relaunch to first heartbeat after a forced stop, crash dialog included     |
| 105 %     | audit threshold for footage enlarged past its pixels                       |
| 16 / 3088 | menu command ids: Edit > Undo, File > Increment and Save                   |

## Quality gates

- Measurable: `ok` true and `dialogs` empty. The diff shows only intended changes. Every touched
  layer prints `changed: []`. Audit errors are zero or each one is reported. No `expression.error`
  finding.
- Visual: one contact sheet read before any claim. Subject present in every frame, no cut-off text,
  no empty frame inside a layer's span, no clipped glow at a layer edge.
- Delivered files: `ae.py probe` matches the brief (codec, size, frame rate, frame count, alpha).
- Report: assumptions listed, skipped items listed with the reason, the undo name given, the
  person's file untouched.

## Common mistakes

| Mistake                                      | Symptom                                                       | Fix                                             |
| -------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------- |
| `alert()` used as a probe                    | every later job waits                                         | `AEK.log()`; the runner shadows dialogs         |
| Display names (`property("Position")`)       | fails on non-English installs                                 | match names (`ADBE Position`)                   |
| Reference kept across `addProperty`          | "Object is invalid"                                           | fetch the property again by match name          |
| `~/` path                                    | "File couldn't be opened for writing"                         | absolute path from `ARGS`                       |
| Layer addressed by index after adding layers | wrong layer changed                                           | new layers land on top: use names or `layer.id` |
| `JSON`, `forEach`, `let` in a job            | syntax or reference error                                     | ES3 only; `AEK.json`                            |
| Frame saved and read at once                 | missing or empty PNG                                          | poll for the file (`AEK.capture.frame` does)    |
| Frame saved from a 32 bpc project            | almost black sheet: values are written divided by 10          | `ae.py sheet ... --gain 10`                     |
| New project assumed to be at defaults        | it inherits bit depth and working space from the last project | read both back, then set them                   |
| Missing font written to a text layer         | silent substitution at render                                 | `AEK.text.fontExists` first                     |
| Broken expression assigned                   | no error until evaluated                                      | `AEK.expr.set` evaluates and raises the message |
| `replaceSource` with a shorter clip          | layer out point pulled in                                     | `AEK.session.swap` (fit comp)                   |
| Seconds used for timing                      | off by a frame at other rates                                 | frames, with the frame rate stated              |

## Routing

| Request or symptom                                                        | Skill                                    |
| ------------------------------------------------------------------------- | ---------------------------------------- |
| messy project, naming, missing footage, slow previews, precomps, proxies  | scenario-after-effects-project           |
| stiff motion, easing, overshoot, overlap, motion blur                     | scenario-after-effects-animation         |
| icons, Trim Paths, Repeater, morphs, SVG, Lottie                          | scenario-after-effects-shape-layers      |
| kinetic type, text animators, text does not fit, languages                | scenario-after-effects-typography        |
| expression error, rigs, controllers, loops, counters                      | scenario-after-effects-expressions       |
| batch versions from CSV, render queue by script, templates, tools         | scenario-after-effects-scripting         |
| 2D character rigs, walk cycles, lip sync                                  | scenario-after-effects-character-rigging |
| keying, green edge, roto, cleanup, light wrap, grain match                | scenario-after-effects-compositing       |
| the track slips, stabilize, screen replacement, camera solve              | scenario-after-effects-tracking          |
| 3D models, cameras, lights, shadows, 2.5D parallax                        | scenario-after-effects-3d                |
| energy, snow, dust, disintegration with built-in effects                  | scenario-after-effects-vfx               |
| color management, banding, export, transparent background, platform specs | scenario-after-effects-color-delivery    |
| ads, hooks, pacing to music, end cards, variants                          | scenario-after-effects-motion-production |
| generated images, video, 3D, voice, music with the Scenario MCP           | scenario-after-effects-generation        |

## Handoffs

- Delivers to every sibling: the channel, the toolkit, the project audit and snapshot, the
  assumptions list.
- Receives from siblings: job bodies and their `AEX.<domain>` helpers (`--lib`). The lead runs the
  loop and reports.
- Generated assets enter through scenario-after-effects-generation, then `AEK.xio.importFile` and an
  audit. Generated media is raw input.

## Version notes

- Expressions run on the JavaScript engine by default. Read `app.project.expressionEngine` before
  relying on syntax.
- Track mattes: any layer can be the matte since 23.0 (`setTrackMatte`). The matte no longer sits
  above its target.
- H.264 renders from the Render Queue since 23.0. Media Encoder is not required for an MP4.
- 3D: Advanced 3D is the renderer for models, environment lights and shadows. Its match name is
  `ADBE Calder`; `ADBE Advanced 3d` is Classic 3D, which is what a comp made by script starts on.
  Ray-traced 3D is gone.
- Text: `app.fonts` since 24.0, character ranges since 24.3, `usedFonts` since 24.5.
- `Layer.id` and `Project.layerByID()` since 22.0: stable handles across reordering.
- Roto: Object Matte replaces the Roto Brush tool icon in 26.2.
- CEP panels are on a removal path and UXP is beta only (27.1 beta). ExtendScript stays.
- The in-app AI Assistant (27.0, beta) is separate from these channels. No outside agent access to
  it is documented.
- More traps: [references/traps.md](references/traps.md).

## References

- [references/procedures.md](references/procedures.md): full jobs per procedure, with channel,
  checked line and what to check.
- [references/traps.md](references/traps.md): version and cross-domain traps, dialogs and recovery.
- [references/expert-notes.md](references/expert-notes.md): what experts observed when agents drove
  After Effects, with timestamps.
- [references/critique.md](references/critique.md): the rubric for judging a run.
- [references/gui-paths.md](references/gui-paths.md): menus, panels and shortcuts for the same
  procedures.
- [references/sources.md](references/sources.md): every source with URL.
- Toolkit: [ae.py](scripts/ae.py), [ae_bridge.jsx](scripts/ae_bridge.jsx),
  [ae_check.py](scripts/ae_check.py), [aekit/](scripts/aekit/).
