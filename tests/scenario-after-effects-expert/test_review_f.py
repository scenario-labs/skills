"""Review round 1, group F: the delivery gate and the ad scorecard fail closed.

- delivery_check.py: every member of an image sequence is probed; every requested key gives a row, and a key a sequence
  cannot carry (fps, duration, faststart) fails with its reason; an empty spec list and a deliverable with no key fail;
  a failed ffmpeg analysis is a failed probe, never parsed measurements.
- adtools.py: a failed or empty picture decode fails the review; a near-empty run from frame 0 fails; rule frame counts
  scale to the report's frame rate; ratio_worst10 is the tenth percentile of the per-pixel contrast ratios.

ffprobe and ffmpeg answers are canned where the logic is what counts; the planted-sequence cases need ffmpeg.
"""

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
for folder in (FAMILY / "scenario-after-effects-color-delivery" / "scripts",
               FAMILY / "scenario-after-effects-motion-production" / "scripts"):
    sys.path.insert(0, str(folder))

import adtools  # noqa: E402
import delivery_check  # noqa: E402

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def png_info(width=1920, height=1080, pix_fmt="rgba"):
    return {"streams": [{"codec_type": "video", "codec_name": "png", "width": width, "height": height, "pix_fmt": pix_fmt,
                         "avg_frame_rate": "25/1"}], "format": {}}


def main_of(module, *argv):
    out = io.StringIO()
    with unittest.mock.patch.object(sys, "argv", [module.__name__ + ".py", *argv]), contextlib.redirect_stdout(out):
        try:
            module.main()
            code = None
        except SystemExit as stop:
            code = stop.code
    return code, out.getvalue()


class Temp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def plant_sequence(self, count, start=0):
        for n in range(start, start + count):
            (self.tmp / ("shot_%05d.png" % n)).write_bytes(b"png")
        return str(self.tmp / "shot_%05d.png")


class DeliverySequence(Temp):
    def test_every_member_is_probed_and_one_odd_frame_fails(self):
        pattern = self.plant_sequence(2)
        answers = {"shot_00000.png": png_info(1920, 1080), "shot_00001.png": png_info(1280, 720)}
        with unittest.mock.patch.object(delivery_check, "ffprobe", side_effect=lambda p: answers[Path(p).name]) as probe:
            rows = {r["check"]: r for r in delivery_check.check({"file": pattern, "width": 1920, "height": 1080, "frames": 2})}
        self.assertEqual(probe.call_count, 2)
        self.assertFalse(rows["width"]["pass"])
        self.assertIn("1 of 2 frames", rows["width"]["measured"])
        self.assertIn("shot_00001.png", rows["width"]["measured"])
        self.assertTrue(rows["frames"]["pass"])

    def test_a_uniform_sequence_still_passes(self):
        pattern = self.plant_sequence(3)
        with unittest.mock.patch.object(delivery_check, "ffprobe", return_value=png_info()):
            rows = delivery_check.check({"file": pattern, "width": 1920, "height": 1080, "pix_fmt": "rgba", "alpha": True,
                                         "frames": 3, "sequence_start": 0, "no_data": True, "no_audio": True})
        self.assertEqual([r["check"] for r in rows if not r["pass"]], [])
        self.assertEqual(len(rows), 9)

    def test_every_requested_key_gives_a_row_and_unmeasurable_ones_fail(self):
        pattern = self.plant_sequence(2)
        spec = {"file": pattern, "fps": 25, "duration": 0.08, "faststart": True, "no_data": True, "levels": {"every": 1}}
        with unittest.mock.patch.object(delivery_check, "ffprobe", return_value=png_info()):
            rows = {r["check"]: r for r in delivery_check.check(spec)}
        for name in ("fps", "duration", "faststart (moov before mdat)"):
            self.assertFalse(rows[name]["pass"], name)
            self.assertEqual(rows[name]["measured"], delivery_check.SEQ_NA)
        self.assertTrue(rows["data streams"]["pass"])
        self.assertFalse(rows["Y levels"]["pass"])
        self.assertEqual(rows["Y levels"]["measured"], "rgba")

    def test_frame_set_is_built_once_and_gaps_still_count(self):
        for n in (3, 4, 7):
            (self.tmp / ("shot_%05d.png" % n)).write_bytes(b"png")
        real_set = set
        calls = []

        def counting_set(*a):
            calls.append(1)
            return real_set(*a)

        with unittest.mock.patch.object(delivery_check, "ffprobe", return_value=png_info()), \
                unittest.mock.patch.object(delivery_check, "set", counting_set, create=True):
            rows = {r["check"]: r for r in delivery_check.check({"file": str(self.tmp / "shot_%05d.png")})}
        self.assertEqual(rows["gaps"]["measured"], 2)
        self.assertEqual(len(calls), 1)


