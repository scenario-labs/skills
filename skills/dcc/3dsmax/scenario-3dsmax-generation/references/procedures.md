# Procedures: generation to 3ds Max and back

Each code block names its channels and the source it was checked against. Names marked `[verify]`
are not in the saved Autodesk docs: confirm them with `showProperties`, the MacroRecorder or a
one-line test before relying on them.

Conventions:

- Runner-side code is plain Python next to the agent and never imports pymxs
  (`scripts/gen_runner.py`).
- In-Max chunks set `result` and run inside the lead's `max_wrap.wrap(...)`, which adds the undo
  record, the result file and the inlined kit modules (`capture`, `xio`, `stats`, and this skill's
  `scripts/maxkit_generation.py`). Module names inside the chunk follow that inlining.
- Arguments reach a chunk through an `ARGS` JSON literal that the runner substitutes with
  `repr(json.dumps(args))`, which keeps Windows backslashes. MAXScript for `mcp-safe` takes them
  from placeholder lines at the top that the agent fills before proposing the script.
- Files are written under the project folder on the machine that runs 3ds Max. Nothing is
  overwritten: new names get `_v002`.

Contents:

1. P1 Inputs from 3ds Max (captures and renders for a generator)
2. P2 Generate through the Scenario MCP (call sequence)
3. P3 Download, file layout and provenance sidecar
4. P4 Land a generated 3D model
5. P5 Land a PBR texture set (checks, then handoff)
6. P6 Land a skybox or HDRI (checks, then handoff)
7. P7 Land a Gaussian splat world
8. P8 Viewport or render to image edit, and back
9. P9 Viewport or render to video
10. P10 Report

---

## P1 Inputs from 3ds Max

Goal: give the generator the scene's own structure: a clay or beauty render from the locked camera
at the deliverable's aspect, plus views of an object for multi-view 3D, plus masks where the
renderer provides them.

