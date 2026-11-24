# Procedures: lighting and rendering

Units: centimeters for positions and light sizes unless stated. Renderer property names are the main
risk: blocks resolve them on the live object (`resolve`, `prop_dump`) and never write a name the
scene did not report. Run the inspect step before any change.

## 0. How to run these blocks

Prepend `scripts/maxkit_render.py` to the chunk and wrap it with the lead's toolkit, so the helpers
(`renderer_info`, `prop_dump`, `set_props`, `resolve`, `render_elements`, `add_element`,
`lights_report`, `color_report`, `bitmap_color_spaces`, `output_settings`, `test_render`) are
defined inside the one undo record.

```python
# channel: runner side (prepares scripts for batch | bridge | handoff)
# checked against the max_wrap contract of scenario-3dsmax-expert
from pathlib import Path

from max_wrap import wrap          # scenario-3dsmax-expert/scripts
from max_batch import run_batch    # scenario-3dsmax-expert/scripts

SKILL = Path(__file__).resolve().parent  # adjust to the installed skill folder


def build(chunk, result_path, kit=("capture",), label="lighting-rendering"):
    helpers = (SKILL / "scripts" / "maxkit_render.py").read_text(encoding="utf-8")
    return wrap(helpers + "\n\n" + chunk, lang="python", kit=list(kit),
                result_path=result_path, label=label)


def run(chunk, scene, out_dir, name):
    script = Path(out_dir) / f"{name}.py"
    script.write_text(build(chunk, str(Path(out_dir) / f"{name}.json")), encoding="utf-8")
    return run_batch(str(script), scene=scene, timeout=3600)
```

Check in the result: `ok` is true and `error` is null; then read `result`. Renders go to new files
only: `test_render` refuses an existing path.

## 1. Inspect (read-only)

Goal: know the renderer, size, output, sampling and denoise settings, elements, lights and color
state before touching anything.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-renderer-2027.md and scripting-pipeline__maxscript-bitmap-values-2027.md
r = rt.renderers.current
info = renderer_info()
result = {
    "renderer": info,
    "output": output_settings(),
    "settings": prop_dump(r, SETTING_KEYWORDS),
    "elements": render_elements(),
    "lights": lights_report(),
    "color": color_report(),
}
```

mcp-safe: propose `scripts/mxs/render_audit.ms` as is (MAXScript, read-only, no blocked commands);
its value is the report text.

Check: `renderer.family` is the one the user expects; if it is `scanline` or `other`, stop and ask
which renderer the project uses (never switch it yourself). Every light has an on state. Save the
JSON as the baseline for the diff at the end.

## 2. Color pipeline audit (read-only)

Goal: confirm one tone mapper and correct texture tagging before lighting.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__maxscript-bitmap-values-2027.md (colorSpace, colorSpaceSource, ColorPipelineMgr lists)
col = color_report()
maps = bitmap_color_spaces()
suspect = [m for m in maps
           if m["data_guess"] and m["color_space"] and "raw" not in m["color_space"].lower()
           and "data" not in m["color_space"].lower()]
invalid = [m for m in maps if m["status"] not in ("#normal", "normal", "")]
result = {"displays": col.get("displays"), "views": col.get("views"),
          "interface_props": col.get("interface_props"),
          "data_maps_tagged_as_color": suspect[:200], "invalid_color_spaces": invalid[:200],
          "bitmaps_checked": len(maps)}
```

Check:

- OCIO mode: an ACES view exists in `views`; the renderer has no exposure control or tone-map imager
  active (look for `exposure` and `tone` in the step 1 dump; V-Ray and Corona frame buffer layers
  are not readable by script, so ask or check the GUI).
- `data_maps_tagged_as_color` is empty. If not, hand the list to scenario-3dsmax-materials; normal,
  roughness and height maps must be Raw (Autodesk, dlwDiLsPWgI 00:07:07).
- Output: EXR stays in rendering space for compositing; a view transform is baked only for direct
  delivery (dlwDiLsPWgI 00:03:26).

## 3. Clay lighting pass

Goal: light without material distraction, with glass still letting light through (x8H1CNNFPgc
00:02:58 to 00:03:31).

