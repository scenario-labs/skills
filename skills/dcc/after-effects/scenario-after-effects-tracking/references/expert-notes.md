# Expert notes: tracking, stabilization, matchmove

Attributed judgment from the sources (sources.md). Timestamps are hh:mm:ss in the video. [added]
marks this skill's own measured additions.

## Choosing the tracker

- Flat target: Mocha or a corner pin. Camera move with parallax: the 3D Camera Tracker. Simple 2D:
  the point tracker to a null (consensus of Boris FX TF3XVBy6sD4, Film Riot kFCNhHI5yOg, Mark
  Christiansen C_dO9HGrYS8).
- The native point tracker needs sharp, unchanging points; the Camera Tracker needs camera movement
  and static objects; Mocha handles blurry, texture-poor planes (Ben Brownlee, TF3XVBy6sD4
  00:02:30).
- Planar tracking is the fallback when the 3D Camera Tracker "gives us nothing" on a locked-off shot
  (TF3XVBy6sD4 00:02:30; Javier Mercedes, UkC9qKS7c0Y 00:03:01).
- Planar means low parallax, not flat: distant backgrounds, faces, rocky ground, torsos and car
  bodies can track (Boris FX doc, Tracking Basics).
- Choose only the channels the shot needs; a handheld push toward a wall needs position, rotation
  and scale (Ryan Connolly, kFCNhHI5yOg 00:00:12).

## Point tracker

- Inner feature box as small as the feature; outer search box as small as the motion allows, since a
  wider one slows the track (kFCNhHI5yOg 00:00:44).
- The search region must hold only the frame-to-frame movement, not the movement over the shot
  (Adobe doc, Tracking and stabilizing).
- One point tracks position, two add scale and rotation, four drive a corner pin (Adobe doc).
- Apply to a null, then parent the content: the content stays editable (kFCNhHI5yOg 00:01:48).

## Planar tracking (Mocha AE)

- The spline is a "sniffer dog": a search area. The Surface is the data (Ben Brownlee, TF3XVBy6sD4
  00:11:20). Judge the track with the Surface and the Grid, never with the shape (TF3XVBy6sD4
  00:11:51).
- Fixing drift by nudging the shape or the Surface does not change the track; fix the cause and
  retrack (TF3XVBy6sD4 00:13:32; UkC9qKS7c0Y 00:11:10).
- Reflections and fingers are the top track killers: an Add-spline hole removes reflections, a layer
  above removes fingers (TF3XVBy6sD4 00:04:33 to 00:07:46).
- When screen content changes, track the stable bezel or cover, then move the Surface to the screen
  corners (UkC9qKS7c0Y 00:04:42).
- Switch the cog off on finished layers before tracking others, or their keys change (UkC9qKS7c0Y
  00:09:00).
- Start from the largest, clearest frame and track both ways (Boris FX doc, Tips for Tracking).
  Raise Min % Pixels Used when it drifts (same doc).
- Settings shown for a hard car track: Luminance, Min % Pixels Used 20, Smoothing 0, Large Motion,
  all five motion types (Ben Brownlee, 1tWKdbjKLNE frame 00:06:33).
- AdjustTrack fixes drift, not jitter. Adjust at the peak of drift, then check halfway between keys;
  hundreds of adjustment keys mean retrack (Boris FX doc, AdjustTrack).
- "Track is good in Mocha but wrong in After Effects" checklist: data created, right layer, right
  data type, Surface set, insert resolution, resolution again (1tWKdbjKLNE 00:06:54).
- The insert must match the tracked footage size. UHD footage in an HD comp: precomp at UHD and
  match the footage layer's scale; the motion blur corner pin breaks that case because it adds scale
  keys (1tWKdbjKLNE 00:05:13 to 00:06:18).
- Javier Mercedes keeps the true screen aspect explicitly: a comp-size reference solid takes the
  pin, then a precomp at the real screen size (1170 x 2532) (UkC9qKS7c0Y 00:12:48). Use it when the
  replacement's aspect differs from the screen.
- Stabilizing from Mocha: export After Effects Transform with Invert and target the footage layer
  (1tWKdbjKLNE 00:01:47); delete anchor point keys after pasting Transform data (Boris FX doc).
- Mocha clip length, frame rate, size and pixel aspect must equal the After Effects footage or
  exports drift (Boris FX doc, Export).

## Patches and inserts

- Corner pin a freeze-frame patch precomp, using Align Surface so the surface equals the full frame:
  every edit on the patch rides the track, and "Support Motion Blur" adds blur (Mark Christiansen,
  C_dO9HGrYS8 00:05:23 to 00:06:30).
- A squashed logo comes from a surface whose aspect differs from the comp: fix with Align Surface or
  a fit-to-comp precomp, not by scaling (C_dO9HGrYS8 00:03:44).
- Match the patch to the plate: color-picked fill, multiplied grunge, Fast Box Blur, keyframed
  Levels, Noise HLS Auto grain (C_dO9HGrYS8 00:08:42 to 00:10:19).
- [added] Measured on 27.0: Corner Pin pixels are identical with the motion blur switch on or off.
  Blur needs the motion on Position, which is what "Support Motion Blur" exports.

## 3D Camera Tracker

- Average Error below 1 pixel is good, lower is better (Guerrilla Filmmaking, wiISCTB4s1Y 00:02:07;
  Film Riot, kFCNhHI5yOg 00:02:19; Cinecom, m2bF4U6EBZU 00:01:46).
