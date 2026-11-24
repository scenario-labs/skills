# GUI paths: scripting and pipeline

For a human or a computer-use agent doing the procedures by hand. Menu names are from the saved 2027
docs unless marked [verify]. Layouts and workspaces can move menus; search Customize User Interface
when a path is missing.

## Running code (P1 to P4)

| Task                                        | Path                                                                                |
| ------------------------------------------- | ----------------------------------------------------------------------------------- |
| Open the Listener                           | Scripting > MAXScript Listener (F11 [verify])                                       |
| Python mode in the Listener                 | Listener language switch to Python, then Ctrl+Enter to run [verify switch location] |
| Open the Editor                             | Scripting > MAXScript Editor (also New Script, Open Script)                         |
| Run the whole Editor buffer                 | Ctrl+E (Evaluate All)                                                               |
| Run the selected lines                      | Shift+Enter                                                                         |
| Run a file with `__name__` or a coding line | Scripting > Run Script, pick the `.py`                                              |
| Record actions as MAXScript                 | Listener > MacroRecorder > Enable; do the action; read the echo                     |
| Clear the Listener                          | Listener > Edit > Clear All [verify]                                                |

## Events and UI (P5 to P7)

| Task                                              | Path                                                                                     |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Find a docked tool panel                          | Right-click any toolbar area or the dock area; panels with a title appear there [verify] |
| Assign a macro to a menu, toolbar, hotkey or quad | Customize > Customize User Interface (category from the `.mcr`)                          |
| Hotkeys                                           | Customize > Hotkey Editor [verify]; packages ship `.hsx` files as "hotkey parts"         |

## Batch (P8)

- 3dsmaxbatch is a command-line program next to `3dsmax.exe` in the install folder. There is no GUI
  path.
- Debug the job first in a GUI session: Scripting > Run Script on the job file with a test scene
  open.

## Import and export (P9)

| Task                   | Path                                                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| Import                 | File > Import > Import (glTF in 2027.3: "glTF 2.0 (KHRglTFImporter_adsk)")               |
| Merge from a .max file | File > Import > Merge                                                                    |
| Export                 | File > Export > Export (glTF: "GL Transmission Format"); File > Export > Export Selected |
| FBX presets            | FBX export dialog > Presets; the last settings stay for the next quiet export            |
| USD export options     | File > Export, pick USD, review the options each time (Chaos, PqwD_pHSv9M 00:00:40)      |

## Scene files (P10)

| Task                                            | Path                                                                                 |
| ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| Save a copy without changing the open file name | File > Save Copy As [verify]                                                         |
| Save to an older release                        | File > Save As, "Save as type" lists the older versions                              |
| Unit rules on load and merge (2027.1)           | Customize > Preferences > Files: Respect System Units in Files, load and merge rules |
| System unit                                     | Customize > Units Setup > System Unit Setup                                          |

## Images and render (P11, P12)

| Task                                                 | Path                                                     |
| ---------------------------------------------------- | -------------------------------------------------------- |
| Render Setup                                         | Rendering > Render Setup (F10); renderer list at the top |
| Pre-render and post-render scripts (UI renders only) | Render Setup > Common > Scripts [verify tab name]        |
| Scene Converter (materials)                          | Rendering > Scene Converter                              |
| Viewport screenshot                                  | Tools > Views - Grab Viewport [verify]                   |

## Packages, startup, pip (P13 to P15)

| Task                         | Path                                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| Per-user package folder      | `%APPDATA%\Autodesk\ApplicationPlugins\<Tool>`                                              |
| All-users package folder     | `%ALLUSERSPROFILE%\Autodesk\ApplicationPlugins\<Tool>`                                      |
| Test one package folder      | set `ADSK_APPLICATION_PLUGINS` to it before starting 3ds Max (2022.2+)                      |
| Silence package error popups | `[PluginPackageManager] ShowMessageDialogOnError=0` in the 3ds Max INI                      |
| User startup scripts         | the user `scripts\startup` folder; files there run at every start                           |
| pip                          | a terminal: `<3ds Max install>\Python\python.exe -m pip install --user <pkg>` [verify path] |

## Autodesk 3ds Max MCP server (context for mcp-safe)

| Task                              | Path                                                                                      |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| Turn on the server, set the level | Customize > Preferences > MCP (levels 0, 1, 2, 10, 20; 20 needs admin)                    |
| Approve a proposed script         | the script preview dialog in 3ds Max (on by default for external clients)                 |
| Safe Scene Script Execution       | Customize > Preferences, security settings [verify tab]; `-safescene` command-line switch |
