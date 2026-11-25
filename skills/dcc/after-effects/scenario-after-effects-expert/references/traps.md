# Traps (lead)

Measured on After Effects 27.0, macOS, unless a source is named.

## What blocks a script

| Blocker                                                                         | What happens                                                                                                                     | Way out                                                                                                                                                              |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Any modal dialog                                                                | Every script and every Apple event waits. The caller only sees a timeout.                                                        | Close it. Avoid causing it.                                                                                                                                          |
| `alert()`, `confirm()`, `prompt()` in a script                                  | A native window opens. `app.beginSuppressDialogs()` does not cover it. Keys and clicks sent to a background app do not close it. | The runner shadows the three functions in every job and returns their text in `dialogs`.                                                                             |
| Home screen at launch                                                           | It is a modal overlay.                                                                                                           | It accepts a posted Return or Escape. It can be switched off in Preferences.                                                                                         |
| Disk cache space warning at launch                                              | Modal.                                                                                                                           | Accepts a posted key.                                                                                                                                                |
| Crash Repair Options after a forced stop                                        | Modal at the next launch, default button Continue.                                                                               | Accepts a posted Return.                                                                                                                                             |
| "3D models or primitives ... require use of the Advanced 3D renderer"           | Raised after a script adds a model layer to a comp on another renderer. A comp made by script is on Classic 3D.                  | Set `comp.renderer = "ADBE Calder"` (Advanced 3D) before adding the layer.                                                                                           |
| `app.open(file)` or `app.newProject()` with unsaved changes in the open project | A native Save As panel opens. A posted Escape does not close it when the app is in the background.                               | In a person's session, ask them to save first. In a session the agent owns, close with `CloseOptions.DO_NOT_SAVE_CHANGES` first (`AEK.core.open`, `AEK.core.fresh`). |
| File dialogs (`File.openDialog`, `selectDialog`)                                | Wait for a person.                                                                                                               | Paths come from `ARGS`.                                                                                                                                              |
| macOS privacy prompts (local network, cloud-synced folders)                     | Wait for a person.                                                                                                               | Keep agent files out of cloud-synced folders.                                                                                                                        |
| macOS Automation permission missing                                             | `DoScriptFile` returns -1712 after the timeout, with no prompt when the screen is locked.                                        | Use the bridge channel.                                                                                                                                              |

## ExtendScript

- ES3 only: `var`, function expressions, `for` loops. No `let`, `const`, arrow functions, template
  strings, `JSON`, `Array.forEach`, `map`, `indexOf`, `Object.keys`, `String.trim`, trailing commas.
- A reserved word used as an object key (`{in: 1}`, `{with: 1}`, `{x: 1, default: 2}`) is a syntax
  error for the whole job: "Illegal use of reserved word". Quote the key. `ae_check.py` reports it.
- `setTimeout` does not exist. `app.scheduleTask(code, ms, repeat)` does.
- `~` is not always the home folder. With Desktop and Documents synced by a cloud provider,
  `Folder("~")`, `Folder.myDocuments` and `Folder.desktop` returned the provider's folder.
  `Folder.userData` is reliable.
- After `addProperty` on a shape, text or effect group, earlier references into that layer are
  invalid ("Object is invalid"). Fetch the property again.
- `canAddProperty(matchName)` returned true for an invented match name. Only `addProperty` throws.
- `layers.precompose` invalidates the reference to the precomposed layer. Keep its name and index
  first.
- `app.project.item(i)` order is not creation order. Find a new item by its `id`.
- Enum values print as numbers. `AEK.core.enumName(KeyframeInterpolationType, v)` gives the name.
- `comp.saveFrameToPng(time, file)` returns at once. The file appears about 100 ms later, longer for
  heavy frames.
- In a 32 bpc project `saveFrameToPng` writes every value divided by 10: white reads 0.1 and the
  frame looks almost black. At 8 and 16 bpc white reads 1.0. `AEK.capture.frame` returns `bpc` and
  `pngScale`; `ae.py sheet ... --gain 10` shows such frames at their real brightness.
- A failed import throws inside `app.beginSuppressDialogs()` and leaves no dialog.
- `e.line` in a caught error is the line in the evaluated text. The runner maps it back to the job
  body and prints the source line.
- The preferences file uses classic Mac line endings (CR only). Split on `\r` to parse it.

## New projects and color settings

