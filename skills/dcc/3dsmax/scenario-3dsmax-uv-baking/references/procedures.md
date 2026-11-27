# Procedures: UVs, mapping and baking

Every block is a chunk for the scenario-3dsmax-expert toolkit. Run
`max_check.check(code=..., lang=..., channel=...)` before sending anything.

**Running a chunk.**

- Python chunks: `max_wrap.wrap(code, lang="python", kit=[...], result_path=...)`. The wrapper
  accepts only the lead's kit names (`result`, `stats`, `capture`, `audit`, `xio`), bound as
  globals. This skill's helper is not a kit name: prepend its source and the arguments to the chunk
  yourself:
  `code = Path("scripts/maxkit_uv.py").read_text() + "\nARGS = " + repr(args) + "\n" + chunk`.
  `uv_audit` and the other helpers are then plain globals. `ARGS` is always a dict literal you write
  in.
- MAXScript chunks: `max_wrap.wrap(code, lang="maxscript")`, which is also the form to propose on
  `mcp-safe`. The chunk must set `result`. Prepend `scripts/mxs/maxkit_uv.ms` when a block calls
  `uvk_*` functions. Arguments are literals written into the chunk.
- The wrapper already puts the chunk in one undo record; the inner `pymxs.undo` or `undo on` blocks
  only label the step.

Names marked `[verify]` were not found in the saved 3ds Max docs. Run P0 once per session to confirm
them, and replace the block with a GUI step if a name is missing.

Contents:

- P0 Discover the scripted interfaces
- P1 UV audit
- P2 Checker capture without losing materials
- P3 Scripted unwrap fallback (Flatten and Pack)
- P4 Lightmap UVs on channel 2
- P5 Real-world mapping for archviz surfaces
- P6 Bake procedural or layered materials to a PBR set (Self projection)
- P7 High to low: normal, AO and curvature with a diagnostic pass
- P8 Legacy Render to Texture bake for batch
- P9 Read the baked maps
- P10 Randomizers and triplanar (V-Ray 7, Corona)
- P11 Substance Painter hand-off
- P12 Fixing what the bake shows

---

## P0 Discover the scripted interfaces

Use this before P3, P4, P7 and P10. It prints what the running build exposes, so later blocks use
real names.

```maxscript
-- channel: mcp-safe | handoff | bridge | batch
-- checked against scripting-pipeline__pymxs-using-2027.md (getPropNames) and scripting-pipeline__maxscript-python-interop-2027.md (showinterface)
-- Prints to the Listener or the result log; changes nothing in the scene.
ss = stringStream ""
u = Unwrap_UVW() -- [verify] class name Unwrap_UVW
format "Unwrap_UVW props: %\n" (getPropNames u) to:ss
showInterfaces u to:ss -- [verify] showInterfaces with to:
m = uvwmap()
format "uvwmap props: %\n" (getPropNames m) to:ss
showInterface BakeToTexture to:ss -- [verify] showInterface on a UtilityPlugin interface
result = ss as string
```

Check in the result: Unwrap_UVW lists interfaces named like `unwrap`, `unwrap2` and so on, with
functions such as `flattenMap`, `pack`, `setMapChannel`. `uvwmap` lists `maptype`, `length`,
`width`, `height`, `mapChannel` and a real-world flag. Record the exact names in your report.

---

## P1 UV audit

Goal: shells, overlap, flipped faces, coverage, texel density spread and minimum gap per node and
channel.

```python
# channel: batch | bridge | handoff
# checked against scripts/maxkit_uv.py (pure analysis run offline on synthetic data), sR1sAWWT2x8 (texel density), 2gv1jYDAoJc (8 px padding at 2K)
# kit: ["audit"], with scripts/maxkit_uv.py prepended; ARGS: names, channel, tex_size, target_td
from pymxs import runtime as rt

names = ARGS["names"]            # node names to audit
channel = ARGS.get("channel", 1)
tex = ARGS.get("tex_size", 2048)
target = ARGS.get("target_td")   # px/cm, None = use the median
reports = []
for name in names:
    node = rt.getNodeByName(name)
    if node is None:
        reports.append({"node": name, "findings": [{"severity": "error", "rule": "uv.node", "message": "not found"}]})
        continue
    reports.append(uv_audit(node, channel=channel, tex_size=tex, target_td=target,
                            tol=0.15, raster=1024, min_pad_px=8 * tex / 2048, min_util=75))
result = {"units": audit.units(), "reports": reports}
```

