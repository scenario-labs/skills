# Sequencer through Epic's Unreal MCP (5.8.3)

Lookup file for `scenario-unreal-cinematics`. Read the table, copy the JSON. Every recipe below ran
on 5.8.3 (2026-10-21) through `ue_mcp.Mcp` in `tests/code/unreal-cinematics/live_mcp_recipes.py` (it
copies the arena project, saves a small level with a headless Python job, starts its own editor,
runs R1 to R6, saves, stops; exit 0 only if all pass). It passed headless (boot 22 s, 41 s in all).
Nothing here needs `describe_toolset`: `SequencerTools` alone costs about 42,010 tokens to describe,
and probing a tool with `{}` to print its schema costs a failed call each time.

Toolsets (full names): `animation_toolset.toolsets.sequencer.SequencerTools` (SEQ below),
`animation_toolset.toolsets.keyframing.SequencerKeyframingTools` (KEY), plus
`...outliner.SequencerOutlinerTools`, `...conditions.SequencerConditionTools`,
`...custom_bindings.SequencerCustomBindingTools`, `...import_export.SequencerImportExportTools`.
Placing, reading and saving use `editor_toolset.toolsets.scene.SceneTools` (ST),
`...actor.ActorTools` (ACT), `...object.ObjectTools` (OT), `...asset.AssetTools` (AT). No toolset
covers Movie Render Graph or Movie Render Queue: renders go through Python (section 7).

## 1. Names that do not exist

These were guessed in agent runs and fail. Use the right column.

| Guessed                              | Use                                                                                                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `add_camera`, `add_spawnable_camera` | SEQ `create_camera {"spawnable": true}` (acts on the open sequence), or ST `add_to_scene_from_class` with `CineCameraActor` then SEQ `add_actors` |
| `add_actor`, `place_actor`           | ST `add_to_scene_from_class` (a class) or `add_to_scene_from_asset` (a mesh or Blueprint path)                                                    |
| `add_track`                          | SEQ `add_track_to_binding` (actor tracks) or `add_track_to_sequence` (camera cut, audio, fade)                                                    |
| `add_spawnable`                      | SEQ `add_spawnable_from_class {"sequence": ..., "actor_class_path": "/Script/CinematicCamera.CineCameraActor"}` or `add_spawnable_from_instance`  |
| `add_key`, `set_key`                 | KEY `add_key_float` (also `_bool`, `_integer`, `_string`)                                                                                         |
| `get_level_info`                     | ST `get_current_level`, `find_actors`                                                                                                             |
| `list_tools`                         | the signature lines in section 3                                                                                                                  |

## 2. Intent to tool

| Intent                          | Toolset and tool                                                                                                 | Notes (run on 5.8.3 unless marked)                                                                                                                      |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New sequence, rate, length      | SEQ `create_level_sequence`, `set_display_rate`, `set_playback_range`                                            | range end is exclusive: 0 to 120 is 120 frames, 5 s at 24 fps                                                                                           |
| Open it (needed before binding) | SEQ `open_sequence`, `get_current_sequence`                                                                      | `add_actors` and `create_camera` act on the open sequence only                                                                                          |
| Bind a level actor              | SEQ `add_actors {"actors": [ref]}`                                                                               | returns `[]` with ok=true when no sequence is open; once open it adds a transform track with one infinite section                                       |
| Camera with lens tracks         | SEQ `create_camera {"spawnable": true}`                                                                          | spawnable CineCameraActor, a component child with CurrentFocalLength, CurrentAperture, ManualFocusDistance tracks, and a camera cut section bound to it |
| Spawnable from a class          | SEQ `add_spawnable_from_class`                                                                                   | ran from Python in this repo (`ue_cine.add_spawnable`); over MCP not run                                                                                |
| Tracks on a binding             | SEQ `get_tracks_on_binding`, `find_tracks_by_type`, `add_track_to_binding`                                       | track type is `{"refPath": "/Script/MovieSceneTracks.MovieScene3DTransformTrack"}`                                                                      |
| Sections                        | SEQ `get_sections`, `add_section`, `set_section_range`, `has_section_start_frame`                                | a new section from `add_section` spans 0 to 0: set its range                                                                                            |
| Keys                            | KEY `add_key_float`, `get_keys`, `get_channel_names`, `get_default_value`                                        | `frame` is a display frame; channels `Location.X` ... `Scale.Z`; a float section's one channel is `None`                                                |
| What plays (read-back)          | SEQ `set_playhead_frame`, `force_evaluate`; ACT `get_actor_transform`                                            | sample 5 or more frames; see R4                                                                                                                         |
| Camera cut                      | SEQ `add_track_to_sequence` (cut track), `add_section`, `set_section_range`; OT `set_properties` for the binding | `set_camera_cut_binding` fails on 5.8.3 (R5)                                                                                                            |
| Markers                         | SEQ `add_marked_frame`, `get_marked_frames`, `find_marked_frame_by_label`                                        | `frame` is in ticks (1000 per display frame at 24 fps), not display frames                                                                              |
| Rate facts                      | SEQ `get_display_rate`, `get_tick_resolution`, `get_playback_range`                                              | tick 24000/1; `get_playback_range` returns JSON text `{"start": 0, "end": 120}`                                                                         |
| Section ease, blend, completion | SEQ `set_section_ease_in`, `set_section_blend_type`, `set_section_completion_mode`                               | not run here                                                                                                                                            |
| Many calls in one turn          | `editor_toolset.toolsets.programmatic.ProgrammaticToolset.execute_tool_script {"script": "..."}`                 | four or more calls in a row: one script (section 9)                                                                                                     |
| Save                            | AT `save_assets {"asset_paths": ["/Game/Cine/LS_Shot"]}`                                                         | package paths, no `.Name` suffix                                                                                                                        |

## 3. Working call order: a camera path that plays as keyed

This is the order that held on 5.8.3 (R2 to R4). The point of each step is in brackets.

1. ST `load_level` (the sequence binds into the open level).
2. SEQ `create_level_sequence`, `set_display_rate`, `set_playback_range`.
3. ST `add_to_scene_from_class` with `CineCameraActor` at the start pose (its location becomes the
   defaults of the section `add_actors` makes).
4. SEQ `open_sequence` (without it, step 5 returns `[]`).
5. SEQ `add_actors` with the camera (one binding, one transform track, one infinite section).
6. SEQ `get_tracks_on_binding`, then `get_sections` on that track: key **this** section. Do not call
   `add_track_to_binding` with a transform track or `add_section` on it.
7. KEY `add_key_float` per channel at the first and last frame; rotation keys from evaluated
   locations if the camera must face a point.
8. Read back: SEQ `set_playhead_frame`, `force_evaluate`, ACT `get_actor_transform` at 5 or more
   frames; compare with the intended path, not with the keys.
