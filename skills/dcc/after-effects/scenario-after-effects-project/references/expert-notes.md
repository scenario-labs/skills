# Expert notes: project setup, structure and speed

Principles and judgment, by expert, with source and timestamp. Items marked [added] are this skill's
own reasoning. Items marked [live 27.0] were measured in After Effects 27.0 and decide any
disagreement.

## Collapse Transformations and Continuously Rasterize

**Caleb Ward, School of Motion** (J3ApvB8sqD0, After Effects CC 2018, Classic 3D)

- One switch, two jobs: Continuously Rasterize on vector layers, Collapse Transformations on a
  nested comp. Either way it changes render order: transformations are computed before other steps
  (00:00:45, 00:01:55).
- A small imported vector scaled up looks pixelated because it was rasterized at import size; the
  switch makes it sharp at every transform change (00:03:27). Same for a masked solid scaled up
  (00:05:40).
- With the switch on, an effect such as Fractal Noise stops scaling with the layer: effects now
  behave "more like a matte" (00:07:21, 00:07:55).
- A normal precomp renders like footage; a collapsed one renders "much more like a folder" of live
  3D layers (00:12:19, 00:12:52).
- Any effect, closed mask or layer style on a collapsed precomp makes the inner layers lose their 3D
  interaction with the parent. Disabling the effect is not enough: delete it (00:13:25, 00:14:31).
  [live 27.0] Confirmed on Classic 3D (`comp.renderer` `ADBE Advanced 3d`; Advanced 3D is
  `ADBE Calder`): with a glow on, then with the glow disabled, three collapsed cards all rendered
  behind an outside 3D plane; with the glow deleted the frame matched the clean collapsed frame (0
  pixels different).
- Use collapse to apply one effect to many 3D layers at once only when they do not need to intersect
  outside layers (00:12:52).

**Jake Bartlett, Jake In Motion** (Ns41v75th_I, 2022)

- "This switch does two different things and it has two different names" (00:00:00).
- Shape and text layers are always continuously rasterized; a flat imported Illustrator layer is not
  until switched on (00:03:00).
- Collapse ignores the cameras inside the precomp: add a camera in the parent comp to see the 3D
  scene again (00:05:59, 00:06:31).
- Collapse also removes precomp bounds cropping (00:08:10).
- Point-control effects (Gradient Ramp) on a collapsed precomp keep their points at comp
  coordinates, because transformations are applied after effects; turn collapse off if the effect
  must follow the layer (00:09:14, 00:09:46).
- Drive depth with one dial: parent offset layers to a 3D null and scale its Z (00:04:58).

**Adobe documentation** (precomposing, nesting, pre-rendering)

- Raster layers render masks, effects, transformations, layer styles; continuously rasterized vector
  layers render masks, then transformations and effects. Nested comps render before the other layers
  of the containing comp. The 2018 chart in J3ApvB8sqD0 differs; trust the documentation.
- An adjustment layer inside a collapsed precomp forces flattening and cropping.
- Collapsing cancels opposite scales (50 % inside, 200 % outside) with no resolution loss.
- Without collapse, a nested 3D comp renders as a 2D image from its own default camera and cannot
  intersect, cast or receive shadows.

## Preparing layered art for After Effects

**Kyle Hamrick, School of Motion** (fuDs-WPyAR4, 2022)

- Prep is about how pieces will move, not how the design looks: an approved design "will probably
  need some restructuring" (00:00:33).
- Make your own copy, name it clearly, export a reference image, resize to what is needed, confirm
  the color mode before anything else (00:02:49).
- Photoshop groups become precomps that hide their contents: "when in doubt fewer groups is probably
  better" (00:04:58, 00:06:02).
- Only one instance of each layer style survives import: three strokes arrive as one (00:13:31).
- Gradient Map and Color Lookup adjustment layers arrive empty: export a LUT from Photoshop and load
  it in Lumetri Input LUT, or rebuild with Tint, Tritone, CC Toner, Colorama (00:15:17, 00:15:49).
- A mask on a Photoshop group is ignored; a pixel layer mask is baked and changes bounds. Rebuild
  the group mask on a solid and use it as a track matte (00:17:46, 00:18:19).
- Difference blend mode on the original over its replacement shows misalignment as non-black pixels
  (00:10:45).

## Proxies, previews and rendering speed

**Motion Science** (y3Qgs2N5z1Y, 2020)

- Work heavy footage through a draft-quality, low-bitrate proxy; the final render uses the original
  (00:00:00, 00:01:28).
