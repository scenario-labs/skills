# Procedures: materials and look-dev

Every block is **not yet run in 3ds Max**. Names marked `[verify]` were not found in the saved docs;
the helper resolves most of them at run time and reports what it found. Units: centimeters unless a
block says otherwise. Renderer-specific blocks check `rt.renderers.current` first.

## P0. How to run a chunk

The helper `scripts/maxkit_materials.py` is plain pymxs. The lead's `max_wrap.wrap` inlines it as a
module named `maxkit_materials` when it is listed in `kit` with this skill's `scripts` folder in
`kit_dirs`. Each chunk below starts with `from maxkit_materials import *` and sets `result`; the
wrapper adds the undo record and writes the JSON result file.

```python
# channel: batch | bridge | handoff (runner side, plain Python)
# status: not yet run in 3ds Max; checked against skills/scenario-3dsmax-expert/scripts/max_wrap.py docstring
import os
import sys


def build_script(chunk, result_path, toolkit_dir, materials_scripts_dir):
    sys.path.insert(0, toolkit_dir)  # skills/scenario-3dsmax-expert/scripts
    from max_wrap import wrap
    return wrap(chunk, lang="python", kit=["capture", "maxkit_materials"],
                kit_dirs=[materials_scripts_dir], result_path=result_path, label="materials")


def write_new(path, text):
    if os.path.exists(path):
        raise FileExistsError(path)  # never overwrite: pick a new _v00N name
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
```

Then `max_check.check(code=script, lang="python")`, then `max_batch.run_batch(script, scene=...)` or
hand the file to the user (`handoff`). Check in the result: `ok` is true and `error` is empty.

## P1. Probe the scene (read-only)

Goal: renderer, color mode, units, class counts, texture color spaces.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripting-pipeline__maxscript-bitmap-values-2027.md
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

result = {
    "renderer": str(rt.renderers.current),
    "units": str(rt.units.SystemType),  # [verify] units.SystemType
    "colorspaces": [str(n) for n in rt.ColorPipelineMgr.GetFileIOColorSpaceList()],
    "materials": audit_materials(),
    "textures": audit_textures(),
}
```

For `mcp-safe`, propose `scripts/mxs/materials_audit.ms` as is: it is read-only and returns a
string. Check:

- `colorspaces` empty means Gamma workflow, or the call is wrong.
- Findings with severity `error` stop the build until fixed (P5).
- `class_counts` tells which renderer family the scene was built for.

## P2. Discover property names once per class

Goal: replace `[verify]` guesses with the real names for this install. Run it once per machine and
keep the result next to the project.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripting-pipeline__pymxs-using-2027.md (PhysicalMaterial)
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

names = {}
for target in ("openpbr", "physical", "gltf", "vray", "corona"):
    m = maxkit_materials._new_material(target, "LKD_probe_" + target)
    names[target] = {"class": str(rt.classOf(m)), "props": discover(m)} if m is not None else None
for frag in ("normalbump", "vraynormalmap", "coronanormal", "vraybitmap", "vraydirt", "vraycurvature",
             "vrayuvwrandomizer", "vraytriplanartex", "coronatriplanar", "falloff", "compositetexturemap"):
    c = find_class(frag, kind="texturemap")
    names[frag] = {"class": str(c), "props": discover(c())} if c is not None else None
for frag in ("vrayblendmtl", "coronalayeredmtl", "multimaterial"):
    c = find_class(frag)
    names[frag] = {"class": str(c), "props": discover(c())} if c is not None else None
result = names
```

The probe materials are created in memory and not assigned, so the undo record removes nothing of
the user's. `mcp-safe` equivalent: `showProperties (PhysicalMaterial())` in the Listener, one class
at a time, and read the output. Check: classes of uninstalled renderers come back `None`. The
material slots listed for each class are the names to trust over this file.

## P3. Arrival check of a PBR set (runner side)

```python
# channel: runner (any OS, no 3ds Max)
# status: runs outside 3ds Max; checked against QuJe2j7SHZ0 00:04:19 (tags) and dlwDiLsPWgI 00:07:08 (data maps)
import json
import subprocess
import sys


def arrival_check(set_dir, out_json, tag_dir=None):
    cmd = [sys.executable, "-I", "skills/scenario-3dsmax-materials/scripts/pbr_set.py", set_dir, "--json", out_json]
    if tag_dir:
        cmd += ["--tag-copy", tag_dir]  # V-Ray name tags, copies only
    subprocess.run(cmd, check=True, capture_output=True)
    with open(out_json, encoding="utf-8") as f:
        return json.load(f)
```