9. Check SEQ `get_tracks_on_binding` returns one transform track, then AT `save_assets`.

**Why a second transform track halves the path (R3).** `add_actors` already made a transform track
whose one section is infinite, Absolute, and holds the actor's location as channel defaults. A
second transform track, or a second section on the same track, also Absolute, overlaps it; Sequencer
blends overlapping absolute sections by weight, so the result is the average of the keyed section
and the unkeyed one. With the camera bound at y = -1000 and keys from -1000 to 1000 on an extra
track, the played path was y = -1000, -495.8, 0 at frames 0, 60, 119: half the distance, first key
right, last key off by half. Keys in the first section with an empty second section (defaults 0)
gave -500, 4.2, 500. Removing the extra track (`remove_track`) and keying the section `add_actors`
made gave -1000, 8.4, 1000. The keys read back fine in every case: only the evaluated transform
shows the fault.

## 4. Struct shapes

`Ref<X>` is `{"refPath": "/Path/Asset.Asset"}`; for a level actor, the refPath the placing tool
returned.

- `FrameRate {"numerator": 24, "denominator": 1}`
- `MovieSceneBindingProxy {"bindingId": "5BB31E00-6146-B991-B0C5-2FB4866035CE", "sequence": {"refPath": "/Game/Cine/LS_Shot.LS_Shot"}}`:
  pass it whole as `binding`.
- `MovieSceneObjectBindingID {"guid": "...", "sequenceId": 0, "resolveParentIndex": 0}`
- `MovieSceneMarkedFrame {"frameNumber": {"value": 60000}, "label": "A", "comment": "", "customColor": {...}, "bUseCustomColor": false, "bIsDeterminismFence": false, "bIsInclusiveTime": false}`
- `SequencerChannelProxy {"channelName": "Location.X", "section": Ref<MovieSceneSection>}` (curve
  editor tools only)
- `ToolsetTransform {"location": {"x": 0, "y": -1000, "z": 200}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0}, "scale": {"x": 1, "y": 1, "z": 1}}`
- `get_keys` returns JSON text: `[{"frame": 0, "value": 35.0}]`. Parse it.
- `add_key_float` `interpolation`: `"linear"`, `"constant"`, `"auto"`, `"user"`, `"break"`; `""` or
  any unknown string gives smart auto; `"cubic"` maps to auto.

## 5. Signature lines

Generated with
`python3 <skills>/scenario-unreal-expert/scripts/gen_toolset_map.py tests/arena/mcp-catalog-5.8.3 sequencer.SequencerTools keyframing outliner conditions custom_bindings import_export`.
`?` marks an optional argument.

### `animation_toolset.toolsets.conditions.SequencerConditionTools` (9 tools, describe is about 2456 tokens)

- `clear_section_condition(section: Ref<MovieSceneSection>) -> bool`
- `clear_track_condition(track: Ref<MovieSceneTrack>) -> bool`
- `clear_track_row_condition(row_index: int, track: Ref<MovieSceneTrack>) -> bool`
- `get_section_condition(section: Ref<MovieSceneSection>) -> str`
- `get_track_condition(track: Ref<MovieSceneTrack>) -> str`
- `get_track_row_condition(row_index: int, track: Ref<MovieSceneTrack>) -> str`
- `set_section_condition(condition_class: str, section: Ref<MovieSceneSection>) -> bool`
- `set_track_condition(condition_class: str, track: Ref<MovieSceneTrack>) -> bool`
- `set_track_row_condition(condition_class: str, row_index: int, track: Ref<MovieSceneTrack>) -> bool`

### `animation_toolset.toolsets.custom_bindings.SequencerCustomBindingTools` (8 tools, describe is about 3969 tokens)

- `change_actor_template_class(actor_class: str, binding: {MovieSceneBindingProxy}) -> bool`
- `convert_to_custom_binding(binding: {MovieSceneBindingProxy}, binding_type_class: str) -> {MovieSceneBindingProxy}`
- `convert_to_possessable(binding: {MovieSceneBindingProxy}) -> {MovieSceneBindingProxy}`
- `convert_to_spawnable(binding: {MovieSceneBindingProxy}) -> [{MovieSceneBindingProxy}]`
- `get_custom_binding_objects(binding: {MovieSceneBindingProxy}) -> [Ref<MovieSceneCustomBinding>]`
- `get_custom_binding_type(binding: {MovieSceneBindingProxy}) -> str`
- `get_custom_bindings_of_type(binding_type_class: str) -> [{MovieSceneBindingProxy}]`
- `save_default_spawnable_state(binding: {MovieSceneBindingProxy}) -> bool`

### `animation_toolset.toolsets.import_export.SequencerImportExportTools` (6 tools, describe is about 3612 tokens)

- `export_anim_sequence(anim_sequence: Ref<AnimSequence>, binding: {MovieSceneBindingProxy}, create_link?: bool, sequence: Ref<LevelSequence>, world: Ref<World>) -> bool`
- `export_fbx(bindings: [{MovieSceneBindingProxy}], fbx_file_path: str, override_options?: Ref<FbxExportOption>, sequence: Ref<LevelSequence>, world: Ref<World>) -> bool`
- `get_linked_anim_sequences(sequence: Ref<LevelSequence>) -> [str]`
- `get_linked_level_sequence(anim_sequence: Ref<AnimSequence>) -> str`
- `import_fbx(bindings: [{MovieSceneBindingProxy}], fbx_file_path: str, import_settings: Ref<MovieSceneUserImportFBXSettings>, sequence: Ref<LevelSequence>, world: Ref<World>) -> bool`
- `link_anim_sequence(anim_sequence: Ref<AnimSequence>, binding: {MovieSceneBindingProxy}, sequence: Ref<LevelSequence>) -> bool`

### `animation_toolset.toolsets.keyframing.SequencerKeyframingTools` (22 tools, describe is about 6464 tokens)