The temporary copy made by `extract_faces` is removed inside the same undo record.

On `mcp-safe`, propose `scripts/mxs/maxkit_uv.ms` followed by
`result = uvk_auditNodes (selection as array) 1 2048`. It reports per object (density, flipped
faces, faces outside 0-1) without shells or overlap.

Read the result:

- `overlap_pct > 0` on a bake channel: stop and fix, unless mirrored halves were offset on purpose
  (P12).
- `flipped_faces` with `mirrored_shells`: mirrored shells are a choice; scattered flipped faces are
  an error.
- `td_outliers`: compare to the target; hero areas may sit above on purpose.
- `min_gap_tex_px` under the padding rule: repack with more padding.
- `outside_0_1_faces` or `outside_0_1_samples` on a single-tile asset: repack; on UDIM or tiling
  surfaces it is expected.

---

## P2 Checker capture without losing materials

Goal: a visual stretch check that leaves the artist's materials untouched.

```python
# channel: batch | bridge | handoff
# checked against uv-baking-texturing__maxscript-render-to-texture-2027.md (checker, coordinates.uTiling) and uv-baking-texturing__maxscript-baketotexture-utilityplugin-2027.md (PhysicalMaterial, base_color_map)
# kit: ["capture"]; args: names, out_dir, tiling
from pymxs import runtime as rt

nodes = [rt.getNodeByName(n) for n in ARGS["names"]]
nodes = [n for n in nodes if n is not None]
chk = rt.checker()
chk.coordinates.uTiling = ARGS.get("tiling", 16)
chk.coordinates.vTiling = ARGS.get("tiling", 16)
mat = rt.PhysicalMaterial()
mat.name = "TMP_UV_CHECKER"
mat.base_color_map = chk
saved = {n.name: n.material for n in nodes}
try:
    for n in nodes:
        n.material = mat
    rt.showTextureMap(mat, chk, True)  # [verify] showTextureMap on a PhysicalMaterial slot
    shots = capture.views(ARGS["out_dir"], views=("persp", "front", "left", "top"))
finally:
    for n in nodes:
        n.material = saved[n.name]
result = {"captures": shots, "restored": len(saved)}
```

Look for: squares that are square (no stretch), the same square size across parts (uniform density),
straight rows on straightened shells, no shell mirrored where text must read.

---

## P3 Scripted unwrap fallback (Flatten and Pack)

Use only when nobody can do the GUI unwrap and a usable bake layout is enough. It cannot place seams
by intent. Every Unwrap UVW function below is `[verify]`; confirm the signatures with P0. Defaults
follow the Unwrap UVW doc: angle 60, spacing 0.02, normalize on, rotate on.

```maxscript
-- channel: mcp-safe | handoff | bridge | batch
-- checked against uv-baking-texturing__unwrap-uvw-modifier.md (Flatten and Pack options); every function name is unconfirmed
-- Adds a new Unwrap UVW on top of the stack: the user's stack is kept and the modifier can be removed.
fn uvb_flattenPack obj channel angle spacing =
(
    select obj
    max modify mode
    local uw = Unwrap_UVW() -- [verify] class name
    addModifier obj uw
    modPanel.setCurrentObject uw -- [verify] most unwrap functions need the modifier active in the panel
    uw.unwrap.setMapChannel channel -- [verify] unwrap.setMapChannel
    -- angle threshold, face selection (empty = all), spacing, normalize, rotate, fill holes
    uw.unwrap.flattenMap angle #() spacing true 0 true true -- [verify] flattenMap argument order
    -- method, spacing, normalize, rotate, fill holes
    uw.unwrap.pack 1 spacing true true true -- [verify] assumed order: method, spacing, normalize, rotate, fillHoles; rotate on
    uw
)
undo "uv flatten pack" on
(
    result = for o in (selection as array) collect (uvb_flattenPack o 1 60.0 0.02).name
)
```

GATE: run P1. Expect many small shells: Flatten cuts on every edge above the angle. Bake results
will show more seams than a hand unwrap. For engine assets, recommend the GUI unwrap or a dedicated
unwrap tool and say why. Painter can also cut, unfold and pack per texture set (xuLRnFBvLyI
00:02:51).

