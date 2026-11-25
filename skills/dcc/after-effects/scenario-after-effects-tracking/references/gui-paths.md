# GUI paths (for a person or a computer-use agent)

After Effects 27.0. Menu labels as in the English UI. Command ids from `app.findMenuCommandId` are
given where they exist.

## Point tracker (Tracker panel)

1. Window > Tracker (command 5005). Select the footage layer.
2. Track Motion (Animation > Track Motion, command 2568) or Stabilize Motion in the panel. Track
   Type: Stabilize, Transform, Parallel Corner Pin (three points, fourth computed), Perspective
   Corner Pin (four points), Raw (position only).
3. Check Position, Rotation, Scale as the shot needs. One point tracks position, two add scale and
   rotation, four pin corners.
4. In the Layer panel, size the inner feature box to the feature and the outer search box to the
   largest frame-to-frame move. Offset the search box toward the direction of travel.
5. Options: Channel (RGB, Luminance, Saturation), Enhance Before Match (blur 2 to 3 px on grainy
   footage), Subpixel Positioning, Adapt Feature On Every Frame, If Confidence Is Below (Continue,
   Stop, Extrapolate Motion, Adapt Feature).
6. Analyze Forward or Backward. Stop at a slip, move the feature box back, analyze again from there.
7. Edit Target (a null), then Apply. Alt or Option on Apply reuses the previous options without the
   dialog.

- With motion blur on the footage, set Shutter Phase to minus half the Shutter Angle (Adobe doc).
- A script reaches the same data at `layer.property("ADBE MTrackers")`; it cannot press Analyze.

## Warp Stabilizer

1. Select the layer. Effect > Distort > Warp Stabilizer, or Animation > Warp Stabilizer. Analysis
   starts in the background with a blue banner.
2. Stabilization: Result (Smooth Motion, No Motion), Smoothness, Method (Position; Position, Scale,
   Rotation; Perspective; Subspace Warp).
3. Borders: Framing (Stabilize Only; Stabilize, Crop; Stabilize, Crop, Auto-scale; Stabilize,
   Synthesize Edges), Auto-scale (shows the percent), Maximum Scale, Action-safe Margin, Additional
   Scale.
4. Advanced: Detailed Analysis, Rolling Shutter Ripple, Crop Less <-> Smooth More, synthesis
   settings, Objective (Stabilize, Reverse Stabilization, Apply Motion to Target, and Reversible
   variants), Target Layer, Show Track Points.
5. Masks and effects on the same layer are ignored by the analysis: precompose them first.

- Then Camera-Shake Deblur (Effect > Blur & Sharpen) below Warp Stabilizer, and Rolling Shutter
  Repair (Effect > Distort) where needed.

## 3D Camera Tracker

1. Select the footage layer. Animation > Track Camera (command 3983), Effect > Perspective > 3D
   Camera Tracker, or Track Camera in the Tracker panel.
2. Wait for "Analyzing in background" and "Solving camera" to clear.
3. Advanced: read Average Error. Try Detailed Analysis, a named Solve Method (Typical, Mostly Flat
   Scene, or the pan-only method for a camera that rotates in place) or Shot Type (Specify Angle of
   View with the horizontal angle). Re-read the error after each change.
4. With the effect selected, delete points on moving subjects (select, Delete). Auto-delete Points
   Across Time removes them at every frame.
5. Select three or more ground points: the target appears. Right-click > Set Ground Plane and
   Origin, before creating anything.
6. Right-click > Create Text and Camera, Create Solid and Camera, Create Null and Camera, the
   "multiple" variants, or Create Shadow Catcher, Camera and Light. Create Camera alone is in Effect
   Controls.
7. Proof: Effect > Generate > Grid on the created solid; scrub for sliding; disable the proof after.
8. Scene at a huge scale: File > Scripts > Run Script File with the free Normalize Track script;
   select the camera and solids, rename a ground solid "floor" if it asks, then Normalize Track
   (wiISCTB4s1Y 00:04:08).

- File > Export > Maxon Cinema 4D Exporter writes the camera for a 3D application (Adobe doc).

## Mocha AE (bundled, effect match name `mochaAECC`)

1. Select the footage layer. Animation > Track in Boris FX Mocha (command 5008), or Effect > Boris
   FX Mocha > Mocha AE, then the large Mocha button in Effect Controls.
2. In Mocha: X-Spline tool, draw around the plane with a little margin; the X-Spline variant with a
   plus ("Add X-Spline to Layer") adds a hole for reflections. Fingers go on a separate layer above.
3. Motion: Translation, Scale, Rotation, Shear, Perspective as needed. Track forward and backward
   from the clearest frame.
4. Surface button: drag the four Surface corners to the real corners on a front-on frame; turn on
   the Grid to check.
5. Drift: AdjustTrack tab (Mocha AE includes AdjustTrack), or retrack after fixing the cause.
6. Save, close Mocha. In Effect Controls: Tracking Data > Create Track Data, pick the layer, OK.
   Export Option: Corner Pin, Corner Pin (Support Motion Blur), or Transform. Layer Export To: the
   insert. Apply Export.
7. Mattes: Matte > Apply Matte, or Create AE Masks (native masks ignore Mocha's feather).

- Paste paths: Edit > Paste Mocha Mask (command 5007) for mask data. Camera solves from the
  tracker's paid edition paste with Edit > Paste Mocha Camera (not present in this install: command
  id 0).
- Mocha AE gives planar tracks, masks and AdjustTrack. The insert, remove and stabilize modules and
  camera solves belong to its paid edition (Mocha AE doc).

## Mask Tracker (26.3)

Draw a mask, select it, then Animation > Track Mask (command 10311) and track forward in the Tracker
panel. Method Perspective for a moving camera and subject.

## Shortcuts

| Action                      | Shortcut              |
| --------------------------- | --------------------- |
| Reveal keyframed properties | U                     |
| Mask path                   | M                     |
| Mattes view in Mocha        | Alt+1 (default)       |
| Apply without the dialog    | Alt or Option + Apply |