- `add_key_bool(channel_name: str, frame: int, section: Ref<MovieSceneSection>, value: bool) -> bool`
- `add_key_float(channel_name: str, frame: int, interpolation: str, section: Ref<MovieSceneSection>, value: float) -> bool`
- `add_key_integer(channel_name: str, frame: int, section: Ref<MovieSceneSection>, value: int) -> bool`
- `add_key_string(channel_name: str, frame: int, section: Ref<MovieSceneSection>, value: str) -> bool`
- `bake_channel_keys(channel_name: str, end_frame: int, section: Ref<MovieSceneSection>, start_frame: int) -> [float]`
- `close_curve_editor() -> bool`
- `curve_editor_empty_selection() -> bool`
- `curve_editor_select_keys(channel: {SequencerChannelProxy}, indices: [int]) -> bool`
- `get_channel_names(section: Ref<MovieSceneSection>) -> [str]`
- `get_curve_editor_selected_keys(channel: {SequencerChannelProxy}) -> [int]`
- `get_default_value(channel_name: str, section: Ref<MovieSceneSection>) -> float`
- `get_keys(channel_name: str, section: Ref<MovieSceneSection>) -> str`
- `get_keys_by_index(channel_name: str, indices: [int], section: Ref<MovieSceneSection>) -> str`
- `get_selected_channels() -> [{SequencerChannelProxy}]`
- `get_selected_key_channels() -> [{SequencerChannelProxy}]`
- `is_curve_editor_open() -> bool`
- `is_curve_shown(channel: {SequencerChannelProxy}) -> bool`
- `open_curve_editor() -> bool`
- `remove_key_at_frame(channel_name: str, frame: int, section: Ref<MovieSceneSection>) -> bool`
- `select_channels(channels: [{SequencerChannelProxy}]) -> bool`
- `set_default_value(channel_name: str, section: Ref<MovieSceneSection>, value: float) -> bool`
- `show_curve(channel: {SequencerChannelProxy}, show: bool) -> bool`

### `animation_toolset.toolsets.outliner.SequencerOutlinerTools` (18 tools, describe is about 3870 tokens)

- `get_deactivated_nodes() -> [{SequencerViewModelScriptingStruct}]`
- `get_locked_nodes() -> [{SequencerViewModelScriptingStruct}]`
- `get_muted_nodes() -> [{SequencerViewModelScriptingStruct}]`
- `get_node_label(node: {SequencerViewModelScriptingStruct}) -> str`
- `get_outliner_children(node: {SequencerViewModelScriptingStruct}, type_filter?: str) -> [{SequencerViewModelScriptingStruct}]`
- `get_outliner_selection() -> [{SequencerViewModelScriptingStruct}]`
- `get_outliner_tree() -> str`
- `get_pinned_nodes() -> [{SequencerViewModelScriptingStruct}]`
- `get_sections_for_nodes(nodes: [{SequencerViewModelScriptingStruct}]) -> [Ref<MovieSceneSection>]`
- `get_soloed_nodes() -> [{SequencerViewModelScriptingStruct}]`
- `is_node_expanded(node: {SequencerViewModelScriptingStruct}) -> bool`
- `set_node_deactivated(deactivated: bool, nodes: [{SequencerViewModelScriptingStruct}]) -> bool`
- `set_node_expanded(expanded: bool, nodes: [{SequencerViewModelScriptingStruct}]) -> bool`
- `set_node_locked(locked: bool, nodes: [{SequencerViewModelScriptingStruct}]) -> bool`
- `set_node_muted(muted: bool, nodes: [{SequencerViewModelScriptingStruct}]) -> bool`
- `set_node_pinned(nodes: [{SequencerViewModelScriptingStruct}], pinned: bool) -> bool`
- `set_node_solo(nodes: [{SequencerViewModelScriptingStruct}], soloed: bool) -> bool`
- `set_outliner_selection(nodes: [{SequencerViewModelScriptingStruct}]) -> bool`

### `animation_toolset.toolsets.sequencer.SequencerTools` (140 tools, describe is about 42010 tokens)

