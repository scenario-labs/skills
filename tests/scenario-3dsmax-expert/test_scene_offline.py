"""Offline tests for scenario-3dsmax-scene: the gate, the audit exit code and maxkit_scene logic.

The fake pymxs in fakes/ stands in for 3ds Max: passing tests prove the Python logic only.
"""
from __future__ import annotations

import contextlib
import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-scene" / "scripts"
sys.path[:0] = [str(HERE / "fakes"), str(SCRIPTS)]

import pymxs  # noqa: E402  (the fake)
import maxkit_scene as ks  # noqa: E402
import scene_gate  # noqa: E402
import scene_run  # noqa: E402
from pymxs import FakeNode  # noqa: E402

rt = pymxs.runtime


def clean_audit(**over):
    audit = {
        "units": {"system_type": "centimeters", "system_scale": 1.0},
        "origin": {"far_cm": 100000.0, "far": []},
        "maps": {"missing_count": 0, "unreadable": 0},
        "xrefs": {"xref_scenes": [], "errors": []},
    }
    audit.update(over)
    return audit


def blocking_failures(audit, spec=None):
    return [r[0] for r in scene_gate.gates(audit, spec or {}) if r[4] and not r[1]]


class GateTests(unittest.TestCase):
    def test_clean_audit_passes(self):
        self.assertEqual(blocking_failures(clean_audit()), [])

    def test_units_only_audit_fails(self):
        audit = {"units": {"system_type": "centimeters", "system_scale": 1}}
        self.assertIn("audit sections present", blocking_failures(audit))

    def test_cutoff_above_limit_fails(self):
        fails = blocking_failures(clean_audit(), {"max_far_m": 100})
        self.assertIn("far from origin", fails)

    def test_cutoff_matching_limit_passes(self):
        audit = clean_audit(origin={"far_cm": 10000.0, "far": []})
        self.assertEqual(blocking_failures(audit, {"max_far_m": 100}), [])

    def test_missing_cutoff_fails(self):
        self.assertIn("far from origin", blocking_failures(clean_audit(origin={"far": []})))

    def test_unreadable_maps_fail(self):
        audit = clean_audit(maps={"missing_count": 0, "unreadable": 2})
        self.assertIn("maps inspected", blocking_failures(audit))

    def test_xref_errors_fail(self):
        audit = clean_audit(xrefs={"xref_scenes": [], "errors": ["getXRefFileCount: boom"]})
        self.assertIn("XRef records inspected", blocking_failures(audit))


class AuditExitCodeTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="scene_run_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.env = self.dir / "scene_audit.json"

    def _code(self, res):
        with contextlib.redirect_stdout(None):
            return scene_run.audit_exit_code(res, self.env)

    def test_missing_envelope_fails(self):
        self.assertEqual(self._code({"ok": True}), 1)

    def test_bad_json_fails(self):
        self.env.write_text("{not json", encoding="utf-8")
        self.assertEqual(self._code({"ok": True}), 1)

    def test_envelope_not_ok_fails(self):
        self.env.write_text(json.dumps({"ok": False, "error": "trace"}), encoding="utf-8")
        self.assertEqual(self._code({"ok": True}), 1)

    def test_batch_failure_fails(self):
        self.env.write_text(json.dumps({"ok": True}), encoding="utf-8")
        self.assertEqual(self._code({"ok": False}), 1)

    def test_ok_envelope_passes(self):
        self.env.write_text(json.dumps({"ok": True, "result": {}}), encoding="utf-8")
        self.assertEqual(self._code({"ok": True}), 0)


class _RaisingFilename:
    @property
    def filename(self):
        raise RuntimeError("no such property")


class SceneKitTests(unittest.TestCase):
    def setUp(self):
        rt.reset()

    def test_rename_refuses_duplicate_targets(self):
        rt.objects = [FakeNode("A"), FakeNode("B")]
        out = ks.rename_nodes({"A": "C", "B": "C"}, dry_run=False)
        self.assertEqual(out["duplicate_targets"], ["C"])
        self.assertEqual([n.name for n in rt.objects], ["A", "B"])

    def test_rename_distinct_targets_applies(self):
        rt.objects = [FakeNode("A"), FakeNode("B")]
        ks.rename_nodes({"A": "C", "B": "D"}, dry_run=False)
        self.assertEqual([n.name for n in rt.objects], ["C", "D"])

    def test_xref_count_error_is_reported(self):
        def boom():
            raise RuntimeError("no xrefs interface")
        xrefs = types.SimpleNamespace(getXRefFileCount=boom)
        with mock.patch.object(rt, "xrefs", xrefs, create=True):
            rep = ks.xref_report()
        self.assertEqual(rep["xref_scenes"], [])
        self.assertTrue(rep["errors"])

    def test_xref_record_error_is_reported(self):
        def get(i):
            raise RuntimeError("bad record %d" % i)
        xrefs = types.SimpleNamespace(getXRefFileCount=lambda: 2, getXRefFile=get)
        with mock.patch.object(rt, "xrefs", xrefs, create=True):
            rep = ks.xref_report()
        self.assertEqual(len(rep["errors"]), 2)

    def test_unreadable_map_is_counted(self):
        rt.bitmaps = [_RaisingFilename()]
        rep = ks.missing_maps_report()
        self.assertEqual(rep["missing_count"], 0)
        self.assertEqual(rep["unreadable"], 1)

    def test_origin_report_records_cutoff(self):
        rt.objects = [FakeNode("A")]
        self.assertEqual(ks.origin_report(far_cm=5000.0)["far_cm"], 5000.0)

    def test_smooth_targets_one_modifier_and_keeps_render_count(self):
        first = types.SimpleNamespace(cls="TurboSmooth", iterations=1, renderIterations=0,
                                      useRenderIterations=False)
        second = types.SimpleNamespace(cls="TurboSmooth", iterations=2, renderIterations=3,
                                       useRenderIterations=True)
        node = FakeNode("Sofa")
        node.modifiers = [first, second]
        rt.objects = [node]
        out = ks.smooth_viewport_off(dry_run=False)
        self.assertEqual(out["changed"], 2)
        # first: render used iterations=1 (flag off), so 1 is kept as the render count
        self.assertEqual((first.iterations, first.renderIterations, first.useRenderIterations), (0, 1, True))
        self.assertEqual((second.iterations, second.renderIterations, second.useRenderIterations), (0, 3, True))

    def test_suppressed_undo_error_raises(self):
        @contextlib.contextmanager
        def swallowing_undo(on, label=None):
            with contextlib.suppress(Exception):
                yield

        def fail(*_a):
            raise RuntimeError("instanceReplace failed")

        rt.objects = [FakeNode("A"), FakeNode("B")]
        with mock.patch.object(pymxs, "undo", swallowing_undo), \
                mock.patch.object(rt, "instanceReplace", fail, create=True):
            with self.assertRaises(RuntimeError):
                ks.instance_copies([{"nodes": ["A", "B"]}], dry_run=False)


if __name__ == "__main__":
    unittest.main()
