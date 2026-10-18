"""
bx_export: engine-ready exports from Blender 5.2, checked by re-importing them.

  import sys; sys.path.append("<skills>/scenario-blender-export/scripts"); import bx_export as bxe

  bxe.export("/abs/out/Crate.fbx", "unity", objects=["Crate"])   # preset, then operator overrides
  bxe.round_trip("/abs/out/Crate.fbx", objects=["Crate"])         # re-import in a background Blender
  bxe.glb_summary("/abs/out/crate.glb")                           # no Blender needed
  bxe.lods("Crate", ratios=(0.5, 0.25))                           # Crate_LOD0..2 under an empty
  bxe.collision("Crate", "unreal")                                # UCX_Crate_00; "godot": Crate-convcolonly

  # headless
  blender -b scene.blend --factory-startup --python-exit-code 1 -P bx_export.py -- \
          --preset godot --out /abs/crate.glb [--objects A B]
  blender -b --factory-startup --python-exit-code 1 -P bx_export.py -- \
          --batch /abs/in /abs/out --preset godot [--profile game]
  blender -b --factory-startup --python-exit-code 1 -P bx_export.py -- --inspect /abs/crate.glb

Every preset was exported and re-imported in Blender 5.2.1 by the family's live suite
(tests/scenario-blender-expert/test_live_export.py in the skills repository).
"""

import json
import os
import struct
import subprocess
import sys
import tempfile

try:
    import bpy
    from mathutils import Vector
except ImportError:  # glb_summary() runs in plain Python
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.dirname(os.path.dirname(HERE))

_FBX = dict(use_selection=True, apply_unit_scale=True, use_mesh_modifiers=True,
            mesh_smooth_type="FACE", add_leaf_bones=False, path_mode="COPY", embed_textures=True,
            axis_forward="-Z", axis_up="Y")
_FBX_RIG = dict(object_types={"ARMATURE", "MESH"}, use_armature_deform_only=True, bake_anim=True,
                bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False)
_GLB = dict(export_format="GLB", use_selection=True, export_yup=True, export_apply=True)

# preset: (extension, exporter operator, keyword arguments)
PRESETS = {
    # Unity 6.3, measured: a static mesh imports at scale 1, rotation 0.
    "unity": (".fbx", "export_scene.fbx", dict(
        _FBX, apply_scale_options="FBX_SCALE_ALL", bake_space_transform=True,
        object_types={"MESH", "EMPTY"}, bake_anim=False)),
    # Measured: scale 1, faces +Z, the armature node keeps a 270 degree X rotation.
    # bake_space_transform (documented as broken with armatures) does not remove it, and
    # Unity's Bake Axis Conversion turns the character to face -Z: leave both off.
    "unity_skeletal": (".fbx", "export_scene.fbx", dict(
        **_FBX, **_FBX_RIG, apply_scale_options="FBX_SCALE_ALL")),
    "unreal": (".fbx", "export_scene.fbx", dict(
        _FBX, apply_scale_options="FBX_SCALE_NONE", object_types={"MESH", "EMPTY"}, bake_anim=False)),
    "unreal_skeletal": (".fbx", "export_scene.fbx", dict(
        **_FBX, **_FBX_RIG, apply_scale_options="FBX_SCALE_NONE")),
    # Roblox Creator Hub export requirements: FBX Unit Scale, Copy + embed textures, no leaf bones.
    "roblox": (".fbx", "export_scene.fbx", dict(
        _FBX, apply_scale_options="FBX_SCALE_UNITS", object_types={"ARMATURE", "MESH"},
        bake_anim=False)),
    "godot": (".glb", "export_scene.gltf", dict(_GLB)),
    "gltf": (".glb", "export_scene.gltf", dict(_GLB)),
    # three.js reads EXT_meshopt_compression through MeshoptDecoder and WebP natively.
    "web": (".glb", "export_scene.gltf", dict(
        _GLB, export_image_format="WEBP", export_meshopt_compression_enable=True)),
    "usd": (".usdc", "wm.usd_export", dict(selected_objects_only=True)),
    "usdz": (".usdz", "wm.usd_export", dict(selected_objects_only=True, usdz_downscale_size="2048")),
    # STL has no unit and slicers read millimeters: 1 Blender meter becomes 1000.
    "print": (".stl", "wm.stl_export", dict(export_selected_objects=True, apply_modifiers=True,
                                             global_scale=1000.0)),
}
# Which presets carry armatures, actions and shape keys through the file.
CARRIES = {
    "unity": set(), "unreal": set(), "roblox": {"armature", "shape_keys"}, "print": set(),
    "unity_skeletal": {"armature", "actions", "shape_keys"},
    "unreal_skeletal": {"armature", "actions", "shape_keys"},
    "godot": {"armature", "actions", "shape_keys"}, "gltf": {"armature", "actions", "shape_keys"},
    "web": {"armature", "actions", "shape_keys"}, "usd": {"shape_keys"}, "usdz": {"shape_keys"},
}
# Presets that rescale on the way out: STL in millimeters.
SCALE = {"print": 1000.0}
IMPORTERS = {
    ".glb": "import_scene.gltf", ".gltf": "import_scene.gltf", ".fbx": "import_scene.fbx",
    ".obj": "wm.obj_import", ".stl": "wm.stl_import", ".ply": "wm.ply_import",
    ".usd": "wm.usd_import", ".usda": "wm.usd_import", ".usdc": "wm.usd_import", ".usdz": "wm.usd_import",
}


