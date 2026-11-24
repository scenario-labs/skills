# Critique rubric: judge a material before it enters a shot

Score each item pass, fail or n/a. One fail on a blocking item (B) stops delivery. Report the
failing items with the finding or crop that shows them. Never judge from a material-editor thumbnail
or a viewport capture: OpenPBR draws with a simplified viewport shader, and Corona and V-Ray maps
such as triplanar and randomizers do not preview there (uv-baking digest batch 3, fact 10).

## 1. Measurable (from the audits and the build report)

| #   | Check                  | Pass when                                                                                                                                                                                                                   | B   |
| --- | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- |
| 1   | Data maps color space  | every roughness, gloss, metalness, normal, height, AO and mask map reads Raw (`audit_textures`)                                                                                                                             | B   |
| 2   | Color maps color space | base color and emission read sRGB                                                                                                                                                                                           | B   |
| 3   | Color-space status     | no `#forcedDefault` or `#invalid`                                                                                                                                                                                           | B   |
| 4   | V-Ray bitmaps          | every VRayBitmap has a `_srgb`, `_raw` or `_lin_srgb` tag, or manual settings recorded                                                                                                                                      | B   |
| 5   | Missing maps           | zero                                                                                                                                                                                                                        | B   |
| 6   | Slots                  | every map in the build report `connected: True`                                                                                                                                                                             | B   |
| 7   | Roughness convention   | one per material; Corona roughness mode and VRayMtl BRDF mode match the map type                                                                                                                                            | B   |
| 8   | Normal maps            | pass through a normal node (not glTF); DirectX sets flipped                                                                                                                                                                 | B   |
| 9   | Metalness              | 0 or 1 unless driven by a mask map                                                                                                                                                                                          |     |
| 10  | Debug leftovers        | no pure red (255, 0, 0) color in any material                                                                                                                                                                               | B   |
| 11  | Albedo extremes        | no base or diffuse color at pure 0 or 255                                                                                                                                                                                   |     |
| 12  | Multi/Sub-Object       | every face ID used has a sub-material                                                                                                                                                                                       | B   |
| 13  | Layered materials      | no empty base; each layer has a mask                                                                                                                                                                                        | B   |
| 14  | VRayMtl options        | Cutoff above 0; no Opacity Clip together with bump; OpenPBR mode only when rendering on CPU; gloss values re-checked after a mode switch (P14); Fog system units scaling on for tinted glass; displacement set in one place |     |
| 15  | Mapping                | one shared mapping source or triplanar per material; real-world repeat size recorded                                                                                                                                        |     |
| 16  | Dirt layers            | opacity below about 50 percent; VRayDirt same-object-only on objects that touch others                                                                                                                                      |     |
| 17  | Class                  | matches the renderer and deliverable table in SKILL.md                                                                                                                                                                      | B   |
| 18  | Render time            | recorded against the same frame with a plain gray material; a large jump is explained (layered stacks, SSS, caustics) [added]                                                                                               |     |
| 18b | OpenPBR exchange       | for a USD or MaterialX deliverable, a round trip rendered against the ASWF OpenPBR Shader Playground or the source render, with the features used listed (Adobe OpenPBR FAQ)                                                |     |

## 2. Visual (look-dev rig renders, then shot renders)

Render the 50 cm ball and floor under (a) a neutral HDRI and (b) the HDRI plus one raking
directional light. Then render two crops of the real shot: close and far. Put the reference photo
next to them in one contact sheet (`max_review.contact_sheet`).

| #   | Look for                                                         | Fail sign                                                                                               | B   |
| --- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | --- |
| 19  | Overall value against the reference at matched exposure and tone | darker or brighter by a visible step; colors washed                                                     | B   |
| 20  | Roughness reading                                                | uniform highlight everywhere (CG look); veins or wear shiny where the reference is matte (inverted map) | B   |
| 21  | Scale                                                            | grain, weave, tiles or flakes the wrong size against the 50 cm ball or a known object                   | B   |
| 22  | Repetition                                                       | the same blotch visible twice on the largest face                                                       |     |
| 23  | Stretching                                                       | smeared texture on faces without UVs                                                                    | B   |
| 24  | Seams                                                            | a line at the tile border or at a triplanar blend                                                       |     |
| 25  | Bump strength                                                    | visible only under the raking light; "crispy" or dark-pixel noise on fabric                             |     |
| 26  | Wear placement (red pass)                                        | red off the convex edges, or a perfectly even edge line                                                 | B   |
| 27  | Dirt placement (red pass)                                        | red on the floor contact underside; no gravity bias on facades                                          | B   |
| 28  | Dust placement (red pass)                                        | red on vertical or downward faces                                                                       |     |
| 29  | Dirt strength in the final                                       | visible as a pattern from the far crop                                                                  |     |
| 30  | Metal                                                            | edge tint missing or wrong; diffuse visible on metal                                                    |     |
| 31  | Glass                                                            | black or opaque core (depth); a refracted background behind a single-face pane (thin-walled off)        | B   |
| 32  | Coat                                                             | color washed out (car paint coat too strong), or a base darkening nobody asked for                      |     |
| 33  | Fabric                                                           | plastic highlight; no sheen at grazing angles                                                           |     |
| 34  | Brightest spot                                                   | a pure white object stealing the focal point in the shot                                                |     |

## 3. How to look at a capture

- Compare at the same exposure. If the reference has bloom or glare, match it before judging
  (CxHKVjeycv0 00:17:19).
- Judge bump only at pre-final resolution, not on a denoised interactive preview (64vzHYEWedI
  00:45:59).
- For an ACEScg switch, render once tagged and once manual: the frames must match to the pixel
  (QuJe2j7SHZ0 00:07:45). `max_review.compare(a, b)` gives the difference.
- For dirt layers, raise the layer until clearly too strong, then back off to about a quarter
  (38-TGp5QCMY 00:08:33).
- Say what the capture cannot show: displacement silhouettes need the final camera, and SSS needs
  real thickness.

## 4. Report format

```
Material: <name>  Class: <class>  Renderer: <renderer>  Target: <deliverable>
Blocking fails: <ids or none>
Other fails: <ids>
Evidence: <finding rules, crop file names>
Known gaps: <items not judged and why>
```
