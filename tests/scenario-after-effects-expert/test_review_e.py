"""Review round 1, group E: audio_to_mouth.py and word_timings.py fail closed on what they cannot read.

- audio_to_mouth.py: empty decoded audio, ffmpeg missing, failing or timing out end with a message, never a traceback;
  --shapes below 1 and --fps at or below 0 are refused by the parser.
- word_timings.py: two words on one first frame read increasing false, are listed and exit 1; a silence log with
  nothing to compare reads silence_agrees null, never true.

Standard library only. Each case builds its inputs in a temporary folder; ffmpeg is replaced by a mock or a stub.
"""

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).parent
FAMILY = HERE.parents[1] / "skills" / "dcc" / "after-effects"
RIGGING = FAMILY / "scenario-after-effects-character-rigging" / "scripts"
WORD_TIMINGS = FAMILY / "scenario-after-effects-typography" / "scripts" / "word_timings.py"
sys.path.insert(0, str(RIGGING))

import audio_to_mouth  # noqa: E402


def call_main(*argv):
    """Run audio_to_mouth.main() with argv; return (exit code or None, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = None
    with unittest.mock.patch.object(sys, "argv", ["audio_to_mouth.py", *argv]), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            audio_to_mouth.main()
        except SystemExit as stop:
            code = stop.code
    return code, out.getvalue(), err.getvalue()


class Temp(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ae_review_e_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write_json(self, name, data):
        path = self.tmp / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)


class AudioToMouthFailsClosed(Temp):
    def test_empty_decoded_audio_exits_with_a_message(self):
        with unittest.mock.patch.object(audio_to_mouth, "rms_per_frame", return_value=[]):
            code, out, _ = call_main("short.wav")
        self.assertIsInstance(code, str)
        self.assertIn("no audio frames decoded from short.wav", code)
        self.assertEqual(out, "")

    def test_ffmpeg_failure_carries_its_stderr(self):
        fail = subprocess.CalledProcessError(1, ["ffmpeg"], output="", stderr="Invalid data found when processing input\n")
        with unittest.mock.patch.object(audio_to_mouth.subprocess, "run", side_effect=fail):
            with self.assertRaises(SystemExit) as stop:
                audio_to_mouth.rms_per_frame("bad.wav", 24)
        self.assertIn("ffmpeg failed on bad.wav (exit 1)", str(stop.exception.code))
        self.assertIn("Invalid data found", str(stop.exception.code))

    def test_ffmpeg_missing_and_timeout_exit_with_a_message(self):
        with unittest.mock.patch.object(audio_to_mouth.subprocess, "run", side_effect=FileNotFoundError("ffmpeg")):
            with self.assertRaises(SystemExit) as stop:
                audio_to_mouth.rms_per_frame("voice.wav", 24)
        self.assertIn("ffmpeg not found", str(stop.exception.code))
        late = subprocess.TimeoutExpired(["ffmpeg"], audio_to_mouth.FFMPEG_TIMEOUT_S)
        with unittest.mock.patch.object(audio_to_mouth.subprocess, "run", side_effect=late) as run:
            with self.assertRaises(SystemExit) as stop:
                audio_to_mouth.rms_per_frame("long.wav", 24)
        self.assertIn("did not finish decoding long.wav", str(stop.exception.code))
        self.assertEqual(run.call_args.kwargs["timeout"], audio_to_mouth.FFMPEG_TIMEOUT_S)

    def test_shapes_below_one_and_zero_fps_are_refused(self):
        with unittest.mock.patch.object(audio_to_mouth, "rms_per_frame") as rms:
            code, _, err = call_main("voice.wav", "--shapes", "0")
            self.assertEqual(code, 2)
            self.assertIn("--shapes must be 1 or more", err)
            code, _, err = call_main("voice.wav", "--fps", "0")
            self.assertEqual(code, 2)
            self.assertIn("--fps must be above 0", err)
            rms.assert_not_called()

    def test_one_and_two_shapes_still_work(self):
        levels = [-120.0, -20.0, -20.0, -8.0, -8.0, -60.0]
        for shapes, top in (("1", 0), ("2", 1)):
            with unittest.mock.patch.object(audio_to_mouth, "rms_per_frame", return_value=levels):
                code, out, _ = call_main("voice.wav", "--shapes", shapes, "--lead", "0")
            self.assertIsNone(code)
            self.assertEqual(max(k[1] for k in json.loads(out)["keys"]), top)


class WordTimingsFailsClosed(Temp):
    def run_script(self, *argv):
        return subprocess.run([sys.executable, "-W", "error::ResourceWarning", str(WORD_TIMINGS), *argv],
                              capture_output=True, text=True, timeout=60)

    def test_two_words_on_one_frame_are_not_increasing(self):
        # 24 fps, lead 1: starts 0, 0.03 and 0.5 s give first frames 0, 0 and 11
        src = self.write_json("t.json", [{"word": "A", "start": 0.0, "end": 0.02}, {"word": "big", "start": 0.03, "end": 0.4},
                                         {"word": "day", "start": 0.5, "end": 0.9}])
        run = self.run_script(src, "--fps", "24", "--lead", "1")
        self.assertEqual(run.returncode, 1)
        self.assertIn("A/big at 0", run.stderr)
        checks = json.loads(run.stdout)["checks"]
        self.assertFalse(checks["increasing"])
        self.assertEqual(checks["same_frame"], [["A", "big", 0]])

    def test_silence_log_without_a_comparison_is_not_a_pass(self):
        src = self.write_json("t.json", {"segments": [{"words": [
            {"word": "Meet", "start": 0.1, "end": 0.4}, {"word": "you.", "start": 0.5, "end": 0.9},
            {"word": "Today", "start": 1.6, "end": 2.0}]}]})
        empty = self.tmp / "empty.log"
        empty.write_text("[silencedetect @ 0x1] nothing recognized here\n", encoding="utf-8")
        run = self.run_script(src, "--fps", "30", "--silence", str(empty))
        self.assertEqual(run.returncode, 0, run.stderr)
        checks = json.loads(run.stdout)["checks"]
        self.assertEqual(checks["phrase_onset_vs_silence_end_frames"], [])
        self.assertIsNone(checks["silence_agrees"])

    def test_a_matched_silence_still_agrees(self):
        src = self.write_json("t.json", {"segments": [{"words": [
            {"word": "Meet", "start": 0.1, "end": 0.4}, {"word": "you.", "start": 0.5, "end": 0.9},
            {"word": "Today", "start": 1.6, "end": 2.0}]}]})
        log = self.tmp / "silence.log"
        log.write_text("[silencedetect @ 0x1] silence_end: 1.58 | silence_duration: 0.6\n", encoding="utf-8")
        run = self.run_script(src, "--fps", "30", "--silence", str(log))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIs(json.loads(run.stdout)["checks"]["silence_agrees"], True)


if __name__ == "__main__":
    unittest.main()