Peel solver (Unfold3D or LSCM) and Pack method (Unfold 3D or Recursive Packing) have no confirmed
script property. Set them in the GUI (gui-paths.md, Unwrap UVW).

---

## P4 Lightmap UVs on channel 2

Goal: a non-overlapping second channel for baked lighting. Skip it when the engine generates
lightmap UVs or the project uses no baked light; say which.

- Fully dynamic lighting (Lumen in Unreal): no lightmap channel; turn lightmap generation off in the
  Datasmith import options (qsV4k09kPV8 00:03:32). Baked lighting: turn it on.
- Unreal creates a lightmap UV channel automatically on Datasmith import (Datasmith doc, UV
  Channels).
- To use this channel instead: a Datasmith Attributes Modifier before export, or Light Map
  Coordinate Index in the Static Mesh Editor after import (Datasmith doc, Use Custom Lightmap UVs).
  Unreal channel indices start at 0, so 3ds Max channel 2 usually becomes Unreal 1.

```maxscript
-- channel: mcp-safe | handoff | bridge | batch
-- checked against uv-baking-texturing__uvw-map-modifier.md (99 channels, channel change copies edits) and game-assets digest (lightmap channel, zero overlap); function names unconfirmed
-- Works on channel 2 only; channel 1 is never written.
fn uvb_lightmap obj spacing =
(
    select obj
    max modify mode
    local uw = Unwrap_UVW() -- [verify]
    uw.name = "Unwrap_LM_ch2"
    addModifier obj uw
    modPanel.setCurrentObject uw -- [verify]
    uw.unwrap.setMapChannel 2 -- [verify] switching an existing modifier copies its edits silently; this one is new
    uw.unwrap.flattenMap 45.0 #() spacing true 0 true true -- [verify]
    uw.unwrap.pack 1 spacing true false true -- [verify] assumed order: method, spacing, normalize, rotate, fillHoles; rotate false keeps texels axis aligned [added]
    uw
)
undo "lightmap uv ch2" on
(
    result = for o in (selection as array) collect (uvb_lightmap o 0.03).name
)
```

GATE: P1 on channel 2: `overlap_pct` 0, `mirrored_shells` 0, `min_gap_tex_px` at least 2 at the
lightmap resolution [added].

For Datasmith, only the 6 lowest channels survive and Datasmith adds 2 lightmap channels
(game-assets digest, Datasmith doc). Keep channel counts low.

---

## P5 Real-world mapping for archviz surfaces

Goal: floors and walls where 1 m of texture equals 1 m of surface, regardless of room size.
Real-World Map Size must be on in both the modifier and the bitmap (zLDLOSx-qL0 00:04:35). It locks
Length, Width, Height, Tiling, Fit, Bitmap Fit and Region Fit, and allows only Planar, Cylindrical,
Spherical and Box (UVW Map doc).

Size the bitmap from real dimensions: a tile of 56 brick courses at about 7 cm is about 400 cm,
typed as 4000 in a millimeter scene (zLDLOSx-qL0 00:08:33). For a plank sheet, use plank count times
plank width.

```python
# channel: batch | bridge | handoff
# checked against uv-baking-texturing__uvw-map-modifier.md (Box type, Real-World Map Size) and zLDLOSx-qL0; property names unconfirmed
# args: names (floor and wall nodes), maptype_box_index; sizes are in system units
import pymxs
from pymxs import runtime as rt

def add_real_world_box(node, channel=1):
    m = rt.uvwmap()                 # constructor confirmed in the BakeToTexture doc example
    m.maptype = ARGS.get("maptype_box_index", 4)   # [verify] index of Box in this build (P0)
    m.realWorldMapSize = True       # [verify] property name
    m.mapChannel = channel          # [verify] property name
    rt.addModifier(node, m)
    return m

def real_world_bitmap(path, width, height):
    b = rt.bitmaptexture(filename=path)            # bitmaptexture filename: confirmed (RTT doc)
    b.coordinates.realWorldScale = True            # [verify]
    b.coordinates.realWorldWidth = width           # [verify] system units
    b.coordinates.realWorldHeight = height         # [verify]
    return b

with pymxs.undo(True, "real-world mapping"):
    done = []
    for name in ARGS["names"]:
        n = rt.getNodeByName(name)
        if n is not None:
            add_real_world_box(n)
            done.append(name)
result = {"mapped": done}
```