- The default proxy codec (Animation) is heavy; switch it to ProRes 422 (00:00:55).
- Render Settings Proxy Use defaults to Use No Proxies, so a proxy cannot reach the master by
  accident (00:02:53). [live 27.0] True for Best Settings and a new queue item. The Draft Settings
  template sets Proxy Use to Current Settings: a draft render then uses every proxy that is switched
  on.

**Ben Marriott, Adobe Video** (p9sFn-b777k, 2022)

- Multi-Frame Rendering helps previews as well as final renders (00:00:00). Speed table on screen:
  1.2 to 1.5x on 4 to 6 cores, 1.75 to 2x on 8 to 10 cores, 2.5 to 4x on 16 to 64 cores (frame
  00:00:38).
- Rendering inside After Effects is generally faster; Media Encoder lets you keep working
  (00:02:11). Since 23.0 H.264 renders from the Render Queue, so Media Encoder is only for
  background export and presets.
- The Render Queue Info panel shows frames per second, average frame time and concurrent frames
  (00:01:05).

**Adobe documentation** (Composition Profiler)

- Render Time column per layer and effect, Frame Render Time in the Timeline footer. Green means
  real time or half real time at the comp frame rate; 100 ms to 5 s runs yellow to red.
- Cached items carry an asterisk: purge All Memory & Disk Cache before profiling. Turn Adaptive
  Resolution off so the times match the preview resolution.
- A layer whose video is off but is used by an effect (Set Matte, Compound Blur) shows no time: the
  referencing effect carries it.
- A precomp used several times shows faster on its later instances because they reuse the cache of
  the first.
- Documented fixes: proxies, pre-render with Import & Replace Usage, lighter alternatives (Fast Box
  Blur for Gaussian Blur, Glow for a heavier glow, Tint or Tritone for Colorama).

**Adobe documentation** (Multi-Frame Rendering)

- On by default; CPU reserved for other applications 0 to 70 %, default 10 %. Effects without MFR
  support show a yellow warning icon. Speculative Preview renders idle comps after 8 seconds by
  default.

## Frame rates and nesting

- Use Preserve frame rate when nested (Composition Settings > Advanced) for a deliberate low frame
  rate precomp instead of Posterize Time (Adobe documentation).
- [live 27.0] Changing a comp's frame rate keeps every key at its time in seconds: keys on frames
  15, 20, 30 at 30 fps landed on 12.5, 16.67 and 25 at 25 fps. Re-snap or rebuild the timing after
  any comp conform.
- [added] Conform footage frame rate only when the file is mistagged. A 30 fps clip in a 25 fps comp
  plays at real speed and only drops frames; conforming it changes its duration.

## Essential Properties

**Jake Bartlett, Jake In Motion** (-XzXh4E6N5o, frames only)

- Rig once inside one precomp, expose only what changes per instance (size, fill color, brightness,
  contrast, a texture offset point), then duplicate the precomp layer and vary the values (frames
  00:04:48 to 00:10:36).
- Group exposed controls under headings in the Essential Graphics panel (frame 00:13:18).

**Adobe documentation** (Essential Properties, Motion Graphics templates)

- An instance stays linked until modified; a modified value is bold. Push applies the override to
  the source and every instance; Pull discards it.
- Exposed Source Text is edited in the parent with Edit Value or an expression; the Type tools do
  not work there.
- A property added from outside the primary comp's hierarchy turns red and does not export.
- [live 27.0] Overrides set by script on one instance left the source comp and the other instances
  unchanged; `essentialPropertySource` returns the source property.

## Fonts and missing media

- [live 27.0] A font that is not installed is accepted silently by a script. After the project is
  saved and reopened, `app.fonts.getFontsByPostScriptName()` returns a substitute Font object for
  that name, so its length is 1: it cannot detect a missing font.
  `Project.usedFonts[i].font.isSubstitute` (and `TextDocument.fontObject.isSubstitute`) does.
- [live 27.0] Moving a source file off its path makes the item missing on the next open;
  `FileSource.missingFootagePath` keeps the old path, which gives the file name to search for.

## After Effects 26 and 27 changes that shorten intake

- **Jake Bartlett** (6wQjuplvypI): keep Advanced 3D Render Quality and Smoothness low while working
  (12 and 2) and raise them only for the final render (00:09:32).
- **Jake Bartlett** (RcNUE6lg3fE): the AI Assistant can organize, rename and color-code project
  items and inspect Essential Graphics; it charges credits per action and asks before acting
  (00:00:33, 00:01:23). Use it for tedious tidying with a person present, not as the agent's
  channel.
- 27.0 Auto-Save works before a project is named and recovers after a crash (version deltas).
