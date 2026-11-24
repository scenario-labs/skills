---
name: scenario-3dsmax-expert
description: "Use when an agent must drive, inspect or change Autodesk 3ds Max (2027.3) through a script, the Autodesk 3ds Max MCP server, a community MCP bridge or 3dsmaxbatch, or when a 3ds Max request spans several domains and needs routing. Triggers: connect to 3ds Max, MCP server not working, Safe MAXScript refused a command, blocked dotNetObject, run a script in the open scene, batch convert max files, headless render, check my scene, audit the scene, what changed, capture the viewport, render test views, the script did nothing, the viewport did not update, a dialog blocks the render, 3ds Max crashed, undo the agent's change, pymxs or MAXScript snippet fails, which skill handles this."
license: MIT
---

# 3ds Max Expert (lead)

Target line: 3ds Max 2027.3 on Windows, driven through the channels and toolkit below.

**Status: not yet run in 3ds Max.** Nothing here has been executed in the application. Code is
checked against the cited documentation, and unconfirmed API names carry a bracketed `verify` mark:
confirm each in the live session first. On a first live run, say so to the user and report what
differed from the skill.

Expert level here means a technical director's discipline in someone else's live scene: find the
channel, inspect before touching, change inside one undo record, prove the result with numbers and
captures, and report what was assumed. The agent is an operator under an art director, never an
autonomous visualizer. If a sibling skill named here is missing from your available skills, load it
with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

## Stance (the expert delta)

- A vague brief gets invented details. Work in short stages, each with a defined finished result
  approved before the next (Forever Stu, kBo57xFC3ic 00:03:12).
- Judge geometry in orthographic top views against dimensions, never from one attractive perspective
  (kBo57xFC3ic 00:08:50).
- Name the renderer and the material class in every plan. Otherwise the agent defaults to Physical
  Material (Arch Viz Artist, c3acjyR7j7E 00:05:02).
- End every task with a summary and the assumptions made. Experts used this list to check accuracy
  (c3acjyR7j7E 00:04:28).
- Preserve the scene: new layer, editable result, no render unless asked (Arch Viz Artist,
  UuWmWAvB4Y0 00:07:05).
- Never call a shot verified without looking at its capture (UuWmWAvB4Y0, frame 00:03:04).
- Layer 0 stays empty. The agent rebuilds lists it finds empty instead of assuming (3D GROUND,
  XpWCMn9Nboc 00:01:05, 00:00:32).
- Taste stays human: composition, planting, lighting mood (kBo57xFC3ic 00:14:06, 00:29:50).

## Establish first

- **Channel:** ask the user, or run `max_env.doctor()` (below).
- **Release:** 3ds Max 2027.3 assumed. 3ds Max opens older files, never newer ones (ArchViz
  Explained, xGm1OBHd50Y 00:01:23).
- **Renderer:** read `renderers.current`. Never switch it unasked.
- **Units:** system unit and scale from `stats.snapshot()`. State the unit behind every number.
- **Deliverable:** stills, animation, engine export (FBX, glTF, USD) or a clean scene.
- **Marked-up screenshot:** ask for one. Rectangles and splines on a capture carry intent better
  than words (UuWmWAvB4Y0 00:04:20).

## Channel decision

`doctor()` returns `{os, installs, batch_exe, mcp_ports, bridge, channel, notes, env}`. It probes
TCP ports on 127.0.0.1 only and sends nothing. `MAX_CHANNEL` overrides it.

| Capability          | batch       | mcp-safe (Autodesk)                             | bridge (community) | handoff          |
| ------------------- | ----------- | ----------------------------------------------- | ------------------ | ---------------- |
| Read scene          | yes         | yes (level 1+)                                  | yes                | yes, by the user |
| Change scene        | yes         | level 10 scripts; level 2 is undo and redo only | yes                | yes              |
| Python allowed      | yes         | level 20 only (admin)                           | yes                | yes              |
| Import and export   | yes         | not documented                                  | yes                | yes              |
| Render to file      | yes         | yes; modal dialogs block it                     | yes                | yes              |
| Viewport capture    | no viewport | not documented                                  | yes (bridge tool)  | user screenshot  |
| Approval per script | no          | yes, script preview                             | not documented     | user runs it     |
| Headless            | yes         | no (not in Batch)                               | no                 | no               |

- **mcp-safe:** the Autodesk 3ds Max MCP server, Tech Preview in 2027.3, off by default. Local HTTP,
  a token on every request, ports 27200 to 27209, lowest free port per instance.
- Autodesk: "Use an MCP client that supports MCP Apps to use the scripting feature. This feature
  doesn't work with Claude Code in the terminal." An agent without MCP Apps uses handoff, batch or a
  bridge.
