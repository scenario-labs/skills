# Plugin channel: tools and limits

The live channel for this skill is the plugin's local Scenario MCP server, `scenario-blender`; its
full tool reference is the plugin repository's `docs/MCP.md`.

| Need                          | Tool and arguments                                                                                                                  |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Probe before building         | `scene_summary` with `fields` (`["type"]`), `limit` (up to 500) and `offset` from `next_offset`; `datablocks_summary` for counts    |
| One object, a camera's lens   | `object_detail` with `name` (cameras add `lens_mm`, `sensor_width`, `clip`)                                                         |
| Build, key, audit             | `execute_python` with `code`: `bpy` and `result = {}` preloaded; fill `result` with what you need back                              |
| Check an API before scripting | `blender_api_help` with `path`                                                                                                      |
| Step to a beat                | `set_frame` with `frame`                                                                                                            |
| Look through the shot camera  | `render_still` with `source` `CAMERA`, `width` 768, `height` 432 (GUI only); `screenshot_viewport` with `max_size` for the viewport |
| Select objects                | `select_objects` with `names`                                                                                                       |

- `execute_python` stays off until the user enables **Allow connected agents to run Python**; a
  `PermissionError` means ask. Without it only the plugin's Blockout and `camera_path` build, and
  neither makes figures or rigs.
- The plugin stops a call after 120 s and some agent clients stop waiting at 60 s. Send one stage
  piece per call (a set section, one figure, one rig, one audit). Releases up to 0.11.0 ignore
  `limit`, `offset`, `fields` and `max_size`, so `scene_summary` returns every object: check
  `datablocks_summary` on a heavy file first.
- A timed-out call has an unknown outcome: read the scene (`scene_summary` with `name_contains`)
  before sending it again.
- Every changing call records one Undo step; no tool saves the user's file. Run
  `B.stage_backup(label)` after each stage (a copy; the open file stays as it was) and ask the user
  to save at milestones.