Then, for each color map, write a 2 x 2 tile with `pbr_set.seam_preview` and look at the center
cross. Check:

- every file has a role, and `unknown` is empty;
- one roughness convention;
- normal convention known, flipped for DirectX;
- one resolution;
- a real-world size decided and written down;
- no visible seam in the 2 x 2 tile. A generated set from scenario-3dsmax-generation gets the same
  check. The generator may name maps differently: extend `ROLE_TOKENS` rather than renaming files.

## P4. Build a material from a set

Goal: one material, every map in the right slot and color space, real-world mapping.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripting-pipeline__maxscript-bitmap-values-2027.md (openBitmap colorSpace:),
#         uv-baking-texturing__maxscript-baketotexture-utilityplugin-2027.md (PhysicalMaterial, base_color_map, uvwmap, addModifier)
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

ARGS = {  # filled by the runner from the P3 report; paths are never hard-coded here
    "target": "openpbr",  # openpbr | physical | gltf | vray | corona
    "name": "M_Oak_Oiled",
    "maps": {},  # {"base_color": path, "roughness": path, "normal": path, "metalness": path}
    "flip_green": False,
    "objects": [],  # node names to assign
    "repeat_cm": 0.0,  # real-world size of one texture repeat; 0 = keep the object's UVs
}
expected = {"openpbr": "arnold", "vray": "v_ray", "corona": "corona"}.get(ARGS["target"])
rend = str(rt.renderers.current).lower()
if expected and expected not in rend.replace("-", "_"):
    result = {"error": f"renderer is {rend}, target {ARGS['target']} expects {expected}; confirm with the user"}
else:
    mat, rep = build_material(ARGS["target"], ARGS["maps"], ARGS["name"], ARGS["flip_green"])
    rep["mapping"] = []
    if mat is not None:
        for n in ARGS["objects"]:
            node = rt.getNodeByName(n)  # [verify] getNodeByName
            if node is None:
                rep["warnings"].append(f"node {n} not found")
                continue
            node.material = mat
            if ARGS["repeat_cm"] > 0:
                rep["mapping"].append(box_map(node, ARGS["repeat_cm"]))
    result = rep
```

OpenPBR is also rendered outside Arnold, so the renderer check only warns through `error` and asks;
it never switches the renderer. Check:

- every `slots[*].connected` is true;
- `resolved` is `explicit`, or `fuzzy` with a property name that makes sense;
- `texture.colorSpace` holds Raw for data maps and sRGB for color, and `colorSpaceStatus` is not
  `forcedDefault`;
- the warnings about roughness mode and flip green are resolved. Then render the look-dev rig (P10).

## P5. Fix color spaces on existing textures

Goal: data maps loaded as color (finding `data_map_as_color`). Reload the bitmap with the Raw space;
the file is untouched.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against scripting-pipeline__maxscript-bitmap-values-2027.md
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

fixed = []
for f in audit_textures():
    if f["rule"] not in ("data_map_as_color", "color_map_as_data"):
        continue
    role = "data" if f["rule"] == "data_map_as_color" else "color"
    for tex in rt.getClassInstances(rt.Bitmaptexture):  # [verify]
        if str(tex.name) != f["node"]:
            continue
        kw = {"colorSpace": colorspace_for(role)}
        if role == "data":
            kw["gamma"] = 1.0
        bm = rt.openBitmap(str(tex.filename), **kw)
        tex.bitmap = bm  # [verify]
        fixed.append({"node": f["node"], "now": str(tex.bitmap.colorSpace)})
result = {"fixed": fixed, "after": [x for x in audit_textures() if x["severity"] == "error"]}
```

V-Ray bitmaps: the scriptable route is a tagged copy of the file (P3 `--tag-copy`) and repointing
the VRayBitmap to the copy. The transfer function and primaries property names are not in the saved
docs [verify]. GUI path: see gui-paths.md. Check: `after` holds no color-space errors. Re-render:
roughness reads the same as in the reference.

## P6. General feeling pass

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against 64vzHYEWedI 00:15:01 to 00:27:26 (method), helper names resolved at run time
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