class DeliveryFailClosed(Temp):
    def test_empty_spec_list_fails(self):
        spec = self.tmp / "spec.json"
        spec.write_text("[]", encoding="utf-8")
        code, out = main_of(delivery_check, str(spec))
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)

    def test_a_deliverable_with_no_key_fails(self):
        path = self.tmp / "ad.mp4"
        path.write_bytes(b"\0" * 16)
        info = {"streams": [dict(png_info()["streams"][0], nb_frames="50")], "format": {"duration": "2.0"}}
        with unittest.mock.patch.object(delivery_check, "ffprobe", return_value=info):
            rows = delivery_check.check({"file": str(path)})
        self.assertEqual([(r["check"], r["pass"]) for r in rows], [("requirements", False)])

    def test_failed_ffmpeg_analysis_is_a_failed_probe(self):
        partial = "[Parsed_metadata_2] lavfi.signalstats.YMIN=20\n[Parsed_metadata_2] lavfi.signalstats.YMAX=230\n" \
                  "Summary:\n  Integrated loudness:\n    I:  -14.0 LUFS\n  True peak:\n    Peak:  -2.0 dBFS\n"
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr=partial + "Error while decoding stream #0:0\n")
        with unittest.mock.patch.object(delivery_check, "run", return_value=failed):
            with self.assertRaises(RuntimeError):
                delivery_check.luma_range("x.mp4", 1)
            with self.assertRaises(RuntimeError):
                delivery_check.loudness("x.mp4")
        path = self.tmp / "ad.mp4"
        path.write_bytes(b"\0" * 16)
        info = {"streams": [dict(png_info()["streams"][0], codec_name="h264", pix_fmt="yuv420p", nb_frames="2")],
                "format": {"duration": "2.0"}}
        spec = self.tmp / "spec.json"
        spec.write_text(json.dumps([{"file": str(path), "levels": {"every": 1}}]), encoding="utf-8")
        with unittest.mock.patch.object(delivery_check, "ffprobe", return_value=info), \
                unittest.mock.patch.object(delivery_check, "run", return_value=failed):
            code, out = main_of(delivery_check, str(spec))
        self.assertEqual(code, 1)
        self.assertIn("probe", out)
        self.assertIn("0 of 1 deliverables pass", out)

    @unittest.skipUnless(HAS_FFMPEG, "needs ffmpeg and ffprobe")
    def test_planted_sequence_of_300_frames_with_one_odd_frame(self):
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=64x36:r=30:d=10",
                        "-start_number", "0", str(self.tmp / "seq_%05d.png")], check=True, timeout=120)
        odd = self.tmp / "seq_00150.png"
        odd.rename(self.tmp / "keep.bin")
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=32x18", "-frames:v", "1", str(odd)],
                       check=True, timeout=60)
        spec = {"file": str(self.tmp / "seq_%05d.png"), "width": 64, "height": 36, "frames": 300, "sequence_start": 0}
        t0 = time.time()
        rows = {r["check"]: r for r in delivery_check.check(spec)}
        elapsed = time.time() - t0
        self.assertFalse(rows["width"]["pass"])
        self.assertIn("1 of 300 frames", rows["width"]["measured"])
        self.assertTrue(rows["frames"]["pass"])
        self.assertLess(elapsed, 120)
        print("\n    300-frame sequence probed in %.1f s" % elapsed, file=sys.stderr)