A texture-set build itself belongs to scenario-3dsmax-materials; this skill sets only the mapping
and its scale.

GATE: a 1 m reference box rendered next to the floor; planks and courses match the real size. A
top-down orthographic render and a grazing camera along the longest wall show no recognizable repeat
[added check].

Never add UVW Map on top of an object that already has authored UVs on that channel: it replaces
them. Check P1 first.

---

## P6 Bake procedural or layered materials to a PBR set (Self projection)

Goal: base color, metalness, roughness and AO files plus a new PBR material inside a Shell material
(2IhYmRsKZ4Q). All `BakeToTexture` names are confirmed in the MAXScript doc (MBT). The renderer
should be Arnold: the BTT doc recommends it for albedo, metalness, roughness and AO.

```maxscript
-- channel: handoff | bridge | mcp-safe (bake and bitmap writes not documented as allowed) | batch (showDialog in batch is unproven)
-- checked against uv-baking-texturing__maxscript-baketotexture-utilityplugin-2027.md and uv-baking-texturing__baking-to-texture-2027.md
-- Writes new files only; never overwrites (alwaysSkipExistingFiles).
fn uvb_compatible =
(
    BakeToTexture.showDialog() -- populates the compatible list (MBT note)
    local names = #()
    local entries = BakeToTexture.getCompatibleMapTypes()
    for s in entries do append names ((filterString s " :")[1])
    #(names, entries)
)

fn uvb_addByName obj mapName entries =
(
    -- addMapByClassID needs the class ID; the entry string holds it after the name [verify string format]
    local m = undefined
    for s in entries while m == undefined do
    (
        if (filterString s " :")[1] == mapName do
        (
            local idx = findString s "#("
            if idx != undefined do
            (
                local cid = execute (substring s idx -1)
                local before = (BakeToTexture.getMaps obj).count
                BakeToTexture.addMapByClassID obj cid
                local after = BakeToTexture.getMaps obj
                if after.count > before do m = after[after.count]
            )
        )
    )
    m
)

fn uvb_pbrBake obj outDir size =
(
    local info = uvb_compatible()
    local entries = info[2]
    BakeToTexture.outputPath = outDir
    BakeToTexture.alwaysOverwriteExistingFiles = false
    BakeToTexture.alwaysSkipExistingFiles = true
    BakeToTexture.showFrameBuffer = false
    BakeToTexture.autoCloseProgressDialog = true
    local maps = #()
    for n in #("Arnold_albedo", "Arnold_metalness", "Arnold_roughness") do
    (
        local m = uvb_addByName obj n entries
        if m != undefined do append maps m
    )
    append maps (BakeToTexture.addMap obj #OcclusionMap)
    for m in maps do
    (
        m.setImageSize size size
        m.edgePadding = 8 -- 8 px at 2K (2gv1jYDAoJc); scale with size
        m.fileType = "png"
        m.uvChannel = 1
    )
    BakeToTexture.setOutputTo obj #CreateNewMaterial material:(PhysicalMaterial())
    local slots = BakeToTexture.getTargetMaterialSlots obj
    local report = stringStream ""
    format "slots: %\n" slots to:report
    for m in maps do format "% bakeable:% frozen:% slot:%\n" m.mapTypeName m.bakeable m.frozen (m.getTargetMapSlot()) to:report
    #(maps, slots, report as string)
)
-- placeholders: write the node name and an output folder chosen by the user
r = uvb_pbrBake (getNodeByName "LOW_NODE_NAME") "OUTPUT_FOLDER" 2048
result = r[3]
```

Second step, after reading the slot list: call `m.setTargetMapSlot "<slot>"` for each map with a
name from `slots`. The 2021 video shows `base_color_map`, `metalness_map`, `roughness_map`, `ao_map`
and `norm_map` on PBR Metal/Rough (2IhYmRsKZ4Q frame 00:01:46). Physical and OpenPBR slot names
differ: use the list, never guess. Then bake:

```maxscript
-- channel: handoff | bridge | mcp-safe (not documented as allowed) | batch (unproven)
-- checked against uv-baking-texturing__maxscript-baketotexture-utilityplugin-2027.md (bake onMapBakedCallback)
global uvb_baked = #()
fn uvb_onBaked ok path =
(
    append uvb_baked #(ok, path)
    ok and (doesFileExist path)
)
result = if BakeToTexture.bakeableMapsAreValid() then
(
    BakeToTexture.bake onMapBakedCallback:uvb_onBaked
    uvb_baked
)
else "maps not valid for the current renderer: check frozen and bakeable"
```

GATE: one file per map at the planned size; the object carries a Shell material whose baked material
has the slots filled. Compare the High Quality viewport with an ActiveShade of the original
(2IhYmRsKZ4Q 00:02:30).

---

## P7 High to low: normal, AO and curvature with a diagnostic pass

Preconditions: low poly unwrapped with no overlap (P1), hard edges split in UVs, one material, no
Edit Normals modifier (TS doc), high and low aligned in world space. Projection names are confirmed
in the MBT projection example.

```maxscript
-- channel: handoff | bridge | mcp-safe (not documented as allowed) | batch (unproven)
-- checked against uv-baking-texturing__maxscript-baketotexture-utilityplugin-2027.md (Projection example, BakeToTextureMap properties)
-- Pass 1 is diagnostic: small size, misses painted red. Pass 2 changes only size, file name and miss color.
fn uvb_setupHighToLow low high outDir size method rayDist =
(
    select low
    max modify mode
    if low.modifiers[#Projection] == undefined do
    (
        modPanel.addModToSelection (Projection name:"Projection") ui:on
        addPModObjects low false true objList:high -- arguments as in the MBT example
    )
    BakeToTexture.showDialog()
    BakeToTexture.outputPath = outDir
    BakeToTexture.alwaysSkipExistingFiles = true
    local nm = BakeToTexture.addMap low #NormalMap
    local ao = BakeToTexture.addMap low #OcclusionMap
    for m in #(nm, ao) do
    (
        m.setImageSize size size
        m.edgePadding = 8
        m.fileType = "png"
        m.projectionModifierIndex = 1 -- 0 would be Self; projectionMethod errors on Self
        m.projectionMethod = method -- 0 Cage, 1 Raytrace, 2 UV Match
        m.projectionMaxRayDistance = rayDist
        m.projectionRayMissColorType = 2 -- diagnostic color
        m.projectionDiagnosticColor = color 255 0 0
    )
    #(nm, ao)
)

fn uvb_dumpOptions m =
(
    local ss = stringStream ""
    for i = 1 to m.getOptionsCount() do
        format "% | % | type % | ro % | %\n" i (m.getOptionName i) (m.getOptionType i) (m.isOptionReadOnly i) (m.getOptionValue i) to:ss
    ss as string
)

fn uvb_setOption m optName val =
(
    local done = false
    for i = 1 to m.getOptionsCount() where (m.getOptionName i) == optName do done = m.setOptionValue i val
    done
)
```

Steps:

1. Run `maps = uvb_setupHighToLow $SM_Crate_low $SM_Crate_high outDir 512 1 10.0` (Raytrace) for
   aligned meshes, or method 0 (Cage) when they do not line up (-SMLc0od_5Y 00:01:38). Then bind
   `nm = maps[1]` and `ao = maps[2]`.
2. Run `uvb_dumpOptions nm` and read the option names. The dialog labels are Normal Map Space, Sync
   With, X (Red), Y (Green), MikkT for Tangent, Calculate bitangent per pixel and Output into Normal
   Bump (BTT doc). The script names may differ: use the dumped strings.
3. Set Tangent space, MikkT on, the per-pixel bitangent for the target, and Output into Normal Bump
   off with `uvb_setOption`. Set the same MikkT and per-pixel choice in Customize > Preferences >
   General > Normal Bump Mode (GUI).
4. Bake (the bake block from P6). Run P9 on the files. Read a lit capture of the low poly with the
   result.
5. Fix (P12). Then set `m.setImageSize 2048 2048`, `m.projectionRayMissColorType = 0`, a new
   `m.fileName` and bake the final.

Target settings:

- Unity has per-pixel bitangent disabled (BTT doc).
- -SMLc0od_5Y 00:02:13 sets MikkT with per-pixel off.
- The high-to-low page says most engines use per pixel.
- The deciding condition is the destination app. If it is not stated, bake both variants on a test
  bevel and compare in the target.

