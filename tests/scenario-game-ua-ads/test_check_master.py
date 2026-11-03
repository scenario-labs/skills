"""check_master.py: the onset search with repeated hits and trims, and the end-to-end report."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

import helpers

cm = helpers.load("check_master")
SR = helpers.SR


def place(render, x, t, gain=1.0):
    p = round(t * SR)
    render[p:p + len(x)] += gain * x[:len(render) - p]


@unittest.skipUnless(helpers.HAS_FFMPEG, "needs ffmpeg and ffprobe")
class OnsetTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.tap = helpers.burst(0.12, amp=0.5, seed=1)
        helpers.write_wav(self.dir / "tap.wav", self.tap)

    def test_repeated_hits_each_match_their_own_onset(self):
        times = [1.0, 1.267, 1.533]  # taps 8 frames apart, closer than the 0.35 s search
        render = np.zeros(3 * SR)
        for t in times:
            place(render, self.tap, t)
        render[round(0.95 * SR):round(1.15 * SR)] += 0.05 * np.random.default_rng(2).standard_normal(round(0.2 * SR))
        hits = [{"label": f"tap {k}", "file": str(self.dir / "tap.wav"), "t": t, "trimStart": 0.0} for k, t in enumerate(times)]
        rows = cm.onset_table(render, hits)
        for r in rows:
            self.assertLess(abs(r["offset"]), 0.001, r)
            self.assertFalse(r["check"], r)
        naive, _ = cm.onset(render, cm.mono(self.dir / "tap.wav")[:round(0.25 * SR)], 1.0, -0.15, 0.35)
        self.assertAlmostEqual(naive, 0.267, delta=0.002)  # the unbounded window takes the clean neighbor

    def test_trim_start_is_honored(self):
        lead = helpers.tone(0.06, amp=0.5, freq=1000)
        helpers.write_wav(self.dir / "swish.wav", np.concatenate([lead, self.tap]))
        render = np.zeros(2 * SR)
        place(render, self.tap, 0.5)
        hit = {"label": "swish", "file": str(self.dir / "swish.wav"), "t": 0.5, "trimStart": 0.06, "end": 0.62}
        (row,) = cm.onset_table(render, [hit])
        self.assertLess(abs(row["offset"]), 0.001, row)

    def test_windows_stop_halfway_to_a_repeat_only(self):
        hits = [{"file": "a", "t": 1.0}, {"file": "a", "t": 1.2}, {"file": "b", "t": 1.1}]
        windows = cm.search_windows(hits)
        self.assertEqual([tuple(round(v, 3) for v in w) for w in windows], [(-0.15, 0.1), (-0.1, 0.35), (-0.15, 0.35)])


@unittest.skipUnless(helpers.HAS_FFMPEG, "needs ffmpeg and ffprobe")
class ReportTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        tap = helpers.burst(0.12, amp=0.6, seed=3)
        helpers.write_wav(self.dir / "tap.wav", tap)
        render = helpers.tone(2.0, amp=0.05)
        for t in (0.5, 1.2):
            place(render, tap, t)
        helpers.write_wav(self.dir / "mix.wav", render)
        helpers.mux(self.dir / "master.mov", self.dir / "mix.wav")
        self.cues = {"duration": 2.0, "fps": 30, "canvas": [64, 112], "sections": [0, 1],
                     "cues": [{"label": f"tap {t}", "role": "hit", "file": str(self.dir / "tap.wav"), "t": t, "end": t + 0.12,
                               "trimStart": 0.0} for t in (0.5, 1.2)]}

    def check(self, cues):
        helpers.write_json(self.dir / "cues.json", cues)
        return helpers.run("check_master.py", self.dir / "master.mov", self.dir / "cues.json", "-o", self.dir / "qa")

    def test_report_writes_the_sheet_and_the_onset_table(self):
        result = self.check(self.cues)
        self.assertIn("video: h264 64x112", result.stdout)
        self.assertIn("section 0-1 s: mean", result.stdout)
        self.assertIn("true peak", result.stdout)
        self.assertTrue((self.dir / "qa/sheet_2fps.jpg").stat().st_size > 0)
        rows = json.loads((self.dir / "qa/onsets.json").read_text())
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertLess(abs(r["offset"]), 0.002, r)
        self.assertNotIn("FAIL hit", result.stderr)
        self.assertEqual(result.returncode, 1)  # the tiny test mix is far below -16 LUFS
        self.assertIn("outside -16 to -14", result.stderr)

    def test_a_wrong_canvas_or_length_fails(self):
        result = self.check({**self.cues, "canvas": [1080, 1920], "duration": 15.0})
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL canvas 64x112, planned 1080x1920", result.stderr)
        self.assertIn("planned 15.0 s", result.stderr)

    def test_a_late_hit_reads_check(self):
        late = {**self.cues, "cues": [{**self.cues["cues"][0], "t": 0.35}]}
        result = self.check(late)
        self.assertIn("CHECK", result.stdout)
        self.assertIn("FAIL hit tap 0.5 at 0.35 s", result.stderr)


if __name__ == "__main__":
    unittest.main()
