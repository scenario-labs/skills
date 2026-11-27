# Sources: scripting and pipeline tools

API names in this skill come only from the Autodesk pages below; anything else carries `[verify]`.
Video ids open as `https://www.youtube.com/watch?v=<id>`.

## Autodesk documentation: Python (2027 unless stated)

| Page                         | Best for                                               | URL                                                                                                                                |
| ---------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| Using pymxs                  | rt alias, indexing, Name values, `getpropnames`, byref | https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/MAXDEV_Python_using_pymxs_html.html                               |
| pymxs differences            | what has no Python form: `$`, `max` commands, gizmos   | https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/using_pymxs/MAXDEV_Python_using_pymxs_pymxs_differences_html.html |
| pymxs renderer               | `render()`, callbacks, Render Setup, viewport DIB      | https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/using_pymxs/MAXDEV_Python_using_pymxs_pymxs_renderer_html.html    |
| pymxs bitmaps                | bitmap create, save, close from Python                 | https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/using_pymxs/MAXDEV_Python_using_pymxs_pymxs_bitmaps_html.html     |
| Threading                    | main thread only, `mxstoken` deprecated                | https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/MAXDEV_Python_threading_html.html                                 |
| Creating Python UIs          | qtmax, dock widgets, accelerators, icons               | https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/MAXDEV_Python_creating_python_uis_html.html                       |
| Executing Python             | Editor, Listener, `-U PythonHost`, `python.Execute`    | https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/MAXDEV_Python_executing_python_html.html                          |
| Python API what's new        | Python and PySide per release, removals                | https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/MAXDEV_Python_what_s_new_in_3ds_max_python_api_html.html          |
| Python API what's new (2026) | 2026 interpreter version                               | https://help.autodesk.com/cloudhelp/2026/ENU/MAXDEV-Python/files/MAXDEV_Python_what_s_new_in_3ds_max_python_api_html.html          |

## Autodesk documentation: MAXScript (2027)

| Page                             | Best for                                                                 | URL                                                                                                                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| What's new in MAXScript          | 2027 to 2027.3 additions                                                 | https://help.autodesk.com/cloudhelp/2027/ENU/MAXScript-Help/files/What-is-New-in-MAXScript/What-s-New-in-MAXScript-in-3ds.html                                                                  |
| Scene file access                | `loadMaxFile`, `saveMaxFile`, `mergeMAXFile`, `importFile`, `exportFile` | https://help.autodesk.com/cloudhelp/2027/ENU/MAXScript-Help/files/MAXScript-Tools-and-Interaction/File-Access/3ds-Max-Scene-Files-Access/GUID-624D3D05-B15D-4A97-9F15-DA35CDB0DDD2.html         |
| Import and export filters        | filter interfaces (few documented)                                       | https://help.autodesk.com/cloudhelp/2027/ENU/MAXScript-Help/files/3ds-Max-Objects-and-Interfaces/Import-and-Export-Filters/GUID-5F4CDEC6-288D-4C33-91FA-0CB1AF4121C7.html                       |
| Bitmap values                    | bitmap keywords, save order, close, compare                              | https://help.autodesk.com/cloudhelp/2027/ENU/MAXScript-Help/files/MAXScript-Language-Reference/Values/Bitmap-Values/GUID-9F6ABEE1-0728-4B39-8903-D909634C1304.html                              |
| Viewport drawing, getViewportDib | `gw` methods, redraw callbacks, capture                                  | https://help.autodesk.com/cloudhelp/2027/ENU/MAXScript-Help/files/MAXScript-Tools-and-Interaction/Interacting-with-the-3ds-Max/Viewports/GUID-1B088FF0-6A36-420E-9F37-F0DBE9FB2676.html         |
| Python interop                   | `python.Execute`, `ExecuteFile`, `Init`, `GetLastError`                  | https://help.autodesk.com/cloudhelp/2027/ENU/MAXScript-Help/files/Interaction-with-Other/GUID-E9BA617D-50E5-447F-997B-4F640F1110BA.html                                                         |
| Render to Texture                | `render` keywords such as `outputSize:`, `vfb:`                          | https://help.autodesk.com/cloudhelp/2027/ENU/MAXScript-Help/files/MAXScript-Tools-and-Interaction/Interacting-with-the-3ds-Max/Render-To-Texture/GUID-61344DFE-8DA6-4E19-A184-BFD9ED093EFF.html |

## Autodesk documentation: batch, startup, packages