class AdPicture(unittest.TestCase):
    REP = {"comp": "AD", "fps": 30, "hook_text_frame": 0, "first_cut_f": 30, "texts": [], "cuts_per_10s": [],
           "logo_first_f": None, "cta_frames": 90, "endcard_frames": 90, "frames": 300, "zone_violations": []}

    def test_failed_or_empty_decode_raises(self):
        w, h = 96, 54
        partial = subprocess.CompletedProcess([], 1, stdout=bytes(w * h * 3), stderr=b"Invalid data found")
        with unittest.mock.patch.object(adtools.subprocess, "run", return_value=partial):
            with self.assertRaises(RuntimeError):
                adtools.occupancy("broken.mp4")
        empty = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
        with unittest.mock.patch.object(adtools.subprocess, "run", return_value=empty):
            with self.assertRaises(RuntimeError):
                adtools.occupancy("empty.mp4")

    def test_review_fails_an_unreadable_picture(self):
        with unittest.mock.patch.object(adtools, "occupancy", side_effect=RuntimeError("ffmpeg decoded no frame")):
            res = adtools.review(dict(self.REP), picture="broken.mp4")
        row = next(r for r in res["rows"] if r["check"] == "picture decode")
        self.assertFalse(row["pass"])

    def test_near_empty_opening_fails(self):
        occ = [0.0] * 60 + [0.5] * 240
        with unittest.mock.patch.object(adtools, "occupancy", return_value=occ):
            res = adtools.review(dict(self.REP), picture="cell.mp4")
        row = next(r for r in res["rows"] if r["check"].startswith("near-empty"))
        self.assertFalse(row["pass"])
        self.assertEqual(row["value"], [[0, 59]])

    def test_end_card_past_the_decoded_frames_fails(self):
        with unittest.mock.patch.object(adtools, "occupancy", return_value=[0.5] * 100):
            res = adtools.review(dict(self.REP), picture="short.mp4")
        row = next(r for r in res["rows"] if r["check"].startswith("end-card content"))
        self.assertFalse(row["pass"])


class AdFrameRate(unittest.TestCase):
    def rep(self, fps, **kw):
        base = {"comp": "AD", "fps": fps, "hook_text_frame": 0, "first_cut_f": 0, "cuts_per_10s": [], "logo_first_f": None,
                "frames": 30 * fps, "zone_violations": [], "texts": [{"text": "Play", "words": 1, "frames": 30}],
                "cta_frames": 60, "endcard_frames": 75}
        base.update(kw)
        return base

    def failed(self, rep):
        return sorted(r["check"].split(" (")[0] for r in adtools.review(rep)["rows"] if not r["pass"])

    def test_thresholds_unchanged_at_30_fps(self):
        self.assertEqual(self.failed(self.rep(30)), [])

    def test_thresholds_scale_at_60_fps(self):
        self.assertEqual(self.failed(self.rep(60)), ["CTA visible frames", "end card hold frames", "text 'Play' frames"])
        self.assertEqual(self.failed(self.rep(60, texts=[{"text": "Play", "words": 1, "frames": 60}], cta_frames=120,
                                              endcard_frames=150)), [])

    def test_need_is_printed_in_frames_of_the_report(self):
        res = adtools.review(self.rep(60))
        self.assertTrue(any("needs 60" in r["check"] for r in res["rows"]))


class AdContrast(unittest.TestCase):
    def test_worst10_is_the_lowest_tenth_of_per_pixel_ratios(self):
        # white text over 85 % black and 15 % RGB 200: the light tenth sets the worst ratio
        px = [bytes([0, 0, 0])] * 85 + [bytes([200, 200, 200])] * 15
        done = subprocess.CompletedProcess([], 0, stdout=b"".join(px), stderr=b"")
        with unittest.mock.patch.object(adtools.subprocess, "run", return_value=done):
            res = adtools.contrast("frame.png", "0,0,10,10", "FFFFFF")
            # black text over the same plate: the black pixels are text, the plate is all RGB 200
            dark = adtools.contrast("frame.png", "0,0,10,10", "000000")
        self.assertEqual(res["ratio_median"], 21.0)
        self.assertAlmostEqual(res["ratio_worst10"], 1.67, places=2)
        self.assertEqual(res["plate_pixels"], 100)
        self.assertEqual(dark["plate_pixels"], 15)
        self.assertEqual(dark["ratio_worst10"], dark["ratio_median"])

    def test_failed_read_is_an_error(self):
        failed = subprocess.CompletedProcess([], 1, stdout=b"", stderr=b"No such file")
        with unittest.mock.patch.object(adtools.subprocess, "run", return_value=failed):
            self.assertIn("error", adtools.contrast("missing.png", "0,0,10,10", "FFFFFF"))


if __name__ == "__main__":
    unittest.main()
