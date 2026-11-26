"""Review round 1, lead runner and checker: planted inputs for the fixes in ae.py, ae_check.py and aekit/json.jsx.

- ae.probe on a stream whose frame rate reads 0/0, ae.render when ffprobe cannot read the rendered file.
- ae.aerender against a stand-in aerender (a small Python script): a frame numbered 9988 on a PROGRESS line, an
  "output module failed" line, a stall, a total timeout and an interrupt (the child must be stopped every time).
- ae.restart without the operator's environment variable, ae.doctor with no readable preferences file.
- ae_check: a trailing comma before a bracket on the next line, the comment and string stripper on a large file.
- AEK.json.parse under Node: valid JSON round-trips, anything else throws and nothing runs.

No After Effects, no network. Each case builds its inputs in a temporary folder.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).parent
LEAD = HERE.parents[1] / "skills" / "dcc" / "after-effects" / "scenario-after-effects-expert" / "scripts"
FAMILY = LEAD.parents[1]
sys.path.insert(0, str(LEAD))

import ae  # noqa: E402
import ae_check  # noqa: E402


def alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    # a zombie still answers signal 0 on some systems: read its state where ps exists
    r = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
    return bool(r.stdout.strip()) and not r.stdout.strip().startswith("Z")


class Probe(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ae_review_a_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_frame_rate_zero_over_zero_does_not_raise(self):
        movie = self.tmp / "cut.mov"
        movie.write_bytes(b"\0" * 64)
        canned = {"format": {"duration": "1.0"}, "streams": [{"codec_type": "video", "codec_name": "prores", "r_frame_rate": "0/0", "width": 8, "height": 8}]}
        done = subprocess.CompletedProcess([], 0, json.dumps(canned), "")
        with unittest.mock.patch.object(ae.shutil, "which", lambda name: "/usr/bin/" + name), \
                unittest.mock.patch.object(ae.subprocess, "run", return_value=done):
            res = ae.probe(str(movie))
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["streams"][0]["fps"], 0.0)

    def test_queue_render_fails_when_ffprobe_cannot_read_the_file(self):
        movie = self.tmp / "preview.mp4"
        movie.write_bytes(b"broken")
        answer = {"ok": True, "result": {"path": str(movie), "done": True}}
        with unittest.mock.patch.object(ae, "run_js", return_value=dict(answer)), \
                unittest.mock.patch.object(ae, "probe", return_value={"ok": False, "error": "Invalid data found"}), \
                unittest.mock.patch.object(ae.shutil, "which", lambda name: "/usr/bin/" + name):
            res = ae.render("MAIN", str(movie))
        self.assertFalse(res["ok"])
        self.assertEqual(res["why"], "probe")

    def test_queue_render_keeps_ok_without_ffprobe(self):
        movie = self.tmp / "preview.mp4"
        movie.write_bytes(b"x")
        answer = {"ok": True, "result": {"path": str(movie), "done": True}}
        with unittest.mock.patch.object(ae, "run_js", return_value=dict(answer)), \
                unittest.mock.patch.object(ae, "probe", return_value={"ok": False, "error": "ffprobe not found"}), \
                unittest.mock.patch.object(ae.shutil, "which", lambda name: None):
            res = ae.render("MAIN", str(movie))
        self.assertTrue(res["ok"])


@unittest.skipIf(os.name == "nt", "the stand-in aerender is a POSIX executable script")
class Aerender(unittest.TestCase):
    """A stand-in aerender: a Python script that prints the given lines, writes the output, then does what `tail` says."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ae_review_a_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pidfile = self.tmp / "child.pid"

    def fake(self, lines, tail="exit"):
        script = self.tmp / "aerender"
        script.write_text(textwrap.dedent("""\
            #!%s
            import sys, time
            args = sys.argv[1:]
            out = args[args.index("-output") + 1]
            open(%r, "w").write(str(__import__("os").getpid()))
            for line in %r:
                print(line, flush=True)
            open(out, "wb").write(b"png")
            tail = %r
            if tail == "hang":
                time.sleep(120)
            elif tail == "chatter":
                while True:
                    print("PROGRESS: still going", flush=True)
                    time.sleep(0.2)
            """) % (sys.executable, str(self.pidfile), list(lines), tail), encoding="utf-8")
        script.chmod(0o755)
        return [{"aerender": str(script), "app": "stand-in", "version": "27.0"}]

    def run_fake(self, lines, tail="exit", **kw):
        with unittest.mock.patch.object(ae, "installs", lambda: self.fake(lines, tail)):
            return ae.aerender(str(self.tmp / "p.aep"), "MAIN", str(self.tmp / "out" / "frame.png"), min_free_gb=0, **kw)

    def child(self):
        for _ in range(50):
            if self.pidfile.exists() and self.pidfile.read_text():
                return int(self.pidfile.read_text())
            time.sleep(0.1)
        self.fail("the stand-in aerender never started")

    def test_frame_9988_on_a_progress_line_is_not_a_disk_failure(self):
        res = self.run_fake(["PROGRESS: 0:05:32:28 (9988): 0 Seconds", "PROGRESS: Finished composition MAIN", "Total Time Elapsed: 1 Min"])
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["checks"]["log_errors"], "ok")

    def test_output_module_failed_is_a_disk_failure_without_retry(self):
        res = self.run_fake(["aerender ERROR: An output module failed. The file may not be complete."])
        self.assertFalse(res["ok"])
        self.assertEqual(res["why"], "disk")
        self.assertNotIn("retry", res)

    def test_stall_stops_the_child_and_gives_no_retry(self):
        res = self.run_fake(["PROGRESS: start"], tail="hang", stall=1)
        self.assertEqual(res["why"], "stall")
        self.assertNotIn("retry", res)
        self.assertFalse(alive(self.child()))

    def test_total_timeout_stops_a_child_that_keeps_printing(self):
        t0 = time.time()
        res = self.run_fake(["PROGRESS: start"], tail="chatter", stall=0, timeout=2)
        self.assertLess(time.time() - t0, 30)
        self.assertEqual(res["why"], "timeout")
        self.assertEqual(res["checks"]["timeout"], "failed")
        self.assertFalse(alive(self.child()))

    def test_interrupt_stops_the_child(self):
        real_sleep = time.sleep
        calls = []

        def sleep(s):
            calls.append(s)
            if len(calls) == 4:
                raise KeyboardInterrupt
            real_sleep(s)
        with unittest.mock.patch.object(ae.time, "sleep", sleep):
            with self.assertRaises(KeyboardInterrupt):
                self.run_fake(["PROGRESS: start"], tail="hang", stall=0)
        self.assertFalse(alive(self.child()))


