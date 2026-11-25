# Sources

## Videos

| Expert                                  | Credential                                     | URL                                         | Best for                                                                             | Best timestamps                                            |
| --------------------------------------- | ---------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| Ben Brownlee                            | planar tracking trainer and author             | https://www.youtube.com/watch?v=TF3XVBy6sD4 | Mocha AE end to end: splines, holes, Surface, export, mattes                         | 00:02:30, 00:05:43, 00:11:20, 00:13:32, 00:18:49, 00:20:49 |
| Ben Brownlee                            | planar tracking trainer                        | https://www.youtube.com/watch?v=1tWKdbjKLNE | why Mocha data is wrong in After Effects; UHD in HD comps                            | 00:01:47, 00:04:05, 00:05:13, 00:06:54                     |
| Ben Brownlee                            | planar tracking trainer                        | https://www.youtube.com/watch?v=wEM6eyrrAgY | camera solve from the tracker's paid edition to After Effects, nulls, shadow catcher | 00:00:48, 00:02:11, 00:06:48, 00:07:53                     |
| Javier Mercedes                         | video editor and educator                      | https://www.youtube.com/watch?v=UkC9qKS7c0Y | phone screen replacement, hands, true screen aspect                                  | 00:03:01, 00:04:42, 00:09:00, 00:12:48                     |
| Mark Christiansen (School of Motion)    | VFX artist, author of the VFX for Motion class | https://www.youtube.com/watch?v=C_dO9HGrYS8 | corner-pinned patch precomp, Align Surface, matching the plate                       | 00:03:44, 00:05:23, 00:08:42                               |
| Jake Bartlett (Jake In Motion)          | motion designer, School of Motion instructor   | https://www.youtube.com/watch?v=28L2XalNr5A | Warp Stabilizer framing, reverse stabilization, deblur, rolling shutter              | 00:02:24, 00:05:40, 00:14:53, 00:18:09, 00:21:17, 00:23:16 |
| Jake Bartlett (Jake In Motion)          | After Effects educator                         | https://www.youtube.com/watch?v=DK04C1mro-U | Mask Tracker in 26.3, tracked censor                                                 | 00:00:40, 00:01:19                                         |
| Cinecom.net                             | filmmaking channel                             | https://www.youtube.com/watch?v=m2bF4U6EBZU | why 3D camera tracks fail: blur, moving subjects, angle of view, solve methods       | 00:01:10, 00:02:18, 00:04:19, 00:04:51, 00:06:44           |
| Guerrilla Filmmaking                    | filmmaking channel                             | https://www.youtube.com/watch?v=wiISCTB4s1Y | reference precomp, Average Error, grid proof, Normalize                              | 00:01:04, 00:02:07, 00:03:09, 00:04:08, 00:05:18           |
| Ryan Connolly (Film Riot x Adobe Video) | filmmaker, Film Riot host                      | https://www.youtube.com/watch?v=kFCNhHI5yOg | point track to a null, 3D camera basics                                              | 00:00:12, 00:00:44, 00:01:48, 00:02:19                     |
| ProductionCrate                         | stock VFX company                              | https://www.youtube.com/watch?v=gomawnMPWEg | elements parented to a tracked null                                                  | 00:03:48                                                   |

## Documentation

| Source                                 | URL                                                                                                                              | Best for                                                                             |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Adobe, Tracking and stabilizing motion | https://helpx.adobe.com/after-effects/desktop/animate-in-after-effects/track-motion/tracking-stabilizing-motion-cs5.html         | Tracker panel, track types, options, Warp Stabilizer settings                        |
| Adobe, Tracking 3D camera movement     | https://helpx.adobe.com/after-effects/desktop/work-with-3d-composition/3d-camera-tracker-effect/tracking-3d-camera-movement.html | 3D Camera Tracker controls, Average Error, ground plane, shadow catcher              |
| Mocha AE quick start                   | https://borisfx.com/documentation/mocha/quick-start-guide                                                                        | Mocha AE menu path, export options, insert size                                      |
| Mocha AE documentation, 12.5.2         | https://borisfx.com/documentation/mocha/12.5.2/                                                                                  | tracking basics and tips, AdjustTrack, export to After Effects, paid-edition modules |

## Live measurements

The measured numbers in this skill come from After Effects 27.0 on macOS with synthetic shots of
known motion (1280x720, 24 fps, 72 frames, motion blur and noise), tracked with
`scripts/track_external.py` (Python, OpenCV 4.13).
