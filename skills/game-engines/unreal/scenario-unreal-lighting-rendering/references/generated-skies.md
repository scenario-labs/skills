# Generated skies: an equirect panorama as sky, sky light and sun (5.8.3)

A text-to-skybox or image generator gives a 2:1 long-lat panorama. This page turns it into a sky the
camera sees, a sky light that lights the scene, and a sun that matches the bright spot in the image,
with the checks that caught the mistakes. Everything marked "run on 5.8.3" was measured with the
synthetic panorama of `tests/code/unreal-lighting-rendering/make_synthetic_sky.py` (compass markers
at azimuth 0, 90, 180 and 270, a sun disc at azimuth 90 and elevation 20, a seam line) and rendered
frames read on the host. MCP calls: `mcp-lighting.md` S5.

## 1. File format decides the asset type

| Source file            | Imports as (run on 5.8.3)                | Use                                                                |
| ---------------------- | ---------------------------------------- | ------------------------------------------------------------------ |
| `.hdr` (Radiance RGBE) | TextureCube, TC_HDR_COMPRESSED, sRGB off | SkyLight specified cubemap, HDRIBackdrop, a material's cube sample |
| `.exr`                 | Texture2D 2048x1024 (long-lat)           | not a cubemap: convert first                                       |
| `.png`, `.jpg`         | Texture2D                                | LDR: no sun energy; convert and scale (section 4)                  |

Conversion without Unreal: `ffmpeg -i sky.exr -c:v hdr sky.hdr` gave a file that imported as a
TextureCube (run on 5.8.3). From an 8-bit image, `ue_light.equirect_to_linear(img, scale)` decodes
sRGB and `write_radiance_hdr(path, img)` writes the `.hdr`. Through MCP:
`TextureTools.import_file {"folder_path", "asset_name", "source_file"}`; through Python: an
`AssetImportTask`.

## 2. Orientation (run on 5.8.3)

Panorama convention used here: column u = 0.5 + azimuth / 360 (azimuth 0 at the image center,
growing to the right), row v = 0.5 - elevation / 180.

| Camera faces | Sees azimuth (SkyLight specified cubemap, angle 0; cube sampled by world direction; HDRIBackdrop) |
| ------------ | ------------------------------------------------------------------------------------------------- |
| +X (yaw 0)   | 90                                                                                                |
| +Y (yaw 90)  | 180 (the seam)                                                                                    |
| -X (yaw 180) | 270                                                                                               |
| -Y (yaw 270) | 0 (image center)                                                                                  |

No mirror flip: turning right moves right in the panorama. Source Cubemap Angle adds to the azimuth:
visible azimuth = camera yaw + 90 + angle. `cubemap_angle_for_forward(az)` returns the angle that
puts azimuth `az` at +X: 270 puts the image center at +X. Rotating the HDRIBackdrop actor (yaw 90)
did not rotate its projected sky: rotate the image with `rotate_equirect(img, yaw)` before import.

## 3. The sun belongs to a DirectionalLight

A 1.5 degree sun disc inside the cubemap did not reach the floor as sunlight: the floor read 0.091
against 0.096 predicted for the sky without the sun and 0.185 with it (run on 5.8.3). The sky light
filters it out. So:

1. `find_sun_in_equirect(linear_img)` returns azimuth, elevation and peak, or None for an overcast
   or LDR image.
2. `sun_light_rotation(az, el, cubemap_angle)` gives the light's (pitch, yaw, roll): pitch is minus
   the elevation, yaw points away from the sun.
3. Set the light with `ActorTools.set_actor_transform` and read the rotation back.
4. Paint the disc out of the panorama, or leave it and accept a visible but non-lighting sun; do not
   leave a SkyAtmosphere on too, or there are two skies.

## 4. Exposure matching

A generated panorama has no physical scale. `sky_mean_radiance(img)` measures it and
`sky_scale_for_ev100(ev100, sky_mean, stops_above_grey=1.5)` returns the multiplier that puts the
mean sky 1.5 stops over mid gray at the scene's EV100 [added default]. Apply it to the pixels before
writing the `.hdr`, or to the SkyLight Intensity. Then meter a 0.18 card in a rendered frame
(`mcp-lighting.md` section 4) and correct. Under Lumen, a visible 500 m emissive sky sphere added
under 3 percent to the floor, and with the SkyLight at intensity 0 the floor read about 0 (run on
5.8.3): the SkyLight carries the fill, the backdrop only shows.

## 5. Checks before handing over

- **Seam**: `equirect_seam_error(img)` near 0 means the left and right edges meet; a generated
  panorama often does not wrap. The seam lands at azimuth 180, so at +Y with angle 0: look there in
  a capture.
- **Orientation**: capture the four world axes and compare with the table above (the synthetic sky's
  colored markers make this one glance).
- **Sun agreement**: shadows in the frame fall away from the bright spot in the sky.
- **One sky light**: HDRIBackdrop brings its own SkyLight component (Movable, captured scene);
  remove or disable the other one. The path tracer double counts an HDRIBackdrop with a second sky
  light (path tracer doc).
- **Lower hemisphere**: a dark ground in the panorama darkens the fill from below; HDRIBackdrop's
  sky light had Lower Hemisphere Is Solid Color off on 5.8.3.

Not yet run: the energy of a sky light fed by a real generated panorama (only the synthetic one was
measured), and a generated panorama's seam in a rendered frame.
