# GUI paths for what scripts cannot reach (After Effects 27.0, macOS shortcuts; Windows: Cmd = Ctrl, Opt = Alt)

## Project color

- File > Project Settings > Color: Color Engine (Adobe color managed or OCIO color managed), Working
  Color Space, Bit Depth, Linearize Working Space, Blend Colors Using 1.0 Gamma, Compensate for
  Scene-referred Profiles.
- OCIO: Project Settings > Color > OCIO Config (ACES 2.0 CG v4.0, ACES 2.0 Studio v4.0, or Custom),
  Working Color Space, Display Color Space. A script can set the engine and config; the OCIO working
  and display spaces are GUI only. Use 32 bpc in OCIO mode (16 bpc is refused).
- Display Color Space per comp: menu at the bottom of the Composition panel (OCIO projects only); it
  overrides the project default for that comp and is preview only.
- Display color management (Adobe engine): View > Use Display Color Management (Ctrl+Opt+/). View >
  Simulate Output is preview only.

## Footage color

- Interpret Footage: select the item, File > Interpret Footage > Main (Cmd+Opt+G) > Color tab:
  Override Media Color Space (tick Show All in OCIO projects), Interpret As Linear Light, Preserve
  RGB (for control layers such as displacement maps).
- Copy an interpretation: Remember Interpretation (Cmd+Opt+C), then Apply Interpretation (Cmd+Opt+V)
  on the other items.
- Limited-range video that looks washed out: Interpret Footage > Color > Media Color Space: HDTV
  (Rec. 709) 16-235.

## Grade

- Effect > Color Correction > Lumetri Color: Basic Correction (Input LUT, white balance, tone),
  Creative (Look, Intensity), Curves, Color Wheels, HSL Secondary, Vignette. Curves, wheels,
  eyedroppers and the LUT and Look pickers are GUI only.
- Black point: with Lumetri Scopes > Waveform open, lower Basic Correction > Blacks until the
  darkest trace touches 0 (y4fuhIPxmJg 00:06:34).
- Window > Lumetri Scopes: Waveform, Parade, Vectorscope, Histogram; 8 Bit, Float or HDR scale.
- Effect > Utility > Apply Color LUT: opens a file chooser at once. Add it by hand only.
- OCIO effects (any project): Effect > Utility > OCIO Color Space Transform, OCIO Display Transform,
  OCIO File Transform, OCIO Look Transform, OCIO CDL Transform. Their color space menus are set in
  Effect Controls.

## Grain and finishing

- Effect > Noise & Grain > Add Grain: Viewing Mode > Final Output before judging; Application >
  Blending Mode (Film for shadows).
- Effect > Noise & Grain > Match Grain (on a title or graphic over a grainy plate): Viewing Mode >
  Final Output; Noise Source Layer = the plate; Compensate for Existing Noise 2 to 4 %; Sampling >
  Selection Manual to drag sample boxes onto flat background.
- Effect > Noise & Grain > Remove Grain: Viewing Mode, Noise Reduction Settings, Fine Tuning.

## Safe areas

- Composition panel > Choose Grid and Guide Options (the grid icon) > Title/Action Safe (apostrophe
  key toggles).
- Preferences > Grids & Guides > Safe Margins: Action-safe and Title-safe percentages, Center-cut
  Action-safe and Title-safe.

## Render and export

- Composition > Add to Render Queue (Cmd+M); Composition > Add to Adobe Media Encoder Queue
  (Cmd+Opt+M) does not carry output module settings or file name templates.
- Render Queue > Render Settings (blue text): Quality, Resolution, Proxy Use, Color Depth, Time
  Span, Frame Rate, Motion Blur.
- Render Queue > Output Module (blue text): Format, Format Options (ProRes flavor, H.264 bitrate,
  PNG Compression, new in 27.0), Channels (RGB + Alpha), Depth, Color (Straight or Premultiplied),
  Resize, Crop, Audio Output. Color tab: Output Profile or Output Color Space (Show All in OCIO),
  Convert To Linear Light, Preserve RGB, Embed color space.
- Add an output module to an item: select the item, Composition > Add Output Module, or click the
  plus sign next to Output Module.
- Templates: Edit > Templates > Render Settings or Output Module: set Movie Default, Frame Default
  and Pre-render defaults; Save All exports `.ars` or `.aom`; Load imports them on another machine.
  Set the Render Settings Frame Default to Best Settings so a single exported frame renders at full
  resolution (FZ9yfCeZZMA 00:04:50). Delete an agent-created template here (reassign it first if it
  is a default).
- Finals: Render Settings > Proxy Use > Use No Proxies (Best Settings already reads it).
- Camera-log version for a colorist: Output Module > Color > Show All > Output Color Space = the
  footage's input transform; ProRes 4444, EXR or DPX.
- Multi-Frame Rendering: Preferences > Memory & Performance > Enable Multi-Frame Rendering, CPU
  limit.
- Transparency check in the viewer: Toggle Transparency Grid at the bottom of the Composition panel.