```python
# channel: batch | bridge | handoff
# checked against x8H1CNNFPgc and 4MeUNMFxiPE notes (V-Ray names [verify]); Corona and Arnold override names unknown
APPLY = False  # first run dry, read the report, then set True
r = rt.renderers.current
fam = renderer_info()["family"]
on_name, mtl_name = resolve(r, "override_on"), resolve(r, "override_mtl")
gray = None
mtl_class = {"vray": "VRayMtl", "corona": "CoronaPhysicalMtl", "arnold": "PhysicalMaterial"}.get(fam)  # [verify] VRayMtl, CoronaPhysicalMtl
if mtl_class and hasattr(rt, mtl_class):
    gray = getattr(rt, mtl_class)()
    gray.name = "LGT_clay_override"
    # mid-gray, never pure white or black (64vzHYEWedI 00:27:26); slot name differs per class
    color_rep = set_props(gray, {"diffuse": rt.Color(128, 128, 128),          # [verify] VRayMtl
                                 "base_color": rt.Color(128, 128, 128),       # [verify] Physical, OpenPBR
                                 "baseColor": rt.Color(128, 128, 128)},       # [verify] Corona
                          dry_run=not APPLY)
else:
    color_rep = {"error": f"no material class for {fam}"}
plan = {}
if on_name and mtl_name and gray is not None:
    plan = set_props(r, {on_name: True, mtl_name: gray}, dry_run=not APPLY)
result = {"family": fam, "override_names": [on_name, mtl_name], "plan": plan,
          "material": color_rep,
          "override_candidates": prop_dump(r, ("override", "mtl")),
          "preserve_candidates": prop_dump(r, ("refract", "opacity", "exclude", "glass")),
          "next": "if override names are None, pick them from override_candidates and rerun with set_props"}
```

Check: in the test render (step 4), windows still pass sunlight (floor sun patch present). If the
preserve-refraction flag is not found, exclude glass objects from the override in the GUI, or rename
and list them for the user. Arnold has a shader override under the Diagnostics tab (ZUEnTb6QnD4
frame 00:08:10); its script name is unknown. Turn the override off before the final.

## 4. Lighting recipes

All values come from the named source; size and intensity units are the renderer's own defaults in
that video. Create lights by script only as far as the class and transform; then dump properties and
set the confirmed names.

### 4a. Light creation and aiming (shared helper)

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-using-2027.md (pos, Point3); light class names and matrixFromNormal [verify]
import math


def make_light(class_names, name, pos, aim_at=None):
    """Create the first available light class, place it, aim local -Z at aim_at."""
    cls = next((c for c in class_names if hasattr(rt, c)), None)
    if cls is None:
        return {"error": f"none of {class_names} in this install"}
    node = getattr(rt, cls)()
    node.name = name
    p = rt.Point3(*pos)
    if aim_at is not None:
        d = rt.Point3(aim_at[0] - pos[0], aim_at[1] - pos[1], aim_at[2] - pos[2])
        node.transform = rt.matrixFromNormal(-d)  # [verify] matrixFromNormal; most area lights emit along local -Z [verify]
    node.pos = p
    return {"node": node, "class": cls, "props": prop_dump(node, ("size", "length", "width", "multiplier",
                                                                   "intensity", "temperature", "kelvin", "color",
                                                                   "invisible", "visible", "type", "shadow"))}


def sun_position(target, elevation_deg, azimuth_deg, distance=5000.0):
    """Only the sun angle matters, not its distance (x8H1CNNFPgc 00:01:54)."""
    el, az = math.radians(elevation_deg), math.radians(azimuth_deg)
    return (target[0] + distance * math.cos(el) * math.sin(az),
            target[1] + distance * math.cos(el) * math.cos(az),
            target[2] + distance * math.sin(el))
