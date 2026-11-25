# GUI paths (lead)

The same procedures for a person or a computer-use agent. Menu names are those of After Effects 27.0
in English. Shortcuts are given as macOS / Windows.

Labels followed by a number were confirmed on 27.0 with `app.findMenuCommandId(label)`. The number
is the command id for `app.executeCommand(id)`. A menu command acts on the active panel and
selection and can open a dialog: in a job, prefer the scripting API.

## Connect

| Step                         | Path                                                                                                                                                         |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Allow scripts to write files | After Effects > Settings > Scripting & Expressions > Allow Scripts to Write Files and Access Network (Windows: Edit > Preferences > Scripting & Expressions) |
| Run a script file once       | File > Scripts > Run Script File... (8000)                                                                                                                   |
| Install a script             | File > Scripts > Install Script File... (10500, restart needed); Install ScriptUI Panel... (10501)                                                           |
| Startup scripts folder       | the `Scripts/Startup` folder inside the user preferences folder of the installed version                                                                     |
| Switch off the Home screen   | Settings > Startup & Repair... (3201), the Home screen option                                                                                                |

## Inspect

| What                                                   | Path                                                                                                                               |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| Project settings (bit depth, color, expression engine) | File > Project Settings... (2611; Cmd+Opt+Shift+K / Ctrl+Alt+Shift+K)                                                              |
| Missing footage, fonts, effects                        | File > Dependencies > Find Missing Footage (4004), Find Missing Fonts (4003), Find Missing Effects (4002)                          |
| Unused and duplicate items                             | File > Dependencies > Remove Unused Footage (2109), Consolidate All Footage (2107), Reduce Project (2735), Collect Files... (2482) |
| What uses a footage item                               | Project panel: select the item, read the usage line next to the thumbnail, or right-click > Reveal in Composition (2775)           |
| Every key on a layer                                   | select the layer, press U. Press U twice for every changed property.                                                               |
| Every expression                                       | select layers, press E twice                                                                                                       |
| Expressions with errors                                | Reveal Expression Errors (2731)                                                                                                    |
| Effect Controls                                        | F3                                                                                                                                 |
| Composition settings                                   | Composition > Composition Settings... (2007; Cmd+K / Ctrl+K)                                                                       |
| Render time per layer                                  | Timeline panel: the snail icon at the bottom left opens the Composition Profiler column                                            |

## Protect the project

| Step                                    | Path                                                                        |
| --------------------------------------- | --------------------------------------------------------------------------- |
| Save a numbered version                 | File > Increment and Save (3088; Cmd+Opt+Shift+S / Ctrl+Alt+Shift+S)        |
| Save a copy                             | File > Save As > Save a Copy... (2166, opens a save dialog)                 |
| Undo, with the name of the last action  | Edit > Undo <name> (Cmd+Z / Ctrl+Z)                                         |
| Step back through history               | Edit > History (2995)                                                       |
| Auto-Save settings                      | Settings, the Auto-Save page                                                |
| Empty caches (agent-owned session only) | Edit > Purge (2370) > All Memory (2373), All Memory & Disk Cache... (10200) |

## Swap a placeholder by hand

1. Select the placeholder layer in the timeline.
2. Select the new footage in the Project panel.
3. Hold Opt / Alt and drag the footage onto the layer, or press Cmd+Opt+/ (Ctrl+Alt+/). The layer
   keeps its effects, keys and trims.
4. Different size: precompose the clip first (Layer > Pre-compose... 2071, Cmd+Shift+C /
   Ctrl+Shift+C) into a comp of the placeholder's size, then swap the precomp in. Fit inside the
   precomp with Layer > Transform > Fit to Comp (2156; Cmd+Opt+F / Ctrl+Alt+F).

## Change a font

| Step                              | Path                                                                                 |
| --------------------------------- | ------------------------------------------------------------------------------------ |
| One layer                         | select the text layer, then the Properties panel or Window > Character               |
| Find missing fonts in the project | File > Dependencies > Find Missing Fonts (4003)                                      |
| See what a layer uses             | Window > Properties (5004) or Window > Character (3011) with the text layer selected |

## Look at the result

| Step                       | Path                                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------ |
| Save the current frame     | Composition > Save Frame As (2233) > File... (2003; Cmd+Opt+S / Ctrl+Alt+S)          |
| Preview at full frame rate | Space, with the Preview panel set to Full resolution and Skip 0                      |
| 100 percent zoom           | press / in the Composition panel                                                     |
| Title and action safe      | the grid and guide button at the bottom of the Composition panel > Title/Action Safe |
| Alpha channel              | the channel button at the bottom of the Composition panel > Alpha                    |

## Render

| Step                      | Path                                                                               |
| ------------------------- | ---------------------------------------------------------------------------------- |
| Add to Render Queue       | Composition > Add to Render Queue (2161; Cmd+Shift+/ / Ctrl+Shift+/)               |
| Send to Media Encoder     | Composition > Add to Adobe Media Encoder Queue... (3800)                           |
| Output module templates   | Render Queue: the arrow next to Output Module, or Edit > Templates > Output Module |
| Switch one queue item off | the checkbox at the left of the item in the Render Queue                           |
| Headless render           | `aerender` in the application folder, from a terminal                              |