- `add_actors(actors: [Ref<Actor>]) -> [{MovieSceneBindingProxy}]`
- `add_actors_by_name(actor_names: [str]) -> [{MovieSceneBindingProxy}]`
- `add_actors_to_binding(actors: [Ref<Actor>], binding: {MovieSceneBindingProxy}) -> bool`
- `add_binding_to_folder(binding: {MovieSceneBindingProxy}, folder: Ref<MovieSceneFolder>) -> bool`
- `add_event_repeater_section(track: Ref<MovieSceneEventTrack>) -> Ref<MovieSceneEventRepeaterSection>`
- `add_event_trigger_section(track: Ref<MovieSceneEventTrack>) -> Ref<MovieSceneEventTriggerSection>`
- `add_marked_frame(frame: int, sequence: Ref<LevelSequence>) -> int`
- `add_root_folder(name: str, sequence: Ref<LevelSequence>) -> Ref<MovieSceneFolder>`
- `add_section(track: Ref<MovieSceneTrack>) -> Ref<MovieSceneSection>`
- `add_spawnable_from_class(actor_class_path: str, sequence: Ref<LevelSequence>) -> {MovieSceneBindingProxy}`
- `add_spawnable_from_instance(obj: Ref<Object>, sequence: Ref<LevelSequence>) -> {MovieSceneBindingProxy}`
- `add_track_to_binding(binding: {MovieSceneBindingProxy}, track_type: Ref<Class>) -> Ref<MovieSceneTrack>`
- `add_track_to_folder(folder: Ref<MovieSceneFolder>, track: Ref<MovieSceneTrack>) -> bool`
- `add_track_to_sequence(sequence: Ref<LevelSequence>, track_type: Ref<Class>) -> Ref<MovieSceneTrack>`
- `bake_transform(bindings: [{MovieSceneBindingProxy}]) -> bool`
- `close_sequence() -> bool`
- `copy_bindings(bindings: [{MovieSceneBindingProxy}]) -> str`
- `copy_folders(folders: [Ref<MovieSceneFolder>]) -> str`
- `copy_sections(sections: [Ref<MovieSceneSection>]) -> str`
- `copy_tracks(tracks: [Ref<MovieSceneTrack>]) -> str`
- `create_camera(spawnable?: bool) -> {MovieSceneBindingProxy}`
- `create_level_sequence(asset_name: str, package_path: str) -> Ref<LevelSequence>`
- `delete_all_marked_frames(sequence: Ref<LevelSequence>) -> bool`
- `delete_marked_frame(index: int, sequence: Ref<LevelSequence>) -> bool`
- `empty_selection() -> bool`
- `find_binding_by_name(name: str, sequence: Ref<LevelSequence>) -> {MovieSceneBindingProxy}`
- `find_binding_by_tag(sequence: Ref<LevelSequence>, tag_name: str) -> {MovieSceneObjectBindingID}`
- `find_bindings_by_tag(sequence: Ref<LevelSequence>, tag_name: str) -> [{MovieSceneObjectBindingID}]`
- `find_marked_frame_by_label(label: str, sequence: Ref<LevelSequence>) -> int`
- `find_tracks_by_type(binding: {MovieSceneBindingProxy}, track_type: Ref<Class>) -> [Ref<MovieSceneTrack>]`
- `fix_actor_references() -> bool`
- `focus_parent_sequence() -> bool`
- `focus_sub_sequence(sub_section: Ref<MovieSceneSubSection>) -> bool`
- `force_evaluate() -> bool`
- `get_all_binding_tags(sequence: Ref<LevelSequence>) -> [str]`
- `get_binding_id(binding: {MovieSceneBindingProxy}, sequence: Ref<LevelSequence>) -> {MovieSceneObjectBindingID}`
- `get_binding_name(binding: {MovieSceneBindingProxy}) -> str`
- `get_binding_tags(binding: {MovieSceneBindingProxy}) -> [str]`
- `get_bindings(sequence: Ref<LevelSequence>) -> [{MovieSceneBindingProxy}]`
- `get_bound_objects(binding: {MovieSceneBindingProxy}) -> [Ref<Object>]`
- `get_child_possessables(binding: {MovieSceneBindingProxy}) -> [{MovieSceneBindingProxy}]`
- `get_clock_source(sequence: Ref<LevelSequence>) -> str`
- `get_current_sequence() -> Ref<LevelSequence>`
- `get_display_rate(sequence: Ref<LevelSequence>) -> {FrameRate}`
- `get_evaluation_type(sequence: Ref<LevelSequence>) -> str`
- `get_focused_sequence() -> Ref<LevelSequence>`
- `get_folder_contents(folder: Ref<MovieSceneFolder>) -> str`
- `get_loop_mode() -> bool`
- `get_marked_frames(sequence: Ref<LevelSequence>) -> [{MovieSceneMarkedFrame}]`
- `get_playback_range(sequence: Ref<LevelSequence>) -> str`
- `get_playback_speed() -> float`
- `get_playhead_frame() -> int`
- `get_root_folders(sequence: Ref<LevelSequence>) -> [Ref<MovieSceneFolder>]`
- `get_section_blend_type(section: Ref<MovieSceneSection>) -> str`
- `get_section_completion_mode(section: Ref<MovieSceneSection>) -> str`
- `get_section_ease_in(section: Ref<MovieSceneSection>) -> int`
- `get_section_ease_out(section: Ref<MovieSceneSection>) -> int`
- `get_section_post_roll_frames(section: Ref<MovieSceneSection>) -> int`
- `get_section_pre_roll_frames(section: Ref<MovieSceneSection>) -> int`
- `get_section_properties(section: Ref<MovieSceneSection>) -> str`
- `get_section_range(section: Ref<MovieSceneSection>) -> str`
- `get_section_to_key(track: Ref<MovieSceneTrack>) -> Ref<MovieSceneSection>`
- `get_sections(track: Ref<MovieSceneTrack>) -> [Ref<MovieSceneSection>]`
- `get_selected_bindings() -> [{MovieSceneBindingProxy}]`
- `get_selected_folders() -> [Ref<MovieSceneFolder>]`
- `get_selected_sections() -> [Ref<MovieSceneSection>]`
- `get_selected_tracks() -> [Ref<MovieSceneTrack>]`
- `get_selection_range() -> str`
- `get_sequence_lock_state() -> bool`
- `get_sub_sequence_hierarchy() -> [Ref<MovieSceneSubSection>]`
- `get_tick_resolution(sequence: Ref<LevelSequence>) -> {FrameRate}`
- `get_track_display_name(track: Ref<MovieSceneTrack>) -> str`
- `get_track_filter_names() -> [str]`
- `get_tracks_on_binding(binding: {MovieSceneBindingProxy}) -> [Ref<MovieSceneTrack>]`
- `get_tracks_on_sequence(sequence: Ref<LevelSequence>) -> [Ref<MovieSceneTrack>]`
- `get_view_range(sequence: Ref<LevelSequence>) -> str`
- `get_work_range(sequence: Ref<LevelSequence>) -> str`
- `has_section_end_frame(section: Ref<MovieSceneSection>) -> bool`
- `has_section_start_frame(section: Ref<MovieSceneSection>) -> bool`
- `is_camera_cut_locked() -> bool`
- `is_playback_range_locked(sequence: Ref<LevelSequence>) -> bool`
- `is_playing() -> bool`
- `is_sequence_locked() -> bool`
- `is_track_filter_active(name: str) -> bool`
- `open_sequence(sequence: Ref<LevelSequence>) -> bool`
- `paste_bindings(parent_folder?: Ref<MovieSceneFolder>, paste_token: str, sequence: Ref<LevelSequence>) -> [{MovieSceneBindingProxy}]`
- `paste_folders(parent_folder?: Ref<MovieSceneFolder>, paste_token: str, sequence: Ref<LevelSequence>) -> [Ref<MovieSceneFolder>]`
- `paste_sections(paste_frame?: int, paste_token: str, target_tracks: [Ref<MovieSceneTrack>]) -> [Ref<MovieSceneSection>]`
- `paste_tracks(parent_folder?: Ref<MovieSceneFolder>, paste_token: str, sequence: Ref<LevelSequence>, target_bindings: [{MovieSceneBindingProxy}]) -> [Ref<MovieSceneTrack>]`
- `pause() -> bool`
- `play() -> bool`
- `play_to(frame: int) -> bool`
- `rebind_component(component_bindings: [{MovieSceneBindingProxy}], component_name: str) -> bool`
- `refresh_sequence() -> bool`
- `remove_actors_from_binding(actors: [Ref<Actor>], binding: {MovieSceneBindingProxy}) -> bool`
- `remove_all_bindings(binding: {MovieSceneBindingProxy}) -> bool`
- `remove_binding(binding: {MovieSceneBindingProxy}) -> bool`
- `remove_binding_tag(sequence: Ref<LevelSequence>, tag_name: str) -> bool`
- `remove_invalid_bindings(binding: {MovieSceneBindingProxy}) -> bool`
- `remove_root_folder(folder: Ref<MovieSceneFolder>, sequence: Ref<LevelSequence>) -> bool`
- `remove_section(section: Ref<MovieSceneSection>, track: Ref<MovieSceneTrack>) -> bool`
- `remove_track(binding: {MovieSceneBindingProxy}, track: Ref<MovieSceneTrack>) -> bool`
- `remove_track_from_sequence(sequence: Ref<LevelSequence>, track: Ref<MovieSceneTrack>) -> bool`
- `replace_binding_with_actors(actors: [Ref<Actor>], binding: {MovieSceneBindingProxy}) -> bool`
- `select_bindings(bindings: [{MovieSceneBindingProxy}]) -> bool`
- `select_folders(folders: [Ref<MovieSceneFolder>]) -> bool`
- `select_sections(sections: [Ref<MovieSceneSection>]) -> bool`
- `select_tracks(tracks: [Ref<MovieSceneTrack>]) -> bool`
- `set_binding_name(binding: {MovieSceneBindingProxy}, name: str) -> bool`
- `set_byte_track_enum(enum_class_path: str, track: Ref<MovieSceneByteTrack>) -> bool`
- `set_camera_cut_binding(camera_binding_id: str, section: Ref<MovieSceneCameraCutSection>) -> bool`
- `set_camera_lock(lock: bool) -> bool`
- `set_clock_source(clock_source: str, sequence: Ref<LevelSequence>) -> bool`
- `set_display_rate(denominator?: int, numerator: int, sequence: Ref<LevelSequence>) -> bool`
- `set_evaluation_type(eval_type: str, sequence: Ref<LevelSequence>) -> bool`
- `set_loop_mode(loop: bool) -> bool`
- `set_playback_range(end_frame: int, sequence: Ref<LevelSequence>, start_frame: int) -> bool`
- `set_playback_range_locked(locked: bool, sequence: Ref<LevelSequence>) -> bool`
- `set_playback_speed(speed: float) -> bool`
- `set_playhead_frame(frame: int) -> bool`
- `set_property_name_and_path(display_name: str, property_path: str, track: Ref<MovieScenePropertyTrack>) -> bool`
- `set_section_animation(anim_sequence_path: str, section: Ref<MovieSceneSkeletalAnimationSection>) -> bool`
- `set_section_blend_type(blend_type: str, section: Ref<MovieSceneSection>) -> bool`
- `set_section_completion_mode(completion_mode: str, section: Ref<MovieSceneSection>) -> bool`
- `set_section_ease_in(duration: int, section: Ref<MovieSceneSection>) -> bool`
- `set_section_ease_out(duration: int, section: Ref<MovieSceneSection>) -> bool`
- `set_section_end_bounded(bounded: bool, section: Ref<MovieSceneSection>) -> bool`
- `set_section_post_roll_frames(frames: int, section: Ref<MovieSceneSection>) -> bool`
- `set_section_pre_roll_frames(frames: int, section: Ref<MovieSceneSection>) -> bool`
- `set_section_range(end_frame: int, section: Ref<MovieSceneSection>, start_frame: int) -> bool`
- `set_section_start_bounded(bounded: bool, section: Ref<MovieSceneSection>) -> bool`
- `set_selection_range(end_frame: int, start_frame: int) -> bool`
- `set_sequence_locked(lock: bool) -> bool`
- `set_tick_resolution(denominator?: int, numerator: int, sequence: Ref<LevelSequence>) -> bool`
- `set_track_display_name(name: str, track: Ref<MovieSceneTrack>) -> bool`
- `set_track_filter_active(active: bool, name: str) -> bool`
- `set_view_range(end_seconds: float, sequence: Ref<LevelSequence>, start_seconds: float) -> bool`
- `set_work_range(end_seconds: float, sequence: Ref<LevelSequence>, start_seconds: float) -> bool`
- `tag_binding(binding: {MovieSceneBindingProxy}, tag_name: str) -> bool`
- `untag_binding(binding: {MovieSceneBindingProxy}, tag_name: str) -> bool`