```

### 4b. Interior day (V-Ray recipe, Chaos x8H1CNNFPgc)

The sun block below uses `make_light` and `sun_position` from 4a.

1. Camera: V-Ray physical camera with automatic vertical tilt; near clipping when it sits outside
   the room [00:00:15 to 00:01:19].
2. Sun with sky: create the sun, accept the sky environment; aim through the window. A low sun is
   warm: set color mode to override for neutral light; raise the sun size multiplier to soften
   shadows without changing output [00:06:20].
3. Lock the render view to the camera before moving the sun in orthographic views [00:02:26] (GUI
   padlock).
4. Exposure on the camera, not the lights. The frames show EV about 10.5 and the triple ISO 100,
   f/8, 1/200 [frames 00:00:40, 00:05:59; reading approximate]. They are two entry modes, not one
   setting: by EV100 = log2(N^2 / t) the triple is about 13.6, three stops darker than EV 10.5
   [added arithmetic]. Use EV for quick look-dev or the triple for photographic behavior (DOF,
   motion blur), never both at once; the dB4975f2yRc sun room ends at EV 10 [00:03:45].
5. Off-camera shadow casters (a tree outside the window) and a view behind the glass [00:06:59].
6. HDRI alternative: dome light with the HDRI, spherical mapping, rotate on Z only [00:13:53];
   several domes rendered once and chosen in LightMix [00:15:39]. Corona and Arnold: same order.
   Camera class differs per renderer and install: read it with `classOf` (section 5) before setting
   exposure. Corona per-camera tone mapping override handles interior about -1 EV and exterior about
   -3 EV cameras in one scene in a Gamma workflow (VizAcademy UK, hz07nIgm7EA 01:13:41).

```python
# channel: batch | bridge | handoff
# checked against x8H1CNNFPgc and 4MeUNMFxiPE notes; VRaySun, CoronaSun, ArnoldLight [verify]
TARGET = (0.0, 0.0, 0.0)        # room center on the floor, cm
fam = renderer_info()["family"]
sun_cls = {"vray": ["VRaySun"], "corona": ["CoronaSun"], "arnold": ["ArnoldLight"]}[fam]  # Arnold: distant light type [verify]
sun = make_light(sun_cls, "LGT_sun", sun_position(TARGET, elevation_deg=35, azimuth_deg=210), aim_at=TARGET)
node = sun.get("node")
if node is not None and getattr(node, "target", None) is not None:  # target-based suns
    node.target.pos = rt.Point3(*TARGET)
result = {"sun": {k: v for k, v in sun.items() if k != "node"}}
```

Elevation 35 and azimuth 210 are placeholders [added]: choose them so the sun patch lands where the
brief wants it, then judge the test render.

### 4c. Interior night (V-Ray recipe, Chaos 4MeUNMFxiPE)

| Light                                                                                                                                                                                                                                                                                                                | Values seen                                                                                      | Time                      |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------- |
| Dome (night sky)                                                                                                                                                                                                                                                                                                     | blue color, or an evening HDRI; multiplier 1.0, later 0.8 in the mix                             | 00:02:41, frame 00:06:36  |
| Dome visibility                                                                                                                                                                                                                                                                                                      | invisible; the same HDRI in Environment as background, balanced as the Environment channel (0.1) | 00:04:02, frame 00:04:36  |
| Moon (V-Ray Sun)                                                                                                                                                                                                                                                                                                     | intensity multiplier 0.02, size multiplier 8.0, blue filter or color override                    | frame 00:05:00            |
| Pendant (instanced spheres)                                                                                                                                                                                                                                                                                          | 300.0                                                                                            | frame 00:00:48            |
| Floor lamp IES                                                                                                                                                                                                                                                                                                       | power 6600 to 10000                                                                              | frame 00:00:48            |
| Fill plane from next room                                                                                                                                                                                                                                                                                            | 30.0, about 214 x 260 cm, directional 0.9 like barn doors                                        | frames 00:05:00, 00:07:00 |
| Corona has no dome light: the environment map lights the scene, and Render Setup > Scene tab > Scene Environment overrides direct visibility, reflections and refractions separately (Aga, _biqhqTpW5c 00:09:29). Use that override to keep the sky lighting the room while the window shows a different background. |
| Order: lights on before IPR, clay first, then materials; brighten pendants on the light, not in the mix [00:05:16]; switch the IPR AI denoiser back to the default denoiser for the final [00:06:53]. Night reads as blue outside, warm practicals inside [frame 00:08:30].                                          |

### 4d. Exterior

- Sun and sky when you need direction control, caustics or a photo-matched time; HDRI when a
  specific sky is wanted and no caustics (Arch Viz Artist, archviz digest: IuQ7QnwSwL0 00:02:19,
  00:08:05).
- HDRI with poor caustics: add a sun limited to the water, disable environment caustics, include
  only pool objects (IuQ7QnwSwL0 00:07:31 to 00:08:47).
- Lock the camera view before moving the sun; put the sun target at ground level (Aga, JmmgSQp6FYI
  00:01:15).
- After adding foliage the image darkens: fix with exposure and a tone curve, not light intensity
  (JmmgSQp6FYI 00:10:33). In an OCIO scene that means camera exposure, not a second tone mapper.

### 4e. Studio product (Corona on screen, valid for V-Ray; Aga, hPZvijDCV-M)

Uses `make_light` from 4a (keep both in the same chunk).

```python
# channel: batch | bridge | handoff
# checked against hPZvijDCV-M frames 5:04, 5:22, 9:12; light classes [verify]; elevations [added]
import math

