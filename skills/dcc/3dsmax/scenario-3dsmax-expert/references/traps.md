# Current 3ds Max traps (2027.3)

Facts follow `3dsmax-version-deltas` and the saved docs. Each trap gives the symptom, the fix and
the sibling skill that owns the domain. None has been checked in a running 3ds Max.

## Across domains

| #   | Trap                                              | Symptom                                                                                                   | Fix                                                                                                                                                | Owner                              |
| --- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 1   | System units changed under existing geometry      | scale off by 10x or 2.54x, broken modifiers                                                               | set units before modeling; rescale or merge into a clean file; 2027.1 adds Preferences > Files unit rules and `ignoreFileUnits:`                   | scenario-3dsmax-scene              |
| 2   | Geometry far from the origin                      | jitter, flicker, wrong normals                                                                            | move to the origin, keep the offset on a helper; the audit flags 1 km [added]                                                                      | scenario-3dsmax-scene              |
| 3   | Scale left on the transform                       | mirrored normals, skin and export errors                                                                  | Reset XForm, then collapse, before modifiers, UVs or export                                                                                        | scenario-3dsmax-modeling           |
| 4   | OpenPBR default since 2026                        | new materials are OpenPBR, not Physical; the viewport shows a simplified shader                           | name the material class in the plan; full viewport shader through `CurrentDefaults.ini`                                                            | scenario-3dsmax-materials          |
| 5   | OCIO default for new scenes                       | V-Ray or Corona looks wrong; EXR normal maps read as linear color                                         | choose OCIO or Gamma per studio; set normal and roughness maps to Raw                                                                              | scenario-3dsmax-lighting-rendering |
| 6   | Arnold flags in Object Properties                 | visibility or shadow flags do nothing                                                                     | use the Arnold Properties modifier                                                                                                                 | scenario-3dsmax-lighting-rendering |
| 7   | Render to Texture habits                          | legacy Scanline tool, wrong normals                                                                       | Bake to Texture; match MikkT with the Preferences Normal Bump mode; `BakeToTexture.getCompatibleMapTypes()` is incomplete until `showDialog()` ran | scenario-3dsmax-uv-baking          |
| 8   | Boolean OpenVDB voxel size                        | the default 1.0 destroyed a 5 in object; 0.1 worked (uDfhmKCdR0U 00:11:30)                                | set voxel size per Boolean, relative to the object in system units                                                                                 | scenario-3dsmax-modeling           |
| 9   | Chamfer version                                   | old results in new files                                                                                  | Chamfer `SetVersion #VerLatest`; Smart Bevel above the Boolean                                                                                     | scenario-3dsmax-modeling           |
| 10  | glTF export limits (2027.3 Khronos exporter)      | hierarchy flattened, vertex colors gone, duplicate names get `_1`, multi/sub nesting past two levels lost | run `xio.gltf_precheck()`; glTF Material for glTF targets                                                                                          | scenario-3dsmax-game-assets        |
| 11  | Exporter settings are global state                | the same batch gives different files                                                                      | set FBX parameters in the job; record them in the report (ArchViz Explained, xGm1OBHd50Y 00:05:28)                                                 | scenario-3dsmax-scripting          |
| 12  | Newer file in an older 3ds Max                    | file will not open                                                                                        | open in an equal or newer release; never "fix" by resaving (xGm1OBHd50Y 00:01:23)                                                                  | scenario-3dsmax-scene              |
| 13  | Phoenix end of support (April 2026)               | no fixes, no new seats                                                                                    | plan new fluid work in tyFlow (Zenith)                                                                                                             | scenario-3dsmax-fx                 |
| 14  | Gaussian splats are native Point objects (2027.2) | V-Ray and Corona do not render them                                                                       | Arnold renders and relights them                                                                                                                   | scenario-3dsmax-scene              |
| 15  | Animation layers removed                          | controller paths renamed, Motion Mixer maps break                                                         | regenerate the maps after collapsing layers                                                                                                        | scenario-3dsmax-animation-rigging  |

## Agent and MCP traps

- The Autodesk 3ds Max MCP server is off by default. It is a Tech Preview that Autodesk may suspend.
- Scripting "doesn't work with Claude Code in the terminal". The client needs MCP Apps support to
  show the script for approval.
- Read/write (level 2) runs no scripts. Safe MAXScript (level 10) is needed.
- "New token on connect" breaks the client entry at each restart. "New token on demand" keeps it.
- A blocked command stays blocked for the rest of the session. Check with `max_check`
  (`channel="mcp-safe"`) before sending.
- External clients may suggest shell or batch-file workarounds. The doc says to use the in-3ds Max
  workaround for the blocked step instead.
- Settings stored in INI files cannot be set (`setINISetting` is blocked). Ask the user to set
  exporter options by hand.
- Files cannot be deleted or copied. Save under new names and leave cleanup to the user.
- Menus, toolbars, hotkeys and startup scripts cannot be added. The user may save a script into
  `scripts\startup` and restart.
- A script cannot close a dialog it opened. Avoid opening any.
- Modal dialogs (missing files, units mismatch from `maxstart.max`, a stuck render) block renders.
  Fix the cause first.
- An Arnold render can crash 3ds Max. Reading a Batch Render view's camera crashes it. Biped
  `scaleFootprints` and footstep retiming crash it. Save first.
- Scripts cannot overwrite rendered `.tx` files, re-imported `.abc` caches, or text files a script
  opened.
- The Autodesk Assistant checks in after 10 tool steps and stops at 25. Long chats raise the error
  rate, so start a new chat per task.
- The Assistant may not recognize objects an external client created.
- MCP is not available in 3ds Max Batch.
- Community bridges run anything with no approval step. Connection drops were the main time cost in
  one test: 25 of 35 minutes lost, fixed by updating the bridge (UuWmWAvB4Y0).
- A viewport grab in the first seconds after launch can come back at the wrong shading level
  (max-mcp README, as reported in research). Redraw, then capture.

## pymxs traps

- Main thread only. `pymxs.mxstoken()` is deprecated and does not work.
- MAXScript arrays are 0-based from Python, but index arguments to MAXScript functions stay 1-based.
- Compare nodes with `==`, not `is`.
- `max ...` commands need `rt.execute("max tool zoomextents all")`.
- `render()` skips the Render Setup pre and post scripts. Use `#preRender` and `#postRender`
  callbacks.
- Change render settings with `renderSceneDialog` closed.
- `loadMaxFile` replaces the scene without a prompt, and `saveMaxFile` overwrites silently.
- Set bitmap format options, then the filename, then save.