- `app.newProject()` keeps the bit depth, working space and linear blending of the project that was
  open before it. A project made after a 32 bpc ACEScg session came up at 32 bpc ACEScg, linearized.
  Read the three values back and set them. `AEK.core.fresh()` writes the defaults (Adobe color
  engine, 8 bpc, no working space, linear blending off) in a session the agent owns.
- The color engine is inherited too. `app.project.colorManagementSystem` is a number on 27.0 (0
  Adobe color management, 1 OCIO); no `ColorManagementSystem` enum exists in ExtendScript. Set the
  engine before the bit depth.
- Never add Apply Color LUT (`ADBE Apply Color LUT2`) from a job: it opens a file panel that blocks
  the application.
- `app.project.workingSpace = "<a name that does not exist>"` throws nothing and switches color
  management off (`None`). Take names from `app.project.listColorProfiles()` and read the value
  back.

## Undo and saving

- One `app.beginUndoGroup(name)` ... `app.endUndoGroup()` pair is one Undo. `ae.py run --undo NAME`
  adds the pair around the job.
- `app.executeCommand(16)` is Edit > Undo. `app.findMenuCommandId("Undo")` does not return it,
  because the menu label carries the action name.
- `app.project.dirty` stays true after an undo.
- `app.project.replaceFont(from, to)` returns true and is not undoable. The next Undo then reverted
  an earlier, unrelated change. Use the text document route.
- `app.project.save(file)` is Save As: the open project moves to the new file. `File.copy` of the
  `.aep` copies the last saved state only.
- File > Increment and Save is command 3088. On a saved project it wrote `<name> 2.aep` with no
  dialog. A project that was never saved has no file to increment: ask the person to save it first.
- A forced stop (`kill`) is treated as a crash: Crash Repair Options at the next launch and a crash
  copy of the project in the Documents folder. Quit with `app.quit()` in a session the agent owns,
  never in a person's session.

## Render queue

- `renderQueue.render()` renders every queued item, the person's included, and blocks until done.
- `rqi.render` can be set only on items that are queued or unqueued.
- Output module templates differ per install. Read them (`ae.py templates`) before naming one.
- A queue item without an output module template can write the wrong format. One expert's batch
  produced 26 AIFF files that way (School of Motion, uo5k4_vu5Vk 00:22:39).
- "Lossless" is a legacy default (Animation codec, 8 bits per channel). "High Quality" and "High
  Quality with Alpha" write ProRes (SternFX, FZ9yfCeZZMA 00:07:29). Measured:
  `High Quality with Alpha` wrote ProRes 4444, `yuva444p12le`, premultiplied.
- `aerender` with a comp name that does not exist prints "aerender ERROR: No comp was found with the
  given name." and exits with code 0. Read the log and probe the file. A missing output folder fails
  with "Directory does not exist": create it first.
- A new queue item reads `NEEDS_OUTPUT` until its output module has a file. The Draft Settings
  render template uses the proxies set in the project; Best Settings does not.
- `aerender` takes no script arguments and reads the saved file. A comp on the Cinema 4D renderer
  can fail silently in `aerender` (version notes of the documentation set).

## Import

| File                                        | Result on 27.0                                                                                                 |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| PNG, EXR, HDR, SVG                          | still footage; SVG sized from the file                                                                         |
| H.264 MP4, HEVC 10-bit MOV, ProRes 4444 MOV | footage; alpha read on ProRes 4444                                                                             |
| WebM VP9 with alpha                         | refused: "not a valid file type for import"                                                                    |
| SRT                                         | refused                                                                                                        |
| WAV, MP3                                    | audio-only footage                                                                                             |
| GLB, OBJ, FBX                               | footage reported as 1920x1080, 30 s, 30 fps; becomes a model layer in a comp                                   |
| PNG sequence                                | arrives at the preference frame rate (30 fps), not the rate it was made for: set `mainSource.conformFrameRate` |

## Renderer match names

| `comp.renderer`    | Renderer                                              | Tells                                                                                 |
| ------------------ | ----------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `ADBE Advanced 3d` | Classic 3D (the start value of a comp made by script) | no text extrusion; layer motion blur works                                            |
| `ADBE Calder`      | Advanced 3D                                           | extrusion, models, environment lights; `layer.motionBlur = true` on a 3D layer throws |
| `ADBE Ernst`       | Cinema 4D                                             | extrusion; the same motion blur error; can fail silently in `aerender`                |

## Layers and text

