"""Runs the After Effects runner (ae.py) on the host side, with no After Effects installed.

The runner wraps a job body into a self-reporting ExtendScript file, drops it in a mailbox folder
that the bridge script inside After Effects polls, and waits for the result file. Everything on
this side of the mailbox is plain Python: argument parsing, the wrapped job's text, the job and
result files, the heartbeat reading, the ffprobe summary and the contact-sheet label PNG. Here a
stand-in thread plays the bridge on a temporary mailbox folder; ffprobe answers come from canned
JSON. What runs inside After Effects (the bridge and the aekit modules) needs the application.
"""

import contextlib
import gc
import io
import json
import os
import shutil
import struct
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock
import warnings
import zlib
from pathlib import Path

HERE = Path(__file__).parent
LEAD = HERE.parents[1] / "skills" / "dcc" / "after-effects" / "scenario-after-effects-expert" / "scripts"
sys.path.insert(0, str(LEAD))

import ae  # noqa: E402


def resource_warnings(fn, *args, **kw):
    """Call fn, collect garbage, and return (ResourceWarning texts, result)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        result = fn(*args, **kw)
        gc.collect()
    return [str(w.message) for w in caught if issubclass(w.category, ResourceWarning)], result


class Mailbox(unittest.TestCase):
    """A temporary bridge folder with a fresh heartbeat, and After Effects reported as running."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ae_mailbox_"))
        self.addCleanup(shutil.rmtree, self.root, True)
        for target, value in (("bridge_dir", lambda: str(self.root)), ("ae_pid", lambda: 4242), ("windows", lambda shot_dir=None: [])):
            patcher = unittest.mock.patch.object(ae, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def beat(self, age_s=0.5):
        status = {"bridge": "test", "ae": "27.0x78", "state": "idle", "time": (time.time() - age_s) * 1000, "jobs": 3}
        (self.root / "status.json").write_text(json.dumps(status), encoding="utf-8")

    def stand_in_bridge(self, answer):
        """Answer the first inbox job the way the bridge does: the job writes outbox/<id>.json, inbox is emptied."""
        seen = {}

        def serve():
            inbox = self.root / "inbox"
            deadline = time.time() + 10
            while time.time() < deadline:
                jobs = sorted(inbox.glob("*.jsx")) if inbox.exists() else []
                if jobs:
                    job = jobs[0]
                    seen["text"] = job.read_text(encoding="utf-8")
                    seen["tmp_left"] = sorted(p.name for p in inbox.glob("*.tmp"))
                    job_id = job.stem
                    result = dict(answer(seen["text"]), id=job_id)
                    tmp = self.root / "outbox" / (job_id + ".json.tmp")
                    tmp.write_text(json.dumps(result), encoding="utf-8")
                    os.replace(tmp, self.root / "outbox" / (job_id + ".json"))
                    os.replace(job, self.root / "done" / job.name)
                    return
                time.sleep(0.02)

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        seen["thread"] = thread
        return seen


class Wrap(unittest.TestCase):
    def test_job_body_is_wrapped_in_one_undo_group_with_dialogs_shadowed(self):
        with unittest.mock.patch.object(ae, "bridge_dir", lambda: "/mailbox"):
            job_id, text, first = ae.wrap("return 1 + 1;", kit="none", undo="Agent: test", args={"comp": "Main"})
        self.assertIn("app.beginUndoGroup(__undo);", text)
        self.assertIn("app.endUndoGroup();", text)
        self.assertIn('var __undo = "Agent: test";', text)
        self.assertIn('var ARGS = {"comp": "Main"};', text)
        for name in ("alert", "confirm", "prompt"):
            self.assertIn("var %s = function" % name, text)
        self.assertIn('"/mailbox/outbox/%s.json"' % job_id, text)
        # `first` is the line the body starts on, so an error line maps back to the body
        self.assertEqual(text.split("\n")[first - 1], "return 1 + 1;")

    def test_kit_selection_always_brings_json_and_core(self):
        src = ae.kit_source("capture")
        self.assertLess(src.index("AEK"), len(src))
        names = [n for n in ae.KIT_ORDER if (Path(ae.KIT_DIR) / (n + ".jsx")).read_text(encoding="utf-8").rstrip() in src]
        self.assertEqual(names, ["json", "core", "capture"])
        self.assertEqual(ae.kit_source("none"), (Path(ae.KIT_DIR) / "json.jsx").read_text(encoding="utf-8").rstrip() + "\n")

    def test_unknown_kit_module_stops_before_anything_is_sent(self):
        with self.assertRaises(SystemExit) as stop:
            ae.kit_source("core,nosuch")
        self.assertIn("nosuch", str(stop.exception))

    def test_every_kit_module_named_in_the_order_ships(self):
        for name in ae.KIT_ORDER:
            self.assertTrue((Path(ae.KIT_DIR) / (name + ".jsx")).is_file(), name)

    def test_lib_files_are_inlined_after_the_kit(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = Path(tmp, "helper.jsx")
            lib.write_text("var AEX = { helper: true };\n", encoding="utf-8")
            leaks, (_, text, _) = resource_warnings(ae.wrap, "return AEX.helper;", kit="none", libs=[str(lib)])
        self.assertEqual(leaks, [])
        self.assertLess(text.index("var AEX = { helper: true };"), text.index("var ARGS"))


class Cli(unittest.TestCase):
    def run_main(self, *argv):
        out = io.StringIO()
        with unittest.mock.patch.object(sys, "argv", ["ae.py", *argv]), contextlib.redirect_stdout(out):
            code = ae.main()
        return code, out.getvalue()

    def test_print_job_stops_before_the_mailbox(self):
        with tempfile.TemporaryDirectory() as tmp, unittest.mock.patch.object(ae, "bridge_dir", lambda: tmp):
            code, out = self.run_main("run", "-e", "return 2;", "--kit", "none", "--print-job", "--args", '{"n": 1}')
            self.assertEqual(os.listdir(tmp), [])
        self.assertEqual(code, 0)
        self.assertIn("return 2;", out)
        self.assertIn('var ARGS = {"n": 1};', out)

    def test_job_file_is_read_as_utf8_and_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp, "job.jsx")
            job.write_text('return "café";\n', encoding="utf-8")
            leaks, (code, out) = resource_warnings(self.run_main, "run", str(job), "--kit", "none", "--print-job")
        self.assertEqual(leaks, [])
        self.assertEqual(code, 0)
        self.assertIn('return "café";', out)

    def test_parser_rejects_an_unknown_channel_and_a_missing_command(self):
        for argv in (["run", "-e", "1", "--channel", "telnet"], []):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stop:
                self.run_main(*argv)
            self.assertEqual(stop.exception.code, 2)

    def test_frames_requires_an_output_folder(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.run_main("frames", "Main")

    def test_a_failed_result_exits_1(self):
        with unittest.mock.patch.object(ae, "probe", return_value={"ok": False, "error": "ffprobe not found"}):
            code, out = self.run_main("probe", "missing.mov")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["error"], "ffprobe not found")


class BridgeChannel(Mailbox):
    def test_job_goes_through_the_inbox_and_the_result_comes_back(self):
        self.beat()
        seen = self.stand_in_bridge(lambda text: {"ok": True, "result": {"items": 7}, "log": [], "ms": 12})
        res = ae.run_js("return app.project.numItems;", kit="none", timeout=10)
        seen["thread"].join(5)  # the stand-in archives the job after it publishes the result
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["result"], {"items": 7})
        self.assertIn("return app.project.numItems;", seen["text"])
        self.assertEqual(seen["tmp_left"], [], "the job lands in inbox under its final name in one rename")
        self.assertEqual(sorted(p.name for p in (self.root / "done").iterdir()), [res["id"] + ".jsx"])

    def test_error_line_maps_back_to_the_job_body(self):
        self.beat()
        body = "var a = 1;\nvar b = a.nope.deeper;\nreturn b;"
        self.stand_in_bridge(lambda text: {"ok": False, "error": "TypeError: undefined is not an object", "line": 2})
        res = ae.run_js(body, kit="none", timeout=10)
        self.assertFalse(res["ok"])
        self.assertEqual(res["source"], "var b = a.nope.deeper;")

    def test_result_files_are_closed_after_reading(self):
        self.beat()
        self.stand_in_bridge(lambda text: {"ok": True, "result": 1})
        leaks, res = resource_warnings(ae.run_js, "return 1;", kit="none", timeout=10)
        self.assertTrue(res["ok"], res)
        self.assertEqual(leaks, [])

    def test_no_heartbeat_returns_the_reason_without_writing_a_job(self):
        res = ae.run_js("return 1;", kit="none", timeout=1)
        self.assertFalse(res["ok"])
        self.assertIn("No bridge heartbeat", res["error"])
        self.assertEqual(list((self.root / "inbox").iterdir()), [])

    def test_unanswered_job_says_it_may_still_run(self):
        self.beat(age_s=20)
        res = ae.run_js("return 1;", kit="none", timeout=0.3)
        self.assertFalse(res["ok"])
        self.assertIn("has not polled for 20 s", res["error"])
        self.assertIn(res["job"], res["note"])
        self.assertEqual([p.name for p in (self.root / "inbox").iterdir()], [res["job"] + ".jsx"])

    def test_after_effects_not_running_is_named(self):
        self.beat()
        with unittest.mock.patch.object(ae, "ae_pid", lambda: None):
            res = ae.explain_block()
        self.assertIn("not running", res["error"])

    def test_handoff_writes_one_file_for_a_person_and_waits_for_nothing(self):
        leaks, res = resource_warnings(ae.run_js, "return 1;", kit="none", channel="handoff")
        self.assertEqual(leaks, [])
        self.assertIsNone(res["ok"])
        handoff = Path(res["handoff"])
        self.assertEqual(handoff.parent, self.root / "handoff")
        self.assertIn("return 1;", handoff.read_text(encoding="utf-8"))
        self.assertIn("File > Scripts > Run Script File", res["say"])

    def test_unknown_channel_is_refused(self):
        res = ae.submit("// job", "j1", timeout=1, channel="telnet")
        self.assertEqual(res, {"ok": False, "error": "unknown channel telnet"})

    def test_status_reports_heartbeat_age(self):
        self.beat(age_s=3)
        leaks, s = resource_warnings(ae.status)
        self.assertEqual(leaks, [])
        self.assertAlmostEqual(s["age_s"], 3, delta=1)

    def test_unreadable_status_counts_as_no_heartbeat(self):
        (self.root / "status.json").write_text("{half", encoding="utf-8")
        self.assertIsNone(ae.status())


