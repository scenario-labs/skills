"""Offline tests for scenario-3dsmax-modeling, with no 3ds Max installed.

maxkit_modeling runs against a stand-in runtime defined here: passing tests prove the
Python logic, not the 3ds Max API.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-modeling" / "scripts"
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

import maxkit_modeling  # noqa: E402


class BitArray:
    """Like a MAXScript BitArray: iterating it yields every bit, numberSet counts the set ones."""

    def __init__(self, size, set_bits=()):
        self.bits = [i + 1 in set_bits for i in range(size)]
        self.numberSet = sum(self.bits)

    def __iter__(self):
        return iter(self.bits)


class Poly:
    def __init__(self):
        self.name = "tmp"
        self.weldThreshold = 0.0001  # a stale value from the source object
        self.nverts = 8
        self.used_threshold = None


class PolyOp:
    def getNumFaces(self, n):
        return 6

    def getNumVerts(self, n):
        return n.nverts

    def getFaceDeg(self, n, i):
        return 4

    def getOpenEdges(self, n):
        return BitArray(12, set_bits={3, 7})

    def weldVertsByThreshold(self, n, verts):
        n.used_threshold = n.weldThreshold
        n.nverts -= 2


class Runtime:
    def __init__(self):
        self.polyop = PolyOp()
        self.tmp = Poly()
        self.deleted = []

    def copy(self, node):
        return self.tmp

    def convertToPoly(self, n):
        pass

    def execute(self, s):
        return s

    def matrix3(self, _):
        return None

    def nodeGetBoundingBox(self, node, _m):
        return ((0, 0, 0), (10, 10, 10))

    def delete(self, n):
        self.deleted.append(n)


class MeshChecks(unittest.TestCase):
    def test_weld_uses_the_requested_tolerance(self):
        rt = Runtime()
        with mock.patch.object(maxkit_modeling, "rt", rt):
            src = mock.Mock()
            src.name = "GEO_Body"
            out = maxkit_modeling.mesh_checks(src, weld_tol=0.001)
        self.assertEqual(rt.tmp.used_threshold, 0.001)
        self.assertEqual(out["weldable_verts"], 2)
        self.assertEqual(out["weld_tol"], 0.001)
        self.assertEqual(out["open_edges"], 2)
        self.assertEqual(rt.deleted, [rt.tmp])

    def test_ms_twin_sets_weld_threshold(self):
        ms = (SCRIPTS / "mxs" / "maxkit_modeling.ms").read_text(encoding="utf-8")
        i = ms.index("fn meshChecks")
        self.assertLess(ms.index("tmp.weldThreshold", i), ms.index("polyop.weldVertsByThreshold", i))


if __name__ == "__main__":
    unittest.main()