- Detailed Analysis is the first retry for a weak solve; check that the error fell (wiISCTB4s1Y
  00:02:07; m2bF4U6EBZU 00:05:10).
- Delete markers on moving subjects; Auto-delete Points Across Time removes a feature at every
  frame; an alpha channel on the layer also excludes regions (m2bF4U6EBZU 00:02:18; Adobe doc).
- Track a prepared reference precomp (Levels, Unsharp Mask Amount 100 Radius 2), then swap back to
  the original (wiISCTB4s1Y 00:01:04 to 00:06:55). Cinecom prefers fixing it at the shoot with a
  faster shutter (m2bF4U6EBZU 00:01:10). Deciding condition: a post-only job with log footage versus
  a shoot you control.
- Leave Auto Detect and read Method Used (wiISCTB4s1Y frame 00:03:01), or name the method because
  Auto Detect "can be wrong" (m2bF4U6EBZU 00:04:51). Deciding condition: a known scene type (flat
  wall, a camera panning in place) versus unknown.
- Specify Angle of View takes the horizontal angle, not the focal length: 15 mm is about 100 degrees
  on full frame, 75.9 on DX (m2bF4U6EBZU 00:04:19).
- Set Ground Plane and Origin before creating layers; layers created earlier are not updated (Adobe
  doc).
- Validate with a Grid on the ground solid and watch for sliding (wiISCTB4s1Y 00:03:09).
- Move a ground layer's anchor to its bottom so scale grows from the ground (wiISCTB4s1Y 00:05:18).
  [added] Measured on 27.0: `AEK.build.anchor(layer, 0.5, 1)` on the 2D layer, then
  `threeDLayer = true`, keeps the anchor at the base.
- The point context menu offers Create Shadow Catcher, Camera and Light next to Create Text, Solid
  or Null and Camera (Cinecom, m2bF4U6EBZU frame 00:06:00; Adobe doc: a white solid at footage size
  set to accept shadows only, plus a light if none exists). Mocha Pro solves build the catcher by
  hand with Accepts Shadows = Only (Ben Brownlee, wEM6eyrrAgY 00:07:53); the renderer choice belongs
  to scenario-after-effects-3d.
- Retrack a failed solve: results vary between runs (m2bF4U6EBZU 00:02:25).
- Normalize scripts fix a huge solved scale; Guerrilla treats it as routine, Cinecom only when the
  space looks huge (wiISCTB4s1Y 00:04:08; m2bF4U6EBZU 00:06:44). The free Normalize Track script
  needs a solid named "ground", "floor" or "wall" (wiISCTB4s1Y 00:04:41).
- Mocha Pro solves: about 1 HPix average error; track at full resolution, proxies misalign; export
  only the nulls you need (Ben Brownlee, wEM6eyrrAgY 00:00:48 to 00:02:11).
- [added] Measured on 27.0: the "Average Error" row is a property whose NAME stays "Average Error:
  -" after a finished solve. A script cannot read it.

## Warp Stabilizer

- Use Stabilize Only framing to see the true correction and warping, then pick the framing (Jake
  Bartlett, 28L2XalNr5A 00:02:24).
- Smoothness above what the framing allows raises the extreme-cropping banner: reduce it or use
  Stabilize Only (28L2XalNr5A 00:05:40).
- Crop Less <-> Smooth More is a tolerance slider; synthesis controls work only with Synthesize
  Edges (28L2XalNr5A 00:12:23, 00:12:56).
- Stabilization does not remove blur: Warp Stabilizer first, then Camera-Shake Deblur on the result
  (28L2XalNr5A 00:01:36, 00:19:38).
- Reversible plus Reverse Stabilization: effects placed between the two inherit the shake
  (28L2XalNr5A 00:14:53).
- Apply Motion to Target with Target Layer set to Effects & Masks lets a Transform effect reposition
  the target (28L2XalNr5A 00:18:09).
- Rolling Shutter Repair: rate 100 % for a whip pan, reverse Scan Direction for upside-down or
  portrait cameras, Warp method (28L2XalNr5A 00:23:16 to 00:24:53).
- Camera-Shake Deblur: Strength up to 200, Blur Duration in frames each side, High Quality method
  (28L2XalNr5A 00:21:17 to 00:22:21).
- The analysis ignores masks and effects on the same layer: precompose them (Adobe doc).
- [added] Measured on 27.0: the analysis only advances while the app is idle; `aerender` renders the
  blue banner; a Smoothness or Method change needs a second idle pass ("Stabilizing"); Framing
  applies at once.

## Stabilizing by keys [added]

- A locked result needs much more scale than a smoothed one: 118.65 % versus 105.37 % on the same
  shot.
- One moving average leaves jitter (0.99 px); two passes leave 0.29 px at 9 frames, 0.066 px at 25
  frames.
- Locking keeps the reference frame's tilt: choose a level frame as reference.

## Mask Tracker (26.3)

- Method Perspective for a moving camera and subject; a garbage mask is enough; nudge the path at
  the failure frame, then retrack (Jake Bartlett, DK04C1mro-U 00:00:40).
- Median scoped to a tracked mask is a fast censor for plates and faces (DK04C1mro-U 00:01:19 to
  00:01:50).