Helper toolsets used by the recipes (same generator, filtered):

- ST `load_level(level_path: str) -> None`
- ST
  `add_to_scene_from_class(actor_type: Ref<Class>, name: str, parent?: Ref<Actor>, snap_to_ground?: bool, xform: {ToolsetTransform}) -> Ref<Actor>`
- ST
  `find_actors(actor_type?: Ref<Class>, bounds?: {Box}, collision_channels: [enum], name: str, root?: Ref<Actor>, tag: str) -> [Ref<Actor>]`
- ACT `get_actor_transform(actor: Ref<Actor>) -> {ToolsetTransform}`
- ACT `set_actor_transform(actor: Ref<Actor>, worldspace?: bool, xform: {ToolsetTransform}) -> bool`
- OT `get_properties(instance: Ref<Object>, properties: [str]) -> str`
- OT `set_properties(instance: Ref<Object>, values: str) -> bool`
- AT `save_assets(asset_paths: [str]) -> bool`
- `ProgrammaticToolset.execute_tool_script(script: str) -> str` (section 9)
- `ProgrammaticToolset.get_execution_environment() -> {ProgrammaticApiExecutionEnvironmentInfo}`

## 6. Recipes (run on 5.8.3)

Each block is the `arguments` object of one call. `<ls>`, `<cam>`, `<b>`, `<track>`, `<sec>` are the
values earlier calls returned, passed back as they came.

### R1. Sequence, rate, range, marker (10 calls)

```
ST  load_level             {"level_path": "/Game/Maps/L_CineReview"}
SEQ create_level_sequence  {"asset_name": "LS_R1", "package_path": "/Game/Cine/Recipes"}          -> <ls>
SEQ set_display_rate       {"sequence": <ls>, "numerator": 24, "denominator": 1}
SEQ set_playback_range     {"sequence": <ls>, "start_frame": 0, "end_frame": 120}
SEQ get_tick_resolution    {"sequence": <ls>}                  -> {"numerator": 24000, "denominator": 1}
SEQ add_marked_frame       {"sequence": <ls>, "frame": 60000}  (display frame 60 = tick 60000)
SEQ get_marked_frames      {"sequence": <ls>}                  -> [{"frameNumber": {"value": 60000}, "label": "A", ...}]
AT  save_assets            {"asset_paths": ["/Game/Cine/Recipes/LS_R1"]}
```

Trap: a marker at `"frame": 60` lands at 0.06 of a frame. Ticks per display frame = tick numerator /
display rate.

### R2. add_actors needs an open sequence (13 calls)

```
ST  add_to_scene_from_class {"actor_type": {"refPath": "/Script/CinematicCamera.CineCameraActor"},
                             "name": "Cam_R2", "xform": {"location": {"x": 0, "y": -1000, "z": 200},
                             "rotation": {"pitch": 0, "yaw": 0, "roll": 0}, "scale": {"x": 1, "y": 1, "z": 1}}}  -> <cam>
SEQ add_actors              {"actors": [<cam>]}          -> []   (ok=true, nothing bound)
SEQ open_sequence           {"sequence": <ls>}           -> true
SEQ add_actors              {"actors": [<cam>]}          -> [<b>]
SEQ get_tracks_on_binding   {"binding": <b>}             -> [MovieScene3DTransformTrack_0]
SEQ get_sections            {"track": <track>}           -> [<sec>]
SEQ has_section_start_frame {"section": <sec>}           -> false (infinite)
KEY get_default_value       {"section": <sec>, "channel_name": "Location.Y"}  -> -1000
```

Traps: the empty list is not an error, so check its length. `get_section_range` on this infinite
section fails ("Section does not have a start frame"); use `has_section_start_frame`.

### R3. The half path, reproduced and fixed (34 calls)

```
SEQ add_track_to_binding {"binding": <b>, "track_type": {"refPath": "/Script/MovieSceneTracks.MovieScene3DTransformTrack"}}  -> <extra>
SEQ add_section          {"track": <extra>}                                         -> <sec2>
SEQ set_section_range    {"section": <sec2>, "start_frame": 0, "end_frame": 120}
KEY add_key_float        {"section": <sec2>, "channel_name": "Location.Y", "frame": 0,   "value": -1000, "interpolation": "linear"}
KEY add_key_float        {"section": <sec2>, "channel_name": "Location.Y", "frame": 119, "value": 1000,  "interpolation": "linear"}
read back at 0, 60, 119  -> y = -1000, -495.8, 0      (broken)
SEQ remove_track         {"binding": <b>, "track": <extra>}
key the first section the same way
read back at 0, 60, 119  -> y = -1000, 8.4, 1000      (fixed)
```

