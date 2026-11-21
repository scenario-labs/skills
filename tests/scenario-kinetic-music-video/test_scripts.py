"""The dependency-light scripts, run as subprocesses the way an agent runs them."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "scenario-kinetic-music-video" / "scripts"


def run(script, *args, cwd):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args], cwd=cwd, capture_output=True, text=True
    )


class SynthBeatTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.tmp.name)
        (self.cwd / "engine" / "data").mkdir(parents=True)
        audio = {
            "beats": [0.0, 0.5, 1.0, 1.5],
            "downbeats": [0.0, 1.0],
            "kicks": [0.0, 1.0],
            "snares": [0.5, 1.5],
        }
        (self.cwd / "engine" / "data" / "audio.json").write_text(json.dumps(audio))

    def tearDown(self):
        self.tmp.cleanup()

    def test_usage_without_arguments(self):
        r = run("synth_beat.py", cwd=self.cwd)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("usage", r.stderr)

    def test_writes_wav_then_refuses_to_replace_without_force(self):
        r = run("synth_beat.py", "0", "2", "beat.wav", cwd=self.cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertGreater((self.cwd / "beat.wav").stat().st_size, 1000)
        again = run("synth_beat.py", "0", "2", "beat.wav", cwd=self.cwd)
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("--force", again.stderr)
        forced = run("synth_beat.py", "0", "2", "beat.wav", "--force", cwd=self.cwd)
        self.assertEqual(forced.returncode, 0, forced.stderr)


class SheetTest(unittest.TestCase):
    def setUp(self):
        from PIL import Image

        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.tmp.name)
        for name in ("t_0001.png", "t_0002.png"):
            Image.new("RGB", (64, 36), "red").save(self.cwd / name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_usage_without_arguments(self):
        r = run("sheet.py", cwd=self.cwd)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("usage", r.stderr)

    def test_builds_sheet_and_protects_existing_and_inputs(self):
        r = run("sheet.py", "out.jpg", "2", "t_0001.png", "t_0002.png", cwd=self.cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.cwd / "out.jpg").exists())
        again = run("sheet.py", "out.jpg", "2", "t_0001.png", "t_0002.png", cwd=self.cwd)
        self.assertIn("--force", again.stderr)
        clobber = run("sheet.py", "t_0001.png", "2", "t_0001.png", "t_0002.png", "--force", cwd=self.cwd)
        self.assertNotEqual(clobber.returncode, 0)
        self.assertIn("also an input", clobber.stderr)

    def test_labels_name_the_time_of_stills_and_of_ffmpeg_frames(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("sheet", SCRIPTS / "sheet.py")
        sheet = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sheet)
        self.assertEqual(sheet.label("out/stills/t_000.25.png"), "0.25")
        self.assertEqual(sheet.label("t_012.50.png"), "12.5")
        # pipeline.md §7 writes f_%04d.jpg at 2 fps: frame 1 is the render's first frame
        self.assertEqual(sheet.label("out/watch/f_0001.jpg", 2), "0")
        self.assertEqual(sheet.label("out/watch/f_0041.jpg", 2, 20.0), "40")
        # a teaser sheet from --start 5.76 once read 5.8, 6.3 ...
        self.assertEqual(sheet.label("f_0002.jpg", 2, 5.76), "6.26")
        self.assertEqual(sheet.label("out/watch/f_0041.jpg"), "f_0041.jpg")
        self.assertEqual(sheet.label("cover.png", 2), "cover.png")

    def test_a_long_label_stays_inside_its_box(self):
        from PIL import Image
        import numpy as np

        name = "onset_10.333_frame0620_close.png"
        Image.new("RGB", (480, 72), "white").save(self.cwd / name)
        r = run("sheet.py", "long.jpg", "1", name, cwd=self.cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        top = np.asarray(Image.open(self.cwd / "long.jpg").convert("RGB")).astype(int)[:30]
        text = (top[..., 0] > 180) & (top[..., 1] > 120) & (top[..., 1] < 235) & (top[..., 2] < 160)
        box = top.max(axis=2) < 60
        self.assertTrue(text.any())
        # the box once took a fixed size per character and 1/14 of the tile's height, so a long file name ran
        # past it, right and below, onto the picture
        self.assertGreaterEqual(np.nonzero(box.any(axis=0))[0].max(), np.nonzero(text.any(axis=0))[0].max())
        self.assertGreaterEqual(np.nonzero(box.any(axis=1))[0].max(), np.nonzero(text.any(axis=1))[0].max())

    def test_fps_and_start_options_are_read(self):
        from PIL import Image

        for name in ("f_0001.jpg", "f_0002.jpg"):
            Image.new("RGB", (64, 36), "blue").save(self.cwd / name)
        r = run("sheet.py", "frames.jpg", "2", "f_0001.jpg", "f_0002.jpg", "--fps", "2", "--start", "20", cwd=self.cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.cwd / "frames.jpg").exists())
        bad = run("sheet.py", "x.jpg", "2", "f_0001.jpg", "--fps", "two", cwd=self.cwd)
        self.assertIn("--fps needs a number, not two", bad.stderr)


if __name__ == "__main__":
    unittest.main()
