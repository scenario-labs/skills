# Sources

## Autodesk documentation (read 2026-11-24)

| Source                                                                                                                                                                                                                          | Best for                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 3ds Max MCP Overview: https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-D2B6DF5A-95EF-49DF-BDE1-ACB61212BE20.html                                                                                              | what the server is, tool levels                                                                   |
| Connect an external client: https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-48002624-B8CE-4F3C-A16C-DE80FD409E5A.html                                                                                        | setup steps, ports, tokens, MCP Apps requirement, "doesn't work with Claude Code in the terminal" |
| Known limitations: https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-25CAA219-2BF8-46C9-82BA-F97D369B6026.html                                                                                                 | block list, dialogs, crashes, file limits                                                         |
| Admin configuration: https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-6C4E10E5-7611-46D3-9F4E-EFE99BB9B716.html                                                                                               | levels, `ADSK_3DSMAX_*` variables, registry precedence, `SKIP_PROPOSE`                            |
| Special terms: https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-MCP/files/GUID-17338963-38FE-4A13-A727-DCC64A965E39.html                                                                                                     | Tech Preview status                                                                               |
| Assistant and MCP FAQ (2026-11-20): https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Autodesk-Assistant-and-MCP-servers-in-Maya-and-3ds-Max-FAQ.html                                           | script preview, 10 and 25 step limits, 45-day retention, not in Batch                             |
| Safe Scene Script Execution: https://help.autodesk.com/cloudhelp/2027/ENU/3DSMax-Getting-Started/files/GUID-7D0E9C58-0BA2-4D17-822E-A3962D68A2F1.htm                                                                            | scene script scanning                                                                             |
| 3ds Max Batch (2027 overview): https://help.autodesk.com/cloudhelp/2027/ENU/3DSMax-Batch/files/GUID-0968FF0A-5ADD-454D-B8F6-1983E76A4AF9.htm                                                                                    | what batch is                                                                                     |
| 3dsmaxbatch options (2020 page): https://help.autodesk.com/cloudhelp/2020/ENU/3DSMax-Batch/files/GUID-48A78515-C24B-4E46-AC5F-884FBCF40D59.htm                                                                                  | options, `-mxsString`, `-mxsValue`, exit codes                                                    |
| Using pymxs: https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/MAXDEV_Python_using_pymxs_html.html                                                                                                               | runtime, names, arrays                                                                            |
| Python threading: https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/MAXDEV_Python_threading_html.html                                                                                                            | main thread rule, `mxstoken`                                                                      |
| pymxs renderer: https://help.autodesk.com/cloudhelp/2027/ENU/MAXDEV-Python/files/using_pymxs/MAXDEV_Python_using_pymxs_pymxs_renderer_html.html                                                                                 | `render(outputFile=)`, callbacks                                                                  |
| Scene file access (MAXScript): https://help.autodesk.com/cloudhelp/2027/ENU/MAXScript-Help/files/MAXScript-Tools-and-Interaction/File-Access/3ds-Max-Scene-Files-Access/GUID-624D3D05-B15D-4A97-9F15-DA35CDB0DDD2.html          | `loadMaxFile`, `saveMaxFile`, `importFile`, `exportFile`, `#noPrompt`                             |
| glTF export (2027.3): https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-Interoperability/files/geometry_file_formats/GUID-5B4C8EC2-2230-4F9F-B3C6-48D9E347E37D.html                                                           | exporter limits                                                                                   |
| Viewport capture (2022 MAXScript page): https://help.autodesk.com/cloudhelp/2022/ENU/MAXScript-Help/files/MAXScript-Tools-and-Interaction/Interacting-with-the-3ds-Max/Viewports/GUID-1B088FF0-6A36-420E-9F37-F0DBE9FB2676.html | `gw.getViewportDib`                                                                               |

Version facts per release are compiled in the project's version-deltas file, which cites each
what's-new page.

## Practitioners (YouTube)

| Expert                   | Credential                                               | Video                                                    | Best for                                                              | Best timestamps                              |
| ------------------------ | -------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------- |
| Forever Stu (Napalm_art) | professional interior archviz artist, 3ds Max and Corona | https://www.youtube.com/watch?v=kBo57xFC3ic (2026-09-15) | staged briefs, orthographic QC, correction list, what not to delegate | 00:03:12, 00:08:50, 00:14:06, 00:29:18       |
| Arch Viz Artist          | archviz educator channel                                 | https://www.youtube.com/watch?v=UuWmWAvB4Y0 (2026-10-19) | eight real agent tasks with timings, prompt constraints, capture rule | 00:03:16, 00:04:20, 00:07:05, frame 00:03:04 |
| Arch Viz Artist          | archviz educator channel                                 | https://www.youtube.com/watch?v=c3acjyR7j7E (2026-09-29) | comparing agents, assumptions list, naming the renderer               | 00:04:28, 00:05:02, 00:05:36                 |
| 3D GROUND                | author of the Max Ultra MCP bridge                       | https://www.youtube.com/watch?v=XpWCMn9Nboc (2026-09-07) | scene cleanup by an agent, layer 0 empty, self-verification           | 00:00:32, 00:01:05, 00:01:38                 |
| 3D GROUND                | author of the Max Ultra MCP bridge                       | https://www.youtube.com/watch?v=GQv8Y_8eiBU (2026-10-14) | bridge install, create plus capture test                              | 00:01:08                                     |
| ArchViz Explained        | archviz tutorial channel                                 | https://www.youtube.com/watch?v=xGm1OBHd50Y (2026-04-02) | batch conversion, version mismatch, exporter global state             | 00:01:23, 00:03:03, 00:05:28                 |
| (poly-modeling digest)   | modeling tutorial                                        | https://www.youtube.com/watch?v=uDfhmKCdR0U              | OpenVDB voxel size                                                    | 00:11:30                                     |

## Community bridges (READMEs, read 2026-11-24)

- 3dsmax-mcp: https://github.com/cl0nazepamm/3dsmax-mcp (native bridge, atomic undo per script, 3ds
  Max 2023 to 2027).
- Max Ultra MCP: https://github.com/maxpkg-dev/max-ultra-mcp and
  https://digitalproduction.com/2026/09/14/max-ultra-mcp-puts-ai-agents-inside-3ds-max/ (localhost
  listeners with a token, viewport capture, render control).
- max-mcp: https://github.com/elturky38/max-mcp (TCP 127.0.0.1:20228, main-thread pump through a Qt
  timer).
- Port 47635 used by `max_env` for Max Ultra MCP was seen on screen in a video frame, not in a
  README [added].