Scene prep before any capture for an AI pass (VizAcademy UK, zARHVN_XN4U 00:24:34, 00:28:47,
00:31:19; ai-workflows batch1 #3, #4):

- Proxies, limiters and hidden-for-render helpers confuse the model: show full geometry, hide
  helpers.
- Window glass off (hidden or opacity off) and edged faces off in the viewport.
- Furniture chamfered: sharp, unbeveled edges read as flat cards.
- The control kit is a white clay render plus a wire-color or masking element (Corona CMasking
  WireColor, V-Ray VRayEnhancerData, Arnold Cryptomatte), saved as EXR with the beauty.
  `scenario-3dsmax-lighting-rendering` adds the elements; the scripted render element calls in the
  notes are [verify].
- Save the prepared state as a new scene version (`_ai_prep_v001`); never edit the production scene
  in place.

```python
# channel: batch (render only), bridge, handoff
# checked against scripting-pipeline__pymxs-renderer-2027.md and the lead's capture contract
import json, os
ARGS = json.loads(__ARGS__)  # {"out_dir": ..., "camera": "CAM_Hero", "size": [2048, 1152], "views": true}
os.makedirs(ARGS["out_dir"], exist_ok=True)
files = []
beauty = os.path.join(ARGS["out_dir"], "source_render.png")
if not os.path.exists(beauty):
    files.append(capture.render(beauty, camera=ARGS.get("camera"), size=ARGS.get("size")))
if ARGS.get("views"):
    files += capture.views(os.path.join(ARGS["out_dir"], "views"))  # bridge and handoff only: needs a viewport
result = {"files": files, "renderer": str(rt.renderers.current)}
```

MAXScript twin for `mcp-safe` (whether bitmap saves and `render outputFile:` pass Safe Scene Script
Execution is not documented: run it once on a test path first).

```maxscript
-- channel: mcp-safe, bridge, handoff
-- checked against scripting-pipeline__maxscript-viewport-drawing-methods-getviewportdib-2027.md, scripting-pipeline__maxscript-bitmap-values-2027.md
outPath = @"__OUT_DIR__\viewport_capture.png"   -- filled by the agent; must not exist yet
camName = "__CAMERA__"
if doesFileExist outPath then throw "target exists: pick a new name"
dib = gw.getViewportDib captureAlpha:false gammaCorrect:true
dib.filename = outPath
save dib
close dib
cam = getNodeByName camName                     -- [verify] getNodeByName
if cam != undefined do
    render camera:cam outputFile:(@"__OUT_DIR__\source_render.png") vfb:false   -- [verify] vfb keyword
```

Check: open each file, confirm size and aspect equal the render output aspect, and look at it. A
viewport grab in the first seconds after launch can come back at the wrong shading level (max-mcp
README, file 01 s8): capture again if it looks flat.

Masks: Cryptomatte, wire color, Material ID or VRayEnhancerData elements come from
`scenario-3dsmax-lighting-rendering`. Ask it for an EXR with the beauty plus ID passes when the edit
must be masked.

---

## P2 Generate through the Scenario MCP

No generation code: the Scenario skills own this. The call sequence, per the `scenario` skill:

1. Load `scenario` once per session, then the skill for the asset type (table in SKILL.md).
2. Resolve scope: `teams_list`, then `projects_list`; pass `team_id` and `project_id` on every call.
3. Upload 3ds Max inputs: `upload_asset` (`kind` image, video or 3d), then `upload_asset_complete`
   for multipart.
4. `recommend` with the user's own words and quality priority. Read `next_step.type`; prefer
   `specialty.model_id`, else the top ranked entry. Run `search` sorted newest first when the type
   is new to the project.
5. `model_schema_get` on the pick. For 3D, prefer a model whose schema has `outputFormat`, and
   request the format from `gen_runner.model_format(release)`.
6. `model_run` with `dry_run: true` for batches, then `model_run` with `wait: false`. Explore first:
   the lowest useful size (1K for images, a draft tier for worlds), several outputs per prompt, a
   new seed per run (2WmOd4C5r7s 00:06:38; i3UbOzrAgLk 00:03:33). When a take is liked, read its
   seed and pass the same `seed` (where the schema has one) for every variant and for the
   high-resolution run (zARHVN_XN4U 00:14:15; D-1Vy864PtQ 00:05:42). Record it in the sidecar. A
   schema without a seed field cannot reproduce a take: say so in the report.
7. `jobs_wait` with the job ids; on timeout re-call with `pending_job_ids`. Never a second
   `model_run` for a timeout.
8. `asset_display` and look at the result before downloading. Reject it here if the subject, anatomy
   or seam is wrong.
9. `asset_download` returns a URL; P3 saves it.

---

## P3 Download, file layout and provenance sidecar

```python
# channel: runner side (feeds batch, mcp-safe, bridge, handoff)
# checked against scripts/gen_runner.py and the scenario skill (asset_download)
import sys
sys.path.insert(0, "__SKILL_DIR__/scripts")    # this skill's scripts folder
import gen_runner as g

folder = g.asset_dir("__PROJECT_ROOT__", kind="props", name="planter_01")
path = g.download("__DOWNLOAD_URL__", folder, "planter_01.fbx")
side = g.write_sidecar(path, {
    "model_id": "__MODEL_ID__", "model_name": "__MODEL_NAME__",
    "prompt": "__PROMPT__", "seed": None, "reference_asset_ids": [],
    "job_id": "__JOB_ID__", "asset_id": "__ASSET_ID__",
    "output_format": "fbx", "scenario_skill": "scenario-3d",
})
print(path, side)
```

Where the file must end up, per channel:

- `batch`, `bridge`: the runner downloads onto the 3ds Max machine or a share it reads. Keep
  downloads out of 3ds Max's main thread.
- `mcp-safe`: the Autodesk 3ds Max MCP server has no download tool and blocks .NET; the agent's own
  shell downloads, on the same machine.
- `handoff`: the user downloads, or the runner writes the files and the script, and the user runs
  it.

Keep the untouched download. Converted or cleaned versions are new files beside it.

---

## P4 Land a generated 3D model

Goal: one root per asset at the right real size, base on the floor, named, on a layer, with
provenance, and a report the agent can judge.

Before importing a GLB in 2027.3, the Khronos glTF importer dialog decides the material class:
Scanline, Physical, PBR, glTF, Arnold, USD or OpenPBR Mtl (scripting-pipeline__gltf-import-2027.md).
The importFile doc says `#noPrompt` uses "the default configuration". No saved doc says whether that
default follows the last dialog choice, and no saved doc gives scripted importer option names
[verify]. So:

1. Import the first GLB through the dialog with the type the scene needs (OpenPBR Mtl for an Arnold
   or OpenPBR scene). On the `handoff` channel the user does this step.
2. Import the second with `#noPrompt` and read `materials` in the report. If the classes match,
   batch the rest; if not, keep importing through the dialog, or convert after import.
3. V-Ray or Corona scene: the dialog has no VRayMtl or Corona type. Import as Physical Mtl and hand
   the material list to `scenario-3dsmax-materials`, which converts with Scene Converter
   (materials-lookdev__scene-converter-2027.md). FBX on any release avoids the glTF question; its
   materials still go through the same conversion.

Passing arguments to a batch MAXScript instead of substituting text:
`3dsmaxbatch script.ms -mxsString path:"..." -mxsValue knownSize:0.85`, read inside with
`maxOps.mxsCmdLineArgs` (a dictionary of DataPairs; `rt.maxops.mxsCmdLineArgs` from pymxs). Source:
scripting-pipeline__3dsmaxbatch-2020.md; the option list is not re-confirmed on a 2027 page (version
deltas).

```maxscript
-- channel: batch
-- checked against scripting-pipeline__3dsmaxbatch-2020.md (mxsCmdLineArgs example)
opts = maxOps.mxsCmdLineArgs
inPath = opts[#path]                 -- dictionary key access as in the doc's loop over opts.keys
if inPath == undefined then throw "missing -mxsString path:"
ok = importFile inPath #noPrompt
format "imported:% path:%\n" ok inPath
```

```python
# channel: batch, bridge, handoff
# checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md and scripts/maxkit_generation.py
import json
import os
ARGS = json.loads(__ARGS__)
# {"path": ".../planter_01.fbx", "name": "planter_01", "layer": "GEN_props",
#  "known_axis": 2, "known_size_m": 0.85, "place_at": [0, 0, 0], "record": {...sidecar fields...},
#  "save_as": ".../scene_v002.max"}  (batch: the session ends with the run, so save under a new name)
report = maxkit_generation.land_model(
    ARGS["path"], ARGS["name"], layer=ARGS.get("layer", "GEN_props"),
    known_axis=ARGS.get("known_axis", 2), known_size_m=ARGS.get("known_size_m"),
    place_at=ARGS.get("place_at"), record=ARGS.get("record"))
report["renderer"] = str(rt.renderers.current)
if ARGS.get("save_as"):
    if os.path.exists(ARGS["save_as"]):
        raise FileExistsError(ARGS["save_as"])  # never over an existing scene
    rt.saveMaxFile(ARGS["save_as"], quiet=True)  # [verify] quiet: keyword
    report["saved_scene"] = ARGS["save_as"]
result = report
```

Runner side, building and running it:

```python
# channel: runner side
# checked against the lead's max_wrap and max_batch contract
import json
from max_wrap import wrap
from max_batch import run_batch

args = {"path": "__PATH__", "name": "planter_01", "known_size_m": 0.85, "record": {"model_name": "__MODEL_NAME__"},
        "save_as": "__NEW_SCENE__.max"}  # a new name such as <scene>_v002.max; an existing file stops the chunk
chunk = open("__CHUNK_FILE__", encoding="utf-8").read().replace("__ARGS__", repr(json.dumps(args)))
script = wrap(chunk, lang="python", kit=["maxkit_generation"], kit_dirs=["__GENERATION_SCRIPTS__"],
              result_path="__RESULT_JSON__")  # kit_dirs: this skill's scripts/ folder
res = run_batch(script, scene="__SCENE__.max", args={"result_path": "__RESULT_JSON__"}, require_result=True)
print(res)  # res["result"]["result"]["saved_scene"] is the landed scene
```

MAXScript twin for `mcp-safe` (import only; scale and layer stay simple to keep the script readable
for the user who approves it):

```maxscript
-- channel: mcp-safe, bridge, handoff
-- checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md
inPath  = @"__PATH__"          -- filled by the agent
assetName = "__NAME__"
knownSizeSys = __KNOWN_SIZE_SYS__  -- real height in system units, or 0 to skip scaling
before = for o in objects collect o
ok = importFile inPath #noPrompt
if not ok then throw ("import failed: " + inPath)
newNodes = for o in objects where findItem before o == 0 collect o
lo = newNodes[1].min; hi = newNodes[1].max
for n in newNodes do (
    lo = [amin lo.x n.min.x, amin lo.y n.min.y, amin lo.z n.min.z]   -- [verify] amin
    hi = [amax hi.x n.max.x, amax hi.y n.max.y, amax hi.z n.max.z]   -- [verify] amax
)
undo "Land generated asset" on (
    root = Dummy name:("GEN_" + assetName + "_root") pos:[(lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z]   -- [verify] Dummy
    for n in newNodes where n.parent == undefined or findItem newNodes n.parent == 0 do n.parent = root
    if knownSizeSys > 0 do (
        f = knownSizeSys / (hi.z - lo.z)
        root.scale = [f, f, f]
    )
    root.pos = [0, 0, 0]
    lay = LayerManager.getLayerFromName "GEN_props"                   -- [verify]
    if lay == undefined do lay = LayerManager.newLayerFromName "GEN_props"   -- [verify]
    lay.addNode root                                                   -- [verify]
    for n in newNodes do lay.addNode n
)
format "nodes:% height_before:% \n" newNodes.count (hi.z - lo.z)
```

Checks on the report (numbers in critique.md):

- `scale_factor` near 10, 100, 1000, 2.54 or 30.48 (or their inverses) points to a unit mismatch
  between file and scene [added]; any other large factor means the generator's size or the known
  dimension is wrong: check both before accepting.
- `size_after` on the other two axes is plausible for the object (a chair 0.85 m high that is 3 m
  wide is a wrong axis or a wrong model).
- `base_z_after` equals the floor height.
- `faces_total` within the budget set before generation; over it goes to
  `scenario-3dsmax-game-assets` (LOD, retopology) or `scenario-3dsmax-modeling` (quad rebuild).
- `materials`: class per material. Conversion to the scene renderer goes to
  `scenario-3dsmax-materials` with this list.
- Then capture: `capture.views` of the root and a render from the scene camera; look at scale
  against neighbors, floating, flipped normals, missing textures.
- UVs: AI UVs are the weakest part of a generated mesh (Top 3D AI, O6G6taj5M14 00:12:46). Put a
  checker on map channel 1 and capture it; stretched or smeared checks go to
  `scenario-3dsmax-uv-baking` (unwrap, pack) or to the Scenario UV unwrap step (`scenario-3d`).
- After any mesh rework (remesh, retopology, decimation, part fixes), the old texture no longer
  fits: regenerate it on the new UVs from the original input images, or rebake from the original
  mesh (O6G6taj5M14 00:20:13, 00:20:45). Keep the original download and its inputs for this.

---

## P5 Land a PBR texture set

Runner-side checks first:

```python
# channel: runner side
# status: checked against scripts/gen_runner.py; the 2 x 2 sheet follows the scenario-textures skill
import sys
sys.path.insert(0, "__SKILL_DIR__/scripts")
import gen_runner as g
for m in ("__BASECOLOR__", "__NORMAL__", "__ROUGHNESS__", "__HEIGHT__"):
    print(g.tile_sheet(m, m.rsplit(".", 1)[0] + "_tile2x2.png"))
```

Look at each sheet for seams and repeating blobs. Texture prompts stay short, with prompt rewriting
off where the schema allows; height maps ask for "medium contrast" (Nuno Silva, i3UbOzrAgLk
00:02:27, 00:08:36).

Seam repair (i3UbOzrAgLk 00:05:01, 00:06:05): offset the map by half its size so the seams form a
cross in the middle, then fix only the cross. Make the offset and a cross mask locally, send both to
a masked edit (`scenario-image`) or a seam-erase model (`scenario-textures`), and offset back. Apply
the same offset to every map of the set so channels stay aligned.

```python
# channel: runner side
# status: checked against Pillow's ImageChops.offset and ImageDraw; the method follows i3UbOzrAgLk 00:05:01, 00:06:05
from PIL import Image, ImageChops, ImageDraw
src = Image.open("__MAP__")
w, h = src.size
shifted = ImageChops.offset(src, w // 2, h // 2)      # seams now cross at the center
shifted.save("__MAP_OFFSET__")                        # new file, never the source
band = max(8, w // 32)                                 # band width is [added]: widen if the seam is soft
mask = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(mask)
d.rectangle([w // 2 - band, 0, w // 2 + band, h], fill=255)
d.rectangle([0, h // 2 - band, w, h // 2 + band], fill=255)
mask.save("__CROSS_MASK__")
# after the masked edit: ImageChops.offset(fixed, -(w // 2), -(h // 2)) restores the original placement
```

Then hand off to `scenario-3dsmax-materials` with:

- the file per channel and its role: base color sRGB; normal, roughness, metalness, height, AO Raw
  (linear, gamma 1.0);
- the provenance of each map: generated by the model, derived locally, or calibrated (label derived
  maps as approximations, per `scenario-textures`);
- the real-world size of one tile (from the reference or the brief);
- the target material class (OpenPBR for Arnold, VRayMtl or Corona Physical when the scene uses
  those renderers).

Gate after the material exists: a plane test render with a 3 x 3 tile at the real-world size, and
the object render beside the reference.

---

## P6 Land a skybox or HDRI

From a site photo: upload the photo with `upload_asset` and ask `recommend` for an image-to-skybox
model (the catalog listed one on 2026-11-24; `scenario-skyboxes` covers the route). Record the
photo's horizon height and sun azimuth before generating, and check them on the result [added].
Generated context around the photo is invented: use it as background, never as site documentation.

```python
# channel: runner side
# status: checked against scripts/gen_runner.py and the scenario-skyboxes skill (column comparison)
import sys
sys.path.insert(0, "__SKILL_DIR__/scripts")
import gen_runner as g
r = g.seam_ratio("__SKY_PNG__")
print("seam ratio", round(r, 3), "OK" if r < 0.3 else "LOOK AT THE SEAM")   # 0.3 is [added]
```

Then decide the role and hand off to `scenario-3dsmax-lighting-rendering`:

- Background and reflections only: the 2:1 PNG or JPG on spherical environment mapping; keep the
  physical sun or Sun and Sky for direction and intensity.
- Light source: only the `.exr` or `.hdr` from the skybox-to-HDRI conversion model. Whether its
  values go above 1.0 is not confirmed: test by rendering a gray sphere with the environment alone
  and compare shadow contrast with a library HDRI.
- Give: file, role, horizon height, sun azimuth to align (from the site photo or the brief), and
  which renderer.

Gate: a render looking across the 0 and 360 degree meridian shows no seam; shadow direction in 3ds
Max matches the photo.

---

## P7 Land a Gaussian splat world

Needs 3ds Max 2027.2 or later. Arnold renders the native Gaussian Splat object. One expert says
V-Ray and Corona do not render it yet (YB330UhrdOA 01:08); V-Ray 7 and Corona 14 ship their own
splat support, so in those scenes ask `scenario-3dsmax-lighting-rendering` which loader to use.

```python
# channel: batch, bridge, handoff
# checked against scripting-pipeline__maxscript-whats-new-2027.md (SPZImport, PLYImport) and fundamentals-scene__gaussian-splat-3dgs-in-3ds-max-2027.md
import json
ARGS = json.loads(__ARGS__)   # {"path": ".../world.spz", "name": "site_context", "record": {...}}
rep = maxkit_generation.land_splat(ARGS["path"], ARGS["name"], record=ARGS.get("record"))
rep["renderer"] = str(rt.renderers.current)
rep["arnold"] = "arnold" in rep["renderer"].lower()
result = rep
```

```maxscript
-- channel: mcp-safe, bridge, handoff
-- checked against scripting-pipeline__maxscript-file-loading-saving-importfile-exportfile-2027.md
inPath = @"__PATH__"
before = for o in objects collect o
ok = importFile inPath #noPrompt
newNodes = for o in objects where findItem before o == 0 collect o
for n in newNodes do format "% % min:% max:%\n" n.name (classOf n) n.min n.max
```

After import, in the Modify panel: Preset (for PLY: Generic, Postshot, Substance 3D or WorldLabs)
sets the up axis; Up Axis and Units fix rotation and size without reimporting; Display Shader
(2027.3) shows splats closer to the render. Scripted names for these parameters are not in the saved
docs [verify]. Gate: extent matches a known dimension of the place (door, road width, room height)
within the tolerance in critique.md, and a capture shows the ground level and horizontal.

---

## P8 Viewport or render to image edit, and back

Goal: an edited image that keeps the 3ds Max geometry, reviewed beside its source, with protected
regions restored from the render.

Sort each requested variant before generating anything:

- Time of day, sun direction, exposure, artificial light on or off: a lighting state in 3ds Max,
  re-rendered from the same camera by `scenario-3dsmax-lighting-rendering` (elm00WQ03vw 00:04:05).
  An image edit cannot move shadows correctly.
- Season, weather and atmosphere (snow, fog, rain, foliage color), context and entourage: an image
  edit on the render of the matching lighting state (2WmOd4C5r7s 00:01:37). For a dusk or night
  season variant, re-render the lighting first, then edit.
- Geometry or a specified material changes: change the scene and re-render; an edit only previews it
  for the client (c3acjyR7j7E 00:07:13).

Regions to protect: architecture, products, signage, and every region where enhancement fails:
glass, fabric, fog, foggy brick. Pavement and ground surfaces respond best (Arch Viz Artist,
y2-zbS5n8Ps 00:05:07, 00:06:00, 00:06:31). Put the failing regions in the protect mask from the
start.

1. P1: render the locked camera at the deliverable aspect, plus an ID or mask pass for what must not
   change (architecture, glass, products, signage).
2. Upload the render (and a reference image) with `upload_asset`.
3. Edit through `scenario-image` (prompt edits, masked inpainting) or `scenario-image-editing`
   (upscale, grade, expand). Prompt states what changes and that geometry, openings, materials named
   in the brief and camera do not.
4. Download with P3, then restore protected regions and compare:

```python
# channel: runner side
# status: checked against Pillow's Image.composite; the review calls follow the lead's max_review contract
from PIL import Image
src = Image.open("__SOURCE_RENDER__").convert("RGB")
ai = Image.open("__EDITED__").convert("RGB").resize(src.size, Image.LANCZOS)
protect = Image.open("__PROTECT_MASK__").convert("L").resize(src.size)   # white = keep the render
out = Image.composite(src, ai, protect)
out_path = "__OUT__"                                                      # new file, never the source
out.save(out_path)
from max_review import compare, contact_sheet
print(compare("__SOURCE_RENDER__", out_path))
contact_sheet(["__SOURCE_RENDER__", "__EDITED__", out_path], "__SHEET__")
```

5. Look at the sheet at full size: building edges, window counts, mullions, signage, people anatomy,
   glass. Reject and regenerate rather than paint over drift.

Detail crops instead of one full-frame edit (elm00WQ03vw 00:02:09, 00:06:02, 00:08:33; zARHVN_XN4U
00:53:21):

- Image models have a pixel ceiling (one expert's model held to about 2 MP, artifact-free near 1.5
  MP). Read the current model's limit from its schema; do not send a 4K frame whole.
- Cut the regions that need work (entrance, people, planting) at one common aspect (4:3 in the
  source), edit each crop, scale it back to its exact pixel box and paste it.
- Scaling by total pixel count shifts the image slightly: repair the shift with small local
  inpaints, not a new full-frame run.

4K delivery [added, from the rules above]:

1. Render the base at the final 4K size in 3ds Max (`scenario-3dsmax-lighting-rendering`); the
   render carries the true detail.
2. Edit at the model's working size (whole frame for mood, crops for detail).
3. Upscale only the AI layer back to 4K, through `scenario-image-editing` with the model `recommend`
   returns. An upscaler adds pixels, not detail (j2qd-kLQY1Q 00:09:30).
4. Composite: protected regions and every pixel the edit did not need come from the 4K render (the
   composite block above).
5. Check 100 percent crops of mullions, signage and people beside the same crops of the render.

What stays manual: the art direction choice between variants, painting a mask where no ID pass
exists, final retouch, client sign-off.

---

## P9 Viewport or render to video

Two routes, in order of geometric fidelity:

A. Animated 3ds Max camera to video-to-video restyle. Render a short sequence from the scene,
assemble it, send it as the reference video.

```python
# channel: batch, bridge, handoff
# checked against scripting-pipeline__pymxs-renderer-2027.md (render, outputFile)
import json, os
ARGS = json.loads(__ARGS__)   # {"camera": "CAM_Walk", "start": 0, "end": 143, "out_dir": ...}
cam = rt.getNodeByName(ARGS["camera"])          # [verify] getNodeByName
os.makedirs(ARGS["out_dir"], exist_ok=True)
done = []
for f in range(ARGS["start"], ARGS["end"] + 1):
    out = os.path.join(ARGS["out_dir"], f"frame_{f:04d}.png")
    if os.path.exists(out):
        continue
    rt.render(camera=cam, frame=f, outputFile=out, vfb=False)   # [verify] frame and vfb keywords
    done.append(out)
result = {"frames": len(done), "renderer": str(rt.renderers.current)}
```

Runner side:
`ffmpeg -framerate 24 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 walk_v001.mp4`
[added]. Respect the video model's input limits from its schema (for example one 3D-to-video model
takes up to 15 s and 50 MB; another video model's edit mode takes reference videos of 2 to 30 s). A
scripted playblast (Make Preview) is not documented: a low-sample render is the scripted route.

B. Still to video from the approved image: start frame only for a camera move; start and end frames
for a transformation (season, furnishing). Render both frames from the same camera with identical
resolution and settings; only the change differs. Each transition is its own generation: four
seasons are four start and end pairs, because one multi-shot run for a four-way season change gave
"pure slop" (renderdrop, 1A7uOdk9Sng 00:02:00, 00:05:15). For day to night, the two frames are two
lighting states rendered in 3ds Max, not one render and one image edit.

People and entourage: add them to the start frame with an image edit before animating, and name the
character as a reference element where the video model's schema allows, so it stays the same person
(1A7uOdk9Sng 00:07:26). Keep people at mid distance: hands and body-to-furniture contact are the
weak points (00:09:05). Some models insert a cut on their own: reject those takes.

Review: contact sheet of about 12 frames per take, then the full clip. Reject takes where walls
bend, windows change count, floors slide, people morph or a cut appears. What stays manual: take
selection, the edit, sound.

---

## P10 Report

End every landing with:

- files: source download, converted files, sidecar, scene saved as `_v002`;
- numbers: scale factor, final size, faces, material classes, seam ratio, splat extent;
- captures looked at, and what was seen;
- handoffs made and their inputs;
- assumptions (missing dimensions, unconfirmed formats) as a list.