- Levels: 0 Off, 1 Read-only, 2 Read/write (undo and redo only, runs no scripts), 10 Safe MAXScript,
  20 Python (admin only, registry or environment).
- Admin settings are read at startup only. Precedence is HKLM registry, then environment variable,
  then preference. The Assistant section of `3dsMax.ini` also holds them.
- Sources conflict on approval. The FAQ says script preview is always on for external clients. The
  admin page lists `ADSK_3DSMAX_MCP_SKIP_PROPOSE=1`. Assume preview is on.
- Scripts run in Safe Scene Script Execution. Blocked: `dotNetObject`, `dotNetClass`, `macroScript`,
  UIAccessor, `windows.sendMessage`, `globalVars.remove`, `setINISetting`, file delete and copy.
  Python can be blocked too.
- A blocked command stays blocked for the rest of the session. A restart may clear it.
- **bridge:** community servers (3dsmax-mcp, Max Ultra MCP, max-mcp) run arbitrary MAXScript or
  Python on the main thread. Nothing asks the user before a script runs, so the agent applies the
  rules below itself.
- **batch:** `3dsmaxbatch.exe` runs a script after loading a scene, then exits. It uses a license,
  has no viewport and no dialogs, and MCP is not available in it.
- **handoff:** the user runs the wrapped script with Scripting > Run Script and returns the result
  JSON and captures.

What to tell the user to set up:

- **mcp-safe:** Customize > Preferences > MCP tab. Enable "3ds Max MCP Server", set "MCP tools
  enabled" to Safe MAXScript, choose "New token on demand", click OK, then Copy the "mcp.json entry"
  into an MCP Apps client. Treat the token like a password. Keep the server off on terminal servers.
- **bridge:** install the bridge the user chose, then test with a harmless create plus capture, not
  a status ping (3D GROUND, GQv8Y_8eiBU 00:01:08).
- **batch:** the 3ds Max install path, or `MAX_BATCH_EXE`, and a free license.
- **handoff:** a folder for result files and captures.

## The expert loop

1. **Inspect.** Run `stats.snapshot()` and `audit.all(expect=...)` before any change. Read findings
   before planning.
2. **State assumptions:** renderer, units, release, channel, target. Ask only what changes the plan.
3. **Save a new increment before destructive work.** Never overwrite the user's file: save
   `<name>_v002.max` with `saveMaxFile ... useNewFile:false` so the open scene keeps its name.
   `saveMaxFile` overwrites silently.
4. **Change inside one undo record**, on a new layer, kept editable. One stage per call.
5. **Verify with numbers:** a second snapshot and `stats.diff(a, b)`, then `audit.all()` again.
6. **Verify by looking:** `capture.views()` (persp, front, left, top), one
   `max_review.contact_sheet()`, `image_checks()` on each image. Look at the sheet before claiming
   anything.
7. **Report:** what changed (the diff), the files written, captures, open findings, the assumptions
   list and minutes per stage.

