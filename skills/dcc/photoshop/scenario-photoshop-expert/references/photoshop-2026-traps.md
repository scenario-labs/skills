# Photoshop 2026 traps for agent code

What breaks ExtendScript and Action Manager code written from memory or from older tutorials, and
what the `ps_run` channel can and cannot reach. "Measured" means run in a live Photoshop 27.11 on
macOS while this skill's toolkit was built; "documented" means Adobe documentation or release notes
only; "not tested" means neither. Load this file before writing a job body of your own.

Read `app.version` at session start (`ps_run.py --ping` returns it): descriptors are undocumented
and change between releases, so a trap measured on 27.11 may move on 28.0.

## 1. What the channel reaches

`ps_run` runs ExtendScript through AppleScript `do javascript`. `executeAction` takes the same
Action Manager descriptors that UXP `batchPlay` sends, so a descriptor found in one works in the
other. Out of its reach: the UXP imaging API, `executeAsModal`, secure storage and panels.

The user keeps working while the agent runs. Never bring Photoshop to the front, click screen
coordinates, or open a modal dialog.

| Area                                                                | Through `ps_run`                                                             | GUI only or out of reach                                | Status                                |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------- |
| Document state, layer tree, selection bounds                        | `ps_audit.doc_state`, `layer_find`, `ps_io.selection`                        |                                                         | measured                              |
| Histograms, difference, texture, halo, skin line, structure         | `ps_gates`, on duplicates the job owns                                       |                                                         | measured                              |
| Pixels and masks in or out                                          | through files: `ps_io.export_region`, `export_mask`, `place`                 | the UXP imaging API (pixel buffers) is not reachable    | measured                              |
| Place a file as an embedded smart object in a box                   | `ps_io.place`                                                                |                                                         | measured                              |
| Replace a smart object's contents                                   | `ps_io.replace`                                                              |                                                         | measured (same pixel size keeps box)  |
| One undo step per job, layer provenance                             | `suspendHistory` per job; XMP written by `place`                             |                                                         | measured                              |
| Masks, adjustment and fill layers, Blend If, clipping               | Action Manager (compositing toolkit)                                         |                                                         | measured                              |
| Warp, four-corner fit, Displace, other smart filters                | Action Manager (mockups, compositing toolkits)                               |                                                         | measured                              |
| Select Subject                                                      | `autoCutout`                                                                 | Select and Mask refine brush                            | measured; refine documented           |
| Remove Background, Camera Raw Filter                                | Action Manager, a subset                                                     | most Camera Raw controls                                | documented                            |
| Generative Fill, Expand, Prompt to edit                             | no toolkit call; a recorded Action played with `app.doAction` may replay one | Adobe documents these steps in Actions                  | not tested                            |
| Harmonize, Relight Layer, Rotate Object, Enhance Edge               | no toolkit call                                                              | GUI; no Action step documented                          | not tested                            |
| Generative Upscale                                                  | no toolkit call                                                              | GUI; UXP `Document.generativeUpscale` (27.2 and later)  | documented                            |
| Brush work: painting, healing, Remove strokes, Mixer Brush, Liquify | scaffold layers only                                                         | the strokes                                             | documented                            |
| Actions                                                             | `app.doAction(action, set)` plays a loaded action                            | loading an `.atn` from a script is unverified on 27.11  | not tested                            |
| Export copies (PNG, JPG, TIF, PSD, TGA)                             | `psr_export`, `ps_review.preview`; TGA 32-bit keeps an alpha channel         | PNG keeps transparency, not alpha channels              | measured                              |
| CMYK pixel work                                                     | mode change only; gates measure RGB copies                                   | no CMYK pixel path                                      | documented                            |
| Live type layers                                                    | `ArtLayer` with kind TEXT                                                    |                                                         | measured (key-art toolkit)            |
| 3D layers                                                           | none                                                                         | removed from Photoshop in July 2024                     | documented                            |
| Video layers                                                        | `LayerKind.VIDEO` is detectable                                              | the timeline has no DOM; Render Video is a menu command | documented; placing a clip not tested |

Adobe documents no script call for its generative tools; a forum reports an undocumented batchPlay
descriptor, not tested. Adobe's generative AI guidelines may cover automated use, so these tools
stay manual steps for the user, and an agent plays no Action that holds one. Adobe's generative
features also exist in Adobe's cloud APIs, under an enterprise contract with server credentials and
no access to the document open on the desktop (documented). Skills route generation to the Scenario
MCP and describe Adobe's features as manual alternatives in [gui-paths.md](gui-paths.md).

## 2. The channel itself

