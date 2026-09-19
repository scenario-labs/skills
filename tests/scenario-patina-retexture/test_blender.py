"""Smoke test against a real bpy module. Skipped where Blender's Python module is absent.

bpy cannot be re-imported after a crash, so everything runs in one TestCase and one test
method, stage by stage, with no rendering (no display or GPU is assumed).
"""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import helpers

HAS_BPY = importlib.util.find_spec("bpy") is not None

MAP_COLORS = {
    "basecolor": (180, 150, 120),
    "normal": (128, 128, 255),
    "roughness": (128, 128, 128),
    "metalness": (0, 0, 0),
    "height": (128, 128, 128),
}


def write_maps(root, family):
    folder = Path(root) / "textures" / family
    folder.mkdir(parents=True, exist_ok=True)
    maps = {}
    for role, color in MAP_COLORS.items():
        path = folder / f"{role}.png"
        Image.new("RGB", (8, 8), color).save(path)
        maps[role] = str(path.relative_to(root))
    return maps


@unittest.skipUnless(HAS_BPY, "bpy module not installed")
class BlenderPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.root = Path(cls.folder.name)
        cls.common = helpers.load("common")
        cls.inventory = helpers.load("inventory")
        cls.apply_materials = helpers.load("apply_materials")
        cls.scene = helpers.load("scene")

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def build_source(self):
        import bpy

        bpy.ops.wm.read_factory_settings(use_empty=True)
        cubes = (
            ("WallCube", (0, 0, 0), (0.8, 0.1, 0.1, 1)),
            ("TrimCube", (3, 0, 0), (0.1, 0.2, 0.9, 1)),
        )
        for name, location, color in cubes:
            bpy.ops.mesh.primitive_cube_add(size=1, location=location)
            obj = bpy.context.object
            obj.name = name
            material = bpy.data.materials.new(name.replace("Cube", ""))
            tree = self.apply_materials.ensure_nodes(material)
            bsdf = next(n for n in tree.nodes if n.type == "BSDF_PRINCIPLED")
            bsdf.inputs["Base Color"].default_value = color
            obj.data.materials.append(material)
        source = self.root / "source.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(source))
        return source

    def quiet(self, function, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            result = function(*args)
        return result, out.getvalue()

    def test_pipeline(self):
        import bpy

        source = self.build_source()
        out_dir = self.root / "inventory"

        with self.subTest("inventory"):
            report, printed = self.quiet(self.inventory.main, [str(source), str(out_dir)])
            self.assertEqual(json.loads(printed.strip().splitlines()[-1]), report)
            self.assertEqual(json.loads((out_dir / "inventory.json").read_text()), report)
            self.assertTrue((out_dir / "Before.blend").is_file())
            self.assertEqual(report["source"], str(source))
            self.assertEqual(report["meshes"], 2)
            self.assertEqual(report["polygons"], 12)
            self.assertEqual(len(report["dimensions"]), 3)
            self.assertAlmostEqual(report["dimensions"][0], 4.0, places=5)
            self.assertAlmostEqual(report["dimensions"][1], 1.0, places=5)
            self.assertEqual(len(report["geometry_sha256"]), 64)
            self.assertEqual(report["objects_without_material"], [])
            self.assertEqual(set(report["materials"]), {"Wall", "Trim"})
            wall = report["materials"]["Wall"]
            self.assertEqual(wall["objects"], 1)
            self.assertEqual(wall["examples"], ["WallCube"])
            self.assertAlmostEqual(wall["base_color"][0], 0.8, places=5)
            self.assertFalse(wall["has_image_textures"])
            self.assertAlmostEqual(wall["bounds"]["lo"][0], -0.5, places=5)
            self.assertAlmostEqual(report["materials"]["Trim"]["bounds"]["hi"][0], 3.5, places=5)
            with self.assertRaises(FileExistsError):
                self.inventory.main([str(source), str(out_dir)])

        manifest_path = self.root / "materials.json"
        manifest = {
            "output": "PATINA.blend",
            "materials": {"Wall": "plaster"},
            "object_overrides": [{"prefixes": ["TrimCube"], "family": "cedar"}],
            "families": {
                "plaster": {"tile_span": 1.2, "maps": write_maps(self.root, "plaster")},
                "cedar": {
                    "tile_span": 0.7,
                    "basecolor_mode": "replace",
                    "roughness_is_smoothness": True,
                    "roughness": [0.35, 0.75],
                    "maps": write_maps(self.root, "cedar"),
                },
            },
            "provenance": {"jobs": ["job_1", "job_2"], "model": "recorded by the agent"},
        }
        manifest_path.write_text(json.dumps(manifest))

        with self.subTest("apply_materials"):
            bpy.ops.wm.open_mainfile(filepath=str(out_dir / "Before.blend"))
            result, printed = self.quiet(self.apply_materials.main, [str(manifest_path)])
            self.assertEqual(json.loads(printed.strip().splitlines()[-1]), result)
            output = Path(result["output"])
            self.assertEqual(output, self.root / "PATINA.blend")
            self.assertTrue(output.is_file())
            self.assertTrue(result["geometry_preserved"])
            self.assertEqual(result["material_variants"], 2)
            self.assertEqual(result["packed_images"], 10)
            written = json.loads((self.root / "PATINA.materials.json").read_text())
            self.assertEqual(written["geometry_sha256_before"], report["geometry_sha256"])
            self.assertEqual(written["geometry_sha256_after"], report["geometry_sha256"])
            self.assertEqual(len(written["materials"]), 2)
            by_family = {m["family"]: m for m in written["materials"]}
            self.assertEqual(by_family["plaster"]["basecolor_mode"], "tint")
            self.assertGreater(by_family["plaster"]["basecolor_mean_linear"], 0.02)
            self.assertEqual(by_family["cedar"]["basecolor_mode"], "replace")
            self.assertIsNone(by_family["cedar"]["basecolor_mean_linear"])

        with self.subTest("reopen output"):
            bpy.ops.wm.open_mainfile(filepath=str(self.root / "PATINA.blend"))
            meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
            self.assertEqual(len(meshes), 2)
            names = {}
            for obj in meshes:
                self.assertIn("PatinaUV", obj.data.uv_layers)
                for slot in obj.material_slots:
                    self.assertTrue(slot.material.name.startswith("PATINA | "), slot.material.name)
                    names[obj.name] = slot.material.name
                    self.assertEqual(
                        json.loads(slot.material["patina_provenance"]), manifest["provenance"]
                    )
            self.assertEqual(
                names, {"WallCube": "PATINA | Wall", "TrimCube": "PATINA | Trim | cedar"}
            )
            wall = bpy.data.materials["PATINA | Wall"]
            self.assertEqual(wall["patina_family"], "plaster")
            base = wall.node_tree.nodes["PATINA Surface"].inputs["Base Color"].links[0].from_node
            self.assertEqual(base.name, "Original Palette")
            trim = bpy.data.materials["PATINA | Trim | cedar"]
            base = trim.node_tree.nodes["PATINA Surface"].inputs["Base Color"].links[0].from_node
            self.assertEqual(base.name, "PATINA basecolor")
            self.assertIn("Convert Smoothness To Roughness", trim.node_tree.nodes)
            remap = trim.node_tree.nodes["Calibrated roughness"]
            self.assertEqual(remap.inputs["To Max"].default_value, 0.75)
            for image in bpy.data.images:
                if image.name.startswith("PATINA | "):
                    self.assertIsNotNone(image.packed_file, image.name)
            self.assertEqual(
                self.common.geometry_hash(meshes), report["geometry_sha256"]
            )

        environment = self.root / "environment.png"
        Image.new("RGB", (16, 8), (200, 200, 220)).save(environment)
        config, _ = self.common.read_config(
            helpers.write_config(
                self.root,
                before="inventory/Before.blend",
                after="PATINA.blend",
                shots=[helpers.shot("Detail", 2.0, 1.5)],
                shot_seconds=1.0,
                width=64,
                height=36,
                environment=str(environment),
            )
        )

        with self.subTest("scene setup in pilot mode"):
            scene, records, contract = self.scene.setup(config, "patina", preview=True)
            self.assertEqual(scene.camera.name, self.scene.CAMERA_NAME)
            lights = sorted(o.name for o in scene.objects if o.type == "LIGHT")
            self.assertEqual(len(lights), 4)
            self.assertIn(self.scene.STRIP_NAME, lights)
            self.assertEqual(len(records), 24)
            self.assertEqual(scene.frame_end, 24)
            self.assertEqual(scene.render.resolution_percentage, 50)
            self.assertIn(scene.render.engine, ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"))
            self.assertEqual(contract["pass_name"], "patina")
            self.assertEqual(len(contract["camera_sha256"]), 64)
            self.assertEqual(contract["geometry_sha256"], report["geometry_sha256"])
            self.assertIn("environment.png", contract["settings"]["environment"])
            self.assertEqual(len(contract["settings"]["lights"]), 4)

        with self.subTest("before pass produces the same contract"):
            bpy.ops.wm.open_mainfile(filepath=str(out_dir / "Before.blend"))
            _, _, other = self.scene.setup(config, "original", preview=True)
            for key in ("camera_sha256", "settings", "geometry_sha256"):
                self.assertEqual(other[key], contract[key], key)

        with self.subTest("manifest problems stop before the scene changes"):
            bpy.ops.wm.open_mainfile(filepath=str(out_dir / "Before.blend"))
            bad = {
                "output": "Rejected.blend",
                "materials": {"Wall": "plaster"},
                "families": {"plaster": {"tile_span": 1, "maps": {"basecolor": "missing.png"}}},
            }
            bad_path = self.root / "bad.json"
            bad_path.write_text(json.dumps(bad))
            with self.assertRaises(SystemExit) as caught:
                self.apply_materials.main([str(bad_path)])
            message = str(caught.exception)
            self.assertIn("material 'Trim' is neither mapped", message)
            self.assertIn("missing map roles", message)
            self.assertIn("basecolor map missing.png not found", message)
            self.assertFalse((self.root / "Rejected.blend").exists())
            self.assertNotIn("PatinaUV", bpy.data.objects["WallCube"].data.uv_layers)


if __name__ == "__main__":
    unittest.main()
