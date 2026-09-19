import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import helpers

scene = helpers.load("scene")


def length(vector):
    return math.sqrt(sum(v * v for v in vector))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


class EasingTests(unittest.TestCase):
    def test_smoothstep_endpoints_and_midpoint(self):
        self.assertEqual(scene.smoothstep(0), 0)
        self.assertEqual(scene.smoothstep(1), 1)
        self.assertAlmostEqual(scene.smoothstep(0.5), 0.5)
        self.assertLess(scene.smoothstep(0.25), 0.25)
        self.assertGreater(scene.smoothstep(0.75), 0.75)

    def test_ease_at_spans_the_shot(self):
        self.assertEqual(scene.ease_at(0, 132), 0)
        self.assertEqual(scene.ease_at(131, 132), 1)
        self.assertEqual(scene.ease_at(0, 1), 0)


class CameraTests(unittest.TestCase):
    start = [[0, 0, 4], [-0.5, -1, 0.5], 20]
    end = [[1, 0, 4], [0.5, -1, 0.5], 18]

    def test_distance_frames_the_visible_width(self):
        self.assertAlmostEqual(scene.camera_distance(36), 85)
        self.assertAlmostEqual(scene.camera_distance(20), 20 * 85 / 36)
        self.assertAlmostEqual(scene.camera_distance(10, lens=50, sensor_width=36), 10 * 50 / 36)

    def test_pose_sits_at_the_framing_distance_along_the_direction(self):
        for ease in (0, 0.3, 1):
            pose = scene.camera_pose(self.start, self.end, ease)
            offset = sub(pose["location"], pose["target"])
            self.assertAlmostEqual(length(offset), scene.camera_distance(pose["width"]))
            self.assertAlmostEqual(length(pose["direction"]), 1)
            for o, d in zip(offset, pose["direction"]):
                self.assertAlmostEqual(o / length(offset), d)

    def test_pose_endpoints_match_the_shot(self):
        first = scene.camera_pose(self.start, self.end, 0)
        last = scene.camera_pose(self.start, self.end, 1)
        self.assertEqual(first["target"], (0, 0, 4))
        self.assertEqual(last["target"], (1, 0, 4))
        self.assertAlmostEqual(first["width"], 20)
        self.assertAlmostEqual(last["width"], 18)

    def test_camera_looks_at_the_target(self):
        pose = scene.camera_pose(self.start, self.end, 0.5)
        view = sub(pose["target"], pose["location"])
        cosine = sum(v * d for v, d in zip(view, pose["direction"])) / length(view)
        self.assertAlmostEqual(cosine, -1)


class LightTests(unittest.TestCase):
    def test_rig_light_scales_with_the_rig(self):
        one = scene.rig_light((-6, -7, 12), 1250, 4.0, (0, 0, 4.5), (0, 0, 0), 1, None)
        two = scene.rig_light((-6, -7, 12), 1250, 4.0, (0, 0, 4.5), (1, 2, 3), 2, 3)
        self.assertEqual(one["location"], (-6, -7, 12))
        self.assertEqual(two["location"], (-11, -12, 27))
        self.assertEqual(two["target"], (1, 2, 12))
        self.assertEqual(two["power"], 1250 * 4)
        self.assertEqual(two["size"], 8.0)
        self.assertEqual(two["size_y"], 6)
        self.assertIsNone(one["size_y"])

    def test_strip_pose_depends_on_rig_scale(self):
        target, direction = (0, 0, 1), (0, -1, 0)
        small = scene.strip_pose(target, direction, 2.0, 0.5, 1)
        large = scene.strip_pose(target, direction, 4.0, 0.5, 2)
        for s, l in zip(sub(small["location"], target), sub(large["location"], target)):
            self.assertAlmostEqual(l, 2 * s)
        self.assertAlmostEqual(large["energy"], 4 * small["energy"])
        self.assertAlmostEqual(large["size"], 2 * small["size"])
        self.assertAlmostEqual(large["size_y"], 2 * small["size_y"])

    def test_strip_switches_between_close_up_and_wide(self):
        close = scene.strip_pose((0, 0, 0), (0, -1, 0), 5.9, 0, 1)
        wide = scene.strip_pose((0, 0, 0), (0, -1, 0), 6.0, 0, 1)
        self.assertAlmostEqual(length(sub(close["location"], (0, 0, 4.5 * 0.48))), 4.5)
        self.assertAlmostEqual(length(sub(wide["location"], (0, 0, 11 * 0.48))), 11)
        self.assertLess(close["energy"], wide["energy"])

    def test_strip_sweeps_ninety_degrees(self):
        target, direction = (0, 0, 0), (0, -1, 0)
        first = scene.strip_pose(target, direction, 2.0, 0, 1)["location"]
        last = scene.strip_pose(target, direction, 2.0, 1, 1)["location"]
        first, last = first[:2], last[:2]
        dot = sum(a * b for a, b in zip(first, last))
        self.assertAlmostEqual(dot / (length(first) * length(last)), 0)


class PickerTests(unittest.TestCase):
    def test_engine_prefers_the_current_identifier(self):
        self.assertEqual(scene.pick_engine(["BLENDER_EEVEE", "CYCLES"]), "BLENDER_EEVEE")
        self.assertEqual(scene.pick_engine(["BLENDER_EEVEE_NEXT", "CYCLES"]), "BLENDER_EEVEE_NEXT")

    def test_look_accepts_both_naming_schemes(self):
        legacy = "AgX - Medium High Contrast"
        self.assertEqual(scene.pick_look(["None", legacy]), legacy)
        self.assertEqual(scene.pick_look(["None", "Medium High Contrast"]), "Medium High Contrast")
        self.assertEqual(scene.pick_look(["None", "High Contrast"]), "None")

    def test_set_present_only_touches_existing_attributes(self):
        target = SimpleNamespace(a=1)
        applied = scene.set_present(target, {"a": 2, "b": 3})
        self.assertEqual(applied, {"a": 2})
        self.assertEqual(target.a, 2)
        self.assertFalse(hasattr(target, "b"))


class EnvironmentTests(unittest.TestCase):
    def test_configured_path(self):
        with tempfile.TemporaryDirectory() as folder:
            hdri = Path(folder) / "studio.hdr"
            hdri.write_bytes(b"x")
            self.assertEqual(scene.find_environment(str(hdri), []), hdri)
            with self.assertRaises(FileNotFoundError):
                scene.find_environment(str(Path(folder) / "missing.exr"), [])

    def test_bundled_search_prefers_studio(self):
        with tempfile.TemporaryDirectory() as folder:
            world = Path(folder) / "5.0" / "datafiles" / "studiolights" / "world"
            world.mkdir(parents=True)
            (world / "city.exr").write_bytes(b"x")
            self.assertEqual(scene.find_environment(None, ["", folder]), world / "city.exr")
            (world / "studio.exr").write_bytes(b"x")
            self.assertEqual(scene.find_environment(None, [folder, ""]), world / "studio.exr")

    def test_nothing_found_tells_the_user_what_to_set(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError) as caught:
                scene.find_environment(None, [folder, "", None])
        self.assertIn("environment", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
