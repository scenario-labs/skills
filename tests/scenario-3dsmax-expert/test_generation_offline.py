"""Offline tests for scenario-3dsmax-generation runner helpers (gen_runner), no 3ds Max needed.

Downloads use a stand-in urlopen; every file goes to a temporary folder removed after each test.
The tiling-sheet test needs Pillow and skips without it.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skills" / "dcc" / "3dsmax" / "scenario-3dsmax-generation" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import gen_runner  # noqa: E402

HAVE_PIL = importlib.util.find_spec("PIL") is not None


class FakeResponse:
    def __init__(self, chunks, length=None, fail_after=None):
        self.chunks = list(chunks)
        self.headers = {"Content-Length": str(length)} if length is not None else {}
        self.fail_after = fail_after
        self.reads = 0

    def read(self, _n):
        if self.fail_after is not None and self.reads >= self.fail_after:
            raise TimeoutError("read timed out")
        self.reads += 1
        return self.chunks.pop(0) if self.chunks else b""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Download(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="gen_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def fetch(self, resp, name="a.glb"):
        with mock.patch.object(gen_runner.urllib.request, "urlopen", lambda req, timeout: resp):
            return gen_runner.download("https://example.invalid/a", self.dir, name)

    def test_complete_download(self):
        path = self.fetch(FakeResponse([b"abc", b"de"], length=5))
        self.assertEqual(Path(path).read_bytes(), b"abcde")

    def test_truncated_download_is_rejected_and_removed(self):
        with self.assertRaises(IOError):
            self.fetch(FakeResponse([b"abc"], length=10))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "a.glb")))

    def test_failed_read_leaves_no_file_so_retry_works(self):
        with self.assertRaises(TimeoutError):
            self.fetch(FakeResponse([b"abc", b"de"], fail_after=1))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "a.glb")))
        self.fetch(FakeResponse([b"abc"]))

    def test_existing_file_is_kept(self):
        Path(self.dir, "a.glb").write_bytes(b"old")
        with self.assertRaises(FileExistsError):
            self.fetch(FakeResponse([b"new"]))
        self.assertEqual(Path(self.dir, "a.glb").read_bytes(), b"old")

    def test_no_content_length_is_accepted(self):
        self.fetch(FakeResponse([b"abc"]))


@unittest.skipUnless(HAVE_PIL, "Pillow not installed")
class TileSheet(unittest.TestCase):
    def test_palette_colors_and_transparency_survive(self):
        from PIL import Image

        d = tempfile.mkdtemp(prefix="gen_")
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        src = Image.new("P", (4, 4), 1)
        src.putpalette([0, 0, 0, 200, 30, 40] + [0] * (254 * 3))
        src.info["transparency"] = 0
        src.putpixel((0, 0), 0)
        src_path, out_path = os.path.join(d, "p.png"), os.path.join(d, "sheet.png")
        src.save(src_path, transparency=0)
        gen_runner.tile_sheet(src_path, out_path)
        sheet = Image.open(out_path).convert("RGBA")
        self.assertEqual(sheet.getpixel((1, 1)), (200, 30, 40, 255))
        self.assertEqual(sheet.getpixel((4, 4))[3], 0)


if __name__ == "__main__":
    unittest.main()
