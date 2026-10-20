# GUI paths (for the user or a computer-use agent)

Steps no script reaches: hand refinement of masks, Photoshop's own generative tools, and brush work
on the masks the toolkit leaves black. For the generative tools, Adobe documents no script call; a
forum reports an undocumented batchPlay descriptor, not tested; Adobe's generative AI guidelines may
cover automated use. None of these paths was run in testing; they come from the expert videos and
Adobe's help pages, on Photoshop 2026 (27.x). Menu names can move between releases. Shortcuts are
macOS first, Windows second.

## Cutouts

- **Select Subject, more accurate:** set the Select Subject mode to Cloud in the options bar, then
  click Select Subject with the layer targeted, then add a layer mask [2Z0CFC7rg8U 00:33]. The
  script route is `C.subject_mask` (procedures P2).
- **Select and Mask for hair:**
  1. Select > Select and Mask. View mode On Black at 100% opacity shows fringing best [2Z0CFC7rg8U
     01:39].
  2. Try Refine Hair in the options bar; undo if it adds odd edges [2Z0CFC7rg8U 02:13].
  3. Refine Edge Brush tool over the hair. Object Aware mode for hair or fur; Color Aware when hair
     and background differ strongly in color [2Z0CFC7rg8U 02:46].
  4. Global Refinements: Smooth, then Shift Edge negative to pull in a halo; Feather stays at 0 on a
     sharp subject [\_PNUQDm6lrA 04:27, 05:00].
  5. Output To: Layer Mask, then OK [2Z0CFC7rg8U 03:18].
- **Hair fringe without thinning the hair** [2Z0CFC7rg8U 03:50, 04:24, 04:56, 05:29]:
  1. Add a Solid Color fill layer and clip it to the subject.
  2. Option-drag or Alt-drag the subject's mask onto it, then invert that mask (Command-I or
     Control-I).
  3. Sample the hair color in the fill's color picker.
- **Enhance Edge (27.11):** target a layer mask, then Enhance Edge. It makes a new layer that
  carries inside colors outward and leaves the mask unchanged [p36McKBhQe8 05:11]. It spends
  generative credits on every run, kept or not [p36McKBhQe8 03:37]; Adobe lists 20 per generation.
- **Too hard to select:** hide the problem area in the mask and paint the detail in instead, such as
  hair with a hair brush [\_PNUQDm6lrA 09:20].
- **Edge softness to match the plate:** Blur tool on the mask where the plate's edges are soft
  [\_PNUQDm6lrA 11:34].
- **Blend If by hand:** double-click the layer, Blend If channel menu, drag the This Layer or
  Underlying Layer slider; Option-click or Alt-click a slider to split it [Wkti_IX3Qzk 02:44].

## Light

- **Harmonize:**
  1. Target the pasted pixel layer (a smart object is not tested). Contextual Task Bar > Harmonize;
     if the bar is hidden, Window > Contextual Task Bar [JGbvUOytwX0 01:36].
  2. Pick one of three variations in the Properties panel [dWiOA5YZXwc 02:09]. Each generation costs
     5 generative credits (Adobe's credits page).
  3. Duplicate the result, set the copy to Luminosity, lower the other's opacity partway
     [C2lo7ew8lHY 06:33, 07:06].
  4. Paint black on the result's mask where the original must show (faces, logos, glass). Harmonize
     does not keep transparency in glass [dWiOA5YZXwc 02:09].
- **Leave the plate's own shadows** in place before Harmonize: they help it read the light
  [2jMaaUSp0dM 03:45].
- **Relight Layer (beta, September 2026):** Layer > New Relight Layer. Drag the light dot to set the
  direction; the Close slider moves it behind for backlight; turn ambient light down to see the
  added light; set the color in Kelvin or a custom color [P0OsXyEeuvM 00:00, 01:12, 01:45, 02:20].
  Up to 3 lights [P0OsXyEeuvM 02:58]. Credits are spent on Done [P0OsXyEeuvM 04:05].
- **Light adjustment layer (27.10):** add it above the layers it should affect, last in the stack.
  It pauses while the layers below it are edited [m6nSl2-t-iQ 07:19].

## Shadows

- **Cast shadow by hand:** Command-click or Control-click the subject's thumbnail, new Solid Color
  layer in the shadow color, Multiply, then Command-T or Control-T to lay it on the ground
  [BrMuLGNoPhs 31:00].
- **Contact shadow by hand:** soft round brush at low flow on a dark Multiply layer, densest at each
  contact point [INmkd2ztW4c 35:10].
- **Fade the cast with distance:** gradient or soft brush in black on the cast layer's mask, away
  from the contact.
- **Shadow from a selection:** Selection Brush over the shadow area, then a Curves adjustment layer
  dragged down; feather the mask in Properties when the edge is too sharp [bMXJwZuzP14 08:20].

## Grain

- **Grain adjustment layer (27.3):** put the generated layers in a group, add the Grain adjustment
  layer above it and click the clipping icon in Properties; Amount sets contrast, Size the grain
  size [YaTBt6nLOd0 03:50, 04:24]. Judge at 100% and 200% [YaTBt6nLOd0 03:17].

## Skin

- **Camera Raw blemishes:** convert the layer to a smart object, Filter > Camera Raw Filter, Remove
  tool, Blemishes, Apply [eOo99mWh15E 00:00]. Refine restores or removes by brush [eOo99mWh15E
  00:31]. Amount sets how many blemishes go; Fade keeps moles and freckles partly visible
  [eOo99mWh15E 01:02, 01:35]. It spends no generative credits [sjX06wve7tw 01:04].
- **Paint the smoother's mask:** soft brush, Hardness 0%, white, over skin only; lower the opacity
  for finesse [qUUyJ6VwQZM 02:13, 02:44]. Keep it off eyes, teeth and hair [3eURUBIrhRY 09:59].
- **Paint the Dodge and Burn masks:** white on each Curves layer's black mask; Dodge lifts, Burn
  lowers [5TaYvLfk2QQ 06:15].
- **Paint the frequency separation tone layer:** Brush tool, Option-click or Alt-click to sample a
  skin color nearby, flow 25% (Shift with 2 then 5), build up; set the retouch layer to Lighten for
  dark circles [REt264jFvqE 07:07, 07:42, 08:16].
- **Restore original eyes after a generative pass:** soft brush on the mask of the original's copy
  over the eyes [3eURUBIrhRY 05:28].
- **Skin line in Camera Raw:** right-click the Vectorscope and choose Show Skin Tone Indicator
  [oZAC8R6zL8A 01:44]; Point Color with the eyedropper on skin, then Hue toward the line
  [oZAC8R6zL8A 03:23].
- **Vibrance, not Saturation, on people:** the Color and Vibrance adjustment layer, Vibrance up and
  Saturation left alone [H7HqYscQdpQ 06:28].