SUBJECT = (0.0, 0.0, 50.0)    # subject center, cm
CAMERA = (0.0, -400.0, 60.0)  # 80 mm camera in the video (00:00:43)
fam = renderer_info()["family"]
area = {"vray": ["VRayLight"], "corona": ["CoronaLight"], "arnold": ["ArnoldLight"]}[fam]


def around(angle_deg, dist, height):
    vx, vy = CAMERA[0] - SUBJECT[0], CAMERA[1] - SUBJECT[1]
    base = math.atan2(vy, vx) + math.radians(angle_deg)
    return (SUBJECT[0] + dist * math.cos(base), SUBJECT[1] + dist * math.sin(base), SUBJECT[2] + height)


rig = {  # name: (angle from camera direction, distance, height, size cm, intensity, kelvin or None)
    "LGT_key": (90, 200, 120, 60, 60, None),     # warm via temperature, value not shown
    "LGT_fill": (-90, 250, 60, 100, 10, None),   # larger and weaker than key, cooler
    "LGT_rim": (170, 220, 160, 35, 200, 8000),   # invisible, backdrop excluded (00:08:55)
}
made = {}
for name, (ang, dist, h, size, inten, kelvin) in rig.items():
    res = make_light(area, name, around(ang, dist, h), aim_at=SUBJECT)
    made[name] = {k: v for k, v in res.items() if k != "node"}
    made[name]["target_values"] = {"size_cm": size, "intensity": inten, "kelvin": kelvin}
result = {"lights": made, "note": "set size, intensity, temperature, invisible and exclusion with set_props "
                                  "using the property names each dump shows; place the background fill by hand"}
```

Rules: key at about 90 degrees between light, subject and camera (00:02:10); fill larger and weaker
than key, about one sixth of key in the shown scene (60 against 10), and never casts its own shadow
(00:05:14); background fill neutral white, about 5 to 15, lights the backdrop evenly (00:06:13);
match the backdrop color to the product last (00:09:53). Gate: render each light alone, then
together: one shadow direction, rim card not visible.

### 4f. Several looks from one scene (day, low sun, dusk)

Goal: one scene, one camera, client choice between lighting conditions without rebuilding the
lighting.

1. Render once with every condition on: each sun, sky or HDRI environment in its own LightSelect
   (Corona) or light mix group (V-Ray). Corona LightMix supports multiple suns and environments and
   picks between them with no re-render (corona-lightmix.md, "Using LightMix with multiple suns and
   environments"); V-Ray: several dome HDRIs rendered once and picked in LightMix, at the cost of
   render time (Chaos, x8H1CNNFPgc 00:15:39).
2. Every light enabled, white and bright at render time; the mix only dims (4MeUNMFxiPE 00:05:16;
   vray7-vraylightmix.md).
3. Practicals (lamps) in their own groups so dusk can lift them relative to a dimmed sky.
4. Decide per look: if a look needs a channel raised above its render-time level, or camera exposure
   raised after the sun is dimmed, that is a brighten. Render that look as its own state instead
   [added, from the dim-only rule]. Reopen the saved scene between states; Reset settings wipes the
   frame buffer (_biqhqTpW5c 00:02:26).
5. Rotate each HDRI on Z only to match the window view (x8H1CNNFPgc 00:13:53).
6. Save each look as a LightMix preset (Corona config file, V-Ray .vfbl) and keep the layered file
   (CXR, EXR) for revisions; write the chosen mix back to the lights (section 6). Gate: each look
   from the mix passes the step 3 exposure gate and the noise gate on its darkest region; a look
   that fails noise there is rendered separately.

## 5. Exposure and white balance on the camera

```python
# channel: batch | bridge | handoff
# note: camera property names unknown, discovered here
cam = rt.getNodeByName("CAM_main")  # pass the shot camera name
result = {"camera_class": str(rt.classOf(cam)),
          "exposure_props": prop_dump(cam, ("exposure", "ev", "iso", "f_number", "fnumber", "shutter",
                                            "white", "balance", "vignet", "tilt", "clip"))}