FFPROBE = {
    "streams": [
        {"codec_type": "video", "codec_name": "prores", "profile": "4444", "width": 1920, "height": 1080,
         "r_frame_rate": "30000/1001", "pix_fmt": "yuva444p12le", "nb_frames": "60",
         "color_range": "tv", "color_space": "bt709", "color_transfer": "bt709", "color_primaries": "bt709"},
        {"codec_type": "audio", "codec_name": "pcm_s16le", "sample_rate": "48000", "channels": 2},
    ],
    "format": {"duration": "2.002000", "bit_rate": "250000000"},
}


class Probe(unittest.TestCase):
    def probe_with(self, payload, returncode=0):
        done = unittest.mock.Mock(returncode=returncode, stdout=json.dumps(payload), stderr="bad file")
        with unittest.mock.patch.object(ae.shutil, "which", return_value="/usr/bin/ffprobe"), \
                unittest.mock.patch.object(ae.subprocess, "run", return_value=done) as run, \
                unittest.mock.patch.object(ae.os.path, "getsize", return_value=3 * 1048576):
            res = ae.probe("/renders/out.mov")
        return res, run.call_args[0][0]

    def test_summary_reads_size_rate_frames_and_alpha(self):
        res, cmd = self.probe_with(FFPROBE)
        self.assertEqual(cmd[:2], ["ffprobe", "-v"])
        self.assertEqual(res["size_mb"], 3.0)
        self.assertEqual(res["bitrate_mbps"], 250.0)
        video, audio = res["streams"]
        self.assertEqual((video["width"], video["height"], video["fps"], video["frames"]), (1920, 1080, 29.97, 60))
        self.assertTrue(video["alpha"])
        self.assertEqual(video["color"], ["tv", "bt709", "bt709", "bt709"])
        self.assertEqual((audio["sample_rate"], audio["channels"]), ("48000", 2))

    def test_no_alpha_and_unknown_frame_count(self):
        payload = json.loads(json.dumps(FFPROBE))
        payload["streams"][0].update(pix_fmt="yuv420p", nb_frames="N/A")
        res, _ = self.probe_with(payload)
        self.assertFalse(res["streams"][0]["alpha"])
        self.assertIsNone(res["streams"][0]["frames"])

    def test_ffprobe_error_and_missing_ffprobe(self):
        res, _ = self.probe_with({}, returncode=1)
        self.assertEqual(res, {"ok": False, "error": "bad file"})
        with unittest.mock.patch.object(ae.shutil, "which", return_value=None):
            self.assertEqual(ae.probe("x.mov"), {"ok": False, "error": "ffprobe not found"})


