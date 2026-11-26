# Traps (lead)

Measured on After Effects 27.0, macOS, unless a source is named.

## Common mistakes

| Mistake                                                                                         | Symptom                                                                                                                          | Fix                                                                                                       |
| ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Reference kept across `addProperty`                                                             | "Object is invalid"                                                                                                              | fetch the property again by match name                                                                    |
| Layer addressed by index after adding layers                                                    | wrong layer changed                                                                                                              | new layers land on top: use names or `layer.id`                                                           |
| `JSON`, `forEach`, `let` in a job                                                               | syntax or reference error                                                                                                        | ES3 only; `AEK.json`                                                                                      |
| Frame saved and read at once                                                                    | missing or empty PNG                                                                                                             | poll for the file (`AEK.capture.frame` does)                                                              |
| Broken expression assigned                                                                      | no error until evaluated                                                                                                         | `AEK.expr.set` evaluates and raises the message                                                           |
| `replaceSource` with a shorter clip                                                             | layer out point pulled in                                                                                                        | `AEK.session.swap` (fit comp)                                                                             |
| Seconds used for timing                                                                         | off by a frame at other rates                                                                                                    | frames, with the frame rate stated                                                                        |
| `alert()` used as a probe                                                                       | every later job waits                                                                                                            | `AEK.log()`; the runner shadows dialogs                                                                   |
| Display names (`property("Position")`)                                                          | fails on non-English installs                                                                                                    | match names (`ADBE Position`)                                                                             |
| `~/` path                                                                                       | "File couldn't be opened for writing"                                                                                            | absolute path from `ARGS`                                                                                 |
| Frame saved from a 32 bpc project                                                               | almost black sheet: values are written divided by 10                                                                             | `ae.py sheet ... --gain 10`                                                                               |
| New project assumed to be at defaults                                                           | it inherits bit depth and working space from the last project                                                                    | read both back, then set them                                                                             |
| Missing font written to a text layer                                                            | silent substitution at render                                                                                                    | `AEK.text.fontExists` first                                                                               |
| A PNG made by ffmpeg imported as a still                                                        | it renders darker than its pixels (a border of 6,10,18 rendered 0,1,4): After Effects applies the file's gAMA chunk              | strip it first: `magick in.png -define png:exclude-chunks=gAMA,cHRM,sRGB,iCCP out.png`                    |
| A string joined to an array with `+` (`"[" + a + "]"`, `s += a`)                                | "invalid numeric result (divide by zero?)": After Effects overloads `+` on arrays as vector math; `"" + a` even returns an array | `a.join(", ")` or `String(a)`                                                                             |
| A Java-era reserved word (`final`, `class`, `int`) as a variable name or an unquoted object key | the whole job fails: "Illegal use of reserved word" (a dotted property, `M.final`, works)                                        | another name, or a quoted key; `ae_check.py` reports both                                                 |
| `AEK.motion.linearKeys` or a hand check on a separated Position after a reopen                  | eased X and Y moves listed as linear: the hidden leader reports its followers' key count with Linear interpolation               | read `X Position` and `Y Position`; skip the leader (`isSeparationLeader`). The kit does since this round |
| `layers.byName` or `property` with a typo                                                       | "null is not an object" on a later line                                                                                          | `AEK.core.layer`, `AEK.core.prop`: they name the missing item and list what exists                        |
| A job ends with unsaved changes on a shared app                                                 | the next agent's raw `app.open` raises a Save As panel; everyone waits                                                           | end every test job with `AEK.core.save(path)`                                                             |

## What blocks a script

| Blocker                                                                                                               | What happens                                                                                                                                                  | Way out                                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Any modal dialog                                                                                                      | Every script and every Apple event waits. The caller only sees a timeout.                                                                                     | Close it. Avoid causing it.                                                                                                                                                                          |
| `alert()`, `confirm()`, `prompt()` in a script                                                                        | A native window opens. `app.beginSuppressDialogs()` does not cover it. Keys and clicks sent to a background app do not close it.                              | The runner shadows the three functions in every job and returns their text in `dialogs`.                                                                                                             |
| Home screen at launch                                                                                                 | It is a modal overlay.                                                                                                                                        | It accepts a posted Return or Escape. It can be switched off in Preferences.                                                                                                                         |
| Disk cache space warning at launch                                                                                    | Modal.                                                                                                                                                        | Accepts a posted key.                                                                                                                                                                                |
| Crash Repair Options after a forced stop                                                                              | Modal at the next launch, default button Continue.                                                                                                            | Accepts a posted Return.                                                                                                                                                                             |
| "3D models or primitives ... require use of the Advanced 3D renderer"                                                 | Raised after a script adds a model layer to a comp on another renderer. A comp made by script is on Classic 3D.                                               | Set `comp.renderer = "ADBE Calder"` (Advanced 3D) before adding the layer.                                                                                                                           |
| `app.open(file)` or `app.newProject()` with unsaved changes in the open project, left by this job or by another agent | A native Save As panel opens. A posted Escape does not close it when the app is in the background. On a shared app it stopped every agent for 3 to 4 minutes. | In a person's session, ask them to save first. In a session the agent owns, close with `CloseOptions.DO_NOT_SAVE_CHANGES` first (`AEK.core.open`, `AEK.core.fresh`). `ae.py run` refuses a raw call. |
| `app.project.save()` on a project that was never saved                                                                | Save As panel, same effect.                                                                                                                                   | `AEK.core.save(path)`; without a path it throws on an untitled project.                                                                                                                              |
| File dialogs (`File.openDialog`, `selectDialog`)                                                                      | Wait for a person.                                                                                                                                            | Paths come from `ARGS`.                                                                                                                                                                              |
| macOS privacy prompts (local network, cloud-synced folders)                                                           | Wait for a person.                                                                                                                                            | Keep agent files out of cloud-synced folders.                                                                                                                                                        |
| macOS Automation permission missing                                                                                   | `DoScriptFile` returns -1712 after the timeout, with no prompt when the screen is locked.                                                                     | Use the bridge channel.                                                                                                                                                                              |

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
- On shape Contents, `canAddProperty(matchName)` returned true for an invented match name. Only
  `addProperty` throws. On a layer's effects group it returned false for an uninstalled effect.
