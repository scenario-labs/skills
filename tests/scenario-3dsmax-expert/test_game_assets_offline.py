"""Offline tests for scenario-3dsmax-game-assets, with no 3ds Max installed.

game_rules is plain Python. maxkit_game runs against a small geometric stand-in for the
pymxs runtime defined here: passing tests prove the Python logic, not the 3ds Max API.
"""
from __future__ import annotations

import contextlib
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-game-assets" / "scripts"
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

import game_rules  # noqa: E402
import maxkit_game  # noqa: E402


def node(name, tris=100, maps=(1,), **kw):
    n = {"name": name, "tris": tris, "map_channels": list(maps), "pos": [0, 0, 0], "parent": None}
    n.update(kw)
    return n


def rules(findings):
    return {f["rule"] for f in findings}


class Rules(unittest.TestCase):
    def report(self, nodes, helpers=(), **kw):
        rep = {"units": "centimeters", "system_scale": 1.0, "nodes": nodes,
               "helpers": [{"name": h} for h in helpers]}
        rep.update(kw)
        return rep

    def test_clean_report_passes(self):
        self.assertEqual([], game_rules.check_report(self.report([node("SM_Crate_A")])))

    def test_empty_or_missing_nodes_fail(self):
        self.assertIn("report.no_nodes", rules(game_rules.check_report(self.report([]))))
        self.assertIn("report.no_nodes", rules(game_rules.check_report({"units": "centimeters"})))

    def test_system_scale_must_be_one(self):
        found = game_rules.check_report(self.report([node("SM_Crate_A")], system_scale=100.0))
        self.assertIn("units.scale", rules(found))

    def test_socket_owner_must_match_whole_name(self):
        ok = game_rules.check_names(["SM_Crate"], ["SOCKET_SM_Crate_00"])
        self.assertNotIn("socket.no_render_mesh", rules(ok))
        bad = game_rules.check_names(["SM_Crate"], ["SOCKET_SM_Crate_Lid_00"])
        self.assertIn("socket.no_render_mesh", rules(bad))

    def test_uv_channel_1_required(self):
        found = game_rules.check_report(self.report([node("SM_Crate_A", maps=(2,))]))
        self.assertIn("uv.channel1", rules(found))

    def test_unmeasured_convexity_blocks(self):
        nodes = [node("SM_Crate_A"), node("UCX_SM_Crate_A_00", convex_violations=-1)]
        self.assertIn("collision.convex_unknown", rules(game_rules.check_report(self.report(nodes))))
        nodes[1]["convex_violations"] = 0
        self.assertNotIn("collision.convex_unknown", rules(game_rules.check_report(self.report(nodes))))

    def test_lod0_budget_applies_to_unsuffixed_mesh(self):
        found = game_rules.check_report(self.report([node("SM_Crate_A", tris=9000)]), budgets={"LOD0": 8000})
        self.assertIn("budget.tris", rules(found))
        lod1 = game_rules.check_report(self.report([node("SM_Crate_A", tris=100), node("SM_Crate_A_LOD1", tris=9000)]),
                                       budgets={"LOD0": 8000})
        self.assertNotIn("budget.tris", rules(lod1))
        exact = game_rules.check_report(self.report([node("SM_Crate_A", tris=600)]), budgets={"SM_Crate_A": 500})
        self.assertIn("budget.tris", rules(exact))


# ---------------------------------------------------------------- maxkit_game stand-in

class P3:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = float(x), float(y), float(z)


