"""Offline tests for scenario-3dsmax-archviz: archviz_plan and maxkit_archviz logic.

The fake pymxs in fakes/ stands in for 3ds Max: passing tests prove the Python logic only.
"""
from __future__ import annotations

import contextlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-archviz" / "scripts"
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

import pymxs  # noqa: E402  (the fake)
import archviz_plan as ap  # noqa: E402
import maxkit_archviz as ka  # noqa: E402
from pymxs import FakeNode  # noqa: E402

rt = pymxs.runtime


class AltitudeTests(unittest.TestCase):
    def test_relative_altitude_wins(self):
        alt, _ref = ap.camera_altitude({"RelativeAltitude": "+120.0", "GPSAltitude": 620})
        self.assertEqual(alt, 120.0)

    def test_gps_altitude_alone_is_missing(self):
        alt, ref = ap.camera_altitude({"GPSAltitude": 620})
        self.assertIsNone(alt)
        self.assertIn("site elevation", ref)

    def test_gps_altitude_minus_site_elevation(self):
        alt, _ref = ap.camera_altitude({"GPSAltitude": 620}, site_elevation_m=500)
        self.assertEqual(alt, 120.0)


class BudgetCliTests(unittest.TestCase):
    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                return ap._main(argv), out.getvalue()
            except SystemExit as exc:
                return exc.code, out.getvalue()

    def test_budget_without_workload_is_rejected(self):
        code, _out = self._run(["budget", "--spf", "540"])
        self.assertNotEqual(code, 0)

    def test_budget_with_both_is_rejected(self):
        code, _out = self._run(["budget", "--spf", "540", "--frames", "10", "--seconds", "2"])
        self.assertNotEqual(code, 0)

    def test_budget_with_seconds_runs(self):
        code, out = self._run(["budget", "--spf", "540", "--seconds", "20", "--fps", "25"])
        self.assertEqual(code, 0)
        self.assertIn('"frames": 500', out)


class _Shape:
    def __init__(self, name, count):
        self.name, self.count = name, count


class MaxkitArchvizTests(unittest.TestCase):
    def setUp(self):
        rt.reset()

    def test_empty_shape_is_a_failure(self):
        with mock.patch.object(rt, "numSplines", lambda s: s.count, create=True), \
                mock.patch.object(rt, "isClosed", lambda s, i: True, create=True):
            out = ka.spline_closed_report([_Shape("area", 0), _Shape("closed", 2)])
        self.assertEqual([r["name"] for r in out], ["area"])

    def test_make_camera_refuses_existing_name(self):
        rt.objects = [FakeNode("CAM_V01_a")]
        with self.assertRaises(ValueError):
            ka.make_camera("CAM_V01_a", (0, 0, 1.5), (0, 5, 1.5), 30)

    def test_set_anim_output_resets_stride(self):
        dialog = types.SimpleNamespace(isOpen=lambda: False, close=lambda: None)
        with mock.patch.object(rt, "renderSceneDialog", dialog, create=True), \
                mock.patch.object(rt, "interval", lambda a, b: (a, b), create=True), \
                mock.patch.object(ka, "anim_report", lambda: {"rendNThFrame": rt.rendNThFrame}):
            rt.rendNThFrame = 5
            rep = ka.set_anim_output(25, 0, 499, "C:/out/shot_.exr")
        self.assertEqual(rep["rendNThFrame"], 1)

    def _render(self, cancelled):
        def render(**kw):
            kw["cancelled"].value = cancelled
            return types.SimpleNamespace(filename=kw.get("outputFile"))
        byref = lambda v: types.SimpleNamespace(value=v)  # noqa: E731
        return mock.patch.object(rt, "render", render), mock.patch.object(pymxs, "byref", byref, create=True)

    def test_cancelled_test_render_raises(self):
        r, b = self._render(True)
        with r, b, self.assertRaises(RuntimeError):
            ka.time_test_frame("CAM", 10, "C:/out/test.png")

    def test_completed_test_render_returns_seconds(self):
        r, b = self._render(False)
        with r, b:
            self.assertGreaterEqual(ka.time_test_frame("CAM", 10, "C:/out/test.png"), 0)


if __name__ == "__main__":
    unittest.main()