- `layers.precompose` invalidates the reference to the precomposed layer. Keep its name and index
  first.
- `app.project.item(i)` order is not creation order. Find a new item by its `id`.
- Enum values print as numbers. `AEK.core.enumName(KeyframeInterpolationType, v)` gives the name.
- `comp.saveFrameToPng(time, file)` returns at once. The file appears about 100 ms later, longer for
  heavy frames.
- `saveFrameToPng` writes the comp background as alpha 0 (the comp color stays in RGB in an 8 bpc
  project; RGB reads 0 in a 16 bpc project). A viewer shows it white or checkered; dropping alpha
  shows feathered and glowing edges too bright (a 40 px feather read 213 where the composite is
  188). Flatten on the comp color: `ae.py sheet --bg RRGGBB` (`AEK.capture.frame` returns `bg`).
- In a 32 bpc project `saveFrameToPng` writes every value divided by 10: white reads 0.1 and the
  frame looks almost black. At 8 and 16 bpc white reads 1.0. `AEK.capture.frame` returns `bpc` and
  `pngScale`; `ae.py sheet ... --gain 10` shows such frames at their real brightness.
- A failed import throws inside `app.beginSuppressDialogs()` and leaves no dialog.
- `e.line` in a caught error is the line in the evaluated text. The runner maps it back to the job
  body and prints the source line. An error thrown inside a kit module or a `--lib` file comes back
  with `in` (`aekit/core.jsx:43 (function prop)`), `in_source`, and `line` set to the job line that
  calls that function.
- A wrong layer name or match name returns null, and the error appears on the next member access as
  "null is not an object". The runner adds `null_from` and `hint`: the lookups on that line or on
  the line that set the variable, and a near-miss match name
  (`'ADBE Postion': did you mean 'ADBE Position'?`).
- "Object is invalid": a reference taken before an `addProperty` on the same layer (a second mask,
  an effect, a shape group) or before a precompose. Fetch it again by name.
- The preferences file uses classic Mac line endings (CR only). Split on `\r` to parse it.
- Reading a delivered H.264 back with ffmpeg's default conversion gave values about 1.7 levels lower
  than After Effects on the same file. Measure with
  `scale=in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int` before judging blacks.

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
  with "Directory does not exist" after about 15 s of launch; `ae.py aerender` creates the folder
  first (`created_folder`).
- A new queue item reads `NEEDS_OUTPUT` until its output module has a file. The Draft Settings
  render template uses the proxies set in the project; Best Settings does not.
- `aerender` starts `aerendercore`, a second After Effects that runs the user Startup scripts with
  `app.isRenderEngine` false. A bridge 1.4 started there swept the interactive job as stopped, and
  once took a job from the inbox and ran it inside the render engine, where `saveFrameToPng` wrote
  nothing for 60 s. Bridge 1.5.0 checks its own process name (`MacOS/After Effects`) and stays off
  elsewhere.
- A full output volume: an H.264 render printed "An output module failed" and left a 24-byte file; a
  ProRes render printed "Finished composition", exited 0 and left a 1 MB file that ffprobe cannot
  read. `ae.py aerender` reports both as failed.
- Every aerender failure measured on 27.0 exited with code 0: full disk (three forms), a collision
  on one output folder, a stop at frame 22 of 72 while other renders ran. Never read the exit code
  alone; read `ok`, `why` and `checks`, then rerun once, alone.
- On a shared machine, the first Advanced 3D frame of a new scene took over 60 s while other renders
  ran (10.7 s alone), and a 6 s aerender took 93 s next to another one. `AEK.capture.frame`,
  `frames` and `spread` take a timeout in ms as their last argument; the default is
  `AEK.capture.timeoutMs`, 180000.
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
- In a shape layer the first group in Contents draws on top. `AEK.build.shape(comp, name, [specs])`
  adds groups in spec order, so `specs[0]` is the top group.
- Mask mode is the `maskMode` attribute (`mask.maskMode = MaskMode.SUBTRACT`);
  `mask.property("ADBE Mask Mode")` returns null.
- The selector Amount of a text animator sits under the Advanced group: `ADBE Text Selector` >
  `ADBE Text Range Advanced` > `ADBE Text Selector Max Amount`. `AEK.text.animator(layer, {amount})`
  sets it and returns it as `amount` for keys.
- A text layer parented to a null: its own Position is in parent space. `AEK.text.measure` and
  `inFrame` walk the parent chain (anchor, scale, Z rotation, position); a measured box matched
  `toComp()` within 0.001 px. 3D layers are read flat.

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