class Restart(unittest.TestCase):
    def test_flag_alone_is_refused_before_anything_is_stopped(self):
        env = {k: v for k, v in os.environ.items() if k != ae.TEST_SESSION_ENV}
        with unittest.mock.patch.dict(ae.os.environ, env, clear=True), \
                unittest.mock.patch.object(ae, "status", lambda: None), \
                unittest.mock.patch.object(ae, "ae_pid", side_effect=AssertionError("looked for a process to stop")), \
                unittest.mock.patch.object(ae.os, "kill", side_effect=AssertionError("sent a signal")):
            res = ae.restart(test_session=True)
        self.assertFalse(res["ok"])
        self.assertIn(ae.TEST_SESSION_ENV, res["error"])

    def test_with_the_variable_the_heartbeat_guard_still_applies(self):
        with unittest.mock.patch.dict(ae.os.environ, {ae.TEST_SESSION_ENV: "1"}), \
                unittest.mock.patch.object(ae, "bridge_dir", lambda: tempfile.gettempdir()), \
                unittest.mock.patch.object(ae, "status", lambda: {"age_s": 5.0}), \
                unittest.mock.patch.object(ae.os, "kill", side_effect=AssertionError("sent a signal")):
            res = ae.restart(test_session=True)
        self.assertFalse(res["ok"])
        self.assertIn("heartbeat", res["error"])


