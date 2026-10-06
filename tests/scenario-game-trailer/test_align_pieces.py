"""align_pieces.py on a synthetic logo, run as a subprocess the way an agent runs it."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "scenario-game-trailer" / "scripts" / "align_pieces.py"


def run(*args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True)


def piece_at(logo, box, scale, canvas, offset):
    """Cut one piece out of the logo and redraw it the way an image edit returns it: rescaled, elsewhere."""
    part = logo.crop(box)
    part = part.resize((round(part.width * scale), round(part.height * scale)), Image.LANCZOS)
    out = Image.new("RGBA", canvas, (0, 0, 0, 0))
    out.alpha_composite(part, offset)
    return out


class AlignPiecesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.tmp.name)
        logo = Image.new("RGBA", (480, 240), (0, 0, 0, 0))
        d = ImageDraw.Draw(logo)
        d.rectangle((40, 60, 160, 180), fill=(220, 40, 40, 255))
        d.rectangle((70, 90, 130, 150), fill=(250, 220, 60, 255))
        d.ellipse((260, 50, 420, 210), fill=(40, 80, 220, 255))
        d.polygon([(340, 70), (400, 190), (280, 190)], fill=(250, 250, 250, 255))
        logo.save(self.cwd / "logo.png")
        (self.cwd / "pieces").mkdir()
        piece_at(logo, (40, 60, 161, 181), 1.25, (512, 512), (200, 150)).save(self.cwd / "pieces" / "square.png")
        piece_at(logo, (260, 50, 421, 211), 0.8, (400, 400), (30, 90)).save(self.cwd / "pieces" / "circle.png")

    def tearDown(self):
        self.tmp.cleanup()

    def test_usage_without_arguments(self):
        r = run(cwd=self.cwd)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Usage", r.stdout)

    def test_puts_each_piece_back_where_it_sits(self):
        r = run("logo.png", "pieces", "aligned", cwd=self.cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        report = json.loads((self.cwd / "aligned" / "align.json").read_text())
        expected = {"square.png": (40, 60, 121), "circle.png": (260, 50, 161)}
        for name, (x, y, w) in expected.items():
            placed = report[name]
            self.assertLessEqual(abs(placed["x"] - x), 3, placed)
            self.assertLessEqual(abs(placed["y"] - y), 3, placed)
            self.assertLessEqual(abs(placed["w"] - w), 4, placed)
            self.assertLess(placed["error"], 0.05, placed)
            with Image.open(self.cwd / "aligned" / name) as im:
                self.assertEqual(im.size, (480, 240))

    def test_places_an_unscaled_piece_to_the_pixel(self):
        logo = Image.open(self.cwd / "logo.png").convert("RGBA")
        exact = self.cwd / "exact"
        exact.mkdir()
        piece_at(logo, (41, 61, 161, 181), 1.0, (300, 300), (77, 33)).save(exact / "odd.png")
        r = run("logo.png", "exact", "out", cwd=self.cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        placed = json.loads((self.cwd / "out" / "align.json").read_text())["odd.png"]
        self.assertEqual((placed["x"], placed["y"], placed["w"]), (41, 61, 120), placed)
        self.assertFalse(placed["redrawn"])

    def test_flags_a_piece_the_edit_redrew(self):
        logo = Image.open(self.cwd / "logo.png").convert("RGBA")
        piece = piece_at(logo, (40, 60, 161, 181), 1.0, (300, 300), (50, 50))
        ImageDraw.Draw(piece).rectangle((80, 80, 140, 140), fill=(20, 200, 20, 255))
        changed = self.cwd / "changed"
        changed.mkdir()
        piece.save(changed / "recolored.png")
        r = run("logo.png", "changed", "out", cwd=self.cwd)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads((self.cwd / "out" / "align.json").read_text())["recolored.png"]["redrawn"])
        self.assertIn("redrawn", r.stdout)

    def test_a_missing_logo_touches_nothing(self):
        self.assertEqual(run("logo.png", "pieces", "aligned", cwd=self.cwd).returncode, 0)
        before = sorted(p.name for p in (self.cwd / "aligned").iterdir())
        r = run("missing.png", "pieces", "aligned", "--force", cwd=self.cwd)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not found", r.stderr)
        self.assertEqual(sorted(p.name for p in (self.cwd / "aligned").iterdir()), before)

    def test_refuses_a_non_empty_output_without_force_and_clears_stale_pieces_with_it(self):
        self.assertEqual(run("logo.png", "pieces", "aligned", cwd=self.cwd).returncode, 0)
        again = run("logo.png", "pieces", "aligned", cwd=self.cwd)
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("--force", again.stderr)
        (self.cwd / "pieces" / "circle.png").unlink()
        forced = run("logo.png", "pieces", "aligned", "--force", cwd=self.cwd)
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertFalse((self.cwd / "aligned" / "circle.png").exists())
        self.assertTrue((self.cwd / "aligned" / "square.png").exists())

    def test_never_writes_into_the_pieces_folder(self):
        r = run("logo.png", "pieces", "pieces", "--force", cwd=self.cwd)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(sorted(p.name for p in (self.cwd / "pieces").iterdir()), ["circle.png", "square.png"])


if __name__ == "__main__":
    unittest.main()