def _op(path):
    module, name = path.split(".")
    return getattr(getattr(bpy.ops, module), name)


def _objects(objects):
    if objects is None:
        return [o for o in bpy.context.scene.objects if o.visible_get()]
    return [bpy.data.objects[o] if isinstance(o, str) else o for o in objects]


IMAGE_EXT = {"JPEG": ".jpg", "PNG": ".png", "TARGA": ".tga", "TARGA_RAW": ".tga", "TIFF": ".tif",
             "WEBP": ".webp", "BMP": ".bmp", "OPEN_EXR": ".exr", "HDR": ".hdr"}


def _name_packed_images():
    """glTF imports pack images with no path, named like "Image_0", and the FBX exporter
    names embedded media after them. Unity's Extract Textures then writes files without an
    extension and never imports them, so the model stays untextured. Returns what to restore."""
    named = []
    for img in bpy.data.images:
        if img.packed_file is not None and not os.path.splitext(img.filepath or img.name)[1]:
            named.append((img, img.filepath_raw))
            img.filepath_raw = ("//textures/" + bpy.path.clean_name(img.name)
                                + IMAGE_EXT.get(img.file_format, ".png"))
    return named


def export(path, preset, objects=None, **overrides):
    """Export `objects` (default: every visible object) with a preset. Children and the
    armature of a skinned mesh are not added for you: pass them. Returns a dict."""
    ext, op, kw = PRESETS[preset]
    if not path.lower().endswith(ext):
        raise ValueError(f"preset {preset!r} writes {ext} files")
    objs = _objects(objects)
    view = bpy.context.view_layer
    # An object removed after a render stays in view.objects as None until the next
    # update (Blender 5.2.1), and select_get() on it raises.
    view.update()
    keep = ([o for o in view.objects if o.select_get()], view.objects.active)
    for o in view.objects:
        o.select_set(o in objs)
    view.objects.active = objs[0] if objs else None
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    args = dict(kw, **overrides)
    named = _name_packed_images() if ext == ".fbx" and args.get("embed_textures") else []
    try:
        _op(op)(filepath=path, **args)
    finally:
        for img, old in named:
            img.filepath_raw = old
        for o in view.objects:
            o.select_set(o in keep[0])
        view.objects.active = keep[1]
    return {"path": path, "preset": preset, "bytes": os.path.getsize(path),
            "objects": [o.name for o in objs],
            "settings": {k: sorted(v) if isinstance(v, set) else v for k, v in args.items()}}