GROUPS = {}  # {"Wall*": (145, 140, 132), "Floor*": (120, 96, 78), "Sofa*": (170, 165, 155)}, 8-bit values
result = general_feeling(GROUPS, target="openpbr")
```

Values in `GROUPS` are display values chosen with the user or from the reference; the helper clamps
to 10..240. Check:

- `assigned` covers every object in the shot;
- `previous` records the old materials for undo by hand. Ask the lighting sibling for a render, then
  squint: is the brightest area the focal point, and do walls and floor carry the intended warmth?

## P7. Weathered states with geometry masks (V-Ray)

Goal: base plus scratched, dirty and dusty states in a VRayBlendMtl, each mask tested in red first
(aHgu1dwjzSo; D-tB0dJp9sU). All V-Ray names come from the notes, not docs; P2 must run first.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against aHgu1dwjzSo 00:06:11 to 00:13:23 and D-tB0dJp9sU 00:07:45 to 00:11:03 (frames)
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

ARGS = {"base": "Wood_Base_mtl", "object": "", "debug": True}
if "v_ray" not in str(rt.renderers.current).lower().replace("-", "_"):
    result = {"error": "V-Ray is not the current renderer"}
else:
    rep = {"warnings": []}
    base = next((m for m in rt.sceneMaterials if str(m.name) == ARGS["base"]), None)  # [verify]
    blend = find_class("vrayblendmtl")()
    blend.name = ARGS["base"] + "_states"
    p, _ = find_prop(blend, ("baseMtl",), ("base",))
    set_prop(blend, p, base)
    red = find_class("vraymtl")()
    red.name = "DEBUG_red"
    dp, _ = find_prop(red, ("diffuse",), ("diffuse",))
    set_prop(red, dp, rt.color(255, 0, 0))

    # wear: convex curvature x dent, two scales
    curv = find_class("vraycurvature", "texturemap")()
    for cands, tokens, val in ((("mode",), ("mode",), 0), (("out_color_max",), ("max", "color"), 10.0)):
        q, how = find_prop(curv, cands, tokens)
        rep[f"curv_{tokens[0]}"] = (q, how, set_prop(curv, q, val) if q else False)  # [verify] mode 0 = convex
    dent = rt.Dent()  # [verify]
    comp = find_class("vraycomptex", "texturemap")()
    for cands, tokens, val in ((("sourceA",), ("source", "a"), curv), (("sourceB",), ("source", "b"), dent),
                               (("operator",), ("operator",), 2)):  # [verify] operator index for Multiply
        q, _ = find_prop(comp, cands, tokens, want_map=not isinstance(val, int))
        rep.setdefault("comp", []).append((q, set_prop(comp, q, val) if q else False))

    # dirt: VRayDirt swapped, same object only
    dirt = find_class("vraydirt", "texturemap")()
    for cands, tokens, val in ((("occluded_color",), ("occluded", "color"), rt.color(255, 255, 255)),
                               (("unoccluded_color",), ("unoccluded", "color"), rt.color(0, 0, 0)),
                               (("consider_same_object_only",), ("same", "object"), True),
                               (("radius",), ("radius",), 1.0), (("bias_z",), ("bias", "z"), 0.1)):
        q, how = find_prop(dirt, cands, tokens)
        rep.setdefault("dirt", []).append((q, how, set_prop(dirt, q, val) if q else False))

    # dust: Falloff towards/away on world Z
    dust = rt.Falloff()  # [verify] class name; type and direction property names unknown
    rep["warnings"].append("Falloff type Towards/Away and direction World Z: set by hand or after P2")

    coats, masks = [], [comp, dirt, dust]
    for i, mask in enumerate(masks):
        coats.append(red if ARGS["debug"] else base)
    q_coat, _ = find_prop(blend, ("coatMtl",), ("coat",))
    q_mask, _ = find_prop(blend, ("texmap_blend",), ("blend",), want_map=True)
    try:
        arr_c = rt.getProperty(blend, q_coat)  # [verify] getProperty; coat array, 9 slots
        arr_m = rt.getProperty(blend, q_mask)
        for i in range(len(masks)):
            arr_c[i] = coats[i]
            arr_m[i] = masks[i]
        rep["wired"] = True
    except Exception as e:
        rep["wired"] = f"failed: {e}; wire coats and masks in Slate (gui-paths.md)"
    node = rt.getNodeByName(ARGS["object"]) if ARGS["object"] else None  # [verify]
    if node is not None:
        node.material = blend
    result = rep
```

Then render. With `debug` on, every coat is red, so check placement per mask:

- red only on convex edges, broken up;
- red under ledges and in crevices, not on the underside touching the floor;
- red only on up-facing faces. Then duplicate the base per state (lower reflection for dirty, none
  for dust, rougher and scratched bump for worn), assign the copies as coats, and re-run
  `audit_materials()` until no `debug_red_left` finding remains. Renderer-neutral variant (OpenPBR,
  Physical): bake curvature and AO through scenario-3dsmax-uv-baking. Use the baked maps as Mix or
  Composite masks between two base color and roughness maps. For tiling breakup without V-Ray, put
  the OSL UVW Randomizer (2D) or Bitmap Random Tiling map in front of each bitmap, seeded by Node
  Handle for per-object variation (`materials-lookdev__osl-map-2027.md`). The doc says only "a
  supported renderer": render one test frame in the target renderer first. OSL class and parameter
  names are not in the saved docs: create them through the GUI or resolve names with `discover()`
  [verify].

## P8. Corona Physical: clear coat, thin shell, roughness mode

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against materials-lookdev__corona-physical-material.md (labels) and CxHKVjeycv0 00:01:33 to 00:03:18
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

SPEC = {  # label tokens -> value; resolved against discover() output of CoronaPhysicalMtl
    ("clearcoat", "amount"): 0.85,
    ("clearcoat", "ior"): 1.5,
    ("base", "rough"): 0.8,
}
if "corona" not in str(rt.renderers.current).lower():
    result = {"error": "Corona is not the current renderer"}
else:
    m = maxkit_materials._new_material("corona", "M_Paint_Solid")
    rep = {"set": []}
    for tokens, val in SPEC.items():
        q, how = find_prop(m, (), tokens)
        rep["set"].append((tokens, q, how, set_prop(m, q, val) if q else False))
    result = rep
```

Check: every `set` entry has a property and True. Then compare the render with the reference at
matched tone mapping. For tinted reflections, use clear coat IOR 1.001 with an Absorption color
(Corona blog). For a single-face pane, turn Thin shell on before anything else.

## P9. Set OpenPBR values by spec name

OpenPBR parameter meanings are public (base, specular, transmission, coat, fuzz, thin film,
emission, geometry). Their 3ds Max property names are not in the saved docs, so the block maps spec
words to whatever P2 found.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against tEUiIBApw-U (parameter semantics) and materials-lookdev__adobe-openpbr-faq.md
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

PRESETS = {
    "glass_solid": {("transmission", "weight"): 1.0, ("base", "metalness"): 0.0, ("specular", "ior"): 1.52,
                    ("specular", "roughness"): 0.0},
    "glass_frosted": {("transmission", "weight"): 1.0, ("specular", "ior"): 1.52, ("specular", "roughness"): 0.3},
    "glass_pane_thin": {("transmission", "weight"): 1.0, ("thin", "walled"): True},
    "coat_varnish": {("coat", "weight"): 1.0, ("coat", "ior"): 1.5, ("coat", "roughness"): 0.05},
    "fabric": {("fuzz", "weight"): 1.0, ("specular", "weight"): 0.2},
}
ARGS = {"material": "", "preset": "glass_solid"}
m = next((x for x in rt.sceneMaterials if str(x.name) == ARGS["material"]), None)  # [verify]
if m is None or "openpbr" not in str(rt.classOf(m)).lower():
    result = {"error": "material not found or not OpenPBR"}
else:
    result = []
    for tokens, val in PRESETS[ARGS["preset"]].items():
        q, how = find_prop(m, (), tokens)
        result.append((tokens, q, how, set_prop(m, q, val) if q else False))
```

The preset values are starting points [added]. Glass IOR 1.52 is the Corona doc value. Frosted
roughness 0.3 is a value shown in the Physical Material doc. Fabric specular weight 0.2 follows "no
reflections on fabric" (64vzHYEWedI 00:22:39). Check: if glass renders dark, raise transmission
depth to object scale. If dispersion is wanted, set dispersion scale above 0, because it defaults
to 0. Coat darkening is on by design.

## P10. Look-dev rig, render and contact sheet

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against the capture contract in skills/_SKILL_WRITING_BRIEF.md
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

ARGS = {"material": "", "out_dir": "", "size": (1200, 1200)}
rig = lookdev_rig(25.0)  # 50 cm ball, CxHKVjeycv0 00:04:53
m = next((x for x in rt.sceneMaterials if str(x.name) == ARGS["material"]), None)  # [verify]
ball = rt.getNodeByName("LKD_ball")  # [verify]
if m is not None and ball is not None:
    ball.material = m
cam = rt.getNodeByName("LKD_cam")
shots = {}
for tag in ("lookdev",):
    path = f"{ARGS['out_dir']}/LKD_{ARGS['material']}_{tag}.png"
    shots[tag] = capture.render(path, camera=cam, size=ARGS["size"])
