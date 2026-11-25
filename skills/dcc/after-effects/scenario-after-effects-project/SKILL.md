---
name: scenario-after-effects-project
description: "Use when an After Effects project must be set up, inherited, cleaned or handed over: a messy project from freelancers, comps named Comp 1 or Pre-comp 12, missing footage or red color bars, missing fonts, missing effects or plugins nobody has, mixed frame rates, 8 bpc banding, wrong working space, no folder or naming scheme, previews or renders that are slow, the Composition Profiler, proxies, precompose versus collapse transformations, a 3D precomp that went flat, Reduce Project, Remove Unused Footage, Collect Files, versioned saves, or Essential Properties to make variants from one precomp. Also when someone says the project is a mess, make it production ready, why is my preview slow, relink everything, or package the project for another artist."
license: MIT
---

# After Effects project lead

Target line: After Effects 27.0 and 2026, driven through the scenario-after-effects-expert channels
and toolkit.

Expert level here means a project another artist can open on another machine with no dialog, find
anything in under a minute, render headless, and change without breaking timing. The stance: measure
the project before touching it, change it inside one undo step per stage, and prove each stage with
numbers and with frames that did not change. If a sibling skill named here is missing from your
available skills, load it with `skill_get` (Scenario MCP) or ask the user to install it
(https://github.com/scenario-labs/skills#install); unattended, proceed from tool schemas and flag
the gap.

**REQUIRED BACKGROUND:** scenario-after-effects-expert (channels, review loop, toolkit, version
traps).

## Stance (the expert delta)

1. **The kit audit is a start, not the contract.** It reads the project item by item; a handoff
   breaks on what only shows from the main comp down: comps and footage nothing uses, a collapsed
   precomp that flattens, a substitute font after reopen, a precomp at another frame rate. Run
   `AEX.project.inventory(main)`, which gathers them in one report [live 27.0].
2. **Test fonts with `isSubstitute`.** Once a project references a font that is not installed,
   `app.fonts.getFontsByPostScriptName(name)` returns a substitute Font object, length 1. Only
   `Project.usedFonts[i].font.isSubstitute` tells the truth [live 27.0].
3. **A frame rate change moves timing off the grid.** Keys keep their seconds: keys on frames 15,
   20, 30 at 30 fps landed on 12.5, 16.67 and 25 at 25 fps [live 27.0]. Conform comps early, then
   re-snap keys. Never conform real-speed footage; use Preserve frame rate when nested for a
   deliberate low rate (Adobe documentation).
4. **Collapse Transformations is one switch with two meanings** (Jake Bartlett, Ns41v75th_I
   00:00:00). On a precomp it keeps 3D and removes cropping. Any effect, closed mask or layer style
   on that layer flattens it, and disabling is not enough: delete it (Caleb Ward, J3ApvB8sqD0
   00:14:31). Measured on Classic 3D (`comp.renderer` `ADBE Advanced 3d`, the start value of a comp
   made by script): a disabled glow still sent every card behind an outside plane; deleting it
   restored the frame, 0 pixels different [live 27.0].
5. **Profile before optimizing, with caches purged.** The Composition Profiler marks cached layers
   with an asterisk and follows the viewer resolution (Adobe documentation). A precomp used twice
   looks cheap the second time. Purge, turn Adaptive Resolution off, then read Render Time. Twirled
   down, a layer splits its time across masks, layer styles and individual effects. A layer with its
   video off that an effect references (Set Matte, Compound Blur) shows an empty time: its cost sits
   in the referencing effect (Adobe documentation).
6. **A proxy can reach a draft render.** New queue items and Best Settings read Proxy Use "Use No
   Proxies" (Motion Science, y3Qgs2N5z1Y 00:02:53), but the Draft Settings template reads "Current
   Settings" [live 27.0]. Force "Use No Proxies" on every final queue item.
7. **A bad working space name turns color management off.**
   `app.project.workingSpace = "Not A Profile"` throws nothing and reads back "None" [live 27.0].
   Pick names from `listColorProfiles()` and read them back.
8. **Fewer nesting levels, named by role.** Layered art arrives with groups that become precomps
   hiding their contents: "when in doubt fewer groups is probably better" (Kyle Hamrick, fuDs-WPyAR4
   00:06:02). Variants of one element are one precomp with Essential Properties, not duplicated
   comps.

## Establish first

| Input                                       | Why it changes the plan                                | Default                                                                                                                                               |
| ------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Main comp (the one that ships)              | everything else is judged by reachability from it      | ask; else the comp with the longest duration and no parent                                                                                            |
| Delivery size, frame rate, duration         | target for every comp conform                          | brief; else the main comp's                                                                                                                           |
| Bit depth and working space                 | banding, color math, delivery                          | 16 bpc; sRGB IEC61966-2.1 for web, Rec.709 Gamma 2.4 for broadcast                                                                                    |
| Renderer per 3D comp                        | Advanced 3D or Classic 3D                              | keep what each comp uses; read `comp.renderer`: `ADBE Advanced 3d` is Classic 3D, `ADBE Calder` is Advanced 3D, `ADBE Ernst` is Cinema 4D [live 27.0] |
| Plugins installed on every artist's machine | missing effects are a blocker, not a warning           | list from the audit                                                                                                                                   |
| Font licenses                               | which fallback is allowed                              | ask before replacing a brand font                                                                                                                     |
| Where footage may live                      | collect target, cloud folders are slow                 | one project folder per job, off cloud sync                                                                                                            |
| After Effects version of the team           | `Save a Copy As` an older version drops newer features | 27.0 or 26.x                                                                                                                                          |
| Channel                                     | bridge in a live session, handoff for a person         | bridge                                                                                                                                                |

Never clean the received file in place: save it as `<name>_v000_received.aep` first, then work in
`_v001`.

In a person's live session, never open, close or switch projects unasked. Opening or creating a
project while the current one has unsaved changes raises a native Save As panel that nothing can
close from outside, and it blocks After Effects. Ask, save first (`app.project.save()`), then open.
`AEK.core.open` and `AEK.core.fresh` discard changes: test sessions only.

## Procedure

Load the helper: `ae.py run job.jsx --lib <skill>/scripts/project.jsx`. Each stage is one job, one
undo group. Full code in [procedures.md](references/procedures.md).

1. **Freeze and inventory.** Goal: a written picture of the mess. Save the received version
   (`AEX.project.saveVersion`), then `AEX.project.inventory(main)`. Capture
   `ae.py frames MAIN --spread 6 --sheet` as the before sheet. GATE: inventory JSON saved; before
   frames exist.
2. **Relink.** `AEX.project.relink([roots])` searches each missing file by name under the roots the
   user gives (drives, the delivery folder). It never picks between two candidates silently. GATE:
   `missing.length` 0, or each leftover listed for the producer.
3. **Fonts and effects.** `AEX.project.missingFonts()`, then `AEX.project.fixFonts(fallback)` only
   with the user's fallback. Missing effects: list match names; rebuild natively, pre-render on a
   machine that has the plugin, or disable and label. If a plugin crashes the project on open, a
   person restarts in Safe Mode (Settings > Startup & Repair > Start in Safe Mode: third-party
   plugins off) (Adobe documentation). Check the installed third-party effects for the yellow
   warning icon in Effect Controls: they do not support Multi-Frame Rendering (Adobe documentation).
   GATE: 0 substitutes; each missing effect has an owner.
4. **Settings.** `AEX.project.color({bpc, workingSpace, linearize})` and read back: a new project
   inherits the bit depth and working space of the one open before it [live 27.0]. Linearize only at
   16 or 32 bpc (Adobe documentation). Before turning a working space on, set Preserve RGB
   (Interpret Footage > Color) on control footage such as displacement maps, or its values get
   converted (Adobe documentation). Set the expression engine to JavaScript and the time display to
   frames. GATE: read-back equals the brief.
5. **Frame rates.** `AEX.project.conformComps(fps, comps)` on comps that must match; keep a
   deliberate low rate with `preserveNestedFrameRate`. GATE: `keysBetweenFrames` 0 after
   re-snapping; `nestedRateMismatch` empty or deliberate.
6. **Names and bins.** `AEX.project.rename(main, "MAIN_<Film>_<fps>")` gives placeholders from the
   tree (`PC_<parent>_<first named layer>`). Read the frames and give final names by role. A rename
   by script does not update expressions that name the comp or layer: they fail with "layer named
   'X' is missing" [live 27.0]. `rename` rewrites `comp("X")` and `layer("X")` references and
   returns `exprErrors` for what it could not see (names built from variables). Apply final names
   with the same care. `AEX.project.fileItems(main)` files items into `01_Main`, `02_Precomps`,
   `03_Footage/Video|Stills|Audio`, `04_Solids`, `99_Unused`. GATE: `defaultNames` 0; `exprErrors`
   empty; nothing at the root.
7. **Structure.** Run `AEX.project.collapseRisks()`. For each collapsed precomp that flattens,
   decide: delete the effect (3D must interact), or turn collapse off (effect must follow the
   layer). `collapseRisks` does not flag two cases; check them by eye: point-control effects
   (Gradient Ramp, Fractal Noise, light sweeps) on a collapsed layer stay at comp coordinates, and a
   camera inside a collapsed precomp is ignored (Jake Bartlett, Ns41v75th_I 00:09:14, 00:06:31).
   GATE: risks 0 or accepted; collapsed 3D frames checked on a sheet.
8. **Speed.** Profile the heaviest frames: Composition Profiler in the GUI, or
   `AEX.project.profile(comp, t, dir, 10)`. Fix the top row first: pre-render (Import & Replace
   Usage), proxy heavy footage (`AEX.project.makeProxy(item, dir, 0.5, "High Quality")` writes
   ProRes 422), or swap to a lighter effect. While working in Advanced 3D, keep Draft 3D on and
   Render Quality and Smoothness low; raise them only for the final (Jake Bartlett, 6wQjuplvypI
   00:09:32). Draft 3D is a GUI switch: `comp.draft3d = true` reads back false [live 27.0]. GATE:
   `msPerFrame` within budget or the remaining cost explained.
9. **Reduce.** Archive a copy, then `app.project.removeUnusedFootage()` and
   `app.project.reduceProject([main])`. GATE: audit errors 0; the main comp renders the same frames.
10. **Save, collect, prove.** `AEX.project.saveVersion(dir, base)`. For handoff,
    `AEX.project.collect(dest, main, name)` copies sources and relinks to the copies. Render
    headless with `ae.py aerender` and `ae.py probe`. For a shared project, a person sets Auto-Save
    with Maximum Project Versions (Settings > Auto-Save; older versions are deleted) (Adobe
    documentation). GATE: every footage path under `dest`; aerender exit 0; the after sheet matches
    the before sheet where nothing was meant to change.

Variants of one element: build one precomp, expose controls with `AEX.project.expose`, override per
instance on the precomp layer's `essentialProperty` group, read them back with
`AEX.project.overrides`. GATE: the source comp is unchanged and each instance shows its own values.

## Numbers

| Value                                      | Number                                                                                                                                                   | Relative to                                     |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Real-time frame budget                     | 1000 / fps ms (40 ms at 25 fps)                                                                                                                          | comp frame rate                                 |
| Profiler colors                            | green up to half real time; 100 ms to 5 s yellow to red                                                                                                  | per layer, current frame                        |
| Multi-Frame Rendering CPU reserve          | 0 to 70 %, default 10 %                                                                                                                                  | machine                                         |
| Speculative Preview idle delay             | 8 s default                                                                                                                                              | preference                                      |
| Proxy size and codec                       | 50 % of source; ProRes 422, not the Animation codec (Motion Science, y3Qgs2N5z1Y 00:00:55); output template "High Quality" writes ProRes 422 [live 27.0] | footage resolution                              |
| Proxy frame time, UHD H.264 source         | 277 ms with proxy, 570 ms without (one frame, caches purged) [live 27.0]                                                                                 | one Apple Silicon Mac: measure yours            |
| Multi-Frame Rendering gain, heavy UHD comp | 9.9 s off, 6.7 s on for 25 frames; no gain on a light 1080p comp [live 27.0]                                                                             | one Apple Silicon Mac under load: measure yours |
| Scripted profile resolution                | about 13 ms per frame of noise over 10 frames                                                                                                            | render queue timing                             |
| Advanced 3D working quality                | Render Quality 12, Smoothness 2 (Jake Bartlett, 6wQjuplvypI 00:09:32)                                                                                    | per comp, raise for final                       |
| Upscale warning                            | above 105 %                                                                                                                                              | footage pixels                                  |
| Bit depth                                  | 8 for simple graphics, 16 for finishing, 32 for linear and HDR                                                                                           | project                                         |
| Naming                                     | `MAIN_`, `PC_`, `UNUSED_`, version `_v###`                                                                                                               | items and files                                 |

## Quality gates

Measurable: inventory BLOCK lines at zero ([critique.md](references/critique.md)), `Proxy Use-str`
"Use No Proxies" on final queue items, `aerender` exit 0, ffprobe size, rate and frame count equal
the brief. Visual: before and after contact sheets of the main comp. Compare frames exactly
(`magick compare -metric AE`, no fuzz) where nothing was meant to change: 0 pixels for rename, bins,
reduce and collect. Allow a tolerance only where a re-encode sits between the two frames (an H.264
render against a PNG), and state it; find it by encoding the untouched project once and comparing.
Relinked shots are the right shots; replaced fonts still fit; collapsed 3D still sorts with outside
layers.

## Common mistakes

| Mistake                                         | Symptom                                            | Fix                                                             |
| ----------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------- |
| Trusting `getFontsByPostScriptName`             | audit says fonts are fine, render shows a fallback | `usedFonts[i].font.isSubstitute`                                |
| Conforming comps late                           | jittery cuts, keys between frames                  | conform first, re-snap, check `offFrameKeys`                    |
| Disabling an effect on a collapsed 3D precomp   | layers still render behind outside 3D layers       | delete the effect, or move it inside the precomp                |
| Effect on a collapsed layer with point controls | gradient or light sweep stuck to the comp frame    | turn collapse off (Jake Bartlett, Ns41v75th_I 00:09:14)         |
| Collapsed 3D precomp shows nothing in 3D        | inner camera ignored                               | add a camera in the parent comp                                 |
| Draft render with proxies on                    | soft frames in a review render                     | set Proxy Use "Use No Proxies"                                  |
| Typo in working space                           | color management silently off                      | validate against `listColorProfiles()`                          |
| Reduce Project on the only copy                 | comps for later versions gone                      | archive `_v###` first, reduce the delivery copy                 |
| Profiling with warm caches                      | everything looks cheap                             | purge All Memory & Disk Cache first                             |
| Opening another project with unsaved changes    | After Effects stops answering (Save As panel)      | save first; never switch projects in a person's session unasked |
| Renaming comps or layers with a plain `name =`  | expressions fail, "layer named 'X' is missing"     | `AEX.project.rename`, then read `exprErrors`                    |
| Relinking by first match                        | wrong take with the same file name                 | stop on ambiguity, show the user                                |

## Handoffs

- Receives layered art and generated assets from scenario-after-effects-generation (generated media
  lands there first) and from people.
- Delivers a clean, versioned project to every domain sibling: scenario-after-effects-animation,
  scenario-after-effects-typography, scenario-after-effects-compositing, scenario-after-effects-3d,
  scenario-after-effects-vfx.
- Hands render settings, color pipeline and delivery files to scenario-after-effects-color-delivery.
- Hands batch versioning, MOGRT export and render automation to scenario-after-effects-scripting;
  template variants and their creative review to scenario-after-effects-motion-production.
- Expression errors found in the audit go to scenario-after-effects-expressions.

## Version notes

- 22.0: Multi-Frame Rendering, Composition Profiler, `Property.essentialPropertySource`,
  `app.setMultiFrameRenderingConfig()`. "Master Properties" is the pre-17.5 name of Essential
  Properties.
- 24.3: `app.purge(PurgeTarget.ALL_CACHES)` also clears the disk cache.
- 24.5: `Project.usedFonts` and `replaceFont()`. Before that, replace fonts per layer through the
  TextDocument.
- 25.2 and 26.0: disk cache playback and Lossless Compressed Playback reduce the need for playback
  proxies.
- 26.2 and 26.3: SVG import and Illustrator paste as shape layers; fewer reasons to continuously
  rasterize imported vectors.
- 27.0: Auto-Save works before the first save and recovers after a crash; the AI Assistant can
  rename and organize items (credits per action, a person must confirm).

## References

- [references/procedures.md](references/procedures.md): every job, its channel, its checked line and
  what to read in the result.
- [references/critique.md](references/critique.md): the rubric for calling a project clean.
- [references/expert-notes.md](references/expert-notes.md): principles by expert, with timestamps.
- [references/gui-paths.md](references/gui-paths.md): menus and settings for the same work by hand.
- [references/sources.md](references/sources.md): videos, documentation and live measurements.
- [scripts/project.jsx](scripts/project.jsx): the `AEX.project` helper module.