```

Then: render once with renderer auto exposure (V-Ray needs light cache as secondary GI for it,
x8H1CNNFPgc 00:05:47), read the value in the frame buffer, round it and write it on the camera with
`set_props`; turn auto off. Gate: two test renders give the same `render_metrics.py exposure` median
within 0.02 [added].

## 6. Render elements and AOVs

```python
# channel: batch | bridge | handoff
# note: class names from vray7-vraylightmix.md, corona-lightmix.md and notes [verify]; AddRenderElement [verify]
APPLY = False
fam = renderer_info()["family"]
want = {"vray": ["VRayLightMix", "VRayCryptomatte"],
        "corona": ["CShading_LightMix"],
        "arnold": []}[fam]
added = [add_element(c, dry_run=not APPLY) for c in want]
crypto_like = [str(c) for c in getattr(rt.RenderElement, "classes", []) if "crypto" in str(c).lower()]  # [verify] RenderElement.classes
result = {"family": fam, "added": added, "existing": render_elements(), "crypto_classes": crypto_like}
```

Per renderer:

- V-Ray: `VRayLightMix` groups by instanced, individual, grouped, layers or manual light selects;
  maximum 254 lights then Rest; needs Consistent lighting elements; "To Scene" only after the render
  stops (vray7-vraylightmix.md). Add `VRayDenoiser` only if the final keeps it. Save layers through
  the V-Ray output, EXR or vrimg (vray7-vfb-frame-buffer.md).
- Corona: one `CShading_LightMix` enables the tab; one `CShading_LightSelect` per group; unassigned
  lights go to Rest and cannot be denoised or saved unless one LightSelect includes lights not
  assigned elsewhere; denoising must be on for every LightSelect to denoise the mix; CoronaLightMtl
  with Emit light off and self-illuminated materials cannot be selected (corona-lightmix.md). The
  Setup LightMix button does all of this in one step (Aga, _biqhqTpW5c 00:01:18). The include list
  property of a LightSelect is not documented: dump it with `prop_dump(el, ("light", "include"))`.
  Corona's equivalent of V-Ray "To Scene" is the LightMix tab button that bakes the current LightMix
  colors and intensities into the scene lights (corona-lightmix.md, Usage Workflow); it is a frame
  buffer button with no documented script call. Corona class and property names (`CoronaCamera`,
  `CoronaSun`, `CoronaSky`, `CoronaLight`, `CoronaColorCorrect`) come from a note, not a saved doc
  [verify]: confirm each with `hasattr(rt, name)` and `prop_dump` before use (JmmgSQp6FYI note).
- Arnold: light groups and AOVs (diffuse_direct, diffuse_indirect, specular_direct,
  specular_indirect, sss, transmission, cryptomatte) live in the Arnold AOV manager; no saved doc
  names a script API, so use the GUI path or a template scene. Cryptomatte instances share one mask
  by default in 5.9 (`object_split_instances` off). Gate: every light in a group or deliberately in
  Rest; output is EXR.

## 7. Noise triage

Render a 1/4-size test or crop around the problem; measure; change one cause at a time.

| Symptom, where                         | Arnold (docs: Removing Noise)                                           | V-Ray 7                               | Corona                                                               |
| -------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------- | -------------------------------------------------------------------- |
| Noise in alpha, DOF or motion blur     | raise Camera (AA), lower the others                                     | lower noise threshold                 | lower noise limit                                                    |
| Blotchy indirect light                 | Diffuse samples                                                         | noise threshold; light cache subdivs  | leave GI defaults; noise limit                                       |
| Soft shadow and direct highlight grain | Light samples 3 to 4; Indirect Light Samples if indirect AOVs are worse | noise threshold                       | light samples multiplier (default 2.0)                               |
| Blurry reflection grain                | Specular samples                                                        | noise threshold                       | noise limit                                                          |
| Frosted glass grain                    | Transmission samples                                                    | noise threshold                       | noise limit                                                          |
| Fireflies                              | clamp samples, light decay filter, raise roughness, bigger dimmer light | Max ray intensity (20 in 7Q3GqtJ56OQ) | Max Sample Intensity (default 20; 0 is unbiased, not for production) |
| Noise only after LightMix              | brighten lights, not groups                                             | same (x8H1CNNFPgc 00:09:41)           | same                                                                 |

Arnold zero test, measured:

```python
# channel: batch | bridge | handoff
# checked against lighting-rendering__arnold-removing-noise.md (zero test) and ZUEnTb6QnD4 note (property names [verify])
import os

