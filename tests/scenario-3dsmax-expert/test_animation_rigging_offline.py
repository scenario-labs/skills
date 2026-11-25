"""Offline tests for scenario-3dsmax-animation-rigging helpers, with no 3ds Max installed.

The fake pymxs in fakes/ only satisfies the import. Scene reads (world_pos, world_axis, skinOps)
are replaced per test, so these tests prove the measurement logic, not the 3ds Max API.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-animation-rigging" / "scripts"
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

import maxkit_anim  # noqa: E402


def node(name):
    return SimpleNamespace(name=name)


class ContactSlide(unittest.TestCase):
    def run_track(self, zs, xs=None):
        xs = xs or [0.0] * len(zs)
        track = {f: (xs[f], 0.0, z) for f, z in enumerate(zs)}
        with mock.patch.object(maxkit_anim, "world_pos", lambda n, f: track[f]):
            return maxkit_anim.contact_slide(node("foot"), 0, len(zs) - 1, ground_z=0.0, height_tol=2.0)

    def test_far_below_ground_is_not_contact(self):
        self.assertEqual(self.run_track([-100.0] * 5), [])

    def test_planted_foot_is_contact(self):
        out = self.run_track([0.5, 0.5, 10.0, 1.0], xs=[0.0, 0.3, 5.0, 5.0])
        self.assertEqual([ph["frames"] for ph in out], [(0, 1), (3, 3)])
        self.assertAlmostEqual(out[0]["slide"], 0.3)

    def test_slightly_below_ground_is_contact(self):
        self.assertEqual(len(self.run_track([-1.5, -1.5])), 1)


class AxisAlignment(unittest.TestCase):
    def measure(self, pos_a, pos_b):
        pos = {"a": pos_a, "b": pos_b}
        with mock.patch.object(maxkit_anim, "world_axis", lambda n, f, axis=0: (0.0, 1.0, 0.0)), \
                mock.patch.object(maxkit_anim, "world_pos", lambda n, f: pos[n.name]):
            return maxkit_anim.axis_alignment([(node("a"), node("b"))], 0, 2)[0]

    def test_parallel_but_offset_axes_report_offset(self):
        out = self.measure((0.0, 0.0, 0.0), (10.0, 0.0, 0.0))
        self.assertAlmostEqual(out["min_abs_dot"], 1.0)
        self.assertAlmostEqual(out["max_offset"], 10.0)

    def test_coaxial_pivots_report_no_offset(self):
        out = self.measure((0.0, 0.0, 0.0), (0.0, 40.0, 0.0))
        self.assertAlmostEqual(out["max_offset"], 0.0)


class SkinReport(unittest.TestCase):
    def report(self, weights, limit=4):
        skin = SimpleNamespace(cls="Skin")
        skin_ops = SimpleNamespace(
            GetNumberVertices=lambda s: 1,
            GetNumberBones=lambda s: len(weights),
            GetVertexWeightCount=lambda s, v: len(weights),
            GetVertexWeight=lambda s, v, i: weights[i - 1],
            GetVertexWeightBoneID=lambda s, v, i: i,
            GetBoneName=lambda s, b, _: "bone%d" % b,
        )
        fake_rt = SimpleNamespace(
            classOf=lambda o: o.cls, select=lambda n: None, execute=lambda s: None,
            modPanel=SimpleNamespace(setCurrentObject=lambda m: None), skinOps=skin_ops)
        mesh = SimpleNamespace(name="mesh", modifiers=[skin])
        with mock.patch.object(maxkit_anim, "rt", fake_rt):
            return maxkit_anim.skin_report(mesh, limit=limit)

    def test_tiny_fifth_weight_counts_toward_limit(self):
        out = self.report([0.249875, 0.249875, 0.249875, 0.249875, 0.0005])
        self.assertEqual(out["over_limit"], 1)
        self.assertEqual(out["unused_bones"], [])

    def test_four_influences_pass(self):
        out = self.report([0.25, 0.25, 0.25, 0.25, 0.0])
        self.assertEqual((out["over_limit"], out["bad_sum"]), (0, 0))
        self.assertEqual(out["unused_bones"], ["bone5"])


if __name__ == "__main__":
    unittest.main()