Expect 10 to 22 minutes per task through a bridge. Connection drops cost 25 of 35 minutes in one
test (UuWmWAvB4Y0). Save before long steps.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripting-pipeline__pymxs-using-2027.md
# Chunk for max_wrap.wrap(code, kit=["audit", "capture"]): stats, audit, capture, log and result are bound.
before = stats.snapshot()
report = audit.all(expect={"units": "centimeters", "renderer": "Arnold"})
log("errors", report["tally"]["error"])
result = {"before": before, "audit": report}
```

## Toolkit (scripts/)

Runner side (plain Python 3.10+, any OS, never imports pymxs):

- `max_env.doctor()`: channel detection, as above. `find_installs()` lists installs.
- `max_wrap.wrap(code, lang="python", kit=(), result_path=None, label="agent change", undo=True, kit_dirs=None)`:
  one self-contained script. The chunk sets `result`. The wrapper writes
  `{ok, result, error, log, max_version}` to `result_path` and prints `MXK_RESULT <json>`.
  - `lang="python"` serves batch, bridge and handoff. With `result_path=None` it reads `result_path`
    from `maxOps.mxsCmdLineArgs`.
  - `lang="maxscript"` is the mcp-safe form. It uses no Python and no blocked command, returns the
    JSON as the script's value, and writes a file only when `result_path` is given.
  - `kit` entries: a lead module (`result`, `stats`, `capture`, `audit`, `xio`; MAXScript twins
    exist for all but `xio`), a path to a `.py` or `.ms` file, or a name found as `<name>.py` or
    `<name>.ms` (also `mxs/<name>.ms`) in `kit_dirs`.
  - Siblings inline their helpers this way, for example
    `kit=["audit", "maxkit_archviz"], kit_dirs=[<their scripts folder>]`. Each file becomes a module
    bound to its file stem. Lead modules it imports are added automatically.
- `max_batch.command(script, scene=None, args=None, exe=None, listener_log=None, log=None, verbosity=3, dialog_monitor=True)`
  returns an argument list, never a shell string. Strings go as `-mxsString key:"..."`, numbers and
  booleans as `-mxsValue key:"..."`.
- `max_batch.run_batch(script, scene=None, args=None, timeout=1800, log_dir=None, exe=None)` returns
  `{ok, exit_code, meaning, result, stdout, listener_log, log, command, seconds}`. Exit codes: -100
  bad arguments, -110 cannot start, -120 connection lost, -130 error in the script.
- `max_check.check(paths=None, code=None, lang=None, channel=None)` returns
  `{ok, errors, warnings, unknown_names, python}`. Python must compile under 3.13. MAXScript is
  checked for bracket and string balance. With `channel="mcp-safe"` it flags the block list.
  `unknown_names` are names missing from `references/api-names.txt`.
- `max_review.image_checks(png)`, `compare(a, b)`, `contact_sheet(pngs, out)`.

Inside 3ds Max (`scripts/maxkit/`, main thread only; twins in `scripts/maxkit/mxs/` named
`mxk_<module>_<fn>`):

- `stats.snapshot()`, `stats.diff(a, b)`, `stats.collect()`.
- `audit.all(expect=None, data=None)` returns `{findings, tally}`. Rules: `units`, `names`,
  `transforms`, `geometry`, `materials`, `maps`, `layers`, `render`, each
  `(data=None, expect=None)`. Expect keys: `units`, `renderer`, `far_limit`, `max_faces`,
  `layer0_empty`.
- `capture.viewport(path, view=None, size=None)`,
  `capture.views(dir, views=("persp", "front", "left", "top"), size=None, stem="view")`,
  `capture.render(path, camera=None, size=None)`. Each writes a new file (`_v002`) and never
  overwrites.
- `xio.import_any(path, **opts)`, `xio.export_fbx(path, preset=None, selected=False)`,
  `xio.export_gltf(path, selected=False)`, `xio.export_usd(path, selected=False)`,
  `xio.gltf_precheck()`.

Run `max_check.check()` on every script before sending it. Names marked `[verify]` are not in the
saved docs.

## Numbers

| Value                | Meaning                                                          |
| -------------------- | ---------------------------------------------------------------- |
| 27200 to 27209       | Autodesk MCP ports, one per running instance                     |
| 10 / 25              | Assistant checks in after 10 tool steps, stops at 25             |
| 45 days              | Assistant prompt retention                                       |
| 1,800 s              | default `run_batch` timeout [added]                              |
| 1 km in system units | audit far-from-origin limit [added]; set `far_limit` per project |

## Quality gates

- Measurable: zero audit errors, or each one reported. The diff shows only the intended changes.
  `run_batch` exit code 0 and `result.ok` true.
- Visual: the contact sheet shows the subject in every view, with no `all_black`, `uniform` or
  `low_contrast_center` flag. Cameras are captured with Safe Frame on.
- Report: the assumptions list is present, the new file names are listed, and the user's file is
  untouched.

## Common mistakes

| Mistake                                 | Symptom                               | Fix                                                                            |
| --------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------ |
| pymxs called from a thread              | freeze or crash                       | main thread only; `mxstoken` is deprecated                                     |
| Viewport not refreshed                  | "the script did nothing"              | `redrawViews()` after changes (wrapper does it)                                |
| Modal dialog during render              | render never starts                   | fix missing maps and units mismatch (`maxstart.max`); close the dialog by hand |
| Blocked command sent in mcp-safe        | blocked for the session               | check with `channel="mcp-safe"`; plain MAXScript or a manual step              |
| Render Setup pre-render script expected | did not fire                          | `render()` skips it; use `#preRender` callbacks                                |
| `loadMaxFile` in a live scene           | user's scene replaced without prompt  | never in a live session; `mergeMAXFile` or batch                               |
| Asset fitted to a scaled placeholder    | wrong size wherever the box is scaled | count the box scale once: procedures P7b                                       |
| `max` commands from Python              | NameError                             | `rt.execute("max tool zoomextents all")`                                       |

## Session safety

- Dialogs: pass `#noPrompt` and `quiet:true` to import, export and save. Batch runs with `-dm on`. A
  script cannot close a dialog it opened in mcp-safe.
