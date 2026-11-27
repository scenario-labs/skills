"""Offline tests for scenario-3dsmax-uv-baking scripts, with no 3ds Max installed.

maxkit_uv.analyze and bake_check are pure Python. bake_check needs Pillow (requirements.txt);
its tests skip without it.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-uv-baking" / "scripts"
sys.path[:0] = [str(SCRIPTS)]

import bake_check  # noqa: E402
import maxkit_uv  # noqa: E402

HAVE_PIL = importlib.util.find_spec("PIL") is not None
RASTER = 64


def rules(report):
    return {f["rule"] for f in report["findings"]}


def analyze(faces):
    return maxkit_uv.analyze(faces, 1.0, tex_size=256, raster=RASTER, min_pad_px=0)


class UvAnalyze(unittest.TestCase):
    def test_triangle_fully_outside_is_reported(self):
        rep = analyze([(1.0, [1, 2, 3], [(3, .1), (3.5, .1), (3, .6)])])
        self.assertIn("uv.outside_0_1", rules(rep))
        self.assertEqual(rep["outside_0_1_faces"], 1)

    def test_overlap_inside_one_shell_is_reported(self):
        tri = [(.1, .1), (.9, .1), (.1, .9)]
        rep = analyze([(1.0, [1, 2, 3], tri), (1.0, [1, 4, 5], tri)])
        self.assertEqual(rep["shells"], 1)
        self.assertGreater(rep["overlap_pct"], 0)
        self.assertIn("uv.overlap", rules(rep))

    def test_quad_split_on_a_diagonal_is_not_an_overlap(self):
        a, b, c, d = (.1, .1), (.9, .1), (.9, .9), (.1, .9)
        rep = analyze([(1.0, [1, 2, 3], [a, b, c]), (1.0, [1, 3, 4], [a, c, d])])
        self.assertEqual(rep["overlap_pct"], 0)
        self.assertNotIn("uv.overlap", rules(rep))

    def test_concave_face_leaves_its_notch_empty(self):
        notch = [(0, 0), (1, 0), (1, 1), (.7, 1), (.7, .3), (.3, .3), (.3, 1), (0, 1)]
        inside = [(.4, .5), (.6, .5), (.5, .9)]
        rep = analyze([(1.0, list(range(1, 9)), notch), (1.0, [20, 21, 22], inside)])
        self.assertEqual(rep["shells"], 2)
        self.assertEqual(rep["overlap_pct"], 0)

    def test_triangulate_covers_the_polygon_area(self):
        notch = [(0, 0), (1, 0), (1, 1), (.7, 1), (.7, .3), (.3, .3), (.3, 1), (0, 1)]
        tris = maxkit_uv.triangulate(notch)
        self.assertEqual(len(tris), len(notch) - 2)
        area = sum(abs(maxkit_uv.signed_area([notch[i] for i in t])) for t in tris)
        self.assertAlmostEqual(area, abs(maxkit_uv.signed_area(notch)))

    def test_inside_layout_has_no_outside_finding(self):
        rep = analyze([(1.0, [1, 2, 3], [(.1, .1), (.5, .1), (.1, .5)])])
        self.assertEqual(rep["outside_0_1_faces"], 0)
        self.assertNotIn("uv.outside_0_1", rules(rep))


@unittest.skipUnless(HAVE_PIL, "needs Pillow")
class BakeCheckSample(unittest.TestCase):
    def test_sample_matches_every_step_pixel(self):
        from PIL import Image
        im = Image.new("RGB", (7, 5))
        im.putdata([(i % 256, (3 * i) % 256, (7 * i) % 256) for i in range(35)])
        everything = [im.getpixel((i % 7, i // 7)) for i in range(35)]
        for step in (1, 2, 3, 4, 6):
            self.assertEqual(bake_check.sample(im, step), everything[::step])


if __name__ == "__main__":
    unittest.main()