def inspect_scene(objects=None):
    """What an engine would receive, measured in Blender: world size, scale, triangles,
    shape keys, bones and actions per object."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    objs = _objects(objects)
    if objects is None:
        actions = {a.name for a in bpy.data.actions}
    else:  # only what these objects play: their action, NLA strips and shape-key action
        actions = set()
        for o in objs:
            for ad in (o.animation_data, getattr(getattr(o.data, "shape_keys", None), "animation_data", None)):
                if ad:
                    actions |= {ad.action.name} if ad.action else set()
                    actions |= {s.action.name for t in ad.nla_tracks for s in t.strips if s.action}
    out = {"objects": {}, "actions": sorted(actions)}
    for o in objs:
        info = {"type": o.type, "scale": [round(s, 4) for s in o.matrix_world.to_scale()]}
        if o.type == "MESH":
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            info["size"] = [round(max(p[k] for p in pts) - min(p[k] for p in pts), 4) for k in range(3)]
            me = o.evaluated_get(dg).to_mesh()
            info["tris"] = sum(len(p.vertices) - 2 for p in me.polygons)
            o.evaluated_get(dg).to_mesh_clear()
            keys = o.data.shape_keys
            info["shape_keys"] = [k.name for k in keys.key_blocks[1:]] if keys else []
        elif o.type == "ARMATURE":
            info["bones"] = len(o.data.bones)
            info["roots"] = [b.name for b in o.data.bones if b.parent is None]
        out["objects"][o.name] = info
    return out


def inspect_file(path):
    """Import a file into an empty scene and measure it (runs inside Blender)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _op(IMPORTERS[os.path.splitext(path)[1].lower()])(filepath=path)
    r = inspect_scene()
    r["file"], r["bytes"] = path, os.path.getsize(path)
    return r


def compare(before, after, carries=("armature", "actions", "shape_keys"), tol=0.001, scale=1.0):
    """Differences between two inspections, matched by object name. Empty when they agree.
    scale: what the preset multiplies sizes by (SCALE), so a millimeter STL compares clean."""
    diffs = []
    ab = after["objects"]
    for name, b in before["objects"].items():
        if b["type"] not in ("MESH", "ARMATURE") or (b["type"] == "ARMATURE" and "armature" not in carries):
            continue
        a = ab.get(name) or next((v for k, v in ab.items() if k.split(".")[0] == name and v["type"] == b["type"]), None)
        meshes = [v for v in ab.values() if v["type"] == "MESH"]
        if a is None and b["type"] == "MESH" and len(meshes) == 1 and \
                sum(v["type"] == "MESH" for v in before["objects"].values()) == 1:
            a = meshes[0]  # STL and OBJ importers name the object after the file
        if a is None:
            diffs.append(f"{name}: missing after the round trip")
            continue
        if b["type"] == "MESH":
            if any(abs(x * scale - y) > tol * scale for x, y in zip(sorted(b["size"]), sorted(a["size"]))):
                diffs.append(f"{name}: size {b['size']} became {a['size']}")
            if b["tris"] != a["tris"]:
                diffs.append(f"{name}: {b['tris']} triangles became {a['tris']}")
            if "shape_keys" in carries and set(b["shape_keys"]) - set(a["shape_keys"]):
                diffs.append(f"{name}: lost shape keys {sorted(set(b['shape_keys']) - set(a['shape_keys']))}")
        else:
            if a["bones"] != b["bones"]:
                diffs.append(f"{name}: {b['bones']} bones became {a['bones']}")
            if any(abs(s - 1.0) > 1e-3 for s in a["scale"]):
                diffs.append(f"{name}: armature scale {a['scale']} after the round trip")
    if "actions" in carries and len(after["actions"]) < len(before["actions"]):
        diffs.append(f"actions: {len(before['actions'])} became {len(after['actions'])}")
    return diffs


