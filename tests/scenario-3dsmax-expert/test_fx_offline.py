"""Offline tests for scenario-3dsmax-fx helpers, with no 3ds Max installed.

sim_budget runs as plain Python. maxkit_fx imports the fake pymxs in fakes/; scene nodes are
stand-ins, so these tests prove the reporting logic, not the 3ds Max or tyFlow API.
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
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-fx" / "scripts"
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

import maxkit_fx  # noqa: E402
import sim_budget  # noqa: E402


class CacheReport(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="fx_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def test_unnumbered_file_fails_a_frame_interval(self):
        (self.dir / "data.tyc").write_bytes(b"x")
        out = sim_budget.cache_report(self.dir, "*.tyc", 0, 3)
        self.assertFalse(out["ok"])
        self.assertEqual(out["missing_frames"], [0, 1, 2, 3])

    def test_complete_sequence_passes(self):
        for f in range(4):
            (self.dir / ("part_%04d.tyc" % f)).write_bytes(b"x")
        self.assertTrue(sim_budget.cache_report(self.dir, "*.tyc", 0, 3)["ok"])

    def test_no_interval_keeps_file_checks_only(self):
        (self.dir / "data.tyc").write_bytes(b"x")
        self.assertTrue(sim_budget.cache_report(self.dir, "*.tyc")["ok"])


class Unreadable:
    name = "broken"

    @property
    def modifiers(self):
        raise RuntimeError("stack locked")


class TyCacheModifier:
    cls = "tyCache"

    def __init__(self):
        self.calls = 0

    def cache(self):
        self.calls += 1


class CacheModifiers(unittest.TestCase):
    def test_empty_selection_does_no_work(self):
        mod = TyCacheModifier()
        scene = [SimpleNamespace(name="all", modifiers=[mod])]
        with mock.patch.object(maxkit_fx, "_all_nodes", lambda: scene):
            self.assertEqual(maxkit_fx.cache_tycache_modifiers([]), [])
            self.assertEqual(mod.calls, 0)
            self.assertEqual(len(maxkit_fx.cache_tycache_modifiers()), 1)
            self.assertEqual(mod.calls, 1)

    def test_unreadable_stack_is_a_failure(self):
        out = maxkit_fx.cache_tycache_modifiers([Unreadable()])
        self.assertEqual(len(out), 1)
        self.assertFalse(out[0]["ok"])
        self.assertIn("stack locked", out[0]["error"])


if __name__ == "__main__":
    unittest.main()