class LabelsAndSheets(unittest.TestCase):
    def test_label_png_is_a_valid_rgba_png_and_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "l.png")
            leaks, _ = resource_warnings(ae.label_png, "F12  0.50S", path, scale=2)
            data = Path(path).read_bytes()
        self.assertEqual(leaks, [])
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        w, h, depth, color = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((depth, color), (8, 6))
        self.assertEqual(h, (7 + 4) * 2)
        self.assertEqual(w, (len("F12  0.50S") * 6 + 3) * 2)
        idat = data.index(b"IDAT")
        size = struct.unpack(">I", data[idat - 4:idat])[0]
        self.assertEqual(len(zlib.decompress(data[idat + 4:idat + 4 + size])), h * (1 + w * 4))

    def test_image_size_reads_a_png_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = ae.label_png("A", os.path.join(tmp, "a.png"))
            self.assertEqual(ae.image_size(path), ((6 + 3) * 3, 11 * 3))
            self.assertIsNone(ae.image_size(os.path.join(tmp, "missing.png")))

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
    def test_contact_sheet_from_labeled_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = [ae.label_png("FRAME %d" % i, os.path.join(tmp, "f%d.png" % i), scale=4) for i in range(4)]
            out = ae.contact_sheet(frames, os.path.join(tmp, "sheet.jpg"), labels=["F%d" % i for i in range(4)])
            self.assertEqual(out, os.path.join(tmp, "sheet.jpg"))
            self.assertGreater(os.path.getsize(out), 1000)

    def test_contact_sheet_without_images_writes_nothing(self):
        self.assertIsNone(ae.contact_sheet([], "unused.jpg"))