- Units Mismatch is modal and blocks a live session. Before any `mergeMAXFile` or `loadMaxFile`,
  compare the file's units with the scene's (procedures P7). Pass `quiet:true` and an explicit
  `ignoreFileUnits:` (2027.1); `loadMaxFile` also takes `allowPrompts:false`. Different units:
  rescale in batch first. Align `maxstart.max` units too.
- Merge with `#autoRenameDups #renameMtlDups #neverReparent`: the defaults prompt, and an incoming
  "Wood" never replaces the scene's "Wood".
- One main thread: a long script freezes the UI. Split work into stages.
- Save first: an Arnold render can crash 3ds Max. Reading a Batch Render view's camera crashes it.
  Biped `scaleFootprints` crashes it. After a crash the user reopens 3ds Max and the MCP connection
  (c3acjyR7j7E 00:09:37); resume from the last `_v002`.
- Autosave and `holdMaxFile()` are no substitute for a saved `_v002`.
- Scripts cannot overwrite rendered `.tx` files, re-imported `.abc` caches, or text files a script
  opened. Write new names.
- Never unattended: render farm submissions, license prompts, overwriting any file, installing
  plugins or startup scripts, changing admin MCP levels.

## Routing

| Request or symptom                                                           | Skill                              |
| ---------------------------------------------------------------------------- | ---------------------------------- |
| units, layers, naming, missing maps, slow scene, CAD or Revit intake, splats | scenario-3dsmax-scene              |
| Editable Poly, Boolean, chamfer, subdivision, retopology                     | scenario-3dsmax-modeling           |
| LODs, collision, FBX to Unreal or Unity, AI mesh cleanup                     | scenario-3dsmax-game-assets        |
| UVs, texel density, Bake to Texture, normal map looks wrong                  | scenario-3dsmax-uv-baking          |
| OpenPBR, VRayMtl, Corona materials, color spaces                             | scenario-3dsmax-materials          |
| noisy render, HDRI, OCIO, AOVs, Arnold, V-Ray, Corona setup                  | scenario-3dsmax-lighting-rendering |
| archviz shots, Forest Pack, RailClone, Cosmos, client revisions              | scenario-3dsmax-archviz            |
| rigs, Skin, CAT, Biped, retargeting, animation export                        | scenario-3dsmax-animation-rigging  |
| tyFlow, destruction, cloth, Phoenix status                                   | scenario-3dsmax-fx                 |
| tools, callbacks, Qt panels, packages, batch pipelines                       | scenario-3dsmax-scripting          |
| generated 3D, textures, skyboxes, splats with the Scenario MCP               | scenario-3dsmax-generation         |

## Handoffs

- Delivers to every sibling: the channel, the toolkit, the audit and snapshot of the scene, and the
  assumptions list.
- Receives from siblings: wrapped chunks and their `maxkit_<domain>` helpers. The lead runs the loop
  and reports.
- Generated assets enter through scenario-3dsmax-generation, then `xio.import_any()` and an audit.
  Generated 3D is raw input, never final.

## Current 3ds Max notes

From `3dsmax-version-deltas` (2027.3, released 2026-11-19):

- Python 3.13.9 and PySide 6.8.3. MaxPlus and Python 2 are gone.
- OpenPBR is the default material since 2026, and the viewport shows a simplified OpenPBR shader.
- New scenes start under OCIO. Studios on V-Ray or Corona often switch to Gamma workflow by choice.
- 2027.1 adds unit rules in Preferences > Files and `loadMaxFile ignoreFileUnits:`.
- 2027.3 adds the Khronos glTF importer and exporter. The exporter flattens hierarchies and drops
  vertex colors. Exporter settings are global state, not part of a job.
- Bake to Texture replaces Render to Texture. Phoenix has been at end of support since April 2026.
- More traps across domains: [references/traps.md](references/traps.md).

## References

- [references/procedures.md](references/procedures.md): full code per procedure, with channel,
  status and checks.
- [references/traps.md](references/traps.md): cross-domain and MCP traps with fixes.
- [references/expert-notes.md](references/expert-notes.md): attributed operating rules with
  timestamps.
- [references/critique.md](references/critique.md): the rubric for judging a run.
- [references/gui-paths.md](references/gui-paths.md): menus and settings for each procedure.
- [references/sources.md](references/sources.md): every source with URL.
- [references/api-names.txt](references/api-names.txt): names extracted from the saved docs, used by
  `max_check`.
- Toolkit: [max_env.py](scripts/max_env.py), [max_wrap.py](scripts/max_wrap.py),
  [max_batch.py](scripts/max_batch.py), [max_check.py](scripts/max_check.py),
  [max_review.py](scripts/max_review.py), [maxkit/](scripts/maxkit/) with its MAXScript twins in
  [maxkit/mxs/](scripts/maxkit/mxs/).
