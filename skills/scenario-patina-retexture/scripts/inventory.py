"""Import a 3D asset into Blender, save a packed Before.blend and summarize its materials.

    blender --background --factory-startup --python scripts/inventory.py -- <source> <out_dir>

<source> is a .glb, .gltf, .obj, .fbx or .blend file. The summary is what the agent
groups into material families; it never dumps geometry.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import dump, geometry_hash  # noqa: E402

IMPORTERS = {
    ".glb": ("import_scene", "gltf"),
    ".gltf": ("import_scene", "gltf"),
    ".obj": ("wm", "obj_import"),
    ".fbx": ("import_scene", "fbx"),
}


def load_source(source: Path):
    import bpy

    suffix = source.suffix.lower()
    if suffix == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(source))
        return
    if suffix not in IMPORTERS:
        raise ValueError(f"{source.name}: expected .glb, .gltf, .obj, .fbx or .blend")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    module, operator = IMPORTERS[suffix]
    getattr(getattr(bpy.ops, module), operator)(filepath=str(source))


def principled_node(material):
    if material.node_tree is None:
        return None
    return next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def material_base_color(material):
    """Principled Base Color default, else the viewport diffuse color, else None."""
    node = principled_node(material)
    if node is not None:
        return [round(v, 6) for v in node.inputs["Base Color"].default_value]
    if hasattr(material, "diffuse_color"):
        return [round(v, 6) for v in material.diffuse_color]
    return None


def has_image_textures(material) -> bool:
    if material.node_tree is None:
        return False
    return any(n.type == "TEX_IMAGE" and n.image is not None for n in material.node_tree.nodes)


def extend_bounds(bounds: dict, corners) -> None:
    for axis in range(3):
        values = [corner[axis] for corner in corners]
        bounds["lo"][axis] = min(bounds["lo"][axis], min(values))
        bounds["hi"][axis] = max(bounds["hi"][axis], max(values))


def new_bounds() -> dict:
    return {"lo": [float("inf")] * 3, "hi": [float("-inf")] * 3}


def world_corners(obj):
    from mathutils import Vector

    return [tuple(obj.matrix_world @ Vector(corner)) for corner in obj.bound_box]


def summarize(objects, source: Path) -> dict:
    materials = {}
    scene_bounds = new_bounds()
    without_material = []
    for obj in objects:
        corners = world_corners(obj)
        extend_bounds(scene_bounds, corners)
        slots = [slot.material for slot in obj.material_slots]
        if not slots or any(material is None for material in slots):
            without_material.append(obj.name)
        for material in slots:
            if material is None:
                continue
            entry = materials.setdefault(
                material.name,
                {
                    "objects": 0,
                    "examples": [],
                    "bounds": new_bounds(),
                    "base_color": material_base_color(material),
                    "has_image_textures": has_image_textures(material),
                },
            )
            entry["objects"] += 1
            if len(entry["examples"]) < 3:
                entry["examples"].append(obj.name)
            extend_bounds(entry["bounds"], corners)
    dimensions = [0.0, 0.0, 0.0]
    if objects:
        dimensions = [hi - lo for lo, hi in zip(scene_bounds["lo"], scene_bounds["hi"])]
    return {
        "source": str(source),
        "meshes": len(objects),
        "polygons": sum(len(obj.data.polygons) for obj in objects),
        "dimensions": dimensions,
        "geometry_sha256": geometry_hash(objects),
        "objects_without_material": without_material,
        "materials": materials,
    }


def main(argv: list[str]) -> dict:
    import bpy

    if len(argv) != 2:
        raise SystemExit("usage: ... --python inventory.py -- <source> <out_dir>")
    source = Path(argv[0]).resolve()
    out_dir = Path(argv[1]).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"{source} does not exist")
    before = out_dir / "Before.blend"
    report_path = out_dir / "inventory.json"
    for path in (before, report_path):
        if path.exists():
            raise FileExistsError(f"{path} exists; choose an empty output directory")
    load_source(source)
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    report = summarize(objects, source)
    out_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(before))
    report["before"] = str(before)
    report_path.write_text(json.dumps(report, indent=2))
    print(dump(report), flush=True)
    return report


def script_args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


if __name__ == "__main__":
    main(script_args())