- **Exit codes.** 0 ok, 1 the job raised, 2 usage or guard refusal, 3 Photoshop not answering, 4
  timeout, 5 Photoshop not found, 6 macOS refused automation. Shell: `python3 ps_run.py --ping`,
  `--launch` (starts Photoshop without stealing focus), `-e "return app.documents.length"`, or
  `job.jsx --undo "Scenario: name"`.
- **A file alias fails.** `do javascript` given a file alias fails with error 8800 on 27.11, while
  `$.evalFile(new File(path))` inside an inline call runs the same file. `ps_run` inlines it
  (measured).
- **A `.psjs` opened in the background runs nothing.** `open -g -a` on a UXP script ran nothing
  within 13 s, with no dialog (measured).
- **Automation consent.** The first call from a terminal asks macOS for permission; a refusal is
  exit 6. The user allows the terminal under System Settings > Privacy & Security > Automation >
  Adobe Photoshop.
- **Modal dialogs block the channel.** `ps_run` sets `DialogModes.NO`, but a filter or third-party
  dialog can still open; the job then times out (exit 4). A filter left in edit mode also blocks.
- **The active document can change between jobs.** The user keeps working. Read
  `app.activeDocument.name` in every job that edits, and keep dependent steps in one job.
- **ExtendScript is ES3.** No `let`, arrow functions, template strings or `Array.prototype.map` by
  default. Java keywords are reserved: `{native: 1}` fails to compile with "Error 9: Illegal use of
  reserved word" (measured). The regex engine rejects `\u` escapes inside character classes
  (measured; `ps_run`'s JSON encoder escapes by code point instead).
- **Chained ternaries group from the left.** `a ? b : c ? d : e` runs as `(a ? b : c) ? d : e`. A
  left alignment came out right-aligned (measured). Parenthesize every nested ternary.
- **Units.** `ps_run` sets rulers to pixels and type to points for the job, then restores them. At
  72 ppi a point equals a pixel; at other resolutions convert. Path anchors read back in pixels; a
  path drawn through the DOM's `PathPointInfo` takes points.
- **`UnitValue(0) == null` is true.** Test `instanceof UnitValue` before a null check; `ps_run`'s
  JSON encoder does, so zero comes back as 0 (measured).
- **Windows.** COM `DoJavaScript` runs ExtendScript on Windows (documented). The toolkit targets
  macOS only and is not tested on Windows.

## 3. Reading the document

- **Descriptors are undocumented.** Adobe's documented way to find one: record an Action, then
  Actions panel flyout > Copy As JavaScript, available when Developer Mode is on (documented). Test
  the result on a document the job created.
- **Layer kinds.** Read `layerKind` through `executeActionGet`, not the DOM's `ArtLayer.kind`. On
  27.11 the DOM reports a rectangle shape layer as `SOLIDFILL` and throws "Internal error" when
  reading `kind` on a Clarity adjustment layer.
  - Measured codes: pixel 1, adjustment 2 (Levels and Clarity), text 3, shape 4, solid fill 11.
  - From the documented enumeration, not re-checked: smart object 5, video 6, group 7.
  - `ps_audit` reads groups from the DOM typename `LayerSet`, not from code 7.
- **Histograms count selected pixels only**, and `Channel.histogram` reads the active layer only.
  Select the region first; flatten a duplicate to measure a composite. Alpha channels survive a
  flatten (measured). That is how `ps_gates` measures regions.
- **Blend If** set through `blendRange` works, but `executeActionGet` never reports it. Test it by
  its effect on pixels (measured).
- **`smartObjectMore`** returns `size` (content width and height), `transform` and
  `nonAffineTransform` (8 doubles, the four corners), and `warp` (measured).
- **Placement bounds.** A file placed with `placeEvent` lands at native pixel size, centered. Layer
  bounds report the non-transparent content box, not the placed canvas, so `ps_io.place` measures
  the box from `smartObjectMore.transform` instead (measured).

## 4. Editing

- **Free Transform needs `freeTransformCenterState`.** Without it the `transform` event can succeed
  and change nothing, with no error (measured). With it, `height`, `width` and `skew` percentages
  work (used for cast shadows).
- **Custom warp** (`warpStyle: warpCustom`): `bounds` equal to the layer's current box, 16
  `rationalPoint` mesh points (row-major 4x4, Bezier control points), and the box already scaled and
  moved onto the mesh's bounding box. After a good fit, `nonAffineTransform` equals that bounding
  box, a pixel-free self-check (measured).
- **A custom warp lands only on an object scaled up** from the box it was converted at. At that box
  or below, corners drift by up to 60 px, more as the quad leaves its bounding box. Convert to Smart
  Object (`newPlacedLayer`) at a slightly smaller box, then scale up and warp; this also covers a
  smart object placed from a file, which otherwise lands about 10 px off (measured).
- **`warpNone` can leave a transform the next warp rejects** ("Numeric value expected"). Reset with
  a flat custom warp (the box's own grid) instead (measured).
- **Convert to Smart Object keeps only the opaque box** and drops the active selection; moving a
  layer into a group first releases its clipping chain. A hidden layer filling the box keeps the
  margins; store the selection and re-clip the chain after (measured, mockups toolkit).
- **Image Size accepts any interpolation name** (`ImgS` with `Intr`), even a made-up one, without an
  error (measured). Keep names exact (`bicubicAutomatic`, `nearestNeighbor`) and check the output by
  effect. `deepUpscale` gives pixels distinct from bicubic, nearest neighbor and a made-up name, so
  it is likely Preserve Details 2.0, not proven.
- **Replace Contents** (`placedLayerReplaceContents`) keeps the layer's transform: after a 50%
  scale, a 300x200 replacement shows at 150x100, same center. It also renames the layer after the
  new file: restore the name in the same job (measured; `ps_io.replace` does).
- **Displace as a Smart Filter** keeps only the map's path and re-reads it at every re-render. Once
  the map is deleted, the next Replace Contents fails with "the file was not found" (measured).
- **Adjustment layers** (measured):
  - `make` with Curves points in the descriptor is refused: make with the default, then `set`.
  - They are born with a white mask. A second mask fails with "The command Make is not currently
    available"; select the mask channel and edit it instead.
  - `make` needs the RGB composite channel targeted first.
  - Dehaze, Grain, Color Grading and Vignette could not be made by those string IDs ("General
    Photoshop error"); their class names are unknown.
- **`channels.add()` leaves only the new alpha channel active**, which sends later transforms and
  fills to it. Set `doc.activeChannels = doc.componentChannels` right after (found building
  `ps_io`).
- **Loading a channel as a selection fails when no pixel is above 50%** ("Set is not currently
  available"), for example a constant alpha of 128. Copy a channel to another document with
  `Channel.duplicate(doc)` instead (measured, game-art packing).
- **Enum names.** The Color blend mode is `BlendMode.COLORBLEND`; `BlendMode.COLOR` throws "Invalid
  enumeration value" when assigned. Check a new DOM constant by reading and assigning it in a
  try/catch on a scratch layer (measured: 60 constants in the toolkits).
- **Exports into a missing folder** fail with "General Photoshop error occurred. This functionality
  may not be available in this version of Photoshop". `psr_export` creates the folder first
  (measured).
- **Clipping chains** (measured; the position decides):
  - A layer inserted between the base and its first clipped layer unclips the whole chain.
  - A layer moved directly above the chain's top clipped layer joins the chain: it is clipped
    already.
  - `artLayers.add()` puts the new layer at the top of the stack, not above the active layer: move
    it directly above the chain's top.
- **`grouped` is a toggle.** On a layer that is clipped already (directly above a chain's top),
  setting `grouped = true` releases the clip; `grouped = false` on a layer that is not clipped clips
  it (measured on 27.11). Read `grouped`, set it only when it differs, then check it.
- **Select Subject** is `executeAction(stringIDToTypeID("autoCutout"))` with
  `sampleAllLayers: false` (measured).
- **Selections.** ExtendScript has no `Selection.border`. Build a ring as expand, store, contract,
  then `store(channel, SelectionType.DIMINISH)` (measured).
- **Auto-Align** (`Algn`, `ADSContent`) (measured):
  - The projection must be the charID `Auto`; the string ID `auto` is accepted and aligns nothing.
  - On a smart object it returns without error and does nothing: rasterize a copy first.
  - The locked layer is the reference. A Background it touches becomes "Layer 0".
  - Both layers stay targeted after it runs, so a DOM `duplicate` copies both. Select the one layer
    by Action Manager first.
  - It misreads a damaged base (section 6).
- **Text layers** (measured): `artLayers.add()`, then `kind = LayerKind.TEXT`, `textItem.font` by
  PostScript name, `size` in points, `position` as [x, baseline y]. A missing font fails silently
  and the layer keeps the default font: read `textItem.font` back. Point text bounds are what
  renders; a paragraph box hides overflow without an error. `translate` on a text layer works in
  pixels.

## 5. History and documents

- **One job, one History state.** `ps_run` wraps the body in
  `app.activeDocument.suspendHistory(name, ...)` when `undo` is given; the state carries the name
  (measured in the generative-edit suite). Without `undo`, every DOM call may add its own state.
- **History calls need the document frontmost.** After `psr_dup`, the copy is the active document;
  switch back before stepping the source's History (found building `ps_io`).
- **Deleting the active History snapshot** sends the document back to its opening state. Step back
  one state instead (measured).
- **Gate on the active state, never the list length.** Captures, previews and exports step History
  back and leave redo states in the list; making a selection is a state of its own (measured). At
  the History limit the oldest state drops and the index holds still, so an index check fails a
  correct edit there; `A.history_gate` checks the name and that the state is new, and skips the
  index at the limit (verified live at a lowered limit with state ids, `test_history_live.py`; the
  fallback for a version without ids compares names and is not verified at the limit). A job with
  `undo` that throws still leaves its named state, possibly empty: the lead SKILL.md's Quality gates
  say how to recover.
- **At the History limit, read-only calls still cost undo depth.** Mask captures (`IO.export_mask`,
  `export_region(punch_selection=True)`, `GE.capture`), gates on `"selection"` or `"outside"`, and
  the batch and colorway exports push temporary states, then step back. Pixels, layers and the
  active state end as they were, but at the limit each temporary state drops one of the user's
  oldest undo steps. Measured at a limit of 5: one `G.stats` on a selection pushed four. At the
  default of 50 states a long session loses its oldest steps, never pixels. Before a long batch, ask
  the user to raise the limit (Preferences > Performance) or take a snapshot.
- **History stepping does not restore layer visibility** under the default preference, which leaves
  visibility out of History (measured). Restore visibility explicitly.
- **Layer XMP** written on a layer survives save, close and reopen (measured). `ps_io.place` writes
  provenance there, and `layer_xmp` reads it back (verified live).
- **A job that throws closes the documents it created** (`ps_run`), so no temporary copy is left in
  front of the user.

## 6. Generated pixels (measured with real Scenario jobs)

- One image-edit job, two takes, re-rendered the whole frame: mean difference 17 to 18 outside the
  mask on an aligned result, texture redrawn and tone 6 to 7 levels darker. Masked placement hid it:
  outside max 0 after placement, no seam at 100% or 4x.
- The model fills the mask. An ellipse wider than an iris made the generated iris grow to fill it.
- A seam shows when tone or alignment is off, not when texture differs. On blurred images in a ring
  outside the mask: real takes scored tone bias 6.4 and 7.3, residual 3.5 and 3.4; a 3 px shift 12.4
  and 8.8. The generative-edit gate is bias under 12 and residual under 6.
- A colorize or restore defeats a plain difference (mean 29 at 256 px on an aligned restore). The
  tone-blind `ps_gates.structure` score ranked the aligned restore at 11.3, a 3 px shift at 14.0 and
  a drifted copy at 22.7. Auto-Align made the aligned restore worse three times out of three (15.1
  to 29.6) and fixed most of a real drift, so it is kept only when the score drops 10% or more.
- Generative upscalers re-synthesize texture: at source resolution two of them differed from the
  source by 9.4 and 9.5 (a bicubic upscale 3.3, a 2 px blur 11.6), and from each other by 8.6. At a
  256 px long side both scored 4.9, a bicubic upscale 0.5, an 8 px shift 16.8, a color cast 38.5.
  Compare identity at 256 px and read texture change separately.

All figures are authoring-time, from one image per check; check them on your own images.

## 7. Version notes (27.x)

- 27.0 (October 2025): Harmonize, Generative Upscale with partner models in the GUI (documented).
- 27.2: `Document.generativeUpscale` in UXP, limited to Adobe's own model at 2x or 4x (documented).
- 27.6 (April 2026): Actions panel redesign with a single-History-state playback option and an
  Essentials catalog; Layer Cleanup renames layers and removes empty ones (documented).
- 27.9 (July 2026): a new UI backend, "an infrastructure change, not a visual redesign"; 27.9 was
  replaced by 27.9.1 for a color bug. Re-test anything built on an earlier version (documented).
- 27.10 (August 2026): Prompt to edit and Markup; recording Prompt to edit in an Action is listed as
  a fixed bug, so an Action can replay it from the UI (documented).
- 27.11 (the September 2026 release): Enhance Edge on Remove Background masks (documented). The
  toolkit was built and measured on this release.
- Adobe's partner model lineup changes in point releases without a scripting signal. Name the
  Photoshop feature, never the partner model, and log `app.version` with every report.
- The next major is expected around Adobe MAX in November 2026 (inferred). Re-run the live checks on
  it.