### R4. Straight eased dolly that keeps facing a point (142 calls)

Camera from (0, -1000, 200) to (0, 1000, 200) over frames 0 to 119, facing a target at (800, 0,
100).

```
SEQ open_sequence; SEQ add_actors {"actors": [<cam>]} -> [<b>]
SEQ get_tracks_on_binding {"binding": <b>} -> [<track>];  SEQ get_sections {"track": <track>} -> [<sec>]
KEY add_key_float {"section": <sec>, "channel_name": "Location.X", "frame": 0,   "value": 0,     "interpolation": ""}
KEY add_key_float {"section": <sec>, "channel_name": "Location.X", "frame": 119, "value": 0,     "interpolation": ""}
    ... same for Location.Y (-1000, 1000) and Location.Z (200, 200)
for f in 0, 6, 12, ... 114, 119:
    SEQ set_playhead_frame {"frame": f};  SEQ force_evaluate {}
    ACT get_actor_transform {"actor": <cam>}  -> location L
    yaw = atan2(ty - L.y, tx - L.x); pitch = atan2(tz - L.z, hypot(tx - L.x, ty - L.y))   (degrees)
    KEY add_key_float {"section": <sec>, "channel_name": "Rotation.Z", "frame": f, "value": yaw,   "interpolation": "linear"}
    KEY add_key_float {"section": <sec>, "channel_name": "Rotation.Y", "frame": f, "value": pitch, "interpolation": "linear"}
read back at 0, 15, 33, 60, 87, 110, 119
```

Result: x = 0 and z = 200 at every sample (straight), y = -1000, -912.7, -623.9, 12.6, 643.9, 967.4,
1000 (eased: linear would give -747.9 at frame 15), worst facing error 0.175 degrees, one transform
track on the binding. Two keys with smart auto give flat tangents at both ends, which is the ease in
and out. Rotation channels: `Rotation.X` roll, `Rotation.Y` pitch, `Rotation.Z` yaw. Unwrap yaw
between keys so the curve never spins through 360. Rotation keys every 6 frames kept the error under
0.2 degrees here. The read-back uses a possessable camera; reading a spawnable camera's spawned
actor (`get_bound_objects`) was not tested.

### R5. Camera cut bound to a possessable camera (9 calls)

```
SEQ add_track_to_sequence {"sequence": <ls>, "track_type": {"refPath": "/Script/MovieSceneTracks.MovieSceneCameraCutTrack"}}  -> <cut>
SEQ add_section           {"track": <cut>}  -> <cs>
SEQ set_section_range     {"section": <cs>, "start_frame": 0, "end_frame": 120}
SEQ set_camera_cut_binding {"section": <cs>, "camera_binding_id": "<b.bindingId>"}
    -> fails on 5.8.3: "call() takes at most 0 arguments (1 given)"
OT  set_properties {"instance": <cs>, "values": "{\"CameraBindingID\": {\"guid\": \"<b.bindingId>\", \"sequenceId\": 0, \"resolveParentIndex\": 0}}"}
OT  get_properties {"instance": <cs>, "properties": ["CameraBindingID"]}   -> same guid back
```

`values` is a JSON string, not an object. The failure is inside the tool (it builds a Guid from the
string, which the 5.8.3 Python `Guid` constructor does not accept); the workaround writes the same
field. `get_section_range` on the bounded section returns `{"start": 0, "end": 120}`.

### R6. Spawnable camera and a lens key (16 calls)

```
SEQ open_sequence {"sequence": <ls>}
SEQ create_camera {"spawnable": true}              -> <camb>
SEQ get_child_possessables {"binding": <camb>}     -> [<comp>]
SEQ get_tracks_on_binding {"binding": <comp>}; SEQ get_track_display_name per track
    -> CurrentAperture, CurrentFocalLength, ManualFocusDistance
SEQ get_sections {"track": <focal>} -> [<fs>];  KEY get_channel_names {"section": <fs>} -> ["None"]
KEY add_key_float {"section": <fs>, "channel_name": "None", "frame": 0, "value": 35, "interpolation": "constant"}
KEY get_keys {"section": <fs>, "channel_name": "None"}  -> "[{\"frame\": 0, \"value\": 35.0}]"
SEQ get_tracks_on_sequence {"sequence": <ls>}   -> includes MovieSceneCameraCutTrack_0
```

## 7. Traps (all run on 5.8.3)

- `add_actors` and `create_camera` act on the sequence open in Sequencer: `open_sequence` first, and
  after switching sequences.
- One transform track per binding. Never `add_track_to_binding` a second transform track or
  `add_section` on the auto one; key the section `add_actors` made. Check with
  `get_tracks_on_binding` before saving.
- Read back what plays (`set_playhead_frame`, `force_evaluate`, `get_actor_transform`) at 5 or more
  frames, including both ends and the middle. Keys can be right while the evaluated path is wrong.
- Keys and section ranges take display frames; markers take ticks.
- `add_section` returns a 0 to 0 section: set its range before keying.
- `get_playback_range`, `get_section_range` and `get_keys` return JSON text. Parse it.
- `set_camera_cut_binding` fails: write `CameraBindingID` with `ObjectTools.set_properties`.
- `create_camera` adds a camera cut section for its camera; bind further cuts yourself.
- Float property tracks (focal length, aperture, focus distance) have one channel named `None`.

## 8. Rendering and when to use Python

No MCP toolset renders or edits a Movie Render Graph on 5.8.3. Use the Python layer in
`scripts/ue_cine.py`:

| Need                                                                           | Python (run on 5.8.3)                                                                                                                                                                              |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A whole cut from a plan (master, shots, spawnable cameras, cuts, keys, `_LGT`) | `build_from_plan` in a headless job (`job_10_build_trailer.py`): `audit_sequence` verdict pass                                                                                                     |
| A template render graph                                                        | `create_render_graph(path, w, h, output_dir, formats)` (`job_25_author_graph.py`), then `audit_render_settings(normalize_graph_snapshot(graph_snapshot(g)))`                                       |
| Boards (stills per shot)                                                       | `board_generator` in a latent offscreen job (`job_20_board_latent.py`): 21 frames at 1280x536                                                                                                      |
| A render                                                                       | `render_generator` in a latent offscreen job (`job_30_render_latent.py`): one shot rendered in about 32 s, end frame exclusive, EXR half PIZ and PNG, output folder and file name format respected |