def round_trip(path, objects=None, preset=None):
    """Re-import an exported file in a background Blender (the open scene is untouched)
    and compare it with `objects` in this scene. Returns {"pass", "diffs", "before", "after"}."""
    before = inspect_scene(objects)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "inspect.json")
        run = subprocess.run([bpy.app.binary_path, "-b", "--factory-startup", "--python-exit-code", "1",
                              "-P", os.path.abspath(__file__), "--", "--inspect", path, "--json", out],
                             capture_output=True, text=True, timeout=600)
        if run.returncode != 0:
            raise RuntimeError(run.stdout[-2000:] + run.stderr[-2000:])
        with open(out) as f:
            after = json.load(f)
    diffs = compare(before, after, CARRIES.get(preset, ("armature", "actions", "shape_keys")),
                    scale=SCALE.get(preset, 1.0))
    return {"pass": not diffs, "diffs": diffs, "before": before, "after": after}


def glb_summary(path):
    """Read a .glb's JSON chunk: extensions, meshes, triangles, morph targets, skins,
    animations and image types. Plain Python, so it also runs outside Blender."""
    with open(path, "rb") as f:
        data = f.read()
    magic, version, _ = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2:
        raise ValueError("not a glTF 2.0 binary")
    size, kind = struct.unpack_from("<I4s", data, 12)
    if kind != b"JSON":
        raise ValueError("first GLB chunk is not JSON")
    g = json.loads(data[20:20 + size])
    acc = g.get("accessors", [])
    tris, morphs = 0, {}
    for m in g.get("meshes", []):
        for p in m.get("primitives", []):
            if p.get("mode", 4) != 4:
                continue
            idx = p.get("indices")
            n = acc[idx]["count"] if idx is not None else acc[p["attributes"]["POSITION"]]["count"]
            tris += n // 3
        names = m.get("extras", {}).get("targetNames")
        if names:
            morphs[m.get("name", "")] = names
    return {
        "bytes": len(data),
        "extensions_used": g.get("extensionsUsed", []),
        "extensions_required": g.get("extensionsRequired", []),
        "nodes": len(g.get("nodes", [])), "meshes": len(g.get("meshes", [])), "triangles": tris,
        "morph_targets": morphs,
        "skins": [len(s.get("joints", [])) for s in g.get("skins", [])],
        "animations": [a.get("name", "") for a in g.get("animations", [])],
        "materials": len(g.get("materials", [])),
        "images": [i.get("mimeType", os.path.splitext(i.get("uri", ""))[1]) for i in g.get("images", [])],
    }


def lods(obj, ratios=(0.5, 0.25)):
    """Decimated copies named for Unity's LOD import (Name_LOD0 is the original), grouped
    under an empty called Name. Godot builds LODs at import; Unreal in the Static Mesh Editor."""
    obj = bpy.data.objects[obj] if isinstance(obj, str) else obj
    name, col = obj.name, obj.users_collection[0]
    group = bpy.data.objects.new(name + "_LODGroup", None)
    col.objects.link(group)
    group.matrix_world = obj.matrix_world.copy()
    obj.name = f"{name}_LOD0"
    obj.parent, obj.matrix_parent_inverse = group, group.matrix_world.inverted()
    group.name = name
    out = {obj.name: sum(len(p.vertices) - 2 for p in obj.data.polygons)}
    for i, r in enumerate(ratios, 1):
        tmp = obj.copy()
        col.objects.link(tmp)
        mod = tmp.modifiers.new("lod", "DECIMATE")
        mod.ratio = r
        bpy.context.view_layer.update()
        me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        bpy.data.objects.remove(tmp)
        lod = bpy.data.objects.new(f"{name}_LOD{i}", me)
        col.objects.link(lod)
        lod.parent, lod.matrix_world = group, obj.matrix_world.copy()
        out[lod.name] = sum(len(p.vertices) - 2 for p in me.polygons)
    return {"group": group.name, "tris": out}