class InstallBridge(unittest.TestCase):
    def test_install_keeps_the_previous_copy_and_never_touches_other_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            newest, older = Path(tmp, "27.0"), Path(tmp, "26.5")
            startup = newest / "Scripts" / "Startup"
            startup.mkdir(parents=True)
            (older / "Scripts" / "Startup").mkdir(parents=True)
            (startup / "ae_bridge.jsx").write_text("// the person's earlier bridge\n", encoding="utf-8")
            with unittest.mock.patch.object(ae, "prefs_dirs", lambda: [str(newest), str(older)]):
                res = ae.install_bridge()
            self.assertTrue(res["ok"])
            self.assertEqual(res["installed"], str(startup / "ae_bridge.jsx"))
            self.assertEqual((startup / "ae_bridge.jsx.previous").read_text(encoding="utf-8"), "// the person's earlier bridge\n")
            self.assertEqual((startup / "ae_bridge.jsx").read_bytes(), (LEAD / "ae_bridge.jsx").read_bytes())
            self.assertEqual(list((older / "Scripts" / "Startup").iterdir()), [])

    def test_no_preferences_folder_means_start_after_effects_first(self):
        with unittest.mock.patch.object(ae, "prefs_dirs", lambda: []):
            res = ae.install_bridge()
        self.assertFalse(res["ok"])
        self.assertIn("start After Effects once", res["error"])

    def test_prefs_dirs_keeps_version_folders_only_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp, "Adobe", "After Effects")
            for name in ("26.5", "27.0", "9.0", "Plug-ins"):
                (root / name).mkdir(parents=True)
            with unittest.mock.patch.object(ae.os.path, "expanduser", lambda p: str(Path(tmp, "Adobe", "After Effects"))), \
                    unittest.mock.patch.dict(ae.os.environ, {"APPDATA": tmp}):
                found = [os.path.basename(d) for d in ae.prefs_dirs()]
        self.assertEqual(found, ["27.0", "26.5", "9.0"])


class Doctor(Mailbox):
    def test_preference_file_with_file_access_off_is_reported(self):
        prefs = self.root / "prefs" / "27.0"
        prefs.mkdir(parents=True)
        (prefs / "Adobe After Effects 27.0 Prefs.txt").write_text(
            '["Main Pref Section v2"]\n\t"Pref_SCRIPTING_FILE_NETWORK_SECURITY" = "0"\n', encoding="utf-8")
        self.beat()
        with unittest.mock.patch.object(ae, "prefs_dirs", lambda: [str(prefs)]), \
                unittest.mock.patch.object(ae, "installs", lambda: []):
            leaks, d = resource_warnings(ae.doctor)
        self.assertEqual(leaks, [])
        self.assertIs(d["allow_file_network"], False)
        self.assertFalse(d["bridge_installed"])
        checks = "\n".join(d["checks"])
        self.assertIn("FAIL Allow Scripts to Write Files and Access Network", checks)
        self.assertIn("FAIL no After Effects found", checks)
        self.assertIn("ok   bridge test alive", checks)


if __name__ == "__main__":
    unittest.main()
