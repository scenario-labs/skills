"""Runs every bx_export preset in a real Blender and re-imports the files.

export_cases.py builds a crate and a skinned, animated character with a shape key,
exports them with each preset, re-imports every file and writes JSON; these tests read
it. Without Blender every test skips; .github/workflows/blender.yml installs Blender.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "blender" / "scenario-blender-export" / "scripts"


def find_blender():
    for path in (os.environ.get("BLENDER"), shutil.which("blender"),
                 "/Applications/Blender.app/Contents/MacOS/Blender"):
        if path and Path(path).is_file():
            return path
    return None


BLENDER = find_blender()


@unittest.skipUnless(BLENDER, "Blender is not installed")
class Presets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = tempfile.mkdtemp(prefix="bx_export_test_")
        out = Path(tmp) / "cases.json"
        run = subprocess.run(
            [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1",
             "-P", str(HERE / "export_cases.py"), "--", str(SCRIPTS), str(out), tmp],
            capture_output=True, text=True, timeout=900,
        )
        if run.returncode != 0:
            raise AssertionError(run.stdout[-3000:] + run.stderr[-3000:])
        cls.c = json.loads(out.read_text())
        shutil.rmtree(tmp, ignore_errors=True)

    def test_every_preset_round_trips(self):
        self.assertEqual(len(self.c["roundtrip"]), 11)
        for preset, r in self.c["roundtrip"].items():
            with self.subTest(preset=preset):
                self.assertEqual(r["diffs"], [])

    def test_rigged_presets_keep_bones_morphs_and_unit_scale(self):
        for preset in ("unity_skeletal", "unreal_skeletal", "roblox", "godot", "web"):
            with self.subTest(preset=preset):
                objs = self.c["roundtrip"][preset]["after"]["objects"]
                self.assertEqual(objs["Rig"]["bones"], 3)
                self.assertEqual(objs["Rig"]["scale"], [1.0, 1.0, 1.0])
                self.assertEqual(objs["Body"]["shape_keys"], ["jawOpen"])
                self.assertEqual(objs["Body"]["size"], [0.65, 0.5, 2.0])

    def test_animation_survives_where_the_preset_carries_it(self):
        for preset in ("unity_skeletal", "unreal_skeletal", "godot", "web"):
            with self.subTest(preset=preset):
                self.assertTrue(self.c["roundtrip"][preset]["after"]["actions"])

    def test_print_writes_millimeters(self):
        objs = self.c["roundtrip"]["print"]["after"]["objects"]
        self.assertEqual(sorted(next(iter(objs.values()))["size"]), [600.0, 700.0, 1000.0])

    def test_round_trip_runs_in_a_background_blender(self):
        r = self.c["round_trip_godot"]
        self.assertTrue(r["pass"], r["diffs"])
        self.assertTrue(r["scene_kept"])

    def test_glb_contents(self):
        g = self.c["glb_godot"]
        self.assertEqual(g["morph_targets"], {"Body": ["jawOpen"]})
        self.assertEqual(g["skins"], [3])
        self.assertEqual(g["animations"], ["Wave"])
        self.assertEqual(g["extensions_required"], [])
        w = self.c["glb_web"]
        self.assertIn("EXT_meshopt_compression", w["extensions_used"])
        self.assertLess(w["bytes"], g["bytes"])

    def test_lods_use_unity_names(self):
        tris = {k: v["tris"] for k, v in self.c["lods"]["objects"].items()}
        self.assertEqual(sorted(tris), ["Crate_LOD0", "Crate_LOD1", "Crate_LOD2"])
        self.assertGreater(tris["Crate_LOD0"], tris["Crate_LOD1"])
        self.assertGreater(tris["Crate_LOD1"], tris["Crate_LOD2"])
        self.assertEqual(self.c["lods_file"], ["Crate", "Crate_LOD0", "Crate_LOD1", "Crate_LOD2"])

    def test_collision_names(self):
        self.assertEqual(self.c["collision_unreal"]["object"], "UCX_Crate_00")
        self.assertEqual(self.c["collision_godot"]["object"], "Crate-convcolonly")
        self.assertIsNone(self.c["collision_unity"])
        self.assertEqual(self.c["ucx_file"], ["Crate", "UCX_Crate_00"])

    def test_usdz_is_a_package(self):
        self.assertTrue(any(m.endswith(".usdc") for m in self.c["usdz_members"]))

    def test_batch_gates_converts_and_checks(self):
        r = self.c["batch"]["files"]["crate.glb"]
        self.assertTrue(r["gate"]["pass"], r["gate"]["errors"])
        self.assertGreater(r["export"], 0)
        self.assertEqual(r["diffs"], [])

    def test_presets_write_the_documented_settings(self):
        s = self.c["exports"]["unity"]["settings"]
        self.assertEqual(s["apply_scale_options"], "FBX_SCALE_ALL")
        self.assertFalse(s["add_leaf_bones"])
        s = self.c["exports"]["roblox"]["settings"]
        self.assertEqual(s["apply_scale_options"], "FBX_SCALE_UNITS")
        self.assertEqual(s["path_mode"], "COPY")
        self.assertTrue(s["embed_textures"])


if __name__ == "__main__":
    unittest.main()
