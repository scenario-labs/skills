"""Offline tests for scenario-3dsmax-scripting runner tools, no 3ds Max needed.

batch_many runs against a stand-in lead toolkit; package_lint and port_scan run on files written
to a temporary folder removed after each test.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-scripting" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import batch_many  # noqa: E402
import package_lint  # noqa: E402
import port_scan  # noqa: E402


def tmpdir(test) -> Path:
    d = Path(tempfile.mkdtemp(prefix="scr_"))
    test.addCleanup(shutil.rmtree, d, ignore_errors=True)
    return d


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*args)


class Collect(unittest.TestCase):
    def test_missing_and_empty_inputs_are_errors(self):
        d = tmpdir(self)
        (d / "empty").mkdir()
        errors = []
        self.assertEqual(batch_many.collect([str(d / "nope"), str(d / "empty")], errors), [])
        self.assertEqual(len(errors), 2)

    def test_main_exits_2_without_scenes(self):
        d = tmpdir(self)
        job = d / "job.py"
        job.write_text("result = 1\n", encoding="utf-8")
        (d / "empty").mkdir()
        self.assertEqual(quiet(batch_many.main, ["--job", str(job), "--out", str(d / "out"), str(d / "empty")]), 2)

    def test_same_file_name_in_two_folders_gets_two_stems(self):
        d = tmpdir(self)
        for sub in ("a", "b"):
            (d / sub).mkdir()
            (d / sub / "model.max").write_bytes(b"x")
        (d / "a" / "other.max").write_bytes(b"x")
        scenes = batch_many.collect([str(d)])
        names = batch_many.stems(scenes)
        self.assertEqual(len(set(names.values())), 3)
        self.assertIn("other", names.values())


class FakeBatch:
    def __init__(self, codes, write=None):
        self.codes = list(codes)
        self.write = write
        self.calls = 0

    def run_batch(self, script, scene=None, args=None, timeout=1800, log_dir=None):
        self.calls += 1
        code = self.codes.pop(0)
        if self.write is not None:
            Path(self.write[0]).write_text(json.dumps(self.write[1]), encoding="utf-8")
        return {"exit_code": code, "meaning": "timeout" if code is None else "code %s" % code}

    def command(self, *a, **k):
        return []


class RunOne(unittest.TestCase):
    def run_with(self, batch, out):
        wrap = SimpleNamespace(wrap=lambda code, **k: code)
        with mock.patch.object(batch_many, "_toolkit", lambda: (wrap, batch)):
            return batch_many.run_one(str(out / "s.max"), "result = 1", [], str(out), 60, False, "s")

    def test_failed_previous_result_is_not_skipped(self):
        out = tmpdir(self)
        (out / "s.json").write_text('{"ok": false}', encoding="utf-8")
        batch = FakeBatch([0], write=(out / "s.json", {"ok": True}))
        self.assertEqual(self.run_with(batch, out)["status"], "ok")
        self.assertEqual(batch.calls, 1)

    def test_ok_previous_result_is_skipped(self):
        out = tmpdir(self)
        (out / "s.json").write_text('{"ok": true}', encoding="utf-8")
        self.assertEqual(self.run_with(FakeBatch([]), out)["status"], "skipped")

    def test_truncated_previous_result_is_not_skipped(self):
        out = tmpdir(self)
        (out / "s.json").write_text('{"ok": tr', encoding="utf-8")
        batch = FakeBatch([0], write=(out / "s.json", {"ok": True}))
        self.assertEqual(self.run_with(batch, out)["status"], "ok")

    def test_timeout_is_not_retried(self):
        out = tmpdir(self)
        batch = FakeBatch([None, None])
        row = self.run_with(batch, out)
        self.assertEqual((row["status"], batch.calls), ("failed", 1))

    def test_other_failure_is_retried_once(self):
        out = tmpdir(self)
        batch = FakeBatch([-120, -120])
        self.assertEqual(self.run_with(batch, out)["attempts"], 2)


PKG = """<ApplicationPackage AutodeskProduct="3ds Max" ProductType="Application" Name="T"
  AppVersion="1.0.0" UpgradeCode="{12345678-1234-1234-1234-123456789012}">
  <CompanyDetails />
  <Components Description="post-start-up scripts parts">
    <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="%s" SeriesMax="%s" />
    <ComponentEntry ModuleName="%s" />
  </Components>
</ApplicationPackage>
"""


class PackageLint(unittest.TestCase):
    def lint(self, smin, smax, module, extra=()):
        d = tmpdir(self)
        (d / "Contents").mkdir()
        (d / "Contents" / "start.ms").write_text("-- start\n", encoding="utf-8")
        for name in extra:
            (d / "Contents" / name).write_text("-- extra\n", encoding="utf-8")
        (d / "PackageContents.xml").write_text(PKG % (smin, smax, module), encoding="utf-8")
        _, findings = package_lint.lint(str(d))
        return [f for f in findings if f["severity"] == "error"]

    def test_reversed_update_bounds_are_an_error(self):
        self.assertTrue(any(f["rule"] == "Series" for f in self.lint("2027.3", "2027.2", "./Contents/start.ms")))

    def test_year_only_max_covers_updates(self):
        self.assertEqual(self.lint("2027.3", "2027", "./Contents/start.ms"), [])

    def test_windows_separators_resolve(self):
        self.assertEqual(self.lint("2027", "2027", ".\\Contents\\start.ms"), [])

    def test_wildcard_matches_a_file(self):
        self.assertEqual(self.lint("2027", "2027", "./Contents/*.ms"), [])
        self.assertTrue(self.lint("2027", "2027", "./Contents/*.py"))

    def test_literal_bracket_name_is_a_file(self):
        self.assertEqual(self.lint("2027", "2027", "./Contents/start[1].ms", extra=["start[1].ms"]), [])


class PortScan(unittest.TestCase):
    def test_folder_without_py_files_exits_2(self):
        d = tmpdir(self)
        (d / "notes.txt").write_text("x", encoding="utf-8")
        self.assertEqual(quiet(port_scan.main, [str(d)]), 2)

    def test_clean_file_exits_0(self):
        d = tmpdir(self)
        (d / "ok.py").write_text("x = 1\n", encoding="utf-8")
        self.assertEqual(quiet(port_scan.main, [str(d)]), 0)

    def test_unreadable_folder_is_reported(self):
        d = tmpdir(self)
        (d / "ok.py").write_text("x = 1\n", encoding="utf-8")

        def walk(root, onerror=None):
            onerror(OSError("permission denied: sub"))
            yield str(d), [], ["ok.py"]

        with mock.patch.object(port_scan.os, "walk", walk):
            self.assertEqual(quiet(port_scan.main, [str(d)]), 2)


if __name__ == "__main__":
    unittest.main()