- New layers land on top. Indices of existing layers shift by one. Use names, `layer.id` (22.0) or
  re-read indices after each add.
- `layer.name` returns the source name when the layer was never named. `AEK.session.swap` writes the
  name back so a swap does not rename the layer.
- `layer.replaceSource(item, false)` keeps effects, masks, keys and transforms. With a shorter clip
  the out point moves in and cannot be extended past the source.
- `layer.parent = other` keeps the layer where it is on screen and rewrites Position in parent
  space.
- Renaming a layer or an effect by script does not rewrite the expressions that name it. They break
  at the next evaluation, and the first read after the rename can return 0 with no error text.
  Rewrite the references in the same job (scenario-after-effects-expressions has a helper).
- `comp.duplicate()` raises the trailing number of the name (`MASTER_16x9` became `MASTER_16x10`)
  and shares nested comps and footage with the original. Set the name at once.
- Changing `comp.frameRate` keeps keys at their time in seconds: keys on frames 15, 20 and 30 at 30
  fps sat on 12.5, 16.67 and 25 at 25 fps.
- A font that is not installed is accepted silently and substituted at render.
  `app.fonts.missingOrSubstitutedFonts` keeps the name for the rest of the session even after the
  layer is fixed.
- Setting `textDocument.font` restyles the whole text. Mixed runs (bold start, regular end) need
  `characterRange(a, b).font` per run (24.3). `AEK.session.setFont` with a `map` keeps each run's
  weight.
- Scale reports three dimensions even on a 2D layer and needs three `KeyframeEase` objects per side.
  Position takes one.
- In a shape layer the first group in Contents draws on top.

## Version traps

| Topic                                                                                         | Since     | Outdated habit to avoid                                                  |
| --------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------ |
| JavaScript expression engine is the default                                                   | 16.0      | ExtendScript-flavored expressions; `this` instead of `thisLayer`         |
| Multi-Frame Rendering, Composition Profiler                                                   | 22.0      | "Render Multiple Frames Simultaneously"; omitting `-mfr` with `aerender` |
| `Layer.id`, `Project.layerByID()`                                                             | 22.0      | addressing layers only by index                                          |
| Any layer as track matte, `setTrackMatte()`                                                   | 23.0      | placing the matte directly above its target                              |
| H.264 in the Render Queue (MOV in 24.2)                                                       | 23.0      | sending the comp to Media Encoder for an MP4                             |
| OCIO color management, ACES 2.0 configs in 26.5                                               | 23.2      | 8 bpc sRGB for everything; treating OCIO as a plugin                     |
| `app.fonts`, font objects                                                                     | 24.0      | styling without checking that the font exists                            |
| Advanced 3D for final renders; glTF and GLB import                                            | 24.1      | Ray-traced 3D (removed in 17.0), the Cinema 4D renderer for models       |
| OBJ import; cast and accept shadows                                                           | 24.2      | faking shadows with solids                                               |
| Character, paragraph and line ranges in text scripting                                        | 24.3      | restyling the whole layer to change one word                             |
| `app.purge(PurgeTarget.ALL_CACHES)` includes the disk cache                                   | 24.3      | purging in a person's session                                            |
| Shadow catcher (Accepts Shadows = Only); `usedFonts`, `replaceFont()`                         | 24.5      | separate shadow passes                                                   |
| Per-character style in expressions                                                            | 25.0      | one text layer per style                                                 |
| FBX import; animated environment lights                                                       | 25.2      | a plugin for every model                                                 |
| SVG as native shape layers; variable font axes; Substance materials; parametric meshes (UI)   | 26.0      | converting SVG in another app first                                      |
| Object Matte replaces the Roto Brush tool icon                                                | 26.2      | telling the person to pick Roto Brush in the toolbar                     |
| `addParametricMesh()`                                                                         | 26.3      | calling it on 26.0 or 26.2                                               |
| Guide enums changed (breaking)                                                                | 26.5      | hard-coded guide integers                                                |
| AI Assistant (beta), Illustrator text as editable text, Auto-Save independent of manual saves | 27.0      | assuming an outside agent can drive the Assistant                        |
| UXP (beta build only); CEP on a removal path                                                  | 27.1 beta | starting a new CEP panel; saying ExtendScript is going away              |

Minimum systems: 27.0 needs Windows 11 or macOS 15. 26.2 to 26.5 need Windows 11 or macOS 14.
