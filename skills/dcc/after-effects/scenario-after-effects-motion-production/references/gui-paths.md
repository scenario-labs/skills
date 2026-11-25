# GUI paths

Menus, panels and shortcuts for the same procedures, for a person or a computer-use agent. After
Effects 27.0 on macOS (Cmd); on Windows use Ctrl.

## Beat sheet into the timeline

| Step                                                 | GUI path                                                                                                           |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Comp marker (no layer selected)                      | Layer > Markers > Add Marker, or Shift+8 on the numeric keypad, or the marker button at the right of the timeline  |
| Layer marker on the music layer, live while it plays | select the layer, press * on the numeric keypad during RAM preview (one marker per tap)                            |
| Marker duration, comment, protected region           | double-click the marker: Composition Marker dialog, Duration, Comment, Responsive Design - Time > Protected Region |
| Set a layer's in and out point at the current time   | Option+[ and Option+]                                                                                              |
| Split a layer at the current time                    | Edit > Split Layer (Cmd+Shift+D)                                                                                   |
| Snap to markers while dragging                       | hold Shift while dragging a layer or the current-time indicator                                                    |
| Go to next or previous marker                        | J and K move between keyframes, markers and in or out points of selected layers                                    |

## Audio

| Step                     | GUI path                                                                                                                         |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Levels in dB             | twirl the layer: Audio > Audio Levels (L twice shows it); or Effect > Audio > Stereo Mixer for a keyable mix                     |
| Mute captured game audio | Audio switch (speaker icon) in the A/V Features column                                                                           |
| Waveform                 | twirl Audio > Waveform (LL)                                                                                                      |
| Amplitude to keys        | Animation > Keyframe Assistant > Convert Audio to Keyframes (creates "Audio Amplitude" with Left, Right, Both Channels)          |
| Preview with audio       | Spacebar or numeric 0, with audio enabled in the Preview panel                                                                   |
| Peak levels              | Window > Audio: level meters in dB during preview (peak only, no loudness reading)                                               |
| Loudness (LUFS)          | not in After Effects: render the mix and read it with `ffmpeg -af ebur128=peak=true`, or Premiere Pro Loudness Radar or Audition |

## Safe zones and guides

| Step                       | GUI path                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------ |
| Show title and action safe | Toggle Grid and Guide Options button under the viewer > Title/Action Safe (apostrophe key) |
| Custom safe margins        | Settings > Grids & Guides > Safe Margins (percent of frame)                                |
| Platform overlay           | import the platform's safe-zone PNG, put it on top, Layer > Guide Layer, lower opacity     |
| Guide layer                | Layer > Guide Layer: visible in the viewer, not rendered, not seen through nesting         |

## Variants and templates

| Step                                   | GUI path                                                                                                                                                            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Expose a property                      | Window > Essential Graphics, set Primary comp, drag the property from the timeline into the panel; or right-click the property > Add Property to Essential Graphics |
| Expose a footage layer for replacement | drag the layer into the Essential Graphics panel (media replacement)                                                                                                |
| Override per instance                  | twirl the nested layer: Essential Properties; right-click an override > Reset                                                                                       |
| Replace media on an instance           | Essential Properties > the media controller > Alt/Option-drag footage from the Project panel onto it                                                                |
| Export a template                      | Essential Graphics > Export Motion Graphics Template (save the project first)                                                                                       |
| Duplicate a comp                       | Edit > Duplicate (Cmd+D) on the comp in the Project panel; nested precomps are shared, not copied                                                                   |

## Responsive time

| Step                          | GUI path                                                                                                          |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Protected intro or outro      | Composition > Responsive Design - Time > Create Intro, Create Outro (15 % of the duration each)                   |
| From the work area            | Composition > Responsive Design - Time > Create Protected Region from Work Area                                   |
| After editing the source comp | select the nested layer > Layer > Markers > Update Markers from Source                                            |
| Stretch the nested comp       | drag the layer's out point in the timeline (it stretches instead of trimming when the comp has protected regions) |

## Render and review

| Step                  | GUI path                                                                                         |
| --------------------- | ------------------------------------------------------------------------------------------------ |
| Add to the queue      | Composition > Add to Render Queue (Cmd+M)                                                        |
| Output module         | Render Queue > Output Module: H.264 - Match Render Settings - 15 Mbps, or AIFF 48kHz for the mix |
| Render part of a comp | set the work area (B and N), Render Settings > Time Span: Work Area Only                         |
| Save one frame        | Composition > Save Frame As > File (Cmd+Option+S)                                                |
| Muted pass            | Preview panel: switch the audio button off, play at full frame rate                              |
| Review comments       | outside After Effects: a review link with timestamped comments on the H.264 draft                |