Green channel: the saved sources do not state which convention Unreal, Unity or glTF expects. The
Painter projects in the sources differ: DirectX in xuLRnFBvLyI (frame 00:04:58), OpenGL in
2gv1jYDAoJc (00:19:04). The control is Y (Green) up or down, or the Sync With preset (BTT doc); 3ds
Max has no "Flip Green" option. Commonly cited, unsourced here: OpenGL (Y up) for Unity and glTF,
DirectX (Y down) for Unreal [added]. Confirm with the target's documentation or a known bevel under
a moving light in the target before the final bake.

Curvature: Bake to Texture has no Curvature common map. Use an Override map (Scanline) or
Arnold_map_override with a curvature map from the Map Browser (BTT doc says override maps cover
curvature). The MAXtoA curvature map's class name is `[verify]`. Add it with
`BakeToTexture.addMap low #OverrideMap` and set its Map option through `uvb_dumpOptions` (option
type 15 = Map). Alternative: bake curvature in Substance Painter from the same low and high
(2gv1jYDAoJc frame 00:21:18 shows Curvature in Painter's bakers). Say which route you used.

Rounded Corners is a normal map that rounds sharp edges without a high poly (BTT doc). It suits
mid-poly props, not a replacement for a high-poly bake.

Several high sources into one map: give each high part the material ID of its low part, then set
`m.projectionHitOnlyMatchingMatID = true` (MBT; BTT Resolve Hit). It replaces an exploded bake when
parts sit close. `projectionResolveHitType` is 0 Closest, 1 Furthest (MBT; Furthest is the legacy
default, PO doc).

Blurry maps with enough texel density: keep Ray Depth and Sampling at the minimum needed and check
the renderer's filter settings (BTT doc).

---

## P8 Legacy Render to Texture bake for batch

Use when the bake must run headless and the BakeToTexture dialog path fails in `3dsmaxbatch`. Names
come from the RTT MAXScript doc. The normal element class and the projection link are `[verify]`.

```maxscript
-- channel: batch | handoff | bridge
-- checked against uv-baking-texturing__maxscript-render-to-texture-2027.md (INodeBakeProperties, render #bakeSelected); normal element and projection names unconfirmed
fn uvb_rttNormal low high outDir size =
(
    renderers.current = Default_Scanline_Renderer()
    select low
    max modify mode
    if low.modifiers[#Projection] == undefined do
    (
        modPanel.addModToSelection (Projection name:"Projection") ui:on
        addPModObjects low false true objList:high
    )
    low.iNodeBakeProperties.removeAllBakeElements()
    local be = NormalsMap() -- [verify] bake element class for Normals
    be.outputSzX = be.outputSzY = size
    be.fileType = outDir + "\\" + low.name + "_normal_rtt.png"
    be.fileName = filenameFromPath be.fileType
    be.enabled = true
    low.INodeBakeProperties.addBakeElement be
    low.INodeBakeProperties.bakeEnabled = true
    low.INodeBakeProperties.bakeChannel = 1
    low.INodeBakeProperties.nDilations = 4 -- [added] dilation in pixels around shells
    low.INodeBakeProjProperties.enabled = true -- [verify] property name
    low.INodeBakeProjProperties.projectionMod = low.modifiers[#Projection] -- [verify] property name
    select low
    render rendertype:#bakeSelected vfb:off progressBar:true outputSize:[size,size]
    doesFileExist be.fileType
)
```

GATE: the file exists, P9 passes. The legacy defaults differ from BTT: Tangent Red Right and Green
Down, Offset 10.0 units without a cage, Resolve Hit Furthest (Projection Options doc).

---

## P9 Read the baked maps

Runner side, after the files come back:

```python
# channel: runner (plain Python, no pymxs)
# checked against scripts/bake_check.py (run offline on synthetic PNGs)
import subprocess
import sys


def bake_check(normal_maps, other_maps):
    """--normal only on normal maps; AO and color maps are read without it. Raises on a flag."""
    if not normal_maps and not other_maps:
        raise FileNotFoundError("no baked map to check: the bake wrote nothing")
    for files, extra in ((normal_maps, ["--normal"]), (other_maps, [])):
        if files:
            subprocess.run([sys.executable, "scripts/bake_check.py", *extra, "--diag", "255,0,0", *files],
                           check=True)
```

Then run `max_review.image_checks(png)` and `max_review.contact_sheet(...)` on the lit captures of
the low poly. Read one contact sheet instead of every image.

Interpretation:

- `diag_color_pct > 0`: rays missed. Raise the ray distance or cage push there (P12).
- `neg_z_pct > 0.5` or a mean far from (0.5, 0.5, 1.0) on a tangent map: wrong space, misses or
  inverted normals.
- Size differs from the plan: fix the Image Size, not the material tiling.

---

## P10 Randomizers and triplanar (V-Ray 7, Corona)

Decide first:

- The asset stays in V-Ray or Corona and has bad or no UVs: use triplanar.
- It has usable UVs but visible repetition: use a randomizer on the UVs.
- Graphics and imperfections: use Corona decals.
- Maps leave 3ds Max: unwrap instead. Randomizers do not survive export.

Check `rt.renderers.current` before creating any node. Class and property names below are
`[verify]`; the parameters are confirmed in the Chaos docs (VTT, VUR, CMR, CTP).

```python
# channel: batch | bridge | handoff
# checked against uv-baking-texturing__vray7-vrayuvwrandomizer.md and uv-baking-texturing__vray7-vraytriplanartex.md (parameters); class and property names unconfirmed
# V-Ray only: one randomizer drives every VRayBitmap of a material through Mapping Source (6FalgHWkhKE 00:04:26)
from pymxs import runtime as rt
import pymxs

if "V_Ray" not in str(rt.classOf(rt.renderers.current)):   # [verify] V-Ray renderer class name
    result = {"skipped": "current renderer is not V-Ray"}
else:
    with pymxs.undo(True, "vray uvw randomizer"):
        rnd = rt.VRayUVWRandomizer()         # [verify] class name
        rnd.mode_by_element = True           # [verify] property for "By element"
        rnd.rotation_min = 0.0               # [verify] keep 0 when the set has a normal map (6FalgHWkhKE 00:07:43)
        rnd.rotation_max = 0.0               # [verify]
        result = {"created": str(rnd), "props": [str(p) for p in rt.getPropNames(rnd)]}
```

The returned `props` list gives the real property names; set the rest from it. Recipes (parameters
confirmed in the docs and videos):

- **Bricks or stones, collapsed mesh (V-Ray):** VRayUVWRandomizer By element, offset U and V 0 to 1,
  rotation 0 when a normal map is in the set. Use it as the Mapping Source of the master VRayBitmap,
  with the other bitmaps linked to the master (6FalgHWkhKE 00:07:09). Lower the blur on the normal
  bitmap (00:13:02).
- **Large ground or plaster (V-Ray):** Mirror Tile on the bitmap, Stochastic tiling in the
  randomizer, Tile blend 0.2 for ground or 0.01 for bricks (6FalgHWkhKE 00:17:27; VUR doc).
- **No usable UVs (V-Ray):** VRayTriplanarTex, Size in scene units, Blend 0.1 or higher if seams
  show, Random texture offset By element. For per-element scale, chain VRayUVWRandomizer into its
  Mapping Source (6FalgHWkhKE 00:11:55). With a normal map, put the VRayNormalMap inside the
  triplanar's Texture slot, not the other way round (VTT doc). On V-Ray GPU, triplanar bump works
  only with bitmaps; otherwise put VRayColor2Bump in the bump slot (VTT doc).
- **Corona planks:** Corona Mapping Randomizer by Mesh Element. Directional wood uses rotation 0 to
  180 with Step 180; 0 to 360 with Step 180 under-rotates (4o3j7PBHLrQ 00:09:11). Rows use Step = 1
  / rows. Whole-number offsets show nothing (CMR doc).
- **Corona with bad UVs:** connect the randomizer into Corona Triplanar, never the reverse, because
  triplanar overrides downstream mapping (CMR doc).
- **Same randomization on every channel:** V-Ray links bitmaps to one master. Corona clones the
  randomizer node or wires its parameters (CMR doc; 4o3j7PBHLrQ 00:07:42).
- **Color variation:** VRayMultiSubTex Random by Element, 20 IDs by default (6FalgHWkhKE 00:14:20),
  or Corona Multimap.

GATE: an interactive render, because neither renderer previews these nodes in the viewport (CTP, CMR
docs; 4o3j7PBHLrQ 00:03:23). First render with a numbered checker in place of the texture
(6FalgHWkhKE 00:03:18), then with the real maps. Renaming objects or materials changes Corona
results when the mode is by name or instance (CMR doc).

---

## P11 Substance Painter hand-off

Rules (Adobe, xuLRnFBvLyI):

- The material name becomes the texture set name.
- Use one material per object where possible.
- Pack UVs per texture set.
- Object names become geometry mask entries.
- An ID map comes from vertex colors or a baked color ID.

```python
# channel: batch | bridge | handoff
# checked against scripting-pipeline__pymxs-using-2027.md (PhysicalMaterial) and xuLRnFBvLyI (texture set rules)
# args: sets = {"Upper": ["node_a", "node_b"], "Base": [...]}
from pymxs import runtime as rt
import pymxs

report = {"sets": {}, "problems": []}
with pymxs.undo(True, "painter texture sets"):
    for set_name, names in ARGS["sets"].items():
        mat = rt.PhysicalMaterial()
        mat.name = set_name
        for n in names:
            node = rt.getNodeByName(n)
            if node is None:
                report["problems"].append("missing node " + n)
                continue
            if str(node.name).startswith(("Box", "Object", "Cylinder")):
                report["problems"].append("default-looking name: " + str(node.name))
            node.material = mat
        report["sets"][set_name] = names
result = report
```

Then:

- Pack per set: P1 per set, then the GUI Pack, or P3's `pack` on the set's selection.
- Vertex Paint ID colors: turn the vertex color display off before leaving the modifier (xuLRnFBvLyI
  00:05:15).
- Export the FBX through scenario-3dsmax-game-assets (`xio.export_fbx`).
- Unreal's FBX import connects only Color and Normal; Specular is imported but unconnected, AO is
  not imported (Unreal FBX static mesh pipeline doc). Deliver AO and the other maps as files with a
  wiring list.

In Painter, the frame shows Normal Map Format DirectX and Compute Tangent Space Per Fragment
(xuLRnFBvLyI frame 00:04:58). Bake in Painter with `_low` and `_high` name suffixes, and set the
Output Size equal to the texture set size (2gv1jYDAoJc 00:21:12).

---

## P12 Fixing what the bake shows

| What you see                              | Cause                                             | Fix (source)                                                                                                                               |
| ----------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Flat red patches (diagnostic color)       | rays miss the high poly                           | raise Max Ray Distance or push the cage there; Include Working Model only when the low does not occlude the high (PO doc)                  |
| Detail missing at cylinder ends           | rays parallel to the detail                       | move that end of the cage out and scale it in, or Break low-res verts (TS doc)                                                             |
| Reddish flare right, bluish left          | flipped UVs in tangent space                      | Unwrap UVW Flip Horizontal on those selections (TS doc)                                                                                    |
| Garbage on one mirrored half              | overlapping UVs                                   | move half of the overlapping UVs on W; the bake uses the higher W (TS doc)                                                                 |
| Neighbor parts printed into a part        | cage or ray distance too large, parts too close   | lower the distance; bake parts exploded by name pairs [added]                                                                              |
| Visible seam line                         | padding too small or hard edge without a UV split | raise edgePadding; split UVs on hard edges                                                                                                 |
| Map looks faceted only in the viewport    | viewport Normal Bump Mode differs from the bake   | match Preferences > Normal Bump Mode (-SMLc0od_5Y 00:03:19)                                                                                |
| Blurry bake                               | low texel density, or renderer filtering          | raise density on that shell first (2gv1jYDAoJc 00:21:47); then check the renderer filter and keep ray depth and sampling minimal (BTT doc) |
| Close parts bleed into each other         | one map, several high sources                     | matching material IDs and `projectionHitOnlyMatchingMatID` true (BTT, MBT)                                                                 |
| Soft normal map in a V-Ray randomized set | linked VRayBitmaps share blur                     | lower blur on the normal bitmap (6FalgHWkhKE 00:13:02)                                                                                     |
| Line where two parts intersect            | hard intersection                                 | merge with a boolean and soften, or accept it (2gv1jYDAoJc 00:23:26)                                                                       |
| Legacy RTT normals inverted               | red or green flip mismatch                        | flip in the Normal Bump map instead of rebaking (PO doc)                                                                                   |

The Flip Horizontal fix is GUI work in the UV editor. Its script name is `[verify]` (P0).
