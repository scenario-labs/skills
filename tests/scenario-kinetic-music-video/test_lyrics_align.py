"""lyrics_align.py align: supplied lyrics that cover only part of the song keep their own timing."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "scenario-kinetic-music-video" / "scripts" / "lyrics_align.py"


def word(w, s, e):
    return {"w": w, "s": s, "e": e}


class PartialLyricsTest(unittest.TestCase):
    def test_last_word_does_not_absorb_the_rest_of_the_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "engine" / "data").mkdir(parents=True)
            (cwd / "analysis").mkdir()
            (cwd / "engine" / "data" / "audio.json").write_text(json.dumps({"vocal_onsets": [], "env": {}, "env_fps": 60}))
            # The transcript runs on for the whole song; the supplied lyrics stop after one line, and the sung name
            # was transcribed phonetically, so the last lyric word does not match.
            raw = [
                {"start": 1.0, "end": 2.4, "text": "", "words": [
                    word("Send", 1.0, 1.3), word("it", 1.3, 1.5), word("to", 1.5, 1.7), word("AirVay", 1.8, 2.4)]},
                {"start": 10.0, "end": 120.0, "text": "", "words": [
                    word("chief", 10.0, 10.4), word("of", 10.5, 10.6), word("the", 10.7, 10.8),
                    word("leftovers", 11.0, 12.0), word("rest", 119.0, 120.0)]},
            ]
            (cwd / "analysis" / "lyrics_raw.json").write_text(json.dumps(raw))
            (cwd / "lyrics.txt").write_text("# section: chorus\nSend it to Hervé\n")
            r = subprocess.run([sys.executable, str(SCRIPT), "align", "lyrics.txt"], cwd=cwd, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            words = json.loads((cwd / "engine" / "data" / "lyrics.json").read_text())["lines"][0]["words"]
            last = words[-1]
            self.assertEqual(last["w"], "Hervé")
            self.assertLess(last["e"], 5.0)
            self.assertLessEqual(last["e"] - last["s"], 2.0)


if __name__ == "__main__":
    unittest.main()