result = {"rig": rig, "shots": shots}
```

The rig has no lights. Ask scenario-3dsmax-lighting-rendering for a neutral HDRI plus one raking
directional light. Then render two passes: HDRI only, and HDRI plus the raking light, which shows
bump (64vzHYEWedI 01:33:52). Runner side, after the render: `max_review.image_checks(png)` for
clipping and black frames. Then
`max_review.contact_sheet([reference, lookdev, shot_close, shot_far], out)` and score with
`critique.md`. Remove the rig after judging only with the user's agreement; otherwise hide it on its
own layer through scenario-3dsmax-scene.

## P11. Multi/Sub-Object hygiene

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against materials-lookdev__multi-sub-object-material-2027.md (behavior)
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

result = []
for node in rt.geometry:  # [verify] geometry collection
    result += audit_multisub(node)
```

Check: no `face_id_without_submaterial` findings, because those faces render black. Unused
sub-materials are reported only; the Clean MultiMaterial utility removes them on the user's go (GUI
path in gui-paths.md). For per-plank or per-object variation with many copies of the same bitmap,
run the Instance Duplicate Maps utility (GUI) to cut video-card load
(`materials-lookdev__multi-sub-object-material-2027.md`).

## P12. Legacy scenes and Scene Converter

- Scripted part: P1 lists legacy classes (`legacy_class`), mental ray leftovers and Corona Legacy
  materials.
- Scene Converter has no documented script entry in the saved docs: run it from the GUI
  (gui-paths.md), then re-run P1.
- Corona Legacy to Physical: the Corona Converter (Corona menu). Afterwards, check translucency and
  glass by render (Corona blog).
- V-Ray to Vantage or GPU: the V-Ray Scene Converter (V-Ray menu, Converters) is owned by
  scenario-3dsmax-archviz.

## P13. glTF deliverable

- Build with target `gltf` (P4). The glTF Material accepts only Bitmap Texture inputs
  (`scripting-pipeline__gltf-export-2027.md`), so `build_material` plugs the normal bitmap directly,
  with no normal node.
- No procedural masks: bake them first through scenario-3dsmax-uv-baking.
- Export belongs to scenario-3dsmax-game-assets or scenario-3dsmax-scripting (`xio.export_gltf`).
  Check before export:
- every exported mesh has a glTF Material;
- no Multi/Sub-Object nesting past two levels;
- no two bitmaps share a name with different extensions.

## P14. VRayMtl to OpenPBR shading mode (V-Ray 7)

Goal: move a VRayMtl to V-Ray's OpenPBR shading mode without flipping its look. It is a mode switch
on the same material (`materials-lookdev__vray7-vraymtl.md`, Shading mode). Use it only when the
frame renders on V-Ray CPU: the mode is not supported on V-Ray GPU. For USD or Arnold, build the 3ds
Max OpenPBR Material instead (P4, P9).

The block below is read-only. Run it before and after the switch, which is made in the GUI
(gui-paths.md, VRayMtl) because the script name and values of the mode property are not in the saved
docs.

```python
# channel: batch | bridge | handoff
# status: not yet run in 3ds Max; checked against materials-lookdev__vray7-vraymtl.md (Shading mode, BRDF, Coat, Sheen)
from pymxs import runtime as rt
from maxkit_materials import *  # noqa: F403 (inlined by max_wrap kit)
import maxkit_materials

ARGS = {"material": ""}
m = next((x for x in rt.sceneMaterials if str(x.name) == ARGS["material"]), None)  # [verify]
if m is None or "vraymtl" not in str(rt.classOf(m)).lower():
    result = {"error": "material not found or not VRayMtl"}
else:
    snap = {}
    for tokens in (("shading", "mode"), ("gloss",), ("rough",), ("brdf",)):
        for p in discover(m):
            n = p.lower()
            if all(t in n for t in tokens):
                try:
                    snap[p] = str(rt.getProperty(m, p))  # [verify] getProperty
                except Exception as exc:
                    snap[p] = "unreadable: %s" % exc
    result = {"material": str(m.name), "props": snap}
```

Check, comparing the two result files:

- the shading-mode property changed; if no property matched, the name is still unknown, say so;
- each glossiness value (reflection, refraction, coat, sheen): if the number is unchanged, its
  meaning reversed, so set `1 - value` by hand and invert any gloss map (V-Ray Invert or Output
  curve);
- BRDF reads GGX with roughness on (doc: forced in OpenPBR mode);
- a render of the look-dev rig matches the pre-switch render (`max_review.compare`); highlights that
  went from sharp to blurry mean a missed inversion. The `1 - value` rule follows the doc's "Use
  roughness reads the inverse value" [added]; the doc does not say whether the switch converts
  stored values itself.