Python is also the better channel for loops over many shots, any check that needs the asset on disk,
and spawnable bindings in a headless job. `ue_cine.add_spawnable` calls
`MovieSceneSequence.add_spawnable_from_class`, deprecated in the 5.8 Python reference, because the
`LevelSequenceEditorSubsystem` versions it points to return an empty binding in a commandlet. Over
MCP, `ProgrammaticToolset.execute_tool_script` batches many toolset calls in one turn (section 9).
Compare binding ids in Python with `guid.to_string()`: on 5.8.3 two `Guid` objects for the same id
are not `==`.

## 9. Batched recipes: one `execute_tool_script` call each

Four or more toolset calls in a row go through one
`editor_toolset.toolsets.programmatic.ProgrammaticToolset.execute_tool_script {"script": "<text>"}`
call. Call `ProgrammaticToolset.get_execution_environment` once per session, before the first
script. The script defines `run()`, calls `execute_tool("<toolset>.<tool>", json_string)` (full
dotted name; it returns a dict with `returnValue` and raises `RuntimeError` when a call fails) and
returns a dict, which comes back as JSON text in `returnValue`. Imports are limited to json, math,
re, time, datetime, copy. Inside a script the same order holds: `open_sequence` before `add_actors`.
A failed call ends the whole script (it raises `RuntimeError` with the tool's message and the script
line), so guard calls that can refuse: `load_level` refuses while the open level has unsaved
changes, hence the `get_current_level` check in B1 and B4. The scripts below are the recipes of
section 6 on their own assets; each ran live as written (`live_mcp_recipes.py` extracts and runs
every block that starts with `# script:`). B5 edits the sequence B4 made. Paths are the test
project's: change them for yours.

```python
# script: B1  (R1) sequence at 24 fps, 120 frames, a marker at display frame 60
import json
SEQ = "animation_toolset.toolsets.sequencer.SequencerTools."

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def run():
    if "L_CineReview" not in t("editor_toolset.toolsets.scene.SceneTools.get_current_level", {}):
        t("editor_toolset.toolsets.scene.SceneTools.load_level", {"level_path": "/Game/Maps/L_CineReview"})
    ls = t(SEQ + "create_level_sequence", {"asset_name": "LS_B1", "package_path": "/Game/Cine/Batch"})
    t(SEQ + "set_display_rate", {"sequence": ls, "numerator": 24, "denominator": 1})
    t(SEQ + "set_playback_range", {"sequence": ls, "start_frame": 0, "end_frame": 120})
    tick = t(SEQ + "get_tick_resolution", {"sequence": ls})
    per_frame = tick["numerator"] // tick["denominator"] // 24
    t(SEQ + "add_marked_frame", {"sequence": ls, "frame": 60 * per_frame})      # ticks, not frames
    marks = t(SEQ + "get_marked_frames", {"sequence": ls})
    t("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": ["/Game/Cine/Batch/LS_B1"]})
    return {"ok": marks[0]["frameNumber"]["value"] == 60 * per_frame, "ticks_per_frame": per_frame,
            "range": json.loads(t(SEQ + "get_playback_range", {"sequence": ls}))}
```

```python
# script: B3  (R2 + R3) add_actors before and after open_sequence; a second transform track halves the path
import json
SEQ = "animation_toolset.toolsets.sequencer.SequencerTools."
KEY = "animation_toolset.toolsets.keyframing.SequencerKeyframingTools."
TRANSFORM = {"refPath": "/Script/MovieSceneTracks.MovieScene3DTransformTrack"}

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def ys(cam, frames):
    out = []
    for f in frames:
        t(SEQ + "set_playhead_frame", {"frame": f})
        t(SEQ + "force_evaluate", {})
        out.append(round(t("editor_toolset.toolsets.actor.ActorTools.get_actor_transform",
                           {"actor": cam})["location"]["y"], 1))
    return out

def key_y(sec):
    for f, y in ((0, -1000.0), (119, 1000.0)):
        t(KEY + "add_key_float", {"section": sec, "channel_name": "Location.Y", "frame": f, "value": y,
                                  "interpolation": "linear"})

def run():
    ls = t(SEQ + "create_level_sequence", {"asset_name": "LS_B3", "package_path": "/Game/Cine/Batch"})
    t(SEQ + "set_display_rate", {"sequence": ls, "numerator": 24, "denominator": 1})
    t(SEQ + "set_playback_range", {"sequence": ls, "start_frame": 0, "end_frame": 120})
    cam = t("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_class", {
        "actor_type": {"refPath": "/Script/CinematicCamera.CineCameraActor"}, "name": "Cam_B3",
        "xform": {"location": {"x": 0, "y": -1000, "z": 200}, "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
                  "scale": {"x": 1, "y": 1, "z": 1}}})
    t(SEQ + "close_sequence", {})
    before = t(SEQ + "add_actors", {"actors": [cam]})                  # [] : nothing open
    t(SEQ + "open_sequence", {"sequence": ls})
    b = t(SEQ + "add_actors", {"actors": [cam]})[0]
    extra = t(SEQ + "add_track_to_binding", {"binding": b, "track_type": TRANSFORM})
    sec = t(SEQ + "add_section", {"track": extra})
    t(SEQ + "set_section_range", {"section": sec, "start_frame": 0, "end_frame": 120})
    key_y(sec)
    broken = ys(cam, [0, 60, 119])
    t(SEQ + "remove_track", {"binding": b, "track": extra})
    first = t(SEQ + "get_sections", {"track": t(SEQ + "get_tracks_on_binding", {"binding": b})[0]})[0]
    key_y(first)
    fixed = ys(cam, [0, 60, 119])
    return {"ok": before == [] and abs(broken[-1]) < 5 and abs(fixed[-1] - 1000) < 1,
            "before_open": before, "two_tracks": broken, "one_track": fixed}
```