class Node:
    """Vertices in world space; pos is the pivot; scale is applied about the pivot."""

    def __init__(self, name, verts):
        self.__dict__.update(name=name, verts=[list(v) for v in verts], _pivot=[0.0, 0.0, 0.0], _scale=1.0)

    @property
    def min(self):
        return P3(*[min(v[k] for v in self.verts) for k in range(3)])

    @property
    def max(self):
        return P3(*[max(v[k] for v in self.verts) for k in range(3)])

    def __setattr__(self, key, val):
        if key == "pivot":
            self._pivot = [val.x, val.y, val.z]
        elif key == "pos":
            d = [val.x - self._pivot[0], val.y - self._pivot[1], val.z - self._pivot[2]]
            self.verts = [[v[k] + d[k] for k in range(3)] for v in self.verts]
            self._pivot = [val.x, val.y, val.z]
        elif key == "scale":
            f = val.x / self._scale
            p = self._pivot
            self.verts = [[p[k] + (v[k] - p[k]) * f for k in range(3)] for v in self.verts]
            self._scale = val.x
        else:
            self.__dict__[key] = val

    @property
    def pivot(self):
        return P3(*self._pivot)

    @property
    def pos(self):
        return P3(*self._pivot)


class Runtime:
    def __init__(self, system_type="centimeters", system_scale=1.0):
        self.units = mock.Mock(SystemType=system_type, SystemScale=system_scale)

    Point3 = P3

    def ResetXForm(self, n):
        n._scale = 1.0

    def collapseStack(self, n):
        pass

    def angleaxis(self, a, axis):
        return (a, axis)

    def rotate(self, n, aa):  # +90 about X around the pivot
        p = n._pivot
        n.verts = [[v[0], p[1] - (v[2] - p[2]), p[2] + (v[1] - p[1])] for v in n.verts]


@contextlib.contextmanager
def swallowing_undo(on, label=None):
    """3ds Max 2027 behavior per the pymxs module doc: roll back and swallow the exception."""
    with contextlib.suppress(Exception):
        yield


def box(name, lo, hi):
    return Node(name, [[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])


class Normalize(unittest.TestCase):
    def setUp(self):
        self.rt = Runtime()
        patches = [mock.patch.object(maxkit_game, "rt", self.rt),
                   mock.patch.object(maxkit_game.pymxs, "undo", swallowing_undo)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_multipart_keeps_relative_placement(self):
        a = box("A", (10, 10, 5), (20, 20, 15))
        b = box("B", (30, 10, 5), (40, 20, 15))
        rep = maxkit_game.normalize_group([a, b], target_cm=60.0)
        self.assertAlmostEqual(rep["scale_factor"], 2.0)
        self.assertAlmostEqual(a.min.x, -30.0)
        self.assertAlmostEqual(b.min.x, 10.0)
        self.assertAlmostEqual(a.min.z, 0.0)
        self.assertAlmostEqual(b.max.x - a.min.x, 60.0)
        for n in (a, b):
            self.assertEqual([n.pos.x, n.pos.y, n.pos.z], [0.0, 0.0, 0.0])

    def test_single_node_report_shape(self):
        n = box("Crate", (5, 5, 5), (15, 15, 25))
        rep = maxkit_game.normalize_intake(n, target_cm=40.0, measure="height")
        self.assertEqual(rep["name"], "Crate")
        self.assertAlmostEqual(n.max.z, 40.0)
        self.assertAlmostEqual(n.min.x, -10.0)

    def test_failure_inside_undo_reaches_caller(self):
        flat = box("Flat", (0, 0, 0), (10, 10, 0))
        with self.assertRaises(RuntimeError):
            maxkit_game.normalize_intake(flat, target_cm=10.0, measure="height")

    def test_refuses_scaled_centimeters(self):
        self.rt.units.SystemScale = 100.0
        with self.assertRaises(RuntimeError):
            maxkit_game.normalize_intake(box("X", (0, 0, 0), (1, 1, 1)), target_cm=10.0)


class AuditText(unittest.TestCase):
    def test_python_copy_matches_ms_file(self):
        ms = (SCRIPTS / "mxs" / "game_audit.ms").read_text(encoding="utf-8")
        body = ms[ms.index("fn gaJsonStr"):ms.rindex("result = gaAuditScene()")].rstrip()
        self.assertEqual(maxkit_game.MXS_AUDIT.strip(), body)

    def test_json_escapes_control_characters(self):
        for esc in ('"\\n"', '"\\r"', '"\\t"'):
            self.assertIn(esc, maxkit_game.MXS_AUDIT)


if __name__ == "__main__":
    unittest.main()
