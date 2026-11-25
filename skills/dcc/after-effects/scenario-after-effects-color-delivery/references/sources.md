# Sources

## Videos

| Expert                         | Credential                           | URL                                         | Best for                                                                | Best timestamps                                  |
| ------------------------------ | ------------------------------------ | ------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------ |
| Eran Stern (SternFX)           | Motion designer, Adobe trainer       | https://www.youtube.com/watch?v=FZ9yfCeZZMA | Render settings and output module templates, several outputs per render | 00:03:44, 00:04:50, 00:07:29, 00:10:28, 00:11:03 |
| ShiveringCactus                | VFX educator, Adobe Community Expert | https://www.youtube.com/watch?v=PS5nPDpVM0E | Every transparent export path, straight or premultiplied                | 00:00:30, 00:01:38, 00:02:42, 00:03:22, 00:06:57 |
| Jake Bartlett (Jake In Motion) | Motion designer and educator         | https://www.youtube.com/watch?v=y4fuhIPxmJg | Lumetri sections, order, scopes, secondaries                            | 00:06:34, 00:10:24, 00:16:20, 00:20:58           |
| Jake Bartlett (Jake In Motion) | same                                 | https://www.youtube.com/watch?v=FmSTOXu2V6I | Add Grain, Match Grain, Remove Grain                                    | 00:00:41, 00:04:27, 00:08:47, 00:11:24           |
| Cameron (Motion Science)       | Motion designer and educator         | https://www.youtube.com/watch?v=M7Ml1KoO4jY | Finishing blur, glow and grain amounts                                  | 00:03:34                                         |
| InLightVFX                     | VFX artist and educator              | https://www.youtube.com/watch?v=x2sx-P5f-iM | OCIO and ACES pipeline, display versus output transform                 | 00:02:26, 00:05:57, 00:06:45, 00:07:52           |
| ActionVFX                      | VFX stock element studio, tutorials  | https://www.youtube.com/watch?v=pYzN_g-1N_w | ACES with stock elements, input transforms, round trip to a colorist    | 00:06:29, 00:07:57, 00:08:28, 00:09:32           |
| Adobe Care                     | Adobe support channel                | https://www.youtube.com/watch?v=zqz7WGK2pCo | Washed-out colors after export                                          | 00:00:05                                         |
| Adobe Video                    | Adobe channel                        | https://www.youtube.com/watch?v=G8BAjmaVaDg | Composition Profiler, render cost per effect                            | 00:00:21, 00:02:39                               |
| LottieFiles                    | Lottie format vendor                 | https://www.youtube.com/watch?v=dtCiHexk7J8 | Lottie exporters compared (vendor view)                                 | whole video                                      |

## Documentation

| Source                                        | URL                                                                                                                                                         | Used for                                                                                                     |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Adobe: Color management                       | https://helpx.adobe.com/after-effects/using/color-management.html                                                                                           | working space choice, linearize, Interpret Footage, output profile, 16 to 235                                |
| Adobe: OpenColorIO and ACES color management  | https://helpx.adobe.com/after-effects/using/opencolorio-aces-color-management.html                                                                          | OCIO engine, ACES 2.0 configs, display versus output color space, OCIO effects                               |
| Adobe: Basics of rendering and exporting      | https://helpx.adobe.com/after-effects/using/basics-rendering-exporting.html                                                                                 | render settings, output modules, several outputs per item, 8 bpc GPU differences, Media Encoder queue limits |
| Adobe: Export H.264 from the Render Queue     | https://helpx.adobe.com/after-effects/desktop/render-and-export/export-h-264-from-the-after-effects/exporting-h264-from-the-after-effects-render-queue.html | native H.264, 5, 15 and 40 Mbps presets                                                                      |
| Adobe: Preferences                            | https://helpx.adobe.com/after-effects/desktop/get-started/preferences-and-settings/preferences.html                                                         | safe margin defaults, Multi-Frame Rendering                                                                  |
| Adobe: Supported file formats                 | https://helpx.adobe.com/after-effects/desktop/get-started/supported-file-formats/supported-file-formats.html                                                | output formats                                                                                               |
| Adobe: Release notes                          | https://helpx.adobe.com/after-effects/desktop/what-s-new/release-notes-after-effects.html                                                                   | version notes                                                                                                |
| LottieFiles: Lottie compatibility             | https://docs.lottiefiles.com/en/integrations/after-effects/09_lottie-compatibility.md                                                                       | what survives a Lottie export                                                                                |
| EBU R 128 (V5)                                | https://tech.ebu.ch/docs/r/r128.pdf                                                                                                                         | -23 LUFS, +/- 0.5 LU, -1 dBTP                                                                                |
| YouTube: Recommended upload encoding settings | https://support.google.com/youtube/answer/1722171                                                                                                           | container, codec, audio, color, frame rate                                                                   |
| YouTube: Get started creating Shorts          | https://support.google.com/youtube/answer/10059070                                                                                                          | Shorts length                                                                                                |
| Apple: App preview specifications             | https://developer.apple.com/help/app-store-connect/reference/app-preview-specifications                                                                     | app preview sizes, length, file size                                                                         |

## Not in the sources

Streaming platform loudness targets and platform UI safe zones (captions, buttons, profile overlays)
are not in the saved sources. Read the platform's current spec and pass the numbers to `safeCheck`
and `delivery_check.py` as parameters.