| Page                              | Best for                                      | URL                                                                                                                        |
| --------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 3dsmaxbatch (2020)                | options, `mxsCmdLineArgs`, exit codes         | https://help.autodesk.com/cloudhelp/2020/ENU/3DSMax-Batch/files/GUID-48A78515-C24B-4E46-AC5F-884FBCF40D59.htm              |
| 3ds Max Batch overview (2027)     | current scope, license                        | https://help.autodesk.com/cloudhelp/2027/ENU/3DSMax-Batch/files/GUID-0968FF0A-5ADD-454D-B8F6-1983E76A4AF9.htm              |
| Command-line options (2024)       | `-mxs`, `-silent`, `-U`, `-safescene`, `-log` | https://help.autodesk.com/cloudhelp/2024/ENU/3DSMax-Basics/files/GUID-1A97CFEC-60A3-4221-B9C3-5C808E2AED35.htm             |
| PackageContents.xml format (2026) | elements, attributes, Description values      | https://help.autodesk.com/cloudhelp/2026/ENU/MAXDEV-Developer/files/writing_plug-ins/plugin_package/packagexml_format.html |
| Packaging plug-ins (2025)         | folders, ADSK_APPLICATION_PLUGINS, errors     | https://help.autodesk.com/cloudhelp/2025/ENU/MAXDEV-Developer/files/writing_plug-ins/plugin_package/packaging_plugins.html |
| Safe Scene Script Execution       | embedded script scan, `-safescene`            | https://help.autodesk.com/cloudhelp/2027/ENU/3DSMax-Getting-Started/files/GUID-7D0E9C58-0BA2-4D17-822E-A3962D68A2F1.htm    |

## Autodesk documentation: formats

| Page                  | Best for                                     | URL                                                                                                                                             |
| --------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| glTF export           | limits: flattening, vertex colors, materials | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-Interoperability/files/geometry_file_formats/GUID-5B4C8EC2-2230-4F9F-B3C6-48D9E347E37D.html |
| glTF import           | importer options and material targets        | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-Interoperability/files/geometry_file_formats/GUID-85FB7E09-D764-4E95-9F9B-6A79E3F0CD9F.html |
| glTF in 2027.3        | Khronos plug-ins shipped                     | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-WhatsNew/files/whats_new_in_3ds_max_2027.3/GUID-38EA97CA-E0B8-45D2-9539-1BF47BDE494D.html   |
| USD import and export | supported data, file types                   | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-USD/files/USD-for-3ds-Max/GUID-F10D6301-D66C-48CE-8D33-65E482734A84.html                    |

## Autodesk documentation: MCP server (2027.3, tech preview)

| Page                       | Best for                              | URL                                                                                                                                               |
| -------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Overview                   | what the server does                  | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-D2B6DF5A-95EF-49DF-BDE1-ACB61212BE20.html                                      |
| Admin configure            | levels 0 to 20, environment variables | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-6C4E10E5-7611-46D3-9F4E-EFE99BB9B716.html                                      |
| Connect an external client | ports, token, client requirements     | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-48002624-B8CE-4F3C-A16C-DE80FD409E5A.html                                      |
| Known limitations          | block list, dialogs, crashes          | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-25CAA219-2BF8-46C9-82BA-F97D369B6026.html                                      |
| Special terms              | tech preview terms                    | https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-17338963-38FE-4A13-A727-DCC64A965E39.html                                      |
| Assistant and MCP FAQ      | MCP not in batch, script preview      | https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Autodesk-Assistant-and-MCP-servers-in-Maya-and-3ds-Max-FAQ.html |

## Videos

| Expert            | Credential                 | Video       | Best for                                           | Best timestamps                                            |
| ----------------- | -------------------------- | ----------- | -------------------------------------------------- | ---------------------------------------------------------- |
| Alexander Richter | pipeline TD, TD Academy    | EiMNwO4buOQ | Listener-first method, pymxs traps                 | 00:22:40, 00:26:34, 00:35:00, 00:40:30, 00:41:06           |
| Alexander Richter | pipeline TD, TD Academy    | Fete0ClQ-3A | MacroRecorder, Editor, fileIn, sys.path (2017 era) | 00:02:29, 00:05:14, 00:06:24, 00:12:37, 00:14:40           |
| Paul Neale        | rigging and tools TD       | ZW5RvjnjxqE | external editor with MXSPyCOM                      | 00:07:13                                                   |
| ArchViz Explained | archviz production channel | xGm1OBHd50Y | batch converter design                             | 00:01:23, 00:02:30, 00:03:03, 00:03:50, 00:04:21, 00:05:28 |
| Daniel Szalapski  | plug-in developer          | 9tf-8Zwkq5I | plug-in install routes                             | whole video                                                |
| Arch Viz Artist   | archviz channel            | c3acjyR7j7E | safe habits with generated scripts                 | 00:04:28, 00:05:02, 00:08:59, 00:09:37                     |
| 3D GROUND         | archviz tools channel      | GQv8Y_8eiBU | create then capture to test a script               | 00:01:08                                                   |
| 3D GROUND         | archviz tools channel      | XpWCMn9Nboc | naming and layer conventions                       | whole video                                                |
| Autodesk (Martin) | 3ds Max product team       | ZoIY5lT6IV4 | MacroRecorder, coordsys                            | 00:00:03, 00:01:40, 00:05:22                               |
| Chaos             | V-Ray developer            | PqwD_pHSv9M | USD export settings and orientation                | 00:00:40                                                   |

## Community code

| Project | Best for                                                            | URL                                  |
| ------- | ------------------------------------------------------------------- | ------------------------------------ |
| max-mcp | QTimer main-thread queue pattern for a socket bridge (not Autodesk) | https://github.com/elturky38/max-mcp |