OUT = os.path.join(str(rt.getDir(rt.Name("renderoutput"))), "triage")  # or a project path passed in
os.makedirs(OUT, exist_ok=True)
SIZE = (640, 360)
r = rt.renderers.current
assert renderer_info()["family"] == "arnold", "Arnold only"
runs = {"base": {}}
for concept in ("diffuse_samples", "specular_samples", "transmission_samples", "sss_samples"):
    name = resolve(r, concept)
    if name:
        runs[concept + "_0"] = {name: 0}
report = {}
for label, change in runs.items():
    before = {k: getattr(r, k) for k in change}
    for k, v in change.items():
        setattr(r, k, v)
    try:
        path = os.path.join(OUT, f"triage_{label}_v001.png")
        report[label] = test_render(path, size=SIZE)
    finally:
        for k, v in before.items():
            setattr(r, k, v)   # restore even if the render fails
result = report
```

Runner side: `python render_metrics.py noise triage_<label>_v001.png` for each file. The ray type
whose zeroed render drops sigma the most is the cause; raise that sample count by 1 or 2 and test
again. Total rays per pixel for a type = AA squared times that sample squared (ZUEnTb6QnD4 frame
00:18:02): log it with the timing.

V-Ray and Corona: there is no per-ray-type sample count to zero. Lower the noise threshold or noise
limit one step, compare sigma and seconds, and stop when the gain per minute drops. Leave V-Ray
quality below High Plus (Educk, 3IZ44a70BPw 00:03:25). Compare CPU, GPU CUDA and GPU RTX on your own
scene rather than assuming (3IZ44a70BPw 00:01:18).

## 8. Estimate, then final

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-renderer-2027.md (render outputFile, outputSize)
import os

OUT = os.path.join(str(rt.getDir(rt.Name("renderoutput"))), "estimate")  # or a project path passed in
os.makedirs(OUT, exist_ok=True)
out = output_settings()
w, h = out["width"] // 4, out["height"] // 4
t = test_render(os.path.join(OUT, "estimate_q_v001.png"), size=(w, h))
r = rt.renderers.current
result = {"test": t, "final_size": [out["width"], out["height"]],
          "stop_criterion": prop_dump(r, ("noise", "limit", "threshold", "time"))}
```

Runner side:

```python
# channel: runner side
# note: standard scaling [added]
from render_metrics import estimate, noise

test = noise("estimate_q_v001.png")["sigma"]
plan = estimate(seconds=95.0, test_px=1250 * 833, final_px=5000 * 3333, frames=1,
                noise_now=test, noise_target=test * 0.8, machines=1)
print(plan)  # compare plan["hours_total"] with the budget before launching
```

Caveat: noise limits and thresholds are adaptive, so a test at the same limit scales roughly with
pixels; a progressive render with a time limit costs exactly its limit [added].

Over budget, in this order:

1. Render big and downscale (Chaos, 1bOmROFahXU): output 2x the target, Corona noise limit 20 to 30
   percent, denoise Intel CPU/GPU AI, amount 0.85, image filter Tent (High Quality does not work
   with the AI denoiser), then save at 50 percent. Script substitute for the frame buffer button:
   `python render_metrics.py downscale big.png final.png 0.5` or
   `magick big.exr -resize 50% final.exr`. Gate: `detail_ratio` on wall and reflection crops against
   a short low-noise crop at least 0.85 [added]; if lower, take the noise limit to about 15 percent.
2. Raise the noise limit and keep the denoiser; a V-Ray Bucket final at 0.005 may not need the
   denoiser at all (x8H1CNNFPgc 00:08:39).
3. A time limit as a safety net (Arnold Frame Time Limit; progressive in V-Ray and Corona).
4. Farm: report the estimate and the farm's own cost calculator inputs (frames, minutes per frame,
   CPU or GPU, renderer), as shown at 7Q3GqtJ56OQ 00:03:38. Memory for large finals and the 2x
   method: the sources give no RAM figure for a given size. At 2x the pixel count is 4x, so every
   frame buffer and render element grows 4x [added arithmetic]; a 5,000 px still rendered at 10,000
   px carries that cost for each element. Find the peak by test: start the full 2x frame with the
   final elements on and a short time limit, and read peak memory in the renderer's statistics or
   the OS monitor [added method]. If peak approaches installed RAM, in Corona
   (corona-performance-tab.md): Conserve memory (up to 30 percent lower peak, slower), Automated
   out-of-core textures, and displacement by Screen size (px) rather than World size. Drop elements
   the compositor did not ask for.