```python
# script: B4  (R4) straight eased dolly that keeps facing a point, read back at 7 frames
import json, math
SEQ = "animation_toolset.toolsets.sequencer.SequencerTools."
KEY = "animation_toolset.toolsets.keyframing.SequencerKeyframingTools."
TARGET = (800.0, 0.0, 100.0)
START, END, LAST = (0.0, -1000.0, 200.0), (0.0, 1000.0, 200.0), 119

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def key(sec, ch, f, v, interp):
    t(KEY + "add_key_float", {"section": sec, "channel_name": ch, "frame": f, "value": v,
                              "interpolation": interp})

def evaluated(cam, f):
    t(SEQ + "set_playhead_frame", {"frame": f})
    t(SEQ + "force_evaluate", {})
    return t("editor_toolset.toolsets.actor.ActorTools.get_actor_transform", {"actor": cam})

def aim(L):
    dx, dy, dz = TARGET[0] - L["x"], TARGET[1] - L["y"], TARGET[2] - L["z"]
    return math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx))

def run():
    if "L_CineReview" not in t("editor_toolset.toolsets.scene.SceneTools.get_current_level", {}):
        t("editor_toolset.toolsets.scene.SceneTools.load_level", {"level_path": "/Game/Maps/L_CineReview"})
    ls = t(SEQ + "create_level_sequence", {"asset_name": "LS_B4", "package_path": "/Game/Cine/Batch"})
    t(SEQ + "set_display_rate", {"sequence": ls, "numerator": 24, "denominator": 1})
    t(SEQ + "set_playback_range", {"sequence": ls, "start_frame": 0, "end_frame": LAST + 1})
    cam = t("editor_toolset.toolsets.scene.SceneTools.add_to_scene_from_class", {
        "actor_type": {"refPath": "/Script/CinematicCamera.CineCameraActor"}, "name": "Cam_B4",
        "xform": {"location": dict(zip("xyz", START)), "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
                  "scale": {"x": 1, "y": 1, "z": 1}}})
    t(SEQ + "open_sequence", {"sequence": ls})                         # before add_actors
    b = t(SEQ + "add_actors", {"actors": [cam]})[0]
    sec = t(SEQ + "get_sections", {"track": t(SEQ + "get_tracks_on_binding", {"binding": b})[0]})[0]
    for i, ch in enumerate(("Location.X", "Location.Y", "Location.Z")):
        key(sec, ch, 0, START[i], "")                                  # "" = smart auto: eased
        key(sec, ch, LAST, END[i], "")
    prev = None
    for f in list(range(0, LAST, 6)) + [LAST]:
        pitch, yaw = aim(evaluated(cam, f)["location"])
        if prev is not None:
            yaw += 360.0 * round((prev - yaw) / 360.0)
        prev = yaw
        key(sec, "Rotation.Z", f, yaw, "linear")
        key(sec, "Rotation.Y", f, pitch, "linear")
    rows, worst = [], 0.0
    for f in (0, 15, 33, 60, 87, 110, LAST):
        x = evaluated(cam, f)
        L, R = x["location"], x["rotation"]
        pitch, yaw = aim(L)
        err = max(abs((R["yaw"] - yaw + 180.0) % 360.0 - 180.0), abs(R["pitch"] - pitch))
        worst = max(worst, err)
        rows.append([f, round(L["x"], 1), round(L["y"], 1), round(L["z"], 1), round(err, 3)])
    tracks = len(t(SEQ + "get_tracks_on_binding", {"binding": b}))
    t("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": ["/Game/Cine/Batch/LS_B4"]})
    linear_15 = START[1] + (END[1] - START[1]) * 15 / LAST
    ok = (tracks == 1 and worst < 1.0 and rows[1][2] < linear_15 - 50
          and all(abs(r[1]) < 0.5 and abs(r[3] - 200) < 0.5 for r in rows))
    return {"ok": ok, "frame_x_y_z_err": rows, "worst_deg": round(worst, 3), "transform_tracks": tracks}
```

```python
# script: B5  (R5) camera cut bound to the B4 camera (set_camera_cut_binding fails on 5.8.3)
import json
SEQ = "animation_toolset.toolsets.sequencer.SequencerTools."
OT = "editor_toolset.toolsets.object.ObjectTools."

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def run():
    ls = {"refPath": "/Game/Cine/Batch/LS_B4.LS_B4"}
    t(SEQ + "open_sequence", {"sequence": ls})
    b = t(SEQ + "get_bindings", {"sequence": ls})[0]
    cut = t(SEQ + "add_track_to_sequence", {"sequence": ls,
        "track_type": {"refPath": "/Script/MovieSceneTracks.MovieSceneCameraCutTrack"}})
    sec = t(SEQ + "add_section", {"track": cut})
    t(SEQ + "set_section_range", {"section": sec, "start_frame": 0, "end_frame": 120})
    t(OT + "set_properties", {"instance": sec, "values": json.dumps({"CameraBindingID": {
        "guid": b["bindingId"], "sequenceId": 0, "resolveParentIndex": 0}})})
    got = json.loads(t(OT + "get_properties", {"instance": sec, "properties": ["CameraBindingID"]}))
    t("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": ["/Game/Cine/Batch/LS_B4"]})
    same = got["CameraBindingID"]["guid"].replace("-", "").upper() == b["bindingId"].replace("-", "").upper()
    return {"ok": same, "cut": got["CameraBindingID"]}
```

```python
# script: B6  (R6) spawnable camera from create_camera, focal length keyed
import json
SEQ = "animation_toolset.toolsets.sequencer.SequencerTools."
KEY = "animation_toolset.toolsets.keyframing.SequencerKeyframingTools."

def t(tool, args):
    r = execute_tool(tool, json.dumps(args))
    return r["returnValue"] if "returnValue" in r else None

def run():
    ls = t(SEQ + "create_level_sequence", {"asset_name": "LS_B6", "package_path": "/Game/Cine/Batch"})
    t(SEQ + "open_sequence", {"sequence": ls})
    cam = t(SEQ + "create_camera", {"spawnable": True})
    comp = t(SEQ + "get_child_possessables", {"binding": cam})[0]
    focal = [tr for tr in t(SEQ + "get_tracks_on_binding", {"binding": comp})
             if "Focal" in t(SEQ + "get_track_display_name", {"track": tr})][0]
    sec = t(SEQ + "get_sections", {"track": focal})[0]
    ch = t(KEY + "get_channel_names", {"section": sec})[0]               # "None"
    t(KEY + "add_key_float", {"section": sec, "channel_name": ch, "frame": 0, "value": 35.0,
                              "interpolation": "constant"})
    keys = json.loads(t(KEY + "get_keys", {"section": sec, "channel_name": ch}))
    t("editor_toolset.toolsets.asset.AssetTools.save_assets", {"asset_paths": ["/Game/Cine/Batch/LS_B6"]})
    return {"ok": abs(keys[0]["value"] - 35.0) < 1e-4, "channel": ch, "keys": keys}
```

## 10. Epic's in-editor skills

No Sequencer, camera or Movie Render skill ships with 5.8.3: the skills registered under the
engine's `Plugins/Experimental/Toolsets` cover materials, Blueprints, default outdoor lighting,
general best practices, Niagara, PCG and Dataflow (read them through
`ToolsetRegistry.AgentSkillToolset`: `ListSkills`, then `GetSkills`). Nothing to reconcile for this
skill; the lit level comes from `scenario-unreal-lighting-rendering`, which covers the outdoor
lighting one. The animation toolset ships its own Python tests next to the toolsets
(`animation_toolset/tests/test_sequencer_*.py` in the AnimationAssistantToolset plugin); they open
the sequence before binding, the same order as section 3.
