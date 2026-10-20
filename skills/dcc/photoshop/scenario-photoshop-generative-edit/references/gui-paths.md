# GUI paths (for the user or a computer-use agent)

Steps no script reaches: hand-drawn selections and Photoshop's own generative tools (Adobe documents
no script call; a forum reports an undocumented batchPlay descriptor, not tested; Adobe's generative
AI guidelines may cover automated use). None of these paths was run in testing; they come from the
expert videos and Adobe's help pages, on Photoshop 2026 (27.x). Menu names can move between
releases. Shortcuts are macOS first, Windows second.

## Selections

- **Selection Brush tool** (Toolbar): paint over the area, or loop around it and release where you
  started to fill the loop. Options bar: Size, Hardness, Opacity, Add or Subtract. Hold Option or
  Alt to subtract, for hair that must stay in front [pgBjkr2X6wI 11:04].
- **Object Selection tool** (Toolbar): hover until the object highlights, then click [7zE6s7_nmIs
  11:25].
- **Select Subject:** Select > Subject, or Select subject in the Contextual Task Bar. The script
  route is `autoCutout` (procedures P1).
- **Grow a selection a few pixels:** press Q for Quick Mask, then Filter > Other > Maximum (Minimum
  to shrink); press Q again [MvxUcebxhRc 05:13]. Select > Modify > Expand does the same without a
  preview.
- **Selection from a channel:** Command-click or Control-click the channel's thumbnail in the
  Channels panel. A gray channel loads as a partial selection, with a warning that no pixels are
  more than 50% selected [0h8lwK-shOY 01:34].
- **Contextual Task Bar missing:** Window > Contextual Task Bar [S-03awqbtqs 02:10].

## Generative Fill (Photoshop's own route)

1. Make a selection, then Generative Fill in the Contextual Task Bar, or Edit > Generative Fill for
   a larger prompt box.
2. Pick the model with the model picker icon [1bFcFVbbzjc 00:32].
3. Type a prompt, or leave it empty to fill from the surroundings, then Generate.
4. Cycle variations with the arrows in the Task Bar or in the Properties panel; Generate again for
   more [Ot_h4s1mXas 02:11].
5. The result is a generative layer with a mask. Paint black on the mask to hide parts [1bFcFVbbzjc
   01:38].
6. For a new edit, make a new selection first. Generating again on the same generative layer
   replaces it [f-7wkNmAtDk 02:05].

## Reference Image in Generative Fill

1. Select where the object goes, at the size it should be.
2. Generative Fill > Reference image > Choose image [7zE6s7_nmIs 12:29].
3. Reference type: Object or Whole image. Intent: Swap the selected area or Place into the selected
   area. With an object reference there is no prompt field [7zE6s7_nmIs 03:14].
4. Pre-cut the reference image to the one object first [7zE6s7_nmIs 11:25].

## Generative Expand and a plain canvas extension

- **Generative Expand:** Crop tool (C), drag a handle past the canvas, then Generative Expand in the
  Task Bar [fR0CI04XBpM 09:16].
- **Extend without generating:** Crop tool with Fill set to Transparent in the Options bar, then
  fill the empty area separately [CyJgXBJVHkU 01:03].
- **Background layer:** unlock it first so the new canvas is transparent, not white [S-03awqbtqs
  08:09].

## Remove tool and Content-Aware Fill

- **Remove tool** (Toolbar): brush or loop over the object. Options: Sample All Layers (the result
  lands on the active layer), Remove after each stroke, Add and Subtract. Find Distractions in the
  Options bar offers Wires and cables, People, and General distractions, with a review before the
  checkmark. It spends no generative credits [nmvewzc6MG4 00:13].
- **Remove on a selection:** select, then Remove in the Contextual Task Bar.
- **Content-Aware Fill:** right-click a selection > Content-Aware Fill. Set the Sampling Area, Color
  Adaptation, and Output To New Layer. It samples existing pixels rather than generating.

## Rotate Object

1. Duplicate the layer first: the conversion replaces the pixel layer [-T5RVvMLUTs 01:05].
2. Command-T or Control-T, then Rotate Object in the Task Bar [-T5RVvMLUTs 00:32].
3. Drag the bottom-center control to turn the object, the tilt and perspective controls to match the
   scene, then commit.
4. For a person over a kept background, make a clean plate first: select the person, Remove, then
   duplicate the original layer above it and rotate that [-T5RVvMLUTs 05:23].

## Prompt to edit and Markup

- **Prompt to edit:** with no selection or with Select All, Prompt to edit in the Contextual Task
  Bar, or Edit > Prompt to edit. It edits the whole image from an instruction.
- **Markup** (27.10): arrows, circles, color picks and notes drawn on the image as instructions for
  Prompt to edit. It creates a temporary markup layer.

## Finishing by hand

- **Grain:** Adjustments panel > Grain. Amount, size and roughness; Darken or Lighten blend mode to
  keep only dark or light grain; lower opacity to taste [mGV_jkmPjcY 02:35, 03:08, 03:42].
- **Compare:** toggle the eye icon of the generated layer [Ot_h4s1mXas 03:17].
- **Organize:** name each generated layer, select them, Command-G or Control-G to group, and name
  the group [Ot_h4s1mXas 04:51].