Final: a new versioned file; save the renderer's layered file too (V-Ray EXR or vrimg through V-Ray
output; Corona CXR). Corona: untick "Clear VFB between renders" before stopping a render you want to
resume (_biqhqTpW5c 00:13:34). V-Ray: aborting skips the denoiser, soft stop applies it
(vray7-vfb-frame-buffer.md).

## 9. Animation

- GI: any moving object besides the camera, use brute force with Bucket (V-Ray) or the Corona UHD
  Cache "Animation (flicker-free)" preset; camera-only, V-Ray can pre-compute (Aga, 7Q3GqtJ56OQ
  00:00:39, 00:03:55).
- V-Ray two-pass fly-through: pass A "Don't render final image" on, irradiance map Multiframe
  incremental, light cache Animation mode, auto save both, every 25th frame for exteriors or every
  5th to 10th inside; pass B both From file, every frame, "Don't render final image" off (00:04:13
  to 00:06:48). Irradiance map is deprecated in V-Ray 7: prefer brute force plus light cache unless
  the time saving is measured.
- Lock the noise pattern for Corona and for any per-frame post denoise; Corona keeps it on
  (corona-performance-tab.md) [deciding condition added].
- Corona and archviz animation: noise limit 3 to 4 percent, not a pass count (archviz digest,
  ZHCVMQeWPEg 00:08:07).

```python
# channel: batch | bridge | handoff
# note: frame keyword of render() [verify]
import os

OUT = os.path.join(str(rt.getDir(rt.Name("renderoutput"))), "flicker")  # or a project path passed in
os.makedirs(OUT, exist_ok=True)
START, COUNT = 100, 10
cam = rt.getNodeByName("CAM_shot")
done = []
for f in range(START, START + COUNT):
    path = os.path.join(OUT, f"flicker_{f:04d}_v001.png")
    if os.path.exists(path):
        raise FileExistsError(path)
    rt.render(camera=cam, frame=f, outputFile=path, vfb=False,  # [verify] frame keyword
              outputSize=rt.Point2(640, 360))
    done.append(path)
result = {"frames": done}
```

Runner side: `python render_metrics.py flicker flicker_*_v001.png`. Gate: `jumps` empty; then play
the frames and look at walls and ceilings for crawling blotches.

## 10. Post outside 3ds Max

LightMix rebuild from separate light layers (EXR, linear): the beauty equals the sum of light-select
layers; the mix is a weighted sum, additive like Photoshop Linear Dodge (Add) (corona-lightmix.md).

```python
# channel: runner side
# note: additive rule from corona-lightmix.md
import numpy as np


def light_mix(layers, weights):
    """layers: {name: HxWx3 linear float}; weights: {name: float or (r, g, b)}. Dim, do not boost."""
    out = None
    for name, img in layers.items():
        w = np.asarray(weights.get(name, 1.0), dtype=np.float32)
        out = img * w if out is None else out + img * w
    return out
```

Cryptomatte matte from an EXR (Corona `.cxr` files are EXR: rename to open them, Jlxe5d1_bFg
00:01:26). Hash rule from the public Cryptomatte specification [added]:

```python
# channel: runner side
# checked against the Cryptomatte specification (github.com/Psyop/Cryptomatte) [added]
import struct

import mmh3
import numpy as np


def name_to_id(name):
    h = mmh3.hash(name, signed=False)
    exp = (h >> 23) & 255
    if exp in (0, 255):
        h ^= 1 << 23
    return struct.unpack("<f", struct.pack("<L", h))[0]


def matte(rank_channels, names):
    """rank_channels: list of (id_array, coverage_array) pairs read from <type>00..NN RGBA."""
    ids = [name_to_id(n) for n in names]
    out = None
    for id_arr, cov in rank_channels:
        hit = np.isin(id_arr, np.asarray(ids, dtype=np.float32))
        part = np.where(hit, cov, 0.0)
        out = part if out is None else out + part
    return np.clip(out, 0.0, 1.0)
```

Cryptomatte beats object ID masks only where edges are blurred (DOF, motion blur); otherwise ID
masks suffice (Jlxe5d1_bFg 00:12:28). A Cryptomatte matte is the mask to send with a render to an
image edit or relight through scenario-3dsmax-generation.