class Doctor(unittest.TestCase):
    def test_no_preferences_file_warns_and_a_fail_sets_ok_false(self):
        tmp = Path(tempfile.mkdtemp(prefix="ae_review_a_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        prefs = tmp / "27.0"
        prefs.mkdir()
        with unittest.mock.patch.object(ae, "prefs_dirs", lambda: [str(prefs)]), \
                unittest.mock.patch.object(ae, "installs", lambda: []), \
                unittest.mock.patch.object(ae, "ae_pid", lambda: 4242), \
                unittest.mock.patch.object(ae, "bridge_dir", lambda: str(tmp)), \
                unittest.mock.patch.object(ae, "status", lambda: {"age_s": 0.5, "bridge": "t", "ae": "27.0", "jobs": 1}), \
                unittest.mock.patch.object(ae, "windows", lambda shot_dir=None: []):
            d = ae.doctor()
        checks = "\n".join(d["checks"])
        self.assertIn("WARN scripting preference not readable", checks)
        self.assertIn("FAIL no After Effects found", checks)
        self.assertIs(d["ok"], False)


class Checker(unittest.TestCase):
    def test_trailing_comma_before_a_bracket_on_the_next_line(self):
        src = "var o = {\n    a: 1,\n    b: [1, 2,\n    ]\n};\n"
        errs = [f for f in ae_check.scan(src, ae_check.ES3, "job.jsx") if "trailing comma" in f["message"]]
        self.assertEqual(sorted(f["line"] for f in errs), [3])

    def test_comma_inside_a_string_or_comment_is_not_reported(self):
        src = 'var s = "a,\\n}";\nvar o = { a: 1 // last,\n};\n/* x,\n} */\n'
        errs = [f for f in ae_check.scan(src, ae_check.ES3, "job.jsx") if "trailing comma" in f["message"]]
        self.assertEqual(errs, [])

    def test_stripper_is_linear_on_a_large_file(self):
        unit = 'var a = b / 2; // c\nvar re = /x\\/y/g; var s = "q\'w"; /* z */\n'
        src = unit * 1500   # about 90 KB
        t0 = time.time()
        clean = ae_check.strip_comments_and_strings(src)
        self.assertLess(time.time() - t0, 3.0)
        self.assertEqual(clean.count("\n"), src.count("\n"))
        self.assertIn("/re/", clean)

    def test_stripper_output_is_unchanged_on_every_family_script(self):
        def old(src, keep_strings=False):
            out, i, n = [], 0, len(src)
            while i < n:
                c = src[i]
                prev = "".join(out).rstrip()[-1:] if out else ""
                if c == "/" and i + 1 < n and src[i + 1] not in "/*" and (prev == "" or prev in "(,=:[!&|?{};"):
                    j = i + 1
                    while j < n and src[j] != "/" and src[j] != "\n":
                        j += 2 if src[j] == "\\" else 1
                    out.append("/re/")
                    i = j + 1
                elif c == "/" and i + 1 < n and src[i + 1] == "/":
                    while i < n and src[i] != "\n":
                        i += 1
                elif c == "/" and i + 1 < n and src[i + 1] == "*":
                    j = src.find("*/", i + 2)
                    j = n if j < 0 else j + 2
                    out.append("\n" * src[i:j].count("\n"))
                    i = j
                elif c in "\"'":
                    j = i + 1
                    while j < n and src[j] != c and src[j] != "\n":
                        j += 2 if src[j] == "\\" else 1
                    out.append(src[i:j + 1] if keep_strings else c + c)
                    if keep_strings is False and src[i + 1:i + 3] == "~/":
                        out[-1] = c + "~/" + c
                    i = j + 1
                else:
                    out.append(c)
                    i += 1
            return "".join(out)
        for path in sorted(LEAD.glob("aekit/*.jsx")) + [LEAD / "ae_bridge.jsx"]:
            src = path.read_text(encoding="utf-8")
            for keep in (False, True):
                self.assertEqual(ae_check.strip_comments_and_strings(src, keep), old(src, keep), "%s keep=%s" % (path.name, keep))


JSON_HARNESS = r"""
const fs = require("fs"), vm = require("vm");
const ctx = { File: function () {}, Folder: function () {} };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), ctx);
const parse = (t) => vm.runInContext("AEK.json.parse(__t)", Object.assign(ctx, { __t: t }));
const out = { valid: [], invalid: [] };
for (const t of JSON.parse(process.argv[2])) {
  try { out.valid.push({ text: t, same: JSON.stringify(parse(t)) === JSON.stringify(JSON.parse(t)) }); }
  catch (e) { out.valid.push({ text: t, same: false, error: String(e) }); }
}
for (const t of JSON.parse(process.argv[3])) {
  let threw = false;
  try { parse(t); } catch (e) { threw = String(e).indexOf("AEK.json.parse") >= 0; }
  out.invalid.push({ text: t, threw: threw });
}
out.pwned = ctx.pwned === 1;
process.stdout.write(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class JsonParse(unittest.TestCase):
    VALID = [
        '{"a": 1, "b": [true, false, null], "c": {"d": "e"}}',
        '  [ -0.5e-3 , 12, 0, 1E2, -7 ]  ',
        '"tab\\t quote\\" slash\\/ back\\\\ nl\\n u\\u00e9\\u2603"',
        '{"rows": [{"id": "x1", "lang": "fr"}, {"id": "x2", "lang": "en"}]}',
        '[]', '{}', 'null', '3.25',
    ]
    INVALID = [
        '(function(){ pwned = 1; return 1; })()',
        '{"a": pwned = 1}',
        "{'a': 1}", '{a: 1}', '[1, 2,]', '{"a": 1,}', '[1 2]', '01', '1.', '.5', '+1', 'NaN', 'undefined',
        '"bad \\x escape"', '"unterminated', '"line\nbreak"', '{"a": 1} trailing', '', 'tru', '[1] // comment',
    ]

    def test_valid_json_round_trips_and_everything_else_throws(self):
        r = subprocess.run(["node", "-e", JSON_HARNESS, str(LEAD / "aekit" / "json.jsx"), json.dumps(self.VALID), json.dumps(self.INVALID)],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual([v["text"] for v in out["valid"] if not v["same"]], [], out["valid"])
        self.assertEqual([v["text"] for v in out["invalid"] if not v["threw"]], [])
        self.assertFalse(out["pwned"], "input text was run as code")


if __name__ == "__main__":
    unittest.main()
