import importlib.util
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "scenario-video-ads" / "scripts" / "card.py"

spec = importlib.util.spec_from_file_location("card", SCRIPT)
card = importlib.util.module_from_spec(spec)
sys.modules["card"] = card
spec.loader.exec_module(card)

from PIL import Image  # noqa: E402


def run(argv):
    card.main(argv)


class ParseSizeTests(unittest.TestCase):
    def test_presets(self):
        self.assertEqual(card.parse_size("9:16"), (1080, 1920))
        self.assertEqual(card.parse_size("16:9"), (1920, 1080))

    def test_explicit_dimensions(self):
        self.assertEqual(card.parse_size("1440x1800"), (1440, 1800))

    def test_invalid_values_exit(self):
        for bad in ("square", "0x100", "-1x100", "1080"):
            with self.assertRaises(SystemExit):
                card.parse_size(bad)


class SafeBoxTests(unittest.TestCase):
    def test_portrait_clears_platform_ui(self):
        left, top, right, bottom = card.safe_box(1080, 1920)
        self.assertEqual(top, round(1920 * 0.14))
        self.assertEqual(bottom, round(1920 * 0.65))
        self.assertEqual(left, round(1080 * 0.08))
        self.assertEqual(right, 1080 - round(1080 * 0.08))

    def test_landscape_title_safe(self):
        self.assertEqual(card.safe_box(1920, 1080), (192, 108, 1728, 972))


class RenderTests(unittest.TestCase):
    def render(self, extra):
        out = pathlib.Path(tempfile.mkdtemp()) / "card.png"
        run(["--size", "9:16", "--text", "Night, distilled.", "--out", str(out)] + extra)
        return Image.open(out)

    def content_bbox(self, image):
        return image.getchannel("A").getbbox()

    def test_canvas_is_transparent_rgba_at_requested_size(self):
        image = self.render([])
        self.assertEqual(image.mode, "RGBA")
        self.assertEqual(image.size, (1080, 1920))
        for corner in [(0, 0), (1079, 0), (0, 1919), (1079, 1919)]:
            self.assertEqual(image.getpixel(corner)[3], 0)

    def test_text_stays_inside_the_safe_zone(self):
        image = self.render([])
        left, top, right, bottom = card.safe_box(1080, 1920)
        x0, y0, x1, y1 = self.content_bbox(image)
        self.assertGreaterEqual(x0, left)
        self.assertGreaterEqual(y0, top)
        self.assertLessEqual(x1, right)
        self.assertLessEqual(y1, bottom)

    def test_long_text_wraps_and_still_fits(self):
        long_text = "the one reason to buy stated plainly " * 6
        out = pathlib.Path(tempfile.mkdtemp()) / "long.png"
        run(["--size", "9:16", "--text", long_text.strip(), "--out", str(out)])
        image = Image.open(out)
        left, top, right, bottom = card.safe_box(1080, 1920)
        x0, y0, x1, y1 = self.content_bbox(image)
        self.assertGreaterEqual(y0, top)
        self.assertLessEqual(y1, bottom)
        self.assertGreaterEqual(x0, left)
        self.assertLessEqual(x1, right)

    def test_backing_draws_a_box_behind_the_text(self):
        image = self.render(["--backing"])
        x0, y0, x1, y1 = self.content_bbox(image)
        center_edge = image.getpixel((x0 + 1, (y0 + y1) // 2))
        self.assertEqual(center_edge[:3], (0, 0, 0))
        self.assertGreater(center_edge[3], 0)

    def test_fixed_font_size_that_cannot_fit_exits(self):
        out = pathlib.Path(tempfile.mkdtemp()) / "nofit.png"
        with self.assertRaises(SystemExit):
            run(["--size", "200x400", "--text", "a sentence far too large for this tiny canvas",
                 "--font-size", "160", "--out", str(out)])

    def test_empty_text_exits(self):
        out = pathlib.Path(tempfile.mkdtemp()) / "empty.png"
        with self.assertRaises(SystemExit):
            run(["--size", "9:16", "--text", "   ", "--out", str(out)])

    def test_missing_text_exits(self):
        out = pathlib.Path(tempfile.mkdtemp()) / "none.png"
        with self.assertRaises(SystemExit):
            run(["--size", "9:16", "--out", str(out)])


if __name__ == "__main__":
    unittest.main()
