# GUI paths (After Effects 27.0)

The same procedures for a person or a computer-use agent. Script equivalents are in procedures.md.

## Text layers

| Task                          | GUI path                                                                           | Script equivalent                                            |
| ----------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| New point text                | Layer > New > Text, click once in the Composition panel                            | `comp.layers.addText(string)`                                |
| New paragraph (box) text      | Type tool, drag a box in the Composition panel                                     | `comp.layers.addBoxText([w, h], string)`                     |
| Font, size, tracking, leading | Window > Character, or Properties panel > Text                                     | `TextDocument.font`, `fontSize`, `tracking`, `leading`       |
| Style one word                | Double-click the layer, select the word, change it in Character                    | `textDocument.characterRange(start, end)` (24.3+)            |
| Resolve missing fonts         | File > Dependencies > Resolve Fonts (opens at project open when fonts are missing) | `app.fonts.missingOrSubstitutedFonts`, `AEK.text.fontExists` |
| Variable font axis values     | Properties panel > Text > Variable Font icon (values only, no stopwatch)           | animator with `addVariableFontAxis(tag)`                     |

## Animators and selectors

| Task                                       | GUI path                                                                                                                                     |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Add an animator                            | Animation > Animate Text > (property); or the Animate menu next to Text in the Timeline; or Properties panel > Text Animation > Add Animator |
| Add a property to an existing animator     | Animator group > Add > Property > (property)                                                                                                 |
| Add a selector                             | Animator group > Add > Selector > Range, Wiggly, or Expression                                                                               |
| Shape, Ease High, Ease Low, Based On, Mode | Range Selector > Advanced (twirl open)                                                                                                       |
| Anchor Point Grouping, Grouping Alignment  | Text > More Options                                                                                                                          |
| Variable font axis animator                | Animate menu > Variable Font Axes > (axis), or right-click selected text > Animate Text > Variable Font Axes                                 |
| Per-character 3D                           | Animation > Animate Text > Enable Per-character 3D, or the Animate menu > Enable Per-character 3D                                            |
| Back to 2D (loses per-character 3D values) | Click the per-character 3D switch in the Switches column                                                                                     |
| Set Offset by dragging                     | Select the selector, drag the selector bars in the Composition panel; Shift-drag the bars to set Offset                                      |
| Random order that holds across duplicates  | Range Selector > Advanced > Randomize Order On, Random Seed non-zero                                                                         |
| Pause inside a reveal                      | Select the selector Offset keys (U), add a middle key at 50 %, Graph Editor: drag its handle flat                                            |
| Save an animation preset                   | Select the animator groups AND any changed More Options property, never Source Text, then Animation > Save Animation Preset                  |
| Apply a preset                             | Effects & Presets panel, or Animation > Apply Animation Preset                                                                               |
| Text on a path                             | Draw a mask on the text layer, Text > Path Options > Path > (mask); animate First Margin                                                     |

## Timing to audio

| Task                       | GUI path                                                                                                    | Script equivalent                                                                                                                 |
| -------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| See the waveform           | Select the audio layer, press LL                                                                            | none needed: use word timings                                                                                                     |
| Layer markers              | Layer > Markers > Add Marker (numpad *)                                                                     | `layer.property("ADBE Marker").setValueAtTime(t, new MarkerValue(word))`                                                          |
| Convert audio to keyframes | Select the audio layer, Animation > Keyframe Assistant > Convert Audio to Keyframes                         | `app.executeCommand(app.findMenuCommandId("Convert Audio to Keyframes"))` with the layer selected and the comp open in the viewer |
| Captions from speech       | Premiere Pro: Text panel > Captions > Create Captions from Transcript (After Effects has no speech-to-text) | a speech-to-text run with word timestamps, then `scripts/word_timings.py`                                                         |

## Templates

| Task                | GUI path                                                               |
| ------------------- | ---------------------------------------------------------------------- |
| Expose Source Text  | Window > Essential Graphics, drag Source Text into the panel           |
| Export a .mogrt     | Essential Graphics > Export Motion Graphics Template                   |
| Center for retyping | Paragraph panel > Center Text, then Align panel > Align to Composition |

## Checking

| Task                         | GUI path                                                              |
| ---------------------------- | --------------------------------------------------------------------- |
| Title and action safe guides | Composition panel > Choose grid and guide options > Title/Action Safe |
| Read a preset's changes      | Select the layer, press U (keys) or UU (changed properties)           |
| Motion blur on text          | Layer switch Motion Blur plus the comp Enable Motion Blur button      |
