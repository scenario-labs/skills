"""Exports fixtures with every bx_export preset inside Blender, re-imports them, writes JSON.

Run by test_live_export.py:
  blender -b --factory-startup --python-exit-code 1 -P export_cases.py -- <export scripts> <out.json> <tmp dir>
"""

import json
import math
import os
import sys
import zipfile

import bmesh
import bpy
from mathutils import Vector

SCRIPTS, OUT, TMP = sys.argv[sys.argv.index("--") + 1:][:3]
sys.path.insert(0, SCRIPTS)
import bx_export as bxe  # noqa: E402

STATIC = ("unity", "unreal", "print", "usd", "usdz", "gltf")
RIGGED = ("unity_skeletal", "unreal_skeletal", "roblox", "godot", "web")


def mesh(name, build):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    build(bm)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bpy.data.materials.new("M_" + name))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def crate():
    """A 1.0 x 0.7 x 0.6 m box resting on the ground."""
    def build(bm):
        bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
        bmesh.ops.scale(bm, vec=(1.0, 0.7, 0.6), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, 0.3), verts=bm.verts)
    return mesh("Crate", build)


def character():
    """A 2 m capsule skinned to a three-bone chain, with a shape key and one action."""
    def build(bm):
        bmesh.ops.create_cone(bm, segments=12, radius1=0.25, radius2=0.25, depth=2.0,
                              cap_ends=True, calc_uvs=True)
        bmesh.ops.translate(bm, vec=(0, 0, 1.0), verts=bm.verts)
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1],
                                  cuts=7, use_grid_fill=False)
    body = mesh("Body", build)
    arm = bpy.data.armatures.new("Rig")
    rig = bpy.data.objects.new("Rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    parent = None
    for i, (name, z0, z1) in enumerate((("Hips", 0.0, 0.8), ("Spine", 0.8, 1.5), ("Head", 1.5, 2.0))):
        b = arm.edit_bones.new(name)
        b.head, b.tail, b.parent = (0, 0, z0), (0, 0, z1), parent
        b.use_connect = parent is not None
        parent = b
    bpy.ops.object.mode_set(mode="OBJECT")
    for name, lo, hi in (("Hips", -1, 0.8), ("Spine", 0.8, 1.5), ("Head", 1.5, 3)):
        vg = body.vertex_groups.new(name=name)
        vg.add([v.index for v in body.data.vertices if lo <= v.co.z < hi], 1.0, "REPLACE")
    body.modifiers.new("Armature", "ARMATURE").object = rig
    body.parent = rig
    body.shape_key_add(name="Basis")
    key = body.shape_key_add(name="jawOpen")
    for v in key.data:
        if v.co.z > 1.8:
            v.co.x *= 1.3
    pb = rig.pose.bones["Spine"]
    for frame, angle in ((1, 0.0), (12, 0.6), (24, 0.0)):
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (angle, 0, 0)
        pb.keyframe_insert("rotation_euler", frame=frame)
    rig.animation_data.action.name = "Wave"
    return body, rig


def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    c = crate()
    body, rig = character()
    rig.location.x = 2.0
    return c, body, rig


cases = {"exports": {}}
scene()
before = {"static": bxe.inspect_scene(["Crate"]), "rigged": bxe.inspect_scene(["Rig", "Body"])}
files = {}
for preset in STATIC + RIGGED:
    ext = bxe.PRESETS[preset][0]
    path = os.path.join(TMP, preset + ext)
    objs = ["Crate"] if preset in STATIC else ["Rig", "Body"]
    cases["exports"][preset] = bxe.export(path, preset, objs)
    files[preset] = path

# round_trip() itself: a background Blender, the open scene untouched.
rt = bxe.round_trip(files["godot"], ["Rig", "Body"], preset="godot")
cases["round_trip_godot"] = {"pass": rt["pass"], "diffs": rt["diffs"],
                             "scene_kept": "Crate" in bpy.data.objects}

# Roblox exports no animation unless asked: with bake_anim=True the clip travels, and
# round_trip() given the same override compares actions.
anim_fbx = os.path.join(TMP, "roblox_anim.fbx")
bxe.export(anim_fbx, "roblox", ["Rig", "Body"], bake_anim=True)
rt = bxe.round_trip(anim_fbx, ["Rig", "Body"], preset="roblox", bake_anim=True)
cases["roblox_anim"] = {"pass": rt["pass"], "diffs": rt["diffs"], "actions": rt["after"]["actions"]}
rt = bxe.round_trip(files["roblox"], ["Rig", "Body"], preset="roblox", bake_anim=True)
cases["roblox_no_anim"] = {"pass": rt["pass"], "diffs": rt["diffs"]}
try:
    bxe.lods("Body")
    cases["lods_skinned"] = "made"
except ValueError as exc:
    cases["lods_skinned"] = str(exc)

# LODs and collision, exported together for Unity and Unreal.
bxe.lods("Crate", ratios=(0.5, 0.25))
cases["lods"] = bxe.inspect_scene([o for o in bpy.data.objects if o.name.startswith("Crate_LOD")])
lod_fbx = os.path.join(TMP, "lods.fbx")
bxe.export(lod_fbx, "unity", ["Crate", "Crate_LOD0", "Crate_LOD1", "Crate_LOD2"])
scene()
cases["collision_unreal"] = bxe.collision("Crate", "unreal")
cases["collision_godot"] = bxe.collision("Crate", "godot")
cases["collision_unity"] = bxe.collision("Crate", "unity")
ucx_fbx = os.path.join(TMP, "ucx.fbx")
bxe.export(ucx_fbx, "unreal", ["Crate", "UCX_Crate_00"])
scene()
cases["collision_godot_box"] = bxe.collision("Crate", "godot", "box")
scene()
cases["collision_godot_mesh"] = bxe.collision("Crate", "godot", "mesh")

cases["roundtrip"] = {}
for preset, path in files.items():
    after = bxe.inspect_file(path)
    kind = "static" if preset in STATIC else "rigged"
    cases["roundtrip"][preset] = {
        "diffs": bxe.compare(before[kind], after, bxe.CARRIES[preset], scale=bxe.SCALE.get(preset, 1.0)),
        "after": after,
    }
cases["lods_file"] = sorted(bxe.inspect_file(lod_fbx)["objects"])
cases["ucx_file"] = sorted(bxe.inspect_file(ucx_fbx)["objects"])
cases["glb_godot"] = bxe.glb_summary(files["godot"])
cases["glb_web"] = bxe.glb_summary(files["web"])
cases["usdz_members"] = zipfile.ZipFile(files["usdz"]).namelist()

# batch(): a folder holding the static GLB, gated and converted for Godot.
src = os.path.join(TMP, "batch_in")
os.makedirs(src)
os.replace(files["gltf"], os.path.join(src, "crate.glb"))
cases["batch"] = bxe.batch(src, os.path.join(TMP, "batch_out"), "godot")
# A review render, then its camera removed: the view layer keeps a None entry
# until its next update, and export() must still work.
bpy.ops.wm.read_factory_settings(use_empty=True)
crate()
cam = bpy.data.objects.new("ReviewCam", bpy.data.cameras.new("ReviewCam"))
sc = bpy.context.scene
sc.collection.objects.link(cam)
sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.render.resolution_x = sc.render.resolution_y = 32
sc.render.filepath = os.path.join(TMP, "review.png")
bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(cam)
cases["after_render"] = bxe.export(os.path.join(TMP, "after_render.glb"), "godot", ["Crate"])["bytes"]

# lods() on a mesh under a moved, turned parent: every LOD keeps the mesh's world place, and
# the group takes the mesh's place under the parent.
def world_center(ob):
    return [round(sum((ob.matrix_world @ Vector(c))[k] for c in ob.bound_box) / 8, 4) for k in range(3)]


bpy.ops.wm.read_factory_settings(use_empty=True)
c = crate()
base = bpy.data.objects.new("Base", None)
bpy.context.scene.collection.objects.link(base)
base.location, base.rotation_euler = (3, 1, 0), (0, 0, 0.5)
c.parent = base
bpy.context.view_layer.update()
start = world_center(c)
r = bxe.lods("Crate", ratios=(0.5,))
bpy.context.view_layer.update()
cases["lods_parented"] = {"start": start, "group_parent": bpy.data.objects[r["group"]].parent.name,
                          "centers": {n: world_center(bpy.data.objects[n]) for n in r["tris"]}}

# A packed image with no path, as a glTF import leaves it: the FBX must name it with an
# extension, and the scene must keep its own path.
bpy.ops.wm.read_factory_settings(use_empty=True)
mat = crate().data.materials[0]
if mat.node_tree is None:
    mat.use_nodes = True
gen = bpy.data.images.new("gen", 8, 8)
gen.filepath_raw, gen.file_format = os.path.join(TMP, "gen.png"), "PNG"
gen.save()
img = bpy.data.images.load(os.path.join(TMP, "gen.png"))
img.pack()
img.filepath_raw, img.name = "", "Image_0"
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bxe.export(os.path.join(TMP, "packed.fbx"), "unity", ["Crate"])
data, rel, i = open(os.path.join(TMP, "packed.fbx"), "rb").read(), set(), 0
while (i := data.find(b"RelativeFilenameS", i)) >= 0:
    n = int.from_bytes(data[i + 17:i + 21], "little")
    rel.add(data[i + 21:i + 21 + n].decode())
    i += 21 + n
cases["packed_fbx"] = {"relative": sorted(rel), "filepath_after": img.filepath_raw}

cases["spine_angle_deg"] = round(math.degrees(0.6), 1)

with open(OUT, "w") as f:
    json.dump(cases, f, indent=1)
print("EXPORT CASES", len(cases))
