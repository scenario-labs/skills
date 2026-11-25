"""Offline tests for scenario-3dsmax-materials scripts, with no 3ds Max installed.

maxkit_materials runs against a stand-in runtime: passing tests prove the Python logic only.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-materials" / "scripts"
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

import maxkit_materials  # noqa: E402  (imports the fake pymxs)
import pbr_set  # noqa: E402


class _TmpCase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="max_mat_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)


class PbrSet(_TmpCase):
    def test_seam_preview_refuses_existing_output_without_pillow(self):
        out = self.dir / "tile.png"
        out.write_bytes(b"keep")
        with mock.patch.dict(sys.modules, {"PIL": None}), self.assertRaises(FileExistsError):
            pbr_set.seam_preview(str(self.dir / "in.png"), str(out))
        self.assertEqual(out.read_bytes(), b"keep")

    def test_seam_preview_returns_command_without_pillow(self):
        with mock.patch.dict(sys.modules, {"PIL": None}):
            cmd = pbr_set.seam_preview("in.png", str(self.dir / "new.png"))
        self.assertTrue(cmd.startswith("magick montage"))

    def test_role_reads_the_last_role_token(self):
        self.assertEqual(pbr_set._role("brushed_metal_basecolor_2k"), "base_color")


class _Rt:
    def __init__(self, unit="#centimeters", scale=1.0, textures=(), vray=(), props=None, existing=()):
        self.units = SimpleNamespace(SystemType=unit, SystemScale=scale)
        self._textures = list(textures)
        self._vray = list(vray)
        self._props = props or {}
        self.Bitmaptexture = "Bitmaptexture"
        self.textureMap = SimpleNamespace(classes=["VRayBitmap"] if vray else [])

    def getClassInstances(self, cls):
        return self._textures if cls == "Bitmaptexture" else self._vray

    def isProperty(self, obj, name):
        return name in self._props.get(id(obj), {})

    def getPropNames(self, obj):
        return list(self._props.get(id(obj), {}))

    def getProperty(self, obj, name):
        value = self._props[id(obj)][name]
        if isinstance(value, Exception):
            raise value
        return value


class _Unreadable:
    name = "tex"

    def __init__(self, filename):
        self.filename = filename

    @property
    def bitmap(self):
        raise RuntimeError("cannot load")


class MaxkitMaterials(_TmpCase):
    def test_unit_scale_includes_system_scale_and_miles(self):
        cases = [("#centimeters", 1.0, 1.0), ("#centimeters", 10.0, 0.1), ("#millimeters", 1.0, 10.0),
                 ("#meters", 1.0, 0.01), ("#miles", 1.0, 1 / 160934.4)]
        for unit, scale, want in cases:
            with mock.patch.object(maxkit_materials, "rt", _Rt(unit, scale)):
                self.assertAlmostEqual(maxkit_materials._unit_scale_to_cm(), want)

    def test_unreadable_color_space_is_an_error(self):
        f = self.dir / "wood_roughness.png"
        f.write_bytes(b"x")
        with mock.patch.object(maxkit_materials, "rt", _Rt(textures=[_Unreadable(str(f))])):
            out = maxkit_materials.audit_textures()
        self.assertEqual([(o["severity"], o["rule"]) for o in out], [("error", "colorspace_unreadable")])

    def test_vraybitmap_missing_file_and_unread_name_are_errors(self):
        missing = SimpleNamespace(name="vb1")
        unread = SimpleNamespace(name="vb2")
        props = {id(missing): {"HDRIMapName": str(self.dir / "oak_basecolor_srgb.png")},
                 id(unread): {"HDRIMapName": RuntimeError("no value")}}
        with mock.patch.object(maxkit_materials, "rt", _Rt(vray=[missing, unread], props=props)):
            out = maxkit_materials.audit_textures()
        self.assertEqual([(o["node"], o["rule"]) for o in out],
                         [("vb1", "missing_map"), ("vb2", "vraybitmap_unreadable")])

    def test_vraybitmap_existing_tagged_file_passes(self):
        f = self.dir / "oak_basecolor_srgb.png"
        f.write_bytes(b"x")
        vb = SimpleNamespace(name="vb")
        with mock.patch.object(maxkit_materials, "rt", _Rt(vray=[vb], props={id(vb): {"HDRIMapName": str(f)}})):
            self.assertEqual(maxkit_materials.audit_textures(), [])

    def test_color_role_wins_over_asset_name(self):
        self.assertEqual(maxkit_materials._role_from_name("brushed_metal_basecolor_srgb.png"), "color")

    def test_gltf_flip_green_leaves_normal_unwired(self):
        mat = SimpleNamespace(name="m")
        fake = _Rt()
        fake.classOf = lambda m: "glTFMaterial"
        with mock.patch.object(maxkit_materials, "rt", fake), \
                mock.patch.object(maxkit_materials, "_new_material", return_value=mat), \
                mock.patch.object(maxkit_materials, "load_texture", return_value=(object(), {})):
            _, rep = maxkit_materials.build_material("gltf", {"normal": "n_dx.png"}, "m", flip_green=True)
        self.assertNotIn("property", rep["slots"]["normal"])
        self.assertTrue(any(w.startswith("flip_green") for w in rep["warnings"]))


if __name__ == "__main__":
    unittest.main()
