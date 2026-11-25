# GUI paths (After Effects 27.0, macOS names; Windows in brackets)

For a person, or a computer-use agent, doing the same procedures by hand. Every scripted procedure
in `procedures.md` has its menu equivalent here.

## Project intake

| Task                                       | Path                                                                                                                           |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Save a copy before touching anything       | File > Save As > Save a Copy                                                                                                   |
| Increment and Save                         | File > Increment and Save, Cmd+Option+Shift+S [Ctrl+Alt+Shift+S]                                                               |
| Save as XML (diff and search names, paths) | File > Save As > Save a Copy As XML (`.aepx`)                                                                                  |
| Project flowchart (who uses what)          | Composition > Composition Flowchart, Cmd+F11 [Ctrl+F11]                                                                        |
| Composition Mini-Flowchart                 | Tab in the Timeline                                                                                                            |
| Find missing footage                       | Project panel search field menu: Missing Footage; File > Dependencies > Find Missing Footage                                   |
| Relink one item                            | Select footage > File > Replace Footage > File, Cmd+H [Ctrl+H]; the dialog relinks others found in the same folder             |
| Find missing fonts                         | File > Dependencies > Find Missing Fonts selects the affected layers; set the replacement in the Character or Properties panel |
| Find missing effects                       | File > Dependencies > Find Missing Effects                                                                                     |
| Reveal on disk                             | Right-click item > Reveal in Finder [Reveal in Explorer]                                                                       |

## Settings

| Task                                                    | Path                                                                                                                          |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Bit depth, working space, Linearize Working Space       | File > Project Settings > Color; Option-click [Alt-click] the bpc readout at the bottom of the Project panel cycles 8, 16, 32 |
| OCIO color engine                                       | File > Project Settings > Color > Color Engine: OCIO color managed                                                            |
| Time display (frames or timecode)                       | File > Project Settings > Time Display Style                                                                                  |
| Expression engine                                       | File > Project Settings > Expressions: JavaScript                                                                             |
| Renderer                                                | Composition > Composition Settings > 3D Renderer tab                                                                          |
| Preserve frame rate or resolution when nested           | Composition > Composition Settings > Advanced                                                                                 |
| Interpret footage (frame rate, alpha, color)            | Select footage > File > Interpret Footage > Main, Cmd+Option+G [Ctrl+Alt+G]                                                   |
| Interpret Unlabeled Alpha default                       | Settings > Import                                                                                                             |
| Auto-Save, Maximum Project Versions                     | Settings > Auto-Save                                                                                                          |
| Disk cache size and location, Empty Disk Cache          | Settings > Media & Disk Cache                                                                                                 |
| Multi-Frame Rendering, CPU reserved                     | Settings > Memory & Performance                                                                                               |
| Speculative Preview idle delay                          | Settings > Previews                                                                                                           |
| Allow Scripts to Write Files and Access Network         | Settings > Scripting & Expressions                                                                                            |
| Start in Safe Mode, Empty All Caches, Reset preferences | Settings > Startup & Repair; or hold Cmd+Option+Shift [Ctrl+Alt+Shift] at launch to reset                                     |

## Structure

| Task                                              | Path                                                                                            |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| New folder (bin)                                  | File > New > New Folder, Cmd+Option+Shift+N [Ctrl+Alt+Shift+N]                                  |
| Pre-compose                                       | Layer > Pre-compose, Cmd+Shift+C [Ctrl+Shift+C]; "Move all attributes into the new composition" |
| Collapse Transformations / Continuously Rasterize | The sun-shaped switch in the Switches column (F4 toggles Switches and Modes)                    |
| Open the parent comp of a precomp                 | Shift+Esc opens the most recently active comp in the network                                    |
| Label colors                                      | Right-click > Label; 16 colors, set in Settings > Labels                                        |

## Speed

| Task                                    | Path                                                                                                                                   |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Composition Profiler                    | Snail icon at the bottom left of the Timeline, or right-click a column heading > Columns > Render Time                                 |
| Purge before profiling                  | Edit > Purge > All Memory & Disk Cache                                                                                                 |
| Adaptive Resolution off while profiling | Settings > Previews > Adaptive Resolution, or the Fast Previews menu in the Composition panel                                          |
| Create a proxy                          | Select footage > File > Create Proxy > Movie (or Still); set the output module to "High Quality" (ProRes 422 in 27.0) before rendering |
| Attach or remove a proxy                | File > Set Proxy > File, or None                                                                                                       |
| Proxy use in the final render           | Render Settings > Proxy Use: Use No Proxies                                                                                            |
| Pre-render a nested comp                | Composition > Pre-render (adds a queue item with Post-Render Action: Import & Replace Usage)                                           |
| Render Queue speed readout              | Render Queue > Info: frames per second, average frame time, concurrent frames                                                          |
| Region of Interest, Draft 3D            | Composition panel toolbar buttons; Draft 3D is GUI only (`comp.draft3d = true` reads back false)                                       |

## Cleanup and delivery

| Task                          | Path                                                                                                                                                                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Remove Unused Footage         | File > Dependencies > Remove Unused Footage                                                                                                                                                                                           |
| Reduce Project                | Select the comps to keep > File > Dependencies > Reduce Project                                                                                                                                                                       |
| Consolidate duplicate footage | File > Dependencies > Consolidate All Footage                                                                                                                                                                                         |
| Collect Files                 | File > Dependencies > Collect Files: Collect Source Files (All, For All Comps, For Selected Comps, For Queued Comps), Generate Report Only, Obey Proxy Settings, Reduce Project (the dialog is modal: never trigger it from a script) |

## Essential Properties

| Task                                      | Path                                                                                                                                                |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Open the panel on a comp                  | Window > Essential Graphics; set Primary comp                                                                                                       |
| Expose a property                         | Drag it into the Essential Graphics panel, or right-click > Add Property to Essential Graphics                                                      |
| Show only exposable properties            | Essential Graphics > Solo Supported Properties                                                                                                      |
| Override on an instance                   | Twirl the precomp layer > Essential Properties; edit the value (it turns bold)                                                                      |
| Push or Pull an override                  | Right-click the overridden (bold) property: Push applies it to the source and every instance, Pull discards it; the group-level commands relink all |
| Edit an exposed Source Text in the parent | Right-click > Edit Value (Type tools do not work there)                                                                                             |
