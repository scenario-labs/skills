# Critique: is the project production ready?

Run this rubric before calling a project clean. Every line is a number read from the project or a
picture read from a contact sheet. A project passes only when every BLOCK line passes; WARN lines
need a written reason in the handoff note.

## Measured (from `AEX.project.inventory(main)` and the kit audit)

| Check                               | Pass                                                                                                                                        | Level                      | Read it from                                                                                                                                                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Missing footage                     | 0                                                                                                                                           | BLOCK                      | `inventory.missing.length`                                                                                                                                                                                            |
| Missing fonts                       | 0 substitutes                                                                                                                               | BLOCK                      | `inventory.missingFonts.length` (uses `Font.isSubstitute`, as the kit `fonts.missing` rule does)                                                                                                                      |
| Missing effects                     | 0, or each one listed with an owner and a native fallback                                                                                   | BLOCK                      | audit rule `effect.missing`                                                                                                                                                                                           |
| Expression errors                   | 0                                                                                                                                           | BLOCK                      | audit rule `expression.error`                                                                                                                                                                                         |
| Expressions after a scripted rename | 0 errors                                                                                                                                    | BLOCK                      | `AEX.project.rename(...).exprErrors`                                                                                                                                                                                  |
| Default names                       | 0 comps matching `Comp N`, `Pre-comp N`                                                                                                     | BLOCK                      | `inventory.defaultNames`                                                                                                                                                                                              |
| Comp frame rates                    | one rate, or a lower rate only with `preserveNestedFrameRate` true                                                                          | BLOCK                      | `inventory.compRates`, `inventory.nestedRateMismatch`                                                                                                                                                                 |
| Keys between frames after a conform | 0                                                                                                                                           | BLOCK                      | `AEX.project.offFrameKeys(comp)` per conformed comp                                                                                                                                                                   |
| Collapsed precomps that flatten     | 0, unless the flattening is the intent                                                                                                      | WARN                       | `inventory.collapseRisks` (enabled and disabled effects both count)                                                                                                                                                   |
| Footage frame rate unlike its comp  | listed and accepted (real-speed footage), never conformed blindly                                                                           | WARN                       | audit rule `layer.frameRateMismatch`                                                                                                                                                                                  |
| Unused comps and footage            | 0 in the delivered project; archived copy keeps them                                                                                        | WARN                       | `inventory.unusedComps`, `inventory.unusedFootage`                                                                                                                                                                    |
| Every item in the bin scheme        | 0 items at the project root except bins                                                                                                     | WARN                       | `item.parentFolder === app.project.rootFolder`                                                                                                                                                                        |
| Color settings                      | bit depth and working space equal the brief; working space never "None" by accident                                                         | BLOCK                      | `AEX.project.color({})` read back                                                                                                                                                                                     |
| Proxies at final render             | queue items read "Use No Proxies"                                                                                                           | BLOCK                      | `rqi.getSetting("Proxy Use-str")`                                                                                                                                                                                     |
| Upscaled footage                    | none above 105 % unless approved                                                                                                            | WARN                       | audit rule `layer.upscaled`; it reads the scale at the comp's current time, so an animated push counts when that frame is above 105 %. A short push on a still with pixels to spare is accepted with a written reason |
| Layout per deliverable              | `ok` at the hold frame: inside the safe area, gaps at least 3 % of the shorter side, content spans half the safe height on vertical formats | BLOCK for a campaign       | `AEX.project.layout(dlv, {t, safe})`                                                                                                                                                                                  |
| Odd comp sizes for H.264 or HEVC    | none                                                                                                                                        | BLOCK for those deliveries | audit rule `comp.oddSize`                                                                                                                                                                                             |
| Saved, versioned                    | project file `<name>_v###.aep`, `dirty` false                                                                                               | BLOCK                      | `saveVersion()` result                                                                                                                                                                                                |
| Collected                           | every footage path under the delivery folder                                                                                                | BLOCK for handoff          | `collect()` result, `outside.length === 0`                                                                                                                                                                            |
| Headless render                     | `aerender` exit 0, frame count right, ffprobe size and rate right                                                                           | BLOCK for handoff          | `ae.py aerender`, `ae.py probe`                                                                                                                                                                                       |

## Speed

| Check                                         | Target                                                                                    | How                                                      |
| --------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Frame render time at preview resolution       | under 1000 / fps ms for real-time preview (40 ms at 25 fps); half real time is acceptable | Profiler footer, or `AEX.project.profile()` `msPerFrame` |
| One layer above half of the frame cost        | fix it first: pre-render, proxy, lighter effect                                           | `profile().rows[0].costShare`                            |
| Profiling conditions                          | caches purged, Adaptive Resolution off, same frame range every measure                    | procedure notes                                          |
| Effects without Multi-Frame Rendering support | none on heavy layers                                                                      | yellow icon in Effect Controls (GUI only)                |

The scripted profile measures whole layers, at render quality, through the render queue. It does not
split a layer's cost across its masks, layer styles and individual effects, does not show the cached
asterisk, and does not see a referenced layer's cost: a layer with its video off that an effect uses
(Set Matte, Compound Blur) shows an empty Render Time, and its cost sits in that effect. Read that
effect, not the empty layer. The Composition Profiler does: use it when a person or a computer-use
agent can open the Timeline.

## Visual (contact sheet: `ae.py frames MAIN --spread 6 --sheet`)

- Same frames before and after cleanup: the picture does not change unless a fix meant it to. Diff
  them exactly: `magick compare -metric AE before.png after.png null:` (no fuzz) returns 0 for a
  pure reorganization (rename, bins, collect, reduce). Use a tolerance only when a re-encode sits
  between the two frames (an H.264 render against a PNG frame); state it in the handoff note and
  find it by encoding the untouched project once and comparing that to its own PNG frames.
- Relinked footage shows the right shot at the right time, not a placeholder (color bars) and not a
  different take with the same file name.
- Replaced fonts: text still fits its box and safe area; line breaks did not move.
- Collapsed 3D precomps: layers still sort with outside 3D layers (a card in front of an outside
  plane stays in front).
- Conformed comps: motion holds on whole frames; no doubled or skipped poses at cuts.
- Essential Properties instances: each instance shows its own values; overridden text stays inside
  the rig precomp frame (it is cropped at the precomp bounds).
- Proxy on: the frame looks soft but framed the same; proxy off: full detail, same framing.
- Formats side by side: each one arranged for its ratio (not the master scaled), text never touching
  a rule or another block, a vertical frame without a dead lower half, no visible rectangle around a
  cut-out subject.

## Handoff note (written next to the project)

List: main comp name, frame rate, size, bit depth, working space, renderer per 3D comp, fonts used,
plugins required, every WARN line kept and why, version file name, collected folder.

## Common mistakes

| Mistake                                         | Symptom                                     | Fix                                       |
| ----------------------------------------------- | ------------------------------------------- | ----------------------------------------- |
| Collapsed 3D precomp shows nothing in 3D        | inner camera ignored                        | add a camera in the parent comp           |
| Draft render with proxies on                    | soft frames in a review render              | set Proxy Use "Use No Proxies"            |
| Typo in working space                           | color management silently off               | validate against `listColorProfiles()`    |
| Profiling with warm caches                      | everything looks cheap                      | purge All Memory & Disk Cache first       |
| Relinking by first match                        | wrong take with the same file name          | stop on ambiguity, show the user          |
| Collecting an image sequence by its first file  | the sequence arrives as a still             | `AEX.project.collect` copies every frame  |
| Setting 16 bpc on a project that inherited OCIO | "Not supported for OCIO color managed mode" | `AEX.project.color` sets the engine first |
