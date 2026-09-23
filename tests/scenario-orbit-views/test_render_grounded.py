import math
import unittest

import _paths  # noqa: F401
import render_grounded as rg


class ParseArgsTests(unittest.TestCase):
    def test_defaults_and_values(self):
        o = rg.parse_args(["blender", "--", "--glb", "m.glb", "--pano", "p.png", "--out", "o",
                           "--az0", "30", "--size", "512", "--only", "00,top"])
        self.assertEqual(o["az0"], 30.0)
        self.assertEqual(o["size"], 512)
        self.assertIsInstance(o["size"], int)
        self.assertEqual(o["only"], {"00", "top"})
        self.assertEqual(o["elev"], 8.0)
        self.assertFalse(o["search"])

    def test_search_does_not_need_a_panorama(self):
        o = rg.parse_args(["--glb", "m.glb", "--out", "o", "--search"])
        self.assertTrue(o["search"])

    def test_missing_panorama_and_unknown_flag_fail(self):
        with self.assertRaises(SystemExit):
            rg.parse_args(["--glb", "m.glb", "--out", "o"])
        with self.assertRaises(SystemExit):
            rg.parse_args(["--glb", "m.glb", "--out", "o", "--pano", "p", "--bogus", "1"])


class CameraTests(unittest.TestCase):
    def test_twenty_five_named_cameras(self):
        cams = rg.camera_list(30, 10, -8)
        self.assertEqual(len(cams), 25)
        keys = [c[0] for c in cams]
        self.assertEqual(keys[0], "00")
        self.assertIn("high_08", keys)
        self.assertIn("low_12", keys)
        self.assertEqual(keys[-1], "top")
        self.assertEqual(dict((k, (a, e)) for k, a, e in cams)["04"], (30 + 90, 10))
        self.assertEqual(dict((k, e) for k, a, e in cams)["low_00"], -8)

    def test_only_filters(self):
        self.assertEqual([c[0] for c in rg.camera_list(0, 8, -10, {"top", "00"})], ["00", "top"])

    def test_search_grid(self):
        grid = rg.search_list()
        self.assertEqual(len(grid), 19 * 4)
        self.assertEqual(grid[0][1:], (-90.0, 0.0))

    def test_distance_is_constant_and_zoom_moves_closer(self):
        d1 = rg.camera_distance((1, 1, 2))
        self.assertAlmostEqual(rg.camera_distance((1, 1, 2), zoom=2.0), d1 / 2)
        self.assertGreater(d1, 1.0)

    def test_position_orbits_at_distance_and_stays_above_floor(self):
        c = (0, 0, 1)
        x, y, z = rg.camera_position(c, 5, 0, 0)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, -5)
        x, y, z = rg.camera_position(c, 5, 90, 0)
        self.assertAlmostEqual(x, 5)
        self.assertAlmostEqual(math.dist((x, y, z), c), 5)
        self.assertGreaterEqual(rg.camera_position(c, 5, 0, -89)[2], 0.05)


if __name__ == "__main__":
    unittest.main()