def collision(obj, engine, shape="convex"):
    """A collision mesh named for the engine's importer: Unreal UCX_ (convex) or UBX_ (box),
    Godot -convcolonly or -colonly. Unity and Roblox set colliders in the editor: None."""
    import bmesh
    obj = bpy.data.objects[obj] if isinstance(obj, str) else obj
    names = {("unreal", "convex"): f"UCX_{obj.name}_00", ("unreal", "box"): f"UBX_{obj.name}_00",
             ("godot", "convex"): f"{obj.name}-convcolonly", ("godot", "box"): f"{obj.name}-convcolonly",
             ("godot", "mesh"): f"{obj.name}-colonly"}
    if (engine, shape) not in names:
        return None
    bm = bmesh.new()
    bm.from_object(obj, bpy.context.evaluated_depsgraph_get())
    if shape == "box":
        lo = [min(v.co[k] for v in bm.verts) for k in range(3)]
        hi = [max(v.co[k] for v in bm.verts) for k in range(3)]
        bm.clear()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector([(lo[k] + hi[k]) / 2 + v.co[k] * (hi[k] - lo[k]) for k in range(3)])
    elif shape == "convex":
        hull = bmesh.ops.convex_hull(bm, input=bm.verts[:])
        bmesh.ops.delete(bm, geom=list(set(hull["geom_interior"]) | set(hull["geom_unused"])), context="VERTS")
    me = bpy.data.meshes.new(names[(engine, shape)])
    bm.to_mesh(me)
    bm.free()
    col = bpy.data.objects.new(me.name, me)
    obj.users_collection[0].objects.link(col)
    col.matrix_world = obj.matrix_world.copy()
    col.display_type = "WIRE"
    return {"object": col.name, "faces": len(me.polygons)}


def batch(src, dst, preset, profile="game", gate=True):
    """Every model file in `src`: import, run the delivery gate, export with `preset`,
    re-import and compare. Writes dst/report.json and returns it. Headless only."""
    if gate:
        sys.path.append(os.path.join(SKILLS, "scenario-blender-expert", "scripts"))
        import bx_audit
    ext = PRESETS[preset][0]
    os.makedirs(dst, exist_ok=True)
    report = {"preset": preset, "profile": profile, "files": {}}
    for fn in sorted(os.listdir(src)):
        stem, e = os.path.splitext(fn)
        if e.lower() not in IMPORTERS:
            continue
        r = report["files"][fn] = {}
        try:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            _op(IMPORTERS[e.lower()])(filepath=os.path.join(src, fn))
            meshes = [o.name for o in bpy.context.scene.objects if o.type == "MESH"]
            if gate and meshes:
                g = bx_audit.deliverable(meshes, profile=profile)
                r["gate"] = {"pass": g["pass"], "errors": g["errors"], "warnings": len(g["warnings"])}
            before = inspect_scene()
            out = os.path.join(dst, stem + ext)
            r["export"] = export(out, preset)["bytes"]
            r["diffs"] = compare(before, inspect_file(out), CARRIES[preset], scale=SCALE.get(preset, 1.0))
        except Exception as exc:  # one bad file must not stop the folder
            r["failed"] = f"{type(exc).__name__}: {exc}"
    with open(os.path.join(dst, "report.json"), "w") as f:
        json.dump(report, f, indent=1)
    return report


def _cli():
    import argparse
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="bx_export.py")
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--out", help="export the scene (or --objects) to this file")
    ap.add_argument("--objects", nargs="+")
    ap.add_argument("--batch", nargs=2, metavar=("SRC", "DST"), help="convert every model in SRC")
    ap.add_argument("--profile", default="game", help="delivery-gate profile for --batch")
    ap.add_argument("--inspect", help="import a file into an empty scene and measure it")
    ap.add_argument("--json", help="also write the result here")
    a = ap.parse_args(argv)
    if a.inspect:
        r = inspect_file(a.inspect)
    elif a.batch:
        r = batch(a.batch[0], a.batch[1], a.preset, profile=a.profile)
    else:
        r = export(a.out, a.preset, a.objects)
    text = json.dumps(r, indent=1)
    if a.json:
        with open(a.json, "w") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    _cli()
