"""song_hits.py on a synthetic click track, run as a subprocess the way an agent runs it."""

import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "scenario-game-trailer" / "scripts" / "song_hits.py"
RATE = 22050


def run(*args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True)


def click_track(path, bpm=120.0, seconds=12.0, silence=(5.0, 7.0)):
    """Short decaying clicks on every beat, with a silent gap where a trailer would drop out."""
    beat = 60.0 / bpm
    samples = [0.0] * int(seconds * RATE)
    t = 0.0
    while t < seconds:
        if not (silence[0] <= t < silence[1]):
            start = int(t * RATE)
            for i in range(int(0.03 * RATE)):
                if start + i < len(samples):
                    samples[start + i] = 0.8 * math.sin(2 * math.pi * 1000 * i / RATE) * math.exp(-i / (0.005 * RATE))
        t += beat
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in samples))


@unittest.skipUnless(shutil.which("ffmpeg"), "song_hits.py reads audio through ffmpeg")
class SongHitsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.tmp.name)
        click_track(self.cwd / "song.wav")

    def tearDown(self):
        self.tmp.cleanup()

    def test_usage_without_arguments(self):
        r = run(cwd=self.cwd)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Usage", r.stdout)

    def test_measures_tempo_silence_and_hits(self):
        r = run("song.wav", "hits.json", cwd=self.cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        report = json.loads((self.cwd / "hits.json").read_text())
        self.assertAlmostEqual(report["bpm"], 120.0, delta=3.0)
        self.assertAlmostEqual(report["duration"], 12.0, delta=0.1)
        silent = [s for s in report["sections"] if s["kind"] == "silence"]
        self.assertTrue(any(s["start"] <= 5.5 and s["end"] >= 6.5 for s in silent), report["sections"])
        self.assertTrue(report["strongest_hits"])
        self.assertFalse(any(5.1 < t < 6.9 for t in report["onsets"]), report["onsets"])

    def test_refuses_to_overwrite_without_force(self):
        self.assertEqual(run("song.wav", "hits.json", cwd=self.cwd).returncode, 0)
        again = run("song.wav", "hits.json", cwd=self.cwd)
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("--force", again.stderr)
        self.assertEqual(run("song.wav", "hits.json", "--force", cwd=self.cwd).returncode, 0)

    def test_never_writes_over_the_song(self):
        before = (self.cwd / "song.wav").read_bytes()
        r = run("song.wav", "song.wav", "--force", cwd=self.cwd)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.cwd / "song.wav").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
